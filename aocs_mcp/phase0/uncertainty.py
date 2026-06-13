"""3.4 Uncertainty Quantifier — score certainty 0.0-1.0 (pure code)."""

from aocs_mcp.pipeline.models import Assumption


def quantify(assumptions: list[Assumption]) -> list[Assumption]:
    """Assign certainty scores to each assumption.

    Rules:
    - Domain defaults from experience → 0.7
    - "assumes" statements (interpretation-dependent) → 0.4
    - "correct lens" statements → 0.3
    - "matches production" statements → 0.6
    - Anything with "correct" or "right" → 0.3
    - Short statements (< 40 chars) tend to be more certain → +0.1
    """
    for a in assumptions:
        statement = a.statement.lower()

        if "assumes" in statement:
            a.certainty = 0.4
        elif "lens" in statement:
            a.certainty = 0.3
        elif "matches production" in statement or "matches prod" in statement:
            a.certainty = 0.6
        elif "correct" in statement or "right" in statement:
            a.certainty = 0.3
        elif "available" in statement or "reliable" in statement:
            a.certainty = 0.65
        elif "documentation" in statement:
            a.certainty = 0.5
        elif "version" in statement:
            a.certainty = 0.55
        else:
            a.certainty = 0.5

        # Short statements tend to be more certain
        if len(a.statement) < 40:
            a.certainty = min(1.0, a.certainty + 0.1)

        # Clamp
        a.certainty = max(0.0, min(1.0, a.certainty))

    return assumptions
