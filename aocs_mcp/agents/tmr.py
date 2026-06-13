"""TMR — Triple Modular Redundancy (3× parallel LLM calls)."""

import asyncio

from aocs_mcp.router import LLMRouter
from aocs_mcp.pipeline.models import TMROutput


TMR_SYSTEM = """You are the AOCS-Omega TMR solver.
Solve this problem using a completely independent method.
Do NOT use any approach that has been used before.

Problem: {problem}
Exclude this approach: {exclude}

Output your solution."""


class TMR:
    """Triple Modular Redundancy — solve 3 independent ways, compare."""

    def __init__(self, router: LLMRouter):
        self.router = router

    async def run(self, problem: str, exclude_approach: str = "") -> TMROutput:
        # Launch 3 independent solutions in parallel
        methods = ["deductive logic", "analogical reasoning", "first principles"]
        tasks = []

        for method in methods:
            system = TMR_SYSTEM.format(problem=problem, exclude=exclude_approach or method)
            tasks.append(self.router.call("tmr", system, f"Method: {method}"))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        outputs = []
        for i, r in enumerate(results):
            if isinstance(r, Exception):
                outputs.append(f"[Method {methods[i]} failed: {r}]")
            else:
                outputs.append(str(r))

        # Check consensus — heuristic: if outputs are similar length, likely agree
        from collections import Counter
        lengths = [len(o) for o in outputs]
        avg = sum(lengths) / max(len(lengths), 1)
        disagreements = []
        for i, l in enumerate(lengths):
            if abs(l - avg) > avg * 0.5:
                disagreements.append(f"Method {methods[i]} diverges significantly")

        consensus = len(disagreements) == 0

        return TMROutput(
            method_a=outputs[0][:2000] if len(outputs) > 0 else "",
            method_b=outputs[1][:2000] if len(outputs) > 1 else "",
            method_c=outputs[2][:2000] if len(outputs) > 2 else "",
            consensus=consensus,
            disagreements=disagreements,
        )
