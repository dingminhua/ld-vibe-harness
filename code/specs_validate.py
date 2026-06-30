from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from ldvh_specs import ROOT, build_validation


def _diagnostics_by_level(result: dict[str, Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for diagnostic in result["diagnostics"]:
        level = diagnostic["level"]
        counts[level] = counts.get(level, 0) + 1
    return counts


def print_text(result: dict[str, Any], command: str) -> None:
    summary = result["summary"]
    print("LDVH v3 specs 校验完成")
    print(f"- command: {command}")
    print(f"- status: {summary['status']}")
    print(f"- specs: {summary['specs']}")
    print(f"- attachments: {summary['attachments']}")
    print(f"- consumption_timings: {summary['consumption_timings']}")
    print(f"- ai_behavior_requirements: {summary['ai_behavior_requirements']}")
    print(f"- takeover_matrix_rows: {summary['takeover_matrix_rows']}")
    print(f"- diagnostics: {summary['diagnostics']}")

    if result["diagnostics"]:
        print("\nDiagnostics:")
        for diagnostic in result["diagnostics"]:
            print(f"- {diagnostic['path']} [{diagnostic['level']}/{diagnostic['code']}] {diagnostic['message']}")
    else:
        print("\nDiagnostics: none")


def select_output(result: dict[str, Any], command: str) -> dict[str, Any]:
    if command == "specs":
        return {
            "metadata": result["metadata"],
            "summary": result["summary"],
            "specs": result["specs"],
            "attachments": result["attachments"],
            "diagnostics": result["diagnostics"],
        }
    if command == "timings":
        return {
            "metadata": result["metadata"],
            "summary": result["summary"],
            "consumption_timings": result["consumption_timings"],
            "diagnostics": result["diagnostics"],
        }
    if command == "ai-behavior":
        return {
            "metadata": result["metadata"],
            "summary": result["summary"],
            "ai_behavior_requirements": result["ai_behavior_requirements"],
            "takeover_matrix": result["takeover_matrix"],
            "diagnostics": result["diagnostics"],
        }
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate LDVH v3 Markdown specs.")
    parser.add_argument(
        "command",
        nargs="?",
        default="all",
        choices=["all", "specs", "timings", "ai-behavior"],
        help="validation surface to print",
    )
    parser.add_argument("--root", default=ROOT.as_posix(), help="repository root")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--fail-on-diagnostics", action="store_true", help="return non-zero when any diagnostic exists")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    result = build_validation(root)
    output = select_output(result, args.command)

    if args.format == "json":
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print_text(output, args.command)

    if args.fail_on_diagnostics and result["diagnostics"]:
        counts = _diagnostics_by_level(result)
        print(f"fail-on-diagnostics: {counts}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
