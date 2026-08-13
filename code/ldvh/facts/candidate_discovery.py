"""Direct discovery snapshot for current authoritative fact objects."""

from __future__ import annotations

import hashlib
import json
import stat
from dataclasses import dataclass
from pathlib import Path

from ldvh.facts.contracts import LAYOUTS, is_ignored_fact_type_root_entry
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
        "content_fingerprint": read.content_fingerprint,
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
    *,
    index: ProjectFactIndex | None = None,
) -> FactCandidateSnapshot:
    """Scan canonical identities once and bind the snapshot to content-sensitive fingerprints."""

    index = index or ProjectFactIndex(root, project_id, schemas, common_dir)
    keys: list[tuple[str, str]] = []
    structural: list[dict[str, object]] = []
    complete = True
    budget_exhausted = False
    scanned_canonical_identities = 0
    for fact_type_key, layout in sorted(LAYOUTS.items()):
        if budget_exhausted:
            structural.append(
                _structural_problem(
                    fact_type_key,
                    layout.directory,
                    "五类事实对象的扫描预算已耗尽，当前目录未被枚举",
                )
            )
            continue
        try:
            paths = sorted(safe_list_directory(root, layout.directory), key=lambda item: item.name)
        except FileNotFoundError:
            structural.append(
                _structural_problem(
                    fact_type_key,
                    layout.directory,
                    "事实类型目录缺失，无法证明当前项目的对象集合完整",
                )
            )
            complete = False
            continue
        except OSError:
            structural.append(
                _structural_problem(
                    fact_type_key,
                    layout.directory,
                    "事实类型目录不得包含符号链接或重解析点，并且必须能够安全、完整地枚举",
                )
            )
            complete = False
            continue
        for path in paths:
            try:
                if is_ignored_fact_type_root_entry(path):
                    continue
            except OSError:
                structural.append(
                    _structural_problem(
                        fact_type_key,
                        f"{layout.directory}/{path.name}",
                        "平台元数据候选无法安全观察，不能证明当前事实类型目录完整",
                    )
                )
                complete = False
                continue
            object_id = path.name.removesuffix(layout.suffix)
            canonical_shape = (
                path.suffix == layout.suffix
                and layout.object_id_pattern.fullmatch(object_id) is not None
            )
            if not canonical_shape:
                structural.append(
                    _structural_problem(
                        fact_type_key,
                        f"{layout.directory}/{path.name}",
                        "该载体不符合当前事实类型的权威文件路径与对象身份规则",
                    )
                )
                complete = False
                continue
            if scanned_canonical_identities >= MAX_GRAPH_OBJECTS:
                structural.append(
                    _structural_problem(
                        fact_type_key,
                        layout.directory,
                        "权威身份文件总数已超过本次最多扫描 10,000 个的上限",
                    )
                )
                complete = False
                budget_exhausted = True
                break
            scanned_canonical_identities += 1
            keys.append((fact_type_key, object_id))
            index.read(fact_type_key, object_id)
    stabilize_project_index(index, keys)
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


__all__ = [
    "FactCandidateSnapshot",
    "discover_fact_candidates",
]
