"""Deterministic fact-object checks derived from current projected fields."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from typing import Any
from urllib.parse import urlparse

from ldvh.facts.contracts import LAYOUTS, TERMINAL_COMMON
from ldvh.facts.models import FactIssue
from ldvh.facts.schema import FactSchema
from ldvh.facts.workcase_validation import validate_workcase_snapshot


@dataclass(slots=True)
class _Node:
    json_type: str | None = None
    presence: str = "conditional"
    children: dict[str, _Node] = field(default_factory=dict)


def _tree(schema: FactSchema) -> _Node:
    root = _Node(json_type="object", presence="required")
    for projected in schema.fields:
        current = root
        for raw_segment in projected.path.split("."):
            segment = raw_segment.removesuffix("[]")
            current = current.children.setdefault(segment, _Node())
        current.json_type = projected.json_type
        current.presence = projected.presence
    return root


def _matches_type(value: Any, expected: str) -> bool:
    if expected == "string":
        return isinstance(value, str)
    if expected == "array":
        return isinstance(value, list)
    if expected == "object":
        return isinstance(value, dict)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    return False


def _join(parent: str, child: str) -> str:
    return child if not parent else f"{parent}.{child}"


def _validate_node(value: Any, node: _Node, path: str, issues: list[FactIssue]) -> None:
    expected = node.json_type
    if expected is None or not _matches_type(value, expected):
        issues.append(FactIssue("schema", f"字段必须是 {expected or '已登记类型'}", path))
        return
    if isinstance(value, str) and not value.strip():
        issues.append(FactIssue("schema", "string 字段不得为空或只包含空白", path))
        return
    if isinstance(value, list):
        if not value:
            issues.append(FactIssue("schema", "array 字段出现时不得为空", path))
            return
        if node.children:
            for index, item in enumerate(value):
                item_path = f"{path}[{index}]"
                if not isinstance(item, dict):
                    issues.append(FactIssue("schema", "array 成员必须是 object", item_path))
                    continue
                _validate_mapping(item, node, item_path, issues)
        return
    if isinstance(value, dict):
        _validate_mapping(value, node, path, issues)


def _validate_mapping(value: dict[str, Any], node: _Node, path: str, issues: list[FactIssue]) -> None:
    for key in value:
        if not isinstance(key, str):
            issues.append(FactIssue("schema", "JSON object 的字段名必须是 string", path or None))
    string_keys = {key for key in value if isinstance(key, str)}
    unknown = sorted(string_keys - set(node.children))
    for key in unknown:
        issues.append(FactIssue("schema", "字段未在当前 Schema 登记", _join(path, str(key))))
    for key, child in node.children.items():
        child_path = _join(path, key)
        if key not in value:
            if child.presence == "required":
                issues.append(FactIssue("schema", "缺少必填字段", child_path))
            continue
        if child.presence == "forbidden":
            issues.append(FactIssue("schema", "当前类型禁止该字段", child_path))
            continue
        if value[key] is None:
            issues.append(FactIssue("schema", "字段不得使用 null 占位", child_path))
            continue
        _validate_node(value[key], child, child_path, issues)


_RFC3339 = re.compile(
    r"(?P<year>[0-9]{4})-(?P<month>0[1-9]|1[0-2])-(?P<day>0[1-9]|[12][0-9]|3[01])"
    r"T(?P<hour>[01][0-9]|2[0-3]):(?P<minute>[0-5][0-9]):(?P<second>[0-5][0-9])"
    r"(?:\.(?P<fraction>[0-9]+))?"
    r"(?P<offset>Z|(?P<offset_sign>[+-])(?P<offset_hour>[01][0-9]|2[0-3]):"
    r"(?P<offset_minute>[0-5][0-9]))\Z"
)
_EPOCH_ORDINAL = date(1970, 1, 1).toordinal()
_FILE_ASSET_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_FILE_ASSET_MEDIA_TYPE = re.compile(
    r"[a-z0-9][a-z0-9!#$&^_.+-]*/[a-z0-9][a-z0-9!#$&^_.+-]*\Z"
)


@dataclass(frozen=True, order=True, slots=True)
class RFC3339Instant:
    """One lossless instant used only for validation and ordering.

    ``fractional_digits`` is the exact decimal fraction after removing only
    trailing zeroes, which preserves the represented instant while making
    numerically equal spellings compare equal.  The caller-owned timestamp
    string is never normalized or rewritten.
    """

    utc_second: int
    fractional_digits: str


def parse_rfc3339(value: object) -> RFC3339Instant | None:
    """Parse LDVH's strict regular RFC 3339 timestamp form.

    This common boundary deliberately rejects ISO 8601 alternatives such as
    week/basic dates and non-colon offsets.  Leap-second support requires a
    separately governed time-scale source and is not inferred here.
    """

    if not isinstance(value, str):
        return None
    match = _RFC3339.fullmatch(value)
    if match is None:
        return None
    if match["offset"] == "-00:00":
        return None
    try:
        local_date = date(
            int(match["year"]),
            int(match["month"]),
            int(match["day"]),
        )
    except ValueError:
        return None

    local_second = (
        (local_date.toordinal() - _EPOCH_ORDINAL) * 86_400
        + int(match["hour"]) * 3_600
        + int(match["minute"]) * 60
        + int(match["second"])
    )
    offset_second = 0
    if match["offset"] != "Z":
        offset_second = int(match["offset_hour"]) * 3_600 + int(match["offset_minute"]) * 60
        if match["offset_sign"] == "-":
            offset_second = -offset_second
    fraction = (match["fraction"] or "").rstrip("0")
    return RFC3339Instant(local_second - offset_second, fraction)


def _time(value: object, path: str, issues: list[FactIssue]) -> RFC3339Instant | None:
    parsed = parse_rfc3339(value)
    if parsed is None:
        issues.append(FactIssue("schema", "时间必须是包含 UTC 偏移的 RFC 3339 string", path))
        return None
    return parsed


def _require(fields: dict[str, Any], names: set[str] | frozenset[str], issues: list[FactIssue]) -> None:
    for name in sorted(names):
        if name not in fields:
            issues.append(FactIssue("schema", "当前状态要求该字段", name))


def _forbid(fields: dict[str, Any], names: set[str] | frozenset[str], issues: list[FactIssue]) -> None:
    for name in sorted(names):
        if name in fields:
            issues.append(FactIssue("schema", "当前状态禁止该字段", name))


def _validate_status(fact_type_key: str, fields: dict[str, Any], issues: list[FactIssue]) -> None:
    status = fields.get("status")
    layout = LAYOUTS[fact_type_key]
    if not isinstance(status, str) or status not in layout.statuses:
        issues.append(FactIssue("schema", f"status 必须属于 {sorted(layout.statuses)}", "status"))
        return
    if "priority" in fields and fields["priority"] not in {"P0", "P1", "P2", "P3"}:
        issues.append(FactIssue("schema", "priority 不在 P0、P1、P2、P3 闭集中", "priority"))
    if fact_type_key == "spark":
        if status == "open":
            _require(fields, {"priority"}, issues)
            _forbid(fields, {"disposition_summary"}, issues)
        elif status == "routed":
            _require(fields, TERMINAL_COMMON, issues)
            _forbid(fields, {"priority"}, issues)
        else:  # discarded
            _require(fields, {"disposition_summary"}, issues)
            _forbid(fields, {"priority"}, issues)
    elif fact_type_key == "workcase":
        # The type has a phase-dependent single current shape.  Its complete
        # presence contract is centralized in workcase_validation.py.
        return
    elif fact_type_key == "study":
        if status == "active":
            _require(fields, {"research_intent", "recommendation_summary"}, issues)
            _forbid(fields, {"disposition_summary"}, issues)
        else:
            _require(fields, TERMINAL_COMMON, issues)
    elif fact_type_key == "pitfall":
        if status in {"draft", "active"}:
            _forbid(fields, {"disposition_summary"}, issues)
        else:
            _require(fields, TERMINAL_COMMON, issues)
    else:
        if status == "active":
            _forbid(fields, {"disposition_summary"}, issues)
        else:
            _require(fields, TERMINAL_COMMON, issues)


def _validate_times(fact_type_key: str, fields: dict[str, Any], issues: list[FactIssue]) -> None:
    created = _time(fields.get("created_at"), "created_at", issues) if "created_at" in fields else None
    updated = _time(fields.get("updated_at"), "updated_at", issues) if "updated_at" in fields else None
    if created is not None and updated is not None and created > updated:
        issues.append(FactIssue("schema", "created_at 不得晚于 updated_at", "created_at"))
    if fact_type_key == "spark" and isinstance(fields.get("evolution"), list):
        evolution = fields["evolution"]
        if len(evolution) > 20:
            issues.append(FactIssue("schema", "evolution 最多保留 20 项", "evolution"))
        for index, entry in enumerate(evolution):
            if not isinstance(entry, dict) or "at" not in entry:
                continue
            at = _time(entry["at"], f"evolution[{index}].at", issues)
            if at is not None and created is not None and at < created:
                issues.append(FactIssue("schema", "evolution.at 不得早于 created_at", f"evolution[{index}].at"))
            if at is not None and updated is not None and at > updated:
                issues.append(FactIssue("schema", "evolution.at 不得晚于 updated_at", f"evolution[{index}].at"))
    if fact_type_key == "workcase":
        nested_times: list[tuple[str, object, bool]] = []
        for array_name in ("creation_reviews", "result_reviews"):
            values = fields.get(array_name)
            if isinstance(values, list):
                nested_times.extend(
                    (
                        f"{array_name}[{index}].reviewed_at",
                        value.get("reviewed_at"),
                        array_name != "creation_reviews",
                    )
                    for index, value in enumerate(values)
                    if isinstance(value, dict) and "reviewed_at" in value
                )
        approval = fields.get("execution_approval")
        if isinstance(approval, dict) and "approved_at" in approval:
            nested_times.append(("execution_approval.approved_at", approval["approved_at"], True))
        for path, value, requires_created_lower_bound in nested_times:
            at = _time(value, path, issues)
            if at is not None and created is not None and requires_created_lower_bound and at < created:
                issues.append(FactIssue("schema", "WorkCase 事件时间不得早于 created_at", path))
            if at is not None and updated is not None and at > updated:
                issues.append(FactIssue("schema", "WorkCase 事件时间不得晚于 updated_at", path))


def _validate_references(fact_type_key: str, fields: dict[str, Any], issues: list[FactIssue]) -> None:
    urls = fields.get("urls")
    if urls is None:
        if fact_type_key == "study":
            issues.append(FactIssue("reference", "Study 必须至少包含一项 urls", "urls"))
        return
    if not isinstance(urls, list):
        return
    seen: set[str] = set()
    for index, value in enumerate(urls):
        if not isinstance(value, dict):
            continue
        ref = value.get("ref")
        if not isinstance(ref, str) or urlparse(ref).scheme not in {"http", "https"} or not urlparse(ref).netloc:
            issues.append(FactIssue("reference", "urls.ref 必须是绝对 HTTP(S) URL", f"urls[{index}].ref"))
            continue
        if ref in seen:
            issues.append(FactIssue("reference", "同一对象中 urls.ref 不得重复", f"urls[{index}].ref"))
        seen.add(ref)


def _validate_relations(fact_type_key: str, fields: dict[str, Any], issues: list[FactIssue]) -> None:
    relations = fields.get("relations")
    if not isinstance(relations, list):
        return
    allowed = LAYOUTS[fact_type_key].relation_keys
    for index, relation in enumerate(relations):
        if not isinstance(relation, dict):
            continue
        path = f"relations[{index}]"
        if relation.get("relation_key") not in allowed:
            issues.append(FactIssue("relation", "relation_key 不在当前类型闭集中", f"{path}.relation_key"))


def _validate_file_asset(fields: dict[str, Any], issues: list[FactIssue]) -> None:
    filename = fields.get("filename")
    if isinstance(filename, str) and (
        filename in {".", ".."} or any(mark in filename for mark in ("/", "\\", "\0"))
    ):
        issues.append(
            FactIssue("schema", "filename 必须是不含路径分隔符或 NUL 的 basename", "filename")
        )
    media_type = fields.get("media_type")
    if isinstance(media_type, str) and _FILE_ASSET_MEDIA_TYPE.fullmatch(media_type) is None:
        issues.append(
            FactIssue("schema", "media_type 必须是小写且不带参数的 type/subtype", "media_type")
        )
    size_bytes = fields.get("size_bytes")
    if isinstance(size_bytes, int) and not isinstance(size_bytes, bool) and size_bytes < 0:
        issues.append(FactIssue("schema", "size_bytes 必须是不小于 0 的 integer", "size_bytes"))
    content_sha256 = fields.get("content_sha256")
    if isinstance(content_sha256, str) and _FILE_ASSET_SHA256.fullmatch(content_sha256) is None:
        issues.append(
            FactIssue(
                "schema",
                "content_sha256 必须是 64 位小写十六进制 SHA-256",
                "content_sha256",
            )
        )

    signature = fields.get("signature")
    if not isinstance(signature, dict):
        return
    signer_type = signature.get("signer_type")
    if signer_type == "human":
        expected = {"signer_type"}
    elif signer_type == "ai-agent":
        expected = {"signer_type", "agent_id", "host_environment"}
    else:
        issues.append(
            FactIssue(
                "schema",
                "signature.signer_type 必须是 human 或 ai-agent",
                "signature.signer_type",
            )
        )
        return
    for name in sorted(set(signature) - expected):
        issues.append(FactIssue("schema", "当前签名分支禁止该字段", f"signature.{name}"))
    for name in sorted(expected - set(signature)):
        issues.append(FactIssue("schema", "当前签名分支缺少必填字段", f"signature.{name}"))


def validate_fact_object(fact_type_key: str, fields: dict[str, Any], schema: FactSchema) -> tuple[FactIssue, ...]:
    issues: list[FactIssue] = []
    _validate_mapping(fields, _tree(schema), "", issues)
    if fields.get("fact_type_key") != fact_type_key:
        issues.append(FactIssue("identity", "fact_type_key 与请求类型不一致", "fact_type_key"))
    _validate_status(fact_type_key, fields, issues)
    if fact_type_key == "workcase":
        issues.extend(validate_workcase_snapshot(fields))
    elif fact_type_key == "file-asset":
        _validate_file_asset(fields, issues)
    _validate_times(fact_type_key, fields, issues)
    _validate_references(fact_type_key, fields, issues)
    _validate_relations(fact_type_key, fields, issues)
    return tuple(issues)


__all__ = ["parse_rfc3339", "validate_fact_object"]
