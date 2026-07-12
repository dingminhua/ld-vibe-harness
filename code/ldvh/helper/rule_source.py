"""Locate and inspect the rule source colocated with the imported Code package."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ldvh.helper.operation_sources import OperationSourceInspection, inspect_operation_sources
from ldvh.specs.repository import RepositoryInspection, inspect_repository


@dataclass(frozen=True, slots=True)
class RuleSourceResult:
    repository: RepositoryInspection | None
    operations: OperationSourceInspection | None
    problem: str | None


def locate_colocated_repository(package_file: Path) -> Path | None:
    package_directory = package_file.resolve().parent
    for candidate in package_directory.parents:
        if (candidate / "code/ldvh").resolve() != package_directory:
            continue
        if not (candidate / "specs/00-理念与构成.md").is_file():
            continue
        return candidate
    return None


def inspect_colocated_rule_source(package_file: Path) -> RuleSourceResult:
    root = locate_colocated_repository(package_file)
    if root is None:
        return RuleSourceResult(None, None, "导入的 ldvh Code 未与可定位的 LDVH Working Tree 规则源共置")
    repository = inspect_repository(root)
    operations = inspect_operation_sources(repository)
    return RuleSourceResult(repository, operations, None)
