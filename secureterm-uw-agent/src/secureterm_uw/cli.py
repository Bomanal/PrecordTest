"""CLI: run an agent, serve the workbench, or execute evals."""

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
    parser = argparse.ArgumentParser(prog="secureterm-uw")
    sub = parser.add_subparsers(dest="cmd", required=True)

    run_p = sub.add_parser("run", help="Run BLK-01 or BLK-02 against a case JSON file")
    run_p.add_argument("--agent", required=True, choices=["BLK-01", "BLK-02"])
    run_p.add_argument("--case", help="Path to case JSON")
    run_p.add_argument("--synthetic", help="Synthetic case id, e.g. LUW-FAST-01")
    run_p.add_argument("--stage", choices=["s3", "s4", "s6"])

    sub.add_parser("eval", help="Run eval cases EC-01, EC-02 and deterministic checks")
    serve = sub.add_parser("serve", help="Start the workbench HTTP API")
    serve.add_argument("--host", default=None)
    serve.add_argument("--port", type=int, default=None)

    args = parser.parse_args(argv)

    if args.cmd == "run":
        if args.synthetic:
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
        uvicorn.run(
            "secureterm_uw.api:APP",
            host=args.host or settings.host,
            port=args.port or settings.port,
            reload=False,
        )
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
