from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from ldvh_specs import ROOT, build_runtime_event
from runtime_receipt_cache import write_ack_receipt


INTEGRATION_SCOPE = "hook.acknowledge_read_plan"


def _bool_text(value: bool) -> str:
    return "true" if value else "false"


def build_acknowledge_read_plan(
    root: Path = ROOT,
    *,
    session_id: str = "",
    target_path: str = "",
    task: str = "",
    trigger_source: str = "hook.runtime",
    acknowledged_paths: list[str] | None = None,
    runtime_cache: bool = True,
) -> dict[str, Any]:
    result = build_runtime_event(
        root,
        event="acknowledge_read_plan",
        trigger_source=trigger_source,
        session_id=session_id,
        target_path=target_path,
        task=task,
        operation="read",
        acknowledged_paths=acknowledged_paths,
    )
    result["metadata"]["integration_scope"] = INTEGRATION_SCOPE
    result["summary"]["environment_integrated"] = False
    result["summary"]["integration_scope"] = INTEGRATION_SCOPE
    result["summary"]["acknowledged_paths"] = len(result["receipt"]["acknowledged_paths"])
    cache_status = {"status": "disabled", "path": "", "expires_at": "", "reason": "runtime cache disabled for this call"}
    if runtime_cache and not result["summary"]["blocking"]:
        cache = write_ack_receipt(
            root,
            session_id=session_id,
            acknowledged_paths=result["receipt"]["acknowledged_paths"],
            trigger_source=trigger_source,
        )
        cache_status = {
            "status": cache.status,
            "path": cache.path,
            "expires_at": cache.expires_at,
            "reason": cache.reason,
        }
    result["runtime_cache"] = cache_status
    result["summary"]["runtime_cache"] = cache_status["status"]
    return result


def _print_text(result: dict[str, Any]) -> None:
    summary = result["summary"]
    receipt = result["receipt"]

    print("LDVH v3 ldvh.acknowledge_read_plan receipt")
    print(f"- status: {summary['status']}")
    print(f"- event: {summary['event']}")
    print(f"- internal_event: {summary['internal_event']}")
    print(f"- session_id: {receipt['session_id']}")
    print(f"- target_path: {receipt['target_path']}")
    print(f"- receipt_id: {receipt['receipt_id']}")
    print(f"- receipt_storage: {receipt['storage']}")
    print(f"- acknowledged_paths: {summary['acknowledged_paths']}")
    print(f"- runtime_cache: {summary['runtime_cache']}")
    if result.get("runtime_cache", {}).get("path"):
        print(f"- runtime_cache_path: {result['runtime_cache']['path']}")
    if result.get("runtime_cache", {}).get("expires_at"):
        print(f"- runtime_cache_expires_at: {result['runtime_cache']['expires_at']}")
    print(f"- environment_integrated: {_bool_text(summary['environment_integrated'])}")
    print(f"- integration_scope: {summary['integration_scope']}")

    if receipt["acknowledged_paths"]:
        print("\nAcknowledged paths:")
        for item in receipt["acknowledged_paths"]:
            print(f"- {item}")

    if result["diagnostics"]:
        print("\nDiagnostics:")
        for diagnostic in result["diagnostics"]:
            print(f"- {diagnostic['path']} [{diagnostic['level']}/{diagnostic['code']}] {diagnostic['message']}")
    else:
        print("\nDiagnostics: none")

    print("\nAuthorization: none")
    print(f"Boundary: {receipt['boundary']}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Acknowledge the LDVH v3 session_start read_plan.")
    parser.add_argument("--root", default=ROOT.as_posix(), help="repository root")
    parser.add_argument("--session-id", default="", help="current session identifier")
    parser.add_argument("--target-path", default="", help="target path for the acknowledged read_plan")
    parser.add_argument("--task", default="", help="current task summary")
    parser.add_argument("--trigger-source", default="hook.runtime", help="trigger source label")
    parser.add_argument(
        "--acknowledged-path",
        action="append",
        default=[],
        help="acknowledged read_plan path; may be repeated or comma-separated",
    )
    parser.add_argument("--no-runtime-cache", action="store_true", help="do not write the session runtime receipt cache")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = build_acknowledge_read_plan(
        Path(args.root).resolve(),
        session_id=args.session_id,
        target_path=args.target_path,
        task=args.task,
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
