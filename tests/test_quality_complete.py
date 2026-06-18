"""Quality gates must use real protocol artifacts."""

import asyncio

from aocs_mcp.pipeline.models import (
    ContrarianOutput,
    JudgeVerdict,
    ObserverResult,
    ProverOutput,
    RedTeamOutput,
    SpecialistOutput,
    TMROutput,
    Type2Result,
    VerificationResult,
)
from aocs_mcp.quality.gates import QualityGates
from aocs_mcp.quality.shadow_orch import ShadowOrchestrator
from aocs_mcp.pipeline.models import Classification
from tests.fakes import ScriptedRouter


def _debate() -> Type2Result:
    return Type2Result(
        specialist=SpecialistOutput(
            proposal="Verified proposal",
            reasoning=(
                "Each reasoning step follows from explicit evidence, stated "
                "constraints, and a falsifiable causal prediction."
            ),
            prediction="The measured result will match the expected result.",
            assumptions=["Instrument is calibrated."],
            confidence=97,
        ),
        red_team=RedTeamOutput(
            critique="The proposal could fail if calibration drifts.",
            flaws=["Calibration drift"],
            risk_estimate="critical",
        ),
        contrarian=ContrarianOutput(
            analysis="The proposal is strongest if calibration is independently checked.",
            agreement_level="partial",
            confidence=90,
        ),
        judge=JudgeVerdict(
            confidence=97,
            decision="accept",
            reasoning="The evidence supports acceptance.",
        ),
    )


def test_quality_gates_use_actual_verification_tmr_prover_and_observer():
    gates = asyncio.run(
        QualityGates(ScriptedRouter({})).run(
            _debate(),
            risk="critical",
            verification=VerificationResult(
                passed=True,
                checks=["proposal executed against constraints"],
                evidence=["all checks passed"],
            ),
            tmr=TMROutput(consensus=True),
            prover=ProverOutput(
                claims=["The procedure terminates."],
                proved=[True],
            ),
            observer=ObserverResult(
                groupthink_detected=False,
                overconfidence_detected=False,
                notes="Independent disagreement was substantive.",
            ),
        )
    )

    by_number = {gate.gate_number: gate for gate in gates}
    assert by_number[2].passed
    assert "all checks passed" in by_number[2].details
    assert by_number[7].passed
    assert "consensus" in by_number[7].details.lower()
    assert by_number[8].passed
    assert "1/1" in by_number[8].details
    assert by_number[9].passed


def test_quality_gates_fail_critical_tmr_and_unproved_claims():
    gates = asyncio.run(
        QualityGates(ScriptedRouter({})).run(
            _debate(),
            risk="critical",
            verification=VerificationResult(passed=True),
            tmr=TMROutput(
                consensus=False,
                disagreements=["Methods disagree on safety."],
            ),
            prover=ProverOutput(
                claims=["Safety is guaranteed."],
                proved=[False],
                unprovable=["Safety is guaranteed."],
            ),
            observer=ObserverResult(
                overconfidence_detected=True,
                notes="Confidence exceeds verified evidence.",
            ),
        )
    )

    by_number = {gate.gate_number: gate for gate in gates}
    assert not by_number[7].passed
    assert not by_number[8].passed
    assert not by_number[9].passed


def test_shadow_prefers_more_conservative_type_when_risk_is_equal():
    router = ScriptedRouter(
        {
            "shadow-orchestrator": [
                {
                    "problem_type": "type3",
                    "risk_level": "medium",
                    "fractal_depth": 2,
                    "reasoning": "The governing rules are unknown.",
                }
            ]
        }
    )

    result = asyncio.run(
        ShadowOrchestrator(router).check(
            "Investigate an unknown mechanism.",
            Classification(
                problem_type="type1",
                risk_level="medium",
                fractal_depth=1,
            ),
        )
    )

    assert result.safe_path.startswith("Use shadow")


if __name__ == "__main__":
    test_quality_gates_use_actual_verification_tmr_prover_and_observer()
    test_quality_gates_fail_critical_tmr_and_unproved_claims()
    test_shadow_prefers_more_conservative_type_when_risk_is_equal()
    print("complete quality gate tests passed")
