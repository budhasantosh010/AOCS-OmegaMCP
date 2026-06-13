"""7.2 Type 2 Pipe — High-Stakes Triad (5 LLM calls)."""

from aocs_mcp.router import LLMRouter
from aocs_mcp.pipeline.models import (
    Phase0Result, Phase1Result, SpecialistOutput, RedTeamOutput,
    ContrarianOutput, JudgeVerdict, Type2Result,
)
from aocs_mcp.agents.specialist import Specialist
from aocs_mcp.agents.red_team import RedTeam
from aocs_mcp.agents.contrarian import Contrarian
from aocs_mcp.agents.deception_detector import DeceptionDetector
from aocs_mcp.agents.judge import Judge


class Type2Pipe:
    """High-Stakes Triad — 5 sequential LLM calls, blind where required."""

    def __init__(self, router: LLMRouter):
        self.router = router

    async def run(
        self,
        phase0: Phase0Result,
        phase1: Phase1Result | None = None,
    ) -> Type2Result:
        # Step 1: Specialist (1 LLM call)
        specialist = await Specialist(self.router).run(
            problem=phase0.parsed_problem,
            root_problem=phase0.root_problem,
            assumptions=phase0.assumptions,
        )

        # Step 2: Red Team — blind to specialist's internal reasoning,
        #            only sees the proposal (1 LLM call)
        red_team = await RedTeam(self.router).challenge(specialist.proposal)

        # Step 3: Contrarian — evaluates both proposals (1 LLM call)
        contrarian = await Contrarian(self.router).evaluate(
            specialist.proposal, red_team.critique,
        )

        # Step 4: Deception Detector — scans all arguments (1 LLM call)
        deception = await DeceptionDetector(self.router).scan(
            specialist.proposal, red_team.critique, contrarian.analysis,
        )

        # Step 5: Judge — blind evaluation, doesn't know roles (1 LLM call)
        judge = await Judge(self.router).evaluate(
            specialist.proposal, red_team.critique, contrarian.analysis,
        )

        return Type2Result(
            specialist=specialist,
            red_team=red_team,
            contrarian=contrarian,
            deception_flags=deception,
            judge=judge,
        )
