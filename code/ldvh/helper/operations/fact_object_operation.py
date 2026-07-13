"""Bind exact current-Working-Tree fact reads to the source-defined operation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from typing import Any

from ldvh.facts.contracts import LAYOUTS
from ldvh.facts.models import FactIssue, FactReferenceScope
from ldvh.facts.relations import ProjectFactIndex, validate_project_relations
from ldvh.facts.repository import FactReadResult, read_fact_object
from ldvh.facts.schema import project_fact_schemas
from ldvh.facts.source_validation import validate_study_sources
from ldvh.governance.models import ObjectStatus
from ldvh.governance.resolver import GovernanceResolutionRun, resolve_governance_scope
from ldvh.helper.operation_runtime import (
    AvailabilityEvaluation,
    OperationExecution,
    OperationExecutionContext,
    OperationImplementation,
    OperationRequestError,
)
from ldvh.helper.operations.fact_object_request import (
    OPTIONAL_INPUTS,
    REQUIRED_INPUTS,
    FactObjectRequest,
    parse_fact_object_request,
)
from ldvh.helper.requests import CommonRequest
from ldvh.helper.responses import source_reference
from ldvh.specs.repository import RepositoryInspection

OPERATION_KEY = "read-fact-objects"
_INPUT_CONTRACT = source_reference("rule", "fact-model-foundation::11.1 事实对象读取输入字段")
_RESULT_CONTRACT = source_reference("rule", "fact-model-foundation::11.2 事实对象读取结果字段")
_IMPLEMENTATION_EVIDENCE = (source_reference("implementation", "code/ldvh/helper/operations/fact_object_operation.py"),)
_TYPE_SOURCES = {
    "spark": "specs/20-Spark-火花.md",
    "workcase": "specs/21-WorkCase-工作项.md",
    "adr": "specs/22-ADR-决策.md",
    "pitfall": "specs/23-Pitfall-踩坑经验.md",
    "study": "specs/24-Study-研究报告.md",
}


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
    return value


def _validated_request(request: CommonRequest, context: OperationExecutionContext) -> FactObjectRequest:
    parsed = parse_fact_object_request(request, context)
    if parsed.request is None:
        raise OperationRequestError(parsed.problems, sources=(_INPUT_CONTRACT,))
    return parsed.request


def _governance(domain: FactObjectRequest) -> GovernanceResolutionRun:
    return resolve_governance_scope(
        domain.governance_scope,
        base=domain.base,
        explicit_workspace_root=domain.workspace_root,
    )


def _reading_boundary(run: GovernanceResolutionRun) -> tuple[str, Path, Path] | None:
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


def _scope_json(scope: FactReferenceScope) -> dict[str, object]:
    return scope.to_json()


def _item_sources(root: Path, scope: FactReferenceScope, canonical_path: str) -> list[dict[str, Any]]:
    return [
        source_reference("rule", _TYPE_SOURCES[scope.requested_ref.fact_type_key]),
        {
            "kind": "working_tree",
            "locator": (root / canonical_path).as_posix(),
            "observed_at": datetime.now().astimezone().isoformat(),
            "details": {"view": "Working Tree"},
        },
    ]


def _item(scope: FactReferenceScope, root: Path, read: FactReadResult) -> dict[str, Any]:
    sources = _item_sources(root, scope, read.canonical_path)
    fact_object: dict[str, Any] | None = None
    if read.check_status == "mechanically_valid" and read.fields is not None:
        fact_object = (
            {"frontmatter": read.fields, "body": read.body or ""} if read.carrier == "markdown" else read.fields
        )
    return {
        "fact_ref_index": scope.fact_ref_index,
        "requested_ref": scope.requested_ref.to_json(),
        "canonical_path": read.canonical_path,
        "carrier": read.carrier,
        "check_status": read.check_status,
        "fact_object": fact_object,
        "issues": [
            {
                "category": issue.category,
                "field_path": issue.field_path,
                "summary": issue.summary,
                "source_refs": sources,
            }
            for issue in read.issues
        ],
        "source_refs": sources,
    }


def _boundary_gap(domain: FactObjectRequest, run: GovernanceResolutionRun) -> dict[str, Any]:
    return {
        "summary": "全部定位输入未能形成同一管辖项目、同一实际 Git Working Tree 的唯一读取边界",
        "scope": [_scope_json(scope) for scope in domain.fact_scopes],
        "source_refs": [_plain(source) for source in run.sources],
    }


def _project_second_pass(index: ProjectFactIndex) -> None:
    """Reach a stable project-backed status without request-order dependence."""

    base_reads = {
        key: read
        for key, read in index.cache.items()
        if read.check_status == "mechanically_valid" and read.fields is not None
    }
    for fact_type_key in LAYOUTS:
        reads, _ = index.scan_valid_objects(fact_type_key)
        for read in reads:
            if read.fields is not None and isinstance(read.fields.get("object_id"), str):
                base_reads[(fact_type_key, read.fields["object_id"])] = read

    for _ in range(len(base_reads) + 1):
        evaluated: dict[tuple[str, str], FactReadResult] = {}
        for (fact_type_key, object_id), base_read in base_reads.items():
            current = index.cache.get((fact_type_key, object_id))
            if current is not None and current.check_status != "mechanically_valid":
                evaluated[(fact_type_key, object_id)] = current
                continue
            relation_issues, relation_unavailable = validate_project_relations(
                index,
                fact_type_key,
                object_id,
                base_read,
            )
            source_issues: tuple[FactIssue, ...] = ()
            source_unavailable = False
            if fact_type_key == "study":
                source_issues, source_unavailable = validate_study_sources(index, base_read)
            project_issues = (*relation_issues, *source_issues)
            if relation_unavailable or source_unavailable:
                evaluated[(fact_type_key, object_id)] = replace(
                    base_read,
                    check_status="unavailable",
                    issues=(
                        *base_read.issues,
                        *project_issues,
                        FactIssue("reference", "项目级关系或来源集合未能完成必需机械检查"),
                    ),
                )
            elif project_issues:
                evaluated[(fact_type_key, object_id)] = replace(
                    base_read,
                    check_status="invalid",
                    issues=(*base_read.issues, *project_issues),
                )
            else:
                evaluated[(fact_type_key, object_id)] = base_read
        if all(index.cache.get(key) == value for key, value in evaluated.items()):
            return
        index.cache.update(evaluated)

    for key, base_read in base_reads.items():
        index.cache[key] = replace(
            base_read,
            check_status="unavailable",
            issues=(*base_read.issues, FactIssue("relation", "项目级关系校验未能收敛")),
        )


def _execute(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> OperationExecution:
    domain = _validated_request(request, context)
    run = _governance(domain)
    requested = tuple(_scope_json(scope) for scope in domain.fact_scopes)
    governance_json = None if run.result is None else run.result.to_json()
    boundary = _reading_boundary(run)
    if boundary is None:
        return OperationExecution(
            outcome="unavailable",
            summary="当前管辖结果不能形成唯一事实对象读取边界",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=governance_json,
            sources=tuple(_plain(source) for source in run.sources) + _IMPLEMENTATION_EVIDENCE,
            gaps=(_boundary_gap(domain, run),),
        )

    project_id, root, common_dir = boundary
    schemas = project_fact_schemas(repository)
    fact_index = ProjectFactIndex(root, project_id, schemas, common_dir)
    first_pass: dict[int, FactReadResult] = {}
    for scope in domain.fact_scopes:
        reference = scope.requested_ref
        layout = LAYOUTS[reference.fact_type_key]
        schema = schemas.get(reference.fact_type_key)
        if reference.governed_project_id != project_id or schema is None:
            continue
        read = read_fact_object(
            root,
            layout,
            schema,
            reference.object_id,
            expected_common_dir=common_dir,
        )
        first_pass[scope.fact_ref_index] = read
        fact_index.cache[(reference.fact_type_key, reference.object_id)] = read
        fact_index.base_cache[(reference.fact_type_key, reference.object_id)] = read
    _project_second_pass(fact_index)

    items: list[dict[str, Any]] = []
    completed: list[dict[str, object]] = []
    not_completed: list[dict[str, object]] = []
    all_sources: list[dict[str, Any]] = []
    for scope in domain.fact_scopes:
        reference = scope.requested_ref
        layout = LAYOUTS[reference.fact_type_key]
        schema = schemas.get(reference.fact_type_key)
        if reference.governed_project_id != project_id:
            read = FactReadResult(
                layout.canonical_path(reference.object_id),
                layout.carrier,
                "unavailable",
                None,
                None,
                (),
            )
        elif schema is None:
            read = FactReadResult(
                layout.canonical_path(reference.object_id),
                layout.carrier,
                "unavailable",
                None,
                None,
                (),
            )
        else:
            read = fact_index.cache.get(
                (reference.fact_type_key, reference.object_id),
                first_pass[scope.fact_ref_index],
            )
        item = _item(scope, root, read)
        if reference.governed_project_id != project_id:
            item["issues"] = [
                {
                    "category": "location",
                    "field_path": "requested_ref.governed_project_id",
                    "summary": "请求项目与实际 Working Tree 的管辖项目不一致",
                    "source_refs": item["source_refs"],
                }
            ]
        elif schema is None:
            item["issues"] = [
                {
                    "category": "schema",
                    "field_path": None,
                    "summary": "当前规则源未能形成该类型的完整派生 Schema",
                    "source_refs": item["source_refs"],
                }
            ]
        items.append(item)
        all_sources.extend(item["source_refs"])
        target = completed if read.check_status != "unavailable" else not_completed
        target.append(_scope_json(scope))

    if completed and not_completed:
        outcome = "partial"
        summary = "已完成部分事实对象机械读取，并保留技术未完成范围"
    elif completed:
        outcome = "ok"
        summary = "已完成全部事实对象的当前 Working Tree 机械读取"
    else:
        outcome = "unavailable"
        summary = "当前技术条件不足，无法完成事实对象机械读取"
    verification = tuple(
        {
            "check": "当前对象适用的载体、Schema、身份、引用与类型机械检查已执行并通过",
            "status": "passed",
            "scope": [requested[item["fact_ref_index"]]],
            "evidence": item["source_refs"],
        }
        for item in items
        if item["check_status"] == "mechanically_valid"
    )
    gaps = tuple(
        {
            "summary": "事实对象存在尚未完成的适用机械检查",
            "scope": [requested[item["fact_ref_index"]]],
            "source_refs": item["source_refs"],
        }
        for item in items
        if item["check_status"] == "unavailable"
    )
    return OperationExecution(
        outcome=outcome,  # type: ignore[arg-type]
        summary=summary,
        result={"items": items},
        requested_scope=requested,
        completed_scope=tuple(completed),
        not_completed_scope=tuple(not_completed),
        governance_resolution=governance_json,
        sources=tuple(_plain(source) for source in run.sources) + tuple(all_sources) + _IMPLEMENTATION_EVIDENCE,
        gaps=gaps,
        verification=verification,
    )


def _check_availability(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> AvailabilityEvaluation:
    execution = _execute(request, repository, context)
    if execution.not_completed_scope and execution.completed_scope:
        availability = "partially_available"
    elif execution.not_completed_scope:
        availability = "unavailable_for_request"
    else:
        availability = "available_for_request"
    return AvailabilityEvaluation(
        availability=availability,
        available_scope=execution.completed_scope,
        unavailable_scope=execution.not_completed_scope,
        gaps=execution.gaps,
    )


def _call(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> OperationExecution:
    return _execute(request, repository, context)


FACT_OBJECT_IMPLEMENTATION = OperationImplementation(
    required_inputs=REQUIRED_INPUTS,
    optional_inputs=OPTIONAL_INPUTS,
    evidence=(*_IMPLEMENTATION_EVIDENCE, _RESULT_CONTRACT),
    check_availability=_check_availability,
    call=_call,
)

__all__ = ["FACT_OBJECT_IMPLEMENTATION", "OPERATION_KEY"]
