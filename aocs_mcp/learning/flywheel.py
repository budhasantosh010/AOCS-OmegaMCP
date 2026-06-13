"""Flywheel — After-action learning: heuristic capture + error classification."""

from aocs_mcp.pipeline.models import AnalysisResult, FlywheelEntry
from aocs_mcp.memory.blackboard import Blackboard


class Flywheel:
    """Captures heuristics and classifies errors for continuous improvement."""

    def capture(
        self,
        problem: str,
        result: AnalysisResult,
        blackboard: Blackboard,
    ) -> list[FlywheelEntry]:
        entries: list[FlywheelEntry] = []

        # Heuristic: what pattern worked?
        heuristic = self._extract_heuristic(result)
        if heuristic:
            entries.append(FlywheelEntry(
                heuristic=heuristic,
                pattern=result.route_taken,
                success=result.verdict == "accept",
            ))

        # Error classification (if verdict was flag_for_review or reject)
        if result.verdict in ("flag_for_review", "reject"):
            error_type = self._classify_error(result)
            if error_type:
                entries.append(FlywheelEntry(
                    heuristic=heuristic,
                    error_type=error_type,
                    pattern=result.route_taken,
                    success=False,
                ))

        # Store in blackboard
        for entry in entries:
            blackboard.store(
                key="flywheel",
                value=entry.model_dump_json(),
                provenance="Reality-Tested",
                confidence=0.8,
            )

        return entries

    @staticmethod
    def _extract_heuristic(result: AnalysisResult) -> str | None:
        """Extract a reusable thinking pattern."""
        if result.problem_type == "type1" and result.verdict == "accept":
            return "Known problems with clear rules → direct Specialist + Verifier is sufficient"
        elif result.problem_type == "type2":
            return "Partially-known problems → Triad (Spec + RT + Contrarian + Judge) catches blind spots"
        elif result.problem_type == "type3":
            return "Unknown problems → Lens + FP + Hypothesis generation enables discovery"
        return None

    @staticmethod
    def _classify_error(result: AnalysisResult) -> str | None:
        """Classify why a result was rejected."""
        if result.judge_verdict and result.judge_verdict.confidence < 50:
            return "Wrong assumption — low judge confidence indicates flawed model"
        if result.deception_flags:
            return "Flawed model — rhetorical manipulation detected in arguments"
        if not result.deep_test_passed:
            return "Wrong assumption — deep test failed, problem was incorrectly framed"
        if result.shadow_check and result.shadow_check.divergence_detected:
            return "Execution error — shadow orchestrator diverged from original routing"
        return None
