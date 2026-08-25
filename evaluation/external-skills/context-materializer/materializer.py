"""Session-local materialization for already selected, approved adapted context.

This module writes verified artifacts only.  It has no process-spawn, model,
transport, network, or raw-Skill fallback behavior.
"""

from __future__ import annotations

import copy
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


HERE = Path(__file__).resolve().parent
CONTEXT_VALIDATOR_DIR = HERE.parent / "context-contract" / "validator"
for directory in (HERE, CONTEXT_VALIDATOR_DIR):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

from artifact_safety import (  # noqa: E402
    ArtifactSafetyError,
    load_json_object,
    make_read_only,
    relative_files,
    replace_json,
    safe_relative_path,
    sha256_file,
    validate_session_location,
    validate_source_path,
    write_bytes_exclusive,
)
from context_contract import (  # noqa: E402
    GATE_RANK,
    TRANSPORT_MODE,
    TRUST_LABEL,
    VALIDATOR_VERSION,
    _validate_definition,
    assemble_context_text,
    canonical_json_bytes,
    canonical_sha256,
    hash_without_field,
    load_schemas,
    strongest_permission_gate,
    utf8_sha256,
)
from lifecycle import create_lifecycle, transition  # noqa: E402
from schema_validation import validate_instance  # noqa: E402


MATERIALIZER_VERSION = "v8.4-context-materializer-1"
MANIFEST_CONTRACT_ID = "v8.4-context-materialization-manifest-v1"
POLICY_PATH = HERE / "policy" / "context-materializer-policy-v1.json"


@dataclass(frozen=True)
class MaterializationIssue:
    code: str
    path: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "path": self.path, "message": self.message}


class MaterializationError(RuntimeError):
    """Fail-closed error with a stable classification and terminal hint."""

    def __init__(self, code: str, message: str, *, status: str = "FAIL") -> None:
        super().__init__(message)
        self.code = code
        self.status = status


def load_policy(path: Path | None = None) -> dict[str, Any]:
    policy_path = path or POLICY_PATH
    try:
        value = json.loads(policy_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise MaterializationError("POLICY_INVALID", str(exc)) from exc
    if not isinstance(value, dict):
        raise MaterializationError("POLICY_INVALID", "materializer policy must be an object")
    expected = {
        "policy_version": "v8.4-context-materializer-policy-1",
        "materializer_version": MATERIALIZER_VERSION,
        "validator_version": VALIDATOR_VERSION,
        "transport_mode": TRANSPORT_MODE,
        "backend_binding": "FAKE_BACKEND_ONLY",
        "raw_external_fallback": False,
        "silent_launcher_v1_fallback": False,
        "runtime_integration": False,
        "external_access": False,
        "backend_execution": False,
    }
    for field, expected_value in expected.items():
        if value.get(field) != expected_value:
            raise MaterializationError("POLICY_INVALID", f"policy {field} must be {expected_value!r}")
    return value


def _all_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        result: list[str] = []
        for item in value:
            result.extend(_all_strings(item))
        return result
    if isinstance(value, dict):
        result = []
        for item in value.values():
            result.extend(_all_strings(item))
        return result
    return []


def _schema_issues(name: str, document: Any, schema: dict[str, Any]) -> list[MaterializationIssue]:
    return [
        MaterializationIssue("SCHEMA_INVALID", f"{name}:{item.path}", item.message)
        for item in validate_instance(document, schema)
    ]


def _raise_issues(issues: list[MaterializationIssue], *, stale: bool = False) -> None:
    if not issues:
        return
    message = "; ".join(f"{item.code}@{item.path}: {item.message}" for item in issues)
    raise MaterializationError(
        issues[0].code,
        message,
        status="INVALIDATED" if stale else "FAIL",
    )


def _ordered_definitions(
    definitions: Iterable[dict[str, Any]],
    selector_output: dict[str, Any],
) -> list[dict[str, Any]]:
    by_candidate: dict[str, dict[str, Any]] = {}
    for definition in definitions:
        candidate_id = definition.get("candidate_id")
        if not isinstance(candidate_id, str) or candidate_id in by_candidate:
            raise MaterializationError("DEFINITION_SET_INVALID", "definition candidate IDs must be unique strings")
        by_candidate[candidate_id] = definition

    selected = selector_output.get("selected_adapted_capabilities", [])
    ordered: list[dict[str, Any]] = []
    for record in selected:
        candidate_id = record.get("candidate_id") if isinstance(record, dict) else None
        definition = by_candidate.get(candidate_id)
        if definition is None:
            raise MaterializationError("DEFINITION_SET_INVALID", f"selected definition missing: {candidate_id}")
        if record.get("adapted_capability_id") != definition.get("adapted_capability_id"):
            raise MaterializationError("DEFINITION_BINDING_MISMATCH", f"adapted capability mismatch: {candidate_id}")
        if record.get("definition_version") != definition.get("version"):
            raise MaterializationError("DEFINITION_BINDING_MISMATCH", f"definition version mismatch: {candidate_id}")
        if record.get("definition_sha256") != canonical_sha256(definition):
            raise MaterializationError("DEFINITION_HASH_MISMATCH", f"definition hash mismatch: {candidate_id}")
        ordered.append(definition)
    if len(ordered) != len(by_candidate) or not ordered:
        raise MaterializationError("DEFINITION_SET_INVALID", "definitions must exactly equal the selector selection")
    return ordered


def _selected_ids_for_definition(
    definition: dict[str, Any],
    selector_output: dict[str, Any],
) -> list[str]:
    candidate_id = definition["candidate_id"]
    records = selector_output.get("budget_plan", {}).get("per_capability", [])
    matching = [item for item in records if item.get("candidate_id") == candidate_id]
    if len(matching) != 1 or not isinstance(matching[0].get("selected_unit_ids"), list):
        raise MaterializationError("BUDGET_BINDING_MISMATCH", f"missing per-capability budget: {candidate_id}")
    return list(matching[0]["selected_unit_ids"])


def _combined_context(
    definitions: list[dict[str, Any]],
    selector_output: dict[str, Any],
) -> tuple[str, list[dict[str, Any]]]:
    texts: list[str] = []
    selected_metadata: list[dict[str, Any]] = []
    all_selected_ids: list[str] = []
    for definition in definitions:
        selected_ids = _selected_ids_for_definition(definition, selector_output)
        units_by_id = {unit["unit_id"]: unit for unit in definition["knowledge_units"]}
        definition_order = [unit["unit_id"] for unit in definition["knowledge_units"]]
        if selected_ids != [unit_id for unit_id in definition_order if unit_id in set(selected_ids)]:
            raise MaterializationError("UNIT_ORDER_INVALID", f"selected unit order invalid: {definition['candidate_id']}")
        if any(unit_id not in units_by_id for unit_id in selected_ids):
            raise MaterializationError("UNKNOWN_UNIT_SELECTED", f"unknown selected unit: {definition['candidate_id']}")
        required = [unit["unit_id"] for unit in definition["knowledge_units"] if unit["required"]]
        missing = [unit_id for unit_id in required if unit_id not in selected_ids]
        if missing:
            raise MaterializationError("REQUIRED_UNIT_TRUNCATED", f"missing required units: {missing}")

        text = assemble_context_text(definition, selected_ids)
        if text:
            texts.append(text)
        for unit_id in selected_ids:
            unit = units_by_id[unit_id]
            selected_metadata.append(
                {
                    "unit_id": unit_id,
                    "required": unit["required"],
                    "content_sha256": unit["content_sha256"],
                    "utf8_bytes": len(unit["content"].encode("utf-8")),
                }
            )
        all_selected_ids.extend(selected_ids)

    if all_selected_ids != selector_output.get("selected_unit_ids"):
        raise MaterializationError("UNIT_SELECTION_MISMATCH", "selector and per-capability unit selections differ")
    return "\n".join(texts), selected_metadata


def _cache_key(definitions: list[dict[str, Any]]) -> str:
    keys = [definition["cache_key"] for definition in definitions]
    return keys[0] if len(keys) == 1 else canonical_sha256(keys)


def build_runtime_envelope(
    *,
    session_id: str,
    task_fingerprint: str,
    definitions: list[dict[str, Any]],
    selector_output: dict[str, Any],
    permission_decision: dict[str, Any],
    materialized_at_utc: str,
) -> dict[str, Any]:
    """Build the exact envelope expected by a later ContextLaunchRequest."""
    ordered = _ordered_definitions(definitions, selector_output)
    context_text, selected_units = _combined_context(ordered, selector_output)
    budget = selector_output["budget_plan"]
    strongest_gate = permission_decision.get("strongest_gate")
    required_gates = [] if strongest_gate == "NONE" else [strongest_gate]
    adaptation_versions = [definition["version"] for definition in ordered]
    if len(set(adaptation_versions)) != len(adaptation_versions):
        # The frozen envelope schema requires unique list items.  Qualifying only
        # colliding versions preserves each exact version and its capability binding.
        adaptation_versions = [
            f"{definition['adapted_capability_id']}@{definition['version']}"
            for definition in ordered
        ]
    return {
        "schema_version": 1,
        "contract_id": "v8.4-runtime-context-envelope-v1",
        "session_id": session_id,
        "task_fingerprint": task_fingerprint,
        "selected_capabilities": [definition["adapted_capability_id"] for definition in ordered],
        "selected_unit_ids": list(selector_output["selected_unit_ids"]),
        "selected_units": selected_units,
        "source_snapshot_hashes": [definition["source"]["snapshot_sha256"] for definition in ordered],
        "adaptation_versions": adaptation_versions,
        "definition_content_hashes": [definition["content_sha256"] for definition in ordered],
        "effective_permissions": list(permission_decision["effective_permissions"]),
        "required_gates": required_gates,
        "trust_label": TRUST_LABEL,
        "context_text": context_text,
        "context_sha256": utf8_sha256(context_text),
        "loaded_context_bytes": len(context_text.encode("utf-8")),
        "prompt_token_count_or_null": budget["token_count_or_null"],
        "tokenizer_id_or_null": budget["tokenizer_id_or_null"],
        "token_unavailable_reason_or_null": budget["unavailable_reason_or_null"],
        "cache_key_or_null": _cache_key(ordered),
        "materialized_at_utc": materialized_at_utc,
        "cleanup_required": True,
    }


def _validate_token_metadata(container: dict[str, Any], path: str) -> list[MaterializationIssue]:
    token_count = container.get("token_count_or_null", container.get("prompt_token_count_or_null"))
    tokenizer = container.get("tokenizer_id_or_null")
    reason = container.get("unavailable_reason_or_null", container.get("token_unavailable_reason_or_null"))
    if token_count is None:
        if tokenizer is not None or not isinstance(reason, str) or not reason.strip():
            return [MaterializationIssue("TOKEN_POLICY_INVALID", path, "null token count requires null tokenizer and a reason")]
    elif tokenizer is None or reason is not None:
        return [MaterializationIssue("TOKEN_POLICY_INVALID", path, "measured tokens require tokenizer and null reason")]
    return []


def validate_inputs(
    *,
    repository_root: Path,
    request: dict[str, Any],
    definitions: list[dict[str, Any]],
    selector_output: dict[str, Any],
    policy: dict[str, Any],
    materialized_at_utc: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Validate selection, provenance, permission, budget, task, and envelope binding."""
    schemas = load_schemas()
    issues = _schema_issues("request", request, schemas["request"])
    _raise_issues(issues)
    if request.get("mode") != TRANSPORT_MODE:
        raise MaterializationError("TRANSPORT_MODE_INVALID", "materialization requires separate verified context mode")
    if request.get("session_id") == "":
        raise MaterializationError("SESSION_BINDING_MISMATCH", "session ID is required")
    if request.get("backend", {}).get("transport_binding") != policy["backend_binding"]:
        raise MaterializationError("BACKEND_BINDING_INVALID", "only the frozen fake backend binding is allowed")
    fallback_id = str(request.get("execution_policy", {}).get("fallback_policy_id", "")).lower()
    if "raw" in fallback_id or "launcher-v1" in fallback_id or "silent" in fallback_id:
        raise MaterializationError("FORBIDDEN_FALLBACK", "raw or silent launcher fallback is forbidden")
    if request.get("execution_policy", {}).get("context_injection_attempt_limit") != 1:
        raise MaterializationError("INJECTION_POLICY_INVALID", "context injection attempt limit must be one")

    if selector_output.get("final_decision") != "ADAPTED_SELECTED":
        raise MaterializationError("SELECTOR_DECISION_INVALID", "materialization requires ADAPTED_SELECTED")
    if selector_output.get("selector_version") != policy["selector_version"]:
        raise MaterializationError("SELECTOR_VERSION_MISMATCH", "selector version is stale")
    if selector_output.get("output_sha256") != hash_without_field(selector_output, "output_sha256"):
        raise MaterializationError("SELECTOR_HASH_MISMATCH", "selector output hash mismatch")
    budget = selector_output.get("budget_plan", {})
    if budget.get("planner_version") != policy["budget_planner_version"] or budget.get("status") != "READY":
        raise MaterializationError("BUDGET_PLAN_INVALID", "budget plan is missing, stale, or not READY")
    if budget.get("budget_plan_sha256") != hash_without_field(budget, "budget_plan_sha256"):
        raise MaterializationError("BUDGET_HASH_MISMATCH", "budget plan hash mismatch")
    _raise_issues(_validate_token_metadata(budget, "selector_output.budget_plan"))

    ordered = _ordered_definitions(definitions, selector_output)
    definition_issues: list[MaterializationIssue] = []
    source_hashes: list[str] = []
    for index, definition in enumerate(ordered):
        definition_issues.extend(_schema_issues(f"definition[{index}]", definition, schemas["definition"]))
        definition_issues.extend(
            MaterializationIssue(item.code, item.path, item.message)
            for item in _validate_definition(definition)
        )
        try:
            source_path = validate_source_path(repository_root, definition["source"]["snapshot_path"])
            actual_hash = sha256_file(source_path)
        except (ArtifactSafetyError, KeyError, OSError) as exc:
            definition_issues.append(MaterializationIssue("SOURCE_PATH_INVALID", f"definition[{index}].source", str(exc)))
            continue
        expected_hash = definition["source"]["snapshot_sha256"]
        if actual_hash != expected_hash:
            definition_issues.append(MaterializationIssue("SOURCE_HASH_MISMATCH", f"definition[{index}].source.snapshot_sha256", "pinned source bytes do not match"))
        source_hashes.append(actual_hash)
    stale = bool(definition_issues) and all(item.code == "STALE_CACHE" for item in definition_issues)
    _raise_issues(definition_issues, stale=stale)

    task = request["task"]
    if task["utf8_sha256"] != utf8_sha256(task["text"]):
        raise MaterializationError("TASK_HASH_MISMATCH", "request task hash mismatch")
    occurrences = [value for value in _all_strings(request) if task["text"] in value]
    if occurrences != [task["text"]]:
        raise MaterializationError("TASK_OCCURRENCE_INVALID", "task must occur exactly once in the request")

    current_permissions = request["current_plan"]["permissions"]
    source_permissions = sorted({permission for definition in ordered for permission in definition["permissions"]["source_permissions"]})
    retained_permissions = sorted({permission for definition in ordered for permission in definition["permissions"]["retained_permissions"]})
    effective, permission_gate = strongest_permission_gate(current_permissions + source_permissions + retained_permissions)
    gates = [permission_gate]
    gates.extend(request["current_plan"]["required_gates"])
    gates.extend(definition["permissions"]["effective_gate"] for definition in ordered)
    strongest_gate = max(gates, key=lambda gate: GATE_RANK[gate])
    permission = request["permission_decision"]
    expected_permission_fields = {
        "current_permissions": sorted(set(current_permissions)),
        "adapted_source_permissions": source_permissions,
        "adapted_effective_permissions": sorted(set(source_permissions) | set(retained_permissions)),
        "effective_permissions": effective,
        "strongest_gate": strongest_gate,
    }
    for field, expected in expected_permission_fields.items():
        if permission.get(field) != expected:
            raise MaterializationError("PERMISSION_DOWNGRADE", f"permission {field} must equal {expected!r}")
    if GATE_RANK[strongest_gate] >= GATE_RANK["NETWORK_REVIEW"] and not permission.get("approval_refs"):
        raise MaterializationError("PERMISSION_APPROVAL_MISSING", "strong permission gate requires approval evidence")

    envelope = build_runtime_envelope(
        session_id=request["session_id"],
        task_fingerprint=task["utf8_sha256"],
        definitions=ordered,
        selector_output=selector_output,
        permission_decision=permission,
        materialized_at_utc=materialized_at_utc,
    )
    _raise_issues(_schema_issues("envelope", envelope, schemas["envelope"]))
    if any(task["text"] in value for value in _all_strings(envelope)):
        raise MaterializationError("TASK_CONTEXT_CONCATENATED", "task text must not occur in the context envelope")

    adapted = request["adapted_context"]
    expected_adapted = {
        "envelope_relative_path": "contexts/envelope.json",
        "envelope_sha256": canonical_sha256(envelope),
        "content_sha256": envelope["context_sha256"],
        "trust_label": TRUST_LABEL,
        "adapted_definition_ids": envelope["selected_capabilities"],
        "adapted_definition_versions": envelope["adaptation_versions"],
        "adapted_definition_hashes": [canonical_sha256(definition) for definition in ordered],
        "source_snapshot_hashes": envelope["source_snapshot_hashes"],
        "selected_unit_ids": envelope["selected_unit_ids"],
        "loaded_context_bytes": envelope["loaded_context_bytes"],
        "prompt_token_count_or_null": envelope["prompt_token_count_or_null"],
        "tokenizer_id_or_null": envelope["tokenizer_id_or_null"],
        "token_unavailable_reason_or_null": envelope["token_unavailable_reason_or_null"],
        "cache_key_or_null": envelope["cache_key_or_null"],
    }
    for field, expected in expected_adapted.items():
        if adapted.get(field) != expected:
            raise MaterializationError("REQUEST_ENVELOPE_MISMATCH", f"adapted context {field} mismatch")
    if adapted["budget"]["budget_policy_version"] != selector_output.get("policy_version"):
        raise MaterializationError("BUDGET_POLICY_MISMATCH", "request and selector budget policy versions differ")
    if envelope["loaded_context_bytes"] != budget["total_utf8_bytes"] or envelope["context_sha256"] != budget["context_sha256"]:
        raise MaterializationError("BUDGET_BINDING_MISMATCH", "assembled context differs from budget plan")
    if envelope["loaded_context_bytes"] > adapted["budget"]["max_utf8_bytes"]:
        status = "BUDGET_BLOCKED" if adapted["budget"]["required_only"] else "FAIL"
        raise MaterializationError("BUDGET_OVERFLOW", "context exceeds request byte budget", status=status)
    _raise_issues(_validate_token_metadata(adapted, "request.adapted_context"))

    computed = {
        "request_hash": canonical_sha256(request),
        "context_hash": envelope["context_sha256"],
        "envelope_hash": canonical_sha256(envelope),
        "source_hashes": source_hashes,
        "effective_permissions": effective,
        "strongest_gate": strongest_gate,
        "loaded_context_bytes": envelope["loaded_context_bytes"],
    }
    return envelope, computed


def _manifest(
    *,
    request: dict[str, Any],
    envelope: dict[str, Any],
    definitions: list[dict[str, Any]],
    selector_output: dict[str, Any],
    computed: dict[str, Any],
    policy: dict[str, Any],
    materialized_at_utc: str,
) -> dict[str, Any]:
    ordered = _ordered_definitions(definitions, selector_output)
    manifest = {
        "schema_version": 1,
        "contract_id": MANIFEST_CONTRACT_ID,
        "managed_by": MATERIALIZER_VERSION,
        "session_id": request["session_id"],
        "state_at_write": "MATERIALIZED",
        "request_hash": computed["request_hash"],
        "context_hash": computed["context_hash"],
        "envelope_hash": computed["envelope_hash"],
        "source_hashes": computed["source_hashes"],
        "adapted_capability_versions": [
            {
                "candidate_id": definition["candidate_id"],
                "adapted_capability_id": definition["adapted_capability_id"],
                "version": definition["version"],
                "definition_sha256": canonical_sha256(definition),
                "definition_content_sha256": definition["content_sha256"],
            }
            for definition in ordered
        ],
        "selected_units": copy.deepcopy(envelope["selected_units"]),
        "selected_unit_ids": list(envelope["selected_unit_ids"]),
        "selected_capability_ids": list(envelope["selected_capabilities"]),
        "loaded_context_bytes": envelope["loaded_context_bytes"],
        "token_count_or_null": envelope["prompt_token_count_or_null"],
        "tokenizer_id_or_null": envelope["tokenizer_id_or_null"],
        "unavailable_reason_or_null": envelope["token_unavailable_reason_or_null"],
        "permission_decision": copy.deepcopy(request["permission_decision"]),
        "budget_plan_sha256": selector_output["budget_plan"]["budget_plan_sha256"],
        "selector_output_sha256": selector_output["output_sha256"],
        "materialized_paths": {
            "context": "contexts/context.jsonl",
            "envelope": "contexts/envelope.json",
        },
        "artifact_hashes": {
            "contexts/context.jsonl": hashlib.sha256(envelope["context_text"].encode("utf-8")).hexdigest(),
            "contexts/envelope.json": canonical_sha256(envelope),
        },
        "cleanup": {
            "required": True,
            "content_files": list(policy["cleanup_content_files"]),
            "quarantine_on_failure": True,
        },
        "component_versions": {
            "compiler": policy["compiler_version"],
            "selector": policy["selector_version"],
            "budget_planner": policy["budget_planner_version"],
            "validator": policy["validator_version"],
            "materializer": policy["materializer_version"],
            "coordinator": policy["coordinator_version"],
            "lifecycle": policy["lifecycle_version"],
            "permission_policy": policy["permission_policy_version"],
            "policy": policy["policy_version"],
        },
        "materialized_at_utc": materialized_at_utc,
        "backend_execution": False,
        "raw_external_fallback": False,
    }
    return manifest


def materialize_context(
    *,
    repository_root: Path,
    sessions_root: Path,
    request: dict[str, Any],
    definitions: list[dict[str, Any]],
    selector_output: dict[str, Any],
    materialized_at_utc: str,
    policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a new session once and return a MATERIALIZED checkpoint."""
    frozen_policy = copy.deepcopy(policy or load_policy())
    try:
        repository, sessions, session = validate_session_location(
            repository_root,
            sessions_root,
            request.get("session_id", ""),
            require_new=True,
        )
    except (ArtifactSafetyError, OSError) as exc:
        raise MaterializationError("SESSION_PATH_INVALID", str(exc)) from exc

    sessions.mkdir(parents=True, exist_ok=True)
    session.mkdir(exist_ok=False)
    lifecycle_path = session / "lifecycle.json"
    lifecycle = create_lifecycle(request["session_id"], materialized_at_utc)
    replace_json(lifecycle_path, lifecycle, canonical_json_bytes)

    try:
        envelope, computed = validate_inputs(
            repository_root=repository,
            request=request,
            definitions=definitions,
            selector_output=selector_output,
            policy=frozen_policy,
            materialized_at_utc=materialized_at_utc,
        )
        lifecycle = transition(
            lifecycle,
            "VALIDATED",
            reason="INPUT_CONTRACT_VALIDATED",
            timestamp_utc=materialized_at_utc,
        )
        replace_json(lifecycle_path, lifecycle, canonical_json_bytes)

        context_path = safe_relative_path(session, "contexts/context.jsonl")
        envelope_path = safe_relative_path(session, request["adapted_context"]["envelope_relative_path"])
        if envelope_path.relative_to(session).as_posix() != "contexts/envelope.json":
            raise MaterializationError("ENVELOPE_PATH_INVALID", "envelope path must be contexts/envelope.json")
        write_bytes_exclusive(context_path, envelope["context_text"].encode("utf-8"))
        write_bytes_exclusive(envelope_path, canonical_json_bytes(envelope))

        manifest = _manifest(
            request=request,
            envelope=envelope,
            definitions=definitions,
            selector_output=selector_output,
            computed=computed,
            policy=frozen_policy,
            materialized_at_utc=materialized_at_utc,
        )
        manifest_path = session / "manifest.json"
        write_bytes_exclusive(manifest_path, canonical_json_bytes(manifest))
        for path in (context_path, envelope_path, manifest_path):
            make_read_only(path)

        lifecycle = transition(
            lifecycle,
            "MATERIALIZED",
            reason="CANONICAL_ARTIFACTS_WRITTEN",
            timestamp_utc=materialized_at_utc,
        )
        replace_json(lifecycle_path, lifecycle, canonical_json_bytes)
        return {
            "status": "MATERIALIZED",
            "session_id": request["session_id"],
            "session_relative_path": session.relative_to(repository).as_posix(),
            "materialized_path": str(session),
            "request_hash": computed["request_hash"],
            "context_hash": computed["context_hash"],
            "envelope_hash": computed["envelope_hash"],
            "manifest_hash": canonical_sha256(manifest),
            "source_hashes": computed["source_hashes"],
            "loaded_context_bytes": computed["loaded_context_bytes"],
            "token_count_or_null": envelope["prompt_token_count_or_null"],
            "tokenizer_id_or_null": envelope["tokenizer_id_or_null"],
            "unavailable_reason_or_null": envelope["token_unavailable_reason_or_null"],
            "permission_decision": copy.deepcopy(request["permission_decision"]),
            "selected_units": list(envelope["selected_unit_ids"]),
            "selected_capabilities": list(envelope["selected_capabilities"]),
            "lifecycle": lifecycle,
            "component_versions": manifest["component_versions"],
            "cleanup_result": "PENDING",
            "quarantine_result": "NOT_REQUIRED",
            "backend_execution": False,
        }
    except Exception:
        # The coordinator owns classification/quarantine; leave this new session
        # intact so no failure evidence is destroyed by an eager recursive delete.
        raise


def load_materialized_session(session_root: Path) -> tuple[dict[str, Any], dict[str, Any], bytes]:
    manifest = load_json_object(session_root / "manifest.json")
    envelope = load_json_object(session_root / "contexts" / "envelope.json")
    context_bytes = (session_root / "contexts" / "context.jsonl").read_bytes()
    return manifest, envelope, context_bytes


def verify_expected_file_set(session_root: Path, *, ready_or_later: bool) -> None:
    expected = {
        "contexts/context.jsonl",
        "contexts/envelope.json",
        "manifest.json",
        "lifecycle.json",
    }
    if ready_or_later:
        expected.add("evidence.json")
    actual = set(relative_files(session_root))
    unexpected = sorted(actual - expected)
    missing = sorted(expected - actual)
    if unexpected:
        raise MaterializationError("UNEXPECTED_FILE", f"unexpected session files: {unexpected}")
    if missing:
        raise MaterializationError("MISSING_ARTIFACT", f"missing session files: {missing}")
