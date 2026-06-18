"""End-to-end orchestration acceptance tests for complete skill parity."""

import asyncio

from aocs_mcp.pipeline.orchestrator import AOCSOrchestrator
from tests.fakes import ScriptedRouter


def _type1_router():
    return ScriptedRouter(
        {
            "multi-framer": [
                {
                    "interpretations": [
                        {
                            "label": "Known procedure",
                            "root_cause": "A standard rule must be applied",
                            "lens": "Established knowledge",
                            "rationale": "The answer can be independently verified.",
                        }
                    ]
                }
            ],
            "root-problem": [{"root_problem": "Apply the known rule correctly."}],
            "deep-test": [
                {
                    "question_1": "It is a real rule.",
                    "question_2": "The rule remains valid.",
                    "question_3": "No further work is needed.",
                    "question_4": "A counterexample would disprove it.",
                    "can_answer_all": True,
                }
            ],
            "scoring-engine": [
                {
                    "sub_problems": [
                        {
                            "name": "Apply known rule",
                            "impact": 9,
                            "leverage": 10,
                            "urgency": 8,
                            "learning": 7,
                            "rationale": "It directly resolves the problem.",
                        }
                    ]
                }
            ],
            "classifier": [
                {
                    "problem_type": "type1",
                    "risk_level": "critical",
                    "fractal_depth": 1,
                    "reasoning": "Known but safety-critical.",
                }
            ],
            "type1-specialist": [
                {
                    "proposal": "Apply the known rule and check the measured output.",
                    "reasoning": (
                        "The rule is established, the input satisfies its "
                        "preconditions, and the output is measurable."
                    ),
                    "prediction": "The measured output will equal the expected value.",
                    "assumptions": ["The measurement is calibrated."],
                    "confidence": 97,
                }
            ],
            "prover": [
                {
                    "claims": [
                        {
                            "statement": "The procedure terminates.",
                            "proved": True,
                            "evidence": "Finite established procedure.",
                        }
                    ]
                }
            ],
            "tmr": ["Independent answer B", "Independent answer C"],
            "tmr-judge": [
                {
                    "consensus": True,
                    "disagreements": [],
                    "reasoning": "All methods agree.",
                }
            ],
            "shadow-orchestrator": [
                {
                    "problem_type": "type1",
                    "risk_level": "critical",
                    "fractal_depth": 1,
                    "reasoning": "Independent route agrees.",
                }
            ],
            "blindspot-hunter": [
                {
                    "missing_perspectives": [],
                    "missing_data": [],
                    "outsider_view": "The calibration assumption is explicit.",
                    "falsification_conditions": ["Measured counterexample."],
                    "simplest_overlooked": "Calibration drift.",
                    "recommended_actions": ["Check calibration."],
                }
            ],
            "observer": [
                {
                    "groupthink_detected": False,
                    "overconfidence_detected": False,
                    "chaos_variable_injected": False,
                    "notes": "Independent methods disagree enough to avoid groupthink.",
                    "chaos_variable": "",
                }
            ],
            "red-team": [
                {
                    "critique": "Calibration drift could invalidate the result.",
                    "flaws": ["Calibration drift"],
                    "risk_estimate": "critical",
                }
            ],
            "contrarian": [
                {
                    "analysis": "The result is valid only with independent calibration.",
                    "agreement_level": "partial",
                    "alternative_model": "Measurement error",
                    "confidence": 88,
                }
            ],
            "judge": [
                {
                    "confidence": 96,
                    "decision": "accept",
                    "reasoning": "The conclusion survives the challenge.",
                }
            ],
        }
    )


def test_canonical_run_integrates_complete_type1_protocol():
    router = _type1_router()

    result = asyncio.run(
        AOCSOrchestrator(router, config=None).analyze(
            "Use the standard documented rule for this critical calculation.",
            max_sub_agents=32,
        )
    )

    assert result.error is None
    assert result.classification.problem_type == "type1"
    assert result.verification.passed
    assert result.prover_result.proved == [True]
    assert result.tmr_result.consensus
    assert result.blindspot_check.falsification_conditions
    assert result.fractal_result.executed_depth == 1
    assert result.memory_audit is not None
    assert result.blackboard_entries
    assert result.learning_entries
    assert result.attempt_history
    assert len(result.quality_gates) == 10


def test_shadow_safer_route_is_executed_instead_of_only_warned():
    router = ScriptedRouter(
        {
            "multi-framer": [
                {
                    "interpretations": [
                        {
                            "label": "Known path",
                            "root_cause": "A documented procedure appears sufficient",
                            "lens": "Established knowledge",
                            "rationale": "The initial evidence looks routine.",
                        }
                    ]
                }
            ],
            "root-problem": [{"root_problem": "Choose the safest valid procedure."}],
            "deep-test": [
                {
                    "question_1": "The limit is real.",
                    "question_2": "The evidence is current.",
                    "question_3": "The procedure would close the task.",
                    "question_4": "A failed measurement would disprove it.",
                    "can_answer_all": True,
                }
            ],
            "scoring-engine": [
                {
                    "sub_problems": [
                        {
                            "name": "Select procedure",
                            "impact": 9,
                            "leverage": 8,
                            "urgency": 8,
                            "learning": 7,
                            "rationale": "It controls the outcome.",
                        }
                    ]
                }
            ],
            "classifier": [
                {
                    "problem_type": "type1",
                    "risk_level": "low",
                    "fractal_depth": 0,
                    "reasoning": "The path initially appears established.",
                }
            ],
            "type1-specialist": [
                {
                    "proposal": "Use the documented procedure.",
                    "reasoning": "The procedure matches the initial facts.",
                    "prediction": "The expected output will be observed.",
                    "assumptions": ["The initial facts are complete."],
                    "confidence": 96,
                }
            ],
            "specialist": [
                {
                    "proposal": "Compare the documented path against the missing evidence.",
                    "reasoning": "The higher-risk route tests competing explanations.",
                    "prediction": "The evidence comparison will distinguish the safe path.",
                    "assumptions": ["The missing evidence can be collected."],
                    "confidence": 95,
                },
            ],
            "prover": [
                {
                    "claims": [
                        {
                            "statement": "The documented procedure terminates.",
                            "proved": True,
                            "evidence": "It is finite.",
                        }
                    ]
                }
            ],
            "shadow-orchestrator": [
                {
                    "problem_type": "type2",
                    "risk_level": "high",
                    "fractal_depth": 0,
                    "reasoning": "Important evidence is missing.",
                }
            ],
            "red-team": [
                {
                    "critique": "The initial facts may be incomplete.",
                    "flaws": ["Missing evidence"],
                    "risk_estimate": "high",
                }
            ],
            "contrarian": [
                {
                    "analysis": "A partially known route is safer.",
                    "agreement_level": "agree with red team",
                    "alternative_model": "Evidence gap",
                    "confidence": 92,
                }
            ],
            "deception-detector": [{"flags": []}],
            "judge": [
                {
                    "confidence": 95,
                    "decision": "accept",
                    "reasoning": "The safer route resolves the evidence gap.",
                }
            ],
            "blindspot-hunter": [
                {
                    "missing_perspectives": [],
                    "missing_data": ["Independent measurement"],
                    "outsider_view": "The first route assumed completeness.",
                    "falsification_conditions": ["The evidence supports the first route."],
                    "simplest_overlooked": "Missing input",
                    "recommended_actions": ["Collect the independent measurement."],
                }
            ],
            "observer": [
                {
                    "groupthink_detected": False,
                    "overconfidence_detected": False,
                    "chaos_variable_injected": False,
                    "notes": "The safer route includes real disagreement.",
                    "chaos_variable": "",
                }
            ],
        }
    )

    result = asyncio.run(
        AOCSOrchestrator(router, config=None).analyze(
            "Use the documented procedure, but important evidence may be missing.",
            max_sub_agents=32,
        )
    )

    assert result.error is None
    assert result.classification.problem_type == "type2"
    assert result.route_taken == "type1->shadow:type2"
    assert result.specialist_proposal.startswith("Compare the documented path")
    assert result.external_review_hooks


def test_observer_chaos_variable_forces_first_principles_reconsideration():
    router = ScriptedRouter(
        {
            "multi-framer": [
                {
                    "interpretations": [
                        {
                            "label": "Evidence gap",
                            "root_cause": "The current proposal relies on incomplete data",
                            "lens": "Evidence",
                            "rationale": "Multiple explanations remain possible.",
                        }
                    ]
                }
            ],
            "root-problem": [{"root_problem": "Resolve the incomplete evidence."}],
            "deep-test": [
                {
                    "question_1": "The uncertainty is real.",
                    "question_2": "The evidence is current.",
                    "question_3": "A test would close the gap.",
                    "question_4": "A counterexample would disprove the frame.",
                    "can_answer_all": True,
                }
            ],
            "scoring-engine": [
                {
                    "sub_problems": [
                        {
                            "name": "Test the evidence",
                            "impact": 9,
                            "leverage": 8,
                            "urgency": 8,
                            "learning": 8,
                            "rationale": "It resolves the main uncertainty.",
                        }
                    ]
                }
            ],
            "classifier": [
                {
                    "problem_type": "type2",
                    "risk_level": "medium",
                    "fractal_depth": 0,
                    "reasoning": "The system is partially known.",
                }
            ],
            "specialist": [
                {
                    "proposal": "Proceed using the majority interpretation.",
                    "reasoning": "Most visible evidence points in one direction.",
                    "prediction": "The majority interpretation will work.",
                    "assumptions": ["The visible evidence is representative."],
                    "confidence": 96,
                }
            ],
            "red-team": [
                {
                    "critique": "The visible evidence may share one bias.",
                    "flaws": ["Shared sampling bias"],
                    "risk_estimate": "medium",
                }
            ],
            "contrarian": [
                {
                    "analysis": "The minority explanation remains plausible.",
                    "agreement_level": "partial",
                    "alternative_model": "Sampling bias",
                    "confidence": 80,
                }
            ],
            "deception-detector": [{"flags": []}],
            "judge": [
                {
                    "confidence": 96,
                    "decision": "accept",
                    "reasoning": "The majority interpretation appears strongest.",
                }
            ],
            "shadow-orchestrator": [
                {
                    "problem_type": "type2",
                    "risk_level": "medium",
                    "fractal_depth": 0,
                    "reasoning": "The original route is reasonable.",
                }
            ],
            "blindspot-hunter": [
                {
                    "missing_perspectives": ["Unobserved failures"],
                    "missing_data": ["Negative cases"],
                    "outsider_view": "The sample is narrow.",
                    "falsification_conditions": ["Negative cases reverse the result."],
                    "simplest_overlooked": "Sampling bias",
                    "recommended_actions": ["Collect negative cases."],
                }
            ],
            "observer": [
                {
                    "groupthink_detected": True,
                    "overconfidence_detected": True,
                    "chaos_variable_injected": True,
                    "notes": "All arguments rely on the same visible sample.",
                    "chaos_variable": "Assume the missing negative cases are the majority.",
                }
            ],
            "chaos-reconsideration": [
                {
                    "proposal": "Collect and test negative cases before choosing a model.",
                    "reasoning": "First principles require representative evidence.",
                    "prediction": "The new sample will separate the competing models.",
                    "assumptions": ["Negative cases can be collected."],
                    "confidence": 84,
                }
            ],
        }
    )

    result = asyncio.run(
        AOCSOrchestrator(router, config=None).analyze(
            "Choose the correct explanation from incomplete evidence.",
            max_sub_agents=32,
        )
    )

    assert result.error is None
    assert result.specialist_proposal.startswith("Collect and test negative cases")
    assert any(
        entry["key"] == "chaos_reconsideration"
        for entry in result.blackboard_entries
    )
    assert result.confidence == 84
    assert result.verdict == "flag_for_review"


def test_type3_paradigm_alert_runs_breakthroughs_and_universal_goal_protocol():
    router = ScriptedRouter(
        {
            "multi-framer": [
                {
                    "interpretations": [
                        {
                            "label": "Unknown mechanism",
                            "root_cause": "The required mechanism has not been discovered",
                            "lens": "Discovery",
                            "rationale": "No established path closes the goal.",
                        }
                    ]
                },
                {
                    "interpretations": [
                        {
                            "label": "Adaptive control frame",
                            "root_cause": "The goal requires continuous feedback control",
                            "lens": "Control theory",
                            "rationale": "The higher-dimensional frame changes the system boundary.",
                        }
                    ]
                },
            ],
            "root-problem": [
                {
                    "root_problem": (
                        "Discover and assemble a closed-loop mechanism for the goal."
                    )
                },
                {
                    "root_problem": (
                        "Maintain verified progress through adaptive feedback control."
                    )
                },
            ],
            "deep-test": [
                {
                    "question_1": "The frontier is real.",
                    "question_2": "No established solution exists.",
                    "question_3": "The complete loop would remove manual handoffs.",
                    "question_4": "An existing complete loop would disprove the frame.",
                    "can_answer_all": True,
                },
                {
                    "question_1": "The feedback requirement is real.",
                    "question_2": "The paradigm alert supplied new evidence.",
                    "question_3": "Adaptive control removes unstable handoffs.",
                    "question_4": "A stable fixed pipeline would disprove it.",
                    "can_answer_all": True,
                },
            ],
            "scoring-engine": [
                {
                    "sub_problems": [
                        {
                            "name": "Discover the mechanism",
                            "impact": 10,
                            "leverage": 8,
                            "urgency": 8,
                            "learning": 10,
                            "rationale": "The mechanism is the bottleneck.",
                        }
                    ]
                },
                {
                    "sub_problems": [
                        {
                            "name": "Stabilize feedback",
                            "impact": 10,
                            "leverage": 9,
                            "urgency": 9,
                            "learning": 10,
                            "rationale": "It resolves the paradigm alert.",
                        }
                    ]
                },
            ],
            "classifier": [
                {
                    "problem_type": "type3",
                    "risk_level": "medium",
                    "fractal_depth": 0,
                    "reasoning": "The governing mechanism is unknown.",
                },
                {
                    "problem_type": "type2",
                    "risk_level": "high",
                    "fractal_depth": 2,
                    "reasoning": "The reframed control problem is partially known.",
                },
            ],
            "type3-lens": [
                {"observations": ["Evidence is sparse."]},
                {"observations": ["The loop has manual handoffs."]},
                {"observations": ["The feedback path is missing."]},
            ],
            "type3-first-principles": [
                {
                    "first_principles": [
                        "Every role must pass its output directly to the next."
                    ],
                    "core_truths": ["Feedback is required to close the loop."],
                }
            ],
            "type3-hypothesis": [
                {
                    "hypotheses": [
                        {"name": "A", "description": "Automated evidence loop"},
                        {"name": "B", "description": "Human coordination loop"},
                        {"name": "C", "description": "Hybrid experiment loop"},
                    ]
                }
            ],
            "idea-mutator": [
                {
                    "mutations": [
                        {"idea": "Cross-domain assembly loop", "novelty": 0.9}
                    ]
                }
            ],
            "ruthless-pruner": [
                {
                    "survivors": ["Automated evidence loop"],
                    "rejected": [
                        {
                            "idea": "Human coordination loop",
                            "reason": "It preserves manual handoffs.",
                        }
                    ],
                    "weirdness_reserve": ["Cross-domain assembly loop"],
                    "anomalies": ["Feedback latency remains unexplained."],
                }
            ],
            "serendipity-injector": [
                {
                    "seeds": ["Biological homeostasis"],
                    "connections": ["Use continuous feedback correction."],
                }
            ],
            "thought-simulator": [
                {
                    "simulations": [
                        {
                            "hypothesis": "Automated evidence loop",
                            "outcome": "The loop closes with delayed feedback.",
                            "status": "partial",
                        }
                    ],
                    "anomalies": ["Delay destabilizes the loop."],
                }
            ],
            "paradigm-detector": [
                {
                    "alert": True,
                    "anomaly_density": 0.7,
                    "reason": "The current frame cannot explain feedback stability.",
                }
            ],
            "universal-goal-assembly": [
                {
                    "single_job": "Take a raw goal and produce a verified outcome.",
                    "starting_point": "raw goal",
                    "desired_end_point": "verified outcome",
                    "roles": [
                        {
                            "name": "Discover",
                            "function": "Generate mechanisms",
                            "current_piece": "Type 3 pipe",
                            "input": "unknown problem",
                            "output": "candidate mechanisms",
                            "cost_share": 50,
                        },
                        {
                            "name": "Verify",
                            "function": "Test the mechanism",
                            "current_piece": "quality gates",
                            "input": "candidate mechanism",
                            "output": "verified result",
                            "cost_share": 30,
                        },
                    ],
                    "closed_loop": ["Discover", "Verify", "Feedback"],
                    "feedback_role": "Feedback",
                    "crude_working_version": "Connect one discovery run to one test.",
                    "completed_loop": True,
                }
            ],
            "inefficiency-hunter": [
                {
                    "root_inefficiency": "Manual experiment transfer",
                    "replacement_architecture": "Automated experiment queue",
                    "cost_before": 50,
                    "cost_after": 15,
                }
            ],
            "analogical-mining": [
                {
                    "abstract_structure": "A delayed feedback loop",
                    "cross_domain_sources": [
                        {
                            "domain": "biology",
                            "analogy": "Homeostasis corrects continuously.",
                        }
                    ],
                    "solution_principle": "Continuous correction",
                    "adapted_proposal": "Add continuous measured feedback.",
                }
            ],
            "higher-dimension": [
                {
                    "current_frame": "Build a fixed pipeline",
                    "higher_dimension_view": "Operate an adaptive control system",
                    "reframed_problem": "Maintain verified progress continuously",
                    "adapted_proposal": "Use feedback as the main architecture.",
                }
            ],
            "future-backcast": [
                {
                    "future_scenario": "The system closes goals autonomously.",
                    "milestones": ["Loop", "Test", "Learn", "Replace", "Scale"],
                    "maybe_that_became_yes": "Feedback-first architecture",
                    "frame_shift": "From pipeline to control system",
                    "roadmap": "Test one complete loop in 30 days.",
                }
            ],
            "break-framework": [
                {
                    "temporary_structure": "Feedback-first discovery",
                    "reordered_phases": ["simulate", "frame", "generate", "verify"],
                    "temporary_agents": ["Control Loop Auditor"],
                    "verification_sequence": ["measurement", "challenge", "judge"],
                    "proposal": "Lead with feedback stability testing.",
                }
            ],
            "shadow-orchestrator": [
                {
                    "problem_type": "type3",
                    "risk_level": "medium",
                    "fractal_depth": 0,
                    "reasoning": "The frontier route is appropriate.",
                }
            ],
            "blindspot-hunter": [
                {
                    "missing_perspectives": ["Control theory"],
                    "missing_data": ["Loop stability measurements"],
                    "outsider_view": "The feedback delay is central.",
                    "falsification_conditions": ["A stable fixed pipeline succeeds."],
                    "simplest_overlooked": "Feedback delay",
                    "recommended_actions": ["Measure feedback latency."],
                }
            ],
            "observer": [
                {
                    "groupthink_detected": False,
                    "overconfidence_detected": False,
                    "chaos_variable_injected": False,
                    "notes": "Multiple discovery paths remain active.",
                    "chaos_variable": "",
                }
            ],
        }
    )

    result = asyncio.run(
        AOCSOrchestrator(router, config=None).analyze(
            "Build a complete closed-loop system for an unknown goal mechanism.",
            max_sub_agents=48,
        )
    )

    assert result.error is None
    assert result.goal_achievement is not None
    assert result.goal_achievement.completed_loop
    assert len(result.breakthroughs) == 3
    assert result.break_framework is not None
    assert result.break_framework.triggered
    assert result.paradigm_reframe["classification"]["problem_type"] == "type2"
    assert result.quests
    assert result.graveyard_entries


def test_two_failed_attempts_fire_kill_switch_and_reframe_from_phase0():
    initial_frame = {
        "interpretations": [
            {
                "label": "Partial model",
                "root_cause": "The current causal model may be incomplete",
                "lens": "Evidence",
                "rationale": "The known rules do not explain the failures.",
            }
        ]
    }
    reframed = {
        "interpretations": [
            {
                "label": "Wrong system boundary",
                "root_cause": "The original frame excludes the real mechanism",
                "lens": "Higher dimension",
                "rationale": "Repeated failures invalidate the original boundary.",
            }
        ]
    }
    failed_specialist = {
        "proposal": "Repeat the current intervention with minor adjustments.",
        "reasoning": "The current model is assumed to be mostly correct.",
        "prediction": "The adjusted intervention will succeed.",
        "assumptions": ["The current causal model is correct."],
        "confidence": 70,
    }
    failed_red_team = {
        "critique": "The causal model has no supporting evidence.",
        "flaws": ["Unsupported causal model"],
        "risk_estimate": "high",
    }
    failed_contrarian = {
        "analysis": "The system boundary may be wrong.",
        "agreement_level": "agree with red team",
        "alternative_model": "Different system boundary",
        "confidence": 90,
    }
    failed_judge = {
        "confidence": 55,
        "decision": "reject",
        "reasoning": "The proposal repeats an unsupported approach.",
    }
    blindspot = {
        "missing_perspectives": ["External system boundary"],
        "missing_data": ["Evidence outside the current model"],
        "outsider_view": "The same failed assumption is being reused.",
        "falsification_conditions": ["External evidence validates the model."],
        "simplest_overlooked": "The frame is wrong.",
        "recommended_actions": ["Change the system boundary."],
    }
    observer = {
        "groupthink_detected": False,
        "overconfidence_detected": False,
        "chaos_variable_injected": False,
        "notes": "The failure is explicit.",
        "chaos_variable": "",
    }
    router = ScriptedRouter(
        {
            "multi-framer": [initial_frame, reframed],
            "root-problem": [
                {"root_problem": "Repair the current causal model."},
                {
                    "root_problem": (
                        "Discover the mechanism outside the original system boundary."
                    )
                },
            ],
            "deep-test": [
                {
                    "question_1": "The initial limit appears real.",
                    "question_2": "The current team supplied the frame.",
                    "question_3": "The intervention would end repeated failures.",
                    "question_4": "Another failed attempt disproves it.",
                    "can_answer_all": True,
                },
                {
                    "question_1": "The old boundary was conventional.",
                    "question_2": "Repeated failures invalidate it.",
                    "question_3": "A new mechanism removes the old intervention.",
                    "question_4": "Evidence inside the old boundary would disprove it.",
                    "can_answer_all": True,
                },
            ],
            "scoring-engine": [
                {
                    "sub_problems": [
                        {
                            "name": "Repair current model",
                            "impact": 8,
                            "leverage": 7,
                            "urgency": 8,
                            "learning": 7,
                            "rationale": "It appears to be the current bottleneck.",
                        }
                    ]
                },
                {
                    "sub_problems": [
                        {
                            "name": "Expand system boundary",
                            "impact": 10,
                            "leverage": 9,
                            "urgency": 10,
                            "learning": 10,
                            "rationale": "It replaces the failed frame.",
                        }
                    ]
                },
            ],
            "classifier": [
                {
                    "problem_type": "type2",
                    "risk_level": "medium",
                    "fractal_depth": 0,
                    "reasoning": "The initial model is partially known.",
                },
                {
                    "problem_type": "type3",
                    "risk_level": "high",
                    "fractal_depth": 2,
                    "reasoning": "The governing mechanism lies outside the old frame.",
                },
            ],
            "specialist": [failed_specialist, failed_specialist],
            "red-team": [failed_red_team, failed_red_team],
            "contrarian": [failed_contrarian, failed_contrarian],
            "deception-detector": [{"flags": []}, {"flags": []}],
            "judge": [failed_judge, failed_judge],
            "shadow-orchestrator": [
                {
                    "problem_type": "type2",
                    "risk_level": "medium",
                    "fractal_depth": 0,
                    "reasoning": "The initial route is plausible enough to test.",
                }
            ],
            "blindspot-hunter": [blindspot, blindspot],
            "observer": [observer, observer],
            "analogical-mining": [
                {
                    "abstract_structure": "Repeated local repair cannot fix a boundary error",
                    "cross_domain_sources": [
                        {
                            "domain": "medicine",
                            "analogy": "Treat the underlying system, not one symptom.",
                        }
                    ],
                    "solution_principle": "Change the level of intervention",
                    "adapted_proposal": "Expand the system boundary.",
                }
            ],
            "higher-dimension": [
                {
                    "current_frame": "Repair the current model",
                    "higher_dimension_view": "The model boundary causes the failure",
                    "reframed_problem": "Discover the external mechanism",
                    "adapted_proposal": "Reframe around the larger system.",
                }
            ],
            "future-backcast": [
                {
                    "future_scenario": "The external mechanism is understood.",
                    "milestones": ["Boundary", "Evidence", "Model", "Test", "Adopt"],
                    "maybe_that_became_yes": "The excluded mechanism",
                    "frame_shift": "From local repair to system discovery",
                    "roadmap": "Test the expanded boundary first.",
                }
            ],
            "break-framework": [
                {
                    "temporary_structure": "Boundary-first investigation",
                    "reordered_phases": ["expand boundary", "collect evidence", "frame"],
                    "temporary_agents": ["Boundary Auditor"],
                    "verification_sequence": ["external evidence", "red team", "judge"],
                    "proposal": "Investigate outside the original frame.",
                }
            ],
        }
    )

    result = asyncio.run(
        AOCSOrchestrator(router, config=None).analyze(
            "Fix the repeated failure in the current causal model.",
            max_sub_agents=48,
        )
    )

    assert result.error is None
    assert result.kill_switch is not None
    assert result.kill_switch.fired
    assert result.kill_switch.failure_count == 2
    assert result.kill_switch.reframed_problem.startswith(
        "Discover the mechanism outside"
    )
    assert result.kill_switch.reclassified_as.problem_type == "type3"
    assert len(result.attempt_history) == 2
    assert result.break_framework is not None
    assert len(result.breakthroughs) == 3
    assert "kill-switch" in result.route_taken
    assert result.verdict == "reject"


if __name__ == "__main__":
    test_canonical_run_integrates_complete_type1_protocol()
    test_shadow_safer_route_is_executed_instead_of_only_warned()
    test_observer_chaos_variable_forces_first_principles_reconsideration()
    test_type3_paradigm_alert_runs_breakthroughs_and_universal_goal_protocol()
    test_two_failed_attempts_fire_kill_switch_and_reframe_from_phase0()
    print("complete orchestrator tests passed")
