from __future__ import annotations

import hashlib
import json
import os
import subprocess
import time
from dataclasses import replace
from pathlib import Path

import pytest
from conftest import HELPER_EXECUTABLE, assert_common_response

from ldvh.facts import file_asset_deletion
from ldvh.filesystem import exclusive_relative_file_lock
from ldvh.helper.service import handle_request


def _git(project: Path, *arguments: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(project), *arguments],
        check=True,
        capture_output=True,
    ).stdout


def _fixture(tmp_path: Path) -> tuple[Path, Path]:
    workspace = tmp_path / "workspace"
    project = workspace / "project"
    project.mkdir(parents=True)
    _git(project, "init", "-q")
    (workspace / "LDVH-GOVERNED-PROJECTS.yaml").write_text(
        "\n".join(
            [
                "product_name: Test Workspace",
                "product_description: FileAsset safe deletion tests.",
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
    for directory in ("sparks", "workcases", "adrs", "pitfalls", "studies"):
        (project / "ldvh-base" / directory).mkdir(parents=True, exist_ok=True)
    return workspace, project


def _create_active(workspace: Path, project: Path, source: Path) -> dict[str, object]:
    prepared = handle_request(
        "call",
        "prepare-file-asset-intake",
        json.dumps(
            {
                "work_object_locators": [str(project)],
                "arguments": {
                    "workspace_root": str(workspace),
                    "governed_project_id": "sample",
                    "source_path": str(source),
                },
            }
        ),
    ).response
    assert prepared["outcome"] == "ok"
    created = handle_request(
        "call",
        "create-file-asset",
        json.dumps(
            {
                "work_object_locators": [str(project)],
                "arguments": {
                    "workspace_root": str(workspace),
                    "intake_basis": prepared["result"]["intake_basis"],
                    "fact_object": {
                        "title": "待安全删除的审计原文",
                        "filename": source.name,
                        "media_type": "text/markdown",
                        "signature": {"signer_type": "human"},
                        "change_log": [
                            {
                                "signature": {"signer_type": "human"},
                                "session_id": "file-asset-delete-creation-test",
                                "at": "2026-08-03T00:00:00+08:00",
                                "summary": "创建用于验证安全删除的资产。",
                            }
                        ],
                    },
                },
            }
        ),
    ).response
    assert created["outcome"] == "ok"
    return created


def _delete_payload(
    workspace: Path,
    project: Path,
    fingerprint: str,
    *,
    authorization: bool = True,
) -> str:
    payload: dict[str, object] = {
        "work_object_locators": [str(project)],
        "arguments": {
            "workspace_root": str(workspace),
            "fact_ref": {
                "governed_project_id": "sample",
                "fact_type_key": "file-asset",
                "object_id": "file-asset-0001",
            },
            "expected_content_fingerprint": fingerprint,
            "deletion_summary": "Human 确认当前没有继续保留该 payload 的需要。",
            "change_log_entry": {
                "signature": {"signer_type": "human"},
                "session_id": "file-asset-delete-test",
                "summary": "执行受控安全删除并保留 tombstone。",
            },
        },
    }
    if authorization:
        payload["authorization_reference"] = [
            {"kind": "human", "locator": "conversation:safe-delete-file-asset-0001"}
        ]
    return json.dumps(payload)


def _workcase_create_payload(workspace: Path, project: Path) -> str:
    prepared = handle_request(
        "call",
        "prepare-fact-object-draft",
        json.dumps(
            {
                "work_object_locators": [str(project)],
                "arguments": {
                    "workspace_root": str(workspace),
                    "governed_project_id": "sample",
                    "fact_type_key": "workcase",
                },
            }
        ),
    ).response
    assert prepared["outcome"] == "ok"
    basis = prepared["result"]
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
                "fact_object": {
                    "title": "Concurrent FileAsset consumer",
                    "status": "open",
                    "summary": "Waiting for Human execution approval.",
                    "waiting_on": "Human execution approval.",
                    "priority": "P2",
                    "goal": "Retain one FileAsset relation.",
                    "scope": "One concurrency fixture.",
                    "success_criterion_definitions": [
                        {
                            "criterion_id": "criterion-01",
                            "statement": "The relation remains mechanically valid.",
                        }
                    ],
                    "phase": "human_plan_confirming",
                    "plan_version": 1,
                    "work_items": [
                        {
                            "item_id": "item-01",
                            "goal": "Reference the FileAsset.",
                            "expected_result": "The relation is retained.",
                            "status": "pending",
                        }
                    ],
                    "creation_reviews": [
                        {
                            "reviewer": "concurrency-fixture-reviewer",
                            "reviewed_at": "2026-07-31T09:00:00+08:00",
                            "subject_version": 1,
                            "scope": "Goal, scope, criteria, method and risk.",
                            "conclusion": "pass",
                        }
                    ],
                    "execution_authorization": {
                        "authorized_actions": [
                            {
                                "action_id": "authorization-concurrency-fixture",
                                "summary": "Create one bounded WorkCase fixture.",
                                "target_scope": "Temporary test project only.",
                                "effect_scope": "One WorkCase carrier.",
                                "risk_summary": "Fixture-only write.",
                                "rollback_summary": "Remove the fixture.",
                                "rule_refs": ["specs/21-WorkCase-工作项.md"],
                            }
                        ],
                        "action_ceiling": "One fixture WorkCase.",
                        "allowed_adjustments": "None.",
                        "verification_and_rollback": "Read final FileAsset and WorkCase state.",
                        "out_of_bounds_handling": "Stop.",
                        "prohibited_actions": ["Writing outside the fixture project."],
                    },
                    "relations": [
                        {
                            "relation_key": "has-file-asset",
                            "target": {
                                "governed_project_id": "sample",
                                "fact_type_key": "file-asset",
                                "object_id": "file-asset-0001",
                            },
                        }
                    ],
                },
            },
        }
    )


def _read_payload(workspace: Path, project: Path) -> str:
    return json.dumps(
        {
            "work_object_locators": [str(project)],
            "arguments": {
                "workspace_root": str(workspace),
                "fact_refs": [
                    {
                        "governed_project_id": "sample",
                        "fact_type_key": "file-asset",
                        "object_id": "file-asset-0001",
                    }
                ],
            },
        }
    )


def _fingerprint(workspace: Path, project: Path) -> str:
    response = handle_request("call", "read-fact-objects", _read_payload(workspace, project)).response
    item = response["result"]["items"][0]
    assert item["check_status"] == "mechanically_valid"
    return item["content_fingerprint"]


def _write_referring_closed_workcase(project: Path) -> None:
    (project / "ldvh-base/workcases/workcase-0001.yaml").write_text(
        """object_id: workcase-0001
fact_type_key: workcase
title: Closed audit consumer
created_at: 2026-07-31T09:00:00+08:00
updated_at: 2026-07-31T11:00:00+08:00
status: closed
goal: Consume one audit FileAsset
scope: One bounded audit
success_criterion_definitions:
  - criterion_id: criterion-01
    statement: The audit was reviewed
success_criterion_results:
  - criterion_id: criterion-01
    outcome: satisfied
    summary: The audit was reviewed
result_summary: The audit was reviewed
validation_summary: The closed record was read back
closure_outcome: completed
disposition_summary: The bounded audit is complete
relations:
  - relation_key: has-file-asset
    target:
      governed_project_id: sample
      fact_type_key: file-asset
      object_id: file-asset-0001
""",
        encoding="utf-8",
    )


@pytest.mark.skipif(os.name != "posix", reason="safe deletion requires POSIX directory exchange")
def test_active_payload_is_removed_and_deleted_tombstone_is_readable(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    source = tmp_path / "external-audit.md"
    source.write_text("审计原始内容。\n", encoding="utf-8")
    created = _create_active(workspace, project, source)
    assert created["result"]["actual_ref"]["object_id"] == "file-asset-0001"
    fingerprint = _fingerprint(workspace, project)
    _git(project, "add", "ldvh-base/file-assets")
    _git(
        project,
        "-c",
        "user.name=LDVH Test",
        "-c",
        "user.email=ldvh@example.invalid",
        "commit",
        "-qm",
        "test: establish active FileAsset",
    )

    deleted = handle_request(
        "call",
        "delete-file-asset",
        _delete_payload(workspace, project, fingerprint),
    ).response

    assert_common_response(deleted)
    assert deleted["outcome"] == "ok"
    directory = project / "ldvh-base/file-assets/file-asset-0001"
    assert {path.name for path in directory.iterdir()} == {"file-asset.yaml"}
    assert deleted["result"]["payload_removed"] is True
    recovery = deleted["result"]["recovery"]
    assert recovery["commit"] == _git(project, "rev-parse", "HEAD").decode().strip()
    assert recovery["path"] == "ldvh-base/file-assets/file-asset-0001/payload"
    assert recovery["blob_oid"] == _git(project, "rev-parse", "HEAD:" + recovery["path"]).decode().strip()

    read = handle_request("call", "read-fact-objects", _read_payload(workspace, project)).response
    item = read["result"]["items"][0]
    assert read["outcome"] == "ok"
    assert item["check_status"] == "mechanically_valid"
    assert item["fact_object"]["status"] == "deleted"
    assert item["file_asset_payload"] is None

    integrity = handle_request(
        "call",
        "check-fact-integrity",
        json.dumps(
            {
                "work_object_locators": [str(project)],
                "arguments": {"workspace_root": str(workspace)},
            }
        ),
    ).response
    assert integrity["outcome"] == "ok"
    assert integrity["result"]["status"] == "complete"


@pytest.mark.skipif(os.name != "posix", reason="cross-process coordination requires POSIX locking")
def test_real_workcase_create_and_file_asset_delete_are_serialized_across_processes(
    tmp_path: Path,
) -> None:
    workspace, project = _fixture(tmp_path)
    source = tmp_path / "concurrent-audit.md"
    source.write_text("并发引用测试内容。\n", encoding="utf-8")
    _create_active(workspace, project, source)
    fingerprint = _fingerprint(workspace, project)
    _git(project, "add", "ldvh-base/file-assets")
    _git(
        project,
        "-c",
        "user.name=LDVH Test",
        "-c",
        "user.email=ldvh@example.invalid",
        "commit",
        "-qm",
        "test: establish concurrent FileAsset baseline",
    )
    create_payload = _workcase_create_payload(workspace, project)
    delete_payload = _delete_payload(workspace, project, fingerprint)
    project_hash = hashlib.sha256(b"sample").hexdigest()[:24]
    lock_path = Path("ldvh/fact-relations") / f"{project_hash}.lock"

    with exclusive_relative_file_lock(project / ".git", lock_path):
        create = subprocess.Popen(
            [str(HELPER_EXECUTABLE), "call", "create-fact-object"],
            cwd=project,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        delete = subprocess.Popen(
            [str(HELPER_EXECUTABLE), "call", "delete-file-asset"],
            cwd=project,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        assert create.stdin is not None and delete.stdin is not None
        create.stdin.write(create_payload)
        create.stdin.close()
        delete.stdin.write(delete_payload)
        delete.stdin.close()
        time.sleep(0.3)
        assert create.poll() is None
        assert delete.poll() is None

    assert create.stdout is not None and create.stderr is not None
    assert delete.stdout is not None and delete.stderr is not None
    create_response = json.loads(create.stdout.read())
    delete_response = json.loads(delete.stdout.read())
    create_stderr = create.stderr.read()
    delete_stderr = delete.stderr.read()
    assert create.wait(timeout=30) in {0, 1, 4}
    assert delete.wait(timeout=30) in {0, 1, 4}
    assert create_stderr == ""
    assert delete_stderr == ""
    assert [create_response["outcome"], delete_response["outcome"]].count("ok") == 1

    read = handle_request("call", "read-fact-objects", _read_payload(workspace, project)).response
    item = read["result"]["items"][0]
    workcase_exists = (project / "ldvh-base/workcases/workcase-0001.yaml").is_file()
    assert item["check_status"] == "mechanically_valid"
    assert (item["fact_object"]["status"], workcase_exists) in {
        ("active", True),
        ("deleted", False),
    }


@pytest.mark.skipif(os.name != "posix", reason="safe deletion requires POSIX directory exchange")
def test_uncommitted_active_file_asset_has_no_recovery_anchor_and_is_not_changed(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    source = tmp_path / "uncommitted.md"
    source.write_text("未提交内容。\n", encoding="utf-8")
    created = _create_active(workspace, project, source)
    assert created["result"]["actual_ref"]["object_id"] == "file-asset-0001"
    fingerprint = _fingerprint(workspace, project)

    response = handle_request(
        "call",
        "delete-file-asset",
        _delete_payload(workspace, project, fingerprint),
    ).response

    assert response["outcome"] == "unavailable"
    directory = project / "ldvh-base/file-assets/file-asset-0001"
    assert {path.name for path in directory.iterdir()} == {"file-asset.yaml", "payload"}
    assert "git_anchor_unavailable" in response["gaps"][0]["summary"]


def test_delete_requires_human_authorization_reference(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    response = handle_request(
        "call",
        "delete-file-asset",
        _delete_payload(workspace, project, "a" * 64, authorization=False),
    ).response

    assert response["outcome"] == "invalid_request"
    assert "authorization_reference" in response["gaps"][0]["summary"]


@pytest.mark.skipif(os.name != "posix", reason="safe deletion requires POSIX directory exchange")
def test_stale_content_fingerprint_rejects_without_changing_active_carrier(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    source = tmp_path / "stale.md"
    source.write_text("仍保留的内容。\n", encoding="utf-8")
    _create_active(workspace, project, source)

    response = handle_request(
        "call",
        "delete-file-asset",
        _delete_payload(workspace, project, "a" * 64),
    ).response

    assert response["outcome"] == "rejected"
    assert "conflict" in response["gaps"][0]["summary"]
    directory = project / "ldvh-base/file-assets/file-asset-0001"
    assert {path.name for path in directory.iterdir()} == {"file-asset.yaml", "payload"}


@pytest.mark.skipif(os.name != "posix", reason="safe deletion requires POSIX directory exchange")
def test_protected_incoming_reference_rejects_before_payload_removal(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, project = _fixture(tmp_path)
    source = tmp_path / "referenced.md"
    source.write_text("仍被 WorkCase 引用。\n", encoding="utf-8")
    _create_active(workspace, project, source)
    fingerprint = _fingerprint(workspace, project)
    monkeypatch.setattr(
        file_asset_deletion,
        "_incoming_references",
        lambda _command: (("workcase-0001",), True),
    )

    response = handle_request(
        "call",
        "delete-file-asset",
        _delete_payload(workspace, project, fingerprint),
    ).response

    assert response["outcome"] == "rejected"
    assert "incoming_reference" in response["gaps"][0]["summary"]
    assert response["result"]["incoming_reference_scan"] == {
        "complete": True,
        "incoming_refs": ["workcase-0001"],
    }
    directory = project / "ldvh-base/file-assets/file-asset-0001"
    assert {path.name for path in directory.iterdir()} == {"file-asset.yaml", "payload"}


@pytest.mark.skipif(os.name != "posix", reason="safe deletion requires POSIX directory exchange")
def test_real_workcase_scan_blocks_a_protected_incoming_reference(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    source = tmp_path / "really-referenced.md"
    source.write_text("真实 WorkCase 引用的内容。\n", encoding="utf-8")
    _create_active(workspace, project, source)
    fingerprint = _fingerprint(workspace, project)
    _write_referring_closed_workcase(project)

    response = handle_request(
        "call",
        "delete-file-asset",
        _delete_payload(workspace, project, fingerprint),
    ).response

    assert response["outcome"] == "rejected"
    assert response["result"]["incoming_reference_scan"] == {
        "complete": True,
        "incoming_refs": ["workcase-0001"],
    }
    directory = project / "ldvh-base/file-assets/file-asset-0001"
    assert {path.name for path in directory.iterdir()} == {"file-asset.yaml", "payload"}


@pytest.mark.skipif(os.name != "posix", reason="safe deletion requires POSIX directory exchange")
def test_invalid_workcase_makes_zero_incoming_reference_proof_unavailable(tmp_path: Path) -> None:
    workspace, project = _fixture(tmp_path)
    source = tmp_path / "invalid-peer.md"
    source.write_text("不能在 peer 无效时删除。\n", encoding="utf-8")
    _create_active(workspace, project, source)
    fingerprint = _fingerprint(workspace, project)
    (project / "ldvh-base/workcases/workcase-0001.yaml").write_text(
        "object_id: workcase-0001\nfact_type_key: workcase\nstatus: closed\n",
        encoding="utf-8",
    )

    response = handle_request(
        "call",
        "delete-file-asset",
        _delete_payload(workspace, project, fingerprint),
    ).response

    assert response["outcome"] == "unavailable"
    assert "incoming_scan_unavailable" in response["gaps"][0]["summary"]
    directory = project / "ldvh-base/file-assets/file-asset-0001"
    assert {path.name for path in directory.iterdir()} == {"file-asset.yaml", "payload"}


@pytest.mark.skipif(os.name != "posix", reason="safe deletion requires POSIX directory exchange")
def test_committed_tombstone_with_cleanup_residue_is_not_reported_as_success(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, project = _fixture(tmp_path)
    source = tmp_path / "residue.md"
    source.write_text("删除事务故障样本。\n", encoding="utf-8")
    _create_active(workspace, project, source)
    fingerprint = _fingerprint(workspace, project)
    _git(project, "add", "ldvh-base/file-assets")
    _git(
        project,
        "-c",
        "user.name=LDVH Test",
        "-c",
        "user.email=ldvh@example.invalid",
        "commit",
        "-qm",
        "test: establish residue baseline",
    )
    original = file_asset_deletion.atomic_replace_directory_relative_if_members_equal

    def committed_with_residue(*args: object, **kwargs: object):
        result = original(*args, **kwargs)
        assert result.namespace_state == "committed"
        return replace(result, durability="unknown", cleanup="residue")

    monkeypatch.setattr(
        file_asset_deletion,
        "atomic_replace_directory_relative_if_members_equal",
        committed_with_residue,
    )

    response = handle_request(
        "call",
        "delete-file-asset",
        _delete_payload(workspace, project, fingerprint),
    ).response

    assert response["outcome"] == "unavailable"
    assert response["result"]["transaction"] == {
        "status": "deleted_with_residue",
        "namespace_state": "committed",
        "durability": "unknown",
        "cleanup": "residue",
    }
    assert response["verification"] == []
    assert response["changes"][0]["status"] == "target-deleted"


@pytest.mark.skipif(os.name != "posix", reason="safe deletion requires POSIX directory exchange")
def test_payload_drift_during_incoming_scan_fails_second_cas_without_deleting(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, project = _fixture(tmp_path)
    source = tmp_path / "drift-during-scan.md"
    source.write_text("删除请求所见的原始内容。\n", encoding="utf-8")
    _create_active(workspace, project, source)
    fingerprint = _fingerprint(workspace, project)
    _git(project, "add", "ldvh-base/file-assets")
    _git(
        project,
        "-c",
        "user.name=LDVH Test",
        "-c",
        "user.email=ldvh@example.invalid",
        "commit",
        "-qm",
        "test: establish second CAS baseline",
    )
    payload = project / "ldvh-base/file-assets/file-asset-0001/payload"

    def drift_then_finish(_command):
        payload.write_bytes(b"different bytes introduced during relation scan\n")
        return (), True

    monkeypatch.setattr(file_asset_deletion, "_incoming_references", drift_then_finish)

    response = handle_request(
        "call",
        "delete-file-asset",
        _delete_payload(workspace, project, fingerprint),
    ).response

    assert response["outcome"] == "rejected"
    assert "conflict" in response["gaps"][0]["summary"]
    directory = payload.parent
    assert {path.name for path in directory.iterdir()} == {"file-asset.yaml", "payload"}
    assert "status: active" in (directory / "file-asset.yaml").read_text(encoding="utf-8")
