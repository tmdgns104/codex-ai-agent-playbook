"""Deterministic offline compiler for two pinned V8.4 adapted candidates.

The compiler treats a snapshot as untrusted UTF-8 data.  It parses text, verifies
exact claims, and emits reviewable DRAFT artifacts.  It never imports or executes
source code, starts a process, contacts a service, reads credentials, invokes a
model, or connects the result to runtime activation.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any


HERE = Path(__file__).resolve().parent
CONTEXT_VALIDATOR_DIR = HERE.parent / "context-contract" / "validator"
if str(CONTEXT_VALIDATOR_DIR) not in sys.path:
    sys.path.insert(0, str(CONTEXT_VALIDATOR_DIR))

from context_contract import (  # noqa: E402
    VALIDATOR_VERSION,
    canonical_json_bytes,
    canonical_sha256,
    compute_cache_key,
    definition_content_bytes,
    definition_content_sha256,
    hash_without_field,
    load_schemas,
    strongest_permission_gate,
    utf8_sha256,
)
from schema_validation import SchemaDefinitionError, validate_instance  # noqa: E402


COMPILER_VERSION = "v8.4-offline-compiler-1"
DEFINITION_CONTRACT_ID = "v8.4-adapted-capability-definition-v1"
PROVENANCE_CONTRACT_ID = "v8.4-offline-compile-provenance-v1"
EVIDENCE_CONTRACT_ID = "v8.4-offline-compile-evidence-v1"


@dataclass(frozen=True)
class CompilerInput:
    candidate_id: str
    snapshot_path: str
    snapshot_revision: str
    snapshot_sha256: str
    license_id: str
    adaptation_policy_version: str
    extractor_version: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "snapshot_path": self.snapshot_path,
            "snapshot_revision": self.snapshot_revision,
            "snapshot_sha256": self.snapshot_sha256,
            "license_id": self.license_id,
            "adaptation_policy_version": self.adaptation_policy_version,
            "extractor_version": self.extractor_version,
        }


@dataclass(frozen=True)
class CompilerIssue:
    code: str
    path: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "path": self.path, "message": self.message}


@dataclass(frozen=True)
class CompileReport:
    status: str
    issues: tuple[CompilerIssue, ...]
    definition: dict[str, Any] | None
    provenance: dict[str, Any] | None
    evidence: dict[str, Any] | None

    @property
    def passed(self) -> bool:
        return self.status == "PASS"

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "passed": self.passed,
            "issues": [issue.as_dict() for issue in self.issues],
            "definition": self.definition,
            "provenance": self.provenance,
            "evidence": self.evidence,
        }


@dataclass(frozen=True)
class SourceSection:
    heading: str
    start_line: int
    end_line: int
    text: str

    @property
    def locator_suffix(self) -> str:
        return f"L{self.start_line}-L{self.end_line}"


@dataclass(frozen=True)
class SourceDocument:
    raw_sha256: str
    raw_bytes: int
    normalized_text: str
    sections: tuple[SourceSection, ...]


def _issue(code: str, path: str, message: str) -> CompilerIssue:
    return CompilerIssue(code=code, path=path, message=message)


def _failed(*issues: CompilerIssue, status: str = "FAIL") -> CompileReport:
    return CompileReport(status=status, issues=tuple(issues), definition=None, provenance=None, evidence=None)


def load_json_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid JSON document {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"JSON document must be an object: {path}")
    return value


def input_from_manifest(
    manifest: dict[str, Any],
    policy: dict[str, Any],
    candidate_id: str,
) -> CompilerInput:
    matches = [record for record in manifest.get("records", []) if record.get("candidate_id") == candidate_id]
    if len(matches) != 1:
        raise ValueError(f"manifest must contain exactly one record for {candidate_id}")
    record = matches[0]
    return CompilerInput(
        candidate_id=candidate_id,
        snapshot_path=record["snapshot_path"],
        snapshot_revision=record["source_revision"],
        snapshot_sha256=record["sha256"],
        license_id=record["license_status"],
        adaptation_policy_version=policy["policy_version"],
        extractor_version=policy["extractor_version"],
    )


def _validate_policy_and_rules(
    compiler_input: CompilerInput,
    policy: dict[str, Any],
    rules: dict[str, Any],
) -> list[CompilerIssue]:
    issues: list[CompilerIssue] = []
    if policy.get("definition_schema_version") != 1:
        issues.append(_issue("UNSUPPORTED_SCHEMA", "policy.definition_schema_version", "only frozen definition schema version 1 is supported"))
    if policy.get("validator_version") != VALIDATOR_VERSION:
        issues.append(_issue("UNSUPPORTED_VALIDATOR", "policy.validator_version", f"expected {VALIDATOR_VERSION}"))
    if policy.get("policy_version") != compiler_input.adaptation_policy_version:
        issues.append(_issue("POLICY_INPUT_MISMATCH", "input.adaptation_policy_version", "compiler input and policy version differ"))
    if policy.get("extractor_version") != compiler_input.extractor_version:
        issues.append(_issue("EXTRACTOR_INPUT_MISMATCH", "input.extractor_version", "compiler input and extractor version differ"))
    if rules.get("policy_version") != policy.get("policy_version") or rules.get("extractor_version") != policy.get("extractor_version"):
        issues.append(_issue("RULESET_VERSION_MISMATCH", "rules", "ruleset is not bound to the selected policy and extractor"))
    allowed = policy.get("allowed_candidates", [])
    if compiler_input.candidate_id not in allowed:
        issues.append(_issue("CANDIDATE_NOT_ALLOWED", "input.candidate_id", "candidate is outside the frozen initial compile set"))
    candidate_rules = rules.get("candidates", {}).get(compiler_input.candidate_id)
    if not isinstance(candidate_rules, dict):
        issues.append(_issue("CANDIDATE_RULES_MISSING", "rules.candidates", "candidate transform rules are missing"))
    if policy.get("definition_status") != "DRAFT" or policy.get("automatic_approval") is not False:
        issues.append(_issue("AUTOMATIC_APPROVAL_FORBIDDEN", "policy", "compiler policy must emit DRAFT and prohibit automatic approval"))
    for field in ("runtime_adaptation", "model_assisted_extraction", "source_execution_allowed", "external_access_allowed"):
        if policy.get(field) is not False:
            issues.append(_issue("OFFLINE_POLICY_VIOLATION", f"policy.{field}", f"{field} must be false"))
    categories = set(policy.get("source_categories", []))
    preserve = set(policy.get("preserve_categories", []))
    remove = set(policy.get("remove_categories", []))
    if not categories or preserve & remove or preserve | remove != categories:
        issues.append(_issue("CATEGORY_POLICY_INVALID", "policy.source_categories", "preserve/remove categories must form a complete disjoint partition"))
    for group in ("classification_patterns", "permission_signals"):
        for key, patterns in policy.get(group, {}).items():
            if group == "classification_patterns" and key not in categories:
                issues.append(_issue("UNKNOWN_SAFETY_CLASSIFICATION", f"policy.{group}.{key}", "classification is not declared"))
            for pattern in patterns:
                try:
                    re.compile(pattern)
                except re.error as exc:
                    issues.append(_issue("POLICY_PATTERN_INVALID", f"policy.{group}.{key}", str(exc)))
    for group in ("high_risk_source_patterns", "forbidden_adapted_content_patterns"):
        for index, item in enumerate(policy.get(group, [])):
            if group == "high_risk_source_patterns" and item.get("category") not in remove:
                issues.append(_issue("UNKNOWN_SAFETY_CLASSIFICATION", f"policy.{group}[{index}].category", "high-risk source signal must map to a removal category"))
            try:
                re.compile(item.get("pattern", ""))
            except re.error as exc:
                issues.append(_issue("POLICY_PATTERN_INVALID", f"policy.{group}[{index}].pattern", str(exc)))
    return issues


def _manifest_record(manifest: dict[str, Any], candidate_id: str) -> tuple[dict[str, Any] | None, list[CompilerIssue]]:
    matches = [record for record in manifest.get("records", []) if record.get("candidate_id") == candidate_id]
    if len(matches) != 1:
        return None, [_issue("MANIFEST_RECORD_INVALID", "manifest.records", "candidate must have exactly one pinned manifest record")]
    return matches[0], []


def _validate_manifest_input(
    compiler_input: CompilerInput,
    manifest_record: dict[str, Any],
) -> list[CompilerIssue]:
    expected = {
        "snapshot_path": manifest_record.get("snapshot_path"),
        "snapshot_revision": manifest_record.get("source_revision"),
        "snapshot_sha256": manifest_record.get("sha256"),
        "license_id": manifest_record.get("license_status"),
    }
    actual = compiler_input.as_dict()
    issues: list[CompilerIssue] = []
    for field, value in expected.items():
        if actual.get(field) != value:
            code = "SOURCE_HASH_MISMATCH" if field == "snapshot_sha256" else "SOURCE_MANIFEST_MISMATCH"
            issues.append(_issue(code, f"input.{field}", f"expected pinned manifest value {value!r}"))
    if manifest_record.get("fetch_status") != "FETCHED" or manifest_record.get("external_scripts_executed") is not False:
        issues.append(_issue("SOURCE_MANIFEST_UNSAFE", "manifest.record", "source must be fetched and have zero external script executions"))
    if manifest_record.get("content_encoding") != "utf-8":
        issues.append(_issue("SOURCE_ENCODING_UNSUPPORTED", "manifest.record.content_encoding", "only UTF-8 snapshots are supported"))
    return issues


def _safe_snapshot_path(repo_root: Path, compiler_input: CompilerInput) -> tuple[Path | None, list[CompilerIssue]]:
    relative_text = compiler_input.snapshot_path
    if "\\" in relative_text or re.match(r"^[A-Za-z]:", relative_text):
        return None, [_issue("SOURCE_PATH_INVALID", "input.snapshot_path", "snapshot path must use portable relative POSIX syntax")]
    pure = PurePosixPath(relative_text)
    expected_prefix = ("evaluation", "external-skills", "snapshots", compiler_input.candidate_id)
    if pure.is_absolute() or ".." in pure.parts or "." in pure.parts or tuple(pure.parts[:4]) != expected_prefix:
        return None, [_issue("SOURCE_PATH_INVALID", "input.snapshot_path", "snapshot must stay in its pinned candidate directory")]
    if pure.name != "SKILL.md":
        return None, [_issue("SOURCE_PATH_INVALID", "input.snapshot_path", "compiler accepts only the pinned SKILL.md")]
    root = repo_root.resolve(strict=True)
    if repo_root.is_symlink():
        return None, [_issue("SOURCE_SYMLINK_BLOCKED", "repo_root", "repository root must not be a symlink")]
    candidate = repo_root.joinpath(*pure.parts)
    current = repo_root
    for part in pure.parts:
        current = current / part
        if current.is_symlink():
            return None, [_issue("SOURCE_SYMLINK_BLOCKED", "input.snapshot_path", f"symlink component blocked: {part}")]
    try:
        candidate.resolve(strict=False).relative_to(root)
    except ValueError:
        return None, [_issue("SOURCE_PATH_INVALID", "input.snapshot_path", "resolved snapshot escapes repository root")]
    if not candidate.is_file():
        return None, [_issue("SOURCE_MISSING", "input.snapshot_path", "pinned snapshot file is missing")]
    return candidate, []


def _normalize_text(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return "\n".join(line.rstrip() for line in normalized.split("\n")).strip()


def _parse_source(raw: bytes) -> tuple[SourceDocument | None, list[CompilerIssue]]:
    try:
        decoded = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        return None, [_issue("MALFORMED_SOURCE", "source", f"source is not valid UTF-8: {exc}")]
    normalized = _normalize_text(decoded)
    if "\x00" in normalized or not normalized.startswith("---\n"):
        return None, [_issue("MALFORMED_SOURCE", "source", "source must begin with a non-binary YAML frontmatter block")]
    lines = normalized.split("\n")
    try:
        frontmatter_end = lines[1:].index("---") + 1
    except ValueError:
        return None, [_issue("MALFORMED_SOURCE", "source", "frontmatter closing delimiter is missing")]
    heading_indexes = [index for index, line in enumerate(lines) if re.match(r"^#{1,6}\s+\S", line)]
    if not heading_indexes or not any(lines[index].startswith("# ") for index in heading_indexes):
        return None, [_issue("MALFORMED_SOURCE", "source", "source must contain a Markdown level-one title")]

    sections: list[SourceSection] = []
    frontmatter_text = "\n".join(lines[: frontmatter_end + 1])
    sections.append(SourceSection("FRONTMATTER", 1, frontmatter_end + 1, frontmatter_text))
    for position, start in enumerate(heading_indexes):
        end = heading_indexes[position + 1] - 1 if position + 1 < len(heading_indexes) else len(lines) - 1
        section_text = "\n".join(lines[start : end + 1]).strip()
        heading = re.sub(r"^#{1,6}\s+", "", lines[start]).strip()
        sections.append(SourceSection(heading, start + 1, end + 1, section_text))
    return SourceDocument(
        raw_sha256=hashlib.sha256(raw).hexdigest(),
        raw_bytes=len(raw),
        normalized_text=normalized,
        sections=tuple(sections),
    ), []


def _source_locator(snapshot_path: str, start_line: int, end_line: int) -> str:
    return f"{snapshot_path}#L{start_line}-L{end_line}"


def _inspect_source(
    compiler_input: CompilerInput,
    source: SourceDocument,
    policy: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]], list[CompilerIssue]]:
    categories = {name: [] for name in policy["source_categories"]}
    removals: list[dict[str, Any]] = []
    preserve = set(policy["preserve_categories"])
    remove = set(policy["remove_categories"])

    for section in source.sections:
        matched = [
            category
            for category, patterns in policy["classification_patterns"].items()
            if any(re.search(pattern, section.text) for pattern in patterns)
        ]
        if not matched:
            matched = ["unrelated_explanatory_content"]
        locator = _source_locator(compiler_input.snapshot_path, section.start_line, section.end_line)
        for category in sorted(matched):
            record = {
                "heading": section.heading,
                "source_locator": locator,
                "source_claim_sha256": utf8_sha256(section.text),
                "source_utf8_bytes": len(section.text.encode("utf-8")),
            }
            categories[category].append(record)
            if category in remove:
                removals.append(
                    {
                        "category": category,
                        "source_locator": locator,
                        "source_claim_sha256": record["source_claim_sha256"],
                        "reason": f"Policy removes raw {category} material from runtime adapted unit content.",
                    }
                )

    high_risk_signals: list[dict[str, Any]] = []
    issues: list[CompilerIssue] = []
    for signal in policy["high_risk_source_patterns"]:
        category = signal["category"]
        if category not in remove:
            issues.append(_issue("UNKNOWN_SAFETY_CLASSIFICATION", "policy.high_risk_source_patterns", f"signal {signal['rule_id']} has no fail-closed removal class"))
            continue
        for match in re.finditer(signal["pattern"], source.normalized_text):
            start_line = source.normalized_text.count("\n", 0, match.start()) + 1
            end_line = start_line + match.group(0).count("\n")
            high_risk_signals.append(
                {
                    "rule_id": signal["rule_id"],
                    "category": category,
                    "source_locator": _source_locator(compiler_input.snapshot_path, start_line, end_line),
                    "matched_text": match.group(0),
                    "matched_text_sha256": utf8_sha256(match.group(0)),
                    "disposition": "REMOVED_FROM_ADAPTED_CONTENT",
                }
            )

    inspection = {
        "trust": "UNTRUSTED_SOURCE_DATA",
        "parser": "deterministic-markdown-lines-v1",
        "section_count": len(source.sections),
        "categories": categories,
        "high_risk_signals": high_risk_signals,
        "category_partition": {
            "preserve": sorted(preserve),
            "remove": sorted(remove),
        },
    }
    return inspection, removals, issues


def _derive_source_permissions(source: SourceDocument, policy: dict[str, Any]) -> list[str]:
    derived = [
        permission
        for permission, patterns in policy["permission_signals"].items()
        if any(re.search(pattern, source.normalized_text) for pattern in patterns)
    ]
    return sorted(set(derived))


def _validate_rule_order(candidate_rules: dict[str, Any]) -> list[CompilerIssue]:
    units = candidate_rules.get("units")
    if not isinstance(units, list) or not units:
        return [_issue("KNOWLEDGE_RULES_MISSING", "rules.units", "at least one knowledge rule is required")]
    issues: list[CompilerIssue] = []
    rule_ids = [unit.get("rule_id") for unit in units]
    priorities = [unit.get("priority") for unit in units]
    if any(not isinstance(rule_id, str) or not rule_id for rule_id in rule_ids):
        issues.append(_issue("KNOWLEDGE_RULE_ID_INVALID", "rules.units", "each rule needs a non-empty rule_id"))
    if len(rule_ids) != len(set(rule_ids)):
        issues.append(_issue("DUPLICATE_KNOWLEDGE_RULE", "rules.units", "knowledge rule IDs must be unique"))
    if any(not isinstance(priority, int) or isinstance(priority, bool) for priority in priorities):
        issues.append(_issue("RULE_ORDER_UNSTABLE", "rules.units", "every priority must be an integer"))
    elif priorities != sorted(priorities) or len(priorities) != len(set(priorities)):
        issues.append(_issue("RULE_ORDER_UNSTABLE", "rules.units", "rules must have unique strictly increasing priorities"))
    return issues


def _locate_exact_claim(
    compiler_input: CompilerInput,
    source_text: str,
    claim: str,
    rule_index: int,
) -> tuple[dict[str, Any] | None, list[CompilerIssue]]:
    normalized_claim = _normalize_text(claim) if isinstance(claim, str) else ""
    if not normalized_claim:
        return None, [_issue("SOURCE_CLAIM_MISSING", f"rules.units[{rule_index}].source_claim", "source claim is required")]
    occurrences = source_text.count(normalized_claim)
    if occurrences == 0:
        return None, [_issue("SOURCE_CLAIM_NOT_FOUND", f"rules.units[{rule_index}].source_claim", "exact normalized source claim was not found")]
    if occurrences != 1:
        return None, [_issue("AMBIGUOUS_PROVENANCE", f"rules.units[{rule_index}].source_claim", f"source claim occurs {occurrences} times")]
    offset = source_text.index(normalized_claim)
    start_line = source_text.count("\n", 0, offset) + 1
    end_line = start_line + normalized_claim.count("\n")
    return {
        "source_locator": _source_locator(compiler_input.snapshot_path, start_line, end_line),
        "source_claim": normalized_claim,
        "source_claim_sha256": utf8_sha256(normalized_claim),
    }, []


def _unit_id(
    compiler_input: CompilerInput,
    rule_id: str,
    source_claim_sha256: str,
) -> str:
    identity = {
        "candidate_id": compiler_input.candidate_id,
        "rule_id": rule_id,
        "source_claim_sha256": source_claim_sha256,
        "policy_version": compiler_input.adaptation_policy_version,
        "extractor_version": compiler_input.extractor_version,
    }
    return f"{compiler_input.candidate_id}.{rule_id}.{canonical_sha256(identity)[:16]}"


def _forbidden_matches(content: str, policy: dict[str, Any]) -> list[str]:
    return [
        item["rule_id"]
        for item in policy["forbidden_adapted_content_patterns"]
        if re.search(item["pattern"], content)
    ]


def _build_units(
    compiler_input: CompilerInput,
    source: SourceDocument,
    candidate_rules: dict[str, Any],
    policy: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[CompilerIssue]]:
    order_issues = _validate_rule_order(candidate_rules)
    if order_issues:
        return [], [], order_issues
    units: list[dict[str, Any]] = []
    provenance: list[dict[str, Any]] = []
    issues: list[CompilerIssue] = []
    compiled_rule_ids: set[str] = set()

    for index, rule in enumerate(candidate_rules["units"]):
        located, claim_issues = _locate_exact_claim(
            compiler_input,
            source.normalized_text,
            rule.get("source_claim"),
            index,
        )
        if claim_issues:
            issues.extend(claim_issues)
            continue
        assert located is not None
        content = _normalize_text(rule.get("content", ""))
        forbidden = _forbidden_matches(content, policy)
        if forbidden:
            issues.append(_issue("FORBIDDEN_ADAPTED_INSTRUCTION", f"rules.units[{index}].content", f"matched forbidden rule(s): {forbidden}"))
        safety_constraints = rule.get("safety_constraints")
        if not isinstance(safety_constraints, list) or not safety_constraints or any(not str(value).strip() for value in safety_constraints):
            issues.append(_issue("REQUIRED_SAFETY_MISSING", f"rules.units[{index}].safety_constraints", "every unit requires an explicit safety constraint"))
            continue
        if not content:
            issues.append(_issue("KNOWLEDGE_CONTENT_MISSING", f"rules.units[{index}].content", "adapted unit content is required"))
            continue
        rule_id = rule["rule_id"]
        compiled_rule_ids.add(rule_id)
        unit: dict[str, Any] = {
            "unit_id": _unit_id(compiler_input, rule_id, located["source_claim_sha256"]),
            "kind": rule.get("kind"),
            "priority": rule.get("priority"),
            "required": rule.get("required"),
            "task_tags": copy.deepcopy(rule.get("task_tags", [])),
            "prerequisites": copy.deepcopy(rule.get("prerequisites", [])),
            "content": content,
            "source_locator": located["source_locator"],
            "source_claim_sha256": located["source_claim_sha256"],
            "verification_requirements": copy.deepcopy(rule.get("verification_requirements", [])),
            "failure_modes": copy.deepcopy(rule.get("failure_modes", [])),
            "safety_constraints": copy.deepcopy(safety_constraints),
        }
        unit["content_sha256"] = canonical_sha256(unit)
        units.append(unit)
        provenance.append(
            {
                "unit_id": unit["unit_id"],
                "rule_id": rule_id,
                "source_locator": located["source_locator"],
                "source_claim": located["source_claim"],
                "source_claim_sha256": located["source_claim_sha256"],
                "adapted_content_sha256": utf8_sha256(content),
                "unit_content_sha256": unit["content_sha256"],
                "transformation": "EXACT_CLAIM_TO_REVIEWED_NORMALIZED_UNIT",
            }
        )

    required_rule_ids = set(candidate_rules.get("required_rule_ids", []))
    missing_required = sorted(required_rule_ids - compiled_rule_ids)
    required_flags = {
        rule.get("rule_id"): rule.get("required")
        for rule in candidate_rules.get("units", [])
        if rule.get("rule_id") in required_rule_ids
    }
    false_required = sorted(rule_id for rule_id, required in required_flags.items() if required is not True)
    if missing_required or false_required:
        issues.append(
            _issue(
                "REQUIRED_KNOWLEDGE_MISSING",
                "rules.required_rule_ids",
                f"missing={missing_required}, not_marked_required={false_required}",
            )
        )
    return units, provenance, issues


def _permission_record(
    compiler_input: CompilerInput,
    source_permissions: list[str],
    candidate_rules: dict[str, Any],
    policy: dict[str, Any],
) -> tuple[dict[str, Any] | None, list[CompilerIssue]]:
    retained = sorted(set(candidate_rules.get("retained_permissions", [])))
    source_set = set(source_permissions)
    retained_set = set(retained)
    if not retained_set.issubset(source_set):
        return None, [_issue("PERMISSION_INCONSISTENCY", "rules.retained_permissions", "retained permission is absent from source permissions")]
    removed = sorted(source_set - retained_set)
    try:
        _, gate = strongest_permission_gate(source_permissions + retained)
    except ValueError as exc:
        return None, [_issue("PERMISSION_INCONSISTENCY", "permissions", str(exc))]
    return {
        "source_permissions": sorted(source_set),
        "retained_permissions": retained,
        "removed_permissions": removed,
        "removal_justification": "Operational source permissions are recorded conservatively; the DRAFT contains reference knowledge only and does not authorize removed operations.",
        "forbidden_actions": copy.deepcopy(policy["forbidden_actions"]),
        "effective_gate": gate,
        "permission_policy_version": policy["permission_policy_version"],
    }, []


def _definition_evidence_paths(candidate_id: str) -> tuple[str, str, str]:
    base = f"evaluation/external-skills/adapted-contexts/{candidate_id}"
    return (
        f"{base}/provenance.json",
        f"{base}/compile-evidence.json#compiler-fixtures",
        f"{base}/compile-evidence.json#human-holdout-pending",
    )


def _build_definition(
    compiler_input: CompilerInput,
    candidate_rules: dict[str, Any],
    policy: dict[str, Any],
    permissions: dict[str, Any],
    units: list[dict[str, Any]],
) -> dict[str, Any]:
    provenance_path, fixture_evidence, holdout_evidence = _definition_evidence_paths(compiler_input.candidate_id)
    definition: dict[str, Any] = {
        "schema_version": 1,
        "contract_id": DEFINITION_CONTRACT_ID,
        "adapted_capability_id": candidate_rules["adapted_capability_id"],
        "version": candidate_rules["definition_version"],
        "status": policy["definition_status"],
        "candidate_id": compiler_input.candidate_id,
        "applicability": copy.deepcopy(candidate_rules["applicability"]),
        "source": {
            "snapshot_path": compiler_input.snapshot_path,
            "snapshot_revision": compiler_input.snapshot_revision,
            "snapshot_sha256": compiler_input.snapshot_sha256,
            "license_id": compiler_input.license_id,
            "inspection_evidence": [
                "evaluation/external-skills/inspections.json",
                provenance_path,
            ],
        },
        "transformation": {
            "policy_version": compiler_input.adaptation_policy_version,
            "method": "DETERMINISTIC_EXTRACTION",
            "tool_or_model_id_or_null": None,
            "reviewer": candidate_rules["reviewer"],
            "created_at_utc": policy["definition_created_at_utc"],
            "extractor_version": compiler_input.extractor_version,
        },
        "permissions": copy.deepcopy(permissions),
        "knowledge_units": copy.deepcopy(units),
        "budget": {
            "utf8_bytes": 0,
            "tokenizer_id_or_null": policy["token_policy"]["tokenizer_id_or_null"],
            "token_count_or_null": policy["token_policy"]["token_count_or_null"],
            "unavailable_reason_or_null": policy["token_policy"]["unavailable_reason_or_null"],
        },
        "verification": {
            "schema_pass": "PASS",
            "provenance_pass": "PASS",
            "safety_pass": "PASS",
            "fixture_pass": "UNKNOWN",
            "holdout_pass": "UNKNOWN",
            "fixture_evidence": [fixture_evidence],
            "holdout_evidence": [holdout_evidence],
        },
        "content_sha256": "0" * 64,
        "cache_key": "0" * 64,
    }
    definition["budget"]["utf8_bytes"] = definition_content_bytes(definition)
    definition["content_sha256"] = definition_content_sha256(definition)
    definition["cache_key"] = compute_cache_key(definition)
    return definition


def _build_provenance(
    compiler_input: CompilerInput,
    source: SourceDocument,
    inspection: dict[str, Any],
    removals: list[dict[str, Any]],
    permission_record: dict[str, Any],
    unit_provenance: list[dict[str, Any]],
    definition: dict[str, Any],
    policy: dict[str, Any],
) -> dict[str, Any]:
    provenance: dict[str, Any] = {
        "schema_version": 1,
        "contract_id": PROVENANCE_CONTRACT_ID,
        "compiler_version": COMPILER_VERSION,
        "candidate_id": compiler_input.candidate_id,
        "compiler_input": compiler_input.as_dict(),
        "source": {
            "raw_sha256": source.raw_sha256,
            "raw_utf8_bytes": source.raw_bytes,
            "normalized_text_sha256": utf8_sha256(source.normalized_text),
            "trust": "UNTRUSTED_SOURCE_DATA",
        },
        "inspection": inspection,
        "unit_provenance": unit_provenance,
        "removal_records": sorted(
            removals,
            key=lambda record: (record["source_locator"], record["category"], record["source_claim_sha256"]),
        ),
        "permission_derivation": {
            "source_permissions": permission_record["source_permissions"],
            "retained_permissions": permission_record["retained_permissions"],
            "removed_permissions": permission_record["removed_permissions"],
            "strongest_gate": permission_record["effective_gate"],
            "permission_policy_version": policy["permission_policy_version"],
        },
        "definition": {
            "status": definition["status"],
            "content_sha256": definition["content_sha256"],
            "cache_key": definition["cache_key"],
            "canonical_sha256": canonical_sha256(definition),
        },
        "approval": {
            "state": policy["review_state"],
            "automatic_approval": False,
            "human_review_required": True,
        },
        "side_effects": {
            "source_instruction_executed": False,
            "source_script_executed": False,
            "external_access": False,
            "credentials": False,
            "llm_or_ollama": False,
            "runtime_activation": False,
        },
        "provenance_sha256": "0" * 64,
    }
    provenance["provenance_sha256"] = hash_without_field(provenance, "provenance_sha256")
    return provenance


def _expected_locator(source_text: str, snapshot_path: str, claim: str) -> str | None:
    if source_text.count(claim) != 1:
        return None
    offset = source_text.index(claim)
    start_line = source_text.count("\n", 0, offset) + 1
    return _source_locator(snapshot_path, start_line, start_line + claim.count("\n"))


def verify_compiled_artifacts(
    *,
    compiler_input: CompilerInput,
    source: SourceDocument,
    definition: dict[str, Any],
    provenance: dict[str, Any],
    policy: dict[str, Any],
    candidate_rules: dict[str, Any],
    schema_root: Path | None = None,
) -> tuple[list[CompilerIssue], dict[str, str]]:
    issues: list[CompilerIssue] = []
    checks = {
        "schema_validation": "PASS",
        "source_hash_verification": "PASS",
        "content_hash_verification": "PASS",
        "provenance_completeness": "PASS",
        "permission_consistency": "PASS",
        "forbidden_instruction_exclusion": "PASS",
        "required_knowledge_preservation": "PASS",
        "budget_metadata_consistency": "PASS",
        "cache_freshness": "PASS",
        "approval_boundary": "PASS",
    }

    try:
        schema = load_schemas(schema_root)["definition"]
    except SchemaDefinitionError as exc:
        issues.append(_issue("UNSUPPORTED_SCHEMA", "schema", str(exc)))
        checks["schema_validation"] = "FAIL"
    else:
        schema_errors = validate_instance(definition, schema)
        if schema_errors:
            checks["schema_validation"] = "FAIL"
            issues.extend(_issue("SCHEMA_INVALID", f"definition:{error.path}", error.message) for error in schema_errors)

    if source.raw_sha256 != compiler_input.snapshot_sha256 or definition.get("source", {}).get("snapshot_sha256") != source.raw_sha256:
        checks["source_hash_verification"] = "FAIL"
        issues.append(_issue("SOURCE_HASH_MISMATCH", "definition.source.snapshot_sha256", "definition is not bound to exact source bytes"))
    source_fields = {
        "snapshot_path": compiler_input.snapshot_path,
        "snapshot_revision": compiler_input.snapshot_revision,
        "license_id": compiler_input.license_id,
    }
    for field, expected in source_fields.items():
        if definition.get("source", {}).get(field) != expected:
            checks["source_hash_verification"] = "FAIL"
            issues.append(_issue("SOURCE_BINDING_MISMATCH", f"definition.source.{field}", f"expected {expected!r}"))

    unit_ids: list[str] = []
    for index, unit in enumerate(definition.get("knowledge_units", [])):
        unit_ids.append(unit.get("unit_id"))
        expected_hash = canonical_sha256({key: value for key, value in unit.items() if key != "content_sha256"})
        if unit.get("content_sha256") != expected_hash:
            checks["content_hash_verification"] = "FAIL"
            issues.append(_issue("UNIT_HASH_MISMATCH", f"definition.knowledge_units[{index}].content_sha256", "unit hash mismatch"))
        if not unit.get("safety_constraints") or any(not str(value).strip() for value in unit.get("safety_constraints", [])):
            checks["required_knowledge_preservation"] = "FAIL"
            issues.append(_issue("REQUIRED_SAFETY_MISSING", f"definition.knowledge_units[{index}].safety_constraints", "unit safety constraint is missing"))
        forbidden = _forbidden_matches(str(unit.get("content", "")), policy)
        if forbidden:
            checks["forbidden_instruction_exclusion"] = "FAIL"
            issues.append(_issue("FORBIDDEN_ADAPTED_INSTRUCTION", f"definition.knowledge_units[{index}].content", f"matched forbidden rule(s): {forbidden}"))
    if len(unit_ids) != len(set(unit_ids)):
        checks["content_hash_verification"] = "FAIL"
        issues.append(_issue("DUPLICATE_UNIT_ID", "definition.knowledge_units", "unit IDs must be unique"))
    if definition.get("content_sha256") != definition_content_sha256(definition):
        checks["content_hash_verification"] = "FAIL"
        issues.append(_issue("DEFINITION_CONTENT_HASH_MISMATCH", "definition.content_sha256", "definition content hash mismatch"))

    expected_bytes = definition_content_bytes(definition)
    if definition.get("budget", {}).get("utf8_bytes") != expected_bytes:
        checks["budget_metadata_consistency"] = "FAIL"
        issues.append(_issue("BUDGET_METADATA_INCONSISTENT", "definition.budget.utf8_bytes", f"expected {expected_bytes}"))
    token = definition.get("budget", {})
    if token.get("token_count_or_null") is None:
        if token.get("tokenizer_id_or_null") is not None or not str(token.get("unavailable_reason_or_null") or "").strip():
            checks["budget_metadata_consistency"] = "FAIL"
            issues.append(_issue("BUDGET_METADATA_INCONSISTENT", "definition.budget", "null token count requires null tokenizer and a reason"))
    if definition.get("cache_key") != compute_cache_key(definition):
        checks["cache_freshness"] = "FAIL"
        issues.append(_issue("STALE_CACHE", "definition.cache_key", "cache key does not match frozen inputs"))

    unit_provenance = provenance.get("unit_provenance", [])
    by_unit = {record.get("unit_id"): record for record in unit_provenance}
    if len(by_unit) != len(unit_provenance) or set(by_unit) != set(unit_ids):
        checks["provenance_completeness"] = "FAIL"
        issues.append(_issue("PROVENANCE_INCOMPLETE", "provenance.unit_provenance", "unit/provenance IDs are not one-to-one"))
    for index, unit in enumerate(definition.get("knowledge_units", [])):
        record = by_unit.get(unit.get("unit_id"), {})
        claim = record.get("source_claim")
        locator = record.get("source_locator")
        expected_locator = _expected_locator(source.normalized_text, compiler_input.snapshot_path, claim) if isinstance(claim, str) else None
        if (
            not locator
            or unit.get("source_locator") != locator
            or expected_locator != locator
            or record.get("source_claim_sha256") != unit.get("source_claim_sha256")
            or (isinstance(claim, str) and utf8_sha256(claim) != unit.get("source_claim_sha256"))
            or record.get("unit_content_sha256") != unit.get("content_sha256")
        ):
            checks["provenance_completeness"] = "FAIL"
            issues.append(_issue("PROVENANCE_INCOMPLETE", f"definition.knowledge_units[{index}]", "locator, claim, or unit provenance is incomplete or ambiguous"))
    if provenance.get("source", {}).get("raw_sha256") != source.raw_sha256:
        checks["provenance_completeness"] = "FAIL"
        issues.append(_issue("PROVENANCE_INCOMPLETE", "provenance.source.raw_sha256", "provenance source hash mismatch"))
    if provenance.get("provenance_sha256") != hash_without_field(provenance, "provenance_sha256"):
        checks["provenance_completeness"] = "FAIL"
        issues.append(_issue("PROVENANCE_HASH_MISMATCH", "provenance.provenance_sha256", "provenance self-hash mismatch"))

    source_permissions = _derive_source_permissions(source, policy)
    reported = definition.get("permissions", {})
    retained = set(reported.get("retained_permissions", []))
    removed = set(reported.get("removed_permissions", []))
    source_set = set(source_permissions)
    try:
        _, strongest_gate = strongest_permission_gate(source_permissions + list(retained))
    except ValueError as exc:
        strongest_gate = None
        issues.append(_issue("PERMISSION_INCONSISTENCY", "definition.permissions", str(exc)))
    if (
        reported.get("source_permissions") != sorted(source_set)
        or retained & removed
        or retained | removed != source_set
        or not retained.issubset(source_set)
        or reported.get("effective_gate") != strongest_gate
        or reported.get("permission_policy_version") != policy.get("permission_policy_version")
    ):
        checks["permission_consistency"] = "FAIL"
        issues.append(_issue("PERMISSION_INCONSISTENCY", "definition.permissions", "source/retained/removed partition or strongest gate is inconsistent"))

    required_rule_ids = set(candidate_rules.get("required_rule_ids", []))
    present_required = {
        record.get("rule_id")
        for record in unit_provenance
        if record.get("unit_id") in unit_ids
        if definition.get("knowledge_units", [])[unit_ids.index(record.get("unit_id"))].get("required")
    }
    missing_required = sorted(required_rule_ids - present_required)
    if missing_required:
        checks["required_knowledge_preservation"] = "FAIL"
        issues.append(_issue("REQUIRED_KNOWLEDGE_MISSING", "definition.knowledge_units", f"missing required rules: {missing_required}"))

    if definition.get("status") != "DRAFT" or provenance.get("approval", {}).get("state") != "APPROVAL_PENDING" or provenance.get("approval", {}).get("automatic_approval") is not False:
        checks["approval_boundary"] = "FAIL"
        issues.append(_issue("AUTOMATIC_APPROVAL_FORBIDDEN", "definition.status", "compiler output must remain DRAFT with separate APPROVAL_PENDING evidence"))
    return issues, checks


def verification_terminal_status(issues: list[CompilerIssue]) -> str:
    if not issues:
        return "PASS"
    if {issue.code for issue in issues} == {"STALE_CACHE"}:
        return "INVALIDATED"
    return "FAIL"


def _compile_once(
    *,
    repo_root: Path,
    compiler_input: CompilerInput,
    manifest: dict[str, Any],
    policy: dict[str, Any],
    rules: dict[str, Any],
    schema_root: Path | None,
) -> CompileReport:
    issues = _validate_policy_and_rules(compiler_input, policy, rules)
    manifest_record, manifest_issues = _manifest_record(manifest, compiler_input.candidate_id)
    issues.extend(manifest_issues)
    if manifest_record is not None:
        issues.extend(_validate_manifest_input(compiler_input, manifest_record))
    if issues:
        return _failed(*issues)

    source_path, path_issues = _safe_snapshot_path(repo_root, compiler_input)
    if path_issues:
        return _failed(*path_issues)
    assert source_path is not None and manifest_record is not None
    raw = source_path.read_bytes()
    actual_hash = hashlib.sha256(raw).hexdigest()
    if actual_hash != compiler_input.snapshot_sha256 or actual_hash != manifest_record.get("sha256"):
        return _failed(_issue("SOURCE_HASH_MISMATCH", "source", f"expected {compiler_input.snapshot_sha256}, got {actual_hash}"))
    if manifest_record.get("byte_size") != len(raw):
        return _failed(_issue("SOURCE_SIZE_MISMATCH", "manifest.record.byte_size", f"expected {manifest_record.get('byte_size')}, got {len(raw)}"))

    source, parse_issues = _parse_source(raw)
    if parse_issues:
        return _failed(*parse_issues)
    assert source is not None
    inspection, removals, inspection_issues = _inspect_source(compiler_input, source, policy)
    if inspection_issues:
        return _failed(*inspection_issues)

    candidate_rules = rules["candidates"][compiler_input.candidate_id]
    units, unit_provenance, unit_issues = _build_units(
        compiler_input,
        source,
        candidate_rules,
        policy,
    )
    if unit_issues:
        return _failed(*unit_issues)

    source_permissions = _derive_source_permissions(source, policy)
    permission_record, permission_issues = _permission_record(
        compiler_input,
        source_permissions,
        candidate_rules,
        policy,
    )
    if permission_issues:
        return _failed(*permission_issues)
    assert permission_record is not None

    definition = _build_definition(compiler_input, candidate_rules, policy, permission_record, units)
    provenance = _build_provenance(
        compiler_input,
        source,
        inspection,
        removals,
        permission_record,
        unit_provenance,
        definition,
        policy,
    )
    verification_issues, checks = verify_compiled_artifacts(
        compiler_input=compiler_input,
        source=source,
        definition=definition,
        provenance=provenance,
        policy=policy,
        candidate_rules=candidate_rules,
        schema_root=schema_root,
    )
    if verification_issues:
        return _failed(*verification_issues, status=verification_terminal_status(verification_issues))

    evidence: dict[str, Any] = {
        "schema_version": 1,
        "contract_id": EVIDENCE_CONTRACT_ID,
        "compiler_version": COMPILER_VERSION,
        "candidate_id": compiler_input.candidate_id,
        "compile_status": "PASS",
        "definition_status": "DRAFT",
        "review_state": "APPROVAL_PENDING",
        "automatic_approval": False,
        "knowledge_unit_count": len(units),
        "required_knowledge_unit_count": sum(1 for unit in units if unit["required"]),
        "source_sha256": source.raw_sha256,
        "definition_canonical_sha256": canonical_sha256(definition),
        "definition_content_sha256": definition["content_sha256"],
        "provenance_sha256": provenance["provenance_sha256"],
        "cache_key": definition["cache_key"],
        "checks": checks,
        "deterministic_rebuild": "PENDING_SECOND_BUILD",
        "side_effects": copy.deepcopy(provenance["side_effects"]),
        "evidence_sha256": "0" * 64,
    }
    evidence["evidence_sha256"] = hash_without_field(evidence, "evidence_sha256")
    return CompileReport("PASS", (), definition, provenance, evidence)


def compile_candidate(
    *,
    repo_root: Path,
    compiler_input: CompilerInput,
    manifest: dict[str, Any],
    policy: dict[str, Any],
    rules: dict[str, Any],
    schema_root: Path | None = None,
) -> CompileReport:
    """Compile twice and return only an identical, fully verified DRAFT."""
    first = _compile_once(
        repo_root=repo_root,
        compiler_input=compiler_input,
        manifest=manifest,
        policy=policy,
        rules=rules,
        schema_root=schema_root,
    )
    if not first.passed:
        return first
    second = _compile_once(
        repo_root=repo_root,
        compiler_input=compiler_input,
        manifest=manifest,
        policy=copy.deepcopy(policy),
        rules=copy.deepcopy(rules),
        schema_root=schema_root,
    )
    if not second.passed:
        return _failed(_issue("NON_DETERMINISTIC_OUTPUT", "$", "second deterministic build failed"))
    assert first.definition is not None and first.provenance is not None and first.evidence is not None
    assert second.definition is not None and second.provenance is not None and second.evidence is not None
    if canonical_json_bytes(first.definition) != canonical_json_bytes(second.definition) or canonical_json_bytes(first.provenance) != canonical_json_bytes(second.provenance):
        return _failed(_issue("NON_DETERMINISTIC_OUTPUT", "$", "identical inputs produced different definition or provenance bytes"))

    evidence = copy.deepcopy(first.evidence)
    evidence["deterministic_rebuild"] = "PASS"
    evidence["evidence_sha256"] = hash_without_field(evidence, "evidence_sha256")
    return CompileReport("PASS", (), first.definition, first.provenance, evidence)


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.parent.is_symlink():
        raise ValueError(f"output parent must not be a symlink: {path.parent}")
    temporary = path.with_name(path.name + ".tmp")
    try:
        temporary.write_bytes(payload)
        temporary.replace(path)
    finally:
        if temporary.exists():
            temporary.unlink()


def write_compilation_artifacts(output_root: Path, report: CompileReport) -> list[Path]:
    """Write canonical artifacts only after a complete PASS."""
    if not report.passed or report.definition is None or report.provenance is None or report.evidence is None:
        raise ValueError("refusing to write failed or incomplete compilation")
    candidate_id = report.definition["candidate_id"]
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", candidate_id):
        raise ValueError("unsafe candidate id")
    candidate_root = output_root / candidate_id
    paths_and_documents = [
        (candidate_root / "definition.json", report.definition),
        (candidate_root / "provenance.json", report.provenance),
        (candidate_root / "compile-evidence.json", report.evidence),
    ]
    for path, document in paths_and_documents:
        _atomic_write(path, canonical_json_bytes(document))
    return [path for path, _ in paths_and_documents]


def repository_documents(repo_root: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    manifest = load_json_object(repo_root / "evaluation" / "external-skills" / "snapshots" / "manifest.json")
    policy = load_json_object(HERE / "policy" / "offline-adaptation-policy-v1.json")
    rules = load_json_object(HERE / "policy" / "transform-rules-v1.json")
    return manifest, policy, rules


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compile one pinned snapshot to an offline V8.4 DRAFT")
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--candidate-id", choices=["kd-sympy", "kd-citation-management"], required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args(argv)

    manifest, policy, rules = repository_documents(args.repo_root)
    compiler_input = input_from_manifest(manifest, policy, args.candidate_id)
    report = compile_candidate(
        repo_root=args.repo_root,
        compiler_input=compiler_input,
        manifest=manifest,
        policy=policy,
        rules=rules,
    )
    if not report.passed:
        print(json.dumps(report.as_dict(), ensure_ascii=False, sort_keys=True))
        return 1
    paths = write_compilation_artifacts(args.output_root, report)
    print(json.dumps({"status": "PASS", "candidate_id": args.candidate_id, "paths": [str(path) for path in paths]}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
