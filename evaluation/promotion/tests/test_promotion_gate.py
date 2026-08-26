import copy
import unittest

from evaluation.promotion.promotion_gate import evaluate


POLICY = {
    "stable_target": "main",
    "performance_policy": {
        "adapted_quality_min_delta_vs_native": 0.0,
        "adapted_latency_max_ratio_vs_native": 1.15,
        "adapted_prompt_token_max_ratio_vs_native": 1.15,
        "adapted_context_bytes_max_ratio_vs_current": 0.75,
        "minimum_holdout_tasks": 12,
        "minimum_task_categories": 4,
        "minimum_repeats_per_variant": 3,
    },
}


def current_rc_evidence():
    return {
        "internal_regression": True,
        "transport_conformance": False,
        "native_vs_playbook_controlled_comparison": False,
        "generalization_holdout": False,
        "candidate_approval": False,
        "stable_runtime_rollback": True,
        "adapted_quality_delta_vs_native": 0.0,
        "adapted_latency_ms": 100.0,
        "native_latency_ms": 100.0,
        "adapted_prompt_tokens": 10000.0,
        "native_prompt_tokens": 10000.0,
        "adapted_context_bytes": 2799.0,
        "current_context_bytes": 54704.0,
        "holdout_task_count": 0,
        "holdout_category_count": 0,
        "repeats_per_variant": 0,
    }


def promotion_ready_evidence():
    evidence = current_rc_evidence()
    evidence.update(
        {
            "transport_conformance": True,
            "native_vs_playbook_controlled_comparison": True,
            "generalization_holdout": True,
            "candidate_approval": True,
            "adapted_quality_delta_vs_native": 0.01,
            "adapted_latency_ms": 105.0,
            "native_latency_ms": 100.0,
            "adapted_prompt_tokens": 10500.0,
            "native_prompt_tokens": 10000.0,
            "holdout_task_count": 24,
            "holdout_category_count": 6,
            "repeats_per_variant": 3,
        }
    )
    return evidence


class PromotionGateTests(unittest.TestCase):
    def test_current_rc_is_not_ready(self):
        result = evaluate(current_rc_evidence(), POLICY)
        self.assertEqual(result["decision"], "NOT_READY")
        self.assertGreaterEqual(result["failure_count"], 3)

    def test_hypothetical_ready_evidence_passes(self):
        result = evaluate(promotion_ready_evidence(), POLICY)
        self.assertEqual(result["decision"], "READY_FOR_PROMOTION")
        self.assertEqual(result["failure_count"], 0)

    def test_missing_gate_fails_closed(self):
        evidence = current_rc_evidence()
        del evidence["transport_conformance"]
        result = evaluate(evidence, POLICY)
        self.assertEqual(result["decision"], "NOT_READY")
        self.assertEqual(result["failure_code"], "EVIDENCE_MISSING")

    def test_bad_latency_blocks(self):
        evidence = promotion_ready_evidence()
        evidence["adapted_latency_ms"] = 120.0
        result = evaluate(evidence, POLICY)
        self.assertEqual(result["decision"], "NOT_READY")
        self.assertIn("performance_latency", {item["gate"] for item in result["failed_checks"]})

    def test_context_reduction_requirement_is_enforced(self):
        evidence = promotion_ready_evidence()
        evidence["adapted_context_bytes"] = 50000.0
        result = evaluate(evidence, POLICY)
        self.assertEqual(result["decision"], "NOT_READY")
        self.assertIn("performance_context", {item["gate"] for item in result["failed_checks"]})


if __name__ == "__main__":
    unittest.main()
