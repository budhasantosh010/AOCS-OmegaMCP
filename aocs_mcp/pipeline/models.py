"""Pydantic models for all AOCS‑Ω data structures."""

from pydantic import BaseModel, Field
from typing import Literal


# ─── Phase 0 Models ───────────────────────────────────────────

class Interpretation(BaseModel):
    label: str
    root_cause: str
    lens: str
    rationale: str


class Assumption(BaseModel):
    statement: str
    certainty: float = 0.5
    provenance: Literal[
        "Reality-Tested", "Sandbox-Simulated", "Proof-Only", "LLM-Hypothesized"
    ] = "LLM-Hypothesized"


class DeepTestResult(BaseModel):
    question_1: str = ""
    question_2: str = ""
    question_3: str = ""
    question_4: str = ""
    passed: bool = False


class Phase0Result(BaseModel):
    parsed_problem: str = ""
    interpretations: list[Interpretation] = []
    assumptions: list[Assumption] = []
    uncertainties: list[Assumption] = []
    root_problem: str = ""
    deep_test: DeepTestResult = DeepTestResult()
    reframe_count: int = 0


# ─── Phase 1 Models ───────────────────────────────────────────

class ScoredProblem(BaseModel):
    name: str
    impact: int = 0
    leverage: int = 0
    urgency: int = 0
    learning: int = 0
    weighted_score: float = 0.0
    zone: Literal["Noise", "Small", "Big", "Critical"] = "Noise"
    rationale: str = ""


class Phase1Result(BaseModel):
    sub_problems: list[ScoredProblem] = []
    top_problem: ScoredProblem | None = None


# ─── Classification Model ─────────────────────────────────────

class Classification(BaseModel):
    problem_type: Literal["type1", "type2", "type3"] = "type2"
    risk_level: Literal["low", "medium", "high", "critical"] = "medium"
    fractal_depth: int = 0
    reasoning: str = ""
    decomposable: bool = False
    chunks: list[str] = Field(default_factory=list)


# ─── Agent Output Models ──────────────────────────────────────

class SpecialistOutput(BaseModel):
    proposal: str = ""
    reasoning: str = ""
    prediction: str = ""
    assumptions: list[str] = []
    confidence: float = 0.0


class RedTeamOutput(BaseModel):
    critique: str = ""
    flaws: list[str] = []
    risk_estimate: str = ""


class ContrarianOutput(BaseModel):
    analysis: str = ""
    agreement_level: str = ""
    alternative_model: str | None = None
    confidence: float = 0.0


class JudgeVerdict(BaseModel):
    confidence: float = 0.0
    decision: Literal["accept", "flag_for_review", "reject"] = "flag_for_review"
    reasoning: str = ""


class ProverOutput(BaseModel):
    claims: list[str] = []
    proved: list[bool] = []
    unprovable: list[str] = []


class TMROutput(BaseModel):
    method_a: str = ""
    method_b: str = ""
    method_c: str = ""
    consensus: bool = False
    disagreements: list[str] = []


class VerificationResult(BaseModel):
    passed: bool = False
    checks: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class FractalChallenge(BaseModel):
    depth: int = 0
    layer: str = ""
    red_team: str = ""
    contrarian: str = ""
    judge: JudgeVerdict | None = None
    observer: str = ""
    shadow: str = ""
    conclusion: str = ""


class FractalResult(BaseModel):
    requested_depth: int = 0
    executed_depth: int = 0
    challenges: list[FractalChallenge] = Field(default_factory=list)
    survived: bool = True
    confidence: float = 0.0


class BlindspotResult(BaseModel):
    missing_perspectives: list[str] = Field(default_factory=list)
    missing_data: list[str] = Field(default_factory=list)
    outsider_view: str = ""
    falsification_conditions: list[str] = Field(default_factory=list)
    simplest_overlooked: str = ""
    recommended_actions: list[str] = Field(default_factory=list)


class KillSwitchResult(BaseModel):
    fired: bool = False
    approach_signature: str = ""
    failure_count: int = 0
    reason: str = ""
    reframed_problem: str | None = None
    reclassified_as: Classification | None = None


class QuestResult(BaseModel):
    name: str = ""
    hypothesis: str = ""
    resource_fraction: float = 0.1
    status: Literal["active", "archived", "resurrected"] = "active"
    progress_notes: list[str] = Field(default_factory=list)
    archived_reason: str | None = None


class BreakFrameworkResult(BaseModel):
    triggered: bool = False
    reason: str = ""
    temporary_structure: str = ""
    reordered_phases: list[str] = Field(default_factory=list)
    temporary_agents: list[str] = Field(default_factory=list)
    verification_sequence: list[str] = Field(default_factory=list)
    proposal: str = ""


class GoalRole(BaseModel):
    name: str
    function: str
    current_piece: str = ""
    input: str = ""
    output: str = ""
    cost_share: float = 0.0


class GoalAchievementResult(BaseModel):
    applies: bool = False
    single_job: str = ""
    starting_point: str = ""
    desired_end_point: str = ""
    roles: list[GoalRole] = Field(default_factory=list)
    closed_loop: list[str] = Field(default_factory=list)
    feedback_role: str = ""
    crude_working_version: str = ""
    root_inefficiency: str = ""
    replacement_architecture: str = ""
    cost_before: float = 0.0
    cost_after: float = 0.0
    completed_loop: bool = False


# ─── Type Pipe Results ────────────────────────────────────────

class Type1Result(BaseModel):
    specialist: SpecialistOutput = SpecialistOutput()
    verified: bool = False
    verification: VerificationResult = VerificationResult()
    prover: ProverOutput = ProverOutput()
    tmr: TMROutput | None = None


class Type2Result(BaseModel):
    specialist: SpecialistOutput = SpecialistOutput()
    red_team: RedTeamOutput = RedTeamOutput()
    contrarian: ContrarianOutput = ContrarianOutput()
    deception_flags: list[str] = []
    judge: JudgeVerdict = JudgeVerdict()
    external_review_hooks: list[str] = Field(default_factory=list)


class Type3Result(BaseModel):
    lens_observations: list[str] = []
    first_principles: str = ""
    hypotheses: list[str] = []
    mutations: list[str] = Field(default_factory=list)
    survivors: list[str] = []
    weirdness_reserve: list[str] = []
    rejected_ideas: list[dict] = Field(default_factory=list)
    serendipity_seeds: list[str] = Field(default_factory=list)
    serendipity_connections: list[str] = Field(default_factory=list)
    simulations: list[dict] = Field(default_factory=list)
    anomalies: list[str] = []
    anomaly_density: float = 0.0
    paradigm_alert: bool = False
    paradigm_reason: str = ""
    quests: list[QuestResult] = Field(default_factory=list)


class WorkerOutput(BaseModel):
    worker_id: int
    result: str = ""


class SwarmResult(BaseModel):
    workers: list[WorkerOutput] = []
    peer_audits: list[str] = []
    auditor_report: str = ""
    synthesis: str = ""


# ─── Quality Gate Models ──────────────────────────────────────

class GateResult(BaseModel):
    gate_number: int
    name: str
    passed: bool
    details: str = ""


class ObserverResult(BaseModel):
    groupthink_detected: bool = False
    overconfidence_detected: bool = False
    chaos_variable_injected: bool = False
    chaos_variable: str = ""
    notes: str = ""


class ShadowResult(BaseModel):
    divergence_detected: bool = False
    original_classification: Classification = Classification()
    shadow_classification: Classification = Classification()
    safe_path: str = ""


class AuditResult(BaseModel):
    contradictions: list[str] = []
    unverified_assumptions: list[str] = []
    corrections: list[str] = []


# ─── Breakthrough Models ──────────────────────────────────────

class BreakthroughResult(BaseModel):
    method: str = ""
    abstract_structure: str = ""
    cross_domain_sources: list[str] = []
    solution_principle: str = ""
    adapted_proposal: str = ""
    reframed_problem: str = ""
    details: dict = Field(default_factory=dict)


# ─── Flywheel Model ───────────────────────────────────────────

class FlywheelEntry(BaseModel):
    heuristic: str = ""
    error_type: str | None = None
    pattern: str = ""
    success: bool = False
    calibration_update: str = ""


# ─── Final Analysis Result ────────────────────────────────────

class AnalysisResult(BaseModel):
    # Metadata
    run_id: str | None = None
    run_dir: str | None = None
    problem: str = ""
    domain: str | None = None
    problem_type: Literal["type1", "type2", "type3"] = "type2"
    route_taken: str = ""
    fractal_depth: int = 0
    total_llm_calls: int = 0
    error: str | None = None
    classification: Classification | None = None
    phase0_reframes: int = 0
    attempt_history: list[dict] = Field(default_factory=list)

    # Phase 0
    root_problem: str = ""
    interpretations: list[Interpretation] = []
    assumptions: list[Assumption] = []
    deep_test_passed: bool = False

    # Phase 1
    top_problem: ScoredProblem | None = None

    # Execution
    specialist_proposal: str | None = None
    red_team_critique: str | None = None
    contrarian_analysis: str | None = None
    deception_flags: list[str] = []
    judge_verdict: JudgeVerdict | None = None
    type1_verified: bool | None = None
    type3_findings: Type3Result | None = None
    swarm_result: SwarmResult | None = None
    verification: VerificationResult | None = None
    prover_result: ProverOutput | None = None
    tmr_result: TMROutput | None = None
    fractal_result: FractalResult | None = None
    blindspot_check: BlindspotResult | None = None
    kill_switch: KillSwitchResult | None = None
    quests: list[QuestResult] = Field(default_factory=list)
    breakthroughs: list[BreakthroughResult] = Field(default_factory=list)
    break_framework: BreakFrameworkResult | None = None
    goal_achievement: GoalAchievementResult | None = None
    paradigm_reframe: dict | None = None
    external_review_hooks: list[str] = Field(default_factory=list)

    # Verification
    quality_gates: list[GateResult] = []
    observer_check: ObserverResult | None = None
    shadow_check: ShadowResult | None = None
    memory_audit: AuditResult | None = None
    blackboard_entries: list[dict] = Field(default_factory=list)
    graveyard_entries: list[dict] = Field(default_factory=list)
    learning_entries: list[FlywheelEntry] = Field(default_factory=list)

    # Final
    confidence: float = 0.0
    verdict: str = "flag_for_review"
    recommendations: list[str] = []
