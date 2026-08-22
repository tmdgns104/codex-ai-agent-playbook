#!/usr/bin/env python3
"""Focused tests for V8.2 bounded Skill Evolver."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from evolver import (
    EvolutionError,
    create_evolution_candidate,
    evolution_eligibility,
    matching_evidence,
    promote_evolution_candidate,
)
from promotion import PromotionError, package_hash

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "harness" / "quality" / "skill_audit.py"


ACTIVE_TEXT = """---
name: testing
description: >-
  Synthetic testing workflow used for deterministic evolution tests.
---

# testing

## Purpose / Scope

Use focused evidence to verify a bounded change without widening unrelated behavior.

## When to use

Use when a reproducible verification workflow is required.

## When not to use

Do not use for unrelated repository cleanup or broad rewrites.

## Workflow

1. Capture concrete evidence for the observed failure.
2. Run focused verification.
3. Preserve unrelated behavior and existing routing expectations.
4. Record the final verification result and any remaining uncertainty.

## Evidence

Keep command, output, and regression evidence. Model self-report is not PASS evidence.

## Stop / Handoff

Stop when required evidence is unavailable or permissions would expand unexpectedly.

## Source / Provenance

- source_id: `test-source`
- license: `repository`
- provenance: synthetic governance test fixture
"""


def make_root(base: Path) -> tuple[Path, Path, bytes]:
    root = base / "repo"
    active = root / "capability-library" / "skills" / "optional" / "testing"
    active.mkdir(parents=True)
    (active / "SKILL.md").write_text(ACTIVE_TEXT, encoding="utf-8", newline="\n")
    routing = active / "tests" / "routing.json"
    routing.parent.mkdir(parents=True)
    routing.write_text(
        json.dumps({"schema_version": 1, "skill_id": "testing", "positive": ["existing pass"], "negative": ["existing no"]}, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    routing_bytes = routing.read_bytes()

    governance = root / "capability-library" / "governance"
    governance.mkdir(parents=True)
    (governance / "policy.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "required_protected_case_ids": ["must-stay"],
                "evolution_min_distinct_evidence": 2,
                "evolution_max_content_edits": 2,
                "evolution_max_changed_fraction": 0.35,
            },
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    (root / "capability-library" / "registry.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "capabilities": [
                    {
                        "id": "testing",
                        "type": "skill",
                        "permissions": ["local_read"],
                        "source_id": "test-source",
                        "license": "repository",
                        "path": "capability-library/skills/optional/testing",
                    }
                ],
            },
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    protected = root / "evaluation" / "self-managing"
    protected.mkdir(parents=True)
    (protected / "protected-routing.json").write_text(
        json.dumps({"schema_version": 1, "protected": True, "cases": [{"id": "must-stay"}]}, indent=2) + "\n",
        encoding="utf-8",
    )
    return root, active, routing_bytes


def evidence(event_id: str, fingerprint_suffix: str) -> dict:
    return {
        "event_id": event_id,
        "event_type": "verification_failure",
        "skill_ids": ["testing"],
        "task_fingerprint": "sha256:" + fingerprint_suffix * 64,
        "verification": "fail",
        "user_correction": False,
        "task_summary": "focused verification step was repeatedly missing a regression case",
        "issue_code": "missing-regression-step",
        "timestamp": "2026-08-23T01:00:00Z",
    }


def spec(*, trigger_add: list[str] | None = None, permission_add: list[str] | None = None, edits: list[dict] | None = None) -> dict:
    return {
        "proposal_id": "prop-testing-evolve-001",
        "skill_id": "testing",
        "base_version": 1,
        "observed_pattern": "verified failures repeatedly missed an explicit regression preservation step",
        "root_cause": "workflow wording did not explicitly require preserving a regression case",
        "expected_behavior": "focused verification records and preserves a regression case before PASS",
        "edits": edits
        or [
            {
                "old": "2. Run focused verification.",
                "new": "2. Run focused verification and preserve a regression case before PASS.",
                "reason": "address the repeated missing-regression evidence",
            }
        ],
        "positive_regressions": ["bug fix runs focused verification and preserves a regression case"],
        "negative_regressions": ["README typo does not require the testing evolution"],
        "trigger_add": trigger_add or [],
        "trigger_remove": [],
        "permission_add": permission_add or [],
        "permission_remove": [],
        "source_id": "test-source",
        "license": "repository",
        "provenance": "bounded evolution from repeated privacy-safe verification evidence",
    }


class EligibilityTests(unittest.TestCase):
    def test_weak_single_observation_waits(self) -> None:
        result = evolution_eligibility([evidence("evt-1", "a")], min_distinct_evidence=2)
        self.assertEqual(result.action, "WAIT")

    def test_single_severe_signal_requests_review_not_auto_evolution(self) -> None:
        result = evolution_eligibility(
            [evidence("evt-1", "a")],
            severe_safety_or_correctness=True,
            min_distinct_evidence=2,
        )
        self.assertEqual(result.action, "REVIEW")

    def test_duplicate_task_fingerprint_counts_once(self) -> None:
        events = [evidence("evt-1", "a"), evidence("evt-2", "a")]
        matched = matching_evidence(events, skill_id="testing", issue_code="missing-regression-step")
        self.assertEqual(len(matched), 1)


class CandidateTests(unittest.TestCase):
    def test_repeated_evidence_creates_candidate_and_active_is_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root, active, _ = make_root(Path(temp))
            state = Path(temp) / ".playbook-state"
            before = (active / "SKILL.md").read_bytes()
            result = create_evolution_candidate(
                root=root,
                state_root=state,
                spec=spec(),
                events=[evidence("evt-1", "a"), evidence("evt-2", "b")],
                issue_code="missing-regression-step",
            )
            self.assertEqual(result["result"], "CANDIDATE_CREATED")
            self.assertEqual((active / "SKILL.md").read_bytes(), before)
            candidate = Path(result["candidate_path"])
            self.assertIn("preserve a regression case before PASS", (candidate / "SKILL.md").read_text(encoding="utf-8"))

    def test_candidate_base_hash_points_to_active_v1(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root, active, _ = make_root(Path(temp))
            result = create_evolution_candidate(
                root=root,
                state_root=Path(temp) / ".playbook-state",
                spec=spec(),
                events=[evidence("evt-1", "a"), evidence("evt-2", "b")],
            )
            self.assertEqual(result["proposal"]["base_hash"], package_hash(active))
            self.assertEqual(result["proposal"]["proposed_version"], 2)
            self.assertEqual(len(result["proposal"]["evidence_refs"]), 2)

    def test_broad_unrelated_rewrite_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root, _, _ = make_root(Path(temp))
            broad = [{"old": ACTIVE_TEXT.strip(), "new": "tiny replacement", "reason": "unrelated rewrite"}]
            with self.assertRaises(EvolutionError):
                create_evolution_candidate(
                    root=root,
                    state_root=Path(temp) / ".playbook-state",
                    spec=spec(edits=broad),
                    events=[evidence("evt-1", "a"), evidence("evt-2", "b")],
                )

    def test_existing_routing_fixture_is_preserved_and_regression_added(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root, _, routing_bytes = make_root(Path(temp))
            result = create_evolution_candidate(
                root=root,
                state_root=Path(temp) / ".playbook-state",
                spec=spec(),
                events=[evidence("evt-1", "a"), evidence("evt-2", "b")],
            )
            candidate = Path(result["candidate_path"])
            self.assertEqual((candidate / "tests" / "routing.json").read_bytes(), routing_bytes)
            routing = json.loads((candidate / "routing.json").read_text(encoding="utf-8"))
            self.assertEqual(routing["preserved_fixture"], "tests/routing.json")
            self.assertEqual(len(routing["positive"]), 1)
            self.assertEqual(len(routing["negative"]), 1)

    def test_permission_expansion_forces_human_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root, _, _ = make_root(Path(temp))
            result = create_evolution_candidate(
                root=root,
                state_root=Path(temp) / ".playbook-state",
                spec=spec(permission_add=["network"]),
                events=[evidence("evt-1", "a"), evidence("evt-2", "b")],
            )
            self.assertTrue(result["proposal"]["requires_human_gate"])

    def test_trigger_expansion_forces_human_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root, _, _ = make_root(Path(temp))
            result = create_evolution_candidate(
                root=root,
                state_root=Path(temp) / ".playbook-state",
                spec=spec(trigger_add=["new trigger"]),
                events=[evidence("evt-1", "a"), evidence("evt-2", "b")],
            )
            self.assertTrue(result["proposal"]["requires_human_gate"])

    def test_modify_candidate_passes_skill_audit(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root, _, _ = make_root(Path(temp))
            result = create_evolution_candidate(
                root=root,
                state_root=Path(temp) / ".playbook-state",
                spec=spec(),
                events=[evidence("evt-1", "a"), evidence("evt-2", "b")],
            )
            audit = subprocess.run(
                [sys.executable, str(AUDIT), "--root", str(root), "--candidate", result["candidate_path"]],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )
            self.assertEqual(audit.returncode, 0, audit.stdout)
            self.assertIn("RESULT     PASS", audit.stdout)


class PromotionTests(unittest.TestCase):
    def _candidate(self, temp: str) -> tuple[Path, Path, Path, Path]:
        root, active, _ = make_root(Path(temp))
        state = Path(temp) / ".playbook-state"
        result = create_evolution_candidate(
            root=root,
            state_root=state,
            spec=spec(),
            events=[evidence("evt-1", "a"), evidence("evt-2", "b")],
        )
        return root, active, state, Path(result["candidate_path"])

    def test_failed_validation_leaves_active_v1_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root, active, state, candidate = self._candidate(temp)
            before = package_hash(active)
            with self.assertRaises(PromotionError):
                promote_evolution_candidate(
                    root=root,
                    state_root=state,
                    candidate_dir=candidate,
                    validation_passed=False,
                    protected_regression_passed=True,
                )
            self.assertEqual(package_hash(active), before)

    def test_failed_protected_regression_leaves_active_v1_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root, active, state, candidate = self._candidate(temp)
            before = package_hash(active)
            with self.assertRaises(PromotionError):
                promote_evolution_candidate(
                    root=root,
                    state_root=state,
                    candidate_dir=candidate,
                    validation_passed=True,
                    protected_regression_passed=False,
                )
            self.assertEqual(package_hash(active), before)

    def test_successful_low_risk_promotion_is_atomic_and_records_history(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root, active, state, candidate = self._candidate(temp)
            old_hash = package_hash(active)
            new_hash = promote_evolution_candidate(
                root=root,
                state_root=state,
                candidate_dir=candidate,
                validation_passed=True,
                protected_regression_passed=True,
                timestamp="2026-08-23T01:10:00Z",
            )
            self.assertNotEqual(new_hash, old_hash)
            self.assertEqual(new_hash, package_hash(active))
            self.assertIn("preserve a regression case before PASS", (active / "SKILL.md").read_text(encoding="utf-8"))
            self.assertTrue((active / "tests" / "routing.json").is_file())
            self.assertFalse((active / "proposal.json").exists())
            self.assertFalse((active / "routing.json").exists())
            history = state / "history" / "promotion-history.jsonl"
            records = [json.loads(line) for line in history.read_text(encoding="utf-8").splitlines() if line.strip()]
            self.assertEqual(records[-1]["status"], "promoted")
            self.assertEqual(records[-1]["skill_id"], "testing")
            self.assertEqual(records[-1]["new_hash"], new_hash)


if __name__ == "__main__":
    unittest.main()
