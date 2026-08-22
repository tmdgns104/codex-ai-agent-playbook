#!/usr/bin/env python3
"""Focused tests for V8.1 optional Skill task-scoped materialization."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from skill_materializer import (
    MANAGED_BY,
    MaterializationError,
    cleanup_session,
    prepare_session,
    validate_session_id,
    verify_session,
)

ROOT = Path(__file__).resolve().parents[2]


class SkillMaterializerTests(unittest.TestCase):
    def make_target(self) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temp = tempfile.TemporaryDirectory()
        return temp, Path(temp.name) / "runtime"

    def test_trivial_task_creates_no_session(self) -> None:
        temp, target = self.make_target()
        self.addCleanup(temp.cleanup)
        payload = prepare_session(
            root=ROOT,
            task_text="README 오타 한 줄 수정",
            target_root=target,
            session="trivial",
        )
        self.assertEqual(payload["result"], "NO_MATERIALIZATION")
        self.assertEqual(payload["materialized"], [])
        self.assertFalse((target / "trivial").exists())

    def test_jwt_task_materializes_selected_three_skills(self) -> None:
        temp, target = self.make_target()
        self.addCleanup(temp.cleanup)
        payload = prepare_session(
            root=ROOT,
            task_text="JWT 인증 오류를 수정하고 regression test를 실행",
            target_root=target,
            session="jwt",
        )
        ids = [item["id"] for item in payload["materialized"]]
        self.assertEqual(ids, ["security-review", "testing", "root-cause-debugging"])
        self.assertEqual(payload["profile"], "strict")
        self.assertFalse(payload["codex_discovery_ready"])
        self.assertFalse(payload["side_effects_executed"])
        for capability_id in ids:
            self.assertTrue((target / "jwt" / "skills" / capability_id / "SKILL.md").is_file())

    def test_profile_gated_testing_is_materialized_under_strict_profile(self) -> None:
        temp, target = self.make_target()
        self.addCleanup(temp.cleanup)
        payload = prepare_session(
            root=ROOT,
            task_text="JWT 인증 오류를 수정하고 regression test를 실행",
            target_root=target,
            session="profile",
        )
        testing = next(item for item in payload["materialized"] if item["id"] == "testing")
        self.assertEqual(testing["decision"], "PROFILE_GATED")

    def test_wrapper_only_task_is_not_materialized(self) -> None:
        temp, target = self.make_target()
        self.addCleanup(temp.cleanup)
        payload = prepare_session(
            root=ROOT,
            task_text="최신 API 공식 문서를 확인",
            target_root=target,
            session="docs",
        )
        self.assertEqual(payload["result"], "NO_MATERIALIZATION")
        self.assertIn({"id": "documentation-lookup", "reason": "not-a-skill"}, payload["skipped"])
        self.assertFalse((target / "docs").exists())

    def test_status_passes_when_hashes_match(self) -> None:
        temp, target = self.make_target()
        self.addCleanup(temp.cleanup)
        prepare_session(
            root=ROOT,
            task_text="코드 diff를 리뷰하고 품질 검토",
            target_root=target,
            session="status",
        )
        result = verify_session(target_root=target, session="status")
        self.assertEqual(result["result"], "INTEGRITY_PASS")
        self.assertEqual(result["materialized_count"], 1)

    def test_status_fails_after_materialized_file_tamper(self) -> None:
        temp, target = self.make_target()
        self.addCleanup(temp.cleanup)
        prepare_session(
            root=ROOT,
            task_text="코드 diff를 리뷰하고 품질 검토",
            target_root=target,
            session="tamper",
        )
        skill = target / "tamper" / "skills" / "code-review" / "SKILL.md"
        skill.write_text(skill.read_text(encoding="utf-8") + "\nTAMPER\n", encoding="utf-8")
        with self.assertRaises(MaterializationError):
            verify_session(target_root=target, session="tamper")

    def test_duplicate_session_prepare_fails(self) -> None:
        temp, target = self.make_target()
        self.addCleanup(temp.cleanup)
        kwargs = dict(
            root=ROOT,
            task_text="코드 diff를 리뷰하고 품질 검토",
            target_root=target,
            session="duplicate",
        )
        prepare_session(**kwargs)
        with self.assertRaises(MaterializationError):
            prepare_session(**kwargs)

    def test_unsafe_session_id_fails(self) -> None:
        for session in ("../escape", "a/b", "a\\b", "", "x" * 65):
            with self.subTest(session=session):
                with self.assertRaises(MaterializationError):
                    validate_session_id(session)

    def test_cleanup_refuses_unmanaged_directory(self) -> None:
        temp, target = self.make_target()
        self.addCleanup(temp.cleanup)
        session_dir = target / "unmanaged"
        session_dir.mkdir(parents=True)
        (session_dir / "activation.json").write_text(
            json.dumps({"managed_by": "someone-else", "schema_version": 1, "session": "unmanaged"}),
            encoding="utf-8",
        )
        with self.assertRaises(MaterializationError):
            cleanup_session(target_root=target, session="unmanaged")
        self.assertTrue(session_dir.exists())

    def test_cleanup_removes_only_managed_session(self) -> None:
        temp, target = self.make_target()
        self.addCleanup(temp.cleanup)
        prepare_session(
            root=ROOT,
            task_text="코드 diff를 리뷰하고 품질 검토",
            target_root=target,
            session="cleanup",
        )
        manifest = json.loads((target / "cleanup" / "activation.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["managed_by"], MANAGED_BY)
        result = cleanup_session(target_root=target, session="cleanup")
        self.assertEqual(result["result"], "CLEANED")
        self.assertFalse((target / "cleanup").exists())


if __name__ == "__main__":
    unittest.main()
