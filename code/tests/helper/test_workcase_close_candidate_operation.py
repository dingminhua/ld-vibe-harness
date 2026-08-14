from __future__ import annotations

from pathlib import Path

import pytest

from ldvh.facts.creation import CreationBoundary
from ldvh.facts.models import FactIssue, FactReference
from ldvh.facts.repository import FactReadResult
from ldvh.facts.schema import FactSchema
from ldvh.governance.resolver import GovernanceResolutionRun
from ldvh.helper.operation_runtime import OperationExecutionContext
from ldvh.helper.operations import IMPLEMENTATIONS
from ldvh.helper.operations import workcase_close_candidate_operation as operation
from ldvh.helper.operations.fact_reference_support import ResolvedFactReference
from ldvh.helper.requests import CommonRequest


def _request() -> CommonRequest:
    return CommonRequest(
        task=None,
        work_object_locators=(),
        arguments={
            "fact_ref": {
                "governed_project_id": "sample",
                "fact_type_key": "workcase",
                "object_id": "workcase-0047",
            }
        },
        requested_disclosure=None,
        observed_context={},
        authorization_reference=(),
    )


def _fields(*, phase: str = "human_closure_confirming", status: str = "open") -> dict[str, object]:
    route_target_uid = "019ffd48-d7b1-7bd4-abf2-3759fa544ba2"
    return {
        "status": status,
        "phase": phase,
        "title": "形成关闭候选",
        "goal": "只投影当前 source。",
        "scope": "不读取 target。",
        "success_criterion_definitions": [{"criterion_id": "criterion-a", "statement": "完成映射。"}],
        "success_criterion_results": [
            {"criterion_id": "criterion-a", "outcome": "not_satisfied", "summary": "仍需转交。"}
        ],
        "result_summary": "已形成局部结果。",
        "validation_summary": "只验证当前 source。",
        "urls": [{"ref": "https://example.com/source", "title": "Source", "summary": "保留。"}],
        "change_log": [
            {
                "signature": {"agent_id": "test-agent", "host_environment": "unit"},
                "session_id": "unit-session",
                "at": "2026-07-26T09:00:00+08:00",
                "summary": "形成候选前已记录。",
            }
        ],
        "closure_proposal": {
            "proposed_outcome": "partial",
            "proposed_disposition_summary": "转交剩余责任。",
            "residual_decisions": [
                {
                    "residual_id": "residual-route",
                    "summary": "后续责任。",
                    "proposed_disposition": "route_existing",
                    "route_target": {
                        "object_uid": route_target_uid,
                        "content_fingerprint": "b" * 64,
                    },
                }
            ],
        },
        "relations": [
            {
                "relation_key": "related-to",
                "target": {"object_uid": "019ffd48-d7b1-7c82-8825-93eafde2fef7"},
            }
        ],
    }


def _run() -> GovernanceResolutionRun:
    return GovernanceResolutionRun(None, (), (), (), (), (), ())


def _install_read(monkeypatch: pytest.MonkeyPatch, fields: dict[str, object], *, status: str = "mechanically_valid"):
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
            content_fingerprint="a" * 64,
            raw_text="source\n",
        )

    monkeypatch.setattr(operation, "_governance", lambda domain: _run())
    monkeypatch.setattr(operation, "reading_boundary", lambda run: ("sample", Path("/project"), Path("/git")))
    monkeypatch.setattr(operation, "project_fact_schemas", lambda repository: {"workcase": FactSchema("workcase", ())})
    monkeypatch.setattr(operation, "read_fact_object", fake_read)
    return calls


def test_candidate_operation_resolves_uid_reference_before_projection(monkeypatch) -> None:
    calls = _install_read(monkeypatch, _fields())
    uid = "0198f1c7-8a2b-7c3d-9e4f-123456789abc"
    monkeypatch.setattr(
        operation,
        "resolve_stable_fact_reference",
        lambda run, reference, schemas: (
            ResolvedFactReference(
                FactReference("sample", "workcase", "workcase-0047"),
                CreationBoundary("sample", Path("/project"), Path("/git")),
            ),
            "resolved",
        ),
    )
    request = _request()
    request.arguments["fact_ref"] = {"object_uid": uid}

    execution = operation._call(request, object(), OperationExecutionContext(Path("/project")))  # type: ignore[arg-type]

    assert execution.outcome == "ok"
    assert calls == ["workcase-0047"]
    assert execution.result is not None
    assert execution.result["actual_ref"] == {"object_uid": uid}


def test_candidate_operation_is_registered_as_one_read_only_input_shape() -> None:
    implementation = IMPLEMENTATIONS["prepare-closed-workcase-candidate"]

    assert implementation.required_inputs == ("arguments.fact_ref",)
    assert implementation.optional_inputs == ("work_object_locators", "arguments.workspace_root")


def test_candidate_operation_returns_complete_nonmanaged_projection_without_reading_target(monkeypatch) -> None:
    calls = _install_read(monkeypatch, _fields())

    execution = operation._call(_request(), object(), OperationExecutionContext(Path("/project")))  # type: ignore[arg-type]

    assert execution.outcome == "ok"
    assert calls == ["workcase-0047"]
    assert execution.changes == ()
    assert execution.result is not None
    assert execution.result["source_content_fingerprint"] == "a" * 64
    candidate = execution.result["fact_object"]
    assert set(candidate).isdisjoint({"object_id", "fact_type_key", "created_at", "updated_at", "phase"})
    assert "change_log" not in candidate
    assert candidate["status"] == "closed"
    assert candidate["urls"] == _fields()["urls"]
    assert candidate["relations"] == [
        _fields()["relations"][0],  # type: ignore[index]
        {
            "relation_key": "routed-to",
            "target": {"object_uid": "019ffd48-d7b1-7bd4-abf2-3759fa544ba2"},
        },
    ]
    assert execution.result["change_log_append"] == {
        "required": True,
        "target": "fact_object.change_log",
        "count": 1,
        "signature": {
            "fields": ["product_name", "model_name", "agent_runtime_name"],
            "source": "close-workcase 调用请求中的 observed_context.signature",
            "provider": "caller",
            "forbidden_fields": ["signer_type"],
        },
    }
    assert execution.result["mapping_basis"] == {
        "proposal_route_targets": [
            {
                "target": {"object_uid": "019ffd48-d7b1-7bd4-abf2-3759fa544ba2"},
                "content_fingerprint": "b" * 64,
            }
        ]
    }
    assert "close-workcase 前" in execution.summary


def test_candidate_operation_prefers_route_over_related_to_for_the_same_target(monkeypatch) -> None:
    fields = _fields()
    fields["relations"] = [
        {
            "relation_key": "related-to",
            "target": {"object_uid": "019ffd48-d7b1-7bd4-abf2-3759fa544ba2"},
        }
    ]
    _install_read(monkeypatch, fields)

    execution = operation._call(_request(), object(), OperationExecutionContext(Path("/project")))  # type: ignore[arg-type]

    assert execution.outcome == "ok"
    assert execution.result is not None
    assert execution.result["fact_object"]["relations"] == [
        {
            "relation_key": "routed-to",
            "target": {"object_uid": "019ffd48-d7b1-7bd4-abf2-3759fa544ba2"},
        }
    ]


def test_candidate_operation_rejects_conflicting_route_target_fingerprints_without_changes(monkeypatch) -> None:
    fields = _fields()
    proposal = fields["closure_proposal"]
    assert isinstance(proposal, dict)
    decisions = proposal["residual_decisions"]
    assert isinstance(decisions, list)
    conflicting = dict(decisions[0])
    conflicting["residual_id"] = "residual-conflict"
    target = dict(conflicting["route_target"])
    target["content_fingerprint"] = "c" * 64
    conflicting["route_target"] = target
    decisions.append(conflicting)
    calls = _install_read(monkeypatch, fields)

    execution = operation._call(_request(), object(), OperationExecutionContext(Path("/project")))  # type: ignore[arg-type]

    assert execution.outcome == "rejected"
    assert execution.result is None
    assert execution.changes == ()
    assert calls == ["workcase-0047"]
    assert "fingerprint" in execution.gaps[0]["summary"]


def test_candidate_operation_rejects_missing_closure_proposal_without_changes(monkeypatch) -> None:
    fields = _fields()
    del fields["closure_proposal"]
    calls = _install_read(monkeypatch, fields)

    execution = operation._call(_request(), object(), OperationExecutionContext(Path("/project")))  # type: ignore[arg-type]

    assert execution.outcome == "rejected"
    assert execution.result is None
    assert execution.changes == ()
    assert calls == ["workcase-0047"]


@pytest.mark.parametrize(
    ("fields", "check_status"),
    [
        (_fields(phase="closure_preparing"), "mechanically_valid"),
        (_fields(status="blocked"), "mechanically_valid"),
        (_fields(status="closed"), "mechanically_valid"),
        (_fields(), "invalid"),
    ],
)
def test_candidate_operation_rejects_non_gate2_or_invalid_source_without_changes(
    monkeypatch,
    fields,
    check_status,
) -> None:
    calls = _install_read(monkeypatch, fields, status=check_status)

    execution = operation._call(_request(), object(), OperationExecutionContext(Path("/project")))  # type: ignore[arg-type]

    assert execution.outcome == "rejected"
    assert execution.result is None
    assert execution.changes == ()
    assert calls == ["workcase-0047"]
