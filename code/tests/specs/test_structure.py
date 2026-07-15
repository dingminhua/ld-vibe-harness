from pathlib import Path

import pytest

from ldvh.specs.identity import parse_identity
from ldvh.specs.markdown import parse_markdown
from ldvh.specs.structure import validate_structure

VERIFICATION_HEADER = "| 验证对象 | 验证时机 | 成立条件 | 可接受依据 | 验证入口 | 可证明范围 | 未满足时的处理 |"
VERIFICATION_DELIMITER = "|---|---|---|---|---|---|---|"
VERIFICATION_ROW = "| object | time | condition | evidence | entry | range | action |"
VERIFICATION_TABLE = f"{VERIFICATION_HEADER}\n{VERIFICATION_DELIMITER}\n{VERIFICATION_ROW}"


def _source(verification_table: str = VERIFICATION_TABLE) -> str:
    return f"""# Example

```yaml
ldvh_spec:
  spec_key: "example-spec"
  spec_id: "99"
  spec_kind: "spec"
  title: "Example"
  status: "active"
  canonical_path: "specs/99-Example.md"
  parent_spec: "ldvh-root"
  relation: "refines"
  positioning: "Example positioning"
  scope: "Example scope"
  basis:
    - "ldvh-root"
  authorized_attachments: []
```

## 1. 价值判断

## 2. 规范依据

## 3. 职责边界

## 4. 适用范围

## 5. 具体规则

## 6. 验证要求

{verification_table}

## 7. Human Gate

## 8. Stop Conditions
"""


def _document(tmp_path: Path, source: str, *, allow_markdown_issues: bool = False):
    path = tmp_path / "specs/99-Example.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")
    markdown = parse_markdown(path, "specs/99-Example.md")
    if not allow_markdown_issues:
        assert markdown.issues == ()
    identity = parse_identity(markdown.document)
    assert identity.document is not None
    return identity.document


def test_accepts_regular_structure_and_independent_seven_column_oracle(tmp_path: Path) -> None:
    assert validate_structure(_document(tmp_path, _source())) == ()


def test_structure_does_not_interpret_semantic_conflicts_or_gate_words(tmp_path: Path) -> None:
    source = _source().replace(
        "## 5. 具体规则",
        """## 5. 具体规则

规则 A 声称同一事项必须执行，规则 B 声称同一事项不得执行。
正文提到 Human Gate 和 Stop Conditions，但不改变固定尾部结构。""",
    )

    assert validate_structure(_document(tmp_path, source)) == ()


def test_rejects_wrong_verification_header_order(tmp_path: Path) -> None:
    wrong = VERIFICATION_TABLE.replace("| 验证入口 | 可证明范围 |", "| 可证明范围 | 验证入口 |")
    issues = validate_structure(_document(tmp_path, _source(wrong)))

    assert any("固定七列" in issue.summary for issue in issues)


def test_rejects_non_contiguous_h2_and_wrong_fixed_head(tmp_path: Path) -> None:
    source = _source().replace("## 1. 价值判断", "## 1. Overview").replace("## 5. 具体规则", "## 9. 具体规则")
    issues = validate_structure(_document(tmp_path, source))

    assert any("前四个 H2" in issue.summary for issue in issues)
    assert any("连续递增" in issue.summary for issue in issues)


def test_rejects_setext_h2_even_when_atx_structure_would_otherwise_pass(tmp_path: Path) -> None:
    source = _source().replace("## 6. 验证要求", "Hidden section\n--------------\n\n## 6. 验证要求")
    document = _document(tmp_path, source, allow_markdown_issues=True)

    issues = validate_structure(document)

    assert any(issue.summary == "规范正文不得使用 Setext H2；必须使用 ATX 标题" for issue in issues)


def test_rejects_verification_table_found_only_inside_fenced_code(tmp_path: Path) -> None:
    fenced_table = f"```markdown\n{VERIFICATION_TABLE}\n```"

    issues = validate_structure(_document(tmp_path, _source(fenced_table)))

    assert any(issue.summary == "验证要求章节必须包含顺序精确的固定七列表格" for issue in issues)


def test_earlier_verification_heading_cannot_supply_the_fixed_tail_table(tmp_path: Path) -> None:
    source = (
        _source("")
        .replace("## 5. 具体规则", f"## 5. 验证要求\n\n{VERIFICATION_TABLE}\n\n## 6. 具体规则")
        .replace("## 6. 验证要求", "## 7. 验证要求")
        .replace("## 7. Human Gate", "## 8. Human Gate")
        .replace("## 8. Stop Conditions", "## 9. Stop Conditions")
    )
    expected_line = source.splitlines().index("## 7. 验证要求") + 1

    issues = validate_structure(_document(tmp_path, source))

    matching = [issue for issue in issues if issue.summary == "验证要求章节必须包含顺序精确的固定七列表格"]
    assert len(matching) == 1
    assert matching[0].location.line == expected_line


def test_verification_table_requires_at_least_one_body_row(tmp_path: Path) -> None:
    empty_table = f"{VERIFICATION_HEADER}\n{VERIFICATION_DELIMITER}"

    issues = validate_structure(_document(tmp_path, _source(empty_table)))

    assert any(issue.summary == "验证要求固定七列表格必须至少包含一行" for issue in issues)


@pytest.mark.parametrize(
    "row",
    (
        "| object | time | condition | evidence | entry | range |",
        "| object | time | condition | evidence | entry | range | action | extra |",
    ),
    ids=("six-columns", "eight-columns"),
)
def test_verification_table_requires_exactly_seven_cells_in_every_row(tmp_path: Path, row: str) -> None:
    table = f"{VERIFICATION_HEADER}\n{VERIFICATION_DELIMITER}\n{VERIFICATION_ROW}\n{row}"

    issues = validate_structure(_document(tmp_path, _source(table)))

    assert any(issue.summary == "验证要求固定七列表格的每一行都必须恰好包含七列" for issue in issues)
