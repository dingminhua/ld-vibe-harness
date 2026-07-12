from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from ldvh.helper.operations.specification_candidate_request import (
    OPTIONAL_INPUTS,
    REQUIRED_INPUTS,
    SpecificationCandidateRequest,
    parse_specification_candidate_request,
)
from ldvh.helper.requests import CommonRequest

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _request(
    *,
    arguments: dict[str, Any] | None = None,
    requested_disclosure: str | None = None,
) -> CommonRequest:
    return CommonRequest(
        task=None,
        work_object_locators=(),
        arguments={} if arguments is None else arguments,
        requested_disclosure=requested_disclosure,
        observed_context={},
        authorization_reference=(),
    )


@pytest.mark.parametrize("arguments", [None, {}, {"responsibility_keys": []}])
def test_missing_or_empty_responsibility_keys_selects_all_candidates(
    arguments: dict[str, Any] | None,
) -> None:
    result = parse_specification_candidate_request(_request(arguments=arguments))

    assert result.problems == ()
    assert result.request == SpecificationCandidateRequest((), "L0")


@pytest.mark.parametrize(
    ("requested", "expected"),
    [(None, "L0"), ("L0", "L0"), ("L1", "L1"), ("L2", "L2")],
)
def test_supported_disclosure_is_normalized(
    requested: str | None,
    expected: str,
) -> None:
    result = parse_specification_candidate_request(
        _request(
            arguments={"responsibility_keys": ["specification-model-foundation"]},
            requested_disclosure=requested,
        )
    )

    assert result.problems == ()
    assert result.request == SpecificationCandidateRequest(("specification-model-foundation",), expected)


@pytest.mark.parametrize("requested", ["L3", "L4"])
def test_l3_and_l4_are_explicitly_rejected_without_downgrade(requested: str) -> None:
    result = parse_specification_candidate_request(_request(requested_disclosure=requested))

    assert result.request is None
    assert result.problems == (f"requested_disclosure={requested} 不受本操作支持；只允许 L0、L1、L2 或 null",)


@pytest.mark.parametrize(
    ("arguments", "problem"),
    [
        ({"unknown": []}, "arguments 包含未知字段: unknown"),
        (
            {"responsibility_keys": "specification-model-foundation"},
            "arguments.responsibility_keys 必须是 array",
        ),
        (
            {"responsibility_keys": [""]},
            "arguments.responsibility_keys[0] 必须是非空 string",
        ),
        (
            {"responsibility_keys": [1]},
            "arguments.responsibility_keys[0] 必须是非空 string",
        ),
        (
            {"responsibility_keys": ["a", "a"]},
            "arguments.responsibility_keys 的成员不得重复",
        ),
    ],
)
def test_invalid_arguments_return_only_domain_input_problems(
    arguments: dict[str, Any],
    problem: str,
) -> None:
    result = parse_specification_candidate_request(_request(arguments=arguments))

    assert result.request is None
    assert problem in result.problems


def test_all_domain_input_problems_are_reported_deterministically() -> None:
    result = parse_specification_candidate_request(
        _request(
            arguments={"z": 1, "a": 2, "responsibility_keys": ["key", "key", None]},
            requested_disclosure="L4",
        )
    )

    assert result.request is None
    assert result.problems == (
        "arguments 包含未知字段: a, z",
        "arguments.responsibility_keys[2] 必须是非空 string",
        "arguments.responsibility_keys 的成员不得重复",
        "requested_disclosure=L4 不受本操作支持；只允许 L0、L1、L2 或 null",
    )


def test_capability_input_descriptions_are_anchored_to_current_source() -> None:
    source = (PROJECT_ROOT / "specs/01-规范模型基础规范.md").read_text(encoding="utf-8")
    section = source.split("### 9.4 规范候选读取输入字段", 1)[1].split("### 9.5 规范候选读取结果字段", 1)[0]

    assert REQUIRED_INPUTS == ()
    assert OPTIONAL_INPUTS == (
        "arguments.responsibility_keys",
        "requested_disclosure",
    )
    assert "`responsibility_keys` | array | 可选" in section
    assert "`requested_disclosure` 缺省或为 `null` 时按 L0 处理" in section
    assert "本操作只接受 L0、L1 或 L2" in section
    assert "L3 或 L4 对本操作明确不受支持" in section
