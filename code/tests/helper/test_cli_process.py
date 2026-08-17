from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

import pytest
from conftest import HELPER_EXECUTABLE, PROJECT_ROOT, assert_common_response


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


def _assert_working_tree_implementation(
    implementation: dict[str, Any],
    locator: str,
) -> None:
    assert implementation["present"] is True
    assert len(implementation["evidence"]) == 1
    evidence = implementation["evidence"][0]
    assert evidence["kind"] == "implementation"
    assert evidence["locator"] == locator
    assert evidence["details"]["implementation_source_view"] == "working_tree"
    assert evidence["details"]["git_worktree_root"].endswith(PROJECT_ROOT.name)


def test_helper_uses_repository_source_launcher() -> None:
    assert HELPER_EXECUTABLE == PROJECT_ROOT / "ldvh"
    assert HELPER_EXECUTABLE.is_file()


def test_explicit_check_shortcut_uses_the_public_operation_contract() -> None:
    completed, response = _run(PROJECT_ROOT, "check")

    assert completed.returncode == 0
    assert response["operation_key"] == "check-current-governed-sources"
    assert response["outcome"] == "ok"
    assert response["result"]["status"] == "passed"

    invalid, invalid_response = _run(PROJECT_ROOT, "check", "unexpected")
    assert invalid.returncode == 2
    assert invalid_response["outcome"] == "invalid_request"


def test_general_discovery_reports_source_bound_implementation(tmp_path: Path) -> None:
    completed, response = _run(tmp_path, "capabilities")

    assert completed.returncode == 0
    assert response["outcome"] == "ok"
    assert response["operation_key"] is None
    assert response["result"]["mode"] == "discovery"
    assert len(response["result"]["operations"]) == 26
    operations = {item["operation_key"]: item for item in response["result"]["operations"]}
    check = operations["check-current-governed-sources"]
    assert check["implementation"]["present"] is True
    assert check["required_inputs"] == []
    assert check["optional_inputs"] == []
    local_edit = operations["prepare-local-edit-candidates"]
    assert local_edit["effect"] == "read"
    assert local_edit["implementation"]["present"] is True
    assert local_edit["required_inputs"] == ["arguments.source_kind"]
    handoff = operations["check-workcase-handoff"]
    assert handoff["implementation"]["present"] is True
    assert handoff["effect"] == "read"
    assert handoff["required_inputs"] == ["arguments.fact_ref"]
    candidates = operations["find-fact-object-candidates"]
    assert candidates["implementation"]["present"] is True
    assert candidates["required_inputs"] == [
        "arguments.governed_project_id",
        "arguments.card_layer",
    ]
    assert operations["prepare-fact-object-draft"]["required_inputs"] == [
        "arguments.governed_project_id",
        "arguments.fact_type_key",
    ]
    assert operations["create-fact-object"]["required_inputs"] == [
        "arguments.draft_basis",
        "arguments.fact_object",
    ]
    facts = operations["read-fact-objects"]
    assert facts["implementation"]["present"] is True
    assert facts["required_inputs"] == ["arguments.fact_refs"]
    assert operations["update-fact-object"]["required_inputs"] == [
        "arguments.fact_ref",
        "arguments.expected_content_fingerprint",
        "arguments.fact_object",
    ]
    assert operations["update-workcase"]["required_inputs"] == [
        "arguments.fact_ref",
        "arguments.expected_content_fingerprint",
    ]
    assert "arguments.item_event" in operations["update-workcase"]["optional_inputs"]
    assert operations["update-workcase"]["implementation"]["present"] is True
    assert operations["close-workcase"]["required_inputs"] == [
        "arguments.fact_ref",
        "arguments.expected_content_fingerprint",
        "arguments.fact_object",
        "authorization_reference",
    ]
    assert operations["close-workcase"]["implementation"]["present"] is True
    assert operations["begin-workcase-termination"]["required_inputs"] == [
        "arguments.fact_ref",
        "arguments.expected_content_fingerprint",
        "arguments.fact_object",
        "authorization_reference",
    ]
    assert operations["begin-workcase-termination"]["implementation"]["present"] is True
    assert operations["complete-workcase-termination"]["required_inputs"] == [
        "arguments.fact_ref",
        "arguments.expected_content_fingerprint",
        "arguments.fact_object",
    ]
    assert operations["complete-workcase-termination"]["implementation"]["present"] is True
    assert operations["correct-closed-workcase"]["required_inputs"] == [
        "arguments.fact_ref",
        "arguments.expected_content_fingerprint",
        "arguments.fact_object",
        "arguments.route_target_fingerprints",
        "arguments.independent_review_reference",
    ]
    assert operations["correct-closed-workcase"]["implementation"]["present"] is True
    operation = operations["read-specification-candidates"]
    assert operation["operation_key"] == "read-specification-candidates"
    _assert_working_tree_implementation(
        operation["implementation"],
        "code/ldvh/helper/operations/specification_candidate_operation.py",
    )
    assert operation["availability"] is None
    assert operation["required_inputs"] == []
    assert operation["optional_inputs"] == [
        "arguments.responsibility_keys",
        "requested_disclosure",
    ]
    content = operations["read-specification-content"]
    _assert_working_tree_implementation(
        content["implementation"],
        "code/ldvh/helper/operations/specification_content_operation.py",
    )
    assert content["required_inputs"] == ["arguments.selections", "requested_disclosure"]
    assert content["optional_inputs"] == []
    assert content["availability"] is None
    context = operations["read-specification-context"]
    _assert_working_tree_implementation(
        context["implementation"],
        "code/ldvh/helper/operations/specification_context_operation.py",
    )
    assert context["required_inputs"] == ["arguments.contexts", "requested_disclosure"]
    assert context["optional_inputs"] == []
    assert context["availability"] is None
    template_candidates = operations["read-action-template-candidates"]
    _assert_working_tree_implementation(
        template_candidates["implementation"],
        "code/ldvh/helper/operations/action_template_operation.py",
    )
    assert template_candidates["required_inputs"] == []
    assert template_candidates["optional_inputs"] == ["arguments.template_keys"]
    assert template_candidates["availability"] is None
    template_content = operations["read-action-template-content"]
    assert template_content["implementation"]["present"] is True
    assert template_content["required_inputs"] == ["arguments.template_keys"]
    assert template_content["optional_inputs"] == ["arguments.heading_path"]
    assert template_content["availability"] is None
    governance = operations["resolve-governance-scope"]
    _assert_working_tree_implementation(
        governance["implementation"],
        "code/ldvh/helper/operations/governance_scope_operation.py",
    )
    assert governance["required_inputs"] == []
    assert governance["optional_inputs"] == ["work_object_locators", "arguments.workspace_root"]
    commit_precheck = operations["precheck-git-commit"]
    assert commit_precheck["implementation"]["present"] is True
    assert {item["locator"] for item in commit_precheck["implementation"]["evidence"]} == {
        "code/ldvh/commits/precheck.py",
        "code/ldvh/helper/operations/commit_precheck_operation.py",
    }
    assert commit_precheck["required_inputs"] == ["work_object_locators", "arguments.message"]
    assert commit_precheck["optional_inputs"] == ["arguments.workspace_root"]
    assert len(response["gaps"]) == 2
    assert sum(item["member_count"] for item in response["gaps"]) == 208


def test_real_cli_local_edit_candidates_supports_rule_and_study_modes() -> None:
    rule_request = {
        "arguments": {
            "source_kind": "rule",
            "responsibility_key": "ldvh-root",
            "heading_path": ["8. 系统级运行架构", "8.1 工作上下文的信息交付顺序与渐进式披露"],
            "candidate_after": "candidate\\n",
        }
    }
    study_request = {
        "work_object_locators": ["."],
        "arguments": {
            "source_kind": "study",
            "fact_ref": {
                "governed_project_id": "ldvh",
                "fact_type_key": "study",
                "object_id": "study-01KZXN5TXNFV8T3AQS1QCPAQ8B",
            },
            "body_heading": "建议",
        },
    }

    rule_completed, rule_response = _run(
        PROJECT_ROOT, "call", "prepare-local-edit-candidates", stdin=json.dumps(rule_request, ensure_ascii=False)
    )
    study_completed, study_response = _run(
        PROJECT_ROOT, "call", "prepare-local-edit-candidates", stdin=json.dumps(study_request, ensure_ascii=False)
    )

    assert rule_completed.returncode == 0
    assert study_completed.returncode == 0
    assert rule_response["changes"] == []
    assert study_response["changes"] == []
    assert rule_response["result"]["items"][0]["source_kind"] == "rule"
    assert study_response["result"]["items"][0]["source_kind"] == "study"
    assert study_response["scope"]["governance_resolution"]["scope_status"] == "governed_single"


def test_real_cli_prepare_exposes_definition_refs_without_a_second_schema() -> None:
    completed, response = _run(
        PROJECT_ROOT,
        "call",
        "prepare-fact-object-draft",
        stdin=json.dumps(
            {
                "work_object_locators": ["."],
                "arguments": {"governed_project_id": "ldvh", "fact_type_key": "spark"},
            }
        ),
    )

    assert completed.returncode == 0
    assert response["outcome"] == "ok"
    contracts = response["result"]["field_contracts"]
    priority = next(item for item in contracts if item["field_path"] == "priority")
    assert priority["definition_ref"] == "fact-object-field-registry::跨类型共享字段定义表::priority"
    assert priority["constraint_ref"] == "spark-fact-type::6. 对象语义与生命周期"
    assert all(
        set(item) == {"field_path", "json_type", "presence", "definition_ref", "constraint_ref"} for item in contracts
    )


def test_diagnostic_profile_expands_qualification_details(tmp_path: Path) -> None:
    completed, response = _run(
        tmp_path,
        "capabilities",
        stdin=json.dumps({"response_profile": "diagnostic"}),
    )

    assert completed.returncode == 0
    assert response["response_profile"] == "diagnostic"
    assert len(response["gaps"]) == 208
    assert all(item["summary"].startswith("当前 Code 尚未自动证明：") for item in response["gaps"])
    assert all("member_count" not in item for item in response["gaps"])


def test_defined_operation_check_and_call_return_actual_l0_results(tmp_path: Path) -> None:
    checked, check_response = _run(tmp_path, "capabilities", "read-specification-candidates")
    called, call_response = _run(tmp_path, "call", "read-specification-candidates")

    assert checked.returncode == 0
    assert check_response["outcome"] == "ok"
    checked_operation = check_response["result"]["operations"][0]
    assert checked_operation["availability"] == "available_for_request"
    assert len(checked_operation["available_scope"]) == 33
    assert "working-tree-test-evidence-fields" in checked_operation["available_scope"]
    assert "web-api-reading-contract" in checked_operation["available_scope"]
    assert checked_operation["unavailable_scope"] == []

    assert called.returncode == 0
    assert call_response["outcome"] == "ok"
    assert len(call_response["result"]["items"]) == 33
    assert "working-tree-test-evidence-fields" in {item["key"] for item in call_response["result"]["items"]}
    assert "web-api-reading-contract" in {item["key"] for item in call_response["result"]["items"]}
    assert call_response["scope"]["requested"] == call_response["scope"]["completed"]
    assert call_response["scope"]["not_completed"] == []
    assert call_response["disclosure"]["requested"] is None
    assert [part["level"] for part in call_response["disclosure"]["parts"]] == ["L0"]
    assert all(item["overview"] is None and item["relationships"] is None for item in call_response["result"]["items"])
    observed_sources = [
        source for source in call_response["sources"] if source["kind"] == "rule" and source["locator"] == "specs/"
    ]
    assert len(observed_sources) == 1
    assert observed_sources[0]["details"]["rule_source_view"] == "working_tree"
    assert observed_sources[0]["details"]["git_worktree_root"].endswith(PROJECT_ROOT.name)
    assert observed_sources[0]["details"]["responsibility_keys"]
    assert observed_sources[0]["details"]["paths"]
    assert all(
        any(
            evidence["kind"] == "rule"
            and evidence["locator"] == "specs/"
            and evidence["details"]["rule_source_view"] == "working_tree"
            for evidence in item["evidence"]
        )
        for item in call_response["verification"]
    )
    assert all(
        any(evidence["kind"] == "implementation" for evidence in item["evidence"])
        for item in call_response["verification"]
    )


def test_action_template_operations_discover_and_read_five_current_sources(tmp_path: Path) -> None:
    discovered, candidate_response = _run(tmp_path, "call", "read-action-template-candidates")
    tasked, tasked_response = _run(
        tmp_path,
        "call",
        "read-action-template-candidates",
        stdin=json.dumps({"task": "Metadata must not filter or rank action templates.", "arguments": {}}),
    )
    read, content_response = _run(
        tmp_path,
        "call",
        "read-action-template-content",
        stdin=json.dumps(
            {
                "arguments": {
                    "template_keys": [
                        "git-commit",
                        "fact-object-controlled-creation",
                        "fact-object-lifecycle-change",
                        "environment-integration-installation-verification",
                        "workcase-approved-plan-execution",
                    ]
                }
            }
        ),
    )

    assert discovered.returncode == tasked.returncode == read.returncode == 0
    assert candidate_response["outcome"] == tasked_response["outcome"] == "ok"
    assert tasked_response["result"] == candidate_response["result"]
    candidate_items = candidate_response["result"]["items"]
    candidate_fields = {
        "template_key",
        "summary",
        "activation_hint",
        "source_key",
        "canonical_path",
        "definition_ref",
        "definition_heading",
        "definition_start_line",
        "definition_end_line",
    }
    assert all(set(item) == candidate_fields for item in candidate_items)
    assert all(item["activation_hint"] for item in candidate_items)
    assert [item["template_key"] for item in candidate_items] == [
        "environment-integration-installation-verification",
        "fact-object-controlled-creation",
        "fact-object-lifecycle-change",
        "git-commit",
        "workcase-approved-plan-execution",
    ]
    assert candidate_response["result"]["unchecked_conditions"]
    assert content_response["outcome"] == "ok"
    assert content_response["scope"]["requested"] == content_response["scope"]["completed"]
    assert content_response["scope"]["not_completed"] == []
    content_items = content_response["result"]["items"]
    assert [item["template_key"] for item in content_items] == [
        "git-commit",
        "fact-object-controlled-creation",
        "fact-object-lifecycle-change",
        "environment-integration-installation-verification",
        "workcase-approved-plan-execution",
    ]
    assert all(
        set(item) == candidate_fields | {"content", "content_sha256", "source_content_sha256"} for item in content_items
    )
    candidate_hints = {item["template_key"]: item["activation_hint"] for item in candidate_items}
    assert all(item["activation_hint"] == candidate_hints[item["template_key"]] for item in content_items)
    assert all("## 8. Stop Conditions" in item["content"] for item in content_items)
    assert all("source_content" not in item for item in content_response["result"]["items"])
    assert all(
        len(item["content_sha256"]) == len(item["source_content_sha256"]) == 64
        for item in content_response["result"]["items"]
    )
    assert content_response["changes"] == []


def test_action_template_content_expands_same_source_through_l4(tmp_path: Path) -> None:
    _, template_response = _run(
        tmp_path,
        "call",
        "read-action-template-content",
        stdin=json.dumps({"arguments": {"template_keys": ["fact-object-controlled-creation"]}}),
    )
    item = template_response["result"]["items"][0]
    completed, source_response = _run(
        tmp_path,
        "call",
        "read-specification-content",
        stdin=json.dumps(
            {
                "requested_disclosure": "L4",
                "arguments": {
                    "selections": [
                        {"responsibility_key": item["source_key"], "heading_path": None}
                    ]
                },
            }
        ),
    )

    assert completed.returncode == 0
    source_item = source_response["result"]["items"][0]
    source_content = source_item["parts"][0]["content"]
    assert "source_content" not in item
    assert source_item["path"] == item["canonical_path"]
    assert hashlib.sha256(source_content.encode()).hexdigest() == item["source_content_sha256"]
    assert item["content"] in source_content


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
    assert source["details"]["git_worktree_root"].endswith(PROJECT_ROOT.name)
    disclosure = call_response["disclosure"]["parts"]
    assert len(disclosure) == 1
    assert disclosure[0]["level"] == "L4"
    assert disclosure[0]["source_refs"] == [source]
    assert disclosure[0]["reason"]
    assert call_response["changes"] == []


def test_specification_content_l3_slices_and_attachment_l4_includes_parent(tmp_path: Path) -> None:
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
    sliced, sliced_response = _run(
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

    assert sliced.returncode == 0
    sliced_item = sliced_response["result"]["items"][0]
    assert sliced_item["requested_disclosure"] == sliced_item["actual_disclosure"] == "L3"
    assert [part["level"] for part in sliced_item["parts"]] == ["L3", "L3"]

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


def test_specification_context_capability_and_call_return_complete_composite(tmp_path: Path) -> None:
    request = {
        "task": "must not select rules",
        "work_object_locators": ["ignored"],
        "arguments": {
            "contexts": [
                {
                    "responsibility_key": "specification-model-foundation",
                    "primary_heading_paths": [["5. 基础术语", "5.1 规范文档（Specification）"]],
                }
            ]
        },
        "requested_disclosure": "L3",
        "authorization_reference": [{"kind": "human", "locator": "ignored"}],
    }
    checked, check_response = _run(
        tmp_path,
        "capabilities",
        "read-specification-context",
        stdin=json.dumps(request),
    )
    called, call_response = _run(
        tmp_path,
        "call",
        "read-specification-context",
        stdin=json.dumps(request),
    )

    assert checked.returncode == 0
    operation = check_response["result"]["operations"][0]
    assert operation["availability"] == "available_for_request"
    assert operation["required_inputs"] == ["arguments.contexts", "requested_disclosure"]
    assert operation["available_scope"] == request["arguments"]["contexts"]

    assert called.returncode == 0
    assert call_response["outcome"] == "ok"
    assert call_response["changes"] == []
    assert call_response["scope"]["governance_resolution"] is None
    item = call_response["result"]["items"][0]
    assert item["responsibility_key"] == "specification-model-foundation"
    assert item["guard_coverage"] == {
        "applicability_scope": "returned",
        "verification": "returned",
        "human_gate": "returned",
        "stop_conditions": "returned",
    }
    assert call_response["disclosure"]["requested"] == "L3"
    assert call_response["disclosure"]["parts"][0]["level"] == "L1"
    assert all(part["level"] == "L3" for part in call_response["disclosure"]["parts"][1:])


def test_specification_context_invalid_heading_is_whole_request_invalid(tmp_path: Path) -> None:
    completed, response = _run(
        tmp_path,
        "call",
        "read-specification-context",
        stdin=json.dumps(
            {
                "arguments": {
                    "contexts": [{"responsibility_key": "ldvh-root", "primary_heading_paths": [["Unknown H2"]]}]
                },
                "requested_disclosure": "L3",
            }
        ),
    )

    assert completed.returncode == 2
    assert response["outcome"] == "invalid_request"
    assert response["result"] is None


def test_request_file_uses_same_helper_request_chain(tmp_path: Path) -> None:
    request = json.dumps({"response_profile": "compact"})
    request_file = tmp_path / "request.json"
    request_file.write_text(request, encoding="utf-8")

    from_file, file_response = _run(
        tmp_path,
        "capabilities",
        "read-action-template-candidates",
        "--request",
        str(request_file),
    )
    from_stdin, stdin_response = _run(
        tmp_path,
        "capabilities",
        "read-action-template-candidates",
        stdin=request,
    )

    assert from_file.returncode == from_stdin.returncode == 0
    assert file_response["outcome"] == stdin_response["outcome"] == "ok"
    assert file_response["result"]["mode"] == stdin_response["result"]["mode"] == "request_check"
    assert file_response["result"]["operations"][0]["operation_key"] == (
        stdin_response["result"]["operations"][0]["operation_key"]
    )


def test_request_file_preserves_raw_helper_json_diagnostics(tmp_path: Path) -> None:
    request_file = tmp_path / "invalid.json"
    request_file.write_text("{not-json", encoding="utf-8")

    completed, response = _run(tmp_path, "capabilities", "--request", request_file.name)

    assert completed.returncode == 2
    assert response["outcome"] == "invalid_request"
    assert any("JSON" in item["summary"] for item in response["gaps"])


@pytest.mark.parametrize("case", ["missing", "directory", "non_utf8", "oversize"])
def test_request_file_rejects_unsafe_inputs_before_helper_call(tmp_path: Path, case: str) -> None:
    request_path = tmp_path / "request.json"
    if case == "directory":
        request_path.mkdir()
    elif case == "non_utf8":
        request_path.write_bytes(b"\xff")
    elif case == "oversize":
        request_path.write_bytes(b" " * (4 * 1024 * 1024 + 1))

    completed, response = _run(tmp_path, "capabilities", "--request", str(request_path))

    assert completed.returncode == 2
    assert response["outcome"] == "invalid_request"
    assert response["changes"] == []
    assert "Traceback" not in completed.stderr


def test_request_file_rejects_symlink_before_helper_call(tmp_path: Path) -> None:
    target = tmp_path / "target.json"
    target.write_text("{}", encoding="utf-8")
    request_path = tmp_path / "request.json"
    try:
        request_path.symlink_to(target)
    except OSError:
        pytest.skip("symlink fixture is unavailable")

    completed, response = _run(tmp_path, "capabilities", "--request", str(request_path))

    assert completed.returncode == 2
    assert response["outcome"] == "invalid_request"
    assert response["changes"] == []


def test_request_file_rejects_live_empty_stdin_pipe_without_waiting(tmp_path: Path) -> None:
    request_path = tmp_path / "request.json"
    request_path.write_text("{}", encoding="utf-8")
    process = subprocess.Popen(
        [str(HELPER_EXECUTABLE), "capabilities", "--request", str(request_path)],
        cwd=tmp_path,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        returncode = process.wait(timeout=10)
        assert process.stdout is not None
        assert process.stderr is not None
        response = json.loads(process.stdout.read())
        stderr = process.stderr.read()
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        if process.stdin is not None:
            process.stdin.close()
        if process.stdout is not None:
            process.stdout.close()
        if process.stderr is not None:
            process.stderr.close()

    assert returncode == 2
    assert response["outcome"] == "invalid_request"
    assert response["changes"] == []
    assert stderr == ""


def test_request_file_rejects_nonempty_stdin_and_option_errors(tmp_path: Path) -> None:
    request_file = tmp_path / "request.json"
    request_file.write_text("{}", encoding="utf-8")

    conflict, conflict_response = _run(
        tmp_path,
        "capabilities",
        "--request",
        str(request_file),
        stdin="{}",
    )
    duplicate, duplicate_response = _run(
        tmp_path,
        "capabilities",
        "--request",
        str(request_file),
        "--request",
        str(request_file),
    )
    unknown, unknown_response = _run(tmp_path, "capabilities", "--unknown")
    dash, dash_response = _run(tmp_path, "capabilities", "--request", "-")

    for completed, response in (
        (conflict, conflict_response),
        (duplicate, duplicate_response),
        (unknown, unknown_response),
        (dash, dash_response),
    ):
        assert completed.returncode == 2
        assert response["outcome"] == "invalid_request"
        assert response["changes"] == []


def _run_projection(
    cwd: Path, *arguments: str, stdin: str = ""
) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
    completed = subprocess.run(
        [str(HELPER_EXECUTABLE), *arguments],
        cwd=cwd,
        input=stdin,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.stderr == ""
    return completed, json.loads(completed.stdout)


def test_example_projects_source_bound_write_signature_without_calling_operation(tmp_path: Path) -> None:
    before = list(tmp_path.iterdir())

    completed, projection = _run_projection(
        tmp_path,
        "capabilities",
        "create-fact-object",
        "--example",
    )

    assert completed.returncode == 0
    assert set(projection) == {
        "operation_key",
        "request",
        "required_input_paths",
        "composition_note",
        "source_refs",
        "response_fields",
        "result_contract",
    }
    assert projection["operation_key"] == "create-fact-object"
    assert projection["request"]["observed_context"]["signature"] == {
        "product_name": None,
        "model_name": None,
        "agent_runtime_name": None,
    }
    assert projection["request"]["arguments"]["draft_basis"] is None
    assert projection["request"]["arguments"]["fact_object"] is None
    assert "全为 null 时不可执行" in projection["composition_note"]
    # 04/05 交互改进: --example 必须暴露 response 字段闭集与结果契约,
    # 调用方无需再查阅 spec 的 "领域 result 字段闭集" 小节。
    assert isinstance(projection["response_fields"], list)
    assert isinstance(projection["result_contract"], str) and projection["result_contract"]
    assert list(tmp_path.iterdir()) == before


def test_example_uses_first_source_example_and_commit_trailer_order(tmp_path: Path) -> None:
    completed, projection = _run_projection(
        tmp_path,
        "capabilities",
        "precheck-git-commit",
        "--example",
    )

    assert completed.returncode == 0
    assert projection["request"]["work_object_locators"] is None
    message = projection["request"]["arguments"]["message"]
    assert message.splitlines()[-3:] == [
        "LDVH-Product-Name: <fill-directly-observed-product-name>",
        "LDVH-Model-Name: <fill-directly-observed-model-name>",
        "LDVH-Agent-Runtime-Name: <fill-directly-observed-agent-runtime-name>",
    ]
    assert "observed_context" not in projection["request"]
    assert any(
        source["locator"] == "source-of-truth-traceability::9.7 Git commit 候选机械预检输入字段"
        for source in projection["source_refs"]
    )


def test_example_rejects_wrong_entry_combination_and_nonempty_stdin(tmp_path: Path) -> None:
    invalid_cases = [
        ("capabilities", "--example"),
        ("call", "create-fact-object", "--example"),
        ("capabilities", "create-fact-object", "--example", "--request", "request.json"),
    ]
    for arguments in invalid_cases:
        completed, response = _run(tmp_path, *arguments)
        assert completed.returncode == 2
        assert response["outcome"] == "invalid_request"

    completed, response = _run(
        tmp_path,
        "capabilities",
        "create-fact-object",
        "--example",
        stdin="{}",
    )
    assert completed.returncode == 2
    assert response["outcome"] == "invalid_request"


def test_summary_projects_compact_discovery_middle_tier(tmp_path: Path) -> None:
    """capabilities --summary 提供渐进发现中间档,每个操作只暴露紧凑投影。"""
    completed, response = _run(tmp_path, "capabilities", "--summary")

    assert completed.returncode == 0
    assert response["outcome"] == "ok"
    assert response["result"]["mode"] == "discovery"
    operations = response["result"]["operations"]
    assert operations, "summary 应返回非空操作列表"
    expected_keys = {"operation_key", "summary", "effect", "result_contract", "response_fields"}
    for op in operations:
        assert set(op) == expected_keys, f"操作 {op.get('operation_key')} 投影字段闭集不符"
        assert isinstance(op["operation_key"], str) and op["operation_key"]
        assert isinstance(op["summary"], str) and op["summary"]
        assert isinstance(op["effect"], str) and op["effect"]
        assert isinstance(op["result_contract"], str) and op["result_contract"]
        assert isinstance(op["response_fields"], list)
    keys = [op["operation_key"] for op in operations]
    assert len(set(keys)) == len(keys), "operation_key 不应重复"
    assert "read-fact-objects" in keys


def test_summary_rejects_wrong_combinations_and_nonempty_stdin(tmp_path: Path) -> None:
    invalid_cases = [
        ("call", "read-fact-objects", "--summary"),
        ("capabilities", "create-fact-object", "--summary"),
        ("capabilities", "--summary", "--request", "request.json"),
        ("capabilities", "--summary", "--example"),
        ("capabilities", "--summary", "--fields", "outcome"),
    ]
    for arguments in invalid_cases:
        completed, response = _run(tmp_path, *arguments)
        assert completed.returncode == 2, arguments
        assert response["outcome"] == "invalid_request", arguments

    completed, response = _run(tmp_path, "capabilities", "--summary", stdin="{}")
    assert completed.returncode == 2
    assert response["outcome"] == "invalid_request"


def test_fields_projects_complete_response_with_mandatory_status_core(tmp_path: Path) -> None:
    completed, projection = _run_projection(
        tmp_path,
        "capabilities",
        "--fields",
        "outcome,result.mode",
    )

    assert completed.returncode == 0
    assert projection["projection"] == {
        "requested": ["outcome", "result.mode"],
        "missing": [],
        "source_outcome": "ok",
        "source_exit_code": 0,
        "source_gap_count": projection["projection"]["source_gap_count"],
        "source_response_complete": True,
    }
    assert projection["response"]["outcome"] == "ok"
    assert projection["response"]["result"] == {"mode": "discovery"}
    assert projection["response"]["scope"] == {"not_completed": []}
    assert isinstance(projection["projection"]["source_gap_count"], int)
    assert "gaps" not in projection["response"]
    assert "sources" not in projection["response"]
    assert "operations" not in projection["response"]["result"]


def test_check_shortcut_supports_fields_projection() -> None:
    completed, projection = _run_projection(
        PROJECT_ROOT,
        "check",
        "--fields",
        "outcome,result.status",
    )

    assert completed.returncode == 0
    assert projection["response"]["operation_key"] == "check-current-governed-sources"
    assert projection["response"]["outcome"] == "ok"
    assert projection["response"]["result"] == {"status": "passed"}


def test_fields_combines_with_request_file_and_selects_into_array_members(tmp_path: Path) -> None:
    request_file = tmp_path / "request.json"
    request_file.write_text("{}", encoding="utf-8")

    completed, projection = _run_projection(
        tmp_path,
        "capabilities",
        "--request",
        request_file.name,
        "--fields",
        "result.operations.operation_key",
    )

    assert completed.returncode == 0
    assert projection["projection"]["source_outcome"] == "ok"
    assert projection["projection"]["source_exit_code"] == 0
    assert projection["projection"]["missing"] == []
    assert projection["response"]["outcome"] == "ok"
    assert "operation_key" in projection["response"]["result"]["operations"][0]


def test_fields_selects_into_array_members_via_cli(tmp_path: Path) -> None:
    completed, projection = _run_projection(
        tmp_path,
        "capabilities",
        "--fields",
        "result.operations.operation_key,result.operations.summary",
    )

    assert completed.returncode == 0
    assert projection["projection"]["missing"] == []
    operations = projection["response"]["result"]["operations"]
    assert isinstance(operations, list) and operations
    assert all("operation_key" in op and "summary" in op for op in operations)
    assert all("sources" not in op for op in operations)


def test_fields_preserves_invalid_request_exit_and_actual_null(tmp_path: Path) -> None:
    completed, projection = _run_projection(
        tmp_path,
        "capabilities",
        "unknown-operation",
        "--fields",
        "result",
    )

    assert completed.returncode == 2
    assert projection["projection"]["source_exit_code"] == 2
    assert projection["projection"]["source_outcome"] == "invalid_request"
    assert projection["projection"]["missing"] == []
    assert projection["response"]["result"] is None
    assert projection["response"]["outcome"] == "invalid_request"


@pytest.mark.parametrize(
    "field_value",
    ["", "result..items", "result.*", "result.items[0]", "a,a", "result,result.items"],
)
def test_fields_rejects_invalid_selector_before_helper_call(tmp_path: Path, field_value: str) -> None:
    completed, response = _run(tmp_path, "capabilities", "--fields", field_value)

    assert completed.returncode == 2
    assert response["outcome"] == "invalid_request"
    assert response["changes"] == []
