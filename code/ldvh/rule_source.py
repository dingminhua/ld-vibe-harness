"""Locate the verified rule repository colocated with the imported package."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ldvh.rule_snapshot import SnapshotError, inspect_verified_snapshot, validate_installed_snapshot
from ldvh.specs.discovery import validate_exact_worktree_root
from ldvh.specs.repository import RepositoryInspection, inspect_repository


@dataclass(frozen=True, slots=True)
class RuleRepositoryResult:
    repository: RepositoryInspection | None
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


def inspect_colocated_rule_repository(package_file: Path) -> RuleRepositoryResult:
    """Inspect the working-tree source or the verified installed snapshot."""

    structural_root = _structural_worktree_root(package_file)
    if structural_root is not None:
        issue = validate_exact_worktree_root(structural_root)
        if issue is not None:
            problem = f"导入的 ldvh Code 具有 Working Tree 结构但无法确认其 Git 根：{issue.summary}"
            return RuleRepositoryResult(None, problem)
        repository = inspect_repository(structural_root)
    else:
        try:
            snapshot = validate_installed_snapshot(package_file)
            repository = inspect_verified_snapshot(snapshot)
        except (OSError, SnapshotError, ValueError) as exc:
            return RuleRepositoryResult(None, f"安装规则快照不可用：{exc}")
    return RuleRepositoryResult(repository, None)


__all__ = ["RuleRepositoryResult", "inspect_colocated_rule_repository", "locate_colocated_repository"]
