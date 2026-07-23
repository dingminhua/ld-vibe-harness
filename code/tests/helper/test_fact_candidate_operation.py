from __future__ import annotations

import json
import subprocess
from pathlib import Path

from conftest import HELPER_EXECUTABLE, assert_common_response

from ldvh.facts.workcase_projection import workcase_subject_fingerprint
from ldvh.helper.service import handle_request


def _git(project: Path, *arguments: str) -> None:
    subprocess.run(["git", "-C", str(project), *arguments], check=True, capture_output=True)


def _fixture(tmp_path: Path) -> tuple[Path, Path]:
    workspace = tmp_path / "workspace"
    project = workspace / "project"
    project.mkdir(parents=True)
    _git(project, "init", "-q")
    (workspace / "LDVH-GOVERNED-PROJECTS.yaml").write_text(
        "\n".join(
            [
                "product_name: Test Workspace",
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
                            "candidate_object_id",
                            "schema_fingerprint",
                            "worktree_fingerprint",
                        )
                    },
                    "fact_object": fields,
                },
            }
        ),
    ).response
    assert response["outcome"] == "ok"
    return response["result"]["actual_ref"]["object_id"]


def _source() -> list[dict[str, str]]:
    return [{"kind": "repository-path", "locator": "docs/input.md"}]


def _workcase() -> dict[str, object]:
    fact_object: dict[str, object] = {
        "title": "Recall contract implementation",
        "status": "open",
        "source_refs": _source(),
        "summary": "Waiting for Human execution approval.",
        "resume_from": "Present plan version 1 for Human approval.",
        "waiting_on": "Human execution approval.",
        "priority": "P1",
        "goal": "Complete the recall Helper operation.",
        "scope": "Stage 5 candidate discovery.",
        "workcase_profile": "control-contract-v1",
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
                "approach_summary": "Use current fact sources and focused Helper tests.",
            }
        ],
        "audit_summary": [
            {
                "audit_id": "audit-01",
                "subject_kind": "pre_creation_plan",
                "subject_version": 1,
                "review_count": 1,
                "summary": "Independent review confirmed the bounded candidate plan.",
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
            "feedback": ["The plan is bounded and testable."],
            "review_basis": {
                "projection_key": "plan_current",
                "subject_fingerprint": workcase_subject_fingerprint(fact_object, "plan_current"),
            },
            "controller_resolution": "1. Accepted; no change required.",
        }
    ]
    return fact_object


def _adr() -> dict[str, object]:
    return {
        "title": "Direct scan before persistent index",
        "status": "active",
        "source_refs": _source(),
        "evidence_refs": [{"kind": "repository-path", "locator": "docs/evidence.md"}],
        "decision_question": "How should the first recall implementation find facts?",
        "decision": "Directly scan current authoritative objects.",
        "applicability": "Stage 5 fact recall implementation.",
        "rationale": "A direct scan avoids a second authority.",
        "consequences": "Large repositories use a fixed scan budget.",
        "decided_at": "2026-07-13T09:00:00+08:00",
    }


def _pitfall() -> dict[str, object]:
    return {
        "title": "Stale cursor mixed with changed objects",
        "status": "active",
        "source_refs": _source(),
        "evidence_refs": [{"kind": "repository-path", "locator": "docs/evidence.md"}],
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
        "source_refs": _source(),
        "summary": "An unresolved candidate topic.",
        "priority": "P2",
    }


def _study() -> dict[str, object]:
    observed = "2026-07-13T09:00:00+08:00"
    return {
        "frontmatter": {
            "title": "Candidate projection Study",
            "status": "active",
            "source_refs": [{"kind": "repository-path", "locator": "docs/question.md", "observed_at": observed}],
            "evidence_refs": [
                {"kind": "repository-path", "locator": "docs/evidence.md", "observed_at": observed},
                {"kind": "web-page", "locator": "https://example.invalid/study-evidence", "observed_at": observed},
            ],
            "applicability": "Current candidate projection contract.",
            "validation_summary": "Tracked evidence supports the bounded conclusion.",
            "research_question": "Can Study cards remain smaller than full reports?",
            "abstract": "Study cards expose a bounded abstract before full report expansion.",
        },
        "body": "\n\n".join(
            [
                "## 研究问题\n\n验证 Study 候选卡。",
                "## 输入、方法与观察边界\n\n读取已跟踪问题、证据与外部网页资料。",
                "## 关键发现\n\n候选卡不需要注入完整正文。",
                "## 结论与限制\n\n只适用于当前测试契约。",
                "## 建议\n\n选中后再读取完整报告。",
                "## 后续分流\n\n没有额外分流。",
            ]
        ),
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
    assert len(first["result"]["recovery_manifest"]["counts"]) == 15
    assert first["result"]["recovery_manifest"]["current_workcase_ref"] == current_workcase_ref
    assert first["result"]["recovery_manifest"]["selected_fact_refs"] == selected_fact_refs
    assert first["result"]["cards"][0]["fact_ref"]["fact_type_key"] == "adr"
    assert set(first["result"]["cards"][0]["fields"]) == {
        "object_id",
        "title",
        "decision_question",
        "decision",
        "applicability",
        "updated_at",
    }
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
    assert second["result"]["cards"][0]["fact_ref"]["fact_type_key"] == "workcase"
    fields = second["result"]["cards"][0]["fields"]
    assert fields["phase"] == "human_plan_confirming"
    assert fields["work_item_counts"] == {
        "pending": 1,
        "in_progress": 0,
        "blocked": 0,
        "completed": 0,
        "cancelled": 0,
    }
    assert second["result"]["cards"][0]["excerpts"] == []


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
    _create(workspace, project, "study", _study())

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
    assert fields["research_question"] == "Can Study cards remain smaller than full reports?"
    assert "body" not in fields
    assert response["result"]["cards"][0]["excerpts"] == []


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
    assert card["fact_ref"] == {
        "governed_project_id": "sample",
        "fact_type_key": "spark",
        "object_id": object_id,
    }
    assert "summary" not in card["fields"]
    assert card["excerpts"] == [
        {"field_path": "summary", "text": "界" * 512, "complete": False}
    ]
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
    assert card["excerpts"] == [
        {"field_path": "summary", "text": summary, "complete": True}
    ]


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

    assert response["result"]["cards"][0]["excerpts"] == [
        {"field_path": "summary", "text": summary, "complete": True}
    ]


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


def test_exact_ref_can_recall_terminal_object_without_bypassing_explicit_status_filter(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    object_id = _create(workspace, project, "pitfall", _pitfall())
    path = project / "ldvh-base" / "pitfalls" / f"{object_id}.yaml"
    text = path.read_text(encoding="utf-8")
    updated_line = next(line for line in text.splitlines() if line.startswith("updated_at:"))
    closed_at = updated_line.split(": ", 1)[1]
    path.write_text(
        text.replace("status: active", "status: retired")
        + f"disposition_summary: Experience no longer applies.\nclosed_at: {closed_at}\n",
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
    assert exact["result"]["cards"][0]["fields"]["status"] == "retired"
    assert filtered["result"]["coverage"]["total_matching"] == 0


def test_invalid_object_makes_coverage_partial_and_remains_observable(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    _create(workspace, project, "workcase", _workcase())
    sparks = project / "ldvh-base" / "sparks"
    sparks.mkdir(parents=True)
    (sparks / "spark-9999.yaml").write_text("not: [valid", encoding="utf-8")

    response = handle_request("call", "find-fact-object-candidates", _payload(workspace, project, "F1")).response

    assert response["outcome"] == "partial"
    assert response["result"]["coverage"]["status"] == "partial"
    invalid = response["result"]["recovery_manifest"]["invalid_objects"]
    assert invalid[0]["fact_ref"]["object_id"] == "spark-9999"
    assert [item["fact_type_key"] for item in response["scope"]["not_completed"]] == ["spark"]
    assert len(response["scope"]["completed"]) == 4


def test_noncanonical_carrier_makes_candidate_coverage_partial_without_silent_exclusion(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    sparks = project / "ldvh-base" / "sparks"
    sparks.mkdir(parents=True)
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
                    "summary": "事实载体不是当前类型的 canonical identity file",
                }
            ],
        }
    ]
    assert [item["fact_type_key"] for item in response["scope"]["not_completed"]] == ["spark"]


def test_wrong_suffix_carrier_makes_candidate_coverage_partial_without_silent_exclusion(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    sparks = project / "ldvh-base" / "sparks"
    sparks.mkdir(parents=True)
    (sparks / "spark-0001.yml").write_text("summary: old carrier\n", encoding="utf-8")

    response = handle_request("call", "find-fact-object-candidates", _payload(workspace, project, "F1")).response

    assert response["outcome"] == "partial"
    unavailable = response["result"]["recovery_manifest"]["unavailable_objects"]
    assert unavailable[0]["canonical_path"] == "ldvh-base/sparks/spark-0001.yml"
    assert unavailable[0]["issues"][0]["summary"] == "事实载体不是当前类型的 canonical identity file"


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
            locator_text="docs/input.md",
            text_match={"text": "unresolved", "field_paths": ["summary"]},
        ),
    ).response

    assert response["outcome"] == "ok"
    assert response["result"]["coverage"]["total_matching"] == 1
    assert [reason["kind"] for reason in response["result"]["cards"][0]["match_reasons"]] == [
        "default-status",
        "relation-target",
        "locator",
        "field-text",
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
    assert response["result"]["cards"][0]["fact_ref"]["fact_type_key"] == "workcase"
