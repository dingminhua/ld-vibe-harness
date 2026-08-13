"""Source-defined, environment-neutral bounded context recovery."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from ldvh.facts.contracts import ACTIVE_STATUSES
from ldvh.helper.responses import CONTRACT, EXIT_CODES

RECOVERY_CONTRACT = "ldvh-context-recovery/1"
GOVERNANCE_OPERATION = "resolve-governance-scope"
FACT_CANDIDATE_OPERATION = "find-fact-object-candidates"
FACT_READ_OPERATION = "read-fact-objects"

F1_PAGE_SIZE = 100
MAX_F1_PAGES = 8
MAX_F1_CARDS = 800
MAX_OPERATIONS = 10
RECOVERY_DEADLINE_SECONDS = 20.0
HELPER_TIMEOUT_SECONDS = 20.0
GOVERNED_PROJECTION_BUDGET_BYTES = 12_000
WORKSPACE_PROJECTION_BUDGET_BYTES = 4_000
_MAX_SUMMARY_ITEMS = 6

type JsonObject = dict[str, Any]


class ContextRecoveryError(ValueError):
    """The recovery runner could not faithfully form its projection."""


class RecoveryBudgetExceeded(ContextRecoveryError):
    """The frozen total recovery resource budget has been exhausted."""


def _absolute_path(value: str, field: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ContextRecoveryError(f"{field} must be a non-empty absolute path")
    path = Path(value)
    if not path.is_absolute():
        raise ContextRecoveryError(f"{field} must be an absolute path")
    return path


def _executable_path(value: str, field: str) -> Path:
    path = _absolute_path(value, field)
    if not path.is_file():
        raise ContextRecoveryError(f"{field} does not identify a current file")
    if not os.access(path, os.X_OK):
        raise ContextRecoveryError(f"{field} is not executable")
    return path


def _directory_path(value: str, field: str) -> Path:
    path = _absolute_path(value, field)
    if not path.is_dir():
        raise ContextRecoveryError(f"{field} does not identify a current directory")
    return path


def _work_object_locator(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContextRecoveryError("work_object_locator must be a non-empty path string")
    return value


def _current_workcase_ref(value: Any) -> JsonObject | None:
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) != {
        "governed_project_id",
        "fact_type_key",
        "object_id",
    }:
        raise ContextRecoveryError("current_workcase_ref must be one exact stable fact reference")
    if value.get("fact_type_key") != "workcase":
        raise ContextRecoveryError("current_workcase_ref.fact_type_key must be workcase")
    if any(not isinstance(value.get(field), str) or not value[field] for field in value):
        raise ContextRecoveryError("current_workcase_ref fields must be non-empty strings")
    return {field: value[field] for field in ("governed_project_id", "fact_type_key", "object_id")}


def _validate_helper_response(value: Any, *, exit_code: int, operation_key: str) -> JsonObject:
    if not isinstance(value, dict):
        raise ContextRecoveryError("Helper response must be a JSON object")
    if value.get("contract") != CONTRACT:
        raise ContextRecoveryError(f"Helper response contract must be {CONTRACT}")
    if value.get("request_kind") != "call":
        raise ContextRecoveryError("Helper response request_kind must be call")
    if value.get("operation_key") != operation_key:
        raise ContextRecoveryError(f"Helper response operation_key must be {operation_key}")
    outcome = value.get("outcome")
    expected_exit_code = EXIT_CODES.get(outcome)
    if expected_exit_code is None:
        raise ContextRecoveryError("Helper response outcome is not supported by the current contract")
    if exit_code != expected_exit_code:
        raise ContextRecoveryError("Helper response outcome and process exit code do not match the current contract")
    return value


def _run_helper(
    helper_executable: Path,
    *,
    helper_cwd: Path,
    operation_key: str,
    request: JsonObject,
    timeout: float,
) -> tuple[int, JsonObject]:
    completed = subprocess.run(
        [str(helper_executable), "call", operation_key],
        cwd=helper_cwd,
        input=json.dumps(request, ensure_ascii=False),
        text=True,
        encoding="utf-8",
        errors="strict",
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    try:
        parsed_response = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise ContextRecoveryError("Helper did not return one JSON response") from error
    return completed.returncode, _validate_helper_response(
        parsed_response,
        exit_code=completed.returncode,
        operation_key=operation_key,
    )


def _objects(value: Any, field: str) -> list[JsonObject]:
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        raise ContextRecoveryError(f"{field} must be an array of objects")
    return value


def _source_locators(value: Any, *, limit: int = _MAX_SUMMARY_ITEMS) -> tuple[list[str], int]:
    if not isinstance(value, list):
        return [], 0
    locators = sorted(
        {
            item["locator"]
            for item in value
            if isinstance(item, dict) and isinstance(item.get("locator"), str) and item["locator"]
        }
    )
    return locators[:limit], max(0, len(locators) - limit)


def _summaries(value: Any) -> tuple[list[str], int]:
    if not isinstance(value, list):
        return [], 0
    summaries = [
        item["summary"]
        for item in value
        if isinstance(item, dict) and isinstance(item.get("summary"), str) and item["summary"]
    ]
    return summaries[:_MAX_SUMMARY_ITEMS], max(0, len(summaries) - _MAX_SUMMARY_ITEMS)


def _operation_summary(operation_key: str, response: JsonObject, *, page: int | None = None) -> JsonObject:
    scope = response.get("scope") if isinstance(response.get("scope"), dict) else {}
    sources, omitted_sources = _source_locators(response.get("sources"))
    gaps, omitted_gaps = _summaries(response.get("gaps"))
    diagnostics, omitted_diagnostics = _summaries(response.get("diagnostics"))
    summary: JsonObject = {
        "operation_key": operation_key,
        "outcome": response["outcome"],
        "completed_scope_count": len(scope.get("completed", [])) if isinstance(scope.get("completed"), list) else 0,
        "not_completed_scope_count": (
            len(scope.get("not_completed", [])) if isinstance(scope.get("not_completed"), list) else 0
        ),
    }
    if sources:
        summary["source_locators"] = sources
    if omitted_sources:
        summary["omitted_source_locator_count"] = omitted_sources
    if gaps:
        summary["gap_summaries"] = gaps
    if omitted_gaps:
        summary["omitted_gap_count"] = omitted_gaps
    if diagnostics:
        summary["diagnostic_summaries"] = diagnostics
    if omitted_diagnostics:
        summary["omitted_diagnostic_count"] = omitted_diagnostics
    if page is not None:
        summary["page"] = page
        result = response.get("result")
        coverage = result.get("coverage") if isinstance(result, dict) else None
        if isinstance(coverage, dict):
            summary["coverage"] = {
                key: coverage.get(key) for key in ("status", "total_matching", "returned", "offset")
            }
            summary["coverage"]["next_cursor_present"] = coverage.get("next_cursor") is not None
    return summary


def _same_real_path(left: Path, right: Path) -> bool:
    try:
        return left.resolve(strict=True) == right.resolve(strict=True)
    except OSError:
        return False


def _compact_registered_candidate(value: JsonObject) -> JsonObject:
    required = ("governed_project_id", "registered_project_path", "git_worktree_root", "git_common_dir")
    if any(not isinstance(value.get(field), str) or not value[field] for field in required):
        raise ContextRecoveryError("registered_project_candidates contains an invalid candidate")
    source_locators, omitted = _source_locators(value.get("source_refs"))
    if not source_locators:
        raise ContextRecoveryError("registered_project_candidates candidate lacks source references")
    return {
        **{field: value[field] for field in required},
        "source_locators": source_locators,
        "omitted_source_locator_count": omitted,
    }


def _project_binding(
    governance_response: JsonObject,
    *,
    workspace: Path,
    locator: str,
) -> tuple[JsonObject, str | None]:
    unresolved: JsonObject = {
        "status": "unresolved",
        "reason": "governance_unavailable",
        "project": None,
        "candidates": [],
    }
    if governance_response["outcome"] != "ok":
        return unresolved, None
    result = governance_response.get("result")
    if not isinstance(result, dict):
        raise ContextRecoveryError("successful governance response must contain a result object")
    raw_candidates = _objects(result.get("registered_project_candidates"), "registered_project_candidates")
    candidates = [_compact_registered_candidate(item) for item in raw_candidates]
    unresolved["candidates"] = candidates
    scope_status = result.get("scope_status")
    resolutions = _objects(result.get("object_resolutions"), "object_resolutions")
    if scope_status == "governed_single" and resolutions:
        governed = [item for item in resolutions if item.get("status") == "governed"]
        project_ids = {item.get("governed_project_id") for item in governed}
        if len(governed) != len(resolutions) or len(project_ids) != 1:
            raise ContextRecoveryError("governed_single response does not contain one governed project")
        resolution = governed[0]
        required = ("governed_project_id", "registered_project_path", "git_worktree_root", "git_common_dir")
        if any(not isinstance(resolution.get(field), str) or not resolution[field] for field in required):
            raise ContextRecoveryError("governed resolution lacks its actual project identity")
        source_locators, omitted = _source_locators(resolution.get("source_refs"))
        project = {
            **{field: resolution[field] for field in required},
            "source_locators": source_locators,
            "omitted_source_locator_count": omitted,
        }
        return {
            "status": "bound",
            "reason": "governed_single",
            "project": project,
            "candidates": candidates,
        }, resolution["git_worktree_root"]

    if (
        result.get("config_status") == "valid"
        and scope_status == "non_governed"
        and len(resolutions) == 1
        and resolutions[0].get("status") == "not_governed"
        and len(candidates) == 1
        and Path(locator).is_absolute()
        and _same_real_path(workspace, Path(locator))
    ):
        return {
            "status": "bound",
            "reason": "sole_registered_project_candidate",
            "project": {
                "governed_project_id": candidates[0]["governed_project_id"],
                "git_worktree_root": candidates[0]["git_worktree_root"],
            },
            "candidates": candidates,
        }, candidates[0]["git_worktree_root"]

    unresolved["reason"] = {
        "non_governed": "registered_project_choice_unresolved",
        "multiple_governed_projects": "multiple_governed_projects",
        "scope_unknown": "governance_unknown",
        "mixed_scope": "mixed_scope",
    }.get(scope_status, "governance_unresolved")
    return unresolved, None


def _fact_ref(value: Any, field: str) -> JsonObject:
    if not isinstance(value, dict):
        raise ContextRecoveryError(f"{field} must be a fact reference")
    if set(value) == {"object_uid"}:
        from ldvh.facts.identity import canonical_object_uid

        object_uid = canonical_object_uid(value.get("object_uid"))
        if object_uid is None:
            raise ContextRecoveryError(f"{field}.object_uid must be a canonical lowercase UUIDv7")
        return {"object_uid": object_uid}
    required = ("governed_project_id", "fact_type_key", "object_id")
    if set(value) != set(required) or any(not isinstance(value.get(key), str) or not value[key] for key in required):
        raise ContextRecoveryError(f"{field} must be one exact stable fact reference")
    return {key: value[key] for key in required}


def _ref_key(value: JsonObject) -> tuple[str, ...]:
    if "object_uid" in value:
        return ("uid", value["object_uid"])
    return ("legacy", value["governed_project_id"], value["fact_type_key"], value["object_id"])


def _compact_card(value: JsonObject) -> JsonObject:
    ref = _fact_ref(value.get("fact_ref"), "cards[].fact_ref")
    if (
        value.get("card_layer") != "F1"
        or not isinstance(value.get("fields"), dict)
        or value.get("excerpts") != []
    ):
        raise ContextRecoveryError("F1 response contains an invalid card")
    object_id = value["fields"].get("object_id")
    fact_type_key = (
        "adr" if isinstance(object_id, str) and object_id.startswith("adr-")
        else "workcase" if isinstance(object_id, str) and object_id.startswith("workcase-")
        else None
    )
    if fact_type_key not in {"adr", "workcase"}:
        raise ContextRecoveryError("F1 response contains a type outside the recovery baseline")
    if fact_type_key == "workcase" and value["fields"].get("status") not in ACTIVE_STATUSES:
        raise ContextRecoveryError("F1 response contains a terminal WorkCase")
    source_locators, omitted = _source_locators(value.get("source_refs"), limit=3)
    return {
        "fact_ref": ref,
        "fact_type_key": fact_type_key,
        "fields": value["fields"],
        "source_locators": source_locators,
        "omitted_source_locator_count": omitted,
    }


def _fact_request(
    *,
    workspace: Path,
    fact_locator: str,
    project_id: str,
    current_ref: JsonObject | None,
    cursor: str | None,
) -> JsonObject:
    arguments: JsonObject = {
        "workspace_root": str(workspace),
        "governed_project_id": project_id,
        "card_layer": "F1",
        "page_size": F1_PAGE_SIZE,
    }
    if current_ref is not None:
        arguments["current_workcase_ref"] = current_ref
    if cursor is not None:
        arguments["cursor"] = cursor
    return {
        "work_object_locators": [fact_locator],
        "arguments": arguments,
        "response_profile": "compact",
    }


def _read_request(*, workspace: Path, fact_locator: str, fact_ref: JsonObject) -> JsonObject:
    return {
        "work_object_locators": [fact_locator],
        "arguments": {"workspace_root": str(workspace), "fact_refs": [fact_ref]},
        "response_profile": "compact",
    }


def _expand_entry(operation_key: str, request: JsonObject) -> JsonObject:
    return {"operation_key": operation_key, "request": request}


def _workcase_projection(response: JsonObject, expected_ref: JsonObject) -> tuple[JsonObject, list[JsonObject]]:
    if response["outcome"] != "ok":
        raise ContextRecoveryError("expanded WorkCase read did not complete")
    result = response.get("result")
    items = _objects(result.get("items") if isinstance(result, dict) else None, "read result items")
    if len(items) != 1:
        raise ContextRecoveryError("expanded WorkCase read must return exactly one item")
    item = items[0]
    if item.get("check_status") != "mechanically_valid" or not isinstance(item.get("fact_object"), dict):
        raise ContextRecoveryError("expanded WorkCase is not mechanically valid")
    if _fact_ref(item.get("requested_ref"), "read item requested_ref") != expected_ref:
        raise ContextRecoveryError("expanded WorkCase reference does not match the requested reference")
    fact_object = item["fact_object"]
    workcase: JsonObject = {"fact_ref": expected_ref}
    termination_mode = "termination" in fact_object
    projected_fields = (
        ("status", "phase", "waiting_on", "blocking_summary")
        if termination_mode
        else ("status", "phase", "summary", "resume_from", "waiting_on")
    )
    for field in projected_fields:
        if field in fact_object:
            workcase[field] = fact_object[field]
    if "termination" in fact_object:
        workcase["termination"] = fact_object["termination"]
    current_projection = item.get("current_snapshot_projection")
    if isinstance(current_projection, dict):
        workcase["current_snapshot_projection"] = current_projection
    raw_items = fact_object.get("work_items", [])
    if not isinstance(raw_items, list):
        raise ContextRecoveryError("expanded WorkCase work_items must be an array")
    if termination_mode:
        return workcase, []
    active: list[JsonObject] = []
    for raw_item in raw_items:
        if not isinstance(raw_item, dict) or raw_item.get("status") not in {"in_progress", "blocked"}:
            continue
        projected = {field: raw_item[field] for field in ("item_id", "status", "goal") if field in raw_item}
        if set(projected) != {"item_id", "status", "goal"}:
            raise ContextRecoveryError("active WorkCase item lacks a required field")
        for field in ("current_summary", "resume_from", "blocking_summary"):
            if field in raw_item:
                projected[field] = raw_item[field]
        evidence = raw_item.get("evidence_refs")
        if isinstance(evidence, list):
            projected["evidence_locators"] = [
                ref["locator"]
                for ref in evidence
                if isinstance(ref, dict) and isinstance(ref.get("locator"), str) and ref["locator"]
            ]
        active.append(projected)
    active.sort(key=lambda value: value["item_id"])
    return workcase, active


def _projection_size(value: JsonObject) -> int:
    return len(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def _bounded_summary(value: str, *, byte_limit: int = 160) -> str:
    encoded = value.encode("utf-8")
    if len(encoded) <= byte_limit:
        return value
    suffix = "..."
    prefix = encoded[: byte_limit - len(suffix)]
    while True:
        try:
            return prefix.decode("utf-8") + suffix
        except UnicodeDecodeError:
            prefix = prefix[:-1]


def _hard_budget_fallback(projection: JsonObject, budget: int) -> None:
    delivery = projection["delivery_coverage"]
    project_counts = delivery["project_candidates"]
    card_counts = delivery["required_f1_cards"]
    original_project_binding = projection["project_binding"]
    project_bound = original_project_binding.get("status") == "bound"
    minimal_operations: list[JsonObject] = []
    for operation in projection["operations"]:
        minimal: JsonObject = {
            key: operation[key]
            for key in (
                "operation_key",
                "outcome",
                "completed_scope_count",
                "not_completed_scope_count",
                "page",
                "coverage",
            )
            if key in operation
        }
        for field in ("source_locators", "gap_summaries", "diagnostic_summaries"):
            values = operation.get(field)
            if isinstance(values, list) and values:
                minimal[field] = [values[0] if field == "source_locators" else _bounded_summary(values[0])]
        for field in ("omitted_source_locator_count", "omitted_gap_count", "omitted_diagnostic_count"):
            if field in operation:
                minimal[field] = operation[field]
        minimal_operations.append(minimal)

    minimal_project: JsonObject | None = None
    if project_bound and isinstance(original_project_binding.get("project"), dict):
        minimal_project = original_project_binding["project"]
    replacement: JsonObject = {
        "contract": projection["contract"],
        "project_binding": {
            "status": "bound" if minimal_project is not None else "unresolved",
            "reason": (
                original_project_binding.get("reason", "governed_single")
                if minimal_project is not None
                else "candidate_delivery_incomplete"
            ),
            "project": minimal_project,
            "candidates": [],
        },
        "workcase_binding": {
            "status": "unresolved",
            "reason": "delivery_incomplete" if minimal_project is not None else "project_delivery_incomplete",
            "selected_ref": None,
            "candidates": [],
        },
        "delivery_coverage": {
            "status": "incomplete",
            "project_candidates": {
                "total": project_counts["total"],
                "delivered": 0,
                "omitted": project_counts["total"],
            },
            "required_f1_cards": {
                "total": card_counts["total"],
                "delivered": 0,
                "omitted": card_counts["total"],
            },
        },
        "operations": minimal_operations,
        "adr_cards": [],
        "active_items": [],
        "expand": projection["expand"],
        "diagnostics": [
            {"code": "delivery_budget_exceeded", "summary": "Recovery projection used its hard byte-budget fallback"}
        ],
    }
    projection.clear()
    projection.update(replacement)
    if _projection_size(projection) <= budget:
        return

    if projection["project_binding"]["status"] == "bound":
        projection["project_binding"].update(
            {"status": "unresolved", "reason": "candidate_delivery_incomplete", "project": None}
        )
        projection["workcase_binding"]["reason"] = "project_delivery_incomplete"
    while len(projection["expand"]) > 1 and _projection_size(projection) > budget:
        projection["expand"].pop()
    if _projection_size(projection) > budget:
        raise ContextRecoveryError("Required recovery projection exceeds the hard byte budget")


def _fit_delivery_budget(projection: JsonObject, budget: int) -> None:
    delivery = projection["delivery_coverage"]
    project_candidates = projection["project_binding"]["candidates"]
    workcase_candidates = projection["workcase_binding"]["candidates"]
    adr_cards = projection["adr_cards"]
    delivery["project_candidates"] = {
        "total": len(project_candidates),
        "delivered": len(project_candidates),
        "omitted": 0,
    }
    required_total = len(workcase_candidates) + len(adr_cards)
    delivery["required_f1_cards"] = {
        "total": required_total,
        "delivered": required_total,
        "omitted": 0,
    }
    if _projection_size(projection) <= budget:
        return

    if required_total:
        delivery["status"] = "incomplete"
        projection["workcase_binding"].update(
            {"status": "unresolved", "reason": "delivery_incomplete", "selected_ref": None}
        )
        projection.pop("workcase", None)
        projection["active_items"] = []
        projection["expand"] = [
            item for item in projection["expand"] if item.get("operation_key") != FACT_READ_OPERATION
        ]
        if projection["project_binding"]["status"] == "bound" and len(projection["expand"]) > 1:
            projection["expand"] = [
                item for item in projection["expand"] if item.get("operation_key") != GOVERNANCE_OPERATION
            ]
        while (workcase_candidates or adr_cards) and _projection_size(projection) > budget:
            (workcase_candidates if workcase_candidates else adr_cards).pop()
        delivered = len(workcase_candidates) + len(adr_cards)
        delivery["required_f1_cards"] = {
            "total": required_total,
            "delivered": delivered,
            "omitted": required_total - delivered,
        }

    if _projection_size(projection) > budget:
        for operation in projection["operations"]:
            if "source_locators" in operation:
                operation["source_locators"] = operation["source_locators"][:1]
            if "gap_summaries" in operation:
                operation["gap_summaries"] = operation["gap_summaries"][:1]
            if "diagnostic_summaries" in operation:
                operation["diagnostic_summaries"] = operation["diagnostic_summaries"][:1]

    if _projection_size(projection) > budget and project_candidates:
        candidate_total = delivery["project_candidates"]["total"]
        delivery["status"] = "incomplete"
        projection["project_binding"].update(
            {"status": "unresolved", "reason": "candidate_delivery_incomplete", "project": None}
        )
        projection["workcase_binding"].update(
            {"status": "unresolved", "reason": "project_delivery_incomplete", "selected_ref": None}
        )
        projection.pop("workcase", None)
        projection["active_items"] = []
        while project_candidates and _projection_size(projection) > budget:
            project_candidates.pop()
        delivery["project_candidates"] = {
            "total": candidate_total,
            "delivered": len(project_candidates),
            "omitted": candidate_total - len(project_candidates),
        }

    if _projection_size(projection) > budget:
        _hard_budget_fallback(projection, budget)


def recover_context(
    *,
    helper_executable: str,
    workspace_root: str,
    work_object_locator: str,
    helper_cwd: str,
    current_workcase_ref: JsonObject | None = None,
) -> JsonObject:
    helper = _executable_path(helper_executable, "helper_executable")
    workspace = _directory_path(workspace_root, "workspace_root")
    locator = _work_object_locator(work_object_locator)
    cwd = _directory_path(helper_cwd, "helper_cwd")
    current_ref = _current_workcase_ref(current_workcase_ref)
    deadline = time.monotonic() + RECOVERY_DEADLINE_SECONDS
    operation_count = 0
    operations: list[JsonObject] = []
    diagnostics: list[JsonObject] = []

    def call(operation_key: str, request: JsonObject, *, page: int | None = None) -> JsonObject:
        nonlocal operation_count
        remaining = deadline - time.monotonic()
        if remaining <= 0 or operation_count >= MAX_OPERATIONS:
            raise RecoveryBudgetExceeded("recovery resource budget exceeded")
        operation_count += 1
        try:
            _, response = _run_helper(
                helper,
                helper_cwd=cwd,
                operation_key=operation_key,
                request=request,
                timeout=max(0.001, min(HELPER_TIMEOUT_SECONDS, remaining)),
            )
        except subprocess.TimeoutExpired as error:
            raise RecoveryBudgetExceeded("recovery deadline expired during a Helper operation") from error
        operations.append(_operation_summary(operation_key, response, page=page))
        return response

    governance_request = {
        "work_object_locators": [locator],
        "arguments": {"workspace_root": str(workspace)},
        "response_profile": "compact",
    }
    try:
        governance_response = call(GOVERNANCE_OPERATION, governance_request)
    except RecoveryBudgetExceeded as error:
        projection = {
            "contract": RECOVERY_CONTRACT,
            "project_binding": {
                "status": "unresolved",
                "reason": "resource_budget_exceeded",
                "project": None,
                "candidates": [],
            },
            "workcase_binding": {
                "status": "unresolved",
                "reason": "project_unresolved",
                "selected_ref": None,
                "helper_coverage": {"status": "not_started", "pages_read": 0, "total_matching": None},
                "candidates": [],
            },
            "delivery_coverage": {"status": "incomplete"},
            "operations": operations,
            "adr_cards": [],
            "active_items": [],
            "expand": [_expand_entry(GOVERNANCE_OPERATION, governance_request)],
            "diagnostics": [{"code": "resource_budget_exceeded", "summary": str(error)}],
        }
        _fit_delivery_budget(projection, WORKSPACE_PROJECTION_BUDGET_BYTES)
        projection["delivery_coverage"]["status"] = "incomplete"
        return projection
    project_binding, fact_locator = _project_binding(governance_response, workspace=workspace, locator=locator)
    projection: JsonObject = {
        "contract": RECOVERY_CONTRACT,
        "project_binding": project_binding,
        "workcase_binding": {
            "status": "unresolved",
            "reason": "project_unresolved",
            "selected_ref": None,
            "helper_coverage": {"status": "not_started", "pages_read": 0, "total_matching": None},
            "candidates": [],
        },
        "delivery_coverage": {"status": "complete"},
        "operations": operations,
        "adr_cards": [],
        "active_items": [],
        "expand": [_expand_entry(GOVERNANCE_OPERATION, governance_request)],
        "diagnostics": diagnostics,
    }
    if fact_locator is None:
        _fit_delivery_budget(projection, WORKSPACE_PROJECTION_BUDGET_BYTES)
        return projection

    project = project_binding["project"]
    project_id = project["governed_project_id"]
    if current_ref is not None and current_ref["governed_project_id"] != project_id:
        projection["workcase_binding"]["reason"] = "current_workcase_ref_project_mismatch"
        projection["diagnostics"].append(
            {
                "code": "current_workcase_ref_project_mismatch",
                "summary": "Exact WorkCase ref belongs to another project",
            }
        )
        _fit_delivery_budget(projection, GOVERNED_PROJECTION_BUDGET_BYTES)
        return projection

    cards: list[JsonObject] = []
    seen_refs: set[tuple[str, str, str]] = set()
    seen_cursors: set[str] = set()
    cursor: str | None = None
    expected_manifest: tuple[Any, ...] | None = None
    expected_total: int | None = None
    coverage_complete = True
    pages_read = 0
    try:
        for page in range(1, MAX_F1_PAGES + 1):
            request = _fact_request(
                workspace=workspace,
                fact_locator=fact_locator,
                project_id=project_id,
                current_ref=current_ref,
                cursor=cursor,
            )
            response = call(FACT_CANDIDATE_OPERATION, request, page=page)
            pages_read = page
            if response["outcome"] != "ok":
                coverage_complete = False
                break
            result = response.get("result")
            if not isinstance(result, dict):
                raise ContextRecoveryError("successful F1 response must contain a result object")
            manifest = result.get("recovery_manifest")
            coverage = result.get("coverage")
            page_cards = _objects(result.get("cards"), "F1 cards")
            if not isinstance(manifest, dict) or not isinstance(coverage, dict):
                raise ContextRecoveryError("successful F1 response lacks manifest or coverage")
            current_manifest = (
                manifest.get("governed_project_id"),
                manifest.get("git_worktree_root"),
                manifest.get("git_common_dir"),
                manifest.get("schema_fingerprint"),
                manifest.get("object_set_fingerprint"),
                manifest.get("current_workcase_ref"),
            )
            if current_manifest[0] != project_id or current_manifest[-1] != current_ref:
                raise ContextRecoveryError("F1 manifest does not match the recovery query")
            if expected_manifest is None:
                expected_manifest = current_manifest
            elif current_manifest != expected_manifest:
                raise ContextRecoveryError("F1 manifest changed between pages")
            total = coverage.get("total_matching")
            offset = coverage.get("offset")
            returned = coverage.get("returned")
            if (
                coverage.get("status") != "complete"
                or not isinstance(total, int)
                or isinstance(total, bool)
                or not isinstance(offset, int)
                or isinstance(offset, bool)
                or not isinstance(returned, int)
                or isinstance(returned, bool)
                or offset != len(cards)
                or returned != len(page_cards)
                or coverage.get("object_set_fingerprint") != manifest.get("object_set_fingerprint")
            ):
                coverage_complete = False
                break
            if expected_total is None:
                expected_total = total
            elif total != expected_total:
                raise ContextRecoveryError("F1 total_matching changed between pages")
            for raw_card in page_cards:
                card = _compact_card(raw_card)
                key = _ref_key(card["fact_ref"])
                if key in seen_refs:
                    raise ContextRecoveryError("F1 pages contain a duplicate fact reference")
                seen_refs.add(key)
                cards.append(card)
            if len(cards) > MAX_F1_CARDS:
                raise RecoveryBudgetExceeded("F1 object budget exceeded")
            next_cursor = coverage.get("next_cursor")
            if next_cursor is None:
                if len(cards) != total:
                    coverage_complete = False
                cursor = None
                break
            if not isinstance(next_cursor, str) or not next_cursor or next_cursor in seen_cursors:
                raise ContextRecoveryError("F1 pagination returned an invalid or repeated cursor")
            seen_cursors.add(next_cursor)
            cursor = next_cursor
        else:
            if cursor is not None:
                raise RecoveryBudgetExceeded("F1 page budget exceeded")
    except RecoveryBudgetExceeded as error:
        coverage_complete = False
        diagnostics.append({"code": "resource_budget_exceeded", "summary": str(error)})

    workcase_cards = [
        {key: value for key, value in card.items() if key != "fact_type_key"}
        for card in cards
        if card["fact_type_key"] == "workcase"
    ]
    adr_cards = [
        {key: value for key, value in card.items() if key != "fact_type_key"}
        for card in cards
        if card["fact_type_key"] == "adr"
    ]
    projection["adr_cards"] = adr_cards
    projection["workcase_binding"].update(
        {
            "reason": "coverage_incomplete" if not coverage_complete else "no_mechanical_candidate",
            "helper_coverage": {
                "status": "complete" if coverage_complete else "incomplete",
                "pages_read": pages_read,
                "total_matching": expected_total,
            },
            "candidates": workcase_cards,
        }
    )
    projection["expand"].append(
        _expand_entry(
            FACT_CANDIDATE_OPERATION,
            _fact_request(
                workspace=workspace,
                fact_locator=fact_locator,
                project_id=project_id,
                current_ref=current_ref,
                cursor=None,
            ),
        )
    )
    if not coverage_complete:
        _fit_delivery_budget(projection, GOVERNED_PROJECTION_BUDGET_BYTES)
        projection["delivery_coverage"]["status"] = "incomplete"
        return projection

    candidate_refs = {_ref_key(card["fact_ref"]): card["fact_ref"] for card in workcase_cards}
    selected_ref: JsonObject | None = None
    if current_ref is not None:
        if _ref_key(current_ref) in candidate_refs:
            selected_ref = current_ref
            projection["workcase_binding"].update(
                {"status": "bound", "reason": "exact_current_workcase_ref", "selected_ref": current_ref}
            )
        else:
            projection["workcase_binding"]["reason"] = "exact_ref_not_in_complete_candidates"
    elif len(workcase_cards) == 1:
        selected_ref = workcase_cards[0]["fact_ref"]
        projection["workcase_binding"].update(
            {"reason": "sole_mechanical_candidate", "selected_ref": selected_ref}
        )
    elif len(workcase_cards) > 1:
        projection["workcase_binding"]["reason"] = "multiple_mechanical_candidates"

    if selected_ref is not None:
        read_request = _read_request(workspace=workspace, fact_locator=fact_locator, fact_ref=selected_ref)
        try:
            read_response = call(FACT_READ_OPERATION, read_request)
        except RecoveryBudgetExceeded as error:
            diagnostics.append({"code": "resource_budget_exceeded", "summary": str(error)})
            projection["workcase_binding"].update(
                {"status": "unresolved", "reason": "read_budget_exceeded", "selected_ref": None}
            )
        else:
            projection["expand"].append(_expand_entry(FACT_READ_OPERATION, read_request))
            if read_response["outcome"] == "ok":
                workcase, active_items = _workcase_projection(read_response, selected_ref)
                projection["workcase"] = workcase
                projection["active_items"] = active_items
            else:
                projection["workcase_binding"].update(
                    {"status": "unresolved", "reason": "workcase_read_incomplete", "selected_ref": None}
                )

    budget = (
        WORKSPACE_PROJECTION_BUDGET_BYTES
        if Path(locator).is_absolute() and _same_real_path(workspace, Path(locator))
        else GOVERNED_PROJECTION_BUDGET_BYTES
    )
    _fit_delivery_budget(projection, budget)
    return projection


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run source-defined LDVH context recovery")
    parser.add_argument("--helper-executable", required=True)
    parser.add_argument("--workspace-root", required=True)
    parser.add_argument("--work-object-locator", required=True)
    parser.add_argument("--helper-cwd", required=True)
    parser.add_argument("--current-workcase-ref")
    return parser


def main(arguments: list[str] | None = None) -> int:
    parsed = _parser().parse_args(arguments)
    try:
        current_ref = json.loads(parsed.current_workcase_ref) if parsed.current_workcase_ref is not None else None
        projection = recover_context(
            helper_executable=parsed.helper_executable,
            workspace_root=parsed.workspace_root,
            work_object_locator=parsed.work_object_locator,
            helper_cwd=parsed.helper_cwd,
            current_workcase_ref=current_ref,
        )
    except (ContextRecoveryError, OSError, UnicodeError, json.JSONDecodeError, subprocess.SubprocessError) as error:
        sys.stderr.write(f"LDVH context recovery unavailable: {error}\n")
        return 1
    payload = json.dumps(projection, ensure_ascii=False, separators=(",", ":")) + "\n"
    sys.stdout.buffer.write(payload.encode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
