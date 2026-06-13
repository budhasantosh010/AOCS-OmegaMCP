"""Prover — deterministic formal verification (pure code)."""

from aocs_mcp.router import LLMRouter
from aocs_mcp.pipeline.models import ProverOutput


PROVER_SYSTEM = """You are the AOCS-Omega Deterministic Prover.
Convert the following reasoning into formal claims and attempt to prove each one.

For each claim, state:
1. The claim
2. Is it provable with available information? (yes/no)
3. Evidence or reasoning for your determination

Output JSON:
```json
{{"claims": [
    {{"statement": "claim text", "proved": true, "evidence": "why it is or isn't provable"}}
]}}
```"""


class Prover:
    """Deterministic Prover — attempts to formalize and prove claims."""

    def __init__(self, router: LLMRouter):
        self.router = router

    async def prove(self, reasoning: str) -> ProverOutput:
        data = await self.router.call_structured("classifier", PROVER_SYSTEM, reasoning)

        claims = []
        proved = []
        unprovable = []

        for c in data.get("claims", []):
            if isinstance(c, dict):
                stmt = c.get("statement", "")
                is_proved = c.get("proved", False)
                claims.append(stmt)
                if is_proved:
                    proved.append(True)
                else:
                    proved.append(False)
                    unprovable.append(stmt)

        return ProverOutput(claims=claims, proved=proved, unprovable=unprovable)
