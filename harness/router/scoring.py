#!/usr/bin/env python3
"""Deterministic metadata scoring for V8.1 capability routing."""

from __future__ import annotations

import re
from typing import Any

TOKEN_RE = re.compile(r"[0-9A-Za-z가-힣]+")
HANGUL_RE = re.compile(r"^[가-힣]+$")

KOREAN_PARTICLES = {
    "은",
    "는",
    "이",
    "가",
    "을",
    "를",
    "에",
    "에서",
    "로",
    "으로",
    "과",
    "와",
    "의",
    "도",
    "만",
    "부터",
    "까지",
}

CONTEXT_PENALTY = {"low": 0, "medium": 1, "high": 2}
ACTIVATION_PENALTY = {"on_demand": 0, "conditional": 1, "manual": 3}
TYPE_THRESHOLD = {
    "skill": 5,
    "cli-wrapper": 6,
    "rest-wrapper": 6,
    "mcp": 10,
    "agent": 12,
}
CONTEXT_RANK = {"low": 0, "medium": 1, "high": 2}
RISK_RANK = {"low": 0, "medium": 1, "high": 2, "critical": 3}
PROFILE_RANK = {"minimal": 0, "standard": 1, "strict": 2}
SENSITIVE_PERMISSIONS = {
    "credential_access",
    "external_write",
    "database_write",
    "destructive",
    "production",
}
STOPWORDS = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "to",
    "of",
    "for",
    "in",
    "on",
    "with",
    "current",
    "using",
    "use",
    "작업",
    "현재",
    "사용",
    "수정",
    "확인",
    "통해",
    "위한",
    "하고",
    "에서",
}


def tokens(text: str) -> list[str]:
    return [token.casefold() for token in TOKEN_RE.findall(text)]


def normalized_phrase(text: str) -> str:
    return " ".join(tokens(text))


def _matches_korean_particle_suffix(task_token: str, trigger_token: str) -> bool:
    """Allow a trigger token followed only by a known Korean particle.

    This supports Korean task text such as ``오류를`` or mixed tokens such as
    ``test를`` without weakening normal ASCII word boundaries (for example,
    ``pr`` must not match ``problem``).
    """

    if not task_token.startswith(trigger_token) or task_token == trigger_token:
        return False
    suffix = task_token[len(trigger_token) :]
    return suffix in KOREAN_PARTICLES


def contains_phrase(task_normalized: str, phrase: str) -> bool:
    normalized = normalized_phrase(phrase)
    if not normalized:
        return False

    if f" {normalized} " in f" {task_normalized} ":
        return True

    phrase_tokens = normalized.split()
    if len(phrase_tokens) != 1:
        return False

    trigger_token = phrase_tokens[0]
    for task_token in task_normalized.split():
        if _matches_korean_particle_suffix(task_token, trigger_token):
            return True

    return False


def score_capability(task_text: str, capability: dict[str, Any]) -> dict[str, Any]:
    task_normalized = normalized_phrase(task_text)
    task_tokens = set(tokens(task_text))

    matched_triggers = [
        trigger for trigger in capability.get("triggers", []) if contains_phrase(task_normalized, trigger)
    ]
    trigger_score = min(len(matched_triggers), 3) * 6

    matched_domains = [
        domain for domain in capability.get("domains", []) if contains_phrase(task_normalized, domain)
    ]
    domain_score = min(len(matched_domains), 2) * 3

    summary_tokens = {
        token for token in tokens(str(capability.get("summary", ""))) if token not in STOPWORDS and len(token) > 1
    }
    summary_overlap = sorted(task_tokens & summary_tokens)
    summary_score = min(len(summary_overlap), 3)

    context_penalty = CONTEXT_PENALTY.get(str(capability.get("context_cost", "high")), 2)
    activation_penalty = ACTIVATION_PENALTY.get(str(capability.get("activation", "manual")), 3)

    score = trigger_score + domain_score + summary_score - context_penalty - activation_penalty
    threshold = TYPE_THRESHOLD.get(str(capability.get("type", "agent")), 12)
    permissions = set(capability.get("permissions", []))
    approval = "required" if permissions & SENSITIVE_PERMISSIONS else "none"

    return {
        "id": capability["id"],
        "type": capability["type"],
        "score": score,
        "threshold": threshold,
        "eligible": score >= threshold,
        "profile": capability["recommended_profile"],
        "approval": approval,
        "context_cost": capability["context_cost"],
        "risk": capability["risk"],
        "matched_triggers": matched_triggers,
        "matched_domains": matched_domains,
        "summary_overlap": summary_overlap,
    }


def ranking_key(item: dict[str, Any]) -> tuple[Any, ...]:
    return (
        -int(item["score"]),
        CONTEXT_RANK.get(str(item["context_cost"]), 99),
        RISK_RANK.get(str(item["risk"]), 99),
        str(item["id"]),
    )


def strongest_profile(selected: list[dict[str, Any]]) -> str:
    if not selected:
        return "minimal"
    return max(
        (str(item["profile"]) for item in selected),
        key=lambda profile: PROFILE_RANK.get(profile, -1),
    )
