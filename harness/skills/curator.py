#!/usr/bin/env python3
"""Deterministic V8.2 Skill Curator boundary.

The Curator keeps normal-task context small. Library-wide inspection produces
metadata-only reports; Skill bodies are opened only for an explicitly selected
Candidate operation. ACTIVE packages are never mutated by proposal creation.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from promotion import package_hash
from proposal import ProposalError, validate_proposal

SUPPORTED_TYPES = {
    "compress",
    "extract-reference",
    "split",
    "merge",
    "trigger-narrow",
    "trigger-expand",
    "archive",
    "restore",
}
PACKAGE_TYPES = {"compress", "extract-reference"}
STRUCTURAL_HUMAN_GATE_TYPES = {"split", "merge", "trigger-expand", "archive"}
SKILL_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SAFE_PROPOSAL_ID = re.compile(r"^[A-Za-z0-9._-]+$")
PROTECTION_KEYS = {"pinned", "specialist", "externally_referenced", "recently_restored"}


class CuratorError(ValueError):
    """Raised when a Curator report/proposal would violate governance policy."""


@dataclass(frozen=True)
class ArchiveReview:
    action: str
    reason: str


def _json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise CuratorError(f"JSON top level must be an object: {path}")
    return data


def _registry(root: Path) -> dict[str, Any]:
    return _json(root / "capability-library" / "registry.json")


def _policy(root: Path) -> dict[str, Any]:
    return _json(root / "capability-library" / "governance" / "policy.json")


def _skill_items(root: Path) -> list[dict[str, Any]]:
    return [
        item
        for item in _registry(root).get("capabilities", [])
        if isinstance(item, dict) and item.get("type") == "skill"
    ]


def _normalized_signature(content: str) -> str:
    normalized = "\n".join(
        line.strip().casefold()
        for line in content.splitlines()
        if line.strip() and not line.lstrip().startswith("<!--")
    )
    return "sha256:" + hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _duplicate_line_ratio(content: str) -> float:
    lines = [line.strip().casefold() for line in content.splitlines() if len(line.strip()) >= 20]
    if not lines:
        return 0.0
    return round((len(lines) - len(set(lines))) / len(lines), 4)


def _trigger_overlap_map(items: list[dict[str, Any]]) -> dict[str, list[str]]:
    mapping: dict[str, set[str]] = {}
    for item in items:
        skill_id = str(item.get("id", ""))
        for trigger in item.get("triggers", []):
            if isinstance(trigger, str) and trigger.strip():
                key = " ".join(trigger.casefold().split())
                mapping.setdefault(key, set()).add(skill_id)
    return {key: sorted(ids) for key, ids in mapping.items() if len(ids) > 1}


def _event_metrics(events: list[dict[str, Any]], skill_id: str) -> dict[str, Any]:
    relevant = [event for event in events if skill_id in event.get("skill_ids", [])]
    verified_usage = [event for event in relevant if event.get("event_type") == "verified_usage"]
    timestamps = [str(event.get("timestamp")) for event in verified_usage if event.get("timestamp")]
    return {
        "usage_count": len(verified_usage),
        "verified_success_count": sum(event.get("verification") == "pass" for event in verified_usage),
        "verified_failure_count": sum(
            event.get("event_type") == "verification_failure" or event.get("verification") == "fail"
            for event in relevant
        ),
        "routing_false_positive_count": sum(event.get("event_type") == "routing_false_positive" for event in relevant),
        "routing_false_negative_count": sum(event.get("event_type") == "routing_false_negative" for event in relevant),
        "user_correction_count": sum(event.get("event_type") == "user_correction" for event in relevant),
        "last_used": max(timestamps) if timestamps else None,
    }


def build_curator_report(
    root: Path,
    *,
    events: list[dict[str, Any]] | None = None,
    protections: dict[str, dict[str, bool]] | None = None,
) -> dict[str, Any]:
    """Build a metadata-only library report; no Skill body is returned."""
    root = root.resolve()
    policy = _policy(root)
    items = _skill_items(root)
    overlaps = _trigger_overlap_map(items)
    events = events or []
    protections = protections or {}
    size_warning = int(policy.get("skill_soft_warning_bytes", 20000))

    skill_reports: list[dict[str, Any]] = []
    for item in items:
        skill_id = str(item["id"])
        skill_dir = root / str(item["path"])
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.is_file():
            raise CuratorError(f"ACTIVE Skill missing SKILL.md: {skill_id}")
        content = skill_file.read_text(encoding="utf-8", errors="replace")
        support_files = [path for path in skill_dir.rglob("*") if path.is_file() and path != skill_file]
        overlap_terms = sorted(term for term, ids in overlaps.items() if skill_id in ids)
        metrics = _event_metrics(events, skill_id)
        flags = protections.get(skill_id, {})
        protected = {key: bool(flags.get(key, False)) for key in sorted(PROTECTION_KEYS)}
        warnings: list[str] = []
        if skill_file.stat().st_size > size_warning:
            warnings.append("oversized")
        if overlap_terms:
            warnings.append("trigger-overlap")
        if metrics["routing_false_positive_count"]:
            warnings.append("routing-false-positive")
        if metrics["routing_false_negative_count"]:
            warnings.append("routing-false-negative")
        if metrics["verified_failure_count"] or metrics["user_correction_count"]:
            warnings.append("quality-evidence")

        skill_reports.append(
            {
                "skill_id": skill_id,
                "path": str(item["path"]),
                "size_bytes": skill_file.stat().st_size,
                "support_file_count": len(support_files),
                "body_signature": _normalized_signature(content),
                "duplicate_line_ratio": _duplicate_line_ratio(content),
                "trigger_count": len(item.get("triggers", [])),
                "trigger_overlap_terms": overlap_terms,
                "permissions": sorted(str(value) for value in item.get("permissions", [])),
                "source_id": item.get("source_id"),
                "license": item.get("license"),
                "metrics": metrics,
                "protection": protected,
                "warnings": sorted(set(warnings)),
            }
        )

    return {
        "schema_version": 1,
        "body_included": False,
        "skill_count": len(skill_reports),
        "skills": skill_reports,
        "warn_candidate_ids": sorted(item["skill_id"] for item in skill_reports if item["warnings"]),
    }


def warn_candidates(report: dict[str, Any]) -> list[dict[str, Any]]:
    if report.get("body_included") is not False:
        raise CuratorError("Curator report must not include whole Skill bodies by default")
    return [item for item in report.get("skills", []) if item.get("warnings")]


def archive_review(
    skill_report: dict[str, Any],
    *,
    replacement_exists: bool = False,
    deprecated_technology: bool = False,
    persistent_router_confusion: bool = False,
) -> ArchiveReview:
    protection = skill_report.get("protection", {})
    protected_reasons = sorted(key for key in PROTECTION_KEYS if protection.get(key))
    if protected_reasons:
        return ArchiveReview("NO_ACTION", "protected: " + ", ".join(protected_reasons))

    metrics = skill_report.get("metrics", {})
    low_usage = int(metrics.get("usage_count", 0)) <= 1
    low_verified_utility = int(metrics.get("verified_success_count", 0)) == 0
    strong_reasons = [
        name
        for name, enabled in (
            ("replacement", replacement_exists),
            ("deprecated-technology", deprecated_technology),
            ("persistent-router-confusion", persistent_router_confusion),
        )
        if enabled
    ]
    if strong_reasons:
        return ArchiveReview("REVIEW", ", ".join(strong_reasons))
    if low_usage and low_verified_utility and int(metrics.get("verified_failure_count", 0)) > 0:
        return ArchiveReview("REVIEW", "low usage + no verified success + verified failure")
    return ArchiveReview("NO_ACTION", "low usage/time alone never auto-archives a Skill")


def _validate_delta(delta: dict[str, list[str]], label: str) -> dict[str, list[str]]:
    if set(delta) != {"add", "remove"}:
        raise CuratorError(f"{label} must contain add/remove")
    for key in ("add", "remove"):
        if not isinstance(delta[key], list) or not all(isinstance(item, str) and item.strip() for item in delta[key]):
            raise CuratorError(f"{label}.{key} must be a string list")
    return {"add": list(delta["add"]), "remove": list(delta["remove"])}


def validate_trigger_maintenance(
    *,
    change_type: str,
    base_triggers: list[str],
    trigger_delta: dict[str, list[str]],
    positive_cases: list[str],
    negative_cases: list[str],
) -> None:
    if change_type not in {"trigger-narrow", "trigger-expand"}:
        raise CuratorError("trigger maintenance requires trigger-narrow or trigger-expand")
    delta = _validate_delta(trigger_delta, "trigger_delta")
    if not positive_cases or not negative_cases:
        raise CuratorError("trigger maintenance requires positive 1+ and negative 1+ regression cases")
    base = {item.casefold() for item in base_triggers}
    if change_type == "trigger-narrow":
        if delta["add"] or not delta["remove"]:
            raise CuratorError("trigger-narrow must remove at least one trigger and add none")
        if any(item.casefold() not in base for item in delta["remove"]):
            raise CuratorError("trigger-narrow can remove only existing triggers")
    else:
        if delta["remove"] or not delta["add"]:
            raise CuratorError("trigger-expand must add at least one trigger and remove none")
        if any(item.casefold() in base for item in delta["add"]):
            raise CuratorError("trigger-expand must add new triggers")


def build_curator_proposal(
    *,
    proposal_id: str,
    change_type: str,
    skill_id: str,
    base_version: int,
    base_hash: str,
    reason: str,
    evidence_refs: list[str],
    source_id: str,
    license_name: str,
    provenance: str,
    trigger_delta: dict[str, list[str]] | None = None,
    permission_delta: dict[str, list[str]] | None = None,
    related_skill_ids: list[str] | None = None,
    protection: dict[str, bool] | None = None,
) -> dict[str, Any]:
    if change_type not in SUPPORTED_TYPES:
        raise CuratorError(f"unsupported Curator change_type: {change_type}")
    if change_type == "delete":
        raise CuratorError("automatic delete is not supported in V8.2")
    if not SKILL_ID.fullmatch(skill_id):
        raise CuratorError("skill_id must be kebab-case")
    if not SAFE_PROPOSAL_ID.fullmatch(proposal_id):
        raise CuratorError("proposal_id contains unsafe path characters")

    trigger = _validate_delta(trigger_delta or {"add": [], "remove": []}, "trigger_delta")
    permission = _validate_delta(permission_delta or {"add": [], "remove": []}, "permission_delta")
    if change_type == "archive":
        protected = sorted(key for key in PROTECTION_KEYS if (protection or {}).get(key))
        if protected:
            raise CuratorError("protected Skill cannot receive archive proposal: " + ", ".join(protected))
        if not evidence_refs:
            raise CuratorError("archive proposal requires evidence beyond age/low usage")

    requires_human_gate = (
        change_type in STRUCTURAL_HUMAN_GATE_TYPES
        or bool(trigger["add"])
        or bool(permission["add"])
    )
    proposal = {
        "proposal_id": proposal_id,
        "change_type": change_type,
        "skill_id": skill_id,
        "base_version": base_version,
        "base_hash": base_hash,
        "proposed_version": base_version + 1,
        "reason": reason,
        "evidence_refs": list(evidence_refs),
        "trigger_delta": trigger,
        "permission_delta": permission,
        "requires_human_gate": requires_human_gate,
        "status": "candidate",
        "source_id": source_id,
        "license": license_name,
        "provenance": provenance,
        "related_skill_ids": list(related_skill_ids or []),
        "auto_promote_allowed": False if change_type in {"split", "merge", "archive", "trigger-expand"} else None,
    }
    try:
        validate_proposal(proposal)
    except ProposalError as exc:
        raise CuratorError(str(exc)) from exc
    return proposal


def _state_candidate_dir(state_root: Path, proposal_id: str) -> Path:
    state_root = state_root.resolve()
    if state_root.name != ".playbook-state":
        raise CuratorError("Curator Candidate state_root must be a .playbook-state directory")
    if not SAFE_PROPOSAL_ID.fullmatch(proposal_id):
        raise CuratorError("unsafe proposal_id")
    return state_root / "candidates" / proposal_id


def _safe_reference_path(candidate_dir: Path, relative: str) -> Path:
    path = (candidate_dir / relative).resolve()
    try:
        path.relative_to(candidate_dir.resolve())
    except ValueError as exc:
        raise CuratorError("reference extraction path escapes Candidate package") from exc
    if not relative.replace("\\", "/").startswith("references/") or path.suffix.casefold() != ".md":
        raise CuratorError("extracted reference must be references/*.md")
    return path


def create_package_candidate(
    *,
    state_root: Path,
    active_dir: Path,
    proposal: dict[str, Any],
    operations: list[dict[str, str]],
    positive_cases: list[str],
    negative_cases: list[str],
) -> Path:
    """Create compress/extract-reference Candidate without changing ACTIVE."""
    validate_proposal(proposal)
    change_type = proposal["change_type"]
    if change_type not in PACKAGE_TYPES:
        raise CuratorError("package Candidate supports compress/extract-reference only")
    if package_hash(active_dir) != proposal["base_hash"]:
        raise CuratorError("proposal base_hash does not match ACTIVE package")
    if not operations:
        raise CuratorError("package Candidate requires at least one structural operation")
    if not positive_cases or not negative_cases:
        raise CuratorError("package Candidate requires positive 1+ and negative 1+ regression cases")

    candidate_dir = _state_candidate_dir(state_root, proposal["proposal_id"])
    if candidate_dir.exists():
        raise CuratorError(f"candidate already exists: {candidate_dir}")
    candidate_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(active_dir, candidate_dir)
    try:
        skill_file = candidate_dir / "SKILL.md"
        content = skill_file.read_text(encoding="utf-8")
        for operation in operations:
            old = operation.get("old", "")
            if not old or content.count(old) != 1:
                raise CuratorError("each structural operation old text must match exactly once")
            if change_type == "compress":
                new = operation.get("new", "")
                if len(new) >= len(old):
                    raise CuratorError("compress operation must reduce content")
                content = content.replace(old, new, 1)
            else:
                relative = operation.get("reference_path", "")
                title = operation.get("title", "Detailed reference").strip() or "Detailed reference"
                target = _safe_reference_path(candidate_dir, relative)
                target.parent.mkdir(parents=True, exist_ok=True)
                if target.exists():
                    raise CuratorError(f"reference target already exists: {relative}")
                target.write_text(old.rstrip() + "\n", encoding="utf-8", newline="\n")
                content = content.replace(old, f"[{title}]({relative.replace(chr(92), '/')})", 1)
        skill_file.write_text(content, encoding="utf-8", newline="\n")

        (candidate_dir / "proposal.json").write_text(
            json.dumps(proposal, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        preserved_fixture = "tests/routing.json" if (candidate_dir / "tests" / "routing.json").is_file() else None
        routing = {
            "schema_version": 1,
            "skill_id": proposal["skill_id"],
            "positive": list(positive_cases),
            "negative": list(negative_cases),
            "preserved_fixture": preserved_fixture,
        }
        (candidate_dir / "routing.json").write_text(
            json.dumps(routing, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    except Exception:
        shutil.rmtree(candidate_dir, ignore_errors=True)
        raise
    return candidate_dir
