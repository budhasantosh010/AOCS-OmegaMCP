"""7.1 Type 1 Pipe — Specialist → Deterministic Verifier → Prover."""

from aocs_mcp.router import LLMRouter
from aocs_mcp.pipeline.models import (
    Phase0Result, SpecialistOutput, ProverOutput, Type1Result,
)
from aocs_mcp.agents.specialist import Specialist
from aocs_mcp.agents.prover import Prover


class Type1Pipe:
    """Known system — established path, verifiable answer."""

    def __init__(self, router: LLMRouter):
        self.router = router

    async def run(self, phase0: Phase0Result) -> Type1Result:
        # Step 1: Specialist
        specialist = await Specialist(self.router).run(
            problem=phase0.parsed_problem,
            root_problem=phase0.root_problem,
            assumptions=phase0.assumptions,
        )

        # Step 2: Deterministic Verifier (code — checks constraints)
        verified = self._verify(specialist)

        # Step 3: Prover (LLM — formal claims)
        prover = Prover(self.router)
        prover_result = await prover.prove(specialist.proposal)

        return Type1Result(
            specialist=specialist,
            verified=verified,
            prover=prover_result,
        )

    @staticmethod
    def _verify(specialist: SpecialistOutput) -> bool:
        """Deterministic verification — checks for basic constraints."""
        if not specialist.proposal.strip():
            return False
        if specialist.confidence < 0:
            return False
        return True
