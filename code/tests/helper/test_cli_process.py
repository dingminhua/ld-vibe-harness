from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from conftest import assert_common_response

HELPER_EXECUTABLE = Path(sys.executable).with_name("ldvh")


def _run(cwd: Path, *arguments: str, stdin: str = "") -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
    completed = subprocess.run(
        [str(HELPER_EXECUTABLE), *arguments],
        cwd=cwd,
        input=stdin,
        text=True,
        capture_output=True,
        check=False,
    )
    response = json.loads(completed.stdout)
    assert_common_response(response)
    assert completed.stderr == ""
    return completed, response


def test_general_discovery_reports_source_bound_implementation(tmp_path: Path) -> None:
    completed, response = _run(tmp_path, "capabilities")

    assert completed.returncode == 0
    assert response["outcome"] == "ok"
    assert response["operation_key"] is None
    assert response["result"]["mode"] == "discovery"
    assert len(response["result"]["operations"]) == 4
    operations = {item["operation_key"]: item for item in response["result"]["operations"]}
    facts = operations["read-fact-objects"]
    assert facts["implementation"]["present"] is True
    assert facts["required_inputs"] == ["arguments.fact_refs"]
    operation = operations["read-specification-candidates"]
    assert operation["operation_key"] == "read-specification-candidates"
    assert operation["implementation"]["present"] is True
    assert operation["implementation"]["evidence"] == [
        {
            "kind": "implementation",
            "locator": "code/ldvh/helper/operations/specification_candidate_operation.py",
        }
    ]
    assert operation["availability"] is None
    assert operation["required_inputs"] == []
    assert operation["optional_inputs"] == [
        "arguments.responsibility_keys",
        "requested_disclosure",
    ]
    content = operations["read-specification-content"]
    assert content["implementation"] == {
        "present": True,
        "evidence": [
            {
                "kind": "implementation",
                "locator": "code/ldvh/helper/operations/specification_content_operation.py",
            }
        ],
    }
    assert content["required_inputs"] == ["arguments.selections", "requested_disclosure"]
    assert content["optional_inputs"] == []
    assert content["availability"] is None
    governance = operations["resolve-governance-scope"]
    assert governance["implementation"] == {
        "present": True,
        "evidence": [
            {
                "kind": "implementation",
                "locator": "code/ldvh/helper/operations/governance_scope_operation.py",
            }
        ],
    }
    assert governance["required_inputs"] == []
    assert governance["optional_inputs"] == ["work_object_locators", "arguments.workspace_root"]
    assert len(response["gaps"]) == 8
    assert all(item["summary"].startswith("当前 Code 尚未自动证明：") for item in response["gaps"])


def test_defined_operation_check_and_call_return_actual_l0_results(tmp_path: Path) -> None:
    checked, check_response = _run(tmp_path, "capabilities", "read-specification-candidates")
    called, call_response = _run(tmp_path, "call", "read-specification-candidates")

    assert checked.returncode == 0
    assert check_response["outcome"] == "ok"
    checked_operation = check_response["result"]["operations"][0]
    assert checked_operation["availability"] == "available_for_request"
    assert len(checked_operation["available_scope"]) == 18
    assert checked_operation["unavailable_scope"] == []

    assert called.returncode == 0
    assert call_response["outcome"] == "ok"
    assert len(call_response["result"]["items"]) == 18
    assert call_response["scope"]["requested"] == call_response["scope"]["completed"]
    assert call_response["scope"]["not_completed"] == []
    assert call_response["disclosure"]["requested"] is None
    assert [part["level"] for part in call_response["disclosure"]["parts"]] == ["L0"]
    assert all(item["overview"] is None and item["relationships"] is None for item in call_response["result"]["items"])
    observed_sources = [source for source in call_response["sources"] if source["kind"] == "working_tree"]
    assert len(observed_sources) == 1
    assert observed_sources[0]["observed_at"]
    assert observed_sources[0]["details"] == {"view": "Working Tree"}
    assert all(
        any(evidence.get("observed_at") == observed_sources[0]["observed_at"] for evidence in item["evidence"])
        for item in call_response["verification"]
    )
    assert all(
        any(evidence["kind"] == "implementation" for evidence in item["evidence"])
        for item in call_response["verification"]
    )


@pytest.mark.parametrize("requested", ["L3", "L4"])
def test_unsupported_disclosure_is_domain_invalid_request(tmp_path: Path, requested: str) -> None:
    completed, response = _run(
        tmp_path,
        "call",
        "read-specification-candidates",
        stdin=json.dumps({"requested_disclosure": requested}),
    )

    assert completed.returncode == 2
    assert response["outcome"] == "invalid_request"
    assert response["result"] is None
    assert any("不受本操作支持" in item["summary"] for item in response["gaps"])


def test_exact_mixed_selection_preserves_completed_item_and_unknown_key(tmp_path: Path) -> None:
    completed, response = _run(
        tmp_path,
        "call",
        "read-specification-candidates",
        stdin=json.dumps(
            {
                "arguments": {
                    "responsibility_keys": ["ldvh-root", "ldvh-roo"],
                }
            }
        ),
    )

    assert completed.returncode == 3
    assert response["outcome"] == "partial"
    assert [item["key"] for item in response["result"]["items"]] == ["ldvh-root"]
    assert response["scope"]["requested"] == ["ldvh-root", "ldvh-roo"]
    assert response["scope"]["completed"] == ["ldvh-root"]
    assert response["scope"]["not_completed"] == ["ldvh-roo"]
    assert any("未精确匹配" in item["summary"] for item in response["gaps"])


def test_l2_call_returns_cumulative_attachment_relationships(tmp_path: Path) -> None:
    completed, response = _run(
        tmp_path,
        "call",
        "read-specification-candidates",
        stdin=json.dumps(
            {
                "arguments": {
                    "responsibility_keys": ["ldvh-bilingual-terminology"],
                },
                "requested_disclosure": "L2",
            }
        ),
    )

    assert completed.returncode == 0
    item = response["result"]["items"][0]
    assert item["overview"] is not None
    assert item["relationships"]["parent_spec"] == {
        "key": "specification-model-foundation",
        "path": "specs/01-规范模型基础规范.md",
    }
    assert [part["level"] for part in response["disclosure"]["parts"]] == ["L0", "L1", "L2"]


@pytest.mark.parametrize("command", [("capabilities", "one", "extra"), ("call", "one", "extra")])
def test_recognized_command_with_extra_arguments_is_json_invalid_request(
    tmp_path: Path,
    command: tuple[str, str, str],
) -> None:
    completed, response = _run(tmp_path, *command)

    assert completed.returncode == 2
    assert response["outcome"] == "invalid_request"
    assert response["operation_key"] == "one"


@pytest.mark.parametrize("command", [(), ("call",), ("unknown-entry",)])
def test_shape_without_fields_required_by_common_response_stays_process_usage_error(
    tmp_path: Path,
    command: tuple[str, ...],
) -> None:
    completed = subprocess.run(
        [str(HELPER_EXECUTABLE), *command],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 2
    assert completed.stdout == ""
    assert completed.stderr.startswith("usage: ldvh ")


@pytest.mark.parametrize("command", [("capabilities", "unknown-operation"), ("call", "unknown-operation")])
def test_unknown_operation_is_invalid_request(tmp_path: Path, command: tuple[str, str]) -> None:
    completed, response = _run(tmp_path, *command)

    assert completed.returncode == 2
    assert response["outcome"] == "invalid_request"
    assert response["operation_key"] == "unknown-operation"
    assert response["result"] is None


def test_invalid_json_is_a_machine_response(tmp_path: Path) -> None:
    completed, response = _run(tmp_path, "capabilities", stdin="not-json")

    assert completed.returncode == 2
    assert response["outcome"] == "invalid_request"
    assert response["gaps"]


def test_invalid_utf8_is_a_machine_invalid_request(tmp_path: Path) -> None:
    completed = subprocess.run(
        [str(HELPER_EXECUTABLE), "capabilities"],
        cwd=tmp_path,
        input=b"\xff",
        capture_output=True,
        check=False,
    )
    response = json.loads(completed.stdout.decode("utf-8"))
    assert_common_response(response)

    assert completed.returncode == 2
    assert completed.stderr == b""
    assert response["outcome"] == "invalid_request"
    assert response["gaps"][0]["summary"] == "标准输入必须是 UTF-8"


def test_specification_content_capabilities_and_l4_call_use_exact_current_source(tmp_path: Path) -> None:
    request = {
        "arguments": {
            "selections": [{"responsibility_key": "ldvh-root", "heading_path": None}],
        },
        "requested_disclosure": "L4",
    }
    checked, check_response = _run(
        tmp_path,
        "capabilities",
        "read-specification-content",
        stdin=json.dumps(request),
    )
    called, call_response = _run(
        tmp_path,
        "call",
        "read-specification-content",
        stdin=json.dumps(request),
    )

    assert checked.returncode == 0
    operation = check_response["result"]["operations"][0]
    assert operation["availability"] == "available_for_request"
    assert operation["required_inputs"] == ["arguments.selections", "requested_disclosure"]
    assert operation["optional_inputs"] == []
    assert operation["available_scope"] == request["arguments"]["selections"]
    assert operation["unavailable_scope"] == []

    assert called.returncode == 0
    assert call_response["outcome"] == "ok"
    item = call_response["result"]["items"][0]
    assert item["key"] == "ldvh-root"
    assert item["requested_disclosure"] == item["actual_disclosure"] == "L4"
    assert item["parts"][0]["content"].startswith("# 理念与构成\n")
    source = item["parts"][0]["source"]
    assert source["locator"].startswith("specs/00-理念与构成.md#L1-L")
    assert source["observed_at"]
    assert source["details"]["git_worktree_root"].endswith("ld-vibe-harness-v4")
    assert call_response["disclosure"]["parts"] == [
        {"level": "L4", "source_refs": [source], "reason": "请求 L4，按契约返回完整来源"}
    ]
    assert call_response["changes"] == []


def test_specification_content_l3_expands_and_attachment_l4_includes_parent(tmp_path: Path) -> None:
    l3_request = {
        "arguments": {
            "selections": [
                {
                    "responsibility_key": "specification-model-foundation",
                    "heading_path": ["5. 基础术语", "5.1 规范文档（Specification）"],
                }
            ]
        },
        "requested_disclosure": "L3",
    }
    expanded, expanded_response = _run(
        tmp_path,
        "call",
        "read-specification-content",
        stdin=json.dumps(l3_request),
    )
    attachment_request = {
        "arguments": {"selections": [{"responsibility_key": "ldvh-bilingual-terminology", "heading_path": None}]},
        "requested_disclosure": "L4",
    }
    attachment, attachment_response = _run(
        tmp_path,
        "call",
        "read-specification-content",
        stdin=json.dumps(attachment_request),
    )

    assert expanded.returncode == 0
    expanded_item = expanded_response["result"]["items"][0]
    assert expanded_item["requested_disclosure"] == "L3"
    assert expanded_item["actual_disclosure"] == "L4"
    assert expanded_item["expanded_to_l4"] is True
    assert expanded_item["expansion_reason"]

    assert attachment.returncode == 0
    parts = attachment_response["result"]["items"][0]["parts"]
    assert [part["source"]["details"]["responsibility_key"] for part in parts] == [
        "ldvh-bilingual-terminology",
        "specification-model-foundation",
    ]


def test_specification_content_invalid_exact_selection_is_invalid_request(tmp_path: Path) -> None:
    completed, response = _run(
        tmp_path,
        "call",
        "read-specification-content",
        stdin=json.dumps(
            {
                "arguments": {
                    "selections": [
                        {"responsibility_key": "specification-model-foundation", "heading_path": ["Unknown H2"]}
                    ]
                },
                "requested_disclosure": "L3",
            }
        ),
    )

    assert completed.returncode == 2
    assert response["outcome"] == "invalid_request"
    assert response["result"] is None
    assert any("无法精确唯一匹配" in gap["summary"] for gap in response["gaps"])
