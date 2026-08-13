"""Stable ``ldvh environment-sync`` surface: inspect and update one AI's LDVH skill.

The current AI must name its platform (a non-empty label, reported only) and the
*absolute* ``--skill-path`` of the actual target.  Nothing guesses a vendor directory.
``inspect`` is read-only and never writes.  ``update`` requires ``--confirm-human-gate``
and, before the Gate, performs zero writes; it reuses the Git Hook manager rather than
copying its state machine.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from ldvh.environment_sync import inspect_skill, update_skill
from ldvh.git_hooks.commit_msg import inspect_commit_msg_hook, install_commit_msg_hook
from ldvh.governance.models import LocatorSource, ScopeDescriptor, ScopeStatus
from ldvh.governance.resolver import resolve_governance_scope

_CONTRACT = "ldvh-environment-sync/1"
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_CANONICAL_SKILL = _PROJECT_ROOT / "skill" / "SKILL.md"


def _run_git(worktree: Path, *arguments: str) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "-C", str(worktree), *arguments],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout.strip()


def _common_hooks_dir(worktree: Path) -> Path | None:
    common = _run_git(worktree, "rev-parse", "--git-common-dir")
    if common is None:
        return None
    candidate = Path(common)
    if candidate.is_absolute():
        return (candidate / "hooks").resolve()
    return (worktree / candidate / "hooks").resolve()


def _resolve_update_context(worktree: str) -> tuple[str, str] | None:
    requested = (ScopeDescriptor(0, worktree, LocatorSource.EXPLICIT_LOCATOR),)
    run = resolve_governance_scope(requested, base=Path.cwd(), explicit_workspace_root=None)
    if run.result is None or run.result.scope_status is not ScopeStatus.GOVERNED_SINGLE:
        return None
    if run.result.workspace_root is None or len(run.result.object_resolutions) != 1:
        return None
    actual_worktree = run.result.object_resolutions[0].git_worktree_root
    if actual_worktree is None:
        return None
    return actual_worktree, run.result.workspace_root


def _emit(report: dict[str, object]) -> None:
    sys.stdout.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")


def _inspect(arguments: argparse.Namespace) -> int:
    skill = inspect_skill(
        platform=arguments.platform,
        skill_path=arguments.skill_path,
        source_path=_CANONICAL_SKILL,
    )
    worktree = Path(arguments.worktree).resolve() if arguments.worktree else _PROJECT_ROOT
    common_hooks = _common_hooks_dir(worktree)
    hook_surface = inspect_skill_hook_surface(common_hooks) if common_hooks is not None else None
    report = {
        "contract": _CONTRACT,
        "verb": "inspect",
        "platform": skill.platform,
        "skill_path": skill.skill_path,
        "canonical_source": str(_CANONICAL_SKILL),
        "skill": {
            "exists": skill.exists,
            "is_ldvh_skill": skill.is_ldvh_skill,
            "target_version": skill.target_version,
            "source_version": skill.source_version,
            "byte_aligned": skill.byte_aligned,
            "version_aligned": skill.version_aligned,
        },
        "git_hooks": hook_surface,
        "stop_gate": _stop_gate_check(_PROJECT_ROOT),
        "worktree": {
            "root": str(worktree),
            "common_hooks_dir": str(common_hooks) if common_hooks is not None else None,
        },
    }
    _emit(report)
    return 0


def inspect_skill_hook_surface(common_hooks: Path) -> dict[str, object]:
    from ldvh.environment_sync import inspect_hook_surface

    return inspect_hook_surface(common_hooks=common_hooks)


def _stop_gate_check(project_root: Path) -> dict[str, object]:
    wrapper = project_root / ".claude" / "hooks" / "ldvh-workcase-stop.py"
    implementation = project_root / "code" / "ldvh" / "hooks" / "workcase_stop.py"
    wrapper_ok = wrapper.is_file()
    impl_ok = implementation.is_file()
    references_impl = False
    if wrapper_ok:
        try:
            text = wrapper.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            text = ""
        references_impl = "from ldvh.hooks.workcase_stop import main" in text
    aligned = wrapper_ok and impl_ok and references_impl
    return {
        "aligned": aligned,
        "wrapper_path": str(wrapper),
        "wrapper_exists": wrapper_ok,
        "implementation_path": str(implementation),
        "implementation_exists": impl_ok,
        "wrapper_references_implementation": references_impl,
    }


def _worktree_coverage(worktree: Path) -> dict[str, object]:
    lines_raw = _run_git(worktree, "worktree", "list", "--porcelain")
    if lines_raw is None:
        return {"aligned": False, "error": "git worktree list failed; is this a git worktree?"}
    worktrees: list[str] = []
    current: dict[str, str] = {}
    for line in lines_raw.splitlines():
        if line.startswith("worktree "):
            if current:
                worktrees.append(current.get("path", ""))
            current = {"path": line.removeprefix("worktree ").strip()}
        elif line.startswith("HEAD "):
            current["head"] = line.removeprefix("HEAD ").strip()
    if current:
        worktrees.append(current.get("path", ""))
    common_dirs: dict[str, str] = {}
    for wt in worktrees:
        if not wt:
            continue
        common = _run_git(Path(wt), "rev-parse", "--git-common-dir")
        if common is None:
            common_dirs[wt] = "unavailable"
        else:
            candidate = Path(common)
            common_dirs[wt] = str((Path(wt) / candidate).resolve()) if not candidate.is_absolute() else common
    distinct = {value for value in common_dirs.values() if value != "unavailable"}
    return {
        "aligned": len(distinct) <= 1,
        "worktrees": worktrees,
        "common_dirs": common_dirs,
        "distinct_common_dirs": sorted(distinct),
    }


def _update(arguments: argparse.Namespace) -> int:
    if not arguments.confirm_human_gate:
        report = {
            "contract": _CONTRACT,
            "verb": "update",
            "platform": arguments.platform,
            "skill_path": arguments.skill_path,
            "human_gate_confirmed": False,
            "writes": 0,
            "detail": "update 需要显式 --confirm-human-gate；Gate 确认前零写入",
        }
        _emit(report)
        return 2
    worktree = arguments.worktree or str(Path.cwd())
    update_context = _resolve_update_context(worktree)
    if update_context is None:
        sys.stderr.write("error: update 无法从 --worktree 或当前目录解析唯一受管辖 worktree 与 workspace\n")
        return 2
    actual_worktree, workspace_root = update_context
    runner = (
        str(Path(arguments.commit_msg_runner).resolve())
        if arguments.commit_msg_runner
        else str(_PROJECT_ROOT / "ldvh")
    )

    skill = update_skill(
        platform=arguments.platform,
        skill_path=arguments.skill_path,
        source_path=_CANONICAL_SKILL,
        human_gate_confirmed=True,
    )
    if skill.conflict or not skill.aligned:
        hook_status = inspect_commit_msg_hook(worktree=actual_worktree)
    else:
        hook_status = install_commit_msg_hook(
            worktree=actual_worktree,
            workspace_root=workspace_root,
            commit_msg_runner=runner,
            human_gate_confirmed=True,
        )
    report = {
        "contract": _CONTRACT,
        "verb": "update",
        "platform": skill.platform,
        "skill_path": skill.skill_path,
        "human_gate_confirmed": True,
        "skill": {
            "created": skill.created,
            "replaced": skill.replaced,
            "conflict": skill.conflict,
            "aligned": skill.aligned,
            "target_version": skill.target_version,
            "source_version": skill.source_version,
            "detail": skill.detail,
        },
        "git_hook": {
            "attempted_update": skill.aligned and not skill.conflict,
            "state": hook_status.state,
            "detail": hook_status.detail,
            "hook_bundle_version": hook_status.hook_bundle_version,
            "expected_hook_bundle_version": hook_status.expected_hook_bundle_version,
        },
        "worktree": actual_worktree,
        "workspace_root": workspace_root,
        "commit_msg_runner": runner,
        "worktree_coverage": _worktree_coverage(Path(actual_worktree)),
    }
    _emit(report)
    if skill.conflict or hook_status.state not in {"managed"}:
        return 1
    return 0


def main(arguments: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="检查或更新单一 AI 环境的 LDVH Skill 与 Git Hook")
    sub = parser.add_subparsers(dest="verb", required=True)

    inspect_parser = sub.add_parser("inspect", help="只读检查 Skill 字节对齐、Hook、Stop gate 与 worktree 覆盖")
    inspect_parser.add_argument("--platform", required=True, help="当前 AI 平台标签（仅报告）")
    inspect_parser.add_argument("--skill-path", required=True, help="实际目标 Skill 绝对路径")
    inspect_parser.add_argument("--worktree", default=None, help="受管辖 worktree，默认项目根")

    update_parser = sub.add_parser("update", help="授权后更新目标 Skill 并部署当前 common-dir Git Hook")
    update_parser.add_argument("--platform", required=True, help="当前 AI 平台标签（仅报告）")
    update_parser.add_argument("--skill-path", required=True, help="实际目标 Skill 绝对路径")
    update_parser.add_argument("--worktree", default=None, help="受管辖 worktree，默认当前目录")
    update_parser.add_argument(
        "--commit-msg-runner",
        default=None,
        help="已确认源码 launcher 绝对路径，默认当前 LDVH 源码根的 ldvh",
    )
    update_parser.add_argument("--confirm-human-gate", action="store_true", help="显式确认 Human Gate 后方可写入")

    parsed = parser.parse_args(arguments)
    if parsed.verb == "inspect":
        return _inspect(parsed)
    return _update(parsed)


if __name__ == "__main__":
    raise SystemExit(main())
