#!/usr/bin/env python3
"""V8.3 Batch 2A candidate-stage validation without ACTIVE registry mutation."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROUTER_DIR = ROOT / "harness" / "router"
QUALITY_DIR = ROOT / "harness" / "quality"
SKILLS_DIR = ROOT / "harness" / "skills"
for import_dir in (ROUTER_DIR, QUALITY_DIR, SKILLS_DIR):
    if str(import_dir) not in sys.path:
        sys.path.insert(0, str(import_dir))

from capability_router import route_capabilities  # noqa: E402
from registry import load_json, validate_registry, validate_sources  # noqa: E402
from skill_audit import audit_candidate, exact_trigger_overlaps  # noqa: E402

REGISTRY_FIELDS = (
    "id",
    "type",
    "summary",
    "domains",
    "triggers",
    "activation",
    "risk",
    "recommended_profile",
    "permissions",
    "context_cost",
    "dependencies",
    "source_id",
    "license",
    "path",
)


class Batch2ACandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        manifest = load_json(ROOT / "evaluation" / "v8_3" / "batch2a-candidates.json")
        cls.candidates_raw = manifest["candidates"]
        cls.candidates = [{key: item[key] for key in REGISTRY_FIELDS} for item in cls.candidates_raw]
        cls.active_registry = load_json(ROOT / "capability-library" / "registry.json")
        cls.active = cls.active_registry["capabilities"]
        cls.sources = load_json(ROOT / "capability-library" / "sources.json")
        cls.source_ids = validate_sources(cls.sources)
        cls.merged = cls.active + cls.candidates

    def test_exactly_eight_candidates_and_active_registry_unchanged(self) -> None:
        candidate_ids = {item["id"] for item in self.candidates}
        active_ids = {item["id"] for item in self.active}
        self.assertEqual(len(candidate_ids), 8)
        self.assertTrue(candidate_ids.isdisjoint(active_ids))

    def test_candidate_metadata_validates_as_future_registry_entries(self) -> None:
        validated = validate_registry(
            {"schema_version": 1, "capabilities": self.merged},
            self.source_ids,
        )
        self.assertEqual(len(validated), len(self.merged))

    def test_candidate_paths_frontmatter_and_routing_fixtures_exist(self) -> None:
        for item in self.candidates_raw:
            with self.subTest(skill=item["id"]):
                skill_dir = ROOT / item["path"]
                skill_file = skill_dir / "SKILL.md"
                routing_file = ROOT / item["routing_path"]
                self.assertTrue(skill_file.is_file())
                self.assertTrue(routing_file.is_file())
                text = skill_file.read_text(encoding="utf-8")
                self.assertIn(f"name: {item['id']}", text)
                self.assertIn("## Evidence", text)
                self.assertIn("## Stop / Handoff", text)
                self.assertIn("## Source / Provenance", text)
                routing = json.loads(routing_file.read_text(encoding="utf-8"))
                self.assertEqual(routing["skill_id"], item["id"])
                self.assertGreaterEqual(len(routing["positive"]), 2)
                self.assertGreaterEqual(len(routing["negative"]), 1)

    def test_v82_candidate_audit_contract_passes_for_all_eight(self) -> None:
        for item in self.candidates_raw:
            with self.subTest(skill=item["id"]), tempfile.TemporaryDirectory() as tmp:
                candidate_dir = Path(tmp) / item["proposal_id"]
                candidate_dir.mkdir()
                shutil.copyfile(ROOT / item["path"] / "SKILL.md", candidate_dir / "SKILL.md")
                routing = load_json(ROOT / item["routing_path"])
                (candidate_dir / "routing.json").write_text(
                    json.dumps(routing, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
                proposal = {
                    "proposal_id": item["proposal_id"],
                    "change_type": "create",
                    "skill_id": item["id"],
                    "base_version": 0,
                    "base_hash": "",
                    "proposed_version": 1,
                    "reason": "V8.3 Batch 2A reviewed candidate",
                    "evidence_refs": ["V8.3-SKILL-001", "V8.3-SKILL-002"],
                    "trigger_delta": {"add": item["triggers"], "remove": []},
                    "permission_delta": {"add": item["permissions"], "remove": []},
                    "requires_human_gate": item["requires_human_gate"],
                    "status": "candidate",
                    "source_id": item["source_id"],
                    "license": item["license"],
                    "provenance": item["provenance"],
                }
                (candidate_dir / "proposal.json").write_text(
                    json.dumps(proposal, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
                report = audit_candidate(candidate_dir, root=ROOT)
                self.assertEqual(report.result, "PASS", report.as_dict())

    def test_new_candidates_add_no_exact_trigger_overlap(self) -> None:
        candidate_ids = {item["id"] for item in self.candidates}
        overlaps = exact_trigger_overlaps(self.merged)
        new_overlaps = {
            trigger: ids
            for trigger, ids in overlaps.items()
            if candidate_ids.intersection(ids)
        }
        self.assertEqual(new_overlaps, {})

    def test_each_candidate_positive_and_negative_routing(self) -> None:
        for item in self.candidates_raw:
            routing = load_json(ROOT / item["routing_path"])
            for task in routing["positive"]:
                with self.subTest(skill=item["id"], kind="positive", task=task):
                    result = route_capabilities(task, self.merged)
                    ids = [selected["id"] for selected in result["selected"]]
                    self.assertIn(item["id"], ids, result)
                    self.assertLessEqual(result["count"], 3)
            for task in routing["negative"]:
                with self.subTest(skill=item["id"], kind="negative", task=task):
                    result = route_capabilities(task, self.merged)
                    ids = [selected["id"] for selected in result["selected"]]
                    self.assertNotIn(item["id"], ids, result)

    def test_protected_existing_routing_is_not_stolen(self) -> None:
        typo = route_capabilities("README의 오타 한 글자 수정", self.merged)
        self.assertEqual(typo["count"], 0)

        jwt = route_capabilities("JWT 인증 오류를 수정하고 regression test를 실행", self.merged)
        jwt_ids = {item["id"] for item in jwt["selected"]}
        self.assertEqual(jwt["count"], 3)
        self.assertEqual(jwt["profile"], "strict")
        self.assertEqual(jwt_ids, {"security-review", "testing", "root-cause-debugging"})

        github = route_capabilities("git 브랜치에서 commit push 하고 PR 생성", self.merged)
        github_item = next(item for item in github["selected"] if item["id"] == "github-ops")
        self.assertEqual(github_item["approval"], "required")

    def test_create_candidates_keep_human_gate_required(self) -> None:
        for item in self.candidates_raw:
            with self.subTest(skill=item["id"]):
                self.assertTrue(item["requires_human_gate"])
                self.assertTrue(item["triggers"] or item["permissions"])


if __name__ == "__main__":
    unittest.main()
