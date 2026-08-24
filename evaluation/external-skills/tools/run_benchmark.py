#!/usr/bin/env python3
"""결정론적 dry-run 계획 검증기 - V8.3 BENCH-004 Stage B."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
BASE = REPO_ROOT / "evaluation" / "external-skills"
RESULTS = BASE / "benchmark-results.json"
FIXTURES = BASE / "benchmark-fixtures.json"
MANIFEST = BASE / "snapshots" / "manifest.json"
POLICY = BASE / "benchmark-policy.json"

VARIANTS = {
    "baseline-no-optional",
    "current-playbook",
    "external-expert",
    "adapted-playbook",
}


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_dry_run() -> dict:
    results = _load(RESULTS)
    fixtures = _load(FIXTURES)
    manifest = _load(MANIFEST)
    policy = _load(POLICY)

    assert policy["external_network_allowed"] is False
    assert policy["external_api_allowed"] is False
    assert policy["credentials_allowed"] is False
    assert policy["external_scripts_executed"] is False
    assert policy["hardware_actuation_allowed"] is False
    assert policy["cloud_write_allowed"] is False
    assert policy["destructive_actions_allowed"] is False
    assert policy["active_registry_changes_allowed"] is False
    assert policy["router_scoring_changes_allowed"] is False
    assert policy["global_agents_changes_allowed"] is False
    assert policy["promotion_allowed"] is False

    fixture_map = {item["candidate_id"]: item for item in fixtures["fixtures"]}
    snapshot_map = {item["candidate_id"]: item for item in manifest["records"]}
    stage_a = {item["candidate_id"]: item for item in results["stage_a"]}
    slots = results["stage_b"]

    assert len(slots) == 20
    assert len(stage_a) == 15
    assert sum(
        item.get("stage_b_candidate") is True
        for item in stage_a.values()
    ) == 5

    plan = []

    for slot in slots:
        cid = slot["candidate_id"]
        variant = slot["variant"]

        assert variant in VARIANTS
        assert cid in fixture_map
        assert cid in snapshot_map
        assert cid in stage_a
        assert slot["acceptance_pass"] is None
        assert slot["external_access_attempted"] is False

        snapshot = snapshot_map[cid]
        raw_path = REPO_ROOT / snapshot["snapshot_path"]
        raw = raw_path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()

        assert len(raw) == snapshot["byte_size"]
        assert digest == snapshot["sha256"]

        plan.append(
            {
                "fixture_id": slot["fixture_id"],
                "candidate_id": cid,
                "variant": variant,
                "action": "PLAN_ONLY",
                "external_access": False,
                "scripts_execute": False,
                "credentials_used": False,
                "hardware_actuation": False,
                "cloud_write": False,
                "destructive_action": False,
                "snapshot_verified": True,
                "snapshot_sha256": digest,
                "loaded_context_bytes": slot["loaded_context_bytes"],
            }
        )

    results["dry_run"] = {
        "status": "VALIDATED",
        "execution_performed": False,
        "external_access_attempted": False,
        "external_scripts_executed": False,
        "plans": plan,
    }
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", required=True)
    args = parser.parse_args()

    if not args.dry_run:
        raise SystemExit("only --dry-run is supported")

    results = validate_dry_run()

    print("BENCHMARK_DRY_RUN_VALID")
    print("SLOTS", len(results["dry_run"]["plans"]))
    print("EXECUTION_PERFORMED", results["dry_run"]["execution_performed"])
    print(
        "EXTERNAL_ACCESS_ATTEMPTED",
        results["dry_run"]["external_access_attempted"],
    )
    print(
        "EXTERNAL_SCRIPTS_EXECUTED",
        results["dry_run"]["external_scripts_executed"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
