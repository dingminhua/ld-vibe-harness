from __future__ import annotations

import copy
from pathlib import Path

import pytest

import ldvh_specs


ROOT = Path(__file__).resolve().parents[2]


E2E_NAME_TOKENS = ("e2e",)
RUNTIME_NAME_TOKENS = (
    "runtime_",
    "runtime_adapter",
    "acknowledge_read_plan",
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
    "governed_project_resolver_matches_git_worktree_common_dir",
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
            item.add_marker(pytest.mark.slow)
        if any(token in name for token in RUNTIME_LONG_NAME_TOKENS):
            item.add_marker(pytest.mark.runtime_slow)


@pytest.fixture(scope="session")
def validation_result() -> dict:
    """build_validation(ROOT) 的 session 级缓存。

    调用方不得修改返回值（已 deepcopy 防御，仍请保持只读）。
    """
    return copy.deepcopy(ldvh_specs.build_validation(ROOT))


@pytest.fixture(scope="session")
def e2e_rehearsal_result() -> dict:
    """build_e2e_rehearsal(ROOT, target_path=tests/code/test_ldvh_specs_validate.py) 的 session 级缓存。

    调用方不得修改返回值（已 deepcopy 防御，仍请保持只读）。
    """
    return copy.deepcopy(
        ldvh_specs.build_e2e_rehearsal(
            ROOT,
            target_path="tests/code/test_ldvh_specs_validate.py",
            task="阶段 8 端到端闭环测试",
        )
    )
