#!/usr/bin/env python3
"""Validate the V8.3 fixed-revision inspection wave without network access."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from external_catalog import ExternalCatalogError, load_and_validate_catalog
from effective_coverage import generate_effective_coverage

BASE = Path("evaluation") / "external-skills"
REQUIRED_INSPECTION_FIELDS = {
    "candidate_id", "source_id", "upstream_path", "domain_pack", "source_revision",
    "license_status", "compatibility_status", "dependencies", "permissions",
    "bundled_scripts", "external_scripts_executed", "decision", "inspection_status",
    "path_status",
}
SHORTLIST_LICENSES = {"permissive", "permissive-mixed"}
SHORTLIST_COMPAT = {"compatible", "adaptation-required"}
SHORTLIST_DECISIONS = {"BENCHMARK_READY", "ADAPT_CANDIDATE"}
CLUSTER_ACTIONS = {"BENCHMARK_SIDE_BY_SIDE", "KEEP_DISTINCT", "HUMAN_REVIEW", "REFERENCE_ONLY"}
TARGET_DOMAINS = {"industrial-automation", "networking", "robotics-ros"}


def _load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ExternalCatalogError(f"{label} missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ExternalCatalogError(f"invalid {label} JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ExternalCatalogError(f"{label} must be a JSON object")
    if data.get("schema_version") != 1:
        raise ExternalCatalogError(f"{label} schema_version must be 1")
    return data


def _candidate_index(candidates: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {candidate["candidate_id"]: candidate for candidate in candidates}


def _validate_inspections(
    inspections_data: dict[str, Any],
    candidates: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    inspections = inspections_data.get("inspections")
    if not isinstance(inspections, list):
        raise ExternalCatalogError("inspections must be a list")
    if len(inspections) < 30:
        raise ExternalCatalogError("inspection wave must contain at least 30 candidates")

    base = _candidate_index(candidates)
    inspected: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(inspections):
        if not isinstance(item, dict):
            raise ExternalCatalogError(f"inspection[{index}] must be an object")
        missing = REQUIRED_INSPECTION_FIELDS - set(item)
        if missing:
            raise ExternalCatalogError(f"inspection[{index}] missing fields: {sorted(missing)}")
        cid = item["candidate_id"]
        if cid in inspected:
            raise ExternalCatalogError(f"duplicate inspection candidate: {cid}")
        raw = base.get(cid)
        if raw is None:
            raise ExternalCatalogError(f"inspection candidate is not in base catalog: {cid}")
        for key in ("source_id", "upstream_path", "domain_pack"):
            if item[key] != raw[key]:
                raise ExternalCatalogError(f"inspection/base mismatch for {cid}: {key}")
        if not isinstance(item["source_revision"], str) or not item["source_revision"].strip():
            raise ExternalCatalogError(f"missing source revision: {cid}")
        if not isinstance(item["dependencies"], list) or not isinstance(item["permissions"], list):
            raise ExternalCatalogError(f"dependencies/permissions must be lists: {cid}")
        if not isinstance(item["bundled_scripts"], bool):
            raise ExternalCatalogError(f"bundled_scripts must be bool: {cid}")
        if item["external_scripts_executed"] is not False:
            raise ExternalCatalogError(f"external script execution is forbidden: {cid}")
        if item["path_status"] == "DRIFT":
            if not (
                item["compatibility_status"] == "blocked"
                and item["inspection_status"] == "BLOCKED_PATH_DRIFT"
                and item["decision"] == "REJECTED"
            ):
                raise ExternalCatalogError(f"path drift must be blocked and rejected: {cid}")
        elif item["path_status"] != "PRESENT":
            raise ExternalCatalogError(f"invalid path_status: {cid}")
        inspected[cid] = item

    sources = {item["source_id"] for item in inspections}
    domains = {item["domain_pack"] for item in inspections}
    if len(sources) < 4:
        raise ExternalCatalogError("inspection wave must cover at least 4 sources")
    if len(domains) < 15:
        raise ExternalCatalogError("inspection wave must cover at least 15 domain packs")
    if sum(item["domain_pack"] == "documentation-guide" for item in inspections) < 3:
        raise ExternalCatalogError("documentation-guide needs at least 3 inspected candidates")
    if sum(item["domain_pack"] == "big-data" for item in inspections) < 3:
        raise ExternalCatalogError("big-data needs at least 3 inspected candidates")

    summary = inspections_data.get("summary")
    if not isinstance(summary, dict):
        raise ExternalCatalogError("inspection summary missing")
    if summary.get("active_import_count") != 0 or summary.get("external_scripts_executed_count") != 0:
        raise ExternalCatalogError("inspection wave must not import ACTIVE skills or execute external scripts")
    return inspected


def _validate_shortlist(data: dict[str, Any], inspected: dict[str, dict[str, Any]]) -> tuple[int, int]:
    ids = data.get("candidate_ids")
    if not isinstance(ids, list) or len(ids) != len(set(ids)):
        raise ExternalCatalogError("shortlist candidate_ids must be a unique list")
    if not 15 <= len(ids) <= 25:
        raise ExternalCatalogError("shortlist must contain 15-25 candidates")
    sources: set[str] = set()
    domains: set[str] = set()
    for cid in ids:
        item = inspected.get(cid)
        if item is None:
            raise ExternalCatalogError(f"shortlist candidate was not inspected: {cid}")
        if item["license_status"] not in SHORTLIST_LICENSES:
            raise ExternalCatalogError(f"shortlist license not cleared: {cid}")
        if item["path_status"] != "PRESENT" or item["inspection_status"] != "INSPECTED":
            raise ExternalCatalogError(f"shortlist path/inspection not cleared: {cid}")
        if item["compatibility_status"] not in SHORTLIST_COMPAT:
            raise ExternalCatalogError(f"shortlist compatibility not cleared: {cid}")
        if item["decision"] not in SHORTLIST_DECISIONS:
            raise ExternalCatalogError(f"shortlist decision not eligible: {cid}")
        if item["external_scripts_executed"] is not False:
            raise ExternalCatalogError(f"shortlist external script execution marker set: {cid}")
        sources.add(item["source_id"])
        domains.add(item["domain_pack"])
    if len(sources) < 4:
        raise ExternalCatalogError("shortlist must cover at least 4 sources")
    if len(domains) < 10:
        raise ExternalCatalogError("shortlist must cover at least 10 domain packs")
    if data.get("active_import_count") != 0 or data.get("external_scripts_executed") is not False:
        raise ExternalCatalogError("shortlist must remain non-ACTIVE and no-execution")
    return len(sources), len(domains)


def _validate_clusters(data: dict[str, Any], inspected: dict[str, dict[str, Any]]) -> None:
    clusters = data.get("clusters")
    if not isinstance(clusters, list) or not clusters:
        raise ExternalCatalogError("duplicate clusters must be a non-empty list")
    for cluster in clusters:
        if cluster.get("recommended_action") not in CLUSTER_ACTIONS:
            raise ExternalCatalogError(f"invalid cluster action: {cluster.get('cluster_id')}")
        ids = cluster.get("candidate_ids")
        if not isinstance(ids, list) or len(ids) < 2:
            raise ExternalCatalogError(f"cluster requires at least two candidates: {cluster.get('cluster_id')}")
        for cid in ids:
            if cid not in inspected:
                raise ExternalCatalogError(f"cluster member was not inspected: {cid}")
    for key in ("automatic_merge_count", "automatic_archive_count", "automatic_delete_count"):
        if data.get(key) != 0:
            raise ExternalCatalogError(f"automatic lifecycle action forbidden: {key}")


def _validate_targeted_discovery(data: dict[str, Any]) -> None:
    rows = data.get("targeted_discovery")
    if not isinstance(rows, list):
        raise ExternalCatalogError("targeted_discovery must be a list")
    by_domain = {row.get("domain_pack"): row for row in rows if isinstance(row, dict)}
    if not TARGET_DOMAINS <= set(by_domain):
        raise ExternalCatalogError("targeted discovery must cover industrial-automation, networking, robotics-ros")
    industrial = by_domain["industrial-automation"]
    if industrial.get("decision") != "KEEP_GAP_OPEN" or industrial.get("candidate_ids") != []:
        raise ExternalCatalogError("industrial-automation gap must remain open without a synthetic candidate")


def validate_repository(root: Path) -> dict[str, int]:
    _, _, candidates = load_and_validate_catalog(root)
    inspection_data = _load_json(root / BASE / "inspection-results.json", "inspection results")
    clusters = _load_json(root / BASE / "duplicate-clusters.json", "duplicate clusters")
    shortlist = _load_json(root / BASE / "benchmark-shortlist.json", "benchmark shortlist")

    inspected = _validate_inspections(inspection_data, candidates)
    shortlist_sources, shortlist_domains = _validate_shortlist(shortlist, inspected)
    _validate_clusters(clusters, inspected)
    _validate_targeted_discovery(inspection_data)

    effective = generate_effective_coverage(root)
    domains = effective.get("domains")
    if not isinstance(domains, list):
        raise ExternalCatalogError("effective coverage domains missing")
    desired = sum(int(row["desired_capability_count"]) for row in domains)
    covered = sum(int(row["current_coverage_count"]) for row in domains)
    if (desired, covered, len(candidates)) != (172, 29, 100):
        raise ExternalCatalogError(
            f"current ACTIVE coverage changed unexpectedly: desired={desired}, covered={covered}, candidates={len(candidates)}"
        )

    return {
        "inspected": len(inspected),
        "sources": len({item["source_id"] for item in inspected.values()}),
        "domains": len({item["domain_pack"] for item in inspected.values()}),
        "shortlist": len(shortlist["candidate_ids"]),
        "shortlist_sources": shortlist_sources,
        "shortlist_domains": shortlist_domains,
        "desired": desired,
        "covered": covered,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    try:
        result = validate_repository(Path(args.root).resolve())
    except ExternalCatalogError as exc:
        print(f"RESULT FAIL: {exc}")
        return 1
    print(f"INSPECTED {result['inspected']}")
    print(f"SOURCES {result['sources']}")
    print(f"DOMAINS {result['domains']}")
    print(f"SHORTLIST {result['shortlist']}")
    print(f"SHORTLIST_SOURCES {result['shortlist_sources']}")
    print(f"SHORTLIST_DOMAINS {result['shortlist_domains']}")
    print("ACTIVE_IMPORTS 0")
    print("EXTERNAL_SCRIPTS_EXECUTED 0")
    print(f"CURRENT_COVERAGE {result['covered']}/{result['desired']}")
    print("RESULT PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
