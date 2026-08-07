"""Parse source-defined inputs for exact specification-content reads."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from ldvh.helper.requests import CommonRequest

DisclosureLevel = Literal["L3", "L4"]

REQUIRED_INPUTS: tuple[str, ...] = (
    "arguments.selections",
    "requested_disclosure",
)
OPTIONAL_INPUTS: tuple[str, ...] = ()

_ARGUMENT_FIELDS = frozenset({"selections"})
_SELECTION_FIELDS = frozenset({"responsibility_key", "heading_path"})


@dataclass(frozen=True, slots=True)
class SpecificationContentSelection:
    responsibility_key: str
    heading_path: tuple[str, ...] | None

    def as_scope(self) -> dict[str, object]:
        return {
            "responsibility_key": self.responsibility_key,
            "heading_path": None if self.heading_path is None else list(self.heading_path),
        }


@dataclass(frozen=True, slots=True)
class SpecificationContentRequest:
    selections: tuple[SpecificationContentSelection, ...]
    disclosure: DisclosureLevel


@dataclass(frozen=True, slots=True)
class SpecificationContentRequestParseResult:
    request: SpecificationContentRequest | None
    problems: tuple[str, ...]


def _parse_heading_path(
    value: object,
    *,
    disclosure: DisclosureLevel | None,
    prefix: str,
    problems: list[str],
) -> tuple[str, ...] | None:
    if disclosure == "L4":
        if value is not None:
            problems.append(f"{prefix} 在 requested_disclosure=L4 时必须为 null")
        return None
    if disclosure != "L3":
        return None
    if not isinstance(value, list):
        problems.append(f"{prefix} 在 requested_disclosure=L3 时必须是长度为 1 或 2 的 string array")
        return None
    if len(value) not in {1, 2}:
        problems.append(f"{prefix} 在 requested_disclosure=L3 时长度只允许 1 或 2")
    headings: list[str] = []
    for index, heading in enumerate(value):
        item_prefix = f"{prefix}[{index}]"
        if not isinstance(heading, str) or not heading:
            problems.append(f"{item_prefix} 必须是非空 string")
            continue
        if heading != heading.strip():
            problems.append(f"{item_prefix} 不得带首尾空白")
        headings.append(heading)
    return tuple(headings)


def parse_specification_content_request(
    request: CommonRequest,
) -> SpecificationContentRequestParseResult:
    """Validate the closed domain request without reading a repository."""

    problems: list[str] = []
    unknown_arguments = sorted(set(request.arguments) - _ARGUMENT_FIELDS)
    if unknown_arguments:
        problems.append(f"arguments 包含未知字段: {', '.join(unknown_arguments)}")

    disclosure: DisclosureLevel | None = None
    if request.requested_disclosure in {"L3", "L4"}:
        disclosure = request.requested_disclosure  # type: ignore[assignment]
    else:
        problems.append("requested_disclosure 必填且只允许 L3 或 L4")

    if request.observed_context:
        problems.append("observed_context 在本操作中必须为空对象")

    raw_selections = request.arguments.get("selections")
    selections: list[SpecificationContentSelection] = []
    if not isinstance(raw_selections, list) or not raw_selections:
        problems.append("arguments.selections 必须是非空 array")
    else:
        for index, raw_selection in enumerate(raw_selections):
            prefix = f"arguments.selections[{index}]"
            if not isinstance(raw_selection, dict):
                problems.append(f"{prefix} 必须是 object")
                continue
            missing = sorted(_SELECTION_FIELDS - set(raw_selection))
            unknown = sorted(set(raw_selection) - _SELECTION_FIELDS)
            if missing:
                problems.append(f"{prefix} 缺少字段: {', '.join(missing)}")
            if unknown:
                problems.append(f"{prefix} 包含未知字段: {', '.join(unknown)}")

            responsibility_key = raw_selection.get("responsibility_key")
            valid_key = isinstance(responsibility_key, str) and bool(responsibility_key)
            if not valid_key:
                problems.append(f"{prefix}.responsibility_key 必须是非空 string")

            heading_path = _parse_heading_path(
                raw_selection.get("heading_path"),
                disclosure=disclosure,
                prefix=f"{prefix}.heading_path",
                problems=problems,
            )
            if valid_key and disclosure is not None:
                selections.append(
                    SpecificationContentSelection(
                        responsibility_key=responsibility_key,
                        heading_path=heading_path,
                    )
                )

    identities = [(selection.responsibility_key, selection.heading_path) for selection in selections]
    if len(identities) != len(set(identities)):
        problems.append("arguments.selections 的精确选择不得重复")

    if problems or disclosure is None:
        return SpecificationContentRequestParseResult(None, tuple(problems))
    return SpecificationContentRequestParseResult(
        SpecificationContentRequest(selections=tuple(selections), disclosure=disclosure),
        (),
    )


__all__ = [
    "OPTIONAL_INPUTS",
    "REQUIRED_INPUTS",
    "SpecificationContentRequest",
    "SpecificationContentRequestParseResult",
    "SpecificationContentSelection",
    "parse_specification_content_request",
]
