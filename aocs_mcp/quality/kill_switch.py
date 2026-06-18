"""Stop repeating an approach after two failed quality attempts."""

from aocs_mcp.pipeline.models import KillSwitchResult


class KillSwitch:
    def __init__(self, max_failures: int = 2):
        self.max_failures = max(1, max_failures)
        self._failures: dict[str, list[str]] = {}

    def record_failure(self, approach_signature: str, reason: str) -> KillSwitchResult:
        reasons = self._failures.setdefault(approach_signature, [])
        reasons.append(reason)
        fired = len(reasons) >= self.max_failures
        return KillSwitchResult(
            fired=fired,
            approach_signature=approach_signature,
            failure_count=len(reasons),
            reason=" | ".join(reasons),
        )

    def can_attempt(self, approach_signature: str) -> bool:
        return len(self._failures.get(approach_signature, [])) < self.max_failures

    def failure_count(self, approach_signature: str) -> int:
        return len(self._failures.get(approach_signature, []))
