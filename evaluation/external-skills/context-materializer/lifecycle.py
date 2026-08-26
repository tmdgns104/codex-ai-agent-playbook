"""Deterministic lifecycle rules for session-local adapted context artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


LIFECYCLE_VERSION = "v8.4-context-lifecycle-1"
STATES = (
    "CREATED",
    "VALIDATED",
    "MATERIALIZED",
    "READY",
    "CLEANUP_PENDING",
    "CLEANED",
    "QUARANTINED",
    "INVALIDATED",
)
ALLOWED_TRANSITIONS = {
    "CREATED": {"VALIDATED", "INVALIDATED", "QUARANTINED"},
    "VALIDATED": {"MATERIALIZED", "INVALIDATED", "QUARANTINED"},
    "MATERIALIZED": {"READY", "INVALIDATED", "QUARANTINED"},
    "READY": {"CLEANUP_PENDING", "INVALIDATED", "QUARANTINED"},
    "CLEANUP_PENDING": {"CLEANED", "QUARANTINED"},
    "INVALIDATED": {"QUARANTINED"},
    "CLEANED": set(),
    "QUARANTINED": set(),
}


class LifecycleError(ValueError):
    """Raised when a state document or transition violates the frozen model."""


@dataclass(frozen=True)
class Transition:
    sequence: int
    from_state_or_null: str | None
    to_state: str
    reason: str
    timestamp_utc: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "sequence": self.sequence,
            "from_state_or_null": self.from_state_or_null,
            "to_state": self.to_state,
            "reason": self.reason,
            "timestamp_utc": self.timestamp_utc,
        }


def create_lifecycle(session_id: str, timestamp_utc: str) -> dict[str, Any]:
    """Create the first immutable-in-meaning lifecycle checkpoint."""
    return {
        "schema_version": 1,
        "lifecycle_version": LIFECYCLE_VERSION,
        "session_id": session_id,
        "state": "CREATED",
        "transition_log": [
            Transition(1, None, "CREATED", "SESSION_CREATED", timestamp_utc).as_dict()
        ],
    }


def validate_lifecycle(document: dict[str, Any]) -> None:
    if document.get("schema_version") != 1:
        raise LifecycleError("unsupported lifecycle schema")
    if document.get("lifecycle_version") != LIFECYCLE_VERSION:
        raise LifecycleError("unsupported lifecycle version")
    if document.get("state") not in STATES:
        raise LifecycleError("unknown lifecycle state")
    log = document.get("transition_log")
    if not isinstance(log, list) or not log:
        raise LifecycleError("transition log must be non-empty")

    previous: str | None = None
    for expected_sequence, entry in enumerate(log, start=1):
        if not isinstance(entry, dict) or entry.get("sequence") != expected_sequence:
            raise LifecycleError("transition sequence is invalid")
        current = entry.get("to_state")
        if current not in STATES or entry.get("from_state_or_null") != previous:
            raise LifecycleError("transition chain is invalid")
        if previous is not None and current not in ALLOWED_TRANSITIONS[previous]:
            raise LifecycleError(f"illegal lifecycle transition: {previous} -> {current}")
        if not isinstance(entry.get("reason"), str) or not entry["reason"]:
            raise LifecycleError("transition reason is required")
        if not isinstance(entry.get("timestamp_utc"), str) or not entry["timestamp_utc"]:
            raise LifecycleError("transition timestamp is required")
        previous = current
    if previous != document["state"]:
        raise LifecycleError("lifecycle state does not match its transition log")


def transition(
    document: dict[str, Any],
    to_state: str,
    *,
    reason: str,
    timestamp_utc: str,
) -> dict[str, Any]:
    """Return a new lifecycle document; illegal transitions always fail closed."""
    validate_lifecycle(document)
    current = document["state"]
    if to_state not in ALLOWED_TRANSITIONS[current]:
        raise LifecycleError(f"illegal lifecycle transition: {current} -> {to_state}")
    if not reason:
        raise LifecycleError("transition reason is required")

    updated = {
        **document,
        "state": to_state,
        "transition_log": [dict(entry) for entry in document["transition_log"]],
    }
    updated["transition_log"].append(
        Transition(
            sequence=len(updated["transition_log"]) + 1,
            from_state_or_null=current,
            to_state=to_state,
            reason=reason,
            timestamp_utc=timestamp_utc,
        ).as_dict()
    )
    validate_lifecycle(updated)
    return updated
