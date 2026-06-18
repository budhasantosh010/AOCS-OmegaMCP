"""Reusable scripted test doubles for deterministic AOCS protocol tests."""


class ScriptedRouter:
    def __init__(self, responses: dict[str, list[object]]):
        self.responses = {key: list(value) for key, value in responses.items()}
        self.call_count = 0
        self.call_log: list[dict] = []
        self.max_calls = None

    def reset_trace(self, max_calls=None):
        self.call_count = 0
        self.call_log = []
        self.max_calls = max_calls

    def _take(self, role: str):
        queue = self.responses.get(role, [])
        if not queue:
            raise AssertionError(f"No scripted response left for role: {role}")
        value = queue.pop(0)
        self.call_count += 1
        self.call_log.append({"call": self.call_count, "role": role, "status": "ok"})
        if isinstance(value, Exception):
            raise value
        return value

    async def call_structured(self, role, system_prompt, user_prompt):
        value = self._take(role)
        if not isinstance(value, dict):
            raise AssertionError(f"Expected dict response for {role}, got {type(value).__name__}")
        return value

    async def call(self, role, system_prompt, user_prompt, expect_json=False):
        value = self._take(role)
        if isinstance(value, dict):
            import json

            return json.dumps(value)
        return str(value)
