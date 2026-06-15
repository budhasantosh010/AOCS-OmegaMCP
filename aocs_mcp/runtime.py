"""Standalone AOCS runtime.

This is the product boundary. MCP, CLI, slash commands, and future agent
adapters should call this module instead of knowing about internal phases.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
from pathlib import Path

from pydantic import BaseModel, Field

from aocs_mcp.config import Config
from aocs_mcp.pipeline.models import AnalysisResult
from aocs_mcp.pipeline.orchestrator import AOCSOrchestrator
from aocs_mcp.router import LLMRouter


class AOCSRunRequest(BaseModel):
    """Portable request object used by MCP, CLI, HTTP, and future adapters."""

    problem: str
    domain: str | None = None
    risk: str | None = None
    fractal_depth: int | None = None
    context: str | None = None
    max_sub_agents: int = 16
    persist: bool = True
    metadata: dict = Field(default_factory=dict)


class AOCSRuntime:
    """Run AOCS independently from any coding-agent host."""

    def __init__(
        self,
        config_dir: str | None = None,
        output_root: str | os.PathLike[str] | None = None,
    ):
        self.config = Config(config_dir=config_dir)
        runtime_cfg = self.config.get("runtime", {}) or {}
        self.persist_runs = bool(runtime_cfg.get("persist_runs", True))
        configured_root = runtime_cfg.get("run_dir")
        self.output_root = Path(
            output_root
            or os.environ.get("AOCS_RUN_DIR")
            or configured_root
            or Path.cwd() / ".aocs" / "runs"
        )

    async def run(self, request: AOCSRunRequest) -> AnalysisResult:
        """Run the deterministic engine and optionally persist artifacts."""
        run_id = self._new_run_id(request.problem)
        run_dir = self.output_root / run_id if request.persist and self.persist_runs else None
        started_at = _dt.datetime.now(_dt.timezone.utc).isoformat()

        if run_dir:
            run_dir.mkdir(parents=True, exist_ok=True)
            self._write_json(run_dir / "request.json", request.model_dump())
            self._write_json(
                run_dir / "status.json",
                {
                    "run_id": run_id,
                    "status": "running",
                    "started_at": started_at,
                    "ended_at": None,
                    "error": None,
                },
            )

        router = LLMRouter(self.config)
        orchestrator = AOCSOrchestrator(router, self.config)
        result = await orchestrator.analyze(
            problem=request.problem,
            domain=request.domain,
            risk=request.risk,
            fractal_depth=request.fractal_depth,
            context=request.context,
            max_sub_agents=request.max_sub_agents,
        )
        result.run_id = run_id
        result.run_dir = str(run_dir) if run_dir else None

        ended_at = _dt.datetime.now(_dt.timezone.utc).isoformat()
        if run_dir:
            self._write_json(run_dir / "trace.json", router.call_log)
            self._write_json(run_dir / "result.json", result.model_dump())
            self._write_text(run_dir / "summary.md", self._summary_markdown(result))
            self._write_json(
                run_dir / "status.json",
                {
                    "run_id": run_id,
                    "status": "error" if result.error else "completed",
                    "started_at": started_at,
                    "ended_at": ended_at,
                    "error": result.error,
                    "verdict": result.verdict,
                    "confidence": result.confidence,
                    "total_llm_calls": result.total_llm_calls,
                },
            )

        return result

    @staticmethod
    def _new_run_id(problem: str) -> str:
        ts = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        digest = hashlib.sha256(problem.encode()).hexdigest()[:8]
        return f"{ts}-{digest}"

    @staticmethod
    def _write_json(path: Path, data) -> None:
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    @staticmethod
    def _write_text(path: Path, data: str) -> None:
        path.write_text(data, encoding="utf-8")

    @staticmethod
    def _summary_markdown(result: AnalysisResult) -> str:
        lines = [
            f"# AOCS Run {result.run_id}",
            "",
            f"- Verdict: {result.verdict}",
            f"- Confidence: {result.confidence}",
            f"- Route: {result.route_taken}",
            f"- Problem type: {result.problem_type}",
            f"- LLM calls: {result.total_llm_calls}",
            "",
            "## Root Problem",
            result.root_problem or "(none)",
            "",
            "## Recommendation",
        ]
        lines.extend(f"- {item}" for item in result.recommendations)
        if result.error:
            lines.extend(["", "## Error", result.error])
        return "\n".join(lines) + "\n"
