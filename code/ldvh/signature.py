"""The product-neutral LDVH signature contract for new writes."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass

FIELD_NAMES = ("product_name", "model_name", "agent_runtime_name")
_RUNTIME_SEPARATORS = re.compile(r"[\s_]+")
_MODEL_SEPARATORS = re.compile(r"\s+")
_MODEL_TRAILING_BRACKET_ANNOTATION = re.compile(r"\s*\[[^\[\]]*\]\s*$")


@dataclass(frozen=True, slots=True)
class LDVHSignature:
    """One environment-supplied attribution snapshot.

    The three fields deliberately carry no product-specific acquisition
    details.  A missing value is represented by ``None``; callers must not
    invent a replacement value.
    """

    product_name: str | None
    model_name: str | None
    agent_runtime_name: str | None

    def as_dict(self) -> dict[str, str | None]:
        return {
            "product_name": self.product_name,
            "model_name": self.model_name,
            "agent_runtime_name": self.agent_runtime_name,
        }

    @property
    def is_empty(self) -> bool:
        return all(value is None for value in self.as_dict().values())


def parse_signature(value: object) -> tuple[LDVHSignature | None, tuple[str, ...]]:
    """Parse the complete three-field snapshot without inferring any value."""

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
            normalized[name] = None
        elif not isinstance(raw, str) or not raw.strip():
            problems.append(f"LDVH 署名.{name} 必须是非空 string 或 null")
        else:
            normalized[name] = _normalize(name, raw)
            if not normalized[name]:
                problems.append(f"LDVH 署名.{name} 归一后不得为空")
    if problems:
        return None, tuple(problems)
    signature = LDVHSignature(**normalized)
    if signature.is_empty:
        return None, ("LDVH 署名三项均不可得，新的受控写入必须停止",)
    return signature, ()


def _normalize_product_name(value: str) -> str:
    return value


def _normalize_model_name(value: str) -> str:
    while annotation := _MODEL_TRAILING_BRACKET_ANNOTATION.search(value):
        value = value[: annotation.start()].rstrip()
    return _MODEL_SEPARATORS.sub("-", value.lower())


def _normalize_agent_runtime_name(value: str) -> str:
    return _RUNTIME_SEPARATORS.sub("-", value.lower())


_FIELD_NORMALIZERS = {
    "product_name": _normalize_product_name,
    "model_name": _normalize_model_name,
    "agent_runtime_name": _normalize_agent_runtime_name,
}


def _normalize(name: str, value: str) -> str:
    """Dispatch every signature field through its one canonical normalizer."""

    value = value.strip()
    normalizer = _FIELD_NORMALIZERS[name]
    return normalizer(value)


__all__ = ["FIELD_NAMES", "LDVHSignature", "parse_signature"]
