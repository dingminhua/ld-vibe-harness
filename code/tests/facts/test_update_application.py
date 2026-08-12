from __future__ import annotations

import ast
import subprocess
from collections.abc import Mapping
from contextlib import contextmanager
from pathlib import Path

import pytest

from ldvh.facts import update_application
from ldvh.facts.creation import CreationBoundary
from ldvh.facts.models import FactIssue
from ldvh.facts.repository import FactReadResult
from ldvh.facts.schema import FactSchema
from ldvh.facts.update_application import FactUpdateCommand, apply_fact_update
from ldvh.filesystem import AtomicWriteResult
from ldvh.time import canonical_utc_timestamp


def _git(project: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(project), *arguments],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _command(current_fact_schemas: Mapping[str, FactSchema], tmp_path: Path) -> tuple[FactUpdateCommand, Path]:
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
change_log:
  - signature:
      agent_id: test-agent
      host_environment: test
    session_id: test-session
    at: 2026-07-20T09:00:00+08:00
    summary: Create test fact
""",
        encoding="utf-8",
    )
    schemas = current_fact_schemas
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
    supplied["change_log"] = [
        *supplied["change_log"],
        {
            "signature": {"agent_id": "test-agent", "host_environment": "test"},
            "session_id": "test-session",
            "at": "2000-01-01T00:00:00Z",
            "summary": "Update test fact",
        },
    ]
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


def test_generic_application_hard_rejects_workcase(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
) -> None:
    generic, _fact = _command(current_fact_schemas, tmp_path)
    command = FactUpdateCommand(
        boundary=generic.boundary,
        fact_type_key="workcase",
        object_id="workcase-0001",
        schemas=generic.schemas,
        schema=generic.schemas["workcase"],
        expected_content_fingerprint="0" * 64,
        supplied={},
        body=None,
        event_at=generic.event_at,
    )

    result = apply_fact_update(command)

    assert result.status == "invalid_request"
    assert any("不接受 WorkCase" in issue.summary for issue in result.issues)


def test_application_binds_managed_timestamp_and_verifies_exact_readback(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
) -> None:
    command, fact = _command(current_fact_schemas, tmp_path)

    result = apply_fact_update(command)

    assert result.status == "updated"
    assert result.readback is not None and result.readback.fields is not None
    assert result.readback.fields["updated_at"] == canonical_utc_timestamp(command.event_at)
    assert result.readback.fields["summary"] == "After update"
    assert result.readback.raw_text == result.candidate_text
    assert fact.read_text(encoding="utf-8") == result.candidate_text


def test_committed_generic_update_result_survives_coordination_release_failure(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
    monkeypatch,
) -> None:
    command, fact = _command(current_fact_schemas, tmp_path)

    @contextmanager
    def release_fails(*_args, **_kwargs):
        yield Path("unused-lock-counter")
        raise OSError("simulated lock release failure")

    monkeypatch.setattr(update_application, "allocation_lock", release_fails)

    result = apply_fact_update(command)

    assert result.status == "updated"
    assert result.coordination_release_uncertain is True
    assert result.replacement_result is not None
    assert result.replacement_result.namespace_state == "committed"
    assert result.readback is not None
    assert result.readback.check_status == "mechanically_valid"
    assert result.readback.raw_text == result.candidate_text
    assert fact.read_text(encoding="utf-8") == result.candidate_text


def test_rejected_generic_update_result_survives_coordination_release_failure(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command, fact = _command(current_fact_schemas, tmp_path)
    original = fact.read_bytes()

    @contextmanager
    def release_fails(*_args, **_kwargs):
        yield Path("unused-lock-counter")
        raise OSError("simulated lock release failure")

    expected = update_application.FactUpdateResult(
        "candidate_rejected",
        command.event_at,
        issues=(FactIssue("schema", "forced candidate rejection"),),
    )
    monkeypatch.setattr(update_application, "allocation_lock", release_fails)
    monkeypatch.setattr(update_application, "apply_fact_update_locked", lambda *_args: expected)

    result = apply_fact_update(command)

    assert result.status == "candidate_rejected"
    assert result.issues == expected.issues
    assert result.coordination_release_uncertain is True
    assert fact.read_bytes() == original


def test_known_uncommitted_generic_replacement_has_zero_source_writes(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
    monkeypatch,
) -> None:
    command, fact = _command(current_fact_schemas, tmp_path)
    original = fact.read_bytes()
    monkeypatch.setattr(
        update_application,
        "atomic_replace_text_if_unchanged",
        lambda *_args, **_kwargs: AtomicWriteResult.not_committed("unavailable"),
    )

    result = apply_fact_update(command)

    assert result.status == "replacement_unavailable"
    assert result.replacement_result is not None
    assert result.replacement_result.namespace_state == "not_committed"
    assert result.readback is None
    assert result.residual_readback is None
    assert fact.read_bytes() == original


def test_no_change_does_not_require_successor_or_rewrite(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command, fact = _command(current_fact_schemas, tmp_path)
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
    actual_lock = update_application.allocation_lock

    @contextmanager
    def release_fails(boundary: CreationBoundary, layout):
        with actual_lock(boundary, layout) as counter_path:
            yield counter_path
        raise OSError("simulated lock release failure")

    monkeypatch.setattr(update_application, "allocation_lock", release_fails)

    result = apply_fact_update(no_change)

    assert result.status == "no_change"
    assert result.coordination_release_uncertain is True
    assert fact.read_bytes() == original
    assert fact.stat().st_ino == inode


def test_open_spark_can_enter_implemented_without_a_routed_to_target(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
) -> None:
    command, _fact = _command(current_fact_schemas, tmp_path)
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


def test_historical_routed_spark_cannot_be_repaired_or_migrated_by_generic_update(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
) -> None:
    command, fact = _command(current_fact_schemas, tmp_path)
    fact.write_text(
        """object_id: spark-0001
fact_type_key: spark
title: Application update
created_at: 2026-07-20T09:00:00+08:00
updated_at: 2026-07-20T10:00:00+08:00
status: routed
summary: Before update
disposition_summary: Incorrectly recorded as routed without a fact target.
change_log:
  - signature:
      agent_id: test-agent
      host_environment: test
    session_id: test-session
    at: 2026-07-20T09:00:00+08:00
    summary: Create test fact
""",
        encoding="utf-8",
    )
    original = fact.read_bytes()
    current = update_application._project_read(command)
    assert current.check_status in {"invalid", "mechanically_valid"}
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
    supplied["change_log"] = [
        *supplied["change_log"],
        {
            "signature": {"agent_id": "test-agent", "host_environment": "test"},
            "session_id": "test-session",
            "at": "2000-01-01T00:00:00Z",
            "summary": "Repair test fact",
        },
    ]

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

    assert result.status == "invalid_request"
    assert any("仅允许只读审计" in issue.summary for issue in result.issues)
    assert fact.read_bytes() == original


def test_non_successor_event_time_and_stale_fingerprint_have_zero_writes(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
) -> None:
    command, fact = _command(current_fact_schemas, tmp_path)
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


@pytest.mark.parametrize(
    ("current_time", "event_time", "expected_status"),
    [
        (
            "2026-07-20T10:00:00.1234567+08:00",
            "2026-07-20T10:00:00.1234568+08:00",
            "updated",
        ),
        (
            "2026-07-20T10:00:00.1234568+08:00",
            "2026-07-20T10:00:00.1234567+08:00",
            "event_time_not_successor",
        ),
        (
            "2026-07-20T10:00:00+08:00",
            "2026-07-20T11:00:00-00:00",
            "event_time_not_successor",
        ),
    ],
)
def test_generic_update_compares_fractional_seconds_beyond_microseconds_without_loss(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
    current_time: str,
    event_time: str,
    expected_status: str,
) -> None:
    command, fact = _command(current_fact_schemas, tmp_path)
    fact.write_text(
        fact.read_text(encoding="utf-8").replace(
            "updated_at: 2026-07-20T10:00:00+08:00",
            f"updated_at: {current_time}",
        ),
        encoding="utf-8",
    )
    current = update_application._project_read(command)
    assert current.fields is not None and current.content_fingerprint is not None
    supplied = {key: value for key, value in current.fields.items() if key not in update_application.MANAGED_FIELDS}
    supplied["summary"] = "After exact-precision update"
    supplied["change_log"] = [
        *supplied["change_log"],
        {
            "signature": {"agent_id": "test-agent", "host_environment": "test"},
            "session_id": "test-session",
            "at": "2000-01-01T00:00:00Z",
            "summary": "Update test fact",
        },
    ]
    exact_command = FactUpdateCommand(
        boundary=command.boundary,
        fact_type_key=command.fact_type_key,
        object_id=command.object_id,
        schemas=command.schemas,
        schema=command.schema,
        expected_content_fingerprint=current.content_fingerprint,
        supplied=supplied,
        body=None,
        event_at=event_time,
    )
    original = fact.read_bytes()

    result = apply_fact_update(exact_command)

    assert result.status == expected_status
    if expected_status == "updated":
        assert result.readback is not None and result.readback.fields is not None
        assert result.readback.fields["updated_at"] == canonical_utc_timestamp(event_time)
    else:
        assert fact.read_bytes() == original


def test_failed_exact_readback_rolls_back_only_matching_replacement(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
    monkeypatch,
) -> None:
    command, fact = _command(current_fact_schemas, tmp_path)
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


def test_failed_generic_rollback_fresh_reads_the_actual_external_residual(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
    monkeypatch,
) -> None:
    command, fact = _command(current_fact_schemas, tmp_path)
    actual_project_read = update_application._project_read
    actual_replace = update_application.atomic_replace_text_if_unchanged
    actual_lock = update_application.allocation_lock
    read_calls = 0
    replace_calls = 0
    candidate_text = ""

    @contextmanager
    def release_fails(boundary: CreationBoundary, layout):
        with actual_lock(boundary, layout) as counter_path:
            yield counter_path
        raise OSError("simulated lock release failure")

    def failing_readback(application_command: FactUpdateCommand) -> FactReadResult:
        nonlocal read_calls
        read_calls += 1
        if read_calls == 2:
            return FactReadResult(
                "ldvh-base/sparks/spark-0001.yaml",
                "yaml",
                "invalid",
                None,
                None,
                (FactIssue("schema", "simulated write-back failure"),),
            )
        return actual_project_read(application_command)

    def conflicting_rollback(*args, **kwargs) -> AtomicWriteResult:
        nonlocal replace_calls, candidate_text
        replace_calls += 1
        if replace_calls == 1:
            candidate_text = args[4]
            return actual_replace(*args, **kwargs)
        fact.write_text(
            candidate_text.replace("After update", "External update after failed readback"),
            encoding="utf-8",
        )
        return AtomicWriteResult.not_committed("conflict")

    monkeypatch.setattr(update_application, "_project_read", failing_readback)
    monkeypatch.setattr(update_application, "atomic_replace_text_if_unchanged", conflicting_rollback)
    monkeypatch.setattr(update_application, "allocation_lock", release_fails)

    result = apply_fact_update(command)

    assert result.status == "readback_failed"
    assert result.coordination_release_uncertain is True
    assert result.rollback_result is not None
    assert result.rollback_result.outcome == "conflict"
    assert result.residual_readback is not None
    assert result.residual_readback.check_status == "mechanically_valid"
    assert result.residual_readback.fields is not None
    assert result.residual_readback.fields["summary"] == "External update after failed readback"
    assert result.residual_readback.raw_text not in {result.current.raw_text, result.candidate_text}
    assert "External update after failed readback" in fact.read_text(encoding="utf-8")


def _legacy_command(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
    *,
    commit: bool,
    include_log: bool = False,
    event_at: str = "2026-07-20T11:00:00+08:00",
) -> tuple[FactUpdateCommand, Path]:
    """Build a Spark command whose current before lacks ``change_log``.

    ``include_log`` writes a committed object WITH a log first and then rewrites
    the Working Tree without one, simulating a deleted committed history.
    """
    project = tmp_path / "project"
    project.mkdir()
    _git(project, "init", "-q")
    common_dir = Path(_git(project, "rev-parse", "--path-format=absolute", "--git-common-dir"))
    fact = project / "ldvh-base/sparks/spark-0001.yaml"
    fact.parent.mkdir(parents=True)
    clean_body = """object_id: spark-0001
fact_type_key: spark
title: Legacy object
created_at: 2026-07-20T09:00:00+08:00
updated_at: 2026-07-20T10:00:00+08:00
status: open
summary: Before first real update
priority: P2
"""
    logged_body = clean_body + """change_log:
  - signature:
      agent_id: test-agent
      host_environment: test
    session_id: test-session
    at: 2026-07-20T09:00:00+08:00
    summary: Create test fact
"""
    fact.write_text(logged_body if include_log else clean_body, encoding="utf-8")
    schemas = current_fact_schemas
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
            event_at=event_at,
        )
    )
    assert current.fields is not None and current.content_fingerprint is not None
    if commit:
        _git(project, "add", "-A")
        _git(project, "-c", "user.name=test", "-c", "user.email=test@example.com", "commit", "-q", "-m", "seed")
    if include_log:
        # Simulate a Working Tree that deleted the committed history while HEAD
        # still carries it.
        fact.write_text(clean_body, encoding="utf-8")
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
                event_at=event_at,
            )
        )
        assert current.fields is not None and current.content_fingerprint is not None
    supplied = {key: value for key, value in current.fields.items() if key not in update_application.MANAGED_FIELDS}
    supplied["summary"] = "First real update"
    supplied["change_log"] = [
        {
            "signature": {
                "product_name": "pytest",
                "model_name": "test-model",
                "agent_runtime_name": "pytest-runtime",
            },
            "at": "2000-01-01T00:00:00Z",
            "summary": "首次真实更新建立流水；此前历史未恢复。",
        }
    ]
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
            event_at=event_at,
        ),
        fact,
    )


def test_first_log_update_requires_committed_head_without_log(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
) -> None:
    command, fact = _legacy_command(current_fact_schemas, tmp_path, commit=False)
    original = fact.read_bytes()

    result = apply_fact_update(command)

    assert result.status == "candidate_rejected"
    assert any(issue.field_path == "change_log" and "HEAD" in issue.summary for issue in result.issues)
    assert fact.read_bytes() == original


def test_first_log_update_succeeds_when_head_and_wt_lack_log(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
) -> None:
    command, fact = _legacy_command(current_fact_schemas, tmp_path, commit=True)

    result = apply_fact_update(command)

    assert result.status == "updated"
    assert result.readback is not None and result.readback.fields is not None
    fields = result.readback.fields
    assert fields["summary"] == "First real update"
    assert fields["status"] == "open"
    assert fields["created_at"] == "2026-07-20T09:00:00+08:00"
    change_log = fields["change_log"]
    assert len(change_log) == 1
    entry = change_log[0]
    assert set(entry["signature"]) == {"product_name", "model_name", "agent_runtime_name"}
    assert "session_id" not in entry
    assert entry["at"] == fields["updated_at"] == canonical_utc_timestamp(command.event_at)
    assert fact.read_text(encoding="utf-8") == result.candidate_text


def test_first_log_update_rejects_deleted_committed_history(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
) -> None:
    command, fact = _legacy_command(current_fact_schemas, tmp_path, commit=True, include_log=True)
    original = fact.read_bytes()

    result = apply_fact_update(command)

    assert result.status == "candidate_rejected"
    assert any(issue.field_path == "change_log" and "HEAD" in issue.summary for issue in result.issues)
    assert fact.read_bytes() == original


def test_study_first_log_update_preserves_body_and_creates_single_entry(
    current_fact_schemas: Mapping[str, FactSchema],
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    _git(project, "init", "-q")
    common_dir = Path(_git(project, "rev-parse", "--path-format=absolute", "--git-common-dir"))
    fact = project / "ldvh-base/studies/study-0001.md"
    fact.parent.mkdir(parents=True)
    frontmatter = {
        "object_id": "study-0001",
        "fact_type_key": "study",
        "title": "Legacy study",
        "status": "active",
        "report_kind": "technical_assessment",
        "created_at": "2026-07-20T09:00:00+08:00",
        "updated_at": "2026-07-20T10:00:00+08:00",
        "research_question": "How to keep checking results?",
        "abstract": "A legacy assessment without a change log.",
        "research_intent": "Record the initial assessment.",
        "recommendation_summary": "Check explicitly and keep the Git gate.",
        "input_refs": [
            {
                "kind": "specification",
                "locator": "specs/00-理念与构成.md §8.2",
            }
        ],
    }
    body = (
        "## 研究问题\n\n如何持续检查结果。\n\n"
        "## 输入与边界\n\n显式检查。\n\n"
        "## 关键发现\n\n发现保留。\n\n"
        "## 建议\n\n建议保留。\n\n"
        "## 后续分流\n\n分流保留。\n"
    )
    from ldvh.facts.carriers.study_markdown import parse_study_markdown
    from ldvh.facts.contracts import LAYOUTS as _LAYOUTS
    from ldvh.facts.creation import serialize_fact_object

    fact.write_text(serialize_fact_object(_LAYOUTS["study"], frontmatter, body), encoding="utf-8")
    _git(project, "add", "-A")
    _git(project, "-c", "user.name=test", "-c", "user.email=test@example.com", "commit", "-q", "-m", "seed")
    schemas = current_fact_schemas
    current = update_application._project_read(
        FactUpdateCommand(
            boundary=CreationBoundary("sample", project, common_dir),
            fact_type_key="study",
            object_id="study-0001",
            schemas=schemas,
            schema=schemas["study"],
            expected_content_fingerprint="0" * 64,
            supplied={},
            body=None,
            event_at="2026-07-20T11:00:00+08:00",
        )
    )
    assert current.fields is not None and current.content_fingerprint is not None
    assert current.body == "\n" + body
    supplied = {
        key: value for key, value in current.fields.items() if key not in update_application.MANAGED_FIELDS
    }
    supplied["title"] = "首次真实更新后的标题"
    supplied["change_log"] = [
        {
            "signature": {
                "product_name": "pytest",
                "model_name": "test-model",
                "agent_runtime_name": "pytest-runtime",
            },
            "at": "2000-01-01T00:00:00Z",
            "summary": "首次真实更新建立流水；此前历史未恢复。",
        }
    ]

    result = apply_fact_update(
        FactUpdateCommand(
            boundary=CreationBoundary("sample", project, common_dir),
            fact_type_key="study",
            object_id="study-0001",
            schemas=schemas,
            schema=schemas["study"],
            expected_content_fingerprint=current.content_fingerprint,
            supplied=supplied,
            body=body,
            event_at="2026-07-20T11:00:00+08:00",
        )
    )

    assert result.status == "updated"
    assert result.readback is not None and result.readback.fields is not None
    assert result.readback.body == "\n" + body
    fields = result.readback.fields
    assert fields["title"] == "首次真实更新后的标题"
    change_log = fields["change_log"]
    assert len(change_log) == 1
    entry = change_log[0]
    assert set(entry["signature"]) == {"product_name", "model_name", "agent_runtime_name"}
    assert entry["at"] == fields["updated_at"]
    assert parse_study_markdown(fact.read_text(encoding="utf-8")).fields is not None
