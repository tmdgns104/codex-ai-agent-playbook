#!/usr/bin/env python3
"""Deterministic integrity tests for the isolated V8.3-2 benchmark wave."""

from __future__ import annotations

import unittest

import run_benchmark as bench
import run_benchmark_wave2 as wave2


class BenchmarkWave2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.control = bench.runtime_control()
        cls.records = wave2.load_wave2_evidence(cls.control)
        cls.summary = bench.load_json(wave2.SUMMARY)
        cls.comparison = bench.load_json(wave2.COMPARISON)

    def test_preflight_freezes_approved_runtime_and_isolated_paths(self) -> None:
        preflight = bench.load_json(wave2.PREFLIGHT)
        self.assertEqual(preflight["status"], "READY")
        self.assertFalse(preflight["generation_started"])
        self.assertEqual(preflight["runtime_control"], self.control)
        self.assertEqual(
            preflight["installed_model"]["digest"],
            wave2.APPROVED_RUNTIME["model_digest"],
        )
        self.assertTrue(preflight["path_isolation"]["separated"])
        self.assertNotEqual(
            preflight["path_isolation"]["wave1_evidence_root"],
            preflight["path_isolation"]["wave2_evidence_root"],
        )

    def test_exact_ordered_matrix_has_one_terminal_evidence_per_slot(self) -> None:
        expected = [
            (candidate_id, variant)
            for candidate_id in bench.CANDIDATE_ORDER
            for variant in bench.VARIANT_ORDER
        ]
        actual = [(item["candidate_id"], item["variant"]) for item in self.records]
        self.assertEqual(actual, expected)
        self.assertEqual(len(self.records), 20)
        self.assertTrue(
            all(item["execution_status"] == "COMPLETED" for item in self.records)
        )
        self.assertTrue(all(item["generation_attempt"] == 1 for item in self.records))

    def test_every_slot_preserves_runtime_and_safety_controls(self) -> None:
        for item in self.records:
            with self.subTest(
                candidate=item["candidate_id"], variant=item["variant"]
            ):
                metadata = item["runtime_metadata"]
                self.assertEqual(metadata["provider"], "Ollama")
                self.assertEqual(metadata["locality"], "local-only")
                self.assertEqual(metadata["model_identifier"], "qwen3.5:9b")
                self.assertEqual(
                    metadata["model_digest"], wave2.APPROVED_RUNTIME["model_digest"]
                )
                self.assertEqual(
                    metadata["generation_parameters"],
                    wave2.APPROVED_GENERATION_PARAMETERS,
                )
                self.assertEqual(metadata["runtime_context_limit_tokens"], 16384)
                self.assertEqual(metadata["output_limit_tokens"], 1024)
                self.assertEqual(metadata["timeout_seconds"], 180)
                self.assertEqual(metadata["retry_count"], 0)
                self.assertFalse(metadata["fallback_allowed"])
                for key in (
                    "external_access_attempted",
                    "external_scripts_executed",
                    "credentials_used",
                    "hardware_or_cloud_write",
                    "destructive_action",
                ):
                    self.assertFalse(item[key])

    def test_slot_token_timing_and_acceptance_evidence_are_complete(self) -> None:
        for item in self.records:
            with self.subTest(
                candidate=item["candidate_id"], variant=item["variant"]
            ):
                tokens = item["token_measurement"]
                metadata = item["runtime_metadata"]
                self.assertTrue(tokens["prompt_token_count_available"])
                self.assertTrue(tokens["output_token_count_available"])
                self.assertGreater(tokens["prompt_token_count"], 0)
                self.assertGreater(tokens["output_token_count"], 0)
                self.assertLessEqual(tokens["output_token_count"], 1024)
                self.assertLess(
                    tokens["prompt_token_count"], metadata["runtime_context_limit_tokens"]
                )
                self.assertLess(metadata["execution_start_utc"], metadata["execution_end_utc"])
                self.assertGreater(metadata["wall_time_ms"], 0)
                acceptance = item["acceptance"]
                self.assertEqual(
                    acceptance["hard_checks_total"], len(acceptance["hard_checks"])
                )
                self.assertEqual(
                    acceptance["hard_checks_passed"],
                    sum(check["pass"] for check in acceptance["hard_checks"]),
                )

    def test_summary_is_an_exact_recalculation_of_slot_evidence(self) -> None:
        calculated = wave2.evidence_metrics(self.records)
        self.assertEqual(self.summary["totals"], calculated)
        self.assertEqual(calculated["slots"], 20)
        self.assertEqual(calculated["generation_completed"], 20)
        self.assertEqual(calculated["generation_failed"], 0)
        self.assertEqual(calculated["acceptance_pass"], 8)
        self.assertEqual(calculated["acceptance_fail"], 12)
        self.assertEqual(calculated["failed_hard_checks"], 25)

    def test_comparison_totals_and_deltas_are_exact(self) -> None:
        before = wave2.comparison_metrics(wave2.wave1_records())
        after = wave2.comparison_metrics(
            wave2.wave2_comparison_records(self.records)
        )
        self.assertEqual(self.comparison["wave1"]["acceptance_pass"], 2)
        self.assertEqual(self.comparison["wave1"]["acceptance_fail"], 18)
        self.assertEqual(self.comparison["wave2"]["acceptance_pass"], 8)
        self.assertEqual(self.comparison["wave2"]["acceptance_fail"], 12)
        self.assertEqual(self.comparison["delta"], wave2.numeric_delta(before, after))
        self.assertEqual(self.comparison["delta"]["failed_hard_checks"], -12)

    def test_semantic_and_output_contract_effects_are_separated(self) -> None:
        semantic = self.comparison["semantic_false_negative_effect"]
        resolved = {
            (row["candidate_id"], row["variant"])
            for row in semantic["rows"]
            if row["validator_only_false_negative_resolved"]
        }
        self.assertEqual(semantic["validator_only_false_negative_resolved_count"], 4)
        self.assertEqual(
            resolved,
            {
                ("kd-exploratory-data-analysis", "external-expert"),
                ("kd-scikit-learn", "baseline-no-optional"),
                ("kd-scikit-learn", "current-playbook"),
                ("kd-scikit-learn", "adapted-playbook"),
            },
        )
        contract_transitions = self.comparison["output_contract_effect"]
        self.assertEqual(len(contract_transitions), 12)
        self.assertEqual(
            sum(row["transition"] == "FAIL->PASS" for row in contract_transitions),
            10,
        )

    def test_wave1_and_postfix_inputs_remain_hash_identical(self) -> None:
        protection = wave2.verify_wave1_protection()
        postfix = wave2.verify_postfix_inputs()
        self.assertEqual(
            protection["protected_sha256"], wave2.WAVE1_PROTECTED_SHA256
        )
        self.assertEqual(
            protection["evidence_set_sha256"], wave2.WAVE1_EVIDENCE_SET_SHA256
        )
        self.assertEqual(postfix["file_sha256"], wave2.POSTFIX_INPUT_SHA256)
        self.assertEqual(
            postfix["snapshot_skill_set_sha256"],
            wave2.SNAPSHOT_SKILL_SET_SHA256,
        )
        self.assertFalse(self.summary["adoption_decisions_updated"])
        self.assertFalse(self.comparison["adoption_decisions_updated"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
