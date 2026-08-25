"""Approved-only deterministic adapted capability selector in shadow mode.

This module consumes existing Router and activation results as immutable inputs.
It never invokes, rescales, or mutates those components and never connects its
selection to a launcher, transport, backend, model, or external service.
"""

from __future__ import annotations

import copy
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
CONTEXT_VALIDATOR_DIR = HERE.parent / "context-contract" / "validator"
if str(CONTEXT_VALIDATOR_DIR) not in sys.path:
    sys.path.insert(0, str(CONTEXT_VALIDATOR_DIR))

from context_contract import (  # noqa: E402
    GATE_RANK,
    VALIDATOR_VERSION,
    canonical_json_bytes,
    canonical_sha256,
    compute_cache_key,
    definition_content_bytes,
    definition_content_sha256,
    hash_without_field,
    load_schemas,
    strongest_permission_gate,
    utf8_sha256,
)
from schema_validation import SchemaDefinitionError, validate_instance  # noqa: E402

from budget_planner import BUDGET_PLANNER_VERSION, contains_phrase, plan_budget  # noqa: E402


SELECTOR_VERSION = "v8.4-adapted-selector-1"
POLICY_VERSION = "v8.4-selector-budget-policy-1"
GATE_ORDER = (
    "approval",
    "freshness",
    "task_applicability",
    "exclusion",
    "overlap",
    "permission",
    "quality_evidence",
    "budget",
    "cardinality",
)
TERMINAL_GATE_STATUSES = {"PASS", "FAIL", "NOT_EVALUATED"}


@dataclass(frozen=True)
class SelectionIssue:
    code: str
    path: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "path": self.path, "message": self.message}


def load_json_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid JSON object {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"JSON document must be an object: {path}")
    return value


def load_policy(path: Path | None = None) -> dict[str, Any]:
    return load_json_object(path or HERE / "policy" / "selector-budget-policy-v1.json")


def repository_shadow_inputs(repo_root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Load immutable V8.4-004 DRAFTs as a non-selectable shadow catalog."""
    candidates: list[dict[str, Any]] = []
    metadata: dict[str, Any] = {}
    for candidate_id in ("kd-sympy", "kd-citation-management"):
        root = repo_root / "evaluation" / "external-skills" / "adapted-contexts" / candidate_id
        definition = load_json_object(root / "definition.json")
        evidence = load_json_object(root / "compile-evidence.json")
        required_unit_ids = [unit["unit_id"] for unit in definition["knowledge_units"] if unit["required"]]
        candidates.append(
            {
                "candidate_id": candidate_id,
                "definition": definition,
                "approval": {
                    "status": evidence["review_state"],
                    "approval_ref_or_null": None,
                    "approved_definition_sha256_or_null": None,
                    "required_unit_ids": required_unit_ids,
                },
                "quality_evidence": {
                    "schema_pass": definition["verification"]["schema_pass"],
                    "provenance_pass": definition["verification"]["provenance_pass"],
                    "safety_pass": definition["verification"]["safety_pass"],
                    "fixture_pass": definition["verification"]["fixture_pass"],
                    "holdout_pass": definition["verification"]["holdout_pass"],
                    "evidence_refs": definition["verification"]["fixture_evidence"] + definition["verification"]["holdout_evidence"],
                    "definition_sha256": canonical_sha256(definition),
                },
            }
        )
        metadata[candidate_id] = {
            "expected_snapshot_sha256": definition["source"]["snapshot_sha256"],
            "expected_definition_content_sha256": definition["content_sha256"],
            "expected_cache_key": definition["cache_key"],
            "expected_version": definition["version"],
            "satisfied_prerequisites": list(definition["applicability"]["prerequisites"]),
            "overlap_capability_ids": [],
            "capability_delta": {
                "status": "NOT_REQUIRED",
                "evidence_refs": [],
            },
        }
    catalog = {
        "schema_version": 1,
        "catalog_id": "v8.4-004-draft-shadow-input",
        "catalog_revision": canonical_sha256([candidate["definition"]["cache_key"] for candidate in candidates]),
        "candidates": candidates,
        "approved_compositions": [],
    }
    return catalog, metadata


def _gate_records() -> list[dict[str, Any]]:
    return [
        {
            "order": index,
            "gate": gate,
            "status": "NOT_EVALUATED",
            "reason_codes": [],
            "details": {},
        }
        for index, gate in enumerate(GATE_ORDER, start=1)
    ]


def _set_gate(
    gates: list[dict[str, Any]],
    gate_name: str,
    status: str,
    reason_codes: list[str] | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    if status not in TERMINAL_GATE_STATUSES:
        raise ValueError(f"invalid gate status: {status}")
    gate = next(item for item in gates if item["gate"] == gate_name)
    gate["status"] = status
    gate["reason_codes"] = sorted(set(reason_codes or []))
    gate["details"] = copy.deepcopy(details or {})


def _selected_router_ids(router_result: dict[str, Any]) -> list[str]:
    selected = router_result.get("selected", [])
    return sorted(str(item.get("id")) for item in selected if isinstance(item, dict) and item.get("id"))


def _activation_permissions(activation_plan: dict[str, Any]) -> list[str]:
    permissions: set[str] = set()
    for plan in activation_plan.get("plans", []):
        permissions.update(plan.get("permissions", []))
    return sorted(permissions)


def _activation_gates(activation_plan: dict[str, Any]) -> list[str]:
    decisions = [str(plan.get("decision")) for plan in activation_plan.get("plans", [])]
    return sorted(set(decision for decision in decisions if decision in GATE_RANK))


def _validate_global_inputs(
    *,
    task_text: str,
    router_result: dict[str, Any],
    activation_plan: dict[str, Any],
    catalog: dict[str, Any],
    candidate_metadata: dict[str, Any],
    permission_state: dict[str, Any],
    policy: dict[str, Any],
) -> list[SelectionIssue]:
    issues: list[SelectionIssue] = []
    if not isinstance(task_text, str) or not task_text.strip():
        issues.append(SelectionIssue("TASK_INVALID", "task_text", "non-empty task text is required"))
    if router_result.get("task") != task_text:
        issues.append(SelectionIssue("ROUTER_TASK_MISMATCH", "router_result.task", "Router task must equal the selector task"))
    if activation_plan.get("task") != task_text:
        issues.append(SelectionIssue("ACTIVATION_TASK_MISMATCH", "activation_plan.task", "activation task must equal the selector task"))
    if activation_plan.get("side_effects_executed") is not False:
        issues.append(SelectionIssue("ACTIVATION_INPUT_INVALID", "activation_plan.side_effects_executed", "shadow selector requires a side-effect-free plan"))
    if policy.get("policy_version") != POLICY_VERSION or policy.get("selector_version") != SELECTOR_VERSION:
        issues.append(SelectionIssue("SELECTOR_POLICY_UNSUPPORTED", "policy", "policy/selector version mismatch"))
    if policy.get("budget_planner_version") != BUDGET_PLANNER_VERSION:
        issues.append(SelectionIssue("BUDGET_POLICY_UNSUPPORTED", "policy.budget_planner_version", "budget planner version mismatch"))
    if tuple(policy.get("gate_order", [])) != GATE_ORDER:
        issues.append(SelectionIssue("GATE_ORDER_INVALID", "policy.gate_order", "gate order differs from the frozen contract"))
    risk_rank = policy.get("risk_rank", {})
    candidate_risk = policy.get("candidate_risk", {})
    for candidate_id in policy.get("allowed_candidates", []):
        if candidate_risk.get(candidate_id) not in risk_rank:
            issues.append(SelectionIssue("RISK_CLASSIFICATION_UNKNOWN", f"policy.candidate_risk.{candidate_id}", "allowed candidate needs a known risk class"))
    for field in ("fuzzy_matching", "runtime_integration", "external_access", "model_calls"):
        if policy.get(field) is not False:
            issues.append(SelectionIssue("SHADOW_POLICY_VIOLATION", f"policy.{field}", f"{field} must be false"))
    if not isinstance(catalog.get("catalog_id"), str) or not catalog.get("catalog_id") or not isinstance(catalog.get("catalog_revision"), str) or not catalog.get("catalog_revision"):
        issues.append(SelectionIssue("CATALOG_MALFORMED", "catalog", "catalog id and revision are required"))
    candidates = catalog.get("candidates")
    if not isinstance(candidates, list):
        issues.append(SelectionIssue("CATALOG_MALFORMED", "catalog.candidates", "candidate list is required"))
    else:
        candidate_ids = [candidate.get("candidate_id") for candidate in candidates if isinstance(candidate, dict)]
        if len(candidate_ids) != len(candidates) or len(candidate_ids) != len(set(candidate_ids)):
            issues.append(SelectionIssue("AMBIGUOUS_SELECTION_INPUT", "catalog.candidates", "candidate IDs must be present and unique"))
        missing_metadata = sorted(set(candidate_ids) - set(candidate_metadata))
        if missing_metadata:
            issues.append(SelectionIssue("CANDIDATE_METADATA_MISSING", "candidate_metadata", f"missing metadata for {missing_metadata}"))

    actual_permissions = _activation_permissions(activation_plan)
    reported_permissions = permission_state.get("current_permissions")
    if reported_permissions != actual_permissions:
        issues.append(SelectionIssue("PERMISSION_STATE_MISMATCH", "permission_state.current_permissions", f"expected activation permission union {actual_permissions}"))
    approved_gates = permission_state.get("approved_gates")
    if not isinstance(approved_gates, list) or any(gate not in GATE_RANK for gate in approved_gates):
        issues.append(SelectionIssue("PERMISSION_STATE_INVALID", "permission_state.approved_gates", "approved gates must be a known gate list"))
    if not isinstance(permission_state.get("approval_refs"), list):
        issues.append(SelectionIssue("PERMISSION_STATE_INVALID", "permission_state.approval_refs", "approval refs list is required"))
    return issues


def _schema_errors(definition: Any) -> list[str]:
    try:
        schema = load_schemas()["definition"]
    except SchemaDefinitionError as exc:
        return [f"schema configuration: {exc}"]
    return [f"{error.path}: {error.message}" for error in validate_instance(definition, schema)]


def _strongest_named_gate(gates: list[str]) -> str:
    unknown = [gate for gate in gates if gate not in GATE_RANK]
    if unknown:
        raise ValueError(f"unknown gate(s): {sorted(set(unknown))}")
    return max(gates or ["NONE"], key=lambda gate: GATE_RANK[gate])


def _evaluate_candidate(
    *,
    task_text: str,
    entry: dict[str, Any],
    metadata: dict[str, Any],
    router_result: dict[str, Any],
    activation_plan: dict[str, Any],
    permission_state: dict[str, Any],
    policy: dict[str, Any],
) -> dict[str, Any]:
    candidate_id = str(entry.get("candidate_id"))
    definition = entry.get("definition")
    gates = _gate_records()
    result: dict[str, Any] = {
        "candidate_id": candidate_id,
        "definition_id_or_null": definition.get("adapted_capability_id") if isinstance(definition, dict) else None,
        "definition_version_or_null": definition.get("version") if isinstance(definition, dict) else None,
        "definition_sha256_or_null": canonical_sha256(definition) if isinstance(definition, dict) else None,
        "gates": gates,
        "ranking": None,
        "permission": None,
        "budget": None,
        "eligible_before_cardinality": False,
    }

    allowed = candidate_id in policy.get("allowed_candidates", [])
    schema_errors = _schema_errors(definition) if isinstance(definition, dict) else ["definition must be an object"]
    approval = entry.get("approval", {})
    approval_hash = approval.get("approved_definition_sha256_or_null")
    approval_ok = (
        allowed
        and not schema_errors
        and definition.get("candidate_id") == candidate_id
        and definition.get("status") == "APPROVED"
        and approval.get("status") == "APPROVED"
        and isinstance(approval.get("approval_ref_or_null"), str)
        and bool(approval.get("approval_ref_or_null"))
        and approval_hash == canonical_sha256(definition)
    )
    approval_reasons: list[str] = []
    if not allowed:
        approval_reasons.append("UNAUTHORIZED_CANDIDATE")
    if schema_errors:
        approval_reasons.append("INVALID_COMPILER_OUTPUT")
    if isinstance(definition, dict) and definition.get("candidate_id") != candidate_id:
        approval_reasons.append("INVALID_COMPILER_OUTPUT")
    if isinstance(definition, dict) and definition.get("status") != "APPROVED":
        approval_reasons.append("DEFINITION_NOT_APPROVED")
    if approval.get("status") != "APPROVED" or approval_hash is None:
        approval_reasons.append("APPROVAL_EVIDENCE_MISSING")
    _set_gate(gates, "approval", "PASS" if approval_ok else "FAIL", approval_reasons, {"schema_errors": schema_errors, "approval_ref_or_null": approval.get("approval_ref_or_null")})
    if not approval_ok:
        return result

    source = definition["source"]
    unit_ids = [unit.get("unit_id") for unit in definition["knowledge_units"]]
    unit_hashes_valid = all(
        unit.get("content_sha256")
        == canonical_sha256({key: value for key, value in unit.items() if key != "content_sha256"})
        for unit in definition["knowledge_units"]
    )
    freshness_checks = {
        "snapshot_sha256": source.get("snapshot_sha256") == metadata.get("expected_snapshot_sha256"),
        "content_sha256": definition.get("content_sha256") == metadata.get("expected_definition_content_sha256") == definition_content_sha256(definition),
        "cache_key": definition.get("cache_key") == metadata.get("expected_cache_key") == compute_cache_key(definition),
        "version": definition.get("version") == metadata.get("expected_version"),
        "utf8_bytes": definition.get("budget", {}).get("utf8_bytes") == definition_content_bytes(definition),
        "unit_hashes": unit_hashes_valid,
        "unit_ids_unique": len(unit_ids) == len(set(unit_ids)),
        "validator_version": policy.get("definition_validator_version") == VALIDATOR_VERSION,
    }
    freshness_ok = all(freshness_checks.values())
    _set_gate(gates, "freshness", "PASS" if freshness_ok else "FAIL", [] if freshness_ok else ["STALE_CANDIDATE"], freshness_checks)
    if not freshness_ok:
        return result

    applicability = definition["applicability"]
    matched_domains = sorted(domain for domain in applicability["domains"] if contains_phrase(task_text, domain))
    matched_triggers = sorted(trigger for trigger in applicability["task_triggers"] if contains_phrase(task_text, trigger))
    required_prerequisites = set(applicability["prerequisites"])
    satisfied_prerequisites = set(metadata.get("satisfied_prerequisites", []))
    missing_prerequisites = sorted(required_prerequisites - satisfied_prerequisites)
    applicability_ok = bool(matched_domains or matched_triggers) and not missing_prerequisites
    _set_gate(
        gates,
        "task_applicability",
        "PASS" if applicability_ok else "FAIL",
        [] if applicability_ok else ["TASK_NOT_APPLICABLE" if not (matched_domains or matched_triggers) else "PREREQUISITE_EVIDENCE_MISSING"],
        {
            "matched_domains": matched_domains,
            "matched_triggers": matched_triggers,
            "missing_prerequisites": missing_prerequisites,
        },
    )
    if not applicability_ok:
        return result

    matched_exclusions = sorted(exclusion for exclusion in applicability["exclusions"] if contains_phrase(task_text, exclusion))
    exclusion_ok = not matched_exclusions
    _set_gate(gates, "exclusion", "PASS" if exclusion_ok else "FAIL", [] if exclusion_ok else ["EXCLUSION_MATCH"], {"matched_exclusions": matched_exclusions})
    if not exclusion_ok:
        return result

    current_ids = sorted(set(_selected_router_ids(router_result)) | {str(plan.get("id")) for plan in activation_plan.get("plans", []) if plan.get("id")})
    declared_overlap = set(metadata.get("overlap_capability_ids", []))
    matched_overlap = sorted(set(current_ids) & declared_overlap)
    delta = metadata.get("capability_delta", {})
    delta_ok = not matched_overlap or (
        delta.get("status") == "PASS"
        and isinstance(delta.get("evidence_refs"), list)
        and bool(delta.get("evidence_refs"))
    )
    _set_gate(gates, "overlap", "PASS" if delta_ok else "FAIL", [] if delta_ok else ["OVERLAP_UNRESOLVED"], {"current_capability_ids": current_ids, "matched_overlap_ids": matched_overlap, "capability_delta_status": delta.get("status"), "capability_delta_evidence": delta.get("evidence_refs", [])})
    if not delta_ok:
        return result

    current_permissions = _activation_permissions(activation_plan)
    definition_permissions = definition["permissions"]
    source_permissions = definition_permissions["source_permissions"]
    retained_permissions = definition_permissions["retained_permissions"]
    removed_permissions = definition_permissions["removed_permissions"]
    permission_reasons: list[str] = []
    try:
        effective_permissions, permission_gate = strongest_permission_gate(current_permissions + source_permissions + retained_permissions)
        _, definition_gate_expected = strongest_permission_gate(source_permissions + retained_permissions)
        strongest_gate = _strongest_named_gate([permission_gate, definition_permissions["effective_gate"]] + _activation_gates(activation_plan))
    except ValueError as exc:
        effective_permissions = []
        strongest_gate = "HUMAN_GATE_REQUIRED"
        permission_reasons.append("PERMISSION_UNKNOWN")
        permission_error_or_null: str | None = str(exc)
    else:
        permission_error_or_null = None
        source_permission_set = set(source_permissions)
        retained_permission_set = set(retained_permissions)
        removed_permission_set = set(removed_permissions)
        if (
            retained_permission_set & removed_permission_set
            or retained_permission_set | removed_permission_set != source_permission_set
        ):
            permission_reasons.append("PERMISSION_PARTITION_MISMATCH")
        if definition_permissions["effective_gate"] != definition_gate_expected:
            permission_reasons.append("PERMISSION_DOWNGRADE")
    approved_gates = set(policy.get("auto_satisfied_gates", [])) | set(permission_state.get("approved_gates", []))
    approval_refs = permission_state.get("approval_refs", [])
    if strongest_gate not in approved_gates:
        permission_reasons.append("PERMISSION_APPROVAL_REQUIRED")
    if strongest_gate not in policy.get("auto_satisfied_gates", []) and not approval_refs:
        permission_reasons.append("PERMISSION_APPROVAL_REFERENCE_MISSING")
    reported_expected = permission_state.get("expected_effective_gates", {}).get(candidate_id)
    if reported_expected is not None and reported_expected != strongest_gate:
        permission_reasons.append("PERMISSION_DOWNGRADE")
    permission_ok = not permission_reasons
    permission_record = {
        "current_playbook_permissions": current_permissions,
        "adapted_source_permissions": source_permissions,
        "adapted_retained_permissions": retained_permissions,
        "adapted_removed_permissions": removed_permissions,
        "effective_permissions": effective_permissions,
        "definition_effective_gate": definition_permissions["effective_gate"],
        "strongest_gate": strongest_gate,
        "approval_refs": approval_refs,
        "error_or_null": permission_error_or_null,
    }
    result["permission"] = permission_record
    _set_gate(gates, "permission", "PASS" if permission_ok else "FAIL", permission_reasons, permission_record)
    if not permission_ok:
        return result

    quality = entry.get("quality_evidence", {})
    quality_fields = ("schema_pass", "provenance_pass", "safety_pass", "fixture_pass", "holdout_pass")
    quality_checks = {field: quality.get(field) == "PASS" and definition["verification"].get(field) == "PASS" for field in quality_fields}
    quality_refs = quality.get("evidence_refs")
    quality_checks["evidence_refs"] = isinstance(quality_refs, list) and bool(quality_refs) and all(isinstance(ref, str) and ref for ref in quality_refs)
    quality_checks["definition_hash"] = quality.get("definition_sha256") == canonical_sha256(definition)
    quality_ok = all(quality_checks.values())
    _set_gate(gates, "quality_evidence", "PASS" if quality_ok else "FAIL", [] if quality_ok else ["QUALITY_EVIDENCE_MISSING"], quality_checks)
    if not quality_ok:
        return result

    required_ids = set(approval.get("required_unit_ids", []))
    present_units = {unit["unit_id"]: unit for unit in definition["knowledge_units"]}
    required_integrity_ok = bool(required_ids) and required_ids.issubset(present_units) and all(present_units[unit_id]["required"] is True for unit_id in required_ids)
    actual_required_ids = {unit["unit_id"] for unit in definition["knowledge_units"] if unit["required"] is True}
    if required_ids != actual_required_ids:
        required_integrity_ok = False
    if not required_integrity_ok:
        _set_gate(gates, "budget", "FAIL", ["REQUIRED_UNIT_MISSING"], {"approved_required_unit_ids": sorted(required_ids), "actual_required_unit_ids": sorted(actual_required_ids)})
        return result

    budget_plan = plan_budget(task_text=task_text, definitions=[definition], policy=policy)
    result["budget"] = budget_plan
    budget_ok = budget_plan["status"] == "READY"
    budget_reason = [] if budget_ok else (["REQUIRED_ONLY_BUDGET_OVERFLOW"] if budget_plan["status"] == "BUDGET_BLOCKED" else ["BUDGET_POLICY_INVALID"])
    _set_gate(gates, "budget", "PASS" if budget_ok else "FAIL", budget_reason, {"status": budget_plan["status"], "total_utf8_bytes": budget_plan["total_utf8_bytes"], "total_utf8_limit": budget_plan["total_utf8_limit"]})
    if not budget_ok:
        return result

    risk = policy["candidate_risk"].get(candidate_id)
    risk_rank = policy["risk_rank"].get(risk)
    if risk_rank is None:
        _set_gate(gates, "budget", "FAIL", ["RISK_CLASSIFICATION_UNKNOWN"], {"risk": risk})
        return result
    specificity = len(matched_triggers) * 100 + len(matched_domains) * 10
    result["ranking"] = {
        "specificity": specificity,
        "matched_trigger_count": len(matched_triggers),
        "matched_domain_count": len(matched_domains),
        "context_utf8_bytes": budget_plan["total_utf8_bytes"],
        "risk": risk,
        "risk_rank": risk_rank,
        "stable_id": candidate_id,
        "rank_key": [-specificity, budget_plan["total_utf8_bytes"], risk_rank, candidate_id],
    }
    result["eligible_before_cardinality"] = True
    return result


def _approved_composition(
    candidate_ids: list[str],
    catalog: dict[str, Any],
    policy: dict[str, Any],
) -> dict[str, Any] | None:
    wanted = sorted(candidate_ids)
    policy_records = [record for record in policy.get("approved_compositions", []) if sorted(record.get("candidate_ids", [])) == wanted and record.get("status") == "APPROVED" and record.get("evidence_refs")]
    catalog_records = [record for record in catalog.get("approved_compositions", []) if sorted(record.get("candidate_ids", [])) == wanted and record.get("status") == "APPROVED" and record.get("evidence_refs")]
    if len(policy_records) != 1 or len(catalog_records) != 1:
        return None
    if canonical_sha256(policy_records[0]) != catalog_records[0].get("policy_record_sha256"):
        return None
    return catalog_records[0]


def _empty_budget(policy: dict[str, Any]) -> dict[str, Any]:
    budget = policy.get("budget", {})
    result = {
        "planner_version": BUDGET_PLANNER_VERSION,
        "status": "NOT_REQUIRED",
        "issues": [],
        "per_capability": [],
        "selected_unit_ids": [],
        "excluded_units": [],
        "pruning_sequence": [],
        "total_utf8_bytes": 0,
        "total_utf8_limit": budget.get("total_utf8_bytes"),
        "tokenizer_id_or_null": budget.get("tokenizer_id_or_null"),
        "token_count_or_null": budget.get("token_count_or_null"),
        "unavailable_reason_or_null": budget.get("unavailable_reason_or_null"),
        "context_sha256": utf8_sha256(""),
        "budget_plan_sha256": "0" * 64,
    }
    result["budget_plan_sha256"] = hash_without_field(result, "budget_plan_sha256")
    return result


def select_adapted_context(
    *,
    task_text: str,
    router_result: dict[str, Any],
    activation_plan: dict[str, Any],
    catalog: dict[str, Any],
    candidate_metadata: dict[str, Any],
    permission_state: dict[str, Any],
    policy: dict[str, Any],
) -> dict[str, Any]:
    """Select approved definitions while preserving all current-path inputs."""
    inputs = {
        "task_text": task_text,
        "router_result": router_result,
        "activation_plan": activation_plan,
        "catalog": catalog,
        "candidate_metadata": candidate_metadata,
        "permission_state": permission_state,
        "policy": policy,
        "selector_version": SELECTOR_VERSION,
    }
    input_sha256 = canonical_sha256(inputs)
    issues = _validate_global_inputs(
        task_text=task_text,
        router_result=router_result,
        activation_plan=activation_plan,
        catalog=catalog,
        candidate_metadata=candidate_metadata,
        permission_state=permission_state,
        policy=policy,
    )

    candidates: list[dict[str, Any]] = []
    if not issues:
        for entry in catalog["candidates"]:
            candidates.append(
                _evaluate_candidate(
                    task_text=task_text,
                    entry=entry,
                    metadata=candidate_metadata[entry["candidate_id"]],
                    router_result=router_result,
                    activation_plan=activation_plan,
                    permission_state=permission_state,
                    policy=policy,
                )
            )

    ranked = sorted(
        (candidate for candidate in candidates if candidate["eligible_before_cardinality"]),
        key=lambda candidate: tuple(candidate["ranking"]["rank_key"]),
    )
    selected: list[dict[str, Any]] = []
    forced_decision: str | None = None
    explicit_multi_domain = any(contains_phrase(task_text, phrase) for phrase in policy.get("explicit_multi_domain_phrases", []))

    if issues:
        forced_decision = "HUMAN_GATE_REQUIRED"
    elif explicit_multi_domain and len(ranked) >= 2:
        proposed = ranked[: policy["approved_composite_max_capabilities"]]
        composition = _approved_composition([candidate["candidate_id"] for candidate in proposed], catalog, policy)
        if composition is None:
            forced_decision = "HUMAN_GATE_REQUIRED"
            for candidate in ranked:
                _set_gate(candidate["gates"], "cardinality", "FAIL", ["MULTI_CAPABILITY_NOT_APPROVED"], {"explicit_multi_domain": True})
        else:
            selected = proposed
            for candidate in selected:
                _set_gate(candidate["gates"], "cardinality", "PASS", [], {"composition_id": composition.get("composition_id"), "evidence_refs": composition.get("evidence_refs")})
            for candidate in ranked[len(selected) :]:
                _set_gate(candidate["gates"], "cardinality", "FAIL", ["CARDINALITY_LIMIT"], {"limit": len(selected)})
    elif ranked:
        selected = ranked[: policy["default_max_capabilities"]]
        for candidate in selected:
            _set_gate(candidate["gates"], "cardinality", "PASS", [], {"limit": policy["default_max_capabilities"]})
        for candidate in ranked[len(selected) :]:
            _set_gate(candidate["gates"], "cardinality", "FAIL", ["CARDINALITY_LIMIT"], {"limit": policy["default_max_capabilities"]})

    combined_budget = _empty_budget(policy)
    if selected:
        definition_by_id = {entry["candidate_id"]: entry["definition"] for entry in catalog["candidates"]}
        selected_definitions = [definition_by_id[candidate["candidate_id"]] for candidate in selected]
        combined_budget = plan_budget(task_text=task_text, definitions=selected_definitions, policy=policy)
        if combined_budget["status"] != "READY":
            forced_decision = "BUDGET_BLOCKED" if combined_budget["status"] == "BUDGET_BLOCKED" else "HUMAN_GATE_REQUIRED"
            for candidate in selected:
                _set_gate(candidate["gates"], "budget", "FAIL", ["REQUIRED_ONLY_BUDGET_OVERFLOW" if forced_decision == "BUDGET_BLOCKED" else "BUDGET_POLICY_INVALID"], {"combined_status": combined_budget["status"]})
                _set_gate(candidate["gates"], "cardinality", "NOT_EVALUATED")
            selected = []

    selected_ids = [candidate["candidate_id"] for candidate in selected]
    exclusion_records: list[dict[str, Any]] = []
    for candidate in candidates:
        if candidate["candidate_id"] in selected_ids:
            continue
        failed_gates = [gate for gate in candidate["gates"] if gate["status"] == "FAIL"]
        exclusion_records.append(
            {
                "candidate_id": candidate["candidate_id"],
                "reasons": sorted({reason for gate in failed_gates for reason in gate["reason_codes"]}) or ["NOT_SELECTED"],
                "failed_gate_or_null": failed_gates[0]["gate"] if failed_gates else None,
            }
        )

    permission_failures = [candidate for candidate in candidates if next(gate for gate in candidate["gates"] if gate["gate"] == "permission")["status"] == "FAIL"]
    budget_failures = [candidate for candidate in candidates if next(gate for gate in candidate["gates"] if gate["gate"] == "budget")["reason_codes"] == ["REQUIRED_ONLY_BUDGET_OVERFLOW"]]
    invalid_compiler_outputs = [
        candidate
        for candidate in candidates
        if "INVALID_COMPILER_OUTPUT"
        in next(gate for gate in candidate["gates"] if gate["gate"] == "approval")["reason_codes"]
    ]
    if forced_decision is not None:
        final_decision = forced_decision
    elif selected:
        final_decision = "ADAPTED_SELECTED"
    elif budget_failures:
        final_decision = "BUDGET_BLOCKED"
    elif permission_failures:
        final_decision = "HUMAN_GATE_REQUIRED"
    elif invalid_compiler_outputs:
        final_decision = "HUMAN_GATE_REQUIRED"
    elif activation_plan.get("result") == "NO_ACTION":
        final_decision = "NO_ACTION"
    else:
        final_decision = "CURRENT_ONLY"

    selected_capabilities = [
        {
            "candidate_id": candidate["candidate_id"],
            "adapted_capability_id": candidate["definition_id_or_null"],
            "definition_version": candidate["definition_version_or_null"],
            "definition_sha256": candidate["definition_sha256_or_null"],
            "ranking": candidate["ranking"],
        }
        for candidate in selected
    ]
    selected_permissions = [candidate["permission"] for candidate in selected]
    effective_permission_union = sorted(
        set(_activation_permissions(activation_plan))
        | {permission for record in selected_permissions for permission in record["effective_permissions"]}
    )
    effective_gate = _strongest_named_gate([record["strongest_gate"] for record in selected_permissions]) if selected_permissions else _strongest_named_gate(_activation_gates(activation_plan))

    output: dict[str, Any] = {
        "schema_version": 1,
        "selector_version": SELECTOR_VERSION,
        "policy_version": policy.get("policy_version"),
        "task_fingerprint": utf8_sha256(task_text),
        "input_sha256": input_sha256,
        "router_result_reference": {
            "sha256": canonical_sha256(router_result),
            "selected_capability_ids": _selected_router_ids(router_result),
            "profile": router_result.get("profile"),
            "result": router_result.get("result"),
            "preserved": True,
        },
        "activation_plan_reference": {
            "sha256": canonical_sha256(activation_plan),
            "selected_capability_ids": sorted(str(plan.get("id")) for plan in activation_plan.get("plans", []) if plan.get("id")),
            "profile": activation_plan.get("profile"),
            "gates": copy.deepcopy(activation_plan.get("gates")),
            "strongest_decision": activation_plan.get("strongest_decision"),
            "preserved": True,
        },
        "catalog_reference": {
            "catalog_id": catalog.get("catalog_id"),
            "catalog_revision": catalog.get("catalog_revision"),
            "sha256": canonical_sha256(catalog),
        },
        "candidate_ids": [candidate.get("candidate_id") for candidate in catalog.get("candidates", []) if isinstance(candidate, dict)],
        "gate_order": list(GATE_ORDER),
        "candidate_evidence": candidates,
        "ranking_order": [candidate["candidate_id"] for candidate in ranked],
        "selected_adapted_capabilities": selected_capabilities,
        "excluded_candidates": exclusion_records,
        "selected_unit_ids": combined_budget["selected_unit_ids"] if selected else [],
        "excluded_units": combined_budget["excluded_units"] if selected else [],
        "budget_plan": combined_budget,
        "permission_result": {
            "current_playbook_permissions": _activation_permissions(activation_plan),
            "selected_candidate_permissions": selected_permissions,
            "effective_permissions": effective_permission_union,
            "strongest_gate": effective_gate,
        },
        "explicit_multi_domain": explicit_multi_domain,
        "issues": [issue.as_dict() for issue in issues],
        "final_decision": final_decision,
        "output_sha256": "0" * 64,
    }
    output["output_sha256"] = hash_without_field(output, "output_sha256")
    return output


def deterministic_select(**kwargs: Any) -> dict[str, Any]:
    """Build twice and fail closed if identical inputs produce different bytes."""
    first = select_adapted_context(**kwargs)
    second = select_adapted_context(**copy.deepcopy(kwargs))
    if canonical_json_bytes(first) != canonical_json_bytes(second):
        failed = copy.deepcopy(first)
        failed["selected_adapted_capabilities"] = []
        failed["selected_unit_ids"] = []
        failed["final_decision"] = "HUMAN_GATE_REQUIRED"
        failed["issues"].append(SelectionIssue("NON_DETERMINISTIC_SELECTION", "$", "identical inputs produced different output bytes").as_dict())
        failed["output_sha256"] = hash_without_field(failed, "output_sha256")
        return failed
    return first
