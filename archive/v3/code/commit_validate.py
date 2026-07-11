from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

from ldvh_specs import ROOT, build_commit_gate


def _staged_paths(repo: Path) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _print_text(result: dict[str, Any]) -> None:
    summary = result["summary"]
    print("LDVH v3 commit message validation")
    print(f"status: {summary['status']}")
    print(f"message_type: {summary['message_type']}")
    print(f"message_scope: {summary['message_scope']}")
    print(f"changed_paths: {summary['changed_paths']}")
    print(f"body_required: {summary['body_required']}")
    print(f"read_plan_required: {summary['read_plan_required']}")
    print(f"read_plan_consumed: {summary['read_plan_consumed']}")
    print(f"environment_integrated: {summary['environment_integrated']}")
    if result["diagnostics"]:
        print("diagnostics:")
        for diagnostic in result["diagnostics"]:
            print(f"- {diagnostic['path']} [{diagnostic['level']}/{diagnostic['code']}] {diagnostic['message']}")
    else:
        print("diagnostics: none")
    print("authorization: none")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate an LDVH v3 commit message.")
    parser.add_argument("--check-message-file", "--message-file", dest="message_file", required=True)
    parser.add_argument("--repo", default=ROOT.as_posix(), help="target repository root used for staged paths")
    parser.add_argument("--ldvh-root", default=ROOT.as_posix(), help="LDVH root used for specs and validator contracts")
    parser.add_argument(
        "--changed-path",
        action="append",
        default=[],
        help="changed path; may be repeated or comma-separated. Defaults to staged paths.",
    )
    parser.add_argument(
        "--acknowledged-path",
        action="append",
        default=[],
        help="acknowledged read_plan path; may be repeated or comma-separated",
    )
    parser.add_argument("--require-read-plan", action="store_true", help="require external read_plan evidence")
    parser.add_argument("--no-require-read-plan", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument(
        "--hook-integrated",
        action="store_true",
        help="mark this invocation as the active git.commit-msg hook integration",
    )
    parser.add_argument("--format", choices=["text", "json"], default="text")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo = Path(args.repo).resolve()
    ldvh_root = Path(args.ldvh_root).resolve()
    message = Path(args.message_file).read_text(encoding="utf-8")
    changed_paths = args.changed_path or _staged_paths(repo)
    result = build_commit_gate(
        ldvh_root,
        message=message,
        changed_paths=changed_paths,
        acknowledged_paths=args.acknowledged_path,
        require_read_plan=args.require_read_plan and not args.no_require_read_plan,
        hook_integrated=args.hook_integrated,
    )
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        _print_text(result)
    return 1 if result["summary"]["blocking"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
