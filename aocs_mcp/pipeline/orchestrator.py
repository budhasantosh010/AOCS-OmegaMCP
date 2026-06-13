"""Pipeline Orchestrator — chains all AOCS phases deterministically."""

from aocs_mcp.router import LLMRouter
from aocs_mcp.config import Config
from aocs_mcp.pipeline.models import (
    Phase0Result, Phase1Result, Classification,
    Type2Result, AnalysisResult, GateResult,
    ObserverResult, ShadowResult, AuditResult,
    ScoredProblem, JudgeVerdict, Assumption, Interpretation, DeepTestResult,
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
        max_sub_agents: int = 10,
    ) -> AnalysisResult:
        """Run the full AOCS pipeline from start to finish."""
        self.llm_call_count = 0

        try:
            # === PHASE 0: Problem Framing ===
            phase0 = await self._run_phase0(problem, domain)

            # === PHASE 1: Scoring ===
            phase1 = Phase1Runner().run(phase0)
            self.blackboard.store("phase1", phase1.top_problem.model_dump() if phase1.top_problem else "none")

            # === CLASSIFICATION ===
            classification = classify(problem, phase0)
            self.blackboard.store("classification", classification.model_dump())
            fd = fractal_depth if fractal_depth is not None else classification.fractal_depth

            # === ROUTING + EXECUTION ===
            result: Type2Result | None = None
            route_taken = ""

            if classification.problem_type == "type1":
                route_taken = "type1"
            elif classification.problem_type == "type3":
                route_taken = "type3"
            else:
                route_taken = "type2"
                result = await Type2Pipe(self.router).run(phase0, phase1)

            # === QUALITY GATES ===
            quality_gates: list[GateResult] = []
            observer_result: ObserverResult | None = None
            if result:
                gates_obj = QualityGates(self.router)
                quality_gates = await gates_obj.run(result, classification.risk_level)

                # Observer check
                observer = Observer(self.router)
                observer_result = await observer.check(
                    specialist_confidence=result.specialist.confidence,
                    judge_confidence=result.judge.confidence,
                    contrarian_agreement=result.contrarian.agreement_level,
                    deception_flags=result.deception_flags,
                )
                self._count_call()

            # === SHADOW ORCHESTRATOR ===
            shadow = await ShadowOrchestrator(self.router).check(problem, classification)
            self._count_call()

            # === MEMORY AUDIT ===
            audit = MemoryAuditor().audit(self.blackboard)

            # === FINAL VERDICT ===
            confidence = result.judge.confidence if result else 50.0
            verdict_str = self._determine_verdict(confidence, quality_gates, observer_result)

            # === FLYWHEEL ===
            analysis_result = AnalysisResult(
                problem=problem,
                domain=domain,
                problem_type=classification.problem_type,
                route_taken=route_taken,
                fractal_depth=fd,
                total_llm_calls=self.llm_call_count,
                root_problem=phase0.root_problem,
                interpretations=phase0.interpretations,
                assumptions=phase0.assumptions,
                deep_test_passed=phase0.deep_test.passed,
                top_problem=phase1.top_problem,
                specialist_proposal=result.specialist.proposal if result else None,
                red_team_critique=result.red_team.critique if result else None,
                contrarian_analysis=result.contrarian.analysis if result else None,
                deception_flags=result.deception_flags if result else [],
                judge_verdict=result.judge if result else None,
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
                error=str(e),
                verdict="error",
                recommendations=[f"Pipeline error: {e}"],
            )

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
