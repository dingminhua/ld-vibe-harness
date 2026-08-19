from __future__ import annotations

import json
import os
import stat
import subprocess
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from conftest import HELPER_EXECUTABLE, assert_common_response

from ldvh.facts import creation_application
from ldvh.facts.contracts import LAYOUTS
from ldvh.facts.creation import FactCoordinationUnavailable, serialize_fact_object
from ldvh.facts.creation_application import FactCreationResult
from ldvh.facts.identity import object_uid_from_locator
from ldvh.facts.models import FactIssue
from ldvh.facts.repository import FactReadResult
from ldvh.filesystem import AtomicWriteResult
from ldvh.helper.service import handle_request

pytestmark = pytest.mark.usefixtures("use_current_rule_source_snapshot")


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
                "governance_instance_name: Test Workspace",
                "product_description: Controlled creation tests.",
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


def _prepare(workspace: Path, project: Path, fact_type_key: str = "spark") -> dict[str, object]:
    payload = json.dumps(
        {
            "work_object_locators": [str(project)],
            "arguments": {
                "workspace_root": str(workspace),
                "governed_project_id": "sample",
                "fact_type_key": fact_type_key,
            },
        }
    )
    response = handle_request("call", "prepare-fact-object-draft", payload).response
    assert_common_response(response)
    assert response["outcome"] == "ok"
    assert response["changes"] == []
    return response["result"]


def test_prepare_projects_definition_and_constraint_sources_without_a_second_schema(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)

    for fact_type_key in ("spark", "workcase", "adr", "pitfall", "study"):
        prepared = _prepare(workspace, project, fact_type_key)
        contracts = prepared["field_contracts"]

        assert contracts
        assert any("." not in item["field_path"] and "[]" not in item["field_path"] for item in contracts)
        assert any("." in item["field_path"] or "[]" in item["field_path"] for item in contracts)
        assert all(
            set(item) == {"field_path", "json_type", "presence", "definition_ref", "constraint_ref"}
            for item in contracts
        )
        assert all(
            isinstance(item["definition_ref"], str)
            and item["definition_ref"].count("::") == 2
            and all(part.strip() for part in item["definition_ref"].split("::"))
            for item in contracts
        )
        assert all(
            not ({"allowed_values", "constraints", "template", "fact_object"} & set(item))
            for item in contracts
        )

    contracts = {item["field_path"]: item for item in _prepare(workspace, project, "workcase")["field_contracts"]}

    resume_from = contracts["resume_from"]
    assert resume_from == {
        "field_path": "resume_from",
        "json_type": "string",
        "presence": "conditional",
        "definition_ref": "workcase-fact-type::5. WorkCase 类型定义::workcase-resume-from",
        "constraint_ref": "workcase-fact-type::6. 状态、阶段与生命周期",
    }
    for field_path in (
        "summary",
        "phase",
        "plan_version",
        "work_items",
        "creation_reviews",
        "work_items[].approach_summary",
        "work_items[].depends_on",
        "creation_reviews[].feedback",
        "creation_reviews[].controller_resolution",
        "result_reviews[].feedback",
        "result_reviews[].controller_resolution",
        "closure_proposal.residual_decisions",
        "closure_proposal.residual_decisions[].route_target",
        "residual_responsibilities",
    ):
        assert contracts[field_path]["presence"] == "conditional"
    assert contracts["priority"]["definition_ref"] == (
        "fact-object-field-registry::跨类型共享字段定义表::priority"
    )
    assert contracts["priority"]["constraint_ref"] == "workcase-fact-type::6. 状态、阶段与生命周期"
    assert contracts["execution_approval.source_refs"]["definition_ref"] == (
        "workcase-fact-type::5. WorkCase 类型定义::workcase-approval-source-refs"
    )
    assert contracts["execution_approval.source_refs"]["constraint_ref"] == "inherit"
    assert contracts["execution_approval.source_refs"]["presence"] == "required"


def _spark(title: str = "Controlled creation") -> dict[str, object]:
    return {
        "title": title,
        "status": "open",
        "summary": "AI supplied semantic content; Code owns identity and timestamps.",
        "priority": "P2",
    }


def _workcase() -> dict[str, object]:
    return {
        "title": "Controlled WorkCase",
        "status": "open",
        "summary": "Waiting for Human execution approval.",
        "waiting_on": "Human execution approval.",
        "priority": "P2",
        "goal": "Verify controlled creation.",
        "scope": "One test object.",
        "success_criterion_definitions": [
            {
                "criterion_id": "criterion-01",
                "statement": "The object passes write-back validation.",
            }
        ],
        "phase": "human_plan_confirming",
        "plan_version": 1,
        "work_items": [
            {
                "item_id": "item-01",
                "goal": "Create and validate one WorkCase.",
                "expected_result": "The object passes write-back validation.",
                "status": "pending",
            }
        ],
        "creation_reviews": [
            {
                "reviewer": "independent-creation-reviewer",
                "reviewed_at": "2026-07-14T09:00:00+08:00",
                "subject_version": 1,
                "scope": "Goal, scope, criteria, work items, method, validation and risks.",
                "conclusion": "pass",
                "actual_method": "subagent-read-only",
                "covered_quality_gate_ids": ["independent-result-review"],
            }
        ],
        "execution_authorization": {
            "authorized_actions": [
                {
                    "action_id": "authorization-creation-fixture",
                    "summary": "Execute the approved creation fixture plan.",
                    "target_scope": "Creation fixture project only.",
                    "effect_scope": "Deterministic helper test workspace.",
                    "risk_summary": "No production effect; fixture data only.",
                    "rollback_summary": "Remove the fixture objects.",
                    "rule_refs": ["specs/21-WorkCase-工作项.md"],
                },
                {
                    "action_id": "authorization-delegate-independent-review",
                    "summary": "Delegate the required independent result review.",
                    "target_scope": "Creation fixture WorkCase result only.",
                    "effect_scope": "Read-only Reviewer delegation.",
                    "risk_summary": "The declaration does not prove independence.",
                    "rollback_summary": "Do not persist a delegation receipt.",
                    "rule_refs": ["specs/21-WorkCase-工作项.md"],
                },
                {
                    "action_id": "authorization-independent-result-review",
                    "summary": "Perform the required independent result review.",
                    "target_scope": "Creation fixture WorkCase result only.",
                    "effect_scope": "Read-only result review.",
                    "risk_summary": "The result review remains advisory.",
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
            "action_ceiling": "Bounded to creation fixture actions.",
            "allowed_adjustments": "No adjustments beyond the recorded fixture summaries.",
            "verification_and_rollback": "Run the creation operation test suite.",
            "out_of_bounds_handling": "Stop and return to Human.",
            "prohibited_actions": ["Writing outside the fixture workspace."],
        },
    }


def _depends_on(object_id: str) -> dict[str, object]:
    return {
        "relation_key": "depends-on",
        "target": {
            "governed_project_id": "sample",
            "fact_type_key": "workcase",
            "object_id": object_id,
        },
    }


def _write_existing_workcase(
    project: Path,
    object_id: str,
    *,
    depends_on: str,
) -> Path:
    fields = deepcopy(_workcase())
    fields.update(
        {
            "object_id": object_id,
            "fact_type_key": "workcase",
            "created_at": "2026-07-14T09:00:00+08:00",
            "updated_at": "2026-07-14T09:00:00+08:00",
            "relations": [_depends_on(depends_on)],
        }
    )
    path = project / LAYOUTS["workcase"].canonical_path(object_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        serialize_fact_object(LAYOUTS["workcase"], fields, None),
        encoding="utf-8",
    )
    return path


@pytest.mark.parametrize(
    ("fact_type_key", "fact_object"),
    [
        (
            "workcase",
            _workcase(),
        ),
        (
            "adr",
            {
                "title": "Controlled ADR",
                "status": "active",
                "decision_question": "Who assigns the final object identity?",
                "decision": "Code assigns it in the creation critical section.",
                "applicability": "Single-object V4 fact creation.",
                "rationale": "A shared allocator avoids same-repository identity collisions.",
                "consequences": "Draft candidate identities are explicitly non-reserved.",
                "trigger_signal": "Creating or modifying fact objects using the controlled creation flow.",
            },
        ),
        (
            "pitfall",
            {
                "title": "Candidate identity treated as reserved",
                "status": "draft",
                "applicability": "Concurrent V4 fact creation.",
                "validation_summary": "Two drafts can safely receive different final identities.",
                "symptoms": "Concurrent drafts expect the same final ID.",
                "trigger_conditions": "A candidate ID is mistaken for a reservation.",
                "scope_of_impact": "Concurrent fact creation when multiple writers share the same identity allocator.",
                "root_cause": "Identity was allocated before entering a shared critical section.",
                "resolution": "Allocate the final ID only during controlled creation.",
                "avoidance": "Treat prepare results as non-reserved draft bases.",
            },
        ),
    ],
)
def test_create_supports_all_yaml_fact_types(
    tmp_path: Path,
    fact_type_key: str,
    fact_object: dict[str, object],
) -> None:
    workspace, project = _fixture(tmp_path)
    basis = _prepare(workspace, project, fact_type_key)

    response = handle_request(
        "call",
        "create-fact-object",
        _create_payload(workspace, project, basis, fact_object),
    ).response

    assert response["outcome"] == "ok"
    assert set(response["result"]["actual_ref"]) == {"object_uid"}
    created_object = response["result"]["fact_object"]
    created_fields = created_object["frontmatter"] if fact_type_key == "study" else created_object
    assert created_fields["fact_type_key"] == fact_type_key
    assert object_uid_from_locator(fact_type_key, created_fields["object_id"]) == created_fields["object_uid"]


def test_workcase_create_follow_up_requires_public_exact_read_before_gate_1(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    basis = _prepare(workspace, project, "workcase")

    response = handle_request(
        "call",
        "create-fact-object",
        _create_payload(workspace, project, basis, _workcase()),
    ).response

    assert response["outcome"] == "ok"
    actual_ref = response["result"]["actual_ref"]
    assert set(actual_ref) == {"object_uid"}
    assert "content_fingerprint" not in actual_ref
    follow_up = response["follow_up"]
    assert "完整当前对象和非空 content_fingerprint" in follow_up["summary"]
    assert "不得向 Human 呈交 Gate 1" in follow_up["summary"]
    assert follow_up["required_human_decisions"] == []
    assert follow_up["required_inputs"][0]["scope"] == [actual_ref]
    assert "result.actual_ref 原样" in follow_up["required_inputs"][0]["summary"]
    assert "内部的 post-create readback 或 integrity audit 不替代" in (
        follow_up["resume_conditions"][0]["summary"]
    )
    assert follow_up["suggested_operations"] == [
        {
            "operation_key": "read-fact-objects",
            "summary": "使用 result.actual_ref 公开精确回读刚创建的 WorkCase",
            "scope": [actual_ref],
            "source_refs": follow_up["suggested_operations"][0]["source_refs"],
        }
    ]


def test_workcase_create_rejects_exact_active_title_retry_with_stable_refs(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    first_basis = _prepare(workspace, project, "workcase")
    first = handle_request(
        "call",
        "create-fact-object",
        _create_payload(workspace, project, first_basis, _workcase()),
    ).response
    assert first["outcome"] == "ok"

    retry_basis = _prepare(workspace, project, "workcase")
    retry = handle_request(
        "call",
        "create-fact-object",
        _create_payload(workspace, project, retry_basis, _workcase()),
    ).response

    assert retry["outcome"] == "rejected"
    assert retry["scope"]["completed"] == []
    assert retry["scope"]["not_completed"] == retry["scope"]["requested"]
    assert retry["gaps"][0]["code"] == "active_workcase_title_conflict"
    assert retry["result"]["existing_refs"] == [first["result"]["actual_ref"]]
    assert retry["result"]["ambiguous"] is False
    assert retry["result"]["target_namespace"]["create_namespace_state"] == "not_attempted"
    assert [change["status"] for change in retry["changes"]] == ["target-not-attempted"]
    assert len(tuple((project / "ldvh-base" / "workcases").glob("*.yaml"))) == 1


def test_workcase_create_fails_closed_when_active_title_scan_is_incomplete(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    workcases = project / "ldvh-base" / "workcases"
    workcases.mkdir(parents=True)
    (workcases / "workcase-0001.yaml").write_text("title: 无法完整解析\nstatus: open\n", encoding="utf-8")
    basis = _prepare(workspace, project, "workcase")

    response = handle_request(
        "call",
        "create-fact-object",
        _create_payload(workspace, project, basis, _workcase()),
    ).response

    assert response["outcome"] == "unavailable"
    assert response["scope"]["completed"] == []
    assert response["scope"]["not_completed"] == response["scope"]["requested"]
    assert response["result"]["target_namespace"]["create_namespace_state"] == "not_attempted"
    assert [change["status"] for change in response["changes"]] == ["target-not-attempted"]
    assert len(tuple(workcases.glob("*.yaml"))) == 1


def test_workcase_create_fails_closed_when_title_directory_cannot_be_listed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, project = _fixture(tmp_path)
    (project / "ldvh-base" / "workcases").mkdir(parents=True)
    basis = _prepare(workspace, project, "workcase")
    monkeypatch.setattr(
        creation_application,
        "safe_list_directory",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(PermissionError("denied")),
    )

    response = handle_request(
        "call",
        "create-fact-object",
        _create_payload(workspace, project, basis, _workcase()),
    ).response

    assert response["outcome"] == "unavailable"
    assert response["result"]["target_namespace"]["create_namespace_state"] == "not_attempted"
    assert len(tuple((project / "ldvh-base" / "workcases").glob("*.yaml"))) == 0


@pytest.mark.parametrize(
    ("existing_status", "existing_title"),
    [("closed", "中文 Controlled WorkCase"), ("open", "中文 Controlled WorkCase ")],
)
def test_workcase_active_title_guard_does_not_normalize_or_block_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    existing_status: str,
    existing_title: str,
) -> None:
    workspace, project = _fixture(tmp_path)
    (project / "ldvh-base" / "workcases").mkdir(parents=True)
    basis = _prepare(workspace, project, "workcase")
    observed = FactReadResult(
        Path("ldvh-base/workcases/workcase-0001.yaml"),
        "yaml",
        "mechanically_valid",
        {
            "object_uid": "0198f1c7-8a2b-7c3d-9e4f-123456789abc",
            "object_id": "workcase-0001",
            "fact_type_key": "workcase",
            "status": existing_status,
            "title": existing_title,
        },
        None,
        (),
    )
    monkeypatch.setattr(
        creation_application.ProjectFactIndex,
        "scan_valid_objects",
        lambda *_args, **_kwargs: ((observed,), True),
    )

    response = handle_request(
        "call",
        "create-fact-object",
        _create_payload(workspace, project, basis, _workcase()),
    ).response

    assert response["outcome"] == "ok"


def test_workcase_active_title_conflict_returns_all_refs_in_stable_order(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, project = _fixture(tmp_path)
    (project / "ldvh-base" / "workcases").mkdir(parents=True)
    basis = _prepare(workspace, project, "workcase")
    reads = tuple(
        FactReadResult(
            Path(f"ldvh-base/workcases/workcase-{index}.yaml"),
            "yaml",
            "mechanically_valid",
            {
                "object_uid": uid,
                "object_id": f"workcase-{index}",
                "fact_type_key": "workcase",
                "status": status,
                "title": "中文 Controlled WorkCase",
            },
            None,
            (),
        )
        for index, uid, status in (
            (2, "0198f1c7-8a2b-7c3d-9e4f-123456789abd", "blocked"),
            (1, "0198f1c7-8a2b-7c3d-9e4f-123456789abc", "open"),
        )
    )
    monkeypatch.setattr(
        creation_application.ProjectFactIndex,
        "scan_valid_objects",
        lambda *_args, **_kwargs: (reads, True),
    )

    response = handle_request(
        "call",
        "create-fact-object",
        _create_payload(workspace, project, basis, _workcase()),
    ).response

    assert response["outcome"] == "rejected"
    assert response["result"]["existing_refs"] == [
        {"object_uid": "0198f1c7-8a2b-7c3d-9e4f-123456789abc"},
        {"object_uid": "0198f1c7-8a2b-7c3d-9e4f-123456789abd"},
    ]
    assert response["result"]["ambiguous"] is True


def test_real_processes_same_workcase_title_create_at_most_one_file(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    bases = (_prepare(workspace, project, "workcase"), _prepare(workspace, project, "workcase"))
    payloads = tuple(_create_payload(workspace, project, basis, _workcase()) for basis in bases)

    def run(payload: str) -> dict[str, object]:
        completed = subprocess.run(
            [str(HELPER_EXECUTABLE), "call", "create-fact-object"],
            cwd=project,
            input=payload,
            text=True,
            capture_output=True,
            check=False,
        )
        return json.loads(completed.stdout)

    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = tuple(executor.map(run, payloads))

    assert sorted(response["outcome"] for response in responses) == ["ok", "rejected"]
    rejected = next(response for response in responses if response["outcome"] == "rejected")
    assert rejected["gaps"][0]["code"] == "active_workcase_title_conflict"
    assert len(tuple((project / "ldvh-base" / "workcases").glob("*.yaml"))) == 1


def test_non_workcase_create_success_keeps_generic_follow_up(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    basis = _prepare(workspace, project, "spark")

    response = handle_request(
        "call",
        "create-fact-object",
        _create_payload(workspace, project, basis, _spark()),
    ).response

    assert response["outcome"] == "ok"
    assert response["follow_up"] == {
        "summary": "当前响应没有能够由 Helper 明确的专属后续信息",
        "required_inputs": [],
        "required_human_decisions": [],
        "resume_conditions": [],
        "suggested_operations": [],
    }


def test_create_rejects_non_open_workcase_initial_state(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    basis = _prepare(workspace, project, "workcase")
    fact_object = _workcase()
    fact_object["status"] = "blocked"
    fact_object["blocking_summary"] = "Required external evidence is not yet available."

    response = handle_request(
        "call",
        "create-fact-object",
        _create_payload(workspace, project, basis, fact_object),
    ).response

    assert_common_response(response)
    assert response["outcome"] == "rejected"
    assert "初始状态" in response["gaps"][0]["summary"]
    assert "open" in response["gaps"][0]["summary"]
    assert not (project / "ldvh-base/workcases").exists()


@pytest.mark.parametrize("missing_member", ("quality_gates", "covered_quality_gate_ids"))
def test_helper_create_rejects_workcase_missing_required_quality_gate_without_writing(
    tmp_path: Path,
    missing_member: str,
) -> None:
    workspace, project = _fixture(tmp_path)
    basis = _prepare(workspace, project, "workcase")
    fact_object = _workcase()

    if missing_member == "quality_gates":
        fact_object["execution_authorization"].pop("quality_gates")
    else:
        fact_object["creation_reviews"][0].pop("covered_quality_gate_ids")

    response = handle_request(
        "call",
        "create-fact-object",
        _create_payload(workspace, project, basis, fact_object),
    ).response

    assert_common_response(response)
    assert response["outcome"] == "rejected"
    assert response["changes"] == []
    assert not (project / "ldvh-base/workcases").exists()


def test_create_rejects_nonpending_workcase_initial_item(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    basis = _prepare(workspace, project, "workcase")
    fact_object = _workcase()
    fact_object["work_items"][0].update(
        {
            "status": "in_progress",
            "current_summary": "Execution was claimed before creation.",
            "resume_from": "Continue the claimed execution.",
        }
    )

    response = handle_request(
        "call",
        "create-fact-object",
        _create_payload(workspace, project, basis, fact_object),
    ).response

    assert_common_response(response)
    assert response["outcome"] == "rejected"
    assert "全部 work item 必须是 pending" in response["gaps"][0]["summary"]
    assert not (project / "ldvh-base/workcases").exists()


def test_create_rejects_workcase_that_bypasses_the_initial_human_gate(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    basis = _prepare(workspace, project, "workcase")
    fact_object = _workcase()
    fact_object.update(
        {
            "phase": "executing",
            "plan_version": 99,
            "execution_approval": {
                "subject_version": 99,
                "approved_at": "2026-07-14T09:30:00+08:00",
                "summary": "Claimed approval before controlled creation",
            },
        }
    )
    fact_object.pop("waiting_on")
    fact_object["creation_reviews"][0]["subject_version"] = 99

    response = handle_request(
        "call",
        "create-fact-object",
        _create_payload(workspace, project, basis, fact_object),
    ).response

    assert response["outcome"] == "rejected"
    summary = response["gaps"][0]["summary"]
    assert "初始 phase" in summary
    assert "初始 plan_version" in summary
    assert "禁止预置 execution_approval" in summary
    assert not (project / "ldvh-base/workcases").exists()


def test_helper_create_rejects_a_three_level_dependency_with_a_missing_target(
    tmp_path: Path,
) -> None:
    workspace, project = _fixture(tmp_path)
    intermediate = _write_existing_workcase(
        project,
        "workcase-0001",
        depends_on="workcase-0003",
    )
    intermediate_bytes = intermediate.read_bytes()
    basis = _prepare(workspace, project, "workcase")
    assert "candidate_object_id" not in basis
    fact_object = _workcase()
    fact_object["relations"] = [_depends_on("workcase-0001")]

    response = handle_request(
        "call",
        "create-fact-object",
        _create_payload(workspace, project, basis, fact_object),
    ).response

    assert_common_response(response)
    assert response["outcome"] == "rejected"
    assert "关系图包含缺失" in response["gaps"][0]["summary"]
    assert not (project / LAYOUTS["workcase"].canonical_path("workcase-0002")).exists()
    assert intermediate.read_bytes() == intermediate_bytes
    assert not (project / ".git/ldvh").exists()


def _chinese_primary_new_fact(value: object, key: str | None = None) -> object:
    constrained = {
        "abstract", "action_ceiling", "allowed_adjustments", "applicability", "avoidance",
        "blocking_summary", "cleanup_summary", "consequences", "controller_check_summary",
        "controller_resolution", "decision", "decision_question", "disposition_summary",
        "effect_scope", "expected_result", "feedback", "goal", "impact_summary", "intent",
        "not_meaning", "observation_summary", "out_of_bounds_handling", "rationale", "reason",
        "recommendation_summary", "research_intent", "research_question", "resolution", "result_summary",
        "resume_from", "risk_summary", "rollback_summary", "root_cause", "scope", "statement", "summary",
        "symptoms", "target_scope", "title", "trigger_conditions", "validation_summary",
        "verification_and_rollback", "waiting_on",
    }
    if isinstance(value, dict):
        return {item_key: _chinese_primary_new_fact(item, item_key) for item_key, item in value.items()}
    if isinstance(value, list):
        return [_chinese_primary_new_fact(item, key) for item in value]
    if key in constrained and isinstance(value, str) and not any("\u3400" <= char <= "\u9fff" for char in value):
        return f"中文 {value}"
    return value


def _create_payload(
    workspace: Path,
    project: Path,
    basis: dict[str, object],
    fact_object: dict[str, object],
) -> str:
    supplied = _chinese_primary_new_fact(deepcopy(fact_object))
    assert isinstance(supplied, dict)
    change_log_target = supplied.get("frontmatter") if set(supplied) == {"frontmatter", "body"} else supplied
    assert isinstance(change_log_target, dict)
    change_log_target.setdefault(
        "change_log",
        [
            {
                "signature": {
                    "product_name": "pytest",
                    "model_name": "test-model",
                },
                "at": (datetime.now().astimezone() - timedelta(minutes=1)).isoformat(),
                "summary": "由受控测试夹具创建。",
            }
        ],
    )
    return json.dumps(
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
                "fact_object": supplied,
            },
            "observed_context": {
                "signature": {
                    "product_name": "pytest",
                    "model_name": "test-model",
                }
            },
        },
    )


def _assert_creation_result_matrix(response: dict[str, object], fact_type_key: str = "spark") -> None:
    result = response["result"]
    assert isinstance(result, dict)
    identity = result["identity"]
    target = result["target_namespace"]
    assert isinstance(identity, dict)
    assert isinstance(target, dict)
    assert set(identity) == {"attempted_object_uid", "attempted_locator"}
    assert set(target) == {
        "canonical_path",
        "create_namespace_state",
        "post_create_readback",
        "rollback_state",
        "final_observation",
    }
    canonical_path = target["canonical_path"]
    create_state = target["create_namespace_state"]
    readback = target["post_create_readback"]
    rollback = target["rollback_state"]
    observation = target["final_observation"]

    assert rollback in {"not_applicable", "not_needed", "removed", "not_removed", "uncertain"}
    assert observation in {
        "not_required",
        "same_created_bytes",
        "other_mechanically_valid",
        "mechanically_invalid",
        "not_found",
        "unavailable",
    }
    fresh_observations = {
        "same_created_bytes",
        "other_mechanically_valid",
        "mechanically_invalid",
        "not_found",
        "unavailable",
    }

    if create_state == "not_attempted":
        assert (readback, rollback, observation) == ("not_run", "not_applicable", "not_required")
    elif create_state in {"not_created", "uncertain"}:
        assert (readback, rollback) == ("not_run", "not_applicable")
        assert observation in fresh_observations
    else:
        assert create_state == "created"
        if readback == "passed":
            assert (rollback, observation) == ("not_needed", "not_required")
        else:
            assert readback in {"failed", "unavailable"}
            if rollback == "removed":
                assert observation == "not_required"
            else:
                assert rollback in {"not_removed", "uncertain"}
                assert observation in fresh_observations

    success_fields = {"created", "actual_ref", "content_fingerprint", "carrier", "fact_object"}
    base_fields = {"identity", "target_namespace"}
    if create_state == "created" and readback == "passed":
        assert set(result) == base_fields | success_fields
    else:
        assert set(result) == base_fields

    target_status = {
        "not_attempted": "target-not-attempted",
        "created": "target-created",
        "not_created": "target-not-created",
        "uncertain": "target-create-uncertain",
    }[create_state]
    expected_statuses = [target_status]
    if rollback == "removed":
        expected_statuses.append("target-removed")
    elif rollback in {"not_removed", "uncertain"}:
        expected_statuses.append("target-remove-unconfirmed")

    changes = response["changes"]
    assert isinstance(changes, list)
    assert [change["status"] for change in changes] == expected_statuses
    assert changes[0]["target"] == canonical_path
    if len(changes) == 2:
        assert changes[1]["target"] == canonical_path
    type_source = {
        "spark": "specs/20-Spark-火花.md",
        "workcase": "specs/21-WorkCase-工作项.md",
        "adr": "specs/22-ADR-决策.md",
        "pitfall": "specs/23-Pitfall-踩坑经验.md",
        "study": "specs/24-Study-研究报告.md",
    }[fact_type_key]
    for change in changes:
        rule_locators = {source["locator"] for source in change["source_refs"] if source.get("kind") == "rule"}
        assert any(locator.startswith("fact-model-foundation::11.4") for locator in rule_locators)
        assert type_source in rule_locators


def test_observed_signature_survives_real_create_and_workcase_update_schema_validation(
    tmp_path: Path,
) -> None:
    workspace, project = _fixture(tmp_path)
    basis = _prepare(workspace, project, "workcase")
    create_payload = json.loads(_create_payload(workspace, project, basis, _workcase()))
    create_payload["observed_context"] = {
        "signature": {
            "product_name": "Cindy",
            "model_name": "gpt-5.6-luna",
        }
    }

    created = handle_request(
        "call", "create-fact-object", json.dumps(create_payload)
    ).response
    assert created["outcome"] == "ok", json.dumps(created, ensure_ascii=False, indent=2)
    created_object = created["result"]["fact_object"]
    created_log = created_object["change_log"][-1]
    assert created_log["signature"] == {
        "product_name": "Cindy",
        "model_name": "gpt-5.6-luna",
    }
    assert "session_id" not in created_log
    assert "session_id" not in created_log["signature"]

    reference = created["result"]["actual_ref"]
    read = handle_request(
        "call",
        "read-fact-objects",
        json.dumps(
            {
                "work_object_locators": [str(project)],
                "arguments": {
                    "workspace_root": str(workspace),
                    "fact_refs": [reference],
                },
            }
        ),
    ).response["result"]["items"][0]
    assert read["check_status"] == "mechanically_valid"
    target = deepcopy(read["fact_object"])
    for key in ("object_uid", "object_id", "fact_type_key", "created_at", "updated_at"):
        target.pop(key)
    target["summary"] = "真实更新后等待 Human 执行批准。"
    target["change_log"].append(
        {
                "signature": {
                    "product_name": "Placeholder Product",
                    "model_name": "placeholder-model",
                },
            "at": datetime.now().astimezone().isoformat(),
            "summary": "更新真实 WorkCase 测试夹具。",
        }
    )
    updated = handle_request(
        "call",
        "update-workcase",
        json.dumps(
            {
                "work_object_locators": [str(project)],
                "arguments": {
                    "workspace_root": str(workspace),
                    "fact_ref": reference,
                    "expected_content_fingerprint": read["content_fingerprint"],
                    "fact_object": target,
                },
                "observed_context": {
                    "signature": {
                        "product_name": "Cindy",
                        "model_name": "gpt-5.6-luna",
                    }
                },
            }
        ),
    ).response
    assert updated["outcome"] == "ok", json.dumps(updated, ensure_ascii=False, indent=2)
    updated_log = updated["result"]["fact_object"]["change_log"][-1]
    assert updated_log["signature"] == {
        "product_name": "Cindy",
        "model_name": "gpt-5.6-luna",
    }
    assert "session_id" not in updated_log
    reread = handle_request(
        "call",
        "read-fact-objects",
        json.dumps(
            {
                "work_object_locators": [str(project)],
                "arguments": {
                    "workspace_root": str(workspace),
                    "fact_refs": [reference],
                },
            }
        ),
    ).response["result"]["items"][0]
    assert reread["check_status"] == "mechanically_valid"

    target_path = project / reread["canonical_path"]
    bytes_before_unavailable = target_path.read_bytes()
    unavailable_target = deepcopy(reread["fact_object"])
    for key in ("object_uid", "object_id", "fact_type_key", "created_at", "updated_at"):
        unavailable_target.pop(key)
    unavailable_target["summary"] = "缺少可观察署名字段时不得写入本次更新。"
    unavailable_target["change_log"].append(
        {
            "signature": {
                "product_name": "Placeholder Product",
                "model_name": "placeholder-model",
            },
            "at": datetime.now().astimezone().isoformat(),
            "summary": "Attempt an update with a wholly unavailable signer snapshot.",
        }
    )
    unavailable_signatures = (
        {
            "product_name": None,
            "model_name": None,
        },
        {"product_name": "Cindy"},
        {
            "product_name": "Cindy",
            "model_name": None,
            "unknown": "not-allowed",
        },
    )
    for unavailable_signature in unavailable_signatures:
        unavailable = handle_request(
            "call",
            "update-workcase",
            json.dumps(
                {
                    "work_object_locators": [str(project)],
                    "arguments": {
                        "workspace_root": str(workspace),
                        "fact_ref": reference,
                        "expected_content_fingerprint": reread["content_fingerprint"],
                        "fact_object": unavailable_target,
                    },
                    "observed_context": {"signature": unavailable_signature},
                }
            ),
        ).response
        assert unavailable["outcome"] == "unavailable", json.dumps(unavailable, ensure_ascii=False, indent=2)
        assert unavailable["changes"] == []
        assert target_path.read_bytes() == bytes_before_unavailable


@pytest.mark.parametrize(
    "unavailable_signature",
    [
        {
            "product_name": None,
            "model_name": None,
        },
        {"product_name": "Cindy"},
        {
            "product_name": "Cindy",
            "model_name": None,
            "unknown": "not-allowed",
        },
    ],
)
def test_create_rejects_unavailable_signature_shapes_without_writing(
    tmp_path: Path,
    unavailable_signature: dict[str, object],
) -> None:
    workspace, project = _fixture(tmp_path)
    basis = _prepare(workspace, project, "spark")
    payload = json.loads(_create_payload(workspace, project, basis, _spark()))
    payload["observed_context"] = {"signature": unavailable_signature}
    yaml_paths_before = tuple(project.rglob("*.yaml"))

    response = handle_request(
        "call", "create-fact-object", json.dumps(payload)
    ).response

    assert response["outcome"] == "invalid_request"
    assert response["changes"] == []
    assert tuple(project.rglob("*.yaml")) == yaml_paths_before


def test_create_rejects_governance_instance_signature_before_writing(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    basis = _prepare(workspace, project, "spark")
    payload = json.loads(_create_payload(workspace, project, basis, _spark()))
    payload["response_profile"] = "diagnostic"
    payload["observed_context"]["signature"]["product_name"] = "Test Workspace"
    yaml_paths_before = tuple(project.rglob("*.yaml"))

    response = handle_request("call", "create-fact-object", json.dumps(payload)).response

    assert response["outcome"] == "rejected"
    assert response["changes"] == []
    assert response["gaps"][0]["code"] == "signature_governance_instance_collision"
    assert response["diagnostics"][0]["code"] == "signature_governance_instance_collision"
    assert tuple(project.rglob("*.yaml")) == yaml_paths_before
    assert not (project / ".git/ldvh").exists()


def test_prepare_has_no_canonical_side_effect_and_create_injects_managed_fields(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)

    basis = _prepare(workspace, project)

    assert "candidate_object_id" not in basis
    assert not (project / "facts").exists()
    response = handle_request(
        "call",
        "create-fact-object",
        _create_payload(workspace, project, basis, _spark()),
    ).response
    assert_common_response(response)
    assert response["outcome"] == "ok"
    _assert_creation_result_matrix(response)
    locator = response["result"]["fact_object"]["object_id"]
    uid = response["result"]["actual_ref"]["object_uid"]
    assert object_uid_from_locator("spark", locator) == uid
    assert set(response["result"]) == {
        "identity",
        "target_namespace",
        "created",
        "actual_ref",
        "content_fingerprint",
        "carrier",
        "fact_object",
    }
    assert response["result"]["identity"] == {
        "attempted_object_uid": uid,
        "attempted_locator": locator,
    }
    assert response["result"]["target_namespace"] == {
        "canonical_path": f"ldvh-base/sparks/{locator}.yaml",
        "create_namespace_state": "created",
        "post_create_readback": "passed",
        "rollback_state": "not_needed",
        "final_observation": "not_required",
    }
    assert response["scope"]["requested"] == response["scope"]["completed"]
    assert response["scope"]["not_completed"] == []
    fact_object = response["result"]["fact_object"]
    assert fact_object["object_id"] == locator
    assert fact_object["fact_type_key"] == "spark"
    assert fact_object["created_at"] == fact_object["updated_at"]
    assert (project / response["result"]["target_namespace"]["canonical_path"]).is_file()


def test_helper_create_read_and_update_accept_ignored_current_fact(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    (project / ".gitignore").write_text("ldvh-base/\n", encoding="utf-8")
    basis = _prepare(workspace, project)

    created = handle_request(
        "call",
        "create-fact-object",
        _create_payload(workspace, project, basis, _spark()),
    ).response
    assert created["outcome"] == "ok"
    reference = created["result"]["actual_ref"]

    read = handle_request(
        "call",
        "read-fact-objects",
        json.dumps(
            {
                "work_object_locators": [str(project)],
                "arguments": {"workspace_root": str(workspace), "fact_refs": [reference]},
            }
        ),
    ).response["result"]["items"][0]
    assert read["check_status"] == "mechanically_valid"

    target = dict(read["fact_object"])
    for key in ("object_uid", "object_id", "fact_type_key", "created_at", "updated_at"):
        target.pop(key)
    target["summary"] = "通过 Helper 更新被忽略的当前事实对象。"
    target["change_log"].append(
        {
            "signature": {
                "product_name": "pytest",
                "model_name": "test-model",
            },
            "at": datetime.now().astimezone().isoformat(),
            "summary": "由受控测试夹具完成更新。",
        }
    )
    updated = handle_request(
        "call",
        "update-fact-object",
        json.dumps(
            {
                "work_object_locators": [str(project)],
                "arguments": {
                    "workspace_root": str(workspace),
                    "fact_ref": reference,
                    "expected_content_fingerprint": read["content_fingerprint"],
                    "fact_object": target,
                },
                "observed_context": {
                    "signature": {
                        "product_name": "pytest",
                        "model_name": "test-model",
                    }
                },
            }
        ),
    ).response
    assert updated["outcome"] == "ok"
    assert updated["result"]["fact_object"]["summary"] == target["summary"]


def test_create_reports_committed_namespace_when_directory_sync_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, project = _fixture(tmp_path)
    basis = _prepare(workspace, project)
    real_fsync = os.fsync
    target_directory = project / "ldvh-base/sparks"

    def fail_directory_sync(descriptor: int) -> None:
        observation = os.fstat(descriptor)
        if (
            stat.S_ISDIR(observation.st_mode)
            and target_directory.exists()
            and (observation.st_dev, observation.st_ino)
            == (target_directory.stat().st_dev, target_directory.stat().st_ino)
        ):
            raise OSError("directory sync failed")
        real_fsync(descriptor)

    monkeypatch.setattr("ldvh.filesystem.os.fsync", fail_directory_sync)

    response = handle_request(
        "call",
        "create-fact-object",
        _create_payload(workspace, project, basis, _spark()),
    ).response

    assert response["outcome"] == "ok"
    assert [change["status"] for change in response["changes"]] == ["target-created"]
    assert (project / response["result"]["target_namespace"]["canonical_path"]).is_file()


def test_create_fails_before_allocator_mutation_when_platform_durability_is_not_approved(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, project = _fixture(tmp_path)
    basis = _prepare(workspace, project)
    monkeypatch.setattr("ldvh.facts.creation_application.native_atomic_fact_writes_supported", lambda: False)

    response = handle_request(
        "call",
        "create-fact-object",
        _create_payload(workspace, project, basis, _spark()),
    ).response

    assert response["outcome"] == "unavailable"
    assert "原生原子后端" in response["summary"]
    assert not (project / ".git/ldvh").exists()
    assert not (project / "facts").exists()


def test_create_maps_shared_lock_permission_failure_to_structured_unavailable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, project = _fixture(tmp_path)
    basis = _prepare(workspace, project)
    monkeypatch.setattr(
        "ldvh.helper.operations.fact_creation_operation.create_fact_object",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(FactCoordinationUnavailable("permission_denied")),
    )

    compact = handle_request(
        "call",
        "create-fact-object",
        _create_payload(workspace, project, basis, _spark()),
    ).response
    diagnostic_payload = json.loads(_create_payload(workspace, project, basis, _spark()))
    diagnostic_payload["response_profile"] = "diagnostic"
    diagnostic = handle_request(
        "call",
        "create-fact-object",
        json.dumps(diagnostic_payload),
    ).response

    assert compact["outcome"] == diagnostic["outcome"] == "unavailable"
    assert compact["gaps"][0]["code"] == "controlled_write_lock_unavailable"
    assert compact["diagnostics"] == []
    assert diagnostic["diagnostics"][0]["code"] == "controlled_write_lock_unavailable"
    assert diagnostic["diagnostics"][0]["details"]["stage"] == "common_dir_lock"
    assert not (project / ".git/ldvh").exists()
    assert not (project / "facts").exists()


def test_real_lock_entry_permission_failure_reaches_helper_without_target_or_counter_change(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, project = _fixture(tmp_path)
    basis = _prepare(workspace, project)

    @contextmanager
    def denied_lock(*_args, **_kwargs):
        raise PermissionError("simulated common-dir lock denial")
        yield  # pragma: no cover - contextmanager shape only

    monkeypatch.setattr("ldvh.facts.creation.exclusive_relative_file_lock", denied_lock)
    response = handle_request(
        "call",
        "create-fact-object",
        _create_payload(workspace, project, basis, _spark()),
    ).response

    assert_common_response(response)
    assert response["outcome"] == "unavailable"
    assert response["gaps"][0]["code"] == "controlled_write_lock_unavailable"
    assert not (project / "ldvh-base" / "sparks" / "spark-0001.yaml").exists()
    assert not list((project / ".git" / "ldvh" / "fact-id-allocators").glob("*.counter"))


def test_helper_preserves_created_result_when_coordination_release_is_uncertain(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, project = _fixture(tmp_path)
    basis = _prepare(workspace, project)
    actual_lock = creation_application.fact_write_lock

    @contextmanager
    def release_fails(boundary, layout):
        with actual_lock(boundary, layout):
            yield
        raise OSError("simulated lock release failure")

    monkeypatch.setattr(creation_application, "fact_write_lock", release_fails)
    payload = json.loads(_create_payload(workspace, project, basis, _spark()))
    payload["response_profile"] = "diagnostic"

    response = handle_request("call", "create-fact-object", json.dumps(payload)).response

    assert_common_response(response)
    assert response["outcome"] == "ok"
    assert response["scope"]["completed"] == response["scope"]["requested"]
    assert response["scope"]["not_completed"] == []
    locator = response["result"]["fact_object"]["object_id"]
    assert object_uid_from_locator("spark", locator) == response["result"]["actual_ref"]["object_uid"]
    assert [change["status"] for change in response["changes"]] == ["target-created"]
    assert response["verification"][0]["status"] == "passed"
    release_gap = next(gap for gap in response["gaps"] if "共同创建锁释放" in gap["summary"])
    assert release_gap["code"] == "controlled_write_lock_release_uncertain"
    assert response["diagnostics"][0]["code"] == "controlled_write_lock_release_uncertain"
    assert response["diagnostics"][0]["details"]["stage"] == "common_dir_lock_release"
    assert response["follow_up"]["resume_conditions"]
    assert (project / response["result"]["target_namespace"]["canonical_path"]).is_file()


def test_helper_separates_consumed_allocator_from_uncertain_target_residual(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, project = _fixture(tmp_path)
    basis = _prepare(workspace, project)

    def uncertain_target_create(root: Path, layout, object_id: str, text: str) -> AtomicWriteResult:
        target = root / layout.canonical_path(object_id)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        return AtomicWriteResult.uncertain()

    monkeypatch.setattr(creation_application, "atomic_create_text", uncertain_target_create)

    response = handle_request(
        "call",
        "create-fact-object",
        _create_payload(workspace, project, basis, _spark()),
    ).response

    assert response["outcome"] == "unavailable"
    _assert_creation_result_matrix(response)
    assert response["summary"] == "UID 定位符目标的原子创建未能完成或确认"
    assert [change["status"] for change in response["changes"]] == ["target-create-uncertain"]
    assert "完整字节内容与本次创建载体一致" in response["changes"][0]["summary"]
    assert response["verification"][0]["status"] == "passed"
    assert response["result"]["target_namespace"] == {
        "canonical_path": response["result"]["target_namespace"]["canonical_path"],
        "create_namespace_state": "uncertain",
        "post_create_readback": "not_run",
        "rollback_state": "not_applicable",
        "final_observation": "same_created_bytes",
    }
    assert "actual_ref" not in response["result"]
    residual_source = next(source for source in response["sources"] if source["kind"] == "working_tree")
    assert residual_source["details"]["check_status"] == "mechanically_valid"


@pytest.mark.parametrize("write_outcome", ["conflict", "unavailable"])
def test_helper_reports_known_target_noncommit_and_consumed_allocator_separately(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    write_outcome: str,
) -> None:
    workspace, project = _fixture(tmp_path)
    basis = _prepare(workspace, project)
    monkeypatch.setattr(
        creation_application,
        "atomic_create_text",
        lambda *_args, **_kwargs: AtomicWriteResult.not_committed(write_outcome),
    )

    response = handle_request(
        "call",
        "create-fact-object",
        _create_payload(workspace, project, basis, _spark()),
    ).response

    assert response["outcome"] == "unavailable"
    _assert_creation_result_matrix(response)
    assert [change["status"] for change in response["changes"]] == ["target-not-created"]
    expected_prefix = "发生冲突" if write_outcome == "conflict" else "确认未在文件命名空间（namespace）提交"
    assert expected_prefix in response["changes"][0]["summary"]
    assert "预期位置不存在" in response["changes"][0]["summary"]
    assert response["verification"][0]["status"] == "failed"
    assert response["result"]["target_namespace"] == {
        "canonical_path": response["result"]["target_namespace"]["canonical_path"],
        "create_namespace_state": "not_created",
        "post_create_readback": "not_run",
        "rollback_state": "not_applicable",
        "final_observation": "not_found",
    }


def test_two_ai_drafts_with_same_candidate_receive_distinct_final_ids(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    first_basis = _prepare(workspace, project)
    second_basis = _prepare(workspace, project)
    assert "candidate_object_id" not in first_basis | second_basis
    payloads = (
        _create_payload(workspace, project, first_basis, _spark("First concurrent draft")),
        _create_payload(workspace, project, second_basis, _spark("Second concurrent draft")),
    )

    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = tuple(
            executor.map(lambda payload: handle_request("call", "create-fact-object", payload).response, payloads)
        )

    assert all(response["outcome"] == "ok" for response in responses)
    actual_ids = {response["result"]["fact_object"]["object_id"] for response in responses}
    assert len(actual_ids) == 2
    assert all(object_uid_from_locator("spark", value) for value in actual_ids)
    assert len(tuple((project / "ldvh-base" / "sparks").glob("*.yaml"))) == 2


def test_create_rejects_ai_managed_fields_without_writing_or_consuming_id(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    basis = _prepare(workspace, project)
    supplied = _spark()
    supplied["object_id"] = "spark-9999"

    response = handle_request(
        "call",
        "create-fact-object",
        _create_payload(workspace, project, basis, supplied),
    ).response

    assert response["outcome"] == "invalid_request"
    assert "Code 托管字段" in response["gaps"][0]["summary"]
    assert not (project / "facts").exists()
    assert "candidate_object_id" not in _prepare(workspace, project)


def test_create_revalidates_cross_type_relation_with_complete_schema_set(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    workcases = project / "ldvh-base" / "workcases"
    workcases.mkdir(parents=True)
    (workcases / "workcase-0001.yaml").write_text(
        "\n".join(
            [
                "object_id: workcase-0001",
                "fact_type_key: workcase",
                "title: Existing target",
                "created_at: 2026-07-14T09:00:00+08:00",
                "updated_at: 2026-07-14T09:00:00+08:00",
                "status: open",
                "summary: Waiting for Human execution approval",
                "resume_from: Present plan version 1 for Human approval",
                "waiting_on: Human execution approval",
                "priority: P2",
                "goal: Complete target",
                "scope: One object",
                "success_criterion_definitions:",
                "  - criterion_id: criterion-01",
                "    statement: Target is complete",
                "phase: human_plan_confirming",
                "plan_version: 1",
                "work_items:",
                "  - item_id: item-01",
                "    goal: Complete the target",
                "    expected_result: Target is complete",
                "    status: pending",
                "    approach_summary: Complete the bounded target and validate it",
                "creation_reviews:",
                "  - reviewer: independent-target-reviewer",
                "    reviewed_at: 2026-07-14T09:00:00+08:00",
                "    subject_version: 1",
                "    scope: Goal, scope, criteria, work items, method, validation and risks",
                "    conclusion: pass",
                "    actual_method: subagent-read-only",
                "    feedback:",
                "      - The plan is bounded and testable",
                "    controller_resolution: '1. Accepted; no change required.'",
                "execution_authorization:",
                "  authorized_actions:",
                "    - action_id: authorization-target-fixture",
                "      summary: Execute the approved target fixture plan.",
                "      target_scope: Creation fixture project only.",
                "      effect_scope: Deterministic helper test workspace.",
                "      risk_summary: No production effect; fixture data only.",
                "      rollback_summary: Remove the fixture objects.",
                "      rule_refs:",
                "        - specs/21-WorkCase-工作项.md",
                "  action_ceiling: Bounded to target fixture actions.",
                "  allowed_adjustments: No adjustments beyond the recorded fixture summaries.",
                "  verification_and_rollback: Run the creation operation test suite.",
                "  out_of_bounds_handling: Stop and return to Human.",
                "  prohibited_actions:",
                "    - Writing outside the fixture workspace.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    basis = _prepare(workspace, project)
    supplied = _spark()
    supplied["relations"] = [
        {
            "relation_key": "related-to",
            "target": {
                "governed_project_id": "sample",
                "fact_type_key": "workcase",
                "object_id": "workcase-0001",
            },
        }
    ]

    response = handle_request(
        "call",
        "create-fact-object",
        _create_payload(workspace, project, basis, supplied),
    ).response

    assert response["outcome"] == "ok"
    created = response["result"]["fact_object"]
    assert object_uid_from_locator("spark", created["object_id"]) == created["object_uid"]


def test_stale_schema_or_worktree_basis_requires_prepare_again(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    basis = _prepare(workspace, project)
    basis["schema_fingerprint"] = "stale"

    response = handle_request(
        "call",
        "create-fact-object",
        _create_payload(workspace, project, basis, _spark()),
    ).response

    assert response["outcome"] == "rejected"
    assert "重新调用 prepare-fact-object-draft" in response["gaps"][0]["summary"]
    assert not (project / "facts").exists()


def test_existing_legacy_object_is_not_overwritten_by_uid_native_creation(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    basis = _prepare(workspace, project)
    sparks = project / "ldvh-base" / "sparks"
    sparks.mkdir(parents=True)
    existing = sparks / "spark-0001.yaml"
    existing.write_text("manual collision\n", encoding="utf-8")

    response = handle_request(
        "call",
        "create-fact-object",
        _create_payload(workspace, project, basis, _spark()),
    ).response

    assert response["outcome"] == "ok"
    created = response["result"]["fact_object"]
    assert object_uid_from_locator("spark", created["object_id"]) == created["object_uid"]
    assert existing.read_text(encoding="utf-8") == "manual collision\n"


def test_linked_worktrees_share_allocator_but_write_to_the_requested_worktree(tmp_path: Path) -> None:
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
    _git(project, "worktree", "add", "-qb", "linked-create", str(linked))

    main_basis = _prepare(workspace, project)
    main_response = handle_request(
        "call",
        "create-fact-object",
        _create_payload(workspace, project, main_basis, _spark("Main worktree")),
    ).response
    linked_basis = _prepare(workspace, linked)
    linked_response = handle_request(
        "call",
        "create-fact-object",
        _create_payload(workspace, linked, linked_basis, _spark("Linked worktree")),
    ).response

    assert main_response["outcome"] == linked_response["outcome"] == "ok"
    main_id = main_response["result"]["fact_object"]["object_id"]
    linked_id = linked_response["result"]["fact_object"]["object_id"]
    assert main_id != linked_id
    assert "candidate_object_id" not in linked_basis
    assert (project / "ldvh-base" / "sparks" / f"{main_id}.yaml").is_file()
    assert (linked / "ldvh-base" / "sparks" / f"{linked_id}.yaml").is_file()


@pytest.mark.parametrize(
    ("read_check_status", "expected_post_create_readback"),
    [("invalid", "failed"), ("unavailable", "unavailable")],
)
def test_failed_write_back_read_rolls_back_file_but_never_reuses_id(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    read_check_status: str,
    expected_post_create_readback: str,
) -> None:
    workspace, project = _fixture(tmp_path)
    basis = _prepare(workspace, project)
    monkeypatch.setattr(
        "ldvh.facts.creation_application.read_fact_object",
        lambda *args, **kwargs: FactReadResult(
            "ldvh-base/sparks/spark-0001.yaml",
            "yaml",
            read_check_status,
            None,
            None,
            (FactIssue("carrier", "forced write-back failure"),),
        ),
    )

    response = handle_request(
        "call",
        "create-fact-object",
        _create_payload(workspace, project, basis, _spark()),
    ).response

    assert response["outcome"] == "error"
    _assert_creation_result_matrix(response)
    assert [change["status"] for change in response["changes"]] == ["target-created", "target-removed"]
    canonical_path = response["result"]["target_namespace"]["canonical_path"]
    assert response["result"]["target_namespace"] == {
        "canonical_path": canonical_path,
        "create_namespace_state": "created",
        "post_create_readback": expected_post_create_readback,
        "rollback_state": "removed",
        "final_observation": "not_required",
    }
    assert "actual_ref" not in response["result"]
    assert not (project / "facts" / "sparks" / "spark-0001.yaml").exists()
    assert "candidate_object_id" not in _prepare(workspace, project)


@pytest.mark.parametrize(
    ("rollback_namespace_state", "expected_rollback_state"),
    [("not_committed", "not_removed"), ("uncertain", "uncertain")],
)
def test_failed_write_back_reports_residue_when_exact_rollback_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    rollback_namespace_state: str,
    expected_rollback_state: str,
) -> None:
    workspace, project = _fixture(tmp_path)
    basis = _prepare(workspace, project)
    actual_lock = creation_application.fact_write_lock

    @contextmanager
    def release_fails(boundary, layout):
        with actual_lock(boundary, layout):
            yield
        raise OSError("simulated lock release failure")

    monkeypatch.setattr(
        "ldvh.facts.creation_application.read_fact_object",
        lambda *args, **kwargs: FactReadResult(
            "ldvh-base/sparks/spark-0001.yaml",
            "yaml",
            "invalid",
            None,
            None,
            (FactIssue("carrier", "forced write-back failure"),),
        ),
    )
    monkeypatch.setattr(
        "ldvh.facts.creation_application.rollback_created_text",
        lambda *args, **kwargs: (
            AtomicWriteResult.uncertain()
            if rollback_namespace_state == "uncertain"
            else AtomicWriteResult.not_committed("unavailable")
        ),
    )
    monkeypatch.setattr(creation_application, "fact_write_lock", release_fails)
    payload = json.loads(_create_payload(workspace, project, basis, _spark()))
    payload["response_profile"] = "diagnostic"

    response = handle_request(
        "call",
        "create-fact-object",
        json.dumps(payload),
    ).response

    assert response["outcome"] == "error"
    _assert_creation_result_matrix(response)
    assert [change["status"] for change in response["changes"]] == [
        "target-created",
        "target-remove-unconfirmed",
    ]
    assert "未能确认删除回滚已经完成" in response["summary"]
    assert "机械检查未通过（状态为 `invalid`）" in response["changes"][1]["summary"]
    release_gap = next(gap for gap in response["gaps"] if "共同锁释放" in gap["summary"])
    assert "status=readback_failed" in release_gap["summary"]
    assert "code" not in release_gap
    assert "code" not in response["diagnostics"][0]
    assert response["verification"][0]["status"] == "failed"
    assert response["result"]["target_namespace"]["rollback_state"] == expected_rollback_state
    assert (project / response["result"]["target_namespace"]["canonical_path"]).is_file()


@pytest.mark.parametrize(
    ("residual_kind", "expected", "verification_status", "excluded", "final_observation"),
    [
        (
            "created",
            "当前重新读取观察到的实际事实对象载体完整字节内容与本次创建载体一致",
            "passed",
            "发生冲突",
            "same_created_bytes",
        ),
        (
            "external",
            "当前重新读取观察到的实际事实对象载体是另一机械有效版本",
            "passed",
            "与本次创建载体一致",
            "other_mechanically_valid",
        ),
        (
            "invalid-read",
            "当前实际事实对象载体已安全完整读取，但对象未通过机械检查",
            "failed",
            "残留状态无法确认",
            "mechanically_invalid",
        ),
        (
            "invalid-unread",
            "当前实际事实对象载体未能安全完整读取，机械检查未通过（状态为 `invalid`）",
            "failed",
            "已安全完整读取",
            "mechanically_invalid",
        ),
        (
            "not-found",
            "当前重新读取确认实际事实对象载体的预期位置不存在",
            "failed",
            "已安全完整读取",
            "not_found",
        ),
        (
            "unavailable",
            "实际事实对象载体的残留状态无法确认",
            "unavailable",
            "已安全完整读取",
            "unavailable",
        ),
    ],
)
def test_creation_helper_reports_the_fresh_actual_residual_after_failed_rollback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    residual_kind: str,
    expected: str,
    verification_status: str,
    excluded: str,
    final_observation: str,
) -> None:
    workspace, project = _fixture(tmp_path)
    basis = _prepare(workspace, project)
    canonical_path = "ldvh-base/sparks/spark-0001.yaml"
    candidate_text = "candidate creation carrier\n"
    residuals = {
        "created": FactReadResult(
            canonical_path,
            "yaml",
            "mechanically_valid",
            {"title": "Created"},
            None,
            (),
            content_fingerprint="a" * 64,
            raw_text=candidate_text,
        ),
        "external": FactReadResult(
            canonical_path,
            "yaml",
            "mechanically_valid",
            {"title": "External"},
            None,
            (),
            content_fingerprint="b" * 64,
            raw_text="external carrier\n",
        ),
        "invalid-read": FactReadResult(
            canonical_path,
            "yaml",
            "invalid",
            None,
            None,
            (FactIssue("schema", "forced invalid residual"),),
            content_fingerprint="c" * 64,
            raw_text="invalid but fully read\n",
        ),
        "invalid-unread": FactReadResult(
            canonical_path,
            "yaml",
            "invalid",
            None,
            None,
            (FactIssue("location", "forced unread residual"),),
        ),
        "not-found": FactReadResult(
            canonical_path,
            "yaml",
            "not_found",
            None,
            None,
            (FactIssue("location", "forced missing residual"),),
        ),
        "unavailable": FactReadResult(
            canonical_path,
            "yaml",
            "unavailable",
            None,
            None,
            (FactIssue("location", "forced unavailable residual"),),
        ),
    }
    creation = FactCreationResult(
        "readback_failed",
        issues=(FactIssue("schema", "forced write-back failure"),),
        actual_id="spark-0001",
        actual_text=candidate_text,
        read=FactReadResult(
            canonical_path,
            "yaml",
            "invalid",
            None,
            None,
            (FactIssue("schema", "forced write-back failure"),),
            raw_text="failed post-create readback\n",
        ),
        creation_result=AtomicWriteResult.committed("created"),
        rollback_result=AtomicWriteResult.uncertain(),
        residual_readback=residuals[residual_kind],
    )
    monkeypatch.setattr(
        "ldvh.helper.operations.fact_creation_operation.create_fact_object",
        lambda *_args, **_kwargs: creation,
    )

    response = handle_request(
        "call",
        "create-fact-object",
        _create_payload(workspace, project, basis, _spark()),
    ).response

    assert response["outcome"] == "error"
    _assert_creation_result_matrix(response)
    assert [change["status"] for change in response["changes"]] == [
        "target-created",
        "target-remove-unconfirmed",
    ]
    assert expected in response["changes"][1]["summary"]
    assert excluded not in response["changes"][1]["summary"]
    assert response["verification"][0]["status"] == verification_status
    assert response["result"]["target_namespace"] == {
        "canonical_path": canonical_path,
        "create_namespace_state": "created",
        "post_create_readback": "failed",
        "rollback_state": "uncertain",
        "final_observation": final_observation,
    }
    assert "actual_ref" not in response["result"]
    residual_source = next(source for source in response["sources"] if source["kind"] == "working_tree")
    assert residual_source["details"]["check_status"] == residuals[residual_kind].check_status


def test_create_study_validates_markdown_carrier_and_external_urls(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    basis = _prepare(workspace, project, "study")
    study = {
        "frontmatter": {
            "title": "Controlled Study creation",
            "status": "active",
            "report_kind": "external_research",
            "urls": [
                {
                    "ref": "https://example.invalid/controlled-study-evidence",
                    "title": "Controlled Study evidence",
                    "summary": "External material used by the test Study.",
                }
            ],
            "research_question": "Can Code create a complete Study only after AI supplies its semantics?",
            "abstract": (
                "The controlled path validates frontmatter, report structure, and external material before creation."
            ),
            "research_intent": (
                "Confirm that a Study can preserve the project reason for researching an external contract."
            ),
            "recommendation_summary": (
                "Use the controlled creation path only after the complete research report is ready."
            ),
        },
        "body": """
## 研究问题

### 项目问题

验证受控创建是否承接完整 Study。

### 外部问题

外部资料如何说明完整载体？

## 输入与边界

### 已读外部资料

阅读外部资料，并保持发现处于其公开范围内。

### 本次边界

不把测试资料提升为项目规则。

## 关键发现

### 创建后回读

Code 可以在最终分配身份后验证完整载体，启发是保留回读；不证明研究结论。

### 草案无副作用

草案阶段不写入正式文件，启发是先形成完整输入；不等于跳过最终校验。

## 建议

### 可立即采用的工作方式

继续保持草案阶段无正式文件副作用。

## 后续分流

| 分流类别 | 触发条件 | 下一步或不创建理由 |
|---|---|---|
| 无需对象化 | 仅验证创建路径 | 不创建额外对象。 |
""",
    }

    response = handle_request(
        "call",
        "create-fact-object",
        _create_payload(workspace, project, basis, study),
    ).response

    assert response["outcome"] == "ok"
    _assert_creation_result_matrix(response, "study")
    assert response["result"]["carrier"] == "markdown"
    frontmatter = response["result"]["fact_object"]["frontmatter"]
    assert object_uid_from_locator("study", frontmatter["object_id"]) == frontmatter["object_uid"]
    assert response["result"]["fact_object"]["body"].lstrip().startswith("## 研究问题")
    assert (project / response["result"]["target_namespace"]["canonical_path"]).is_file()


def test_real_cli_prepares_and_creates_fact_object(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    prepare = subprocess.run(
        [str(HELPER_EXECUTABLE), "call", "prepare-fact-object-draft"],
        cwd=project,
        input=json.dumps(
            {
                "work_object_locators": [str(project)],
                "arguments": {
                    "workspace_root": str(workspace),
                    "governed_project_id": "sample",
                    "fact_type_key": "spark",
                },
            }
        ),
        text=True,
        capture_output=True,
        check=False,
    )
    prepare_response = json.loads(prepare.stdout)
    assert prepare.returncode == 0
    assert prepare.stderr == ""
    assert_common_response(prepare_response)

    create = subprocess.run(
        [str(HELPER_EXECUTABLE), "call", "create-fact-object"],
        cwd=project,
        input=_create_payload(workspace, project, prepare_response["result"], _spark("Real CLI")),
        text=True,
        capture_output=True,
        check=False,
    )
    create_response = json.loads(create.stdout)
    assert create.returncode == 0
    assert create.stderr == ""
    assert_common_response(create_response)
    assert create_response["outcome"] == "ok"
    created = create_response["result"]["fact_object"]
    assert object_uid_from_locator("spark", created["object_id"]) == created["object_uid"]
