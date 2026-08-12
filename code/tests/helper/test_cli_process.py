from __future__ import annotations

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


def test_general_discovery_reports_source_bound_implementation(tmp_path: Path) -> None:
    completed, response = _run(tmp_path, "capabilities")

    assert completed.returncode == 0
    assert response["outcome"] == "ok"
    assert response["operation_key"] is None
    assert response["result"]["mode"] == "discovery"
    assert len(response["result"]["operations"]) == 22
    operations = {item["operation_key"]: item for item in response["result"]["operations"]}
    local_edit = operations["prepare-local-edit-candidates"]
    assert local_edit["effect"] == "read"
    assert local_edit["implementation"]["present"] is True
    assert local_edit["required_inputs"] == ["arguments.source_kind"]
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
        "arguments.fact_object",
    ]
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
    assert template_content["optional_inputs"] == []
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
    assert sum(item["member_count"] for item in response["gaps"]) == 176


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
            "fact_ref": {"governed_project_id": "ldvh", "fact_type_key": "study", "object_id": "study-0030"},
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
    assert len(response["gaps"]) == 176
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

    assert discovered.returncode == read.returncode == 0
    assert candidate_response["outcome"] == "ok"
    assert [item["template_key"] for item in candidate_response["result"]["items"]] == [
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
    assert [item["template_key"] for item in content_response["result"]["items"]] == [
        "git-commit",
        "fact-object-controlled-creation",
        "fact-object-lifecycle-change",
        "environment-integration-installation-verification",
        "workcase-approved-plan-execution",
    ]
    assert all("## 8. Stop Conditions" in item["source_content"] for item in content_response["result"]["items"])
    assert all(
        len(item["content_sha256"]) == len(item["source_content_sha256"]) == 64
        for item in content_response["result"]["items"]
    )
    assert content_response["changes"] == []


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
