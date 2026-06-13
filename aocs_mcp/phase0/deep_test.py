"""3.6 Deep Test — 4-question sanity check (LLM call)."""

from aocs_mcp.router import LLMRouter
from aocs_mcp.pipeline.models import DeepTestResult


DEEP_TEST_SYSTEM = """You are the AOCS-Omega Deep Test.
Answer these 4 questions about the problem framing. Be honest — if you cannot answer all 4, the problem needs reframing.

Output JSON:
```json
{{
    "question_1": "Is this a real limit, or just how things have always been done? ...",
    "question_2": "Who said this was the problem? Does it still hold today? ...",
    "question_3": "If I solved it fully, what work would no longer be needed? ...",
    "question_4": "What would prove this is the WRONG problem? ...",
    "can_answer_all": true/false
}}
```"""


class DeepTest:
    """Runs 4-question deep test on the problem framing."""

    def __init__(self, router: LLMRouter):
        self.router = router

    async def run(self, root_problem: str, parsed: str) -> DeepTestResult:
        user_prompt = f"Root problem: {root_problem}\n\nContext:\n{parsed}"
        data = await self.router.call_structured("deep-test", DEEP_TEST_SYSTEM, user_prompt)

        return DeepTestResult(
            question_1=data.get("question_1", ""),
            question_2=data.get("question_2", ""),
            question_3=data.get("question_3", ""),
            question_4=data.get("question_4", ""),
            passed=data.get("can_answer_all", False),
        )
