from __future__ import annotations

import pytest

from ldvh.helper.requests import parse_common_request, valid_operation_key


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


@pytest.mark.parametrize("value", ["read-source", "a", "a1-b2"])
def test_accepts_operation_key_format(value: str) -> None:
    assert valid_operation_key(value)


@pytest.mark.parametrize("value", ["", "Read-source", "read_source", "1-read", "read--source"])
def test_rejects_operation_key_format(value: str) -> None:
    assert not valid_operation_key(value)
