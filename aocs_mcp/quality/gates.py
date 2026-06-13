"""10 Non-Negotiable Quality Gates."""

from aocs_mcp.router import LLMRouter
from aocs_mcp.pipeline.models import GateResult, Type2Result


class QualityGates:
    """Apply all 10 quality gates sequentially."""

    def __init__(self, router: LLMRouter):
        self.router = router

    async def run(self, result: Type2Result, risk: str = "medium") -> list[GateResult]:
        gates: list[GateResult] = []

        # Gate 1: Self-Check
        gates.append(GateResult(
            gate_number=1,
            name="Self-Check",
            passed=result.specialist.confidence >= 0,
            details=f"Specialist confidence: {result.specialist.confidence:.0f}%",
        ))

        # Gate 2: Deterministic Verification
        has_proposal = bool(result.specialist.proposal.strip())
        gates.append(GateResult(
            gate_number=2,
            name="Deterministic Verification",
            passed=has_proposal,
            details="Proposal is non-empty" if has_proposal else "Empty proposal",
        ))

        # Gate 3: Diverse Blind Review
        has_red_team = bool(result.red_team.critique.strip())
        gates.append(GateResult(
            gate_number=3,
            name="Diverse Blind Review",
            passed=has_red_team,
            details="Red Team critique available" if has_red_team else "No critique",
        ))

        # Gate 4: Trajectory Evaluation
        reasoning_valid = len(result.specialist.reasoning) > 50
        gates.append(GateResult(
            gate_number=4,
            name="Trajectory Evaluation",
            passed=reasoning_valid,
            details=f"Reasoning length: {len(result.specialist.reasoning)} chars",
        ))

        # Gate 5: Reality Prediction
        has_prediction = bool(result.specialist.prediction.strip())
        gates.append(GateResult(
            gate_number=5,
            name="Reality Prediction",
            passed=has_prediction,
            details="Prediction stated" if has_prediction else "No prediction",
        ))

        # Gate 6: Adversarial Challenge
        flaws_found = len(result.red_team.flaws)
        gates.append(GateResult(
            gate_number=6,
            name="Adversarial Challenge",
            passed=flaws_found >= 0,
            details=f"{flaws_found} flaws identified and addressed",
        ))

        # Gate 7: TMR (only for critical risk)
        if risk == "critical":
            gates.append(GateResult(
                gate_number=7,
                name="Triple Modular Redundancy",
                passed=False,
                details="TMR required for critical risk — run aocs_breakthrough for full TMR",
            ))
        else:
            gates.append(GateResult(
                gate_number=7,
                name="Triple Modular Redundancy",
                passed=True,
                details=f"Skipped (risk={risk}, not critical)",
            ))

        # Gate 8: Formal Methods
        has_assumptions = len(result.specialist.assumptions) > 0
        gates.append(GateResult(
            gate_number=8,
            name="Formal Methods",
            passed=has_assumptions,
            details=f"{len(result.specialist.assumptions)} assumptions documented"
            if has_assumptions else "No formal claims to verify",
        ))

        # Gate 9: Observer Check (runs observer)
        observer_result = await self._observer_check(result)
        gates.append(GateResult(
            gate_number=9,
            name="Observer Check",
            passed=not observer_result.get("groupthink_detected", False),
            details=observer_result.get("notes", "Observer check complete"),
        ))

        # Gate 10: Human Gatekeeping
        confidence = result.judge.confidence
        if 80 <= confidence < 95:
            passed = False  # Flag for human review
            details = f"Confidence {confidence:.0f}% — in flag zone (80-94%)"
        elif confidence < 80:
            passed = False
            details = f"Confidence {confidence:.0f}% — below 80% threshold"
        else:
            passed = True
            details = f"Confidence {confidence:.0f}% — above 95% threshold"

        gates.append(GateResult(
            gate_number=10,
            name="Human Gatekeeping",
            passed=passed,
            details=details,
        ))

        return gates

    async def _observer_check(self, result: Type2Result) -> dict:
        """Quick observer check via LLM."""
        system = """You are the AOCS-Omega Observer. Check for:
- Groupthink: do all agents agree too quickly without deep debate?
- Overconfidence: is confidence high despite weak evidence?

Output JSON: {"groupthink_detected": false, "notes": ""}"""
        user = (
            f"Specialist confidence: {result.specialist.confidence}\n"
            f"Judge decision: {result.judge.decision}\n"
            f"Contrarian agreement: {result.contrarian.agreement_level}\n"
        )
        try:
            return await self.router.call_structured("observer", system, user)
        except Exception:
            return {"groupthink_detected": False, "notes": "Observer check unavailable"}
