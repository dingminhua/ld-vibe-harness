"""Single Code maintenance point for the common Helper response shape."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

CONTRACT = "ldvh-helper-cli/1"
EXIT_CODES = {
    "ok": 0,
    "no_change": 0,
    "partial": 3,
    "rejected": 4,
    "unavailable": 5,
    "invalid_request": 2,
    "error": 1,
}

RequestKind = Literal["capabilities", "call"]


@dataclass(frozen=True, slots=True)
class ServiceResult:
    response: dict[str, Any]
    exit_code: int


def source_reference(kind: str, locator: str, **details: Any) -> dict[str, Any]:
    result: dict[str, Any] = {"kind": kind, "locator": locator}
    if details:
        result["details"] = details
    return result


def gap(
    summary: str,
    *,
    scope: list[object] | None = None,
    sources: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "summary": summary,
        "scope": [] if scope is None else scope,
        "source_refs": [] if sources is None else sources,
    }


def diagnostic(summary: str, **details: Any) -> dict[str, Any]:
    return {"summary": summary, "details": details}


def common_response(
    *,
    request_kind: RequestKind,
    operation_key: str | None,
    outcome: str,
    summary: str,
    result: dict[str, Any] | None = None,
    requested_scope: list[object] | None = None,
    completed_scope: list[object] | None = None,
    not_completed_scope: list[object] | None = None,
    sources: list[dict[str, Any]] | None = None,
    gaps: list[dict[str, Any]] | None = None,
    diagnostics: list[dict[str, Any]] | None = None,
) -> ServiceResult:
    if outcome not in EXIT_CODES:
        raise ValueError(f"unsupported Helper outcome: {outcome}")
    response = {
        "contract": CONTRACT,
        "request_kind": request_kind,
        "operation_key": operation_key,
        "outcome": outcome,
        "summary": summary,
        "result": result,
        "scope": {
            "requested": [] if requested_scope is None else requested_scope,
            "completed": [] if completed_scope is None else completed_scope,
            "not_completed": [] if not_completed_scope is None else not_completed_scope,
            "governance_resolution": None,
        },
        "sources": [] if sources is None else sources,
        "disclosure": None,
        "gaps": [] if gaps is None else gaps,
        "changes": [],
        "verification": [],
        "diagnostics": [] if diagnostics is None else diagnostics,
        "follow_up": {
            "summary": "当前响应没有能够由 Helper 明确的专属后续信息",
            "required_inputs": [],
            "required_human_decisions": [],
            "resume_conditions": [],
            "suggested_operations": [],
        },
    }
    return ServiceResult(response=response, exit_code=EXIT_CODES[outcome])
