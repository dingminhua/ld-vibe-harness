from __future__ import annotations

from pathlib import Path

import pytest

from ldvh.helper.operation_runtime import OperationExecutionContext
from ldvh.helper.operations.local_edit_request import (
    OPTIONAL_INPUTS,
    REQUIRED_INPUTS,
    parse_local_edit_request,
)
from ldvh.helper.requests import CommonRequest


def _request(
    arguments: dict[str, object],
    *,
    locators: tuple[str, ...] = (),
    disclosure: str | None = None,
    observed_context: dict[str, object] | None = None,
    authorization_reference: tuple[object, ...] = (),
) -> CommonRequest:
    return CommonRequest(
        task=None,
        work_object_locators=locators,
        arguments=arguments,
        requested_disclosure=disclosure,
        observed_context={} if observed_context is None else observed_context,
        authorization_reference=authorization_reference,
    )


def test_declares_source_kind_and_mode_specific_inputs() -> None:
    assert REQUIRED_INPUTS == ("arguments.source_kind",)
    assert OPTIONAL_INPUTS == (
        "arguments.responsibility_key",
        "arguments.heading_path",
        "arguments.fact_ref",
        "arguments.body_heading",
        "arguments.expected_baseline",
        "arguments.candidate_after",
        "work_object_locators",
    )


def test_parses_exact_rule_target() -> None:
    parsed = parse_local_edit_request(
        _request(
            {
                "source_kind": "rule",
                "responsibility_key": "ldvh-root",
                "heading_path": ["8. 系统级运行架构", "8.1 工作上下文的信息交付顺序与渐进式披露"],
                "expected_baseline": "a" * 64,
                "candidate_after": "candidate\n",
            }
        ),
        OperationExecutionContext(Path("/project")),
    )

    assert parsed.problems == ()
    assert parsed.request is not None
    assert parsed.request.source_kind == "rule"
    assert parsed.request.rule is not None
    assert parsed.request.rule.heading_path == ("8. 系统级运行架构", "8.1 工作上下文的信息交付顺序与渐进式披露")


def test_parses_study_target_with_fixed_body_heading() -> None:
    parsed = parse_local_edit_request(
        _request(
            {
                "source_kind": "study",
                "fact_ref": {"governed_project_id": "sample", "fact_type_key": "study", "object_id": "study-0001"},
                "body_heading": "建议",
            },
            locators=("/project",),
        ),
        OperationExecutionContext(Path("/project")),
    )

    assert parsed.problems == ()
    assert parsed.request is not None
    assert parsed.request.study is not None
    assert parsed.request.study.fact_ref.object_id == "study-0001"


@pytest.mark.parametrize(
    "arguments",
    (
        {
            "source_kind": "rule",
            "responsibility_key": "ldvh-root",
            "heading_path": ["8. 系统级运行架构"],
            "candidate_after": "",
        },
        {
            "source_kind": "study",
            "fact_ref": {"governed_project_id": "sample", "fact_type_key": "study", "object_id": "study-0001"},
            "body_heading": "建议",
            "candidate_after": "",
        },
    ),
)
def test_rejects_empty_candidate_after(arguments: dict[str, object]) -> None:
    parsed = parse_local_edit_request(_request(arguments), OperationExecutionContext(Path("/project")))

    assert parsed.request is None
    assert parsed.problems == ("arguments.candidate_after 必须是 null 或非空 string",)


@pytest.mark.parametrize(
    ("arguments", "locators", "problem"),
    (
        ({}, (), "arguments.source_kind 必须精确为 rule 或 study"),
        (
            {"source_kind": "rule", "responsibility_key": "x", "heading_path": ["one"], "fact_ref": {}},
            (),
            "source_kind=rule 禁止字段",
        ),
        ({"source_kind": "rule", "responsibility_key": "x", "heading_path": [" one"]}, (), "不得带首尾空白"),
        (
            {
                "source_kind": "study",
                "fact_ref": {"governed_project_id": "x", "fact_type_key": "spark", "object_id": "spark-0001"},
                "body_heading": "建议",
            },
            (),
            "必须精确等于 study",
        ),
        (
            {
                "source_kind": "study",
                "fact_ref": {"governed_project_id": "x", "fact_type_key": "study", "object_id": "study-0001"},
                "body_heading": "任意标题",
            },
            (),
            "只允许",
        ),
        (
            {
                "source_kind": "study",
                "fact_ref": {"governed_project_id": "x", "fact_type_key": "study", "object_id": "study-0001"},
                "body_heading": "建议",
                "heading_path": ["x"],
            },
            (),
            "source_kind=study 禁止字段",
        ),
    ),
)
def test_rejects_mixed_or_inexact_mode_inputs(
    arguments: dict[str, object], locators: tuple[str, ...], problem: str
) -> None:
    parsed = parse_local_edit_request(
        _request(arguments, locators=locators), OperationExecutionContext(Path("/project"))
    )

    assert parsed.request is None
    assert any(problem in item for item in parsed.problems)


@pytest.mark.parametrize(
    ("common_request", "problem"),
    (
        (
            _request(
                {"source_kind": "rule", "responsibility_key": "ldvh-root", "heading_path": ["8. 系统级运行架构"]},
                observed_context={"unexpected": True},
            ),
            "observed_context 对本操作必须为空 object",
        ),
        (
            _request(
                {"source_kind": "rule", "responsibility_key": "ldvh-root", "heading_path": ["8. 系统级运行架构"]},
                authorization_reference=("authorization",),
            ),
            "authorization_reference 对本只读操作必须为空 array",
        ),
        (
            _request(
                {"source_kind": "rule", "responsibility_key": "ldvh-root", "heading_path": ["8. 系统级运行架构"]},
                disclosure="L1",
            ),
            "requested_disclosure 对本操作必须为 null 或省略",
        ),
        (
            _request(
                {
                    "source_kind": "rule",
                    "responsibility_key": "ldvh-root",
                    "heading_path": ["8. 系统级运行架构"],
                    "unknown": True,
                }
            ),
            "arguments 包含未知字段: unknown",
        ),
    ),
)
def test_rejects_non_read_only_common_request_inputs(common_request: CommonRequest, problem: str) -> None:
    parsed = parse_local_edit_request(common_request, OperationExecutionContext(Path("/project")))

    assert parsed.request is None
    assert problem in parsed.problems
