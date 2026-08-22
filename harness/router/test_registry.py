#!/usr/bin/env python3
"""Focused regression tests for the V8.1 capability registry validator."""

from __future__ import annotations

import copy
import unittest

from registry import RegistryValidationError, validate_registry, validate_sources


class RegistryValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.sources = {
            "schema_version": 1,
            "sources": [
                {
                    "id": "internal",
                    "name": "internal",
                    "kind": "internal",
                    "license": "repository",
                    "adaptation": "original",
                }
            ],
        }
        self.capability = {
            "id": "security-review",
            "type": "skill",
            "summary": "security review",
            "domains": ["security"],
            "triggers": ["jwt"],
            "activation": "on_demand",
            "risk": "high",
            "recommended_profile": "strict",
            "permissions": ["local_read"],
            "context_cost": "medium",
            "dependencies": [],
            "source_id": "internal",
            "license": "repository",
            "path": "capability-library/skills/optional/security-review",
        }

    def registry(self, capabilities: list[dict] | None = None) -> dict:
        return {
            "schema_version": 1,
            "capabilities": capabilities if capabilities is not None else [copy.deepcopy(self.capability)],
        }

    def test_valid_registry_passes(self) -> None:
        source_ids = validate_sources(self.sources)
        entries = validate_registry(self.registry(), source_ids)
        self.assertEqual([entry["id"] for entry in entries], ["security-review"])

    def test_duplicate_id_fails(self) -> None:
        source_ids = validate_sources(self.sources)
        duplicate = copy.deepcopy(self.capability)
        with self.assertRaisesRegex(RegistryValidationError, "duplicate capability id"):
            validate_registry(self.registry([copy.deepcopy(self.capability), duplicate]), source_ids)

    def test_invalid_permission_fails(self) -> None:
        source_ids = validate_sources(self.sources)
        invalid = copy.deepcopy(self.capability)
        invalid["permissions"] = ["root_everything"]
        with self.assertRaisesRegex(RegistryValidationError, "permissions unknown"):
            validate_registry(self.registry([invalid]), source_ids)

    def test_unknown_source_fails(self) -> None:
        source_ids = validate_sources(self.sources)
        invalid = copy.deepcopy(self.capability)
        invalid["source_id"] = "missing-source"
        with self.assertRaisesRegex(RegistryValidationError, "source_id unknown"):
            validate_registry(self.registry([invalid]), source_ids)

    def test_personal_absolute_path_fails(self) -> None:
        source_ids = validate_sources(self.sources)
        invalid = copy.deepcopy(self.capability)
        invalid["path"] = r"C:\Users\someone\.agents\skills\security-review"
        with self.assertRaisesRegex(RegistryValidationError, "absolute/personal"):
            validate_registry(self.registry([invalid]), source_ids)

    def test_unknown_dependency_fails(self) -> None:
        source_ids = validate_sources(self.sources)
        invalid = copy.deepcopy(self.capability)
        invalid["dependencies"] = ["missing-capability"]
        with self.assertRaisesRegex(RegistryValidationError, "dependencies unknown id"):
            validate_registry(self.registry([invalid]), source_ids)


if __name__ == "__main__":
    unittest.main()
