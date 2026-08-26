"""Deterministic, fail-closed V8.4 main-promotion gate.

This module evaluates frozen evidence only. It never launches Codex, calls an LLM,
changes runtime state, or mutates the stable branch.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class PromotionGateError(ValueError):
    pass


REQUIRED_GATES = (
    "internal_regression",
    "transport_conformance",
    "native_vs_playbook_controlled_comparison",
    "generalization_holdout",
    "candidate_approval",
    "stable_runtime_rollback",
)


def _bool(evidence: dict[str, Any], key: str) -> bool:
    value = evidence.get(key)
    if not isinstance(value, bool):
        raise PromotionGateError(f"{key} must be boolean")
    return value


def _num(evidence: dict[str, Any], key: str) -> float:
    value = evidence.get(key)
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise PromotionGateError(f"{key} must be numeric")
    return float(value)


def _ratio(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        raise PromotionGateError("ratio denominator must be positive")
    return numerator / denominator


def evaluate(evidence: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    for gate in REQUIRED_GATES:
        if gate not in evidence:
            return {
                "decision": "NOT_READY",
                "failure_code": "EVIDENCE_MISSING",
                "missing_gate": gate,
            }

    failed: list[dict[str, Any]] = []

    for gate in REQUIRED_GATES:
        try:
            passed = _bool(evidence, gate)
        except PromotionGateError as exc:
            return {"decision": "BLOCKED", "failure_code": "INVALID_EVIDENCE", "message": str(exc)}
        if not passed:
            failed.append({"gate": gate, "reason": "gate_false"})

    perf = policy["performance_policy"]
    try:
        quality_delta = _num(evidence, "adapted_quality_delta_vs_native")
        latency_ratio = _ratio(_num(evidence, "adapted_latency_ms"), _num(evidence, "native_latency_ms"))
        token_ratio = _ratio(_num(evidence, "adapted_prompt_tokens"), _num(evidence, "native_prompt_tokens"))
        context_ratio = _ratio(_num(evidence, "adapted_context_bytes"), _num(evidence, "current_context_bytes"))
        holdout_tasks = int(_num(evidence, "holdout_task_count"))
        categories = int(_num(evidence, "holdout_category_count"))
        repeats = int(_num(evidence, "repeats_per_variant"))
    except (PromotionGateError, KeyError) as exc:
        return {"decision": "BLOCKED", "failure_code": "INVALID_PERFORMANCE_EVIDENCE", "message": str(exc)}

    if quality_delta < float(perf["adapted_quality_min_delta_vs_native"]):
        failed.append({"gate": "performance_quality", "reason": "quality_below_threshold", "value": quality_delta})
    if latency_ratio > float(perf["adapted_latency_max_ratio_vs_native"]):
        failed.append({"gate": "performance_latency", "reason": "latency_above_threshold", "value": latency_ratio})
    if token_ratio > float(perf["adapted_prompt_token_max_ratio_vs_native"]):
        failed.append({"gate": "performance_tokens", "reason": "tokens_above_threshold", "value": token_ratio})
    if context_ratio > float(perf["adapted_context_bytes_max_ratio_vs_current"]):
        failed.append({"gate": "performance_context", "reason": "context_reduction_insufficient", "value": context_ratio})
    if holdout_tasks < int(perf["minimum_holdout_tasks"]):
        failed.append({"gate": "generalization_holdout", "reason": "too_few_tasks", "value": holdout_tasks})
    if categories < int(perf["minimum_task_categories"]):
        failed.append({"gate": "generalization_holdout", "reason": "too_few_categories", "value": categories})
    if repeats < int(perf["minimum_repeats_per_variant"]):
        failed.append({"gate": "generalization_holdout", "reason": "too_few_repeats", "value": repeats})

    decision = "READY_FOR_PROMOTION" if not failed else "NOT_READY"
    return {
        "decision": decision,
        "failure_count": len(failed),
        "failed_checks": failed,
        "metrics": {
            "quality_delta_vs_native": quality_delta,
            "latency_ratio_vs_native": latency_ratio,
            "token_ratio_vs_native": token_ratio,
            "context_ratio_vs_current": context_ratio,
            "holdout_tasks": holdout_tasks,
            "holdout_categories": categories,
            "repeats_per_variant": repeats,
        },
        "required_gates": list(REQUIRED_GATES),
        "stable_target": policy["stable_target"],
    }


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", required=True)
    parser.add_argument("--evidence", required=True)
    args = parser.parse_args(argv)

    policy = json.loads(Path(args.policy).read_text(encoding="utf-8"))
    evidence = json.loads(Path(args.evidence).read_text(encoding="utf-8"))
    result = evaluate(evidence, policy)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["decision"] == "READY_FOR_PROMOTION" else 2


if __name__ == "__main__":
    raise SystemExit(main())
