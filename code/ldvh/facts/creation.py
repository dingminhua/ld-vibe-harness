"""Source-derived draft fingerprints, shared ID allocation, and atomic creation."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from io import StringIO
from pathlib import Path

from ruamel.yaml import YAML

from ldvh.facts.contracts import FactTypeLayout
from ldvh.facts.repository import _git
from ldvh.facts.schema import FactSchema
from ldvh.filesystem import (
    AtomicWriteResult,
    atomic_create_relative,
    atomic_store_relative,
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
    try:
        raw = safe_read_relative(root, relative_path).decode("ascii").strip()
    except FileNotFoundError:
        return 0
    except (OSError, UnicodeError):
        return None
    return int(raw) if raw.isdigit() else None


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
    if counter_path != _allocator_relative_paths(boundary, layout)[1]:
        return None
    visible = _max_visible_id(boundary, layout)
    counter = _read_counter(boundary.git_common_dir, counter_path)
    if visible is None or counter is None:
        return None
    allocated = max(visible, counter) + 1
    payload = f"{allocated}\n".encode("ascii")
    stored = atomic_store_relative(boundary.git_common_dir, counter_path, payload)
    if stored.namespace_state != "committed":
        return None
    try:
        observed = safe_read_relative(boundary.git_common_dir, counter_path)
    except OSError:
        return None
    return f"{layout.fact_type_key}-{allocated:04d}" if observed == payload else None


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
