"""Direct discovery snapshot for current authoritative fact objects."""

from __future__ import annotations

import hashlib
import json
import stat
from dataclasses import dataclass
from pathlib import Path

from ldvh.facts.contracts import LAYOUTS
from ldvh.facts.creation import schema_fingerprint
from ldvh.facts.project_validation import stabilize_project_index
from ldvh.facts.relations import MAX_GRAPH_OBJECTS, ProjectFactIndex
from ldvh.facts.repository import FactReadResult, _identity_issue
from ldvh.facts.schema import FactSchema
from ldvh.filesystem import safe_list_directory

MAX_WEB_FACT_AGGREGATE_BYTES = 16 * 1024 * 1024


@dataclass(frozen=True, slots=True)
class FactCandidateSnapshot:
    index: ProjectFactIndex
    keys: tuple[tuple[str, str], ...]
    structural_problems: tuple[dict[str, object], ...]
    complete: bool
    schema_fingerprint: str
    object_set_fingerprint: str


@dataclass(frozen=True, slots=True)
class FactTypeRawSnapshot:
    fact_type_key: str
    objects: tuple[tuple[str, FactReadResult], ...]
    structural_problems: tuple[dict[str, object], ...]
    coverage_complete: bool


def _digest(value: object) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _read_fingerprint(path: Path, read: FactReadResult) -> dict[str, object]:
    try:
        observed = path.lstat()
        metadata: object = {
            "mode": stat.S_IFMT(observed.st_mode),
            "size": observed.st_size,
            "mtime_ns": observed.st_mtime_ns,
        }
    except OSError as error:
        metadata = {"error": type(error).__name__}
    return {
        "path": read.canonical_path,
        "metadata": metadata,
        "status": read.check_status,
        "fields": read.fields,
        "body": read.body,
        "issues": [
            {"category": issue.category, "field_path": issue.field_path, "summary": issue.summary}
            for issue in read.issues
        ],
    }


def _structural_problem(fact_type_key: str, canonical_path: str, summary: str) -> dict[str, object]:
    return {
        "fact_type_key": fact_type_key,
        "canonical_path": canonical_path,
        "check_status": "unavailable",
        "issues": [{"category": "location", "field_path": None, "summary": summary}],
    }


def discover_fact_candidates(
    root: Path,
    project_id: str,
    common_dir: Path,
    schemas: dict[str, FactSchema],
) -> FactCandidateSnapshot:
    """Scan canonical identities once and bind the snapshot to content-sensitive fingerprints."""

    index = ProjectFactIndex(root, project_id, schemas, common_dir)
    keys: list[tuple[str, str]] = []
    structural: list[dict[str, object]] = []
    complete = True
    budget_exhausted = False
    for fact_type_key, layout in sorted(LAYOUTS.items()):
        if budget_exhausted:
            structural.append(
                _structural_problem(fact_type_key, layout.directory, "五类型扫描预算已耗尽，当前目录未枚举")
            )
            continue
        try:
            paths = sorted(safe_list_directory(root, layout.directory), key=lambda item: item.name)
        except FileNotFoundError:
            continue
        except OSError:
            structural.append(
                _structural_problem(fact_type_key, layout.directory, "事实类型目录必须是非 link/reparse 可安全枚举目录")
            )
            complete = False
            continue
        for path in paths:
            if path.suffix != layout.suffix:
                continue
            object_id = path.name.removesuffix(layout.suffix)
            if layout.object_id_pattern.fullmatch(object_id) is None:
                continue
            if len(keys) >= MAX_GRAPH_OBJECTS:
                structural.append(
                    _structural_problem(
                        fact_type_key,
                        layout.directory,
                        "五类型 canonical 身份文件超过 10,000 个扫描预算",
                    )
                )
                complete = False
                budget_exhausted = True
                break
            keys.append((fact_type_key, object_id))
            index.read(fact_type_key, object_id)
    stabilize_project_index(index)
    reads = [(fact_type, object_id, index.cache[(fact_type, object_id)]) for fact_type, object_id in keys]
    fingerprint_rows = [_read_fingerprint(root / read.canonical_path, read) for _, _, read in reads]
    fingerprint_rows.extend(structural)
    combined_schema = _digest({key: schema_fingerprint(schemas[key]) for key in sorted(schemas)})
    return FactCandidateSnapshot(
        index,
        tuple(keys),
        tuple(structural),
        complete,
        combined_schema,
        _digest(fingerprint_rows),
    )


def discover_fact_type_raw(
    root: Path,
    project_id: str,
    common_dir: Path,
    schemas: dict[str, FactSchema],
    fact_type_key: str,
    *,
    aggregate_budget_bytes: int | None = None,
) -> FactTypeRawSnapshot:
    """Read one complete canonical directory without filtering invalid objects."""

    layout = LAYOUTS[fact_type_key]
    schema = schemas.get(fact_type_key)
    if schema is None:
        return FactTypeRawSnapshot(
            fact_type_key,
            (),
            (_structural_problem(fact_type_key, layout.directory, "事实类型 Schema 不可用"),),
            False,
        )
    identity_issue, _ = _identity_issue(root, common_dir)
    if identity_issue is not None:
        return FactTypeRawSnapshot(
            fact_type_key,
            (),
            (_structural_problem(fact_type_key, layout.directory, identity_issue.summary),),
            False,
        )

    def listing() -> tuple[Path, ...] | None:
        try:
            return tuple(sorted(safe_list_directory(root, layout.directory), key=lambda item: item.name))
        except FileNotFoundError:
            return ()
        except OSError:
            return None

    before = listing()
    if before is None:
        return FactTypeRawSnapshot(
            fact_type_key,
            (),
            (_structural_problem(fact_type_key, layout.directory, "事实类型目录无法安全完整枚举"),),
            False,
        )
    relevant = tuple(path for path in before if path.suffix == layout.suffix)
    structural: list[dict[str, object]] = []
    canonical: list[tuple[str, Path]] = []
    if len(relevant) > MAX_GRAPH_OBJECTS:
        structural.append(
            _structural_problem(fact_type_key, layout.directory, "当前事实类型超过 10,000 个载体扫描预算")
        )
        return FactTypeRawSnapshot(fact_type_key, (), tuple(structural), False)
    for path in relevant:
        object_id = path.name.removesuffix(layout.suffix)
        if layout.object_id_pattern.fullmatch(object_id) is None:
            structural.append(_structural_problem(fact_type_key, path.name, "事实文件名不是 canonical fact identity"))
        else:
            canonical.append((object_id, path))
    index = ProjectFactIndex(
        root,
        project_id,
        schemas,
        common_dir,
        aggregate_budget_bytes,
    )
    base_objects: list[tuple[str, FactReadResult]] = []
    for object_id, _ in canonical:
        read = index.read(fact_type_key, object_id)
        if read is None:
            structural.append(_structural_problem(fact_type_key, object_id, "canonical 事实对象无法读取"))
            continue
        base_objects.append((object_id, read))
        if index.aggregate_budget_exhausted:
            structural.append(
                _structural_problem(
                    fact_type_key,
                    layout.directory,
                    f"事实类型安全读取超过 {aggregate_budget_bytes} bytes 聚合预算",
                )
            )
            break
    stabilize_project_index(index)
    if index.aggregate_budget_exhausted and not any("聚合预算" in str(problem) for problem in structural):
        structural.append(
            _structural_problem(
                fact_type_key,
                layout.directory,
                f"事实类型关系校验超过 {aggregate_budget_bytes} bytes 聚合预算",
            )
        )
    objects = tuple(
        (object_id, index.cache.get((fact_type_key, object_id), base_read)) for object_id, base_read in base_objects
    )
    after = listing()
    identity_after, _ = _identity_issue(root, common_dir)
    stable_listing = after is not None and tuple(path.name for path in before) == tuple(path.name for path in after)
    complete = stable_listing and identity_after is None and not structural
    if not stable_listing:
        structural.append(_structural_problem(fact_type_key, layout.directory, "事实目录在扫描期间发生变化"))
    if identity_after is not None:
        structural.append(_structural_problem(fact_type_key, layout.directory, identity_after.summary))
    return FactTypeRawSnapshot(fact_type_key, objects, tuple(structural), complete)


__all__ = [
    "FactCandidateSnapshot",
    "FactTypeRawSnapshot",
    "MAX_WEB_FACT_AGGREGATE_BYTES",
    "discover_fact_candidates",
    "discover_fact_type_raw",
]
