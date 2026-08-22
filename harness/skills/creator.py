#!/usr/bin/env python3
"""Deterministic Skill Creator boundary for V8.2.

The Creator never mutates the ACTIVE library. It consumes structured, reviewed
inputs and writes only runtime candidates under .playbook-state/candidates.
"""

from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from gap_detector import matching_gap_events
from proposal import ProposalError, validate_proposal

SKILL_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
HIGH_RISK_PERMISSIONS = {
    "network",
    "credential_access",
    "external_write",
    "database_write",
    "destructive",
    "production",
}
FORBIDDEN_SOURCE_LICENSE = {"", "unknown", "unverified", "unspecified"}


class CreatorError(ValueError):
    """Raised when a Skill Candidate request is invalid or unsafe."""


@dataclass(frozen=True)
class Eligibility:
    action: str
    reason: str


REQUIRED_SPEC_FIELDS = {
    "proposal_id",
    "skill_id",
    "description",
    "purpose",
    "workflow",
    "triggers",
    "permissions",
    "positive_cases",
    "negative_cases",
    "source_id",
    "license",
    "provenance",
    "domain_hypothesis",
}


def creator_eligibility(
    *,
    router_selected_ids: list[str],
    nearby_skill_ids: list[str],
    gap_event_count: int,
    reusable_workflow: bool,
    repository_specific_one_off: bool,
    positive_cases: list[str],
    negative_cases: list[str],
) -> Eligibility:
    """Conservative gate: one Router miss never creates a Skill."""
    if router_selected_ids:
        return Eligibility("NO_ACTION", "existing Skill/capability already selected")
    if repository_specific_one_off:
        return Eligibility("NO_ACTION", "repository-specific one-off belongs in repository guidance")
    if not reusable_workflow:
        return Eligibility("NO_ACTION", "workflow is not reusable")
    if nearby_skill_ids:
        return Eligibility("NO_ACTION", "nearby Skill exists; evaluate minimal extension before new Skill")
    if gap_event_count < 2:
        return Eligibility("WAIT", "at least two matching Gap Events are required")
    if len(positive_cases) < 2 or len(negative_cases) < 1:
        return Eligibility("WAIT", "candidate requires at least two positive and one negative routing cases")
    return Eligibility("CREATE_CANDIDATE", "repeated reusable gap with minimum routing evidence")


def validate_creator_spec(spec: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(spec, dict):
        raise CreatorError("creator spec must be an object")
    missing = REQUIRED_SPEC_FIELDS - spec.keys()
    if missing:
        raise CreatorError("creator spec missing fields: " + ", ".join(sorted(missing)))

    for key in ("proposal_id", "skill_id", "description", "purpose", "source_id", "license", "provenance", "domain_hypothesis"):
        if not isinstance(spec.get(key), str) or not spec[key].strip():
            raise CreatorError(f"{key} must be a non-empty string")
    if not SKILL_ID.fullmatch(spec["skill_id"]):
        raise CreatorError("skill_id must be kebab-case")

    for key in ("workflow", "triggers", "permissions", "positive_cases", "negative_cases"):
        value = spec.get(key)
        if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
            raise CreatorError(f"{key} must be a string list")
    if not spec["workflow"]:
        raise CreatorError("workflow must not be empty")
    if len(spec["positive_cases"]) < 2 or len(spec["negative_cases"]) < 1:
        raise CreatorError("routing fixtures require positive 2+ and negative 1+")

    if spec["source_id"].strip().casefold() in FORBIDDEN_SOURCE_LICENSE:
        raise CreatorError("source_id must be known before candidate creation")
    if spec["license"].strip().casefold() in FORBIDDEN_SOURCE_LICENSE:
        raise CreatorError("license must be known before candidate creation")
    return spec


def _skill_markdown(spec: dict[str, Any]) -> str:
    workflow = "\n".join(f"{index}. {step}" for index, step in enumerate(spec["workflow"], start=1))
    permissions = ", ".join(spec["permissions"]) or "local_read only / no additional permission"
    return f'''---
name: {spec["skill_id"]}
description: >-
  {spec["description"]}
---

# {spec["skill_id"]}

## Purpose / Scope

{spec["purpose"]}

## When to use

Use this Skill only when the task matches the candidate routing fixtures and the workflow is reusable across repositories.

## When not to use

Do not use for one-off repository conventions, trivial edits, or when an existing Skill is sufficient.

## Workflow

{workflow}

## Evidence

Record concrete inputs, commands/checks performed, outputs, and verification results. Do not report PASS from model self-assessment alone.

## Permissions

Declared candidate permissions: {permissions}.

## Stop / Handoff

Stop and request review when required evidence is unavailable, permissions would expand, an external write/destructive action is needed, or the candidate conflicts with an existing Skill contract.

## Source / Provenance

- source_id: `{spec["source_id"]}`
- license: `{spec["license"]}`
- provenance: {spec["provenance"]}
- status: runtime Candidate only; not ACTIVE
'''


def build_proposal(spec: dict[str, Any], *, evidence_refs: list[str]) -> dict[str, Any]:
    requires_human_gate = bool(set(spec["permissions"]) & HIGH_RISK_PERMISSIONS) or bool(spec["triggers"])
    proposal = {
        "proposal_id": spec["proposal_id"],
        "change_type": "create",
        "skill_id": spec["skill_id"],
        "base_version": 0,
        "base_hash": "",
        "proposed_version": 1,
        "reason": "Repeated reusable capability gap with minimum routing evidence",
        "evidence_refs": list(evidence_refs),
        "trigger_delta": {"add": list(spec["triggers"]), "remove": []},
        "permission_delta": {"add": list(spec["permissions"]), "remove": []},
        "requires_human_gate": requires_human_gate,
        "status": "candidate",
        "source_id": spec["source_id"],
        "license": spec["license"],
        "provenance": spec["provenance"],
    }
    try:
        validate_proposal(proposal)
    except ProposalError as exc:
        raise CreatorError(str(exc)) from exc
    return proposal


def create_candidate(
    *,
    state_root: Path,
    spec: dict[str, Any],
    events: list[dict[str, Any]],
    router_selected_ids: list[str] | None = None,
    nearby_skill_ids: list[str] | None = None,
    reusable_workflow: bool = True,
    repository_specific_one_off: bool = False,
) -> dict[str, Any]:
    """Create a runtime candidate package after deterministic eligibility checks."""
    spec = validate_creator_spec(spec)
    matches = matching_gap_events(events, domain_hypothesis=spec["domain_hypothesis"])
    eligibility = creator_eligibility(
        router_selected_ids=router_selected_ids or [],
        nearby_skill_ids=nearby_skill_ids or [],
        gap_event_count=len(matches),
        reusable_workflow=reusable_workflow,
        repository_specific_one_off=repository_specific_one_off,
        positive_cases=spec["positive_cases"],
        negative_cases=spec["negative_cases"],
    )
    if eligibility.action != "CREATE_CANDIDATE":
        return {"result": eligibility.action, "reason": eligibility.reason, "candidate_path": None}

    evidence_refs = [str(event["event_id"]) for event in matches]
    proposal = build_proposal(spec, evidence_refs=evidence_refs)
    candidate_dir = state_root / "candidates" / spec["proposal_id"]
    if candidate_dir.exists():
        raise CreatorError(f"candidate already exists: {candidate_dir}")

    candidate_dir.mkdir(parents=True, exist_ok=False)
    try:
        (candidate_dir / "SKILL.md").write_text(_skill_markdown(spec), encoding="utf-8", newline="\n")
        (candidate_dir / "proposal.json").write_text(
            json.dumps(proposal, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        routing = {
            "schema_version": 1,
            "skill_id": spec["skill_id"],
            "positive": list(spec["positive_cases"]),
            "negative": list(spec["negative_cases"]),
        }
        (candidate_dir / "routing.json").write_text(
            json.dumps(routing, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    except Exception:
        shutil.rmtree(candidate_dir, ignore_errors=True)
        raise

    return {
        "result": "CANDIDATE_CREATED",
        "reason": eligibility.reason,
        "candidate_path": str(candidate_dir),
        "proposal": proposal,
    }
