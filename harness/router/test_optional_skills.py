#!/usr/bin/env python3
"""Focused tests for V8.1 optional Skill content integrity."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FRONTMATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.S)
NAME = re.compile(r"(?m)^name:\s*([^\n]+)$")
DESCRIPTION = re.compile(r"(?m)^description:\s*([^\n]+)$")


class OptionalSkillContentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = json.loads(
            (ROOT / "capability-library" / "registry.json").read_text(encoding="utf-8")
        )
        cls.skills = {
            item["id"]: item
            for item in cls.registry["capabilities"]
            if item.get("type") == "skill"
        }

    def skill_text(self, capability_id: str) -> str:
        entry = self.skills[capability_id]
        return (ROOT / entry["path"] / "SKILL.md").read_text(encoding="utf-8")

    def test_expected_optional_skills_exist(self) -> None:
        self.assertEqual(
            set(self.skills),
            {"security-review", "testing", "root-cause-debugging", "code-review"},
        )
        for capability_id, entry in self.skills.items():
            self.assertTrue((ROOT / entry["path"] / "SKILL.md").is_file(), capability_id)

    def test_frontmatter_name_and_description_match(self) -> None:
        for capability_id in sorted(self.skills):
            content = self.skill_text(capability_id)
            match = FRONTMATTER.search(content)
            self.assertIsNotNone(match, capability_id)
            frontmatter = match.group(1)
            name = NAME.search(frontmatter)
            description = DESCRIPTION.search(frontmatter)
            self.assertIsNotNone(name, capability_id)
            self.assertIsNotNone(description, capability_id)
            self.assertEqual(name.group(1).strip().strip("'\""), capability_id)

    def test_optional_skills_are_not_always_discovered(self) -> None:
        for capability_id in self.skills:
            self.assertFalse((ROOT / ".agents" / "skills" / capability_id).exists(), capability_id)

    def test_external_provenance_is_recorded(self) -> None:
        sources = json.loads(
            (ROOT / "capability-library" / "sources.json").read_text(encoding="utf-8")
        )
        by_id = {item["id"]: item for item in sources["sources"]}
        ecc = by_id["ecc-rewritten"]
        self.assertEqual(ecc["license"], "MIT")
        self.assertEqual(ecc["adaptation"], "rewritten")
        for capability_id in ("security-review", "testing", "code-review"):
            self.assertEqual(self.skills[capability_id]["source_id"], "ecc-rewritten")
            self.assertEqual(self.skills[capability_id]["license"], "MIT")

    def test_testing_does_not_impose_global_coverage_target(self) -> None:
        content = self.skill_text("testing")
        self.assertIn("임의로 `80%` 같은 전역 숫자를 강제하지 않습니다", content)
        self.assertIn("Repository가 coverage threshold를 정의했다면 그 기준을 따릅니다", content)

    def test_skills_preserve_evidence_and_handoff_rules(self) -> None:
        for capability_id in self.skills:
            content = self.skill_text(capability_id)
            self.assertTrue("Evidence" in content or "근거" in content, capability_id)
        self.assertIn("root-cause-debugging", self.skill_text("testing"))
        self.assertIn("security-review", self.skill_text("root-cause-debugging"))
        self.assertIn("security-review", self.skill_text("code-review"))


if __name__ == "__main__":
    unittest.main()
