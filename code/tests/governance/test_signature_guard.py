from __future__ import annotations

from ldvh.governance.signature_guard import (
    SIGNATURE_GOVERNANCE_INSTANCE_COLLISION,
    signature_governance_instance_collision,
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
