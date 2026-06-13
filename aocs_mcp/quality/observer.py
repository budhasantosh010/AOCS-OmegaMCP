"""Observer — groupthink + overconfidence detection (1 LLM call)."""

from aocs_mcp.router import LLMRouter
from aocs_mcp.pipeline.models import ObserverResult


OBSERVER_SYSTEM = """You are the AOCS-Omega Observer Agent.

Scan the reasoning for:
1. Groupthink: Did all sub-agents agree too quickly without deep debate?
2. Overconfidence: Is confidence high despite weak or few verified assumptions?

If you detect either issue, inject a Chaos Variable — a deliberate,
plausible counter-argument or alternative framing designed to force
re-evaluation from First Principles.

Output JSON:
```json
{{
    "groupthink_detected": false,
    "overconfidence_detected": false,
    "chaos_variable_injected": false,
    "notes": "analysis of the reasoning quality",
    "chaos_variable": "the injected counter-argument if applicable"
}}
```"""


class Observer:
    """Detects groupthink and overconfidence in the pipeline."""

    def __init__(self, router: LLMRouter):
        self.router = router

    async def check(
        self,
        specialist_confidence: float,
        judge_confidence: float,
        contrarian_agreement: str,
        deception_flags: list[str],
    ) -> ObserverResult:
        user_prompt = (
            f"Specialist confidence: {specialist_confidence:.0f}%\n"
            f"Judge confidence: {judge_confidence:.0f}%\n"
            f"Contrarian agreement: {contrarian_agreement}\n"
            f"Deception flags: {deception_flags}\n"
        )

        data = await self.router.call_structured("observer", OBSERVER_SYSTEM, user_prompt)

        return ObserverResult(
            groupthink_detected=data.get("groupthink_detected", False),
            overconfidence_detected=data.get("overconfidence_detected", False),
            chaos_variable_injected=data.get("chaos_variable_injected", False),
            notes=data.get("notes", ""),
        )
