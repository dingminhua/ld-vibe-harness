from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import Any

import pytest

from ldvh.governance.models import LocatorSource, ScopeDescriptor
from ldvh.helper.operation_runtime import OperationExecutionContext
from ldvh.helper.operations.governance_scope_request import (
    OPTIONAL_INPUTS,
    REQUIRED_INPUTS,
    GovernanceScopeRequest,
    parse_governance_scope_request,
)
from ldvh.helper.requests import CommonRequest

CWD = Path("/workspace/current-worktree")


def _request(
    *,
    locators: tuple[str | dict[str, Any], ...] = (),
    arguments: dict[str, Any] | None = None,
    observed_context: dict[str, Any] | None = None,
    task: str | None = None,
    requested_disclosure: str | None = None,
    authorization_reference: tuple[dict[str, Any], ...] = (),
) -> CommonRequest:
    return CommonRequest(
        task=task,
        work_object_locators=locators,
        arguments={} if arguments is None else arguments,
        requested_disclosure=requested_disclosure,
        observed_context={} if observed_context is None else observed_context,
        authorization_reference=authorization_reference,
    )


def _parse(request: CommonRequest, *, cwd: Path = CWD):
    return parse_governance_scope_request(request, OperationExecutionContext(cwd=cwd))


def test_empty_locators_use_actual_cwd_as_the_single_fallback_scope() -> None:
    result = _parse(_request())

    assert result.problems == ()
    assert result.request == GovernanceScopeRequest(
        workspace_root=None,
        requested_scope=(ScopeDescriptor(0, str(CWD), LocatorSource.CWD),),
        base=CWD,
    )


def test_explicit_locators_preserve_order_duplicates_and_original_text() -> None:
    result = _parse(_request(locators=("relative/file", "/absolute/file", "relative/file")))

    assert result.problems == ()
    assert result.request == GovernanceScopeRequest(
        workspace_root=None,
        requested_scope=(
            ScopeDescriptor(0, "relative/file", LocatorSource.EXPLICIT_LOCATOR),
            ScopeDescriptor(1, "/absolute/file", LocatorSource.EXPLICIT_LOCATOR),
            ScopeDescriptor(2, "relative/file", LocatorSource.EXPLICIT_LOCATOR),
        ),
        base=CWD,
    )


def test_workspace_root_is_parsed_but_not_checked_for_existence() -> None:
    root = "/workspace/does-not-need-to-exist-yet"
    result = _parse(_request(arguments={"workspace_root": root}))

    assert result.problems == ()
    assert result.request is not None
    assert result.request.workspace_root == Path(root)


@pytest.mark.parametrize("value", ["", "relative/root", 1, None, {}, []])
def test_workspace_root_must_be_a_non_empty_absolute_string(value: object) -> None:
    result = _parse(_request(arguments={"workspace_root": value}))

    assert result.request is None
    assert result.problems == ("arguments.workspace_root 必须是非空绝对路径 string",)


@pytest.mark.parametrize("locator", ["", {}, {"path": "/workspace/object"}])
def test_locator_members_must_be_non_empty_path_strings(locator: str | dict[str, Any]) -> None:
    result = _parse(_request(locators=("valid", locator, "valid")))

    assert result.request is None
    assert result.problems == ("work_object_locators[1] 必须是非空路径 string",)


def test_unknown_argument_and_observed_context_fields_are_closed_and_sorted() -> None:
    result = _parse(
        _request(
            arguments={"z": 1, "workspace_root": "/workspace", "a": 2},
            observed_context={"vendor": "payload", "cwd": "/forged"},
        )
    )

    assert result.request is None
    assert result.problems == (
        "arguments 包含未知字段: a, z",
        "observed_context 包含本操作未知字段: cwd, vendor",
    )


def test_relative_process_cwd_is_rejected_even_for_absolute_locator() -> None:
    result = _parse(_request(locators=("/workspace/object",)), cwd=Path("relative/cwd"))

    assert result.request is None
    assert result.problems == ("Helper 进程实际 cwd 必须是绝对路径",)


def test_task_disclosure_and_authorization_do_not_change_domain_request() -> None:
    reference = ({"kind": "authorization", "locator": "human:decision-1"},)
    baseline = _parse(_request(locators=("object",)))
    decorated = _parse(
        _request(
            locators=("object",),
            task="不要从这里猜测工作对象",
            requested_disclosure="L4",
            authorization_reference=reference,
        )
    )

    assert decorated == baseline


def test_all_operation_input_problems_are_reported_deterministically() -> None:
    result = _parse(
        _request(
            locators=("", {}, "valid"),
            arguments={"z": 1, "a": 2, "workspace_root": "relative"},
            observed_context={"z": 1, "a": 2},
        ),
        cwd=Path("relative"),
    )

    assert result.request is None
    assert result.problems == (
        "Helper 进程实际 cwd 必须是绝对路径",
        "work_object_locators[0] 必须是非空路径 string",
        "work_object_locators[1] 必须是非空路径 string",
        "arguments 包含未知字段: a, z",
        "arguments.workspace_root 必须是非空绝对路径 string",
        "observed_context 包含本操作未知字段: a, z",
    )


def test_domain_request_and_parse_result_are_immutable() -> None:
    result = _parse(_request())
    assert result.request is not None

    with pytest.raises(FrozenInstanceError):
        result.request.base = Path("/changed")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.problems = ("changed",)  # type: ignore[misc]


def test_capability_input_metadata_matches_the_public_operation_contract() -> None:
    assert REQUIRED_INPUTS == ()
    assert OPTIONAL_INPUTS == ("work_object_locators", "arguments.workspace_root")
