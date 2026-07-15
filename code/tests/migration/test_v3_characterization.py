from __future__ import annotations

import hashlib
import inspect
import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest

import ldvh.migration.v3_characterization as characterization_module
from ldvh.migration.v3_characterization import (
    _join_pointer,
    _reference_classification,
    _reference_observations,
    _structure_counts,
    _time_classification,
    build_v3_source_characterization,
    render_v3_source_characterization,
    verify_v3_source_characterization,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ARTIFACT = PROJECT_ROOT / "migration" / "v3-facts" / "source-characterization.json"
BASELINE = PROJECT_ROOT / "migration" / "v3-facts" / "baseline.json"


def _loaded() -> dict[str, object]:
    return json.loads(ARTIFACT.read_text(encoding="utf-8"))


def _write_artifact(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def test_checked_in_characterization_is_canonical_and_decision_free() -> None:
    result = verify_v3_source_characterization(PROJECT_ROOT, ARTIFACT)
    assert result.valid, result.issues
    assert result.entry_count == 92
    assert ARTIFACT.read_text(encoding="utf-8") == render_v3_source_characterization(PROJECT_ROOT)

    loaded = _loaded()
    summary = loaded["summary"]
    assert summary["entry_count"] == 92
    assert summary["source_type_counts"] == {
        "adr": 0,
        "pitfall": 2,
        "spark": 49,
        "study": 17,
        "workcase": 24,
    }
    assert summary["semantic_reviewed_count"] == summary["target_decided_count"] == 0
    assert summary["mechanical_observation_counts"]["time_observation_count"] == 797
    assert summary["mechanical_observation_counts"]["exact_title_collision_pair_count"] == 1
    assert all(entry["review_state"] == "not_started" for entry in loaded["entries"])
    assert all(
        entry[field] == "undecided"
        for entry in loaded["entries"]
        for field in ("target_identity", "target_type", "target_status", "split_merge")
    )


def test_characterization_joins_baseline_one_to_one_and_records_all_top_level_fields() -> None:
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    loaded = _loaded()
    baseline_by_key = {entry["source_key"]: entry for entry in baseline["entries"]}
    assert [entry["source_key"] for entry in loaded["entries"]] == sorted(baseline_by_key)
    for entry in loaded["entries"]:
        source = baseline_by_key[entry["source_key"]]
        assert entry["source_sha256"] == source["sha256"]
        path = PROJECT_ROOT / source["source_path"]
        raw = path.read_bytes()
        assert hashlib.sha256(raw).hexdigest() == entry["source_sha256"]
        if source["carrier"] == "markdown":
            yaml_text = raw.decode("utf-8").split("---", 2)[1]
        else:
            yaml_text = raw.decode("utf-8")
        from ruamel.yaml import YAML

        fields = YAML(typ="safe").load(yaml_text)
        pointers = {item["source_pointer"] for item in entry["top_level_fields"]}
        assert pointers == {_join_pointer("", key) for key in fields}


@pytest.mark.parametrize(
    ("value", "classification", "risk_codes"),
    (
        ("2026-07-15T18:00:00+08:00", "offset_datetime", []),
        ("2026-07-15T10:00:00Z", "offset_datetime", []),
        ("2026-07-15T18:00:00", "naive_datetime", ["missing-timezone"]),
        ("2026-07-15", "date_only", ["date-only-no-timezone"]),
        ("", "empty_string", ["empty-time-value"]),
        (None, "null", ["null-time-value"]),
        (7, "unrecognized", ["non-string-time-value"]),
        ("tomorrow", "unrecognized", ["unrecognized-time-value"]),
    ),
)
def test_time_classification_preserves_raw_uncertainty(
    value: object,
    classification: str,
    risk_codes: list[str],
) -> None:
    assert _time_classification(value) == (classification, risk_codes)


def test_json_pointer_escape_and_structure_kinds_are_mechanical() -> None:
    assert _join_pointer("", "a~/") == "/a~0~1"
    counts = _structure_counts({"a~/": [None, True, 1, 1.5, "x", {"nested": []}]}, None)
    assert counts == {
        "mapping_node_count": 2,
        "array_node_count": 2,
        "scalar_node_count": 4,
        "null_node_count": 1,
        "maximum_depth": 3,
    }


@pytest.mark.parametrize(
    ("value", "syntactic_class", "candidate"),
    (
        ("spark-0001", "exact_fact_id", "spark-0001"),
        ("ldvh-base/sparks/spark-0001-title.yaml", "fact_path", "spark-0001"),
        ("specs/20-Spark-火花.md", "document_path", None),
        ("https://example.com/a", "url", None),
        ("https://example.com/spark-0001", "url", None),
        ("spec-key::section", "rule_ref", None),
        ("current-conversation", "opaque", None),
        ("", "empty", None),
        (None, "null", None),
    ),
)
def test_reference_classification_is_syntactic_only(
    value: object,
    syntactic_class: str,
    candidate: str | None,
) -> None:
    assert _reference_classification(value) == (syntactic_class, candidate)


def test_reference_observations_never_decide_v4_relations() -> None:
    fields = {
        "input_refs": [
            "spark-0001",
            "spark-0001",
            "spark-9999",
            "docs/a.md",
            "https://example.com",
            "opaque",
        ],
        "description": "spark-0002 in ordinary prose is not scanned",
    }
    observed = _reference_observations(
        fields,
        "spark:spark-0001",
        {"spark-0001": "spark:spark-0001", "spark-0002": "spark:spark-0002"},
    )
    assert len(observed) == 6
    assert all(item["v4_relation_decision"] == "undecided" for item in observed)
    assert all(item["legacy_field_role"] == "input_refs" for item in observed)
    assert all("raw_value" not in item for item in observed)
    assert all(len(item["raw_value_sha256"]) == 64 for item in observed)
    assert all(item["raw_value_byte_count"] >= 2 for item in observed)
    self_refs = [item for item in observed if item.get("resolved_baseline_source_key") == "spark:spark-0001"]
    assert len(self_refs) == 2
    assert all("legacy-self-reference-candidate" in item["risk_codes"] for item in self_refs)
    assert all("duplicate-legacy-target-reference" in item["risk_codes"] for item in self_refs)
    assert any("legacy-fact-target-not-in-baseline" in item["risk_codes"] for item in observed)


def test_real_legacy_shape_anomalies_and_study_regions_are_preserved() -> None:
    loaded = _loaded()
    entries = {entry["source_key"]: entry for entry in loaded["entries"]}
    spark = entries["spark:spark-0032"]
    workcase = entries["workcase:workcase-0024"]
    study = entries["study:study-0011"]
    spark_fields = {field["source_pointer"]: field for field in spark["top_level_fields"]}
    workcase_fields = {field["source_pointer"]: field for field in workcase["top_level_fields"]}
    assert spark_fields["/resolved_to"]["value_kind"] == "mapping"
    assert workcase_fields["/residual_risks"]["value_kind"] == "string"
    assert study["structure_counts"]["study_body"]["h1_count"] >= 1
    heading_regions = [region for region in study["content_regions"] if region["locator"].startswith("study-body:H")]
    assert any(region["locator"].startswith("study-body:H2:") for region in heading_regions)
    assert all("heading_text_sha256" in region for region in heading_regions)


@pytest.mark.parametrize(
    "mutation",
    (
        "baseline_digest",
        "source_sha",
        "missing_entry",
        "duplicate_entry",
        "out_of_order",
        "top_level_digest",
        "time_classification",
        "relation_decision",
        "target_decision",
        "unknown_field",
    ),
)
def test_characterization_tampering_is_rejected(tmp_path: Path, mutation: str) -> None:
    loaded = deepcopy(_loaded())
    if mutation == "baseline_digest":
        loaded["baseline_binding"]["manifest_sha256"] = "0" * 64
    elif mutation == "source_sha":
        loaded["entries"][0]["source_sha256"] = "0" * 64
    elif mutation == "missing_entry":
        loaded["entries"].pop()
    elif mutation == "duplicate_entry":
        loaded["entries"].append(deepcopy(loaded["entries"][-1]))
    elif mutation == "out_of_order":
        loaded["entries"][0], loaded["entries"][1] = loaded["entries"][1], loaded["entries"][0]
    elif mutation == "top_level_digest":
        loaded["entries"][0]["top_level_fields"][0]["value_sha256"] = "0" * 64
    elif mutation == "time_classification":
        loaded["entries"][2]["time_observations"][0]["classification"] = "date_only"
    elif mutation == "relation_decision":
        loaded["entries"][0]["reference_observations"][0]["v4_relation_decision"] = "mapped"
    elif mutation == "target_decision":
        loaded["entries"][0]["target_type"] = "pitfall"
    elif mutation == "unknown_field":
        loaded["entries"][0]["mapped"] = True
    artifact = tmp_path / "characterization.json"
    _write_artifact(artifact, loaded)
    result = verify_v3_source_characterization(PROJECT_ROOT, artifact)
    assert not result.valid
    assert result.issues


def test_duplicate_key_noncanonical_bytes_and_invalid_cli_exit_are_rejected(tmp_path: Path) -> None:
    canonical = ARTIFACT.read_text(encoding="utf-8")
    duplicate = tmp_path / "duplicate.json"
    duplicate.write_text(
        canonical.replace('{\n  "artifact_kind"', '{\n  "schema_version": 1,\n  "artifact_kind"', 1),
        encoding="utf-8",
    )
    noncanonical = tmp_path / "noncanonical.json"
    noncanonical.write_text(canonical.rstrip(), encoding="utf-8")
    assert not verify_v3_source_characterization(PROJECT_ROOT, duplicate).valid
    assert not verify_v3_source_characterization(PROJECT_ROOT, noncanonical).valid

    completed = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "tools" / "verify_v3_fact_characterization.py"),
            "--artifact",
            str(noncanonical),
        ],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 1
    assert json.loads(completed.stdout)["valid"] is False


def test_characterization_artifact_symlink_and_non_file_are_rejected(tmp_path: Path) -> None:
    target = tmp_path / "canonical.json"
    target.write_bytes(ARTIFACT.read_bytes())
    linked = tmp_path / "linked.json"
    try:
        linked.symlink_to(target)
    except OSError as exc:
        pytest.skip(f"symlinks unavailable: {exc}")
    linked_result = verify_v3_source_characterization(PROJECT_ROOT, linked)
    directory_result = verify_v3_source_characterization(PROJECT_ROOT, tmp_path)
    assert not linked_result.valid
    assert linked_result.issues[0].code == "artifact"
    assert "symbolic link" in linked_result.issues[0].summary
    assert not directory_result.valid
    assert directory_result.issues[0].code == "artifact"
    assert "regular file" in directory_result.issues[0].summary


def test_characterizer_has_no_dependency_on_v4_fact_specs_or_registry() -> None:
    source = inspect.getsource(characterization_module)
    assert "ldvh.specs" not in source
    assert "ldvh.facts" not in source
    built = build_v3_source_characterization(PROJECT_ROOT)
    assert built["summary"]["semantic_reviewed_count"] == 0
    assert built["summary"]["target_decided_count"] == 0
