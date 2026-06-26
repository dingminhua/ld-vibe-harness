#!/usr/bin/env python3
"""Install LDVH native Git hooks for the current repository."""

from __future__ import annotations

import argparse
import os
import stat
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
MARKER = "# LDVH managed commit-msg hook"


def git_root(cwd: Path) -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "当前目录不在 Git 仓库中")
    return Path(result.stdout.strip()).resolve()


def hook_path(repo_root: Path) -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--git-path", "hooks/commit-msg"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "无法定位 .git/hooks/commit-msg")
    path = Path(result.stdout.strip())
    if not path.is_absolute():
        path = repo_root / path
    return path.resolve()


def render_commit_msg_hook(ldvh_root: Path, repo_root: Path) -> str:
    dispatcher = ldvh_root / "code" / "hook_dispatch.py"
    return f"""#!/bin/sh
{MARKER}
set -eu

LDVH_ROOT={str(ldvh_root)!r}
REPO_ROOT={str(repo_root)!r}
case "$1" in
  /*) MSG_FILE="$1" ;;
  *) MSG_FILE="$REPO_ROOT/$1" ;;
esac

cd "$LDVH_ROOT"
exec python3 {str(dispatcher)!r} run git.commit-msg --trigger-source hook --cwd "$REPO_ROOT" --message-file "$MSG_FILE"
"""


def ensure_executable(path: Path) -> None:
    mode = path.stat().st_mode
    path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def install_commit_msg_hook(repo_root: Path, ldvh_root: Path, *, force: bool = False) -> Path:
    target = hook_path(repo_root)
    desired = render_commit_msg_hook(ldvh_root, repo_root)

    if target.exists():
        current = target.read_text(encoding="utf-8", errors="replace")
        if current == desired:
            ensure_executable(target)
            return target
        if MARKER not in current and not force:
            raise RuntimeError(
                f"{target} 已存在且不是 LDVH 管理的 hook；如确认覆盖，请使用 --force"
            )

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(desired, encoding="utf-8")
    ensure_executable(target)
    return target


def status(repo_root: Path, ldvh_root: Path) -> int:
    target = hook_path(repo_root)
    desired = render_commit_msg_hook(ldvh_root, repo_root)
    if not target.exists():
        print(f"missing: {target}")
        return 1
    current = target.read_text(encoding="utf-8", errors="replace")
    executable = os.access(target, os.X_OK)
    if current == desired and executable:
        print(f"installed: {target}")
        return 0
    if MARKER in current:
        print(f"outdated: {target}")
        return 1
    print(f"foreign: {target}")
    return 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="安装或检查 LDVH native Git hooks")
    parser.add_argument(
        "action",
        nargs="?",
        choices=("install", "status"),
        default="install",
        help="install 写入 commit-msg hook；status 只检查当前状态",
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=PROJECT_ROOT,
        help="目标 Git 仓库目录，默认当前 LDVH 仓库",
    )
    parser.add_argument(
        "--ldvh-root",
        type=Path,
        default=PROJECT_ROOT,
        help="LDVH 实例根目录，默认当前仓库",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="覆盖已有非 LDVH commit-msg hook",
    )
    args = parser.parse_args(argv)

    try:
        repo_root = git_root(args.repo.resolve())
        ldvh_root = args.ldvh_root.resolve()
        if args.action == "status":
            return status(repo_root, ldvh_root)
        target = install_commit_msg_hook(repo_root, ldvh_root, force=args.force)
    except RuntimeError as exc:
        print(f"LDVH Git hook install failed: {exc}", file=sys.stderr)
        return 1

    print(f"installed: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
