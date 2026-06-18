"""Universal goal-achievement assembly from first principles."""

from aocs_mcp.pipeline.models import (
    Classification,
    GoalAchievementResult,
    GoalRole,
)
from aocs_mcp.router import LLMRouter


ASSEMBLY_SYSTEM = """You are the AOCS-Omega Universal Goal Assembly Agent.
Build a complete machine for the goal:
1. Define its single functional job from start to desired end.
2. Discover the goal-specific roles without using a fixed generic role list.
3. Identify existing real-world pieces for each role.
4. Connect roles into a closed loop with a feedback role.
5. Define a crude first version that closes the loop.

Output JSON:
{
  "single_job": "",
  "starting_point": "",
  "desired_end_point": "",
  "roles": [
    {
      "name": "",
      "function": "",
      "current_piece": "",
      "input": "",
      "output": "",
      "cost_share": 0
    }
  ],
  "closed_loop": [],
  "feedback_role": "",
  "crude_working_version": "",
  "completed_loop": false
}"""


INEFFICIENCY_SYSTEM = """You are the AOCS-Omega Inefficiency Hunter.
Measure role/connection waste in the currency relevant to the goal.
Identify the largest waste generator whose replacement collapses collateral
waste. Replace it with an outcome-equivalent architecture and recalculate cost.

Output JSON:
{
  "root_inefficiency": "",
  "replacement_architecture": "",
  "cost_before": 0,
  "cost_after": 0
}"""


class UniversalGoalProtocol:
    def __init__(self, router: LLMRouter):
        self.router = router

    @staticmethod
    def applies(problem: str, classification: Classification) -> bool:
        if classification.problem_type != "type3":
            return False
        text = problem.lower()
        goal_terms = (
            "build ",
            "create ",
            "achieve ",
            "complete system",
            "machine",
            "end-to-end",
            "closed loop",
        )
        return any(term in text for term in goal_terms)

    async def run(self, problem: str) -> GoalAchievementResult:
        assembly = await self.router.call_structured(
            "universal-goal-assembly",
            ASSEMBLY_SYSTEM,
            problem,
        )
        roles = [
            GoalRole(
                name=str(item.get("name", "")),
                function=str(item.get("function", "")),
                current_piece=str(item.get("current_piece", "")),
                input=str(item.get("input", "")),
                output=str(item.get("output", "")),
                cost_share=self._number(item.get("cost_share")),
            )
            for item in assembly.get("roles", [])
            if isinstance(item, dict) and item.get("name")
        ]

        inefficiency = await self.router.call_structured(
            "inefficiency-hunter",
            INEFFICIENCY_SYSTEM,
            (
                f"Goal: {problem}\n"
                f"Single job: {assembly.get('single_job', '')}\n"
                f"Roles: {[role.model_dump() for role in roles]}\n"
                f"Closed loop: {assembly.get('closed_loop', [])}"
            ),
        )

        return GoalAchievementResult(
            applies=True,
            single_job=str(assembly.get("single_job", "")),
            starting_point=str(assembly.get("starting_point", "")),
            desired_end_point=str(assembly.get("desired_end_point", "")),
            roles=roles,
            closed_loop=[
                str(item) for item in assembly.get("closed_loop", [])
            ],
            feedback_role=str(assembly.get("feedback_role", "")),
            crude_working_version=str(
                assembly.get("crude_working_version", "")
            ),
            root_inefficiency=str(
                inefficiency.get("root_inefficiency", "")
            ),
            replacement_architecture=str(
                inefficiency.get("replacement_architecture", "")
            ),
            cost_before=self._number(inefficiency.get("cost_before")),
            cost_after=self._number(inefficiency.get("cost_after")),
            completed_loop=bool(assembly.get("completed_loop", False)),
        )

    @staticmethod
    def _number(value) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
