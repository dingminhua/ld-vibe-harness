from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


class ActionGuideError(ValueError):
    """Raised when a formatted source cannot be compiled deterministically."""


REQUIRED_SOURCE_FIELDS = ("kind", "id", "title", "status", "authority", "source_refs")
LIMITED_STATUSES = {"candidate", "deprecated", "archived"}


def load_formatted_source(path: str | Path) -> dict[str, Any]:
    source_path = Path(path)
    with source_path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle)
    if not isinstance(loaded, dict):
        raise ActionGuideError(f"{source_path}: expected a mapping at document root")
    return loaded


def compile_action_guide(source: dict[str, Any]) -> dict[str, Any]:
    _validate_source_shape(source)

    status = source["status"]
    authority = source["authority"]
    can_authorize = bool(authority["can_authorize_actions"])
    not_authorized = _authorization_blocks(source)

    guide = {
        "guide_type": "action_guide",
        "target": {
            "id": source["id"],
            "kind": source["kind"],
            "title": source["title"],
            "status": status,
            "authority_layer": authority["layer"],
            "can_authorize_actions": can_authorize,
        },
        "result_status": "limited" if not_authorized else "usable",
        "source_refs": list(source["source_refs"]),
        "relationships": list(source.get("relations") or []),
        "read_plan": _ordered_read_plan(source),
        "impact_judgment": list(source.get("impact_judgment") or []),
        "stop_conditions": _stop_conditions(source, not_authorized),
        "next_queries": list(source.get("next_queries") or []),
        "action_hints": list(source.get("action_hints") or []),
        "not_authorized": not_authorized,
    }
    return guide


def _validate_source_shape(source: dict[str, Any]) -> None:
    missing = [field for field in REQUIRED_SOURCE_FIELDS if field not in source]
    if missing:
        raise ActionGuideError(f"missing required fields: {', '.join(missing)}")

    authority = source["authority"]
    if not isinstance(authority, dict):
        raise ActionGuideError("authority must be a mapping")
    for field in ("layer", "can_authorize_actions"):
        if field not in authority:
            raise ActionGuideError(f"authority missing required field: {field}")

    source_refs = source["source_refs"]
    if not isinstance(source_refs, list) or not source_refs:
        raise ActionGuideError("source_refs must be a non-empty list")
    for index, ref in enumerate(source_refs, start=1):
        if not isinstance(ref, dict):
            raise ActionGuideError(f"source_refs[{index}] must be a mapping")
        if not ref.get("path") or not ref.get("role"):
            raise ActionGuideError(f"source_refs[{index}] requires path and role")


def _authorization_blocks(source: dict[str, Any]) -> list[dict[str, str]]:
    blocks: list[dict[str, str]] = []
    status = source["status"]
    if status in LIMITED_STATUSES:
        blocks.append(
            {
                "source": source["id"],
                "reason": f"target status is {status}; use only for inspection or migration review",
            }
        )
    if not bool(source["authority"]["can_authorize_actions"]):
        blocks.append(
            {
                "source": source["id"],
                "reason": "authority.can_authorize_actions is false",
            }
        )
    return blocks


def _ordered_read_plan(source: dict[str, Any]) -> list[dict[str, Any]]:
    read_plan = source.get("read_plan") or []
    if not isinstance(read_plan, list):
        raise ActionGuideError("read_plan must be a list when provided")
    return sorted(read_plan, key=lambda item: item.get("order", 0))


def _stop_conditions(
    source: dict[str, Any], not_authorized: list[dict[str, str]]
) -> list[str]:
    conditions = list(source.get("stop_conditions") or [])
    for block in not_authorized:
        conditions.append(block["reason"])
    return conditions
