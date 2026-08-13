from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest

from ldvh import filesystem
from ldvh.filesystem import (
    AtomicWriteResult,
    atomic_create_relative,
    atomic_replace_relative_if_equal,
    native_atomic_fact_writes_supported,
    remove_relative_if_equal,
)

# POSIX-specific directory fsync error injection and mode tests.
_POSIX_ONLY = pytest.mark.skipif(os.name == "nt", reason="POSIX-specific fsync behaviour")

def test_atomic_write_results_only_allow_valid_commit_shapes() -> None:
    with pytest.raises(TypeError):
        AtomicWriteResult("created", "not_committed")  # type: ignore[call-arg]
    with pytest.raises(ValueError, match="committed writes require"):
        AtomicWriteResult.committed("conflict")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="not-committed writes require"):
        AtomicWriteResult.not_committed("created")  # type: ignore[arg-type]

    committed = AtomicWriteResult.committed("created")
    not_committed = AtomicWriteResult.not_committed("conflict")
    uncertain = AtomicWriteResult.uncertain()

    assert (committed.outcome, committed.namespace_state) == ("created", "committed")
    assert (not_committed.outcome, not_committed.namespace_state) == ("conflict", "not_committed")
    assert (uncertain.outcome, uncertain.namespace_state) == ("unavailable", "uncertain")

def test_native_atomic_fact_write_support_describes_backend_availability() -> None:
    assert native_atomic_fact_writes_supported("posix") is True
    assert native_atomic_fact_writes_supported("nt") is True
    assert native_atomic_fact_writes_supported("unknown") is False

def test_allow_file_only_override_does_not_bypass_platform_gate_on_unknown_platform(tmp_path: Path) -> None:
    """allow_file_only=True must not enable writes on platforms other than nt."""
    result = atomic_create_relative(
        tmp_path,
        "ldvh-base/sparks/spark-0001.yaml",
        b"first\n",
        platform_name="java",
        allow_file_only=True,
    )
    assert result.outcome == "unavailable"
    assert result.namespace_state == "not_committed"

@_POSIX_ONLY
def test_posix_create_publishes_exact_bytes(tmp_path: Path) -> None:
    result = atomic_create_relative(tmp_path, "ldvh-base/sparks/spark-0001.yaml", b"first\n")

    assert result.outcome == "created"
    assert result.namespace_state == "committed"
    assert (tmp_path / "ldvh-base/sparks/spark-0001.yaml").read_bytes() == b"first\n"
    assert not tuple((tmp_path / "ldvh-base/sparks").glob(".ldvh-create-*.tmp"))

@_POSIX_ONLY
def test_posix_create_preserves_public_fact_directory_modes(tmp_path: Path) -> None:
    previous_umask = os.umask(0)
    try:
        result = atomic_create_relative(tmp_path, "ldvh-base/sparks/spark-0001.yaml", b"first\n")
    finally:
        os.umask(previous_umask)

    assert result.outcome == "created"
    assert stat.S_IMODE((tmp_path / "ldvh-base").stat().st_mode) == 0o755
    assert stat.S_IMODE((tmp_path / "ldvh-base/sparks").stat().st_mode) == 0o755

def test_posix_create_never_overwrites_an_existing_target(tmp_path: Path) -> None:
    target = tmp_path / "ldvh-base/sparks/spark-0001.yaml"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"existing\n")

    result = atomic_create_relative(tmp_path, "ldvh-base/sparks/spark-0001.yaml", b"replacement\n")

    assert result.outcome == "conflict"
    assert result.namespace_state == "not_committed"
    assert target.read_bytes() == b"existing\n"

def test_create_rejects_linked_parent_without_touching_external_target(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    facts = tmp_path / "ldvh-base"
    try:
        facts.symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks are unavailable")

    result = atomic_create_relative(tmp_path, "ldvh-base/sparks/spark-0001.yaml", b"outside\n")

    assert result.outcome == "unavailable"
    assert result.namespace_state == "not_committed"
    assert not (outside / "sparks/spark-0001.yaml").exists()


def test_file_sync_failure_before_create_commit_leaves_no_target(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_fsync = os.fsync

    def fail_file_sync(descriptor: int) -> None:
        if stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise OSError("file sync failed")
        real_fsync(descriptor)

    monkeypatch.setattr(filesystem.os, "fsync", fail_file_sync)

    result = atomic_create_relative(tmp_path, "ldvh-base/sparks/spark-0001.yaml", b"first\n")

    assert result.outcome == "unavailable"
    assert result.namespace_state == "not_committed"
    assert not (tmp_path / "ldvh-base/sparks/spark-0001.yaml").exists()
    assert not tuple((tmp_path / "ldvh-base/sparks").glob(".ldvh-create-*.tmp"))

@_POSIX_ONLY
def test_new_parent_sync_failure_happens_before_create_commit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_fsync = os.fsync
    failed = False

    def fail_first_directory_sync(descriptor: int) -> None:
        nonlocal failed
        if not failed and stat.S_ISDIR(os.fstat(descriptor).st_mode):
            failed = True
            raise OSError("parent entry sync failed")
        real_fsync(descriptor)

    monkeypatch.setattr(filesystem.os, "fsync", fail_first_directory_sync)

    result = atomic_create_relative(tmp_path, "ldvh-base/sparks/spark-0001.yaml", b"first\n")

    assert failed
    assert result.outcome == "unavailable"
    assert result.namespace_state == "not_committed"
    assert not (tmp_path / "ldvh-base/sparks/spark-0001.yaml").exists()

@_POSIX_ONLY
def test_directory_sync_failure_after_create_reports_committed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_fsync = os.fsync
    target = tmp_path / "ldvh-base/sparks/spark-0001.yaml"

    def fail_directory_sync(descriptor: int) -> None:
        if stat.S_ISDIR(os.fstat(descriptor).st_mode) and target.exists():
            raise OSError("directory sync failed")
        real_fsync(descriptor)

    monkeypatch.setattr(filesystem.os, "fsync", fail_directory_sync)

    result = atomic_create_relative(tmp_path, "ldvh-base/sparks/spark-0001.yaml", b"first\n")

    assert result.outcome == "created"
    assert result.namespace_state == "committed"
    assert (tmp_path / "ldvh-base/sparks/spark-0001.yaml").read_bytes() == b"first\n"

@_POSIX_ONLY
def test_create_syncs_directory_after_target_publish_and_temporary_cleanup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[str] = []
    target = tmp_path / "ldvh-base/sparks/spark-0001.yaml"
    real_link = os.link
    real_unlink = os.unlink
    real_fsync = os.fsync

    def recording_link(*args: object, **kwargs: object) -> None:
        real_link(*args, **kwargs)
        events.append("link")

    def recording_unlink(path: str | bytes, *args: object, **kwargs: object) -> None:
        if os.fsdecode(path).startswith(".ldvh-create-"):
            events.append("unlink-temporary")
        real_unlink(path, *args, **kwargs)

    def recording_fsync(descriptor: int) -> None:
        if stat.S_ISDIR(os.fstat(descriptor).st_mode) and target.exists():
            events.append("final-directory-fsync")
        real_fsync(descriptor)

    monkeypatch.setattr(filesystem.os, "link", recording_link)
    monkeypatch.setattr(filesystem.os, "unlink", recording_unlink)
    monkeypatch.setattr(filesystem.os, "fsync", recording_fsync)

    atomic_create_relative(tmp_path, "ldvh-base/sparks/spark-0001.yaml", b"first\n")

    assert events == ["link", "unlink-temporary", "final-directory-fsync"]

@_POSIX_ONLY
def test_cleanup_failure_is_reported_after_create_commit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_unlink = os.unlink

    def fail_temporary_cleanup(path: str | bytes, *args: object, **kwargs: object) -> None:
        if os.fsdecode(path).startswith(".ldvh-create-"):
            raise OSError("cleanup failed")
        real_unlink(path, *args, **kwargs)

    monkeypatch.setattr(filesystem.os, "unlink", fail_temporary_cleanup)

    result = atomic_create_relative(tmp_path, "ldvh-base/sparks/spark-0001.yaml", b"first\n")

    assert result.outcome == "created"
    assert result.namespace_state == "committed"
    assert (tmp_path / "ldvh-base/sparks/spark-0001.yaml").read_bytes() == b"first\n"
    assert len(tuple((tmp_path / "ldvh-base/sparks").glob(".ldvh-create-*.tmp"))) == 1

@_POSIX_ONLY
def test_create_reconciles_a_link_that_committed_before_error_return(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_link = os.link

    def commit_then_fail(*args: object, **kwargs: object) -> None:
        real_link(*args, **kwargs)
        raise OSError("simulated post-commit link error")

    monkeypatch.setattr(filesystem.os, "link", commit_then_fail)

    result = atomic_create_relative(tmp_path, "ldvh-base/sparks/spark-0001.yaml", b"first\n")

    assert result.outcome == "created"
    assert result.namespace_state == "committed"
    
    assert (tmp_path / "ldvh-base/sparks/spark-0001.yaml").read_bytes() == b"first\n"


def test_replace_conflict_preserves_current_bytes(tmp_path: Path) -> None:
    target = tmp_path / "ldvh-base/sparks/spark-0001.yaml"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"current\n")

    result = atomic_replace_relative_if_equal(
        tmp_path,
        "ldvh-base/sparks/spark-0001.yaml",
        b"stale\n",
        b"replacement\n",
    )

    assert result.outcome == "conflict"
    assert result.namespace_state == "not_committed"
    assert target.read_bytes() == b"current\n"

@_POSIX_ONLY
def test_directory_sync_failure_after_replace_reports_committed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "ldvh-base/sparks/spark-0001.yaml"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"current\n")
    real_fsync = os.fsync

    def fail_directory_sync(descriptor: int) -> None:
        if stat.S_ISDIR(os.fstat(descriptor).st_mode):
            raise OSError("directory sync failed")
        real_fsync(descriptor)

    monkeypatch.setattr(filesystem.os, "fsync", fail_directory_sync)

    result = atomic_replace_relative_if_equal(
        tmp_path,
        "ldvh-base/sparks/spark-0001.yaml",
        b"current\n",
        b"replacement\n",
    )

    assert result.outcome == "replaced"
    assert result.namespace_state == "committed"
    assert target.read_bytes() == b"replacement\n"

def test_replace_reconciles_namespace_when_replace_commits_before_error_return(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "ldvh-base/sparks/spark-0001.yaml"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"current\n")
    real_replace = os.replace

    def commit_then_fail(*args: object, **kwargs: object) -> None:
        real_replace(*args, **kwargs)
        raise OSError("simulated post-commit replace error")

    monkeypatch.setattr(filesystem.os, "replace", commit_then_fail)

    result = atomic_replace_relative_if_equal(
        tmp_path,
        "ldvh-base/sparks/spark-0001.yaml",
        b"current\n",
        b"replacement\n",
    )

    assert result.outcome == "replaced"
    assert result.namespace_state == "committed"
    assert target.read_bytes() == b"replacement\n"

def test_unknown_platform_write_policy_fails_closed_before_mutation(tmp_path: Path) -> None:
    """Platforms without a native backend (not posix or approved nt) stay fail-closed."""
    create = atomic_create_relative(
        tmp_path,
        "ldvh-base/sparks/spark-0001.yaml",
        b"first\n",
        platform_name="java",
    )

    assert create.outcome == "unavailable"
    assert create.namespace_state == "not_committed"
    assert not (tmp_path / "facts").exists()

def test_windows_candidate_create_and_replace_are_file_only_without_posix_backend(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        filesystem,
        "_open_relative_directory_posix",
        lambda *args, **kwargs: pytest.fail("portable branch must not enter POSIX directory backend"),
    )
    monkeypatch.setattr(
        filesystem,
        "_read_bytes_posix",
        lambda *args, **kwargs: pytest.fail("portable branch must not enter POSIX read backend"),
    )
    relative = "ldvh-base/sparks/spark-0001.yaml"

    created = atomic_create_relative(
        tmp_path,
        relative,
        b"first\n",
        platform_name="nt",
        allow_file_only=True,
    )
    replaced = atomic_replace_relative_if_equal(
        tmp_path,
        relative,
        b"first\n",
        b"second\n",
        platform_name="nt",
        allow_file_only=True,
    )
    removed = remove_relative_if_equal(
        tmp_path,
        relative,
        b"second\n",
        platform_name="nt",
        allow_file_only=True,
    )

    assert (created.outcome, created.namespace_state) == ("created", "committed")
    assert (replaced.outcome, replaced.namespace_state) == ("replaced", "committed")
    assert (removed.outcome, removed.namespace_state) == ("removed", "committed")
    assert not (tmp_path / relative).exists()

def test_remove_missing_path_does_not_create_parent_directories(tmp_path: Path) -> None:
    result = remove_relative_if_equal(tmp_path, "ldvh-base/sparks/spark-0001.yaml", b"missing\n")

    assert result.outcome == "conflict"
    assert result.namespace_state == "not_committed"
    assert not (tmp_path / "facts").exists()
