from __future__ import annotations

from pathlib import Path

import pytest
from conftest import commit_all

from ldvh.diagnostics import Issue, SourceLocation
from ldvh.helper.operation_sources import inspect_operation_sources
from ldvh.specs import repository as repository_module
from ldvh.specs.action_templates import inspect_action_template_sources
from ldvh.specs.discovery import DiscoveryResult
from ldvh.specs.field_registry import inspect_field_registry
from ldvh.specs.repository import UNCHECKED_CONDITIONS, inspect_repository


def test_current_v4_sources_form_the_expected_real_combination(current_specs_repository: Path) -> None:
    inspection = inspect_repository(current_specs_repository)
    operations = inspect_operation_sources(inspection)
    action_templates = inspect_action_template_sources(inspection)
    fields = inspect_field_registry(inspection.active_documents_passing_implemented_checks)

    assert inspection.issues == ()
    assert inspection.implemented_checks_complete is True
    checked_documents = inspection.active_documents_passing_implemented_checks
    assert len(checked_documents) == 26
    assert sum(document.kind != "attachment" for document in checked_documents) == 19

    assert sum(document.kind == "attachment" for document in checked_documents) == 7
    assert len(inspection.projections) == 78
    assert {projection.layer for projection in inspection.projections} == {"L0", "L1", "L2"}
    field_registry = inspection.document_passing_implemented_checks_by_key("fact-object-field-registry")
    assert field_registry is not None
    assert field_registry.canonical_path == "specs/attachments/05.Att.01-事实对象统一字段登记.md"
    fact_model = inspection.document_passing_implemented_checks_by_key("fact-model-foundation")
    assert fact_model is not None
    assert "fact-object-field-registry" in fact_model.authorized_attachments
    code_practices = inspection.document_passing_implemented_checks_by_key("code-engineering-practices")
    assert code_practices is not None
    assert code_practices.authorized_attachments == ("working-tree-test-evidence-fields",)
    evidence_fields = inspection.document_passing_implemented_checks_by_key("working-tree-test-evidence-fields")
    assert evidence_fields is not None
    assert evidence_fields.current_id == "07.Att.01"
    assert evidence_fields.canonical_path == (
        "specs/attachments/07.Att.01-Working Tree 测试证据字段表.md"
    )
    helper_contract = inspection.document_passing_implemented_checks_by_key("helper-cli-service-contract")
    assert helper_contract is not None
    assert helper_contract.basis == (
        "ldvh-root",
        "specification-model-foundation",
        "work-object-governance-scope",
        "source-of-truth-traceability",
        "code-engineering-practices",
    )
    environment_integration = inspection.document_passing_implemented_checks_by_key("environment-integration")
    assert environment_integration is not None
    assert environment_integration.current_id == "09"
    assert environment_integration.canonical_path == "specs/09-环境接入规范.md"
    assert environment_integration.basis == (
        "ldvh-root",
        "work-object-governance-scope",
        "source-of-truth-traceability",
        "helper-cli-service-contract",
    )
    assert inspection.unchecked_conditions == UNCHECKED_CONDITIONS
    assert [declaration.operation_key for declaration in operations.candidate_declarations] == [
        "create-fact-object",
        "find-fact-object-candidates",
        "precheck-git-commit",
        "prepare-fact-object-draft",
        "read-action-template-candidates",
        "read-action-template-content",
        "read-fact-objects",
        "read-specification-candidates",
        "read-specification-content",
        "read-specification-context",
        "resolve-governance-scope",
        "update-fact-object",
        "update-workcase",
    ]
    declaration_sources = {
        declaration.operation_key: declaration.source.path for declaration in operations.candidate_declarations
    }
    assert declaration_sources == {
        "create-fact-object": "specs/05-事实模型基础规范.md",
        "find-fact-object-candidates": "specs/05-事实模型基础规范.md",
        "precheck-git-commit": "specs/03-事实源与信息溯源规范.md",
        "prepare-fact-object-draft": "specs/05-事实模型基础规范.md",
        "read-action-template-candidates": "specs/06-行动模板基础规范.md",
        "read-action-template-content": "specs/06-行动模板基础规范.md",
        "read-fact-objects": "specs/05-事实模型基础规范.md",
        "read-specification-candidates": "specs/01-规范模型基础规范.md",
        "read-specification-content": "specs/01-规范模型基础规范.md",
        "read-specification-context": "specs/01-规范模型基础规范.md",
        "resolve-governance-scope": "specs/02-工作对象与管辖范围规范.md",
        "update-fact-object": "specs/05-事实模型基础规范.md",
        "update-workcase": "specs/21-WorkCase-工作项.md",
    }
    assert operations.issues == ()
    assert operations.incomplete_sources == ()
    assert [declaration.template_key for declaration in action_templates.candidate_declarations] == [
        "environment-integration-installation-verification",
        "fact-object-controlled-creation",
        "fact-object-lifecycle-change",
        "git-commit",
    ]
    assert {
        declaration.template_key: (
            declaration.source_key,
            declaration.definition_heading.title,
        )
        for declaration in action_templates.candidate_declarations
    } == {
        "environment-integration-installation-verification": (
            "environment-integration-installation-verification-action-template",
            "5. 环境安装、部署、接入与验证行动模板定义",
        ),
        "fact-object-controlled-creation": (
            "fact-object-controlled-creation-action-template",
            "5. 事实对象判定与受控创建行动模板定义",
        ),
        "fact-object-lifecycle-change": (
            "fact-object-lifecycle-change-action-template",
            "5. 事实对象生命周期变更与承接处置行动模板定义",
        ),
        "git-commit": ("git-commit-action-template", "5. Git 提交行动模板定义"),
    }
    assert action_templates.issues == ()
    assert action_templates.incomplete_sources == ()
    assert fields.complete is True
    assert len(fields.structures) == 16
    assert len(fields.registrations) == 121


def test_mechanically_distinct_spec_does_not_create_a_semantic_duplicate_diagnosis(
    current_specs_repository: Path,
) -> None:
    source = (current_specs_repository / "specs/07-Code 实践与测试规范.md").read_text(encoding="utf-8")
    duplicate = current_specs_repository / "specs/90-Code-Semantic-Copy.md"
    duplicate.write_text(
        source.replace('spec_key: "code-engineering-practices"', 'spec_key: "code-engineering-practices-copy"', 1)
        .replace('spec_id: "07"', 'spec_id: "90"', 1)
        .replace('title: "Code 实践与测试规范"', 'title: "Code 实践与测试规范语义副本"', 1)
        .replace(
            'canonical_path: "specs/07-Code 实践与测试规范.md"',
            'canonical_path: "specs/90-Code-Semantic-Copy.md"',
            1,
        )
        .replace(
            '  authorized_attachments:\n    - "working-tree-test-evidence-fields"',
            "  authorized_attachments: []",
            1,
        )
        .replace("# Code 实践与测试规范", "# Code 实践与测试规范语义副本", 1),
        encoding="utf-8",
    )

    inspection = inspect_repository(current_specs_repository)

    assert inspection.document_passing_implemented_checks_by_key("code-engineering-practices-copy") is not None
    assert inspection.issues == ()


def test_invalid_working_tree_source_is_not_replaced_with_committed_content(
    current_specs_repository: Path,
) -> None:
    commit_all(current_specs_repository)
    source = current_specs_repository / "specs/07-Code 实践与测试规范.md"
    source.write_text(source.read_text(encoding="utf-8").replace("# Code 实践与测试规范", "# 已改变标题", 1))

    inspection = inspect_repository(current_specs_repository)

    assert inspection.document_passing_implemented_checks_by_key("code-engineering-practices") is None
    assert "specs/07-Code 实践与测试规范.md" in inspection.incomplete_scope
    assert any("YAML title 与 H1" in issue.summary for issue in inspection.issues)
    assert inspection.implemented_checks_complete is False
    assert inspection.document_passing_implemented_checks_by_key("web-presentation-interaction") is None
    assert len(inspection.active_documents_passing_implemented_checks) == 18
    assert len(inspection.projections) == 54


def test_invalid_foundation_stops_dependent_current_projection(current_specs_repository: Path) -> None:
    foundation = current_specs_repository / "specs/01-规范模型基础规范.md"
    foundation.write_text(foundation.read_text(encoding="utf-8").replace('status: "active"', 'status: "draft"', 1))

    inspection = inspect_repository(current_specs_repository)
    operations = inspect_operation_sources(inspection)

    assert inspection.active_documents_passing_implemented_checks == ()
    assert inspection.projections == ()
    assert inspection.implemented_checks_complete is False
    assert "specification-model-foundation" in inspection.incomplete_scope
    assert all(not Path(issue.location.path).is_absolute() for issue in inspection.issues)
    assert operations.candidate_declarations == ()
    assert operations.issues
    assert operations.incomplete_sources


def test_startup_validates_root_then_foundation_before_other_candidates(
    current_specs_repository: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_parse_identity = repository_module.parse_identity
    validated_paths: list[str] = []

    def record_validation(document):
        validated_paths.append(document.relative_path)
        return original_parse_identity(document)

    monkeypatch.setattr(repository_module, "parse_identity", record_validation)

    inspection = inspect_repository(current_specs_repository)

    assert validated_paths[:2] == [
        "specs/00-理念与构成.md",
        "specs/01-规范模型基础规范.md",
    ]
    assert len(validated_paths) == len(set(validated_paths)) == len(inspection.candidates)


def test_full_foundation_failure_stops_before_other_identity_validation(
    current_specs_repository: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    foundation = current_specs_repository / "specs/01-规范模型基础规范.md"
    foundation.write_text(
        foundation.read_text(encoding="utf-8").replace("# 规范模型基础规范", "# 已改变标题", 1),
        encoding="utf-8",
    )
    original_parse_identity = repository_module.parse_identity
    validated_paths: list[str] = []

    def record_validation(document):
        validated_paths.append(document.relative_path)
        return original_parse_identity(document)

    monkeypatch.setattr(repository_module, "parse_identity", record_validation)

    inspection = inspect_repository(current_specs_repository)

    assert validated_paths == [
        "specs/00-理念与构成.md",
        "specs/01-规范模型基础规范.md",
    ]
    assert tuple(document.key for document in inspection.parsed_documents) == ("ldvh-root",)
    assert inspection.active_documents_passing_implemented_checks == ()
    assert inspection.projections == ()
    assert "specification-model-foundation" in inspection.incomplete_scope


def test_foundation_relationship_failure_stops_before_other_identity_validation(
    current_specs_repository: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    foundation = current_specs_repository / "specs/01-规范模型基础规范.md"
    foundation.write_text(
        foundation.read_text(encoding="utf-8").replace(
            '    - "ldvh-root"\n  authorized_attachments:',
            '    - "missing-root"\n  authorized_attachments:',
            1,
        ),
        encoding="utf-8",
    )
    original_parse_identity = repository_module.parse_identity
    validated_paths: list[str] = []

    def record_validation(document):
        validated_paths.append(document.relative_path)
        return original_parse_identity(document)

    monkeypatch.setattr(repository_module, "parse_identity", record_validation)

    inspection = inspect_repository(current_specs_repository)

    assert validated_paths == [
        "specs/00-理念与构成.md",
        "specs/01-规范模型基础规范.md",
        "specs/attachments/01.Att.01-LDVH双语术语表.md",
    ]
    assert inspection.active_documents_passing_implemented_checks == ()
    assert inspection.projections == ()
    assert "specification-model-foundation" in inspection.incomplete_scope
    assert len([issue for issue in inspection.issues if "missing-root" in issue.summary]) == 1


def test_partial_discovery_retains_reproducible_range_passing_implemented_checks(
    current_specs_repository: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    complete = repository_module.discover_candidates(current_specs_repository)
    missing_path = "specs/attachments/04.Att.01-Helper CLI 请求与响应字段表.md"
    assert complete.issues == ()
    assert any(candidate.relative_path == missing_path for candidate in complete.candidates)
    local_issue = Issue(
        summary="Cannot reproduce one local attachment candidate",
        location=SourceLocation(missing_path),
        affected=("helper-cli-request-response-fields",),
    )
    partial = DiscoveryResult(
        repository_root=complete.repository_root,
        candidates=tuple(candidate for candidate in complete.candidates if candidate.relative_path != missing_path),
        issues=(local_issue,),
        complete=False,
    )
    monkeypatch.setattr(repository_module, "discover_candidates", lambda _: partial)

    first = inspect_repository(current_specs_repository)
    second = inspect_repository(current_specs_repository)

    assert first.implemented_checks_complete is False
    assert first.document_passing_implemented_checks_by_key("ldvh-root") is not None
    assert first.document_passing_implemented_checks_by_key("helper-cli-request-response-fields") is None
    assert first.active_documents_passing_implemented_checks
    assert first.projections
    assert "helper-cli-request-response-fields" in first.incomplete_scope
    assert local_issue in first.issues
    assert tuple((item.layer, item.key, item.path) for item in first.projections) == tuple(
        (item.layer, item.key, item.path) for item in second.projections
    )


def test_file_replaced_by_external_symlink_after_discovery_is_not_read(
    current_specs_repository: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = current_specs_repository / "specs/07-Code 实践与测试规范.md"
    external = tmp_path / "external.md"
    external.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    original_parse = repository_module.parse_markdown
    swapped = False

    def swap_then_parse(path: Path, relative_path: str):
        nonlocal swapped
        if not swapped and relative_path == "specs/07-Code 实践与测试规范.md":
            target.unlink()
            target.symlink_to(external)
            swapped = True
        return original_parse(path, relative_path)

    monkeypatch.setattr(repository_module, "parse_markdown", swap_then_parse)

    inspection = inspect_repository(current_specs_repository)

    assert swapped is True
    assert inspection.document_passing_implemented_checks_by_key("code-engineering-practices") is None
    assert "specs/07-Code 实践与测试规范.md" in inspection.incomplete_scope
    assert any(
        issue.summary == "Markdown source could not be read safely from its current path" for issue in inspection.issues
    )
