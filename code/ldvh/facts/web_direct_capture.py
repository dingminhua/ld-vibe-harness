"""Unmounted Web-only application service for one V4 Spark direct capture."""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import re
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal

from ldvh.facts.candidate_discovery import (
    MAX_WEB_FACT_AGGREGATE_BYTES,
    FactTypeRawSnapshot,
    discover_fact_type_raw,
)
from ldvh.facts.contracts import LAYOUTS
from ldvh.facts.creation import CreationBoundary, allocation_lock, candidate_object_id, serialize_fact_object
from ldvh.facts.creation_application import (
    FactCreationCommand,
    FactCreationResult,
    PreparedFactCreation,
    commit_fact_creation_attempt_locked,
    prepare_fact_creation,
    preview_fact_creation_locked,
)
from ldvh.facts.repository import MAX_FACT_BYTES
from ldvh.facts.schema import FactSchema
from ldvh.facts.validation import parse_rfc3339
from ldvh.filesystem import durable_writes_enabled

UNICODE_NFC_CONTRACT_VERSION = "15.1.0"
SUPPORTED_UNIDATA_VERSIONS = frozenset({"15.0.0", "15.1.0"})
# Unicode 15.0 and 15.1 NormalizationTest.txt have byte-identical test bodies.
# The only 15.1 additions below are CCC=0, have no canonical decomposition,
# and are not composition targets, so a 15.0 NFC engine is equivalent for 15.1.
UNICODE_15_1_NFC_INERT_RANGES = ((0x2FFC, 0x2FFF), (0x31EF, 0x31EF), (0x2EBF0, 0x2EE5D))
UNICODE_15_0_NORMALIZATION_TEST_URL = "https://www.unicode.org/Public/15.0.0/ucd/NormalizationTest.txt"
UNICODE_15_1_NORMALIZATION_TEST_URL = "https://www.unicode.org/Public/15.1.0/ucd/NormalizationTest.txt"

_WHITE_SPACE = "".join(
    chr(codepoint)
    for start, end in (
        (0x0009, 0x000D),
        (0x0020, 0x0020),
        (0x0085, 0x0085),
        (0x00A0, 0x00A0),
        (0x1680, 0x1680),
        (0x2000, 0x200A),
        (0x2028, 0x2029),
        (0x202F, 0x202F),
        (0x205F, 0x205F),
        (0x3000, 0x3000),
    )
    for codepoint in range(start, end + 1)
)
_PRIORITIES = frozenset({"P0", "P1", "P2", "P3"})
_DATA_PREFIX = "data:application/json;base64,"
_VERSION_PATTERN = re.compile(r"sha256:([0-9a-f]{64})\Z")
_REQUEST_FIELDS = frozenset({"title", "description", "priority"})
_SOURCE_FIELDS = frozenset({"kind", "locator", "version", "observed_at"})

DirectCaptureStatus = Literal[
    "created",
    "exact_duplicate",
    "invalid",
    "unavailable",
    "integrity_conflict",
    "readback_failed",
    "rollback_residue",
]


@dataclass(frozen=True, slots=True)
class WebCaptureIdentity:
    title: str
    summary: str
    priority: str
    canonical_bytes: bytes
    digest: str
    locator: str


@dataclass(frozen=True, slots=True)
class WebDirectCaptureResult:
    status: DirectCaptureStatus
    code: str
    summary: str
    actual_ref: Mapping[str, str] | None = None
    existing_ref: Mapping[str, str] | None = None
    canonical_path: str | None = None
    fact_object: Mapping[str, Any] | None = None
    details: tuple[str, ...] = ()


def _normalized_text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string")
    if any(0xD800 <= ord(character) <= 0xDFFF for character in value):
        raise ValueError(f"{field} contains an unpaired surrogate")
    normalized = unicodedata.normalize("NFC", value).strip(_WHITE_SPACE)
    if not normalized:
        raise ValueError(f"{field} must not be empty")
    return normalized


def _identity(title: object, summary: object, priority: object) -> WebCaptureIdentity:
    normalized_title = _normalized_text(title, "title")
    normalized_summary = _normalized_text(summary, "summary")
    if not isinstance(priority, str) or priority not in _PRIORITIES:
        raise ValueError("priority must be exactly P0, P1, P2, or P3")
    payload = {
        "priority": priority,
        "summary": normalized_summary,
        "title": normalized_title,
    }
    canonical = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    digest = hashlib.sha256(canonical).hexdigest()
    locator = _DATA_PREFIX + base64.b64encode(canonical).decode("ascii")
    return WebCaptureIdentity(normalized_title, normalized_summary, priority, canonical, digest, locator)


def canonicalize_web_capture(request: Mapping[str, object]) -> WebCaptureIdentity:
    """Validate the closed request and form its Unicode-15.1 canonical identity."""

    if set(request) != _REQUEST_FIELDS:
        raise ValueError("request fields must be exactly title, description, and priority")
    return _identity(request["title"], request["description"], request["priority"])


def _pairs_no_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def validate_web_direct_source_ref(reference: object) -> WebCaptureIdentity:
    """Recover and validate one self-contained historical capture identity."""

    if not isinstance(reference, Mapping) or set(reference) != _SOURCE_FIELDS:
        raise ValueError("web-direct-capture source fields are not closed")
    if reference.get("kind") != "web-direct-capture":
        raise ValueError("source kind is not web-direct-capture")
    locator = reference.get("locator")
    version = reference.get("version")
    observed_at = reference.get("observed_at")
    if not isinstance(locator, str) or not locator.startswith(_DATA_PREFIX):
        raise ValueError("source locator is not the required data URI")
    encoded = locator.removeprefix(_DATA_PREFIX)
    try:
        decoded = base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error) as error:
        raise ValueError("source locator Base64 is invalid") from error
    if base64.b64encode(decoded).decode("ascii") != encoded:
        raise ValueError("source locator Base64 is not canonical")
    try:
        payload = json.loads(decoded.decode("utf-8"), object_pairs_hook=_pairs_no_duplicates)
    except (UnicodeError, json.JSONDecodeError, ValueError) as error:
        raise ValueError("source locator JSON is invalid") from error
    if not isinstance(payload, dict) or set(payload) != {"priority", "summary", "title"}:
        raise ValueError("source locator JSON fields are not closed")
    recovered = _identity(payload["title"], payload["summary"], payload["priority"])
    if recovered.canonical_bytes != decoded or recovered.locator != locator:
        raise ValueError("source locator bytes are not canonical")
    match = _VERSION_PATTERN.fullmatch(version) if isinstance(version, str) else None
    if match is None or match.group(1) != recovered.digest:
        raise ValueError("source version digest does not match locator")
    if parse_rfc3339(observed_at) is None:
        raise ValueError("source observed_at is not timezone-aware RFC3339")
    return recovered


def _source_reference(identity: WebCaptureIdentity, observed_at: str) -> dict[str, str]:
    return {
        "kind": "web-direct-capture",
        "locator": identity.locator,
        "version": f"sha256:{identity.digest}",
        "observed_at": observed_at,
    }


def _conservative_envelope(
    identity: WebCaptureIdentity,
    source: dict[str, str],
    observed_at: str,
    candidate_id: str,
) -> int:
    digits = max(1018, len(candidate_id.removeprefix("spark-")) + 1)
    fields: dict[str, object] = {
        "object_id": "spark-" + ("9" * digits),
        "fact_type_key": "spark",
        "title": identity.title,
        "created_at": observed_at,
        "updated_at": observed_at,
        "status": "open",
        "source_refs": [source],
        "summary": identity.summary,
        "priority": identity.priority,
    }
    return len(serialize_fact_object(LAYOUTS["spark"], fields, None).encode("utf-8"))


def _snapshot_identities(
    snapshot: FactTypeRawSnapshot,
    requested_digest: str,
) -> WebDirectCaptureResult | tuple[tuple[str, str], ...]:
    if snapshot.structural_problems:
        structural = tuple(
            str(problem.get("canonical_path", "ldvh-base/sparks")) for problem in snapshot.structural_problems
        )
        if all("identity" in str(problem) or "文件名" in str(problem) for problem in snapshot.structural_problems):
            return WebDirectCaptureResult(
                "integrity_conflict",
                "spark_integrity_conflict",
                "Spark 目录包含非 canonical 对象",
                details=structural,
            )
        return WebDirectCaptureResult(
            "unavailable",
            "spark_coverage_unavailable",
            "Spark 全状态扫描未形成完整 coverage",
            details=structural,
        )
    if not snapshot.coverage_complete:
        return WebDirectCaptureResult(
            "unavailable",
            "spark_coverage_unavailable",
            "Spark 全状态扫描未形成完整 coverage",
        )
    matches: list[tuple[str, str]] = []
    for object_id, read in snapshot.objects:
        if read.check_status == "invalid":
            return WebDirectCaptureResult(
                "integrity_conflict",
                "spark_integrity_conflict",
                "Spark 对象机械完整性损坏",
                details=(read.canonical_path,),
            )
        if read.check_status != "mechanically_valid" or read.fields is None:
            return WebDirectCaptureResult(
                "unavailable",
                "spark_coverage_unavailable",
                "Spark 对象无法完成全状态读取",
                details=(read.canonical_path,),
            )
        identities: set[str] = set()
        source_refs = read.fields.get("source_refs")
        if not isinstance(source_refs, list):
            return WebDirectCaptureResult(
                "integrity_conflict",
                "spark_integrity_conflict",
                "Spark source_refs 损坏",
                details=(read.canonical_path,),
            )
        for reference in source_refs:
            if isinstance(reference, Mapping) and reference.get("kind") == "web-direct-capture":
                try:
                    identities.add(validate_web_direct_source_ref(reference).digest)
                except ValueError as error:
                    return WebDirectCaptureResult(
                        "integrity_conflict",
                        "web_capture_source_invalid",
                        "历史 Web direct capture 来源损坏",
                        details=(read.canonical_path, str(error)),
                    )
        status = read.fields.get("status")
        if status == "open":
            try:
                current = _identity(
                    read.fields.get("title"),
                    read.fields.get("summary"),
                    read.fields.get("priority"),
                )
            except ValueError as error:
                return WebDirectCaptureResult(
                    "integrity_conflict",
                    "spark_current_identity_invalid",
                    "open Spark 当前 identity 无法复算",
                    details=(read.canonical_path, str(error)),
                )
            identities.add(current.digest)
        if requested_digest in identities:
            matches.append((object_id, str(status)))
    return tuple(matches)


def _creation_failure(result: FactCreationResult) -> WebDirectCaptureResult:
    if result.status in {"attempt_rejected", "candidate_rejected"}:
        return WebDirectCaptureResult(
            "invalid",
            "fact_validation_failed",
            "Spark 内容未通过机械检查",
            details=tuple(issue.summary for issue in result.issues),
        )
    if result.status == "readback_failed":
        rollback = result.rollback_result
        rolled_back = rollback is not None and rollback.outcome == "removed" and rollback.namespace_state == "committed"
        return WebDirectCaptureResult(
            "readback_failed" if rolled_back else "rollback_residue",
            "spark_readback_failed" if rolled_back else "spark_rollback_residue",
            "Spark 写后回读失败，已回滚" if rolled_back else "Spark 写后回读失败且存在残留",
            canonical_path=(
                LAYOUTS["spark"].canonical_path(result.actual_id) if result.actual_id is not None else None
            ),
            details=tuple(issue.summary for issue in result.issues),
        )
    canonical_path = None
    if result.actual_id is not None and result.creation_result is not None:
        if result.creation_result.namespace_state == "uncertain" or result.creation_result.cleanup == "residue":
            canonical_path = LAYOUTS["spark"].canonical_path(result.actual_id)
    return WebDirectCaptureResult(
        "unavailable",
        "spark_creation_unavailable",
        "Spark 创建事务当前不可用",
        canonical_path=canonical_path,
        details=((result.allocation_status or result.status),),
    )


def create_web_spark_direct_capture(
    boundary: CreationBoundary,
    schemas: Mapping[str, FactSchema],
    request: Mapping[str, object],
) -> WebDirectCaptureResult:
    """Create one open V4 Spark; this service is intentionally not mounted to Web yet."""

    if unicodedata.unidata_version not in SUPPORTED_UNIDATA_VERSIONS:
        return WebDirectCaptureResult(
            "unavailable",
            "unicode_nfc_unavailable",
            f"Unicode {UNICODE_NFC_CONTRACT_VERSION} NFC 执行器不可用",
            details=(unicodedata.unidata_version,),
        )
    try:
        identity = canonicalize_web_capture(request)
    except (KeyError, ValueError) as error:
        return WebDirectCaptureResult("invalid", "invalid_capture", "Spark capture 请求无效", details=(str(error),))
    schema_snapshot = dict(schemas)
    schema = schema_snapshot.get("spark")
    if schema is None:
        return WebDirectCaptureResult("unavailable", "spark_schema_unavailable", "Spark Schema 当前不可用")
    if not durable_writes_enabled():
        return WebDirectCaptureResult(
            "unavailable",
            "durable_write_unavailable",
            "当前平台未获准写入事实对象",
        )
    observed_at = datetime.now().astimezone().isoformat()
    source = _source_reference(identity, observed_at)
    candidate = candidate_object_id(boundary, LAYOUTS["spark"])
    if candidate is None:
        return WebDirectCaptureResult("unavailable", "allocator_unavailable", "Spark allocator 当前不可用")
    if _conservative_envelope(identity, source, observed_at, candidate) > MAX_FACT_BYTES:
        return WebDirectCaptureResult(
            "invalid",
            "capture_too_large",
            "Spark capture 超过 4 MiB 事实读取预算",
        )
    prepared = prepare_fact_creation(
        FactCreationCommand(
            boundary,
            "spark",
            schema_snapshot,
            schema,
            candidate,
            {
                "title": identity.title,
                "status": "open",
                "source_refs": [source],
                "summary": identity.summary,
                "priority": identity.priority,
            },
            None,
        ),
        observed_at=observed_at,
    )
    if isinstance(prepared, FactCreationResult):
        return _creation_failure(prepared)
    assert isinstance(prepared, PreparedFactCreation)

    with allocation_lock(boundary, LAYOUTS["spark"]) as counter_path:
        for _ in range(16):
            snapshot = discover_fact_type_raw(
                boundary.worktree_root,
                boundary.governed_project_id,
                boundary.git_common_dir,
                schema_snapshot,
                "spark",
                aggregate_budget_bytes=MAX_WEB_FACT_AGGREGATE_BYTES,
            )
            matches = _snapshot_identities(snapshot, identity.digest)
            if isinstance(matches, WebDirectCaptureResult):
                return matches
            if len(matches) == 1:
                object_id, status = matches[0]
                return WebDirectCaptureResult(
                    "exact_duplicate",
                    "exact_duplicate",
                    "已存在相同 Web capture identity 的 Spark",
                    existing_ref={
                        "governed_project_id": boundary.governed_project_id,
                        "fact_type_key": "spark",
                        "object_id": object_id,
                        "status": status,
                    },
                )
            if len(matches) > 1:
                return WebDirectCaptureResult(
                    "integrity_conflict",
                    "multiple_exact_duplicates",
                    "多个 Spark 对象命中相同 capture identity",
                    details=tuple(object_id for object_id, _ in matches),
                )
            attempt = preview_fact_creation_locked(prepared, counter_path)
            if isinstance(attempt, FactCreationResult):
                return _creation_failure(attempt)
            if len(attempt.payload) > MAX_FACT_BYTES:
                return WebDirectCaptureResult(
                    "invalid",
                    "capture_too_large",
                    "Spark 最终 YAML 超过 4 MiB 事实读取预算",
                )
            result = commit_fact_creation_attempt_locked(attempt)
            if result.status in {"allocation_stale", "creation_conflict"}:
                continue
            if result.status != "created" or result.actual_id is None or result.read is None:
                return _creation_failure(result)
            fields = result.read.fields
            if fields is None:
                return _creation_failure(result)
            return WebDirectCaptureResult(
                "created",
                "spark_created",
                "V4 Spark 已原子创建并精确回读",
                actual_ref={
                    "governed_project_id": boundary.governed_project_id,
                    "fact_type_key": "spark",
                    "object_id": result.actual_id,
                },
                canonical_path=LAYOUTS["spark"].canonical_path(result.actual_id),
                fact_object=fields,
            )
    return WebDirectCaptureResult(
        "unavailable",
        "spark_creation_retry_exhausted",
        "Spark 创建在受控重试范围内未完成",
    )


__all__ = [
    "SUPPORTED_UNIDATA_VERSIONS",
    "UNICODE_15_0_NORMALIZATION_TEST_URL",
    "UNICODE_15_1_NFC_INERT_RANGES",
    "UNICODE_15_1_NORMALIZATION_TEST_URL",
    "UNICODE_NFC_CONTRACT_VERSION",
    "WebCaptureIdentity",
    "WebDirectCaptureResult",
    "canonicalize_web_capture",
    "create_web_spark_direct_capture",
    "validate_web_direct_source_ref",
]
