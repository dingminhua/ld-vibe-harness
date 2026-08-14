from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from ldvh.specs.action_templates import ActionTemplateDeclaration, inspect_action_template_sources
from ldvh.specs.identity import FormalDocument
from ldvh.specs.markdown import parse_markdown
from ldvh.specs.repository import RepositoryInspection

DECLARATION_HEADERS = "| template_key | summary | activation_hint | definition_ref |\n|---|---|---|---|\n"


def _source(
    tmp_path: Path,
    key: str,
    *,
    template_key: str = "git-commit",
    definition_level: int = 2,
    definition_title: str = "1. Template definition",
    definition_ref: str | None = None,
    activation_hint: str = "Use when a local commit is explicitly authorized; do not use for inspection only.",
    declaration_heading: str = "行动模板声明",
    content_before_table: str = "",
    table_headers: str = DECLARATION_HEADERS,
    row_override: str | None = None,
    status: str = "active",
    kind: str = "spec",
) -> FormalDocument:
    path = tmp_path / f"specs/{key}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    reference = definition_ref if definition_ref is not None else f"{key}::{definition_title}"
    row = row_override
    if row is None:
        row = f"| `{template_key}` | Commit changes | {activation_hint} | `{reference}` |\n"
    marks = "#" * definition_level
    if definition_level == 2:
        definition = f"{marks} {definition_title}\n\nTemplate body.\n\n### {declaration_heading}\n\n"
    else:
        definition = f"## 1. Templates\n\n{marks} {definition_title}\n\nTemplate body.\n\n### {declaration_heading}\n\n"
    raw = (
        f"# {key}\n\n"
        "```yaml\nplaceholder: true\n```\n\n"
        f"{definition}"
        f"{content_before_table}"
        f"{table_headers}"
        f"{row}"
        "\n## 2. Verification\n\nVerification body.\n"
    )
    path.write_text(raw, encoding="utf-8")
    parsed = parse_markdown(path, f"specs/{key}.md")
    assert parsed.issues == ()
    return FormalDocument(
        kind=kind,
        key=key,
        current_id="30",
        title=key,
        status=status,
        canonical_path=f"specs/{key}.md",
        positioning="test source",
        scope="test scope" if kind != "attachment" else None,
        basis=(),
        parent_spec=None,
        relation=None,
        authorized_attachments=(),
        supersedes=(),
        markdown=parsed.document,
    )


def _repository(
    tmp_path: Path,
    *active_documents: FormalDocument,
    parsed_documents: tuple[FormalDocument, ...] | None = None,
) -> RepositoryInspection:
    return RepositoryInspection(
        repository_root=tmp_path,
        candidates=(),
        parsed_documents=parsed_documents or active_documents,
        active_documents_passing_implemented_checks=active_documents,
        projections=(),
        issues=(),
        incomplete_scope=(),
        unchecked_conditions=("repository semantic review",),
        basis_reachability_overlaps=(),
        implemented_checks_complete=True,
    )


@pytest.mark.parametrize("definition_level", [2, 3])
def test_reads_valid_h2_or_h3_definition_and_exact_range(tmp_path: Path, definition_level: int) -> None:
    source = _source(tmp_path, "source-one", definition_level=definition_level)

    result = inspect_action_template_sources(_repository(tmp_path, source))

    assert result.issues == ()
    assert result.incomplete_sources == ()
    assert len(result.candidate_declarations) == 1
    declaration = result.candidate_declarations[0]
    assert declaration.template_key == "git-commit"
    assert declaration.summary == "Commit changes"
    assert declaration.activation_hint == (
        "Use when a local commit is explicitly authorized; do not use for inspection only."
    )
    assert declaration.source_key == "source-one"
    assert declaration.definition_heading.level == definition_level
    assert declaration.definition_start_line == declaration.definition_heading.line
    assert declaration.definition_end_line < len(source.markdown.raw_lines)
    expected_boundary = "## 2." if definition_level == 2 else "### 行动模板声明"
    assert source.markdown.raw_lines[declaration.definition_end_line].startswith(expected_boundary)
    assert declaration.source.path == "specs/source-one.md"
    assert result.unchecked_conditions == (
        "repository semantic review",
        "行动模板的重复价值、稳定剩余结构、承载位置、独立失败和净价值是否满足准入条件",
    )


@pytest.mark.parametrize(
    ("changes", "expected_summary"),
    [
        ({"content_before_table": "ordinary text\n\n"}, "必须紧接固定 Markdown 表格"),
        (
            {"table_headers": "| template_key | summary | definition_ref |\n|---|---|---|\n"},
            "表头与固定字段不一致",
        ),
        (
            {
                "table_headers": (
                    "| template_key | summary | activation_hint | definition_ref | extra |\n|---|---|---|---|---|\n"
                )
            },
            "表头与固定字段不一致",
        ),
        ({"row_override": ""}, "至少包含一个数据行"),
    ],
)
def test_source_level_shape_errors_suspend_all_declarations(
    tmp_path: Path,
    changes: dict[str, object],
    expected_summary: str,
) -> None:
    source = _source(tmp_path, "source-one", **changes)

    result = inspect_action_template_sources(_repository(tmp_path, source))

    assert result.candidate_declarations == ()
    assert result.incomplete_sources == ("source-one",)
    assert any(expected_summary in issue.summary for issue in result.issues)


def test_trailing_content_or_duplicate_heading_suspends_source(tmp_path: Path) -> None:
    source = _source(tmp_path, "source-one")
    path = tmp_path / "specs/source-one.md"
    raw = path.read_text(encoding="utf-8").replace(
        "\n## 2. Verification",
        "\nextra declaration prose\n\n## 2. Verification",
        1,
    )
    path.write_text(raw, encoding="utf-8")
    source = replace(source, markdown=parse_markdown(path, "specs/source-one.md").document)

    trailing = inspect_action_template_sources(_repository(tmp_path, source))

    assert trailing.candidate_declarations == ()
    assert any("只能包含唯一声明表" in issue.summary for issue in trailing.issues)

    path.write_text(raw + "\n### 行动模板声明\n", encoding="utf-8")
    source = replace(source, markdown=parse_markdown(path, "specs/source-one.md").document)
    duplicate = inspect_action_template_sources(_repository(tmp_path, source))

    assert duplicate.candidate_declarations == ()
    assert any("至多包含一个" in issue.summary for issue in duplicate.issues)


@pytest.mark.parametrize(
    ("changes", "expected_summary"),
    [
        ({"template_key": "Invalid_Key"}, "格式无效"),
        ({"definition_ref": "other::1. Template definition"}, "definition_ref 无效"),
        ({"definition_ref": "source-one::one::two"}, "definition_ref 无效"),
        ({"definition_ref": "source-one::Missing"}, "必须唯一指向同来源 H2 或 H3"),
        ({"definition_ref": "source-one::行动模板声明"}, "不得指向声明 H3 自身"),
        ({"activation_hint": ""}, "恰有四个非空单元格"),
        ({"row_override": "| `git-commit` | only two |\n"}, "恰有四个非空单元格"),
        (
            {"row_override": "| `git-commit` | Summary | Hint | `source-one::1. Template definition` | extra |\n"},
            "恰有四个非空单元格",
        ),
    ],
)
def test_invalid_rows_are_suspended_with_diagnostics(
    tmp_path: Path,
    changes: dict[str, object],
    expected_summary: str,
) -> None:
    source = _source(tmp_path, "source-one", **changes)

    result = inspect_action_template_sources(_repository(tmp_path, source))

    assert result.candidate_declarations == ()
    assert result.incomplete_sources == ("source-one",)
    assert any(expected_summary in issue.summary for issue in result.issues)


def test_ambiguous_definition_heading_is_rejected(tmp_path: Path) -> None:
    source = _source(tmp_path, "source-one", definition_level=3)
    path = tmp_path / "specs/source-one.md"
    raw = path.read_text(encoding="utf-8").replace(
        "### 行动模板声明",
        "### 1. Template definition\n\nDuplicate body.\n\n### 行动模板声明",
        1,
    )
    path.write_text(raw, encoding="utf-8")
    source = replace(source, markdown=parse_markdown(path, "specs/source-one.md").document)

    result = inspect_action_template_sources(_repository(tmp_path, source))

    assert result.candidate_declarations == ()
    assert any("必须唯一指向同来源 H2 或 H3" in issue.summary for issue in result.issues)


def test_invalid_sibling_row_does_not_remove_valid_row(tmp_path: Path) -> None:
    rows = (
        "| `git-commit` | Commit changes | Valid hint | `source-one::1. Template definition` |\n"
        "| `Invalid_Key` | Invalid | Invalid hint | `source-one::1. Template definition` |\n"
    )
    source = _source(tmp_path, "source-one", row_override=rows)

    result = inspect_action_template_sources(_repository(tmp_path, source))

    assert [item.template_key for item in result.candidate_declarations] == ["git-commit"]
    assert result.incomplete_sources == ("source-one",)
    assert any("格式无效" in issue.summary for issue in result.issues)


def test_duplicate_key_removes_all_conflicts_but_preserves_other_keys(tmp_path: Path) -> None:
    first = _source(tmp_path, "source-one", template_key="shared-template")
    second = _source(tmp_path, "source-two", template_key="shared-template")
    third = _source(tmp_path, "source-three", template_key="other-template")

    result = inspect_action_template_sources(_repository(tmp_path, first, second, third))

    assert [item.template_key for item in result.candidate_declarations] == ["other-template"]
    assert result.incomplete_sources == ("source-one", "source-two")
    duplicate_issues = [issue for issue in result.issues if "在本次声明候选中重复" in issue.summary]
    assert len(duplicate_issues) == 2
    assert all("shared-template" in issue.affected for issue in duplicate_issues)


def test_duplicate_key_in_one_source_removes_all_matching_rows(tmp_path: Path) -> None:
    rows = (
        "| `git-commit` | First | First hint | `source-one::1. Template definition` |\n"
        "| `git-commit` | Second | Second hint | `source-one::1. Template definition` |\n"
        "| `other-template` | Other | Other hint | `source-one::1. Template definition` |\n"
    )
    source = _source(tmp_path, "source-one", row_override=rows)

    result = inspect_action_template_sources(_repository(tmp_path, source))

    assert [item.template_key for item in result.candidate_declarations] == ["other-template"]
    assert result.incomplete_sources == ("source-one",)
    assert len([issue for issue in result.issues if "在本次声明候选中重复" in issue.summary]) == 2


def test_draft_or_non_passing_source_is_not_inspected(tmp_path: Path) -> None:
    active = _source(tmp_path, "source-active", template_key="active-template")
    draft = _source(tmp_path, "source-draft", template_key="draft-template", status="draft")

    result = inspect_action_template_sources(
        _repository(tmp_path, active, parsed_documents=(active, draft)),
    )

    assert [item.template_key for item in result.candidate_declarations] == ["active-template"]
    assert all(item.source_key != "source-draft" for item in result.candidate_declarations)


def test_non_spec_declaration_is_rejected(tmp_path: Path) -> None:
    attachment = _source(tmp_path, "source-attachment", kind="attachment")

    result = inspect_action_template_sources(_repository(tmp_path, attachment))

    assert result.candidate_declarations == ()
    assert result.incomplete_sources == ("source-attachment",)
    assert any("只有普通 spec" in issue.summary for issue in result.issues)


def test_result_does_not_claim_applicability_authorization_or_capability(tmp_path: Path) -> None:
    source = _source(tmp_path, "source-one")

    result = inspect_action_template_sources(_repository(tmp_path, source))

    declaration_fields = set(ActionTemplateDeclaration.__dataclass_fields__)
    inspection_fields = set(type(result).__dataclass_fields__)
    forbidden = {"applicable", "authorized", "executable", "available", "helper_operation"}
    assert declaration_fields.isdisjoint(forbidden)
    assert inspection_fields.isdisjoint(forbidden)
