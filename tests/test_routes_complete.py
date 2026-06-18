"""Complete Type 1, Type 2, and swarm route tests."""

import asyncio

from aocs_mcp.pipeline.models import Assumption, Phase0Result
from aocs_mcp.routing.swarm import Swarm
from aocs_mcp.routing.type1_pipe import Type1Pipe
from aocs_mcp.routing.type2_pipe import Type2Pipe
from aocs_mcp.pipeline.models import Classification, Phase1Result
from aocs_mcp.pipeline.orchestrator import AOCSOrchestrator
from tests.fakes import ScriptedRouter


SPECIALIST_RESPONSE = {
    "proposal": "Apply the established procedure and verify the measured output.",
    "reasoning": "The rules are known, the constraints are explicit, and the output can be checked.",
    "prediction": "The measured output will match the known expected value.",
    "assumptions": ["The measuring instrument is calibrated."],
    "confidence": 97,
}


def _phase0():
    return Phase0Result(
        parsed_problem="Known problem",
        root_problem="Apply and verify the established procedure.",
        assumptions=[Assumption(statement="The measuring instrument is calibrated.")],
    )


class PromptCapturingRouter(ScriptedRouter):
    def __init__(self, responses):
        super().__init__(responses)
        self.system_prompts = {}

    async def call_structured(self, role, system_prompt, user_prompt):
        self.system_prompts[role] = system_prompt
        return await super().call_structured(role, system_prompt, user_prompt)


def test_critical_type1_executes_verifier_prover_and_tmr():
    router = PromptCapturingRouter(
        {
            "type1-specialist": [SPECIALIST_RESPONSE],
            "prover": [
                {
                    "claims": [
                        {
                            "statement": "The procedure is valid under the stated constraint.",
                            "proved": True,
                            "evidence": "Known rule.",
                        }
                    ]
                }
            ],
            "tmr": ["Independent method A", "Independent method B"],
            "tmr-judge": [
                {
                    "consensus": True,
                    "disagreements": [],
                    "reasoning": "All methods reach the same operational conclusion.",
                }
            ],
        }
    )

    result = asyncio.run(Type1Pipe(router).run(_phase0(), risk="critical"))

    assert result.verification.passed
    assert result.prover.proved == [True]
    assert result.tmr is not None
    assert result.tmr.consensus
    assert [entry["role"] for entry in router.call_log] == [
        "type1-specialist",
        "tmr",
        "tmr",
        "tmr-judge",
        "prover",
    ]
    prompt = router.system_prompts["type1-specialist"]
    assert all(
        step in prompt
        for step in ["Question", "Cut", "Simplify", "Speed up", "Automate"]
    )


def test_high_risk_type2_emits_external_independence_hook():
    router = ScriptedRouter(
        {
            "specialist": [SPECIALIST_RESPONSE],
            "red-team": [
                {
                    "critique": "Independent evidence is missing.",
                    "flaws": ["No external replication."],
                    "risk_estimate": "high",
                }
            ],
            "contrarian": [
                {
                    "analysis": "A different causal model remains possible.",
                    "agreement_level": "propose alternative",
                    "alternative_model": "Measurement artifact",
                    "confidence": 75,
                }
            ],
            "deception-detector": [{"flags": []}],
            "judge": [
                {
                    "confidence": 82,
                    "decision": "flag_for_review",
                    "reasoning": "External replication is required.",
                }
            ],
        }
    )

    result = asyncio.run(Type2Pipe(router).run(_phase0(), risk="high"))

    assert any("external" in item.lower() for item in result.external_review_hooks)


def test_swarm_runs_peer_audits_independent_auditor_and_synthesis():
    router = ScriptedRouter(
        {
            "swarm-worker": ["worker one", "worker two"],
            "swarm-peer-audit": [
                {"audit": "worker one missed an edge case"},
                {"audit": "worker two used weak evidence"},
            ],
            "swarm-auditor": [
                {"auditor_report": "Both outputs require evidence checks."}
            ],
            "swarm-synthesis": [
                {
                    "synthesis": "Merged answer with evidence checks.",
                    "common_themes": ["evidence"],
                    "resolved_conflicts": ["scope"],
                }
            ],
        }
    )

    result = asyncio.run(Swarm(router).run("Review", ["item one", "item two"], 2))

    assert len(result.peer_audits) == 2
    assert result.auditor_report == "Both outputs require evidence checks."
    assert result.synthesis == "Merged answer with evidence checks."
    assert [entry["role"] for entry in router.call_log] == [
        "swarm-worker",
        "swarm-worker",
        "swarm-peer-audit",
        "swarm-peer-audit",
        "swarm-auditor",
        "swarm-synthesis",
    ]


def test_orchestrator_integrates_swarm_before_type2_debate():
    router = ScriptedRouter(
        {
            "swarm-worker": ["worker one", "worker two"],
            "swarm-peer-audit": [
                {"audit": "audit one"},
                {"audit": "audit two"},
            ],
            "swarm-auditor": [{"auditor_report": "independent audit"}],
            "swarm-synthesis": [{"synthesis": "combined evidence"}],
            "specialist": [SPECIALIST_RESPONSE],
            "red-team": [
                {
                    "critique": "Check the combined evidence.",
                    "flaws": ["One evidence gap"],
                    "risk_estimate": "medium",
                }
            ],
            "contrarian": [
                {
                    "analysis": "The synthesis is directionally valid.",
                    "agreement_level": "partial",
                    "confidence": 80,
                }
            ],
            "deception-detector": [{"flags": []}],
            "judge": [
                {
                    "confidence": 90,
                    "decision": "flag_for_review",
                    "reasoning": "The composite needs validation.",
                }
            ],
        }
    )
    classification = Classification(
        problem_type="type2",
        risk_level="medium",
        fractal_depth=1,
        decomposable=True,
        chunks=["item one", "item two"],
    )

    execution = asyncio.run(
        AOCSOrchestrator(router, config=None)._execute_route(
            classification,
            _phase0(),
            Phase1Result(),
            domain=None,
        )
    )

    assert execution.swarm is not None
    assert execution.swarm.synthesis == "combined evidence"
    assert "combined evidence" in execution.quality_subject.specialist.reasoning
    assert [entry["role"] for entry in router.call_log][:6] == [
        "swarm-worker",
        "swarm-worker",
        "swarm-peer-audit",
        "swarm-peer-audit",
        "swarm-auditor",
        "swarm-synthesis",
    ]


if __name__ == "__main__":
    test_critical_type1_executes_verifier_prover_and_tmr()
    test_high_risk_type2_emits_external_independence_hook()
    test_swarm_runs_peer_audits_independent_auditor_and_synthesis()
    test_orchestrator_integrates_swarm_before_type2_debate()
    print("complete route tests passed")
