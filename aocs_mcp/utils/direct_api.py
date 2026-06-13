"""Direct API wrappers for Anthropic and OpenAI."""

from aocs_mcp.config import Config


async def call_anthropic(
    config: Config,
    model: str,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 4000,
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
) -> str:
    """Call OpenAI API directly."""
    api_key = config.direct_api_key("openai")
    if not api_key:
        raise RuntimeError("OpenAI API key not configured")

    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=api_key)
        resp = await client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return resp.choices[0].message.content or ""
    except ImportError:
        raise RuntimeError("openai package not installed. Run: pip install openai")


PROVIDERS = {
    "anthropic": call_anthropic,
    "openai": call_openai,
}
