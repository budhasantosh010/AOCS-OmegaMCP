# AOCS‑Ω FastMCP Server

**Apex Omniscient Cognitive System** — quality-first multi-agent reasoning framework with fractal verification, adversarial red-teaming, and self-audit pipelines.

This is a **deterministic, executable MCP server** — not a SKILL.md the model can forget. Every AOCS phase runs as real Python code, called via the Model Context Protocol (MCP) from any compatible client.

## Quick Start

```bash
# 1. Install dependencies
pip install mcp pydantic anthropic openai

# 2. Connect to OpenCode
opencode mcp add aocs-omega -- "python" "-m" "aocs_mcp"

# 3. Verify
opencode mcp list
# → aocs-omega  running
```

## How It Works

When you ask a question in OpenCode/Claude Code, the model calls `aocs_analyze` which runs the full pipeline:

```
Phase 0 (Framing)  →  Phase 1 (Scoring)  →  Classify (Type 1/2/3)
  →  Route & Execute (Specialist → Red Team → ... → Judge)
  →  Quality Gates (10 checks)
  →  Observer (groupthink detection)
  →  Shadow Orchestrator (divergence check)
  →  Final Report
```

Everything runs in **real code**. The model can't skip or forget steps because it's not reading instructions — it's calling tools.

## LLM Calls

Each sub-agent (Specialist, Red Team, Judge, etc.) calls an LLM through the **LLM Router**:

1. **Host CLI** (primary, zero extra cost): shells out to `opencode run` / `claude --print`, using your host's configured models and API keys
2. **Direct API** (optional): configure API keys in `config/models.local.json` for per-role model selection

### Per-Role Model Configuration

```json
// config/models.local.json (gitignored)
{
  "direct_api": {
    "enabled": true,
    "anthropic": { "api_key": "sk-...", "default_model": "claude-sonnet-4-6" },
    "openai": { "api_key": "sk-...", "default_model": "gpt-4o" }
  },
  "roles": {
    "specialist": { "mode": "direct-api", "direct_api": { "provider": "anthropic", "model": "claude-opus-4-8" } },
    "deception-detector": { "mode": "direct-api", "direct_api": { "provider": "openai", "model": "gpt-4o-mini" } }
  }
}
```

## Tools

| Tool | Description | LLM Calls |
|---|---|---|
| `aocs_analyze` | Full pipeline: frame → score → classify → route → execute → verify → report | ~11 |
| `aocs_classify` | Classify problem Type 1/2/3 | 0 (rules) |
| `aocs_phase0_frame` | Phase 0 Problem Framing only | 3 |
| `aocs_phase1_score` | Score sub-problems on I/L/U/V | 0 |
| `aocs_run_type2` | Type 2 Triad: Specialist → RT → Contrarian → DD → Judge | 5 |
| `aocs_specialist` | Specialist Builder (Elon+Larson+Polya loop) | 1 |
| `aocs_red_team` | Adversarial challenge | 1 |
| `aocs_contrarian` | Truth-seeker evaluation | 1 |
| `aocs_deception_detector` | Rhetorical manipulation scan | 1 |
| `aocs_judge` | Blind evaluation with confidence score | 1 |
| `aocs_quality_gates` | 10 quality gates | 2 |
| `aocs_breakthrough` | Breakthrough protocols (analogical/reframe/backcast) | 2-3 |
| `aocs_swarm` | Volume Swarm (parallel workers) | N+2 |
| `aocs_observer` | Groupthink + overconfidence check | 1 |
| `aocs_prover` | Formal claim verification | 1 |

## Cross-Platform

### Claude Code
Add to `.claude/settings.json`:
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

### Cursor
Add to `.cursor/mcp.json`:
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

### Codex / Cline / Any MCP Client
Same pattern — `"python" "-m" "aocs_mcp"` as the command.

## Project Structure

```
aocs-mcp-server/
├── aocs_mcp/
│   ├── server.py              # FastMCP + tool registrations
│   ├── router.py              # LLM Router (host CLI / direct API)
│   ├── config.py              # Config loader
│   ├── phase0/                # Problem Framing (6 sub-phases)
│   ├── phase1/                # Scoring
│   ├── routing/               # Type 1/2/3 pipes + swarm
│   ├── agents/                # Specialist, Red Team, Contrarian, etc.
│   ├── quality/               # 10 quality gates, observer, shadow
│   ├── memory/                # Blackboard, graveyard, auditor
│   ├── breakthrough/          # Analogical, reframe, backcast
│   ├── learning/              # Flywheel
│   └── pipeline/              # Orchestrator + models
├── config/
│   ├── models.default.json    # Default routing (checked in)
│   └── models.local.json      # Local overrides (gitignored)
├── pyproject.toml
└── README.md
```

## New Laptop Setup

```bash
# 3 commands
git clone https://github.com/your-org/aocs-mcp-server.git
pip install mcp pydantic
opencode mcp add aocs-omega -- "python" "-m" "aocs_mcp"
```

No API keys needed — uses your host's LLM via CLI subprocess.

## Architecture

Built with **FastMCP** (Anthropic's official MCP Python SDK). Deterministic pipeline enforced in code. The model cannot skip or forget any phase because each phase is a real function call, not text instructions.

MCP protocol means it works with any client: OpenCode, Claude Code, Cursor, Codex, Cline, or any MCP-compatible tool.
