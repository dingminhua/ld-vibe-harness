"""Migrate one explicitly authorized historical routed Spark to implemented."""

from __future__ import annotations

import re
from dataclasses import replace
from pathlib import Path
from typing import Any

from ldvh.facts.contracts import LAYOUTS, LEGACY_SPARK_IDS
from ldvh.facts.creation import CreationBoundary
from ldvh.facts.models import FactReference
from ldvh.facts.repository import read_fact_object
from ldvh.facts.schema import project_fact_schemas
from ldvh.governance.models import cwd_scope, explicit_scope
from ldvh.governance.resolver import resolve_governance_scope
from ldvh.helper.operation_runtime import (
    AvailabilityEvaluation,
    OperationExecution,
    OperationExecutionContext,
    OperationImplementation,
)
from ldvh.helper.operations.fact_operation_support import reading_boundary
from ldvh.helper.operations.fact_update_operation import _execute as execute_fact_update
from ldvh.helper.requests import CommonRequest
from ldvh.helper.responses import source_reference
from ldvh.specs.repository import RepositoryInspection

OPERATION_KEY = "migrate-legacy-routed-spark"
_CONTRACT = source_reference("rule", "spark-fact-type::8. 历史 routed Spark 受控迁移")
_IMPLEMENTATION_SOURCE = source_reference(
    "implementation", "code/ldvh/helper/operations/legacy_routed_spark_migration_operation.py"
)
_FINGERPRINT = re.compile(r"[0-9a-f]{64}\Z")
_REF_FIELDS = frozenset({"governed_project_id", "fact_type_key", "object_id"})

REQUIRED_INPUTS = ("arguments.fact_ref", "arguments.expected_content_fingerprint", "authorization_reference")
OPTIONAL_INPUTS = ("work_object_locators", "arguments.workspace_root")


def _failure(requested: dict[str, str], summary: str, detail: str, *, outcome: str = "rejected") -> OperationExecution:
    return OperationExecution(
        outcome=outcome,
        summary=summary,
        requested_scope=(requested,),
        not_completed_scope=(requested,),
        sources=(_CONTRACT, _IMPLEMENTATION_SOURCE),
        gaps=({"summary": detail, "scope": [requested], "source_refs": [_CONTRACT]},),
    )


def _reference(request: CommonRequest) -> tuple[FactReference | None, tuple[str, ...]]:
    problems: list[str] = []
    if set(request.arguments) - {"workspace_root", "fact_ref", "expected_content_fingerprint"}:
        problems.append("arguments 只允许 workspace_root、fact_ref、expected_content_fingerprint")
    raw = request.arguments.get("fact_ref")
    if not isinstance(raw, dict) or set(raw) != _REF_FIELDS:
        problems.append("arguments.fact_ref 必须使用完整稳定三元组")
        return None, tuple(problems)
    if any(not isinstance(raw.get(key), str) or not raw[key] for key in _REF_FIELDS):
        problems.append("arguments.fact_ref 的每个成员必须是非空 string")
        return None, tuple(problems)
    reference = FactReference(raw["governed_project_id"], raw["fact_type_key"], raw["object_id"])
    if reference.fact_type_key != "spark" or reference.object_id not in LEGACY_SPARK_IDS:
        problems.append("该操作只接受固定 allow-list 中的历史 Spark")
    fingerprint = request.arguments.get("expected_content_fingerprint")
    if not isinstance(fingerprint, str) or _FINGERPRINT.fullmatch(fingerprint) is None:
        problems.append("arguments.expected_content_fingerprint 必须是 64 位小写十六进制 string")
    if not request.authorization_reference:
        problems.append("authorization_reference 必须至少包含一个逐条 Human 授权来源")
    if request.requested_disclosure is not None:
        problems.append("requested_disclosure 必须为 null 或省略")
    return reference, tuple(problems)


def _execute(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> OperationExecution:
    reference, problems = _reference(request)
    requested = (
        reference.to_json()
        if reference is not None
        else {"governed_project_id": "unknown", "fact_type_key": "spark", "object_id": "unknown"}
    )
    if problems:
        return _failure(requested, "历史 Spark 迁移请求不符合契约", "；".join(problems), outcome="invalid_request")
    assert reference is not None
    scopes = (
        explicit_scope([item for item in request.work_object_locators if isinstance(item, str)])
        if request.work_object_locators
        else cwd_scope(str(context.cwd))
    )
    workspace_root = request.arguments.get("workspace_root")
    run = resolve_governance_scope(
        scopes,
        base=context.cwd,
        explicit_workspace_root=None if workspace_root is None else Path(workspace_root),
    )
    boundary_values = reading_boundary(run)
    if boundary_values is None:
        return _failure(
            requested,
            "当前管辖结果不能形成唯一历史 Spark 迁移边界",
            "管辖、worktree 或 common-dir 未形成唯一边界",
            outcome="unavailable",
        )
    boundary = CreationBoundary(*boundary_values)
    if boundary.governed_project_id != reference.governed_project_id:
        return _failure(requested, "请求项目与实际管辖项目不一致", "fact_ref 属于另一项目")
    schemas = project_fact_schemas(repository)
    schema = schemas.get("spark")
    if schema is None:
        return _failure(requested, "当前来源未形成 Spark Schema", "目标类型 Schema 不可用", outcome="unavailable")
    current = read_fact_object(
        boundary.worktree_root,
        LAYOUTS["spark"],
        schema,
        reference.object_id,
        expected_common_dir=boundary.git_common_dir,
    )
    if current.fields is None or current.raw_text is None or current.content_fingerprint is None:
        return _failure(requested, "历史 Spark 无法形成可迁移快照", "目标未能安全读取", outcome="unavailable")
    if current.content_fingerprint != request.arguments["expected_content_fingerprint"]:
        return _failure(requested, "历史 Spark 内容指纹已经过期", "必须重新精确读取后再迁移")
    if current.fields.get("status") != "routed":
        return _failure(requested, "目标不是可迁移的 routed 历史 Spark", "当前状态必须仍为 routed")
    has_disposition = (
        isinstance(current.fields.get("disposition_summary"), str)
        and current.fields["disposition_summary"].strip()
    )
    if not has_disposition:
        return _failure(requested, "历史 Spark 缺少可保留的处置依据", "disposition_summary 必须非空")
    after = {
        key: value
        for key, value in current.fields.items()
        if key not in {"object_id", "fact_type_key", "created_at", "updated_at", "priority"}
    }
    after["status"] = "implemented"
    relations: list[dict[str, Any]] = []
    seen_relation_targets: set[tuple[str, str, str]] = set()
    for item in after.get("relations", []):
        if not isinstance(item, dict):
            continue
        candidate = dict(item)
        if candidate.get("relation_key") == "routed-to":
            candidate["relation_key"] = "related-to"
        target = candidate.get("target")
        if not isinstance(target, dict) or candidate.get("relation_key") != "related-to":
            relations.append(candidate)
            continue
        identity = (
            str(target.get("governed_project_id", "")),
            str(target.get("fact_type_key", "")),
            str(target.get("object_id", "")),
        )
        if identity not in seen_relation_targets:
            relations.append(candidate)
            seen_relation_targets.add(identity)
    if relations:
        after["relations"] = relations
    else:
        after.pop("relations", None)
    change_log = (
        list(after.get("change_log", [])) if isinstance(after.get("change_log"), list) else []
    )
    change_log.append(
        {
            "at": context.event_at,
            "summary": "经逐条 Human 授权，历史 routed Spark 迁移为 implemented；旧 routed-to 已转为 related-to。",
            "signature": {},
        }
    )
    after["change_log"] = change_log
    delegated = replace(
        request,
        arguments={
            "fact_ref": reference.to_json(),
            "expected_content_fingerprint": current.content_fingerprint,
            "fact_object": after,
        },
    )
    return execute_fact_update(delegated, repository, context, allow_legacy_routed_spark_migration=True)


def _availability(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> AvailabilityEvaluation:
    reference, problems = _reference(request)
    if reference is None or problems:
        return AvailabilityEvaluation(
            availability="unavailable_for_request",
            unavailable_scope=(() if reference is None else (reference.to_json(),)),
            gaps=(),
        )
    return AvailabilityEvaluation(availability="available_for_request", available_scope=(reference.to_json(),))


MIGRATION_IMPLEMENTATION = OperationImplementation(
    required_inputs=REQUIRED_INPUTS,
    optional_inputs=OPTIONAL_INPUTS,
    evidence=(_IMPLEMENTATION_SOURCE, _CONTRACT),
    check_availability=_availability,
    call=_execute,
    response_fields=(
    "actual_ref",
    "canonical_path",
    "carrier",
    "previous_content_fingerprint",
    "content_fingerprint",
    "fact_object",
    ),
)

__all__ = ["MIGRATION_IMPLEMENTATION", "OPERATION_KEY"]
