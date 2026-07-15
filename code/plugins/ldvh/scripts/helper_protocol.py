from __future__ import annotations

from typing import Any

from configuration import ConfigurationError

HELPER_CONTRACT = "ldvh-helper-cli/2"
HELPER_EXIT_CODES = {
    "ok": 0,
    "no_change": 0,
    "partial": 3,
    "rejected": 4,
    "unavailable": 5,
    "invalid_request": 2,
    "error": 1,
}


def validate_helper_response(
    value: Any,
    *,
    exit_code: int,
    request_kind: str,
    operation_key: str,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ConfigurationError("Helper response must be a JSON object")
    if value.get("contract") != HELPER_CONTRACT:
        raise ConfigurationError(f"Helper response contract must be {HELPER_CONTRACT}")
    if value.get("request_kind") != request_kind:
        raise ConfigurationError(f"Helper response request_kind must be {request_kind}")
    if value.get("operation_key") != operation_key:
        raise ConfigurationError(f"Helper response operation_key must be {operation_key}")
    outcome = value.get("outcome")
    expected_exit_code = HELPER_EXIT_CODES.get(outcome)
    if expected_exit_code is None:
        raise ConfigurationError("Helper response outcome is not supported by the current contract")
    if exit_code != expected_exit_code:
        raise ConfigurationError("Helper response outcome and process exit code do not match the current contract")
    return value
