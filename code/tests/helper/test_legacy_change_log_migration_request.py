"""Request contract tests for the legacy change-log migration operation."""

from __future__ import annotations

from pathlib import Path

from ldvh.helper.operation_runtime import OperationExecutionContext
from ldvh.helper.operations.legacy_change_log_migration_request import (
    parse_legacy_change_log_migration_request,
)
from ldvh.helper.requests import CommonRequest


def _common(**overrides: object) -> tuple[str, ...]:
    request: dict[str, object] = {
        "work_object_locators": ("/project",),
        "authorization_reference": ({"kind": "human_instruction", "locator": "turn:authorize-migration"},),
        "arguments": {
            "workspace_root": "/workspace",
            "fact_ref": {
                "governed_project_id": "sample",
                "fact_type_key": "spark",
                "object_id": "spark-0001",
            },
            "expected_content_fingerprint": "a" * 64,
            "migration_signature": {
                "agent_id": "test-agent",
                "host_environment": "test",
                "session_id": "test-session",
            },
            "migration_summary": "建立历史不可得时的可信迁移起点。",
        },
        "requested_disclosure": None,
        "response_profile": "compact",
        "observed_context": {},
        "task": None,
    }
    arguments = dict(request["arguments"])  # type: ignore[arg-type]
    if "arguments" in overrides:
        override_arguments = overrides.pop("arguments")
        if override_arguments == {}:
            arguments = {}
        else:
            arguments.update(override_arguments)  # type: ignore[arg-type]
    request.update(overrides)
    request["arguments"] = arguments
    common = CommonRequest(
        task=request["task"],  # type: ignore[arg-type]
        work_object_locators=request["work_object_locators"],  # type: ignore[arg-type]
        arguments=request["arguments"],  # type: ignore[arg-type]
        requested_disclosure=request["requested_disclosure"],  # type: ignore[arg-type]
        response_profile=request["response_profile"],  # type: ignore[arg-type]
        observed_context=request["observed_context"],  # type: ignore[arg-type]
        authorization_reference=request["authorization_reference"],  # type: ignore[arg-type]
    )
    result = parse_legacy_change_log_migration_request(
        common,
        OperationExecutionContext(cwd=Path("/project")),
    )
    return result.problems


def test_valid_minimal_request_parses() -> None:
    assert _common() == ()


def test_all_required_fields_are_enforced() -> None:
    problems = _common(arguments={})
    assert "arguments.fact_ref 必须是 object" in problems
    assert any(problem.startswith("arguments.expected_content_fingerprint") for problem in problems)
    assert any(problem.startswith("arguments.migration_signature") for problem in problems)
    assert any(problem.startswith("arguments.migration_summary") for problem in problems)


def test_unknown_argument_is_rejected() -> None:
    problems = _common(arguments={"extra": True})
    assert problems == ("arguments 包含未知字段: extra",)


def test_unknown_signature_member_is_rejected() -> None:
    problems = _common(
        arguments={
            "migration_signature": {
                "agent_id": "test-agent",
                "host_environment": "test",
                "session_id": "test-session",
                "signer_type": "ai-agent",
            }
        }
    )
    assert problems == ("arguments.migration_signature 包含未知字段: signer_type",)


def test_empty_signature_members_are_rejected() -> None:
    problems = _common(
        arguments={
            "migration_signature": {
                "agent_id": " ",
                "host_environment": "test",
                "session_id": "test-session",
            }
        }
    )
    assert problems == ("arguments.migration_signature.agent_id 必须是非空 string",)


def test_invalid_fingerprint_is_rejected() -> None:
    problems = _common(arguments={"expected_content_fingerprint": "A" * 64})
    assert problems == ("arguments.expected_content_fingerprint 必须是 64 位小写十六进制 string",)


def test_workcase_is_rejected_by_generic_migration() -> None:
    problems = _common(
        arguments={
            "fact_ref": {
                "governed_project_id": "sample",
                "fact_type_key": "workcase",
                "object_id": "workcase-0001",
            }
        }
    )
    assert problems == ("arguments.fact_ref.fact_type_key 未匹配当前支持迁移的五类事实类型",)


def test_authorization_reference_is_required() -> None:
    problems = _common(authorization_reference=())
    assert problems == ("authorization_reference 必须至少包含一个 Human 授权来源",)


def test_disclosure_and_observed_context_are_rejected() -> None:
    assert _common(observed_context={"x": 1}) == ("observed_context 对 legacy change_log migration 必须为空 object",)
    assert _common(requested_disclosure="L3") == (
        "requested_disclosure 对 legacy change_log migration 必须为 null 或省略",
    )
