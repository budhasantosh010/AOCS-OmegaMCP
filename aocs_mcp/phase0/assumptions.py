"""3.3 Assumption Mapper — extract hidden assumptions (pure code)."""

from aocs_mcp.pipeline.models import Interpretation, Assumption


# Common assumptions per domain. When no domain is given, use open-domain
# assumptions so AOCS does not silently force a software worldview.
OPEN_DOMAIN_ASSUMPTIONS = [
    "The problem statement may be underspecified",
    "The stated goal may not be the root problem",
    "The relevant domain must be inferred from evidence, not assumed",
    "Available evidence may be incomplete, stale, or misleading",
    "The correct verification method depends on the inferred domain",
    "Multiple disciplines may be needed to evaluate the problem",
    "Safety, ethical, legal, or real-world constraints may apply",
    "The answer may require external validation before action",
]


DOMAIN_ASSUMPTIONS = {
    "software": [
        "The development environment matches production",
        "Third-party APIs are reliable and available",
        "Network latency is within normal bounds",
        "Documentation is accurate and up-to-date",
        "Test coverage is adequate for the change",
        "The bug is reproducible",
        "Logging is comprehensive enough to trace the issue",
        "Configuration files are in the expected format",
        "Dependencies are correctly versioned",
        "The team understands the affected system",
    ],
}


class AssumptionMapper:
    """Extracts hidden assumptions from each interpretation."""

    def extract(
        self,
        interpretations: list[Interpretation],
        domain: str | None = None,
        problem: str = "",
    ) -> list[Assumption]:
        assumptions: list[Assumption] = []

        # Domain-level assumptions
        domain_defaults = DOMAIN_ASSUMPTIONS.get(domain or "", OPEN_DOMAIN_ASSUMPTIONS)
        for stmt in domain_defaults:
            assumptions.append(Assumption(
                statement=stmt,
                certainty=0.7,
                provenance="LLM-Hypothesized",
            ))

        # Interpretation-specific assumptions
        for interp in interpretations:
            assumptions.append(Assumption(
                statement=f"'{interp.label}' assumes the root cause is: {interp.root_cause}",
                certainty=0.5,
                provenance="LLM-Hypothesized",
            ))
            assumptions.append(Assumption(
                statement=f"The {interp.lens} lens is the correct disciplinary view",
                certainty=0.4,
                provenance="LLM-Hypothesized",
            ))

        return assumptions[:15]  # cap at 15
