"""Small, explicit filesystem safety helpers for context materialization."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from pathlib import Path
from typing import Any


SESSION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


class ArtifactSafetyError(RuntimeError):
    """Raised before a path or artifact operation can cross its authority boundary."""


def is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _reject_symlink_components(path: Path, stop: Path) -> None:
    current = path
    while True:
        if current.exists() and current.is_symlink():
            raise ArtifactSafetyError(f"symlink path component blocked: {current}")
        if current == stop:
            return
        if current.parent == current:
            raise ArtifactSafetyError(f"path does not descend from containment root: {path}")
        current = current.parent


def validate_session_location(
    repository_root: Path,
    sessions_root: Path,
    session_id: str,
    *,
    require_new: bool,
) -> tuple[Path, Path, Path]:
    """Return resolved roots only when the session is dedicated and contained."""
    if not SESSION_RE.fullmatch(session_id):
        raise ArtifactSafetyError("invalid session ID")
    repository = repository_root.resolve(strict=True)
    if repository.is_symlink():
        raise ArtifactSafetyError("repository root must not be a symlink")

    sessions = sessions_root.resolve(strict=False)
    if sessions == repository or not is_within(sessions, repository):
        raise ArtifactSafetyError("sessions root must be a dedicated directory inside repository root")
    _reject_symlink_components(sessions, repository)

    session = sessions / session_id
    if session.resolve(strict=False) != session:
        raise ArtifactSafetyError("session path normalization mismatch")
    if not is_within(session, sessions):
        raise ArtifactSafetyError("session path escapes sessions root")
    if session.exists() and session.is_symlink():
        raise ArtifactSafetyError("session path must not be a symlink")
    if require_new and session.exists():
        raise ArtifactSafetyError("duplicate session ID or session artifact reuse attempt")
    return repository, sessions, session


def safe_relative_path(session_root: Path, relative_text: str) -> Path:
    if not relative_text or "\\" in relative_text or re.match(r"^[A-Za-z]:", relative_text):
        raise ArtifactSafetyError("artifact path must use normalized relative POSIX syntax")
    parts = relative_text.split("/")
    if any(part in ("", ".", "..") for part in parts):
        raise ArtifactSafetyError("artifact path contains an unsafe component")
    candidate = session_root.joinpath(*parts)
    if not is_within(candidate.resolve(strict=False), session_root.resolve(strict=False)):
        raise ArtifactSafetyError("artifact path escapes session root")
    _reject_symlink_components(candidate, session_root)
    return candidate


def validate_source_path(repository_root: Path, relative_text: str) -> Path:
    if not relative_text or "\\" in relative_text or re.match(r"^[A-Za-z]:", relative_text):
        raise ArtifactSafetyError("source snapshot path must be repository-relative POSIX syntax")
    parts = relative_text.split("/")
    if any(part in ("", ".", "..") for part in parts):
        raise ArtifactSafetyError("source snapshot path contains an unsafe component")
    candidate = repository_root.joinpath(*parts)
    if not is_within(candidate.resolve(strict=True), repository_root.resolve(strict=True)):
        raise ArtifactSafetyError("source snapshot path escapes repository root")
    _reject_symlink_components(candidate, repository_root)
    if not candidate.is_file():
        raise ArtifactSafetyError("source snapshot is not a regular file")
    return candidate


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_bytes_exclusive(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _reject_symlink_components(path, path.parents[1] if len(path.parents) > 1 else path.parent)
    with path.open("xb") as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())


def replace_json(path: Path, payload: dict[str, Any], canonical_json_bytes) -> None:
    """Replace a mutable control document without following a symlink target."""
    if path.exists() and path.is_symlink():
        raise ArtifactSafetyError(f"refusing to replace symlink: {path}")
    temporary = path.with_name(path.name + ".tmp")
    if temporary.exists() or temporary.is_symlink():
        raise ArtifactSafetyError(f"unexpected temporary control file: {temporary}")
    write_bytes_exclusive(temporary, canonical_json_bytes(payload))
    os.replace(temporary, path)


def load_json_object(path: Path) -> dict[str, Any]:
    if path.is_symlink():
        raise ArtifactSafetyError(f"refusing to read symlink: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ArtifactSafetyError(f"invalid JSON artifact {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ArtifactSafetyError(f"JSON artifact must be an object: {path}")
    return value


def make_read_only(path: Path) -> None:
    path.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)


def make_owner_writable(path: Path) -> None:
    path.chmod(path.stat().st_mode | stat.S_IWUSR)


def relative_files(session_root: Path) -> list[str]:
    """List files without following directory symlinks; any symlink fails closed."""
    found: list[str] = []
    for current_text, directories, filenames in os.walk(session_root, followlinks=False):
        current = Path(current_text)
        for name in list(directories):
            child = current / name
            if child.is_symlink():
                raise ArtifactSafetyError(f"unexpected symlink directory: {child}")
        for name in filenames:
            child = current / name
            if child.is_symlink():
                raise ArtifactSafetyError(f"unexpected symlink file: {child}")
            found.append(child.relative_to(session_root).as_posix())
    return sorted(found)
