"""Tests for Phase 1 scorer."""

from aocs_mcp.phase1.scorer import score_interp_as_problem, Phase1Runner
from aocs_mcp.pipeline.models import Phase0Result, Interpretation


def test_score_interp_defaults():
    sp = score_interp_as_problem("Test interpretation", "root cause", 1)
    assert sp.name.startswith("sub-1:")
    assert 0 <= sp.impact <= 10
    assert 0 <= sp.leverage <= 10
    assert 0 <= sp.urgency <= 10
    assert 0 <= sp.learning <= 10
    assert sp.weighted_score > 0


def test_phase1_runner_empty():
    runner = Phase1Runner()
    result = runner.run(Phase0Result())
    assert len(result.sub_problems) == 0
    assert result.top_problem is None


def test_phase1_runner_with_interpretations():
    interps = [
        Interpretation(label="Hardware issue", root_cause="bad RAM", lens="Hardware", rationale="test"),
        Interpretation(label="Software bug", root_cause="null pointer", lens="Software", rationale="test"),
    ]
    phase0 = Phase0Result(parsed_problem="test", interpretations=interps)
    runner = Phase1Runner()
    result = runner.run(phase0)

    assert len(result.sub_problems) == 2
    assert result.top_problem is not None
    # Top problem should have highest weighted score
    assert result.sub_problems[0].weighted_score >= result.sub_problems[1].weighted_score


def test_scored_problem_zones():
    sp = score_interp_as_problem("test", "cause", 1)
    assert sp.zone in ("Noise", "Small", "Big", "Critical")


if __name__ == "__main__":
    test_score_interp_defaults()
    test_phase1_runner_empty()
    test_phase1_runner_with_interpretations()
    test_scored_problem_zones()
    print("All scorer tests passed!")
