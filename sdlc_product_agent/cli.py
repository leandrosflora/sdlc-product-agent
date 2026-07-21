"""Command-line entrypoint: `python -m sdlc_product_agent <command> ...`."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from .agent import ACTIONS, ROLE, UnknownActionError, execute
from .authorization import PolicyUnavailableError, check_authorization


def _load_input(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=f"python -m sdlc_product_agent", description=f"{ROLE} agent CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    authorize_p = sub.add_parser("authorize", help="Evaluate OPA authorization for an input document")
    authorize_p.add_argument("--input", "-i", required=True, help="Path to input JSON (identity/action/resource/change)")

    execute_p = sub.add_parser("execute", help="Authorize then run a role action")
    execute_p.add_argument("action", choices=sorted(ACTIONS), help="Action to execute")
    execute_p.add_argument("--input", "-i", required=True, help="Path to input JSON (identity/resource/change)")

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        input_doc = _load_input(args.input)
        if args.command == "authorize":
            result = check_authorization(input_doc)
            print(json.dumps({"allowed": result.allowed, "action": result.action}, indent=2))
        else:
            result = execute(args.action, input_doc)
            print(json.dumps(result.__dict__, indent=2))
    except (PolicyUnavailableError, UnknownActionError, FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
