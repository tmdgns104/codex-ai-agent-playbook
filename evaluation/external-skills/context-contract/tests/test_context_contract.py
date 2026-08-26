"""Unit tests for the offline V8.4 context contract."""

from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


HERE = Path(__file__).resolve().parent
VALIDATOR = HERE.parent / "validator"
SCHEMA = HERE.parent / "schema"
sys.path.insert(0, str(VALIDATOR))
sys.path.insert(0, str(HERE))

from context_contract import (  # noqa: E402
    CanonicalJsonError,
    assemble_context_text,
    canonical_json_bytes,
    canonical_sha256,
    hash_without_field,
    load_schemas,
    strongest_permission_gate,
    utf8_sha256,
    validate_contract_bundle,
)
from fake_backend import make_compliant_result  # noqa: E402
from fixture_factory import (  # noqa: E402
    apply_failure_case,
    build_compliant_bundle,
    canonical_envelope_bytes,
)
from schema_validation import validate_instance  # noqa: E402


class ContractTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.compliant_path = HERE / "fixtures" / "compliant.json"
        cls.failure_path = HERE / "fixtures" / "failure-cases.json"
        cls.compliant = json.loads(cls.compliant_path.read_text(encoding="utf-8"))
        cls.failure_cases = json.loads(cls.failure_path.read_text(encoding="utf-8"))["cases"]

    def validate_bundle(
        self,
        bundle: dict,
        *,
        artifact_bytes: bytes | None = None,
        definition_marker: object = ...,
        envelope_marker: object = ...,
    ):
        with tempfile.TemporaryDirectory(prefix="v84-context-contract-") as temp:
            session_root = Path(temp) / bundle["request"]["session_id"]
            context_dir = session_root / "contexts"
            context_dir.mkdir(parents=True)
            (context_dir / "envelope.json").write_bytes(
                artifact_bytes if artifact_bytes is not None else canonical_envelope_bytes(bundle)
            )
            definition = bundle["definition"] if definition_marker is ... else definition_marker
            envelope = bundle["envelope"] if envelope_marker is ... else envelope_marker
            return validate_contract_bundle(
                request=bundle["request"],
                result=bundle["result"],
                probe=bundle["probe"],
                expected_task_text=bundle["expected_task_text"],
                session_root=session_root,
                definition=definition,
                envelope=envelope,
                schema_root=SCHEMA,
                validation_time_utc=bundle["validation_time_utc"],
            )

    def test_checked_in_fixture_is_reproducible(self) -> None:
        self.assertEqual(self.compliant, build_compliant_bundle())

    def test_all_schema_documents_and_compliant_instances_are_valid(self) -> None:
        schemas = load_schemas(SCHEMA)
        self.assertEqual({"definition", "envelope", "request", "result", "probe"}, set(schemas))
        for name, schema in schemas.items():
            with self.subTest(schema=name):
                parsed = json.loads((SCHEMA / next(
                    filename for key, filename in {
                        "definition": "adapted-capability-definition-v1.schema.json",
                        "envelope": "runtime-context-envelope-v1.schema.json",
                        "request": "context-launch-request-v1.schema.json",
                        "result": "context-launch-result-v1.schema.json",
                        "probe": "backend-capability-probe-v1.schema.json",
                    }.items() if key == name
                )).read_text(encoding="utf-8"))
                self.assertEqual(schema, parsed)
                self.assertEqual([], validate_instance(self.compliant[name], schema))

    def test_canonical_serialization_is_deterministic_utf8_and_preserves_null(self) -> None:
        left = {"한글": "값", "z": None, "a": [2, 1]}
        right = {"a": [2, 1], "z": None, "한글": "값"}
        self.assertEqual(canonical_json_bytes(left), canonical_json_bytes(right))
        self.assertEqual(canonical_sha256(left), canonical_sha256(right))
        self.assertEqual('{"a":[2,1],"z":null,"한글":"값"}'.encode("utf-8"), canonical_json_bytes(left))

    def test_canonical_serialization_rejects_floating_point(self) -> None:
        with self.assertRaises(CanonicalJsonError):
            canonical_json_bytes({"ambiguous": 0.1})

    def test_strongest_permission_is_order_independent_and_cannot_downgrade(self) -> None:
        first = strongest_permission_gate(["network", "local_read", "external_write"])
        second = strongest_permission_gate(["external_write", "network", "local_read", "network"])
        self.assertEqual(first, second)
        self.assertEqual((["external_write", "local_read", "network"], "HUMAN_GATE_REQUIRED"), first)
        with self.assertRaises(ValueError):
            strongest_permission_gate(["unknown-permission"])

    def test_compliant_fake_backend_passes(self) -> None:
        report = self.validate_bundle(self.compliant)
        self.assertEqual("PASS", report.status, report.as_dict())
        self.assertEqual((), report.issues)

    def test_fake_backend_result_is_pure_and_reproducible(self) -> None:
        expected = self.compliant["result"]
        actual = make_compliant_result(
            self.compliant["request"],
            self.compliant["probe"],
            self.compliant["envelope"]["context_sha256"],
        )
        self.assertEqual(expected, actual)
        self.assertEqual(
            {"external_access": False, "credentials": False, "external_write": False, "destructive": False},
            actual["side_effects"],
        )

    def test_all_declared_failure_fixtures_fail_closed(self) -> None:
        pass_count = 0
        non_pass_count = 0
        for case in self.failure_cases:
            with self.subTest(fixture=case["fixture_id"]):
                bundle = apply_failure_case(self.compliant, case)
                report = self.validate_bundle(bundle)
                self.assertEqual(case["expected_status"], report.status, report.as_dict())
                codes = {issue.code for issue in report.issues}
                if case["expected_code"] is not None:
                    self.assertIn(case["expected_code"], codes, report.as_dict())
                pass_count += int(report.status == "PASS")
                non_pass_count += int(report.status != "PASS")
        self.assertEqual(0, pass_count)
        self.assertEqual(len(self.failure_cases), non_pass_count)

    def test_current_only_requires_zero_context_injections(self) -> None:
        bundle = copy.deepcopy(self.compliant)
        bundle["request"]["mode"] = "CURRENT_ONLY"
        bundle["request"]["adapted_context"] = None
        bundle["request"]["cleanup"]["context_cleanup_required"] = False
        bundle["result"] = make_compliant_result(bundle["request"], bundle["probe"], None)
        report = self.validate_bundle(bundle, definition_marker=None, envelope_marker=None)
        self.assertEqual("PASS", report.status, report.as_dict())
        self.assertEqual(0, bundle["result"]["context_injection_attempt_count"])
        self.assertEqual(0, bundle["result"]["context_injection_count"])

    def test_context_mode_zero_injection_cannot_claim_pass(self) -> None:
        bundle = copy.deepcopy(self.compliant)
        bundle["result"]["context_injection_attempt_count"] = 0
        bundle["result"]["context_injection_count"] = 0
        bundle["result"]["result_sha256"] = hash_without_field(bundle["result"], "result_sha256")
        report = self.validate_bundle(bundle)
        self.assertEqual("FAIL", report.status)
        self.assertIn("RESULT_PASS_INVARIANT_FAILED", {issue.code for issue in report.issues})

    def test_original_task_must_occur_exactly_once_in_request(self) -> None:
        bundle = copy.deepcopy(self.compliant)
        bundle["request"]["current_plan"]["selected_capability_ids"] = [bundle["expected_task_text"]]
        bundle["result"]["request_sha256"] = canonical_sha256(bundle["request"])
        bundle["result"]["result_sha256"] = hash_without_field(bundle["result"], "result_sha256")
        report = self.validate_bundle(bundle)
        self.assertEqual("FAIL", report.status)
        self.assertIn("TASK_OCCURRENCE_INVALID", {issue.code for issue in report.issues})

    def test_backend_declared_failure_cannot_become_validator_pass(self) -> None:
        bundle = copy.deepcopy(self.compliant)
        bundle["result"]["transport_status"] = "FAIL"
        bundle["result"]["failure_code_or_null"] = "VALIDATION_FAILED"
        bundle["result"]["result_sha256"] = hash_without_field(bundle["result"], "result_sha256")
        report = self.validate_bundle(bundle)
        self.assertEqual("FAIL", report.status)
        self.assertIn("BACKEND_RESULT_NOT_PASS", {issue.code for issue in report.issues})

    def test_unknown_or_missing_values_never_become_pass(self) -> None:
        unknown = copy.deepcopy(self.compliant)
        unknown["result"]["integrity_result"] = "UNKNOWN"
        unknown["result"]["result_sha256"] = hash_without_field(unknown["result"], "result_sha256")
        unknown_report = self.validate_bundle(unknown)
        self.assertEqual("FAIL", unknown_report.status)
        self.assertIn("UNKNOWN_CANNOT_PASS", {issue.code for issue in unknown_report.issues})

        missing = copy.deepcopy(self.compliant)
        del missing["probe"]["support_status"]
        missing_report = self.validate_bundle(missing)
        self.assertEqual("FAIL", missing_report.status)
        self.assertIn("SCHEMA_INVALID", {issue.code for issue in missing_report.issues})

    def test_required_unit_truncation_is_blocked(self) -> None:
        bundle = copy.deepcopy(self.compliant)
        definition = bundle["definition"]
        selected_ids = [definition["knowledge_units"][0]["unit_id"]]
        envelope = bundle["envelope"]
        envelope["selected_unit_ids"] = selected_ids
        envelope["selected_units"] = envelope["selected_units"][:1]
        envelope["context_text"] = assemble_context_text(definition, selected_ids)
        envelope["context_sha256"] = utf8_sha256(envelope["context_text"])
        envelope["loaded_context_bytes"] = len(envelope["context_text"].encode("utf-8"))
        adapted = bundle["request"]["adapted_context"]
        adapted["selected_unit_ids"] = selected_ids
        adapted["content_sha256"] = envelope["context_sha256"]
        adapted["loaded_context_bytes"] = envelope["loaded_context_bytes"]
        adapted["envelope_sha256"] = canonical_sha256(envelope)
        bundle["result"] = make_compliant_result(bundle["request"], bundle["probe"], envelope["context_sha256"])
        report = self.validate_bundle(bundle)
        self.assertEqual("FAIL", report.status)
        self.assertIn("REQUIRED_UNIT_TRUNCATED", {issue.code for issue in report.issues})

    def test_source_hash_mismatch_is_blocked(self) -> None:
        bundle = copy.deepcopy(self.compliant)
        wrong = "9" * 64
        bundle["envelope"]["source_snapshot_hashes"] = [wrong]
        bundle["request"]["adapted_context"]["source_snapshot_hashes"] = [wrong]
        bundle["request"]["adapted_context"]["envelope_sha256"] = canonical_sha256(bundle["envelope"])
        bundle["result"]["request_sha256"] = canonical_sha256(bundle["request"])
        bundle["result"]["result_sha256"] = hash_without_field(bundle["result"], "result_sha256")
        report = self.validate_bundle(bundle)
        self.assertEqual("FAIL", report.status)
        self.assertIn("SOURCE_HASH_MISMATCH", {issue.code for issue in report.issues})

    def test_noncanonical_envelope_artifact_is_blocked(self) -> None:
        pretty = json.dumps(self.compliant["envelope"], ensure_ascii=False, indent=2).encode("utf-8")
        report = self.validate_bundle(self.compliant, artifact_bytes=pretty)
        self.assertEqual("FAIL", report.status)
        self.assertIn("ENVELOPE_NOT_CANONICAL", {issue.code for issue in report.issues})

    def test_symlink_component_is_blocked(self) -> None:
        original = Path.is_symlink

        def fake_is_symlink(path: Path) -> bool:
            return path.name == "contexts" or original(path)

        with patch.object(Path, "is_symlink", fake_is_symlink):
            report = self.validate_bundle(self.compliant)
        self.assertEqual("FAIL", report.status)
        self.assertIn("SYMLINK_PATH_BLOCKED", {issue.code for issue in report.issues})

    def test_windows_style_escape_is_blocked_portably(self) -> None:
        bundle = copy.deepcopy(self.compliant)
        bundle["request"]["adapted_context"]["envelope_relative_path"] = "contexts\\..\\escape.json"
        bundle["result"]["request_sha256"] = canonical_sha256(bundle["request"])
        bundle["result"]["result_sha256"] = hash_without_field(bundle["result"], "result_sha256")
        report = self.validate_bundle(bundle)
        self.assertEqual("FAIL", report.status)
        self.assertIn("PATH_ESCAPE_BLOCKED", {issue.code for issue in report.issues})

    def test_token_null_policy_is_fail_closed(self) -> None:
        bundle = copy.deepcopy(self.compliant)
        bundle["envelope"]["token_unavailable_reason_or_null"] = None
        bundle["request"]["adapted_context"]["token_unavailable_reason_or_null"] = None
        bundle["request"]["adapted_context"]["envelope_sha256"] = canonical_sha256(bundle["envelope"])
        bundle["result"]["request_sha256"] = canonical_sha256(bundle["request"])
        bundle["result"]["result_sha256"] = hash_without_field(bundle["result"], "result_sha256")
        report = self.validate_bundle(bundle)
        self.assertEqual("FAIL", report.status)
        self.assertIn("TOKEN_NULL_POLICY_INVALID", {issue.code for issue in report.issues})


if __name__ == "__main__":
    unittest.main()
