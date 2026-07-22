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
    load_existing_configuration,
    load_rule_orientation_configuration,
    write_configuration,
)


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
        child.add_argument("--context-recovery-executable")
        child.add_argument("--workspace-root")
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
    return load_existing_configuration(plugin_data)


def _check(plugin_data: Path) -> int:
    rule_orientation_configuration = load_rule_orientation_configuration(plugin_data)
    try:
        configuration = load_configuration(plugin_data)
    except ConfigurationError as error:
        return _emit(
            "ok",
            configuration_path=str(configuration_path(plugin_data)),
            configuration=rule_orientation_configuration,
            fact_recovery_configuration={"status": "invalid", "summary": str(error)},
            changes=[],
        )
    return _emit(
        "ok",
        configuration_path=str(configuration_path(plugin_data)),
        configuration=configuration,
        fact_recovery_configuration={
            "status": "configured" if "context_recovery_executable" in configuration else "not_configured"
        },
        changes=[],
    )


def _plan(plugin_data: Path, helper: str, context_recovery: str | None, workspace: str | None) -> int:
    proposed = build_configuration(helper, context_recovery, workspace)
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
    context_recovery: str | None,
    workspace: str | None,
    *,
    confirm_write: bool,
    replace: bool,
) -> int:
    proposed = build_configuration(helper, context_recovery, workspace)
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
    configuration = load_rule_orientation_configuration(plugin_data)
    completed = subprocess.run(
        [
            configuration["helper_executable"],
            "capabilities",
        ],
        cwd=plugin_data,
        input=json.dumps({"response_profile": "compact"}, ensure_ascii=False),
        text=True,
        encoding="utf-8",
        errors="strict",
        capture_output=True,
        timeout=30,
        check=False,
    )
    if completed.returncode != 0:
        raise ConfigurationError("Rule orientation Helper verification did not complete successfully")
    try:
        parsed_response = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise ConfigurationError("Rule orientation Helper verification did not return JSON") from error
    if (
        not isinstance(parsed_response, dict)
        or parsed_response.get("contract") != "ldvh-helper-cli/2"
        or parsed_response.get("request_kind") != "capabilities"
        or parsed_response.get("operation_key") is not None
        or parsed_response.get("outcome") != "ok"
    ):
        raise ConfigurationError("Rule orientation Helper verification did not return Helper capabilities")
    result = parsed_response.get("result")
    operations = result.get("operations") if isinstance(result, dict) else []
    if not isinstance(operations, list) or not any(
        isinstance(item, dict)
        and item.get("operation_key") == "read-specification-content"
        and item.get("implementation", {}).get("present") is True
        for item in operations
    ):
        raise ConfigurationError("Rule orientation Helper verification did not expose read-specification-content")
    try:
        full_configuration = load_configuration(plugin_data)
    except ConfigurationError:
        fact_recovery_configuration = "invalid"
    else:
        fact_recovery_configuration = (
            "configured_not_checked" if "context_recovery_executable" in full_configuration else "not_configured"
        )
    return _emit(
        "ok",
        configuration_path=str(configuration_path(plugin_data)),
        rule_orientation_helper_verified=True,
        fact_recovery_configuration=fact_recovery_configuration,
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
            return _plan(
                plugin_data,
                arguments.helper_executable,
                arguments.context_recovery_executable,
                arguments.workspace_root,
            )
        if arguments.command == "apply":
            return _apply(
                plugin_data,
                arguments.helper_executable,
                arguments.context_recovery_executable,
                arguments.workspace_root,
                confirm_write=arguments.confirm_write,
                replace=arguments.replace,
            )
        return _verify(plugin_data)
    except (ConfigurationError, OSError, UnicodeError, subprocess.SubprocessError) as error:
        return _emit("unavailable", summary=str(error), changes=[])


if __name__ == "__main__":
    sys.exit(main())
