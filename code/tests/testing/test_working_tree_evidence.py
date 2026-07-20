from __future__ import annotations

import hashlib
from copy import deepcopy
from typing import Any

import pytest

from ldvh.testing.working_tree_evidence import (
    EVIDENCE_CONTRACT,
    canonical_json_bytes,
    compare_manifests,
    current_complete_coverage,
    current_policy_fingerprint,
    current_policy_projection,
    manifest_fingerprint,
    normalize_relative_path,
    normalize_relative_paths,
    validate_manifest,
    validate_working_tree_evidence,
)


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _file(path: str, content: bytes) -> dict[str, Any]:
    return {"path": path, "size_bytes": len(content), "sha256": _sha(content)}


def _manifest(files: list[dict[str, Any]], *, observed_at: str = "2026-07-20T08:00:00+08:00") -> dict[str, Any]:
    policy_fingerprint = current_policy_fingerprint()
    return {
        "observed_at": observed_at,
        "status": "complete",
        "manifest_fingerprint": manifest_fingerprint(files, policy_fingerprint),
        "file_count": len(files),
        "byte_count": sum(file["size_bytes"] for file in files),
        "files": files,
    }


def _incomplete_manifest(files: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    files = files or []
    return {
        "observed_at": "2026-07-20T08:00:00Z",
        "status": "incomplete",
        "manifest_fingerprint": None,
        "file_count": len(files),
        "byte_count": sum(file["size_bytes"] for file in files),
        "files": files,
    }


def _evidence(
    before: dict[str, Any],
    after: dict[str, Any] | None,
    *,
    status: str,
    changes: list[dict[str, Any]],
    coverage: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "contract": EVIDENCE_CONTRACT,
        "governed_project_id": "ldvh",
        "git_worktree_root": "/workspace/ldvh",
        "git_common_dir": "/workspace/ldvh-main/.git",
        "status": status,
        "coverage": coverage or current_complete_coverage(),
        "before": before,
        "after": after,
        "changes": changes,
    }


def _incomplete_coverage(*, code: str = "read_unavailable") -> dict[str, Any]:
    coverage = current_complete_coverage()
    coverage.update(
        {
            "status": "incomplete",
            "gaps": [
                {
                    "stage": "after",
                    "path": "code/example.py",
                    "code": code,
                    "summary": "could not safely read the complete file",
                }
            ],
        }
    )
    return coverage


def test_canonical_json_and_fixed_policy_fingerprint_are_stable() -> None:
    assert canonical_json_bytes({"é": 2, "a": ["值", True]}) == '{"a":["值",true],"é":2}'.encode()
    projection = current_policy_projection()
    assert set(projection) == {"contract", "policy_key", "rules"}
    assert projection["rules"] == sorted(projection["rules"], key=lambda rule: rule["policy_ref"])
    assert all(rule["path_rules"] == sorted(rule["path_rules"]) for rule in projection["rules"])
    assert current_policy_fingerprint() == "9a597eea4a3f2ec561ea1c4fb56f9e4ddd0d1a85f889e2b5ee4ba4ffaf9c33a6"


def test_canonical_json_rejects_non_json_and_non_finite_values() -> None:
    with pytest.raises(ValueError, match="non-JSON"):
        canonical_json_bytes({"bad": object()})
    with pytest.raises(ValueError, match="non-finite"):
        canonical_json_bytes({"bad": float("nan")})
    with pytest.raises(ValueError, match="non-string"):
        canonical_json_bytes({1: "bad"})


@pytest.mark.parametrize(
    "path",
    ["", "/absolute", "C:/absolute", r"code\file.py", "code//file.py", "./code", "code/../file.py", "code/"],
)
def test_relative_path_rejects_values_outside_the_lexical_contract(path: str) -> None:
    with pytest.raises(ValueError):
        normalize_relative_path(path)


def test_relative_path_normalizes_nfc_and_detects_collision() -> None:
    decomposed = "notes/e\u0301.md"
    composed = "notes/é.md"
    assert normalize_relative_path(decomposed) == composed
    with pytest.raises(ValueError, match="collides"):
        normalize_relative_paths([decomposed, composed])


def test_complete_manifest_fingerprint_excludes_time_and_absolute_identity() -> None:
    files = [_file("README.md", b"hello"), _file("specs/规则.md", "内容".encode())]
    first = _manifest(files, observed_at="2026-07-20T08:00:00+08:00")
    second = _manifest(files, observed_at="2026-07-20T09:00:00+08:00")
    assert first["manifest_fingerprint"] == second["manifest_fingerprint"]
    validate_manifest(first, current_policy_fingerprint())


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda value: value.update({"extra": True}), "invalid field set"),
        (lambda value: value.update({"status": "partial"}), "manifest.status"),
        (lambda value: value.update({"file_count": 2}), "file_count"),
        (lambda value: value.update({"byte_count": 2}), "byte_count"),
        (lambda value: value.update({"manifest_fingerprint": "0" * 64}), "incorrect"),
    ],
)
def test_manifest_rejects_closed_set_enum_count_and_fingerprint_violations(mutation: Any, message: str) -> None:
    manifest = _manifest([_file("a.txt", b"a")])
    mutation(manifest)
    with pytest.raises(ValueError, match=message):
        validate_manifest(manifest, current_policy_fingerprint())


def test_manifest_rejects_non_nfc_unsorted_and_duplicate_paths() -> None:
    non_nfc = _file("e\u0301.txt", b"a")
    with pytest.raises(ValueError, match="NFC"):
        _manifest([non_nfc])

    unsorted = [_file("z.txt", b"z"), _file("a.txt", b"a")]
    with pytest.raises(ValueError, match="strictly ordered"):
        manifest_fingerprint(unsorted, current_policy_fingerprint())

    duplicated = [_file("a.txt", b"a"), _file("a.txt", b"a")]
    with pytest.raises(ValueError, match="strictly ordered"):
        manifest_fingerprint(duplicated, current_policy_fingerprint())


def test_identical_complete_manifests_produce_and_validate_complete_evidence() -> None:
    before = _manifest([_file("a.txt", b"a")])
    after = _manifest([_file("a.txt", b"a")], observed_at="2026-07-20T08:05:00+08:00")
    comparison = compare_manifests(before, after, policy_fingerprint=current_policy_fingerprint())
    assert comparison == {"status": "complete", "changes": []}
    validate_working_tree_evidence(_evidence(before, after, status="complete", changes=[]))


def test_complete_manifest_diff_is_sorted_and_produces_stale_evidence() -> None:
    before = _manifest([_file("a.txt", b"old"), _file("m.txt", b"removed")])
    after = _manifest(
        [_file("a.txt", b"new"), _file("z.txt", b"added")],
        observed_at="2026-07-20T08:05:00+08:00",
    )
    comparison = compare_manifests(before, after, policy_fingerprint=current_policy_fingerprint())
    assert comparison == {
        "status": "stale",
        "changes": [
            {
                "path": "a.txt",
                "kind": "modified",
                "before_sha256": _sha(b"old"),
                "after_sha256": _sha(b"new"),
            },
            {
                "path": "m.txt",
                "kind": "removed",
                "before_sha256": _sha(b"removed"),
                "after_sha256": None,
            },
            {
                "path": "z.txt",
                "kind": "added",
                "before_sha256": None,
                "after_sha256": _sha(b"added"),
            },
        ],
    }
    validate_working_tree_evidence(
        _evidence(before, after, status="stale", changes=comparison["changes"])
    )


@pytest.mark.parametrize(
    "kwargs",
    [
        {"identities_match": False},
        {"policies_match": False},
        {"comparison_complete": False},
    ],
)
def test_incomparable_complete_manifests_return_incomplete_without_changes(kwargs: dict[str, bool]) -> None:
    before = _manifest([_file("a.txt", b"old")])
    after = _manifest([_file("a.txt", b"new")])
    assert compare_manifests(
        before,
        after,
        policy_fingerprint=current_policy_fingerprint(),
        **kwargs,
    ) == {"status": "incomplete", "changes": []}


def test_missing_or_incomplete_after_returns_incomplete_without_changes() -> None:
    before = _manifest([_file("a.txt", b"old")])
    assert compare_manifests(
        before, None, policy_fingerprint=current_policy_fingerprint()
    ) == {"status": "incomplete", "changes": []}
    assert compare_manifests(
        before,
        _incomplete_manifest([_file("a.txt", b"new")]),
        policy_fingerprint=current_policy_fingerprint(),
    ) == {"status": "incomplete", "changes": []}

    evidence = _evidence(
        before,
        None,
        status="incomplete",
        changes=[],
        coverage=_incomplete_coverage(),
    )
    validate_working_tree_evidence(evidence)


def test_incomplete_evidence_forbids_partial_changes() -> None:
    before = _manifest([_file("a.txt", b"old")])
    evidence = _evidence(
        before,
        None,
        status="incomplete",
        changes=[
            {
                "path": "a.txt",
                "kind": "removed",
                "before_sha256": _sha(b"old"),
                "after_sha256": None,
            }
        ],
        coverage=_incomplete_coverage(),
    )
    with pytest.raises(ValueError, match="partial changes"):
        validate_working_tree_evidence(evidence)


def test_evidence_rejects_closed_fields_enums_and_inconsistent_changes() -> None:
    before = _manifest([_file("a.txt", b"old")])
    after = _manifest([_file("a.txt", b"new")])
    comparison = compare_manifests(before, after, policy_fingerprint=current_policy_fingerprint())
    evidence = _evidence(before, after, status="stale", changes=comparison["changes"])

    with_extra = deepcopy(evidence)
    with_extra["head"] = "deadbeef"
    with pytest.raises(ValueError, match="invalid field set"):
        validate_working_tree_evidence(with_extra)

    bad_enum = deepcopy(evidence)
    bad_enum["changes"][0]["kind"] = "renamed"
    with pytest.raises(ValueError, match="closed enum"):
        validate_working_tree_evidence(bad_enum)

    partial = deepcopy(evidence)
    partial["changes"] = []
    with pytest.raises(ValueError, match="complete deterministic difference"):
        validate_working_tree_evidence(partial)


def test_coverage_rejects_unknown_gap_code_and_policy_reference_drift() -> None:
    before = _manifest([])
    coverage = _incomplete_coverage(code="read_unavailable")
    coverage["gaps"][0]["code"] = "git_dirty"
    evidence = _evidence(before, None, status="incomplete", changes=[], coverage=coverage)
    with pytest.raises(ValueError, match="closed enum"):
        validate_working_tree_evidence(evidence)

    coverage = current_complete_coverage()
    coverage["exclude_policy_refs"] = coverage["exclude_policy_refs"][:-1]
    evidence = _evidence(before, before, status="complete", changes=[], coverage=coverage)
    with pytest.raises(ValueError, match="fixed sorted policy references"):
        validate_working_tree_evidence(evidence)
