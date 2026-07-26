"""Web-owned projection orchestration over reusable LDVH fact reads."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from ldvh.facts.contracts import LAYOUTS
from ldvh.facts.creation import CreationBoundary
from ldvh.facts.project_validation import stabilize_project_index
from ldvh.facts.relations import MAX_GRAPH_OBJECTS, ProjectFactIndex
from ldvh.facts.repository import FactReadResult, _identity_issue
from ldvh.facts.schema import FactSchema
from ldvh.filesystem import safe_list_directory

WebFactListStatus = Literal["complete", "partial", "unavailable"]
WebFactDetailStatus = Literal["ok", "not_found", "invalid", "unavailable"]
MAX_WEB_FACT_AGGREGATE_BYTES = 16 * 1024 * 1024
MAX_WEB_SPARK_RAW_BYTES = MAX_WEB_FACT_AGGREGATE_BYTES
MAX_WEB_SPARK_PROJECTED_BYTES = 16 * 1024 * 1024
MAX_WEB_WORKCASE_RAW_BYTES = MAX_WEB_FACT_AGGREGATE_BYTES
MAX_WEB_WORKCASE_PROJECTED_BYTES = 16 * 1024 * 1024


@dataclass(frozen=True, slots=True)
class WebFactListResult:
    status: WebFactListStatus
    items: tuple[dict[str, Any], ...] = ()
    object_problems: tuple[dict[str, Any], ...] = ()
    structural_problems: tuple[dict[str, object], ...] = ()


@dataclass(frozen=True, slots=True)
class WebFactDetailResult:
    status: WebFactDetailStatus
    item: dict[str, Any] | None = None
    problems: tuple[dict[str, Any], ...] = ()
    coverage_status: WebFactListStatus = "complete"


@dataclass(frozen=True, slots=True)
class FactTypeRawSnapshot:
    fact_type_key: str
    objects: tuple[tuple[str, FactReadResult], ...]
    structural_problems: tuple[dict[str, object], ...]
    coverage_complete: bool


def _structural_problem(fact_type_key: str, canonical_path: str, summary: str) -> dict[str, object]:
    return {
        "fact_type_key": fact_type_key,
        "canonical_path": canonical_path,
        "check_status": "unavailable",
        "issues": [{"category": "location", "field_path": None, "summary": summary}],
    }


def discover_fact_type_raw(
    root: Path,
    project_id: str,
    common_dir: Path,
    schemas: dict[str, FactSchema],
    fact_type_key: str,
    *,
    aggregate_budget_bytes: int | None = None,
) -> FactTypeRawSnapshot:
    """Read one complete canonical directory for the Web list projection."""

    layout = LAYOUTS[fact_type_key]
    schema = schemas.get(fact_type_key)
    if schema is None:
        return FactTypeRawSnapshot(
            fact_type_key,
            (),
            (_structural_problem(fact_type_key, layout.directory, "事实类型 Schema 不可用"),),
            False,
        )
    identity_cache: dict[str, tuple[Path, Path] | None] = {}
    identity_issue, _ = _identity_issue(root, common_dir, identity_cache)
    if identity_issue is not None:
        return FactTypeRawSnapshot(
            fact_type_key,
            (),
            (_structural_problem(fact_type_key, layout.directory, identity_issue.summary),),
            False,
        )

    def listing() -> tuple[Path, ...] | None:
        try:
            return tuple(sorted(safe_list_directory(root, layout.directory), key=lambda item: item.name))
        except FileNotFoundError:
            return ()
        except OSError:
            return None

    before = listing()
    if before is None:
        return FactTypeRawSnapshot(
            fact_type_key,
            (),
            (_structural_problem(fact_type_key, layout.directory, "事实类型目录无法安全、完整地枚举"),),
            False,
        )
    structural: list[dict[str, object]] = []
    canonical: list[tuple[str, Path]] = []
    if len(before) > MAX_GRAPH_OBJECTS:
        structural.append(
            _structural_problem(
                fact_type_key,
                layout.directory,
                "当前事实类型的载体数量已超过单次扫描上限（10,000 个）",
            )
        )
        return FactTypeRawSnapshot(fact_type_key, (), tuple(structural), False)
    for path in before:
        if path.suffix != layout.suffix:
            structural.append(
                _structural_problem(
                    fact_type_key,
                    f"{layout.directory}/{path.name}",
                    "该载体不符合当前事实类型的权威文件路径与对象身份规则",
                )
            )
            continue
        object_id = path.name.removesuffix(layout.suffix)
        if layout.object_id_pattern.fullmatch(object_id) is None:
            structural.append(
                _structural_problem(
                    fact_type_key,
                    f"{layout.directory}/{path.name}",
                    "文件名不符合当前事实类型的对象身份规则",
                )
            )
        else:
            canonical.append((object_id, path))
    index = ProjectFactIndex(root, project_id, schemas, common_dir, aggregate_budget_bytes)
    base_objects: list[tuple[str, FactReadResult]] = []
    for object_id, _ in canonical:
        read = index.read(fact_type_key, object_id)
        if read is None:
            structural.append(_structural_problem(fact_type_key, object_id, "无法读取具有该权威身份的事实对象"))
            continue
        base_objects.append((object_id, read))
        if index.aggregate_budget_exhausted:
            structural.append(
                _structural_problem(
                    fact_type_key,
                    layout.directory,
                    f"该事实类型的累计安全读取量超过 {aggregate_budget_bytes} bytes 聚合预算",
                )
            )
            break
    stabilize_project_index(
        index,
        ((fact_type_key, object_id) for object_id, _ in base_objects),
    )
    if index.aggregate_budget_exhausted and not any("聚合预算" in str(problem) for problem in structural):
        structural.append(
            _structural_problem(
                fact_type_key,
                layout.directory,
                f"该事实类型的关系校验累计读取量超过 {aggregate_budget_bytes} bytes 聚合预算",
            )
        )
    objects = tuple(
        (object_id, index.cache.get((fact_type_key, object_id), base_read))
        for object_id, base_read in base_objects
    )
    after = listing()
    identity_after, _ = _identity_issue(root, common_dir)
    stable_listing = after is not None and tuple(path.name for path in before) == tuple(path.name for path in after)
    complete = stable_listing and identity_after is None and not structural
    if not stable_listing:
        structural.append(_structural_problem(fact_type_key, layout.directory, "事实目录在扫描期间发生变化"))
    if identity_after is not None:
        structural.append(_structural_problem(fact_type_key, layout.directory, identity_after.summary))
    return FactTypeRawSnapshot(fact_type_key, objects, tuple(structural), complete)


def _issues(read: FactReadResult) -> list[dict[str, object | None]]:
    return [
        {
            "category": issue.category,
            "field_path": issue.field_path,
            "summary": issue.summary,
        }
        for issue in read.issues
    ]


def _read_item(
    boundary: CreationBoundary,
    fact_type_key: str,
    object_id: str,
    read: FactReadResult,
) -> dict[str, Any]:
    return {
        "object_ref": {
            "governed_project_id": boundary.governed_project_id,
            "fact_type_key": fact_type_key,
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


def _list_from_snapshot(
    boundary: CreationBoundary,
    snapshot: FactTypeRawSnapshot,
    *,
    display_name: str,
    projected_budget_bytes: int,
) -> WebFactListResult:
    items: list[dict[str, Any]] = []
    problems: list[dict[str, Any]] = []
    structural = list(snapshot.structural_problems)
    projected_bytes = 0
    for object_id, read in snapshot.objects:
        item = _read_item(boundary, snapshot.fact_type_key, object_id, read)
        encoded_bytes = len(json.dumps(item, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
        if projected_bytes + encoded_bytes > projected_budget_bytes:
            structural.append(
                {
                    "fact_type_key": snapshot.fact_type_key,
                    "canonical_path": LAYOUTS[snapshot.fact_type_key].directory,
                    "check_status": "unavailable",
                    "issues": [
                        {
                            "category": "reference",
                            "field_path": None,
                            "summary": (
                                f"{display_name} Web 读取结果超过 "
                                f"{projected_budget_bytes} bytes 聚合预算"
                            ),
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
    completed_problems = [
        problem for problem in problems if problem["check_status"] in {"invalid", "not_found"}
    ]
    unavailable_problems = [
        problem for problem in problems if problem["check_status"] == "unavailable"
    ]
    has_unfinished = bool(structural or unavailable_problems or not snapshot.coverage_complete)
    has_completed = bool(items or completed_problems)
    if has_unfinished:
        status: WebFactListStatus = "partial" if has_completed else "unavailable"
    else:
        # invalid/not_found are completed exact checks.  They remain independently
        # observable in object_problems without turning complete coverage into partial.
        status = "complete"
    return WebFactListResult(status, tuple(items), tuple(problems), tuple(structural))


def _read_web_fact_list(
    boundary: CreationBoundary,
    schemas: dict[str, FactSchema],
    fact_type_key: str,
    *,
    display_name: str,
    raw_budget_bytes: int,
    projected_budget_bytes: int,
) -> WebFactListResult:
    snapshot = discover_fact_type_raw(
        boundary.worktree_root,
        boundary.governed_project_id,
        boundary.git_common_dir,
        schemas,
        fact_type_key,
        aggregate_budget_bytes=raw_budget_bytes,
    )
    return _list_from_snapshot(
        boundary,
        snapshot,
        display_name=display_name,
        projected_budget_bytes=projected_budget_bytes,
    )


def _read_web_fact_detail(
    boundary: CreationBoundary,
    schemas: dict[str, FactSchema],
    fact_type_key: str,
    object_id: str,
    *,
    display_name: str,
    raw_budget_bytes: int,
    projected_budget_bytes: int,
) -> WebFactDetailResult:
    index = ProjectFactIndex(
        boundary.worktree_root,
        boundary.governed_project_id,
        schemas,
        boundary.git_common_dir,
        raw_budget_bytes,
    )
    key = (fact_type_key, object_id)
    read = index.read(*key)
    if read is None:
        return WebFactDetailResult("not_found")
    stabilize_project_index(index, (key,))
    read = index.cache.get(key, read)
    item = _read_item(boundary, fact_type_key, object_id, read)
    encoded_bytes = len(json.dumps(item, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    if encoded_bytes > projected_budget_bytes:
        problem = {
            "object_ref": item["object_ref"],
            "canonical_path": item["canonical_path"],
            "absolute_path": item["absolute_path"],
            "carrier": item["carrier"],
            "check_status": "unavailable",
            "fact_object": None,
            "content_fingerprint": None,
            "issues": [
                {
                    "category": "reference",
                    "field_path": None,
                    "summary": (
                        f"{display_name} Web 读取结果超过 "
                        f"{projected_budget_bytes} bytes 投影预算"
                    ),
                }
            ],
        }
        return WebFactDetailResult(
            "unavailable",
            problems=(problem,),
            coverage_status="unavailable",
        )
    if read.check_status == "mechanically_valid" and read.fields is not None:
        return WebFactDetailResult("ok", item)
    if read.check_status == "not_found":
        return WebFactDetailResult("not_found", problems=(item,))
    if read.check_status == "invalid":
        return WebFactDetailResult("invalid", problems=(item,))
    return WebFactDetailResult("unavailable", problems=(item,), coverage_status="unavailable")


def read_web_spark_list(
    boundary: CreationBoundary,
    schemas: dict[str, FactSchema],
) -> WebFactListResult:
    """Read every canonical V4 Spark and preserve incomplete coverage explicitly."""

    return _read_web_fact_list(
        boundary,
        schemas,
        "spark",
        display_name="Spark",
        raw_budget_bytes=MAX_WEB_SPARK_RAW_BYTES,
        projected_budget_bytes=MAX_WEB_SPARK_PROJECTED_BYTES,
    )


def read_web_spark_detail(
    boundary: CreationBoundary,
    schemas: dict[str, FactSchema],
    object_id: str,
) -> WebFactDetailResult:
    """Read one exact V4 Spark without treating incomplete coverage as absence."""

    return _read_web_fact_detail(
        boundary,
        schemas,
        "spark",
        object_id,
        display_name="Spark",
        raw_budget_bytes=MAX_WEB_SPARK_RAW_BYTES,
        projected_budget_bytes=MAX_WEB_SPARK_PROJECTED_BYTES,
    )


def read_web_workcase_list(
    boundary: CreationBoundary,
    schemas: dict[str, FactSchema],
) -> WebFactListResult:
    """Read every current WorkCase through Core schema and relation stabilization."""

    return _read_web_fact_list(
        boundary,
        schemas,
        "workcase",
        display_name="WorkCase",
        raw_budget_bytes=MAX_WEB_WORKCASE_RAW_BYTES,
        projected_budget_bytes=MAX_WEB_WORKCASE_PROJECTED_BYTES,
    )


def read_web_workcase_detail(
    boundary: CreationBoundary,
    schemas: dict[str, FactSchema],
    object_id: str,
) -> WebFactDetailResult:
    """Read one exact current WorkCase without accepting a merely parseable carrier."""

    return _read_web_fact_detail(
        boundary,
        schemas,
        "workcase",
        object_id,
        display_name="WorkCase",
        raw_budget_bytes=MAX_WEB_WORKCASE_RAW_BYTES,
        projected_budget_bytes=MAX_WEB_WORKCASE_PROJECTED_BYTES,
    )


__all__ = [
    "FactTypeRawSnapshot",
    "WebFactDetailResult",
    "WebFactListResult",
    "discover_fact_type_raw",
    "read_web_spark_detail",
    "read_web_spark_list",
    "read_web_workcase_detail",
    "read_web_workcase_list",
]
