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
from ldvh.helper.operations import fact_update_operation
from ldvh.helper.service import handle_request


def _git(project: Path, *arguments: str) -> None:
    subprocess.run(["git", "-C", str(project), *arguments], check=True, capture_output=True)


def _fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    workspace = tmp_path / "workspace"
    project = workspace / "project"
    project.mkdir(parents=True)
    _git(project, "init", "-q")
    fact = project / "facts" / "sparks" / "spark-0001.yaml"
    fact.parent.mkdir(parents=True)
    fact.write_text(
        """object_id: spark-0001
fact_type_key: spark
title: Exact update
created_at: 2026-07-14T09:00:00+08:00
updated_at: 2026-07-14T10:00:00+08:00
status: open
source_refs:
  - kind: repository-path
    locator: docs/input.md
summary: Before update
priority: P2
""",
        encoding="utf-8",
    )
    (workspace / "LDVH-GOVERNED-PROJECTS.yaml").write_text(
        "\n".join(
            [
                "product_name: Test Workspace",
                "product_description: Fact update tests.",
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
    return workspace, project, fact


def _ref() -> dict[str, str]:
    return {
        "governed_project_id": "sample",
        "fact_type_key": "spark",
        "object_id": "spark-0001",
    }


def _read(workspace: Path, project: Path) -> dict[str, object]:
    response = handle_request(
        "call",
        "read-fact-objects",
        json.dumps(
            {
                "work_object_locators": [str(project)],
                "arguments": {"workspace_root": str(workspace), "fact_refs": [_ref()]},
            }
        ),
    ).response
    assert response["outcome"] == "ok"
    item = response["result"]["items"][0]
    assert item["check_status"] == "mechanically_valid"
    return item


def _mutable(item: dict[str, object]) -> dict[str, object]:
    fields = dict(item["fact_object"])
    for key in ("object_id", "fact_type_key", "created_at", "updated_at"):
        fields.pop(key)
    return fields


def _update_payload(
    workspace: Path,
    project: Path,
    fingerprint: object,
    fact_object: dict[str, object],
) -> str:
    return json.dumps(
        {
            "work_object_locators": [str(project)],
            "arguments": {
                "workspace_root": str(workspace),
                "fact_ref": _ref(),
                "expected_content_fingerprint": fingerprint,
                "fact_object": fact_object,
            },
        }
    )


def test_update_replaces_full_target_and_preserves_managed_identity(tmp_path: Path) -> None:
    workspace, project, fact = _fixture(tmp_path)
    before = _read(workspace, project)
    before_fields = dict(before["fact_object"])
    target = _mutable(before)
    target["summary"] = "After update"
    fact.chmod(0o640)

    result = handle_request(
        "call",
        "update-fact-object",
        _update_payload(workspace, project, before["content_fingerprint"], target),
    )
    response = result.response

    assert result.exit_code == 0
    assert_common_response(response)
    assert response["outcome"] == "ok"
    assert response["result"]["previous_content_fingerprint"] == before["content_fingerprint"]
    assert response["result"]["content_fingerprint"] != before["content_fingerprint"]
    after_fields = response["result"]["fact_object"]
    assert after_fields["summary"] == "After update"
    assert after_fields["object_id"] == before_fields["object_id"]
    assert after_fields["fact_type_key"] == before_fields["fact_type_key"]
    assert after_fields["created_at"] == before_fields["created_at"]
    assert after_fields["updated_at"] != before_fields["updated_at"]
    assert fact.stat().st_mode & 0o777 == 0o640
    assert response["changes"][0]["status"] == "updated"


def test_no_change_does_not_rewrite_or_change_timestamp(tmp_path: Path) -> None:
    workspace, project, fact = _fixture(tmp_path)
    before = _read(workspace, project)
    raw = fact.read_bytes()
    stat_before = fact.stat()

    response = handle_request(
        "call",
        "update-fact-object",
        _update_payload(workspace, project, before["content_fingerprint"], _mutable(before)),
    ).response

    assert response["outcome"] == "no_change"
    assert response["changes"] == []
    assert response["result"]["previous_content_fingerprint"] == response["result"]["content_fingerprint"]
    assert fact.read_bytes() == raw
    assert fact.stat().st_ino == stat_before.st_ino
    assert response["result"]["fact_object"]["updated_at"] == "2026-07-14T10:00:00+08:00"


def test_stale_fingerprint_rejects_without_writing(tmp_path: Path) -> None:
    workspace, project, fact = _fixture(tmp_path)
    before = _read(workspace, project)
    target = _mutable(before)
    target["summary"] = "Requested update"
    fact.write_text(fact.read_text(encoding="utf-8").replace("Before update", "Manual change"), encoding="utf-8")
    manually_changed = fact.read_bytes()

    response = handle_request(
        "call",
        "update-fact-object",
        _update_payload(workspace, project, before["content_fingerprint"], target),
    ).response

    assert response["outcome"] == "rejected"
    assert "指纹" in response["summary"]
    assert response["changes"] == []
    assert fact.read_bytes() == manually_changed


def test_capability_check_never_mutates_target(tmp_path: Path) -> None:
    workspace, project, fact = _fixture(tmp_path)
    before = _read(workspace, project)
    target = _mutable(before)
    target["summary"] = "Would change on call"
    raw = fact.read_bytes()

    response = handle_request(
        "capabilities",
        "update-fact-object",
        _update_payload(workspace, project, before["content_fingerprint"], target),
    ).response

    assert response["outcome"] == "ok"
    assert response["result"]["operations"][0]["availability"] == "available_for_request"
    assert fact.read_bytes() == raw


def test_failed_write_back_read_rolls_back_only_matching_replacement(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, project, fact = _fixture(tmp_path)
    before = _read(workspace, project)
    original = fact.read_bytes()
    target = _mutable(before)
    target["summary"] = "This replacement will fail its simulated readback"
    actual_current_read = fact_update_operation._current_read
    calls = 0

    def failing_readback(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            return FactReadResult(
                "facts/sparks/spark-0001.yaml",
                "yaml",
                "invalid",
                None,
                None,
                (FactIssue("schema", "simulated write-back failure"),),
            )
        return actual_current_read(*args, **kwargs)

    monkeypatch.setattr(fact_update_operation, "_current_read", failing_readback)
    response = handle_request(
        "call",
        "update-fact-object",
        _update_payload(workspace, project, before["content_fingerprint"], target),
    ).response

    assert response["outcome"] == "error"
    assert response["changes"][0]["status"] == "rolled-back"
    assert fact.read_bytes() == original


def test_concurrent_updates_with_one_fingerprint_have_one_winner(tmp_path: Path) -> None:
    workspace, project, _ = _fixture(tmp_path)
    before = _read(workspace, project)
    targets: list[dict[str, object]] = []
    for summary in ("First contender", "Second contender"):
        target = _mutable(before)
        target["summary"] = summary
        targets.append(target)
    payloads = [_update_payload(workspace, project, before["content_fingerprint"], target) for target in targets]

    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = tuple(
            executor.map(
                lambda payload: handle_request("call", "update-fact-object", payload).response,
                payloads,
            )
        )

    assert sorted(response["outcome"] for response in responses) == ["ok", "rejected"]
    final = _read(workspace, project)
    assert final["fact_object"]["summary"] in {"First contender", "Second contender"}


def test_update_reports_committed_namespace_when_directory_sync_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, project, fact = _fixture(tmp_path)
    before = _read(workspace, project)
    target = _mutable(before)
    target["summary"] = "Committed despite directory sync failure"
    real_fsync = os.fsync
    target_directory = fact.parent

    def fail_directory_sync(descriptor: int) -> None:
        observation = os.fstat(descriptor)
        if stat.S_ISDIR(observation.st_mode) and (observation.st_dev, observation.st_ino) == (
            target_directory.stat().st_dev,
            target_directory.stat().st_ino,
        ):
            raise OSError("directory sync failed")
        real_fsync(descriptor)

    monkeypatch.setattr("ldvh.filesystem.os.fsync", fail_directory_sync)
    response = handle_request(
        "call",
        "update-fact-object",
        _update_payload(workspace, project, before["content_fingerprint"], target),
    ).response

    assert response["outcome"] == "ok"
    assert response["changes"][0]["status"] == "updated"
    assert "durability=unknown" in response["changes"][0]["summary"]
    assert "Committed despite directory sync failure" in fact.read_text(encoding="utf-8")


def test_update_fails_before_lock_or_file_mutation_when_platform_durability_is_not_approved(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, project, fact = _fixture(tmp_path)
    before = _read(workspace, project)
    target = _mutable(before)
    target["summary"] = "Must not be written"
    original = fact.read_bytes()
    monkeypatch.setattr(fact_update_operation, "durable_writes_enabled", lambda: False)

    response = handle_request(
        "call",
        "update-fact-object",
        _update_payload(workspace, project, before["content_fingerprint"], target),
    ).response

    assert response["outcome"] == "unavailable"
    assert "file-only" in response["summary"]
    assert not (project / ".git/ldvh").exists()
    assert fact.read_bytes() == original


def test_independent_process_updates_with_one_fingerprint_have_one_winner(tmp_path: Path) -> None:
    workspace, project, _ = _fixture(tmp_path)
    before = _read(workspace, project)
    payloads: list[str] = []
    for summary in ("First process", "Second process"):
        target = _mutable(before)
        target["summary"] = summary
        payloads.append(_update_payload(workspace, project, before["content_fingerprint"], target))

    def run(payload: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [str(HELPER_EXECUTABLE), "call", "update-fact-object"],
            cwd=project,
            input=payload,
            text=True,
            capture_output=True,
            check=False,
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        completed = tuple(executor.map(run, payloads))

    assert all(item.stderr == "" for item in completed)
    assert sorted(json.loads(item.stdout)["outcome"] for item in completed) == ["ok", "rejected"]
    final = _read(workspace, project)
    assert final["fact_object"]["summary"] in {"First process", "Second process"}


def test_update_rejects_managed_fields_and_terminal_reopen(tmp_path: Path) -> None:
    workspace, project, fact = _fixture(tmp_path)
    before = _read(workspace, project)
    managed = _mutable(before)
    managed["object_id"] = "spark-9999"

    invalid_request = handle_request(
        "call",
        "update-fact-object",
        _update_payload(workspace, project, before["content_fingerprint"], managed),
    ).response
    assert invalid_request["outcome"] == "invalid_request"

    terminal = _mutable(before)
    terminal["status"] = "discarded"
    terminal["disposition_summary"] = "Human chose not to route this Spark"
    terminal["closed_at"] = "2026-07-14T11:00:00+08:00"
    terminal["evidence_refs"] = [{"kind": "repository-path", "locator": "docs/evidence.md"}]
    terminal.pop("priority")
    response = handle_request(
        "call",
        "update-fact-object",
        _update_payload(workspace, project, before["content_fingerprint"], terminal),
    ).response

    assert response["outcome"] == "ok"
    assert response["result"]["fact_object"]["status"] == "discarded"
    terminal_read = _read(workspace, project)
    reopen = _mutable(terminal_read)
    reopen["status"] = "open"
    for key in ("disposition_summary", "closed_at", "evidence_refs"):
        reopen.pop(key)
    reopen["priority"] = "P2"
    rejected = handle_request(
        "call",
        "update-fact-object",
        _update_payload(workspace, project, terminal_read["content_fingerprint"], reopen),
    ).response

    assert rejected["outcome"] == "rejected"
    assert "status 转换" in rejected["gaps"][0]["summary"]
    assert fact.is_file()


def test_study_update_preserves_submitted_body_boundary(tmp_path: Path) -> None:
    workspace, project, _ = _fixture(tmp_path)
    docs = project / "docs"
    docs.mkdir()
    (docs / "question.md").write_text("question\n", encoding="utf-8")
    (docs / "evidence.md").write_text("evidence\n", encoding="utf-8")
    prepare = handle_request(
        "call",
        "prepare-fact-object-draft",
        json.dumps(
            {
                "work_object_locators": [str(project)],
                "arguments": {
                    "workspace_root": str(workspace),
                    "governed_project_id": "sample",
                    "fact_type_key": "study",
                },
            }
        ),
    ).response["result"]
    observed = "2026-07-14T09:00:00+08:00"
    study = {
        "frontmatter": {
            "title": "Study update",
            "status": "active",
            "source_refs": [{"kind": "repository-path", "locator": "docs/question.md", "observed_at": observed}],
            "evidence_refs": [{"kind": "repository-path", "locator": "docs/evidence.md", "observed_at": observed}],
            "applicability": "Current Study update test.",
            "validation_summary": "The local evidence was checked.",
            "research_question": "Does update preserve the submitted Markdown body boundary?",
            "abstract": "The full target body remains stable across serialization.",
        },
        "body": "\n\n".join(
            [
                "## 研究问题\n\n验证 Study 更新。",
                "## 输入、方法与观察边界\n\n读取本地问题和证据。",
                "## 关键发现\n\n完整目标不会积累空行。",
                "## 结论与限制\n\n只覆盖当前载体序列化。",
                "## 建议\n\n保持完整目标语义。",
                "## 后续分流\n\n没有额外分流。",
            ]
        ),
    }
    created = handle_request(
        "call",
        "create-fact-object",
        json.dumps(
            {
                "work_object_locators": [str(project)],
                "arguments": {
                    "workspace_root": str(workspace),
                    "draft_basis": {
                        key: prepare[key]
                        for key in (
                            "governed_project_id",
                            "fact_type_key",
                            "candidate_object_id",
                            "schema_fingerprint",
                            "worktree_fingerprint",
                        )
                    },
                    "fact_object": study,
                },
            }
        ),
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
    target = {
        "frontmatter": dict(read["fact_object"]["frontmatter"]),
        "body": read["fact_object"]["body"].replace("完整目标不会积累空行。", "更新后的正文不会积累空行。"),
    }
    for key in ("object_id", "fact_type_key", "created_at", "updated_at"):
        target["frontmatter"].pop(key)

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
            }
        ),
    ).response

    assert updated["outcome"] == "ok"
    assert updated["result"]["fact_object"]["body"] == target["body"]
