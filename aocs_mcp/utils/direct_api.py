"""Direct API wrappers for all supported AOCS model providers."""

import asyncio
import base64
import json
import os
import time
import urllib.error
import urllib.request

from aocs_mcp.config import Config


def _provider_cfg(config: Config, key: str) -> dict:
    return config.get(key, {}) or {}


def _api_key(config: Config, provider: str, env_name: str) -> str | None:
    return os.environ.get(env_name) or _provider_cfg(config, provider).get("api_key")


def _extract_openai_compatible_text(payload: dict, provider_name: str) -> str:
    choices = payload.get("choices") or []
    if choices:
        message = choices[0].get("message") or {}
        content = message.get("content")
        if isinstance(content, str) and content.strip():
            return content.strip()
        reasoning = message.get("reasoning_content")
        if isinstance(reasoning, str) and reasoning.strip():
            return reasoning.strip()
    text = payload.get("output_text")
    if isinstance(text, str) and text.strip():
        return text.strip()
    raise RuntimeError(f"{provider_name} returned no assistant text")


async def _call_openai_compatible_http(
    *,
    provider_name: str,
    base_url: str,
    api_key: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 4000,
    expect_json: bool = False,
    timeout: float = 300,
    user_agent: str = "aocs-omega/1.0",
    extra_headers: dict | None = None,
    extra_body: dict | None = None,
) -> str:
    """Call an OpenAI-compatible chat completions endpoint."""
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {api_key}",
        "User-Agent": user_agent,
    }
    if extra_headers:
        headers.update(extra_headers)

    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": max_tokens,
        "stream": False,
    }
    if expect_json:
        body["response_format"] = {"type": "json_object"}
    if extra_body:
        body.update(extra_body)

    def _call() -> str:
        req = urllib.request.Request(
            f"{base_url.rstrip('/')}/chat/completions",
            data=json.dumps(body).encode(),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                payload = json.loads(resp.read())
        except urllib.error.HTTPError as e:
            raw = e.read().decode(errors="replace")
            raise RuntimeError(f"{provider_name} HTTP {e.code}: {raw[:500]}")
        except urllib.error.URLError as e:
            raise RuntimeError(f"{provider_name} unreachable: {e.reason}")

        return _extract_openai_compatible_text(payload, provider_name)

    return await asyncio.to_thread(_call)


async def call_anthropic(
    config: Config,
    model: str,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 4000,
    expect_json: bool = False,
) -> str:
    """Call Anthropic API directly."""
    api_key = config.direct_api_key("anthropic")
    if not api_key:
        raise RuntimeError("Anthropic API key not configured")

    try:
        from anthropic import AsyncAnthropic

        client = AsyncAnthropic(api_key=api_key)
        msg = await client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return msg.content[0].text
    except ImportError:
        raise RuntimeError("anthropic package not installed. Run: pip install anthropic")


async def call_openai(
    config: Config,
    model: str,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 4000,
    expect_json: bool = False,
) -> str:
    """Call OpenAI API directly."""
    api_key = config.direct_api_key("openai")
    if not api_key:
        raise RuntimeError("OpenAI API key not configured")

    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=api_key)
        kwargs = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        if expect_json:
            kwargs["response_format"] = {"type": "json_object"}
        resp = await client.chat.completions.create(**kwargs)
        return resp.choices[0].message.content or ""
    except ImportError:
        raise RuntimeError("openai package not installed. Run: pip install openai")


async def call_openrouter(
    config: Config,
    model: str,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 4000,
    expect_json: bool = False,
) -> str:
    """Call OpenRouter's OpenAI-compatible API."""
    rc = _provider_cfg(config, "openrouter")
    api_key = _api_key(config, "openrouter", "OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY not set in environment")

    headers = {}
    referer = rc.get("http_referer") or os.environ.get("OPENROUTER_HTTP_REFERER")
    title = rc.get("app_title") or os.environ.get("OPENROUTER_APP_TITLE")
    if referer:
        headers["HTTP-Referer"] = referer
    if title:
        headers["X-Title"] = title

    return await _call_openai_compatible_http(
        provider_name="OpenRouter",
        base_url=rc.get("base_url", "https://openrouter.ai/api/v1"),
        api_key=api_key,
        model=model or rc.get("model", "openai/gpt-4o-mini"),
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        max_tokens=max_tokens,
        expect_json=expect_json,
        timeout=float(rc.get("timeout", 300)),
        user_agent=rc.get("user_agent", "aocs-omega/1.0"),
        extra_headers=headers,
    )


async def call_nvidia(
    config: Config,
    model: str,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 4000,
    expect_json: bool = False,
) -> str:
    """Call NVIDIA NIM's OpenAI-compatible API."""
    nc = _provider_cfg(config, "nvidia")
    api_key = _api_key(config, "nvidia", "NVIDIA_API_KEY")
    if not api_key:
        raise RuntimeError("NVIDIA_API_KEY not set in environment")

    return await _call_openai_compatible_http(
        provider_name="NVIDIA NIM",
        base_url=nc.get("base_url", "https://integrate.api.nvidia.com/v1"),
        api_key=api_key,
        model=model or nc.get("model", "meta/llama-3.1-70b-instruct"),
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        max_tokens=max_tokens,
        expect_json=expect_json,
        timeout=float(nc.get("timeout", 300)),
        user_agent=nc.get("user_agent", "aocs-omega/1.0"),
    )


async def call_gemini(
    config: Config,
    model: str,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 4000,
    expect_json: bool = False,
) -> str:
    """Call Google Gemini's generateContent REST API."""
    gc = _provider_cfg(config, "gemini")
    api_key = (
        _api_key(config, "gemini", "GEMINI_API_KEY")
        or os.environ.get("GOOGLE_API_KEY")
    )
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY or GOOGLE_API_KEY not set in environment")

    base = gc.get("base_url", "https://generativelanguage.googleapis.com/v1beta").rstrip("/")
    model = model or gc.get("model", "gemini-2.5-flash")
    request_timeout = float(gc.get("timeout", 300))
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": gc.get("user_agent", "aocs-omega/1.0"),
    }
    body = {
        "systemInstruction": {
            "parts": [{"text": system_prompt}],
        },
        "contents": [
            {
                "role": "user",
                "parts": [{"text": user_prompt}],
            }
        ],
        "generationConfig": {
            "maxOutputTokens": max_tokens,
        },
    }
    if expect_json:
        body["generationConfig"]["responseMimeType"] = "application/json"

    def _call() -> str:
        req = urllib.request.Request(
            f"{base}/models/{model}:generateContent?key={api_key}",
            data=json.dumps(body).encode(),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=request_timeout) as resp:
                payload = json.loads(resp.read())
        except urllib.error.HTTPError as e:
            raw = e.read().decode(errors="replace")
            raise RuntimeError(f"Gemini HTTP {e.code}: {raw[:500]}")
        except urllib.error.URLError as e:
            raise RuntimeError(f"Gemini unreachable: {e.reason}")

        candidates = payload.get("candidates") or []
        for candidate in candidates:
            content = candidate.get("content") or {}
            parts = content.get("parts") or []
            text = "".join(
                part.get("text", "")
                for part in parts
                if isinstance(part, dict)
            ).strip()
            if text:
                return text
        raise RuntimeError("Gemini returned no assistant text")

    return await asyncio.to_thread(_call)


async def call_opencode_go(
    config: Config,
    model: str,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 4000,
    expect_json: bool = False,
) -> str:
    """Call OpenCode Go through the configured transport.

    Supported transports:
    - local-server: OpenCode's local REST session API, authenticated with
      OPENCODE_SERVER_PASSWORD.
    - direct-http: OpenCode Go's OpenAI-compatible endpoint, authenticated with
      OPENCODE_API_KEY.
    - auto: try direct-http when OPENCODE_API_KEY exists, otherwise local-server.
    """
    oc = config.get("opencode_go", {}) or {}
    transport = oc.get("transport", "local-server")
    if transport == "auto":
        transport = "direct-http" if os.environ.get("OPENCODE_API_KEY") else "local-server"
    if transport in ("direct-http", "openai-compatible"):
        return await _call_opencode_go_direct_http(
            config, model, system_prompt, user_prompt, max_tokens=max_tokens, expect_json=expect_json
        )
    if transport != "local-server":
        raise RuntimeError(
            f"Unknown OpenCode Go transport '{transport}'. "
            "Use local-server, direct-http, or auto."
        )

    return await _call_opencode_go_local_server(
        config, model, system_prompt, user_prompt, max_tokens=max_tokens, expect_json=expect_json
    )


async def _call_opencode_go_direct_http(
    config: Config,
    model: str,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 4000,
    expect_json: bool = False,
) -> str:
    """Call OpenCode Go's OpenAI-compatible hosted endpoint."""
    oc = config.get("opencode_go", {}) or {}
    base = (
        oc.get("api_base_url")
        or os.environ.get("OPENCODE_GO_API_BASE_URL")
        or "https://opencode.ai/zen/go/v1"
    ).rstrip("/")
    api_key = os.environ.get("OPENCODE_API_KEY") or oc.get("api_key")
    if not api_key:
        raise RuntimeError("OPENCODE_API_KEY not set in environment")

    extra_body = {}
    if oc.get("reasoning_effort"):
        extra_body["reasoning_effort"] = oc["reasoning_effort"]

    try:
        return await _call_openai_compatible_http(
            provider_name="OpenCode Go",
            base_url=base,
            api_key=api_key,
            model=model or oc.get("model", "deepseek-v4-flash"),
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=max_tokens,
            expect_json=expect_json,
            timeout=float(oc.get("timeout", 300)),
            user_agent=oc.get("user_agent", "aocs-omega/1.0"),
            extra_body=extra_body,
        )
    except RuntimeError as e:
        if "browser_signature_banned" in str(e) or "Error 1010" in str(e):
            raise RuntimeError(
                "OpenCode Go direct HTTP was blocked by the provider edge "
                "(Cloudflare browser_signature_banned). Set a normal user_agent "
                "or use an allowed runtime."
            )
        raise


async def _call_opencode_go_local_server(
    config: Config,
    model: str,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 4000,
    expect_json: bool = False,
) -> str:
    """Call OpenCode Go's local HTTP API using the synchronous message endpoint.

    Each AOCS role gets a fresh OpenCode session, preserving blind independent
    sub-agent calls while the Python runtime controls the pipeline order.
    Authentication uses OPENCODE_SERVER_PASSWORD and is never stored in config.
    """
    oc = config.get("opencode_go", {}) or {}
    base = (
        oc.get("base_url")
        or os.environ.get("OPENCODE_GO_URL")
        or "http://127.0.0.1:60679"
    ).rstrip("/")
    variant = oc.get("variant", "max")
    request_timeout = float(oc.get("timeout", 300))
    empty_assistant_grace = float(oc.get("empty_assistant_grace_seconds", 15))
    agent = oc.get("agent", "build")
    model = model or oc.get("model", "deepseek-v4-flash")
    password = os.environ.get("OPENCODE_SERVER_PASSWORD", "")
    if not password:
        raise RuntimeError("OPENCODE_SERVER_PASSWORD not set in environment")

    auth = base64.b64encode(f"opencode:{password}".encode()).decode()
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Basic {auth}",
    }

    def _req(
        method: str,
        path: str,
        body: dict | None = None,
        timeout: float = 60,
    ):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(
            f"{base}{path}",
            data=data,
            headers=headers,
            method=method,
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read()
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"OpenCode Go HTTP {e.code}: {e.read().decode()[:300]}")
        except urllib.error.URLError as e:
            raise RuntimeError(
                f"OpenCode Go unreachable at {base}: {e.reason}. Is the server running?"
            )
        return json.loads(raw) if raw else None

    def _extract_text(payload) -> str:
        parts = (payload or {}).get("parts", [])
        return "".join(
            part.get("text", "")
            for part in parts
            if isinstance(part, dict) and part.get("type") == "text"
        ).strip()

    def _latest_assistant_text(messages) -> tuple[str, bool]:
        saw_assistant = False
        latest_text = ""
        for message in messages or []:
            info = message.get("info", {}) if isinstance(message, dict) else {}
            if info.get("role") != "assistant":
                continue
            saw_assistant = True
            text = _extract_text(message)
            if text:
                latest_text = text
        return latest_text, saw_assistant

    def _call() -> str:
        session = _req("POST", "/session", {"title": "aocs-omega"})
        sid = session["id"]
        prompt = f"{system_prompt}\n\n{user_prompt}" if system_prompt else user_prompt
        result = _req(
            "POST",
            f"/session/{sid}/message",
            {
                "parts": [{"type": "text", "text": prompt}],
                "model": {
                    "providerID": "opencode-go",
                    "modelID": model,
                },
                "variant": variant,
                "agent": agent,
            },
            timeout=request_timeout,
        )

        text = _extract_text(result)
        if text:
            return text

        deadline = time.time() + request_timeout
        empty_since = None
        while time.time() < deadline:
            messages = _req("GET", f"/session/{sid}/message", timeout=60)
            text, saw_assistant = _latest_assistant_text(messages)
            if text:
                return text
            if saw_assistant:
                empty_since = empty_since or time.time()
                if time.time() - empty_since >= empty_assistant_grace:
                    raise RuntimeError(
                        "OpenCode Go created an assistant message with no text "
                        "and zero visible generation. The local REST server is "
                        "recording messages but not invoking the model."
                    )
            time.sleep(1.5)

        raise RuntimeError("OpenCode Go did not return assistant text before timeout")

    return await asyncio.to_thread(_call)


PROVIDERS = {
    "anthropic": call_anthropic,
    "claude": call_anthropic,
    "gemini": call_gemini,
    "google": call_gemini,
    "nvidia": call_nvidia,
    "nvidia-nim": call_nvidia,
    "openai": call_openai,
    "opencode-go": call_opencode_go,
    "openrouter": call_openrouter,
}
