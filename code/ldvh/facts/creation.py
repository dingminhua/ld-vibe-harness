"""Source-derived draft fingerprints, shared ID allocation, and atomic creation."""

from __future__ import annotations

import errno
import fcntl
import hashlib
import json
import os
import secrets
import stat
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from io import StringIO
from pathlib import Path

from ruamel.yaml import YAML

from ldvh.facts.contracts import FactTypeLayout
from ldvh.facts.repository import _git
from ldvh.facts.schema import FactSchema


@dataclass(frozen=True, slots=True)
class CreationBoundary:
    governed_project_id: str
    worktree_root: Path
    git_common_dir: Path


def schema_fingerprint(schema: FactSchema) -> str:
    payload = [(field.path, field.json_type, field.presence, field.value_structure) for field in schema.fields]
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def worktree_fingerprint(boundary: CreationBoundary) -> str:
    payload = "\0".join(
        (
            boundary.governed_project_id,
            boundary.worktree_root.resolve().as_posix(),
            boundary.git_common_dir.resolve().as_posix(),
        )
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def _numeric_suffix(layout: FactTypeLayout, path: Path) -> int | None:
    object_id = path.name.removesuffix(layout.suffix)
    if layout.object_id_pattern.fullmatch(object_id) is None:
        return None
    return int(object_id.rsplit("-", 1)[1])


def _visible_worktrees(boundary: CreationBoundary) -> tuple[Path, ...] | None:
    observed = _git(boundary.worktree_root, "worktree", "list", "--porcelain")
    if observed is None or observed.returncode != 0:
        return None
    roots = [
        Path(line.removeprefix("worktree ")) for line in observed.stdout.splitlines() if line.startswith("worktree ")
    ]
    return tuple(roots) if roots else (boundary.worktree_root,)


def _max_visible_id(boundary: CreationBoundary, layout: FactTypeLayout) -> int | None:
    roots = _visible_worktrees(boundary)
    if roots is None:
        return None
    maximum = 0
    for root in roots:
        directory = root / layout.directory
        try:
            if stat.S_ISLNK(directory.lstat().st_mode):
                return None
            paths = tuple(directory.iterdir())
        except FileNotFoundError:
            continue
        except OSError:
            return None
        for path in paths:
            suffix = _numeric_suffix(layout, path)
            if suffix is not None:
                maximum = max(maximum, suffix)
    return maximum


def _allocator_key(boundary: CreationBoundary, layout: FactTypeLayout) -> str:
    project_hash = hashlib.sha256(boundary.governed_project_id.encode()).hexdigest()[:24]
    return f"{project_hash}-{layout.fact_type_key}"


def _allocator_paths(boundary: CreationBoundary, layout: FactTypeLayout) -> tuple[Path, Path]:
    state = boundary.git_common_dir / "ldvh" / "fact-id-allocators"
    key = _allocator_key(boundary, layout)
    return state / f"{key}.lock", state / f"{key}.counter"


def _read_counter(path: Path) -> int | None:
    try:
        raw = path.read_text(encoding="ascii").strip()
    except FileNotFoundError:
        return 0
    except OSError:
        return None
    return int(raw) if raw.isdigit() else None


def candidate_object_id(boundary: CreationBoundary, layout: FactTypeLayout) -> str | None:
    visible = _max_visible_id(boundary, layout)
    _, counter_path = _allocator_paths(boundary, layout)
    counter = _read_counter(counter_path)
    if visible is None or counter is None:
        return None
    return f"{layout.fact_type_key}-{max(visible, counter) + 1:04d}"


@contextmanager
def allocation_lock(boundary: CreationBoundary, layout: FactTypeLayout) -> Iterator[Path]:
    lock_path, counter_path = _allocator_paths(boundary, layout)
    lock_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    descriptor = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        yield counter_path
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def allocate_object_id_locked(
    boundary: CreationBoundary,
    layout: FactTypeLayout,
    counter_path: Path,
) -> str | None:
    visible = _max_visible_id(boundary, layout)
    counter = _read_counter(counter_path)
    if visible is None or counter is None:
        return None
    allocated = max(visible, counter) + 1
    temporary = counter_path.with_name(f".{counter_path.name}.{secrets.token_hex(8)}.tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        os.write(descriptor, f"{allocated}\n".encode("ascii"))
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    os.replace(temporary, counter_path)
    directory_fd = os.open(counter_path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)
    return f"{layout.fact_type_key}-{allocated:04d}"


def serialize_fact_object(layout: FactTypeLayout, fields: dict[str, object], body: str | None) -> str:
    yaml = YAML(typ="rt")
    yaml.default_flow_style = False
    yaml.allow_unicode = True
    stream = StringIO()
    yaml.dump(fields, stream)
    frontmatter = stream.getvalue()
    if layout.carrier == "markdown":
        assert body is not None
        return f"---\n{frontmatter}---\n\n{body.rstrip()}\n"
    return frontmatter


def _open_creation_directory(root: Path, layout: FactTypeLayout) -> int:
    descriptor = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for segment in Path(layout.directory).parts:
            try:
                os.mkdir(segment, mode=0o755, dir_fd=descriptor)
            except FileExistsError:
                pass
            next_descriptor = os.open(
                segment,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                dir_fd=descriptor,
            )
            os.close(descriptor)
            descriptor = next_descriptor
        return descriptor
    except Exception:
        os.close(descriptor)
        raise


def atomic_create_text(root: Path, layout: FactTypeLayout, object_id: str, text: str) -> bool:
    directory_fd = _open_creation_directory(root, layout)
    temporary_name = f".ldvh-create-{secrets.token_hex(12)}.tmp"
    target_name = f"{object_id}{layout.suffix}"
    temporary_fd: int | None = None
    try:
        temporary_fd = os.open(
            temporary_name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o600,
            dir_fd=directory_fd,
        )
        payload = text.encode("utf-8")
        offset = 0
        while offset < len(payload):
            offset += os.write(temporary_fd, payload[offset:])
        os.fsync(temporary_fd)
        os.close(temporary_fd)
        temporary_fd = None
        try:
            os.link(
                temporary_name,
                target_name,
                src_dir_fd=directory_fd,
                dst_dir_fd=directory_fd,
                follow_symlinks=False,
            )
        except FileExistsError:
            return False
        os.fsync(directory_fd)
        return True
    finally:
        if temporary_fd is not None:
            os.close(temporary_fd)
        try:
            os.unlink(temporary_name, dir_fd=directory_fd)
        except FileNotFoundError:
            pass
        os.close(directory_fd)


def rollback_created_text(root: Path, layout: FactTypeLayout, object_id: str, expected_text: str) -> bool:
    directory_fd = _open_creation_directory(root, layout)
    target_name = f"{object_id}{layout.suffix}"
    try:
        descriptor = os.open(target_name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=directory_fd)
        try:
            observed = os.read(descriptor, len(expected_text.encode("utf-8")) + 1)
        finally:
            os.close(descriptor)
        if observed != expected_text.encode("utf-8"):
            return False
        os.unlink(target_name, dir_fd=directory_fd)
        os.fsync(directory_fd)
        return True
    except OSError as error:
        if error.errno in {errno.ENOENT, errno.ELOOP, errno.ENOTDIR}:
            return False
        return False
    finally:
        os.close(directory_fd)


__all__ = [
    "CreationBoundary",
    "allocate_object_id_locked",
    "allocation_lock",
    "atomic_create_text",
    "candidate_object_id",
    "rollback_created_text",
    "schema_fingerprint",
    "serialize_fact_object",
    "worktree_fingerprint",
]
