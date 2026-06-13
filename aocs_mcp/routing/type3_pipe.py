"""7.3 Type 3 Pipe — Discovery (Lens → FP → Hypothesis → Evolution)."""

from aocs_mcp.router import LLMRouter
from aocs_mcp.pipeline.models import Type3Result


LENS_AGENT_SYSTEM = """You are a {lens} expert analyzing a problem.
What would your expertise notice that others miss?
Provide structured observations about the problem.

Output as JSON:
```json
{{"observations": ["obs1", "obs2", "obs3"], "key_insight": "what your lens uniquely reveals"}}
```"""


FIRST_PRINCIPLES_SYSTEM = """You are the AOCS-Omega First Principles Thinker.
Strip away all existing solutions and assumptions. Rebuild from the most basic truths.
Ask: "What must be true regardless of current theories or implementations?"

Output JSON:
```json
{{"first_principles": ["fp1", "fp2", "fp3"], "core_truths": ["truth1", "truth2"]}}
```"""


HYPOTHESIS_SYSTEM = """You are the AOCS-Omega Hypothesis Generator.
Generate 3 competing models that could explain the unknown.
For each, state the model, what evidence would support it, and what would refute it.

Output JSON:
```json
{{"hypotheses": [
    {{"name": "Model A", "description": "...", "supporting_evidence": "...", "refuting_evidence": "..."}}
]}}
```"""


LENSES = [
    "Systems Architect",
    "Security Researcher",
    "Performance Engineer",
    "UX-Aware Developer",
    "Data Scientist",
]


class Type3Pipe:
    """Discovery pipe — for Type 3 (Unknown) problems."""

    def __init__(self, router: LLMRouter, max_lens: int = 3):
        self.router = router
        self.max_lens = max_lens

    async def run(self, domain: str, seed_question: str) -> Type3Result:
        # Step 1: Lens Agents — parallel observations
        lens_observations = []
        for lens in LENSES[: self.max_lens]:
            system = LENS_AGENT_SYSTEM.format(lens=lens)
            try:
                data = await self.router.call_structured(
                    "type3-lens", system, f"Domain: {domain}\nProblem: {seed_question}"
                )
                obs = data.get("observations", [])
                lens_observations.extend(obs)
            except Exception:
                lens_observations.append(f"[{lens}] unavailable")

        # Step 2: First Principles
        fp_data = await self.router.call_structured(
            "type3-first-principles",
            FIRST_PRINCIPLES_SYSTEM,
            f"Domain: {domain}\nProblem: {seed_question}\nObservations: {'; '.join(lens_observations)}",
        )
        first_principles = "\n".join(fp_data.get("first_principles", []))

        # Step 3: Hypothesis Generation
        hyp_data = await self.router.call_structured(
            "type3-hypothesis",
            HYPOTHESIS_SYSTEM,
            f"Domain: {domain}\nProblem: {seed_question}\nFirst Principles: {first_principles}",
        )
        hypotheses = [h.get("description", "") for h in hyp_data.get("hypotheses", [])]

        return Type3Result(
            lens_observations=lens_observations,
            first_principles=first_principles,
            hypotheses=hypotheses,
            survivors=hypotheses,
            weirdness_reserve=[],
            anomalies=[],
        )
