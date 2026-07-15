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


def test_candidate_operation_discovers_four_real_templates_in_stable_order(
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


def test_content_operation_returns_exact_definition_and_complete_source_from_same_snapshot(
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
    assert "## 6. 验证要求" not in item["content"]
    assert "## 6. 验证要求" in item["source_content"]
    assert "## 8. Stop Conditions" in item["source_content"]
    assert hashlib.sha256(item["content"].encode()).hexdigest() == item["content_sha256"]
    assert hashlib.sha256(item["source_content"].encode()).hexdigest() == item["source_content_sha256"]


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
