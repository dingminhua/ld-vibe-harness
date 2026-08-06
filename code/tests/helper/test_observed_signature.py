"""Contract tests for observed_context.signature parsing and injection."""

from __future__ import annotations

from ldvh.helper.operations.fact_creation_operation import inject_observed_write_signature
from ldvh.helper.operations.fact_creation_request import (
    observed_signature_injection_problems,
    parse_observed_write_signature,
)


def _supplied() -> dict[str, object]:
    return {
        "title": "test",
        "change_log": [
            {
                "at": "2000-01-01T00:00:00Z",
                "session_id": "old-session",
                "summary": "create",
                "signature": {"agent_id": "old-agent", "host_environment": "Old Host"},
            }
        ],
    }


def test_parse_empty_observed_context() -> None:
    result = parse_observed_write_signature({})
    assert result.signature == {}
    assert result.session_id is None
    assert result.problems == ()


def test_parse_complete_signature_normalizes_only_agent_id() -> None:
    result = parse_observed_write_signature(
        {
            "signature": {
                "agent_id": " GLM-5.2 ",
                "host_environment": " Claude Code (macOS) ",
                "session_id": " Session-001 ",
            }
        }
    )
    assert result.problems == ()
    assert result.signature == {
        "agent_id": "glm-5.2",
        "host_environment": "Claude Code (macOS)",
    }
    assert result.session_id == "Session-001"


def test_parse_partial_signature_preserves_supplied_subset() -> None:
    result = parse_observed_write_signature({"signature": {"agent_id": "GLM-5.2"}})
    assert result.problems == ()
    assert result.signature == {"agent_id": "glm-5.2"}
    assert result.session_id is None


def test_parse_signature_empty_value_rejected() -> None:
    result = parse_observed_write_signature(
        {"signature": {"agent_id": "  ", "host_environment": "Claude Code"}}
    )
    assert result.problems
    assert "observed_context.signature.agent_id" in result.problems[0]
    assert "agent_id" not in result.signature
    assert result.signature["host_environment"] == "Claude Code"


def test_parse_signature_unknown_field_rejected() -> None:
    result = parse_observed_write_signature(
        {"signature": {"agent_id": "glm-5.2", "unknown_field": "value"}}
    )
    assert result.problems
    assert "未知字段" in result.problems[0]
    assert "unknown_field" in result.problems[0]


def test_parse_observed_context_unknown_field_rejected() -> None:
    result = parse_observed_write_signature(
        {"signature": {"agent_id": "glm-5.2"}, "other_field": "value"}
    )
    assert result.problems
    assert "只允许" in result.problems[0]
    assert "other_field" in result.problems[0]


def test_inject_complete_signature_and_top_level_session_id() -> None:
    result = inject_observed_write_signature(
        _supplied(),
        {
            "signature": {
                "agent_id": "GLM-5.2",
                "host_environment": "Claude Code",
                "session_id": "Session-ABC",
            }
        },
    )
    newest = result["change_log"][-1]
    assert newest["signature"] == {
        "agent_id": "glm-5.2",
        "host_environment": "Claude Code",
    }
    assert newest["session_id"] == "Session-ABC"
    assert "session_id" not in newest["signature"]


def test_inject_partial_signature_merges_to_complete_signature() -> None:
    result = inject_observed_write_signature(
        _supplied(),
        {"signature": {"agent_id": "GLM-5.2"}},
    )
    assert result["change_log"][-1]["signature"] == {
        "agent_id": "glm-5.2",
        "host_environment": "Old Host",
    }


def test_injection_validation_rejects_incomplete_final_signature() -> None:
    supplied = _supplied()
    supplied["change_log"][-1]["signature"] = {"agent_id": "old-agent"}
    problems = observed_signature_injection_problems(
        {"signature": {"session_id": "Session-ABC"}},
        supplied,
    )
    assert problems
    assert "合并后必须恰含" in problems[0]


def test_inject_missing_observed_signature_preserves_supplied() -> None:
    supplied = _supplied()
    assert inject_observed_write_signature(supplied, {}) == supplied


def test_inject_without_change_log_preserves_supplied() -> None:
    supplied = {"title": "test"}
    assert inject_observed_write_signature(
        supplied,
        {"signature": {"agent_id": "gpt-5"}},
    ) == supplied


def test_parse_observed_context_signature_not_object() -> None:
    result = parse_observed_write_signature({"signature": "not-an-object"})
    assert result.problems
    assert "必须是 object" in result.problems[0]
