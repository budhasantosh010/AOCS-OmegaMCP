"""Setup diagnostics for AOCS Omega.

The doctor command is intentionally conservative: it checks local setup and
configuration without making paid model calls by default.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

from aocs_mcp.config import Config


@dataclass
class DoctorCheck:
    name: str
    status: str
    message: str
    fix: str | None = None


def _ok(name: str, message: str) -> DoctorCheck:
    return DoctorCheck(name=name, status="ok", message=message)


def _warn(name: str, message: str, fix: str | None = None) -> DoctorCheck:
    return DoctorCheck(name=name, status="warn", message=message, fix=fix)


def _fail(name: str, message: str, fix: str | None = None) -> DoctorCheck:
    return DoctorCheck(name=name, status="fail", message=message, fix=fix)


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _display_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.name


def _run_command(args: list[str], cwd: Path) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            args,
            cwd=str(cwd),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=45,
            check=False,
        )
    except FileNotFoundError:
        return 127, f"{args[0]} not found"
    except subprocess.TimeoutExpired:
        return 124, "command timed out"
    return proc.returncode, proc.stdout.strip()


def run_doctor(*, include_opencode: bool = True) -> list[DoctorCheck]:
    """Run local setup checks and return structured results."""
    root = _project_root()
    checks: list[DoctorCheck] = []

    checks.append(_ok("python", f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"))
    if sys.version_info < (3, 10):
        checks[-1] = _fail("python", sys.version.split()[0], "Install Python 3.10 or newer.")

    try:
        import mcp  # noqa: F401

        checks.append(_ok("mcp package", "import succeeded"))
    except Exception as exc:
        checks.append(_fail("mcp package", f"import failed: {exc}", "Run: pip install -e ."))

    try:
        import pydantic  # noqa: F401

        checks.append(_ok("pydantic package", "import succeeded"))
    except Exception as exc:
        checks.append(_fail("pydantic package", f"import failed: {exc}", "Run: pip install -e ."))

    config_dir = root / "config"
    default_cfg = config_dir / "models.default.json"
    local_cfg = config_dir / "models.local.json"
    checks.append(
        _ok("models.default.json", _display_path(default_cfg, root))
        if default_cfg.exists()
        else _fail("models.default.json", "missing", "Restore config/models.default.json.")
    )
    checks.append(
        _ok("models.local.json", _display_path(local_cfg, root))
        if local_cfg.exists()
        else _warn("models.local.json", "missing", "Optional: create config/models.local.json for local overrides.")
    )

    try:
        cfg = Config(config_dir=str(config_dir))
        checks.append(_ok("config load", f"{len(cfg.data)} top-level keys loaded"))
    except Exception as exc:
        checks.append(_fail("config load", f"failed: {exc}", "Fix JSON syntax in config files."))

    api_envs = [
        "OPENCODE_API_KEY",
        "OPENROUTER_API_KEY",
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "GEMINI_API_KEY",
        "GOOGLE_API_KEY",
        "NVIDIA_API_KEY",
    ]
    present = [name for name in api_envs if os.environ.get(name)]
    if present:
        checks.append(_ok("model API environment", f"set: {', '.join(present)}"))
    else:
        checks.append(
            _warn(
                "model API environment",
                "no supported provider API key is set",
                'Set one key, for example: $env:OPENCODE_API_KEY="..."',
            )
        )

    opencode_cfg = root / "opencode.jsonc"
    checks.append(
        _ok("opencode.jsonc", _display_path(opencode_cfg, root))
        if opencode_cfg.exists()
        else _warn("opencode.jsonc", "missing", "OpenCode MCP will need project config or manual setup.")
    )

    if include_opencode:
        opencode = shutil.which("opencode") or shutil.which("opencode.cmd")
        if not opencode:
            checks.append(_warn("opencode binary", "not found", "Install OpenCode or use AOCS through CLI/MCP elsewhere."))
        else:
            code, out = _run_command([opencode, "--version"], root)
            if code == 0:
                checks.append(_ok("opencode binary", out or opencode))
            else:
                checks.append(_warn("opencode binary", out or "version check failed"))

            code, out = _run_command([opencode, "mcp", "list"], root)
            if code == 0 and "aocs-omega" in out and "connected" in out.lower():
                checks.append(_ok("opencode mcp", "aocs-omega connected"))
            elif code == 0 and "aocs-omega" in out:
                checks.append(_warn("opencode mcp", "aocs-omega listed but connection status was unclear", out[-500:]))
            else:
                checks.append(
                    _warn(
                        "opencode mcp",
                        out[-500:] if out else "aocs-omega not listed",
                        "Run from the repo root and check opencode.jsonc.",
                    )
                )

    return checks


def checks_to_dict(checks: list[DoctorCheck]) -> dict:
    failures = sum(1 for check in checks if check.status == "fail")
    warnings = sum(1 for check in checks if check.status == "warn")
    return {
        "status": "fail" if failures else "warn" if warnings else "ok",
        "failures": failures,
        "warnings": warnings,
        "checks": [asdict(check) for check in checks],
    }


def format_checks(checks: list[DoctorCheck]) -> str:
    symbols = {"ok": "OK", "warn": "WARN", "fail": "FAIL"}
    lines = ["AOCS Doctor", ""]
    for check in checks:
        lines.append(f"[{symbols[check.status]}] {check.name}: {check.message}")
        if check.fix:
            lines.append(f"      fix: {check.fix}")
    result = checks_to_dict(checks)
    lines.extend(["", f"Result: {result['status']} ({result['failures']} fail, {result['warnings']} warn)"])
    return "\n".join(lines)


def checks_to_json(checks: list[DoctorCheck]) -> str:
    return json.dumps(checks_to_dict(checks), indent=2)
