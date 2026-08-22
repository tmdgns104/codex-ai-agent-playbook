#!/usr/bin/env python3
"""Validate the V8.1 Dynamic Capability Library metadata registry."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

CAPABILITY_TYPES = {"skill", "mcp", "agent", "cli-wrapper", "rest-wrapper"}
ACTIVATION_MODES = {"on_demand", "conditional", "manual"}
RISK_LEVELS = {"low", "medium", "high", "critical"}
PROFILES = {"minimal", "standard", "strict"}
CONTEXT_COSTS = {"low", "medium", "high"}
PERMISSIONS = {
    "local_read",
    "local_write",
    "process_exec",
    "network",
    "browser_control",
    "credential_access",
    "external_write",
    "database_write",
    "destructive",
    "production",
}
REQUIRED_FIELDS = {
    "id",
    "type",
    "summary",
    "domains",
    "triggers",
    "activation",
    "risk",
    "recommended_profile",
    "permissions",
    "context_cost",
    "dependencies",
    "source_id",
    "license",
    "path",
}
ALLOWED_LIBRARY_PREFIXES = (
    "capability-library/skills/optional/",
    "capability-library/mcp/optional/",
    "capability-library/agents/optional/",
    "capability-library/wrappers/cli/",
    "capability-library/wrappers/rest/",
)
PERSONAL_ABSOLUTE_PATH = re.compile(
    r"^(?:[A-Za-z]:[\\/]|/Users/|/home/)|(?:[A-Za-z]:\\Users\\[^\\]+|/Users/[^/]+|/home/[^/]+)"
)
ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class RegistryValidationError(ValueError):
    """Raised when capability metadata is invalid."""


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RegistryValidationError(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RegistryValidationError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise RegistryValidationError(f"top-level JSON must be an object: {path}")
    return data


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _string_list(value: Any, *, allow_empty: bool = True) -> bool:
    if not isinstance(value, list) or not all(_non_empty_string(item) for item in value):
        return False
    return allow_empty or bool(value)


def validate_sources(data: dict[str, Any]) -> set[str]:
    errors: list[str] = []
    if data.get("schema_version") != 1:
        errors.append("sources schema_version must be 1")
    sources = data.get("sources")
    if not isinstance(sources, list) or not sources:
        errors.append("sources must be a non-empty list")
        sources = []

    ids: set[str] = set()
    for index, source in enumerate(sources):
        label = f"sources[{index}]"
        if not isinstance(source, dict):
            errors.append(f"{label} must be an object")
            continue
        source_id = source.get("id")
        if not _non_empty_string(source_id):
            errors.append(f"{label}.id must be a non-empty string")
            continue
        if source_id in ids:
            errors.append(f"duplicate source id: {source_id}")
        ids.add(source_id)
        for key in ("name", "kind", "license", "adaptation"):
            if not _non_empty_string(source.get(key)):
                errors.append(f"{label}.{key} must be a non-empty string")

    if errors:
        raise RegistryValidationError("; ".join(errors))
    return ids


def validate_registry(data: dict[str, Any], source_ids: set[str]) -> list[dict[str, Any]]:
    errors: list[str] = []
    if data.get("schema_version") != 1:
        errors.append("registry schema_version must be 1")
    capabilities = data.get("capabilities")
    if not isinstance(capabilities, list) or not capabilities:
        errors.append("capabilities must be a non-empty list")
        capabilities = []

    ids: set[str] = set()
    entries: list[dict[str, Any]] = []

    for index, capability in enumerate(capabilities):
        label = f"capabilities[{index}]"
        if not isinstance(capability, dict):
            errors.append(f"{label} must be an object")
            continue
        entries.append(capability)
        missing = REQUIRED_FIELDS - capability.keys()
        if missing:
            errors.append(f"{label} missing fields: {', '.join(sorted(missing))}")
            continue

        capability_id = capability.get("id")
        if not _non_empty_string(capability_id) or not ID_PATTERN.fullmatch(capability_id):
            errors.append(f"{label}.id must be kebab-case")
        elif capability_id in ids:
            errors.append(f"duplicate capability id: {capability_id}")
        else:
            ids.add(capability_id)

        if capability.get("type") not in CAPABILITY_TYPES:
            errors.append(f"{label}.type invalid: {capability.get('type')}")
        if capability.get("activation") not in ACTIVATION_MODES:
            errors.append(f"{label}.activation invalid: {capability.get('activation')}")
        if capability.get("risk") not in RISK_LEVELS:
            errors.append(f"{label}.risk invalid: {capability.get('risk')}")
        if capability.get("recommended_profile") not in PROFILES:
            errors.append(f"{label}.recommended_profile invalid: {capability.get('recommended_profile')}")
        if capability.get("context_cost") not in CONTEXT_COSTS:
            errors.append(f"{label}.context_cost invalid: {capability.get('context_cost')}")

        if not _non_empty_string(capability.get("summary")):
            errors.append(f"{label}.summary must be non-empty")
        if not _string_list(capability.get("domains"), allow_empty=False):
            errors.append(f"{label}.domains must be a non-empty string list")
        if not _string_list(capability.get("triggers")):
            errors.append(f"{label}.triggers must be a string list")
        if not _string_list(capability.get("permissions")):
            errors.append(f"{label}.permissions must be a string list")
        else:
            unknown_permissions = set(capability["permissions"]) - PERMISSIONS
            if unknown_permissions:
                errors.append(
                    f"{label}.permissions unknown: {', '.join(sorted(unknown_permissions))}"
                )
        if not _string_list(capability.get("dependencies")):
            errors.append(f"{label}.dependencies must be a string list")

        source_id = capability.get("source_id")
        if source_id not in source_ids:
            errors.append(f"{label}.source_id unknown: {source_id}")
        if not _non_empty_string(capability.get("license")):
            errors.append(f"{label}.license must be non-empty")

        relative_path = capability.get("path")
        if not _non_empty_string(relative_path):
            errors.append(f"{label}.path must be non-empty")
        else:
            normalized = relative_path.replace("\\", "/")
            if PERSONAL_ABSOLUTE_PATH.search(relative_path) or normalized.startswith("/"):
                errors.append(f"{label}.path must not be absolute/personal: {relative_path}")
            elif ".." in Path(normalized).parts:
                errors.append(f"{label}.path must not traverse parents: {relative_path}")
            elif not normalized.startswith(ALLOWED_LIBRARY_PREFIXES):
                errors.append(f"{label}.path outside allowed capability library roots: {relative_path}")

    for index, capability in enumerate(entries):
        dependencies = capability.get("dependencies")
        if not isinstance(dependencies, list):
            continue
        for dependency in dependencies:
            if isinstance(dependency, str) and dependency not in ids:
                errors.append(f"capabilities[{index}].dependencies unknown id: {dependency}")

    if errors:
        raise RegistryValidationError("; ".join(errors))
    return entries


def validate_root(root: Path) -> tuple[int, int]:
    library = root / "capability-library"
    sources = load_json(library / "sources.json")
    source_ids = validate_sources(sources)
    registry = load_json(library / "registry.json")
    entries = validate_registry(registry, source_ids)
    return len(source_ids), len(entries)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate V8.1 capability registry metadata.")
    parser.add_argument("--root", default=".", help="Playbook repository root.")
    parser.add_argument("--quiet", action="store_true", help="Only print failures.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    try:
        source_count, capability_count = validate_root(root)
    except RegistryValidationError as exc:
        print(f"FAIL       capability registry: {exc}")
        return 1

    if not args.quiet:
        print(f"PASS       capability sources: {source_count}")
        print(f"PASS       capability registry: {capability_count}")
        print("RESULT     PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
