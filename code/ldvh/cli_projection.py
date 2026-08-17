"""Pure CLI option parsing and transport projections for the LDVH launcher."""

from __future__ import annotations

import copy
import json
import os
import re
import stat
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from ldvh.signature import FIELD_NAMES

RequestKind = Literal["capabilities", "call"]
MAX_REQUEST_BYTES = 4 * 1024 * 1024
_FIELD_MEMBER = re.compile(r"[A-Za-z_][A-Za-z0-9_-]*\Z")
_OPERATION_EFFECTS = frozenset({"read", "may_change_state"})
_INPUT_EXAMPLE_FIELDS = frozenset({"summary", "arguments_fragment", "source_refs", "composition_note"})
_MANDATORY_PROJECTION_PATHS = (
    "contract",
    "request_kind",
    "operation_key",
    "outcome",
    "scope.not_completed",
)


@dataclass(frozen=True, slots=True)
class ParsedCLICommand:
    """One mechanically parsed Helper CLI invocation."""

    request_kind: RequestKind
    operation_key: str | None
    request_path: str | None = None
    message_file_path: str | None = None
    example: bool = False
    summary: bool = False
    field_selectors: tuple[str, ...] = ()


def parse_cli_arguments(
    arguments: list[str],
) -> tuple[ParsedCLICommand | None, tuple[str, ...], bool]:
    """Parse the closed command/option grammar.

    The final boolean asks the process boundary to print usage instead of a
    machine response.  Once a recognized Helper entry has enough shape to
    identify a request kind, option and extra-position errors stay machine
    readable.
    """

    if not arguments or arguments[0] not in {"capabilities", "call"}:
        return None, (), True

    request_kind: RequestKind = arguments[0]  # type: ignore[assignment]
    positionals: list[str] = []
    request_path: str | None = None
    message_file_path: str | None = None
    example = False
    summary = False
    fields_seen = False
    field_selectors: tuple[str, ...] = ()
    problems: list[str] = []
    index = 1
    while index < len(arguments):
        token = arguments[index]
        if token == "--summary":
            if summary:
                problems.append("--summary 不得重复")
            summary = True
            index += 1
            continue
        if token == "--request":
            if request_path is not None:
                problems.append("--request 不得重复")
                index += 1
                if index < len(arguments) and not arguments[index].startswith("--"):
                    index += 1
                continue
            index += 1
            if index >= len(arguments) or arguments[index].startswith("--"):
                problems.append("--request 必须紧随一个非空路径")
                continue
            request_path = arguments[index]
            index += 1
            continue
        if token == "--message-file":
            if message_file_path is not None:
                problems.append("--message-file 不得重复")
                index += 1
                if index < len(arguments) and not arguments[index].startswith("--"):
                    index += 1
                continue
            index += 1
            if index >= len(arguments) or arguments[index].startswith("--"):
                problems.append("--message-file 必须紧随一个非空路径")
                continue
            message_file_path = arguments[index]
            index += 1
            continue
        if token == "--fields":
            if fields_seen:
                problems.append("--fields 不得重复")
                index += 1
                if index < len(arguments) and not arguments[index].startswith("--"):
                    index += 1
                continue
            fields_seen = True
            index += 1
            if index >= len(arguments) or arguments[index].startswith("--"):
                problems.append("--fields 必须紧随非空 selector 列表")
                continue
            field_selectors, field_problems = parse_field_selectors(arguments[index])
            problems.extend(field_problems)
            index += 1
            continue
        if token == "--example":
            if example:
                problems.append("--example 不得重复")
            example = True
            index += 1
            continue
        if token.startswith("--"):
            problems.append(f"未知 CLI 选项: {token}")
            index += 1
            continue
        positionals.append(token)
        index += 1

    operation_key = positionals[0] if positionals else None
    if request_kind == "capabilities":
        if len(positionals) > 1:
            problems.append("capabilities 至多接受一个 operation_key")
    elif not positionals:
        if not problems and request_path is None:
            return None, (), True
        problems.append("call 必须提供一个 operation_key")
    elif len(positionals) > 1:
        problems.append("call 只接受一个 operation_key")

    if example:
        if request_kind != "capabilities" or operation_key is None:
            problems.append("--example 只允许用于带 operation_key 的 capabilities")
        if request_path is not None:
            problems.append("--example 不得与 --request 同时使用")
        if fields_seen:
            problems.append("--example 不得与 --fields 同时使用")
        if message_file_path is not None:
            problems.append("--example 不得与 --message-file 同时使用")
    if summary:
        if request_kind != "capabilities":
            problems.append("--summary 只允许用于 capabilities")
        if operation_key is not None:
            problems.append("--summary 不得与 operation_key 同时使用")
        if request_path is not None:
            problems.append("--summary 不得与 --request 同时使用")
        if fields_seen:
            problems.append("--summary 不得与 --fields 同时使用")
        if example:
            problems.append("--summary 不得与 --example 同时使用")
        if message_file_path is not None:
            problems.append("--summary 不得与 --message-file 同时使用")
    if message_file_path is not None and request_kind != "call":
        problems.append("--message-file 只允许用于 call")

    return (
        ParsedCLICommand(
            request_kind=request_kind,
            operation_key=operation_key,
            request_path=request_path,
            message_file_path=message_file_path,
            example=example,
            summary=summary,
            field_selectors=field_selectors,
        ),
        tuple(problems),
        False,
    )


def parse_field_selectors(value: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Parse the deliberately small object-only dotted selector grammar."""

    selectors = tuple(value.split(","))
    problems: list[str] = []
    if not value or any(not selector for selector in selectors):
        problems.append("--fields selector 不得为空")
    for selector in selectors:
        members = selector.split(".")
        if not selector or any(not _FIELD_MEMBER.fullmatch(member) for member in members):
            problems.append(f"--fields selector 语法无效: {selector!r}")
    if len(set(selectors)) != len(selectors):
        problems.append("--fields selector 不得重复")
    for index, selector in enumerate(selectors):
        for other in selectors[index + 1 :]:
            if selector.startswith(f"{other}.") or other.startswith(f"{selector}."):
                problems.append(f"--fields 不得同时选择祖先与后代路径: {selector}, {other}")
    return selectors, tuple(problems)


def read_request_file(path_text: str) -> tuple[str | None, tuple[str, ...]]:
    """Read one explicit bounded regular UTF-8 request file without rewriting it."""

    if not path_text or path_text == "-":
        return None, ("--request 路径必须非空且不得使用 '-'",)
    path = Path(path_text)
    if path.is_symlink():
        return None, ("--request 只接受非符号链接的普通文件",)
    descriptor: int | None = None
    try:
        flags = os.O_RDONLY | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(path, flags)
        file_stat = os.fstat(descriptor)
        if not stat.S_ISREG(file_stat.st_mode):
            return None, ("--request 只接受普通文件",)
        if file_stat.st_size > MAX_REQUEST_BYTES:
            return None, (f"--request 文件不得超过 {MAX_REQUEST_BYTES} bytes",)
        chunks: list[bytes] = []
        remaining = MAX_REQUEST_BYTES + 1
        while remaining:
            chunk = os.read(descriptor, remaining)
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        raw = b"".join(chunks)
    except OSError:
        return None, ("--request 指定的文件不存在或不可读",)
    finally:
        if descriptor is not None:
            os.close(descriptor)
    if len(raw) > MAX_REQUEST_BYTES:
        return None, (f"--request 文件不得超过 {MAX_REQUEST_BYTES} bytes",)
    try:
        return raw.decode("utf-8"), ()
    except UnicodeDecodeError:
        return None, ("--request 文件必须是 UTF-8",)


def _set_skeleton_path(target: dict[str, Any], dotted_path: str) -> None:
    members = dotted_path.split(".")
    current = target
    for member in members[:-1]:
        existing = current.get(member)
        if existing is None:
            nested: dict[str, Any] = {}
            current[member] = nested
            current = nested
        elif isinstance(existing, dict):
            current = existing
        else:
            raise ValueError(f"required input path 与 example fragment 结构冲突: {dotted_path}")
    current.setdefault(members[-1], None)


def _unique_source_refs(source_refs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for source_ref in source_refs:
        key = json.dumps(source_ref, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        if key not in seen:
            seen.add(key)
            result.append(source_ref)
    return result


def _lookup_object_path(source: Mapping[str, Any], dotted_path: str) -> tuple[bool, Any]:
    """Resolve a dotted path through dicts and lists.

    Mapping members are resolved by key.  A list is traversed by projecting the
    remaining members into every element, so the returned value keeps the source
    array structure while only containing the selected members.  ``False`` is
    returned only when the path is absent everywhere along the navigation.
    """

    members = dotted_path.split(".")
    return _project_path(source, members)


def _project_path(current: Any, members: list[str]) -> tuple[bool, Any]:
    if not members:
        return True, copy.deepcopy(current)
    if isinstance(current, list):
        if not current:
            return True, []
        projected: list[Any] = []
        any_present = False
        for element in current:
            present, sub = _project_path(element, members)
            if present:
                projected.append(sub)
                any_present = True
        if not any_present:
            return False, None
        return True, projected
    if not isinstance(current, Mapping):
        return False, None
    member = members[0]
    if member not in current:
        return False, None
    present, sub = _project_path(current[member], members[1:])
    if not present:
        return False, None
    return True, {member: sub}


def _assign_object_path(target: dict[str, Any], dotted_path: str, value: Any) -> None:
    """Deep-merge a structure-preserving projection into ``target``.

    ``value`` already mirrors the source structure along ``dotted_path`` (a
    dict or list), so this only merges it at the path root.  The path is
    accepted for call compatibility; nested members of ``value`` carry the
    remaining structure.
    """

    _deep_merge(target, value)


def _deep_merge(target: dict[str, Any], patch: Any) -> None:
    if not isinstance(patch, Mapping) or not isinstance(target, dict):
        return
    for key, value in patch.items():
        existing = target.get(key)
        if isinstance(value, Mapping) and isinstance(existing, Mapping):
            _deep_merge(existing, value)
        elif isinstance(value, list) and isinstance(existing, list) and len(value) == len(existing):
            for index, member in enumerate(value):
                if isinstance(member, Mapping) and isinstance(existing[index], Mapping):
                    _deep_merge(existing[index], member)
                else:
                    existing[index] = copy.deepcopy(member)
        else:
            target[key] = copy.deepcopy(value)


def _validate_projectable_response(response: Mapping[str, Any]) -> None:
    for path in _MANDATORY_PROJECTION_PATHS:
        present, _ = _lookup_object_path(response, path)
        if not present:
            raise ValueError(f"完整 Helper response 缺少 projection core: {path}")
    if response.get("contract") != "ldvh-helper-cli/2":
        raise ValueError("完整 Helper response contract 无效")
    if response.get("request_kind") not in {"capabilities", "call"}:
        raise ValueError("完整 Helper response request_kind 无效")
    operation_key = response.get("operation_key")
    if operation_key is not None and not isinstance(operation_key, str):
        raise ValueError("完整 Helper response operation_key 无效")
    if not isinstance(response.get("outcome"), str):
        raise ValueError("完整 Helper response outcome 无效")
    if not isinstance(response.get("gaps"), list):
        raise ValueError("完整 Helper response gaps 无效")
    scope = response.get("scope")
    if not isinstance(scope, Mapping) or not isinstance(scope.get("not_completed"), list):
        raise ValueError("完整 Helper response scope.not_completed 无效")


def project_response_fields(
    response: Mapping[str, Any], selectors: tuple[str, ...], source_exit_code: int
) -> dict[str, Any]:
    """Project a complete Helper response without changing its outcome or exit code."""

    _validate_projectable_response(response)
    projected_response: dict[str, Any] = {}
    for path in _MANDATORY_PROJECTION_PATHS:
        _, value = _lookup_object_path(response, path)
        _assign_object_path(projected_response, path, value)

    missing: list[str] = []
    for selector in selectors:
        present, value = _lookup_object_path(response, selector)
        if present:
            _assign_object_path(projected_response, selector, value)
        else:
            missing.append(selector)

    return {
        "projection": {
            "requested": list(selectors),
            "missing": missing,
            "source_outcome": response.get("outcome"),
            "source_exit_code": source_exit_code,
            "source_gap_count": len(response["gaps"]),
            "source_response_complete": True,
        },
        "response": projected_response,
    }


def _validate_example_metadata(operation: Mapping[str, Any]) -> None:
    required_inputs = operation.get("required_inputs")
    input_examples = operation.get("input_examples")
    sources = operation.get("sources")
    if not isinstance(operation.get("operation_key"), str) or not operation["operation_key"].strip():
        raise ValueError("单操作 capabilities metadata 缺少 operation_key")
    if operation.get("effect") not in _OPERATION_EFFECTS:
        raise ValueError("单操作 capabilities metadata effect 无效")
    if (
        not isinstance(required_inputs, list)
        or any(not isinstance(path, str) or not path for path in required_inputs)
        or len(set(required_inputs)) != len(required_inputs)
    ):
        raise ValueError("单操作 capabilities metadata required_inputs 无效")
    if not isinstance(sources, list) or not sources or any(not isinstance(item, Mapping) for item in sources):
        raise ValueError("单操作 capabilities metadata sources 无效")
    if not isinstance(input_examples, list):
        raise ValueError("单操作 capabilities metadata input_examples 无效")
    for example in input_examples:
        if not isinstance(example, Mapping) or set(example) != _INPUT_EXAMPLE_FIELDS:
            raise ValueError("source-bound input example 字段闭集无效")
        if any(
            not isinstance(example[field], str) or not example[field].strip()
            for field in ("summary", "composition_note")
        ):
            raise ValueError("source-bound input example 文本字段无效")
        if not isinstance(example["arguments_fragment"], Mapping):
            raise ValueError("source-bound input example arguments_fragment 无效")
        source_refs = example["source_refs"]
        if (
            not isinstance(source_refs, (list, tuple))
            or not source_refs
            or any(not isinstance(item, Mapping) for item in source_refs)
        ):
            raise ValueError("source-bound input example source_refs 无效")


def build_example_projection(operation: Mapping[str, Any]) -> dict[str, Any]:
    """Build one explicitly non-executable request skeleton from capability metadata."""

    _validate_example_metadata(operation)
    required_inputs = operation["required_inputs"]
    input_examples = operation["input_examples"]
    sources = operation["sources"]

    request: dict[str, Any] = {}
    source_refs = [copy.deepcopy(dict(item)) for item in sources]
    note_parts = ["这是待填写的 CLI 请求骨架，不表示授权、适用、可用或可执行。"]
    if input_examples:
        selected = input_examples[0]
        if not isinstance(selected, Mapping) or not isinstance(selected.get("arguments_fragment"), Mapping):
            raise ValueError("首个 source-bound input example 结构无效")
        request["arguments"] = copy.deepcopy(dict(selected["arguments_fragment"]))
        example_sources = selected.get("source_refs")
        if not isinstance(example_sources, (list, tuple)):
            raise ValueError("首个 source-bound input example 缺少来源")
        source_refs.extend(copy.deepcopy(dict(item)) for item in example_sources)
        composition_note = selected.get("composition_note")
        if isinstance(composition_note, str) and composition_note.strip():
            note_parts.append(composition_note.strip())
    else:
        note_parts.append("当前操作没有 source-bound input example；仅按 required input path 生成 null 占位。")

    for dotted_path in required_inputs:
        _set_skeleton_path(request, dotted_path)

    if operation.get("effect") == "may_change_state":
        observed_context = request.setdefault("observed_context", {})
        if not isinstance(observed_context, dict):
            raise ValueError("请求骨架 observed_context 路径冲突")
        observed_context["signature"] = {field_name: None for field_name in FIELD_NAMES}
        note_parts.append("两字段署名全为 null 时不可执行；调用方必须逐项直接观察，不得缓存、推导或默认填值。")

    return {
        "operation_key": operation["operation_key"],
        "request": request,
        "required_input_paths": list(required_inputs),
        "composition_note": " ".join(note_parts),
        "source_refs": _unique_source_refs(source_refs),
    }


__all__ = [
    "MAX_REQUEST_BYTES",
    "ParsedCLICommand",
    "build_example_projection",
    "parse_cli_arguments",
    "parse_field_selectors",
    "project_response_fields",
    "read_request_file",
]
