from __future__ import annotations

import json
import os
import stat
import subprocess
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from pathlib import Path

import pytest
from conftest import HELPER_EXECUTABLE, assert_common_response

from ldvh.facts import update_application
from ldvh.facts.creation import CreationBoundary, FactCoordinationUnavailable
from ldvh.facts.models import FactIssue, FactReference
from ldvh.facts.repository import FactReadResult
from ldvh.facts.schema import FactSchema
from ldvh.facts.update_application import FactUpdateResult
from ldvh.filesystem import AtomicWriteResult
from ldvh.governance.resolver import GovernanceResolutionRun
from ldvh.helper.operation_runtime import OperationExecutionContext
from ldvh.helper.operations import fact_update_operation
from ldvh.helper.operations.fact_update_request import FactUpdateRequest
from ldvh.helper.requests import CommonRequest
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
    fact.write_text(
        """object_id: spark-0001
fact_type_key: spark
title: Exact update
created_at: 2026-07-14T09:00:00+08:00
updated_at: 2026-07-14T10:00:00+08:00
status: open
summary: Before update
priority: P2
change_log:
  - signature:
      model_id: test-model
      agent_workbench: test
    session_id: test-session
    at: 2026-07-14T09:00:00+08:00
    summary: Create test fact
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


def _write_routing_target(project: Path, object_id: str) -> Path:
    """Create a mechanically valid fixture target without touching real facts."""

    target = project / "ldvh-base" / "workcases" / f"{object_id}.yaml"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        f"""object_id: {object_id}
fact_type_key: workcase
title: Stable routing target {object_id}
created_at: 2026-07-14T09:00:00+08:00
updated_at: 2026-07-14T10:00:00+08:00
status: closed
goal: Preserve the fully covered Spark responsibility.
scope: Isolated update-operation fixture only.
success_criterion_definitions:
  - criterion_id: criterion-01
    statement: The fixture is available as a stable routing target.
success_criterion_results:
  - criterion_id: criterion-01
    outcome: satisfied
    summary: The fixture target is mechanically valid.
result_summary: The fixture target is available for a complete Spark routing after.
validation_summary: The fixture target is read through the same project relation checks.
closure_outcome: completed
disposition_summary: The bounded fixture responsibility is complete.
change_log:
  - signature:
      model_id: test-model
      agent_workbench: test
    session_id: test-session
    at: 2026-07-14T09:00:00+08:00
    summary: Create routing target fixture.
""",
        encoding="utf-8",
    )
    return target


def _ref() -> dict[str, str]:
    return {
        "governed_project_id": "sample",
        "fact_type_key": "spark",
        "object_id": "spark-0001",
    }


def _domain() -> FactUpdateRequest:
    return FactUpdateRequest(
        workspace_root=Path("/project"),
        governance_scope=(),
        fact_ref=FactReference("sample", "spark", "spark-0001"),
        expected_content_fingerprint="a" * 64,
        fact_object={"status": "open", "summary": "After"},
        authorization_reference=(),
        base=Path("/project"),
    )


def _run() -> GovernanceResolutionRun:
    return GovernanceResolutionRun(None, (), (), (), (), (), ())


def _boundary() -> CreationBoundary:
    return CreationBoundary("sample", Path("/project"), Path("/project/.git"))


def _synthetic_read(
    *,
    summary: str,
    fingerprint: str,
    raw_text: str,
    check_status: str = "mechanically_valid",
) -> FactReadResult:
    fields = (
        {"status": "open", "summary": summary}
        if check_status in {"mechanically_valid", "invalid"} and raw_text
        else None
    )
    return FactReadResult(
        "ldvh-base/sparks/spark-0001.yaml",
        "yaml",
        check_status,
        fields,
        None,
        () if check_status == "mechanically_valid" else (FactIssue("location", "forced residual state"),),
        content_fingerprint=fingerprint or None,
        raw_text=raw_text or None,
    )


def _read(
    workspace: Path,
    project: Path,
    fact_ref: dict[str, str] | None = None,
) -> dict[str, object]:
    item = _read_unchecked(workspace, project, fact_ref)
    assert item["check_status"] == "mechanically_valid"
    return item


def _read_unchecked(
    workspace: Path,
    project: Path,
    fact_ref: dict[str, str] | None = None,
) -> dict[str, object]:
    response = handle_request(
        "call",
        "read-fact-objects",
        json.dumps(
            {
                "work_object_locators": [str(project)],
                "arguments": {"workspace_root": str(workspace), "fact_refs": [fact_ref or _ref()]},
            }
        ),
    ).response
    assert response["outcome"] == "ok"
    item = response["result"]["items"][0]
    return item


def _mutable(item: dict[str, object]) -> dict[str, object]:
    fields = deepcopy(item["fact_object"])
    for key in ("object_uid", "object_id", "fact_type_key", "created_at", "updated_at"):
        fields.pop(key, None)
    return fields


def _append_update_log(fields: dict[str, object]) -> None:
    change_log = fields.get("change_log")
    assert isinstance(change_log, list)
    change_log.append(
        {
            "signature": {
                "product_name": "test",
                "model_name": "test-model",
                "agent_runtime_name": "pytest",
            },
            "at": "2000-01-01T00:00:00Z",
            "summary": "Update test fact",
        }
    )


def _update_payload(
    workspace: Path,
    project: Path,
    fingerprint: object,
    fact_object: dict[str, object],
    fact_ref: dict[str, str] | None = None,
) -> str:
    return json.dumps(
        {
            "work_object_locators": [str(project)],
            "arguments": {
                "workspace_root": str(workspace),
                "fact_ref": fact_ref or _ref(),
                "expected_content_fingerprint": fingerprint,
                "fact_object": fact_object,
            },
            "observed_context": {
                "signature": {
                    "product_name": "test",
                    "model_name": "test-model",
                    "agent_runtime_name": "pytest",
                }
            },
        },
    )


def test_generic_update_rejects_workcase_before_core_or_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, project, _ = _fixture(tmp_path)
    fact = project / "ldvh-base/workcases/workcase-0001.yaml"
    fact.parent.mkdir(parents=True)
    fact.write_bytes(b"current WorkCase bytes\n")
    original = fact.read_bytes()
    reference = {
        "governed_project_id": "sample",
        "fact_type_key": "workcase",
        "object_id": "workcase-0001",
    }

    def unexpected_core_call(*_args, **_kwargs):
        pytest.fail("generic Core update must not receive a WorkCase request")

    monkeypatch.setattr(fact_update_operation, "apply_fact_update", unexpected_core_call)
    response = handle_request(
        "call",
        "update-fact-object",
        _update_payload(workspace, project, "a" * 64, {"title": "Must not be written"}, reference),
    ).response

    assert_common_response(response)
    assert response["outcome"] == "invalid_request"
    problem = response["gaps"][0]["summary"]
    assert "update-fact-object 不接受 WorkCase" in problem
    assert "update-workcase" in problem
    assert "close-workcase" in problem
    assert "correct-closed-workcase" in problem
    assert response["changes"] == []
    assert fact.read_bytes() == original
    assert not (project / ".git/ldvh").exists()


def test_update_replaces_full_target_and_preserves_managed_identity(tmp_path: Path) -> None:
    workspace, project, fact = _fixture(tmp_path)
    before = _read(workspace, project)
    before_fields = dict(before["fact_object"])
    target = _mutable(before)
    target["summary"] = "After update"
    _append_update_log(target)
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
    working_tree_source = next(source for source in response["sources"] if source["kind"] == "working_tree")
    assert working_tree_source["observed_at"] == after_fields["updated_at"]
    assert fact.stat().st_mode & 0o777 == 0o640
    assert response["changes"][0]["status"] == "updated"


def test_uid_object_update_preserves_uid_and_returns_uid_authority(tmp_path: Path) -> None:
    workspace, project, fact = _fixture(tmp_path)
    object_uid = "0198f1c7-8a2b-7c3d-9e4f-123456789abc"
    fact.write_text(
        fact.read_text(encoding="utf-8").replace(
            "object_id: spark-0001\n",
            f"object_id: spark-0001\nobject_uid: {object_uid}\n",
            1,
        ),
        encoding="utf-8",
    )
    before = _read(workspace, project, {"object_uid": object_uid})
    target = _mutable(before)
    target["summary"] = "UID remains authoritative after update"
    _append_update_log(target)

    response = handle_request(
        "call",
        "update-fact-object",
        _update_payload(
            workspace,
            project,
            before["content_fingerprint"],
            target,
            {"object_uid": object_uid},
        ),
    ).response

    assert response["outcome"] == "ok"
    assert response["result"]["actual_ref"] == {"object_uid": object_uid}
    assert response["result"]["fact_object"]["object_uid"] == object_uid
    assert _read(workspace, project, {"object_uid": object_uid})["fact_object"]["object_uid"] == object_uid


def test_uid_object_update_rejects_caller_supplied_uid_without_writing(tmp_path: Path) -> None:
    workspace, project, fact = _fixture(tmp_path)
    object_uid = "0198f1c7-8a2b-7c3d-9e4f-123456789abc"
    fact.write_text(
        fact.read_text(encoding="utf-8").replace(
            "object_id: spark-0001\n",
            f"object_id: spark-0001\nobject_uid: {object_uid}\n",
            1,
        ),
        encoding="utf-8",
    )
    original = fact.read_bytes()
    before = _read(workspace, project, {"object_uid": object_uid})
    target = _mutable(before)
    target["object_uid"] = "0198f1c7-8a2b-7c3d-9e4f-123456789abd"

    response = handle_request(
        "call",
        "update-fact-object",
        _update_payload(
            workspace,
            project,
            before["content_fingerprint"],
            target,
            {"object_uid": object_uid},
        ),
    ).response

    assert response["outcome"] == "invalid_request"
    assert fact.read_bytes() == original


def test_observed_partial_signature_and_session_survive_real_generic_update_schema_validation(
    tmp_path: Path,
) -> None:
    workspace, project, fact = _fixture(tmp_path)
    before = _read(workspace, project)
    target = _mutable(before)
    target["summary"] = "After observed signature update"
    _append_update_log(target)
    payload = json.loads(
        _update_payload(workspace, project, before["content_fingerprint"], target)
    )
    payload["observed_context"] = {
        "signature": {
            "product_name": "test",
            "model_name": None,
            "agent_runtime_name": "pytest",
        }
    }

    response = handle_request(
        "call", "update-fact-object", json.dumps(payload)
    ).response

    assert response["outcome"] == "ok", json.dumps(response, ensure_ascii=False, indent=2)
    newest = response["result"]["fact_object"]["change_log"][-1]
    assert newest["signature"] == {
        "product_name": "test",
        "model_name": None,
        "agent_runtime_name": "pytest",
    }
    assert "session_id" not in newest
    reread = _read(workspace, project)
    assert reread["check_status"] == "mechanically_valid"

    bytes_before_unavailable = fact.read_bytes()
    unavailable_target = _mutable(reread)
    unavailable_target["summary"] = "This update must remain unavailable."
    _append_update_log(unavailable_target)
    unavailable_signatures = (
        {
            "product_name": None,
            "model_name": None,
            "agent_runtime_name": None,
        },
        {"product_name": "test"},
        {
            "product_name": "test",
            "model_name": None,
            "agent_runtime_name": "pytest",
            "unknown": "not-allowed",
        },
    )
    for unavailable_signature in unavailable_signatures:
        unavailable_payload = json.loads(
            _update_payload(
                workspace,
                project,
                reread["content_fingerprint"],
                unavailable_target,
            )
        )
        unavailable_payload["observed_context"] = {"signature": unavailable_signature}
        unavailable = handle_request(
            "call", "update-fact-object", json.dumps(unavailable_payload)
        ).response
        assert unavailable["outcome"] == "unavailable"
        assert unavailable["changes"] == []
        assert fact.read_bytes() == bytes_before_unavailable


def test_update_reports_the_independent_post_write_integrity_audit(tmp_path: Path) -> None:
    workspace, project, _ = _fixture(tmp_path)
    before = _read(workspace, project)
    target = _mutable(before)
    target["summary"] = "After update"
    _append_update_log(target)

    response = handle_request(
        "call",
        "update-fact-object",
        _update_payload(workspace, project, before["content_fingerprint"], target),
    ).response

    audit = next(item for item in response["verification"] if item["check"] == "事实写入后的独立全库机械完整性审计")
    assert audit["status"] == "unavailable"
    assert any(item.get("code") == "post_write_integrity_incomplete" for item in response["gaps"])


def test_generic_helper_preserves_committed_result_when_coordination_release_is_uncertain(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    domain = _domain()
    run = _run()
    boundary = _boundary()
    schema = FactSchema("spark", ())
    before = _synthetic_read(summary="Before", fingerprint="a" * 64, raw_text="before\n")
    after = _synthetic_read(summary="After", fingerprint="b" * 64, raw_text="after\n")
    application = FactUpdateResult(
        "updated",
        "2026-07-26T16:00:00+08:00",
        current=before,
        candidate=after,
        readback=after,
        candidate_text="after\n",
        replacement_result=AtomicWriteResult.committed("replaced"),
        coordination_release_uncertain=True,
    )
    monkeypatch.setattr(fact_update_operation, "_validated_request", lambda *_args: domain)
    monkeypatch.setattr(fact_update_operation, "_governance", lambda *_args: run)
    monkeypatch.setattr(fact_update_operation, "_boundary", lambda *_args: boundary)
    monkeypatch.setattr(fact_update_operation, "project_fact_schemas", lambda *_args: {"spark": schema})
    monkeypatch.setattr(fact_update_operation, "native_atomic_fact_writes_supported", lambda: True)
    monkeypatch.setattr(fact_update_operation, "apply_fact_update", lambda *_args: application)
    event_at = "2026-07-26T16:00:00+08:00"

    execution = fact_update_operation._execute(
        CommonRequest(
            None,
            (),
            {},
            None,
            {
                "signature": {
                    "product_name": "test",
                    "model_name": "test-model",
                    "agent_runtime_name": "pytest",
                }
            },
            (),
            response_profile="diagnostic",
        ),
        object(),
        OperationExecutionContext(Path("/project"), event_at),
    )

    assert execution.outcome == "ok"
    assert execution.completed_scope == execution.requested_scope == (domain.fact_ref.to_json(),)
    assert execution.not_completed_scope == ()
    assert execution.result is not None
    assert execution.result["fact_object"]["summary"] == "After"
    assert execution.changes[0]["status"] == "updated"
    assert execution.verification[0]["status"] == "passed"
    assert execution.gaps[0]["code"] == "controlled_write_lock_release_uncertain"
    assert "原子替换已在 Working Tree 生效并成功回读" in execution.gaps[0]["summary"]
    assert execution.diagnostics[0]["details"]["stage"] == "common_dir_lock_release"
    assert execution.follow_up is not None and execution.follow_up["resume_conditions"]


def test_generic_helper_preserves_candidate_rejection_when_coordination_release_is_uncertain(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    domain = _domain()
    run = _run()
    boundary = _boundary()
    schema = FactSchema("spark", ())
    application = FactUpdateResult(
        "candidate_rejected",
        "2026-07-26T16:00:00+08:00",
        issues=(FactIssue("schema", "forced candidate rejection"),),
        coordination_release_uncertain=True,
    )
    monkeypatch.setattr(fact_update_operation, "_validated_request", lambda *_args: domain)
    monkeypatch.setattr(fact_update_operation, "_governance", lambda *_args: run)
    monkeypatch.setattr(fact_update_operation, "_boundary", lambda *_args: boundary)
    monkeypatch.setattr(fact_update_operation, "project_fact_schemas", lambda *_args: {"spark": schema})
    monkeypatch.setattr(fact_update_operation, "native_atomic_fact_writes_supported", lambda: True)
    monkeypatch.setattr(fact_update_operation, "apply_fact_update", lambda *_args: application)

    execution = fact_update_operation._execute(
        CommonRequest(
            None,
            (),
            {},
            None,
            {
                "signature": {
                    "product_name": "test",
                    "model_name": "test-model",
                    "agent_runtime_name": "pytest",
                }
            },
            (),
            response_profile="diagnostic",
        ),
        object(),
        OperationExecutionContext(Path("/project"), "2026-07-26T16:00:00+08:00"),
    )

    assert execution.outcome == "rejected"
    assert execution.completed_scope == ()
    assert execution.not_completed_scope == execution.requested_scope
    assert execution.changes == ()
    release_gap = next(gap for gap in execution.gaps if "共同锁释放" in gap["summary"])
    assert "status=candidate_rejected" in release_gap["summary"]
    assert "code" not in release_gap
    assert "code" not in execution.diagnostics[0]
    assert execution.follow_up is not None and execution.follow_up["resume_conditions"]


def test_generic_no_change_release_gap_has_observation_but_no_commit_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    domain = _domain()
    run = _run()
    boundary = _boundary()
    schema = FactSchema("spark", ())
    current = _synthetic_read(summary="Before", fingerprint="a" * 64, raw_text="before\n")
    application = FactUpdateResult(
        "no_change",
        "2026-07-26T16:00:00+08:00",
        current=current,
        readback=current,
        coordination_release_uncertain=True,
    )
    monkeypatch.setattr(fact_update_operation, "_validated_request", lambda *_args: domain)
    monkeypatch.setattr(fact_update_operation, "_governance", lambda *_args: run)
    monkeypatch.setattr(fact_update_operation, "_boundary", lambda *_args: boundary)
    monkeypatch.setattr(fact_update_operation, "project_fact_schemas", lambda *_args: {"spark": schema})
    monkeypatch.setattr(fact_update_operation, "native_atomic_fact_writes_supported", lambda: True)
    monkeypatch.setattr(fact_update_operation, "apply_fact_update", lambda *_args: application)
    event_at = "2026-07-26T16:00:00+08:00"

    execution = fact_update_operation._execute(
        CommonRequest(
            None,
            (),
            {},
            None,
            {
                "signature": {
                    "product_name": "test",
                    "model_name": "test-model",
                    "agent_runtime_name": "pytest",
                }
            },
            (),
            response_profile="diagnostic",
        ),
        object(),
        OperationExecutionContext(Path("/project"), event_at),
    )

    assert execution.outcome == "no_change"
    assert execution.changes == ()
    assert "code" not in execution.gaps[0]
    working_tree_source = next(source for source in execution.sources if source["kind"] == "working_tree")
    assert working_tree_source["observed_at"] == event_at


def test_update_rejects_a_parseable_invalid_legacy_spark_snapshot(tmp_path: Path) -> None:
    workspace, project, fact = _fixture(tmp_path)
    fact.write_text(
        """object_id: spark-0001
fact_type_key: spark
title: Exact update
created_at: 2026-07-14T09:00:00+08:00
updated_at: 2026-07-14T10:00:00+08:00
status: routed
summary: Before update
disposition_summary: Incorrectly recorded as routed without a fact target.
change_log:
  - signature:
      agent_id: test-agent
      host_environment: test
    session_id: test-session
    at: 2026-07-14T09:00:00+08:00
    summary: Create test fact.
""",
        encoding="utf-8",
    )
    read = handle_request(
        "call",
        "read-fact-objects",
        json.dumps(
            {
                "work_object_locators": [str(project)],
                "arguments": {
                    "workspace_root": str(workspace),
                    "fact_refs": [_ref()],
                },
            }
        ),
    ).response
    item = read["result"]["items"][0]
    original = fact.read_bytes()

    assert item["check_status"] == "invalid"
    assert item["content_fingerprint"] is not None
    response = handle_request(
        "call",
        "update-fact-object",
        _update_payload(
            workspace,
            project,
            item["content_fingerprint"],
            {
                "title": "Exact update",
                "status": "implemented",
                "summary": "Before update",
                "disposition_summary": (
                    "The bounded Spark content was directly implemented with no residual fact responsibility."
                ),
                "change_log": [
                    {
                        "signature": {"agent_id": "test-agent", "host_environment": "test"},
                        "session_id": "test-session",
                        "at": "2026-07-14T09:00:00+08:00",
                        "summary": "Create test fact.",
                    },
                    {
                        "signature": {"model_id": "test-model", "agent_workbench": "test"},
                        "session_id": "test-session",
                        "at": "2000-01-01T00:00:00Z",
                        "summary": "Repair invalid test fact.",
                    }
                ],
            },
        ),
    ).response

    assert response["outcome"] == "invalid_request"
    assert response["changes"] == []
    assert fact.read_bytes() == original


def test_update_repairs_legacy_retired_pitfall_to_equal_body_discarded_with_exact_cas(tmp_path: Path) -> None:
    workspace, project, _spark = _fixture(tmp_path)
    fact = project / "ldvh-base/pitfalls/pitfall-0001.yaml"
    fact.parent.mkdir(parents=True)
    fact.write_text(
        """object_id: pitfall-0001
fact_type_key: pitfall
title: Legacy complete experience
created_at: 2026-07-14T09:00:00+08:00
updated_at: 2026-07-14T10:00:00+08:00
status: retired
applicability: Only the observed runtime conditions.
validation_summary: The bounded handling was verified; other environments remain unknown.
symptoms: The declared operation did not run.
trigger_conditions: The required runtime input was absent.
root_cause: The runtime could not locate its required input.
resolution: Restore the required input and rerun the operation.
avoidance: Check the required input before relying on the operation.
disposition_summary: The experience no longer applies under the current runtime conditions.
change_log:
  - signature:
      agent_id: test-agent
      host_environment: test
    session_id: test-session
    at: 2026-07-14T09:00:00+08:00
    summary: Create legacy pitfall fixture.
""",
        encoding="utf-8",
    )
    reference = {
        "governed_project_id": "sample",
        "fact_type_key": "pitfall",
        "object_id": "pitfall-0001",
    }
    before = _read_unchecked(workspace, project, reference)
    assert before["check_status"] == "invalid"
    assert before["content_fingerprint"] is not None
    target = _mutable(before)
    target["status"] = "discarded"
    _append_update_log(target)

    rewritten = dict(target)
    rewritten["symptoms"] = "A migration-time rewrite that must be rejected."
    rejected = handle_request(
        "call",
        "update-fact-object",
        _update_payload(workspace, project, before["content_fingerprint"], rewritten, reference),
    ).response
    assert rejected["outcome"] == "rejected"
    assert "status: retired" in fact.read_text(encoding="utf-8")

    response = handle_request(
        "call",
        "update-fact-object",
        _update_payload(workspace, project, before["content_fingerprint"], target, reference),
    ).response

    assert response["outcome"] == "ok", json.dumps(response, ensure_ascii=False, indent=2)
    after = response["result"]["fact_object"]
    assert after["status"] == "discarded"
    for field in (
        "title",
        "applicability",
        "validation_summary",
        "symptoms",
        "trigger_conditions",
        "root_cause",
        "resolution",
        "avoidance",
        "disposition_summary",
    ):
        assert after[field] == before["fact_object"][field]


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

    assert response["outcome"] == "rejected"
    assert response["changes"] == []
    assert fact.read_bytes() == raw
    assert fact.stat().st_ino == stat_before.st_ino


def test_spark_routed_after_is_rejected_without_writing_targets(tmp_path: Path) -> None:
    workspace, project, fact = _fixture(tmp_path)
    routing_targets = {
        "workcase-0001": _write_routing_target(project, "workcase-0001"),
        "workcase-0002": _write_routing_target(project, "workcase-0002"),
    }
    target_bytes = {object_id: path.read_bytes() for object_id, path in routing_targets.items()}
    before = _read(workspace, project)
    original = fact.read_bytes()
    target = _mutable(before)
    target.update(
        {
            "status": "routed",
            "disposition_summary": (
                "The entire isolated fixture Spark is covered by the stable WorkCase target; "
                "the target lifecycle is not tracked by this routed Spark."
            ),
            "relations": [
                {
                    "relation_key": "routed-to",
                    "target": {
                        "governed_project_id": "sample",
                        "fact_type_key": "workcase",
                        "object_id": "workcase-0001",
                    },
                },
                {
                    "relation_key": "routed-to",
                    "target": {
                        "governed_project_id": "sample",
                        "fact_type_key": "workcase",
                        "object_id": "workcase-0002",
                    },
                },
            ],
        }
    )
    target.pop("priority")
    _append_update_log(target)

    stale = handle_request(
        "call",
        "update-fact-object",
        _update_payload(workspace, project, "0" * 64, target),
    ).response

    assert stale["outcome"] == "rejected"
    assert stale["changes"] == []
    assert fact.read_bytes() == original

    routed = handle_request(
        "call",
        "update-fact-object",
        _update_payload(workspace, project, before["content_fingerprint"], target),
    ).response

    assert routed["outcome"] == "rejected"
    assert routed["changes"] == []
    assert fact.read_bytes() == original
    assert {object_id: path.read_bytes() for object_id, path in routing_targets.items()} == target_bytes


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
    _append_update_log(target)
    actual_project_read = update_application._project_read
    calls = 0

    def failing_readback(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            return FactReadResult(
                "ldvh-base/sparks/spark-0001.yaml",
                "yaml",
                "invalid",
                None,
                None,
                (FactIssue("schema", "simulated write-back failure"),),
            )
        return actual_project_read(*args, **kwargs)

    monkeypatch.setattr(update_application, "_project_read", failing_readback)
    response = handle_request(
        "call",
        "update-fact-object",
        _update_payload(workspace, project, before["content_fingerprint"], target),
    ).response

    assert response["outcome"] == "error"
    assert response["changes"][0]["status"] == "rolled-back"
    assert fact.read_bytes() == original


@pytest.mark.parametrize(
    ("residual_kind", "rollback", "expected", "verification_status", "excluded"),
    [
        (
            "candidate",
            AtomicWriteResult.uncertain(),
            "当前重新读取观察到的实际事实对象载体完整字节内容与本次新载体一致",
            "passed",
            "发生冲突",
        ),
        (
            "before",
            AtomicWriteResult.not_committed("conflict"),
            "当前重新读取观察到的实际事实对象载体完整字节内容与更新前载体一致",
            "passed",
            "生效情况无法确认",
        ),
        (
            "external",
            AtomicWriteResult.uncertain(),
            "当前重新读取观察到的实际事实对象载体是另一机械有效版本",
            "passed",
            "发生冲突",
        ),
        (
            "invalid-read",
            AtomicWriteResult.not_committed("conflict"),
            "当前实际事实对象载体已安全完整读取，但对象未通过机械检查",
            "failed",
            "残留状态无法确认",
        ),
        (
            "invalid-unread",
            AtomicWriteResult.not_committed("conflict"),
            "当前实际事实对象载体未能安全完整读取，机械检查未通过（状态为 `invalid`）",
            "failed",
            "已安全完整读取",
        ),
        (
            "not-found",
            AtomicWriteResult.not_committed("conflict"),
            "当前重新读取确认实际事实对象载体的预期位置不存在",
            "failed",
            "已安全完整读取",
        ),
        (
            "unavailable",
            AtomicWriteResult.uncertain(),
            "实际事实对象载体的残留状态无法确认",
            "unavailable",
            "本次新载体一致",
        ),
    ],
)
def test_generic_helper_reports_fresh_residual_without_exceeding_rollback_evidence(
    residual_kind: str,
    rollback: AtomicWriteResult,
    expected: str,
    verification_status: str,
    excluded: str,
) -> None:
    before = _synthetic_read(summary="Before", fingerprint="a" * 64, raw_text="before\n")
    candidate = _synthetic_read(summary="Candidate", fingerprint="b" * 64, raw_text="candidate\n")
    residuals = {
        "candidate": candidate,
        "before": before,
        "external": _synthetic_read(summary="External", fingerprint="c" * 64, raw_text="external\n"),
        "invalid-read": _synthetic_read(
            summary="Invalid",
            fingerprint="c" * 64,
            raw_text="invalid\n",
            check_status="invalid",
        ),
        "invalid-unread": _synthetic_read(
            summary="",
            fingerprint="",
            raw_text="",
            check_status="invalid",
        ),
        "not-found": _synthetic_read(
            summary="",
            fingerprint="",
            raw_text="",
            check_status="not_found",
        ),
        "unavailable": _synthetic_read(
            summary="",
            fingerprint="",
            raw_text="",
            check_status="unavailable",
        ),
    }
    application = FactUpdateResult(
        "readback_failed",
        "2026-07-26T16:00:00+08:00",
        issues=(FactIssue("reference", "forced readback failure"),),
        current=before,
        candidate=candidate,
        readback=candidate,
        candidate_text="candidate\n",
        replacement_result=AtomicWriteResult.committed("replaced"),
        rollback_result=rollback,
        residual_readback=residuals[residual_kind],
    )
    domain = _domain()

    execution = fact_update_operation._application_failure(
        application,
        domain,
        _run(),
        (domain.fact_ref.to_json(),),
        (),
        _boundary(),
        "2026-07-26T16:00:00+08:00",
    )

    assert execution is not None
    assert execution.outcome == "error"
    assert execution.result is None
    assert execution.completed_scope == ()
    assert execution.not_completed_scope == (domain.fact_ref.to_json(),)
    assert expected in execution.changes[0]["summary"]
    assert excluded not in execution.changes[0]["summary"]
    assert execution.verification[0]["status"] == verification_status
    observation = next(source for source in execution.sources if source["kind"] == "working_tree")
    assert observation["details"]["check_status"] == residuals[residual_kind].check_status


def test_concurrent_updates_with_one_fingerprint_have_one_winner(tmp_path: Path) -> None:
    workspace, project, _ = _fixture(tmp_path)
    before = _read(workspace, project)
    targets: list[dict[str, object]] = []
    for summary in ("First contender", "Second contender"):
        target = _mutable(before)
        target["summary"] = summary
        _append_update_log(target)
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
    _append_update_log(target)
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
    monkeypatch.setattr(fact_update_operation, "native_atomic_fact_writes_supported", lambda: False)

    response = handle_request(
        "call",
        "update-fact-object",
        _update_payload(workspace, project, before["content_fingerprint"], target),
    ).response

    assert response["outcome"] == "unavailable"
    assert "原生原子后端" in response["summary"]
    assert not (project / ".git/ldvh").exists()
    assert fact.read_bytes() == original


def test_coordination_permission_failure_is_structured_unavailable_with_zero_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, project, fact = _fixture(tmp_path)
    before = _read(workspace, project)
    target = _mutable(before)
    target["summary"] = "Must remain unwritten"
    original = fact.read_bytes()

    def unavailable(*args, **kwargs):
        raise FactCoordinationUnavailable("permission_denied")

    monkeypatch.setattr(fact_update_operation, "apply_fact_update", unavailable)
    response = handle_request(
        "call",
        "update-fact-object",
        json.dumps(
            {
                "response_profile": "diagnostic",
                "work_object_locators": [str(project)],
                "arguments": {
                    "workspace_root": str(workspace),
                    "fact_ref": _ref(),
                    "expected_content_fingerprint": before["content_fingerprint"],
                    "fact_object": target,
                },
                "observed_context": {
                        "signature": {
                            "product_name": "test",
                            "model_name": "test-model",
                            "agent_runtime_name": "pytest",
                        }
                },
            }
        ),
    ).response

    assert response["outcome"] == "unavailable"
    assert response["changes"] == []
    assert response["gaps"][0]["code"] == "controlled_write_lock_unavailable"
    assert response["diagnostics"][0]["code"] == "controlled_write_lock_unavailable"
    assert response["diagnostics"][0]["details"] == {
        "stage": "common_dir_lock",
        "path_role": "git_common_dir_ldvh_coordination_root",
        "required_access": "create_or_open_and_exclusively_lock",
        "system_error_category": "permission_denied",
        "target_unchanged": True,
        "counter_unchanged": True,
    }
    assert fact.read_bytes() == original


def test_independent_process_updates_with_one_fingerprint_have_one_winner(tmp_path: Path) -> None:
    workspace, project, _ = _fixture(tmp_path)
    before = _read(workspace, project)
    payloads: list[str] = []
    for summary in ("First process", "Second process"):
        target = _mutable(before)
        target["summary"] = summary
        _append_update_log(target)
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
    _append_update_log(terminal)
    terminal["disposition_summary"] = "Human chose to stop tracking this Spark"
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
    for key in ("disposition_summary",):
        reopen.pop(key)
    reopen["priority"] = "P2"
    _append_update_log(reopen)
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
    study = {
        "frontmatter": {
            "title": "Study update",
            "status": "active",
            "change_log": [
                {
                    "signature": {
                        "product_name": "test",
                        "model_name": "test-model",
                        "agent_runtime_name": "pytest",
                    },
                    "at": "2000-01-01T00:00:00Z",
                    "summary": "Create Study test fact.",
                }
            ],
            "report_kind": "external_research",
            "urls": [
                {
                    "ref": "https://example.invalid/study-update",
                    "title": "Study update evidence",
                    "summary": "External material used by the test Study.",
                }
            ],
            "research_question": "Does update preserve the submitted Markdown body boundary?",
            "abstract": "The full target body remains stable across serialization.",
            "research_intent": (
                "Confirm that a controlled update retains the project reason for this external research."
            ),
            "recommendation_summary": "Use the complete target boundary when updating a Study report.",
        },
        "body": """
## 研究问题

### 项目问题

验证 Study 更新。

### 外部问题

外部资料如何限定完整目标更新？

## 输入与边界

### 已读外部资料

读取外部研究资料并限定当前问题。

### 本次边界

不把序列化行为当作研究结论。

## 关键发现

### 完整目标

完整目标不会积累空行，启发是保持一次完整替换；不等于任意内容均可更新。

### 载体边界

提交正文会被保留，启发是避免隐式改写；不证明外部资料当前。

## 建议

### 可立即采用的工作方式

保持完整目标语义。

## 后续分流

| 分流类别 | 触发条件 | 下一步或不创建理由 |
|---|---|---|
| 无需对象化 | 仅验证更新路径 | 不创建额外对象。 |
""",
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
                            "schema_fingerprint",
                            "worktree_fingerprint",
                        )
                    },
                    "fact_object": study,
                },
                "observed_context": {
                    "signature": {
                        "product_name": "test",
                        "model_name": "test-model",
                        "agent_runtime_name": "pytest",
                    }
                },
            }
        ),
    ).response
    assert created["outcome"] == "ok", json.dumps(created, ensure_ascii=False, indent=2)
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
        "body": read["fact_object"]["body"].replace(
            "完整目标不会积累空行，启发是保持一次完整替换；不等于任意内容均可更新。",
            "更新后的正文不会积累空行，启发是保持一次完整替换；不等于任意内容均可更新。",
        ),
    }
    for key in ("object_uid", "object_id", "fact_type_key", "created_at", "updated_at"):
        target["frontmatter"].pop(key)
    target["frontmatter"]["change_log"].append(
        {
            "signature": {
                "product_name": "test",
                "model_name": "test-model",
                "agent_runtime_name": "pytest",
            },
            "at": "2000-01-01T00:00:00Z",
            "summary": "Update Study test fact.",
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
                            "product_name": "test",
                            "model_name": "test-model",
                            "agent_runtime_name": "pytest",
                        }
                    },
            }
        ),
    ).response

    assert updated["outcome"] == "ok", json.dumps(updated, ensure_ascii=False, indent=2)
    assert updated["result"]["fact_object"]["body"] == target["body"]


def _legacy_fixture(tmp_path: Path, *, include_log: bool = False) -> tuple[Path, Path, Path]:
    """Create a Spark fixture whose committed baseline lacks ``change_log``.

    ``include_log`` commits a logged object and then rewrites the Working Tree
    without the log, simulating a deleted committed history.
    """
    workspace = tmp_path / "workspace"
    project = workspace / "project"
    project.mkdir(parents=True)
    _git(project, "init", "-q")
    fact = project / "ldvh-base" / "sparks" / "spark-0001.yaml"
    fact.parent.mkdir(parents=True)
    clean = (
        "object_id: spark-0001\n"
        "fact_type_key: spark\n"
        "title: Legacy object\n"
        "created_at: 2026-07-14T09:00:00+08:00\n"
        "updated_at: 2026-07-14T10:00:00+08:00\n"
        "status: open\n"
        "summary: Before first real update\n"
        "priority: P2\n"
    )
    logged = clean + (
        "change_log:\n"
        "  - signature:\n"
        "      agent_id: test-agent\n"
        "      host_environment: test\n"
        "    session_id: test-session\n"
        "    at: 2026-07-14T09:00:00+08:00\n"
        "    summary: Create test fact\n"
    )
    fact.write_text(logged if include_log else clean, encoding="utf-8")
    (workspace / "LDVH-GOVERNED-PROJECTS.yaml").write_text(
        "\n".join(
            [
                "product_name: Test Workspace",
                "product_description: First-log update tests.",
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
    _git(project, "add", "-A")
    _git(
        project,
        "-c",
        "user.name=test",
        "-c",
        "user.email=test@example.com",
        "commit",
        "-q",
        "-m",
        "seed",
    )
    if include_log:
        fact.write_text(clean, encoding="utf-8")
    return workspace, project, fact


def test_first_log_generic_update_succeeds_when_head_lacks_log(tmp_path: Path) -> None:
    workspace, project, fact = _legacy_fixture(tmp_path)
    before = _read(workspace, project)
    assert "change_log" not in before["fact_object"]
    target = _mutable(before)
    target["summary"] = "First real update"
    target["change_log"] = [
        {
            "signature": {
                "product_name": "placeholder",
                "model_name": "placeholder",
                "agent_runtime_name": "placeholder",
            },
            "at": "2000-01-01T00:00:00Z",
            "summary": "首次真实更新建立流水；此前历史未恢复。",
        }
    ]

    response = handle_request(
        "call",
        "update-fact-object",
        _update_payload(workspace, project, before["content_fingerprint"], target),
    ).response

    assert_common_response(response)
    assert response["outcome"] == "ok"
    after_fields = response["result"]["fact_object"]
    assert after_fields["summary"] == "First real update"
    assert after_fields["status"] == "open"
    change_log = after_fields["change_log"]
    assert len(change_log) == 1
    entry = change_log[0]
    assert set(entry["signature"]) == {"product_name", "model_name", "agent_runtime_name"}
    assert entry["signature"]["model_name"] == "test-model"
    assert "session_id" not in entry
    assert entry["at"] == after_fields["updated_at"]
    assert any(
        item["check"] == "事实写入后的独立全库机械完整性审计" for item in response["verification"]
    )
    assert fact.read_text(encoding="utf-8") != before["fact_object"]


def test_first_log_generic_update_rejects_deleted_committed_history(tmp_path: Path) -> None:
    workspace, project, fact = _legacy_fixture(tmp_path, include_log=True)
    before = _read(workspace, project)
    assert "change_log" not in before["fact_object"]
    original = fact.read_bytes()
    target = _mutable(before)
    target["summary"] = "First real update"
    target["change_log"] = [
        {
            "signature": {
                "product_name": "test",
                "model_name": "test-model",
                "agent_runtime_name": "pytest",
            },
            "at": "2000-01-01T00:00:00Z",
            "summary": "首次真实更新建立流水；此前历史未恢复。",
        }
    ]

    response = handle_request(
        "call",
        "update-fact-object",
        _update_payload(workspace, project, before["content_fingerprint"], target),
    ).response

    assert_common_response(response)
    assert response["outcome"] == "rejected"
    assert any("HEAD" in gap["summary"] for gap in response["gaps"])
    assert fact.read_bytes() == original
