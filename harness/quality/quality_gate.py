#!/usr/bin/env python3
"""Deterministic supplemental quality gate for Codex repository work.

Exit codes:
  0 = PASS
  1 = FAIL
  2 = UNVERIFIED (structural checks passed but required execution evidence missing)
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

SECRET_PATTERNS = (
    ("private-key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("aws-access-key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("github-token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b")),
    ("api-key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
)


def run(args: list[str], cwd: Path, *, shell: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args if not shell else args[0],
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        shell=shell,
        check=False,
    )


def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return run(["git", *args], repo)


def repo_root(path: Path) -> Path:
    probe = git(path, "rev-parse", "--show-toplevel")
    if probe.returncode != 0:
        raise RuntimeError(probe.stdout.strip() or f"not a Git repository: {path}")
    return Path(probe.stdout.strip()).resolve()


def load_profile(script: Path, name: str) -> dict:
    profile_path = script.parent.parent / "profiles" / f"{name.lower()}.json"
    with profile_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if data.get("name") != name.upper():
        raise RuntimeError(f"profile name mismatch: {profile_path}")
    return data


def changed_paths(repo: Path) -> list[Path]:
    changed = set()

    tracked = git(repo, "diff", "--name-only", "HEAD", "--")
    if tracked.returncode == 0:
        changed.update(line for line in tracked.stdout.splitlines() if line.strip())

    untracked = git(repo, "ls-files", "--others", "--exclude-standard")
    if untracked.returncode == 0:
        changed.update(line for line in untracked.stdout.splitlines() if line.strip())

    return [repo / item for item in sorted(changed)]


def read_text(path: Path, max_bytes: int = 1_000_000) -> str | None:
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if len(data) > max_bytes or b"\x00" in data:
        return None
    return data.decode("utf-8", errors="replace")


def print_command_result(command: str, result: subprocess.CompletedProcess[str]) -> None:
    status = "PASS" if result.returncode == 0 else "FAIL"
    print(f"{status:10} verification: {command}")
    output = result.stdout.strip()
    if output:
        lines = output.splitlines()
        for line in lines[-20:]:
            print(f"           {line}")
        if len(lines) > 20:
            print(f"           ... {len(lines) - 20} earlier lines omitted")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a deterministic repository quality gate.")
    parser.add_argument("--repo", default=".", help="Repository path (default: current directory).")
    parser.add_argument("--profile", choices=("minimal", "standard", "strict"), default="standard")
    parser.add_argument(
        "--verify",
        action="append",
        default=[],
        help="Explicit repository-defined verification command. May be supplied more than once.",
    )
    args = parser.parse_args()

    script = Path(__file__).resolve()
    profile = load_profile(script, args.profile.upper())

    try:
        repo = repo_root(Path(args.repo).resolve())
    except RuntimeError as exc:
        print(f"FAIL       {exc}")
        return 1

    print(f"Codex Playbook Quality Gate - {profile['name']}")
    print(f"Repository: {repo}")
    print()

    failed = False
    unverified = False

    for label, command in (
        ("unstaged diff whitespace", ("diff", "--check")),
        ("staged diff whitespace", ("diff", "--cached", "--check")),
    ):
        result = git(repo, *command)
        if result.returncode == 0:
            print(f"PASS       {label}")
        else:
            print(f"FAIL       {label}")
            if result.stdout.strip():
                print(result.stdout.rstrip())
            failed = True

    conflicts = git(repo, "diff", "--name-only", "--diff-filter=U")
    conflict_files = [line for line in conflicts.stdout.splitlines() if line.strip()]
    if conflict_files:
        print(f"FAIL       unresolved Git conflicts: {', '.join(conflict_files)}")
        failed = True
    else:
        print("PASS       unresolved Git conflicts")

    paths = changed_paths(repo)
    print(f"INFO       changed/untracked files: {len(paths)}")
    limit = int(profile.get("max_changed_files_warning", 0) or 0)
    if limit and len(paths) > limit:
        print(f"WARN       changed file count exceeds profile warning threshold ({limit})")

    if profile.get("scan_conflict_markers", True):
        marker_hits: list[str] = []
        for path in paths:
            text = read_text(path)
            if text is None:
                continue
            for number, line in enumerate(text.splitlines(), start=1):
                if line.startswith("<<<<<<< ") or line.startswith(">>>>>>> "):
                    marker_hits.append(f"{path.relative_to(repo)}:{number}")
        if marker_hits:
            print(f"FAIL       conflict markers: {', '.join(marker_hits[:10])}")
            failed = True
        else:
            print("PASS       conflict-marker scan")

    if profile.get("scan_secrets", False):
        secret_hits: list[str] = []
        for path in paths:
            text = read_text(path)
            if text is None:
                continue
            for label, pattern in SECRET_PATTERNS:
                if pattern.search(text):
                    secret_hits.append(f"{path.relative_to(repo)} ({label})")
        if secret_hits:
            joined = ", ".join(secret_hits[:10])
            if profile["name"] == "STRICT":
                print(f"FAIL       suspicious secret material: {joined}")
                failed = True
            else:
                print(f"WARN       suspicious secret material: {joined}")
        else:
            print("PASS       suspicious-secret scan")

    if args.verify:
        print()
        for command in args.verify:
            result = run([command], repo, shell=True)
            print_command_result(command, result)
            if result.returncode != 0:
                failed = True
    elif profile.get("verification_required", False):
        print("UNVERIFIED STRICT profile requires explicit --verify evidence")
        unverified = True
    else:
        print("INFO       no verification command supplied; repository checks remain separate evidence")

    print()
    if failed:
        print("RESULT     FAIL")
        return 1
    if unverified:
        print("RESULT     UNVERIFIED")
        return 2

    print("RESULT     PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
