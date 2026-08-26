#!/usr/bin/env python3
"""Validate V8.3 external-skill inspection artifacts without network execution."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from external_catalog import ExternalCatalogError, load_and_validate_catalog

BASE = Path("evaluation") / "external-skills"
ALLOWED_DECISIONS = {"BENCHMARK_READY", "REFERENCE_ONLY", "REJECTED"}
REVISION_RE = re.compile(r"^[0-9a-f]{40}$")
PROTECTED_DOMAINS = {"documentation-guide", "big-data"}
TARGETED_DOMAINS = {"industrial-automation", "networking", "robotics-ros"}


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


def _text(entry: dict[str, Any], field: str, context: str) -> str:
    value = entry.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ExternalCatalogError(f"{context}.{field} must be a non-empty string")
    return value.strip()


def _list(entry: dict[str, Any], field: str, context: str) -> list[Any]:
    value = entry.get(field)
    if not isinstance(value, list):
        raise ExternalCatalogError(f"{context}.{field} must be a list")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_manifest_records(root: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    manifest = _load_json(root / BASE / "inspection-results.json", "inspection result manifest")
    if manifest.get("inspection_policy") != "fixed-revision-static-only":
        raise ExternalCatalogError("inspection policy must remain fixed-revision-static-only")
    if manifest.get("external_scripts_executed") is not False or manifest.get("active_import_count") != 0:
        raise ExternalCatalogError("inspection manifest must remain no-execution and non-ACTIVE")
    records_name = _text(manifest, "records_file", "inspection result manifest")
    followups_name = _text(manifest, "targeted_discovery_file", "inspection result manifest")
    if Path(records_name).name != records_name or Path(followups_name).name != followups_name:
        raise ExternalCatalogError("inspection manifest references must remain local evaluation filenames")
    records = _load_json(root / BASE / records_name, "inspection records")
    followups = _load_json(root / BASE / followups_name, "discovery followups")
    return manifest, records, followups


def validate_repository(root: Path) -> dict[str, Any]:
    _, domain_packs, candidates = load_and_validate_catalog(root)
    manifest, records_data, followups_data = _load_manifest_records(root)
    clusters_data = _load_json(root / BASE / "duplicate-clusters.json", "duplicate clusters")
    shortlist_data = _load_json(root / BASE / "benchmark-shortlist.json", "benchmark shortlist")

    compatibility = manifest.get("compatibility_resolution")
    if not isinstance(compatibility, dict) or set(compatibility) != ALLOWED_DECISIONS:
        raise ExternalCatalogError("compatibility_resolution must cover all provisional decisions")

    candidate_by_id = {candidate["candidate_id"]: candidate for candidate in candidates}
    inspections = records_data.get("inspections")
    if not isinstance(inspections, list) or len(inspections) < 30:
        raise ExternalCatalogError("inspection wave must contain at least 30 candidates")
    if records_data.get("external_scripts_executed") is not False:
        raise ExternalCatalogError("inspection records must keep external_scripts_executed=false")

    inspected: dict[str, dict[str, Any]] = {}
    domain_counts: Counter[str] = Counter()
    sources: set[str] = set()
    benchmark_ready: set[str] = set()
    for index, item in enumerate(inspections):
        if not isinstance(item, dict):
            raise ExternalCatalogError(f"inspection[{index}] must be an object")
        context = f"inspection[{index}]"
        cid = _text(item, "candidate_id", context)
        if cid in inspected:
            raise ExternalCatalogError(f"duplicate inspection candidate: {cid}")
        raw = candidate_by_id.get(cid)
        if raw is None:
            raise ExternalCatalogError(f"inspection candidate is not in base catalog: {cid}")
        inspected[cid] = item
        for field in ("source_id", "upstream_path", "domain_pack"):
            if _text(item, field, context) != raw[field]:
                raise ExternalCatalogError(f"inspection/base mismatch for {cid}: {field}")
        revision = _text(item, "source_revision", context)
        if not REVISION_RE.fullmatch(revision):
            raise ExternalCatalogError(f"source_revision must be exact 40-char lowercase SHA: {cid}")
        license_status = _text(item, "license_status", context)
        _text(item, "dependency_burden", context)
        _list(item, "dependencies", context)
        _list(item, "permissions", context)
        _text(item, "network_auth_notes", context)
        if not isinstance(item.get("bundled_scripts"), bool):
            raise ExternalCatalogError(f"bundled_scripts must be bool: {cid}")
        if item.get("external_scripts_executed") is not False:
            raise ExternalCatalogError(f"external script execution is forbidden: {cid}")
        findings = _list(item, "safety_findings", context)
        if not findings or not all(isinstance(value, str) and value.strip() for value in findings):
            raise ExternalCatalogError(f"safety_findings must contain strings: {cid}")
        _list(item, "overlap_with_current", context)
        _text(item, "inspection_notes", context)
        decision = _text(item, "provisional_decision", context)
        if decision not in ALLOWED_DECISIONS:
            raise ExternalCatalogError(f"invalid provisional decision: {cid}/{decision}")
        if decision == "BENCHMARK_READY" and license_status.lower() in {"unknown", "source-available"}:
            raise ExternalCatalogError(f"uncleared license cannot be BENCHMARK_READY: {cid}")
        if decision == "BENCHMARK_READY":
            benchmark_ready.add(cid)
        domain = item["domain_pack"]
        if domain not in domain_packs:
            raise ExternalCatalogError(f"unknown inspection domain: {domain}")
        domain_counts[domain] += 1
        sources.add(item["source_id"])

    if len(sources) < 4:
        raise ExternalCatalogError("inspection wave must cover at least 4 sources")
    if len(domain_counts) < 15:
        raise ExternalCatalogError("inspection wave must cover at least 15 domain packs")
    if domain_counts["documentation-guide"] < 3:
        raise ExternalCatalogError("documentation-guide needs at least 3 inspected candidates")
    if domain_counts["big-data"] < 3:
        raise ExternalCatalogError("big-data needs at least 3 inspected candidates")

    clusters = clusters_data.get("clusters")
    if not isinstance(clusters, list) or not clusters:
        raise ExternalCatalogError("duplicate clusters must be a non-empty list")
    seen_clusters: set[str] = set()
    for index, cluster in enumerate(clusters):
        if not isinstance(cluster, dict):
            raise ExternalCatalogError(f"cluster[{index}] must be an object")
        cluster_id = _text(cluster, "cluster_id", f"cluster[{index}]")
        if cluster_id in seen_clusters:
            raise ExternalCatalogError(f"duplicate cluster_id: {cluster_id}")
        seen_clusters.add(cluster_id)
        members = _list(cluster, "candidate_ids", f"cluster[{index}]")
        if len(members) < 2 or len(set(members)) != len(members):
            raise ExternalCatalogError(f"cluster requires at least two unique members: {cluster_id}")
        if any(member not in inspected for member in members):
            raise ExternalCatalogError(f"cluster contains uninspected member: {cluster_id}")
        _text(cluster, "reason", f"cluster[{index}]")
    for field in ("automatic_merge_count", "automatic_archive_count", "automatic_delete_count"):
        if clusters_data.get(field) != 0:
            raise ExternalCatalogError(f"automatic lifecycle action forbidden: {field}")

    shortlist = shortlist_data.get("entries")
    if not isinstance(shortlist, list) or len(shortlist) < 15:
        raise ExternalCatalogError("benchmark shortlist must contain at least 15 entries")
    if shortlist_data.get("external_scripts_executed") is not False or shortlist_data.get("active_import_count") != 0:
        raise ExternalCatalogError("shortlist must remain no-execution and non-ACTIVE")
    shortlist_ids: list[str] = []
    shortlist_domains: set[str] = set()
    shortlist_sources: set[str] = set()
    for index, entry in enumerate(shortlist):
        if not isinstance(entry, dict):
            raise ExternalCatalogError(f"shortlist[{index}] must be an object")
        cid = _text(entry, "candidate_id", f"shortlist[{index}]")
        _text(entry, "reason", f"shortlist[{index}]")
        if cid in shortlist_ids:
            raise ExternalCatalogError(f"duplicate shortlist candidate: {cid}")
        if cid not in benchmark_ready:
            raise ExternalCatalogError(f"shortlist candidate is not BENCHMARK_READY: {cid}")
        shortlist_ids.append(cid)
        shortlist_domains.add(inspected[cid]["domain_pack"])
        shortlist_sources.add(inspected[cid]["source_id"])
    if len(shortlist_domains) < 10:
        raise ExternalCatalogError("shortlist must cover at least 10 domain packs")
    for domain in PROTECTED_DOMAINS:
        if not any(inspected[cid]["domain_pack"] == domain for cid in shortlist_ids):
            raise ExternalCatalogError(f"shortlist omitted protected domain: {domain}")
    if shortlist_data.get("candidate_count") != len(shortlist_ids):
        raise ExternalCatalogError("shortlist candidate_count mismatch")
    if shortlist_data.get("domain_pack_count") != len(shortlist_domains):
        raise ExternalCatalogError("shortlist domain_pack_count mismatch")
    if shortlist_data.get("source_count") != len(shortlist_sources):
        raise ExternalCatalogError("shortlist source_count mismatch")

    followups = followups_data.get("followups")
    if not isinstance(followups, list):
        raise ExternalCatalogError("discovery followups must be a list")
    if followups_data.get("external_scripts_executed") is not False:
        raise ExternalCatalogError("discovery followups must remain no-execution")
    followup_domains = {
        row.get("domain_pack")
        for row in followups
        if isinstance(row, dict) and isinstance(row.get("domain_pack"), str)
    }
    if not TARGETED_DOMAINS <= followup_domains:
        raise ExternalCatalogError("targeted discovery must cover industrial-automation, networking, robotics-ros")
    industrial_rows = [row for row in followups if isinstance(row, dict) and row.get("domain_pack") == "industrial-automation"]
    if len(industrial_rows) != 1 or industrial_rows[0].get("status") != "gap-retained":
        raise ExternalCatalogError("industrial-automation gap must remain explicitly retained")

    return {
        "inspected": len(inspected),
        "inspection_sources": len(sources),
        "inspection_domains": len(domain_counts),
        "documentation_guide_inspected": domain_counts["documentation-guide"],
        "big_data_inspected": domain_counts["big-data"],
        "benchmark_ready": len(benchmark_ready),
        "duplicate_clusters": len(clusters),
        "shortlist": len(shortlist_ids),
        "shortlist_sources": len(shortlist_sources),
        "shortlist_domains": len(shortlist_domains),
        "external_scripts_executed": 0,
        "active_imports": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--write-report")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    registry = root / "capability-library" / "registry.json"
    before = _sha256(registry)
    try:
        result = validate_repository(root)
    except ExternalCatalogError as exc:
        print(f"RESULT FAIL: {exc}")
        return 1
    if _sha256(registry) != before:
        print("RESULT FAIL: ACTIVE registry changed during inspection validation")
        return 1
    result["active_registry_unchanged"] = True
    if args.write_report:
        path = Path(args.write_report)
        if not path.is_absolute():
            path = root / path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"REPORT {path}")
    for key in sorted(result):
        print(f"{key.upper()} {result[key]}")
    print("RESULT PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
