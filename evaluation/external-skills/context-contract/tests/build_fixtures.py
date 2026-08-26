"""Regenerate the checked-in compliant fixture deterministically."""

from __future__ import annotations

import json
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
VALIDATOR = HERE.parent / "validator"
sys.path.insert(0, str(VALIDATOR))
sys.path.insert(0, str(HERE))

from fixture_factory import build_compliant_bundle  # noqa: E402


def main() -> None:
    target = HERE / "fixtures" / "compliant.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(build_compliant_bundle(), ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    target.write_text(text, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
