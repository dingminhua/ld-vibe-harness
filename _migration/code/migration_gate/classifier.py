from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml


class MigrationGateError(ValueError):
    """Raised when a temporary migration candidate cannot be classified."""


REQUIRED_FIELDS = (
    "source_path",
    "source_kind",
    "candidate_role",
    "authority_source",
    "target_area",
    "why_needed",
)

STABLE_ROLE_TARGETS = {
    "parent_spec": "specs",
    "child_spec": "specs",
    "schema": "specs/schemas",
    "fixture": "tests/fixtures",
    "fact_object": "ldvh-base",
}


def load_candidate(path: str | Path) -> dict[str, Any]:
    candidate_path = Path(path)
    with candidate_path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle)
    if not isinstance(loaded, dict):
        raise MigrationGateError(f"{candidate_path}: expected mapping root")
    return loaded


def classify_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    diagnostics = _validate_candidate(candidate)
    if diagnostics:
        return _decision(candidate, "invalid", "", "; ".join(diagnostics), diagnostics, "fix_candidate")

    role = candidate["candidate_role"]
    if role == "derived_checklist":
        return _decision(
            candidate,
            "do_not_migrate",
            "",
            "derived checklist should be generated from specs, schemas, code, or tests",
            [],
            "encode_as_schema_code_or_test",
        )
    if role == "runtime_strategy":
        return _decision(
            candidate,
            "defer",
            "",
            "runtime, hook, and dispatcher strategy requires separate human confirmation",
            ["stop_before_runtime_or_hook_strategy_change"],
            "open_runtime_strategy_workcase",
        )
    if role == "reject":
        return _decision(
            candidate,
            "do_not_migrate",
            "",
            "candidate is explicitly rejected",
            [],
            "record_rejection_reason",
        )
    if role in STABLE_ROLE_TARGETS:
        expected_area = STABLE_ROLE_TARGETS[role]
        if candidate["target_area"] != expected_area:
            return _decision(
                candidate,
                "invalid",
                "",
                f"{role} must target {expected_area}",
                [f"target_area_mismatch:{candidate['target_area']}"],
                "fix_target_area",
            )
        if role == "child_spec" and not candidate.get("parent_ref"):
            return _decision(
                candidate,
                "invalid",
                "",
                "child_spec requires parent_ref",
                ["missing_parent_ref"],
                "add_parent_ref_or_reclassify",
            )
        target_path = candidate.get("proposed_target") or _default_target_path(candidate)
        return _decision(
            candidate,
            "migrate",
            target_path,
            f"{role} carries non-derived v3 material in {expected_area}",
            [],
            "migrate_with_source_refs",
        )

    return _decision(
        candidate,
        "invalid",
        "",
        f"unsupported candidate_role: {role}",
        ["unsupported_candidate_role"],
        "fix_candidate_role",
    )


def _validate_candidate(candidate: dict[str, Any]) -> list[str]:
    diagnostics: list[str] = []
    for field in REQUIRED_FIELDS:
        value = candidate.get(field)
        if not isinstance(value, str) or not value.strip():
            diagnostics.append(f"missing_or_empty:{field}")
    if candidate.get("candidate_role") == "schema" and candidate.get("source_kind") not in {"schema", "spec"}:
        diagnostics.append("schema_role_requires_schema_or_spec_source")
    if candidate.get("candidate_role") == "fixture" and candidate.get("source_kind") != "fixture":
        diagnostics.append("fixture_role_requires_fixture_source")
    return diagnostics


def _decision(
    candidate: dict[str, Any],
    decision: str,
    target_path: str,
    reason: str,
    stop_conditions: list[str],
    next_action: str,
) -> dict[str, Any]:
    source_path = str(candidate.get("source_path", ""))
    authority_source = str(candidate.get("authority_source", ""))
    source_refs = [ref for ref in (source_path, authority_source) if ref]
    return {
        "decision": decision,
        "role": str(candidate.get("candidate_role", "")),
        "source_path": source_path,
        "target_path": target_path,
        "reason": reason,
        "stop_conditions": stop_conditions,
        "next_action": next_action,
        "source_refs": source_refs,
        "diagnostics": stop_conditions if decision == "invalid" else [],
    }


def _default_target_path(candidate: dict[str, Any]) -> str:
    role = candidate["candidate_role"]
    source_path = candidate["source_path"]
    stem = Path(source_path).stem
    slug = _slug(stem)
    if role == "schema":
        suffix = "" if slug.endswith(".schema") else ".schema"
        return f"specs/schemas/{slug}{suffix}.yaml"
    if role == "fixture":
        return f"tests/fixtures/{slug}.yaml"
    if role == "fact_object":
        return f"ldvh-base/{slug}.yaml"
    return f"specs/{slug}.yaml"


def _slug(value: str) -> str:
    lowered = value.strip().lower()
    lowered = re.sub(r"[^a-z0-9._-]+", "-", lowered)
    lowered = re.sub(r"-+", "-", lowered).strip("-")
    return lowered or "candidate"
