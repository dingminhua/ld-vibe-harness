from __future__ import annotations

import uuid

import pytest

from ldvh.facts.identity import (
    canonical_object_uid,
    generate_object_uid,
    short_reference,
)


def test_uuid7_generation_sets_timestamp_version_variant_and_canonical_text() -> None:
    value = generate_object_uid(timestamp_ms=0x0123456789AB, random_bits=0)
    parsed = uuid.UUID(value)

    assert value == "01234567-89ab-7000-8000-000000000000"
    assert parsed.version == 7
    assert parsed.variant == uuid.RFC_4122
    assert canonical_object_uid(value) == value


@pytest.mark.parametrize(
    "value",
    (
        "0198F1C7-8A2B-7C3D-9E4F-123456789ABC",
        "0198f1c78a2b7c3d9e4f123456789abc",
        "550e8400-e29b-41d4-a716-446655440000",
        "not-a-uuid",
        "",
    ),
)
def test_object_uid_accepts_only_canonical_lowercase_uuid7(value: str) -> None:
    assert canonical_object_uid(value) is None


def test_uuid7_generation_rejects_values_outside_the_wire_bit_ranges() -> None:
    with pytest.raises(ValueError):
        generate_object_uid(timestamp_ms=1 << 48, random_bits=0)
    with pytest.raises(ValueError):
        generate_object_uid(timestamp_ms=0, random_bits=1 << 74)


def test_short_reference_has_type_prefix_and_stable_sha256_base26_fingerprint() -> None:
    uid = "0198f1c7-8a2b-7c3d-9e4f-123456789abc"

    assert short_reference("spark", uid) == "SVUATH"
    assert short_reference("workcase", uid).startswith("C")
    assert short_reference("adr", uid).startswith("A")
    assert short_reference("pitfall", uid).startswith("P")
    assert short_reference("study", uid).startswith("T")


def test_short_reference_rejects_unknown_type_and_noncanonical_uid() -> None:
    with pytest.raises(ValueError):
        short_reference("unknown", "0198f1c7-8a2b-7c3d-9e4f-123456789abc")
    with pytest.raises(ValueError):
        short_reference("spark", "0198F1C7-8A2B-7C3D-9E4F-123456789ABC")
