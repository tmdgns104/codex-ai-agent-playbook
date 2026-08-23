#!/usr/bin/env python3
"""Cross-platform file locks for one-writer-per-Skill governance updates."""

from __future__ import annotations

import json
import os
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


class SkillLockError(RuntimeError):
    """Raised when a Skill governance lock cannot be safely acquired/released."""


def _lock_path(state_root: Path, skill_id: str) -> Path:
    if not skill_id or any(part in skill_id for part in ("/", "\\", "..")):
        raise SkillLockError(f"invalid skill id for lock: {skill_id!r}")
    return state_root / "locks" / f"{skill_id}.lock"


def _read_lock(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def acquire_lock(state_root: Path, skill_id: str, *, stale_seconds: int = 3600) -> str:
    path = _lock_path(state_root, skill_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    token = uuid.uuid4().hex

    for attempt in range(2):
        payload = {
            "skill_id": skill_id,
            "token": token,
            "created_at_epoch": time.time(),
        }
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            existing = _read_lock(path)
            created = existing.get("created_at_epoch")
            is_stale = isinstance(created, (int, float)) and (time.time() - float(created)) > stale_seconds
            if is_stale and attempt == 0:
                try:
                    path.unlink()
                except FileNotFoundError:
                    pass
                continue
            raise SkillLockError(f"skill already locked: {skill_id}")
        else:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                json.dump(payload, handle, ensure_ascii=False, sort_keys=True)
                handle.write("\n")
            return token

    raise SkillLockError(f"could not acquire lock: {skill_id}")


def release_lock(state_root: Path, skill_id: str, token: str) -> None:
    path = _lock_path(state_root, skill_id)
    existing = _read_lock(path)
    if not path.exists():
        raise SkillLockError(f"lock missing: {skill_id}")
    if existing.get("token") != token:
        raise SkillLockError(f"lock token mismatch: {skill_id}")
    path.unlink()


@contextmanager
def skill_lock(state_root: Path, skill_id: str, *, stale_seconds: int = 3600) -> Iterator[str]:
    token = acquire_lock(state_root, skill_id, stale_seconds=stale_seconds)
    try:
        yield token
    finally:
        path = _lock_path(state_root, skill_id)
        if path.exists():
            release_lock(state_root, skill_id, token)
