"""Controlled write preflight diagnostics for LDVH assets."""

import json
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PREFLIGHT_TOOL = "code/specs_validate.py preflight"
PREFLIGHT_OPERATIONS = {"create", "update", "delete", "move", "rename"}
HIGH_IMPACT_OPERATIONS = {"delete", "move", "rename"}


AUTHORIZED_PREFIXES = [
    ("specs/", "specs", "01/04/07"),
    ("code/", "code", "04/08"),
    ("web/", "web", "05/08"),
    ("rules/", "runtime_extension", "06/07"),
    ("skills/", "runtime_extension", "06/07"),
    ("agents/", "runtime_extension", "06/07"),
    ("hooks/", "runtime_extension", "06/07"),
    ("tests/", "tests", "08"),
    ("ldvh-base/", "fact_source", "02/07"),
]
AUTHORIZED_FILES = {
    "LDVH-GOVERNED-PROJECTS.yaml": ("runtime_extension", "06/07"),
    "README.md": ("project_entry", "01/07"),
}


def source_ref(path, line=1, field=None):
    ref = {"path": path, "line_start": line, "line_end": line}
    if field:
        ref["field"] = field
    return ref


def diagnostic(code, severity, message, path, owner, check_id):
    return {
        "severity": severity,
        "code": code,
        "message": message,
        "path": path,
        "line": 1,
        "suggested_owner": owner,
        "check_id": check_id,
        "source_refs": [source_ref(path)],
    }


def relative_target(root, target_path):
    path = Path(target_path)
    absolute = path if path.is_absolute() else root / path
    try:
        relative = absolute.resolve().relative_to(root.resolve())
        return str(relative), absolute.resolve(), True
    except ValueError:
        return str(absolute), absolute.resolve(), False


def classify_target(relative_path, inside_root):
    if not inside_root:
        return None
    if relative_path in AUTHORIZED_FILES:
        asset_type, owner = AUTHORIZED_FILES[relative_path]
        return {"asset_type": asset_type, "owner": owner}
    for prefix, asset_type, owner in AUTHORIZED_PREFIXES:
        if relative_path.startswith(prefix):
            return {"asset_type": asset_type, "owner": owner}
    return None


def check_status(diagnostics):
    if any(item["severity"] == "error" for item in diagnostics):
        return "blocked"
    if any(item["severity"] == "warning" for item in diagnostics):
        return "needs_human_gate"
    return "pass"


def preflight_build(root=None, target_path=None, operation="update", field_path=None, status=None):
    root = Path(root or PROJECT_ROOT).resolve()
    relative_path, absolute_path, inside_root = relative_target(root, target_path or "")
    target_info = classify_target(relative_path, inside_root)
    operation = operation or "update"
    diagnostics = []
    checks = []

    def add_check(check_id, label, items):
        checks.append(
            {
                "id": check_id,
                "label": label,
                "status": check_status(items),
                "diagnostics": items,
            }
        )
        diagnostics.extend(items)

    if operation not in PREFLIGHT_OPERATIONS:
        add_check(
            "operation",
            "操作类型",
            [
                diagnostic(
                    "PREFLIGHT_OPERATION_INVALID",
                    "error",
                    f"operation 非法: {operation}",
                    relative_path or "<runtime>",
                    "04-Code确定性执行规范",
                    "operation",
                )
            ],
        )
    else:
        add_check("operation", "操作类型", [])

    if not target_info:
        add_check(
            "authorized_location",
            "授权位置",
            [
                diagnostic(
                    "PREFLIGHT_TARGET_LOCATION_UNAUTHORIZED",
                    "error",
                    "写入目标不在当前受控写入授权位置内",
                    relative_path or "<runtime>",
                    "04-Code确定性执行规范",
                    "authorized_location",
                )
            ],
        )
    else:
        add_check("authorized_location", "授权位置", [])

    field_items = []
    exists = absolute_path.exists()
    if operation == "create" and exists:
        field_items.append(
            diagnostic(
                "PREFLIGHT_CREATE_TARGET_EXISTS",
                "error",
                "create 操作的目标已存在",
                relative_path,
                target_info["owner"] if target_info else "04-Code确定性执行规范",
                "field_and_state",
            )
        )
    if operation in {"update", "delete", "move", "rename"} and not exists:
        field_items.append(
            diagnostic(
                "PREFLIGHT_TARGET_MISSING",
                "error",
                f"{operation} 操作的目标不存在",
                relative_path,
                target_info["owner"] if target_info else "04-Code确定性执行规范",
                "field_and_state",
            )
        )
    if target_info and target_info["asset_type"] in {"specs", "project_entry"} and absolute_path.suffix != ".md":
        field_items.append(
            diagnostic(
                "PREFLIGHT_MARKDOWN_EXPECTED",
                "warning",
                "该位置通常应使用 Markdown 承载；请确认目标格式是否由上位规范授权",
                relative_path,
                target_info["owner"],
                "field_and_state",
            )
        )
    if field_path:
        field_items.append(
            diagnostic(
                "PREFLIGHT_FIELD_PATH_NOT_VALIDATED",
                "warning",
                f"field_path 已接收但第一版 preflight 尚未做字段级 Schema 校验: {field_path}",
                relative_path,
                target_info["owner"] if target_info else "04-Code确定性执行规范",
                "field_and_state",
            )
        )
    if status:
        field_items.append(
            diagnostic(
                "PREFLIGHT_STATUS_CHANGE_REQUIRES_OWNER_RULE",
                "warning",
                f"status={status} 需要回到对应规范或事实模型确认状态规则",
                relative_path,
                target_info["owner"] if target_info else "04-Code确定性执行规范",
                "field_and_state",
            )
        )
    add_check("field_and_state", "字段与状态", field_items)

    gate_items = []
    if operation in HIGH_IMPACT_OPERATIONS or status or (target_info and target_info["asset_type"] in {"specs", "runtime_extension", "fact_source"}):
        gate_items.append(
            diagnostic(
                "PREFLIGHT_HUMAN_GATE_REQUIRED",
                "warning",
                "本次写入可能影响规范、运行时扩展、事实源、状态或路径，应先识别 Human Gate",
                relative_path,
                target_info["owner"] if target_info else "04-Code确定性执行规范",
                "human_gate",
            )
        )
    add_check("human_gate", "Human Gate", gate_items)

    add_check(
        "git_trace",
        "Git 追溯",
        [
            diagnostic(
                "PREFLIGHT_GIT_TRACE_REQUIRED",
                "info",
                "若继续写入，应通过 Git commit records 保留事实源追溯",
                relative_path,
                "07-事实源边界与Git追溯规范",
                "git_trace",
            )
        ],
    )

    sync_owner = target_info["owner"] if target_info else "04-Code确定性执行规范"
    add_check(
        "sync_impact",
        "同步影响",
        [
            diagnostic(
                "PREFLIGHT_SYNC_IMPACT_REVIEW_REQUIRED",
                "info",
                "继续写入前应检查 specs、Code、Web、运行时扩展和测试是否存在同步影响",
                relative_path,
                sync_owner,
                "sync_impact",
            )
        ],
    )

    add_check(
        "failure_owner",
        "失败归口",
        [
            diagnostic(
                "PREFLIGHT_FAILURE_OWNER_IDENTIFIED",
                "info",
                f"检查失败或降级时回到 {sync_owner}",
                relative_path,
                sync_owner,
                "failure_owner",
            )
        ],
    )

    summary_status = check_status(diagnostics)
    return {
        "metadata": {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "tool": PREFLIGHT_TOOL,
            "read_only": True,
            "write_authorized": False,
            "root": str(root),
        },
        "input": {
            "operation": operation,
            "target_path": target_path,
            "relative_path": relative_path,
            "field_path": field_path,
            "status": status,
            "asset_type": target_info["asset_type"] if target_info else None,
        },
        "summary": {
            "status": summary_status,
            "error_count": sum(1 for item in diagnostics if item["severity"] == "error"),
            "warning_count": sum(1 for item in diagnostics if item["severity"] == "warning"),
            "info_count": sum(1 for item in diagnostics if item["severity"] == "info"),
        },
        "checks": checks,
        "diagnostics": diagnostics,
    }


def preflight_format_text(report):
    summary = report.get("summary", {})
    input_data = report.get("input", {})
    lines = [
        "受控写入 preflight 完成",
        f"- operation: {input_data.get('operation')}",
        f"- target: {input_data.get('relative_path')}",
        f"- asset_type: {input_data.get('asset_type')}",
        f"- status: {summary.get('status')}",
        f"- write_authorized: {report.get('metadata', {}).get('write_authorized')}",
        f"- errors: {summary.get('error_count', 0)}",
        f"- warnings: {summary.get('warning_count', 0)}",
        f"- infos: {summary.get('info_count', 0)}",
    ]
    for item in report.get("diagnostics", []):
        lines.append(f"- {item['path']} [{item['severity']}/{item['code']}] {item['message']}")
    return "\n".join(lines)


def preflight_main(root=None, target_path=None, operation="update", field_path=None, status=None, output_format="text"):
    report = preflight_build(root, target_path, operation, field_path, status)
    if output_format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(preflight_format_text(report))
    return 1 if report.get("summary", {}).get("status") == "blocked" else 0
