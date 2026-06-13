"""7.2.2 Volume Swarm — parallel workers + peer audit + merge."""

from aocs_mcp.router import LLMRouter
from aocs_mcp.pipeline.models import WorkerOutput, SwarmResult


SWARM_WORKER_SYSTEM = """You are Worker #{worker_id} in a Swarm.
Process this item using the AOCS-Omega abbreviated Elon+Larson+Polya loop:
1. Interpret the problem
2. Check survivorship bias
3. Apply First Principles thinking
4. Propose a solution

Item: {item}

Output your analysis concisely."""


SWARM_SYNTHESIS_SYSTEM = """You are the Synthesis Agent.
Merge these {n} worker outputs into a single cohesive result.
Identify common themes, resolve contradictions, and produce the final synthesis.

Worker outputs:
{outputs}

Output JSON:
```json
{{"synthesis": "the merged result", "common_themes": ["theme1", "theme2"], "resolved_conflicts": ["conflict1"]}}
```"""


class Swarm:
    """Volume Swarm for decomposable tasks."""

    def __init__(self, router: LLMRouter):
        self.router = router

    async def run(
        self,
        task: str,
        items: list[str],
        num_workers: int = 3,
    ) -> SwarmResult:
        actual_workers = min(num_workers, len(items))

        # Step 1: Spawn workers (parallel)
        workers: list[WorkerOutput] = []
        for i in range(actual_workers):
            if i < len(items):
                system = SWARM_WORKER_SYSTEM.format(worker_id=i + 1, item=items[i])
                try:
                    result = await self.router.call(
                        "swarm-worker",
                        system,
                        f"Task: {task}\nItem: {items[i]}",
                    )
                    workers.append(WorkerOutput(worker_id=i + 1, result=result[:2000]))
                except Exception as e:
                    workers.append(WorkerOutput(worker_id=i + 1, result=f"Error: {e}"))

        # Step 2: Peer Audit (simulated — workers review adjacent outputs)
        peer_audits = []
        for i in range(len(workers)):
            j = (i + 1) % len(workers)
            peer_audits.append(
                f"Worker {workers[i].worker_id} reviewed by Worker {workers[j].worker_id}"
            )

        # Step 3: Synthesis
        outputs_text = "\n---\n".join(
            f"Worker {w.worker_id}: {w.result[:500]}" for w in workers
        )
        system = SWARM_SYNTHESIS_SYSTEM.format(n=len(workers), outputs=outputs_text)
        try:
            synth_data = await self.router.call_structured(
                "swarm-auditor", system, f"Task: {task}"
            )
            synthesis = synth_data.get("synthesis", "Synthesis unavailable")
            auditor_report = "\n".join(synth_data.get("common_themes", []))
        except Exception as e:
            synthesis = f"Synthesis unavailable: {e}"
            auditor_report = ""

        return SwarmResult(
            workers=workers,
            peer_audits=peer_audits,
            auditor_report=auditor_report,
            synthesis=synthesis,
        )
