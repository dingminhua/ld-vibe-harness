"""Parse source-defined action-template candidate and content requests."""

from __future__ import annotations

from dataclasses import dataclass

from ldvh.helper.requests import CommonRequest, valid_operation_key

CANDIDATE_REQUIRED_INPUTS: tuple[str, ...] = ()
CANDIDATE_OPTIONAL_INPUTS: tuple[str, ...] = ("arguments.template_keys",)
CONTENT_REQUIRED_INPUTS: tuple[str, ...] = ("arguments.template_keys",)
CONTENT_OPTIONAL_INPUTS: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ActionTemplateRequest:
    template_keys: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ActionTemplateRequestParseResult:
    request: ActionTemplateRequest | None
    problems: tuple[str, ...]


def parse_action_template_request(
    request: CommonRequest,
    *,
    require_keys: bool,
) -> ActionTemplateRequestParseResult:
    problems: list[str] = []
    unknown = sorted(set(request.arguments) - {"template_keys"})
    if unknown:
        problems.append(f"arguments 包含未知字段: {', '.join(unknown)}")
    raw_keys = request.arguments.get("template_keys")
    if raw_keys is None:
        raw_keys = []
    if not isinstance(raw_keys, list):
        problems.append("arguments.template_keys 必须是 array")
        raw_keys = []
    limit = 64 if require_keys else 128
    if require_keys and not raw_keys:
        problems.append("arguments.template_keys 必须包含至少一个成员")
    if len(raw_keys) > limit:
        problems.append(f"arguments.template_keys 最多包含 {limit} 个成员")
    keys: list[str] = []
    for index, key in enumerate(raw_keys):
        if not isinstance(key, str) or not key:
            problems.append(f"arguments.template_keys[{index}] 必须是非空 string")
        elif not valid_operation_key(key):
            problems.append(f"arguments.template_keys[{index}] 格式无效")
        else:
            keys.append(key)
    if len(keys) != len(set(keys)):
        problems.append("arguments.template_keys 的成员不得重复")
    if request.work_object_locators:
        problems.append("work_object_locators 必须为空数组")
    if request.observed_context:
        problems.append("observed_context 必须为空对象")
    if request.authorization_reference:
        problems.append("authorization_reference 必须为空数组")
    if request.requested_disclosure is not None:
        problems.append("requested_disclosure 必须为 null")
    if problems:
        return ActionTemplateRequestParseResult(None, tuple(problems))
    return ActionTemplateRequestParseResult(ActionTemplateRequest(tuple(keys)), ())


__all__ = [
    "ActionTemplateRequest",
    "ActionTemplateRequestParseResult",
    "CANDIDATE_OPTIONAL_INPUTS",
    "CANDIDATE_REQUIRED_INPUTS",
    "CONTENT_OPTIONAL_INPUTS",
    "CONTENT_REQUIRED_INPUTS",
    "parse_action_template_request",
]
