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
from ldvh.facts.repository import FactReadResult
from ldvh.facts.schema import FactSchema
from ldvh.filesystem import safe_list_directory


@dataclass(frozen=True, slots=True)
class FactCandidateSnapshot:
    index: ProjectFactIndex
    keys: tuple[tuple[str, str], ...]
    structural_problems: tuple[dict[str, object], ...]
    complete: bool
    schema_fingerprint: str
    object_set_fingerprint: str


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


__all__ = ["FactCandidateSnapshot", "discover_fact_candidates"]
