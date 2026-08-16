"""Deterministic fact-object checks derived from current projected fields."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date
from typing import Any
from urllib.parse import urlparse

from ldvh.facts.contracts import LAYOUTS, TERMINAL_COMMON, is_legacy_spark_object
from ldvh.facts.identity import canonical_object_uid
from ldvh.facts.models import FactIssue
from ldvh.facts.schema import FactSchema
from ldvh.facts.workcase_validation import validate_workcase_snapshot
from ldvh.signature import parse_signature


_CHINESE_PRIMARY_NATURAL_FIELD_NAMES = frozenset(
    {
        "abstract", "action_ceiling", "allowed_adjustments", "applicability", "avoidance",
        "blocking_summary", "cleanup_summary", "consequences", "controller_check_summary",
        "controller_resolution", "current_summary", "decision", "decision_question",
        "disposition_summary", "effect_scope", "expected_result", "feedback", "goal",
        "impact_summary", "intent", "not_meaning", "observation_summary",
        "out_of_bounds_handling", "rationale", "reason", "recommendation_summary",
        "research_intent", "research_question", "resolution", "result_summary", "resume_from",
        "risk_summary", "rollback_summary", "root_cause", "scope", "statement",
        "summary", "symptoms", "target_scope", "title", "trigger_conditions",
        "validation_summary", "verification_and_rollback", "waiting_on",
    }
)
_CJK_CHARACTER = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")


def validate_chinese_primary_changes(
    fields: Mapping[str, Any],
    *,
    before: Mapping[str, Any] | None = None,
) -> tuple[FactIssue, ...]:
    """Reject changed natural-language strings that contain no Han character.

    This is deliberately a minimum mechanical guard: it does not decide whether
    prose is Chinese-primary.  The optional ``before`` confines updates to the
    controlled write's changed values, preserving legacy reads and untouched
    English fields.  Arrays of members that carry a stable identity key
    (``item_id`` / ``criterion_id`` / ``action_id``…) are matched by that key so
    that reordering the array does not re-baseline untouched members against a
    different sibling; new members without a matching identity are treated as
    this-write's changes.
    """
    issues: list[FactIssue] = []

    # 稳定身份候选键：数组成员里携带这些键之一时，用它做跨 before/after 的身份对照。
    _IDENTITY_KEYS = ("item_id", "criterion_id", "action_id", "limitation_id", "gate_id", "reviewed_at")

    def _member_identity(member: Mapping[str, Any]) -> tuple[str | None, Any]:
        for key in _IDENTITY_KEYS:
            if key in member:
                return key, member[key]
        return None, None

    def visit(value: Any, previous: Any, path: str, key: str | None) -> None:
        if isinstance(value, Mapping):
            prior = previous if isinstance(previous, Mapping) else {}
            for member_key, member in value.items():
                next_path = f"{path}.{member_key}" if path else str(member_key)
                visit(member, prior.get(member_key), next_path, str(member_key))
        elif isinstance(value, list):
            prior = previous if isinstance(previous, list) else []
            if all(isinstance(item, Mapping) for item in value):
                # 所有列表成员都是 object：优先按稳定身份键对照。
                prior_by_identity: dict[Any, Mapping[str, Any]] = {}
                for prior_member in prior:
                    if isinstance(prior_member, Mapping):
                        identity_key, identity_value = _member_identity(prior_member)
                        if identity_key is not None and identity_value is not None:
                            prior_by_identity[identity_value] = prior_member
                for index, member in enumerate(value):
                    identity_key, identity_value = _member_identity(member)
                    prior_member = None
                    if identity_key is not None and identity_value is not None:
                        prior_member = prior_by_identity.get(identity_value)
                        if prior_member is None:
                            prior_member = (
                                prior[index] if index < len(prior) else None
                            )
                    else:
                        # 没有可识别身份键：退化为按位置对照。
                        prior_member = prior[index] if index < len(prior) else None
                    visit(member, prior_member, f"{path}[{index}]", key)
            else:
                prior = previous if isinstance(previous, list) else []
                for index, member in enumerate(value):
                    prior_member = prior[index] if index < len(prior) else None
                    visit(member, prior_member, f"{path}[{index}]", key)
        elif (
            key in _CHINESE_PRIMARY_NATURAL_FIELD_NAMES
            and isinstance(value, str)
            and value != previous
            and not _CJK_CHARACTER.search(value)
        ):
            issues.append(FactIssue("language", "受约束自然语言字段至少必须包含一个汉字", path))

    visit(fields, before, "", None)
    return tuple(issues)


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
        if value[key] is None and path.endswith(".signature"):
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
# Placeholder session ids (e.g. ``current-session``) are never valid; a real
# session identifier must be supplied instead.  This is a denylist, not a UUID
# requirement, because session ids across the suite are arbitrary tokens
# (test-session, trae-commit-session, …) and a UUID-only rule would false-positive.
_SESSION_PLACEHOLDER_RE = re.compile(
    r"^(current-session|session|placeholder|todo|none|null|n/a|tbd)$", re.I
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


def _validate_change_log_signature(value: object, path: str, issues: list[FactIssue]) -> None:
    if not isinstance(value, dict):
        return
    legacy_allowed = {"agent_id", "host_environment"}
    if set(value) == legacy_allowed:
        # Historical shape remains readable and mechanically valid.
        return
    if set(value) == {"signer_type", *legacy_allowed} and value.get("signer_type") in {"human", "ai-agent"}:
        # Existing facts must remain readable long enough for the narrowly
        # controlled transition validator to remove this retired member.
        return
    interim_legacy = {"model_id", "host_name"}
    if set(value) == interim_legacy and all(
        isinstance(value.get(name), str) and value[name].strip() for name in interim_legacy
    ):
        # The host_name shape predates the agent_workbench rename.  Historical
        # records stay readable.
        return
    previous_current = {"model_id", "agent_workbench"}
    if set(value) == previous_current and all(
        isinstance(value.get(name), str) and value[name].strip() for name in previous_current
    ):
        # This was the canonical shape before LDVH's three-field signature.
        # It remains a strictly read-only historical shape.
        return
    _, problems = parse_signature(value)
    for problem in problems:
        issues.append(FactIssue("schema", problem, path))


def _validate_change_log(fields: dict[str, Any], issues: list[FactIssue]) -> None:
    change_log = fields.get("change_log")
    if not isinstance(change_log, list):
        return
    created = parse_rfc3339(fields.get("created_at"))
    updated = parse_rfc3339(fields.get("updated_at"))
    previous: RFC3339Instant | None = None
    for index, entry in enumerate(change_log):
        if not isinstance(entry, dict):
            continue
        path = f"change_log[{index}]"
        _validate_change_log_signature(entry.get("signature"), f"{path}.signature", issues)
        session_id = entry.get("session_id")
        if isinstance(session_id, str) and _SESSION_PLACEHOLDER_RE.fullmatch(session_id.strip()):
            issues.append(
                FactIssue(
                    "schema",
                    "change_log.session_id 不得为占位符（如 current-session），必须是真实会话标识",
                    f"{path}.session_id",
                )
            )
        event_at = _time(entry.get("at"), f"{path}.at", issues)
        if event_at is not None:
            if created is not None and event_at < created:
                issues.append(FactIssue("schema", "change_log.at 不得早于 created_at", f"{path}.at"))
            if updated is not None and event_at > updated:
                issues.append(FactIssue("schema", "change_log.at 不得晚于 updated_at", f"{path}.at"))
            if previous is not None and event_at <= previous:
                issues.append(FactIssue("schema", "change_log.at 必须严格递增", f"{path}.at"))
            previous = event_at


def change_log_creation_issues(fields: Mapping[str, Any]) -> tuple[FactIssue, ...]:
    """Require a new fact to begin with exactly one attributable event.

    A creation is one event, not an opportunity to import multiple historical
    events.  The creation application binds that event's time to its own
    observed time before serializing the fact.
    """

    change_log = fields.get("change_log")
    if not isinstance(change_log, list) or len(change_log) != 1:
        return (FactIssue("schema", "新建事实对象必须包含首条 change_log 流水", "change_log"),)
    issues = [
        FactIssue("schema", "新建 change_log 不得使用已退役 signer_type", f"change_log[{index}].signature.signer_type")
        for index, entry in enumerate(change_log)
        if isinstance(entry, dict) and isinstance(entry.get("signature"), dict) and "signer_type" in entry["signature"]
    ]
    if isinstance(change_log[0], dict) and change_log[0].get("at") != fields.get("created_at"):
        issues.append(FactIssue("schema", "新建首条 change_log.at 必须等于 Code 绑定的 created_at", "change_log[0].at"))
    return tuple(issues)


def timestamp_initial_change_log(fields: dict[str, Any], event_at: str) -> None:
    """Bind a newly created object's sole initial log entry to Code's event time."""

    change_log = fields.get("change_log")
    if isinstance(change_log, list) and len(change_log) == 1 and isinstance(change_log[0], dict):
        change_log[0]["at"] = event_at


def timestamp_appended_change_log(fields: dict[str, Any], event_at: str) -> None:
    """Bind the proposed update's newest log entry to Code's observed time.

    A non-empty log binds its last entry.  This covers both a first real update
    (exactly one entry on a previously log-less object) and ordinary appends.
    Creation uses :func:`timestamp_initial_change_log` and never reaches here.
    """

    change_log = fields.get("change_log")
    if isinstance(change_log, list) and change_log and isinstance(change_log[-1], dict):
        change_log[-1]["at"] = event_at


def validate_change_log_transition(
    before: Mapping[str, Any],
    after: Mapping[str, Any],
    *,
    require_append: bool = True,
    allow_first_log: bool = False,
) -> tuple[FactIssue, ...]:
    """Require one appended event while allowing the one-time signer-type removal.

    A legacy object without history cannot acquire an invented history through
    a normal update.  The only path is an explicitly authorized first real
    update that establishes exactly one current three-field entry; the caller
    must have already verified the same-path HEAD baseline.
    """

    previous = before.get("change_log")
    current = after.get("change_log")
    if not isinstance(previous, list):
        if allow_first_log:
            return _first_log_issues(current, after)
        return (
            FactIssue(
                "schema",
                "缺少 change_log 历史的遗留对象不得经普通更新补写；必须使用受控迁移",
                "change_log",
            ),
        )
    if not isinstance(current, list) or len(current) != len(previous) + (1 if require_append else 0):
        return (FactIssue("schema", "受控更新必须保留既有 change_log 并追加一条流水", "change_log"),)
    normalized_history = [_without_legacy_change_log_signer_type(entry) for entry in previous]
    if current[: len(previous)] != normalized_history:
        return (FactIssue("schema", "change_log 历史条目不可改写或删除", "change_log"),)
    issues: list[FactIssue] = []
    for index, entry in enumerate(current[len(previous) :], start=len(previous)):
        if isinstance(entry, dict) and isinstance(entry.get("signature"), dict) and "signer_type" in entry["signature"]:
            issues.append(
                FactIssue(
                    "schema", "新增 change_log 不得使用已退役 signer_type", f"change_log[{index}].signature.signer_type"
                )
            )
        if "updated_at" in after and isinstance(entry, dict) and entry.get("at") != after.get("updated_at"):
            issues.append(
                FactIssue(
                    "schema",
                    "新增 change_log.at 必须等于本次 Code 绑定的 updated_at",
                    f"change_log[{index}].at",
                )
            )
    return tuple(issues)


def _first_log_issues(current: object, after: Mapping[str, Any]) -> tuple[FactIssue, ...]:
    """Validate an authorized first real update's single log entry.

    The after must contain exactly one entry whose signature is the current
    closed three-field set, with no ``session_id``, and whose ``at`` equals the
    Code-bound ``updated_at``.  Anything else means the first update invented
    history or fell back to a retired signature shape.
    """

    if not isinstance(current, list) or len(current) != 1:
        return (FactIssue("schema", "首次真实更新必须恰好建立一条 change_log 流水", "change_log"),)
    entry = current[0]
    if not isinstance(entry, dict):
        return (FactIssue("schema", "首次 change_log 条目必须是 object", "change_log[0]"),)
    signature = entry.get("signature")
    if not isinstance(signature, dict) or set(signature) != {
        "product_name",
        "model_name",
        "agent_runtime_name",
    }:
        return (FactIssue("schema", "首次 change_log 必须使用当前三字段署名", "change_log[0].signature"),)
    if "session_id" in entry:
        return (FactIssue("schema", "首次 change_log 不得携带 session_id", "change_log[0].session_id"),)
    if "updated_at" in after and entry.get("at") != after.get("updated_at"):
        return (FactIssue("schema", "新增 change_log.at 必须等于本次 Code 绑定的 updated_at", "change_log[0].at"),)
    return ()


def _without_legacy_change_log_signer_type(entry: object) -> object:
    """Project the narrowly authorized legacy signature-field migration.

    The migration removes only ``signature.signer_type``; all other historical
    content remains byte-for-value identical under the parsed object model.
    """

    if not isinstance(entry, dict) or not isinstance(entry.get("signature"), dict):
        return entry
    signature = entry["signature"]
    if "signer_type" not in signature:
        return entry
    return {**entry, "signature": {key: value for key, value in signature.items() if key != "signer_type"}}


def _require(fields: dict[str, Any], names: set[str] | frozenset[str], issues: list[FactIssue]) -> None:
    for name in sorted(names):
        if name not in fields:
            issues.append(FactIssue("schema", "当前状态要求该字段", name))


def _forbid(fields: dict[str, Any], names: set[str] | frozenset[str], issues: list[FactIssue]) -> None:
    for name in sorted(names):
        if name in fields:
            issues.append(FactIssue("schema", "当前状态禁止该字段", name))


def _validate_status(
    fact_type_key: str,
    fields: dict[str, Any],
    issues: list[FactIssue],
    *,
    allow_legacy_spark: bool = False,
) -> None:
    status = fields.get("status")
    layout = LAYOUTS[fact_type_key]
    legacy_spark = (
        fact_type_key == "spark"
        and allow_legacy_spark
        and is_legacy_spark_object(fields.get("object_id"))
        and status == "routed"
    )
    if not isinstance(status, str) or (status not in layout.statuses and not legacy_spark):
        issues.append(FactIssue("schema", f"status 必须属于 {sorted(layout.statuses)}", "status"))
        return
    if "priority" in fields and fields["priority"] not in {"P0", "P1", "P2", "P3"}:
        issues.append(FactIssue("schema", "priority 不在 P0、P1、P2、P3 闭集中", "priority"))
    if fact_type_key == "spark":
        if status == "open":
            _require(fields, {"priority"}, issues)
            _forbid(fields, {"disposition_summary"}, issues)
        elif legacy_spark:
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


def _validate_relations(
    fact_type_key: str,
    fields: dict[str, Any],
    issues: list[FactIssue],
    *,
    allow_legacy_spark: bool = False,
) -> None:
    relations = fields.get("relations")
    if not isinstance(relations, list):
        return
    allowed = LAYOUTS[fact_type_key].relation_keys
    if (
        fact_type_key == "spark"
        and allow_legacy_spark
        and is_legacy_spark_object(fields.get("object_id"))
        and fields.get("status") == "routed"
    ):
        allowed = allowed | {"routed-to"}
    for index, relation in enumerate(relations):
        if not isinstance(relation, dict):
            continue
        path = f"relations[{index}]"
        if relation.get("relation_key") not in allowed:
            issues.append(FactIssue("relation", "relation_key 不在当前类型闭集中", f"{path}.relation_key"))
        target = relation.get("target")
        if not isinstance(target, dict):
            continue
        target_keys = set(target)
        uid_shape = target_keys == {"object_uid"}
        legacy_shape = target_keys == {"governed_project_id", "fact_type_key", "object_id"}
        if not uid_shape and not legacy_shape:
            issues.append(
                FactIssue(
                    "relation",
                    "关系目标必须恰好使用 object_uid 或完整 legacy 三元组",
                    f"{path}.target",
                )
            )
        elif uid_shape and canonical_object_uid(target.get("object_uid")) is None:
            issues.append(
                FactIssue(
                    "identity",
                    "关系目标 object_uid 必须是 canonical 小写 UUIDv7",
                    f"{path}.target.object_uid",
                )
            )


STUDY_REPORT_KINDS = frozenset(
    {
        "external_research",
        "internal_audit",
        "technical_assessment",
        "comparison",
    }
)


def _nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validate_study(fields: dict[str, Any], issues: list[FactIssue]) -> None:
    report_kind = fields.get("report_kind")
    if report_kind is not None and report_kind not in STUDY_REPORT_KINDS:
        issues.append(FactIssue("schema", "Study report_kind 不在当前闭集中", "report_kind"))

    input_refs = fields.get("input_refs")
    if input_refs is not None:
        if not isinstance(input_refs, list):
            return
        for index, value in enumerate(input_refs):
            path = f"input_refs[{index}]"
            if not isinstance(value, dict):
                continue
            if not _nonempty_string(value.get("kind")):
                issues.append(FactIssue("reference", "Study input_refs.kind 必须是非空 string", f"{path}.kind"))
            if not _nonempty_string(value.get("locator")):
                issues.append(FactIssue("reference", "Study input_refs.locator 必须是非空 string", f"{path}.locator"))
            for name in ("version", "observed_at"):
                if name in value and not _nonempty_string(value[name]):
                    issues.append(
                        FactIssue("reference", f"Study input_refs.{name} 必须是非空 string", f"{path}.{name}")
                    )
            if (
                "observed_at" in value
                and _nonempty_string(value.get("observed_at"))
                and parse_rfc3339(value["observed_at"]) is None
            ):
                issues.append(
                    FactIssue("schema", "Study input_refs.observed_at 必须是有效 RFC 3339 时间", f"{path}.observed_at")
                )


def study_report_creation_issues(fields: dict[str, Any]) -> tuple[FactIssue, ...]:
    """Require new Study report metadata without invalidating legacy reads."""
    issues: list[FactIssue] = []
    report_kind = fields.get("report_kind")
    if report_kind not in STUDY_REPORT_KINDS:
        issues.append(FactIssue("schema", "新建 Study 必须提供合法 report_kind", "report_kind"))
    input_refs = fields.get("input_refs")
    urls = fields.get("urls")
    if report_kind == "external_research":
        if not isinstance(urls, list) or not urls:
            issues.append(FactIssue("reference", "external_research Study 必须至少包含一项 urls", "urls"))
    elif report_kind in {"internal_audit", "technical_assessment", "comparison"}:
        if not isinstance(input_refs, list) or not input_refs:
            issues.append(FactIssue("reference", f"{report_kind} Study 必须至少包含一项 input_refs", "input_refs"))
    return tuple(issues)


def validate_fact_object(
    fact_type_key: str,
    fields: dict[str, Any],
    schema: FactSchema,
    *,
    allow_legacy_spark: bool = False,
) -> tuple[FactIssue, ...]:
    issues: list[FactIssue] = []
    _validate_mapping(fields, _tree(schema), "", issues)
    issues[:] = [
        issue
        for issue in issues
        if not _is_legacy_change_log_signature_issue(fields, issue)
        and not _is_legacy_change_log_signer_type_issue(fields, issue)
    ]
    if fields.get("fact_type_key") != fact_type_key:
        issues.append(FactIssue("identity", "fact_type_key 与请求类型不一致", "fact_type_key"))
    if "object_uid" in fields and canonical_object_uid(fields.get("object_uid")) is None:
        issues.append(FactIssue("identity", "object_uid 必须是 canonical 小写 UUIDv7", "object_uid"))
    _validate_status(fact_type_key, fields, issues, allow_legacy_spark=allow_legacy_spark)
    if fact_type_key == "workcase":
        issues.extend(validate_workcase_snapshot(fields))
    elif fact_type_key == "study":
        _validate_study(fields, issues)
    _validate_times(fact_type_key, fields, issues)
    _validate_change_log(fields, issues)
    _validate_references(fact_type_key, fields, issues)
    _validate_relations(fact_type_key, fields, issues, allow_legacy_spark=allow_legacy_spark)
    return tuple(issues)


def _is_legacy_change_log_signer_type_issue(fields: Mapping[str, Any], issue: FactIssue) -> bool:
    """Let old records be read solely to complete the signer-type migration."""

    match = re.fullmatch(r"change_log\[(\d+)\]\.signature\.signer_type", issue.field_path or "")
    if match is None or issue.summary != "字段未在当前 Schema 登记":
        return False
    change_log = fields.get("change_log")
    index = int(match.group(1))
    if not isinstance(change_log, list) or index >= len(change_log) or not isinstance(change_log[index], dict):
        return False
    signature = change_log[index].get("signature")
    return (
        isinstance(signature, dict)
        and set(signature) == {"signer_type", "agent_id", "host_environment"}
        and signature.get("signer_type") in {"human", "ai-agent"}
        and all(
            isinstance(signature.get(name), str) and signature[name].strip()
            for name in ("agent_id", "host_environment")
        )
    )


def _is_legacy_change_log_signature_issue(fields: Mapping[str, Any], issue: FactIssue) -> bool:
    """Suppress schema unknown-field issues for the retained old shapes."""

    match = re.fullmatch(
        r"change_log\[(\d+)\](?:\.signature\.(agent_id|host_environment|model_id|host_name|agent_workbench|product_name|model_name|agent_runtime_name)|\.session_id)",
        issue.field_path or "",
    )
    if match is None or issue.summary not in {"字段未在当前 Schema 登记", "缺少必填字段"}:
        return False
    change_log = fields.get("change_log")
    index = int(match.group(1))
    if not isinstance(change_log, list) or index >= len(change_log) or not isinstance(change_log[index], dict):
        return False
    signature = change_log[index].get("signature")
    legacy_shapes = (
        frozenset({"agent_id", "host_environment"}),
        frozenset({"model_id", "host_name"}),
        frozenset({"model_id", "agent_workbench"}),
    )
    if not (
        isinstance(signature, dict)
        and set(signature) in legacy_shapes
        and all(isinstance(signature.get(name), str) and signature[name].strip() for name in signature)
    ):
        return False
    return (
        match.group(2) in {"agent_id", "host_environment", "model_id", "host_name", "agent_workbench", None}
        or issue.summary == "缺少必填字段"
    )


__all__ = [
    "STUDY_REPORT_KINDS",
    "change_log_creation_issues",
    "parse_rfc3339",
    "study_report_creation_issues",
    "timestamp_initial_change_log",
    "timestamp_appended_change_log",
    "validate_change_log_transition",
    "validate_fact_object",
]
