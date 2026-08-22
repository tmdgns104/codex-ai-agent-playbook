#!/usr/bin/env python3
"""Focused tests for the V8.1 dry-run capability activation manager."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from capability_manager import activation_decision, build_activation_plan

ROUTER_DIR = Path(__file__).resolve().parents[1] / "router"
if str(ROUTER_DIR) not in sys.path:
    sys.path.insert(0, str(ROUTER_DIR))

from capability_router import load_capabilities  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]


def synthetic_capability(
    capability_id: str,
    capability_type: str = "skill",
    *,
    permissions: list[str] | None = None,
) -> dict:
    return {
        "id": capability_id,
        "type": capability_type,
        "summary": "synthetic",
        "domains": ["synthetic"],
        "triggers": ["synthetic"],
        "activation": "on_demand",
        "risk": "low",
        "recommended_profile": "standard",
        "permissions": permissions or ["local_read"],
        "context_cost": "low",
        "dependencies": [],
        "source_id": "test",
        "license": "test",
        "path": "capability-library/skills/optional/test",
    }


class CapabilityManagerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.capabilities = load_capabilities(ROOT)

    def test_trivial_task_returns_no_action(self) -> None:
        result = build_activation_plan("README 오타 한 줄 수정", self.capabilities)
        self.assertEqual(result["result"], "NO_ACTION")
        self.assertEqual(result["count"], 0)
        self.assertEqual(result["profile"], "minimal")
        self.assertFalse(result["side_effects_executed"])

    def test_security_review_is_auto_allowed(self) -> None:
        result = build_activation_plan("JWT 인증 보안 검토", self.capabilities)
        item = next(plan for plan in result["plans"] if plan["id"] == "security-review")
        self.assertEqual(item["decision"], "AUTO_ALLOWED")

    def test_testing_is_profile_gated(self) -> None:
        result = build_activation_plan("pytest regression test를 실행", self.capabilities)
        item = next(plan for plan in result["plans"] if plan["id"] == "testing")
        self.assertEqual(item["decision"], "PROFILE_GATED")

    def test_documentation_lookup_requires_network_review(self) -> None:
        result = build_activation_plan("최신 API 공식 문서를 확인", self.capabilities)
        item = next(plan for plan in result["plans"] if plan["id"] == "documentation-lookup")
        self.assertEqual(item["decision"], "NETWORK_REVIEW")

    def test_github_ops_requires_human_gate(self) -> None:
        result = build_activation_plan("GitHub에 commit push하고 PR 생성", self.capabilities)
        item = next(plan for plan in result["plans"] if plan["id"] == "github-ops")
        self.assertEqual(item["decision"], "HUMAN_GATE_REQUIRED")

    def test_read_only_mcp_is_manual_only_in_p0(self) -> None:
        decision, _ = activation_decision(
            synthetic_capability("browser-mcp", "mcp", permissions=["local_read"])
        )
        self.assertEqual(decision, "MANUAL_ONLY")

    def test_read_only_agent_is_manual_only_in_p0(self) -> None:
        decision, _ = activation_decision(
            synthetic_capability("review-agent", "agent", permissions=["local_read"])
        )
        self.assertEqual(decision, "MANUAL_ONLY")

    def test_sensitive_permission_overrides_mcp_manual_only(self) -> None:
        decision, _ = activation_decision(
            synthetic_capability(
                "sensitive-mcp",
                "mcp",
                permissions=["local_read", "credential_access"],
            )
        )
        self.assertEqual(decision, "HUMAN_GATE_REQUIRED")

    def test_sensitive_permission_overrides_agent_manual_only(self) -> None:
        decision, _ = activation_decision(
            synthetic_capability(
                "sensitive-agent",
                "agent",
                permissions=["local_read", "production"],
            )
        )
        self.assertEqual(decision, "HUMAN_GATE_REQUIRED")

    def test_router_profile_is_preserved(self) -> None:
        result = build_activation_plan(
            "JWT 인증 오류를 수정하고 regression test를 실행",
            self.capabilities,
        )
        self.assertEqual(result["profile"], "strict")
        self.assertEqual(result["count"], 3)

    def test_no_side_effect_flag_is_always_false(self) -> None:
        result = build_activation_plan("GitHub에 commit push하고 PR 생성", self.capabilities)
        self.assertFalse(result["side_effects_executed"])

    def test_json_cli_output_is_machine_readable(self) -> None:
        script = ROOT / "harness" / "activation" / "capability_manager.py"
        result = subprocess.run(
            [
                sys.executable,
                str(script),
                "--root",
                str(ROOT),
                "--task",
                "최신 API 공식 문서를 확인",
                "--json",
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertIn("plans", payload)
        self.assertIn("gates", payload)
        self.assertFalse(payload["side_effects_executed"])


if __name__ == "__main__":
    unittest.main()
