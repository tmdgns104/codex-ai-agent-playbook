#!/usr/bin/env python3
"""Focused tests for the V8.1 one-command automatic Skill launcher."""

from __future__ import annotations

import re
import shutil
import unittest
import uuid
from pathlib import Path

from playbook_launch import (
    build_launch_plan,
    execute_launch,
    generate_session_id,
)

ROOT = Path(__file__).resolve().parents[2]
RUNTIME_BASE = ROOT / ".playbook-runtime"
JWT_TASK = "JWT 인증 오류를 수정하고 regression test를 실행"


class Completed:
    def __init__(self, returncode: int) -> None:
        self.returncode = returncode


class PlaybookLaunchTests(unittest.TestCase):
    def make_target(self) -> Path:
        target = RUNTIME_BASE / f"cap007-test-{uuid.uuid4().hex}"
        self.addCleanup(lambda: shutil.rmtree(target, ignore_errors=True))
        return target

    def make_session(self) -> str:
        return "launch-test-" + uuid.uuid4().hex[:12]

    def test_trivial_task_uses_zero_skills_and_repo_cwd(self) -> None:
        target = self.make_target()
        task = "README 오타 한 줄 수정"
        plan = build_launch_plan(
            root=ROOT,
            task_text=task,
            target_root=target,
            session=self.make_session(),
        )
        self.assertEqual(plan["result"], "READY")
        self.assertEqual(plan["profile"], "minimal")
        self.assertEqual(plan["skills"], [])
        self.assertEqual(plan["count"], 0)
        self.assertFalse(plan["bridge"])
        self.assertEqual(plan["argv"][:3], ["codex", "-C", str(ROOT.resolve())])
        self.assertEqual(plan["argv"][-2:], ["--", task])

    def test_jwt_task_auto_selects_exactly_three_skills(self) -> None:
        target = self.make_target()
        session = self.make_session()
        plan = build_launch_plan(
            root=ROOT,
            task_text=JWT_TASK,
            target_root=target,
            session=session,
        )
        self.assertEqual(plan["result"], "READY")
        self.assertEqual(plan["profile"], "strict")
        self.assertEqual(
            set(plan["skills"]),
            {"security-review", "testing", "root-cause-debugging"},
        )
        self.assertEqual(plan["count"], 3)
        self.assertTrue(plan["bridge"])
        self.assertIn("--add-dir", plan["argv"])
        self.assertTrue((target / session / "cwd" / ".agents" / "skills").is_dir())

    def test_task_prompt_is_present_exactly_once_after_option_terminator(self) -> None:
        target = self.make_target()
        plan = build_launch_plan(
            root=ROOT,
            task_text=JWT_TASK,
            target_root=target,
            session=self.make_session(),
        )
        self.assertEqual(plan["argv"].count(JWT_TASK), 1)
        self.assertEqual(plan["argv"][-2], "--")
        self.assertEqual(plan["argv"][-1], JWT_TASK)

    def test_option_like_task_cannot_become_codex_option(self) -> None:
        target = self.make_target()
        task = "--dangerously-bypass-approvals-and-sandbox 문구를 README 예제로 설명"
        plan = build_launch_plan(
            root=ROOT,
            task_text=task,
            target_root=target,
            session=self.make_session(),
        )
        self.assertEqual(plan["argv"][-2:], ["--", task])
        self.assertEqual(plan["argv"].count(task), 1)

    def test_dry_run_does_not_spawn_and_cleans_bridge(self) -> None:
        target = self.make_target()
        session = self.make_session()
        plan = build_launch_plan(root=ROOT, task_text=JWT_TASK, target_root=target, session=session)
        called = []

        def runner(*args, **kwargs):
            called.append((args, kwargs))
            return Completed(0)

        result = execute_launch(plan, dry_run=True, runner=runner)
        self.assertEqual(called, [])
        self.assertEqual(result["result"], "DRY_RUN_COMPLETE")
        self.assertEqual(result["cleanup"], "BRIDGE_CLEANED")
        self.assertFalse((target / session).exists())

    def test_successful_child_exit_is_propagated_and_bridge_cleaned(self) -> None:
        target = self.make_target()
        session = self.make_session()
        plan = build_launch_plan(root=ROOT, task_text=JWT_TASK, target_root=target, session=session)
        captured = []

        def runner(argv, check=False):
            captured.append((argv, check))
            return Completed(0)

        result = execute_launch(plan, runner=runner)
        self.assertEqual(result["codex_exit"], 0)
        self.assertEqual(result["result"], "COMPLETE")
        self.assertEqual(result["cleanup"], "BRIDGE_CLEANED")
        self.assertEqual(captured[0][0], plan["argv"])
        self.assertFalse(captured[0][1])
        self.assertFalse((target / session).exists())

    def test_nonzero_child_exit_is_propagated_and_bridge_cleaned(self) -> None:
        target = self.make_target()
        session = self.make_session()
        plan = build_launch_plan(root=ROOT, task_text=JWT_TASK, target_root=target, session=session)

        def runner(argv, check=False):
            return Completed(7)

        result = execute_launch(plan, runner=runner)
        self.assertEqual(result["codex_exit"], 7)
        self.assertEqual(result["result"], "FAIL")
        self.assertEqual(result["cleanup"], "BRIDGE_CLEANED")
        self.assertFalse((target / session).exists())

    def test_spawn_failure_still_cleans_bridge(self) -> None:
        target = self.make_target()
        session = self.make_session()
        plan = build_launch_plan(root=ROOT, task_text=JWT_TASK, target_root=target, session=session)

        def runner(argv, check=False):
            raise FileNotFoundError("codex missing")

        result = execute_launch(plan, runner=runner)
        self.assertEqual(result["codex_exit"], 1)
        self.assertEqual(result["result"], "FAIL")
        self.assertEqual(result["cleanup"], "BRIDGE_CLEANED")
        self.assertIn("codex missing", result["error"])
        self.assertFalse((target / session).exists())

    def test_keep_runtime_is_opt_in(self) -> None:
        target = self.make_target()
        session = self.make_session()
        plan = build_launch_plan(root=ROOT, task_text=JWT_TASK, target_root=target, session=session)
        result = execute_launch(plan, dry_run=True, keep_runtime=True)
        self.assertEqual(result["cleanup"], "KEPT")
        self.assertTrue((target / session).exists())

    def test_human_gate_blocks_external_write_before_bridge(self) -> None:
        target = self.make_target()
        session = self.make_session()
        plan = build_launch_plan(
            root=ROOT,
            task_text="GitHub에 commit push하고 PR 생성",
            target_root=target,
            session=session,
        )
        self.assertEqual(plan["result"], "HUMAN_GATE_REQUIRED")
        self.assertEqual(plan["argv"], [])
        self.assertFalse(plan["bridge"])
        self.assertFalse((target / session).exists())

    def test_network_review_blocks_network_capability_before_bridge(self) -> None:
        target = self.make_target()
        session = self.make_session()
        plan = build_launch_plan(
            root=ROOT,
            task_text="최신 API 공식 문서를 확인",
            target_root=target,
            session=session,
        )
        self.assertEqual(plan["result"], "NETWORK_REVIEW_REQUIRED")
        self.assertEqual(plan["argv"], [])
        self.assertFalse((target / session).exists())

    def test_generated_session_id_matches_safe_contract(self) -> None:
        session = generate_session_id()
        self.assertRegex(session, re.compile(r"^launch-[0-9a-f]{8}$"))


if __name__ == "__main__":
    unittest.main()
