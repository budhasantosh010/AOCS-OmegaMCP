"""Classifier — determine Type 1/2/3 + risk level + fractal depth."""

from aocs_mcp.pipeline.models import Classification, Phase0Result


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
