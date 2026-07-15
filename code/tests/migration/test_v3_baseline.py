from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from ruamel.yaml import YAML

from ldvh.migration.v3_baseline import (
    EXPECTED_COUNTS,
    EXPECTED_STATUSES,
    render_v3_baseline,
    verify_v3_baseline,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
MANIFEST = PROJECT_ROOT / "migration" / "v3-facts" / "baseline.json"


def test_checked_in_v3_baseline_is_the_canonical_92_item_projection() -> None:
    result = verify_v3_baseline(PROJECT_ROOT, MANIFEST)
    assert result.valid, result.issues
    assert result.entry_count == 92
    assert MANIFEST.read_text(encoding="utf-8") == render_v3_baseline(PROJECT_ROOT)


def test_v3_baseline_freezes_counts_statuses_paths_blobs_and_times() -> None:
    loaded = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert loaded["expected_counts"] == EXPECTED_COUNTS
    assert loaded["expected_statuses"] == EXPECTED_STATUSES
    assert len(loaded["entries"]) == 92
    assert [entry["source_key"] for entry in loaded["entries"]] == sorted(
        entry["source_key"] for entry in loaded["entries"]
    )


def test_v3_baseline_records_historical_time_and_closed_workcase_observations() -> None:
    loaded = json.loads(MANIFEST.read_text(encoding="utf-8"))
    offset = re.compile(r"(?:Z|[+-][0-9]{2}:[0-9]{2})\Z")
    affected: set[str] = set()
    missing_offset = 0
    for entry in loaded["entries"]:
        times = entry["source_times"]
        values = [times["created"], times["updated"]]
        if times["terminal"] is not None:
            values.append(times["terminal"]["value"])
        for value in values:
            if isinstance(value, str) and offset.search(value) is None:
                affected.add(entry["source_key"])
                missing_offset += 1
    assert (len(affected), missing_offset) == (28, 33)

    loader = YAML(typ="safe")
    closed = 0
    with_v3_confirmation = 0
    for entry in loaded["entries"]:
        if entry["source_type"] != "workcase" or entry["source_status"] != "closed":
            continue
        closed += 1
        source = loader.load((PROJECT_ROOT / entry["source_path"]).read_text(encoding="utf-8"))
        if source.get("human_closure_confirmation"):
            with_v3_confirmation += 1
    assert (closed, with_v3_confirmation) == (13, 6)
    assert all(
        {
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
        <= set(entry)
        for entry in loaded["entries"]
    )


def test_v3_baseline_ignores_current_paths_outside_the_frozen_archive(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = tmp_path / "migration" / "v3-facts" / "baseline.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(MANIFEST.read_text(encoding="utf-8"), encoding="utf-8")
    loaded = json.loads(manifest.read_text(encoding="utf-8"))
    shutil.copytree(
        PROJECT_ROOT / "archive" / "v3" / "ldvh-base",
        tmp_path / "archive" / "v3" / "ldvh-base",
    )

    for relative in (
        Path("facts/sparks/spark-0001.yaml"),
        Path("ldvh-base/sparks/spark-0050.yaml"),
    ):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("object_id: example\n", encoding="utf-8")

    snapshot_commit = loaded["snapshot_commit"]
    snapshot_tree = loaded["snapshot_tree"]
    source_root = loaded["source_root"]
    entries_by_path = {entry["source_path"]: entry for entry in loaded["entries"]}

    def fake_git(repository_root: Path, *args: str) -> bytes:
        assert repository_root == tmp_path.resolve()
        if args == ("rev-parse", "--verify", f"{snapshot_commit}^{{commit}}"):
            return f"{snapshot_commit}\n".encode()
        if args in {
            ("rev-parse", f"{snapshot_commit}:{source_root}"),
            ("rev-parse", f"HEAD:{source_root}"),
        }:
            return f"{snapshot_tree}\n".encode()
        if args == ("status", "--porcelain=v1", "--untracked-files=all", "--", source_root):
            return b""
        if len(args) == 2 and args[0] == "show":
            revision, relative = args[1].split(":", 1)
            assert revision == snapshot_commit
            return (tmp_path / relative).read_bytes()
        if len(args) == 2 and args[0] == "rev-parse":
            revision, relative = args[1].split(":", 1)
            assert revision == snapshot_commit
            return f"{entries_by_path[relative]['git_blob_oid']}\n".encode()
        raise AssertionError(f"unexpected git call: {args}")

    monkeypatch.setattr("ldvh.migration.v3_baseline._git", fake_git)

    result = verify_v3_baseline(tmp_path, manifest)
    assert result.valid, result.issues


@pytest.mark.parametrize(
    ("field_path", "replacement"),
    (
        (("snapshot_commit",), "0" * 40),
        (("snapshot_tree",), "0" * 40),
        (("entries", 0, "source_path"), "archive/v3/ldvh-base/pitfalls/wrong.yaml"),
        (("entries", 0, "sha256"), "0" * 64),
        (("entries", 0, "git_blob_oid"), "0" * 40),
        (("entries", 0, "snapshot_commit"), "0" * 40),
    ),
)
def test_tampered_manifest_fields_are_rejected(
    tmp_path: Path,
    field_path: tuple[object, ...],
    replacement: str,
) -> None:
    loaded = json.loads(MANIFEST.read_text(encoding="utf-8"))
    target = loaded
    for segment in field_path[:-1]:
        target = target[segment]
    target[field_path[-1]] = replacement
    manifest = tmp_path / "baseline.json"
    manifest.write_text(json.dumps(loaded, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    result = verify_v3_baseline(PROJECT_ROOT, manifest)
    assert not result.valid
    assert result.issues


def test_duplicate_key_and_noncanonical_manifest_bytes_are_rejected(tmp_path: Path) -> None:
    canonical = MANIFEST.read_text(encoding="utf-8")
    duplicate = tmp_path / "duplicate.json"
    duplicate.write_text(
        canonical.replace('{\n  "entries"', '{\n  "schema_version": 1,\n  "entries"', 1),
        encoding="utf-8",
    )
    noncanonical = tmp_path / "noncanonical.json"
    noncanonical.write_text(canonical.rstrip(), encoding="utf-8")

    duplicate_result = verify_v3_baseline(PROJECT_ROOT, duplicate)
    noncanonical_result = verify_v3_baseline(PROJECT_ROOT, noncanonical)
    assert not duplicate_result.valid
    assert any("duplicate JSON key" in issue.summary for issue in duplicate_result.issues)
    assert not noncanonical_result.valid
    assert any("canonical JSON" in issue.summary for issue in noncanonical_result.issues)


def test_source_id_prefix_must_match_source_type() -> None:
    from ldvh.migration.v3_baseline import _valid_source_id

    assert _valid_source_id("spark", "spark-0001")
    assert not _valid_source_id("spark", "workcase-0001")
    assert not _valid_source_id("workcase", "spark-0001")


def test_cli_returns_one_for_an_invalid_manifest(tmp_path: Path) -> None:
    manifest = tmp_path / "baseline.json"
    manifest.write_text("{}\n", encoding="utf-8")
    completed = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "tools" / "verify_v3_fact_baseline.py"), "--manifest", str(manifest)],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    response = json.loads(completed.stdout)
    assert completed.returncode == 1
    assert response["valid"] is False
