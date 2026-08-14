from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from ldvh.diagnostics import Issue, SourceLocation
from ldvh.helper.operation_runtime import AvailabilityEvaluation, OperationExecution, OperationImplementation
from ldvh.helper.operation_sources import OperationSourceInspection, inspect_operation_sources
from ldvh.helper.operations import IMPLEMENTATIONS
from ldvh.helper.responses import gap, source_reference
from ldvh.helper.rule_source import RuleSourceResult, inspect_colocated_rule_source
from ldvh.helper.service import handle_request
from ldvh.specs.repository import RepositoryInspection, inspect_repository


def _working_rule_source(tmp_path: Path) -> RuleSourceResult:
    repository = RepositoryInspection(
        repository_root=tmp_path,
        candidates=(),
        parsed_documents=(),
        active_documents_passing_implemented_checks=(),
        projections=(),
        issues=(),
        incomplete_scope=(),
        unchecked_conditions=(),
        basis_reachability_overlaps=(),
        implemented_checks_complete=True,
    )
    from ldvh.helper.operation_sources import OperationDeclarationCandidate

    declaration = OperationDeclarationCandidate(
        operation_key="read-source",
        summary="Read one source",
        effect="read",
        arguments_contract="source-one::输入字段",
        result_contract="source-one::结果字段",
        source_key="source-one",
        source=SourceLocation("specs/source-one.md", 20, "Helper 公开操作"),
    )
    return RuleSourceResult(repository, OperationSourceInspection((declaration,), (), (), (), ()), None)


def _implementation(*, raises: bool = False) -> OperationImplementation:
    def call(_request, _repository, _context) -> OperationExecution:
        if raises:
            raise RuntimeError("private failure detail")
        return OperationExecution(
            outcome="partial",
            summary="one fake range completed",
            result={"items": ["one"]},
            requested_scope=("one", "two"),
            completed_scope=("one",),
            not_completed_scope=("two",),
            sources=(source_reference("observation", "fake-runtime"),),
            gaps=(gap("second range unavailable", scope=["two"]),),
        )

    return OperationImplementation(
        required_inputs=("arguments.source_key",),
        optional_inputs=("requested_disclosure",),
        evidence=(source_reference("implementation", "ldvh.test.fake"),),
        check_availability=lambda _request, _repository, _context: AvailabilityEvaluation(
            "partially_available",
            available_scope=("one",),
            unavailable_scope=("two",),
            gaps=(gap("second range unavailable", scope=["two"]),),
        ),
        call=call,
    )


def test_rule_source_location_gap_is_unavailable(monkeypatch) -> None:
    monkeypatch.setattr(
        "ldvh.helper.service.inspect_colocated_rule_source",
        lambda _: RuleSourceResult(None, None, "没有共置规则源"),
    )

    result = handle_request("capabilities", None, "")

    assert result.exit_code == 5
    assert result.response["outcome"] == "unavailable"
    assert result.response["gaps"][0]["summary"] == "没有共置规则源"


def test_capability_profiles_preserve_domain_result_and_compact_size(monkeypatch) -> None:
    monkeypatch.setattr("ldvh.helper.service.utc_now_iso", lambda: "2026-07-20T08:30:00Z")
    monkeypatch.setattr("ldvh.governance.resolver.utc_now_iso", lambda **_: "2026-07-20T08:30:00Z")
    real_inspect = inspect_colocated_rule_source
    inspect_cache: dict[Path, RuleSourceResult] = {}

    def memoized_inspect(package_file: Path) -> RuleSourceResult:
        if package_file not in inspect_cache:
            inspect_cache[package_file] = real_inspect(package_file)
        return inspect_cache[package_file]

    monkeypatch.setattr("ldvh.helper.service.inspect_colocated_rule_source", memoized_inspect)

    compact = handle_request("capabilities", None, json.dumps({"response_profile": "compact"})).response
    diagnostic = handle_request("capabilities", None, json.dumps({"response_profile": "diagnostic"})).response
    single_compact = handle_request(
        "capabilities",
        "resolve-governance-scope",
        json.dumps({"response_profile": "compact"}),
    ).response
    single_diagnostic = handle_request(
        "capabilities",
        "resolve-governance-scope",
        json.dumps({"response_profile": "diagnostic"}),
    ).response

    assert compact["result"] == diagnostic["result"]
    assert single_compact["result"] == single_diagnostic["result"]
    compact_bytes = len(json.dumps(compact, ensure_ascii=False, separators=(",", ":")).encode())
    diagnostic_bytes = len(json.dumps(diagnostic, ensure_ascii=False, separators=(",", ":")).encode())
    assert compact_bytes <= diagnostic_bytes * 0.65


def test_candidate_discovery_publishes_only_the_source_bound_text_match_input_fragment() -> None:
    response = handle_request("capabilities", None, "").response
    operations = response["result"]["operations"]
    candidate_operation = next(
        operation for operation in operations if operation["operation_key"] == "find-fact-object-candidates"
    )

    assert all(
        operation["input_examples"] == []
        for operation in operations
        if operation["operation_key"] not in {"find-fact-object-candidates", "update-fact-object"}
    )
    assert len(candidate_operation["input_examples"]) == 2
    assert candidate_operation["input_examples"][0] == {
        "summary": "按 Spark 标题进行 F2 文本筛选",
        "arguments_fragment": {
            "card_layer": "F2",
            "fact_type_keys": ["spark"],
            "text_match": {"text": "text", "field_paths": ["title"]},
        },
        "source_refs": candidate_operation["input_examples"][0]["source_refs"],
        "composition_note": (
            "这是可组合输入片段，不是完整请求；调用者仍须加入当前实际 governed_project_id，"
            "并可按所选类型当前允许的 F2 字段替换 text 与 field_paths。"
        ),
    }
    source = candidate_operation["input_examples"][0]["source_refs"][0]
    assert source["kind"] == "rule"
    assert source["locator"] == "fact-model-foundation::11.5 事实对象候选发现输入字段"


def test_fact_update_publishes_a_source_bound_read_to_update_after_example() -> None:
    response = handle_request("capabilities", None, "").response
    operation = next(
        item for item in response["result"]["operations"] if item["operation_key"] == "update-fact-object"
    )

    assert len(operation["input_examples"]) == 1
    example = operation["input_examples"][0]
    fragment = example["arguments_fragment"]
    fact_object = fragment["fact_object"]
    assert set(fact_object).isdisjoint({"object_uid", "object_id", "fact_type_key", "created_at", "updated_at"})
    assert set(fragment) == {"fact_ref", "expected_content_fingerprint", "fact_object"}
    assert len(fact_object["change_log"]) == 2
    assert fact_object["change_log"][-1]["signature"] == {
        "product_name": None,
        "model_name": None,
        "agent_runtime_name": None,
    }
    assert [source["locator"] for source in example["source_refs"]] == [
        "fact-model-foundation::11.2 事实对象读取结果字段",
        "fact-model-foundation::11.7 事实对象单对象 CAS 更新输入与结果",
    ]
    assert "全部非托管字段" in example["composition_note"]
    assert "observed_context.signature" in example["composition_note"]


def test_repository_problem_is_not_rewritten_as_empty_discovery(monkeypatch, tmp_path: Path) -> None:
    issue = Issue("规则源检查失败", SourceLocation("specs/broken.md"), affected=("broken",))
    repository = RepositoryInspection(
        repository_root=tmp_path,
        candidates=(),
        parsed_documents=(),
        active_documents_passing_implemented_checks=(),
        projections=(),
        issues=(issue,),
        incomplete_scope=("broken",),
        unchecked_conditions=(),
        basis_reachability_overlaps=(),
        implemented_checks_complete=False,
    )
    operations = OperationSourceInspection((), (), (), ())
    monkeypatch.setattr(
        "ldvh.helper.service.inspect_colocated_rule_source",
        lambda _: RuleSourceResult(repository, operations, None),
    )

    result = handle_request("capabilities", None, "")

    assert result.exit_code == 5
    assert result.response["outcome"] == "unavailable"
    assert result.response["result"] is None
    assert result.response["scope"]["not_completed"] == ["broken"]
    assert result.response["diagnostics"][0]["summary"] == "规则源检查失败"
    assert result.response["diagnostics"][0]["details"] == {
        "path": "specs/broken.md",
        "line": None,
        "affected": ["broken"],
    }
    assert result.response["diagnostics"][0]["source_refs"] == [
        {
            "kind": "rule",
            "locator": "specs/broken.md",
            "details": {
                "rule_source_view": "working_tree",
                "git_worktree_root": tmp_path.resolve().as_posix(),
            },
        }
    ]


def test_defined_implementation_is_discovered_and_preserves_partial_scope(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        "ldvh.helper.service.inspect_colocated_rule_source",
        lambda _: _working_rule_source(tmp_path),
    )
    monkeypatch.setattr("ldvh.helper.service.OPERATION_IMPLEMENTATIONS", {"read-source": _implementation()})

    discovered = handle_request("capabilities", None, "")
    checked = handle_request("capabilities", "read-source", "")
    called = handle_request("call", "read-source", "")

    operation = discovered.response["result"]["operations"][0]
    assert operation["implementation"] == {
        "present": True,
        "evidence": [
            {
                "kind": "implementation",
                "locator": "ldvh.test.fake",
                "details": {
                    "implementation_source_view": "working_tree",
                    "git_worktree_root": tmp_path.resolve().as_posix(),
                },
            }
        ],
    }
    assert operation["required_inputs"] == ["arguments.source_key"]
    assert operation["optional_inputs"] == ["requested_disclosure"]
    assert operation["input_examples"] == []
    assert checked.response["result"]["operations"][0]["availability"] == "partially_available"
    assert checked.response["result"]["operations"][0]["available_scope"] == ["one"]
    assert called.response["outcome"] == "partial"
    assert called.exit_code == 3
    assert called.response["scope"] == {
        "requested": ["one", "two"],
        "completed": ["one"],
        "not_completed": ["two"],
        "governance_resolution": None,
    }


def test_execution_can_carry_governance_resolution(monkeypatch, tmp_path: Path) -> None:
    source = _working_rule_source(tmp_path)
    implementation = _implementation()
    original_call = implementation.call
    governance_resolution = {
        "workspace_root": "/workspace",
        "config_path": "/workspace/LDVH-GOVERNED-PROJECTS.yaml",
        "config_status": "valid",
        "scope_status": "governed_single",
        "object_resolutions": [],
        "source_refs": [{"kind": "rule", "locator": "fixture"}],
    }

    def call_with_governance(request, repository, context):
        execution = original_call(request, repository, context)
        return replace(execution, governance_resolution=governance_resolution)

    monkeypatch.setattr("ldvh.helper.service.inspect_colocated_rule_source", lambda _: source)
    monkeypatch.setattr(
        "ldvh.helper.service.OPERATION_IMPLEMENTATIONS",
        {"read-source": replace(implementation, call=call_with_governance)},
    )

    called = handle_request("call", "read-source", "")

    assert called.response["scope"]["governance_resolution"] == governance_resolution


def test_undeclared_implementation_is_diagnostic_only(monkeypatch, tmp_path: Path) -> None:
    source = _working_rule_source(tmp_path)
    monkeypatch.setattr("ldvh.helper.service.inspect_colocated_rule_source", lambda _: source)
    monkeypatch.setattr("ldvh.helper.service.OPERATION_IMPLEMENTATIONS", {"internal-only": _implementation()})

    result = handle_request("capabilities", None, "")

    assert [item["operation_key"] for item in result.response["result"]["operations"]] == ["read-source"]
    assert result.response["result"]["operations"][0]["implementation"]["present"] is False
    assert result.response["diagnostics"][0]["details"]["implementation_key"] == "internal-only"


def test_unknown_key_remains_invalid_when_other_implementation_exists(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        "ldvh.helper.service.inspect_colocated_rule_source",
        lambda _: _working_rule_source(tmp_path),
    )
    monkeypatch.setattr("ldvh.helper.service.OPERATION_IMPLEMENTATIONS", {"read-source": _implementation()})

    result = handle_request("call", "unknown-source", "")

    assert result.response["outcome"] == "invalid_request"
    assert result.response["result"] is None


def test_implementation_exception_is_bounded_error(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        "ldvh.helper.service.inspect_colocated_rule_source",
        lambda _: _working_rule_source(tmp_path),
    )
    monkeypatch.setattr("ldvh.helper.service.OPERATION_IMPLEMENTATIONS", {"read-source": _implementation(raises=True)})

    result = handle_request("call", "read-source", "")

    assert result.exit_code == 1
    assert result.response["outcome"] == "error"
    assert result.response["scope"]["requested"] == ["read-source"]
    assert result.response["scope"]["not_completed"] == ["read-source"]
    assert result.response["diagnostics"][0]["details"] == {
        "operation_key": "read-source",
        "exception_type": "RuntimeError",
    }
    assert "private failure detail" not in str(result.response)


def test_unrelated_candidate_problem_does_not_block_defined_operation(
    monkeypatch,
    current_specs_repository: Path,
) -> None:
    inspected = inspect_repository(current_specs_repository)
    issue = Issue(
        "Unrelated candidate failed",
        SourceLocation("specs/99-Broken.md"),
        affected=("broken",),
    )
    repository = replace(
        inspected,
        issues=(issue,),
        incomplete_scope=("broken",),
        implemented_checks_complete=False,
    )
    operations = inspect_operation_sources(repository)
    monkeypatch.setattr(
        "ldvh.helper.service.inspect_colocated_rule_source",
        lambda _: RuleSourceResult(repository, operations, None),
    )
    monkeypatch.setattr("ldvh.helper.service.OPERATION_IMPLEMENTATIONS", dict(IMPLEMENTATIONS))

    discovered = handle_request("capabilities", None, "")
    called = handle_request(
        "call",
        "read-specification-candidates",
        json.dumps({"arguments": {"responsibility_keys": ["ldvh-root"]}}),
    )
    unknown = handle_request("call", "possibly-hidden-operation", "")

    assert discovered.response["outcome"] == "partial"
    assert discovered.response["scope"]["completed"] == [
        "begin-workcase-termination",
        "check-current-governed-sources",
        "check-fact-integrity",
        "check-workcase-handoff",
        "close-workcase",
        "complete-workcase-termination",
        "correct-closed-workcase",
        "create-fact-object",
        "find-fact-object-candidates",
        "git-hooks-status",
        "migrate-legacy-routed-spark",
        "precheck-git-commit",
        "prepare-closed-workcase-candidate",
        "prepare-fact-object-draft",
        "prepare-local-edit-candidates",
        "read-action-template-candidates",
        "read-action-template-content",
        "read-fact-objects",
        "read-specification-candidates",
        "read-specification-content",
        "read-specification-context",
        "recover-invalid-workcase",
        "resolve-governance-scope",
        "update-fact-object",
        "update-workcase",
    ]
    assert discovered.response["scope"]["not_completed"] == ["broken"]
    governance = next(
        item
        for item in discovered.response["result"]["operations"]
        if item["operation_key"] == "resolve-governance-scope"
    )
    assert governance["implementation"]["present"] is True
    assert governance["required_inputs"] == []
    facts = next(
        item for item in discovered.response["result"]["operations"] if item["operation_key"] == "read-fact-objects"
    )
    assert facts["implementation"]["present"] is True
    assert facts["required_inputs"] == ["arguments.fact_refs"]
    assert governance["optional_inputs"] == ["work_object_locators", "arguments.workspace_root"]
    assert any(source["locator"] == "specs/99-Broken.md" for source in discovered.response["sources"])
    assert discovered.response["diagnostics"][-1]["details"]["path"] == "specs/99-Broken.md"
    assert discovered.response["diagnostics"][-1]["source_refs"] == [
        {
            "kind": "rule",
            "locator": "specs/99-Broken.md",
            "details": {
                "rule_source_view": "working_tree",
                "git_worktree_root": current_specs_repository.resolve().as_posix(),
            },
        }
    ]
    assert called.response["outcome"] == "ok"
    assert called.response["scope"]["completed"] == ["ldvh-root"]
    assert unknown.response["outcome"] == "unavailable"
    assert unknown.response["result"] is None
    assert any(source["locator"] == "specs/99-Broken.md" for source in unknown.response["sources"])
