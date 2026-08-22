#!/usr/bin/env python3
"""Prepare a task-scoped Codex Skill discovery bridge for a new session.

The bridge never launches Codex and never modifies global or repository-root
Skill directories. It materializes eligible optional Skills using the verified
CAP-005 materializer, then relocates that managed copy under a session-local
`cwd/.agents/skills` directory that current Codex discovery rules can scan when
Codex is started with `-C <bridge-cwd>`.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Any

from skill_materializer import (
    MANAGED_BY,
    MaterializationError,
    cleanup_session,
    prepare_session,
    validate_session_id,
    verify_session,
)

BRIDGE_MANAGED_BY = "codex-ai-agent-playbook-v8.1-discovery-bridge"
BRIDGE_SCHEMA_VERSION = 1
BRIDGE_FILENAME = "bridge.json"


class DiscoveryBridgeError(RuntimeError):
    """Raised when a discovery bridge operation is unsafe or inconsistent."""


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _require_git_root(root: Path) -> Path:
    root = root.resolve()
    if not (root / ".git").exists():
        raise DiscoveryBridgeError(f"repository root must contain .git: {root}")
    return root


def _require_target_inside_repo(root: Path, target_root: Path) -> Path:
    target_root = target_root.resolve()
    if target_root == root or not _is_within(target_root, root):
        raise DiscoveryBridgeError("bridge target must be a dedicated directory inside repository root")
    return target_root


def _activation_manifest_path(session_dir: Path) -> Path:
    return session_dir / "activation.json"


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise DiscoveryBridgeError(f"manifest missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise DiscoveryBridgeError(f"invalid JSON manifest {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise DiscoveryBridgeError(f"manifest must contain a JSON object: {path}")
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _rewrite_activation_destinations(session_dir: Path) -> dict[str, Any]:
    activation_path = _activation_manifest_path(session_dir)
    payload = _load_json(activation_path)
    if payload.get("managed_by") != MANAGED_BY:
        raise DiscoveryBridgeError("activation manifest is not managed by this playbook")

    for item in payload.get("materialized", []):
        destination = str(item.get("destination", ""))
        prefix = "skills/"
        if not destination.startswith(prefix):
            raise DiscoveryBridgeError(f"unexpected CAP-005 destination: {destination}")
        item["destination"] = "cwd/.agents/skills/" + destination[len(prefix) :]

    payload["codex_discovery_ready"] = True
    _write_json(activation_path, payload)
    return payload


def _launch_argv(root: Path, bridge_cwd: Path) -> list[str]:
    return ["codex", "-C", str(bridge_cwd), "--add-dir", str(root)]


def format_launch_command(argv: list[str]) -> str:
    if os.name == "nt":
        return subprocess.list2cmdline(argv)
    return shlex.join(argv)


def prepare_bridge(
    *,
    root: Path,
    task_text: str,
    target_root: Path,
    session: str,
    catalog_root: Path | None = None,
) -> dict[str, Any]:
    """Prepare selected Skills under a Codex-discoverable session-local cwd."""
    validate_session_id(session)
    root = _require_git_root(root)
    catalog_root = (catalog_root or root).resolve()
    target_root = _require_target_inside_repo(root, target_root)
    session_dir = target_root / session

    try:
        activation = prepare_session(
            root=root,
            catalog_root=catalog_root,
            task_text=task_text,
            target_root=target_root,
            session=session,
        )
    except MaterializationError as exc:
        raise DiscoveryBridgeError(str(exc)) from exc

    if activation.get("result") == "NO_MATERIALIZATION":
        return {
            "schema_version": BRIDGE_SCHEMA_VERSION,
            "managed_by": BRIDGE_MANAGED_BY,
            "session": session,
            "task": task_text,
            "catalog_root": str(catalog_root),
            "materialized": [],
            "codex_discovery_ready": False,
            "result": "NO_BRIDGE",
        }

    source_skill_root = session_dir / "skills"
    bridge_cwd = session_dir / "cwd"
    bridge_skill_root = bridge_cwd / ".agents" / "skills"

    try:
        if not source_skill_root.is_dir():
            raise DiscoveryBridgeError("CAP-005 materialized Skill root missing")
        bridge_skill_root.parent.mkdir(parents=True, exist_ok=False)
        shutil.move(str(source_skill_root), str(bridge_skill_root))
        activation = _rewrite_activation_destinations(session_dir)

        materialized = [str(item["id"]) for item in activation.get("materialized", [])]
        argv = _launch_argv(root, bridge_cwd)
        bridge = {
            "schema_version": BRIDGE_SCHEMA_VERSION,
            "managed_by": BRIDGE_MANAGED_BY,
            "session": session,
            "task": task_text,
            "repository_root": str(root),
            "catalog_root": str(catalog_root),
            "bridge_cwd": str(bridge_cwd),
            "skill_root": str(bridge_skill_root),
            "materialized": materialized,
            "codex_discovery_ready": True,
            "launch_argv": argv,
            "result": "BRIDGE_READY",
        }
        _write_json(session_dir / BRIDGE_FILENAME, bridge)
        return bridge
    except Exception:
        if session_dir.exists():
            shutil.rmtree(session_dir)
        raise


def _load_bridge(target_root: Path, session: str) -> tuple[Path, dict[str, Any]]:
    validate_session_id(session)
    target_root = target_root.resolve()
    session_dir = target_root / session
    bridge = _load_json(session_dir / BRIDGE_FILENAME)
    if bridge.get("managed_by") != BRIDGE_MANAGED_BY:
        raise DiscoveryBridgeError("refusing operation on unmanaged discovery bridge")
    if bridge.get("schema_version") != BRIDGE_SCHEMA_VERSION:
        raise DiscoveryBridgeError("unsupported discovery bridge schema")
    if bridge.get("session") != session:
        raise DiscoveryBridgeError("discovery bridge session mismatch")
    return session_dir, bridge


def verify_bridge(*, target_root: Path, session: str) -> dict[str, Any]:
    session_dir, bridge = _load_bridge(target_root, session)
    try:
        integrity = verify_session(target_root=target_root, session=session)
    except MaterializationError as exc:
        raise DiscoveryBridgeError(str(exc)) from exc

    bridge_cwd = Path(str(bridge.get("bridge_cwd", ""))).resolve()
    skill_root = Path(str(bridge.get("skill_root", ""))).resolve()
    expected_cwd = (session_dir / "cwd").resolve()
    expected_skill_root = (expected_cwd / ".agents" / "skills").resolve()

    if bridge_cwd != expected_cwd:
        raise DiscoveryBridgeError("bridge cwd drift")
    if skill_root != expected_skill_root:
        raise DiscoveryBridgeError("bridge skill root drift")
    if not skill_root.is_dir():
        raise DiscoveryBridgeError("bridge skill root missing")

    discovered_dirs = sorted(path.name for path in skill_root.iterdir() if path.is_dir())
    expected_ids = sorted(str(item) for item in bridge.get("materialized", []))
    if discovered_dirs != expected_ids:
        raise DiscoveryBridgeError("bridge Skill directory set drift")

    activation = _load_json(_activation_manifest_path(session_dir))
    activation_ids = sorted(str(item.get("id")) for item in activation.get("materialized", []))
    if activation_ids != expected_ids:
        raise DiscoveryBridgeError("bridge and activation materialized ids differ")
    if not activation.get("codex_discovery_ready"):
        raise DiscoveryBridgeError("activation manifest does not mark discovery ready")

    argv = bridge.get("launch_argv")
    expected_argv = _launch_argv(Path(str(bridge["repository_root"])).resolve(), expected_cwd)
    if argv != expected_argv:
        raise DiscoveryBridgeError("launch argv drift")

    return {
        "session": session,
        "materialized": expected_ids,
        "count": len(expected_ids),
        "integrity": integrity["result"],
        "codex_discovery_ready": True,
        "result": "DISCOVERY_READY",
    }


def bridge_command(*, target_root: Path, session: str) -> dict[str, Any]:
    _, bridge = _load_bridge(target_root, session)
    argv = bridge.get("launch_argv")
    if not isinstance(argv, list) or not all(isinstance(item, str) and item for item in argv):
        raise DiscoveryBridgeError("invalid launch argv in bridge manifest")
    return {
        "session": session,
        "argv": argv,
        "command": format_launch_command(argv),
        "result": "COMMAND_READY",
    }


def cleanup_bridge(*, target_root: Path, session: str) -> dict[str, Any]:
    _load_bridge(target_root, session)
    try:
        cleaned = cleanup_session(target_root=target_root, session=session)
    except MaterializationError as exc:
        raise DiscoveryBridgeError(str(exc)) from exc
    return {
        "session": session,
        "removed": bool(cleaned["removed"]),
        "materialized_count": int(cleaned["materialized_count"]),
        "result": "BRIDGE_CLEANED",
    }


def _print_prepare(payload: dict[str, Any]) -> None:
    print("Codex Playbook Pre-session Discovery Bridge")
    print(f"Session: {payload['session']}")
    print(f"Task: {payload['task']}")
    print()
    for capability_id in payload.get("materialized", []):
        print(f"DISCOVER    {capability_id}")
    print()
    print(f"COUNT       {len(payload.get('materialized', []))}")
    print(f"DISCOVERY   {str(payload['codex_discovery_ready']).lower()}")
    print(f"RESULT      {payload['result']}")
    if payload.get("launch_argv"):
        print(f"COMMAND     {format_launch_command(payload['launch_argv'])}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare and verify a pre-session Codex Skill discovery bridge.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare = subparsers.add_parser("prepare")
    prepare.add_argument("--root", default=".")
    prepare.add_argument("--catalog-root", help="Optional Playbook catalog root; defaults to --root.")
    prepare.add_argument("--task", required=True)
    prepare.add_argument("--target", default=".playbook-runtime")
    prepare.add_argument("--session", required=True)
    prepare.add_argument("--json", action="store_true")

    status = subparsers.add_parser("status")
    status.add_argument("--target", default=".playbook-runtime")
    status.add_argument("--session", required=True)
    status.add_argument("--json", action="store_true")

    command = subparsers.add_parser("command")
    command.add_argument("--target", default=".playbook-runtime")
    command.add_argument("--session", required=True)
    command.add_argument("--json", action="store_true")

    cleanup = subparsers.add_parser("cleanup")
    cleanup.add_argument("--target", default=".playbook-runtime")
    cleanup.add_argument("--session", required=True)
    cleanup.add_argument("--json", action="store_true")

    args = parser.parse_args()

    try:
        if args.command == "prepare":
            payload = prepare_bridge(
                root=Path(args.root),
                catalog_root=Path(args.catalog_root) if args.catalog_root else None,
                task_text=args.task,
                target_root=Path(args.target),
                session=args.session,
            )
            if args.json:
                print(json.dumps(payload, ensure_ascii=False, indent=2))
            else:
                _print_prepare(payload)
            return 0

        if args.command == "status":
            payload = verify_bridge(target_root=Path(args.target), session=args.session)
            if args.json:
                print(json.dumps(payload, ensure_ascii=False, indent=2))
            else:
                print(f"SESSION     {payload['session']}")
                print(f"COUNT       {payload['count']}")
                print(f"INTEGRITY   {payload['integrity']}")
                print(f"DISCOVERY   {str(payload['codex_discovery_ready']).lower()}")
                print(f"RESULT      {payload['result']}")
            return 0

        if args.command == "command":
            payload = bridge_command(target_root=Path(args.target), session=args.session)
            if args.json:
                print(json.dumps(payload, ensure_ascii=False, indent=2))
            else:
                print(f"SESSION     {payload['session']}")
                print(f"COMMAND     {payload['command']}")
                print(f"RESULT      {payload['result']}")
            return 0

        payload = cleanup_bridge(target_root=Path(args.target), session=args.session)
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(f"SESSION     {payload['session']}")
            print(f"REMOVED     {str(payload['removed']).lower()}")
            print(f"COUNT       {payload['materialized_count']}")
            print(f"RESULT      {payload['result']}")
        return 0
    except (DiscoveryBridgeError, MaterializationError, ValueError, OSError) as exc:
        if getattr(args, "json", False):
            print(json.dumps({"result": "FAIL", "error": str(exc)}, ensure_ascii=False))
        else:
            print(f"FAIL        {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
