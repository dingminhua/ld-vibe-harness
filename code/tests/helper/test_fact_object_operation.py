from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest
from conftest import HELPER_EXECUTABLE, assert_common_response

from ldvh.helper.service import handle_request


def _git(project: Path, *arguments: str) -> None:
    subprocess.run(["git", "-C", str(project), *arguments], check=True, capture_output=True)


def _fixture(tmp_path: Path) -> tuple[Path, Path]:
    workspace = tmp_path / "workspace"
    project = workspace / "project"
    project.mkdir(parents=True)
    _git(project, "init", "-q")
    facts = project / "ldvh-base" / "sparks"
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


def _file_asset_payload(workspace: Path, project: Path, object_id: str = "file-asset-0001") -> str:
    return json.dumps(
        {
            "work_object_locators": [str(project)],
            "arguments": {
                "workspace_root": str(workspace),
                "fact_refs": [
                    {
                        "governed_project_id": "sample",
                        "fact_type_key": "file-asset",
                        "object_id": object_id,
                    }
                ],
            },
        }
    )


def _write_file_asset(project: Path, payload: bytes = b"external audit bytes\n") -> Path:
    directory = project / "ldvh-base/file-assets/file-asset-0001"
    directory.mkdir(parents=True)
    (directory / "file-asset.yaml").write_text(
        "\n".join(
            [
                "object_id: file-asset-0001",
                "fact_type_key: file-asset",
                "title: External audit",
                "created_at: 2026-07-31T10:00:00+08:00",
                "updated_at: 2026-07-31T10:00:00+08:00",
                "status: active",
                "filename: audit.bin",
                "media_type: application/octet-stream",
                f"size_bytes: {len(payload)}",
                f"content_sha256: {hashlib.sha256(payload).hexdigest()}",
                "signature:",
                "  signer_type: human",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (directory / "payload").write_bytes(payload)
    return directory


def test_exact_file_asset_read_returns_integrity_metadata_without_payload_bytes(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    payload = b"\x00\xffexternal audit bytes\n"
    _write_file_asset(project, payload)

    response = handle_request(
        "call",
        "read-fact-objects",
        _file_asset_payload(workspace, project),
    ).response
    item = response["result"]["items"][0]

    assert response["outcome"] == "ok"
    assert item["carrier"] == "file-asset-directory"
    assert item["check_status"] == "mechanically_valid"
    assert item["fact_object"]["signature"] == {"signer_type": "human"}
    assert item["file_asset_payload"] == {
        "canonical_path": "ldvh-base/file-assets/file-asset-0001/payload",
        "observed_size_bytes": len(payload),
        "observed_content_sha256": hashlib.sha256(payload).hexdigest(),
        "integrity_coverage": [
            "manifest-read",
            "members-closed",
            "payload-size-read",
            "payload-sha256-computed",
        ],
        "matches_manifest": True,
    }
    serialized = json.dumps(response, ensure_ascii=False)
    assert "external audit bytes" not in serialized


def test_exact_file_asset_read_uses_null_payload_metadata_when_read_is_incomplete(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    directory = _write_file_asset(project)
    (directory / "payload").unlink()

    response = handle_request(
        "call",
        "read-fact-objects",
        _file_asset_payload(workspace, project),
    ).response
    item = response["result"]["items"][0]

    assert response["outcome"] == "ok"
    assert item["check_status"] == "invalid"
    assert item["file_asset_payload"] is None


def test_exact_missing_file_asset_uses_null_payload_metadata(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)

    response = handle_request(
        "call",
        "read-fact-objects",
        _file_asset_payload(workspace, project),
    ).response
    item = response["result"]["items"][0]

    assert response["outcome"] == "ok"
    assert item["check_status"] == "not_found"
    assert item["file_asset_payload"] is None


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
    assert response["result"]["items"][0]["file_asset_payload"] is None
    raw = (project / "ldvh-base" / "sparks" / "spark-0001.yaml").read_bytes()
    assert response["result"]["items"][0]["content_fingerprint"] == hashlib.sha256(raw).hexdigest()
    assert response["result"]["items"][1]["fact_object"] is None
    assert response["result"]["items"][1]["file_asset_payload"] is None
    assert response["result"]["items"][1]["content_fingerprint"] is None
    assert response["changes"] == []


def test_parseable_invalid_fact_exposes_only_the_complete_cas_repair_snapshot(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    fact = project / "ldvh-base" / "sparks" / "spark-0001.yaml"
    fact.write_text(
        fact.read_text(encoding="utf-8").replace("priority: P2\n", ""),
        encoding="utf-8",
    )

    response = handle_request("call", "read-fact-objects", _payload(workspace, project, "spark-0001")).response
    item = response["result"]["items"][0]

    assert response["outcome"] == "ok"
    assert item["check_status"] == "invalid"
    assert item["fact_object"]["object_id"] == "spark-0001"
    assert "priority" not in item["fact_object"]
    raw = fact.read_bytes()
    assert item["content_fingerprint"] == hashlib.sha256(raw).hexdigest()
    assert any(issue["field_path"] == "priority" for issue in item["issues"])


def test_fact_read_supports_space_and_unicode_worktree_paths(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path / "工作区 with space")

    result = handle_request("call", "read-fact-objects", _payload(workspace, project, "spark-0001"))

    assert result.exit_code == 0
    assert result.response["outcome"] == "ok"
    assert result.response["result"]["items"][0]["check_status"] == "mechanically_valid"
    assert result.response["scope"]["governance_resolution"]["object_resolutions"][0]["git_worktree_root"] == str(
        project.resolve()
    )


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
    original = project / "ldvh-base" / "sparks" / "spark-0001.yaml"
    target = project / "real.yaml"
    original.replace(target)
    original.symlink_to(target)

    result = handle_request("call", "read-fact-objects", _payload(workspace, project, "spark-0001"))
    item = result.response["result"]["items"][0]

    assert result.response["outcome"] == "ok"
    assert item["check_status"] == "invalid"
    assert item["issues"][0]["category"] == "location"


def test_fact_read_rejects_symlinked_parent_directory(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    facts = project / "ldvh-base"
    sparks = facts / "sparks"
    real_sparks = project / "real-sparks"
    sparks.replace(real_sparks)
    try:
        sparks.symlink_to(real_sparks, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks are unavailable")

    result = handle_request("call", "read-fact-objects", _payload(workspace, project, "spark-0001"))
    item = result.response["result"]["items"][0]

    assert result.response["outcome"] == "ok"
    assert item["check_status"] == "invalid"
    assert "link/reparse" in item["issues"][0]["summary"]


def test_fact_read_checks_relation_targets_and_reachable_dag(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    directory = project / "ldvh-base" / "workcases"
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
                    "summary: Waiting for Human execution approval",
                    "waiting_on: Human execution approval",
                    "priority: P2",
                    "goal: Finish",
                    "scope: One object",
                    "success_criterion_definitions:",
                    "  - criterion_id: criterion-01",
                    "    statement: The bounded object is complete",
                    "phase: human_plan_confirming",
                    "plan_version: 1",
                    "work_items:",
                    "  - item_id: item-01",
                    "    goal: Finish the object",
                    "    expected_result: Done",
                    "    status: pending",
                    "    approach_summary: Complete the bounded target and validate it",
                    "creation_reviews:",
                    "  - reviewer: independent-dependency-reviewer",
                    "    reviewed_at: 2026-07-14T09:30:00+08:00",
                    "    subject_version: 1",
                    "    scope: Goal, scope, criteria, work items, method, validation and risks",
                    "    conclusion: pass",
                    "execution_authorization:",
                    "  authorized_actions:",
                    "    - action_id: authorization-dependency-fixture",
                    "      summary: Execute the approved dependency fixture plan.",
                    "      target_scope: Read fixture project only.",
                    "      effect_scope: Deterministic helper test workspace.",
                    "      risk_summary: No production effect; fixture data only.",
                    "      rollback_summary: Remove the fixture objects.",
                    "      rule_refs:",
                    "        - specs/21-WorkCase-工作项.md",
                    "  action_ceiling: Bounded to dependency fixture actions.",
                    "  allowed_adjustments: No adjustments beyond the recorded fixture summaries.",
                    "  verification_and_rollback: Run the read operation test suite.",
                    "  out_of_bounds_handling: Stop and return to Human.",
                    "  prohibited_actions:",
                    "    - Writing outside the fixture workspace.",
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


def test_fact_qualification_is_independent_of_git_status_but_content_rules_still_apply(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    ignore = project / ".gitignore"
    ignore.write_text("ldvh-base/\n", encoding="utf-8")

    ignored = handle_request("call", "read-fact-objects", _payload(workspace, project, "spark-0001"))
    assert ignored.response["result"]["items"][0]["check_status"] == "mechanically_valid"
    assert ignored.response["result"]["items"][0]["issues"] == []

    _git(project, "add", ".gitignore")
    _git(project, "add", "-f", "ldvh-base/sparks/spark-0001.yaml")
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
    fact = project / "ldvh-base" / "sparks" / "spark-0001.yaml"
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
    (project / "ldvh-base" / "sparks" / "spark-0002.yaml").write_text(
        (project / "ldvh-base" / "sparks" / "spark-0001.yaml")
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
    large = project / "ldvh-base" / "sparks" / "spark-0002.yaml"
    large.write_text(
        (project / "ldvh-base" / "sparks" / "spark-0001.yaml")
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


def test_current_closed_workcase_rejects_an_unregistered_unknown_field(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    directory = project / "ldvh-base" / "workcases"
    directory.mkdir()
    (directory / "workcase-0001.yaml").write_text(
        """object_id: workcase-0001
fact_type_key: workcase
title: Closed item
created_at: 2026-07-14T09:00:00+08:00
updated_at: 2026-07-14T10:00:00+08:00
status: closed
goal: Finish
scope: One object
success_criterion_definitions:
  - criterion_id: criterion-01
    statement: The bounded object is complete
success_criterion_results:
  - criterion_id: criterion-01
    outcome: satisfied
    summary: The bounded object was completed
result_summary: The bounded object was completed
validation_summary: The current closed result was read back successfully
closure_outcome: completed
disposition_summary: The original scope is complete with no remaining responsibility
unknown_field: rejected
""",
        encoding="utf-8",
    )
    payload = json.loads(_payload(workspace, project, "spark-0001"))
    payload["arguments"]["fact_refs"][0].update({"fact_type_key": "workcase", "object_id": "workcase-0001"})
    item = handle_request("call", "read-fact-objects", json.dumps(payload)).response["result"]["items"][0]
    assert item["check_status"] == "invalid"
    assert any(issue["field_path"] == "unknown_field" for issue in item["issues"])


def test_legacy_superseded_adr_status_and_relation_are_rejected(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    directory = project / "ldvh-base" / "adrs"
    directory.mkdir()
    (directory / "adr-0001.yaml").write_text(
        """object_id: adr-0001
fact_type_key: adr
title: Old decision
created_at: 2026-07-14T09:00:00+08:00
updated_at: 2026-07-14T10:00:00+08:00
status: superseded
disposition_summary: Replaced
decision_question: Which?
decision: A
applicability: This project
rationale: Lower risk
consequences: Maintain A
""",
        encoding="utf-8",
    )
    payload = json.loads(_payload(workspace, project, "spark-0001"))
    payload["arguments"]["fact_refs"][0].update({"fact_type_key": "adr", "object_id": "adr-0001"})
    item = handle_request("call", "read-fact-objects", json.dumps(payload)).response["result"]["items"][0]
    assert item["check_status"] == "invalid"
    assert any(issue["field_path"] == "status" for issue in item["issues"])

    successor = directory / "adr-0002.yaml"
    successor.write_text(
        """object_id: adr-0002
fact_type_key: adr
title: New decision
created_at: 2026-07-14T11:00:00+08:00
updated_at: 2026-07-14T12:00:00+08:00
status: active
decision_question: Which?
decision: B
applicability: This project
rationale: Better
consequences: Maintain B
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

    successor.write_text(
        successor.read_text(encoding="utf-8").replace(
            "created_at: 2026-07-14T11:00:00+08:00", "created_at: 2026-07-14T09:30:00+08:00"
        ),
        encoding="utf-8",
    )
    still_invalid = handle_request("call", "read-fact-objects", json.dumps(payload)).response
    assert {item["check_status"] for item in still_invalid["result"]["items"]} == {"invalid"}

    successor.write_text(
        successor.read_text(encoding="utf-8").replace(
            "status: active\n",
            "status: retired\ndisposition_summary: Replacement later retired without deleting its established edge\n",
        ),
        encoding="utf-8",
    )
    retained_legacy_relation = handle_request("call", "read-fact-objects", json.dumps(payload)).response
    assert {item["check_status"] for item in retained_legacy_relation["result"]["items"]} == {"invalid"}

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
    assert {item["check_status"] for item in recovered["result"]["items"]} == {"invalid"}


def test_project_relation_results_are_stable_across_request_order(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    directory = project / "ldvh-base" / "sparks"
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
