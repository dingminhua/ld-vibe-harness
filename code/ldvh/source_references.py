"""Pure validation for the shared 04.Att.01 source-reference shape."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from ldvh.facts.validation import parse_rfc3339

SOURCE_REFERENCE_FIELDS = frozenset({"kind", "locator", "version", "observed_at", "details"})


@dataclass(frozen=True, slots=True)
class SourceReferenceProblem:
    path: str
    summary: str


def _nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_rfc3339_with_offset(value: str) -> bool:
    return parse_rfc3339(value) is not None


def validate_source_reference(value: object, path: str) -> tuple[SourceReferenceProblem, ...]:
    """Validate one source reference without normalizing caller-provided values."""

    if not isinstance(value, Mapping):
        return (SourceReferenceProblem(path, "必须是对象"),)

    problems: list[SourceReferenceProblem] = []
    unknown = sorted(key for key in value if isinstance(key, str) and key not in SOURCE_REFERENCE_FIELDS)
    if unknown:
        problems.append(SourceReferenceProblem(path, f"包含未知字段: {', '.join(unknown)}"))
    if any(not isinstance(key, str) for key in value):
        problems.append(SourceReferenceProblem(path, "字段名必须是 string"))

    for required in ("kind", "locator"):
        if not _nonempty_string(value.get(required)):
            problems.append(
                SourceReferenceProblem(
                    f"{path}.{required}",
                    "必须是非空 string（至少包含一个非空白字符）",
                )
            )
    for optional in ("version", "observed_at"):
        if optional in value and not _nonempty_string(value[optional]):
            problems.append(
                SourceReferenceProblem(
                    f"{path}.{optional}",
                    "出现时必须是非空 string（至少包含一个非空白字符）",
                )
            )
    observed_at = value.get("observed_at")
    if _nonempty_string(observed_at) and not _is_rfc3339_with_offset(observed_at):
        problems.append(
            SourceReferenceProblem(
                f"{path}.observed_at",
                "必须是包含 UTC 偏移的 RFC 3339 时间",
            )
        )
    if "details" in value and not isinstance(value["details"], Mapping):
        problems.append(SourceReferenceProblem(f"{path}.details", "必须是 object"))
    return tuple(problems)


def source_reference_problems(value: object, path: str) -> list[str]:
    """Render shared source-reference problems for request diagnostics."""

    return [f"{problem.path} {problem.summary}" for problem in validate_source_reference(value, path)]


__all__ = [
    "SOURCE_REFERENCE_FIELDS",
    "SourceReferenceProblem",
    "source_reference_problems",
    "validate_source_reference",
]
