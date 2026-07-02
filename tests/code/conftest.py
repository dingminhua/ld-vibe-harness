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
    "commit_validate",
)
HOOK_ADAPTER_NAME_TOKENS = (
    "governed_hook_adapter",
    "install_git_hooks",
    "environment_status",
    "environment_entry_audit",
    "runtime_adapter",
)
RUNTIME_LONG_NAME_TOKENS = (
    "runtime_supports_all_consumption_timings",
    "specs_validate_cli_e2e_json",
    "e2e_rehearsal",
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
        if any(token in name for token in HOOK_ADAPTER_NAME_TOKENS):
            item.add_marker(pytest.mark.hook_adapter)
        if any(token in name for token in RUNTIME_LONG_NAME_TOKENS):
            item.add_marker(pytest.mark.runtime_slow)
