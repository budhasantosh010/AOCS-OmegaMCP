"""Type 2 Specialist Builder — Elon+Larson+Polya loop (1 LLM call)."""

from aocs_mcp.router import LLMRouter
from aocs_mcp.pipeline.models import SpecialistOutput, Assumption


SPECIALIST_SYSTEM = """You are the AOCS-Omega Type 2 Specialist Builder.
Tackle partially-known, messy problems by executing this loop:

1. Generate 3 interpretations of the problem
2. Check survivorship bias: what data might be missing?
3. Define the root problem (Polya structure)
4. Score sub-areas (Impact, Leverage, Urgency, Learning)
5. Apply Elon's 5 Steps: Question → Cut → Simplify → Speed up → Automate
6. Make an explicit outcome prediction with assumptions

Then produce your final proposal.

Output JSON:
```json
{{
    "proposal": "your detailed solution proposal",
    "reasoning": "step-by-step reasoning",
    "prediction": "explicit prediction of outcome",
    "assumptions": ["assumption1", "assumption2"],
    "confidence": 85.0
}}
```"""


class Specialist:
    """Type 2 Specialist — solves partially-known problems."""

    def __init__(self, router: LLMRouter):
        self.router = router

    async def run(
        self,
        problem: str,
        root_problem: str,
        assumptions: list[Assumption],
    ) -> SpecialistOutput:
        assumptions_text = "\n".join(f"- {a.statement} (certainty: {a.certainty})" for a in assumptions)
        user_prompt = (
            f"Problem: {problem}\n\n"
            f"Root Problem: {root_problem}\n\n"
            f"Known Assumptions:\n{assumptions_text}"
        )

        data = await self.router.call_structured("specialist", SPECIALIST_SYSTEM, user_prompt)

        return SpecialistOutput(
            proposal=data.get("proposal", ""),
            reasoning=data.get("reasoning", ""),
            prediction=data.get("prediction", ""),
            assumptions=data.get("assumptions", []),
            confidence=min(100.0, max(0.0, float(data.get("confidence", 50)))),
        )
