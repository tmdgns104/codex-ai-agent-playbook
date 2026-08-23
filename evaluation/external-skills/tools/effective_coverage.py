#!/usr/bin/env python3
"""Resolve V8.3 domain coverage using explicit current capability mappings."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from external_catalog import ExternalCatalogError, load_and_validate_catalog

VALID_PROVIDER_SOURCES = {"active-registry", "core-skill"}


def _load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ExternalCatalogError(f"{label} missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ExternalCatalogError(f"invalid {label} JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ExternalCatalogError(f"{label} must be a JSON object")
    return data


def _active_registry_ids(root: Path) -> set[str]:
    data = _load_json(root / "capability-library" / "registry.json", "active registry")
    capabilities = data.get("capabilities")
    if not isinstance(capabilities, list):
        raise ExternalCatalogError("active registry capabilities must be a list")
    result: set[str] = set()
    for entry in capabilities:
        if isinstance(entry, dict) and isinstance(entry.get("id"), str) and entry["id"].strip():
            result.add(entry["id"].strip())
    return result


def _core_skill_ids(root: Path) -> set[str]:
    base = root / ".agents" / "skills"
    if not base.exists():
        raise ExternalCatalogError(f"core skill directory missing: {base}")
    return {
        path.name
        for path in base.iterdir()
        if path.is_dir() and (path / "SKILL.md").is_file()
    }


def validate_current_coverage_map(
    data: dict[str, Any],
    *,
    domain_packs: dict[str, list[str]],
    active_registry_ids: set[str],
    core_skill_ids: set[str],
) -> dict[str, dict[str, list[str]]]:
    if data.get("schema_version") != 1:
        raise ExternalCatalogError("current coverage map schema_version must be 1")
    if data.get("mapping_policy") != "explicit-conservative":
        raise ExternalCatalogError("current coverage mapping_policy must remain explicit-conservative")

    providers = data.get("providers")
    if not isinstance(providers, list):
        raise ExternalCatalogError("current coverage providers must be a list")

    seen: set[str] = set()
    by_domain: dict[str, dict[str, list[str]]] = {domain_id: {} for domain_id in domain_packs}
    for index, provider in enumerate(providers):
        if not isinstance(provider, dict):
            raise ExternalCatalogError(f"coverage provider[{index}] must be an object")
        provider_id = provider.get("id")
        if not isinstance(provider_id, str) or not provider_id.strip():
            raise ExternalCatalogError(f"coverage provider[{index}].id must be non-empty")
        provider_id = provider_id.strip()
        if provider_id in seen:
            raise ExternalCatalogError(f"duplicate coverage provider: {provider_id}")
        seen.add(provider_id)

        source = provider.get("source")
        if source not in VALID_PROVIDER_SOURCES:
            raise ExternalCatalogError(f"invalid provider source for {provider_id}: {source}")
        if source == "active-registry" and provider_id not in active_registry_ids:
            raise ExternalCatalogError(f"mapped active provider is not in registry: {provider_id}")
        if source == "core-skill" and provider_id not in core_skill_ids:
            raise ExternalCatalogError(f"mapped core provider is not installed in repository: {provider_id}")

        coverage = provider.get("coverage")
        if not isinstance(coverage, dict) or not coverage:
            raise ExternalCatalogError(f"coverage must be a non-empty object: {provider_id}")
        for domain_id, capabilities in coverage.items():
            if domain_id not in domain_packs:
                raise ExternalCatalogError(f"unknown mapped domain for {provider_id}: {domain_id}")
            if not isinstance(capabilities, list) or not capabilities:
                raise ExternalCatalogError(f"mapped capabilities must be a non-empty list: {provider_id}/{domain_id}")
            desired = set(domain_packs[domain_id])
            for capability in capabilities:
                if not isinstance(capability, str) or not capability.strip():
                    raise ExternalCatalogError(f"invalid mapped capability: {provider_id}/{domain_id}")
                capability = capability.strip()
                if capability not in desired:
                    raise ExternalCatalogError(
                        f"mapped capability is not declared by domain pack: {provider_id}/{domain_id}/{capability}"
                    )
                providers_for_capability = by_domain[domain_id].setdefault(capability, [])
                if provider_id not in providers_for_capability:
                    providers_for_capability.append(provider_id)

    for domain in by_domain.values():
        for providers_for_capability in domain.values():
            providers_for_capability.sort()
    return by_domain


def generate_effective_coverage(root: Path) -> dict[str, Any]:
    _, domain_packs, candidates = load_and_validate_catalog(root)
    active_ids = _active_registry_ids(root)
    core_ids = _core_skill_ids(root)
    map_data = _load_json(
        root / "evaluation" / "external-skills" / "current-coverage-map.json",
        "current coverage map",
    )
    claims = validate_current_coverage_map(
        map_data,
        domain_packs=domain_packs,
        active_registry_ids=active_ids,
        core_skill_ids=core_ids,
    )

    domains: list[dict[str, Any]] = []
    total_desired = 0
    total_covered = 0
    for domain_id in sorted(domain_packs):
        desired = list(domain_packs[domain_id])
        total_desired += len(desired)
        covered = sorted(claims[domain_id])
        total_covered += len(covered)
        domain_candidates = [candidate for candidate in candidates if candidate["domain_pack"] == domain_id]
        inspected = [candidate for candidate in domain_candidates if candidate["decision"] != "DISCOVERED"]
        benchmark_ready = [
            candidate
            for candidate in domain_candidates
            if candidate["decision"]
            in {"BENCHMARK_READY", "ADOPT_CANDIDATE", "ADAPT_CANDIDATE", "PROMOTED"}
        ]
        domains.append(
            {
                "domain_pack": domain_id,
                "desired_capability_count": len(desired),
                "current_coverage_count": len(covered),
                "current_covered_capabilities": covered,
                "coverage_providers": {capability: claims[domain_id][capability] for capability in covered},
                "uncovered_capabilities": sorted(set(desired) - set(covered)),
                "discovered_candidate_count": len(domain_candidates),
                "inspected_count": len(inspected),
                "benchmark_ready_count": len(benchmark_ready),
            }
        )

    return {
        "schema_version": 1,
        "report_type": "effective-current-coverage",
        "mapping_policy": "explicit-conservative",
        "active_registry_capability_count": len(active_ids),
        "core_skill_count": len(core_ids),
        "mapped_provider_count": len(map_data.get("providers", [])),
        "domain_pack_count": len(domain_packs),
        "candidate_count": len(candidates),
        "desired_capability_total": total_desired,
        "current_covered_capability_total": total_covered,
        "uncovered_capability_total": total_desired - total_covered,
        "domains": domains,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Playbook repository root")
    parser.add_argument("--write-report", help="Optional output path relative to root unless absolute")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    try:
        report = generate_effective_coverage(root)
    except ExternalCatalogError as exc:
        print(f"RESULT FAIL: {exc}")
        return 1

    rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.write_report:
        path = Path(args.write_report)
        if not path.is_absolute():
            path = root / path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered, encoding="utf-8")
        print(f"REPORT {path}")
    else:
        print(rendered, end="")
    print("RESULT PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
