"""AOCS‑Ω FastMCP Server — all tool registrations."""

import os
from mcp.server.fastmcp import FastMCP

from aocs_mcp.config import Config
from aocs_mcp.router import LLMRouter
from aocs_mcp.pipeline.models import (
    AnalysisResult, Phase0Result, Classification, Type2Result,
    SpecialistOutput, RedTeamOutput, JudgeVerdict,
    GateResult, BreakthroughResult, SwarmResult,
    Assumption, ScoredProblem,
)
from aocs_mcp.pipeline.orchestrator import AOCSOrchestrator
from aocs_mcp.phase0.parser import parse
from aocs_mcp.phase0.multi_framer import MultiFramer
from aocs_mcp.phase0.assumptions import AssumptionMapper
from aocs_mcp.phase0.uncertainty import quantify
from aocs_mcp.phase0.root_problem import RootProblemExtractor
from aocs_mcp.phase0.deep_test import DeepTest
from aocs_mcp.phase1.scorer import Phase1Runner
from aocs_mcp.routing.classifier import classify
from aocs_mcp.routing.type2_pipe import Type2Pipe
from aocs_mcp.routing.swarm import Swarm
from aocs_mcp.agents.specialist import Specialist
from aocs_mcp.agents.red_team import RedTeam
from aocs_mcp.agents.contrarian import Contrarian
from aocs_mcp.agents.deception_detector import DeceptionDetector
from aocs_mcp.agents.judge import Judge
from aocs_mcp.agents.prover import Prover
from aocs_mcp.quality.gates import QualityGates
from aocs_mcp.quality.observer import Observer
from aocs_mcp.quality.shadow_orch import ShadowOrchestrator
from aocs_mcp.breakthrough.analogical_mining import AnalogicalMining
from aocs_mcp.breakthrough.higher_dimension import HigherDimension
from aocs_mcp.breakthrough.future_backcast import FutureBackcast


# ── Server Setup ──────────────────────────────────────────────

def _resolve_config_dir() -> str:
    """Find the config directory relative to this file's location."""
    this_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(this_dir)
    return os.path.join(project_root, "config")


config_dir = _resolve_config_dir()
config = Config(config_dir=config_dir)
router = LLMRouter(config)

mcp = FastMCP("aocs-omega")


# ── Tool: Full Orchestrator ───────────────────────────────────

@mcp.tool()
async def aocs_analyze(
    problem: str,
    domain: str = "software",
    risk: str = "medium",
    fractal_depth: int = 0,
    context: str | None = None,
    max_sub_agents: int = 10,
) -> AnalysisResult:
    """Full AOCS‑Ω pipeline: Phase 0 → Phase 1 → Classify → Route → Execute → Verify → Report.

    - problem: The raw problem or request to analyze
    - domain: Domain context (software, hardware, business, etc.)
    - risk: Risk level (low, medium, high, critical)
    - fractal_depth: Depth of recursive self-challenge (0-3)
    - context: Additional context (logs, error messages, etc.)
    - max_sub_agents: Maximum LLM sub-agent calls allowed
    """
    orchestrator = AOCSOrchestrator(router, config)
    return await orchestrator.analyze(
        problem=problem,
        domain=domain,
        risk=risk,
        fractal_depth=fractal_depth if fractal_depth > 0 else None,
        context=context,
        max_sub_agents=max_sub_agents,
    )


# ── Tool: Classify ────────────────────────────────────────────

@mcp.tool()
async def aocs_classify(
    problem: str,
    domain: str = "software",
) -> Classification:
    """Classify problem as Type 1 (Known), Type 2 (Partially Known), or Type 3 (Unknown/Discovery)."""
    # Do a minimal Phase 0 to inform classification
    from aocs_mcp.pipeline.models import Phase0Result, DeepTestResult
    parsed = parse(problem, domain)
    phase0 = Phase0Result(parsed_problem=parsed)
    return classify(problem, phase0)


# ── Tool: Phase 0 Frame ──────────────────────────────────────

@mcp.tool()
async def aocs_phase0_frame(
    problem: str,
    domain: str = "software",
) -> Phase0Result:
    """Full Phase 0 Problem Framing: Parser → Multi-Framer → Assumptions → Uncertainty → Root → Deep Test."""
    parsed = parse(problem, domain)
    framer = MultiFramer(router)
    interpretations = await framer.generate(problem, domain)
    mapper = AssumptionMapper()
    assumptions = mapper.extract(interpretations, domain, problem)
    uncertainties = quantify(assumptions)
    interp_summary = "\n".join(f"- {i.label}: {i.root_cause}" for i in interpretations)
    extractor = RootProblemExtractor(router)
    root_problem = await extractor.extract(problem, parsed, interp_summary)
    deep_test = await DeepTest(router).run(root_problem, parsed)

    return Phase0Result(
        parsed_problem=parsed,
        interpretations=interpretations,
        assumptions=assumptions,
        uncertainties=uncertainties,
        root_problem=root_problem,
        deep_test=deep_test,
    )


# ── Tool: Phase 1 Score ──────────────────────────────────────

@mcp.tool()
async def aocs_phase1_score(
    interpretations: list[str],
) -> list[ScoredProblem]:
    """Score sub-problems on Impact, Leverage, Urgency, and Structural Learning Value (0-10)."""
    from aocs_mcp.pipeline.models import Phase0Result
    from aocs_mcp.pipeline.models import Interpretation as InterpModel
    interps = [InterpModel(label=i, root_cause="", lens="", rationale="") for i in interpretations]
    phase0 = Phase0Result(parsed_problem="", interpretations=interps)
    result = Phase1Runner().run(phase0)
    return result.sub_problems


# ── Tool: Type 2 Triad ───────────────────────────────────────

@mcp.tool()
async def aocs_run_type2(
    problem: str,
    root_problem: str = "",
    assumptions: list[str] | None = None,
) -> Type2Result:
    """Full Type 2 High-Stakes Triad: Specialist → Red Team → Contrarian → Deception Detector → Judge."""
    from aocs_mcp.pipeline.models import Phase0Result, Phase1Result
    from aocs_mcp.pipeline.models import Assumption as AssumptionModel
    a_list = [AssumptionModel(statement=a) for a in (assumptions or [])]
    phase0 = Phase0Result(
        parsed_problem=problem,
        root_problem=root_problem or problem,
        assumptions=a_list,
    )
    pipe = Type2Pipe(router)
    return await pipe.run(phase0)


# ── Tool: Specialist ─────────────────────────────────────────

@mcp.tool()
async def aocs_specialist(
    problem: str,
    root_problem: str = "",
    assumptions: list[str] | None = None,
) -> SpecialistOutput:
    """Type 2 Specialist Builder — full Elon+Larson+Polya loop. 1 LLM call."""
    from aocs_mcp.pipeline.models import Assumption as AssumptionModel
    a_list = [AssumptionModel(statement=a) for a in (assumptions or [])]
    agent = Specialist(router)
    return await agent.run(
        problem=problem,
        root_problem=root_problem or problem,
        assumptions=a_list,
    )


# ── Tool: Red Team ───────────────────────────────────────────

@mcp.tool()
async def aocs_red_team(proposal: str) -> str:
    """Adversarial Red Team — challenges every assumption. 1 LLM call."""
    result = await RedTeam(router).challenge(proposal)
    return result.critique


# ── Tool: Contrarian ─────────────────────────────────────────

@mcp.tool()
async def aocs_contrarian(proposal: str, critique: str) -> str:
    """Truth-seeker evaluation of proposal and critique. 1 LLM call."""
    result = await Contrarian(router).evaluate(proposal, critique)
    return result.analysis


# ── Tool: Deception Detector ──────────────────────────────────

@mcp.tool()
async def aocs_deception_detector(
    specialist: str,
    red_team: str,
    contrarian: str,
) -> list[str]:
    """Scan arguments for rhetorical manipulation. 1 LLM call."""
    detector = DeceptionDetector(router)
    return await detector.scan(specialist, red_team, contrarian)


# ── Tool: Judge ──────────────────────────────────────────────

@mcp.tool()
async def aocs_judge(
    proposal: str,
    critique: str,
    contrarian: str,
    deception_flags: list[str] | None = None,
) -> JudgeVerdict:
    """Neutral blind evaluation with confidence score (0-100). 1 LLM call."""
    agent = Judge(router)
    return await agent.evaluate(proposal, critique, contrarian)


# ── Tool: Quality Gates ──────────────────────────────────────

@mcp.tool()
async def aocs_quality_gates(
    solution: str,
    risk: str = "medium",
) -> list[GateResult]:
    """Apply all 10 quality gates to a proposed solution. Returns pass/fail per gate."""
    from aocs_mcp.pipeline.models import Type2Result, SpecialistOutput, RedTeamOutput, ContrarianOutput, JudgeVerdict
    dummy = Type2Result(
        specialist=SpecialistOutput(proposal=solution),
        judge=JudgeVerdict(confidence=50.0),
    )
    gates = QualityGates(router)
    return await gates.run(dummy, risk)


# ── Tool: Breakthrough ───────────────────────────────────────

@mcp.tool()
async def aocs_breakthrough(
    problem: str,
    method: str = "analogical",
) -> BreakthroughResult:
    """Breakthrough protocol to escape cognitive deadlock.

    Methods:
    - analogical: Cross-domain analogical mining (Elon's 'toy car' method)
    - reframe: Higher-dimension frame escape
    - backcast: Future retrospective from 2035
    """
    protocols = {
        "analogical": AnalogicalMining(router),
        "reframe": HigherDimension(router),
        "backcast": FutureBackcast(router),
    }
    worker = protocols.get(method)
    if not worker:
        raise ValueError(f"Unknown method: {method}. Choose: {list(protocols.keys())}")
    return await worker.run(problem)


# ── Tool: Swarm ───────────────────────────────────────────────

@mcp.tool()
async def aocs_swarm(
    task: str,
    items: list[str],
    num_workers: int = 3,
) -> SwarmResult:
    """Volume Swarm: N Workers → Peer Audit → Independent Auditor → Synthesis."""
    swarm = Swarm(router)
    return await swarm.run(task, items, num_workers)


# ── Tool: Observer ───────────────────────────────────────────

@mcp.tool()
async def aocs_observer(
    specialist_confidence: float = 50.0,
    judge_confidence: float = 50.0,
    contrarian_agreement: str = "unknown",
    deception_flags: list[str] | None = None,
) -> str:
    """Check for groupthink and overconfidence in the pipeline."""
    observer = Observer(router)
    result = await observer.check(
        specialist_confidence=specialist_confidence,
        judge_confidence=judge_confidence,
        contrarian_agreement=contrarian_agreement,
        deception_flags=deception_flags or [],
    )
    return result.notes or "No issues detected"


# ── Tool: Prover ──────────────────────────────────────────────

@mcp.tool()
async def aocs_prover(reasoning: str) -> str:
    """Attempt to formalize and prove claims in the reasoning."""
    prover = Prover(router)
    result = await prover.prove(reasoning)
    proved_count = sum(1 for p in result.proved if p)
    return f"Claims: {len(result.claims)}, Proved: {proved_count}, Unprovable: {len(result.unprovable)}"


# ── Entry Point ──────────────────────────────────────────────

def main() -> None:
    """Start the AOCS‑Ω FastMCP server over stdio."""
    mcp.run("stdio")


if __name__ == "__main__":
    main()
