"""Read-only execution-carrier comparability audit for DSH session logs.

This module turns a DeepSeek Harness persistent session log (a Zstandard
compressed or plain JSONL stream of ``SessionEvent`` objects) into a
structural execution-carrier fingerprint and a three-value comparability
verdict (``comparable`` / ``not_comparable`` / ``inconclusive``) with machine
reasons.  It deliberately reads only structured fields: event type, sequence,
timestamp, ``request/header`` provider/model/reason, tool name, and pairing
counts.  It never reads message bodies, tool-result content, or assistant
output, matching the privacy stop-boundary of the governing Spark/Study.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from collections import Counter
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ZSTD_MAGIC = b"\x28\xb5\x2f\xfd"
ZSTD_SUFFIX = ".zstd"
REQUEST_HEADER = "request/header"
TOOL_CALL = "tool/call"
TOOL_RESULT = "tool/result"
TURN_START = "turn/start"
TURN_END = "turn/end"
STEP_START = "step/start"
STEP_END = "step/end"
# Structured-only event markers whose mere presence is a comparability flag.
FLAG_EVENT_TYPES = frozenset(
    {
        "approval/asked",
        "approval/decided",
        "approval/policy",
        "permission/preset",
        "sandbox/mode",
        "compaction/start",
        "compaction/end",
        "compaction/summary",
        "compaction/prune",
        "llm/retry",
        "llm/retry-started",
        "hook/invoked",
        "hook/result",
        "session/end-seed",
        "plan/mode",
        "feedback/record",
        "subagent/descriptor",
        "todo/write",
        "tool-workflow/run-start",
        "tool-workflow/run-end",
    }
)
# Event types whose payloads are never inspected (content-privacy boundary).
_OPAQUE_EVENT_TYPES = frozenset(
    {
        "user/message",
        "assistant/message",
        "assistant/chunk",
        "text-chunks",
        "reasoning-chunks",
        "tool-call-chunks",
        "agent/inbox/spliced",
        "session/title",
        "session/title-llm-request",
        "request/context",
        "session",
        "agent-preset/selected",
    }
)


class SessionLogError(ValueError):
    """A session log could not be read as a structural event stream."""


@dataclass(frozen=True, slots=True)
class RequestHeaderFingerprint:
    """One machine-observable model/tool entry point of a session."""

    provider: str
    model: str
    reason: str
    seq: int

    @property
    def entry(self) -> tuple[str, str]:
        return (self.provider, self.model)


@dataclass(frozen=True, slots=True)
class SessionFingerprint:
    """Structural execution-carrier fingerprint of one session log.

    Content-bearing fields (message text, tool arguments/results, assistant
    output) are intentionally absent; only structured fields are retained.
    """

    headers: tuple[RequestHeaderFingerprint, ...] = ()
    tool_names: tuple[str, ...] = ()
    turn_start: int = 0
    turn_end: int = 0
    step_start: int = 0
    step_end: int = 0
    tool_call: int = 0
    tool_result: int = 0
    flags: tuple[tuple[str, int], ...] = ()

    @property
    def distinct_entries(self) -> tuple[tuple[str, str], ...]:
        return tuple(dict.fromkeys(header.entry for header in self.headers))

    @property
    def pairing_ok(self) -> bool:
        return (
            self.turn_start == self.turn_end
            and self.step_start == self.step_end
            and self.tool_call == self.tool_result
        )


@dataclass(frozen=True, slots=True)
class ComparabilityVerdict:
    """Three-value comparability judgement plus machine reasons."""

    verdict: str
    reasons: tuple[str, ...] = ()


def _nonempty_string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value:
        raise SessionLogError(f"{field_name} must be a non-empty string")
    return value


def _parse_event_line(line: str) -> Mapping[str, Any]:
    try:
        parsed = json.loads(line)
    except (TypeError, json.JSONDecodeError) as error:
        raise SessionLogError("session log line is not valid JSON") from error
    if not isinstance(parsed, Mapping):
        raise SessionLogError("session log line must be a JSON object")
    return parsed


def _iter_events_from_lines(lines: Iterable[str]) -> Iterator[Mapping[str, Any]]:
    for line in lines:
        if not line.strip():
            continue
        yield _parse_event_line(line)


def _is_zstd_stream(raw: bytes) -> bool:
    return raw.startswith(ZSTD_MAGIC)


def _decode_zstd_bytes(raw: bytes) -> bytes:
    """Decode a Zstandard stream via zstandard module or the zstd CLI."""
    try:
        import zstandard  # type: ignore[import-not-found]  # optional runtime dep

        return zstandard.ZstdDecompressor().decompress(raw, max_output_size=2**30)
    except ImportError:
        pass
    except Exception as error:  # pragma: no cover - defensive for corrupted frames
        raise SessionLogError(f"zstandard decode failed: {error}") from error
    executable = shutil.which("zstd")
    if executable is None:
        raise SessionLogError(
            "zstd decoding requires the 'zstandard' Python module or the 'zstd' CLI on PATH"
        )
    try:
        completed = subprocess.run(
            [executable, "-d", "--stdout"],
            input=raw,
            capture_output=True,
            check=False,
        )
    except OSError as error:
        raise SessionLogError(f"zstd CLI invocation failed: {error}") from error
    if completed.returncode != 0:
        raise SessionLogError(
            f"zstd CLI decode failed (rc={completed.returncode}): {completed.stderr.decode(errors='replace')[:200]}"
        )
    return completed.stdout


def _lines_from_bytes(raw: bytes) -> list[str]:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise SessionLogError("session log is not UTF-8 text") from error
    return text.splitlines()


def iter_events(source: object) -> Iterator[Mapping[str, Any]]:
    """Yield parsed session events from a path, raw bytes, or text lines.

    ``source`` may be a ``str``/``Path`` (a ``.zstd`` or plain JSONL file), a
    ``bytes`` payload (auto-detected Zstandard magic), or an iterable of text
    lines.  Events are parsed structurally; content fields are never read.
    """
    if isinstance(source, (str, Path)):
        path = Path(source)
        try:
            raw = path.read_bytes()
        except OSError as error:
            raise SessionLogError(f"session log is not readable: {path}") from error
        if _is_zstd_stream(raw) or path.name.endswith(ZSTD_SUFFIX):
            payload = _decode_zstd_bytes(raw)
        else:
            payload = raw
        return _iter_events_from_lines(_lines_from_bytes(payload))
    if isinstance(source, bytes):
        if _is_zstd_stream(source):
            return _iter_events_from_lines(_lines_from_bytes(_decode_zstd_bytes(source)))
        return _iter_events_from_lines(_lines_from_bytes(source))
    if isinstance(source, Iterable):
        return _iter_events_from_lines(source)
    raise SessionLogError("session log source must be a path, bytes, or iterable of lines")


def audit_events(events: Iterable[Mapping[str, Any]]) -> SessionFingerprint:
    """Extract the structural fingerprint from parsed session events."""
    headers: list[RequestHeaderFingerprint] = []
    tool_names: Counter[str] = Counter()
    turn_start = turn_end = step_start = step_end = tool_call = tool_result = 0
    flags: Counter[str] = Counter()

    for event in events:
        if not isinstance(event, Mapping):
            raise SessionLogError("session event must be a JSON object")
        event_type = event.get("type")
        if not isinstance(event_type, str) or not event_type:
            raise SessionLogError("session event requires a non-empty type")
        if event_type in _OPAQUE_EVENT_TYPES:
            # Content-privacy boundary: never inspect payloads of these types.
            continue
        if event_type == REQUEST_HEADER:
            data = event.get("data")
            if not isinstance(data, Mapping):
                raise SessionLogError("request/header requires a data object")
            header = data.get("header")
            if not isinstance(header, Mapping):
                raise SessionLogError("request/header requires a header object")
            config = header.get("config")
            if not isinstance(config, Mapping):
                raise SessionLogError("request/header requires a config object")
            provider = config.get("provider")
            model = config.get("model")
            if not isinstance(provider, str) or not provider:
                raise SessionLogError("request/header provider must be a non-empty string")
            if not isinstance(model, str) or not model:
                raise SessionLogError("request/header model must be a non-empty string")
            reason = data.get("reason")
            if reason is None:
                reason = "unknown"
            if not isinstance(reason, str) or not reason:
                raise SessionLogError("request/header reason must be a non-empty string")
            seq = event.get("seq", 0)
            if type(seq) is not int:
                raise SessionLogError("request/header seq must be an integer")
            headers.append(RequestHeaderFingerprint(provider=provider, model=model, reason=reason, seq=seq))
            continue
        if event_type == TOOL_CALL:
            data = event.get("data")
            if not isinstance(data, Mapping):
                raise SessionLogError("tool/call requires a data object")
            name = data.get("name")
            if not isinstance(name, str) or not name:
                raise SessionLogError("tool/call name must be a non-empty string")
            tool_names[name] += 1
            tool_call += 1
            continue
        if event_type == TOOL_RESULT:
            tool_result += 1
            continue
        if event_type == TURN_START:
            turn_start += 1
            continue
        if event_type == TURN_END:
            turn_end += 1
            continue
        if event_type == STEP_START:
            step_start += 1
            continue
        if event_type == STEP_END:
            step_end += 1
            continue
        if event_type in FLAG_EVENT_TYPES:
            flags[event_type] += 1
            continue
        # Unknown structured event types are recorded by name only (count 1).
        flags[f"event/{event_type}"] += 1

    return SessionFingerprint(
        headers=tuple(headers),
        tool_names=tuple(sorted(tool_names)),
        turn_start=turn_start,
        turn_end=turn_end,
        step_start=step_start,
        step_end=step_end,
        tool_call=tool_call,
        tool_result=tool_result,
        flags=tuple(sorted(flags.items())),
    )


def judge_comparability(fingerprint: SessionFingerprint) -> ComparabilityVerdict:
    """Return the three-value comparability judgement with machine reasons.

    Rules (matching the observation-surface Study):
    - no request/header entries -> ``inconclusive``;
    - more than one distinct provider/model entry -> ``not_comparable``;
    - any turn/step/tool pairing mismatch -> ``not_comparable``;
    - otherwise -> ``comparable``.
    """
    reasons: list[str] = []
    if not fingerprint.headers:
        reasons.append("no request/header (session not run)")
        return ComparabilityVerdict(verdict="inconclusive", reasons=tuple(reasons))
    entries = fingerprint.distinct_entries
    if len(entries) > 1:
        reasons.append(f"multi-model entry {len(entries)}")
    if fingerprint.turn_start != fingerprint.turn_end:
        reasons.append(f"turn unpaired {fingerprint.turn_start}/{fingerprint.turn_end}")
    if fingerprint.step_start != fingerprint.step_end:
        reasons.append(f"step unpaired {fingerprint.step_start}/{fingerprint.step_end}")
    if fingerprint.tool_call != fingerprint.tool_result:
        reasons.append(f"tool unpaired {fingerprint.tool_call}/{fingerprint.tool_result}")
    if reasons:
        return ComparabilityVerdict(verdict="not_comparable", reasons=tuple(reasons))
    return ComparabilityVerdict(verdict="comparable")


def audit_session(source: object) -> tuple[SessionFingerprint, ComparabilityVerdict]:
    """Audit one session log end to end (structural only)."""
    fingerprint = audit_events(iter_events(source))
    return fingerprint, judge_comparability(fingerprint)
