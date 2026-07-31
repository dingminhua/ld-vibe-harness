from __future__ import annotations

import hashlib
import os
from pathlib import Path

import pytest

from ldvh.facts import file_asset
from ldvh.facts.contracts import LAYOUTS
from ldvh.facts.file_asset import DEFAULT_PAYLOAD_BUDGET, read_file_asset
from ldvh.facts.schema import FactSchema, ProjectedField

pytestmark = pytest.mark.skipif(
    os.name != "posix", reason="FileAsset carrier requires POSIX directory descriptors"
)


def _schema() -> FactSchema:
    def field(
        path: str,
        json_type: str = "string",
        presence: str = "required",
        structure: str | None = None,
    ) -> ProjectedField:
        return ProjectedField(path, json_type, presence, structure, "test-registry")

    return FactSchema(
        "file-asset",
        (
            field("object_id"),
            field("fact_type_key"),
            field("title"),
            field("created_at"),
            field("updated_at"),
            field("status"),
            field("filename"),
            field("media_type"),
            field("size_bytes", "integer"),
            field("content_sha256"),
            field("signature", "object", structure="file-asset-signature"),
            field("signature.signer_type"),
            field("signature.agent_id", presence="conditional"),
            field("signature.host_environment", presence="conditional"),
            field("disposition_summary", presence="conditional"),
        ),
    )


def _manifest(
    payload: bytes,
    *,
    object_id: str = "file-asset-0001",
    status: str = "active",
    signature: str = "  signer_type: human",
    disposition: str | None = None,
) -> str:
    lines = [
        f'object_id: "{object_id}"',
        'fact_type_key: "file-asset"',
        'title: "审计文件"',
        'created_at: "2026-07-31T10:00:00+08:00"',
        'updated_at: "2026-07-31T10:00:00+08:00"',
        f'status: "{status}"',
        'filename: "audit.bin"',
        'media_type: "application/octet-stream"',
        f"size_bytes: {len(payload)}",
        f'content_sha256: "{hashlib.sha256(payload).hexdigest()}"',
        "signature:",
        signature,
    ]
    if disposition is not None:
        lines.append(f'disposition_summary: "{disposition}"')
    return "\n".join(lines) + "\n"


def _asset(
    root: Path,
    payload: bytes = b"objective bytes\n",
    *,
    object_id: str = "file-asset-0001",
    manifest: str | None = None,
) -> Path:
    directory = root / "ldvh-base/file-assets" / object_id
    directory.mkdir(parents=True)
    (directory / "file-asset.yaml").write_text(
        _manifest(payload, object_id=object_id) if manifest is None else manifest,
        encoding="utf-8",
    )
    (directory / "payload").write_bytes(payload)
    return directory


def _read(root: Path, object_id: str = "file-asset-0001", **budgets: int):
    return read_file_asset(root, LAYOUTS["file-asset"], _schema(), object_id, **budgets)


def test_human_file_asset_confirms_current_bytes_without_returning_payload(tmp_path: Path) -> None:
    payload = "外部提供的审计文档\n".encode()
    _asset(tmp_path, payload)

    result = _read(tmp_path)

    assert result.check_status == "mechanically_valid"
    assert result.coverage == (
        "manifest-read",
        "members-closed",
        "payload-size-read",
        "payload-sha256-computed",
    )
    assert result.fields is not None and result.fields["signature"] == {"signer_type": "human"}
    assert result.observed_size_bytes == len(payload)
    assert result.observed_content_sha256 == hashlib.sha256(payload).hexdigest()
    assert result.payload_matches_manifest is True
    assert result.current_bytes_confirmed is True
    assert result.default_candidate is True
    assert result.payload_canonical_path.endswith("/file-asset-0001/payload")
    assert not hasattr(result, "payload_bytes")


def test_ai_agent_signature_accepts_binary_payload_without_decoding_it(tmp_path: Path) -> None:
    payload = b"\x00\xff\x89PNG\r\n\x1a\n"
    signature = "\n".join(
        (
            '  signer_type: "ai-agent"',
            '  agent_id: "codex"',
            '  host_environment: "Codex Desktop"',
        )
    )
    _asset(tmp_path, payload, manifest=_manifest(payload, signature=signature))

    result = _read(tmp_path)

    assert result.check_status == "mechanically_valid"
    assert result.fields is not None
    assert result.fields["signature"] == {
        "signer_type": "ai-agent",
        "agent_id": "codex",
        "host_environment": "Codex Desktop",
    }
    assert result.current_bytes_confirmed is True


def test_archived_file_asset_is_exactly_readable_but_not_default_candidate(tmp_path: Path) -> None:
    payload = b"historical snapshot"
    _asset(
        tmp_path,
        payload,
        manifest=_manifest(
            payload,
            status="archived",
            disposition="已由后续版本取代，保留历史回读",
        ),
    )

    result = _read(tmp_path)

    assert result.check_status == "mechanically_valid"
    assert result.current_bytes_confirmed is True
    assert result.default_candidate is False


def test_missing_payload_is_invalid_and_never_confirms_current_bytes(tmp_path: Path) -> None:
    directory = _asset(tmp_path)
    (directory / "payload").unlink()

    result = _read(tmp_path)

    assert result.check_status == "invalid"
    assert result.coverage == ("manifest-read",)
    assert result.payload_matches_manifest is None
    assert result.current_bytes_confirmed is False
    assert any(issue.field_path == "payload" and "缺少" in issue.summary for issue in result.issues)


def test_tampered_payload_has_full_coverage_but_fails_integrity(tmp_path: Path) -> None:
    directory = _asset(tmp_path, b"registered")
    (directory / "payload").write_bytes(b"tampered")

    result = _read(tmp_path)

    assert result.check_status == "invalid"
    assert result.coverage[-2:] == ("payload-size-read", "payload-sha256-computed")
    assert result.payload_matches_manifest is False
    assert result.current_bytes_confirmed is False
    assert {issue.field_path for issue in result.issues if issue.category == "integrity"} == {
        "size_bytes",
        "content_sha256",
    }


def test_unknown_member_breaks_closed_carrier(tmp_path: Path) -> None:
    directory = _asset(tmp_path)
    (directory / "notes.txt").write_text("not part of carrier", encoding="utf-8")

    result = _read(tmp_path)

    assert result.check_status == "invalid"
    assert "members-closed" not in result.coverage
    assert result.payload_matches_manifest is True
    assert any(issue.field_path == "notes.txt" and "未知成员" in issue.summary for issue in result.issues)


@pytest.mark.parametrize("member", ["payload", "file-asset.yaml"])
def test_symlink_member_is_rejected_without_following_target(tmp_path: Path, member: str) -> None:
    directory = _asset(tmp_path)
    (directory / member).unlink()
    target = tmp_path / f"outside-{member}"
    target.write_bytes(b"outside")
    try:
        (directory / member).symlink_to(target)
    except OSError as error:
        pytest.skip(f"symlink creation unavailable: {error}")

    result = _read(tmp_path)

    assert result.check_status == "invalid"
    assert result.current_bytes_confirmed is False
    assert any(issue.field_path == member and "symlink" in issue.summary for issue in result.issues)


def test_symlink_object_directory_is_rejected_without_following_it(tmp_path: Path) -> None:
    target = tmp_path / "outside" / "file-asset-0001"
    target.mkdir(parents=True)
    namespace = tmp_path / "ldvh-base/file-assets"
    namespace.mkdir(parents=True)
    try:
        (namespace / "file-asset-0001").symlink_to(target, target_is_directory=True)
    except OSError as error:
        pytest.skip(f"symlink creation unavailable: {error}")

    result = _read(tmp_path)

    assert result.check_status == "invalid"
    assert result.coverage == ()


@pytest.mark.parametrize(
    ("manifest_factory", "expected_path"),
    [
        (lambda payload: _manifest(payload, object_id="file-asset-9999"), "object_id"),
        (
            lambda payload: _manifest(
                payload,
                signature='  signer_type: "human"\n  agent_id: "must-not-appear"',
            ),
            "signature.agent_id",
        ),
        (lambda payload: _manifest(payload, status="archived"), "disposition_summary"),
        (lambda payload: _manifest(payload).replace('status: "active"', "status:\n  - active"), "status"),
    ],
)
def test_identity_signature_and_lifecycle_shape_failures_are_explicit(
    tmp_path: Path,
    manifest_factory,
    expected_path: str,
) -> None:
    payload = b"shape fixture"
    _asset(tmp_path, payload, manifest=manifest_factory(payload))

    result = _read(tmp_path)

    assert result.check_status == "invalid"
    assert any(issue.field_path == expected_path for issue in result.issues)


def test_payload_budget_exhaustion_reports_incomplete_coverage(tmp_path: Path) -> None:
    _asset(tmp_path, b"larger than selected budget")

    result = _read(tmp_path, payload_budget=4)

    assert result.check_status == "unavailable"
    assert result.coverage == ("manifest-read", "members-closed")
    assert result.observed_size_bytes is None
    assert any(issue.category == "resource" and "payload" in issue.summary for issue in result.issues)


def test_default_budget_rejects_large_binary_without_truncation(tmp_path: Path) -> None:
    _asset(tmp_path, b"\x00" * (DEFAULT_PAYLOAD_BUDGET + 1))

    result = _read(tmp_path)

    assert result.check_status == "unavailable"
    assert result.observed_size_bytes is None
    assert result.current_bytes_confirmed is False


def test_binary_manifest_is_invalid_even_though_payload_may_be_binary(tmp_path: Path) -> None:
    directory = _asset(tmp_path)
    (directory / "file-asset.yaml").write_bytes(b"\xff\xfe\x00")

    result = _read(tmp_path)

    assert result.check_status == "invalid"
    assert result.fields is None
    assert any(issue.category == "parse" and "UTF-8" in issue.summary for issue in result.issues)


def test_registered_layout_rejects_noncanonical_object_id_before_opening(tmp_path: Path) -> None:
    result = _read(tmp_path, "not-an-object-id")

    assert "file-asset" in LAYOUTS
    assert result.check_status == "invalid"
    assert result.coverage == ()


def test_member_enumeration_stops_at_third_entry(tmp_path: Path) -> None:
    directory = _asset(tmp_path)
    for index in range(100):
        (directory / f"unknown-{index:03d}").touch()

    result = _read(tmp_path)

    assert result.check_status == "invalid"
    assert "members-closed" not in result.coverage
    assert sum(
        issue.field_path is not None and issue.field_path.startswith("unknown-")
        for issue in result.issues
    ) <= 3
    assert any(issue.category == "resource" and "第三个成员" in issue.summary for issue in result.issues)


def test_final_enumeration_gap_cannot_confirm_current_bytes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _asset(tmp_path)
    original = file_asset._bounded_member_names
    calls = 0

    def inject_final_third_member(directory_descriptor: int) -> tuple[set[str], bool]:
        nonlocal calls
        calls += 1
        names, complete = original(directory_descriptor)
        if calls == 2:
            return names | {"late-member"}, False
        return names, complete

    monkeypatch.setattr(file_asset, "_bounded_member_names", inject_final_third_member)

    result = _read(tmp_path)

    assert result.check_status == "invalid"
    assert "members-closed" not in result.coverage
    assert result.current_bytes_confirmed is False


def test_object_fingerprint_changes_when_payload_changes(tmp_path: Path) -> None:
    directory = _asset(tmp_path, b"first")
    first = _read(tmp_path)
    payload = b"second"
    (directory / "payload").write_bytes(payload)
    (directory / "file-asset.yaml").write_text(_manifest(payload), encoding="utf-8")

    second = _read(tmp_path)

    assert first.check_status == second.check_status == "mechanically_valid"
    assert first.content_fingerprint is not None
    assert second.content_fingerprint is not None
    assert first.content_fingerprint != second.content_fingerprint
