"""Contract tests for the product-neutral observed LDVH signature."""

from __future__ import annotations

from ldvh.helper.operations.fact_creation_operation import inject_observed_write_signature
from ldvh.helper.operations.fact_creation_request import (
    observed_signature_injection_problems,
    observed_write_signature_required_problem,
    parse_observed_write_signature,
)


def _signature(**overrides: str | None) -> dict[str, str | None]:
    return {
        "product_name": "Cindy",
        "model_name": "GLM-5.2",
        "agent_runtime_name": "Codex CLI",
        **overrides,
    }


def _supplied() -> dict[str, object]:
    return {
        "title": "test",
        "change_log": [
            {
                "at": "2000-01-01T00:00:00Z",
                "session_id": "historical-session",
                "summary": "create",
                "signature": {"model_id": "old-model", "agent_workbench": "Old Host"},
            }
        ],
    }


def test_parse_normalizes_the_complete_snapshot_without_inference() -> None:
    result = parse_observed_write_signature({"signature": _signature()})
    assert result.problems == ()
    assert result.signature is not None
    assert result.signature.as_dict() == {
        "product_name": "Cindy",
        "model_name": "glm-5.2",
        "agent_runtime_name": "codex-cli",
    }


def test_partial_values_are_allowed_but_the_three_keys_are_not_optional() -> None:
    allowed = parse_observed_write_signature(
        {"signature": _signature(model_name=None, agent_runtime_name=None)}
    )
    assert allowed.problems == ()
    assert allowed.signature is not None
    assert allowed.signature.as_dict()["model_name"] is None

    missing = parse_observed_write_signature({"signature": {"product_name": "Cindy"}})
    assert any("缺少字段" in problem for problem in missing.problems)


def test_an_empty_snapshot_blocks_new_controlled_writes() -> None:
    observed = {"signature": _signature(product_name=None, model_name=None, agent_runtime_name=None)}
    assert observed_write_signature_required_problem(observed) is not None
    assert observed_signature_injection_problems(observed, _supplied())


def test_injection_replaces_draft_and_historical_shapes_and_removes_session_id() -> None:
    result = inject_observed_write_signature(_supplied(), {"signature": _signature()})
    newest = result["change_log"][-1]
    assert newest["signature"] == {
        "product_name": "Cindy",
        "model_name": "glm-5.2",
        "agent_runtime_name": "codex-cli",
    }
    assert "session_id" not in newest


def test_unknown_or_empty_values_are_rejected() -> None:
    unknown = parse_observed_write_signature({"signature": {**_signature(), "unknown": "x"}})
    empty = parse_observed_write_signature({"signature": _signature(model_name="  ")})
    assert any("未知字段" in problem for problem in unknown.problems)
    assert any("必须是非空" in problem for problem in empty.problems)
