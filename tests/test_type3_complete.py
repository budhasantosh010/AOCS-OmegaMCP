"""Complete Type 3 discovery-pipe tests."""

import asyncio

from aocs_mcp.memory.graveyard import Graveyard
from aocs_mcp.routing.type3_pipe import Type3Pipe
from tests.fakes import ScriptedRouter


def test_type3_executes_full_evolutionary_discovery_protocol():
    router = ScriptedRouter(
        {
            "type3-lens": [
                {"observations": ["lens one observation"], "key_insight": "one"},
                {"observations": ["lens two observation"], "key_insight": "two"},
            ],
            "type3-first-principles": [
                {
                    "first_principles": ["Evidence must distinguish causal models."],
                    "core_truths": ["Unknown mechanisms require experiments."],
                }
            ],
            "type3-hypothesis": [
                {
                    "hypotheses": [
                        {"name": "Model A", "description": "Mechanism A"},
                        {"name": "Model B", "description": "Mechanism B"},
                        {"name": "Model C", "description": "Mechanism C"},
                    ]
                }
            ],
            "idea-mutator": [
                {
                    "mutations": [
                        {"idea": "Mutation A", "novelty": 0.4},
                        {"idea": "Impossible but interesting mutation", "novelty": 0.99},
                    ]
                }
            ],
            "ruthless-pruner": [
                {
                    "survivors": ["Mechanism A", "Mutation A"],
                    "rejected": [
                        {"idea": "Mechanism B", "reason": "Violates observed evidence."}
                    ],
                    "weirdness_reserve": ["Impossible but interesting mutation"],
                    "anomalies": ["Anomaly signal remains unexplained."],
                }
            ],
            "serendipity-injector": [
                {
                    "seeds": ["Ant colony path selection"],
                    "connections": ["Use distributed exploration."],
                }
            ],
            "thought-simulator": [
                {
                    "simulations": [
                        {
                            "hypothesis": "Mechanism A",
                            "outcome": "Predicts the observed signal.",
                            "status": "survives",
                        }
                    ],
                    "anomalies": ["Second anomaly"],
                }
            ],
            "paradigm-detector": [
                {
                    "alert": True,
                    "anomaly_density": 0.6,
                    "reason": "Too many observations remain unexplained.",
                }
            ],
        }
    )
    graveyard = Graveyard()
    graveyard.bury(
        "Archived anomaly model",
        "No anomaly signal existed",
        assumptions_at_time="Requires anomaly signal",
    )

    result = asyncio.run(
        Type3Pipe(router, max_lens=2, graveyard=graveyard).run(
            domain=None,
            seed_question="Discover the unknown mechanism.",
        )
    )

    assert result.mutations == ["Mutation A", "Impossible but interesting mutation"]
    assert result.survivors == [
        "Mechanism A",
        "Mutation A",
        "Archived anomaly model",
    ]
    assert result.weirdness_reserve == ["Impossible but interesting mutation"]
    assert result.serendipity_seeds == ["Ant colony path selection"]
    assert result.simulations[0]["status"] == "survives"
    assert result.paradigm_alert
    assert result.anomaly_density == 0.6
    assert result.quests[0].resource_fraction == 0.1
    assert any(item["idea"] == "Mechanism B" for item in graveyard.all())
    assert any(item["resurrected"] for item in graveyard.all())
    assert [entry["role"] for entry in router.call_log] == [
        "type3-lens",
        "type3-lens",
        "type3-first-principles",
        "type3-hypothesis",
        "idea-mutator",
        "ruthless-pruner",
        "serendipity-injector",
        "thought-simulator",
        "paradigm-detector",
    ]


if __name__ == "__main__":
    test_type3_executes_full_evolutionary_discovery_protocol()
    print("complete Type 3 tests passed")
