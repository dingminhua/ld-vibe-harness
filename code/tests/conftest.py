from __future__ import annotations

import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

import ldvh
from ldvh.helper.rule_source import RuleSourceResult, inspect_colocated_rule_source

PROJECT_ROOT = Path(__file__).resolve().parents[2]


HELPER_EXECUTABLE = PROJECT_ROOT / "ldvh"


@pytest.fixture(scope="session")
def current_rule_source_snapshot() -> RuleSourceResult:
    """Parse the current rule source once for explicitly opted-in unit tests.

    The fixture deliberately fails when the Working Tree rule source is not
    complete.  It is not suitable for tests whose subject is source refresh,
    observation time, source identity, or source qualification.
    """

    snapshot = inspect_colocated_rule_source(Path(ldvh.__file__))
    assert snapshot.problem is None
    assert snapshot.repository is not None
    assert snapshot.operations is not None
    assert not snapshot.repository.issues
    assert not snapshot.repository.incomplete_scope
    assert not snapshot.operations.issues
    assert not snapshot.operations.incomplete_sources
    return snapshot


@pytest.fixture
def use_current_rule_source_snapshot(
    monkeypatch: pytest.MonkeyPatch,
    current_rule_source_snapshot: RuleSourceResult,
) -> None:
    """Reuse one immutable rule snapshot without caching request-local state."""

    monkeypatch.setattr(
        "ldvh.helper.service.inspect_colocated_rule_source",
        lambda _: current_rule_source_snapshot,
    )


def _assert_source_reference(reference: dict[str, Any]) -> None:
    assert {"kind", "locator"} <= set(reference) <= {"kind", "locator", "version", "observed_at", "details"}
    assert isinstance(reference["kind"], str) and reference["kind"]
    assert isinstance(reference["locator"], str) and reference["locator"]
    if "version" in reference:
        assert isinstance(reference["version"], str) and reference["version"]
    if "observed_at" in reference:
        assert isinstance(reference["observed_at"], str) and reference["observed_at"]
        parsed = datetime.fromisoformat(reference["observed_at"].replace("Z", "+00:00"))
        assert parsed.tzinfo is not None
    if "details" in reference:
        assert isinstance(reference["details"], dict)


def _assert_follow_up_item(item: dict[str, Any], *, operation: bool = False) -> None:
    expected = {"summary", "scope", "source_refs"} | ({"operation_key"} if operation else set())
    assert set(item) == expected
    assert isinstance(item["summary"], str) and item["summary"]
    assert isinstance(item["scope"], list)
    assert isinstance(item["source_refs"], list) and item["source_refs"]
    for reference in item["source_refs"]:
        _assert_source_reference(reference)
    if operation:
        assert isinstance(item["operation_key"], str) and item["operation_key"]


def assert_common_response(response: dict[str, Any]) -> None:
    assert set(response) == {
        "contract",
        "response_profile",
        "request_kind",
        "operation_key",
        "outcome",
        "summary",
        "result",
        "scope",
        "sources",
        "disclosure",
        "gaps",
        "changes",
        "verification",
        "diagnostics",
        "follow_up",
    }
    assert response["contract"] == "ldvh-helper-cli/2"
    assert response["response_profile"] in {"compact", "diagnostic"}
    assert response["request_kind"] in {"capabilities", "call"}
    assert response["outcome"] in {
        "ok",
        "no_change",
        "partial",
        "rejected",
        "unavailable",
        "invalid_request",
        "error",
    }
    assert isinstance(response["summary"], str) and response["summary"]
    assert set(response["scope"]) == {"requested", "completed", "not_completed", "governance_resolution"}
    assert isinstance(response["scope"]["requested"], list)
    assert isinstance(response["scope"]["completed"], list)
    assert isinstance(response["scope"]["not_completed"], list)
    governance_resolution = response["scope"]["governance_resolution"]
    assert governance_resolution is None or isinstance(governance_resolution, dict)
    assert isinstance(response["sources"], list)
    for reference in response["sources"]:
        _assert_source_reference(reference)
    disclosure = response["disclosure"]
    if disclosure is not None:
        assert set(disclosure) == {"requested", "parts"}
        assert disclosure["requested"] in {None, "L0", "L1", "L2", "L3", "L4"}
        assert isinstance(disclosure["parts"], list)
        for part in disclosure["parts"]:
            assert set(part) == {"level", "source_refs", "reason"}
            assert part["level"] in {"L0", "L1", "L2", "L3", "L4"}
            assert isinstance(part["source_refs"], list) and part["source_refs"]
            for reference in part["source_refs"]:
                _assert_source_reference(reference)
            assert isinstance(part["reason"], str) and part["reason"]
    assert isinstance(response["gaps"], list)
    for item in response["gaps"]:
        assert (
            {"summary", "scope", "source_refs"}
            <= set(item)
            <= {
                "summary",
                "scope",
                "source_refs",
                "code",
                "member_count",
            }
        )
        assert isinstance(item["summary"], str) and item["summary"]
        assert isinstance(item["scope"], list)
        assert isinstance(item["source_refs"], list)
        for reference in item["source_refs"]:
            _assert_source_reference(reference)
        if "code" in item:
            assert isinstance(item["code"], str) and item["code"]
        if "member_count" in item:
            assert response["response_profile"] == "compact"
            assert isinstance(item["member_count"], int) and not isinstance(item["member_count"], bool)
            assert item["member_count"] > 0
    assert isinstance(response["changes"], list)
    for item in response["changes"]:
        assert set(item) == {"summary", "status", "target", "source_refs"}
        assert isinstance(item["summary"], str) and item["summary"]
        assert isinstance(item["status"], str) and item["status"]
        assert isinstance(item["target"], (str, dict))
        assert isinstance(item["source_refs"], list)
        for reference in item["source_refs"]:
            _assert_source_reference(reference)
    assert isinstance(response["verification"], list)
    for item in response["verification"]:
        assert set(item) == {"check", "status", "scope", "evidence"}
        assert isinstance(item["check"], str) and item["check"]
        assert isinstance(item["status"], str) and item["status"]
        assert isinstance(item["scope"], list)
        assert isinstance(item["evidence"], list)
        for reference in item["evidence"]:
            _assert_source_reference(reference)
    assert isinstance(response["diagnostics"], list)
    for item in response["diagnostics"]:
        assert {"summary", "details"} <= set(item) <= {"summary", "details", "code", "source_refs"}
        assert isinstance(item["summary"], str) and item["summary"]
        assert isinstance(item["details"], dict)
        if "code" in item:
            assert isinstance(item["code"], str) and item["code"]
        if "source_refs" in item:
            assert isinstance(item["source_refs"], list)
            for reference in item["source_refs"]:
                _assert_source_reference(reference)
    assert set(response["follow_up"]) == {
        "summary",
        "required_inputs",
        "required_human_decisions",
        "resume_conditions",
        "suggested_operations",
    }
    assert response["follow_up"]["summary"]
    for field in (
        "required_inputs",
        "required_human_decisions",
        "resume_conditions",
        "suggested_operations",
    ):
        assert isinstance(response["follow_up"][field], list)
    for item in response["follow_up"]["required_inputs"]:
        _assert_follow_up_item(item)
    for item in response["follow_up"]["required_human_decisions"]:
        _assert_follow_up_item(item)
    for item in response["follow_up"]["resume_conditions"]:
        _assert_follow_up_item(item)
    for item in response["follow_up"]["suggested_operations"]:
        _assert_follow_up_item(item, operation=True)


@pytest.fixture
def current_specs_repository(tmp_path: Path) -> Path:
    """Copy the current V4 specification files into an isolated Git worktree."""

    repository = tmp_path / "repository"
    repository.mkdir()
    shutil.copytree(PROJECT_ROOT / "specs", repository / "specs")
    _git(repository, "init", "-q")
    return repository


def commit_all(repository: Path, message: str = "test fixture") -> None:
    _git(repository, "add", ".")
    _git(
        repository,
        "-c",
        "user.name=LDVH Test",
        "-c",
        "user.email=ldvh@example.invalid",
        "commit",
        "-qm",
        message,
    )


def _git(repository: Path, *arguments: str) -> None:
    subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=True,
        capture_output=True,
    )
