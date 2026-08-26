"""Deterministic V8.4-006A transport-conformance classifier.

No backend, model, API, network, or production integration is used here.
The current Codex CLI adapter stays fail-closed until a separate verified
context channel is proven by executable backend evidence.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any

CONTRACT = "C_VERSIONED_OPT_IN_LAUNCHER_CONTRACT"
MODE = "SEPARATE_VERIFIED_CONTEXT_V1"


@dataclass(frozen=True)
class AdapterSpec:
    name: str
    supports_separate_verified_context: bool
    preserves_exact_task_once: bool
    deterministic_context_binding: bool
    verifies_hash_size_permission_before_spawn: bool
    cleanup_control: bool
    failure_control: bool
    notes: str = ""


REQUIRED_CHECKS = (
    "supports_separate_verified_context",
    "preserves_exact_task_once",
    "deterministic_context_binding",
    "verifies_hash_size_permission_before_spawn",
    "cleanup_control",
    "failure_control",
)


def _digest(spec: AdapterSpec, checks: dict[str, bool]) -> str:
    payload = {
        "contract": CONTRACT,
        "mode": MODE,
        "adapter": asdict(spec),
        "checks": checks,
    }
    data = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def classify(spec: AdapterSpec) -> dict[str, Any]:
    checks = {name: bool(getattr(spec, name)) for name in REQUIRED_CHECKS}
    missing = [name for name, passed in checks.items() if not passed]

    if not checks["supports_separate_verified_context"]:
        classification = "unsupported"
    elif not missing:
        classification = "compatible"
    else:
        classification = "partial"

    return {
        "adapter": spec.name,
        "contract": CONTRACT,
        "mode": MODE,
        "classification": classification,
        "checks": checks,
        "missing": missing,
        "evidence_digest": _digest(spec, checks),
        "notes": spec.notes,
    }


def default_specs() -> list[AdapterSpec]:
    return [
        AdapterSpec(
            name="codex-cli-current",
            supports_separate_verified_context=False,
            preserves_exact_task_once=True,
            deterministic_context_binding=False,
            verifies_hash_size_permission_before_spawn=False,
            cleanup_control=False,
            failure_control=True,
            notes=(
                "Repository evidence shows exact task positional delivery but no "
                "proven separate verified-context channel."
            ),
        ),
        AdapterSpec(
            name="simulated-separate-context-complete",
            supports_separate_verified_context=True,
            preserves_exact_task_once=True,
            deterministic_context_binding=True,
            verifies_hash_size_permission_before_spawn=True,
            cleanup_control=True,
            failure_control=True,
            notes="Positive control only; deterministic simulation, not backend evidence.",
        ),
        AdapterSpec(
            name="simulated-separate-context-partial",
            supports_separate_verified_context=True,
            preserves_exact_task_once=True,
            deterministic_context_binding=True,
            verifies_hash_size_permission_before_spawn=False,
            cleanup_control=True,
            failure_control=True,
            notes=(
                "Partial control: separate context exists but final pre-spawn "
                "verification is incomplete."
            ),
        ),
    ]


def build_matrix(specs: list[AdapterSpec] | None = None) -> dict[str, Any]:
    results = [classify(spec) for spec in (default_specs() if specs is None else specs)]
    return {
        "task_id": "V8_4-EXPERT-CONTEXT-006A",
        "scope": "non-inference transport conformance simulation",
        "contract": CONTRACT,
        "mode": MODE,
        "model_used": False,
        "api_used": False,
        "network_used": False,
        "production_integration_used": False,
        "results": results,
        "summary": {
            "compatible": sum(r["classification"] == "compatible" for r in results),
            "partial": sum(r["classification"] == "partial" for r in results),
            "unsupported": sum(r["classification"] == "unsupported" for r in results),
        },
        "promotion_evidence": {
            "classifier_simulation": "PASS",
            "transport_conformance": False,
            "production_transport_approved": False,
            "blocking_reason": (
                "codex-cli-current has no proven SEPARATE_VERIFIED_CONTEXT_V1 "
                "binding; simulation controls cannot satisfy the real transport gate."
            ),
        },
    }


if __name__ == "__main__":
    print(json.dumps(build_matrix(), ensure_ascii=False, indent=2, sort_keys=True))
