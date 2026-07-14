"""Parse the closed common Helper request object from standard input."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any

OPERATION_KEY_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
REQUEST_FIELDS = frozenset(
    {
        "task",
        "work_object_locators",
        "arguments",
        "requested_disclosure",
        "response_profile",
        "observed_context",
        "authorization_reference",
    }
)
DISCLOSURE_LEVELS = frozenset({"L0", "L1", "L2", "L3", "L4"})
SOURCE_REFERENCE_FIELDS = frozenset({"kind", "locator", "version", "observed_at", "details"})
_MISSING = object()


@dataclass(frozen=True, slots=True)
class CommonRequest:
    task: str | None
    work_object_locators: tuple[str | dict[str, Any], ...]
    arguments: dict[str, Any]
    requested_disclosure: str | None
    observed_context: dict[str, Any]
    authorization_reference: tuple[dict[str, Any], ...]
    response_profile: str = "compact"


@dataclass(frozen=True, slots=True)
class RequestParseResult:
    request: CommonRequest | None
    problems: tuple[str, ...]


def valid_operation_key(value: str) -> bool:
    return bool(OPERATION_KEY_PATTERN.fullmatch(value))


def _is_object(value: object) -> bool:
    return isinstance(value, dict)


def _is_rfc3339_with_offset(value: str) -> bool:
    if "T" not in value:
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None


def _source_reference_problems(value: object, index: int) -> list[str]:
    prefix = f"authorization_reference[{index}]"
    if not _is_object(value):
        return [f"{prefix} 必须是对象"]
    problems: list[str] = []
    unknown = sorted(set(value) - SOURCE_REFERENCE_FIELDS)
    if unknown:
        problems.append(f"{prefix} 包含未知字段: {', '.join(unknown)}")
    for required in ("kind", "locator"):
        item = value.get(required)
        if not isinstance(item, str) or not item:
            problems.append(f"{prefix}.{required} 必须是非空 string")
    for optional in ("version", "observed_at"):
        if optional in value and (not isinstance(value[optional], str) or not value[optional]):
            problems.append(f"{prefix}.{optional} 出现时必须是非空 string")
    observed_at = value.get("observed_at")
    if isinstance(observed_at, str) and observed_at and not _is_rfc3339_with_offset(observed_at):
        problems.append(f"{prefix}.observed_at 必须是包含 UTC 偏移的 RFC 3339 时间")
    if "details" in value and not _is_object(value["details"]):
        problems.append(f"{prefix}.details 必须是 object")
    return problems


def parse_common_request(raw: str, *, general_discovery: bool) -> RequestParseResult:
    if not raw.strip():
        value: object = {}
    else:
        try:
            value = json.loads(raw)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            return RequestParseResult(None, (f"标准输入不是一个有效 JSON 对象: {exc.msg}",))

    if not _is_object(value):
        return RequestParseResult(None, ("标准输入 JSON 顶层必须是对象",))

    problems: list[str] = []
    unknown = sorted(set(value) - REQUEST_FIELDS)
    if unknown:
        problems.append(f"请求包含未知共同字段: {', '.join(unknown)}")

    task_value = value.get("task", _MISSING)
    if task_value is not _MISSING and (not isinstance(task_value, str) or not task_value):
        problems.append("task 出现时必须是非空 string")
    task = None if task_value is _MISSING else task_value

    locators = value.get("work_object_locators", [])
    if not isinstance(locators, list):
        problems.append("work_object_locators 必须是 array")
        locators = []
    else:
        for index, locator in enumerate(locators):
            if not isinstance(locator, (str, dict)):
                problems.append(f"work_object_locators[{index}] 必须是 string 或 object")

    arguments = value.get("arguments", {})
    if not _is_object(arguments):
        problems.append("arguments 必须是 object")
        arguments = {}
    elif general_discovery and arguments:
        problems.append("通用 capabilities 请求的 arguments 必须为空对象")

    disclosure = value.get("requested_disclosure")
    if disclosure is not None and disclosure not in DISCLOSURE_LEVELS:
        problems.append("requested_disclosure 只允许 L0、L1、L2、L3、L4 或 null")

    response_profile = value.get("response_profile", "compact")
    if not isinstance(response_profile, str) or response_profile not in {"compact", "diagnostic"}:
        problems.append("response_profile 只允许 compact 或 diagnostic")

    observed = value.get("observed_context", {})
    if not _is_object(observed):
        problems.append("observed_context 必须是 object")
        observed = {}

    authorization = value.get("authorization_reference", [])
    if not isinstance(authorization, list):
        problems.append("authorization_reference 必须是 array")
        authorization = []
    else:
        for index, reference in enumerate(authorization):
            problems.extend(_source_reference_problems(reference, index))

    if problems:
        return RequestParseResult(None, tuple(problems))
    return RequestParseResult(
        CommonRequest(
            task=task,
            work_object_locators=tuple(locators),
            arguments=dict(arguments),
            requested_disclosure=disclosure,
            response_profile=response_profile,
            observed_context=dict(observed),
            authorization_reference=tuple(dict(reference) for reference in authorization),
        ),
        (),
    )
