"""Expose the three source-defined WorkCase full-after write operations."""

from __future__ import annotations

import subprocess
from collections.abc import Mapping
from copy import deepcopy
from dataclasses import replace
from typing import Any, Literal

from ldvh.facts.carriers.yaml_object import parse_yaml_object
from ldvh.facts.contracts import LAYOUTS
from ldvh.facts.creation import CreationBoundary, FactCoordinationUnavailable
from ldvh.facts.models import FactIssue
from ldvh.facts.project_validation import stabilize_project_index
from ldvh.facts.relations import ProjectFactIndex
from ldvh.facts.repository import FactReadResult, read_fact_object
from ldvh.facts.schema import FactSchema, project_fact_schemas
from ldvh.facts.update_application import MANAGED_FIELDS
from ldvh.facts.validation import validate_fact_object
from ldvh.filesystem import native_atomic_fact_writes_supported
from ldvh.governance.resolver import GovernanceResolutionRun, resolve_governance_scope
from ldvh.helper.operation_runtime import (
    AvailabilityEvaluation,
    OperationExecution,
    OperationExecutionContext,
    OperationImplementation,
    OperationRequestError,
)
from ldvh.helper.operations.fact_creation_operation import inject_observed_write_signature
from ldvh.helper.operations.fact_creation_request import observed_write_signature_required_problem
from ldvh.helper.operations.fact_operation_support import (
    plain,
    post_write_integrity_audit,
    reading_boundary,
)
from ldvh.helper.operations.workcase_update_request import (
    BEGIN_TERMINATION_OPTIONAL_INPUTS,
    BEGIN_TERMINATION_REQUIRED_INPUTS,
    CLOSE_OPTIONAL_INPUTS,
    CLOSE_REQUIRED_INPUTS,
    COMPLETE_TERMINATION_OPTIONAL_INPUTS,
    COMPLETE_TERMINATION_REQUIRED_INPUTS,
    CORRECT_CLOSED_OPTIONAL_INPUTS,
    CORRECT_CLOSED_REQUIRED_INPUTS,
    UPDATE_OPTIONAL_INPUTS,
    UPDATE_REQUIRED_INPUTS,
    CorrectClosedWorkCaseRequest,
    WorkCaseWriteRequest,
    parse_begin_workcase_termination_request,
    parse_close_workcase_request,
    parse_complete_workcase_termination_request,
    parse_correct_closed_workcase_request,
    parse_update_workcase_request,
)
from ldvh.helper.requests import CommonRequest
from ldvh.helper.responses import source_reference
from ldvh.specs.repository import RepositoryInspection

WorkCaseWriteMode = Literal["update", "close", "correct", "begin_termination", "complete_termination", "recover"]

UPDATE_OPERATION_KEY = "update-workcase"
CLOSE_OPERATION_KEY = "close-workcase"
CORRECT_CLOSED_OPERATION_KEY = "correct-closed-workcase"
BEGIN_TERMINATION_OPERATION_KEY = "begin-workcase-termination"
COMPLETE_TERMINATION_OPERATION_KEY = "complete-workcase-termination"
RECOVER_INVALID_OPERATION_KEY = "recover-invalid-workcase"

_CONTRACTS = {
    "update": source_reference("rule", "workcase-fact-type::update-workcase 输入与结果"),
    "close": source_reference("rule", "workcase-fact-type::close-workcase 输入与结果"),
    "correct": source_reference("rule", "workcase-fact-type::correct-closed-workcase 输入与结果"),
    "begin_termination": source_reference("rule", "workcase-fact-type::begin-workcase-termination 输入与结果"),
    "complete_termination": source_reference("rule", "workcase-fact-type::complete-workcase-termination 输入与结果"),
    "recover": source_reference("rule", "workcase-fact-type::recover-invalid-workcase 输入与结果"),
}
_SHARED_WRITE_CONTRACT = source_reference("rule", "fact-model-foundation::11.8 共享单对象受控写事务")
_INTEGRITY_CONTRACT = source_reference("rule", "fact-model-foundation::11.9-11.10 事实写后独立完整性审计")
_IMPLEMENTATION_SOURCE = source_reference(
    "implementation",
    "code/ldvh/helper/operations/workcase_update_operation.py",
)

RECOVER_REQUIRED_INPUTS = (
    "arguments.fact_ref",
    "arguments.expected_content_fingerprint",
    "authorization_reference",
)
RECOVER_OPTIONAL_INPUTS = ("work_object_locators", "arguments.workspace_root")
_RECOVER_ARGUMENT_FIELDS = frozenset({"workspace_root", "fact_ref", "expected_content_fingerprint"})
_RECOVERY_SNAPSHOTS = {
    "workcase-0092": {
        "revision": "3f6310ec36c27168db32b3091ca0c361aee485ce",
        "path": "ldvh-base/workcases/workcase-0092.yaml",
        "blob": "7adb18786a483c66a50033f687dd9dbf7af94879",
    },
    "workcase-0093": {
        "revision": "3f6310ec36c27168db32b3091ca0c361aee485ce",
        "path": "ldvh-base/workcases/workcase-0093.yaml",
        "blob": "0df53dbf63735f007e42d32eab58d092054cc8c8",
    },
}

_RECOVERY_REFERENCE_SCOPE = "recover-invalid-workcase"
_RECOVERY_REFERENCE_KINDS = frozenset({"human", "review"})
_RECOVERY_AUDIT_KIND = "integrity-audit"
_RECOVERY_MARKER_PREFIX = "recover-invalid-workcase|"
_RECOVERY_REQUIRED_BEFORE_STATUS = {"workcase-0092": "invalid", "workcase-0093": "invalid"}


def _recovery_snapshot(object_id: str) -> dict[str, str]:
    return _RECOVERY_SNAPSHOTS[object_id]


def _recovery_carrier_source(object_id: str) -> dict[str, Any]:
    snapshot = _recovery_snapshot(object_id)
    return source_reference(
        "git",
        f"{snapshot['revision']}:{snapshot['path']}",
        object_id=object_id,
        blob=snapshot["blob"],
    )


def _recovery_marker(object_id: str) -> str:
    snapshot = _recovery_snapshot(object_id)
    return (
        f"{_RECOVERY_MARKER_PREFIX}{object_id}|revision={snapshot['revision']}|"
        f"path={snapshot['path']}|blob={snapshot['blob']}"
    )


def _has_recovery_marker(fields: Mapping[str, Any], object_id: str) -> bool:
    change_log = fields.get("change_log")
    if not isinstance(change_log, list):
        return False
    return any(
        isinstance(entry, Mapping)
        and isinstance(entry.get("summary"), str)
        and entry["summary"].startswith(_recovery_marker(object_id))
        for entry in change_log
    )


def _target_details(reference: Mapping[str, Any]) -> Mapping[str, Any] | None:
    details = reference.get("details")
    if not isinstance(details, Mapping):
        return None
    target = details.get("target")
    return target if isinstance(target, Mapping) else None


def _recovery_reference_issues(request: WorkCaseWriteRequest) -> tuple[str, ...]:
    references = request.authorization_reference
    kinds = [reference.get("kind") for reference in references]
    expected_kinds = set(_RECOVERY_REFERENCE_KINDS)
    if request.fact_ref.object_id == "workcase-0093":
        expected_kinds.add(_RECOVERY_AUDIT_KIND)
    if len(references) != len(expected_kinds) or set(kinds) != expected_kinds:
        expected = ", ".join(sorted(expected_kinds))
        return (f"authorization_reference 必须恰好包含 kind={expected} 各一项",)
    issues: list[str] = []
    expected_target = request.fact_ref.to_json()
    prerequisite_target = {**expected_target, "object_id": "workcase-0092"}
    for index, reference in enumerate(references):
        target = _target_details(reference)
        required_target = (
            prerequisite_target
            if request.fact_ref.object_id == "workcase-0093" and reference.get("kind") == _RECOVERY_AUDIT_KIND
            else expected_target
        )
        if target != required_target:
            issues.append(
                "authorization_reference[{}].details.target 必须精确绑定{}".format(
                    index,
                    "已恢复的 workcase-0092" if required_target == prerequisite_target else "当前恢复对象",
                )
            )
        details = reference.get("details")
        if not isinstance(details, Mapping) or details.get("scope") != _RECOVERY_REFERENCE_SCOPE:
            issues.append(
                f"authorization_reference[{index}].details.scope 必须精确等于 {_RECOVERY_REFERENCE_SCOPE}"
            )
    return tuple(issues)


def _recovery_integrity_reference_issues(
    request: WorkCaseWriteRequest,
    prerequisite: FactReadResult,
) -> tuple[str, ...]:
    if prerequisite.content_fingerprint is None:
        return ("0092 当前恢复后指纹不可用，不能绑定完整性审计证明",)
    reference = next(
        (item for item in request.authorization_reference if item.get("kind") == _RECOVERY_AUDIT_KIND),
        None,
    )
    details = reference.get("details") if isinstance(reference, Mapping) else None
    expected_target = {**request.fact_ref.to_json(), "object_id": "workcase-0092"}
    if not isinstance(details, Mapping):
        return ("0093 必须提供 integrity-audit 的完整性审计证明 details",)
    issues: list[str] = []
    if details.get("operation_key") != "check-fact-integrity":
        issues.append("integrity-audit 必须回指 check-fact-integrity")
    if details.get("audit_scope") != "full_worktree":
        issues.append("integrity-audit 必须声明 audit_scope=full_worktree 范围")
    if details.get("outcome") != "ok" or details.get("result_status") != "complete":
        issues.append("integrity-audit 必须同时证明 outcome=ok 与 result.status=complete")
    if details.get("target") != expected_target:
        issues.append("integrity-audit target 必须精确绑定 workcase-0092")
    if details.get("content_fingerprint") != prerequisite.content_fingerprint:
        issues.append("integrity-audit content_fingerprint 必须精确等于 0092 恢复后当前指纹")
    return tuple(issues)


def _parse_recover_request(
    request: CommonRequest,
    context: OperationExecutionContext,
) -> WorkCaseWriteRequest:
    unknown = sorted(set(request.arguments) - _RECOVER_ARGUMENT_FIELDS)
    if unknown:
        raise OperationRequestError(
            (f"arguments 包含未知字段: {', '.join(unknown)}",), sources=(_CONTRACTS["recover"],)
        )
    synthetic = replace(
        request,
        arguments={
            **request.arguments,
            "fact_object": {},
        },
    )
    parsed = parse_update_workcase_request(synthetic, context)
    if parsed.request is None:
        raise OperationRequestError(parsed.problems, sources=(_CONTRACTS["recover"],))
    kinds = {reference.get("kind") for reference in parsed.request.authorization_reference}
    missing = [kind for kind in ("human", "review") if kind not in kinds]
    if missing:
        raise OperationRequestError(
            (
                f"authorization_reference 必须分别包含 kind=human 与 kind=review 的当前来源回指；"
                f"缺少: {', '.join(missing)}",
            ),
            sources=(_CONTRACTS["recover"],),
        )
    if (
        parsed.request.fact_ref.fact_type_key != "workcase"
        or parsed.request.fact_ref.object_id not in _RECOVERY_SNAPSHOTS
    ):
        raise OperationRequestError(
            ("recover-invalid-workcase 只允许恢复 workcase-0092 或 workcase-0093",),
            sources=(_CONTRACTS["recover"],),
        )
    recovery_issues = _recovery_reference_issues(parsed.request)
    if recovery_issues:
        raise OperationRequestError(recovery_issues, sources=(_CONTRACTS["recover"],))
    return parsed.request


def _validated_request(
    mode: WorkCaseWriteMode,
    request: CommonRequest,
    context: OperationExecutionContext,
) -> WorkCaseWriteRequest:
    if mode == "recover":
        return _parse_recover_request(request, context)
    if mode == "update":
        parsed = parse_update_workcase_request(request, context)
    elif mode == "close":
        parsed = parse_close_workcase_request(request, context)
    elif mode == "begin_termination":
        parsed = parse_begin_workcase_termination_request(request, context)
    elif mode == "complete_termination":
        parsed = parse_complete_workcase_termination_request(request, context)
    else:
        parsed = parse_correct_closed_workcase_request(request, context)
    if parsed.request is None:
        raise OperationRequestError(parsed.problems, sources=(_CONTRACTS[mode],))
    return parsed.request


def _governance(domain: WorkCaseWriteRequest) -> GovernanceResolutionRun:
    return resolve_governance_scope(
        domain.governance_scope,
        base=domain.base,
        explicit_workspace_root=domain.workspace_root,
    )


def _boundary(run: GovernanceResolutionRun) -> CreationBoundary | None:
    resolved = reading_boundary(run)
    return CreationBoundary(*resolved) if resolved is not None else None


def _current_read(
    boundary: CreationBoundary,
    schemas: dict[str, FactSchema],
    object_id: str,
) -> FactReadResult:
    layout = LAYOUTS["workcase"]
    read = read_fact_object(
        boundary.worktree_root,
        layout,
        schemas["workcase"],
        object_id,
        expected_common_dir=boundary.git_common_dir,
    )
    if read.check_status != "mechanically_valid" or read.fields is None:
        return read
    index = ProjectFactIndex(
        boundary.worktree_root,
        boundary.governed_project_id,
        schemas,
        boundary.git_common_dir,
    )
    key = ("workcase", object_id)
    index.cache[key] = read
    index.base_cache[key] = read
    stabilize_project_index(index, (key,))
    return index.cache.get(key, read)


def _working_tree_source(
    boundary: CreationBoundary,
    canonical_path: str,
    event_at: str | None,
) -> dict[str, Any]:
    source: dict[str, Any] = {
        "kind": "working_tree",
        "locator": (boundary.worktree_root / canonical_path).as_posix(),
        "details": {"view": "Working Tree"},
    }
    if event_at is not None:
        source["observed_at"] = event_at
    return source


def _residual_working_tree_source(
    boundary: CreationBoundary,
    read: FactReadResult,
    event_at: str,
) -> dict[str, Any]:
    source = _working_tree_source(boundary, read.canonical_path, event_at)
    details = source["details"]
    details["check_status"] = read.check_status
    if read.content_fingerprint is not None:
        details["content_fingerprint"] = read.content_fingerprint
    return source


def _coordination_release_gap(
    requested: tuple[dict[str, str], ...],
    *,
    committed: bool,
) -> dict[str, Any]:
    gap = {
        "summary": (
            "事实目标的原子替换已在 Working Tree 生效并成功回读；共同锁释放未能确认，"
            "后续受控写的串行协调状态未知；再次执行受控写入前须人工核对锁状态"
            if committed
            else (
                "事实目标确认未变化；共同锁释放未能确认，后续受控写的串行协调状态未知；"
                "再次执行受控写入前须人工核对锁状态"
            )
        ),
        "scope": list(requested),
        "source_refs": [_SHARED_WRITE_CONTRACT],
    }
    if committed:
        gap["code"] = "controlled_write_lock_release_uncertain"
    return gap


def _coordination_release_diagnostic(*, committed: bool) -> dict[str, Any]:
    diagnostic = {
        "summary": "共同协调锁释放状态未能确认",
        "details": {
            "stage": "common_dir_lock_release",
            "fact_target_state": "committed_and_read_back" if committed else "unchanged_and_read_back",
            "subsequent_controlled_write_serialization": "uncertain",
        },
        "source_refs": [_SHARED_WRITE_CONTRACT],
    }
    if committed:
        diagnostic["code"] = "controlled_write_lock_release_uncertain"
    return diagnostic


def _coordination_release_follow_up(requested: tuple[dict[str, str], ...]) -> dict[str, Any]:
    return {
        "summary": "再次执行受控写入前，需要恢复并确认共同锁的串行协调状态",
        "required_inputs": [],
        "required_human_decisions": [],
        "resume_conditions": [
            {
                "summary": "人工核对共同锁状态，并确认受控写入口能够重新取得和释放该锁",
                "scope": list(requested),
                "source_refs": [_SHARED_WRITE_CONTRACT],
            }
        ],
        "suggested_operations": [],
    }


def _merge_follow_up(
    existing: dict[str, Any] | None,
    coordination: dict[str, Any],
) -> dict[str, Any]:
    if existing is None:
        return coordination
    return {
        "summary": f"{existing['summary']}；{coordination['summary']}",
        "required_inputs": [*existing["required_inputs"], *coordination["required_inputs"]],
        "required_human_decisions": [
            *existing["required_human_decisions"],
            *coordination["required_human_decisions"],
        ],
        "resume_conditions": [*existing["resume_conditions"], *coordination["resume_conditions"]],
        "suggested_operations": [*existing["suggested_operations"], *coordination["suggested_operations"]],
    }


def _coordination_preserved_result_overlay(
    execution: OperationExecution,
    application: object,
    requested: tuple[dict[str, str], ...],
    *,
    diagnostic_profile: bool,
) -> OperationExecution:
    if not bool(getattr(application, "coordination_release_uncertain", False)):
        return execution
    status = getattr(application, "status", None)
    gap = {
        "summary": (
            f"WorkCase 领域结果（status={status}）已在共同锁释放前形成并保留；共同锁释放未能确认，"
            "后续受控写的串行协调状态未知；目标、残留与未完成验证仍以本响应原结果为准，"
            "再次执行受控写入前须人工核对锁状态"
        ),
        "scope": list(requested),
        "source_refs": [_SHARED_WRITE_CONTRACT],
    }
    diagnostic = {
        "summary": "共同协调锁释放状态未能确认",
        "details": {
            "stage": "common_dir_lock_release",
            "domain_result_status": status,
            "fact_target_state": "as_reported_by_domain_result",
            "subsequent_controlled_write_serialization": "uncertain",
        },
        "source_refs": [_SHARED_WRITE_CONTRACT],
    }
    sources = (
        execution.sources
        if _SHARED_WRITE_CONTRACT in execution.sources
        else (*execution.sources, _SHARED_WRITE_CONTRACT)
    )
    coordination_follow_up = _coordination_release_follow_up(requested)
    return replace(
        execution,
        sources=sources,
        gaps=(*execution.gaps, gap),
        diagnostics=(*execution.diagnostics, *((diagnostic,) if diagnostic_profile else ())),
        follow_up=_merge_follow_up(execution.follow_up, coordination_follow_up),
    )


def _rollback_failure_prefix(rollback: object) -> str:
    """Describe only the rollback result's own namespace evidence."""

    namespace_state = getattr(rollback, "namespace_state", None)
    if namespace_state == "uncertain":
        return "条件回滚在文件命名空间（namespace）中的生效情况无法确认"
    if namespace_state == "not_committed":
        if getattr(rollback, "outcome", None) == "conflict":
            return "条件回滚发生冲突，确认未在文件命名空间（namespace）生效"
        return "条件回滚确认未在文件命名空间（namespace）生效"
    return "条件回滚未完成"


def _fact_object(read: FactReadResult) -> dict[str, Any]:
    assert read.fields is not None
    return read.fields


def _result(
    before: FactReadResult,
    after: FactReadResult,
    project_id: str,
    object_id: str,
    *,
    recovery_carrier: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    assert before.content_fingerprint is not None
    assert after.content_fingerprint is not None
    result = {
        "actual_ref": {
            "governed_project_id": project_id,
            "fact_type_key": "workcase",
            "object_id": object_id,
        },
        "canonical_path": after.canonical_path,
        "carrier": after.carrier,
        "previous_content_fingerprint": before.content_fingerprint,
        "content_fingerprint": after.content_fingerprint,
        "fact_object": _fact_object(after),
    }
    if recovery_carrier is not None:
        result["recovery_carrier"] = dict(recovery_carrier)
    return result


def _issue_summary(issues: tuple[FactIssue, ...]) -> str:
    return "; ".join(f"{issue.field_path + ': ' if issue.field_path else ''}{issue.summary}" for issue in issues)


def _request_sources(
    mode: WorkCaseWriteMode,
    domain: WorkCaseWriteRequest,
    run: GovernanceResolutionRun,
) -> tuple[dict[str, Any], ...]:
    review_reference: tuple[dict[str, Any], ...] = ()
    if isinstance(domain, CorrectClosedWorkCaseRequest) and domain.independent_review_reference is not None:
        review_reference = (plain(domain.independent_review_reference),)
    recovery_source = (_recovery_carrier_source(domain.fact_ref.object_id),) if mode == "recover" else ()
    return (
        *tuple(plain(source) for source in run.sources),
        *tuple(plain(source) for source in domain.authorization_reference),
        *review_reference,
        *recovery_source,
        _CONTRACTS[mode],
    )


def _rejected(
    mode: WorkCaseWriteMode,
    domain: WorkCaseWriteRequest,
    run: GovernanceResolutionRun,
    summary: str,
    detail: str,
    sources: tuple[dict[str, Any], ...],
) -> OperationExecution:
    requested = (domain.fact_ref.to_json(),)
    return OperationExecution(
        outcome="rejected",
        summary=summary,
        requested_scope=requested,
        not_completed_scope=requested,
        governance_resolution=run.result.to_json() if run.result else None,
        sources=sources,
        gaps=(
            {
                "summary": detail,
                "scope": list(requested),
                "source_refs": [_CONTRACTS[mode]],
            },
        ),
    )


class RecoverySnapshotError(ValueError):
    """The fixed historical recovery source cannot produce a safe active after."""


def _recovery_fact_object(
    domain: WorkCaseWriteRequest,
    boundary: CreationBoundary,
    schema: FactSchema,
    event_at: str,
) -> dict[str, Any]:
    snapshot = _recovery_snapshot(domain.fact_ref.object_id)
    reference = f"{snapshot['revision']}:{snapshot['path']}"
    try:
        blob = subprocess.run(
            ["git", "-C", str(boundary.worktree_root), "rev-parse", reference],
            check=False,
            capture_output=True,
            text=True,
        )
        source = subprocess.run(
            ["git", "-C", str(boundary.worktree_root), "show", reference],
            check=False,
            capture_output=True,
        )
    except OSError as error:
        raise RecoverySnapshotError("固定历史载体读取所需的 Git 能力不可用") from error
    if blob.returncode != 0 or blob.stdout.strip() != snapshot["blob"]:
        raise RecoverySnapshotError("固定历史载体不可读取，或其 blob 身份与恢复清单不一致")
    if source.returncode != 0:
        raise RecoverySnapshotError("固定历史载体内容不可读取")
    try:
        text = source.stdout.decode("utf-8")
    except UnicodeDecodeError as error:
        raise RecoverySnapshotError("固定历史载体不是完整 UTF-8 YAML") from error
    parsed = parse_yaml_object(text)
    fields = parsed.fields
    if parsed.issues or not isinstance(fields, dict):
        raise RecoverySnapshotError("固定历史载体无法完整解析")
    if (
        fields.get("object_id") != domain.fact_ref.object_id
        or fields.get("fact_type_key") != "workcase"
        or fields.get("status") not in {"open", "blocked"}
    ):
        raise RecoverySnapshotError("固定历史载体不是该对象的活动期 WorkCase 快照")
    carrier_issues = validate_fact_object("workcase", fields, schema)
    if carrier_issues:
        raise RecoverySnapshotError("固定历史载体不是当前 Schema 下机械有效的活动期 WorkCase")
    recovery_entry = {
        # The write adapter replaces this complete, all-null placeholder with
        # the required current LDVH signature before validation or persistence.
        "signature": {
            "product_name": None,
            "model_name": None,
            "agent_runtime_name": None,
        },
        "at": event_at,
        "summary": (
            f"{_recovery_marker(domain.fact_ref.object_id)}；按当前 Human 决定，从 "
            f"{snapshot['revision']} 的已验证历史载体恢复活动期快照；撤回无法真实归属的关闭记录，"
            "后续关闭必须依据当前事实重新形成。"
        ),
    }
    change_log = fields.get("change_log")
    if not isinstance(change_log, list):
        raise RecoverySnapshotError("固定历史载体缺少可追加的 change_log")
    supplied = {key: deepcopy(value) for key, value in fields.items() if key not in MANAGED_FIELDS}
    supplied["change_log"] = [*deepcopy(change_log), recovery_entry]
    return supplied


def _apply_core_workcase_write(
    mode: WorkCaseWriteMode,
    domain: WorkCaseWriteRequest,
    boundary: CreationBoundary,
    schemas: dict[str, FactSchema],
    schema: FactSchema,
    event_at: str,
    observed_context: dict[str, Any],
) -> object:
    """The only Helper-to-Core WorkCase transaction adapter."""

    from ldvh.facts.relations import WorkCaseRouteTargetSnapshot
    from ldvh.facts.workcase_update import WorkCaseWriteCommand, apply_workcase_write

    route_targets = ()
    independent_review_reference = None
    if isinstance(domain, CorrectClosedWorkCaseRequest):
        route_targets = tuple(
            WorkCaseRouteTargetSnapshot(
                item.target,
                item.content_fingerprint,
                f"route_target_fingerprints[{index}].target",
            )
            for index, item in enumerate(domain.route_target_fingerprints)
        )
        independent_review_reference = domain.independent_review_reference
    return apply_workcase_write(
        WorkCaseWriteCommand(
            boundary=boundary,
            schemas=schemas,
            schema=schema,
            object_id=domain.fact_ref.object_id,
            expected_content_fingerprint=domain.expected_content_fingerprint,
            supplied=inject_observed_write_signature(dict(domain.fact_object), observed_context),
            event_at=event_at,
            mode=mode,
            authorization_reference=domain.authorization_reference,
            route_target_fingerprints=route_targets,
            independent_review_reference=independent_review_reference,
        )
    )


def _application_failure(
    mode: WorkCaseWriteMode,
    result: object,
    domain: WorkCaseWriteRequest,
    run: GovernanceResolutionRun,
    sources: tuple[dict[str, Any], ...],
    boundary: CreationBoundary,
    event_at: str,
) -> OperationExecution | None:
    status = getattr(result, "status", None)
    if status in {"updated", "no_change"}:
        return None
    requested = (domain.fact_ref.to_json(),)
    governance = run.result.to_json() if run.result else None
    issues = getattr(result, "issues", ())
    issue_summary = _issue_summary(issues) if isinstance(issues, tuple) else ""

    if status == "invalid_request":
        return OperationExecution(
            outcome="invalid_request",
            summary="提交给 WorkCase 核心事务的请求结构不符合规范",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=governance,
            sources=sources,
            gaps=({"summary": issue_summary, "scope": list(requested), "source_refs": [_CONTRACTS[mode]]},),
        )
    if status == "durability_unavailable":
        return OperationExecution(
            outcome="unavailable",
            summary="当前平台没有启用 WorkCase 写入的原生原子后端",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=governance,
            sources=sources,
            gaps=({"summary": "未写入目标载体", "scope": list(requested), "source_refs": [_SHARED_WRITE_CONTRACT]},),
        )
    if status in {"current_rejected", "current_unavailable"}:
        return OperationExecution(
            outcome="unavailable" if status == "current_unavailable" else "rejected",
            summary="当前 WorkCase 不满足该操作对变更前快照的要求",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=governance,
            sources=sources,
            gaps=(
                {
                    "summary": issue_summary or "当前对象读取或 operation before 条件不成立",
                    "scope": list(requested),
                    "source_refs": [_CONTRACTS[mode]],
                },
            ),
        )
    if status == "fingerprint_stale":
        return _rejected(mode, domain, run, "WorkCase 内容指纹已经过期", "重新精确读取当前对象后重试", sources)
    if status == "event_time_not_successor":
        return _rejected(
            mode,
            domain,
            run,
            "本次事件时间不能形成 updated_at 严格后继",
            issue_summary,
            sources,
        )
    if status in {"candidate_rejected", "candidate_unavailable"}:
        return OperationExecution(
            outcome="unavailable" if status == "candidate_unavailable" else "rejected",
            summary="WorkCase 完整 after 未通过专属机械检查",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=governance,
            sources=sources,
            gaps=(
                {
                    "summary": issue_summary or "完整 after、转换、关口或目标检查未成立",
                    "scope": list(requested),
                    "source_refs": [_CONTRACTS[mode]],
                },
            ),
        )
    if status in {"replacement_conflict", "replacement_unavailable"}:
        replacement = getattr(result, "replacement_result", None)
        namespace_uncertain = getattr(replacement, "namespace_state", None) == "uncertain"
        return OperationExecution(
            outcome="rejected" if status == "replacement_conflict" else "unavailable",
            summary=(
                "原子替换前 WorkCase 已发生变化" if status == "replacement_conflict" else "原子替换技术条件不成立"
            ),
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=governance,
            sources=(*sources, _IMPLEMENTATION_SOURCE),
            gaps=(
                {
                    "summary": (
                        "文件命名空间（namespace）中的原子替换是否生效无法确认；"
                        "必须重新精确读取当前 WorkCase 事实载体与全部分流目标（route targets）"
                        if namespace_uncertain
                        else (
                            "已确认原子替换未在文件命名空间（namespace）生效；"
                            "重新精确读取当前 WorkCase 事实载体与全部分流目标（route targets）后重试"
                        )
                    ),
                    "scope": list(requested),
                    "source_refs": [_CONTRACTS[mode]],
                },
            ),
        )
    if status == "readback_failed":
        rollback = getattr(result, "rollback_result", None)
        rolled_back = (
            rollback is not None
            and getattr(rollback, "outcome", None) == "replaced"
            and getattr(rollback, "namespace_state", None) == "committed"
        )
        residual = getattr(result, "residual_readback", None)
        residual_source: dict[str, Any] | None = None
        if isinstance(residual, FactReadResult):
            residual_source = _residual_working_tree_source(boundary, residual, event_at)
        current = getattr(result, "current", None)
        rollback_failure_prefix = _rollback_failure_prefix(rollback)
        if rolled_back:
            change_summary = "已恢复更新前载体"
        elif not isinstance(residual, FactReadResult) or residual.check_status == "unavailable":
            change_summary = f"{rollback_failure_prefix}；实际 WorkCase 事实载体的残留状态无法确认"
        elif residual.raw_text == getattr(result, "candidate_text", None):
            change_summary = (
                f"{rollback_failure_prefix}；当前重新读取观察到的实际 WorkCase 事实载体完整字节内容与本次新载体一致"
            )
        elif isinstance(current, FactReadResult) and residual.raw_text == current.raw_text:
            change_summary = (
                f"{rollback_failure_prefix}；当前重新读取观察到的实际 WorkCase 事实载体完整字节内容与更新前载体一致"
            )
        elif residual.check_status == "mechanically_valid":
            change_summary = f"{rollback_failure_prefix}；当前重新读取观察到的实际 WorkCase 事实载体是另一机械有效版本"
        elif residual.check_status == "not_found":
            change_summary = f"{rollback_failure_prefix}；当前重新读取确认实际 WorkCase 事实载体的预期位置不存在"
        elif residual.raw_text is not None:
            change_summary = (
                f"{rollback_failure_prefix}；当前实际 WorkCase 事实载体已安全完整读取，但对象未通过机械检查"
            )
        else:
            change_summary = (
                f"{rollback_failure_prefix}；当前实际 WorkCase 事实载体未能安全完整读取，"
                "机械检查未通过（状态为 `invalid`）"
            )
        residual_unknown = not rolled_back and (
            not isinstance(residual, FactReadResult) or residual.check_status == "unavailable"
        )
        residual_refs = () if residual_source is None else (residual_source,)
        residual_gap = (
            (
                {
                    "summary": "条件回滚后的实际 WorkCase 事实载体无法确认",
                    "scope": list(requested),
                    "source_refs": [_CONTRACTS[mode]],
                },
            )
            if residual_unknown
            else ()
        )
        residual_verification = (
            (
                {
                    "check": "条件回滚后重新精确读取并机械检查实际 WorkCase 事实载体",
                    "status": (
                        "unavailable"
                        if not isinstance(residual, FactReadResult) or residual.check_status == "unavailable"
                        else "passed"
                        if residual.check_status == "mechanically_valid"
                        else "failed"
                    ),
                    "scope": list(requested),
                    "evidence": [*residual_refs, _CONTRACTS[mode]],
                },
            )
            if not rolled_back
            else ()
        )
        return OperationExecution(
            outcome="error",
            summary=("写后回读未通过；已完成条件回滚" if rolled_back else "写后回读未通过，且未能确认条件回滚已经完成"),
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=governance,
            sources=(*sources, *residual_refs, _IMPLEMENTATION_SOURCE),
            changes=(
                {
                    "summary": change_summary,
                    "status": "rolled-back" if rolled_back else "rollback-failed",
                    "target": domain.fact_ref.to_json(),
                    "source_refs": [_CONTRACTS[mode], *residual_refs],
                },
            ),
            gaps=(
                {
                    "summary": issue_summary or "写后项目级检查未完成",
                    "scope": list(requested),
                    "source_refs": [_CONTRACTS[mode]],
                },
                *residual_gap,
            ),
            verification=residual_verification,
        )
    return OperationExecution(
        outcome="error",
        summary="WorkCase 专属事务返回未知内部状态",
        requested_scope=requested,
        not_completed_scope=requested,
        governance_resolution=governance,
        sources=(*sources, _IMPLEMENTATION_SOURCE),
    )


def _coordination_unavailable(
    mode: WorkCaseWriteMode,
    error: FactCoordinationUnavailable,
    domain: WorkCaseWriteRequest,
    run: GovernanceResolutionRun,
    sources: tuple[dict[str, Any], ...],
    *,
    diagnostic_profile: bool,
) -> OperationExecution:
    requested = (domain.fact_ref.to_json(),)
    diagnostic = {
        "summary": "受控写入共同协调锁不可用",
        "code": "controlled_write_lock_unavailable",
        "details": {
            "stage": error.stage,
            "path_role": error.path_role,
            "required_access": error.required_access,
            "system_error_category": error.system_error_category,
            "target_unchanged": True,
            "counter_unchanged": True,
        },
        "source_refs": [_SHARED_WRITE_CONTRACT],
    }
    return OperationExecution(
        outcome="unavailable",
        summary="WorkCase 共同协调锁当前不可用，未更新目标",
        requested_scope=requested,
        not_completed_scope=requested,
        governance_resolution=run.result.to_json() if run.result else None,
        sources=(*sources, _SHARED_WRITE_CONTRACT),
        gaps=(
            {
                "summary": "恢复 git common-dir 下 LDVH 协调根访问后重试",
                "scope": list(requested),
                "source_refs": [_SHARED_WRITE_CONTRACT],
                "code": "controlled_write_lock_unavailable",
            },
        ),
        diagnostics=(diagnostic,) if diagnostic_profile else (),
    )


def _execute(
    mode: WorkCaseWriteMode,
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> OperationExecution:
    domain = _validated_request(mode, request, context)
    reference = domain.fact_ref
    requested = (reference.to_json(),)
    run = _governance(domain)
    sources = _request_sources(mode, domain, run)
    boundary = _boundary(run)
    if boundary is None:
        return OperationExecution(
            outcome="unavailable",
            summary="当前管辖结果不能形成唯一 WorkCase 写入边界",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=run.result.to_json() if run.result else None,
            sources=sources,
            gaps=(
                {
                    "summary": "管辖输入未形成同一项目、实际 worktree 和 common-dir 的唯一边界",
                    "scope": list(requested),
                    "source_refs": [_CONTRACTS[mode]],
                },
            ),
        )
    if boundary.governed_project_id != reference.governed_project_id:
        return _rejected(mode, domain, run, "请求项目与实际管辖项目不一致", "fact_ref 属于另一项目", sources)

    schemas = project_fact_schemas(repository)
    schema = schemas.get("workcase")
    if schema is None:
        return OperationExecution(
            outcome="unavailable",
            summary="当前来源未形成 WorkCase 的完整派生 Schema",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=run.result.to_json() if run.result else None,
            sources=sources,
        )
    if not native_atomic_fact_writes_supported():
        return OperationExecution(
            outcome="unavailable",
            summary="当前平台没有启用 WorkCase 写入的原生原子后端",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=run.result.to_json() if run.result else None,
            sources=(*sources, _SHARED_WRITE_CONTRACT),
        )

    if mode == "recover":
        current = _current_read(boundary, schemas, reference.object_id)
        expected_check_status = _RECOVERY_REQUIRED_BEFORE_STATUS[reference.object_id]
        if (
            current.check_status != expected_check_status
            or current.fields is None
            or current.raw_text is None
            or current.content_fingerprint is None
            or current.fields.get("status") != "closed"
        ):
            return _rejected(
                mode,
                domain,
                run,
                "当前 WorkCase 不是该固定恢复入口允许的 closed 载体",
                f"{reference.object_id} 必须是完整可读取、status=closed 且 check_status={expected_check_status}",
                sources,
            )
        if _has_recovery_marker(current.fields, reference.object_id):
            return _rejected(
                mode,
                domain,
                run,
                "该 WorkCase 已经消费过固定恢复入口",
                "恢复标记已经存在；为避免重复重建与重复流水，本入口确定性拒绝再次恢复",
                sources,
            )
        if reference.object_id == "workcase-0093":
            prerequisite = _current_read(boundary, schemas, "workcase-0092")
            prerequisite_issues = ()
            if (
                prerequisite.check_status != "mechanically_valid"
                or prerequisite.fields is None
                or prerequisite.fields.get("status") not in {"open", "blocked"}
                or not _has_recovery_marker(prerequisite.fields, "workcase-0092")
            ):
                prerequisite_issues = (
                    "0092 当前对象必须是本恢复入口已经形成的 mechanically valid open/blocked 快照，"
                    "不能由任意既有 open 0092 解锁 0093",
                )
            else:
                prerequisite_issues = _recovery_integrity_reference_issues(domain, prerequisite)
            if prerequisite_issues:
                return _rejected(
                    mode,
                    domain,
                    run,
                    "workcase-0093 必须绑定 0092 的本次恢复与完整性审计证明",
                    "; ".join(prerequisite_issues),
                    sources,
                )
        try:
            domain = replace(domain, fact_object=_recovery_fact_object(domain, boundary, schema, context.event_at))
        except RecoverySnapshotError as error:
            return _rejected(mode, domain, run, "固定历史快照不能用于恢复", str(error), sources)

    observed_problem = observed_write_signature_required_problem(request.observed_context)
    if observed_problem is not None:
        return OperationExecution(
            outcome="unavailable",
            summary=observed_problem,
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=run.result.to_json() if run.result else None,
            sources=sources,
            gaps=({"summary": observed_problem, "scope": list(requested), "source_refs": [_CONTRACTS[mode]]},),
        )
    try:
        application = _apply_core_workcase_write(
            mode,
            domain,
            boundary,
            schemas,
            schema,
            context.event_at,
            request.observed_context,
        )
    except FactCoordinationUnavailable as error:
        return _coordination_unavailable(
            mode,
            error,
            domain,
            run,
            sources,
            diagnostic_profile=request.response_profile == "diagnostic",
        )

    failure = _application_failure(
        mode,
        application,
        domain,
        run,
        sources,
        boundary,
        context.event_at,
    )
    if failure is not None:
        return _coordination_preserved_result_overlay(
            failure,
            application,
            requested,
            diagnostic_profile=request.response_profile == "diagnostic",
        )
    before = getattr(application, "current", None)
    after = getattr(application, "readback", None)
    if not isinstance(before, FactReadResult) or not isinstance(after, FactReadResult):
        return OperationExecution(
            outcome="error",
            summary="WorkCase 专属事务没有返回可回读的 before/after",
            requested_scope=requested,
            not_completed_scope=requested,
            governance_resolution=run.result.to_json() if run.result else None,
            sources=(*sources, _IMPLEMENTATION_SOURCE),
        )
    no_change = getattr(application, "status", None) == "no_change"
    coordination_release_uncertain = bool(getattr(application, "coordination_release_uncertain", False))
    working_tree_source = _working_tree_source(
        boundary,
        after.canonical_path,
        context.event_at,
    )
    result = _result(
        before,
        after,
        boundary.governed_project_id,
        reference.object_id,
        recovery_carrier=_recovery_snapshot(reference.object_id) if mode == "recover" else None,
    )
    if no_change:
        return OperationExecution(
            outcome="no_change",
            summary="完整 after 与当前 WorkCase 相同，未重写目标",
            result=result,
            requested_scope=requested,
            completed_scope=requested,
            governance_resolution=run.result.to_json() if run.result else None,
            sources=(
                *sources,
                working_tree_source,
                *((_SHARED_WRITE_CONTRACT,) if coordination_release_uncertain else ()),
                _IMPLEMENTATION_SOURCE,
            ),
            gaps=(_coordination_release_gap(requested, committed=False),) if coordination_release_uncertain else (),
            verification=(
                {
                    "check": "当前对象指纹匹配且完整 after 与 before 相同",
                    "status": "passed",
                    "scope": list(requested),
                    "evidence": [working_tree_source, _CONTRACTS[mode]],
                },
            ),
            diagnostics=(_coordination_release_diagnostic(committed=False),)
            if coordination_release_uncertain and request.response_profile == "diagnostic"
            else (),
            follow_up=(_coordination_release_follow_up(requested) if coordination_release_uncertain else None),
        )
    replacement = getattr(application, "replacement_result", None)
    return post_write_integrity_audit(
        OperationExecution(
        outcome="ok",
        summary="WorkCase 已完成专属完整 after 校验、CAS 替换和写后回读",
        result=result,
        requested_scope=requested,
        completed_scope=requested,
        governance_resolution=run.result.to_json() if run.result else None,
        sources=(
            *sources,
            working_tree_source,
            *((_SHARED_WRITE_CONTRACT,) if coordination_release_uncertain else ()),
            _IMPLEMENTATION_SOURCE,
        ),
        gaps=(_coordination_release_gap(requested, committed=True),) if coordination_release_uncertain else (),
        changes=(
            {
                "summary": "已原子更新 WorkCase 当前完整快照",
                "status": "updated",
                "target": reference.to_json(),
                "source_refs": [working_tree_source],
            },
        ),
        verification=(
            {
                "check": (
                    "完整 after 的结构与转换机械检查、CAS 与写后回读已通过"
                    if replacement is None
                    else (
                        "完整 after 的结构与转换机械检查、CAS 与写后回读已通过；"
                        f"namespace={replacement.namespace_state}"
                    )
                ),
                "status": "passed",
                "scope": list(requested),
                "evidence": [working_tree_source, _CONTRACTS[mode]],
            },
        ),
        diagnostics=(_coordination_release_diagnostic(committed=True),)
        if coordination_release_uncertain and request.response_profile == "diagnostic"
        else (),
        follow_up=(_coordination_release_follow_up(requested) if coordination_release_uncertain else None),
    ),
        boundary=boundary,
        schemas=schemas,
        audit_contract=_INTEGRITY_CONTRACT,
    )


def _check_availability(
    mode: WorkCaseWriteMode,
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> AvailabilityEvaluation:
    domain = _validated_request(mode, request, context)
    requested = domain.fact_ref.to_json()
    if not native_atomic_fact_writes_supported():
        return AvailabilityEvaluation(
            availability="unavailable_for_request",
            unavailable_scope=(requested,),
            gaps=(
                {
                    "summary": "当前平台没有启用 WorkCase 写入的原生原子后端",
                    "scope": [requested],
                    "source_refs": [_SHARED_WRITE_CONTRACT],
                },
            ),
        )
    run = _governance(domain)
    boundary = _boundary(run)
    schemas = project_fact_schemas(repository)
    schema = schemas.get("workcase")
    if boundary is None or boundary.governed_project_id != domain.fact_ref.governed_project_id or schema is None:
        return AvailabilityEvaluation(
            availability="unavailable_for_request",
            unavailable_scope=(requested,),
            gaps=(
                {
                    "summary": "当前请求的管辖、项目或 WorkCase Schema 前置条件不成立",
                    "scope": [requested],
                    "source_refs": [_CONTRACTS[mode]],
                },
            ),
        )
    current = _current_read(boundary, schemas, domain.fact_ref.object_id)
    if mode == "recover":
        expected_check_status = _RECOVERY_REQUIRED_BEFORE_STATUS[domain.fact_ref.object_id]
        recover_unavailable = (
            current.check_status != expected_check_status
            or current.fields is None
            or current.fields.get("status") != "closed"
            or current.content_fingerprint != domain.expected_content_fingerprint
            or _has_recovery_marker(current.fields, domain.fact_ref.object_id)
        )
        if not recover_unavailable and domain.fact_ref.object_id == "workcase-0093":
            prerequisite = _current_read(boundary, schemas, "workcase-0092")
            recover_unavailable = (
                prerequisite.check_status != "mechanically_valid"
                or prerequisite.fields is None
                or prerequisite.fields.get("status") not in {"open", "blocked"}
                or not _has_recovery_marker(prerequisite.fields, "workcase-0092")
                or bool(_recovery_integrity_reference_issues(domain, prerequisite))
            )
    else:
        recover_unavailable = (
            current.check_status != "mechanically_valid"
            or current.content_fingerprint != domain.expected_content_fingerprint
        )
    if recover_unavailable:
        return AvailabilityEvaluation(
            availability="unavailable_for_request",
            unavailable_scope=(requested,),
            gaps=(
                {
                    "summary": "当前对象不可读取、不能进入该操作或请求指纹已过期",
                    "scope": [requested],
                    "source_refs": [_CONTRACTS[mode]],
                },
            ),
        )
    return AvailabilityEvaluation(availability="available_for_request", available_scope=(requested,))


def _update_call(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> OperationExecution:
    return _execute("update", request, repository, context)


def _close_call(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> OperationExecution:
    return _execute("close", request, repository, context)


def _begin_termination_call(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> OperationExecution:
    return _execute("begin_termination", request, repository, context)


def _complete_termination_call(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> OperationExecution:
    return _execute("complete_termination", request, repository, context)


def _correct_call(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> OperationExecution:
    return _execute("correct", request, repository, context)


def _recover_call(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> OperationExecution:
    return _execute("recover", request, repository, context)


def _update_availability(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> AvailabilityEvaluation:
    return _check_availability("update", request, repository, context)


def _close_availability(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> AvailabilityEvaluation:
    return _check_availability("close", request, repository, context)


def _begin_termination_availability(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> AvailabilityEvaluation:
    return _check_availability("begin_termination", request, repository, context)


def _complete_termination_availability(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> AvailabilityEvaluation:
    return _check_availability("complete_termination", request, repository, context)


def _correct_availability(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> AvailabilityEvaluation:
    return _check_availability("correct", request, repository, context)


def _recover_availability(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> AvailabilityEvaluation:
    return _check_availability("recover", request, repository, context)


UPDATE_WORKCASE_IMPLEMENTATION = OperationImplementation(
    required_inputs=UPDATE_REQUIRED_INPUTS,
    optional_inputs=UPDATE_OPTIONAL_INPUTS,
    evidence=(_IMPLEMENTATION_SOURCE, _CONTRACTS["update"]),
    check_availability=_update_availability,
    call=_update_call,
)
BEGIN_WORKCASE_TERMINATION_IMPLEMENTATION = OperationImplementation(
    required_inputs=BEGIN_TERMINATION_REQUIRED_INPUTS,
    optional_inputs=BEGIN_TERMINATION_OPTIONAL_INPUTS,
    evidence=(_IMPLEMENTATION_SOURCE, _CONTRACTS["begin_termination"]),
    check_availability=_begin_termination_availability,
    call=_begin_termination_call,
)
COMPLETE_WORKCASE_TERMINATION_IMPLEMENTATION = OperationImplementation(
    required_inputs=COMPLETE_TERMINATION_REQUIRED_INPUTS,
    optional_inputs=COMPLETE_TERMINATION_OPTIONAL_INPUTS,
    evidence=(_IMPLEMENTATION_SOURCE, _CONTRACTS["complete_termination"]),
    check_availability=_complete_termination_availability,
    call=_complete_termination_call,
)
CLOSE_WORKCASE_IMPLEMENTATION = OperationImplementation(
    required_inputs=CLOSE_REQUIRED_INPUTS,
    optional_inputs=CLOSE_OPTIONAL_INPUTS,
    evidence=(_IMPLEMENTATION_SOURCE, _CONTRACTS["close"]),
    check_availability=_close_availability,
    call=_close_call,
)
CORRECT_CLOSED_WORKCASE_IMPLEMENTATION = OperationImplementation(
    required_inputs=CORRECT_CLOSED_REQUIRED_INPUTS,
    optional_inputs=CORRECT_CLOSED_OPTIONAL_INPUTS,
    evidence=(_IMPLEMENTATION_SOURCE, _CONTRACTS["correct"]),
    check_availability=_correct_availability,
    call=_correct_call,
)
RECOVER_INVALID_WORKCASE_IMPLEMENTATION = OperationImplementation(
    required_inputs=RECOVER_REQUIRED_INPUTS,
    optional_inputs=RECOVER_OPTIONAL_INPUTS,
    evidence=(_IMPLEMENTATION_SOURCE, _CONTRACTS["recover"]),
    check_availability=_recover_availability,
    call=_recover_call,
)


__all__ = [
    "BEGIN_TERMINATION_OPERATION_KEY",
    "BEGIN_WORKCASE_TERMINATION_IMPLEMENTATION",
    "CLOSE_OPERATION_KEY",
    "CLOSE_WORKCASE_IMPLEMENTATION",
    "CORRECT_CLOSED_OPERATION_KEY",
    "CORRECT_CLOSED_WORKCASE_IMPLEMENTATION",
    "RECOVER_INVALID_OPERATION_KEY",
    "RECOVER_INVALID_WORKCASE_IMPLEMENTATION",
    "COMPLETE_TERMINATION_OPERATION_KEY",
    "COMPLETE_WORKCASE_TERMINATION_IMPLEMENTATION",
    "UPDATE_OPERATION_KEY",
    "UPDATE_WORKCASE_IMPLEMENTATION",
]
