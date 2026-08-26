"""Pure fake backend used only to exercise the V8.4 contract validator.

The fake produces a deterministic receipt.  It never starts a process, opens a
network connection, reads credentials, or invokes an LLM.
"""

from __future__ import annotations

from typing import Any

from context_contract import (
    RESULT_CONTRACT_ID,
    TRANSPORT_MODE,
    canonical_sha256,
    hash_without_field,
)


def make_compliant_result(
    request: dict[str, Any],
    probe: dict[str, Any],
    context_sha256_or_null: str | None,
) -> dict[str, Any]:
    """Return a deterministic successful fake-backend result."""
    context_mode = request["mode"] == TRANSPORT_MODE
    result: dict[str, Any] = {
        "schema_version": 1,
        "contract_id": RESULT_CONTRACT_ID,
        "session_id": request["session_id"],
        "request_sha256": canonical_sha256(request),
        "result_sha256": "0" * 64,
        "transport_status": "PASS",
        "backend_receipt": {
            "adapter_id": request["backend"]["adapter_id"],
            "adapter_version": request["backend"]["adapter_version"],
            "capability_probe_sha256": canonical_sha256(probe),
            "task_channel_sha256": request["task"]["utf8_sha256"],
            "context_channel_sha256_or_null": context_sha256_or_null,
            "task_context_channels_separate": True if context_mode else None,
        },
        "task_occurrence_count": 1,
        "context_injection_attempt_count": 1 if context_mode else 0,
        "context_injection_count": 1 if context_mode else 0,
        "child_spawned": True,
        "child_exit_code_or_null": 0,
        "degraded_fallback_used": False,
        "degraded_reason_or_null": None,
        "integrity_result": "PASS",
        "permission_result": "PASS",
        "budget_result": "PASS",
        "context_cleanup_result": "PASS" if context_mode else "NOT_REQUIRED",
        "bridge_cleanup_result": "PASS",
        "quarantine_paths": [],
        "started_at_utc": "2030-01-01T00:00:01Z",
        "finished_at_utc": "2030-01-01T00:00:02Z",
        "failure_code_or_null": None,
        "evidence_path": "evidence/fake-backend-result.json",
        "side_effects": {
            "external_access": False,
            "credentials": False,
            "external_write": False,
            "destructive": False,
        },
    }
    result["result_sha256"] = hash_without_field(result, "result_sha256")
    return result
