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


def test_dashboard_derives_complete_protocol_outputs():
    steps = build_agent_steps(
        {
            "verification": {"passed": True, "checks": ["validated"]},
            "prover_result": {"claims": ["terminates"], "proved": [True]},
            "tmr_result": {"consensus": True, "method_b": "B", "method_c": "C"},
            "blindspot_check": {
                "missing_data": ["negative cases"],
                "falsification_conditions": ["counterexample"],
            },
            "fractal_result": {
                "executed_depth": 2,
                "survived": True,
                "challenges": [{"layer": "first-order", "red_team": "attack"}],
            },
            "kill_switch": {
                "fired": True,
                "failure_count": 2,
                "reframed_problem": "new root",
            },
            "goal_achievement": {
                "single_job": "close the gap",
                "closed_loop": ["A", "B", "feedback"],
            },
            "breakthroughs": [
                {"method": "analogical", "adapted_proposal": "import principle"}
            ],
            "break_framework": {
                "triggered": True,
                "temporary_structure": "evidence-first",
            },
            "swarm_result": {
                "workers": [{"worker_id": 1, "result": "chunk result"}],
                "peer_audits": ["peer audit"],
                "auditor_report": "independent audit",
                "synthesis": "merged result",
            },
            "paradigm_reframe": {
                "problem": "new frame",
                "classification": {"problem_type": "type2"},
            },
            "learning_entries": [
                {"heuristic": "test assumptions", "success": True}
            ],
        },
        [],
    )

    titles = {step["title"] for step in steps}
    assert {
        "Deterministic Verifier",
        "Formal Prover",
        "Triple Modular Redundancy",
        "Blindspot Hunter",
        "Fractal Verification",
        "Kill Switch",
        "Universal Goal Protocol",
        "Breakthrough Protocols",
        "Break-Framework",
        "Volume Swarm",
        "Paradigm Reframe",
        "Learning Flywheel",
    } <= titles


if __name__ == "__main__":
    test_dashboard_lists_and_loads_runs()
    test_dashboard_derives_agent_steps_from_result_without_trace()
    test_dashboard_derives_complete_protocol_outputs()
    print("dashboard tests passed")
