"""Canonical UTC timestamps used by LDVH runtime observations and writes."""

from __future__ import annotations

import re
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta, timezone
from typing import Any

_RFC3339 = re.compile(
    r"(?P<year>[0-9]{4})-(?P<month>0[1-9]|1[0-2])-(?P<day>0[1-9]|[12][0-9]|3[01])"
    r"T(?P<hour>[01][0-9]|2[0-3]):(?P<minute>[0-5][0-9]):(?P<second>[0-5][0-9])"
    r"(?:\.(?P<fraction>[0-9]+))?"
    r"(?P<offset>Z|(?P<offset_sign>[+-])(?P<offset_hour>[01][0-9]|2[0-3]):"
    r"(?P<offset_minute>[0-5][0-9]))\Z"
)
_TIMESTAMP_KEYS = frozenset(
    {
        "approved_at",
        "at",
        "completed_at",
        "created_at",
        "ended_at",
        "observed_at",
        "reviewed_at",
        "started_at",
        "updated_at",
    }
)


def canonical_utc_timestamp(value: object) -> str | None:
    """Return a strict RFC 3339 timestamp in UTC ``Z`` form when parseable.

    Fractional precision is copied verbatim so converting an explicit legacy
    offset never loses precision. Invalid values stay on the normal schema
    validation path instead of being guessed or repaired here.
    """

    if not isinstance(value, str):
        return None
    match = _RFC3339.fullmatch(value)
    if match is None or match["offset"] == "-00:00":
        return None
    try:
        offset_seconds = 0
        if match["offset"] != "Z":
            offset_seconds = int(match["offset_hour"]) * 3_600 + int(match["offset_minute"]) * 60
            if match["offset_sign"] == "-":
                offset_seconds = -offset_seconds
        source = datetime(
            int(match["year"]),
            int(match["month"]),
            int(match["day"]),
            int(match["hour"]),
            int(match["minute"]),
            int(match["second"]),
            tzinfo=timezone(timedelta(seconds=offset_seconds)),
        )
        utc = source.astimezone(UTC)
    except (OverflowError, ValueError):
        return None
    fraction = match["fraction"]
    rendered = f"{utc.year:04d}-{utc.month:02d}-{utc.day:02d}T{utc.hour:02d}:{utc.minute:02d}:{utc.second:02d}"
    return f"{rendered}{f'.{fraction}' if fraction else ''}Z"


def canonicalize_new_timestamp_fields(value: object, *, before: object | None = None) -> object:
    """Canonicalize only new or changed timestamp fields in a fact write.

    Existing fact values compare against ``before`` and remain byte-for-value
    unchanged. This keeps legacy offset spelling readable without treating an
    ordinary update as a historical migration.
    """

    if isinstance(value, Mapping):
        previous = before if isinstance(before, Mapping) else {}
        result: dict[str, Any] = {}
        for key, current in value.items():
            prior = previous.get(key) if key in previous else None
            if key in _TIMESTAMP_KEYS and current != prior:
                result[key] = canonical_utc_timestamp(current) or current
            else:
                result[key] = canonicalize_new_timestamp_fields(current, before=prior)
        return result
    if isinstance(value, list):
        previous_items = before if isinstance(before, list) else []
        return [
            canonicalize_new_timestamp_fields(
                item,
                before=previous_items[index] if index < len(previous_items) else None,
            )
            for index, item in enumerate(value)
        ]
    return value


def utc_now_iso(*, timespec: str = "microseconds") -> str:
    """Return a canonical RFC 3339 UTC timestamp with a ``Z`` suffix."""

    return datetime.now(UTC).isoformat(timespec=timespec).replace("+00:00", "Z")
