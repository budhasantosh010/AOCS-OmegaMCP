"""Pipeline Orchestrator — chains all AOCS phases deterministically."""

import re

from aocs_mcp.router import LLMRouter
from aocs_mcp.config import Config
from aocs_mcp.pipeline.models import (
    Phase0Result, Phase1Result, Classification,
    Type1Result, Type2Result, Type3Result, AnalysisResult, GateResult,
    ObserverResult, ShadowResult, AuditResult,
    ScoredProblem, JudgeVerdict, Assumption, Interpretation, DeepTestResult,
    SpecialistOutput, RedTeamOutput, ContrarianOutput,
)
from aocs_mcp.phase0.parser import parse
from aocs_mcp.phase0.multi_framer import MultiFramer
from aocs_mcp.phase0.assumptions import AssumptionMapper
from aocs_mcp.phase0.uncertainty import quantify
from aocs_mcp.phase0.root_problem import RootProblemExtractor
from aocs_mcp.phase0.deep_test import DeepTest
from aocs_mcp.phase1.scorer import Phase1Runner
from aocs_mcp.routing.classifier import classify
from aocs_mcp.routing.type1_pipe import Type1Pipe
from aocs_mcp.routing.type2_pipe import Type2Pipe
from aocs_mcp.routing.type3_pipe import Type3Pipe
from aocs_mcp.quality.gates import QualityGates
from aocs_mcp.quality.observer import Observer
from aocs_mcp.quality.shadow_orch import ShadowOrchestrator
from aocs_mcp.memory.blackboard import Blackboard
from aocs_mcp.memory.auditor import MemoryAuditor
from aocs_mcp.learning.flywheel import Flywheel


class AOCSOrchestrator:
    """Chains all AOCS phases sequentially and returns the final AnalysisResult."""

    def __init__(self, router: LLMRouter, config: Config):
        self.router = router
        self.config = config
        self.blackboard = Blackboard()
        self.llm_call_count = 0

    def _count_call(self) -> None:
        self.llm_call_count += 1

    async def analyze(
        self,
        problem: str,
        domain: str = "software",
        risk: str = "medium",
        fractal_depth: int | None = None,
        context: str | None = None,
        max_sub_agents: int = 16,
    ) -> AnalysisResult:
        """Run the full AOCS pipeline from start to finish."""
        self.llm_call_count = 0
        if hasattr(self.router, "reset_trace"):
            self.router.reset_trace(max_calls=max_sub_agents)

        try:
            direct_result = await self._maybe_direct_low_risk(problem, domain, risk, fractal_depth)
            if direct_result:
                return direct_result

            # === PHASE 0: Problem Framing ===
            phase0 = await self._run_phase0(problem, domain)

            # === PHASE 1: Scoring ===
            phase1 = Phase1Runner().run(phase0)
            self.blackboard.store("phase1", phase1.top_problem.model_dump() if phase1.top_problem else "none")

            # === CLASSIFICATION ===
            classification = classify(problem, phase0)
            classification.risk_level = risk or classification.risk_level
            self.blackboard.store("classification", classification.model_dump())
            fd = fractal_depth if fractal_depth is not None else classification.fractal_depth

            # === ROUTING + EXECUTION ===
            type1_result: Type1Result | None = None
            result: Type2Result | None = None
            type3_result: Type3Result | None = None
            quality_subject: Type2Result | None = None
            route_taken = ""

            if classification.problem_type == "type1":
                route_taken = "type1"
                type1_result = await Type1Pipe(self.router).run(phase0)
                quality_subject = Type2Result(
                    specialist=type1_result.specialist,
                    red_team=RedTeamOutput(
                        critique="Type 1 route used deterministic verifier and prover instead of full red-team debate.",
                        flaws=[],
                        risk_estimate=classification.risk_level,
                    ),
                    contrarian=ContrarianOutput(
                        analysis="Type 1 route accepted the known-system path unless verifier/prover failed.",
                        agreement_level="route-limited",
                        confidence=type1_result.specialist.confidence,
                    ),
                    deception_flags=[],
                    judge=JudgeVerdict(
                        confidence=type1_result.specialist.confidence,
                        decision="accept" if type1_result.verified and type1_result.specialist.confidence >= 95 else "flag_for_review",
                        reasoning="Confidence derived from Type 1 specialist plus deterministic verifier.",
                    ),
                )
            elif classification.problem_type == "type3":
                route_taken = "type3"
                type3_result = await Type3Pipe(self.router).run(domain, phase0.root_problem or problem)
                proposal = (
                    "First principles:\n"
                    f"{type3_result.first_principles}\n\n"
                    "Surviving hypotheses:\n"
                    + "\n".join(f"- {h}" for h in type3_result.survivors)
                )
                quality_subject = Type2Result(
                    specialist=SpecialistOutput(
                        proposal=proposal,
                        reasoning="Type 3 discovery route generated lens observations, first principles, and competing hypotheses.",
                        prediction="Next step is to test the surviving hypotheses against reality.",
                        assumptions=type3_result.hypotheses,
                        confidence=60.0,
                    ),
                    red_team=RedTeamOutput(
                        critique="Discovery output is intentionally provisional and must not be treated as final proof.",
                        flaws=type3_result.anomalies,
                        risk_estimate=classification.risk_level,
                    ),
                    contrarian=ContrarianOutput(
                        analysis="Type 3 route preserves multiple hypotheses instead of forcing premature convergence.",
                        agreement_level="discovery-mode",
                        confidence=60.0,
                    ),
                    deception_flags=[],
                    judge=JudgeVerdict(
                        confidence=60.0,
                        decision="flag_for_review",
                        reasoning="Discovery route returns hypotheses, not a final answer.",
                    ),
                )
            else:
                route_taken = "type2"
                result = await Type2Pipe(self.router).run(phase0, phase1)
                quality_subject = result

            # === QUALITY GATES ===
            quality_gates: list[GateResult] = []
            observer_result: ObserverResult | None = None
            if quality_subject:
                gates_obj = QualityGates(self.router)
                quality_gates = await gates_obj.run(quality_subject, classification.risk_level)

                # Observer check
                observer = Observer(self.router)
                observer_result = await observer.check(
                    specialist_confidence=quality_subject.specialist.confidence,
                    judge_confidence=quality_subject.judge.confidence,
                    contrarian_agreement=quality_subject.contrarian.agreement_level,
                    deception_flags=quality_subject.deception_flags,
                )
                self._count_call()

            # === SHADOW ORCHESTRATOR ===
            shadow = await ShadowOrchestrator(self.router).check(problem, classification)
            self._count_call()

            # === MEMORY AUDIT ===
            audit = MemoryAuditor().audit(self.blackboard)

            # === FINAL VERDICT ===
            confidence = quality_subject.judge.confidence if quality_subject else 50.0
            verdict_str = self._determine_verdict(confidence, quality_gates, observer_result)
            total_llm_calls = getattr(self.router, "call_count", self.llm_call_count)

            # === FLYWHEEL ===
            analysis_result = AnalysisResult(
                problem=problem,
                domain=domain,
                problem_type=classification.problem_type,
                route_taken=route_taken,
                fractal_depth=fd,
                total_llm_calls=total_llm_calls,
                root_problem=phase0.root_problem,
                interpretations=phase0.interpretations,
                assumptions=phase0.assumptions,
                deep_test_passed=phase0.deep_test.passed,
                top_problem=phase1.top_problem,
                specialist_proposal=quality_subject.specialist.proposal if quality_subject else None,
                red_team_critique=quality_subject.red_team.critique if quality_subject else None,
                contrarian_analysis=quality_subject.contrarian.analysis if quality_subject else None,
                deception_flags=quality_subject.deception_flags if quality_subject else [],
                judge_verdict=quality_subject.judge if quality_subject else None,
                type1_verified=type1_result.verified if type1_result else None,
                type3_findings=type3_result,
                quality_gates=quality_gates,
                observer_check=observer_result,
                shadow_check=shadow,
                memory_audit=audit,
                confidence=round(confidence, 1),
                verdict=verdict_str,
                recommendations=self._build_recommendations(verdict_str, audit),
            )

            Flywheel().capture(problem, analysis_result, self.blackboard)
            return analysis_result

        except Exception as e:
            return AnalysisResult(
                problem=problem,
                domain=domain,
                total_llm_calls=getattr(self.router, "call_count", self.llm_call_count),
                error=str(e),
                verdict="error",
                recommendations=[f"Pipeline error: {e}"],
            )

    async def _maybe_direct_low_risk(
        self,
        problem: str,
        domain: str,
        risk: str,
        fractal_depth: int | None,
    ) -> AnalysisResult | None:
        """Collapse obvious low-risk arithmetic to the shortest useful path."""
        arithmetic_answer = self._solve_simple_arithmetic(problem)
        if arithmetic_answer is not None:
            total_llm_calls = getattr(self.router, "call_count", self.llm_call_count)
            route = "direct-low-risk" if risk == "low" else "direct-arithmetic"
            return AnalysisResult(
                problem=problem,
                domain=domain,
                problem_type="type1",
                route_taken=route,
                fractal_depth=0,
                total_llm_calls=total_llm_calls,
                root_problem="Answer the directly verifiable arithmetic question.",
                specialist_proposal=arithmetic_answer,
                confidence=100.0,
                verdict="accept",
                recommendations=["Use the deterministic arithmetic answer; no model call was needed."],
            )

        if risk != "low" or (fractal_depth is not None and fractal_depth > 0):
            return None

        system = (
            "You are AOCS-Omega Direct Low-Risk Specialist. "
            "The problem is directly verifiable and low-risk. "
            "Answer plainly in one short sentence. Do not over-analyze."
        )
        answer = await self.router.call("direct-answer", system, problem)
        total_llm_calls = getattr(self.router, "call_count", self.llm_call_count)
        return AnalysisResult(
            problem=problem,
            domain=domain,
            problem_type="type1",
            route_taken="direct-low-risk",
            fractal_depth=0,
            total_llm_calls=total_llm_calls,
            root_problem="Answer the directly verifiable low-risk arithmetic question.",
            specialist_proposal=answer,
            confidence=99.0,
            verdict="accept",
            recommendations=["Use the direct answer; no deeper AOCS route was needed."],
        )

    @staticmethod
    def _looks_like_simple_arithmetic(problem: str) -> bool:
        return bool(re.search(r"\b\d+\s*(?:\+|-|\*|/|x|X)\s*\d+\b", problem))

    @staticmethod
    def _solve_simple_arithmetic(problem: str) -> str | None:
        """Safely solve a single two-number arithmetic expression."""
        match = re.search(r"\b(-?\d+)\s*(\+|-|\*|/|x|X)\s*(-?\d+)\b", problem)
        if not match:
            return None

        left = int(match.group(1))
        op = match.group(2)
        right = int(match.group(3))

        if op == "+":
            value = left + right
        elif op == "-":
            value = left - right
        elif op in ("*", "x", "X"):
            value = left * right
        elif op == "/":
            if right == 0:
                return "undefined: division by zero"
            value = left / right
        else:
            return None

        if isinstance(value, float) and value.is_integer():
            value = int(value)
        return str(value)

    async def _run_phase0(self, problem: str, domain: str) -> Phase0Result:
        """Execute Phase 0: Parser → Multi-Framer → Assumptions → Uncertainty → Root → Deep Test."""
        # Step 1: Parser
        parsed = parse(problem, domain)
        self.blackboard.store("phase0:parsed", parsed[:200])

        # Step 2: Multi-Framer (1 LLM call)
        framer = MultiFramer(self.router)
        interpretations = await framer.generate(problem, domain)
        self._count_call()
        self.blackboard.store("phase0:interpretations", len(interpretations))

        # Step 3: Assumption Mapper (pure code)
        mapper = AssumptionMapper()
        assumptions = mapper.extract(interpretations, domain, problem)
        self.blackboard.store_assumptions(assumptions)

        # Step 4: Uncertainty Quantifier (pure code)
        uncertainties = quantify(assumptions)

        # Step 5: Root Problem (1 LLM call)
        interp_summary = "\n".join(f"- {i.label}: {i.root_cause}" for i in interpretations)
        extractor = RootProblemExtractor(self.router)
        root_problem = await extractor.extract(problem, parsed, interp_summary)
        self._count_call()
        self.blackboard.store("phase0:root_problem", root_problem)

        # Step 6: Deep Test (1 LLM call)
        deep_test = await DeepTest(self.router).run(root_problem, parsed)
        self._count_call()
        self.blackboard.store("phase0:deep_test", deep_test.passed)

        return Phase0Result(
            parsed_problem=parsed,
            interpretations=interpretations,
            assumptions=assumptions,
            uncertainties=uncertainties,
            root_problem=root_problem,
            deep_test=deep_test,
        )

    @staticmethod
    def _determine_verdict(
        confidence: float,
        gates: list[GateResult],
        observer: ObserverResult | None,
    ) -> str:
        """Determine final verdict based on all checks."""
        failed_gates = [g for g in gates if not g.passed]
        if observer and (observer.groupthink_detected or observer.overconfidence_detected):
            if confidence < 80:
                return "reject"
            return "flag_for_review"
        if len(failed_gates) >= 3:
            return "reject"
        if confidence >= 95:
            return "accept"
        return "flag_for_review"

    @staticmethod
    def _build_recommendations(verdict: str, audit: AuditResult) -> list[str]:
        recs = []
        if verdict == "reject":
            recs.append("Return to Phase 0: reframe the problem completely")
            recs.append("Consider re-classification to a different Type")
        if audit.contradictions:
            recs.append(f"Resolve contradictions: {audit.contradictions[0]}")
        if audit.unverified_assumptions:
            recs.append(f"Verify assumptions: {audit.unverified_assumptions[0]}")
        if not recs:
            recs.append("Proceed with the proposed solution with stated confidence")
        return recs
