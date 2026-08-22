#!/usr/bin/env python3
"""Proposal schema and deterministic delta helpers for V8.2 Skill governance."""

from __future__ import annotations

from typing import Any

CHANGE_TYPES = {
    "create",
    "modify",
    "compress",
    "extract-reference",
    "trigger-narrow",
    "trigger-expand",
    "permission-expand",
    "split",
    "merge",
    "archive",
    "restore",
    "core-promote",
    "core-demote",
    "executable-resource-add",
}
PROPOSAL_STATUSES = {
    "candidate",
    "validating",
    "waiting_for_analysis",
    "approved",
    "rejected",
    "blocked",
    "promoted",
}
HUMAN_GATE_CHANGE_TYPES = {
    "trigger-expand",
    "permission-expand",
    "split",
    "merge",
    "archive",
    "core-promote",
    "core-demote",
    "executable-resource-add",
}
REQUIRED_FIELDS = {
    "proposal_id",
    "change_type",
    "skill_id",
    "base_version",
    "base_hash",
    "proposed_version",
    "reason",
    "evidence_refs",
    "trigger_delta",
    "permission_delta",
    "requires_human_gate",
    "status",
}


class ProposalError(ValueError):
    """Raised when a Skill change proposal is malformed or unsafe."""


def _string_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) and item.strip() for item in value)


def _delta(value: Any, label: str) -> dict[str, list[str]]:
    if not isinstance(value, dict):
        raise ProposalError(f"{label} must be an object")
    if set(value) != {"add", "remove"}:
        raise ProposalError(f"{label} must contain exactly add/remove")
    if not _string_list(value["add"]) or not _string_list(value["remove"]):
        raise ProposalError(f"{label} add/remove must be string lists")
    return {"add": list(value["add"]), "remove": list(value["remove"])}


def permission_delta(base: list[str], candidate: list[str]) -> dict[str, list[str]]:
    return {
        "add": sorted(set(candidate) - set(base)),
        "remove": sorted(set(base) - set(candidate)),
    }


def trigger_delta(base: list[str], candidate: list[str]) -> dict[str, list[str]]:
    base_norm = {item.casefold(): item for item in base}
    candidate_norm = {item.casefold(): item for item in candidate}
    return {
        "add": sorted(candidate_norm[key] for key in candidate_norm.keys() - base_norm.keys()),
        "remove": sorted(base_norm[key] for key in base_norm.keys() - candidate_norm.keys()),
    }


def validate_proposal(data: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ProposalError("proposal must be an object")
    missing = REQUIRED_FIELDS - data.keys()
    if missing:
        raise ProposalError(f"proposal missing fields: {', '.join(sorted(missing))}")

    for key in ("proposal_id", "skill_id", "reason"):
        if not isinstance(data.get(key), str) or not data[key].strip():
            raise ProposalError(f"{key} must be a non-empty string")

    if data["change_type"] not in CHANGE_TYPES:
        raise ProposalError(f"unsupported change_type: {data['change_type']}")
    if data["status"] not in PROPOSAL_STATUSES:
        raise ProposalError(f"unsupported proposal status: {data['status']}")

    base_version = data["base_version"]
    proposed_version = data["proposed_version"]
    if not isinstance(base_version, int) or isinstance(base_version, bool) or base_version < 0:
        raise ProposalError("base_version must be an integer >= 0")
    if not isinstance(proposed_version, int) or isinstance(proposed_version, bool) or proposed_version < 1:
        raise ProposalError("proposed_version must be an integer >= 1")
    if data["change_type"] != "create" and proposed_version <= base_version:
        raise ProposalError("modified Skill proposed_version must exceed base_version")
    if data["change_type"] == "create" and base_version != 0:
        raise ProposalError("created Skill base_version must be 0")

    base_hash = data["base_hash"]
    if not isinstance(base_hash, str):
        raise ProposalError("base_hash must be a string")
    if data["change_type"] != "create" and not base_hash.strip():
        raise ProposalError("non-create proposal requires base_hash")

    if not _string_list(data["evidence_refs"]):
        raise ProposalError("evidence_refs must be a string list")
    trigger = _delta(data["trigger_delta"], "trigger_delta")
    permission = _delta(data["permission_delta"], "permission_delta")

    if not isinstance(data["requires_human_gate"], bool):
        raise ProposalError("requires_human_gate must be boolean")

    required_gate = (
        data["change_type"] in HUMAN_GATE_CHANGE_TYPES
        or bool(trigger["add"])
        or bool(permission["add"])
    )
    if required_gate and not data["requires_human_gate"]:
        raise ProposalError("proposal expands structure/trigger/permission but human gate is false")

    return data
