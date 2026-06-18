# AOCS Omega MCP - Task And Decision Log

This is the living text record for the AOCS Omega MCP project.

Purpose: preserve the full context of what was decided, why it was decided, what was built, what was tested, what was rejected, and what must remain true in future work.

Audience: a curious beginner should be able to read this without already knowing coding-agent terms. The goal is to avoid information loss. If the internal project context is "1", this document tries to make an outside reader see the same "1" instead of a distorted copy.

Rule for future updates: do not delete old entries. Add new dated sections. If something old was wrong, add a correction section that explains what changed and why.

## 2026-06-14 - Documentation Protocol Decision

### Decision

The project will keep two permanent documentation files:

1. `docs/000_AOCS_OMEGA_TASK_AND_DECISION_LOG.md`
   - Plain text record.
   - Explains every task, decision, tradeoff, test, failure, and conclusion.
   - Written so a beginner can understand it.

2. `docs/001_AOCS_OMEGA_UML_STATECHART.md`
   - Visual record.
   - Uses a UML state machine diagram, also called a statechart.
   - Uses composite states, meaning big states that contain smaller states.
   - Uses orthogonal regions, meaning multiple related areas shown side by side as concurrent regions.

### Why this decision exists

The user wants the project knowledge to survive handoffs, future chats, and future machines without shrinking into vague summaries. The user explicitly warned about information loss, like the Chinese whisper game, where even a tiny misunderstanding compounds over time. Because AOCS is meant to be a serious deterministic reasoning system, the documentation must preserve not only the final conclusions but also the reasoning path that led to them.

### Documentation standard

Every future chat should append to both docs:

- The task log records what happened in words.
- The statechart records the same project state visually.
- Neither file should be treated as disposable notes.
- Secrets must never be written into either file.

## 2026-06-14 - Original User Goal

### Plain-English version

The user built a deep reasoning skill called AOCS Omega. As a Markdown skill, it depends on the outer language model reading and following many important instructions. That failed in practice because even strong models can skim, forget, skip steps, or take shortcuts.

The user does not want AOCS to be only a prompt. The user wants AOCS to be a real engine: code runs the workflow, calls models at required steps, records the result, and gives the final output back to the coding agent.

### Main constraints from the user

1. Future-proof across coding agents.
   - Must be able to connect to tools like OpenCode, Claude Code, Cursor, Codex, and future coding agents.
   - The project should not be locked to one app.

2. Easy to trigger.
   - Ideally callable by a slash command, button, MCP tool, or simple CLI command.
   - The user should not have to remember a complex setup every time.

3. Deterministic workflow.
   - The outer coding agent must not be trusted to remember every AOCS step.
   - The required steps must be enforced by code.
   - The model should be called at specific steps, like sub-agents inside the workflow.

4. AOCS must be separate from the host coding agent.
   - OpenCode, Claude Code, Cursor, and Codex should only call AOCS.
   - They should not become AOCS.
   - They should not need their internal architecture changed.

5. Do not damage or rewrite existing coding-agent settings.
   - No silent global config edits.
   - No unexpected changes to Claude Code, OpenCode, Cursor, Codex, or other agent settings.
   - Prefer project-scoped config snippets.

6. Model provider flexibility.
   - AOCS should be able to use external provider APIs.
   - It should also be ready for future host-model callbacks if coding agents support them.
   - Different AOCS roles should eventually be able to use different models.

7. Secrets stay outside the repo.
   - API keys and GitHub tokens must use environment variables or local credential systems.
   - They must not be committed.

## 2026-06-14 - Terms Explained For Beginners

### Skill

A skill is usually a folder with a Markdown instruction file, often named `SKILL.md`. It tells a model how to behave.

Good for: teaching a model a method.

Bad for: forcing the model to run every step exactly, because the model can skip or forget instructions.

AOCS started as a skill, but the user correctly identified that a skill alone is not deterministic enough.

### Slash command

A slash command is a shortcut the user can type, such as `/aocs-run`.

Important point: a slash command is usually a button or shortcut, not the real engine. It should trigger AOCS, not contain all AOCS logic.

### Plugin

A plugin is usually a packaged extension for an app. Depending on the host app, it can include skills, commands, tools, MCP servers, or UI pieces.

Good for: distribution and install experience.

Bad for: being the core deterministic engine by itself, because each coding agent has its own plugin rules.

### MCP

MCP means Model Context Protocol. It is a standard way for an AI app to connect to external tools.

In this project, MCP lets a coding agent call one AOCS tool, and AOCS runs its own engine separately.

### CLI

CLI means command-line interface. It is a terminal command, for example:

```bash
aocs run "Analyze this problem deeply"
```

The CLI is the universal backup. Even if a coding agent has no good plugin system, it can often run a terminal command.

### Host CLI Mode

Host CLI Mode means AOCS would call a coding agent's command-line interface directly, for example:

```text
AOCS -> claude -p "prompt"
AOCS -> opencode run "prompt"
```

This can reuse the host app's logged-in model account, but it is fragile. It can stream in unusual formats, hang, touch local session databases, ask permissions, or behave differently across agents.

Decision: keep Host CLI Mode as a possible fallback, not the main path.

### MCP Sampling

MCP Sampling is an official MCP idea where an MCP server can ask the host client to run a model prompt.

Shape:

```text
AOCS MCP server -> host client -> host model -> AOCS MCP server
```

This is close to the user's dream of using the current coding agent's model directly without separate provider keys.

But it only works if the host app supports the MCP `sampling` capability. The protocol supports it, but the coding agent must expose it. We did not add it now because the user chose to avoid more headache for this version.

## 2026-06-14 - Main Architecture Decision

### Chosen architecture

```text
AOCS Core Runtime + One Public MCP Tool + CLI + Thin Agent Adapters
```

### Meaning

AOCS Core Runtime:
- The real engine.
- Owns the sequence of phases.
- Calls models when required.
- Writes run artifacts.
- Returns the final structured result.

One Public MCP Tool:
- The coding agent sees one main tool: `aocs_run_full`.
- There is also `aocs_analyze` as a compatibility alias.
- Internal phase tools are hidden by default.

CLI:
- Lets AOCS run from terminal without any coding-agent host.
- Provides a universal fallback.

Thin Agent Adapters:
- Slash commands and project config files.
- They act like buttons.
- They do not contain the real AOCS logic.

### Why this architecture was chosen

This shape satisfies the user's constraints:

- It is future-proof because MCP and CLI are portable.
- It is deterministic because the runtime controls the steps.
- It is safe because adapters are small and project-scoped.
- It avoids forcing the outer model to read and remember a huge skill.
- It avoids flooding coding agents with many MCP tools.

### Rejected architecture

Rejected: make AOCS only a Markdown skill.

Reason: the model can skim or skip parts.

Rejected: make the coding agent itself own the AOCS phases.

Reason: every host app behaves differently, so AOCS would not be portable.

Rejected: expose every AOCS phase as a public MCP tool.

Reason: OpenCode warns that MCP tools add context. Many tools would increase context load, confuse the outer model, and let the outer model call the wrong subset of steps.

Rejected for now: MCP Sampling as the main model provider.

Reason: it is promising, but not reliable across all current hosts unless the host declares support for sampling.

Rejected as primary path: Host CLI Mode.

Reason: direct API calls are cleaner, more deterministic, and easier to test.

## 2026-06-14 - Implemented Runtime Boundary

### Files

- `aocs_mcp/runtime.py`
- `aocs_mcp/cli.py`
- `aocs_mcp/server.py`
- `aocs_mcp/router.py`
- `aocs_mcp/pipeline/orchestrator.py`
- `aocs_mcp/utils/direct_api.py`
- `config/models.default.json`
- `config/models.local.json`

### Runtime request object

`AOCSRunRequest` is the portable input shape used by MCP, CLI, HTTP, and future adapters.

It contains:

- `problem`
- `domain`
- `risk`
- `fractal_depth`
- `context`
- `max_sub_agents`
- `persist`
- `metadata`

### Runtime engine

`AOCSRuntime` is the product boundary. MCP and CLI should call this runtime instead of knowing about internal AOCS phases.

It does these jobs:

1. Load config.
2. Create a run id.
3. Create a run directory if persistence is enabled.
4. Write `request.json` and running `status.json`.
5. Create a model router.
6. Create the orchestrator.
7. Run the full analysis.
8. Attach `run_id` and `run_dir` to the result.
9. Write trace, result, summary, and final status artifacts.

### Run artifact files

Each persisted run writes under `.aocs/runs/<run-id>/`:

- `request.json`: what the user asked AOCS to analyze.
- `status.json`: running, completed, or error status.
- `trace.json`: model call trace with role names and prompt hashes.
- `result.json`: full structured AOCS output.
- `summary.md`: human-readable summary.

Decision: keep these under `.aocs/runs/` so AOCS does not write into the host coding agent's own database or settings.

## 2026-06-14 - MCP Server Decision

### Implemented with FastMCP

The server uses Python FastMCP:

```python
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("aocs-omega")
```

### Public MCP tools

Normal use exposes only:

- `aocs_run_full`
- `aocs_analyze`

`aocs_analyze` calls `aocs_run_full` and exists as a friendly alias.

### Hidden debug tools

The old/internal phase tools are still present in code, but hidden unless config says:

```json
{
  "expose_debug_tools": true
}
```

Decision: hide debug tools by default so the outer coding agent cannot accidentally run only one phase and skip the rest.

## 2026-06-14 - CLI Decision

### Implemented command

The CLI supports:

```bash
aocs run "Analyze this problem"
```

It also supports:

- `--domain`
- `--risk`
- `--fractal-depth`
- `--context`
- `--max-sub-agents`
- `--output-dir`
- `--no-store`

Decision: the CLI is the universal backup adapter. If a future coding agent cannot use MCP cleanly, it can still call the CLI.

## 2026-06-14 - Model Provider Decisions

### Provider rule

The outer coding agent should not run AOCS's reasoning phases. AOCS calls model providers itself through the router.

### Implemented providers

The provider registry supports:

- `opencode-go`
- `openai`
- `anthropic`
- `claude` as alias for Anthropic
- `openrouter`
- `gemini`
- `google` as alias for Gemini
- `nvidia`
- `nvidia-nim` as alias for NVIDIA

### OpenCode Go direct HTTPS

For this version, the user wanted to test with paid OpenCode Go DeepSeek V4 Flash. The clean path is direct HTTPS:

```text
AOCS -> OpenCode Go hosted API -> model response
```

This does not open the OpenCode app.
This does not start the OpenCode TUI.
This does not use `opencode run`.
This does not attach to a local OpenCode server.

The API key is read from `OPENCODE_API_KEY`.

### OpenCode local server transport

A local-server transport remains available because it was useful during research, but it is not the preferred path for the user's current desire.

It uses:

- `POST /session`
- `POST /session/:id/message`
- `OPENCODE_SERVER_PASSWORD`

### OpenRouter

OpenRouter uses an OpenAI-compatible chat completions endpoint.

Environment variable:

```text
OPENROUTER_API_KEY
```

### Gemini / Google

Gemini uses Google's REST `generateContent` endpoint.

Environment variables:

```text
GEMINI_API_KEY
GOOGLE_API_KEY
```

### NVIDIA / NVIDIA NIM

NVIDIA uses an OpenAI-compatible endpoint.

Environment variable:

```text
NVIDIA_API_KEY
```

### OpenAI and Anthropic

OpenAI and Anthropic direct SDK paths remain supported.

Environment variables:

```text
OPENAI_API_KEY
ANTHROPIC_API_KEY
```

### Secrets decision

No API key belongs in Git.
No API key belongs in `models.default.json`.
No API key belongs in `models.local.json`.
No API key belongs in documentation.

## 2026-06-14 - Router Decisions

### Call tracing

The router records each model call with:

- call number
- AOCS role
- whether JSON was expected
- start time
- system prompt hash
- user prompt hash
- prompt lengths
- provider and model when known
- status
- response length
- duration
- error if any

Decision: store hashes instead of full prompts in trace so run artifacts are useful without dumping all prompt content into logs.

### Model-call budget

`max_sub_agents` is used as a call budget. If the workflow tries to exceed it, the router raises an error.

Decision: this keeps runs bounded and prevents runaway model calls.

### Structured output

`expect_json` is passed into provider calls so providers that support JSON response mode can be asked for structured output.

Decision: structured calls make deterministic parsing more reliable.

## 2026-06-14 - Orchestrator Decisions

### Main pipeline

The orchestrator runs:

```text
Phase 0 framing
Phase 1 scoring
classification
Type 1 / Type 2 / Type 3 route
quality gates
observer
shadow orchestrator
memory audit
final verdict
```

### Direct low-risk route

A direct low-risk route was added for simple arithmetic-like questions when:

- risk is `low`
- fractal depth is absent or zero
- the problem looks like a simple arithmetic expression

Example: `what is 2+2?`

This route calls the `direct-answer` role once and returns a short answer.

Decision: AOCS should not waste a deep multi-agent workflow on trivial, low-risk, directly verifiable questions.

### Type 1 result compatibility

Type 1 and Type 3 routes are wrapped into a Type 2-like quality subject when needed so quality gates and observer logic can still run with a consistent shape.

Decision: keep final verification consistent across routes.

## 2026-06-14 - Agent Adapter Decisions

### OpenCode project-scoped adapter

Files:

- `opencode.jsonc`
- `.opencode/commands/aocs-run.md`

Decision: use project-scoped OpenCode configuration instead of silently changing global OpenCode settings.

### Claude Code project-scoped adapter

File:

- `.claude/commands/aocs-run.md`

Decision: provide a slash-command-like entrypoint without changing global Claude Code settings.

### Cursor, Codex, and future agents

Decision: future agents should use the same idea:

- MCP command when supported.
- CLI fallback when MCP is not available.
- Thin adapter only.
- No core AOCS logic inside the host agent's prompt files.

## 2026-06-14 - Research Findings

### MCP Sampling

Official MCP sampling exists and uses `sampling/createMessage`.

Important facts:

- It lets an MCP server request a model call through the MCP client.
- The client keeps control of model access and permissions.
- The server does not need provider API keys if the client supports sampling.
- The client must declare the `sampling` capability.
- Model hints are only suggestions. The client chooses the final model.
- The client can reject the sampling request.

Decision for this version: do not implement MCP Sampling now. Keep it as a future optional provider adapter.

Source:

- https://modelcontextprotocol.io/specification/2025-06-18/client/sampling

### OpenCode CLI

OpenCode CLI can be used programmatically with `opencode run`, but it can also start a TUI when run without arguments.

Decision: do not use `opencode run` as the primary AOCS model path because direct HTTPS is cleaner for deterministic runtime.

Source:

- https://opencode.ai/docs/cli/

### OpenCode MCP

OpenCode supports local and remote MCP servers and project configuration. OpenCode docs warn that MCP tools add context, which supports the decision to expose a small public tool surface.

Source:

- https://opencode.ai/docs/mcp-servers/

### Claude Code CLI and MCP

Claude Code supports print mode with `claude -p` and supports MCP configuration. This makes host CLI mode possible for Claude, but still not ideal as the primary AOCS model path.

Sources:

- https://code.claude.com/docs/en/cli-reference
- https://code.claude.com/docs/en/mcp

### FastMCP

FastMCP is the Python SDK layer used to expose AOCS as an MCP server.

Source:

- https://modelcontextprotocol.io/docs/develop/build-server

## 2026-06-14 - Tests And Observed Results

### Direct provider test

OpenCode Go direct HTTPS was tested with the user's API key stored only in an environment variable.

Observed result:

```text
TEST_OK
```

Meaning: the provider adapter can call the model directly without opening OpenCode app or CLI.

### Full runtime simple test

Problem:

```text
what is 2+2?
```

Observed result:

```text
route: direct-low-risk
answer: 4
verdict: accept
total_llm_calls: 1
```

Meaning: the standalone AOCS runtime can run independently and return a result.

### MCP protocol test

The MCP tool list exposed:

```text
aocs_run_full
aocs_analyze
```

Calling `aocs_run_full` through MCP returned the simple arithmetic answer through the runtime.

Meaning: the MCP adapter correctly triggers the AOCS runtime.

### OpenCode MCP connection test

Normal OpenCode data/config hit an existing SQLite/WAL issue unrelated to AOCS.

An isolated OpenCode config/data test connected successfully:

```text
aocs-omega connected
```

Meaning: the AOCS MCP server itself can connect; the earlier issue was in the user's existing OpenCode local state.

### Script-style tests run during development

Tests that were run and passed during the session included:

- `tests/test_models.py`
- `tests/test_config.py`
- `tests/test_scorer.py`
- `tests/test_phase0.py`
- `tests/test_runtime.py`
- `tests/test_router.py`
- `tests/test_opencode_go_direct_http.py`
- `tests/test_provider_adapters.py`
- `tests/test_orchestrator_direct.py`

### Secret scan result

A scan was performed for obvious committed secrets. No OpenCode API key or server password was found in files.

Decision: continue scanning before every push.

## 2026-06-14 - Current Repository Change Summary

### Modified existing files

- `.gitignore`
- `README.md`
- `aocs_mcp/__init__.py`
- `aocs_mcp/pipeline/models.py`
- `aocs_mcp/pipeline/orchestrator.py`
- `aocs_mcp/router.py`
- `aocs_mcp/server.py`
- `aocs_mcp/utils/direct_api.py`
- `config/models.default.json`
- `config/models.local.json`
- `opencode.jsonc`
- `pyproject.toml`

### Added files and folders

- `.claude/commands/aocs-run.md`
- `.opencode/commands/aocs-run.md`
- `aocs_mcp/cli.py`
- `aocs_mcp/runtime.py`
- `tests/test_opencode_go.py`
- `tests/test_opencode_go_direct_http.py`
- `tests/test_orchestrator_direct.py`
- `tests/test_provider_adapters.py`
- `tests/test_router.py`
- `tests/test_runtime.py`
- `docs/000_AOCS_OMEGA_TASK_AND_DECISION_LOG.md`
- `docs/001_AOCS_OMEGA_UML_STATECHART.md`

## 2026-06-14 - Current Final Decision Before GitHub Push

The project should stay as it is for this version.

Do not add MCP Sampling right now.
Do not add more provider complexity right now.
Do not add a plugin installer right now.
Do not convert Host CLI Mode into the primary path right now.

Push this version with:

- standalone deterministic runtime
- FastMCP server
- one main public MCP tool
- CLI fallback
- OpenCode Go direct HTTPS provider
- OpenRouter/Gemini/NVIDIA provider support
- project-scoped OpenCode and Claude adapters
- run artifact storage
- tests
- living documentation

## Future Update Template

Use this template after every future chat.

```text
## YYYY-MM-DD - Short Title

### User request

### What changed

### Decisions made

### Reasons

### Files changed

### Tests or checks

### Risks or open questions

### Next step
```

## 2026-06-14 - Pre-Push Verification Entry

### What was checked

Before staging and pushing to GitHub, the repository was checked again.

### Secret scan

A secret scan was run for obvious pasted secrets and known sensitive fragments from the chat.

Result:

```text
No matches found.
```

The docs and repo contain placeholder examples such as `"..."`, but they do not contain the real API keys or GitHub token from the chat.

### Test results

The first direct test command failed because Python did not see the local package on `PYTHONPATH`. That was an environment setup issue, not an AOCS logic failure.

After setting `PYTHONPATH` to the repo root, these passed:

- `tests/test_models.py`
- `tests/test_scorer.py`
- `tests/test_phase0.py`
- `tests/test_router.py`
- `tests/test_orchestrator_direct.py`
- `tests/test_opencode_go.py`
- `tests/test_opencode_go_direct_http.py`
- `tests/test_provider_adapters.py`

Two tests that write temporary files needed to be run outside the sandbox because the sandbox blocked generated temp directories. After running outside the sandbox, these passed:

- `tests/test_config.py`
- `tests/test_runtime.py`

### Compile check note

`python -m compileall aocs_mcp` was attempted. It failed because Python tried to write `.pyc` files into `__pycache__` folders and the sandbox blocked those writes. This is not counted as a code failure because the script tests imported and exercised the touched modules successfully.

### Decision

Proceed to stage, commit, and push the current version.

## 2026-06-15 - Real OpenCode MCP Smoke Test

### User request

The user asked to test the project with the real OpenCode MCP server to confirm whether it actually works.

### Environment

- Repository: `C:\Users\Lenovo\Music\AOCS-Ω\AOCS Main MCP\AOCS MCP`
- Branch: `main`
- Local repo status before test: clean and aligned with `origin/main`
- OpenCode binary: `C:\Users\Lenovo\AppData\Roaming\npm\opencode.cmd`
- OpenCode version: `1.16.0`
- OpenCode auth list showed real configured credentials, including OpenCode Go.
- `OPENCODE_API_KEY` was not set in the shell environment used by the test.

### Test 1: OpenCode MCP server discovery

Command intent:

```text
Ask OpenCode to list MCP servers from the real project config.
```

Observed result:

```text
MCP Servers
- aocs-omega connected
  python -m aocs_mcp
1 server(s)
```

Conclusion:

OpenCode can discover and start the AOCS MCP server from `opencode.jsonc`.

### Test 2: Real OpenCode agent invokes AOCS MCP tool

Command intent:

```text
Run a real OpenCode agent session and ask it to call the aocs-omega MCP tool aocs_run_full exactly once.
```

The test did not use auto-approved permissions. An attempted command with broad auto-approval was rejected by the execution safety layer, so the safer version was run without bypassing permissions.

Observed OpenCode output:

```text
MCP_TOOL_RESULT=error: OPENCODE_API_KEY not set in environment
build · deepseek-v4-flash
⚙ aocs-omega_aocs_run_full {"problem":"what is 2+2?","domain":"software","risk":"low","fractal_depth":0,"max_sub_agents":1}
```

### Interpretation

This is a partial success and a precise failure.

What worked:

- OpenCode started normally.
- OpenCode used the requested model session.
- OpenCode saw the `aocs-omega` MCP server.
- OpenCode invoked the `aocs_run_full` MCP tool.
- The tool call reached the AOCS runtime.

What failed:

- The AOCS runtime tried to call the configured OpenCode Go direct HTTPS provider.
- The runtime did not receive `OPENCODE_API_KEY` in its process environment.
- Therefore the AOCS model call failed with: `OPENCODE_API_KEY not set in environment`.

### Decision

The OpenCode MCP integration itself works.

The full end-to-end AOCS run through OpenCode MCP requires starting OpenCode from a shell where `OPENCODE_API_KEY` is set, or changing future configuration/provider logic so AOCS can read a supported credential source without storing secrets in the repo.

For this version, do not read OpenCode's private auth file and do not store API keys in config files. Keep the key requirement explicit and environment-based.

### Next valid test

Run from a shell where the environment variable is set:

```powershell
$env:OPENCODE_API_KEY = "..."
opencode mcp list
opencode run "Use the aocs-omega MCP server tool aocs_run_full exactly once. Input: problem='what is 2+2?', domain='software', risk='low', fractal_depth=0, max_sub_agents=1. Return only the final answer."
```

Expected successful result:

```text
4
```

## 2026-06-15 - Real OpenCode Chat-Style MCP Test With API Key

### User request

The user asked to set the OpenCode Go API key and run the test like a real OpenCode GUI/chat problem-solving session.

### Security handling

The API key was passed only into the process environment for the test command. It was not written into repo files, documentation, Git config, or OpenCode project config.

### First realistic test result

The first realistic test asked OpenCode to call `aocs_run_full` for this medium-risk architecture question:

```text
A beginner is deciding whether AOCS should be a standalone runtime with MCP adapters or only a Markdown skill. Give the practical recommendation and why.
```

Observed result:

```text
MCP error -32001: Request timed out
```

OpenCode then manually improvised using the Markdown skill. That fallback behavior is not acceptable for deterministic AOCS because it means the outer coding agent is again doing the reasoning manually instead of letting the runtime enforce the workflow.

### Decision: increase OpenCode MCP timeout

The project-scoped OpenCode MCP timeout was changed from:

```json
"timeout": 30000
```

to:

```json
"timeout": 300000
```

Reason: 30 seconds is too short for a real AOCS run with multiple model calls. Five minutes is a more realistic project default for medium-depth AOCS analysis.

Files updated:

- `opencode.jsonc`
- `README.md`

### Strict low-risk end-to-end test

The next test used strict instructions:

- OpenCode must call `aocs_run_full` exactly once.
- OpenCode must not read or manually emulate the AOCS Markdown skill.
- If the tool fails, OpenCode must return `MCP_FAILED`.
- If the tool succeeds, OpenCode must return `MCP_SUCCESS`.

Input:

```text
problem: what is 2+2?
domain: software
risk: low
fractal_depth: 0
max_sub_agents: 1
```

Observed OpenCode output:

```text
MCP_SUCCESS=4.
```

AOCS artifact:

```text
run_id: 20260615T050331Z-61a33850
status: completed
verdict: accept
confidence: 99.0
total_llm_calls: 1
route: direct-low-risk
```

Conclusion: the real chain works for the low-risk deterministic route:

```text
OpenCode chat -> MCP tool -> AOCS runtime -> OpenCode Go API -> final answer
```

### Strict realistic architecture test

Input:

```text
problem: A beginner is deciding whether AOCS should be a standalone runtime with MCP adapters or only a Markdown skill. Give the practical recommendation and why.
domain: software architecture
risk: medium
fractal_depth: 1
max_sub_agents: 12
```

Observed OpenCode output:

```text
MCP_SUCCESS

The AOCS-Omega pipeline ran 11 LLM calls across 5 lenses. The final recommendation was context-dependent: for a beginner, start with a Markdown skill for simplicity and fast iteration, but design the rendering layer to be swappable so migration to a standalone runtime is easy later. Confidence: 90%; verdict flagged for human review.
```

AOCS artifact:

```text
run_id: 20260615T050411Z-56ffec8b
status: completed
verdict: flag_for_review
confidence: 90.0
total_llm_calls: 11
route: type2
problem_type: type2
```

### Final conclusion from this test

The real OpenCode chat-style MCP path works when:

1. `OPENCODE_API_KEY` is present in the environment before OpenCode starts.
2. The OpenCode MCP timeout is long enough for the AOCS runtime.
3. The prompt explicitly forbids manual fallback to the Markdown skill when testing deterministic execution.

Operationally verified path:

```text
OpenCode agent -> aocs-omega MCP server -> aocs_run_full -> AOCSRuntime -> LLMRouter -> OpenCode Go direct HTTPS -> AOCS result -> OpenCode summary
```

## 2026-06-15 - Setup Hardening And Coauthor Check

### User request

The user asked what to do next. The chosen next step was hardening, specifically adding beginner-facing diagnostics. The user also asked to remove Claude as a coauthor on GitHub.

### GitHub coauthor investigation

Full recent and all-history Git metadata was inspected.

Result:

```text
All commits are authored by budhasantosh010.
All commits are committed by budhasantosh010.
No Co-authored-by: Claude trailer was found.
No Claude/Anthropic author email was found.
```

Decision:

Do not rewrite Git history, because there is no Claude coauthor metadata in the repository history to remove. Rewriting history without a real metadata problem would create unnecessary risk.

Related note:

The repository does contain Claude Code adapter/config files. That is not the same as a GitHub coauthor. If the user wants Claude Code project adapter files removed later, that should be a separate explicit decision because it changes supported agent adapters.

### Added `aocs doctor`

New command:

```bash
aocs doctor
```

Purpose:

Give beginners a direct setup check instead of making them understand MCP, Python imports, provider keys, and OpenCode configuration manually.

Checks included:

- Python version
- `mcp` package import
- `pydantic` package import
- `config/models.default.json`
- `config/models.local.json`
- config JSON loading
- supported model-provider environment variable names
- `opencode.jsonc`
- OpenCode binary/version
- OpenCode MCP connection status for `aocs-omega`

Security rule:

`aocs doctor` reports which API key environment variable names are set. It does not print secret values.

### Added JSON output

New command:

```bash
aocs doctor --json
```

Purpose:

Allow future installer scripts, CI checks, or GUI wrappers to read setup status mechanically.

### Added no-OpenCode mode

New command:

```bash
aocs doctor --no-opencode
```

Purpose:

Allow diagnostics on machines that are using Claude Code, Cursor, Codex, or plain CLI instead of OpenCode.

### Windows-specific fix

Initial full doctor check could not find OpenCode from Python even though PowerShell could run it. The cause was Windows command resolution: Python did not find `opencode`, but the installed executable is `opencode.cmd`.

Fix:

Doctor now checks both:

```text
opencode
opencode.cmd
```

and uses the resolved executable path for version and MCP checks.

### Verification

Commands run:

```bash
python -m aocs_mcp.cli doctor --no-opencode
python -m aocs_mcp.cli doctor --no-opencode --json
python -m aocs_mcp.cli doctor
python tests/test_doctor.py
python tests/test_router.py
```

Observed full doctor result:

```text
[OK] python: 3.13.5
[OK] mcp package: import succeeded
[OK] pydantic package: import succeeded
[OK] models.default.json: config/models.default.json
[OK] models.local.json: config/models.local.json
[OK] config load: 8 top-level keys loaded
[WARN] model API environment: no supported provider API key is set
[OK] opencode.jsonc: opencode.jsonc
[OK] opencode binary: 1.16.0
[OK] opencode mcp: aocs-omega connected

Result: warn (0 fail, 1 warn)
```

Interpretation:

The local setup is structurally valid. The only warning is expected because no model provider API key was set in the shell used for this diagnostic run.

## 2026-06-15 - Beginner No-Install Test Confusion And Doctor Encoding Fix

### User request

The user tried the no-install command:

```powershell
python -m aocs_mcp.cli doctor
```

and asked why the output looked wrong.

### Problem 1: `doctor` crashed on Windows text decoding

Observed error:

```text
UnicodeDecodeError: 'charmap' codec can't decode byte ...
AttributeError: 'NoneType' object has no attribute 'strip'
```

Cause:

`aocs doctor` runs `opencode mcp list` internally. OpenCode prints some Unicode symbols in its output. Windows PowerShell / Python was trying to decode that output using the local `cp1252` encoding, which could not decode one of the bytes.

Then Python's subprocess output became `None`, and our code tried to call `.strip()` on `None`.

Fix:

`aocs_mcp/doctor.py` now runs subprocess checks with:

```python
encoding="utf-8"
errors="replace"
```

and safely handles empty output:

```python
(proc.stdout or "").strip()
```

Result after fix:

```text
[OK] opencode binary: 1.16.0
[OK] opencode mcp: aocs-omega connected
```

### Problem 2: `python -m aocs_mcp.cli run "what is 2+2?"` used the deep default route

Observed behavior:

The user ran:

```powershell
python -m aocs_mcp.cli run "what is 2+2?"
```

That command uses the default CLI settings:

```text
risk: medium
fractal_depth: 1
```

Because of those defaults, AOCS treated `2+2` as a medium-risk analysis problem instead of a trivial arithmetic smoke test. It ran the deeper Type 2 pipeline and produced over-analysis.

Correct beginner smoke-test command:

```powershell
python -m aocs_mcp.cli run "what is 2+2?" --risk low --fractal-depth 0 --max-sub-agents 1
```

Reason:

```text
--risk low
```

tells AOCS this is safe and simple.

```text
--fractal-depth 0
```

tells AOCS not to do recursive deep analysis.

```text
--max-sub-agents 1
```

keeps the model-call budget small.

### Important security note

The user's pasted terminal transcript included an API key. Any API key pasted into chat or a text file should be considered exposed and rotated before serious use.

## 2026-06-15 - Fix Beginner Arithmetic Smoke Test

### User request

The user asked Codex to run the terminal tests and fix the errors directly after seeing this command fail or over-analyze:

```powershell
python -m aocs_mcp.cli run "what is 2+2?"
```

### Root cause

The CLI default for `aocs run` is a real analysis posture:

```text
risk: medium
fractal_depth: 1
```

That is reasonable for serious problems, but bad for beginner smoke tests. A trivial arithmetic question entered the deep AOCS pipeline, which required structured JSON from model calls. The model returned prose instead of JSON at one phase, causing:

```text
Could not extract JSON from response
```

### Decision

Obvious two-number arithmetic should be answered deterministically by code before any LLM call, regardless of risk or fractal-depth defaults.

Reason:

Smoke tests must be stable, cheap, and beginner-safe. A question like `what is 2+2?` should not spend model calls, require API keys, or enter Type 2 reasoning.

### Implementation

Added deterministic arithmetic handling in `AOCSOrchestrator._maybe_direct_low_risk`.

For simple expressions such as:

```text
2+2
2 - 1
3 * 4
8 / 2
```

AOCS now returns a direct result without calling a model.

Routes:

- `direct-low-risk` when the user explicitly sets `risk=low`
- `direct-arithmetic` when the user forgets flags and uses the default medium-risk CLI path

### Verified exact beginner command

Command:

```powershell
python -m aocs_mcp.cli run "what is 2+2?" --no-store
```

Observed result:

```text
problem_type: type1
route_taken: direct-arithmetic
total_llm_calls: 0
specialist_proposal: 4
verdict: accept
confidence: 100.0
```

### Tests run

```bash
python tests/test_orchestrator_direct.py
python tests/test_doctor.py
python tests/test_router.py
python tests/test_runtime.py
python tests/test_provider_adapters.py
python tests/test_opencode_go_direct_http.py
python -m aocs_mcp.cli doctor --no-opencode
```

All passed.

---

## 2026-06-18 - Updated Skill Re-Audit And Complete Runtime Parity

### User request

The user asked for a new audit of the updated AOCS Omega skill at:

```text
C:\Users\Lenovo\Music\AOCS-OMEGA\main resource\my-aocs-omega
```

The actual Windows folder uses the Omega character in the path. The operational
skill file contains 520 lines and defines the complete AOCS-Omega behavior.

The user requirement was stronger than "add the important parts." The user
required every operational part of the skill to be implemented and reachable
through the standalone engine, with nothing silently left as a Markdown-only
instruction.

### Definition of complete parity

For this implementation, "complete parity" means:

1. Every skill protocol has a code-owned trigger or deterministic position in
   the pipeline.
2. Every required model role is called by the engine, not remembered by the
   outer coding agent.
3. Every protocol produces structured data that can be persisted and displayed.
4. Conditional protocols run when their stated condition is true.
5. The engine records what happened, including failures, reroutes, assumptions,
   rejected ideas, and learning.
6. The normal MCP surface exposes one complete entrypoint so a host agent cannot
   accidentally skip phases.

This does not mean AOCS can manufacture missing physical evidence. A runtime can
enforce reasoning, challenge, traceability, and verification attempts. Real
laboratory tests, production measurements, legal review, or other external
reality checks still require the relevant external tool or qualified human.
AOCS now records that boundary instead of pretending that model prose is
physical proof.

### Architecture decision retained

The architecture remains:

```text
AOCS Core Runtime
-> deterministic orchestrator
-> model router
-> provider APIs or configured host adapters
-> persisted AOCS artifacts

Thin host adapter
-> one public MCP tool: aocs_run_full
-> or CLI: aocs run
```

The outer coding agent remains a caller. It does not become the AOCS workflow.

### Test-driven implementation method

The work followed RED, GREEN, REFACTOR cycles.

Examples of observed RED failures:

- Complete result models did not exist.
- Context was not preserved through Phase 0.
- Model-derived scoring and classification were not wired.
- Deep Test failure did not return to Multi-Framer.
- Blackboard values were truncated.
- Type 1 did not return real verification/TMR/prover artifacts.
- Swarm peer audit was incomplete.
- Type 3 stopped before mutation, pruning, serendipity, simulation, paradigm,
  and quest behavior.
- Blindspot and fractal modules did not exist.
- Kill-switch and Universal Goal protocols did not exist.
- Quality gates did not consume real verifier/TMR/prover/observer outputs.
- The Observer was called twice.
- Shadow only warned instead of executing the safer route.
- Chaos Variable did not change the conclusion.
- Paradigm alerts did not run breakthrough protocols.
- The canonical orchestrator did not expose memory and learning artifacts.
- The default role map omitted newly introduced agents.
- The default model-call budget was too small for critical runs.
- The dashboard omitted the new protocol outputs.
- Two public MCP tools were registered instead of one.
- Type 1 reused the Type 2 Specialist prompt and ran Prover before critical TMR.
- The Volume Swarm existed but was unreachable from normal classification.
- Higher-Dimension Reframing discarded its new root problem.
- Memory Auditor treated different assumptions as contradictions.
- Direct low-risk runs skipped blackboard and flywheel learning.

Each failure was reproduced in a focused test before the production change.

### Complete implementation record

#### Structured result contract

`aocs_mcp/pipeline/models.py` now represents:

- deterministic verification
- recursive fractal challenges
- blindspot results
- kill-switch state
- quests
- break-framework output
- Universal Goal roles and closed loop
- swarm output
- blackboard, graveyard, and learning entries
- full attempt history
- paradigm reframe evidence
- classification decomposition and chunks

Decision: protocol outputs must be data, not only prose, so they survive
handoffs and can be inspected without reading model prompts.

#### Phase 0

The engine now performs:

```text
Parser + supplied context
-> Multi-Framer
-> Assumption Mapper
-> Uncertainty Quantifier
-> Root Problem Extractor
-> four-question Deep Test
```

If the Deep Test fails, the engine returns to Multi-Framer with the rejected
root and all four answers. It allows two reframes, for three total attempts.

Decision: the loop is code-owned. The model cannot skip the return transition.

#### Phase 1

The Scoring Engine now asks a model to score every proposed vertical on:

- Impact
- Leverage
- Urgency
- Structural Learning Value

Code owns the official weighting:

```text
I * 0.35 + L * 0.25 + U * 0.20 + V * 0.20
```

Code also owns Noise, Small, Big, and Critical zone assignment.

Decision: the model supplies judgment; code supplies the fixed formula.

#### Classification and Volume Swarm selection

Classification is now a structured model call that selects:

- Type 1, Type 2, or Type 3
- low, medium, high, or critical risk
- fractal depth 0 through 3
- whether the work is decomposable
- concrete chunks for a Volume Swarm

If a Type 2 task is decomposable, the canonical route runs:

```text
N workers
-> peer audits
-> independent auditor
-> synthesis
-> Type 2 high-stakes debate using the synthesized evidence
```

Decision: the swarm is no longer a disconnected helper.

#### Type 1 exact route

Type 1 now uses a dedicated Type 1 Specialist prompt, not the generic Type 2
Specialist prompt.

The role must apply:

```text
Question
-> Cut
-> Simplify
-> Speed up
-> Automate
```

The exact critical route is:

```text
Type 1 Specialist
-> Deterministic Verifier
-> TMR when critical
-> Prover
```

Critical TMR produces two independent alternatives and a separate comparison.

#### Type 2 exact route

The Type 2 route remains blind where required:

```text
Specialist
-> anonymized Red Team
-> Contrarian
-> Deception Detector
-> blind Judge
```

High and critical outputs include an external review hook.

#### Type 3 complete route

The Type 3 engine now executes:

```text
multiple lenses
-> first principles
-> competing hypotheses
-> Idea Mutator
-> Ruthless Pruner
-> Protected Weirdness Reserve
-> Graveyard archive
-> Serendipity Injector
-> thought experiments and simulations
-> anomaly capture
-> Paradigm Detector
-> Graveyard resurrection check
-> Quest Tracker with 10 percent protected allocation
```

Rejected ideas are never silently deleted. Their reason and assumptions are
stored in the Graveyard.

#### Fractal verification

Depth behavior is explicit:

- Depth 0: no recursive challenge.
- Depth 1: Red Team, Contrarian, Judge.
- Depth 2: depth 1 plus Observer and Shadow review of the verification.
- Depth 3: a new Red Team, Contrarian, Judge challenge of the second-order
  verification.

The executed depth and every challenge are stored in `FractalResult`.

#### Blindspot discipline

The Blindspot Hunter answers all five mandatory questions:

- What perspective is missing?
- What data is missing?
- What would an outsider notice?
- What would falsify the conclusion?
- What simple factor may be overlooked?

It also returns recommended actions.

#### Shadow Orchestrator

Shadow classification is independent.

If Shadow selects a more conservative route, the engine now executes that route
once. The route record shows transitions such as:

```text
type1->shadow:type2
```

Decision: a safety reroute is an execution decision, not merely warning text.
Conservatism is compared by risk first, then problem type (`type3` over `type2`
over `type1`), then fractal depth. This means equal-risk disagreements no longer
automatically favor the original route.

#### Observer and Chaos Variable

The Observer runs once and its artifact is reused by Gate 9.

If it injects a Chaos Variable, the engine calls a separate
`chaos-reconsideration` role. That role must rebuild the answer from first
principles. The revised answer and recalibrated confidence replace the previous
conclusion.

#### Ten quality gates

The ten gates now consume actual artifacts:

1. Specialist confidence
2. Deterministic verification
3. Red Team, Contrarian, and Judge review
4. Reasoning trajectory
5. Falsifiable prediction
6. Concrete adversarial flaws
7. Actual critical-risk TMR consensus
8. Actual Prover claims
9. The one Observer artifact
10. Human review threshold

Decision: no gate may claim that a protocol ran when its artifact is absent.

#### Memory and source decay

Blackboard entries preserve:

- exact value
- provenance
- confidence
- timestamp

Source decay is applied before delivery.

Memory Auditor now checks only identity-bearing claim keys such as `claim:`,
`fact:`, and `decision:` for conflicting values. Different assumptions are a
set, not a contradiction.

Unresolved contradictions or low-confidence critical entries cap confidence at
94 and prevent an `accept` verdict.

#### Kill-switch

When the same approach fails quality twice:

```text
failure 1
-> one bounded retry of the same approach
-> failure 2
-> no third same-path attempt
-> Analogical Mining
-> Higher-Dimension Reframing
-> Future Backcasting
-> Break-Framework
-> fresh Phase 0
-> fresh scoring
-> fresh classification
```

The kill-switch result stores the failure count, combined reasons, reframed root
problem, and new classification.

#### Breakthrough protocols

Cross-Domain Analogical Mining now also requests a concrete feasibility test.

Higher-Dimension Reframing preserves the actual reframed problem. On a Type 3
paradigm alert, that new problem is fed into fresh framing, scoring, and
classification. The result is stored as `paradigm_reframe`.

Future Backcasting preserves its milestones and the "maybe that became yes"
turning point.

Break-Framework stores temporary phase order, temporary roles, verification
order, and proposal.

#### Universal Goal-Achievement Protocol

For novel Type 3 goals such as "build a complete system," the engine runs:

```text
define the single job
-> discover goal-specific roles
-> identify existing pieces
-> connect a closed loop
-> identify the feedback role
-> define a crude working version
-> measure role costs
-> find the root inefficiency
-> replace it with an outcome-equivalent architecture
-> recalculate cost
```

Decision: the goal dictates its roles. The runtime does not force a generic
fixed role template.

#### Learning and flywheel

Every completed normal or direct run records:

- reusable heuristic
- success or failure pattern
- one of the four error classes when unsuccessful:
  - Wrong assumption
  - Flawed model
  - Execution error
  - Random variance
- an explicit confidence-calibration update

The calibration update is stored as `model_update` on the Blackboard.

#### Direct low-risk collapse

Simple low-risk arithmetic still uses exactly one LLM answer call. Code does not
compute the answer secretly.

The direct route now also records:

- structural verification
- approach history
- Blackboard provenance
- flywheel learning

Decision: directness does not mean loss of traceability.

#### Runtime, artifacts, and dashboard

Persisted runs include:

```text
request.json
status.json
trace.json
result.json
blackboard.json
graveyard.json
learning.json
summary.md
```

The standalone dashboard can derive visible entries for:

- Type 1 and Type 2 specialists
- verifier
- TMR
- Prover
- Red Team
- Contrarian
- Deception Detector
- Judge
- Volume Swarm
- all Type 3 stages
- Quest Tracker
- Blindspot Hunter
- Fractal Verification
- Observer
- Shadow
- quality gates
- Kill Switch
- breakthrough protocols
- Break-Framework
- Universal Goal Protocol
- paradigm reframe
- Memory Audit
- Learning Flywheel

#### Public MCP surface

The normal MCP server now registers only:

```text
aocs_run_full
```

`aocs_analyze` remains an internal Python compatibility function but is not
advertised to MCP clients.

Decision: one public tool minimizes context usage and prevents partial pipeline
execution.

#### Model-call budget

The default budget changed from 16 to 64 model calls in:

- portable run request
- CLI
- MCP tool
- orchestrator

Decision: a default budget must be large enough for critical fractal depth,
kill-switch escape, and Type 3 breakthrough paths. Users may still lower it
explicitly.

### Skill compliance matrix

The user required documentation to remain in exactly two living files. For that
reason, the compliance matrix is embedded here instead of creating a third
documentation source.

| Skill section | Runtime implementation | Main evidence | Status |
| --- | --- | --- | --- |
| 1 Core principles | Direct path, risk-scaled expansion, independent roles, provenance, truth-calibrated verdicts | orchestrator, router, blackboard | Implemented |
| 2 Type classification | Model classification with code validation | `routing/classifier.py` | Implemented |
| 3 Phase 0 | Parser, 3-5 frames, assumptions, uncertainty, root, Deep Test reframe loop | `phase0/*`, orchestrator | Implemented |
| 4 Phase 1 | Model I/L/U/V scoring plus code-owned formula and zones | `phase1/scorer.py` | Implemented |
| 5 Fractal depth | Explicit depth 0/1/2/3 call sequences | `quality/fractal.py` | Implemented |
| 6 Blackboard and Graveyard | Provenance, confidence, timestamp, decay, archive, resurrection | `memory/*` | Implemented |
| 7.1 Type 1 | Dedicated Specialist, verifier, critical TMR, Prover | `type1_pipe.py` | Implemented |
| 7.2 Type 2 triad | Blind debate, deception scan, Judge, external review | `type2_pipe.py` | Implemented |
| 7.2.2 Volume Swarm | Worker, peer audit, auditor, synthesis, canonical selection | `swarm.py`, orchestrator | Implemented |
| 7.3 Type 3 | All nine discovery stages and protected quest | `type3_pipe.py` | Implemented |
| 8 Shadow | Independent classification and safer route execution | `shadow_orch.py`, orchestrator | Implemented |
| 9 Observer | Groupthink/overconfidence and first-principles Chaos reconsideration | `observer.py`, orchestrator | Implemented |
| 10 Quality gates | Ten gates use real artifacts | `quality/gates.py` | Implemented |
| 11 Memory Auditor | Claim conflict detection, unverified entries, confidence downgrade | `memory/auditor.py` | Implemented |
| 12 Kill-switch | Two failures, no third attempt, reframe and reclassify | `quality/kill_switch.py`, orchestrator | Implemented |
| 13 Quest Tracker | 10 percent protected quest, archive/resurrect operations | `routing/quest_tracker.py` | Implemented |
| 14.1 Analogical Mining | Structural analogy, transplant, feasibility test | `analogical_mining.py` | Implemented |
| 14.2 Higher Dimension | Preserved reframe and fresh Phase 0/scoring/classification | `higher_dimension.py`, orchestrator | Implemented |
| 14.3 Future Backcast | Milestones, failures, maybe-to-yes, frame shift, roadmap | `future_backcast.py` | Implemented |
| 14.4 Break-Framework | Temporary solving structure and verification order | `break_framework.py` | Implemented |
| 14.5 Universal Goal | Job, roles, pieces, loop, crude version, inefficiency replacement | `universal_goal.py` | Implemented |
| 15 Learning | Heuristic, four error classes, calibration update | `learning/flywheel.py` | Implemented |
| 16 Output | Structured labeled artifacts, confidence, recommendations, dashboard | models, runtime, dashboard | Implemented |
| 17 Domain adaptation | Open-domain parser/prompts and optional explicit hints | parser, framer, classifier, Type 3 | Implemented |

### New and changed tests

Focused test files now cover:

```text
tests/test_skill_compliance.py
tests/test_memory_complete.py
tests/test_routes_complete.py
tests/test_type3_complete.py
tests/test_fractal_and_blindspot.py
tests/test_kill_switch.py
tests/test_universal_goal.py
tests/test_quality_complete.py
tests/test_orchestrator_complete.py
tests/test_server_surface.py
```

### Verification result before browser and GitHub publication

```text
python -m pytest tests -q
81 passed
```

No test is currently failing.

### Security and settings statement

- No API key was added to source code or documentation.
- Provider secrets remain environment variables.
- No global coding-agent configuration was rewritten by this implementation.
- AOCS artifacts remain inside the isolated AOCS run directory.
- The public MCP context remains one tool.

### Final local verification evidence

Commands and results:

```text
python -m pytest tests -q
81 passed

ruff check .
All checks passed

python -m compileall -q aocs_mcp
compileall: ok

git diff --check
ok
```

Security checks:

- No hardcoded credential pattern was found in added lines.
- No shell injection, `eval`, `exec`, unsafe pickle, or formatted SQL pattern
  was found.
- The OpenCode API key and GitHub token previously pasted in chat are not
  present anywhere in the repository.

Doctor result:

```text
failures: 0
warnings: 1
OpenCode MCP: aocs-omega connected
```

The one warning is that this Codex terminal does not currently have a supported
provider API key environment variable. A fresh paid-model call was therefore
not attempted. The implementation did not reuse or write a secret from chat.

Dashboard verification:

```text
URL: http://127.0.0.1:8766/
Desktop: 1265 px client width, 1265 px scroll width
Mobile: 375 px client width, 375 px scroll width
```

There was no horizontal overflow at either size. Desktop retained the run-list
and detail layout. Mobile collapsed to one column with all five metrics and all
timeline steps still present.

The dashboard was tested against historical run artifacts from June 15, 2026.
Those old artifacts correctly continue to display their old duplicate Observer
and old assumption-audit results. New runs use the corrected engine and will not
reproduce those historical behaviors.

## 2026-06-15 - Independent AOCS Dashboard and Visible Agent Answers

### Trigger

The user clarified that answer visibility must belong to AOCS itself, not to
OpenCode, Claude, Codex, Cursor, or any outer coding agent.

User requirement:

- AOCS should be viewable independently.
- The user should be able to see what happened inside a run.
- The view should show which AOCS agent ran and what answer/output it produced.
- This visual representation is part of the AOCS engine, not part of a coding
  agent adapter.

### Decision

Add an AOCS-owned local dashboard server.

The dashboard is launched with:

```powershell
aocs dashboard
```

or:

```powershell
python -m aocs_mcp.cli dashboard
```

Default URL:

```text
http://127.0.0.1:8765/
```

### Why This Design

The dashboard reads `.aocs/runs/` artifacts directly.

That means:

- OpenCode does not need to display the run.
- Claude Code does not need to display the run.
- Codex does not need to display the run.
- Cursor does not need to display the run.
- Any future coding agent can trigger AOCS while AOCS still owns its own visual
  audit trail.

This preserves the architecture rule:

```text
Adapters are buttons. AOCS is the machine.
```

### Code Added

New file:

```text
aocs_mcp/dashboard.py
```

New CLI command:

```text
aocs dashboard
```

Dashboard endpoints:

```text
GET /              browser UI
GET /api/runs      list persisted runs
GET /api/run?id=   load one run with derived agent timeline
```

New test:

```text
tests/test_dashboard.py
```

### What The Dashboard Shows

The dashboard shows:

- run history
- run directory
- problem text
- final verdict
- confidence
- route taken
- problem type
- total LLM calls
- final recommendations
- agent timeline
- raw summary

The agent timeline maps raw AOCS artifacts into readable steps such as:

- Direct Answer
- Multi-Framer
- Root Problem Extractor
- Deep Test
- Specialist
- Red Team
- Contrarian
- Deception Detector
- Judge
- Quality Gates
- Observer
- Shadow Orchestrator
- Type 3 Lens Agent
- Type 3 First Principles
- Type 3 Hypothesis Generator
- Memory Audit

### Trace Preview Change

Before this change, `trace.json` stored role names, timing, providers, models,
prompt hashes, and response length, but not visible model output.

Now future traces store a local response preview:

```json
{
  "response_preview": "first part of the model answer..."
}
```

Default preview size:

```json
{
  "runtime": {
    "trace_response_preview_chars": 2000
  }
}
```

This is local-only in `.aocs/runs`. It makes the dashboard useful without asking
the coding agent to remember or display the AOCS internal run.

To disable previews:

```json
{
  "runtime": {
    "trace_response_preview_chars": 0
  }
}
```

### OpenCode Global Status Observed

OpenCode global config path on this laptop:

```text
C:\Users\Lenovo\.config\opencode\opencode.jsonc
```

Observation:

- A global `aocs-omega` MCP entry already exists.
- It points to Python 3.10.
- Python 3.10 has `aocs-mcp-server` installed editable from this repo.
- `opencode mcp list` failed during inspection with a local database
  `PRAGMA wal_checkpoint(PASSIVE)` error, so no automatic global config rewrite
  was performed.

Security observation:

- The global OpenCode config contains a plaintext provider key.
- Do not paste that file into chats or commit it to GitHub.

### Verification

Focused tests:

```powershell
python -X utf8 -B -m pytest tests/test_dashboard.py tests/test_router.py tests/test_runtime.py tests/test_open_domain_defaults.py -p no:cacheprovider
```

Result:

```text
8 passed
```

Full suite:

```powershell
python -X utf8 -B -m pytest tests -p no:cacheprovider
```

Result:

```text
40 passed in 3.80s
```

Dashboard server started:

```text
http://127.0.0.1:8765/
```

Verified endpoint:

```text
GET http://127.0.0.1:8765/api/runs
```

Result:

- endpoint responded successfully
- it listed existing `.aocs/runs` records

### Global OpenCode Slash Command Installed

The global OpenCode command file was installed at:

```text
C:\Users\Lenovo\.config\opencode\commands\aocs-run.md
```

This makes `/aocs-run` available in normal/global OpenCode sessions, not only in
the AOCS project folder.

The command content matches the project-scoped `.opencode/commands/aocs-run.md`
and tells OpenCode to call only the canonical MCP tool:

```text
aocs_run_full
```

It also preserves the open-domain rule:

```text
Do not provide domain, risk, or fractal_depth unless the user explicitly gave them.
```

## 2026-06-15 - Correction: Remove Hidden Software/Medium Defaults

### Trigger

The user rejected the earlier behavior where AOCS silently used `domain=software`,
`risk=medium`, or a fixed fractal-depth sentinel when the caller did not provide
those values.

User requirement, restated precisely:

- Every problem is a new problem.
- AOCS must not force a software worldview unless the user explicitly gives that
  domain or the problem evidence points there.
- AOCS must not receive a caller-injected medium risk level just because no risk
  was provided.
- AOCS must not rely on slash-command defaults that shape the problem before the
  engine sees it.
- The skill structure can guide the engine, but the problem domain, risk, route,
  and depth must be inferred inside the AOCS pipeline.

### Decision

The public request boundary is now open-domain by default.

This means:

```text
domain omitted -> request.domain is None
risk omitted -> request.risk is None
fractal_depth omitted -> request.fractal_depth is None
```

This does not mean AOCS has no classification. It means the caller does not
inject a classification before AOCS runs. After Phase 0, the classifier may still
decide that a problem is Type 1, Type 2, or Type 3 and assign a risk level based
on the available framing evidence.

### Code Changes

Updated request/adapters:

- `AOCSRunRequest.domain`: changed from `"software"` to `None`
- `AOCSRunRequest.risk`: changed from `"medium"` to `None`
- CLI `--domain`: optional hint only
- CLI `--risk`: optional hint only
- CLI `--fractal-depth`: optional hint only; removed `-1` sentinel
- MCP `aocs_run_full.domain`: optional hint only
- MCP `aocs_run_full.risk`: optional hint only
- MCP `aocs_run_full.fractal_depth`: optional hint only
- `.opencode/commands/aocs-run.md`: now tells the agent not to provide
  `domain`, `risk`, or `fractal_depth` unless the user explicitly gave them
- `.claude/commands/aocs-run.md`: same correction

Updated Phase 0:

- Parser now writes `Domain: auto-infer from problem` when no domain hint exists.
- Multi-Framer lenses are no longer software-specific.
- Multi-Framer prompt explicitly says not to assume software.
- Assumption Mapper now uses open-domain assumptions when no domain is given.
- Software assumptions are still available only when the caller explicitly
  provides `domain="software"`.

Updated Type 3:

- Type 3 discovery lenses are now generic:
  `Domain Inference`, `First Principles`, `Evidence and Measurement`,
  `Systems and Constraints`, `Safety and Consequences`.
- Type 3 prompt explicitly says to infer the correct discipline and not assume
  software unless the problem evidence points there.

Updated classification wording:

- Removed wording that said `Default to Type 2`.
- Type 2 is now described as a classifier decision when the problem is neither
  clearly established nor clearly frontier-level.

### Important Clarification

Risk values such as `medium` can still appear after classification. That is not
the same as a caller default.

Bad behavior removed:

```text
Caller omits risk -> adapter sends risk=medium before AOCS thinks
```

Allowed behavior:

```text
Caller omits risk -> AOCS runs Phase 0 -> classifier decides risk=medium
```

The first one is an outside default. The second one is an internal AOCS decision.

### Tests Added/Updated

Added:

- `tests/test_open_domain_defaults.py`

Updated:

- `tests/test_phase0.py`
- `tests/test_models.py`
- `tests/test_runtime.py`
- `tests/test_orchestrator_direct.py`

The regression test checks:

- parser without domain does not say `software`
- assumption mapper without domain does not use software assumptions
- CLI parser leaves domain/risk/fractal-depth absent
- CLI runtime request preserves those absent values

### Test Run

Full suite:

```powershell
python -X utf8 -B -m pytest tests -p no:cacheprovider
```

Result:

```text
38 passed in 4.74s
```

### Current Correct Contract

When the user runs:

```powershell
python -m aocs_mcp.cli run "find the cure of cancer"
```

the request sent into AOCS is:

```json
{
  "domain": null,
  "risk": null,
  "fractal_depth": null
}
```

AOCS must infer domain/risk/depth internally.

When the user explicitly runs:

```powershell
python -m aocs_mcp.cli run "debug this Python error" --domain software --risk high --fractal-depth 2
```

then those values are accepted as user-provided hints.

### Supersedes Earlier Notes

Earlier documentation sections mention using `domain=software`, `risk=medium`,
or `--risk low --fractal-depth 0` for smoke tests. Those sections remain as
historical records, but this section supersedes them as the current design rule.

Current rule:

```text
Do not provide domain/risk/fractal_depth unless the user explicitly gives them.
Let AOCS infer them from the problem.
```

## 2026-06-15 - Correction: Arithmetic Shortcut Must Still Use LLM

### User correction

The user correctly objected to the previous deterministic arithmetic shortcut.

The user's core AOCS principle is:

```text
Code enforces the workflow.
LLMs perform the reasoning and deliver the answer.
```

Therefore, code should not directly answer `2+2` by computing `4`, even though code can technically do that. AOCS is meant to test and enforce a model-driven reasoning chain, not silently replace the model with hidden application logic.

### Corrected design

Code may do routing and guardrail decisions, such as:

```text
This looks like a simple directly-answerable problem.
Do not send it through the expensive deep Type 2 pipeline.
Send it to the direct-answer LLM role.
```

But the final answer must come from an LLM role.

### Corrected flow for `what is 2+2?`

Current flow:

```text
CLI command
-> AOCSRuntime
-> AOCSOrchestrator.analyze()
-> _maybe_direct_low_risk()
-> _looks_like_simple_arithmetic()
-> router.call(role="direct-answer")
-> LLM returns answer
-> AnalysisResult returned
```

What code decides:

```text
route_taken: direct-answer
problem_type: type1
skip deep Type 2 pipeline
```

What the LLM decides:

```text
specialist_proposal: the actual answer text
```

### Updated expected result

For the default beginner command:

```powershell
python -m aocs_mcp.cli run "what is 2+2?"
```

Expected behavior is now:

```text
route_taken: direct-answer
total_llm_calls: 1
specialist_proposal: answer produced by the direct-answer LLM role
```

### Why this still fixes the JSON error

The old JSON error happened because a trivial question entered a structured deep phase that expected JSON. The corrected shortcut still avoids that deep structured phase, but it does not compute the answer in code. It uses one plain direct-answer LLM call.

### Tests updated

`tests/test_orchestrator_direct.py` now asserts:

```text
router.call_log == [{"role": "direct-answer"}]
total_llm_calls == 1
```

This prevents future regressions where code secretly answers instead of calling the LLM role.

## 2026-06-15 - Check User Transcript And Promote Shadow Reroute

### User request

The user attached a terminal transcript and asked to check it.

### What the transcript showed

The `doctor` command now worked:

```text
[OK] opencode binary: 1.16.0
[OK] opencode mcp: aocs-omega connected
```

The `2+2` command now followed the corrected model-driven direct route:

```text
problem_type: type1
route_taken: direct-answer
total_llm_calls: 1
specialist_proposal: 4.
verdict: accept
confidence: 95.0
```

Conclusion:

The simple direct-answer route is now correct: code routes, LLM answers.

### Typo observed

The user accidentally typed:

```powershell
ython -m aocs_mcp.cli run "how do we make AGI ?"
```

PowerShell correctly failed because `ython` is not a command. The corrected command is:

```powershell
python -m aocs_mcp.cli run "how do we make AGI"
```

### AGI run result

The AGI run completed:

```text
route_taken: type2
problem_type: type2
total_llm_calls: 11
verdict: flag_for_review
confidence: 88.0
```

The shadow orchestrator independently classified the problem as:

```text
shadow problem_type: type3
shadow risk_level: critical
safe_path: Use shadow: type3 (risk critical)
```

### Gap found

AOCS recorded the shadow warning, but it did not promote that warning strongly enough into final recommendations.

This matters because a broad question like `how do we make AGI` can be safety-critical and discovery-oriented. If the shadow route says Type 3 critical, the final output must make that conservative route obvious to the user.

### Fix

The orchestrator now promotes a conservative shadow reroute into recommendations.

If:

```text
shadow.divergence_detected == true
shadow.safe_path starts with "Use shadow"
```

then recommendations include:

```text
Shadow orchestrator recommends safer reroute: Use shadow: type3 (risk critical). Do not act on the current route without review.
```

If the main route verdict was `accept`, a shadow reroute also downgrades it to `flag_for_review`.

### Tests added

`tests/test_orchestrator_direct.py` now checks that a Type 3 critical shadow reroute is promoted into recommendations.

### Tests run

```bash
python tests/test_orchestrator_direct.py
python tests/test_runtime.py
python tests/test_router.py
```

All passed.
