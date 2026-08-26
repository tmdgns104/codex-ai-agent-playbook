"""Regression guards for artifacts explicitly frozen by V8.4-003."""

from __future__ import annotations

import hashlib
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
PROTECTED_SHA256 = {
    "tasks/V8_4-EXPERT-CONTEXT-001.md": "bea3db0a7351a10358290b603b3cfe329190c379c364983ed9b8e652521c58fd",
    "tasks/V8_4-EXPERT-CONTEXT-002.md": "fb4b1d474572e54e6b5c0cf413d9de9f32e1486d00e5325ef532e377bc7be572",
    "evaluation/external-skills/reports/v8.4-design-summary.json": "6d29f8ae11aac29a5fd8d5cb2b03299e6213a9d5fa8940705b6ea47e70960548",
    "evaluation/external-skills/reports/v8.4-transport-decision-summary.json": "4fceb162f54f229f4579052bb65390cc73f643d7316e06910ad6bb1e89c4e176",
    "evaluation/external-skills/benchmark-results.json": "21cb7165c4e02397fdafa9bc5d20f715e723ff351965cf71e00e42f6e7e80249",
    "evaluation/external-skills/adoption-decisions.json": "4078ba8597bc9483606c41dcae2a88d5096de13ce22cb6c1084665079433bbe3",
    "evaluation/external-skills/adapted-contexts.json": "f972f89a57dd853eaf7f88648e8a5ce9f6a26f9335e6f03131a48222246e9816",
    "evaluation/external-skills/reports/stage-b-failure-analysis.json": "22f590325b312ec52b9ab54e889eff7f6c23eb0c3064229d738a4dada307c692",
    "evaluation/external-skills/reports/stage-b-wave2-comparison.json": "7566322a62064797df4fefbf0319794aab40b1cd66df8cec77c934047f031a6e",
    "evaluation/external-skills/reports/stage-b-wave2-execution-summary.json": "48ba11e17931c406fc8c1026727bb6dbbce58c2c52652c16e895b15fff7f3c9b",
    "harness/router/capability_router.py": "f6897fa59fa02e6b2dc21bc3295e79f41c648b9c795bb5df03cb12ceb5b3f2b2",
    "harness/router/scoring.py": "80866867ba3997b537233b2d8134ace8504126c53a7804d03c94966a98f5bf0e",
    "harness/activation/playbook_launch.py": "7e53c79e40635bfc98b14fee77213051a0576a0f8e567a2fe36ea0fa5d19540d",
    "harness/activation/capability_manager.py": "05aa3e36c82e9cb0ac3baf661b05072d5962437ae1704035e0db013123f90b95",
    "harness/activation/skill_materializer.py": "ab211d9b0b956f15c29f8d391c6b5b2016c8450d08007a6f00b877547790dd0f",
    "harness/activation/discovery_bridge.py": "40d3ecf319998b5708d83d9de8d5acb993ab462856d95ec3c649210ca26c306f",
    "capability-library/registry.json": "2c2aec89ea40655d99497064c91d74b6c905bf0ce1d87bbbcdda2a071480a4a9",
    ".codex/AGENTS.md": "ebcd3c6627b4679101f98ce59897f528622db9f50d2cd601693f3940b968320c",
}
V83_EVIDENCE_AGGREGATE_SHA256 = "001ed39bc3d95c8506b8ca98ec9d9aa792389a5e1361622fa4a81c6ca07f06ab"


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ProtectedArtifactTests(unittest.TestCase):
    def test_explicit_protected_artifact_hashes_are_unchanged(self) -> None:
        for relative, expected in PROTECTED_SHA256.items():
            with self.subTest(path=relative):
                self.assertEqual(expected, file_sha256(REPO_ROOT / relative))

    def test_all_v83_stage_b_evidence_hashes_are_unchanged(self) -> None:
        evidence_root = REPO_ROOT / "evaluation" / "external-skills" / "evidence"
        files = sorted(evidence_root.rglob("*.json"), key=lambda path: path.relative_to(REPO_ROOT).as_posix())
        self.assertEqual(40, len(files))
        aggregate = hashlib.sha256()
        for path in files:
            relative = path.relative_to(REPO_ROOT).as_posix()
            aggregate.update(relative.encode("utf-8"))
            aggregate.update(b"\0")
            aggregate.update(file_sha256(path).encode("ascii"))
            aggregate.update(b"\n")
        self.assertEqual(V83_EVIDENCE_AGGREGATE_SHA256, aggregate.hexdigest())


if __name__ == "__main__":
    unittest.main()
