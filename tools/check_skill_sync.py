#!/usr/bin/env python3
"""Check LDVH skill/hook deployment alignment after a skill update.

Reads only; never writes, unless --sync is explicitly given together with an
explicit Human Gate confirmation.  Reports the alignment of four surfaces so a
"skill updated" event can be checked in one command instead of hand-assembled
steps:

1. skill copy: project skill/SKILL.md vs the explicitly named --skill-path target
2. commit-msg hook: state (managed/absent/conflict) and bundle version vs HOOK_BUNDLE_VERSION
4. Stop gate: .claude/hooks/ldvh-workcase-stop.py wrapper vs code/ldvh/hooks/workcase_stop.py
5. worktree coverage: every worktree shares the same git common-dir hooks boundary

The current AI must pass a non-empty --platform label (reported only) and the
absolute --skill-path of the actual target.  No vendor directory (e.g. WorkBuddy)
is guessed.  The module shares all skill/Hook logic with the Helper operation and
the ``ldvh environment-sync`` surface via ``ldvh.environment_sync``.

Exit code 0 = all surfaces aligned; 1 = at least one misalignment; 2 = usage/environment error.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "code"))


def _ensure_dependency_runtime() -> None:
    """Hand off to the project venv when the current interpreter is too old.

    The shared ``ldvh.environment_sync`` module uses Python 3.11+ dataclass slots,
    so a host Python 3.10 or older must delegate to the prepared venv before import.
    """
    if sys.version_info >= (3, 11):  # noqa: UP036 - host 3.10/3.9 still needs this gate
        return
    candidates = (
        PROJECT_ROOT / ".venv" / "bin" / "python",
        PROJECT_ROOT / ".venv" / "Scripts" / "python.exe",
    )
    for candidate in candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            completed = subprocess.run([str(candidate), str(Path(__file__).resolve()), *sys.argv[1:]], check=False)
            raise SystemExit(completed.returncode)
    sys.stderr.write("error: check_skill_sync 需要 Python 3.11+ 或已准备的 .venv\n")
    raise SystemExit(2)


_ensure_dependency_runtime()

from ldvh.environment_sync import (  # noqa: E402
    _has_ldvh_frontmatter,
    _read_skill_version,
    inspect_hook_surface,
    update_skill,
    validate_skill_frontmatter,
)

CONTRACT = "ldvh-skill-sync-check/1"
PROJECT_SKILL = PROJECT_ROOT / "skill" / "SKILL.md"
STOP_WRAPPER = PROJECT_ROOT / ".claude" / "hooks" / "ldvh-workcase-stop.py"
STOP_IMPL = PROJECT_ROOT / "code" / "ldvh" / "hooks" / "workcase_stop.py"


def _run_git(worktree: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(worktree), *args],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def check_skill_copy(*, skill_path: str, platform: str, sync: bool, confirm_human_gate: bool) -> tuple[bool, dict]:
    target = Path(skill_path)
    target_exists = target.is_file()
    project_exists = PROJECT_SKILL.is_file()
    aligned = False
    if project_exists and target_exists:
        try:
            aligned = PROJECT_SKILL.read_bytes() == target.read_bytes()
        except OSError:
            aligned = False
    detail: dict = {
        "platform": platform,
        "target_path": str(target),
        "target_exists": target_exists,
        "is_ldvh_skill": bool(target_exists and _has_ldvh_frontmatter(target)),
        "target_version": _read_skill_version(target) if target_exists else None,
        "project_path": str(PROJECT_SKILL),
        "project_exists": project_exists,
        "project_version": _read_skill_version(PROJECT_SKILL) if project_exists else None,
        "aligned": aligned,
    }

    if sync and confirm_human_gate and project_exists:
        outcome = update_skill(
            platform=platform,
            skill_path=skill_path,
            source_path=PROJECT_SKILL,
            human_gate_confirmed=True,
        )
        detail["synced"] = outcome.replaced or outcome.created
        detail["aligned"] = outcome.aligned
    return bool(detail["aligned"]), detail


def check_skill_frontmatter(*, skill_path: str) -> tuple[bool, dict]:
    """Frontmatter legality gate: both the project canonical source and the
    named target must pass strict YAML validation.

    This is the check that a byte-alignment-only check cannot catch: runtime
    skill loaders silently DROP a SKILL.md whose frontmatter does not parse
    (e.g. a plain-scalar `: ` inside the description), so an otherwise
    byte-identical copy can be deployed-but-invisible.  A failed frontmatter
    here must block deployment/sync even when every byte matches.
    """
    project_exists = PROJECT_SKILL.is_file()
    target = Path(skill_path)
    target_exists = target.is_file()
    project_valid, project_error = (
        validate_skill_frontmatter(PROJECT_SKILL) if project_exists else (False, "项目源不存在")
    )
    target_valid, target_error = (
        validate_skill_frontmatter(target) if target_exists else (False, "目标不存在")
    )
    aligned = project_valid and target_valid
    return aligned, {
        "project_path": str(PROJECT_SKILL),
        "project_exists": project_exists,
        "project_frontmatter_valid": project_valid,
        "target_path": str(target),
        "target_exists": target_exists,
        "target_frontmatter_valid": target_valid,
        "error": project_error if project_error is not None else target_error,
    }


def check_hook_surface(common_hooks: Path) -> dict[str, dict]:
    surface = inspect_hook_surface(common_hooks=common_hooks)
    return {key: dict(value) for key, value in surface.items()}  # type: ignore[arg-type]


def check_stop_gate() -> tuple[bool, dict]:
    wrapper_ok = STOP_WRAPPER.is_file()
    impl_ok = STOP_IMPL.is_file()
    references_impl = False
    if wrapper_ok:
        try:
            text = STOP_WRAPPER.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            text = ""
        references_impl = "from ldvh.hooks.workcase_stop import main" in text
    aligned = wrapper_ok and impl_ok and references_impl
    return aligned, {
        "wrapper_path": str(STOP_WRAPPER),
        "wrapper_exists": wrapper_ok,
        "implementation_path": str(STOP_IMPL),
        "implementation_exists": impl_ok,
        "wrapper_references_implementation": references_impl,
    }


def check_worktree_coverage(worktree: Path) -> tuple[bool, dict]:
    lines_raw = _run_git(worktree, "worktree", "list", "--porcelain")
    if lines_raw is None:
        return False, {"error": "git worktree list failed; is this a git worktree?"}
    worktrees: list[str] = []
    current: dict = {}
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
    distinct = {c for c in common_dirs.values() if c != "unavailable"}
    aligned = len(distinct) <= 1
    return aligned, {
        "worktrees": worktrees,
        "common_dirs": common_dirs,
        "distinct_common_dirs": sorted(distinct),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--platform", required=True, help="当前 AI 平台标签（仅报告）")
    parser.add_argument("--skill-path", required=True, help="实际目标 Skill 绝对路径")
    parser.add_argument("--json", action="store_true", help="emit the report as JSON")
    parser.add_argument("--worktree", default=str(PROJECT_ROOT), help="target git worktree (default: project root)")
    parser.add_argument(
        "--sync",
        action="store_true",
        help="sync the named target from the project source (requires --confirm-human-gate)",
    )
    parser.add_argument(
        "--confirm-human-gate",
        action="store_true",
        help="explicit Human Gate confirmation; required for any write (--sync)",
    )
    args = parser.parse_args()

    if args.sync and not args.confirm_human_gate:
        print("error: --sync 需要显式 --confirm-human-gate；未确认前不写入任何字节", file=sys.stderr)
        return 2

    worktree = Path(args.worktree).resolve()
    common = _run_git(worktree, "rev-parse", "--git-common-dir")
    if common is None:
        print(f"error: {worktree} is not a git worktree", file=sys.stderr)
        return 2
    common_candidate = Path(common)
    common_dir = (
        common_candidate.resolve() if common_candidate.is_absolute() else (worktree / common_candidate).resolve()
    )
    common_hooks = common_dir / "hooks"

    skill_ok, skill_detail = check_skill_copy(
        skill_path=args.skill_path,
        platform=args.platform,
        sync=args.sync,
        confirm_human_gate=args.confirm_human_gate,
    )
    fm_ok, fm_detail = check_skill_frontmatter(skill_path=args.skill_path)
    hooks = check_hook_surface(common_hooks)
    hook_ok = bool(hooks["commit-msg"]["aligned"])
    stop_ok, stop_detail = check_stop_gate()
    wt_ok, wt_detail = check_worktree_coverage(worktree)

    checks = [
        ("skill", skill_ok, skill_detail),
        ("frontmatter", fm_ok, fm_detail),
        ("commit-msg", hook_ok, hooks["commit-msg"]),
        ("stop-gate", stop_ok, stop_detail),
        ("worktrees", wt_ok, wt_detail),
    ]
    all_ok = all(ok for _, ok, _ in checks)

    report = {
        "contract": CONTRACT,
        "platform": args.platform,
        "skill_path": args.skill_path,
        "worktree": str(worktree),
        "common_hooks_dir": str(common_hooks),
        "aligned": all_ok,
        "checks": [{"surface": name, "aligned": ok, "detail": detail} for name, ok, detail in checks],
    }

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"LDVH skill/hook alignment check ({CONTRACT})")
        print(f"platform: {report['platform']}")
        print(f"skill_path: {report['skill_path']}")
        print(f"worktree: {report['worktree']}")
        print(f"common hooks dir: {report['common_hooks_dir']}")
        print()
        for name, ok, detail in checks:
            mark = "OK " if ok else "MISALIGNED"
            print(f"[{mark}] {name}")
            for key, value in detail.items():
                print(f"    {key}: {value}")
        print()
        print("RESULT:", "ALIGNED" if all_ok else "MISALIGNED")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
