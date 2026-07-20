"""Pure validation and comparison for full-v4 Working Tree evidence.

This module deliberately does not inspect paths, read files, invoke Git, or
touch test-run records.  Callers provide already observed manifests; the
functions here only enforce the DTO contract and perform deterministic
fingerprinting/comparison.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import unicodedata
from collections.abc import Mapping, Sequence
from datetime import datetime
from pathlib import PureWindowsPath
from typing import Any, Literal

EVIDENCE_CONTRACT = "ldvh-working-tree-evidence/1"
COVERAGE_POLICY_CONTRACT = "ldvh-working-tree-coverage-policy/1"
MANIFEST_CONTRACT = "ldvh-working-tree-manifest/1"
POLICY_KEY = "full-v4-working-tree-inputs"
ATTACHMENT_KEY = "working-tree-test-evidence-fields"

_INCLUDE_POLICY_REFS = (f"{ATTACHMENT_KEY}::full-v4-all-regular-files",)
_EXCLUDE_POLICY_REFS = tuple(
    sorted(
        (
            f"{ATTACHMENT_KEY}::full-v4-git-administration",
            f"{ATTACHMENT_KEY}::full-v4-run-evidence-output",
            f"{ATTACHMENT_KEY}::full-v4-local-environments",
            f"{ATTACHMENT_KEY}::full-v4-local-tool-state",
            f"{ATTACHMENT_KEY}::full-v4-generated-and-cache-output",
            f"{ATTACHMENT_KEY}::full-v4-platform-noise",
        )
    )
)

_POLICY_RULES = (
    {
        "policy_ref": f"{ATTACHMENT_KEY}::full-v4-all-regular-files",
        "effect": "include",
        "path_rules": ["ALL_REGULAR_FILES"],
    },
    {
        "policy_ref": f"{ATTACHMENT_KEY}::full-v4-generated-and-cache-output",
        "effect": "exclude",
        "path_rules": sorted(
            [
                "ROOT:.pytest_cache/**",
                "ROOT:.ruff_cache/**",
                "ROOT:build/**",
                "ROOT:dist/**",
                "ROOT:web/dist/**",
                "ANY_DIR:__pycache__/**",
                "ANY_SUFFIX_DIR:.egg-info/**",
                "ANY_SUFFIX_FILE:.pyc",
                "ANY_SUFFIX_FILE:.pyo",
            ]
        ),
    },
    {
        "policy_ref": f"{ATTACHMENT_KEY}::full-v4-git-administration",
        "effect": "exclude",
        "path_rules": ["ROOT:.git"],
    },
    {
        "policy_ref": f"{ATTACHMENT_KEY}::full-v4-local-environments",
        "effect": "exclude",
        "path_rules": sorted(["ROOT:.venv/**", "ROOT:web/node_modules/**"]),
    },
    {
        "policy_ref": f"{ATTACHMENT_KEY}::full-v4-local-tool-state",
        "effect": "exclude",
        "path_rules": sorted(["ROOT:.githooks-v4/**", "ROOT:.zcode/**"]),
    },
    {
        "policy_ref": f"{ATTACHMENT_KEY}::full-v4-platform-noise",
        "effect": "exclude",
        "path_rules": ["ANY_FILE:.DS_Store"],
    },
    {
        "policy_ref": f"{ATTACHMENT_KEY}::full-v4-run-evidence-output",
        "effect": "exclude",
        "path_rules": ["ROOT:.ldvh-test-runs/**"],
    },
)

_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_OFFSET_DATETIME_PATTERN = re.compile(r"(?:Z|[+-][0-9]{2}:[0-9]{2})$")
_WINDOWS_DRIVE_ABSOLUTE_PATTERN = re.compile(r"^[A-Za-z]:[\\/]")

_GAP_STAGES = frozenset({"before", "after", "comparison"})
_GAP_CODES = frozenset(
    {
        "policy_unavailable",
        "traversal_unavailable",
        "unsafe_entry",
        "unsupported_entry",
        "read_unavailable",
        "path_changed",
        "normalization_collision",
        "identity_mismatch",
        "policy_mismatch",
    }
)
_CHANGE_KINDS = frozenset({"added", "removed", "modified"})


def canonical_json_bytes(value: Any) -> bytes:
    """Return the contract's canonical JSON encoding for a JSON value."""

    _validate_json_value(value)
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    """Hash a value using the contract's canonical JSON encoding."""

    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def current_policy_projection() -> dict[str, Any]:
    """Return an independent copy of the fixed full-v4 policy projection."""

    return {
        "contract": COVERAGE_POLICY_CONTRACT,
        "policy_key": POLICY_KEY,
        "rules": [
            {
                "policy_ref": rule["policy_ref"],
                "effect": rule["effect"],
                "path_rules": list(rule["path_rules"]),
            }
            for rule in _POLICY_RULES
        ],
    }


def current_policy_fingerprint() -> str:
    """Return the SHA-256 fingerprint of the fixed full-v4 policy."""

    return canonical_sha256(current_policy_projection())


def current_complete_coverage() -> dict[str, Any]:
    """Return the complete-coverage value for the fixed policy."""

    return {
        "policy_key": POLICY_KEY,
        "policy_fingerprint": current_policy_fingerprint(),
        "include_policy_refs": list(_INCLUDE_POLICY_REFS),
        "exclude_policy_refs": list(_EXCLUDE_POLICY_REFS),
        "status": "complete",
        "gaps": [],
    }


def policy_excludes_relative_path(
    path: str,
    *,
    entry_kind: Literal["directory", "regular_file", "other"],
) -> bool:
    """Return whether the fixed policy excludes one normalized relative path.

    ``entry_kind`` is supplied by the filesystem observation layer.  Keeping
    path-rule matching here ensures capture code cannot silently duplicate or
    drift from the policy projection used for the policy fingerprint.
    """

    normalized = normalize_relative_path(path)
    if entry_kind not in {"directory", "regular_file", "other"}:
        raise ValueError("entry_kind is outside the closed enum")
    segments = normalized.split("/")
    for rule in _POLICY_RULES:
        if rule["effect"] != "exclude":
            continue
        for path_rule in rule["path_rules"]:
            if _path_rule_matches(path_rule, normalized, segments, entry_kind):
                return True
    return False


def normalize_relative_path(path: str) -> str:
    """Normalize one observed worktree-relative path to NFC.

    The function validates only the lexical contract.  It does not resolve or
    inspect the path on a filesystem.
    """

    _require_type(path, str, "path")
    normalized = unicodedata.normalize("NFC", path)
    if not normalized:
        raise ValueError("path must not be empty")
    if "\\" in normalized:
        raise ValueError("path must use '/' separators")
    if normalized.startswith("/") or PureWindowsPath(normalized).is_absolute():
        raise ValueError("path must be relative")
    segments = normalized.split("/")
    if any(segment in {"", ".", ".."} for segment in segments):
        raise ValueError("path contains an empty, '.' or '..' segment")
    return normalized


def normalize_relative_paths(paths: Sequence[str]) -> tuple[str, ...]:
    """Normalize paths and reject normalization collisions."""

    _require_sequence(paths, "paths")
    normalized: list[str] = []
    sources: dict[str, str] = {}
    for index, path in enumerate(paths):
        result = normalize_relative_path(path)
        if result in sources:
            raise ValueError(
                f"paths[{index}] collides after NFC normalization with {sources[result]!r}"
            )
        sources[result] = path
        normalized.append(result)
    return tuple(normalized)


def _path_rule_matches(
    path_rule: str,
    path: str,
    segments: list[str],
    entry_kind: str,
) -> bool:
    if path_rule.startswith("ROOT:"):
        target = path_rule.removeprefix("ROOT:")
        if target.endswith("/**"):
            target = target.removesuffix("/**")
            return path == target or path.startswith(f"{target}/")
        # The sole current exact ROOT rule is .git, whose attachment-defined
        # boundary covers either the administration file or its complete tree.
        return path == target or path.startswith(f"{target}/")
    if path_rule.startswith("ANY_DIR:"):
        target = path_rule.removeprefix("ANY_DIR:").removesuffix("/**")
        directory_segments = segments if entry_kind == "directory" else segments[:-1]
        return target in directory_segments
    if path_rule.startswith("ANY_SUFFIX_DIR:"):
        suffix = path_rule.removeprefix("ANY_SUFFIX_DIR:").removesuffix("/**")
        directory_segments = segments if entry_kind == "directory" else segments[:-1]
        return any(segment.endswith(suffix) for segment in directory_segments)
    if path_rule.startswith("ANY_FILE:"):
        target = path_rule.removeprefix("ANY_FILE:")
        return entry_kind == "regular_file" and segments[-1] == target
    if path_rule.startswith("ANY_SUFFIX_FILE:"):
        suffix = path_rule.removeprefix("ANY_SUFFIX_FILE:")
        return entry_kind == "regular_file" and segments[-1].endswith(suffix)
    if path_rule == "ALL_REGULAR_FILES":
        return False
    raise ValueError(f"unsupported fixed policy path rule: {path_rule!r}")


def manifest_fingerprint(files: Sequence[Mapping[str, Any]], policy_fingerprint: str) -> str:
    """Calculate a complete manifest fingerprint from provided file entries."""

    _validate_sha256(policy_fingerprint, "policy_fingerprint")
    normalized_files = _validate_files(files)
    projection = {
        "contract": MANIFEST_CONTRACT,
        "policy_fingerprint": policy_fingerprint,
        "files": normalized_files,
    }
    return canonical_sha256(projection)


def validate_coverage(coverage: Mapping[str, Any]) -> None:
    """Validate the closed coverage object for contract version 1."""

    value = _require_mapping(coverage, "coverage")
    _require_keys(
        value,
        {
            "policy_key",
            "policy_fingerprint",
            "include_policy_refs",
            "exclude_policy_refs",
            "status",
            "gaps",
        },
        "coverage",
    )
    if value["policy_key"] != POLICY_KEY:
        raise ValueError(f"coverage.policy_key must be {POLICY_KEY!r}")
    if value["policy_fingerprint"] != current_policy_fingerprint():
        raise ValueError("coverage.policy_fingerprint does not match the fixed policy")
    _validate_exact_string_array(value["include_policy_refs"], _INCLUDE_POLICY_REFS, "coverage.include_policy_refs")
    _validate_exact_string_array(value["exclude_policy_refs"], _EXCLUDE_POLICY_REFS, "coverage.exclude_policy_refs")
    status = value["status"]
    if status not in {"complete", "incomplete"}:
        raise ValueError("coverage.status must be 'complete' or 'incomplete'")
    gaps = _require_sequence(value["gaps"], "coverage.gaps")
    for index, gap in enumerate(gaps):
        _validate_gap(gap, f"coverage.gaps[{index}]")
    if status == "complete" and gaps:
        raise ValueError("complete coverage must have no gaps")
    if status == "incomplete" and not gaps:
        raise ValueError("incomplete coverage must have at least one gap")


def validate_manifest(manifest: Mapping[str, Any], policy_fingerprint: str) -> None:
    """Validate one closed manifest object against a policy fingerprint."""

    _validate_sha256(policy_fingerprint, "policy_fingerprint")
    value = _require_mapping(manifest, "manifest")
    _require_keys(
        value,
        {"observed_at", "status", "manifest_fingerprint", "file_count", "byte_count", "files"},
        "manifest",
    )
    _validate_offset_datetime(value["observed_at"], "manifest.observed_at")
    status = value["status"]
    if status not in {"complete", "incomplete"}:
        raise ValueError("manifest.status must be 'complete' or 'incomplete'")
    files = _validate_files(value["files"])
    _require_nonnegative_int(value["file_count"], "manifest.file_count")
    _require_nonnegative_int(value["byte_count"], "manifest.byte_count")
    if value["file_count"] != len(files):
        raise ValueError("manifest.file_count does not equal the files length")
    if value["byte_count"] != sum(file["size_bytes"] for file in files):
        raise ValueError("manifest.byte_count does not equal the sum of files[].size_bytes")
    fingerprint = value["manifest_fingerprint"]
    if status == "incomplete":
        if fingerprint is not None:
            raise ValueError("incomplete manifest must have a null manifest_fingerprint")
        return
    expected = manifest_fingerprint(files, policy_fingerprint)
    if fingerprint != expected:
        raise ValueError("complete manifest has an incorrect manifest_fingerprint")


def compare_manifests(
    before: Mapping[str, Any],
    after: Mapping[str, Any] | None,
    *,
    policy_fingerprint: str,
    identities_match: bool = True,
    policies_match: bool = True,
    comparison_complete: bool = True,
) -> dict[str, Any]:
    """Compare provided manifests without observing or interpreting content.

    The three boolean inputs are mechanical facts established by the caller's
    observation boundary.  A false value makes the manifests incomparable and
    therefore returns ``incomplete`` with no partial changes.
    """

    for name, value in (
        ("identities_match", identities_match),
        ("policies_match", policies_match),
        ("comparison_complete", comparison_complete),
    ):
        _require_type(value, bool, name)
    validate_manifest(before, policy_fingerprint)
    if after is not None:
        validate_manifest(after, policy_fingerprint)
    if (
        after is None
        or before["status"] != "complete"
        or after["status"] != "complete"
        or not identities_match
        or not policies_match
        or not comparison_complete
    ):
        return {"status": "incomplete", "changes": []}

    changes = _diff_files(before["files"], after["files"])
    same_fingerprint = before["manifest_fingerprint"] == after["manifest_fingerprint"]
    if same_fingerprint:
        if changes:
            raise ValueError("equal manifest fingerprints produced file differences")
        return {"status": "complete", "changes": []}
    if not changes:
        # The change DTO cannot represent a size-only difference with equal
        # content hashes.  It must not emit a partial or invented difference.
        return {"status": "incomplete", "changes": []}
    return {"status": "stale", "changes": changes}


def finalize_working_tree_evidence(
    *,
    governed_project_id: str,
    git_worktree_root: str,
    git_common_dir: str,
    coverage: Mapping[str, Any],
    before: Mapping[str, Any],
    after: Mapping[str, Any] | None,
    identities_match: bool = True,
    policies_match: bool = True,
    comparison_complete: bool = True,
) -> dict[str, Any]:
    """Form and validate the sole closed Working Tree evidence DTO.

    Filesystem and runner layers provide already observed identity, coverage,
    and manifests.  Keeping the DTO field set and deterministic comparison in
    this pure module prevents those side-effect layers from maintaining a
    second evidence schema.
    """

    comparison = compare_manifests(
        before,
        after,
        policy_fingerprint=coverage["policy_fingerprint"],
        identities_match=identities_match,
        policies_match=policies_match,
        comparison_complete=comparison_complete,
    )
    evidence = {
        "contract": EVIDENCE_CONTRACT,
        "governed_project_id": governed_project_id,
        "git_worktree_root": git_worktree_root,
        "git_common_dir": git_common_dir,
        "status": comparison["status"],
        "coverage": dict(coverage),
        "before": dict(before),
        "after": None if after is None else dict(after),
        "changes": comparison["changes"],
    }
    validate_working_tree_evidence(evidence)
    return evidence


def validate_working_tree_evidence(evidence: Mapping[str, Any]) -> None:
    """Validate the complete closed Working Tree evidence DTO."""

    value = _require_mapping(evidence, "evidence")
    _require_keys(
        value,
        {
            "contract",
            "governed_project_id",
            "git_worktree_root",
            "git_common_dir",
            "status",
            "coverage",
            "before",
            "after",
            "changes",
        },
        "evidence",
    )
    if value["contract"] != EVIDENCE_CONTRACT:
        raise ValueError(f"evidence.contract must be {EVIDENCE_CONTRACT!r}")
    _require_nonempty_string(value["governed_project_id"], "evidence.governed_project_id")
    _validate_absolute_path(value["git_worktree_root"], "evidence.git_worktree_root")
    _validate_absolute_path(value["git_common_dir"], "evidence.git_common_dir")
    validate_coverage(value["coverage"])
    policy_fingerprint = value["coverage"]["policy_fingerprint"]
    validate_manifest(value["before"], policy_fingerprint)
    if value["after"] is not None:
        validate_manifest(value["after"], policy_fingerprint)
    changes = _validate_changes(value["changes"])
    status = value["status"]
    if status not in {"complete", "stale", "incomplete"}:
        raise ValueError("evidence.status must be 'complete', 'stale' or 'incomplete'")

    if status == "incomplete":
        if value["coverage"]["status"] != "incomplete":
            raise ValueError("incomplete evidence must have incomplete coverage")
        if changes:
            raise ValueError("incomplete evidence must not contain partial changes")
        return

    if value["coverage"]["status"] != "complete":
        raise ValueError("complete or stale evidence requires complete coverage")
    comparison = compare_manifests(
        value["before"],
        value["after"],
        policy_fingerprint=policy_fingerprint,
    )
    if comparison["status"] != status:
        raise ValueError("evidence.status does not match its manifests")
    if comparison["changes"] != changes:
        raise ValueError("evidence.changes is not the complete deterministic difference")


def _diff_files(before: Sequence[Mapping[str, Any]], after: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    before_by_path = {item["path"]: item for item in before}
    after_by_path = {item["path"]: item for item in after}
    changes: list[dict[str, Any]] = []
    for path in sorted(set(before_by_path) | set(after_by_path), key=lambda item: item.encode("utf-8")):
        before_file = before_by_path.get(path)
        after_file = after_by_path.get(path)
        if before_file is None:
            changes.append(
                {
                    "path": path,
                    "kind": "added",
                    "before_sha256": None,
                    "after_sha256": after_file["sha256"],
                }
            )
        elif after_file is None:
            changes.append(
                {
                    "path": path,
                    "kind": "removed",
                    "before_sha256": before_file["sha256"],
                    "after_sha256": None,
                }
            )
        elif before_file["sha256"] != after_file["sha256"]:
            changes.append(
                {
                    "path": path,
                    "kind": "modified",
                    "before_sha256": before_file["sha256"],
                    "after_sha256": after_file["sha256"],
                }
            )
    return changes


def _validate_files(files: Any) -> list[dict[str, Any]]:
    values = _require_sequence(files, "files")
    normalized: list[dict[str, Any]] = []
    previous_key: bytes | None = None
    for index, file in enumerate(values):
        location = f"files[{index}]"
        value = _require_mapping(file, location)
        _require_keys(value, {"path", "size_bytes", "sha256"}, location)
        path = normalize_relative_path(value["path"])
        if path != value["path"]:
            raise ValueError(f"{location}.path must already be NFC-normalized")
        path_key = path.encode("utf-8")
        if previous_key is not None and path_key <= previous_key:
            raise ValueError("files must be strictly ordered by path UTF-8 bytes without duplicates")
        previous_key = path_key
        _require_nonnegative_int(value["size_bytes"], f"{location}.size_bytes")
        _validate_sha256(value["sha256"], f"{location}.sha256")
        normalized.append({"path": path, "size_bytes": value["size_bytes"], "sha256": value["sha256"]})
    return normalized


def _validate_gap(gap: Any, location: str) -> None:
    value = _require_mapping(gap, location)
    _require_keys(value, {"stage", "path", "code", "summary"}, location)
    if value["stage"] not in _GAP_STAGES:
        raise ValueError(f"{location}.stage is outside the closed enum")
    if value["path"] is not None:
        normalized = normalize_relative_path(value["path"])
        if normalized != value["path"]:
            raise ValueError(f"{location}.path must already be NFC-normalized")
    if value["code"] not in _GAP_CODES:
        raise ValueError(f"{location}.code is outside the closed enum")
    _require_nonempty_string(value["summary"], f"{location}.summary")


def _validate_changes(changes: Any) -> list[dict[str, Any]]:
    values = _require_sequence(changes, "changes")
    normalized: list[dict[str, Any]] = []
    previous_key: bytes | None = None
    for index, change in enumerate(values):
        location = f"changes[{index}]"
        value = _require_mapping(change, location)
        _require_keys(value, {"path", "kind", "before_sha256", "after_sha256"}, location)
        path = normalize_relative_path(value["path"])
        if path != value["path"]:
            raise ValueError(f"{location}.path must already be NFC-normalized")
        path_key = path.encode("utf-8")
        if previous_key is not None and path_key <= previous_key:
            raise ValueError("changes must be strictly ordered by path UTF-8 bytes without duplicates")
        previous_key = path_key
        kind = value["kind"]
        if kind not in _CHANGE_KINDS:
            raise ValueError(f"{location}.kind is outside the closed enum")
        before_sha256, after_sha256 = value["before_sha256"], value["after_sha256"]
        if kind == "added":
            if before_sha256 is not None:
                raise ValueError(f"{location}.before_sha256 must be null for added")
            _validate_sha256(after_sha256, f"{location}.after_sha256")
        elif kind == "removed":
            _validate_sha256(before_sha256, f"{location}.before_sha256")
            if after_sha256 is not None:
                raise ValueError(f"{location}.after_sha256 must be null for removed")
        else:
            _validate_sha256(before_sha256, f"{location}.before_sha256")
            _validate_sha256(after_sha256, f"{location}.after_sha256")
            if before_sha256 == after_sha256:
                raise ValueError(f"{location} modified hashes must differ")
        normalized.append(dict(value))
    return normalized


def _validate_exact_string_array(value: Any, expected: tuple[str, ...], location: str) -> None:
    values = _require_sequence(value, location)
    if any(type(item) is not str for item in values):
        raise ValueError(f"{location} must contain only strings")
    if tuple(values) != expected:
        raise ValueError(f"{location} does not match the fixed sorted policy references")


def _validate_json_value(value: Any, location: str = "value") -> None:
    if value is None or type(value) in {bool, int, str}:
        return
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError(f"{location} contains a non-finite number")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_json_value(item, f"{location}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{location} contains a non-string object key")
            _validate_json_value(item, f"{location}.{key}")
        return
    raise ValueError(f"{location} contains a non-JSON value")


def _validate_offset_datetime(value: Any, location: str) -> None:
    _require_type(value, str, location)
    if not _OFFSET_DATETIME_PATTERN.search(value):
        raise ValueError(f"{location} must include a UTC offset")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(f"{location} must be an RFC 3339 date-time") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{location} must include a UTC offset")


def _validate_absolute_path(value: Any, location: str) -> None:
    _require_nonempty_string(value, location)
    is_absolute = value.startswith("/") or value.startswith("//") or bool(_WINDOWS_DRIVE_ABSOLUTE_PATTERN.match(value))
    if not is_absolute:
        try:
            is_absolute = PureWindowsPath(value).is_absolute()
        except (TypeError, ValueError):
            is_absolute = False
    if not is_absolute:
        raise ValueError(f"{location} must be an absolute path")


def _validate_sha256(value: Any, location: str) -> None:
    if type(value) is not str or not _SHA256_PATTERN.fullmatch(value):
        raise ValueError(f"{location} must be a 64-character lowercase SHA-256")


def _require_nonnegative_int(value: Any, location: str) -> None:
    if type(value) is not int or value < 0:
        raise ValueError(f"{location} must be a non-negative integer")


def _require_nonempty_string(value: Any, location: str) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{location} must be a non-empty string")


def _require_mapping(value: Any, location: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{location} must be an object")
    if any(type(key) is not str for key in value):
        raise ValueError(f"{location} contains a non-string object key")
    return value


def _require_sequence(value: Any, location: str) -> Sequence[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{location} must be an array")
    return value


def _require_keys(value: Mapping[str, Any], expected: set[str], location: str) -> None:
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise ValueError(f"{location} has an invalid field set; missing={missing}, extra={extra}")


def _require_type(value: Any, expected: type[Any], location: str) -> None:
    if type(value) is not expected:
        raise ValueError(f"{location} must be {expected.__name__}")
