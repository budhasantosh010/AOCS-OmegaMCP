"""Tests for Pydantic models."""

from aocs_mcp.pipeline.models import (
    AnalysisResult, Phase0Result, Type2Result, SpecialistOutput,
    RedTeamOutput, ContrarianOutput, JudgeVerdict, GateResult,
    Assumption, Interpretation, DeepTestResult,
)


def test_assumption_defaults():
    a = Assumption(statement="Test assumption")
    assert a.statement == "Test assumption"
    assert a.certainty == 0.5
    assert a.provenance == "LLM-Hypothesized"


def test_analysis_result_empty():
    r = AnalysisResult()
    assert r.problem == ""
    assert r.domain == "software"
    assert r.problem_type == "type2"
    assert r.verdict == "flag_for_review"
    assert len(r.interpretations) == 0
    assert r.total_llm_calls == 0


def test_analysis_result_with_data():
    r = AnalysisResult(
        problem="Test problem",
        domain="software",
        problem_type="type2",
        root_problem="Root cause",
        verdict="accept",
        confidence=95.0,
        recommendations=["Do X"],
    )
    assert r.problem == "Test problem"
    assert r.root_problem == "Root cause"
    assert r.verdict == "accept"
    assert r.confidence == 95.0
    assert r.recommendations == ["Do X"]


def test_type2_result_full():
    r = Type2Result(
        specialist=SpecialistOutput(proposal="Fix X", reasoning="Because", prediction="Works", confidence=80),
        red_team=RedTeamOutput(critique="Not good", flaws=["Missing edge case"], risk_estimate="medium"),
        contrarian=ContrarianOutput(analysis="Alternative view", agreement_level="partial"),
        deception_flags=["Cherry-picked data"],
        judge=JudgeVerdict(confidence=75, decision="flag_for_review", reasoning="Needs work"),
    )
    assert r.specialist.proposal == "Fix X"
    assert r.specialist.confidence == 80
    assert len(r.red_team.flaws) == 1
    assert r.judge.decision == "flag_for_review"
    assert len(r.deception_flags) == 1


def test_gate_result_pass():
    g = GateResult(gate_number=1, name="Self-Check", passed=True, details="OK")
    assert g.passed
    assert g.gate_number == 1


def test_phase0_result():
    interp = Interpretation(label="Test", root_cause="cause", lens="SW", rationale="test")
    dt = DeepTestResult(question_1="Q1", passed=True)
    r = Phase0Result(
        parsed_problem="problem",
        interpretations=[interp],
        root_problem="root",
        deep_test=dt,
    )
    assert len(r.interpretations) == 1
    assert r.root_problem == "root"
    assert r.deep_test.passed


def test_serialization():
    """Pydantic models should serialize to dict and back."""
    r = AnalysisResult(problem="test", confidence=88.5, verdict="flag_for_review")
    data = r.model_dump()
    assert data["problem"] == "test"
    assert data["confidence"] == 88.5
    assert data["verdict"] == "flag_for_review"
    restored = AnalysisResult(**data)
    assert restored.confidence == 88.5


if __name__ == "__main__":
    test_assumption_defaults()
    test_analysis_result_empty()
    test_analysis_result_with_data()
    test_type2_result_full()
    test_gate_result_pass()
    test_phase0_result()
    test_serialization()
    print("All model tests passed!")
