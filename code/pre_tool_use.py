from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from ldvh_specs import ROOT, build_runtime_event
from runtime_receipt_cache import read_ack_receipt


INTEGRATION_SCOPE = "manual.pre_tool_use"


def _bool_text(value: bool) -> str:
    return "true" if value else "false"


def build_pre_tool_use(
    root: Path = ROOT,
    *,
    session_id: str = "",
    target_path: str = "",
    cwd: str | Path | None = None,
    config_root: str | Path | None = None,
    target_paths: list[str | Path] | None = None,
    task: str = "",
    operation: str = "write",
    trigger_source: str = "manual",
    acknowledged_paths: list[str] | None = None,
    runtime_cache: bool = True,
) -> dict[str, Any]:
    cache_status = {"status": "skipped", "path": "", "expires_at": "", "reason": "explicit acknowledged_paths supplied"}
    effective_acknowledged_paths = acknowledged_paths
    if runtime_cache and not acknowledged_paths:
        cache = read_ack_receipt(root, session_id=session_id)
        cache_status = {
            "status": cache.status,
            "path": cache.path,
            "expires_at": cache.expires_at,
            "reason": cache.reason,
        }
        if cache.acknowledged_paths:
            effective_acknowledged_paths = cache.acknowledged_paths
    elif not runtime_cache:
        cache_status = {"status": "disabled", "path": "", "expires_at": "", "reason": "runtime cache disabled for this call"}

    result = build_runtime_event(
        root,
        event="pre_tool_use",
        trigger_source=trigger_source,
        session_id=session_id,
        target_path=target_path,
        task=task,
        operation=operation,
        cwd=cwd,
        config_root=config_root,
        target_paths=target_paths,
        acknowledged_paths=effective_acknowledged_paths,
    )
    preflight = result["preflight"] or {}
    result["metadata"]["integration_scope"] = INTEGRATION_SCOPE
    result["summary"]["environment_integrated"] = False
    result["summary"]["integration_scope"] = INTEGRATION_SCOPE
    result["summary"]["acknowledged_paths"] = len(result["receipt"]["acknowledged_paths"])
    result["summary"]["preflight_status"] = preflight.get("summary", {}).get("status", "")
    result["summary"]["required_read_plan"] = len(preflight.get("required_read_plan", []))
    result["runtime_cache"] = cache_status
    result["summary"]["runtime_cache"] = cache_status["status"]
    return result


def _print_text(result: dict[str, Any]) -> None:
    summary = result["summary"]
    receipt = result["receipt"]
    preflight = result["preflight"] or {}
    preflight_summary = preflight.get("summary", {})

    print("LDVH v3 pre_tool_use check")
    print(f"- status: {summary['status']}")
    print(f"- operation: {result['input']['operation']}")
    print(f"- target_path: {receipt['target_path']}")
    print(f"- target_type: {preflight_summary.get('target_type', '')}")
    print(f"- preflight_status: {summary['preflight_status']}")
    print(f"- receipt_id: {receipt['receipt_id']}")
    print(f"- receipt_storage: {receipt['storage']}")
    print(f"- acknowledged_paths: {summary['acknowledged_paths']}")
    print(f"- runtime_cache: {summary['runtime_cache']}")
    if result.get("runtime_cache", {}).get("path"):
        print(f"- runtime_cache_path: {result['runtime_cache']['path']}")
    print(f"- required_read_plan: {summary['required_read_plan']}")
    print(f"- environment_integrated: {_bool_text(summary['environment_integrated'])}")
    print(f"- integration_scope: {summary['integration_scope']}")

    required_read_plan = preflight.get("required_read_plan", [])
    if required_read_plan:
        print("\nRequired read plan:")
        for item in required_read_plan:
            print(f"- {item['priority']}: {item['path']} ({item['role']})")

    human_gate_risks = preflight.get("human_gate_risks", [])
    if human_gate_risks:
        print("\nHuman Gate risks:")
        for item in human_gate_risks:
            print(f"- {item['path']} [{item['code']}] {item['message']}")

    if result["diagnostics"]:
        print("\nDiagnostics:")
        for diagnostic in result["diagnostics"]:
            print(f"- {diagnostic['path']} [{diagnostic['level']}/{diagnostic['code']}] {diagnostic['message']}")
    else:
        print("\nDiagnostics: none")

    print("\nAuthorization: none")
    print(f"Boundary: {receipt['boundary']}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the LDVH v3 pre_tool_use check.")
    parser.add_argument("--root", default=ROOT.as_posix(), help="repository root")
    parser.add_argument("--session-id", default="", help="current session identifier")
    parser.add_argument("--cwd", default="", help="current working directory for target resolution")
    parser.add_argument("--config-root", default="", help="root containing LDVH-GOVERNED-PROJECTS.yaml")
    parser.add_argument("--target-path", default="", help="target path for the pending write/tool operation")
    parser.add_argument("--target-paths", action="append", default=[], help="explicit target path; may be repeated")
    parser.add_argument("--task", default="", help="current task summary")
    parser.add_argument("--operation", default="write", help="pending operation kind, such as write/edit/apply_patch")
    parser.add_argument("--trigger-source", default="manual", help="trigger source label")
    parser.add_argument(
        "--acknowledged-path",
        action="append",
        default=[],
        help="acknowledged read_plan path; may be repeated or comma-separated",
    )
    parser.add_argument("--no-runtime-cache", action="store_true", help="do not read the session runtime receipt cache")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = build_pre_tool_use(
        Path(args.root).resolve(),
        session_id=args.session_id,
        target_path=args.target_path,
        cwd=args.cwd or None,
        config_root=args.config_root or None,
        target_paths=args.target_paths,
        task=args.task,
        operation=args.operation,
        trigger_source=args.trigger_source,
        acknowledged_paths=args.acknowledged_path,
        runtime_cache=not args.no_runtime_cache,
    )
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        _print_text(result)
    return 1 if result["summary"]["blocking"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
