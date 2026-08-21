#!/usr/bin/env bash
set -euo pipefail

KIT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GLOBAL_CODEX_DIR="$HOME/.codex"
GLOBAL_AGENTS="$GLOBAL_CODEX_DIR/AGENTS.md"
SOURCE_AGENTS="$KIT_ROOT/.codex/AGENTS.md"
SKILLS_DIR="$HOME/.agents/skills"
SKILLS_SOURCE_ROOT="$KIT_ROOT/.agents/skills"

mkdir -p "$GLOBAL_CODEX_DIR" "$SKILLS_DIR"

BEGIN='<!-- BEGIN AI_AGENT_PLAYBOOK_KIT -->'
END='<!-- END AI_AGENT_PLAYBOOK_KIT -->'

python3 - "$SOURCE_AGENTS" "$GLOBAL_AGENTS" "$BEGIN" "$END" <<'PY'
import sys, re
from pathlib import Path
src = Path(sys.argv[1])
dst = Path(sys.argv[2])
begin, end = sys.argv[3], sys.argv[4]
source = src.read_text(encoding="utf-8")
m = re.search(re.escape(begin) + r".*?" + re.escape(end), source, flags=re.S)
if not m:
    raise SystemExit("Source marker not found")
block = m.group(0)

if dst.exists():
    current = dst.read_text(encoding="utf-8")
    pat = re.compile(re.escape(begin) + r".*?" + re.escape(end), re.S)
    if pat.search(current):
        current = pat.sub(block, current)
    else:
        current = current.rstrip() + "\n\n" + block + "\n"
    dst.write_text(current, encoding="utf-8")
else:
    dst.write_text(source, encoding="utf-8")
PY

for source in "$SKILLS_SOURCE_ROOT"/*; do
  [ -d "$source" ] || continue
  skill_name="$(basename "$source")"
  target="$SKILLS_DIR/$skill_name"
  if [ -d "$target" ]; then
    stamp="$(date +%Y%m%d-%H%M%S)"
    cp -R "$target" "$target.backup-$stamp"
    rm -rf "$target"
  fi
  cp -R "$source" "$target"
  echo "Installed skill: $skill_name"
done

echo "Installation complete."
echo 'Try: $ai-agent-development-playbook'
echo 'Try: $human-readable-code'
echo 'Try: $human-centered-project-builder'
echo 'Try: $guide-ppt-creator'
echo 'Try: $codex-long-run'
echo 'Try: $codex-task-router'
