#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml


# Git 提交记录使用 Git commit records 作为事实源，不通过本 CLI 管理 YAML 文件
OBJECT_TYPES = {"workcase", "adr", "pitfall", "spark", "study"}
FILENAME_PATTERNS = {
    "workcase": re.compile(r"^workcase-\d{4}-[a-z0-9]+(?:-[a-z0-9]+)*\.yaml$"),
    "adr": re.compile(r"^adr-\d{4}-[a-z0-9]+(?:-[a-z0-9]+)*\.yaml$"),
    "pitfall": re.compile(r"^pitfall-\d{4}-[a-z0-9]+(?:-[a-z0-9]+)*\.yaml$"),
    "spark": re.compile(r"^spark-\d{4}-[a-z0-9]+(?:-[a-z0-9]+)*\.yaml$"),
    "study": re.compile(r"^study-\d{4}-[a-z0-9]+(?:-[a-z0-9]+)*\.md$"),
}
ID_PATTERNS = {
    "workcase": re.compile(r"^workcase-\d{4}$"),
    "adr": re.compile(r"^adr-\d{4}$"),
    "pitfall": re.compile(r"^pitfall-\d{4}$"),
    "spark": re.compile(r"^spark-\d{4}$"),
    "study": re.compile(r"^study-\d{4}$"),
}
WORKCASE_LEGACY_STATUSES = {"draft", "active", "review_needed"}
WORKCASE_CURRENT_STATUSES = {
    "subagents_plan_reviewing",
    "human_plan_confirming",
    "executing",
    "result_self_checking",
    "subagents_result_reviewing",
    "human_closure_confirming",
    "closed",
}
WORKCASE_STATUSES_REQUIRING_CURRENT_REVIEW_CONTRACT = WORKCASE_CURRENT_STATUSES - {"closed"}
WORKCASE_STATUSES_REQUIRING_EXECUTION_ITEMS = WORKCASE_CURRENT_STATUSES - {"closed"} | {"active", "review_needed", "closed"}
WORKCASE_STATUSES_REQUIRING_PLAN_CONFIRMATION = {
    "executing",
    "result_self_checking",
    "subagents_result_reviewing",
    "human_closure_confirming",
    "closed",
}
WORKCASE_STATUSES_REQUIRING_RESULT_SELF_CHECK = {"subagents_result_reviewing", "human_closure_confirming", "closed"}
WORKCASE_STATUSES_REQUIRING_CLOSURE_REQUEST = {"human_closure_confirming", "closed"}
WORKCASE_STATUSES_WITH_CLOSED_EXECUTION = {"result_self_checking", "subagents_result_reviewing", "human_closure_confirming", "closed", "review_needed"}
WORKCASE_CLOSURE_OUTCOMES = {"completed", "partial_completed", "cancelled", "superseded", "invalid", "degraded_accepted"}
WORKCASE_CONTROLLER_REVIEW_AGENT_NAMES = {
    "codex-main-controller",
    "codex_main_controller",
    "main-controller",
    "main_controller",
    "controller",
    "主控",
    "主控ai",
}
VALID_STATUSES = {
    "workcase": WORKCASE_CURRENT_STATUSES | WORKCASE_LEGACY_STATUSES,
    "adr": {"active", "archived", "deprecated"},
    "pitfall": {"active", "archived"},
    "spark": {"pending", "resolved", "discarded"},
    "study": {"active", "archived"},
}
VALID_SPARK_RESOLVED_TO_TYPES = {"workcase", "adr", "pitfall", "docs", "governed-projects", "other"}
REQUIRED_FIELDS = {
    "workcase": ["id", "type", "title", "goal", "status", "created", "updated", "priority", "description", "success_criteria", "source", "orchestration"],
    "adr": ["id", "type", "title", "status", "created", "updated", "date", "context", "decision", "consequences"],
    "pitfall": ["id", "type", "title", "status", "created", "updated", "symptoms", "trigger_conditions", "root_cause", "resolution", "verification", "avoidance", "applicability"],
    "spark": ["id", "type", "title", "status", "created", "updated", "description", "source", "priority"],
    "study": ["id", "type", "title", "status", "created", "updated", "summary"],
}
LIST_FIELDS = {
    "workcase": {"related_adrs", "related_sparks", "related_pitfalls", "related_docs", "related_workcases"},
    "adr": {"related_workcases", "related_adrs", "related_sparks", "related_rules"},
    "pitfall": {
        "source_objects", "related_objects", "related_rules", "tags",
        "source_sparks", "related_adrs", "related_docs",
    },
    "spark": {"evolution", "input_refs", "related_workcases", "related_adrs", "related_studies", "related_docs"},
    "study": {
        "urls", "input_refs", "related_workcases", "related_adrs", "related_sparks", "related_pitfalls", "related_docs",
    },
}
GLOBAL_REMOVED_FIELDS = {
    "related_changes": "related_changes 不再由工作对象手写维护；关联提交应由 Git 历史、文件路径、对象 ID 和提交正文自然文本派生",
    "related_" + "work" + "areas": "旧范围对象关联字段已移除；当前工作对象不得继续手写该关系字段",
}

# 05.02 工作模型字段内容与格式规范：长文本字段定义
LONG_TEXT_FIELDS = {
    "workcase": {"description", "success_criteria", "verification_evidence", "closure_evidence"},
    "adr": {"context", "decision", "consequences", "archive_reason", "deprecated_reason"},
    "pitfall": {"symptoms", "trigger_conditions", "root_cause", "resolution", "verification", "avoidance", "applicability"},
    "spark": {"description", "source_detail", "discard_reason"},
    "study": {"summary", "user_intent", "conclusion", "archive_reason"},
}

# 05.02 工作模型字段内容与格式规范：路径引用字段定义
PATH_FIELDS = {"related_docs", "related_rules", "source_docs"}

# 05.02 工作模型字段内容与格式规范：Evidence 字段定义
EVIDENCE_FIELDS_BY_TYPE = {
    "workcase": {"verification_evidence", "closure_evidence"},
    "pitfall": {"verification"},
}
EVIDENCE_REQUIRED_HEADINGS = ["验证计划", "验证命令", "验证结果", "结论"]
ADR_CONSEQUENCES_REQUIRED_HEADINGS = ["正向价值", "逆向价值", "实施成本", "风险评估", "注意事项"]
ADR_NO_REVERSE_VALUE_TEXT = "当前决策无逆向价值"
VALUE_STANDARD_REF_RE = re.compile(r"(?<![A-Za-z0-9_])V(?:[1-9]|10)(?![A-Za-z0-9_])")
PITFALL_TAG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

WORKCASE_ORCHESTRATION_MODES = {"single", "sequential", "parallel", "mixed"}
WORKCASE_EXECUTION_ITEM_MODES = {"single", "sequential", "parallel"}
WORKCASE_EXECUTION_ITEM_STATUSES = {"pending", "in_progress", "blocked", "done", "skipped"}
COMMITISH_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{6,}$")
ISO_DATETIME_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:?\d{2})?$"
)
URL_ITEM_KEYS = {"ref", "title", "summary"}
URL_REF_RE = re.compile(r"^https?://", re.IGNORECASE)
CHINESE_TEXT_RE = re.compile(r"[\u4e00-\u9fff]")
STUDY_REQUIRED_BODY_HEADINGS = ["研究问题", "输入与边界", "关键发现", "建议", "后续分流"]

# 05.02：verification 字段不应包含的风险/约束/降级标题模式
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
    if name.startswith("workcase-"):
        return "workcase"
    if name.startswith("adr-"):
        return "adr"
    if name.startswith("pitfall-"):
        return "pitfall"
    if name.startswith("spark-"):
        return "spark"
    if name.startswith("study-"):
        return "study"
    return None


def validate_long_text_block_scalar(path: Path, data: dict[str, Any], object_type: str) -> list[Issue]:
    """05.02 工作模型字段内容与格式规范：长文本字段含冒号/换行但未用 YAML 块标量时报 warning。"""
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
    """05.02 工作模型字段内容与格式规范：路径引用字段中的相对路径不存在时报 error。"""
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
            path_part = extract_checkable_path_ref(item, project_root)
            if path_part is None:
                continue
            resolved = resolve_path_ref(project_root, path_part)
            if not resolved.exists():
                level = "warning" if field == "related_rules" else "error"
                issues.append(Issue(
                    str(path), level, "PATH_NOT_FOUND",
                    f"字段 {field} 中引用的路径不存在: {item}",
                    field=field,
                ))
    return issues


def extract_checkable_path_ref(item: str, project_root: Path, *, allow_command_like: bool = True) -> str | None:
    """Return the path-like portion of a reference that should be checked on disk."""
    # 跳过明显不是纯路径的描述性文本（含括号、书名号或其他附注）。
    if re.search(r"[（）\(\)「」【】]", item):
        return None
    # 支持 `path §section` 形式，只校验路径段。
    path_part = item.split(" §", 1)[0].strip()
    if not path_part:
        return None
    # evidence_refs 可能包含命令；带空白的片段不按路径校验，避免误伤 `python3 code/...`。
    if not allow_command_like and re.search(r"\s", path_part):
        return None
    # 只校验看起来像文件或目录路径的字符串（含 /、以 . 开头或 basename 含扩展名）。
    if "/" not in path_part and not path_part.startswith(".") and "." not in path_part.split("/")[-1]:
        return None
    candidate = Path(path_part).expanduser()
    if candidate.is_absolute():
        try:
            candidate.relative_to(project_root)
        except ValueError:
            return None
    return path_part


def resolve_path_ref(project_root: Path, path_part: str) -> Path:
    candidate = Path(path_part).expanduser()
    if candidate.is_absolute():
        return candidate
    return project_root / candidate


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


def validate_urls(path: Path, data: dict[str, Any]) -> list[Issue]:
    items = data.get("urls")
    if not isinstance(items, list):
        return []
    issues = []
    for index, item in enumerate(items, start=1):
        if isinstance(item, str):
            issues.append(Issue(str(path), "error", "INVALID_URL", f"urls 第 {index} 项必须使用包含 ref 和中文 summary 的对象", field="urls"))
            continue
        if not isinstance(item, dict):
            issues.append(Issue(str(path), "error", "INVALID_URL", f"urls 第 {index} 项必须是包含 ref 和中文 summary 的对象", field="urls"))
            continue
        unknown_keys = sorted(set(item) - URL_ITEM_KEYS)
        if unknown_keys:
            issues.append(Issue(str(path), "error", "INVALID_URL", f"urls 第 {index} 项包含未定义字段: {', '.join(unknown_keys)}", field="urls"))
        ref = item.get("ref")
        if not isinstance(ref, str) or not ref.strip():
            issues.append(Issue(str(path), "error", "INVALID_URL", f"urls 第 {index} 项必须提供非空 ref", field="urls.ref"))
        elif not URL_REF_RE.match(ref.strip()):
            issues.append(Issue(str(path), "error", "INVALID_URL", f"urls 第 {index} 项的 ref 必须是 http(s) URL", field="urls.ref"))
        summary = item.get("summary")
        if not isinstance(summary, str) or not summary.strip():
            issues.append(Issue(str(path), "error", "INVALID_URL", f"urls 第 {index} 项必须提供中文 summary", field="urls.summary"))
        elif not CHINESE_TEXT_RE.search(summary):
            issues.append(Issue(str(path), "error", "INVALID_URL", f"urls 第 {index} 项的 summary 必须包含中文简介", field="urls.summary"))
        for optional_field in ("title",):
            value = item.get(optional_field)
            if value is not None and not isinstance(value, str):
                issues.append(Issue(str(path), "error", "INVALID_URL", f"urls 第 {index} 项的 {optional_field} 必须是字符串", field=f"urls.{optional_field}"))
    return issues


def validate_study_report_body_structure(path: Path, data: dict[str, Any]) -> list[Issue]:
    body = data.get("report_body")
    if not isinstance(body, str) or not body.strip():
        return []
    issues = []
    lines = body.splitlines()
    non_empty = [line.strip() for line in lines if line.strip()]
    if not non_empty or not non_empty[0].startswith("# "):
        issues.append(Issue(str(path), "error", "INVALID_STUDY_BODY_STRUCTURE", "Study 正文第一行必须是一级标题 # {title}", field="report_body"))
    else:
        h1_title = non_empty[0][2:].strip()
        expected_title = data.get("title")
        if isinstance(expected_title, str) and expected_title.strip() and h1_title != expected_title.strip():
            issues.append(Issue(str(path), "warning", "STUDY_BODY_TITLE_MISMATCH", "Study 正文一级标题建议与 frontmatter title 保持一致", field="report_body"))

    h1_count = sum(1 for line in lines if re.match(r"^#\s+", line))
    if h1_count != 1:
        issues.append(Issue(str(path), "error", "INVALID_STUDY_BODY_STRUCTURE", "Study 正文必须且只能包含一个一级标题", field="report_body"))

    h2_headings = [line[3:].strip() for line in lines if re.match(r"^##\s+", line)]
    if h2_headings != STUDY_REQUIRED_BODY_HEADINGS:
        issues.append(Issue(
            str(path),
            "error",
            "INVALID_STUDY_BODY_STRUCTURE",
            "Study 正文二级标题必须按顺序固定为: " + "、".join(STUDY_REQUIRED_BODY_HEADINGS),
            field="report_body",
        ))
    return issues


def validate_dangerous_html(path: Path, data: dict[str, Any], object_type: str) -> list[Issue]:
    """05.02 工作模型字段内容与格式规范：长文本字段包含危险 HTML 标签时报 error。"""
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
    """05.02：verification 字段包含风险/约束/降级标题时报 warning，建议迁移到 description 或 notes。"""
    issues = []
    if object_type != "pitfall":
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
    """05.02 §3.3：Evidence 字段非空但缺少四段式结构时报 warning。"""
    issues = []
    for field in sorted(EVIDENCE_FIELDS_BY_TYPE.get(object_type, set())):
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            continue
        headings = [line[3:].strip() for line in value.splitlines() if re.match(r"^##\s+", line)]
        missing_headings = [heading for heading in EVIDENCE_REQUIRED_HEADINGS if heading not in headings]
        if missing_headings:
            issues.append(Issue(
                str(path), "warning", "EVIDENCE_FORMAT_HINT",
                f"字段 {field} 建议按 05.02 四段式结构书写，缺少: {', '.join(missing_headings)}",
                field=field,
            ))
            continue
        ordered_headings = [heading for heading in headings if heading in EVIDENCE_REQUIRED_HEADINGS]
        if ordered_headings != EVIDENCE_REQUIRED_HEADINGS:
            issues.append(Issue(
                str(path), "warning", "EVIDENCE_FORMAT_ORDER",
                f"字段 {field} 的 05.02 四段式标题顺序应为: {', '.join(EVIDENCE_REQUIRED_HEADINGS)}",
                field=field,
            ))
    return issues


def validate_pitfall_tags(path: Path, data: dict[str, Any]) -> list[Issue]:
    issues = []
    tags = data.get("tags")
    if tags is None:
        return issues
    if not isinstance(tags, list):
        return issues
    for index, tag in enumerate(tags, start=1):
        if not isinstance(tag, str) or not tag.strip():
            issues.append(Issue(str(path), "error", "INVALID_PITFALL_TAG", f"tags 第 {index} 项必须是非空英文 slug 字符串", field="tags"))
            continue
        if not PITFALL_TAG_RE.match(tag):
            issues.append(Issue(str(path), "error", "INVALID_PITFALL_TAG", f"tags 第 {index} 项必须使用小写英文 slug: {tag}", field="tags"))
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
    issues.extend(validate_datetime_fields(path, data, ("created", "updated")))
    for field in sorted(LIST_FIELDS[object_type]):
        if field in data and not isinstance(data[field], list):
            issues.append(Issue(display_path, "error", "INVALID_LIST_FIELD", f"字段必须是 list: {field}"))
    for field, message in GLOBAL_REMOVED_FIELDS.items():
        if field in data:
            issues.append(Issue(display_path, "error", "REMOVED_OBJECT_FIELD", message, field=field))
    # 05.02 工作模型字段内容与格式规范：长文本字段 YAML 块标量提示
    issues.extend(validate_long_text_block_scalar(path, data, object_type))
    # 05.02 工作模型字段内容与格式规范：路径引用字段存在性校验
    issues.extend(validate_path_fields_exist(path, data, object_type))
    # 05.02 工作模型字段内容与格式规范：危险 HTML 拦截
    issues.extend(validate_dangerous_html(path, data, object_type))
    # 05.02 工作模型字段内容与格式规范：Evidence 字段格式提示
    issues.extend(validate_evidence_format(path, data, object_type))
    # 05.02：verification 字段风险/约束/降级内容迁移提示
    issues.extend(validate_verification_misplaced_content(path, data, object_type))
    return issues


def validate_datetime_fields(path: Path, data: dict[str, Any], fields: tuple[str, ...]) -> list[Issue]:
    issues = []
    for field in fields:
        value = data.get(field)
        if is_empty(value):
            continue
        if isinstance(value, datetime):
            continue
        if isinstance(value, date):
            issues.append(Issue(str(path), "error", "INVALID_DATETIME_FIELD", f"{field} 必须是 ISO 8601 时间戳，不得只写日期", field=field))
            continue
        if isinstance(value, str) and ISO_DATETIME_RE.match(value):
            continue
        issues.append(Issue(str(path), "error", "INVALID_DATETIME_FIELD", f"{field} 必须是 ISO 8601 时间戳，至少包含小时和分钟", field=field))
    return issues


def find_object_by_id(project_root: Path, object_type: str, object_id: str) -> tuple[Path | None, dict[str, Any] | None, Issue | None]:
    directory_name = {
        "workcase": "workcases",
        "adr": "adrs",
        "pitfall": "pitfalls",
        "spark": "sparks",
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


def validate_workcase(path: Path, data: dict[str, Any]) -> list[Issue]:
    issues = validate_common(path, data, "workcase")
    issues.extend(validate_datetime_fields(path, data, ("plan_confirmed_at", "closure_requested_at", "review_requested_at", "closed_at")))
    status = data.get("status")
    issues.extend(validate_enum_field(path, data, "priority", {"P0", "P1", "P2", "P3"}))
    if "importance" in data:
        issues.append(Issue(str(path), "error", "LEGACY_WORKCASE_FIELD", "WorkCase 不得继续使用旧字段 importance；请只维护 priority", field="importance"))
    if not is_empty(data.get("closure_outcome")) and data.get("closure_outcome") not in WORKCASE_CLOSURE_OUTCOMES:
        valid_outcomes = ", ".join(sorted(WORKCASE_CLOSURE_OUTCOMES))
        issues.append(Issue(str(path), "error", "INVALID_WORKCASE_CLOSURE_OUTCOME", f"closure_outcome 必须是以下值之一: {valid_outcomes}", field="closure_outcome"))
    for legacy_field in ("tasks", "completion_evidence"):
        if legacy_field in data:
            issues.append(Issue(str(path), "error", "LEGACY_WORKCASE_FIELD", f"WorkCase 不得继续使用旧字段: {legacy_field}", field=legacy_field))
    issues.extend(validate_id_list_references(path, data, "related_workcases", "workcase"))

    orchestration = data.get("orchestration")
    if not isinstance(orchestration, dict):
        issues.append(Issue(str(path), "error", "INVALID_ORCHESTRATION", "orchestration 必须是 object", field="orchestration"))
        return issues

    mode = orchestration.get("mode")
    if mode not in WORKCASE_ORCHESTRATION_MODES:
        valid_modes = ", ".join(sorted(WORKCASE_ORCHESTRATION_MODES))
        issues.append(Issue(str(path), "error", "INVALID_ORCHESTRATION_MODE", f"orchestration.mode 必须是以下值之一: {valid_modes}", field="orchestration.mode"))

    execution_items = orchestration.get("execution_items")
    if not isinstance(execution_items, list):
        issues.append(Issue(str(path), "error", "INVALID_EXECUTION_ITEMS", "orchestration.execution_items 必须是 list", field="orchestration.execution_items"))
        execution_items = []
    elif status in WORKCASE_STATUSES_REQUIRING_EXECUTION_ITEMS and not execution_items:
        issues.append(Issue(str(path), "error", "EXECUTION_ITEMS_EMPTY", f"{status} 状态下 orchestration.execution_items 不得为空", field="orchestration.execution_items"))

    seen_item_ids: set[str] = set()
    execution_item_statuses: list[str] = []
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
                issues.append(Issue(str(path), "error", "DUPLICATE_EXECUTION_ITEM_ID", f"执行项 id 在当前 WorkCase 内重复: {item_id}", field=f"{item_field}.id"))
            seen_item_ids.add(item_id)

        item_mode = item.get("mode")
        if item_mode and item_mode not in WORKCASE_EXECUTION_ITEM_MODES:
            valid_modes = ", ".join(sorted(WORKCASE_EXECUTION_ITEM_MODES))
            issues.append(Issue(str(path), "error", "INVALID_EXECUTION_ITEM_MODE", f"{item_field}.mode 必须是以下值之一: {valid_modes}", field=f"{item_field}.mode"))

        item_status = item.get("status")
        if isinstance(item_status, str):
            execution_item_statuses.append(item_status)
        if item_status and item_status not in WORKCASE_EXECUTION_ITEM_STATUSES:
            valid_statuses = ", ".join(sorted(WORKCASE_EXECUTION_ITEM_STATUSES))
            issues.append(Issue(str(path), "error", "INVALID_EXECUTION_ITEM_STATUS", f"{item_field}.status 必须是以下值之一: {valid_statuses}", field=f"{item_field}.status"))
        if status in WORKCASE_STATUSES_WITH_CLOSED_EXECUTION and item_status in {"pending", "in_progress"}:
            issues.append(Issue(str(path), "error", "EXECUTION_ITEM_OPEN_IN_REVIEW", f"{status} 状态下执行项不得仍为 {item_status}", field=f"{item_field}.status"))
        if item_status == "blocked" and is_empty(item.get("blocking_reason")):
            issues.append(Issue(str(path), "error", "MISSING_EXECUTION_ITEM_BLOCKING_REASON", "blocked 执行项必须填写 blocking_reason", field=f"{item_field}.blocking_reason"))
        if item_status in {"done", "skipped"} and is_empty(item.get("result_summary")):
            issues.append(Issue(str(path), "error", "MISSING_EXECUTION_ITEM_RESULT_SUMMARY", "done 或 skipped 执行项必须填写 result_summary", field=f"{item_field}.result_summary"))

        for list_field in ("input_refs", "evidence_refs"):
            if list_field in item and not isinstance(item[list_field], list):
                issues.append(Issue(str(path), "error", "INVALID_EXECUTION_ITEM_LIST_FIELD", f"{item_field}.{list_field} 必须是 list", field=f"{item_field}.{list_field}"))
        evidence_refs = item.get("evidence_refs")
        if isinstance(evidence_refs, list):
            issues.extend(validate_execution_item_evidence_refs(path, evidence_refs, item_field))

    if status == "executing" and execution_item_statuses and all(item_status == "pending" for item_status in execution_item_statuses):
        issues.append(Issue(
            str(path),
            "warning",
            "WORKCASE_EXECUTION_PROGRESS_NOT_RECORDED",
            "executing 状态下所有执行项仍为 pending；若已发生实质执行，应回写执行项状态、result_summary 和 evidence_refs，避免 Web 派生态势与真实进展脱节",
            field="orchestration.execution_items",
        ))

    plan_review = orchestration.get("plan_review")
    result_review = orchestration.get("result_review")
    uses_current_review_contract = (
        "plan_review" in orchestration
        or "result_review" in orchestration
        or status in WORKCASE_STATUSES_REQUIRING_CURRENT_REVIEW_CONTRACT
    )

    if uses_current_review_contract:
        if "plan_review" not in orchestration:
            issues.append(Issue(str(path), "error", "MISSING_PLAN_REVIEW", "当前 WorkCase 状态必须提供 orchestration.plan_review", field="orchestration.plan_review"))
            plan_review = {}
        elif not isinstance(plan_review, dict):
            issues.append(Issue(str(path), "error", "INVALID_PLAN_REVIEW", "orchestration.plan_review 必须是 object", field="orchestration.plan_review"))

        if "result_review" not in orchestration:
            issues.append(Issue(str(path), "error", "MISSING_RESULT_REVIEW", "当前 WorkCase 状态必须提供 orchestration.result_review", field="orchestration.result_review"))
            result_review = {}
        elif not isinstance(result_review, dict):
            issues.append(Issue(str(path), "error", "INVALID_RESULT_REVIEW", "orchestration.result_review 必须是 object", field="orchestration.result_review"))

    if isinstance(plan_review, dict):
        issues.extend(validate_workcase_review_section(path, plan_review, "orchestration.plan_review"))

    if isinstance(result_review, dict):
        issues.extend(validate_workcase_review_section(path, result_review, "orchestration.result_review", allow_self_check=True))
        result_review_items = result_review.get("review_items")
        if status == "subagents_result_reviewing" and isinstance(result_review_items, list) and not result_review_items:
            issues.append(Issue(
                str(path),
                "warning",
                "RESULT_REVIEW_NOT_STARTED",
                "subagents_result_reviewing 状态下 result_review.review_items 仍为空；应启动并记录独立结果复核子 Agent，避免完成后缺少第三方审核流程",
                field="orchestration.result_review.review_items",
            ))

    if uses_current_review_contract and status in {"human_plan_confirming", "executing", "result_self_checking", "subagents_result_reviewing", "human_closure_confirming", "closed"}:
        if not isinstance(plan_review, dict) or not isinstance(plan_review.get("controller_resolution"), dict):
            issues.append(Issue(str(path), "error", "MISSING_PLAN_REVIEW_RESOLUTION", "进入 Human 方案确认及后续状态前必须填写 plan_review.controller_resolution", field="orchestration.plan_review.controller_resolution"))

    if uses_current_review_contract and status in WORKCASE_STATUSES_REQUIRING_PLAN_CONFIRMATION:
        for field in ("plan_confirmed_at",):
            if is_empty(data.get(field)):
                issues.append(Issue(str(path), "error", "MISSING_WORKCASE_PLAN_CONFIRMATION", f"{status} 状态必须提供非空字段: {field}", field=field))
        if not isinstance(plan_review, dict) or not isinstance(plan_review.get("human_confirmation"), dict):
            issues.append(Issue(str(path), "error", "MISSING_PLAN_HUMAN_CONFIRMATION", "executing 及后续状态必须填写 plan_review.human_confirmation", field="orchestration.plan_review.human_confirmation"))
        controller_resolution = plan_review.get("controller_resolution") if isinstance(plan_review, dict) else None
        unresolved_items = controller_resolution.get("unresolved_items") if isinstance(controller_resolution, dict) else None
        if isinstance(unresolved_items, list) and unresolved_items:
            issues.append(Issue(
                str(path),
                "error",
                "UNRESOLVED_PLAN_ITEMS_AFTER_CONFIRMATION",
                "executing 及后续状态不得在 plan_review.controller_resolution.unresolved_items 中保留行动前未确认事项；必须由 Human 确认覆盖、改入执行范围、降级为后续事项或退回重审",
                field="orchestration.plan_review.controller_resolution.unresolved_items",
            ))

    if uses_current_review_contract and status in WORKCASE_STATUSES_REQUIRING_RESULT_SELF_CHECK:
        if not isinstance(result_review, dict) or not isinstance(result_review.get("controller_self_check"), dict):
            issues.append(Issue(str(path), "error", "MISSING_RESULT_SELF_CHECK", f"{status} 状态必须填写 result_review.controller_self_check", field="orchestration.result_review.controller_self_check"))
        elif status in {"subagents_result_reviewing", "human_closure_confirming", "closed"}:
            self_check_result = result_review["controller_self_check"].get("result")
            if isinstance(self_check_result, dict):
                required_changes = self_check_result.get("required_changes")
                if isinstance(required_changes, list) and required_changes:
                    issues.append(Issue(
                        str(path),
                        "error",
                        "UNRESOLVED_RESULT_SELF_CHECK_REQUIRED_CHANGES",
                        f"{status} 状态不得在 result_review.controller_self_check.result.required_changes 中保留主控自检发现的未处理必须修改项；必须先自行修复并回写证据，再提交结果复核",
                        field="orchestration.result_review.controller_self_check.result.required_changes",
                    ))
        for field in ("verification_evidence", "closure_evidence"):
            if is_empty(data.get(field)):
                issues.append(Issue(str(path), "error", "MISSING_WORKCASE_REVIEW_FIELD", f"{status} 状态必须提供非空字段: {field}", field=field))

    if uses_current_review_contract and status in {"human_closure_confirming", "closed"}:
        if not isinstance(result_review, dict) or not isinstance(result_review.get("controller_resolution"), dict):
            issues.append(Issue(str(path), "error", "MISSING_RESULT_REVIEW_RESOLUTION", f"{status} 状态必须填写 result_review.controller_resolution", field="orchestration.result_review.controller_resolution"))

    review = orchestration.get("review")
    if review is not None and not isinstance(review, dict):
        issues.append(Issue(str(path), "error", "INVALID_ORCHESTRATION_REVIEW", "orchestration.review 必须是 object", field="orchestration.review"))
    elif isinstance(review, dict):
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
                issues.append(Issue(str(path), "error", "MISSING_WORKCASE_REVIEW_FIELD", f"{status} 状态必须提供非空字段: {field}", field=field))
    if uses_current_review_contract and status in WORKCASE_STATUSES_REQUIRING_CLOSURE_REQUEST:
        if is_empty(data.get("closure_requested_at")):
            issues.append(Issue(str(path), "error", "MISSING_WORKCASE_CLOSURE_REQUESTED_AT", f"{status} 状态必须提供非空字段: closure_requested_at", field="closure_requested_at"))
    if status == "closed" and is_empty(data.get("closed_at")):
        issues.append(Issue(str(path), "error", "MISSING_WORKCASE_CLOSED_AT", "closed 状态必须提供非空字段: closed_at", field="closed_at"))
    if uses_current_review_contract and status == "closed" and is_empty(data.get("closure_outcome")):
        issues.append(Issue(str(path), "error", "MISSING_WORKCASE_CLOSURE_OUTCOME", "closed 状态必须提供非空字段: closure_outcome", field="closure_outcome"))
    issues.extend(validate_workcase_revision_history(path, data))
    return issues


def validate_workcase_review_section(path: Path, section: dict[str, Any], field_prefix: str, *, allow_self_check: bool = False) -> list[Issue]:
    issues: list[Issue] = []
    owner = section.get("orchestration_owner")
    if owner is not None and owner not in {"main_controller", "workflow"}:
        issues.append(Issue(str(path), "error", "INVALID_REVIEW_ORCHESTRATION_OWNER", f"{field_prefix}.orchestration_owner 必须是 main_controller 或 workflow", field=f"{field_prefix}.orchestration_owner"))
    workflow_ref = section.get("workflow_ref")
    if owner == "workflow" and is_empty(workflow_ref):
        issues.append(Issue(str(path), "error", "MISSING_REVIEW_WORKFLOW_REF", f"{field_prefix}.workflow_ref 在 workflow 接管时必须填写", field=f"{field_prefix}.workflow_ref"))

    review_policy = section.get("review_policy")
    if review_policy is not None and not isinstance(review_policy, dict):
        issues.append(Issue(str(path), "error", "INVALID_REVIEW_POLICY", f"{field_prefix}.review_policy 必须是 object", field=f"{field_prefix}.review_policy"))

    review_items = section.get("review_items")
    if review_items is not None and not isinstance(review_items, list):
        issues.append(Issue(str(path), "error", "INVALID_REVIEW_ITEMS", f"{field_prefix}.review_items 必须是 list", field=f"{field_prefix}.review_items"))
    elif isinstance(review_items, list):
        seen_ids: set[str] = set()
        for index, item in enumerate(review_items, start=1):
            item_prefix = f"{field_prefix}.review_items[{index}]"
            if not isinstance(item, dict):
                issues.append(Issue(str(path), "error", "INVALID_REVIEW_ITEM", f"{item_prefix} 必须是 object", field=f"{field_prefix}.review_items"))
                continue
            item_id = item.get("id")
            if isinstance(item_id, str):
                if item_id in seen_ids:
                    issues.append(Issue(str(path), "error", "DUPLICATE_REVIEW_ITEM_ID", f"审核条目 id 在当前 WorkCase 内重复: {item_id}", field=f"{item_prefix}.id"))
                seen_ids.add(item_id)
            for required_field in ("id", "role", "agent_name", "requested_at"):
                if is_empty(item.get(required_field)):
                    issues.append(Issue(str(path), "error", "MISSING_REVIEW_ITEM_FIELD", f"{item_prefix} 缺少非空字段: {required_field}", field=f"{item_prefix}.{required_field}"))
            agent_name = item.get("agent_name")
            if (
                owner == "main_controller"
                and isinstance(agent_name, str)
                and agent_name.strip().lower() in WORKCASE_CONTROLLER_REVIEW_AGENT_NAMES
            ):
                issues.append(Issue(
                    str(path),
                    "warning",
                    "WORKCASE_REVIEW_ITEM_SELF_SIGNED",
                    f"{item_prefix}.agent_name 使用主控标识，不能作为独立子 Agent / 第三方审核 Agent 的审核事实；应补充真实审核主体，或改由 workflow_ref 记录专门流程接管",
                    field=f"{item_prefix}.agent_name",
                ))
            prompt_context = item.get("prompt_context")
            if prompt_context is not None and not isinstance(prompt_context, dict):
                issues.append(Issue(str(path), "error", "INVALID_REVIEW_PROMPT_CONTEXT", f"{item_prefix}.prompt_context 必须是 object", field=f"{item_prefix}.prompt_context"))
            result = item.get("result")
            if result is not None and not isinstance(result, dict):
                issues.append(Issue(str(path), "error", "INVALID_REVIEW_RESULT", f"{item_prefix}.result 必须是 object", field=f"{item_prefix}.result"))
            elif isinstance(result, dict):
                status = result.get("status")
                if status is not None and status not in {"pass", "pass_with_followups", "fail", "needs_human_gate"}:
                    issues.append(Issue(str(path), "error", "INVALID_REVIEW_RESULT_STATUS", f"{item_prefix}.result.status 必须是 pass/pass_with_followups/fail/needs_human_gate", field=f"{item_prefix}.result.status"))
            attestation = item.get("attestation")
            if attestation is not None and not isinstance(attestation, dict):
                issues.append(Issue(str(path), "error", "INVALID_REVIEW_ATTESTATION", f"{item_prefix}.attestation 必须是 object", field=f"{item_prefix}.attestation"))

    if allow_self_check:
        self_check = section.get("controller_self_check")
        if self_check is not None and not isinstance(self_check, dict):
            issues.append(Issue(str(path), "error", "INVALID_CONTROLLER_SELF_CHECK", f"{field_prefix}.controller_self_check 必须是 object", field=f"{field_prefix}.controller_self_check"))
        elif isinstance(self_check, dict):
            self_check_result = self_check.get("result")
            result_field = f"{field_prefix}.controller_self_check.result"
            if not isinstance(self_check_result, dict):
                issues.append(Issue(str(path), "error", "MISSING_RESULT_SELF_CHECK_RESULT", f"{result_field} 必须是 object", field=result_field))
            else:
                status = self_check_result.get("status")
                if status is not None and status not in {"pass", "pass_with_followups", "fail", "needs_human_gate"}:
                    issues.append(Issue(str(path), "error", "INVALID_RESULT_SELF_CHECK_STATUS", f"{result_field}.status 必须是 pass/pass_with_followups/fail/needs_human_gate", field=f"{result_field}.status"))
                key_findings = self_check_result.get("key_findings")
                if not isinstance(key_findings, list) or not key_findings or all(is_empty(item) for item in key_findings):
                    issues.append(Issue(
                        str(path),
                        "error",
                        "MISSING_RESULT_SELF_CHECK_FINDINGS",
                        f"{result_field}.key_findings 必须是非空 list；未发现问题也必须明写未发现范围内问题",
                        field=f"{result_field}.key_findings",
                    ))
                required_changes = self_check_result.get("required_changes")
                if not isinstance(required_changes, list):
                    issues.append(Issue(
                        str(path),
                        "error",
                        "MISSING_RESULT_SELF_CHECK_REQUIRED_CHANGES",
                        f"{result_field}.required_changes 必须是 list；没有必须修改项时填写空列表",
                        field=f"{result_field}.required_changes",
                    ))
    return issues


def validate_workcase_revision_history(path: Path, data: dict[str, Any]) -> list[Issue]:
    issues: list[Issue] = []
    revision_history = data.get("revision_history")
    if revision_history is None:
        return issues
    if not isinstance(revision_history, list):
        return [Issue(str(path), "error", "INVALID_WORKCASE_REVISION_HISTORY", "revision_history 必须是 list", field="revision_history")]

    for index, item in enumerate(revision_history, start=1):
        item_field = f"revision_history[{index}]"
        if not isinstance(item, dict):
            issues.append(Issue(str(path), "error", "INVALID_WORKCASE_REVISION_HISTORY_ITEM", f"{item_field} 必须是 object", field=item_field))
            continue
        if "revised_at" in item and "at" not in item:
            issues.append(Issue(
                str(path),
                "error",
                "LEGACY_WORKCASE_REVISION_TIME_FIELD",
                f"{item_field} 必须使用 at，不得使用旧字段 revised_at",
                field=f"{item_field}.revised_at",
            ))
        for field in ("at", "from_status", "to_status", "actor", "reason", "changed_fields", "summary"):
            if is_empty(item.get(field)):
                issues.append(Issue(str(path), "error", "MISSING_WORKCASE_REVISION_FIELD", f"{item_field} 缺少非空字段: {field}", field=f"{item_field}.{field}"))
        for status_field in ("from_status", "to_status"):
            status_value = item.get(status_field)
            if isinstance(status_value, str) and status_value not in WORKCASE_CURRENT_STATUSES:
                valid_statuses = ", ".join(sorted(WORKCASE_CURRENT_STATUSES))
                issues.append(Issue(str(path), "error", "INVALID_WORKCASE_REVISION_STATUS", f"{item_field}.{status_field} 必须属于当前 WorkCase 状态: {valid_statuses}", field=f"{item_field}.{status_field}"))
        changed_fields = item.get("changed_fields")
        if changed_fields is not None and not isinstance(changed_fields, list):
            issues.append(Issue(str(path), "error", "INVALID_WORKCASE_REVISION_CHANGED_FIELDS", f"{item_field}.changed_fields 必须是 list", field=f"{item_field}.changed_fields"))
    return issues


def validate_execution_item_evidence_refs(path: Path, evidence_refs: list[Any], item_field: str) -> list[Issue]:
    """WorkCase execution item evidence_refs: only path-like refs are checked."""
    issues = []
    project_root = infer_project_root(path)
    for ref in evidence_refs:
        if not isinstance(ref, str):
            continue
        if ref.startswith("http://") or ref.startswith("https://"):
            continue
        path_part = extract_checkable_path_ref(ref, project_root, allow_command_like=False)
        if path_part is None:
            continue
        resolved = resolve_path_ref(project_root, path_part)
        if not resolved.exists():
            issues.append(Issue(
                str(path),
                "error",
                "EVIDENCE_REF_PATH_NOT_FOUND",
                f"{item_field}.evidence_refs 中引用的路径不存在: {ref}",
                field=f"{item_field}.evidence_refs",
            ))
    return issues


def validate_adr(path: Path, data: dict[str, Any]) -> list[Issue]:
    issues = validate_common(path, data, "adr")
    for removed_field in ("related_taskplans", "related_tasks", "related_objects", "superseded_by", "alternatives", "affects"):
        if removed_field in data:
            issues.append(Issue(str(path), "error", "REMOVED_OBJECT_FIELD", f"当前 ADR 不得维护旧对象关联字段: {removed_field}", field=removed_field))
    if data.get("status") == "active":
        consequences = data.get("consequences")
        headings = []
        if isinstance(consequences, str):
            headings = [line[3:].strip() for line in consequences.splitlines() if re.match(r"^##\s+", line)]
        if headings != ADR_CONSEQUENCES_REQUIRED_HEADINGS:
            issues.append(Issue(
                str(path),
                "error",
                "INVALID_ADR_CONSEQUENCES_STRUCTURE",
                "active ADR 的 consequences 必须按顺序固定为: " + "、".join(ADR_CONSEQUENCES_REQUIRED_HEADINGS),
                field="consequences",
            ))
        elif isinstance(consequences, str):
            reverse_value = extract_markdown_section(consequences, "逆向价值")
            if reverse_value.strip() != ADR_NO_REVERSE_VALUE_TEXT and not VALUE_STANDARD_REF_RE.search(reverse_value):
                issues.append(Issue(
                    str(path),
                    "error",
                    "INVALID_ADR_REVERSE_VALUE",
                    f"active ADR 的逆向价值必须引用 00 价值标准 V1-V10；无逆向价值时填写: {ADR_NO_REVERSE_VALUE_TEXT}",
                    field="consequences",
                ))
    for field, target_type in ID_LIST_FIELDS.items():
        issues.extend(validate_id_list_format(path, data, field, target_type))
    if data.get("status") == "archived" and is_empty(data.get("archive_reason")):
        issues.append(Issue(str(path), "error", "MISSING_ARCHIVE_REASON", "archived 状态必须提供归档原因: archive_reason", field="archive_reason"))
    if data.get("status") == "deprecated" and is_empty(data.get("deprecated_reason")):
        issues.append(Issue(str(path), "error", "MISSING_DEPRECATED_REASON", "deprecated 状态必须提供废弃原因: deprecated_reason", field="deprecated_reason"))
    return issues


def extract_markdown_section(value: str, heading: str) -> str:
    lines = value.splitlines()
    body: list[str] = []
    in_section = False
    for line in lines:
        match = re.match(r"^##\s+(.+?)\s*$", line)
        if match:
            if in_section:
                break
            in_section = match.group(1).strip() == heading
            continue
        if in_section:
            body.append(line)
    return "\n".join(body).strip()

VALID_PRIORITY = {"P0", "P1", "P2", "P3"}
VALID_SPARK_SOURCE = {"web", "conversation"}

ID_LIST_FIELDS = {
    "related_adrs": "adr",
    "related_sparks": "spark",
    "related_studies": "study",
    "related_pitfalls": "pitfall",
    "source_sparks": "spark",
}


def validate_pitfall(path: Path, data: dict[str, Any]) -> list[Issue]:
    issues = validate_common(path, data, "pitfall")
    issues.extend(validate_pitfall_tags(path, data))
    for removed_field in ("source_tasks", "related_taskplans", "related_tasks", "repeatability", "superseded_by"):
        if removed_field in data:
            issues.append(Issue(str(path), "error", "REMOVED_OBJECT_FIELD", f"当前 Pitfall 不得维护旧对象关联字段: {removed_field}", field=removed_field))
    if "severity" in data:
        issues.append(Issue(str(path), "error", "LEGACY_PITFALL_FIELD", "Pitfall 不得继续使用旧字段 severity；影响和后果请迁移到 symptoms、applicability、avoidance 或 notes", field="severity"))
    for field, target_type in ID_LIST_FIELDS.items():
        issues.extend(validate_id_list_format(path, data, field, target_type))
    issues.extend(validate_any_object_id_list_format(path, data, "source_objects"))
    issues.extend(validate_any_object_id_list_format(path, data, "related_objects"))
    if data.get("status") == "archived" and is_empty(data.get("archive_reason")):
        issues.append(Issue(str(path), "error", "MISSING_ARCHIVE_REASON", "archived 状态必须提供归档原因: archive_reason", field="archive_reason"))
    return issues


def validate_spark(path: Path, data: dict[str, Any]) -> list[Issue]:
    issues = validate_common(path, data, "spark")
    for removed_field in ("related_taskplans", "related_tasks"):
        if removed_field in data:
            issues.append(Issue(str(path), "error", "REMOVED_OBJECT_FIELD", f"当前 Spark 不得维护旧对象关联字段: {removed_field}", field=removed_field))
    if "category" in data:
        issues.append(Issue(str(path), "error", "LEGACY_SPARK_FIELD", "Spark 不得维护 category；请删除该字段", field="category"))
    if "importance" in data:
        issues.append(Issue(str(path), "error", "LEGACY_SPARK_FIELD", "Spark 不得继续使用旧字段 importance；请迁移为 priority", field="importance"))
    issues.extend(validate_enum_field(path, data, "source", VALID_SPARK_SOURCE))
    issues.extend(validate_enum_field(path, data, "priority", VALID_PRIORITY))
    if "evolution" in data:
        evolution = data.get("evolution")
        if not isinstance(evolution, list):
            issues.append(Issue(str(path), "error", "INVALID_EVOLUTION", "evolution 必须是 list", field="evolution"))
        else:
            for index, item in enumerate(evolution, start=1):
                if not isinstance(item, dict) or is_empty(item.get("at")) or is_empty(item.get("summary")):
                    issues.append(Issue(str(path), "error", "INVALID_EVOLUTION_ITEM", f"evolution 第 {index} 项至少需要 at 和 summary", field="evolution"))
                elif validate_datetime_fields(path, item, ("at",)):
                    issues.append(Issue(str(path), "error", "INVALID_EVOLUTION_ITEM", f"evolution 第 {index} 项的 at 必须是 ISO 8601 时间戳", field="evolution.at"))
    if data.get("status") == "resolved":
        for field in ["resolved_to", "resolved_at"]:
            if is_empty(data.get(field)):
                issues.append(Issue(str(path), "error", "MISSING_RESOLVED_FIELD", f"resolved 状态必须提供非空字段: {field}"))
        resolved_to = data.get("resolved_to")
        if not is_empty(resolved_to):
            if not isinstance(resolved_to, dict):
                issues.append(Issue(str(path), "error", "INVALID_SPARK_RESOLVED_TO", "resolved_to 必须是 {type, ref} 对象", field="resolved_to"))
            else:
                target_type = resolved_to.get("type")
                target_ref = resolved_to.get("ref")
                if is_empty(target_type) or is_empty(target_ref):
                    issues.append(Issue(str(path), "error", "INVALID_SPARK_RESOLVED_TO", "resolved_to 必须填写 type 和 ref", field="resolved_to"))
                elif target_type not in VALID_SPARK_RESOLVED_TO_TYPES:
                    valid_values = ", ".join(sorted(VALID_SPARK_RESOLVED_TO_TYPES))
                    issues.append(Issue(
                        str(path),
                        "error",
                        "INVALID_SPARK_RESOLVED_TO_TYPE",
                        f"resolved_to.type 必须是以下值之一: {valid_values}；Study 只能通过 related_studies 关联",
                        field="resolved_to.type",
                    ))
    if data.get("status") == "discarded" and is_empty(data.get("discard_reason")):
        issues.append(Issue(str(path), "error", "MISSING_DISCARD_REASON", "discarded 状态必须提供非空字段: discard_reason", field="discard_reason"))
    return issues


def validate_study(path: Path, data: dict[str, Any]) -> list[Issue]:
    issues = validate_common(path, data, "study")
    for removed_field in ("related_taskplans", "related_tasks", "related_refs", "superseded_by", "source", "source_detail", "source_docs"):
        if removed_field in data:
            issues.append(Issue(str(path), "error", "REMOVED_OBJECT_FIELD", f"当前 Study 不得维护旧对象关联字段: {removed_field}", field=removed_field))
    if is_empty(data.get("report_body")):
        issues.append(Issue(str(path), "error", "MISSING_REPORT_BODY", "Study Markdown 必须包含非空报告正文", field="report_body"))
    if data.get("status") == "archived" and is_empty(data.get("archive_reason")):
        issues.append(Issue(str(path), "error", "MISSING_ARCHIVE_REASON", "archived 状态必须提供归档原因: archive_reason", field="archive_reason"))
    issues.extend(validate_urls(path, data))
    issues.extend(validate_study_report_body_structure(path, data))
    return issues


def validate_file(path: Path) -> tuple[list[Issue], bool]:
    data, load_issue = load_yaml(path)
    if load_issue:
        return [load_issue], True
    object_type = infer_object_type(path, data)
    if object_type is None:
        return [Issue(str(path), "error", "UNKNOWN_OBJECT_TYPE", "无法根据 YAML type 或文件名前缀识别对象类型")], True
    validators = {
        "workcase": validate_workcase,
        "adr": validate_adr,
        "pitfall": validate_pitfall,
        "spark": validate_spark,
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
