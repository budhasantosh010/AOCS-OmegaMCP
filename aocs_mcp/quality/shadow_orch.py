"""Shadow Orchestrator — independent re-classification + divergence check (1 LLM call)."""

from aocs_mcp.router import LLMRouter
from aocs_mcp.pipeline.models import Classification, ShadowResult
from aocs_mcp.routing.classifier import classify


SHADOW_SYSTEM = """You are the AOCS-Omega Shadow Orchestrator.
Independently re-classify this problem from scratch.
Do NOT look at the previous classification.

Consider the problem fresh. What type is it really?
What risk level? What fractal depth?

Output JSON:
```json
{{
    "problem_type": "type1 | type2 | type3",
    "risk_level": "low | medium | high | critical",
    "fractal_depth": 0,
    "reasoning": "your independent reasoning"
}}
```"""


class ShadowOrchestrator:
    """Independent re-classification — checks for divergence."""

    def __init__(self, router: LLMRouter):
        self.router = router

    async def check(
        self,
        problem: str,
        original: Classification,
    ) -> ShadowResult:
        # Get shadow classification (LLM-based, independent)
        try:
            data = await self.router.call_structured(
                "shadow-orchestrator", SHADOW_SYSTEM, problem
            )
            shadow_type = data.get("problem_type", "type2")
            shadow_risk = data.get("risk_level", "medium")
            shadow_depth = int(data.get("fractal_depth", 0))
            shadow_reasoning = data.get("reasoning", "")
        except Exception:
            # Fallback: rules-based classification
            shadow = classify(problem, None)  # type: ignore
            shadow_type = shadow.problem_type
            shadow_risk = shadow.risk_level
            shadow_depth = shadow.fractal_depth
            shadow_reasoning = "Fallback rules-based classification"

        shadow = Classification(
            problem_type=shadow_type,
            risk_level=shadow_risk,
            fractal_depth=shadow_depth,
            reasoning=shadow_reasoning,
        )

        # Check divergence
        divergence = (
            original.problem_type != shadow.problem_type
            or original.risk_level != shadow.risk_level
        )

        # Safe path: choose the more conservative
        risk_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        type_order = {"type1": 0, "type2": 1, "type3": 2}
        original_conservatism = (
            risk_order.get(original.risk_level, 0),
            type_order.get(original.problem_type, 1),
            original.fractal_depth,
        )
        shadow_conservatism = (
            risk_order.get(shadow.risk_level, 0),
            type_order.get(shadow.problem_type, 1),
            shadow.fractal_depth,
        )
        if original_conservatism >= shadow_conservatism:
            safe_path = f"Use original: {original.problem_type} (risk {original.risk_level})"
        else:
            safe_path = f"Use shadow: {shadow.problem_type} (risk {shadow.risk_level})"

        return ShadowResult(
            divergence_detected=divergence,
            original_classification=original,
            shadow_classification=shadow,
            safe_path=safe_path,
        )
