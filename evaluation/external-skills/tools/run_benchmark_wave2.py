#!/usr/bin/env python3
"""Run the isolated V8.3-2 validator-postfix benchmark.

Wave 2 reuses the approved local runtime and fixed 20-slot matrix, writes only
to Wave 2 paths, and treats every V8.3-1 result and decision artifact as
immutable. Existing Wave 2 slot Evidence is validated and skipped so an
interrupted run can resume without generating any slot twice.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import run_benchmark as bench

WAVE_ID = "V8.3-2-validator-postfix"
WAVE1_COMMIT = "cb10e1a9f81cbce5cedf354c071202f30dc72b5c"
WAVE2_EVIDENCE_ROOT = bench.BASE / "evidence" / "stage-b-wave2"
PREFLIGHT = bench.BASE / "reports" / "stage-b-wave2-preflight.json"
SUMMARY = bench.BASE / "reports" / "stage-b-wave2-execution-summary.json"
COMPARISON = bench.BASE / "reports" / "stage-b-wave2-comparison.json"

APPROVED_RUNTIME = {
    "provider": "Ollama",
    "locality": "local-only",
    "local_endpoint": "http://127.0.0.1:11434",
    "model_identifier": "qwen3.5:9b",
    "model_digest": "6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7",
    "runtime_context_limit_tokens": 16384,
    "output_limit_tokens": 1024,
    "timeout_seconds": 180,
    "retry_count": 0,
    "model_fallback_allowed": False,
}
APPROVED_GENERATION_PARAMETERS = {
    "temperature": 0,
    "top_p": 0.95,
    "top_k": 20,
    "presence_penalty": 1.5,
    "seed": 42,
    "think": False,
}

WAVE1_PROTECTED_SHA256 = {
    "evaluation/external-skills/benchmark-results.json": "21cb7165c4e02397fdafa9bc5d20f715e723ff351965cf71e00e42f6e7e80249",
    "evaluation/external-skills/adoption-decisions.json": "4078ba8597bc9483606c41dcae2a88d5096de13ce22cb6c1084665079433bbe3",
    "evaluation/external-skills/reports/stage-b-execution-summary.json": "6ff9a6a08186250768153acab19fa63501b4fee08e22fe6ff10deecb370e6e25",
    "evaluation/external-skills/reports/stage-b-failure-analysis.json": "22f590325b312ec52b9ab54e889eff7f6c23eb0c3064229d738a4dada307c692",
}
WAVE1_EVIDENCE_SET_SHA256 = "a3aa40c312ff5fa91c76d75775f6b9bf4c173da9cc4fefa9df7090e8273e9392"

POSTFIX_INPUT_SHA256 = {
    "evaluation/external-skills/benchmark-fixtures.json": "bf33aa6efa11b021ee51ac975ec3913fd4bf3f1b2b2ae2a564156d3afacdfc1c",
    "evaluation/external-skills/fixtures/stage-b-local-inputs.json": "75f137f7a241c2abfaa1fe91cc40ee67d9c0f16e7f5f616b2263c741adc9d6eb",
    "evaluation/external-skills/stage-b-acceptance-rubrics.json": "12f1772661a32d268812373eb06717422c79ccba28acc6a384c67666c48e4aa5",
    "evaluation/external-skills/adapted-contexts.json": "f972f89a57dd853eaf7f88648e8a5ce9f6a26f9335e6f03131a48222246e9816",
    "evaluation/external-skills/snapshots/manifest.json": "265a2ad0ed15d847eac43a46d6477389cba18ffd9044f983bb33c0d88c049135",
    "capability-library/registry.json": "2c2aec89ea40655d99497064c91d74b6c905bf0ce1d87bbbcdda2a071480a4a9",
    "harness/router/scoring.py": "80866867ba3997b537233b2d8134ace8504126c53a7804d03c94966a98f5bf0e",
    ".codex/AGENTS.md": "ebcd3c6627b4679101f98ce59897f528622db9f50d2cd601693f3940b968320c",
}
SNAPSHOT_SKILL_SET_SHA256 = "eb284731c29f848a29e536b7a11729c0b74984b8add07bf4f4283954b4cc58a8"


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative_path(path: Path) -> str:
    return path.relative_to(bench.REPO_ROOT).as_posix()


def evidence_set_sha256(root: Path) -> tuple[int, str]:
    digest = hashlib.sha256()
    paths = sorted(root.glob("*/*.json"))
    for path in paths:
        raw = path.read_bytes()
        digest.update(relative_path(path).encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(raw).hexdigest().encode("ascii"))
        digest.update(b"\n")
    return len(paths), digest.hexdigest()


def expected_slot_paths() -> list[Path]:
    return [
        bench.slot_evidence_path(
            candidate_id,
            variant,
            evidence_root=WAVE2_EVIDENCE_ROOT,
        )
        for candidate_id in bench.CANDIDATE_ORDER
        for variant in bench.VARIANT_ORDER
    ]


def assert_paths_are_isolated() -> None:
    wave1_root = bench.EVIDENCE_ROOT.resolve()
    wave2_root = WAVE2_EVIDENCE_ROOT.resolve()
    if wave1_root == wave2_root or wave1_root in wave2_root.parents:
        raise bench.BenchmarkError("Wave 2 Evidence path overlaps Wave 1")
    protected_reports = {
        (bench.BASE / "reports" / "stage-b-execution-summary.json").resolve(),
        (bench.BASE / "reports" / "stage-b-failure-analysis.json").resolve(),
        bench.RESULTS.resolve(),
        (bench.BASE / "adoption-decisions.json").resolve(),
    }
    if SUMMARY.resolve() in protected_reports or COMPARISON.resolve() in protected_reports:
        raise bench.BenchmarkError("Wave 2 report path overlaps a protected Wave 1 artifact")


def assert_runtime(control: dict[str, Any], model: dict[str, Any]) -> None:
    for key, expected in APPROVED_RUNTIME.items():
        if control.get(key) != expected:
            raise bench.BenchmarkError(f"Wave 2 runtime mismatch for {key}")
    if control.get("generation_parameters") != APPROVED_GENERATION_PARAMETERS:
        raise bench.BenchmarkError("Wave 2 generation parameters differ from approval")
    if control.get("candidate_order") != bench.CANDIDATE_ORDER:
        raise bench.BenchmarkError("Wave 2 candidate order differs from approval")
    if control.get("variant_order") != bench.VARIANT_ORDER:
        raise bench.BenchmarkError("Wave 2 variant order differs from approval")
    if model.get("name") != APPROVED_RUNTIME["model_identifier"]:
        raise bench.BenchmarkError("installed Wave 2 model identifier mismatch")
    if model.get("digest") != APPROVED_RUNTIME["model_digest"]:
        raise bench.BenchmarkError("installed Wave 2 model digest mismatch")
    capacity = model.get("details", {}).get("context_length")
    if capacity != 262144:
        raise bench.BenchmarkError("installed Wave 2 model context metadata mismatch")


def verify_file_hashes(expected: dict[str, str]) -> dict[str, str]:
    actual: dict[str, str] = {}
    for path_text, expected_hash in expected.items():
        path = bench.REPO_ROOT / path_text
        digest = file_sha256(path)
        if digest != expected_hash:
            raise bench.BenchmarkError(f"protected hash mismatch: {path_text}")
        actual[path_text] = digest
    return actual


def verify_wave1_protection() -> dict[str, Any]:
    protected = verify_file_hashes(WAVE1_PROTECTED_SHA256)
    evidence_count, evidence_hash = evidence_set_sha256(bench.EVIDENCE_ROOT)
    if evidence_count != 20 or evidence_hash != WAVE1_EVIDENCE_SET_SHA256:
        raise bench.BenchmarkError("Wave 1 slot Evidence set changed")
    results = bench.load_json(bench.RESULTS)
    if not bench.exact_matrix(results["stage_b"]):
        raise bench.BenchmarkError("Wave 1 matrix changed")
    if results["stage_b_acceptance_pass_count"] != 2 or results["stage_b_acceptance_fail_count"] != 18:
        raise bench.BenchmarkError("Wave 1 acceptance totals changed")
    return {
        "baseline_commit": WAVE1_COMMIT,
        "protected_sha256": protected,
        "evidence_file_count": evidence_count,
        "evidence_set_sha256": evidence_hash,
        "acceptance_pass": 2,
        "acceptance_fail": 18,
    }


def verify_postfix_inputs() -> dict[str, Any]:
    files = verify_file_hashes(POSTFIX_INPUT_SHA256)
    bench.verify_snapshots()
    snapshot_count, snapshot_hash = evidence_set_sha256_for_pattern(
        bench.BASE / "snapshots",
        "*/SKILL.md",
    )
    if snapshot_count != 15 or snapshot_hash != SNAPSHOT_SKILL_SET_SHA256:
        raise bench.BenchmarkError("pinned snapshot Skill set changed")
    return {
        "file_sha256": files,
        "snapshot_skill_count": snapshot_count,
        "snapshot_skill_set_sha256": snapshot_hash,
    }


def evidence_set_sha256_for_pattern(root: Path, pattern: str) -> tuple[int, str]:
    digest = hashlib.sha256()
    paths = sorted(root.glob(pattern))
    for path in paths:
        raw = path.read_bytes()
        digest.update(relative_path(path).encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(raw).hexdigest().encode("ascii"))
        digest.update(b"\n")
    return len(paths), digest.hexdigest()


def preflight() -> dict[str, Any]:
    assert_paths_are_isolated()
    if any(path.exists() for path in expected_slot_paths()) or SUMMARY.exists() or COMPARISON.exists():
        raise bench.BenchmarkError("Wave 2 outputs already exist; refusing a new preflight")
    control = bench.runtime_control()
    static = bench.validate_static_inputs()
    model = bench.verify_local_model(control)
    assert_runtime(control, model)
    report = {
        "schema_version": 1,
        "task_id": "V8_3-SKILL-BENCH-004",
        "wave_id": WAVE_ID,
        "status": "READY",
        "checked_at_utc": bench.utc_now(),
        "generation_started": False,
        "runtime_control": control,
        "installed_model": model,
        "matrix": {
            "candidate_order": bench.CANDIDATE_ORDER,
            "variant_order": bench.VARIANT_ORDER,
            "slot_count": 20,
        },
        "path_isolation": {
            "wave1_evidence_root": relative_path(bench.EVIDENCE_ROOT),
            "wave2_evidence_root": relative_path(WAVE2_EVIDENCE_ROOT),
            "wave2_summary": relative_path(SUMMARY),
            "wave2_comparison": relative_path(COMPARISON),
            "separated": True,
        },
        "wave1_protection": verify_wave1_protection(),
        "postfix_inputs": verify_postfix_inputs(),
        "static_matrix_valid": bench.exact_matrix(static["results"]["stage_b"]),
        "retry_count": 0,
        "fallback_allowed": False,
        "external_network_allowed": False,
        "remote_api_allowed": False,
        "credentials_allowed": False,
    }
    bench.write_json(PREFLIGHT, report)
    return report


def load_and_validate_preflight(control: dict[str, Any], model: dict[str, Any]) -> dict[str, Any]:
    if not PREFLIGHT.is_file():
        raise bench.BenchmarkError("Wave 2 preflight Evidence is missing")
    report = bench.load_json(PREFLIGHT)
    if report.get("wave_id") != WAVE_ID or report.get("status") != "READY":
        raise bench.BenchmarkError("Wave 2 preflight is not READY")
    assert_runtime(control, model)
    if report.get("runtime_control") != control:
        raise bench.BenchmarkError("Wave 2 runtime changed after preflight")
    verify_wave1_protection()
    verify_postfix_inputs()
    assert_paths_are_isolated()
    return report


def validate_slot_evidence(
    evidence: dict[str, Any],
    candidate_id: str,
    variant: str,
    control: dict[str, Any],
) -> None:
    if evidence.get("wave_id") != WAVE_ID:
        raise bench.BenchmarkError("Wave 2 Evidence has the wrong wave_id")
    if evidence.get("candidate_id") != candidate_id or evidence.get("variant") != variant:
        raise bench.BenchmarkError("Wave 2 Evidence path/content mismatch")
    if evidence.get("execution_status") not in {"COMPLETED", "FAILED"}:
        raise bench.BenchmarkError("Wave 2 Evidence has no terminal execution status")
    metadata = evidence.get("runtime_metadata", {})
    for key in ("provider", "locality", "model_identifier", "model_digest"):
        if metadata.get(key) != control.get(key):
            raise bench.BenchmarkError(f"Wave 2 slot runtime mismatch for {key}")
    if metadata.get("generation_parameters") != control["generation_parameters"]:
        raise bench.BenchmarkError("Wave 2 slot generation parameters changed")
    if metadata.get("retry_count") != 0 or metadata.get("fallback_allowed") is not False:
        raise bench.BenchmarkError("Wave 2 slot retry/fallback invariant failed")
    if evidence.get("generation_attempt") != 1:
        raise bench.BenchmarkError("Wave 2 slot generation attempt count is not one")
    for safety_key in (
        "external_access_attempted",
        "external_scripts_executed",
        "credentials_used",
        "hardware_or_cloud_write",
        "destructive_action",
    ):
        if evidence.get(safety_key) is not False:
            raise bench.BenchmarkError(f"Wave 2 safety invariant failed: {safety_key}")


def load_wave2_evidence(control: dict[str, Any]) -> list[dict[str, Any]]:
    expected = expected_slot_paths()
    actual = sorted(WAVE2_EVIDENCE_ROOT.glob("*/*.json"))
    unexpected = set(actual) - set(expected)
    if unexpected:
        raise bench.BenchmarkError(f"unexpected Wave 2 Evidence files: {unexpected}")
    records: list[dict[str, Any]] = []
    for candidate_id in bench.CANDIDATE_ORDER:
        for variant in bench.VARIANT_ORDER:
            path = bench.slot_evidence_path(
                candidate_id,
                variant,
                evidence_root=WAVE2_EVIDENCE_ROOT,
            )
            if not path.is_file():
                continue
            evidence = bench.load_json(path)
            validate_slot_evidence(evidence, candidate_id, variant, control)
            records.append(evidence)
    return records


def failed_hard_checks(acceptance: dict[str, Any]) -> list[str]:
    return [item["check"] for item in acceptance["hard_checks"] if not item["pass"]]


def evidence_metrics(records: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "slots": len(records),
        "generation_completed": sum(item["execution_status"] == "COMPLETED" for item in records),
        "generation_failed": sum(item["execution_status"] == "FAILED" for item in records),
        "acceptance_pass": sum(
            bool((item.get("acceptance") or {}).get("acceptance_pass"))
            for item in records
        ),
        "acceptance_fail": sum(
            not bool((item.get("acceptance") or {}).get("acceptance_pass"))
            for item in records
        ),
        "failed_hard_checks": sum(len(failed_hard_checks(item["acceptance"])) for item in records if item.get("acceptance")),
        "loaded_context_bytes": sum(item["context_evidence"]["loaded_context_bytes"] for item in records),
        "prompt_tokens": sum(item["token_measurement"]["prompt_token_count"] or 0 for item in records),
        "output_tokens": sum(item["token_measurement"]["output_token_count"] or 0 for item in records),
        "execution_time_ms": round(sum(item["runtime_metadata"]["wall_time_ms"] or 0 for item in records), 3),
    }


def grouped_metrics(records: list[dict[str, Any]], key: str, order: list[str]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for value in order:
        selected = [item for item in records if item[key] == value]
        result.append({key: value, **evidence_metrics(selected)})
    return result


def build_summary(records: list[dict[str, Any]], control: dict[str, Any]) -> dict[str, Any]:
    if len(records) != 20:
        raise bench.BenchmarkError("Wave 2 summary requires 20 slot Evidence files")
    starts = [item["runtime_metadata"]["execution_start_utc"] for item in records]
    ends = [item["runtime_metadata"]["execution_end_utc"] for item in records]
    protection = verify_wave1_protection()
    return {
        "schema_version": 1,
        "task_id": "V8_3-SKILL-BENCH-004",
        "wave_id": WAVE_ID,
        "status": "EXECUTION_COMPLETE",
        "runtime": {
            "provider": control["provider"],
            "locality": control["locality"],
            "model_identifier": control["model_identifier"],
            "model_digest": control["model_digest"],
            "runtime_context_limit_tokens": control["runtime_context_limit_tokens"],
            "output_limit_tokens": control["output_limit_tokens"],
            "generation_parameters": control["generation_parameters"],
            "timeout_seconds": control["timeout_seconds"],
            "retry_count": control["retry_count"],
            "fallback_used": False,
        },
        "execution_window": {
            "start_utc": min(starts),
            "end_utc": max(ends),
            "slot_wall_time_sum_ms": evidence_metrics(records)["execution_time_ms"],
        },
        "totals": evidence_metrics(records),
        "variants": grouped_metrics(records, "variant", bench.VARIANT_ORDER),
        "candidates": grouped_metrics(records, "candidate_id", bench.CANDIDATE_ORDER),
        "preflight_evidence": relative_path(PREFLIGHT),
        "evidence_root": relative_path(WAVE2_EVIDENCE_ROOT),
        "wave1_protection_after_execution": protection,
        "safety": {
            "external_access_attempted": False,
            "external_scripts_executed": False,
            "credentials_used": False,
            "hardware_or_cloud_write": False,
            "destructive_action": False,
        },
        "adoption_decisions_updated": False,
        "limitations": [
            "Each slot has one fixed-seed generation attempt; no retry, fallback, or repeated-run variance estimate is present.",
            "Wave 2 changes both validator semantics and the explicit output contract supplied to generation, so observed output changes are not validator-only effects.",
            "The read-only Wave 1 rescore diagnostic isolates validator behavior but does not replace or modify historical acceptance Evidence.",
        ],
    }


def wave1_records() -> list[dict[str, Any]]:
    results = bench.load_json(bench.RESULTS)
    records: list[dict[str, Any]] = []
    for slot in results["stage_b"]:
        records.append(
            {
                "candidate_id": slot["candidate_id"],
                "variant": slot["variant"],
                "acceptance_pass": slot["acceptance_pass"],
                "acceptance": slot["acceptance_details"],
                "loaded_context_bytes": slot["loaded_context_bytes"],
                "prompt_tokens": slot["token_count"],
                "output_tokens": slot["output_token_count"],
                "execution_time_ms": slot["execution_time_ms"],
                "evidence_path": slot["acceptance_evidence"],
            }
        )
    return records


def wave2_comparison_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "candidate_id": item["candidate_id"],
            "variant": item["variant"],
            "acceptance_pass": bool(
                (item.get("acceptance") or {}).get("acceptance_pass")
            ),
            "acceptance": item.get("acceptance")
            or {"acceptance_pass": False, "hard_checks": []},
            "execution_status": item["execution_status"],
            "failure_reason": item.get("failure_reason"),
            "loaded_context_bytes": item["context_evidence"]["loaded_context_bytes"],
            "prompt_tokens": item["token_measurement"]["prompt_token_count"],
            "output_tokens": item["token_measurement"]["output_token_count"],
            "execution_time_ms": item["runtime_metadata"]["wall_time_ms"],
            "evidence_path": relative_path(
                bench.slot_evidence_path(
                    item["candidate_id"],
                    item["variant"],
                    evidence_root=WAVE2_EVIDENCE_ROOT,
                )
            ),
        }
        for item in records
    ]


def comparison_metrics(records: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "slots": len(records),
        "acceptance_pass": sum(item["acceptance_pass"] is True for item in records),
        "acceptance_fail": sum(item["acceptance_pass"] is False for item in records),
        "failed_hard_checks": sum(len(failed_hard_checks(item["acceptance"])) for item in records),
        "loaded_context_bytes": sum(item["loaded_context_bytes"] for item in records),
        "prompt_tokens": sum(item["prompt_tokens"] or 0 for item in records),
        "output_tokens": sum(item["output_tokens"] or 0 for item in records),
        "execution_time_ms": round(sum(item["execution_time_ms"] or 0 for item in records), 3),
    }


def numeric_delta(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "acceptance_pass",
        "acceptance_fail",
        "failed_hard_checks",
        "loaded_context_bytes",
        "prompt_tokens",
        "output_tokens",
        "execution_time_ms",
    )
    return {key: round(after[key] - before[key], 3) for key in keys}


def group_comparison(
    wave1: list[dict[str, Any]],
    wave2: list[dict[str, Any]],
    key: str,
    order: list[str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for value in order:
        before = comparison_metrics([item for item in wave1 if item[key] == value])
        after = comparison_metrics([item for item in wave2 if item[key] == value])
        rows.append({key: value, "wave1": before, "wave2": after, "delta": numeric_delta(before, after)})
    return rows


def find_check(acceptance: dict[str, Any], check_name: str) -> dict[str, Any]:
    matches = [item for item in acceptance["hard_checks"] if item["check"] == check_name]
    if len(matches) != 1:
        raise bench.BenchmarkError(f"hard check is not unique: {check_name}")
    return matches[0]


def optional_check(
    acceptance: dict[str, Any] | None,
    check_name: str,
) -> dict[str, Any] | None:
    if not acceptance:
        return None
    return find_check(acceptance, check_name)


def semantic_diagnostics(wave2_map: dict[tuple[str, str], dict[str, Any]]) -> dict[str, Any]:
    checks = {
        "kd-exploratory-data-analysis": "non-causal correlation interpretation",
        "kd-scikit-learn": "final-once test usage",
    }
    rows: list[dict[str, Any]] = []
    for candidate_id, check_name in checks.items():
        for variant in bench.VARIANT_ORDER:
            old_path = bench.slot_evidence_path(candidate_id, variant)
            old_evidence = bench.load_json(old_path)
            stored_check = find_check(old_evidence["acceptance"], check_name)
            diagnostic = bench.acceptance(candidate_id, old_evidence["parsed_output"])
            diagnostic_check = find_check(diagnostic, check_name)
            wave2_check = optional_check(
                wave2_map[(candidate_id, variant)].get("acceptance"),
                check_name,
            )
            rows.append(
                {
                    "candidate_id": candidate_id,
                    "variant": variant,
                    "check": check_name,
                    "wave1_stored_pass": stored_check["pass"],
                    "wave1_postfix_validator_diagnostic_pass": diagnostic_check["pass"],
                    "wave2_observed_pass": wave2_check["pass"] if wave2_check else None,
                    "wave1_evidence": stored_check["evidence"],
                    "wave2_evidence": wave2_check["evidence"] if wave2_check else None,
                    "validator_only_false_negative_resolved": (
                        stored_check["pass"] is False and diagnostic_check["pass"] is True
                    ),
                }
            )
    return {
        "scope": "read-only diagnostic; historical Wave 1 acceptance is not modified",
        "validator_only_false_negative_resolved_count": sum(
            item["validator_only_false_negative_resolved"] for item in rows
        ),
        "rows": rows,
    }


def contract_check_transitions(
    wave1_map: dict[tuple[str, str], dict[str, Any]],
    wave2_map: dict[tuple[str, str], dict[str, Any]],
) -> list[dict[str, Any]]:
    checks = {
        "kd-sympy": "zero substitution residuals",
        "kd-citation-management": "normalized local DOI values",
        "kd-docx": "consistent heading hierarchy",
    }
    rows: list[dict[str, Any]] = []
    for candidate_id, check_name in checks.items():
        for variant in bench.VARIANT_ORDER:
            before = find_check(wave1_map[(candidate_id, variant)]["acceptance"], check_name)
            after = optional_check(
                wave2_map[(candidate_id, variant)].get("acceptance"),
                check_name,
            )
            rows.append(
                {
                    "candidate_id": candidate_id,
                    "variant": variant,
                    "check": check_name,
                    "wave1_pass": before["pass"],
                    "wave2_pass": after["pass"] if after else None,
                    "transition": (
                        f"{'PASS' if before['pass'] else 'FAIL'}->"
                        f"{'PASS' if after and after['pass'] else 'FAIL'}"
                    ),
                    "wave1_evidence": before["evidence"],
                    "wave2_evidence": after["evidence"] if after else None,
                }
            )
    return rows


def build_comparison(records: list[dict[str, Any]]) -> dict[str, Any]:
    before_records = wave1_records()
    after_records = wave2_comparison_records(records)
    before_map = {(item["candidate_id"], item["variant"]): item for item in before_records}
    after_map = {(item["candidate_id"], item["variant"]): item for item in after_records}
    evidence_map = {(item["candidate_id"], item["variant"]): item for item in records}
    before_totals = comparison_metrics(before_records)
    after_totals = comparison_metrics(after_records)
    slots: list[dict[str, Any]] = []
    for candidate_id in bench.CANDIDATE_ORDER:
        for variant in bench.VARIANT_ORDER:
            before = before_map[(candidate_id, variant)]
            after = after_map[(candidate_id, variant)]
            slots.append(
                {
                    "candidate_id": candidate_id,
                    "variant": variant,
                    "wave1_acceptance": "PASS" if before["acceptance_pass"] else "FAIL",
                    "wave2_acceptance": "PASS" if after["acceptance_pass"] else "FAIL",
                    "acceptance_transition": (
                        f"{'PASS' if before['acceptance_pass'] else 'FAIL'}->"
                        f"{'PASS' if after['acceptance_pass'] else 'FAIL'}"
                    ),
                    "wave1_failed_hard_checks": failed_hard_checks(before["acceptance"]),
                    "wave2_failed_hard_checks": failed_hard_checks(after["acceptance"]),
                    "failed_hard_check_delta": (
                        len(failed_hard_checks(after["acceptance"]))
                        - len(failed_hard_checks(before["acceptance"]))
                    ),
                    "prompt_tokens": {"wave1": before["prompt_tokens"], "wave2": after["prompt_tokens"], "delta": after["prompt_tokens"] - before["prompt_tokens"]},
                    "output_tokens": {"wave1": before["output_tokens"], "wave2": after["output_tokens"], "delta": after["output_tokens"] - before["output_tokens"]},
                    "loaded_context_bytes": {"wave1": before["loaded_context_bytes"], "wave2": after["loaded_context_bytes"], "delta": after["loaded_context_bytes"] - before["loaded_context_bytes"]},
                    "execution_time_ms": {"wave1": before["execution_time_ms"], "wave2": after["execution_time_ms"], "delta": round(after["execution_time_ms"] - before["execution_time_ms"], 3)},
                    "wave1_evidence": before["evidence_path"],
                    "wave2_evidence": after["evidence_path"],
                }
            )
    return {
        "schema_version": 1,
        "task_id": "V8_3-SKILL-BENCH-004",
        "comparison_id": "V8.3-1-vs-V8.3-2-validator-postfix",
        "generated_at_utc": bench.utc_now(),
        "purpose": "Measure validator-contract improvement without changing historical results or adoption decisions.",
        "wave1": {"wave_id": "V8.3-1", "baseline_commit": WAVE1_COMMIT, **before_totals},
        "wave2": {"wave_id": WAVE_ID, **after_totals},
        "delta": numeric_delta(before_totals, after_totals),
        "candidate_comparison": group_comparison(before_records, after_records, "candidate_id", bench.CANDIDATE_ORDER),
        "variant_comparison": group_comparison(before_records, after_records, "variant", bench.VARIANT_ORDER),
        "slot_comparison": slots,
        "semantic_false_negative_effect": semantic_diagnostics(evidence_map),
        "output_contract_effect": contract_check_transitions(before_map, evidence_map),
        "wave1_protection_after_comparison": verify_wave1_protection(),
        "adoption_decisions_updated": False,
        "interpretation_guard": "Wave 2 is a separate experiment. No Wave 1 PASS/FAIL or adoption decision is overwritten or retrospectively changed.",
    }


def finalize(control: dict[str, Any]) -> dict[str, Any]:
    records = load_wave2_evidence(control)
    if len(records) != 20:
        raise bench.BenchmarkError(f"Wave 2 finalize requires 20 slots; found {len(records)}")
    summary = build_summary(records, control)
    bench.write_json(SUMMARY, summary)
    comparison = build_comparison(records)
    bench.write_json(COMPARISON, comparison)
    verify_wave1_protection()
    return {"summary": summary["totals"], "comparison_delta": comparison["delta"]}


def execute() -> dict[str, Any]:
    if SUMMARY.exists() or COMPARISON.exists():
        raise bench.BenchmarkError("Wave 2 is already finalized; refusing execution")
    control = bench.runtime_control()
    model = bench.verify_local_model(control)
    load_and_validate_preflight(control, model)
    static = bench.validate_static_inputs()
    existing = load_wave2_evidence(control)
    completed = len(existing)
    for candidate_id in bench.CANDIDATE_ORDER:
        for variant in bench.VARIANT_ORDER:
            path = bench.slot_evidence_path(
                candidate_id,
                variant,
                evidence_root=WAVE2_EVIDENCE_ROOT,
            )
            if path.exists():
                continue
            evidence = bench.execute_slot(
                candidate_id,
                variant,
                static,
                control,
                evidence_root=WAVE2_EVIDENCE_ROOT,
                wave_id=WAVE_ID,
            )
            completed += 1
            acceptance_pass = bool(
                evidence.get("acceptance") and evidence["acceptance"]["acceptance_pass"]
            )
            print(
                f"WAVE2 SLOT {completed:02d}/20 {candidate_id} {variant} "
                f"{evidence['execution_status']} acceptance={acceptance_pass}",
                flush=True,
            )
    model = bench.verify_local_model(control)
    assert_runtime(control, model)
    return finalize(control)


def validate() -> dict[str, Any]:
    assert_paths_are_isolated()
    protection = verify_wave1_protection()
    verify_postfix_inputs()
    control = bench.runtime_control()
    records = load_wave2_evidence(control)
    if len(records) != 20:
        raise bench.BenchmarkError(f"Wave 2 is incomplete: {len(records)}/20")
    if not SUMMARY.is_file() or not COMPARISON.is_file():
        raise bench.BenchmarkError("Wave 2 summary/comparison Evidence is missing")
    summary = bench.load_json(SUMMARY)
    comparison = bench.load_json(COMPARISON)
    calculated = evidence_metrics(records)
    if summary.get("totals") != calculated:
        raise bench.BenchmarkError("Wave 2 summary totals do not match slot Evidence")
    if comparison.get("wave2", {}).get("acceptance_pass") != calculated["acceptance_pass"]:
        raise bench.BenchmarkError("Wave 2 comparison totals do not match slot Evidence")
    return {
        "status": "COMPLETE",
        "slots": len(records),
        "acceptance_pass": calculated["acceptance_pass"],
        "acceptance_fail": calculated["acceptance_fail"],
        "failed_hard_checks": calculated["failed_hard_checks"],
        "wave1_protection": protection,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--preflight", action="store_true")
    action.add_argument("--execute", action="store_true")
    action.add_argument("--finalize", action="store_true")
    action.add_argument("--validate", action="store_true")
    args = parser.parse_args()
    try:
        if args.preflight:
            result = preflight()
        elif args.execute:
            result = execute()
        elif args.finalize:
            control = bench.runtime_control()
            result = finalize(control)
        else:
            result = validate()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except bench.BenchmarkError as exc:
        print(f"WAVE2_BENCHMARK_ERROR {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
