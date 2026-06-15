"""Tests for OpenCode Go direct HTTP request shape."""

import asyncio
import json
from unittest.mock import patch

from aocs_mcp.utils.direct_api import call_opencode_go


class FakeConfig:
    def get(self, key, default=None):
        if key == "opencode_go":
            return {
                "transport": "direct-http",
                "api_base_url": "https://opencode.example/v1",
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


def test_opencode_go_direct_http_uses_openai_compatible_body():
    calls = []

    def fake_urlopen(req, timeout):
        body = json.loads(req.data.decode())
        calls.append((req.full_url, body, timeout, req.get_header("Authorization")))
        return FakeHTTPResponse(
            {"choices": [{"message": {"content": "TEST_OK"}}]}
        )

    with patch.dict("os.environ", {"OPENCODE_API_KEY": "test-key"}):
        with patch("urllib.request.urlopen", fake_urlopen):
            text = asyncio.run(
                call_opencode_go(
                    FakeConfig(),
                    "deepseek-v4-flash",
                    "system",
                    "user",
                    max_tokens=64,
                )
            )

    assert text == "TEST_OK"
    assert calls[0][0] == "https://opencode.example/v1/chat/completions"
    assert calls[0][1]["model"] == "deepseek-v4-flash"
    assert calls[0][1]["messages"] == [
        {"role": "system", "content": "system"},
        {"role": "user", "content": "user"},
    ]
    assert "reasoning_effort" not in calls[0][1]
    assert calls[0][1]["max_tokens"] == 64
    assert calls[0][2] == 123
    assert calls[0][3] == "Bearer test-key"


def test_opencode_go_direct_http_sets_json_response_format_when_requested():
    calls = []

    def fake_urlopen(req, timeout):
        body = json.loads(req.data.decode())
        calls.append(body)
        return FakeHTTPResponse(
            {"choices": [{"message": {"content": "{\"ok\": true}"}}]}
        )

    with patch.dict("os.environ", {"OPENCODE_API_KEY": "test-key"}):
        with patch("urllib.request.urlopen", fake_urlopen):
            text = asyncio.run(
                call_opencode_go(
                    FakeConfig(),
                    "deepseek-v4-flash",
                    "system",
                    "user",
                    expect_json=True,
                )
            )

    assert text == "{\"ok\": true}"
    assert calls[0]["response_format"] == {"type": "json_object"}


if __name__ == "__main__":
    test_opencode_go_direct_http_uses_openai_compatible_body()
    test_opencode_go_direct_http_sets_json_response_format_when_requested()
    print("opencode direct-http tests passed")
