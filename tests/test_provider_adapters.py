"""Tests for direct provider adapters."""

import asyncio
import json
from unittest.mock import patch

from aocs_mcp.utils.direct_api import call_gemini, call_nvidia, call_openrouter


class FakeConfig:
    def __init__(self, data):
        self.data = data

    def get(self, key, default=None):
        return self.data.get(key, default)


class FakeHTTPResponse:
    def __init__(self, body):
        self.body = json.dumps(body).encode()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return self.body


def test_openrouter_uses_openai_compatible_api():
    calls = []

    def fake_urlopen(req, timeout):
        body = json.loads(req.data.decode())
        calls.append((req.full_url, body, req.get_header("Authorization")))
        return FakeHTTPResponse({"choices": [{"message": {"content": "OR_OK"}}]})

    cfg = FakeConfig({"openrouter": {"base_url": "https://openrouter.example/api/v1"}})
    with patch.dict("os.environ", {"OPENROUTER_API_KEY": "or-key"}):
        with patch("urllib.request.urlopen", fake_urlopen):
            text = asyncio.run(call_openrouter(cfg, "openai/gpt-4o-mini", "sys", "user", expect_json=True))

    assert text == "OR_OK"
    assert calls[0][0] == "https://openrouter.example/api/v1/chat/completions"
    assert calls[0][1]["model"] == "openai/gpt-4o-mini"
    assert calls[0][1]["response_format"] == {"type": "json_object"}
    assert calls[0][2] == "Bearer or-key"


def test_nvidia_uses_openai_compatible_api():
    calls = []

    def fake_urlopen(req, timeout):
        body = json.loads(req.data.decode())
        calls.append((req.full_url, body, req.get_header("Authorization")))
        return FakeHTTPResponse({"choices": [{"message": {"content": "NV_OK"}}]})

    cfg = FakeConfig({"nvidia": {"base_url": "https://nvidia.example/v1"}})
    with patch.dict("os.environ", {"NVIDIA_API_KEY": "nv-key"}):
        with patch("urllib.request.urlopen", fake_urlopen):
            text = asyncio.run(call_nvidia(cfg, "meta/llama-test", "sys", "user"))

    assert text == "NV_OK"
    assert calls[0][0] == "https://nvidia.example/v1/chat/completions"
    assert calls[0][1]["model"] == "meta/llama-test"
    assert calls[0][2] == "Bearer nv-key"


def test_gemini_uses_generate_content_api():
    calls = []

    def fake_urlopen(req, timeout):
        body = json.loads(req.data.decode())
        calls.append((req.full_url, body))
        return FakeHTTPResponse(
            {"candidates": [{"content": {"parts": [{"text": "{\"ok\": true}"}]}}]}
        )

    cfg = FakeConfig({"gemini": {"base_url": "https://gemini.example/v1beta"}})
    with patch.dict("os.environ", {"GEMINI_API_KEY": "gm-key"}):
        with patch("urllib.request.urlopen", fake_urlopen):
            text = asyncio.run(call_gemini(cfg, "gemini-test", "sys", "user", expect_json=True))

    assert text == "{\"ok\": true}"
    assert calls[0][0] == "https://gemini.example/v1beta/models/gemini-test:generateContent?key=gm-key"
    assert calls[0][1]["systemInstruction"]["parts"] == [{"text": "sys"}]
    assert calls[0][1]["contents"][0]["parts"] == [{"text": "user"}]
    assert calls[0][1]["generationConfig"]["responseMimeType"] == "application/json"


if __name__ == "__main__":
    test_openrouter_uses_openai_compatible_api()
    test_nvidia_uses_openai_compatible_api()
    test_gemini_uses_generate_content_api()
    print("provider adapter tests passed")
