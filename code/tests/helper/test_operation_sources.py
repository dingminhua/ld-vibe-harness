from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from ldvh.helper.operation_sources import inspect_operation_sources
from ldvh.specs.identity import FormalDocument
from ldvh.specs.markdown import parse_markdown
from ldvh.specs.repository import RepositoryInspection

DECLARATION_HEADERS = (
    "| operation_key | summary | effect | arguments_contract | result_contract |\n|---|---|---|---|---|\n"
)


def _source(
    tmp_path: Path,
    key: str,
    *,
    operation_key: str = "read-source",
    effect: str = "read",
    declaration_heading: str = "Helper 公开操作",
    content_before_table: str = "",
    table_headers: str = DECLARATION_HEADERS,
    extra_contract_heading: str = "",
    arguments_contract: str | None = None,
    result_contract: str | None = None,
    row_override: str | None = None,
    authorized_attachments: tuple[str, ...] = (),
) -> FormalDocument:
    path = tmp_path / f"specs/{key}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    operation_row = row_override
    if operation_row is None:
        arguments_reference = f"{key}::输入字段" if arguments_contract is None else arguments_contract
        result_reference = f"{key}::结果字段" if result_contract is None else result_contract
        operation_row = (
            f"| `{operation_key}` | Read source | `{effect}` | `{arguments_reference}` | `{result_reference}` |\n"
        )
    raw = (
        f"# {key}\n\n"
        "```yaml\nplaceholder: true\n```\n\n"
        "## 1. Contract\n\n"
        "### 输入字段\n\n"
        "| field | meaning |\n|---|---|\n| value | input |\n\n"
        f"{extra_contract_heading}"
        "### 结果字段\n\n"
        "| field | meaning |\n|---|---|\n| value | output |\n\n"
        f"### {declaration_heading}\n\n"
        f"{content_before_table}"
        f"{table_headers}"
        f"{operation_row}"
    )
    path.write_text(raw, encoding="utf-8")
    parsed = parse_markdown(path, f"specs/{key}.md")
    assert parsed.issues == ()
    return FormalDocument(
        kind="spec",
        key=key,
        current_id="10",
        title=key,
        status="active",
        canonical_path=f"specs/{key}.md",
        positioning="test source",
        scope="test scope",
        basis=(),
        parent_spec=None,
        relation=None,
        authorized_attachments=authorized_attachments,
        supersedes=(),
        markdown=parsed.document,
    )


def _repository(tmp_path: Path, *documents: FormalDocument) -> RepositoryInspection:
    return RepositoryInspection(
        repository_root=tmp_path,
        candidates=(),
        parsed_documents=documents,
        active_documents_passing_implemented_checks=documents,
        projections=(),
        issues=(),
        incomplete_scope=(),
        unchecked_conditions=("repository semantic review",),
        basis_reachability_overlaps=(),
        implemented_checks_complete=True,
    )


def test_reads_one_valid_declaration_and_preserves_source(tmp_path: Path) -> None:
    source = _source(tmp_path, "source-one")

    result = inspect_operation_sources(_repository(tmp_path, source))

    assert result.issues == ()
    assert result.incomplete_sources == ()
    assert len(result.candidate_declarations) == 1
    declaration = result.candidate_declarations[0]
    assert declaration.operation_key == "read-source"
    assert declaration.effect == "read"
    assert declaration.arguments_contract == "source-one::输入字段"
    assert declaration.result_contract == "source-one::结果字段"
    assert declaration.source_key == "source-one"
    assert declaration.source.path == "specs/source-one.md"
    assert result.unchecked_conditions == (
        "repository semantic review",
        "契约目标章节是否完整定义字段、类型、必填性、空值和闭集语义",
    )


@pytest.mark.parametrize(
    ("changes", "expected_summary"),
    [
        ({"effect": "write"}, "不是 read 或 may_change_state"),
        ({"operation_key": "Invalid_Key"}, "格式无效"),
        ({"operation_key": "capabilities"}, "是 Helper 保留入口"),
        ({"content_before_table": "ordinary text\n\n"}, "必须紧接固定 Markdown 表格"),
        (
            {
                "table_headers": (
                    "| operation_key | summary | effect | arguments_contract | wrong |\n|---|---|---|---|---|\n"
                )
            },
            "表头与固定字段不一致",
        ),
        ({"extra_contract_heading": "### 输入字段\n\n"}, "精确标题缺失或不唯一"),
        ({"arguments_contract": "other-source::输入字段"}, "越过声明来源或其授权附件"),
        ({"arguments_contract": "source-one::"}, "缺少精确标题文本"),
        ({"arguments_contract": "source-one::不存在"}, "精确标题缺失或不唯一"),
        ({"row_override": "| `read-source` | only two |\n"}, "恰有五个非空单元格"),
        ({"row_override": ""}, "至少包含一个数据行"),
    ],
)
def test_rejects_invalid_declaration_shapes(
    tmp_path: Path,
    changes: dict[str, object],
    expected_summary: str,
) -> None:
    source = _source(tmp_path, "source-one", **changes)

    result = inspect_operation_sources(_repository(tmp_path, source))

    assert result.candidate_declarations == ()
    assert result.incomplete_sources == ("source-one",)
    assert any(expected_summary in issue.summary for issue in result.issues)


def test_contract_reference_may_target_one_authorized_attachment(tmp_path: Path) -> None:
    attachment_source = _source(tmp_path, "source-fields", declaration_heading="Not a declaration")
    attachment_path = "specs/attachments/10.Att.01-source-fields.md"
    attachment = FormalDocument(
        kind="attachment",
        key="source-fields",
        current_id="10.Att.01",
        title=attachment_source.title,
        status="active",
        canonical_path=attachment_path,
        positioning=attachment_source.positioning,
        scope=None,
        basis=(),
        parent_spec=None,
        relation=None,
        authorized_attachments=(),
        supersedes=(),
        markdown=replace(attachment_source.markdown, relative_path=attachment_path),
    )
    source = _source(
        tmp_path,
        "source-one",
        arguments_contract="source-fields::输入字段",
        result_contract="source-fields::结果字段",
        authorized_attachments=("source-fields",),
    )

    result = inspect_operation_sources(_repository(tmp_path, source, attachment))

    assert result.issues == ()
    assert len(result.candidate_declarations) == 1
    assert result.candidate_declarations[0].arguments_contract == "source-fields::输入字段"


def test_rejects_duplicate_exact_declaration_heading(tmp_path: Path) -> None:
    source = _source(tmp_path, "source-one")
    path = tmp_path / "specs/source-one.md"
    path.write_text(path.read_text(encoding="utf-8") + "\n### Helper 公开操作\n", encoding="utf-8")
    reparsed = parse_markdown(path, "specs/source-one.md")
    source = replace(source, markdown=reparsed.document)

    result = inspect_operation_sources(_repository(tmp_path, source))

    assert result.candidate_declarations == ()
    assert result.incomplete_sources == ("source-one",)
    assert any("至多包含一个" in issue.summary for issue in result.issues)


def test_duplicate_operation_key_is_removed_from_all_conflicting_sources(tmp_path: Path) -> None:
    first = _source(tmp_path, "source-one", operation_key="shared-operation")
    second = _source(tmp_path, "source-two", operation_key="shared-operation")

    result = inspect_operation_sources(_repository(tmp_path, first, second))

    assert result.candidate_declarations == ()
    assert result.incomplete_sources == ("source-one", "source-two")
    assert len([issue for issue in result.issues if "在本次声明候选中重复" in issue.summary]) == 2


def test_invalid_duplicate_row_still_blocks_the_valid_candidate(tmp_path: Path) -> None:
    source = _source(tmp_path, "source-one", operation_key="shared-operation")
    path = tmp_path / "specs/source-one.md"
    raw = path.read_text(encoding="utf-8")
    raw += "| `shared-operation` | Duplicate | `invalid-effect` | `source-one::输入字段` | `source-one::结果字段` |\n"
    path.write_text(raw, encoding="utf-8")
    source = replace(source, markdown=parse_markdown(path, "specs/source-one.md").document)

    result = inspect_operation_sources(_repository(tmp_path, source))

    assert result.candidate_declarations == ()
    assert result.incomplete_sources == ("source-one",)
    assert len([issue for issue in result.issues if "在本次声明候选中重复" in issue.summary]) == 2


def test_example_heading_does_not_create_a_public_operation(tmp_path: Path) -> None:
    source = _source(tmp_path, "source-one", declaration_heading="Helper 公开操作示例")

    result = inspect_operation_sources(_repository(tmp_path, source))

    assert result.candidate_declarations == ()
    assert result.issues == ()
    assert result.incomplete_sources == ()
    assert result.unchecked_conditions == ("repository semantic review",)
