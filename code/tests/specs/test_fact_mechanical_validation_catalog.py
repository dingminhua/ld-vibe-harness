from __future__ import annotations

import re
from pathlib import Path


_ROOT = Path(__file__).resolve().parents[3]
_CATALOG = _ROOT / "specs/attachments/05.Att.02-事实对象机械校验目录.md"
_REFERENCE = re.compile(r"`(code/(?:ldvh|tests)/[^`]+?\.py)::([A-Za-z_][A-Za-z0-9_]*)`")
_OPERATIONS_BY_COVERAGE = {
    "read": "read-fact-objects",
    "draft": "prepare-fact-object-draft",
    "create": "create-fact-object",
    "update": "update-fact-object",
    "workcase-update": "update-workcase",
    "readback": "readback",
    "candidates": "find-fact-object-candidates",
}


def _table_rows(markdown: str, heading: str) -> list[list[str]]:
    section = markdown.split(heading, 1)[1].split("\n## ", 1)[0]
    return [
        [cell.strip() for cell in line.strip().strip("|").split("|")]
        for line in section.splitlines()
        if line.startswith("|") and not line.startswith("|---")
    ][1:]


def test_mechanical_catalog_has_one_executable_mapping_per_rule_and_real_evidence() -> None:
    markdown = _CATALOG.read_text(encoding="utf-8")
    catalog_rows = _table_rows(markdown, "## Code 机械规则目录")
    catalog_keys = {row[0].strip("`") for row in catalog_rows}
    mapping_rows = _table_rows(markdown, "## 可执行机械覆盖映射")
    test_rows = _table_rows(markdown, "## 正反范围测试映射")
    mapping_keys = {row[0].strip("`") for row in mapping_rows}
    test_keys = {row[0].strip("`") for row in test_rows}

    assert catalog_keys == mapping_keys
    assert catalog_keys == test_keys
    coverage_by_key = {row[0].strip("`"): row[4] for row in catalog_rows}
    for raw_rule_key, implementation, operations, evidence in mapping_rows:
        rule_key = raw_rule_key.strip("`")
        assert implementation and operations and evidence, rule_key
        expected_operations = {_OPERATIONS_BY_COVERAGE[item] for item in coverage_by_key[rule_key].split(", ")}
        assert {item.strip("`") for item in operations.split(", ")} == expected_operations
        references = _REFERENCE.findall(f"{implementation}; {evidence}")
        assert references, rule_key
        for relative_path, symbol in references:
            source = _ROOT / relative_path
            assert source.is_file(), f"{rule_key}: missing {relative_path}"
            assert re.search(rf"^(?:def|class) {re.escape(symbol)}\b", source.read_text(encoding="utf-8"), re.MULTILINE), (
                f"{rule_key}: missing {relative_path}::{symbol}"
            )
    for raw_rule_key, positive, negative in test_rows:
        rule_key = raw_rule_key.strip("`")
        assert positive and negative, rule_key
        for relative_path, symbol in _REFERENCE.findall(f"{positive}; {negative}"):
            source = _ROOT / relative_path
            assert source.is_file(), f"{rule_key}: missing {relative_path}"
            assert re.search(rf"^def {re.escape(symbol)}\b", source.read_text(encoding="utf-8"), re.MULTILINE), (
                f"{rule_key}: missing test {relative_path}::{symbol}"
            )
