from __future__ import annotations

import json
import subprocess
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from conftest import assert_common_response

from ldvh.facts.contracts import LAYOUTS
from ldvh.facts.creation import serialize_fact_object
from ldvh.helper.operation_runtime import OperationExecution, OperationExecutionContext
from ldvh.helper.operations import IMPLEMENTATIONS, fact_update_prepare_operation
from ldvh.helper.requests import CommonRequest
from ldvh.helper.service import handle_request

pytestmark = pytest.mark.usefixtures("use_current_rule_source_snapshot")

_SPARK_UID = "0198f1c7-8a2b-7c3d-9e4f-123456789abc"
_STUDY_UID = "0198f1c7-8a2b-7c3d-9e4f-123456789abd"
_WORKCASE_UID = "0198f1c7-8a2b-7c3d-9e4f-123456789abe"
_SIGNATURE = {
    "product_name": "pytest",
    "model_name": "test-model",
    "agent_runtime_name": "pytest-runtime",
}


def _git(project: Path, *arguments: str) -> None:
    subprocess.run(["git", "-C", str(project), *arguments], check=True, capture_output=True)


def _fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    workspace = tmp_path / "workspace"
    project = workspace / "project"
    project.mkdir(parents=True)
    _git(project, "init", "-q")
    fact = project / "ldvh-base/sparks/spark-0001.yaml"
    fact.parent.mkdir(parents=True)
    fact.write_text(
        f"""object_uid: {_SPARK_UID}
object_id: spark-0001
fact_type_key: spark
title: Prepare exact update
created_at: 2026-07-14T09:00:00+08:00
updated_at: 2026-07-14T10:00:00+08:00
status: open
summary: Before update
priority: P2
change_log:
  - signature:
      model_id: legacy-model
      agent_workbench: legacy-test
    session_id: legacy-session
    at: 2026-07-14T09:00:00+08:00
    summary: Create test fact
""",
        encoding="utf-8",
    )
    (workspace / "LDVH-GOVERNED-PROJECTS.yaml").write_text(
        "\n".join(
            [
                "governance_instance_name: Test Workspace",
                "product_description: Fact update prepare tests.",
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


def _prepare_payload(workspace: Path, project: Path, uid: str = _SPARK_UID) -> str:
    return json.dumps(
        {
            "work_object_locators": [str(project)],
            "arguments": {
                "workspace_root": str(workspace),
                "fact_ref": {"object_uid": uid},
            },
        }
    )


def _prepare(workspace: Path, project: Path, uid: str = _SPARK_UID) -> dict[str, Any]:
    response = handle_request(
        "call",
        "prepare-fact-object-update",
        _prepare_payload(workspace, project, uid),
    ).response
    assert_common_response(response)
    assert response["outcome"] == "ok"
    return response


def _completed_update_request(prepared: dict[str, Any], *, summary: str) -> dict[str, Any]:
    request = deepcopy(prepared["result"]["request_draft"])
    fact_object = request["arguments"]["fact_object"]
    fact_object["summary"] = summary
    fact_object["change_log"].append(
        {
            "at": "2000-01-01T00:00:00Z",
            "summary": "Apply a real isolated fixture update.",
        }
    )
    request["observed_context"]["signature"] = deepcopy(_SIGNATURE)
    return request


def _synthetic_request(uid: str = _WORKCASE_UID) -> CommonRequest:
    return CommonRequest(
        task=None,
        work_object_locators=(),
        arguments={"fact_ref": {"object_uid": uid}},
        requested_disclosure=None,
        observed_context={},
        authorization_reference=(),
    )


def _synthetic_read(fields: dict[str, Any], *, check_status: str = "mechanically_valid") -> OperationExecution:
    fact_object = deepcopy(fields) if check_status == "mechanically_valid" else None
    return OperationExecution(
        outcome="ok",
        summary="synthetic read",
        result={
            "items": [
                {
                    "resolved_ref": {"object_uid": _WORKCASE_UID},
                    "canonical_path": "ldvh-base/workcases/workcase-0001.yaml",
                    "carrier": "yaml",
                    "check_status": check_status,
                    "fact_object": fact_object,
                    "content_fingerprint": "a" * 64 if fact_object is not None else None,
                    "source_refs": [],
                }
            ]
        },
        requested_scope=({"object_uid": _WORKCASE_UID},),
        completed_scope=({"object_uid": _WORKCASE_UID},),
    )


def test_prepare_operation_is_registered_with_exact_read_inputs() -> None:
    implementation = IMPLEMENTATIONS["prepare-fact-object-update"]

    assert implementation.required_inputs == ("arguments.fact_ref",)
    assert implementation.optional_inputs == ("work_object_locators", "arguments.workspace_root")
    assert implementation.input_examples[0]["arguments_fragment"] == {
        "fact_ref": {"object_uid": "0198f1c7-8a2b-7c3d-9e4f-123456789abc"}
    }

    response = handle_request("capabilities", None, "{}").response
    operation = next(
        item for item in response["result"]["operations"] if item["operation_key"] == "prepare-fact-object-update"
    )
    assert operation["effect"] == "read"
    assert operation["implementation"]["present"] is True


@pytest.mark.parametrize(
    "overlay, expected",
    [
        ({"requested_disclosure": "L1"}, "requested_disclosure"),
        ({"observed_context": {"signature": _SIGNATURE}}, "observed_context"),
        ({"authorization_reference": [{"kind": "human", "locator": "turn:1"}]}, "authorization_reference"),
    ],
)
def test_prepare_rejects_write_context_fields(overlay: dict[str, Any], expected: str) -> None:
    payload: dict[str, Any] = {"arguments": {"fact_ref": {"object_uid": _SPARK_UID}}}
    payload.update(overlay)

    response = handle_request("call", "prepare-fact-object-update", json.dumps(payload)).response

    assert response["outcome"] == "invalid_request"
    assert expected in response["gaps"][0]["summary"]
    assert response["changes"] == []


def test_prepare_spark_returns_exact_incomplete_draft_without_writing(tmp_path: Path) -> None:
    workspace, project, fact = _fixture(tmp_path)
    before = fact.read_bytes()

    response = _prepare(workspace, project)

    result = response["result"]
    assert response["changes"] == []
    assert fact.read_bytes() == before
    assert result["actual_ref"] == {"object_uid": _SPARK_UID}
    assert result["carrier"] == "yaml"
    assert result["fact_type_key"] == "spark"
    assert result["target_operation"] == "update-fact-object"
    assert result["draft_status"] == "caller_completion_required"
    assert result["managed_fields_removed"] == [
        "object_uid",
        "object_id",
        "fact_type_key",
        "created_at",
        "updated_at",
    ]
    request_draft = result["request_draft"]
    assert set(request_draft) == {"arguments", "observed_context"}
    assert request_draft["arguments"]["fact_ref"] == {"object_uid": _SPARK_UID}
    assert request_draft["arguments"]["expected_content_fingerprint"] == result[
        "source_content_fingerprint"
    ]
    fact_object = request_draft["arguments"]["fact_object"]
    assert fact_object["summary"] == "Before update"
    assert len(fact_object["change_log"]) == 1
    assert not set(result["managed_fields_removed"]) & set(fact_object)
    assert request_draft["observed_context"] == {
        "signature": {
            "product_name": None,
            "model_name": None,
            "agent_runtime_name": None,
        }
    }
    requirements = result["completion_requirements"]
    assert set(requirements) == {
        "semantic_change",
        "change_log_append",
        "observed_signature",
        "authorization_reference",
    }
    assert requirements["change_log_append"]["count"] == 1
    assert requirements["authorization_reference"]["required"] == "source_conditioned"


def test_prepare_study_strips_only_frontmatter_and_preserves_body(tmp_path: Path) -> None:
    workspace, project, _ = _fixture(tmp_path)
    fact = project / "ldvh-base/studies/study-0001.md"
    fact.parent.mkdir(parents=True)
    frontmatter = {
        "object_uid": _STUDY_UID,
        "object_id": "study-0001",
        "fact_type_key": "study",
        "title": "Prepared study",
        "status": "active",
        "report_kind": "technical_assessment",
        "created_at": "2026-07-20T09:00:00+08:00",
        "updated_at": "2026-07-20T10:00:00+08:00",
        "research_question": "Does the prepared draft preserve its body?",
        "abstract": "An isolated Markdown preparation fixture.",
        "research_intent": "Verify exact body preservation.",
        "recommendation_summary": "Keep the current body unchanged.",
        "input_refs": [{"kind": "specification", "locator": "specs/05-事实模型基础规范.md"}],
    }
    body = (
        "## 研究问题\n\n是否保持正文。\n\n"
        "## 输入与边界\n\n隔离 fixture。\n\n"
        "## 关键发现\n\n正文必须保持。\n\n"
        "## 建议\n\n不修改正文。\n\n"
        "## 后续分流\n\n无需分流。\n"
    )
    fact.write_text(serialize_fact_object(LAYOUTS["study"], frontmatter, body), encoding="utf-8")
    before = fact.read_bytes()

    response = _prepare(workspace, project, _STUDY_UID)

    result = response["result"]
    draft = result["request_draft"]["arguments"]["fact_object"]
    assert result["carrier"] == "markdown"
    assert set(draft) == {"frontmatter", "body"}
    assert draft["body"] == "\n" + body
    assert not set(result["managed_fields_removed"]) & set(draft["frontmatter"])
    assert draft["frontmatter"]["research_question"] == frontmatter["research_question"]
    assert fact.read_bytes() == before


def test_open_workcase_routes_only_to_full_object_update(monkeypatch: pytest.MonkeyPatch) -> None:
    fields = {
        "object_uid": _WORKCASE_UID,
        "object_id": "workcase-0001",
        "fact_type_key": "workcase",
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
        "title": "Open fixture",
        "status": "open",
        "phase": "executing",
        "change_log": [{"at": "2026-01-01T00:00:00Z", "summary": "Existing"}],
    }
    monkeypatch.setattr(
        fact_update_prepare_operation,
        "FACT_OBJECT_IMPLEMENTATION",
        SimpleNamespace(call=lambda *_args: _synthetic_read(fields)),
    )

    execution = fact_update_prepare_operation._execute(
        _synthetic_request(),
        object(),  # type: ignore[arg-type]
        OperationExecutionContext(Path("/project")),
    )

    assert execution.outcome == "ok"
    assert execution.result is not None
    assert execution.result["target_operation"] == "update-workcase"
    draft = execution.result["request_draft"]
    assert set(draft["arguments"]) == {
        "fact_ref",
        "expected_content_fingerprint",
        "fact_object",
    }
    assert "item_event" not in json.dumps(draft)


@pytest.mark.parametrize("status", ["blocked", "closed"])
def test_non_open_workcase_returns_no_draft(monkeypatch: pytest.MonkeyPatch, status: str) -> None:
    fields = {
        "object_uid": _WORKCASE_UID,
        "object_id": "workcase-0001",
        "fact_type_key": "workcase",
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
        "title": "Ineligible fixture",
        "status": status,
    }
    monkeypatch.setattr(
        fact_update_prepare_operation,
        "FACT_OBJECT_IMPLEMENTATION",
        SimpleNamespace(call=lambda *_args: _synthetic_read(fields)),
    )

    execution = fact_update_prepare_operation._execute(
        _synthetic_request(),
        object(),  # type: ignore[arg-type]
        OperationExecutionContext(Path("/project")),
    )

    assert execution.outcome == "rejected"
    assert execution.result is None
    assert execution.changes == ()


def test_invalid_target_returns_no_draft(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        fact_update_prepare_operation,
        "FACT_OBJECT_IMPLEMENTATION",
        SimpleNamespace(call=lambda *_args: _synthetic_read({}, check_status="invalid")),
    )

    execution = fact_update_prepare_operation._execute(
        _synthetic_request(),
        object(),  # type: ignore[arg-type]
        OperationExecutionContext(Path("/project")),
    )

    assert execution.outcome == "rejected"
    assert execution.result is None
    assert execution.changes == ()


def test_completed_prepare_draft_uses_official_update_route(tmp_path: Path) -> None:
    workspace, project, fact = _fixture(tmp_path)
    prepared = _prepare(workspace, project)
    before = fact.read_bytes()
    request = _completed_update_request(prepared, summary="After prepared update")
    request["work_object_locators"] = [str(project)]
    request["arguments"]["workspace_root"] = str(workspace)

    response = handle_request(
        "call",
        prepared["result"]["target_operation"],
        json.dumps(request),
    ).response

    assert response["outcome"] == "ok"
    assert response["changes"][0]["status"] == "updated"
    assert fact.read_bytes() != before
    assert response["result"]["fact_object"]["summary"] == "After prepared update"
    assert response["result"]["fact_object"]["change_log"][-1]["signature"] == _SIGNATURE


def test_stale_prepared_draft_is_rejected_without_second_write(tmp_path: Path) -> None:
    workspace, project, fact = _fixture(tmp_path)
    prepared = _prepare(workspace, project)
    first = _completed_update_request(prepared, summary="First official update")
    first["work_object_locators"] = [str(project)]
    first["arguments"]["workspace_root"] = str(workspace)
    assert handle_request("call", "update-fact-object", json.dumps(first)).response["outcome"] == "ok"
    after_first = fact.read_bytes()

    stale = _completed_update_request(prepared, summary="Stale second update")
    stale["work_object_locators"] = [str(project)]
    stale["arguments"]["workspace_root"] = str(workspace)
    response = handle_request("call", "update-fact-object", json.dumps(stale)).response

    assert response["outcome"] == "rejected"
    assert response["changes"] == []
    assert fact.read_bytes() == after_first


def test_uncompleted_or_invalid_signature_drafts_never_write(tmp_path: Path) -> None:
    workspace, project, fact = _fixture(tmp_path)
    prepared = _prepare(workspace, project)
    original = fact.read_bytes()

    no_op = deepcopy(prepared["result"]["request_draft"])
    no_op["work_object_locators"] = [str(project)]
    no_op["arguments"]["workspace_root"] = str(workspace)
    no_op["observed_context"]["signature"] = deepcopy(_SIGNATURE)
    no_op_response = handle_request("call", "update-fact-object", json.dumps(no_op)).response
    assert no_op_response["outcome"] in {"rejected", "no_change"}
    assert no_op_response["changes"] == []
    assert fact.read_bytes() == original

    invalid = _completed_update_request(prepared, summary="Must remain unwritten")
    invalid["work_object_locators"] = [str(project)]
    invalid["arguments"]["workspace_root"] = str(workspace)
    invalid["observed_context"]["signature"] = {
        "product_name": None,
        "model_name": None,
        "agent_runtime_name": None,
    }
    invalid_response = handle_request("call", "update-fact-object", json.dumps(invalid)).response
    assert invalid_response["outcome"] == "unavailable"
    assert invalid_response["changes"] == []
    assert fact.read_bytes() == original
