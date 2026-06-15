---
description: Run the full deterministic AOCS-Omega pipeline
---

Call the MCP tool `aocs_run_full` from the `aocs-omega` server with this exact problem:

```text
$ARGUMENTS
```

Do not provide `domain`, `risk`, or `fractal_depth` unless the user explicitly
gave those values. Let AOCS infer the domain, risk, route, and depth from the
problem itself.

Do not call phase-level or debug tools. Return the final AOCS report from the tool result.
