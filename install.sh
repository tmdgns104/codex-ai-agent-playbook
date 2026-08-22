#!/usr/bin/env bash
set -euo pipefail

KIT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GLOBAL_CODEX_DIR="$HOME/.codex"
GLOBAL_AGENTS="$GLOBAL_CODEX_DIR/AGENTS.md"
SOURCE_AGENTS="$KIT_ROOT/.codex/AGENTS.md"
SKILLS_DIR="$HOME/.agents/skills"
SKILLS_SOURCE_ROOT="$KIT_ROOT/.agents/skills"
HARNESS_SOURCE_ROOT="$KIT_ROOT/harness"
HARNESS_TARGET_ROOT="$GLOBAL_CODEX_DIR/playbook-harness"
BACKUP_BASE="$GLOBAL_CODEX_DIR/playbook-backups"
RUN_BACKUP=""

BEGIN='<!-- BEGIN AI_AGENT_PLAYBOOK_KIT -->'
END='<!-- END AI_AGENT_PLAYBOOK_KIT -->'

mkdir -p "$GLOBAL_CODEX_DIR" "$SKILLS_DIR"

ensure_backup_root() {
  if [ -z "$RUN_BACKUP" ]; then
    RUN_BACKUP="$BACKUP_BASE/$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$RUN_BACKUP"
  fi
}

fingerprint_dir() {
  python3 - "$1" <<'PY'
import hashlib, sys
from pathlib import Path
root = Path(sys.argv[1])
if not root.exists():
    print("")
    raise SystemExit(0)
parts = []
for path in sorted(p for p in root.rglob("*") if p.is_file()):
    rel = path.relative_to(root).as_posix()
    parts.append(f"{rel}={hashlib.sha256(path.read_bytes()).hexdigest()}")
print(hashlib.sha256("\n".join(parts).encode()).hexdigest())
PY
}

same_dir() {
  [ -d "$2" ] || return 1
  [ "$(fingerprint_dir "$1")" = "$(fingerprint_dir "$2")" ]
}

tmp_agents="$(mktemp)"
trap 'rm -f "$tmp_agents"' EXIT
python3 - "$SOURCE_AGENTS" "$GLOBAL_AGENTS" "$tmp_agents" "$BEGIN" "$END" <<'PY'
import re, sys
from pathlib import Path
src, dst, out = map(Path, sys.argv[1:4])
begin, end = sys.argv[4], sys.argv[5]
source = src.read_text(encoding="utf-8")
match = re.search(re.escape(begin) + r".*?" + re.escape(end), source, flags=re.S)
if not match:
    raise SystemExit("Source marker not found")
block = match.group(0)
if dst.exists():
    current = dst.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(begin) + r".*?" + re.escape(end), re.S)
    updated = pattern.sub(block, current) if pattern.search(current) else current.rstrip() + "\n\n" + block + "\n"
else:
    updated = source
out.write_text(updated, encoding="utf-8")
PY

if [ -f "$GLOBAL_AGENTS" ] && cmp -s "$tmp_agents" "$GLOBAL_AGENTS"; then
  echo "OK       $GLOBAL_AGENTS"
else
  if [ -f "$GLOBAL_AGENTS" ]; then
    ensure_backup_root
    cp "$GLOBAL_AGENTS" "$RUN_BACKUP/AGENTS.md"
    echo "BACKUP   $GLOBAL_AGENTS"
  fi
  cp "$tmp_agents" "$GLOBAL_AGENTS"
  echo "INSTALLED $GLOBAL_AGENTS"
fi

for legacy in "$SKILLS_DIR"/*.backup-*; do
  [ -d "$legacy" ] || continue
  ensure_backup_root
  mkdir -p "$RUN_BACKUP/legacy-skill-backups"
  mv "$legacy" "$RUN_BACKUP/legacy-skill-backups/"
  echo "MOVED    legacy backup $(basename "$legacy")"
done

for source in "$SKILLS_SOURCE_ROOT"/*; do
  [ -d "$source" ] || continue
  skill_name="$(basename "$source")"
  target="$SKILLS_DIR/$skill_name"
  if same_dir "$source" "$target"; then
    echo "OK       skill '$skill_name'"
    continue
  fi
  if [ -d "$target" ]; then
    ensure_backup_root
    mkdir -p "$RUN_BACKUP/skills"
    cp -R "$target" "$RUN_BACKUP/skills/$skill_name"
    rm -rf "$target"
    echo "BACKUP   skill '$skill_name'"
  fi
  cp -R "$source" "$target"
  echo "INSTALLED skill '$skill_name'"
done

if same_dir "$HARNESS_SOURCE_ROOT" "$HARNESS_TARGET_ROOT"; then
  echo "OK       playbook harness"
else
  if [ -d "$HARNESS_TARGET_ROOT" ]; then
    ensure_backup_root
    mkdir -p "$RUN_BACKUP/harness"
    cp -R "$HARNESS_TARGET_ROOT" "$RUN_BACKUP/harness/playbook-harness"
    rm -rf "$HARNESS_TARGET_ROOT"
    echo "BACKUP   playbook harness"
  fi
  cp -R "$HARNESS_SOURCE_ROOT" "$HARNESS_TARGET_ROOT"
  echo "INSTALLED playbook harness"
fi

echo
echo "Installation complete."
[ -z "$RUN_BACKUP" ] || echo "Backup: $RUN_BACKUP"

echo
python3 "$HARNESS_TARGET_ROOT/security/harness_audit.py" --root "$KIT_ROOT"

echo
echo 'Try: $codex-skill-router'
echo 'Try: $ai-agent-development-playbook'
echo 'Try: $codex-long-run'
