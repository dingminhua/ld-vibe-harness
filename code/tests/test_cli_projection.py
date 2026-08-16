from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import pytest

from ldvh import cli as cli_module
from ldvh.cli_projection import (
    MAX_REQUEST_BYTES,
    build_example_projection,
    parse_cli_arguments,
    parse_field_selectors,
    project_response_fields,
    read_request_file,
)
from ldvh.helper.responses import ServiceResult


def test_parse_request_option_in_any_position() -> None:
    before, before_problems, before_usage = parse_cli_arguments(
        ["call", "--request", "request.json", "read-fact-objects"]
    )
    after, after_problems, after_usage = parse_cli_arguments(
        ["call", "read-fact-objects", "--request", "request.json"]
    )

    assert before == after
    assert before is not None
    assert before.request_kind == "call"
    assert before.operation_key == "read-fact-objects"
    assert before.request_path == "request.json"
    assert before_problems == after_problems == ()
    assert before_usage is after_usage is False


@pytest.mark.parametrize(
    ("arguments", "expected_problem"),
    [
        (["capabilities", "--request"], "必须紧随"),
        (["capabilities", "--request", "one", "--request", "two"], "不得重复"),
        (["capabilities", "--unknown"], "未知 CLI 选项"),
        (["capabilities", "one", "two"], "至多接受"),
        (["call", "one", "two"], "只接受"),
    ],
)
def test_parse_request_option_rejects_closed_grammar(
    arguments: list[str], expected_problem: str
) -> None:
    parsed, problems, show_usage = parse_cli_arguments(arguments)

    assert parsed is not None
    assert show_usage is False
    assert any(expected_problem in problem for problem in problems)


def test_request_file_is_bounded_strict_utf8_and_unmodified(tmp_path: Path) -> None:
    request = tmp_path / "request.json"
    request.write_bytes(b'{"task":"same raw text"}\n')

    raw, problems = read_request_file(str(request))

    assert problems == ()
    assert raw == '{"task":"same raw text"}\n'


@pytest.mark.parametrize("case", ["dash", "missing", "directory", "non_utf8", "oversize"])
def test_request_file_rejects_unsafe_source(tmp_path: Path, case: str) -> None:
    request = tmp_path / "request.json"
    path_text = str(request)
    if case == "dash":
        path_text = "-"
    elif case == "directory":
        request.mkdir()
    elif case == "non_utf8":
        request.write_bytes(b"\xff")
    elif case == "oversize":
        request.write_bytes(b"x" * (MAX_REQUEST_BYTES + 1))

    raw, problems = read_request_file(path_text)

    assert raw is None
    assert problems


def test_request_file_rejects_fifo_without_blocking(tmp_path: Path) -> None:
    if not hasattr(os, "mkfifo"):
        pytest.skip("FIFO fixture is unavailable")
    request = tmp_path / "request.pipe"
    os.mkfifo(request)

    raw, problems = read_request_file(str(request))

    assert raw is None
    assert problems == ("--request 只接受普通文件",)


def test_request_file_rejects_symlink_to_regular_file(tmp_path: Path) -> None:
    target = tmp_path / "target.json"
    target.write_text("{}", encoding="utf-8")
    link = tmp_path / "request.json"
    try:
        link.symlink_to(target)
    except OSError:
        pytest.skip("symlink fixture is unavailable")

    raw, problems = read_request_file(str(link))

    assert raw is None
    assert problems == ("--request 只接受非符号链接的普通文件",)


def test_parse_example_requires_exact_capabilities_operation() -> None:
    parsed, problems, show_usage = parse_cli_arguments(
        ["capabilities", "create-fact-object", "--example"]
    )
    assert parsed is not None and parsed.example is True
    assert problems == ()
    assert show_usage is False

    _, no_operation, _ = parse_cli_arguments(["capabilities", "--example"])
    _, wrong_entry, _ = parse_cli_arguments(["call", "create-fact-object", "--example"])
    _, conflicts, _ = parse_cli_arguments(
        ["capabilities", "create-fact-object", "--example", "--request", "request.json"]
    )
    assert no_operation
    assert wrong_entry
    assert conflicts


def _valid_operation_metadata() -> dict[str, object]:
    return {
        "operation_key": "sample-operation",
        "effect": "read",
        "required_inputs": ["arguments.value"],
        "sources": [{"kind": "rule", "locator": "sample::input"}],
        "input_examples": [],
    }


@pytest.mark.parametrize("case", ["effect", "duplicate_required", "sources", "example_sources", "path_conflict"])
def test_example_rejects_incomplete_or_conflicting_capability_metadata(case: str) -> None:
    operation = _valid_operation_metadata()
    if case == "effect":
        operation["effect"] = "unknown"
    elif case == "duplicate_required":
        operation["required_inputs"] = ["arguments.value", "arguments.value"]
    elif case == "sources":
        operation["sources"] = []
    elif case == "example_sources":
        operation["input_examples"] = [
            {
                "summary": "sample",
                "arguments_fragment": {"value": "sample"},
                "source_refs": [],
                "composition_note": "sample note",
            }
        ]
    else:
        operation["required_inputs"] = ["arguments.value.member"]
        operation["input_examples"] = [
            {
                "summary": "sample",
                "arguments_fragment": {"value": "scalar"},
                "source_refs": [{"kind": "rule", "locator": "sample::input"}],
                "composition_note": "sample note",
            }
        ]

    with pytest.raises(ValueError):
        build_example_projection(operation)


def test_parse_fields_supports_closed_object_paths_and_request_combination() -> None:
    parsed, problems, show_usage = parse_cli_arguments(
        [
            "call",
            "read-fact-objects",
            "--request",
            "request.json",
            "--fields",
            "outcome,result.items",
        ]
    )

    assert parsed is not None
    assert parsed.field_selectors == ("outcome", "result.items")
    assert parsed.request_path == "request.json"
    assert problems == ()
    assert show_usage is False


@pytest.mark.parametrize(
    "value",
    ["", "result..items", ".result", "result.", "result.*", "result.items[0]", "a,a", "result,result.items"],
)
def test_parse_fields_rejects_invalid_duplicate_and_overlapping_paths(value: str) -> None:
    _, problems = parse_field_selectors(value)

    assert problems


def test_project_fields_preserves_nested_shape_null_and_exit_code() -> None:
    response = {
        "contract": "ldvh-helper-cli/2",
        "request_kind": "call",
        "operation_key": "sample",
        "outcome": "unavailable",
        "result": {"value": None, "items": [{"id": 1}]},
        "scope": {"requested": ["sample"], "completed": [], "not_completed": ["sample"]},
        "gaps": [{"summary": "missing"}],
        "sources": [{"large": "omitted"}],
    }

    projection = project_response_fields(response, ("result.value", "result.items"), 5)

    assert projection["projection"] == {
        "requested": ["result.value", "result.items"],
        "missing": [],
        "source_outcome": "unavailable",
        "source_exit_code": 5,
        "source_gap_count": 1,
        "source_response_complete": True,
    }
    assert projection["response"]["result"] == {"value": None, "items": [{"id": 1}]}
    assert projection["response"]["scope"] == {"not_completed": ["sample"]}
    assert "gaps" not in projection["response"]
    assert "sources" not in projection["response"]


def test_project_fields_distinguishes_missing_from_null_and_array_traversal() -> None:
    response = {
        "contract": "ldvh-helper-cli/2",
        "request_kind": "capabilities",
        "operation_key": None,
        "outcome": "ok",
        "result": {"null_value": None, "items": [{"id": 1}, {"id": 2}]},
        "scope": {"not_completed": []},
        "gaps": [],
    }

    projection = project_response_fields(
        response,
        ("result.null_value", "result.absent", "result.items.id"),
        0,
    )

    assert projection["response"]["result"] == {"null_value": None, "items": [{"id": 1}, {"id": 2}]}
    assert projection["projection"]["missing"] == ["result.absent"]


def test_project_fields_selects_into_array_members() -> None:
    response = {
        "contract": "ldvh-helper-cli/2",
        "request_kind": "call",
        "operation_key": "read-fact-objects",
        "outcome": "ok",
        "result": {
            "items": [
                {"fact_object": {"title": "alpha", "status": "open"}},
                {"fact_object": {"title": "beta", "status": "open"}},
            ]
        },
        "scope": {"not_completed": []},
        "gaps": [],
    }

    projection = project_response_fields(response, ("result.items.fact_object.title",), 0)

    assert projection["projection"]["missing"] == []
    assert projection["response"]["result"] == {
        "items": [
            {"fact_object": {"title": "alpha"}},
            {"fact_object": {"title": "beta"}},
        ]
    }


def test_project_fields_empty_array_present_subpath_reports_present() -> None:
    response = {
        "contract": "ldvh-helper-cli/2",
        "request_kind": "call",
        "operation_key": "sample",
        "outcome": "ok",
        "result": {"items": []},
        "scope": {"not_completed": []},
        "gaps": [],
    }

    projection = project_response_fields(response, ("result.items.fact_object.title",), 0)

    assert projection["projection"]["missing"] == []
    assert projection["response"]["result"] == {"items": []}


def test_project_fields_array_path_missing_everywhere_reports_missing() -> None:
    response = {
        "contract": "ldvh-helper-cli/2",
        "request_kind": "call",
        "operation_key": "sample",
        "outcome": "ok",
        "result": {"items": [{"id": 1}, {"id": 2}]},
        "scope": {"not_completed": []},
        "gaps": [],
    }

    projection = project_response_fields(response, ("result.items.fact_object",), 0)

    assert projection["projection"]["missing"] == ["result.items.fact_object"]
    assert "result" not in projection["response"] or "items" not in projection["response"]["result"]


@pytest.mark.parametrize("case", ["contract", "scope", "gaps"])
def test_project_fields_rejects_incomplete_common_response_core(case: str) -> None:
    response: dict[str, object] = {
        "contract": "ldvh-helper-cli/2",
        "request_kind": "call",
        "operation_key": "sample",
        "outcome": "ok",
        "scope": {"not_completed": []},
        "gaps": [],
    }
    if case == "contract":
        response.pop("contract")
    elif case == "scope":
        response["scope"] = {}
    else:
        response["gaps"] = None

    with pytest.raises(ValueError):
        project_response_fields(response, ("outcome",), 0)


def test_example_cli_consumes_general_discovery_not_request_check(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, str | None, str]] = []
    emitted: list[dict[str, Any]] = []
    operation = {
        **_valid_operation_metadata(),
        "implementation": {"present": True, "evidence": []},
    }
    discovery_response = {
        "outcome": "ok",
        "result": {"mode": "discovery", "operations": [operation]},
    }

    def fake_handle(request_kind: str, operation_key: str | None, raw: str) -> ServiceResult:
        calls.append((request_kind, operation_key, raw))
        return ServiceResult(discovery_response, 0)

    monkeypatch.setattr(cli_module, "handle_request", fake_handle)
    monkeypatch.setattr(cli_module, "_alternate_input_conflicts", lambda: False)
    monkeypatch.setattr(cli_module, "_emit", emitted.append)
    monkeypatch.setattr(sys, "argv", ["ldvh", "capabilities", "sample-operation", "--example"])

    assert cli_module.main() == 0
    assert calls == [("capabilities", None, "")]
    assert emitted[0]["operation_key"] == "sample-operation"


@pytest.mark.parametrize("case", ["not_found", "implementation", "metadata", "path_conflict"])
def test_example_cli_failure_never_calls_single_operation_request_check(
    monkeypatch: pytest.MonkeyPatch, case: str
) -> None:
    calls: list[tuple[str, str | None, str]] = []
    emitted: list[dict[str, Any]] = []
    operation = {
        **_valid_operation_metadata(),
        "implementation": {"present": case != "implementation", "evidence": []},
    }
    if case == "metadata":
        operation["effect"] = "unknown"
    elif case == "path_conflict":
        operation["required_inputs"] = ["arguments.value.member"]
        operation["input_examples"] = [
            {
                "summary": "sample",
                "arguments_fragment": {"value": "scalar"},
                "source_refs": [{"kind": "rule", "locator": "sample::input"}],
                "composition_note": "sample note",
            }
        ]
    operations = [] if case == "not_found" else [operation]
    discovery_response = {
        "outcome": "ok",
        "result": {"mode": "discovery", "operations": operations},
    }

    def fake_handle(request_kind: str, operation_key: str | None, raw: str) -> ServiceResult:
        calls.append((request_kind, operation_key, raw))
        return ServiceResult(discovery_response, 0)

    monkeypatch.setattr(cli_module, "handle_request", fake_handle)
    monkeypatch.setattr(cli_module, "_alternate_input_conflicts", lambda: False)
    monkeypatch.setattr(cli_module, "_emit", emitted.append)
    monkeypatch.setattr(sys, "argv", ["ldvh", "capabilities", "sample-operation", "--example"])

    assert cli_module.main() == 2
    assert calls == [("capabilities", None, "")]
    assert emitted[0]["outcome"] == "invalid_request"
    assert emitted[0]["operation_key"] == "sample-operation"


def test_fields_cli_falls_back_when_common_response_core_is_invalid(monkeypatch: pytest.MonkeyPatch) -> None:
    malformed_response = {
        "request_kind": "capabilities",
        "operation_key": None,
        "outcome": "ok",
        "scope": {"not_completed": []},
        "gaps": [],
    }
    emitted: list[dict[str, Any]] = []
    monkeypatch.setattr(
        cli_module,
        "handle_request",
        lambda *_: ServiceResult(malformed_response, 0),
    )
    monkeypatch.setattr(cli_module, "_read_request_input", lambda: "")
    monkeypatch.setattr(cli_module, "_emit", emitted.append)
    monkeypatch.setattr(sys, "argv", ["ldvh", "capabilities", "--fields", "outcome"])

    assert cli_module.main() == 0
    assert emitted == [malformed_response]
