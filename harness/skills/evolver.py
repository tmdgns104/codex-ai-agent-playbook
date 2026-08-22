#!/usr/bin/env python3
"""Deterministic V8.2 Skill Evolver boundary.

The Evolver never edits ACTIVE content in place. It creates a bounded runtime
Candidate from repeated privacy-safe evidence, then delegates promotion to the
existing Governance gate.
"""

from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from events import normalize_issue_code, validate_event
from locking import acquire_lock, release_lock
from promotion import PromotionError, load_protected_regressions, package_hash, promote_package
from proposal import ProposalError, validate_proposal

RELEVANT_EVENT_TYPES = {
    "verification_failure",
    "user_correction",
    "routing_false_positive",
    "routing_false_negative",
}
UNKNOWN_SOURCE_VALUES = {"", "unknown", "unverified", "unspecified"}
METADATA_FILES = {"proposal.json", "routing.json"}


class EvolutionError(ValueError):
    """Raised when an evolution request violates the bounded-change contract."""


@dataclass(frozen=True)
class EvolutionEligibility:
    action: str
    reason: str


REQUIRED_SPEC_FIELDS = {
    "proposal_id",
    "skill_id",
    "base_version",
    "observed_pattern",
    "root_cause",
    "expected_behavior",
    "edits",
    "positive_regressions",
    "negative_regressions",
    "trigger_add",
    "trigger_remove",
    "permission_add",
    "permission_remove",
    "source_id",
    "license",
    "provenance",
}


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise EvolutionError(f"required file missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise EvolutionError(f"invalid JSON: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise EvolutionError(f"JSON root must be an object: {path}")
    return value


def _policy(root: Path) -> dict[str, Any]:
    policy = _json(root / "capability-library" / "governance" / "policy.json")
    if policy.get("schema_version") != 1:
        raise EvolutionError("governance policy schema_version must be 1")
    return policy


def _registry_skill(root: Path, skill_id: str) -> dict[str, Any]:
    registry = _json(root / "capability-library" / "registry.json")
    for item in registry.get("capabilities", []):
        if isinstance(item, dict) and item.get("id") == skill_id and item.get("type") == "skill":
            return item
    raise EvolutionError(f"ACTIVE Skill not found in registry: {skill_id}")


def matching_evidence(
    events: list[dict[str, Any]],
    *,
    skill_id: str,
    issue_code: str | None = None,
) -> list[dict[str, Any]]:
    """Return distinct-task evidence for one Skill/problem bucket."""
    wanted_issue = normalize_issue_code(issue_code) if issue_code else None
    by_fingerprint: dict[str, dict[str, Any]] = {}
    for event in events:
        validate_event(event)
        if event["event_type"] not in RELEVANT_EVENT_TYPES:
            continue
        if skill_id not in event.get("skill_ids", []):
            continue
        if wanted_issue and normalize_issue_code(event.get("issue_code")) != wanted_issue:
            continue
        by_fingerprint.setdefault(event["task_fingerprint"], event)
    return sorted(by_fingerprint.values(), key=lambda item: str(item["event_id"]))


def evolution_eligibility(
    evidence: list[dict[str, Any]],
    *,
    severe_safety_or_correctness: bool = False,
    min_distinct_evidence: int = 2,
) -> EvolutionEligibility:
    if not evidence:
        return EvolutionEligibility("NO_ACTION", "no matching verified problem evidence")
    if len(evidence) < min_distinct_evidence:
        if severe_safety_or_correctness:
            return EvolutionEligibility("REVIEW", "single severe signal requires review but not automatic evolution")
        return EvolutionEligibility("WAIT", "normal evolution requires repeated distinct evidence")
    return EvolutionEligibility("CREATE_CANDIDATE", "repeated evidence qualifies for bounded evolution")


def _string_list(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        raise EvolutionError(f"{label} must be a string list")
    return list(value)


def validate_evolution_spec(spec: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(spec, dict):
        raise EvolutionError("evolution spec must be an object")
    missing = REQUIRED_SPEC_FIELDS - spec.keys()
    if missing:
        raise EvolutionError("evolution spec missing fields: " + ", ".join(sorted(missing)))

    for key in (
        "proposal_id",
        "skill_id",
        "observed_pattern",
        "root_cause",
        "expected_behavior",
        "source_id",
        "license",
        "provenance",
    ):
        if not isinstance(spec.get(key), str) or not spec[key].strip():
            raise EvolutionError(f"{key} must be a non-empty string")

    if not isinstance(spec["base_version"], int) or isinstance(spec["base_version"], bool) or spec["base_version"] < 1:
        raise EvolutionError("base_version must be an integer >= 1")

    for key in ("positive_regressions", "negative_regressions", "trigger_add", "trigger_remove", "permission_add", "permission_remove"):
        _string_list(spec[key], key)
    if not spec["positive_regressions"] or not spec["negative_regressions"]:
        raise EvolutionError("evolution requires at least one positive and one negative regression")

    edits = spec.get("edits")
    if not isinstance(edits, list) or not edits:
        raise EvolutionError("edits must be a non-empty list")
    for index, edit in enumerate(edits, start=1):
        if not isinstance(edit, dict) or set(edit) != {"old", "new", "reason"}:
            raise EvolutionError(f"edit {index} must contain exactly old/new/reason")
        for key in ("old", "new", "reason"):
            if not isinstance(edit[key], str) or not edit[key].strip():
                raise EvolutionError(f"edit {index} {key} must be a non-empty string")
        if edit["old"] == edit["new"]:
            raise EvolutionError(f"edit {index} does not change content")

    if spec["source_id"].strip().casefold() in UNKNOWN_SOURCE_VALUES:
        raise EvolutionError("source_id must be known")
    if spec["license"].strip().casefold() in UNKNOWN_SOURCE_VALUES:
        raise EvolutionError("license must be known")
    return spec


def apply_bounded_edits(
    content: str,
    edits: list[dict[str, str]],
    *,
    max_edits: int,
    max_changed_fraction: float,
) -> str:
    if len(edits) > max_edits:
        raise EvolutionError(f"evolution exceeds max content edits: {len(edits)} > {max_edits}")
    if not (0 < max_changed_fraction <= 1):
        raise EvolutionError("evolution_max_changed_fraction must be within (0, 1]")

    changed_weight = 0
    result = content
    for index, edit in enumerate(edits, start=1):
        old = edit["old"]
        new = edit["new"]
        occurrences = result.count(old)
        if occurrences != 1:
            raise EvolutionError(f"edit {index} old text must match exactly once; found {occurrences}")
        changed_weight += max(len(old), len(new))
        result = result.replace(old, new, 1)

    baseline = max(len(content), 1)
    fraction = changed_weight / baseline
    if fraction > max_changed_fraction:
        raise EvolutionError(
            f"evolution change is too broad: {fraction:.3f} > {max_changed_fraction:.3f}"
        )
    return result


def _proposal(
    spec: dict[str, Any],
    *,
    base_hash: str,
    evidence_refs: list[str],
) -> dict[str, Any]:
    trigger_delta = {"add": list(spec["trigger_add"]), "remove": list(spec["trigger_remove"])}
    permission_delta = {"add": list(spec["permission_add"]), "remove": list(spec["permission_remove"])}
    requires_human_gate = bool(trigger_delta["add"] or permission_delta["add"])
    proposal = {
        "proposal_id": spec["proposal_id"],
        "change_type": "modify",
        "skill_id": spec["skill_id"],
        "base_version": spec["base_version"],
        "base_hash": base_hash,
        "proposed_version": spec["base_version"] + 1,
        "reason": spec["observed_pattern"],
        "evidence_refs": evidence_refs,
        "trigger_delta": trigger_delta,
        "permission_delta": permission_delta,
        "requires_human_gate": requires_human_gate,
        "status": "candidate",
        "source_id": spec["source_id"],
        "license": spec["license"],
        "provenance": spec["provenance"],
        "observed_pattern": spec["observed_pattern"],
        "root_cause": spec["root_cause"],
        "expected_behavior": spec["expected_behavior"],
    }
    try:
        validate_proposal(proposal)
    except ProposalError as exc:
        raise EvolutionError(str(exc)) from exc
    if not evidence_refs:
        raise EvolutionError("modify proposal requires evidence_refs")
    return proposal


def create_evolution_candidate(
    *,
    root: Path,
    state_root: Path,
    spec: dict[str, Any],
    events: list[dict[str, Any]],
    issue_code: str | None = None,
    severe_safety_or_correctness: bool = False,
) -> dict[str, Any]:
    """Create candidate vN+1 without mutating ACTIVE vN."""
    root = root.resolve()
    state_root = state_root.resolve()
    if state_root.name != ".playbook-state":
        raise EvolutionError("state_root must be a .playbook-state directory")
    spec = validate_evolution_spec(spec)
    policy = _policy(root)
    max_edits = int(policy.get("evolution_max_content_edits", 2))
    max_fraction = float(policy.get("evolution_max_changed_fraction", 0.35))
    min_evidence = int(policy.get("evolution_min_distinct_evidence", 2))

    registry_item = _registry_skill(root, spec["skill_id"])
    active_dir = (root / str(registry_item["path"])).resolve()
    if not active_dir.is_dir():
        raise EvolutionError(f"ACTIVE Skill package missing: {active_dir}")

    evidence = matching_evidence(events, skill_id=spec["skill_id"], issue_code=issue_code)
    eligibility = evolution_eligibility(
        evidence,
        severe_safety_or_correctness=severe_safety_or_correctness,
        min_distinct_evidence=min_evidence,
    )
    if eligibility.action != "CREATE_CANDIDATE":
        return {"result": eligibility.action, "reason": eligibility.reason, "candidate_path": None}

    active_skill = active_dir / "SKILL.md"
    if not active_skill.is_file():
        raise EvolutionError("ACTIVE Skill is missing SKILL.md")
    before = active_skill.read_text(encoding="utf-8")
    after = apply_bounded_edits(
        before,
        spec["edits"],
        max_edits=max_edits,
        max_changed_fraction=max_fraction,
    )
    if before == after:
        raise EvolutionError("evolution produced no content change")

    current_hash = package_hash(active_dir)
    proposal = _proposal(
        spec,
        base_hash=current_hash,
        evidence_refs=[str(item["event_id"]) for item in evidence],
    )

    candidate_dir = state_root / "candidates" / spec["proposal_id"]
    if candidate_dir.exists():
        raise EvolutionError(f"candidate already exists: {candidate_dir}")
    candidate_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(active_dir, candidate_dir)
    try:
        (candidate_dir / "SKILL.md").write_text(after, encoding="utf-8", newline="\n")
        (candidate_dir / "proposal.json").write_text(
            json.dumps(proposal, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        preserved_fixture = candidate_dir / "tests" / "routing.json"
        routing = {
            "schema_version": 1,
            "skill_id": spec["skill_id"],
            "positive": list(spec["positive_regressions"]),
            "negative": list(spec["negative_regressions"]),
            "preserved_fixture": "tests/routing.json" if preserved_fixture.is_file() else None,
        }
        (candidate_dir / "routing.json").write_text(
            json.dumps(routing, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    except Exception:
        shutil.rmtree(candidate_dir, ignore_errors=True)
        raise

    if active_skill.read_text(encoding="utf-8") != before:
        raise EvolutionError("ACTIVE Skill changed during candidate creation")
    return {
        "result": "CANDIDATE_CREATED",
        "reason": eligibility.reason,
        "candidate_path": str(candidate_dir),
        "proposal": proposal,
    }


def _append_history(state_root: Path, record: dict[str, Any]) -> None:
    history = state_root / "history" / "promotion-history.jsonl"
    history.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, ensure_ascii=False, sort_keys=True)
    with history.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(line + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def promote_evolution_candidate(
    *,
    root: Path,
    state_root: Path,
    candidate_dir: Path,
    validation_passed: bool,
    protected_regression_passed: bool,
    human_gate_approved: bool = False,
    timestamp: str | None = None,
) -> str:
    """Promote only package content, preserving proposal/routing as runtime metadata."""
    root = root.resolve()
    state_root = state_root.resolve()
    candidate_dir = candidate_dir.resolve()
    proposal = _json(candidate_dir / "proposal.json")
    try:
        validate_proposal(proposal)
    except ProposalError as exc:
        raise EvolutionError(str(exc)) from exc
    if proposal.get("change_type") != "modify":
        raise EvolutionError("evolution promotion requires change_type=modify")
    if not protected_regression_passed:
        raise PromotionError("protected regression did not PASS")
    load_protected_regressions(root)

    registry_item = _registry_skill(root, str(proposal["skill_id"]))
    active_dir = (root / str(registry_item["path"])).resolve()
    if proposal.get("trigger_delta", {}).get("add") or proposal.get("trigger_delta", {}).get("remove"):
        raise PromotionError("registry trigger delta requires lifecycle integration; package-only promotion blocked")
    if proposal.get("permission_delta", {}).get("add") or proposal.get("permission_delta", {}).get("remove"):
        raise PromotionError("registry permission delta requires lifecycle integration; package-only promotion blocked")

    token = acquire_lock(state_root, str(proposal["skill_id"]))
    stage = state_root / "promotion-stage" / str(proposal["proposal_id"])
    try:
        if stage.exists():
            shutil.rmtree(stage)
        stage.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(candidate_dir, stage, ignore=shutil.ignore_patterns(*METADATA_FILES))
        new_hash = promote_package(
            active_dir,
            stage,
            expected_base_hash=str(proposal["base_hash"]),
            validation_passed=validation_passed,
            requires_human_gate=bool(proposal["requires_human_gate"]),
            human_gate_approved=human_gate_approved,
        )
        _append_history(
            state_root,
            {
                "proposal_id": proposal["proposal_id"],
                "skill_id": proposal["skill_id"],
                "base_hash": proposal["base_hash"],
                "new_hash": new_hash,
                "base_version": proposal["base_version"],
                "promoted_version": proposal["proposed_version"],
                "evidence_refs": proposal["evidence_refs"],
                "status": "promoted",
                "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
            },
        )
        return new_hash
    finally:
        shutil.rmtree(stage, ignore_errors=True)
        release_lock(state_root, str(proposal["skill_id"]), token)
