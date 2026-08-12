from __future__ import annotations

from pathlib import Path

import pytest

from ldvh.facts.models import FactIssue
from ldvh.facts.repository import FactReadResult
from ldvh.facts.schema import FactSchema
from ldvh.governance.resolver import GovernanceResolutionRun
from ldvh.helper.operation_runtime import OperationExecutionContext
from ldvh.helper.operations import IMPLEMENTATIONS
from ldvh.helper.operations import check_workcase_handoff_operation as operation
from ldvh.helper.requests import CommonRequest

FINGERPRINT = "a" * 64


def _request(*, governed_project_id: str = "sample") -> CommonRequest:
    return CommonRequest(
        task=None,
        work_object_locators=(),
        arguments={
            "fact_ref": {
                "governed_project_id": governed_project_id,
                "fact_type_key": "workcase",
                "object_id": "workcase-0047",
            }
        },
        requested_disclosure=None,
        observed_context={},
        authorization_reference=(),
    )


def _run() -> GovernanceResolutionRun:
    return GovernanceResolutionRun(None, (), (), (), (), (), ())


def _install_read(
    monkeypatch: pytest.MonkeyPatch,
    fields: dict[str, object],
    *,
    status: str = "mechanically_valid",
    governed_project_id: str = "sample",
):
    calls: list[str] = []

    def fake_read(root, layout, schema, object_id, *, expected_common_dir):
        del root, layout, schema, expected_common_dir
        calls.append(object_id)
        return FactReadResult(
            "ldvh-base/workcases/workcase-0047.yaml",
            "yaml",
            status,
            fields,
            None,
            () if status == "mechanically_valid" else (FactIssue("schema", "invalid source"),),
            content_fingerprint=FINGERPRINT,
            raw_text="source\n",
        )

    def fake_governance(domain):
        return GovernanceResolutionRun(None, (), (), (), (), (), ())

    monkeypatch.setattr(operation, "_governance", fake_governance)
    monkeypatch.setattr(
        operation,
        "reading_boundary",
        lambda run: (governed_project_id, Path("/project"), Path("/git")),
    )
    monkeypatch.setattr(
        operation,
        "project_fact_schemas",
        lambda repository: {"workcase": FactSchema("workcase", ())},
    )
    monkeypatch.setattr(operation, "read_fact_object", fake_read)
    return calls


def test_operation_is_registered_as_read_only_with_exact_fact_ref() -> None:
    implementation = IMPLEMENTATIONS["check-workcase-handoff"]

    assert implementation.required_inputs == ("arguments.fact_ref",)
    assert implementation.optional_inputs == ("work_object_locators", "arguments.workspace_root")


def test_operation_returns_handoff_verdict_for_controller_owned_phase(monkeypatch) -> None:
    calls = _install_read(monkeypatch, {"status": "open", "phase": "executing"})

    execution = operation._call(_request(), object(), OperationExecutionContext(Path("/project")))  # type: ignore[arg-type]

    assert execution.outcome == "ok"
    assert calls == ["workcase-0047"]
    assert execution.changes == ()
    assert execution.result is not None
    assert execution.result["actual_ref"]["fact_type_key"] == "workcase"
    assert execution.result["source_content_fingerprint"] == FINGERPRINT
    projection = execution.result["current_snapshot_projection"]
    assert projection["contract_identity"] == "workcase-current-snapshot-presentation/2"
    assert projection["resolution"] == "resolved"
    assert projection["handoff_allowed"] is False
    assert projection["handoff_reason"] == "controller_owned"
    assert execution.result["handoff_allowed"] is False
    assert execution.result["handoff_reason"] == "controller_owned"
    assert execution.result["next_required_control_step"] == "advance_current_work_item"


@pytest.mark.parametrize(
    ("fields", "allowed", "reason", "next_step"),
    [
        ({"status": "open", "phase": "human_plan_confirming"}, True, "gate1_waiting", "human_gate_1"),
        ({"status": "open", "phase": "human_closure_confirming"}, True, "gate2_waiting", "human_gate_2"),
        ({"status": "closed"}, True, "closed", "none"),
        ({"status": "blocked", "phase": "executing"}, True, "blocked_at_current_position", "advance_current_work_item"),
        ({"status": "open", "phase": "independent_reviewing"}, False, "controller_owned", "complete_independent_result_review"),
    ],
)
def test_operation_returns_the_exit_set_verdict(
    monkeypatch,
    fields,
    allowed,
    reason,
    next_step,
) -> None:
    _install_read(monkeypatch, fields)

    execution = operation._call(_request(), object(), OperationExecutionContext(Path("/project")))  # type: ignore[arg-type]

    assert execution.outcome == "ok"
    assert execution.result is not None
    assert execution.result["handoff_allowed"] is allowed
    assert execution.result["handoff_reason"] == reason
    assert execution.result["next_required_control_step"] == next_step


def test_operation_rejects_invalid_source_without_changes(monkeypatch) -> None:
    calls = _install_read(monkeypatch, {"status": "open", "phase": "executing"}, status="invalid")

    execution = operation._call(_request(), object(), OperationExecutionContext(Path("/project")))  # type: ignore[arg-type]

    assert execution.outcome == "rejected"
    assert execution.result is None
    assert execution.changes == ()
    assert calls == ["workcase-0047"]


def test_operation_rejects_governance_mismatch_without_changes(monkeypatch) -> None:
    calls = _install_read(
        monkeypatch,
        {"status": "open", "phase": "executing"},
        governed_project_id="other",
    )

    execution = operation._call(_request(), object(), OperationExecutionContext(Path("/project")))  # type: ignore[arg-type]

    assert execution.outcome == "rejected"
    assert execution.result is None
    assert calls == []


def test_operation_is_unavailable_when_read_is_unavailable(monkeypatch) -> None:
    _install_read(monkeypatch, {"status": "open", "phase": "executing"}, status="unavailable")

    execution = operation._call(_request(), object(), OperationExecutionContext(Path("/project")))  # type: ignore[arg-type]

    assert execution.outcome == "unavailable"
    assert execution.result is None
    assert execution.changes == ()
