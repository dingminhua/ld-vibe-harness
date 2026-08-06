from __future__ import annotations

import ast
import subprocess
from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path

import pytest

from ldvh.facts import creation_application
from ldvh.facts.contracts import LAYOUTS
from ldvh.facts.creation import (
    AllocationCommitResult,
    CreationBoundary,
    allocation_lock,
    serialize_fact_object,
)
from ldvh.facts.creation_application import (
    FactCreationCommand,
    FactCreationResult,
    PreparedFactCreation,
    create_fact_object,
    create_fact_object_locked,
    prepare_fact_creation,
)
from ldvh.facts.models import FactIssue
from ldvh.facts.relations import ProjectFactIndex
from ldvh.facts.repository import FactReadResult
from ldvh.facts.schema import project_fact_schemas
from ldvh.filesystem import AtomicWriteResult
from ldvh.specs.repository import inspect_repository


def _git(project: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(project), *arguments],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _command(current_specs_repository: Path, tmp_path: Path) -> FactCreationCommand:
    project = tmp_path / "project"
    project.mkdir()
    _git(project, "init", "-q")
    common_dir = Path(_git(project, "rev-parse", "--path-format=absolute", "--git-common-dir"))
    schemas = project_fact_schemas(inspect_repository(current_specs_repository))
    return FactCreationCommand(
        boundary=CreationBoundary("sample", project, common_dir),
        fact_type_key="spark",
        schemas=schemas,
        schema=schemas["spark"],
        requested_candidate_id="spark-0001",
        supplied={
            "title": "Application boundary",
            "status": "open",
            "summary": "The application layer owns the complete creation transaction.",
            "priority": "P2",
            "change_log": [
                {
                    "signature": {"agent_id": "test-agent", "host_environment": "test"},
                    "session_id": "test-session",
                    "at": "2000-01-01T00:00:00Z",
                    "summary": "Create the test fact.",
                }
            ],
        },
        body=None,
    )


def _workcase_command(current_specs_repository: Path, tmp_path: Path) -> FactCreationCommand:
    base = _command(current_specs_repository, tmp_path)
    supplied = {
        "title": "Initial WorkCase boundary",
        "status": "open",
        "summary": "The plan is waiting for Human execution approval",
        "priority": "P2",
        "goal": "Exercise the initial WorkCase creation boundary",
        "scope": "One controlled creation",
        "execution_authorization": {
            "authorized_actions": [
                {
                    "action_id": "authorization-create-boundary",
                    "summary": "Exercise the bounded creation path.",
                    "target_scope": "Only the requested test WorkCase.",
                    "effect_scope": "One fact-object creation transaction.",
                    "risk_summary": "Reject invalid plan or relation state.",
                    "rollback_summary": "Remove only the uncommitted candidate.",
                    "rule_refs": ["specs/21"],
                },
                {
                    "action_id": "authorization-delegate-independent-review",
                    "summary": "Delegate the required independent result review.",
                    "target_scope": "Only the current test WorkCase result.",
                    "effect_scope": "Read-only Reviewer delegation.",
                    "risk_summary": "The declaration does not prove real-world independence.",
                    "rollback_summary": "Do not persist a delegation receipt.",
                    "rule_refs": ["specs/21"],
                },
                {
                    "action_id": "authorization-independent-result-review",
                    "summary": "Perform the required independent result review.",
                    "target_scope": "Only the current test WorkCase result.",
                    "effect_scope": "Read-only result review.",
                    "risk_summary": "The review remains advisory.",
                    "rollback_summary": "Record only the current review result.",
                    "rule_refs": ["specs/21"],
                },
            ],
            "quality_gates": [
                {
                    "gate_id": "independent-result-review",
                    "reviewer_mode": "independent-read-only",
                    "delegation_action_id": "authorization-delegate-independent-review",
                    "result_review_action_id": "authorization-independent-result-review",
                }
            ],
            "action_ceiling": "No unrelated fact or external write.",
            "prohibited_actions": ["publish", "push"],
            "allowed_adjustments": "Only the declared test creation.",
            "verification_and_rollback": "Validate the candidate and read back the exact carrier.",
            "out_of_bounds_handling": "Reject the candidate without writing.",
        },
        "success_criterion_definitions": [
            {"criterion_id": "criterion-01", "statement": "The initial boundary is enforced"}
        ],
        "phase": "human_plan_confirming",
        "plan_version": 1,
        "waiting_on": "Human execution approval",
        "work_items": [
            {
                "item_id": "item-01",
                "goal": "Exercise the creation boundary",
                "expected_result": "The invalid initial state is rejected",
                "status": "pending",
            }
        ],
        "creation_reviews": [
            {
                "reviewer": "independent-creation-reviewer",
                "reviewed_at": "2026-07-26T12:50:00+08:00",
                "subject_version": 1,
                "scope": "Current initial plan",
                "conclusion": "pass",
                "covered_quality_gate_ids": ["independent-result-review"],
            }
        ],
        "change_log": [
            {
                "signature": {"agent_id": "test-agent", "host_environment": "test"},
                "session_id": "test-session",
                "at": "2000-01-01T00:00:00Z",
                "summary": "Create the test WorkCase.",
            }
        ],
    }
    return FactCreationCommand(
        boundary=base.boundary,
        fact_type_key="workcase",
        schemas=base.schemas,
        schema=base.schemas["workcase"],
        requested_candidate_id="workcase-0001",
        supplied=supplied,
        body=None,
    )


def _depends_on(object_id: str) -> dict[str, object]:
    return {
        "relation_key": "depends-on",
        "target": {
            "governed_project_id": "sample",
            "fact_type_key": "workcase",
            "object_id": object_id,
        },
    }


def _write_existing_workcase(
    command: FactCreationCommand,
    object_id: str,
    *,
    depends_on: str,
) -> Path:
    fields = deepcopy(command.supplied)
    fields.update(
        {
            "object_id": object_id,
            "fact_type_key": "workcase",
            "created_at": "2026-07-26T12:00:00+08:00",
            "updated_at": "2026-07-26T12:00:00+08:00",
            "relations": [_depends_on(depends_on)],
        }
    )
    change_log = fields.get("change_log")
    if isinstance(change_log, list) and change_log and isinstance(change_log[0], dict):
        change_log[0]["at"] = fields["created_at"]
    path = command.boundary.worktree_root / LAYOUTS["workcase"].canonical_path(object_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        serialize_fact_object(LAYOUTS["workcase"], fields, None),
        encoding="utf-8",
    )
    return path


def test_application_module_has_no_helper_dependency() -> None:
    module = Path(__file__).resolve().parents[2] / "ldvh/facts/creation_application.py"
    tree = ast.parse(module.read_text(encoding="utf-8"))
    imports = {alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names} | {
        node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
    }
    assert not any(name == "ldvh.helper" or name.startswith("ldvh.helper.") for name in imports)


def test_workcase_creation_preflight_rejects_noninitial_phase_approval_and_plan_version(
    current_specs_repository: Path,
    tmp_path: Path,
) -> None:
    command = _workcase_command(current_specs_repository, tmp_path)
    command.supplied.update(
        {
            "phase": "executing",
            "execution_approval": {
                "subject_version": 1,
                "approved_at": "2026-07-26T13:00:00+08:00",
                "summary": "Claimed approval before object creation",
            },
        }
    )
    command.supplied.pop("waiting_on")

    rejected = prepare_fact_creation(command, observed_at="2026-07-26T13:00:00+08:00")
    assert isinstance(rejected, FactCreationResult)
    assert rejected.status == "candidate_rejected"
    assert any(issue.field_path == "phase" and "初始 phase" in issue.summary for issue in rejected.issues)
    assert any(issue.field_path == "execution_approval" and "禁止预置" in issue.summary for issue in rejected.issues)

    second_root = tmp_path / "second"
    second_root.mkdir()
    revised = _workcase_command(current_specs_repository, second_root)
    revised.supplied["plan_version"] = 99
    revised.supplied["creation_reviews"][0]["subject_version"] = 99
    rejected = prepare_fact_creation(revised, observed_at="2026-07-26T13:00:00+08:00")
    assert isinstance(rejected, FactCreationResult)
    assert rejected.status == "candidate_rejected"
    assert any(issue.field_path == "plan_version" and "必须是 1" in issue.summary for issue in rejected.issues)


def test_workcase_creation_preflight_rejects_non_open_status_and_nonpending_items(
    current_specs_repository: Path,
    tmp_path: Path,
) -> None:
    blocked = _workcase_command(current_specs_repository, tmp_path)
    blocked.supplied["status"] = "blocked"
    blocked.supplied["blocking_summary"] = "The responsibility cannot currently continue"

    rejected = prepare_fact_creation(blocked, observed_at="2026-07-26T13:00:00+08:00")
    assert isinstance(rejected, FactCreationResult)
    assert rejected.status == "candidate_rejected"
    assert any(issue.field_path == "status" and "必须是 open" in issue.summary for issue in rejected.issues)

    second_root = tmp_path / "second"
    second_root.mkdir()
    advancing = _workcase_command(current_specs_repository, second_root)
    advancing.supplied["work_items"][0].update(
        {
            "status": "in_progress",
            "current_summary": "Execution was claimed before creation",
            "resume_from": "Continue the claimed execution",
        }
    )

    rejected = prepare_fact_creation(advancing, observed_at="2026-07-26T13:00:00+08:00")
    assert isinstance(rejected, FactCreationResult)
    assert rejected.status == "candidate_rejected"
    assert any(
        issue.field_path == "work_items" and "全部 work item 必须是 pending" in issue.summary
        for issue in rejected.issues
    )


def test_workcase_creation_rejects_whitespace_only_text_without_writing(
    current_specs_repository: Path,
    tmp_path: Path,
) -> None:
    command = _workcase_command(current_specs_repository, tmp_path)
    command.supplied["goal"] = " \t\n "
    candidate = command.boundary.worktree_root / LAYOUTS["workcase"].canonical_path("workcase-0001")

    result = create_fact_object(command, observed_at="2026-07-26T13:00:00+08:00")

    assert result.status == "candidate_rejected"
    assert any(issue.field_path == "goal" and "空白" in issue.summary for issue in result.issues)
    assert not candidate.exists()


@pytest.mark.parametrize(
    ("mutate", "expected_path"),
    [
        (
            lambda fields: fields["execution_authorization"].pop("quality_gates"),
            "execution_authorization.quality_gates",
        ),
        (
            lambda fields: fields["execution_authorization"]["quality_gates"][0].update(
                {"reviewer_mode": "unknown"}
            ),
            "execution_authorization.quality_gates[0].reviewer_mode",
        ),
        (
            lambda fields: fields["creation_reviews"][0].update({"covered_quality_gate_ids": []}),
            "creation_reviews[0].covered_quality_gate_ids",
        ),
    ],
)
def test_workcase_creation_requires_current_quality_gate_authorization(
    current_specs_repository: Path,
    tmp_path: Path,
    mutate: object,
    expected_path: str,
) -> None:
    command = _workcase_command(current_specs_repository, tmp_path)
    mutate(command.supplied)  # type: ignore[operator]

    rejected = prepare_fact_creation(command, observed_at="2026-07-26T13:00:00+08:00")

    assert isinstance(rejected, FactCreationResult)
    assert rejected.status == "candidate_rejected"
    assert any(issue.field_path == expected_path for issue in rejected.issues)
    assert not (command.boundary.git_common_dir / "ldvh").exists()


def test_workcase_creation_rejects_a_locally_valid_target_with_a_missing_deep_dependency(
    current_specs_repository: Path,
    tmp_path: Path,
) -> None:
    command = _workcase_command(current_specs_repository, tmp_path)
    intermediate = _write_existing_workcase(
        command,
        "workcase-0002",
        depends_on="workcase-0003",
    )
    intermediate_bytes = intermediate.read_bytes()
    command.supplied["relations"] = [_depends_on("workcase-0002")]

    result = create_fact_object(command, observed_at="2026-07-26T13:00:00+08:00")

    assert result.status == "candidate_rejected"
    assert any("关系图包含缺失" in issue.summary for issue in result.issues)
    candidate = command.boundary.worktree_root / LAYOUTS["workcase"].canonical_path("workcase-0001")
    assert not candidate.exists()
    assert intermediate.read_bytes() == intermediate_bytes
    assert not (command.boundary.git_common_dir / "ldvh").exists()


def test_unrelated_invalid_workcase_chain_does_not_block_spark_creation(
    current_specs_repository: Path,
    tmp_path: Path,
) -> None:
    workcase = _workcase_command(current_specs_repository, tmp_path)
    _write_existing_workcase(
        workcase,
        "workcase-0002",
        depends_on="workcase-0003",
    )
    spark = FactCreationCommand(
        boundary=workcase.boundary,
        fact_type_key="spark",
        schemas=workcase.schemas,
        schema=workcase.schemas["spark"],
        requested_candidate_id="spark-0001",
        supplied={
            "title": "Independent Spark creation",
            "status": "open",
                "summary": "The unrelated WorkCase chain does not govern this Spark.",
                "priority": "P2",
                "change_log": [
                    {
                        "signature": {"agent_id": "test-agent", "host_environment": "test"},
                        "session_id": "test-session",
                        "at": "2000-01-01T00:00:00Z",
                        "summary": "Create the independent test Spark.",
                    }
                ],
            },
        body=None,
    )

    result = create_fact_object(spark, observed_at="2026-07-26T13:00:00+08:00")

    assert result.status == "created"
    assert result.actual_id == "spark-0001"


def test_prepared_creation_can_run_under_one_external_allocation_lock(
    current_specs_repository: Path,
    tmp_path: Path,
) -> None:
    command = _command(current_specs_repository, tmp_path)
    prepared = prepare_fact_creation(command)

    assert isinstance(prepared, PreparedFactCreation)
    assert not (command.boundary.git_common_dir / "ldvh").exists()
    with allocation_lock(command.boundary, LAYOUTS["spark"]) as counter_path:
        result = create_fact_object_locked(prepared, counter_path)

    assert result.status == "created"
    assert result.actual_id == "spark-0001"
    assert result.read is not None and result.read.check_status == "mechanically_valid"
    assert (command.boundary.worktree_root / "ldvh-base/sparks/spark-0001.yaml").is_file()


def test_public_create_rechecks_final_preflight_after_counter_commit(
    current_specs_repository: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command = _command(current_specs_repository, tmp_path)
    actual_preflight = creation_application._preflight
    observed_counters: list[tuple[str, ...]] = []

    def observing_preflight(*args, **kwargs):
        counter_root = command.boundary.git_common_dir / "ldvh/fact-id-allocators"
        observed_counters.append(
            tuple(path.read_text(encoding="ascii") for path in sorted(counter_root.glob("*.counter")))
            if counter_root.exists()
            else ()
        )
        return actual_preflight(*args, **kwargs)

    monkeypatch.setattr(creation_application, "_preflight", observing_preflight)

    result = create_fact_object(command, observed_at="2026-07-26T13:00:00+08:00")

    assert result.status == "created"
    assert observed_counters == [(), ("1\n",)]


def test_created_result_survives_coordination_release_failure(
    current_specs_repository: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command = _command(current_specs_repository, tmp_path)
    actual_lock = creation_application.allocation_lock

    @contextmanager
    def release_fails(boundary: CreationBoundary, layout):
        with actual_lock(boundary, layout) as counter_path:
            yield counter_path
        raise OSError("simulated lock release failure")

    monkeypatch.setattr(creation_application, "allocation_lock", release_fails)

    result = create_fact_object(command, observed_at="2026-07-26T13:00:00+08:00")

    assert result.status == "created"
    assert result.coordination_release_uncertain is True
    assert result.actual_id == "spark-0001"
    assert result.read is not None and result.read.check_status == "mechanically_valid"
    assert (command.boundary.worktree_root / "ldvh-base/sparks/spark-0001.yaml").is_file()
    counters = tuple((command.boundary.git_common_dir / "ldvh/fact-id-allocators").glob("*.counter"))
    assert len(counters) == 1
    assert counters[0].read_text(encoding="ascii") == "1\n"


def test_non_success_creation_result_survives_coordination_release_failure(
    current_specs_repository: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command = _command(current_specs_repository, tmp_path)

    @contextmanager
    def release_fails(*_args, **_kwargs):
        yield Path("unused-counter")
        raise OSError("simulated lock release failure")

    expected = FactCreationResult(
        "final_rejected",
        issues=(FactIssue("schema", "forced final rejection"),),
        actual_id="spark-0001",
        allocation_consumed=True,
        allocation_status="committed",
        allocation_result=AllocationCommitResult("committed", "spark-0001"),
    )
    monkeypatch.setattr(creation_application, "allocation_lock", release_fails)
    monkeypatch.setattr(creation_application, "create_fact_object_locked", lambda *_args: expected)

    result = create_fact_object(command, observed_at="2026-07-26T13:00:00+08:00")

    assert result.status == "final_rejected"
    assert result.issues == expected.issues
    assert result.actual_id == "spark-0001"
    assert result.allocation_consumed is True
    assert result.coordination_release_uncertain is True


def test_prepared_creation_defensively_freezes_nested_supplied_values(
    current_specs_repository: Path,
    tmp_path: Path,
) -> None:
    command = _command(current_specs_repository, tmp_path)
    command.supplied["urls"] = [
        {"ref": "https://example.invalid/original", "title": "Original", "summary": "Test material."}
    ]
    prepared = prepare_fact_creation(command)
    assert isinstance(prepared, PreparedFactCreation)

    command.supplied["title"] = "mutated"
    command.supplied["urls"][0]["ref"] = "https://example.invalid/mutated"
    with allocation_lock(command.boundary, LAYOUTS["spark"]) as counter_path:
        result = create_fact_object_locked(prepared, counter_path)

    assert result.status == "created"
    assert result.read is not None and result.read.fields is not None
    assert result.read.fields["title"] == "Application boundary"
    assert result.read.fields["urls"][0]["ref"] == "https://example.invalid/original"


def test_caller_supplied_observation_time_binds_both_managed_timestamps(
    current_specs_repository: Path,
    tmp_path: Path,
) -> None:
    command = _command(current_specs_repository, tmp_path)
    observed_at = "2026-07-15T16:00:00+08:00"

    prepared = prepare_fact_creation(command, observed_at=observed_at)

    assert isinstance(prepared, PreparedFactCreation)
    assert prepared.observed_at == observed_at
    with allocation_lock(command.boundary, LAYOUTS["spark"]) as counter_path:
        result = create_fact_object_locked(prepared, counter_path)
    assert result.status == "created"
    assert result.read is not None and result.read.fields is not None
    assert result.read.fields["created_at"] == observed_at
    assert result.read.fields["updated_at"] == observed_at


def test_candidate_rejection_has_no_allocator_or_fact_side_effect(
    current_specs_repository: Path,
    tmp_path: Path,
) -> None:
    command = _command(current_specs_repository, tmp_path)
    command.supplied.pop("title")

    result = prepare_fact_creation(command)

    assert isinstance(result, FactCreationResult)
    assert result.status == "candidate_rejected"
    assert not (command.boundary.git_common_dir / "ldvh").exists()
    assert not (command.boundary.worktree_root / "facts").exists()


def test_missing_stabilized_candidate_result_is_reported_as_a_check_gap(
    current_specs_repository: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command = _command(current_specs_repository, tmp_path)

    def omit_candidate(
        index: ProjectFactIndex,
        seed_keys: object,
    ) -> None:
        del seed_keys
        index.cache.clear()

    monkeypatch.setattr(creation_application, "stabilize_project_index", omit_candidate)

    result = prepare_fact_creation(command, observed_at="2026-07-26T13:00:00+08:00")

    assert isinstance(result, FactCreationResult)
    assert result.status == "candidate_unavailable"
    assert result.issues == (FactIssue("reference", "项目级关系检查未返回当前候选的稳定检查结果"),)


def test_durability_rejection_precedes_allocation_lock(
    current_specs_repository: Path,
    tmp_path: Path,
    monkeypatch,
) -> None:
    command = _command(current_specs_repository, tmp_path)
    monkeypatch.setattr("ldvh.facts.creation_application.native_atomic_fact_writes_supported", lambda: False)

    result = prepare_fact_creation(command)

    assert isinstance(result, FactCreationResult)
    assert result.status == "durability_unavailable"
    assert not (command.boundary.git_common_dir / "ldvh").exists()
    assert not (command.boundary.worktree_root / "facts").exists()


def test_locked_creation_stops_after_one_known_target_conflict(
    current_specs_repository: Path,
    tmp_path: Path,
    monkeypatch,
) -> None:
    command = _command(current_specs_repository, tmp_path)
    prepared = prepare_fact_creation(command)
    assert isinstance(prepared, PreparedFactCreation)
    target_attempts = 0

    def conflict_once(*_args, **_kwargs) -> AtomicWriteResult:
        nonlocal target_attempts
        target_attempts += 1
        return AtomicWriteResult.not_committed("conflict")

    monkeypatch.setattr(
        "ldvh.facts.creation_application.atomic_create_text",
        conflict_once,
    )

    with allocation_lock(command.boundary, LAYOUTS["spark"]) as counter_path:
        result = create_fact_object_locked(prepared, counter_path)

    assert result.status == "creation_conflict"
    assert result.allocation_consumed is True
    assert result.actual_id == "spark-0001"
    assert result.allocation_status == "committed"
    assert result.allocation_result is not None
    assert result.allocation_result.status == "committed"
    assert result.residual_readback is not None
    assert result.residual_readback.check_status == "not_found"
    assert target_attempts == 1
    counters = tuple((command.boundary.git_common_dir / "ldvh/fact-id-allocators").glob("*.counter"))
    assert len(counters) == 1
    assert counters[0].read_text(encoding="ascii") == "1\n"
    assert not (command.boundary.worktree_root / "facts").exists()


@pytest.mark.parametrize(
    ("counter_status", "expected_status"),
    [("stale", "allocation_stale"), ("unavailable", "allocation_unavailable")],
)
def test_pre_atomic_counter_recheck_failure_does_not_form_an_attempted_identity(
    current_specs_repository: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    counter_status: str,
    expected_status: str,
) -> None:
    command = _command(current_specs_repository, tmp_path)
    target_create_called = False

    def pre_atomic_failure(*_args, **_kwargs) -> AllocationCommitResult:
        return AllocationCommitResult(counter_status, None)

    def forbidden_target_create(*_args, **_kwargs) -> AtomicWriteResult:
        nonlocal target_create_called
        target_create_called = True
        raise AssertionError("target creation must not start before a counter atomic advance")

    monkeypatch.setattr(creation_application, "commit_object_id_locked", pre_atomic_failure)
    monkeypatch.setattr(creation_application, "atomic_create_text", forbidden_target_create)

    result = create_fact_object(command, observed_at="2026-07-26T13:00:00+08:00")

    assert result.status == expected_status
    assert result.actual_id is None
    assert result.allocation_consumed is False
    assert result.allocation_result == AllocationCommitResult(counter_status, None)
    assert result.creation_result is None
    assert target_create_called is False


def test_allocator_commit_uncertainty_preserves_attempted_identity_without_starting_target_create(
    current_specs_repository: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command = _command(current_specs_repository, tmp_path)
    counter_write = AtomicWriteResult.uncertain()
    expected_allocation = AllocationCommitResult("uncertain", None, counter_write)
    target_create_called = False

    def uncertain_allocation(*_args, **_kwargs) -> AllocationCommitResult:
        return expected_allocation

    def forbidden_target_create(*_args, **_kwargs) -> AtomicWriteResult:
        nonlocal target_create_called
        target_create_called = True
        raise AssertionError("target creation must not start while allocator state is uncertain")

    monkeypatch.setattr(creation_application, "commit_object_id_locked", uncertain_allocation)
    monkeypatch.setattr(creation_application, "atomic_create_text", forbidden_target_create)

    result = create_fact_object(command, observed_at="2026-07-26T13:00:00+08:00")

    assert result.status == "allocation_unavailable"
    assert result.actual_id == "spark-0001"
    assert result.allocation_status == "uncertain"
    assert result.allocation_consumed is None
    assert result.allocation_result is expected_allocation
    assert result.creation_result is None
    assert result.residual_readback is not None
    assert result.residual_readback.check_status == "not_found"
    assert target_create_called is False
    assert not (command.boundary.worktree_root / "ldvh-base/sparks/spark-0001.yaml").exists()


def test_target_namespace_uncertainty_preserves_allocator_and_fresh_target_residual(
    current_specs_repository: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command = _command(current_specs_repository, tmp_path)

    def uncertain_target_create(root: Path, layout, object_id: str, text: str) -> AtomicWriteResult:
        target = root / layout.canonical_path(object_id)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        return AtomicWriteResult.uncertain()

    monkeypatch.setattr(creation_application, "atomic_create_text", uncertain_target_create)

    result = create_fact_object(command, observed_at="2026-07-26T13:00:00+08:00")

    assert result.status == "creation_unavailable"
    assert result.actual_id == "spark-0001"
    assert result.allocation_consumed is True
    assert result.allocation_status == "committed"
    assert result.allocation_result is not None
    assert result.allocation_result.status == "committed"
    assert result.creation_result is not None
    assert result.creation_result.namespace_state == "uncertain"
    assert result.residual_readback is not None
    assert result.residual_readback.check_status == "mechanically_valid"
    assert result.residual_readback.raw_text == result.actual_text


def test_target_known_noncommit_preserves_consumed_allocator_and_fresh_not_found_residual(
    current_specs_repository: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command = _command(current_specs_repository, tmp_path)
    monkeypatch.setattr(
        creation_application,
        "atomic_create_text",
        lambda *_args, **_kwargs: AtomicWriteResult.not_committed("unavailable"),
    )

    result = create_fact_object(command, observed_at="2026-07-26T13:00:00+08:00")

    assert result.status == "creation_unavailable"
    assert result.actual_id == "spark-0001"
    assert result.allocation_consumed is True
    assert result.allocation_result is not None
    assert result.allocation_result.status == "committed"
    assert result.creation_result is not None
    assert result.creation_result.namespace_state == "not_committed"
    assert result.residual_readback is not None
    assert result.residual_readback.check_status == "not_found"


def test_failed_creation_rollback_fresh_reads_the_actual_external_residual(
    current_specs_repository: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command = _command(current_specs_repository, tmp_path)
    actual_project_read = creation_application._project_read
    actual_lock = creation_application.allocation_lock
    read_calls = 0

    @contextmanager
    def release_fails(boundary: CreationBoundary, layout):
        with actual_lock(boundary, layout) as counter_path:
            yield counter_path
        raise OSError("simulated lock release failure")

    def failing_readback(application_command: FactCreationCommand, object_id: str) -> FactReadResult:
        nonlocal read_calls
        read_calls += 1
        if read_calls == 1:
            return FactReadResult(
                "ldvh-base/sparks/spark-0001.yaml",
                "yaml",
                "invalid",
                None,
                None,
                (FactIssue("schema", "simulated write-back failure"),),
            )
        return actual_project_read(application_command, object_id)

    def conflicting_rollback(root: Path, layout, object_id: str, expected_text: str) -> AtomicWriteResult:
        external_text = expected_text.replace("Application boundary", "External occupant")
        (root / layout.canonical_path(object_id)).write_text(external_text, encoding="utf-8")
        return AtomicWriteResult.not_committed("conflict")

    monkeypatch.setattr(creation_application, "_project_read", failing_readback)
    monkeypatch.setattr(creation_application, "rollback_created_text", conflicting_rollback)
    monkeypatch.setattr(creation_application, "allocation_lock", release_fails)

    result = create_fact_object(command, observed_at="2026-07-26T13:00:00+08:00")

    assert result.status == "readback_failed"
    assert result.coordination_release_uncertain is True
    assert result.allocation_consumed is True
    assert result.rollback_result is not None
    assert result.rollback_result.outcome == "conflict"
    assert result.residual_readback is not None
    assert result.residual_readback.check_status == "mechanically_valid"
    assert result.residual_readback.fields is not None
    assert result.residual_readback.fields["title"] == "External occupant"
    assert result.residual_readback.raw_text != result.actual_text


@pytest.mark.parametrize(
    ("residual_kind", "expected_status"),
    [
        ("created-bytes", "mechanically_valid"),
        ("invalid", "invalid"),
        ("not-found", "not_found"),
        ("unavailable", "unavailable"),
    ],
)
def test_failed_creation_rollback_core_preserves_each_actual_residual_class(
    current_specs_repository: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    residual_kind: str,
    expected_status: str,
) -> None:
    command = _command(current_specs_repository, tmp_path)
    actual_project_read = creation_application._project_read
    read_calls = 0

    def failing_then_fresh_read(
        application_command: FactCreationCommand,
        object_id: str,
    ) -> FactReadResult:
        nonlocal read_calls
        read_calls += 1
        if read_calls == 1:
            return FactReadResult(
                "ldvh-base/sparks/spark-0001.yaml",
                "yaml",
                "invalid",
                None,
                None,
                (FactIssue("schema", "simulated write-back failure"),),
            )
        if residual_kind == "unavailable":
            return FactReadResult(
                "ldvh-base/sparks/spark-0001.yaml",
                "yaml",
                "unavailable",
                None,
                None,
                (FactIssue("location", "simulated fresh-read failure"),),
            )
        return actual_project_read(application_command, object_id)

    def noncommitted_rollback(
        root: Path,
        layout,
        object_id: str,
        _expected_text: str,
    ) -> AtomicWriteResult:
        target = root / layout.canonical_path(object_id)
        if residual_kind == "invalid":
            target.write_text("not: [valid\n", encoding="utf-8")
        elif residual_kind == "not-found":
            target.unlink()
        return (
            AtomicWriteResult.uncertain()
            if residual_kind == "unavailable"
            else AtomicWriteResult.not_committed("conflict")
        )

    monkeypatch.setattr(creation_application, "_project_read", failing_then_fresh_read)
    monkeypatch.setattr(creation_application, "rollback_created_text", noncommitted_rollback)

    result = create_fact_object(command, observed_at="2026-07-26T13:00:00+08:00")

    assert result.status == "readback_failed"
    assert result.residual_readback is not None
    assert result.residual_readback.check_status == expected_status
    if residual_kind == "created-bytes":
        assert result.residual_readback.raw_text == result.actual_text
    elif residual_kind == "invalid":
        assert result.residual_readback.raw_text == "not: [valid\n"
    elif residual_kind == "not-found":
        assert result.residual_readback.raw_text is None
    else:
        assert result.residual_readback.issues[0].summary == "simulated fresh-read failure"
