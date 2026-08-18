from __future__ import annotations

import pytest

from ldvh.helper.requests import parse_common_request, valid_operation_key
from ldvh.source_references import source_reference_problems


def test_empty_input_uses_all_common_defaults() -> None:
    result = parse_common_request("", general_discovery=True)

    assert result.problems == ()
    assert result.request is not None
    assert result.request.task is None
    assert result.request.work_object_locators == ()
    assert result.request.arguments == {}
    assert result.request.requested_disclosure is None
    assert result.request.response_profile == "compact"
    assert result.request.observed_context == {}
    assert result.request.authorization_reference == ()


@pytest.mark.parametrize(
    ("raw", "problem"),
    [
        ("not-json", "有效 JSON 对象"),
        ("[]", "顶层必须是对象"),
        ('{"unknown": true}', "未知共同字段"),
        ('{"task": ""}', "task"),
        ('{"task": null}', "task"),
        ('{"work_object_locators": [1]}', "work_object_locators[0]"),
        ('{"arguments": []}', "arguments"),
        ('{"arguments": {"unexpected": true}}', "通用 capabilities"),
        ('{"requested_disclosure": "L5"}', "requested_disclosure"),
        ('{"response_profile": "verbose"}', "response_profile"),
        ('{"response_profile": []}', "response_profile"),
        ('{"observed_context": []}', "observed_context"),
        ('{"authorization_reference": {}}', "authorization_reference"),
        ('{"authorization_reference": [{}]}', "kind"),
        (
            '{"authorization_reference": [{"kind": "   ", "locator": "\\t"}]}',
            "非空白字符",
        ),
        (
            '{"authorization_reference": [{"kind": "human", "locator": "turn", "observed_at": "2026-07-12"}]}',
            "RFC 3339",
        ),
    ],
)
def test_rejects_invalid_common_request(raw: str, problem: str) -> None:
    result = parse_common_request(raw, general_discovery=True)

    assert result.request is None
    assert any(problem in item for item in result.problems)


def test_accepts_diagnostic_response_profile() -> None:
    result = parse_common_request('{"response_profile": "diagnostic"}', general_discovery=True)

    assert result.problems == ()
    assert result.request is not None
    assert result.request.response_profile == "diagnostic"


def test_accepts_lean_response_profile() -> None:
    result = parse_common_request('{"response_profile": "lean"}', general_discovery=True)

    assert result.problems == ()
    assert result.request is not None
    assert result.request.response_profile == "lean"


def test_source_reference_rejects_every_whitespace_only_string_member() -> None:
    problems = source_reference_problems(
        {"kind": "   ", "locator": "\t", "version": "\n", "observed_at": "\r\n"},
        "source",
    )

    assert {problem.split(" ", 1)[0] for problem in problems} == {
        "source.kind",
        "source.locator",
        "source.version",
        "source.observed_at",
    }
    assert all("非空白字符" in problem for problem in problems)


@pytest.mark.parametrize(
    "observed_at",
    [
        "2026-W30-1T10:20:30+08:00",
        "20260727T102030+08:00",
        "2026-07-27T10:20:30+0800",
        "2026-07-27T10:20:30+08:00:30",
        "2026-07-27T10:20:30+08:60",
        "2026-07-27T10:20:60+08:00",
        "2026-07-27T10:20:30-00:00",
        "2026-02-30T10:20:30+08:00",
    ],
)
def test_source_reference_rejects_noncanonical_or_invalid_observed_at(observed_at: str) -> None:
    problems = source_reference_problems(
        {"kind": "human", "locator": "turn:12", "observed_at": observed_at},
        "source",
    )

    assert problems == ["source.observed_at 必须是包含 UTC 偏移的 RFC 3339 时间"]


@pytest.mark.parametrize(
    "observed_at",
    [
        "2026-07-27T10:20:30Z",
        "2026-07-27T10:20:30+08:00",
        "2026-07-27T10:20:30.125-03:30",
        "2026-07-27T10:20:30.12345678901234567890+08:00",
    ],
)
def test_source_reference_accepts_regular_rfc3339_observed_at(observed_at: str) -> None:
    assert (
        source_reference_problems(
            {"kind": "human", "locator": "turn:12", "observed_at": observed_at},
            "source",
        )
        == []
    )


def test_source_reference_validation_preserves_nonblank_original_strings() -> None:
    result = parse_common_request(
        '{"authorization_reference": [{"kind": " human ", "locator": " turn:12 ", "version": " v1 "}]}',
        general_discovery=False,
    )

    assert result.problems == ()
    assert result.request is not None
    assert result.request.authorization_reference == ({"kind": " human ", "locator": " turn:12 ", "version": " v1 "},)


@pytest.mark.parametrize("value", ["read-source", "a", "a1-b2"])
def test_accepts_operation_key_format(value: str) -> None:
    assert valid_operation_key(value)


@pytest.mark.parametrize("value", ["", "Read-source", "read_source", "1-read", "read--source"])
def test_rejects_operation_key_format(value: str) -> None:
    assert not valid_operation_key(value)
