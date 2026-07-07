from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from ldvh_specs import ROOT, build_runtime_event


INTEGRATION_SCOPE = "hook.completion_claim"


def _bool_text(value: bool) -> str:
    return "true" if value else "false"


def build_completion_claim(
    root: Path = ROOT,
    *,
    session_id: str = "",
    target_path: str = "",
    cwd: str | Path | None = None,
    config_root: str | Path | None = None,
    target_paths: list[str | Path] | None = None,
    task: str = "",
    operation: str = "complete",
    trigger_source: str = "hook.runtime",
    acknowledged_paths: list[str] | None = None,
    verification_evidence: list[str] | None = None,
) -> dict[str, Any]:
    result = build_runtime_event(
        root,
        event="completion_claim",
        trigger_source=trigger_source,
        session_id=session_id,
        target_path=target_path,
        task=task,
        operation=operation,
        cwd=cwd,
        config_root=config_root,
        target_paths=target_paths,
        acknowledged_paths=acknowledged_paths,
        verification_evidence=verification_evidence,
    )
    preflight = result["preflight"] or {}
    result["metadata"]["integration_scope"] = INTEGRATION_SCOPE
    result["summary"]["environment_integrated"] = False
    result["summary"]["integration_scope"] = INTEGRATION_SCOPE
    result["summary"]["verification_evidence"] = len(result["receipt"]["verification_evidence"])
    result["summary"]["acknowledged_paths"] = len(result["receipt"]["acknowledged_paths"])
    result["summary"]["preflight_status"] = preflight.get("summary", {}).get("status", "")
    result["summary"]["completion_diagnostics"] = len(result["diagnostics"])
    result["summary"]["completion_blockers"] = result["summary"]["blocking"]
    return result


def _print_text(result: dict[str, Any]) -> None:
    summary = result["summary"]
    receipt = result["receipt"]

    print("LDVH v3 ldvh.completion_claim check")
    print(f"- status: {summary['status']}")
    print(f"- event: {summary['event']}")
    print(f"- internal_event: {summary['internal_event']}")
    print(f"- operation: {result['input']['operation']}")
    print(f"- target_path: {receipt['target_path']}")
    print(f"- receipt_id: {receipt['receipt_id']}")
    print(f"- receipt_storage: {receipt['storage']}")
    print(f"- verification_evidence: {summary['verification_evidence']}")
    print(f"- acknowledged_paths: {summary['acknowledged_paths']}")
    print(f"- preflight_status: {summary['preflight_status']}")
    print(f"- completion_diagnostics: {summary['completion_diagnostics']}")
    print(f"- completion_blockers: {summary['completion_blockers']}")
    print(f"- environment_integrated: {_bool_text(summary['environment_integrated'])}")
    print(f"- integration_scope: {summary['integration_scope']}")

    if receipt["verification_evidence"]:
        print("\nVerification evidence:")
        for item in receipt["verification_evidence"]:
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
    parser = argparse.ArgumentParser(description="Run the LDVH v3 completion_claim check.")
    parser.add_argument("--root", default=ROOT.as_posix(), help="repository root")
    parser.add_argument("--session-id", default="", help="current session identifier")
    parser.add_argument("--cwd", default="", help="current working directory for target resolution")
    parser.add_argument("--config-root", default="", help="root containing LDVH-GOVERNED-PROJECTS.yaml")
    parser.add_argument("--target-path", default="", help="target path for the completion claim")
    parser.add_argument("--target-paths", action="append", default=[], help="explicit target path; may be repeated")
    parser.add_argument("--task", default="", help="current task summary")
    parser.add_argument("--operation", default="complete", help="completion operation kind")
    parser.add_argument("--trigger-source", default="hook.runtime", help="trigger source label")
    parser.add_argument(
        "--acknowledged-path",
        action="append",
        default=[],
        help="acknowledged read_plan path; may be repeated or comma-separated",
    )
    parser.add_argument(
        "--verification-evidence",
        action="append",
        default=[],
        help="verification evidence, unverified scope, or residual risk statement; may be repeated or comma-separated",
    )
    parser.add_argument("--format", choices=["text", "json"], default="text")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = build_completion_claim(
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
        verification_evidence=args.verification_evidence,
    )
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        _print_text(result)
    return 1 if result["summary"]["blocking"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
