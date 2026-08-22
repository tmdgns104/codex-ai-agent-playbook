#!/usr/bin/env python3
"""Materialize selected optional Skills into a task-scoped staging directory.

This module deliberately does not write to Codex Skill discovery paths. It stages
only eligible Skill bundles, records SHA256 evidence, and supports integrity
checking and managed cleanup.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any

ACTIVATION_DIR = Path(__file__).resolve().parent
if str(ACTIVATION_DIR) not in sys.path:
    sys.path.insert(0, str(ACTIVATION_DIR))

from capability_manager import build_activation_plan, load_capabilities  # noqa: E402

MANAGED_BY = "codex-ai-agent-playbook-v8.1"
SCHEMA_VERSION = 1
SESSION_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
PROFILE_RANK = {"minimal": 0, "standard": 1, "strict": 2}
MATERIALIZABLE_DECISIONS = {"AUTO_ALLOWED", "PROFILE_GATED"}


class MaterializationError(RuntimeError):
    """Raised when a staging operation would be unsafe or inconsistent."""


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def validate_session_id(session: str) -> None:
    if not SESSION_ID.fullmatch(session):
        raise MaterializationError(
            "unsafe session id; use 1-64 characters from A-Z, a-z, 0-9, dot, underscore, hyphen"
        )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _source_files(source_dir: Path) -> list[Path]:
    if source_dir.is_symlink():
        raise MaterializationError(f"source Skill directory must not be a symlink: {source_dir}")
    files: list[Path] = []
    for path in sorted(source_dir.rglob("*")):
        if path.is_symlink():
            raise MaterializationError(f"source Skill contains symlink: {path}")
        if path.is_file():
            files.append(path)
    if not files:
        raise MaterializationError(f"source Skill contains no files: {source_dir}")
    return files


def _skill_file_manifest(source_dir: Path, destination_dir: Path) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for source_file in _source_files(source_dir):
        relative = source_file.relative_to(source_dir)
        destination_file = destination_dir / relative
        if not destination_file.exists():
            raise MaterializationError(f"materialized file missing: {destination_file}")
        source_hash = sha256_file(source_file)
        destination_hash = sha256_file(destination_file)
        if source_hash != destination_hash:
            raise MaterializationError(f"hash mismatch after materialization: {relative.as_posix()}")
        entries.append(
            {
                "path": relative.as_posix(),
                "sha256": source_hash,
            }
        )
    return entries


def _can_materialize(plan_item: dict[str, Any], final_profile: str) -> tuple[bool, str]:
    if plan_item.get("type") != "skill":
        return False, "not-a-skill"

    decision = str(plan_item.get("decision", ""))
    if decision not in MATERIALIZABLE_DECISIONS:
        return False, f"decision:{decision}"

    if decision == "PROFILE_GATED" and PROFILE_RANK.get(final_profile, -1) < PROFILE_RANK["standard"]:
        return False, f"profile-too-weak:{final_profile}"

    return True, "eligible"


def prepare_session(
    *,
    root: Path,
    task_text: str,
    target_root: Path,
    session: str,
    catalog_root: Path | None = None,
) -> dict[str, Any]:
    """Stage only eligible selected Skills and return the written manifest payload."""
    validate_session_id(session)
    root = root.resolve()
    catalog_root = (catalog_root or root).resolve()
    target_root = target_root.resolve()
    session_dir = target_root / session

    if session_dir.exists():
        raise MaterializationError(f"session already exists: {session_dir}")

    capabilities = load_capabilities(catalog_root)
    by_id = {capability["id"]: capability for capability in capabilities}
    activation = build_activation_plan(task_text, capabilities)
    final_profile = str(activation["profile"]).lower()

    materializable: list[tuple[dict[str, Any], dict[str, Any]]] = []
    skipped: list[dict[str, str]] = []

    for plan_item in activation["plans"]:
        capability = by_id[plan_item["id"]]
        allowed, reason = _can_materialize(plan_item, final_profile)
        if allowed:
            materializable.append((plan_item, capability))
        else:
            skipped.append({"id": capability["id"], "reason": reason})

    if not materializable:
        return {
            "schema_version": SCHEMA_VERSION,
            "managed_by": MANAGED_BY,
            "session": session,
            "task": task_text,
            "profile": final_profile,
            "catalog_root": str(catalog_root),
            "selected": [item["id"] for item in activation["plans"]],
            "materialized": [],
            "skipped": skipped,
            "side_effects_executed": False,
            "staging_write_performed": False,
            "codex_discovery_ready": False,
            "result": "NO_MATERIALIZATION",
        }

    library_root = (catalog_root / "capability-library").resolve()
    skills_dir = session_dir / "skills"
    manifest: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "managed_by": MANAGED_BY,
        "session": session,
        "task": task_text,
        "profile": final_profile,
        "catalog_root": str(catalog_root),
        "selected": [item["id"] for item in activation["plans"]],
        "materialized": [],
        "skipped": skipped,
        "side_effects_executed": False,
        "staging_write_performed": True,
        "codex_discovery_ready": False,
        "result": "PREPARED",
    }

    try:
        skills_dir.mkdir(parents=True, exist_ok=False)

        for plan_item, capability in materializable:
            source_dir = (catalog_root / str(capability["path"])).resolve()
            if not _is_within(source_dir, library_root):
                raise MaterializationError(f"source path escaped capability library: {source_dir}")
            if not source_dir.is_dir():
                raise MaterializationError(f"source Skill directory missing: {source_dir}")

            destination_dir = skills_dir / capability["id"]
            shutil.copytree(source_dir, destination_dir, symlinks=False)
            files = _skill_file_manifest(source_dir, destination_dir)
            manifest["materialized"].append(
                {
                    "id": capability["id"],
                    "decision": plan_item["decision"],
                    "source": source_dir.relative_to(catalog_root).as_posix(),
                    "destination": destination_dir.relative_to(session_dir).as_posix(),
                    "files": files,
                }
            )

        (session_dir / "activation.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except Exception:
        if session_dir.exists():
            shutil.rmtree(session_dir)
        raise

    return manifest


def _load_managed_manifest(target_root: Path, session: str) -> tuple[Path, dict[str, Any]]:
    validate_session_id(session)
    target_root = target_root.resolve()
    session_dir = target_root / session
    manifest_path = session_dir / "activation.json"
    if not manifest_path.is_file():
        raise MaterializationError(f"managed activation manifest missing: {manifest_path}")

    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise MaterializationError(f"invalid activation manifest: {exc}") from exc

    if payload.get("managed_by") != MANAGED_BY:
        raise MaterializationError("refusing operation on unmanaged session")
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise MaterializationError("unsupported activation manifest schema")
    if payload.get("session") != session:
        raise MaterializationError("activation manifest session mismatch")
    return session_dir, payload


def verify_session(*, target_root: Path, session: str) -> dict[str, Any]:
    session_dir, payload = _load_managed_manifest(target_root, session)
    errors: list[str] = []

    for skill in payload.get("materialized", []):
        destination = session_dir / str(skill.get("destination", ""))
        if not _is_within(destination.resolve(), session_dir.resolve()):
            errors.append(f"destination escaped session: {skill.get('id')}")
            continue

        expected_files = {str(item["path"]): str(item["sha256"]) for item in skill.get("files", [])}
        actual_files: dict[str, str] = {}
        if destination.is_dir():
            for path in sorted(destination.rglob("*")):
                if path.is_symlink():
                    errors.append(f"symlink found in materialized Skill: {path}")
                    continue
                if path.is_file():
                    relative = path.relative_to(destination).as_posix()
                    actual_files[relative] = sha256_file(path)
        else:
            errors.append(f"materialized Skill directory missing: {skill.get('id')}")
            continue

        if set(actual_files) != set(expected_files):
            errors.append(f"file set drift: {skill.get('id')}")
            continue
        for relative, expected_hash in expected_files.items():
            if actual_files.get(relative) != expected_hash:
                errors.append(f"hash drift: {skill.get('id')}/{relative}")

    if errors:
        raise MaterializationError("; ".join(errors))

    return {
        "session": session,
        "profile": payload.get("profile"),
        "materialized_count": len(payload.get("materialized", [])),
        "result": "INTEGRITY_PASS",
        "codex_discovery_ready": bool(payload.get("codex_discovery_ready", False)),
    }


def cleanup_session(*, target_root: Path, session: str) -> dict[str, Any]:
    session_dir, payload = _load_managed_manifest(target_root, session)
    materialized_count = len(payload.get("materialized", []))
    shutil.rmtree(session_dir)
    return {
        "session": session,
        "removed": True,
        "materialized_count": materialized_count,
        "result": "CLEANED",
    }


def _print_prepare(payload: dict[str, Any]) -> None:
    print("Codex Playbook Optional Skill Materializer")
    print(f"Session: {payload['session']}")
    print(f"Task: {payload['task']}")
    print()
    for item in payload["materialized"]:
        print(f"MATERIALIZE {item['id']:<24} {item['decision']}")
    for item in payload["skipped"]:
        print(f"SKIP        {item['id']:<24} {item['reason']}")
    print()
    print(f"PROFILE     {str(payload['profile']).upper()}")
    print(f"COUNT       {len(payload['materialized'])}")
    print(f"DISCOVERY   {str(payload['codex_discovery_ready']).lower()}")
    print(f"CAP_SIDEFX  {str(payload['side_effects_executed']).lower()}")
    print(f"RESULT      {payload['result']}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage, verify, and clean task-scoped optional Skills.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare = subparsers.add_parser("prepare")
    prepare.add_argument("--root", default=".", help="Target repository root.")
    prepare.add_argument("--catalog-root", help="Optional Playbook catalog root; defaults to --root.")
    prepare.add_argument("--task", required=True)
    prepare.add_argument("--target", default=".playbook-runtime")
    prepare.add_argument("--session", required=True)
    prepare.add_argument("--json", action="store_true")

    status = subparsers.add_parser("status")
    status.add_argument("--target", default=".playbook-runtime")
    status.add_argument("--session", required=True)
    status.add_argument("--json", action="store_true")

    cleanup = subparsers.add_parser("cleanup")
    cleanup.add_argument("--target", default=".playbook-runtime")
    cleanup.add_argument("--session", required=True)
    cleanup.add_argument("--json", action="store_true")

    args = parser.parse_args()

    try:
        if args.command == "prepare":
            payload = prepare_session(
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
            payload = verify_session(target_root=Path(args.target), session=args.session)
            if args.json:
                print(json.dumps(payload, ensure_ascii=False, indent=2))
            else:
                print(f"SESSION     {payload['session']}")
                print(f"COUNT       {payload['materialized_count']}")
                print(f"DISCOVERY   {str(payload['codex_discovery_ready']).lower()}")
                print(f"RESULT      {payload['result']}")
            return 0

        payload = cleanup_session(target_root=Path(args.target), session=args.session)
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(f"SESSION     {payload['session']}")
            print(f"REMOVED     {str(payload['removed']).lower()}")
            print(f"RESULT      {payload['result']}")
        return 0
    except (MaterializationError, ValueError, OSError) as exc:
        if getattr(args, "json", False):
            print(json.dumps({"result": "FAIL", "error": str(exc)}, ensure_ascii=False))
        else:
            print(f"FAIL        {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
