#!/usr/bin/env python3
"""Deterministic metadata-first router for V8.1 optional capabilities."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from registry import load_json, validate_registry, validate_sources
from scoring import ranking_key, score_capability, strongest_profile

DEFAULT_MAX_SELECTED = 3
DEFAULT_MAX_MCP = 1
DEFAULT_MAX_AGENT = 1


def load_capabilities(root: Path) -> list[dict[str, Any]]:
    library = root / "capability-library"
    sources = load_json(library / "sources.json")
    source_ids = validate_sources(sources)
    registry = load_json(library / "registry.json")
    return validate_registry(registry, source_ids)


def route_capabilities(
    task_text: str,
    capabilities: list[dict[str, Any]],
    *,
    max_selected: int = DEFAULT_MAX_SELECTED,
    max_mcp: int = DEFAULT_MAX_MCP,
    max_agent: int = DEFAULT_MAX_AGENT,
) -> dict[str, Any]:
    scored = [score_capability(task_text, capability) for capability in capabilities]
    eligible = sorted((item for item in scored if item["eligible"]), key=ranking_key)

    selected: list[dict[str, Any]] = []
    mcp_count = 0
    agent_count = 0

    for item in eligible:
        if len(selected) >= max_selected:
            break
        if item["type"] == "mcp":
            if mcp_count >= max_mcp:
                continue
            mcp_count += 1
        elif item["type"] == "agent":
            if agent_count >= max_agent:
                continue
            agent_count += 1
        selected.append(item)

    profile = strongest_profile(selected)
    return {
        "task": task_text,
        "selected": selected,
        "profile": profile,
        "count": len(selected),
        "result": "ROUTED" if selected else "NO_CAPABILITY",
    }


def print_human(result: dict[str, Any]) -> None:
    print("Codex Playbook Capability Router")
    print(f"Task: {result['task']}")
    print()

    for item in result["selected"]:
        print(
            f"SELECT     {item['id']:<24} "
            f"score={item['score']:<3} "
            f"profile={str(item['profile']).upper():<8} "
            f"approval={item['approval']}"
        )
        reasons: list[str] = []
        if item["matched_triggers"]:
            reasons.append("triggers=" + ",".join(item["matched_triggers"]))
        if item["matched_domains"]:
            reasons.append("domains=" + ",".join(item["matched_domains"]))
        if item["summary_overlap"]:
            reasons.append("summary=" + ",".join(item["summary_overlap"]))
        if reasons:
            print("           " + " | ".join(reasons))

    print()
    print(f"PROFILE    {str(result['profile']).upper()}")
    print(f"COUNT      {result['count']}")
    print(f"RESULT     {result['result']}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Route a task to the minimum useful V8.1 capabilities.")
    parser.add_argument("--root", default=".", help="Playbook repository root.")
    parser.add_argument("--task", required=True, help="Task text to classify.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    try:
        capabilities = load_capabilities(root)
    except ValueError as exc:
        if args.json:
            print(json.dumps({"result": "FAIL", "error": str(exc)}, ensure_ascii=False))
        else:
            print(f"FAIL       {exc}")
        return 1

    result = route_capabilities(args.task, capabilities)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_human(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
