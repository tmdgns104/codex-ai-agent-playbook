#!/usr/bin/env python3
"""Focused CAP-008 tests for installed catalog / arbitrary repository use."""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from playbook_launch import build_launch_plan, execute_launch

CATALOG_ROOT = Path(__file__).resolve().parents[2]
JWT_TASK = "JWT 인증 오류를 수정하고 regression test를 실행"


class InstalledLauncherTests(unittest.TestCase):
    def make_repo(self) -> Path:
        path = Path(tempfile.mkdtemp(prefix="cap008-target-"))
        self.addCleanup(lambda: shutil.rmtree(path, ignore_errors=True))
        (path / ".git").mkdir()
        return path

    def test_catalog_can_be_separate_from_target_repository(self) -> None:
        repo = self.make_repo()
        self.assertFalse((repo / "capability-library").exists())

        plan = build_launch_plan(
            root=repo,
            catalog_root=CATALOG_ROOT,
            task_text=JWT_TASK,
            target_root=repo / ".playbook-runtime",
            session="cap008-detached",
        )

        self.assertEqual(plan["result"], "READY")
        self.assertEqual(plan["profile"], "strict")
        self.assertEqual(
            set(plan["skills"]),
            {"security-review", "testing", "root-cause-debugging"},
        )
        self.assertEqual(Path(plan["catalog_root"]).resolve(), CATALOG_ROOT.resolve())
        self.assertTrue(plan["bridge"])
        self.assertTrue((repo / ".playbook-runtime" / "cap008-detached").is_dir())
        self.assertFalse((repo / "capability-library").exists())

        result = execute_launch(plan, dry_run=True)
        self.assertEqual(result["result"], "DRY_RUN_COMPLETE")
        self.assertEqual(result["cleanup"], "BRIDGE_CLEANED")
        self.assertFalse((repo / ".playbook-runtime" / "cap008-detached").exists())

    def test_trivial_detached_repository_needs_no_runtime(self) -> None:
        repo = self.make_repo()
        plan = build_launch_plan(
            root=repo,
            catalog_root=CATALOG_ROOT,
            task_text="README 오타 한 줄 수정",
            target_root=repo / ".playbook-runtime",
            session="cap008-trivial",
        )

        self.assertEqual(plan["result"], "READY")
        self.assertEqual(plan["profile"], "minimal")
        self.assertEqual(plan["skills"], [])
        self.assertFalse(plan["bridge"])
        self.assertEqual(plan["argv"][:3], ["codex", "-C", str(repo.resolve())])
        self.assertFalse((repo / ".playbook-runtime" / "cap008-trivial").exists())


if __name__ == "__main__":
    unittest.main()
