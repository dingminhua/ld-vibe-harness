#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


# Change 使用 Git commit 作为事实源，不通过本 CLI 管理 YAML 文件
OBJECT_TYPES = {"intent", "task", "adr", "pitfall", "memo"}
FILENAME_PATTERNS = {
    "intent": re.compile(r"^intent-\d{4}-[a-z0-9]+(?:-[a-z0-9]+)*\.yaml$"),
    "task": re.compile(r"^task-\d{4}-[a-z0-9]+(?:-[a-z0-9]+)*\.yaml$"),
    "adr": re.compile(r"^adr-\d{4}-[a-z0-9]+(?:-[a-z0-9]+)*\.yaml$"),
    "pitfall": re.compile(r"^pitfall-\d{4}-[a-z0-9]+(?:-[a-z0-9]+)*\.yaml$"),
    "memo": re.compile(r"^memo-\d{4}-[a-z0-9]+(?:-[a-z0-9]+)*\.yaml$"),
}
ID_PATTERNS = {
    "intent": re.compile(r"^intent-\d{4}$"),
    "task": re.compile(r"^task-\d{4}$"),
    "adr": re.compile(r"^adr-\d{4}$"),
    "pitfall": re.compile(r"^pitfall-\d{4}$"),
    "memo": re.compile(r"^memo-\d{4}$"),
}
VALID_STATUSES = {
    "intent": {"draft", "active", "completed", "closed"},
    "task": {"planned", "executing", "verifying", "review_needed", "closed"},
    "adr": {"proposed", "accepted", "rejected", "deprecated", "superseded"},
    "pitfall": {"draft", "active", "superseded", "archived"},
    "memo": {"draft", "active", "resolved", "archived"},
}
REQUIRED_FIELDS = {
    "intent": ["id", "type", "title", "status", "created", "updated", "description", "success_criteria", "source"],
    "task": ["id", "type", "title", "status", "created", "updated", "description", "source", "acceptance"],
    "adr": ["id", "type", "title", "status", "created", "updated", "context", "decision", "consequences"],
    "pitfall": ["id", "type", "title", "status", "created", "updated", "symptoms", "trigger_conditions", "root_cause", "resolution", "verification", "avoidance", "applicability"],
    "memo": ["id", "type", "title", "status", "created", "updated", "description", "source", "category"],
}
LIST_FIELDS = {
    "intent": {"related_tasks", "related_adrs", "related_pitfalls", "related_docs"},
    "task": {"related_adrs", "sub_tasks", "blocked_by", "related_docs", "affected_docs", "deliverables"},
    "adr": {"related_tasks", "related_adrs"},
    "pitfall": {
        "source_objects", "related_objects", "related_rules", "tags",
        "source_tasks", "source_memos", "related_intents", "related_adrs",
        "related_changes", "related_docs",
    },
    "memo": {"related_tasks", "related_adrs", "related_docs"},
}

# 12-工作模型字段内容格式规范：长文本字段定义
LONG_TEXT_FIELDS = {
    "intent": {"description", "success_criteria", "constraints"},
    "task": {"description", "acceptance", "verification", "closure_evidence"},
    "adr": {"context", "decision", "consequences"},
    "pitfall": {"symptoms", "trigger_conditions", "root_cause", "resolution", "verification", "avoidance", "applicability"},
    "memo": {"description"},
}

# 12-工作模型字段内容格式规范：路径引用字段定义
PATH_FIELDS = {"related_docs", "deliverables", "affected_docs", "related_rules"}

# 12-工作模型字段内容格式规范：Evidence 字段定义
EVIDENCE_FIELDS = {"verification", "closure_evidence"}

# 危险 HTML 标签和属性模式
DANGEROUS_HTML_PATTERNS = [
    re.compile(r"<\s*script", re.IGNORECASE),
    re.compile(r"<\s*iframe", re.IGNORECASE),
    re.compile(r"<\s*[a-z][a-z0-9]*\s+[^>]*on\w+\s*=", re.IGNORECASE),
]


@dataclass(frozen=True)
class Issue:
    path: str
    level: str
    code: str
    message: str
    field: str | None = None
    suggestion: str | None = None

    def format(self) -> str:
        return f"{self.path}: [{self.level}] {self.code}: {self.message}"

    def to_dict(self) -> dict[str, str | None]:
        return {
            "level": self.level,
            "code": self.code,
            "message": self.message,
            "path": self.path,
            "field": self.field,
            "suggestion": self.suggestion,
        }


def is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    if isinstance(value, (list, dict)) and not value:
        return True
    return False


def collect_yaml_files(paths: list[str]) -> tuple[list[Path], list[Issue]]:
    files = []
    issues = []
    seen = set()
    for raw_path in paths:
        path = Path(raw_path)
        display_path = str(path)
        if not path.exists():
            issues.append(Issue(display_path, "error", "INPUT_PATH_MISSING", "路径不存在"))
            continue
        if path.is_file():
            if path.suffix != ".yaml":
                issues.append(Issue(display_path, "error", "INPUT_NOT_YAML", "输入文件必须是 .yaml 文件"))
                continue
            resolved = path.resolve()
            if resolved not in seen:
                seen.add(resolved)
                files.append(path)
            continue
        if path.is_dir():
            for yaml_path in sorted(path.rglob("*.yaml"), key=lambda item: str(item)):
                resolved = yaml_path.resolve()
                if resolved not in seen:
                    seen.add(resolved)
                    files.append(yaml_path)
            continue
        issues.append(Issue(display_path, "error", "INPUT_UNSUPPORTED", "输入路径必须是 .yaml 文件或目录"))
    return files, issues


def load_yaml(path: Path) -> tuple[dict[str, Any] | None, Issue | None]:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    except yaml.YAMLError as exc:
        return None, Issue(
            str(path),
            "error",
            "YAML_PARSE_ERROR",
            f"YAML 解析失败: {exc}。如果长文本包含冒号、换行、命令或列表式说明，请优先使用 YAML 块标量 |。",
        )
    except OSError as exc:
        return None, Issue(str(path), "error", "INPUT_READ_ERROR", f"读取失败: {exc}")
    if not isinstance(data, dict):
        return None, Issue(str(path), "error", "YAML_TYPE_ERROR", "YAML 顶层结构必须是映射对象")
    return data, None


def infer_object_type(path: Path, data: dict[str, Any]) -> str | None:
    yaml_type = data.get("type")
    if yaml_type in OBJECT_TYPES:
        return yaml_type
    name = path.name
    if name.startswith("intent-"):
        return "intent"
    if name.startswith("task-"):
        return "task"
    if name.startswith("adr-"):
        return "adr"
    if name.startswith("pitfall-"):
        return "pitfall"
    if name.startswith("memo-"):
        return "memo"
    return None


def validate_long_text_block_scalar(path: Path, data: dict[str, Any], object_type: str) -> list[Issue]:
    """12-工作模型字段内容格式规范 §6.2：长文本字段含冒号/换行但未用 YAML 块标量时报 warning。"""
    issues = []
    fields = LONG_TEXT_FIELDS.get(object_type, set())
    # 读取原始 YAML 文本，检查字段是否使用了块标量 | 或 >
    try:
        raw_text = path.read_text(encoding="utf-8")
    except OSError:
        return issues
    for field in sorted(fields):
        value = data.get(field)
        if not isinstance(value, str) or not value:
            continue
        # 只对包含换行或冒号的字段检查
        if "\n" not in value and ": " not in value:
            continue
        # 检查原始文本中该字段是否使用了块标量
        # 匹配 field: | 或 field: > 或 field: |+ 等
        block_scalar_pattern = re.compile(rf"^{re.escape(field)}:\s*[|>]", re.MULTILINE)
        if block_scalar_pattern.search(raw_text):
            continue  # 已使用块标量，不报
        issues.append(Issue(
            str(path), "warning", "LONG_TEXT_NOT_BLOCK_SCALAR",
            f"字段 {field} 包含换行或冒号，建议使用 YAML 块标量 | 书写",
            field=field,
            suggestion=f'将 {field} 改为块标量写法，如 {field}: |',
        ))
    return issues


def validate_path_fields_exist(path: Path, data: dict[str, Any], object_type: str) -> list[Issue]:
    """12-工作模型字段内容格式规范 §6.1：路径引用字段中的相对路径不存在时报 error。"""
    issues = []
    project_root = infer_project_root(path)
    for field in sorted(PATH_FIELDS):
        items = data.get(field)
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, str):
                continue
            if item.startswith("http://") or item.startswith("https://"):
                continue  # 外部链接不校验
            # 跳过明显不是路径的描述性文本（含中文括号、中文标点等）
            if re.search(r"[（）\(\)「」【】]", item):
                continue
            # 只校验看起来像文件路径的字符串（含 / 或以 . 开头或含扩展名）
            if "/" not in item and not item.startswith(".") and "." not in item.split("/")[-1]:
                continue
            path_part = item.split(" §", 1)[0].strip()
            resolved = project_root / path_part
            if not resolved.exists():
                level = "warning" if field == "related_rules" else "error"
                issues.append(Issue(
                    str(path), level, "PATH_NOT_FOUND",
                    f"字段 {field} 中引用的路径不存在: {item}",
                    field=field,
                ))
    return issues


def infer_project_root(path: Path) -> Path:
    resolved = path.resolve()
    parts = resolved.parts
    if "ldvh-base" in parts:
        index = parts.index("ldvh-base")
        if index > 0:
            return Path(*parts[:index])
    return resolved.parent


def resolve_fact_path(path: Path, raw_value: str) -> Path:
    value_path = Path(raw_value).expanduser()
    if value_path.is_absolute():
        return value_path
    return infer_project_root(path) / value_path


def validate_path_value(path: Path, field: str, raw_value: Any, *, required_existing: bool = True) -> list[Issue]:
    if is_empty(raw_value):
        return []
    if not isinstance(raw_value, str):
        return [Issue(str(path), "error", "INVALID_PATH_FIELD", f"字段必须是路径字符串: {field}", field=field)]
    resolved = resolve_fact_path(path, raw_value)
    if required_existing and not resolved.exists():
        return [Issue(str(path), "error", "PATH_NOT_FOUND", f"字段 {field} 指向的路径不存在: {raw_value}", field=field)]
    return []


def validate_enum_field(path: Path, data: dict[str, Any], field: str, allowed_values: set[str], *, level: str = "error") -> list[Issue]:
    value = data.get(field)
    if value is None:
        return []
    if value not in allowed_values:
        valid_values = ", ".join(sorted(allowed_values))
        code = f"INVALID_{field.upper()}"
        return [Issue(str(path), level, code, f"{field} 必须是以下值之一: {valid_values}", field=field)]
    return []


def validate_id_list_format(path: Path, data: dict[str, Any], field: str, object_type: str) -> list[Issue]:
    items = data.get(field)
    if not isinstance(items, list):
        return []
    issues = []
    pattern = ID_PATTERNS[object_type]
    for item in items:
        if not isinstance(item, str) or not pattern.match(item):
            issues.append(Issue(
                str(path),
                "error",
                "INVALID_OBJECT_REFERENCE",
                f"{field} 中必须使用 {object_type}-{{NNNN}} 格式的对象 ID: {item}",
                field=field,
            ))
    return issues


def validate_any_object_id_list_format(path: Path, data: dict[str, Any], field: str) -> list[Issue]:
    items = data.get(field)
    if not isinstance(items, list):
        return []
    issues = []
    legacy_object_id_pattern = re.compile(r"^[a-z]+-\d{4}$")
    for item in items:
        if not isinstance(item, str) or not legacy_object_id_pattern.match(item):
            issues.append(Issue(
                str(path),
                "error",
                "INVALID_OBJECT_REFERENCE",
                f"{field} 中必须使用已知工作对象 ID 格式: {item}",
                field=field,
            ))
    return issues


def validate_dangerous_html(path: Path, data: dict[str, Any], object_type: str) -> list[Issue]:
    """12-工作模型字段内容格式规范 §6.1：长文本字段包含危险 HTML 标签时报 error。"""
    issues = []
    fields = LONG_TEXT_FIELDS.get(object_type, set())
    for field in sorted(fields):
        value = data.get(field)
        if not isinstance(value, str) or not value:
            continue
        for pattern in DANGEROUS_HTML_PATTERNS:
            if pattern.search(value):
                issues.append(Issue(
                    str(path), "error", "DANGEROUS_HTML",
                    f"字段 {field} 包含危险 HTML 内容（script/iframe/事件处理器），请移除",
                    field=field,
                ))
                break  # 每个字段只报一次
    return issues


def validate_evidence_format(path: Path, data: dict[str, Any], object_type: str) -> list[Issue]:
    """12-工作模型字段内容格式规范 §6.2：Evidence 字段非空但缺少验证结果或结论结构时报 warning。"""
    issues = []
    for field in sorted(EVIDENCE_FIELDS):
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            continue
        has_result = bool(re.search(r"##\s*验证结果|##\s*结果|##\s*Result", value))
        has_conclusion = bool(re.search(r"##\s*结论|##\s*Conclusion", value))
        if not (has_result or has_conclusion):
            issues.append(Issue(
                str(path), "warning", "EVIDENCE_FORMAT_HINT",
                f"字段 {field} 建议包含验证结果（## 验证结果）和结论（## 结论）结构",
                field=field,
            ))
    return issues


def validate_common(path: Path, data: dict[str, Any], object_type: str) -> list[Issue]:
    issues = []
    display_path = str(path)
    if not FILENAME_PATTERNS[object_type].match(path.name):
        issues.append(Issue(display_path, "error", "INVALID_FILENAME", f"文件名不符合 {object_type} 命名规则"))
    object_id = data.get("id")
    if not isinstance(object_id, str) or not ID_PATTERNS[object_type].match(object_id):
        issues.append(Issue(display_path, "error", "INVALID_ID", f"id 必须匹配 {ID_PATTERNS[object_type].pattern}"))
    yaml_type = data.get("type")
    if yaml_type != object_type:
        issues.append(Issue(display_path, "error", "INVALID_TYPE", f"type 必须是 {object_type}"))
    status = data.get("status")
    if status not in VALID_STATUSES[object_type]:
        valid_values = ", ".join(sorted(VALID_STATUSES[object_type]))
        issues.append(Issue(display_path, "error", "INVALID_STATUS", f"status 必须是以下值之一: {valid_values}"))
    for field in REQUIRED_FIELDS[object_type]:
        if is_empty(data.get(field)):
            issues.append(Issue(display_path, "error", "MISSING_REQUIRED_FIELD", f"缺少必填字段或字段为空: {field}"))
    for field in sorted(LIST_FIELDS[object_type]):
        if field in data and not isinstance(data[field], list):
            issues.append(Issue(display_path, "error", "INVALID_LIST_FIELD", f"字段必须是 list: {field}"))
    # 12-工作模型字段内容格式规范：长文本字段 YAML 块标量提示
    issues.extend(validate_long_text_block_scalar(path, data, object_type))
    # 12-工作模型字段内容格式规范：路径引用字段存在性校验
    issues.extend(validate_path_fields_exist(path, data, object_type))
    # 12-工作模型字段内容格式规范：危险 HTML 拦截
    issues.extend(validate_dangerous_html(path, data, object_type))
    # 12-工作模型字段内容格式规范：Evidence 字段格式提示
    issues.extend(validate_evidence_format(path, data, object_type))
    return issues


def validate_intent(path: Path, data: dict[str, Any]) -> list[Issue]:
    return validate_common(path, data, "intent")


def validate_adr(path: Path, data: dict[str, Any]) -> list[Issue]:
    return validate_common(path, data, "adr")




def find_task_by_id(tasks_dir: Path, task_id: str) -> tuple[Path | None, dict[str, Any] | None, Issue | None]:
    matches = sorted(tasks_dir.glob(f"{task_id}-*.yaml"))
    if not matches:
        return None, None, None
    task_path = matches[0]
    task_data, load_issue = load_yaml(task_path)
    return task_path, task_data, load_issue


def validate_task_id_list(path: Path, field: str, value: Any) -> list[Issue]:
    issues = []
    if field not in value:
        return issues
    items = value.get(field)
    if not isinstance(items, list):
        return issues
    for item in items:
        if not isinstance(item, str) or not ID_PATTERNS["task"].match(item):
            issues.append(Issue(str(path), "error", "INVALID_TASK_REFERENCE", f"{field} 中必须使用 task-{{NNNN}} 格式的 Task ID: {item}", field=field))
    return issues


def validate_task(path: Path, data: dict[str, Any]) -> list[Issue]:
    issues = validate_common(path, data, "task")
    task_id = data.get("id")
    tasks_dir = path.parent
    # deliverables 元素类型校验
    deliverables = data.get("deliverables")
    if isinstance(deliverables, list):
        for i, item in enumerate(deliverables):
            if not isinstance(item, str):
                issues.append(Issue(str(path), "error", "INVALID_DELIVERABLES_ELEMENT", f"deliverables 中每个元素必须是字符串，第 {i + 1} 项类型为 {type(item).__name__}", field="deliverables"))
    issues.extend(validate_task_id_list(path, "blocked_by", data))
    if data.get("status") == "closed":
        for field in ["closed_at", "closure_evidence"]:
            if is_empty(data.get(field)):
                issues.append(Issue(str(path), "error", "MISSING_CLOSURE_FIELD", f"closed 状态必须提供非空字段: {field}"))
    # acceptance 检查列表格式校验
    acceptance_text = data.get("acceptance")
    if acceptance_text and isinstance(acceptance_text, str):
        unchecked_items = re.findall(r"^- \[ \]", acceptance_text, re.MULTILINE)
        checked_items = re.findall(r"^- \[x\]", acceptance_text, re.MULTILINE)
        if not unchecked_items and not checked_items:
            issues.append(Issue(str(path), "error", "ACCEPTANCE_NOT_CHECKLIST",
                "acceptance 字段应使用检查列表格式（- [ ] / - [x]），每项为可独立验证的原子条件"))
    elif not acceptance_text:
        issues.append(Issue(str(path), "error", "MISSING_REQUIRED_FIELD", "acceptance 字段为空"))
    blocked_by = data.get("blocked_by", [])
    if isinstance(blocked_by, list):
        for blocker_id in blocked_by:
            if not isinstance(blocker_id, str) or not ID_PATTERNS["task"].match(blocker_id):
                continue
            if blocker_id == task_id:
                issues.append(Issue(str(path), "error", "SELF_BLOCKED_TASK", "blocked_by 不得引用当前 Task 自身", field="blocked_by"))
                continue
            blocker_path, blocker_data, load_issue = find_task_by_id(tasks_dir, blocker_id)
            if load_issue:
                issues.append(load_issue)
                continue
            if blocker_path is None or blocker_data is None:
                issues.append(Issue(str(path), "error", "BLOCKED_BY_NOT_FOUND", f"blocked_by 引用的 Task 不存在: {blocker_id}", field="blocked_by"))
                continue
            if blocker_data.get("status") != "closed" and data.get("status") in {"executing", "verifying", "review_needed", "closed"}:
                issues.append(Issue(str(path), "error", "BLOCKED_BY_NOT_CLOSED", f"前置 Task 未关闭，当前 Task 不得执行或关闭: {blocker_id}", field="blocked_by"))
    return issues


VALID_SEVERITY = {"low", "medium", "high", "critical"}
VALID_REPEATABILITY = {"unknown", "once", "recurring"}
VALID_MEMO_CATEGORIES = {"discovery", "reminder", "question", "gap", "preference"}
VALID_MEMO_PRIORITIES = {"low", "medium", "high"}

ID_LIST_FIELDS = {
    "related_intents": "intent",
    "related_tasks": "task",
    "related_adrs": "adr",
    "related_memos": "memo",
    "related_pitfalls": "pitfall",
    "source_tasks": "task",
    "source_memos": "memo",
}


def validate_pitfall(path: Path, data: dict[str, Any]) -> list[Issue]:
    issues = validate_common(path, data, "pitfall")
    issues.extend(validate_enum_field(path, data, "severity", VALID_SEVERITY))
    issues.extend(validate_enum_field(path, data, "repeatability", VALID_REPEATABILITY))
    for field, target_type in ID_LIST_FIELDS.items():
        issues.extend(validate_id_list_format(path, data, field, target_type))
    issues.extend(validate_any_object_id_list_format(path, data, "source_objects"))
    issues.extend(validate_any_object_id_list_format(path, data, "related_objects"))
    if data.get("status") == "superseded" and is_empty(data.get("superseded_by")):
        issues.append(Issue(str(path), "error", "MISSING_SUPERSEDED_BY", "superseded 状态必须提供非空字段: superseded_by", field="superseded_by"))
    if data.get("status") == "archived" and is_empty(data.get("archive_reason")) and is_empty(data.get("superseded_by")):
        issues.append(Issue(str(path), "error", "MISSING_ARCHIVE_REASON", "archived 状态未被替代时必须提供归档原因: archive_reason", field="archive_reason"))
    return issues


def validate_memo(path: Path, data: dict[str, Any]) -> list[Issue]:
    issues = validate_common(path, data, "memo")
    category = data.get("category")
    if category is not None and category not in VALID_MEMO_CATEGORIES:
        valid_values = ", ".join(sorted(VALID_MEMO_CATEGORIES))
        issues.append(Issue(str(path), "error", "INVALID_CATEGORY", f"category 必须是以下值之一: {valid_values}"))
    priority = data.get("priority")
    if priority is not None and priority not in VALID_MEMO_PRIORITIES:
        valid_values = ", ".join(sorted(VALID_MEMO_PRIORITIES))
        issues.append(Issue(str(path), "warning", "INVALID_PRIORITY", f"priority 必须是以下值之一: {valid_values}"))
    if data.get("status") == "resolved":
        for field in ["resolved_to", "resolved_at"]:
            if is_empty(data.get(field)):
                issues.append(Issue(str(path), "error", "MISSING_RESOLVED_FIELD", f"resolved 状态必须提供非空字段: {field}"))
    return issues


def validate_file(path: Path) -> tuple[list[Issue], bool]:
    data, load_issue = load_yaml(path)
    if load_issue:
        return [load_issue], True
    object_type = infer_object_type(path, data)
    if object_type is None:
        return [Issue(str(path), "error", "UNKNOWN_OBJECT_TYPE", "无法根据 YAML type 或文件名前缀识别对象类型")], True
    validators = {
        "intent": validate_intent,
        "task": validate_task,
        "adr": validate_adr,
        "pitfall": validate_pitfall,
        "memo": validate_memo,
    }
    return validators[object_type](path, data), False


def print_issues(issues: list[Issue]) -> None:
    for issue in sorted(issues, key=lambda item: (item.path, item.level, item.code, item.message)):
        print(issue.format())


def build_tool_result(target: Path, files_count: int, issues: list[Issue]) -> dict[str, Any]:
    errors = sum(1 for issue in issues if issue.level == "error")
    warnings = sum(1 for issue in issues if issue.level == "warning")
    return {
        "ok": errors == 0,
        "command": "fact_validate",
        "action": "validate",
        "target": str(target),
        "summary": {
            "files": files_count,
            "errors": errors,
            "warnings": warnings,
        },
        "issues": [issue.to_dict() for issue in issues],
        "data": {},
    }


def print_text_result(files_count: int, issues: list[Issue]) -> None:
    print_issues(issues)
    errors = sum(1 for issue in issues if issue.level == "error")
    warnings = sum(1 for issue in issues if issue.level == "warning")
    print(f"检查完成: files={files_count} errors={errors} warnings={warnings}")


def print_json_result(result: dict[str, Any]) -> None:
    print(json.dumps(result, ensure_ascii=False, indent=2))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="校验 Intent、Task 事实模型 YAML 文件")
    parser.add_argument("paths", nargs="+", help="一个或多个 .yaml 文件或目录")
    parser.add_argument("--format", choices={"text", "json"}, default="text", help="输出格式，默认 text")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    files, input_issues = collect_yaml_files(args.paths)
    issues = list(input_issues)
    has_input_parse_type_error = bool(input_issues)
    for path in files:
        file_issues, is_input_parse_type_error = validate_file(path)
        issues.extend(file_issues)
        has_input_parse_type_error = has_input_parse_type_error or is_input_parse_type_error
    error_count = sum(1 for issue in issues if issue.level == "error")
    if args.format == "json":
        print_json_result(build_tool_result(Path(",".join(args.paths)), len(files), issues))
    else:
        print_text_result(len(files), issues)
    if has_input_parse_type_error:
        return 2
    if error_count:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
