"""Deterministic structural verification for AOCS proposals."""

from aocs_mcp.pipeline.models import SpecialistOutput, VerificationResult


class DeterministicVerifier:
    """Check machine-verifiable output constraints without another model call."""

    def verify(self, specialist: SpecialistOutput) -> VerificationResult:
        checks: list[str] = []
        evidence: list[str] = []
        limitations: list[str] = []

        if specialist.proposal.strip():
            checks.append("proposal is non-empty")
            evidence.append(f"proposal_chars={len(specialist.proposal)}")
        else:
            limitations.append("proposal is empty")

        if specialist.reasoning.strip():
            checks.append("reasoning is present")
            evidence.append(f"reasoning_chars={len(specialist.reasoning)}")
        else:
            limitations.append("reasoning is missing")

        if specialist.prediction.strip():
            checks.append("reality prediction is present")
        else:
            limitations.append("reality prediction is missing")

        if specialist.assumptions:
            checks.append("assumptions are explicit")
            evidence.append(f"assumption_count={len(specialist.assumptions)}")
        else:
            limitations.append("assumptions are not explicit")

        if 0 <= specialist.confidence <= 100:
            checks.append("confidence is calibrated to 0-100")
        else:
            limitations.append("confidence is outside 0-100")

        return VerificationResult(
            passed=not limitations,
            checks=checks,
            evidence=evidence,
            limitations=limitations,
        )
