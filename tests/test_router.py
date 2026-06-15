"""Tests for LLM router accounting and guardrails."""

import asyncio

from aocs_mcp.router import LLMRouter, LLMUnavailable
from aocs_mcp.utils import direct_api


class FakeConfig:
    def get(self, key, default=None):
        if key == "force_provider":
            return {"provider": "fake", "model": "fake-model"}
        return default

    def get_role(self, role):
        return {}

    def host_cli_config(self):
        return {}


async def _fake_provider(config, model, system_prompt, user_prompt, **kwargs):
    return '{"ok": true}'


def test_router_records_trace_and_enforces_budget():
    direct_api.PROVIDERS["fake"] = _fake_provider
    try:
        router = LLMRouter(FakeConfig())
        router.reset_trace(max_calls=1)

        text = asyncio.run(router.call("specialist", "system", "user"))
        assert text == '{"ok": true}'
        assert router.call_count == 1
        assert router.call_log[0]["role"] == "specialist"
        assert router.call_log[0]["status"] == "ok"
        assert router.call_log[0]["response_preview"] == '{"ok": true}'
        assert "system_prompt_sha256" in router.call_log[0]

        try:
            asyncio.run(router.call("judge", "system", "user"))
        except LLMUnavailable as exc:
            assert "Model-call budget exceeded" in str(exc)
        else:
            raise AssertionError("Expected budget failure")
    finally:
        direct_api.PROVIDERS.pop("fake", None)


if __name__ == "__main__":
    test_router_records_trace_and_enforces_budget()
    print("router tests passed")
