from __future__ import annotations

import json
from pathlib import Path

import pytest

from ldvh.facts.creation import CreationBoundary
from ldvh.facts.models import FactIssue, FactReference
from ldvh.facts.repository import FactReadResult
from ldvh.facts.schema import FactSchema
from ldvh.facts.workcase_update import WorkCaseWriteResult
from ldvh.filesystem import AtomicWriteResult
from ldvh.governance.models import LocatorSource, ScopeDescriptor
from ldvh.governance.resolver import GovernanceResolutionRun
from ldvh.helper.operation_runtime import OperationExecutionContext
from ldvh.helper.operations import IMPLEMENTATIONS, workcase_update_operation
from ldvh.helper.operations.workcase_update_request import (
    CorrectClosedWorkCaseRequest,
    RouteTargetFingerprint,
    UpdateWorkCaseRequest,
)
from ldvh.helper.requests import CommonRequest
from ldvh.helper.service import handle_request


def _domain() -> UpdateWorkCaseRequest:
    return UpdateWorkCaseRequest(
        workspace_root=Path("/project"),
        governance_scope=(),
        fact_ref=FactReference("sample", "workcase", "workcase-0006"),
        expected_content_fingerprint="a" * 64,
        fact_object={"status": "open", "title": "After"},
        authorization_reference=(),
        base=Path("/project"),
    )


def _run() -> GovernanceResolutionRun:
    return GovernanceResolutionRun(None, (), (), (), (), (), ())


def _read(
    *,
    title: str,
    fingerprint: str,
    raw_text: str,
    check_status: str = "mechanically_valid",
) -> FactReadResult:
    fields = None if check_status == "unavailable" else {"status": "open", "title": title}
    return FactReadResult(
        "ldvh-base/workcases/workcase-0006.yaml",
        "yaml",
        check_status,
        fields,
        None,
        () if check_status == "mechanically_valid" else (FactIssue("parse", "forced failure"),),
        content_fingerprint=fingerprint or None,
        raw_text=raw_text or None,
    )


def _boundary() -> CreationBoundary:
    return CreationBoundary("sample", Path("/project"), Path("/project/.git"))


def test_current_workcase_operations_are_registered_with_exact_inputs() -> None:
    candidate = IMPLEMENTATIONS["prepare-closed-workcase-candidate"]
    update = IMPLEMENTATIONS["update-workcase"]
    close = IMPLEMENTATIONS["close-workcase"]
    correct = IMPLEMENTATIONS["correct-closed-workcase"]

    assert candidate.required_inputs == ("arguments.fact_ref",)
    assert candidate.optional_inputs == ("work_object_locators", "arguments.workspace_root")

    assert update.required_inputs == (
        "arguments.fact_ref",
        "arguments.expected_content_fingerprint",
        "arguments.fact_object",
    )
    assert update.optional_inputs == (
        "work_object_locators",
        "arguments.workspace_root",
        "authorization_reference",
    )
    assert close.required_inputs == (*update.required_inputs, "authorization_reference")
    assert close.optional_inputs == ("work_object_locators", "arguments.workspace_root")
    assert correct.required_inputs == (
        *update.required_inputs,
        "arguments.route_target_fingerprints",
        "arguments.independent_review_reference",
    )
    assert correct.optional_inputs == update.optional_inputs


def test_capability_discovery_exposes_all_current_implementations() -> None:
    response = handle_request("capabilities", None, "{}").response

    assert response["outcome"] in {"ok", "partial"}
    operations = {
        item["operation_key"]: item
        for item in response["result"]["operations"]
        if item["operation_key"]
        in {
            "prepare-closed-workcase-candidate",
            "update-workcase",
            "close-workcase",
            "correct-closed-workcase",
        }
    }
    assert set(operations) == {
        "prepare-closed-workcase-candidate",
        "update-workcase",
        "close-workcase",
        "correct-closed-workcase",
    }
    assert all(item["implementation"]["present"] for item in operations.values())
    assert operations["prepare-closed-workcase-candidate"]["effect"] == "read"
    assert operations["prepare-closed-workcase-candidate"]["required_inputs"] == ["arguments.fact_ref"]
    assert operations["update-workcase"]["required_inputs"] == [
        "arguments.fact_ref",
        "arguments.expected_content_fingerprint",
        "arguments.fact_object",
    ]
    assert operations["close-workcase"]["required_inputs"][-1] == "authorization_reference"
    assert operations["correct-closed-workcase"]["required_inputs"][-2:] == [
        "arguments.route_target_fingerprints",
        "arguments.independent_review_reference",
    ]
    encoded = json.dumps(operations, ensure_ascii=False)
    assert "managed_records" not in encoded
    assert '"arguments.set"' not in encoded
    assert '"arguments.remove"' not in encoded
    assert "workcase-fact-type::update-workcase 输入与结果" in encoded
    assert "workcase-fact-type::close-workcase 输入与结果" in encoded
    assert "workcase-fact-type::correct-closed-workcase 输入与结果" in encoded


def test_success_result_is_exactly_the_shared_six_field_shape() -> None:
    before = FactReadResult(
        "ldvh-base/workcases/workcase-0006.yaml",
        "yaml",
        "mechanically_valid",
        {"status": "open", "summary": "Before"},
        None,
        (),
        content_fingerprint="a" * 64,
        raw_text="before\n",
    )
    after_fields = {"status": "open", "summary": "After"}
    after = FactReadResult(
        "ldvh-base/workcases/workcase-0006.yaml",
        "yaml",
        "mechanically_valid",
        after_fields,
        None,
        (),
        content_fingerprint="b" * 64,
        raw_text="after\n",
    )

    result = workcase_update_operation._result(before, after, "sample", "workcase-0006")

    assert result == {
        "actual_ref": {
            "governed_project_id": "sample",
            "fact_type_key": "workcase",
            "object_id": "workcase-0006",
        },
        "canonical_path": "ldvh-base/workcases/workcase-0006.yaml",
        "carrier": "yaml",
        "previous_content_fingerprint": "a" * 64,
        "content_fingerprint": "b" * 64,
        "fact_object": after_fields,
    }


def test_helper_adapter_passes_complete_correct_request_to_core_without_reconstructing_it(monkeypatch) -> None:
    source = FactReference("sample", "workcase", "workcase-0006")
    target = FactReference("sample", "workcase", "workcase-0042")
    review_reference = {"kind": "review", "locator": "review:closed-correction"}
    authorization = ({"kind": "human", "locator": "turn:12"},)
    domain = CorrectClosedWorkCaseRequest(
        workspace_root=Path("/workspace"),
        governance_scope=(ScopeDescriptor(0, "/project", LocatorSource.EXPLICIT_LOCATOR),),
        fact_ref=source,
        expected_content_fingerprint="a" * 64,
        fact_object={"title": "Corrected", "status": "closed"},
        authorization_reference=authorization,
        base=Path("/project"),
        route_target_fingerprints=(RouteTargetFingerprint(target, "b" * 64),),
        independent_review_reference=review_reference,
    )
    boundary = CreationBoundary("sample", Path("/project"), Path("/project/.git"))
    schema = FactSchema("workcase", ())
    captured = {}

    def fake_apply(command):
        captured["command"] = command
        return WorkCaseWriteResult("candidate_rejected", "2026-07-26T16:00:00+08:00")

    monkeypatch.setattr("ldvh.facts.workcase_update.apply_workcase_write", fake_apply)

    result = workcase_update_operation._apply_core_workcase_write(
        "correct",
        domain,
        boundary,
        {"workcase": schema},
        schema,
        "2026-07-26T16:00:00+08:00",
        {},
    )

    assert isinstance(result, WorkCaseWriteResult)
    command = captured["command"]
    assert command.mode == "correct"
    # 未提供 observed_context.signature → supplied 原样保留（既有行为）
    assert command.supplied == domain.fact_object
    assert command.authorization_reference == authorization
    assert command.independent_review_reference == review_reference
    assert len(command.route_target_fingerprints) == 1
    assert command.route_target_fingerprints[0].target == target
    assert command.route_target_fingerprints[0].content_fingerprint == "b" * 64
    assert command.route_target_fingerprints[0].origin_path == "route_target_fingerprints[0].target"


def test_workcase_helper_chinese_describes_the_mechanical_boundary_without_overclaiming() -> None:
    module = Path(workcase_update_operation.__file__).read_text(encoding="utf-8")

    assert "当前 WorkCase 不满足该操作对变更前快照的要求" in module
    assert "提交给 WorkCase 核心事务的请求结构不符合规范" in module
    assert "完整 after 的结构与转换机械检查、CAS 与写后回读已通过" in module
    assert "当前 WorkCase 未形成该操作可消费的 before" not in module
    assert "WorkCase Core 请求未满足专属事务结构" not in module
    assert "完整 after、operation transition、CAS 与写后读取已通过" not in module


def test_common_whitespace_authorization_is_rejected_before_rule_read_or_write(monkeypatch) -> None:
    reached: list[str] = []

    def forbidden_rule_read(*args, **kwargs):
        reached.append("rule_read")
        raise AssertionError("invalid common request must stop before rule-source inspection")

    def forbidden_core_write(*args, **kwargs):
        reached.append("core_write")
        raise AssertionError("invalid common request must stop before the WorkCase write adapter")

    monkeypatch.setattr("ldvh.helper.service.inspect_colocated_rule_source", forbidden_rule_read)
    monkeypatch.setattr(workcase_update_operation, "_apply_core_workcase_write", forbidden_core_write)

    result = handle_request(
        "call",
        "close-workcase",
        json.dumps(
            {
                "authorization_reference": [
                    {"kind": "   ", "locator": "\t"},
                ]
            }
        ),
    )

    assert result.response["outcome"] == "invalid_request"
    assert result.response["changes"] == []
    assert reached == []


def test_helper_preserves_committed_result_when_coordination_release_is_uncertain(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    domain = _domain()
    run = _run()
    boundary = _boundary()
    schema = FactSchema("workcase", ())
    before = _read(title="Before", fingerprint="a" * 64, raw_text="before\n")
    after = _read(title="After", fingerprint="b" * 64, raw_text="after\n")
    application = WorkCaseWriteResult(
        "updated",
        "2026-07-26T16:00:00+08:00",
        current=before,
        candidate=after,
        readback=after,
        candidate_text="after\n",
        replacement_result=AtomicWriteResult.committed("replaced"),
        coordination_release_uncertain=True,
    )

    monkeypatch.setattr(workcase_update_operation, "_validated_request", lambda *_args: domain)
    monkeypatch.setattr(workcase_update_operation, "_governance", lambda *_args: run)
    monkeypatch.setattr(workcase_update_operation, "_boundary", lambda *_args: boundary)
    monkeypatch.setattr(
        workcase_update_operation,
        "project_fact_schemas",
        lambda *_args: {"workcase": schema},
    )
    monkeypatch.setattr(workcase_update_operation, "native_atomic_fact_writes_supported", lambda: True)
    monkeypatch.setattr(
        workcase_update_operation,
        "_apply_core_workcase_write",
        lambda *_args: application,
    )
    request = CommonRequest(None, (), {}, None, {}, (), response_profile="diagnostic")

    execution = workcase_update_operation._execute(
        "update",
        request,
        object(),
        OperationExecutionContext(Path("/project"), "2026-07-26T16:00:00+08:00"),
    )

    assert execution.outcome == "ok"
    assert execution.completed_scope == execution.requested_scope == (domain.fact_ref.to_json(),)
    assert execution.not_completed_scope == ()
    assert execution.result is not None
    assert set(execution.result) == {
        "actual_ref",
        "canonical_path",
        "carrier",
        "previous_content_fingerprint",
        "content_fingerprint",
        "fact_object",
    }
    assert execution.result["fact_object"]["title"] == "After"
    assert execution.changes[0]["status"] == "updated"
    assert execution.verification[0]["status"] == "passed"
    assert execution.gaps[0]["code"] == "controlled_write_lock_release_uncertain"
    assert "原子替换已在 Working Tree 生效并成功回读" in execution.gaps[0]["summary"]
    assert "后续受控写" in execution.gaps[0]["summary"]
    assert execution.diagnostics[0]["details"]["stage"] == "common_dir_lock_release"
    assert execution.follow_up is not None
    assert execution.follow_up["resume_conditions"]


def test_workcase_helper_preserves_candidate_rejection_when_coordination_release_is_uncertain(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    domain = _domain()
    run = _run()
    boundary = _boundary()
    schema = FactSchema("workcase", ())
    application = WorkCaseWriteResult(
        "candidate_rejected",
        "2026-07-26T16:00:00+08:00",
        issues=(FactIssue("schema", "forced candidate rejection"),),
        coordination_release_uncertain=True,
    )
    monkeypatch.setattr(workcase_update_operation, "_validated_request", lambda *_args: domain)
    monkeypatch.setattr(workcase_update_operation, "_governance", lambda *_args: run)
    monkeypatch.setattr(workcase_update_operation, "_boundary", lambda *_args: boundary)
    monkeypatch.setattr(
        workcase_update_operation,
        "project_fact_schemas",
        lambda *_args: {"workcase": schema},
    )
    monkeypatch.setattr(workcase_update_operation, "native_atomic_fact_writes_supported", lambda: True)
    monkeypatch.setattr(
        workcase_update_operation,
        "_apply_core_workcase_write",
        lambda *_args: application,
    )

    execution = workcase_update_operation._execute(
        "update",
        CommonRequest(None, (), {}, None, {}, (), response_profile="diagnostic"),
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


@pytest.mark.parametrize(
    ("namespace_state", "expected", "excluded"),
    [
        ("uncertain", "原子替换是否生效无法确认", "已确认原子替换未"),
        ("not_committed", "已确认原子替换未", "原子替换是否生效无法确认"),
    ],
)
def test_workcase_helper_distinguishes_uncertain_namespace_from_known_noncommit(
    namespace_state: str,
    expected: str,
    excluded: str,
) -> None:
    application = WorkCaseWriteResult(
        "replacement_unavailable",
        "2026-07-26T16:00:00+08:00",
        replacement_result=(
            AtomicWriteResult.uncertain()
            if namespace_state == "uncertain"
            else AtomicWriteResult.not_committed("unavailable")
        ),
    )

    execution = workcase_update_operation._application_failure(
        "update",
        application,
        _domain(),
        _run(),
        (),
        _boundary(),
        "2026-07-26T16:00:00+08:00",
    )

    assert execution is not None
    assert execution.outcome == "unavailable"
    assert execution.completed_scope == ()
    assert execution.not_completed_scope == (_domain().fact_ref.to_json(),)
    assert execution.changes == ()
    assert expected in execution.gaps[0]["summary"]
    assert excluded not in execution.gaps[0]["summary"]


def test_no_change_release_gap_keeps_observation_time_without_using_commit_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    domain = _domain()
    run = _run()
    boundary = _boundary()
    schema = FactSchema("workcase", ())
    current = _read(title="Before", fingerprint="a" * 64, raw_text="before\n")
    application = WorkCaseWriteResult(
        "no_change",
        "2026-07-26T16:00:00+08:00",
        current=current,
        readback=current,
        coordination_release_uncertain=True,
    )
    monkeypatch.setattr(workcase_update_operation, "_validated_request", lambda *_args: domain)
    monkeypatch.setattr(workcase_update_operation, "_governance", lambda *_args: run)
    monkeypatch.setattr(workcase_update_operation, "_boundary", lambda *_args: boundary)
    monkeypatch.setattr(
        workcase_update_operation,
        "project_fact_schemas",
        lambda *_args: {"workcase": schema},
    )
    monkeypatch.setattr(workcase_update_operation, "native_atomic_fact_writes_supported", lambda: True)
    monkeypatch.setattr(
        workcase_update_operation,
        "_apply_core_workcase_write",
        lambda *_args: application,
    )
    event_at = "2026-07-26T16:00:00+08:00"

    execution = workcase_update_operation._execute(
        "update",
        CommonRequest(None, (), {}, None, {}, (), response_profile="diagnostic"),
        object(),
        OperationExecutionContext(Path("/project"), event_at),
    )

    assert execution.outcome == "no_change"
    assert execution.completed_scope == execution.requested_scope == (domain.fact_ref.to_json(),)
    assert execution.not_completed_scope == ()
    assert execution.changes == ()
    assert "code" not in execution.gaps[0]
    assert "事实目标确认未变化" in execution.gaps[0]["summary"]
    working_tree_sources = [source for source in execution.sources if source["kind"] == "working_tree"]
    assert len(working_tree_sources) == 1
    assert working_tree_sources[0]["observed_at"] == event_at


def test_workcase_helper_reports_the_fresh_external_residual_after_rollback_conflict() -> None:
    before = _read(title="Before", fingerprint="a" * 64, raw_text="before\n")
    candidate = _read(title="Candidate", fingerprint="b" * 64, raw_text="candidate\n")
    residual = _read(title="External", fingerprint="c" * 64, raw_text="external\n")
    application = WorkCaseWriteResult(
        "readback_failed",
        "2026-07-26T16:00:00+08:00",
        issues=(FactIssue("reference", "forced post-write target drift"),),
        current=before,
        candidate=candidate,
        readback=candidate,
        candidate_text="candidate\n",
        replacement_result=AtomicWriteResult.committed("replaced"),
        rollback_result=AtomicWriteResult.not_committed("conflict"),
        residual_readback=residual,
    )

    execution = workcase_update_operation._application_failure(
        "update",
        application,
        _domain(),
        _run(),
        (),
        _boundary(),
        "2026-07-26T16:00:00+08:00",
    )

    assert execution is not None
    assert execution.outcome == "error"
    assert execution.summary == "写后回读未通过，且未能确认条件回滚已经完成"
    assert execution.changes[0]["status"] == "rollback-failed"
    assert "当前重新读取观察到的实际 WorkCase 事实载体是另一机械有效版本" in execution.changes[0]["summary"]
    assert "本次新载体" not in execution.changes[0]["summary"]
    observation = execution.changes[0]["source_refs"][-1]
    assert observation["details"] == {
        "view": "Working Tree",
        "check_status": "mechanically_valid",
        "content_fingerprint": "c" * 64,
    }
    assert execution.verification[0]["status"] == "passed"


def test_workcase_helper_marks_actual_residual_unavailable_without_guessing() -> None:
    before = _read(title="Before", fingerprint="a" * 64, raw_text="before\n")
    candidate = _read(title="Candidate", fingerprint="b" * 64, raw_text="candidate\n")
    unavailable = _read(title="", fingerprint="", raw_text="", check_status="unavailable")
    application = WorkCaseWriteResult(
        "readback_failed",
        "2026-07-26T16:00:00+08:00",
        issues=(FactIssue("reference", "forced post-write target drift"),),
        current=before,
        candidate=candidate,
        readback=candidate,
        candidate_text="candidate\n",
        replacement_result=AtomicWriteResult.committed("replaced"),
        rollback_result=AtomicWriteResult.uncertain(),
        residual_readback=unavailable,
    )

    execution = workcase_update_operation._application_failure(
        "update",
        application,
        _domain(),
        _run(),
        (),
        _boundary(),
        "2026-07-26T16:00:00+08:00",
    )

    assert execution is not None
    assert execution.outcome == "error"
    assert execution.summary == "写后回读未通过，且未能确认条件回滚已经完成"
    assert execution.changes[0]["summary"] == (
        "条件回滚在文件命名空间（namespace）中的生效情况无法确认；实际 WorkCase 事实载体的残留状态无法确认"
    )
    assert all("本次新载体" not in item["summary"] for item in execution.changes)
    assert any("实际 WorkCase 事实载体无法确认" in gap["summary"] for gap in execution.gaps)
    assert execution.verification[0]["status"] == "unavailable"


def test_workcase_helper_separates_complete_carrier_read_from_invalid_object() -> None:
    before = _read(title="Before", fingerprint="a" * 64, raw_text="before\n")
    candidate = _read(title="Candidate", fingerprint="b" * 64, raw_text="candidate\n")
    invalid = _read(
        title="Invalid external carrier",
        fingerprint="c" * 64,
        raw_text="invalid-external\n",
        check_status="invalid",
    )
    application = WorkCaseWriteResult(
        "readback_failed",
        "2026-07-26T16:00:00+08:00",
        issues=(FactIssue("reference", "forced post-write target drift"),),
        current=before,
        candidate=candidate,
        readback=candidate,
        candidate_text="candidate\n",
        replacement_result=AtomicWriteResult.committed("replaced"),
        rollback_result=AtomicWriteResult.not_committed("conflict"),
        residual_readback=invalid,
    )

    execution = workcase_update_operation._application_failure(
        "update",
        application,
        _domain(),
        _run(),
        (),
        _boundary(),
        "2026-07-26T16:00:00+08:00",
    )

    assert execution is not None
    assert execution.changes[0]["summary"] == (
        "条件回滚发生冲突，确认未在文件命名空间（namespace）生效；"
        "当前实际 WorkCase 事实载体已安全完整读取，但对象未通过机械检查"
    )
    assert execution.verification[0]["check"] == ("条件回滚后重新精确读取并机械检查实际 WorkCase 事实载体")
    assert execution.verification[0]["status"] == "failed"
    assert not any("无法确认" in gap["summary"] for gap in execution.gaps[1:])


@pytest.mark.parametrize(
    ("rollback", "expected", "excluded"),
    [
        (
            AtomicWriteResult.not_committed("conflict"),
            "条件回滚发生冲突，确认未在文件命名空间（namespace）生效",
            "生效情况无法确认",
        ),
        (
            AtomicWriteResult.uncertain(),
            "条件回滚在文件命名空间（namespace）中的生效情况无法确认",
            "确认未在文件命名空间（namespace）生效",
        ),
    ],
)
def test_workcase_helper_separates_rollback_namespace_evidence_when_residual_matches_before(
    rollback: AtomicWriteResult,
    expected: str,
    excluded: str,
) -> None:
    before = _read(title="Before", fingerprint="a" * 64, raw_text="before\n")
    candidate = _read(title="Candidate", fingerprint="b" * 64, raw_text="candidate\n")
    application = WorkCaseWriteResult(
        "readback_failed",
        "2026-07-26T16:00:00+08:00",
        current=before,
        candidate=candidate,
        readback=candidate,
        candidate_text="candidate\n",
        replacement_result=AtomicWriteResult.committed("replaced"),
        rollback_result=rollback,
        residual_readback=before,
    )

    execution = workcase_update_operation._application_failure(
        "update",
        application,
        _domain(),
        _run(),
        (),
        _boundary(),
        "2026-07-26T16:00:00+08:00",
    )

    assert execution is not None
    summary = execution.changes[0]["summary"]
    assert expected in summary
    assert excluded not in summary
    assert "当前重新读取观察到的实际 WorkCase 事实载体完整字节内容与更新前载体一致" in summary
    assert "已恢复" not in summary


@pytest.mark.parametrize(
    ("residual", "expected"),
    [
        (
            FactReadResult(
                "ldvh-base/workcases/workcase-0006.yaml",
                "yaml",
                "not_found",
                None,
                None,
                (FactIssue("location", "事实对象预期位置不存在"),),
            ),
            "当前重新读取确认实际 WorkCase 事实载体的预期位置不存在",
        ),
        (
            FactReadResult(
                "ldvh-base/workcases/workcase-0006.yaml",
                "yaml",
                "invalid",
                None,
                None,
                (FactIssue("location", "canonical path 不是普通文件"),),
            ),
            "当前实际 WorkCase 事实载体未能安全完整读取，机械检查未通过（状态为 `invalid`）",
        ),
    ],
)
def test_workcase_helper_does_not_claim_an_unread_residual_was_fully_read(
    residual: FactReadResult,
    expected: str,
) -> None:
    before = _read(title="Before", fingerprint="a" * 64, raw_text="before\n")
    candidate = _read(title="Candidate", fingerprint="b" * 64, raw_text="candidate\n")
    application = WorkCaseWriteResult(
        "readback_failed",
        "2026-07-26T16:00:00+08:00",
        current=before,
        candidate=candidate,
        readback=candidate,
        candidate_text="candidate\n",
        replacement_result=AtomicWriteResult.committed("replaced"),
        rollback_result=AtomicWriteResult.not_committed("conflict"),
        residual_readback=residual,
    )

    execution = workcase_update_operation._application_failure(
        "update",
        application,
        _domain(),
        _run(),
        (),
        _boundary(),
        "2026-07-26T16:00:00+08:00",
    )

    assert execution is not None
    assert expected in execution.changes[0]["summary"]
    assert "已完整读取，但对象未通过" not in execution.changes[0]["summary"]
    assert execution.verification[0]["status"] == "failed"


def test_release_uncertainty_code_and_success_boundary_are_defined_by_current_source() -> None:
    foundation = (Path(__file__).resolve().parents[3] / "specs/05-事实模型基础规范.md").read_text(encoding="utf-8")

    assert "`controlled_write_lock_release_uncertain`" in foundation
    assert "事实目标仍属于已完成范围" in foundation
    assert "不得把事实写入表述为未知" in foundation
    assert "后续受控写的串行协调状态无法确认" in foundation
