"""Authoritative UUIDv7 identities and derived six-letter references."""

from __future__ import annotations

import hashlib
import secrets
import time
import uuid

TYPE_CODES = {
    "adr": "A",
    "workcase": "C",
    "pitfall": "P",
    "spark": "S",
    "study": "T",
}

_MAX_TIMESTAMP_MS = 1 << 48
_MAX_RANDOM_BITS = 1 << 74
_SHORT_MODULUS = 26**5


def canonical_object_uid(value: object) -> str | None:
    """Return a canonical lowercase UUIDv7 string, or ``None``."""

    if not isinstance(value, str):
        return None
    try:
        parsed = uuid.UUID(value)
    except (ValueError, AttributeError):
        return None
    if str(parsed) != value or parsed.version != 7 or parsed.variant != uuid.RFC_4122:
        return None
    return value


def generate_object_uid(*, timestamp_ms: int | None = None, random_bits: int | None = None) -> str:
    """Generate a canonical UUIDv7 using a 48-bit millisecond time and 74 random bits."""

    timestamp = time.time_ns() // 1_000_000 if timestamp_ms is None else timestamp_ms
    randomness = secrets.randbits(74) if random_bits is None else random_bits
    if isinstance(timestamp, bool) or not isinstance(timestamp, int) or not 0 <= timestamp < _MAX_TIMESTAMP_MS:
        raise ValueError("timestamp_ms must fit in 48 bits")
    if isinstance(randomness, bool) or not isinstance(randomness, int) or not 0 <= randomness < _MAX_RANDOM_BITS:
        raise ValueError("random_bits must fit in 74 bits")

    rand_a = randomness >> 62
    rand_b = randomness & ((1 << 62) - 1)
    value = timestamp << 80
    value |= 0x7 << 76
    value |= rand_a << 64
    value |= 0b10 << 62
    value |= rand_b
    return str(uuid.UUID(int=value))


def short_reference(fact_type_key: str, object_uid: str) -> str:
    """Derive the six-character display/candidate reference for one UID object."""

    type_code = TYPE_CODES.get(fact_type_key)
    if type_code is None:
        raise ValueError(f"unknown fact type: {fact_type_key}")
    canonical = canonical_object_uid(object_uid)
    if canonical is None:
        raise ValueError("object_uid must be a canonical lowercase UUIDv7")

    digest = hashlib.sha256(f"{fact_type_key}:{canonical}".encode()).digest()
    number = int.from_bytes(digest, "big") % _SHORT_MODULUS
    encoded = ["A"] * 5
    for index in range(4, -1, -1):
        number, digit = divmod(number, 26)
        encoded[index] = chr(ord("A") + digit)
    return type_code + "".join(encoded)


__all__ = ["TYPE_CODES", "canonical_object_uid", "generate_object_uid", "short_reference"]
