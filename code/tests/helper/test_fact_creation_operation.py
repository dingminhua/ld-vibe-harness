from __future__ import annotations

import json
import os
import stat
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from conftest import HELPER_EXECUTABLE, assert_common_response

from ldvh.facts.models import FactIssue
from ldvh.facts.repository import FactReadResult
from ldvh.helper.operations import fact_creation_operation
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


def _spark(title: str = "Controlled creation") -> dict[str, object]:
    return {
        "title": title,
        "status": "open",
        "source_refs": [{"kind": "repository-path", "locator": "docs/input.md"}],
        "summary": "AI supplied semantic content; Code owns identity and timestamps.",
        "priority": "P2",
    }


def _workcase(*, status: str = "open") -> dict[str, object]:
    fact_object: dict[str, object] = {
        "title": "Controlled WorkCase",
        "status": status,
        "source_refs": [{"kind": "repository-path", "locator": "docs/input.md"}],
        "summary": "Waiting for Human execution approval.",
        "resume_from": "Present plan version 1 for Human approval.",
        "waiting_on": "Human execution approval.",
        "priority": "P2",
        "goal": "Verify controlled creation.",
        "scope": "One test object.",
        "success_criteria": ["The object passes write-back validation."],
        "phase": "human_plan_confirming",
        "plan_version": 1,
        "work_items": [
            {
                "item_id": "item-01",
                "goal": "Create and validate one WorkCase.",
                "expected_result": "The object passes write-back validation.",
                "status": "pending",
                "approach_summary": "Use controlled creation and read back the object.",
            }
        ],
        "creation_reviews": [
            {
                "reviewer": "independent-creation-reviewer",
                "reviewed_at": "2026-07-14T09:00:00+08:00",
                "subject_version": 1,
                "scope": "Goal, scope, criteria, work items, method, validation and risks.",
                "conclusion": "pass",
                "feedback": ["The plan is bounded and testable."],
                "controller_resolution": "1. Accepted; no change required.",
            }
        ],
    }
    if status == "blocked":
        fact_object["blocking_summary"] = "Required external evidence is not yet available."
        fact_object["evidence_refs"] = [{"kind": "repository-path", "locator": "docs/blocker.md"}]
    return fact_object


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
                "source_refs": [{"kind": "repository-path", "locator": "docs/input.md"}],
                "evidence_refs": [{"kind": "repository-path", "locator": "docs/evidence.md"}],
                "decision_question": "Who assigns the final object identity?",
                "decision": "Code assigns it in the creation critical section.",
                "applicability": "Single-object V4 fact creation.",
                "rationale": "A shared allocator avoids same-repository identity collisions.",
                "consequences": "Draft candidate identities are explicitly non-reserved.",
                "decided_at": "2026-07-13T09:00:00+08:00",
            },
        ),
        (
            "pitfall",
            {
                "title": "Candidate identity treated as reserved",
                "status": "active",
                "source_refs": [{"kind": "repository-path", "locator": "docs/input.md"}],
                "evidence_refs": [{"kind": "repository-path", "locator": "docs/evidence.md"}],
                "applicability": "Concurrent V4 fact creation.",
                "validation_summary": "Two drafts can safely receive different final identities.",
                "symptoms": "Concurrent drafts expect the same final ID.",
                "trigger_conditions": "A candidate ID is mistaken for a reservation.",
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
    assert response["result"]["actual_ref"]["fact_type_key"] == fact_type_key
    assert response["result"]["actual_ref"]["object_id"] == f"{fact_type_key}-0001"


def test_create_accepts_workcase_blocked_initial_state_defined_by_type_source(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    basis = _prepare(workspace, project, "workcase")

    response = handle_request(
        "call",
        "create-fact-object",
        _create_payload(workspace, project, basis, _workcase(status="blocked")),
    ).response

    assert_common_response(response)
    assert response["outcome"] == "ok"
    assert response["result"]["fact_object"]["status"] == "blocked"
    assert response["result"]["fact_object"]["blocking_summary"]


def _create_payload(
    workspace: Path,
    project: Path,
    basis: dict[str, object],
    fact_object: dict[str, object],
) -> str:
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
                        "candidate_object_id",
                        "schema_fingerprint",
                        "worktree_fingerprint",
                    )
                },
                "fact_object": fact_object,
            },
        }
    )


def test_prepare_has_no_canonical_side_effect_and_create_injects_managed_fields(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)

    basis = _prepare(workspace, project)

    assert basis["candidate_object_id"] == "spark-0001"
    assert not (project / "facts").exists()
    response = handle_request(
        "call",
        "create-fact-object",
        _create_payload(workspace, project, basis, _spark()),
    ).response
    assert_common_response(response)
    assert response["outcome"] == "ok"
    assert response["result"]["requested_candidate_id"] == "spark-0001"
    assert response["result"]["actual_ref"]["object_id"] == "spark-0001"
    assert response["scope"]["requested"] == response["scope"]["completed"]
    assert response["scope"]["not_completed"] == []
    fact_object = response["result"]["fact_object"]
    assert fact_object["object_id"] == "spark-0001"
    assert fact_object["fact_type_key"] == "spark"
    assert fact_object["created_at"] == fact_object["updated_at"]
    assert (project / response["result"]["canonical_path"]).is_file()


def test_create_reports_committed_namespace_when_directory_sync_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, project = _fixture(tmp_path)
    basis = _prepare(workspace, project)
    real_fsync = os.fsync
    target_directory = project / "facts/sparks"

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
    assert response["changes"][0]["status"] == "created"
    assert "durability=unknown" in response["changes"][0]["summary"]
    assert (project / "facts/sparks/spark-0001.yaml").is_file()


def test_create_fails_before_allocator_mutation_when_platform_durability_is_not_approved(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, project = _fixture(tmp_path)
    basis = _prepare(workspace, project)
    monkeypatch.setattr(fact_creation_operation, "durable_writes_enabled", lambda: False)

    response = handle_request(
        "call",
        "create-fact-object",
        _create_payload(workspace, project, basis, _spark()),
    ).response

    assert response["outcome"] == "unavailable"
    assert "file-only" in response["summary"]
    assert not (project / ".git/ldvh").exists()
    assert not (project / "facts").exists()


def test_two_ai_drafts_with_same_candidate_receive_distinct_final_ids(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    first_basis = _prepare(workspace, project)
    second_basis = _prepare(workspace, project)
    assert first_basis["candidate_object_id"] == second_basis["candidate_object_id"] == "spark-0001"
    payloads = (
        _create_payload(workspace, project, first_basis, _spark("First concurrent draft")),
        _create_payload(workspace, project, second_basis, _spark("Second concurrent draft")),
    )

    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = tuple(
            executor.map(lambda payload: handle_request("call", "create-fact-object", payload).response, payloads)
        )

    assert all(response["outcome"] == "ok" for response in responses)
    actual_ids = {response["result"]["actual_ref"]["object_id"] for response in responses}
    assert actual_ids == {"spark-0001", "spark-0002"}
    assert sorted(path.name for path in (project / "facts" / "sparks").glob("*.yaml")) == [
        "spark-0001.yaml",
        "spark-0002.yaml",
    ]


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
    assert _prepare(workspace, project)["candidate_object_id"] == "spark-0001"


def test_create_revalidates_cross_type_relation_with_complete_schema_set(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    workcases = project / "facts" / "workcases"
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
                "source_refs:",
                "  - kind: repository-path",
                "    locator: docs/input.md",
                "summary: Waiting for Human execution approval",
                "resume_from: Present plan version 1 for Human approval",
                "waiting_on: Human execution approval",
                "priority: P2",
                "goal: Complete target",
                "scope: One object",
                "success_criteria:",
                "  - Target is complete",
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
                "    feedback:",
                "      - The plan is bounded and testable",
                "    controller_resolution: '1. Accepted; no change required.'",
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
    assert response["result"]["actual_ref"]["object_id"] == "spark-0001"


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


def test_existing_candidate_is_never_overwritten_and_allocator_advances(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    basis = _prepare(workspace, project)
    sparks = project / "facts" / "sparks"
    sparks.mkdir(parents=True)
    existing = sparks / "spark-0001.yaml"
    existing.write_text("manual collision\n", encoding="utf-8")

    response = handle_request(
        "call",
        "create-fact-object",
        _create_payload(workspace, project, basis, _spark()),
    ).response

    assert response["outcome"] == "ok"
    assert response["result"]["requested_candidate_id"] == "spark-0001"
    assert response["result"]["actual_ref"]["object_id"] == "spark-0002"
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
    assert main_response["result"]["actual_ref"]["object_id"] == "spark-0001"
    assert linked_basis["candidate_object_id"] == "spark-0002"
    assert linked_response["result"]["actual_ref"]["object_id"] == "spark-0002"
    assert (project / "facts" / "sparks" / "spark-0001.yaml").is_file()
    assert not (project / "facts" / "sparks" / "spark-0002.yaml").exists()
    assert (linked / "facts" / "sparks" / "spark-0002.yaml").is_file()


def test_failed_write_back_read_rolls_back_file_but_never_reuses_id(tmp_path: Path, monkeypatch) -> None:
    workspace, project = _fixture(tmp_path)
    basis = _prepare(workspace, project)
    monkeypatch.setattr(
        "ldvh.helper.operations.fact_creation_operation.read_fact_object",
        lambda *args, **kwargs: FactReadResult(
            "facts/sparks/spark-0001.yaml",
            "yaml",
            "invalid",
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
    assert response["changes"][0]["status"] == "rolled-back"
    assert not (project / "facts" / "sparks" / "spark-0001.yaml").exists()
    assert _prepare(workspace, project)["candidate_object_id"] == "spark-0002"


def test_create_study_validates_markdown_carrier_and_tracked_sources(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    docs = project / "docs"
    docs.mkdir()
    (docs / "question.md").write_text("Research request.\n", encoding="utf-8")
    (docs / "evidence.md").write_text("Observed evidence.\n", encoding="utf-8")
    _git(project, "add", "docs")
    basis = _prepare(workspace, project, "study")
    observed = "2026-07-13T09:00:00+08:00"
    study = {
        "frontmatter": {
            "title": "Controlled Study creation",
            "status": "active",
            "source_refs": [
                {
                    "kind": "repository-path",
                    "locator": "docs/question.md",
                    "observed_at": observed,
                }
            ],
            "evidence_refs": [
                {
                    "kind": "repository-path",
                    "locator": "docs/evidence.md",
                    "observed_at": observed,
                }
            ],
            "applicability": "This test repository and the current creation contract.",
            "validation_summary": "The tracked evidence file was read and mapped to the conclusion.",
            "research_question": "Can Code create a complete Study only after AI supplies its semantics?",
            "abstract": (
                "The controlled path validates frontmatter, report structure, and tracked evidence before creation."
            ),
        },
        "body": "\n\n".join(
            [
                "## 研究问题\n\n验证受控创建是否承接完整 Study。",
                "## 输入、方法与观察边界\n\n读取 docs/question.md 与 docs/evidence.md。",
                "## 关键发现\n\nCode 可以在最终分配身份后验证完整载体。",
                "## 结论与限制\n\n结论仅适用于当前测试仓库和当前契约。",
                "## 建议\n\n继续保持草案阶段无正式文件副作用。",
                "## 后续分流\n\n当前没有额外分流。",
            ]
        ),
    }

    response = handle_request(
        "call",
        "create-fact-object",
        _create_payload(workspace, project, basis, study),
    ).response

    assert response["outcome"] == "ok"
    assert response["result"]["carrier"] == "markdown"
    assert response["result"]["actual_ref"]["object_id"] == "study-0001"
    assert response["result"]["fact_object"]["body"].lstrip().startswith("## 研究问题")
    assert (project / "facts" / "studies" / "study-0001.md").is_file()


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
    assert create_response["result"]["actual_ref"]["object_id"] == "spark-0001"
