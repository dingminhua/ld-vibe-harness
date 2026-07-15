"""Freeze and verify the closed set of 92 V3 fact-object migration inputs.

This module is deliberately read-only.  It does not interpret V3 semantics,
allocate V4 identities, or write fact instances.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from ruamel.yaml import YAML

SNAPSHOT_COMMIT = "5c885d55a1b3fc511672f9b1007880d283382502"
SNAPSHOT_TREE = "61fcd28ee85b8ae38956c644926a491006509628"
SOURCE_ROOT = PurePosixPath("archive/v3/ldvh-base")
EXPECTED_COUNTS = {"spark": 49, "workcase": 24, "study": 17, "pitfall": 2, "adr": 0}
EXPECTED_STATUSES = {
    "spark": {"pending": 46, "resolved": 2, "discarded": 1},
    "workcase": {
        "closed": 13,
        "subagents_plan_reviewing": 4,
        "human_plan_confirming": 2,
        "result_self_checking": 2,
        "human_closure_confirming": 3,
    },
    "study": {"active": 17},
    "pitfall": {"active": 2},
    "adr": {},
}
_LAYOUTS = {
    "spark": ("sparks", ".yaml", "yaml"),
    "workcase": ("workcases", ".yaml", "yaml"),
    "study": ("studies", ".md", "markdown"),
    "pitfall": ("pitfalls", ".yaml", "yaml"),
    "adr": ("adrs", ".yaml", "yaml"),
}
_ID = re.compile(r"(spark|workcase|study|pitfall|adr)-[0-9]{4,}\Z")
_ENTRY_KEYS = {
    "source_key",
    "source_type",
    "source_id",
    "source_status",
    "source_path",
    "carrier",
    "byte_size",
    "sha256",
    "git_blob_oid",
    "snapshot_commit",
    "source_times",
}


@dataclass(frozen=True, slots=True)
class BaselineIssue:
    code: str
    summary: str
    source_path: str | None = None


@dataclass(frozen=True, slots=True)
class BaselineVerification:
    entry_count: int
    issues: tuple[BaselineIssue, ...]

    @property
    def valid(self) -> bool:
        return not self.issues


def _git(repository_root: Path, *args: str) -> bytes:
    completed = subprocess.run(
        ["git", *args],
        cwd=repository_root,
        check=False,
        capture_output=True,
        timeout=30,
    )
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"git {' '.join(args)} failed: {detail}")
    return completed.stdout


def _frontmatter(raw: bytes, carrier: str) -> dict[str, Any]:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("source is not UTF-8") from exc
    yaml_text = text
    if carrier == "markdown":
        if not text.startswith("---\n"):
            raise ValueError("Markdown source has no opening frontmatter delimiter")
        parts = text.split("---", 2)
        if len(parts) != 3:
            raise ValueError("Markdown source has no closing frontmatter delimiter")
        yaml_text = parts[1]
    loader = YAML(typ="safe")
    try:
        loaded = loader.load(yaml_text)
    except Exception as exc:  # ruamel exposes several parser-specific subclasses
        raise ValueError(f"source cannot be parsed as YAML: {exc}") from exc
    if not isinstance(loaded, dict) or any(not isinstance(key, str) for key in loaded):
        raise ValueError("source frontmatter must be a string-keyed mapping")
    return loaded


def _terminal_time(fields: dict[str, Any]) -> dict[str, str] | None:
    for name in ("closed_at", "resolved_at"):
        value = fields.get(name)
        if isinstance(value, str) and value:
            return {"field": name, "value": value}
    return None


def _valid_source_id(fact_type: str, source_id: object) -> bool:
    if not isinstance(source_id, str):
        return False
    match = _ID.fullmatch(source_id)
    return match is not None and match.group(1) == fact_type


def _source_files(repository_root: Path) -> list[tuple[str, Path, str]]:
    source_root = repository_root / SOURCE_ROOT
    found: list[tuple[str, Path, str]] = []
    for fact_type, (directory, suffix, carrier) in _LAYOUTS.items():
        parent = source_root / directory
        if not parent.exists():
            if EXPECTED_COUNTS[fact_type]:
                raise ValueError(f"missing V3 source directory: {parent}")
            continue
        if parent.is_symlink() or not parent.is_dir():
            raise ValueError(f"V3 source directory is not a regular directory: {parent}")
        for path in sorted(parent.iterdir(), key=lambda item: item.name):
            if path.name == ".DS_Store":
                continue
            if path.is_symlink() or not path.is_file() or path.suffix != suffix:
                raise ValueError(f"unexpected V3 source member: {path}")
            found.append((fact_type, path, carrier))
    return found


def build_v3_baseline(repository_root: Path) -> dict[str, Any]:
    """Build the canonical in-memory manifest from the frozen source tree."""

    repository_root = repository_root.resolve()
    commit = _git(repository_root, "rev-parse", "--verify", f"{SNAPSHOT_COMMIT}^{{commit}}").decode().strip()
    tree = _git(repository_root, "rev-parse", f"{commit}:{SOURCE_ROOT.as_posix()}").decode().strip()
    if commit != SNAPSHOT_COMMIT or tree != SNAPSHOT_TREE:
        raise ValueError("configured V3 snapshot commit or tree does not match the reviewed baseline")
    head_tree = _git(repository_root, "rev-parse", f"HEAD:{SOURCE_ROOT.as_posix()}").decode().strip()
    if head_tree != SNAPSHOT_TREE:
        raise ValueError("current HEAD no longer contains the reviewed V3 source tree")
    source_status = _git(
        repository_root,
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
        "--",
        SOURCE_ROOT.as_posix(),
    )
    if source_status:
        raise ValueError("archive/v3 source tree has working-tree modifications or untracked members")
    entries: list[dict[str, Any]] = []
    for fact_type, path, carrier in _source_files(repository_root):
        relative = path.relative_to(repository_root).as_posix()
        raw = path.read_bytes()
        frozen_raw = _git(repository_root, "show", f"{SNAPSHOT_COMMIT}:{relative}")
        if raw != frozen_raw:
            raise ValueError(f"working source differs from frozen Git blob: {relative}")
        fields = _frontmatter(raw, carrier)
        source_id = fields.get("id")
        status = fields.get("status")
        if not isinstance(source_id, str) or not isinstance(status, str):
            raise ValueError(f"source lacks string id/status: {relative}")
        source_stem = path.name.removesuffix(path.suffix)
        if (
            not (source_stem == source_id or source_stem.startswith(f"{source_id}-"))
            or fields.get("type") != fact_type
            or not _valid_source_id(fact_type, source_id)
        ):
            raise ValueError(f"source path, id, or type disagree: {relative}")
        blob_oid = _git(repository_root, "rev-parse", f"{SNAPSHOT_COMMIT}:{relative}").decode().strip()
        entries.append(
            {
                "source_key": f"{fact_type}:{source_id}",
                "source_type": fact_type,
                "source_id": source_id,
                "source_status": status,
                "source_path": relative,
                "carrier": carrier,
                "byte_size": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "git_blob_oid": blob_oid,
                "snapshot_commit": SNAPSHOT_COMMIT,
                "source_times": {
                    "created": fields.get("created"),
                    "updated": fields.get("updated"),
                    "terminal": _terminal_time(fields),
                },
            }
        )
    entries.sort(key=lambda entry: entry["source_key"])
    return {
        "schema_version": 1,
        "source_root": SOURCE_ROOT.as_posix(),
        "snapshot_commit": SNAPSHOT_COMMIT,
        "snapshot_tree": SNAPSHOT_TREE,
        "expected_counts": EXPECTED_COUNTS,
        "expected_statuses": EXPECTED_STATUSES,
        "entries": entries,
    }


def render_v3_baseline(repository_root: Path) -> str:
    return json.dumps(build_v3_baseline(repository_root), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _issue(code: str, summary: str, path: object = None) -> BaselineIssue:
    return BaselineIssue(code, summary, path if isinstance(path, str) else None)


def verify_v3_baseline(repository_root: Path, manifest_path: Path) -> BaselineVerification:
    """Verify manifest shape, frozen Git identity, working bytes, and closed-set coverage."""

    repository_root = repository_root.resolve()
    issues: list[BaselineIssue] = []
    try:
        raw_manifest = manifest_path.read_bytes()
        manifest_text = raw_manifest.decode("utf-8")

        def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
            result: dict[str, Any] = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError(f"duplicate JSON key: {key}")
                result[key] = value
            return result

        loaded = json.loads(manifest_text, object_pairs_hook=unique_object)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        return BaselineVerification(0, (_issue("manifest", f"cannot read baseline manifest: {exc}"),))
    if not isinstance(loaded, dict):
        return BaselineVerification(0, (_issue("manifest", "baseline manifest must be an object"),))
    expected_top = {
        "schema_version",
        "source_root",
        "snapshot_commit",
        "snapshot_tree",
        "expected_counts",
        "expected_statuses",
        "entries",
    }
    if set(loaded) != expected_top:
        issues.append(_issue("manifest", "baseline manifest top-level keys are not the closed schema"))
    if loaded.get("schema_version") != 1:
        issues.append(_issue("manifest", "unsupported baseline schema_version"))
    if loaded.get("source_root") != SOURCE_ROOT.as_posix():
        issues.append(_issue("manifest", "source_root differs from the reviewed archive path"))
    if loaded.get("snapshot_commit") != SNAPSHOT_COMMIT or loaded.get("snapshot_tree") != SNAPSHOT_TREE:
        issues.append(_issue("manifest", "snapshot commit/tree differs from the reviewed baseline"))
    if loaded.get("expected_counts") != EXPECTED_COUNTS or loaded.get("expected_statuses") != EXPECTED_STATUSES:
        issues.append(_issue("manifest", "count or status expectations differ from the reviewed closed set"))
    canonical_manifest = json.dumps(loaded, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    if raw_manifest != canonical_manifest:
        issues.append(_issue("manifest", "baseline manifest bytes are not the unique canonical JSON encoding"))
    entries = loaded.get("entries")
    if not isinstance(entries, list):
        return BaselineVerification(0, (*issues, _issue("manifest", "entries must be an array")))
    keys: list[str] = []
    paths: list[str] = []
    counts = {key: 0 for key in EXPECTED_COUNTS}
    statuses = {key: {} for key in EXPECTED_STATUSES}
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict) or set(entry) != _ENTRY_KEYS:
            issues.append(_issue("manifest", f"entry {index} does not match the closed entry schema"))
            continue
        source_key = entry.get("source_key")
        source_type = entry.get("source_type")
        source_id = entry.get("source_id")
        source_path = entry.get("source_path")
        if not all(isinstance(value, str) for value in (source_key, source_type, source_id, source_path)):
            issues.append(_issue("manifest", f"entry {index} identity fields must be strings"))
            continue
        keys.append(source_key)
        paths.append(source_path)
        if source_key != f"{source_type}:{source_id}":
            issues.append(_issue("identity", "source_key does not equal type:id", source_path))
        if source_type not in _LAYOUTS or not _valid_source_id(source_type, source_id):
            issues.append(_issue("identity", "source type or id is outside the reviewed layouts", source_path))
            continue
        directory, suffix, carrier = _LAYOUTS[source_type]
        source_posix = PurePosixPath(source_path)
        source_stem = source_posix.name.removesuffix(suffix)
        if (
            source_posix.parent != SOURCE_ROOT / directory
            or not (source_stem == source_id or source_stem.startswith(f"{source_id}-"))
            or entry.get("carrier") != carrier
        ):
            issues.append(_issue("identity", "source path or carrier disagrees with type/id", source_path))
        counts[source_type] += 1
        status = entry.get("source_status")
        if isinstance(status, str):
            statuses[source_type][status] = statuses[source_type].get(status, 0) + 1
        else:
            issues.append(_issue("manifest", "source_status must be a string", source_path))
    if len(entries) != 92 or counts != EXPECTED_COUNTS or statuses != EXPECTED_STATUSES:
        issues.append(
            _issue("coverage", "entry count, type counts, or status distribution is not the frozen 92-item set")
        )
    if keys != sorted(keys) or len(keys) != len(set(keys)) or len(paths) != len(set(paths)):
        issues.append(_issue("coverage", "source keys must be sorted and source keys/paths unique"))
    try:
        generated = build_v3_baseline(repository_root)
    except (OSError, RuntimeError, ValueError) as exc:
        issues.append(_issue("source", str(exc)))
    else:
        if loaded != generated:
            issues.append(
                _issue("drift", "checked-in manifest differs from the current frozen Git/working-tree projection")
            )
    return BaselineVerification(len(entries), tuple(issues))


__all__ = [
    "BaselineIssue",
    "BaselineVerification",
    "build_v3_baseline",
    "render_v3_baseline",
    "verify_v3_baseline",
]
