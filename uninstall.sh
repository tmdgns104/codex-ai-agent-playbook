#!/usr/bin/env bash
set -euo pipefail

KIT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GLOBAL_AGENTS="$HOME/.codex/AGENTS.md"
SKILLS_DIR="$HOME/.agents/skills"
SKILLS_SOURCE_ROOT="$KIT_ROOT/.agents/skills"

BEGIN='<!-- BEGIN AI_AGENT_PLAYBOOK_KIT -->'
END='<!-- END AI_AGENT_PLAYBOOK_KIT -->'

if [ -f "$GLOBAL_AGENTS" ]; then
python3 - "$GLOBAL_AGENTS" "$BEGIN" "$END" <<'PY'
import sys, re
from pathlib import Path
p = Path(sys.argv[1])
begin, end = sys.argv[2], sys.argv[3]
text = p.read_text(encoding="utf-8")
pat = re.compile(r"\s*" + re.escape(begin) + r".*?" + re.escape(end) + r"\s*", re.S)
text = pat.sub("\n", text).strip()
p.write_text(text + ("\n" if text else ""), encoding="utf-8")
PY
fi

for source in "$SKILLS_SOURCE_ROOT"/*; do
  [ -d "$source" ] || continue
  skill_name="$(basename "$source")"
  rm -rf "$SKILLS_DIR/$skill_name"
  echo "Removed skill: $skill_name"
done

echo "Uninstall complete."
