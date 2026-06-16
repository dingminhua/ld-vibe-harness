"""Runtime projection drift checks for LDVH."""

import json
import re
from datetime import datetime
from pathlib import Path

from .common import Issue, count_by, is_project_local as common_is_project_local, relative_path as common_relative_path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FORMAL_SPECS_DIR = PROJECT_ROOT / "specs"
RUNTIME_PROJECTION_DEFAULT_PATHS = [
    "rules/LDVH-WORKSPACE-ENTRY.md",
    "rules/LDVH-MAINTAINER-ENTRY.md",
    ".trae/rules",
    ".trae/skills",
]
RUNTIME_PROJECTION_SPEC_REF_RE = re.compile(r"specs/[^`\s，。；、)）]+\.md")
RUNTIME_PROJECTION_AUTHORITY_RE = re.compile(r"(specs/|规范来源|权威来源|上位依据|相关规范|降级|人工降级|degradation)")
RUNTIME_PROJECTION_NEGATIVE_AUTHORITY_RE = re.compile(r"(无|没有|缺少|未).{0,8}(权威来源|规范来源|上位依据|相关规范|specs/|降级)")


def relative_path(path):
    return common_relative_path(path, PROJECT_ROOT)


def default_paths():
    paths = []
    for raw_path in RUNTIME_PROJECTION_DEFAULT_PATHS:
        path = PROJECT_ROOT / raw_path
        if path.exists():
            paths.append(str(path))
    return paths


def is_project_local(path):
    return common_is_project_local(path, PROJECT_ROOT)


def iter_files(paths):
    files = []
    for raw_path in paths:
        path = Path(raw_path)
        if not path.exists():
            continue
        if not is_project_local(path):
            continue
        if path.is_file() and path.suffix in {".md", ".yaml", ".yml", ".json", ".toml"}:
            files.append(path)
        elif path.is_dir():
            for child in path.rglob("*"):
                if child.is_file() and child.suffix in {".md", ".yaml", ".yml", ".json", ".toml"}:
                    files.append(child)
    return sorted(set(files))


def has_authority(text):
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if RUNTIME_PROJECTION_NEGATIVE_AUTHORITY_RE.search(stripped):
            continue
        if RUNTIME_PROJECTION_AUTHORITY_RE.search(stripped):
            return True
    return False


def spec_refs(text):
    return sorted(set(RUNTIME_PROJECTION_SPEC_REF_RE.findall(text)))


def spec_path_exists(ref):
    return (PROJECT_ROOT / ref).exists()


def formal_spec_lines():
    lines = {}
    if not FORMAL_SPECS_DIR.exists():
        return lines
    for spec_path in sorted(FORMAL_SPECS_DIR.glob("*.md")):
        for line in spec_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if len(stripped) < 32:
                continue
            if stripped.startswith("|") or stripped.startswith(">") or stripped.startswith("#"):
                continue
            lines.setdefault(stripped, relative_path(spec_path))
    return lines


def detect_copied_formal_lines(text, formal_lines):
    matches = []
    for line in text.splitlines():
        stripped = line.strip()
        source = formal_lines.get(stripped)
        if source:
            matches.append({"source": source, "text": stripped})
    return matches[:5]


def check_file(path, formal_lines_input=None):
    checked_formal_lines = formal_lines_input if formal_lines_input is not None else formal_spec_lines()
    text = path.read_text(encoding="utf-8")
    issues = []
    if not has_authority(text):
        issues.append(Issue(path, 1, "运行投影缺少 specs 权威来源引用或明确降级来源", code="RUNTIME_PROJECTION_AUTHORITY_MISSING"))
    for ref in spec_refs(text):
        if not spec_path_exists(ref):
            issues.append(Issue(path, 1, f"运行投影引用的正式规范不存在: {ref}", code="RUNTIME_PROJECTION_SPEC_REF_MISSING"))
    copied = detect_copied_formal_lines(text, checked_formal_lines)
    if len(copied) >= 3:
        sources = ", ".join(sorted({item["source"] for item in copied}))
        issues.append(Issue(path, 1, f"运行投影疑似复制正式规范正文，可能产生漂移: {sources}", code="RUNTIME_PROJECTION_BODY_COPIED"))
    return issues


def issue_status(issue):
    if issue.code == "RUNTIME_PROJECTION_BODY_COPIED":
        return "degraded"
    return "open"


def report_build(paths=None):
    check_paths = paths if paths is not None else default_paths()
    files = iter_files(check_paths)
    checked_formal_lines = formal_spec_lines()
    issues = []
    for file_path in files:
        issues.extend(check_file(file_path, checked_formal_lines))
    issue_items = []
    for issue in issues:
        issue_items.append(
            {
                "source": relative_path(issue.path),
                "line": issue.line,
                "code": issue.code,
                "status": issue_status(issue),
                "message": issue.message,
            }
        )
    status = "closed"
    if any(item["status"] == "open" for item in issue_items):
        status = "open"
    elif any(item["status"] == "degraded" for item in issue_items):
        status = "degraded"
    elif not files:
        status = "open"
    return {
        "metadata": {
            "tool": "code/specs_validate.py",
            "report": "runtime-projection",
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "source_of_truth": False,
            "status_source": "derived heuristic",
            "checked_file_count": len(files),
            "issue_count": len(issue_items),
            "scope": "project-local runtime projections only",
        },
        "summary": {
            "status": status,
            "by_status": count_by(issue_items, "status"),
            "by_code": count_by(issue_items, "code"),
        },
        "issues": issue_items,
    }


def format_text(report):
    lines = ["运行投影漂移检查"]
    metadata = report["metadata"]
    lines.append(f"- 检查文件数: {metadata['checked_file_count']}")
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


def main(paths=None, output_format="text"):
    report = report_build(paths if paths else None)
    if output_format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(format_text(report))
    return 0 if report["summary"]["status"] == "closed" else 1
