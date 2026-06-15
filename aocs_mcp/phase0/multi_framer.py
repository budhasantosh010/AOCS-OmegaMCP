"""3.2 Multi-Framer — generate 3-5 interpretations (LLM call)."""

from aocs_mcp.router import LLMRouter
from aocs_mcp.pipeline.models import Interpretation


FRAMER_PROMPT = """You are the AOCS-Omega Multi-Framer.
Generate {num} genuinely different interpretations of the given problem.
Each interpretation MUST change the root cause, scale, or disciplinary lens.

Consider these lenses: {lenses}

If no domain is explicitly provided, infer the domain from the problem itself.
Do not assume software. Adapt expertise, verification tools, assumptions, and
failure modes to the inferred domain.

For each interpretation, output JSON:
```json
{{"interpretations": [
    {{"label": "short label", "root_cause": "the assumed root cause", "lens": "which lens", "rationale": "why this could be true"}}
]}}
```"""


LENSES = [
    "Domain inference / disciplinary context",
    "First-principles mechanism",
    "Evidence / empirical reality",
    "Systems / infrastructure",
    "Human workflow / incentives",
    "Data / measurement / uncertainty",
    "Safety / ethics / risk",
    "Unknown frontier / discovery",
]


class MultiFramer:
    """Generates 3-5 diverse interpretations of the problem."""

    def __init__(self, router: LLMRouter):
        self.router = router

    async def generate(self, problem: str, domain: str | None = None) -> list[Interpretation]:
        domain_label = domain or "infer from problem; do not assume software"
        user_prompt = f"Problem: {problem}\nDomain: {domain_label}\nLenses: {', '.join(LENSES)}"
        system = FRAMER_PROMPT.format(num=5, lenses=", ".join(LENSES))

        data = await self.router.call_structured("multi-framer", system, user_prompt)
        raw = data.get("interpretations", [])
        return [Interpretation(**item) for item in raw[:5]]
