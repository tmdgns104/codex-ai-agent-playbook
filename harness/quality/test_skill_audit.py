#!/usr/bin/env python3
"""Focused tests for V8.2 deterministic Skill audit."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from skill_audit import (
    AuditReport,
    _central_router_test_path,
    audit_candidate,
    audit_library,
    exact_trigger_overlaps,
    relative_link_failures,
)

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = Path(__file__).resolve().parent / "skill_audit.py"


class AuditClassificationTests(unittest.TestCase):
    def test_pass_warn_fail_classification(self) -> None:
        report = AuditReport()
        self.assertEqual(report.result, "PASS")
        self.assertEqual(report.exit_code(), 0)

        report.add("WARN", "test", "warning")
        self.assertEqual(report.result, "WARN")
        self.assertEqual(report.exit_code(), 0)
        self.assertEqual(report.exit_code(warn_exit_code=True), 2)

        report.add("FAIL", "test", "failure")
        self.assertEqual(report.result, "FAIL")
        self.assertEqual(report.exit_code(), 1)

    def test_current_library_has_no_audit_failures(self) -> None:
        report = audit_library(ROOT)
        failures = [item for item in report.findings if item.level == "FAIL"]
        self.assertEqual(failures, [], [item.message for item in failures])

    def test_json_cli_is_machine_readable(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--root", str(ROOT), "--json"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        payload = json.loads(result.stdout)
        self.assertIn(payload["result"], {"PASS", "WARN"})
        self.assertIn("findings", payload)


class AuditHelperTests(unittest.TestCase):
    def test_broken_relative_link_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            skill_dir = Path(temp)
            content = "See [missing](references/missing.md)."
            failures = relative_link_failures(skill_dir, content)
            self.assertEqual(failures, ["broken relative link: references/missing.md"])

    def test_existing_relative_link_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            skill_dir = Path(temp)
            reference = skill_dir / "references" / "ok.md"
            reference.parent.mkdir(parents=True)
            reference.write_text("ok\n", encoding="utf-8")
            self.assertEqual(relative_link_failures(skill_dir, "[ok](references/ok.md)"), [])

    def test_exact_trigger_overlap_is_reported_without_merging(self) -> None:
        capabilities = [
            {"id": "a", "triggers": ["same", "only-a"]},
            {"id": "b", "triggers": ["same", "only-b"]},
        ]
        overlaps = exact_trigger_overlaps(capabilities)
        self.assertEqual(overlaps, {"same": ["a", "b"]})
        self.assertEqual(capabilities[0]["id"], "a")
        self.assertEqual(capabilities[1]["id"], "b")

    def test_central_router_test_resolves_repository_layout(self) -> None:
        self.assertEqual(
            _central_router_test_path(ROOT),
            (ROOT / "harness" / "router" / "test_capability_router.py").resolve(),
        )

    def test_central_router_test_resolves_installed_layout(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            installed_test = root / "playbook-harness" / "router" / "test_capability_router.py"
            installed_test.parent.mkdir(parents=True)
            installed_test.write_text("# installed router fixture\n", encoding="utf-8")
            self.assertEqual(_central_router_test_path(root), installed_test.resolve())

    def test_curator_compress_candidate_is_auditable(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            candidate = Path(temp) / "candidate"
            candidate.mkdir()
            (candidate / "SKILL.md").write_text(
                "---\nname: sample-skill\ndescription: sample\n---\n\n"
                "# sample-skill\n\n## Evidence\nEvidence.\n\n"
                "## Stop / Handoff\nStop.\n\n## Source / Provenance\nSource.\n",
                encoding="utf-8",
            )
            proposal = {
                "proposal_id": "compress-sample-001",
                "change_type": "compress",
                "skill_id": "sample-skill",
                "base_version": 1,
                "base_hash": "sha256:base",
                "proposed_version": 2,
                "reason": "remove duplicated guidance",
                "evidence_refs": ["audit-warning-1"],
                "trigger_delta": {"add": [], "remove": []},
                "permission_delta": {"add": [], "remove": []},
                "requires_human_gate": False,
                "status": "candidate",
                "source_id": "internal",
                "license": "repository",
                "provenance": "synthetic test candidate",
            }
            (candidate / "proposal.json").write_text(
                json.dumps(proposal, ensure_ascii=False), encoding="utf-8"
            )
            (candidate / "routing.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "skill_id": "sample-skill",
                        "positive": ["sample positive"],
                        "negative": ["sample negative"],
                        "preserved_fixture": None,
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            report = audit_candidate(candidate)
            self.assertEqual(report.result, "PASS", [item.message for item in report.findings])


if __name__ == "__main__":
    unittest.main()
