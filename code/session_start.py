from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from ldvh_specs import ROOT, build_runtime_event


INTEGRATION_SCOPE = "manual.session_start"


def _bool_text(value: bool) -> str:
    return "true" if value else "false"


def build_session_start(
    root: Path = ROOT,
    *,
    session_id: str = "",
    target_path: str = "",
    task: str = "",
    trigger_source: str = "manual",
) -> dict[str, Any]:
    result = build_runtime_event(
        root,
        event="session_start",
        trigger_source=trigger_source,
        session_id=session_id,
        target_path=target_path,
        task=task,
        operation="read",
    )
    result["metadata"]["integration_scope"] = INTEGRATION_SCOPE
    result["summary"]["environment_integrated"] = False
    result["summary"]["integration_scope"] = INTEGRATION_SCOPE
    result["summary"]["task_read_plan"] = len(result["action_guide"]["task_read_plan"]) if result["action_guide"] else 0
    return result


def _print_text(result: dict[str, Any]) -> None:
    summary = result["summary"]
    receipt = result["receipt"]
    action_guide = result["action_guide"] or {}

    print("LDVH v3 session_start read_plan")
    print(f"- status: {summary['status']}")
    print(f"- session_id: {receipt['session_id']}")
    print(f"- target_path: {receipt['target_path']}")
    print(f"- task_read_plan: {summary['task_read_plan']}")
    print(f"- receipt_id: {receipt['receipt_id']}")
    print(f"- receipt_storage: {receipt['storage']}")
    print(f"- environment_integrated: {_bool_text(summary['environment_integrated'])}")
    print(f"- integration_scope: {summary['integration_scope']}")

    read_plan = action_guide.get("task_read_plan", [])
    if read_plan:
        print("\nTask read plan:")
        for item in read_plan:
            path = item["path"] or item["label"]
            print(f"- {item['priority']}: {path} ({item['requirement_id']})")

    stop_conditions = action_guide.get("stop_conditions", [])
    if stop_conditions:
        print("\nStop conditions:")
        for item in stop_conditions:
            print(f"- {item['requirement_id']}: {item['condition']}")

    if result["diagnostics"]:
        print("\nDiagnostics:")
        for diagnostic in result["diagnostics"]:
            print(f"- {diagnostic['path']} [{diagnostic['level']}/{diagnostic['code']}] {diagnostic['message']}")
    else:
        print("\nDiagnostics: none")

    print("\nAuthorization: none")
    print(f"Boundary: {receipt['boundary']}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate the LDVH v3 session_start read_plan.")
    parser.add_argument("--root", default=ROOT.as_posix(), help="repository root")
    parser.add_argument("--session-id", default="", help="current session identifier")
    parser.add_argument("--target-path", default="", help="current target path, if known")
    parser.add_argument("--task", default="", help="current task summary")
    parser.add_argument("--trigger-source", default="manual", help="trigger source label")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = build_session_start(
        Path(args.root).resolve(),
        session_id=args.session_id,
        target_path=args.target_path,
        task=args.task,
        trigger_source=args.trigger_source,
    )
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        _print_text(result)
    return 1 if result["summary"]["blocking"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
