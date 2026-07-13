"""Shared adapters for fact operations without granting public behavior."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ldvh.governance.models import ObjectStatus
from ldvh.governance.resolver import GovernanceResolutionRun


def plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): plain(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [plain(item) for item in value]
    return value


def reading_boundary(run: GovernanceResolutionRun) -> tuple[str, Path, Path] | None:
    if run.result is None or run.technical_non_completions or len(run.completed_scope) != len(run.requested_scope):
        return None
    resolutions = run.result.object_resolutions
    if len(resolutions) != len(run.requested_scope) or any(
        item.status is not ObjectStatus.GOVERNED for item in resolutions
    ):
        return None
    project_ids = {item.governed_project_id for item in resolutions}
    roots = {item.git_worktree_root for item in resolutions}
    common_dirs = {item.git_common_dir for item in resolutions}
    if (
        len(project_ids) != 1
        or len(roots) != 1
        or len(common_dirs) != 1
        or None in project_ids
        or None in roots
        or None in common_dirs
    ):
        return None
    return (
        next(iter(project_ids)),
        Path(next(iter(roots))),  # type: ignore[arg-type]
        Path(next(iter(common_dirs))),  # type: ignore[arg-type]
    )


__all__ = ["plain", "reading_boundary"]
