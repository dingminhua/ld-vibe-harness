from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from types import MappingProxyType

from ldvh.diagnostics import Issue, SourceLocation
from ldvh.helper.operations.specification_candidates import read_specification_candidates
from ldvh.specs.repository import inspect_repository


def test_reads_l0_without_reopening_the_working_tree(current_specs_repository: Path) -> None:
    inspection = inspect_repository(current_specs_repository)
    expected = inspection.document_passing_implemented_checks_by_key("specification-model-foundation")
    assert expected is not None
    source = current_specs_repository / expected.canonical_path
    source.unlink()

    result = read_specification_candidates(
        inspection,
        responsibility_keys=("specification-model-foundation",),
        disclosure="L0",
    )

    assert result.suggested_outcome == "ok"
    assert result.requested_scope == result.completed_scope == ("specification-model-foundation",)
    assert result.not_completed_scope == ()
    assert result.items == (
        {
            "kind": "spec",
            "key": "specification-model-foundation",
            "id": "01",
            "title": "规范模型基础规范",
            "status": "active",
            "path": "specs/01-规范模型基础规范.md",
            "overview": None,
            "relationships": None,
        },
    )
    assert [part["level"] for part in result.disclosure_parts] == ["L0"]
    assert result.verification[0]["status"] == "passed"
    assert len(result.gaps) == len(inspection.unchecked_conditions)


def test_l2_is_cumulative_and_exact_selection_keeps_request_order(current_specs_repository: Path) -> None:
    inspection = inspect_repository(current_specs_repository)

    result = read_specification_candidates(
        inspection,
        responsibility_keys=("ldvh-bilingual-terminology", "ldvh-root"),
        disclosure="L2",
    )

    assert result.suggested_outcome == "ok"
    assert [item["key"] for item in result.items or ()] == ["ldvh-bilingual-terminology", "ldvh-root"]
    attachment = (result.items or ())[0]
    assert attachment["overview"] == {
        "positioning": "登记 LDVH 跨规范核心术语的中英文规范名称、缩写、机器表示和唯一定义来源，不复制或改写来源定义",
        "scope": None,
    }
    assert attachment["relationships"] == {
        "basis": [],
        "parent_spec": {"key": "specification-model-foundation", "path": "specs/01-规范模型基础规范.md"},
        "relation": None,
        "authorized_attachments": [],
        "supersedes": [],
    }
    assert [part["level"] for part in result.disclosure_parts] == ["L0", "L1", "L2"]


def test_empty_selection_is_deterministic_by_path_then_key(current_specs_repository: Path) -> None:
    inspection = inspect_repository(current_specs_repository)

    result = read_specification_candidates(inspection, responsibility_keys=(), disclosure="L1")

    items = result.items or ()
    expected = sorted(
        inspection.active_documents_passing_implemented_checks,
        key=lambda document: (document.canonical_path, document.key),
    )
    assert [item["key"] for item in items] == [document.key for document in expected]
    assert result.requested_scope == result.completed_scope
    assert result.suggested_outcome == "ok"


def test_mixed_exact_selection_is_partial_and_unknown_key_does_not_fuzzy_match(
    current_specs_repository: Path,
) -> None:
    inspection = inspect_repository(current_specs_repository)

    result = read_specification_candidates(
        inspection,
        responsibility_keys=("ldvh-root", "ldvh-roo"),
        disclosure="L0",
    )

    assert result.suggested_outcome == "partial"
    assert result.completed_scope == ("ldvh-root",)
    assert result.not_completed_scope == ("ldvh-roo",)
    assert [item["key"] for item in result.items or ()] == ["ldvh-root"]
    assert any("未精确匹配" in gap["summary"] for gap in result.gaps)


def test_only_unknown_selection_is_unavailable_with_null_items(current_specs_repository: Path) -> None:
    inspection = inspect_repository(current_specs_repository)

    result = read_specification_candidates(
        inspection,
        responsibility_keys=("unknown-key",),
        disclosure="L0",
    )

    assert result.suggested_outcome == "unavailable"
    assert result.items is None
    assert result.completed_scope == ()
    assert result.not_completed_scope == ("unknown-key",)
    assert result.sources == ()
    assert result.disclosure_parts == ()
    assert result.verification == ()


def test_issue_affecting_one_key_does_not_discard_an_independent_completed_key(
    current_specs_repository: Path,
) -> None:
    inspection = inspect_repository(current_specs_repository)
    broken_key = "code-engineering-practices"
    issue = Issue(
        "Code 规范当前无法形成投影",
        SourceLocation("specs/07-Code 实践与测试规范.md", 5),
        affected=(broken_key,),
    )
    partial = replace(
        inspection,
        active_documents_passing_implemented_checks=tuple(
            document
            for document in inspection.active_documents_passing_implemented_checks
            if document.key != broken_key
        ),
        projections=tuple(projection for projection in inspection.projections if projection.key != broken_key),
        issues=(issue,),
        incomplete_scope=(broken_key,),
        implemented_checks_complete=False,
    )

    result = read_specification_candidates(
        partial,
        responsibility_keys=("ldvh-root", broken_key),
        disclosure="L0",
    )

    assert result.suggested_outcome == "partial"
    assert result.completed_scope == ("ldvh-root",)
    assert result.not_completed_scope == (broken_key,)
    assert [diagnostic["summary"] for diagnostic in result.diagnostics] == [issue.summary]


def test_empty_selection_exposes_failed_candidates_without_expanding_its_scope(
    current_specs_repository: Path,
) -> None:
    inspection = inspect_repository(current_specs_repository)
    broken_key = "code-engineering-practices"
    issue = Issue(
        "Code 规范当前无法形成投影",
        SourceLocation("specs/07-Code 实践与测试规范.md", 5),
        affected=(broken_key,),
    )
    partial = replace(
        inspection,
        active_documents_passing_implemented_checks=tuple(
            document
            for document in inspection.active_documents_passing_implemented_checks
            if document.key != broken_key
        ),
        projections=tuple(projection for projection in inspection.projections if projection.key != broken_key),
        issues=(issue,),
        incomplete_scope=(broken_key,),
        implemented_checks_complete=False,
    )

    result = read_specification_candidates(partial, responsibility_keys=(), disclosure="L0")

    assert result.suggested_outcome == "ok"
    assert broken_key not in result.requested_scope
    assert result.requested_scope == result.completed_scope
    assert result.not_completed_scope == ()
    assert any(gap["scope"] == [broken_key] for gap in result.gaps)
    assert [diagnostic["summary"] for diagnostic in result.diagnostics] == [issue.summary]


def test_unrelated_repository_issue_is_not_attached_to_an_exact_successful_selection(
    current_specs_repository: Path,
) -> None:
    inspection = inspect_repository(current_specs_repository)
    unrelated = Issue("Unrelated candidate failed", SourceLocation("specs/99-Broken.md"), affected=("broken",))
    partial = replace(
        inspection,
        issues=(unrelated,),
        incomplete_scope=("broken",),
        implemented_checks_complete=False,
    )

    result = read_specification_candidates(partial, responsibility_keys=("ldvh-root",), disclosure="L0")

    assert result.suggested_outcome == "ok"
    assert result.completed_scope == ("ldvh-root",)
    assert result.diagnostics == ()
    assert all(gap["scope"] != ["broken"] for gap in result.gaps)


def test_incomplete_relationship_projection_moves_only_that_key_to_not_completed(
    current_specs_repository: Path,
) -> None:
    inspection = inspect_repository(current_specs_repository)
    key = "specification-model-foundation"
    projections = []
    for projection in inspection.projections:
        if projection.key == key and projection.layer == "L2":
            broken_content = dict(projection.content)
            broken_content["basis"] = ({"key": "ldvh-root"},)
            projection = replace(projection, content=MappingProxyType(broken_content))
        projections.append(projection)
    broken = replace(inspection, projections=tuple(projections))

    result = read_specification_candidates(broken, responsibility_keys=(key,), disclosure="L2")

    assert result.suggested_outcome == "unavailable"
    assert result.items is None
    assert result.not_completed_scope == (key,)
    assert any("关系目标字段不完整" in diagnostic["summary"] for diagnostic in result.diagnostics)


def test_unchecked_qualification_and_basis_review_gaps_do_not_downgrade_success(
    current_specs_repository: Path,
) -> None:
    inspection = inspect_repository(current_specs_repository)
    overlap = inspection.basis_reachability_overlaps[0]

    result = read_specification_candidates(
        inspection,
        responsibility_keys=(overlap.spec_key,),
        disclosure="L0",
    )

    assert result.suggested_outcome == "ok"
    matching_overlaps = [item for item in inspection.basis_reachability_overlaps if item.spec_key == overlap.spec_key]
    assert len(result.gaps) == len(inspection.unchecked_conditions) + len(matching_overlaps)
    assert any("语义复核" in gap["summary"] for gap in result.gaps)
    assert "整体结果" in result.verification[0]["check"]
