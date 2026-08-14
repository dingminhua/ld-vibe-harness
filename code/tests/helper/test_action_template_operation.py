from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from ldvh.helper.operation_runtime import OperationExecutionContext, OperationRequestError
from ldvh.helper.operations.action_template_operation import (
    ACTION_TEMPLATE_CANDIDATE_IMPLEMENTATION,
    ACTION_TEMPLATE_CONTENT_IMPLEMENTATION,
)
from ldvh.helper.requests import CommonRequest
from ldvh.specs.repository import inspect_repository


def _request(*keys: str, disclosure: str | None = None) -> CommonRequest:
    return CommonRequest(
        task=None,
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
