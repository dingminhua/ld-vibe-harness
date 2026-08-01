from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest

from ldvh import filesystem
from ldvh.filesystem import (
    atomic_create_directory_relative,
    atomic_create_relative,
    atomic_replace_directory_relative_if_members_equal,
    atomic_replace_relative_if_equal,
    atomic_store_relative,
    remove_directory_relative_if_members_equal,
    remove_relative_if_equal,
)


def test_posix_create_publishes_exact_bytes_and_full_durability(tmp_path: Path) -> None:
    result = atomic_create_relative(tmp_path, "ldvh-base/sparks/spark-0001.yaml", b"first\n")

    assert result.outcome == "created"
    assert result.namespace_state == "committed"
    assert result.durability == "file_and_directory"
    assert result.cleanup == "clean"
    assert (tmp_path / "ldvh-base/sparks/spark-0001.yaml").read_bytes() == b"first\n"
    assert not tuple((tmp_path / "ldvh-base/sparks").glob(".ldvh-create-*.tmp"))


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


def test_store_rejects_symlink_counter_without_replacing_or_following_it(tmp_path: Path) -> None:
    outside = tmp_path / "outside.counter"
    outside.write_bytes(b"outside\n")
    counter = tmp_path / "ldvh/fact-id-allocators/sample.counter"
    counter.parent.mkdir(parents=True)
    try:
        counter.symlink_to(outside)
    except OSError:
        pytest.skip("symlinks are unavailable")

    result = atomic_store_relative(tmp_path, "ldvh/fact-id-allocators/sample.counter", b"1\n")

    assert result.outcome == "unavailable"
    assert result.namespace_state == "not_committed"
    assert outside.read_bytes() == b"outside\n"
    assert counter.is_symlink()


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


def test_directory_sync_failure_after_create_reports_committed_unknown_durability(
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
    assert result.durability == "unknown"
    assert (tmp_path / "ldvh-base/sparks/spark-0001.yaml").read_bytes() == b"first\n"


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

    result = atomic_create_relative(tmp_path, "ldvh-base/sparks/spark-0001.yaml", b"first\n")

    assert result.durability == "file_and_directory"
    assert events == ["link", "unlink-temporary", "final-directory-fsync"]


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
    assert result.cleanup == "residue"
    assert (tmp_path / "ldvh-base/sparks/spark-0001.yaml").read_bytes() == b"first\n"
    assert len(tuple((tmp_path / "ldvh-base/sparks").glob(".ldvh-create-*.tmp"))) == 1


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
    assert result.durability == "file_and_directory"
    assert (tmp_path / "ldvh-base/sparks/spark-0001.yaml").read_bytes() == b"first\n"


def test_store_reconciles_replace_that_committed_before_error_return(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_replace = os.replace

    def commit_then_fail(*args: object, **kwargs: object) -> None:
        real_replace(*args, **kwargs)
        raise OSError("simulated post-commit replace error")

    monkeypatch.setattr(filesystem.os, "replace", commit_then_fail)

    result = atomic_store_relative(tmp_path, "ldvh/fact-id-allocators/sample.counter", b"1\n")

    assert result.outcome == "stored"
    assert result.namespace_state == "committed"
    assert result.durability == "unknown"
    assert (tmp_path / "ldvh/fact-id-allocators/sample.counter").read_bytes() == b"1\n"


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


def test_directory_sync_failure_after_replace_reports_committed_unknown_durability(
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
    assert result.durability == "unknown"
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
    assert result.durability == "unknown"
    assert target.read_bytes() == b"replacement\n"


def test_windows_public_write_policy_fails_before_mutation(tmp_path: Path) -> None:
    create = atomic_create_relative(
        tmp_path,
        "ldvh-base/sparks/spark-0001.yaml",
        b"first\n",
        platform_name="nt",
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
    stored = atomic_store_relative(
        tmp_path,
        "ldvh/fact-id-allocators/sample.counter",
        b"1\n",
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

    assert (created.outcome, created.namespace_state, created.durability) == (
        "created",
        "committed",
        "file_only",
    )
    assert (replaced.outcome, replaced.namespace_state, replaced.durability) == (
        "replaced",
        "committed",
        "file_only",
    )
    assert (stored.outcome, stored.namespace_state, stored.durability) == (
        "stored",
        "committed",
        "file_only",
    )
    assert (removed.outcome, removed.namespace_state, removed.durability) == (
        "removed",
        "committed",
        "file_only",
    )
    assert not (tmp_path / relative).exists()
    assert (tmp_path / "ldvh/fact-id-allocators/sample.counter").read_bytes() == b"1\n"


def test_remove_missing_path_does_not_create_parent_directories(tmp_path: Path) -> None:
    result = remove_relative_if_equal(tmp_path, "ldvh-base/sparks/spark-0001.yaml", b"missing\n")

    assert result.outcome == "conflict"
    assert result.namespace_state == "not_committed"
    assert not (tmp_path / "facts").exists()


@pytest.mark.skipif(os.name != "posix", reason="directory publication requires POSIX primitives")
def test_atomic_directory_create_is_no_replace_and_cleans_staging(tmp_path: Path) -> None:
    relative = "ldvh-base/file-assets/file-asset-0001"
    members = {"file-asset.yaml": b"object_id: file-asset-0001\n", "payload": b"payload\n"}

    created = atomic_create_directory_relative(tmp_path, relative, members)
    conflict = atomic_create_directory_relative(
        tmp_path,
        relative,
        {"file-asset.yaml": b"other\n", "payload": b"other\n"},
    )

    assert (created.outcome, created.namespace_state, created.durability) == (
        "created",
        "committed",
        "file_and_directory",
    )
    assert (conflict.outcome, conflict.namespace_state) == ("conflict", "not_committed")
    directory = tmp_path / relative
    assert (directory / "file-asset.yaml").read_bytes() == members["file-asset.yaml"]
    assert (directory / "payload").read_bytes() == members["payload"]
    staging = tmp_path / "ldvh-base/.file-asset-staging"
    assert not tuple(staging.iterdir())


@pytest.mark.skipif(os.name != "posix", reason="directory rollback requires POSIX primitives")
def test_directory_rollback_requires_exact_closed_members(tmp_path: Path) -> None:
    relative = "ldvh-base/file-assets/file-asset-0001"
    members = {"file-asset.yaml": b"manifest\n", "payload": b"payload\n"}
    assert atomic_create_directory_relative(tmp_path, relative, members).outcome == "created"

    conflict = remove_directory_relative_if_members_equal(
        tmp_path,
        relative,
        {**members, "payload": b"different\n"},
    )
    removed = remove_directory_relative_if_members_equal(tmp_path, relative, members)

    assert (conflict.outcome, conflict.namespace_state) == ("conflict", "not_committed")
    assert (removed.outcome, removed.namespace_state, removed.durability) == (
        "removed",
        "committed",
        "file_and_directory",
    )
    assert not (tmp_path / relative).exists()


@pytest.mark.skipif(os.name != "posix", reason="directory exchange requires POSIX primitives")
def test_atomic_directory_replace_removes_payload_and_keeps_only_tombstone(tmp_path: Path) -> None:
    relative = "ldvh-base/file-assets/file-asset-0001"
    before = {"file-asset.yaml": b"status: active\n", "payload": b"payload\n"}
    after = {"file-asset.yaml": b"status: deleted\n"}
    assert atomic_create_directory_relative(tmp_path, relative, before).outcome == "created"

    replaced = atomic_replace_directory_relative_if_members_equal(tmp_path, relative, before, after)

    assert (replaced.outcome, replaced.namespace_state, replaced.durability, replaced.cleanup) == (
        "replaced",
        "committed",
        "file_and_directory",
        "clean",
    )
    directory = tmp_path / relative
    assert {path.name for path in directory.iterdir()} == {"file-asset.yaml"}
    assert (directory / "file-asset.yaml").read_bytes() == after["file-asset.yaml"]
    assert not tuple((tmp_path / "ldvh-base/file-assets").glob(".ldvh-directory-replace-*.tmp"))


@pytest.mark.skipif(os.name != "posix", reason="directory exchange requires POSIX primitives")
def test_atomic_directory_replace_rolls_back_if_exchanged_before_cannot_be_confirmed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    relative = "ldvh-base/file-assets/file-asset-0001"
    before = {"file-asset.yaml": b"status: active\n", "payload": b"payload\n"}
    after = {"file-asset.yaml": b"status: deleted\n"}
    assert atomic_create_directory_relative(tmp_path, relative, before).outcome == "created"
    original = filesystem._directory_members_equal
    calls = 0

    def fail_second_confirmation(directory_fd: int, expected: dict[str, bytes]) -> bool:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("injected pre-destruction failure")
        return original(directory_fd, expected)

    monkeypatch.setattr(filesystem, "_directory_members_equal", fail_second_confirmation)

    replaced = atomic_replace_directory_relative_if_members_equal(tmp_path, relative, before, after)

    assert (replaced.outcome, replaced.namespace_state, replaced.cleanup) == (
        "unavailable",
        "not_committed",
        "clean",
    )
    directory = tmp_path / relative
    assert (directory / "file-asset.yaml").read_bytes() == before["file-asset.yaml"]
    assert (directory / "payload").read_bytes() == before["payload"]
    assert not tuple((tmp_path / "ldvh-base/file-assets").glob(".ldvh-directory-replace-*.tmp"))


@pytest.mark.skipif(os.name != "posix", reason="directory exchange requires POSIX primitives")
def test_atomic_directory_rollback_preserves_concurrent_after_image_as_residue(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    relative = "ldvh-base/file-assets/file-asset-0001"
    before = {"file-asset.yaml": b"status: active\n", "payload": b"payload\n"}
    after = {"file-asset.yaml": b"status: deleted\n"}
    concurrent_after = b"status: deleted\ndisposition_summary: concurrent\n"
    assert atomic_create_directory_relative(tmp_path, relative, before).outcome == "created"
    original_equal = filesystem._directory_members_equal
    original_exchange = filesystem._exchange_directories_posix
    equal_calls = 0
    exchange_calls = 0

    def fail_first_after_confirmation(directory_fd: int, expected: dict[str, bytes]) -> bool:
        nonlocal equal_calls
        equal_calls += 1
        if equal_calls == 2:
            raise OSError("injected pre-destruction failure")
        return original_equal(directory_fd, expected)

    def mutate_before_rollback(*args: object, **kwargs: object) -> None:
        nonlocal exchange_calls
        exchange_calls += 1
        if exchange_calls == 2:
            (tmp_path / relative / "file-asset.yaml").write_bytes(concurrent_after)
        original_exchange(*args, **kwargs)

    monkeypatch.setattr(filesystem, "_directory_members_equal", fail_first_after_confirmation)
    monkeypatch.setattr(filesystem, "_exchange_directories_posix", mutate_before_rollback)

    replaced = atomic_replace_directory_relative_if_members_equal(tmp_path, relative, before, after)

    assert (replaced.outcome, replaced.namespace_state, replaced.cleanup) == (
        "unavailable",
        "uncertain",
        "residue",
    )
    directory = tmp_path / relative
    assert (directory / "file-asset.yaml").read_bytes() == before["file-asset.yaml"]
    assert (directory / "payload").read_bytes() == before["payload"]
    residue = tuple((tmp_path / "ldvh-base/file-assets").glob(".ldvh-directory-replace-*.tmp"))
    assert len(residue) == 1
    assert (residue[0] / "file-asset.yaml").read_bytes() == concurrent_after


@pytest.mark.skipif(os.name != "posix", reason="directory exchange requires POSIX primitives")
def test_atomic_directory_replace_never_downgrades_post_payload_residue_to_clean(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    relative = "ldvh-base/file-assets/file-asset-0001"
    before = {"file-asset.yaml": b"status: active\n", "payload": b"payload\n"}
    after = {"file-asset.yaml": b"status: deleted\n"}
    assert atomic_create_directory_relative(tmp_path, relative, before).outcome == "created"
    original_unlink = filesystem.os.unlink

    def fail_old_manifest_cleanup(path: str, *args: object, **kwargs: object) -> None:
        if path == "file-asset.yaml":
            raise OSError("injected post-payload cleanup failure")
        original_unlink(path, *args, **kwargs)

    monkeypatch.setattr(filesystem.os, "unlink", fail_old_manifest_cleanup)

    replaced = atomic_replace_directory_relative_if_members_equal(tmp_path, relative, before, after)

    assert (replaced.outcome, replaced.namespace_state, replaced.durability, replaced.cleanup) == (
        "replaced",
        "committed",
        "unknown",
        "residue",
    )
    directory = tmp_path / relative
    assert (directory / "file-asset.yaml").read_bytes() == after["file-asset.yaml"]
    residue = tuple((tmp_path / "ldvh-base/file-assets").glob(".ldvh-directory-replace-*.tmp"))
    assert len(residue) == 1
    assert {path.name for path in residue[0].iterdir()} == {"file-asset.yaml"}
