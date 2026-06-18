"""Breakthrough — Cross-Domain Analogical Mining (Elon's "toy car" method)."""

from aocs_mcp.router import LLMRouter
from aocs_mcp.pipeline.models import BreakthroughResult


ANALOGICAL_SYSTEM = """You are the AOCS-Omega Analogical Mining Agent (Elon's "Toy Car" method).

When stuck, import ideas from completely unrelated domains.

Protocol:
1. Identify the structural core: Reduce the problem to its most essential abstract structure.
2. Search across domains: Scan manufacturing, biology, music, sports, nature, cooking, children's toys, etc.
3. Extract the solution principle: What made it work in the other domain?
4. Transplant and adapt: Propose applying it here.
5. Define a concrete feasibility test. Reject the analogy only if that test
   demonstrates failure, not because the approach is unconventional.

Output JSON:
```json
{{
    "abstract_structure": "the core abstract problem",
    "cross_domain_sources": [{{"domain": "biology", "analogy": "..."}}],
    "solution_principle": "the core mechanism from the analogy",
    "adapted_proposal": "how to apply it here",
    "feasibility_test": "simulation, prototype, or experiment"
}}
```"""


class AnalogicalMining:
    """Cross-domain analogical reasoning — Elon's 'toy car' method."""

    def __init__(self, router: LLMRouter):
        self.router = router

    async def run(self, problem: str) -> BreakthroughResult:
        data = await self.router.call_structured(
            "analogical-mining", ANALOGICAL_SYSTEM, problem
        )

        sources = []
        for s in data.get("cross_domain_sources", []):
            if isinstance(s, dict):
                sources.append(f"[{s.get('domain', '?')}] {s.get('analogy', '')[:200]}")
            else:
                sources.append(str(s))

        return BreakthroughResult(
            method="analogical",
            abstract_structure=data.get("abstract_structure", ""),
            cross_domain_sources=sources,
            solution_principle=data.get("solution_principle", ""),
            adapted_proposal=data.get("adapted_proposal", ""),
            details={
                "feasibility_test": data.get("feasibility_test", ""),
            },
        )
