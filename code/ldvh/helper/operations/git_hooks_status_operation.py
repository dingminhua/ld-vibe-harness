"""Read-only Helper operation: git-hooks-status.

Inspect the common-dir Git Hook deployment state, deployed vs expected bundle
versions, the worktrees sharing that common-dir, the project skill copy
alignment, and the project Stop gate wrapper/implementation consistency for a
governed worktree.  It never writes a fact, never deploys a Hook and never
syncs a skill copy.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ldvh.git_hooks.commit_msg import (
    _LAST_PREPARE_BUNDLE_VERSION,
    _MANAGED_MARKER_PREFIX,
    _PREPARE_MANAGED_MARKER_PREFIX,
    HOOK_BUNDLE_VERSION,
    _existing_hook_state,
    _hook_bundle_version,
)
from ldvh.governance.models import LocatorSource, ScopeDescriptor
from ldvh.governance.resolver import resolve_governance_scope
from ldvh.helper.operation_runtime import (
    AvailabilityEvaluation,
    OperationExecution,
    OperationExecutionContext,
    OperationImplementation,
    OperationRequestError,
)
from ldvh.helper.operations.fact_operation_support import plain, reading_boundary
from ldvh.helper.requests import CommonRequest
from ldvh.helper.responses import source_reference
from ldvh.specs.repository import RepositoryInspection

OPERATION_KEY = "git-hooks-status"
REQUIRED_INPUTS: tuple[str, ...] = ()
OPTIONAL_INPUTS: tuple[str, ...] = ("work_object_locators",)
_CONTRACT = source_reference(
    "rule",
    "environment-integration::5.9.1 Git Hook 部署状态只读检查输入",
)
_RESULT_CONTRACT = source_reference(
    "rule",
    "environment-integration::5.9.2 Git Hook 部署状态只读检查结果",
)
_IMPLEMENTATION_EVIDENCE = (
    source_reference(
        "implementation",
        "code/ldvh/helper/operations/git_hooks_status_operation.py",
    ),
    source_reference("implementation", "code/ldvh/git_hooks/commit_msg.py"),
)

_PROJECT_SKILL_REL = Path("skill") / "SKILL.md"
_USER_SKILL_REL = Path(".workbuddy") / "skills" / "ldvh" / "SKILL.md"


def _validated_locator(
    request: CommonRequest,
    context: OperationExecutionContext,
) -> str | None:
    """Return exactly one worktree locator, or None to fall back to cwd."""
    problems: list[str] = []
    locator: str | None = None
    if request.task is not None:
        problems.append("git-hooks-status 不接受 task")
    if request.arguments:
        problems.append("git-hooks-status 不接受 arguments")
    if request.requested_disclosure is not None:
        problems.append("git-hooks-status 不接受 requested_disclosure")
    if request.observed_context:
        problems.append("git-hooks-status 不接受 observed_context")
    if request.authorization_reference:
        problems.append("git-hooks-status 不接受 authorization_reference")
    if request.work_object_locators:
        if len(request.work_object_locators) != 1:
            problems.append("work_object_locators 必须恰有一个目标路径 string")
        else:
            raw = request.work_object_locators[0]
            if not isinstance(raw, str) or not raw.strip():
                problems.append("work_object_locators[0] 必须是非空路径 string")
            else:
                locator = raw
    if problems:
        raise OperationRequestError(tuple(problems), sources=(_CONTRACT,))
    return locator if locator is not None else str(context.cwd)


def _run_git(worktree: Path, *args: str) -> str | None:
    import subprocess

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


def _version_line(path: Path) -> str | None:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("> Skill 版本"):
            return stripped.removeprefix("> ").strip()
    return None


def _skill_check(project_root: Path) -> dict[str, Any]:
    project_skill = project_root / _PROJECT_SKILL_REL
    user_skill = Path.home() / _USER_SKILL_REL
    project_exists = project_skill.is_file()
    user_exists = user_skill.is_file()
    aligned = False
    if project_exists and user_exists:
        try:
            aligned = project_skill.read_bytes() == user_skill.read_bytes()
        except OSError:
            aligned = False
    return {
        "aligned": aligned,
        "project_path": str(project_skill),
        "project_exists": project_exists,
        "project_version": _version_line(project_skill) if project_exists else None,
        "user_path": str(user_skill),
        "user_exists": user_exists,
        "user_version": _version_line(user_skill) if user_exists else None,
    }


def _stop_gate_check(project_root: Path) -> dict[str, Any]:
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


def _worktree_check(worktree: Path) -> dict[str, Any]:
    lines_raw = _run_git(worktree, "worktree", "list", "--porcelain")
    if lines_raw is None:
        return {"aligned": False, "error": "git worktree list failed"}
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
    aligned = len(distinct) <= 1
    return {
        "aligned": aligned,
        "worktrees": worktrees,
        "common_dirs": common_dirs,
        "distinct_common_dirs": sorted(distinct),
    }


def _hook_check(
    common_hooks: Path,
    name: str,
    marker_prefix: str,
    expected_version: str,
) -> dict[str, Any]:
    hook = common_hooks / name
    state, detail = _existing_hook_state(hook, name=name, marker_prefix=marker_prefix)
    deployed = _hook_bundle_version(hook) if hook.is_file() else None
    if name == "prepare-commit-msg":
        aligned = state in {"absent", "managed"}
    else:
        aligned = state == "managed" and deployed == expected_version
    return {
        "aligned": aligned,
        "path": str(hook),
        "state": state,
        "detail": detail,
        "deployed_bundle_version": deployed,
        "expected_bundle_version": expected_version,
    }


def _execute(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> OperationExecution:
    try:
        locator = _validated_locator(request, context)
    except OperationRequestError:
        return OperationExecution(
            outcome="invalid_request",
            summary="Helper 请求不符合 5.9.1 输入契约",
            requested_scope=(),
            not_completed_scope=(),
            gaps=(),
            diagnostics=(),
        )


    base = context.cwd
    requested_scope = (ScopeDescriptor(0, locator, LocatorSource.EXPLICIT_LOCATOR),)
    run = resolve_governance_scope(requested_scope, base=base, explicit_workspace_root=None)
    boundary = reading_boundary(run)
    sources: tuple[Any, ...] = (_CONTRACT, _RESULT_CONTRACT, *_IMPLEMENTATION_EVIDENCE)

    if boundary is None:
        return OperationExecution(
            outcome="unavailable",
            summary="当前管辖结果不能形成唯一 worktree 检查边界",
            requested_scope=(locator,),
            not_completed_scope=(locator,),
            governance_resolution=None if run.result is None else run.result.to_json(),
            sources=(*tuple(plain(source) for source in run.sources), *sources),
            gaps=(
                {
                    "summary": "无法按 locator 或 cwd 解析唯一受管辖 worktree",
                    "scope": [locator],
                    "source_refs": [plain(source) for source in run.sources],
                },
            ),
        )

    project_id, root, common_dir = boundary
    worktree = root
    common_hooks = common_dir / "hooks"

    skill = _skill_check(root)
    stop_gate = _stop_gate_check(root)
    commit_msg = _hook_check(common_hooks, "commit-msg", _MANAGED_MARKER_PREFIX, HOOK_BUNDLE_VERSION)
    prepare = _hook_check(
        common_hooks,
        "prepare-commit-msg",
        _PREPARE_MANAGED_MARKER_PREFIX,
        _LAST_PREPARE_BUNDLE_VERSION,
    )
    worktrees = _worktree_check(root)

    checks = [
        {"surface": "commit-msg", "aligned": commit_msg["aligned"], "detail": commit_msg},
        {"surface": "prepare-commit-msg", "aligned": prepare["aligned"], "detail": prepare},
        {"surface": "skill", "aligned": skill["aligned"], "detail": skill},
        {"surface": "stop-gate", "aligned": stop_gate["aligned"], "detail": stop_gate},
        {"surface": "worktrees", "aligned": worktrees["aligned"], "detail": worktrees},
    ]
    aligned = all(check["aligned"] for check in checks)

    return OperationExecution(
        outcome="ok",
        summary="已完成 Git Hook 部署状态、skill 副本对齐与 Stop gate 一致性的只读机械检查",
        requested_scope=(locator,),
        completed_scope=(locator,),
        governance_resolution=None if run.result is None else run.result.to_json(),
        sources=sources,
        result={
            "status": "aligned" if aligned else "misaligned",
            "worktree": str(worktree),
            "common_hooks_dir": str(common_hooks),
            "checks": checks,
        },
    )


def _check_availability(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> AvailabilityEvaluation:
    return AvailabilityEvaluation(
        available=True,
        detail="git-hooks-status 已实现，零输入或单一 worktree locator 可调用",
    )


def _call(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> OperationExecution:
    return _execute(request, repository, context)


GIT_HOOKS_STATUS_IMPLEMENTATION = OperationImplementation(
    required_inputs=REQUIRED_INPUTS,
    optional_inputs=OPTIONAL_INPUTS,
    evidence=(*_IMPLEMENTATION_EVIDENCE, _CONTRACT, _RESULT_CONTRACT),
    check_availability=_check_availability,
    call=_call,
)

__all__ = ["GIT_HOOKS_STATUS_IMPLEMENTATION", "OPERATION_KEY"]
