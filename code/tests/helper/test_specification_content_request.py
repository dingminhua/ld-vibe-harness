from __future__ import annotations

import pytest

from ldvh.helper.operations.specification_content_request import (
    OPTIONAL_INPUTS,
    REQUIRED_INPUTS,
    SpecificationContentSelection,
    parse_specification_content_request,
)
from ldvh.helper.requests import CommonRequest


def _common(
    *,
    arguments: dict[str, object],
    disclosure: str | None,
    observed_context: dict[str, object] | None = None,
) -> CommonRequest:
    return CommonRequest(
        task="ignored but legal",
        work_object_locators=("/ignored",),
        arguments=arguments,
        requested_disclosure=disclosure,
        observed_context={} if observed_context is None else observed_context,
        authorization_reference=(),
    )


def test_declares_only_the_two_required_domain_inputs() -> None:
    assert REQUIRED_INPUTS == ("arguments.selections", "requested_disclosure")
    assert OPTIONAL_INPUTS == ()


def test_parses_multiple_exact_l3_selections_in_request_order() -> None:
    parsed = parse_specification_content_request(
        _common(
            disclosure="L3",
            arguments={
                "selections": [
                    {"responsibility_key": "one", "heading_path": ["2. Scope"]},
                    {"responsibility_key": "two", "heading_path": ["3. Rules", "Rule A"]},
                ]
            },
        )
    )

    assert parsed.problems == ()
    assert parsed.request is not None
    assert parsed.request.disclosure == "L3"
    assert parsed.request.selections == (
        SpecificationContentSelection("one", ("2. Scope",)),
        SpecificationContentSelection("two", ("3. Rules", "Rule A")),
    )
    assert parsed.request.selections[0].as_scope() == {
        "responsibility_key": "one",
        "heading_path": ["2. Scope"],
    }


def test_parses_l4_only_with_null_heading_path() -> None:
    parsed = parse_specification_content_request(
        _common(
            disclosure="L4",
            arguments={"selections": [{"responsibility_key": "one", "heading_path": None}]},
        )
    )

    assert parsed.problems == ()
    assert parsed.request is not None
    assert parsed.request.selections == (SpecificationContentSelection("one", None),)


@pytest.mark.parametrize(
    ("arguments", "disclosure", "observed", "problem"),
    (
        ({}, "L4", {}, "arguments.selections 必须是非空 array"),
        ({"selections": []}, "L4", {}, "arguments.selections 必须是非空 array"),
        ({"selections": "one"}, "L4", {}, "arguments.selections 必须是非空 array"),
        ({"selections": ["one"]}, "L4", {}, "arguments.selections[0] 必须是 object"),
        (
            {"selections": [{"responsibility_key": "one", "heading_path": None, "extra": True}]},
            "L4",
            {},
            "包含未知字段: extra",
        ),
        (
            {"selections": [{"responsibility_key": "", "heading_path": None}]},
            "L4",
            {},
            "responsibility_key 必须是非空 string",
        ),
        (
            {"selections": [{"responsibility_key": "one", "heading_path": ["Only"]}]},
            "L4",
            {},
            "requested_disclosure=L4 时必须为 null",
        ),
        (
            {"selections": [{"responsibility_key": "one", "heading_path": None}]},
            "L3",
            {},
            "requested_disclosure=L3 时必须是",
        ),
        (
            {"selections": [{"responsibility_key": "one", "heading_path": []}]},
            "L3",
            {},
            "长度只允许 1 或 2",
        ),
        (
            {"selections": [{"responsibility_key": "one", "heading_path": [" One"]}]},
            "L3",
            {},
            "不得带首尾空白",
        ),
        (
            {"selections": [{"responsibility_key": "one", "heading_path": None}]},
            None,
            {},
            "requested_disclosure 必填",
        ),
        (
            {"selections": [{"responsibility_key": "one", "heading_path": None}], "extra": True},
            "L4",
            {},
            "arguments 包含未知字段: extra",
        ),
        (
            {"selections": [{"responsibility_key": "one", "heading_path": None}]},
            "L4",
            {"cache": True},
            "observed_context 在本操作中必须为空对象",
        ),
    ),
)
def test_rejects_non_contract_inputs(
    arguments: dict[str, object],
    disclosure: str | None,
    observed: dict[str, object],
    problem: str,
) -> None:
    parsed = parse_specification_content_request(
        _common(arguments=arguments, disclosure=disclosure, observed_context=observed)
    )

    assert parsed.request is None
    assert any(problem in item for item in parsed.problems)


def test_rejects_duplicate_exact_selection() -> None:
    selection = {"responsibility_key": "one", "heading_path": ["2. Scope"]}
    parsed = parse_specification_content_request(
        _common(arguments={"selections": [selection, dict(selection)]}, disclosure="L3")
    )

    assert parsed.request is None
    assert "arguments.selections 的精确选择不得重复" in parsed.problems
