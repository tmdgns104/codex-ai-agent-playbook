from __future__ import annotations

import copy
import json
import shutil
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


TEST_ROOT = Path(__file__).resolve().parent
MATERIALIZER_ROOT = TEST_ROOT.parent
REPO_ROOT = MATERIALIZER_ROOT.parents[2]
CONTEXT_VALIDATOR_DIR = MATERIALIZER_ROOT.parent / "context-contract" / "validator"
for directory in (TEST_ROOT, MATERIALIZER_ROOT, CONTEXT_VALIDATOR_DIR):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

from artifact_safety import ArtifactSafetyError  # noqa: E402
from context_contract import canonical_json_bytes, canonical_sha256  # noqa: E402
from coordinator import cleanup_context, prepare_context_launch, verify_prelaunch  # noqa: E402
from fixture_factory import FIXED_TIME_UTC, build_bundle, current_only_bundle  # noqa: E402
from lifecycle import LifecycleError, create_lifecycle, transition  # noqa: E402
from materializer import load_policy, materialize_context  # noqa: E402


class ContextMaterializerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.workspace = Path(tempfile.mkdtemp(prefix=".v84-materializer-test-", dir=REPO_ROOT))
        self.sessions_root = self.workspace / "sessions"

    def tearDown(self) -> None:
        if not self.workspace.exists():
            return
        for path in self.workspace.rglob("*"):
            if path.is_file():
                try:
                    path.chmod(path.stat().st_mode | stat.S_IWUSR)
                except OSError:
                    pass
        shutil.rmtree(self.workspace)

    def prepare(self, bundle=None):
        bundle = bundle or build_bundle()
        result = prepare_context_launch(
            repository_root=REPO_ROOT,
            sessions_root=self.sessions_root,
            **bundle,
        )
        return bundle, result

    def test_a_normal_materialization_reaches_ready_without_backend(self):
        bundle, result = self.prepare()
        self.assertEqual("READY", result["status"], result)
        self.assertTrue(result["launch_allowed"])
        self.assertFalse(result["backend_execution"])
        session = self.sessions_root / bundle["request"]["session_id"]
        self.assertTrue((session / "contexts/context.jsonl").is_file())
        self.assertTrue((session / "contexts/envelope.json").is_file())
        self.assertEqual(
            ["CREATED", "VALIDATED", "MATERIALIZED", "READY"],
            [item["to_state"] for item in result["lifecycle"]["transition_log"]],
        )

    def test_b_duplicate_session_id_is_rejected(self):
        bundle, first = self.prepare()
        self.assertEqual("READY", first["status"])
        second = prepare_context_launch(
            repository_root=REPO_ROOT,
            sessions_root=self.sessions_root,
            **bundle,
        )
        self.assertFalse(second["launch_allowed"])
        self.assertEqual("SESSION_PATH_INVALID", second["failure_code"])

    def test_c_session_path_escape_is_blocked_without_writing_outside(self):
        bundle = build_bundle("escape-session")
        outside = REPO_ROOT.parent / "v84-forbidden-sessions-root"
        result = prepare_context_launch(
            repository_root=REPO_ROOT,
            sessions_root=outside,
            **bundle,
        )
        self.assertFalse(result["launch_allowed"])
        self.assertEqual("SESSION_PATH_INVALID", result["failure_code"])
        self.assertEqual("IN_MEMORY_ONLY_UNSAFE_PATH_NOT_CREATED", result["quarantine_result"]["quarantine"]["record_location"])

    def test_d_symlink_session_component_is_blocked(self):
        bundle = build_bundle("symlink-session")
        original = Path.is_symlink

        def fake_is_symlink(path: Path) -> bool:
            return path == self.sessions_root or original(path)

        with patch.object(Path, "is_symlink", fake_is_symlink):
            result = prepare_context_launch(
                repository_root=REPO_ROOT,
                sessions_root=self.sessions_root,
                **bundle,
            )
        self.assertFalse(result["launch_allowed"])
        self.assertEqual("SESSION_PATH_INVALID", result["failure_code"])

    def test_e_context_hash_mismatch_is_quarantined(self):
        bundle, ready = self.prepare()
        self.assertEqual("READY", ready["status"])
        path = self.sessions_root / bundle["request"]["session_id"] / "contexts/context.jsonl"
        path.chmod(path.stat().st_mode | stat.S_IWUSR)
        path.write_bytes(path.read_bytes() + b"tamper")
        result = verify_prelaunch(
            repository_root=REPO_ROOT,
            sessions_root=self.sessions_root,
            **bundle,
        )
        self.assertEqual("CONTEXT_HASH_MISMATCH", result["failure_code"])
        self.assertEqual("QUARANTINED", result["state"])

    def test_f_source_hash_mismatch_is_blocked(self):
        bundle = build_bundle("source-mismatch-session")
        with patch("materializer.sha256_file", return_value="0" * 64):
            result = prepare_context_launch(
                repository_root=REPO_ROOT,
                sessions_root=self.sessions_root,
                **bundle,
            )
        self.assertFalse(result["launch_allowed"])
        self.assertEqual("SOURCE_HASH_MISMATCH", result["failure_code"])

    def test_g_permission_downgrade_is_blocked(self):
        bundle = build_bundle("permission-session")
        bundle["request"]["permission_decision"]["strongest_gate"] = "AUTO_ALLOWED"
        result = prepare_context_launch(
            repository_root=REPO_ROOT,
            sessions_root=self.sessions_root,
            **bundle,
        )
        self.assertFalse(result["launch_allowed"])
        self.assertEqual("PERMISSION_DOWNGRADE", result["failure_code"])

    def test_h_budget_overflow_is_blocked(self):
        bundle = build_bundle("budget-session")
        bundle["request"]["adapted_context"]["budget"]["max_utf8_bytes"] = 1
        result = prepare_context_launch(
            repository_root=REPO_ROOT,
            sessions_root=self.sessions_root,
            **bundle,
        )
        self.assertEqual("BUDGET_BLOCKED", result["status"])
        self.assertFalse(result["launch_allowed"])

    def test_i_stale_artifact_is_invalidated_then_quarantined(self):
        bundle = build_bundle("stale-session")
        materialize_context(
            repository_root=REPO_ROOT,
            sessions_root=self.sessions_root,
            request=bundle["request"],
            definitions=bundle["definitions"],
            selector_output=bundle["selector_output"],
            materialized_at_utc=bundle["timestamp_utc"],
        )
        manifest_path = self.sessions_root / bundle["request"]["session_id"] / "manifest.json"
        manifest_path.chmod(manifest_path.stat().st_mode | stat.S_IWUSR)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["component_versions"]["selector"] = "stale-selector"
        manifest_path.write_bytes(canonical_json_bytes(manifest))
        result = verify_prelaunch(
            repository_root=REPO_ROOT,
            sessions_root=self.sessions_root,
            **bundle,
        )
        self.assertEqual("INVALIDATED", result["status"])
        states = [item["to_state"] for item in result["quarantine_result"]["lifecycle"]["transition_log"]]
        self.assertEqual(["CREATED", "VALIDATED", "MATERIALIZED", "INVALIDATED", "QUARANTINED"], states)

    def test_j_unexpected_extra_file_is_quarantined(self):
        bundle = build_bundle("extra-file-session")
        materialize_context(
            repository_root=REPO_ROOT,
            sessions_root=self.sessions_root,
            request=bundle["request"],
            definitions=bundle["definitions"],
            selector_output=bundle["selector_output"],
            materialized_at_utc=bundle["timestamp_utc"],
        )
        session = self.sessions_root / bundle["request"]["session_id"]
        (session / "unexpected.txt").write_text("unexpected", encoding="utf-8")
        result = verify_prelaunch(
            repository_root=REPO_ROOT,
            sessions_root=self.sessions_root,
            **bundle,
        )
        self.assertEqual("UNEXPECTED_FILE", result["failure_code"])
        self.assertEqual("QUARANTINED", result["state"])

    def test_k_cleanup_success_removes_only_context_content(self):
        bundle, ready = self.prepare(build_bundle("cleanup-success-session"))
        self.assertEqual("READY", ready["status"])
        result = cleanup_context(
            repository_root=REPO_ROOT,
            sessions_root=self.sessions_root,
            request=bundle["request"],
            definitions=bundle["definitions"],
            timestamp_utc=FIXED_TIME_UTC,
        )
        self.assertEqual("CLEANED", result["state"], result)
        session = self.sessions_root / bundle["request"]["session_id"]
        self.assertFalse((session / "contexts").exists())
        self.assertTrue((session / "manifest.json").is_file())
        self.assertTrue((session / "evidence.json").is_file())

    def test_l_cleanup_failure_is_quarantined(self):
        bundle, ready = self.prepare(build_bundle("cleanup-failure-session"))
        self.assertEqual("READY", ready["status"])

        def fail_delete(_path: Path) -> None:
            raise OSError("deterministic cleanup fixture failure")

        result = cleanup_context(
            repository_root=REPO_ROOT,
            sessions_root=self.sessions_root,
            request=bundle["request"],
            definitions=bundle["definitions"],
            timestamp_utc=FIXED_TIME_UTC,
            remove_file=fail_delete,
        )
        self.assertEqual("CLEANUP_FAILED", result["failure_code"])
        self.assertEqual("QUARANTINED", result["state"])

    def test_m_invalid_lifecycle_transition_is_rejected(self):
        lifecycle = create_lifecycle("transition-session", FIXED_TIME_UTC)
        with self.assertRaises(LifecycleError):
            transition(lifecycle, "READY", reason="SKIP_REQUIRED_STATES", timestamp_utc=FIXED_TIME_UTC)

    def test_n_immutable_artifacts_are_read_only_and_modification_fails_integrity(self):
        bundle, ready = self.prepare(build_bundle("immutable-session"))
        self.assertEqual("READY", ready["status"])
        path = self.sessions_root / bundle["request"]["session_id"] / "contexts/envelope.json"
        self.assertEqual(0, path.stat().st_mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH))
        path.chmod(path.stat().st_mode | stat.S_IWUSR)
        path.write_bytes(b"{}")
        result = verify_prelaunch(
            repository_root=REPO_ROOT,
            sessions_root=self.sessions_root,
            **bundle,
        )
        self.assertIn(result["failure_code"], {"ENVELOPE_HASH_MISMATCH", "ARTIFACT_HASH_MISMATCH"})

    def test_o_deterministic_rebuild_has_identical_context_envelope_and_manifest(self):
        left_root = self.workspace / "left"
        right_root = self.workspace / "right"
        left = build_bundle("deterministic-session")
        right = copy.deepcopy(left)
        materialize_context(
            repository_root=REPO_ROOT,
            sessions_root=left_root,
            request=left["request"],
            definitions=left["definitions"],
            selector_output=left["selector_output"],
            materialized_at_utc=left["timestamp_utc"],
        )
        materialize_context(
            repository_root=REPO_ROOT,
            sessions_root=right_root,
            request=right["request"],
            definitions=right["definitions"],
            selector_output=right["selector_output"],
            materialized_at_utc=right["timestamp_utc"],
        )
        for relative in ("contexts/context.jsonl", "contexts/envelope.json", "manifest.json"):
            left_bytes = (left_root / "deterministic-session" / relative).read_bytes()
            right_bytes = (right_root / "deterministic-session" / relative).read_bytes()
            self.assertEqual(left_bytes, right_bytes, relative)

    def test_p_quarantine_isolated_to_failed_session(self):
        first, first_ready = self.prepare(build_bundle("isolated-first"))
        second, second_ready = self.prepare(build_bundle("isolated-second"))
        self.assertEqual("READY", first_ready["status"])
        self.assertEqual("READY", second_ready["status"])
        first_path = self.sessions_root / first["request"]["session_id"] / "contexts/context.jsonl"
        first_path.chmod(first_path.stat().st_mode | stat.S_IWUSR)
        first_path.write_bytes(b"tampered")
        failed = verify_prelaunch(
            repository_root=REPO_ROOT,
            sessions_root=self.sessions_root,
            **first,
        )
        self.assertEqual("QUARANTINED", failed["state"])
        second_state = json.loads((self.sessions_root / second["request"]["session_id"] / "lifecycle.json").read_text(encoding="utf-8"))["state"]
        self.assertEqual("READY", second_state)

    def test_q_current_only_fallback_is_explicit_and_pre_injection(self):
        bundle = current_only_bundle()
        result = prepare_context_launch(
            repository_root=REPO_ROOT,
            sessions_root=self.sessions_root,
            adapted_context_optional=True,
            **bundle,
        )
        self.assertEqual("CURRENT_ONLY", result["status"], result)
        self.assertTrue(result["explicit_fallback"])
        self.assertEqual(0, result["context_injection_attempt_count"])
        blocked = prepare_context_launch(
            repository_root=REPO_ROOT,
            sessions_root=self.sessions_root,
            adapted_context_optional=True,
            context_injection_attempt_count=1,
            **bundle,
        )
        self.assertFalse(blocked["launch_allowed"])
        self.assertEqual("FALLBACK_AFTER_INJECTION_FORBIDDEN", blocked["failure_code"])

    def test_r_raw_external_and_silent_fallback_are_forbidden(self):
        bundle = build_bundle("raw-fallback-session")
        bundle["request"]["execution_policy"]["fallback_policy_id"] = "raw-external-skill-fallback"
        result = prepare_context_launch(
            repository_root=REPO_ROOT,
            sessions_root=self.sessions_root,
            **bundle,
        )
        self.assertFalse(result["launch_allowed"])
        self.assertEqual("FORBIDDEN_FALLBACK", result["failure_code"])
        self.assertFalse(result["raw_external_fallback"])
        self.assertFalse(result["silent_fallback"])

    def test_backend_false_or_unknown_never_reaches_ready(self):
        for status, support in (("UNSUPPORTED", False), ("UNKNOWN", None)):
            with self.subTest(status=status):
                bundle = build_bundle(f"backend-{status.lower()}")
                bundle["probe"]["support_status"] = status
                bundle["probe"]["supports_separate_verified_context"] = support
                bundle["request"]["backend"]["capability_probe_sha256"] = canonical_sha256(bundle["probe"])
                result = prepare_context_launch(
                    repository_root=REPO_ROOT,
                    sessions_root=self.sessions_root,
                    **bundle,
                )
                self.assertFalse(result["launch_allowed"])
                self.assertIn(result["failure_code"], {"BACKEND_CAPABILITY_FALSE", "BACKEND_CAPABILITY_UNKNOWN"})

    def test_both_initial_candidates_and_approved_composition_materialize(self):
        citation = build_bundle(
            "citation-session",
            candidate_ids=("kd-citation-management",),
            task_text="perform local citation normalization and bibliography-consistency",
        )
        citation_result = prepare_context_launch(
            repository_root=REPO_ROOT,
            sessions_root=self.sessions_root,
            **citation,
        )
        self.assertEqual("READY", citation_result["status"], citation_result)
        self.assertEqual("HUMAN_GATE_REQUIRED", citation_result["permission_decision"]["strongest_gate"])

        composition = build_bundle(
            "composition-session",
            candidate_ids=("kd-sympy", "kd-citation-management"),
            task_text="both symbolic mathematics and citation management with exact symbolic algebra and local citation normalization",
            approve_composition=True,
        )
        composition_result = prepare_context_launch(
            repository_root=REPO_ROOT,
            sessions_root=self.sessions_root,
            **composition,
        )
        self.assertEqual("READY", composition_result["status"], composition_result)
        envelope = json.loads(
            (
                self.sessions_root
                / composition["request"]["session_id"]
                / "contexts/envelope.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(2, len(envelope["selected_capabilities"]))
        self.assertEqual(8, len(envelope["selected_unit_ids"]))

    def test_malformed_request_schema_never_materializes(self):
        bundle = build_bundle("malformed-request-session")
        del bundle["request"]["task"]["utf8_sha256"]
        result = prepare_context_launch(
            repository_root=REPO_ROOT,
            sessions_root=self.sessions_root,
            **bundle,
        )
        self.assertFalse(result["launch_allowed"])
        self.assertEqual("SCHEMA_INVALID", result["failure_code"])

    def test_task_occurrence_and_context_path_escape_fail_closed(self):
        duplicate_task = build_bundle("duplicate-task-session")
        duplicate_task["request"]["current_plan"]["selected_capability_ids"] = [
            duplicate_task["request"]["task"]["text"]
        ]
        duplicate_result = prepare_context_launch(
            repository_root=REPO_ROOT,
            sessions_root=self.sessions_root,
            **duplicate_task,
        )
        self.assertEqual("TASK_OCCURRENCE_INVALID", duplicate_result["failure_code"])

        escaped_path = build_bundle("envelope-path-session")
        escaped_path["request"]["adapted_context"]["envelope_relative_path"] = "../envelope.json"
        escaped_result = prepare_context_launch(
            repository_root=REPO_ROOT,
            sessions_root=self.sessions_root,
            **escaped_path,
        )
        self.assertFalse(escaped_result["launch_allowed"])
        self.assertEqual("REQUEST_ENVELOPE_MISMATCH", escaped_result["failure_code"])

    def test_duplicate_injection_attempt_is_blocked_before_ready(self):
        bundle = build_bundle("duplicate-injection-session")
        result = prepare_context_launch(
            repository_root=REPO_ROOT,
            sessions_root=self.sessions_root,
            context_injection_attempt_count=1,
            **bundle,
        )
        self.assertFalse(result["launch_allowed"])
        self.assertEqual("DUPLICATE_INJECTION", result["failure_code"])

    def test_malformed_manifest_is_quarantined(self):
        bundle = build_bundle("malformed-manifest-session")
        materialize_context(
            repository_root=REPO_ROOT,
            sessions_root=self.sessions_root,
            request=bundle["request"],
            definitions=bundle["definitions"],
            selector_output=bundle["selector_output"],
            materialized_at_utc=bundle["timestamp_utc"],
        )
        path = self.sessions_root / bundle["request"]["session_id"] / "manifest.json"
        path.chmod(path.stat().st_mode | stat.S_IWUSR)
        path.write_text("{malformed", encoding="utf-8")
        result = verify_prelaunch(
            repository_root=REPO_ROOT,
            sessions_root=self.sessions_root,
            **bundle,
        )
        self.assertEqual("QUARANTINED", result["state"])
        self.assertEqual("MALFORMED_MANIFEST", result["failure_code"])


if __name__ == "__main__":
    unittest.main()
