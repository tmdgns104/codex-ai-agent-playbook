#!/usr/bin/env python3
"""Focused deterministic tests for V8.3 candidate inspection artifacts."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from external_catalog import ExternalCatalogError
from inspect_catalog import validate_repository

REPO_ROOT = Path(__file__).resolve().parents[3]
BASE = Path("evaluation") / "external-skills"


class InspectionWaveTests(unittest.TestCase):
    def _temp_repo(self) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        holder: tempfile.TemporaryDirectory[str] = tempfile.TemporaryDirectory()
        root = Path(holder.name)
        shutil.copytree(REPO_ROOT / BASE, root / BASE)
        registry_dst = root / "capability-library"
        registry_dst.mkdir(parents=True)
        shutil.copy2(REPO_ROOT / "capability-library" / "registry.json", registry_dst / "registry.json")
        return holder, root

    @staticmethod
    def _load(root: Path, name: str) -> dict:
        return json.loads((root / BASE / name).read_text(encoding="utf-8"))

    @staticmethod
    def _write(root: Path, name: str, data: dict) -> None:
        (root / BASE / name).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    def test_repository_baseline_validates(self) -> None:
        result = validate_repository(REPO_ROOT)
        self.assertGreaterEqual(result["inspected"], 30)
        self.assertGreaterEqual(result["inspection_domains"], 15)
        self.assertGreaterEqual(result["shortlist"], 15)
        self.assertEqual(result["external_scripts_executed"], 0)
        self.assertEqual(result["active_imports"], 0)

    def test_duplicate_inspection_rejected(self) -> None:
        holder, root = self._temp_repo()
        with holder:
            data = self._load(root, "inspections.json")
            data["inspections"].append(dict(data["inspections"][0]))
            self._write(root, "inspections.json", data)
            with self.assertRaises(ExternalCatalogError):
                validate_repository(root)

    def test_unknown_license_benchmark_ready_rejected(self) -> None:
        holder, root = self._temp_repo()
        with holder:
            data = self._load(root, "inspections.json")
            row = next(item for item in data["inspections"] if item["candidate_id"] == "kd-dask")
            row["license_status"] = "unknown"
            self._write(root, "inspections.json", data)
            with self.assertRaises(ExternalCatalogError):
                validate_repository(root)

    def test_external_script_execution_marker_rejected(self) -> None:
        holder, root = self._temp_repo()
        with holder:
            data = self._load(root, "inspections.json")
            data["inspections"][0]["external_scripts_executed"] = True
            self._write(root, "inspections.json", data)
            with self.assertRaises(ExternalCatalogError):
                validate_repository(root)

    def test_shortlist_non_ready_candidate_rejected(self) -> None:
        holder, root = self._temp_repo()
        with holder:
            data = self._load(root, "benchmark-shortlist.json")
            data["entries"][0]["candidate_id"] = "anth-doc-coauthoring"
            self._write(root, "benchmark-shortlist.json", data)
            with self.assertRaises(ExternalCatalogError):
                validate_repository(root)

    def test_shortlist_requires_reason(self) -> None:
        holder, root = self._temp_repo()
        with holder:
            data = self._load(root, "benchmark-shortlist.json")
            data["entries"][0]["reason"] = ""
            self._write(root, "benchmark-shortlist.json", data)
            with self.assertRaises(ExternalCatalogError):
                validate_repository(root)

    def test_uninspected_cluster_member_rejected(self) -> None:
        holder, root = self._temp_repo()
        with holder:
            data = self._load(root, "duplicate-clusters.json")
            data["clusters"][0]["candidate_ids"].append("anth-claude-api")
            self._write(root, "duplicate-clusters.json", data)
            with self.assertRaises(ExternalCatalogError):
                validate_repository(root)

    def test_industrial_automation_gap_must_remain_explicit(self) -> None:
        holder, root = self._temp_repo()
        with holder:
            data = self._load(root, "discovery-followups.json")
            row = next(item for item in data["followups"] if item["domain_pack"] == "industrial-automation")
            row["status"] = "candidate-invented"
            self._write(root, "discovery-followups.json", data)
            with self.assertRaises(ExternalCatalogError):
                validate_repository(root)


if __name__ == "__main__":
    unittest.main()
