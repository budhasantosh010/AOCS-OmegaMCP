"""Command-line entrypoint for running AOCS without a coding-agent host."""

import argparse
import asyncio
import json

from aocs_mcp.doctor import checks_to_json, checks_to_dict, format_checks, run_doctor
from aocs_mcp.runtime import AOCSRunRequest, AOCSRuntime


async def _run(args: argparse.Namespace) -> int:
    runtime = AOCSRuntime(output_root=args.output_dir)
    request = AOCSRunRequest(
        problem=" ".join(args.problem),
        domain=args.domain,
        risk=args.risk,
        fractal_depth=args.fractal_depth,
        context=args.context,
        max_sub_agents=args.max_sub_agents,
        persist=not args.no_store,
    )
    result = await runtime.run(request)
    print(json.dumps(result.model_dump(), indent=2, ensure_ascii=False))
    return 1 if result.error else 0


async def _doctor(args: argparse.Namespace) -> int:
    checks = run_doctor(include_opencode=not args.no_opencode)
    if args.json:
        print(checks_to_json(checks))
    else:
        print(format_checks(checks))
    return 1 if checks_to_dict(checks)["failures"] else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aocs")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="Run the full deterministic AOCS pipeline")
    run.add_argument("problem", nargs="+", help="Problem or question to analyze")
    run.add_argument("--domain", default=None, help="Optional domain hint. Omit to let AOCS infer the domain.")
    run.add_argument("--risk", default=None, choices=["low", "medium", "high", "critical"], help="Optional risk hint. Omit to let AOCS infer risk.")
    run.add_argument("--fractal-depth", type=int, default=None, help="Optional recursion depth hint. Omit to let AOCS classify depth.")
    run.add_argument("--context", default=None)
    run.add_argument("--max-sub-agents", type=int, default=16)
    run.add_argument("--output-dir", default=None, help="Where to write .aocs run artifacts")
    run.add_argument("--no-store", action="store_true", help="Run without writing .aocs artifacts")
    run.set_defaults(func=_run)

    doctor = sub.add_parser("doctor", help="Check local AOCS, provider, and OpenCode MCP setup")
    doctor.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    doctor.add_argument("--no-opencode", action="store_true", help="Skip OpenCode binary and MCP checks")
    doctor.set_defaults(func=_doctor)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    raise SystemExit(asyncio.run(args.func(args)))


if __name__ == "__main__":
    main()
