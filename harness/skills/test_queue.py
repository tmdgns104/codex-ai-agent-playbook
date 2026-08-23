#!/usr/bin/env python3
"""Focused tests for the V8.2 provider-independent proposal queue."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from queue import ProposalQueue, QueueError, validate_queue_transition

ROOT = Path(__file__).resolve().parents[2]


def sample_item() -> dict:
    return {
        "queue_id": "queue-1",
        "skill_id": "docker-container",
        "pattern_key": "docker-container|verification_failure|build-cache-miss",
        "reason": "repeated verified failure pattern needs semantic review",
        "evidence_refs": ["evt-1", "evt-2"],
        "semantic_analysis_required": True,
        "status": "waiting_for_analysis",
        "created_at": "2026-08-22T15:00:00Z",
        "updated_at": "2026-08-22T15:00:00Z",
    }


class ProposalQueueTests(unittest.TestCase):
    def test_waiting_item_works_without_any_llm_provider(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            queue = ProposalQueue(Path(temp))
            queue.enqueue(sample_item())
            current = queue.current()["queue-1"]
            self.assertEqual(current["status"], "waiting_for_analysis")
            self.assertEqual(current["revision"], 1)

    def test_valid_transition_moves_to_processed_log(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            queue = ProposalQueue(Path(temp))
            queue.enqueue(sample_item())
            queue.transition("queue-1", "analyzing", updated_at="2026-08-22T15:01:00Z")
            final = queue.transition("queue-1", "proposal_created", updated_at="2026-08-22T15:02:00Z")
            self.assertEqual(final["status"], "proposal_created")
            self.assertTrue(queue.processed_path.exists())
            self.assertEqual(queue.current()["queue-1"]["status"], "proposal_created")

    def test_invalid_transition_is_rejected(self) -> None:
        with self.assertRaises(QueueError):
            validate_queue_transition("waiting_for_analysis", "proposal_created")

    def test_duplicate_queue_id_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            queue = ProposalQueue(Path(temp))
            item = sample_item()
            queue.enqueue(item)
            with self.assertRaises(QueueError):
                queue.enqueue(item)

    def test_llm_unavailable_queue_does_not_modify_active_skill(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            active = root / "active" / "SKILL.md"
            active.parent.mkdir(parents=True)
            active.write_text("ACTIVE v1\n", encoding="utf-8")
            before = active.read_bytes()

            queue = ProposalQueue(root / ".playbook-state")
            queue.enqueue(sample_item())

            self.assertEqual(queue.current()["queue-1"]["status"], "waiting_for_analysis")
            self.assertEqual(active.read_bytes(), before)

    def test_analyzing_can_return_to_waiting_when_provider_is_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            queue = ProposalQueue(Path(temp))
            queue.enqueue(sample_item())
            queue.transition("queue-1", "analyzing", updated_at="2026-08-22T15:01:00Z")
            returned = queue.transition(
                "queue-1",
                "waiting_for_analysis",
                updated_at="2026-08-22T15:02:00Z",
            )
            self.assertEqual(returned["status"], "waiting_for_analysis")

    def test_protected_llm_unavailable_contract_is_executable(self) -> None:
        fixture_path = ROOT / "evaluation" / "self-managing" / "protected-routing.json"
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        case = next(item for item in fixture["cases"] if item["id"] == "llm-unavailable-control-plane")
        self.assertTrue(case["semantic_analysis_required"])
        self.assertFalse(case["llm_available"])
        self.assertEqual(case["expected_queue_status"], "waiting_for_analysis")
        self.assertFalse(case["active_skill_mutation"])
        self.assertTrue(case["governance_continues"])

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            active = root / "active" / "SKILL.md"
            active.parent.mkdir(parents=True)
            active.write_text("ACTIVE v1\n", encoding="utf-8")
            before = active.read_bytes()
            queue = ProposalQueue(root / ".playbook-state")
            queue.enqueue(sample_item())
            self.assertEqual(queue.current()["queue-1"]["status"], case["expected_queue_status"])
            self.assertEqual(active.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
