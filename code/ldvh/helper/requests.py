"""Parse the closed common Helper request object from standard input."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from ldvh.source_references import source_reference_problems

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


SIGNATURE_FIELDS = frozenset({"agent_id", "host_environment", "session_id"})


@dataclass(frozen=True, slots=True)
class ObservedSignatureParseResult:
    signature: dict[str, str]
    problems: tuple[str, ...]


def parse_observed_signature(observed_context: dict[str, Any]) -> ObservedSignatureParseResult:
    """Parse the optional ``observed_context.signature`` common sub-field.

    ``observed_context`` is an existing common request field; its ``signature``
    sub-field lets the executing session inject a responsibility signature
    (agent_id / host_environment / session_id) without creating a new top-level
    common field.  When ``observed_context`` is empty or carries no ``signature``,
    the result holds an empty signature and no problems, preserving legacy calls.
    """
    problems: list[str] = []
    if not observed_context:
        return ObservedSignatureParseResult({}, ())
    unknown = sorted(set(observed_context) - {"signature"})
    if unknown:
        problems.append(f"observed_context 只允许 signature 子字段: {', '.join(unknown)}")
        return ObservedSignatureParseResult({}, tuple(problems))
    raw_sig = observed_context.get("signature", {})
    if not _is_object(raw_sig):
        problems.append("observed_context.signature 必须是 object")
        return ObservedSignatureParseResult({}, tuple(problems))
    unknown_sig = sorted(set(raw_sig) - SIGNATURE_FIELDS)
    if unknown_sig:
        problems.append(f"observed_context.signature 包含未知字段: {', '.join(unknown_sig)}")
    signature: dict[str, str] = {}
    for name in sorted(SIGNATURE_FIELDS):
        value = raw_sig.get(name)
        if value is None:
            continue
        if not isinstance(value, str) or not value.strip():
            problems.append(f"observed_context.signature.{name} 出现时必须是非空 string")
        else:
            signature[name] = value.strip().lower()
    return ObservedSignatureParseResult(signature, tuple(problems))


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
            problems.extend(source_reference_problems(reference, f"authorization_reference[{index}]"))

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
