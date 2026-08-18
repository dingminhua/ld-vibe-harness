from __future__ import annotations

from ldvh.governance.signature_guard import (
    SIGNATURE_GOVERNANCE_INSTANCE_COLLISION,
    SIGNATURE_TRAILER_RESERVED_FRAMEWORK_NAME,
    signature_governance_instance_collision,
    signature_trailer_reserved_framework_name,
)
from ldvh.signature import LDVHSignature


def _signature(product_name: str | None) -> LDVHSignature:
    return LDVHSignature(product_name=product_name, model_name="gpt-5")


def test_trimmed_governance_instance_name_collides_with_normalized_product_name() -> None:
    collision = signature_governance_instance_collision("  LDVH Governance  ", _signature("LDVH Governance"))

    assert collision is not None
    assert collision.code == SIGNATURE_GOVERNANCE_INSTANCE_COLLISION


def test_collision_comparison_does_not_fold_case() -> None:
    assert signature_governance_instance_collision("LDVH Governance", _signature("ldvh governance")) is None


def test_null_or_different_product_name_does_not_collide() -> None:
    assert signature_governance_instance_collision("LDVH Governance", _signature(None)) is None
    assert signature_governance_instance_collision("LDVH Governance", _signature("codex-desktop")) is None


class TestReservedFrameworkName:
    """The framework's own name (LDVH) must never be an outer-product name.

    The reserved check is case-insensitive on purpose: `LDVH`, `ldvh` and
    `Ldvh` are all the framework name, and no spelling should slip through.
    """

    def test_upper_case_ldvh_is_rejected(self) -> None:
        result = signature_trailer_reserved_framework_name(_signature("LDVH"))
        assert result is not None
        assert result.code == SIGNATURE_TRAILER_RESERVED_FRAMEWORK_NAME

    def test_lower_case_ldvh_is_rejected(self) -> None:
        result = signature_trailer_reserved_framework_name(_signature("ldvh"))
        assert result is not None
        assert result.code == SIGNATURE_TRAILER_RESERVED_FRAMEWORK_NAME

    def test_mixed_case_ldvh_is_rejected(self) -> None:
        result = signature_trailer_reserved_framework_name(_signature("Ldvh"))
        assert result is not None
        assert result.code == SIGNATURE_TRAILER_RESERVED_FRAMEWORK_NAME

    def test_trimmed_ldvh_is_rejected(self) -> None:
        result = signature_trailer_reserved_framework_name(_signature("  LDVH  "))
        assert result is not None
        assert result.code == SIGNATURE_TRAILER_RESERVED_FRAMEWORK_NAME

    def test_actual_product_name_is_allowed(self) -> None:
        for product_name in ("DeepSeek Harness", "Cindy", "codex-desktop", "DeepSeek Harness Web GUI"):
            assert signature_trailer_reserved_framework_name(_signature(product_name)) is None

    def test_null_product_name_is_allowed(self) -> None:
        assert signature_trailer_reserved_framework_name(_signature(None)) is None
