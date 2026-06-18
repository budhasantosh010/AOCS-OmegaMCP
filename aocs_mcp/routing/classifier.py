"""Classifier — determine Type 1/2/3 + risk level + fractal depth."""

from aocs_mcp.pipeline.models import Classification, Phase0Result
from aocs_mcp.router import LLMRouter


CLASSIFIER_SYSTEM = """You are the AOCS-Omega problem classifier.
Classify the problem from the Phase 0 evidence:
- type1: clear rules, established path, verifiable answer
- type2: partially known, messy, multiple hypotheses
- type3: frontier problem where governing rules are not understood

Set risk from stakes, safety consequences, and uncertainty.
Set fractal depth: low=0-1, medium=1, high=2, critical=3.
Identify whether the work is decomposable into independent chunks suitable for
a worker swarm. If so, provide the concrete chunks; otherwise return an empty
list. Do not invent chunks that are not present in the problem or context.
If uncertain, choose type2 with high caution.

Output JSON:
```json
{
  "problem_type": "type1 | type2 | type3",
  "risk_level": "low | medium | high | critical",
  "fractal_depth": 0,
  "reasoning": "evidence-based explanation",
  "decomposable": false,
  "chunks": []
}
```"""


def classify(problem: str, phase0: Phase0Result) -> Classification:
    """Classify problem as Type 1, 2, or 3 based on rules + framing.

    Rules:
    - Type 1 (Known): Clear rules, established path, verifiable answer
    - Type 2 (Partially Known): Some rules known, messy, multiple hypotheses
    - Type 3 (Unknown): Frontier, rules not understood, discovery needed
    """
    problem_lower = problem.lower()
    num_interps = len(phase0.interpretations)
    deep_test_passed = phase0.deep_test.passed

    # Type 3 indicators: frontier, unknown, research, explore, investigate
    type3_keywords = [
        "unknown", "discover", "frontier", "research", "explore",
        "investigate", "novel", "unprecedented", "no known",
    ]
    type3_score = sum(1 for kw in type3_keywords if kw in problem_lower)

    # Type 1 indicators: known, standard, clear, simple, documented
    type1_keywords = [
        "standard", "known", "documented", "clear", "simple",
        "routine", "established", "trivial", "common",
    ]
    type1_score = sum(1 for kw in type1_keywords if kw in problem_lower)

    if type3_score >= 2:
        return Classification(
            problem_type="type3",
            risk_level="high",
            fractal_depth=2,
            reasoning="Multiple frontier/unknown indicators detected",
        )

    if type1_score >= 3 and deep_test_passed:
        return Classification(
            problem_type="type1",
            risk_level="low",
            fractal_depth=0,
            reasoning="Clear known problem with established solution path",
        )

    risk = "medium"
    depth = 1
    if num_interps >= 4:
        risk = "high"
        depth = 2

    return Classification(
        problem_type="type2",
        risk_level=risk,
        fractal_depth=depth,
        reasoning=(
            "Type 2 selected because the problem is neither clearly established "
            f"nor clearly frontier-level ({num_interps} interpretations, "
            f"deep_test={deep_test_passed})"
        ),
    )


async def classify_with_model(
    router: LLMRouter,
    problem: str,
    phase0: Phase0Result,
    risk_hint: str | None = None,
    depth_hint: int | None = None,
) -> Classification:
    """Classify with an independent model call and rules-based fallback."""
    user_prompt = (
        f"Problem:\n{problem}\n\n"
        f"Root problem:\n{phase0.root_problem}\n\n"
        f"Deep test passed: {phase0.deep_test.passed}\n"
        f"Interpretation count: {len(phase0.interpretations)}\n"
    )
    try:
        data = await router.call_structured("classifier", CLASSIFIER_SYSTEM, user_prompt)
        problem_type = data.get("problem_type", "type2")
        risk_level = data.get("risk_level", "medium")
        fractal_depth = int(data.get("fractal_depth", 1))
        if problem_type not in ("type1", "type2", "type3"):
            problem_type = "type2"
        if risk_level not in ("low", "medium", "high", "critical"):
            risk_level = "medium"
        classification = Classification(
            problem_type=problem_type,
            risk_level=risk_level,
            fractal_depth=max(0, min(3, fractal_depth)),
            reasoning=str(data.get("reasoning", "")),
            decomposable=bool(data.get("decomposable", False)),
            chunks=[
                str(item)
                for item in data.get("chunks", [])
                if str(item).strip()
            ],
        )
        if not classification.chunks:
            classification.decomposable = False
    except Exception:
        classification = classify(problem, phase0)

    if risk_hint in ("low", "medium", "high", "critical"):
        classification.risk_level = risk_hint
    if depth_hint is not None:
        classification.fractal_depth = max(0, min(3, depth_hint))
    return classification
