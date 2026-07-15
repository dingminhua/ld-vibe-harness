from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from ldvh.helper.operations.specification_content import (
    SpecificationContentSelectionError,
    read_specification_content,
)
from ldvh.helper.operations.specification_content_request import (
    SpecificationContentRequest,
    SpecificationContentSelection,
)
from ldvh.specs.markdown import Heading
from ldvh.specs.repository import UNCHECKED_CONDITIONS, inspect_repository


def _request(
    disclosure: str,
    *selections: SpecificationContentSelection,
) -> SpecificationContentRequest:
    assert disclosure in {"L3", "L4"}
    return SpecificationContentRequest(selections=selections, disclosure=disclosure)  # type: ignore[arg-type]


def _read_raw(path: Path) -> str:
    with path.open("r", encoding="utf-8", newline="") as source:
        return source.read()


def test_reads_exact_l4_source_with_fixed_traceability_fields(current_specs_repository: Path) -> None:
    repository = inspect_repository(current_specs_repository)
    selection = SpecificationContentSelection("specification-model-foundation", None)

    result = read_specification_content(
        repository,
        request=_request("L4", selection),
    )

    assert result.suggested_outcome == "ok"
    assert result.requested_scope == result.completed_scope == (selection.as_scope(),)
    assert result.not_completed_scope == ()
    assert result.items is not None and len(result.items) == 1
    item = result.items[0]
    assert item["selection"] == selection.as_scope()
    assert item["requested_disclosure"] == item["actual_disclosure"] == "L4"
    parts = item["parts"]
    assert isinstance(parts, list) and len(parts) == 1
    part = parts[0]
    assert isinstance(part, dict)
    expected = _read_raw(current_specs_repository / "specs/01-规范模型基础规范.md")
    assert part["content"] == expected
    assert part["start_line"] == 1
    assert part["end_line"] == len(expected.splitlines())
    source = part["source"]
    document = repository.document_passing_implemented_checks_by_key("specification-model-foundation")
    assert document is not None and document.markdown.observed_at is not None
    assert source == {
        "kind": "rule",
        "locator": f"specs/01-规范模型基础规范.md#L1-L{len(expected.splitlines())}",
        "observed_at": document.markdown.observed_at,
        "details": {
            "responsibility_key": "specification-model-foundation",
            "path": "specs/01-规范模型基础规范.md",
            "heading_path": None,
            "start_line": 1,
            "end_line": len(expected.splitlines()),
            "rule_source_view": "working_tree",
            "git_worktree_root": current_specs_repository.resolve().as_posix(),
        },
    }
    assert result.sources == (source,)
    assert result.disclosure_parts == (
        {"level": "L4", "source_refs": [source], "reason": "请求 L4，按契约返回完整来源"},
    )
    assert len(result.verification) == 1
    assert result.verification[0]["status"] == "passed"
    assert len(result.gaps) == 1


def test_diagnostic_keeps_semantic_qualification_in_gaps(
    current_specs_repository: Path,
) -> None:
    repository = inspect_repository(current_specs_repository)
    selection = SpecificationContentSelection("specification-model-foundation", None)

    result = read_specification_content(
        repository,
        request=_request("L4", selection),
        response_profile="diagnostic",
    )

    assert len(result.verification) == 1
    verification = result.verification[0]
    assert verification["status"] == "passed"
    assert verification["scope"] == [selection.as_scope()]
    assert len(result.gaps) == len(UNCHECKED_CONDITIONS)
    for condition in UNCHECKED_CONDITIONS:
        matching_gaps = [gap for gap in result.gaps if condition in gap["summary"]]
        assert len(matching_gaps) == 1
        assert matching_gaps[0]["scope"] == [selection.as_scope()]
        assert matching_gaps[0]["source_refs"]
        assert condition not in verification["check"]
    assert all(
        unsupported_claim not in verification["check"]
        for unsupported_claim in (
            "规则语义完整",
            "规则适用",
            "Human Gate",
            "Stop Conditions",
            "完整取得当前规则源资格",
        )
    )


def test_attachment_l4_includes_attachment_then_unique_parent_without_basis_recursion(
    current_specs_repository: Path,
) -> None:
    repository = inspect_repository(current_specs_repository)
    selection = SpecificationContentSelection("ldvh-bilingual-terminology", None)

    result = read_specification_content(
        repository,
        request=_request("L4", selection),
    )

    assert result.items is not None
    item = result.items[0]
    parts = item["parts"]
    assert isinstance(parts, list)
    assert [part["source"]["details"]["responsibility_key"] for part in parts] == [
        "ldvh-bilingual-terminology",
        "specification-model-foundation",
    ]
    assert [part["source"]["details"]["path"] for part in parts] == [
        "specs/attachments/01.Att.01-LDVH双语术语表.md",
        "specs/01-规范模型基础规范.md",
    ]
    assert "ldvh-root" not in {part["source"]["details"]["responsibility_key"] for part in parts}
    assert len(result.disclosure_parts) == 2
    assert [part["source_refs"][0] for part in result.disclosure_parts] == [part["source"] for part in parts]


def test_valid_l3_h3_returns_exact_mechanical_slice(current_specs_repository: Path) -> None:
    repository = inspect_repository(current_specs_repository)
    selection = SpecificationContentSelection(
        "specification-model-foundation",
        ("5. 基础术语", "5.1 规范文档（Specification）"),
    )

    result = read_specification_content(
        repository,
        request=_request("L3", selection),
    )

    assert result.suggested_outcome == "ok"
    assert result.items is not None
    item = result.items[0]
    assert item["requested_disclosure"] == "L3"
    assert item["actual_disclosure"] == "L3"
    assert [part["heading_path"] for part in item["parts"]] == [
        ["5. 基础术语"],
        ["5. 基础术语", "5.1 规范文档（Specification）"],
    ]
    assert item["parts"][1]["content"].startswith("### 5.1 规范文档（Specification）")
    assert result.disclosure_parts[0]["level"] == "L3"
    assert "请求 L3" in result.disclosure_parts[0]["reason"]


@pytest.mark.parametrize(
    "selection",
    (
        SpecificationContentSelection("unknown-key", None),
        SpecificationContentSelection("specification-model-foundation", ("Unknown H2",)),
        SpecificationContentSelection(
            "specification-model-foundation",
            ("5. 基础术语", "Unknown H3"),
        ),
    ),
)
def test_clean_source_rejects_unknown_exact_selection_as_invalid_request_candidate(
    current_specs_repository: Path,
    selection: SpecificationContentSelection,
) -> None:
    repository = inspect_repository(current_specs_repository)
    disclosure = "L4" if selection.heading_path is None else "L3"

    with pytest.raises(SpecificationContentSelectionError):
        read_specification_content(
            repository,
            request=_request(disclosure, selection),
        )


@pytest.mark.parametrize(
    ("heading_path", "duplicate"),
    (
        (("5. 基础术语",), Heading(2, "5. 基础术语", 80)),
        (
            ("5. 基础术语", "5.1 规范文档（Specification）"),
            Heading(3, "5.1 规范文档（Specification）", 82),
        ),
    ),
)
def test_duplicate_exact_heading_is_invalid_after_the_source_is_formed(
    current_specs_repository: Path,
    heading_path: tuple[str, ...],
    duplicate: Heading,
) -> None:
    repository = inspect_repository(current_specs_repository)
    document = repository.document_passing_implemented_checks_by_key("specification-model-foundation")
    assert document is not None
    changed_document = replace(
        document,
        markdown=replace(document.markdown, headings=(*document.markdown.headings, duplicate)),
    )
    changed_repository = replace(
        repository,
        active_documents_passing_implemented_checks=tuple(
            changed_document if candidate.key == changed_document.key else candidate
            for candidate in repository.active_documents_passing_implemented_checks
        ),
    )
    selection = SpecificationContentSelection("specification-model-foundation", heading_path)

    with pytest.raises(SpecificationContentSelectionError) as raised:
        read_specification_content(changed_repository, request=_request("L3", selection))

    assert "无法精确唯一匹配" in raised.value.problems[0]


def test_parsed_but_inactive_source_makes_the_exact_selection_invalid(
    current_specs_repository: Path,
) -> None:
    web = current_specs_repository / "specs/08-Web 呈现与交互规范.md"
    web.write_text(web.read_text(encoding="utf-8").replace('status: "active"', 'status: "draft"', 1), encoding="utf-8")
    repository = inspect_repository(current_specs_repository)
    selection = SpecificationContentSelection("web-presentation-interaction", None)

    with pytest.raises(SpecificationContentSelectionError) as raised:
        read_specification_content(
            repository,
            request=_request("L4", selection),
        )

    assert "active 载体集合中精确匹配" in raised.value.problems[0]


def test_active_source_blocked_by_relationship_stop_can_form_partial(
    current_specs_repository: Path,
) -> None:
    web = current_specs_repository / "specs/08-Web 呈现与交互规范.md"
    web.write_text(
        web.read_text(encoding="utf-8").replace('    - "ldvh-root"', '    - "missing-basis"', 1),
        encoding="utf-8",
    )
    repository = inspect_repository(current_specs_repository)
    valid = SpecificationContentSelection("ldvh-root", None)
    rejected = SpecificationContentSelection("web-presentation-interaction", None)

    result = read_specification_content(
        repository,
        request=_request("L4", valid, rejected),
    )

    assert result.suggested_outcome == "partial"
    assert result.completed_scope == (valid.as_scope(),)
    assert result.not_completed_scope == (rejected.as_scope(),)
    assert any("Stop Conditions" in gap["summary"] for gap in result.gaps)


def test_duplicate_parsed_key_is_a_source_identity_error(current_specs_repository: Path) -> None:
    web = current_specs_repository / "specs/08-Web 呈现与交互规范.md"
    web.write_text(
        web.read_text(encoding="utf-8").replace(
            'spec_key: "web-presentation-interaction"',
            'spec_key: "code-engineering-practices"',
            1,
        ),
        encoding="utf-8",
    )
    repository = inspect_repository(current_specs_repository)
    selection = SpecificationContentSelection("code-engineering-practices", None)

    result = read_specification_content(
        repository,
        request=_request("L4", selection),
    )

    assert result.suggested_outcome == "error"
    assert result.items is None
    assert result.not_completed_scope == (selection.as_scope(),)
    assert any("重复职责标识符" in gap["summary"] for gap in result.gaps)


def test_zero_completed_aggregates_error_before_rejected(current_specs_repository: Path) -> None:
    web = current_specs_repository / "specs/08-Web 呈现与交互规范.md"
    web_text = web.read_text(encoding="utf-8")
    web.write_text(web_text.replace('    - "ldvh-root"', '    - "missing-basis"', 1), encoding="utf-8")
    code_copy = current_specs_repository / "specs/09-Code-Duplicate.md"
    code_source = (current_specs_repository / "specs/07-Code 实践与测试规范.md").read_text(encoding="utf-8")
    code_copy.write_text(
        code_source.replace('spec_id: "07"', 'spec_id: "09"', 1)
        .replace('canonical_path: "specs/07-Code 实践与测试规范.md"', 'canonical_path: "specs/09-Code-Duplicate.md"', 1)
        .replace("# Code 实践与测试规范", "# Code-Duplicate", 1)
        .replace('title: "Code 实践与测试规范"', 'title: "Code-Duplicate"', 1),
        encoding="utf-8",
    )
    repository = inspect_repository(current_specs_repository)
    duplicate = SpecificationContentSelection("code-engineering-practices", None)
    rejected = SpecificationContentSelection("web-presentation-interaction", None)

    result = read_specification_content(repository, request=_request("L4", duplicate, rejected))

    assert result.completed_scope == ()
    assert result.suggested_outcome == "error"
    assert result.not_completed_scope == (duplicate.as_scope(), rejected.as_scope())
    assert any("重复职责标识符" in gap["summary"] for gap in result.gaps)
    assert any("Stop Conditions" in gap["summary"] for gap in result.gaps)


def test_incomplete_source_does_not_relabel_an_unresolved_key_as_invalid_request(
    current_specs_repository: Path,
) -> None:
    web = current_specs_repository / "specs/08-Web 呈现与交互规范.md"
    web.write_text(web.read_text(encoding="utf-8").replace("# Web 呈现与交互规范", "# Broken", 1), encoding="utf-8")
    repository = inspect_repository(current_specs_repository)
    selection = SpecificationContentSelection("possibly-hidden-by-broken-source", None)

    result = read_specification_content(
        repository,
        request=_request("L4", selection),
    )

    assert result.suggested_outcome == "error"
    assert result.items is None
    assert result.not_completed_scope == (selection.as_scope(),)
    assert result.gaps
    assert result.diagnostics


def test_reader_uses_the_same_inspection_snapshot_without_reopening_source(current_specs_repository: Path) -> None:
    repository = inspect_repository(current_specs_repository)
    selection = SpecificationContentSelection("ldvh-root", None)
    inspected_text = repository.document_passing_implemented_checks_by_key("ldvh-root")
    assert inspected_text is not None and inspected_text.markdown.observed_at is not None
    inspected_at = inspected_text.markdown.observed_at
    source = current_specs_repository / "specs/00-理念与构成.md"
    source.write_text(source.read_text(encoding="utf-8") + "\nAFTER_INSPECTION\n", encoding="utf-8")

    result = read_specification_content(
        repository,
        request=_request("L4", selection),
    )

    assert result.items is not None
    content = result.items[0]["parts"][0]["content"]
    assert content == inspected_text.markdown.raw_text
    assert "AFTER_INSPECTION" not in content
    assert result.items[0]["parts"][0]["source"]["observed_at"] == inspected_at
