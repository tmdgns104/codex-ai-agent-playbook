#!/usr/bin/env python3
"""Deterministic audit for V8.2 Self-Managing Skill Library governance.

Default exit codes:
  0 = PASS or WARN-only
  1 = FAIL
With --warn-exit-code:
  2 = WARN-only

Library and runtime Candidate audits are deterministic and do not require an LLM.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

HARNESS_ROOT = Path(__file__).resolve().parents[1]
ROUTER_DIR = HARNESS_ROOT / "router"
SKILLS_DIR = HARNESS_ROOT / "skills"
for import_dir in (ROUTER_DIR, SKILLS_DIR):
    if str(import_dir) not in sys.path:
        sys.path.insert(0, str(import_dir))

from lifecycle import LifecycleError, load_lifecycle  # noqa: E402
from promotion import PromotionError, load_protected_regressions, package_hash  # noqa: E402
from proposal import ProposalError, validate_proposal  # noqa: E402
from registry import RegistryValidationError, validate_root  # noqa: E402

FRONTMATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.S)
NAME = re.compile(r"(?m)^name:\s*([^\n]+)$")
DESCRIPTION = re.compile(r"(?m)^description:\s*(?:>-?|>?)\s*(.*)$")
MARKDOWN_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
PERSONAL_PATH = re.compile(r"(?:[A-Za-z]:\\Users\\[^\\\s]+|/Users/[^/\s]+|/home/[^/\s]+)")
OBVIOUS_SECRET = re.compile(
    r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|\bAKIA[0-9A-Z]{16}\b|\bgh[pousr]_[A-Za-z0-9]{20,}\b|\bsk-[A-Za-z0-9_-]{20,}\b"
)
EXECUTABLE_SUFFIXES = {".py", ".sh", ".ps1", ".bat", ".cmd", ".exe"}
UNKNOWN_SOURCE_VALUES = {"", "unknown", "unverified", "unspecified"}
PACKAGE_CANDIDATE_TYPES = {"create", "modify", "compress", "extract-reference"}


@dataclass(frozen=True)
class Finding:
    level: str
    code: str
    message: str


@dataclass
class AuditReport:
    findings: list[Finding] = field(default_factory=list)

    def add(self, level: str, code: str, message: str) -> None:
        self.findings.append(Finding(level=level, code=code, message=message))

    @property
    def result(self) -> str:
        if any(item.level == "FAIL" for item in self.findings):
            return "FAIL"
        if any(item.level == "WARN" for item in self.findings):
            return "WARN"
        return "PASS"

    def exit_code(self, *, warn_exit_code: bool = False) -> int:
        if self.result == "FAIL":
            return 1
        if self.result == "WARN" and warn_exit_code:
            return 2
        return 0

    def as_dict(self) -> dict[str, Any]:
        return {
            "result": self.result,
            "counts": {
                level: sum(1 for item in self.findings if item.level == level)
                for level in ("INFO", "WARN", "FAIL")
            },
            "findings": [item.__dict__ for item in self.findings],
        }


def _json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"top-level JSON must be an object: {path}")
    return data


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _central_router_test_path(root: Path) -> Path:
    """Resolve the central Router test in repository or installed layout."""
    root = root.resolve()
    candidates = (
        root / "harness" / "router" / "test_capability_router.py",
        root / "playbook-harness" / "router" / "test_capability_router.py",
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return candidates[0]


def _always_discovered_roots(root: Path) -> list[Path]:
    """Return discovery roots relevant to repository and installed layouts."""
    root = root.resolve()
    roots = [root / ".agents" / "skills"]
    if (root / "playbook-harness").is_dir():
        roots.append(root.parent / ".agents" / "skills")
    return roots


def relative_link_failures(skill_dir: Path, content: str) -> list[str]:
    failures: list[str] = []
    for raw_target in MARKDOWN_LINK.findall(content):
        target = raw_target.strip().split()[0].strip("<>")
        if not target or target.startswith("#"):
            continue
        if target.casefold().startswith(("http://", "https://", "mailto:", "data:")):
            continue
        target = target.split("#", 1)[0]
        if not target:
            continue
        candidate = (skill_dir / target).resolve()
        try:
            candidate.relative_to(skill_dir.resolve())
        except ValueError:
            failures.append(f"link escapes Skill package: {raw_target}")
            continue
        if not candidate.exists():
            failures.append(f"broken relative link: {raw_target}")
    return failures


def exact_trigger_overlaps(capabilities: list[dict[str, Any]]) -> dict[str, list[str]]:
    mapping: dict[str, set[str]] = {}
    for item in capabilities:
        capability_id = str(item.get("id", ""))
        for trigger in item.get("triggers", []):
            if isinstance(trigger, str):
                key = " ".join(trigger.casefold().split())
                mapping.setdefault(key, set()).add(capability_id)
    return {key: sorted(ids) for key, ids in mapping.items() if key and len(ids) > 1}


def _audit_skill_content(report: AuditReport, skill_id: str, skill_dir: Path, content: str) -> None:
    match = FRONTMATTER.search(content)
    if not match:
        report.add("FAIL", "frontmatter", f"{skill_id}: frontmatter missing/invalid")
    else:
        frontmatter = match.group(1)
        name_match = NAME.search(frontmatter)
        desc_match = DESCRIPTION.search(frontmatter)
        if not name_match:
            report.add("FAIL", "frontmatter-name", f"{skill_id}: name missing")
        else:
            actual_name = name_match.group(1).strip().strip("'\"")
            if actual_name != skill_id:
                report.add("FAIL", "frontmatter-name", f"{skill_id}: name mismatch ({actual_name})")
        if not desc_match:
            report.add("FAIL", "frontmatter-description", f"{skill_id}: description missing")

    if PERSONAL_PATH.search(content):
        report.add("FAIL", "personal-path", f"{skill_id}: personal absolute path found")
    if OBVIOUS_SECRET.search(content):
        report.add("FAIL", "secret", f"{skill_id}: obvious secret material found")
    for link_failure in relative_link_failures(skill_dir, content):
        report.add("FAIL", "relative-link", f"{skill_id}: {link_failure}")


def _find_active_skill(root: Path, skill_id: str) -> Path | None:
    try:
        registry = _json(root / "capability-library" / "registry.json")
    except (OSError, json.JSONDecodeError, ValueError):
        return None
    for item in registry.get("capabilities", []):
        if isinstance(item, dict) and item.get("id") == skill_id and item.get("type") == "skill":
            return (root / str(item.get("path", ""))).resolve()
    return None


def audit_candidate(candidate_dir: Path, *, root: Path | None = None) -> AuditReport:
    """Audit one runtime package Candidate before promotion."""
    candidate_dir = candidate_dir.resolve()
    root = root.resolve() if root is not None else None
    report = AuditReport()
    for name in ("SKILL.md", "proposal.json", "routing.json"):
        if not (candidate_dir / name).is_file():
            report.add("FAIL", "candidate-file", f"candidate missing {name}")
    if report.result == "FAIL":
        return report

    try:
        proposal = _json(candidate_dir / "proposal.json")
        validate_proposal(proposal)
    except (OSError, json.JSONDecodeError, ValueError, ProposalError) as exc:
        report.add("FAIL", "candidate-proposal", f"invalid proposal: {exc}")
        return report

    skill_id = str(proposal.get("skill_id", ""))
    change_type = proposal.get("change_type")
    if change_type not in PACKAGE_CANDIDATE_TYPES:
        report.add(
            "FAIL",
            "candidate-change-type",
            "Package Candidate proposal must use create, modify, compress, or extract-reference",
        )

    for field_name in ("source_id", "license", "provenance"):
        value = str(proposal.get(field_name, "")).strip()
        if value.casefold() in UNKNOWN_SOURCE_VALUES:
            report.add("FAIL", "candidate-provenance", f"{field_name} must be known before promotion")

    if change_type == "modify":
        if not proposal.get("evidence_refs"):
            report.add("FAIL", "candidate-evidence", "Evolver Candidate requires evidence_refs")
        for field_name in ("observed_pattern", "root_cause", "expected_behavior"):
            if not isinstance(proposal.get(field_name), str) or not proposal[field_name].strip():
                report.add("FAIL", "candidate-evolution", f"modify Candidate missing {field_name}")
        if root is not None:
            active_dir = _find_active_skill(root, skill_id)
            if active_dir is None or not active_dir.is_dir():
                report.add("FAIL", "candidate-base", f"ACTIVE Skill not found for modify Candidate: {skill_id}")
            else:
                try:
                    current_hash = package_hash(active_dir)
                except PromotionError as exc:
                    report.add("FAIL", "candidate-base", str(exc))
                else:
                    if current_hash != proposal.get("base_hash"):
                        report.add("FAIL", "candidate-base", "modify Candidate base_hash does not match ACTIVE Skill")

    content = _text(candidate_dir / "SKILL.md")
    _audit_skill_content(report, skill_id, candidate_dir, content)
    for required_heading in ("## Evidence", "## Stop / Handoff", "## Source / Provenance"):
        if required_heading not in content:
            report.add("FAIL", "candidate-content", f"{skill_id}: missing {required_heading}")

    try:
        routing = _json(candidate_dir / "routing.json")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        report.add("FAIL", "candidate-routing", f"invalid routing fixture: {exc}")
        return report
    if routing.get("skill_id") != skill_id:
        report.add("FAIL", "candidate-routing", "routing skill_id does not match proposal")
    positive = routing.get("positive")
    negative = routing.get("negative")
    minimum_positive = 2 if change_type == "create" else 1
    if not isinstance(positive, list) or len(positive) < minimum_positive:
        report.add("FAIL", "candidate-routing", f"routing fixture requires positive {minimum_positive}+")
    if not isinstance(negative, list) or len(negative) < 1:
        report.add("FAIL", "candidate-routing", "routing fixture requires negative 1+")
    preserved = routing.get("preserved_fixture")
    if preserved is not None:
        if not isinstance(preserved, str) or not preserved.strip():
            report.add("FAIL", "candidate-routing", "preserved_fixture must be a path or null")
        else:
            preserved_path = (candidate_dir / preserved).resolve()
            try:
                preserved_path.relative_to(candidate_dir)
            except ValueError:
                report.add("FAIL", "candidate-routing", "preserved_fixture escapes Candidate package")
            else:
                if not preserved_path.is_file():
                    report.add("FAIL", "candidate-routing", "preserved routing fixture is missing")

    scripts_dir = candidate_dir / "scripts"
    if scripts_dir.exists():
        executables = [
            path for path in scripts_dir.rglob("*")
            if path.is_file() and path.suffix.casefold() in EXECUTABLE_SUFFIXES
        ]
        if executables:
            added_permissions = set(proposal.get("permission_delta", {}).get("add", []))
            if change_type == "create" and "process_exec" not in added_permissions:
                report.add("FAIL", "candidate-executable", "executable Creator Candidate resource lacks process_exec")
            if added_permissions and not proposal.get("requires_human_gate"):
                report.add("FAIL", "candidate-executable", "executable Candidate permission expansion requires Human Gate")

    if report.result == "PASS":
        report.add("INFO", "candidate", f"candidate valid: {skill_id} ({change_type})")
    return report


def audit_library(root: Path, *, max_skill_bytes: int | None = None) -> AuditReport:
    root = root.resolve()
    report = AuditReport()
    policy_path = root / "capability-library" / "governance" / "policy.json"
    try:
        policy = _json(policy_path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        report.add("FAIL", "policy", f"governance policy invalid: {exc}")
        return report
    if policy.get("schema_version") != 1:
        report.add("FAIL", "policy-schema", "governance policy schema_version must be 1")
    warning_bytes = max_skill_bytes or int(policy.get("skill_soft_warning_bytes", 20000))

    try:
        source_count, capability_count = validate_root(root)
        report.add("INFO", "registry", f"registry valid: {source_count} sources / {capability_count} capabilities")
    except RegistryValidationError as exc:
        report.add("FAIL", "registry", f"registry validation failed: {exc}")
        return report
    try:
        load_lifecycle(root)
        report.add("INFO", "lifecycle", "lifecycle schema valid")
    except LifecycleError as exc:
        report.add("FAIL", "lifecycle", str(exc))
    try:
        load_protected_regressions(root)
        report.add("INFO", "protected-regression", "required protected regressions present")
    except PromotionError as exc:
        report.add("FAIL", "protected-regression", str(exc))

    registry = _json(root / "capability-library" / "registry.json")
    capabilities = registry.get("capabilities", [])
    optional_skills = [item for item in capabilities if isinstance(item, dict) and item.get("type") == "skill"]
    discovered_roots = _always_discovered_roots(root)
    central_router_tests = _central_router_test_path(root)
    central_test_text = _text(central_router_tests) if central_router_tests.exists() else ""

    for item in optional_skills:
        capability_id = str(item["id"])
        skill_dir = root / str(item["path"])
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            report.add("FAIL", "skill-file", f"{capability_id}: SKILL.md missing")
            continue
        content = _text(skill_file)
        _audit_skill_content(report, capability_id, skill_dir, content)
        if skill_dir.name != capability_id:
            report.add("FAIL", "frontmatter-name", f"{capability_id}: path/name mismatch")
        size = skill_file.stat().st_size
        report.add("INFO", "skill-size", f"{capability_id}: SKILL.md {size} bytes")
        if size > warning_bytes:
            report.add("WARN", "skill-size", f"{capability_id}: SKILL.md exceeds soft warning {warning_bytes} bytes ({size})")
        if any((discovery_root / capability_id).exists() for discovery_root in discovered_roots):
            report.add("FAIL", "optional-isolation", f"{capability_id}: leaked into .agents/skills")

        scripts_dir = skill_dir / "scripts"
        executables = []
        if scripts_dir.exists():
            executables = [path for path in scripts_dir.rglob("*") if path.is_file() and path.suffix.casefold() in EXECUTABLE_SUFFIXES]
        if executables:
            permissions = set(item.get("permissions", []))
            if "process_exec" not in permissions:
                report.add("FAIL", "executable-permission", f"{capability_id}: executable resources exist without process_exec declaration")
            if "scripts/" not in content and "script" not in content.casefold():
                report.add("WARN", "executable-declaration", f"{capability_id}: executable resources are not referenced by SKILL.md")

        local_fixture = skill_dir / "tests" / "routing.json"
        if not local_fixture.exists() and capability_id not in central_test_text:
            report.add("WARN", "routing-fixture", f"{capability_id}: no local or centralized routing fixture reference found")

    for trigger, ids in sorted(exact_trigger_overlaps(capabilities).items()):
        report.add("WARN", "trigger-overlap", f"trigger {trigger!r} shared by: {', '.join(ids)}")

    broad_terms = {str(item).casefold() for item in policy.get("broad_trigger_terms", [])}
    for item in capabilities:
        capability_id = str(item.get("id", ""))
        matches = sorted({trigger for trigger in item.get("triggers", []) if isinstance(trigger, str) and trigger.casefold() in broad_terms})
        if matches:
            report.add("WARN", "broad-trigger", f"{capability_id}: broad trigger review suggested: {', '.join(matches)}")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit V8.2 Skill governance, library, or runtime Candidate hygiene.")
    parser.add_argument("--root", default=".", help="Playbook repository root.")
    parser.add_argument("--candidate", default=None, help="Audit one runtime Candidate directory instead of ACTIVE library.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument("--max-skill-bytes", type=int, default=None, help="Override soft SKILL.md warning size.")
    parser.add_argument("--warn-exit-code", action="store_true", help="Return exit code 2 when only WARN findings exist.")
    args = parser.parse_args()

    report = (
        audit_candidate(Path(args.candidate), root=Path(args.root))
        if args.candidate
        else audit_library(Path(args.root), max_skill_bytes=args.max_skill_bytes)
    )
    if args.json:
        print(json.dumps(report.as_dict(), ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print("Codex Playbook - Skill Audit")
        print(f"Candidate: {Path(args.candidate).resolve()}" if args.candidate else f"Root: {Path(args.root).resolve()}")
        print()
        for item in report.findings:
            print(f"{item.level:10} {item.code}: {item.message}")
        print()
        print(f"RESULT     {report.result}")
    return report.exit_code(warn_exit_code=args.warn_exit_code)


if __name__ == "__main__":
    sys.exit(main())
