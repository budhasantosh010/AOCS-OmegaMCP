"""Tests for the local AOCS dashboard data layer."""

import json
import tempfile
from pathlib import Path

from aocs_mcp.dashboard import build_agent_steps, list_runs, load_run


def _write_json(path: Path, payload) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_dashboard_lists_and_loads_runs():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        run_dir = root / "run-1"
        run_dir.mkdir()
        _write_json(run_dir / "request.json", {"problem": "what is 2+2?"})
        _write_json(run_dir / "status.json", {"status": "completed", "started_at": "2026-06-15T00:00:00Z"})
        _write_json(
            run_dir / "result.json",
            {
                "problem": "what is 2+2?",
                "verdict": "accept",
                "confidence": 95.0,
                "route_taken": "direct-answer",
                "problem_type": "type1",
                "total_llm_calls": 1,
                "specialist_proposal": "2 + 2 = 4.",
            },
        )
        _write_json(
            run_dir / "trace.json",
            [{"call": 1, "role": "direct-answer", "status": "ok", "response_chars": 10}],
        )
        (run_dir / "summary.md").write_text("# Summary", encoding="utf-8")

        runs = list_runs(root)
        assert len(runs) == 1
        assert runs[0]["run_id"] == "run-1"
        assert runs[0]["problem"] == "what is 2+2?"

        loaded = load_run(root, "run-1")
        assert loaded["summary"] == "# Summary"
        assert loaded["agent_steps"][0]["title"] == "Direct Answer"
        assert loaded["agent_steps"][0]["answer"] == "2 + 2 = 4."


def test_dashboard_derives_agent_steps_from_result_without_trace():
    steps = build_agent_steps(
        {
            "root_problem": "Find the real root problem.",
            "specialist_proposal": "Proposed answer.",
            "red_team_critique": "Weak evidence.",
            "judge_verdict": {
                "decision": "flag_for_review",
                "confidence": 80,
                "reasoning": "Needs validation.",
            },
        },
        [],
    )

    titles = [step["title"] for step in steps]
    assert "Root Problem Extractor" in titles
    assert "Specialist" in titles
    assert "Red Team" in titles
    assert "Judge" in titles


if __name__ == "__main__":
    test_dashboard_lists_and_loads_runs()
    test_dashboard_derives_agent_steps_from_result_without_trace()
    print("dashboard tests passed")
