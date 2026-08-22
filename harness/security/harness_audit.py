#!/usr/bin/env python3
"""Static audit for the Codex AI Agent Playbook repository."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

FRONTMATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.S)
NAME = re.compile(r"(?m)^name:\s*([^\n]+)$")
DESCRIPTION = re.compile(r"(?m)^description:\s*(?:>-?|>?)\s*(.*)$")
GLOBAL_MODEL_NAME = re.compile(r"\b(?:gpt-\d[^\s`|,;)]*|claude-[^\s`|,;)]*)", re.I)
PERSONAL_PATH = re.compile(r"(?:[A-Za-z]:\\Users\\[^\\\s]+|/Users/[^/\s]+|/home/[^/\s]+)")
OBVIOUS_SECRET = re.compile(
    r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|\bAKIA[0-9A-Z]{16}\b|\bgh[pousr]_[A-Za-z0-9]{20,}\b"
)

ROOT_MANAGED = {
    "install.ps1",
    "install.sh",
    "uninstall.ps1",
    "uninstall.sh",
    "verify-install.ps1",
}


def iter_files(root: Path, subtree: str):
    base = root / subtree
    if not base.exists():
        return []
    return [p for p in base.rglob("*") if p.is_file()]


def rel(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit Codex Playbook structure, metadata, and context hygiene.")
    parser.add_argument("--root", default=".", help="Playbook repository root.")
    parser.add_argument("--max-global-bytes", type=int, default=6000)
    parser.add_argument("--max-skill-bytes", type=int, default=20000)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    failures: list[str] = []
    warnings: list[str] = []

    def fail(message: str) -> None:
        failures.append(message)
        print(f"FAIL       {message}")

    def warn(message: str) -> None:
        warnings.append(message)
        print(f"WARN       {message}")

    print("Codex AI Agent Playbook - Harness Audit")
    print(f"Root: {root}")
    print()

    agents = root / ".codex" / "AGENTS.md"
    if not agents.exists():
        fail(".codex/AGENTS.md missing")
    else:
        size = agents.stat().st_size
        if size > args.max_global_bytes:
            fail(f"global AGENTS.md exceeds {args.max_global_bytes} bytes ({size})")
        else:
            print(f"PASS       global AGENTS.md size: {size} bytes")
        body = text(agents)
        begin = body.count("<!-- BEGIN AI_AGENT_PLAYBOOK_KIT -->")
        end = body.count("<!-- END AI_AGENT_PLAYBOOK_KIT -->")
        if begin != 1 or end != 1:
            fail(f"global AGENTS.md marker count invalid (begin={begin}, end={end})")
        else:
            print("PASS       global AGENTS.md markers")
        models = GLOBAL_MODEL_NAME.findall(body)
        if models:
            fail(f"vendor/model names hard-coded in permanent global context: {', '.join(models[:5])}")
        else:
            print("PASS       no hard-coded current model names in global context")

    skills_root = root / ".agents" / "skills"
    names: dict[str, str] = {}
    if not skills_root.exists():
        fail(".agents/skills missing")
    else:
        backup_dirs = [p for p in skills_root.iterdir() if p.is_dir() and ".backup-" in p.name]
        if backup_dirs:
            fail("backup directories inside Skill discovery path: " + ", ".join(p.name for p in backup_dirs))
        else:
            print("PASS       no backup directories inside Skill discovery path")

        for skill_dir in sorted(p for p in skills_root.iterdir() if p.is_dir()):
            skill_file = skill_dir / "SKILL.md"
            if not skill_file.exists():
                fail(f"skill missing SKILL.md: {skill_dir.name}")
                continue
            content = text(skill_file)
            match = FRONTMATTER.search(content)
            if not match:
                fail(f"skill frontmatter missing/invalid: {skill_dir.name}")
                continue
            frontmatter = match.group(1)
            name_match = NAME.search(frontmatter)
            desc_match = DESCRIPTION.search(frontmatter)
            if not name_match:
                fail(f"skill name missing: {skill_dir.name}")
                continue
            name = name_match.group(1).strip().strip("'\"")
            if name != skill_dir.name:
                fail(f"skill name/path mismatch: {skill_dir.name} != {name}")
            if name in names:
                fail(f"duplicate skill name '{name}' in {names[name]} and {skill_dir.name}")
            names[name] = skill_dir.name
            if not desc_match:
                fail(f"skill description missing: {skill_dir.name}")
            size = skill_file.stat().st_size
            if size > args.max_skill_bytes:
                warn(f"large SKILL.md ({size} bytes): {skill_dir.name}")

        if names:
            print(f"PASS       skill metadata checked: {len(names)} skills")

    profiles_dir = root / "harness" / "profiles"
    required_profile_keys = {
        "name",
        "description",
        "max_changed_files_warning",
        "scan_conflict_markers",
        "scan_secrets",
        "verification_required",
    }
    for profile_name in ("minimal", "standard", "strict"):
        path = profiles_dir / f"{profile_name}.json"
        if not path.exists():
            fail(f"profile missing: {profile_name}.json")
            continue
        try:
            data = json.loads(text(path))
        except json.JSONDecodeError as exc:
            fail(f"invalid JSON profile {profile_name}: {exc}")
            continue
        missing = required_profile_keys - data.keys()
        if missing:
            fail(f"profile {profile_name} missing keys: {', '.join(sorted(missing))}")
        elif str(data["name"]).lower() != profile_name:
            fail(f"profile name mismatch: {profile_name}")
        else:
            print(f"PASS       profile '{profile_name}'")

    python_files = iter_files(root, "harness")
    for path in python_files:
        if path.suffix != ".py":
            continue
        try:
            compile(text(path), rel(root, path), "exec")
        except SyntaxError as exc:
            fail(f"Python syntax error in {rel(root, path)}:{exc.lineno}: {exc.msg}")
    if any(p.suffix == ".py" for p in python_files):
        print("PASS       harness Python syntax")

    manifest_path = root / "MANIFEST.txt"
    if not manifest_path.exists():
        fail("MANIFEST.txt missing")
    else:
        manifest = {line.strip() for line in text(manifest_path).splitlines() if line.strip()}
        for entry in sorted(manifest):
            if not (root / entry).exists():
                fail(f"MANIFEST entry missing on disk: {entry}")

        managed = set(ROOT_MANAGED)
        for subtree in (".agents", ".codex", "harness"):
            managed.update(rel(root, p) for p in iter_files(root, subtree))
        missing_from_manifest = managed - manifest
        if missing_from_manifest:
            fail("managed files missing from MANIFEST: " + ", ".join(sorted(missing_from_manifest)))
        else:
            print("PASS       MANIFEST covers managed files")

    scan_files = iter_files(root, ".agents") + iter_files(root, ".codex")
    for path in scan_files:
        if path.suffix.lower() not in {".md", ".txt", ".json", ".yaml", ".yml", ".toml"}:
            continue
        content = text(path)
        if PERSONAL_PATH.search(content):
            fail(f"personal absolute path in reusable content: {rel(root, path)}")
        if OBVIOUS_SECRET.search(content):
            fail(f"obvious secret material in reusable content: {rel(root, path)}")

    print()
    print(f"INFO       warnings: {len(warnings)}")
    if failures:
        print(f"RESULT     FAIL ({len(failures)} issue(s))")
        return 1
    print("RESULT     PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
