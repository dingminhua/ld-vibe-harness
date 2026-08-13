"""Source-derived draft fingerprints, shared fact-write locking, and atomic creation."""

from __future__ import annotations

import errno
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
from ldvh.facts.schema import FactSchema
from ldvh.filesystem import (
    AtomicWriteResult,
    atomic_create_relative,
    exclusive_relative_file_lock,
    remove_relative_if_equal,
)


@dataclass(frozen=True, slots=True)
class CreationBoundary:
    governed_project_id: str
    worktree_root: Path
    git_common_dir: Path


class FactCoordinationUnavailable(RuntimeError):
    """A controlled write could not enter its durable shared coordination domain."""

    stage = "common_dir_lock"
    path_role = "git_common_dir_ldvh_coordination_root"
    required_access = "create_or_open_and_exclusively_lock"

    def __init__(self, system_error_category: Literal["permission_denied", "read_only_filesystem"]) -> None:
        super().__init__("controlled fact coordination is unavailable")
        self.system_error_category = system_error_category


def schema_fingerprint(schema: FactSchema) -> str:
    payload = [
        (
            field.path,
            field.json_type,
            field.presence,
            field.value_structure,
            field.definition_ref,
            field.constraint_ref,
        )
        for field in schema.fields
    ]
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


@contextmanager
def fact_write_lock(boundary: CreationBoundary, layout: FactTypeLayout) -> Iterator[None]:
    """Serialize one project's writes for a fact type without allocating an ID."""

    project_hash = hashlib.sha256(boundary.governed_project_id.encode()).hexdigest()[:24]
    lock_path = Path("ldvh") / "fact-creation-locks" / f"{project_hash}-{layout.fact_type_key}.lock"
    entered = False
    try:
        with exclusive_relative_file_lock(boundary.git_common_dir, lock_path):
            entered = True
            yield
    except OSError as error:
        if entered:
            raise
        if error.errno == errno.EROFS:
            raise FactCoordinationUnavailable("read_only_filesystem") from error
        if isinstance(error, PermissionError) or error.errno in {errno.EACCES, errno.EPERM}:
            raise FactCoordinationUnavailable("permission_denied") from error
        raise


def serialize_fact_object(layout: FactTypeLayout, fields: dict[str, object], body: str | None) -> str:
    yaml = YAML(typ="rt")
    yaml.default_flow_style = False
    yaml.allow_unicode = True
    yaml.width = 2**31 - 1
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
    "FactCoordinationUnavailable",
    "atomic_create_text",
    "fact_write_lock",
    "rollback_created_text",
    "schema_fingerprint",
    "serialize_fact_object",
    "worktree_fingerprint",
]
