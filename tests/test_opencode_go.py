"""Tests for the OpenCode Go HTTP provider."""

import asyncio
import json

from aocs_mcp.utils.direct_api import call_opencode_go


class FakeConfig:
    def get(self, key, default=None):
        if key == "opencode_go":
            return {
                "base_url": "http://127.0.0.1:60679",
                "variant": "max",
                "timeout": 123,
            }
        return default


class FakeHTTPResponse:
    def __init__(self, body):
        self.body = json.dumps(body).encode()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return self.body


def test_opencode_go_uses_synchronous_message_response(monkeypatch):
    monkeypatch.setenv("OPENCODE_SERVER_PASSWORD", "test-password")
    calls = []

    def fake_urlopen(req, timeout):
        body = json.loads(req.data.decode()) if req.data else None
        calls.append((req.full_url, body, timeout, req.get_header("Authorization")))
        if req.full_url.endswith("/session"):
            return FakeHTTPResponse({"id": "session-1"})
        if req.full_url.endswith("/session/session-1/message"):
            return FakeHTTPResponse(
                {
                    "info": {"id": "message-1"},
                    "parts": [{"type": "text", "text": "TEST_OK"}],
                }
            )
        raise AssertionError(f"Unexpected URL: {req.full_url}")

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    text = asyncio.run(
        call_opencode_go(
            FakeConfig(),
            "deepseek-v4-flash",
            "system",
            "user",
        )
    )

    assert text == "TEST_OK"
    assert calls[0][0] == "http://127.0.0.1:60679/session"
    assert calls[1][0] == "http://127.0.0.1:60679/session/session-1/message"
    assert calls[1][1]["model"] == {
        "providerID": "opencode-go",
        "modelID": "deepseek-v4-flash",
    }
    assert calls[1][1]["variant"] == "max"
    assert calls[1][1]["agent"] == "build"
    assert calls[1][1]["parts"] == [{"type": "text", "text": "system\n\nuser"}]
    assert calls[1][2] == 123
    assert calls[1][3].startswith("Basic ")
