"""Memory Auditor — contradiction detection across the blackboard."""

from aocs_mcp.memory.blackboard import Blackboard
from aocs_mcp.pipeline.models import AuditResult


class MemoryAuditor:
    """Checks for contradictions and unverified assumptions in the blackboard."""

    def audit(self, blackboard: Blackboard) -> AuditResult:
        entries = blackboard.all()
        contradictions: list[str] = []
        unverified: list[str] = []
        corrections: list[str] = []

        # Check for contradictory claims
        seen: dict[str, list[dict]] = {}
        for entry in entries:
            key = entry["key"]
            if key not in seen:
                seen[key] = []
            seen[key].append(entry)

        # Find entries with same key but different values
        for key, same_key_entries in seen.items():
            if not key.startswith(("claim:", "fact:", "decision:")):
                continue
            if len(same_key_entries) < 2:
                continue
            values = set(str(e["value"])[:100] for e in same_key_entries)
            if len(values) > 1:
                contradictions.append(
                    f"Multiple values for '{key}': {' vs '.join(list(values)[:3])}"
                )

        # Check for low-confidence entries
        for entry in entries:
            if entry["confidence"] < 0.3:
                unverified.append(
                    f"Low confidence ({entry['confidence']:.0%}): {str(entry['value'])[:80]}"
                )

        # Generate corrections
        for c in contradictions[:3]:
            corrections.append(f"Needs resolution: {c}")
        for u in unverified[:3]:
            corrections.append(f"Needs verification: {u}")

        return AuditResult(
            contradictions=contradictions,
            unverified_assumptions=unverified,
            corrections=corrections,
        )
