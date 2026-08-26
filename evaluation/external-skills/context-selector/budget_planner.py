"""Deterministic whole-unit byte budget planning for adapted context.

The planner never truncates or summarizes a knowledge unit.  It measures the
exact canonical context bytes that V8.4-003 would assemble and removes only
task-relevant optional units when a hard byte limit requires pruning.
"""

from __future__ import annotations

import hashlib
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
CONTEXT_VALIDATOR_DIR = HERE.parent / "context-contract" / "validator"
if str(CONTEXT_VALIDATOR_DIR) not in sys.path:
    sys.path.insert(0, str(CONTEXT_VALIDATOR_DIR))

from context_contract import assemble_context_text, hash_without_field  # noqa: E402


BUDGET_PLANNER_VERSION = "v8.4-budget-planner-1"
TOKEN_RE = re.compile(r"[0-9A-Za-z가-힣]+")


@dataclass(frozen=True)
class BudgetIssue:
    code: str
    path: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "path": self.path, "message": self.message}


def normalized_phrase(text: str) -> str:
    return " ".join(token.casefold() for token in TOKEN_RE.findall(text))


def contains_phrase(task_text: str, phrase: str) -> bool:
    """Match an explicit normalized phrase without fuzzy or substring matching."""
    task = normalized_phrase(task_text)
    expected = normalized_phrase(phrase)
    return bool(expected and f" {expected} " in f" {task} ")


def _content_bytes(definition: dict[str, Any], selected_unit_ids: list[str]) -> tuple[int, str]:
    text = assemble_context_text(definition, selected_unit_ids)
    return len(text.encode("utf-8")), hashlib.sha256(text.encode("utf-8")).hexdigest()


def _combined_bytes(
    definitions: list[dict[str, Any]],
    selected_by_capability: dict[str, list[str]],
) -> tuple[int, str]:
    texts = [
        assemble_context_text(definition, selected_by_capability[definition["candidate_id"]])
        for definition in definitions
    ]
    combined = "\n".join(text for text in texts if text)
    return len(combined.encode("utf-8")), hashlib.sha256(combined.encode("utf-8")).hexdigest()


def _validate_policy(policy: dict[str, Any]) -> list[BudgetIssue]:
    issues: list[BudgetIssue] = []
    budget = policy.get("budget")
    if not isinstance(budget, dict):
        return [BudgetIssue("BUDGET_POLICY_INVALID", "policy.budget", "budget object is required")]

    for field in ("total_utf8_bytes", "per_capability_utf8_bytes"):
        value = budget.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            issues.append(BudgetIssue("BUDGET_POLICY_INVALID", f"policy.budget.{field}", "non-negative integer is required"))

    token_count = budget.get("token_count_or_null")
    tokenizer = budget.get("tokenizer_id_or_null")
    unavailable_reason = budget.get("unavailable_reason_or_null")
    total_token_limit = budget.get("total_token_limit_or_null")
    per_capability_token_limit = budget.get("per_capability_token_limit_or_null")
    if token_count is None:
        if tokenizer is not None or not isinstance(unavailable_reason, str) or not unavailable_reason.strip():
            issues.append(BudgetIssue("TOKEN_NULL_POLICY_INVALID", "policy.budget", "null token count requires null tokenizer and a reason"))
        if total_token_limit is not None or per_capability_token_limit is not None:
            issues.append(BudgetIssue("TOKEN_BUDGET_UNAVAILABLE", "policy.budget", "token limits cannot be enforced without measured selected-unit token counts"))
    else:
        issues.append(BudgetIssue("TOKEN_MEASUREMENT_UNSUPPORTED", "policy.budget.token_count_or_null", "planner does not estimate or reuse whole-definition tokens for selected units"))

    if policy.get("required_unit_truncation") is not False or policy.get("optional_unit_truncation") is not False:
        issues.append(BudgetIssue("TRUNCATION_POLICY_INVALID", "policy", "whole-unit planning requires both truncation flags to be false"))
    if policy.get("raw_external_fallback") is not False:
        issues.append(BudgetIssue("RAW_FALLBACK_FORBIDDEN", "policy.raw_external_fallback", "raw external fallback must be false"))
    return issues


def plan_budget(
    *,
    task_text: str,
    definitions: list[dict[str, Any]],
    policy: dict[str, Any],
) -> dict[str, Any]:
    """Plan exact bytes for ranked definitions and fail closed on required overflow."""
    issues = _validate_policy(policy)
    if issues:
        result = {
            "planner_version": BUDGET_PLANNER_VERSION,
            "status": "INVALID",
            "issues": [issue.as_dict() for issue in issues],
            "per_capability": [],
            "selected_unit_ids": [],
            "excluded_units": [],
            "pruning_sequence": [],
            "total_utf8_bytes": 0,
            "total_utf8_limit": policy.get("budget", {}).get("total_utf8_bytes"),
            "tokenizer_id_or_null": policy.get("budget", {}).get("tokenizer_id_or_null"),
            "token_count_or_null": policy.get("budget", {}).get("token_count_or_null"),
            "unavailable_reason_or_null": policy.get("budget", {}).get("unavailable_reason_or_null"),
            "context_sha256": hashlib.sha256(b"").hexdigest(),
            "budget_plan_sha256": "0" * 64,
        }
        result["budget_plan_sha256"] = hash_without_field(result, "budget_plan_sha256")
        return result

    budget = policy["budget"]
    per_limit = budget["per_capability_utf8_bytes"]
    total_limit = budget["total_utf8_bytes"]
    selected_by_capability: dict[str, list[str]] = {}
    optional_by_capability: dict[str, list[dict[str, Any]]] = {}
    excluded_units: list[dict[str, str]] = []
    required_ids_by_capability: dict[str, list[str]] = {}
    pruning_sequence: list[dict[str, str]] = []

    for definition in definitions:
        candidate_id = definition["candidate_id"]
        units = definition.get("knowledge_units", [])
        ordered = sorted(units, key=lambda unit: (unit.get("priority"), unit.get("unit_id")))
        unit_ids = [unit.get("unit_id") for unit in ordered]
        priorities = [unit.get("priority") for unit in ordered]
        if (
            units != ordered
            or len(unit_ids) != len(set(unit_ids))
            or len(priorities) != len(set(priorities))
            or any(not isinstance(value, int) or isinstance(value, bool) for value in priorities)
        ):
            issues.append(BudgetIssue("UNIT_ORDER_INVALID", f"definition[{candidate_id}].knowledge_units", "units require unique stable increasing priorities and IDs"))
            continue

        required = [unit for unit in ordered if unit.get("required") is True]
        optional_relevant: list[dict[str, Any]] = []
        for unit in ordered:
            if unit.get("required") is True:
                continue
            tags = unit.get("task_tags", [])
            if any(contains_phrase(task_text, tag) for tag in tags):
                optional_relevant.append(unit)
            else:
                excluded_units.append(
                    {
                        "candidate_id": candidate_id,
                        "unit_id": str(unit.get("unit_id")),
                        "reason": "TASK_IRRELEVANT_OPTIONAL",
                    }
                )

        required_ids = [unit["unit_id"] for unit in required]
        required_ids_by_capability[candidate_id] = required_ids
        optional_by_capability[candidate_id] = optional_relevant
        selected_by_capability[candidate_id] = required_ids + [unit["unit_id"] for unit in optional_relevant]

        required_bytes, _ = _content_bytes(definition, required_ids)
        if required_bytes > per_limit:
            issues.append(
                BudgetIssue(
                    "REQUIRED_ONLY_BUDGET_OVERFLOW",
                    f"definition[{candidate_id}]",
                    f"required bytes {required_bytes} exceed per-capability limit {per_limit}",
                )
            )
            continue

        while True:
            current_bytes, _ = _content_bytes(definition, selected_by_capability[candidate_id])
            if current_bytes <= per_limit:
                break
            removable = [
                unit
                for unit in optional_by_capability[candidate_id]
                if unit["unit_id"] in selected_by_capability[candidate_id]
            ]
            if not removable:
                issues.append(BudgetIssue("REQUIRED_ONLY_BUDGET_OVERFLOW", f"definition[{candidate_id}]", "per-capability budget remains exceeded after optional pruning"))
                break
            removed = max(removable, key=lambda unit: (unit["priority"], unit["unit_id"]))
            selected_by_capability[candidate_id].remove(removed["unit_id"])
            excluded_units.append(
                {
                    "candidate_id": candidate_id,
                    "unit_id": removed["unit_id"],
                    "reason": "PER_CAPABILITY_BUDGET_PRUNED",
                }
            )
            pruning_sequence.append(
                {
                    "candidate_id": candidate_id,
                    "unit_id": removed["unit_id"],
                    "reason": "PER_CAPABILITY_BUDGET_PRUNED",
                }
            )

    if issues:
        status = "BUDGET_BLOCKED" if any(issue.code == "REQUIRED_ONLY_BUDGET_OVERFLOW" for issue in issues) else "INVALID"
    else:
        required_selected = {
            candidate_id: list(required_ids)
            for candidate_id, required_ids in required_ids_by_capability.items()
        }
        required_total, _ = _combined_bytes(definitions, required_selected)
        if required_total > total_limit:
            issues.append(BudgetIssue("REQUIRED_ONLY_BUDGET_OVERFLOW", "policy.budget.total_utf8_bytes", f"combined required bytes {required_total} exceed total limit {total_limit}"))
            status = "BUDGET_BLOCKED"
        else:
            while True:
                total_bytes, _ = _combined_bytes(definitions, selected_by_capability)
                if total_bytes <= total_limit:
                    break
                removable: list[tuple[int, str, str]] = []
                for candidate_id, optional_units in optional_by_capability.items():
                    for unit in optional_units:
                        if unit["unit_id"] in selected_by_capability[candidate_id]:
                            removable.append((unit["priority"], candidate_id, unit["unit_id"]))
                if not removable:
                    issues.append(BudgetIssue("REQUIRED_ONLY_BUDGET_OVERFLOW", "policy.budget.total_utf8_bytes", "total budget remains exceeded after optional pruning"))
                    status = "BUDGET_BLOCKED"
                    break
                _, candidate_id, unit_id = max(removable)
                selected_by_capability[candidate_id].remove(unit_id)
                excluded_units.append(
                    {
                        "candidate_id": candidate_id,
                        "unit_id": unit_id,
                        "reason": "TOTAL_BUDGET_PRUNED",
                    }
                )
                pruning_sequence.append(
                    {
                        "candidate_id": candidate_id,
                        "unit_id": unit_id,
                        "reason": "TOTAL_BUDGET_PRUNED",
                    }
                )
            if not issues:
                status = "READY"

    per_capability: list[dict[str, Any]] = []
    selected_unit_ids: list[str] = []
    for definition in definitions:
        candidate_id = definition["candidate_id"]
        selected = selected_by_capability.get(candidate_id, [])
        selected_unit_ids.extend(selected)
        measured_bytes, context_hash = _content_bytes(definition, selected)
        required_ids = required_ids_by_capability.get(candidate_id, [])
        required_bytes, _ = _content_bytes(definition, required_ids)
        per_capability.append(
            {
                "candidate_id": candidate_id,
                "selected_unit_ids": selected,
                "required_unit_ids": required_ids,
                "utf8_bytes": measured_bytes,
                "required_only_utf8_bytes": required_bytes,
                "utf8_limit": per_limit,
                "context_sha256": context_hash,
            }
        )

    total_bytes, context_hash = _combined_bytes(definitions, selected_by_capability) if definitions else (0, hashlib.sha256(b"").hexdigest())
    result = {
        "planner_version": BUDGET_PLANNER_VERSION,
        "status": status,
        "issues": [issue.as_dict() for issue in issues],
        "per_capability": per_capability,
        "selected_unit_ids": selected_unit_ids,
        "excluded_units": sorted(excluded_units, key=lambda item: (item["candidate_id"], item["unit_id"], item["reason"])),
        "pruning_sequence": pruning_sequence,
        "total_utf8_bytes": total_bytes,
        "total_utf8_limit": total_limit,
        "tokenizer_id_or_null": budget["tokenizer_id_or_null"],
        "token_count_or_null": budget["token_count_or_null"],
        "unavailable_reason_or_null": budget["unavailable_reason_or_null"],
        "context_sha256": context_hash,
        "budget_plan_sha256": "0" * 64,
    }
    result["budget_plan_sha256"] = hash_without_field(result, "budget_plan_sha256")
    return result
