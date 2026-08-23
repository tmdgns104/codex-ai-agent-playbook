#!/usr/bin/env python3
"""Focused tests for the V8.2 append-only Skill event store."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from events import EventError, EventStore, pattern_key, redact_summary, task_fingerprint, validate_event


def sample_event() -> dict:
    return {
        "event_id": "evt-1",
        "event_type": "verification_failure",
        "task_fingerprint": task_fingerprint("Docker build failed in cache stage"),
        "task_summary": "Docker build cache failure",
        "skill_ids": ["docker-container"],
        "verification": "fail",
        "user_correction": False,
        "issue_code": "build cache miss",
        "timestamp": "2026-08-22T15:00:00Z",
    }


class EventValidationTests(unittest.TestCase):
    def test_task_fingerprint_does_not_store_raw_task(self) -> None:
        raw = "private task contents"
        fingerprint = task_fingerprint(raw)
        self.assertTrue(fingerprint.startswith("sha256:"))
        self.assertNotIn(raw, fingerprint)

    def test_secret_summary_is_redacted_before_storage(self) -> None:
        summary = redact_summary("token sk-abcdefghijklmnopqrstuvwxyz123456 caused failure")
        self.assertIn("[REDACTED]", summary)
        self.assertNotIn("sk-abcdefghijklmnopqrstuvwxyz123456", summary)

    def test_raw_prompt_field_is_rejected(self) -> None:
        event = sample_event()
        event["task_text"] = "do not persist me"
        with self.assertRaises(EventError):
            validate_event(event)

    def test_pattern_key_is_deterministic(self) -> None:
        event = sample_event()
        first = pattern_key(event)
        second = pattern_key(dict(event))
        self.assertEqual(first, second)
        self.assertEqual(first, "docker-container|verification_failure|build-cache-miss")


class EventStoreTests(unittest.TestCase):
    def test_append_and_read_are_llm_independent(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            store = EventStore(Path(temp))
            event = sample_event()
            store.append(event)
            self.assertEqual(store.read_all(), [event])

    def test_malformed_jsonl_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            store = EventStore(Path(temp))
            store.path.parent.mkdir(parents=True)
            store.path.write_text("{not-json}\n", encoding="utf-8")
            with self.assertRaises(EventError):
                store.read_all()


if __name__ == "__main__":
    unittest.main()
