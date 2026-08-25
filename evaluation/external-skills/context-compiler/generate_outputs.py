"""Generate the two review-only V8.4-004 adapted context artifacts."""

from __future__ import annotations

import json
from pathlib import Path

from compiler import (
    compile_candidate,
    input_from_manifest,
    repository_documents,
    write_compilation_artifacts,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
OUTPUT_ROOT = REPO_ROOT / "evaluation" / "external-skills" / "adapted-contexts"
CANDIDATES = ("kd-sympy", "kd-citation-management")


def main() -> int:
    manifest, policy, rules = repository_documents(REPO_ROOT)
    generated: list[dict[str, object]] = []
    for candidate_id in CANDIDATES:
        compiler_input = input_from_manifest(manifest, policy, candidate_id)
        report = compile_candidate(
            repo_root=REPO_ROOT,
            compiler_input=compiler_input,
            manifest=manifest,
            policy=policy,
            rules=rules,
        )
        if not report.passed:
            print(json.dumps(report.as_dict(), ensure_ascii=False, sort_keys=True))
            return 1
        paths = write_compilation_artifacts(OUTPUT_ROOT, report)
        generated.append(
            {
                "candidate_id": candidate_id,
                "knowledge_unit_count": report.evidence["knowledge_unit_count"],
                "cache_key": report.definition["cache_key"],
                "paths": [path.relative_to(REPO_ROOT).as_posix() for path in paths],
            }
        )
    print(json.dumps({"status": "PASS", "generated": generated}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
