"""Deterministic fact-object checks derived from projected fields and type sources."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import PurePosixPath
from typing import Any
from urllib.parse import urlparse

from ldvh.facts.contracts import LAYOUTS, TERMINAL_COMMON
from ldvh.facts.models import FactIssue
from ldvh.facts.schema import FactSchema


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
    if isinstance(value, str) and not value:
        issues.append(FactIssue("schema", "string 字段不得为空", path))
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
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?(?:Z|[+-][0-9]{2}:[0-9]{2})\Z"
)


def parse_rfc3339(value: object) -> datetime | None:
    if not isinstance(value, str) or _RFC3339.fullmatch(value) is None:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def _time(value: object, path: str, issues: list[FactIssue]) -> datetime | None:
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
    if status not in layout.statuses:
        issues.append(FactIssue("schema", f"status 必须属于 {sorted(layout.statuses)}", "status"))
        return
    if "priority" in fields and fields["priority"] not in {"P0", "P1", "P2", "P3"}:
        issues.append(FactIssue("schema", "priority 不在 P0、P1、P2、P3 闭集中", "priority"))
    if fact_type_key == "spark":
        if status == "open":
            _require(fields, {"priority"}, issues)
            _forbid(fields, {"disposition_summary", "closed_at"}, issues)
        else:
            _require(fields, TERMINAL_COMMON, issues)
            _forbid(fields, {"priority"}, issues)
    elif fact_type_key == "workcase":
        terminal = {"validation_summary", "closure_outcome", "disposition_summary", "closed_at", "evidence_refs"}
        if status == "open":
            _require(fields, {"priority"}, issues)
            _forbid(fields, {"blocking_summary", *terminal}, issues)
        elif status == "blocked":
            _require(fields, {"priority", "blocking_summary", "evidence_refs"}, issues)
            _forbid(fields, {"closure_outcome", "disposition_summary", "closed_at", "validation_summary"}, issues)
        else:
            _require(fields, terminal, issues)
            _forbid(fields, {"priority", "blocking_summary"}, issues)
            if fields.get("closure_outcome") not in {
                "completed",
                "partial",
                "not-achieved",
                "cancelled",
                "superseded",
            }:
                issues.append(FactIssue("schema", "closure_outcome 不在当前闭集中", "closure_outcome"))
    else:
        if status == "active":
            _forbid(fields, {"disposition_summary", "closed_at"}, issues)
        else:
            _require(fields, TERMINAL_COMMON, issues)


def _validate_times(fact_type_key: str, fields: dict[str, Any], issues: list[FactIssue]) -> None:
    created = _time(fields.get("created_at"), "created_at", issues) if "created_at" in fields else None
    updated = _time(fields.get("updated_at"), "updated_at", issues) if "updated_at" in fields else None
    if created is not None and updated is not None and created > updated:
        issues.append(FactIssue("schema", "created_at 不得晚于 updated_at", "created_at"))
    closed = _time(fields.get("closed_at"), "closed_at", issues) if "closed_at" in fields else None
    if created is not None and closed is not None and created > closed:
        issues.append(FactIssue("schema", "closed_at 不得早于 created_at", "closed_at"))
    if updated is not None and closed is not None and closed > updated:
        issues.append(FactIssue("schema", "closed_at 不得晚于 updated_at", "closed_at"))
    if fact_type_key == "adr" and "decided_at" in fields:
        decided = _time(fields["decided_at"], "decided_at", issues)
        if decided is not None and created is not None and decided > created:
            issues.append(FactIssue("schema", "decided_at 不得晚于 created_at", "decided_at"))
    if fact_type_key == "spark" and isinstance(fields.get("evolution"), list):
        evolution = fields["evolution"]
        if len(evolution) > 8:
            issues.append(FactIssue("schema", "evolution 最多保留 8 项", "evolution"))
        for index, entry in enumerate(evolution):
            if not isinstance(entry, dict) or "at" not in entry:
                continue
            at = _time(entry["at"], f"evolution[{index}].at", issues)
            if at is not None and created is not None and at < created:
                issues.append(FactIssue("schema", "evolution.at 不得早于 created_at", f"evolution[{index}].at"))
            if at is not None and updated is not None and at > updated:
                issues.append(FactIssue("schema", "evolution.at 不得晚于 updated_at", f"evolution[{index}].at"))


def _validate_references(fact_type_key: str, fields: dict[str, Any], issues: list[FactIssue]) -> None:
    updated = None
    if fact_type_key == "study" and "updated_at" in fields:
        updated = _time(fields["updated_at"], "updated_at", [])
    study_kinds = {
        "fact-object",
        "repository-path",
        "git-revision",
        "web-page",
        "api-observation",
        "runtime-observation",
        "human-provided-artifact",
    }
    arrays: list[tuple[str, object, bool]] = [
        ("source_refs", fields.get("source_refs"), True),
        ("evidence_refs", fields.get("evidence_refs"), True),
    ]
    relations = fields.get("relations")
    if isinstance(relations, list):
        for relation_index, relation in enumerate(relations):
            if not isinstance(relation, dict):
                continue
            arrays.append((f"relations[{relation_index}].source_refs", relation.get("source_refs"), False))
            target = relation.get("target")
            if isinstance(target, dict):
                arrays.append(
                    (f"relations[{relation_index}].target.governance_refs", target.get("governance_refs"), False)
                )
    for array_name, values, study_top_level in arrays:
        if not isinstance(values, list):
            continue
        seen: set[tuple[object, ...]] = set()
        for index, reference in enumerate(values):
            if not isinstance(reference, dict):
                continue
            path = f"{array_name}[{index}]"
            identity = tuple(reference.get(key) for key in ("kind", "locator", "version", "observed_at"))
            if fact_type_key == "study" and study_top_level and identity in seen:
                issues.append(FactIssue("reference", "同一引用数组中不得重复引用", path))
            seen.add(identity)
            if "observed_at" in reference:
                observed = _time(reference["observed_at"], f"{path}.observed_at", issues)
            else:
                observed = None
            if fact_type_key != "study" or not study_top_level:
                continue
            kind = reference.get("kind")
            if kind not in study_kinds:
                issues.append(FactIssue("reference", "Study 引用 kind 不在当前闭集中", f"{path}.kind"))
            if "observed_at" not in reference:
                issues.append(FactIssue("reference", "Study 的每项引用必须包含 observed_at", f"{path}.observed_at"))
            else:
                if observed is not None and updated is not None and observed > updated:
                    issues.append(FactIssue("reference", "observed_at 不得晚于 updated_at", f"{path}.observed_at"))
            if kind in {"git-revision", "api-observation", "runtime-observation"} and "version" not in reference:
                issues.append(FactIssue("reference", f"{kind} 引用必须包含 version", f"{path}.version"))
            locator = reference.get("locator")
            if isinstance(kind, str) and isinstance(locator, str) and not _valid_study_locator(kind, locator):
                issues.append(FactIssue("reference", f"locator 不符合 {kind} profile", f"{path}.locator"))


_FACT_OBJECT_LOCATOR = re.compile(
    r"facts/(?P<directory>sparks|workcases|adrs|pitfalls|studies)/"
    r"(?P<object_id>spark|workcase|adr|pitfall|study)-[0-9]{4,}(?P<suffix>\.yaml|\.md)\Z"
)


def _stable_relative_path(locator: str) -> bool:
    if (
        not locator
        or locator.startswith("/")
        or locator.endswith("/")
        or "//" in locator
        or "\\" in locator
        or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", locator)
    ):
        return False
    parts = PurePosixPath(locator).parts
    return bool(parts) and all(part not in {"", ".", ".."} for part in parts)


def _valid_study_locator(kind: str, locator: str) -> bool:
    if kind in {"web-page", "api-observation"}:
        parsed = urlparse(locator)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
    if kind == "fact-object":
        match = _FACT_OBJECT_LOCATOR.fullmatch(locator)
        if match is None:
            return False
        object_id = match.group("object_id")
        directory = match.group("directory")
        suffix = match.group("suffix")
        expected = {
            "spark": ("sparks", ".yaml"),
            "workcase": ("workcases", ".yaml"),
            "adr": ("adrs", ".yaml"),
            "pitfall": ("pitfalls", ".yaml"),
            "study": ("studies", ".md"),
        }
        prefix = object_id.split("-", 1)[0]
        return expected.get(prefix) == (directory, suffix)
    return _stable_relative_path(locator)


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


def validate_fact_object(fact_type_key: str, fields: dict[str, Any], schema: FactSchema) -> tuple[FactIssue, ...]:
    issues: list[FactIssue] = []
    _validate_mapping(fields, _tree(schema), "", issues)
    if fields.get("fact_type_key") != fact_type_key:
        issues.append(FactIssue("identity", "fact_type_key 与请求类型不一致", "fact_type_key"))
    _validate_status(fact_type_key, fields, issues)
    _validate_times(fact_type_key, fields, issues)
    if fact_type_key == "workcase" and isinstance(fields.get("success_criteria"), list):
        criteria = fields["success_criteria"]
        if any(not isinstance(item, str) or not item for item in criteria):
            issues.append(FactIssue("schema", "success_criteria 成员必须是非空 string", "success_criteria"))
        elif len(criteria) != len(set(criteria)):
            issues.append(FactIssue("schema", "success_criteria 成员不得重复", "success_criteria"))
    _validate_references(fact_type_key, fields, issues)
    _validate_relations(fact_type_key, fields, issues)
    return tuple(issues)


__all__ = ["parse_rfc3339", "validate_fact_object"]
