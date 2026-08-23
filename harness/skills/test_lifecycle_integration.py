#!/usr/bin/env python3
"""Focused E2E-style tests for V8.2 Self-Managing Lifecycle integration."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve()
HARNESS_ROOT = HERE.parents[1]
for import_dir in (HARNESS_ROOT / "activation", HARNESS_ROOT / "router"):
    if str(import_dir) not in sys.path:
        sys.path.insert(0, str(import_dir))

from curator import build_curator_proposal, create_package_candidate
from events import EventStore
from evolver import create_evolution_candidate
from lifecycle_integration import (
    build_task_event,
    list_candidates,
    promote_candidate,
    record_task_event,
    validate_candidate,
)
from manage import benchmark_router
from playbook_launch import record_launch_event
from promotion import package_hash


ACTIVE_BODY = """---
name: synthetic-skill
description: >-
  Synthetic Skill used for lifecycle integration tests.
---

# synthetic-skill

## Purpose / Scope

Synthetic reusable workflow for deterministic tests.

## Workflow

1. Inspect evidence.
2. Apply the old step.
3. Verify the result.

## Evidence

Record concrete verification evidence.

## Stop / Handoff

Stop when evidence is missing or scope expands.

## Source / Provenance

- source_id: `internal-test`
- license: `repository`
- provenance: synthetic test fixture
"""


class Completed:
    def __init__(self, returncode: int, stdout: str = "OK\n") -> None:
        self.returncode = returncode
        self.stdout = stdout


class SyntheticRepo:
    def __init__(self, base: Path) -> None:
        self.root = base / "repo"
        self.state = self.root / ".playbook-state"
        self.active = self.root / "capability-library" / "skills" / "optional" / "synthetic-skill"
        self.active.mkdir(parents=True)
        (self.active / "SKILL.md").write_text(ACTIVE_BODY, encoding="utf-8", newline="\n")
        (self.active / "assets").mkdir()
        (self.active / "assets" / "keep.txt").write_text("KEEP\n", encoding="utf-8")

        capability = self.root / "capability-library"
        governance = capability / "governance"
        governance.mkdir(parents=True)
        registry = {
            "schema_version": 1,
            "capabilities": [
                {
                    "id": "synthetic-skill",
                    "type": "skill",
                    "path": "capability-library/skills/optional/synthetic-skill",
                    "source_id": "internal-test",
                    "license": "repository",
                    "triggers": ["synthetic"],
                    "permissions": ["local_read"],
                }
            ],
        }
        (capability / "registry.json").write_text(json.dumps(registry) + "\n", encoding="utf-8")
        policy = {
            "schema_version": 1,
            "required_protected_case_ids": ["jwt-exact-3", "max-selected-3", "llm-unavailable-control-plane"],
            "evolution_min_distinct_evidence": 2,
            "evolution_max_content_edits": 2,
            "evolution_max_changed_fraction": 0.35,
        }
        (governance / "policy.json").write_text(json.dumps(policy) + "\n", encoding="utf-8")

        evaluation = self.root / "evaluation" / "self-managing"
        evaluation.mkdir(parents=True)
        fixture = {
            "schema_version": 1,
            "protected": True,
            "cases": [
                {"id": "jwt-exact-3"},
                {"id": "max-selected-3"},
                {"id": "llm-unavailable-control-plane"},
            ],
        }
        (evaluation / "protected-routing.json").write_text(json.dumps(fixture) + "\n", encoding="utf-8")
        router = self.root / "harness" / "router"
        router.mkdir(parents=True)
        (router / "test_capability_router.py").write_text("# synthetic protected runner\n", encoding="utf-8")

    @staticmethod
    def events() -> list[dict]:
        return [
            {
                "event_id": "e1",
                "event_type": "verification_failure",
                "task_fingerprint": "sha256:1111",
                "timestamp": "2026-08-23T00:00:00Z",
                "skill_ids": ["synthetic-skill"],
                "verification": "fail",
                "user_correction": False,
                "issue_code": "missing-step",
            },
            {
                "event_id": "e2",
                "event_type": "verification_failure",
                "task_fingerprint": "sha256:2222",
                "timestamp": "2026-08-23T00:01:00Z",
                "skill_ids": ["synthetic-skill"],
                "verification": "fail",
                "user_correction": False,
                "issue_code": "missing-step",
            },
        ]

    @staticmethod
    def evolution_spec(proposal_id: str) -> dict:
        return {
            "proposal_id": proposal_id,
            "skill_id": "synthetic-skill",
            "base_version": 1,
            "observed_pattern": "Repeated missing workflow step",
            "root_cause": "Old step lacks explicit deterministic check",
            "expected_behavior": "New step performs explicit deterministic check",
            "edits": [
                {
                    "old": "2. Apply the old step.",
                    "new": "2. Apply the new deterministic check.",
                    "reason": "Repeated verified failure evidence",
                }
            ],
            "positive_regressions": ["synthetic deterministic check"],
            "negative_regressions": ["unrelated documentation task"],
            "trigger_add": [],
            "trigger_remove": [],
            "permission_add": [],
            "permission_remove": [],
            "source_id": "internal-test",
            "license": "repository",
            "provenance": "synthetic integration test",
        }


def pass_runner(*args, **kwargs):
    return Completed(0)


def fail_runner(*args, **kwargs):
    return Completed(1, "FAILED\n")


class LifecycleEventTests(unittest.TestCase):
    def test_selected_skill_success_records_verified_usage_without_raw_task(self) -> None:
        event = build_task_event(
            task_text="JWT secret-looking task text is not persisted",
            skill_ids=["testing"],
            codex_exit=0,
            event_id="event-1",
            timestamp="2026-08-23T00:00:00Z",
        )
        self.assertEqual(event["event_type"], "verified_usage")
        self.assertEqual(event["verification"], "pass")
        self.assertNotIn("task_text", event)
        self.assertTrue(event["task_fingerprint"].startswith("sha256:"))

    def test_no_skill_task_records_gap_only_not_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            state = Path(temp) / ".playbook-state"
            result = record_task_event(state_root=state, task_text="known gap", skill_ids=[], codex_exit=0)
            self.assertEqual(result["result"], "EVENT_RECORDED")
            events = EventStore(state).read_all()
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0]["event_type"], "capability_gap")
            self.assertFalse((state / "candidates").exists())

    def test_explicit_correction_is_marked(self) -> None:
        event = build_task_event(
            task_text="fix correction",
            skill_ids=["testing"],
            codex_exit=0,
            user_correction=True,
            event_id="event-2",
            timestamp="2026-08-23T00:00:00Z",
        )
        self.assertEqual(event["event_type"], "user_correction")
        self.assertTrue(event["user_correction"])

    def test_event_failure_is_best_effort(self) -> None:
        result = record_task_event(
            state_root=Path(tempfile.gettempdir()) / "wrong-state-name",
            task_text="task",
            skill_ids=[],
            codex_exit=0,
        )
        self.assertEqual(result["result"], "EVENT_RECORD_FAILED")

    def test_launcher_event_uses_catalog_state_not_target_repository(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            catalog = base / "catalog"
            target = base / "target-repo"
            catalog.mkdir()
            target.mkdir()
            plan = {
                "catalog_root": str(catalog),
                "target_root": str(target),
                "task": "gap task",
                "skills": [],
            }
            result = {"codex_exit": 0}
            event = record_launch_event(plan, result)
            self.assertEqual(event["result"], "EVENT_RECORDED")
            self.assertTrue((catalog / ".playbook-state" / "events" / "skill-events.jsonl").is_file())
            self.assertFalse((target / ".playbook-state").exists())


class LifecycleCandidateTests(unittest.TestCase):
    def make_repo(self) -> tuple[tempfile.TemporaryDirectory, SyntheticRepo]:
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        return holder, SyntheticRepo(Path(holder.name))

    def test_evolver_candidate_integrates_and_active_stays_unchanged(self) -> None:
        _, repo = self.make_repo()
        before = package_hash(repo.active)
        result = create_evolution_candidate(
            root=repo.root,
            state_root=repo.state,
            spec=repo.evolution_spec("evolve-1"),
            events=repo.events(),
            issue_code="missing-step",
        )
        self.assertEqual(result["result"], "CANDIDATE_CREATED")
        self.assertEqual(package_hash(repo.active), before)
        self.assertEqual(list_candidates(repo.state)[0]["proposal_id"], "evolve-1")

    def test_failed_protected_regression_blocks_promotion_and_preserves_active(self) -> None:
        _, repo = self.make_repo()
        before = package_hash(repo.active)
        create_evolution_candidate(
            root=repo.root,
            state_root=repo.state,
            spec=repo.evolution_spec("evolve-fail"),
            events=repo.events(),
            issue_code="missing-step",
        )
        result = promote_candidate(
            root=repo.root,
            state_root=repo.state,
            proposal_id="evolve-fail",
            regression_runner=fail_runner,
        )
        self.assertEqual(result["result"], "VALIDATION_FAILED")
        self.assertEqual(package_hash(repo.active), before)

    def test_low_risk_evolver_candidate_promotes_atomically_and_records_history(self) -> None:
        _, repo = self.make_repo()
        before = package_hash(repo.active)
        create_evolution_candidate(
            root=repo.root,
            state_root=repo.state,
            spec=repo.evolution_spec("evolve-pass"),
            events=repo.events(),
            issue_code="missing-step",
        )
        result = promote_candidate(
            root=repo.root,
            state_root=repo.state,
            proposal_id="evolve-pass",
            regression_runner=pass_runner,
        )
        self.assertEqual(result["result"], "PROMOTED")
        self.assertNotEqual(package_hash(repo.active), before)
        self.assertIn("new deterministic check", (repo.active / "SKILL.md").read_text(encoding="utf-8"))
        self.assertFalse((repo.active / "proposal.json").exists())
        self.assertFalse((repo.active / "routing.json").exists())
        self.assertTrue((repo.state / "history" / "promotion-history.jsonl").is_file())

    def test_curator_compress_candidate_validates_without_active_mutation(self) -> None:
        _, repo = self.make_repo()
        before = package_hash(repo.active)
        proposal = build_curator_proposal(
            proposal_id="curate-1",
            change_type="compress",
            skill_id="synthetic-skill",
            base_version=1,
            base_hash=before,
            reason="synthetic duplicate prose",
            evidence_refs=["audit:size"],
            source_id="internal-test",
            license_name="repository",
            provenance="synthetic integration test",
        )
        create_package_candidate(
            state_root=repo.state,
            active_dir=repo.active,
            proposal=proposal,
            operations=[
                {
                    "old": "Synthetic reusable workflow for deterministic tests.",
                    "new": "Synthetic deterministic workflow.",
                }
            ],
            positive_cases=["synthetic workflow"],
            negative_cases=["unrelated task"],
        )
        result = validate_candidate(
            root=repo.root,
            state_root=repo.state,
            proposal_id="curate-1",
            regression_runner=pass_runner,
        )
        self.assertEqual(result["result"], "READY")
        self.assertEqual(package_hash(repo.active), before)
        self.assertEqual((repo.active / "assets" / "keep.txt").read_text(encoding="utf-8"), "KEEP\n")

    def test_structural_archive_requires_human_gate_and_never_auto_promotes(self) -> None:
        _, repo = self.make_repo()
        candidate = repo.state / "candidates" / "archive-1"
        candidate.mkdir(parents=True)
        proposal = {
            "proposal_id": "archive-1",
            "change_type": "archive",
            "skill_id": "synthetic-skill",
            "base_version": 1,
            "base_hash": package_hash(repo.active),
            "proposed_version": 2,
            "reason": "replacement and verified low utility",
            "evidence_refs": ["evidence-1"],
            "trigger_delta": {"add": [], "remove": []},
            "permission_delta": {"add": [], "remove": []},
            "requires_human_gate": True,
            "status": "candidate",
        }
        (candidate / "proposal.json").write_text(json.dumps(proposal) + "\n", encoding="utf-8")
        blocked = promote_candidate(root=repo.root, state_root=repo.state, proposal_id="archive-1")
        self.assertEqual(blocked["result"], "HUMAN_GATE_REQUIRED")
        approved = promote_candidate(
            root=repo.root,
            state_root=repo.state,
            proposal_id="archive-1",
            human_gate_approved=True,
        )
        self.assertEqual(approved["result"], "MANUAL_ONLY")


class ScalingTests(unittest.TestCase):
    def test_metadata_router_scaling_records_required_sizes(self) -> None:
        measurements = benchmark_router(repeats=2)
        self.assertEqual([item["skill_count"] for item in measurements], [10, 50, 100, 500, 1000])
        self.assertTrue(all(item["average_ms"] >= 0 for item in measurements))
        self.assertTrue(all(item["selected_count"] <= 3 for item in measurements))


if __name__ == "__main__":
    unittest.main()
