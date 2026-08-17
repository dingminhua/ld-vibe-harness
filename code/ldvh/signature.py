"""The product-neutral LDVH signature contract for new writes.

2026-08-17: Removed agent_runtime_name per WorkCase
workcase-01M08D6XAKF3FSTMETTGKEK7T7.  The two-field contract
(product_name, model_name) is now mandatory: both must be non-null
and non-empty, or the write is blocked.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass

FIELD_NAMES = ("product_name", "model_name")
_MODEL_SEPARATORS = re.compile(r"\s+")
_MODEL_TRAILING_BRACKET_ANNOTATION = re.compile(r"\s*\[[^\[\]]*\]\s*$")

@dataclass(frozen=True, slots=True)
class LDVHSignature:
    """One environment-supplied attribution snapshot.

    Both fields are mandatory for new writes.  A missing value means
    the caller must report the gap and stop; unlike the previous three-field
    contract, partial observability is not an acceptable path.
    """

    product_name: str
    model_name: str

    def as_dict(self) -> dict[str, str | None]:
        return {
            "product_name": self.product_name,
            "model_name": self.model_name,
        }


def parse_signature(value: object) -> tuple[LDVHSignature | None, tuple[str, ...]]:
    """Parse the complete two-field signature.

    Both fields must be present, non-null, and normalize to a non-empty
    string.  Unlike the retired three-field contract, a missing / null
    value is a hard error: the caller must report the gap and stop.
    """

    if not isinstance(value, Mapping):
        return None, ("LDVH 署名必须是 object",)
    keys = set(value)
    expected = set(FIELD_NAMES)
    problems: list[str] = []
    unknown = sorted(keys - expected)
    missing = sorted(expected - keys)
    if unknown:
        problems.append(f"LDVH 署名包含未知字段: {', '.join(unknown)}")
    if missing:
        problems.append(f"LDVH 署名缺少字段: {', '.join(missing)}")
    normalized: dict[str, str | None] = {}
    for name in FIELD_NAMES:
        raw = value.get(name)
        if raw is None:
            problems.append(f"LDVH 署名.{name} 必须是非空 string（不可观察时必须停止并报告）")
        elif not isinstance(raw, str) or not raw.strip():
            problems.append(f"LDVH 署名.{name} 必须是非空 string 或 null")
        else:
            normalized[name] = _normalize(name, raw)
            if not normalized[name]:
                problems.append(f"LDVH 署名.{name} 归一后不得为空")
    if problems:
        return None, tuple(problems)
    return LDVHSignature(**normalized), ()


def _normalize_product_name(value: str) -> str:
    return value


def _normalize_model_name(value: str) -> str:
    while annotation := _MODEL_TRAILING_BRACKET_ANNOTATION.search(value):
        value = value[: annotation.start()].rstrip()
    return _MODEL_SEPARATORS.sub("-", value.lower())


_FIELD_NORMALIZERS = {
    "product_name": _normalize_product_name,
    "model_name": _normalize_model_name,
}


def _normalize(name: str, value: str) -> str:
    """Dispatch every signature field through its one canonical normalizer."""

    value = value.strip()
    normalizer = _FIELD_NORMALIZERS[name]
    return normalizer(value)


__all__ = ["FIELD_NAMES", "LDVHSignature", "parse_signature"]
