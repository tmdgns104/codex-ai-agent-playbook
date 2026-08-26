"""Deterministic fake fixture construction and mutation helpers."""

from __future__ import annotations

import copy
from typing import Any

from context_contract import (
    CONTRACT_ID,
    TRANSPORT_MODE,
    TRUST_LABEL,
    assemble_context_text,
    canonical_json_bytes,
    canonical_sha256,
    compute_cache_key,
    definition_content_bytes,
    definition_content_sha256,
    hash_without_field,
    utf8_sha256,
)
from fake_backend import make_compliant_result


EXPECTED_TASK = "분리된 적응 컨텍스트를 사용해 이 작업을 검증한다."
VALIDATION_TIME_UTC = "2030-01-01T00:00:00Z"
SESSION_ID = "fixture-session-001"


def _hashed_unit(**values: Any) -> dict[str, Any]:
    unit = dict(values)
    unit["content_sha256"] = canonical_sha256(unit)
    return unit


def build_compliant_bundle() -> dict[str, Any]:
    definition: dict[str, Any] = {
        "schema_version": 1,
        "contract_id": "v8.4-adapted-capability-definition-v1",
        "adapted_capability_id": "fixture-data-quality-guidance",
        "version": "1.0.0",
        "status": "APPROVED",
        "candidate_id": "fixture-candidate-001",
        "applicability": {
            "domains": ["data-analysis"],
            "task_triggers": ["classification-evaluation"],
            "exclusions": ["runtime-control"],
            "prerequisites": ["labeled-data"],
        },
        "source": {
            "snapshot_path": "evaluation/external-skills/snapshots/fixture/SKILL.md",
            "snapshot_revision": "fixture-revision-001",
            "snapshot_sha256": "1" * 64,
            "license_id": "fixture-only",
            "inspection_evidence": ["evidence/fixture-source-inspection.json"],
        },
        "transformation": {
            "policy_version": "adaptation-policy-v1",
            "method": "DETERMINISTIC_EXTRACTION",
            "tool_or_model_id_or_null": None,
            "reviewer": "offline-fixture-reviewer",
            "created_at_utc": "2029-12-31T00:00:00Z",
            "extractor_version": "fixture-extractor-v1",
        },
        "permissions": {
            "source_permissions": ["local_read", "network"],
            "retained_permissions": ["local_read"],
            "removed_permissions": ["network"],
            "removal_justification": "The adapted reference needs no network access.",
            "forbidden_actions": ["network access", "credential access", "runtime mutation"],
            "effective_gate": "NETWORK_REVIEW",
            "permission_policy_version": "permission-union-v1",
        },
        "knowledge_units": [
            _hashed_unit(
                unit_id="unit-evaluation",
                kind="RULE",
                priority=0,
                required=True,
                task_tags=["classification-evaluation"],
                prerequisites=[],
                content="불균형 분류에서는 정확도만으로 판단하지 않고 PR-AUC와 재현율을 함께 검증한다.",
                source_locator="SKILL.md#evaluation",
                source_claim_sha256="2" * 64,
                verification_requirements=["report class-sensitive metrics"],
                failure_modes=["accuracy-only conclusion"],
                safety_constraints=["do not infer missing metrics"],
            ),
            _hashed_unit(
                unit_id="unit-preprocessing",
                kind="PROCEDURE",
                priority=1,
                required=True,
                task_tags=["classification-evaluation"],
                prerequisites=["unit-evaluation"],
                content="전처리는 학습 데이터에만 적합하고 검증 데이터에는 동일 변환을 적용한다.",
                source_locator="SKILL.md#preprocessing",
                source_claim_sha256="3" * 64,
                verification_requirements=["fit transforms on training data"],
                failure_modes=["validation leakage"],
                safety_constraints=["preserve split boundaries"],
            ),
        ],
        "budget": {
            "utf8_bytes": 0,
            "tokenizer_id_or_null": None,
            "token_count_or_null": None,
            "unavailable_reason_or_null": "No tokenizer is used by the offline fixture.",
        },
        "verification": {
            "schema_pass": "PASS",
            "provenance_pass": "PASS",
            "safety_pass": "PASS",
            "fixture_pass": "PASS",
            "holdout_pass": "PASS",
            "fixture_evidence": ["evidence/fixture-validation.json"],
            "holdout_evidence": ["evidence/fixture-holdout.json"],
        },
        "content_sha256": "0" * 64,
        "cache_key": "0" * 64,
    }
    definition["budget"]["utf8_bytes"] = definition_content_bytes(definition)
    definition["content_sha256"] = definition_content_sha256(definition)
    definition["cache_key"] = compute_cache_key(definition)

    selected_ids = [unit["unit_id"] for unit in definition["knowledge_units"]]
    context_text = assemble_context_text(definition, selected_ids)
    context_hash = utf8_sha256(context_text)
    effective_permissions = ["external_write", "local_read", "network"]
    envelope: dict[str, Any] = {
        "schema_version": 1,
        "contract_id": "v8.4-runtime-context-envelope-v1",
        "session_id": SESSION_ID,
        "task_fingerprint": utf8_sha256(EXPECTED_TASK),
        "selected_capabilities": [definition["adapted_capability_id"]],
        "selected_unit_ids": selected_ids,
        "selected_units": [
            {
                "unit_id": unit["unit_id"],
                "required": unit["required"],
                "content_sha256": unit["content_sha256"],
                "utf8_bytes": len(unit["content"].encode("utf-8")),
            }
            for unit in definition["knowledge_units"]
        ],
        "source_snapshot_hashes": [definition["source"]["snapshot_sha256"]],
        "adaptation_versions": [definition["version"]],
        "definition_content_hashes": [definition["content_sha256"]],
        "effective_permissions": effective_permissions,
        "required_gates": ["HUMAN_GATE_REQUIRED"],
        "trust_label": TRUST_LABEL,
        "context_text": context_text,
        "context_sha256": context_hash,
        "loaded_context_bytes": len(context_text.encode("utf-8")),
        "prompt_token_count_or_null": None,
        "tokenizer_id_or_null": None,
        "token_unavailable_reason_or_null": "No tokenizer is used by the offline fixture.",
        "cache_key_or_null": definition["cache_key"],
        "materialized_at_utc": "2030-01-01T00:00:00Z",
        "cleanup_required": True,
    }

    probe: dict[str, Any] = {
        "schema_version": 1,
        "contract_id": "v8.4-backend-capability-probe-v1",
        "probe_id": "fake-probe-001",
        "backend_id": "pure-fake-backend",
        "backend_version": "1.0.0",
        "adapter_id": "pure-fake-adapter",
        "adapter_version": "1.0.0",
        "support_status": "SUPPORTED",
        "supports_separate_verified_context": True,
        "task_channel_separate": True,
        "context_channel_separate": True,
        "supported_transport_modes": [TRANSPORT_MODE],
        "probed_at_utc": "2029-12-31T00:00:00Z",
        "expires_at_utc": "2099-01-01T00:00:00Z",
        "evidence_refs": ["evidence/fake-probe.json"],
        "external_access_performed": False,
    }

    request: dict[str, Any] = {
        "schema_version": 1,
        "contract_id": CONTRACT_ID,
        "session_id": SESSION_ID,
        "mode": TRANSPORT_MODE,
        "task": {
            "text": EXPECTED_TASK,
            "utf8_sha256": utf8_sha256(EXPECTED_TASK),
            "required_occurrence_count": 1,
        },
        "current_plan": {
            "router_result": "READY",
            "selected_capability_ids": ["base-fixture-capability"],
            "verification_profile": "STANDARD",
            "permissions": ["external_write", "local_read"],
            "required_gates": ["HUMAN_GATE_REQUIRED"],
        },
        "adapted_context": {
            "envelope_relative_path": "contexts/envelope.json",
            "envelope_sha256": canonical_sha256(envelope),
            "content_sha256": context_hash,
            "trust_label": TRUST_LABEL,
            "adapted_definition_ids": [definition["adapted_capability_id"]],
            "adapted_definition_versions": [definition["version"]],
            "adapted_definition_hashes": [canonical_sha256(definition)],
            "source_snapshot_hashes": [definition["source"]["snapshot_sha256"]],
            "selected_unit_ids": selected_ids,
            "loaded_context_bytes": envelope["loaded_context_bytes"],
            "prompt_token_count_or_null": None,
            "tokenizer_id_or_null": None,
            "token_unavailable_reason_or_null": "No tokenizer is used by the offline fixture.",
            "cache_key_or_null": definition["cache_key"],
            "budget": {
                "max_utf8_bytes": 4096,
                "max_prompt_tokens_or_null": None,
                "required_only": True,
                "budget_policy_version": "context-budget-v1",
            },
        },
        "permission_decision": {
            "current_permissions": ["external_write", "local_read"],
            "adapted_source_permissions": ["local_read", "network"],
            "adapted_effective_permissions": ["local_read", "network"],
            "effective_permissions": effective_permissions,
            "strongest_gate": "HUMAN_GATE_REQUIRED",
            "approval_refs": ["approval/fake-human-gate.json"],
            "verified_at_utc": "2030-01-01T00:00:00Z",
        },
        "backend": {
            "adapter_id": probe["adapter_id"],
            "adapter_version": probe["adapter_version"],
            "capability_probe_id": probe["probe_id"],
            "capability_probe_sha256": canonical_sha256(probe),
            "transport_binding": "FAKE_BACKEND_ONLY",
        },
        "execution_policy": {
            "context_injection_attempt_limit": 1,
            "task_occurrence_limit": 1,
            "retry_count": 0,
            "fallback_policy_id": "fail-closed-v1",
        },
        "cleanup": {
            "policy_id": "session-cleanup-v1",
            "owner": "fake-backend-harness",
            "context_cleanup_required": True,
            "bridge_cleanup_required": True,
            "quarantine_on_failure": True,
        },
    }
    result = make_compliant_result(request, probe, context_hash)
    return {
        "fixture_id": "compliant",
        "expected_task_text": EXPECTED_TASK,
        "validation_time_utc": VALIDATION_TIME_UTC,
        "definition": definition,
        "envelope": envelope,
        "probe": probe,
        "request": request,
        "result": result,
    }


def _parent_and_key(document: dict[str, Any], dotted_path: str) -> tuple[dict[str, Any], str]:
    parts = dotted_path.split(".")
    parent: dict[str, Any] = document
    for part in parts[:-1]:
        child = parent[part]
        if not isinstance(child, dict):
            raise TypeError(f"fixture mutation parent is not an object: {dotted_path}")
        parent = child
    return parent, parts[-1]


def apply_failure_case(bundle: dict[str, Any], case: dict[str, Any]) -> dict[str, Any]:
    mutated = copy.deepcopy(bundle)
    mutated["fixture_id"] = case["fixture_id"]
    for mutation in case["mutations"]:
        parent, key = _parent_and_key(mutated, mutation["path"])
        if mutation["op"] == "set":
            parent[key] = mutation["value"]
        elif mutation["op"] == "delete":
            del parent[key]
        else:
            raise ValueError(f"unsupported fixture mutation: {mutation['op']}")

    for target in case.get("rehash", []):
        if target == "probe":
            probe_hash = canonical_sha256(mutated["probe"])
            mutated["request"]["backend"]["capability_probe_sha256"] = probe_hash
            mutated["result"]["backend_receipt"]["capability_probe_sha256"] = probe_hash
        elif target == "envelope":
            mutated["request"]["adapted_context"]["envelope_sha256"] = canonical_sha256(mutated["envelope"])
        elif target == "request":
            mutated["result"]["request_sha256"] = canonical_sha256(mutated["request"])
        elif target == "result":
            mutated["result"]["result_sha256"] = hash_without_field(mutated["result"], "result_sha256")
        else:
            raise ValueError(f"unsupported rehash target: {target}")
    return mutated


def canonical_envelope_bytes(bundle: dict[str, Any]) -> bytes:
    return canonical_json_bytes(bundle["envelope"])
