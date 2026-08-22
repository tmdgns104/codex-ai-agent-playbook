#!/usr/bin/env python3
"""Focused tests for V8.2 privacy-safe Skill Creator Candidate generation."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from creator import CreatorError, create_candidate, creator_eligibility, validate_creator_spec
from gap_detector import build_gap_event

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "harness" / "quality" / "skill_audit.py"


def creator_spec(*, permissions: list[str] | None = None, license_name: str = "repository") -> dict:
    return {
        "proposal_id": "prop-ros2-can-mqtt-001",
        "skill_id": "ros2-can-mqtt-integration",
        "description": "ROS2 QoS와 CAN-MQTT integration 설계 및 진단 workflow",
        "purpose": "반복되는 ROS2 publisher/subscriber QoS와 CAN-MQTT integration 문제를 evidence 기반으로 설계하고 진단합니다.",
        "workflow": [
            "입출력 topic, CAN signal, MQTT boundary를 확인",
            "ROS2 QoS reliability/durability/depth 요구를 명시",
            "CAN-MQTT 변환 경계와 failure path를 점검",
            "focused integration verification을 실행",
        ],
        "triggers": ["ros2 qos can mqtt", "can mqtt integration", "ros2 qos integration"],
        "permissions": permissions or ["local_read"],
        "positive_cases": [
            "ROS2 publisher subscriber QoS와 CAN-MQTT integration을 설계",
            "CAN signal을 MQTT로 전달하는 ROS2 bridge의 QoS 문제를 진단",
        ],
        "negative_cases": ["README에서 ROS2 단어 오타 수정"],
        "source_id": "internal-gap-evidence",
        "license": license_name,
        "provenance": "generated from repeated privacy-safe capability_gap evidence; no external wholesale copy",
        "domain_hypothesis": "ros2-can-mqtt-integration",
    }


def gap(event_id: str, task: str) -> dict:
    return build_gap_event(
        event_id=event_id,
        task_text=task,
        summary="ROS2 QoS와 CAN-MQTT integration 반복 설계/진단 gap",
        router_result="NO_CAPABILITY",
        nearby_skill_ids=[],
        domain_hypothesis="ros2-can-mqtt-integration",
        issue_code="integration-gap",
        timestamp="2026-08-23T00:30:00Z",
    )


class GapPrivacyTests(unittest.TestCase):
    def test_gap_event_keeps_fingerprint_not_raw_task(self) -> None:
        event = gap("gap-1", "private raw task text")
        self.assertNotIn("task_text", event)
        self.assertTrue(event["task_fingerprint"].startswith("sha256:"))
        self.assertEqual(event["router_result"], "NO_CAPABILITY")
        self.assertEqual(event["skill_ids"], [])


class EligibilityTests(unittest.TestCase):
    def test_one_router_miss_does_not_create_skill(self) -> None:
        result = creator_eligibility(
            router_selected_ids=[], nearby_skill_ids=[], gap_event_count=1,
            reusable_workflow=True, repository_specific_one_off=False,
            positive_cases=["p1", "p2"], negative_cases=["n1"],
        )
        self.assertEqual(result.action, "WAIT")

    def test_trivial_task_is_no_action_when_not_reusable(self) -> None:
        result = creator_eligibility(
            router_selected_ids=[], nearby_skill_ids=[], gap_event_count=3,
            reusable_workflow=False, repository_specific_one_off=False,
            positive_cases=["p1", "p2"], negative_cases=["n1"],
        )
        self.assertEqual(result.action, "NO_ACTION")

    def test_repository_specific_one_off_is_no_action(self) -> None:
        result = creator_eligibility(
            router_selected_ids=[], nearby_skill_ids=[], gap_event_count=3,
            reusable_workflow=True, repository_specific_one_off=True,
            positive_cases=["p1", "p2"], negative_cases=["n1"],
        )
        self.assertEqual(result.action, "NO_ACTION")

    def test_existing_selected_skill_prevents_creation(self) -> None:
        result = creator_eligibility(
            router_selected_ids=["testing"], nearby_skill_ids=[], gap_event_count=3,
            reusable_workflow=True, repository_specific_one_off=False,
            positive_cases=["p1", "p2"], negative_cases=["n1"],
        )
        self.assertEqual(result.action, "NO_ACTION")

    def test_nearby_skill_prefers_extension_review(self) -> None:
        result = creator_eligibility(
            router_selected_ids=[], nearby_skill_ids=["resilient-error-handling"], gap_event_count=3,
            reusable_workflow=True, repository_specific_one_off=False,
            positive_cases=["p1", "p2"], negative_cases=["n1"],
        )
        self.assertEqual(result.action, "NO_ACTION")


class CandidateTests(unittest.TestCase):
    def test_repeated_reusable_gap_creates_runtime_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            state = Path(temp) / ".playbook-state"
            result = create_candidate(
                state_root=state,
                spec=creator_spec(),
                events=[gap("gap-1", "task a"), gap("gap-2", "task b")],
            )
            self.assertEqual(result["result"], "CANDIDATE_CREATED")
            candidate = Path(result["candidate_path"])
            self.assertTrue(candidate.is_relative_to(state / "candidates"))
            self.assertTrue((candidate / "SKILL.md").is_file())
            self.assertTrue((candidate / "proposal.json").is_file())
            self.assertTrue((candidate / "routing.json").is_file())

            proposal = json.loads((candidate / "proposal.json").read_text(encoding="utf-8"))
            routing = json.loads((candidate / "routing.json").read_text(encoding="utf-8"))
            self.assertEqual(proposal["change_type"], "create")
            self.assertEqual(proposal["source_id"], "internal-gap-evidence")
            self.assertEqual(proposal["license"], "repository")
            self.assertTrue(proposal["requires_human_gate"])
            self.assertEqual(len(routing["positive"]), 2)
            self.assertEqual(len(routing["negative"]), 1)

    def test_high_risk_permission_candidate_is_human_gated(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            result = create_candidate(
                state_root=Path(temp) / ".playbook-state",
                spec=creator_spec(permissions=["local_read", "network"]),
                events=[gap("gap-1", "task a"), gap("gap-2", "task b")],
            )
            self.assertTrue(result["proposal"]["requires_human_gate"])
            self.assertIn("network", result["proposal"]["permission_delta"]["add"])

    def test_unknown_license_is_rejected_before_candidate_creation(self) -> None:
        with self.assertRaises(CreatorError):
            validate_creator_spec(creator_spec(license_name="unknown"))

    def test_candidate_can_be_audited_by_skill_audit_cli(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            result = create_candidate(
                state_root=Path(temp) / ".playbook-state",
                spec=creator_spec(),
                events=[gap("gap-1", "task a"), gap("gap-2", "task b")],
            )
            audit = subprocess.run(
                [sys.executable, str(AUDIT), "--candidate", result["candidate_path"]],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )
            self.assertEqual(audit.returncode, 0, audit.stdout)
            self.assertIn("RESULT     PASS", audit.stdout)

    def test_insufficient_gap_evidence_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            state = Path(temp) / ".playbook-state"
            result = create_candidate(
                state_root=state,
                spec=creator_spec(),
                events=[gap("gap-1", "task a")],
            )
            self.assertEqual(result["result"], "WAIT")
            self.assertFalse((state / "candidates").exists())

    def test_duplicate_same_task_fingerprint_does_not_count_as_two_gaps(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            state = Path(temp) / ".playbook-state"
            result = create_candidate(
                state_root=state,
                spec=creator_spec(),
                events=[gap("gap-1", "same task"), gap("gap-2", "same task")],
            )
            self.assertEqual(result["result"], "WAIT")
            self.assertFalse((state / "candidates").exists())

    def test_creator_rejects_candidate_write_outside_playbook_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(CreatorError):
                create_candidate(
                    state_root=Path(temp) / "capability-library",
                    spec=creator_spec(),
                    events=[gap("gap-1", "task a"), gap("gap-2", "task b")],
                )


if __name__ == "__main__":
    unittest.main()
