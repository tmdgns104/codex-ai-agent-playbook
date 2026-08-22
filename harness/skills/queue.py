#!/usr/bin/env python3
"""Provider-independent proposal analysis queue for V8.2 Skill governance."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

QUEUE_STATES = {
    "waiting_for_analysis",
    "analyzing",
    "proposal_created",
    "no_change_needed",
    "blocked",
    "failed",
}
TERMINAL_STATES = {"proposal_created", "no_change_needed", "blocked", "failed"}
TRANSITIONS = {
    "waiting_for_analysis": {"analyzing", "no_change_needed", "blocked", "failed"},
    "analyzing": {"waiting_for_analysis", "proposal_created", "no_change_needed", "blocked", "failed"},
    "proposal_created": set(),
    "no_change_needed": set(),
    "blocked": set(),
    "failed": set(),
}


class QueueError(ValueError):
    """Raised when proposal queue data or a state transition is invalid."""


def validate_queue_item(data: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise QueueError("queue item must be an object")
    for key in ("queue_id", "pattern_key", "reason", "status", "created_at", "updated_at"):
        value = data.get(key)
        if not isinstance(value, str) or not value.strip():
            raise QueueError(f"{key} must be a non-empty string")
    if data["status"] not in QUEUE_STATES:
        raise QueueError(f"unsupported queue status: {data['status']}")
    if data.get("semantic_analysis_required") is not True:
        raise QueueError("queue items must represent semantic_analysis_required work")
    skill_id = data.get("skill_id")
    if skill_id is not None and (not isinstance(skill_id, str) or not skill_id.strip()):
        raise QueueError("skill_id must be null or a non-empty string")
    refs = data.get("evidence_refs")
    if not isinstance(refs, list) or not all(isinstance(item, str) and item.strip() for item in refs):
        raise QueueError("evidence_refs must be a string list")
    revision = data.get("revision", 1)
    if not isinstance(revision, int) or isinstance(revision, bool) or revision < 1:
        raise QueueError("revision must be an integer >= 1")
    return data


def validate_queue_transition(from_state: str, to_state: str) -> None:
    if from_state not in QUEUE_STATES or to_state not in QUEUE_STATES:
        raise QueueError(f"unknown queue transition: {from_state} -> {to_state}")
    if to_state not in TRANSITIONS[from_state]:
        raise QueueError(f"invalid queue transition: {from_state} -> {to_state}")


class ProposalQueue:
    """Append-only queue. It deliberately has no Codex/OpenAI/Ollama dependency."""

    def __init__(self, state_root: Path):
        self.pending_path = state_root / "queue" / "pending.jsonl"
        self.processed_path = state_root / "queue" / "processed.jsonl"

    @staticmethod
    def _append(path: Path, item: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())

    @staticmethod
    def _read(path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        result: list[dict[str, Any]] = []
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise QueueError(f"malformed queue JSONL {path.name}:{number}: {exc}") from exc
            validate_queue_item(item)
            result.append(item)
        return result

    def history(self) -> list[dict[str, Any]]:
        return self._read(self.pending_path) + self._read(self.processed_path)

    def current(self) -> dict[str, dict[str, Any]]:
        current: dict[str, dict[str, Any]] = {}
        for item in self.history():
            previous = current.get(item["queue_id"])
            if previous is None or int(item.get("revision", 1)) >= int(previous.get("revision", 1)):
                current[item["queue_id"]] = item
        return current

    def enqueue(self, item: dict[str, Any]) -> None:
        validate_queue_item(item)
        if item["status"] != "waiting_for_analysis":
            raise QueueError("new queue item must start at waiting_for_analysis")
        if item["queue_id"] in self.current():
            raise QueueError(f"duplicate queue_id: {item['queue_id']}")
        record = dict(item)
        record["revision"] = 1
        self._append(self.pending_path, record)

    def transition(self, queue_id: str, to_state: str, *, updated_at: str) -> dict[str, Any]:
        current = self.current().get(queue_id)
        if current is None:
            raise QueueError(f"queue item not found: {queue_id}")
        validate_queue_transition(current["status"], to_state)
        record = dict(current)
        record["status"] = to_state
        record["updated_at"] = updated_at
        record["revision"] = int(current.get("revision", 1)) + 1
        target = self.processed_path if to_state in TERMINAL_STATES else self.pending_path
        self._append(target, record)
        return record
