from __future__ import annotations

import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
_CATALOG = _ROOT / "specs/attachments/05.Att.02-事实对象机械校验目录.md"
_FOUNDATION = _ROOT / "specs/05-事实模型基础规范.md"
_REFERENCE = re.compile(r"`(code/(?:ldvh|tests)/[^`]+?\.py)::([A-Za-z_][A-Za-z0-9_]*)`")
_OPERATIONS_BY_COVERAGE = {
    "read": "read-fact-objects",
    "draft": "prepare-fact-object-draft",
    "create": "create-fact-object",
    "update": "update-fact-object",
    "workcase-update": "update-workcase",
    "workcase-termination-begin": "begin-workcase-termination",
    "workcase-termination-complete": "complete-workcase-termination",
    "workcase-close": "close-workcase",
    "workcase-close-candidate": "prepare-closed-workcase-candidate",
    "workcase-closed-correction": "correct-closed-workcase",
    "readback": "readback",
    "candidates": "find-fact-object-candidates",
    "integrity": "check-fact-integrity",
    "git-gate": "precheck-git-commit",
}
_COVERAGE_STATUSES = {"complete", "incomplete"}
_UNAVAILABLE = "unavailable"
_NO_GAP = "—"
_CURRENT_WORKCASE_RULE_KEYS = {
    "workcase-current-shape-and-presence",
    "workcase-item-plan-approval-transitions",
    "workcase-result-review-versioning",
    "workcase-proposal-atomic-close",
    "workcase-closed-correction",
    "workcase-human-termination-transaction",
}
_INCOMPLETE_WORKCASE_RULE_KEYS: set[str] = set()


def _table_rows(markdown: str, heading: str) -> list[list[str]]:
    section = markdown.split(heading, 1)[1].split("\n## ", 1)[0]
    return [
        [cell.strip() for cell in line.strip().strip("|").split("|")]
        for line in section.splitlines()
        if line.startswith("|") and not line.startswith("|---")
    ][1:]


def _assert_real_references(rule_key: str, value: str, *, tests_only: bool = False) -> None:
    references = _REFERENCE.findall(value)
    assert references, f"{rule_key}: expected real references, got {value!r}"
    for relative_path, symbol in references:
        source = _ROOT / relative_path
        assert source.is_file(), f"{rule_key}: missing {relative_path}"
        declaration = "def" if tests_only else "(?:def|class)"
        assert re.search(
            rf"^{declaration} {re.escape(symbol)}\b",
            source.read_text(encoding="utf-8"),
            re.MULTILINE,
        ), f"{rule_key}: missing {relative_path}::{symbol}"


def _assert_real_or_unavailable(rule_key: str, value: str, *, tests_only: bool = False) -> None:
    if value == _UNAVAILABLE:
        return
    _assert_real_references(rule_key, value, tests_only=tests_only)


def test_mechanical_catalog_has_closed_status_aware_mappings_and_real_complete_evidence() -> None:
    markdown = _CATALOG.read_text(encoding="utf-8")
    catalog_rows = _table_rows(markdown, "## Code 机械规则目录")
    mapping_rows = _table_rows(markdown, "## 可执行机械覆盖映射")
    test_rows = _table_rows(markdown, "## 正反范围测试映射")

    assert all(len(row) == 8 for row in catalog_rows)
    assert all(len(row) == 6 for row in mapping_rows)
    assert all(len(row) == 5 for row in test_rows)

    catalog_by_key = {row[0].strip("`"): row for row in catalog_rows}
    mapping_by_key = {row[0].strip("`"): row for row in mapping_rows}
    tests_by_key = {row[0].strip("`"): row for row in test_rows}
    assert len(catalog_by_key) == len(catalog_rows)
    assert len(mapping_by_key) == len(mapping_rows)
    assert len(tests_by_key) == len(test_rows)
    assert catalog_by_key.keys() == mapping_by_key.keys() == tests_by_key.keys()

    assert {key for key in catalog_by_key if key.startswith("workcase-")} == _CURRENT_WORKCASE_RULE_KEYS

    covered_operations: set[str] = set()
    workcase_rule_operations: set[str] = set()
    for rule_key, catalog_row in catalog_by_key.items():
        catalog_status = catalog_row[6]
        assert catalog_status in _COVERAGE_STATUSES, rule_key

        _, mapping_status, implementation, operations, evidence, mapping_gap = mapping_by_key[rule_key]
        _, test_status, positive, negative, test_gap = tests_by_key[rule_key]
        assert mapping_status == catalog_status == test_status, rule_key

        expected_operations = {_OPERATIONS_BY_COVERAGE[item] for item in catalog_row[4].split(", ")}
        actual_operations = {item.strip("`") for item in operations.split(", ")}
        assert actual_operations == expected_operations, rule_key
        covered_operations.update(actual_operations)
        if rule_key in _CURRENT_WORKCASE_RULE_KEYS:
            workcase_rule_operations.update(actual_operations)

        if catalog_status == "complete":
            assert implementation != _UNAVAILABLE and evidence != _UNAVAILABLE, rule_key
            assert positive != _UNAVAILABLE and negative != _UNAVAILABLE, rule_key
            assert mapping_gap == _NO_GAP and test_gap == _NO_GAP, rule_key
            _assert_real_references(rule_key, implementation)
            _assert_real_references(rule_key, evidence, tests_only=True)
            _assert_real_references(rule_key, positive, tests_only=True)
            _assert_real_references(rule_key, negative, tests_only=True)
        else:
            assert mapping_gap not in {"", _NO_GAP}, rule_key
            assert test_gap not in {"", _NO_GAP}, rule_key
            _assert_real_or_unavailable(rule_key, implementation)
            _assert_real_or_unavailable(rule_key, evidence, tests_only=True)
            _assert_real_or_unavailable(rule_key, positive, tests_only=True)
            _assert_real_or_unavailable(rule_key, negative, tests_only=True)

    assert {
        "prepare-closed-workcase-candidate",
        "update-workcase",
        "close-workcase",
        "correct-closed-workcase",
    } <= covered_operations
    assert {
        "prepare-closed-workcase-candidate",
        "update-workcase",
        "close-workcase",
        "correct-closed-workcase",
    } <= workcase_rule_operations
    assert {
        key for key in _CURRENT_WORKCASE_RULE_KEYS if catalog_by_key[key][6] == "incomplete"
    } == _INCOMPLETE_WORKCASE_RULE_KEYS


def test_create_contract_closes_single_attempt_result_and_change_matrix() -> None:
    markdown = _FOUNDATION.read_text(encoding="utf-8")
    section = markdown.split("### 11.4 事实对象受控创建输入与结果", 1)[1].split("### 11.5", 1)[0]

    for field in (
        "attempted_object_id",
        "allocated_object_id",
        "counter_state",
        "allocation_consumed",
        "create_namespace_state",
        "post_create_readback",
        "rollback_state",
        "final_observation",
    ):
        assert f"`{field}`" in section
    for state in (
        "not_applicable",
        "not_needed",
        "removed",
        "not_removed",
        "uncertain",
        "counter-consumed",
        "counter-not-advanced",
        "counter-advance-uncertain",
        "target-not-attempted",
        "target-created",
        "target-not-created",
        "target-create-uncertain",
        "target-removed",
        "target-remove-unconfirmed",
    ):
        assert f"`{state}`" in section
    assert "至多发起一次 counter 原子推进和一次目标 no-overwrite 创建" in section
    assert "按发生顺序精确包含两项或三项" in section
    assert "在对具体 `attempted_object_id` 发起 counter 原子推进前失败时，`changes` 必须为空" in section
