#!/usr/bin/env python3
"""Maintenance CLI for the V8.2 Self-Managing Skill Lifecycle.

This entry point is intentionally separate from the normal Codex launch path.
No command here requires an LLM provider.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve()
HARNESS_ROOT = HERE.parents[1]
DEFAULT_ROOT = HERE.parents[2]
for import_dir in (HARNESS_ROOT / "quality", HARNESS_ROOT / "router"):
    if str(import_dir) not in sys.path:
        sys.path.insert(0, str(import_dir))

from capability_router import route_capabilities  # noqa: E402
from creator import CreatorError, create_candidate  # noqa: E402
from curator import CuratorError, build_curator_report, warn_candidates  # noqa: E402
from events import EventError, EventStore  # noqa: E402
from evolver import EvolutionError, create_evolution_candidate  # noqa: E402
from lifecycle_integration import (  # noqa: E402
    LifecycleIntegrationError,
    list_candidates,
    promote_candidate,
    scaling_registry_sizes,
    validate_candidate,
)
from skill_audit import audit_library  # noqa: E402


def _json_file(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("JSON spec root must be an object")
    return data


def _print_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def _synthetic_capabilities(count: int) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for index in range(count):
        items.append(
            {
                "id": f"synthetic-{index:04d}",
                "type": "skill",
                "summary": "deterministic synthetic routing benchmark capability",
                "triggers": ["benchmark-target" if index == 0 else f"synthetic-trigger-{index}"],
                "domains": ["benchmark"],
                "permissions": ["local_read"],
                "context_cost": "low",
                "activation": "on_demand",
                "recommended_profile": "minimal",
                "risk": "low",
            }
        )
    return items


def benchmark_router(*, repeats: int = 20) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for count in scaling_registry_sizes():
        capabilities = _synthetic_capabilities(count)
        started = time.perf_counter()
        last = None
        for _ in range(repeats):
            last = route_capabilities("benchmark-target task", capabilities)
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        results.append(
            {
                "skill_count": count,
                "repeats": repeats,
                "average_ms": round(elapsed_ms / repeats, 4),
                "selected_count": int(last["count"] if last else 0),
            }
        )
    return results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="V8.2 Self-Managing Skill maintenance CLI")
    parser.add_argument("--root", default=str(DEFAULT_ROOT), help="Playbook catalog root")
    parser.add_argument("--state-root", help="Runtime state root; defaults to <root>/.playbook-state")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("audit", help="Run deterministic Skill Library audit")
    sub.add_parser("gaps", help="List recorded capability-gap events without auto-creating Skills")
    sub.add_parser("proposals", help="List runtime Candidate proposals")
    sub.add_parser("curate", help="Build metadata-only Curator WARN report")

    create = sub.add_parser("create", help="Create a reviewed Creator Candidate from a JSON spec")
    create.add_argument("--spec", required=True)

    evolve = sub.add_parser("evolve", help="Create a reviewed Evolver Candidate from a JSON spec")
    evolve.add_argument("--spec", required=True)
    evolve.add_argument("--issue-code")
    evolve.add_argument("--severe", action="store_true")

    validate = sub.add_parser("validate", help="Audit Candidate and run protected routing regression")
    validate.add_argument("proposal_id")

    promote = sub.add_parser("promote", help="Promote a validated low-risk package Candidate")
    promote.add_argument("proposal_id")
    promote.add_argument("--approve-human-gate", action="store_true")

    benchmark = sub.add_parser("benchmark", help="Measure deterministic metadata router scaling")
    benchmark.add_argument("--repeats", type=int, default=20)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    root = Path(args.root).resolve()
    state_root = Path(args.state_root).resolve() if args.state_root else root / ".playbook-state"

    try:
        events = EventStore(state_root).read_all()

        if args.command == "audit":
            report = audit_library(root)
            _print_json(report.as_dict())
            return report.exit_code()

        if args.command == "gaps":
            gaps = [event for event in events if event.get("event_type") == "capability_gap"]
            distinct = sorted({str(event.get("task_fingerprint")) for event in gaps})
            _print_json(
                {
                    "result": "GAPS_RECORDED" if gaps else "NO_GAPS",
                    "event_count": len(gaps),
                    "distinct_task_count": len(distinct),
                    "events": gaps,
                    "auto_creation": False,
                }
            )
            return 0

        if args.command == "proposals":
            _print_json({"result": "OK", "proposals": list_candidates(state_root)})
            return 0

        if args.command == "curate":
            report = build_curator_report(root, events=events)
            _print_json(
                {
                    "result": "WARN_CANDIDATES" if report["warn_candidate_ids"] else "NO_WARN_CANDIDATES",
                    "body_included": report["body_included"],
                    "candidates": warn_candidates(report),
                }
            )
            return 0

        if args.command == "create":
            spec = _json_file(Path(args.spec))
            result = create_candidate(state_root=state_root, spec=spec, events=events)
            _print_json(result)
            return 0 if result["result"] in {"CANDIDATE_CREATED", "WAIT", "NO_ACTION"} else 1

        if args.command == "evolve":
            spec = _json_file(Path(args.spec))
            result = create_evolution_candidate(
                root=root,
                state_root=state_root,
                spec=spec,
                events=events,
                issue_code=args.issue_code,
                severe_safety_or_correctness=args.severe,
            )
            _print_json(result)
            return 0 if result["result"] in {"CANDIDATE_CREATED", "WAIT", "NO_ACTION", "REVIEW"} else 1

        if args.command == "validate":
            result = validate_candidate(root=root, state_root=state_root, proposal_id=args.proposal_id)
            _print_json(result)
            return 0 if result["result"] == "READY" else 1

        if args.command == "promote":
            result = promote_candidate(
                root=root,
                state_root=state_root,
                proposal_id=args.proposal_id,
                human_gate_approved=args.approve_human_gate,
            )
            _print_json(result)
            if result["result"] == "PROMOTED":
                return 0
            if result["result"] in {"HUMAN_GATE_REQUIRED", "MANUAL_ONLY", "STALE_BASE"}:
                return 2
            return 1

        if args.command == "benchmark":
            if args.repeats < 1:
                raise ValueError("--repeats must be >= 1")
            _print_json({"result": "RECORDED", "semantic_router_added": False, "measurements": benchmark_router(repeats=args.repeats)})
            return 0

        raise ValueError(f"unsupported command: {args.command}")
    except (
        CreatorError,
        CuratorError,
        EventError,
        EvolutionError,
        LifecycleIntegrationError,
        OSError,
        ValueError,
        json.JSONDecodeError,
    ) as exc:
        _print_json({"result": "FAIL", "error": str(exc)})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
