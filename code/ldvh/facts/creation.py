"""Source-derived draft fingerprints, shared ID allocation, and atomic creation."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from typing import Literal

from ruamel.yaml import YAML

from ldvh.facts.contracts import FactTypeLayout
from ldvh.facts.repository import _git
from ldvh.facts.schema import FactSchema
from ldvh.filesystem import (
    AtomicWriteResult,
    atomic_create_relative,
    atomic_replace_relative_if_equal,
    exclusive_relative_file_lock,
    remove_relative_if_equal,
    safe_list_directory,
    safe_read_relative,
)


@dataclass(frozen=True, slots=True)
class CreationBoundary:
    governed_project_id: str
    worktree_root: Path
    git_common_dir: Path


@dataclass(frozen=True, slots=True)
class AllocationPreview:
    counter_path: Path
    prior_counter_bytes: bytes | None
    visible_max: int
    sequence: int
    object_id: str
    counter_bytes: bytes


@dataclass(frozen=True, slots=True)
class AllocationCommitResult:
    status: Literal["committed", "stale", "unavailable", "uncertain"]
    object_id: str | None
    write_result: AtomicWriteResult | None = None


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
    try:
        output = observed.stdout.decode("utf-8")
    except UnicodeDecodeError:
        return None
    roots = [Path(line.removeprefix("worktree ")) for line in output.splitlines() if line.startswith("worktree ")]
    return tuple(roots) if roots else (boundary.worktree_root,)


def _max_visible_id(boundary: CreationBoundary, layout: FactTypeLayout) -> int | None:
    roots = _visible_worktrees(boundary)
    if roots is None:
        return None
    maximum = 0
    for root in roots:
        try:
            paths = safe_list_directory(root, layout.directory)
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


def _allocator_relative_paths(boundary: CreationBoundary, layout: FactTypeLayout) -> tuple[Path, Path]:
    state = Path("ldvh") / "fact-id-allocators"
    key = _allocator_key(boundary, layout)
    return state / f"{key}.lock", state / f"{key}.counter"


def _allocator_paths(boundary: CreationBoundary, layout: FactTypeLayout) -> tuple[Path, Path]:
    lock_path, counter_path = _allocator_relative_paths(boundary, layout)
    return boundary.git_common_dir / lock_path, boundary.git_common_dir / counter_path


def _read_counter(root: Path, relative_path: Path) -> int | None:
    observed = _read_counter_snapshot(root, relative_path)
    return None if observed is None else observed[0]


def _read_counter_snapshot(root: Path, relative_path: Path) -> tuple[int, bytes | None] | None:
    try:
        payload = safe_read_relative(root, relative_path)
    except FileNotFoundError:
        return 0, None
    except OSError:
        return None
    try:
        raw = payload.decode("ascii").strip()
    except UnicodeError:
        return None
    if not raw.isdigit():
        return None
    try:
        counter = int(raw)
    except ValueError:
        return None
    return counter, payload


def candidate_object_id(boundary: CreationBoundary, layout: FactTypeLayout) -> str | None:
    visible = _max_visible_id(boundary, layout)
    _, counter_path = _allocator_relative_paths(boundary, layout)
    counter = _read_counter(boundary.git_common_dir, counter_path)
    if visible is None or counter is None:
        return None
    return f"{layout.fact_type_key}-{max(visible, counter) + 1:04d}"


@contextmanager
def allocation_lock(boundary: CreationBoundary, layout: FactTypeLayout) -> Iterator[Path]:
    lock_path, counter_path = _allocator_relative_paths(boundary, layout)
    with exclusive_relative_file_lock(boundary.git_common_dir, lock_path):
        yield counter_path


def allocate_object_id_locked(
    boundary: CreationBoundary,
    layout: FactTypeLayout,
    counter_path: Path,
) -> str | None:
    preview = preview_object_id_locked(boundary, layout, counter_path)
    if preview is None:
        return None
    committed = commit_object_id_locked(boundary, layout, preview)
    return committed.object_id if committed.status == "committed" else None


def preview_object_id_locked(
    boundary: CreationBoundary,
    layout: FactTypeLayout,
    counter_path: Path,
) -> AllocationPreview | None:
    """Preview the next identity without mutating allocator state; caller holds the lock."""

    if counter_path != _allocator_relative_paths(boundary, layout)[1]:
        return None
    visible = _max_visible_id(boundary, layout)
    observed = _read_counter_snapshot(boundary.git_common_dir, counter_path)
    if visible is None or observed is None:
        return None
    counter, prior = observed
    sequence = max(visible, counter) + 1
    return AllocationPreview(
        counter_path,
        prior,
        visible,
        sequence,
        f"{layout.fact_type_key}-{sequence:04d}",
        f"{sequence}\n".encode("ascii"),
    )


def commit_object_id_locked(
    boundary: CreationBoundary,
    layout: FactTypeLayout,
    preview: AllocationPreview,
) -> AllocationCommitResult:
    """Conditionally commit one preview after revalidating all allocator observations."""

    current = preview_object_id_locked(boundary, layout, preview.counter_path)
    if current is None:
        return AllocationCommitResult("unavailable", None)
    if current != preview:
        return AllocationCommitResult("stale", None)
    if preview.prior_counter_bytes is None:
        stored = atomic_create_relative(
            boundary.git_common_dir,
            preview.counter_path,
            preview.counter_bytes,
        )
    else:
        stored = atomic_replace_relative_if_equal(
            boundary.git_common_dir,
            preview.counter_path,
            preview.prior_counter_bytes,
            preview.counter_bytes,
        )
    if stored.namespace_state == "uncertain":
        return AllocationCommitResult("uncertain", None, stored)
    if stored.namespace_state != "committed":
        status = "stale" if stored.outcome == "conflict" else "unavailable"
        return AllocationCommitResult(status, None, stored)
    try:
        observed = safe_read_relative(boundary.git_common_dir, preview.counter_path)
    except OSError:
        return AllocationCommitResult("uncertain", None, stored)
    if observed != preview.counter_bytes:
        return AllocationCommitResult("uncertain", None, stored)
    return AllocationCommitResult("committed", preview.object_id, stored)


def serialize_fact_object(layout: FactTypeLayout, fields: dict[str, object], body: str | None) -> str:
    yaml = YAML(typ="rt")
    yaml.default_flow_style = False
    yaml.allow_unicode = True
    stream = StringIO()
    yaml.dump(fields, stream)
    frontmatter = stream.getvalue()
    if layout.carrier == "markdown":
        assert body is not None
        normalized_body = body.rstrip()
        separator = "" if normalized_body.startswith("\n") else "\n"
        return f"---\n{frontmatter}---\n{separator}{normalized_body}\n"
    return frontmatter


def atomic_create_text(root: Path, layout: FactTypeLayout, object_id: str, text: str) -> AtomicWriteResult:
    return atomic_create_relative(root, layout.canonical_path(object_id), text.encode("utf-8"))


def rollback_created_text(
    root: Path,
    layout: FactTypeLayout,
    object_id: str,
    expected_text: str,
) -> AtomicWriteResult:
    return remove_relative_if_equal(root, layout.canonical_path(object_id), expected_text.encode("utf-8"))


__all__ = [
    "AllocationCommitResult",
    "AllocationPreview",
    "CreationBoundary",
    "allocate_object_id_locked",
    "allocation_lock",
    "atomic_create_text",
    "candidate_object_id",
    "commit_object_id_locked",
    "preview_object_id_locked",
    "rollback_created_text",
    "schema_fingerprint",
    "serialize_fact_object",
    "worktree_fingerprint",
]
