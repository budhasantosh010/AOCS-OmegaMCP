"""Temporary solving-structure invention after repeated framework failure."""

from aocs_mcp.pipeline.models import BreakFrameworkResult
from aocs_mcp.router import LLMRouter


BREAK_FRAMEWORK_SYSTEM = """You are the AOCS-Omega Break-Framework Meta-Agent.
The standard solving structure failed or a paradigm alert fired.
Invent a temporary solving structure that changes phase order, introduces only
necessary temporary roles, or changes verification order.
Log the structure so a human vision owner can review it.

Output JSON:
{
  "temporary_structure": "",
  "reordered_phases": [],
  "temporary_agents": [],
  "verification_sequence": [],
  "proposal": ""
}"""


class BreakFrameworkAgent:
    def __init__(self, router: LLMRouter):
        self.router = router

    async def run(self, problem: str, reason: str) -> BreakFrameworkResult:
        data = await self.router.call_structured(
            "break-framework",
            BREAK_FRAMEWORK_SYSTEM,
            f"Problem:\n{problem}\n\nTrigger reason:\n{reason}",
        )
        return BreakFrameworkResult(
            triggered=True,
            reason=reason,
            temporary_structure=str(data.get("temporary_structure", "")),
            reordered_phases=[
                str(item) for item in data.get("reordered_phases", [])
            ],
            temporary_agents=[
                str(item) for item in data.get("temporary_agents", [])
            ],
            verification_sequence=[
                str(item) for item in data.get("verification_sequence", [])
            ],
            proposal=str(data.get("proposal", "")),
        )
