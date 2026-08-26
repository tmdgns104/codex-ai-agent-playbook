import importlib.util
import pathlib
import sys
import unittest

MODULE_PATH = pathlib.Path(__file__).resolve().parents[1] / "conformance.py"
SPEC = importlib.util.spec_from_file_location("transport_conformance", MODULE_PATH)
module = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = module
assert SPEC.loader is not None
SPEC.loader.exec_module(module)


class TransportConformanceTests(unittest.TestCase):
    def test_complete_adapter_is_compatible(self):
        result = module.classify(module.AdapterSpec("ok", True, True, True, True, True, True))
        self.assertEqual(result["classification"], "compatible")
        self.assertEqual(result["missing"], [])

    def test_missing_separate_channel_is_unsupported(self):
        result = module.classify(module.AdapterSpec("legacy", False, True, False, False, False, True))
        self.assertEqual(result["classification"], "unsupported")
        self.assertIn("supports_separate_verified_context", result["missing"])

    def test_incomplete_final_verification_is_partial(self):
        result = module.classify(module.AdapterSpec("partial", True, True, True, False, True, True))
        self.assertEqual(result["classification"], "partial")
        self.assertEqual(
            result["missing"],
            ["verifies_hash_size_permission_before_spawn"],
        )

    def test_current_codex_stays_unsupported(self):
        matrix = module.build_matrix()
        current = next(item for item in matrix["results"] if item["adapter"] == "codex-cli-current")
        self.assertEqual(current["classification"], "unsupported")
        self.assertFalse(matrix["promotion_evidence"]["transport_conformance"])

    def test_simulation_never_claims_real_execution_or_approval(self):
        matrix = module.build_matrix()
        self.assertFalse(matrix["model_used"])
        self.assertFalse(matrix["api_used"])
        self.assertFalse(matrix["network_used"])
        self.assertFalse(matrix["production_integration_used"])
        self.assertFalse(matrix["promotion_evidence"]["production_transport_approved"])


if __name__ == "__main__":
    unittest.main()
