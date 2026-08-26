"""V8.4-007 frozen benchmark/holdout preflight.

This module validates policy and fixture shape only. It never executes a model.
"""

from __future__ import annotations

import hashlib
from typing import Any


def validate(policy: dict[str, Any], holdout: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    fixtures = holdout.get("fixtures")
    if not isinstance(fixtures, list):
        return {"status": "BLOCKED", "failures": ["fixtures_missing_or_invalid"]}

    ids = [item.get("fixture_id") for item in fixtures]
    categories = {item.get("category") for item in fixtures if item.get("category")}
    candidates = {item.get("candidate_id") for item in fixtures if item.get("candidate_id")}

    if len(fixtures) < int(policy["minimum_holdout_tasks"]):
        failures.append("too_few_holdout_tasks")
    if len(categories) < int(policy["minimum_task_categories"]):
        failures.append("too_few_categories")
    if int(policy["repeats_per_variant"]) < 3:
        failures.append("too_few_repeats")
    if len(ids) != len(set(ids)):
        failures.append("duplicate_fixture_id")
    if any(str(item).startswith(holdout["development_fixture_prefix"]) for item in ids):
        failures.append("development_holdout_id_overlap")
    if candidates - {"kd-sympy", "kd-citation-management"}:
        failures.append("unapproved_candidate_in_holdout")

    for item in fixtures:
        task = item.get("task")
        expected = item.get("task_sha256")
        if not isinstance(task, str) or not isinstance(expected, str):
            failures.append(f"invalid_task_hash_fields:{item.get('fixture_id')}")
            continue
        actual = hashlib.sha256(task.encode("utf-8")).hexdigest()
        if actual != expected:
            failures.append(f"task_hash_mismatch:{item.get('fixture_id')}")

    current = policy["current_execution_state"]
    if current.get("transport_conformance") is not True:
        execution_state = "EXECUTION_BLOCKED_BY_TRANSPORT"
    else:
        execution_state = "EXECUTION_PREFLIGHT_READY"

    return {
        "status": "PASS" if not failures else "BLOCKED",
        "failures": failures,
        "fixture_count": len(fixtures),
        "category_count": len(categories),
        "candidate_count": len(candidates),
        "repeats_per_variant": int(policy["repeats_per_variant"]),
        "policy_frozen": True,
        "holdout_frozen": True,
        "generalization_holdout": False,
        "native_vs_playbook_controlled_comparison": False,
        "execution_state": execution_state,
    }
