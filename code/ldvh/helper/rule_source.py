"""Helper compatibility wrapper around the shared verified rule repository."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ldvh.helper.operation_sources import OperationSourceInspection, inspect_operation_sources
from ldvh.rule_snapshot import validate_installed_snapshot
from ldvh.rule_source import inspect_colocated_rule_repository, locate_colocated_repository
from ldvh.specs.repository import RepositoryInspection


@dataclass(frozen=True, slots=True)
class RuleSourceResult:
    repository: RepositoryInspection | None
    operations: OperationSourceInspection | None
    problem: str | None


def inspect_colocated_rule_source(package_file: Path) -> RuleSourceResult:
    shared = inspect_colocated_rule_repository(package_file)
    if shared.repository is None:
        return RuleSourceResult(None, None, shared.problem)
    repository = shared.repository
    operations = inspect_operation_sources(repository)
    return RuleSourceResult(repository, operations, None)


__all__ = [
    "RuleSourceResult",
    "inspect_colocated_rule_source",
    "locate_colocated_repository",
    "validate_installed_snapshot",
]
