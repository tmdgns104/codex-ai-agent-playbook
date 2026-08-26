"""Small deterministic JSON Schema subset used by the V8.4 context contract.

This is intentionally not a general JSON Schema implementation. It supports only
the Draft 2020-12 keywords used by the five versioned schemas in this directory.
Keeping the supported surface explicit avoids adding a runtime dependency or
silently accepting an unsupported schema feature.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any


SUPPORTED_TYPES = {"array", "boolean", "integer", "null", "object", "string"}
RFC3339_DATE_TIME = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)
SUPPORTED_KEYWORDS = {
    "$defs",
    "$id",
    "$ref",
    "$schema",
    "additionalProperties",
    "anyOf",
    "const",
    "description",
    "enum",
    "format",
    "items",
    "maxItems",
    "maxLength",
    "maximum",
    "minItems",
    "minLength",
    "minimum",
    "pattern",
    "properties",
    "required",
    "title",
    "type",
    "uniqueItems",
}


@dataclass(frozen=True)
class SchemaViolation:
    path: str
    message: str


class SchemaDefinitionError(ValueError):
    """Raised when a repository schema uses an invalid or unsupported construct."""


def _json_identity(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _resolve_local_ref(root_schema: dict[str, Any], reference: str) -> dict[str, Any]:
    if not reference.startswith("#/"):
        raise SchemaDefinitionError(f"only local JSON pointers are supported: {reference}")
    current: Any = root_schema
    for encoded_part in reference[2:].split("/"):
        part = encoded_part.replace("~1", "/").replace("~0", "~")
        if not isinstance(current, dict) or part not in current:
            raise SchemaDefinitionError(f"unresolved local schema reference: {reference}")
        current = current[part]
    if not isinstance(current, dict):
        raise SchemaDefinitionError(f"schema reference is not an object: {reference}")
    return current


def validate_schema_definition(schema: dict[str, Any]) -> None:
    """Validate the structural subset relied on by the local schema engine."""
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        raise SchemaDefinitionError("schema must declare Draft 2020-12")
    if not isinstance(schema.get("$id"), str) or not schema["$id"]:
        raise SchemaDefinitionError("schema must have a non-empty $id")

    def walk(node: Any, path: str) -> None:
        if isinstance(node, list):
            for index, item in enumerate(node):
                walk(item, f"{path}/{index}")
            return
        if not isinstance(node, dict):
            return

        unknown = set(node) - SUPPORTED_KEYWORDS
        if unknown:
            raise SchemaDefinitionError(f"unsupported keyword(s) at {path}: {sorted(unknown)}")

        if "$ref" in node:
            if not isinstance(node["$ref"], str):
                raise SchemaDefinitionError(f"$ref must be a string at {path}")
            _resolve_local_ref(schema, node["$ref"])

        declared_type = node.get("type")
        if declared_type is not None and declared_type not in SUPPORTED_TYPES:
            raise SchemaDefinitionError(f"unsupported type at {path}: {declared_type}")

        pattern = node.get("pattern")
        if pattern is not None:
            if not isinstance(pattern, str):
                raise SchemaDefinitionError(f"pattern must be a string at {path}")
            re.compile(pattern)

        declared_format = node.get("format")
        if declared_format is not None and declared_format != "date-time":
            raise SchemaDefinitionError(f"unsupported format at {path}: {declared_format}")

        properties = node.get("properties")
        if properties is not None and not isinstance(properties, dict):
            raise SchemaDefinitionError(f"properties must be an object at {path}")
        required = node.get("required")
        if required is not None:
            if not isinstance(required, list) or not all(isinstance(item, str) for item in required):
                raise SchemaDefinitionError(f"required must be a string list at {path}")
            missing = set(required) - set(properties or {})
            if missing:
                raise SchemaDefinitionError(
                    f"required fields missing from properties at {path}: {sorted(missing)}"
                )

        for key in ("$defs", "properties"):
            entries = node.get(key, {})
            if isinstance(entries, dict):
                for name, child in entries.items():
                    walk(child, f"{path}/{key}/{name}")
        if "items" in node:
            walk(node["items"], f"{path}/items")
        for index, child in enumerate(node.get("anyOf", [])):
            walk(child, f"{path}/anyOf/{index}")

    walk(schema, "#")


def _matches_type(instance: Any, expected: str) -> bool:
    if expected == "null":
        return instance is None
    if expected == "boolean":
        return isinstance(instance, bool)
    if expected == "integer":
        return isinstance(instance, int) and not isinstance(instance, bool)
    if expected == "string":
        return isinstance(instance, str)
    if expected == "array":
        return isinstance(instance, list)
    if expected == "object":
        return isinstance(instance, dict)
    raise SchemaDefinitionError(f"unsupported type: {expected}")


def validate_instance(
    instance: Any,
    schema: dict[str, Any],
    *,
    root_schema: dict[str, Any] | None = None,
    path: str = "$",
) -> list[SchemaViolation]:
    """Return deterministic violations for the supported schema subset."""
    root = root_schema or schema
    violations: list[SchemaViolation] = []

    if "$ref" in schema:
        resolved = _resolve_local_ref(root, schema["$ref"])
        violations.extend(validate_instance(instance, resolved, root_schema=root, path=path))
        siblings = {key: value for key, value in schema.items() if key != "$ref"}
        if siblings:
            violations.extend(validate_instance(instance, siblings, root_schema=root, path=path))
        return violations

    if "anyOf" in schema:
        branches = [
            validate_instance(instance, branch, root_schema=root, path=path)
            for branch in schema["anyOf"]
        ]
        if not any(not branch for branch in branches):
            violations.append(SchemaViolation(path, "does not match any allowed schema"))
        return violations

    if "const" in schema and instance != schema["const"]:
        violations.append(SchemaViolation(path, f"must equal {schema['const']!r}"))
    if "enum" in schema and instance not in schema["enum"]:
        violations.append(SchemaViolation(path, f"must be one of {schema['enum']!r}"))

    expected_type = schema.get("type")
    if expected_type is not None and not _matches_type(instance, expected_type):
        violations.append(SchemaViolation(path, f"must have type {expected_type}"))
        return violations

    if isinstance(instance, str):
        if len(instance) < schema.get("minLength", 0):
            violations.append(SchemaViolation(path, "is shorter than minLength"))
        if "maxLength" in schema and len(instance) > schema["maxLength"]:
            violations.append(SchemaViolation(path, "is longer than maxLength"))
        if "pattern" in schema and re.search(schema["pattern"], instance) is None:
            violations.append(SchemaViolation(path, "does not match required pattern"))
        if schema.get("format") == "date-time":
            try:
                if RFC3339_DATE_TIME.fullmatch(instance) is None:
                    raise ValueError("invalid RFC 3339 lexical form")
                parsed = datetime.fromisoformat(instance[:-1] + "+00:00" if instance.endswith("Z") else instance)
                if parsed.tzinfo is None:
                    raise ValueError("timezone is required")
            except ValueError:
                violations.append(SchemaViolation(path, "must be an RFC 3339 date-time with timezone"))

    if isinstance(instance, int) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            violations.append(SchemaViolation(path, "is below minimum"))
        if "maximum" in schema and instance > schema["maximum"]:
            violations.append(SchemaViolation(path, "is above maximum"))

    if isinstance(instance, list):
        if len(instance) < schema.get("minItems", 0):
            violations.append(SchemaViolation(path, "has fewer than minItems"))
        if "maxItems" in schema and len(instance) > schema["maxItems"]:
            violations.append(SchemaViolation(path, "has more than maxItems"))
        if schema.get("uniqueItems"):
            identities = [_json_identity(item) for item in instance]
            if len(identities) != len(set(identities)):
                violations.append(SchemaViolation(path, "must contain unique items"))
        item_schema = schema.get("items")
        if item_schema is not None:
            for index, item in enumerate(instance):
                violations.extend(
                    validate_instance(item, item_schema, root_schema=root, path=f"{path}[{index}]")
                )

    if isinstance(instance, dict):
        properties = schema.get("properties", {})
        for field in schema.get("required", []):
            if field not in instance:
                violations.append(SchemaViolation(f"{path}.{field}", "is required"))
        for field, value in instance.items():
            if field in properties:
                violations.extend(
                    validate_instance(
                        value,
                        properties[field],
                        root_schema=root,
                        path=f"{path}.{field}",
                    )
                )
            elif schema.get("additionalProperties") is False:
                violations.append(SchemaViolation(f"{path}.{field}", "is not allowed"))

    return violations
