#!/usr/bin/env python3
"""检查 Git commit message 是否符合 specs/07-事实源边界与Git追溯规范.md。

功能：
  - 默认模式：检查最近 N 条 git commit 记录
  - --show-format：展示正确的 commit message 格式规范（供 AI 参考）
  - --check-message：在提交前校验拟提交的 message 文本（提交前强制预检）
"""

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


PROJECT_ROOT = Path(__file__).resolve().parent.parent
COMMIT_SPEC_PATH = "specs/07-事实源边界与Git追溯规范.md"
COMMIT_TYPE_SPEC_PATH = "specs/attachments/07.Att.02-Commit-Type枚举表.md"
COMMIT_SCOPE_SPEC_PATH = "specs/attachments/07.Att.03-Commit-Scope推荐表.md"
COMMIT_BODY_SPEC_PATH = "specs/attachments/07.Att.04-Commit-Body必填条件表.md"
COMMIT_FIELD_SPEC_PATH = "specs/attachments/07.Att.08-Commit-Message字段表.md"

# specs/attachments/07.Att.02-Commit-Type枚举表.md type 枚举
VALID_TYPES = {
    "build", "chore", "ci", "docs", "feat", "fix", "perf",
    "refactor", "revert", "style", "test",
}

# specs/attachments/07.Att.03-Commit-Scope推荐表.md scope 推荐值（非强制）
RECOMMENDED_SCOPES = {
    "specs", "docs", "rules", "code", "web", "tests", "config",
    "workcase", "adr", "spark", "study", "pitfall",
    "studies", "sources",
}

# specs/attachments/07.Att.08-Commit-Message字段表.md: description 推荐不超过 72 字符
MAX_SUBJECT_LEN = 72

# 第一行格式: <type>[optional scope][!]: <description>
HEADER_RE = re.compile(r"^([A-Za-z]+)(?:\(([^)]+)\))?(!)?:\s+(.+)$")
LDVH_PRIVATE_TRAILER_RE = re.compile(r"^\s*(Human-Gate|Verification|Risk):\s+.+$", re.MULTILINE)
COMMAND_LINE_RE = re.compile(
    r"^\s*(?:npm|pnpm|yarn|bun|python3?|pytest|ruff|mypy|node|tsc|git|make|cargo|go|deno)\b"
)
FILE_LIST_LINE_RE = re.compile(
    r"^\s*(?:[-*]\s+)?(?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.@%+~#=,:;()\\/\-\u4e00-\u9fff]+(?:\s+\|\s+\d+.*)?\s*$"
)
DIFF_STAT_LINE_RE = re.compile(r"^\s*(?:\d+\s+files?\s+changed|\d+\s+insertions?\(\+\)|\d+\s+deletions?\(-\))")
VAGUE_BODY_RE = re.compile(r"(更新|优化|完善|调整|修改|处理|补充|整理|按要求|相关|一些|若干|东西|内容)")
CONCRETE_OBJECT_RE = re.compile(
    r"(`[^`]+`|[A-Za-z0-9_.-]+/[A-Za-z0-9_./-]+|specs?|Code|Web|API|DTO|body|scope|type|commit|校验|展示|规范|事实源|提交|对象|入口|风险|兼容|契约)"
)

BODY_MIN_CHARS = 30

# 中文字符检测（当前 LDVH 自身项目 Code 实现纪律）
HAS_CHINESE_RE = re.compile(r"[\u4e00-\u9fff]")

FORMAT_HELP = """\
正确的 commit message 格式（{commit_spec_path}）：

    <type>[optional scope][!]: <description>

    [optional body]
    [optional footer(s)]

各部分说明：
  type      必填。变更类型闭集见 {commit_type_spec_path}：{valid_types}
  scope     可选。影响范围优先使用 {commit_scope_spec_path} 推荐值：{valid_scopes}
  !         可选。表示破坏性变更
  description 必填。简短描述，不超过 72 字符
  body      条件必填，条件见 {commit_body_spec_path}。推荐使用结构化语义清单说明动机、关键变更、影响边界、验证结论与风险
  footer    可选，字段契约见 {commit_field_spec_path}。遵守 Conventional Commits / git trailer，例如 BREAKING CHANGE、Refs、Co-authored-by

注意：
  footer 不得替代 body 的语义清单；LDVH 不定义 Human-Gate、Verification、Risk 作为标准必填 trailer

示例：
  docs(specs): 采用约定式提交规范

  动机:
  - 解决 Code 和 Web 解析边界不稳定的问题。

  关键变更:
  - 明确 type/scope 单主语义。
  - 把 body 定位为 Git 无法自动提供的人类语义层。

  验证结论:
  - 已确认提交预检能识别格式错误和明显空泛正文。
""".format(
    commit_spec_path=COMMIT_SPEC_PATH,
    commit_type_spec_path=COMMIT_TYPE_SPEC_PATH,
    commit_scope_spec_path=COMMIT_SCOPE_SPEC_PATH,
    commit_body_spec_path=COMMIT_BODY_SPEC_PATH,
    commit_field_spec_path=COMMIT_FIELD_SPEC_PATH,
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


def get_staged_files() -> list[str]:
    """返回当前 index 中 staged 的文件路径；失败时保守返回空列表。"""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMRT"],
        capture_output=True, text=True, cwd=PROJECT_ROOT,
    )
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def body_required_for_paths(paths: list[str]) -> bool:
    """按 staged touched files 的路径做 body 必填的保守判断。"""
    normalized = [path.strip().replace("\\", "/") for path in paths if path.strip()]
    if not normalized:
        return False
    if len(normalized) >= 2:
        return True

    body_required_prefixes = (
        "specs/",
        "rules/",
        "code/",
        "tests/",
        "web/",
        "hooks/",
        "agents/",
        "skills/",
        "ldvh-base/",
        ".github/",
    )
    body_required_names = {
        "AGENTS.md",
        "package.json",
        "package-lock.json",
        "pnpm-lock.yaml",
        "yarn.lock",
        "pyproject.toml",
        "requirements.txt",
    }

    return any(
        path.startswith(body_required_prefixes)
        or Path(path).name in body_required_names
        for path in normalized
    )


def body_lines(body: str) -> list[str]:
    return [line.strip() for line in body.splitlines() if line.strip()]


def mostly_matches(lines: list[str], pattern: re.Pattern[str]) -> bool:
    if not lines:
        return False
    matched = sum(1 for line in lines if pattern.search(line))
    return matched / len(lines) >= 0.6


def semantic_signal_count(body: str) -> int:
    signals = [
        r"(为什么|为了|因为|解决|避免|收敛|动机|目的|偏差)",
        r"(关键|变更|新增|明确|支持|禁止|改为|返回|展示|校验|实现)",
        r"(影响|范围|边界|对象|下游|用户|AI|Web|Code|契约|兼容)",
        r"(已确认|通过|未发现|验证|风险|未验证|后续|残留)",
    ]
    return sum(1 for pattern in signals if re.search(pattern, body))


def check_body_quality(commit: CommitInfo) -> list[Issue]:
    """检查 body 的明显偏差；不尝试替代 Human 语义审查。"""
    issues: list[Issue] = []
    body = commit.body.strip()
    if not body:
        return issues

    lines = body_lines(body)
    if len(body) < BODY_MIN_CHARS:
        issues.append(Issue(
            commit.hash, "warning",
            f"body 过短，可能不足以说明动机、关键变更、影响边界和风险（当前 {len(body)} 字符）"
        ))

    if mostly_matches(lines, COMMAND_LINE_RE):
        issues.append(Issue(
            commit.hash, "warning",
            "body 主要由检查命令组成；应改写为验证结论和残留风险，命令只能作为辅助证据"
        ))

    if mostly_matches(lines, FILE_LIST_LINE_RE) or mostly_matches(lines, DIFF_STAT_LINE_RE):
        issues.append(Issue(
            commit.hash, "warning",
            "body 主要像文件清单或 diff stat；Git 已提供这些信息，body 应说明人类语义"
        ))

    if VAGUE_BODY_RE.search(body) and not CONCRETE_OBJECT_RE.search(body):
        issues.append(Issue(
            commit.hash, "warning",
            "body 命中空泛词且缺少具体对象；应说明具体行为、契约、事实源或展示影响"
        ))

    if semantic_signal_count(body) < 2:
        issues.append(Issue(
            commit.hash, "warning",
            "body 缺少明显语义信号；建议覆盖动机、关键变更、影响边界、验证结论或风险中的至少两类"
        ))

    return issues


def check_commit(commit: CommitInfo, touched_files: Optional[list[str]] = None) -> list[Issue]:
    """检查单条 commit message 格式。"""
    issues = []

    # 检查第一行格式
    first_line = commit.subject.strip()
    m = HEADER_RE.match(first_line)
    if not m:
        issues.append(Issue(
            commit.hash, "error",
            f"第一行格式不符合 '<type>[optional scope][!]: <description>': {first_line[:80]}"
        ))
        return issues

    raw_type_val = m.group(1)
    type_val = raw_type_val.lower()
    scope_val = m.group(2)
    description_val = m.group(4).strip()

    # 检查 type
    if type_val not in VALID_TYPES:
        issues.append(Issue(
            commit.hash, "error",
            f"type '{type_val}' 不在有效枚举中 ({', '.join(sorted(VALID_TYPES))})"
        ))

    if raw_type_val != type_val:
        issues.append(Issue(
            commit.hash, "warning",
            f"type 建议使用小写: {raw_type_val}"
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
            commit.hash, "warning",
            f"description 所在首行超过 {MAX_SUBJECT_LEN} 字符（当前 {len(first_line)} 字符）"
        ))

    # 检查 description 不为空
    if not description_val:
        issues.append(Issue(
            commit.hash, "error",
            "description 不能为空"
        ))

    if touched_files is not None and body_required_for_paths(touched_files) and not commit.body.strip():
        issues.append(Issue(
            commit.hash, "error",
            "当前 staged files 要求 commit body 非空；body 应说明动机、关键变更、影响边界和风险"
        ))

    private_trailers = sorted({match.group(1) for match in LDVH_PRIVATE_TRAILER_RE.finditer(commit.full_message)})
    if private_trailers:
        issues.append(Issue(
            commit.hash, "warning",
            f"不建议使用 LDVH 私有 trailer 替代 body 语义清单: {', '.join(private_trailers)}"
        ))

    # 检查是否包含中文（error，强制）
    # description + body 全文
    if m:
        content_to_check = description_val + "\n" + commit.body
        if not HAS_CHINESE_RE.search(content_to_check):
            issues.append(Issue(
                commit.hash, "error",
                "commit message 必须包含中文字符（description 和 body 部分），type 和 scope 不要求中文"
            ))

    issues.extend(check_body_quality(commit))

    return issues


def check_message(message_text: str, touched_files: Optional[list[str]] = None) -> list[Issue]:
    """检查提交前拟写入的 message 文本是否符合格式。"""
    if not message_text or not message_text.strip():
        return [Issue("<message>", "error", "message 不能为空")]
    commit = parse_message_text(message_text)
    return check_commit(commit, touched_files=touched_files)


def main():
    parser = argparse.ArgumentParser(
        description=f"检查 Git commit message 是否符合 {COMMIT_SPEC_PATH}"
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
        "--check-message-file", type=Path, metavar="PATH", default=None,
        help="从文件读取拟提交的 message 文本并检查格式（供统一 Hook dispatcher 调用）"
    )
    parser.add_argument(
        "--files", nargs="*", default=None,
        help="指定本次提交的文件清单；未指定时 --check-message 会读取 staged files"
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

    if args.check_message is not None and args.check_message_file is not None:
        print("--check-message 和 --check-message-file 只能选择一个", file=sys.stderr)
        sys.exit(2)

    # --check-message / --check-message-file 模式：提交前预检
    if args.check_message is not None or args.check_message_file is not None:
        if args.check_message_file is not None:
            try:
                message_text = args.check_message_file.read_text(encoding="utf-8")
            except OSError as exc:
                print(f"读取 commit message 文件失败: {exc}", file=sys.stderr)
                sys.exit(1)
        else:
            message_text = args.check_message
        touched_files = args.files if args.files is not None else get_staged_files()
        issues = check_message(message_text, touched_files=touched_files)
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
        print(f"最近 {args.count} 条 commit 格式均符合 {COMMIT_SPEC_PATH} 要求")
    else:
        print(f"\n共 {total_issues} 个问题（{error_count} 个 error），检查了 {len(commits)} 条 commit")
        if error_count > 0:
            sys.exit(1)


if __name__ == "__main__":
    main()
