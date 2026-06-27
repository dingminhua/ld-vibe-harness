from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

from action_guide import ActionGuideError, compile_action_guide, load_formatted_source  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compile a formatted LDVH source into an action guide.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    action_guide = subparsers.add_parser("action-guide")
    action_guide.add_argument("--source", required=True, help="Formatted source YAML file.")
    action_guide.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")

    args = parser.parse_args(argv)
    if args.command != "action-guide":
        parser.error(f"unknown command: {args.command}")

    try:
        source = load_formatted_source(args.source)
        guide = compile_action_guide(source)
    except ActionGuideError as exc:
        print(f"action-guide: {exc}", file=sys.stderr)
        return 2

    indent = 2 if args.pretty else None
    print(json.dumps(guide, ensure_ascii=False, indent=indent, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
