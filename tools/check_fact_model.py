#!/usr/bin/env python3

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


OBJECT_TYPES = {"intent", "task", "evidence", "pitfall"}
FILENAME_PATTERNS = {
    "intent": re.compile(r"^intent-\d{4}-[a-z0-9]+(?:-[a-z0-9]+)*\.yaml$"),
    "task": re.compile(r"^task-\d{4}-[a-z0-9]+(?:-[a-z0-9]+)*\.yaml$"),
    "evidence": re.compile(r"^ev-\d{4}-[a-z0-9]+(?:-[a-z0-9]+)*\.yaml$"),
    "pitfall": re.compile(r"^pitfall-\d{4}-[a-z0-9]+(?:-[a-z0-9]+)*\.yaml$"),
}
ID_PATTERNS = {
    "intent": re.compile(r"^intent-\d{4}$"),
    "task": re.compile(r"^task-\d{4}$"),
    "evidence": re.compile(r"^ev-\d{4}$"),
    "pitfall": re.compile(r"^pitfall-\d{4}$"),
}
VALID_STATUSES = {
    "intent": {"draft", "active", "completed", "closed"},
    "task": {"planned", "executing", "review_needed", "closed"},
    "evidence": {"candidate", "verified", "archived"},
    "pitfall": {"draft", "active", "superseded", "archived"},
}
REQUIRED_FIELDS = {
    "intent": ["id", "type", "title", "status", "created", "updated", "description", "success_criteria", "source"],
    "task": ["id", "type", "title", "status", "created", "updated", "description", "source", "acceptance"],
    "evidence": ["id", "type", "title", "status", "created", "updated", "evidence_type", "verification_method", "verification_result", "content"],
    "pitfall": ["id", "type", "title", "status", "created", "updated", "symptoms", "trigger_conditions", "root_cause", "resolution", "verification", "avoidance", "applicability"],
}
LIST_FIELDS = {
    "intent": {"related_tasks", "related_adrs"},
    "task": {"related_adrs", "related_evidence", "related_changes"},
    "evidence": set(),
    "pitfall": {"source_objects", "related_objects", "related_rules", "tags"},
}
VALID_EVIDENCE_TYPES = {"verification", "execution", "closure", "review"}
VALID_VERIFICATION_RESULTS = {"pass", "fail", "partial"}


@dataclass(frozen=True)
class Issue:
    path: str
    level: str
    code: str
    message: str

    def format(self) -> str:
        return f"{self.path}: [{self.level}] {self.code}: {self.message}"


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
    if name.startswith("ev-"):
        return "evidence"
    return None


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
    return issues


def validate_intent(path: Path, data: dict[str, Any]) -> list[Issue]:
    return validate_common(path, data, "intent")


def validate_task(path: Path, data: dict[str, Any]) -> list[Issue]:
    issues = validate_common(path, data, "task")
    if data.get("status") == "closed":
        for field in ["closed_at", "closure_evidence"]:
            if is_empty(data.get(field)):
                issues.append(Issue(str(path), "error", "MISSING_CLOSURE_FIELD", f"closed 状态必须提供非空字段: {field}"))
    return issues


def validate_evidence(path: Path, data: dict[str, Any]) -> list[Issue]:
    issues = validate_common(path, data, "evidence")
    evidence_type = data.get("evidence_type")
    if evidence_type not in VALID_EVIDENCE_TYPES:
        valid_values = ", ".join(sorted(VALID_EVIDENCE_TYPES))
        issues.append(Issue(str(path), "error", "INVALID_EVIDENCE_TYPE", f"evidence_type 必须是以下值之一: {valid_values}"))
    verification_result = data.get("verification_result")
    if verification_result not in VALID_VERIFICATION_RESULTS:
        valid_values = ", ".join(sorted(VALID_VERIFICATION_RESULTS))
        issues.append(Issue(str(path), "error", "INVALID_VERIFICATION_RESULT", f"verification_result 必须是以下值之一: {valid_values}"))
    if is_empty(data.get("source_task")) and is_empty(data.get("source_adr")):
        issues.append(Issue(str(path), "error", "MISSING_EVIDENCE_SOURCE", "source_task 或 source_adr 至少一个必须非空"))
    return issues


VALID_SEVERITY = {"low", "medium", "high", "critical"}
VALID_REPEATABILITY = {"always", "conditional", "rare", "once"}


def validate_pitfall(path: Path, data: dict[str, Any]) -> list[Issue]:
    issues = validate_common(path, data, "pitfall")
    severity = data.get("severity")
    if severity is not None and severity not in VALID_SEVERITY:
        valid_values = ", ".join(sorted(VALID_SEVERITY))
        issues.append(Issue(str(path), "warning", "INVALID_SEVERITY", f"severity 必须是以下值之一: {valid_values}"))
    repeatability = data.get("repeatability")
    if repeatability is not None and repeatability not in VALID_REPEATABILITY:
        valid_values = ", ".join(sorted(VALID_REPEATABILITY))
        issues.append(Issue(str(path), "warning", "INVALID_REPEATABILITY", f"repeatability 必须是以下值之一: {valid_values}"))
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
        "evidence": validate_evidence,
        "pitfall": validate_pitfall,
    }
    return validators[object_type](path, data), False


def print_issues(issues: list[Issue]) -> None:
    for issue in sorted(issues, key=lambda item: (item.path, item.level, item.code, item.message)):
        print(issue.format())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="校验 Intent、Task、Evidence 事实模型 YAML 文件")
    parser.add_argument("paths", nargs="+", help="一个或多个 .yaml 文件或目录")
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
    print_issues(issues)
    error_count = sum(1 for issue in issues if issue.level == "error")
    warning_count = sum(1 for issue in issues if issue.level == "warning")
    print(f"检查完成: files={len(files)} errors={error_count} warnings={warning_count}")
    if has_input_parse_type_error:
        return 2
    if error_count:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
