"""Type 1 specialist for known, directly verifiable systems."""

from aocs_mcp.pipeline.models import Assumption, SpecialistOutput
from aocs_mcp.router import LLMRouter


TYPE1_SPECIALIST_SYSTEM = """You are the AOCS-Omega Type 1 Specialist.
Solve a problem in a known system using its established rules and constraints.

Apply these five steps in this exact order:
1. Question every requirement and verify the framing.
2. Cut unnecessary requirements, steps, or components.
3. Simplify the remaining solution.
4. Speed up the verified path without reducing quality.
5. Automate only after the first four steps are complete.

Produce a concrete solution, step-by-step reasoning, a falsifiable prediction,
explicit assumptions, and a calibrated confidence score from 0 to 100.

Output JSON:
{
  "proposal": "",
  "reasoning": "",
  "prediction": "",
  "assumptions": [],
  "confidence": 0
}"""


class Type1Specialist:
    def __init__(self, router: LLMRouter):
        self.router = router

    async def run(
        self,
        problem: str,
        root_problem: str,
        assumptions: list[Assumption],
    ) -> SpecialistOutput:
        assumptions_text = "\n".join(
            f"- {item.statement} (certainty: {item.certainty})"
            for item in assumptions
        )
        data = await self.router.call_structured(
            "type1-specialist",
            TYPE1_SPECIALIST_SYSTEM,
            (
                f"Problem:\n{problem}\n\n"
                f"Root problem:\n{root_problem}\n\n"
                f"Known assumptions:\n{assumptions_text}"
            ),
        )
        return SpecialistOutput(
            proposal=str(data.get("proposal", "")),
            reasoning=str(data.get("reasoning", "")),
            prediction=str(data.get("prediction", "")),
            assumptions=[
                str(item) for item in data.get("assumptions", [])
            ],
            confidence=max(
                0.0,
                min(100.0, float(data.get("confidence", 50))),
            ),
        )
