from __future__ import annotations

import pytest


E2E_NAME_TOKENS = ("e2e",)
RUNTIME_NAME_TOKENS = (
    "runtime_",
    "runtime_adapter",
    "pre_tool_use",
    "preflight_",
    "session_start",
    "completion_claim",
    "environment_status",
    "environment_entry_audit",
)


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    for item in items:
        name = item.name
        if any(token in name for token in E2E_NAME_TOKENS):
            item.add_marker(pytest.mark.e2e)
            item.add_marker(pytest.mark.slow)
        if any(token in name for token in RUNTIME_NAME_TOKENS):
            item.add_marker(pytest.mark.runtime)
            item.add_marker(pytest.mark.slow)
