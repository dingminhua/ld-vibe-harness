from __future__ import annotations

import argparse
from dataclasses import dataclass
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
from datetime import datetime


ROOT = Path(__file__).resolve().parents[1]
HOOKS_PATH = "hooks"
COMMIT_MSG_HOOK = "commit-msg"
HOOK_MARKER = "# LDVH v3 managed commit-msg hook"
EXTERNAL_REPO_BLOCK_MESSAGE = (
    "External repo install/uninstall must use code/governed_hook_adapter.py "
    "with governed project resolution and --confirm-human-gate."
)


@dataclass(frozen=True)
class HookStatus:
    repo: Path
    hooks_path: str
    active_hook: Path
    active_hook_exists: bool
    active_hook_executable: bool
    active_hook_managed: bool
    common_hook: Path
    common_hook_exists: bool

    @property
    def installed(self) -> bool:
        return (
            self.hooks_path in {HOOKS_PATH, f"./{HOOKS_PATH}"}
            and self.active_hook_exists
            and self.active_hook_executable
            and self.active_hook_managed
        )


def _run_git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        capture_output=True,
        check=check,
    )


def resolve_repo(repo: Path) -> Path:
    completed = _run_git(repo, "rev-parse", "--show-toplevel")
    return Path(completed.stdout.strip()).resolve()


def _git_config(repo: Path, *args: str) -> str:
    completed = _run_git(repo, "config", *args, check=False)
    if completed.returncode != 0:
        return ""
    return completed.stdout.strip()


def _common_dir(repo: Path) -> Path:
    completed = _run_git(repo, "rev-parse", "--git-common-dir")
    raw = completed.stdout.strip()
    common = Path(raw)
    if not common.is_absolute():
        common = repo / common
    return common.resolve()


def template_path(ldvh_root: Path = ROOT) -> Path:
    return ldvh_root / HOOKS_PATH / COMMIT_MSG_HOOK


def render_commit_msg_hook(ldvh_root: Path = ROOT, embed_ldvh_root: bool = False) -> str:
    text = template_path(ldvh_root).read_text(encoding="utf-8")
    if not embed_ldvh_root:
        return text
    resolved_root = shlex.quote(ldvh_root.resolve().as_posix())
    return text.replace(
        "LDVH_ROOT=${LDVH_ROOT:-$REPO_ROOT}",
        f"LDVH_ROOT=${{LDVH_ROOT:-{resolved_root}}}",
    )


def inspect_status(repo: Path, ldvh_root: Path = ROOT) -> HookStatus:
    resolved_repo = resolve_repo(repo)
    hooks_path = _git_config(resolved_repo, "--get", "core.hooksPath")
    active_hook = resolved_repo / HOOKS_PATH / COMMIT_MSG_HOOK
    common_hook = _common_dir(resolved_repo) / "hooks" / COMMIT_MSG_HOOK
    active_text = active_hook.read_text(encoding="utf-8") if active_hook.is_file() else ""
    return HookStatus(
        repo=resolved_repo,
        hooks_path=hooks_path,
        active_hook=active_hook,
        active_hook_exists=active_hook.is_file(),
        active_hook_executable=active_hook.is_file() and os.access(active_hook, os.X_OK),
        active_hook_managed=HOOK_MARKER in active_text,
        common_hook=common_hook,
        common_hook_exists=common_hook.is_file(),
    )


def _backup_path(path: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return path.with_name(f"{path.name}.ldvh-backup-{timestamp}")


def install(repo: Path, ldvh_root: Path = ROOT, embed_ldvh_root: bool = False) -> HookStatus:
    resolved_repo = resolve_repo(repo)
    target_dir = resolved_repo / HOOKS_PATH
    target_dir.mkdir(parents=True, exist_ok=True)
    target_hook = target_dir / COMMIT_MSG_HOOK
    template = render_commit_msg_hook(ldvh_root, embed_ldvh_root=embed_ldvh_root)

    if target_hook.exists() and target_hook.read_text(encoding="utf-8") != template:
        shutil.copy2(target_hook, _backup_path(target_hook))

    target_hook.write_text(template, encoding="utf-8")
    target_hook.chmod(target_hook.stat().st_mode | 0o755)

    _run_git(resolved_repo, "config", "extensions.worktreeConfig", "true")
    _run_git(resolved_repo, "config", "--worktree", "core.hooksPath", HOOKS_PATH)
    return inspect_status(resolved_repo, ldvh_root)


def uninstall(repo: Path, ldvh_root: Path = ROOT) -> HookStatus:
    resolved_repo = resolve_repo(repo)
    current = _git_config(resolved_repo, "--get", "core.hooksPath")
    if current in {HOOKS_PATH, f"./{HOOKS_PATH}"}:
        _run_git(resolved_repo, "config", "--worktree", "--unset", "core.hooksPath", check=False)
    return inspect_status(resolved_repo, ldvh_root)


def is_current_ldvh_repo(repo: Path, ldvh_root: Path = ROOT) -> bool:
    try:
        return resolve_repo(repo) == resolve_repo(ldvh_root)
    except subprocess.CalledProcessError:
        return False


def print_status(status: HookStatus) -> None:
    print("LDVH v3 git hook status")
    print(f"- repo: {status.repo}")
    print(f"- core.hooksPath: {status.hooks_path or '<unset>'}")
    print(f"- active_hook: {status.active_hook}")
    print(f"- active_hook_exists: {status.active_hook_exists}")
    print(f"- active_hook_executable: {status.active_hook_executable}")
    print(f"- active_hook_managed: {status.active_hook_managed}")
    print(f"- common_hook: {status.common_hook}")
    print(f"- common_hook_exists: {status.common_hook_exists}")
    print(f"- installed: {status.installed}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Install LDVH v3 worktree-local Git hooks.")
    parser.add_argument("command", choices=["status", "install", "uninstall"])
    parser.add_argument("--repo", default=ROOT.as_posix(), help="target repository root")
    parser.add_argument("--ldvh-root", default=ROOT.as_posix(), help="LDVH v3 root containing hooks/ and code/")
    parser.add_argument(
        "--embed-ldvh-root",
        action="store_true",
        help="render the hook with this LDVH root as the default validator location",
    )
    parser.add_argument(
        "--backend-allow-external",
        action="store_true",
        help="backend-only escape hatch for tests/adapters; external users should use governed_hook_adapter.py",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo = Path(args.repo).resolve()
    ldvh_root = Path(args.ldvh_root).resolve()

    if args.command in {"install", "uninstall"} and not args.backend_allow_external:
        if not is_current_ldvh_repo(repo, ldvh_root):
            status = inspect_status(repo, ldvh_root)
            print_status(status)
            print(f"- diagnostic: {EXTERNAL_REPO_BLOCK_MESSAGE}")
            return 1

    if args.command == "install":
        status = install(repo, ldvh_root, embed_ldvh_root=args.embed_ldvh_root)
    elif args.command == "uninstall":
        status = uninstall(repo, ldvh_root)
    else:
        status = inspect_status(repo, ldvh_root)

    print_status(status)
    if args.command == "uninstall":
        return 0 if not status.installed else 1
    return 0 if status.installed else 1


if __name__ == "__main__":
    raise SystemExit(main())
