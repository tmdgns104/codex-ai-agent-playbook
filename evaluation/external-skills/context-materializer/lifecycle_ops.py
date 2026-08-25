"""Cleanup and quarantine operations constrained to one materialized session."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Callable

from artifact_safety import (
    ArtifactSafetyError,
    load_json_object,
    make_owner_writable,
    relative_files,
    replace_json,
    safe_relative_path,
    sha256_file,
    validate_session_location,
)
from context_contract import canonical_json_bytes, canonical_sha256
from lifecycle import LifecycleError, create_lifecycle, transition, validate_lifecycle


def _artifact_hashes(session_root: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    try:
        files = relative_files(session_root)
    except ArtifactSafetyError as exc:
        return {"unreadable": hashlib.sha256(str(exc).encode("utf-8")).hexdigest()}
    for relative in files:
        if relative in {"quarantine.json"}:
            continue
        path = safe_relative_path(session_root, relative)
        try:
            hashes[relative] = sha256_file(path)
        except OSError:
            hashes[relative] = "UNREADABLE"
    return hashes


def quarantine_session(
    *,
    repository_root: Path,
    sessions_root: Path,
    session_id: str,
    reason: str,
    timestamp_utc: str,
    request_hash_or_null: str | None,
    source_hashes: list[str] | None,
    invalidated: bool = False,
) -> dict[str, Any]:
    """Record evidence in the affected session without moving or deleting it."""
    repository, _, session = validate_session_location(
        repository_root,
        sessions_root,
        session_id,
        require_new=False,
    )
    if not session.is_dir():
        evidence = {
            "session_id": session_id,
            "reason": reason,
            "artifact_hash": canonical_sha256({}),
            "timestamp_utc": timestamp_utc,
            "source_hashes": source_hashes or [],
            "request_hash_or_null": request_hash_or_null,
            "record_location": "IN_MEMORY_ONLY_UNSAFE_PATH_NOT_CREATED",
        }
        return {"status": "QUARANTINED", "state": "QUARANTINED", "quarantine": evidence}

    hashes = _artifact_hashes(session)
    lifecycle_path = session / "lifecycle.json"
    lifecycle_valid = True
    try:
        lifecycle = load_json_object(lifecycle_path)
        validate_lifecycle(lifecycle)
    except (ArtifactSafetyError, LifecycleError):
        lifecycle_valid = False
        lifecycle = create_lifecycle(session_id, timestamp_utc)

    if lifecycle_valid:
        try:
            if invalidated and lifecycle["state"] not in {"INVALIDATED", "QUARANTINED"}:
                lifecycle = transition(
                    lifecycle,
                    "INVALIDATED",
                    reason="STALE_OR_INVALIDATED_ARTIFACT",
                    timestamp_utc=timestamp_utc,
                )
            if lifecycle["state"] != "QUARANTINED":
                lifecycle = transition(
                    lifecycle,
                    "QUARANTINED",
                    reason=reason,
                    timestamp_utc=timestamp_utc,
                )
            replace_json(lifecycle_path, lifecycle, canonical_json_bytes)
        except (LifecycleError, ArtifactSafetyError):
            lifecycle_valid = False

    quarantine = {
        "schema_version": 1,
        "session_id": session_id,
        "reason": reason,
        "artifact_hash": canonical_sha256(hashes),
        "artifact_hashes": hashes,
        "timestamp_utc": timestamp_utc,
        "source_hashes": source_hashes or [],
        "request_hash_or_null": request_hash_or_null,
        "session_relative_path": session.relative_to(repository).as_posix(),
        "lifecycle_record_updated": lifecycle_valid,
        "automatic_recovery_allowed": False,
    }
    replace_json(session / "quarantine.json", quarantine, canonical_json_bytes)
    return {
        "status": "QUARANTINED",
        "state": "QUARANTINED",
        "quarantine": quarantine,
        "lifecycle": lifecycle if lifecycle_valid else None,
    }


def cleanup_materialized_session(
    *,
    repository_root: Path,
    sessions_root: Path,
    session_id: str,
    timestamp_utc: str,
    remove_file: Callable[[Path], None] | None = None,
) -> dict[str, Any]:
    """Delete only manifest-declared context files and retain minimal audit evidence."""
    repository, _, session = validate_session_location(
        repository_root,
        sessions_root,
        session_id,
        require_new=False,
    )
    if not session.is_dir():
        raise ArtifactSafetyError("managed session does not exist")
    expected_before = {
        "contexts/context.jsonl",
        "contexts/envelope.json",
        "manifest.json",
        "lifecycle.json",
        "evidence.json",
    }
    actual = set(relative_files(session))
    if actual != expected_before:
        raise ArtifactSafetyError(f"cleanup refuses unexpected or missing files: {sorted(actual ^ expected_before)}")

    manifest = load_json_object(session / "manifest.json")
    evidence_path = session / "evidence.json"
    evidence = load_json_object(evidence_path)
    if evidence.get("manifest_hash") != canonical_sha256(manifest):
        raise ArtifactSafetyError("cleanup manifest hash does not match READY evidence")
    expected_content_files = ["contexts/context.jsonl", "contexts/envelope.json"]
    if manifest.get("cleanup", {}).get("content_files") != expected_content_files:
        raise ArtifactSafetyError("cleanup manifest contains an unauthorized deletion list")
    lifecycle_path = session / "lifecycle.json"
    lifecycle = load_json_object(lifecycle_path)
    validate_lifecycle(lifecycle)
    if lifecycle["state"] != "READY":
        raise LifecycleError("cleanup requires READY state")

    for relative, expected_hash in manifest.get("artifact_hashes", {}).items():
        path = safe_relative_path(session, relative)
        if sha256_file(path) != expected_hash:
            raise ArtifactSafetyError(f"cleanup integrity mismatch: {relative}")

    lifecycle = transition(
        lifecycle,
        "CLEANUP_PENDING",
        reason="NORMAL_SESSION_TERMINATION",
        timestamp_utc=timestamp_utc,
    )
    replace_json(lifecycle_path, lifecycle, canonical_json_bytes)
    remover = remove_file or (lambda path: path.unlink())
    removed: list[str] = []
    try:
        for relative in manifest["cleanup"]["content_files"]:
            path = safe_relative_path(session, relative)
            make_owner_writable(path)
            remover(path)
            removed.append(relative)
        contexts = session / "contexts"
        if contexts.exists():
            contexts.rmdir()
    except Exception:
        raise

    lifecycle = transition(
        lifecycle,
        "CLEANED",
        reason="MANAGED_CONTEXT_CONTENT_REMOVED",
        timestamp_utc=timestamp_utc,
    )
    replace_json(lifecycle_path, lifecycle, canonical_json_bytes)
    evidence["state"] = "CLEANED"
    evidence["cleanup_result"] = {
        "status": "PASS",
        "removed": removed,
        "retained_audit_files": ["manifest.json", "lifecycle.json", "evidence.json"],
        "timestamp_utc": timestamp_utc,
    }
    evidence["lifecycle_transition_log"] = lifecycle["transition_log"]
    replace_json(evidence_path, evidence, canonical_json_bytes)
    return {
        "status": "CLEANED",
        "state": "CLEANED",
        "session_id": session_id,
        "session_relative_path": session.relative_to(repository).as_posix(),
        "removed": removed,
        "cleanup_result": "PASS",
        "quarantine_result": "NOT_REQUIRED",
        "lifecycle": lifecycle,
    }
