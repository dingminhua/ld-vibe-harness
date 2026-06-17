#!/usr/bin/env python3
"""Preview and optionally write legacy TaskPlan/Task facts as WorkPlan objects.

The default mode is read-only. Write mode requires explicit Human Gate
confirmation flags and only creates WorkPlan facts plus WorkArea back-links; it
does not delete or mutate legacy TaskPlan/Task facts.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml


TASKPLAN_ID_RE = re.compile(r"^taskplan-(\d{4})$")
TASK_ID_RE = re.compile(r"^task-\d{4}$")
TASK_STATUS_TO_EXECUTION_STATUS = {
    "planned": "pending",
    "executing": "in_progress",
    "verifying": "in_progress",
    "review_needed": "done",
    "closed": "done",
}


class BlockScalarDumper(yaml.SafeDumper):
    pass


class LiteralString(str):
    pass


def _string_representer(dumper: yaml.Dumper, data: str) -> yaml.Node:
    style = "|" if "\n" in data else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", str(data), style=style)


BlockScalarDumper.add_representer(str, _string_representer)
BlockScalarDumper.add_representer(LiteralString, _string_representer)


def load_yaml(path: Path) -> dict[str, Any] | None:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return None
    return data if isinstance(data, dict) else None


def json_safe(value: Any) -> Any:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    return value


def as_string(value: Any, fallback: str = "") -> str:
    if value is None:
        return fallback
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return str(value)


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def merge_unique_strings(*values: Any) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        for item in as_list(value):
            if not isinstance(item, str) or not item.strip():
                continue
            if item in seen:
                continue
            seen.add(item)
            result.append(item)
    return result


def blockify_multiline(value: Any) -> Any:
    if isinstance(value, str) and "\n" in value:
        return LiteralString(value)
    if isinstance(value, dict):
        return {key: blockify_multiline(item) for key, item in value.items()}
    if isinstance(value, list):
        return [blockify_multiline(item) for item in value]
    return value


def write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.dump(
            blockify_multiline(data),
            Dumper=BlockScalarDumper,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
        ),
        encoding="utf-8",
    )


def render_workplans_block(workplan_ids: list[str]) -> str:
    if not workplan_ids:
        return "workplans: []\n"
    return "workplans:\n" + "".join(f"- {workplan_id}\n" for workplan_id in workplan_ids)


def replace_workplans_block(text: str, workplan_ids: list[str]) -> str:
    lines = text.splitlines(keepends=True)
    for start, line in enumerate(lines):
        if not re.match(r"^workplans\s*:", line):
            continue
        end = start + 1
        while end < len(lines):
            candidate = lines[end]
            is_top_level_key = candidate == candidate.lstrip() and bool(re.match(r"^[A-Za-z_][A-Za-z0-9_-]*\s*:", candidate))
            if is_top_level_key:
                break
            end += 1
        return "".join(lines[:start]) + render_workplans_block(workplan_ids) + "".join(lines[end:])

    suffix = "" if text.endswith("\n") or not text else "\n"
    return text + suffix + render_workplans_block(workplan_ids)


def update_workarea_workplans(path: Path, workplan_ids: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    path.write_text(replace_workplans_block(text, workplan_ids), encoding="utf-8")


def target_id_for_taskplan(taskplan_id: str) -> str:
    match = TASKPLAN_ID_RE.match(taskplan_id)
    if not match:
        return ""
    return f"workplan-{match.group(1)}"


def target_path_for_taskplan(source_path: Path, target_dir: Path, target_id: str) -> Path:
    suffix = source_path.name.split("-", 2)[2] if len(source_path.name.split("-", 2)) >= 3 else "migrated.yaml"
    return target_dir / f"{target_id}-{suffix}"


def task_result_summary(task: dict[str, Any]) -> str:
    parts = []
    verification = as_string(task.get("verification")).strip()
    closure = as_string(task.get("closure_evidence")).strip()
    if verification:
        parts.append("verification: " + verification)
    if closure:
        parts.append("closure_evidence: " + closure)
    if parts:
        return "\n\n".join(parts)
    return f"Legacy task {task.get('id', '')} status was {task.get('status', 'unknown')}."


def normalize_evidence_text(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        return ""
    if re.search(r"##\s*验证结果|##\s*结果|##\s*Result|##\s*结论|##\s*Conclusion", stripped):
        return stripped
    return f"## 验证结果\n\n{stripped}"


def execution_item_from_task(task_id: str, task: dict[str, Any] | None) -> tuple[dict[str, Any], list[dict[str, str]]]:
    issues: list[dict[str, str]] = []
    if task is None:
        issues.append({"level": "error", "code": "TASK_NOT_FOUND", "message": f"Task not found: {task_id}"})
        return {
            "id": task_id,
            "title": task_id,
            "role": "legacy-task",
            "mode": "single",
            "input_refs": [task_id],
            "expected_output": "Recover legacy Task result.",
            "status": "blocked",
            "result_summary": "",
            "evidence_refs": [],
            "blocking_reason": f"Legacy Task not found: {task_id}",
        }, issues

    task_status = as_string(task.get("status"), "planned")
    execution_status = TASK_STATUS_TO_EXECUTION_STATUS.get(task_status, "blocked")
    if execution_status == "blocked":
        issues.append({"level": "warning", "code": "UNKNOWN_TASK_STATUS", "message": f"Task {task_id} has unmapped status: {task_status}"})

    evidence_refs = merge_unique_strings(task.get("deliverables"), task.get("related_docs"), task.get("affected_docs"), task.get("related_adrs"), task.get("related_changes"))
    result_summary = task_result_summary(task) if execution_status == "done" else ""
    blocking_reason = ""
    if execution_status in {"pending", "in_progress"}:
        blocking_reason = "Legacy Task is not closed; keep WorkPlan active after migration."
    elif execution_status == "blocked":
        blocking_reason = f"Legacy Task status requires manual review: {task_status}"

    return {
        "id": task_id,
        "title": as_string(task.get("title"), task_id),
        "role": "legacy-task",
        "mode": "single",
        "input_refs": [task_id],
        "expected_output": as_string(task.get("acceptance"), "Recover legacy Task result."),
        "status": execution_status,
        "result_summary": result_summary,
        "evidence_refs": evidence_refs,
        "blocking_reason": blocking_reason or None,
    }, issues


def workplan_status_for_taskplan(taskplan: dict[str, Any], execution_items: list[dict[str, Any]]) -> tuple[str, list[dict[str, str]]]:
    warnings: list[dict[str, str]] = []
    status = as_string(taskplan.get("status"), "draft")
    if status in {"draft", "active"}:
        return status, warnings
    if status == "review_needed":
        open_items = [item["id"] for item in execution_items if item.get("status") in {"pending", "in_progress"}]
        if open_items:
            warnings.append({
                "level": "warning",
                "code": "REVIEW_NEEDED_WITH_OPEN_EXECUTION_ITEMS",
                "message": f"review_needed TaskPlan has open legacy Tasks: {', '.join(open_items)}; proposed WorkPlan is downgraded to active.",
            })
            return "active", warnings
        return "review_needed", warnings
    if status == "closed":
        open_items = [item["id"] for item in execution_items if item.get("status") in {"pending", "in_progress"}]
        if open_items:
            warnings.append({
                "level": "warning",
                "code": "CLOSED_WITH_OPEN_EXECUTION_ITEMS",
                "message": f"closed TaskPlan has open legacy Tasks: {', '.join(open_items)}; proposed WorkPlan is downgraded to active.",
            })
            return "active", warnings
        return "closed", warnings
    warnings.append({"level": "warning", "code": "UNKNOWN_TASKPLAN_STATUS", "message": f"Unknown TaskPlan status: {status}; proposed WorkPlan is draft."})
    return "draft", warnings


def build_workplan(
    taskplan: dict[str, Any],
    tasks_by_id: dict[str, dict[str, Any]],
    source_path: Path,
    target_path: Path,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    issues: list[dict[str, str]] = []
    taskplan_id = as_string(taskplan.get("id"))
    target_id = target_id_for_taskplan(taskplan_id)
    task_ids = [item for item in as_list(taskplan.get("tasks")) if isinstance(item, str)]

    if not target_id:
        issues.append({"level": "error", "code": "INVALID_TASKPLAN_ID", "message": f"Invalid TaskPlan id: {taskplan_id}"})
    if not task_ids:
        issues.append({"level": "error", "code": "TASKPLAN_WITHOUT_TASKS", "message": f"TaskPlan has no tasks: {taskplan_id}"})

    execution_items = []
    for task_id in task_ids:
        if not TASK_ID_RE.match(task_id):
            issues.append({"level": "error", "code": "INVALID_TASK_ID", "message": f"Invalid task id in {taskplan_id}: {task_id}"})
            continue
        execution_item, item_issues = execution_item_from_task(task_id, tasks_by_id.get(task_id))
        execution_items.append(execution_item)
        issues.extend(item_issues)

    proposed_status, status_warnings = workplan_status_for_taskplan(taskplan, execution_items)
    issues.extend(status_warnings)
    mode = "single" if len(execution_items) <= 1 else "sequential"
    completion_evidence = normalize_evidence_text(as_string(taskplan.get("completion_evidence")))
    verification_evidence = completion_evidence
    closure_evidence = completion_evidence
    if completion_evidence:
        issues.append({
            "level": "warning",
            "code": "COMPLETION_EVIDENCE_SPLIT",
            "message": "Legacy completion_evidence is copied to both verification_evidence and closure_evidence; review semantic fit before writing.",
        })

    workplan = {
        "id": target_id,
        "type": "workplan",
        "title": taskplan.get("title", target_id),
        "status": proposed_status,
        "created": taskplan.get("created", ""),
        "updated": taskplan.get("updated", ""),
        "workarea": taskplan.get("workarea", ""),
        "priority": taskplan.get("priority", "P2"),
        "description": taskplan.get("description", ""),
        "success_criteria": taskplan.get("success_criteria", ""),
        "source": f"Legacy TaskPlan migration from {taskplan_id}; source path: {source_path}",
        "orchestration": {
            "mode": mode,
            "execution_items": execution_items,
            "review": {
                "controller_self_check": True,
                "specialist_review": {
                    "required": False,
                    "role": None,
                    "expected_output": None,
                },
                "human_closure_review": True,
            },
        },
        "verification_evidence": verification_evidence,
        "closure_evidence": closure_evidence,
        "review_requested_at": taskplan.get("review_requested_at", "") if proposed_status in {"review_needed", "closed"} else "",
        "closed_at": taskplan.get("closed_at", "") if proposed_status == "closed" else "",
        "related_docs": taskplan.get("related_docs", []),
        "related_adrs": taskplan.get("related_adrs", []),
        "related_memos": taskplan.get("related_memos", []),
        "related_pitfalls": taskplan.get("related_pitfalls", []),
        "related_workplans": [],
        "related_changes": [],
    }

    if proposed_status in {"review_needed", "closed"}:
        for field in ("verification_evidence", "closure_evidence", "review_requested_at"):
            if not workplan.get(field):
                issues.append({"level": "error", "code": "MISSING_WORKPLAN_REVIEW_FIELD", "message": f"Proposed {proposed_status} WorkPlan lacks {field}."})
    if proposed_status == "closed" and not workplan.get("closed_at"):
        issues.append({"level": "error", "code": "MISSING_WORKPLAN_CLOSED_AT", "message": "Proposed closed WorkPlan lacks closed_at."})

    return workplan, issues


def collect_objects(
    base_dir: Path,
) -> tuple[
    list[tuple[Path, dict[str, Any]]],
    dict[str, dict[str, Any]],
    dict[str, Path],
    dict[str, dict[str, Any]],
    dict[str, Path],
]:
    ldvh_base = base_dir / "ldvh-base"
    taskplans: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted((ldvh_base / "taskplans").glob("taskplan-*.yaml")):
        data = load_yaml(path)
        if data:
            taskplans.append((path, data))

    tasks_by_id: dict[str, dict[str, Any]] = {}
    for path in sorted((ldvh_base / "tasks").glob("task-*.yaml")):
        data = load_yaml(path)
        if data and isinstance(data.get("id"), str):
            tasks_by_id[data["id"]] = data

    workplan_paths: dict[str, Path] = {}
    for path in sorted((ldvh_base / "workplans").glob("workplan-*.yaml")):
        data = load_yaml(path)
        if data and isinstance(data.get("id"), str):
            workplan_paths[data["id"]] = path

    workareas_by_id: dict[str, dict[str, Any]] = {}
    workarea_paths: dict[str, Path] = {}
    for path in sorted((ldvh_base / "workareas").glob("workarea-*.yaml")):
        data = load_yaml(path)
        if data and isinstance(data.get("id"), str):
            workareas_by_id[data["id"]] = data
            workarea_paths[data["id"]] = path

    return taskplans, tasks_by_id, workplan_paths, workareas_by_id, workarea_paths


def preview_migration(base_dir: Path, ids: list[str] | None = None, statuses: list[str] | None = None) -> dict[str, Any]:
    taskplans, tasks_by_id, existing_workplans, workareas_by_id, _workarea_paths = collect_objects(base_dir)
    id_filter = set(ids or [])
    status_filter = set(statuses or [])
    target_dir = base_dir / "ldvh-base" / "workplans"
    items = []
    by_status: Counter[str] = Counter()
    issue_count = 0
    blocked_count = 0

    for source_path, taskplan in taskplans:
        taskplan_id = as_string(taskplan.get("id"))
        taskplan_status = as_string(taskplan.get("status"))
        if id_filter and taskplan_id not in id_filter:
            continue
        if status_filter and taskplan_status not in status_filter:
            continue

        target_id = target_id_for_taskplan(taskplan_id)
        target_path = target_path_for_taskplan(source_path, target_dir, target_id or "workplan-0000")
        workplan, issues = build_workplan(taskplan, tasks_by_id, source_path, target_path)
        if target_id in existing_workplans:
            issues.append({
                "level": "error",
                "code": "TARGET_WORKPLAN_EXISTS",
                "message": f"Target WorkPlan already exists: {target_id}",
            })
        workarea_id = as_string(workplan.get("workarea"))
        if not workarea_id or workarea_id not in workareas_by_id:
            issues.append({
                "level": "error",
                "code": "WORKAREA_NOT_FOUND",
                "message": f"Target WorkPlan references missing WorkArea: {workarea_id or '<empty>'}",
            })

        error_count = sum(1 for issue in issues if issue["level"] == "error")
        warning_count = sum(1 for issue in issues if issue["level"] == "warning")
        issue_count += len(issues)
        blocked_count += 1 if error_count else 0
        by_status[taskplan_status] += 1

        items.append({
            "source_id": taskplan_id,
            "source_status": taskplan_status,
            "source_path": str(source_path),
            "target_id": target_id,
            "target_path": str(target_path),
            "task_count": len(as_list(taskplan.get("tasks"))),
            "execution_item_count": len(workplan.get("orchestration", {}).get("execution_items", [])),
            "can_convert": error_count == 0,
            "error_count": error_count,
            "warning_count": warning_count,
            "issues": issues,
            "mapping": {
                "taskplan.id": "workplan.id",
                "taskplan.tasks[]": "workplan.orchestration.execution_items[]",
                "taskplan.completion_evidence": ["workplan.verification_evidence", "workplan.closure_evidence"],
                "taskplan.related_*": "workplan.related_*",
            },
            "workplan": workplan,
        })

    return {
        "ok": blocked_count == 0,
        "action": "preview-taskplan-to-workplan",
        "summary": {
            "taskplan_count": len(items),
            "convertible_count": len(items) - blocked_count,
            "blocked_count": blocked_count,
            "issue_count": issue_count,
            "by_source_status": dict(sorted(by_status.items())),
        },
        "items": items,
    }


def confirmation_error_result(message: str) -> dict[str, Any]:
    return {
        "ok": False,
        "action": "write-taskplan-to-workplan",
        "summary": {
            "taskplan_count": 0,
            "convertible_count": 0,
            "blocked_count": 1,
            "issue_count": 1,
            "by_source_status": {},
        },
        "items": [],
        "write": {
            "written_count": 0,
            "updated_workarea_count": 0,
            "written_paths": [],
            "updated_workarea_paths": [],
        },
        "issues": [{"level": "error", "code": "HUMAN_GATE_REQUIRED", "message": message}],
    }


def validate_write_confirmation(args: argparse.Namespace) -> str | None:
    if not args.human_gate_confirmed:
        return "Write mode requires --human-gate-confirmed."
    if not as_string(args.confirmed_by).strip():
        return "Write mode requires --confirmed-by."
    if not as_string(args.confirmation_context).strip():
        return "Write mode requires --confirmation-context."
    return None


def append_human_gate_source(workplan: dict[str, Any], args: argparse.Namespace) -> None:
    confirmation = f"Human Gate confirmed by {args.confirmed_by}: {args.confirmation_context}"
    existing_source = as_string(workplan.get("source")).rstrip()
    workplan["source"] = f"{existing_source}\n{confirmation}" if existing_source else confirmation


def workplan_sort_key(workplan_id: str) -> tuple[int, str]:
    match = re.match(r"^workplan-(\d{4})$", workplan_id)
    return (int(match.group(1)) if match else 9999, workplan_id)


def write_migration(base_dir: Path, args: argparse.Namespace) -> dict[str, Any]:
    confirmation_error = validate_write_confirmation(args)
    if confirmation_error:
        return confirmation_error_result(confirmation_error)

    result = preview_migration(base_dir, ids=args.ids, statuses=args.statuses)
    result["action"] = "write-taskplan-to-workplan"
    result["write"] = {
        "written_count": 0,
        "updated_workarea_count": 0,
        "written_paths": [],
        "updated_workarea_paths": [],
    }
    if not result["ok"]:
        return result

    _taskplans, _tasks_by_id, _existing_workplans, workareas_by_id, workarea_paths = collect_objects(base_dir)
    written_paths: list[str] = []
    updated_workareas: set[str] = set()

    for item in result["items"]:
        workplan = item["workplan"]
        append_human_gate_source(workplan, args)
        target_path = Path(item["target_path"])
        write_yaml(target_path, workplan)
        written_paths.append(str(target_path))

        workarea_id = as_string(workplan.get("workarea"))
        workarea = workareas_by_id[workarea_id]
        existing_refs = [ref for ref in as_list(workarea.get("workplans")) if isinstance(ref, str) and ref.strip()]
        refs = sorted(set(existing_refs + [workplan["id"]]), key=workplan_sort_key)
        if refs != existing_refs:
            workarea["workplans"] = refs
            updated_workareas.add(workarea_id)

    updated_workarea_paths: list[str] = []
    for workarea_id in sorted(updated_workareas):
        path = workarea_paths[workarea_id]
        update_workarea_workplans(path, workareas_by_id[workarea_id]["workplans"])
        updated_workarea_paths.append(str(path))

    result["write"] = {
        "written_count": len(written_paths),
        "updated_workarea_count": len(updated_workarea_paths),
        "written_paths": written_paths,
        "updated_workarea_paths": updated_workarea_paths,
    }
    return result


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Preview or write legacy TaskPlan facts as WorkPlan objects.")
    parser.add_argument("--base-dir", default=".", help="Project root containing ldvh-base/")
    parser.add_argument("--id", action="append", dest="ids", help="Limit preview to a TaskPlan id; may be repeated.")
    parser.add_argument("--status", action="append", dest="statuses", help="Limit preview to a TaskPlan status; may be repeated.")
    parser.add_argument("--write", action="store_true", help="Write generated WorkPlan facts and WorkArea back-links.")
    parser.add_argument("--human-gate-confirmed", action="store_true", help="Required with --write after explicit Human Gate approval.")
    parser.add_argument("--confirmed-by", help="Human or delegated approver identity for --write.")
    parser.add_argument("--confirmation-context", help="Short context proving why --write was authorized.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if args.write:
        result = write_migration(Path(args.base_dir), args)
    else:
        result = preview_migration(Path(args.base_dir), ids=args.ids, statuses=args.statuses)
    print(json.dumps(json_safe(result), ensure_ascii=False, indent=2 if args.pretty else None))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
