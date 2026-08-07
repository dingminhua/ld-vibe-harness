"""Parse exact inputs for specification-context composition reads."""

from __future__ import annotations

from dataclasses import dataclass

from ldvh.helper.requests import CommonRequest
from ldvh.specs.identity import KEY_PATTERN

REQUIRED_INPUTS: tuple[str, ...] = (
    "arguments.contexts",
    "requested_disclosure",
)
OPTIONAL_INPUTS: tuple[str, ...] = ()

_ARGUMENT_FIELDS = frozenset({"contexts"})
_CONTEXT_FIELDS = frozenset({"responsibility_key", "primary_heading_paths"})


@dataclass(frozen=True, slots=True)
class SpecificationContextSelection:
    responsibility_key: str
    primary_heading_paths: tuple[tuple[str, ...], ...]

    def as_scope(self) -> dict[str, object]:
        return {
            "responsibility_key": self.responsibility_key,
            "primary_heading_paths": [list(path) for path in self.primary_heading_paths],
        }


@dataclass(frozen=True, slots=True)
class SpecificationContextRequest:
    contexts: tuple[SpecificationContextSelection, ...]


@dataclass(frozen=True, slots=True)
class SpecificationContextRequestParseResult:
    request: SpecificationContextRequest | None
    problems: tuple[str, ...]


def _parse_heading_path(value: object, *, prefix: str, problems: list[str]) -> tuple[str, ...] | None:
    if not isinstance(value, list):
        problems.append(f"{prefix} 必须是长度为 1 或 2 的 string array")
        return None
    if len(value) not in {1, 2}:
        problems.append(f"{prefix} 长度只允许 1 或 2")
    headings: list[str] = []
    for index, heading in enumerate(value):
        item_prefix = f"{prefix}[{index}]"
        if not isinstance(heading, str) or not heading:
            problems.append(f"{item_prefix} 必须是非空 string")
            continue
        if heading != heading.strip():
            problems.append(f"{item_prefix} 不得带首尾空白")
        headings.append(heading)
    return tuple(headings) if len(headings) == len(value) and len(value) in {1, 2} else None


def _parse_primary_paths(value: object, *, prefix: str, problems: list[str]) -> tuple[tuple[str, ...], ...]:
    if not isinstance(value, list):
        problems.append(f"{prefix} 必须是 array")
        return ()
    if len(value) > 16:
        problems.append(f"{prefix} 最多允许 16 项")

    paths: list[tuple[str, ...]] = []
    for index, raw_path in enumerate(value):
        path = _parse_heading_path(raw_path, prefix=f"{prefix}[{index}]", problems=problems)
        if path is not None:
            paths.append(path)

    if len(paths) != len(set(paths)):
        problems.append(f"{prefix} 不得包含重复标题路径")
    for index, left in enumerate(paths):
        for right in paths[index + 1 :]:
            shorter, longer = (left, right) if len(left) <= len(right) else (right, left)
            if len(shorter) < len(longer) and longer[: len(shorter)] == shorter:
                problems.append(f"{prefix} 不得同时包含互为前缀的 H2 与 H3 路径")
                return tuple(paths)
    return tuple(paths)


def parse_specification_context_request(
    request: CommonRequest,
) -> SpecificationContextRequestParseResult:
    """Validate the closed context-selection contract without reading a repository."""

    problems: list[str] = []
    unknown_arguments = sorted(set(request.arguments) - _ARGUMENT_FIELDS)
    if unknown_arguments:
        problems.append(f"arguments 包含未知字段: {', '.join(unknown_arguments)}")
    if request.requested_disclosure != "L3":
        problems.append("requested_disclosure 必填且固定为 L3")
    if request.observed_context:
        problems.append("observed_context 在本操作中必须为空对象")

    raw_contexts = request.arguments.get("contexts")
    contexts: list[SpecificationContextSelection] = []
    if not isinstance(raw_contexts, list) or not raw_contexts:
        problems.append("arguments.contexts 必须是包含 1–32 项的非空 array")
    elif len(raw_contexts) > 32:
        problems.append("arguments.contexts 最多允许 32 项")
    else:
        for index, raw_context in enumerate(raw_contexts):
            prefix = f"arguments.contexts[{index}]"
            if not isinstance(raw_context, dict):
                problems.append(f"{prefix} 必须是 object")
                continue
            missing = sorted(_CONTEXT_FIELDS - set(raw_context))
            unknown = sorted(set(raw_context) - _CONTEXT_FIELDS)
            if missing:
                problems.append(f"{prefix} 缺少字段: {', '.join(missing)}")
            if unknown:
                problems.append(f"{prefix} 包含未知字段: {', '.join(unknown)}")

            responsibility_key = raw_context.get("responsibility_key")
            valid_key = isinstance(responsibility_key, str) and KEY_PATTERN.fullmatch(responsibility_key) is not None
            if not valid_key:
                problems.append(f"{prefix}.responsibility_key 必须是合法的非空职责标识符")
            primary_paths = _parse_primary_paths(
                raw_context.get("primary_heading_paths"),
                prefix=f"{prefix}.primary_heading_paths",
                problems=problems,
            )
            if valid_key and "primary_heading_paths" in raw_context:
                contexts.append(SpecificationContextSelection(responsibility_key, primary_paths))

    keys = [context.responsibility_key for context in contexts]
    if len(keys) != len(set(keys)):
        problems.append("arguments.contexts 的 responsibility_key 不得重复")

    if problems:
        return SpecificationContextRequestParseResult(None, tuple(problems))
    return SpecificationContextRequestParseResult(SpecificationContextRequest(tuple(contexts)), ())


__all__ = [
    "OPTIONAL_INPUTS",
    "REQUIRED_INPUTS",
    "SpecificationContextRequest",
    "SpecificationContextRequestParseResult",
    "SpecificationContextSelection",
    "parse_specification_context_request",
]
