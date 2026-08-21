#!/usr/bin/env bash
set -euo pipefail

GLOBAL_AGENTS="$HOME/.codex/AGENTS.md"
SKILLS_DIR="$HOME/.agents/skills"
SKILLS=("ai-agent-development-playbook" "human-readable-code" "human-centered-project-builder" "guide-ppt-creator")

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

for skill in "${SKILLS[@]}"; do
  rm -rf "$SKILLS_DIR/$skill"
  echo "Removed skill: $skill"
done

echo "Uninstall complete."
