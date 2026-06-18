"""Volume swarm with workers, peer audits, independent audit, and synthesis."""

from aocs_mcp.pipeline.models import SwarmResult, WorkerOutput
from aocs_mcp.router import LLMRouter


WORKER_SYSTEM = """You are an AOCS-Omega swarm worker.
Analyze only your assigned item with an abbreviated Elon+Larson+Polya loop.
State assumptions, evidence gaps, and a concrete result."""


PEER_AUDIT_SYSTEM = """You are an AOCS-Omega peer auditor.
Review another worker's output. Identify errors, missing evidence, and edge cases.
Output JSON: {"audit": "specific audit"}"""


INDEPENDENT_AUDIT_SYSTEM = """You are the independent AOCS-Omega swarm auditor.
Spot-check the complete worker set from a different model perspective.
Output JSON: {"auditor_report": "independent audit"}"""


SYNTHESIS_SYSTEM = """You are the AOCS-Omega swarm synthesis agent.
Merge worker outputs only after considering peer and independent audits.
Output JSON:
{
  "synthesis": "merged result",
  "common_themes": [],
  "resolved_conflicts": []
}"""


class Swarm:
    """Execute the complete decomposable-task swarm protocol."""

    def __init__(self, router: LLMRouter):
        self.router = router

    async def run(
        self,
        task: str,
        items: list[str],
        num_workers: int = 3,
    ) -> SwarmResult:
        actual_workers = min(max(num_workers, 0), len(items))
        workers: list[WorkerOutput] = []

        for index in range(actual_workers):
            try:
                output = await self.router.call(
                    "swarm-worker",
                    WORKER_SYSTEM,
                    f"Task: {task}\nAssigned item: {items[index]}",
                )
            except Exception as exc:
                output = f"Error: {exc}"
            workers.append(WorkerOutput(worker_id=index + 1, result=output[:4000]))

        peer_audits: list[str] = []
        for index, worker in enumerate(workers):
            reviewer = workers[(index + 1) % len(workers)] if workers else worker
            data = await self.router.call_structured(
                "swarm-peer-audit",
                PEER_AUDIT_SYSTEM,
                (
                    f"Reviewer identity: worker {reviewer.worker_id}\n"
                    f"Output to audit from worker {worker.worker_id}:\n{worker.result}"
                ),
            )
            peer_audits.append(str(data.get("audit", "")))

        worker_text = "\n\n".join(
            f"Worker {worker.worker_id}:\n{worker.result}" for worker in workers
        )
        audit_data = await self.router.call_structured(
            "swarm-auditor",
            INDEPENDENT_AUDIT_SYSTEM,
            f"Task: {task}\n\n{worker_text}",
        )
        auditor_report = str(audit_data.get("auditor_report", ""))

        synthesis_data = await self.router.call_structured(
            "swarm-synthesis",
            SYNTHESIS_SYSTEM,
            (
                f"Task: {task}\n\n"
                f"Worker outputs:\n{worker_text}\n\n"
                f"Peer audits:\n{peer_audits}\n\n"
                f"Independent audit:\n{auditor_report}"
            ),
        )

        return SwarmResult(
            workers=workers,
            peer_audits=peer_audits,
            auditor_report=auditor_report,
            synthesis=str(synthesis_data.get("synthesis", "")),
        )
