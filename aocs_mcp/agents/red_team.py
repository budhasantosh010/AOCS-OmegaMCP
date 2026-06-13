"""Red Team — adversarial challenger (1 LLM call)."""

from aocs_mcp.router import LLMRouter
from aocs_mcp.pipeline.models import RedTeamOutput


RED_TEAM_SYSTEM = """You are the AOCS-Omega Red Team — an adversarial agent.
Your success is measured by the flaws you find.

You receive an anonymised proposal. Challenge EVERY assumption.
Propose 3-5 alternative hypotheses with different core assumptions.
Run extreme stress tests: "What if this assumption is false?"
Flag survivorship bias, missing data, and logical gaps.

Output JSON:
```json
{{
    "critique": "your full adversarial critique",
    "flaws": ["flaw1", "flaw2", "flaw3"],
    "risk_estimate": "high/medium/low — explanation",
    "alternatives": ["alt1", "alt2", "alt3"]
}}
```"""


class RedTeam:
    """Adversarial challenger — attacks every assumption."""

    def __init__(self, router: LLMRouter):
        self.router = router

    async def challenge(self, proposal: str) -> RedTeamOutput:
        data = await self.router.call_structured("red-team", RED_TEAM_SYSTEM, proposal)

        return RedTeamOutput(
            critique=data.get("critique", ""),
            flaws=data.get("flaws", []),
            risk_estimate=data.get("risk_estimate", "medium"),
        )
