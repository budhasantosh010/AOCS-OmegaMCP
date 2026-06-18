"""Graveyard — archive rejected ideas for potential resurrection."""

import json
import os
import re
import time
from typing import Any


class Graveyard:
    """Archives rejected ideas with failure reasons.

    Supports resurrection: if assumptions change, buried ideas can be revived.
    """

    def __init__(self, storage_path: str | None = None):
        self._dead: list[dict[str, Any]] = []
        self._storage_path = storage_path

    def bury(
        self,
        idea: str,
        reason: str,
        category: str = "rejected",
        assumptions_at_time: str = "",
    ) -> None:
        """Archive a rejected idea."""
        self._dead.append({
            "idea": idea,
            "reason": reason,
            "category": category,
            "assumptions": assumptions_at_time,
            "buried_at": time.time(),
            "resurrected": False,
        })

    def resurrect(self, idea_id: int) -> str | None:
        """Resurrect a buried idea. Returns the idea text or None."""
        if 0 <= idea_id < len(self._dead):
            entry = self._dead[idea_id]
            if not entry["resurrected"]:
                entry["resurrected"] = True
                return entry["idea"]
        return None

    def find_candidates(self, new_assumptions: str) -> list[dict]:
        """Find ideas whose failed assumptions may now be invalid."""
        new_terms = self._significant_terms(new_assumptions)
        candidates = []
        for entry in self._dead:
            prior_terms = self._significant_terms(
                f"{entry.get('assumptions', '')} {entry.get('reason', '')}"
            )
            if not entry["resurrected"] and new_terms.intersection(prior_terms):
                candidates.append(entry)
        return candidates[:5]

    @staticmethod
    def _significant_terms(text: str) -> set[str]:
        stopwords = {
            "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
            "available", "evidence", "has", "in", "is", "it", "new", "no",
            "not", "now", "of", "on", "or", "requires", "shows", "the", "this",
            "to", "unavailable", "was", "were", "with",
        }
        return {
            token
            for token in re.findall(r"[a-z0-9]+", text.lower())
            if len(token) >= 4 and token not in stopwords
        }

    def all(self) -> list[dict]:
        return list(self._dead)

    def save(self, path: str | None = None) -> None:
        target = path or self._storage_path
        if target:
            with open(target, "w") as f:
                json.dump(self._dead, f, indent=2)

    def load(self, path: str) -> None:
        if os.path.isfile(path):
            with open(path) as f:
                self._dead = json.load(f)

    def summary(self) -> str:
        if not self._dead:
            return "Graveyard is empty."
        alive = sum(1 for d in self._dead if d.get("resurrected"))
        return f"Graveyard: {len(self._dead)} buried, {alive} resurrected"
