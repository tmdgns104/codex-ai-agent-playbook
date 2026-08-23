#!/usr/bin/env python3
"""Deterministic validation and coverage reporting for V8.3 expert skill catalog."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

VALID_SOURCE_TIERS = {"A", "B", "C", "discovery"}
VALID_DECISIONS = {
    "DISCOVERED",
    "INSPECTED",
    "BENCHMARK_READY",
    "ADOPT_CANDIDATE",
    "ADAPT_CANDIDATE",
    "REFERENCE_ONLY",
    "REJECTED",
    "PROMOTED",
}
VALID_LICENSE_STATUS = {
    "unknown",
    "verified",
    "mixed-reviewed",
    "reference-only",
    "rejected",
}
VALID_COMPATIBILITY_STATUS = {
    "unknown",
    "compatible",
    "adaptation-required",
    "incompatible",
}
PROTECTED_DOMAIN_PACKS = {"documentation-guide", "big-data"}
REQUIRED_BENCHMARK_VARIANTS = {
    "baseline-no-optional",
    "current-playbook",
    "external-expert",
    "adapted-playbook",
}
REQUIRED_EVIDENCE_FIELDS = {
    "acceptance_result",
    "selected_capabilities",
    "selected_count",
    "loaded_skill_bytes",
    "gate_result",
    "dependency_burden",
    "execution_time_ms",
    "notes",
}


class ExternalCatalogError(ValueError):
    """Raised when V8.3 external catalog data violates the contract."""


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


def _require_nonempty_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ExternalCatalogError(f"{label} must be a non-empty string")
    return value.strip()


def _require_string_list(value: Any, label: str, *, allow_empty: bool = True) -> list[str]:
    if not isinstance(value, list):
        raise ExternalCatalogError(f"{label} must be a list")
    if not allow_empty and not value:
        raise ExternalCatalogError(f"{label} must not be empty")
    result: list[str] = []
    for item in value:
        text = _require_nonempty_string(item, label)
        if text in result:
            raise ExternalCatalogError(f"{label} contains duplicate value: {text}")
        result.append(text)
    return result


def validate_sources_document(data: dict[str, Any]) -> set[str]:
    if data.get("schema_version") != 1:
        raise ExternalCatalogError("sources schema_version must be 1")
    sources = data.get("sources")
    if not isinstance(sources, list):
        raise ExternalCatalogError("sources must be a list")

    source_ids: set[str] = set()
    trusted_count = 0
    discovery_count = 0
    for index, entry in enumerate(sources):
        if not isinstance(entry, dict):
            raise ExternalCatalogError(f"source[{index}] must be an object")
        source_id = _require_nonempty_string(entry.get("id"), f"source[{index}].id")
        if source_id in source_ids:
            raise ExternalCatalogError(f"duplicate source id: {source_id}")
        source_ids.add(source_id)

        repository = _require_nonempty_string(entry.get("repository"), f"source[{source_id}].repository")
        if "/" not in repository:
            raise ExternalCatalogError(f"source repository must use owner/name form: {source_id}")

        tier = entry.get("tier")
        if tier not in VALID_SOURCE_TIERS:
            raise ExternalCatalogError(f"invalid source tier for {source_id}: {tier}")
        if tier == "discovery":
            discovery_count += 1
        else:
            trusted_count += 1

        _require_nonempty_string(entry.get("license"), f"source[{source_id}].license")
        _require_nonempty_string(entry.get("role"), f"source[{source_id}].role")
        _require_nonempty_string(entry.get("import_policy"), f"source[{source_id}].import_policy")
        _require_nonempty_string(entry.get("observed_claim"), f"source[{source_id}].observed_claim")
        _require_string_list(entry.get("compatibility"), f"source[{source_id}].compatibility")
        _require_string_list(entry.get("focus"), f"source[{source_id}].focus", allow_empty=False)
        if entry.get("auto_execute_external_scripts") is not False:
            raise ExternalCatalogError(
                f"external script auto-execution must remain disabled: {source_id}"
            )

    if trusted_count < 6:
        raise ExternalCatalogError("source baseline requires at least 6 trusted sources")
    if discovery_count < 1:
        raise ExternalCatalogError("source baseline requires at least 1 discovery-only source")
    return source_ids


def validate_domain_packs_document(data: dict[str, Any]) -> dict[str, list[str]]:
    if data.get("schema_version") != 1:
        raise ExternalCatalogError("domain-packs schema_version must be 1")
    packs = data.get("domain_packs")
    if not isinstance(packs, list):
        raise ExternalCatalogError("domain_packs must be a list")
    if len(packs) < 25:
        raise ExternalCatalogError("domain baseline requires at least 25 packs")

    result: dict[str, list[str]] = {}
    for index, entry in enumerate(packs):
        if not isinstance(entry, dict):
            raise ExternalCatalogError(f"domain_packs[{index}] must be an object")
        domain_id = _require_nonempty_string(entry.get("id"), f"domain_packs[{index}].id")
        if domain_id in result:
            raise ExternalCatalogError(f"duplicate domain pack id: {domain_id}")
        _require_nonempty_string(entry.get("label"), f"domain_pack[{domain_id}].label")
        desired = _require_string_list(
            entry.get("desired_capabilities"),
            f"domain_pack[{domain_id}].desired_capabilities",
            allow_empty=False,
        )
        result[domain_id] = desired

    missing = PROTECTED_DOMAIN_PACKS - set(result)
    if missing:
        raise ExternalCatalogError(f"missing protected domain pack(s): {sorted(missing)}")
    return result


def validate_candidates_document(
    data: dict[str, Any], *, source_ids: set[str], domain_ids: set[str]
) -> list[dict[str, Any]]:
    if data.get("schema_version") != 1:
        raise ExternalCatalogError("candidates schema_version must be 1")
    candidates = data.get("candidates")
    if not isinstance(candidates, list):
        raise ExternalCatalogError("candidates must be a list")

    candidate_ids: set[str] = set()
    validated: list[dict[str, Any]] = []
    for index, entry in enumerate(candidates):
        if not isinstance(entry, dict):
            raise ExternalCatalogError(f"candidate[{index}] must be an object")
        candidate_id = _require_nonempty_string(entry.get("candidate_id"), f"candidate[{index}].candidate_id")
        if candidate_id in candidate_ids:
            raise ExternalCatalogError(f"duplicate candidate id: {candidate_id}")
        candidate_ids.add(candidate_id)

        source_id = _require_nonempty_string(entry.get("source_id"), f"candidate[{candidate_id}].source_id")
        if source_id not in source_ids:
            raise ExternalCatalogError(f"unknown source id for candidate {candidate_id}: {source_id}")
        domain_pack = _require_nonempty_string(entry.get("domain_pack"), f"candidate[{candidate_id}].domain_pack")
        if domain_pack not in domain_ids:
            raise ExternalCatalogError(f"unknown domain pack for candidate {candidate_id}: {domain_pack}")

        _require_nonempty_string(entry.get("upstream_path"), f"candidate[{candidate_id}].upstream_path")
        source_revision = entry.get("source_revision")
        if source_revision is not None:
            _require_nonempty_string(source_revision, f"candidate[{candidate_id}].source_revision")

        decision = entry.get("decision")
        if decision not in VALID_DECISIONS:
            raise ExternalCatalogError(f"invalid decision for candidate {candidate_id}: {decision}")
        license_status = entry.get("license_status")
        if license_status not in VALID_LICENSE_STATUS:
            raise ExternalCatalogError(f"invalid license_status for candidate {candidate_id}: {license_status}")
        compatibility_status = entry.get("compatibility_status")
        if compatibility_status not in VALID_COMPATIBILITY_STATUS:
            raise ExternalCatalogError(
                f"invalid compatibility_status for candidate {candidate_id}: {compatibility_status}"
            )

        _require_string_list(entry.get("dependencies"), f"candidate[{candidate_id}].dependencies")
        _require_string_list(entry.get("permissions"), f"candidate[{candidate_id}].permissions")
        if not isinstance(entry.get("bundled_scripts"), bool):
            raise ExternalCatalogError(f"bundled_scripts must be boolean: {candidate_id}")
        if entry.get("external_scripts_executed") is not False:
            raise ExternalCatalogError(f"external scripts must not execute during intake: {candidate_id}")

        if decision in {"ADOPT_CANDIDATE", "ADAPT_CANDIDATE", "PROMOTED"} and license_status == "unknown":
            raise ExternalCatalogError(f"unknown license cannot advance candidate: {candidate_id}")
        if decision == "PROMOTED" and license_status != "verified":
            raise ExternalCatalogError(f"PROMOTED candidate requires verified license: {candidate_id}")
        if decision == "PROMOTED" and compatibility_status not in {"compatible", "adaptation-required"}:
            raise ExternalCatalogError(f"PROMOTED candidate requires compatible status: {candidate_id}")

        validated.append(entry)
    return validated


def validate_benchmark_schema_document(data: dict[str, Any]) -> None:
    if data.get("schema_version") != 1:
        raise ExternalCatalogError("benchmark schema_version must be 1")
    variants = set(_require_string_list(data.get("variants"), "benchmark.variants", allow_empty=False))
    missing_variants = REQUIRED_BENCHMARK_VARIANTS - variants
    if missing_variants:
        raise ExternalCatalogError(f"missing benchmark variant(s): {sorted(missing_variants)}")
    evidence = set(
        _require_string_list(data.get("evidence_fields"), "benchmark.evidence_fields", allow_empty=False)
    )
    missing_evidence = REQUIRED_EVIDENCE_FIELDS - evidence
    if missing_evidence:
        raise ExternalCatalogError(f"missing benchmark evidence field(s): {sorted(missing_evidence)}")
    if data.get("llm_self_report_is_sufficient") is not False:
        raise ExternalCatalogError("LLM self-report must not be sufficient benchmark evidence")


def _load_active_capability_ids(root: Path) -> set[str]:
    registry = _load_json(root / "capability-library" / "registry.json", "active registry")
    capabilities = registry.get("capabilities")
    if not isinstance(capabilities, list):
        raise ExternalCatalogError("active registry capabilities must be a list")
    result: set[str] = set()
    for entry in capabilities:
        if isinstance(entry, dict) and isinstance(entry.get("id"), str) and entry["id"].strip():
            result.add(entry["id"].strip())
    return result


def build_coverage_report(
    *, domain_packs: dict[str, list[str]], candidates: list[dict[str, Any]], active_ids: set[str]
) -> dict[str, Any]:
    reports: list[dict[str, Any]] = []
    for domain_id in sorted(domain_packs):
        desired = list(domain_packs[domain_id])
        domain_candidates = [c for c in candidates if c["domain_pack"] == domain_id]
        inspected = [c for c in domain_candidates if c["decision"] != "DISCOVERED"]
        benchmark_ready = [
            c
            for c in domain_candidates
            if c["decision"]
            in {"BENCHMARK_READY", "ADOPT_CANDIDATE", "ADAPT_CANDIDATE", "PROMOTED"}
        ]
        active_covered = sorted(set(desired) & active_ids)
        reports.append(
            {
                "domain_pack": domain_id,
                "desired_capability_count": len(desired),
                "discovered_candidate_count": len(domain_candidates),
                "inspected_count": len(inspected),
                "benchmark_ready_count": len(benchmark_ready),
                "active_coverage_count": len(active_covered),
                "active_covered_capabilities": active_covered,
                "uncovered_active_capabilities": sorted(set(desired) - active_ids),
            }
        )

    return {
        "schema_version": 1,
        "domain_pack_count": len(domain_packs),
        "candidate_count": len(candidates),
        "active_capability_count": len(active_ids),
        "protected_domain_packs": sorted(PROTECTED_DOMAIN_PACKS),
        "domains": reports,
    }


def load_and_validate_catalog(root: Path) -> tuple[dict[str, Any], dict[str, list[str]], list[dict[str, Any]]]:
    base = root / "evaluation" / "external-skills"
    sources = _load_json(base / "sources.json", "sources")
    source_ids = validate_sources_document(sources)
    domains_data = _load_json(base / "domain-packs.json", "domain packs")
    domains = validate_domain_packs_document(domains_data)
    candidates_data = _load_json(base / "candidates.json", "candidates")
    candidates = validate_candidates_document(
        candidates_data, source_ids=source_ids, domain_ids=set(domains)
    )
    benchmark = _load_json(base / "benchmark-schema.json", "benchmark schema")
    validate_benchmark_schema_document(benchmark)
    return sources, domains, candidates


def generate_coverage_report(root: Path) -> dict[str, Any]:
    _, domains, candidates = load_and_validate_catalog(root)
    active_ids = _load_active_capability_ids(root)
    return build_coverage_report(domain_packs=domains, candidates=candidates, active_ids=active_ids)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Playbook repository root")
    parser.add_argument("--write-report", help="Optional path, relative to root unless absolute")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    try:
        report = generate_coverage_report(root)
    except ExternalCatalogError as exc:
        print(f"RESULT FAIL: {exc}")
        return 1

    rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.write_report:
        report_path = Path(args.write_report)
        if not report_path.is_absolute():
            report_path = root / report_path
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(rendered, encoding="utf-8")
        print(f"REPORT {report_path}")
    else:
        print(rendered, end="")
    print("RESULT PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
