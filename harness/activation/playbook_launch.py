#!/usr/bin/env python3
"""One-command Codex launcher with deterministic automatic Skill selection.

The launcher reuses the verified V8.1 router, activation policy, and discovery
bridge. Users provide only the task. Eligible Skills are selected automatically,
exposed for the new Codex session, and cleaned up after Codex exits.
"""

from __future__ import annotations

import argparse
import secrets
import subprocess
from pathlib import Path
from typing import Any, Callable

from capability_manager import build_activation_plan, load_capabilities
from discovery_bridge import (
    DiscoveryBridgeError,
    cleanup_bridge,
    format_launch_command,
    prepare_bridge,
)

BLOCKING_RESULTS = {
    "human": "HUMAN_GATE_REQUIRED",
    "manual": "MANUAL_ONLY",
    "network": "NETWORK_REVIEW_REQUIRED",
}


def generate_session_id() -> str:
    return f"launch-{secrets.token_hex(4)}"


def resolve_target(root: Path, target: Path) -> Path:
    root = root.resolve()
    if target.is_absolute():
        return target.resolve()
    return (root / target).resolve()


def _blocking_result(activation: dict[str, Any]) -> str | None:
    gates = activation.get("gates", {})
    for gate_name in ("human", "manual", "network"):
        if int(gates.get(gate_name, 0)) > 0:
            return BLOCKING_RESULTS[gate_name]
    return None


def build_launch_plan(
    *,
    root: Path,
    task_text: str,
    target_root: Path,
    session: str,
) -> dict[str, Any]:
    """Build the launch plan and prepare a bridge only when eligible Skills exist."""
    root = root.resolve()
    target_root = resolve_target(root, target_root)
    capabilities = load_capabilities(root)
    activation = build_activation_plan(task_text, capabilities)
    blocker = _blocking_result(activation)

    if blocker is not None:
        return {
            "session": session,
            "task": task_text,
            "profile": str(activation["profile"]).lower(),
            "skills": [],
            "count": 0,
            "bridge": False,
            "target_root": str(target_root),
            "argv": [],
            "result": blocker,
        }

    bridge = prepare_bridge(
        root=root,
        task_text=task_text,
        target_root=target_root,
        session=session,
    )

    if bridge["result"] == "BRIDGE_READY":
        base_argv = list(bridge["launch_argv"])
        skills = list(bridge.get("materialized", []))
        bridge_created = True
    else:
        base_argv = ["codex", "-C", str(root)]
        skills = []
        bridge_created = False

    # `--` prevents task text that begins with '-' from being interpreted as a
    # Codex option. The exact user task is passed once as the positional prompt.
    argv = base_argv + ["--", task_text]

    return {
        "session": session,
        "task": task_text,
        "profile": str(activation["profile"]).lower(),
        "skills": skills,
        "count": len(skills),
        "bridge": bridge_created,
        "target_root": str(target_root),
        "argv": argv,
        "result": "READY",
    }


def _cleanup_if_needed(plan: dict[str, Any], *, keep_runtime: bool) -> str:
    if not plan.get("bridge"):
        return "NOT_NEEDED"
    if keep_runtime:
        return "KEPT"
    cleaned = cleanup_bridge(
        target_root=Path(str(plan["target_root"])),
        session=str(plan["session"]),
    )
    return str(cleaned["result"])


def execute_launch(
    plan: dict[str, Any],
    *,
    dry_run: bool = False,
    keep_runtime: bool = False,
    runner: Callable[..., Any] = subprocess.run,
) -> dict[str, Any]:
    """Execute a READY plan without shell interpolation and clean managed runtime."""
    if plan.get("result") != "READY":
        return {
            "result": str(plan.get("result", "BLOCKED")),
            "codex_exit": None,
            "cleanup": "NOT_NEEDED",
        }

    if dry_run:
        cleanup = _cleanup_if_needed(plan, keep_runtime=keep_runtime)
        return {
            "result": "DRY_RUN_COMPLETE",
            "codex_exit": None,
            "cleanup": cleanup,
        }

    exit_code = 1
    cleanup = "NOT_NEEDED"
    launch_error: str | None = None
    try:
        completed = runner(list(plan["argv"]), check=False)
        exit_code = int(completed.returncode)
    except KeyboardInterrupt:
        exit_code = 130
    except OSError as exc:
        launch_error = str(exc)
        exit_code = 1
    finally:
        try:
            cleanup = _cleanup_if_needed(plan, keep_runtime=keep_runtime)
        except (DiscoveryBridgeError, OSError) as exc:
            cleanup = f"FAIL:{exc}"
            if exit_code == 0:
                exit_code = 1

    return {
        "result": "COMPLETE" if exit_code == 0 and not cleanup.startswith("FAIL:") else "FAIL",
        "codex_exit": exit_code,
        "cleanup": cleanup,
        "error": launch_error,
    }


def print_plan(plan: dict[str, Any], *, dry_run: bool) -> None:
    print("Codex Playbook Auto Skill Launcher")
    print(f"Session: {plan['session']}")
    print(f"Task: {plan['task']}")
    print()
    print(f"PROFILE     {str(plan['profile']).upper()}")
    print(f"SKILLS      {','.join(plan['skills']) if plan['skills'] else 'none'}")
    print(f"COUNT       {plan['count']}")
    print(f"BRIDGE      {str(bool(plan['bridge'])).lower()}")
    print(f"DRY_RUN     {str(dry_run).lower()}")
    print(f"RESULT      {plan['result']}")
    if plan.get("argv"):
        print(f"COMMAND     {format_launch_command(list(plan['argv']))}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Automatically select only needed Skills and launch Codex once."
    )
    parser.add_argument("--root", default=".", help="Repository root.")
    parser.add_argument("--task", required=True, help="Task passed once to Codex as the initial prompt.")
    parser.add_argument("--target", default=".playbook-runtime", help="Managed runtime directory under the repository.")
    parser.add_argument("--session", help="Optional safe session id. Generated automatically when omitted.")
    parser.add_argument("--dry-run", action="store_true", help="Plan and print argv without starting Codex.")
    parser.add_argument("--keep-runtime", action="store_true", help="Keep managed bridge after dry-run/exit for debugging.")
    args = parser.parse_args()

    session = args.session or generate_session_id()
    root = Path(args.root).resolve()

    try:
        plan = build_launch_plan(
            root=root,
            task_text=args.task,
            target_root=Path(args.target),
            session=session,
        )
        print_plan(plan, dry_run=args.dry_run)

        if plan["result"] != "READY":
            return 2

        result = execute_launch(
            plan,
            dry_run=args.dry_run,
            keep_runtime=args.keep_runtime,
        )
        print()
        if result["codex_exit"] is not None:
            print(f"CODEX_EXIT  {result['codex_exit']}")
        print(f"CLEANUP     {result['cleanup']}")
        print(f"RESULT      {result['result']}")
        if result.get("error"):
            print(f"ERROR       {result['error']}")

        if result["result"] == "DRY_RUN_COMPLETE":
            return 0
        return int(result["codex_exit"] or 0) if result["result"] == "COMPLETE" else int(result["codex_exit"] or 1)
    except (DiscoveryBridgeError, ValueError, OSError) as exc:
        print(f"FAIL        {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
