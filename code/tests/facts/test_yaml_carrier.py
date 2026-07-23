from ldvh.facts.carriers.yaml_object import parse_yaml_object
from ldvh.facts.contracts import LAYOUTS
from ldvh.facts.creation import serialize_fact_object
from ldvh.facts.models import FactIssue


def test_parses_utf8_yaml_mapping_with_json_scalar_semantics() -> None:
    result = parse_yaml_object(
        """title: 中文火花
active: true
count: 3
ratio: 1.5
optional: null
tags:
  - 设计
  - validation
"""
    )

    assert result.parsed
    assert result.issues == ()
    assert result.body is None
    assert result.fields == {
        "title": "中文火花",
        "active": True,
        "count": 3,
        "ratio": 1.5,
        "optional": None,
        "tags": ["设计", "validation"],
    }


def test_rejects_duplicate_keys_without_leaking_an_exception() -> None:
    result = parse_yaml_object("title: first\ntitle: second\n")

    assert result.fields is None
    assert result.body is None
    assert len(result.issues) == 1
    assert result.issues[0].category == "parse"
    assert "DuplicateKeyError" not in result.issues[0].summary


def test_rejects_non_mapping_root() -> None:
    result = parse_yaml_object("- one\n- two\n")

    assert result.fields is None
    assert result.issues == (FactIssue(category="parse", summary="YAML 事实对象顶层必须是映射"),)


def test_rejects_invalid_yaml_without_leaking_an_exception() -> None:
    result = parse_yaml_object("title: [unterminated\n")

    assert result.fields is None
    assert len(result.issues) == 1
    assert result.issues[0].category == "parse"
    assert "ParserError" not in result.issues[0].summary


def test_rejects_escaped_lone_surrogate_before_fact_strings_are_consumed() -> None:
    result = parse_yaml_object('summary: "\\uD800"\n')

    assert result.fields is None
    assert len(result.issues) == 1
    assert result.issues[0].category == "parse"


def test_keeps_timestamp_shaped_scalars_as_strings() -> None:
    result = parse_yaml_object("created_at: 2026-07-14\nupdated_at: 2026-07-14T12:34:56+08:00\n")

    assert result.parsed
    assert result.fields == {
        "created_at": "2026-07-14",
        "updated_at": "2026-07-14T12:34:56+08:00",
    }


def test_serializer_preserves_values_without_physical_trailing_whitespace() -> None:
    fields = {
        "title": "中文 WorkCase " + "长标题" * 300,
        "urls": [
            {
                "ref": "https://example.invalid/" + "nested-directory/" * 300,
                "title": "Long external reference",
                "summary": "Serializer round-trip fixture.",
            }
        ],
        "summary": "semantic trailing space is preserved inside the scalar ",
        "notes": "line one\nline two with a semantic trailing space \nline three",
    }

    text = serialize_fact_object(LAYOUTS["workcase"], fields, None)
    parsed = parse_yaml_object(text)

    assert parsed.issues == ()
    assert parsed.fields == fields
    assert text.endswith("\n") and not text.endswith("\n\n")
    assert all(not line.endswith((" ", "\t")) for line in text.splitlines())
