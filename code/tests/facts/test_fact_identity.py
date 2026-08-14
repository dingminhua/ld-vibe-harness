from __future__ import annotations

import uuid

import pytest

import ldvh.facts.identity as identity
from ldvh.facts.identity import (
    canonical_object_uid,
    generate_object_uid,
    locator_from_object_uid,
    object_uid_from_locator,
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


def test_identity_public_api_contains_only_full_uid_and_reversible_locator_capabilities() -> None:
    retired_name = "".join(("short", "_reference"))

    assert retired_name not in identity.__all__
    assert not hasattr(identity, retired_name)


def test_crockford_locator_has_fixed_width_and_round_trips_uuid7() -> None:
    uid = "019ffb52-ebb5-72f3-861a-31869779aa44"
    locator = locator_from_object_uid("spark", uid)

    assert locator == "spark-01KZXN5TXNEBSRC6HHGTBQKAJ4"
    assert object_uid_from_locator("spark", locator) == uid


@pytest.mark.parametrize(
    "locator",
    (
        "spark-01KZXN5TXNEBSRC6HHGTBQKAJ!4",
        "spark-81KZXN5TXNEBSRC6HHGTBQKAJ4",  # 130-bit overflow
        "spark-01KZXN5TXNEBSRC6HHGTBQKAJ",
        "spark-01KZXN5TXNEBSRC6HHGTBQKAJ4x",
        "spark-01kzxn5txnebsrc6hhgtbqkaj4",  # lowercase is not canonical
        "workcase-01KZXN5TXNEBSRC6HHGTBQKAJ4",
    ),
)
def test_crockford_locator_rejects_invalid_or_wrong_type_encoding(locator: str) -> None:
    assert object_uid_from_locator("spark", locator) is None
