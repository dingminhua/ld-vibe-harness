"""Expose the whole-library fact mechanical integrity check (specs 05 §11.9-11.10)."""

from __future__ import annotations

from typing import Any
from collections import Counter

from ldvh.facts.candidate_discovery import discover_fact_candidates
from ldvh.facts.contracts import LAYOUTS
from ldvh.facts.configuration_index import ConfigurationFactIndex
from ldvh.facts.identity import canonical_object_uid, short_reference
from ldvh.facts.schema import project_fact_schemas
from ldvh.governance.models import LocatorSource, ScopeDescriptor
from ldvh.governance.resolver import GovernanceResolutionRun, resolve_governance_scope
from ldvh.helper.operation_runtime import (
    AvailabilityEvaluation,
    OperationExecution,
    OperationExecutionContext,
    OperationImplementation,
    OperationRequestError,
)
from ldvh.helper.operations.fact_integrity_request import (
    OPTIONAL_INPUTS,
    REQUIRED_INPUTS,
    FactIntegrityRequest,
    parse_fact_integrity_request,
)
from ldvh.helper.operations.fact_operation_support import configuration_reading_boundaries, plain, reading_boundary
from ldvh.helper.requests import CommonRequest
from ldvh.helper.responses import source_reference
from ldvh.specs.repository import RepositoryInspection
from ldvh.testing.fact_integrity import assess_fact_snapshot

OPERATION_KEY = "check-fact-integrity"
_INPUT_CONTRACT = source_reference("rule", "fact-model-foundation::11.9 事实完整性机械检查输入字段")
_RESULT_CONTRACT = source_reference("rule", "fact-model-foundation::11.10 事实完整性机械检查结果字段")
_IMPLEMENTATION_EVIDENCE = (
    source_reference("implementation", "code/ldvh/helper/operations/fact_integrity_operation.py"),
    source_reference("implementation", "code/ldvh/testing/fact_integrity.py"),
    source_reference("implementation", "code/ldvh/facts/candidate_discovery.py"),
)


def _validated_request(request: CommonRequest, context: OperationExecutionContext) -> FactIntegrityRequest:
    parsed = parse_fact_integrity_request(request, context)
    if parsed.request is None:
        raise OperationRequestError(parsed.problems, sources=(_INPUT_CONTRACT,))
    return parsed.request


def _scope(domain: FactIntegrityRequest) -> dict[str, object]:
    return {
        "locator_index": 0,
        "locator": domain.locator,
        "source": "explicit_locator",
    }


def _governance(domain: FactIntegrityRequest) -> GovernanceResolutionRun:
    requested_scope = (ScopeDescriptor(0, domain.locator, LocatorSource.EXPLICIT_LOCATOR),)
    return resolve_governance_scope(
        requested_scope,
        base=domain.base,
        explicit_workspace_root=domain.workspace_root,
    )


def _unavailable(
    summary: str,
    scope: tuple[dict[str, object], ...],
    run: GovernanceResolutionRun,
    problems: tuple[dict[str, object], ...],
) -> OperationExecution:
    governance_json = None if run.result is None else run.result.to_json()
    sources = (
        (_INPUT_CONTRACT, _RESULT_CONTRACT) + tuple(plain(source) for source in run.sources) + _IMPLEMENTATION_EVIDENCE
    )
    return OperationExecution(
        outcome="unavailable",
        summary=summary,
        requested_scope=scope,
        not_completed_scope=scope,
        governance_resolution=governance_json,
        sources=sources,
        gaps=tuple(
            {
                "summary": problem.get("summary") or str(problem),
                "scope": list(scope),
                "source_refs": list(sources),
            }
            for problem in problems
        )
        or (
            {
                "summary": summary,
                "scope": list(scope),
                "source_refs": list(sources),
            },
        ),
    )


def _format_integrity_problem_summary(problem: dict[str, Any]) -> str:
    label = problem.get("canonical_path") or problem.get("fact_type_key") or "扫描边界"
    detail = (
        "; ".join(str(issue.get("summary")) for issue in problem.get("issues", ()) if isinstance(issue, dict))
        or problem.get("check_status")
        or "读取未完成"
    )
    return f"{label}: {detail}"


def execute_fact_integrity(
    domain: FactIntegrityRequest,
    repository: RepositoryInspection,
    *,
    scope: tuple[dict[str, object], ...] | None = None,
) -> OperationExecution:
    scope = (_scope(domain),) if scope is None else scope
    run = _governance(domain)
    boundary = reading_boundary(run)
    configuration_boundaries = configuration_reading_boundaries(run)
    if boundary is None or configuration_boundaries is None:
        return _unavailable(
            "当前管辖结果不能形成唯一事实完整性检查边界",
            scope,
            run,
            ({"summary": "管辖输入未形成同一项目、同一实际 worktree 和 common-dir 的唯一边界"},),
        )
    project_id, root, common_dir = boundary
    schemas = project_fact_schemas(repository)
    if set(schemas) != set(LAYOUTS):
        return _unavailable(
            "当前规则源不能形成五类型完整派生 Schema",
            scope,
            run,
            ({"summary": "五类型派生 Schema 不完整，不能形成可信全量检查"},),
        )

    configuration_index = ConfigurationFactIndex(configuration_boundaries, schemas)
    if not configuration_index.prepare():
        return _unavailable(
            "事实对象发现、读取或配置级 UID 索引未完成，不能形成可信全量检查",
            scope,
            run,
            ({"summary": "配置中至少一个项目未完成五类型 UID 全扫描"},),
        )
    snapshots = {
        candidate_project_id: discover_fact_candidates(
            candidate_root,
            candidate_project_id,
            candidate_common_dir,
            schemas,
            index=candidate_index,
        )
        for candidate_project_id, candidate_root, candidate_common_dir, candidate_index
        in configuration_index.project_indexes
    }
    snapshot = snapshots[project_id]
    assessed = {candidate_id: assess_fact_snapshot(candidate) for candidate_id, candidate in snapshots.items()}
    status, selected_problems = assessed[project_id]
    if any(candidate_status == "unavailable" for candidate_status, _ in assessed.values()):
        return _unavailable(
            "事实对象发现、读取或配置级 UID 索引未完成，不能形成可信全量检查",
            scope,
            run,
            tuple(
                {
                    "summary": _format_integrity_problem_summary(problem),
                    **problem,
                }
                for _, candidate_problems in assessed.values()
                for problem in candidate_problems
            ),
        )

    uid_entries: dict[str, list[tuple[str, str, str]]] = {}
    short_counts: Counter[str] = Counter()
    uid_index_object_count = 0
    for candidate_id, candidate in snapshots.items():
        uid_index_object_count += len(candidate.keys)
        for fact_type_key, object_id in candidate.keys:
            read = candidate.index.cache[(fact_type_key, object_id)]
            if read.fields is None:
                continue
            object_uid = canonical_object_uid(read.fields.get("object_uid"))
            if object_uid is None:
                continue
            uid_entries.setdefault(object_uid, []).append((candidate_id, fact_type_key, read.canonical_path))
            short_counts[short_reference(fact_type_key, object_uid)] += 1
    duplicate_problems: list[dict[str, object]] = []
    for object_uid, entries in uid_entries.items():
        if len(entries) < 2:
            continue
        paths = sorted({entry[2] for entry in entries})
        for _, fact_type_key, canonical_path in entries:
            duplicate_problems.append(
                {
                    "fact_type_key": fact_type_key,
                    "canonical_path": canonical_path,
                    "related_paths": [path for path in paths if path != canonical_path],
                    "check_status": "invalid",
                    "issues": [{"category": "identity", "field_path": "object_uid", "summary": "object_uid 在当前选定管辖配置中重复"}],
                }
            )
    problems = [
        {**problem, "related_paths": list(problem.get("related_paths", []))}
        for problem in selected_problems
    ] + duplicate_problems
    if problems:
        status = "partial"

    governance_json = None if run.result is None else run.result.to_json()
    sources = (
        (_INPUT_CONTRACT, _RESULT_CONTRACT) + tuple(plain(source) for source in run.sources) + _IMPLEMENTATION_EVIDENCE
    )
    result_json: dict[str, Any] = {
        "status": status,
        "object_count": len(snapshot.keys),
        "uid_index_object_count": uid_index_object_count,
        "short_ref_collision_group_count": sum(count > 1 for count in short_counts.values()),
        "problems": [dict(problem) for problem in problems],
    }
    return OperationExecution(
        outcome="ok",
        summary=f"已完成当前事实库全量机械完整性检查：{status}（{len(snapshot.keys)} 个对象）",
        result=result_json,
        requested_scope=scope,
        completed_scope=scope,
        governance_resolution=governance_json,
        sources=sources,
        verification=(
            {
                "check": "05 事实完整性机械检查",
                "status": status,
                "scope": list(scope),
                "evidence": list(sources),
            },
        ),
    )


def _execute(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> OperationExecution:
    return execute_fact_integrity(_validated_request(request, context), repository)


def _check_availability(
    request: CommonRequest,
    repository: RepositoryInspection,
    context: OperationExecutionContext,
) -> AvailabilityEvaluation:
    execution = _execute(request, repository, context)
    if execution.outcome == "ok":
        return AvailabilityEvaluation(
            availability="available_for_request",
            available_scope=execution.completed_scope,
        )
    return AvailabilityEvaluation(
        availability="unavailable_for_request",
        unavailable_scope=execution.requested_scope,
        gaps=execution.gaps,
    )


FACT_INTEGRITY_IMPLEMENTATION = OperationImplementation(
    required_inputs=REQUIRED_INPUTS,
    optional_inputs=OPTIONAL_INPUTS,
    evidence=_IMPLEMENTATION_EVIDENCE,
    check_availability=_check_availability,
    call=_execute,
)

__all__ = ["FACT_INTEGRITY_IMPLEMENTATION", "OPERATION_KEY", "execute_fact_integrity"]
