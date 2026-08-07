"""Fail-closed measurement primitives for synthetic trial tests.

This module deliberately does not know how to run a Helper task.  It records
events supplied by a test runner, validates the resulting record, and protects
its temporary output boundary.  A future experiment must build on this record
rather than reconstructing metrics from prose or terminal output.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
import tempfile
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

TRIAL_SCHEMA_VERSION = "ldvh-trial-measurement/1"
_CALL_CATEGORIES = frozenset({"discovery", "target", "repair"})
_OUTCOMES = frozenset({"success", "failure", "timeout"})


class TrialMeasurementError(ValueError):
    """A trial record or output boundary is not trustworthy."""


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _nonempty_string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value:
        raise TrialMeasurementError(f"{field_name} must be a non-empty string")
    return value


def _nonnegative_int(value: object, field_name: str, *, nullable: bool = False) -> int | None:
    if value is None and nullable:
        return None
    if type(value) is not int or value < 0:
        raise TrialMeasurementError(f"{field_name} must be a non-negative integer")
    return value


def _nullable_bool(value: object, field_name: str) -> bool | None:
    if value is None:
        return None
    if type(value) is not bool:
        raise TrialMeasurementError(f"{field_name} must be a boolean or null")
    return value


def validate_trial_record(record: Mapping[str, Any]) -> None:
    """Validate the versioned, closed JSON trial-record schema.

    Records are intentionally complete for every terminal outcome.  Metrics
    that cannot be observed are represented by ``null`` plus a reason; they
    must never be replaced with a convenient zero.
    """

    required = {
        "schema_version",
        "trial_id",
        "task_package_hash",
        "condition",
        "runner_fingerprint",
        "schema_fingerprint",
        "rule_fingerprint",
        "capability_fingerprint",
        "outcome",
        "correct",
        "first_legal",
        "discovery_calls",
        "target_calls",
        "repair_calls",
        "total_calls",
        "extra_calls",
        "invalid_requests",
        "response_bytes",
        "estimated_tokens",
        "duration_seconds",
        "timed_out",
        "failure",
        "unavailable_reason",
    }
    actual = set(record)
    if actual != required:
        missing = sorted(required - actual)
        extra = sorted(actual - required)
        raise TrialMeasurementError(f"record fields must be closed; missing={missing}, extra={extra}")
    if record["schema_version"] != TRIAL_SCHEMA_VERSION:
        raise TrialMeasurementError("unrecognized trial schema version")
    for field_name in (
        "trial_id",
        "task_package_hash",
        "condition",
        "runner_fingerprint",
        "schema_fingerprint",
        "rule_fingerprint",
        "capability_fingerprint",
    ):
        _nonempty_string(record[field_name], field_name)
    if record["outcome"] not in _OUTCOMES:
        raise TrialMeasurementError("outcome must be success, failure, or timeout")
    _nullable_bool(record["correct"], "correct")
    _nullable_bool(record["first_legal"], "first_legal")
    for field_name in (
        "discovery_calls",
        "target_calls",
        "repair_calls",
        "total_calls",
        "extra_calls",
        "invalid_requests",
        "response_bytes",
    ):
        _nonnegative_int(record[field_name], field_name)
    if record["total_calls"] != record["discovery_calls"] + record["target_calls"] + record["repair_calls"]:
        raise TrialMeasurementError("total_calls must equal the classified call count")
    _nonnegative_int(record["estimated_tokens"], "estimated_tokens", nullable=True)
    if record["estimated_tokens"] is None and record["unavailable_reason"] is None:
        raise TrialMeasurementError("unavailable token data requires unavailable_reason")
    if record["estimated_tokens"] is not None and record["unavailable_reason"] is not None:
        raise TrialMeasurementError("unavailable_reason is only allowed when a metric is unavailable")
    if type(record["duration_seconds"]) not in (int, float) or record["duration_seconds"] < 0:
        raise TrialMeasurementError("duration_seconds must be a non-negative number")
    if type(record["timed_out"]) is not bool or record["timed_out"] != (record["outcome"] == "timeout"):
        raise TrialMeasurementError("timed_out must exactly match timeout outcome")
    failure = record["failure"]
    if record["outcome"] == "success":
        if failure is not None:
            raise TrialMeasurementError("successful records cannot contain failure")
    elif not isinstance(failure, str) or not failure:
        raise TrialMeasurementError("failed and timeout records require failure")


def parse_trial_record(raw: str | bytes) -> dict[str, Any]:
    """Parse an externally supplied record and fail closed on malformed JSON."""

    try:
        parsed = json.loads(raw)
    except (TypeError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise TrialMeasurementError("trial record is not valid JSON") from error
    if not isinstance(parsed, dict):
        raise TrialMeasurementError("trial record must be a JSON object")
    validate_trial_record(parsed)
    return parsed


@dataclass(frozen=True, slots=True)
class HelperResponseEvent:
    """One raw Helper response observed by a synthetic runner."""

    category: str
    raw_response: str | bytes
    legal: bool

    def byte_count(self) -> int:
        if self.category not in _CALL_CATEGORIES:
            raise TrialMeasurementError("response category is not recognized")
        if type(self.legal) is not bool:
            raise TrialMeasurementError("legal must be a boolean")
        if isinstance(self.raw_response, bytes):
            return len(self.raw_response)
        if isinstance(self.raw_response, str):
            return len(self.raw_response.encode("utf-8"))
        raise TrialMeasurementError("raw_response must be bytes or text")


@dataclass(slots=True)
class TrialMeasurementCollector:
    """Collect metrics from raw events without performing Helper calls."""

    trial_id: str
    task_package_hash: str
    condition: str
    runner_fingerprint: str
    rule_fingerprint: str
    capability_fingerprint: str
    expected_calls: int = 1
    _started_monotonic: float = field(default_factory=time.monotonic)
    _calls: dict[str, int] = field(default_factory=lambda: {category: 0 for category in _CALL_CATEGORIES})
    _invalid_requests: int = 0
    _response_bytes: int = 0
    _first_legal: bool | None = None

    def observe(self, event: HelperResponseEvent) -> None:
        """Capture a raw response regardless of whether the call was legal."""

        byte_count = event.byte_count()
        total_before = sum(self._calls.values())
        self._calls[event.category] += 1
        self._response_bytes += byte_count
        if total_before == 0:
            self._first_legal = event.legal
        if not event.legal:
            self._invalid_requests += 1

    def finalize(
        self,
        *,
        outcome: str,
        correct: bool | None,
        failure: str | None = None,
        estimated_tokens: int | None = None,
        unavailable_reason: str | None = None,
    ) -> dict[str, Any]:
        if outcome not in _OUTCOMES:
            raise TrialMeasurementError("outcome must be success, failure, or timeout")
        _nonnegative_int(self.expected_calls, "expected_calls")
        total_calls = sum(self._calls.values())
        record: dict[str, Any] = {
            "schema_version": TRIAL_SCHEMA_VERSION,
            "trial_id": self.trial_id,
            "task_package_hash": self.task_package_hash,
            "condition": self.condition,
            "runner_fingerprint": self.runner_fingerprint,
            "schema_fingerprint": _sha256_text(TRIAL_SCHEMA_VERSION),
            "rule_fingerprint": self.rule_fingerprint,
            "capability_fingerprint": self.capability_fingerprint,
            "outcome": outcome,
            "correct": correct,
            "first_legal": self._first_legal,
            "discovery_calls": self._calls["discovery"],
            "target_calls": self._calls["target"],
            "repair_calls": self._calls["repair"],
            "total_calls": total_calls,
            "extra_calls": max(total_calls - self.expected_calls, 0),
            "invalid_requests": self._invalid_requests,
            "response_bytes": self._response_bytes,
            "estimated_tokens": estimated_tokens,
            "duration_seconds": time.monotonic() - self._started_monotonic,
            "timed_out": outcome == "timeout",
            "failure": failure,
            "unavailable_reason": unavailable_reason,
        }
        validate_trial_record(record)
        return record


@dataclass(frozen=True, slots=True)
class ContractClaim:
    """An exact prompt-card statement tied to a currently read contract source."""

    statement: str
    source_ref: str
    source_fingerprint: str


def build_prompt_card(
    claims: Sequence[ContractClaim],
    *,
    read_current_source: Callable[[str], str],
) -> dict[str, Any]:
    """Read current sources to build a card, rejecting unverified assertions.

    Claims are exact excerpts rather than model-authored paraphrases.  This is
    intentionally conservative: a caller must obtain current capability or
    specification content through its approved reader and cannot attach a
    stale, unrelated, or invented statement to a valid-looking fingerprint.
    """

    if not claims:
        raise TrialMeasurementError("a prompt card requires at least one verified claim")
    rendered: list[dict[str, str]] = []
    seen: set[str] = set()
    for claim in claims:
        _nonempty_string(claim.statement, "claim.statement")
        _nonempty_string(claim.source_ref, "claim.source_ref")
        source_text = read_current_source(claim.source_ref)
        _nonempty_string(source_text, "current source text")
        if claim.source_fingerprint != _sha256_text(source_text):
            raise TrialMeasurementError("claim source fingerprint does not match current source text")
        if claim.statement not in source_text:
            raise TrialMeasurementError("claim statement is not supported by current source text")
        if claim.statement in seen:
            raise TrialMeasurementError("prompt card claims must be unique")
        seen.add(claim.statement)
        rendered.append(
            {
                "statement": claim.statement,
                "source_ref": claim.source_ref,
                "source_fingerprint": claim.source_fingerprint,
            }
        )
    card_payload = json.dumps(rendered, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return {"claims": rendered, "card_fingerprint": _sha256_text(card_payload)}


def _contained(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


@dataclass(slots=True)
class SafeTrialTempRoot:
    """A temporary-root writer that rejects every path escape before writing."""

    root: Path
    _identity: tuple[int, int]
    _resolved_root: Path
    _created_directories: set[Path]

    @classmethod
    def create(cls, *, prefix: str = "ldvh-trial-", repository_root: Path) -> SafeTrialTempRoot:
        root = Path(tempfile.mkdtemp(prefix=prefix))
        resolved = root.resolve(strict=True)
        if _contained(resolved, repository_root.resolve(strict=True)):
            raise TrialMeasurementError("mkdtemp root may not be inside the repository")
        info = root.lstat()
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
            raise TrialMeasurementError("mkdtemp did not create a safe directory")
        return cls(
            root=root,
            _identity=(info.st_dev, info.st_ino),
            _resolved_root=resolved,
            _created_directories={root},
        )

    def _verify_root(self) -> None:
        info = self.root.lstat()
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode) or (info.st_dev, info.st_ino) != self._identity:
            raise TrialMeasurementError("temporary root identity changed")
        if self.root.resolve(strict=True) != self._resolved_root:
            raise TrialMeasurementError("temporary root realpath drifted")

    def _output_path(self, relative_path: str) -> Path:
        candidate = Path(relative_path)
        if not relative_path or candidate.is_absolute() or any(part in {"", ".", ".."} for part in candidate.parts):
            raise TrialMeasurementError("output path must be a non-empty, traversal-free relative path")
        return self.root.joinpath(*candidate.parts)

    def write_json(self, relative_path: str, value: Mapping[str, Any]) -> Path:
        """Create exactly one new JSON file beneath the identity-bound root."""

        self._verify_root()
        output = self._output_path(relative_path)
        parent = self.root
        for part in output.relative_to(self.root).parts[:-1]:
            parent = parent / part
            if parent.exists():
                info = parent.lstat()
                if (
                    stat.S_ISLNK(info.st_mode)
                    or not stat.S_ISDIR(info.st_mode)
                    or parent not in self._created_directories
                ):
                    raise TrialMeasurementError("output parent was not created by this runner")
            else:
                parent.mkdir()
                self._created_directories.add(parent)
            if not _contained(parent.resolve(strict=True), self._resolved_root):
                raise TrialMeasurementError("output parent escaped temporary root")
        if output.exists() or output.is_symlink():
            raise TrialMeasurementError("output path must be newly created")
        if not _contained(output.parent.resolve(strict=True), self._resolved_root):
            raise TrialMeasurementError("output realpath escaped temporary root")
        payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n"
        try:
            descriptor = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError as error:
            if output.is_symlink():
                output.unlink()
            raise TrialMeasurementError("output path changed before exclusive creation") from error
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
        except BaseException:
            try:
                output.unlink()
            except FileNotFoundError:
                pass
            raise
        self._verify_root()
        if output.is_symlink() or not _contained(output.resolve(strict=True), self._resolved_root):
            raise TrialMeasurementError("output path changed after write")
        return output


def synthetic_trial(
    factory: Callable[[], TrialMeasurementCollector],
    events: Sequence[HelperResponseEvent],
    **terminal: Any,
) -> dict[str, Any]:
    """Small helper for synthetic tests; it never invokes a real Helper."""

    collector = factory()
    for event in events:
        collector.observe(event)
    return collector.finalize(**terminal)
