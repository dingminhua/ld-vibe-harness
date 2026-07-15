from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

CONFIG_FILENAME = "ldvh.json"
CONFIG_VERSION = 1
GOVERNED_PROJECTS_FILENAME = "LDVH-GOVERNED-PROJECTS.yaml"


class ConfigurationError(ValueError):
    pass


def configure_utf8_standard_streams() -> None:
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="strict")


def _absolute_path(value: Any, field: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ConfigurationError(f"{field} must be a non-empty absolute path string")
    path = Path(value)
    if not path.is_absolute():
        raise ConfigurationError(f"{field} must be an absolute path")
    return path


def validate_configuration(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ConfigurationError("configuration must be a JSON object")
    expected = {"config_version", "helper_executable", "workspace_root"}
    unknown = sorted(set(value) - expected)
    missing = sorted(expected - set(value))
    if unknown:
        raise ConfigurationError(f"configuration contains unknown fields: {', '.join(unknown)}")
    if missing:
        raise ConfigurationError(f"configuration is missing fields: {', '.join(missing)}")
    if value["config_version"] != CONFIG_VERSION:
        raise ConfigurationError(f"config_version must be {CONFIG_VERSION}")

    helper = _absolute_path(value["helper_executable"], "helper_executable")
    workspace = _absolute_path(value["workspace_root"], "workspace_root")
    if not helper.is_file():
        raise ConfigurationError("helper_executable does not identify a current file")
    if not os.access(helper, os.X_OK):
        raise ConfigurationError("helper_executable is not executable")
    if not workspace.is_dir():
        raise ConfigurationError("workspace_root does not identify a current directory")
    governed_projects = workspace / GOVERNED_PROJECTS_FILENAME
    if not governed_projects.is_file():
        raise ConfigurationError(f"workspace_root does not contain {GOVERNED_PROJECTS_FILENAME}")
    return {
        "config_version": CONFIG_VERSION,
        "helper_executable": str(helper.resolve()),
        "workspace_root": str(workspace.resolve()),
    }


def configuration_path(plugin_data: Path) -> Path:
    if not plugin_data.is_absolute():
        raise ConfigurationError("plugin_data must be an absolute path")
    return plugin_data / CONFIG_FILENAME


def load_configuration(plugin_data: Path) -> dict[str, Any]:
    path = configuration_path(plugin_data)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ConfigurationError(f"configuration does not exist: {path}") from error
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ConfigurationError(f"configuration cannot be read as UTF-8 JSON: {path}") from error
    return validate_configuration(value)


def build_configuration(helper_executable: str, workspace_root: str) -> dict[str, Any]:
    return validate_configuration(
        {
            "config_version": CONFIG_VERSION,
            "helper_executable": helper_executable,
            "workspace_root": workspace_root,
        }
    )


def write_configuration(plugin_data: Path, value: dict[str, Any]) -> Path:
    normalized = validate_configuration(value)
    path = configuration_path(plugin_data)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{CONFIG_FILENAME}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(normalized, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return path
