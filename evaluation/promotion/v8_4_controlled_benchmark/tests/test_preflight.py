import importlib.util
import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("benchmark_preflight", ROOT / "preflight.py")
module = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = module
assert SPEC.loader is not None
SPEC.loader.exec_module(module)

POLICY = json.loads((ROOT / "policy.json").read_text(encoding="utf-8"))
HOLDOUT = json.loads((ROOT / "holdout.json").read_text(encoding="utf-8"))


class BenchmarkPreflightTests(unittest.TestCase):
    def test_frozen_holdout_meets_promotion_shape(self):
        result = module.validate(POLICY, HOLDOUT)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["fixture_count"], 12)
        self.assertEqual(result["category_count"], 4)
        self.assertEqual(result["repeats_per_variant"], 3)

    def test_execution_stays_blocked_without_transport(self):
        result = module.validate(POLICY, HOLDOUT)
        self.assertEqual(result["execution_state"], "EXECUTION_BLOCKED_BY_TRANSPORT")
        self.assertFalse(result["generalization_holdout"])
        self.assertFalse(result["native_vs_playbook_controlled_comparison"])

    def test_task_tamper_is_detected(self):
        holdout = json.loads(json.dumps(HOLDOUT))
        holdout["fixtures"][0]["task"] += " tampered"
        result = module.validate(POLICY, holdout)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertTrue(any(item.startswith("task_hash_mismatch:") for item in result["failures"]))

    def test_unapproved_candidate_is_rejected(self):
        holdout = json.loads(json.dumps(HOLDOUT))
        holdout["fixtures"][0]["candidate_id"] = "kd-docx"
        result = module.validate(POLICY, holdout)
        self.assertIn("unapproved_candidate_in_holdout", result["failures"])

    def test_development_fixture_overlap_is_rejected(self):
        holdout = json.loads(json.dumps(HOLDOUT))
        holdout["fixtures"][0]["fixture_id"] = "bench004-06"
        result = module.validate(POLICY, holdout)
        self.assertIn("development_holdout_id_overlap", result["failures"])


if __name__ == "__main__":
    unittest.main()
