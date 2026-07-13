from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from conftest import assert_common_response

from ldvh.helper.service import handle_request

HELPER_EXECUTABLE = Path(sys.executable).with_name("ldvh")


def _git(project: Path, *arguments: str) -> None:
    subprocess.run(["git", "-C", str(project), *arguments], check=True, capture_output=True)


def _fixture(tmp_path: Path) -> tuple[Path, Path]:
    workspace = tmp_path / "workspace"
    project = workspace / "project"
    project.mkdir(parents=True)
    _git(project, "init", "-q")
    facts = project / "facts" / "sparks"
    facts.mkdir(parents=True)
    (facts / "spark-0001.yaml").write_text(
        "\n".join(
            [
                "object_id: spark-0001",
                "fact_type_key: spark",
                "title: Exact read",
                "created_at: 2026-07-14T09:00:00+08:00",
                "updated_at: 2026-07-14T10:00:00+08:00",
                "status: open",
                "source_refs:",
                "  - kind: repository-path",
                "    locator: docs/input.md",
                "summary: Read one object",
                "priority: P2",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (workspace / "LDVH-GOVERNED-PROJECTS.yaml").write_text(
        "\n".join(
            [
                "product_name: Test Workspace",
                "product_description: Fact operation tests.",
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


def _payload(workspace: Path, project: Path, *object_ids: str) -> str:
    return json.dumps(
        {
            "work_object_locators": [str(project)],
            "arguments": {
                "workspace_root": str(workspace),
                "fact_refs": [
                    {
                        "governed_project_id": "sample",
                        "fact_type_key": "spark",
                        "object_id": object_id,
                    }
                    for object_id in object_ids
                ],
            },
        }
    )


def test_exact_fact_read_preserves_valid_and_not_found_local_results(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)

    result = handle_request("call", "read-fact-objects", _payload(workspace, project, "spark-0001", "spark-9999"))
    response = result.response

    assert result.exit_code == 0
    assert_common_response(response)
    assert response["outcome"] == "ok"
    assert response["scope"]["governance_resolution"]["scope_status"] == "governed_single"
    assert response["scope"]["requested"] == response["scope"]["completed"]
    assert response["scope"]["not_completed"] == []
    assert [item["check_status"] for item in response["result"]["items"]] == [
        "mechanically_valid",
        "not_found",
    ]
    assert response["result"]["items"][0]["fact_object"]["summary"] == "Read one object"
    assert response["result"]["items"][1]["fact_object"] is None
    assert response["changes"] == []


def test_fact_read_rejects_invalid_selector_before_resolution() -> None:
    result = handle_request(
        "call",
        "read-fact-objects",
        json.dumps(
            {
                "arguments": {
                    "fact_refs": [{"governed_project_id": "sample", "fact_type_key": "spark", "object_id": "wrong"}]
                }
            }
        ),
    )

    assert result.exit_code == 2
    assert result.response["outcome"] == "invalid_request"
    assert "object_id" in result.response["gaps"][0]["summary"]


def test_fact_read_rejects_symlink_canonical_path(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    original = project / "facts" / "sparks" / "spark-0001.yaml"
    target = project / "real.yaml"
    original.replace(target)
    original.symlink_to(target)

    result = handle_request("call", "read-fact-objects", _payload(workspace, project, "spark-0001"))
    item = result.response["result"]["items"][0]

    assert result.response["outcome"] == "ok"
    assert item["check_status"] == "invalid"
    assert item["issues"][0]["category"] == "location"


def test_fact_read_checks_relation_targets_and_reachable_dag(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    directory = project / "facts" / "workcases"
    directory.mkdir()
    for object_id, target_id in (("workcase-0001", "workcase-0002"), ("workcase-0002", "workcase-0001")):
        (directory / f"{object_id}.yaml").write_text(
            "\n".join(
                [
                    f"object_id: {object_id}",
                    "fact_type_key: workcase",
                    "title: Dependency",
                    "created_at: 2026-07-14T09:00:00+08:00",
                    "updated_at: 2026-07-14T10:00:00+08:00",
                    "status: open",
                    "source_refs:",
                    "  - kind: repository-path",
                    "    locator: docs/input.md",
                    "summary: Current",
                    "priority: P2",
                    "goal: Finish",
                    "scope: One object",
                    "success_criteria:",
                    "  - Done",
                    "relations:",
                    "  - relation_key: depends-on",
                    "    target:",
                    "      governed_project_id: sample",
                    "      fact_type_key: workcase",
                    f"      object_id: {target_id}",
                    "",
                ]
            ),
            encoding="utf-8",
        )
    payload = json.dumps(
        {
            "work_object_locators": [str(project)],
            "arguments": {
                "workspace_root": str(workspace),
                "fact_refs": [
                    {
                        "governed_project_id": "sample",
                        "fact_type_key": "workcase",
                        "object_id": "workcase-0001",
                    }
                ],
            },
        }
    )

    result = handle_request("call", "read-fact-objects", payload)
    item = result.response["result"]["items"][0]

    assert result.response["outcome"] == "ok"
    assert item["check_status"] == "invalid"
    assert any(issue["category"] == "relation" and "有向循环" in issue["summary"] for issue in item["issues"])


def test_untracked_ignored_fact_is_invalid_but_tracked_dirty_content_is_current(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    ignore = project / ".gitignore"
    ignore.write_text("facts/\n", encoding="utf-8")

    ignored = handle_request("call", "read-fact-objects", _payload(workspace, project, "spark-0001"))
    assert ignored.response["result"]["items"][0]["check_status"] == "invalid"
    assert ignored.response["result"]["items"][0]["issues"][0]["category"] == "git-traceability"

    _git(project, "add", ".gitignore")
    _git(project, "add", "-f", "facts/sparks/spark-0001.yaml")
    _git(
        project,
        "-c",
        "user.name=LDVH Test",
        "-c",
        "user.email=ldvh@example.invalid",
        "commit",
        "-qm",
        "tracked fact",
    )
    fact = project / "facts" / "sparks" / "spark-0001.yaml"
    fact.write_text(fact.read_text(encoding="utf-8") + "implementation_private: true\n", encoding="utf-8")

    dirty = handle_request("call", "read-fact-objects", _payload(workspace, project, "spark-0001"))
    item = dirty.response["result"]["items"][0]
    assert item["check_status"] == "invalid"
    assert any(issue["field_path"] == "implementation_private" for issue in item["issues"])


def test_git_environment_cannot_redirect_governance_or_traceability(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, project = _fixture(tmp_path)
    monkeypatch.setenv("GIT_DIR", str(tmp_path / "attacker.git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(tmp_path / "attacker-worktree"))
    monkeypatch.setenv("GIT_INDEX_FILE", str(tmp_path / "attacker-index"))
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "core.excludesfile")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", str(tmp_path / "attacker-ignore"))

    result = handle_request("call", "read-fact-objects", _payload(workspace, project, "spark-0001"))
    assert result.response["outcome"] == "ok"
    assert result.response["result"]["items"][0]["check_status"] == "mechanically_valid"


def test_same_project_different_worktrees_do_not_form_one_read_boundary(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
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
    _git(project, "worktree", "add", "-qb", "linked-facts", str(linked))
    payload = json.dumps(
        {
            "work_object_locators": [str(project), str(linked)],
            "arguments": {
                "workspace_root": str(workspace),
                "fact_refs": [
                    {
                        "governed_project_id": "sample",
                        "fact_type_key": "spark",
                        "object_id": "spark-0001",
                    }
                ],
            },
        }
    )

    result = handle_request("call", "read-fact-objects", payload)

    assert result.response["outcome"] == "unavailable"
    assert result.response["result"] is None
    assert result.response["scope"]["completed"] == []
    assert result.response["scope"]["requested"] == result.response["scope"]["not_completed"]


def test_real_cli_reads_current_fact_object(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)

    completed = subprocess.run(
        [str(HELPER_EXECUTABLE), "call", "read-fact-objects"],
        cwd=project,
        input=_payload(workspace, project, "spark-0001"),
        text=True,
        capture_output=True,
        check=False,
    )
    response = json.loads(completed.stdout)

    assert completed.returncode == 0
    assert completed.stderr == ""
    assert_common_response(response)
    assert response["result"]["items"][0]["check_status"] == "mechanically_valid"


def test_malformed_mapping_key_is_local_to_one_requested_object(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    (project / "facts" / "sparks" / "spark-0002.yaml").write_text(
        (project / "facts" / "sparks" / "spark-0001.yaml")
        .read_text(encoding="utf-8")
        .replace("spark-0001", "spark-0002")
        .replace("summary: Read one object", "true: invalid-key\nsummary: Read one object"),
        encoding="utf-8",
    )

    result = handle_request("call", "read-fact-objects", _payload(workspace, project, "spark-0002", "spark-0001"))
    assert result.response["outcome"] == "ok"
    assert [item["check_status"] for item in result.response["result"]["items"]] == [
        "invalid",
        "mechanically_valid",
    ]


def test_wrong_project_reference_is_unavailable_and_not_completed(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    payload = json.loads(_payload(workspace, project, "spark-0001"))
    payload["arguments"]["fact_refs"][0]["governed_project_id"] = "another-project"

    result = handle_request("call", "read-fact-objects", json.dumps(payload))
    item = result.response["result"]["items"][0]
    assert result.response["outcome"] == "unavailable"
    assert item["check_status"] == "unavailable"
    assert result.response["scope"]["completed"] == []
    assert result.response["scope"]["not_completed"] == result.response["scope"]["requested"]
    assert result.response["gaps"]


def test_fact_reference_batch_has_a_bounded_size() -> None:
    refs = [
        {"governed_project_id": "sample", "fact_type_key": "spark", "object_id": f"spark-{index:04d}"}
        for index in range(1, 130)
    ]
    result = handle_request("call", "read-fact-objects", json.dumps({"arguments": {"fact_refs": refs}}))
    assert result.exit_code == 2
    assert result.response["outcome"] == "invalid_request"
    assert "1–128" in result.response["gaps"][0]["summary"]


def test_oversized_fact_is_unavailable_without_affecting_other_exact_reads(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    large = project / "facts" / "sparks" / "spark-0002.yaml"
    large.write_text(
        (project / "facts" / "sparks" / "spark-0001.yaml")
        .read_text(encoding="utf-8")
        .replace("spark-0001", "spark-0002")
        + "#"
        + ("x" * (4 * 1024 * 1024)),
        encoding="utf-8",
    )
    result = handle_request("call", "read-fact-objects", _payload(workspace, project, "spark-0002", "spark-0001"))
    assert result.response["outcome"] == "partial"
    assert [item["check_status"] for item in result.response["result"]["items"]] == [
        "unavailable",
        "mechanically_valid",
    ]


def test_closed_superseded_workcase_requires_a_routed_to_successor(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    directory = project / "facts" / "workcases"
    directory.mkdir()
    (directory / "workcase-0001.yaml").write_text(
        """object_id: workcase-0001
fact_type_key: workcase
title: Closed item
created_at: 2026-07-14T09:00:00+08:00
updated_at: 2026-07-14T10:00:00+08:00
status: closed
source_refs:
  - kind: repository-path
    locator: docs/input.md
evidence_refs:
  - kind: repository-path
    locator: docs/evidence.md
summary: Closed
goal: Finish
scope: One object
success_criteria:
  - Done
validation_summary: Validated
closure_outcome: superseded
disposition_summary: Replaced
closed_at: 2026-07-14T10:00:00+08:00
""",
        encoding="utf-8",
    )
    payload = json.loads(_payload(workspace, project, "spark-0001"))
    payload["arguments"]["fact_refs"][0].update({"fact_type_key": "workcase", "object_id": "workcase-0001"})
    item = handle_request("call", "read-fact-objects", json.dumps(payload)).response["result"]["items"][0]
    assert item["check_status"] == "invalid"
    assert any("routed-to" in issue["summary"] for issue in item["issues"])


def test_superseded_adr_requires_exactly_one_valid_incoming_source(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    directory = project / "facts" / "adrs"
    directory.mkdir()
    (directory / "adr-0001.yaml").write_text(
        """object_id: adr-0001
fact_type_key: adr
title: Old decision
created_at: 2026-07-14T09:00:00+08:00
updated_at: 2026-07-14T10:00:00+08:00
status: superseded
source_refs:
  - kind: repository-path
    locator: docs/input.md
evidence_refs:
  - kind: repository-path
    locator: docs/evidence.md
disposition_summary: Replaced
closed_at: 2026-07-14T10:00:00+08:00
decision_question: Which?
decision: A
applicability: This project
rationale: Lower risk
consequences: Maintain A
decided_at: 2026-07-14T08:00:00+08:00
""",
        encoding="utf-8",
    )
    payload = json.loads(_payload(workspace, project, "spark-0001"))
    payload["arguments"]["fact_refs"][0].update({"fact_type_key": "adr", "object_id": "adr-0001"})
    item = handle_request("call", "read-fact-objects", json.dumps(payload)).response["result"]["items"][0]
    assert item["check_status"] == "invalid"
    assert any("有且只有一个" in issue["summary"] for issue in item["issues"])

    successor = directory / "adr-0002.yaml"
    successor.write_text(
        """object_id: adr-0002
fact_type_key: adr
title: New decision
created_at: 2026-07-14T11:00:00+08:00
updated_at: 2026-07-14T12:00:00+08:00
status: active
source_refs:
  - kind: repository-path
    locator: docs/input.md
evidence_refs:
  - kind: repository-path
    locator: docs/evidence.md
decision_question: Which?
decision: B
applicability: This project
rationale: Better
consequences: Maintain B
decided_at: 2026-07-14T11:00:00+08:00
relations:
  - relation_key: supersedes
    target:
      governed_project_id: sample
      fact_type_key: adr
      object_id: adr-0001
""",
        encoding="utf-8",
    )
    payload["arguments"]["fact_refs"] = [
        {"governed_project_id": "sample", "fact_type_key": "adr", "object_id": "adr-0002"},
        {"governed_project_id": "sample", "fact_type_key": "adr", "object_id": "adr-0001"},
    ]
    out_of_range = handle_request("call", "read-fact-objects", json.dumps(payload)).response
    assert {item["check_status"] for item in out_of_range["result"]["items"]} == {"invalid"}
    assert any("时间顺序" in issue["summary"] for item in out_of_range["result"]["items"] for issue in item["issues"])

    successor.write_text(
        successor.read_text(encoding="utf-8")
        .replace("created_at: 2026-07-14T11:00:00+08:00", "created_at: 2026-07-14T09:30:00+08:00")
        .replace("decided_at: 2026-07-14T11:00:00+08:00", "decided_at: 2026-07-14T09:30:00+08:00"),
        encoding="utf-8",
    )
    valid = handle_request("call", "read-fact-objects", json.dumps(payload)).response
    assert [item["check_status"] for item in valid["result"]["items"]] == [
        "mechanically_valid",
        "mechanically_valid",
    ]

    invalid_candidate = directory / "adr-0003.yaml"
    invalid_candidate.write_text(
        successor.read_text(encoding="utf-8")
        .replace("adr-0002", "adr-0003", 1)
        .replace(
            "      object_id: adr-0001\n",
            """      object_id: adr-0001
  - relation_key: supersedes
    target:
      governed_project_id: sample
      fact_type_key: adr
      object_id: adr-9999
""",
        ),
        encoding="utf-8",
    )
    payload["arguments"]["fact_refs"] = [
        {"governed_project_id": "sample", "fact_type_key": "adr", "object_id": "adr-0001"},
        {"governed_project_id": "sample", "fact_type_key": "adr", "object_id": "adr-0002"},
        {"governed_project_id": "sample", "fact_type_key": "adr", "object_id": "adr-0003"},
    ]
    recovered = handle_request("call", "read-fact-objects", json.dumps(payload)).response
    assert [item["check_status"] for item in recovered["result"]["items"]] == [
        "mechanically_valid",
        "mechanically_valid",
        "invalid",
    ]


def test_project_relation_results_are_stable_across_request_order(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    directory = project / "facts" / "sparks"
    for object_id, target_type, target_id in (
        ("spark-0002", "workcase", "workcase-9999"),
        ("spark-0003", "spark", "spark-0002"),
    ):
        (directory / f"{object_id}.yaml").write_text(
            f"""object_id: {object_id}
fact_type_key: spark
title: Related
created_at: 2026-07-14T09:00:00+08:00
updated_at: 2026-07-14T10:00:00+08:00
status: open
source_refs:
  - kind: repository-path
    locator: docs/input.md
summary: Related object
priority: P2
relations:
  - relation_key: related-to
    target:
      governed_project_id: sample
      fact_type_key: {target_type}
      object_id: {target_id}
""",
            encoding="utf-8",
        )

    forward = handle_request(
        "call",
        "read-fact-objects",
        _payload(workspace, project, "spark-0002", "spark-0003"),
    ).response
    reverse = handle_request(
        "call",
        "read-fact-objects",
        _payload(workspace, project, "spark-0003", "spark-0002"),
    ).response
    forward_by_id = {item["requested_ref"]["object_id"]: item["check_status"] for item in forward["result"]["items"]}
    reverse_by_id = {item["requested_ref"]["object_id"]: item["check_status"] for item in reverse["result"]["items"]}
    assert forward_by_id == reverse_by_id == {"spark-0002": "invalid", "spark-0003": "invalid"}
