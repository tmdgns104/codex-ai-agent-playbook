#!/usr/bin/env python3
"""Build a deterministic, side-effect-free activation plan for routed capabilities."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROUTER_DIR = Path(__file__).resolve().parents[1] / "router"
if str(ROUTER_DIR) not in sys.path:
    sys.path.insert(0, str(ROUTER_DIR))

from capability_router import load_capabilities, route_capabilities  # noqa: E402

SENSITIVE_PERMISSIONS = {
    "credential_access",
    "external_write",
    "database_write",
    "destructive",
    "production",
}
NETWORK_PERMISSIONS = {"network", "browser_control"}
PROFILE_GATED_PERMISSIONS = {"process_exec", "local_write"}

DECISION_RANK = {
    "AUTO_ALLOWED": 0,
    "PROFILE_GATED": 1,
    "NETWORK_REVIEW": 2,
    "MANUAL_ONLY": 3,
    "HUMAN_GATE_REQUIRED": 4,
}


def activation_decision(capability: dict[str, Any]) -> tuple[str, list[str]]:
    """Return the strongest activation decision and its reasons."""
    permissions = set(capability.get("permissions", []))
    capability_type = str(capability.get("type", ""))

    sensitive = sorted(permissions & SENSITIVE_PERMISSIONS)
    if sensitive:
        return "HUMAN_GATE_REQUIRED", [f"sensitive:{item}" for item in sensitive]

    if capability_type in {"mcp", "agent"}:
        return "MANUAL_ONLY", [f"type:{capability_type}", "p0-no-auto-activation"]

    network = sorted(permissions & NETWORK_PERMISSIONS)
    if network:
        return "NETWORK_REVIEW", [f"permission:{item}" for item in network]

    profile_gated = sorted(permissions & PROFILE_GATED_PERMISSIONS)
    if profile_gated:
        return "PROFILE_GATED", [f"permission:{item}" for item in profile_gated]

    return "AUTO_ALLOWED", ["read-only-or-metadata"]


def build_activation_plan(task_text: str, capabilities: list[dict[str, Any]]) -> dict[str, Any]:
    """Route the task, then classify selected capabilities without executing anything."""
    routed = route_capabilities(task_text, capabilities)
    by_id = {capability["id"]: capability for capability in capabilities}

    plans: list[dict[str, Any]] = []
    for selected in routed["selected"]:
        capability = by_id[selected["id"]]
        decision, reasons = activation_decision(capability)
        plans.append(
            {
                "id": capability["id"],
                "type": capability["type"],
                "decision": decision,
                "permissions": list(capability.get("permissions", [])),
                "reasons": reasons,
                "score": selected["score"],
                "profile": selected["profile"],
            }
        )

    gates = {
        "profile": sum(item["decision"] == "PROFILE_GATED" for item in plans),
        "network": sum(item["decision"] == "NETWORK_REVIEW" for item in plans),
        "human": sum(item["decision"] == "HUMAN_GATE_REQUIRED" for item in plans),
        "manual": sum(item["decision"] == "MANUAL_ONLY" for item in plans),
    }

    strongest_decision = (
        max((item["decision"] for item in plans), key=lambda name: DECISION_RANK[name])
        if plans
        else "NONE"
    )

    return {
        "task": task_text,
        "profile": routed["profile"],
        "plans": plans,
        "count": len(plans),
        "gates": gates,
        "strongest_decision": strongest_decision,
        "result": "PLANNED" if plans else "NO_ACTION",
        "side_effects_executed": False,
    }


def print_human(result: dict[str, Any]) -> None:
    print("Codex Playbook Capability Activation Plan")
    print(f"Task: {result['task']}")
    print()

    for item in result["plans"]:
        print(f"PLAN       {item['id']:<24} {item['decision']}")
        print(
            "           "
            + " | ".join(
                [
                    "permissions=" + ",".join(item["permissions"]),
                    "reasons=" + ",".join(item["reasons"]),
                ]
            )
        )

    gates = result["gates"]
    print()
    print(f"PROFILE    {str(result['profile']).upper()}")
    print(f"COUNT      {result['count']}")
    print(
        "GATES      "
        f"profile={gates['profile']} "
        f"network={gates['network']} "
        f"human={gates['human']} "
        f"manual={gates['manual']}"
    )
    print(f"SIDEFX     {str(result['side_effects_executed']).lower()}")
    print(f"RESULT     {result['result']}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a side-effect-free V8.1 capability activation plan."
    )
    parser.add_argument("--root", default=".", help="Playbook repository root.")
    parser.add_argument("--task", required=True, help="Task text to route and classify.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    try:
        capabilities = load_capabilities(root)
        result = build_activation_plan(args.task, capabilities)
    except ValueError as exc:
        if args.json:
            print(json.dumps({"result": "FAIL", "error": str(exc)}, ensure_ascii=False))
        else:
            print(f"FAIL       {exc}")
        return 1

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_human(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
