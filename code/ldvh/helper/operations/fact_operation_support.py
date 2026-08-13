"""Shared adapters for fact operations without granting public behavior."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path
from typing import Any

from ldvh.facts.candidate_discovery import discover_fact_candidates
from ldvh.facts.configuration_index import ConfigurationFactIndex
from ldvh.facts.contracts import LAYOUTS
from ldvh.facts.identity import canonical_object_uid
from ldvh.governance.models import ObjectStatus
from ldvh.governance.resolver import GovernanceResolutionRun
from ldvh.helper.operation_runtime import OperationExecution
from ldvh.testing.fact_integrity import assess_fact_snapshot


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


def configuration_reading_boundaries(
    run: GovernanceResolutionRun,
) -> tuple[tuple[str, Path, Path], ...] | None:
    """Return every validated project in the one selected configuration."""

    if run.result is None or run.technical_non_completions or len(run.completed_scope) != len(run.requested_scope):
        return None
    candidates = run.result.registered_project_candidates
    if not candidates:
        return None
    selected = reading_boundary(run)
    boundaries: list[tuple[str, Path, Path]] = []
    for candidate in candidates:
        if selected is not None and candidate.governed_project_id == selected[0]:
            boundaries.append(selected)
            continue
        if candidate.git_worktree_root is None or candidate.git_common_dir is None:
            return None
        boundaries.append(
            (
                candidate.governed_project_id,
                Path(candidate.git_worktree_root),
                Path(candidate.git_common_dir),
            )
        )
    return tuple(boundaries)


def post_write_integrity_audit(
    execution: OperationExecution,
    *,
    boundary: Any,
    schemas: dict[str, Any],
    audit_contract: dict[str, Any],
    configuration_boundaries: tuple[tuple[str, Path, Path], ...] | None = None,
) -> OperationExecution:
    """Attach the independent whole-library audit required after a fact write.

    The writer has already completed its type-specific atomic write and exact
    readback.  This deliberately uses the same whole-library integrity core as
    the public check-fact-integrity operation, instead of treating that local
    readback as a substitute for an independent audit.
    """
    if set(schemas) != set(LAYOUTS):
        status = "unavailable"
        problems: list[dict[str, Any]] = [{"summary": "当前规则源不能形成五类型完整派生 Schema"}]
    else:
        boundaries = configuration_boundaries or (
            (boundary.governed_project_id, boundary.worktree_root, boundary.git_common_dir),
        )
        configuration_index = ConfigurationFactIndex(boundaries, schemas)
        if not configuration_index.prepare():
            status = "unavailable"
            problems = [{"summary": "配置级 UID 全扫描未能完整形成"}]
        else:
            snapshots = tuple(
                discover_fact_candidates(root, project_id, common_dir, schemas, index=index)
                for project_id, root, common_dir, index in configuration_index.project_indexes
            )
            assessed = tuple(assess_fact_snapshot(snapshot) for snapshot in snapshots)
            status = (
                "unavailable"
                if any(item_status == "unavailable" for item_status, _ in assessed)
                else "partial"
                if any(item_status != "complete" for item_status, _ in assessed)
                else "complete"
            )
            problems = [problem for _item_status, item_problems in assessed for problem in item_problems]
            uid_counts: dict[str, int] = {}
            for snapshot in snapshots:
                for key in snapshot.keys:
                    read = snapshot.index.cache[key]
                    object_uid = canonical_object_uid(None if read.fields is None else read.fields.get("object_uid"))
                    if object_uid is not None:
                        uid_counts[object_uid] = uid_counts.get(object_uid, 0) + 1
            duplicates = sorted(uid for uid, count in uid_counts.items() if count > 1)
            if duplicates and status == "complete":
                status = "partial"
            problems.extend({"summary": f"object_uid 在当前选定管辖配置中重复: {uid}"} for uid in duplicates)

    audit = {
        "check": "事实写入后的独立全库机械完整性审计",
        "status": "passed" if status == "complete" else status,
        "scope": list(execution.requested_scope),
        "evidence": [audit_contract],
    }
    sources = (*execution.sources, audit_contract)
    if status == "complete":
        return replace(execution, sources=sources, verification=(*execution.verification, audit))

    gap = {
        "summary": "事实写入已发生，但写后独立完整性审计未达到 complete；不得继续事实写入、提交或声明成功",
        "scope": list(execution.requested_scope),
        "source_refs": [audit_contract],
        "code": "post_write_integrity_incomplete",
    }
    # The atomic write and its exact target readback remain true observations.
    # The incomplete independent audit is recorded separately, so callers can
    # neither omit it nor collapse it into the writer's own success claim.
    return replace(
        execution,
        sources=sources,
        gaps=(*execution.gaps, gap),
        verification=(*execution.verification, audit),
    )


__all__ = ["configuration_reading_boundaries", "plain", "post_write_integrity_audit", "reading_boundary"]
