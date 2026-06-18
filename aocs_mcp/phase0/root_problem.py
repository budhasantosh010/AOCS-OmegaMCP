"""3.5 Root Problem Extraction — one-sentence root (LLM call)."""

from aocs_mcp.router import LLMRouter


ROOT_PROMPT = """You are the AOCS-Omega Root Problem Extractor.
Given the problem and its interpretations, identify the ONE sentence that captures the root problem.

Use Polya's structure: identify what is unknown, what is known, and what the conditions are.
This is the thing that, if fixed, makes most other problems vanish.

Output JSON:
```json
{{"root_problem": "the one-sentence root problem", "reasoning": "why this is the root"}}
```"""


class RootProblemExtractor:
    """Extracts the single root problem from all framing."""

    def __init__(self, router: LLMRouter):
        self.router = router

    async def extract(
        self,
        problem: str,
        framed: str,
        interpretations_summary: str,
    ) -> str:
        user_prompt = (
            f"Original problem:\n{problem}\n\n"
            f"Framed context:\n{framed}\n\n"
            f"Interpretations:\n{interpretations_summary}\n\n"
        )
        data = await self.router.call_structured("root-problem", ROOT_PROMPT, user_prompt)
        return data.get("root_problem", problem[:200])
