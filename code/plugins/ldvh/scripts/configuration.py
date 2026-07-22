from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

CONFIG_FILENAME = "ldvh.json"
CONFIG_VERSION = 3
FACT_RECOVERY_CONFIG_VERSION = 2
LEGACY_CONFIG_VERSION = 1
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


def _executable_path(value: Any, field: str) -> Path:
    path = _absolute_path(value, field)
    if not path.is_file():
        raise ConfigurationError(f"{field} does not identify a current file")
    if not os.access(path, os.X_OK):
        raise ConfigurationError(f"{field} is not executable")
    return path


def _configuration_fields(value: Any, expected: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ConfigurationError("configuration must be a JSON object")
    unknown = sorted(set(value) - expected)
    missing = sorted(expected - set(value))
    if unknown:
        raise ConfigurationError(f"configuration contains unknown fields: {', '.join(unknown)}")
    if missing:
        raise ConfigurationError(f"configuration is missing fields: {', '.join(missing)}")
    return value


def _configuration_allowed_fields(value: Any, *, required: set[str], allowed: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ConfigurationError("configuration must be a JSON object")
    unknown = sorted(set(value) - allowed)
    missing = sorted(required - set(value))
    if unknown:
        raise ConfigurationError(f"configuration contains unknown fields: {', '.join(unknown)}")
    if missing:
        raise ConfigurationError(f"configuration is missing fields: {', '.join(missing)}")
    return value


def _workspace(value: Any) -> Path:
    workspace = _absolute_path(value, "workspace_root")
    if not workspace.is_dir():
        raise ConfigurationError("workspace_root does not identify a current directory")
    governed_projects = workspace / GOVERNED_PROJECTS_FILENAME
    if not governed_projects.is_file():
        raise ConfigurationError(f"workspace_root does not contain {GOVERNED_PROJECTS_FILENAME}")
    return workspace


def _validate_fact_recovery_fields(value: dict[str, Any]) -> dict[str, str]:
    fields = {"context_recovery_executable", "workspace_root"}
    present = fields & set(value)
    if not present:
        return {}
    if present != fields:
        raise ConfigurationError("context_recovery_executable and workspace_root must be provided together")
    context_recovery = _executable_path(value["context_recovery_executable"], "context_recovery_executable")
    workspace = _workspace(value["workspace_root"])
    return {
        "context_recovery_executable": str(context_recovery.resolve()),
        "workspace_root": str(workspace.resolve()),
    }


def validate_configuration(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ConfigurationError("configuration must be a JSON object")
    version = value.get("config_version")
    if version == FACT_RECOVERY_CONFIG_VERSION:
        legacy_v2 = _configuration_fields(
            value,
            {"config_version", "helper_executable", "context_recovery_executable", "workspace_root"},
        )
        helper = _executable_path(legacy_v2["helper_executable"], "helper_executable")
        return {
            "config_version": FACT_RECOVERY_CONFIG_VERSION,
            "helper_executable": str(helper.resolve()),
            **_validate_fact_recovery_fields(legacy_v2),
        }
    value = _configuration_allowed_fields(
        value,
        required={"config_version", "helper_executable"},
        allowed={"config_version", "helper_executable", "context_recovery_executable", "workspace_root"},
    )
    if value["config_version"] != CONFIG_VERSION:
        raise ConfigurationError(f"config_version must be {FACT_RECOVERY_CONFIG_VERSION} or {CONFIG_VERSION}")
    helper = _executable_path(value["helper_executable"], "helper_executable")
    return {
        "config_version": CONFIG_VERSION,
        "helper_executable": str(helper.resolve()),
        **_validate_fact_recovery_fields(value),
    }


def validate_legacy_configuration(value: Any) -> dict[str, Any]:
    expected = {"config_version", "helper_executable", "workspace_root"}
    value = _configuration_fields(value, expected)
    if value["config_version"] != LEGACY_CONFIG_VERSION:
        raise ConfigurationError(f"config_version must be {LEGACY_CONFIG_VERSION}")
    helper = _executable_path(value["helper_executable"], "helper_executable")
    workspace = _workspace(value["workspace_root"])
    return {
        "config_version": LEGACY_CONFIG_VERSION,
        "helper_executable": str(helper.resolve()),
        "workspace_root": str(workspace.resolve()),
    }


def configuration_path(plugin_data: Path) -> Path:
    if not plugin_data.is_absolute():
        raise ConfigurationError("plugin_data must be an absolute path")
    return plugin_data / CONFIG_FILENAME


def _read_configuration(plugin_data: Path) -> Any:
    path = configuration_path(plugin_data)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ConfigurationError(f"configuration does not exist: {path}") from error
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ConfigurationError(f"configuration cannot be read as UTF-8 JSON: {path}") from error
    return value


def load_configuration(plugin_data: Path) -> dict[str, Any]:
    value = _read_configuration(plugin_data)
    if isinstance(value, dict) and value.get("config_version") == LEGACY_CONFIG_VERSION:
        raise ConfigurationError("configuration version 1 requires explicit v3 replacement")
    return validate_configuration(value)


def load_rule_orientation_configuration(plugin_data: Path) -> dict[str, Any]:
    value = _read_configuration(plugin_data)
    if not isinstance(value, dict):
        raise ConfigurationError("configuration must be a JSON object")
    version = value.get("config_version")
    if version not in {FACT_RECOVERY_CONFIG_VERSION, CONFIG_VERSION}:
        raise ConfigurationError(f"config_version must be {FACT_RECOVERY_CONFIG_VERSION} or {CONFIG_VERSION}")
    allowed = {"config_version", "helper_executable", "context_recovery_executable", "workspace_root"}
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise ConfigurationError(f"configuration contains unknown fields: {', '.join(unknown)}")
    if "helper_executable" not in value:
        raise ConfigurationError("configuration is missing fields: helper_executable")
    helper = _executable_path(value["helper_executable"], "helper_executable")
    return {"config_version": version, "helper_executable": str(helper.resolve())}


def load_existing_configuration(plugin_data: Path) -> dict[str, Any]:
    value = _read_configuration(plugin_data)
    if isinstance(value, dict) and value.get("config_version") == LEGACY_CONFIG_VERSION:
        return validate_legacy_configuration(value)
    return validate_configuration(value)


def build_configuration(
    helper_executable: str,
    context_recovery_executable: str | None = None,
    workspace_root: str | None = None,
) -> dict[str, Any]:
    value: dict[str, Any] = {
        "config_version": CONFIG_VERSION,
        "helper_executable": helper_executable,
    }
    if context_recovery_executable is not None:
        value["context_recovery_executable"] = context_recovery_executable
    if workspace_root is not None:
        value["workspace_root"] = workspace_root
    return validate_configuration(
        value
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
