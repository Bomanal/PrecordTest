"""CLI: run an agent, serve the workbench, or execute evals.

Prefer ``python -m secureterm_uw …`` over the ``secureterm-uw`` console
script. The console script is easy to miss if the virtualenv bin directory
is not on PATH, and it is easy to confuse with Google ADK's ``adk`` CLI.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .case_model import Case
from .evals.runner import run_evals
from .runtime import run_agent
from .tools.mock_policycenter import SYNTHETIC_CASES, build_gateway


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m secureterm_uw",
        description="SecureTerm UW workbench. This is not the Google ADK `adk` CLI.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    run_p = sub.add_parser("run", help="Run BLK-01 or BLK-02 against a case JSON file")
    run_p.add_argument("--agent", required=True, choices=["BLK-01", "BLK-02"])
    run_p.add_argument("--case", help="Path to case JSON")
    run_p.add_argument("--synthetic", help="Synthetic case id, e.g. LUW-FAST-01")
    run_p.add_argument("--stage", choices=["s3", "s4", "s6"])

    sub.add_parser("eval", help="Run eval cases EC-01, EC-02 and deterministic checks")
    sub.add_parser("cases", help="List synthetic case ids")
    serve = sub.add_parser("serve", help="Start the workbench HTTP API (not `adk web`)")
    serve.add_argument("--host", default=None)
    serve.add_argument("--port", type=int, default=None)

    args = parser.parse_args(argv)

    if args.cmd == "cases":
        json.dump({"synthetic_cases": sorted(SYNTHETIC_CASES)}, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0

    if args.cmd == "run":
        if args.synthetic:
            if args.synthetic not in SYNTHETIC_CASES:
                known = ", ".join(sorted(SYNTHETIC_CASES))
                parser.error(f"unknown synthetic case {args.synthetic!r}. Known: {known}")
            payload = SYNTHETIC_CASES[args.synthetic]
        elif args.case:
            payload = json.loads(Path(args.case).read_text(encoding="utf-8"))
        else:
            parser.error("provide --case or --synthetic")
        output = run_agent(
            args.agent,
            Case.model_validate(payload),
            gateway=build_gateway(),
            stage=args.stage,
        )
        json.dump(output, sys.stdout, indent=2, default=str)
        sys.stdout.write("\n")
        return 0 if output["result"]["status"] != "error" else 1

    if args.cmd == "eval":
        report = run_evals()
        json.dump(report, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0 if report["passed"] else 1

    if args.cmd == "serve":
        import uvicorn

        from .config import get_settings

        settings = get_settings()
        host = args.host or settings.host
        port = args.port or settings.port
        sys.stderr.write(
            "\nSecureTerm UW workbench (FastAPI — not Google ADK)\n"
            f"  UI:     http://{host}:{port}/\n"
            f"  Health: http://{host}:{port}/health\n"
            "  Stop with Ctrl+C\n\n"
        )
        sys.stderr.flush()
        uvicorn.run(
            "secureterm_uw.api:APP",
            host=host,
            port=port,
            reload=False,
        )
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
