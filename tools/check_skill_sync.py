#!/usr/bin/env python3
"""Check LDVH skill/hook deployment alignment after a skill update.

Reads only; never writes, unless --sync is explicitly given.  Reports the
alignment of four surfaces so a "skill updated" event can be checked in one
command instead of hand-assembled steps:

1. skill copy: project skill/SKILL.md vs the user-level ~/.workbuddy/skills/ldvh/SKILL.md
2. commit-msg hook: state (managed/absent/conflict) and bundle version vs HOOK_BUNDLE_VERSION
3. prepare-commit-msg hook: retired asset state
4. Stop gate: .claude/hooks/ldvh-workcase-stop.py wrapper vs code/ldvh/hooks/workcase_stop.py
5. worktree coverage: every worktree shares the same git common-dir hooks boundary

Exit code 0 = all surfaces aligned; 1 = at least one misalignment; 2 = usage/environment error.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from ldvh.git_hooks.commit_msg import (  # noqa: E402
    _LAST_PREPARE_BUNDLE_VERSION,
    _MANAGED_MARKER_PREFIX,
    _PREPARE_MANAGED_MARKER_PREFIX,
    HOOK_BUNDLE_VERSION,
    _existing_hook_state,
    _hook_bundle_version,
)  # noqa: I001

CONTRACT = "ldvh-skill-sync-check/1"

USER_SKILL_DEFAULT = Path.home() / ".workbuddy" / "skills" / "ldvh" / "SKILL.md"
PROJECT_SKILL = PROJECT_ROOT / "skill" / "SKILL.md"
STOP_WRAPPER = PROJECT_ROOT / ".claude" / "hooks" / "ldvh-workcase-stop.py"
STOP_IMPL = PROJECT_ROOT / "code" / "ldvh" / "hooks" / "workcase_stop.py"


def _version_line(path: Path) -> str | None:
    """Extract the '> Skill 版本：...' marker from a SKILL.md, if present."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("> Skill 版本"):
            return stripped.removeprefix("> ").strip()
    return None


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


def check_skill_copy(*, sync: bool) -> tuple[bool, dict]:
    """Compare project skill source with the user-level installed copy."""
    project_exists = PROJECT_SKILL.is_file()
    user_exists = USER_SKILL_DEFAULT.is_file()
    same = False
    detail: dict = {
        "project_path": str(PROJECT_SKILL),
        "project_exists": project_exists,
        "user_path": str(USER_SKILL_DEFAULT),
        "user_exists": user_exists,
    }
    if project_exists and user_exists:
        same = PROJECT_SKILL.read_bytes() == USER_SKILL_DEFAULT.read_bytes()
    detail["aligned"] = same
    detail["project_version"] = _version_line(PROJECT_SKILL) if project_exists else None
    detail["user_version"] = _version_line(USER_SKILL_DEFAULT) if user_exists else None

    if sync and project_exists and not same:
        USER_SKILL_DEFAULT.parent.mkdir(parents=True, exist_ok=True)
        USER_SKILL_DEFAULT.write_bytes(PROJECT_SKILL.read_bytes())
        detail["synced"] = True
        detail["aligned"] = True
    return bool(detail["aligned"]), detail


def check_commit_msg_hook(common_hooks: Path) -> tuple[bool, dict]:
    hook = common_hooks / "commit-msg"
    state, detail_text = _existing_hook_state(hook, name="commit-msg", marker_prefix=_MANAGED_MARKER_PREFIX)
    deployed_version = _hook_bundle_version(hook) if hook.is_file() else None
    aligned = state == "managed" and deployed_version == HOOK_BUNDLE_VERSION
    return aligned, {
        "path": str(hook),
        "state": state,
        "detail": detail_text,
        "deployed_bundle_version": deployed_version,
        "expected_bundle_version": HOOK_BUNDLE_VERSION,
    }


def check_prepare_hook(common_hooks: Path) -> tuple[bool, dict]:
    hook = common_hooks / "prepare-commit-msg"
    state, detail_text = _existing_hook_state(
        hook, name="prepare-commit-msg", marker_prefix=_PREPARE_MANAGED_MARKER_PREFIX
    )
    deployed_version = _hook_bundle_version(hook) if hook.is_file() else None
    # Retired asset: absent is the expected end state; a managed legacy copy is
    # acceptable (eligible for removal), anything else is a misalignment.
    aligned = state in {"absent", "managed"}
    return aligned, {
        "path": str(hook),
        "state": state,
        "detail": detail_text,
        "deployed_bundle_version": deployed_version,
        "expected_bundle_version": _LAST_PREPARE_BUNDLE_VERSION,
    }


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
            common_dirs[wt] = str((Path(wt) / common).resolve()) if not Path(common).is_absolute() else common
    distinct = {c for c in common_dirs.values() if c != "unavailable"}
    aligned = len(distinct) <= 1
    return aligned, {
        "worktrees": worktrees,
        "common_dirs": common_dirs,
        "distinct_common_dirs": sorted(distinct),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sync", action="store_true", help="sync the user-level skill copy from the project source")
    parser.add_argument("--json", action="store_true", help="emit the report as JSON")
    parser.add_argument("--worktree", default=str(PROJECT_ROOT), help="target git worktree (default: project root)")
    args = parser.parse_args()

    worktree = Path(args.worktree).resolve()
    common = _run_git(worktree, "rev-parse", "--git-common-dir")
    if common is None:
        print(f"error: {worktree} is not a git worktree", file=sys.stderr)
        return 2
    common_hooks = (worktree / common).resolve() / "hooks"

    skill_ok, skill_detail = check_skill_copy(sync=args.sync)
    hook_ok, hook_detail = check_commit_msg_hook(common_hooks)
    prepare_ok, prepare_detail = check_prepare_hook(common_hooks)
    stop_ok, stop_detail = check_stop_gate()
    wt_ok, wt_detail = check_worktree_coverage(worktree)

    checks = [
        ("skill", skill_ok, skill_detail),
        ("commit-msg", hook_ok, hook_detail),
        ("prepare-commit-msg", prepare_ok, prepare_detail),
        ("stop-gate", stop_ok, stop_detail),
        ("worktrees", wt_ok, wt_detail),
    ]
    all_ok = all(ok for _, ok, _ in checks)

    report = {
        "contract": CONTRACT,
        "worktree": str(worktree),
        "common_hooks_dir": str(common_hooks),
        "aligned": all_ok,
        "checks": [{"surface": name, "aligned": ok, "detail": detail} for name, ok, detail in checks],
    }

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"LDVH skill/hook alignment check ({CONTRACT})")
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
