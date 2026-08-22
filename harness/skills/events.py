#!/usr/bin/env python3
"""Append-only, LLM-independent Skill evidence event store."""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

EVENT_TYPES = {
    "verified_usage",
    "verification_failure",
    "capability_gap",
    "user_correction",
    "routing_false_positive",
    "routing_false_negative",
}
VERIFICATION_VALUES = {"pass", "fail", "unknown"}
FORBIDDEN_PERSISTED_KEYS = {
    "task_text",
    "raw_prompt",
    "prompt",
    "credential",
    "credentials",
    "password",
    "secret",
    "api_key",
    "token",
}
SECRET_VALUE = re.compile(
    r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|\bAKIA[0-9A-Z]{16}\b|\bgh[pousr]_[A-Za-z0-9]{20,}\b|\bsk-[A-Za-z0-9_-]{20,}\b"
)
ISSUE_CODE = re.compile(r"[^a-z0-9._-]+")


class EventError(ValueError):
    """Raised when an evidence event violates the local telemetry contract."""


def task_fingerprint(task_text: str) -> str:
    if not isinstance(task_text, str) or not task_text:
        raise EventError("task text is required to compute a fingerprint")
    return "sha256:" + hashlib.sha256(task_text.encode("utf-8")).hexdigest()


def redact_summary(summary: str, *, max_chars: int = 160) -> str:
    if not isinstance(summary, str):
        raise EventError("summary must be a string")
    value = SECRET_VALUE.sub("[REDACTED]", summary.replace("\r", " ").replace("\n", " "))
    value = " ".join(value.split())
    return value[:max_chars]


def normalize_issue_code(value: str | None) -> str:
    raw = (value or "unspecified").strip().casefold()
    normalized = ISSUE_CODE.sub("-", raw).strip("-")
    return normalized or "unspecified"


def validate_event(data: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise EventError("event must be an object")
    forbidden = FORBIDDEN_PERSISTED_KEYS & {str(key).casefold() for key in data}
    if forbidden:
        raise EventError("raw/sensitive fields are not allowed: " + ", ".join(sorted(forbidden)))

    for key in ("event_id", "event_type", "task_fingerprint", "timestamp"):
        value = data.get(key)
        if not isinstance(value, str) or not value.strip():
            raise EventError(f"{key} must be a non-empty string")
    if data["event_type"] not in EVENT_TYPES:
        raise EventError(f"unsupported event_type: {data['event_type']}")
    if not data["task_fingerprint"].startswith("sha256:"):
        raise EventError("task_fingerprint must use sha256: prefix")

    skill_ids = data.get("skill_ids", [])
    if not isinstance(skill_ids, list) or not all(isinstance(item, str) and item.strip() for item in skill_ids):
        raise EventError("skill_ids must be a string list")

    verification = data.get("verification", "unknown")
    if verification not in VERIFICATION_VALUES:
        raise EventError(f"invalid verification value: {verification}")
    if not isinstance(data.get("user_correction", False), bool):
        raise EventError("user_correction must be boolean")

    summary = data.get("task_summary")
    if summary is not None:
        if not isinstance(summary, str):
            raise EventError("task_summary must be a string")
        if SECRET_VALUE.search(summary):
            raise EventError("task_summary contains obvious secret material")
        if len(summary) > 160:
            raise EventError("task_summary exceeds 160 characters")

    issue_code = data.get("issue_code")
    if issue_code is not None and (not isinstance(issue_code, str) or not issue_code.strip()):
        raise EventError("issue_code must be a non-empty string when supplied")
    return data


def pattern_key(data: dict[str, Any]) -> str:
    validate_event(data)
    skills = "+".join(sorted(data.get("skill_ids", []))) or "no-skill"
    return f"{skills}|{data['event_type']}|{normalize_issue_code(data.get('issue_code'))}"


class EventStore:
    """Append-only JSONL store under .playbook-state by default."""

    def __init__(self, state_root: Path):
        self.path = state_root / "events" / "skill-events.jsonl"

    def append(self, event: dict[str, Any]) -> None:
        validate_event(event)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(event, ensure_ascii=False, sort_keys=True)
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(line + "\n")
            handle.flush()
            os.fsync(handle.fileno())

    def read_all(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        events: list[dict[str, Any]] = []
        for number, line in enumerate(self.path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise EventError(f"malformed event JSONL at line {number}: {exc}") from exc
            validate_event(item)
            events.append(item)
        return events
