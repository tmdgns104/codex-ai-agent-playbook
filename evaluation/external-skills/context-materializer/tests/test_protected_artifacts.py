from __future__ import annotations

import hashlib
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]

PROTECTED_FILES = {
    "tasks/V8_4-EXPERT-CONTEXT-001.md": "bea3db0a7351a10358290b603b3cfe329190c379c364983ed9b8e652521c58fd",
    "tasks/V8_4-EXPERT-CONTEXT-002.md": "fb4b1d474572e54e6b5c0cf413d9de9f32e1486d00e5325ef532e377bc7be572",
    "tasks/V8_4-EXPERT-CONTEXT-003.md": "5d3cde649cdaa1c84e0ca3fbcd86e03e71b5fb1dda314fc796ba95c54c40b17b",
    "tasks/V8_4-EXPERT-CONTEXT-004.md": "0db5b84f85d138d7547fa71b29d593f88d045807b099af32c3d8229d7f9dc689",
    "tasks/V8_4-EXPERT-CONTEXT-005.md": "dba099e91719714b74de10c4c58403cd0eac05a0219c6f2b843178f500f49b36",
    "evaluation/external-skills/reports/v8.4-design-summary.json": "6d29f8ae11aac29a5fd8d5cb2b03299e6213a9d5fa8940705b6ea47e70960548",
    "evaluation/external-skills/reports/v8.4-transport-decision-summary.json": "4fceb162f54f229f4579052bb65390cc73f643d7316e06910ad6bb1e89c4e176",
    "evaluation/external-skills/reports/v8.4-schema-validator-summary.json": "1ee46ace36c9cfb2dbf8ab8bfea96a70b1a73ab94bb3a0368f2f2d5d816a43cc",
    "evaluation/external-skills/reports/v8.4-compiler-summary.json": "5d27741d18b49bb20b8e8b62e97ca0ca68d7c7caaf58899b8bb6b7204124cd49",
    "evaluation/external-skills/reports/v8.4-selector-budget-summary.json": "10c7b2f1d5878dd8cac0a32d71f5920eae59288ecad5a99bf356b8a4272ef8e0",
    "evaluation/external-skills/benchmark-results.json": "21cb7165c4e02397fdafa9bc5d20f715e723ff351965cf71e00e42f6e7e80249",
    "evaluation/external-skills/adoption-decisions.json": "4078ba8597bc9483606c41dcae2a88d5096de13ce22cb6c1084665079433bbe3",
    "evaluation/external-skills/adapted-contexts.json": "f972f89a57dd853eaf7f88648e8a5ce9f6a26f9335e6f03131a48222246e9816",
    "harness/router/capability_router.py": "f6897fa59fa02e6b2dc21bc3295e79f41c648b9c795bb5df03cb12ceb5b3f2b2",
    "harness/router/scoring.py": "80866867ba3997b537233b2d8134ace8504126c53a7804d03c94966a98f5bf0e",
    "harness/activation/playbook_launch.py": "7e53c79e40635bfc98b14fee77213051a0576a0f8e567a2fe36ea0fa5d19540d",
    "harness/activation/capability_manager.py": "05aa3e36c82e9cb0ac3baf661b05072d5962437ae1704035e0db013123f90b95",
    "harness/activation/skill_materializer.py": "ab211d9b0b956f15c29f8d391c6b5b2016c8450d08007a6f00b877547790dd0f",
    "harness/activation/discovery_bridge.py": "40d3ecf319998b5708d83d9de8d5acb993ab462856d95ec3c649210ca26c306f",
    "capability-library/registry.json": "2c2aec89ea40655d99497064c91d74b6c905bf0ce1d87bbbcdda2a071480a4a9",
    ".codex/AGENTS.md": "ebcd3c6627b4679101f98ce59897f528622db9f50d2cd601693f3940b968320c",
}

PROTECTED_TREES = {
    "evaluation/external-skills/context-contract": (14, "98fc03d723cddfab69811e075bb98377eed3abcad11eeb961d64550b0fa62f4f"),
    "evaluation/external-skills/context-compiler": (6, "5f20cd02868ea8c9fcf9e3ae8b54e4e8b04ede55213c586e87ea6183749f72a2"),
    "evaluation/external-skills/adapted-contexts": (6, "b08b81615e246f4f5c5a3209596867d21b6a34dd6445efd6a331f3b31fb2282d"),
    "evaluation/external-skills/context-selector": (6, "46791ddf9f03c3348c7b11cc75a6c37430746fa535342b5c5c4e97d02202c5a7"),
    "evaluation/external-skills/evidence": (40, "001ed39bc3d95c8506b8ca98ec9d9aa792389a5e1361622fa4a81c6ca07f06ab"),
}


def aggregate_tree(relative_root: str) -> tuple[int, str]:
    root = REPO_ROOT / relative_root
    files = sorted(
        (path for path in root.rglob("*") if path.is_file() and "__pycache__" not in path.parts),
        key=lambda path: path.relative_to(REPO_ROOT).as_posix(),
    )
    digest = hashlib.sha256()
    for path in files:
        relative = path.relative_to(REPO_ROOT).as_posix()
        file_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_hash.encode("ascii"))
        digest.update(b"\n")
    return len(files), digest.hexdigest()


class ProtectedArtifactTests(unittest.TestCase):
    def test_explicit_v8_1_to_v8_4_artifacts_are_unchanged(self):
        for relative, expected in PROTECTED_FILES.items():
            with self.subTest(path=relative):
                self.assertEqual(expected, hashlib.sha256((REPO_ROOT / relative).read_bytes()).hexdigest())

    def test_protected_trees_are_unchanged(self):
        for relative, expected in PROTECTED_TREES.items():
            with self.subTest(path=relative):
                self.assertEqual(expected, aggregate_tree(relative))


if __name__ == "__main__":
    unittest.main()
