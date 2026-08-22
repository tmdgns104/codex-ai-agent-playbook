#!/usr/bin/env python3
"""Focused tests for V8.2 deterministic Skill governance foundation."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from lifecycle import LifecycleError, load_lifecycle, validate_transition
from locking import SkillLockError, acquire_lock, release_lock
from promotion import PromotionError, load_protected_regressions, package_hash, promote_package
from proposal import ProposalError, permission_delta, validate_proposal

ROOT = Path(__file__).resolve().parents[2]


def valid_proposal() -> dict:
    return {
        "proposal_id": "prop-test-1",
        "change_type": "modify",
        "skill_id": "testing",
        "base_version": 1,
        "base_hash": "sha256:base",
        "proposed_version": 2,
        "reason": "verified repeated issue",
        "evidence_refs": ["evt-1", "evt-2"],
        "trigger_delta": {"add": [], "remove": []},
        "permission_delta": {"add": [], "remove": []},
        "requires_human_gate": false,
        "status": "candidate"
    }


class LifecycleTests(unittest.TestCase):
    def test_valid_transition_is_accepted(self) -> None:
        lifecycle = load_lifecycle(ROOT)
        validate_transition(lifecycle, "candidate", "validating")
        validate_transition(lifecycle, "validating", "active")
        validate_transition(lifecycle, "archived", "candidate")

    def test_invalid_transition_is_rejected(self) -> None:
        lifecycle = load_lifecycle(ROOT)
        with self.assertRaises(LifecycleError):
            validate_transition(lifecycle, "active", "rejected")


class ProposalTests(unittest.TestCase):
    def test_proposal_schema_is_validated(self) -> None:
        proposal = valid_proposal()
        proposal["requires_human_gate"] = False
        validate_proposal(proposal)

    def test_permission_expansion_requires_human_gate(self) -> None:
        proposal = valid_proposal()
        proposal["permission_delta"] = {"add": ["network"], "remove": []}
        proposal["requires_human_gate"] = False
        with self.assertRaises(ProposalError):
            validate_proposal(proposal)

    def test_permission_delta_detects_add_and_remove(self) -> None:
        delta = permission_delta(["local_read", "process_exec"], ["local_read", "network"])
        self.assertEqual(delta["add"], ["network"])
        self.assertEqual(delta["remove"], ["process_exec"])


class LockingTests(unittest.TestCase):
    def test_same_skill_lock_collision_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            state_root = Path(temp)
            token = acquire_lock(state_root, "testing")
            try:
                with self.assertRaises(SkillLockError):
                    acquire_lock(state_root, "testing")
            finally:
                release_lock(state_root, "testing", token)

    def test_stale_lock_can_be_recovered(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            state_root = Path(temp)
            lock_path = state_root / "locks" / "testing.lock"
            lock_path.parent.mkdir(parents=True, exist_ok=True)
            lock_path.write_text(
                json.dumps({"skill_id": "testing", "token": "old", "created_at_epoch": 0}) + "\n",
                encoding="utf-8",
            )
            token = acquire_lock(state_root, "testing", stale_seconds=1)
            release_lock(state_root, "testing", token)
            self.assertFalse(lock_path.exists())


class PromotionTests(unittest.TestCase):
    @staticmethod
    def _packages(root: Path) -> tuple[Path, Path]:
        active = root / "testing"
        candidate = root / "candidate-testing"
        active.mkdir()
        candidate.mkdir()
        (active / "SKILL.md").write_text("active-v1\n", encoding="utf-8")
        (candidate / "SKILL.md").write_text("candidate-v2\n", encoding="utf-8")
        return active, candidate

    def test_base_hash_mismatch_rejects_without_active_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            active, candidate = self._packages(Path(temp))
            before = (active / "SKILL.md").read_text(encoding="utf-8")
            with self.assertRaises(PromotionError):
                promote_package(
                    active,
                    candidate,
                    expected_base_hash="sha256:not-current",
                    validation_passed=True,
                )
            self.assertEqual((active / "SKILL.md").read_text(encoding="utf-8"), before)

    def test_failed_validation_leaves_active_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            active, candidate = self._packages(Path(temp))
            base_hash = package_hash(active)
            before = (active / "SKILL.md").read_text(encoding="utf-8")
            with self.assertRaises(PromotionError):
                promote_package(
                    active,
                    candidate,
                    expected_base_hash=base_hash,
                    validation_passed=False,
                )
            self.assertEqual((active / "SKILL.md").read_text(encoding="utf-8"), before)

    def test_successful_promotion_replaces_package_after_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            active, candidate = self._packages(Path(temp))
            base_hash = package_hash(active)
            new_hash = promote_package(
                active,
                candidate,
                expected_base_hash=base_hash,
                validation_passed=True,
            )
            self.assertEqual((active / "SKILL.md").read_text(encoding="utf-8"), "candidate-v2\n")
            self.assertEqual(new_hash, package_hash(active))


class ProtectedRegressionTests(unittest.TestCase):
    def test_required_protected_regressions_exist(self) -> None:
        fixture = load_protected_regressions(ROOT)
        ids = {case["id"] for case in fixture["cases"]}
        self.assertIn("jwt-exact-3", ids)
        self.assertIn("max-selected-3", ids)
        self.assertIn("llm-unavailable-control-plane", ids)

    def test_protected_case_cannot_be_silently_removed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            policy = root / "capability-library" / "governance"
            evaluation = root / "evaluation" / "self-managing"
            policy.mkdir(parents=True)
            evaluation.mkdir(parents=True)
            (policy / "policy.json").write_text(
                json.dumps({"required_protected_case_ids": ["must-stay"]}),
                encoding="utf-8",
            )
            (evaluation / "protected-routing.json").write_text(
                json.dumps({"schema_version": 1, "protected": True, "cases": []}),
                encoding="utf-8",
            )
            with self.assertRaises(PromotionError):
                load_protected_regressions(root)


if __name__ == "__main__":
    unittest.main()
