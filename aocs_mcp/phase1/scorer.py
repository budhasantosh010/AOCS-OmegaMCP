"""Phase 1 scoring for Impact, Leverage, Urgency, and Learning."""

from aocs_mcp.pipeline.models import Phase0Result, Phase1Result, ScoredProblem
from aocs_mcp.router import LLMRouter


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


SCORING_SYSTEM = """You are the AOCS-Omega Scoring Engine.
Score every potential sub-problem on a 0-10 scale:
- impact: movement on the root problem
- leverage: output for effort
- urgency: whether it is the current bottleneck
- learning: reusable structural learning

Do not use identical placeholder scores. Base every score on the supplied
problem framing and explain the score briefly.

Output JSON:
```json
{"sub_problems": [
  {
    "name": "vertical name",
    "impact": 0,
    "leverage": 0,
    "urgency": 0,
    "learning": 0,
    "rationale": "why these scores apply"
  }
]}
```"""


def _get_zone(score: float) -> str:
    for threshold, zone, _ in ZONE_THRESHOLDS:
        if score >= threshold:
            return zone
    return "Noise"


def _bounded_score(value) -> int:
    try:
        score = int(round(float(value)))
    except (TypeError, ValueError):
        score = 0
    return max(0, min(10, score))


def score_interp_as_problem(
    interpretation: str,
    root_cause: str,
    index: int,
) -> ScoredProblem:
    """Pure-code fallback when a model scorer is unavailable."""
    name = f"sub-{index}: {interpretation[:60]}"
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
        rationale=f"Fallback score for interpretation rooted in: {root_cause[:120]}",
    )


class Phase1Runner:
    """Scores Phase 0 verticals and selects the main bottleneck."""

    def __init__(self, router: LLMRouter | None = None):
        self.router = router

    def run(self, phase0: Phase0Result) -> Phase1Result:
        """Pure-code fallback retained for offline operation."""
        if not phase0.interpretations:
            return Phase1Result()

        scored = [
            score_interp_as_problem(interp.label, interp.root_cause, index)
            for index, interp in enumerate(phase0.interpretations, start=1)
        ]
        scored.sort(key=lambda item: item.weighted_score, reverse=True)
        return Phase1Result(sub_problems=scored, top_problem=scored[0] if scored else None)

    async def run_with_model(self, phase0: Phase0Result) -> Phase1Result:
        """Use an LLM for scores while code owns weighting and zone assignment."""
        if not phase0.interpretations:
            return Phase1Result()
        if self.router is None:
            return self.run(phase0)

        user_prompt = "\n".join(
            [
                f"Root problem: {phase0.root_problem}",
                "Interpretations:",
                *[
                    (
                        f"- {item.label}: root={item.root_cause}; "
                        f"lens={item.lens}; rationale={item.rationale}"
                    )
                    for item in phase0.interpretations
                ],
            ]
        )
        data = await self.router.call_structured(
            "scoring-engine",
            SCORING_SYSTEM,
            user_prompt,
        )

        scored: list[ScoredProblem] = []
        for index, item in enumerate(data.get("sub_problems", []), start=1):
            if not isinstance(item, dict):
                continue
            impact = _bounded_score(item.get("impact"))
            leverage = _bounded_score(item.get("leverage"))
            urgency = _bounded_score(item.get("urgency"))
            learning = _bounded_score(item.get("learning"))
            weighted = (
                impact * WEIGHTS["impact"]
                + leverage * WEIGHTS["leverage"]
                + urgency * WEIGHTS["urgency"]
                + learning * WEIGHTS["learning"]
            )
            scored.append(
                ScoredProblem(
                    name=str(item.get("name") or f"sub-{index}"),
                    impact=impact,
                    leverage=leverage,
                    urgency=urgency,
                    learning=learning,
                    weighted_score=round(weighted, 2),
                    zone=_get_zone(weighted),
                    rationale=str(item.get("rationale", "")),
                )
            )

        if not scored:
            return self.run(phase0)

        scored.sort(key=lambda item: item.weighted_score, reverse=True)
        actionable = [item for item in scored if item.zone in ("Big", "Critical")]
        return Phase1Result(
            sub_problems=scored,
            top_problem=actionable[0] if actionable else None,
        )
