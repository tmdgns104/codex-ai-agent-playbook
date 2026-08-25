from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path


SELECTOR_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
if str(SELECTOR_ROOT) not in sys.path:
    sys.path.insert(0, str(SELECTOR_ROOT))

from budget_planner import plan_budget  # noqa: E402
from selector import GATE_ORDER, canonical_json_bytes, deterministic_select, repository_shadow_inputs  # noqa: E402
from fixture_factory import (  # noqa: E402
    activation_plan,
    add_approved_composition,
    approved_inputs,
    permission_state,
    refresh_approved_entry,
    router_result,
)


def select(
    task: str,
    *,
    candidate_ids: tuple[str, ...] = ("kd-sympy",),
    catalog=None,
    metadata=None,
    policy=None,
    router=None,
    activation=None,
    permissions=None,
):
    if catalog is None or metadata is None or policy is None:
        catalog, metadata, policy = approved_inputs(candidate_ids)
    router = router or router_result(task)
    activation = activation or activation_plan(task)
    permissions = permissions or permission_state(activation)
    return deterministic_select(
        task_text=task,
        router_result=router,
        activation_plan=activation,
        catalog=catalog,
        candidate_metadata=metadata,
        permission_state=permissions,
        policy=policy,
    )


class SelectorBudgetTests(unittest.TestCase):
    def assert_gate_order(self, result):
        self.assertEqual(list(GATE_ORDER), result["gate_order"])
        for candidate in result["candidate_evidence"]:
            self.assertEqual(list(GATE_ORDER), [gate["gate"] for gate in candidate["gates"]])
            self.assertEqual(list(range(1, 10)), [gate["order"] for gate in candidate["gates"]])

    def test_a_exact_domain_match(self):
        result = select("verify an exact symbolic mathematics derivation")
        self.assertEqual("ADAPTED_SELECTED", result["final_decision"])
        self.assertEqual(["kd-sympy"], [item["candidate_id"] for item in result["selected_adapted_capabilities"]])
        self.assert_gate_order(result)

    def test_b_trigger_match(self):
        result = select("perform exact symbolic equation solving and verify every residual")
        applicability = result["candidate_evidence"][0]["gates"][2]
        self.assertEqual("PASS", applicability["status"])
        self.assertEqual(["symbolic equation solving"], applicability["details"]["matched_triggers"])

    def test_c_exclusion_match(self):
        task = "exact symbolic equation solving where floating point approximation is sufficient"
        result = select(task)
        self.assertIn("EXCLUSION_MATCH", result["excluded_candidates"][0]["reasons"])
        self.assertEqual("NO_ACTION", result["final_decision"])

    def test_d_stale_candidate(self):
        catalog, metadata, policy = approved_inputs()
        metadata["kd-sympy"]["expected_cache_key"] = "0" * 64
        result = select("exact symbolic algebra", catalog=catalog, metadata=metadata, policy=policy)
        self.assertIn("STALE_CANDIDATE", result["excluded_candidates"][0]["reasons"])

    def test_e_unapproved_candidate(self):
        catalog, metadata = repository_shadow_inputs(REPO_ROOT)
        policy = approved_inputs()[2]
        task = "exact symbolic algebra"
        result = select(task, catalog=catalog, metadata=metadata, policy=policy)
        self.assertEqual([], result["selected_adapted_capabilities"])
        self.assertIn("DEFINITION_NOT_APPROVED", result["excluded_candidates"][0]["reasons"])

    def test_f_router_overlap_requires_delta_evidence(self):
        task = "exact symbolic algebra"
        catalog, metadata, policy = approved_inputs()
        metadata["kd-sympy"]["overlap_capability_ids"] = ["symbolic-review"]
        metadata["kd-sympy"]["capability_delta"] = {"status": "UNKNOWN", "evidence_refs": []}
        router = router_result(task, ["symbolic-review"])
        activation = activation_plan(task, ["symbolic-review"], ["local_read"])
        result = select(task, catalog=catalog, metadata=metadata, policy=policy, router=router, activation=activation, permissions=permission_state(activation))
        self.assertEqual("CURRENT_ONLY", result["final_decision"])
        self.assertIn("OVERLAP_UNRESOLVED", result["excluded_candidates"][0]["reasons"])

    def test_g_permission_downgrade_is_human_gated(self):
        task = "exact symbolic algebra"
        activation = activation_plan(task)
        permissions = permission_state(activation)
        permissions["expected_effective_gates"]["kd-sympy"] = "AUTO_ALLOWED"
        result = select(task, activation=activation, permissions=permissions)
        self.assertEqual("HUMAN_GATE_REQUIRED", result["final_decision"])
        self.assertIn("PERMISSION_DOWNGRADE", result["excluded_candidates"][0]["reasons"])

    def test_definition_permission_downgrade_is_human_gated(self):
        catalog, metadata, policy = approved_inputs()
        entry = catalog["candidates"][0]
        entry["definition"]["permissions"]["effective_gate"] = "AUTO_ALLOWED"
        refresh_approved_entry(entry, metadata["kd-sympy"])
        result = select("exact symbolic algebra", catalog=catalog, metadata=metadata, policy=policy)
        self.assertEqual("HUMAN_GATE_REQUIRED", result["final_decision"])
        self.assertIn("PERMISSION_DOWNGRADE", result["excluded_candidates"][0]["reasons"])

    def test_h_required_units_are_always_retained(self):
        result = select("exact symbolic equation solving")
        candidate = result["candidate_evidence"][0]
        required = set(candidate["budget"]["per_capability"][0]["required_unit_ids"])
        selected_ids = set(result["selected_unit_ids"])
        self.assertTrue(required)
        self.assertTrue(required.issubset(selected_ids))
        self.assertEqual(4, len(required))

    def test_i_optional_unit_budget_removal_is_deterministic(self):
        task = "exact symbolic algebra with numerical evaluation"
        catalog, metadata, policy = approved_inputs()
        definition = catalog["candidates"][0]["definition"]
        required_definition = copy.deepcopy(definition)
        required_definition["knowledge_units"] = [unit for unit in definition["knowledge_units"] if unit["required"]]
        required_bytes = plan_budget(task_text=task, definitions=[required_definition], policy=policy)["total_utf8_bytes"]
        policy["budget"]["per_capability_utf8_bytes"] = required_bytes
        policy["budget"]["total_utf8_bytes"] = required_bytes
        result = select(task, catalog=catalog, metadata=metadata, policy=policy)
        self.assertEqual("ADAPTED_SELECTED", result["final_decision"])
        excluded = {item["unit_id"]: item["reason"] for item in result["excluded_units"]}
        optional_id = next(unit["unit_id"] for unit in definition["knowledge_units"] if not unit["required"])
        self.assertIn(excluded[optional_id], {"PER_CAPABILITY_BUDGET_PRUNED", "TOTAL_BUDGET_PRUNED"})

    def test_j_required_only_budget_overflow_blocks(self):
        catalog, metadata, policy = approved_inputs()
        policy["budget"]["per_capability_utf8_bytes"] = 1
        policy["budget"]["total_utf8_bytes"] = 1
        result = select("exact symbolic algebra", catalog=catalog, metadata=metadata, policy=policy)
        self.assertEqual("BUDGET_BLOCKED", result["final_decision"])
        self.assertEqual([], result["selected_unit_ids"])

    def test_k_tie_break_uses_stable_id_after_specificity_cost_and_risk(self):
        task = "exact symbolic algebra"
        catalog, metadata, policy = approved_inputs(("kd-sympy", "kd-citation-management"))
        sympy = next(entry for entry in catalog["candidates"] if entry["candidate_id"] == "kd-sympy")
        citation = next(entry for entry in catalog["candidates"] if entry["candidate_id"] == "kd-citation-management")
        citation_definition = citation["definition"]
        for field in ("applicability", "permissions", "knowledge_units", "budget", "content_sha256"):
            citation_definition[field] = copy.deepcopy(sympy["definition"][field])
        policy["candidate_risk"]["kd-citation-management"] = policy["candidate_risk"]["kd-sympy"]
        refresh_approved_entry(citation, metadata["kd-citation-management"])
        catalog["catalog_revision"] = "tie-break-fixture"
        permissions = permission_state(activation_plan(task))
        permissions["expected_effective_gates"]["kd-citation-management"] = "NETWORK_REVIEW"
        result = select(task, candidate_ids=("kd-sympy", "kd-citation-management"), catalog=catalog, metadata=metadata, policy=policy, permissions=permissions)
        self.assertEqual(["kd-citation-management", "kd-sympy"], result["ranking_order"])
        self.assertEqual("kd-citation-management", result["selected_adapted_capabilities"][0]["candidate_id"])

    def test_l_multi_capability_is_denied_without_composition_evidence(self):
        task = "both symbolic mathematics and citation management with exact symbolic algebra and local citation normalization"
        catalog, metadata, policy = approved_inputs(("kd-sympy", "kd-citation-management"))
        result = select(task, candidate_ids=("kd-sympy", "kd-citation-management"), catalog=catalog, metadata=metadata, policy=policy)
        self.assertEqual("HUMAN_GATE_REQUIRED", result["final_decision"])
        self.assertEqual([], result["selected_adapted_capabilities"])

    def test_m_multi_capability_is_allowed_with_exact_composition_evidence(self):
        task = "both symbolic mathematics and citation management with exact symbolic algebra and local citation normalization"
        catalog, metadata, policy = approved_inputs(("kd-sympy", "kd-citation-management"))
        add_approved_composition(catalog, policy, ["kd-sympy", "kd-citation-management"])
        result = select(task, candidate_ids=("kd-sympy", "kd-citation-management"), catalog=catalog, metadata=metadata, policy=policy)
        self.assertEqual("ADAPTED_SELECTED", result["final_decision"])
        self.assertEqual(2, len(result["selected_adapted_capabilities"]))
        self.assertLessEqual(result["budget_plan"]["total_utf8_bytes"], policy["budget"]["total_utf8_bytes"])

    def test_n_deterministic_rebuild_is_byte_identical(self):
        task = "exact symbolic equation solving"
        catalog, metadata, policy = approved_inputs()
        router = router_result(task)
        activation = activation_plan(task)
        permissions = permission_state(activation)
        kwargs = dict(task_text=task, router_result=router, activation_plan=activation, catalog=catalog, candidate_metadata=metadata, permission_state=permissions, policy=policy)
        first = deterministic_select(**kwargs)
        second = deterministic_select(**copy.deepcopy(kwargs))
        self.assertEqual(canonical_json_bytes(first), canonical_json_bytes(second))
        self.assertEqual(first["output_sha256"], second["output_sha256"])

    def test_o_no_approved_match_keeps_current_path(self):
        task = "review an existing authentication capability"
        router = router_result(task, ["security-review"])
        activation = activation_plan(task, ["security-review"], ["local_read"])
        result = select(task, router=router, activation=activation, permissions=permission_state(activation))
        self.assertEqual("CURRENT_ONLY", result["final_decision"])
        self.assertEqual(["security-review"], result["router_result_reference"]["selected_capability_ids"])

    def test_p_malformed_catalog_or_compiler_output_fails_closed(self):
        catalog, metadata, policy = approved_inputs()
        del catalog["candidates"][0]["definition"]["knowledge_units"][0]["content"]
        result = select("exact symbolic algebra", catalog=catalog, metadata=metadata, policy=policy)
        self.assertEqual("HUMAN_GATE_REQUIRED", result["final_decision"])
        self.assertIn("INVALID_COMPILER_OUTPUT", result["excluded_candidates"][0]["reasons"])

    def test_router_and_activation_inputs_are_not_mutated(self):
        task = "exact symbolic algebra"
        router = router_result(task, ["testing"])
        activation = activation_plan(task, ["testing"], ["local_read"])
        router_before = copy.deepcopy(router)
        activation_before = copy.deepcopy(activation)
        select(task, router=router, activation=activation, permissions=permission_state(activation))
        self.assertEqual(router_before, router)
        self.assertEqual(activation_before, activation)

    def test_unknown_quality_evidence_never_selects(self):
        catalog, metadata, policy = approved_inputs()
        catalog["candidates"][0]["quality_evidence"]["holdout_pass"] = "UNKNOWN"
        result = select("exact symbolic algebra", catalog=catalog, metadata=metadata, policy=policy)
        self.assertEqual([], result["selected_adapted_capabilities"])
        self.assertIn("QUALITY_EVIDENCE_MISSING", result["excluded_candidates"][0]["reasons"])

    def test_missing_permission_evidence_never_selects(self):
        task = "exact symbolic algebra"
        activation = activation_plan(task)
        permissions = permission_state(activation)
        permissions["approved_gates"] = []
        permissions["approval_refs"] = []
        result = select(task, activation=activation, permissions=permissions)
        self.assertEqual("HUMAN_GATE_REQUIRED", result["final_decision"])
        self.assertIn("PERMISSION_APPROVAL_REQUIRED", result["excluded_candidates"][0]["reasons"])

    def test_unauthorized_candidate_never_selects(self):
        catalog, metadata, policy = approved_inputs()
        catalog["candidates"][0]["candidate_id"] = "kd-unauthorized"
        catalog["candidates"][0]["definition"]["candidate_id"] = "kd-unauthorized"
        metadata["kd-unauthorized"] = metadata.pop("kd-sympy")
        result = select("exact symbolic algebra", catalog=catalog, metadata=metadata, policy=policy)
        self.assertEqual([], result["selected_adapted_capabilities"])
        self.assertIn("UNAUTHORIZED_CANDIDATE", result["excluded_candidates"][0]["reasons"])

    def test_missing_required_unit_fails_closed(self):
        catalog, metadata, policy = approved_inputs()
        entry = catalog["candidates"][0]
        missing_id = entry["approval"]["required_unit_ids"][0]
        entry["definition"]["knowledge_units"] = [unit for unit in entry["definition"]["knowledge_units"] if unit["unit_id"] != missing_id]
        refresh_approved_entry(entry, metadata["kd-sympy"])
        entry["approval"]["required_unit_ids"].append(missing_id)
        entry["approval"]["approved_definition_sha256_or_null"] = entry["quality_evidence"]["definition_sha256"]
        result = select("exact symbolic algebra", catalog=catalog, metadata=metadata, policy=policy)
        self.assertEqual([], result["selected_adapted_capabilities"])
        self.assertIn("REQUIRED_UNIT_MISSING", result["excluded_candidates"][0]["reasons"])


if __name__ == "__main__":
    unittest.main()
