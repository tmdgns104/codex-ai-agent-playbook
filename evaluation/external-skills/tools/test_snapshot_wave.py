#!/usr/bin/env python3
"""Focused deterministic tests for V8.3 pinned expert Skill snapshots."""

from __future__ import annotations

import hashlib
import json
import re
import unittest
from pathlib import Path

from fetch_snapshots import ALLOWED, build_url

REPO_ROOT = Path(__file__).resolve().parents[3]
BASE = Path("evaluation") / "external-skills"
SNAPSHOT_ROOT = REPO_ROOT / BASE / "snapshots"


class SnapshotWaveTests(unittest.TestCase):
    @staticmethod
    def _load(name: str) -> dict:
        return json.loads((REPO_ROOT / BASE / name).read_text(encoding="utf-8"))

    def _manifest(self) -> dict:
        return json.loads((SNAPSHOT_ROOT / "manifest.json").read_text(encoding="utf-8"))

    def test_manifest_matches_shortlist_and_provenance(self) -> None:
        manifest = self._manifest()
        shortlist = self._load("benchmark-shortlist.json")
        inspections = self._load("inspections.json")
        sources = self._load("sources.json")

        expected = [item["candidate_id"] for item in shortlist["entries"]]
        records = manifest["records"]
        inspection_map = {item["candidate_id"]: item for item in inspections["inspections"]}
        source_map = {item["id"]: item for item in sources["sources"]}

        self.assertEqual(manifest["schema_version"], 1)
        self.assertEqual(manifest["task_id"], "V8_3-SKILL-BENCH-003B")
        self.assertEqual(manifest["snapshot_count"], 15)
        self.assertEqual([item["candidate_id"] for item in records], expected)
        self.assertEqual(len({item["candidate_id"] for item in records}), 15)

        for record in records:
            inspection = inspection_map[record["candidate_id"]]
            source = source_map[record["source_id"]]
            self.assertEqual(record["source_id"], inspection["source_id"])
            self.assertEqual(record["repository"], source["repository"])
            self.assertEqual(record["source_revision"], inspection["source_revision"])
            self.assertEqual(record["upstream_path"], inspection["upstream_path"])
            self.assertEqual(record["license_status"], inspection["license_status"])

    def test_all_snapshot_hashes_and_bytes_match(self) -> None:
        records = self._manifest()["records"]
        self.assertEqual(len(records), 15)

        for record in records:
            path = REPO_ROOT / record["snapshot_path"]
            self.assertTrue(path.is_file(), record["candidate_id"])
            raw = path.read_bytes()
            self.assertGreater(len(raw), 0)
            self.assertEqual(len(raw), record["byte_size"])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), record["sha256"])
            self.assertRegex(record["sha256"], r"[0-9a-f]{64}$")
            self.assertEqual(record["fetch_status"], "FETCHED")

    def test_pinned_source_groups_are_exact(self) -> None:
        records = self._manifest()["records"]
        kd = [r for r in records if r["source_id"] == "k-dense-scientific"]
        nv = [r for r in records if r["source_id"] == "nvidia-verified-skills"]

        self.assertEqual(len(kd), 11)
        self.assertEqual(len(nv), 4)
        self.assertTrue(all(r["repository"] == "K-Dense-AI/scientific-agent-skills" for r in kd))
        self.assertTrue(all(r["source_revision"] == "390f5146bf3c1877cf15636a3dd7b775e4f0f185" for r in kd))
        self.assertTrue(all(r["repository"] == "NVIDIA/skills" for r in nv))
        self.assertTrue(all(r["source_revision"] == "7149a886d50da8db72cdc1f20ff01cefeadfe6a9" for r in nv))

    def test_snapshot_paths_stay_in_evaluation_area(self) -> None:
        root = SNAPSHOT_ROOT.resolve()
        for record in self._manifest()["records"]:
            path = (REPO_ROOT / record["snapshot_path"]).resolve()
            self.assertTrue(path.is_relative_to(root), record["candidate_id"])
            self.assertEqual(path.name, "SKILL.md")

    def test_safety_markers_remain_zero(self) -> None:
        manifest = self._manifest()
        self.assertFalse(manifest["external_scripts_executed"])
        for record in manifest["records"]:
            self.assertFalse(record["external_scripts_executed"])
            self.assertEqual(record["network_scope"], "PINNED_GITHUB_READ_ONLY")

    def test_exact_pinned_raw_urls(self) -> None:
        for record in self._manifest()["records"]:
            url = build_url(record)
            self.assertTrue(url.startswith("https://raw.githubusercontent.com/"))
            self.assertIn("/" + record["source_revision"] + "/", url)
            self.assertTrue(url.endswith("/" + record["upstream_path"] + "/SKILL.md"))
            self.assertNotIn("/main/", url)
            self.assertNotIn("/master/", url)

    def test_unapproved_revision_is_rejected(self) -> None:
        record = dict(self._manifest()["records"][0])
        record["source_revision"] = "main"
        with self.assertRaises(ValueError):
            build_url(record)

    def test_path_traversal_is_rejected(self) -> None:
        record = dict(self._manifest()["records"][0])
        record["upstream_path"] = "skills/../unsafe"
        with self.assertRaises(ValueError):
            build_url(record)

    def test_allowed_repository_revision_pairs_are_fixed(self) -> None:
        self.assertEqual(
            ALLOWED,
            {
                ("K-Dense-AI/scientific-agent-skills", "390f5146bf3c1877cf15636a3dd7b775e4f0f185"),
                ("NVIDIA/skills", "7149a886d50da8db72cdc1f20ff01cefeadfe6a9"),
            },
        )


if __name__ == "__main__":
    unittest.main()
