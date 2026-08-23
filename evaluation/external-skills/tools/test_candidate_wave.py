#!/usr/bin/env python3
"""Focused tests for V8.3 expert Candidate Wave 1."""

from __future__ import annotations

import hashlib
import unittest
from collections import Counter
from pathlib import Path

from effective_coverage import generate_effective_coverage
from external_catalog import load_and_validate_catalog

ROOT = Path(__file__).resolve().parents[3]


class CandidateWaveTests(unittest.TestCase):
    def test_wave_contains_exactly_100_discovered_candidates(self) -> None:
        _, _, candidates = load_and_validate_catalog(ROOT)
        self.assertEqual(100, len(candidates))
        self.assertTrue(all(item["decision"] == "DISCOVERED" for item in candidates))

    def test_wave_has_five_sources_and_broad_domain_coverage(self) -> None:
        _, _, candidates = load_and_validate_catalog(ROOT)
        self.assertGreaterEqual(len({item["source_id"] for item in candidates}), 5)
        self.assertGreaterEqual(len({item["domain_pack"] for item in candidates}), 18)

    def test_protected_domains_have_multiple_candidates(self) -> None:
        _, _, candidates = load_and_validate_catalog(ROOT)
        counts = Counter(item["domain_pack"] for item in candidates)
        self.assertGreaterEqual(counts["documentation-guide"], 3)
        self.assertGreaterEqual(counts["big-data"], 3)

    def test_discovery_keeps_external_execution_disabled_and_unknown_scripts(self) -> None:
        _, _, candidates = load_and_validate_catalog(ROOT)
        self.assertTrue(all(item["external_scripts_executed"] is False for item in candidates))
        self.assertTrue(all(item["bundled_scripts"] is None for item in candidates))

    def test_candidate_validation_does_not_mutate_active_registry_or_coverage(self) -> None:
        registry = ROOT / "capability-library" / "registry.json"
        before = hashlib.sha256(registry.read_bytes()).hexdigest()
        report = generate_effective_coverage(ROOT)
        after = hashlib.sha256(registry.read_bytes()).hexdigest()
        self.assertEqual(before, after)
        self.assertEqual(100, report["candidate_count"])
        self.assertEqual(172, report["desired_capability_total"])
        self.assertEqual(29, report["current_covered_capability_total"])
        self.assertEqual(143, report["uncovered_capability_total"])


if __name__ == "__main__":
    unittest.main()
