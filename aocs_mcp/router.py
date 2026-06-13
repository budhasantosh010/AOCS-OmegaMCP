"""LLM Router — routes every sub-agent call to host CLI or direct API."""

import json
import re

from aocs_mcp.config import Config
from aocs_mcp.utils.host_cli import call_host_cli
from aocs_mcp.utils.direct_api import PROVIDERS


class LLMUnavailable(RuntimeError):
    """No LLM provider could handle the request."""
    pass


class LLMRouter:
    """
    Routes LLM calls per-role configuration.

    Priority:
    1. host-cli mode → subprocess to opencode / claude
    2. direct-api mode → SDK call to anthropic / openai
    3. auto mode → try host-cli, fallback to direct-api
    """

    def __init__(self, config: Config):
        self.config = config

    async def call(
        self,
        role: str,
        system_prompt: str,
        user_prompt: str,
        expect_json: bool = False,
    ) -> str:
        """Route an LLM call for a given AOCS role."""
        role_cfg = self.config.get_role(role)
        mode = role_cfg.get("mode", "host-cli")
        errors: list[str] = []

        # Strategy 1: host-cli
        if mode in ("host-cli", "auto"):
            try:
                hc = self.config.host_cli_config()
                return await call_host_cli(
                    system_prompt,
                    user_prompt,
                    priority=hc.get("priority", ["opencode"]),
                )
            except RuntimeError as e:
                errors.append(str(e))
                if mode == "host-cli":
                    raise LLMUnavailable(str(e))

        # Strategy 2: direct-api
        if mode in ("direct-api", "auto"):
            direct = role_cfg.get("direct_api", {})
            provider = direct.get("provider", "anthropic")
            model = direct.get("model", "claude-sonnet-4-6")
            caller = PROVIDERS.get(provider)
            if caller:
                try:
                    return await caller(self.config, model, system_prompt, user_prompt)
                except Exception as e:
                    errors.append(f"Direct API ({provider}): {e}")
                    if mode == "direct-api":
                        raise LLMUnavailable(str(e))

        raise LLMUnavailable(
            f"No provider for role '{role}'. Tried: {'; '.join(errors) or 'nothing configured'}"
        )

    async def call_structured(
        self,
        role: str,
        system_prompt: str,
        user_prompt: str,
    ) -> dict:
        """Call LLM and parse JSON response."""
        text = await self.call(role, system_prompt, user_prompt, expect_json=True)
        return self._extract_json(text)

    @staticmethod
    def _extract_json(text: str) -> dict:
        """Extract JSON object from LLM response (handles markdown fences)."""
        # Try parsing the whole thing
        text = text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try extracting from ```json ... ``` fences
        m = re.search(r"```(?:json)?\s*\n?([\s\S]*?)```", text)
        if m:
            try:
                return json.loads(m.group(1).strip())
            except json.JSONDecodeError:
                pass

        # Try finding {...} in the text
        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                pass

        raise ValueError(f"Could not extract JSON from response:\n{text[:500]}")
