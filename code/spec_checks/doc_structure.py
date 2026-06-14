"""Markdown document heading structure checks for LDVH specs."""

import re
from dataclasses import dataclass
from pathlib import Path

from .common import HEADING_RE, Issue, iter_markdown_files


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOC_NUMBERED_HEADING_RE = re.compile(r"^(\d+(?:\.\d+)*)\.?(?:\s+|$)")
DOC_CHINESE_HEADING_RE = re.compile(r"^[一二三四五六七八九十百千万]+[、，.．]\s*")
DOC_ROMAN_HEADING_RE = re.compile(r"^[IVXLCDM]+[、.．]\s+", re.IGNORECASE)
DOC_UNNUMBERED_ALLOWED_HEADINGS = {"章节索引"}


@dataclass
class Heading:
    path: Path
    line: int
    level: int
    title: str
    numbers: tuple


class HeadingNumberState:
    def __init__(self):
        self.current = {}
        self.seen = set()

    def check(self, heading):
        issues = []
        structural_level = heading.level - 1
        number_depth = len(heading.numbers)
        number_text = ".".join(str(part) for part in heading.numbers)

        if heading.level == 1:
            return issues

        if heading.level > 4:
            issues.append(Issue(heading.path, heading.line, f"不支持超过四级的正文章节标题: {'#' * heading.level}"))
            return issues

        if number_depth != structural_level:
            issues.append(
                Issue(
                    heading.path,
                    heading.line,
                    f"标题层级与编号层级不一致: {'#' * heading.level} 应使用 {structural_level} 段编号，实际为 {number_text}",
                )
            )
            return issues

        if heading.numbers in self.seen:
            issues.append(Issue(heading.path, heading.line, f"章节编号重复: §{number_text}"))
        self.seen.add(heading.numbers)

        parent = heading.numbers[:-1]
        if structural_level > 1:
            expected_parent = self.current.get(structural_level - 1)
            if expected_parent != parent:
                expected_text = ".".join(str(part) for part in expected_parent) if expected_parent else "无父章节"
                parent_text = ".".join(str(part) for part in parent)
                issues.append(
                    Issue(
                        heading.path,
                        heading.line,
                        f"章节父级不一致: §{number_text} 的父级应为 §{expected_text}，实际编号父级为 §{parent_text}",
                    )
                )

        previous = self.current.get(structural_level)
        if previous and previous[:-1] == parent:
            expected_last = previous[-1] + 1
            expected = parent + (expected_last,)
        elif structural_level > 1:
            expected_parent = self.current.get(structural_level - 1) or parent
            expected = expected_parent + (1,)
        else:
            expected = (1,)
        if heading.numbers != expected:
            expected_text = ".".join(str(part) for part in expected)
            issues.append(Issue(heading.path, heading.line, f"章节编号不连续: 期望 §{expected_text}，实际 §{number_text}"))

        self.current[structural_level] = heading.numbers
        for level in list(self.current):
            if level > structural_level:
                del self.current[level]
        return issues


def parse_heading_number(title):
    match = DOC_NUMBERED_HEADING_RE.match(title)
    if not match:
        return None
    return tuple(int(part) for part in match.group(1).split("."))


def check_file(path):
    issues = []
    state = HeadingNumberState()
    in_code_block = False

    for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue

        match = HEADING_RE.match(line)
        if not match:
            continue

        level = len(match.group(1))
        title = match.group(2).strip()
        if level == 1:
            continue

        if DOC_CHINESE_HEADING_RE.match(title):
            issues.append(Issue(path, index, f"章节标题使用中文大写编号: {title}"))
            continue
        if DOC_ROMAN_HEADING_RE.match(title):
            issues.append(Issue(path, index, f"章节标题使用罗马数字编号: {title}"))
            continue

        numbers = parse_heading_number(title)
        if numbers is None:
            if title in DOC_UNNUMBERED_ALLOWED_HEADINGS:
                continue
            issues.append(Issue(path, index, f"章节标题缺少阿拉伯数字编号: {title}"))
            continue

        issues.extend(state.check(Heading(path, index, level, title, numbers)))

    return issues


def check_paths(paths):
    issues = []
    for path in iter_markdown_files(paths):
        issues.extend(check_file(path))
    return issues


def main(paths):
    issues = check_paths(paths)
    if issues:
        print(f"03 文档基础规范检查失败，共 {len(issues)} 个问题：")
        for issue in issues:
            print(f"- {issue.format(PROJECT_ROOT)}")
        return 1
    print("03 文档基础规范检查通过。")
    return 0
