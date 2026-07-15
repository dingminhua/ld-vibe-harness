"""Build and verify the immutable rule snapshot carried by ordinary installs."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Literal

from ldvh.diagnostics import Issue, SourceLocation
from ldvh.filesystem import walk_regular_files
from ldvh.specs.audit_evidence import inspect_audit_evidence_locators
from ldvh.specs.discovery import Candidate, DiscoveryResult, discover_candidates, validate_non_ignored_git_path
from ldvh.specs.markdown import MarkdownResult, parse_markdown_bytes, read_observed_resource
from ldvh.specs.repository import RepositoryInspection, inspect_repository_source
from ldvh.specs.source import ObservedResource, RuleSourceIdentity

DISTRIBUTION_NAME = "ld-vibe-harness"
SNAPSHOT_FORMAT = "ldvh-rule-snapshot/1"
SNAPSHOT_DIRECTORY = "_rule_snapshot"
MANIFEST_NAME = "manifest.json"
_SPEC_NAME = re.compile(r"[0-9]{2,}-.+\.md\Z")
_ATTACHMENT_NAME = re.compile(r"[0-9]{2,}\.Att\.[0-9]{2,}-.+\.md\Z")
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_ROLES = frozenset({"rule_candidate", "mechanical_evidence"})


class SnapshotError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class SnapshotFile:
    path: str
    role: Literal["rule_candidate", "mechanical_evidence"]
    raw_bytes: bytes
    observed_at: str

    @property
    def size(self) -> int:
        return len(self.raw_bytes)

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.raw_bytes).hexdigest()


@dataclass(frozen=True, slots=True)
class SnapshotPlan:
    distribution: str
    version: str
    files: tuple[SnapshotFile, ...]
    manifest_bytes: bytes
    snapshot_sha256: str


@dataclass(frozen=True, slots=True)
class VerifiedSnapshot:
    root: Path
    distribution: str
    version: str
    files: tuple[SnapshotFile, ...]
    snapshot_sha256: str


def _json_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise SnapshotError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def _normal_path(value: str) -> bool:
    path = PurePosixPath(value)
    return (
        bool(value)
        and not value.startswith("/")
        and "\\" not in value
        and "//" not in value
        and all(part not in {"", ".", ".."} for part in path.parts)
        and path.as_posix() == value
    )


def _candidate_kind(path: str) -> Literal["spec", "attachment"] | None:
    parts = PurePosixPath(path).parts
    if len(parts) == 2 and parts[0] == "specs" and _SPEC_NAME.fullmatch(parts[1]):
        return "spec"
    if len(parts) == 3 and parts[:2] == ("specs", "attachments") and _ATTACHMENT_NAME.fullmatch(parts[2]):
        return "attachment"
    return None


def _manifest_payload(distribution: str, version: str, files: tuple[SnapshotFile, ...]) -> dict[str, Any]:
    return {
        "format": SNAPSHOT_FORMAT,
        "distribution": distribution,
        "version": version,
        "algorithm": "sha256",
        "files": [{"path": item.path, "role": item.role, "size": item.size, "sha256": item.sha256} for item in files],
    }


def make_snapshot_plan(distribution: str, version: str, files: tuple[SnapshotFile, ...]) -> SnapshotPlan:
    ordered = tuple(sorted(files, key=lambda item: (item.role, item.path)))
    if ordered != files:
        raise SnapshotError("snapshot files must be sorted by role and path")
    paths = [item.path for item in files]
    if len(paths) != len(set(paths)):
        raise SnapshotError("snapshot paths must be unique")
    for item in files:
        if item.role not in _ROLES or not _normal_path(item.path):
            raise SnapshotError(f"invalid snapshot member {item.path!r}")
        is_candidate = _candidate_kind(item.path) is not None
        if (item.role == "rule_candidate") != is_candidate:
            raise SnapshotError(f"snapshot role does not match path {item.path!r}")
    payload = _manifest_payload(distribution, version, files)
    snapshot_sha256 = hashlib.sha256(_canonical_json(payload)).hexdigest()
    manifest = {**payload, "snapshot_sha256": snapshot_sha256}
    return SnapshotPlan(distribution, version, files, _canonical_json(manifest) + b"\n", snapshot_sha256)


def _observe_worktree_plan(repository_root: Path, version: str) -> SnapshotPlan:
    discovery = discover_candidates(repository_root)
    if not discovery.complete:
        raise SnapshotError("cannot build a snapshot from an incomplete Working Tree discovery")
    observed_candidates: dict[str, ObservedResource] = {
        candidate.relative_path: read_observed_resource(candidate.absolute_path, candidate.relative_path)
        for candidate in discovery.candidates
    }
    markdown_results = {
        path: parse_markdown_bytes(item.raw_bytes, path, observed_at=item.observed_at)
        for path, item in observed_candidates.items()
    }
    identity = RuleSourceIdentity("working_tree", git_worktree_root=discovery.repository_root)
    first = inspect_repository_source(discovery, identity, markdown_results=markdown_results)
    locators = inspect_audit_evidence_locators(first.parsed_documents)
    if locators.issues:
        raise SnapshotError("cannot resolve mechanical evidence from the current rule source")
    observed_evidence: dict[str, ObservedResource] = {}
    evidence_results: dict[str, MarkdownResult] = {}
    for locator in locators.locators:
        issue = validate_non_ignored_git_path(discovery.repository_root, locator.canonical_path)
        if issue is not None:
            raise SnapshotError(issue.summary)
        observed = read_observed_resource(
            discovery.repository_root / locator.canonical_path,
            locator.canonical_path,
        )
        observed_evidence[locator.canonical_path] = observed
        evidence_results[locator.canonical_path] = parse_markdown_bytes(
            observed.raw_bytes,
            locator.canonical_path,
            observed_at=observed.observed_at,
        )
    final = inspect_repository_source(
        discovery,
        identity,
        markdown_results=markdown_results,
        admission_audits=evidence_results,
    )
    if not final.implemented_checks_complete:
        summaries = "; ".join(issue.summary for issue in final.issues[:3])
        raise SnapshotError(f"current rule source did not pass implemented checks: {summaries}")
    files = tuple(
        sorted(
            (
                *(
                    SnapshotFile(path, "rule_candidate", item.raw_bytes, item.observed_at)
                    for path, item in observed_candidates.items()
                ),
                *(
                    SnapshotFile(path, "mechanical_evidence", item.raw_bytes, item.observed_at)
                    for path, item in observed_evidence.items()
                ),
            ),
            key=lambda item: (item.role, item.path),
        )
    )
    return make_snapshot_plan(DISTRIBUTION_NAME, version, files)


def _strict_manifest(
    raw_bytes: bytes,
    *,
    distribution: str,
    version: str,
) -> tuple[dict[str, Any], tuple[dict[str, Any], ...]]:
    try:
        manifest = json.loads(raw_bytes.decode("utf-8"), object_pairs_hook=_json_pairs)
    except (UnicodeError, json.JSONDecodeError, SnapshotError) as exc:
        raise SnapshotError(f"invalid snapshot manifest JSON: {exc}") from exc
    if not isinstance(manifest, dict) or set(manifest) != {
        "format",
        "distribution",
        "version",
        "algorithm",
        "files",
        "snapshot_sha256",
    }:
        raise SnapshotError("snapshot manifest has an invalid top-level field set")
    if manifest["format"] != SNAPSHOT_FORMAT or manifest["algorithm"] != "sha256":
        raise SnapshotError("snapshot manifest format or algorithm is unsupported")
    if manifest["distribution"] != distribution or manifest["version"] != version:
        raise SnapshotError("snapshot distribution or version does not match the installed owner")
    if not isinstance(manifest["snapshot_sha256"], str) or _SHA256.fullmatch(manifest["snapshot_sha256"]) is None:
        raise SnapshotError("snapshot_sha256 is invalid")
    if not isinstance(manifest["files"], list) or not manifest["files"]:
        raise SnapshotError("snapshot files must be a non-empty array")
    entries: list[dict[str, Any]] = []
    for entry in manifest["files"]:
        if not isinstance(entry, dict) or set(entry) != {"path", "role", "size", "sha256"}:
            raise SnapshotError("snapshot file member has an invalid field set")
        path, role, size, digest = entry["path"], entry["role"], entry["size"], entry["sha256"]
        if not isinstance(path, str) or not _normal_path(path):
            raise SnapshotError("snapshot file path is invalid")
        if role not in _ROLES:
            raise SnapshotError("snapshot file role is invalid")
        if not isinstance(size, int) or isinstance(size, bool) or size < 0:
            raise SnapshotError("snapshot file size is invalid")
        if not isinstance(digest, str) or _SHA256.fullmatch(digest) is None:
            raise SnapshotError("snapshot file sha256 is invalid")
        is_candidate = _candidate_kind(path) is not None
        if (role == "rule_candidate") != is_candidate:
            raise SnapshotError("snapshot role does not match its path")
        entries.append(entry)
    order = [(entry["role"], entry["path"]) for entry in entries]
    if order != sorted(order) or len({entry["path"] for entry in entries}) != len(entries):
        raise SnapshotError("snapshot files are not canonically sorted or contain duplicate paths")
    payload = {key: manifest[key] for key in ("format", "distribution", "version", "algorithm", "files")}
    expected_snapshot_hash = hashlib.sha256(_canonical_json(payload)).hexdigest()
    if manifest["snapshot_sha256"] != expected_snapshot_hash:
        raise SnapshotError("snapshot collection digest does not match the manifest")
    if raw_bytes != _canonical_json(manifest) + b"\n":
        raise SnapshotError("snapshot manifest is not canonical JSON with one terminal LF")
    return manifest, tuple(entries)


def validate_snapshot_directory(root: Path, *, distribution: str, version: str) -> VerifiedSnapshot:
    manifest_resource = _read_snapshot_resource(root, MANIFEST_NAME)
    manifest, entries = _strict_manifest(manifest_resource.raw_bytes, distribution=distribution, version=version)
    files: list[SnapshotFile] = []
    declared = {entry["path"] for entry in entries}
    for entry in entries:
        observed = _read_snapshot_resource(root, entry["path"])
        digest = hashlib.sha256(observed.raw_bytes).hexdigest()
        if len(observed.raw_bytes) != entry["size"] or digest != entry["sha256"]:
            raise SnapshotError(f"snapshot resource does not match manifest: {entry['path']}")
        files.append(SnapshotFile(entry["path"], entry["role"], observed.raw_bytes, observed.observed_at))
    try:
        walked_files = walk_regular_files(root)
    except OSError as exc:
        raise SnapshotError(f"snapshot contains an unsafe resource: {exc}") from exc
    actual = {relative for path in walked_files if (relative := path.relative_to(root).as_posix()) != MANIFEST_NAME}
    if actual != declared:
        raise SnapshotError("snapshot directory contains missing or undeclared resources")
    return VerifiedSnapshot(root, distribution, version, tuple(files), manifest["snapshot_sha256"])


def _read_snapshot_resource(root: Path, relative_path: str) -> ObservedResource:
    try:
        return read_observed_resource(root / relative_path, relative_path)
    except OSError as exc:
        raise SnapshotError(f"snapshot resource cannot be read safely: {relative_path}") from exc


def write_snapshot(plan: SnapshotPlan, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    for item in plan.files:
        target = destination / item.path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(item.raw_bytes)
    (destination / MANIFEST_NAME).write_bytes(plan.manifest_bytes)


def snapshot_plan_for_source(source_root: Path, version: str) -> SnapshotPlan:
    frozen_root = source_root / "code/ldvh" / SNAPSHOT_DIRECTORY
    if (frozen_root / MANIFEST_NAME).is_file():
        verified = validate_snapshot_directory(frozen_root, distribution=DISTRIBUTION_NAME, version=version)
        for item in verified.files:
            source = read_observed_resource(source_root / item.path, item.path)
            if source.raw_bytes != item.raw_bytes:
                raise SnapshotError(f"sdist source does not match its frozen snapshot: {item.path}")
        return make_snapshot_plan(DISTRIBUTION_NAME, version, verified.files)
    return _observe_worktree_plan(source_root, version)


def _normalised_distribution_name(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).lower()


def _same_file(first: Path, second: Path) -> bool:
    try:
        return first.resolve(strict=True) == second.resolve(strict=True) and os.path.samefile(first, second)
    except OSError:
        return False


def _distribution_file_map(distribution: importlib.metadata.Distribution) -> dict[str, Path] | None:
    if distribution.files is None:
        return None
    result: dict[str, Path] = {}
    for item in distribution.files:
        relative = PurePosixPath(str(item)).as_posix()
        try:
            result[relative] = Path(distribution.locate_file(item))
        except (OSError, TypeError):
            return None
    return result


def validate_installed_snapshot(package_file: Path) -> VerifiedSnapshot:
    owners: list[tuple[importlib.metadata.Distribution, dict[str, Path]]] = []
    for distribution in importlib.metadata.distributions(name=DISTRIBUTION_NAME):
        name = distribution.metadata.get("Name", "")
        if _normalised_distribution_name(name) != _normalised_distribution_name(DISTRIBUTION_NAME):
            continue
        files = _distribution_file_map(distribution)
        if files is None:
            continue
        claimed_init = files.get("ldvh/__init__.py")
        claimed_manifest = files.get(f"ldvh/{SNAPSHOT_DIRECTORY}/{MANIFEST_NAME}")
        if claimed_init is None or claimed_manifest is None or not _same_file(package_file, claimed_init):
            continue
        owners.append((distribution, files))
    if len(owners) != 1:
        raise SnapshotError("the imported ldvh package does not have one proven distribution owner")
    owner, owner_files = owners[0]
    version = owner.version
    snapshot_root = package_file.resolve(strict=True).parent / SNAPSHOT_DIRECTORY
    verified = validate_snapshot_directory(snapshot_root, distribution=DISTRIBUTION_NAME, version=version)
    required = {
        f"ldvh/{SNAPSHOT_DIRECTORY}/{MANIFEST_NAME}",
        *(f"ldvh/{SNAPSHOT_DIRECTORY}/{item.path}" for item in verified.files),
    }
    if not required.issubset(owner_files):
        raise SnapshotError("the owning distribution does not claim every snapshot resource")
    for relative in required:
        expected = package_file.resolve(strict=True).parent.parent / relative
        if not _same_file(expected, owner_files[relative]):
            raise SnapshotError("a claimed snapshot resource is outside the imported distribution package")
    return verified


def inspect_verified_snapshot(snapshot: VerifiedSnapshot) -> RepositoryInspection:
    identity = RuleSourceIdentity(
        "installed_release_snapshot",
        distribution=snapshot.distribution,
        version=snapshot.version,
        snapshot_sha256=snapshot.snapshot_sha256,
    )
    candidates: list[Candidate] = []
    markdown_results: dict[str, MarkdownResult] = {}
    evidence_results: dict[str, MarkdownResult] = {}
    for item in snapshot.files:
        parsed = parse_markdown_bytes(item.raw_bytes, item.path, observed_at=item.observed_at)
        if item.role == "rule_candidate":
            kind = _candidate_kind(item.path)
            if kind is None:
                raise SnapshotError("verified rule candidate has an invalid path")
            candidates.append(Candidate(item.path, snapshot.root / item.path, kind))
            markdown_results[item.path] = parsed
        else:
            evidence_results[item.path] = parsed
    discovery = DiscoveryResult(snapshot.root, tuple(candidates), (), complete=True)
    inspection = inspect_repository_source(
        discovery,
        identity,
        markdown_results=markdown_results,
        admission_audits=evidence_results,
    )
    locators = inspect_audit_evidence_locators(inspection.parsed_documents)
    expected_evidence = {locator.canonical_path for locator in locators.locators}
    if locators.issues or expected_evidence != set(evidence_results):
        issue = Issue(
            summary="安装快照机械证据集合与当前规则声明不一致",
            location=SourceLocation(MANIFEST_NAME),
            affected=tuple(sorted(expected_evidence | set(evidence_results))),
        )
        failed = DiscoveryResult(snapshot.root, tuple(candidates), (issue,), complete=False)
        inspection = inspect_repository_source(
            failed,
            identity,
            markdown_results=markdown_results,
            admission_audits=evidence_results,
        )
    return inspection


__all__ = [
    "DISTRIBUTION_NAME",
    "MANIFEST_NAME",
    "SNAPSHOT_DIRECTORY",
    "SnapshotError",
    "SnapshotFile",
    "SnapshotPlan",
    "VerifiedSnapshot",
    "inspect_verified_snapshot",
    "make_snapshot_plan",
    "snapshot_plan_for_source",
    "validate_installed_snapshot",
    "validate_snapshot_directory",
    "write_snapshot",
]
