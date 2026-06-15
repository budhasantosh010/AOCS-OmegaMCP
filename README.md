# AOCS Omega

AOCS Omega is a standalone deterministic reasoning runtime.

It is not a Markdown skill that a model has to remember. The coding agent calls
one entrypoint, and the AOCS runtime executes the required phases in code:

```text
Phase 0 framing
-> Phase 1 scoring
-> Type 1/2/3 routing
-> specialist / red team / contrarian / judge
-> quality gates
-> observer
-> shadow orchestrator
-> memory audit
-> final result
```

## Architecture

```text
AOCS runtime
  The real engine. Owns the workflow and run records.

MCP server
  Lets Claude Code, OpenCode, Codex, Cursor, and other MCP clients call AOCS.

CLI
  Universal fallback. Anything that can run a terminal command can run AOCS.

Model provider adapters
  Let AOCS call OpenCode Go, OpenAI, Anthropic, host CLIs, or future providers.

Thin agent adapters
  Slash commands or tiny config snippets that only trigger the runtime.
```

The key rule: adapters are buttons. The runtime is the machine.

## Quick Start

Install dependencies:

```bash
pip install -e .
```

Run directly from the terminal:

```bash
aocs run "Analyze this problem deeply"
```

Check local setup before using a coding agent:

```bash
aocs doctor
```

The doctor command checks Python packages, config files, provider environment
variables, OpenCode availability, and whether OpenCode can connect to the
`aocs-omega` MCP server. It reports which environment variable names are set,
but never prints API key values.

Start the MCP server:

```bash
python -m aocs_mcp
```

## MCP Tool Surface

Normal agent use exposes only two public tools:

| Tool | Purpose |
| --- | --- |
| `aocs_run_full` | Canonical full deterministic AOCS run |
| `aocs_analyze` | Compatibility alias for `aocs_run_full` |

Internal phase tools are hidden by default so an outer coding agent cannot
accidentally call only one shallow phase and skip the rest.

To expose debug tools intentionally:

```json
{
  "expose_debug_tools": true
}
```

## Run Artifacts

Every persisted run writes files under `.aocs/runs/<run-id>/`:

```text
request.json   input request
status.json    running/completed/error status
trace.json     model-call trace with role names and prompt hashes
result.json    full structured AOCS result
summary.md     human-readable summary
```

This is intentionally separate from Claude/OpenCode/Codex/Cursor settings and
databases.

Open the AOCS-owned visual dashboard:

```bash
aocs dashboard
```

Then open:

```text
http://127.0.0.1:8765/
```

The dashboard is independent from coding agents. It reads AOCS run artifacts and
shows:

- run history
- final verdict and confidence
- route and problem type
- agent timeline
- visible answers from Specialist, Red Team, Contrarian, Judge, Observer, Shadow
  Orchestrator, Type 3 agents, and direct-answer runs
- raw summary

By default, future `trace.json` files store a local response preview for each
model call:

```json
{
  "runtime": {
    "trace_response_preview_chars": 2000
  }
}
```

Set this value to `0` in `config/models.local.json` if you want traces to keep
only metadata and prompt hashes.

Override the run directory:

```bash
aocs run "question" --output-dir "C:/path/to/runs"
```

Disable artifact writing:

```bash
aocs run "question" --no-store
```

## Model Providers

AOCS roles call models through the router. The outer coding agent does not run
the AOCS phases itself.

### OpenCode Go

Preferred direct HTTPS transport:

```json
{
  "force_provider": { "provider": "opencode-go", "model": "deepseek-v4-flash" },
  "opencode_go": {
    "transport": "direct-http",
    "variant": "max",
    "timeout": 300
  }
}
```

Set the API key as an environment variable:

```powershell
$env:OPENCODE_API_KEY = "..."
```

This calls `https://opencode.ai/zen/go/v1/chat/completions` directly. It does
not open the OpenCode app, run the OpenCode CLI, or attach to a local OpenCode
server.

Optional local OpenCode server transport:

```json
{
  "force_provider": { "provider": "opencode-go", "model": "deepseek-v4-flash" },
  "opencode_go": {
    "transport": "local-server",
    "base_url": "http://127.0.0.1:60679",
    "variant": "max",
    "timeout": 300
  }
}
```

Set the local server password as an environment variable:

```powershell
$env:OPENCODE_SERVER_PASSWORD = "..."
```

Do not commit API keys to the repo.

### OpenAI / Anthropic

### OpenRouter / Google Gemini / NVIDIA NIM

AOCS can also route roles through:

```text
openrouter   env: OPENROUTER_API_KEY
gemini       env: GEMINI_API_KEY or GOOGLE_API_KEY
google       alias for gemini
nvidia       env: NVIDIA_API_KEY
nvidia-nim   alias for nvidia
```

Default endpoints:

```text
OpenRouter: https://openrouter.ai/api/v1/chat/completions
Gemini:     https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent
NVIDIA:     https://integrate.api.nvidia.com/v1/chat/completions
```

Per-role direct API routing example:

```json
{
  "roles": {
    "specialist": {
      "mode": "direct-api",
      "direct_api": { "provider": "openrouter", "model": "anthropic/claude-3.5-sonnet" }
    },
    "red-team": {
      "mode": "direct-api",
      "direct_api": { "provider": "nvidia", "model": "meta/llama-3.1-70b-instruct" }
    },
    "judge": {
      "mode": "direct-api",
      "direct_api": { "provider": "gemini", "model": "gemini-2.5-pro" }
    }
  }
}
```

Use environment variables:

```powershell
$env:ANTHROPIC_API_KEY = "..."
$env:OPENAI_API_KEY = "..."
$env:OPENROUTER_API_KEY = "..."
$env:GEMINI_API_KEY = "..."
$env:NVIDIA_API_KEY = "..."
```

## Agent Adapters

### OpenCode

Project-scoped slash command:

```text
.opencode/commands/aocs-run.md
```

Project-scoped MCP config in `opencode.jsonc`:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "aocs-omega": {
      "type": "local",
      "command": ["python", "-m", "aocs_mcp"],
      "cwd": ".",
      "environment": {
        "OPENCODE_API_KEY": "{env:OPENCODE_API_KEY}",
        "PYTHONDONTWRITEBYTECODE": "1"
      },
      "enabled": true,
      "timeout": 300000
    }
  }
}
```

Optional global MCP config command:

```bash
opencode mcp add aocs-omega -- "python" "-m" "aocs_mcp"
```

On Windows, the global OpenCode config file is usually:

```text
C:\Users\<you>\.config\opencode\opencode.jsonc
```

Global config means the MCP server appears in the normal OpenCode GUI/TUI across
projects. Project config means it appears only inside that project. Prefer
project config until you intentionally choose global setup.

### Claude Code

Project-scoped slash command:

```text
.claude/commands/aocs-run.md
```

Example MCP config:

```json
{
  "mcpServers": {
    "aocs-omega": {
      "command": "python",
      "args": ["-m", "aocs_mcp"]
    }
  }
}
```

### Cursor / Codex / Other MCP Clients

Use the same MCP command:

```json
{
  "mcpServers": {
    "aocs-omega": {
      "command": "python",
      "args": ["-m", "aocs_mcp"]
    }
  }
}
```

## Safety Rules

- Do not make the outer coding agent read the skill and remember steps.
- Call `aocs_run_full`; let the runtime enforce every phase.
- Keep API keys in environment variables.
- Keep run artifacts in `.aocs/runs/`.
- Keep adapters project-scoped unless the user explicitly chooses global setup.
- Keep debug MCP tools off for normal use.

## Tests

Run the script-style tests:

```bash
python tests/test_doctor.py
python tests/test_models.py
python tests/test_config.py
python tests/test_scorer.py
python tests/test_phase0.py
python tests/test_runtime.py
python tests/test_router.py
python tests/test_opencode_go_direct_http.py
python tests/test_provider_adapters.py
```
