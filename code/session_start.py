from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from ldvh_specs import ROOT, build_runtime_event


INTEGRATION_SCOPE = "hook.session_start"
RELATIONSHIP_PROJECTION_TEXT_LIMIT = 8


def _bool_text(value: bool) -> str:
    return "true" if value else "false"


def _format_ref(item: dict[str, Any]) -> str:
    return str(item.get("path") or item.get("label") or item.get("to") or item.get("target_path") or "")


def build_session_start(
    root: Path = ROOT,
    *,
    session_id: str = "",
    target_path: str = "",
    cwd: str | Path | None = None,
    config_root: str | Path | None = None,
    target_paths: list[str | Path] | None = None,
    task: str = "",
    trigger_source: str = "hook.runtime",
) -> dict[str, Any]:
    result = build_runtime_event(
        root,
        event="session_start",
        trigger_source=trigger_source,
        session_id=session_id,
        target_path=target_path,
        task=task,
        operation="read",
        cwd=cwd,
        config_root=config_root,
        target_paths=target_paths,
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

    print("LDVH v3 ldvh.session_start Action Guide / read_plan")
    print(f"- status: {summary['status']}")
    print(f"- event: {summary['event']}")
    print(f"- internal_event: {summary['internal_event']}")
    print(f"- session_id: {receipt['session_id']}")
    print(f"- target_path: {receipt['target_path']}")
    print(f"- task_read_plan: {summary['task_read_plan']}")
    print(f"- receipt_id: {receipt['receipt_id']}")
    print(f"- receipt_storage: {receipt['storage']}")
    print(f"- environment_integrated: {_bool_text(summary['environment_integrated'])}")
    print(f"- integration_scope: {summary['integration_scope']}")
    guide_receipt = action_guide.get("guide_receipt", {})
    if guide_receipt:
        print(f"- guide_receipt_id: {guide_receipt.get('receipt_id', '')}")
        print(f"- guide_receipt_storage: {guide_receipt.get('storage', '')}")

    task_context = action_guide.get("task_context", {})
    if task_context:
        print("\nTask context:")
        print(f"- task: {task_context.get('task', '')}")
        print(f"- stage: {task_context.get('current_stage', '')}")
        print(f"- consumption_timing: {task_context.get('consumption_timing', '')}")
        print(f"- trigger_source: {task_context.get('trigger_source', '')}")
        print(f"- target_path: {task_context.get('target_path', '')}")
        target_paths = ", ".join(task_context.get("target_paths", []))
        print(f"- target_paths: {target_paths}")
        print(f"- cwd: {task_context.get('cwd', '')}")
        print(f"- scope_status: {task_context.get('scope_status', '')}")
        print(f"- read_write_kind: {task_context.get('read_write_kind', '')}")
        print(f"- governed_project_id: {task_context.get('governed_project_id', '')}")

    action_type = action_guide.get("action_type", {})
    if action_type:
        print("\nAction type:")
        print(f"- action_type: {action_type.get('action_type', '')}")
        print(f"- source: {action_type.get('action_type_source', '')}")
        print(f"- authorization: {action_type.get('authorization', '')}")

    read_budget = action_guide.get("summary", {}).get("read_budget", {})
    if read_budget:
        print("\nRead budget:")
        print(
            "- P0/P1: "
            f"{read_budget.get('p0_items', 0)}/{read_budget.get('p1_items', 0)} "
            f"(limits {read_budget.get('p0_inline_limit', 0)}/{read_budget.get('p1_inline_limit', 0)})"
        )
        print(f"- overflow_to: {read_budget.get('overflow_to', '')}")

    attention_points = action_guide.get("attention_points", [])
    if attention_points:
        print("\nAttention points:")
        for item in attention_points:
            print(f"- {item.get('message', '')}")

    read_plan = action_guide.get("task_read_plan", [])
    if read_plan:
        print("\nTask read plan:")
        for item in read_plan:
            path = item["path"] or item["label"]
            print(f"- {item['priority']}/{item.get('read_mode', 'contract')}: {path} ({item['requirement_id']})")

    suggested_sections = action_guide.get("suggested_sections", [])
    if suggested_sections:
        print("\nSuggested sections:")
        for item in suggested_sections:
            sections = ", ".join(item.get("sections", []))
            print(f"- {item.get('path', '')}: {sections}")

    relationships = action_guide.get("relationship_projection", [])
    if relationships:
        print("\nRelationship projection:")
        for item in relationships[:RELATIONSHIP_PROJECTION_TEXT_LIMIT]:
            print(f"- {item.get('from', '')} -> {_format_ref(item)} [{item.get('relationship', '')}]")
        if len(relationships) > RELATIONSHIP_PROJECTION_TEXT_LIMIT:
            print(f"- ... {len(relationships) - RELATIONSHIP_PROJECTION_TEXT_LIMIT} more")

    stop_conditions = action_guide.get("stop_conditions", [])
    if stop_conditions:
        print("\nStop conditions:")
        for item in stop_conditions:
            print(f"- {item['requirement_id']}: {item['condition']}")

    validation_guard = action_guide.get("validation_guard", [])
    if validation_guard:
        print("\nValidation guard:")
        for item in validation_guard:
            print(f"- {item.get('requirement_id', '')}: {item.get('guard', '')}")

    tool_plan = action_guide.get("tool_plan", [])
    if tool_plan:
        print("\nTool plan:")
        for item in tool_plan:
            print(f"- {item.get('tool', '')}: {item.get('command', '')}")

    next_queries = action_guide.get("next_queries", [])
    if next_queries:
        print("\nNext queries:")
        for item in next_queries:
            print(f"- {item.get('query', '')}: {item.get('reason', '')}")

    capability_gap = action_guide.get("capability_gap", [])
    if capability_gap:
        print("\nCapability gaps:")
        for item in capability_gap:
            print(f"- {item.get('required_capability', '')}: {item.get('current_gap', '')}")

    unverifiable = action_guide.get("unverifiable", [])
    if unverifiable:
        print("\nUnverifiable:")
        for item in unverifiable:
            print(f"- {item.get('code', '')}: {item.get('reason', '')}")

    source_boundaries = action_guide.get("source_boundaries", [])
    if source_boundaries:
        print("\nSource boundaries:")
        for item in source_boundaries:
            print(f"- {item.get('source_type', '')}: {item.get('boundary', '')}")

    next_action = action_guide.get("next_action", "")
    if next_action:
        print("\nNext action:")
        print(f"- {next_action}")

    post_read_action = action_guide.get("post_read_action", {})
    if post_read_action:
        print("\nPost-read action:")
        print(f"- {post_read_action.get('kind', '')}: {post_read_action.get('instruction', '')}")
        print(f"- authorization: {post_read_action.get('authorization', '')}")

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
    parser.add_argument("--cwd", default="", help="current working directory for target resolution")
    parser.add_argument("--config-root", default="", help="root containing LDVH-GOVERNED-PROJECTS.yaml")
    parser.add_argument("--target-path", default="", help="current target path, if known")
    parser.add_argument("--target-paths", action="append", default=[], help="explicit target path; may be repeated")
    parser.add_argument("--task", default="", help="current task summary")
    parser.add_argument("--trigger-source", default="hook.runtime", help="trigger source label")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = build_session_start(
        Path(args.root).resolve(),
        session_id=args.session_id,
        target_path=args.target_path,
        cwd=args.cwd or None,
        config_root=args.config_root or None,
        target_paths=args.target_paths,
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
