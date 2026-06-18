"""Breakthrough — Future Backcasting (reverse engineer from 2035)."""

from aocs_mcp.router import LLMRouter
from aocs_mcp.pipeline.models import BreakthroughResult


BACKCAST_SYSTEM = """You are the AOCS-Omega Future Backcasting Agent.

Assume it is 2035. The problem has been solved and is now standard practice.
You are writing a retrospective article for a leading journal explaining how.

From that future vantage point:

1. Identify 5 key milestones that had to occur for the breakthrough.
2. For each milestone: what was attempted, what was learned, what was abandoned.
3. Find the "maybe that became yes" — the idea initially dismissed as impossible.
4. Identify where the frame shift happened.
5. Extract the present-day roadmap.

Output JSON:
```json
{{
    "future_scenario": "description of the solved world in 2035",
    "milestones": ["milestone1", "milestone2", "milestone3", "milestone4", "milestone5"],
    "maybe_that_became_yes": "the idea initially dismissed",
    "frame_shift": "where understanding fundamentally changed",
    "roadmap": "actionable steps for next 30/90/365 days"
}}
```"""


class FutureBackcast:
    """2035 retrospective simulation."""

    def __init__(self, router: LLMRouter):
        self.router = router

    async def run(self, problem: str) -> BreakthroughResult:
        data = await self.router.call_structured(
            "future-backcast", BACKCAST_SYSTEM, problem
        )

        # Pack milestones into cross_domain_sources for display
        milestones = data.get("milestones", [])
        sources = [f"Milestone {i+1}: {m}" for i, m in enumerate(milestones)]

        return BreakthroughResult(
            method="backcast",
            abstract_structure=data.get("future_scenario", ""),
            cross_domain_sources=sources,
            solution_principle=data.get("frame_shift", ""),
            adapted_proposal=data.get("roadmap", ""),
            details={
                "maybe_that_became_yes": data.get(
                    "maybe_that_became_yes",
                    "",
                ),
                "milestones": milestones,
            },
        )
