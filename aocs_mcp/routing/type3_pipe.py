"""Complete Type 3 discovery pipe."""

from aocs_mcp.memory.graveyard import Graveyard
from aocs_mcp.pipeline.models import Type3Result
from aocs_mcp.router import LLMRouter
from aocs_mcp.routing.quest_tracker import QuestTracker


LENSES = [
    "Domain Inference",
    "First Principles",
    "Evidence and Measurement",
    "Systems and Constraints",
    "Safety and Consequences",
]


LENS_SYSTEM = """You are a {lens} expert.
Infer the correct discipline from the problem. Do not assume software.
Identify what this lens notices that other lenses miss.
Output JSON: {{"observations": [], "key_insight": ""}}"""


FIRST_PRINCIPLES_SYSTEM = """Strip away inherited solutions and assumptions.
State truths that must hold regardless of current theories.
Output JSON: {"first_principles": [], "core_truths": []}"""


HYPOTHESIS_SYSTEM = """Generate 3-5 competing models for the unknown.
For each, state its description, supporting evidence, and refuting evidence.
Output JSON: {"hypotheses": [{"name": "", "description": ""}]}"""


MUTATOR_SYSTEM = """Mutate the supplied hypotheses by flipping assumptions,
relaxing constraints, combining unrelated domains, and pushing ideas to limits.
Output JSON: {"mutations": [{"idea": "", "novelty": 0.0}]}"""


PRUNER_SYSTEM = """Prune ideas that violate basic evidence, logic, physical laws,
or feasibility. Preserve a small Protected Weirdness Reserve instead of deleting
every exotic idea. Capture unexplained anomalies.
Output JSON:
{
  "survivors": [],
  "rejected": [{"idea": "", "reason": ""}],
  "weirdness_reserve": [],
  "anomalies": []
}"""


SERENDIPITY_SYSTEM = """Inject high-quality stimuli from unrelated domains and
test whether their structural principles connect to this problem.
Output JSON: {"seeds": [], "connections": []}"""


SIMULATION_SYSTEM = """Run thought experiments or sandbox-style simulations for
the surviving hypotheses. Capture outcomes, failures, and new anomalies.
Output JSON:
{
  "simulations": [{"hypothesis": "", "outcome": "", "status": ""}],
  "anomalies": []
}"""


PARADIGM_SYSTEM = """Evaluate anomaly density. Trigger a paradigm alert when the
current framework fails to explain enough observations.
Output JSON: {"alert": false, "anomaly_density": 0.0, "reason": ""}"""


class Type3Pipe:
    """Execute all Type 3 exploration stages without premature convergence."""

    def __init__(
        self,
        router: LLMRouter,
        max_lens: int = 3,
        graveyard: Graveyard | None = None,
    ):
        self.router = router
        self.max_lens = max_lens
        self.graveyard = graveyard or Graveyard()

    async def run(self, domain: str | None, seed_question: str) -> Type3Result:
        domain_label = domain or "infer from problem; do not assume software"
        lens_observations: list[str] = []

        for lens in LENSES[: self.max_lens]:
            try:
                data = await self.router.call_structured(
                    "type3-lens",
                    LENS_SYSTEM.format(lens=lens),
                    f"Domain: {domain_label}\nProblem: {seed_question}",
                )
                lens_observations.extend(
                    str(item) for item in data.get("observations", [])
                )
            except Exception as exc:
                lens_observations.append(f"[{lens}] unavailable: {exc}")

        first_data = await self.router.call_structured(
            "type3-first-principles",
            FIRST_PRINCIPLES_SYSTEM,
            (
                f"Domain: {domain_label}\nProblem: {seed_question}\n"
                f"Lens observations: {lens_observations}"
            ),
        )
        first_principles_list = [
            str(item) for item in first_data.get("first_principles", [])
        ]
        first_principles = "\n".join(first_principles_list)

        hypothesis_data = await self.router.call_structured(
            "type3-hypothesis",
            HYPOTHESIS_SYSTEM,
            (
                f"Problem: {seed_question}\n"
                f"First principles: {first_principles}\n"
                f"Observations: {lens_observations}"
            ),
        )
        hypotheses = [
            str(item.get("description", ""))
            if isinstance(item, dict)
            else str(item)
            for item in hypothesis_data.get("hypotheses", [])
        ]
        hypotheses = [item for item in hypotheses if item]

        mutation_data = await self.router.call_structured(
            "idea-mutator",
            MUTATOR_SYSTEM,
            f"Problem: {seed_question}\nHypotheses: {hypotheses}",
        )
        mutations = [
            str(item.get("idea", "")) if isinstance(item, dict) else str(item)
            for item in mutation_data.get("mutations", [])
        ]
        mutations = [item for item in mutations if item]

        pruner_data = await self.router.call_structured(
            "ruthless-pruner",
            PRUNER_SYSTEM,
            (
                f"Problem: {seed_question}\n"
                f"Hypotheses: {hypotheses}\nMutations: {mutations}\n"
                f"First principles: {first_principles}"
            ),
        )
        survivors = [str(item) for item in pruner_data.get("survivors", [])]
        rejected = [
            item
            for item in pruner_data.get("rejected", [])
            if isinstance(item, dict)
        ]
        weirdness = [
            str(item) for item in pruner_data.get("weirdness_reserve", [])
        ]
        anomalies = [str(item) for item in pruner_data.get("anomalies", [])]

        for item in rejected:
            self.graveyard.bury(
                str(item.get("idea", "")),
                str(item.get("reason", "Rejected by ruthless pruner")),
                category="type3-pruned",
                assumptions_at_time=first_principles,
            )

        serendipity_data = await self.router.call_structured(
            "serendipity-injector",
            SERENDIPITY_SYSTEM,
            f"Problem: {seed_question}\nSurvivors: {survivors}",
        )
        serendipity_seeds = [
            str(item) for item in serendipity_data.get("seeds", [])
        ]
        serendipity_connections = [
            str(item) for item in serendipity_data.get("connections", [])
        ]

        simulation_data = await self.router.call_structured(
            "thought-simulator",
            SIMULATION_SYSTEM,
            (
                f"Problem: {seed_question}\nSurvivors: {survivors}\n"
                f"Curiosity seeds: {serendipity_seeds}\n"
                f"Connections: {serendipity_connections}"
            ),
        )
        simulations = [
            item
            for item in simulation_data.get("simulations", [])
            if isinstance(item, dict)
        ]
        anomalies.extend(
            str(item) for item in simulation_data.get("anomalies", [])
        )

        paradigm_data = await self.router.call_structured(
            "paradigm-detector",
            PARADIGM_SYSTEM,
            (
                f"Problem: {seed_question}\nAnomalies: {anomalies}\n"
                f"Model count: {len(survivors)}"
            ),
        )
        paradigm_alert = bool(paradigm_data.get("alert", False))
        try:
            anomaly_density = float(paradigm_data.get("anomaly_density", 0.0))
        except (TypeError, ValueError):
            anomaly_density = 0.0
        paradigm_reason = str(paradigm_data.get("reason", ""))

        if paradigm_alert:
            for candidate in self.graveyard.find_candidates(" ".join(anomalies)):
                idea_id = self.graveyard.all().index(candidate)
                resurrected = self.graveyard.resurrect(idea_id)
                if resurrected and resurrected not in survivors:
                    survivors.append(resurrected)

        quests = QuestTracker().create(survivors, weirdness)

        return Type3Result(
            lens_observations=lens_observations,
            first_principles=first_principles,
            hypotheses=hypotheses,
            mutations=mutations,
            survivors=survivors,
            weirdness_reserve=weirdness,
            rejected_ideas=rejected,
            serendipity_seeds=serendipity_seeds,
            serendipity_connections=serendipity_connections,
            simulations=simulations,
            anomalies=anomalies,
            anomaly_density=max(0.0, min(1.0, anomaly_density)),
            paradigm_alert=paradigm_alert,
            paradigm_reason=paradigm_reason,
            quests=quests,
        )
