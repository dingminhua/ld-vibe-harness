from pathlib import Path

import pytest

from ldvh.diagnostics import SourceLocation
from ldvh.specs.identity import parse_identity
from ldvh.specs.markdown import parse_markdown

EXPECTED_SPEC_FIELDS = {
    "spec_key",
    "spec_id",
    "spec_kind",
    "title",
    "status",
    "canonical_path",
    "parent_spec",
    "relation",
    "positioning",
    "scope",
    "basis",
    "authorized_attachments",
}

REQUIRED_SPEC_FIELD_FRAGMENTS = (
    ("spec_key", '  spec_key: "example-spec"\n'),
    ("spec_id", '  spec_id: "99"\n'),
    ("spec_kind", '  spec_kind: "spec"\n'),
    ("title", '  title: "Example"\n'),
    ("status", '  status: "active"\n'),
    ("canonical_path", '  canonical_path: "specs/99-Example.md"\n'),
    ("positioning", '  positioning: "Example positioning"\n'),
    ("scope", '  scope: "Example scope"\n'),
    ("basis", '  basis:\n    - "ldvh-root"\n'),
    ("authorized_attachments", "  authorized_attachments: []\n"),
)


def _spec_source(extra: str = "", *, title: str = "Example") -> str:
    return f'''# {title}

```yaml
ldvh_spec:
  spec_key: "example-spec"
  spec_id: "99"
  spec_kind: "spec"
  title: "{title}"
  status: "active"
  canonical_path: "specs/99-Example.md"
  parent_spec: "ldvh-root"
  relation: "refines"
  positioning: "Example positioning"
  scope: "Example scope"
  basis:
    - "ldvh-root"
  authorized_attachments: []
{extra}```
'''


def _attachment_source(*, title: str = "Example attachment") -> str:
    return f'''# {title}

```yaml
ldvh_attachment:
  attachment_key: "example-attachment"
  attachment_id: "99.Att.01"
  title: "{title}"
  status: "active"
  canonical_path: "specs/attachments/99.Att.01-{title}.md"
  positioning: "Example attachment positioning"
```
'''


def _root_source() -> str:
    return """# 理念与构成

```yaml
ldvh_spec:
  spec_id: "00"
  spec_kind: "spec"
  title: "理念与构成"
  status: "active"
  authority: "active"
  canonical_path: "specs/00-理念与构成.md"
  parent_spec: ""
  relation: ""
  positioning: "Root positioning"
  scope: "Root scope"
  basis: []
  related_specs: []
  code_consumption:
    - "root-consumer"
```
"""


def _parse(tmp_path: Path, source: str, relative_path: str = "specs/99-Example.md"):
    path = tmp_path / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")
    markdown = parse_markdown(path, relative_path)
    assert markdown.issues == ()
    return parse_identity(markdown.document)


def test_parses_independently_enumerated_regular_spec_fields(tmp_path: Path) -> None:
    result = _parse(tmp_path, _spec_source())

    assert result.issues == ()
    assert result.document is not None
    assert result.document.key == "example-spec"
    assert result.document.basis == ("ldvh-root",)
    yaml_lines = _spec_source().split("```yaml\n", 1)[1].split("```", 1)[0]
    actual_fields = {
        line.strip().split(":", 1)[0]
        for line in yaml_lines.splitlines()
        if line.startswith("  ") and not line.startswith("    ")
    }
    assert actual_fields == EXPECTED_SPEC_FIELDS


def test_preserves_immutable_field_source_locations(tmp_path: Path) -> None:
    result = _parse(tmp_path, _spec_source())

    assert result.document is not None
    assert result.document.field_locations == {
        "spec_key": SourceLocation("specs/99-Example.md", 5),
        "spec_id": SourceLocation("specs/99-Example.md", 6),
        "spec_kind": SourceLocation("specs/99-Example.md", 7),
        "title": SourceLocation("specs/99-Example.md", 8),
        "status": SourceLocation("specs/99-Example.md", 9),
        "canonical_path": SourceLocation("specs/99-Example.md", 10),
        "parent_spec": SourceLocation("specs/99-Example.md", 11),
        "relation": SourceLocation("specs/99-Example.md", 12),
        "positioning": SourceLocation("specs/99-Example.md", 13),
        "scope": SourceLocation("specs/99-Example.md", 14),
        "basis": SourceLocation("specs/99-Example.md", 15),
        "authorized_attachments": SourceLocation("specs/99-Example.md", 17),
    }
    with pytest.raises(TypeError):
        result.document.field_locations["status"] = SourceLocation("elsewhere", 1)  # type: ignore[index]


def test_root_implicit_key_does_not_claim_a_yaml_field_location(tmp_path: Path) -> None:
    result = _parse(tmp_path, _root_source(), "specs/00-理念与构成.md")

    assert result.issues == ()
    assert result.document is not None
    assert result.document.key == "ldvh-root"
    assert "spec_key" not in result.document.field_locations
    assert result.document.field_locations["spec_id"] == SourceLocation("specs/00-理念与构成.md", 5)


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        ('  unknown_field: "x"\n', "未知字段"),
        ('  supersedes: ["old", "old"]\n', ""),
    ],
)
def test_field_mutations_do_not_change_the_independent_oracle(tmp_path: Path, mutation: str, expected: str) -> None:
    result = _parse(tmp_path, _spec_source(mutation))

    if expected:
        assert any(expected in issue.summary for issue in result.issues)
    else:
        assert result.document is not None
        assert result.document.supersedes == ("old", "old")
    assert EXPECTED_SPEC_FIELDS == {
        "spec_key",
        "spec_id",
        "spec_kind",
        "title",
        "status",
        "canonical_path",
        "parent_spec",
        "relation",
        "positioning",
        "scope",
        "basis",
        "authorized_attachments",
    }


@pytest.mark.parametrize(("field_name", "fragment"), REQUIRED_SPEC_FIELD_FRAGMENTS)
def test_rejects_each_deleted_required_spec_field(tmp_path: Path, field_name: str, fragment: str) -> None:
    source = _spec_source().replace(fragment, "")

    result = _parse(tmp_path, source)

    assert result.document is None
    assert any(issue.summary == f"YAML 身份缺少字段: {field_name}" for issue in result.issues)


@pytest.mark.parametrize(
    ("original", "replacement", "expected_summary"),
    (
        ('  status: "active"', '  status: "enabled"', "status 必须是 draft、active 或 retired"),
        ('  spec_kind: "spec"', '  spec_kind: "attachment"', "spec_kind 必须固定为 'spec'"),
        ('  relation: "refines"', '  relation: "contains"', "当前普通规范 relation 只允许 'refines'"),
    ),
)
def test_rejects_values_outside_independent_allowed_value_literals(
    tmp_path: Path,
    original: str,
    replacement: str,
    expected_summary: str,
) -> None:
    result = _parse(tmp_path, _spec_source().replace(original, replacement))

    assert result.document is None
    assert any(issue.summary == expected_summary for issue in result.issues)


def test_rejects_plain_string_value(tmp_path: Path) -> None:
    result = _parse(tmp_path, _spec_source().replace('  title: "Example"', "  title: Example"))

    assert result.document is None
    assert any("双引号" in issue.summary for issue in result.issues)


def test_rejects_duplicate_yaml_key(tmp_path: Path) -> None:
    source = _spec_source().replace('  status: "active"', '  status: "active"\n  status: "draft"')
    result = _parse(tmp_path, source)

    assert result.document is None
    assert any("唯一映射" in issue.summary for issue in result.issues)


def test_rejects_non_string_identity_field_name_without_raising(tmp_path: Path) -> None:
    result = _parse(tmp_path, _spec_source('  1: "unexpected"\n'))

    assert result.document is None
    assert tuple(issue.summary for issue in result.issues) == ("YAML 身份字段名 1 必须是字符串",)
    assert result.issues[0].location.path == "specs/99-Example.md"


def test_rejects_anchor_and_alias(tmp_path: Path) -> None:
    source = (
        _spec_source()
        .replace(
            '  positioning: "Example positioning"',
            '  positioning: &shared "Example positioning"\n  scope: *shared',
        )
        .replace('  scope: "Example scope"\n', "")
    )
    result = _parse(tmp_path, source)

    assert result.document is None
    assert any("锚点或别名" in issue.summary for issue in result.issues)


def test_rejects_an_implicit_document_followed_by_a_second_document(tmp_path: Path) -> None:
    source = _spec_source().replace("```\n", "---\nldvh_spec: {{}}\n```\n", 1)

    result = _parse(tmp_path, source)

    assert result.document is None
    assert any(issue.summary == "YAML 身份块不得包含多个 YAML 文档" for issue in result.issues)


def test_rejects_custom_yaml_tag(tmp_path: Path) -> None:
    source = _spec_source().replace('  title: "Example"', '  title: !example "Example"')

    result = _parse(tmp_path, source)

    assert result.document is None
    assert any(issue.summary == "YAML 身份块不得包含标签" for issue in result.issues)


def test_rejects_merge_key_without_relying_on_anchor_diagnostic(tmp_path: Path) -> None:
    source = _spec_source("  <<: {}\n")

    result = _parse(tmp_path, source)

    assert result.document is None
    assert any(issue.summary == "YAML 身份块不得包含合并键" for issue in result.issues)


@pytest.mark.parametrize(
    ("source", "relative_path", "expected_summary"),
    (
        (
            _attachment_source(),
            "specs/99-Example attachment.md",
            "YAML 顶层 ldvh_attachment 只能用于授权附件候选路径",
        ),
        (
            _attachment_source(title="理念与构成"),
            "specs/00-理念与构成.md",
            "YAML 顶层 ldvh_attachment 只能用于授权附件候选路径",
        ),
        (
            _spec_source(),
            "specs/attachments/99.Att.01-Example.md",
            "YAML 顶层 ldvh_spec 不能用于授权附件候选路径",
        ),
    ),
)
def test_top_level_discriminator_cannot_be_overridden_by_path(
    tmp_path: Path,
    source: str,
    relative_path: str,
    expected_summary: str,
) -> None:
    result = _parse(tmp_path, source, relative_path)

    assert result.document is None
    assert tuple(issue.summary for issue in result.issues) == (expected_summary,)


@pytest.mark.parametrize(
    ("yaml_text", "expected_summary"),
    (
        ("- ldvh_spec\n", "YAML 身份块顶层必须是映射"),
        ('ldvh_spec: "not-a-mapping"\n', "YAML 身份对象必须是映射"),
    ),
)
def test_rejects_non_mapping_yaml_shapes(tmp_path: Path, yaml_text: str, expected_summary: str) -> None:
    source = f"# Example\n\n```yaml\n{yaml_text}```\n"

    result = _parse(tmp_path, source)

    assert result.document is None
    assert tuple(issue.summary for issue in result.issues) == (expected_summary,)


def test_attachment_filename_title_need_not_duplicate_h1_spacing(tmp_path: Path) -> None:
    source = """# LDVH 双语术语表

```yaml
ldvh_attachment:
  attachment_key: "example-attachment"
  attachment_id: "01.Att.99"
  title: "LDVH 双语术语表"
  status: "active"
  canonical_path: "specs/attachments/01.Att.99-LDVH双语术语表.md"
  positioning: "Example attachment"
```
"""
    result = _parse(tmp_path, source, "specs/attachments/01.Att.99-LDVH双语术语表.md")

    assert result.issues == ()
    assert result.document is not None
