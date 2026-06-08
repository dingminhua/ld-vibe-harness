#!/usr/bin/env python3
"""检查 Git commit message 是否符合 docs/specs/22-Change-变更.md 格式。

功能：
  - 默认模式：检查最近 N 条 git commit 历史
  - --show-format：展示正确的 commit message 格式规范（供 AI 参考）
  - --check-message：在提交前校验拟提交的 message 文本（提交前强制预检）
"""

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

# docs/specs/22-Change-变更.md type 枚举
VALID_TYPES = {"feat", "fix", "docs", "refactor", "test", "chore", "spec", "rule", "adr", "revert"}

# docs/specs/22-Change-变更.md scope 枚举（推荐值，非强制）
RECOMMENDED_SCOPES = {"specs", "docs", "rules", "adr", "tools", "web", "tests", "config", "evals", "refs"}

# docs/specs/22-Change-变更.md: subject 推荐不超过 72 字符
MAX_SUBJECT_LEN = 72

# 第一行格式: <type>(<scope>): <subject>
HEADER_RE = re.compile(r"^([a-z]+)(?:\(([^)]+)\))?:\s+(.+)$")

# Refs 行格式
REFS_RE = re.compile(r"^Refs:\s*(.+)$", re.MULTILINE)

# 中文字符检测（当前 LDVH 自身项目 Code 实现纪律）
HAS_CHINESE_RE = re.compile(r"[\u4e00-\u9fff]")

FORMAT_HELP = """\
正确的 commit message 格式（docs/specs/22-Change-变更.md）：

    <type>(<scope>): <subject>

    <body>

    Refs: <object-refs>

各部分说明：
  type      必填。变更类型：{valid_types}
  scope     可选。影响范围（推荐）：{valid_scopes}
  subject   必填。简短描述，不超过 72 字符
  body      可选。详细说明变更原因和内容
  Refs      建议。关联对象，多个对象用逗号分隔

示例：
  docs(specs): 迁移 Change 工作模型到 v2

  新增 docs/specs/22-Change-变更.md，明确 Change
  以 Git commit 历史作为事实实例。

  Refs: 22-Change-变更
""".format(
    valid_types=", ".join(sorted(VALID_TYPES)),
    valid_scopes=", ".join(sorted(RECOMMENDED_SCOPES)),
)


@dataclass
class Issue:
    source: str   # commit hash 或 "<message>"（表示预检）
    level: str    # "error" | "warning"
    message: str

    def format(self):
        prefix = "ERROR" if self.level == "error" else "WARN"
        display = self.source[:8] if len(self.source) >= 8 else self.source
        return f"{display}: [{prefix}] {self.message}"


@dataclass
class CommitInfo:
    hash: str
    subject: str
    body: str
    full_message: str


def show_format():
    """展示正确的 commit message 格式。"""
    print(FORMAT_HELP)


def parse_message_text(text: str) -> CommitInfo:
    """将纯文本 message 解析为 CommitInfo，用于提交前预检。"""
    lines = text.strip().split("\n", 1)
    subject = lines[0]
    body = lines[1] if len(lines) > 1 else ""
    full = f"{subject}\n\n{body}".strip() if body else subject
    return CommitInfo(hash="<message>", subject=subject, body=body, full_message=full)


def git_log(n: int) -> list[CommitInfo]:
    """获取最近 n 条 commit 信息。"""
    result = subprocess.run(
        ["git", "log", f"-{n}", "--format=%H%x00%s%x00%b%x1e"],
        capture_output=True, text=True, cwd=PROJECT_ROOT,
    )
    if result.returncode != 0:
        print(f"git log 失败: {result.stderr}", file=sys.stderr)
        sys.exit(1)

    commits = []
    for block in result.stdout.strip().split("\x1e"):
        block = block.strip()
        if not block:
            continue
        parts = block.split("\x00", 2)
        if len(parts) < 3:
            continue
        commits.append(CommitInfo(
            hash=parts[0],
            subject=parts[1],
            body=parts[2],
            full_message=f"{parts[1]}\n\n{parts[2]}".strip(),
        ))
    return commits


def check_commit(commit: CommitInfo) -> list[Issue]:
    """检查单条 commit message 格式。"""
    issues = []

    # 检查第一行格式
    first_line = commit.subject.strip()
    m = HEADER_RE.match(first_line)
    if not m:
        issues.append(Issue(
            commit.hash, "error",
            f"第一行格式不符合 '<type>(<scope>): <subject>': {first_line[:80]}"
        ))
        return issues

    type_val = m.group(1)
    scope_val = m.group(2)
    subject_val = m.group(3).strip()

    # 检查 type
    if type_val not in VALID_TYPES:
        issues.append(Issue(
            commit.hash, "error",
            f"type '{type_val}' 不在有效枚举中 ({', '.join(sorted(VALID_TYPES))})"
        ))

    # 检查 scope（推荐值，warning）
    if scope_val and scope_val not in RECOMMENDED_SCOPES:
        issues.append(Issue(
            commit.hash, "warning",
            f"scope '{scope_val}' 不在推荐枚举中 ({', '.join(sorted(RECOMMENDED_SCOPES))})"
        ))

    # 检查 subject 长度
    if len(first_line) > MAX_SUBJECT_LEN:
        issues.append(Issue(
            commit.hash, "error",
            f"subject 超过 {MAX_SUBJECT_LEN} 字符（当前 {len(first_line)} 字符）"
        ))

    # 检查 subject 不为空
    if not subject_val:
        issues.append(Issue(
            commit.hash, "error",
            "subject 不能为空"
        ))

    # 检查是否存在 Refs 行（warning，非强制）
    if not REFS_RE.search(commit.full_message):
        issues.append(Issue(
            commit.hash, "warning",
            "缺少 Refs: 行（非强制但建议添加关联对象引用）"
        ))

    # 检查是否包含中文（error，强制）
    # subject 中 type(scope) 之后的内容 + body 全文
    if m:
        content_to_check = subject_val + "\n" + commit.body
        if not HAS_CHINESE_RE.search(content_to_check):
            issues.append(Issue(
                commit.hash, "error",
                "commit message 必须包含中文字符（subject 和 body 部分），type 和 scope 不要求中文"
            ))

    return issues


def check_message(message_text: str) -> list[Issue]:
    """检查提交前拟写入的 message 文本是否符合格式。"""
    if not message_text or not message_text.strip():
        return [Issue("<message>", "error", "message 不能为空")]
    commit = parse_message_text(message_text)
    return check_commit(commit)


def main():
    parser = argparse.ArgumentParser(
        description="检查 Git commit message 是否符合 docs/specs/22-Change-变更.md 格式"
    )
    parser.add_argument(
        "--show-format", action="store_true",
        help="展示正确的 commit message 格式规范"
    )
    parser.add_argument(
        "--check-message", type=str, metavar="MSG", default=None,
        help="检查拟提交的 message 文本是否符合格式（提交前强制预检）"
    )
    parser.add_argument(
        "-n", "--count", type=int, default=10,
        help="检查最近 N 条 commit（默认 10，仅在默认模式下有效）"
    )
    parser.add_argument(
        "--no-warnings", action="store_true",
        help="只显示 error，不显示 warning"
    )
    args = parser.parse_args()

    # --show-format 模式
    if args.show_format:
        show_format()
        return

    # --check-message 模式：提交前预检
    if args.check_message is not None:
        issues = check_message(args.check_message)
        errors = [i for i in issues if i.level == "error"]
        warnings = [i for i in issues if i.level == "warning"]

        for issue in issues:
            if args.no_warnings and issue.level == "warning":
                continue
            print(issue.format())

        if errors:
            print(f"\n预检不通过：{len(errors)} 个 error")
            if not args.no_warnings and warnings:
                print(f"另有 {len(warnings)} 个 warning")
            sys.exit(1)
        else:
            print("预检通过")
            if not args.no_warnings and warnings:
                print(f"（{len(warnings)} 个 warning）")
        return

    # 默认模式：检查 git log
    commits = git_log(args.count)
    if not commits:
        print("没有找到 commit 记录")
        return

    total_issues = 0
    error_count = 0
    for commit in commits:
        issues = check_commit(commit)
        for issue in issues:
            if args.no_warnings and issue.level == "warning":
                continue
            print(issue.format())
            total_issues += 1
            if issue.level == "error":
                error_count += 1

    if total_issues == 0:
        print(f"最近 {args.count} 条 commit 格式均符合 docs/specs/22-Change-变更.md 要求")
    else:
        print(f"\n共 {total_issues} 个问题（{error_count} 个 error），检查了 {len(commits)} 条 commit")
        if error_count > 0:
            sys.exit(1)


if __name__ == "__main__":
    main()
