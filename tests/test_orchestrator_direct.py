"""Tests for low-risk direct-route collapse."""

import asyncio

from aocs_mcp.pipeline.orchestrator import AOCSOrchestrator


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
    assert result.total_llm_calls == 0
    assert result.specialist_proposal == "4"
    assert router.call_log == []


def test_default_arithmetic_uses_deterministic_route():
    router = FakeRouter()
    result = asyncio.run(
        AOCSOrchestrator(router, config=None).analyze(
            "what is 2+2?",
            domain="software",
            risk="medium",
            fractal_depth=1,
        )
    )

    assert result.route_taken == "direct-arithmetic"
    assert result.problem_type == "type1"
    assert result.total_llm_calls == 0
    assert result.specialist_proposal == "4"
    assert router.call_log == []


if __name__ == "__main__":
    test_low_risk_arithmetic_uses_direct_route()
    test_default_arithmetic_uses_deterministic_route()
    print("orchestrator direct-route tests passed")
