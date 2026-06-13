"""Phase 1 Scoring — score sub-problems on I/L/U/V (pure code)."""

from aocs_mcp.pipeline.models import ScoredProblem, Phase0Result, Phase1Result


WEIGHTS = {
    "impact": 0.35,
    "leverage": 0.25,
    "urgency": 0.20,
    "learning": 0.20,
}


ZONE_THRESHOLDS = [
    (9, "Critical", "Stop everything"),
    (7, "Big", "Execute"),
    (5, "Small", "Park"),
    (0, "Noise", "Discard"),
]


def _get_zone(score: float) -> str:
    for threshold, zone, _ in ZONE_THRESHOLDS:
        if score >= threshold:
            return zone
    return "Noise"


def score_interp_as_problem(
    interpretation: str,
    root_cause: str,
    index: int,
) -> ScoredProblem:
    """Convert a multi-framer interpretation into a scored sub-problem.

    In a real implementation, these scores would be LLM-derived.
    Here we use heuristic defaults based on position and lens cues.
    """
    name = f"sub-{index}: {interpretation[:60]}"

    # Heuristic defaults — the orchestrator can call LLM for more accuracy
    impact = 7
    leverage = 6
    urgency = 5
    learning = 6

    weighted = (
        impact * WEIGHTS["impact"]
        + leverage * WEIGHTS["leverage"]
        + urgency * WEIGHTS["urgency"]
        + learning * WEIGHTS["learning"]
    )

    return ScoredProblem(
        name=name,
        impact=impact,
        leverage=leverage,
        urgency=urgency,
        learning=learning,
        weighted_score=round(weighted, 2),
        zone=_get_zone(weighted),
    )


class Phase1Runner:
    """Scores sub-problems from Phase 0 interpretations."""

    def run(self, phase0: Phase0Result) -> Phase1Result:
        if not phase0.interpretations:
            return Phase1Result()

        scored = []
        for idx, interp in enumerate(phase0.interpretations):
            sp = score_interp_as_problem(interp.label, interp.root_cause, idx + 1)
            scored.append(sp)

        scored.sort(key=lambda x: x.weighted_score, reverse=True)
        top = scored[0] if scored else None

        return Phase1Result(sub_problems=scored, top_problem=top)
