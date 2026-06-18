"""Pipeline orchestrator for the complete AOCS-Omega runtime."""

from dataclasses import dataclass
import re

from aocs_mcp.breakthrough.analogical_mining import AnalogicalMining
from aocs_mcp.breakthrough.break_framework import BreakFrameworkAgent
from aocs_mcp.breakthrough.future_backcast import FutureBackcast
from aocs_mcp.breakthrough.higher_dimension import HigherDimension
from aocs_mcp.breakthrough.universal_goal import UniversalGoalProtocol
from aocs_mcp.config import Config
from aocs_mcp.learning.flywheel import Flywheel
from aocs_mcp.memory.auditor import MemoryAuditor
from aocs_mcp.memory.blackboard import Blackboard
from aocs_mcp.memory.graveyard import Graveyard
from aocs_mcp.phase0.assumptions import AssumptionMapper
from aocs_mcp.phase0.deep_test import DeepTest
from aocs_mcp.phase0.multi_framer import MultiFramer
from aocs_mcp.phase0.parser import parse
from aocs_mcp.phase0.root_problem import RootProblemExtractor
from aocs_mcp.phase0.uncertainty import quantify
from aocs_mcp.phase1.scorer import Phase1Runner
from aocs_mcp.pipeline.models import (
    AnalysisResult,
    AuditResult,
    BlindspotResult,
    Classification,
    ContrarianOutput,
    FractalResult,
    GateResult,
    JudgeVerdict,
    KillSwitchResult,
    ObserverResult,
    Phase0Result,
    Phase1Result,
    RedTeamOutput,
    ShadowResult,
    SpecialistOutput,
    SwarmResult,
    Type1Result,
    Type2Result,
    Type3Result,
    VerificationResult,
)
from aocs_mcp.quality.blindspot import BlindspotHunter
from aocs_mcp.quality.fractal import FractalVerifier
from aocs_mcp.quality.gates import QualityGates
from aocs_mcp.quality.kill_switch import KillSwitch
from aocs_mcp.quality.observer import Observer
from aocs_mcp.quality.shadow_orch import ShadowOrchestrator
from aocs_mcp.quality.verifier import DeterministicVerifier
from aocs_mcp.router import LLMRouter
from aocs_mcp.routing.classifier import classify_with_model
from aocs_mcp.routing.swarm import Swarm
from aocs_mcp.routing.type1_pipe import Type1Pipe
from aocs_mcp.routing.type2_pipe import Type2Pipe
from aocs_mcp.routing.type3_pipe import Type3Pipe


@dataclass
class _RouteExecution:
    route_taken: str
    quality_subject: Type2Result
    verification: VerificationResult
    type1: Type1Result | None = None
    type2: Type2Result | None = None
    type3: Type3Result | None = None
    swarm: SwarmResult | None = None


@dataclass
class _EvaluatedAttempt:
    execution: _RouteExecution
    proposal: str
    blindspot: BlindspotResult
    fractal: FractalResult
    observer: ObserverResult
    quality_gates: list[GateResult]


class AOCSOrchestrator:
    """Chain all AOCS phases and preserve every produced artifact."""

    def __init__(self, router: LLMRouter, config: Config | None):
        self.router = router
        self.config = config
        self.blackboard = Blackboard()
        self.graveyard = Graveyard()
        self.kill_switch = KillSwitch()
        self.llm_call_count = 0

    def _count_call(self) -> None:
        self.llm_call_count += 1

    async def analyze(
        self,
        problem: str,
        domain: str | None = None,
        risk: str | None = None,
        fractal_depth: int | None = None,
        context: str | None = None,
        max_sub_agents: int = 64,
    ) -> AnalysisResult:
        """Run the deterministic AOCS pipeline from framing through learning."""
        self.llm_call_count = 0
        self.blackboard = Blackboard()
        self.graveyard = Graveyard()
        self.kill_switch = KillSwitch()
        if hasattr(self.router, "reset_trace"):
            self.router.reset_trace(max_calls=max_sub_agents)

        try:
            direct_result = await self._maybe_direct_low_risk(
                problem, domain, risk, fractal_depth
            )
            if direct_result:
                return direct_result

            phase0 = await self._run_phase0(problem, domain, context)
            phase1 = await Phase1Runner(self.router).run_with_model(phase0)
            self.blackboard.store(
                "phase1",
                phase1.top_problem.model_dump() if phase1.top_problem else None,
            )

            classification = await classify_with_model(
                self.router,
                problem,
                phase0,
                risk_hint=risk,
                depth_hint=fractal_depth,
            )
            if fractal_depth is not None:
                classification.fractal_depth = max(0, min(3, fractal_depth))
            self.blackboard.store("classification", classification)

            execution = await self._execute_route(
                classification,
                phase0,
                phase1,
                domain,
            )
            self._store_route(execution)

            shadow = await ShadowOrchestrator(self.router).check(
                problem,
                classification,
            )
            self.blackboard.store("shadow", shadow)
            if (
                shadow.divergence_detected
                and shadow.safe_path.startswith("Use shadow")
            ):
                original_route = execution.route_taken
                classification = shadow.shadow_classification
                execution = await self._execute_route(
                    classification,
                    phase0,
                    phase1,
                    domain,
                )
                execution.route_taken = (
                    f"{original_route}->shadow:{execution.route_taken}"
                )
                self.blackboard.store(
                    "shadow_reroute",
                    {
                        "from": original_route,
                        "to": execution.route_taken,
                        "classification": classification.model_dump(),
                    },
                )
                self._store_route(execution)

            goal_achievement = None
            if UniversalGoalProtocol.applies(problem, classification):
                goal_achievement = await UniversalGoalProtocol(
                    self.router
                ).run(problem)
                self.blackboard.store(
                    "universal_goal",
                    goal_achievement,
                )

            breakthroughs = []
            break_framework = None
            paradigm_reframe = None
            if execution.type3 and execution.type3.paradigm_alert:
                breakthroughs = [
                    await AnalogicalMining(self.router).run(problem),
                    await HigherDimension(self.router).run(problem),
                    await FutureBackcast(self.router).run(problem),
                ]
                break_framework = await BreakFrameworkAgent(self.router).run(
                    problem,
                    execution.type3.paradigm_reason
                    or "Type 3 paradigm detection alert.",
                )
                self.blackboard.store(
                    "breakthroughs",
                    [item.model_dump() for item in breakthroughs],
                )
                self.blackboard.store(
                    "break_framework",
                    break_framework,
                )
                higher_dimension = next(
                    (
                        item
                        for item in breakthroughs
                        if item.method == "reframe"
                    ),
                    None,
                )
                if higher_dimension and higher_dimension.reframed_problem:
                    reframed_phase0 = await self._run_phase0(
                        higher_dimension.reframed_problem,
                        domain,
                        (
                            "A Type 3 paradigm alert forced higher-dimension "
                            "reframing. Treat this as a new problem."
                        ),
                    )
                    reframed_phase1 = await Phase1Runner(
                        self.router
                    ).run_with_model(reframed_phase0)
                    reframed_classification = await classify_with_model(
                        self.router,
                        higher_dimension.reframed_problem,
                        reframed_phase0,
                    )
                    paradigm_reframe = {
                        "problem": higher_dimension.reframed_problem,
                        "phase0": reframed_phase0.model_dump(),
                        "phase1": reframed_phase1.model_dump(),
                        "classification": (
                            reframed_classification.model_dump()
                        ),
                    }
                    self.blackboard.store(
                        "paradigm_reframe",
                        paradigm_reframe,
                    )

            proposal = execution.quality_subject.specialist.proposal
            blindspot = await BlindspotHunter(self.router).run(
                problem,
                phase0.root_problem,
                proposal,
            )
            self.blackboard.store("blindspot", blindspot)

            fd = classification.fractal_depth
            fractal = await FractalVerifier(self.router).run(proposal, fd)
            self.blackboard.store("fractal", fractal)
            self._merge_fractal_review(execution.quality_subject, fractal)

            observer = await Observer(self.router).check(
                specialist_confidence=execution.quality_subject.specialist.confidence,
                judge_confidence=execution.quality_subject.judge.confidence,
                contrarian_agreement=(
                    execution.quality_subject.contrarian.agreement_level
                ),
                deception_flags=execution.quality_subject.deception_flags,
            )
            self.blackboard.store("observer", observer)
            if observer.chaos_variable_injected:
                execution.verification = await self._apply_chaos_reconsideration(
                    problem,
                    phase0,
                    execution.quality_subject,
                    observer,
                )
                proposal = execution.quality_subject.specialist.proposal

            quality_gates = await QualityGates(self.router).run(
                execution.quality_subject,
                classification.risk_level,
                verification=execution.verification,
                tmr=execution.type1.tmr if execution.type1 else None,
                prover=execution.type1.prover if execution.type1 else None,
                observer=observer,
            )
            self.blackboard.store(
                "quality_gates",
                [gate.model_dump() for gate in quality_gates],
            )

            confidence = execution.quality_subject.judge.confidence
            verdict = self._determine_verdict(
                confidence,
                quality_gates,
                observer,
            )
            verdict = self._apply_shadow_escalation(verdict, shadow)

            failed_gates = [gate for gate in quality_gates if not gate.passed]
            attempt_history = [
                self._attempt_record(
                    classification,
                    phase0,
                    execution,
                    confidence,
                    failed_gates,
                    verdict,
                )
            ]
            kill_switch_result: KillSwitchResult | None = None
            approach_signature = (
                f"{classification.problem_type}:{phase0.root_problem}"
            )

            if (
                classification.problem_type != "type3"
                and self._quality_attempt_failed(
                    execution,
                    quality_gates,
                    fractal,
                )
            ):
                kill_switch_result = self.kill_switch.record_failure(
                    approach_signature,
                    self._failure_reason(quality_gates),
                )
                retry = await self._retry_same_approach(
                    problem,
                    domain,
                    phase0,
                    phase1,
                    classification,
                    execution.route_taken,
                )
                execution = retry.execution
                proposal = retry.proposal
                blindspot = retry.blindspot
                fractal = retry.fractal
                observer = retry.observer
                quality_gates = retry.quality_gates
                confidence = execution.quality_subject.judge.confidence
                verdict = self._determine_verdict(
                    confidence,
                    quality_gates,
                    observer,
                )
                verdict = self._apply_shadow_escalation(verdict, shadow)
                failed_gates = [
                    gate for gate in quality_gates if not gate.passed
                ]
                attempt_history.append(
                    self._attempt_record(
                        classification,
                        phase0,
                        execution,
                        confidence,
                        failed_gates,
                        verdict,
                    )
                )

                if self._quality_attempt_failed(
                    execution,
                    quality_gates,
                    fractal,
                ):
                    kill_switch_result = self.kill_switch.record_failure(
                        approach_signature,
                        self._failure_reason(quality_gates),
                    )

                if kill_switch_result.fired:
                    breakthroughs = [
                        await AnalogicalMining(self.router).run(problem),
                        await HigherDimension(self.router).run(problem),
                        await FutureBackcast(self.router).run(problem),
                    ]
                    higher_dimension = next(
                        (
                            item
                            for item in breakthroughs
                            if item.method == "reframe"
                        ),
                        None,
                    )
                    break_framework = await BreakFrameworkAgent(
                        self.router
                    ).run(
                        problem,
                        kill_switch_result.reason,
                    )
                    self.blackboard.store(
                        "kill_switch_breakthroughs",
                        [item.model_dump() for item in breakthroughs],
                    )
                    self.blackboard.store(
                        "kill_switch_break_framework",
                        break_framework,
                    )

                    reframe_context = (
                        "The same approach failed the quality gates twice. "
                        "Do not preserve its root assumptions.\n"
                        f"Failure record: {kill_switch_result.reason}\n"
                        "Higher-dimension proposal: "
                        f"{higher_dimension.adapted_proposal if higher_dimension else ''}"
                    )
                    reframed_phase0 = await self._run_phase0(
                        problem,
                        domain,
                        reframe_context,
                    )
                    reframed_phase1 = await Phase1Runner(
                        self.router
                    ).run_with_model(reframed_phase0)
                    reclassified = await classify_with_model(
                        self.router,
                        problem,
                        reframed_phase0,
                    )
                    kill_switch_result.reframed_problem = (
                        reframed_phase0.root_problem
                    )
                    kill_switch_result.reclassified_as = reclassified
                    execution.route_taken = (
                        f"{execution.route_taken}->kill-switch:reframe"
                    )
                    verdict = "reject"
                    self.blackboard.store(
                        "kill_switch_reframe",
                        {
                            "phase0": reframed_phase0.model_dump(),
                            "phase1": reframed_phase1.model_dump(),
                            "classification": reclassified.model_dump(),
                        },
                    )

            self.blackboard.apply_decay()
            audit = MemoryAuditor().audit(self.blackboard)
            confidence, verdict = self._apply_memory_audit(
                confidence,
                verdict,
                audit,
            )

            result = AnalysisResult(
                problem=problem,
                domain=domain,
                problem_type=classification.problem_type,
                route_taken=execution.route_taken,
                fractal_depth=fd,
                total_llm_calls=getattr(
                    self.router, "call_count", self.llm_call_count
                ),
                classification=classification,
                phase0_reframes=phase0.reframe_count,
                attempt_history=attempt_history,
                root_problem=phase0.root_problem,
                interpretations=phase0.interpretations,
                assumptions=phase0.assumptions,
                deep_test_passed=phase0.deep_test.passed,
                top_problem=phase1.top_problem,
                specialist_proposal=proposal,
                red_team_critique=execution.quality_subject.red_team.critique,
                contrarian_analysis=(
                    execution.quality_subject.contrarian.analysis
                ),
                deception_flags=execution.quality_subject.deception_flags,
                judge_verdict=execution.quality_subject.judge,
                type1_verified=(
                    execution.type1.verified if execution.type1 else None
                ),
                type3_findings=execution.type3,
                swarm_result=execution.swarm,
                verification=execution.verification,
                prover_result=(
                    execution.type1.prover if execution.type1 else None
                ),
                tmr_result=(
                    execution.type1.tmr if execution.type1 else None
                ),
                fractal_result=fractal,
                blindspot_check=blindspot,
                kill_switch=kill_switch_result,
                quests=execution.type3.quests if execution.type3 else [],
                breakthroughs=breakthroughs,
                break_framework=break_framework,
                goal_achievement=goal_achievement,
                paradigm_reframe=paradigm_reframe,
                external_review_hooks=(
                    execution.type2.external_review_hooks
                    if execution.type2
                    else []
                ),
                quality_gates=quality_gates,
                observer_check=observer,
                shadow_check=shadow,
                memory_audit=audit,
                graveyard_entries=self.graveyard.all(),
                confidence=round(confidence, 1),
                verdict=verdict,
                recommendations=self._build_recommendations(
                    verdict,
                    audit,
                    shadow,
                    blindspot.recommended_actions,
                ),
            )

            result.learning_entries = Flywheel().capture(
                problem,
                result,
                self.blackboard,
            )
            result.blackboard_entries = self.blackboard.all()
            result.total_llm_calls = getattr(
                self.router, "call_count", self.llm_call_count
            )
            return result

        except Exception as exc:
            return AnalysisResult(
                problem=problem,
                domain=domain,
                total_llm_calls=getattr(
                    self.router, "call_count", self.llm_call_count
                ),
                blackboard_entries=self.blackboard.all(),
                graveyard_entries=self.graveyard.all(),
                error=str(exc),
                verdict="error",
                recommendations=[f"Pipeline error: {exc}"],
            )

    async def _retry_same_approach(
        self,
        problem: str,
        domain: str | None,
        phase0: Phase0Result,
        phase1: Phase1Result,
        classification: Classification,
        route_label: str,
    ) -> _EvaluatedAttempt:
        execution = await self._execute_route(
            classification,
            phase0,
            phase1,
            domain,
        )
        execution.route_taken = route_label
        self._store_route(execution)

        proposal = execution.quality_subject.specialist.proposal
        blindspot = await BlindspotHunter(self.router).run(
            problem,
            phase0.root_problem,
            proposal,
        )
        self.blackboard.store("blindspot:retry", blindspot)

        fractal = await FractalVerifier(self.router).run(
            proposal,
            classification.fractal_depth,
        )
        self.blackboard.store("fractal:retry", fractal)
        self._merge_fractal_review(execution.quality_subject, fractal)

        observer = await Observer(self.router).check(
            specialist_confidence=execution.quality_subject.specialist.confidence,
            judge_confidence=execution.quality_subject.judge.confidence,
            contrarian_agreement=(
                execution.quality_subject.contrarian.agreement_level
            ),
            deception_flags=execution.quality_subject.deception_flags,
        )
        self.blackboard.store("observer:retry", observer)
        if observer.chaos_variable_injected:
            execution.verification = await self._apply_chaos_reconsideration(
                problem,
                phase0,
                execution.quality_subject,
                observer,
            )
            proposal = execution.quality_subject.specialist.proposal

        quality_gates = await QualityGates(self.router).run(
            execution.quality_subject,
            classification.risk_level,
            verification=execution.verification,
            tmr=execution.type1.tmr if execution.type1 else None,
            prover=execution.type1.prover if execution.type1 else None,
            observer=observer,
        )
        self.blackboard.store(
            "quality_gates:retry",
            [gate.model_dump() for gate in quality_gates],
        )
        return _EvaluatedAttempt(
            execution=execution,
            proposal=proposal,
            blindspot=blindspot,
            fractal=fractal,
            observer=observer,
            quality_gates=quality_gates,
        )

    @staticmethod
    def _quality_attempt_failed(
        execution: _RouteExecution,
        quality_gates: list[GateResult],
        fractal: FractalResult,
    ) -> bool:
        failed_count = sum(1 for gate in quality_gates if not gate.passed)
        return bool(
            execution.quality_subject.judge.decision == "reject"
            or not execution.verification.passed
            or not fractal.survived
            or failed_count >= 3
        )

    @staticmethod
    def _failure_reason(quality_gates: list[GateResult]) -> str:
        failed = [
            f"Gate {gate.gate_number} {gate.name}: {gate.details}"
            for gate in quality_gates
            if not gate.passed
        ]
        return "; ".join(failed) or "Judge rejected the approach."

    @staticmethod
    def _attempt_record(
        classification: Classification,
        phase0: Phase0Result,
        execution: _RouteExecution,
        confidence: float,
        failed_gates: list[GateResult],
        verdict: str,
    ) -> dict:
        return {
            "approach_signature": (
                f"{classification.problem_type}:{phase0.root_problem}"
            ),
            "route": execution.route_taken,
            "confidence": confidence,
            "failed_gates": [
                f"{gate.gate_number}:{gate.name}" for gate in failed_gates
            ],
            "verdict": verdict,
        }

    async def _execute_route(
        self,
        classification: Classification,
        phase0: Phase0Result,
        phase1: Phase1Result,
        domain: str | None,
    ) -> _RouteExecution:
        if classification.problem_type == "type1":
            result = await Type1Pipe(self.router).run(
                phase0,
                risk=classification.risk_level,
            )
            confidence = result.specialist.confidence
            if not result.verification.passed:
                confidence = min(confidence, 70.0)
            if result.prover.unprovable:
                confidence = min(confidence, 85.0)
            if result.tmr is not None and not result.tmr.consensus:
                confidence = min(confidence, 79.0)
            quality_subject = Type2Result(
                specialist=result.specialist,
                red_team=RedTeamOutput(
                    critique="Fractal blind review is pending.",
                    flaws=[],
                    risk_estimate=classification.risk_level,
                ),
                contrarian=ContrarianOutput(
                    analysis="Fractal contrarian review is pending.",
                    agreement_level="pending",
                    confidence=confidence,
                ),
                judge=JudgeVerdict(
                    confidence=confidence,
                    decision=self._decision_for_confidence(confidence),
                    reasoning=(
                        "Initial confidence combines deterministic verification, "
                        "formal claims, and critical-risk TMR where required."
                    ),
                ),
            )
            return _RouteExecution(
                route_taken="type1",
                quality_subject=quality_subject,
                verification=result.verification,
                type1=result,
            )

        if classification.problem_type == "type3":
            result = await Type3Pipe(
                self.router,
                graveyard=self.graveyard,
            ).run(domain, phase0.root_problem)
            proposal = (
                f"First principles:\n{result.first_principles}\n\n"
                "Surviving hypotheses:\n"
                + "\n".join(f"- {item}" for item in result.survivors)
            )
            quality_subject = Type2Result(
                specialist=SpecialistOutput(
                    proposal=proposal,
                    reasoning=(
                        "The discovery route used independent lenses, first "
                        "principles, mutation, pruning, and simulation."
                    ),
                    prediction=(
                        "The surviving hypotheses will separate under the "
                        "documented simulations or real-world tests."
                    ),
                    assumptions=result.hypotheses,
                    confidence=60.0,
                ),
                red_team=RedTeamOutput(
                    critique=(
                        "Discovery findings remain provisional until tested "
                        "against reality."
                    ),
                    flaws=(
                        result.anomalies
                        or ["Surviving hypotheses lack real-world validation."]
                    ),
                    risk_estimate=classification.risk_level,
                ),
                contrarian=ContrarianOutput(
                    analysis=(
                        "Competing models remain viable; premature convergence "
                        "would be unjustified."
                    ),
                    agreement_level="discovery-mode",
                    confidence=60.0,
                ),
                judge=JudgeVerdict(
                    confidence=60.0,
                    decision="reject",
                    reasoning=(
                        "The route produced testable hypotheses rather than a "
                        "verified final answer."
                    ),
                ),
            )
            return _RouteExecution(
                route_taken="type3",
                quality_subject=quality_subject,
                verification=DeterministicVerifier().verify(
                    quality_subject.specialist
                ),
                type3=result,
            )

        swarm_result = None
        type2_phase0 = phase0
        if classification.decomposable and classification.chunks:
            swarm_result = await Swarm(self.router).run(
                phase0.root_problem or phase0.parsed_problem,
                classification.chunks,
                num_workers=len(classification.chunks),
            )
            type2_phase0 = phase0.model_copy(deep=True)
            type2_phase0.parsed_problem = (
                f"{phase0.parsed_problem}\n\n"
                "Volume Swarm synthesis and audits:\n"
                f"Synthesis: {swarm_result.synthesis}\n"
                f"Peer audits: {swarm_result.peer_audits}\n"
                f"Independent audit: {swarm_result.auditor_report}"
            )

        result = await Type2Pipe(self.router).run(
            type2_phase0,
            phase1,
            risk=classification.risk_level,
        )
        if swarm_result:
            result.specialist.reasoning = (
                f"{result.specialist.reasoning}\n\n"
                f"Volume Swarm synthesis: {swarm_result.synthesis}\n"
                f"Independent swarm audit: {swarm_result.auditor_report}"
            ).strip()
        return _RouteExecution(
            route_taken="type2",
            quality_subject=result,
            verification=DeterministicVerifier().verify(result.specialist),
            type2=result,
            swarm=swarm_result,
        )

    def _store_route(self, execution: _RouteExecution) -> None:
        self.blackboard.store(
            "specialist",
            execution.quality_subject.specialist,
        )
        self.blackboard.store("verification", execution.verification)
        if execution.type1:
            self.blackboard.store("prover", execution.type1.prover)
            if execution.type1.tmr:
                self.blackboard.store("tmr", execution.type1.tmr)
        if execution.type2:
            self.blackboard.store("type2_debate", execution.type2)
        if execution.swarm:
            self.blackboard.store("volume_swarm", execution.swarm)
        if execution.type3:
            self.blackboard.store("type3_discovery", execution.type3)

    async def _apply_chaos_reconsideration(
        self,
        problem: str,
        phase0: Phase0Result,
        quality_subject: Type2Result,
        observer: ObserverResult,
    ) -> VerificationResult:
        system = """You are the AOCS-Omega Chaos Reconsideration Agent.
Re-evaluate the conclusion from first principles using the Observer's chaos
variable. Do not defend the previous answer. Return a revised proposal,
reasoning, falsifiable prediction, explicit assumptions, and confidence.

Output JSON:
{
  "proposal": "",
  "reasoning": "",
  "prediction": "",
  "assumptions": [],
  "confidence": 0
}"""
        data = await self.router.call_structured(
            "chaos-reconsideration",
            system,
            (
                f"Problem:\n{problem}\n\n"
                f"Root problem:\n{phase0.root_problem}\n\n"
                f"Previous conclusion:\n{quality_subject.specialist.proposal}\n\n"
                f"Chaos variable:\n{observer.chaos_variable}"
            ),
        )
        confidence = max(
            0.0,
            min(100.0, float(data.get("confidence", 50.0))),
        )
        revised = SpecialistOutput(
            proposal=str(data.get("proposal", "")),
            reasoning=str(data.get("reasoning", "")),
            prediction=str(data.get("prediction", "")),
            assumptions=[
                str(item) for item in data.get("assumptions", [])
            ],
            confidence=confidence,
        )
        quality_subject.specialist = revised
        quality_subject.judge = JudgeVerdict(
            confidence=confidence,
            decision=self._decision_for_confidence(confidence),
            reasoning=(
                "Confidence was recalibrated after the Observer forced a "
                "first-principles reconsideration."
            ),
        )
        self.blackboard.store(
            "chaos_reconsideration",
            {
                "chaos_variable": observer.chaos_variable,
                "revised_output": revised.model_dump(),
            },
        )
        return DeterministicVerifier().verify(revised)

    @staticmethod
    def _merge_fractal_review(
        quality_subject: Type2Result,
        fractal: FractalResult,
    ) -> None:
        if not fractal.challenges:
            return
        first = fractal.challenges[0]
        if first.red_team:
            quality_subject.red_team = RedTeamOutput(
                critique=first.red_team,
                flaws=["The fractal Red Team identified a concrete challenge."],
                risk_estimate=quality_subject.red_team.risk_estimate,
            )
        if first.contrarian:
            quality_subject.contrarian = ContrarianOutput(
                analysis=first.contrarian,
                agreement_level="independent-fractal-review",
                confidence=(
                    first.judge.confidence
                    if first.judge
                    else quality_subject.contrarian.confidence
                ),
            )
        if first.judge:
            quality_subject.judge = first.judge

    async def _maybe_direct_low_risk(
        self,
        problem: str,
        domain: str | None,
        risk: str | None,
        fractal_depth: int | None,
    ) -> AnalysisResult | None:
        """Collapse an obvious, directly verifiable question to one model call."""
        is_simple_arithmetic = self._looks_like_simple_arithmetic(problem)
        if not is_simple_arithmetic and (
            risk != "low" or (fractal_depth is not None and fractal_depth > 0)
        ):
            return None

        system = (
            "You are AOCS-Omega Direct Low-Risk Specialist. "
            "The problem is directly verifiable and low-risk. "
            "Answer plainly in one short sentence. Do not over-analyze."
        )
        answer = await self.router.call("direct-answer", system, problem)
        verification = VerificationResult(
            passed=bool(str(answer).strip()),
            checks=["direct low-risk response is non-empty"],
            evidence=[f"response_chars={len(str(answer))}"],
            limitations=[
                "Only the direct response structure was checked; domain-specific "
                "reality verification remains the caller's responsibility."
            ],
        )
        self.blackboard.store(
            "direct_answer",
            answer,
            confidence=0.95,
        )
        self.blackboard.store(
            "verification",
            verification,
            provenance="Proof-Only",
            confidence=0.95,
        )
        result = AnalysisResult(
            problem=problem,
            domain=domain,
            problem_type="type1",
            route_taken="direct-low-risk" if risk == "low" else "direct-answer",
            fractal_depth=0,
            total_llm_calls=getattr(
                self.router, "call_count", self.llm_call_count
            ),
            root_problem="Answer the directly verifiable question.",
            specialist_proposal=answer,
            verification=verification,
            attempt_history=[
                {
                    "approach_signature": "type1:direct-low-risk",
                    "route": (
                        "direct-low-risk" if risk == "low" else "direct-answer"
                    ),
                    "confidence": 99.0 if risk == "low" else 95.0,
                    "failed_gates": [],
                    "verdict": "accept",
                }
            ],
            confidence=99.0 if risk == "low" else 95.0,
            verdict="accept",
            recommendations=[
                "Use the direct LLM answer; no deeper AOCS route was needed."
            ],
        )
        result.learning_entries = Flywheel().capture(
            problem,
            result,
            self.blackboard,
        )
        result.blackboard_entries = self.blackboard.all()
        return result

    @staticmethod
    def _looks_like_simple_arithmetic(problem: str) -> bool:
        return bool(re.search(r"\b\d+\s*(?:\+|-|\*|/|x|X)\s*\d+\b", problem))

    async def _run_phase0(
        self,
        problem: str,
        domain: str | None,
        context: str | None = None,
        max_reframes: int = 2,
    ) -> Phase0Result:
        """Return to Multi-Framer whenever the four-question Deep Test fails."""
        reframe_context = context

        for attempt in range(max_reframes + 1):
            parsed = parse(problem, domain, reframe_context)
            self.blackboard.store(f"phase0:{attempt}:parsed", parsed)

            interpretations = await MultiFramer(self.router).generate(
                problem,
                domain,
                reframe_context,
            )
            self.blackboard.store(
                f"phase0:{attempt}:interpretations",
                [item.model_dump() for item in interpretations],
            )

            assumptions = AssumptionMapper().extract(
                interpretations,
                domain,
                problem,
            )
            self.blackboard.store_assumptions(assumptions)
            uncertainties = quantify(assumptions)

            interp_summary = "\n".join(
                f"- {item.label}: {item.root_cause}"
                for item in interpretations
            )
            root_problem = await RootProblemExtractor(self.router).extract(
                problem,
                parsed,
                interp_summary,
            )
            self.blackboard.store(
                f"phase0:{attempt}:root_problem",
                root_problem,
            )

            deep_test = await DeepTest(self.router).run(root_problem, parsed)
            self.blackboard.store(
                f"phase0:{attempt}:deep_test",
                deep_test,
            )

            result = Phase0Result(
                parsed_problem=parsed,
                interpretations=interpretations,
                assumptions=assumptions,
                uncertainties=uncertainties,
                root_problem=root_problem,
                deep_test=deep_test,
                reframe_count=attempt,
            )
            if deep_test.passed or attempt >= max_reframes:
                return result

            deep_answers = "\n".join(
                [
                    deep_test.question_1,
                    deep_test.question_2,
                    deep_test.question_3,
                    deep_test.question_4,
                ]
            )
            reframe_context = (
                f"{context or ''}\n\n"
                "Previous framing failed the Deep Test.\n"
                f"Rejected root problem: {root_problem}\n"
                f"Deep Test answers:\n{deep_answers}\n"
                "Generate genuinely different interpretations and a new root problem."
            ).strip()

        raise RuntimeError("Phase 0 reframe loop exited unexpectedly")

    @staticmethod
    def _decision_for_confidence(confidence: float) -> str:
        if confidence >= 95:
            return "accept"
        if confidence >= 80:
            return "flag_for_review"
        return "reject"

    @staticmethod
    def _determine_verdict(
        confidence: float,
        gates: list[GateResult],
        observer: ObserverResult | None,
    ) -> str:
        failed_gates = [gate for gate in gates if not gate.passed]
        if observer and (
            observer.groupthink_detected or observer.overconfidence_detected
        ):
            return "reject" if confidence < 80 else "flag_for_review"
        if len(failed_gates) >= 3:
            return "reject"
        if confidence >= 95 and not failed_gates:
            return "accept"
        return "flag_for_review"

    @staticmethod
    def _apply_shadow_escalation(
        verdict: str,
        shadow: ShadowResult | None,
    ) -> str:
        if not shadow or not shadow.divergence_detected:
            return verdict
        if shadow.safe_path.startswith("Use shadow") and verdict == "accept":
            return "flag_for_review"
        return verdict

    @staticmethod
    def _apply_memory_audit(
        confidence: float,
        verdict: str,
        audit: AuditResult,
    ) -> tuple[float, str]:
        if not audit.contradictions and not audit.unverified_assumptions:
            return confidence, verdict
        revised_confidence = min(confidence, 94.0)
        revised_verdict = (
            "flag_for_review" if verdict == "accept" else verdict
        )
        return revised_confidence, revised_verdict

    @staticmethod
    def _build_recommendations(
        verdict: str,
        audit: AuditResult,
        shadow: ShadowResult | None = None,
        blindspot_actions: list[str] | None = None,
    ) -> list[str]:
        recommendations = list(blindspot_actions or [])
        if (
            shadow
            and shadow.divergence_detected
            and shadow.safe_path.startswith("Use shadow")
        ):
            recommendations.append(
                "Shadow orchestrator recommends safer reroute: "
                f"{shadow.safe_path}. Do not act on the current route without review."
            )
        if verdict == "reject":
            recommendations.append(
                "Return to Phase 0 and reframe the problem completely."
            )
            recommendations.append(
                "Consider reclassification to a different problem type."
            )
        if audit.contradictions:
            recommendations.append(
                f"Resolve contradictions: {audit.contradictions[0]}"
            )
        if audit.unverified_assumptions:
            recommendations.append(
                f"Verify assumptions: {audit.unverified_assumptions[0]}"
            )
        if not recommendations:
            recommendations.append(
                "Proceed with the proposed solution at the stated confidence."
            )
        return recommendations
