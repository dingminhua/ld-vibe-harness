from __future__ import annotations

import json
from pathlib import Path

import pytest

from ldvh.helper.service import handle_request

pytestmark = pytest.mark.usefixtures("use_current_rule_source_snapshot")


def _rule_payload(**extra: object) -> str:
    arguments: dict[str, object] = {
        "source_kind": "rule",
        "responsibility_key": "ldvh-root",
        "heading_path": ["8. 系统级运行架构", "8.1 工作上下文的信息交付顺序与渐进式披露"],
    }
    arguments.update(extra)
    return json.dumps({"arguments": arguments}, ensure_ascii=False)


def test_rule_candidate_returns_exact_range_diff_stale_and_no_changes(current_specs_repository: Path) -> None:
    response = handle_request(
        "call",
        "prepare-local-edit-candidates",
        _rule_payload(candidate_after="candidate\n", expected_baseline="0" * 64),
    ).response

    assert response["outcome"] == "ok"
    assert response["changes"] == []
    item = response["result"]["items"][0]
    assert item["source_kind"] == "rule"
    assert item["stale"] is True
    assert item["candidate_after"] == "candidate\n"
    assert item["unified_diff"].startswith("--- specs/00-理念与构成.md:before\n")
    assert item["source_ranges"][0]["start_line"] == 213
    assert item["scope_coverage"]["unexpanded"]
    assert response["scope"]["governance_resolution"] is None
    assert any(gap.get("code") == "baseline_stale" for gap in response["gaps"])


def test_rule_matching_baseline_is_not_stale() -> None:
    initial = handle_request("call", "prepare-local-edit-candidates", _rule_payload()).response
    baseline = initial["result"]["items"][0]["baseline"]["value"]

    response = handle_request(
        "call",
        "prepare-local-edit-candidates",
        _rule_payload(expected_baseline=baseline),
    ).response

    assert response["outcome"] == "ok"
    item = response["result"]["items"][0]
    assert item["stale"] is False
    assert item["baseline"]["matches_expected"] is True
    assert not any(gap.get("code") == "baseline_stale" for gap in response["gaps"])


def test_rule_candidate_rejects_ambiguous_or_missing_heading() -> None:
    response = handle_request(
        "call",
        "prepare-local-edit-candidates",
        _rule_payload(heading_path=["不存在"], candidate_after=None),
    ).response

    assert response["outcome"] == "rejected"
    assert response["result"] is None
    assert response["scope"]["not_completed"]
    assert response["changes"] == []


def test_capabilities_discovers_the_source_declared_read_only_operation() -> None:
    response = handle_request("capabilities", "prepare-local-edit-candidates", _rule_payload()).response

    assert response["outcome"] == "ok"
    operation = response["result"]["operations"][0]
    assert operation["effect"] == "read"
    assert operation["implementation"]["present"] is True
    assert operation["availability"] == "available_for_request"
