#!/usr/bin/env python3
"""Privacy-safe capability-gap recording and deterministic Creator eligibility helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from events import EventError, redact_summary, task_fingerprint, validate_event


class GapError(ValueError):
    """Raised when a capability gap cannot be recorded safely."""


def build_gap_event(
    *,
    event_id: str,
    task_text: str,
    summary: str,
    router_result: str,
    nearby_skill_ids: list[str] | None = None,
    domain_hypothesis: str = "unspecified",
    issue_code: str = "capability-gap",
    timestamp: str | None = None,
) -> dict[str, Any]:
    """Build a privacy-safe capability_gap event without persisting raw task text."""
    if router_result not in {"NO_CAPABILITY", "ROUTED", "NO_ACTION"}:
        raise GapError(f"unsupported router_result: {router_result}")
    nearby = nearby_skill_ids or []
    if not all(isinstance(item, str) and item.strip() for item in nearby):
        raise GapError("nearby_skill_ids must be a string list")
    if not isinstance(domain_hypothesis, str) or not domain_hypothesis.strip():
        raise GapError("domain_hypothesis must be a non-empty string")

    event = {
        "event_id": event_id,
        "event_type": "capability_gap",
        "task_fingerprint": task_fingerprint(task_text),
        "task_summary": redact_summary(summary),
        "timestamp": timestamp or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "skill_ids": [],
        "verification": "unknown",
        "user_correction": False,
        "issue_code": issue_code,
        "router_result": router_result,
        "nearby_skill_ids": sorted(set(nearby)),
        "domain_hypothesis": domain_hypothesis.strip()[:80],
    }
    try:
        validate_event(event)
    except EventError as exc:
        raise GapError(str(exc)) from exc
    return event


def matching_gap_events(events: list[dict[str, Any]], *, domain_hypothesis: str) -> list[dict[str, Any]]:
    """Return only validated capability-gap events for one deterministic domain bucket."""
    target = domain_hypothesis.strip().casefold()
    matches: list[dict[str, Any]] = []
    for event in events:
        try:
            validate_event(event)
        except EventError:
            continue
        if event.get("event_type") != "capability_gap":
            continue
        if str(event.get("domain_hypothesis", "")).strip().casefold() == target:
            matches.append(event)
    return matches
