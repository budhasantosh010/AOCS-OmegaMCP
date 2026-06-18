"""Complete memory, graveyard, and learning behavior tests."""

import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from aocs_mcp.memory.blackboard import Blackboard
from aocs_mcp.memory.auditor import MemoryAuditor
from aocs_mcp.memory.graveyard import Graveyard
from aocs_mcp.pipeline.models import AnalysisResult, AuditResult, FlywheelEntry
from aocs_mcp.pipeline.orchestrator import AOCSOrchestrator
from aocs_mcp.learning.flywheel import Flywheel
from aocs_mcp.runtime import AOCSRunRequest, AOCSRuntime


def test_blackboard_preserves_complete_source_value():
    board = Blackboard()
    value = "evidence-" + ("x" * 1000)

    board.store("claim", value, provenance="Reality-Tested", confidence=0.9)

    assert board.get("claim")[0]["value"] == value


def test_blackboard_source_decay_reduces_stale_confidence():
    board = Blackboard()
    with patch("aocs_mcp.memory.blackboard.time.time", return_value=1000.0):
        board.store("claim", "stale claim", confidence=1.0)

    with patch("aocs_mcp.memory.blackboard.time.time", return_value=1000.0 + 24 * 3600):
        board.apply_decay(half_life_hours=24.0)

    assert board.get("claim")[0]["confidence"] == 0.5


def test_memory_auditor_distinguishes_assumption_lists_from_conflicting_claims():
    board = Blackboard()
    board.store("assumption", "The sensor is calibrated.")
    board.store("assumption", "The network is available.")
    board.store("claim:temperature", "20 C")
    board.store("claim:temperature", "80 C")

    audit = MemoryAuditor().audit(board)

    assert len(audit.contradictions) == 1
    assert "claim:temperature" in audit.contradictions[0]
    assert "assumption" not in audit.contradictions[0]


def test_memory_audit_downgrades_acceptance_when_conflicts_remain():
    confidence, verdict = AOCSOrchestrator._apply_memory_audit(
        98,
        "accept",
        AuditResult(
            contradictions=["Conflicting reality claims"],
            corrections=["Re-test the measurement"],
        ),
    )

    assert confidence == 94
    assert verdict == "flag_for_review"


def test_graveyard_only_resurrects_ideas_affected_by_changed_assumptions():
    graveyard = Graveyard()
    graveyard.bury(
        "Use superconducting storage",
        "Ambient-temperature superconductors are unavailable",
        assumptions_at_time="Requires ambient-temperature superconductors",
    )
    graveyard.bury(
        "Replace the sales team",
        "No evidence of sales failure",
        assumptions_at_time="Sales conversion is low",
    )

    candidates = graveyard.find_candidates(
        "New evidence shows ambient-temperature superconductors are now available"
    )

    assert [item["idea"] for item in candidates] == ["Use superconducting storage"]


def test_flywheel_records_error_classification_and_calibration_update():
    board = Blackboard()
    result = AnalysisResult(
        problem="Failed intervention",
        problem_type="type2",
        route_taken="type2",
        deep_test_passed=True,
        verdict="reject",
        confidence=70,
    )

    entries = Flywheel().capture(result.problem, result, board)

    assert entries[-1].error_type == "Random variance"
    assert "reduce" in entries[-1].calibration_update.lower()
    assert any(item["key"] == "model_update" for item in board.all())


async def _fake_complete_analyze(self, **kwargs):
    return AnalysisResult(
        problem=kwargs["problem"],
        blackboard_entries=[{"key": "claim", "value": "evidence"}],
        graveyard_entries=[{"idea": "old idea", "reason": "failed"}],
        learning_entries=[
            FlywheelEntry(
                heuristic="test reality",
                error_type=None,
                pattern="type1",
                success=True,
            )
        ],
        verdict="accept",
    )


def test_runtime_persists_blackboard_graveyard_and_learning_artifacts():
    with tempfile.TemporaryDirectory() as tmp:
        with patch.object(AOCSOrchestrator, "analyze", _fake_complete_analyze):
            result = asyncio.run(
                AOCSRuntime(output_root=tmp).run(AOCSRunRequest(problem="test"))
            )

        run_dir = Path(result.run_dir)
        assert json.loads((run_dir / "blackboard.json").read_text()) == result.blackboard_entries
        assert json.loads((run_dir / "graveyard.json").read_text()) == result.graveyard_entries
        learning = json.loads((run_dir / "learning.json").read_text())
        assert learning[0]["heuristic"] == "test reality"


if __name__ == "__main__":
    test_blackboard_preserves_complete_source_value()
    test_blackboard_source_decay_reduces_stale_confidence()
    test_graveyard_only_resurrects_ideas_affected_by_changed_assumptions()
    test_runtime_persists_blackboard_graveyard_and_learning_artifacts()
    print("memory completion tests passed")
