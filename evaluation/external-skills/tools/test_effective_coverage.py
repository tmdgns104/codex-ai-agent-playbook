#!/usr/bin/env python3
"""Focused tests for V8.3 effective current coverage mapping."""

from __future__ import annotations

import copy
import hashlib
import json
import unittest
from pathlib import Path

from effective_coverage import (
    ExternalCatalogError,
    _active_registry_ids,
    _core_skill_ids,
    generate_effective_coverage,
    validate_current_coverage_map,
)
from external_catalog import load_and_validate_catalog

ROOT = Path(__file__).resolve().parents[3]
EXTERNAL = ROOT / "evaluation" / "external-skills"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class EffectiveCoverageTests(unittest.TestCase):
    def test_repository_mapping_validates(self) -> None:
        _, domains, _ = load_and_validate_catalog(ROOT)
        mapped = validate_current_coverage_map(
            load_json(EXTERNAL / "current-coverage-map.json"),
            domain_packs=domains,
            active_registry_ids=_active_registry_ids(ROOT),
            core_skill_ids=_core_skill_ids(ROOT),
        )
        self.assertEqual(["api-design"], mapped["backend-api"]["api-contract"])
        self.assertEqual(["docker-container"], mapped["devops-container"]["docker"])
        self.assertEqual(["guide-ppt-creator"], mapped["presentation-visual"]["technical-slides"])

    def test_unknown_provider_is_rejected(self) -> None:
        _, domains, _ = load_and_validate_catalog(ROOT)
        data = load_json(EXTERNAL / "current-coverage-map.json")
        broken = copy.deepcopy(data)
        broken["providers"][0]["id"] = "not-installed"
        with self.assertRaisesRegex(ExternalCatalogError, "not in registry"):
            validate_current_coverage_map(
                broken,
                domain_packs=domains,
                active_registry_ids=_active_registry_ids(ROOT),
                core_skill_ids=_core_skill_ids(ROOT),
            )

    def test_undeclared_domain_capability_is_rejected(self) -> None:
        _, domains, _ = load_and_validate_catalog(ROOT)
        data = load_json(EXTERNAL / "current-coverage-map.json")
        broken = copy.deepcopy(data)
        broken["providers"][0]["coverage"]["backend-api"].append("not-a-declared-capability")
        with self.assertRaisesRegex(ExternalCatalogError, "not declared"):
            validate_current_coverage_map(
                broken,
                domain_packs=domains,
                active_registry_ids=_active_registry_ids(ROOT),
                core_skill_ids=_core_skill_ids(ROOT),
            )

    def test_effective_report_is_deterministic_and_read_only(self) -> None:
        registry_path = ROOT / "capability-library" / "registry.json"
        before = hashlib.sha256(registry_path.read_bytes()).hexdigest()
        first = generate_effective_coverage(ROOT)
        second = generate_effective_coverage(ROOT)
        after = hashlib.sha256(registry_path.read_bytes()).hexdigest()
        self.assertEqual(first, second)
        self.assertEqual(before, after)
        self.assertEqual(25, first["domain_pack_count"])
        self.assertEqual(12, first["active_registry_capability_count"])
        self.assertEqual(7, first["core_skill_count"])
        self.assertGreater(first["current_covered_capability_total"], 3)

    def test_known_existing_skills_reduce_false_gaps_but_do_not_hide_real_gaps(self) -> None:
        report = generate_effective_coverage(ROOT)
        domains = {entry["domain_pack"]: entry for entry in report["domains"]}
        self.assertIn("api-contract", domains["backend-api"]["current_covered_capabilities"])
        self.assertIn("docker", domains["devops-container"]["current_covered_capabilities"])
        self.assertIn("profiling", domains["debug-performance"]["current_covered_capabilities"])
        self.assertIn("technical-slides", domains["presentation-visual"]["current_covered_capabilities"])
        self.assertEqual(0, domains["big-data"]["current_coverage_count"])
        self.assertEqual(0, domains["documentation-guide"]["current_coverage_count"])


if __name__ == "__main__":
    unittest.main()
