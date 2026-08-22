#!/usr/bin/env python3
"""Safe promotion and protected-regression helpers for V8.2 Skill governance."""

from __future__ import annotations

import hashlib
import json
import shutil
import uuid
from pathlib import Path
from typing import Any


class PromotionError(RuntimeError):
    """Raised when a candidate cannot be promoted safely."""


def package_hash(path: Path) -> str:
    if not path.exists() or not path.is_dir():
        raise PromotionError(f"Skill package missing: {path}")
    digest = hashlib.sha256()
    files = sorted(p for p in path.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    for file_path in files:
        relative = file_path.relative_to(path).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        data = file_path.read_bytes()
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(data)
    return "sha256:" + digest.hexdigest()


def validate_promotion_preconditions(
    active_dir: Path,
    *,
    expected_base_hash: str,
    validation_passed: bool,
    requires_human_gate: bool = False,
    human_gate_approved: bool = False,
) -> None:
    if not validation_passed:
        raise PromotionError("candidate validation did not PASS")
    if requires_human_gate and not human_gate_approved:
        raise PromotionError("required Human Gate has not been approved")
    current_hash = package_hash(active_dir)
    if current_hash != expected_base_hash:
        raise PromotionError(
            f"base hash mismatch: expected {expected_base_hash}, current {current_hash}"
        )


def promote_package(
    active_dir: Path,
    candidate_dir: Path,
    *,
    expected_base_hash: str,
    validation_passed: bool,
    requires_human_gate: bool = False,
    human_gate_approved: bool = False,
) -> str:
    """Replace an ACTIVE package only after all deterministic gates pass.

    The existing package is renamed to a temporary sibling backup and restored if
    the candidate rename fails. Preconditions run before any ACTIVE mutation.
    """

    validate_promotion_preconditions(
        active_dir,
        expected_base_hash=expected_base_hash,
        validation_passed=validation_passed,
        requires_human_gate=requires_human_gate,
        human_gate_approved=human_gate_approved,
    )
    if not candidate_dir.exists() or not candidate_dir.is_dir():
        raise PromotionError(f"candidate package missing: {candidate_dir}")

    parent = active_dir.parent
    token = uuid.uuid4().hex
    staged = parent / f".{active_dir.name}.candidate-{token}"
    backup = parent / f".{active_dir.name}.rollback-{token}"
    shutil.copytree(candidate_dir, staged)

    try:
        active_dir.rename(backup)
        try:
            staged.rename(active_dir)
        except Exception:
            if not active_dir.exists() and backup.exists():
                backup.rename(active_dir)
            raise
        shutil.rmtree(backup)
    except Exception as exc:
        if staged.exists():
            shutil.rmtree(staged, ignore_errors=True)
        if backup.exists() and not active_dir.exists():
            backup.rename(active_dir)
        raise PromotionError(f"candidate promotion failed: {exc}") from exc

    return package_hash(active_dir)


def load_protected_regressions(root: Path) -> dict[str, Any]:
    fixture_path = root / "evaluation" / "self-managing" / "protected-routing.json"
    policy_path = root / "capability-library" / "governance" / "policy.json"
    try:
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PromotionError(f"protected regression file missing: {exc.filename}") from exc
    except json.JSONDecodeError as exc:
        raise PromotionError(f"invalid protected regression JSON: {exc}") from exc

    if fixture.get("schema_version") != 1 or fixture.get("protected") is not True:
        raise PromotionError("protected regression marker missing or invalid")
    cases = fixture.get("cases")
    if not isinstance(cases, list):
        raise PromotionError("protected regression cases must be a list")
    ids = {
        item.get("id")
        for item in cases
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    required = policy.get("required_protected_case_ids")
    if not isinstance(required, list) or not all(isinstance(item, str) for item in required):
        raise PromotionError("governance policy required_protected_case_ids invalid")
    missing = set(required) - ids
    if missing:
        raise PromotionError("protected regression case(s) missing: " + ", ".join(sorted(missing)))
    return fixture
