#!/usr/bin/env python3
"""Focused tests for V8.2 metadata-first Skill Curator."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from curator import (
    CuratorError,
    archive_review,
    build_curator_proposal,
    build_curator_report,
    create_package_candidate,
    validate_trigger_maintenance,
    warn_candidates,
)
from promotion import package_hash


LONG_BLOCK = "Repeated long example line for extraction and compression.\n" * 12
SKILL_BODY = """---
name: synthetic-skill
description: >-
  Synthetic Skill used only for focused Curator tests.
---

# synthetic-skill

## Purpose / Scope

SENTINEL_PRIVATE_BODY_ALPHA. This workflow is intentionally synthetic.

## When to use

Use for deterministic synthetic test work.

## Workflow

1. Inspect evidence.
2. Apply a focused change.
3. Verify the result.

## Evidence

Record commands and concrete verification results.

## Stop / Handoff

Stop when evidence is missing or scope expands.

## Source / Provenance

- source_id: `internal-test`
- license: `repository`

""" + LONG_BLOCK


class SyntheticLibrary:
    def __init__(self, base: Path, *, oversized_warning: int = 200) -> None:
        self.root = base / "repo"
        self.active = self.root / "capability-library" / "skills" / "optional" / "synthetic-skill"
        governance = self.root / "capability-library" / "governance"
        governance.mkdir(parents=True)
        self.active.mkdir(parents=True)
        (self.active / "SKILL.md").write_text(SKILL_BODY, encoding="utf-8", newline="\n")
        (self.active / "assets").mkdir()
        (self.active / "assets" / "keep.txt").write_text("KEEP-RESOURCE\n", encoding="utf-8")
        (self.active / "tests").mkdir()
        (self.active / "tests" / "routing.json").write_text(
            json.dumps({"positive": ["existing positive"], "negative": ["existing negative"]}) + "\n",
            encoding="utf-8",
        )
        (governance / "policy.json").write_text(
            json.dumps({"schema_version": 1, "skill_soft_warning_bytes": oversized_warning}) + "\n",
            encoding="utf-8",
        )
        registry = {
            "schema_version": 1,
            "capabilities": [
                {
                    "id": "synthetic-skill",
                    "type": "skill",
                    "path": "capability-library/skills/optional/synthetic-skill",
                    "triggers": ["synthetic trigger", "shared trigger"],
                    "permissions": ["local_read"],
                    "source_id": "internal-test",
                    "license": "repository",
                },
                {
                    "id": "second-skill",
                    "type": "skill",
                    "path": "capability-library/skills/optional/second-skill",
                    "triggers": ["shared trigger"],
                    "permissions": ["local_read"],
                    "source_id": "internal-test",
                    "license": "repository",
                },
            ],
        }
        second = self.root / "capability-library" / "skills" / "optional" / "second-skill"
        second.mkdir(parents=True)
        (second / "SKILL.md").write_text(SKILL_BODY.replace("synthetic-skill", "second-skill"), encoding="utf-8")
        (self.root / "capability-library" / "registry.json").write_text(
            json.dumps(registry, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def proposal(self, change_type: str, **kwargs) -> dict:
        return build_curator_proposal(
            proposal_id=kwargs.pop("proposal_id", f"prop-{change_type}"),
            change_type=change_type,
            skill_id="synthetic-skill",
            base_version=1,
            base_hash=package_hash(self.active),
            reason=kwargs.pop("reason", "deterministic Curator warning/evidence"),
            evidence_refs=kwargs.pop("evidence_refs", ["audit:synthetic"]),
            source_id="internal-test",
            license_name="repository",
            provenance="ACTIVE registry + deterministic Curator report",
            **kwargs,
        )


class ReportTests(unittest.TestCase):
    def test_report_is_metadata_only_and_warn_candidates_are_filtered(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            lib = SyntheticLibrary(Path(temp))
            report = build_curator_report(lib.root)
            serialized = json.dumps(report, ensure_ascii=False)
            self.assertFalse(report["body_included"])
            self.assertNotIn("SENTINEL_PRIVATE_BODY_ALPHA", serialized)
            self.assertIn("synthetic-skill", report["warn_candidate_ids"])
            self.assertTrue(all(item["warnings"] for item in warn_candidates(report)))

    def test_report_uses_deterministic_event_metrics_without_raw_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            lib = SyntheticLibrary(Path(temp), oversized_warning=100000)
            events = [
                {"event_type": "verified_usage", "skill_ids": ["synthetic-skill"], "verification": "pass", "timestamp": "2026-08-20T00:00:00Z"},
                {"event_type": "routing_false_positive", "skill_ids": ["synthetic-skill"], "verification": "fail", "timestamp": "2026-08-21T00:00:00Z"},
            ]
            report = build_curator_report(lib.root, events=events)
            item = next(row for row in report["skills"] if row["skill_id"] == "synthetic-skill")
            self.assertEqual(item["metrics"]["usage_count"], 1)
            self.assertEqual(item["metrics"]["verified_success_count"], 1)
            self.assertEqual(item["metrics"]["routing_false_positive_count"], 1)
            self.assertNotIn("task_text", json.dumps(report))


class PackageCandidateTests(unittest.TestCase):
    def test_compress_candidate_reduces_selected_block_and_preserves_resources(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            lib = SyntheticLibrary(Path(temp))
            state = Path(temp) / ".playbook-state"
            active_before = (lib.active / "SKILL.md").read_bytes()
            resource_before = (lib.active / "assets" / "keep.txt").read_bytes()
            proposal = lib.proposal("compress", proposal_id="prop-compress-001")
            candidate = create_package_candidate(
                state_root=state,
                active_dir=lib.active,
                proposal=proposal,
                operations=[{"old": LONG_BLOCK, "new": "Long example condensed; see focused workflow above.\n"}],
                positive_cases=["compress duplicated example while preserving workflow"],
                negative_cases=["rewrite the whole Skill for style only"],
            )
            self.assertEqual((lib.active / "SKILL.md").read_bytes(), active_before)
            self.assertEqual((lib.active / "assets" / "keep.txt").read_bytes(), resource_before)
            self.assertEqual((candidate / "assets" / "keep.txt").read_bytes(), resource_before)
            self.assertLess((candidate / "SKILL.md").stat().st_size, len(active_before))
            self.assertTrue((candidate / "tests" / "routing.json").is_file())

    def test_extract_reference_creates_valid_relative_link_and_keeps_active_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            lib = SyntheticLibrary(Path(temp))
            state = Path(temp) / ".playbook-state"
            active_before = (lib.active / "SKILL.md").read_bytes()
            proposal = lib.proposal("extract-reference", proposal_id="prop-reference-001")
            candidate = create_package_candidate(
                state_root=state,
                active_dir=lib.active,
                proposal=proposal,
                operations=[{"old": LONG_BLOCK, "reference_path": "references/long-example.md", "title": "Long example"}],
                positive_cases=["move long reusable example to reference"],
                negative_cases=["move core workflow out of SKILL.md"],
            )
            content = (candidate / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("[Long example](references/long-example.md)", content)
            self.assertTrue((candidate / "references" / "long-example.md").is_file())
            self.assertEqual((lib.active / "SKILL.md").read_bytes(), active_before)
            self.assertEqual((candidate / "assets" / "keep.txt").read_text(encoding="utf-8"), "KEEP-RESOURCE\n")


class StructuralProposalTests(unittest.TestCase):
    def test_split_and_merge_are_human_gated_and_not_auto_promoted(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            lib = SyntheticLibrary(Path(temp))
            split = lib.proposal("split", related_skill_ids=["synthetic-a", "synthetic-b"])
            merge = lib.proposal("merge", related_skill_ids=["second-skill"])
            for proposal in (split, merge):
                self.assertTrue(proposal["requires_human_gate"])
                self.assertFalse(proposal["auto_promote_allowed"])

    def test_trigger_narrow_requires_regression_and_can_avoid_scope_expansion_gate(self) -> None:
        validate_trigger_maintenance(
            change_type="trigger-narrow",
            base_triggers=["broad", "specific"],
            trigger_delta={"add": [], "remove": ["broad"]},
            positive_cases=["specific intended task"],
            negative_cases=["broad unrelated task"],
        )
        with tempfile.TemporaryDirectory() as temp:
            lib = SyntheticLibrary(Path(temp))
            proposal = lib.proposal("trigger-narrow", trigger_delta={"add": [], "remove": ["shared trigger"]})
            self.assertFalse(proposal["requires_human_gate"])

    def test_trigger_expand_requires_human_gate(self) -> None:
        validate_trigger_maintenance(
            change_type="trigger-expand",
            base_triggers=["existing"],
            trigger_delta={"add": ["new precise trigger"], "remove": []},
            positive_cases=["new intended task"],
            negative_cases=["unrelated task"],
        )
        with tempfile.TemporaryDirectory() as temp:
            lib = SyntheticLibrary(Path(temp))
            proposal = lib.proposal("trigger-expand", trigger_delta={"add": ["new precise trigger"], "remove": []})
            self.assertTrue(proposal["requires_human_gate"])
            self.assertFalse(proposal["auto_promote_allowed"])

    def test_delete_is_not_a_supported_curator_action(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            lib = SyntheticLibrary(Path(temp))
            with self.assertRaises(CuratorError):
                lib.proposal("delete")


class ArchiveProtectionTests(unittest.TestCase):
    @staticmethod
    def _report(*, usage: int = 0, success: int = 0, failure: int = 0, **protection: bool) -> dict:
        return {
            "metrics": {
                "usage_count": usage,
                "verified_success_count": success,
                "verified_failure_count": failure,
            },
            "protection": {key: bool(protection.get(key, False)) for key in ("pinned", "specialist", "externally_referenced", "recently_restored")},
        }

    def test_low_usage_alone_does_not_archive(self) -> None:
        result = archive_review(self._report(usage=0, success=0, failure=0))
        self.assertEqual(result.action, "NO_ACTION")

    def test_low_usage_plus_verified_failure_is_review_not_auto_archive(self) -> None:
        result = archive_review(self._report(usage=1, success=0, failure=2))
        self.assertEqual(result.action, "REVIEW")

    def test_pinned_and_specialist_protection_block_archive_review(self) -> None:
        for key in ("pinned", "specialist"):
            result = archive_review(self._report(**{key: True}), deprecated_technology=True)
            self.assertEqual(result.action, "NO_ACTION")
            self.assertIn("protected", result.reason)

    def test_archive_proposal_requires_human_gate_and_rejects_protected_skill(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            lib = SyntheticLibrary(Path(temp))
            proposal = lib.proposal("archive", evidence_refs=["curator:deprecated"])
            self.assertTrue(proposal["requires_human_gate"])
            self.assertFalse(proposal["auto_promote_allowed"])
            with self.assertRaises(CuratorError):
                lib.proposal("archive", evidence_refs=["curator:deprecated"], protection={"pinned": True})


if __name__ == "__main__":
    unittest.main()
