#!/usr/bin/env python3
"""检查 Git commit message 是否符合 specs/22-Change-变更记录.md §8 格式。"""

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

# specs/22 §8.2 type 枚举
VALID_TYPES = {"feat", "fix", "docs", "refactor", "test", "chore", "spec", "rule", "adr", "revert"}

# specs/22 §8.3 scope 枚举（推荐值，非强制）
RECOMMENDED_SCOPES = {"specs", "rules", "adr", "tools", "web"}

# specs/22 §8.1: subject 不超过 72 字符
MAX_SUBJECT_LEN = 72

# 第一行格式: <type>(<scope>): <subject>
HEADER_RE = re.compile(r"^([a-z]+)(?:\(([^)]+)\))?:\s+(.+)$")

# Refs 行格式
REFS_RE = re.compile(r"^Refs:\s*(.+)$", re.MULTILINE)


@dataclass
class Issue:
    commit_hash: str
    level: str  # "error" | "warning"
    message: str

    def format(self):
        prefix = "ERROR" if self.level == "error" else "WARN"
        return f"{self.commit_hash[:8]}: [{prefix}] {self.message}"


@dataclass
class CommitInfo:
    hash: str
    subject: str
    body: str
    full_message: str


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

    return issues


def main():
    parser = argparse.ArgumentParser(
        description="检查 Git commit message 是否符合 specs/22 §8 格式"
    )
    parser.add_argument(
        "-n", "--count", type=int, default=10,
        help="检查最近 N 条 commit（默认 10）"
    )
    parser.add_argument(
        "--no-warnings", action="store_true",
        help="只显示 error，不显示 warning"
    )
    args = parser.parse_args()

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
        print(f"最近 {args.count} 条 commit 格式均符合 specs/22 §8 要求")
    else:
        print(f"\n共 {total_issues} 个问题（{error_count} 个 error），检查了 {len(commits)} 条 commit")
        if error_count > 0:
            sys.exit(1)


if __name__ == "__main__":
    main()