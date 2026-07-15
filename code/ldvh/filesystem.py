"""Platform-selected filesystem primitives shared by LDVH production modules."""

from __future__ import annotations

import os
import secrets
import stat
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol


class UnsafePathError(OSError):
    """A path has a forbidden type or link/reparse topology."""


class PathChangedError(OSError):
    """A path or open handle changed during one observation."""


class UnstableIdentityError(OSError):
    """The platform did not expose a stable filesystem identity."""


class ReadBudgetExceeded(OSError):
    """A regular file exceeded the caller's bounded-read budget."""


WriteOutcome = Literal["created", "replaced", "stored", "removed", "conflict", "unavailable"]
NamespaceState = Literal["not_committed", "committed", "uncertain"]
Durability = Literal["file_and_directory", "file_only", "unknown"]
CleanupState = Literal["clean", "residue"]


@dataclass(frozen=True, slots=True)
class AtomicWriteResult:
    outcome: WriteOutcome
    namespace_state: NamespaceState
    durability: Durability
    cleanup: CleanupState


def durable_writes_enabled(platform_name: str | None = None) -> bool:
    """Return whether public writes may claim the platform's required durability."""

    selected_platform = os.name if platform_name is None else platform_name
    return selected_platform == "posix"


class _LockingApi(Protocol):
    def lock(self, descriptor: int) -> None: ...

    def unlock(self, descriptor: int) -> None: ...


class _PosixLockingApi:
    def __init__(self) -> None:
        import fcntl

        self._fcntl = fcntl

    def lock(self, descriptor: int) -> None:
        self._fcntl.flock(descriptor, self._fcntl.LOCK_EX)

    def unlock(self, descriptor: int) -> None:
        self._fcntl.flock(descriptor, self._fcntl.LOCK_UN)


class _WindowsLockingApi:
    def __init__(self) -> None:
        import msvcrt

        self._msvcrt = msvcrt

    def lock(self, descriptor: int) -> None:
        os.lseek(descriptor, 0, os.SEEK_SET)
        self._msvcrt.locking(descriptor, self._msvcrt.LK_LOCK, 1)

    def unlock(self, descriptor: int) -> None:
        os.lseek(descriptor, 0, os.SEEK_SET)
        self._msvcrt.locking(descriptor, self._msvcrt.LK_UNLCK, 1)


def _locking_api(platform_name: str) -> _LockingApi:
    if platform_name == "posix":
        return _PosixLockingApi()
    if platform_name == "nt":
        return _WindowsLockingApi()
    raise OSError(f"unsupported operating system: {platform_name}")


@contextmanager
def _exclusive_file_lock(path: Path, api: _LockingApi) -> Iterator[None]:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_RDWR | os.O_CREAT, 0o600)
    locked = False
    try:
        api.lock(descriptor)
        locked = True
        yield
    finally:
        if locked:
            try:
                api.unlock(descriptor)
            finally:
                os.close(descriptor)
        else:
            os.close(descriptor)


@contextmanager
def _exclusive_descriptor_lock(descriptor: int, api: _LockingApi) -> Iterator[None]:
    locked = False
    try:
        api.lock(descriptor)
        locked = True
        yield
    finally:
        if locked:
            try:
                api.unlock(descriptor)
            finally:
                os.close(descriptor)
        else:
            os.close(descriptor)


@contextmanager
def exclusive_file_lock(path: Path) -> Iterator[None]:
    """Hold the platform-native exclusive lock associated with ``path``."""

    with _exclusive_file_lock(path, _locking_api(os.name)):
        yield


def is_reparse_point(observation: os.stat_result) -> bool:
    """Return whether a stat observation carries the Windows reparse attribute."""

    attributes = getattr(observation, "st_file_attributes", 0)
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return bool(attributes & reparse_flag)


def is_link_or_reparse(observation: os.stat_result) -> bool:
    """Return whether an observation is a symbolic link or Windows reparse point."""

    return stat.S_ISLNK(observation.st_mode) or is_reparse_point(observation)


def _normal_relative_path(relative_path: str | Path) -> Path:
    relative = Path(relative_path)
    if relative.is_absolute() or not relative.parts or any(part in {"", ".", ".."} for part in relative.parts):
        raise UnsafePathError("path must be normalized and relative")
    return relative


def _windows_unc_path(path: Path) -> bool:
    value = os.fspath(path)
    return value.startswith(("\\\\", "//"))


def _open_relative_directory_posix(
    root: Path,
    relative_directory: Path,
    *,
    create: bool,
    directory_mode: int = 0o755,
) -> int:
    no_follow = getattr(os, "O_NOFOLLOW", None)
    directory_flag = getattr(os, "O_DIRECTORY", None)
    if no_follow is None or directory_flag is None:
        raise OSError("POSIX no-follow directory operations are unavailable")
    descriptor = os.open(root, os.O_RDONLY | directory_flag | no_follow)
    try:
        for component in relative_directory.parts:
            if component == ".":
                continue
            if create:
                try:
                    os.mkdir(component, mode=directory_mode, dir_fd=descriptor)
                except FileExistsError:
                    pass
                else:
                    # Persist each newly published directory entry before descending.
                    os.fsync(descriptor)
            next_descriptor = os.open(
                component,
                os.O_RDONLY | directory_flag | no_follow,
                dir_fd=descriptor,
            )
            os.close(descriptor)
            descriptor = next_descriptor
        return descriptor
    except Exception:
        os.close(descriptor)
        raise


def _ensure_relative_directory_portable(
    root: Path,
    relative_directory: Path,
    *,
    directory_mode: int = 0o755,
) -> Path:
    if _windows_unc_path(root):
        raise UnstableIdentityError("UNC paths are unsupported without native verification")
    root_observation = root.lstat()
    if is_link_or_reparse(root_observation) or not stat.S_ISDIR(root_observation.st_mode):
        raise UnsafePathError("root must be a non-reparse directory")
    root_signature = _portable_topology_identity(root_observation)
    current = root
    for component in relative_directory.parts:
        if component == ".":
            continue
        current = current / component
        try:
            current.mkdir(mode=directory_mode)
        except FileExistsError:
            pass
        observed = current.lstat()
        if is_link_or_reparse(observed) or not stat.S_ISDIR(observed.st_mode):
            raise UnsafePathError("directory path contains a link, reparse point, or non-directory")
        _portable_signature(observed)
    if root_signature != _portable_topology_identity(root.lstat()):
        raise PathChangedError("root changed while a directory path was prepared")
    return current


def _open_relative_lock_descriptor(
    root: Path,
    relative_path: Path,
    *,
    platform_name: str,
) -> int:
    parent = relative_path.parent
    target_name = relative_path.name
    no_follow = getattr(os, "O_NOFOLLOW", None)
    directory_flag = getattr(os, "O_DIRECTORY", None)
    if platform_name != "nt" and no_follow is not None and directory_flag is not None:
        directory_fd = _open_relative_directory_posix(root, parent, create=True, directory_mode=0o700)
        try:
            try:
                descriptor = os.open(
                    target_name,
                    os.O_RDWR | os.O_CREAT | no_follow,
                    0o600,
                    dir_fd=directory_fd,
                )
            except FileNotFoundError:
                # Darwin may transiently report ENOENT when independent
                # processes concurrently publish the same O_CREAT name.
                descriptor = os.open(
                    target_name,
                    os.O_RDWR | os.O_CREAT | no_follow,
                    0o600,
                    dir_fd=directory_fd,
                )
        finally:
            os.close(directory_fd)
        try:
            observed = os.fstat(descriptor)
            if not stat.S_ISREG(observed.st_mode):
                raise UnsafePathError("lock path is not a regular file")
        except Exception:
            os.close(descriptor)
            raise
        return descriptor

    directory = _ensure_relative_directory_portable(root, parent, directory_mode=0o700)
    target = directory / target_name
    try:
        before = target.lstat()
    except FileNotFoundError:
        before = None
    else:
        if is_link_or_reparse(before) or not stat.S_ISREG(before.st_mode):
            raise UnsafePathError("lock path must be a regular non-reparse file")
    descriptor = os.open(target, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        handle = os.fstat(descriptor)
        after = target.lstat()
        if is_link_or_reparse(handle) or is_link_or_reparse(after):
            raise UnsafePathError("opened lock is a reparse point")
        if _portable_signature(handle) != _portable_signature(after):
            raise PathChangedError("opened lock does not match its path")
        if before is not None and _portable_signature(before) != _portable_signature(after):
            raise PathChangedError("lock path changed while it was opened")
        return descriptor
    except Exception:
        os.close(descriptor)
        raise


@contextmanager
def exclusive_relative_file_lock(
    root: Path,
    relative_path: str | Path,
    *,
    platform_name: str | None = None,
) -> Iterator[None]:
    """Lock one regular state file below a trusted root without following link/reparse paths."""

    relative = _normal_relative_path(relative_path)
    selected_platform = os.name if platform_name is None else platform_name
    api = _locking_api(selected_platform)
    descriptor = _open_relative_lock_descriptor(root, relative, platform_name=selected_platform)
    with _exclusive_descriptor_lock(descriptor, api):
        yield


def _portable_signature(observation: os.stat_result) -> tuple[int, ...]:
    identity: list[int] = []
    for field in ("st_dev", "st_ino"):
        value = getattr(observation, field, None)
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise UnstableIdentityError(f"filesystem identity field {field} is unavailable")
        identity.append(value)
    metadata: list[int] = []
    for field in ("st_size", "st_mtime_ns", "st_ctime_ns"):
        value = getattr(observation, field, None)
        if not isinstance(value, int) or isinstance(value, bool):
            raise UnstableIdentityError(f"filesystem metadata field {field} is unavailable")
        metadata.append(value)
    return (
        stat.S_IFMT(observation.st_mode),
        *identity,
        *metadata,
        getattr(observation, "st_nlink", 0),
        getattr(observation, "st_file_attributes", 0),
    )


def _portable_topology_identity(observation: os.stat_result) -> tuple[int, int, int, int]:
    signature = _portable_signature(observation)
    return signature[0], signature[1], signature[2], signature[-1]


def _observe_relative_path(
    root: Path,
    relative_path: Path,
    *,
    final_type: str,
) -> tuple[tuple[Path, tuple[int, ...]], ...]:
    observations: list[tuple[Path, tuple[int, ...]]] = []
    paths = [root]
    current = root
    for component in relative_path.parts:
        current = current / component
        paths.append(current)
    for index, path in enumerate(paths):
        observed = path.lstat()
        if is_link_or_reparse(observed):
            raise UnsafePathError("path contains a symbolic link or reparse point")
        is_final = index == len(paths) - 1
        if not is_final and not stat.S_ISDIR(observed.st_mode):
            raise UnsafePathError("path component is not a directory")
        if is_final and final_type == "regular" and not stat.S_ISREG(observed.st_mode):
            raise UnsafePathError("path is not a regular file")
        if is_final and final_type == "directory" and not stat.S_ISDIR(observed.st_mode):
            raise UnsafePathError("path is not a directory")
        observations.append((path, _portable_signature(observed)))
    return tuple(observations)


def validate_relative_regular_file(root: Path, relative_path: str | Path) -> Path:
    """Validate a relative regular-file topology without following link/reparse paths."""

    relative = _normal_relative_path(relative_path)
    _observe_relative_path(root, relative, final_type="regular")
    return root / relative


def safe_list_directory(root: Path, relative_path: str | Path) -> tuple[Path, ...]:
    """List one relative directory only if its complete topology stays stable."""

    relative = _normal_relative_path(relative_path)
    before = _observe_relative_path(root, relative, final_type="directory")
    entries = tuple((root / relative).iterdir())
    after = _observe_relative_path(root, relative, final_type="directory")
    if before != after:
        raise PathChangedError("directory topology changed while it was listed")
    return entries


def _read_descriptor(descriptor: int, *, max_bytes: int | None) -> bytes:
    before = os.fstat(descriptor)
    if not stat.S_ISREG(before.st_mode) or is_reparse_point(before):
        raise UnsafePathError("opened handle is not a regular non-reparse file")
    if max_bytes is not None and before.st_size > max_bytes:
        raise ReadBudgetExceeded("file exceeds the bounded-read budget")
    chunks: list[bytes] = []
    observed = 0
    while max_bytes is None or observed <= max_bytes:
        budget = 64 * 1024 if max_bytes is None else min(64 * 1024, max_bytes + 1 - observed)
        chunk = os.read(descriptor, budget)
        if not chunk:
            break
        chunks.append(chunk)
        observed += len(chunk)
    if max_bytes is not None and observed > max_bytes:
        raise ReadBudgetExceeded("file exceeds the bounded-read budget")
    after = os.fstat(descriptor)
    if _portable_signature(before) != _portable_signature(after):
        raise PathChangedError("opened file changed while it was read")
    return b"".join(chunks)


def _read_bytes_posix(
    root: Path,
    relative_path: Path,
    *,
    no_follow: int,
    directory_flag: int,
    max_bytes: int | None,
) -> bytes:
    directory_fd = os.open(root, os.O_RDONLY | directory_flag | no_follow)
    file_fd: int | None = None
    try:
        for component in relative_path.parts[:-1]:
            next_fd = os.open(component, os.O_RDONLY | directory_flag | no_follow, dir_fd=directory_fd)
            os.close(directory_fd)
            directory_fd = next_fd
        file_fd = os.open(relative_path.parts[-1], os.O_RDONLY | no_follow, dir_fd=directory_fd)
        return _read_descriptor(file_fd, max_bytes=max_bytes)
    finally:
        if file_fd is not None:
            os.close(file_fd)
        os.close(directory_fd)


def _read_bytes_portable(
    root: Path,
    relative_path: Path,
    *,
    max_bytes: int | None,
) -> bytes:
    absolute_path = root / relative_path
    before_components = _observe_relative_path(root, relative_path, final_type="regular")
    with absolute_path.open("rb", buffering=0) as source:
        before_handle = os.fstat(source.fileno())
        if before_components[-1][1] != _portable_signature(before_handle):
            raise PathChangedError("opened file does not match the observed path")
        raw_bytes = _read_descriptor(source.fileno(), max_bytes=max_bytes)
        after_handle = os.fstat(source.fileno())
    after_components = _observe_relative_path(root, relative_path, final_type="regular")
    if _portable_signature(before_handle) != _portable_signature(after_handle):
        raise PathChangedError("opened file changed while it was read")
    if before_components != after_components:
        raise PathChangedError("path topology changed while the file was read")
    if after_components[-1][1] != _portable_signature(after_handle):
        raise PathChangedError("opened file no longer matches the observed path")
    return raw_bytes


def safe_read_relative(
    root: Path,
    relative_path: str | Path,
    *,
    max_bytes: int | None = None,
    platform_name: str | None = None,
) -> bytes:
    """Read one relative regular file through the strongest available platform path."""

    relative = _normal_relative_path(relative_path)
    selected_platform = os.name if platform_name is None else platform_name
    if selected_platform == "nt" and _windows_unc_path(root):
        raise UnstableIdentityError("UNC paths are unsupported without native verification")
    no_follow = getattr(os, "O_NOFOLLOW", None)
    directory_flag = getattr(os, "O_DIRECTORY", None)
    if selected_platform != "nt" and no_follow is not None and directory_flag is not None:
        return _read_bytes_posix(
            root,
            relative,
            no_follow=no_follow,
            directory_flag=directory_flag,
            max_bytes=max_bytes,
        )
    return _read_bytes_portable(root, relative, max_bytes=max_bytes)


def _write_all(descriptor: int, payload: bytes) -> None:
    offset = 0
    while offset < len(payload):
        written = os.write(descriptor, payload[offset:])
        if written <= 0:
            raise OSError("write made no progress")
        offset += written


def _atomic_create_posix(root: Path, relative: Path, payload: bytes, mode: int) -> AtomicWriteResult:
    directory_fd: int | None = None
    temporary_fd: int | None = None
    temporary_name = f".ldvh-create-{secrets.token_hex(12)}.tmp"
    cleanup: CleanupState = "clean"
    outcome: WriteOutcome = "unavailable"
    namespace: NamespaceState = "not_committed"
    durability: Durability = "unknown"
    cleanup_attempted = False
    try:
        directory_fd = _open_relative_directory_posix(
            root,
            relative.parent,
            create=True,
            directory_mode=0o755,
        )
        no_follow = os.O_NOFOLLOW
        temporary_fd = os.open(
            temporary_name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | no_follow,
            mode,
            dir_fd=directory_fd,
        )
        _write_all(temporary_fd, payload)
        os.fsync(temporary_fd)
        os.close(temporary_fd)
        temporary_fd = None
        try:
            os.link(
                temporary_name,
                relative.name,
                src_dir_fd=directory_fd,
                dst_dir_fd=directory_fd,
                follow_symlinks=False,
            )
        except FileExistsError:
            outcome = "conflict"
        except OSError:
            try:
                temporary_observation = os.stat(temporary_name, dir_fd=directory_fd, follow_symlinks=False)
                target_observation = os.stat(relative.name, dir_fd=directory_fd, follow_symlinks=False)
            except FileNotFoundError:
                namespace = "not_committed"
            except OSError:
                namespace = "uncertain"
            else:
                if (
                    stat.S_ISREG(temporary_observation.st_mode)
                    and stat.S_ISREG(target_observation.st_mode)
                    and (temporary_observation.st_dev, temporary_observation.st_ino)
                    == (target_observation.st_dev, target_observation.st_ino)
                ):
                    outcome = "created"
                    namespace = "committed"
                else:
                    namespace = "uncertain"
        else:
            outcome = "created"
            namespace = "committed"
        if namespace == "committed":
            cleanup_attempted = True
            try:
                os.unlink(temporary_name, dir_fd=directory_fd)
            except FileNotFoundError:
                pass
            except OSError:
                cleanup = "residue"
            try:
                os.fsync(directory_fd)
            except OSError:
                pass
            else:
                durability = "file_and_directory"
    except OSError:
        pass
    finally:
        if temporary_fd is not None:
            os.close(temporary_fd)
        if directory_fd is not None and not cleanup_attempted:
            try:
                os.unlink(temporary_name, dir_fd=directory_fd)
            except FileNotFoundError:
                pass
            except OSError:
                cleanup = "residue"
        if directory_fd is not None:
            os.close(directory_fd)
    return AtomicWriteResult(outcome, namespace, durability, cleanup)


def _atomic_create_portable(root: Path, relative: Path, payload: bytes, mode: int) -> AtomicWriteResult:
    temporary: Path | None = None
    descriptor: int | None = None
    cleanup: CleanupState = "clean"
    outcome: WriteOutcome = "unavailable"
    namespace: NamespaceState = "not_committed"
    durability: Durability = "unknown"
    try:
        directory = _ensure_relative_directory_portable(root, relative.parent, directory_mode=0o755)
        temporary = directory / f".ldvh-create-{secrets.token_hex(12)}.tmp"
        target = directory / relative.name
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
        _write_all(descriptor, payload)
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = None
        temporary_observation = temporary.lstat()
        if is_link_or_reparse(temporary_observation) or not stat.S_ISREG(temporary_observation.st_mode):
            raise UnsafePathError("temporary create carrier is unsafe")
        try:
            os.link(temporary, target, follow_symlinks=False)
        except FileExistsError:
            outcome = "conflict"
        except OSError:
            try:
                same_file = os.path.samefile(temporary, target)
            except FileNotFoundError:
                namespace = "not_committed"
            except OSError:
                namespace = "uncertain"
            else:
                if same_file:
                    outcome = "created"
                    namespace = "committed"
                else:
                    namespace = "uncertain"
        else:
            outcome = "created"
            namespace = "committed"
            durability = "file_only"
            target_observation = target.lstat()
            if (
                is_link_or_reparse(target_observation)
                or not stat.S_ISREG(target_observation.st_mode)
                or not os.path.samefile(temporary, target)
            ):
                durability = "unknown"
    except OSError:
        pass
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if temporary is not None:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass
            except OSError:
                cleanup = "residue"
    return AtomicWriteResult(outcome, namespace, durability, cleanup)


def atomic_create_relative(
    root: Path,
    relative_path: str | Path,
    payload: bytes,
    *,
    mode: int = 0o600,
    platform_name: str | None = None,
    allow_file_only: bool = False,
) -> AtomicWriteResult:
    """Atomically publish a new relative file without replacing an existing name."""

    relative = _normal_relative_path(relative_path)
    selected_platform = os.name if platform_name is None else platform_name
    if selected_platform == "nt":
        if not allow_file_only:
            return AtomicWriteResult("unavailable", "not_committed", "unknown", "clean")
        return _atomic_create_portable(root, relative, payload, mode)
    if selected_platform == "posix":
        return _atomic_create_posix(root, relative, payload, mode)
    return AtomicWriteResult("unavailable", "not_committed", "unknown", "clean")


def _atomic_store_posix(root: Path, relative: Path, payload: bytes, mode: int) -> AtomicWriteResult:
    directory_fd: int | None = None
    temporary_fd: int | None = None
    temporary_name = f".ldvh-store-{secrets.token_hex(12)}.tmp"
    cleanup: CleanupState = "clean"
    outcome: WriteOutcome = "unavailable"
    namespace: NamespaceState = "not_committed"
    durability: Durability = "unknown"
    try:
        directory_fd = _open_relative_directory_posix(
            root,
            relative.parent,
            create=True,
            directory_mode=0o700,
        )
        no_follow = os.O_NOFOLLOW
        try:
            existing = os.stat(relative.name, dir_fd=directory_fd, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            if is_link_or_reparse(existing) or not stat.S_ISREG(existing.st_mode):
                raise UnsafePathError("state target must be a regular non-reparse file")
        temporary_fd = os.open(
            temporary_name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | no_follow,
            mode,
            dir_fd=directory_fd,
        )
        _write_all(temporary_fd, payload)
        os.fsync(temporary_fd)
        os.close(temporary_fd)
        temporary_fd = None
        try:
            os.replace(temporary_name, relative.name, src_dir_fd=directory_fd, dst_dir_fd=directory_fd)
        except OSError:
            status, observed = _comparison_bytes(root, relative, len(payload), platform_name="posix")
            if status == "observed" and observed == payload:
                outcome = "stored"
                namespace = "committed"
            elif status == "unavailable":
                namespace = "uncertain"
        else:
            outcome = "stored"
            namespace = "committed"
            try:
                os.fsync(directory_fd)
            except OSError:
                durability = "unknown"
            else:
                durability = "file_and_directory"
    except OSError:
        pass
    finally:
        if temporary_fd is not None:
            os.close(temporary_fd)
        if directory_fd is not None:
            try:
                os.unlink(temporary_name, dir_fd=directory_fd)
            except FileNotFoundError:
                pass
            except OSError:
                cleanup = "residue"
            os.close(directory_fd)
    return AtomicWriteResult(outcome, namespace, durability, cleanup)


def _atomic_store_portable(root: Path, relative: Path, payload: bytes, mode: int) -> AtomicWriteResult:
    temporary: Path | None = None
    descriptor: int | None = None
    cleanup: CleanupState = "clean"
    outcome: WriteOutcome = "unavailable"
    namespace: NamespaceState = "not_committed"
    try:
        directory = _ensure_relative_directory_portable(root, relative.parent, directory_mode=0o700)
        temporary = directory / f".ldvh-store-{secrets.token_hex(12)}.tmp"
        target = directory / relative.name
        try:
            existing = target.lstat()
        except FileNotFoundError:
            pass
        else:
            if is_link_or_reparse(existing) or not stat.S_ISREG(existing.st_mode):
                raise UnsafePathError("state target must be a regular non-reparse file")
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
        _write_all(descriptor, payload)
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = None
        try:
            os.replace(temporary, target)
        except OSError:
            status, observed = _comparison_bytes(root, relative, len(payload), platform_name="nt")
            if status == "observed" and observed == payload:
                outcome = "stored"
                namespace = "committed"
            elif status == "unavailable":
                namespace = "uncertain"
        else:
            temporary = None
            outcome = "stored"
            namespace = "committed"
    except OSError:
        pass
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if temporary is not None:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass
            except OSError:
                cleanup = "residue"
    return AtomicWriteResult(outcome, namespace, "file_only" if namespace == "committed" else "unknown", cleanup)


def atomic_store_relative(
    root: Path,
    relative_path: str | Path,
    payload: bytes,
    *,
    mode: int = 0o600,
    platform_name: str | None = None,
    allow_file_only: bool = False,
) -> AtomicWriteResult:
    """Atomically store state below a trusted root, replacing the prior regular file if present."""

    relative = _normal_relative_path(relative_path)
    selected_platform = os.name if platform_name is None else platform_name
    if selected_platform == "nt":
        if not allow_file_only:
            return AtomicWriteResult("unavailable", "not_committed", "unknown", "clean")
        return _atomic_store_portable(root, relative, payload, mode)
    if selected_platform == "posix":
        return _atomic_store_posix(root, relative, payload, mode)
    return AtomicWriteResult("unavailable", "not_committed", "unknown", "clean")


def _comparison_bytes(
    root: Path,
    relative: Path,
    maximum: int,
    *,
    platform_name: str,
) -> tuple[Literal["observed", "different", "unavailable"], bytes | None]:
    try:
        return "observed", safe_read_relative(
            root,
            relative,
            max_bytes=maximum,
            platform_name=platform_name,
        )
    except (FileNotFoundError, ReadBudgetExceeded, UnsafePathError):
        return "different", None
    except OSError:
        return "unavailable", None


def _reconcile_replace(
    root: Path,
    relative: Path,
    expected: bytes,
    replacement: bytes,
    *,
    platform_name: str,
) -> AtomicWriteResult:
    status, observed = _comparison_bytes(
        root,
        relative,
        max(len(expected), len(replacement)),
        platform_name=platform_name,
    )
    if status == "unavailable":
        return AtomicWriteResult("unavailable", "uncertain", "unknown", "clean")
    if observed == replacement:
        return AtomicWriteResult("replaced", "committed", "unknown", "clean")
    if observed == expected:
        return AtomicWriteResult("unavailable", "not_committed", "unknown", "clean")
    return AtomicWriteResult("unavailable", "uncertain", "unknown", "clean")


def _atomic_replace_posix(
    root: Path,
    relative: Path,
    expected: bytes,
    replacement: bytes,
) -> AtomicWriteResult:
    initial_status, initial = _comparison_bytes(root, relative, len(expected), platform_name="posix")
    if initial_status == "unavailable":
        return AtomicWriteResult("unavailable", "not_committed", "unknown", "clean")
    if initial != expected:
        return AtomicWriteResult("conflict", "not_committed", "unknown", "clean")
    try:
        mode = stat.S_IMODE(validate_relative_regular_file(root, relative).lstat().st_mode)
    except OSError:
        return AtomicWriteResult("unavailable", "not_committed", "unknown", "clean")
    directory_fd: int | None = None
    temporary_fd: int | None = None
    temporary_name = f".ldvh-update-{secrets.token_hex(12)}.tmp"
    cleanup: CleanupState = "clean"
    result = AtomicWriteResult("unavailable", "not_committed", "unknown", cleanup)
    try:
        directory_fd = _open_relative_directory_posix(root, relative.parent, create=False)
        no_follow = os.O_NOFOLLOW
        temporary_fd = os.open(
            temporary_name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | no_follow,
            mode,
            dir_fd=directory_fd,
        )
        _write_all(temporary_fd, replacement)
        os.fsync(temporary_fd)
        os.close(temporary_fd)
        temporary_fd = None
        second_status, second = _comparison_bytes(root, relative, len(expected), platform_name="posix")
        if second_status == "unavailable":
            result = AtomicWriteResult("unavailable", "not_committed", "unknown", cleanup)
        elif second != expected:
            result = AtomicWriteResult("conflict", "not_committed", "unknown", cleanup)
        else:
            try:
                os.replace(temporary_name, relative.name, src_dir_fd=directory_fd, dst_dir_fd=directory_fd)
            except OSError:
                result = _reconcile_replace(
                    root,
                    relative,
                    expected,
                    replacement,
                    platform_name="posix",
                )
            else:
                result = AtomicWriteResult("replaced", "committed", "unknown", cleanup)
                try:
                    os.fsync(directory_fd)
                except OSError:
                    pass
                else:
                    result = AtomicWriteResult("replaced", "committed", "file_and_directory", cleanup)
    except OSError:
        pass
    finally:
        if temporary_fd is not None:
            os.close(temporary_fd)
        if directory_fd is not None:
            try:
                os.unlink(temporary_name, dir_fd=directory_fd)
            except FileNotFoundError:
                pass
            except OSError:
                cleanup = "residue"
            os.close(directory_fd)
    if cleanup != result.cleanup:
        result = AtomicWriteResult(result.outcome, result.namespace_state, result.durability, cleanup)
    return result


def _atomic_replace_portable(
    root: Path,
    relative: Path,
    expected: bytes,
    replacement: bytes,
) -> AtomicWriteResult:
    initial_status, initial = _comparison_bytes(root, relative, len(expected), platform_name="nt")
    if initial_status == "unavailable":
        return AtomicWriteResult("unavailable", "not_committed", "unknown", "clean")
    if initial != expected:
        return AtomicWriteResult("conflict", "not_committed", "unknown", "clean")
    temporary: Path | None = None
    descriptor: int | None = None
    cleanup: CleanupState = "clean"
    result = AtomicWriteResult("unavailable", "not_committed", "unknown", cleanup)
    try:
        directory = _ensure_relative_directory_portable(root, relative.parent, directory_mode=0o755)
        target = directory / relative.name
        mode = stat.S_IMODE(validate_relative_regular_file(root, relative).lstat().st_mode)
        temporary = directory / f".ldvh-update-{secrets.token_hex(12)}.tmp"
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
        _write_all(descriptor, replacement)
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = None
        second_status, second = _comparison_bytes(root, relative, len(expected), platform_name="nt")
        if second_status == "unavailable":
            result = AtomicWriteResult("unavailable", "not_committed", "unknown", cleanup)
        elif second != expected:
            result = AtomicWriteResult("conflict", "not_committed", "unknown", cleanup)
        else:
            try:
                os.replace(temporary, target)
            except OSError:
                result = _reconcile_replace(
                    root,
                    relative,
                    expected,
                    replacement,
                    platform_name="nt",
                )
            else:
                temporary = None
                result = AtomicWriteResult("replaced", "committed", "file_only", cleanup)
    except OSError:
        pass
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if temporary is not None:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass
            except OSError:
                cleanup = "residue"
    if cleanup != result.cleanup:
        result = AtomicWriteResult(result.outcome, result.namespace_state, result.durability, cleanup)
    return result


def atomic_replace_relative_if_equal(
    root: Path,
    relative_path: str | Path,
    expected: bytes,
    replacement: bytes,
    *,
    platform_name: str | None = None,
    allow_file_only: bool = False,
) -> AtomicWriteResult:
    """Replace a relative file after an equality check inside the caller's LDVH lock."""

    relative = _normal_relative_path(relative_path)
    selected_platform = os.name if platform_name is None else platform_name
    if selected_platform == "nt":
        if not allow_file_only:
            return AtomicWriteResult("unavailable", "not_committed", "unknown", "clean")
        return _atomic_replace_portable(root, relative, expected, replacement)
    if selected_platform == "posix":
        return _atomic_replace_posix(root, relative, expected, replacement)
    return AtomicWriteResult("unavailable", "not_committed", "unknown", "clean")


def _remove_posix(root: Path, relative: Path, expected: bytes) -> AtomicWriteResult:
    status, observed = _comparison_bytes(root, relative, len(expected), platform_name="posix")
    if status == "unavailable":
        return AtomicWriteResult("unavailable", "not_committed", "unknown", "clean")
    if observed != expected:
        return AtomicWriteResult("conflict", "not_committed", "unknown", "clean")
    directory_fd: int | None = None
    try:
        directory_fd = _open_relative_directory_posix(root, relative.parent, create=False)
        os.unlink(relative.name, dir_fd=directory_fd)
    except OSError:
        if directory_fd is not None:
            os.close(directory_fd)
        return AtomicWriteResult("unavailable", "uncertain", "unknown", "clean")
    try:
        os.fsync(directory_fd)
    except OSError:
        return AtomicWriteResult("removed", "committed", "unknown", "clean")
    finally:
        os.close(directory_fd)
    return AtomicWriteResult("removed", "committed", "file_and_directory", "clean")


def _remove_portable(root: Path, relative: Path, expected: bytes) -> AtomicWriteResult:
    status, observed = _comparison_bytes(root, relative, len(expected), platform_name="nt")
    if status == "unavailable":
        return AtomicWriteResult("unavailable", "not_committed", "unknown", "clean")
    if observed != expected:
        return AtomicWriteResult("conflict", "not_committed", "unknown", "clean")
    try:
        directory = _ensure_relative_directory_portable(root, relative.parent, directory_mode=0o755)
        (directory / relative.name).unlink()
    except OSError:
        return AtomicWriteResult("unavailable", "uncertain", "unknown", "clean")
    return AtomicWriteResult("removed", "committed", "file_only", "clean")


def remove_relative_if_equal(
    root: Path,
    relative_path: str | Path,
    expected: bytes,
    *,
    platform_name: str | None = None,
    allow_file_only: bool = False,
) -> AtomicWriteResult:
    """Remove a relative file only if it still equals the caller's expected bytes."""

    relative = _normal_relative_path(relative_path)
    selected_platform = os.name if platform_name is None else platform_name
    if selected_platform == "nt":
        if not allow_file_only:
            return AtomicWriteResult("unavailable", "not_committed", "unknown", "clean")
        return _remove_portable(root, relative, expected)
    if selected_platform == "posix":
        return _remove_posix(root, relative, expected)
    return AtomicWriteResult("unavailable", "not_committed", "unknown", "clean")


def walk_regular_files(root: Path) -> tuple[Path, ...]:
    """Walk a directory tree without descending through link/reparse entries."""

    root_observation = root.lstat()
    if is_link_or_reparse(root_observation) or not stat.S_ISDIR(root_observation.st_mode):
        raise UnsafePathError("walk root must be a non-reparse directory")
    root_signature = _portable_signature(root_observation)
    files: list[Path] = []
    pending = [(root, root_signature)]
    while pending:
        directory, expected_signature = pending.pop()
        before = directory.lstat()
        if is_link_or_reparse(before) or not stat.S_ISDIR(before.st_mode):
            raise UnsafePathError("walk path contains an unsafe directory")
        before_signature = _portable_signature(before)
        if before_signature != expected_signature:
            raise PathChangedError("directory changed before it was enumerated")
        with os.scandir(directory) as entries:
            current_entries = tuple(entries)
        after = directory.lstat()
        if before_signature != _portable_signature(after):
            raise PathChangedError("directory changed while it was enumerated")
        for entry in current_entries:
            observation = entry.stat(follow_symlinks=False)
            if is_link_or_reparse(observation):
                raise UnsafePathError("walk path contains a symbolic link or reparse point")
            path = Path(entry.path)
            if stat.S_ISDIR(observation.st_mode):
                pending.append((path, _portable_signature(observation)))
            elif stat.S_ISREG(observation.st_mode):
                files.append(path)
            else:
                raise UnsafePathError("walk path contains an unsupported file type")
    if root_signature != _portable_signature(root.lstat()):
        raise PathChangedError("walk root changed while it was enumerated")
    return tuple(sorted(files, key=lambda path: path.relative_to(root).as_posix()))
