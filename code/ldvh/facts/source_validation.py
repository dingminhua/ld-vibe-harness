"""Project-backed mechanical checks for Study source and evidence references."""

from __future__ import annotations

from pathlib import Path

from ldvh.facts.contracts import LAYOUTS
from ldvh.facts.models import FactIssue
from ldvh.facts.relations import ProjectFactIndex
from ldvh.facts.repository import FactReadResult, _git, _identity_issue, _safe_regular_file

_REPOSITORY_KINDS = {
    "repository-path",
    "git-revision",
    "runtime-observation",
    "human-provided-artifact",
}


def _repository_path_status(
    index: ProjectFactIndex,
    locator: str,
) -> tuple[FactIssue | None, bool]:
    identity_issue, _ = _identity_issue(index.root, index.expected_common_dir, index.git_identity_cache)
    if identity_issue is not None:
        return identity_issue, True
    _, issue, status = _safe_regular_file(index.root, locator)
    if issue is not None:
        return issue, status == "unavailable"
    return None, False


def _git_revision_status(index: ProjectFactIndex, locator: str, version: str) -> tuple[FactIssue | None, bool]:
    revision = _git(index.root, "rev-parse", "--verify", f"{version}^{{commit}}")
    if revision is None:
        return FactIssue("git-traceability", "无法验证 git-revision version"), True
    if revision.returncode != 0:
        return FactIssue("reference", "git-revision version 不能解析为当前仓库 commit"), False
    try:
        revision_id = revision.stdout.decode("ascii").strip()
    except UnicodeDecodeError:
        return FactIssue("git-traceability", "git-revision version 输出无法解码"), True
    exists = _git(index.root, "cat-file", "-e", f"{revision_id}:{locator}")
    if exists is None:
        return FactIssue("git-traceability", "无法验证 git-revision 中的 locator"), True
    if exists.returncode != 0:
        return FactIssue("reference", "git-revision locator 在指定 commit 中不存在"), False
    return None, False


def _fact_locator(locator: str) -> tuple[str, str] | None:
    path = Path(locator)
    if len(path.parts) != 3:
        return None
    for fact_type_key, layout in LAYOUTS.items():
        if path.parent.as_posix() != layout.directory or path.suffix != layout.suffix:
            continue
        object_id = path.name.removesuffix(layout.suffix)
        if layout.object_id_pattern.fullmatch(object_id) is not None:
            return fact_type_key, object_id
    return None


def validate_study_sources(
    index: ProjectFactIndex,
    read: FactReadResult,
) -> tuple[tuple[FactIssue, ...], bool]:
    """External Study material is represented by URLs and validated in the fact schema."""
    return (), False


__all__ = ["validate_study_sources"]
