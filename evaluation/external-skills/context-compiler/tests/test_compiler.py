from __future__ import annotations

import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path


COMPILER_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
if str(COMPILER_ROOT) not in sys.path:
    sys.path.insert(0, str(COMPILER_ROOT))

import compiler  # noqa: E402


class OfflineCompilerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest, cls.policy, cls.rules = compiler.repository_documents(REPO_ROOT)

    def compile(self, candidate_id: str = "kd-sympy", *, policy=None, rules=None, manifest=None, repo_root=None):
        selected_policy = copy.deepcopy(policy or self.policy)
        selected_rules = copy.deepcopy(rules or self.rules)
        selected_manifest = copy.deepcopy(manifest or self.manifest)
        compiler_input = compiler.input_from_manifest(selected_manifest, selected_policy, candidate_id)
        return compiler.compile_candidate(
            repo_root=repo_root or REPO_ROOT,
            compiler_input=compiler_input,
            manifest=selected_manifest,
            policy=selected_policy,
            rules=selected_rules,
        )

    def source_and_input(self, candidate_id: str):
        compiler_input = compiler.input_from_manifest(self.manifest, self.policy, candidate_id)
        source_path = REPO_ROOT.joinpath(*Path(compiler_input.snapshot_path).parts)
        source, issues = compiler._parse_source(source_path.read_bytes())
        self.assertEqual([], issues)
        self.assertIsNotNone(source)
        return compiler_input, source

    def verify_mutation(self, report, candidate_id: str, definition, provenance):
        compiler_input, source = self.source_and_input(candidate_id)
        issues, checks = compiler.verify_compiled_artifacts(
            compiler_input=compiler_input,
            source=source,
            definition=definition,
            provenance=provenance,
            policy=self.policy,
            candidate_rules=self.rules["candidates"][candidate_id],
        )
        return issues, checks

    @staticmethod
    def codes(report_or_issues):
        issues = report_or_issues.issues if isinstance(report_or_issues, compiler.CompileReport) else report_or_issues
        return {issue.code for issue in issues}

    def test_a_normal_pinned_snapshots_compile_as_draft(self):
        for candidate_id in ("kd-sympy", "kd-citation-management"):
            with self.subTest(candidate_id=candidate_id):
                report = self.compile(candidate_id)
                self.assertTrue(report.passed, report.as_dict())
                self.assertEqual("DRAFT", report.definition["status"])
                self.assertEqual("APPROVAL_PENDING", report.provenance["approval"]["state"])
                self.assertFalse(report.provenance["approval"]["automatic_approval"])
                self.assertEqual(5, len(report.definition["knowledge_units"]))
                self.assertTrue(all(value == "PASS" for value in report.evidence["checks"].values()))

    def test_b_source_hash_mismatch_fails_closed(self):
        compiler_input = compiler.input_from_manifest(self.manifest, self.policy, "kd-sympy")
        bad_input = compiler.CompilerInput(**{**compiler_input.as_dict(), "snapshot_sha256": "0" * 64})
        report = compiler.compile_candidate(
            repo_root=REPO_ROOT,
            compiler_input=bad_input,
            manifest=self.manifest,
            policy=self.policy,
            rules=self.rules,
        )
        self.assertFalse(report.passed)
        self.assertIn("SOURCE_HASH_MISMATCH", self.codes(report))

    def test_c_duplicate_or_unstable_unit_order_is_rejected(self):
        rules = copy.deepcopy(self.rules)
        units = rules["candidates"]["kd-sympy"]["units"]
        units[1]["priority"] = units[0]["priority"]
        report = self.compile(rules=rules)
        self.assertIn("RULE_ORDER_UNSTABLE", self.codes(report))

    def test_d_missing_source_locator_fails_provenance(self):
        report = self.compile()
        definition = copy.deepcopy(report.definition)
        provenance = copy.deepcopy(report.provenance)
        definition["knowledge_units"][0]["source_locator"] = ""
        issues, checks = self.verify_mutation(report, "kd-sympy", definition, provenance)
        self.assertIn("PROVENANCE_INCOMPLETE", self.codes(issues))
        self.assertEqual("FAIL", checks["provenance_completeness"])

    def test_e_missing_safety_constraint_fails_closed(self):
        rules = copy.deepcopy(self.rules)
        rules["candidates"]["kd-sympy"]["units"][0]["safety_constraints"] = []
        report = self.compile(rules=rules)
        self.assertIn("REQUIRED_SAFETY_MISSING", self.codes(report))

    def test_f_forbidden_network_or_credential_instruction_is_excluded(self):
        rules = copy.deepcopy(self.rules)
        rules["candidates"]["kd-sympy"]["units"][0]["content"] = "Use curl with an API key to fetch the answer."
        report = self.compile(rules=rules)
        self.assertIn("FORBIDDEN_ADAPTED_INSTRUCTION", self.codes(report))

    def test_g_destructive_or_script_instruction_is_excluded(self):
        rules = copy.deepcopy(self.rules)
        rules["candidates"]["kd-sympy"]["units"][0]["content"] = "Run rm -rf /tmp/result before checking the expression."
        report = self.compile(rules=rules)
        self.assertIn("FORBIDDEN_ADAPTED_INSTRUCTION", self.codes(report))

    def test_h_permission_downgrade_fails_closed(self):
        report = self.compile()
        definition = copy.deepcopy(report.definition)
        provenance = copy.deepcopy(report.provenance)
        definition["permissions"]["effective_gate"] = "none"
        definition["budget"]["utf8_bytes"] = compiler.definition_content_bytes(definition)
        definition["content_sha256"] = compiler.definition_content_sha256(definition)
        definition["cache_key"] = compiler.compute_cache_key(definition)
        issues, checks = self.verify_mutation(report, "kd-sympy", definition, provenance)
        self.assertIn("PERMISSION_INCONSISTENCY", self.codes(issues))
        self.assertEqual("FAIL", checks["permission_consistency"])

    def test_i_required_knowledge_omission_fails_closed(self):
        report = self.compile()
        definition = copy.deepcopy(report.definition)
        provenance = copy.deepcopy(report.provenance)
        removed = definition["knowledge_units"].pop(0)
        provenance["unit_provenance"] = [record for record in provenance["unit_provenance"] if record["unit_id"] != removed["unit_id"]]
        definition["budget"]["utf8_bytes"] = compiler.definition_content_bytes(definition)
        definition["content_sha256"] = compiler.definition_content_sha256(definition)
        definition["cache_key"] = compiler.compute_cache_key(definition)
        provenance["provenance_sha256"] = compiler.hash_without_field(provenance, "provenance_sha256")
        issues, checks = self.verify_mutation(report, "kd-sympy", definition, provenance)
        self.assertIn("REQUIRED_KNOWLEDGE_MISSING", self.codes(issues))
        self.assertEqual("FAIL", checks["required_knowledge_preservation"])

    def test_j_deterministic_rebuild_has_identical_bytes_ids_hashes_and_cache_key(self):
        first = self.compile()
        second = self.compile()
        self.assertTrue(first.passed and second.passed)
        self.assertEqual(compiler.canonical_json_bytes(first.definition), compiler.canonical_json_bytes(second.definition))
        self.assertEqual(compiler.canonical_json_bytes(first.provenance), compiler.canonical_json_bytes(second.provenance))
        self.assertEqual(
            [unit["unit_id"] for unit in first.definition["knowledge_units"]],
            [unit["unit_id"] for unit in second.definition["knowledge_units"]],
        )
        self.assertEqual(first.definition["cache_key"], second.definition["cache_key"])
        self.assertEqual("PASS", first.evidence["deterministic_rebuild"])

    def test_k_stale_cache_is_invalidated(self):
        report = self.compile()
        definition = copy.deepcopy(report.definition)
        definition["cache_key"] = "0" * 64
        issues, checks = self.verify_mutation(report, "kd-sympy", definition, report.provenance)
        self.assertEqual({"STALE_CACHE"}, self.codes(issues))
        self.assertEqual("INVALIDATED", compiler.verification_terminal_status(issues))
        self.assertEqual("FAIL", checks["cache_freshness"])

    def test_k_policy_version_changes_cache_key(self):
        report = self.compile()
        definition = copy.deepcopy(report.definition)
        definition["transformation"]["policy_version"] = "offline-adaptation-policy-v1-next"
        definition["budget"]["utf8_bytes"] = compiler.definition_content_bytes(definition)
        definition["content_sha256"] = compiler.definition_content_sha256(definition)
        definition["cache_key"] = compiler.compute_cache_key(definition)
        self.assertNotEqual(report.definition["cache_key"], definition["cache_key"])

    def test_l_malformed_source_fails_closed(self):
        raw = b"---\nname: broken\n# no closed frontmatter\n"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "evaluation" / "external-skills" / "snapshots" / "kd-sympy" / "SKILL.md"
            path.parent.mkdir(parents=True)
            path.write_bytes(raw)
            manifest = copy.deepcopy(self.manifest)
            record = next(item for item in manifest["records"] if item["candidate_id"] == "kd-sympy")
            record["snapshot_path"] = "evaluation/external-skills/snapshots/kd-sympy/SKILL.md"
            record["sha256"] = hashlib.sha256(raw).hexdigest()
            record["byte_size"] = len(raw)
            report = self.compile(manifest=manifest, repo_root=root)
        self.assertIn("MALFORMED_SOURCE", self.codes(report))

    def test_ambiguous_provenance_fails_closed(self):
        source_record = next(item for item in self.manifest["records"] if item["candidate_id"] == "kd-sympy")
        raw = REPO_ROOT.joinpath(*Path(source_record["snapshot_path"]).parts).read_bytes()
        claim = self.rules["candidates"]["kd-sympy"]["units"][0]["source_claim"].encode("utf-8")
        duplicated = raw + b"\n\n## Duplicate fixture\n" + claim + b"\n"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root.joinpath(*Path(source_record["snapshot_path"]).parts)
            path.parent.mkdir(parents=True)
            path.write_bytes(duplicated)
            manifest = copy.deepcopy(self.manifest)
            record = next(item for item in manifest["records"] if item["candidate_id"] == "kd-sympy")
            record["sha256"] = hashlib.sha256(duplicated).hexdigest()
            record["byte_size"] = len(duplicated)
            report = self.compile(manifest=manifest, repo_root=root)
        self.assertIn("AMBIGUOUS_PROVENANCE", self.codes(report))

    def test_unknown_safety_classification_and_unsupported_schema_fail_closed(self):
        bad_safety = copy.deepcopy(self.policy)
        bad_safety["high_risk_source_patterns"][0]["category"] = "unknown"
        self.assertIn("UNKNOWN_SAFETY_CLASSIFICATION", self.codes(self.compile(policy=bad_safety)))
        bad_schema = copy.deepcopy(self.policy)
        bad_schema["definition_schema_version"] = 2
        self.assertIn("UNSUPPORTED_SCHEMA", self.codes(self.compile(policy=bad_schema)))

    def test_budget_metadata_inconsistency_fails_closed(self):
        report = self.compile()
        definition = copy.deepcopy(report.definition)
        definition["budget"]["utf8_bytes"] += 1
        issues, checks = self.verify_mutation(report, "kd-sympy", definition, report.provenance)
        self.assertIn("BUDGET_METADATA_INCONSISTENT", self.codes(issues))
        self.assertEqual("FAIL", checks["budget_metadata_consistency"])

    def test_source_high_risk_material_is_recorded_but_not_adapted(self):
        for candidate_id in ("kd-sympy", "kd-citation-management"):
            report = self.compile(candidate_id)
            self.assertTrue(report.provenance["inspection"]["high_risk_signals"])
            all_content = "\n".join(unit["content"] for unit in report.definition["knowledge_units"])
            self.assertEqual([], compiler._forbidden_matches(all_content, self.policy))
            self.assertFalse(any(report.provenance["side_effects"].values()))


if __name__ == "__main__":
    unittest.main()
