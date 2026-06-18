"""Blackboard — structured knowledge base with provenance + confidence."""

import json
import os
import time

from aocs_mcp.pipeline.models import Assumption


class Blackboard:
    """Structured KB: each claim has provenance, confidence, and decay."""

    def __init__(self, storage_dir: str | None = None):
        self._entries: list[dict] = []
        self._storage_dir = storage_dir

    def store(
        self,
        key: str,
        value: object,
        provenance: str = "LLM-Hypothesized",
        confidence: float = 0.5,
    ) -> None:
        """Store a result with provenance metadata."""
        self._entries.append({
            "key": key,
            "value": self._serializable_value(value),
            "type": type(value).__name__,
            "provenance": provenance,
            "confidence": max(0.0, min(1.0, confidence)),
            "timestamp": time.time(),
        })

    @staticmethod
    def _serializable_value(value: object):
        if hasattr(value, "model_dump"):
            return value.model_dump()
        if isinstance(value, (str, int, float, bool, list, dict)) or value is None:
            return value
        return str(value)

    def store_assumptions(self, assumptions: list[Assumption]) -> None:
        for a in assumptions:
            self.store(
                key="assumption",
                value=a.statement,
                provenance=a.provenance,
                confidence=a.certainty,
            )

    def get(self, key: str, limit: int = 10) -> list[dict]:
        """Get entries by key, most recent first."""
        entries = [e for e in self._entries if e["key"] == key]
        entries.sort(key=lambda x: x["timestamp"], reverse=True)
        return entries[:limit]

    def all(self) -> list[dict]:
        return list(self._entries)

    def apply_decay(self, half_life_hours: float = 24.0) -> None:
        """Apply source decay — older claims lose confidence."""
        now = time.time()
        for entry in self._entries:
            age_hours = (now - entry["timestamp"]) / 3600
            if age_hours > 0:
                decay = 0.5 ** (age_hours / half_life_hours)
                entry["confidence"] = max(0.0, entry["confidence"] * decay)

    def save(self, path: str | None = None) -> None:
        target = path or self._storage_dir
        if target:
            os.makedirs(os.path.dirname(target) if "." in os.path.basename(target) else target, exist_ok=True)
            with open(target if "." in os.path.basename(target) else os.path.join(target, "blackboard.json"), "w") as f:
                json.dump(self._entries, f, indent=2)

    def load(self, path: str) -> None:
        if os.path.isfile(path):
            with open(path) as f:
                self._entries = json.load(f)

    def summary(self) -> str:
        """Produce a readable summary of all entries."""
        entries = self.all()
        if not entries:
            return "Blackboard is empty."

        lines = [f"Blackboard: {len(entries)} entries"]
        for e in entries[:20]:
            value = str(e["value"])
            lines.append(
                f"  [{e['key']}] {value[:80]} "
                f"(confidence: {e['confidence']:.0%}, provenance: {e['provenance']})"
            )
        return "\n".join(lines)
