from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from conftest import HELPER_EXECUTABLE, assert_common_response

from ldvh.facts.carriers.yaml_object import parse_yaml_object
from ldvh.facts.contracts import LAYOUTS
from ldvh.facts.creation import serialize_fact_object
from ldvh.facts.identity import object_uid_from_locator
from ldvh.helper.service import handle_request

pytestmark = pytest.mark.usefixtures("use_current_rule_source_snapshot")


def _git(project: Path, *arguments: str) -> None:
    subprocess.run(["git", "-C", str(project), *arguments], check=True, capture_output=True)


def _fixture(tmp_path: Path) -> tuple[Path, Path]:
    workspace = tmp_path / "workspace"
    project = workspace / "project"
    project.mkdir(parents=True)
    for directory in ("workcases", "adrs", "pitfalls", "sparks", "studies"):
        (project / "ldvh-base" / directory).mkdir(parents=True, exist_ok=True)
    _git(project, "init", "-q")
    (workspace / "LDVH-GOVERNED-PROJECTS.yaml").write_text(
        "\n".join(
            [
                "governance_instance_name: Test Workspace",
                "product_description: Fact candidate tests.",
                "projects:",
                "  - id: sample",
                f"    path: {project}",
                "    name: Sample",
                "    description: Test project.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return workspace, project


def _prepare(workspace: Path, project: Path, fact_type_key: str) -> dict[str, object]:
    response = handle_request(
        "call",
        "prepare-fact-object-draft",
        json.dumps(
            {
                "work_object_locators": [str(project)],
                "arguments": {
                    "workspace_root": str(workspace),
                    "governed_project_id": "sample",
                    "fact_type_key": fact_type_key,
                },
            }
        ),
    ).response
    assert response["outcome"] == "ok"
    return response["result"]


def _create(workspace: Path, project: Path, fact_type_key: str, fields: dict[str, object]) -> str:
    basis = _prepare(workspace, project, fact_type_key)
    creation_fields = dict(fields)
    promote_after_create = fact_type_key == "pitfall" and creation_fields.get("status") == "active"
    if promote_after_create:
        creation_fields["status"] = "draft"
    change_log_target = (
        creation_fields.get("frontmatter")
        if set(creation_fields) == {"frontmatter", "body"}
        else creation_fields
    )
    assert isinstance(change_log_target, dict)
    change_log_target.setdefault(
        "change_log",
        [
            {
                "signature": {
                    "product_name": "pytest",
                    "model_name": "pytest-model",
                    "agent_runtime_name": "pytest",
                },
                "at": "2000-01-01T00:00:00Z",
                "summary": "Created by the candidate test fixture.",
            }
        ],
    )
    response = handle_request(
        "call",
        "create-fact-object",
        json.dumps(
            {
                "work_object_locators": [str(project)],
                "arguments": {
                    "workspace_root": str(workspace),
                    "draft_basis": {
                        key: basis[key]
                        for key in (
                            "governed_project_id",
                            "fact_type_key",
                            "schema_fingerprint",
                            "worktree_fingerprint",
                        )
                    },
                    "fact_object": creation_fields,
                },
                "observed_context": {
                    "signature": {
                        "product_name": "pytest",
                        "model_name": "pytest-model",
                        "agent_runtime_name": "pytest",
                    }
                },
            }
        ),
    ).response
    assert response["outcome"] == "ok"
    created = response["result"]["fact_object"]
    object_id = created["frontmatter"]["object_id"] if fact_type_key == "study" else created["object_id"]
    if promote_after_create:
        path = project / "ldvh-base" / "pitfalls" / f"{object_id}.yaml"
        path.write_text(path.read_text(encoding="utf-8").replace("status: draft", "status: active"), encoding="utf-8")
    return object_id


def _workcase() -> dict[str, object]:
    fact_object: dict[str, object] = {
        "title": "Recall contract implementation",
        "status": "open",
        "summary": "Waiting for Human execution approval.",
        "waiting_on": "Human execution approval.",
        "priority": "P1",
        "goal": "Complete the recall Helper operation.",
        "scope": "Stage 5 candidate discovery.",
        "success_criterion_definitions": [
            {
                "criterion_id": "criterion-01",
                "statement": "F1 and F2 cards are deterministic.",
            }
        ],
        "phase": "human_plan_confirming",
        "plan_version": 1,
        "work_items": [
            {
                "item_id": "item-01",
                "goal": "Implement deterministic candidate cards.",
                "expected_result": "F1 and F2 cards are deterministic.",
                "status": "pending",
            }
        ],
    }
    fact_object["creation_reviews"] = [
        {
            "reviewer": "independent-candidate-reviewer",
            "reviewed_at": "2026-07-20T07:35:00+08:00",
            "subject_version": 1,
            "scope": "Goal, scope, criteria, work items, method, validation and risks.",
            "conclusion": "pass",
            "covered_quality_gate_ids": ["independent-result-review"],
        }
    ]
    fact_object["execution_authorization"] = {
        "authorized_actions": [
            {
                "action_id": "authorization-candidate-fixture",
                "summary": "Execute the approved candidate fixture plan.",
                "target_scope": "Candidate fixture project only.",
                "effect_scope": "Deterministic helper test workspace.",
                "risk_summary": "No production effect; fixture data only.",
                "rollback_summary": "Remove the fixture objects.",
                "rule_refs": ["specs/21-WorkCase-工作项.md"],
            },
            {
                "action_id": "authorization-delegate-independent-review",
                "summary": "Delegate the required independent result review.",
                "target_scope": "Candidate fixture WorkCase result only.",
                "effect_scope": "Read-only review delegation.",
                "risk_summary": "Delegation does not prove independence.",
                "rollback_summary": "Do not persist an invalid review receipt.",
                "rule_refs": ["specs/21-WorkCase-工作项.md"],
            },
            {
                "action_id": "authorization-independent-result-review",
                "summary": "Perform the required independent result review.",
                "target_scope": "Candidate fixture WorkCase result only.",
                "effect_scope": "Read-only result review.",
                "risk_summary": "The review remains advisory.",
                "rollback_summary": "Do not accept a result automatically.",
                "rule_refs": ["specs/21-WorkCase-工作项.md"],
            },
        ],
        "quality_gates": [
            {
                "gate_id": "independent-result-review",
                "reviewer_mode": "independent-read-only",
                "delegation_action_id": "authorization-delegate-independent-review",
                "result_review_action_id": "authorization-independent-result-review",
            }
        ],
        "action_ceiling": "Bounded to candidate fixture actions.",
        "allowed_adjustments": "No adjustments beyond the recorded fixture summaries.",
        "verification_and_rollback": "Run the candidate operation test suite.",
        "out_of_bounds_handling": "Stop and return to Human.",
        "prohibited_actions": ["Writing outside the fixture workspace."],
    }
    return fact_object


def _write_closed_workcase(project: Path, object_id: str) -> None:
    path = project / "ldvh-base" / "workcases" / f"{object_id}.yaml"
    object_uid = object_uid_from_locator("workcase", object_id)
    uid_field = "" if object_uid is None else f"object_uid: {object_uid}\n"
    path.write_text(
        f"""object_id: {object_id}
{uid_field}fact_type_key: workcase
title: Closed recall contract implementation
created_at: 2026-07-26T09:00:00+08:00
updated_at: 2026-07-26T10:00:00+08:00
status: closed
goal: Complete the recall Helper operation.
scope: Stage 5 candidate discovery.
success_criterion_definitions:
  - criterion_id: criterion-01
    statement: F1 and F2 cards are deterministic.
success_criterion_results:
  - criterion_id: criterion-01
    outcome: satisfied
    summary: Active and closed cards use their current projections.
result_summary: The candidate projection now distinguishes active and closed WorkCases.
validation_summary: Candidate queries covered the active default and explicit closed status.
closure_outcome: completed
disposition_summary: The original scope is complete with no remaining responsibility.
""",
        encoding="utf-8",
    )


def _adr() -> dict[str, object]:
    return {
        "title": "Direct scan before persistent index",
        "status": "active",
        "decision_question": "How should the first recall implementation find facts?",
        "decision": "Directly scan current authoritative objects.",
        "applicability": "Stage 5 fact recall implementation.",
        "rationale": "A direct scan avoids a second authority.",
        "consequences": "Large repositories use a fixed scan budget.",
    }


def _pitfall() -> dict[str, object]:
    return {
        "title": "Stale cursor mixed with changed objects",
        "status": "active",
        "applicability": "Paginated fact candidate scans.",
        "validation_summary": "Changed object sets reject the old cursor.",
        "symptoms": "Cards from two different snapshots are combined.",
        "trigger_conditions": "A fact changes between candidate pages.",
        "root_cause": "The cursor was not bound to the object-set fingerprint.",
        "resolution": "Bind every cursor to the current query and object set.",
        "avoidance": "Restart from page one after a stale cursor response.",
    }


def _spark(title: str) -> dict[str, object]:
    return {
        "title": title,
        "status": "open",
        "summary": "An unresolved candidate topic.",
        "priority": "P2",
    }


def _study() -> dict[str, object]:
    return {
        "frontmatter": {
            "title": "Candidate projection Study",
            "status": "active",
            "report_kind": "external_research",
            "urls": [
                {
                    "ref": "https://example.invalid/study-evidence",
                    "title": "Study evidence",
                    "summary": "External material used by this test Study.",
                }
            ],
            "research_question": "Can Study cards remain smaller than full reports?",
            "abstract": "Study cards expose a bounded abstract before full report expansion.",
            "research_intent": (
                "Preserve the project reason for studying a readable card without expanding the full report."
            ),
            "recommendation_summary": (
                "Show the study's core advice before a reader decides whether to open the full report."
            ),
        },
        "body": """
## 研究问题

### 项目问题

验证 Study 候选卡。

### 外部问题

外部阅读器如何保持候选卡简洁？

## 输入与边界

### 已读外部资料

读取已跟踪问题与外部网页资料。

### 本次边界

不把候选卡当作完整报告。

## 关键发现

### 候选卡保持简洁

候选卡不需要注入完整正文，启发是按需展开；不等于省略研究正文。

### 正文按需读取

完整报告保留在对象中，启发是减少初始噪音；不证明发现已经采纳。

## 建议

### 可立即采用的工作方式

选中后再读取完整报告。

## 后续分流

| 分流类别 | 触发条件 | 下一步或不创建理由 |
|---|---|---|
| 无需对象化 | 仅验证候选卡投影 | 不创建额外对象。 |
""",
    }


def _payload(
    workspace: Path,
    project: Path,
    layer: str,
    **arguments: object,
) -> str:
    return json.dumps(
        {
            "work_object_locators": [str(project)],
            "arguments": {
                "workspace_root": str(workspace),
                "governed_project_id": "sample",
                "card_layer": layer,
                **arguments,
            },
        }
    )


def test_f1_returns_complete_active_adr_and_open_workcase_baseline_with_pagination(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    workcase_id = _create(workspace, project, "workcase", _workcase())
    adr_id = _create(workspace, project, "adr", _adr())
    current_workcase_ref = {
        "governed_project_id": "sample",
        "fact_type_key": "workcase",
        "object_id": workcase_id,
    }
    selected_fact_refs = [{"governed_project_id": "sample", "fact_type_key": "adr", "object_id": adr_id}]

    first = handle_request(
        "call",
        "find-fact-object-candidates",
        _payload(
            workspace,
            project,
            "F1",
            page_size=1,
            current_workcase_ref=current_workcase_ref,
            selected_fact_refs=selected_fact_refs,
        ),
    ).response

    assert_common_response(first)
    assert first["outcome"] == "ok"
    assert first["result"]["coverage"]["status"] == "complete"
    assert first["result"]["coverage"]["total_matching"] == 2
    assert first["result"]["coverage"]["returned"] == 1
    assert len(first["result"]["recovery_manifest"]["counts"]) == 13
    assert first["result"]["recovery_manifest"]["current_workcase_ref"] == current_workcase_ref
    assert first["result"]["recovery_manifest"]["selected_fact_refs"] == selected_fact_refs
    assert set(first["result"]["cards"][0]["fact_ref"]) == {"object_uid"}
    assert first["result"]["cards"][0]["excerpts"] == []
    cursor = first["result"]["coverage"]["next_cursor"]
    assert isinstance(cursor, str) and cursor

    second = handle_request(
        "call",
        "find-fact-object-candidates",
        _payload(
            workspace,
            project,
            "F1",
            page_size=1,
            cursor=cursor,
            current_workcase_ref=current_workcase_ref,
            selected_fact_refs=selected_fact_refs,
        ),
    ).response

    assert second["outcome"] == "ok"
    assert second["result"]["coverage"]["offset"] == 1
    assert second["result"]["coverage"]["next_cursor"] is None
    assert set(second["result"]["cards"][0]["fact_ref"]) == {"object_uid"}
    cards = [first["result"]["cards"][0], second["result"]["cards"][0]]
    fields = next(card["fields"] for card in cards if card["fields"]["object_id"] == workcase_id)
    adr_fields = next(card["fields"] for card in cards if card["fields"]["object_id"] == adr_id)
    assert set(adr_fields) == {
        "object_uid", "object_id", "title", "decision_question", "decision", "applicability", "updated_at"
    }
    assert fields["phase"] == "human_plan_confirming"
    assert fields["work_item_counts"] == {
        "pending": 1,
        "in_progress": 0,
        "blocked": 0,
        "completed": 0,
        "cancelled": 0,
    }
    assert second["result"]["cards"][0]["excerpts"] == []


def test_f2_workcase_uses_distinct_current_active_and_closed_projections(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    active_id = _create(workspace, project, "workcase", _workcase())
    closed_id = _create(workspace, project, "workcase", _workcase())
    _write_closed_workcase(project, closed_id)

    active = handle_request(
        "call",
        "find-fact-object-candidates",
        _payload(workspace, project, "F2", fact_type_keys=["workcase"]),
    ).response
    closed = handle_request(
        "call",
        "find-fact-object-candidates",
        _payload(workspace, project, "F2", fact_type_keys=["workcase"], statuses=["closed"]),
    ).response

    assert active["outcome"] == "ok"
    assert active["result"]["coverage"]["total_matching"] == 1
    active_card = active["result"]["cards"][0]
    assert active_card["fields"]["object_id"] == active_id
    assert set(active_card["fields"]) == {
        "object_uid",
        "object_id",
        "title",
        "status",
        "phase",
        "goal",
        "scope",
        "summary",
        "priority",
        "updated_at",
        "work_item_counts",
    }

    assert closed["outcome"] == "ok"
    closed_card = closed["result"]["cards"][0]
    assert closed_card["fields"]["object_id"] == closed_id
    assert set(closed_card["fields"]) == {
        "object_uid",
        "object_id",
        "title",
        "status",
        "goal",
        "scope",
        "result_summary",
        "closure_outcome",
        "disposition_summary",
        "updated_at",
    }
    assert "phase" not in closed_card["fields"]
    assert "work_item_counts" not in closed_card["fields"]
    assert closed_card["excerpts"] == []


def test_f2_workcase_text_match_uses_only_the_current_direct_text_field_closure(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    closed_id = _create(workspace, project, "workcase", _workcase())
    _write_closed_workcase(project, closed_id)

    matched = handle_request(
        "call",
        "find-fact-object-candidates",
        _payload(
            workspace,
            project,
            "F2",
            fact_type_keys=["workcase"],
            statuses=["closed"],
            text_match={"text": "distinguishes active", "field_paths": ["result_summary"]},
        ),
    ).response
    forbidden = handle_request(
        "call",
        "find-fact-object-candidates",
        _payload(
            workspace,
            project,
            "F2",
            fact_type_keys=["workcase"],
            text_match={"text": "human_plan_confirming", "field_paths": ["phase"]},
        ),
    ).response

    assert matched["outcome"] == "ok"
    assert matched["result"]["cards"][0]["fields"]["object_id"] == closed_id
    assert matched["result"]["cards"][0]["match_reasons"][-1] == {
        "kind": "field-text",
        "field_path": "result_summary",
        "matched_text": "distinguishes active",
    }
    assert forbidden["outcome"] == "invalid_request"
    assert "F2 投影之外" in forbidden["gaps"][0]["summary"]


def test_discovery_text_match_fragment_combines_with_an_actual_governed_project(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    spark_id = _create(workspace, project, "spark", _spark("Nested text matching is discoverable"))
    discovery = handle_request("capabilities", None, "").response
    operation = next(
        item for item in discovery["result"]["operations"] if item["operation_key"] == "find-fact-object-candidates"
    )
    fragment = operation["input_examples"][0]["arguments_fragment"]

    response = handle_request(
        "call",
        "find-fact-object-candidates",
        json.dumps(
            {
                "work_object_locators": [str(project)],
                "arguments": {
                    "workspace_root": str(workspace),
                    "governed_project_id": "sample",
                    **fragment,
                },
            }
        ),
    ).response

    assert response["outcome"] == "ok"
    assert [card["fields"]["object_id"] for card in response["result"]["cards"]] == [spark_id]
    assert response["result"]["cards"][0]["match_reasons"][-1] == {
        "kind": "field-text",
        "field_path": "title",
        "matched_text": "text",
    }


def test_f2_uses_pitfall_authoritative_fields_without_tags_or_scores(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    _create(workspace, project, "pitfall", _pitfall())

    response = handle_request(
        "call",
        "find-fact-object-candidates",
        _payload(
            workspace,
            project,
            "F2",
            fact_type_keys=["pitfall"],
            text_match={"text": "A fact changes", "field_paths": ["trigger_conditions", "symptoms"]},
        ),
    ).response

    assert response["outcome"] == "ok"
    assert response["result"]["coverage"]["total_matching"] == 1
    card = response["result"]["cards"][0]
    assert card["match_reasons"][-1] == {
        "kind": "field-text",
        "field_path": "trigger_conditions",
        "matched_text": "A fact changes",
    }
    assert "tags" not in card["fields"]
    assert card["excerpts"] == []
    assert all("score" not in reason for reason in card["match_reasons"])


def test_f2_projects_study_frontmatter_without_injecting_report_body(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    docs = project / "docs"
    docs.mkdir()
    (docs / "question.md").write_text("Research question.\n", encoding="utf-8")
    (docs / "evidence.md").write_text("Observed evidence.\n", encoding="utf-8")
    _git(project, "add", "docs")
    workcase_id = _create(workspace, project, "workcase", _workcase())
    study = _study()
    study["frontmatter"]["relations"] = [
        {
            "relation_key": "informs",
            "target": {
                "governed_project_id": "sample",
                "fact_type_key": "workcase",
                "object_id": workcase_id,
            },
        }
    ]
    _create(workspace, project, "study", study)

    response = handle_request(
        "call",
        "find-fact-object-candidates",
        _payload(
            workspace,
            project,
            "F2",
            fact_type_keys=["study"],
            text_match={"text": "bounded abstract", "field_paths": ["abstract"]},
        ),
    ).response

    assert response["outcome"] == "ok"
    fields = response["result"]["cards"][0]["fields"]
    assert set(fields) == {
        "object_uid",
        "object_id",
        "title",
        "status",
        "research_intent",
        "research_question",
        "abstract",
        "recommendation_summary",
        "relations",
        "updated_at",
    }
    assert fields["research_question"] == "Can Study cards remain smaller than full reports?"
    assert fields["research_intent"] == (
        "Preserve the project reason for studying a readable card without expanding the full report."
    )
    assert fields["recommendation_summary"] == (
        "Show the study's core advice before a reader decides whether to open the full report."
    )
    assert "body" not in fields
    assert response["result"]["cards"][0]["excerpts"] == []


def test_f2_study_rejects_text_fields_outside_its_exact_projection(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)

    for field_path in ("applicability", "validation_summary"):
        response = handle_request(
            "call",
            "find-fact-object-candidates",
            _payload(
                workspace,
                project,
                "F2",
                fact_type_keys=["study"],
                text_match={"text": "not projected", "field_paths": [field_path]},
            ),
        ).response

        assert response["outcome"] == "invalid_request"
        assert "F2 投影之外" in response["gaps"][0]["summary"]


def test_f2_spark_summary_is_a_bounded_verbatim_excerpt_with_f3_reference(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    summary = "界" * 512 + "摘录之外的命中"
    spark = _spark("Bounded Spark excerpt")
    spark["summary"] = summary
    object_id = _create(workspace, project, "spark", spark)

    response = handle_request(
        "call",
        "find-fact-object-candidates",
        _payload(
            workspace,
            project,
            "F2",
            fact_type_keys=["spark"],
            text_match={"text": "摘录之外", "field_paths": ["summary"]},
        ),
    ).response

    assert response["outcome"] == "ok"
    assert response["result"]["coverage"]["total_matching"] == 1
    card = response["result"]["cards"][0]
    assert set(card["fact_ref"]) == {"object_uid"}
    assert card["fields"]["object_id"] == object_id
    assert "summary" not in card["fields"]
    assert card["excerpts"] == [{"field_path": "summary", "text": "界" * 512, "complete": False}]
    assert card["match_reasons"][-1] == {
        "kind": "field-text",
        "field_path": "summary",
        "matched_text": "摘录之外",
    }


def test_f2_spark_intent_is_searchable_and_precedes_summary_excerpt(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    spark = _spark("Intent-aware Spark excerpt")
    spark["intent"] = "为了分流阅读边界而创建"
    spark["summary"] = "当前判断仍在形成中。"
    _create(workspace, project, "spark", spark)

    response = handle_request(
        "call",
        "find-fact-object-candidates",
        _payload(
            workspace,
            project,
            "F2",
            fact_type_keys=["spark"],
            text_match={"text": "阅读边界", "field_paths": ["intent"]},
        ),
    ).response

    card = response["result"]["cards"][0]
    assert card["excerpts"] == [
        {"field_path": "intent", "text": "为了分流阅读边界而创建", "complete": True},
        {"field_path": "summary", "text": "当前判断仍在形成中。", "complete": True},
    ]
    assert card["match_reasons"][-1] == {
        "kind": "field-text",
        "field_path": "intent",
        "matched_text": "阅读边界",
    }


def test_f2_spark_excerpt_marks_exact_512_scalar_summary_complete(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    summary = "火" * 512
    spark = _spark("Exactly complete Spark excerpt")
    spark["summary"] = summary
    _create(workspace, project, "spark", spark)

    response = handle_request(
        "call",
        "find-fact-object-candidates",
        _payload(workspace, project, "F2", fact_type_keys=["spark"]),
    ).response

    card = response["result"]["cards"][0]
    assert card["excerpts"] == [{"field_path": "summary", "text": summary, "complete": True}]


def test_f2_spark_excerpt_marks_511_scalar_summary_complete(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    summary = "焰" * 511
    spark = _spark("Short complete Spark excerpt")
    spark["summary"] = summary
    _create(workspace, project, "spark", spark)

    response = handle_request(
        "call",
        "find-fact-object-candidates",
        _payload(workspace, project, "F2", fact_type_keys=["spark"]),
    ).response

    assert response["result"]["cards"][0]["excerpts"] == [{"field_path": "summary", "text": summary, "complete": True}]


def test_f2_rejects_the_retired_candidate_filter_as_an_unknown_field(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    retired_field = "".join(("short", "_refs"))
    payload = json.loads(_payload(workspace, project, "F2", fact_type_keys=["spark"]))
    payload["arguments"][retired_field] = ["SABCDE"]

    response = handle_request("call", "find-fact-object-candidates", json.dumps(payload)).response

    assert response["outcome"] == "invalid_request"
    assert any("未知字段" in gap["summary"] for gap in response["gaps"])


def test_f2_exact_uid_reference_resolves_to_the_authority_card(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    object_id = _create(workspace, project, "spark", _spark("Exact UID candidate"))
    parsed = parse_yaml_object(
        (project / "ldvh-base" / "sparks" / f"{object_id}.yaml").read_text(encoding="utf-8")
    )
    assert parsed.fields is not None
    object_uid = str(parsed.fields["object_uid"])

    response = handle_request(
        "call",
        "find-fact-object-candidates",
        _payload(
            workspace,
            project,
            "F2",
            fact_type_keys=["spark"],
            exact_refs=[{"object_uid": object_uid}],
        ),
    ).response

    assert response["outcome"] == "ok"
    assert response["result"]["cards"][0]["fact_ref"] == {"object_uid": object_uid}
    assert {"kind": "exact-ref", "field_path": "object_id"} in response["result"]["cards"][0]["match_reasons"]


def test_f2_uid_relation_source_returns_its_direct_target(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    target_id = _create(workspace, project, "workcase", _workcase())
    source = _spark("UID source")
    source["relations"] = [
        {
            "relation_key": "related-to",
            "target": {
                "governed_project_id": "sample",
                "fact_type_key": "workcase",
                "object_id": target_id,
            },
        }
    ]
    source_id = _create(workspace, project, "spark", source)
    parsed = parse_yaml_object(
        (project / "ldvh-base" / "sparks" / f"{source_id}.yaml").read_text(encoding="utf-8")
    )
    assert parsed.fields is not None

    response = handle_request(
        "call",
        "find-fact-object-candidates",
        _payload(
            workspace,
            project,
            "F2",
            fact_type_keys=["workcase"],
            relation_source_refs=[{"object_uid": str(parsed.fields["object_uid"])}],
        ),
    ).response

    assert response["outcome"] == "ok"
    assert response["result"]["relation_navigation"]["edges"][0]["edge_status"] == "returned"
    assert response["result"]["cards"][0]["fields"]["object_id"] == target_id


def test_f2_spark_excerpt_marks_exact_513_scalar_summary_incomplete(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    summary = "界" * 512 + "尾"
    spark = _spark("Exact incomplete Spark excerpt")
    spark["summary"] = summary
    _create(workspace, project, "spark", spark)

    response = handle_request(
        "call",
        "find-fact-object-candidates",
        _payload(workspace, project, "F2", fact_type_keys=["spark"]),
    ).response

    assert response["result"]["cards"][0]["excerpts"] == [
        {"field_path": "summary", "text": "界" * 512, "complete": False}
    ]


def test_cursor_is_rejected_after_any_canonical_fact_object_changes(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    _create(workspace, project, "workcase", _workcase())
    _create(workspace, project, "adr", _adr())
    first = handle_request(
        "call", "find-fact-object-candidates", _payload(workspace, project, "F1", page_size=1)
    ).response
    cursor = first["result"]["coverage"]["next_cursor"]
    _create(workspace, project, "spark", _spark("Changes the global object set"))

    stale = handle_request(
        "call",
        "find-fact-object-candidates",
        _payload(workspace, project, "F1", page_size=1, cursor=cursor),
    ).response

    assert stale["outcome"] == "rejected"
    assert stale["gaps"][0]["code"] == "stale_cursor"
    assert stale["result"] is None


def test_exact_ref_can_recall_discarded_object_without_bypassing_explicit_status_filter(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    object_id = _create(workspace, project, "pitfall", _pitfall())
    path = project / "ldvh-base" / "pitfalls" / f"{object_id}.yaml"
    text = path.read_text(encoding="utf-8")
    path.write_text(
        text.replace("status: active", "status: discarded")
        + "disposition_summary: Experience no longer applies.\n",
        encoding="utf-8",
    )
    exact_ref = {
        "governed_project_id": "sample",
        "fact_type_key": "pitfall",
        "object_id": object_id,
    }

    exact = handle_request(
        "call",
        "find-fact-object-candidates",
        _payload(workspace, project, "F2", fact_type_keys=["pitfall"], exact_refs=[exact_ref]),
    ).response
    filtered = handle_request(
        "call",
        "find-fact-object-candidates",
        _payload(
            workspace,
            project,
            "F2",
            fact_type_keys=["pitfall"],
            statuses=["active"],
            exact_refs=[exact_ref],
        ),
    ).response

    assert exact["outcome"] == "ok"
    assert exact["result"]["coverage"]["total_matching"] == 1
    assert exact["result"]["cards"][0]["fields"]["status"] == "discarded"
    assert filtered["result"]["coverage"]["total_matching"] == 0


def test_invalid_object_makes_coverage_partial_and_remains_observable(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    _create(workspace, project, "workcase", _workcase())
    sparks = project / "ldvh-base" / "sparks"
    sparks.mkdir(parents=True, exist_ok=True)
    (sparks / "spark-9999.yaml").write_text("not: [valid", encoding="utf-8")

    response = handle_request("call", "find-fact-object-candidates", _payload(workspace, project, "F1")).response

    assert response["outcome"] == "partial"
    assert response["result"]["coverage"]["status"] == "partial"
    invalid = response["result"]["recovery_manifest"]["invalid_objects"]
    assert invalid[0]["fact_ref"]["object_id"] == "spark-9999"
    assert [item["fact_type_key"] for item in response["scope"]["not_completed"]] == ["spark"]
    assert len(response["scope"]["completed"]) == 4


def test_invalid_uid_is_observable_without_emitting_an_invalid_stable_reference(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    object_id = _create(workspace, project, "spark", _spark("Malformed UID remains observable"))
    path = project / "ldvh-base" / "sparks" / f"{object_id}.yaml"
    parsed = parse_yaml_object(path.read_text(encoding="utf-8"))
    assert parsed.fields is not None
    fields = dict(parsed.fields)
    fields["object_uid"] = str(fields["object_uid"]).upper()
    path.write_text(serialize_fact_object(LAYOUTS["spark"], fields, None), encoding="utf-8")

    response = handle_request(
        "call",
        "find-fact-object-candidates",
        _payload(workspace, project, "F2", fact_type_keys=["spark"]),
    ).response

    assert response["outcome"] == "partial"
    assert response["result"]["cards"] == []
    invalid = response["result"]["recovery_manifest"]["invalid_objects"]
    assert len(invalid) == 1
    assert "fact_ref" not in invalid[0]
    assert invalid[0]["fact_type_key"] == "spark"
    assert invalid[0]["canonical_path"] == f"ldvh-base/sparks/{object_id}.yaml"
    assert any(issue["field_path"] == "object_uid" for issue in invalid[0]["issues"])


def test_noncanonical_carrier_makes_candidate_coverage_partial_without_silent_exclusion(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    sparks = project / "ldvh-base" / "sparks"
    sparks.mkdir(parents=True, exist_ok=True)
    (sparks / "legacy.yaml").write_text("summary: old carrier\n", encoding="utf-8")

    response = handle_request("call", "find-fact-object-candidates", _payload(workspace, project, "F1")).response

    assert response["outcome"] == "partial"
    assert response["result"]["coverage"]["status"] == "partial"
    unavailable = response["result"]["recovery_manifest"]["unavailable_objects"]
    assert unavailable == [
        {
            "fact_type_key": "spark",
            "canonical_path": "ldvh-base/sparks/legacy.yaml",
            "check_status": "unavailable",
            "issues": [
                {
                    "category": "location",
                    "field_path": None,
                        "summary": "该载体不符合当前事实类型的权威文件路径与对象身份规则",
                }
            ],
        }
    ]
    assert [item["fact_type_key"] for item in response["scope"]["not_completed"]] == ["spark"]


def test_wrong_suffix_carrier_makes_candidate_coverage_partial_without_silent_exclusion(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    sparks = project / "ldvh-base" / "sparks"
    sparks.mkdir(parents=True, exist_ok=True)
    (sparks / "spark-0001.yml").write_text("summary: old carrier\n", encoding="utf-8")

    response = handle_request("call", "find-fact-object-candidates", _payload(workspace, project, "F1")).response

    assert response["outcome"] == "partial"
    unavailable = response["result"]["recovery_manifest"]["unavailable_objects"]
    assert unavailable[0]["canonical_path"] == "ldvh-base/sparks/spark-0001.yml"
    assert unavailable[0]["issues"][0]["summary"] == "该载体不符合当前事实类型的权威文件路径与对象身份规则"


def test_f1_rejects_candidate_filters_and_f2_rejects_unprojected_text_fields(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)

    f1 = handle_request(
        "call",
        "find-fact-object-candidates",
        _payload(workspace, project, "F1", fact_type_keys=["adr"]),
    ).response
    f2 = handle_request(
        "call",
        "find-fact-object-candidates",
        _payload(
            workspace,
            project,
            "F2",
            fact_type_keys=["pitfall"],
            text_match={"text": "cause", "field_paths": ["root_cause"]},
        ),
    ).response

    assert f1["outcome"] == "invalid_request"
    assert "F1 不接受" in f1["gaps"][0]["summary"]
    assert f2["outcome"] == "invalid_request"
    assert "F2 投影之外" in f2["gaps"][0]["summary"]


def test_f2_combines_relation_locator_and_field_filters_deterministically(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    workcase_id = _create(workspace, project, "workcase", _workcase())
    spark = _spark("Candidate connected to current work")
    spark["relations"] = [
        {
            "relation_key": "related-to",
            "target": {
                "governed_project_id": "sample",
                "fact_type_key": "workcase",
                "object_id": workcase_id,
            },
        }
    ]
    _create(workspace, project, "spark", spark)

    response = handle_request(
        "call",
        "find-fact-object-candidates",
        _payload(
            workspace,
            project,
            "F2",
            fact_type_keys=["spark"],
            relation_targets=[
                {
                    "governed_project_id": "sample",
                    "fact_type_key": "workcase",
                    "object_id": workcase_id,
                }
            ],
            text_match={"text": "unresolved", "field_paths": ["summary"]},
        ),
    ).response

    assert response["outcome"] == "ok"
    assert response["result"]["coverage"]["total_matching"] == 1
    assert [reason["kind"] for reason in response["result"]["cards"][0]["match_reasons"]] == [
        "default-status",
        "relation-target",
        "field-text",
    ]


def test_f2_relation_source_returns_one_hop_edges_with_single_edge_cursor(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    first_workcase = _create(workspace, project, "workcase", _workcase())
    second_workcase = _create(workspace, project, "workcase", _workcase())
    spark = _spark("Known source for direct navigation")
    spark["relations"] = [
        {
            "relation_key": "related-to",
            "target": {
                "governed_project_id": "sample",
                "fact_type_key": "workcase",
                "object_id": first_workcase,
            },
        },
        {
            "relation_key": "related-to",
            "target": {
                "governed_project_id": "sample",
                "fact_type_key": "workcase",
                "object_id": second_workcase,
            },
        },
    ]
    spark_id = _create(workspace, project, "spark", spark)
    source_ref = {
        "governed_project_id": "sample",
        "fact_type_key": "spark",
        "object_id": spark_id,
    }

    first = handle_request(
        "call",
        "find-fact-object-candidates",
        _payload(
            workspace,
            project,
            "F2",
            fact_type_keys=["workcase"],
            relation_source_refs=[source_ref],
            page_size=1,
        ),
    ).response

    assert first["outcome"] == "ok"
    assert first["result"]["coverage"] == {
        "status": "complete",
        "total_matching": 2,
        "returned": 1,
        "offset": 0,
        "next_cursor": first["result"]["coverage"]["next_cursor"],
        "object_set_fingerprint": first["result"]["recovery_manifest"]["object_set_fingerprint"],
    }
    cursor = first["result"]["coverage"]["next_cursor"]
    assert isinstance(cursor, str) and cursor
    navigation = first["result"]["relation_navigation"]
    assert set(navigation["source_results"][0]["source_ref"]) == {"object_uid"}
    assert set(navigation["edges"][0]["source_ref"]) == {"object_uid"}
    assert set(navigation["edges"][0]["target_ref"]) == {"object_uid"}
    assert navigation["source_results"][0]["check_status"] == "mechanically_valid"
    assert navigation["edges"][0]["edge_status"] == "returned"
    assert navigation["edges"][0]["reasons"] == ["relation-source"]
    assert navigation["edges"][0]["relation_definition_refs"][0]["locator"] == (
        "spark-fact-type::7. 外部资料、关系与处置"
    )
    assert first["result"]["cards"][0]["match_reasons"] == [
        {"kind": "relation-source", "field_path": "relations[0].target"}
    ]

    second = handle_request(
        "call",
        "find-fact-object-candidates",
        _payload(
            workspace,
            project,
            "F2",
            fact_type_keys=["workcase"],
            relation_source_refs=[source_ref],
            page_size=1,
            cursor=cursor,
        ),
    ).response

    assert second["outcome"] == "ok"
    assert second["result"]["coverage"]["offset"] == 1
    assert second["result"]["coverage"]["returned"] == 1
    assert second["result"]["coverage"]["next_cursor"] is None
    assert second["result"]["relation_navigation"]["edges"][0]["relation_index"] == 1
    assert second["result"]["cards"][0]["match_reasons"] == [
        {"kind": "relation-source", "field_path": "relations[1].target"}
    ]


def test_f2_relation_source_uses_the_study_relation_definition_without_crashing(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    target_id = _create(workspace, project, "workcase", _workcase())
    study = _study()
    study["frontmatter"]["relations"] = [
        {
            "relation_key": "informs",
            "target": {
                "governed_project_id": "sample",
                "fact_type_key": "workcase",
                "object_id": target_id,
            },
        }
    ]
    study_id = _create(workspace, project, "study", study)

    response = handle_request(
        "call",
        "find-fact-object-candidates",
        _payload(
            workspace,
            project,
            "F2",
            fact_type_keys=["workcase"],
            relation_source_refs=[
                {
                    "governed_project_id": "sample",
                    "fact_type_key": "study",
                    "object_id": study_id,
                }
            ],
        ),
    ).response

    assert response["outcome"] == "ok"
    edge = response["result"]["relation_navigation"]["edges"][0]
    assert edge["edge_status"] == "returned"
    assert set(edge["target_ref"]) == {"object_uid"}
    assert len(edge["relation_definition_refs"]) == 1
    assert edge["relation_definition_refs"][0]["kind"] == "rule"
    assert edge["relation_definition_refs"][0]["locator"] == (
        "study-fact-type::7. 外部网址、研究边界、关系与时效"
    )


def test_f2_rejects_removed_spark_routed_to_relation_key(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    workcase_id = _create(workspace, project, "workcase", _workcase())
    spark = _spark("Source with an unselected key")
    spark["relations"] = [
        {
            "relation_key": "related-to",
            "target": {
                "governed_project_id": "sample",
                "fact_type_key": "workcase",
                "object_id": workcase_id,
            },
        }
    ]
    spark_id = _create(workspace, project, "spark", spark)

    response = handle_request(
        "call",
        "find-fact-object-candidates",
        _payload(
            workspace,
            project,
            "F2",
            fact_type_keys=["workcase"],
            relation_source_refs=[{"governed_project_id": "sample", "fact_type_key": "spark", "object_id": spark_id}],
            relation_keys=["routed-to"],
        ),
    ).response

    assert response["outcome"] == "invalid_request"
    assert response["result"] is None


def test_f2_relation_source_reports_missing_target_without_hiding_the_edge(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    workcase_id = _create(workspace, project, "workcase", _workcase())
    spark = _spark("Source whose target later disappears")
    spark["relations"] = [
        {
            "relation_key": "related-to",
            "target": {
                "governed_project_id": "sample",
                "fact_type_key": "workcase",
                "object_id": workcase_id,
            },
        }
    ]
    spark_id = _create(workspace, project, "spark", spark)
    (project / "ldvh-base" / "workcases" / f"{workcase_id}.yaml").unlink()

    response = handle_request(
        "call",
        "find-fact-object-candidates",
        _payload(
            workspace,
            project,
            "F2",
            fact_type_keys=["workcase"],
            relation_source_refs=[{"governed_project_id": "sample", "fact_type_key": "spark", "object_id": spark_id}],
        ),
    ).response

    assert response["outcome"] == "partial"
    assert response["result"]["coverage"]["status"] == "partial"
    edge = response["result"]["relation_navigation"]["edges"][0]
    assert edge["target_ref"]["object_id"] == workcase_id
    assert edge["edge_status"] == "not_found"
    assert edge["reasons"] == ["target-not-found"]
    assert response["result"]["cards"] == []
    assert any(
        isinstance(item, dict) and item.get("edge_status") == "not_found" for item in response["gaps"][0]["scope"]
    )


def test_f2_omits_invalid_legacy_spark_routed_to_edge(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    workcase_id = _create(workspace, project, "workcase", _workcase())
    spark_id = _create(workspace, project, "spark", _spark("Source with a disallowed routed-to declaration"))
    spark_path = project / "ldvh-base" / "sparks" / f"{spark_id}.yaml"
    spark_path.write_text(
        spark_path.read_text(encoding="utf-8")
        + "relations:\n"
        + "- relation_key: routed-to\n"
        + "  target:\n"
        + "    governed_project_id: sample\n"
        + "    fact_type_key: workcase\n"
        + f"    object_id: {workcase_id}\n",
        encoding="utf-8",
    )

    response = handle_request(
        "call",
        "find-fact-object-candidates",
        _payload(
            workspace,
            project,
            "F2",
            fact_type_keys=["workcase"],
            relation_source_refs=[{"governed_project_id": "sample", "fact_type_key": "spark", "object_id": spark_id}],
        ),
    ).response

    assert response["outcome"] == "partial"
    assert response["result"]["relation_navigation"]["edges"] == []
    assert response["result"]["cards"] == []


def test_f2_relation_source_reports_invalid_target_after_source_validation(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    workcase_id = _create(workspace, project, "workcase", _workcase())
    spark = _spark("Source whose target becomes structurally invalid")
    spark["relations"] = [
        {
            "relation_key": "related-to",
            "target": {
                "governed_project_id": "sample",
                "fact_type_key": "workcase",
                "object_id": workcase_id,
            },
        }
    ]
    spark_id = _create(workspace, project, "spark", spark)
    (project / "ldvh-base" / "workcases" / f"{workcase_id}.yaml").write_text("not: [valid", encoding="utf-8")

    response = handle_request(
        "call",
        "find-fact-object-candidates",
        _payload(
            workspace,
            project,
            "F2",
            fact_type_keys=["workcase"],
            relation_source_refs=[{"governed_project_id": "sample", "fact_type_key": "spark", "object_id": spark_id}],
        ),
    ).response

    assert response["outcome"] == "partial"
    edge = response["result"]["relation_navigation"]["edges"][0]
    assert edge["edge_status"] == "invalid"
    assert edge["reasons"] == ["target-invalid"]
    assert response["result"]["cards"] == []


def test_f2_relation_source_applies_type_status_and_reverse_relation_filters_with_and_semantics(
    tmp_path: Path,
) -> None:
    workspace, project = _fixture(tmp_path)
    dependency_id = _create(workspace, project, "workcase", _workcase())
    target = _workcase()
    target["relations"] = [
        {
            "relation_key": "depends-on",
            "target": {
                "governed_project_id": "sample",
                "fact_type_key": "workcase",
                "object_id": dependency_id,
            },
        }
    ]
    target_id = _create(workspace, project, "workcase", target)
    source = _spark("Source used with forward and reverse filters")
    source["relations"] = [
        {
            "relation_key": "related-to",
            "target": {
                "governed_project_id": "sample",
                "fact_type_key": "workcase",
                "object_id": target_id,
            },
        }
    ]
    source_id = _create(workspace, project, "spark", source)
    source_ref = {"governed_project_id": "sample", "fact_type_key": "spark", "object_id": source_id}
    dependency_ref = {"governed_project_id": "sample", "fact_type_key": "workcase", "object_id": dependency_id}
    target_ref = {"governed_project_id": "sample", "fact_type_key": "workcase", "object_id": target_id}

    returned = handle_request(
        "call",
        "find-fact-object-candidates",
        _payload(
            workspace,
            project,
            "F2",
            fact_type_keys=["workcase"],
            statuses=["open"],
            relation_targets=[dependency_ref],
            relation_source_refs=[source_ref],
        ),
    ).response
    wrong_type = handle_request(
        "call",
        "find-fact-object-candidates",
        _payload(
            workspace,
            project,
            "F2",
            fact_type_keys=["spark"],
            relation_source_refs=[source_ref],
        ),
    ).response
    wrong_status = handle_request(
        "call",
        "find-fact-object-candidates",
        _payload(
            workspace,
            project,
            "F2",
            fact_type_keys=["workcase"],
            statuses=["blocked"],
            relation_source_refs=[source_ref],
        ),
    ).response
    dependency_navigation = handle_request(
        "call",
        "find-fact-object-candidates",
        _payload(
            workspace,
            project,
            "F2",
            fact_type_keys=["workcase"],
            relation_source_refs=[target_ref],
        ),
    ).response

    assert returned["outcome"] == "ok"
    assert [reason["kind"] for reason in returned["result"]["cards"][0]["match_reasons"]] == [
        "status",
        "relation-target",
        "relation-source",
    ]
    assert wrong_type["result"]["cards"] == []
    assert wrong_type["result"]["relation_navigation"]["edges"][0]["reasons"] == ["fact-type-filter"]
    assert wrong_status["result"]["cards"] == []
    assert wrong_status["result"]["relation_navigation"]["edges"][0]["reasons"] == ["explicit-status-filter"]
    assert dependency_navigation["outcome"] == "ok"
    assert (
        dependency_navigation["result"]["relation_navigation"]["edges"][0]["relation_definition_refs"][0]["locator"]
        == "workcase-fact-type::8. 来源、外部资料与关系"
    )


def test_f2_relation_source_rejects_cross_project_duplicate_and_illegal_key_inputs(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    source_ref = {"governed_project_id": "sample", "fact_type_key": "spark", "object_id": "spark-0001"}

    cross_project = handle_request(
        "call",
        "find-fact-object-candidates",
        _payload(
            workspace,
            project,
            "F2",
            fact_type_keys=["spark"],
            relation_source_refs=[{**source_ref, "governed_project_id": "other-project"}],
        ),
    ).response
    duplicate = handle_request(
        "call",
        "find-fact-object-candidates",
        _payload(
            workspace,
            project,
            "F2",
            fact_type_keys=["spark"],
            relation_source_refs=[source_ref, source_ref],
        ),
    ).response
    missing_source = handle_request(
        "call",
        "find-fact-object-candidates",
        _payload(workspace, project, "F2", fact_type_keys=["spark"], relation_keys=["related-to"]),
    ).response
    illegal_key = handle_request(
        "call",
        "find-fact-object-candidates",
        _payload(
            workspace,
            project,
            "F2",
            fact_type_keys=["spark"],
            relation_source_refs=[source_ref],
            relation_keys=["not-a-relation-key"],
        ),
    ).response

    assert [response["outcome"] for response in (cross_project, duplicate, missing_source, illegal_key)] == [
        "invalid_request",
        "invalid_request",
        "invalid_request",
        "invalid_request",
    ]


def test_f2_relation_source_does_not_leak_later_failed_edge_gaps_before_its_page(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    first_workcase = _create(workspace, project, "workcase", _workcase())
    second_workcase = _create(workspace, project, "workcase", _workcase())

    def source_for(target_id: str, title: str) -> str:
        spark = _spark(title)
        spark["relations"] = [
            {
                "relation_key": "related-to",
                "target": {
                    "governed_project_id": "sample",
                    "fact_type_key": "workcase",
                    "object_id": target_id,
                },
            }
        ]
        return _create(workspace, project, "spark", spark)

    first_source = source_for(first_workcase, "First source with a disappearing target")
    second_source = source_for(second_workcase, "Second source with a disappearing target")
    (project / "ldvh-base" / "workcases" / f"{first_workcase}.yaml").unlink()
    (project / "ldvh-base" / "workcases" / f"{second_workcase}.yaml").unlink()

    response = handle_request(
        "call",
        "find-fact-object-candidates",
        _payload(
            workspace,
            project,
            "F2",
            fact_type_keys=["workcase"],
            relation_source_refs=[
                {"governed_project_id": "sample", "fact_type_key": "spark", "object_id": first_source},
                {"governed_project_id": "sample", "fact_type_key": "spark", "object_id": second_source},
            ],
            page_size=1,
        ),
    ).response

    assert response["outcome"] == "partial"
    assert response["result"]["coverage"]["total_matching"] == 2
    assert response["result"]["coverage"]["returned"] == 1
    assert isinstance(response["result"]["coverage"]["next_cursor"], str)
    assert len(response["result"]["relation_navigation"]["edges"]) == 1
    delivered_edge_gaps = [
        item for item in response["gaps"][0]["scope"] if isinstance(item, dict) and item.get("edge_status")
    ]
    assert delivered_edge_gaps == [
        {
            "source_ref": response["result"]["relation_navigation"]["edges"][0]["source_ref"],
            "relation_key": "related-to",
            "target_ref": response["result"]["relation_navigation"]["edges"][0]["target_ref"],
            "edge_status": "not_found",
            "reasons": ["target-not-found"],
        }
    ]


def test_f2_relation_source_reports_each_missing_target_of_one_source_as_target_not_found(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    first_workcase = _create(workspace, project, "workcase", _workcase())
    second_workcase = _create(workspace, project, "workcase", _workcase())
    source = _spark("One source with two independently missing targets")
    source["relations"] = [
        {
            "relation_key": "related-to",
            "target": {
                "governed_project_id": "sample",
                "fact_type_key": "workcase",
                "object_id": first_workcase,
            },
        },
        {
            "relation_key": "related-to",
            "target": {
                "governed_project_id": "sample",
                "fact_type_key": "workcase",
                "object_id": second_workcase,
            },
        },
    ]
    source_id = _create(workspace, project, "spark", source)
    (project / "ldvh-base" / "workcases" / f"{first_workcase}.yaml").unlink()
    (project / "ldvh-base" / "workcases" / f"{second_workcase}.yaml").unlink()

    response = handle_request(
        "call",
        "find-fact-object-candidates",
        _payload(
            workspace,
            project,
            "F2",
            fact_type_keys=["workcase"],
            relation_source_refs=[{"governed_project_id": "sample", "fact_type_key": "spark", "object_id": source_id}],
            page_size=2,
        ),
    ).response

    assert response["outcome"] == "partial"
    assert [edge["edge_status"] for edge in response["result"]["relation_navigation"]["edges"]] == [
        "not_found",
        "not_found",
    ]
    assert [edge["reasons"] for edge in response["result"]["relation_navigation"]["edges"]] == [
        ["target-not-found"],
        ["target-not-found"],
    ]


def test_f2_relation_source_deduplicates_target_cards_without_dropping_distinct_edges(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    workcase_id = _create(workspace, project, "workcase", _workcase())

    def source_for(title: str) -> str:
        spark = _spark(title)
        spark["relations"] = [
            {
                "relation_key": "related-to",
                "target": {
                    "governed_project_id": "sample",
                    "fact_type_key": "workcase",
                    "object_id": workcase_id,
                },
            }
        ]
        return _create(workspace, project, "spark", spark)

    first_source = source_for("First source to the same target")
    second_source = source_for("Second source to the same target")
    response = handle_request(
        "call",
        "find-fact-object-candidates",
        _payload(
            workspace,
            project,
            "F2",
            fact_type_keys=["workcase"],
            relation_source_refs=[
                {"governed_project_id": "sample", "fact_type_key": "spark", "object_id": first_source},
                {"governed_project_id": "sample", "fact_type_key": "spark", "object_id": second_source},
            ],
            page_size=2,
        ),
    ).response

    assert response["outcome"] == "ok"
    assert response["result"]["coverage"]["total_matching"] == 2
    assert len(response["result"]["relation_navigation"]["edges"]) == 2
    assert len(response["result"]["cards"]) == 1
    assert response["result"]["cards"][0]["fields"]["object_id"] == workcase_id


def test_f2_relation_source_keeps_a_self_edge_as_source_invalid_without_recursing(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    source_id = _create(workspace, project, "spark", _spark("Source with a self edge"))
    source_path = project / "ldvh-base" / "sparks" / f"{source_id}.yaml"
    source_path.write_text(
        source_path.read_text(encoding="utf-8")
        + "relations:\n"
        + "- relation_key: related-to\n"
        + "  target:\n"
        + "    governed_project_id: sample\n"
        + "    fact_type_key: spark\n"
        + f"    object_id: {source_id}\n",
        encoding="utf-8",
    )

    response = handle_request(
        "call",
        "find-fact-object-candidates",
        _payload(
            workspace,
            project,
            "F2",
            fact_type_keys=["spark"],
            relation_source_refs=[{"governed_project_id": "sample", "fact_type_key": "spark", "object_id": source_id}],
        ),
    ).response

    assert response["outcome"] == "partial"
    assert len(response["result"]["relation_navigation"]["edges"]) == 1
    edge = response["result"]["relation_navigation"]["edges"][0]
    assert set(edge["target_ref"]) == {"object_uid"}
    assert edge["edge_status"] == "invalid"
    assert edge["reasons"] == ["source-invalid"]
    assert response["result"]["cards"] == []


def test_f2_relation_source_keeps_terminal_direct_target_without_default_status_filter(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    pitfall_id = _create(workspace, project, "pitfall", _pitfall())
    spark = _spark("Source to a terminal direct target")
    spark["relations"] = [
        {
            "relation_key": "related-to",
            "target": {
                "governed_project_id": "sample",
                "fact_type_key": "pitfall",
                "object_id": pitfall_id,
            },
        }
    ]
    spark_id = _create(workspace, project, "spark", spark)
    pitfall_path = project / "ldvh-base" / "pitfalls" / f"{pitfall_id}.yaml"
    pitfall_text = pitfall_path.read_text(encoding="utf-8")
    pitfall_path.write_text(
        pitfall_text.replace("status: active", "status: discarded")
        + "disposition_summary: This experience is now historical.\n",
        encoding="utf-8",
    )

    response = handle_request(
        "call",
        "find-fact-object-candidates",
        _payload(
            workspace,
            project,
            "F2",
            fact_type_keys=["pitfall"],
            relation_source_refs=[{"governed_project_id": "sample", "fact_type_key": "spark", "object_id": spark_id}],
        ),
    ).response

    assert response["outcome"] == "ok"
    assert response["result"]["coverage"]["status"] == "complete"
    assert response["result"]["cards"][0]["fields"]["status"] == "discarded"
    assert response["result"]["cards"][0]["match_reasons"] == [
        {"kind": "relation-source", "field_path": "relations[0].target"}
    ]


def test_candidate_scan_stays_bound_to_selected_linked_worktree(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    marker = project / "tracked.txt"
    marker.write_text("initial\n", encoding="utf-8")
    _git(project, "add", ".")
    _git(
        project,
        "-c",
        "user.name=LDVH Test",
        "-c",
        "user.email=ldvh@example.invalid",
        "commit",
        "-qm",
        "initial",
    )
    linked = tmp_path / "linked"
    _git(project, "worktree", "add", "-qb", "linked-candidates", str(linked))
    _create(workspace, linked, "spark", _spark("Linked-only candidate"))

    linked_response = handle_request(
        "call",
        "find-fact-object-candidates",
        _payload(workspace, linked, "F2", fact_type_keys=["spark"]),
    ).response
    main_response = handle_request(
        "call",
        "find-fact-object-candidates",
        _payload(workspace, project, "F2", fact_type_keys=["spark"]),
    ).response

    assert linked_response["result"]["coverage"]["total_matching"] == 1
    assert linked_response["result"]["recovery_manifest"]["git_worktree_root"] == str(linked)
    assert main_response["result"]["coverage"]["total_matching"] == 0
    assert main_response["result"]["recovery_manifest"]["git_worktree_root"] == str(project)


def test_real_cli_returns_source_bound_f1_cards(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    _create(workspace, project, "workcase", _workcase())
    completed = subprocess.run(
        [str(HELPER_EXECUTABLE), "call", "find-fact-object-candidates"],
        cwd=project,
        input=_payload(workspace, project, "F1"),
        text=True,
        capture_output=True,
        check=False,
    )
    response = json.loads(completed.stdout)

    assert completed.returncode == 0
    assert completed.stderr == ""
    assert_common_response(response)
    assert response["result"]["coverage"]["total_matching"] == 1
    assert set(response["result"]["cards"][0]["fact_ref"]) == {"object_uid"}
