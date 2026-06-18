"""Blindspot hunting and recursive fractal verification tests."""

import asyncio

from aocs_mcp.quality.blindspot import BlindspotHunter
from aocs_mcp.quality.fractal import FractalVerifier
from aocs_mcp.quality.observer import Observer
from tests.fakes import ScriptedRouter


def test_blindspot_hunter_answers_all_mandatory_questions():
    router = ScriptedRouter(
        {
            "blindspot-hunter": [
                {
                    "missing_perspectives": ["affected users"],
                    "missing_data": ["failed unpublished trials"],
                    "outsider_view": "The goal assumes the metric is meaningful.",
                    "falsification_conditions": ["The metric does not predict outcomes."],
                    "simplest_overlooked": "The input data may be stale.",
                    "recommended_actions": ["Validate the metric and refresh the data."],
                }
            ]
        }
    )

    result = asyncio.run(
        BlindspotHunter(router).run(
            problem="Choose the best intervention.",
            framing="Current analysis focuses on successful trials.",
            conclusion="Use intervention A.",
        )
    )

    assert result.missing_perspectives == ["affected users"]
    assert result.missing_data == ["failed unpublished trials"]
    assert result.falsification_conditions
    assert result.simplest_overlooked == "The input data may be stale."


def _fractal_responses(depth: int):
    responses = {
        "red-team": [
            {
                "critique": "The conclusion depends on weak evidence.",
                "flaws": ["Weak evidence"],
                "risk_estimate": "high",
            }
        ],
        "contrarian": [
            {
                "analysis": "A different mechanism explains the result.",
                "agreement_level": "propose alternative",
                "alternative_model": "Alternative mechanism",
                "confidence": 70,
            }
        ],
        "judge": [
            {
                "confidence": 85,
                "decision": "flag_for_review",
                "reasoning": "The conclusion survives partially.",
            }
        ],
    }
    if depth >= 2:
        responses["fractal-observer"] = [
            {
                "groupthink_detected": False,
                "overconfidence_detected": True,
                "notes": "Evidence remains thin.",
            }
        ]
        responses["fractal-shadow"] = [
            {
                "routing_valid": False,
                "recommended_route": "type3",
                "reasoning": "The challenge reveals an unknown mechanism.",
            }
        ]
    if depth >= 3:
        responses["red-team"].append(
            {
                "critique": "The second-order review may itself be biased.",
                "flaws": ["Review bias"],
                "risk_estimate": "critical",
            }
        )
        responses["contrarian"].append(
            {
                "analysis": "The review framework is the wrong frame.",
                "agreement_level": "propose alternative",
                "alternative_model": "Different verification framework",
                "confidence": 65,
            }
        )
        responses["judge"].append(
            {
                "confidence": 78,
                "decision": "reject",
                "reasoning": "The verification does not survive third-order audit.",
            }
        )
    return responses


def test_fractal_depth_one_runs_red_team_contrarian_and_judge():
    router = ScriptedRouter(_fractal_responses(1))

    result = asyncio.run(
        FractalVerifier(router).run("Use intervention A.", depth=1)
    )

    assert result.executed_depth == 1
    assert [entry["role"] for entry in router.call_log] == [
        "red-team",
        "contrarian",
        "judge",
    ]


def test_fractal_depth_two_challenges_the_first_order_verification():
    router = ScriptedRouter(_fractal_responses(2))

    result = asyncio.run(
        FractalVerifier(router).run("Use intervention A.", depth=2)
    )

    assert result.executed_depth == 2
    assert [entry["role"] for entry in router.call_log][-2:] == [
        "fractal-observer",
        "fractal-shadow",
    ]


def test_fractal_depth_three_challenges_second_order_verification():
    router = ScriptedRouter(_fractal_responses(3))

    result = asyncio.run(
        FractalVerifier(router).run("Use intervention A.", depth=3)
    )

    roles = [entry["role"] for entry in router.call_log]
    assert result.executed_depth == 3
    assert roles.count("red-team") == 2
    assert roles.count("contrarian") == 2
    assert roles.count("judge") == 2
    assert not result.survived


def test_observer_preserves_injected_chaos_variable():
    router = ScriptedRouter(
        {
            "observer": [
                {
                    "groupthink_detected": True,
                    "overconfidence_detected": True,
                    "chaos_variable_injected": True,
                    "notes": "All agents shared the same assumption.",
                    "chaos_variable": "Assume the central measurement is inverted.",
                }
            ]
        }
    )

    result = asyncio.run(
        Observer(router).check(
            specialist_confidence=98,
            judge_confidence=97,
            contrarian_agreement="agree with specialist",
            deception_flags=[],
        )
    )

    assert result.chaos_variable == "Assume the central measurement is inverted."


if __name__ == "__main__":
    test_blindspot_hunter_answers_all_mandatory_questions()
    test_fractal_depth_one_runs_red_team_contrarian_and_judge()
    test_fractal_depth_two_challenges_the_first_order_verification()
    test_fractal_depth_three_challenges_second_order_verification()
    test_observer_preserves_injected_chaos_variable()
    print("fractal and blindspot tests passed")
