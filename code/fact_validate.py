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
OBJECT_TYPES = {"workarea", "workplan", "taskplan", "task", "subtask", "adr", "pitfall", "memo", "study"}
FILENAME_PATTERNS = {
    "workarea": re.compile(r"^workarea-\d{4}-[a-z0-9]+(?:-[a-z0-9]+)*\.yaml$"),
    "workplan": re.compile(r"^workplan-\d{4}-[a-z0-9]+(?:-[a-z0-9]+)*\.yaml$"),
    "taskplan": re.compile(r"^taskplan-\d{4}-[a-z0-9]+(?:-[a-z0-9]+)*\.yaml$"),
    "task": re.compile(r"^task-\d{4}-[a-z0-9]+(?:-[a-z0-9]+)*\.yaml$"),
    "subtask": re.compile(r"^subtask-\d{4}-[a-z0-9]+(?:-[a-z0-9]+)*\.yaml$"),
    "adr": re.compile(r"^adr-\d{4}-[a-z0-9]+(?:-[a-z0-9]+)*\.yaml$"),
    "pitfall": re.compile(r"^pitfall-\d{4}-[a-z0-9]+(?:-[a-z0-9]+)*\.yaml$"),
    "memo": re.compile(r"^memo-\d{4}-[a-z0-9]+(?:-[a-z0-9]+)*\.yaml$"),
    "study": re.compile(r"^study-\d{4}-[a-z0-9]+(?:-[a-z0-9]+)*\.md$"),
}
ID_PATTERNS = {
    "workarea": re.compile(r"^workarea-\d{4}$"),
    "workplan": re.compile(r"^workplan-\d{4}$"),
    "taskplan": re.compile(r"^taskplan-\d{4}$"),
    "task": re.compile(r"^task-\d{4}$"),
    "subtask": re.compile(r"^subtask-\d{4}$"),
    "adr": re.compile(r"^adr-\d{4}$"),
    "pitfall": re.compile(r"^pitfall-\d{4}$"),
    "memo": re.compile(r"^memo-\d{4}$"),
    "study": re.compile(r"^study-\d{4}$"),
}
VALID_STATUSES = {
    "workarea": {"active", "archived"},
    "workplan": {"draft", "active", "review_needed", "closed"},
    "taskplan": {"draft", "active", "review_needed", "closed"},
    "task": {"planned", "executing", "verifying", "review_needed", "closed"},
    "subtask": {"planned", "executing", "verifying", "review_needed", "closed"},
    "adr": {"proposed", "accepted", "rejected", "deprecated", "superseded"},
    "pitfall": {"draft", "active", "superseded", "archived"},
    "memo": {"pending", "resolved", "discarded"},
    "study": {"draft", "active", "superseded", "archived"},
}
REQUIRED_FIELDS = {
    "workarea": ["id", "type", "title", "status", "created", "updated", "description", "source"],
    "workplan": ["id", "type", "title", "status", "created", "updated", "workarea", "priority", "description", "success_criteria", "source", "orchestration"],
    "taskplan": ["id", "type", "title", "status", "created", "updated", "workarea", "priority", "description", "success_criteria", "source", "tasks"],
    "task": ["id", "type", "title", "status", "created", "updated", "taskplan", "description", "source", "acceptance"],
    "subtask": ["id", "type", "title", "status", "created", "updated", "task", "description", "source", "acceptance"],
    "adr": ["id", "type", "title", "status", "created", "updated", "context", "decision", "consequences"],
    "pitfall": ["id", "type", "title", "status", "created", "updated", "symptoms", "trigger_conditions", "root_cause", "resolution", "verification", "avoidance", "applicability"],
    "memo": ["id", "type", "title", "status", "created", "updated", "description", "source", "priority"],
    "study": ["id", "type", "title", "status", "created", "updated", "summary", "source"],
}
LIST_FIELDS = {
    "workarea": {"related_adrs", "related_memos", "related_pitfalls", "related_docs", "workplans", "taskplans"},
    "workplan": {"related_adrs", "related_memos", "related_pitfalls", "related_docs", "related_workplans", "related_changes"},
    "taskplan": {"tasks", "related_adrs", "related_memos", "related_pitfalls", "related_docs"},
    "task": {"related_adrs", "blocked_by", "related_docs", "affected_docs", "deliverables"},
    "subtask": {"blocked_by"},
    "adr": {
        "affects", "related_workareas", "related_taskplans", "related_tasks",
        "related_adrs", "related_memos", "related_changes", "related_rules",
    },
    "pitfall": {
        "source_objects", "related_objects", "related_rules", "tags",
        "source_tasks", "source_memos", "related_workareas", "related_taskplans", "related_adrs",
        "related_changes", "related_docs",
    },
    "memo": {"evolution", "related_workareas", "related_workplans", "related_adrs", "related_studies", "related_docs"},
    "study": {
        "source_docs", "related_workareas", "related_workplans", "related_adrs",
        "related_memos", "related_pitfalls", "related_docs",
    },
}

# 12-工作模型字段内容格式规范：长文本字段定义
LONG_TEXT_FIELDS = {
    "workarea": {"description", "scope", "constraints", "archive_reason"},
    "workplan": {"description", "success_criteria", "verification_evidence", "closure_evidence"},
    "taskplan": {"description", "success_criteria", "completion_evidence"},
    "task": {"description", "acceptance", "verification", "closure_evidence"},
    "subtask": {"description", "acceptance", "verification", "closure_evidence"},
    "adr": {"context", "decision", "consequences"},
    "pitfall": {"symptoms", "trigger_conditions", "root_cause", "resolution", "verification", "avoidance", "applicability"},
    "memo": {"description", "source_detail", "discard_reason"},
    "study": {"summary", "source_detail", "conclusion", "archive_reason"},
}

# 12-工作模型字段内容格式规范：路径引用字段定义
PATH_FIELDS = {"related_docs", "deliverables", "affected_docs", "related_rules", "source_docs"}
LEGACY_REMOVED_SPEC_PATHS = {
    "specs/21-TaskPlan-任务计划.md",
    "specs/22-Task-任务.md",
    "specs/23-SubTask-子任务.md",
}

# 12-工作模型字段内容格式规范：Evidence 字段定义
EVIDENCE_FIELDS = {"verification", "verification_evidence", "closure_evidence"}

WORKPLAN_ORCHESTRATION_MODES = {"single", "sequential", "parallel", "mixed"}
WORKPLAN_EXECUTION_ITEM_MODES = {"single", "sequential", "parallel"}
WORKPLAN_EXECUTION_ITEM_STATUSES = {"pending", "in_progress", "blocked", "done", "skipped"}
COMMITISH_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{6,}$")

# 05.01 §3.5.2：verification 字段不应包含的风险/约束/降级标题模式
VERIFICATION_MISPLACED_HEADING_PATTERNS = [
    re.compile(r"^##\s*风险", re.MULTILINE),
    re.compile(r"^##\s*约束", re.MULTILINE),
    re.compile(r"^##\s*降级", re.MULTILINE),
    re.compile(r"^##\s*风险、约束和降级说明", re.MULTILINE),
]

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


def is_fact_file(path: Path) -> bool:
    if path.suffix == ".yaml":
        return True
    return path.suffix == ".md" and path.name.startswith("study-")


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
            if not is_fact_file(path):
                issues.append(Issue(display_path, "error", "INPUT_NOT_FACT_FILE", "输入文件必须是 .yaml 工作对象或 study-*.md Study 文件"))
                continue
            resolved = path.resolve()
            if resolved not in seen:
                seen.add(resolved)
                files.append(path)
            continue
        if path.is_dir():
            candidates = list(path.rglob("*.yaml")) + list(path.rglob("study-*.md"))
            for fact_path in sorted(candidates, key=lambda item: str(item)):
                resolved = fact_path.resolve()
                if resolved not in seen:
                    seen.add(resolved)
                    files.append(fact_path)
            continue
        issues.append(Issue(display_path, "error", "INPUT_UNSUPPORTED", "输入路径必须是工作对象文件或目录"))
    return files, issues


def load_study_markdown(path: Path) -> tuple[dict[str, Any] | None, Issue | None]:
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        return None, Issue(str(path), "error", "INPUT_READ_ERROR", f"读取失败: {exc}")
    if not content.startswith("---\n"):
        return None, Issue(str(path), "error", "FRONTMATTER_MISSING", "Study Markdown 必须以 YAML frontmatter 开始")
    end = content.find("\n---", 4)
    if end == -1:
        return None, Issue(str(path), "error", "FRONTMATTER_MISSING", "Study Markdown 缺少 frontmatter 结束标记")
    frontmatter = content[4:end]
    body = content[end + 4:].lstrip("\n")
    try:
        data = yaml.safe_load(frontmatter)
    except yaml.YAMLError as exc:
        return None, Issue(str(path), "error", "YAML_PARSE_ERROR", f"frontmatter 解析失败: {exc}")
    if not isinstance(data, dict):
        return None, Issue(str(path), "error", "YAML_TYPE_ERROR", "frontmatter 顶层结构必须是映射对象")
    data["report_body"] = body
    return data, None


def load_yaml(path: Path) -> tuple[dict[str, Any] | None, Issue | None]:
    if path.suffix == ".md":
        return load_study_markdown(path)
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
    if name.startswith("workarea-"):
        return "workarea"
    if name.startswith("workplan-"):
        return "workplan"
    if name.startswith("taskplan-"):
        return "taskplan"
    if name.startswith("task-"):
        return "task"
    if name.startswith("subtask-"):
        return "subtask"
    if name.startswith("adr-"):
        return "adr"
    if name.startswith("pitfall-"):
        return "pitfall"
    if name.startswith("memo-"):
        return "memo"
    if name.startswith("study-"):
        return "study"
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
                level = "warning" if field == "related_rules" or path_part in LEGACY_REMOVED_SPEC_PATHS else "error"
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


def validate_id_list_references(path: Path, data: dict[str, Any], field: str, object_type: str) -> list[Issue]:
    issues = validate_id_list_format(path, data, field, object_type)
    items = data.get(field)
    if not isinstance(items, list):
        return issues

    project_root = infer_project_root(path)
    for item in items:
        if not isinstance(item, str) or not ID_PATTERNS[object_type].match(item):
            continue
        ref_path, ref_data, load_issue = find_object_by_id(project_root, object_type, item)
        if load_issue:
            issues.append(load_issue)
        elif ref_path is None or ref_data is None:
            issues.append(Issue(str(path), "error", "OBJECT_REFERENCE_NOT_FOUND", f"{field} 引用的 {object_type} 不存在: {item}", field=field))
    return issues


def validate_any_object_id_list_format(path: Path, data: dict[str, Any], field: str) -> list[Issue]:
    items = data.get(field)
    if not isinstance(items, list):
        return []
    issues = []
    allowed_prefixes = set(ID_PATTERNS)
    for item in items:
        if not isinstance(item, str):
            issues.append(Issue(
                str(path),
                "error",
                "INVALID_OBJECT_REFERENCE",
                f"{field} 中必须使用已知工作对象 ID 格式: {item}",
                field=field,
            ))
            continue
        prefix = item.split("-", 1)[0]
        pattern = ID_PATTERNS.get(prefix)
        if prefix not in allowed_prefixes or pattern is None or not pattern.match(item):
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


def validate_verification_misplaced_content(path: Path, data: dict[str, Any], object_type: str) -> list[Issue]:
    """05.01 §3.5.2：verification 字段包含风险/约束/降级标题时报 warning，建议迁移到 description 或 notes。"""
    issues = []
    if object_type not in ("task", "subtask", "pitfall"):
        return issues
    value = data.get("verification")
    if not isinstance(value, str) or not value.strip():
        return issues
    for pattern in VERIFICATION_MISPLACED_HEADING_PATTERNS:
        if pattern.search(value):
            issues.append(Issue(
                str(path), "warning", "VERIFICATION_MISPLACED_CONTENT",
                "verification 字段不应包含风险、约束或降级说明，建议迁移到 description 或 notes 字段",
                field="verification",
                suggestion="将风险、约束、降级内容从 verification 迁移到 description 或 notes",
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
    # 05.01 §3.5.2：verification 字段风险/约束/降级内容迁移提示
    issues.extend(validate_verification_misplaced_content(path, data, object_type))
    return issues


def find_object_by_id(project_root: Path, object_type: str, object_id: str) -> tuple[Path | None, dict[str, Any] | None, Issue | None]:
    directory_name = {
        "workarea": "workareas",
        "workplan": "workplans",
        "taskplan": "taskplans",
        "task": "tasks",
        "subtask": "subtasks",
        "adr": "adrs",
        "pitfall": "pitfalls",
        "memo": "memos",
        "study": "studies",
    }.get(object_type)
    if directory_name is None:
        return None, None, None
    directory = project_root / "ldvh-base" / directory_name
    suffix = ".md" if object_type == "study" else ".yaml"
    matches = sorted(directory.glob(f"{object_id}-*{suffix}"))
    if not matches:
        return None, None, None
    object_path = matches[0]
    object_data, load_issue = load_yaml(object_path)
    return object_path, object_data, load_issue


def validate_single_id_reference(path: Path, data: dict[str, Any], field: str, object_type: str) -> list[Issue]:
    value = data.get(field)
    if is_empty(value):
        return []
    if not isinstance(value, str) or not ID_PATTERNS[object_type].match(value):
        return [Issue(str(path), "error", "INVALID_OBJECT_REFERENCE", f"{field} 必须使用 {object_type}-{{NNNN}} 格式的对象 ID: {value}", field=field)]
    project_root = infer_project_root(path)
    ref_path, ref_data, load_issue = find_object_by_id(project_root, object_type, value)
    if load_issue:
        return [load_issue]
    if ref_path is None or ref_data is None:
        return [Issue(str(path), "error", "OBJECT_REFERENCE_NOT_FOUND", f"{field} 引用的 {object_type} 不存在: {value}", field=field)]
    return []


def validate_workarea(path: Path, data: dict[str, Any]) -> list[Issue]:
    issues = validate_common(path, data, "workarea")
    project_root = infer_project_root(path)
    workarea_id = data.get("id")
    workplans = data.get("workplans")
    if isinstance(workplans, list) and isinstance(workarea_id, str):
        for workplan_id in workplans:
            if not isinstance(workplan_id, str) or not ID_PATTERNS["workplan"].match(workplan_id):
                issues.append(Issue(str(path), "error", "INVALID_WORKPLAN_REFERENCE", f"workplans 中必须使用 workplan-{{NNNN}} 格式的 WorkPlan ID: {workplan_id}", field="workplans"))
                continue
            workplan_path, workplan_data, load_issue = find_object_by_id(project_root, "workplan", workplan_id)
            if load_issue:
                issues.append(load_issue)
                continue
            if workplan_path is None or workplan_data is None:
                issues.append(Issue(str(path), "error", "WORKPLAN_NOT_FOUND", f"workplans 引用的 WorkPlan 不存在: {workplan_id}", field="workplans"))
                continue
            if workplan_data.get("workarea") != workarea_id:
                issues.append(Issue(str(path), "error", "WORKAREA_BACKREF_MISMATCH", f"WorkPlan 未通过 workarea 指回当前工作域: {workplan_id}", field="workplans"))
    taskplans = data.get("taskplans")
    if isinstance(taskplans, list) and isinstance(workarea_id, str):
        issues.append(Issue(str(path), "warning", "LEGACY_WORKAREA_FIELD", "WorkArea 的 taskplans 字段已废弃；请使用 workplans", field="taskplans"))
        for taskplan_id in taskplans:
            if not isinstance(taskplan_id, str) or not ID_PATTERNS["taskplan"].match(taskplan_id):
                issues.append(Issue(str(path), "error", "INVALID_TASKPLAN_REFERENCE", f"taskplans 中必须使用 taskplan-{{NNNN}} 格式的 TaskPlan ID: {taskplan_id}", field="taskplans"))
                continue
            taskplan_path, taskplan_data, load_issue = find_object_by_id(project_root, "taskplan", taskplan_id)
            if load_issue:
                issues.append(load_issue)
                continue
            if taskplan_path is None or taskplan_data is None:
                issues.append(Issue(str(path), "error", "TASKPLAN_NOT_FOUND", f"taskplans 引用的 TaskPlan 不存在: {taskplan_id}", field="taskplans"))
                continue
            if taskplan_data.get("workarea") != workarea_id:
                issues.append(Issue(str(path), "error", "WORKAREA_BACKREF_MISMATCH", f"TaskPlan 未通过 workarea 指回当前工作域: {taskplan_id}", field="taskplans"))
    if data.get("status") == "archived" and is_empty(data.get("archive_reason")):
        issues.append(Issue(str(path), "error", "MISSING_ARCHIVE_REASON", "archived 状态必须提供非空字段: archive_reason", field="archive_reason"))
    return issues


def validate_taskplan(path: Path, data: dict[str, Any]) -> list[Issue]:
    issues = validate_common(path, data, "taskplan")
    issues.extend(validate_enum_field(path, data, "priority", {"P0", "P1", "P2", "P3"}))
    if "importance" in data:
        issues.append(Issue(str(path), "error", "LEGACY_TASKPLAN_FIELD", "TaskPlan 不得继续使用旧字段 importance；请只维护 priority", field="importance"))
    issues.extend(validate_single_id_reference(path, data, "workarea", "workarea"))
    project_root = infer_project_root(path)
    taskplan_id = data.get("id")
    tasks = data.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        issues.append(Issue(str(path), "error", "TASKPLAN_TASKS_EMPTY", "tasks 必须是非空 Task ID 列表", field="tasks"))
    elif isinstance(taskplan_id, str):
        for task_id in tasks:
            if not isinstance(task_id, str) or not ID_PATTERNS["task"].match(task_id):
                issues.append(Issue(str(path), "error", "INVALID_TASK_REFERENCE", f"tasks 中必须使用 task-{{NNNN}} 格式的 Task ID: {task_id}", field="tasks"))
                continue
            task_path, task_data, load_issue = find_object_by_id(project_root, "task", task_id)
            if load_issue:
                issues.append(load_issue)
                continue
            if task_path is None or task_data is None:
                issues.append(Issue(str(path), "error", "TASK_NOT_FOUND", f"tasks 引用的 Task 不存在: {task_id}", field="tasks"))
                continue
            if task_data.get("taskplan") != taskplan_id:
                issues.append(Issue(str(path), "error", "TASKPLAN_BACKREF_MISMATCH", f"Task 未通过 taskplan 指回当前任务计划: {task_id}", field="tasks"))
            if data.get("status") == "closed" and task_data.get("status") != "closed":
                issues.append(Issue(str(path), "error", "TASKPLAN_TASK_NOT_CLOSED", f"closed 任务计划中的 Task 未关闭: {task_id}", field="tasks"))
    if data.get("status") in {"review_needed", "closed"}:
        for field in ["review_requested_at", "completion_evidence"]:
            if is_empty(data.get(field)):
                issues.append(Issue(str(path), "error", "MISSING_TASKPLAN_REVIEW_FIELD", f"{data.get('status')} 状态必须提供非空字段: {field}", field=field))
    if data.get("status") == "closed" and is_empty(data.get("closed_at")):
        issues.append(Issue(str(path), "error", "MISSING_TASKPLAN_CLOSED_AT", "closed 状态必须提供非空字段: closed_at", field="closed_at"))
    return issues


def validate_workplan(path: Path, data: dict[str, Any]) -> list[Issue]:
    issues = validate_common(path, data, "workplan")
    status = data.get("status")
    issues.extend(validate_enum_field(path, data, "priority", {"P0", "P1", "P2", "P3"}))
    if "importance" in data:
        issues.append(Issue(str(path), "error", "LEGACY_WORKPLAN_FIELD", "WorkPlan 不得继续使用旧字段 importance；请只维护 priority", field="importance"))
    for legacy_field in ("tasks", "completion_evidence"):
        if legacy_field in data:
            issues.append(Issue(str(path), "error", "LEGACY_WORKPLAN_FIELD", f"WorkPlan 不得继续使用旧字段: {legacy_field}", field=legacy_field))
    issues.extend(validate_single_id_reference(path, data, "workarea", "workarea"))
    issues.extend(validate_id_list_references(path, data, "related_workplans", "workplan"))

    related_changes = data.get("related_changes")
    if isinstance(related_changes, list):
        for item in related_changes:
            if not isinstance(item, str) or not COMMITISH_RE.match(item):
                issues.append(Issue(str(path), "error", "INVALID_RELATED_CHANGE", f"related_changes 必须使用 Git commit hash、短 hash 或可回指 commit 的引用: {item}", field="related_changes"))

    orchestration = data.get("orchestration")
    if not isinstance(orchestration, dict):
        issues.append(Issue(str(path), "error", "INVALID_ORCHESTRATION", "orchestration 必须是 object", field="orchestration"))
        return issues

    mode = orchestration.get("mode")
    if mode not in WORKPLAN_ORCHESTRATION_MODES:
        valid_modes = ", ".join(sorted(WORKPLAN_ORCHESTRATION_MODES))
        issues.append(Issue(str(path), "error", "INVALID_ORCHESTRATION_MODE", f"orchestration.mode 必须是以下值之一: {valid_modes}", field="orchestration.mode"))

    execution_items = orchestration.get("execution_items")
    if not isinstance(execution_items, list):
        issues.append(Issue(str(path), "error", "INVALID_EXECUTION_ITEMS", "orchestration.execution_items 必须是 list", field="orchestration.execution_items"))
        execution_items = []
    elif status in {"active", "review_needed", "closed"} and not execution_items:
        issues.append(Issue(str(path), "error", "EXECUTION_ITEMS_EMPTY", f"{status} 状态下 orchestration.execution_items 不得为空", field="orchestration.execution_items"))

    seen_item_ids: set[str] = set()
    for index, item in enumerate(execution_items, start=1):
        item_field = f"orchestration.execution_items[{index}]"
        if not isinstance(item, dict):
            issues.append(Issue(str(path), "error", "INVALID_EXECUTION_ITEM", f"{item_field} 必须是 object", field="orchestration.execution_items"))
            continue

        for field in ("id", "title", "role", "mode", "input_refs", "expected_output", "status"):
            if is_empty(item.get(field)):
                issues.append(Issue(str(path), "error", "MISSING_EXECUTION_ITEM_FIELD", f"{item_field} 缺少非空字段: {field}", field=f"{item_field}.{field}"))

        item_id = item.get("id")
        if isinstance(item_id, str):
            if item_id in seen_item_ids:
                issues.append(Issue(str(path), "error", "DUPLICATE_EXECUTION_ITEM_ID", f"执行项 id 在当前 WorkPlan 内重复: {item_id}", field=f"{item_field}.id"))
            seen_item_ids.add(item_id)

        item_mode = item.get("mode")
        if item_mode and item_mode not in WORKPLAN_EXECUTION_ITEM_MODES:
            valid_modes = ", ".join(sorted(WORKPLAN_EXECUTION_ITEM_MODES))
            issues.append(Issue(str(path), "error", "INVALID_EXECUTION_ITEM_MODE", f"{item_field}.mode 必须是以下值之一: {valid_modes}", field=f"{item_field}.mode"))

        item_status = item.get("status")
        if item_status and item_status not in WORKPLAN_EXECUTION_ITEM_STATUSES:
            valid_statuses = ", ".join(sorted(WORKPLAN_EXECUTION_ITEM_STATUSES))
            issues.append(Issue(str(path), "error", "INVALID_EXECUTION_ITEM_STATUS", f"{item_field}.status 必须是以下值之一: {valid_statuses}", field=f"{item_field}.status"))
        if status in {"review_needed", "closed"} and item_status in {"pending", "in_progress"}:
            issues.append(Issue(str(path), "error", "EXECUTION_ITEM_OPEN_IN_REVIEW", f"{status} 状态下执行项不得仍为 {item_status}", field=f"{item_field}.status"))
        if item_status == "blocked" and is_empty(item.get("blocking_reason")):
            issues.append(Issue(str(path), "error", "MISSING_EXECUTION_ITEM_BLOCKING_REASON", "blocked 执行项必须填写 blocking_reason", field=f"{item_field}.blocking_reason"))
        if item_status in {"done", "skipped"} and is_empty(item.get("result_summary")):
            issues.append(Issue(str(path), "error", "MISSING_EXECUTION_ITEM_RESULT_SUMMARY", "done 或 skipped 执行项必须填写 result_summary", field=f"{item_field}.result_summary"))

        for list_field in ("input_refs", "evidence_refs"):
            if list_field in item and not isinstance(item[list_field], list):
                issues.append(Issue(str(path), "error", "INVALID_EXECUTION_ITEM_LIST_FIELD", f"{item_field}.{list_field} 必须是 list", field=f"{item_field}.{list_field}"))

    review = orchestration.get("review")
    if not isinstance(review, dict):
        issues.append(Issue(str(path), "error", "INVALID_ORCHESTRATION_REVIEW", "orchestration.review 必须是 object", field="orchestration.review"))
    else:
        for field in ("controller_self_check", "human_closure_review"):
            if not isinstance(review.get(field), bool):
                issues.append(Issue(str(path), "error", "INVALID_REVIEW_BOOLEAN", f"orchestration.review.{field} 必须是 boolean", field=f"orchestration.review.{field}"))
        specialist_review = review.get("specialist_review")
        if not isinstance(specialist_review, dict):
            issues.append(Issue(str(path), "error", "INVALID_SPECIALIST_REVIEW", "orchestration.review.specialist_review 必须是 object", field="orchestration.review.specialist_review"))
        else:
            required = specialist_review.get("required")
            if not isinstance(required, bool):
                issues.append(Issue(str(path), "error", "INVALID_SPECIALIST_REVIEW_REQUIRED", "orchestration.review.specialist_review.required 必须是 boolean", field="orchestration.review.specialist_review.required"))
            if required is True:
                for field in ("role", "expected_output"):
                    if is_empty(specialist_review.get(field)):
                        issues.append(Issue(str(path), "error", "MISSING_SPECIALIST_REVIEW_FIELD", f"specialist_review.required=true 时必须填写 {field}", field=f"orchestration.review.specialist_review.{field}"))

    if status in {"review_needed", "closed"}:
        for field in ("verification_evidence", "closure_evidence", "review_requested_at"):
            if is_empty(data.get(field)):
                issues.append(Issue(str(path), "error", "MISSING_WORKPLAN_REVIEW_FIELD", f"{status} 状态必须提供非空字段: {field}", field=field))
    if status == "closed" and is_empty(data.get("closed_at")):
        issues.append(Issue(str(path), "error", "MISSING_WORKPLAN_CLOSED_AT", "closed 状态必须提供非空字段: closed_at", field="closed_at"))
    return issues


def validate_adr(path: Path, data: dict[str, Any]) -> list[Issue]:
    issues = validate_common(path, data, "adr")
    for field, target_type in ID_LIST_FIELDS.items():
        issues.extend(validate_id_list_format(path, data, field, target_type))
    issues.extend(validate_any_object_id_list_format(path, data, "related_objects"))
    return issues




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
    project_root = infer_project_root(path)
    for legacy_field in ["source_intent", "parent_task", "sub_tasks", "priority", "importance", "risk_assessment"]:
        if legacy_field in data:
            issues.append(Issue(str(path), "error", "LEGACY_TASK_FIELD", f"Task 不得继续使用旧字段: {legacy_field}；风险、约束和降级说明请迁移到 description、acceptance 或 verification", field=legacy_field))
    issues.extend(validate_single_id_reference(path, data, "taskplan", "taskplan"))
    taskplan_id = data.get("taskplan")
    if isinstance(taskplan_id, str) and ID_PATTERNS["taskplan"].match(taskplan_id) and isinstance(task_id, str):
        taskplan_path, taskplan_data, load_issue = find_object_by_id(project_root, "taskplan", taskplan_id)
        if load_issue:
            issues.append(load_issue)
        elif taskplan_path is not None and taskplan_data is not None:
            taskplan_tasks = taskplan_data.get("tasks")
            if isinstance(taskplan_tasks, list) and task_id not in taskplan_tasks:
                issues.append(Issue(str(path), "error", "TASKPLAN_MISSING_TASK", f"所属 TaskPlan 的 tasks 未包含当前 Task: {task_id}", field="taskplan"))
    # deliverables 元素类型校验
    deliverables = data.get("deliverables")
    if isinstance(deliverables, list):
        for i, item in enumerate(deliverables):
            if not isinstance(item, str):
                issues.append(Issue(str(path), "error", "INVALID_DELIVERABLES_ELEMENT", f"deliverables 中每个元素必须是字符串，第 {i + 1} 项类型为 {type(item).__name__}", field="deliverables"))
    issues.extend(validate_task_id_list(path, "blocked_by", data))
    if data.get("status") == "closed":
        for field in ["closed_at", "verification", "closure_evidence"]:
            if is_empty(data.get(field)):
                issues.append(Issue(str(path), "error", "MISSING_CLOSURE_FIELD", f"closed 状态必须提供非空字段: {field}"))
        if isinstance(task_id, str):
            for subtask_path, subtask_data, load_issue in find_subtasks_for_task(project_root, task_id):
                if load_issue:
                    issues.append(load_issue)
                    continue
                if subtask_data and subtask_data.get("status") != "closed":
                    issues.append(Issue(str(path), "error", "SUBTASK_NOT_CLOSED", f"所属 SubTask 未关闭，当前 Task 不得关闭: {subtask_data.get('id', subtask_path.name)}", field="task"))
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
            blocker_path, blocker_data, load_issue = find_object_by_id(project_root, "task", blocker_id)
            if load_issue:
                issues.append(load_issue)
                continue
            if blocker_path is None or blocker_data is None:
                issues.append(Issue(str(path), "error", "BLOCKED_BY_NOT_FOUND", f"blocked_by 引用的 Task 不存在: {blocker_id}", field="blocked_by"))
                continue
            if blocker_data.get("taskplan") != taskplan_id:
                issues.append(Issue(str(path), "error", "BLOCKED_BY_TASKPLAN_MISMATCH", f"blocked_by 只能引用同一 TaskPlan 内的 Task: {blocker_id}", field="blocked_by"))
            if blocker_data.get("status") != "closed" and data.get("status") in {"executing", "verifying", "review_needed", "closed"}:
                issues.append(Issue(str(path), "error", "BLOCKED_BY_NOT_CLOSED", f"前置 Task 未关闭，当前 Task 不得执行或关闭: {blocker_id}", field="blocked_by"))
    return issues


def find_subtasks_for_task(project_root: Path, task_id: str) -> list[tuple[Path, dict[str, Any] | None, Issue | None]]:
    subtasks_dir = project_root / "ldvh-base" / "subtasks"
    if not subtasks_dir.exists():
        return []
    result = []
    for subtask_path in sorted(subtasks_dir.glob("subtask-*.yaml")):
        subtask_data, load_issue = load_yaml(subtask_path)
        if load_issue:
            result.append((subtask_path, None, load_issue))
            continue
        if subtask_data and subtask_data.get("task") == task_id:
            result.append((subtask_path, subtask_data, None))
    return result


def validate_subtask(path: Path, data: dict[str, Any]) -> list[Issue]:
    issues = validate_common(path, data, "subtask")
    subtask_id = data.get("id")
    project_root = infer_project_root(path)
    for forbidden_field in ["parent_task", "sub_tasks"]:
        if forbidden_field in data:
            issues.append(Issue(str(path), "error", "FORBIDDEN_SUBTASK_FIELD", f"SubTask 不得拥有字段: {forbidden_field}", field=forbidden_field))
    issues.extend(validate_single_id_reference(path, data, "task", "task"))
    if data.get("status") == "closed":
        for field in ["closed_at", "verification", "closure_evidence"]:
            if is_empty(data.get(field)):
                issues.append(Issue(str(path), "error", "MISSING_CLOSURE_FIELD", f"closed 状态必须提供非空字段: {field}", field=field))
    acceptance_text = data.get("acceptance")
    if acceptance_text and isinstance(acceptance_text, str):
        unchecked_items = re.findall(r"^- \[ \]", acceptance_text, re.MULTILINE)
        checked_items = re.findall(r"^- \[x\]", acceptance_text, re.MULTILINE)
        if not unchecked_items and not checked_items:
            issues.append(Issue(str(path), "error", "ACCEPTANCE_NOT_CHECKLIST",
                "acceptance 字段应使用检查列表格式（- [ ] / - [x]），每项为可独立验证的原子条件"))
    task_id = data.get("task")
    blocked_by = data.get("blocked_by", [])
    if isinstance(blocked_by, list):
        for blocker_id in blocked_by:
            if not isinstance(blocker_id, str) or not ID_PATTERNS["subtask"].match(blocker_id):
                issues.append(Issue(str(path), "error", "INVALID_SUBTASK_REFERENCE", f"blocked_by 中必须使用 subtask-{{NNNN}} 格式的 SubTask ID: {blocker_id}", field="blocked_by"))
                continue
            if blocker_id == subtask_id:
                issues.append(Issue(str(path), "error", "SELF_BLOCKED_SUBTASK", "blocked_by 不得引用当前 SubTask 自身", field="blocked_by"))
                continue
            blocker_path, blocker_data, load_issue = find_object_by_id(project_root, "subtask", blocker_id)
            if load_issue:
                issues.append(load_issue)
                continue
            if blocker_path is None or blocker_data is None:
                issues.append(Issue(str(path), "error", "BLOCKED_BY_NOT_FOUND", f"blocked_by 引用的 SubTask 不存在: {blocker_id}", field="blocked_by"))
                continue
            if blocker_data.get("task") != task_id:
                issues.append(Issue(str(path), "error", "BLOCKED_BY_TASK_MISMATCH", f"blocked_by 只能引用同一 Task 下的 SubTask: {blocker_id}", field="blocked_by"))
            if blocker_data.get("status") != "closed" and data.get("status") in {"executing", "verifying", "review_needed", "closed"}:
                issues.append(Issue(str(path), "error", "BLOCKED_BY_NOT_CLOSED", f"前置 SubTask 未关闭，当前 SubTask 不得执行或关闭: {blocker_id}", field="blocked_by"))
    return issues


VALID_REPEATABILITY = {"unknown", "once", "recurring"}
VALID_PRIORITY = {"P0", "P1", "P2", "P3"}
VALID_MEMO_SOURCE = {"web", "conversation"}
VALID_STUDY_SOURCE = {"human", "ai"}

ID_LIST_FIELDS = {
    "related_workareas": "workarea",
    "related_taskplans": "taskplan",
    "related_tasks": "task",
    "related_adrs": "adr",
    "related_memos": "memo",
    "related_studies": "study",
    "related_pitfalls": "pitfall",
    "source_tasks": "task",
    "source_memos": "memo",
}


def validate_pitfall(path: Path, data: dict[str, Any]) -> list[Issue]:
    issues = validate_common(path, data, "pitfall")
    if "severity" in data:
        issues.append(Issue(str(path), "error", "LEGACY_PITFALL_FIELD", "Pitfall 不得继续使用旧字段 severity；影响和后果请迁移到 symptoms、applicability、avoidance 或 notes", field="severity"))
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
    if "category" in data:
        issues.append(Issue(str(path), "error", "LEGACY_MEMO_FIELD", "Memo 不得维护 category；请删除该字段", field="category"))
    if "importance" in data:
        issues.append(Issue(str(path), "error", "LEGACY_MEMO_FIELD", "Memo 不得继续使用旧字段 importance；请迁移为 priority", field="importance"))
    issues.extend(validate_enum_field(path, data, "source", VALID_MEMO_SOURCE))
    issues.extend(validate_enum_field(path, data, "priority", VALID_PRIORITY))
    if "evolution" in data:
        evolution = data.get("evolution")
        if not isinstance(evolution, list):
            issues.append(Issue(str(path), "error", "INVALID_EVOLUTION", "evolution 必须是 list", field="evolution"))
        else:
            for index, item in enumerate(evolution, start=1):
                if not isinstance(item, dict) or is_empty(item.get("at")) or is_empty(item.get("summary")):
                    issues.append(Issue(str(path), "error", "INVALID_EVOLUTION_ITEM", f"evolution 第 {index} 项至少需要 at 和 summary", field="evolution"))
    if data.get("status") == "resolved":
        for field in ["resolved_to", "resolved_at"]:
            if is_empty(data.get(field)):
                issues.append(Issue(str(path), "error", "MISSING_RESOLVED_FIELD", f"resolved 状态必须提供非空字段: {field}"))
    if data.get("status") == "discarded" and is_empty(data.get("discard_reason")):
        issues.append(Issue(str(path), "error", "MISSING_DISCARD_REASON", "discarded 状态必须提供非空字段: discard_reason", field="discard_reason"))
    return issues


def validate_study(path: Path, data: dict[str, Any]) -> list[Issue]:
    issues = validate_common(path, data, "study")
    issues.extend(validate_enum_field(path, data, "source", VALID_STUDY_SOURCE))
    if is_empty(data.get("report_body")):
        issues.append(Issue(str(path), "error", "MISSING_REPORT_BODY", "Study Markdown 必须包含非空报告正文", field="report_body"))
    if data.get("status") == "superseded" and is_empty(data.get("superseded_by")):
        issues.append(Issue(str(path), "error", "MISSING_SUPERSEDED_BY", "superseded 状态必须提供非空字段: superseded_by", field="superseded_by"))
    if data.get("status") == "archived" and is_empty(data.get("archive_reason")):
        issues.append(Issue(str(path), "error", "MISSING_ARCHIVE_REASON", "archived 状态必须提供归档原因: archive_reason", field="archive_reason"))
    return issues


def validate_file(path: Path) -> tuple[list[Issue], bool]:
    data, load_issue = load_yaml(path)
    if load_issue:
        return [load_issue], True
    object_type = infer_object_type(path, data)
    if object_type is None:
        return [Issue(str(path), "error", "UNKNOWN_OBJECT_TYPE", "无法根据 YAML type 或文件名前缀识别对象类型")], True
    validators = {
        "workarea": validate_workarea,
        "workplan": validate_workplan,
        "taskplan": validate_taskplan,
        "task": validate_task,
        "subtask": validate_subtask,
        "adr": validate_adr,
        "pitfall": validate_pitfall,
        "memo": validate_memo,
        "study": validate_study,
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
    parser = argparse.ArgumentParser(description="校验 LDVH 工作对象事实模型 YAML 文件")
    parser.add_argument("paths", nargs="+", help="一个或多个 .yaml 工作对象、study-*.md 文件或目录")
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
