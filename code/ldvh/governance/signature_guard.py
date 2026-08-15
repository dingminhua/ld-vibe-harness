"""Side-effect-free guard between governance identity and write attribution."""

from __future__ import annotations

from dataclasses import dataclass

from ldvh.signature import LDVHSignature

SIGNATURE_GOVERNANCE_INSTANCE_COLLISION = "signature_governance_instance_collision"


@dataclass(frozen=True, slots=True)
class SignatureGovernanceInstanceCollision:
    code: str
    message: str


def signature_governance_instance_collision(
    governance_instance_name: str | None,
    signature: LDVHSignature,
) -> SignatureGovernanceInstanceCollision | None:
    """Reject an instance name reused as the outer-product attribution."""

    product_name = signature.product_name
    if governance_instance_name is None or product_name is None:
        return None
    effective_instance_name = governance_instance_name.strip()
    if effective_instance_name != product_name:
        return None
    return SignatureGovernanceInstanceCollision(
        SIGNATURE_GOVERNANCE_INSTANCE_COLLISION,
        "署名 product_name 不得使用当前管辖实例名；请填写实际外层产品或在不可观察时使用 null",
    )


__all__ = [
    "SIGNATURE_GOVERNANCE_INSTANCE_COLLISION",
    "SignatureGovernanceInstanceCollision",
    "signature_governance_instance_collision",
]
