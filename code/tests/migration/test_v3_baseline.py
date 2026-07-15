from __future__ import annotations

import json
import re
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


def test_v3_baseline_exposes_time_and_closed_workcase_migration_blockers() -> None:
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


def test_root_v3_object_is_reported_as_out_of_baseline(tmp_path: Path) -> None:
    root = tmp_path / "ldvh-base" / "sparks"
    root.mkdir(parents=True)
    (root / "spark-0050.yaml").write_text("id: spark-0050\ntype: spark\nstatus: pending\n", encoding="utf-8")

    from ldvh.migration.v3_baseline import _detect_out_of_baseline

    issues = _detect_out_of_baseline(tmp_path)
    assert [(issue.code, issue.source_path) for issue in issues] == [
        ("out-of-baseline", "ldvh-base/sparks/spark-0050.yaml")
    ]


@pytest.mark.parametrize(
    ("directory", "filename"),
    (("sparks", "spark-0050.yml"), ("adrs", "adr-0001.yaml"), ("studies", "study-0018.md")),
)
def test_every_legacy_web_carrier_is_reported_out_of_baseline(
    tmp_path: Path,
    directory: str,
    filename: str,
) -> None:
    parent = tmp_path / "ldvh-base" / directory
    parent.mkdir(parents=True)
    path = parent / filename
    path.write_text("id: candidate\n", encoding="utf-8")

    from ldvh.migration.v3_baseline import _detect_out_of_baseline

    issues = _detect_out_of_baseline(tmp_path)
    assert [(issue.code, issue.source_path) for issue in issues] == [
        ("out-of-baseline", path.relative_to(tmp_path).as_posix())
    ]


@pytest.mark.parametrize(
    "link_kind",
    ("root", "broken-root", "directory", "broken-directory", "member", "broken-member"),
)
def test_legacy_symlinks_fail_closed(tmp_path: Path, link_kind: str) -> None:
    target = tmp_path / "target"
    target.mkdir()
    legacy = tmp_path / "ldvh-base"
    try:
        if link_kind in {"root", "broken-root"}:
            root_target = target if link_kind == "root" else tmp_path / "missing-root"
            legacy.symlink_to(root_target, target_is_directory=True)
        else:
            sparks = legacy / "sparks"
            if link_kind in {"directory", "broken-directory"}:
                legacy.mkdir()
                directory_target = target if link_kind == "directory" else tmp_path / "missing-directory"
                sparks.symlink_to(directory_target, target_is_directory=True)
            else:
                sparks.mkdir(parents=True)
                link_target = target / "missing.yaml" if link_kind == "broken-member" else target
                (sparks / "spark-0050.yaml").symlink_to(link_target, target_is_directory=link_kind == "member")
    except OSError as exc:
        pytest.skip(f"symlink creation is unavailable: {exc}")

    from ldvh.migration.v3_baseline import _detect_out_of_baseline

    issues = _detect_out_of_baseline(tmp_path)
    assert len(issues) == 1
    assert issues[0].code == "out-of-baseline"
    assert "symlink" in issues[0].summary


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


def test_any_v4_fact_file_is_rejected_during_baseline_only_stage(tmp_path: Path) -> None:
    path = tmp_path / "facts" / "sparks" / "spark-0001.yaml"
    path.parent.mkdir(parents=True)
    path.write_text("object_id: spark-0001\n", encoding="utf-8")

    from ldvh.migration.v3_baseline import _detect_out_of_baseline

    issues = _detect_out_of_baseline(tmp_path)
    assert [(issue.code, issue.source_path) for issue in issues] == [
        ("unexpected-v4-instance", "facts/sparks/spark-0001.yaml")
    ]
