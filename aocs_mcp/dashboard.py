"""Local AOCS dashboard server.

This is an AOCS-owned viewer for persisted runs. It does not depend on
OpenCode, Claude, Codex, Cursor, or any other coding-agent UI.
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from aocs_mcp.config import Config


def default_run_dir(config_dir: str | None = None) -> Path:
    """Resolve the run directory the same way the runtime does."""
    cfg = Config(config_dir=config_dir)
    runtime_cfg = cfg.get("runtime", {}) or {}
    return Path(
        os.environ.get("AOCS_RUN_DIR")
        or runtime_cfg.get("run_dir")
        or Path.cwd() / ".aocs" / "runs"
    )


def read_json(path: Path, fallback):
    """Read JSON with a fallback for incomplete or older run artifacts."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback


def list_runs(run_dir: Path) -> list[dict]:
    """Return persisted run summaries newest first."""
    if not run_dir.exists():
        return []

    runs: list[dict] = []
    for child in run_dir.iterdir():
        if not child.is_dir():
            continue
        status = read_json(child / "status.json", {})
        result = read_json(child / "result.json", {})
        request = read_json(child / "request.json", {})
        problem = result.get("problem") or request.get("problem") or ""
        runs.append(
            {
                "run_id": child.name,
                "status": status.get("status", "unknown"),
                "started_at": status.get("started_at"),
                "ended_at": status.get("ended_at"),
                "problem": problem,
                "verdict": result.get("verdict"),
                "confidence": result.get("confidence"),
                "route_taken": result.get("route_taken"),
                "problem_type": result.get("problem_type"),
                "total_llm_calls": result.get("total_llm_calls"),
                "updated_ts": child.stat().st_mtime,
            }
        )

    return sorted(runs, key=lambda item: item.get("updated_ts") or 0, reverse=True)


def load_run(run_dir: Path, run_id: str) -> dict:
    """Load one run and derive a readable agent timeline."""
    if "/" in run_id or "\\" in run_id or run_id in ("", ".", ".."):
        raise FileNotFoundError(run_id)

    path = run_dir / run_id
    if not path.is_dir():
        raise FileNotFoundError(run_id)

    result = read_json(path / "result.json", {})
    trace = read_json(path / "trace.json", [])
    payload = {
        "run_id": run_id,
        "request": read_json(path / "request.json", {}),
        "status": read_json(path / "status.json", {}),
        "result": result,
        "trace": trace if isinstance(trace, list) else [],
        "summary": (path / "summary.md").read_text(encoding="utf-8")
        if (path / "summary.md").exists()
        else "",
    }
    payload["agent_steps"] = build_agent_steps(result, payload["trace"])
    return payload


def build_agent_steps(result: dict, trace: list[dict]) -> list[dict]:
    """Convert raw result/trace files into readable AOCS agent steps."""
    output_by_role = _outputs_by_role(result)
    steps: list[dict] = []

    for entry in trace:
        role = entry.get("role", "unknown")
        step = {
            "call": entry.get("call"),
            "role": role,
            "title": _role_title(role),
            "status": entry.get("status", "unknown"),
            "mode": entry.get("mode") or entry.get("configured_mode"),
            "provider": entry.get("provider"),
            "model": entry.get("model"),
            "duration_ms": entry.get("duration_ms"),
            "response_chars": entry.get("response_chars"),
            "answer": output_by_role.get(role) or entry.get("response_preview") or "",
            "errors": entry.get("errors") or ([entry["error"]] if entry.get("error") else []),
        }
        steps.append(step)

    for role, answer in output_by_role.items():
        if not any(step["role"] == role for step in steps):
            steps.append(
                {
                    "call": None,
                    "role": role,
                    "title": _role_title(role),
                    "status": "derived",
                    "mode": "result",
                    "provider": None,
                    "model": None,
                    "duration_ms": None,
                    "response_chars": len(answer),
                    "answer": answer,
                    "errors": [],
                }
            )

    return steps


def _outputs_by_role(result: dict) -> dict[str, str]:
    outputs: dict[str, str] = {}

    if result.get("root_problem"):
        outputs["root-problem"] = result["root_problem"]
    if result.get("specialist_proposal"):
        outputs["specialist"] = result["specialist_proposal"]
        outputs["direct-answer"] = result["specialist_proposal"]
    if result.get("red_team_critique"):
        outputs["red-team"] = result["red_team_critique"]
    if result.get("contrarian_analysis"):
        outputs["contrarian"] = result["contrarian_analysis"]
    if result.get("deception_flags"):
        outputs["deception-detector"] = "\n".join(f"- {item}" for item in result["deception_flags"])

    judge = result.get("judge_verdict") or {}
    if judge:
        outputs["judge"] = "\n".join(
            part
            for part in [
                f"Decision: {judge.get('decision')}",
                f"Confidence: {judge.get('confidence')}",
                judge.get("reasoning"),
            ]
            if part
        )

    if result.get("interpretations"):
        outputs["multi-framer"] = "\n".join(
            f"- {item.get('label', 'Interpretation')}: {item.get('root_cause', '')}"
            for item in result["interpretations"]
        )

    gates = result.get("quality_gates") or []
    if gates:
        outputs["quality-gates"] = "\n".join(
            f"- Gate {gate.get('gate_number')}: {gate.get('name')} -> "
            f"{'passed' if gate.get('passed') else 'failed'}; {gate.get('details', '')}"
            for gate in gates
        )

    observer = result.get("observer_check") or {}
    if observer:
        outputs["observer"] = observer.get("notes", "")

    shadow = result.get("shadow_check") or {}
    if shadow:
        outputs["shadow-orchestrator"] = "\n".join(
            part
            for part in [
                f"Divergence: {shadow.get('divergence_detected')}",
                shadow.get("safe_path"),
            ]
            if part
        )

    type3 = result.get("type3_findings") or {}
    if type3:
        if type3.get("lens_observations"):
            outputs["type3-lens"] = "\n".join(f"- {item}" for item in type3["lens_observations"])
        if type3.get("first_principles"):
            outputs["type3-first-principles"] = type3["first_principles"]
        if type3.get("hypotheses"):
            outputs["type3-hypothesis"] = "\n".join(f"- {item}" for item in type3["hypotheses"])

    audit = result.get("memory_audit") or {}
    if audit:
        outputs["memory-audit"] = json.dumps(audit, indent=2, ensure_ascii=False)

    structured_outputs = {
        "deterministic-verifier": result.get("verification"),
        "formal-prover": result.get("prover_result"),
        "triple-modular-redundancy": result.get("tmr_result"),
        "blindspot-hunter": result.get("blindspot_check"),
        "fractal-verification": result.get("fractal_result"),
        "kill-switch": result.get("kill_switch"),
        "universal-goal-protocol": result.get("goal_achievement"),
        "breakthrough-protocols": result.get("breakthroughs"),
        "break-framework": result.get("break_framework"),
        "volume-swarm": result.get("swarm_result"),
        "paradigm-reframe": result.get("paradigm_reframe"),
        "learning-flywheel": result.get("learning_entries"),
    }
    for role, value in structured_outputs.items():
        if value:
            outputs[role] = json.dumps(value, indent=2, ensure_ascii=False)

    if type3:
        type3_roles = {
            "idea-mutator": type3.get("mutations"),
            "ruthless-pruner": {
                "survivors": type3.get("survivors"),
                "rejected_ideas": type3.get("rejected_ideas"),
                "weirdness_reserve": type3.get("weirdness_reserve"),
            },
            "serendipity-injector": {
                "seeds": type3.get("serendipity_seeds"),
                "connections": type3.get("serendipity_connections"),
            },
            "thought-simulator": type3.get("simulations"),
            "paradigm-detector": {
                "alert": type3.get("paradigm_alert"),
                "density": type3.get("anomaly_density"),
                "reason": type3.get("paradigm_reason"),
            },
            "quest-tracker": type3.get("quests"),
        }
        for role, value in type3_roles.items():
            if value:
                outputs[role] = json.dumps(
                    value,
                    indent=2,
                    ensure_ascii=False,
                )

    return {key: value for key, value in outputs.items() if value}


def _role_title(role: str) -> str:
    return {
        "direct-answer": "Direct Answer",
        "multi-framer": "Multi-Framer",
        "root-problem": "Root Problem Extractor",
        "deep-test": "Deep Test",
        "specialist": "Specialist",
        "red-team": "Red Team",
        "contrarian": "Contrarian",
        "deception-detector": "Deception Detector",
        "judge": "Judge",
        "observer": "Observer",
        "shadow-orchestrator": "Shadow Orchestrator",
        "type3-lens": "Type 3 Lens Agent",
        "type3-first-principles": "Type 3 First Principles",
        "type3-hypothesis": "Type 3 Hypothesis Generator",
        "idea-mutator": "Idea Mutator",
        "ruthless-pruner": "Ruthless Pruner",
        "serendipity-injector": "Serendipity Injector",
        "thought-simulator": "Thought Experiments and Simulations",
        "paradigm-detector": "Paradigm Detector",
        "quest-tracker": "Quest Tracker",
        "deterministic-verifier": "Deterministic Verifier",
        "formal-prover": "Formal Prover",
        "triple-modular-redundancy": "Triple Modular Redundancy",
        "blindspot-hunter": "Blindspot Hunter",
        "fractal-verification": "Fractal Verification",
        "kill-switch": "Kill Switch",
        "universal-goal-protocol": "Universal Goal Protocol",
        "breakthrough-protocols": "Breakthrough Protocols",
        "break-framework": "Break-Framework",
        "volume-swarm": "Volume Swarm",
        "paradigm-reframe": "Paradigm Reframe",
        "learning-flywheel": "Learning Flywheel",
        "quality-gates": "Quality Gates",
        "memory-audit": "Memory Audit",
    }.get(role, role.replace("-", " ").title())


def serve_dashboard(host: str, port: int, run_dir: Path) -> None:
    """Start the local HTTP dashboard."""
    run_dir = run_dir.resolve()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 - http.server API
            parsed = urlparse(self.path)
            try:
                if parsed.path in ("", "/"):
                    self._send_html(DASHBOARD_HTML)
                elif parsed.path == "/api/runs":
                    self._send_json({"run_dir": str(run_dir), "runs": list_runs(run_dir)})
                elif parsed.path == "/api/run":
                    params = parse_qs(parsed.query)
                    run_id = params.get("id", [""])[0]
                    self._send_json(load_run(run_dir, run_id))
                elif parsed.path == "/favicon.ico":
                    self.send_response(HTTPStatus.NO_CONTENT)
                    self.end_headers()
                else:
                    self.send_error(HTTPStatus.NOT_FOUND)
            except FileNotFoundError:
                self.send_error(HTTPStatus.NOT_FOUND, "Run not found")
            except Exception as exc:
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))

        def log_message(self, format: str, *args) -> None:  # noqa: A002
            return

        def _send_json(self, payload) -> None:
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _send_html(self, body: str) -> None:
            data = body.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", mimetypes.types_map.get(".html", "text/html"))
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    server = ThreadingHTTPServer((host, port), Handler)
    actual_host, actual_port = server.server_address[:2]
    print(f"AOCS dashboard: http://{actual_host}:{actual_port}/")
    print(f"Run directory: {run_dir}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


DASHBOARD_HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AOCS Dashboard</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f7f8fa;
      --panel: #ffffff;
      --ink: #172033;
      --muted: #657083;
      --line: #d8dde6;
      --accent: #2266cc;
      --ok: #0f7b44;
      --warn: #9a5b00;
      --bad: #a32020;
      --shadow: 0 1px 4px rgba(18, 28, 45, 0.08);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: var(--bg);
      color: var(--ink);
      letter-spacing: 0;
    }
    header {
      height: 56px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 20px;
      border-bottom: 1px solid var(--line);
      background: var(--panel);
    }
    h1 { font-size: 18px; margin: 0; font-weight: 700; }
    button {
      border: 1px solid var(--line);
      background: #fff;
      color: var(--ink);
      border-radius: 6px;
      padding: 8px 10px;
      cursor: pointer;
      font: inherit;
    }
    button:hover { border-color: var(--accent); }
    main {
      display: grid;
      grid-template-columns: 360px 1fr;
      min-height: calc(100vh - 56px);
    }
    aside {
      border-right: 1px solid var(--line);
      background: #fff;
      overflow: auto;
    }
    .runs-head {
      padding: 14px 16px;
      border-bottom: 1px solid var(--line);
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
    }
    .run-dir { color: var(--muted); font-size: 12px; overflow-wrap: anywhere; }
    .run-list { display: grid; }
    .run-item {
      text-align: left;
      border: 0;
      border-bottom: 1px solid var(--line);
      border-radius: 0;
      padding: 12px 16px;
      background: #fff;
    }
    .run-item.active { background: #edf4ff; border-left: 4px solid var(--accent); padding-left: 12px; }
    .problem {
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
      font-weight: 650;
      line-height: 1.3;
    }
    .meta { margin-top: 6px; color: var(--muted); font-size: 12px; }
    section { padding: 20px; overflow: auto; }
    .empty {
      border: 1px dashed var(--line);
      background: #fff;
      border-radius: 8px;
      padding: 24px;
      color: var(--muted);
    }
    .summary {
      display: grid;
      grid-template-columns: repeat(5, minmax(120px, 1fr));
      gap: 10px;
      margin-bottom: 16px;
    }
    .metric {
      background: #fff;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      box-shadow: var(--shadow);
    }
    .metric span { color: var(--muted); display: block; font-size: 12px; }
    .metric strong { display: block; margin-top: 4px; font-size: 18px; overflow-wrap: anywhere; }
    .block {
      background: #fff;
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: var(--shadow);
      margin-bottom: 14px;
      overflow: hidden;
    }
    .block h2 {
      margin: 0;
      padding: 12px 14px;
      font-size: 14px;
      border-bottom: 1px solid var(--line);
      background: #fbfcfe;
    }
    .content { padding: 14px; }
    .timeline { display: grid; gap: 10px; }
    .step {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      background: #fff;
    }
    .step-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 8px;
    }
    .step-title { font-weight: 700; }
    .pill {
      display: inline-flex;
      align-items: center;
      border-radius: 999px;
      border: 1px solid var(--line);
      padding: 2px 8px;
      font-size: 12px;
      color: var(--muted);
      white-space: nowrap;
    }
    .ok { color: var(--ok); border-color: #b7dfc8; }
    .error { color: var(--bad); border-color: #efb7b7; }
    .derived { color: var(--warn); border-color: #e6cc98; }
    pre {
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      margin: 0;
      color: #263145;
      font-family: ui-monospace, "Cascadia Mono", Consolas, monospace;
      font-size: 13px;
      line-height: 1.45;
    }
    .details {
      color: var(--muted);
      font-size: 12px;
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 8px;
    }
    @media (max-width: 900px) {
      main { grid-template-columns: 1fr; }
      aside { max-height: 42vh; border-right: 0; border-bottom: 1px solid var(--line); }
      .summary { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    }
  </style>
</head>
<body>
  <header>
    <h1>AOCS Dashboard</h1>
    <button id="refresh">Refresh</button>
  </header>
  <main>
    <aside>
      <div class="runs-head">
        <div>
          <strong>Runs</strong>
          <div class="run-dir" id="run-dir"></div>
        </div>
      </div>
      <div class="run-list" id="runs"></div>
    </aside>
    <section id="detail">
      <div class="empty">No run selected.</div>
    </section>
  </main>
  <script>
    let currentRun = null;

    function text(value) {
      if (value === null || value === undefined || value === "") return "none";
      return String(value);
    }

    function esc(value) {
      return text(value).replace(/[&<>"']/g, ch => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
      }[ch]));
    }

    async function loadRuns() {
      const res = await fetch("/api/runs");
      const data = await res.json();
      document.getElementById("run-dir").textContent = data.run_dir;
      const list = document.getElementById("runs");
      list.innerHTML = "";
      if (!data.runs.length) {
        list.innerHTML = '<div class="empty">No persisted AOCS runs found.</div>';
        document.getElementById("detail").innerHTML = '<div class="empty">Run AOCS once, then refresh.</div>';
        return;
      }
      data.runs.forEach((run, index) => {
        const button = document.createElement("button");
        button.className = "run-item" + (run.run_id === currentRun ? " active" : "");
        button.innerHTML = `
          <div class="problem">${esc(run.problem || run.run_id)}</div>
          <div class="meta">${esc(run.verdict)} | ${esc(run.route_taken)} | ${esc(run.total_llm_calls)} calls</div>
          <div class="meta">${esc(run.run_id)}</div>
        `;
        button.onclick = () => loadRun(run.run_id);
        list.appendChild(button);
        if (!currentRun && index === 0) loadRun(run.run_id);
      });
    }

    async function loadRun(runId) {
      currentRun = runId;
      const res = await fetch("/api/run?id=" + encodeURIComponent(runId));
      const data = await res.json();
      renderRun(data);
      await loadRuns();
    }

    function renderRun(data) {
      const r = data.result || {};
      const steps = data.agent_steps || [];
      const detail = document.getElementById("detail");
      detail.innerHTML = `
        <div class="summary">
          ${metric("Verdict", r.verdict)}
          ${metric("Confidence", r.confidence)}
          ${metric("Route", r.route_taken)}
          ${metric("Type", r.problem_type)}
          ${metric("LLM Calls", r.total_llm_calls)}
        </div>
        <div class="block">
          <h2>Problem</h2>
          <div class="content"><pre>${esc(r.problem)}</pre></div>
        </div>
        <div class="block">
          <h2>Final Recommendation</h2>
          <div class="content"><pre>${esc((r.recommendations || []).join("\\n"))}</pre></div>
        </div>
        <div class="block">
          <h2>Agent Timeline</h2>
          <div class="content timeline">${steps.map(renderStep).join("") || '<div class="empty">No agent steps recorded.</div>'}</div>
        </div>
        <div class="block">
          <h2>Raw Summary</h2>
          <div class="content"><pre>${esc(data.summary)}</pre></div>
        </div>
      `;
    }

    function metric(label, value) {
      return `<div class="metric"><span>${esc(label)}</span><strong>${esc(value)}</strong></div>`;
    }

    function renderStep(step) {
      const statusClass = step.status === "ok" ? "ok" : step.status === "error" ? "error" : step.status === "derived" ? "derived" : "";
      const detail = [
        step.call ? `call ${step.call}` : null,
        step.mode,
        step.provider,
        step.model,
        step.duration_ms ? `${step.duration_ms} ms` : null,
        step.response_chars ? `${step.response_chars} chars` : null,
      ].filter(Boolean).map(esc).join(" | ");
      const errors = (step.errors || []).length ? "\\nErrors:\\n" + step.errors.join("\\n") : "";
      return `
        <article class="step">
          <div class="step-head">
            <div class="step-title">${esc(step.title)}</div>
            <span class="pill ${statusClass}">${esc(step.status)}</span>
          </div>
          <div class="details">${detail}</div>
          <pre>${esc((step.answer || "") + errors)}</pre>
        </article>
      `;
    }

    document.getElementById("refresh").onclick = loadRuns;
    loadRuns().catch(err => {
      document.getElementById("detail").innerHTML = `<div class="empty">${esc(err.message)}</div>`;
    });
  </script>
</body>
</html>
"""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="aocs-dashboard")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--run-dir", default=None)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    run_dir = Path(args.run_dir) if args.run_dir else default_run_dir()
    serve_dashboard(args.host, args.port, run_dir)


if __name__ == "__main__":
    main()
