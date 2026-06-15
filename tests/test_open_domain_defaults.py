"""Regression tests for open-domain AOCS request hints."""

import argparse
import asyncio
from unittest.mock import patch

from aocs_mcp.cli import _run, build_parser
from aocs_mcp.phase0.assumptions import AssumptionMapper
from aocs_mcp.phase0.parser import parse
from aocs_mcp.pipeline.models import AnalysisResult


def test_parser_without_domain_does_not_assume_software():
    parsed = parse("find the cure of cancer")

    assert "domain: software" not in parsed.lower()
    assert "Domain: auto-infer" in parsed


def test_assumption_mapper_without_domain_uses_open_domain_assumptions():
    assumptions = AssumptionMapper().extract([], None, "find the cure of cancer")
    statements = [item.statement for item in assumptions]

    assert "The development environment matches production" not in statements
    assert any("problem statement may be underspecified" in item.lower() for item in statements)


def test_cli_parser_defaults_are_open_domain():
    parser = build_parser()
    args = parser.parse_args(["run", "find", "the", "cure", "of", "cancer"])

    assert args.domain is None
    assert args.risk is None
    assert args.fractal_depth is None


def test_cli_run_default_domain_and_risk_are_open():
    captured = {}

    async def fake_run(self, request):
        captured["domain"] = request.domain
        captured["risk"] = request.risk
        captured["fractal_depth"] = request.fractal_depth
        return AnalysisResult(problem=request.problem)

    args = argparse.Namespace(
        problem=["find the cure of cancer"],
        domain=None,
        risk=None,
        fractal_depth=None,
        context=None,
        max_sub_agents=16,
        output_dir=None,
        no_store=True,
    )

    with patch("aocs_mcp.cli.AOCSRuntime.run", fake_run):
        asyncio.run(_run(args))

    assert captured["domain"] is None
    assert captured["risk"] is None
    assert captured["fractal_depth"] is None


if __name__ == "__main__":
    test_parser_without_domain_does_not_assume_software()
    test_assumption_mapper_without_domain_uses_open_domain_assumptions()
    test_cli_parser_defaults_are_open_domain()
    test_cli_run_default_domain_and_risk_are_open()
    print("open-domain default tests passed")
