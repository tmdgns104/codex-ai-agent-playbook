#!/usr/bin/env python3
"""Deterministic lifecycle validation for V8.2 self-managing Skills."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

VALID_STATES = {
    "candidate",
    "validating",
    "active",
    "review_required",
    "rejected",
    "stale",
    "archived",
}


class LifecycleError(ValueError):
    """Raised when lifecycle state or transition data is invalid."""


def load_lifecycle(root: Path) -> dict[str, Any]:
    path = root / "capability-library" / "governance" / "lifecycle.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise LifecycleError(f"lifecycle file missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise LifecycleError(f"invalid lifecycle JSON: {exc}") from exc
    validate_lifecycle_document(data)
    return data


def validate_lifecycle_document(data: dict[str, Any]) -> None:
    if not isinstance(data, dict):
        raise LifecycleError("lifecycle must be a JSON object")
    if data.get("schema_version") != 1:
        raise LifecycleError("lifecycle schema_version must be 1")

    states = data.get("states")
    if not isinstance(states, list) or set(states) != VALID_STATES:
        raise LifecycleError("lifecycle states do not match the V8.2 contract")

    transitions = data.get("transitions")
    if not isinstance(transitions, dict):
        raise LifecycleError("lifecycle transitions must be an object")
    for state in VALID_STATES:
        targets = transitions.get(state)
        if not isinstance(targets, list):
            raise LifecycleError(f"missing transition list for state: {state}")
        unknown = set(targets) - VALID_STATES
        if unknown:
            raise LifecycleError(f"unknown transition target(s) for {state}: {sorted(unknown)}")

    if data.get("active_is_immutable_during_validation") is not True:
        raise LifecycleError("ACTIVE immutability contract must remain enabled")

    skills = data.get("skills")
    if not isinstance(skills, dict):
        raise LifecycleError("lifecycle skills must be an object")
    for skill_id, entry in skills.items():
        if not isinstance(skill_id, str) or not skill_id:
            raise LifecycleError("lifecycle skill id must be non-empty")
        if not isinstance(entry, dict):
            raise LifecycleError(f"lifecycle entry must be an object: {skill_id}")
        state = entry.get("state")
        if state not in VALID_STATES:
            raise LifecycleError(f"invalid lifecycle state for {skill_id}: {state}")
        version = entry.get("version")
        if not isinstance(version, int) or isinstance(version, bool) or version < 1:
            raise LifecycleError(f"invalid lifecycle version for {skill_id}: {version}")
        active_hash = entry.get("active_hash")
        if state == "active" and (not isinstance(active_hash, str) or not active_hash.strip()):
            raise LifecycleError(f"active lifecycle entry requires active_hash: {skill_id}")


def validate_transition(data: dict[str, Any], from_state: str, to_state: str) -> None:
    validate_lifecycle_document(data)
    if from_state not in VALID_STATES or to_state not in VALID_STATES:
        raise LifecycleError(f"unknown lifecycle transition: {from_state} -> {to_state}")
    allowed = data["transitions"][from_state]
    if to_state not in allowed:
        raise LifecycleError(f"invalid lifecycle transition: {from_state} -> {to_state}")


def can_transition(data: dict[str, Any], from_state: str, to_state: str) -> bool:
    try:
        validate_transition(data, from_state, to_state)
    except LifecycleError:
        return False
    return True
