"""Tests for low-risk direct-route collapse."""

import asyncio

from aocs_mcp.pipeline.orchestrator import AOCSOrchestrator
from aocs_mcp.pipeline.models import AuditResult, Classification, ShadowResult


class FakeRouter:
    def __init__(self):
        self.call_count = 0
        self.call_log = []

    def reset_trace(self, max_calls=None):
        self.call_count = 0
        self.call_log = []

    async def call(self, role, system_prompt, user_prompt, expect_json=False):
        self.call_count += 1
        self.call_log.append({"role": role})
        return "2 + 2 = 4."


def test_low_risk_arithmetic_uses_direct_route():
    router = FakeRouter()
    result = asyncio.run(
        AOCSOrchestrator(router, config=None).analyze(
            "What is 2 + 2?",
            domain="general",
            risk="low",
            fractal_depth=0,
        )
    )

    assert result.route_taken == "direct-low-risk"
    assert result.problem_type == "type1"
    assert result.total_llm_calls == 1
    assert result.specialist_proposal == "2 + 2 = 4."
    assert router.call_log == [{"role": "direct-answer"}]


def test_unhinted_arithmetic_uses_direct_llm_route():
    router = FakeRouter()
    result = asyncio.run(
        AOCSOrchestrator(router, config=None).analyze(
            "what is 2+2?",
        )
    )

    assert result.route_taken == "direct-answer"
    assert result.problem_type == "type1"
    assert result.total_llm_calls == 1
    assert result.specialist_proposal == "2 + 2 = 4."
    assert router.call_log == [{"role": "direct-answer"}]


def test_shadow_reroute_is_promoted_to_recommendation():
    shadow = ShadowResult(
        divergence_detected=True,
        original_classification=Classification(problem_type="type2", risk_level="medium"),
        shadow_classification=Classification(problem_type="type3", risk_level="critical"),
        safe_path="Use shadow: type3 (risk critical)",
    )

    recs = AOCSOrchestrator._build_recommendations(
        "flag_for_review",
        AuditResult(),
        shadow,
    )

    assert any("Shadow orchestrator recommends safer reroute" in rec for rec in recs)
    assert any("type3" in rec and "critical" in rec for rec in recs)


if __name__ == "__main__":
    test_low_risk_arithmetic_uses_direct_route()
    test_unhinted_arithmetic_uses_direct_llm_route()
    test_shadow_reroute_is_promoted_to_recommendation()
    print("orchestrator direct-route tests passed")
