from __future__ import annotations

import json
from dataclasses import replace

import pytest

from ldvh.diagnostics import Issue, SourceLocation
from ldvh.facts.models import FactReference
from ldvh.helper.operations import local_edit_candidates
from ldvh.helper.operations.local_edit_candidates import LocalEditSelectionError, read_local_edit_candidates
from ldvh.helper.operations.local_edit_request import LocalEditRequest, RuleLocalEditRequest
from ldvh.helper.service import handle_request
from ldvh.specs.repository import inspect_repository

pytestmark = pytest.mark.usefixtures("use_current_rule_source_snapshot")


def _study_payload(*, expected_baseline: str | None = None, candidate_after: str | None = None) -> str:
    return json.dumps(
        {
            "work_object_locators": ["."],
            "arguments": {
                "source_kind": "study",
                "fact_ref": {
                    "governed_project_id": "ldvh",
                    "fact_type_key": "study",
                    "object_id": "study-0030",
                },
                "body_heading": "建议",
                "expected_baseline": expected_baseline,
                "candidate_after": candidate_after,
            },
        },
        ensure_ascii=False,
    )


def _rule_request() -> LocalEditRequest:
    return LocalEditRequest(
        "rule",
        rule=RuleLocalEditRequest(
            "ldvh-root",
            ("8. 系统级运行架构", "8.1 工作上下文的信息交付顺序与渐进式披露"),
            None,
            None,
        ),
    )


@pytest.mark.parametrize(
    ("repository_update", "summary"),
    (
        (
            lambda repository: replace(
                repository,
                active_documents_passing_implemented_checks=tuple(
                    document
                    for document in repository.active_documents_passing_implemented_checks
                    if document.key != "ldvh-root"
                ),
                parsed_documents=tuple(
                    replace(document, status="retired") if document.key == "ldvh-root" else document
                    for document in repository.parsed_documents
                ),
            ),
            "当前未声明为 active",
        ),
        (
            lambda repository: replace(
                repository,
                active_documents_passing_implemented_checks=tuple(
                    document
                    for document in repository.active_documents_passing_implemented_checks
                    if document.key != "ldvh-root"
                ),
            ),
            "目标规则载体未通过既有机械检查",
        ),
        (
            lambda repository: replace(
                repository,
                active_documents_passing_implemented_checks=tuple(
                    document
                    for document in repository.active_documents_passing_implemented_checks
                    if document.key != "ldvh-root"
                ),
                parsed_documents=tuple(
                    document for document in repository.parsed_documents if document.key != "ldvh-root"
                ),
                issues=(Issue("规则源范围不完整", SourceLocation("specs/broken.md")),),
                incomplete_scope=("broken",),
                implemented_checks_complete=False,
            ),
            "当前规则源存在未完成范围",
        ),
    ),
)
def test_rule_unreadable_target_conditions_are_rejected(
    current_specs_repository, repository_update, summary: str
) -> None:
    result = read_local_edit_candidates(
        repository_update(inspect_repository(current_specs_repository)), _rule_request()
    )

    assert result.outcome == "rejected"
    assert result.items is None
    assert result.completed_scope == ()
    assert result.not_completed_scope == result.requested_scope
    assert summary in result.gaps[0]["summary"]


def test_study_candidate_uses_full_object_fingerprint_and_fixed_h2_target() -> None:
    response = handle_request(
        "call",
        "prepare-local-edit-candidates",
        _study_payload(expected_baseline="0" * 64, candidate_after="## 建议\n\n候选。\n"),
    ).response

    assert response["outcome"] == "ok"
    assert response["changes"] == []
    assert response["scope"]["governance_resolution"]["scope_status"] == "governed_single"
    item = response["result"]["items"][0]
    assert item["source_kind"] == "study"
    assert item["target"]["body_heading"] == "建议"
    assert item["baseline"]["kind"] == "content_fingerprint"
    assert item["stale"] is True
    assert item["before"].startswith("## 建议\n")
    assert item["unified_diff"].startswith("--- ldvh-base/studies/study-0030.md:before\n")
    assert set(item["scope_coverage"]["unexpanded"][0]["body_headings"]) == {
        "研究问题",
        "输入与边界",
        "关键发现",
        "后续分流",
    }
    assert any(gap.get("code") == "baseline_stale" for gap in response["gaps"])


def test_study_uid_request_reads_the_resolved_locator_and_preserves_requested_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    object_uid = "0198f1c7-8a2b-7c3d-9e4f-123456789abc"
    payload = json.loads(_study_payload())
    payload["arguments"]["fact_ref"] = {"object_uid": object_uid}
    original_resolver = local_edit_candidates.resolve_stable_fact_reference

    def resolve_existing_study(run, _reference, schemas):
        return original_resolver(run, FactReference("ldvh", "study", "study-0030"), schemas)

    monkeypatch.setattr(local_edit_candidates, "resolve_stable_fact_reference", resolve_existing_study)

    response = handle_request(
        "call",
        "prepare-local-edit-candidates",
        json.dumps(payload, ensure_ascii=False),
    ).response

    assert response["outcome"] == "ok"
    item = response["result"]["items"][0]
    assert item["target"]["fact_ref"] == {"object_uid": object_uid}
    assert item["source_ranges"][0]["source_ref"]["locator"].endswith("/ldvh-base/studies/study-0030.md")


def test_study_selection_error_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        local_edit_candidates,
        "_study_range",
        lambda _read, _heading: (_ for _ in ()).throw(LocalEditSelectionError(("Study 目标无法定位",))),
    )

    response = handle_request("call", "prepare-local-edit-candidates", _study_payload()).response

    assert response["outcome"] == "rejected"
    assert response["result"] is None
    assert response["scope"]["completed"] == []
    assert response["scope"]["not_completed"]
    assert response["changes"] == []


def test_study_matching_baseline_is_not_stale() -> None:
    initial = handle_request("call", "prepare-local-edit-candidates", _study_payload()).response
    baseline = initial["result"]["items"][0]["baseline"]["value"]

    response = handle_request(
        "call",
        "prepare-local-edit-candidates",
        _study_payload(expected_baseline=baseline),
    ).response

    assert response["outcome"] == "ok"
    item = response["result"]["items"][0]
    assert item["stale"] is False
    assert item["baseline"]["matches_expected"] is True
    assert not any(gap.get("code") == "baseline_stale" for gap in response["gaps"])


def test_study_request_for_other_governed_project_is_unavailable() -> None:
    payload = json.loads(_study_payload())
    payload["arguments"]["fact_ref"]["governed_project_id"] = "other-project"

    response = handle_request("call", "prepare-local-edit-candidates", json.dumps(payload, ensure_ascii=False)).response

    assert response["outcome"] == "unavailable"
    assert response["result"] is None
    assert "管辖项目不一致" in response["gaps"][0]["summary"]
    assert response["changes"] == []


def test_study_request_without_unique_governance_boundary_does_no_fact_read() -> None:
    response = handle_request(
        "call",
        "prepare-local-edit-candidates",
        json.dumps(
            {
                "work_object_locators": ["/does-not-exist"],
                "arguments": {
                    "source_kind": "study",
                    "fact_ref": {
                        "governed_project_id": "ldvh",
                        "fact_type_key": "study",
                        "object_id": "study-0030",
                    },
                    "body_heading": "建议",
                },
            },
            ensure_ascii=False,
        ),
    ).response

    assert response["outcome"] == "unavailable"
    assert response["result"] is None
    assert response["scope"]["completed"] == []
    assert response["changes"] == []
