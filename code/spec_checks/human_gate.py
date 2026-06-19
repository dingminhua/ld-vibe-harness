"""Human Gate evidence structure checks for LDVH."""

import json
import re
from datetime import datetime
from pathlib import Path

import yaml

from .common import Issue, count_by, is_project_local as common_is_project_local, relative_path as common_relative_path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FORMAL_SPECS_DIR = PROJECT_ROOT / "specs"
DOCS_DIR = PROJECT_ROOT / "docs"
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
HUMAN_GATE_HEADER_RE = re.compile(r"^Human Gate\s*记录[:：]\s*$", re.IGNORECASE)
HUMAN_GATE_FIELD_RE = re.compile(r"^\s*[-*]\s*(?P<label>[^:：]+?)\s*[:：]\s*(?P<value>.*)$")
HUMAN_GATE_FILE_SUFFIXES = {".md", ".yaml", ".yml"}
HUMAN_GATE_REQUIRED_FIELDS = [
    ("时间", ["时间", "确认人/时间", "确认人和时间", "确认来源和时间", "确认人及时间", "time", "date", "confirmed_at"]),
    ("决策", ["决策", "Human 决策", "Human 选择", "确认结果", "用户选择", "decision", "result"]),
    ("范围", ["范围", "影响范围", "确认事项", "确认对象", "确认对象或确认事项", "scope"]),
    ("约束", ["约束", "确认依据", "依据", "确认上下文", "后续动作", "后续执行动作", "确认后的执行动作", "验证方式", "验证结果", "验证方式或结果", "回写位置", "残留风险", "残留风险或后续 WorkPlan", "constraints"]),
]
HUMAN_GATE_YAML_KEYS = {"human_gate", "human_gates", "human_gate_records"}


def relative_path(path):
    return common_relative_path(path, PROJECT_ROOT)


def is_project_local(path):
    return common_is_project_local(path, PROJECT_ROOT)


def default_check_paths():
    paths = []
    for path in [FORMAL_SPECS_DIR, DOCS_DIR, PROJECT_ROOT / "ldvh-base"]:
        if path.exists():
            paths.append(str(path))
    return paths


def iter_files(paths):
    files = []
    for raw_path in paths:
        path = Path(raw_path)
        if path.is_file() and path.suffix in HUMAN_GATE_FILE_SUFFIXES:
            files.append(path)
        elif path.is_dir():
            for child in path.rglob("*"):
                if child.is_file() and child.suffix in HUMAN_GATE_FILE_SUFFIXES:
                    files.append(child)
    return sorted(set(files))


def normalize_label(label):
    return str(label).strip().strip("*").strip("`").strip()


def alias_map():
    aliases = {}
    for canonical, labels in HUMAN_GATE_REQUIRED_FIELDS:
        for label in labels:
            aliases[normalize_label(label)] = canonical
    return aliases


def parse_field_line(line):
    match = HUMAN_GATE_FIELD_RE.match(line)
    if not match:
        return None
    label = normalize_label(match.group("label"))
    value = match.group("value").strip().strip("*").strip()
    return label, value


def collect_record(lines, start_index):
    block = []
    for index in range(start_index + 1, len(lines)):
        line = lines[index]
        stripped = line.strip()
        if not stripped:
            if block:
                break
            continue
        if HEADING_RE.match(line) or stripped == "---" or HUMAN_GATE_HEADER_RE.match(stripped):
            break
        if block and not stripped.startswith(("-", "*")) and not line.startswith((" ", "\t")):
            break
        block.append((index + 1, line))
    return block


def record_fields(block):
    aliases = alias_map()
    fields = {}
    field_lines = {}

    for position, (line_number, line) in enumerate(block):
        parsed = parse_field_line(line)
        if not parsed:
            continue
        label, value = parsed
        canonical = aliases.get(label)
        if not canonical:
            continue

        continuation = []
        for _, next_line in block[position + 1 :]:
            next_parsed = parse_field_line(next_line)
            if next_parsed and aliases.get(next_parsed[0]):
                break
            if next_line.strip():
                continuation.append(next_line.strip())

        text = "\n".join(item for item in [fields.get(canonical, ""), value, *continuation] if item).strip()
        fields[canonical] = text
        field_lines.setdefault(canonical, line_number)

    return fields, field_lines


def check_record_fields(path, line, fields, field_lines):
    issues = []
    if not fields:
        issues.append(Issue(path, line, "Human Gate 记录缺少可识别字段", code="HUMAN_GATE_RECORD_EMPTY"))

    for canonical, _ in HUMAN_GATE_REQUIRED_FIELDS:
        if canonical not in fields:
            issues.append(Issue(path, line, f"Human Gate 记录缺少字段: {canonical}", code="HUMAN_GATE_FIELD_MISSING"))
        elif not str(fields[canonical]).strip():
            issues.append(Issue(path, field_lines.get(canonical, line), f"Human Gate 记录字段为空: {canonical}", code="HUMAN_GATE_FIELD_EMPTY"))
    return issues


def check_markdown_file(path):
    issues = []
    lines = path.read_text(encoding="utf-8").splitlines()
    in_code_block = False

    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        if not HUMAN_GATE_HEADER_RE.match(stripped):
            continue

        block = collect_record(lines, index)
        fields, field_lines = record_fields(block)
        issues.extend(check_record_fields(path, index + 1, fields, field_lines))

    return issues


def yaml_records(data):
    records = []
    if isinstance(data, dict):
        for key, value in data.items():
            if key in HUMAN_GATE_YAML_KEYS:
                if isinstance(value, list):
                    records.extend(item for item in value if isinstance(item, dict))
                elif isinstance(value, dict):
                    records.append(value)
            elif isinstance(value, (dict, list)):
                records.extend(yaml_records(value))
    elif isinstance(data, list):
        for item in data:
            records.extend(yaml_records(item))
    return records


def yaml_line_map(text):
    aliases = alias_map()
    lines = {}
    for index, line in enumerate(text.splitlines(), start=1):
        match = re.match(r"^\s*([A-Za-z_\-/\u4e00-\u9fff ]+)\s*:", line)
        if not match:
            continue
        canonical = aliases.get(normalize_label(match.group(1)))
        if canonical and canonical not in lines:
            lines[canonical] = index
    return lines


def yaml_record_fields(record):
    aliases = alias_map()
    fields = {}
    for key, value in record.items():
        canonical = aliases.get(normalize_label(key))
        if not canonical:
            continue
        if isinstance(value, (dict, list)):
            text = json.dumps(value, ensure_ascii=False)
        elif value is None:
            text = ""
        else:
            text = str(value).strip()
        fields[canonical] = "\n".join(item for item in [fields.get(canonical, ""), text] if item).strip()
    return fields


def check_yaml_file(path):
    text = path.read_text(encoding="utf-8")
    if not any(key in text for key in HUMAN_GATE_YAML_KEYS):
        return []
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        return [Issue(path, 1, f"Human Gate YAML 解析失败: {exc}", code="HUMAN_GATE_YAML_INVALID")]
    records = yaml_records(data)
    line_map = yaml_line_map(text)
    issues = []
    for record in records:
        fields = yaml_record_fields(record)
        issues.extend(check_record_fields(path, 1, fields, line_map))
    return issues


def check_file(path):
    if path.suffix == ".md":
        return check_markdown_file(path)
    if path.suffix in {".yaml", ".yml"}:
        return check_yaml_file(path)
    return []


def check_paths(paths):
    issues = []
    for path in iter_files(paths):
        issues.extend(check_file(path))
    return issues


def count_markdown_records_file(path):
    count = 0
    lines = path.read_text(encoding="utf-8").splitlines()
    in_code_block = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        if HUMAN_GATE_HEADER_RE.match(stripped):
            count += 1
    return count


def count_yaml_records_file(path):
    text = path.read_text(encoding="utf-8")
    if not any(key in text for key in HUMAN_GATE_YAML_KEYS):
        return 0
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError:
        return 0
    return len(yaml_records(data))


def count_records_file(path):
    if path.suffix == ".md":
        return count_markdown_records_file(path)
    if path.suffix in {".yaml", ".yml"}:
        return count_yaml_records_file(path)
    return 0


def report_build(paths=None):
    check_paths = paths if paths is not None else default_check_paths()
    files = [path for path in iter_files(check_paths) if is_project_local(path)]
    issues = []
    record_count = 0
    for file_path in files:
        record_count += count_records_file(file_path)
        issues.extend(check_file(file_path))
    issue_items = []
    for issue in issues:
        issue_items.append(
            {
                "source": relative_path(issue.path),
                "line": issue.line,
                "code": issue.code,
                "status": "open",
                "message": issue.message,
            }
        )
    status = "closed"
    if issue_items:
        status = "open"
    elif record_count == 0:
        status = "degraded"
    return {
        "metadata": {
            "tool": "code/specs_validate.py",
            "report": "human-gate",
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "source_of_truth": False,
            "status_source": "derived heuristic",
            "checked_file_count": len(files),
            "record_count": record_count,
            "issue_count": len(issue_items),
            "scope": "project-local Markdown/YAML facts only",
        },
        "summary": {
            "status": status,
            "by_status": count_by(issue_items, "status"),
            "by_code": count_by(issue_items, "code"),
        },
        "issues": issue_items,
    }


def report_format_text(report):
    lines = ["Human Gate 证据结构检查"]
    metadata = report["metadata"]
    lines.append(f"- 检查文件数: {metadata['checked_file_count']}")
    lines.append(f"- 记录数: {metadata['record_count']}")
    lines.append(f"- 问题数: {metadata['issue_count']}")
    lines.append(f"- 状态: {report['summary']['status']}")
    lines.append("- 状态判断: Code 派生启发式，非事实源")
    lines.append("")
    lines.append("问题:")
    if not report["issues"]:
        lines.append("- 无")
    else:
        for item in report["issues"]:
            lines.append(f"- {item['source']}:{item['line']} [{item['status']}/{item['code']}] {item['message']}")
    return "\n".join(lines)


def report_main(paths=None, output_format="text"):
    report = report_build(paths if paths else None)
    if output_format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(report_format_text(report))
    return 0 if report["summary"]["status"] == "closed" else 1


def main(paths):
    selected_paths = paths if paths else default_check_paths()
    issues = check_paths(selected_paths)
    if issues:
        print(f"Human Gate 轻量人类决策记录结构检查失败，共 {len(issues)} 个问题：")
        for issue in issues:
            print(f"- {issue.format(PROJECT_ROOT)}")
        return 1
    print("Human Gate 最小证据结构检查通过。")
    return 0
