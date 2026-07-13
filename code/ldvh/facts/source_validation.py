"""Project-backed mechanical checks for Study source and evidence references."""

from __future__ import annotations

from pathlib import Path

from ldvh.facts.contracts import LAYOUTS
from ldvh.facts.models import FactIssue
from ldvh.facts.relations import ProjectFactIndex
from ldvh.facts.repository import FactReadResult, _git, _identity_issue, _safe_regular_file, _traceability

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
    identity_issue, _ = _identity_issue(index.root, index.expected_common_dir)
    if identity_issue is not None:
        return identity_issue, True
    _, issue, status = _safe_regular_file(index.root, locator)
    if issue is not None:
        return issue, status == "unavailable"
    issue, status = _traceability(index.root, locator)
    return issue, status == "unavailable"


def _git_revision_status(index: ProjectFactIndex, locator: str, version: str) -> tuple[FactIssue | None, bool]:
    revision = _git(index.root, "rev-parse", "--verify", f"{version}^{{commit}}")
    if revision is None:
        return FactIssue("git-traceability", "无法验证 git-revision version"), True
    if revision.returncode != 0:
        return FactIssue("reference", "git-revision version 不能解析为当前仓库 commit"), False
    exists = _git(index.root, "cat-file", "-e", f"{revision.stdout.strip()}:{locator}")
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
    """Validate only source properties explicitly observable in the governed repository."""

    assert read.fields is not None
    issues: list[FactIssue] = []
    unavailable = False
    for array_name in ("source_refs", "evidence_refs"):
        references = read.fields.get(array_name)
        if not isinstance(references, list):
            continue
        for reference_index, reference in enumerate(references):
            if not isinstance(reference, dict):
                continue
            kind = reference.get("kind")
            locator = reference.get("locator")
            if not isinstance(kind, str) or not isinstance(locator, str):
                continue
            path = f"{array_name}[{reference_index}].locator"
            issue: FactIssue | None = None
            technical = False
            if kind == "fact-object":
                target = _fact_locator(locator)
                if target is not None:
                    target_read = index.read(*target)
                    if target_read is None or target_read.check_status in {"not_found", "invalid"}:
                        issue = FactIssue("reference", "fact-object locator 不是当前 mechanically valid 对象", path)
                    elif target_read.check_status == "unavailable":
                        technical = True
            elif kind in _REPOSITORY_KINDS:
                issue, technical = _repository_path_status(index, locator)
                if issue is not None:
                    issue = FactIssue(issue.category, issue.summary, path)
                if issue is None and not technical and kind == "git-revision":
                    version = reference.get("version")
                    if isinstance(version, str):
                        issue, technical = _git_revision_status(index, locator, version)
                        if issue is not None:
                            issue = FactIssue(issue.category, issue.summary, path)
            if issue is not None:
                issues.append(issue)
            unavailable = unavailable or technical
    return tuple(issues), unavailable


__all__ = ["validate_study_sources"]
