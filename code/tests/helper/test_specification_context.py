from __future__ import annotations

import hashlib
from dataclasses import replace
from pathlib import Path

import pytest

from ldvh.helper.operations.specification_content import read_specification_content
from ldvh.helper.operations.specification_content_request import (
    SpecificationContentRequest,
    SpecificationContentSelection,
)
from ldvh.helper.operations.specification_context import (
    SpecificationContextSelectionError,
    read_specification_context,
)
from ldvh.helper.operations.specification_context_request import (
    SpecificationContextRequest,
    SpecificationContextSelection,
)
from ldvh.specs.repository import UNCHECKED_CONDITIONS, inspect_repository


def _request(*contexts: SpecificationContextSelection) -> SpecificationContextRequest:
    return SpecificationContextRequest(contexts)


def _digest(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def test_regular_context_returns_complete_companions_outline_hashes_and_exact_primary(
    current_specs_repository: Path,
) -> None:
    repository = inspect_repository(current_specs_repository)
    primary = ("5. 基础术语", "5.1 规范文档（Specification）")
    selection = SpecificationContextSelection("specification-model-foundation", (primary,))

    result = read_specification_context(repository, request=_request(selection))
    baseline = read_specification_content(
        repository,
        request=SpecificationContentRequest(
            (SpecificationContentSelection("specification-model-foundation", primary),),
            "L3",
        ),
    )

    assert result.suggested_outcome == "ok"
    assert result.requested_scope == result.completed_scope == (selection.as_scope(),)
    assert result.not_completed_scope == ()
    assert result.items is not None and len(result.items) == 1
    item = result.items[0]
    assert set(item) == {
        "responsibility_key",
        "kind",
        "id",
        "title",
        "path",
        "overview_scope",
        "heading_outline",
        "primary_heading_paths",
        "parts",
        "guard_coverage",
        "source_content_sha256",
    }
    assert item["kind"] == "spec"
    assert item["primary_heading_paths"] == [list(primary)]
    assert item["guard_coverage"] == {
        "applicability_scope": "returned",
        "verification": "returned",
        "human_gate": "returned",
        "stop_conditions": "returned",
    }
    document = repository.document_passing_implemented_checks_by_key("specification-model-foundation")
    assert document is not None
    assert item["overview_scope"] == document.scope
    assert item["source_content_sha256"] == _digest(document.markdown.raw_text)

    parts = item["parts"]
    assert isinstance(parts, list)
    assert [part["start_line"] for part in parts] == sorted(part["start_line"] for part in parts)
    reasons = [part["inclusion_reason"] for part in parts]
    assert set(reasons) == {
        "explicit-primary",
        "applicability-scope-companion",
        "verification-companion",
        "human-gate-companion",
        "stop-conditions-companion",
    }
    for part in parts:
        assert part["content_sha256"] == _digest(part["content"])

    assert baseline.items is not None
    baseline_parts = baseline.items[0]["parts"]
    explicit = [part for part in parts if part["inclusion_reason"] == "explicit-primary"]
    assert [
        (part["content"], part["start_line"], part["end_line"], part["source"])
        for part in explicit
    ] == [
        (part["content"], part["start_line"], part["end_line"], part["source"])
        for part in baseline_parts
    ]

    outline = item["heading_outline"]
    assert isinstance(outline, list) and outline
    assert outline[0]["heading_path"] == ["1. 价值判断"]
    assert outline[0]["start_line"] < outline[0]["end_line"]
    assert {entry["structural_role"] for entry in outline} >= {
        "applicability_scope",
        "verification",
        "human_gate",
        "stop_conditions",
        None,
    }
    assert len(result.disclosure_parts) == len(parts) + 1
    assert result.disclosure_parts[0]["level"] == "L1"
    assert all(part["level"] == "L3" for part in result.disclosure_parts[1:])
    assert len(result.gaps) == 1
    assert result.gaps[0]["code"] == "qualification_unproven"
    assert result.gaps[0]["member_count"] == len(UNCHECKED_CONDITIONS)
    assert len(result.verification) == 1


def test_root_empty_primary_returns_three_companions_and_no_applicability_part(
    current_specs_repository: Path,
) -> None:
    repository = inspect_repository(current_specs_repository)
    selection = SpecificationContextSelection("ldvh-root", ())

    result = read_specification_context(repository, request=_request(selection))

    assert result.items is not None
    item = result.items[0]
    assert item["kind"] == "root"
    assert item["primary_heading_paths"] == []
    assert item["guard_coverage"]["applicability_scope"] == "not_applicable"
    assert [part["inclusion_reason"] for part in item["parts"]] == [
        "verification-companion",
        "human-gate-companion",
        "stop-conditions-companion",
    ]


def test_root_free_body_heading_named_applicability_scope_is_not_a_structural_role(
    current_specs_repository: Path,
) -> None:
    repository = inspect_repository(current_specs_repository)
    root = repository.document_passing_implemented_checks_by_key("ldvh-root")
    assert root is not None
    changed_heading = next(heading for heading in root.markdown.headings if heading.title.startswith("7. "))
    changed_root = replace(
        root,
        markdown=replace(
            root.markdown,
            headings=tuple(
                replace(heading, title="7. 适用范围") if heading is changed_heading else heading
                for heading in root.markdown.headings
            ),
        ),
    )
    changed = replace(
        repository,
        active_documents_passing_implemented_checks=tuple(
            changed_root if document.key == root.key else document
            for document in repository.active_documents_passing_implemented_checks
        ),
    )

    result = read_specification_context(
        changed,
        request=_request(SpecificationContextSelection("ldvh-root", ())),
    )

    assert result.items is not None
    matching = [
        heading
        for heading in result.items[0]["heading_outline"]
        if heading["heading_path"] == ["7. 适用范围"]
    ]
    assert len(matching) == 1
    assert matching[0]["structural_role"] is None


def test_primary_equal_to_companion_is_returned_once_with_companion_reason(
    current_specs_repository: Path,
) -> None:
    repository = inspect_repository(current_specs_repository)
    selection = SpecificationContextSelection("ldvh-root", (("9. 验证要求",),))

    result = read_specification_context(repository, request=_request(selection))

    assert result.items is not None
    matching = [part for part in result.items[0]["parts"] if part["heading_path"] == ["9. 验证要求"]]
    assert len(matching) == 1
    assert matching[0]["inclusion_reason"] == "verification-companion"


@pytest.mark.parametrize(
    "selection",
    (
        SpecificationContextSelection("ldvh-bilingual-terminology", ()),
        SpecificationContextSelection("unknown-key", ()),
        SpecificationContextSelection("ldvh-root", (("Unknown H2",),)),
    ),
)
def test_attachment_unknown_key_and_unknown_heading_are_invalid_exact_selections(
    current_specs_repository: Path,
    selection: SpecificationContextSelection,
) -> None:
    repository = inspect_repository(current_specs_repository)

    with pytest.raises(SpecificationContextSelectionError):
        read_specification_context(repository, request=_request(selection))


def test_unqualified_attachment_identity_is_still_invalid_input(current_specs_repository: Path) -> None:
    repository = inspect_repository(current_specs_repository)
    attachment = next(document for document in repository.parsed_documents if document.kind == "attachment")
    changed = replace(
        repository,
        active_documents_passing_implemented_checks=tuple(
            document
            for document in repository.active_documents_passing_implemented_checks
            if document.key != attachment.key
        ),
    )

    with pytest.raises(SpecificationContextSelectionError) as raised:
        read_specification_context(
            changed,
            request=_request(SpecificationContextSelection(attachment.key, ())),
        )

    assert "是附件" in raised.value.problems[0]


def test_broken_companion_keeps_context_atomic_and_allows_another_context_to_complete(
    current_specs_repository: Path,
) -> None:
    web = current_specs_repository / "specs/08-Web 呈现与交互规范.md"
    web.write_text(web.read_text(encoding="utf-8").replace(". Stop Conditions", ". Stop Boundary"), encoding="utf-8")
    repository = inspect_repository(current_specs_repository)
    good = SpecificationContextSelection("ldvh-root", ())
    broken = SpecificationContextSelection("web-presentation-interaction", ())

    result = read_specification_context(repository, request=_request(good, broken))

    assert result.suggested_outcome == "partial"
    assert result.completed_scope == (good.as_scope(),)
    assert result.not_completed_scope == (broken.as_scope(),)
    assert result.items is not None and [item["responsibility_key"] for item in result.items] == ["ldvh-root"]
    assert result.gaps
    assert any("Stop Conditions" in diagnostic["summary"] for diagnostic in result.diagnostics)


def test_reader_uses_inspection_snapshot_for_content_and_hash(current_specs_repository: Path) -> None:
    repository = inspect_repository(current_specs_repository)
    document = repository.document_passing_implemented_checks_by_key("ldvh-root")
    assert document is not None
    expected_hash = _digest(document.markdown.raw_text)
    source = current_specs_repository / document.canonical_path
    source.write_text(source.read_text(encoding="utf-8") + "\nAFTER_INSPECTION\n", encoding="utf-8")

    result = read_specification_context(
        repository,
        request=_request(SpecificationContextSelection("ldvh-root", ())),
    )

    assert result.items is not None
    item = result.items[0]
    assert item["source_content_sha256"] == expected_hash
    assert all("AFTER_INSPECTION" not in part["content"] for part in item["parts"])


def test_duplicate_passing_identity_is_reported_as_source_error(current_specs_repository: Path) -> None:
    repository = inspect_repository(current_specs_repository)
    root = repository.document_passing_implemented_checks_by_key("ldvh-root")
    assert root is not None
    changed = replace(repository, active_documents_passing_implemented_checks=(root, root))

    result = read_specification_context(
        changed,
        request=_request(SpecificationContextSelection("ldvh-root", ())),
    )

    assert result.suggested_outcome == "error"
    assert result.items is None
    assert result.not_completed_scope == ({"responsibility_key": "ldvh-root", "primary_heading_paths": []},)


def test_missing_companion_after_qualification_is_context_error_not_request_error(
    current_specs_repository: Path,
) -> None:
    repository = inspect_repository(current_specs_repository)
    root = repository.document_passing_implemented_checks_by_key("ldvh-root")
    regular = repository.document_passing_implemented_checks_by_key("specification-model-foundation")
    assert root is not None and regular is not None
    broken_root = replace(
        root,
        markdown=replace(
            root.markdown,
            headings=tuple(heading for heading in root.markdown.headings if heading.title != "11. Stop Conditions"),
        ),
    )
    changed = replace(
        repository,
        active_documents_passing_implemented_checks=tuple(
            broken_root if document.key == "ldvh-root" else document
            for document in repository.active_documents_passing_implemented_checks
        ),
    )
    good = SpecificationContextSelection(regular.key, ())
    broken = SpecificationContextSelection(root.key, ())

    result = read_specification_context(changed, request=_request(good, broken))

    assert result.suggested_outcome == "partial"
    assert result.completed_scope == (good.as_scope(),)
    assert result.not_completed_scope == (broken.as_scope(),)
    assert any("Stop Conditions" in gap["summary"] for gap in result.gaps)


def test_missing_snapshot_observation_is_atomic_per_context(current_specs_repository: Path) -> None:
    repository = inspect_repository(current_specs_repository)
    regular = repository.document_passing_implemented_checks_by_key("specification-model-foundation")
    assert regular is not None
    broken_regular = replace(regular, markdown=replace(regular.markdown, observed_at=None))
    changed = replace(
        repository,
        active_documents_passing_implemented_checks=tuple(
            broken_regular if document.key == regular.key else document
            for document in repository.active_documents_passing_implemented_checks
        ),
    )
    good = SpecificationContextSelection("ldvh-root", ())
    broken = SpecificationContextSelection(regular.key, ())

    result = read_specification_context(changed, request=_request(good, broken))

    assert result.suggested_outcome == "partial"
    assert result.completed_scope == (good.as_scope(),)
    assert result.not_completed_scope == (broken.as_scope(),)
    assert result.items is not None and [item["responsibility_key"] for item in result.items] == ["ldvh-root"]
    assert any("同一规则源快照" in gap["summary"] for gap in result.gaps)
