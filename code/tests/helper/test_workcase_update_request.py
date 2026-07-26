from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import Any

import pytest

from ldvh.facts.models import FactReference
from ldvh.facts.schema import FactSchema, ProjectedField
from ldvh.governance.models import LocatorSource, ScopeDescriptor
from ldvh.helper.operation_runtime import OperationExecutionContext
from ldvh.helper.operations.workcase_update_request import (
    OPTIONAL_INPUTS,
    REQUIRED_INPUTS,
    WorkCaseUpdateRequest,
    parse_workcase_update_request,
    workcase_top_level_fields,
)
from ldvh.helper.requests import CommonRequest

CWD = Path("/workspace/current-worktree")
FINGERPRINT = "a" * 64


def _field(path: str, json_type: str = "string") -> ProjectedField:
    return ProjectedField(path, json_type, "conditional", None, "workcase-fact-type::test")


SCHEMA = FactSchema(
    "workcase",
    tuple(
        _field(path)
        for path in (
            "object_id",
            "fact_type_key",
            "created_at",
            "updated_at",
            "workcase_profile",
            "title",
            "status",
            "phase",
            "summary",
            "priority",
            "resume_from",
            "waiting_on",
            "blocking_summary",
            "goal",
            "scope",
            "plan_version",
            "result_version",
            "work_items[].item_id",
            "controller_check_summary",
            "validation_summary",
            "audit_summary[].audit_id",
            "creation_reviews[].reviewer",
            "result_reviews[].reviewer",
            "execution_approval.summary",
            "closure_approval.summary",
            "progress_history.coverage",
            "improvement_observations[].observation_id",
            "nonbinding_followups[].followup_id",
        )
    ),
)


def _arguments(**changes: object) -> dict[str, object]:
    value: dict[str, object] = {
        "fact_ref": {
            "governed_project_id": "ldvh",
            "fact_type_key": "workcase",
            "object_id": "workcase-0006",
        },
        "expected_content_fingerprint": FINGERPRINT,
        "set": {"summary": "Updated"},
        "remove": [],
        "managed_records": {},
    }
    value.update(changes)
    return value


def _request(
    *,
    arguments: dict[str, object] | None = None,
    locators: tuple[str | dict[str, Any], ...] = (),
    observed_context: dict[str, Any] | None = None,
    requested_disclosure: str | None = None,
) -> CommonRequest:
    return CommonRequest(
        task="ignored",
        work_object_locators=locators,
        arguments=_arguments() if arguments is None else arguments,
        requested_disclosure=requested_disclosure,
        observed_context={} if observed_context is None else observed_context,
        authorization_reference=({"kind": "human", "locator": "turn:1"},),
    )


def _parse(request: CommonRequest, *, schema: FactSchema | None = SCHEMA):
    return parse_workcase_update_request(
        request,
        OperationExecutionContext(cwd=CWD),
        schema,
    )


def test_parses_closed_request_and_projects_nested_schema_fields_to_top_level() -> None:
    result = _parse(
        _request(
            arguments=_arguments(
                workspace_root="/workspace",
                set={"summary": "Updated", "work_items": [{"item_id": "item-01"}]},
                remove=["waiting_on"],
            ),
            locators=("relative/object",),
        )
    )

    assert result.problems == ()
    assert result.request == WorkCaseUpdateRequest(
        workspace_root=Path("/workspace"),
        governance_scope=(ScopeDescriptor(0, "relative/object", LocatorSource.EXPLICIT_LOCATOR),),
        fact_ref=FactReference("ldvh", "workcase", "workcase-0006"),
        expected_content_fingerprint=FINGERPRINT,
        set_fields={"summary": "Updated", "work_items": [{"item_id": "item-01"}]},
        remove_fields=("waiting_on",),
        managed_records={},
        authorization_reference=({"kind": "human", "locator": "turn:1"},),
        base=CWD,
    )
    assert "work_items" in workcase_top_level_fields(SCHEMA)


def test_empty_locators_use_actual_cwd_scope_and_result_is_immutable() -> None:
    result = _parse(_request())
    assert result.request is not None
    assert result.request.governance_scope == (ScopeDescriptor(0, str(CWD), LocatorSource.CWD),)

    with pytest.raises(FrozenInstanceError):
        result.request.base = Path("/changed")  # type: ignore[misc]


@pytest.mark.parametrize(
    ("changes", "problem"),
    (
        ({"unknown": True}, "arguments 包含未知字段"),
        ({"workspace_root": "relative"}, "workspace_root"),
        ({"fact_ref": []}, "fact_ref 必须是 object"),
        (
            {
                "fact_ref": {
                    "governed_project_id": "ldvh",
                    "fact_type_key": "spark",
                    "object_id": "spark-0001",
                }
            },
            "fact_type_key 必须精确等于 workcase",
        ),
        (
            {
                "fact_ref": {
                    "governed_project_id": "ldvh",
                    "fact_type_key": "workcase",
                    "object_id": "bad",
                }
            },
            "object_id 必须匹配",
        ),
        ({"expected_content_fingerprint": "A" * 64}, "64 位小写"),
        ({"set": []}, "arguments.set 必须是 object"),
        ({"remove": {}}, "arguments.remove 必须是 array"),
        ({"managed_records": []}, "managed_records 必须是 object"),
    ),
)
def test_rejects_argument_shape_and_identity_errors(changes: dict[str, object], problem: str) -> None:
    result = _parse(_request(arguments=_arguments(**changes)))

    assert result.request is None
    assert any(problem in item for item in result.problems)


def test_closes_ordinary_delta_against_current_schema_and_managed_fields() -> None:
    result = _parse(
        _request(
            arguments=_arguments(
                set={"vendor": 1, "updated_at": "forged", "summary": "x"},
                remove=["title", "title", "plan_version", "result_reviews", "summary"],
            )
        )
    )

    assert result.request is None
    assert any("未在当前 WorkCase Schema" in item and "vendor" in item for item in result.problems)
    assert any("remove 成员不得重复" in item for item in result.problems)
    assert any("set 不得触碰 Helper 托管字段" in item for item in result.problems)
    assert any("remove 不得触碰 Helper 托管字段" in item for item in result.problems)
    assert any("remove 不得包含版本字段" in item for item in result.problems)
    assert any("set 与 arguments.remove 不得交叉" in item for item in result.problems)


def test_schema_membership_can_be_deferred_until_current_schema_is_available() -> None:
    result = _parse(_request(arguments=_arguments(set={"future_field": "value"})), schema=None)

    assert result.problems == ()
    assert result.request is not None
    assert result.request.set_fields == {"future_field": "value"}


@pytest.mark.parametrize("name", ("plan_version", "result_version"))
@pytest.mark.parametrize("value", (True, 0, -1, "1"))
def test_set_versions_must_be_positive_integers(name: str, value: object) -> None:
    set_fields: dict[str, object] = {name: value}
    if name == "plan_version":
        set_fields["phase"] = "human_plan_confirming"
    managed = {"replace_creation_reviews": []} if name == "plan_version" else {}
    result = _parse(_request(arguments=_arguments(set=set_fields, managed_records=managed)))

    assert result.request is None
    assert any(f"set.{name} 必须是正整数" in item for item in result.problems)


def test_plan_version_requires_only_replacement_reviews_and_fixed_phase() -> None:
    result = _parse(
        _request(
            arguments=_arguments(
                set={"plan_version": 2, "phase": "executing", "result_version": 2},
                managed_records={
                    "append_result_reviews": [],
                    "execution_approval": None,
                },
            )
        )
    )

    assert result.request is None
    assert any("set.phase=human_plan_confirming" in item for item in result.problems)
    assert any("要求同次 replace_creation_reviews" in item for item in result.problems)
    assert any("只允许 replace_creation_reviews" in item for item in result.problems)
    assert any("固定 reset 字段" in item and "result_version" in item for item in result.problems)


@pytest.mark.parametrize("managed_reset_field", ("execution_approval", "result_reviews", "closure_approval"))
def test_plan_bump_cannot_redeclare_helper_managed_reset_fields_in_remove(managed_reset_field: str) -> None:
    result = _parse(
        _request(
            arguments=_arguments(
                set={"plan_version": 2, "phase": "human_plan_confirming"},
                remove=[managed_reset_field],
                managed_records={
                    "replace_creation_reviews": [
                        {
                            "reviewer": "reviewer-1",
                            "scope": "Current plan",
                            "conclusion": "pass",
                        }
                    ]
                },
            )
        )
    )

    assert result.request is None
    assert any("remove 不得触碰 Helper 托管字段" in problem for problem in result.problems)


def test_valid_plan_replacement_review_has_exact_shape() -> None:
    review = {
        "reviewer": "reviewer-1",
        "scope": "Current plan",
        "conclusion": "pass",
        "feedback": ["Plan is coherent"],
        "controller_resolution": "Accepted.",
    }
    result = _parse(
        _request(
            arguments=_arguments(
                set={"plan_version": 2, "phase": "human_plan_confirming"},
                managed_records={"replace_creation_reviews": [review]},
            )
        )
    )

    assert result.problems == ()
    assert result.request is not None
    assert result.request.managed_records == {"replace_creation_reviews": [review]}


def test_review_feedback_is_optional_only_for_plain_pass() -> None:
    passed = _parse(
        _request(
            arguments=_arguments(
                set={"plan_version": 2, "phase": "human_plan_confirming"},
                managed_records={
                    "replace_creation_reviews": [
                        {"reviewer": "reviewer-1", "scope": "Current plan", "conclusion": "pass"}
                    ]
                },
            )
        )
    )
    assert passed.problems == ()

    needless_resolution = _parse(
        _request(
            arguments=_arguments(
                set={"plan_version": 2, "phase": "human_plan_confirming"},
                managed_records={
                    "replace_creation_reviews": [
                        {
                            "reviewer": "reviewer-1",
                            "scope": "Current plan",
                            "conclusion": "pass",
                            "controller_resolution": "Nothing to resolve",
                        }
                    ]
                },
            )
        )
    )
    assert needless_resolution.request is None
    assert any("没有 feedback 时必须省略" in item for item in needless_resolution.problems)

    missing_feedback = _parse(
        _request(
            arguments=_arguments(
                set={},
                managed_records={
                    "append_result_reviews": [
                        {"reviewer": "reviewer-1", "scope": "Current result", "conclusion": "blocked"}
                    ]
                },
            )
        )
    )
    assert missing_feedback.request is None
    assert any("feedback 对非 pass conclusion 必须提供" in item for item in missing_feedback.problems)


@pytest.mark.parametrize(
    ("managed", "problem"),
    (
        ({"unknown": []}, "包含未知字段"),
        ({"append_result_reviews": {}}, "必须是 array 或 null"),
        (
            {
                "append_result_reviews": [
                    {
                        "reviewer": "reviewer",
                        "scope": "result",
                        "conclusion": "pass",
                        "feedback": ["same", "same"],
                    }
                ]
            },
            "feedback 成员不得重复",
        ),
        (
            {
                "resolve_result_reviews": [
                    {"review_index": 0, "controller_resolution": "done"},
                    {"review_index": 0, "controller_resolution": "again"},
                ]
            },
            "review_index 不得重复",
        ),
        ({"execution_approval": {"summary": ""}}, "summary 必须是非空 string"),
        ({"progress_transition": {"summary": "", "extra": True}}, "包含未知字段"),
        (
            {
                "closure_approval": {
                    "summary": "approved",
                    "source_refs": [{"kind": "human", "locator": "turn", "extra": True}],
                }
            },
            "source_refs[0] 包含未知字段",
        ),
    ),
)
def test_managed_record_members_are_closed_and_typed(
    managed: dict[str, object],
    problem: str,
) -> None:
    set_fields = {"summary": "updated"}
    if "closure_approval" in managed:
        set_fields = {"status": "closed", "phase": "closed"}
    result = _parse(_request(arguments=_arguments(set=set_fields, managed_records=managed)))

    assert result.request is None
    assert any(problem in item for item in result.problems)


def test_managed_action_limit_and_action_exclusivity_are_structural() -> None:
    reviews = [
        {
            "reviewer": f"reviewer-{index}",
            "scope": "result",
            "conclusion": "pass",
            "feedback": [f"feedback-{index}"],
        }
        for index in range(17)
    ]
    over_limit = _parse(_request(arguments=_arguments(set={}, managed_records={"append_result_reviews": reviews})))
    mixed = _parse(
        _request(
            arguments=_arguments(
                managed_records={
                    "append_result_reviews": [],
                    "resolve_result_reviews": [],
                    "execution_approval": {"summary": "approved"},
                }
            )
        )
    )

    assert any("最多包含 16" in item for item in over_limit.problems)
    assert any("append_result_reviews 与 resolve_result_reviews" in item for item in mixed.problems)
    assert any("execution_approval 不得与其它" in item for item in mixed.problems)


def test_result_review_append_allows_only_review_context_companions() -> None:
    review = {"reviewer": "reviewer", "scope": "Current result", "conclusion": "pass"}
    allowed = _parse(
        _request(
            arguments=_arguments(
                set={"phase": "controller_checking", "summary": "Review completed"},
                remove=["blocking_summary"],
                managed_records={"append_result_reviews": [review]},
            )
        )
    )
    rejected = _parse(
        _request(
            arguments=_arguments(
                set={"controller_check_summary": "Changed reviewed subject", "work_items": []},
                remove=["validation_summary"],
                managed_records={"append_result_reviews": [review]},
            )
        )
    )

    assert allowed.problems == ()
    assert allowed.request is not None
    assert rejected.request is None
    assert any("不得变更被审结果主体" in problem for problem in rejected.problems)


def test_approval_source_reference_accepts_typed_details() -> None:
    result = _parse(
        _request(
            arguments=_arguments(
                managed_records={
                    "execution_approval": {
                        "summary": "Human approved",
                        "source_refs": [
                            {
                                "kind": "human-input",
                                "locator": "turn-1",
                                "details": {"channel": "current-task"},
                            }
                        ],
                    }
                }
            )
        )
    )

    assert result.problems == ()
    assert result.request is not None


def test_execution_approval_is_a_complete_managed_action_without_progress_transition() -> None:
    result = _parse(
        _request(
            arguments=_arguments(
                set={"phase": "executing"},
                managed_records={"execution_approval": {"summary": "Human approved"}},
            )
        )
    )

    assert result.problems == ()
    assert result.request is not None
    assert result.request.managed_records == {"execution_approval": {"summary": "Human approved"}}


def test_v2_only_update_rejects_registered_v1_process_fields() -> None:
    for field_name, value in {
        "audit_summary": [],
        "progress_history": {"coverage": "full"},
        "improvement_observations": [],
        "nonbinding_followups": [],
    }.items():
        result = _parse(_request(arguments=_arguments(set={field_name: value})))
        assert result.request is None
        assert any("禁止 V1-only 字段" in item and field_name in item for item in result.problems)

        removed = _parse(_request(arguments=_arguments(set={}, remove=[field_name])))
        assert removed.request is None
        assert any("禁止 V1-only 字段" in item and field_name in item for item in removed.problems)


def test_approval_source_reference_details_must_be_object() -> None:
    result = _parse(
        _request(
            arguments=_arguments(
                managed_records={
                    "execution_approval": {
                        "summary": "Human approved",
                        "source_refs": [{"kind": "human-input", "locator": "turn-1", "details": "not-an-object"}],
                    }
                }
            )
        )
    )

    assert result.request is None
    assert any("details 出现时必须是 object" in item for item in result.problems)


def test_closure_approval_requires_explicit_closed_status_and_phase() -> None:
    result = _parse(
        _request(arguments=_arguments(managed_records={"closure_approval": {"summary": "Human approved closure"}}))
    )

    assert result.request is None
    assert any("set.status=closed" in item for item in result.problems)


def test_withdraw_execution_approval_requires_explicit_human_plan_phase() -> None:
    missing = _parse(
        _request(
            arguments=_arguments(
                set={"summary": "Human withdrew the recorded approval"},
                managed_records={"withdraw_execution_approval": {"summary": "Human withdrew approval"}},
            )
        )
    )
    valid_shape = _parse(
        _request(
            arguments=_arguments(
                set={"phase": "human_plan_confirming"},
                managed_records={"withdraw_execution_approval": {"summary": "Human withdrew approval"}},
            )
        )
    )

    assert missing.request is None
    assert any("set.phase=human_plan_confirming" in problem for problem in missing.problems)
    assert valid_shape.problems == ()
    assert valid_shape.request is not None


def test_all_three_delta_inputs_cannot_be_empty_or_null_only() -> None:
    result = _parse(
        _request(
            arguments=_arguments(
                set={},
                remove=[],
                managed_records={"execution_approval": None},
            )
        )
    )

    assert result.request is None
    assert any("不得同时为空" in item for item in result.problems)


@pytest.mark.parametrize(
    "name",
    ("replace_creation_reviews", "append_result_reviews", "resolve_result_reviews"),
)
def test_managed_record_arrays_are_nonempty_when_present(name: str) -> None:
    set_fields = {"plan_version": 2, "phase": "human_plan_confirming"} if name == "replace_creation_reviews" else {}
    result = _parse(
        _request(
            arguments=_arguments(
                set=set_fields,
                managed_records={name: []},
            )
        )
    )

    assert result.request is None
    assert any("出现时必须是非空 array" in item for item in result.problems)


def test_common_operation_restrictions_are_enforced() -> None:
    result = parse_workcase_update_request(
        _request(
            locators=("", {}),
            observed_context={"forged": True},
            requested_disclosure="L3",
        ),
        OperationExecutionContext(cwd=Path("relative")),
        SCHEMA,
    )

    assert result.request is None
    assert any("cwd 必须是绝对路径" in item for item in result.problems)
    assert sum("必须是非空路径 string" in item for item in result.problems) == 2
    assert any("observed_context" in item for item in result.problems)
    assert any("requested_disclosure" in item for item in result.problems)


def test_input_metadata_matches_public_contract() -> None:
    assert REQUIRED_INPUTS == (
        "arguments.fact_ref",
        "arguments.expected_content_fingerprint",
        "arguments.set",
        "arguments.remove",
        "arguments.managed_records",
    )
    assert OPTIONAL_INPUTS == (
        "work_object_locators",
        "arguments.workspace_root",
        "authorization_reference",
    )
