"""Tests for Phase 0 modules."""

from aocs_mcp.phase0.parser import parse
from aocs_mcp.phase0.assumptions import AssumptionMapper
from aocs_mcp.phase0.uncertainty import quantify
from aocs_mcp.pipeline.models import Interpretation


def test_parser_basic():
    result = parse("My app crashes on startup")
    assert "My app crashes on startup" in result
    assert "Domain:" in result
    assert "Input size:" in result


def test_parser_with_error():
    result = parse("""Error: Connection refused
Traceback (most recent call last):
  File "app.py", line 42, in main
    connect()
ConnectionError: Can't connect to database:5432""")
    assert "Error signatures:" in result
    assert "ConnectionError" in result


def test_assumption_mapper_empty():
    mapper = AssumptionMapper()
    assumptions = mapper.extract([], "software")
    assert len(assumptions) > 0  # gets domain defaults


def test_assumption_mapper_with_interpretations():
    interps = [
        Interpretation(label="Hardware fault", root_cause="bad RAM", lens="Hardware", rationale="test"),
    ]
    mapper = AssumptionMapper()
    assumptions = mapper.extract(interps, "software")
    assert len(assumptions) <= 15
    # Should have interpretation-specific assumptions
    has_interp_assumption = any("Hardware fault" in a.statement for a in assumptions)
    assert has_interp_assumption


def test_uncertainty_scoring():
    mapper = AssumptionMapper()
    assumptions = mapper.extract([], "software")
    quantified = quantify(assumptions)

    for a in quantified:
        assert 0.0 <= a.certainty <= 1.0
        assert a.provenance in ("Reality-Tested", "Sandbox-Simulated", "Proof-Only", "LLM-Hypothesized")


def test_uncertainty_short_statements():
    mapper = AssumptionMapper()
    assumptions = mapper.extract([], "software")
    quantified = quantify(assumptions)

    # Short statements should be slightly more certain
    for a in quantified:
        if len(a.statement) < 40:
            assert a.certainty >= 0.4


if __name__ == "__main__":
    test_parser_basic()
    test_parser_with_error()
    test_assumption_mapper_empty()
    test_assumption_mapper_with_interpretations()
    test_uncertainty_scoring()
    test_uncertainty_short_statements()
    print("All Phase 0 tests passed!")
