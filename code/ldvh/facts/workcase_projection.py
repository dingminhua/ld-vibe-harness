"""Canonical projections and structural predicates for the current WorkCase contract.

This module deliberately knows nothing about historical WorkCase shapes.  It
normalizes only the collection ordering that specification 21 declares
non-semantic.  Snapshot validity and lifecycle transitions are checked by the
dedicated validation and transition modules.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence

_PLAN_ITEM_FIELDS = (
    "item_id",
    "goal",
    "expected_result",
    "depends_on",
    "approach_summary",
    "template_keys",
    "template_deviation_summary",
)
_RESULT_ITEM_FIELDS = ("item_id", "status", "result_summary")
_RESULT_MEMBER_FIELDS = (
    "success_criterion_results",
    "result_summary",
    "controller_check_summary",
    "validation_summary",
)
_RESULT_CONTEXT_FIELDS = frozenset(
    {
        "result_version",
        *_RESULT_MEMBER_FIELDS,
        "result_reviews",
        "closure_proposal",
        "closure_outcome",
        "disposition_summary",
        "residual_responsibilities",
    }
)
_TERMINAL_ITEM_STATUSES = frozenset({"completed", "cancelled"})
_CRITERION_OUTCOMES = frozenset({"satisfied", "not_satisfied", "not_verified"})
_PRE_EXECUTION_STOP_PHASES = frozenset(
    {
        "plan_revising",
        "controller_checking",
        "independent_reviewing",
        "closure_preparing",
        "human_closure_confirming",
    }
)


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _nonblank_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _plain(value: object) -> object:
    if isinstance(value, Mapping):
        return {str(key): _plain(member) for key, member in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_plain(member) for member in value]
    return value


def _stable_unique(values: Sequence[object]) -> list[object]:
    by_value: dict[str, object] = {}
    for value in values:
        normalized = _plain(value)
        by_value.setdefault(_canonical_json(normalized), normalized)
    return [by_value[key] for key in sorted(by_value)]


def _selected(raw: Mapping[str, object], names: Sequence[str]) -> dict[str, object]:
    return {name: _plain(raw[name]) for name in names if name in raw}


def _sorted_objects(value: object, identity_key: str, fields: Sequence[str]) -> list[dict[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    selected = [_selected(member, fields) for member in value if isinstance(member, Mapping)]
    for member in selected:
        for key in ("depends_on", "template_keys"):
            raw = member.get(key)
            if isinstance(raw, Sequence) and not isinstance(raw, (str, bytes, bytearray)):
                member[key] = _stable_unique(raw)
    return sorted(
        selected,
        key=lambda member: (str(member.get(identity_key, "")), _canonical_json(member)),
    )


def canonical_plan_projection(fields: Mapping[str, object]) -> dict[str, object]:
    """Return the normalized current plan projection defined by specification 21."""

    projected = _selected(fields, ("goal", "scope"))
    if "success_criterion_definitions" in fields:
        projected["success_criterion_definitions"] = _sorted_objects(
            fields["success_criterion_definitions"],
            "criterion_id",
            ("criterion_id", "statement"),
        )
    if "work_items" in fields:
        projected["work_items"] = _sorted_objects(fields["work_items"], "item_id", _PLAN_ITEM_FIELDS)
    return projected


def canonical_result_projection(fields: Mapping[str, object]) -> dict[str, object]:
    """Return the normalized result members currently present in ``fields``.

    The function is intentionally usable while ``controller_checking`` holds a
    partial projection.  Call :func:`result_projection_complete` before treating
    the returned value as a complete review subject.
    """

    projected: dict[str, object] = {}
    if "work_items" in fields:
        projected["work_items"] = _sorted_objects(fields["work_items"], "item_id", _RESULT_ITEM_FIELDS)
    if "success_criterion_results" in fields:
        projected["success_criterion_results"] = _sorted_objects(
            fields["success_criterion_results"],
            "criterion_id",
            ("criterion_id", "outcome", "summary"),
        )
    projected.update(_selected(fields, ("result_summary", "controller_check_summary", "validation_summary")))
    return projected


def plan_delta(before: Mapping[str, object], after: Mapping[str, object]) -> bool:
    """Return whether the normalized plan projection changed structurally."""

    return canonical_plan_projection(before) != canonical_plan_projection(after)


def result_delta(before: Mapping[str, object], after: Mapping[str, object]) -> bool:
    """Return whether two *complete* normalized result projections differ.

    A partial controller checkpoint is not a ResultDelta comparison subject and
    is rejected instead of being silently compared as though it were complete.
    """

    if not result_projection_complete(before) or not result_projection_complete(after):
        raise ValueError("ResultDelta requires two complete canonical result projections")
    return canonical_result_projection(before) != canonical_result_projection(after)


def all_terminal(fields: Mapping[str, object]) -> bool:
    """Return whether the non-empty work-item set is entirely terminal."""

    items = fields.get("work_items")
    return bool(items) and isinstance(items, list) and all(
        isinstance(item, Mapping) and item.get("status") in _TERMINAL_ITEM_STATUSES for item in items
    )


def no_execution_facts(fields: Mapping[str, object]) -> bool:
    """Return the exact structural ``NoExec`` predicate from specification 21."""

    items = fields.get("work_items")
    if not items or not isinstance(items, list):
        return False
    for item in items:
        if not isinstance(item, Mapping) or item.get("status") != "pending":
            return False
        if any(name in item for name in ("current_summary", "resume_from", "blocking_summary", "result_summary")):
            return False
    return not any(name in fields for name in _RESULT_CONTEXT_FIELDS)


def pre_execution_stop_shape(fields: Mapping[str, object]) -> bool:
    """Return whether the snapshot has the sole approval-less result-chain shape."""

    if fields.get("phase") not in _PRE_EXECUTION_STOP_PHASES or "execution_approval" in fields:
        return False
    result_version = fields.get("result_version")
    if not isinstance(result_version, int) or isinstance(result_version, bool) or result_version <= 0:
        return False
    items = fields.get("work_items")
    return bool(items) and isinstance(items, list) and all(
        isinstance(item, Mapping)
        and item.get("status") == "cancelled"
        and _nonblank_string(item.get("result_summary"))
        and not any(name in item for name in ("current_summary", "resume_from", "blocking_summary"))
        for item in items
    )


def result_projection_complete(fields: Mapping[str, object]) -> bool:
    """Return whether every canonical result member is present and structurally complete."""

    if not all_terminal(fields):
        return False
    items = fields.get("work_items")
    assert isinstance(items, list)
    if any(
        not isinstance(item, Mapping)
        or not _nonblank_string(item.get("item_id"))
        or not _nonblank_string(item.get("result_summary"))
        for item in items
    ):
        return False

    definitions = fields.get("success_criterion_definitions")
    results = fields.get("success_criterion_results")
    if not isinstance(definitions, list) or not definitions or not isinstance(results, list) or not results:
        return False
    if any(
        not isinstance(member, Mapping)
        or member.get("outcome") not in _CRITERION_OUTCOMES
        or not _nonblank_string(member.get("summary"))
        for member in results
    ):
        return False
    definition_ids = [
        member.get("criterion_id") for member in definitions if isinstance(member, Mapping)
    ]
    result_ids = [member.get("criterion_id") for member in results if isinstance(member, Mapping)]
    if (
        len(definition_ids) != len(definitions)
        or len(result_ids) != len(results)
        or any(not _nonblank_string(value) for value in definition_ids)
        or any(not _nonblank_string(value) for value in result_ids)
        or len(set(definition_ids)) != len(definition_ids)
        or len(set(result_ids)) != len(result_ids)
        or set(definition_ids) != set(result_ids)
    ):
        return False
    return all(_nonblank_string(fields.get(name)) for name in _RESULT_MEMBER_FIELDS[1:])


__all__ = [
    "all_terminal",
    "canonical_plan_projection",
    "canonical_result_projection",
    "no_execution_facts",
    "plan_delta",
    "pre_execution_stop_shape",
    "result_delta",
    "result_projection_complete",
]
