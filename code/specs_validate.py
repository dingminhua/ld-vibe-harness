from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from ldvh_specs import (
    ROOT,
    build_action_guide,
    build_commit_gate,
    build_e2e_rehearsal,
    build_governed_projects_report,
    build_preflight,
    build_runtime_event,
    build_validation,
)


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

    if command == "governed-projects":
        summary = result["summary"]
        resolution = result["resolution"]
        print("LDVH v3 受管项目解析完成")
        print(f"- status: {summary['status']}")
        print(f"- projects: {summary['projects']}")
        print(f"- governed: {summary['governed']}")
        print(f"- blocked: {summary['blocked']}")
        print(f"- governed_project_id: {resolution['governed_project_id']}")
        print(f"- governed_via: {resolution['governed_via']}")
        print(f"- diagnostics: {summary['diagnostics']}")
        if result["diagnostics"]:
            print("\nDiagnostics:")
            for diagnostic in result["diagnostics"]:
                print(f"- {diagnostic['path']} [{diagnostic['level']}/{diagnostic['code']}] {diagnostic['message']}")
        else:
            print("\nDiagnostics: none")
        print("\nAuthorization: none")
        return

    if command == "e2e":
        summary = result["summary"]
        print("LDVH v3 端到端闭环演练完成")
        print(f"- status: {summary['status']}")
        print(f"- target_path: {summary['target_path']}")
        print(f"- stages: {summary['stages']}")
        print(f"- governed: {summary['governed']}")
        print(f"- validation_status: {summary['validation_status']}")
        print(f"- environment_integrated: {summary['environment_integrated']}")
        print(f"- diagnostics: {summary['diagnostics']}")
        print(f"- blocking: {summary['blocking']}")
        print("\nWorkflow:")
        for stage in result["workflow"]:
            print(f"- {stage['stage']}: {stage['status']} (diagnostics={stage['diagnostics']}, blocking={stage['blocking']})")
        if result["diagnostics"]:
            print("\nDiagnostics:")
            for diagnostic in result["diagnostics"]:
                print(f"- {diagnostic['origin']}::{diagnostic['path']} [{diagnostic['level']}/{diagnostic['code']}] {diagnostic['message']}")
        else:
            print("\nDiagnostics: none")
        print("\nAuthorization: none")
        return

    if command == "commit-gate":
        summary = result["summary"]
        print("LDVH v3 commit gate 校验完成")
        print(f"- status: {summary['status']}")
        print(f"- message_type: {summary['message_type']}")
        print(f"- message_scope: {summary['message_scope']}")
        print(f"- changed_paths: {summary['changed_paths']}")
        print(f"- body_required: {summary['body_required']}")
        print(f"- read_plan_required: {summary['read_plan_required']}")
        print(f"- read_plan_consumed: {summary['read_plan_consumed']}")
        print(f"- environment_integrated: {summary['environment_integrated']}")
        print(f"- diagnostics: {summary['diagnostics']}")
        print(f"- blocking: {summary['blocking']}")
        if result["body_required_reasons"]:
            print("\nBody required reasons:")
            for reason in result["body_required_reasons"]:
                print(f"- {reason}")
        if result["diagnostics"]:
            print("\nDiagnostics:")
            for diagnostic in result["diagnostics"]:
                print(f"- {diagnostic['path']} [{diagnostic['level']}/{diagnostic['code']}] {diagnostic['message']}")
        else:
            print("\nDiagnostics: none")
        print("\nAuthorization: none")
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
    print(f"- foundation_spec_contracts: {summary['foundation_spec_contracts']}")
    print(f"- fact_instances: {summary['fact_instances']}")
    print(f"- governed_projects: {summary['governed_projects']}")
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
            "foundation_spec_contracts": result["foundation_spec_contracts"],
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
        choices=[
            "all",
            "specs",
            "timings",
            "ai-behavior",
            "action-guide",
            "preflight",
            "runtime",
            "governed-projects",
            "e2e",
            "commit-gate",
        ],
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
    parser.add_argument("--message", default="", help="commit message text for commit-gate")
    parser.add_argument("--message-file", default="", help="path to commit message file for commit-gate")
    parser.add_argument(
        "--changed-path",
        action="append",
        default=[],
        help="changed path for commit-gate; may be repeated or comma-separated",
    )
    parser.add_argument("--require-read-plan", action="store_true", help="require external read_plan evidence for commit-gate")
    parser.add_argument("--no-require-read-plan", action="store_true", help=argparse.SUPPRESS)
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
    elif args.command == "commit-gate":
        message = args.message
        if args.message_file:
            message = Path(args.message_file).read_text(encoding="utf-8")
        output = build_commit_gate(
            root,
            message=message,
            changed_paths=args.changed_path,
            acknowledged_paths=args.acknowledged_path,
            require_read_plan=args.require_read_plan and not args.no_require_read_plan,
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
    elif args.command == "governed-projects":
        target_paths = [args.target_path] if args.target_path else []
        output = build_governed_projects_report(
            root,
            cwd=root,
            target_paths=target_paths,
            read_write_kind="commit" if args.operation == "commit" else "write",
        )
        result = output
    elif args.command == "e2e":
        output = build_e2e_rehearsal(
            root,
            target_path=args.target_path or "tests/code/test_ldvh_specs_validate.py",
            task=args.task or "LDVH v3 stage 8 end-to-end rehearsal",
            operation=args.operation,
            trigger_source=args.trigger_source,
            verification_evidence=args.verification_evidence or None,
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
