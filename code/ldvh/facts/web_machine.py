"""Closed JSON machine transport for the unmounted V4 Web bridge."""

from __future__ import annotations

import json
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import ldvh
from ldvh.facts.contracts import LAYOUTS
from ldvh.facts.creation import CreationBoundary
from ldvh.facts.schema import project_fact_schemas
from ldvh.facts.web_direct_capture import WebDirectCaptureResult, create_web_spark_direct_capture
from ldvh.facts.web_read_application import read_web_spark_detail, read_web_spark_list
from ldvh.governance.models import ObjectStatus, ScopeStatus, explicit_scope
from ldvh.governance.resolver import resolve_governance_scope
from ldvh.rule_source import inspect_colocated_rule_repository

PROTOCOL_VERSION = 1
MAX_REQUEST_BYTES = 12 * 1024 * 1024
MAX_RESPONSE_BYTES = 32 * 1024 * 1024
_ROOT_FIELDS = frozenset({"protocol_version", "operation", "scope", "arguments"})
_SCOPE_FIELDS = frozenset({"workspace_root", "worktree_locator", "expected_governed_project_id"})
_OPERATIONS = frozenset({"list-sparks", "read-spark", "create-spark"})


class MachineRequestError(ValueError):
    pass


class MachineUnavailableError(RuntimeError):
    pass


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
    return value


def _pairs_no_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise MachineRequestError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_nonfinite(value: str) -> object:
    raise MachineRequestError(f"non-finite JSON number is not allowed: {value}")


def _closed_mapping(value: object, fields: frozenset[str], name: str) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != fields:
        raise MachineRequestError(f"{name} fields must be exactly {sorted(fields)!r}")
    return value


def _non_empty_string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise MachineRequestError(f"{name} must be a non-empty string")
    return value


def _absolute_path(value: object, name: str) -> Path:
    text = _non_empty_string(value, name)
    path = Path(text)
    if not path.is_absolute():
        raise MachineRequestError(f"{name} must be an absolute path")
    return path


def _parse_request(raw: bytes) -> dict[str, object]:
    if not raw:
        raise MachineRequestError("request is empty")
    if len(raw) > MAX_REQUEST_BYTES:
        raise MachineRequestError("request exceeds the 12 MiB transport budget")
    if raw.startswith(b"\xef\xbb\xbf"):
        raise MachineRequestError("request must not contain a UTF-8 BOM")
    if raw != raw.strip():
        raise MachineRequestError("request must not contain framing whitespace")
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_pairs_no_duplicates,
            parse_constant=_reject_nonfinite,
        )
    except (UnicodeError, json.JSONDecodeError, MachineRequestError) as exc:
        raise MachineRequestError(f"request is not one unique UTF-8 JSON object: {exc}") from exc
    return _closed_mapping(value, _ROOT_FIELDS, "request")


def _request_parts(value: dict[str, object]) -> tuple[str, dict[str, object], dict[str, object]]:
    if value["protocol_version"] != PROTOCOL_VERSION:
        raise MachineRequestError("unsupported protocol_version")
    operation = _non_empty_string(value["operation"], "operation")
    if operation not in _OPERATIONS:
        raise MachineRequestError("operation is not supported")
    scope = _closed_mapping(value["scope"], _SCOPE_FIELDS, "scope")
    arguments = value["arguments"]
    if not isinstance(arguments, dict):
        raise MachineRequestError("arguments must be an object")
    return operation, scope, arguments


def _boundary(scope: dict[str, object]) -> tuple[CreationBoundary, dict[str, object]]:
    workspace_root = _absolute_path(scope["workspace_root"], "scope.workspace_root")
    locator = _absolute_path(scope["worktree_locator"], "scope.worktree_locator")
    expected_project = _non_empty_string(
        scope["expected_governed_project_id"],
        "scope.expected_governed_project_id",
    )
    run = resolve_governance_scope(
        explicit_scope((str(locator),)),
        base=locator.parent,
        explicit_workspace_root=workspace_root,
    )
    if (
        run.result is None
        or run.technical_non_completions
        or len(run.completed_scope) != 1
        or run.result.scope_status is not ScopeStatus.GOVERNED_SINGLE
        or len(run.result.object_resolutions) != 1
    ):
        raise MachineUnavailableError("scope did not resolve to one complete governed project boundary")
    resolution = run.result.object_resolutions[0]
    if (
        resolution.status is not ObjectStatus.GOVERNED
        or resolution.governed_project_id != expected_project
        or resolution.git_worktree_root is None
        or resolution.git_common_dir is None
    ):
        raise MachineRequestError("scope project identity does not match the expected governed project")
    boundary = CreationBoundary(
        expected_project,
        Path(resolution.git_worktree_root),
        Path(resolution.git_common_dir),
    )
    return boundary, run.result.to_json()


def _response(
    operation: str | None,
    status: str,
    *,
    result: object | None = None,
    error: str | None = None,
    completion_unknown: bool = False,
) -> dict[str, object]:
    return {
        "protocol_version": PROTOCOL_VERSION,
        "operation": operation,
        "status": status,
        "result": result,
        "error": error,
        "completion_unknown": completion_unknown,
    }


def _capture_json(value: WebDirectCaptureResult) -> dict[str, object]:
    return {
        "status": value.status,
        "code": value.code,
        "summary": value.summary,
        "actual_ref": _plain(value.actual_ref),
        "existing_ref": _plain(value.existing_ref),
        "canonical_path": value.canonical_path,
        "fact_object": _plain(value.fact_object),
        "details": list(value.details),
    }


def handle_machine_request(value: dict[str, object]) -> dict[str, object]:
    _closed_mapping(value, _ROOT_FIELDS, "request")
    operation, scope, arguments = _request_parts(value)
    boundary, governance = _boundary(scope)
    package_file = getattr(ldvh, "__file__", None)
    if not package_file:
        return _response(operation, "unavailable", error="the imported ldvh package has no filesystem identity")
    source = inspect_colocated_rule_repository(Path(package_file))
    if source.repository is None:
        return _response(operation, "unavailable", error=source.problem)
    schemas = project_fact_schemas(source.repository)
    if "spark" not in schemas:
        return _response(operation, "unavailable", error="the verified rule source has no Spark schema")

    if operation == "list-sparks":
        _closed_mapping(arguments, frozenset(), "arguments")
        listed = read_web_spark_list(boundary, schemas)
        result = {
            "status": listed.status,
            "items": list(listed.items),
            "object_problems": list(listed.object_problems),
            "structural_problems": list(listed.structural_problems),
            "governance_resolution": governance,
        }
        return _response(operation, listed.status, result=result)
    if operation == "read-spark":
        detail_arguments = _closed_mapping(arguments, frozenset({"object_id"}), "arguments")
        object_id = _non_empty_string(detail_arguments["object_id"], "arguments.object_id")
        if LAYOUTS["spark"].object_id_pattern.fullmatch(object_id) is None:
            raise MachineRequestError("arguments.object_id is not a canonical Spark identity")
        detail = read_web_spark_detail(boundary, schemas, object_id)
        result = {
            "status": detail.status,
            "item": detail.item,
            "problems": list(detail.problems),
            "coverage_status": detail.coverage_status,
            "governance_resolution": governance,
        }
        return _response(operation, detail.status, result=result)

    capture_arguments = _closed_mapping(
        arguments,
        frozenset({"title", "intent", "description", "priority"}),
        "arguments",
    )
    capture = create_web_spark_direct_capture(boundary, schemas, capture_arguments)
    return _response(operation, capture.status, result={**_capture_json(capture), "governance_resolution": governance})


def _encode_response(value: dict[str, object]) -> bytes:
    encoded = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8") + b"\n"
    if len(encoded) <= MAX_RESPONSE_BYTES:
        return encoded
    operation = value.get("operation") if isinstance(value.get("operation"), str) else None
    fallback = _response(
        operation,
        "error" if operation == "create-spark" else "unavailable",
        error="response exceeds the 32 MiB transport budget",
        completion_unknown=operation == "create-spark",
    )
    return json.dumps(fallback, ensure_ascii=False, separators=(",", ":")).encode("utf-8") + b"\n"


def _process_request_bytes(raw: bytes) -> bytes:
    operation: str | None = None
    try:
        request = _parse_request(raw)
        raw_operation = request.get("operation")
        operation = raw_operation if isinstance(raw_operation, str) else None
        response = handle_machine_request(request)
        return _encode_response(response)
    except MachineRequestError as exc:
        response = _response(operation, "invalid", error=str(exc))
    except MachineUnavailableError as exc:
        response = _response(operation, "unavailable", error=str(exc))
    except (Exception, MemoryError) as exc:  # machine boundary must always emit one closed response
        response = _response(
            operation,
            "error",
            error=f"internal machine failure: {type(exc).__name__}",
            completion_unknown=operation == "create-spark",
        )
    return _encode_response(response)


def main() -> int:
    raw = sys.stdin.buffer.read(MAX_REQUEST_BYTES + 1)
    sys.stdout.buffer.write(_process_request_bytes(raw))
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

__all__ = ["MachineRequestError", "MachineUnavailableError", "handle_machine_request", "main"]
