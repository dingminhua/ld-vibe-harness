from __future__ import annotations

import pytest

from ldvh.helper.operations.specification_context_request import (
    OPTIONAL_INPUTS,
    REQUIRED_INPUTS,
    parse_specification_context_request,
)
from ldvh.helper.requests import CommonRequest


def _request(arguments: dict[str, object], *, disclosure: str | None = "L3") -> CommonRequest:
    return CommonRequest(
        task="ignored task",
        work_object_locators=("ignored-object",),
        arguments=arguments,
        requested_disclosure=disclosure,
        observed_context={},
        authorization_reference=({"kind": "human", "locator": "ignored-authorization"},),
    )


def test_parses_empty_and_multiple_primary_paths_without_consuming_common_selection_fields() -> None:
    parsed = parse_specification_context_request(
        _request(
            {
                "contexts": [
                    {"responsibility_key": "ldvh-root", "primary_heading_paths": []},
                    {
                        "responsibility_key": "specification-model-foundation",
                        "primary_heading_paths": [["5. 基础术语", "5.1 规范文档（Specification）"]],
                    },
                ]
            }
        )
    )

    assert parsed.problems == ()
    assert parsed.request is not None
    assert [context.as_scope() for context in parsed.request.contexts] == [
        {"responsibility_key": "ldvh-root", "primary_heading_paths": []},
        {
            "responsibility_key": "specification-model-foundation",
            "primary_heading_paths": [["5. 基础术语", "5.1 规范文档（Specification）"]],
        },
    ]
    assert REQUIRED_INPUTS == ("arguments.contexts", "requested_disclosure")
    assert OPTIONAL_INPUTS == ()


@pytest.mark.parametrize(
    "common_request",
    (
        _request({"contexts": []}),
        _request({"contexts": [{"responsibility_key": "ldvh-root", "primary_heading_paths": []}]}, disclosure="L4"),
        _request({"contexts": [{"responsibility_key": "bad key", "primary_heading_paths": []}]}),
        _request(
            {
                "contexts": [
                    {
                        "responsibility_key": "ldvh-root",
                        "primary_heading_paths": [["9. 验证要求"], ["9. 验证要求", "child"]],
                    }
                ]
            }
        ),
        _request(
            {
                "contexts": [
                    {"responsibility_key": "ldvh-root", "primary_heading_paths": []},
                    {"responsibility_key": "ldvh-root", "primary_heading_paths": []},
                ]
            }
        ),
        _request({"contexts": [{"responsibility_key": "ldvh-root", "primary_heading_paths": []}], "extra": True}),
    ),
)
def test_rejects_closed_contract_violations(common_request: CommonRequest) -> None:
    parsed = parse_specification_context_request(common_request)

    assert parsed.request is None
    assert parsed.problems


def test_rejects_nonempty_observed_context() -> None:
    request = _request({"contexts": [{"responsibility_key": "ldvh-root", "primary_heading_paths": []}]})
    request = CommonRequest(
        task=request.task,
        work_object_locators=request.work_object_locators,
        arguments=request.arguments,
        requested_disclosure=request.requested_disclosure,
        observed_context={"inferred": True},
        authorization_reference=request.authorization_reference,
    )

    parsed = parse_specification_context_request(request)

    assert parsed.request is None
    assert "observed_context 在本操作中必须为空对象" in parsed.problems
