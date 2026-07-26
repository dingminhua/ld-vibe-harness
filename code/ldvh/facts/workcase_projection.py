"""Deterministic WorkCase review-subject projections.

The projections deliberately contain only the fields owned by the selected
review subject.  Reviews, approvals, lifecycle state and managed identity are
excluded by construction rather than filtered from a whole object snapshot.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence

PROJECTION_KEYS = frozenset({"plan_current", "result_implementation", "result_with_closure_report"})

_PLAN_ITEM_FIELDS = (
    "item_id",
    "goal",
    "expected_result",
    "depends_on",
    "approach_summary",
    "template_keys",
    "template_deviation_summary",
)
_RESULT_ITEM_FIELDS = (*_PLAN_ITEM_FIELDS, "status", "result_summary")


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _plain(value: object) -> object:
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_plain(item) for item in value]
    return value


def _sort_objects(value: object, identity_key: str) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    objects = [_normalize(item) for item in value if isinstance(item, dict)]
    return sorted(
        (item for item in objects if isinstance(item, dict)),
        key=lambda item: (str(item.get(identity_key, "")), _canonical_json(item)),
    )


def _normalize(value: object) -> object:
    """Normalize ordering that the WorkCase contract declares non-semantic."""

    if isinstance(value, Mapping):
        normalized: dict[str, object] = {}
        for key, item in value.items():
            if key in {"depends_on", "template_keys", "value_dimensions"} and isinstance(item, list):
                normalized[str(key)] = sorted((_normalize(member) for member in item), key=_canonical_json)
            else:
                normalized[str(key)] = _normalize(item)
        return normalized
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_normalize(item) for item in value]
    return value


def _selected(raw: Mapping[str, object], names: tuple[str, ...]) -> dict[str, object]:
    normalized_raw = _normalize(raw)
    assert isinstance(normalized_raw, dict)
    selected: dict[str, object] = {}
    for name in names:
        if name not in normalized_raw:
            continue
        selected[name] = normalized_raw[name]
    return selected


def _items(fields: Mapping[str, object], names: tuple[str, ...]) -> list[dict[str, object]]:
    raw_items = fields.get("work_items")
    if not isinstance(raw_items, list):
        return []
    selected = [_selected(item, names) for item in raw_items if isinstance(item, dict)]
    return sorted(selected, key=lambda item: (str(item.get("item_id", "")), _canonical_json(item)))


def project_workcase_subject(fields: Mapping[str, object], projection_key: str) -> dict[str, object]:
    """Return the canonical review subject selected by ``projection_key``.

    Unknown keys are programmer errors.  Mechanical fact validation is
    responsible for turning an unknown value in an object into a FactIssue.
    """

    if projection_key not in PROJECTION_KEYS:
        raise ValueError(f"unknown WorkCase projection key: {projection_key}")

    projected: dict[str, object] = _selected(fields, ("goal", "scope", "success_criterion_definitions"))
    if "success_criterion_definitions" in projected:
        projected["success_criterion_definitions"] = _sort_objects(
            projected["success_criterion_definitions"], "criterion_id"
        )
    projected["work_items"] = _items(
        fields,
        _PLAN_ITEM_FIELDS if projection_key == "plan_current" else _RESULT_ITEM_FIELDS,
    )
    if projection_key == "plan_current":
        return _plain(projected)  # type: ignore[return-value]

    projected.update(
        _selected(
            fields,
            (
                "success_criterion_results",
                "controller_check_summary",
                "improvement_observations",
            ),
        )
    )
    if "success_criterion_results" in projected:
        projected["success_criterion_results"] = _sort_objects(projected["success_criterion_results"], "criterion_id")
    if "improvement_observations" in projected:
        projected["improvement_observations"] = _sort_objects(projected["improvement_observations"], "observation_id")
    if projection_key == "result_implementation":
        return _plain(projected)  # type: ignore[return-value]

    projected.update(
        _selected(
            fields,
            (
                "validation_summary",
                "closure_outcome",
                "disposition_summary",
                "residual_responsibilities",
                "nonbinding_followups",
            ),
        )
    )
    if "residual_responsibilities" in projected:
        projected["residual_responsibilities"] = _sort_objects(projected["residual_responsibilities"], "residual_id")
    if "nonbinding_followups" in projected:
        projected["nonbinding_followups"] = _sort_objects(projected["nonbinding_followups"], "followup_id")
    return _plain(projected)  # type: ignore[return-value]


def workcase_subject_fingerprint(fields: Mapping[str, object], projection_key: str) -> str:
    """Return the SHA-256 of the selected compact canonical JSON projection."""

    encoded = _canonical_json(project_workcase_subject(fields, projection_key)).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


__all__ = ["PROJECTION_KEYS", "project_workcase_subject", "workcase_subject_fingerprint"]
