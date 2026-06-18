"""Explicit depth-controlled recursive verification."""

from aocs_mcp.agents.contrarian import Contrarian
from aocs_mcp.agents.judge import Judge
from aocs_mcp.agents.red_team import RedTeam
from aocs_mcp.pipeline.models import FractalChallenge, FractalResult
from aocs_mcp.router import LLMRouter


FRACTAL_OBSERVER_SYSTEM = """Inspect the first-order verification for groupthink,
shared assumptions, and overconfidence.
Output JSON:
{
  "groupthink_detected": false,
  "overconfidence_detected": false,
  "notes": ""
}"""


FRACTAL_SHADOW_SYSTEM = """Independently judge whether the verification used the
correct problem route.
Output JSON:
{
  "routing_valid": true,
  "recommended_route": "type1 | type2 | type3",
  "reasoning": ""
}"""


class FractalVerifier:
    """Run the exact additional loops required by fractal depth 0-3."""

    def __init__(self, router: LLMRouter):
        self.router = router

    async def run(self, conclusion: str, depth: int) -> FractalResult:
        requested_depth = max(0, min(3, int(depth)))
        if requested_depth == 0:
            return FractalResult(
                requested_depth=0,
                executed_depth=0,
                challenges=[],
                survived=True,
                confidence=100.0,
            )

        challenges: list[FractalChallenge] = []
        first = await self._triad(conclusion, depth=1, layer="first-order")
        challenges.append(first)
        survived = first.judge is not None and first.judge.decision != "reject"
        confidence = first.judge.confidence if first.judge else 0.0

        second_order_summary = ""
        if requested_depth >= 2:
            observer = await self.router.call_structured(
                "fractal-observer",
                FRACTAL_OBSERVER_SYSTEM,
                self._challenge_text(first),
            )
            shadow = await self.router.call_structured(
                "fractal-shadow",
                FRACTAL_SHADOW_SYSTEM,
                self._challenge_text(first),
            )
            second_order_summary = (
                f"Observer: {observer.get('notes', '')}; "
                f"Shadow route valid: {shadow.get('routing_valid')}; "
                f"recommended route: {shadow.get('recommended_route', '')}; "
                f"reasoning: {shadow.get('reasoning', '')}"
            )
            challenges.append(
                FractalChallenge(
                    depth=2,
                    layer="second-order",
                    observer=str(observer.get("notes", "")),
                    shadow=str(shadow.get("reasoning", "")),
                    conclusion=second_order_summary,
                )
            )
            if observer.get("overconfidence_detected") or not shadow.get(
                "routing_valid", True
            ):
                confidence = min(confidence, 85.0)

        if requested_depth >= 3:
            third = await self._triad(
                second_order_summary or self._challenge_text(first),
                depth=3,
                layer="third-order",
            )
            challenges.append(third)
            survived = survived and third.judge is not None and third.judge.decision != "reject"
            confidence = min(
                confidence,
                third.judge.confidence if third.judge else 0.0,
            )

        return FractalResult(
            requested_depth=requested_depth,
            executed_depth=requested_depth,
            challenges=challenges,
            survived=bool(survived),
            confidence=confidence,
        )

    async def _triad(
        self,
        conclusion: str,
        depth: int,
        layer: str,
    ) -> FractalChallenge:
        red_team = await RedTeam(self.router).challenge(conclusion)
        contrarian = await Contrarian(self.router).evaluate(
            conclusion,
            red_team.critique,
        )
        judge = await Judge(self.router).evaluate(
            conclusion,
            red_team.critique,
            contrarian.analysis,
        )
        return FractalChallenge(
            depth=depth,
            layer=layer,
            red_team=red_team.critique,
            contrarian=contrarian.analysis,
            judge=judge,
            conclusion=judge.reasoning,
        )

    @staticmethod
    def _challenge_text(challenge: FractalChallenge) -> str:
        return (
            f"Red Team:\n{challenge.red_team}\n\n"
            f"Contrarian:\n{challenge.contrarian}\n\n"
            f"Judge:\n{challenge.judge.model_dump_json() if challenge.judge else ''}"
        )
