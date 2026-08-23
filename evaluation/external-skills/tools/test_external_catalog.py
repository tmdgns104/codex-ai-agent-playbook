#!/usr/bin/env python3
"""Focused tests for V8.3 external expert skill catalog foundation."""

from __future__ import annotations

import copy
import hashlib
import json
import unittest
from pathlib import Path

from external_catalog import (
    ExternalCatalogError,
    PROTECTED_DOMAIN_PACKS,
    REQUIRED_BENCHMARK_VARIANTS,
    build_coverage_report,
    generate_coverage_report,
    load_and_validate_catalog,
    validate_benchmark_schema_document,
    validate_candidates_document,
    validate_domain_packs_document,
    validate_sources_document,
)

ROOT = Path(__file__).resolve().parents[3]
EXTERNAL = ROOT / "evaluation" / "external-skills"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class ExternalCatalogBaselineTests(unittest.TestCase):
    def test_repository_baseline_validates(self) -> None:
        sources, domains, candidates = load_and_validate_catalog(ROOT)
        trusted = [s for s in sources["sources"] if s["tier"] != "discovery"]
        discovery = [s for s in sources["sources"] if s["tier"] == "discovery"]
        self.assertGreaterEqual(len(trusted), 6)
        self.assertGreaterEqual(len(discovery), 1)
        self.assertEqual(25, len(domains))
        self.assertTrue(PROTECTED_DOMAIN_PACKS.issubset(domains))
        self.assertEqual([], candidates)

    def test_source_auto_execution_is_rejected(self) -> None:
        data = load_json(EXTERNAL / "sources.json")
        broken = copy.deepcopy(data)
        broken["sources"][0]["auto_execute_external_scripts"] = True
        with self.assertRaisesRegex(ExternalCatalogError, "auto-execution"):
            validate_sources_document(broken)

    def test_duplicate_domain_is_rejected(self) -> None:
        data = load_json(EXTERNAL / "domain-packs.json")
        broken = copy.deepcopy(data)
        broken["domain_packs"].append(copy.deepcopy(broken["domain_packs"][0]))
        with self.assertRaisesRegex(ExternalCatalogError, "duplicate domain pack"):
            validate_domain_packs_document(broken)

    def test_protected_domain_pack_is_required(self) -> None:
        data = load_json(EXTERNAL / "domain-packs.json")
        broken = copy.deepcopy(data)
        broken["domain_packs"] = [
            item for item in broken["domain_packs"] if item["id"] != "big-data"
        ]
        with self.assertRaises(ExternalCatalogError):
            validate_domain_packs_document(broken)

    def test_candidate_unknown_source_is_rejected(self) -> None:
        sources = validate_sources_document(load_json(EXTERNAL / "sources.json"))
        domains = validate_domain_packs_document(load_json(EXTERNAL / "domain-packs.json"))
        data = {
            "schema_version": 1,
            "candidates": [
                {
                    "candidate_id": "bad-source",
                    "source_id": "not-registered",
                    "upstream_path": "skills/example",
                    "domain_pack": "documentation-guide",
                    "source_revision": None,
                    "license_status": "unknown",
                    "compatibility_status": "unknown",
                    "dependencies": [],
                    "permissions": [],
                    "bundled_scripts": False,
                    "external_scripts_executed": False,
                    "decision": "DISCOVERED"
                }
            ]
        }
        with self.assertRaisesRegex(ExternalCatalogError, "unknown source"):
            validate_candidates_document(data, source_ids=sources, domain_ids=set(domains))

    def test_unknown_license_cannot_advance_candidate(self) -> None:
        sources = validate_sources_document(load_json(EXTERNAL / "sources.json"))
        domains = validate_domain_packs_document(load_json(EXTERNAL / "domain-packs.json"))
        source_id = sorted(sources)[0]
        data = {
            "schema_version": 1,
            "candidates": [
                {
                    "candidate_id": "unknown-license",
                    "source_id": source_id,
                    "upstream_path": "skills/example",
                    "domain_pack": "documentation-guide",
                    "source_revision": "abc123",
                    "license_status": "unknown",
                    "compatibility_status": "compatible",
                    "dependencies": [],
                    "permissions": ["local_read"],
                    "bundled_scripts": False,
                    "external_scripts_executed": False,
                    "decision": "ADOPT_CANDIDATE"
                }
            ]
        }
        with self.assertRaisesRegex(ExternalCatalogError, "unknown license"):
            validate_candidates_document(data, source_ids=sources, domain_ids=set(domains))

    def test_external_script_execution_marker_is_rejected(self) -> None:
        sources = validate_sources_document(load_json(EXTERNAL / "sources.json"))
        domains = validate_domain_packs_document(load_json(EXTERNAL / "domain-packs.json"))
        source_id = sorted(sources)[0]
        data = {
            "schema_version": 1,
            "candidates": [
                {
                    "candidate_id": "script-executed",
                    "source_id": source_id,
                    "upstream_path": "skills/example",
                    "domain_pack": "big-data",
                    "source_revision": "abc123",
                    "license_status": "verified",
                    "compatibility_status": "compatible",
                    "dependencies": [],
                    "permissions": ["local_read"],
                    "bundled_scripts": True,
                    "external_scripts_executed": True,
                    "decision": "INSPECTED"
                }
            ]
        }
        with self.assertRaisesRegex(ExternalCatalogError, "must not execute"):
            validate_candidates_document(data, source_ids=sources, domain_ids=set(domains))

    def test_benchmark_schema_contains_four_required_variants(self) -> None:
        data = load_json(EXTERNAL / "benchmark-schema.json")
        validate_benchmark_schema_document(data)
        self.assertTrue(REQUIRED_BENCHMARK_VARIANTS.issubset(set(data["variants"])))

    def test_coverage_report_is_deterministic_and_read_only(self) -> None:
        registry_path = ROOT / "capability-library" / "registry.json"
        before = hashlib.sha256(registry_path.read_bytes()).hexdigest()
        first = generate_coverage_report(ROOT)
        second = generate_coverage_report(ROOT)
        after = hashlib.sha256(registry_path.read_bytes()).hexdigest()
        self.assertEqual(first, second)
        self.assertEqual(before, after)
        self.assertEqual(25, first["domain_pack_count"])
        self.assertEqual(0, first["candidate_count"])
        self.assertEqual(sorted(PROTECTED_DOMAIN_PACKS), first["protected_domain_packs"])

    def test_build_coverage_counts_candidates_without_loading_skill_body(self) -> None:
        domains = {"big-data": ["pyspark", "cudf"]}
        candidates = [
            {"domain_pack": "big-data", "decision": "DISCOVERED"},
            {"domain_pack": "big-data", "decision": "BENCHMARK_READY"},
        ]
        report = build_coverage_report(
            domain_packs=domains,
            candidates=candidates,
            active_ids={"cudf"},
        )
        domain = report["domains"][0]
        self.assertEqual(2, domain["discovered_candidate_count"])
        self.assertEqual(1, domain["inspected_count"])
        self.assertEqual(1, domain["benchmark_ready_count"])
        self.assertEqual(["cudf"], domain["active_covered_capabilities"])
        self.assertEqual(["pyspark"], domain["uncovered_active_capabilities"])


if __name__ == "__main__":
    unittest.main()
