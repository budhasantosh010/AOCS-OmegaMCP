"""Triple Modular Redundancy with independent methods and comparison."""

import asyncio

from aocs_mcp.pipeline.models import TMROutput
from aocs_mcp.router import LLMRouter


TMR_SYSTEM = """You are an independent AOCS-Omega TMR solver.
Solve the problem without copying the supplied base solution.
Use the assigned method and state a concrete conclusion.
"""


TMR_JUDGE_SYSTEM = """You are the AOCS-Omega TMR comparator.
Compare the base solution and two independently generated solutions.
Judge substantive agreement, not writing style or answer length.

Output JSON:
```json
{
  "consensus": true,
  "disagreements": [],
  "reasoning": "comparison"
}
```"""


class TMR:
    """Generate two alternatives and compare all three substantive results."""

    def __init__(self, router: LLMRouter):
        self.router = router

    async def run(self, problem: str, base_solution: str = "") -> TMROutput:
        methods = ["independent deductive method", "independent first-principles method"]
        tasks = [
            self.router.call(
                "tmr",
                TMR_SYSTEM,
                f"Problem: {problem}\nMethod: {method}\nBase solution to avoid copying:\n{base_solution}",
            )
            for method in methods
        ]
        raw_results = await asyncio.gather(*tasks, return_exceptions=True)
        alternatives = [
            f"[Method failed: {value}]" if isinstance(value, Exception) else str(value)
            for value in raw_results
        ]

        comparison = await self.router.call_structured(
            "tmr-judge",
            TMR_JUDGE_SYSTEM,
            (
                f"Problem: {problem}\n\n"
                f"Solution A (base):\n{base_solution}\n\n"
                f"Solution B:\n{alternatives[0]}\n\n"
                f"Solution C:\n{alternatives[1]}"
            ),
        )

        return TMROutput(
            method_a=base_solution[:2000],
            method_b=alternatives[0][:2000],
            method_c=alternatives[1][:2000],
            consensus=bool(comparison.get("consensus", False)),
            disagreements=[str(item) for item in comparison.get("disagreements", [])],
        )
