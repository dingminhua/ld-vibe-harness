from __future__ import annotations

import base64
import hashlib
import subprocess
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace

import pytest
from ruamel.yaml import YAML

from ldvh.facts import creation_application, web_direct_capture
from ldvh.facts.contracts import LAYOUTS
from ldvh.facts.creation import CreationBoundary, _allocator_paths
from ldvh.facts.schema import project_fact_schemas
from ldvh.facts.web_direct_capture import (
    UNICODE_15_1_NFC_INERT_RANGES,
    canonicalize_web_capture,
    create_web_spark_direct_capture,
    validate_web_direct_source_ref,
)
from ldvh.filesystem import AtomicWriteResult
from ldvh.specs.repository import inspect_repository

ASCII_DIGEST = "5626348cede47a57cdb59910a5b23e11013c5508554b1998ba92bcd4ab18ec69"
ASCII_BASE64 = "eyJwcmlvcml0eSI6IlAzIiwic3VtbWFyeSI6IkJldGEiLCJ0aXRsZSI6IkFscGhhIn0="
UNICODE_DIGEST = "e3208211e97f642d5bb5e363cd5ea64c68c7f872c6aca294edca6ccc60d491ef"
UNICODE_BASE64 = (
    "eyJwcmlvcml0eSI6IlAyIiwic3VtbWFyeSI6IuS4reKAqOaWhyBcIui3r+W+hFxcXCJcblx1MDAwMfCfmIAi"
    "LCJ0aXRsZSI6IkNhZsOpIFwiQS9CXCIifQ=="
)


def _git(project: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(project), *arguments],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _fixture(current_specs_repository: Path, tmp_path: Path):
    project = tmp_path / "project"
    project.mkdir()
    _git(project, "init", "-q")
    common = Path(_git(project, "rev-parse", "--path-format=absolute", "--git-common-dir"))
    schemas = project_fact_schemas(inspect_repository(current_specs_repository))
    return CreationBoundary("sample", project, common), schemas


def _request(title: str = "Alpha", description: str = "Beta", priority: str = "P3") -> dict[str, str]:
    return {"title": title, "description": description, "priority": priority}


def _counter(boundary: CreationBoundary) -> Path:
    return _allocator_paths(boundary, LAYOUTS["spark"])[1]


def _relate_created_spark(boundary: CreationBoundary, target_id: str) -> None:
    path = boundary.worktree_root / "facts/sparks/spark-0001.yaml"
    yaml = YAML(typ="rt")
    fields = yaml.load(path.read_text(encoding="utf-8"))
    fields["relations"] = [
        {
            "relation_key": "related-to",
            "target": {
                "governed_project_id": boundary.governed_project_id,
                "fact_type_key": "workcase",
                "object_id": target_id,
            },
        }
    ]
    with path.open("w", encoding="utf-8") as stream:
        yaml.dump(fields, stream)


def test_canonical_vectors_match_rule_contract() -> None:
    ascii_identity = canonicalize_web_capture(_request("  Alpha  ", "  Beta  ", "P3"))
    assert ascii_identity.canonical_bytes == b'{"priority":"P3","summary":"Beta","title":"Alpha"}'
    assert ascii_identity.digest == ASCII_DIGEST
    assert ascii_identity.locator.removeprefix("data:application/json;base64,") == ASCII_BASE64

    unicode_identity = canonicalize_web_capture(
        _request(
            '\u2003Cafe\u0301 "A/B"\u00a0',
            '\u3000中\u2028文 "路径\\"\n\u0001😀\u00a0',
            "P2",
        )
    )
    assert unicode_identity.digest == UNICODE_DIGEST
    assert unicode_identity.locator.removeprefix("data:application/json;base64,") == UNICODE_BASE64


def test_unicode_15_1_additions_are_nfc_inert_under_python_312_data() -> None:
    observed = 0
    for start, end in UNICODE_15_1_NFC_INERT_RANGES:
        for codepoint in range(start, end + 1):
            character = chr(codepoint)
            assert unicodedata.combining(character) == 0
            assert unicodedata.decomposition(character) == ""
            assert unicodedata.normalize("NFC", character) == character
            assert unicodedata.normalize("NFC", "A\u0301" + character + "\u0301") == "Á" + character + "\u0301"
            observed += 1
    assert observed == 627


@pytest.mark.parametrize(
    "capture_request",
    [
        {"title": "Alpha", "description": "Beta", "priority": "P3", "status": "open"},
        {"title": "\u3000", "description": "Beta", "priority": "P3"},
        {"title": "Alpha\ud800", "description": "Beta", "priority": "P3"},
        {"title": "Alpha", "description": "Beta", "priority": "p3"},
        {"title": True, "description": "Beta", "priority": "P3"},
    ],
)
def test_capture_request_is_closed_and_fail_closed(capture_request: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        canonicalize_web_capture(capture_request)


def test_source_ref_rejects_noncanonical_base64_and_digest_tampering() -> None:
    identity = canonicalize_web_capture(_request())
    reference = {
        "kind": "web-direct-capture",
        "locator": identity.locator,
        "version": f"sha256:{identity.digest}",
        "observed_at": "2026-07-15T16:00:00+08:00",
    }
    assert validate_web_direct_source_ref(reference).digest == identity.digest
    tampered = dict(reference, version="sha256:" + ("0" * 64))
    with pytest.raises(ValueError, match="digest"):
        validate_web_direct_source_ref(tampered)
    encoded = identity.locator.removeprefix("data:application/json;base64,")
    noncanonical = dict(reference, locator="data:application/json;base64," + encoded.rstrip("="))
    with pytest.raises(ValueError, match="Base64"):
        validate_web_direct_source_ref(noncanonical)


def test_service_creates_once_and_duplicate_does_not_consume_counter(
    current_specs_repository: Path,
    tmp_path: Path,
) -> None:
    boundary, schemas = _fixture(current_specs_repository, tmp_path)

    created = create_web_spark_direct_capture(boundary, schemas, _request())
    before = _counter(boundary).read_bytes()
    duplicate = create_web_spark_direct_capture(boundary, schemas, _request())

    assert created.status == "created"
    assert created.actual_ref == {
        "governed_project_id": "sample",
        "fact_type_key": "spark",
        "object_id": "spark-0001",
    }
    assert created.fact_object is not None
    assert created.fact_object["status"] == "open"
    assert created.fact_object["source_refs"][0]["kind"] == "web-direct-capture"
    assert duplicate.status == "exact_duplicate"
    assert duplicate.existing_ref == {
        "governed_project_id": "sample",
        "fact_type_key": "spark",
        "object_id": "spark-0001",
        "status": "open",
    }
    assert _counter(boundary).read_bytes() == before
    assert len(tuple((boundary.worktree_root / "facts/sparks").glob("*.yaml"))) == 1


def test_concurrent_same_capture_has_one_creator_and_one_duplicate(
    current_specs_repository: Path,
    tmp_path: Path,
) -> None:
    boundary, schemas = _fixture(current_specs_repository, tmp_path)

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = tuple(
            executor.map(lambda _: create_web_spark_direct_capture(boundary, schemas, _request()), range(2))
        )

    assert sorted(result.status for result in results) == ["created", "exact_duplicate"]
    assert _counter(boundary).read_bytes() == b"1\n"


def test_create_conflict_restarts_full_scan_preview_and_budget(
    current_specs_repository: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    boundary, schemas = _fixture(current_specs_repository, tmp_path)
    real_scan = web_direct_capture.discover_fact_type_raw
    real_preview = web_direct_capture.preview_fact_creation_locked
    real_create = creation_application.atomic_create_text
    counts = {"scan": 0, "preview": 0, "create": 0}

    def counted_scan(*args, **kwargs):
        counts["scan"] += 1
        return real_scan(*args, **kwargs)

    def counted_preview(*args, **kwargs):
        counts["preview"] += 1
        return real_preview(*args, **kwargs)

    def conflict_once(*args, **kwargs):
        counts["create"] += 1
        if counts["create"] == 1:
            return AtomicWriteResult("conflict", "not_committed", "unknown", "clean")
        return real_create(*args, **kwargs)

    monkeypatch.setattr(web_direct_capture, "discover_fact_type_raw", counted_scan)
    monkeypatch.setattr(web_direct_capture, "preview_fact_creation_locked", counted_preview)
    monkeypatch.setattr(creation_application, "atomic_create_text", conflict_once)

    result = create_web_spark_direct_capture(boundary, schemas, _request())

    assert result.status == "created"
    assert result.actual_ref is not None and result.actual_ref["object_id"] == "spark-0002"
    assert counts == {"scan": 2, "preview": 2, "create": 2}
    assert _counter(boundary).read_bytes() == b"2\n"


def test_open_current_identity_is_checked_after_legal_content_change(
    current_specs_repository: Path,
    tmp_path: Path,
) -> None:
    boundary, schemas = _fixture(current_specs_repository, tmp_path)
    assert create_web_spark_direct_capture(boundary, schemas, _request()).status == "created"
    path = boundary.worktree_root / "facts/sparks/spark-0001.yaml"
    yaml = YAML(typ="rt")
    fields = yaml.load(path.read_text(encoding="utf-8"))
    fields["title"] = "Current B"
    fields["summary"] = "Current summary B"
    fields["priority"] = "P1"
    fields["updated_at"] = "2026-07-15T17:00:00+08:00"
    with path.open("w", encoding="utf-8") as stream:
        yaml.dump(fields, stream)

    duplicate = create_web_spark_direct_capture(boundary, schemas, _request("Current B", "Current summary B", "P1"))

    assert duplicate.status == "exact_duplicate"
    assert duplicate.existing_ref is not None and duplicate.existing_ref["object_id"] == "spark-0001"


def test_damaged_historical_source_fails_closed_before_current_identity(
    current_specs_repository: Path,
    tmp_path: Path,
) -> None:
    boundary, schemas = _fixture(current_specs_repository, tmp_path)
    assert create_web_spark_direct_capture(boundary, schemas, _request()).status == "created"
    path = boundary.worktree_root / "facts/sparks/spark-0001.yaml"
    yaml = YAML(typ="rt")
    fields = yaml.load(path.read_text(encoding="utf-8"))
    fields["source_refs"][0]["version"] = "sha256:" + ("0" * 64)
    with path.open("w", encoding="utf-8") as stream:
        yaml.dump(fields, stream)
    before = _counter(boundary).read_bytes()

    result = create_web_spark_direct_capture(boundary, schemas, _request())

    assert result.status == "integrity_conflict"
    assert result.code == "web_capture_source_invalid"
    assert _counter(boundary).read_bytes() == before


def test_missing_relation_target_is_integrity_conflict_without_state_change(
    current_specs_repository: Path,
    tmp_path: Path,
) -> None:
    boundary, schemas = _fixture(current_specs_repository, tmp_path)
    assert create_web_spark_direct_capture(boundary, schemas, _request()).status == "created"
    _relate_created_spark(boundary, "workcase-9999")
    before = _counter(boundary).read_bytes()

    result = create_web_spark_direct_capture(boundary, schemas, _request())

    assert result.status == "integrity_conflict"
    assert result.code == "spark_integrity_conflict"
    assert _counter(boundary).read_bytes() == before
    assert len(tuple((boundary.worktree_root / "facts/sparks").glob("*.yaml"))) == 1


def test_unreadable_relation_target_is_unavailable_without_state_change(
    current_specs_repository: Path,
    tmp_path: Path,
) -> None:
    boundary, schemas = _fixture(current_specs_repository, tmp_path)
    assert create_web_spark_direct_capture(boundary, schemas, _request()).status == "created"
    _relate_created_spark(boundary, "workcase-9999")
    target = boundary.worktree_root / "facts/workcases/workcase-9999.yaml"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"x" * (4 * 1024 * 1024 + 1))
    before = _counter(boundary).read_bytes()

    result = create_web_spark_direct_capture(boundary, schemas, _request())

    assert result.status == "unavailable"
    assert result.code == "spark_coverage_unavailable"
    assert _counter(boundary).read_bytes() == before
    assert len(tuple((boundary.worktree_root / "facts/sparks").glob("*.yaml"))) == 1


def test_terminal_spark_uses_validated_historical_identity_without_priority(
    current_specs_repository: Path,
    tmp_path: Path,
) -> None:
    boundary, schemas = _fixture(current_specs_repository, tmp_path)
    assert create_web_spark_direct_capture(boundary, schemas, _request()).status == "created"
    path = boundary.worktree_root / "facts/sparks/spark-0001.yaml"
    yaml = YAML(typ="rt")
    fields = yaml.load(path.read_text(encoding="utf-8"))
    fields["status"] = "discarded"
    fields.pop("priority")
    fields["disposition_summary"] = "The captured signal is no longer worth tracking."
    fields["closed_at"] = fields["updated_at"]
    fields["evidence_refs"] = [{"kind": "repository-path", "locator": "docs/disposition.md"}]
    with path.open("w", encoding="utf-8") as stream:
        yaml.dump(fields, stream)

    result = create_web_spark_direct_capture(boundary, schemas, _request())

    assert result.status == "exact_duplicate"
    assert result.existing_ref is not None and result.existing_ref["status"] == "discarded"


def test_multiple_objects_with_same_historical_identity_are_integrity_conflict(
    current_specs_repository: Path,
    tmp_path: Path,
) -> None:
    boundary, schemas = _fixture(current_specs_repository, tmp_path)
    assert create_web_spark_direct_capture(boundary, schemas, _request()).status == "created"
    first = boundary.worktree_root / "facts/sparks/spark-0001.yaml"
    second = boundary.worktree_root / "facts/sparks/spark-0002.yaml"
    second.write_text(first.read_text(encoding="utf-8").replace("spark-0001", "spark-0002"), encoding="utf-8")
    before = _counter(boundary).read_bytes()

    result = create_web_spark_direct_capture(boundary, schemas, _request())

    assert result.status == "integrity_conflict"
    assert result.code == "multiple_exact_duplicates"
    assert result.details == ("spark-0001", "spark-0002")
    assert _counter(boundary).read_bytes() == before


def test_noncanonical_spark_filename_is_integrity_conflict_without_counter(
    current_specs_repository: Path,
    tmp_path: Path,
) -> None:
    boundary, schemas = _fixture(current_specs_repository, tmp_path)
    directory = boundary.worktree_root / "facts/sparks"
    directory.mkdir(parents=True)
    (directory / "legacy.yaml").write_text("status: open\n", encoding="utf-8")

    result = create_web_spark_direct_capture(boundary, schemas, _request())

    assert result.status == "integrity_conflict"
    assert not _counter(boundary).exists()


def test_conservative_budget_rejects_before_allocator_state(
    current_specs_repository: Path,
    tmp_path: Path,
) -> None:
    boundary, schemas = _fixture(current_specs_repository, tmp_path)

    result = create_web_spark_direct_capture(boundary, schemas, _request(description="x" * 3_200_000))

    assert result.status == "invalid"
    assert result.code == "capture_too_large"
    assert not (boundary.git_common_dir / "ldvh").exists()


def test_durability_and_unsupported_unicode_fail_before_allocator_state(
    current_specs_repository: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    boundary, schemas = _fixture(current_specs_repository, tmp_path)
    monkeypatch.setattr(web_direct_capture, "durable_writes_enabled", lambda: False)
    durability = create_web_spark_direct_capture(boundary, schemas, _request())
    assert durability.code == "durable_write_unavailable"
    assert not (boundary.git_common_dir / "ldvh").exists()

    monkeypatch.setattr(
        web_direct_capture,
        "unicodedata",
        SimpleNamespace(unidata_version="16.0.0"),
    )
    unicode_result = create_web_spark_direct_capture(boundary, schemas, _request())
    assert unicode_result.code == "unicode_nfc_unavailable"
    assert not (boundary.git_common_dir / "ldvh").exists()


def test_linked_worktree_uses_shared_counter_but_selected_worktree_duplicate_scope(
    current_specs_repository: Path,
    tmp_path: Path,
) -> None:
    boundary, schemas = _fixture(current_specs_repository, tmp_path)
    marker = boundary.worktree_root / "tracked.txt"
    marker.write_text("tracked\n", encoding="utf-8")
    _git(boundary.worktree_root, "add", "tracked.txt")
    _git(
        boundary.worktree_root,
        "-c",
        "user.name=LDVH Test",
        "-c",
        "user.email=ldvh@example.invalid",
        "commit",
        "-qm",
        "initial",
    )
    linked = tmp_path / "linked worktree"
    _git(boundary.worktree_root, "worktree", "add", "-qb", "linked-capture", str(linked))
    assert create_web_spark_direct_capture(boundary, schemas, _request()).status == "created"
    linked_boundary = CreationBoundary("sample", linked, boundary.git_common_dir)

    linked_result = create_web_spark_direct_capture(linked_boundary, schemas, _request())

    assert linked_result.status == "created"
    assert linked_result.actual_ref is not None and linked_result.actual_ref["object_id"] == "spark-0002"
    assert (boundary.worktree_root / "facts/sparks/spark-0001.yaml").is_file()
    assert (linked / "facts/sparks/spark-0002.yaml").is_file()


def test_id_growth_from_9999_to_10000_is_repreviewed_in_final_yaml(
    current_specs_repository: Path,
    tmp_path: Path,
) -> None:
    boundary, schemas = _fixture(current_specs_repository, tmp_path)
    counter = _counter(boundary)
    counter.parent.mkdir(parents=True)
    counter.write_bytes(b"9999\n")

    result = create_web_spark_direct_capture(boundary, schemas, _request())

    assert result.status == "created"
    assert result.actual_ref is not None and result.actual_ref["object_id"] == "spark-10000"
    assert result.fact_object is not None and result.fact_object["object_id"] == "spark-10000"
    assert counter.read_bytes() == b"10000\n"


def test_locator_payload_is_self_contained() -> None:
    identity = canonicalize_web_capture(_request())
    decoded = base64.b64decode(identity.locator.split(",", 1)[1], validate=True)
    assert hashlib.sha256(decoded).hexdigest() == identity.digest
    assert decoded == identity.canonical_bytes
