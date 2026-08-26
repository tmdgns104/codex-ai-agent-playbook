from __future__ import annotations

import copy
import sys
from pathlib import Path
from typing import Any


SELECTOR_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
CONTEXT_VALIDATOR_DIR = SELECTOR_ROOT.parent / "context-contract" / "validator"
for directory in (SELECTOR_ROOT, CONTEXT_VALIDATOR_DIR):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

from context_contract import (  # noqa: E402
    canonical_sha256,
    compute_cache_key,
    definition_content_bytes,
    definition_content_sha256,
)
from selector import load_policy, repository_shadow_inputs  # noqa: E402


def router_result(task_text: str, selected_ids: list[str] | None = None) -> dict[str, Any]:
    selected = [
        {
            "id": capability_id,
            "type": "skill",
            "score": 10,
            "threshold": 5,
            "eligible": True,
            "profile": "standard",
            "approval": "none",
            "context_cost": "low",
            "risk": "low",
            "matched_triggers": [capability_id],
            "matched_domains": [],
            "summary_overlap": [],
        }
        for capability_id in (selected_ids or [])
    ]
    return {
        "task": task_text,
        "selected": selected,
        "profile": "standard" if selected else "minimal",
        "count": len(selected),
        "result": "ROUTED" if selected else "NO_CAPABILITY",
    }


def activation_plan(
    task_text: str,
    selected_ids: list[str] | None = None,
    permissions: list[str] | None = None,
) -> dict[str, Any]:
    selected = selected_ids or []
    permission_list = permissions or []
    plans = [
        {
            "id": capability_id,
            "type": "skill",
            "decision": "AUTO_ALLOWED" if permission_list in ([], ["local_read"]) else "PROFILE_GATED",
            "permissions": list(permission_list),
            "reasons": ["test-fixture"],
            "score": 10,
            "profile": "standard",
        }
        for capability_id in selected
    ]
    return {
        "task": task_text,
        "profile": "standard" if plans else "minimal",
        "plans": plans,
        "count": len(plans),
        "gates": {
            "profile": sum(plan["decision"] == "PROFILE_GATED" for plan in plans),
            "network": 0,
            "human": 0,
            "manual": 0,
        },
        "strongest_decision": plans[0]["decision"] if plans else "NONE",
        "result": "PLANNED" if plans else "NO_ACTION",
        "side_effects_executed": False,
    }


def permission_state(
    activation: dict[str, Any],
    *,
    approved_gates: list[str] | None = None,
) -> dict[str, Any]:
    current_permissions = sorted(
        {permission for plan in activation["plans"] for permission in plan["permissions"]}
    )
    return {
        "current_permissions": current_permissions,
        "approved_gates": approved_gates or ["NETWORK_REVIEW", "HUMAN_GATE_REQUIRED"],
        "approval_refs": ["tests/fixtures/permission-approval.json"],
        "expected_effective_gates": {
            "kd-sympy": "NETWORK_REVIEW",
            "kd-citation-management": "HUMAN_GATE_REQUIRED",
        },
    }


def refresh_approved_entry(
    entry: dict[str, Any],
    metadata: dict[str, Any],
) -> None:
    definition = entry["definition"]
    definition["status"] = "APPROVED"
    definition["version"] = "1.0.0-test-only"
    definition["transformation"]["reviewer"] = "TEST_FIXTURE_REVIEWER"
    definition["verification"].update(
        {
            "schema_pass": "PASS",
            "provenance_pass": "PASS",
            "safety_pass": "PASS",
            "fixture_pass": "PASS",
            "holdout_pass": "PASS",
            "fixture_evidence": [f"tests/fixtures/{entry['candidate_id']}-fixture.json"],
            "holdout_evidence": [f"tests/fixtures/{entry['candidate_id']}-holdout.json"],
        }
    )
    definition["budget"]["utf8_bytes"] = definition_content_bytes(definition)
    definition["content_sha256"] = definition_content_sha256(definition)
    definition["cache_key"] = compute_cache_key(definition)
    definition_hash = canonical_sha256(definition)
    required_ids = [unit["unit_id"] for unit in definition["knowledge_units"] if unit["required"]]
    entry["approval"] = {
        "status": "APPROVED",
        "approval_ref_or_null": f"tests/fixtures/{entry['candidate_id']}-approval.json",
        "approved_definition_sha256_or_null": definition_hash,
        "required_unit_ids": required_ids,
    }
    entry["quality_evidence"] = {
        "schema_pass": "PASS",
        "provenance_pass": "PASS",
        "safety_pass": "PASS",
        "fixture_pass": "PASS",
        "holdout_pass": "PASS",
        "evidence_refs": definition["verification"]["fixture_evidence"] + definition["verification"]["holdout_evidence"],
        "definition_sha256": definition_hash,
    }
    metadata.update(
        {
            "expected_snapshot_sha256": definition["source"]["snapshot_sha256"],
            "expected_definition_content_sha256": definition["content_sha256"],
            "expected_cache_key": definition["cache_key"],
            "expected_version": definition["version"],
            "satisfied_prerequisites": list(definition["applicability"]["prerequisites"]),
            "overlap_capability_ids": metadata.get("overlap_capability_ids", []),
            "capability_delta": metadata.get(
                "capability_delta",
                {"status": "NOT_REQUIRED", "evidence_refs": []},
            ),
        }
    )


def approved_inputs(candidate_ids: tuple[str, ...] = ("kd-sympy",)) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    catalog, metadata = repository_shadow_inputs(REPO_ROOT)
    catalog = copy.deepcopy(catalog)
    metadata = copy.deepcopy(metadata)
    catalog["candidates"] = [entry for entry in catalog["candidates"] if entry["candidate_id"] in candidate_ids]
    metadata = {candidate_id: metadata[candidate_id] for candidate_id in candidate_ids}
    for entry in catalog["candidates"]:
        refresh_approved_entry(entry, metadata[entry["candidate_id"]])
    catalog["catalog_id"] = "test-only-approved-adapted-catalog"
    catalog["catalog_revision"] = canonical_sha256(
        [entry["approval"]["approved_definition_sha256_or_null"] for entry in catalog["candidates"]]
    )
    return catalog, metadata, copy.deepcopy(load_policy())


def add_approved_composition(
    catalog: dict[str, Any],
    policy: dict[str, Any],
    candidate_ids: list[str],
) -> None:
    policy_record = {
        "composition_id": "test-only-sympy-citation-composition",
        "candidate_ids": sorted(candidate_ids),
        "status": "APPROVED",
        "evidence_refs": ["tests/fixtures/test-only-composition-evidence.json"],
    }
    policy["approved_compositions"] = [policy_record]
    catalog["approved_compositions"] = [
        {
            **copy.deepcopy(policy_record),
            "policy_record_sha256": canonical_sha256(policy_record),
        }
    ]
    catalog["catalog_revision"] = canonical_sha256(
        {
            "definitions": [entry["approval"]["approved_definition_sha256_or_null"] for entry in catalog["candidates"]],
            "compositions": catalog["approved_compositions"],
        }
    )
