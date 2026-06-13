"""Host CLI subprocess — calls opencode run / claude --print."""

import os
import subprocess
import shutil


def find_cli(name: str) -> str | None:
    """Check if a CLI is available on PATH."""
    return shutil.which(name)


async def call_host_cli(
    system_prompt: str,
    user_prompt: str,
    priority: list[str] | None = None,
    timeout: int = 120,
) -> str:
    """Try each available CLI in priority order. Returns stdout text."""
    priority = priority or ["opencode", "claude", "cursor"]
    full_prompt = f"{system_prompt}\n\n{user_prompt}"

    for cli in priority:
        exe = find_cli(cli)
        if not exe:
            continue

        try:
            if cli == "opencode":
                cmd = [exe, "run", "--format", "json", full_prompt]
            elif cli == "claude":
                cmd = [exe, "--print", full_prompt]
            else:
                # Generic fallback: assume --print flag
                cmd = [exe, "--print", full_prompt]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            continue

    raise RuntimeError(
        f"No compatible host CLI found. Tried: {', '.join(priority)}. "
        "Install opencode, claude, or configure direct_api in models.local.json"
    )
