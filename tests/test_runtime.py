"""Tests for the standalone runtime boundary."""

import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from aocs_mcp.pipeline.models import AnalysisResult
from aocs_mcp.pipeline.orchestrator import AOCSOrchestrator
from aocs_mcp.runtime import AOCSRunRequest, AOCSRuntime


async def _fake_analyze(
    self,
    problem,
    domain=None,
    risk=None,
    fractal_depth=None,
    context=None,
    max_sub_agents=16,
):
    return AnalysisResult(
        problem=problem,
        domain=domain,
        route_taken="type2",
        total_llm_calls=3,
        root_problem="fake root",
        verdict="flag_for_review",
        confidence=80,
        recommendations=["fake recommendation"],
    )


def test_runtime_persists_run_artifacts():
    with tempfile.TemporaryDirectory() as tmp:
        with patch.object(AOCSOrchestrator, "analyze", _fake_analyze):
            result = asyncio.run(
                AOCSRuntime(output_root=tmp).run(AOCSRunRequest(problem="test problem"))
            )

        run_dir = Path(result.run_dir)
        assert result.run_id
        assert run_dir.exists()
        assert (run_dir / "request.json").exists()
        assert (run_dir / "result.json").exists()
        assert (run_dir / "trace.json").exists()
        assert (run_dir / "summary.md").exists()

        status = json.loads((run_dir / "status.json").read_text(encoding="utf-8"))
        assert status["status"] == "completed"
        assert status["total_llm_calls"] == 3


if __name__ == "__main__":
    test_runtime_persists_run_artifacts()
    print("runtime tests passed")
