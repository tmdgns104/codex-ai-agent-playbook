#!/usr/bin/env python3
"""Focused tests for the V8.1 pre-session Codex discovery bridge."""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import unittest
import uuid
from pathlib import Path

from discovery_bridge import (
    BRIDGE_MANAGED_BY,
    DiscoveryBridgeError,
    bridge_command,
    cleanup_bridge,
    prepare_bridge,
    verify_bridge,
)

ROOT = Path(__file__).resolve().parents[2]
RUNTIME_BASE = ROOT / ".playbook-runtime"
JWT_TASK = "JWT 인증 오류를 수정하고 regression test를 실행"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def core_skill_snapshot() -> dict[str, str]:
    base = ROOT / ".agents" / "skills"
    return {
        path.relative_to(base).as_posix(): file_sha256(path)
        for path in sorted(base.rglob("*"))
        if path.is_file()
    }


class DiscoveryBridgeTests(unittest.TestCase):
    def make_target(self) -> Path:
        target = RUNTIME_BASE / f"cap006-test-{uuid.uuid4().hex}"
        self.addCleanup(lambda: shutil.rmtree(target, ignore_errors=True))
        return target

    def make_session(self) -> str:
        return "s-" + uuid.uuid4().hex[:16]

    def test_trivial_task_creates_no_bridge(self) -> None:
        target = self.make_target()
        session = self.make_session()
        result = prepare_bridge(
            root=ROOT,
            task_text="README 오타 한 줄 수정",
            target_root=target,
            session=session,
        )
        self.assertEqual(result["result"], "NO_BRIDGE")
        self.assertFalse(result["codex_discovery_ready"])
        self.assertFalse((target / session).exists())

    def test_jwt_task_exposes_exactly_three_optional_skills(self) -> None:
        target = self.make_target()
        session = self.make_session()
        result = prepare_bridge(root=ROOT, task_text=JWT_TASK, target_root=target, session=session)
        self.assertEqual(result["result"], "BRIDGE_READY")
        self.assertEqual(
            set(result["materialized"]),
            {"security-review", "testing", "root-cause-debugging"},
        )
        skill_root = target / session / "cwd" / ".agents" / "skills"
        self.assertEqual(
            {path.name for path in skill_root.iterdir() if path.is_dir()},
            {"security-review", "testing", "root-cause-debugging"},
        )
        self.assertFalse((skill_root / "code-review").exists())

    def test_bridge_status_preserves_cap005_integrity(self) -> None:
        target = self.make_target()
        session = self.make_session()
        prepare_bridge(root=ROOT, task_text=JWT_TASK, target_root=target, session=session)
        result = verify_bridge(target_root=target, session=session)
        self.assertEqual(result["integrity"], "INTEGRITY_PASS")
        self.assertEqual(result["result"], "DISCOVERY_READY")
        self.assertTrue(result["codex_discovery_ready"])
        self.assertEqual(result["count"], 3)

    def test_launch_command_uses_cd_and_add_dir(self) -> None:
        target = self.make_target()
        session = self.make_session()
        prepare_bridge(root=ROOT, task_text=JWT_TASK, target_root=target, session=session)
        payload = bridge_command(target_root=target, session=session)
        argv = payload["argv"]
        self.assertEqual(argv[0], "codex")
        self.assertEqual(argv[1], "-C")
        self.assertEqual(Path(argv[2]).resolve(), (target / session / "cwd").resolve())
        self.assertEqual(argv[3], "--add-dir")
        self.assertEqual(Path(argv[4]).resolve(), ROOT.resolve())
        self.assertEqual(payload["result"], "COMMAND_READY")

    def test_prepare_does_not_modify_repository_core_skills(self) -> None:
        before = core_skill_snapshot()
        target = self.make_target()
        session = self.make_session()
        prepare_bridge(root=ROOT, task_text=JWT_TASK, target_root=target, session=session)
        after = core_skill_snapshot()
        self.assertEqual(before, after)

    def test_duplicate_session_is_rejected(self) -> None:
        target = self.make_target()
        session = self.make_session()
        prepare_bridge(root=ROOT, task_text=JWT_TASK, target_root=target, session=session)
        with self.assertRaises(DiscoveryBridgeError):
            prepare_bridge(root=ROOT, task_text=JWT_TASK, target_root=target, session=session)

    def test_unsafe_session_id_is_rejected(self) -> None:
        target = self.make_target()
        with self.assertRaises(Exception):
            prepare_bridge(root=ROOT, task_text=JWT_TASK, target_root=target, session="../escape")

    def test_target_outside_repository_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as outside:
            with self.assertRaises(DiscoveryBridgeError):
                prepare_bridge(
                    root=ROOT,
                    task_text=JWT_TASK,
                    target_root=Path(outside),
                    session=self.make_session(),
                )

    def test_tamper_is_detected_by_bridge_status(self) -> None:
        target = self.make_target()
        session = self.make_session()
        prepare_bridge(root=ROOT, task_text=JWT_TASK, target_root=target, session=session)
        skill_file = target / session / "cwd" / ".agents" / "skills" / "testing" / "SKILL.md"
        skill_file.write_text(skill_file.read_text(encoding="utf-8") + "\nTAMPER\n", encoding="utf-8")
        with self.assertRaises(DiscoveryBridgeError):
            verify_bridge(target_root=target, session=session)

    def test_managed_cleanup_removes_bridge_and_unmanaged_is_rejected(self) -> None:
        target = self.make_target()
        session = self.make_session()
        prepare_bridge(root=ROOT, task_text=JWT_TASK, target_root=target, session=session)
        cleaned = cleanup_bridge(target_root=target, session=session)
        self.assertEqual(cleaned["result"], "BRIDGE_CLEANED")
        self.assertFalse((target / session).exists())

        unmanaged = self.make_session()
        unmanaged_dir = target / unmanaged
        unmanaged_dir.mkdir(parents=True)
        (unmanaged_dir / "bridge.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "managed_by": "someone-else",
                    "session": unmanaged,
                }
            ),
            encoding="utf-8",
        )
        with self.assertRaises(DiscoveryBridgeError):
            cleanup_bridge(target_root=target, session=unmanaged)
        self.assertTrue(unmanaged_dir.exists())


if __name__ == "__main__":
    unittest.main()
