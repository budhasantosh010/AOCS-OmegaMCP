"""Mandatory blindspot hunting at major AOCS decision points."""

from aocs_mcp.pipeline.models import BlindspotResult
from aocs_mcp.router import LLMRouter


BLINDSPOT_SYSTEM = """You are the AOCS-Omega Blindspot Hunter.
Answer every mandatory question:
1. What perspectives are not being examined?
2. What data is missing or was never collected?
3. What would an outsider, skeptic, or competitor notice?
4. What evidence would falsify the conclusion?
5. What is the simplest overlooked explanation?

Output JSON:
{
  "missing_perspectives": [],
  "missing_data": [],
  "outsider_view": "",
  "falsification_conditions": [],
  "simplest_overlooked": "",
  "recommended_actions": []
}"""


class BlindspotHunter:
    def __init__(self, router: LLMRouter):
        self.router = router

    async def run(
        self,
        problem: str,
        framing: str,
        conclusion: str,
    ) -> BlindspotResult:
        data = await self.router.call_structured(
            "blindspot-hunter",
            BLINDSPOT_SYSTEM,
            (
                f"Problem:\n{problem}\n\n"
                f"Framing:\n{framing}\n\n"
                f"Current conclusion:\n{conclusion}"
            ),
        )
        return BlindspotResult(
            missing_perspectives=[
                str(item) for item in data.get("missing_perspectives", [])
            ],
            missing_data=[str(item) for item in data.get("missing_data", [])],
            outsider_view=str(data.get("outsider_view", "")),
            falsification_conditions=[
                str(item) for item in data.get("falsification_conditions", [])
            ],
            simplest_overlooked=str(data.get("simplest_overlooked", "")),
            recommended_actions=[
                str(item) for item in data.get("recommended_actions", [])
            ],
        )
