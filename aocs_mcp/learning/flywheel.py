"""After-action heuristic capture, error classification, and calibration."""

from aocs_mcp.memory.blackboard import Blackboard
from aocs_mcp.pipeline.models import AnalysisResult, FlywheelEntry


class Flywheel:
    """Capture reusable learning and update future confidence calibration."""

    def capture(
        self,
        problem: str,
        result: AnalysisResult,
        blackboard: Blackboard,
    ) -> list[FlywheelEntry]:
        entries: list[FlywheelEntry] = []
        heuristic = self._extract_heuristic(result)
        calibration = (
            "Maintain calibration for this verified route."
            if result.verdict == "accept"
            else (
                "Reduce confidence for this route until new evidence resolves "
                "the failure."
            )
        )

        if heuristic:
            entries.append(
                FlywheelEntry(
                    heuristic=heuristic,
                    pattern=result.route_taken,
                    success=result.verdict == "accept",
                    calibration_update=calibration,
                )
            )

        if result.verdict in ("flag_for_review", "reject"):
            entries.append(
                FlywheelEntry(
                    heuristic=(
                        heuristic
                        or "No successful heuristic; preserve the failed pattern"
                    ),
                    error_type=self._classify_error(result),
                    pattern=result.route_taken,
                    success=False,
                    calibration_update=calibration,
                )
            )

        for entry in entries:
            blackboard.store(
                key="flywheel",
                value=entry.model_dump(),
                provenance="Reality-Tested",
                confidence=0.8,
            )
            blackboard.store(
                key="model_update",
                value={
                    "problem": problem,
                    "pattern": entry.pattern,
                    "error_type": entry.error_type,
                    "calibration_update": entry.calibration_update,
                },
                provenance="Reality-Tested",
                confidence=0.8,
            )
        return entries

    @staticmethod
    def _extract_heuristic(result: AnalysisResult) -> str | None:
        if result.problem_type == "type1" and result.verdict == "accept":
            return (
                "Known problems with clear rules use a direct Specialist and "
                "deterministic verification."
            )
        if result.problem_type == "type2":
            return (
                "Partially known problems use independent generation, "
                "adversarial challenge, and neutral judgment."
            )
        if result.problem_type == "type3":
            return (
                "Unknown problems use lenses, first principles, competing "
                "hypotheses, mutation, pruning, and simulation."
            )
        return None

    @staticmethod
    def _classify_error(result: AnalysisResult) -> str:
        if result.error:
            return "Execution error"
        if result.judge_verdict and result.judge_verdict.confidence < 50:
            return "Wrong assumption"
        if result.deception_flags:
            return "Flawed model"
        if not result.deep_test_passed:
            return "Wrong assumption"
        if result.shadow_check and result.shadow_check.divergence_detected:
            return "Execution error"
        return "Random variance"
