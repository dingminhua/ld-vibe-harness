"""Locate and inspect the rule source colocated with the imported Code package."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ldvh.helper.operation_sources import OperationSourceInspection, inspect_operation_sources
from ldvh.specs.discovery import validate_exact_worktree_root
from ldvh.specs.repository import RepositoryInspection, inspect_repository


@dataclass(frozen=True, slots=True)
class RuleSourceResult:
    repository: RepositoryInspection | None
    operations: OperationSourceInspection | None
    problem: str | None


def locate_colocated_repository(package_file: Path) -> Path | None:
    root = _structural_worktree_root(package_file)
    if root is None or validate_exact_worktree_root(root) is not None:
        return None
    return root


def _structural_worktree_root(package_file: Path) -> Path | None:
    try:
        package_directory = package_file.resolve(strict=True).parent
    except OSError:
        return None
    for candidate in package_directory.parents:
        try:
            expected = (candidate / "code/ldvh").resolve(strict=True)
        except OSError:
            continue
        if expected == package_directory:
            return candidate
    return None


def inspect_colocated_repository(package_file: Path) -> RuleSourceResult:
    """Inspect only the current rule repository colocated with imported Code."""

    structural_root = _structural_worktree_root(package_file)
    if structural_root is None:
        return RuleSourceResult(None, None, "无法从导入的 ldvh Code 唯一确认源码 Git Working Tree")
    issue = validate_exact_worktree_root(structural_root)
    if issue is not None:
        problem = f"导入的 ldvh Code 具有 Working Tree 结构但无法确认其 Git 根：{issue.summary}"
        return RuleSourceResult(None, None, problem)
    repository = inspect_repository(structural_root)
    return RuleSourceResult(repository, None, None)


def inspect_colocated_rule_source(package_file: Path) -> RuleSourceResult:
    """Inspect the colocated rule repository and Helper operation declarations."""

    result = inspect_colocated_repository(package_file)
    if result.problem is not None or result.repository is None:
        return result
    return RuleSourceResult(result.repository, inspect_operation_sources(result.repository), None)
