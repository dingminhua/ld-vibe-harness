"""Bind exact current-Working-Tree fact reads to the source-defined operation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ldvh.facts.configuration_index import ConfigurationFactIndex
from ldvh.facts.contracts import LAYOUTS
from ldvh.facts.models import FactReference, FactReferenceScope, UIDFactReference
from ldvh.facts.project_validation import stabilize_project_index
from ldvh.facts.relations import ProjectFactIndex
from ldvh.facts.repository import FactReadResult, read_fact_object
from ldvh.facts.schema import project_fact_schemas
from ldvh.facts.workcase_presentation import derive_workcase_presentation
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
from ldvh.helper.operations.fact_operation_support import configuration_reading_boundaries, plain, reading_boundary
from ldvh.helper.requests import CommonRequest
from ldvh.helper.responses import source_reference
from ldvh.specs.repository import RepositoryInspection
from ldvh.time import utc_now_iso

OPERATION_KEY = "read-fact-objects"
_INPUT_CONTRACT = source_reference("rule", "fact-model-foundation::11.1 事实对象读取输入字段")
_RESULT_CONTRACT = source_reference("rule", "fact-model-foundation::11.2 事实对象读取结果字段")
_IMPLEMENTATION_EVIDENCE = (source_reference("implementation", "code/ldvh/helper/operations/fact_object_operation.py"),)
_INPUT_EXAMPLES = (
    {
        "summary": "按 UID 引用读取事实对象",
        "arguments_fragment": {
            "fact_refs": [{"object_uid": "01ar3x8gf1ta0ex4j6rvq7vt9s"}],
        },
        "source_refs": (_RESULT_CONTRACT, *_IMPLEMENTATION_EVIDENCE),
        "composition_note": "UID 引用使用 §11.0 所定义的 object_uid 形状",
    },
    {
        "summary": "按 legacy 三元组引用读取事实对象",
        "arguments_fragment": {
            "fact_refs": [{"governed_project_id": "sample", "fact_type_key": "spark", "object_id": "spark-0001"}],
        },
        "source_refs": (_RESULT_CONTRACT, *_IMPLEMENTATION_EVIDENCE),
        "composition_note": "legacy 引用使用 §11.0 所定义的 governed_project_id + fact_type_key + object_id 形状",
    },
)
_TYPE_SOURCES = {
    "spark": "specs/20-Spark-火花.md",
    "workcase": "specs/21-WorkCase-工作项.md",
    "adr": "specs/22-ADR-决策.md",
    "pitfall": "specs/23-Pitfall-踩坑经验.md",
    "study": "specs/24-Study-研究报告.md",
}


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


def _scope_json(scope: FactReferenceScope) -> dict[str, object]:
    return scope.to_json()


def _item_sources(root: Path, fact_type_key: str, canonical_path: str) -> list[dict[str, Any]]:
    return [
        source_reference("rule", _TYPE_SOURCES[fact_type_key]),
        {
            "kind": "working_tree",
            "locator": (root / canonical_path).as_posix(),
            "observed_at": utc_now_iso(),
            "details": {"view": "Working Tree"},
        },
    ]


def _item(
    scope: FactReferenceScope,
    root: Path,
    fact_type_key: str,
    read: FactReadResult,
) -> dict[str, Any]:
    sources = _item_sources(root, fact_type_key, read.canonical_path)
    fact_object: dict[str, Any] | None = None
    if read.fields is not None and (
        read.check_status == "mechanically_valid" or read.content_fingerprint is not None
    ):
        fact_object = (
            {"frontmatter": read.fields, "body": read.body or ""} if read.carrier == "markdown" else read.fields
        )
    item = {
        "fact_ref_index": scope.fact_ref_index,
        "requested_ref": scope.requested_ref.to_json(),
        "resolved_ref": (
            {"object_uid": read.fields["object_uid"]}
            if read.fields is not None and isinstance(read.fields.get("object_uid"), str)
            else (
                {
                    "governed_project_id": scope.requested_ref.governed_project_id,
                    "fact_type_key": fact_type_key,
                    "object_id": read.fields["object_id"],
                }
                if isinstance(scope.requested_ref, FactReference) and read.fields is not None
                else None
            )
        ),
        "canonical_path": read.canonical_path,
        "carrier": read.carrier,
        "check_status": read.check_status,
        "fact_object": fact_object,
        "content_fingerprint": read.content_fingerprint,
        "current_snapshot_projection": None,
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
    if (
        fact_type_key == "workcase"
        and read.check_status == "mechanically_valid"
        and fact_object is not None
        and read.content_fingerprint is not None
    ):
        item["current_snapshot_projection"] = derive_workcase_presentation(
            fact_object.get("status"),
            fact_object.get("phase"),
            read.content_fingerprint,
        )
    return item


def _unresolved_uid_item(scope: FactReferenceScope, status: str) -> dict[str, Any]:
    summary = {
        "not_found": "当前选定管辖配置中不存在该 object_uid",
        "duplicate": "object_uid 在当前选定管辖配置中重复，不能唯一解析",
        "unavailable": "未能完整扫描当前选定管辖配置中的 object_uid",
        "invalid": "object_uid 不是 canonical 小写 UUIDv7",
    }.get(status, "object_uid 未能唯一解析")
    check_status = "not_found" if status == "not_found" else "invalid" if status == "duplicate" else "unavailable"
    return {
        "fact_ref_index": scope.fact_ref_index,
        "requested_ref": scope.requested_ref.to_json(),
        "resolved_ref": None,
        "canonical_path": None,
        "carrier": None,
        "check_status": check_status,
        "fact_object": None,
        "content_fingerprint": None,
        "current_snapshot_projection": None,
        "issues": [
            {
                "category": "identity" if status == "duplicate" else "reference",
                "field_path": "requested_ref.object_uid",
                "summary": summary,
                "source_refs": [],
            }
        ],
        "source_refs": [],
    }


def _boundary_gap(domain: FactObjectRequest, run: GovernanceResolutionRun) -> dict[str, Any]:
    return {
        "summary": "全部定位输入未能形成同一管辖项目、同一实际 Git Working Tree 的唯一读取边界",
        "scope": [_scope_json(scope) for scope in domain.fact_scopes],
        "source_refs": [plain(source) for source in run.sources],
    }


def _execute(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> OperationExecution:
    domain = _validated_request(request, context)
    run = _governance(domain)
    requested = tuple(_scope_json(scope) for scope in domain.fact_scopes)
    governance_json = None if run.result is None else run.result.to_json()
    boundary = reading_boundary(run)
    configuration_boundaries = configuration_reading_boundaries(run)
    if boundary is None or configuration_boundaries is None:
        return OperationExecution(
            outcome="unavailable",
            summary="当前管辖结果不能形成唯一事实对象读取边界",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=governance_json,
            sources=tuple(plain(source) for source in run.sources) + _IMPLEMENTATION_EVIDENCE,
            gaps=(_boundary_gap(domain, run),),
        )

    project_id, root, common_dir = boundary
    schemas = project_fact_schemas(repository)
    boundaries_by_project = {item[0]: item for item in configuration_boundaries}
    project_indexes: dict[str, ProjectFactIndex] = {}
    configuration_index = ConfigurationFactIndex(configuration_boundaries, schemas)
    resolved: dict[int, tuple[Path, str, FactReadResult, ProjectFactIndex] | str] = {}
    seed_keys: dict[int, list[tuple[str, str]]] = {}
    for scope in domain.fact_scopes:
        reference = scope.requested_ref
        if isinstance(reference, UIDFactReference):
            entry, status = configuration_index.resolve_uid(reference.object_uid)
            if entry is None:
                resolved[scope.fact_ref_index] = status
                continue
            resolved[scope.fact_ref_index] = (entry.root, entry.fact_type_key, entry.read, entry.project_index)
            seed_keys.setdefault(id(entry.project_index), []).append((entry.fact_type_key, entry.object_id))
            continue
        target_boundary = boundaries_by_project.get(reference.governed_project_id)
        layout = LAYOUTS[reference.fact_type_key]
        schema = schemas.get(reference.fact_type_key)
        if target_boundary is None or schema is None:
            resolved[scope.fact_ref_index] = "unavailable"
            continue
        target_project_id, target_root, target_common_dir = target_boundary
        index = project_indexes.setdefault(
            target_project_id,
            ProjectFactIndex(target_root, target_project_id, schemas, target_common_dir),
        )
        read = read_fact_object(
            target_root,
            layout,
            schema,
            reference.object_id,
            expected_common_dir=target_common_dir,
        )
        key = (reference.fact_type_key, reference.object_id)
        index.cache[key] = read
        index.base_cache[key] = read
        resolved[scope.fact_ref_index] = (target_root, reference.fact_type_key, read, index)
        seed_keys.setdefault(id(index), []).append(key)
    indexes = {id(index): index for index in project_indexes.values()}
    for value in resolved.values():
        if isinstance(value, tuple):
            indexes[id(value[3])] = value[3]
    for index_id, keys in seed_keys.items():
        stabilize_project_index(indexes[index_id], keys)

    items: list[dict[str, Any]] = []
    completed: list[dict[str, object]] = []
    not_completed: list[dict[str, object]] = []
    all_sources: list[dict[str, Any]] = []
    for scope in domain.fact_scopes:
        reference = scope.requested_ref
        resolution = resolved.get(scope.fact_ref_index, "unavailable")
        if isinstance(resolution, str):
            item = _unresolved_uid_item(scope, resolution) if isinstance(reference, UIDFactReference) else {
                **_unresolved_uid_item(scope, "unavailable"),
                "issues": [
                    {
                        "category": "location",
                        "field_path": "requested_ref.governed_project_id",
                        "summary": "请求项目未形成当前配置中的实际 Working Tree",
                        "source_refs": [],
                    }
                ],
            }
        else:
            item_root, fact_type_key, base_read, index = resolution
            assert base_read.fields is None or isinstance(base_read.fields.get("object_id"), str)
            key = (
                fact_type_key,
                str(base_read.fields["object_id"]) if base_read.fields is not None else (
                    reference.object_id if isinstance(reference, FactReference) else ""
                ),
            )
            read = index.cache.get(key, base_read)
            item = _item(scope, item_root, fact_type_key, read)
        items.append(item)
        all_sources.extend(item["source_refs"])
        target = completed if item["check_status"] != "unavailable" else not_completed
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
        sources=tuple(plain(source) for source in run.sources) + tuple(all_sources) + _IMPLEMENTATION_EVIDENCE,
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
    response_fields=("items",),
    input_examples=_INPUT_EXAMPLES,
)

__all__ = ["FACT_OBJECT_IMPLEMENTATION", "OPERATION_KEY"]
