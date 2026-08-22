#!/usr/bin/env python3
"""Focused tests for the V8.1 deterministic capability router."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from capability_router import load_capabilities, route_capabilities
from scoring import contains_phrase, normalized_phrase

ROOT = Path(__file__).resolve().parents[2]


def synthetic_capability(
    capability_id: str,
    capability_type: str,
    *,
    triggers: list[str],
    domains: list[str] | None = None,
    summary: str = "synthetic candidate",
    profile: str = "standard",
    context_cost: str = "low",
    risk: str = "low",
) -> dict:
    return {
        "id": capability_id,
        "type": capability_type,
        "summary": summary,
        "domains": domains or [],
        "triggers": triggers,
        "activation": "on_demand",
        "risk": risk,
        "recommended_profile": profile,
        "permissions": ["local_read"],
        "context_cost": context_cost,
        "dependencies": [],
        "source_id": "test",
        "license": "test",
        "path": "capability-library/skills/optional/test",
    }


class CapabilityRouterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.capabilities = load_capabilities(ROOT)

    def ids(self, task: str) -> list[str]:
        result = route_capabilities(task, self.capabilities)
        return [item["id"] for item in result["selected"]]

    def test_trivial_task_allows_zero_capabilities(self) -> None:
        result = route_capabilities("README의 오타 한 글자 수정", self.capabilities)
        self.assertEqual(result["count"], 0)
        self.assertEqual(result["profile"], "minimal")
        self.assertEqual(result["result"], "NO_CAPABILITY")

    def test_korean_jwt_auth_routes_security_review(self) -> None:
        result = route_capabilities("JWT 인증 권한 오류를 수정", self.capabilities)
        ids = [item["id"] for item in result["selected"]]
        self.assertIn("security-review", ids)
        self.assertEqual(result["profile"], "strict")

    def test_testing_signal_routes_testing(self) -> None:
        ids = self.ids("pytest 테스트 실패 회귀 원인을 확인")
        self.assertIn("testing", ids)

    def test_documentation_signal_routes_docs_lookup(self) -> None:
        ids = self.ids("최신 API 공식 문서 version 사용법 확인")
        self.assertIn("documentation-lookup", ids)

    def test_github_signal_routes_github_ops_and_requires_approval(self) -> None:
        result = route_capabilities("git 브랜치에서 commit push 하고 PR 생성", self.capabilities)
        github = next(item for item in result["selected"] if item["id"] == "github-ops")
        self.assertEqual(github["approval"], "required")

    def test_root_cause_signal_routes_debugging(self) -> None:
        ids = self.ids("버그 오류 원인을 디버그해서 찾아줘")
        self.assertIn("root-cause-debugging", ids)

    def test_review_signal_routes_code_review(self) -> None:
        ids = self.ids("리팩터링 diff를 리뷰하고 품질 검토")
        self.assertIn("code-review", ids)

    def test_total_selection_never_exceeds_three(self) -> None:
        result = route_capabilities(
            "JWT 인증 버그를 테스트하고 최신 API 문서를 검토한 뒤 git push PR 리뷰",
            self.capabilities,
        )
        self.assertLessEqual(result["count"], 3)

    def test_mcp_threshold_is_lower_than_agent_but_both_are_high(self) -> None:
        task = "foo bar baz"
        mcp = synthetic_capability(
            "mcp-candidate",
            "mcp",
            triggers=["foo"],
            domains=["bar"],
            summary="baz",
        )
        agent = synthetic_capability(
            "agent-candidate",
            "agent",
            triggers=["foo"],
            domains=["bar"],
            summary="baz",
        )
        result = route_capabilities(task, [mcp, agent])
        ids = [item["id"] for item in result["selected"]]
        self.assertIn("mcp-candidate", ids)
        self.assertNotIn("agent-candidate", ids)

    def test_single_weak_signal_does_not_select_mcp_or_agent(self) -> None:
        candidates = [
            synthetic_capability("weak-mcp", "mcp", triggers=["foo"]),
            synthetic_capability("weak-agent", "agent", triggers=["foo"]),
        ]
        result = route_capabilities("foo", candidates)
        self.assertEqual(result["count"], 0)

    def test_tie_break_is_deterministic_and_lexical_last_resort(self) -> None:
        candidates = [
            synthetic_capability("beta", "skill", triggers=["shared"]),
            synthetic_capability("alpha", "skill", triggers=["shared"]),
        ]
        result = route_capabilities("shared", candidates, max_selected=1)
        self.assertEqual(result["selected"][0]["id"], "alpha")

    def test_json_cli_output_is_machine_readable(self) -> None:
        script = ROOT / "harness" / "router" / "capability_router.py"
        result = subprocess.run(
            [sys.executable, str(script), "--root", str(ROOT), "--task", "README 오타 수정", "--json"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertIn("selected", payload)
        self.assertIn("profile", payload)
        self.assertIn("result", payload)

    def test_known_korean_particles_extend_trigger_boundary(self) -> None:
        task = normalized_phrase("JWT 인증 오류를 수정하고 regression test를 실행")
        self.assertTrue(contains_phrase(task, "오류"))
        self.assertTrue(contains_phrase(task, "test"))

    def test_unrelated_korean_suffix_does_not_match(self) -> None:
        task = normalized_phrase("보안관을 호출")
        self.assertFalse(contains_phrase(task, "보안"))

    def test_ascii_prefix_does_not_match_longer_ascii_word(self) -> None:
        task = normalized_phrase("problem을 분석")
        self.assertFalse(contains_phrase(task, "pr"))

    def test_real_jwt_regression_sentence_avoids_code_review_false_activation(self) -> None:
        result = route_capabilities(
            "JWT 인증 오류를 수정하고 regression test를 실행",
            self.capabilities,
        )
        ids = [item["id"] for item in result["selected"]]
        self.assertEqual(result["count"], 3)
        self.assertEqual(result["profile"], "strict")
        self.assertIn("security-review", ids)
        self.assertIn("testing", ids)
        self.assertIn("root-cause-debugging", ids)
        self.assertNotIn("code-review", ids)


if __name__ == "__main__":
    unittest.main()
