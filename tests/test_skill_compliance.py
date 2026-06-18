"""Acceptance tests derived directly from the complete AOCS skill."""

import asyncio

from aocs_mcp.phase0.parser import parse
from aocs_mcp.phase1.scorer import Phase1Runner
from aocs_mcp.pipeline import models
from aocs_mcp.pipeline.orchestrator import AOCSOrchestrator
from aocs_mcp.routing import classifier
from tests.fakes import ScriptedRouter


def test_complete_result_models_exist():
    required_models = [
        "VerificationResult",
        "FractalChallenge",
        "FractalResult",
        "BlindspotResult",
        "KillSwitchResult",
        "QuestResult",
        "BreakFrameworkResult",
        "GoalRole",
        "GoalAchievementResult",
    ]

    missing = [name for name in required_models if not hasattr(models, name)]

    assert missing == []


def test_analysis_result_exposes_all_skill_protocol_outputs():
    fields = set(models.AnalysisResult.model_fields)
    required_fields = {
        "classification",
        "phase0_reframes",
        "verification",
        "prover_result",
        "tmr_result",
        "fractal_result",
        "blindspot_check",
        "kill_switch",
        "quests",
        "breakthroughs",
        "break_framework",
        "goal_achievement",
        "external_review_hooks",
        "blackboard_entries",
        "graveyard_entries",
        "learning_entries",
        "attempt_history",
    }

    assert required_fields - fields == set()


def test_parser_context_filler_preserves_supplied_context():
    parsed = parse(
        "Why is the experiment failing?",
        domain="biology",
        context="The control group is stable; treatment samples degraded after 24 hours.",
    )

    assert "control group is stable" in parsed
    assert "treatment samples degraded" in parsed


def test_phase1_scoring_uses_model_scores_and_selects_biggest_vertical():
    router = ScriptedRouter(
        {
            "scoring-engine": [
                {
                    "sub_problems": [
                        {
                            "name": "measurement quality",
                            "impact": 8,
                            "leverage": 9,
                            "urgency": 9,
                            "learning": 8,
                            "rationale": "It blocks trustworthy conclusions.",
                        },
                        {
                            "name": "report formatting",
                            "impact": 2,
                            "leverage": 3,
                            "urgency": 1,
                            "learning": 2,
                            "rationale": "Cosmetic only.",
                        },
                    ]
                }
            ]
        }
    )
    phase0 = models.Phase0Result(
        interpretations=[
            models.Interpretation(
                label="Measurement failure",
                root_cause="Bad instrumentation",
                lens="Evidence",
                rationale="Observed readings are inconsistent.",
            )
        ]
    )

    result = asyncio.run(Phase1Runner(router).run_with_model(phase0))

    assert result.top_problem.name == "measurement quality"
    assert result.top_problem.zone in ("Big", "Critical")
    assert result.sub_problems[1].zone == "Noise"


def test_classifier_uses_model_reasoning_without_caller_defaults():
    router = ScriptedRouter(
        {
            "classifier": [
                {
                    "problem_type": "type3",
                    "risk_level": "critical",
                    "fractal_depth": 3,
                    "reasoning": "The governing mechanism is unknown and consequences are severe.",
                }
            ]
        }
    )

    result = asyncio.run(
        classifier.classify_with_model(
            router,
            "Discover a safe cure for an unknown disease.",
            models.Phase0Result(),
        )
    )

    assert result.problem_type == "type3"
    assert result.risk_level == "critical"
    assert result.fractal_depth == 3


def test_classifier_preserves_volume_swarm_decomposition():
    router = ScriptedRouter(
        {
            "classifier": [
                {
                    "problem_type": "type2",
                    "risk_level": "medium",
                    "fractal_depth": 1,
                    "reasoning": "The work contains independent review units.",
                    "decomposable": True,
                    "chunks": ["file one", "file two"],
                }
            ]
        }
    )

    result = asyncio.run(
        classifier.classify_with_model(
            router,
            "Review these files and synthesize the findings.",
            models.Phase0Result(),
        )
    )

    assert result.decomposable
    assert result.chunks == ["file one", "file two"]


def test_phase0_reframes_until_deep_test_passes():
    interpretations = {
        "interpretations": [
            {
                "label": "Evidence gap",
                "root_cause": "Missing evidence",
                "lens": "Evidence",
                "rationale": "The claim is not yet testable.",
            }
        ]
    }
    router = ScriptedRouter(
        {
            "multi-framer": [interpretations, interpretations],
            "root-problem": [
                {"root_problem": "First root"},
                {"root_problem": "Reframed root"},
            ],
            "deep-test": [
                {
                    "question_1": "unclear",
                    "question_2": "unclear",
                    "question_3": "unclear",
                    "question_4": "unclear",
                    "can_answer_all": False,
                },
                {
                    "question_1": "yes",
                    "question_2": "yes",
                    "question_3": "yes",
                    "question_4": "yes",
                    "can_answer_all": True,
                },
            ],
        }
    )

    result = asyncio.run(
        AOCSOrchestrator(router, config=None)._run_phase0(
            "Investigate the claim.",
            domain=None,
            context="Initial evidence is incomplete.",
        )
    )

    assert result.deep_test.passed
    assert result.root_problem == "Reframed root"
    assert result.reframe_count == 1


if __name__ == "__main__":
    test_complete_result_models_exist()
    test_analysis_result_exposes_all_skill_protocol_outputs()
    test_parser_context_filler_preserves_supplied_context()
    test_phase1_scoring_uses_model_scores_and_selects_biggest_vertical()
    test_classifier_uses_model_reasoning_without_caller_defaults()
    test_phase0_reframes_until_deep_test_passes()
    print("skill compliance model tests passed")
