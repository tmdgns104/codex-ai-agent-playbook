"""Deterministic V8.4 adapted-context contract validation.

The module validates typed offline artifacts and fake backend receipts only. It
does not spawn a process, invoke a backend, load a model, or modify the existing
Router/activation/launcher path.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

from schema_validation import (
    SchemaDefinitionError,
    validate_instance,
    validate_schema_definition,
)


VALIDATOR_VERSION = "v8.4-context-validator-1"
CONTRACT_ID = "v8.4-context-launch-v1"
RESULT_CONTRACT_ID = "v8.4-context-launch-result-v1"
TRANSPORT_MODE = "SEPARATE_VERIFIED_CONTEXT_V1"
TRUST_LABEL = "untrusted-derived-approved-reference"
SCHEMA_FILES = {
    "definition": "adapted-capability-definition-v1.schema.json",
    "envelope": "runtime-context-envelope-v1.schema.json",
    "request": "context-launch-request-v1.schema.json",
    "result": "context-launch-result-v1.schema.json",
    "probe": "backend-capability-probe-v1.schema.json",
}

KNOWN_PERMISSIONS = {
    "browser_control",
    "credential_access",
    "database_write",
    "destructive",
    "external_write",
    "local_read",
    "local_write",
    "network",
    "process_exec",
    "production",
}
SENSITIVE_PERMISSIONS = {
    "credential_access",
    "database_write",
    "destructive",
    "external_write",
    "production",
}
NETWORK_PERMISSIONS = {"browser_control", "network"}
PROFILE_PERMISSIONS = {"local_write", "process_exec"}
GATE_RANK = {
    "NONE": 0,
    "AUTO_ALLOWED": 1,
    "PROFILE_GATED": 2,
    "NETWORK_REVIEW": 3,
    "MANUAL_ONLY": 4,
    "HUMAN_GATE_REQUIRED": 5,
}


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    path: str
    message: str


@dataclass(frozen=True)
class ValidationReport:
    status: str
    issues: tuple[ValidationIssue, ...]
    computed: dict[str, Any]

    @property
    def passed(self) -> bool:
        return self.status == "PASS"

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "passed": self.passed,
            "issues": [
                {"code": issue.code, "path": issue.path, "message": issue.message}
                for issue in self.issues
            ],
            "computed": self.computed,
        }


class CanonicalJsonError(ValueError):
    """Raised when a value cannot be represented by the frozen canonical rules."""


def _validate_canonical_value(value: Any, path: str = "$") -> None:
    if value is None or isinstance(value, (str, bool)):
        return
    if isinstance(value, int) and not isinstance(value, bool):
        return
    if isinstance(value, float):
        raise CanonicalJsonError(f"floating-point values are forbidden at {path}")
    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_canonical_value(item, f"{path}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise CanonicalJsonError(f"object key must be a string at {path}")
            _validate_canonical_value(item, f"{path}.{key}")
        return
    raise CanonicalJsonError(f"unsupported canonical JSON value at {path}: {type(value).__name__}")


def canonical_json_bytes(value: Any) -> bytes:
    """Serialize with sorted fields, UTF-8, compact separators, and explicit nulls."""
    _validate_canonical_value(value)
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def utf8_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def hash_without_field(document: dict[str, Any], field: str) -> str:
    payload = {key: value for key, value in document.items() if key != field}
    return canonical_sha256(payload)


def definition_content_sha256(definition: dict[str, Any]) -> str:
    units: list[dict[str, Any]] = []
    for unit in definition.get("knowledge_units", []):
        units.append({key: value for key, value in unit.items() if key != "content_sha256"})
    return canonical_sha256(units)


def definition_content_bytes(definition: dict[str, Any]) -> int:
    return sum(len(str(unit.get("content", "")).encode("utf-8")) for unit in definition.get("knowledge_units", []))


def compute_cache_key(definition: dict[str, Any]) -> str:
    transformation = definition.get("transformation", {})
    permissions = definition.get("permissions", {})
    verification = definition.get("verification", {})
    budget = definition.get("budget", {})
    source = definition.get("source", {})
    payload = {
        "source_sha256": source.get("snapshot_sha256"),
        "schema_version": definition.get("schema_version"),
        "policy_version": transformation.get("policy_version"),
        "extractor_version": transformation.get("extractor_version"),
        "validator_version": VALIDATOR_VERSION,
        "permission_policy_version": permissions.get("permission_policy_version"),
        "knowledge_unit_hashes": [
            unit.get("content_sha256") for unit in definition.get("knowledge_units", [])
        ],
        "status": definition.get("status"),
        "fixture_evidence": verification.get("fixture_evidence", []),
        "holdout_evidence": verification.get("holdout_evidence", []),
        "tokenizer_id_or_null": budget.get("tokenizer_id_or_null"),
    }
    return canonical_sha256(payload)


def assemble_context_text(definition: dict[str, Any], selected_unit_ids: Iterable[str]) -> str:
    """Assemble exact whole units in definition order as canonical JSON lines."""
    selected = set(selected_unit_ids)
    rows = [
        canonical_json_bytes({"content": unit["content"], "unit_id": unit["unit_id"]}).decode("utf-8")
        for unit in definition.get("knowledge_units", [])
        if unit.get("unit_id") in selected
    ]
    return "\n".join(rows)


def strongest_permission_gate(permissions: Iterable[str]) -> tuple[list[str], str]:
    """Return sorted permission union and its deterministic strongest gate."""
    effective = sorted(set(permissions))
    unknown = sorted(set(effective) - KNOWN_PERMISSIONS)
    if unknown:
        raise ValueError(f"unknown permission(s): {unknown}")
    permission_set = set(effective)
    if permission_set & SENSITIVE_PERMISSIONS:
        return effective, "HUMAN_GATE_REQUIRED"
    if permission_set & NETWORK_PERMISSIONS:
        return effective, "NETWORK_REVIEW"
    if permission_set & PROFILE_PERMISSIONS:
        return effective, "PROFILE_GATED"
    if permission_set:
        return effective, "AUTO_ALLOWED"
    return effective, "NONE"


def load_schemas(schema_root: Path | None = None) -> dict[str, dict[str, Any]]:
    root = schema_root or Path(__file__).resolve().parents[1] / "schema"
    schemas: dict[str, dict[str, Any]] = {}
    for name, filename in SCHEMA_FILES.items():
        path = root / filename
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise SchemaDefinitionError(f"invalid schema file {path}: {exc}") from exc
        if not isinstance(document, dict):
            raise SchemaDefinitionError(f"schema must be an object: {path}")
        validate_schema_definition(document)
        schemas[name] = document
    return schemas


def _issue(code: str, path: str, message: str) -> ValidationIssue:
    return ValidationIssue(code=code, path=path, message=message)


def _report(status: str, issues: list[ValidationIssue], computed: dict[str, Any]) -> ValidationReport:
    return ValidationReport(status=status, issues=tuple(issues), computed=computed)


def _schema_issues(name: str, document: Any, schema: dict[str, Any]) -> list[ValidationIssue]:
    return [
        _issue("SCHEMA_INVALID", f"{name}:{violation.path}", violation.message)
        for violation in validate_instance(document, schema)
    ]


def _parse_utc(value: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError("timestamp must be UTC and end with Z")
    parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include timezone")
    return parsed.astimezone(timezone.utc)


def _all_string_values(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        result: list[str] = []
        for item in value:
            result.extend(_all_string_values(item))
        return result
    if isinstance(value, dict):
        result = []
        for item in value.values():
            result.extend(_all_string_values(item))
        return result
    return []


def _validate_token_policy(container: dict[str, Any], path: str) -> list[ValidationIssue]:
    token_count = container.get("prompt_token_count_or_null", container.get("token_count_or_null"))
    tokenizer = container.get("tokenizer_id_or_null")
    reason = container.get("token_unavailable_reason_or_null", container.get("unavailable_reason_or_null"))
    if token_count is None:
        if tokenizer is not None or not isinstance(reason, str) or not reason.strip():
            return [
                _issue(
                    "TOKEN_NULL_POLICY_INVALID",
                    path,
                    "null token count requires null tokenizer and a non-empty unavailable reason",
                )
            ]
    elif tokenizer is None or reason is not None:
        return [
            _issue(
                "TOKEN_MEASURED_POLICY_INVALID",
                path,
                "measured token count requires tokenizer id and null unavailable reason",
            )
        ]
    return []


def _validate_definition(definition: dict[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if definition.get("status") != "APPROVED":
        issues.append(_issue("DEFINITION_NOT_APPROVED", "definition.status", "runtime definition must be APPROVED"))

    unit_ids: list[str] = []
    for index, unit in enumerate(definition.get("knowledge_units", [])):
        unit_id = unit.get("unit_id")
        unit_ids.append(unit_id)
        expected = canonical_sha256({key: value for key, value in unit.items() if key != "content_sha256"})
        if unit.get("content_sha256") != expected:
            issues.append(
                _issue("UNIT_HASH_MISMATCH", f"definition.knowledge_units[{index}].content_sha256", "knowledge unit hash mismatch")
            )
    if len(unit_ids) != len(set(unit_ids)):
        issues.append(_issue("DUPLICATE_UNIT_ID", "definition.knowledge_units", "unit ids must be unique"))

    if definition.get("content_sha256") != definition_content_sha256(definition):
        issues.append(_issue("DEFINITION_CONTENT_HASH_MISMATCH", "definition.content_sha256", "definition content hash mismatch"))
    if definition.get("budget", {}).get("utf8_bytes") != definition_content_bytes(definition):
        issues.append(_issue("DEFINITION_BYTE_COUNT_MISMATCH", "definition.budget.utf8_bytes", "definition byte count mismatch"))
    issues.extend(_validate_token_policy(definition.get("budget", {}), "definition.budget"))

    verification = definition.get("verification", {})
    for field in ("schema_pass", "provenance_pass", "safety_pass", "fixture_pass", "holdout_pass"):
        if verification.get(field) != "PASS":
            issues.append(_issue("DEFINITION_VERIFICATION_NOT_PASS", f"definition.verification.{field}", "missing, FAIL, or UNKNOWN verification cannot pass"))

    permissions = definition.get("permissions", {})
    source_permissions = set(permissions.get("source_permissions", []))
    retained = set(permissions.get("retained_permissions", []))
    removed = set(permissions.get("removed_permissions", []))
    if not retained.issubset(source_permissions) or not removed.issubset(source_permissions):
        issues.append(_issue("PERMISSION_DELTA_INVALID", "definition.permissions", "retained and removed permissions must come from source permissions"))
    if retained & removed:
        issues.append(_issue("PERMISSION_DELTA_INVALID", "definition.permissions", "a permission cannot be both retained and removed"))
    if removed and not str(permissions.get("removal_justification") or "").strip():
        issues.append(_issue("PERMISSION_REMOVAL_UNJUSTIFIED", "definition.permissions.removal_justification", "removed permissions require justification"))
    try:
        _, definition_gate = strongest_permission_gate(source_permissions | retained)
    except ValueError as exc:
        issues.append(_issue("UNKNOWN_PERMISSION", "definition.permissions", str(exc)))
    else:
        if permissions.get("effective_gate") != definition_gate:
            issues.append(_issue("DEFINITION_GATE_DOWNGRADE", "definition.permissions.effective_gate", f"expected {definition_gate}"))

    if definition.get("cache_key") != compute_cache_key(definition):
        issues.append(_issue("STALE_CACHE", "definition.cache_key", "definition cache key is stale"))
    return issues


def _safe_envelope_path(session_root: Path, session_id: str, relative_text: str) -> tuple[Path | None, list[ValidationIssue]]:
    issues: list[ValidationIssue] = []
    if session_root.name != session_id:
        issues.append(_issue("SESSION_ROOT_MISMATCH", "request.session_id", "session root name must match session id"))
        return None, issues
    if session_root.is_symlink():
        issues.append(_issue("SYMLINK_PATH_BLOCKED", "session_root", "session root must not be a symlink"))
        return None, issues

    if "\\" in relative_text or re.match(r"^[A-Za-z]:", relative_text):
        issues.append(_issue("PATH_ESCAPE_BLOCKED", "request.adapted_context.envelope_relative_path", "envelope path must use portable relative POSIX syntax"))
        return None, issues
    pure = PurePosixPath(relative_text)
    if pure.is_absolute() or not pure.parts or ".." in pure.parts or "." in pure.parts:
        issues.append(_issue("PATH_ESCAPE_BLOCKED", "request.adapted_context.envelope_relative_path", "envelope path must be a normalized relative path"))
        return None, issues
    lowered = [part.lower() for part in pure.parts]
    if lowered[0] != "contexts" or ".agents" in lowered or "skills" in lowered or any(part == "agents.md" for part in lowered):
        issues.append(_issue("FORBIDDEN_CONTEXT_PATH", "request.adapted_context.envelope_relative_path", "context path must stay under the session contexts directory"))
        return None, issues

    candidate = session_root.joinpath(*pure.parts)
    current = session_root
    for part in pure.parts:
        current = current / part
        if current.is_symlink():
            issues.append(_issue("SYMLINK_PATH_BLOCKED", "request.adapted_context.envelope_relative_path", f"symlink component blocked: {part}"))
            return None, issues
    try:
        candidate.resolve(strict=False).relative_to(session_root.resolve(strict=False))
    except ValueError:
        issues.append(_issue("PATH_ESCAPE_BLOCKED", "request.adapted_context.envelope_relative_path", "resolved envelope path escapes session root"))
        return None, issues
    return candidate, issues


def _validate_probe(probe: dict[str, Any], request: dict[str, Any], now: datetime) -> list[ValidationIssue]:
    backend = request.get("backend", {})
    issues: list[ValidationIssue] = []
    if backend.get("capability_probe_id") != probe.get("probe_id") or backend.get("capability_probe_sha256") != canonical_sha256(probe):
        issues.append(_issue("PROBE_HASH_MISMATCH", "request.backend", "backend probe id/hash does not match probe"))
        return issues
    if backend.get("adapter_id") != probe.get("adapter_id") or backend.get("adapter_version") != probe.get("adapter_version"):
        issues.append(_issue("PROBE_ADAPTER_MISMATCH", "request.backend", "request adapter does not match the probed adapter"))
    try:
        expires = _parse_utc(probe["expires_at_utc"])
        _parse_utc(probe["probed_at_utc"])
    except (KeyError, ValueError) as exc:
        return [_issue("PROBE_TIME_INVALID", "probe", str(exc))]
    if expires <= now:
        return [_issue("BACKEND_CAPABILITY_UNKNOWN", "probe.expires_at_utc", "expired probe is not support evidence")]

    status = probe.get("support_status")
    supported = probe.get("supports_separate_verified_context")
    task_separate = probe.get("task_channel_separate")
    context_separate = probe.get("context_channel_separate")
    modes = probe.get("supported_transport_modes", [])
    if status == "UNSUPPORTED" or supported is False:
        return [_issue("BACKEND_CAPABILITY_FALSE", "probe.support_status", "backend explicitly does not support separate verified context")]
    if status == "UNKNOWN" or supported is None or task_separate is None or context_separate is None:
        return [_issue("BACKEND_CAPABILITY_UNKNOWN", "probe.support_status", "unknown backend capability cannot pass")]
    if status != "SUPPORTED" or supported is not True or task_separate is not True or context_separate is not True or TRANSPORT_MODE not in modes:
        return [_issue("BACKEND_CAPABILITY_INCONSISTENT", "probe", "supported probe fields are inconsistent")]
    if probe.get("external_access_performed") is not False:
        issues.append(_issue("EXTERNAL_ACCESS_FORBIDDEN", "probe.external_access_performed", "probe must be offline/fake in this task"))
    return issues


def _validate_task_boundary(request: dict[str, Any], envelope: dict[str, Any] | None, expected_task_text: str) -> list[ValidationIssue]:
    task = request.get("task", {})
    issues: list[ValidationIssue] = []
    if task.get("text") != expected_task_text:
        issues.append(_issue("TASK_TEXT_CHANGED", "request.task.text", "request task must equal the original task exactly"))
    if task.get("utf8_sha256") != utf8_sha256(expected_task_text):
        issues.append(_issue("TASK_HASH_MISMATCH", "request.task.utf8_sha256", "task UTF-8 hash mismatch"))
    containing_values = [value for value in _all_string_values(request) if expected_task_text in value]
    if containing_values != [expected_task_text]:
        issues.append(_issue("TASK_OCCURRENCE_INVALID", "request", "original task must occur in exactly one request string value"))
    if envelope is not None and any(expected_task_text in value for value in _all_string_values(envelope)):
        issues.append(_issue("TASK_CONTEXT_CONCATENATED", "envelope", "task text must not appear in adapted context"))
    return issues


def _validate_permission_decision(definition: dict[str, Any], request: dict[str, Any]) -> tuple[list[ValidationIssue], dict[str, Any]]:
    current_permissions = request.get("current_plan", {}).get("permissions", [])
    definition_permissions = definition.get("permissions", {})
    source_permissions = definition_permissions.get("source_permissions", [])
    retained_permissions = definition_permissions.get("retained_permissions", [])
    reported = request.get("permission_decision", {})
    issues: list[ValidationIssue] = []
    computed: dict[str, Any] = {}
    try:
        effective, permission_gate = strongest_permission_gate(
            list(current_permissions) + list(source_permissions) + list(retained_permissions)
        )
    except ValueError as exc:
        return [_issue("UNKNOWN_PERMISSION", "request.permission_decision", str(exc))], computed
    candidate_gates = [permission_gate, definition_permissions.get("effective_gate", "NONE")]
    candidate_gates.extend(request.get("current_plan", {}).get("required_gates", []))
    strongest = max(candidate_gates, key=lambda gate: GATE_RANK[gate])
    computed["effective_permissions"] = effective
    computed["strongest_gate"] = strongest

    expected_adapted = sorted(set(source_permissions) | set(retained_permissions))
    comparisons = {
        "current_permissions": sorted(set(current_permissions)),
        "adapted_source_permissions": sorted(set(source_permissions)),
        "adapted_effective_permissions": expected_adapted,
        "effective_permissions": effective,
    }
    for field, expected in comparisons.items():
        if reported.get(field) != expected:
            issues.append(_issue("PERMISSION_UNION_MISMATCH", f"request.permission_decision.{field}", f"expected {expected}"))
    if reported.get("strongest_gate") != strongest:
        issues.append(_issue("PERMISSION_DOWNGRADE", "request.permission_decision.strongest_gate", f"expected strongest gate {strongest}"))
    if GATE_RANK[strongest] >= GATE_RANK["NETWORK_REVIEW"] and not reported.get("approval_refs"):
        issues.append(_issue("APPROVAL_REQUIRED", "request.permission_decision.approval_refs", f"{strongest} requires approval evidence"))
    return issues, computed


def _validate_envelope_definition(definition: dict[str, Any], envelope: dict[str, Any], request: dict[str, Any]) -> tuple[list[ValidationIssue], dict[str, Any]]:
    issues: list[ValidationIssue] = []
    computed: dict[str, Any] = {}
    definition_id = definition["adapted_capability_id"]
    selected_ids = envelope.get("selected_unit_ids", [])
    units_by_id = {unit["unit_id"]: unit for unit in definition.get("knowledge_units", [])}
    definition_order = [unit["unit_id"] for unit in definition.get("knowledge_units", [])]
    required_ids = [unit["unit_id"] for unit in definition.get("knowledge_units", []) if unit.get("required")]

    if envelope.get("session_id") != request.get("session_id"):
        issues.append(_issue("SESSION_BINDING_MISMATCH", "envelope.session_id", "envelope session must match request session"))
    if envelope.get("task_fingerprint") != request.get("task", {}).get("utf8_sha256"):
        issues.append(_issue("TASK_FINGERPRINT_MISMATCH", "envelope.task_fingerprint", "envelope task fingerprint must match request task hash"))
    if request.get("adapted_context", {}).get("trust_label") != envelope.get("trust_label"):
        issues.append(_issue("TRUST_LABEL_MISMATCH", "request.adapted_context.trust_label", "request and envelope trust labels must match"))
    reported_permissions = request.get("permission_decision", {})
    if envelope.get("effective_permissions") != reported_permissions.get("effective_permissions"):
        issues.append(_issue("ENVELOPE_PERMISSION_MISMATCH", "envelope.effective_permissions", "envelope permissions must match the verified permission union"))
    strongest_gate = reported_permissions.get("strongest_gate")
    expected_gates = [] if strongest_gate == "NONE" else [strongest_gate]
    if envelope.get("required_gates") != expected_gates:
        issues.append(_issue("ENVELOPE_GATE_MISMATCH", "envelope.required_gates", f"expected {expected_gates}"))

    if envelope.get("selected_capabilities") != [definition_id]:
        issues.append(_issue("CAPABILITY_BINDING_MISMATCH", "envelope.selected_capabilities", "envelope must bind the validated definition"))
    if envelope.get("adaptation_versions") != [definition["version"]]:
        issues.append(_issue("VERSION_BINDING_MISMATCH", "envelope.adaptation_versions", "adaptation version mismatch"))
    if envelope.get("definition_content_hashes") != [definition["content_sha256"]]:
        issues.append(_issue("DEFINITION_HASH_BINDING_MISMATCH", "envelope.definition_content_hashes", "definition content hash mismatch"))
    if envelope.get("source_snapshot_hashes") != [definition["source"]["snapshot_sha256"]]:
        issues.append(_issue("SOURCE_HASH_MISMATCH", "envelope.source_snapshot_hashes", "source snapshot hash mismatch"))
    if any(unit_id not in units_by_id for unit_id in selected_ids):
        issues.append(_issue("UNKNOWN_UNIT_SELECTED", "envelope.selected_unit_ids", "selected unit does not exist in definition"))
    expected_order = [unit_id for unit_id in definition_order if unit_id in set(selected_ids)]
    if selected_ids != expected_order:
        issues.append(_issue("UNIT_ORDER_INVALID", "envelope.selected_unit_ids", "selected units must follow definition order"))
    missing_required = [unit_id for unit_id in required_ids if unit_id not in selected_ids]
    if missing_required:
        issues.append(_issue("REQUIRED_UNIT_TRUNCATED", "envelope.selected_unit_ids", f"missing required units: {missing_required}"))

    expected_units = []
    for unit_id in selected_ids:
        unit = units_by_id.get(unit_id)
        if unit is None:
            continue
        expected_units.append(
            {
                "unit_id": unit_id,
                "required": unit["required"],
                "content_sha256": unit["content_sha256"],
                "utf8_bytes": len(unit["content"].encode("utf-8")),
            }
        )
    if envelope.get("selected_units") != expected_units:
        issues.append(_issue("SELECTED_UNIT_METADATA_MISMATCH", "envelope.selected_units", "selected unit metadata does not match whole definition units"))

    expected_text = assemble_context_text(definition, selected_ids)
    expected_bytes = len(expected_text.encode("utf-8"))
    expected_context_hash = utf8_sha256(expected_text)
    computed.update({"context_sha256": expected_context_hash, "loaded_context_bytes": expected_bytes})
    if envelope.get("context_text") != expected_text:
        issues.append(_issue("CONTEXT_ASSEMBLY_MISMATCH", "envelope.context_text", "context must be exact whole-unit canonical assembly"))
    if envelope.get("context_sha256") != expected_context_hash:
        issues.append(_issue("CONTENT_HASH_MISMATCH", "envelope.context_sha256", "context hash mismatch"))
    if envelope.get("loaded_context_bytes") != expected_bytes:
        issues.append(_issue("CONTEXT_BYTE_COUNT_MISMATCH", "envelope.loaded_context_bytes", "context UTF-8 byte count mismatch"))
    issues.extend(_validate_token_policy(envelope, "envelope"))

    if envelope.get("cache_key_or_null") != definition.get("cache_key"):
        issues.append(_issue("STALE_CACHE", "envelope.cache_key_or_null", "envelope cache key does not match approved definition"))

    adapted = request.get("adapted_context", {})
    expected_definition_hash = canonical_sha256(definition)
    cross_checks = {
        "content_sha256": envelope.get("context_sha256"),
        "adapted_definition_ids": [definition_id],
        "adapted_definition_versions": [definition["version"]],
        "adapted_definition_hashes": [expected_definition_hash],
        "source_snapshot_hashes": [definition["source"]["snapshot_sha256"]],
        "selected_unit_ids": selected_ids,
        "loaded_context_bytes": envelope.get("loaded_context_bytes"),
        "prompt_token_count_or_null": envelope.get("prompt_token_count_or_null"),
        "tokenizer_id_or_null": envelope.get("tokenizer_id_or_null"),
        "token_unavailable_reason_or_null": envelope.get("token_unavailable_reason_or_null"),
        "cache_key_or_null": envelope.get("cache_key_or_null"),
    }
    for field, expected in cross_checks.items():
        if adapted.get(field) != expected:
            issues.append(_issue("REQUEST_ENVELOPE_MISMATCH", f"request.adapted_context.{field}", f"expected {expected!r}"))
    issues.extend(_validate_token_policy(adapted, "request.adapted_context"))

    budget = adapted.get("budget", {})
    required_only = bool(expected_units) and all(item["required"] for item in expected_units)
    if budget.get("required_only") != required_only:
        issues.append(_issue("BUDGET_REQUIRED_FLAG_MISMATCH", "request.adapted_context.budget.required_only", f"expected {required_only}"))
    max_bytes = budget.get("max_utf8_bytes")
    if isinstance(max_bytes, int) and expected_bytes > max_bytes:
        if required_only:
            issues.append(_issue("REQUIRED_ONLY_BUDGET_OVERFLOW", "request.adapted_context.budget.max_utf8_bytes", "required-only context exceeds byte budget"))
        else:
            issues.append(_issue("OPTIONAL_UNIT_PRUNING_REQUIRED", "request.adapted_context.budget.max_utf8_bytes", "optional whole-unit pruning is required before validation"))
    max_tokens = budget.get("max_prompt_tokens_or_null")
    token_count = envelope.get("prompt_token_count_or_null")
    if max_tokens is not None and token_count is not None and token_count > max_tokens:
        if required_only:
            issues.append(_issue("REQUIRED_ONLY_BUDGET_OVERFLOW", "request.adapted_context.budget.max_prompt_tokens_or_null", "required-only context exceeds token budget"))
        else:
            issues.append(_issue("OPTIONAL_UNIT_PRUNING_REQUIRED", "request.adapted_context.budget.max_prompt_tokens_or_null", "optional whole-unit pruning is required before validation"))
    return issues, computed


def _validate_artifact(session_root: Path, request: dict[str, Any], envelope: dict[str, Any]) -> list[ValidationIssue]:
    adapted = request["adapted_context"]
    target, issues = _safe_envelope_path(session_root, request["session_id"], adapted["envelope_relative_path"])
    if issues:
        return issues
    assert target is not None
    if not target.is_file():
        return [_issue("ENVELOPE_ARTIFACT_MISSING", "request.adapted_context.envelope_relative_path", "managed envelope artifact is missing")]
    raw = target.read_bytes()
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError:
        return [_issue("ENVELOPE_NOT_UTF8", "request.adapted_context.envelope_relative_path", "envelope artifact must be UTF-8")]
    expected_raw = canonical_json_bytes(envelope)
    if raw != expected_raw:
        return [_issue("ENVELOPE_NOT_CANONICAL", "request.adapted_context.envelope_relative_path", "artifact bytes must equal canonical envelope bytes")]
    actual_hash = hashlib.sha256(raw).hexdigest()
    if adapted.get("envelope_sha256") != actual_hash:
        return [_issue("ENVELOPE_HASH_MISMATCH", "request.adapted_context.envelope_sha256", "artifact hash mismatch")]
    return []


def _validate_result(request: dict[str, Any], envelope: dict[str, Any] | None, result: dict[str, Any], probe: dict[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if result.get("session_id") != request.get("session_id"):
        issues.append(_issue("SESSION_BINDING_MISMATCH", "result.session_id", "result session must match request session"))
    if result.get("request_sha256") != canonical_sha256(request):
        issues.append(_issue("REQUEST_HASH_MISMATCH", "result.request_sha256", "result is not bound to request"))
    if result.get("result_sha256") != hash_without_field(result, "result_sha256"):
        issues.append(_issue("RESULT_HASH_MISMATCH", "result.result_sha256", "result self-hash mismatch"))
    receipt = result.get("backend_receipt", {})
    expected_context_hash = envelope.get("context_sha256") if envelope is not None else None
    receipt_checks = {
        "adapter_id": request.get("backend", {}).get("adapter_id"),
        "adapter_version": request.get("backend", {}).get("adapter_version"),
        "capability_probe_sha256": canonical_sha256(probe),
        "task_channel_sha256": request.get("task", {}).get("utf8_sha256"),
        "context_channel_sha256_or_null": expected_context_hash,
    }
    for field, expected in receipt_checks.items():
        if receipt.get(field) != expected:
            issues.append(_issue("BACKEND_RECEIPT_MISMATCH", f"result.backend_receipt.{field}", f"expected {expected!r}"))

    mode = request.get("mode")
    if mode == TRANSPORT_MODE:
        if result.get("transport_status") == "PASS":
            required = {
                "task_occurrence_count": 1,
                "context_injection_attempt_count": 1,
                "context_injection_count": 1,
                "child_spawned": True,
                "integrity_result": "PASS",
                "permission_result": "PASS",
                "budget_result": "PASS",
                "context_cleanup_result": "PASS",
            }
            for field, expected in required.items():
                if result.get(field) != expected:
                    issues.append(_issue("RESULT_PASS_INVARIANT_FAILED", f"result.{field}", f"PASS requires {expected!r}"))
            if receipt.get("task_context_channels_separate") is not True:
                issues.append(_issue("RESULT_PASS_INVARIANT_FAILED", "result.backend_receipt.task_context_channels_separate", "PASS requires separate task and context channels"))
            if result.get("failure_code_or_null") is not None or result.get("quarantine_paths"):
                issues.append(_issue("RESULT_PASS_INVARIANT_FAILED", "result", "PASS cannot include failure or quarantine"))
        if result.get("task_occurrence_count") not in {0, 1}:
            issues.append(_issue("TASK_OCCURRENCE_INVALID", "result.task_occurrence_count", "task occurrence count must be 0 or 1"))
        for field in ("context_injection_attempt_count", "context_injection_count"):
            if result.get(field) not in {0, 1}:
                issues.append(_issue("INJECTION_COUNT_INVALID", f"result.{field}", "injection count must be 0 or 1"))
    else:
        if result.get("context_injection_attempt_count") != 0 or result.get("context_injection_count") != 0:
            issues.append(_issue("CURRENT_ONLY_INJECTION_FORBIDDEN", "result", "CURRENT_ONLY requires zero injections"))

    if result.get("transport_status") == "PASS":
        for field in ("integrity_result", "permission_result", "budget_result", "context_cleanup_result", "bridge_cleanup_result"):
            if result.get(field) == "UNKNOWN":
                issues.append(_issue("UNKNOWN_CANNOT_PASS", f"result.{field}", "UNKNOWN cannot be converted to PASS"))

    cleanup_failed = result.get("context_cleanup_result") == "FAIL" or result.get("bridge_cleanup_result") == "FAIL"
    if cleanup_failed:
        if result.get("transport_status") != "QUARANTINED" or result.get("failure_code_or_null") != "CLEANUP_FAILED" or not result.get("quarantine_paths"):
            issues.append(_issue("CLEANUP_FAILURE_NOT_QUARANTINED", "result", "cleanup failure requires QUARANTINED status, failure code, and path"))
    elif result.get("transport_status") != "PASS":
        issues.append(_issue("BACKEND_RESULT_NOT_PASS", "result.transport_status", "a non-PASS backend result cannot be converted to validator PASS"))
    return issues


def _terminal_status(issues: list[ValidationIssue]) -> str:
    if not issues:
        return "PASS"
    codes = {issue.code for issue in issues}
    if "CLEANUP_FAILURE_NOT_QUARANTINED" in codes:
        return "FAIL"
    if "REQUIRED_ONLY_BUDGET_OVERFLOW" in codes:
        return "BUDGET_BLOCKED"
    if "STALE_CACHE" in codes and codes <= {"STALE_CACHE"}:
        return "INVALIDATED"
    return "FAIL"


def validate_contract_bundle(
    *,
    request: dict[str, Any],
    result: dict[str, Any],
    probe: dict[str, Any],
    expected_task_text: str,
    session_root: Path,
    definition: dict[str, Any] | None = None,
    envelope: dict[str, Any] | None = None,
    schema_root: Path | None = None,
    validation_time_utc: str = "2030-01-01T00:00:00Z",
) -> ValidationReport:
    """Validate a complete fake/offline launch contract without executing it."""
    computed: dict[str, Any] = {"validator_version": VALIDATOR_VERSION}
    try:
        schemas = load_schemas(schema_root)
        now = _parse_utc(validation_time_utc)
    except (SchemaDefinitionError, ValueError) as exc:
        return _report("FAIL", [_issue("VALIDATOR_CONFIGURATION_INVALID", "$", str(exc))], computed)

    schema_issues: list[ValidationIssue] = []
    for name, document in (("request", request), ("result", result), ("probe", probe)):
        schema_issues.extend(_schema_issues(name, document, schemas[name]))
    mode = request.get("mode")
    if mode == TRANSPORT_MODE:
        if definition is None:
            schema_issues.append(_issue("SCHEMA_INVALID", "definition", "context mode requires definition"))
        else:
            schema_issues.extend(_schema_issues("definition", definition, schemas["definition"]))
        if envelope is None:
            schema_issues.append(_issue("SCHEMA_INVALID", "envelope", "context mode requires envelope"))
        else:
            schema_issues.extend(_schema_issues("envelope", envelope, schemas["envelope"]))
    if schema_issues:
        return _report("FAIL", schema_issues, computed)

    if mode == "CURRENT_ONLY":
        issues: list[ValidationIssue] = []
        if request.get("adapted_context") is not None or definition is not None or envelope is not None:
            issues.append(_issue("CURRENT_ONLY_CONTEXT_FORBIDDEN", "request.adapted_context", "CURRENT_ONLY must not carry adapted context"))
        issues.extend(_validate_task_boundary(request, None, expected_task_text))
        issues.extend(_validate_result(request, None, result, probe))
        return _report(_terminal_status(issues), issues, computed)

    if mode != TRANSPORT_MODE:
        return _report("FAIL", [_issue("TRANSPORT_MODE_INVALID", "request.mode", "unsupported transport mode")], computed)
    assert definition is not None and envelope is not None

    probe_issues = _validate_probe(probe, request, now)
    if probe_issues:
        return _report("FAIL", probe_issues, computed)

    task_issues = _validate_task_boundary(request, envelope, expected_task_text)
    if task_issues:
        return _report("FAIL", task_issues, computed)

    definition_issues = _validate_definition(definition)
    stale_only = definition_issues and all(issue.code == "STALE_CACHE" for issue in definition_issues)
    if definition_issues:
        return _report("INVALIDATED" if stale_only else "FAIL", definition_issues, computed)

    permission_issues, permission_computed = _validate_permission_decision(definition, request)
    computed.update(permission_computed)
    if permission_issues:
        return _report("FAIL", permission_issues, computed)

    envelope_issues, envelope_computed = _validate_envelope_definition(definition, envelope, request)
    computed.update(envelope_computed)
    if envelope_issues:
        return _report(_terminal_status(envelope_issues), envelope_issues, computed)

    artifact_issues = _validate_artifact(session_root, request, envelope)
    if artifact_issues:
        return _report("FAIL", artifact_issues, computed)

    result_issues = _validate_result(request, envelope, result, probe)
    if result.get("context_cleanup_result") == "FAIL" or result.get("bridge_cleanup_result") == "FAIL":
        if not result_issues and result.get("transport_status") == "QUARANTINED":
            return _report("QUARANTINED", [], computed)
    return _report(_terminal_status(result_issues), result_issues, computed)
