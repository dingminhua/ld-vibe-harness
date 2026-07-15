"""Boundary-bound V4 Spark reads for the unmounted Web bridge."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Literal

from ldvh.facts.candidate_discovery import (
    MAX_WEB_FACT_AGGREGATE_BYTES,
    FactTypeRawSnapshot,
    discover_fact_type_raw,
)
from ldvh.facts.creation import CreationBoundary
from ldvh.facts.repository import FactReadResult
from ldvh.facts.schema import FactSchema

WebSparkListStatus = Literal["complete", "partial", "unavailable", "integrity_conflict"]
WebSparkDetailStatus = Literal["ok", "not_found", "invalid", "unavailable"]
MAX_WEB_SPARK_RAW_BYTES = MAX_WEB_FACT_AGGREGATE_BYTES
MAX_WEB_SPARK_PROJECTED_BYTES = 16 * 1024 * 1024


@dataclass(frozen=True, slots=True)
class WebSparkListResult:
    status: WebSparkListStatus
    items: tuple[dict[str, Any], ...] = ()
    object_problems: tuple[dict[str, Any], ...] = ()
    structural_problems: tuple[dict[str, object], ...] = ()


@dataclass(frozen=True, slots=True)
class WebSparkDetailResult:
    status: WebSparkDetailStatus
    item: dict[str, Any] | None = None
    problems: tuple[dict[str, Any], ...] = ()
    coverage_status: WebSparkListStatus = "complete"


def _issues(read: FactReadResult) -> list[dict[str, object | None]]:
    return [
        {
            "category": issue.category,
            "field_path": issue.field_path,
            "summary": issue.summary,
        }
        for issue in read.issues
    ]


def _read_item(boundary: CreationBoundary, object_id: str, read: FactReadResult) -> dict[str, Any]:
    return {
        "object_ref": {
            "governed_project_id": boundary.governed_project_id,
            "fact_type_key": "spark",
            "object_id": object_id,
        },
        "canonical_path": read.canonical_path,
        "absolute_path": str(boundary.worktree_root / read.canonical_path),
        "carrier": read.carrier,
        "check_status": read.check_status,
        "fact_object": read.fields if read.check_status == "mechanically_valid" else None,
        "content_fingerprint": read.content_fingerprint if read.check_status == "mechanically_valid" else None,
        "issues": _issues(read),
    }


def _structural_integrity(snapshot: FactTypeRawSnapshot) -> bool:
    for problem in snapshot.structural_problems:
        for issue in problem.get("issues", []):
            if isinstance(issue, dict) and "canonical" in str(issue.get("summary", "")):
                return True
    return False


def _list_from_snapshot(boundary: CreationBoundary, snapshot: FactTypeRawSnapshot) -> WebSparkListResult:
    items: list[dict[str, Any]] = []
    problems: list[dict[str, Any]] = []
    structural = list(snapshot.structural_problems)
    projected_bytes = 0
    for object_id, read in snapshot.objects:
        item = _read_item(boundary, object_id, read)
        encoded_bytes = len(json.dumps(item, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
        if projected_bytes + encoded_bytes > MAX_WEB_SPARK_PROJECTED_BYTES:
            structural.append(
                {
                    "fact_type_key": "spark",
                    "canonical_path": "facts/sparks",
                    "check_status": "unavailable",
                    "issues": [
                        {
                            "category": "budget",
                            "field_path": None,
                            "summary": (f"Spark Web 读取结果超过 {MAX_WEB_SPARK_PROJECTED_BYTES} bytes 聚合预算"),
                        }
                    ],
                }
            )
            break
        projected_bytes += encoded_bytes
        if read.check_status == "mechanically_valid" and read.fields is not None:
            items.append(item)
        else:
            problems.append(item)
    if structural:
        structural_snapshot = FactTypeRawSnapshot(
            snapshot.fact_type_key,
            snapshot.objects,
            tuple(structural),
            False,
        )
        status: WebSparkListStatus = (
            "integrity_conflict" if _structural_integrity(structural_snapshot) else "unavailable"
        )
    elif problems or not snapshot.coverage_complete:
        status = "partial"
    else:
        status = "complete"
    return WebSparkListResult(status, tuple(items), tuple(problems), tuple(structural))


def read_web_spark_list(
    boundary: CreationBoundary,
    schemas: dict[str, FactSchema],
) -> WebSparkListResult:
    """Read every canonical V4 Spark and preserve incomplete coverage explicitly."""

    snapshot = discover_fact_type_raw(
        boundary.worktree_root,
        boundary.governed_project_id,
        boundary.git_common_dir,
        schemas,
        "spark",
        aggregate_budget_bytes=MAX_WEB_SPARK_RAW_BYTES,
    )
    return _list_from_snapshot(boundary, snapshot)


def read_web_spark_detail(
    boundary: CreationBoundary,
    schemas: dict[str, FactSchema],
    object_id: str,
) -> WebSparkDetailResult:
    """Read one exact V4 Spark without treating incomplete coverage as absence."""

    snapshot = discover_fact_type_raw(
        boundary.worktree_root,
        boundary.governed_project_id,
        boundary.git_common_dir,
        schemas,
        "spark",
        aggregate_budget_bytes=MAX_WEB_SPARK_RAW_BYTES,
    )
    listed = _list_from_snapshot(boundary, snapshot)
    for current_id, read in snapshot.objects:
        if current_id != object_id:
            continue
        item = _read_item(boundary, current_id, read)
        if read.check_status == "mechanically_valid" and read.fields is not None:
            return WebSparkDetailResult("ok", item, coverage_status=listed.status)
        status: WebSparkDetailStatus = "invalid" if read.check_status == "invalid" else "unavailable"
        return WebSparkDetailResult(status, problems=(item,), coverage_status=listed.status)
    if listed.status != "complete":
        problems = (*listed.object_problems, *listed.structural_problems)
        return WebSparkDetailResult("unavailable", problems=problems, coverage_status=listed.status)
    return WebSparkDetailResult("not_found")


__all__ = [
    "WebSparkDetailResult",
    "WebSparkListResult",
    "read_web_spark_detail",
    "read_web_spark_list",
]
