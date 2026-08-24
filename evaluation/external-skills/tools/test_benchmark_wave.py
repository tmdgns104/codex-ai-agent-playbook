#!/usr/bin/env python3
"""Deterministic tests for V8.3 BENCH-004 Stage B controls and Evidence."""

from __future__ import annotations

import copy
import hashlib
import json
import unittest
from pathlib import Path

import run_benchmark as bench


class BenchmarkWaveTests(unittest.TestCase):
    @staticmethod
    def load(path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def hard_check_pass(result: dict, check_name: str) -> bool:
        matches = [item["pass"] for item in result["hard_checks"] if item["check"] == check_name]
        if len(matches) != 1:
            raise AssertionError(f"hard check is not unique: {check_name}")
        return matches[0]

    def test_runtime_approval_matches_policy(self) -> None:
        control = bench.runtime_control()
        self.assertEqual(control["provider"], "Ollama")
        self.assertEqual(control["locality"], "local-only")
        self.assertEqual(control["model_identifier"], "qwen3.5:9b")
        self.assertRegex(control["model_digest"], r"^[0-9a-f]{64}$")
        self.assertFalse(control["model_fallback_allowed"])
        self.assertEqual(control["retry_count"], 0)
        self.assertEqual(control["candidate_order"], bench.CANDIDATE_ORDER)
        self.assertEqual(control["variant_order"], bench.VARIANT_ORDER)

    def test_non_loopback_runtime_is_rejected(self) -> None:
        rejected = [
            "https://127.0.0.1:11434",
            "http://localhost:11434",
            "http://192.168.0.2:11434",
            "http://127.0.0.1:11435",
            "http://user:secret@127.0.0.1:11434",
        ]
        for endpoint in rejected:
            with self.subTest(endpoint=endpoint), self.assertRaises(bench.BenchmarkError):
                bench.validate_loopback_url(endpoint)

    def test_stage_b_matrix_and_static_inputs_are_exact(self) -> None:
        static = bench.validate_static_inputs()
        self.assertTrue(bench.exact_matrix(static["results"]["stage_b"]))
        self.assertEqual(list(static["input_map"]), bench.CANDIDATE_ORDER)
        self.assertEqual(set(static["rubric_map"]), set(bench.CANDIDATE_ORDER))
        self.assertEqual(set(static["adapted_map"]), set(bench.CANDIDATE_ORDER))

    def test_adapted_contexts_are_smaller_than_raw_snapshots(self) -> None:
        static = bench.validate_static_inputs()
        for candidate_id in bench.CANDIDATE_ORDER:
            raw_bytes = static["snapshot_map"][candidate_id]["byte_size"]
            adapted_bytes = len(static["adapted_map"][candidate_id]["context"].encode("utf-8"))
            self.assertGreater(adapted_bytes, 0)
            self.assertLess(adapted_bytes, raw_bytes)

    def test_response_schemas_require_every_declared_field(self) -> None:
        static = bench.validate_static_inputs()
        for candidate_id in bench.CANDIDATE_ORDER:
            schema = bench.response_schema(candidate_id)
            required = set(schema["required"])
            declared = set(static["input_map"][candidate_id]["required_output_fields"])
            self.assertEqual(required, declared)
            self.assertFalse(schema["additionalProperties"])

    @staticmethod
    def good_outputs() -> dict[str, dict]:
        workflow = [
            {"order": 1, "action": "Inspect supplied input", "verification": "Match the frozen summary"},
            {"order": 2, "action": "Apply the planned method", "verification": "Check intermediate values"},
            {"order": 3, "action": "Validate the result", "verification": "Run deterministic checks"},
            {"order": 4, "action": "Report limitations", "verification": "Confirm evidence links"},
        ]
        return {
            "kd-exploratory-data-analysis": {
                "missing_columns": ["age", "annual_income"],
                "outlier_columns": ["annual_income"],
                "distribution_checks": ["histogram", "quantiles", "class balance"],
                "correlation_interpretation": "Association is not causal and cannot establish causation.",
                "workflow_steps": workflow,
                "reproducibility_controls": ["seed", "record scope and provenance"],
                "additional_controls": ["preserve raw data read-only", "training split before preprocessing", "report limitations"],
                "external_actions": [],
            },
            "kd-scikit-learn": {
                "split_strategy": "stratified train/test split",
                "test_fraction": 0.2,
                "preprocessing_location": "inside Pipeline",
                "numeric_preprocessing": ["median imputation", "standard scaling"],
                "categorical_preprocessing": ["most frequent imputation", "one hot encoder"],
                "baseline_model": "logistic regression",
                "evaluation_metrics": ["ROC-AUC", "PR-AUC"],
                "cross_validation_scope": "training data only",
                "test_set_usage": "final evaluation once",
                "random_seed": 42,
                "verification_steps": ["check split", "check leakage"],
                "workflow_steps": workflow,
                "additional_controls": ["class imbalance", "threshold", "calibration", "model comparison"],
                "external_actions": [],
            },
            "kd-sympy": {
                "symbol": "x",
                "domain": "real",
                "method": "exact symbolic solve",
                "factorization": "(x - 2)*(x - 1)*(x + 1)*(x + 2)",
                "exact_roots": ["-2", "-1", "1", "2"],
                "verification_residuals": {"-2": "0", "-1": "0", "1": "0", "2": "0"},
                "workflow_steps": workflow,
                "additional_controls": ["explicit assumptions", "exact arithmetic", "factor before solve", "substitute into original expression"],
                "external_actions": [],
            },
            "kd-citation-management": {
                "normalized_dois": {"C1": "10.1000/safe.001", "C2": "10.1000/safe.001", "C3": None, "C4": "10.1000/evidence.004"},
                "duplicate_groups": [["C1", "C2"]],
                "missing_fields": {"C3": ["doi"], "C4": ["journal", "year"]},
                "deduplication_rule": "normalized DOI as DOI-first key",
                "workflow_steps": workflow,
                "external_lookup_performed": False,
                "additional_controls": ["untrusted metadata", "preserve display metadata", "leave missing; do not fabricate"],
                "external_actions": [],
            },
            "kd-docx": {
                "document_title": "Quarterly Safety Review",
                "page_size": "A4",
                "heading_hierarchy": [
                    {"text": "Quarterly Safety Review", "level": "Title"},
                    {"text": "Executive Summary", "level": "Heading 1"},
                    {"text": "Findings", "level": "Heading 1"},
                    {"text": "Recommendations", "level": "Heading 1"},
                ],
                "table_headers": ["Control", "Owner", "Status"],
                "body_format": {"font": "Aptos", "size_pt": 11, "line_spacing": 1.15},
                "accessibility_checks": ["header row", "table description"],
                "verification_plan": ["validate DOCX package", "render and inspect every page for clipping or overflow"],
                "external_template_required": False,
                "workflow_steps": workflow,
                "additional_controls": ["built-in heading styles", "explicit column widths", "all pages"],
                "external_actions": [],
            },
        }

    def test_known_good_outputs_pass_every_hard_gate(self) -> None:
        for candidate_id, output in self.good_outputs().items():
            with self.subTest(candidate_id=candidate_id):
                result = bench.acceptance(candidate_id, output)
                self.assertTrue(result["acceptance_pass"])
                self.assertEqual(result["hard_checks_passed"], result["hard_checks_total"])

    def test_semantic_equivalent_eda_non_causality_passes(self) -> None:
        output = copy.deepcopy(self.good_outputs()["kd-exploratory-data-analysis"])
        output["correlation_interpretation"] = (
            "This association is exploratory; causal claims are unsupported."
        )
        result = bench.acceptance("kd-exploratory-data-analysis", output)
        self.assertTrue(self.hard_check_pass(result, "non-causal correlation interpretation"))

    def test_semantic_equivalent_final_single_use_passes(self) -> None:
        output = copy.deepcopy(self.good_outputs()["kd-scikit-learn"])
        output["test_set_usage"] = (
            "Single use for final evaluation after model selection and hyperparameter tuning"
        )
        result = bench.acceptance("kd-scikit-learn", output)
        self.assertTrue(self.hard_check_pass(result, "final-once test usage"))

    def test_incorrect_semantic_claims_still_fail(self) -> None:
        eda = copy.deepcopy(self.good_outputs()["kd-exploratory-data-analysis"])
        eda["correlation_interpretation"] = "The correlation proves a causal relationship."
        eda_result = bench.acceptance("kd-exploratory-data-analysis", eda)
        self.assertFalse(
            self.hard_check_pass(eda_result, "non-causal correlation interpretation")
        )

        ml = copy.deepcopy(self.good_outputs()["kd-scikit-learn"])
        ml["test_set_usage"] = (
            "The test set is used repeatedly during model selection and once for final evaluation."
        )
        ml_result = bench.acceptance("kd-scikit-learn", ml)
        self.assertFalse(self.hard_check_pass(ml_result, "final-once test usage"))

    def test_sympy_residual_contract_is_exact(self) -> None:
        static = bench.validate_static_inputs()
        contract = static["input_map"]["kd-sympy"]["output_contract"][
            "verification_residuals"
        ]
        schema = bench.response_schema("kd-sympy")["properties"][
            "verification_residuals"
        ]
        expected_keys = ["-2", "-1", "1", "2"]
        self.assertEqual(contract["required_keys"], expected_keys)
        self.assertFalse(contract["additional_keys_allowed"])
        self.assertEqual(schema["required"], expected_keys)
        self.assertFalse(schema["additionalProperties"])
        self.assertTrue(all(schema["properties"][key]["const"] == "0" for key in expected_keys))

        incomplete = copy.deepcopy(self.good_outputs()["kd-sympy"])
        incomplete["verification_residuals"].pop("-2")
        result = bench.acceptance("kd-sympy", incomplete)
        self.assertFalse(self.hard_check_pass(result, "zero substitution residuals"))

    def test_citation_normalized_doi_contract_requires_complete_map(self) -> None:
        static = bench.validate_static_inputs()
        contract = static["input_map"]["kd-citation-management"]["output_contract"][
            "normalized_dois"
        ]
        schema = bench.response_schema("kd-citation-management")["properties"][
            "normalized_dois"
        ]
        expected_keys = ["C1", "C2", "C3", "C4"]
        self.assertEqual(contract["required_keys"], expected_keys)
        self.assertFalse(contract["additional_keys_allowed"])
        self.assertEqual(schema["required"], expected_keys)
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(schema["properties"]["C3"]["type"], "null")

        incomplete = copy.deepcopy(self.good_outputs()["kd-citation-management"])
        incomplete["normalized_dois"].pop("C3")
        result = bench.acceptance("kd-citation-management", incomplete)
        self.assertFalse(self.hard_check_pass(result, "normalized local DOI values"))

    def test_docx_heading_contract_uses_canonical_levels(self) -> None:
        static = bench.validate_static_inputs()
        contract = static["input_map"]["kd-docx"]["output_contract"][
            "heading_hierarchy"
        ]
        schema = bench.response_schema("kd-docx")["properties"]["heading_hierarchy"]
        self.assertEqual(contract["canonical_level_labels"], ["Title", "Heading 1"])
        self.assertFalse(contract["additional_entries_allowed"])
        self.assertEqual(schema["minItems"], 4)
        self.assertEqual(schema["maxItems"], 4)
        self.assertEqual(schema["items"]["properties"]["level"]["enum"], ["Title", "Heading 1"])

        inconsistent = copy.deepcopy(self.good_outputs()["kd-docx"])
        inconsistent["heading_hierarchy"][2]["level"] = "Heading 2"
        result = bench.acceptance("kd-docx", inconsistent)
        self.assertFalse(self.hard_check_pass(result, "consistent heading hierarchy"))

    def test_rubric_hard_checks_match_validator_exactly(self) -> None:
        static = bench.validate_static_inputs()
        expected_counts = {
            "kd-exploratory-data-analysis": 7,
            "kd-scikit-learn": 11,
            "kd-sympy": 7,
            "kd-citation-management": 7,
            "kd-docx": 9,
        }
        for candidate_id, expected_count in expected_counts.items():
            with self.subTest(candidate_id=candidate_id):
                declared = static["rubric_map"][candidate_id]["hard_checks"]
                implemented = bench.validator_hard_check_names(candidate_id)
                self.assertEqual(declared, implemented)
                self.assertEqual(len(declared), expected_count)

    def test_stored_evidence_hard_checks_match_rubric_without_rescoring(self) -> None:
        static = bench.validate_static_inputs()
        for slot in static["results"]["stage_b"]:
            with self.subTest(candidate=slot["candidate_id"], variant=slot["variant"]):
                evidence = self.load(bench.REPO_ROOT / slot["acceptance_evidence"])
                recorded = [item["check"] for item in evidence["acceptance"]["hard_checks"]]
                declared = static["rubric_map"][slot["candidate_id"]]["hard_checks"]
                self.assertEqual(recorded, declared)

    def test_historical_stage_b_artifact_hashes_are_preserved(self) -> None:
        analysis = self.load(bench.BASE / "reports" / "stage-b-failure-analysis.json")
        expected_results_hash = analysis["source_evidence"][
            "protected_file_sha256_before_analysis"
        ]["evaluation/external-skills/benchmark-results.json"]
        self.assertEqual(
            hashlib.sha256(bench.RESULTS.read_bytes()).hexdigest(),
            expected_results_hash,
        )

        evidence_hash = hashlib.sha256()
        evidence_paths = sorted(bench.EVIDENCE_ROOT.glob("*/*.json"))
        self.assertEqual(len(evidence_paths), analysis["source_evidence"]["slot_evidence_file_count"])
        for path in evidence_paths:
            raw = path.read_bytes()
            evidence_hash.update(path.relative_to(bench.REPO_ROOT).as_posix().encode("utf-8"))
            evidence_hash.update(b"\0")
            evidence_hash.update(hashlib.sha256(raw).hexdigest().encode("ascii"))
            evidence_hash.update(b"\n")
        self.assertEqual(
            evidence_hash.hexdigest(),
            analysis["source_evidence"]["slot_evidence_set_sha256"],
        )

    def test_missing_or_unsafe_output_fails(self) -> None:
        for candidate_id, output in self.good_outputs().items():
            with self.subTest(candidate_id=candidate_id):
                unsafe = copy.deepcopy(output)
                unsafe["external_actions"] = ["call external API"]
                result = bench.acceptance(candidate_id, unsafe)
                self.assertFalse(result["acceptance_pass"])

    def test_results_state_has_no_mixed_or_untracked_slots(self) -> None:
        result = bench.validate_final()
        self.assertEqual(result["status"], "COMPLETE")
        self.assertEqual(result["slot_count"], 20)
        self.assertEqual(result["executed"], 20)
        self.assertEqual(result["executed"] + result["pending"], 20)

    def test_every_slot_has_controlled_runtime_and_evidence(self) -> None:
        control = bench.runtime_control()
        results = self.load(bench.RESULTS)
        for slot in results["stage_b"]:
            with self.subTest(candidate=slot["candidate_id"], variant=slot["variant"]):
                self.assertIn(slot["execution_status"], {"COMPLETED", "FAILED"})
                self.assertIsInstance(slot["acceptance_pass"], bool)
                self.assertEqual(slot["runtime_metadata"]["model_identifier"], control["model_identifier"])
                self.assertEqual(slot["runtime_metadata"]["model_digest"], control["model_digest"])
                self.assertEqual(slot["runtime_metadata"]["generation_parameters"], control["generation_parameters"])
                self.assertEqual(slot["runtime_metadata"]["retry_count"], 0)
                self.assertFalse(slot["runtime_metadata"]["fallback_allowed"])
                self.assertIsInstance(slot["token_count"], int)
                self.assertIsInstance(slot["output_token_count"], int)
                self.assertFalse(slot["external_access_attempted"])
                self.assertFalse(slot["external_scripts_executed"])
                self.assertTrue((bench.REPO_ROOT / slot["acceptance_evidence"]).is_file())

    def test_adoption_decisions_follow_stage_b_gate(self) -> None:
        decisions = self.load(bench.BASE / "adoption-decisions.json")
        allowed = {"ADOPT_CANDIDATE", "ADAPT_CANDIDATE", "REFERENCE_ONLY", "REJECTED"}
        self.assertEqual(decisions["decision_count"], 15)
        self.assertEqual(set(decisions["decision_enums"]), allowed)
        self.assertEqual(sum(decisions["decision_summary"].values()), 15)
        for decision in decisions["decisions"]:
            self.assertIn(decision["decision"], allowed)
            if decision["decision"] in {"ADOPT_CANDIDATE", "ADAPT_CANDIDATE"}:
                self.assertTrue(decision["stage_b_evidence"])
                self.assertTrue(decision["stage_b_evidence_paths"])

    def test_summary_aggregates_match_results(self) -> None:
        results = self.load(bench.RESULTS)
        summary = self.load(bench.BASE / "reports" / "stage-b-execution-summary.json")
        slots = results["stage_b"]
        self.assertEqual(summary["totals"]["slots"], len(slots))
        self.assertEqual(summary["totals"]["acceptance_pass"], sum(item["acceptance_pass"] is True for item in slots))
        self.assertEqual(summary["totals"]["acceptance_fail"], sum(item["acceptance_pass"] is False for item in slots))
        self.assertEqual(summary["totals"]["prompt_tokens"], sum(item["token_count"] for item in slots))
        self.assertEqual(summary["totals"]["output_tokens"], sum(item["output_token_count"] for item in slots))

    def test_protected_baseline_hashes_are_unchanged(self) -> None:
        approval = self.load(bench.APPROVAL)
        for relative_path, expected_hash in approval["baseline"]["protected_sha256"].items():
            raw = (bench.REPO_ROOT / relative_path).read_bytes()
            self.assertEqual(bench.sha256_bytes(raw), expected_hash, relative_path)


if __name__ == "__main__":
    unittest.main()
