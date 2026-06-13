"""Breakthrough — Higher-Dimension Reframing (escape the frame)."""

from aocs_mcp.router import LLMRouter
from aocs_mcp.pipeline.models import BreakthroughResult


REFRAME_SYSTEM = """You are the AOCS-Omega Higher-Dimension Reframer.

When standard approaches fail, step outside the current frame.

Protocol:
1. Expose the current dimension: Articulate the unwritten rules and hidden constraints.
2. Shift to higher dimension: Ask "What would a 5D being notice?"
   Ask "If all rules were suspended, what becomes possible?"
   Ask "Is the goal itself the problem?"
3. Generate the reframed problem statement from the higher dimension.
4. Propose how to attack the reframed problem.

Output JSON:
```json
{{
    "current_frame": "the unwritten rules and constraints",
    "higher_dimension_view": "what a higher-D observer would see",
    "reframed_problem": "the completely reframed problem",
    "adapted_proposal": "how to attack the reframed problem"
}}
```"""


class HigherDimension:
    """Step-outside-the-frame reframing."""

    def __init__(self, router: LLMRouter):
        self.router = router

    async def run(self, problem: str) -> BreakthroughResult:
        data = await self.router.call_structured(
            "higher-dimension", REFRAME_SYSTEM, problem
        )

        return BreakthroughResult(
            method="reframe",
            abstract_structure=data.get("current_frame", ""),
            cross_domain_sources=[],
            solution_principle=data.get("higher_dimension_view", ""),
            adapted_proposal=data.get("adapted_proposal", ""),
        )
