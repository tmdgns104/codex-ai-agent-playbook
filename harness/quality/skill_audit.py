#!/usr/bin/env python3
"""Deterministic audit for V8.2 Self-Managing Skill Library governance.

Default exit codes:
  0 = PASS or WARN-only
  1 = FAIL

With --warn-exit-code:
  2 = WARN-only

This is intentionally separate from quality_gate.py so the existing V8.1 gate
contract is not changed.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT_FROM_SCRIPT = Path(__file__).resolve().parents[2]
ROUTER_DIR = ROOT_FROM_SCRIPT / "harness" / "router"
SKILLS_DIR = ROOT_FROM_SCRIPT / "harness" / "skills"
for import_dir in (ROUTER_DIR, SKILLS_DIR):
    if str(import_dir) not in sys.path:
        sys.path.insert(0, str(import_dir))

from lifecycle import LifecycleError, load_lifecycle  # noqa: E402
from promotion import PromotionError, load_protected_regressions  # noqa: E402
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


def relative_link_failures(skill_dir: Path, content: str) -> list[str]:
    failures: list[str] = []
    for raw_target in MARKDOWN_LINK.findall(content):
        target = raw_target.strip().split()[0].strip("<>")
        if not target or target.startswith("#"):
            continue
        lower = target.casefold()
        if lower.startswith(("http://", "https://", "mailto:", "data:")):
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
            if not isinstance(trigger, str):
                continue
            key = " ".join(trigger.casefold().split())
            mapping.setdefault(key, set()).add(capability_id)
    return {key: sorted(ids) for key, ids in mapping.items() if key and len(ids) > 1}


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
    optional_skills = [
        item for item in capabilities if isinstance(item, dict) and item.get("type") == "skill"
    ]
    always_discovered = root / ".agents" / "skills"
    central_router_tests = root / "harness" / "router" / "test_capability_router.py"
    central_test_text = _text(central_router_tests) if central_router_tests.exists() else ""

    for item in optional_skills:
        capability_id = str(item["id"])
        skill_dir = root / str(item["path"])
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            report.add("FAIL", "skill-file", f"{capability_id}: SKILL.md missing")
            continue

        content = _text(skill_file)
        match = FRONTMATTER.search(content)
        if not match:
            report.add("FAIL", "frontmatter", f"{capability_id}: frontmatter missing/invalid")
        else:
            frontmatter = match.group(1)
            name_match = NAME.search(frontmatter)
            desc_match = DESCRIPTION.search(frontmatter)
            if not name_match:
                report.add("FAIL", "frontmatter-name", f"{capability_id}: name missing")
            else:
                actual_name = name_match.group(1).strip().strip("'\"")
                if actual_name != capability_id or skill_dir.name != capability_id:
                    report.add(
                        "FAIL",
                        "frontmatter-name",
                        f"{capability_id}: path/name mismatch ({actual_name})",
                    )
            if not desc_match:
                report.add("FAIL", "frontmatter-description", f"{capability_id}: description missing")

        size = skill_file.stat().st_size
        report.add("INFO", "skill-size", f"{capability_id}: SKILL.md {size} bytes")
        if size > warning_bytes:
            report.add(
                "WARN",
                "skill-size",
                f"{capability_id}: SKILL.md exceeds soft warning {warning_bytes} bytes ({size})",
            )

        if (always_discovered / capability_id).exists():
            report.add("FAIL", "optional-isolation", f"{capability_id}: leaked into .agents/skills")

        if PERSONAL_PATH.search(content):
            report.add("FAIL", "personal-path", f"{capability_id}: personal absolute path found")
        if OBVIOUS_SECRET.search(content):
            report.add("FAIL", "secret", f"{capability_id}: obvious secret material found")

        for link_failure in relative_link_failures(skill_dir, content):
            report.add("FAIL", "relative-link", f"{capability_id}: {link_failure}")

        scripts_dir = skill_dir / "scripts"
        executable_resources = []
        if scripts_dir.exists():
            executable_resources = [
                path for path in scripts_dir.rglob("*") if path.is_file() and path.suffix.casefold() in EXECUTABLE_SUFFIXES
            ]
        if executable_resources:
            permissions = set(item.get("permissions", []))
            if "process_exec" not in permissions:
                report.add(
                    "FAIL",
                    "executable-permission",
                    f"{capability_id}: executable resources exist without process_exec declaration",
                )
            if "scripts/" not in content and "script" not in content.casefold():
                report.add(
                    "WARN",
                    "executable-declaration",
                    f"{capability_id}: executable resources are not referenced by SKILL.md",
                )

        local_fixture = skill_dir / "tests" / "routing.json"
        if not local_fixture.exists() and capability_id not in central_test_text:
            report.add(
                "WARN",
                "routing-fixture",
                f"{capability_id}: no local or centralized routing fixture reference found",
            )

    overlaps = exact_trigger_overlaps(capabilities)
    for trigger, ids in sorted(overlaps.items()):
        report.add("WARN", "trigger-overlap", f"trigger {trigger!r} shared by: {', '.join(ids)}")

    broad_terms = {str(item).casefold() for item in policy.get("broad_trigger_terms", [])}
    for item in capabilities:
        capability_id = str(item.get("id", ""))
        matches = sorted(
            {
                trigger
                for trigger in item.get("triggers", [])
                if isinstance(trigger, str) and trigger.casefold() in broad_terms
            }
        )
        if matches:
            report.add(
                "WARN",
                "broad-trigger",
                f"{capability_id}: broad trigger review suggested: {', '.join(matches)}",
            )

    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit V8.2 Skill governance and package hygiene.")
    parser.add_argument("--root", default=".", help="Playbook repository root.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument("--max-skill-bytes", type=int, default=None, help="Override soft SKILL.md warning size.")
    parser.add_argument(
        "--warn-exit-code",
        action="store_true",
        help="Return exit code 2 when only WARN findings exist.",
    )
    args = parser.parse_args()

    report = audit_library(Path(args.root), max_skill_bytes=args.max_skill_bytes)
    if args.json:
        print(json.dumps(report.as_dict(), ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print("Codex Playbook - Skill Audit")
        print(f"Root: {Path(args.root).resolve()}")
        print()
        for item in report.findings:
            print(f"{item.level:10} {item.code}: {item.message}")
        print()
        print(f"RESULT     {report.result}")
    return report.exit_code(warn_exit_code=args.warn_exit_code)


if __name__ == "__main__":
    sys.exit(main())
