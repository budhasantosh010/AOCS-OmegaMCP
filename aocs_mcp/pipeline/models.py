"""Pydantic models for all AOCS‑Ω data structures."""

from pydantic import BaseModel
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


# ─── Phase 1 Models ───────────────────────────────────────────

class ScoredProblem(BaseModel):
    name: str
    impact: int = 0
    leverage: int = 0
    urgency: int = 0
    learning: int = 0
    weighted_score: float = 0.0
    zone: Literal["Noise", "Small", "Big", "Critical"] = "Noise"


class Phase1Result(BaseModel):
    sub_problems: list[ScoredProblem] = []
    top_problem: ScoredProblem | None = None


# ─── Classification Model ─────────────────────────────────────

class Classification(BaseModel):
    problem_type: Literal["type1", "type2", "type3"] = "type2"
    risk_level: Literal["low", "medium", "high", "critical"] = "medium"
    fractal_depth: int = 0
    reasoning: str = ""


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


# ─── Type Pipe Results ────────────────────────────────────────

class Type1Result(BaseModel):
    specialist: SpecialistOutput = SpecialistOutput()
    verified: bool = False
    prover: ProverOutput = ProverOutput()


class Type2Result(BaseModel):
    specialist: SpecialistOutput = SpecialistOutput()
    red_team: RedTeamOutput = RedTeamOutput()
    contrarian: ContrarianOutput = ContrarianOutput()
    deception_flags: list[str] = []
    judge: JudgeVerdict = JudgeVerdict()


class Type3Result(BaseModel):
    lens_observations: list[str] = []
    first_principles: str = ""
    hypotheses: list[str] = []
    survivors: list[str] = []
    weirdness_reserve: list[str] = []
    anomalies: list[str] = []


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


# ─── Flywheel Model ───────────────────────────────────────────

class FlywheelEntry(BaseModel):
    heuristic: str = ""
    error_type: str | None = None
    pattern: str = ""
    success: bool = False


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

    # Verification
    quality_gates: list[GateResult] = []
    observer_check: ObserverResult | None = None
    shadow_check: ShadowResult | None = None
    memory_audit: AuditResult | None = None

    # Final
    confidence: float = 0.0
    verdict: str = "flag_for_review"
    recommendations: list[str] = []
