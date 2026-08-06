"""Contract tests for observed_context.signature parsing and injection."""

from __future__ import annotations

from ldvh.helper.operations.fact_operation_support import inject_observed_signature
from ldvh.helper.requests import parse_observed_signature


def test_parse_empty_observed_context() -> None:
    """observed_context 为空 → 返回空签名、无问题."""
    result = parse_observed_signature({})
    assert result.signature == {}
    assert result.problems == ()


def test_parse_complete_signature() -> None:
    """提供完整 signature → 三个字段均正确解析，字段值强制小写."""
    result = parse_observed_signature({
        "signature": {
            "agent_id": "GLM-5.2",
            "host_environment": "Claude Code (macOS)",
            "session_id": "Session-001",
        },
    })
    assert result.problems == ()
    assert result.signature == {
        "agent_id": "glm-5.2",
        "host_environment": "claude code (macos)",
        "session_id": "session-001",
    }


def test_parse_partial_signature() -> None:
    """只提供部分字段 → 只解析出现且非空的字段，值强制小写."""
    result = parse_observed_signature({
        "signature": {"agent_id": "GLM-5.2"},
    })
    assert result.problems == ()
    assert result.signature == {"agent_id": "glm-5.2"}


def test_parse_signature_empty_value_rejected() -> None:
    """signature 字段出现但值为空 string → 拒绝."""
    result = parse_observed_signature({
        "signature": {"agent_id": "  ", "host_environment": "Claude Code"},
    })
    assert result.problems
    assert "observed_context.signature.agent_id" in result.problems[0]
    assert "agent_id" not in result.signature
    assert result.signature["host_environment"] == "claude code"


def test_parse_signature_unknown_field_rejected() -> None:
    """signature 含未知字段 → 拒绝."""
    result = parse_observed_signature({
        "signature": {"agent_id": "glm-5.2", "unknown_field": "value"},
    })
    assert result.problems
    assert "未知字段" in result.problems[0]
    assert "unknown_field" in result.problems[0]


def test_parse_observed_context_unknown_field_rejected() -> None:
    """observed_context 包含 signature 以外的未知字段 → 拒绝."""
    result = parse_observed_signature({
        "signature": {"agent_id": "glm-5.2"},
        "other_field": "value",
    })
    assert result.problems
    assert "只允许" in result.problems[0]
    assert "other_field" in result.problems[0]


def test_inject_signature_on_newest_change_log() -> None:
    """提供 signature → 注入到最新 change_log 条目的 signature."""
    supplied = {
        "title": "test",
        "change_log": [
            {
                "at": "2000-01-01T00:00:00Z",
                "session_id": "s1",
                "summary": "create",
                "signature": {"agent_id": "old-agent", "host_environment": "old"},
            },
        ],
    }
    result = inject_observed_signature(supplied, {
        "signature": {"agent_id": "GLM-5.2", "host_environment": "Claude Code"},
    })
    assert result["change_log"][-1]["signature"] == {
        "agent_id": "glm-5.2",
        "host_environment": "claude code",
    }
    # 仅有一条 change_log 条目时注入覆写整条 signature
    # 多条目场景测试在 test_inject_signature_with_multiple_entries


def test_inject_signature_no_change_log() -> None:
    """change_log 不存在或为空 → 保留 supplied 不变."""
    for supplied in [{"title": "test"}, {"title": "test", "change_log": []}]:
        result = inject_observed_signature(supplied, {"signature": {"agent_id": "a"}})
        assert result == supplied


def test_inject_signature_no_observed_signature() -> None:
    """observed_context 不含 signature → 保留既有行为."""
    supplied = {
        "title": "test",
        "change_log": [
            {
                "at": "2000-01-01T00:00:00Z",
                "session_id": "s1",
                "summary": "create",
                "signature": {"agent_id": "old-agent", "host_environment": "old"},
            },
        ],
    }
    result = inject_observed_signature(supplied, {})
    assert result["change_log"][-1]["signature"] == {"agent_id": "old-agent", "host_environment": "old"}


def test_inject_signature_partial_override() -> None:
    """只提供部分签名字段 → 只覆写出现的字段,其他字段未提供."""
    supplied = {
        "title": "test",
        "change_log": [
            {
                "at": "2000-01-01T00:00:00Z",
                "session_id": "s1",
                "summary": "create",
                "signature": {"agent_id": "old-agent", "host_environment": "old"},
            },
        ],
    }
    result = inject_observed_signature(supplied, {"signature": {"agent_id": "GLM-5.2"}})
    assert result["change_log"][-1]["signature"] == {"agent_id": "glm-5.2"}


def test_inject_signature_with_session_id() -> None:
    """session_id 也一并注入."""
    supplied = {
        "title": "test",
        "change_log": [
            {
                "at": "2000-01-01T00:00:00Z",
                "session_id": "old-session",
                "summary": "create",
                "signature": {"agent_id": "old-agent", "host_environment": "old"},
            },
        ],
    }
    result = inject_observed_signature(supplied, {
        "signature": {
            "agent_id": "GLM-5.2",
            "host_environment": "Claude Code",
            "session_id": "Session-ABC",
        },
    })
    assert result["change_log"][-1]["signature"] == {
        "agent_id": "glm-5.2",
        "host_environment": "claude code",
        "session_id": "session-abc",
    }


def test_parse_observed_context_signature_not_object() -> None:
    """observed_context.signature 不是 object → 拒绝."""
    result = parse_observed_signature({"signature": "not-an-object"})
    assert result.problems
    assert "必须是 object" in result.problems[0]