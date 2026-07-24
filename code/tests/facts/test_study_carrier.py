from __future__ import annotations

import pytest

from ldvh.facts.carriers.study_markdown import STUDY_H2_TITLES, parse_study_markdown


def _body(*, content: str = "内容") -> str:
    return "".join(f"## {title}\n\n{content} {index}\n\n" for index, title in enumerate(STUDY_H2_TITLES, start=1))


def _active_body() -> str:
    return """## 研究问题

当前项目需要判断外部实践是否值得转成下一步行动。

外部实践如何处理边界清晰的协作任务？

## 输入与边界

已读取外部资料并区分其说明范围。

不把产品能力直接写成项目规则。

## 关键发现

### 一个强发现即可

外部资料说明独立读取可并行；项目可据此组织探索，并提出由单一汇总人收敛的下一步方向。

## 建议

先明确独立读取任务的输出和汇总人。

## 后续分流

- 当前没有需改变的项目行为，因此无需对象化。
"""


def _study(frontmatter: str = 'object_id: "study-0001"\ntitle: "Example"\n', body: str | None = None) -> str:
    return f"---\n{frontmatter}---\n{_body() if body is None else body}"


def test_parses_frontmatter_and_preserves_body_exactly() -> None:
    body = _body(content="正文")

    result = parse_study_markdown(_study(body=body))

    assert result.issues == ()
    assert result.parsed
    assert result.fields == {"object_id": "study-0001", "title": "Example"}
    assert result.body == body


@pytest.mark.parametrize(
    ("source", "summary"),
    (
        ("", "必须以唯一 YAML frontmatter 开始"),
        (_body(), "必须以唯一 YAML frontmatter 开始"),
        ("---\nobject_id: study-0001\n", "frontmatter 未闭合"),
    ),
)
def test_rejects_missing_or_unclosed_opening_frontmatter(source: str, summary: str) -> None:
    result = parse_study_markdown(source)

    assert result.fields is None
    assert result.body is None
    assert len(result.issues) == 1
    assert result.issues[0].category == "parse"
    assert summary in result.issues[0].summary


def test_rejects_duplicate_frontmatter_keys() -> None:
    result = parse_study_markdown(_study('object_id: "study-0001"\nobject_id: "study-0002"\n'))

    assert result.fields is None
    assert result.body is not None
    assert result.issues[0].category == "parse"
    assert result.issues[0].summary == "Study frontmatter 无法形成唯一 YAML mapping"


@pytest.mark.parametrize("frontmatter", ("- one\n- two\n", "plain scalar\n", "\n"))
def test_rejects_non_mapping_frontmatter(frontmatter: str) -> None:
    result = parse_study_markdown(_study(frontmatter))

    assert result.fields is None
    assert len(result.issues) == 1
    assert result.issues[0].category == "schema"
    assert "顶层必须是 mapping" in result.issues[0].summary


@pytest.mark.parametrize("mutation", ("missing", "duplicate", "out_of_order"))
def test_rejects_missing_duplicate_or_out_of_order_fixed_h2(mutation: str) -> None:
    sections = [f"## {title}\n\n内容\n\n" for title in STUDY_H2_TITLES]
    if mutation == "missing":
        sections.pop(2)
    elif mutation == "duplicate":
        sections.insert(3, sections[2])
    else:
        sections[1], sections[2] = sections[2], sections[1]

    result = parse_study_markdown(_study(body="".join(sections)))

    assert not result.parsed
    assert all(issue.category == "schema" for issue in result.issues)
    assert any("一次" in issue.summary or "顺序" in issue.summary for issue in result.issues)


def test_rejects_empty_section_before_next_h2() -> None:
    body = _body().replace("## 关键发现\n\n内容 3", "## 关键发现\n\n### 子节")

    result = parse_study_markdown(_study(body=body))

    assert any("关键发现" in issue.summary and "不得为空" in issue.summary for issue in result.issues)


def test_h3_does_not_end_h2_content() -> None:
    body = _body().replace("## 关键发现\n\n内容 3", "## 关键发现\n\n### 证据\n\n实际内容")

    result = parse_study_markdown(_study(body=body))

    assert result.issues == ()


def test_active_study_accepts_free_reading_units_after_fixed_h2() -> None:
    result = parse_study_markdown(_study('object_id: "study-0001"\ntitle: "Example"\nstatus: active\n', _active_body()))

    assert result.issues == ()


def test_ignores_pseudo_fixed_h2_inside_fenced_code() -> None:
    body = _body() + "```markdown\n## 研究问题\n```\n"

    result = parse_study_markdown(_study(body=body))

    assert result.issues == ()


def test_unexpected_h2_ends_the_preceding_fixed_section() -> None:
    body = _body().replace("## 关键发现\n\n内容 3", "## 关键发现\n\n## 额外章节\n\n内容")

    result = parse_study_markdown(_study(body=body))

    assert any("关键发现" in issue.summary and "不得为空" in issue.summary for issue in result.issues)
    assert any("固定骨架之外" in issue.summary for issue in result.issues)


def test_rejects_additional_h2_even_when_fixed_sections_remain_nonempty() -> None:
    body = _body().replace("## 关键发现", "## 补充章节\n\n额外内容\n\n## 关键发现")

    result = parse_study_markdown(_study(body=body))

    assert any("固定骨架之外" in issue.summary for issue in result.issues)
