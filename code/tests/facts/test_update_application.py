from __future__ import annotations

import ast
import subprocess
from pathlib import Path

from ldvh.facts import update_application
from ldvh.facts.creation import CreationBoundary
from ldvh.facts.models import FactIssue
from ldvh.facts.repository import FactReadResult
from ldvh.facts.schema import project_fact_schemas
from ldvh.facts.update_application import FactUpdateCommand, apply_fact_update
from ldvh.specs.repository import inspect_repository


def _git(project: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(project), *arguments],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _command(current_specs_repository: Path, tmp_path: Path) -> tuple[FactUpdateCommand, Path]:
    project = tmp_path / "project"
    project.mkdir()
    _git(project, "init", "-q")
    common_dir = Path(_git(project, "rev-parse", "--path-format=absolute", "--git-common-dir"))
    fact = project / "ldvh-base/sparks/spark-0001.yaml"
    fact.parent.mkdir(parents=True)
    fact.write_text(
        """object_id: spark-0001
fact_type_key: spark
title: Application update
created_at: 2026-07-20T09:00:00+08:00
updated_at: 2026-07-20T10:00:00+08:00
status: open
summary: Before update
priority: P2
""",
        encoding="utf-8",
    )
    schemas = project_fact_schemas(inspect_repository(current_specs_repository))
    current = update_application._project_read(
        FactUpdateCommand(
            boundary=CreationBoundary("sample", project, common_dir),
            fact_type_key="spark",
            object_id="spark-0001",
            schemas=schemas,
            schema=schemas["spark"],
            expected_content_fingerprint="0" * 64,
            supplied={},
            body=None,
            event_at="2026-07-20T11:00:00+08:00",
        )
    )
    assert current.fields is not None and current.content_fingerprint is not None
    supplied = {key: value for key, value in current.fields.items() if key not in update_application.MANAGED_FIELDS}
    supplied["summary"] = "After update"
    return (
        FactUpdateCommand(
            boundary=CreationBoundary("sample", project, common_dir),
            fact_type_key="spark",
            object_id="spark-0001",
            schemas=schemas,
            schema=schemas["spark"],
            expected_content_fingerprint=current.content_fingerprint,
            supplied=supplied,
            body=None,
            event_at="2026-07-20T11:00:00+08:00",
        ),
        fact,
    )


def test_application_module_has_no_helper_dependency() -> None:
    module = Path(__file__).resolve().parents[2] / "ldvh/facts/update_application.py"
    tree = ast.parse(module.read_text(encoding="utf-8"))
    imports = {alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names} | {
        node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
    }
    assert not any(name == "ldvh.helper" or name.startswith("ldvh.helper.") for name in imports)


def test_generic_managed_record_gate_blocks_v2_event_formation_but_not_legacy_compatibility() -> None:
    v2_before = {
        "workcase_profile": "control-contract-v2",
        "phase": "human_plan_confirming",
        "plan_version": 1,
        "creation_reviews": [],
    }
    v2_approval = {
        **v2_before,
        "phase": "executing",
        "execution_approval": {"subject_version": 1, "approved_at": "2026-07-26T13:00:00+08:00"},
    }
    issues = update_application._generic_workcase_managed_record_issues(v2_before, v2_approval)
    assert any(issue.field_path == "execution_approval" and "update-workcase" in issue.summary for issue in issues)

    v2_reviewing = {**v2_before, "phase": "independent_reviewing", "result_version": 1}
    v2_review = {
        **v2_reviewing,
        "result_reviews": [
            {
                "reviewer": "reviewer",
                "reviewed_at": "2026-07-26T13:00:00+08:00",
                "subject_version": 1,
            }
        ],
    }
    issues = update_application._generic_workcase_managed_record_issues(v2_reviewing, v2_review)
    assert any(issue.field_path == "result_reviews" and "update-workcase" in issue.summary for issue in issues)

    legacy_before = {"phase": "human_plan_confirming", "plan_version": 1, "creation_reviews": []}
    legacy_after = {
        **legacy_before,
        "phase": "executing",
        "execution_approval": {"subject_version": 1, "approved_at": "2026-07-14T10:00:00+08:00"},
    }
    assert update_application._generic_workcase_managed_record_issues(legacy_before, legacy_after) == ()


def test_generic_managed_record_gate_cannot_be_bypassed_by_repairing_unknown_profile_to_v2() -> None:
    invalid_before = {
        "workcase_profile": "unknown-contract",
        "status": "open",
        "phase": "human_plan_confirming",
        "plan_version": 1,
        "creation_reviews": [],
    }
    forged_review = {
        **invalid_before,
        "workcase_profile": "control-contract-v2",
        "plan_version": 2,
        "creation_reviews": [
            {
                "reviewer": "forged-reviewer",
                "reviewed_at": "2026-07-26T13:00:00+08:00",
                "subject_version": 2,
            }
        ],
    }
    review_issues = update_application._generic_workcase_managed_record_issues(
        invalid_before,
        forged_review,
        repairing_invalid_before=True,
    )
    assert any(issue.field_path == "creation_reviews" and "update-workcase" in issue.summary for issue in review_issues)

    forged_approval = {
        **invalid_before,
        "workcase_profile": "control-contract-v2",
        "phase": "executing",
        "execution_approval": {
            "subject_version": 1,
            "approved_at": "2026-07-26T13:00:00+08:00",
        },
    }
    approval_issues = update_application._generic_workcase_managed_record_issues(
        invalid_before,
        forged_approval,
        repairing_invalid_before=True,
    )
    assert any(
        issue.field_path == "execution_approval" and "update-workcase" in issue.summary
        for issue in approval_issues
    )


def test_generic_gate_rejects_review_event_deletion_or_reordering_without_a_version_reset() -> None:
    first = {
        "reviewer": "reviewer-a",
        "reviewed_at": "2026-07-26T13:00:00+08:00",
        "subject_version": 1,
    }
    second = {
        "reviewer": "reviewer-b",
        "reviewed_at": "2026-07-26T13:05:00+08:00",
        "subject_version": 1,
    }
    before = {
        "workcase_profile": "control-contract-v2",
        "status": "open",
        "phase": "independent_reviewing",
        "plan_version": 1,
        "result_version": 1,
        "creation_reviews": [first, second],
        "result_reviews": [first, second],
    }

    creation_deleted = {**before, "creation_reviews": [first]}
    creation_issues = update_application._generic_workcase_managed_record_issues(before, creation_deleted)
    assert any(issue.field_path == "creation_reviews" and "移除" in issue.summary for issue in creation_issues)

    result_deleted = {**before, "result_reviews": [second]}
    result_issues = update_application._generic_workcase_managed_record_issues(before, result_deleted)
    assert any(issue.field_path == "result_reviews" and "移除" in issue.summary for issue in result_issues)

    reordered = {**before, "creation_reviews": [second, first]}
    reorder_issues = update_application._generic_workcase_managed_record_issues(before, reordered)
    assert any(issue.field_path == "creation_reviews" and "顺序不变" in issue.summary for issue in reorder_issues)


def test_generic_gate_does_not_claim_to_decide_same_event_fact_correction_semantics() -> None:
    before = {
        "workcase_profile": "control-contract-v2",
        "phase": "controller_checking",
        "plan_version": 1,
        "result_version": 1,
        "execution_approval": {
            "subject_version": 1,
            "approved_at": "2026-07-26T13:00:00+08:00",
            "summary": "Original recorded wording",
        },
        "result_reviews": [
            {
                "reviewer": "reviewer",
                "reviewed_at": "2026-07-26T13:30:00+08:00",
                "subject_version": 1,
                "scope": "Current result",
                "conclusion": "changes_required",
                "feedback": ["Original recorded feedback"],
                "controller_resolution": "Original recorded resolution",
            }
        ],
    }
    corrected = {
        **before,
        "execution_approval": {**before["execution_approval"], "summary": "Corrected recorded wording"},
        "result_reviews": [
            {
                **before["result_reviews"][0],
                "feedback": ["Corrected recorded feedback"],
                "controller_resolution": "Corrected recorded resolution",
            }
        ],
    }

    assert update_application._generic_workcase_managed_record_issues(before, corrected) == ()

    retimed = {
        **before,
        "execution_approval": {
            **before["execution_approval"],
            "approved_at": "2026-07-26T13:05:00+08:00",
        },
    }
    issues = update_application._generic_workcase_managed_record_issues(before, retimed)
    assert any(issue.field_path == "execution_approval" and "事件身份" in issue.summary for issue in issues)

    corrected_on_phase_edge = {**corrected, "phase": "closure_preparing"}
    issues = update_application._generic_workcase_managed_record_issues(before, corrected_on_phase_edge)
    assert any(issue.field_path == "result_reviews" and "lifecycle" in issue.summary for issue in issues)
    assert any(issue.field_path == "execution_approval" and "原样保留" in issue.summary for issue in issues)

    closed_before = {
        "workcase_profile": "control-contract-v2",
        "status": "closed",
        "phase": "closed",
        "plan_version": 1,
        "result_version": 1,
        "closure_approval": {
            "subject_version": 1,
            "approved_at": "2026-07-26T14:00:00+08:00",
            "summary": "Original closure wording",
        },
    }
    corrected_closure = {
        **closed_before,
        "closure_approval": {**closed_before["closure_approval"], "summary": "Corrected closure wording"},
    }
    assert update_application._generic_workcase_managed_record_issues(closed_before, corrected_closure) == ()
    corrected_closure_on_edge = {
        **corrected_closure,
        "status": "open",
        "phase": "human_closure_confirming",
    }
    issues = update_application._generic_workcase_managed_record_issues(closed_before, corrected_closure_on_edge)
    assert any(issue.field_path == "closure_approval" and "原样保留" in issue.summary for issue in issues)


def test_generic_gate_allows_required_resolution_with_a_valid_same_event_reviewer_correction() -> None:
    review = {
        "reviewer": "independent-reviewer",
        "reviewed_at": "2026-07-26T13:30:00+08:00",
        "subject_version": 1,
        "scope": "Original review scope",
        "conclusion": "pass",
    }
    corrected_review = {
        **review,
        "conclusion": "changes_required",
        "feedback": ["The original review omitted one finding"],
        "controller_resolution": "Accepted the corrected finding.",
    }
    creation_before = {
        "workcase_profile": "control-contract-v2",
        "status": "open",
        "phase": "human_plan_confirming",
        "plan_version": 1,
        "creation_reviews": [review],
    }
    creation_after = {**creation_before, "creation_reviews": [corrected_review]}
    assert update_application._generic_workcase_managed_record_issues(creation_before, creation_after) == ()

    result_before = {
        "workcase_profile": "control-contract-v2",
        "status": "open",
        "phase": "controller_checking",
        "plan_version": 1,
        "result_version": 1,
        "result_reviews": [review],
    }
    result_after = {**result_before, "result_reviews": [corrected_review]}
    assert update_application._generic_workcase_managed_record_issues(result_before, result_after) == ()

    still_reviewing = {**result_before, "phase": "independent_reviewing"}
    corrected_while_reviewing = {**still_reviewing, "result_reviews": [corrected_review]}
    issues = update_application._generic_workcase_managed_record_issues(
        still_reviewing,
        corrected_while_reviewing,
    )
    assert any(issue.field_path == "result_reviews" and "Controller 处置" in issue.summary for issue in issues)


def test_generic_gate_counts_resolution_events_when_review_identities_repeat() -> None:
    review = {
        "reviewer": "same-reviewer",
        "reviewed_at": "2026-07-26T13:30:00+08:00",
        "subject_version": 1,
        "scope": "Current result",
        "conclusion": "changes_required",
        "feedback": ["One finding"],
    }
    before = {
        "workcase_profile": "control-contract-v2",
        "phase": "independent_reviewing",
        "plan_version": 1,
        "result_version": 1,
        "result_reviews": [review, {**review, "controller_resolution": "Existing resolution"}],
    }
    formed_second_resolution = {
        **before,
        "result_reviews": [
            {**review, "controller_resolution": "New resolution"},
            before["result_reviews"][1],
        ],
    }

    issues = update_application._generic_workcase_managed_record_issues(before, formed_second_resolution)
    assert any(issue.field_path == "result_reviews" and "Controller 处置" in issue.summary for issue in issues)

    corrected_existing_resolution = {
        **before,
        "result_reviews": [
            review,
            {**review, "controller_resolution": "Corrected existing resolution"},
        ],
    }
    assert update_application._generic_workcase_managed_record_issues(before, corrected_existing_resolution) == ()


def test_generic_gate_allows_only_same_event_resolution_during_invalid_before_repair() -> None:
    review = {
        "reviewer": "independent-reviewer",
        "reviewed_at": "2026-07-26T13:30:00+08:00",
        "subject_version": 1,
        "scope": "Current result",
        "conclusion": "changes_required",
        "feedback": ["One finding"],
    }
    before = {
        "workcase_profile": "control-contract-v2",
        "status": "open",
        "phase": "controller_checking",
        "plan_version": 1,
        "result_version": 1,
        "result_reviews": [review],
    }
    repaired = {
        **before,
        "result_reviews": [{**review, "controller_resolution": "Accepted and handled."}],
    }

    ordinary_issues = update_application._generic_workcase_managed_record_issues(before, repaired)
    assert any("Controller 处置" in issue.summary for issue in ordinary_issues)
    assert (
        update_application._generic_workcase_managed_record_issues(
            before,
            repaired,
            repairing_invalid_before=True,
        )
        == ()
    )

    retimed = {
        **repaired,
        "result_reviews": [
            {
                **repaired["result_reviews"][0],
                "reviewed_at": "2026-07-26T13:31:00+08:00",
            }
        ],
    }
    issues = update_application._generic_workcase_managed_record_issues(
        before,
        retimed,
        repairing_invalid_before=True,
    )
    assert any("review 必须使用 update-workcase" in issue.summary for issue in issues)

    moved = {**repaired, "phase": "closure_preparing"}
    issues = update_application._generic_workcase_managed_record_issues(
        before,
        moved,
        repairing_invalid_before=True,
    )
    assert any("Controller 处置" in issue.summary or "lifecycle" in issue.summary for issue in issues)

    widened = {
        **repaired,
        "summary": "Also changed while repairing the invalid review",
        "result_reviews": [
            {
                **repaired["result_reviews"][0],
                "feedback": ["Also rewrote Reviewer-owned feedback"],
            }
        ],
    }
    issues = update_application._generic_workcase_managed_record_issues(
        before,
        widened,
        repairing_invalid_before=True,
    )
    assert any("invalid-before 窄修复" in issue.summary for issue in issues)

    second_review = {
        **review,
        "reviewer": "second-independent-reviewer",
        "reviewed_at": "2026-07-26T13:35:00+08:00",
    }
    two_missing = {**before, "result_reviews": [review, second_review]}
    two_repaired = {
        **two_missing,
        "result_reviews": [
            {**review, "controller_resolution": "Accepted first finding."},
            {**second_review, "controller_resolution": "Accepted second finding."},
        ],
    }
    issues = update_application._generic_workcase_managed_record_issues(
        two_missing,
        two_repaired,
        repairing_invalid_before=True,
    )
    assert any("唯一窄例外" in issue.summary or "invalid-before 窄修复" in issue.summary for issue in issues)


def test_generic_invalid_before_ordinary_repair_preserves_all_managed_record_content() -> None:
    review = {
        "reviewer": "independent-plan-reviewer",
        "reviewed_at": "2026-07-26T13:30:00+08:00",
        "subject_version": 1,
        "scope": "Original reviewed plan",
        "conclusion": "pass",
    }
    approval = {
        "subject_version": 1,
        "approved_at": "2026-07-26T13:45:00+08:00",
        "summary": "Original Human approval statement",
    }
    invalid_before = {
        "workcase_profile": "control-contract-v2",
        "status": "open",
        "phase": "executing",
        "summary": "",
        "plan_version": 1,
        "creation_reviews": [review],
        "execution_approval": approval,
    }
    rewritten = {
        **invalid_before,
        "summary": "Repaired current summary",
        "creation_reviews": [{**review, "scope": "Silently rewritten review scope"}],
        "execution_approval": {**approval, "summary": "Silently rewritten approval statement"},
    }

    issues = update_application._generic_workcase_managed_record_issues(
        invalid_before,
        rewritten,
        repairing_invalid_before=True,
    )

    assert any(
        issue.field_path == "creation_reviews" and "invalid-before 修复必须原样保留" in issue.summary
        for issue in issues
    )
    assert any(
        issue.field_path == "execution_approval" and "invalid-before 修复必须原样保留" in issue.summary
        for issue in issues
    )


def test_application_binds_managed_timestamp_and_verifies_exact_readback(
    current_specs_repository: Path,
    tmp_path: Path,
) -> None:
    command, fact = _command(current_specs_repository, tmp_path)

    result = apply_fact_update(command)

    assert result.status == "updated"
    assert result.readback is not None and result.readback.fields is not None
    assert result.readback.fields["updated_at"] == command.event_at
    assert result.readback.fields["summary"] == "After update"
    assert result.readback.raw_text == result.candidate_text
    assert fact.read_text(encoding="utf-8") == result.candidate_text


def test_no_change_does_not_require_successor_or_rewrite(
    current_specs_repository: Path,
    tmp_path: Path,
) -> None:
    command, fact = _command(current_specs_repository, tmp_path)
    current = update_application._project_read(command)
    assert current.fields is not None
    supplied = {key: value for key, value in current.fields.items() if key not in update_application.MANAGED_FIELDS}
    no_change = FactUpdateCommand(
        boundary=command.boundary,
        fact_type_key=command.fact_type_key,
        object_id=command.object_id,
        schemas=command.schemas,
        schema=command.schema,
        expected_content_fingerprint=command.expected_content_fingerprint,
        supplied=supplied,
        body=None,
        event_at="2026-07-20T08:00:00+08:00",
    )
    original = fact.read_bytes()
    inode = fact.stat().st_ino

    result = apply_fact_update(no_change)

    assert result.status == "no_change"
    assert fact.read_bytes() == original
    assert fact.stat().st_ino == inode


def test_open_spark_can_enter_implemented_without_a_routed_to_target(
    current_specs_repository: Path,
    tmp_path: Path,
) -> None:
    command, _fact = _command(current_specs_repository, tmp_path)
    supplied = dict(command.supplied)
    supplied.update(
        {
            "status": "implemented",
            "disposition_summary": (
                "The bounded Spark content was directly implemented with no residual fact responsibility."
            ),
        }
    )
    supplied.pop("priority")

    result = apply_fact_update(
        FactUpdateCommand(
            boundary=command.boundary,
            fact_type_key=command.fact_type_key,
            object_id=command.object_id,
            schemas=command.schemas,
            schema=command.schema,
            expected_content_fingerprint=command.expected_content_fingerprint,
            supplied=supplied,
            body=None,
            event_at=command.event_at,
        )
    )

    assert result.status == "updated"
    assert result.readback is not None and result.readback.fields is not None
    assert result.readback.fields["status"] == "implemented"


def test_parseable_invalid_spark_can_be_repaired_to_implemented_with_exact_cas(
    current_specs_repository: Path,
    tmp_path: Path,
) -> None:
    command, fact = _command(current_specs_repository, tmp_path)
    fact.write_text(
        """object_id: spark-0001
fact_type_key: spark
title: Application update
created_at: 2026-07-20T09:00:00+08:00
updated_at: 2026-07-20T10:00:00+08:00
status: routed
summary: Before update
disposition_summary: Incorrectly recorded as routed without a fact target.
""",
        encoding="utf-8",
    )
    current = update_application._project_read(command)
    assert current.check_status == "invalid"
    assert current.fields is not None and current.content_fingerprint is not None
    supplied = {key: value for key, value in current.fields.items() if key not in update_application.MANAGED_FIELDS}
    supplied.update(
        {
            "status": "implemented",
            "disposition_summary": (
                "The bounded Spark content was directly implemented with no residual fact responsibility."
            ),
        }
    )

    result = apply_fact_update(
        FactUpdateCommand(
            boundary=command.boundary,
            fact_type_key=command.fact_type_key,
            object_id=command.object_id,
            schemas=command.schemas,
            schema=command.schema,
            expected_content_fingerprint=current.content_fingerprint,
            supplied=supplied,
            body=None,
            event_at=command.event_at,
        )
    )

    assert result.status == "updated"
    assert result.readback is not None and result.readback.check_status == "mechanically_valid"
    assert result.readback.fields is not None and result.readback.fields["status"] == "implemented"


def test_non_successor_event_time_and_stale_fingerprint_have_zero_writes(
    current_specs_repository: Path,
    tmp_path: Path,
) -> None:
    command, fact = _command(current_specs_repository, tmp_path)
    original = fact.read_bytes()
    non_successor = FactUpdateCommand(
        boundary=command.boundary,
        fact_type_key=command.fact_type_key,
        object_id=command.object_id,
        schemas=command.schemas,
        schema=command.schema,
        expected_content_fingerprint=command.expected_content_fingerprint,
        supplied=command.supplied,
        body=None,
        event_at="2026-07-20T10:00:00+08:00",
    )

    assert apply_fact_update(non_successor).status == "event_time_not_successor"
    assert fact.read_bytes() == original
    stale = FactUpdateCommand(
        boundary=command.boundary,
        fact_type_key=command.fact_type_key,
        object_id=command.object_id,
        schemas=command.schemas,
        schema=command.schema,
        expected_content_fingerprint="0" * 64,
        supplied=command.supplied,
        body=None,
        event_at=command.event_at,
    )
    assert apply_fact_update(stale).status == "fingerprint_stale"
    assert fact.read_bytes() == original


def test_failed_exact_readback_rolls_back_only_matching_replacement(
    current_specs_repository: Path,
    tmp_path: Path,
    monkeypatch,
) -> None:
    command, fact = _command(current_specs_repository, tmp_path)
    original = fact.read_bytes()
    actual_project_read = update_application._project_read
    calls = 0

    def failing_readback(application_command: FactUpdateCommand) -> FactReadResult:
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
        return actual_project_read(application_command)

    monkeypatch.setattr(update_application, "_project_read", failing_readback)

    result = apply_fact_update(command)

    assert result.status == "readback_failed"
    assert result.rollback_result is not None
    assert result.rollback_result.outcome == "replaced"
    assert result.rollback_result.namespace_state == "committed"
    assert fact.read_bytes() == original
