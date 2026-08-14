from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from ldvh.diagnostics import Issue, SourceLocation
from ldvh.helper.operation_runtime import OperationExecutionContext, OperationRequestError
from ldvh.helper.operations import action_template_operation
from ldvh.helper.operations.action_template_operation import (
    ACTION_TEMPLATE_CANDIDATE_IMPLEMENTATION,
    ACTION_TEMPLATE_CONTENT_IMPLEMENTATION,
)
from ldvh.helper.requests import CommonRequest
from ldvh.specs.action_templates import ActionTemplateSourceInspection, inspect_action_template_sources
from ldvh.specs.repository import inspect_repository

CANDIDATE_FIELDS = {
    "template_key",
    "summary",
    "activation_hint",
    "source_key",
    "canonical_path",
    "definition_ref",
    "definition_heading",
    "definition_start_line",
    "definition_end_line",
}
CONTENT_FIELDS = CANDIDATE_FIELDS | {"content", "content_sha256", "source_content_sha256"}


def _request(*keys: str, disclosure: str | None = None, task: str | None = None) -> CommonRequest:
    return CommonRequest(
        task=task,
        work_object_locators=(),
        arguments={} if not keys else {"template_keys": list(keys)},
        requested_disclosure=disclosure,
        observed_context={},
        authorization_reference=(),
    )


def test_candidate_operation_discovers_five_real_templates_in_stable_order(
    current_specs_repository: Path,
) -> None:
    repository = inspect_repository(current_specs_repository)

    execution = ACTION_TEMPLATE_CANDIDATE_IMPLEMENTATION.call(
        _request(),
        repository,
        OperationExecutionContext(cwd=current_specs_repository),
    )

    assert execution.outcome == "ok"
    assert (
        execution.requested_scope
        == execution.completed_scope
        == (
            "environment-integration-installation-verification",
            "fact-object-controlled-creation",
            "fact-object-lifecycle-change",
            "git-commit",
            "workcase-approved-plan-execution",
        )
    )
    assert execution.not_completed_scope == ()
    assert execution.result is not None
    items = execution.result["items"]
    assert isinstance(items, list)
    assert [item["template_key"] for item in items] == list(execution.completed_scope)
    assert all(set(item) == CANDIDATE_FIELDS for item in items)
    assert all(isinstance(item["activation_hint"], str) and item["activation_hint"] for item in items)
    assert all(item["definition_start_line"] <= item["definition_end_line"] for item in items)
    assert execution.result["unchecked_conditions"]
    assert execution.changes == ()


def test_candidate_exact_selection_keeps_order_and_reports_partial(
    current_specs_repository: Path,
) -> None:
    repository = inspect_repository(current_specs_repository)

    execution = ACTION_TEMPLATE_CANDIDATE_IMPLEMENTATION.call(
        _request("git-commit", "unknown-template", "fact-object-controlled-creation"),
        repository,
        OperationExecutionContext(cwd=current_specs_repository),
    )

    assert execution.outcome == "partial"
    assert execution.completed_scope == ("git-commit", "fact-object-controlled-creation")
    assert execution.not_completed_scope == ("unknown-template",)
    assert execution.result is not None
    assert [item["template_key"] for item in execution.result["items"]] == [
        "git-commit",
        "fact-object-controlled-creation",
    ]
    assert any("未从当前有效行动模板声明" in gap["summary"] for gap in execution.gaps)


def test_content_operation_returns_executable_package_without_duplicate_source_body(
    current_specs_repository: Path,
) -> None:
    repository = inspect_repository(current_specs_repository)

    execution = ACTION_TEMPLATE_CONTENT_IMPLEMENTATION.call(
        _request("fact-object-lifecycle-change"),
        repository,
        OperationExecutionContext(cwd=current_specs_repository),
    )

    assert execution.outcome == "ok"
    assert execution.result is not None
    item = execution.result["items"][0]
    assert set(item) == CONTENT_FIELDS
    assert item["activation_hint"]
    assert item["content"].startswith("## 5. 事实对象生命周期变更与承接处置行动模板定义\n")
    assert "## 6. 验证要求" in item["content"]
    assert "## 7. Human Gate" in item["content"]
    assert "## 8. Stop Conditions" in item["content"]
    assert "source_content" not in item
    assert hashlib.sha256(item["content"].encode()).hexdigest() == item["content_sha256"]
    source = (current_specs_repository / item["canonical_path"]).read_text(encoding="utf-8")
    assert hashlib.sha256(source.encode()).hexdigest() == item["source_content_sha256"]


def test_workcase_execution_template_keeps_result_review_out_of_work_items(
    current_specs_repository: Path,
) -> None:
    """Keep one explicit bad plan as a source-delivery contract, not an NLP validator."""

    invalid_item_goal = "全部实现完成后安排独立结果复核"
    invalid_criterion_statement = "独立结果复核确认本 WorkCase 未引入来源语义削弱"
    workcase_source = (current_specs_repository / "specs/21-WorkCase-工作项.md").read_text(encoding="utf-8")
    execution = ACTION_TEMPLATE_CONTENT_IMPLEMENTATION.call(
        _request("workcase-approved-plan-execution"),
        inspect_repository(current_specs_repository),
        OperationExecutionContext(cwd=current_specs_repository),
    )
    creation = ACTION_TEMPLATE_CONTENT_IMPLEMENTATION.call(
        _request("fact-object-controlled-creation"),
        inspect_repository(current_specs_repository),
        OperationExecutionContext(cwd=current_specs_repository),
    )

    assert execution.outcome == "ok"
    assert execution.result is not None
    assert creation.outcome == "ok"
    assert creation.result is not None
    delivered_template_package = execution.result["items"][0]["content"]
    delivered_creation_package = creation.result["items"][0]["content"]
    assert invalid_item_goal in workcase_source
    assert invalid_item_goal in delivered_template_package
    assert invalid_criterion_statement in workcase_source
    assert invalid_criterion_statement in delivered_template_package
    assert invalid_criterion_statement in delivered_creation_package
    assert "不得被写成 item" in workcase_source
    assert "保留当前批准的授权包并自动返回执行，不再次请求 Human" in delivered_template_package
    assert "将受影响 item 据实取消并转入结果链" in delivered_template_package
    assert "Code 不判断自然语言是否属于生命周期关口" in workcase_source
    assert "Code 不从关键词或字段形状替 AI 作出结论" in delivered_template_package


def test_fact_write_templates_deliver_process_checks_and_direct_write_rejection(
    current_specs_repository: Path,
) -> None:
    execution = ACTION_TEMPLATE_CONTENT_IMPLEMENTATION.call(
        _request("git-commit", "fact-object-controlled-creation", "fact-object-lifecycle-change"),
        inspect_repository(current_specs_repository),
        OperationExecutionContext(cwd=current_specs_repository),
    )

    assert execution.outcome == "ok"
    assert execution.result is not None
    content_by_key = {item["template_key"]: item["content"] for item in execution.result["items"]}
    for content in content_by_key.values():
        assert "绕过 Helper" in content
        assert "`ldvh-base/`" in content
        assert "`check-fact-integrity`" in content
        assert "result.status=complete" in content
        assert "`precheck-git-commit`" in content
        assert "result.mechanical_outcome=passed" in content

    assert "不得用提交预检或 Git Gate 把该候选追认为合规写入" in content_by_key["git-commit"]
    for key in ("fact-object-controlled-creation", "fact-object-lifecycle-change"):
        assert "精确回读与整库机械审计互不替代" in content_by_key[key]
        assert "无论 Helper 外层 `outcome` 为何" in content_by_key[key]
        assert "共同 `changes`" in content_by_key[key]

    assert "无法排除任何事实源写入" in content_by_key["fact-object-controlled-creation"]
    assert "不得等待或假定其它目标回读全部完成" in content_by_key["fact-object-lifecycle-change"]


def test_git_commit_template_requires_real_index_and_real_hook_event(
    current_specs_repository: Path,
) -> None:
    execution = ACTION_TEMPLATE_CONTENT_IMPLEMENTATION.call(
        _request("git-commit"),
        inspect_repository(current_specs_repository),
        OperationExecutionContext(cwd=current_specs_repository),
    )

    assert execution.outcome == "ok"
    assert execution.result is not None
    content = execution.result["items"][0]["content"]
    assert "AI 已明确声明的当次候选文件清单" in content
    assert "逐文件审核对应 diff" in content
    assert "当前真实 Index" in content
    assert "未声明、无关或归属无法确认的 staged 内容" in content
    assert "不得触碰、代为 unstage、覆盖、清空或改用临时/alternate Index" in content
    assert "common-dir `commit-msg` Git Hook" in content
    assert "不带 `--no-verify` 的原生本地 `git commit`" in content
    assert "该真实事件必须实际触发" in content
    assert "Helper 不可用或调用错误都必须保留诊断并停止本次 commit 创建" in content


def test_candidate_and_content_share_hint_and_ignore_task_for_selection(
    current_specs_repository: Path,
) -> None:
    repository = inspect_repository(current_specs_repository)
    context = OperationExecutionContext(cwd=current_specs_repository)
    baseline = ACTION_TEMPLATE_CANDIDATE_IMPLEMENTATION.call(_request(), repository, context)
    tasked = ACTION_TEMPLATE_CANDIDATE_IMPLEMENTATION.call(
        _request(task="This metadata must not filter, rank, or select templates."),
        repository,
        context,
    )
    content = ACTION_TEMPLATE_CONTENT_IMPLEMENTATION.call(
        _request("git-commit", task="This metadata is not an applicability decision."),
        repository,
        context,
    )

    assert tasked.outcome == baseline.outcome == "ok"
    assert tasked.result == baseline.result
    assert content.result is not None
    content_item = content.result["items"][0]
    assert baseline.result is not None
    candidate_item = next(item for item in baseline.result["items"] if item["template_key"] == "git-commit")
    assert content_item["activation_hint"] == candidate_item["activation_hint"]
    assert set(content_item) == set(candidate_item) | {"content", "content_sha256", "source_content_sha256"}
    assert {"applicable", "authorized", "activated", "executable"}.isdisjoint(content_item)


def _inspection_with_issue(repository, *, keep_candidates: bool) -> ActionTemplateSourceInspection:
    inspected = inspect_action_template_sources(repository)
    issue = Issue(
        summary="Synthetic incomplete action-template declaration source.",
        location=SourceLocation("specs/broken-template-source.md", 12),
        affected=("broken-template-source",),
    )
    return ActionTemplateSourceInspection(
        candidate_declarations=inspected.candidate_declarations if keep_candidates else (),
        issues=(*inspected.issues, issue),
        incomplete_sources=(*inspected.incomplete_sources, "broken-template-source"),
        unchecked_conditions=inspected.unchecked_conditions,
    )


def test_all_candidate_read_keeps_valid_template_scope_and_discloses_incomplete_source(
    current_specs_repository: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = inspect_repository(current_specs_repository)
    inspection = _inspection_with_issue(repository, keep_candidates=True)
    monkeypatch.setattr(action_template_operation, "inspect_action_template_sources", lambda _repository: inspection)

    execution = ACTION_TEMPLATE_CANDIDATE_IMPLEMENTATION.call(
        _request(),
        repository,
        OperationExecutionContext(cwd=current_specs_repository),
    )

    assert execution.outcome == "ok"
    assert execution.completed_scope
    assert execution.not_completed_scope == ()
    assert all(scope != "broken-template-source" for scope in execution.requested_scope)
    assert any(gap["scope"] == [] and "broken-template-source" in gap["summary"] for gap in execution.gaps)
    assert any(item["details"]["path"] == "specs/broken-template-source.md" for item in execution.diagnostics)


def test_all_candidate_read_is_unavailable_when_only_incomplete_sources_remain(
    current_specs_repository: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = inspect_repository(current_specs_repository)
    inspection = _inspection_with_issue(repository, keep_candidates=False)
    monkeypatch.setattr(action_template_operation, "inspect_action_template_sources", lambda _repository: inspection)

    execution = ACTION_TEMPLATE_CANDIDATE_IMPLEMENTATION.call(
        _request(),
        repository,
        OperationExecutionContext(cwd=current_specs_repository),
    )

    assert execution.outcome == "unavailable"
    assert execution.result is None
    assert execution.requested_scope == execution.completed_scope == execution.not_completed_scope == ()
    assert execution.gaps
    assert execution.diagnostics


def test_exact_valid_key_remains_ok_while_disclosing_unrelated_incomplete_source(
    current_specs_repository: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = inspect_repository(current_specs_repository)
    inspection = _inspection_with_issue(repository, keep_candidates=True)
    monkeypatch.setattr(action_template_operation, "inspect_action_template_sources", lambda _repository: inspection)

    execution = ACTION_TEMPLATE_CANDIDATE_IMPLEMENTATION.call(
        _request("git-commit"),
        repository,
        OperationExecutionContext(cwd=current_specs_repository),
    )

    assert execution.outcome == "ok"
    assert execution.completed_scope == ("git-commit",)
    assert execution.not_completed_scope == ()
    assert any(gap["scope"] == [] and "broken-template-source" in gap["summary"] for gap in execution.gaps)


def test_exact_missing_key_does_not_claim_absence_when_any_source_is_incomplete(
    current_specs_repository: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = inspect_repository(current_specs_repository)
    inspection = _inspection_with_issue(repository, keep_candidates=True)
    monkeypatch.setattr(action_template_operation, "inspect_action_template_sources", lambda _repository: inspection)

    execution = ACTION_TEMPLATE_CANDIDATE_IMPLEMENTATION.call(
        _request("missing-template"),
        repository,
        OperationExecutionContext(cwd=current_specs_repository),
    )

    assert execution.outcome == "unavailable"
    assert execution.not_completed_scope == ("missing-template",)
    missing_gap = next(gap for gap in execution.gaps if gap["scope"] == ["missing-template"])
    assert "无法" in missing_gap["summary"]
    assert "遮蔽" in missing_gap["summary"]


def test_content_operation_requires_nonempty_exact_keys_and_null_disclosure(
    current_specs_repository: Path,
) -> None:
    repository = inspect_repository(current_specs_repository)
    context = OperationExecutionContext(cwd=current_specs_repository)

    with pytest.raises(OperationRequestError) as empty:
        ACTION_TEMPLATE_CONTENT_IMPLEMENTATION.call(_request(), repository, context)
    with pytest.raises(OperationRequestError) as disclosed:
        ACTION_TEMPLATE_CONTENT_IMPLEMENTATION.call(_request("git-commit", disclosure="L4"), repository, context)

    assert "至少一个成员" in empty.value.problems[0]
    assert "requested_disclosure 必须为 null" in disclosed.value.problems


def test_capability_availability_uses_same_exact_candidate_boundary(current_specs_repository: Path) -> None:
    repository = inspect_repository(current_specs_repository)
    availability = ACTION_TEMPLATE_CONTENT_IMPLEMENTATION.check_availability(
        _request("git-commit", "missing-template"),
        repository,
        OperationExecutionContext(cwd=current_specs_repository),
    )

    assert availability.availability == "partially_available"
    assert availability.available_scope == ("git-commit",)
    assert availability.unavailable_scope == ("missing-template",)
