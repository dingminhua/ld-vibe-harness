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
                "signature": {"model_id": "old-model", "agent_workbench": "Old Host"},
            }
        ],
    }


def test_parse_empty_observed_context() -> None:
    result = parse_observed_write_signature({})
    assert result.signature == {}
    assert result.session_id is None
    assert result.problems == ()


def test_parse_complete_signature_normalizes_only_model_id() -> None:
    result = parse_observed_write_signature(
        {
            "signature": {
                "model_id": " gpt-5.6-luna ",
                "agent_workbench": " Cindy ",
                "session_id": " Session-001 ",
            }
        }
    )
    assert result.problems == ()
    assert result.signature == {
        "model_id": "gpt-5.6-luna",
        "agent_workbench": "Cindy",
    }
    assert result.session_id == "Session-001"


def test_parse_partial_signature_preserves_supplied_subset() -> None:
    result = parse_observed_write_signature({"signature": {"model_id": "gpt-5.6-luna"}})
    assert result.problems == ()
    assert result.signature == {"model_id": "gpt-5.6-luna"}
    assert result.session_id is None


def test_parse_signature_empty_value_rejected() -> None:
    result = parse_observed_write_signature(
        {"signature": {"model_id": "  ", "agent_workbench": "Cindy"}}
    )
    assert result.problems
    assert "observed_context.signature.model_id" in result.problems[0]
    assert "model_id" not in result.signature
    assert result.signature["agent_workbench"] == "Cindy"


def test_parse_signature_unknown_field_rejected() -> None:
    result = parse_observed_write_signature(
        {"signature": {"model_id": "gpt-5.6-luna", "unknown_field": "value"}}
    )
    assert result.problems
    assert "未知字段" in result.problems[0]
    assert "unknown_field" in result.problems[0]


def test_parse_observed_context_unknown_field_rejected() -> None:
    result = parse_observed_write_signature(
        {"signature": {"model_id": "gpt-5.6-luna"}, "other_field": "value"}
    )
    assert result.problems
    assert "只允许" in result.problems[0]
    assert "other_field" in result.problems[0]


def test_inject_complete_signature_and_top_level_session_id() -> None:
    result = inject_observed_write_signature(
        _supplied(),
        {
            "signature": {
                "model_id": "gpt-5.6-luna",
                "agent_workbench": "Cindy",
                "session_id": "Session-ABC",
            }
        },
    )
    newest = result["change_log"][-1]
    assert newest["signature"] == {
        "model_id": "gpt-5.6-luna",
        "agent_workbench": "Cindy",
    }
    assert newest["session_id"] == "Session-ABC"
    assert "session_id" not in newest["signature"]


def test_inject_partial_signature_merges_to_complete_signature() -> None:
    result = inject_observed_write_signature(
        _supplied(),
        {"signature": {"model_id": "gpt-5.6-luna"}},
    )
    assert result["change_log"][-1]["signature"] == {
        "model_id": "gpt-5.6-luna",
        "agent_workbench": "Old",
    }


def test_injection_validation_rejects_incomplete_final_signature() -> None:
    supplied = _supplied()
    supplied["change_log"][-1]["signature"] = {"model_id": "old-model"}
    problems = observed_signature_injection_problems(
        {"signature": {"session_id": "Session-ABC"}},
        supplied,
    )
    assert problems
    assert "合并后必须恰含" in problems[0]


def test_injection_validation_rejects_appended_legacy_signature_without_observed_context() -> None:
    supplied = _supplied()
    supplied["change_log"][-1]["signature"] = {
        "agent_id": "legacy-model",
        "host_environment": "legacy-host",
    }
    problems = observed_signature_injection_problems({}, supplied)
    assert problems
    assert "旧形状" in problems[0]


def test_injection_validation_rejects_appended_host_name_legacy_signature() -> None:
    supplied = _supplied()
    supplied["change_log"][-1]["signature"] = {
        "model_id": "legacy-model",
        "host_name": "legacy-host",
    }
    problems = observed_signature_injection_problems({}, supplied)
    assert problems
    assert "旧形状" in problems[0]


def test_inject_onto_host_name_legacy_restarts_signature() -> None:
    supplied = _supplied()
    supplied["change_log"][-1]["signature"] = {
        "model_id": "legacy-model",
        "host_name": "legacy-host",
    }
    result = inject_observed_write_signature(
        supplied,
        {"signature": {"model_id": "gpt-5.6-luna", "agent_workbench": "Cindy", "session_id": "Session-X"}},
    )
    newest = result["change_log"][-1]
    assert newest["signature"] == {"model_id": "gpt-5.6-luna", "agent_workbench": "Cindy"}
    assert newest["session_id"] == "Session-X"
    assert "host_name" not in newest["signature"]


def test_inject_missing_observed_signature_normalizes_existing_agent_workbench() -> None:
    """空 observed_context 时仍应归一化 change_log 中已有的 agent_workbench。

    _supplied() 的 agent_workbench 是 "Old Host"——多 token 复合形，
    应被归一化为 "Old"，而不是原样保留。
    """
    supplied = _supplied()
    result = inject_observed_write_signature(supplied, {})
    assert result != supplied  # 归一化改变了内容
    assert result["change_log"][-1]["signature"]["agent_workbench"] == "Old"


def test_inject_without_change_log_preserves_supplied() -> None:
    supplied = {"title": "test"}
    assert inject_observed_write_signature(
        supplied,
        {"signature": {"model_id": "gpt-5.6-luna"}},
    ) == supplied


def test_parse_observed_context_signature_not_object() -> None:
    result = parse_observed_write_signature({"signature": "not-an-object"})
    assert result.problems
    assert "必须是 object" in result.problems[0]


def test_new_signature_tripwires_reject_product_alias_and_system_suffix() -> None:
    alias = parse_observed_write_signature(
        {"signature": {"model_id": "GPT", "agent_workbench": "Cindy", "session_id": "s"}}
    )
    suffix = parse_observed_write_signature(
        {"signature": {"model_id": "gpt-5.6-luna", "agent_workbench": "Cindy (macOS)", "session_id": "s"}}
    )
    spliced = parse_observed_write_signature(
        {"signature": {"model_id": "workbuddy-hy3", "agent_workbench": "Cindy", "session_id": "s"}}
    )
    assert any("裸产品别名" in problem for problem in alias.problems)
    assert any("括号系统后缀" in problem for problem in suffix.problems)
    assert any("拼接宿主产品名" in problem for problem in spliced.problems)


def test_observed_agent_workbench_compound_normalizes_to_single_token() -> None:
    compound = parse_observed_write_signature(
        {"signature": {"model_id": "gpt-5", "agent_workbench": "workbuddy-claw", "session_id": "s"}}
    )
    assert compound.problems == ()
    assert compound.signature["agent_workbench"] == "Workbuddy"
    assert compound.signature["model_id"] == "gpt-5"

    for raw, expected in (
        ("claude-code", "Claude"),
        ("claude-code-mcp", "Claude"),
        ("Claude Code", "Claude"),
        ("Cindy/Codex", "Cindy"),
        ("trae-desktop", "Trae"),
        ("traecode-macos", "Traecode"),
    ):
        result = parse_observed_write_signature(
            {"signature": {"model_id": "gpt-5", "agent_workbench": raw, "session_id": "s"}}
        )
        assert result.signature["agent_workbench"] == expected, raw


def test_observed_agent_workbench_capitalizes_first_and_lowercases_rest() -> None:
    for raw, expected in (
        ("workbuddy", "Workbuddy"),
        ("WORKBUDDY", "Workbuddy"),
        ("TraeCode", "Traecode"),
        ("TRAE", "Trae"),
        ("Cindy", "Cindy"),
        ("WorkBuddy", "Workbuddy"),
        ("Kimi", "Kimi"),
        ("codex", "Codex"),
    ):
        result = parse_observed_write_signature(
            {"signature": {"model_id": "gpt-5", "agent_workbench": raw, "session_id": "s"}}
        )
        assert result.signature["agent_workbench"] == expected, raw


def test_inject_normalizes_existing_compound_workbench_in_merge() -> None:
    supplied = {
        "title": "test",
        "change_log": [
            {
                "at": "2000-01-01T00:00:00Z",
                "session_id": "old",
                "summary": "create",
                "signature": {"model_id": "old-model", "agent_workbench": "workbuddy-claw"},
            }
        ],
    }
    result = inject_observed_write_signature(
        supplied,
        {"signature": {"model_id": "gpt-5.6-luna", "session_id": "Session-X"}},
    )
    newest = result["change_log"][-1]
    assert newest["signature"]["agent_workbench"] == "Workbuddy"
    assert newest["signature"]["model_id"] == "gpt-5.6-luna"
