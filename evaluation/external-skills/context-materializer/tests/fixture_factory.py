"""Cross-layer fixtures using the frozen V8.4-005 selector output."""

from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path
from typing import Any


MATERIALIZER_ROOT = Path(__file__).resolve().parents[1]
EXTERNAL_ROOT = MATERIALIZER_ROOT.parent
REPO_ROOT = MATERIALIZER_ROOT.parents[2]
SELECTOR_ROOT = EXTERNAL_ROOT / "context-selector"
SELECTOR_FIXTURE_PATH = SELECTOR_ROOT / "tests" / "fixture_factory.py"
CONTEXT_VALIDATOR_DIR = EXTERNAL_ROOT / "context-contract" / "validator"
for directory in (MATERIALIZER_ROOT, SELECTOR_ROOT, CONTEXT_VALIDATOR_DIR):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

from context_contract import (  # noqa: E402
    CONTRACT_ID,
    TRANSPORT_MODE,
    TRUST_LABEL,
    canonical_sha256,
    utf8_sha256,
)
from materializer import build_runtime_envelope  # noqa: E402
from selector import deterministic_select  # noqa: E402


FIXED_TIME_UTC = "2030-01-01T00:00:00Z"
TASK_TEXT = "perform exact symbolic equation solving and verify every residual"


def _load_selector_fixture_module():
    module_name = "v84_selector_fixture_factory_for_materializer"
    if module_name in sys.modules:
        return sys.modules[module_name]
    spec = importlib.util.spec_from_file_location(module_name, SELECTOR_FIXTURE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load selector fixture factory")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def build_bundle(
    session_id: str = "materializer-session-001",
    *,
    candidate_ids: tuple[str, ...] = ("kd-sympy",),
    task_text: str = TASK_TEXT,
    approve_composition: bool = False,
) -> dict[str, Any]:
    selector_fixture = _load_selector_fixture_module()
    catalog, metadata, selector_policy = selector_fixture.approved_inputs(candidate_ids)
    if approve_composition:
        selector_fixture.add_approved_composition(catalog, selector_policy, list(candidate_ids))
    router = selector_fixture.router_result(task_text)
    activation = selector_fixture.activation_plan(task_text)
    permissions = selector_fixture.permission_state(activation)
    selection = deterministic_select(
        task_text=task_text,
        router_result=router,
        activation_plan=activation,
        catalog=catalog,
        candidate_metadata=metadata,
        permission_state=permissions,
        policy=selector_policy,
    )
    if selection["final_decision"] != "ADAPTED_SELECTED":
        raise RuntimeError("fixture selector did not select adapted context")

    selected_candidates = [item["candidate_id"] for item in selection["selected_adapted_capabilities"]]
    definitions = [
        copy.deepcopy(entry["definition"])
        for candidate_id in selected_candidates
        for entry in catalog["candidates"]
        if entry["candidate_id"] == candidate_id
    ]
    current_permissions = selection["permission_result"]["current_playbook_permissions"]
    source_permissions = sorted(
        {permission for definition in definitions for permission in definition["permissions"]["source_permissions"]}
    )
    retained_permissions = sorted(
        {permission for definition in definitions for permission in definition["permissions"]["retained_permissions"]}
    )
    permission_decision = {
        "current_permissions": current_permissions,
        "adapted_source_permissions": source_permissions,
        "adapted_effective_permissions": sorted(set(source_permissions) | set(retained_permissions)),
        "effective_permissions": selection["permission_result"]["effective_permissions"],
        "strongest_gate": selection["permission_result"]["strongest_gate"],
        "approval_refs": ["tests/fixtures/materializer-permission-approval.json"],
        "verified_at_utc": FIXED_TIME_UTC,
    }
    envelope = build_runtime_envelope(
        session_id=session_id,
        task_fingerprint=utf8_sha256(task_text),
        definitions=definitions,
        selector_output=selection,
        permission_decision=permission_decision,
        materialized_at_utc=FIXED_TIME_UTC,
    )
    probe = {
        "schema_version": 1,
        "contract_id": "v8.4-backend-capability-probe-v1",
        "probe_id": "pure-fake-probe-v84-006",
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
        "evidence_refs": ["tests/fixtures/pure-fake-probe.json"],
        "external_access_performed": False,
    }
    budget = selection["budget_plan"]
    required_only = all(item["required"] for item in envelope["selected_units"])
    request = {
        "schema_version": 1,
        "contract_id": CONTRACT_ID,
        "session_id": session_id,
        "mode": TRANSPORT_MODE,
        "task": {
            "text": task_text,
            "utf8_sha256": utf8_sha256(task_text),
            "required_occurrence_count": 1,
        },
        "current_plan": {
            "router_result": "NO_ACTION",
            "selected_capability_ids": [],
            "verification_profile": "MINIMAL",
            "permissions": current_permissions,
            "required_gates": [],
        },
        "adapted_context": {
            "envelope_relative_path": "contexts/envelope.json",
            "envelope_sha256": canonical_sha256(envelope),
            "content_sha256": envelope["context_sha256"],
            "trust_label": TRUST_LABEL,
            "adapted_definition_ids": envelope["selected_capabilities"],
            "adapted_definition_versions": envelope["adaptation_versions"],
            "adapted_definition_hashes": [canonical_sha256(definition) for definition in definitions],
            "source_snapshot_hashes": envelope["source_snapshot_hashes"],
            "selected_unit_ids": envelope["selected_unit_ids"],
            "loaded_context_bytes": envelope["loaded_context_bytes"],
            "prompt_token_count_or_null": envelope["prompt_token_count_or_null"],
            "tokenizer_id_or_null": envelope["tokenizer_id_or_null"],
            "token_unavailable_reason_or_null": envelope["token_unavailable_reason_or_null"],
            "cache_key_or_null": envelope["cache_key_or_null"],
            "budget": {
                "max_utf8_bytes": budget["total_utf8_limit"],
                "max_prompt_tokens_or_null": None,
                "required_only": required_only,
                "budget_policy_version": selection["policy_version"],
            },
        },
        "permission_decision": permission_decision,
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
            "fallback_policy_id": "fail-closed-no-fallback-v1",
        },
        "cleanup": {
            "policy_id": "context-session-cleanup-v1",
            "owner": "v8.4-launch-coordinator",
            "context_cleanup_required": True,
            "bridge_cleanup_required": False,
            "quarantine_on_failure": True,
        },
    }
    return {
        "request": request,
        "definitions": definitions,
        "selector_output": selection,
        "probe": probe,
        "timestamp_utc": FIXED_TIME_UTC,
    }


def current_only_bundle(session_id: str = "current-only-session-001") -> dict[str, Any]:
    bundle = build_bundle(session_id)
    request = copy.deepcopy(bundle["request"])
    request["mode"] = "CURRENT_ONLY"
    request["adapted_context"] = None
    request["execution_policy"]["fallback_policy_id"] = "explicit-current-only-v1"
    request["cleanup"]["context_cleanup_required"] = False
    selector_output = {
        "final_decision": "CURRENT_ONLY",
        "selected_adapted_capabilities": [],
        "selected_unit_ids": [],
    }
    return {
        "request": request,
        "definitions": [],
        "selector_output": selector_output,
        "probe": bundle["probe"],
        "timestamp_utc": FIXED_TIME_UTC,
    }
