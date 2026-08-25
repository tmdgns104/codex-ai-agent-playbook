"""Final pre-launch coordinator for fake-backend contract verification only."""

from __future__ import annotations

import copy
import stat
import sys
from pathlib import Path
from typing import Any, Callable


HERE = Path(__file__).resolve().parent
CONTEXT_VALIDATOR_DIR = HERE.parent / "context-contract" / "validator"
for directory in (HERE, CONTEXT_VALIDATOR_DIR):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

from artifact_safety import (  # noqa: E402
    ArtifactSafetyError,
    load_json_object,
    relative_files,
    replace_json,
    sha256_file,
    validate_session_location,
)
from context_contract import (  # noqa: E402
    _parse_utc,
    _validate_probe,
    canonical_json_bytes,
    canonical_sha256,
    load_schemas,
    utf8_sha256,
)
from lifecycle import LifecycleError, transition, validate_lifecycle  # noqa: E402
from lifecycle_ops import cleanup_materialized_session, quarantine_session  # noqa: E402
from materializer import (  # noqa: E402
    MANIFEST_CONTRACT_ID,
    MaterializationError,
    _manifest,
    load_materialized_session,
    load_policy,
    materialize_context,
    validate_inputs,
    verify_expected_file_set,
)
from schema_validation import validate_instance  # noqa: E402


COORDINATOR_VERSION = "v8.4-launch-coordinator-1"


def _request_hash_or_null(request: dict[str, Any]) -> str | None:
    try:
        return canonical_sha256(request)
    except (TypeError, ValueError):
        return None


def _source_hashes(definitions: list[dict[str, Any]]) -> list[str]:
    return [
        definition.get("source", {}).get("snapshot_sha256")
        for definition in definitions
        if isinstance(definition, dict)
        and isinstance(definition.get("source"), dict)
        and isinstance(definition["source"].get("snapshot_sha256"), str)
    ]


def _quarantine_after_failure(
    *,
    repository_root: Path,
    sessions_root: Path,
    request: dict[str, Any],
    definitions: list[dict[str, Any]],
    timestamp_utc: str,
    error: Exception,
    invalidated: bool,
) -> dict[str, Any]:
    session_id = str(request.get("session_id", "invalid-session"))
    reason = getattr(error, "code", type(error).__name__)
    try:
        quarantined = quarantine_session(
            repository_root=repository_root,
            sessions_root=sessions_root,
            session_id=session_id,
            reason=reason,
            timestamp_utc=timestamp_utc,
            request_hash_or_null=_request_hash_or_null(request),
            source_hashes=_source_hashes(definitions),
            invalidated=invalidated,
        )
    except Exception:
        quarantined = {
            "status": "QUARANTINED",
            "state": "QUARANTINED",
            "quarantine": {
                "session_id": session_id,
                "reason": reason,
                "artifact_hash": canonical_sha256({}),
                "timestamp_utc": timestamp_utc,
                "source_hashes": _source_hashes(definitions),
                "request_hash_or_null": _request_hash_or_null(request),
                "record_location": "IN_MEMORY_ONLY_UNSAFE_PATH_NOT_CREATED",
            },
        }
    error_status = getattr(error, "status", "FAIL")
    terminal_status = "INVALIDATED" if invalidated else error_status
    return {
        "status": terminal_status,
        "state": quarantined["state"],
        "session_id": session_id,
        "launch_allowed": False,
        "failure_code": reason,
        "message": str(error),
        "cleanup_result": "NOT_RUN",
        "quarantine_result": quarantined,
        "backend_execution": False,
        "raw_external_fallback": False,
        "silent_fallback": False,
    }


def _validate_current_only(
    *,
    request: dict[str, Any],
    definitions: list[dict[str, Any]],
    selector_output: dict[str, Any],
    context_injection_attempt_count: int,
    adapted_context_optional: bool,
) -> dict[str, Any]:
    schemas = load_schemas()
    violations = validate_instance(request, schemas["request"])
    if violations:
        raise MaterializationError("SCHEMA_INVALID", violations[0].message)
    if request.get("mode") != "CURRENT_ONLY" or request.get("adapted_context") is not None:
        raise MaterializationError("CURRENT_ONLY_CONTEXT_FORBIDDEN", "CURRENT_ONLY must carry no adapted context")
    if definitions or selector_output.get("selected_unit_ids") or selector_output.get("selected_adapted_capabilities"):
        raise MaterializationError("CURRENT_ONLY_SELECTION_FORBIDDEN", "CURRENT_ONLY must carry no selected adapted data")
    if not adapted_context_optional:
        raise MaterializationError("CURRENT_ONLY_NOT_AUTHORIZED", "adapted context is required for this task")
    if context_injection_attempt_count != 0:
        raise MaterializationError("FALLBACK_AFTER_INJECTION_FORBIDDEN", "CURRENT_ONLY is allowed only before injection")
    fallback_id = str(request.get("execution_policy", {}).get("fallback_policy_id", "")).lower()
    if fallback_id != "explicit-current-only-v1":
        raise MaterializationError("SILENT_FALLBACK_FORBIDDEN", "CURRENT_ONLY requires the explicit fallback policy")
    task = request["task"]
    if task["utf8_sha256"] != utf8_sha256(task["text"]):
        raise MaterializationError("TASK_HASH_MISMATCH", "CURRENT_ONLY task hash mismatch")
    occurrences = sum(
        1
        for value in _all_strings(request)
        if task["text"] in value
    )
    if occurrences != 1:
        raise MaterializationError("TASK_OCCURRENCE_INVALID", "CURRENT_ONLY task must occur exactly once")
    return {
        "status": "CURRENT_ONLY",
        "state": "VALIDATED",
        "session_id": request["session_id"],
        "launch_allowed": True,
        "explicit_fallback": True,
        "fallback_stage": "BEFORE_CONTEXT_INJECTION",
        "context_injection_attempt_count": 0,
        "context_injection_count": 0,
        "request_hash": canonical_sha256(request),
        "evidence": {
            "reason": "ADAPTED_CONTEXT_OPTIONAL_AND_NOT_INJECTED",
            "selector_decision": selector_output.get("final_decision"),
            "raw_external_fallback": False,
            "silent_launcher_v1_fallback": False,
        },
        "backend_execution": False,
    }


def _all_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [text for item in value for text in _all_strings(item)]
    if isinstance(value, dict):
        return [text for item in value.values() for text in _all_strings(item)]
    return []


def _require_manifest_shape(manifest: dict[str, Any], request: dict[str, Any], policy: dict[str, Any]) -> None:
    required = {
        "schema_version",
        "contract_id",
        "managed_by",
        "session_id",
        "state_at_write",
        "request_hash",
        "context_hash",
        "envelope_hash",
        "source_hashes",
        "adapted_capability_versions",
        "selected_units",
        "selected_unit_ids",
        "selected_capability_ids",
        "loaded_context_bytes",
        "token_count_or_null",
        "tokenizer_id_or_null",
        "unavailable_reason_or_null",
        "permission_decision",
        "budget_plan_sha256",
        "selector_output_sha256",
        "materialized_paths",
        "artifact_hashes",
        "cleanup",
        "component_versions",
        "materialized_at_utc",
        "backend_execution",
        "raw_external_fallback",
    }
    missing = sorted(required - set(manifest))
    if missing:
        raise MaterializationError("MALFORMED_MANIFEST", f"manifest fields missing: {missing}")
    if manifest.get("schema_version") != 1 or manifest.get("contract_id") != MANIFEST_CONTRACT_ID:
        raise MaterializationError("MALFORMED_MANIFEST", "unsupported manifest contract")
    if manifest.get("session_id") != request.get("session_id"):
        raise MaterializationError("SESSION_BINDING_MISMATCH", "manifest session mismatch")
    expected_versions = {
        "compiler": policy["compiler_version"],
        "selector": policy["selector_version"],
        "budget_planner": policy["budget_planner_version"],
        "validator": policy["validator_version"],
        "materializer": policy["materializer_version"],
        "coordinator": policy["coordinator_version"],
        "lifecycle": policy["lifecycle_version"],
        "permission_policy": policy["permission_policy_version"],
        "policy": policy["policy_version"],
    }
    if manifest.get("component_versions") != expected_versions:
        raise MaterializationError("STALE_ARTIFACT", "manifest component versions are stale", status="INVALIDATED")
    if manifest.get("backend_execution") is not False or manifest.get("raw_external_fallback") is not False:
        raise MaterializationError("MALFORMED_MANIFEST", "manifest claims forbidden execution or fallback")


def _verify_prelaunch(
    *,
    repository_root: Path,
    sessions_root: Path,
    request: dict[str, Any],
    definitions: list[dict[str, Any]],
    selector_output: dict[str, Any],
    probe: dict[str, Any],
    validation_time_utc: str,
    context_injection_attempt_count: int,
    policy: dict[str, Any],
) -> dict[str, Any]:
    try:
        repository, _, session = validate_session_location(
            repository_root,
            sessions_root,
            request["session_id"],
            require_new=False,
        )
    except (ArtifactSafetyError, OSError) as exc:
        raise MaterializationError("SESSION_PATH_INVALID", str(exc)) from exc
    lifecycle_path = session / "lifecycle.json"
    lifecycle = load_json_object(lifecycle_path)
    validate_lifecycle(lifecycle)
    if lifecycle["state"] not in {"MATERIALIZED", "READY"}:
        raise MaterializationError("LIFECYCLE_NOT_PRELAUNCH", f"pre-launch verification cannot run from {lifecycle['state']}")
    verify_expected_file_set(session, ready_or_later=lifecycle["state"] == "READY")

    try:
        manifest, envelope, context_bytes = load_materialized_session(session)
    except ArtifactSafetyError as exc:
        raise MaterializationError("MALFORMED_MANIFEST", str(exc)) from exc
    _require_manifest_shape(manifest, request, policy)
    expected_envelope, computed = validate_inputs(
        repository_root=repository,
        request=request,
        definitions=definitions,
        selector_output=selector_output,
        policy=policy,
        materialized_at_utc=manifest["materialized_at_utc"],
    )
    expected_manifest = _manifest(
        request=request,
        envelope=expected_envelope,
        definitions=definitions,
        selector_output=selector_output,
        computed=computed,
        policy=policy,
        materialized_at_utc=manifest["materialized_at_utc"],
    )
    if canonical_json_bytes(manifest) != canonical_json_bytes(expected_manifest):
        raise MaterializationError("MANIFEST_HASH_MISMATCH", "manifest differs from deterministic reconstruction")
    if canonical_json_bytes(envelope) != canonical_json_bytes(expected_envelope):
        raise MaterializationError("ENVELOPE_HASH_MISMATCH", "materialized envelope differs from the verified envelope")
    if context_bytes != envelope["context_text"].encode("utf-8"):
        raise MaterializationError("CONTEXT_HASH_MISMATCH", "materialized context bytes were modified")
    if manifest["request_hash"] != computed["request_hash"]:
        raise MaterializationError("REQUEST_HASH_MISMATCH", "manifest request hash mismatch")
    if manifest["context_hash"] != computed["context_hash"] or manifest["envelope_hash"] != computed["envelope_hash"]:
        raise MaterializationError("MANIFEST_HASH_MISMATCH", "manifest content or envelope hash mismatch")
    if manifest["source_hashes"] != computed["source_hashes"]:
        raise MaterializationError("SOURCE_HASH_MISMATCH", "manifest source hash mismatch")
    if manifest["loaded_context_bytes"] != computed["loaded_context_bytes"]:
        raise MaterializationError("BUDGET_BINDING_MISMATCH", "manifest byte count mismatch")
    for relative, expected_hash in manifest["artifact_hashes"].items():
        path = session.joinpath(*relative.split("/"))
        if sha256_file(path) != expected_hash:
            raise MaterializationError("ARTIFACT_HASH_MISMATCH", f"artifact hash mismatch: {relative}")
        if path.stat().st_mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH):
            raise MaterializationError("ARTIFACT_MUTABLE", f"immutable artifact is writable: {relative}")

    probe_schema = load_schemas()["probe"]
    violations = validate_instance(probe, probe_schema)
    if violations:
        raise MaterializationError("PROBE_SCHEMA_INVALID", violations[0].message)
    probe_issues = _validate_probe(probe, request, _parse_utc(validation_time_utc))
    if probe_issues:
        raise MaterializationError(probe_issues[0].code, probe_issues[0].message)
    if context_injection_attempt_count != 0:
        raise MaterializationError("DUPLICATE_INJECTION", "pre-launch verification requires zero prior injection attempts")

    gate_results = [
        {"gate": "request_schema", "status": "PASS"},
        {"gate": "task_integrity", "status": "PASS"},
        {"gate": "context_integrity", "status": "PASS"},
        {"gate": "source_integrity", "status": "PASS"},
        {"gate": "definition_integrity", "status": "PASS"},
        {"gate": "selected_unit_integrity", "status": "PASS"},
        {"gate": "budget", "status": "PASS"},
        {"gate": "permission_strongest_gate", "status": "PASS"},
        {"gate": "session_path_containment", "status": "PASS"},
        {"gate": "backend_capability", "status": "PASS"},
        {"gate": "injection_policy", "status": "PASS"},
        {"gate": "freshness", "status": "PASS"},
    ]
    if lifecycle["state"] == "MATERIALIZED":
        lifecycle = transition(
            lifecycle,
            "READY",
            reason="FINAL_PRELAUNCH_GATES_PASSED",
            timestamp_utc=validation_time_utc,
        )
        replace_json(lifecycle_path, lifecycle, canonical_json_bytes)

    evidence = {
        "schema_version": 1,
        "session_id": request["session_id"],
        "state": "READY",
        "request_hash": computed["request_hash"],
        "context_hash": computed["context_hash"],
        "manifest_hash": canonical_sha256(manifest),
        "source_hashes": computed["source_hashes"],
        "adapted_capability_versions": copy.deepcopy(manifest["adapted_capability_versions"]),
        "selected_units": copy.deepcopy(manifest["selected_units"]),
        "loaded_context_bytes": computed["loaded_context_bytes"],
        "token_count_or_null": manifest["token_count_or_null"],
        "tokenizer_id_or_null": manifest["tokenizer_id_or_null"],
        "unavailable_reason_or_null": manifest["unavailable_reason_or_null"],
        "permission_decision": copy.deepcopy(request["permission_decision"]),
        "gate_results": gate_results,
        "materialized_path": session.relative_to(repository).as_posix(),
        "cleanup_result": {"status": "PENDING"},
        "quarantine_result": {"status": "NOT_REQUIRED"},
        "timestamps": {
            "materialized_at_utc": manifest["materialized_at_utc"],
            "validated_at_utc": validation_time_utc,
        },
        "lifecycle_transition_log": lifecycle["transition_log"],
        "component_versions": copy.deepcopy(manifest["component_versions"]),
        "context_injection_attempt_count": 0,
        "context_injection_count": 0,
        "backend_execution": False,
        "launch_contract_ready": True,
    }
    replace_json(session / "evidence.json", evidence, canonical_json_bytes)
    return {
        "status": "READY",
        "state": "READY",
        "session_id": request["session_id"],
        "launch_allowed": True,
        "request_hash": computed["request_hash"],
        "context_hash": computed["context_hash"],
        "manifest_hash": canonical_sha256(manifest),
        "source_hashes": computed["source_hashes"],
        "loaded_context_bytes": computed["loaded_context_bytes"],
        "gate_results": gate_results,
        "permission_decision": copy.deepcopy(request["permission_decision"]),
        "materialized_path": str(session),
        "cleanup_result": "PENDING",
        "quarantine_result": "NOT_REQUIRED",
        "lifecycle": lifecycle,
        "component_versions": manifest["component_versions"],
        "backend_execution": False,
        "transport_execution": False,
        "raw_external_fallback": False,
        "silent_fallback": False,
    }


def verify_prelaunch(
    *,
    repository_root: Path,
    sessions_root: Path,
    request: dict[str, Any],
    definitions: list[dict[str, Any]],
    selector_output: dict[str, Any],
    probe: dict[str, Any],
    timestamp_utc: str,
    context_injection_attempt_count: int = 0,
    policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    frozen_policy = copy.deepcopy(policy or load_policy())
    try:
        return _verify_prelaunch(
            repository_root=repository_root,
            sessions_root=sessions_root,
            request=request,
            definitions=definitions,
            selector_output=selector_output,
            probe=probe,
            validation_time_utc=timestamp_utc,
            context_injection_attempt_count=context_injection_attempt_count,
            policy=frozen_policy,
        )
    except Exception as exc:
        if isinstance(exc, ArtifactSafetyError):
            exc = MaterializationError("SESSION_PATH_INVALID", str(exc))
        invalidated = isinstance(exc, MaterializationError) and exc.status == "INVALIDATED"
        return _quarantine_after_failure(
            repository_root=repository_root,
            sessions_root=sessions_root,
            request=request,
            definitions=definitions,
            timestamp_utc=timestamp_utc,
            error=exc,
            invalidated=invalidated,
        )


def prepare_context_launch(
    *,
    repository_root: Path,
    sessions_root: Path,
    request: dict[str, Any],
    definitions: list[dict[str, Any]],
    selector_output: dict[str, Any],
    probe: dict[str, Any],
    timestamp_utc: str,
    context_injection_attempt_count: int = 0,
    adapted_context_optional: bool = False,
    policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Materialize and verify, but never invoke a backend or transport."""
    frozen_policy = copy.deepcopy(policy or load_policy())
    try:
        if request.get("mode") == "CURRENT_ONLY":
            return _validate_current_only(
                request=request,
                definitions=definitions,
                selector_output=selector_output,
                context_injection_attempt_count=context_injection_attempt_count,
                adapted_context_optional=adapted_context_optional,
            )
        materialize_context(
            repository_root=repository_root,
            sessions_root=sessions_root,
            request=request,
            definitions=definitions,
            selector_output=selector_output,
            materialized_at_utc=timestamp_utc,
            policy=frozen_policy,
        )
    except Exception as exc:
        if isinstance(exc, ArtifactSafetyError):
            exc = MaterializationError("SESSION_PATH_INVALID", str(exc))
        invalidated = isinstance(exc, MaterializationError) and exc.status == "INVALIDATED"
        return _quarantine_after_failure(
            repository_root=repository_root,
            sessions_root=sessions_root,
            request=request,
            definitions=definitions,
            timestamp_utc=timestamp_utc,
            error=exc,
            invalidated=invalidated,
        )
    return verify_prelaunch(
        repository_root=repository_root,
        sessions_root=sessions_root,
        request=request,
        definitions=definitions,
        selector_output=selector_output,
        probe=probe,
        timestamp_utc=timestamp_utc,
        context_injection_attempt_count=context_injection_attempt_count,
        policy=frozen_policy,
    )


def cleanup_context(
    *,
    repository_root: Path,
    sessions_root: Path,
    request: dict[str, Any],
    definitions: list[dict[str, Any]],
    timestamp_utc: str,
    remove_file: Callable[[Path], None] | None = None,
) -> dict[str, Any]:
    """Run finally-safe cleanup and quarantine any failure without broad deletion."""
    try:
        return cleanup_materialized_session(
            repository_root=repository_root,
            sessions_root=sessions_root,
            session_id=request["session_id"],
            timestamp_utc=timestamp_utc,
            remove_file=remove_file,
        )
    except Exception as exc:
        return _quarantine_after_failure(
            repository_root=repository_root,
            sessions_root=sessions_root,
            request=request,
            definitions=definitions,
            timestamp_utc=timestamp_utc,
            error=MaterializationError("CLEANUP_FAILED", str(exc)),
            invalidated=False,
        )
