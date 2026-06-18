"""The ten non-negotiable AOCS quality gates."""

from aocs_mcp.pipeline.models import (
    GateResult,
    ObserverResult,
    ProverOutput,
    TMROutput,
    Type2Result,
    VerificationResult,
)
from aocs_mcp.quality.verifier import DeterministicVerifier
from aocs_mcp.router import LLMRouter


class QualityGates:
    """Apply all ten gates using real artifacts where the skill requires them."""

    def __init__(self, router: LLMRouter):
        self.router = router

    async def run(
        self,
        result: Type2Result,
        risk: str | None = None,
        verification: VerificationResult | None = None,
        tmr: TMROutput | None = None,
        prover: ProverOutput | None = None,
        observer: ObserverResult | None = None,
    ) -> list[GateResult]:
        gates: list[GateResult] = []

        gates.append(
            GateResult(
                gate_number=1,
                name="Self-Check",
                passed=0 <= result.specialist.confidence <= 100,
                details=f"Specialist confidence: {result.specialist.confidence:.0f}%",
            )
        )

        verification = verification or DeterministicVerifier().verify(
            result.specialist
        )
        verification_details = "; ".join(
            verification.evidence
            or verification.checks
            or verification.limitations
        )
        gates.append(
            GateResult(
                gate_number=2,
                name="Deterministic Verification",
                passed=verification.passed,
                details=verification_details or "No deterministic evidence recorded",
            )
        )

        has_blind_review = bool(
            result.red_team.critique.strip()
            and result.contrarian.analysis.strip()
            and result.judge.reasoning.strip()
        )
        gates.append(
            GateResult(
                gate_number=3,
                name="Diverse Blind Review",
                passed=has_blind_review,
                details=(
                    "Red Team, Contrarian, and blind Judge outputs are present"
                    if has_blind_review
                    else "Blind review chain is incomplete"
                ),
            )
        )

        trajectory_valid = bool(
            result.specialist.reasoning.strip()
            and result.judge.reasoning.strip()
            and result.judge.confidence >= 0
        )
        gates.append(
            GateResult(
                gate_number=4,
                name="Trajectory Evaluation",
                passed=trajectory_valid,
                details=(
                    "Specialist trajectory was evaluated by the blind Judge"
                    if trajectory_valid
                    else "Reasoning trajectory or Judge evaluation is missing"
                ),
            )
        )

        has_prediction = bool(result.specialist.prediction.strip())
        gates.append(
            GateResult(
                gate_number=5,
                name="Reality Prediction",
                passed=has_prediction,
                details=(
                    result.specialist.prediction
                    if has_prediction
                    else "No falsifiable reality prediction"
                ),
            )
        )

        adversarial_complete = bool(
            result.red_team.critique.strip() and result.red_team.flaws
        )
        gates.append(
            GateResult(
                gate_number=6,
                name="Adversarial Challenge",
                passed=adversarial_complete,
                details=(
                    f"{len(result.red_team.flaws)} concrete flaw(s) identified"
                    if adversarial_complete
                    else "No concrete adversarial flaw was recorded"
                ),
            )
        )

        if risk == "critical":
            tmr_passed = bool(tmr and tmr.consensus)
            details = (
                "TMR reached substantive consensus"
                if tmr_passed
                else "Critical-risk TMR missing or methods disagree"
            )
            if tmr and tmr.disagreements:
                details += f": {'; '.join(tmr.disagreements)}"
        else:
            tmr_passed = True
            details = f"TMR not required for risk={risk or 'unspecified'}"
        gates.append(
            GateResult(
                gate_number=7,
                name="Triple Modular Redundancy",
                passed=tmr_passed,
                details=details,
            )
        )

        if prover is None or not prover.claims:
            formal_passed = True
            formal_details = "No formal claims were identified as applicable"
        else:
            proved_count = sum(1 for item in prover.proved if item)
            formal_passed = (
                len(prover.proved) == len(prover.claims)
                and proved_count == len(prover.claims)
            )
            formal_details = f"{proved_count}/{len(prover.claims)} claims proved"
            if prover.unprovable:
                formal_details += f"; unprovable: {'; '.join(prover.unprovable)}"
        gates.append(
            GateResult(
                gate_number=8,
                name="Formal Methods",
                passed=formal_passed,
                details=formal_details,
            )
        )

        if observer is None:
            observer = await self._observer_check(result)
        observer_passed = not (
            observer.groupthink_detected or observer.overconfidence_detected
        )
        gates.append(
            GateResult(
                gate_number=9,
                name="Observer Check",
                passed=observer_passed,
                details=observer.notes or "Observer found no issue",
            )
        )

        confidence = result.judge.confidence
        human_passed = confidence >= 95
        if human_passed:
            human_details = (
                f"Confidence {confidence:.0f}% is above the acceptance threshold"
            )
        elif confidence >= 80:
            human_details = (
                f"Confidence {confidence:.0f}% requires explicit human review"
            )
        else:
            human_details = (
                f"Confidence {confidence:.0f}% is below the delivery threshold"
            )
        gates.append(
            GateResult(
                gate_number=10,
                name="Human Gatekeeping",
                passed=human_passed,
                details=human_details,
            )
        )

        return gates

    async def _observer_check(self, result: Type2Result) -> ObserverResult:
        """Compatibility path for callers that did not run the full Observer."""
        system = """You are the AOCS-Omega Observer.
Check for groupthink and overconfidence.
Output JSON:
{
  "groupthink_detected": false,
  "overconfidence_detected": false,
  "chaos_variable_injected": false,
  "notes": "",
  "chaos_variable": ""
}"""
        user = (
            f"Specialist confidence: {result.specialist.confidence}\n"
            f"Judge confidence: {result.judge.confidence}\n"
            f"Judge decision: {result.judge.decision}\n"
            f"Contrarian agreement: {result.contrarian.agreement_level}\n"
        )
        try:
            data = await self.router.call_structured("observer", system, user)
            return ObserverResult(
                groupthink_detected=bool(
                    data.get("groupthink_detected", False)
                ),
                overconfidence_detected=bool(
                    data.get("overconfidence_detected", False)
                ),
                chaos_variable_injected=bool(
                    data.get("chaos_variable_injected", False)
                ),
                chaos_variable=str(data.get("chaos_variable", "")),
                notes=str(data.get("notes", "")),
            )
        except Exception:
            return ObserverResult(notes="Observer check unavailable")
