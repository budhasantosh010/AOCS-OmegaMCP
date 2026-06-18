"""Universal Goal-Achievement Protocol tests."""

import asyncio

from aocs_mcp.breakthrough.universal_goal import UniversalGoalProtocol
from aocs_mcp.pipeline.models import Classification
from tests.fakes import ScriptedRouter


def test_universal_goal_protocol_applies_to_novel_goal_systems():
    classification = Classification(
        problem_type="type3",
        risk_level="high",
        fractal_depth=2,
    )

    assert UniversalGoalProtocol.applies(
        "Build a complete system that turns raw research into validated treatments.",
        classification,
    )


def test_universal_goal_protocol_builds_loop_and_replaces_root_inefficiency():
    router = ScriptedRouter(
        {
            "universal-goal-assembly": [
                {
                    "single_job": "Take raw research and produce validated treatments without manual hand-carrying.",
                    "starting_point": "raw research",
                    "desired_end_point": "validated treatment",
                    "roles": [
                        {
                            "name": "Evidence Intake",
                            "function": "Collect and normalize evidence",
                            "current_piece": "research database",
                            "input": "papers",
                            "output": "normalized evidence",
                            "cost_share": 20,
                        },
                        {
                            "name": "Experiment Loop",
                            "function": "Test candidate mechanisms",
                            "current_piece": "laboratory",
                            "input": "candidate mechanism",
                            "output": "validated result",
                            "cost_share": 60,
                        },
                    ],
                    "closed_loop": ["Evidence Intake", "Experiment Loop", "Feedback"],
                    "feedback_role": "Feedback",
                    "crude_working_version": "Manually connect the database to one laboratory trial.",
                    "completed_loop": True,
                }
            ],
            "inefficiency-hunter": [
                {
                    "root_inefficiency": "Experiment scheduling delay",
                    "replacement_architecture": "Automated parallel experiment scheduler",
                    "cost_before": 60,
                    "cost_after": 20,
                }
            ],
        }
    )

    result = asyncio.run(
        UniversalGoalProtocol(router).run(
            "Build a complete system that turns raw research into validated treatments."
        )
    )

    assert result.completed_loop
    assert result.roles[0].name == "Evidence Intake"
    assert result.feedback_role == "Feedback"
    assert result.root_inefficiency == "Experiment scheduling delay"
    assert result.replacement_architecture == "Automated parallel experiment scheduler"
    assert result.cost_after < result.cost_before
    assert [entry["role"] for entry in router.call_log] == [
        "universal-goal-assembly",
        "inefficiency-hunter",
    ]


if __name__ == "__main__":
    test_universal_goal_protocol_applies_to_novel_goal_systems()
    test_universal_goal_protocol_builds_loop_and_replaces_root_inefficiency()
    print("universal goal tests passed")
