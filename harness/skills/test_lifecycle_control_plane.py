#!/usr/bin/env python3
"""Safety-boundary tests for the V8.2 lifecycle control plane."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve()
HARNESS_ROOT = HERE.parents[1]
if str(HARNESS_ROOT / "activation") not in sys.path:
    sys.path.insert(0, str(HARNESS_ROOT / "activation"))

from creator import create_candidate
from gap_detector import build_gap_event
from lifecycle_integration import promote_candidate, run_protected_regression


class Completed:
    returncode = 0
    stdout = "OK\n"


def pass_runner(*args, **kwargs):
    return Completed()


class CreatorIntegrationTests(unittest.TestCase):
    def test_repeated_reviewed_gap_can_create_candidate_but_one_gap_cannot(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            state = Path(temp) / ".playbook-state"
            spec = {
                "proposal_id": "creator-1",
                "skill_id": "new-reusable-skill",
                "description": "Reusable synthetic workflow.",
                "purpose": "Handle a repeated reviewed capability gap.",
                "workflow": ["Inspect reviewed evidence", "Apply deterministic workflow", "Verify result"],
                "triggers": [],
                "permissions": ["local_read"],
                "positive_cases": ["reusable gap alpha", "reusable gap beta"],
                "negative_cases": ["unrelated one-off"],
                "source_id": "internal-test",
                "license": "repository",
                "provenance": "synthetic reviewed evidence",
                "domain_hypothesis": "synthetic-domain",
            }
            event1 = build_gap_event(
                event_id="gap-1",
                task_text="first reusable gap",
                summary="first reusable gap",
                router_result="NO_CAPABILITY",
                domain_hypothesis="synthetic-domain",
                timestamp="2026-08-23T00:00:00Z",
            )
            wait = create_candidate(state_root=state, spec=spec, events=[event1])
            self.assertEqual(wait["result"], "WAIT")
            self.assertFalse((state / "candidates" / "creator-1").exists())

            event2 = build_gap_event(
                event_id="gap-2",
                task_text="second reusable gap",
                summary="second reusable gap",
                router_result="NO_CAPABILITY",
                domain_hypothesis="synthetic-domain",
                timestamp="2026-08-23T00:01:00Z",
            )
            created = create_candidate(state_root=state, spec=spec, events=[event1, event2])
            self.assertEqual(created["result"], "CANDIDATE_CREATED")
            self.assertTrue((state / "candidates" / "creator-1" / "SKILL.md").is_file())


class HumanGateIntegrationTests(unittest.TestCase):
    def test_permission_split_merge_archive_all_block_without_human_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "catalog"
            state = root / ".playbook-state"
            for index, change_type in enumerate(("permission-expand", "split", "merge", "archive"), start=1):
                proposal_id = f"gate-{index}"
                candidate = state / "candidates" / proposal_id
                candidate.mkdir(parents=True)
                proposal = {
                    "proposal_id": proposal_id,
                    "change_type": change_type,
                    "skill_id": "synthetic-skill",
                    "base_version": 1,
                    "base_hash": "sha256:base",
                    "proposed_version": 2,
                    "reason": "synthetic human gate test",
                    "evidence_refs": ["evidence-1"],
                    "trigger_delta": {"add": [], "remove": []},
                    "permission_delta": {"add": ["network"] if change_type == "permission-expand" else [], "remove": []},
                    "requires_human_gate": True,
                    "status": "candidate",
                }
                (candidate / "proposal.json").write_text(json.dumps(proposal) + "\n", encoding="utf-8")
                result = promote_candidate(root=root, state_root=state, proposal_id=proposal_id)
                self.assertEqual(result["result"], "HUMAN_GATE_REQUIRED", change_type)


class InstalledControlPlaneTests(unittest.TestCase):
    def test_protected_regression_uses_installed_governance_snapshot_without_evaluation_tree(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "installed-catalog"
            governance = root / "capability-library" / "governance"
            governance.mkdir(parents=True)
            policy = {
                "schema_version": 1,
                "required_protected_case_ids": ["jwt-exact-3", "max-selected-3", "llm-unavailable-control-plane"],
            }
            fixture = {
                "schema_version": 1,
                "protected": True,
                "cases": [
                    {"id": "jwt-exact-3"},
                    {"id": "max-selected-3"},
                    {"id": "llm-unavailable-control-plane"},
                ],
            }
            (governance / "policy.json").write_text(json.dumps(policy) + "\n", encoding="utf-8")
            (governance / "protected-routing.json").write_text(json.dumps(fixture) + "\n", encoding="utf-8")
            router = root / "playbook-harness" / "router"
            router.mkdir(parents=True)
            (router / "test_capability_router.py").write_text("# installed synthetic runner\n", encoding="utf-8")

            result = run_protected_regression(root, runner=pass_runner)
            self.assertEqual(result["result"], "PASS")
            self.assertFalse((root / "evaluation").exists())

    def test_normal_launcher_source_does_not_directly_invoke_maintenance_components(self) -> None:
        launcher = (HARNESS_ROOT / "activation" / "playbook_launch.py").read_text(encoding="utf-8")
        self.assertNotIn("create_candidate(", launcher)
        self.assertNotIn("create_evolution_candidate(", launcher)
        self.assertNotIn("build_curator_report(", launcher)
        self.assertIn("record_launch_event", launcher)


if __name__ == "__main__":
    unittest.main()
