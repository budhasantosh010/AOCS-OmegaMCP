"""Kill-switch and break-framework tests."""

import asyncio

from aocs_mcp.breakthrough.break_framework import BreakFrameworkAgent
from aocs_mcp.breakthrough.higher_dimension import HigherDimension
from aocs_mcp.quality.kill_switch import KillSwitch
from tests.fakes import ScriptedRouter


def test_kill_switch_fires_after_two_failures_on_same_approach():
    switch = KillSwitch(max_failures=2)

    first = switch.record_failure("type2:root-problem", "Quality gates failed.")
    second = switch.record_failure("type2:root-problem", "Quality gates failed again.")

    assert not first.fired
    assert second.fired
    assert second.failure_count == 2
    assert not switch.can_attempt("type2:root-problem")


def test_kill_switch_does_not_merge_different_approaches():
    switch = KillSwitch(max_failures=2)

    switch.record_failure("type1:first-root", "failed")
    result = switch.record_failure("type2:reframed-root", "failed")

    assert not result.fired
    assert switch.can_attempt("type1:first-root")
    assert switch.can_attempt("type2:reframed-root")


def test_break_framework_agent_invents_and_logs_temporary_structure():
    router = ScriptedRouter(
        {
            "break-framework": [
                {
                    "temporary_structure": "Evidence-first inversion loop",
                    "reordered_phases": ["verify evidence", "frame", "generate"],
                    "temporary_agents": ["Evidence Coroner"],
                    "verification_sequence": ["reality test", "red team", "judge"],
                    "proposal": "Test the evidence before generating another solution.",
                }
            ]
        }
    )

    result = asyncio.run(
        BreakFrameworkAgent(router).run(
            problem="Repeated attempts fail.",
            reason="Kill-switch fired.",
        )
    )

    assert result.triggered
    assert result.temporary_structure == "Evidence-first inversion loop"
    assert result.temporary_agents == ["Evidence Coroner"]


def test_higher_dimension_preserves_the_reframed_problem():
    router = ScriptedRouter(
        {
            "higher-dimension": [
                {
                    "current_frame": "Optimize the current transport",
                    "higher_dimension_view": "The real need is access, not transport",
                    "reframed_problem": "Provide access without requiring transport",
                    "adapted_proposal": "Test telepresence and local delivery.",
                }
            ]
        }
    )

    result = asyncio.run(HigherDimension(router).run("Improve transport."))

    assert result.reframed_problem == "Provide access without requiring transport"


if __name__ == "__main__":
    test_kill_switch_fires_after_two_failures_on_same_approach()
    test_kill_switch_does_not_merge_different_approaches()
    test_break_framework_agent_invents_and_logs_temporary_structure()
    test_higher_dimension_preserves_the_reframed_problem()
    print("kill-switch tests passed")
