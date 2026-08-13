from __future__ import annotations

from collections.abc import Callable
from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import Any

import pytest

from ldvh.facts.models import FactReference
from ldvh.governance.models import LocatorSource, ScopeDescriptor
from ldvh.helper.operation_runtime import OperationExecutionContext
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
    BeginWorkCaseTerminationRequest,
    CloseWorkCaseRequest,
    CompleteWorkCaseTerminationRequest,
    CorrectClosedWorkCaseRequest,
    RouteTargetFingerprint,
    UpdateWorkCaseRequest,
    WorkCaseWriteRequestParseResult,
    parse_begin_workcase_termination_request,
    parse_close_workcase_request,
    parse_complete_workcase_termination_request,
    parse_correct_closed_workcase_request,
    parse_update_workcase_request,
)
from ldvh.helper.requests import CommonRequest

CWD = Path("/workspace/current-worktree")
FINGERPRINT = "a" * 64
TARGET_FINGERPRINT = "b" * 64
HUMAN_REFERENCE = {"kind": "human", "locator": "turn:12"}

Parser = Callable[[CommonRequest, OperationExecutionContext], WorkCaseWriteRequestParseResult]


def _fact_ref(*, project: str = "ldvh", object_id: str = "workcase-0006") -> dict[str, str]:
    return {
        "governed_project_id": project,
        "fact_type_key": "workcase",
        "object_id": object_id,
    }


def _fact_object(**changes: object) -> dict[str, object]:
    value: dict[str, object] = {
        "title": "Current WorkCase",
        "status": "open",
        "phase": "executing",
    }
    value.update(changes)
    return value


def _closed_fact_object() -> dict[str, object]:
    value = _fact_object(status="closed")
    value.pop("phase")
    return value


def _arguments(**changes: object) -> dict[str, object]:
    value: dict[str, object] = {
        "fact_ref": _fact_ref(),
        "expected_content_fingerprint": FINGERPRINT,
        "fact_object": _fact_object(),
    }
    value.update(changes)
    return value


def _correct_arguments(**changes: object) -> dict[str, object]:
    value = _arguments(
        fact_object=_closed_fact_object(),
        route_target_fingerprints=[],
        independent_review_reference=None,
    )
    value.update(changes)
    return value


def _request(
    arguments: dict[str, object],
    *,
    locators: tuple[str | dict[str, Any], ...] = (),
    authorization: tuple[dict[str, Any], ...] = (HUMAN_REFERENCE,),
    observed_context: dict[str, Any] | None = None,
    requested_disclosure: str | None = None,
) -> CommonRequest:
    return CommonRequest(
        task="write one WorkCase",
        work_object_locators=locators,
        arguments=arguments,
        requested_disclosure=requested_disclosure,
        observed_context=(
            {
                "signature": {
                    "product_name": "test",
                    "model_name": "test-model",
                    "agent_runtime_name": "pytest",
                }
            }
            if observed_context is None
            else observed_context
        ),
        authorization_reference=authorization,
    )


def _parse(parser: Parser, request: CommonRequest) -> WorkCaseWriteRequestParseResult:
    return parser(request, OperationExecutionContext(cwd=CWD))


def test_update_parses_one_complete_after_request() -> None:
    after = _fact_object(summary="Stable checkpoint")
    result = _parse(
        parse_update_workcase_request,
        _request(
            _arguments(workspace_root="/workspace", fact_object=after),
            locators=("relative/object",),
        ),
    )

    assert result.problems == ()
    assert result.request == UpdateWorkCaseRequest(
        workspace_root=Path("/workspace"),
        governance_scope=(ScopeDescriptor(0, "relative/object", LocatorSource.EXPLICIT_LOCATOR),),
        fact_ref=FactReference("ldvh", "workcase", "workcase-0006"),
        expected_content_fingerprint=FINGERPRINT,
        fact_object=after,
        authorization_reference=(HUMAN_REFERENCE,),
        base=CWD,
    )


def test_close_requires_and_preserves_nonempty_human_authorization() -> None:
    after = _fact_object(status="closed")
    parsed = _parse(parse_close_workcase_request, _request(_arguments(fact_object=after)))

    assert parsed.problems == ()
    assert isinstance(parsed.request, CloseWorkCaseRequest)
    assert parsed.request.fact_object == after
    assert parsed.request.authorization_reference == (HUMAN_REFERENCE,)

    missing = _parse(
        parse_close_workcase_request,
        _request(_arguments(fact_object=after), authorization=()),
    )
    assert missing.request is None
    assert any("authorization_reference" in problem for problem in missing.problems)


def test_close_rejects_whitespace_only_authorization_members_from_a_common_request() -> None:
    parsed = _parse(
        parse_close_workcase_request,
        _request(
            _arguments(fact_object=_closed_fact_object()),
            authorization=({"kind": "   ", "locator": "\t"},),
        ),
    )

    assert parsed.request is None
    assert sum("非空白字符" in problem for problem in parsed.problems) == 2
    assert any("authorization_reference[0].kind" in problem for problem in parsed.problems)
    assert any("authorization_reference[0].locator" in problem for problem in parsed.problems)


def test_correct_parses_route_snapshots_and_nullable_review_reference() -> None:
    route = {
        "target": _fact_ref(object_id="workcase-0042"),
        "content_fingerprint": TARGET_FINGERPRINT,
    }
    parsed = _parse(
        parse_correct_closed_workcase_request,
        _request(_correct_arguments(route_target_fingerprints=[route])),
    )

    assert parsed.problems == ()
    assert parsed.request == CorrectClosedWorkCaseRequest(
        workspace_root=None,
        governance_scope=(ScopeDescriptor(0, str(CWD), LocatorSource.CWD),),
        fact_ref=FactReference("ldvh", "workcase", "workcase-0006"),
        expected_content_fingerprint=FINGERPRINT,
        fact_object=_closed_fact_object(),
        authorization_reference=(HUMAN_REFERENCE,),
        base=CWD,
        route_target_fingerprints=(
            RouteTargetFingerprint(
                FactReference("ldvh", "workcase", "workcase-0042"),
                TARGET_FINGERPRINT,
            ),
        ),
        independent_review_reference=None,
    )


def test_correct_accepts_one_common_source_reference_for_independent_review() -> None:
    reference = {
        "kind": "review",
        "locator": "review:workcase-0006:closed-correction",
        "observed_at": "2026-07-26T15:00:00+08:00",
        "details": {"scope": "complete before and after"},
    }
    parsed = _parse(
        parse_correct_closed_workcase_request,
        _request(_correct_arguments(independent_review_reference=reference)),
    )

    assert parsed.problems == ()
    assert isinstance(parsed.request, CorrectClosedWorkCaseRequest)
    assert parsed.request.independent_review_reference == reference


def test_correct_rejects_whitespace_only_independent_review_reference() -> None:
    parsed = _parse(
        parse_correct_closed_workcase_request,
        _request(
            _correct_arguments(
                independent_review_reference={"kind": "   ", "locator": "\t"},
            )
        ),
    )

    assert parsed.request is None
    assert sum("非空白字符" in problem for problem in parsed.problems) == 2
    assert any("arguments.independent_review_reference.kind" in problem for problem in parsed.problems)
    assert any("arguments.independent_review_reference.locator" in problem for problem in parsed.problems)


@pytest.mark.parametrize(
    ("parser", "arguments"),
    (
        (parse_update_workcase_request, _arguments(set={"summary": "old delta"})),
        (parse_update_workcase_request, _arguments(remove=["waiting_on"])),
        (parse_update_workcase_request, _arguments(managed_records={})),
        (parse_close_workcase_request, _arguments(set={})),
        (parse_correct_closed_workcase_request, _correct_arguments(remove=[])),
    ),
)
def test_retired_delta_arguments_are_unknown(parser: Parser, arguments: dict[str, object]) -> None:
    parsed = _parse(parser, _request(arguments))

    assert parsed.request is None
    assert any("arguments 包含未知字段" in problem for problem in parsed.problems)


@pytest.mark.parametrize("field", ("object_uid", "object_id", "fact_type_key", "created_at", "updated_at"))
def test_complete_after_rejects_code_managed_fields(field: str) -> None:
    parsed = _parse(
        parse_update_workcase_request,
        _request(_arguments(fact_object={**_fact_object(), field: "caller supplied"})),
    )

    assert parsed.request is None
    assert any("Code 托管字段" in problem and field in problem for problem in parsed.problems)


def test_fact_object_schema_membership_is_left_to_the_current_core_schema() -> None:
    parsed = _parse(
        parse_update_workcase_request,
        _request(_arguments(fact_object={**_fact_object(), "unknown_domain_field": True})),
    )

    assert isinstance(parsed.request, UpdateWorkCaseRequest)


@pytest.mark.parametrize(
    ("changes", "expected"),
    (
        ({"unknown": True}, "未知字段"),
        ({"workspace_root": "relative"}, "绝对路径"),
        ({"fact_ref": []}, "fact_ref 必须是 object"),
        (
            {"fact_ref": {**_fact_ref(), "fact_type_key": "spark"}},
            "fact_type_key 必须精确等于 workcase",
        ),
        ({"fact_ref": _fact_ref(object_id="bad")}, "object_id 必须匹配"),
        ({"expected_content_fingerprint": "A" * 64}, "64 位小写"),
        ({"fact_object": []}, "fact_object 必须是 object"),
    ),
)
def test_common_full_after_request_shape_is_closed(changes: dict[str, object], expected: str) -> None:
    parsed = _parse(parse_update_workcase_request, _request(_arguments(**changes)))

    assert parsed.request is None
    assert any(expected in problem for problem in parsed.problems)


def test_workcase_reference_and_locator_nonempty_checks_reject_whitespace_only_values() -> None:
    reference = _parse(
        parse_update_workcase_request,
        _request(_arguments(fact_ref=_fact_ref(project="   "))),
    )
    locator = _parse(
        parse_update_workcase_request,
        _request(_arguments(), locators=("\t",)),
    )

    assert reference.request is None
    assert any("fact_ref.governed_project_id" in problem and "非空白字符" in problem for problem in reference.problems)
    assert locator.request is None
    assert any("work_object_locators[0]" in problem for problem in locator.problems)


@pytest.mark.parametrize(
    ("changes", "expected"),
    (
        ({"route_target_fingerprints": None}, "必须是 array"),
        ({"route_target_fingerprints": [{}]}, "缺少字段"),
        (
            {
                "route_target_fingerprints": [
                    {
                        "target": _fact_ref(object_id="workcase-0042"),
                        "content_fingerprint": "A" * 64,
                    }
                ]
            },
            "64 位小写",
        ),
        (
            {
                "route_target_fingerprints": [
                    {
                        "target": _fact_ref(project="other", object_id="workcase-0042"),
                        "content_fingerprint": TARGET_FINGERPRINT,
                    }
                ]
            },
            "同一项目",
        ),
        ({"independent_review_reference": []}, "必须是对象"),
        (
            {"independent_review_reference": {"kind": "review", "locator": ""}},
            "locator 必须是非空",
        ),
    ),
)
def test_correct_specific_members_are_closed_and_typed(changes: dict[str, object], expected: str) -> None:
    parsed = _parse(
        parse_correct_closed_workcase_request,
        _request(_correct_arguments(**changes)),
    )

    assert parsed.request is None
    assert any(expected in problem for problem in parsed.problems)


def test_correct_requires_both_operation_specific_fields_even_when_null_is_allowed() -> None:
    parsed = _parse(
        parse_correct_closed_workcase_request,
        _request(_arguments()),
    )

    assert parsed.request is None
    assert any("route_target_fingerprints 必填" in problem for problem in parsed.problems)
    assert any("independent_review_reference 必填" in problem for problem in parsed.problems)


def test_correct_rejects_duplicate_route_targets() -> None:
    route = {
        "target": _fact_ref(object_id="workcase-0042"),
        "content_fingerprint": TARGET_FINGERPRINT,
    }
    parsed = _parse(
        parse_correct_closed_workcase_request,
        _request(_correct_arguments(route_target_fingerprints=[route, route])),
    )

    assert parsed.request is None
    assert any("不得包含重复 target" in problem for problem in parsed.problems)


def test_empty_locators_use_actual_cwd_and_requests_are_immutable() -> None:
    parsed = _parse(parse_update_workcase_request, _request(_arguments()))
    assert isinstance(parsed.request, UpdateWorkCaseRequest)
    assert parsed.request.governance_scope == (ScopeDescriptor(0, str(CWD), LocatorSource.CWD),)

    with pytest.raises(FrozenInstanceError):
        parsed.request.base = Path("/changed")  # type: ignore[misc]


def test_common_operation_restrictions_are_enforced() -> None:
    observed = _parse(
        parse_update_workcase_request,
        _request(_arguments(), observed_context={"tool": "output"}),
    )
    disclosure = _parse(
        parse_update_workcase_request,
        _request(_arguments(), requested_disclosure="L1"),
    )
    object_locator = _parse(
        parse_update_workcase_request,
        _request(_arguments(), locators=({"path": "/workspace"},)),
    )

    assert observed.request is None
    assert disclosure.request is None
    assert object_locator.request is None


def test_input_metadata_matches_the_three_public_contracts() -> None:
    assert UPDATE_REQUIRED_INPUTS == (
        "arguments.fact_ref",
        "arguments.expected_content_fingerprint",
        "arguments.fact_object",
    )
    assert UPDATE_OPTIONAL_INPUTS == (
        "work_object_locators",
        "arguments.workspace_root",
        "authorization_reference",
    )
    assert CLOSE_REQUIRED_INPUTS == (*UPDATE_REQUIRED_INPUTS, "authorization_reference")
    assert CLOSE_OPTIONAL_INPUTS == ("work_object_locators", "arguments.workspace_root")
    assert CORRECT_CLOSED_REQUIRED_INPUTS == (
        *UPDATE_REQUIRED_INPUTS,
        "arguments.route_target_fingerprints",
        "arguments.independent_review_reference",
    )
    assert CORRECT_CLOSED_OPTIONAL_INPUTS == UPDATE_OPTIONAL_INPUTS
    assert BEGIN_TERMINATION_REQUIRED_INPUTS == (*UPDATE_REQUIRED_INPUTS, "authorization_reference")
    assert BEGIN_TERMINATION_OPTIONAL_INPUTS == CLOSE_OPTIONAL_INPUTS
    assert COMPLETE_TERMINATION_REQUIRED_INPUTS == UPDATE_REQUIRED_INPUTS
    assert COMPLETE_TERMINATION_OPTIONAL_INPUTS == CLOSE_OPTIONAL_INPUTS


def test_termination_parsers_enforce_one_human_instruction_without_second_gate() -> None:
    begun = _parse(parse_begin_workcase_termination_request, _request(_arguments()))
    assert isinstance(begun.request, BeginWorkCaseTerminationRequest)

    missing_human = _parse(
        parse_begin_workcase_termination_request,
        _request(_arguments(), authorization=()),
    )
    assert missing_human.request is None

    completed = _parse(
        parse_complete_workcase_termination_request,
        _request(_arguments(fact_object=_closed_fact_object()), authorization=()),
    )
    assert isinstance(completed.request, CompleteWorkCaseTerminationRequest)

    repeated_gate = _parse(
        parse_complete_workcase_termination_request,
        _request(_arguments(fact_object=_closed_fact_object())),
    )
    assert repeated_gate.request is None
