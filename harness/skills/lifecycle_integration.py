#!/usr/bin/env python3
"""LLM-independent V8.2 lifecycle integration helpers.

Normal task execution only records one privacy-safe event after Codex exits.
Creator/Evolver/Curator remain maintenance-path operations and are never invoked
automatically by this module.
"""

from __future__ import annotations

import json
import secrets
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from events import EventError, EventStore, task_fingerprint, validate_event
from locking import skill_lock
from promotion import PromotionError, load_protected_regressions, package_hash, promote_package
from proposal import ProposalError, validate_proposal

HERE = Path(__file__).resolve()
HARNESS_ROOT = HERE.parents[1]
QUALITY_DIR = HARNESS_ROOT / "quality"
if str(QUALITY_DIR) not in sys.path:
    sys.path.insert(0, str(QUALITY_DIR))

from skill_audit import audit_candidate  # noqa: E402

CURATOR_PACKAGE_TYPES = {"compress", "extract-reference"}
STRUCTURAL_TYPES = {"split", "merge", "trigger-expand", "archive"}
PROMOTABLE_PACKAGE_TYPES = {"modify", *CURATOR_PACKAGE_TYPES}


class LifecycleIntegrationError(RuntimeError):
    """Raised when lifecycle integration cannot continue safely."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def build_task_event(
    *,
    task_text: str,
    skill_ids: list[str],
    codex_exit: int,
    user_correction: bool = False,
    event_id: str | None = None,
    timestamp: str | None = None,
) -> dict[str, Any]:
    """Build one privacy-safe post-task event without retaining raw task text."""
    if not isinstance(codex_exit, int):
        raise LifecycleIntegrationError("codex_exit must be an integer")
    if not all(isinstance(item, str) and item.strip() for item in skill_ids):
        raise LifecycleIntegrationError("skill_ids must be a string list")

    if user_correction:
        event_type = "user_correction"
        verification = "pass" if codex_exit == 0 else "fail"
        issue_code = "explicit-user-correction"
    elif skill_ids:
        event_type = "verified_usage" if codex_exit == 0 else "verification_failure"
        verification = "pass" if codex_exit == 0 else "fail"
        issue_code = "codex-exit-0" if codex_exit == 0 else "codex-exit-nonzero"
    else:
        event_type = "capability_gap"
        verification = "unknown"
        issue_code = "router-no-capability"

    event = {
        "event_id": event_id or f"task-{secrets.token_hex(8)}",
        "event_type": event_type,
        "task_fingerprint": task_fingerprint(task_text),
        "timestamp": timestamp or _utc_now(),
        "skill_ids": sorted(set(skill_ids)),
        "verification": verification,
        "user_correction": bool(user_correction),
        "issue_code": issue_code,
    }
    if event_type == "capability_gap":
        event["router_result"] = "NO_CAPABILITY"
        event["domain_hypothesis"] = "unclassified"
    try:
        validate_event(event)
    except EventError as exc:
        raise LifecycleIntegrationError(str(exc)) from exc
    return event


def record_task_event(
    *,
    state_root: Path,
    task_text: str,
    skill_ids: list[str],
    codex_exit: int,
    user_correction: bool = False,
) -> dict[str, Any]:
    """Best-effort event recording. Failure is returned, never raised."""
    try:
        state_root = state_root.resolve()
        if state_root.name != ".playbook-state":
            raise LifecycleIntegrationError("state_root must be a .playbook-state directory")
        event = build_task_event(
            task_text=task_text,
            skill_ids=skill_ids,
            codex_exit=codex_exit,
            user_correction=user_correction,
        )
        EventStore(state_root).append(event)
        return {
            "result": "EVENT_RECORDED",
            "event_id": event["event_id"],
            "event_type": event["event_type"],
        }
    except (OSError, ValueError, EventError, LifecycleIntegrationError) as exc:
        return {"result": "EVENT_RECORD_FAILED", "error": str(exc)}


def load_candidate_proposal(state_root: Path, proposal_id: str) -> tuple[Path, dict[str, Any]]:
    state_root = state_root.resolve()
    if state_root.name != ".playbook-state":
        raise LifecycleIntegrationError("state_root must be a .playbook-state directory")
    candidate_dir = state_root / "candidates" / proposal_id
    proposal_path = candidate_dir / "proposal.json"
    if not proposal_path.is_file():
        raise LifecycleIntegrationError(f"proposal not found: {proposal_id}")
    try:
        proposal = json.loads(proposal_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise LifecycleIntegrationError(f"invalid proposal JSON: {exc}") from exc
    if not isinstance(proposal, dict):
        raise LifecycleIntegrationError("proposal JSON root must be an object")
    try:
        validate_proposal(proposal)
    except ProposalError as exc:
        raise LifecycleIntegrationError(str(exc)) from exc
    if proposal.get("proposal_id") != proposal_id:
        raise LifecycleIntegrationError("proposal_id does not match Candidate directory")
    return candidate_dir, proposal


def list_candidates(state_root: Path) -> list[dict[str, Any]]:
    root = state_root.resolve() / "candidates"
    if not root.exists():
        return []
    items: list[dict[str, Any]] = []
    for path in sorted(p for p in root.iterdir() if p.is_dir()):
        proposal_path = path / "proposal.json"
        if not proposal_path.is_file():
            items.append({"proposal_id": path.name, "status": "INVALID", "path": str(path)})
            continue
        try:
            proposal = json.loads(proposal_path.read_text(encoding="utf-8"))
            validate_proposal(proposal)
        except (json.JSONDecodeError, ProposalError, OSError):
            items.append({"proposal_id": path.name, "status": "INVALID", "path": str(path)})
            continue
        items.append(
            {
                "proposal_id": proposal["proposal_id"],
                "change_type": proposal["change_type"],
                "skill_id": proposal["skill_id"],
                "requires_human_gate": proposal["requires_human_gate"],
                "status": proposal["status"],
                "path": str(path),
            }
        )
    return items


def _active_skill_dir(root: Path, skill_id: str) -> Path:
    registry_path = root / "capability-library" / "registry.json"
    try:
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LifecycleIntegrationError(f"invalid capability registry: {exc}") from exc
    for item in registry.get("capabilities", []):
        if isinstance(item, dict) and item.get("type") == "skill" and item.get("id") == skill_id:
            path = (root / str(item.get("path", ""))).resolve()
            if not path.is_dir():
                raise LifecycleIntegrationError(f"ACTIVE Skill package missing: {skill_id}")
            return path
    raise LifecycleIntegrationError(f"ACTIVE Skill not found: {skill_id}")


def run_protected_regression(
    root: Path,
    *,
    runner: Callable[..., Any] = subprocess.run,
) -> dict[str, Any]:
    """Run the protected Router suite with no semantic/LLM dependency."""
    root = root.resolve()
    load_protected_regressions(root)
    script = root / "harness" / "router" / "test_capability_router.py"
    if not script.is_file():
        installed = root / "playbook-harness" / "router" / "test_capability_router.py"
        script = installed if installed.is_file() else script
    if not script.is_file():
        raise LifecycleIntegrationError(f"protected router test missing: {script}")
    completed = runner(
        [sys.executable, str(script)],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    output = str(getattr(completed, "stdout", "") or "")
    code = int(completed.returncode)
    return {
        "result": "PASS" if code == 0 else "FAIL",
        "returncode": code,
        "output": output,
    }


def validate_candidate(
    *,
    root: Path,
    state_root: Path,
    proposal_id: str,
    run_regression: bool = True,
    regression_runner: Callable[..., Any] = subprocess.run,
) -> dict[str, Any]:
    candidate_dir, proposal = load_candidate_proposal(state_root, proposal_id)
    report = audit_candidate(candidate_dir, root=root)
    if report.result == "FAIL":
        return {
            "result": "VALIDATION_FAILED",
            "audit": report.as_dict(),
            "protected_regression": None,
        }

    regression = None
    if run_regression:
        try:
            regression = run_protected_regression(root, runner=regression_runner)
        except (PromotionError, LifecycleIntegrationError, OSError) as exc:
            return {
                "result": "VALIDATION_FAILED",
                "audit": report.as_dict(),
                "protected_regression": {"result": "FAIL", "error": str(exc)},
            }
        if regression["result"] != "PASS":
            return {
                "result": "VALIDATION_FAILED",
                "audit": report.as_dict(),
                "protected_regression": regression,
            }

    return {
        "result": "READY",
        "audit": report.as_dict(),
        "protected_regression": regression,
        "proposal": proposal,
    }


def _sanitized_candidate(candidate_dir: Path) -> tuple[tempfile.TemporaryDirectory[str], Path]:
    holder = tempfile.TemporaryDirectory(prefix="playbook-promote-")
    staged = Path(holder.name) / "package"
    shutil.copytree(candidate_dir, staged)
    for metadata in ("proposal.json", "routing.json"):
        path = staged / metadata
        if path.exists():
            path.unlink()
    return holder, staged


def promote_candidate(
    *,
    root: Path,
    state_root: Path,
    proposal_id: str,
    human_gate_approved: bool = False,
    regression_runner: Callable[..., Any] = subprocess.run,
) -> dict[str, Any]:
    """Promote only low-risk package Candidates through deterministic gates."""
    candidate_dir, proposal = load_candidate_proposal(state_root, proposal_id)
    change_type = str(proposal["change_type"])

    if proposal.get("requires_human_gate") and not human_gate_approved:
        return {"result": "HUMAN_GATE_REQUIRED"}
    if change_type in STRUCTURAL_TYPES:
        return {"result": "HUMAN_GATE_REQUIRED" if not human_gate_approved else "MANUAL_ONLY"}
    if change_type == "create":
        return {"result": "MANUAL_ONLY", "reason": "registry insertion is not automatic in V8.2"}
    if change_type not in PROMOTABLE_PACKAGE_TYPES:
        return {
            "result": "MANUAL_ONLY",
            "reason": f"automatic package promotion unsupported: {change_type}",
        }
    if proposal.get("trigger_delta", {}).get("add") or proposal.get("trigger_delta", {}).get("remove"):
        return {"result": "MANUAL_ONLY", "reason": "registry trigger mutation is not automatic"}
    if proposal.get("permission_delta", {}).get("add") or proposal.get("permission_delta", {}).get("remove"):
        return {"result": "MANUAL_ONLY", "reason": "registry permission mutation is not automatic"}

    validation = validate_candidate(
        root=root,
        state_root=state_root,
        proposal_id=proposal_id,
        run_regression=True,
        regression_runner=regression_runner,
    )
    if validation["result"] != "READY":
        return validation

    active_dir = _active_skill_dir(root.resolve(), str(proposal["skill_id"]))
    current_hash = package_hash(active_dir)
    if current_hash != proposal["base_hash"]:
        return {
            "result": "STALE_BASE",
            "current_hash": current_hash,
            "expected_hash": proposal["base_hash"],
        }

    with skill_lock(state_root.resolve(), str(proposal["skill_id"])):
        holder, staged = _sanitized_candidate(candidate_dir)
        try:
            new_hash = promote_package(
                active_dir,
                staged,
                expected_base_hash=str(proposal["base_hash"]),
                validation_passed=True,
                requires_human_gate=bool(proposal["requires_human_gate"]),
                human_gate_approved=human_gate_approved,
            )
        finally:
            holder.cleanup()

    return {"result": "PROMOTED", "new_hash": new_hash}


def scaling_registry_sizes() -> tuple[int, ...]:
    return (10, 50, 100, 500, 1000)
