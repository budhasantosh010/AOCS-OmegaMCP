"""Deception Detector — rhetorical manipulation scanner (1 LLM call)."""

from aocs_mcp.router import LLMRouter


DECEPTION_SYSTEM = """You are the AOCS-Omega Deception Detector.
Scan all arguments for rhetorical manipulation:

- Emotional appeals replacing evidence
- Cherry-picking data
- Inflated or exaggerated claims
- Information hiding / strategic omissions
- Straw man arguments
- False dichotomies
- Appeal to authority without substance

Flag each instance with the exact text and the manipulation type.

Output JSON:
```json
{{"flags": [
    {{"text": "exact text", "type": "manipulation type", "severity": "high/medium/low"}}
]}}
```"""


class DeceptionDetector:
    """Scans arguments for rhetorical manipulation."""

    def __init__(self, router: LLMRouter):
        self.router = router

    async def scan(
        self,
        specialist: str,
        red_team: str,
        contrarian: str,
    ) -> list[str]:
        user_prompt = (
            f"=== Specialist ===\n{specialist[:2000]}\n\n"
            f"=== Red Team ===\n{red_team[:2000]}\n\n"
            f"=== Contrarian ===\n{contrarian[:2000]}"
        )
        data = await self.router.call_structured(
            "deception-detector", DECEPTION_SYSTEM, user_prompt
        )
        flags = data.get("flags", [])

        result = []
        for f in flags:
            if isinstance(f, dict):
                result.append(f"[{f.get('severity', 'medium')}] {f.get('type', '?')}: {f.get('text', '')[:100]}")
            else:
                result.append(str(f))
        return result
