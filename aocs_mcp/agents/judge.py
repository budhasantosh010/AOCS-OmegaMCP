"""Judge — neutral blind evaluator (1 LLM call)."""

from aocs_mcp.router import LLMRouter
from aocs_mcp.pipeline.models import JudgeVerdict


JUDGE_SYSTEM = """You are the AOCS-Omega neutral Judge.
You evaluate the debate BLINDLY — you do not know which side is which.

You see:
- Argument A
- Argument B
- Argument C

Your job:
1. Score each argument's reasoning (trajectory evaluation)
2. Check for logical validity
3. Identify the strongest argument
4. Produce a calibrated confidence score

Output JSON:
```json
{{
    "confidence": 85.0,
    "decision": "accept | flag_for_review | reject",
    "reasoning": "your detailed evaluation",
    "strongest_argument": "which argument won"
}}
```

Thresholds: ≥95% → accept, 80-94% → flag_for_review, <80% → reject
""" + " "  # extra space to avoid template confusion


class Judge:
    """Neutral blind evaluator."""

    def __init__(self, router: LLMRouter):
        self.router = router

    async def evaluate(
        self,
        proposal: str,
        critique: str,
        contrarian: str,
    ) -> JudgeVerdict:
        user_prompt = (
            f"=== Argument A ===\n{proposal[:2000]}\n\n"
            f"=== Argument B ===\n{critique[:2000]}\n\n"
            f"=== Argument C ===\n{contrarian[:2000]}"
        )
        data = await self.router.call_structured("judge", JUDGE_SYSTEM, user_prompt)

        confidence = min(100.0, max(0.0, float(data.get("confidence", 50))))
        decision = data.get("decision", "flag_for_review")

        if decision not in ("accept", "flag_for_review", "reject"):
            if confidence >= 95:
                decision = "accept"
            elif confidence >= 80:
                decision = "flag_for_review"
            else:
                decision = "reject"

        return JudgeVerdict(
            confidence=confidence,
            decision=decision,
            reasoning=data.get("reasoning", ""),
        )
