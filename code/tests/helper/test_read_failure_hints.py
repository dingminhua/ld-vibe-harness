"""Focused tests for structured fix hints on read-only operation failures.

These tests assert that invalid_request responses for read-only operations
carry structured correction hints (missing required inputs, allowed inputs,
minimal examples) inside ``diagnostics[0].details.hints``, while write
operations and other failure paths keep their existing output unchanged.
"""

from __future__ import annotations

import json
from pathlib import Path

from conftest import assert_common_response

from ldvh.helper.operations import IMPLEMENTATIONS
from ldvh.helper.rule_source import RuleSourceResult
from ldvh.helper.service import handle_request
from ldvh.specs.repository import inspect_repository

_READ_ONLY_OPERATIONS = (
    "check-current-governed-sources",
    "check-fact-integrity",
    "check-workcase-handoff",
    "find-fact-object-candidates",
    "git-hooks-status",
    "precheck-git-commit",
    "prepare-closed-workcase-candidate",
    "prepare-fact-object-draft",
    "prepare-fact-object-update",
    "prepare-local-edit-candidates",
    "read-action-template-candidates",
    "read-action-template-content",
    "read-fact-objects",
    "read-specification-candidates",
    "read-specification-content",
    "read-specification-context",
    "resolve-governance-scope",
)


def _bind_real_operations(monkeypatch, repository: Path) -> None:
    inspected = inspect_repository(repository)
    from ldvh.helper.operation_sources import inspect_operation_sources

    operations = inspect_operation_sources(inspected)
    monkeypatch.setattr(
        "ldvh.helper.service.inspect_colocated_rule_source",
        lambda _path: RuleSourceResult(inspected, operations, None),
    )
    monkeypatch.setattr("ldvh.helper.service.OPERATION_IMPLEMENTATIONS", dict(IMPLEMENTATIONS))


def _hints(response: dict) -> list[dict] | None:
    details = response["diagnostics"][0]["details"]
    return details.get("hints")


def test_read_only_operations_are_the_declared_effect_read_set(
    monkeypatch,
    current_specs_repository: Path,
) -> None:
    _bind_real_operations(monkeypatch, current_specs_repository)
    discovered = handle_request("capabilities", None, "").response
    declared = {
        item["operation_key"]
        for item in discovered["result"]["operations"]
        if item.get("effect") == "read"
    }
    assert declared == set(_READ_ONLY_OPERATIONS)


def test_missing_required_inputs_produce_structured_hints(
    monkeypatch,
    current_specs_repository: Path,
) -> None:
    _bind_real_operations(monkeypatch, current_specs_repository)
    response = handle_request("call", "read-fact-objects", json.dumps({"arguments": {}})).response
    assert_common_response(response)
    assert response["outcome"] == "invalid_request"
    hints = _hints(response)
    assert hints is not None
    assert {"kind": "missing_required_inputs"} in [
        {"kind": hint["kind"]} for hint in hints
    ]
    missing = next(hint for hint in hints if hint["kind"] == "missing_required_inputs")
    assert "arguments.fact_refs" in missing["fields"]
    allowed = next(hint for hint in hints if hint["kind"] == "allowed_inputs")
    assert "arguments.fact_refs" in allowed["fields"]
    assert "work_object_locators" in allowed["fields"]


def test_required_inputs_are_reported_for_multiple_read_operations(
    monkeypatch,
    current_specs_repository: Path,
) -> None:
    _bind_real_operations(monkeypatch, current_specs_repository)
    cases = {
        "read-action-template-content": {"arguments": {}},
        "find-fact-object-candidates": {"arguments": {}},
        "git-hooks-status": {"arguments": {}},
        "check-workcase-handoff": {"arguments": {}},
    }
    for operation, arguments in cases.items():
        response = handle_request("call", operation, json.dumps(arguments)).response
        assert response["outcome"] == "invalid_request", operation
        hints = _hints(response)
        assert hints is not None, operation
        missing = next((hint for hint in hints if hint["kind"] == "missing_required_inputs"), None)
        assert missing is not None, operation
        assert missing["fields"], operation


def test_closed_set_violation_still_carries_hints(
    monkeypatch,
    current_specs_repository: Path,
) -> None:
    _bind_real_operations(monkeypatch, current_specs_repository)
    response = handle_request(
        "call",
        "read-specification-content",
        json.dumps(
            {
                "requested_disclosure": "L9",
                "arguments": {"selections": [{"responsibility_key": "ldvh-root", "heading_path": None}]},
            }
        ),
    ).response
    assert response["outcome"] == "invalid_request"
    hints = _hints(response)
    assert hints is not None
    missing = next(hint for hint in hints if hint["kind"] == "missing_required_inputs")
    assert "requested_disclosure" in missing["fields"]
    assert "arguments.selections" in missing["fields"]


def test_shape_error_still_carries_hints(
    monkeypatch,
    current_specs_repository: Path,
) -> None:
    _bind_real_operations(monkeypatch, current_specs_repository)
    response = handle_request(
        "call",
        "read-fact-objects",
        json.dumps({"arguments": {"fact_refs": "not-an-array"}}),
    ).response
    assert response["outcome"] == "invalid_request"
    hints = _hints(response)
    assert hints is not None
    missing = next(hint for hint in hints if hint["kind"] == "missing_required_inputs")
    assert "arguments.fact_refs" in missing["fields"]


def test_minimal_examples_are_attached_when_available(
    monkeypatch,
    current_specs_repository: Path,
) -> None:
    _bind_real_operations(monkeypatch, current_specs_repository)
    response = handle_request("call", "find-fact-object-candidates", json.dumps({"arguments": {}})).response
    assert response["outcome"] == "invalid_request"
    hints = _hints(response)
    assert hints is not None
    examples = next((hint for hint in hints if hint["kind"] == "minimal_examples"), None)
    assert examples is not None
    assert examples["examples"]
    assert all(isinstance(example, dict) for example in examples["examples"])


def test_write_operation_failure_keeps_existing_output(
    monkeypatch,
    current_specs_repository: Path,
) -> None:
    _bind_real_operations(monkeypatch, current_specs_repository)
    response = handle_request("call", "update-workcase", json.dumps({"arguments": {}})).response
    assert response["outcome"] == "invalid_request"
    assert _hints(response) is None


def test_unknown_operation_keeps_existing_output(
    monkeypatch,
    current_specs_repository: Path,
) -> None:
    _bind_real_operations(monkeypatch, current_specs_repository)
    response = handle_request("call", "not-a-real-operation", "").response
    assert response["outcome"] == "invalid_request"
    assert _hints(response) is None
