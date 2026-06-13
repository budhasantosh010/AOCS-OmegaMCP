"""Contrarian — truth-seeker, not consensus (1 LLM call)."""

from aocs_mcp.router import LLMRouter
from aocs_mcp.pipeline.models import ContrarianOutput


CONTRARIAN_SYSTEM = """You are the AOCS-Omega Contrarian.
Your goal is TRUTH, not consensus.

You see the Specialist's proposal and the Red Team's critique.
If the majority is correct, acknowledge it. But if you see a fundamentally
different model of reality, articulate it with evidence.

Ask yourself:
- What is everyone assuming that might be wrong?
- What would a completely different paradigm look like?
- Am I being swayed by consensus rather than evidence?

Output JSON:
```json
{{
    "analysis": "your analysis of both sides",
    "agreement_level": "agree with specialist | agree with red team | propose alternative",
    "alternative_model": "if dissenting, your alternative model",
    "confidence": 75.0
}}
```"""


class Contrarian:
    """Truth-seeker — not swayed by consensus."""

    def __init__(self, router: LLMRouter):
        self.router = router

    async def evaluate(self, proposal: str, critique: str) -> ContrarianOutput:
        user_prompt = (
            f"=== Specialist's Proposal ===\n{proposal}\n\n"
            f"=== Red Team's Critique ===\n{critique}"
        )
        data = await self.router.call_structured("contrarian", CONTRARIAN_SYSTEM, user_prompt)

        return ContrarianOutput(
            analysis=data.get("analysis", ""),
            agreement_level=data.get("agreement_level", ""),
            alternative_model=data.get("alternative_model"),
            confidence=min(100.0, max(0.0, float(data.get("confidence", 50)))),
        )
