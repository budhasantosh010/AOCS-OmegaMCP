"""Type 1 route: Specialist -> Verifier -> critical TMR -> Prover."""

from aocs_mcp.agents.prover import Prover
from aocs_mcp.agents.tmr import TMR
from aocs_mcp.agents.type1_specialist import Type1Specialist
from aocs_mcp.pipeline.models import Phase0Result, SpecialistOutput, Type1Result
from aocs_mcp.quality.verifier import DeterministicVerifier
from aocs_mcp.router import LLMRouter


class Type1Pipe:
    """Known system with an established, independently verifiable path."""

    def __init__(self, router: LLMRouter):
        self.router = router

    async def run(
        self,
        phase0: Phase0Result,
        risk: str | None = None,
    ) -> Type1Result:
        specialist = await Type1Specialist(self.router).run(
            problem=phase0.parsed_problem,
            root_problem=phase0.root_problem,
            assumptions=phase0.assumptions,
        )
        verification = DeterministicVerifier().verify(specialist)

        tmr_result = None
        if risk == "critical":
            tmr_result = await TMR(self.router).run(
                phase0.root_problem or phase0.parsed_problem,
                specialist.proposal,
            )

        prover_result = await Prover(self.router).prove(specialist.proposal)

        return Type1Result(
            specialist=specialist,
            verified=verification.passed,
            verification=verification,
            prover=prover_result,
            tmr=tmr_result,
        )

    @staticmethod
    def _verify(specialist: SpecialistOutput) -> bool:
        if not specialist.proposal.strip():
            return False
        return specialist.confidence >= 0
