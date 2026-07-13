from pathlib import Path

import pytest

from ldvh.specs.markdown import Heading, parse_markdown, parse_table_after_heading


def _write(tmp_path: Path, text: str, relative_path: str = "specs/99-Example.md") -> Path:
    path = tmp_path / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_parses_fixed_header_yaml_and_headings_outside_fences(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        """# Example

```yaml
ldvh_spec:
  spec_key: "example"
```

## 1. First

```markdown
## Not a heading
```

### Exact target
""",
    )

    result = parse_markdown(path, "specs/99-Example.md")

    assert result.issues == ()
    assert result.document.relative_path == "specs/99-Example.md"
    assert result.document.h1 == "Example"
    assert result.document.h1_line == 1
    assert result.document.yaml_text == 'ldvh_spec:\n  spec_key: "example"'
    assert result.document.yaml_line == 3
    assert result.document.raw_lines[0] == "# Example"
    assert result.document.raw_text == path.read_text(encoding="utf-8")
    assert result.document.headings == (
        Heading(2, "1. First", 8),
        Heading(3, "Exact target", 14),
    )


def test_preserves_decoded_source_line_endings_and_terminal_newline(tmp_path: Path) -> None:
    source = b'# Example\r\n\r\n```yaml\r\nkey: "value"\r\n```\r\n'
    path = tmp_path / "specs/99-Example.md"
    path.parent.mkdir(parents=True)
    path.write_bytes(source)

    result = parse_markdown(path, "specs/99-Example.md")

    assert result.issues == ()
    assert result.document.raw_text.encode("utf-8") == source
    assert result.document.raw_lines == ("# Example", "", "```yaml", 'key: "value"', "```")


def test_requires_first_line_unique_h1_and_fixed_yaml_position(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        """
# Late title


```yaml
key: value
```

# Another title
""",
        "specs/99-Bad.md",
    )

    result = parse_markdown(path, "specs/99-Bad.md")

    assert result.document.h1 is None
    assert [issue.location.line for issue in result.issues] == [1, 2, 2, 9]
    assert "exactly one blank line" in result.issues[1].summary


def test_reports_unclosed_yaml_fence(tmp_path: Path) -> None:
    path = _write(tmp_path, '# Example\n\n```yaml\nkey: "value"\n')

    result = parse_markdown(path, "specs/99-Example.md")

    assert result.document.yaml_text == 'key: "value"'
    assert len(result.issues) == 1
    assert result.issues[0].location.line == 3
    assert "not closed" in result.issues[0].summary


@pytest.mark.parametrize(
    ("opening", "closing"),
    (
        ("~~~yaml", "~~~"),
        ("````yaml", "````"),
        ("~~~~ yaml  ", "~~~~~\t"),
    ),
    ids=("tilde", "four-backticks", "trimmed-exact-info-and-longer-close"),
)
def test_accepts_gfm_identity_fence_markers(
    tmp_path: Path,
    opening: str,
    closing: str,
) -> None:
    path = _write(
        tmp_path,
        f"""# Example

{opening}
ldvh_spec:
  spec_key: "example"
{closing}

## 1. First
""",
    )

    result = parse_markdown(path, "specs/99-Example.md")

    assert result.issues == ()
    assert result.document.yaml_text == 'ldvh_spec:\n  spec_key: "example"'
    assert result.document.headings == (Heading(2, "1. First", 8),)


def test_identity_fence_ignores_shorter_and_different_marker_closes(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        """# Example

````yaml
key: "value"
```
~~~~
`````
""",
    )

    result = parse_markdown(path, "specs/99-Example.md")

    assert result.issues == ()
    assert result.document.yaml_text == 'key: "value"\n```\n~~~~'


@pytest.mark.parametrize("opening", ("~~~YAML", "~~~yaml example", "~~~"))
def test_identity_fence_requires_exact_yaml_info(tmp_path: Path, opening: str) -> None:
    path = _write(tmp_path, f'# Example\n\n{opening}\nkey: "value"\n~~~\n')

    result = parse_markdown(path, "specs/99-Example.md")

    assert result.document.yaml_text is None
    assert any("YAML identity fence must follow" in issue.summary for issue in result.issues)


def test_exact_heading_lookup_preserves_duplicates(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        """# Example

```yaml
key: "value"
```

### Helper public operations
### Helper public operations extra
### Helper public operations
""",
    )

    document, issues = parse_markdown(path, "specs/99-Example.md")

    assert issues == ()
    matches = document.find_headings("Helper public operations", level=3)
    assert [heading.line for heading in matches] == [7, 9]
    assert document.find_headings("helper public operations", level=3) == ()
    assert document.find_heading("Helper public operations", level=3) == matches[0]


def test_rejects_setext_h1_and_h2_but_ignores_setext_shapes_inside_fences(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        """# Example

```yaml
key: "value"
```

Setext level one
================
Setext level two
----------------
```markdown
Fenced Setext
-------------
```
""",
    )

    result = parse_markdown(path, "specs/99-Example.md")

    setext_issues = [issue for issue in result.issues if issue.summary.startswith("Setext H")]
    assert [(issue.summary, issue.location.line, issue.location.heading) for issue in setext_issues] == [
        ("Setext H1 headings are not allowed; use ATX headings", 7, "Setext level one"),
        ("Setext H2 headings are not allowed; use ATX headings", 9, "Setext level two"),
    ]
    assert result.document.headings == ()


def test_parses_adjacent_table_with_escaped_pipe_and_inline_code(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        """# Example

```yaml
key: "value"
```

### Contract

| `operation_key` | summary | reference |
|---|:---:|---:|
| `read-rules` | keeps \\| pipe | `source::Heading` |
| `short` | only two |

After the table.
""",
    )
    document = parse_markdown(path, "specs/99-Example.md").document
    heading = document.find_heading("Contract", level=3)

    assert heading is not None
    table = parse_table_after_heading(document, heading)
    assert table is not None
    assert table.line == 9
    assert table.headers == ("operation_key", "summary", "reference")
    assert table.rows == (
        ("read-rules", "keeps | pipe", "source::Heading"),
        ("short", "only two"),
    )


def test_synthetic_anchor_cannot_read_a_table_inside_fenced_code(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        """# Example

```yaml
key: "value"
```

```markdown
| one | two |
|---|---|
| a | b |
```
""",
    )
    document = parse_markdown(path, "specs/99-Example.md").document

    assert parse_table_after_heading(document, Heading(3, "synthetic", 7)) is None


def test_table_must_be_adjacent_after_optional_blank_lines(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        """# Example

```yaml
key: "value"
```

### Contract

An intervening paragraph.

| key | value |
|---|---|
| a | b |
""",
    )
    document = parse_markdown(path, "specs/99-Example.md").document
    heading = document.find_heading("Contract", level=3)

    assert heading is not None
    assert document.table_after(heading) is None


def test_invalid_table_delimiter_is_not_a_table(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        """# Example

```yaml
key: "value"
```

### Contract
| key | value |
| -- | --- |
| a | b |
""",
    )
    document = parse_markdown(path, "specs/99-Example.md").document
    heading = document.find_heading("Contract", level=3)

    assert heading is not None
    assert document.table_after(heading) is None


def test_only_unwraps_inline_code_that_covers_the_entire_cell(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        """# Example

```yaml
key: "value"
```

### Contract
| one span | two spans | nested tick |
|---|---|---|
| `value` | `first` `second` | ``a`b`` |
""",
    )

    document = parse_markdown(path, "specs/99-Example.md").document
    table = document.table_after_heading("Contract", level=3)

    assert table is not None
    assert table.rows == (("value", "`first` `second`", "a`b"),)


def test_source_read_does_not_follow_final_file_symlink(tmp_path: Path) -> None:
    external = tmp_path / "external.md"
    external.write_text('# External\n\n```yaml\nkey: "value"\n```\n', encoding="utf-8")
    linked = tmp_path / "specs/99-Example.md"
    linked.parent.mkdir(parents=True)
    linked.symlink_to(external)

    result = parse_markdown(linked, "specs/99-Example.md")

    assert result.document.raw_lines == ()
    assert len(result.issues) == 1
    assert result.issues[0].summary == "Markdown source could not be read safely from its current path"


def test_source_read_does_not_follow_parent_directory_symlink(tmp_path: Path) -> None:
    external_specs = tmp_path / "external-specs"
    external_specs.mkdir()
    (external_specs / "99-Example.md").write_text(
        '# External\n\n```yaml\nkey: "value"\n```\n',
        encoding="utf-8",
    )
    repository = tmp_path / "repository"
    repository.mkdir()
    (repository / "specs").symlink_to(external_specs, target_is_directory=True)

    result = parse_markdown(repository / "specs/99-Example.md", "specs/99-Example.md")

    assert result.document.raw_lines == ()
    assert len(result.issues) == 1
    assert result.issues[0].summary == "Markdown source could not be read safely from its current path"
