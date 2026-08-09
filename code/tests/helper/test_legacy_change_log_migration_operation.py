"""End-to-end Helper tests for the legacy change-log migration operation."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from conftest import assert_common_response

from ldvh.helper.service import handle_request

pytestmark = pytest.mark.usefixtures("use_current_rule_source_snapshot")


def _git(project: Path, *arguments: str) -> None:
    subprocess.run(["git", "-C", str(project), *arguments], check=True, capture_output=True)


def _fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    workspace = tmp_path / "workspace"
    project = workspace / "project"
    project.mkdir(parents=True)
    _git(project, "init", "-q")
    fact = project / "ldvh-base" / "sparks" / "spark-0001.yaml"
    fact.parent.mkdir(parents=True)
    for directory in ("adrs", "pitfalls", "studies", "workcases"):
        (project / "ldvh-base" / directory).mkdir(parents=True)
    fact.write_text(
        """object_id: spark-0001
fact_type_key: spark
title: Legacy object without change log
created_at: 2026-07-14T09:00:00+08:00
updated_at: 2026-07-14T10:00:00+08:00
status: open
summary: Before migration
priority: P2
""",
        encoding="utf-8",
    )
    (workspace / "LDVH-GOVERNED-PROJECTS.yaml").write_text(
        "\n".join(
            [
                "product_name: Test Workspace",
                "product_description: Legacy change-log migration tests.",
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


def _read_item(workspace: Path, project: Path) -> dict[str, object]:
    response = handle_request(
        "call",
        "read-fact-objects",
        json.dumps(
            {
                "work_object_locators": [str(project)],
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
        ),
    ).response
    assert_common_response(response)
    assert response["outcome"] == "ok"
    item = response["result"]["items"][0]
    assert item["check_status"] == "mechanically_valid"
    return item


def _payload(
    workspace: Path,
    project: Path,
    fingerprint: object,
    *,
    summary: str = "受 Human 当前授权建立遗留对象的可信迁移起点；原始历史不可得。",
) -> str:
    return json.dumps(
        {
            "work_object_locators": [str(project)],
            "authorization_reference": [{"kind": "human_instruction", "locator": "turn:authorize-migration"}],
            "arguments": {
                "workspace_root": str(workspace),
                "fact_ref": {
                    "governed_project_id": "sample",
                    "fact_type_key": "spark",
                    "object_id": "spark-0001",
                },
                "expected_content_fingerprint": fingerprint,
                "migration_signature": {
                    "agent_id": "test-agent",
                    "host_environment": "test",
                    "session_id": "test-session",
                },
                "migration_summary": summary,
            },
        }
    )


def test_migration_seeds_trusted_start_and_preserves_existing_facts(tmp_path: Path) -> None:
    workspace, project, _ = _fixture(tmp_path)
    before = _read_item(workspace, project)
    assert "change_log" not in before["fact_object"]

    response = handle_request(
        "call",
        "migrate-legacy-change-log",
        _payload(workspace, project, before["content_fingerprint"]),
    ).response

    assert_common_response(response)
    assert response["outcome"] == "ok"
    result = response["result"]
    migrated = result["fact_object"]
    assert result["previous_content_fingerprint"] == before["content_fingerprint"]
    assert result["content_fingerprint"] != before["content_fingerprint"]
    assert migrated["status"] == "open"
    assert migrated["priority"] == "P2"
    assert migrated["summary"] == "Before migration"
    assert migrated["created_at"] == before["fact_object"]["created_at"]
    assert result["migration"]["history_recovered"] is False
    change_log = migrated["change_log"]
    assert len(change_log) == 1
    entry = change_log[0]
    assert set(entry["signature"]) == {"agent_id", "host_environment"}
    assert entry["signature"] == {"agent_id": "test-agent", "host_environment": "test"}
    assert entry["session_id"] == "test-session"
    assert entry["at"] == migrated["updated_at"] == result["migration"]["event_at"]
    assert "历史不可得" in entry["summary"]
    assert any(
        item["status"] == "passed" and item["check"] == "事实写入后的独立全库机械完整性审计"
        for item in response["verification"]
    )

    reread = _read_item(workspace, project)
    assert reread["content_fingerprint"] == result["content_fingerprint"]
    assert reread["fact_object"] == migrated


def test_migration_rejects_object_that_already_has_change_log(tmp_path: Path) -> None:
    workspace, project, fact = _fixture(tmp_path)
    before = _read_item(workspace, project)
    migrated = handle_request(
        "call",
        "migrate-legacy-change-log",
        _payload(workspace, project, before["content_fingerprint"]),
    ).response
    assert migrated["outcome"] == "ok"
    original_bytes = fact.read_bytes()

    replay = handle_request(
        "call",
        "migrate-legacy-change-log",
        _payload(workspace, project, migrated["result"]["content_fingerprint"]),
    ).response

    assert_common_response(replay)
    assert replay["outcome"] == "rejected"
    assert "已有 change_log" in replay["summary"]
    assert fact.read_bytes() == original_bytes


def test_migration_rejects_stale_fingerprint_without_writing(tmp_path: Path) -> None:
    workspace, project, fact = _fixture(tmp_path)
    original_bytes = fact.read_bytes()

    response = handle_request(
        "call",
        "migrate-legacy-change-log",
        _payload(workspace, project, "0" * 64),
    ).response

    assert_common_response(response)
    assert response["outcome"] == "rejected"
    assert "指纹已经过期" in response["summary"]
    assert fact.read_bytes() == original_bytes


def test_migration_requires_human_authorization_reference(tmp_path: Path) -> None:
    workspace, project, fact = _fixture(tmp_path)
    before = _read_item(workspace, project)
    original_bytes = fact.read_bytes()
    payload = json.loads(_payload(workspace, project, before["content_fingerprint"]))
    payload["authorization_reference"] = []

    response = handle_request("call", "migrate-legacy-change-log", json.dumps(payload)).response

    assert_common_response(response)
    assert response["outcome"] == "invalid_request"
    assert "authorization_reference" in response["diagnostics"][0]["details"]["problems"][0]
    assert fact.read_bytes() == original_bytes


def test_capabilities_discovers_migration_operation(tmp_path: Path) -> None:
    workspace, project, _ = _fixture(tmp_path)
    response = handle_request("capabilities", None, "{}").response
    assert_common_response(response)
    assert response["outcome"] == "ok"
    operation = next(
        item for item in response["result"]["operations"] if item["operation_key"] == "migrate-legacy-change-log"
    )
    assert operation["effect"] == "may_change_state"
    assert operation["implementation"]["present"] is True
    assert operation["required_inputs"] == [
        "arguments.fact_ref",
        "arguments.expected_content_fingerprint",
        "arguments.migration_signature",
        "arguments.migration_summary",
    ]
