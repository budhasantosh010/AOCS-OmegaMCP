"""Protect promising Type 3 explorations from premature abandonment."""

from aocs_mcp.pipeline.models import QuestResult


class QuestTracker:
    """Allocate a protected ten-percent exploration slot."""

    def create(
        self,
        survivors: list[str],
        weirdness_reserve: list[str],
    ) -> list[QuestResult]:
        candidate = (
            weirdness_reserve[0]
            if weirdness_reserve
            else survivors[0]
            if survivors
            else None
        )
        if not candidate:
            return []
        return [
            QuestResult(
                name="Protected Type 3 exploration",
                hypothesis=candidate,
                resource_fraction=0.1,
                status="active",
                progress_notes=["Protected from short-term score-based pruning."],
            )
        ]

    @staticmethod
    def archive(quest: QuestResult, reason: str) -> QuestResult:
        quest.status = "archived"
        quest.archived_reason = reason
        quest.progress_notes.append(f"Archived: {reason}")
        return quest

    @staticmethod
    def resurrect(quest: QuestResult, evidence: str) -> QuestResult:
        quest.status = "resurrected"
        quest.archived_reason = None
        quest.progress_notes.append(f"Resurrected because: {evidence}")
        return quest
