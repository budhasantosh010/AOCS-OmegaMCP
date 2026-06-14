"""LLM Router — routes every sub-agent call to host CLI or direct API."""

import datetime as _dt
import hashlib
import json
import re
import time

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
        self.call_count = 0
        self.max_calls: int | None = None
        self.call_log: list[dict] = []

    def reset_trace(self, max_calls: int | None = None) -> None:
        """Reset per-run call accounting and optional model-call budget."""
        self.call_count = 0
        self.max_calls = max_calls if max_calls and max_calls > 0 else None
        self.call_log = []

    async def call(
        self,
        role: str,
        system_prompt: str,
        user_prompt: str,
        expect_json: bool = False,
    ) -> str:
        """Route an LLM call for a given AOCS role."""
        if self.max_calls is not None and self.call_count >= self.max_calls:
            raise LLMUnavailable(
                f"Model-call budget exceeded before role '{role}'. "
                f"Budget: {self.max_calls}"
            )

        self.call_count += 1
        entry = {
            "call": self.call_count,
            "role": role,
            "expect_json": expect_json,
            "started_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
            "system_prompt_sha256": hashlib.sha256(system_prompt.encode()).hexdigest(),
            "user_prompt_sha256": hashlib.sha256(user_prompt.encode()).hexdigest(),
            "system_prompt_chars": len(system_prompt),
            "user_prompt_chars": len(user_prompt),
        }
        started = time.perf_counter()
        self.call_log.append(entry)

        # Global override (used for testing): force every role to one provider+model.
        force = self.config.get("force_provider")
        if force:
            caller = PROVIDERS.get(force.get("provider"))
            if not caller:
                entry["mode"] = "force_provider"
                entry["provider"] = force.get("provider")
                entry["model"] = force.get("model")
                entry["status"] = "error"
                entry["error"] = f"force_provider: unknown provider '{force.get('provider')}'"
                entry["duration_ms"] = round((time.perf_counter() - started) * 1000, 1)
                raise LLMUnavailable(f"force_provider: unknown provider '{force.get('provider')}'")
            entry["mode"] = "force_provider"
            entry["provider"] = force.get("provider")
            entry["model"] = force.get("model")
            try:
                text = await caller(
                    self.config,
                    force.get("model"),
                    system_prompt,
                    user_prompt,
                    expect_json=expect_json,
                )
                entry["status"] = "ok"
                entry["response_chars"] = len(text)
                return text
            except Exception as e:
                entry["status"] = "error"
                entry["error"] = str(e)
                raise
            finally:
                entry["duration_ms"] = round((time.perf_counter() - started) * 1000, 1)

        role_cfg = self.config.get_role(role)
        mode = role_cfg.get("mode", "host-cli")
        errors: list[str] = []
        entry["configured_mode"] = mode

        # Strategy 1: host-cli
        if mode in ("host-cli", "auto"):
            try:
                hc = self.config.host_cli_config()
                entry["mode"] = "host-cli"
                entry["priority"] = hc.get("priority", ["opencode"])
                text = await call_host_cli(
                    system_prompt,
                    user_prompt,
                    priority=hc.get("priority", ["opencode"]),
                )
                entry["status"] = "ok"
                entry["response_chars"] = len(text)
                entry["duration_ms"] = round((time.perf_counter() - started) * 1000, 1)
                return text
            except RuntimeError as e:
                errors.append(str(e))
                entry.setdefault("errors", []).append(f"host-cli: {e}")
                if mode == "host-cli":
                    entry["status"] = "error"
                    entry["error"] = str(e)
                    entry["duration_ms"] = round((time.perf_counter() - started) * 1000, 1)
                    raise LLMUnavailable(str(e))

        # Strategy 2: direct-api
        if mode in ("direct-api", "auto"):
            direct = role_cfg.get("direct_api", {})
            provider = direct.get("provider", "anthropic")
            model = direct.get("model", "claude-sonnet-4-6")
            caller = PROVIDERS.get(provider)
            if caller:
                try:
                    entry["mode"] = "direct-api"
                    entry["provider"] = provider
                    entry["model"] = model
                    text = await caller(
                        self.config,
                        model,
                        system_prompt,
                        user_prompt,
                        expect_json=expect_json,
                    )
                    entry["status"] = "ok"
                    entry["response_chars"] = len(text)
                    entry["duration_ms"] = round((time.perf_counter() - started) * 1000, 1)
                    return text
                except Exception as e:
                    errors.append(f"Direct API ({provider}): {e}")
                    entry.setdefault("errors", []).append(f"direct-api ({provider}): {e}")
                    if mode == "direct-api":
                        entry["status"] = "error"
                        entry["error"] = str(e)
                        entry["duration_ms"] = round((time.perf_counter() - started) * 1000, 1)
                        raise LLMUnavailable(str(e))

        entry["status"] = "error"
        entry["error"] = f"No provider for role '{role}'"
        entry["duration_ms"] = round((time.perf_counter() - started) * 1000, 1)
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
