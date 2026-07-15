from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from configuration import (
    ConfigurationError,
    build_configuration,
    configuration_path,
    configure_utf8_standard_streams,
    load_configuration,
    write_configuration,
)
from helper_protocol import validate_helper_response


def _emit(outcome: str, **details: Any) -> int:
    print(json.dumps({"outcome": outcome, **details}, ensure_ascii=False, sort_keys=True))
    return 0 if outcome in {"ok", "no_change"} else 2


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Configure the LDVH Codex adapter")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("check", "verify"):
        child = subparsers.add_parser(command)
        child.add_argument("--plugin-data", required=True)
    for command in ("plan", "apply"):
        child = subparsers.add_parser(command)
        child.add_argument("--plugin-data", required=True)
        child.add_argument("--helper-executable", required=True)
        child.add_argument("--workspace-root", required=True)
        if command == "apply":
            child.add_argument("--confirm-write", action="store_true")
            child.add_argument("--replace", action="store_true")
    return parser


def _plugin_data(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        raise ConfigurationError("plugin_data must be an absolute path")
    return path


def _load_optional_configuration(plugin_data: Path) -> dict[str, Any] | None:
    path = configuration_path(plugin_data)
    if not path.exists() and not path.is_symlink():
        return None
    return load_configuration(plugin_data)


def _check(plugin_data: Path) -> int:
    configuration = load_configuration(plugin_data)
    return _emit(
        "ok",
        configuration_path=str(configuration_path(plugin_data)),
        configuration=configuration,
        changes=[],
    )


def _plan(plugin_data: Path, helper: str, workspace: str) -> int:
    proposed = build_configuration(helper, workspace)
    path = configuration_path(plugin_data)
    current = _load_optional_configuration(plugin_data)
    change = "none" if current == proposed else ("create" if current is None else "replace")
    return _emit(
        "no_change" if change == "none" else "ok",
        configuration_path=str(path),
        current=current,
        proposed=proposed,
        planned_change=change,
        changes=[],
    )


def _apply(
    plugin_data: Path,
    helper: str,
    workspace: str,
    *,
    confirm_write: bool,
    replace: bool,
) -> int:
    proposed = build_configuration(helper, workspace)
    path = configuration_path(plugin_data)
    current = _load_optional_configuration(plugin_data)
    if current == proposed:
        return _emit("no_change", configuration_path=str(path), configuration=proposed, changes=[])
    if not confirm_write:
        return _emit(
            "invalid_request",
            summary="apply requires --confirm-write",
            configuration_path=str(path),
            changes=[],
        )
    if current is not None and not replace:
        return _emit(
            "conflict",
            summary="an existing different configuration requires --replace",
            configuration_path=str(path),
            current=current,
            proposed=proposed,
            changes=[],
        )
    written = write_configuration(plugin_data, proposed)
    reread = load_configuration(plugin_data)
    return _emit(
        "ok",
        configuration_path=str(written),
        configuration=reread,
        changes=[{"kind": "created" if current is None else "replaced", "path": str(written)}],
    )


def _verify(plugin_data: Path) -> int:
    configuration = load_configuration(plugin_data)
    request = json.dumps(
        {
            "arguments": {"workspace_root": configuration["workspace_root"]},
            "response_profile": "compact",
        }
    )
    completed = subprocess.run(
        [configuration["helper_executable"], "capabilities", "resolve-governance-scope"],
        input=request,
        text=True,
        encoding="utf-8",
        errors="strict",
        capture_output=True,
        timeout=30,
        check=False,
    )
    try:
        parsed_response = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise ConfigurationError("Helper verification did not return JSON") from error
    helper_response = validate_helper_response(
        parsed_response,
        exit_code=completed.returncode,
        request_kind="capabilities",
        operation_key="resolve-governance-scope",
    )
    result = helper_response.get("result")
    operations = result.get("operations", []) if isinstance(result, dict) else []
    available = (
        len(operations) == 1
        and isinstance(operations[0], dict)
        and operations[0].get("operation_key") == "resolve-governance-scope"
        and operations[0].get("availability") == "available_for_request"
    )
    outcome = "ok" if available else "unavailable"
    return _emit(
        outcome,
        configuration_path=str(configuration_path(plugin_data)),
        helper_exit_code=completed.returncode,
        helper_response=helper_response,
        helper_available_for_request=available,
        real_environment_trigger_verified=False,
        changes=[],
    )


def main() -> int:
    configure_utf8_standard_streams()
    arguments = _parser().parse_args()
    try:
        plugin_data = _plugin_data(arguments.plugin_data)
        if arguments.command == "check":
            return _check(plugin_data)
        if arguments.command == "plan":
            return _plan(plugin_data, arguments.helper_executable, arguments.workspace_root)
        if arguments.command == "apply":
            return _apply(
                plugin_data,
                arguments.helper_executable,
                arguments.workspace_root,
                confirm_write=arguments.confirm_write,
                replace=arguments.replace,
            )
        return _verify(plugin_data)
    except (ConfigurationError, OSError, UnicodeError, subprocess.SubprocessError) as error:
        return _emit("unavailable", summary=str(error), changes=[])


if __name__ == "__main__":
    sys.exit(main())
