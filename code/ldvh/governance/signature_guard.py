"""Side-effect-free guard between governance identity and write attribution."""

from __future__ import annotations

from dataclasses import dataclass

from ldvh.signature import LDVHSignature

SIGNATURE_GOVERNANCE_INSTANCE_COLLISION = "signature_governance_instance_collision"
SIGNATURE_TRAILER_RESERVED_FRAMEWORK_NAME = "signature_trailer_reserved_framework_name"

# LDVH is the framework's own name, not an outer product.  Because the value
# is a product *display name* held verbatim, comparison is intentionally
# case-insensitive: `LDVH`, `ldvh`, `Ldvh` are all the framework name, and a
# product-name comparison that folded case only some of the time would let an
# unexpected spelling slip through.  The raw product_name is preserved for the
# message; only the reserved check folds case.
_RESERVED_FRAMEWORK_NAME = "ldvh"


@dataclass(frozen=True, slots=True)
class SignatureGovernanceInstanceCollision:
    code: str
    message: str


@dataclass(frozen=True, slots=True)
class ReservedFrameworkName:
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


def signature_trailer_reserved_framework_name(
    signature: LDVHSignature,
) -> ReservedFrameworkName | None:
    """Reject the framework's own name (`LDVH`) as the outer-product attribution.

    ``LDVH`` is the management framework's name, never an outer product; the
    product_name field must carry the product display name declared by the
    hosting prompt (e.g. ``DeepSeek Harness``).  Comparison is
    case-insensitive so no spelling of the framework name can slip through.
    """

    product_name = signature.product_name
    if product_name is None:
        return None
    if product_name.strip().lower() != _RESERVED_FRAMEWORK_NAME:
        return None
    return ReservedFrameworkName(
        SIGNATURE_TRAILER_RESERVED_FRAMEWORK_NAME,
        f"署名 product_name 不得使用 LDVH 框架名（收到 {product_name!r}）；"
        "请填写宿主系统提示直接声明的外层产品显示名（如 DeepSeek Harness），"
        "不可观察时停止并报告",
    )


__all__ = [
    "SIGNATURE_GOVERNANCE_INSTANCE_COLLISION",
    "SIGNATURE_TRAILER_RESERVED_FRAMEWORK_NAME",
    "SignatureGovernanceInstanceCollision",
    "ReservedFrameworkName",
    "signature_governance_instance_collision",
    "signature_trailer_reserved_framework_name",
]
