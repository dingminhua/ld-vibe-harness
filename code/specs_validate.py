from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from ldvh_specs import ROOT, build_action_guide, build_preflight, build_runtime_event, build_validation


def _diagnostics_by_level(result: dict[str, Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for diagnostic in result["diagnostics"]:
        level = diagnostic["level"]
        counts[level] = counts.get(level, 0) + 1
    return counts


def print_text(result: dict[str, Any], command: str) -> None:
    if command == "runtime":
        summary = result["summary"]
        print("LDVH v3 runtime facade 处理完成")
        print(f"- status: {summary['status']}")
        print(f"- event: {summary['event']}")
        print(f"- trigger_source: {summary['trigger_source']}")
        print(f"- diagnostics: {summary['diagnostics']}")
        print(f"- blocking: {summary['blocking']}")
        print(f"- receipt_status: {summary['receipt_status']}")
        print(f"- has_action_guide: {summary['has_action_guide']}")
        print(f"- has_preflight: {summary['has_preflight']}")
        print("\nReceipt:")
        print(f"- id: {result['receipt']['receipt_id']}")
        print(f"- storage: {result['receipt']['storage']}")
        print(f"- boundary: {result['receipt']['boundary']}")
        if result["diagnostics"]:
            print("\nDiagnostics:")
            for diagnostic in result["diagnostics"]:
                print(f"- {diagnostic['path']} [{diagnostic['level']}/{diagnostic['code']}] {diagnostic['message']}")
        else:
            print("\nDiagnostics: none")
        print("\nEnvironment integrated: false")
        print("Authorization: none")
        return

    if command == "preflight":
        summary = result["summary"]
        print("LDVH v3 preflight 诊断完成")
        print(f"- status: {summary['status']}")
        print(f"- operation: {summary['operation']}")
        print(f"- target_type: {summary['target_type']}")
        print(f"- impact: {summary['impact']}")
        print(f"- diagnostics: {summary['diagnostics']}")
        print(f"- blocking: {summary['blocking']}")
        print(f"- human_gate_risks: {summary['human_gate_risks']}")
        print("\nRequired read plan:")
        for item in result["required_read_plan"]:
            print(f"- {item['priority']}: {item['path']} ({item['role']})")
        if result["diagnostics"]:
            print("\nDiagnostics:")
            for diagnostic in result["diagnostics"]:
                print(f"- {diagnostic['path']} [{diagnostic['level']}/{diagnostic['code']}] {diagnostic['message']}")
        else:
            print("\nDiagnostics: none")
        print("\nAuthorization: none")
        return

    if command == "action-guide":
        summary = result["summary"]
        print("LDVH v3 Action Guide 生成完成")
        print(f"- status: {summary['status']}")
        print(f"- consumption_timing: {summary['consumption_timing']}")
        print(f"- requirements: {summary['requirements']}")
        print(f"- task_read_plan: {summary['task_read_plan']}")
        print(f"- missing_fields: {summary['missing_fields']}")
        print(f"- capability_gap: {summary['capability_gap']}")
        print(f"- diagnostics: {summary['diagnostics']}")
        print(f"- next_action: {result['next_action']}")
        print("- authorization: none")
        if result["task_read_plan"]:
            print("\nTask read plan:")
            for item in result["task_read_plan"]:
                path = item["path"] or item["label"]
                print(f"- {item['priority']}/{item['source_type']}: {path} ({item['requirement_id']})")
        if result["missing_fields"]:
            print("\nMissing fields:")
            for item in result["missing_fields"]:
                print(f"- {item['field']}: {item['reason']}")
        if result["diagnostics"]:
            print("\nDiagnostics:")
            for diagnostic in result["diagnostics"]:
                print(f"- {diagnostic['path']} [{diagnostic['level']}/{diagnostic['code']}] {diagnostic['message']}")
        else:
            print("\nDiagnostics: none")
        return

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
        choices=["all", "specs", "timings", "ai-behavior", "action-guide", "preflight", "runtime"],
        help="validation surface to print",
    )
    parser.add_argument("--root", default=ROOT.as_posix(), help="repository root")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--fail-on-diagnostics", action="store_true", help="return non-zero when any diagnostic exists")
    parser.add_argument("--timing", default="session_start", help="consumption timing for action-guide")
    parser.add_argument("--task", default="", help="current task summary for action-guide")
    parser.add_argument("--target-path", default="", help="target path for action-guide")
    parser.add_argument("--trigger-source", default="manual", help="trigger source for action-guide")
    parser.add_argument("--operation", default="write", help="operation for preflight")
    parser.add_argument("--high-impact", action="store_true", help="mark preflight as high impact")
    parser.add_argument("--event", default="session_start", help="runtime canonical event")
    parser.add_argument("--session-id", default="", help="runtime session id")
    parser.add_argument(
        "--acknowledged-path",
        action="append",
        default=[],
        help="acknowledged read plan path for runtime acknowledge_read_plan; may be repeated or comma-separated",
    )
    parser.add_argument(
        "--verification-evidence",
        action="append",
        default=[],
        help="verification evidence for runtime completion_claim; may be repeated or comma-separated",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    if args.command == "action-guide":
        output = build_action_guide(
            root,
            consumption_timing=args.timing,
            task=args.task,
            target_path=args.target_path,
            trigger_source=args.trigger_source,
        )
        result = output
    elif args.command == "preflight":
        output = build_preflight(
            root,
            target_path=args.target_path,
            operation=args.operation,
            task=args.task,
            trigger_source=args.trigger_source,
            high_impact=args.high_impact,
        )
        result = output
    elif args.command == "runtime":
        output = build_runtime_event(
            root,
            event=args.event,
            trigger_source=args.trigger_source,
            session_id=args.session_id,
            target_path=args.target_path,
            task=args.task,
            operation=args.operation,
            acknowledged_paths=args.acknowledged_path,
            verification_evidence=args.verification_evidence,
        )
        result = output
    else:
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
