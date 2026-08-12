"""Manage the LDVH Git Hook bundle at the Git common-dir boundary."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import os
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from ldvh.governance.git import resolve_git_identity
from ldvh.governance.models import LocatorSource, ScopeDescriptor, ScopeStatus
from ldvh.governance.resolver import resolve_governance_scope

_MANAGED_MARKER_PREFIX = "# ldvh-native-commit-msg-hook: v1 sha256:"
_PREPARE_MANAGED_MARKER_PREFIX = "# ldvh-native-prepare-commit-msg-hook: v1 sha256:"
_GIT_TIMEOUT_SECONDS = 10
_HOOK_PREFLIGHT_TIMEOUT_SECONDS = 20
_LEGACY_HOOKS_PATH = ".githooks-v4"
HookState = Literal["absent", "managed", "conflict", "unavailable"]


@dataclass(frozen=True, slots=True)
class CommitMsgHookStatus:
    """Current ownership state of the common-dir Git Hook deployment."""

    state: HookState
    detail: str
    worktree_root: str | None
    hook_directory: str | None
    hook_path: str | None
    git_common_dir: str | None = None
    worktree_roots: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class _GitConfigEntry:
    scope: str
    origin: str
    value: str


@dataclass(frozen=True, slots=True)
class _LegacyOverride:
    worktree: Path
    config_path: Path
    hook_directory: Path
    hook_path: Path


@dataclass(frozen=True, slots=True)
class _HookDeployment:
    name: str
    rendered: str
    marker_prefix: str


class CommitMsgHookError(ValueError):
    """A requested deployment cannot safely touch the target Git Hook boundary."""


def _status(
    state: HookState,
    detail: str,
    *,
    worktree: Path | None = None,
    common_dir: Path | None = None,
    hook_directory: Path | None = None,
    worktrees: tuple[Path, ...] = (),
) -> CommitMsgHookStatus:
    hook_path = None if hook_directory is None else hook_directory / "commit-msg"
    return CommitMsgHookStatus(
        state,
        detail,
        None if worktree is None else str(worktree),
        None if hook_directory is None else str(hook_directory),
        None if hook_path is None else str(hook_path),
        None if common_dir is None else str(common_dir),
        tuple(str(item) for item in worktrees),
    )


def _has_runtime_config_injection() -> bool:
    return "GIT_CONFIG_COUNT" in os.environ or any(
        key.startswith(("GIT_CONFIG_KEY_", "GIT_CONFIG_VALUE_")) for key in os.environ
    )


def _installation_environment() -> dict[str, str]:
    """Use the user's normal config scopes while rejecting process-level injection."""

    environment = os.environ.copy()
    for key in (
        "GIT_COMMON_DIR",
        "GIT_CONFIG_COUNT",
        "GIT_DIR",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_WORK_TREE",
    ):
        environment.pop(key, None)
    for key in tuple(environment):
        if key.startswith(("GIT_CONFIG_KEY_", "GIT_CONFIG_VALUE_")):
            environment.pop(key, None)
    environment["GIT_TERMINAL_PROMPT"] = "0"
    return environment


def _run_git(worktree: Path, *arguments: str, allow_missing: bool = False) -> tuple[str | None, str | None]:
    try:
        completed = subprocess.run(
            ("git", "-C", str(worktree), *arguments),
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="strict",
            env=_installation_environment(),
            timeout=_GIT_TIMEOUT_SECONDS,
        )
    except FileNotFoundError as error:
        return None, f"Git executable is unavailable: {error}"
    except (OSError, UnicodeError) as error:
        return None, f"Git inspection could not start: {error}"
    except subprocess.TimeoutExpired:
        return None, f"Git inspection exceeded {_GIT_TIMEOUT_SECONDS} seconds"
    if allow_missing and completed.returncode == 1 and not completed.stdout and not completed.stderr:
        return None, None
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip() or str(completed.returncode)
        return None, f"Git inspection failed: {detail}"
    return completed.stdout.strip(), None


def _worktree(value: str) -> tuple[Path | None, str | None]:
    if not isinstance(value, str) or not value.strip() or not Path(value).is_absolute():
        return None, "worktree must be a non-empty absolute path"
    requested = Path(value)
    identity = resolve_git_identity(str(requested), base=requested)
    if identity.status != "git_worktree" or identity.identity is None:
        detail = identity.failure.summary if identity.failure is not None else identity.non_worktree_reason
        return None, f"worktree is not an available non-bare Git worktree: {detail}"
    return identity.identity.worktree_root, None


def _absolute_directory(value: str, field: str) -> Path:
    if not isinstance(value, str) or not value.strip() or not Path(value).is_absolute():
        raise CommitMsgHookError(f"{field} must be a non-empty absolute directory path")
    try:
        path = Path(value).resolve(strict=True)
    except OSError as error:
        raise CommitMsgHookError(f"{field} could not be resolved: {error}") from error
    if not path.is_dir() or "\n" in str(path) or "\r" in str(path):
        raise CommitMsgHookError(f"{field} does not identify a representable current directory")
    return path


def _executable(value: str) -> Path:
    if not isinstance(value, str) or not value.strip() or not Path(value).is_absolute():
        raise CommitMsgHookError("commit_msg_runner must be a non-empty absolute file path")
    try:
        path = Path(value).resolve(strict=True)
    except OSError as error:
        raise CommitMsgHookError(f"commit_msg_runner could not be resolved: {error}") from error
    if not path.is_file() or not os.access(path, os.X_OK) or "\n" in str(path) or "\r" in str(path):
        raise CommitMsgHookError("commit_msg_runner must identify a representable executable file")
    return path


def _common_dir(worktree: Path) -> tuple[Path | None, str | None]:
    output, failure = _run_git(worktree, "rev-parse", "--path-format=absolute", "--git-common-dir")
    if failure is not None or output is None:
        return None, failure
    candidate = Path(output)
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as error:
        return None, f"Git common-dir could not be resolved: {error}"
    if candidate != resolved or not resolved.is_dir():
        return None, "Git common-dir must be a current directory without symbolic-link traversal"
    return resolved, None


def _common_hooks_directory(common_dir: Path) -> tuple[Path | None, str | None]:
    candidate = common_dir / "hooks"
    try:
        resolved = candidate.resolve(strict=False)
    except (OSError, RuntimeError) as error:
        return None, f"common-dir hooks directory could not be resolved: {error}"
    if candidate != resolved or candidate.is_symlink():
        return None, "common-dir hooks directory must not traverse a symbolic link"
    if candidate.exists() and not candidate.is_dir():
        return None, "common-dir hooks path exists but is not a directory"
    return candidate, None


def _enumerate_worktrees(worktree: Path) -> tuple[tuple[Path, ...] | None, str | None]:
    output, failure = _run_git(worktree, "worktree", "list", "--porcelain")
    if failure is not None or output is None:
        return None, failure
    discovered: list[Path] = []
    for record in output.strip().split("\n\n"):
        lines = record.splitlines()
        if not lines or not lines[0].startswith("worktree "):
            return None, "Git worktree inventory contains an invalid record"
        candidate = Path(lines[0].removeprefix("worktree "))
        prunable = any(line == "prunable" or line.startswith("prunable ") for line in lines[1:])
        try:
            resolved = candidate.resolve(strict=True)
        except OSError as error:
            if prunable and not candidate.exists():
                continue
            return None, f"registered worktree could not be resolved: {candidate}: {error}"
        if prunable:
            return None, f"registered worktree is marked prunable but still resolves: {resolved}"
        if not resolved.is_dir():
            return None, f"registered worktree is not a directory: {resolved}"
        discovered.append(resolved)
    if not discovered:
        return None, "Git did not enumerate any worktree"
    return tuple(dict.fromkeys(discovered)), None


def _config_entries(worktree: Path, key: str) -> tuple[tuple[_GitConfigEntry, ...] | None, str | None]:
    try:
        completed = subprocess.run(
            ("git", "-C", str(worktree), "config", "--null", "--show-origin", "--show-scope", "--get-all", key),
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="strict",
            env=_installation_environment(),
            timeout=_GIT_TIMEOUT_SECONDS,
        )
    except (OSError, UnicodeError, subprocess.TimeoutExpired) as error:
        return None, f"Git configuration inspection failed: {error}"
    if completed.returncode == 1 and not completed.stdout and not completed.stderr:
        return (), None
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip() or str(completed.returncode)
        return None, f"Git configuration inspection failed: {detail}"
    fields = completed.stdout.split("\0")
    if fields and fields[-1] == "":
        fields.pop()
    if len(fields) % 3 or not all(fields):
        return None, f"Git configuration inspection returned invalid {key} records"
    return tuple(_GitConfigEntry(*fields[index : index + 3]) for index in range(0, len(fields), 3)), None


def _origin_path(worktree: Path, origin: str) -> Path | None:
    if not origin.startswith("file:"):
        return None
    path = Path(origin.removeprefix("file:"))
    if not path.is_absolute():
        path = worktree / path
    try:
        return path.resolve(strict=False)
    except (OSError, RuntimeError):
        return None


def _worktree_config_path(worktree: Path) -> tuple[Path | None, str | None]:
    output, failure = _run_git(worktree, "rev-parse", "--path-format=absolute", "--git-path", "config.worktree")
    if failure is not None or output is None:
        return None, failure
    try:
        return Path(output).resolve(strict=False), None
    except (OSError, RuntimeError) as error:
        return None, f"worktree config path could not be resolved: {error}"


def _existing_hook_state(path: Path, *, name: str, marker_prefix: str) -> tuple[HookState, str]:
    if path.is_symlink():
        return "conflict", f"existing Git {name} Hook is a symbolic link and is not managed by LDVH"
    try:
        info = path.stat()
    except FileNotFoundError:
        return "absent", f"no Git {name} Hook is installed at the common-dir Hook path"
    except OSError as error:
        return "unavailable", f"existing Git {name} Hook could not be inspected: {error}"
    if not stat.S_ISREG(info.st_mode):
        return "conflict", f"existing Git {name} Hook is not a regular file"
    try:
        contents = path.read_bytes()
    except OSError as error:
        return "conflict", f"existing Git {name} Hook cannot be identified safely: {error}"
    prefix = b"#!/bin/sh\n"
    marker, delimiter, body = contents.removeprefix(prefix).partition(b"\n")
    expected_prefix = marker_prefix.encode("ascii")
    if contents.startswith(prefix) and delimiter and marker.startswith(expected_prefix):
        observed = marker.removeprefix(expected_prefix)
        expected = hashlib.sha256(body).hexdigest().encode("ascii")
        if hmac.compare_digest(observed, expected):
            return "managed", f"LDVH owns the current Git {name} Hook"
        return "conflict", f"existing Git {name} Hook carries an invalid LDVH ownership digest"
    return "conflict", f"an existing Git {name} Hook is not owned by LDVH"


def _deployment_state(
    path: Path,
    deployment: _HookDeployment,
    *,
    legacy_content: str | None = None,
) -> tuple[HookState, str]:
    """Classify a bundle member, accepting only a byte-exact legacy LDVH asset."""

    state, detail = _existing_hook_state(path, name=deployment.name, marker_prefix=deployment.marker_prefix)
    if state == "conflict" and legacy_content is not None:
        try:
            if not path.is_symlink() and hmac.compare_digest(path.read_bytes(), legacy_content.encode("utf-8")):
                return "managed", f"LDVH owns the legacy {deployment.name} Hook eligible for upgrade"
        except OSError:
            pass
    return state, detail


def _bundle_inventory(
    hooks: Path,
    deployments: tuple[_HookDeployment, ...],
    *,
    legacy_contents: dict[str, str],
) -> tuple[dict[str, bytes | None] | None, str | None]:
    """Preflight ownership for both managed files before any file is changed."""

    originals: dict[str, bytes | None] = {}
    for deployment in deployments:
        path = hooks / deployment.name
        state, detail = _deployment_state(path, deployment, legacy_content=legacy_contents.get(deployment.name))
        if state in {"conflict", "unavailable"}:
            return None, detail
        try:
            originals[deployment.name] = path.read_bytes() if path.exists() else None
        except OSError as error:
            return None, f"existing Git {deployment.name} Hook could not be snapshotted: {error}"
    return originals, None


def _active_hook_assets(directory: Path, *, ignore: frozenset[str] = frozenset()) -> tuple[str, ...] | None:
    if not directory.exists():
        return ()
    if directory.is_symlink() or not directory.is_dir():
        return None
    try:
        entries = tuple(directory.iterdir())
    except OSError:
        return None
    return tuple(
        sorted(
            entry.name
            for entry in entries
            if entry.name not in ignore
            and not entry.name.endswith(".sample")
            and (entry.is_symlink() or (entry.is_file() and os.access(entry, os.X_OK)))
        )
    )


def _legacy_override(worktree: Path, entry: _GitConfigEntry) -> tuple[_LegacyOverride | None, str | None]:
    config_path, failure = _worktree_config_path(worktree)
    if failure is not None or config_path is None:
        return None, failure
    if (
        entry.scope != "worktree"
        or entry.value != _LEGACY_HOOKS_PATH
        or _origin_path(worktree, entry.origin) != config_path
    ):
        return None, "effective core.hooksPath is unknown or not an LDVH-owned legacy worktree override"
    directory = worktree / _LEGACY_HOOKS_PATH
    try:
        resolved = directory.resolve(strict=False)
    except (OSError, RuntimeError) as error:
        return None, f"legacy Hook directory could not be resolved: {error}"
    if resolved != directory or directory.is_symlink():
        return None, "legacy Hook directory traverses a symbolic link"
    state, detail = _existing_hook_state(
        directory / "commit-msg", name="commit-msg", marker_prefix=_MANAGED_MARKER_PREFIX
    )
    if state != "managed":
        return None, f"legacy worktree override lacks an intact LDVH-owned commit-msg Hook: {detail}"
    active = _active_hook_assets(directory, ignore=frozenset({"commit-msg"}))
    if active is None or active:
        return None, "legacy Hook directory contains unknown active assets"
    return _LegacyOverride(worktree, config_path, directory, directory / "commit-msg"), None


def _equivalent_common_hooks_path(
    worktree: Path,
    entries: tuple[_GitConfigEntry, ...],
    hooks: Path,
) -> tuple[bool, str | None]:
    """Accept one local/worktree setting only when it resolves to this common-dir Hook directory."""

    if len(entries) != 1:
        return False, "multiple core.hooksPath values are not safe to migrate"
    entry = entries[0]
    if entry.scope not in {"local", "worktree"}:
        return False, "effective core.hooksPath is not a local or worktree-scoped common-dir setting"
    if entry.value.startswith("!"):
        return False, "effective core.hooksPath uses a command value and is not safe to migrate"
    effective, failure = _effective_hooks_directory(worktree)
    if failure is not None or effective is None:
        return False, failure or "effective core.hooksPath is unavailable"
    if effective != hooks:
        return False, "effective core.hooksPath does not resolve to this common-dir Hook directory"
    return True, None


def _override_inventory(
    worktrees: tuple[Path, ...], hooks: Path
) -> tuple[tuple[_LegacyOverride, ...] | None, str | None]:
    legacy: list[_LegacyOverride] = []
    for worktree in worktrees:
        entries, failure = _config_entries(worktree, "core.hooksPath")
        if failure is not None or entries is None:
            return None, f"{worktree}: {failure}"
        if not entries:
            continue
        if len(entries) != 1:
            return None, f"{worktree}: multiple core.hooksPath values are not safe to migrate"
        equivalent, equivalent_failure = _equivalent_common_hooks_path(worktree, entries, hooks)
        if equivalent:
            continue
        override, failure = _legacy_override(worktree, entries[0])
        if failure is not None or override is None:
            return None, f"{worktree}: {equivalent_failure or failure}"
        legacy.append(override)
    return tuple(legacy), None


def _governance_failure(worktrees: tuple[Path, ...], workspace: Path, common_dir: Path) -> str | None:
    for worktree in worktrees:
        run = resolve_governance_scope(
            (ScopeDescriptor(0, str(worktree), LocatorSource.EXPLICIT_LOCATOR),),
            base=worktree,
            explicit_workspace_root=workspace,
        )
        if run.result is None:
            details = "; ".join(item.summary for item in run.diagnostics) or "governance resolution did not complete"
            return f"{worktree}: actual worktree governance is unavailable: {details}"
        if run.result.scope_status is not ScopeStatus.GOVERNED_SINGLE:
            return f"{worktree}: actual worktree must resolve as governed_single, not {run.result.scope_status.value}"
        resolution = run.result.object_resolutions[0]
        if resolution.git_common_dir is None or Path(resolution.git_common_dir).resolve(strict=False) != common_dir:
            return f"{worktree}: governance did not bind the requested Git common-dir"
    return None


def render_commit_msg_hook(*, commit_msg_runner: Path, workspace_root: Path) -> str:
    """Render the common-dir POSIX adapter; it contains no LDVH rule data."""

    runner = shlex.quote(str(commit_msg_runner))
    workspace = shlex.quote(str(workspace_root))
    body = "\n".join(
        (
            "set -eu",
            'if [ "$#" -ne 1 ]; then',
            '  printf "%s\\n" "LDVH Git commit-msg Hook expected one message-file argument" >&2',
            "  exit 1",
            "fi",
            "worktree=$(git rev-parse --show-toplevel) || {",
            '  printf "%s\\n" "LDVH Git commit-msg Hook could not determine the current worktree" >&2',
            "  exit 1",
            "}",
            "# The source launcher may be named python3 or python on different hosts.",
            "run_runner() {",
            "  if command -v python3 >/dev/null 2>&1; then",
            f'    exec python3 {runner} "$@"',
            "  elif command -v python >/dev/null 2>&1; then",
            f'    exec python {runner} "$@"',
            "  fi",
            f'  exec {runner} "$@"',
            "}",
            'case "$1" in',
            "  /*|[A-Za-z]:\\\\*|//*) message_file=$1 ;;",
            '  *) message_file="$worktree/$1" ;;',
            "esac",
            'if [ -n "${GIT_INDEX_FILE:-}" ]; then',
            '  case "$GIT_INDEX_FILE" in',
            "    /*|[A-Za-z]:\\\\*|//*) index_file=$GIT_INDEX_FILE ;;",
            '    *) index_file="$worktree/$GIT_INDEX_FILE" ;;',
            "  esac",
            f'  run_runner git-commit-msg --workspace-root {workspace} --worktree "$worktree" '
            f'--message-file "$message_file" --index-file "$index_file"',
            "fi",
            f'run_runner git-commit-msg --workspace-root {workspace} --worktree "$worktree" '
            '--message-file "$message_file"',
            "",
        )
    )
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    return f"#!/bin/sh\n{_MANAGED_MARKER_PREFIX}{digest}\n{body}"


def render_prepare_commit_msg_hook(*, commit_msg_runner: Path) -> str:
    """Render the companion signature injector without embedding signature data."""

    runner = shlex.quote(str(commit_msg_runner))
    body = "\n".join(
        (
            "set -eu",
            'if [ "$#" -lt 1 ]; then',
            "  exit 0",
            "fi",
            "worktree=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0",
            "run_runner() {",
            "  if command -v python3 >/dev/null 2>&1; then",
            f'    exec python3 {runner} "$@"',
            "  elif command -v python >/dev/null 2>&1; then",
            f'    exec python {runner} "$@"',
            "  fi",
            f'  exec {runner} "$@"',
            "}",
            'case "$1" in',
            "  /*|[A-Za-z]:\\\\*|//*) message_file=$1 ;;",
            '  *) message_file="$worktree/$1" ;;',
            "esac",
            'run_runner prepare-commit-msg --message-file "$message_file"',
            "",
        )
    )
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    return f"#!/bin/sh\n{_PREPARE_MANAGED_MARKER_PREFIX}{digest}\n{body}"


def _hook_deployments(*, commit_msg_runner: Path, workspace_root: Path) -> tuple[_HookDeployment, ...]:
    return (
        _HookDeployment(
            "commit-msg",
            render_commit_msg_hook(commit_msg_runner=commit_msg_runner, workspace_root=workspace_root),
            _MANAGED_MARKER_PREFIX,
        ),
        _HookDeployment(
            "prepare-commit-msg",
            render_prepare_commit_msg_hook(commit_msg_runner=commit_msg_runner),
            _PREPARE_MANAGED_MARKER_PREFIX,
        ),
    )


def _legacy_prepare_commit_msg_hook(*, commit_msg_runner: Path) -> str:
    """The exact v1 injector wrapper that predated managed bundle deployment.

    It is recognized only to migrate an already-known LDVH asset.  Any variation is
    deliberately treated as user-owned instead of being overwritten.
    """

    runner = shlex.quote(str(commit_msg_runner))
    return "\n".join(
        (
            "#!/bin/sh",
            "# ldvh-native-prepare-commit-msg-hook: v1",
            "set -eu",
            'if [ "$#" -lt 1 ]; then',
            "  exit 0",
            "fi",
            "worktree=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0",
            'case "$1" in',
            "  /*) message_file=$1 ;;",
            '  *) message_file="$worktree/$1" ;;',
            "esac",
            "# Check all env vars in the fallback chain, not just LDVH_*",
            'if [ -n "${LDVH_MODEL_ID:-}${LDVH_WORKBENCH_NAME:-}${LDVH_SESSION_ID:-}'
            '${CODEBUDDY_SESSION_ID:-}${CLAUDE_SESSION_ID:-}${CLIENT_INFO_PRODUCT_NAME:-}" ]; then',
            f'  {runner} prepare-commit-msg --message-file "$message_file" >&2 || true',
            "fi",
            "exit 0",
            "",
        )
    )


def _legacy_commit_msg_hook(*, commit_msg_runner: Path, workspace_root: Path) -> str:
    """The exact pre-bundle Gate wrapper, recognized only with its bindings intact."""

    runner = shlex.quote(str(commit_msg_runner))
    workspace = shlex.quote(str(workspace_root))
    body = "\n".join(
        (
            "set -eu",
            'if [ "$#" -ne 1 ]; then',
            '  printf "%s\\n" "LDVH Git commit-msg Hook expected one message-file argument" >&2',
            "  exit 1",
            "fi",
            "worktree=$(git rev-parse --show-toplevel) || {",
            '  printf "%s\\n" "LDVH Git commit-msg Hook could not determine the current worktree" >&2',
            "  exit 1",
            "}",
            'case "$1" in',
            "  /*) message_file=$1 ;;",
            '  *) message_file="$worktree/$1" ;;',
            "esac",
            'if [ -n "${GIT_INDEX_FILE:-}" ]; then',
            '  case "$GIT_INDEX_FILE" in',
            "    /*) index_file=$GIT_INDEX_FILE ;;",
            '    *) index_file="$worktree/$GIT_INDEX_FILE" ;;',
            "  esac",
            f'  exec {runner} git-commit-msg --workspace-root {workspace} --worktree "$worktree" '
            f'--message-file "$message_file" --index-file "$index_file"',
            "fi",
            f'exec {runner} git-commit-msg --workspace-root {workspace} --worktree "$worktree" '
            '--message-file "$message_file"',
            "",
        )
    )
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    return f"#!/bin/sh\n{_MANAGED_MARKER_PREFIX}{digest}\n{body}"


def _atomic_write(path: Path, content: str, *, expected: bytes | None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=".ldvh-commit-msg-", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
        temporary.chmod(0o755)
        try:
            current = path.read_bytes()
        except FileNotFoundError:
            current = None
        except OSError as error:
            raise CommitMsgHookError(f"Git Hook changed before deployment could not be inspected: {error}") from error
        if current != expected:
            raise CommitMsgHookError("Git Hook changed before bundle deployment")
        os.replace(temporary, path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def _restore_hook_bytes(path: Path, original: bytes | None) -> str | None:
    """Restore one bundle member exactly; used only after a failed bundle write."""

    try:
        if original is None:
            path.unlink(missing_ok=True)
            return None
        descriptor, temporary_name = tempfile.mkstemp(prefix=".ldvh-hook-rollback-", dir=path.parent)
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(original)
            os.replace(temporary, path)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise
        return None
    except OSError as error:
        return f"{path}: {error}"


def _deploy_hook_bundle(
    hooks: Path, deployments: tuple[_HookDeployment, ...], originals: dict[str, bytes | None]
) -> str | None:
    """Replace the two owned Hook files as one recoverable deployment unit."""

    replaced: list[_HookDeployment] = []
    try:
        for deployment in deployments:
            _atomic_write(hooks / deployment.name, deployment.rendered, expected=originals[deployment.name])
            replaced.append(deployment)
    except (CommitMsgHookError, OSError) as error:
        rollback_failures = [
            failure
            for deployment in reversed(replaced)
            if (failure := _restore_hook_bytes(hooks / deployment.name, originals[deployment.name])) is not None
        ]
        detail = f"Git Hook bundle deployment failed: {error}"
        if rollback_failures:
            detail += "; rollback failures: " + "; ".join(rollback_failures)
        return detail
    for deployment in deployments:
        if not _matches(hooks / deployment.name, deployment.rendered):
            return f"Git Hook bundle deployment could not verify {deployment.name}"
    return None


def _matches(path: Path, rendered: str) -> bool:
    try:
        return not path.is_symlink() and hmac.compare_digest(path.read_bytes(), rendered.encode("utf-8"))
    except OSError:
        return False


def _preflight_rendered_hook(rendered: str, worktree: Path) -> str | None:
    """Run syntax plus real block/allow probes without touching the worktree or its real Index."""

    shell = shutil.which("sh")
    if shell is None:
        return "a POSIX shell is unavailable for commit-msg Hook syntax verification"
    with tempfile.TemporaryDirectory(prefix="ldvh-hook-preflight-") as temporary_name:
        temporary = Path(temporary_name)
        hook = temporary / "commit-msg"
        index = temporary / "index"
        invalid_message = temporary / "invalid-message"
        valid_message = temporary / "valid-message"
        try:
            hook.write_text(rendered, encoding="utf-8", newline="\n")
            hook.chmod(0o755)
            invalid_message.write_text("test: invalid\n", encoding="utf-8")
            valid_message.write_text(
                "test: 验证 Git Hook 预检\n\n"
                "关键变更:\n- 验证待部署 Hook 的真实 allow 与 block 路径\n\n"
                "LDVH-Product-Name: localverification\n"
                "LDVH-Model-Name: ldvh-hook-manager\n"
                "LDVH-Agent-Runtime-Name: ldvh-hook-manager\n",
                encoding="utf-8",
            )
        except OSError as error:
            return f"commit-msg Hook preflight assets could not be prepared: {error}"
        syntax = subprocess.run(
            (shell, "-n", str(hook)),
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="strict",
            timeout=_GIT_TIMEOUT_SECONDS,
        )
        if syntax.returncode != 0:
            return f"rendered commit-msg Hook failed shell syntax verification: {syntax.stderr.strip()}"

        environment = _installation_environment()
        environment["GIT_INDEX_FILE"] = str(index)
        environment["LDVH_SIGNATURE"] = (
            '{"product_name":"localverification","model_name":"ldvh-hook-manager",'
            '"agent_runtime_name":"ldvh-hook-manager"}'
        )
        read_tree = subprocess.run(
            ("git", "-C", str(worktree), "read-tree", "HEAD"),
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="strict",
            env=environment,
            timeout=_GIT_TIMEOUT_SECONDS,
        )
        if read_tree.returncode != 0:
            return "commit-msg Hook preflight requires a readable HEAD with at least one tracked blob"
        staged = subprocess.run(
            ("git", "-C", str(worktree), "ls-files", "--stage", "-z"),
            check=False,
            capture_output=True,
            env=environment,
            timeout=_GIT_TIMEOUT_SECONDS,
        )
        if staged.returncode != 0:
            return "commit-msg Hook preflight could not inspect the temporary Index"
        entries = tuple(item for item in staged.stdout.split(b"\0") if item)
        entry = next((item for item in entries if b" 0\t" in item), None)
        if entry is None:
            return "commit-msg Hook preflight requires at least one stage-zero tracked blob"
        metadata = entry.split(b"\t", 1)[0].decode("ascii").split()
        if len(metadata) != 3:
            return "commit-msg Hook preflight observed an invalid temporary Index entry"
        mode, object_id, _stage = metadata
        existing_paths = {item.split(b"\t", 1)[1] for item in entries if b"\t" in item}
        probe_path = next(
            candidate
            for number in range(1000)
            if (candidate := f".ldvh-hook-preflight-probe-{number}").encode("utf-8") not in existing_paths
        )
        update = subprocess.run(
            (
                "git",
                "-C",
                str(worktree),
                "update-index",
                "--add",
                "--cacheinfo",
                f"{mode},{object_id},{probe_path}",
            ),
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="strict",
            env=environment,
            timeout=_GIT_TIMEOUT_SECONDS,
        )
        if update.returncode != 0:
            return f"commit-msg Hook preflight could not prepare its temporary candidate: {update.stderr.strip()}"

        def invoke(message: Path) -> subprocess.CompletedProcess[str]:
            # The Hook is a POSIX shell script. On Windows (os.name == "nt") subprocess
            # cannot CreateProcess a shell script without .bat/.cmd extension (WinError 193);
            # wrap through a POSIX shell available on the Git Bash/MSYS runtime.
            # Use the shell directly (no exec wrapper) so the hook's own exec call
            # and the subprocess exit code propagate correctly.
            hook_argv = (str(hook), str(message))
            if os.name == "nt":
                shell = shutil.which("sh")
                if shell is None:
                    raise CommitMsgHookError("a POSIX shell is unavailable for commit-msg Hook invocation")
                hook_argv = (shell, str(hook), str(message))
            return subprocess.run(
                hook_argv,
                cwd=worktree,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="strict",
                env=environment,
                timeout=_HOOK_PREFLIGHT_TIMEOUT_SECONDS,
            )

        blocked = invoke(invalid_message)
        if blocked.returncode == 0:
            return "rendered commit-msg Hook preflight did not block an invalid message"
        allowed = invoke(valid_message)
        if allowed.returncode != 0:
            detail = allowed.stderr.strip() or allowed.stdout.strip() or str(allowed.returncode)
            return f"rendered commit-msg Hook preflight did not allow a valid message: {detail}"
    return None


def _preflight_rendered_prepare_hook(rendered: str, worktree: Path) -> str | None:
    """Prove that the injector preserves ordinary messages and injects valid snapshots."""

    shell = shutil.which("sh")
    if shell is None:
        return "a POSIX shell is unavailable for prepare-commit-msg Hook syntax verification"
    with tempfile.TemporaryDirectory(prefix="ldvh-prepare-hook-preflight-") as temporary_name:
        temporary = Path(temporary_name)
        hook = temporary / "prepare-commit-msg"
        message = temporary / "message"
        try:
            hook.write_text(rendered, encoding="utf-8", newline="\n")
            hook.chmod(0o755)
        except OSError as error:
            return f"prepare-commit-msg Hook preflight assets could not be prepared: {error}"
        syntax = subprocess.run(
            (shell, "-n", str(hook)),
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="strict",
            timeout=_GIT_TIMEOUT_SECONDS,
        )
        if syntax.returncode != 0:
            return f"rendered prepare-commit-msg Hook failed shell syntax verification: {syntax.stderr.strip()}"

        ordinary = "docs: ordinary\n\nLDVH-Product-Name: retained\n"
        try:
            message.write_text(ordinary, encoding="utf-8")
        except OSError as error:
            return f"prepare-commit-msg Hook preflight could not write a message: {error}"
        environment = _installation_environment()
        environment.pop("LDVH_SIGNATURE", None)

        def invoke(message_path: Path) -> subprocess.CompletedProcess[str]:
            # Git for Windows supplies a POSIX shell, but CreateProcess cannot
            # launch an extensionless shell script directly on native Windows.
            hook_argv = (str(hook), str(message_path))
            if os.name == "nt":
                hook_argv = (shell, str(hook), str(message_path))
            return subprocess.run(
                hook_argv,
                cwd=worktree,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="strict",
                env=environment,
                timeout=_HOOK_PREFLIGHT_TIMEOUT_SECONDS,
            )

        invocation = invoke(message)
        if invocation.returncode != 0:
            detail = invocation.stderr.strip() or invocation.stdout.strip() or str(invocation.returncode)
            return f"rendered prepare-commit-msg Hook did not preserve an ordinary message: {detail}"
        try:
            if message.read_text(encoding="utf-8") != ordinary:
                return "rendered prepare-commit-msg Hook changed an ordinary message without LDVH_SIGNATURE"
            message.write_text("docs: signed\n\nSession-ID: retired\n", encoding="utf-8")
        except OSError as error:
            return f"prepare-commit-msg Hook preflight could not read its message: {error}"
        environment["LDVH_SIGNATURE"] = (
            '{"product_name":"localverification","model_name":"ldvh-hook-manager",'
            '"agent_runtime_name":"ldvh-hook-manager"}'
        )
        injected = invoke(message)
        if injected.returncode != 0:
            detail = injected.stderr.strip() or injected.stdout.strip() or str(injected.returncode)
            return f"rendered prepare-commit-msg Hook could not inject a valid signature: {detail}"
        try:
            content = message.read_text(encoding="utf-8")
        except OSError as error:
            return f"prepare-commit-msg Hook preflight could not read its injected message: {error}"
        if "Session-ID:" in content or "LDVH-Product-Name: localverification" not in content:
            return "rendered prepare-commit-msg Hook did not replace retired trailers with LDVH signature trailers"
    return None


def _remove_exact(path: Path, rendered: str) -> str | None:
    if not _matches(path, rendered):
        return "managed Git commit-msg Hook changed before removal"
    try:
        path.unlink()
    except OSError as error:
        return f"managed Git commit-msg Hook could not be removed: {error}"
    return None


def _effective_hooks_directory(worktree: Path) -> tuple[Path | None, str | None]:
    output, failure = _run_git(worktree, "rev-parse", "--path-format=absolute", "--git-path", "hooks")
    if failure is not None or output is None:
        return None, failure
    try:
        return Path(output).resolve(strict=False), None
    except (OSError, RuntimeError) as error:
        return None, f"effective Hook directory could not be resolved: {error}"


def inspect_commit_msg_hook(*, worktree: str) -> CommitMsgHookStatus:
    current, failure = _worktree(worktree)
    if failure is not None or current is None:
        return _status("unavailable", failure or "worktree is unavailable")
    if _has_runtime_config_injection():
        return _status("conflict", "runtime Git config injection is not accepted", worktree=current)
    common_dir, failure = _common_dir(current)
    if failure is not None or common_dir is None:
        return _status("unavailable", failure or "Git common-dir is unavailable", worktree=current)
    worktrees, failure = _enumerate_worktrees(current)
    if failure is not None or worktrees is None:
        return _status(
            "unavailable", failure or "worktree inventory is unavailable", worktree=current, common_dir=common_dir
        )
    hooks, failure = _common_hooks_directory(common_dir)
    if failure is not None or hooks is None:
        return _status(
            "conflict",
            failure or "common-dir hooks path is unavailable",
            worktree=current,
            common_dir=common_dir,
            worktrees=worktrees,
        )
    legacy, failure = _override_inventory(worktrees, hooks)
    if failure is not None:
        return _status(
            "conflict", failure, worktree=current, common_dir=common_dir, hook_directory=hooks, worktrees=worktrees
        )
    if legacy:
        return _status(
            "conflict",
            "LDVH-owned legacy worktree Hook overrides still require common-dir migration",
            worktree=current,
            common_dir=common_dir,
            hook_directory=hooks,
            worktrees=worktrees,
        )
    states: list[HookState] = []
    for deployment in _hook_deployments(commit_msg_runner=Path("/unbound"), workspace_root=Path("/unbound")):
        # Inspection only establishes ownership/digest.  Binding is verified by install
        # and uninstall, where the intended runner and workspace are explicit.
        state, detail = _existing_hook_state(
            hooks / deployment.name, name=deployment.name, marker_prefix=deployment.marker_prefix
        )
        if state in {"conflict", "unavailable"}:
            return _status(
                state, detail, worktree=current, common_dir=common_dir, hook_directory=hooks, worktrees=worktrees
            )
        states.append(state)
    if all(state == "absent" for state in states):
        return _status(
            "absent",
            "no LDVH Git Hook bundle is installed at the common-dir Hook path",
            worktree=current,
            common_dir=common_dir,
            hook_directory=hooks,
            worktrees=worktrees,
        )
    if all(state == "managed" for state in states):
        return _status(
            "managed",
            "LDVH Git Hook bundle is installed at the common-dir Hook path",
            worktree=current,
            common_dir=common_dir,
            hook_directory=hooks,
            worktrees=worktrees,
        )
    return _status(
        "conflict",
        "LDVH Git Hook bundle is incomplete at the common-dir Hook path",
        worktree=current,
        common_dir=common_dir,
        hook_directory=hooks,
        worktrees=worktrees,
    )


def _restore_overrides(overrides: tuple[_LegacyOverride, ...]) -> list[str]:
    failures: list[str] = []
    for override in overrides:
        _, failure = _run_git(override.worktree, "config", "--worktree", "core.hooksPath", _LEGACY_HOOKS_PATH)
        if failure is not None:
            failures.append(f"{override.worktree}: {failure}")
    return failures


def install_commit_msg_hook(
    *,
    worktree: str,
    workspace_root: str,
    commit_msg_runner: str,
    human_gate_confirmed: bool,
) -> CommitMsgHookStatus:
    """Deploy one common-dir Hook and migrate only proven LDVH legacy overrides."""

    current, failure = _worktree(worktree)
    if failure is not None or current is None:
        return _status("unavailable", failure or "worktree is unavailable")
    if not human_gate_confirmed:
        return _status(
            "unavailable", "Human Gate confirmation is required before Git Hook deployment", worktree=current
        )
    if _has_runtime_config_injection():
        return _status("conflict", "runtime Git config injection is not accepted", worktree=current)
    try:
        workspace = _absolute_directory(workspace_root, "workspace_root")
        runner = _executable(commit_msg_runner)
    except CommitMsgHookError as error:
        return _status("unavailable", str(error), worktree=current)
    common_dir, failure = _common_dir(current)
    if failure is not None or common_dir is None:
        return _status("unavailable", failure or "Git common-dir is unavailable", worktree=current)
    worktrees, failure = _enumerate_worktrees(current)
    if failure is not None or worktrees is None:
        return _status(
            "unavailable", failure or "worktree inventory is unavailable", worktree=current, common_dir=common_dir
        )
    governance_failure = _governance_failure(worktrees, workspace, common_dir)
    if governance_failure is not None:
        return _status("conflict", governance_failure, worktree=current, common_dir=common_dir, worktrees=worktrees)
    hooks, failure = _common_hooks_directory(common_dir)
    if failure is not None or hooks is None:
        return _status(
            "conflict",
            failure or "common-dir hooks path is unavailable",
            worktree=current,
            common_dir=common_dir,
            worktrees=worktrees,
        )
    legacy, failure = _override_inventory(worktrees, hooks)
    if failure is not None or legacy is None:
        return _status(
            "conflict",
            failure or "Hook override inventory is unavailable",
            worktree=current,
            common_dir=common_dir,
            hook_directory=hooks,
            worktrees=worktrees,
        )
    deployments = _hook_deployments(commit_msg_runner=runner, workspace_root=workspace)
    originals, detail = _bundle_inventory(
        hooks,
        deployments,
        legacy_contents={
            "commit-msg": _legacy_commit_msg_hook(commit_msg_runner=runner, workspace_root=workspace),
            "prepare-commit-msg": _legacy_prepare_commit_msg_hook(commit_msg_runner=runner),
        },
    )
    if originals is None:
        return _status(
            "conflict", detail, worktree=current, common_dir=common_dir, hook_directory=hooks, worktrees=worktrees
        )
    for deployment in deployments:
        path = hooks / deployment.name
        original = originals[deployment.name]
        legacy_content = {
            "commit-msg": _legacy_commit_msg_hook(commit_msg_runner=runner, workspace_root=workspace),
            "prepare-commit-msg": _legacy_prepare_commit_msg_hook(commit_msg_runner=runner),
        }.get(deployment.name)
        if (
            original is not None
            and not _matches(path, deployment.rendered)
            and (legacy_content is None or not hmac.compare_digest(original, legacy_content.encode("utf-8")))
        ):
            return _status(
                "conflict",
                "existing LDVH Hook belongs to a different runner or workspace binding",
                worktree=current,
                common_dir=common_dir,
                hook_directory=hooks,
                worktrees=worktrees,
            )
    try:
        preflight_failure = _preflight_rendered_hook(deployments[0].rendered, current)
        if preflight_failure is None:
            preflight_failure = _preflight_rendered_prepare_hook(deployments[1].rendered, current)
    except (OSError, UnicodeError, subprocess.SubprocessError) as error:
        preflight_failure = f"commit-msg Hook preflight could not complete: {error}"
    if preflight_failure is not None:
        return _status(
            "unavailable",
            preflight_failure,
            worktree=current,
            common_dir=common_dir,
            hook_directory=hooks,
            worktrees=worktrees,
        )
    deployment_failure = _deploy_hook_bundle(hooks, deployments, originals)
    if deployment_failure is not None:
        return _status(
            "unavailable",
            deployment_failure,
            worktree=current,
            common_dir=common_dir,
            hook_directory=hooks,
            worktrees=worktrees,
        )

    removed_overrides: list[_LegacyOverride] = []
    for override in legacy:
        _, failure = _run_git(override.worktree, "config", "--worktree", "--unset-all", "core.hooksPath")
        if failure is not None:
            migration_failure = failure
            rollback_failures = _restore_overrides(tuple(removed_overrides))
            rollback_failures.extend(
                failure
                for deployment in deployments
                if (failure := _restore_hook_bytes(hooks / deployment.name, originals[deployment.name])) is not None
            )
            detail = f"legacy override migration failed for {override.worktree}: {migration_failure}"
            if rollback_failures:
                detail += "; rollback failures: " + "; ".join(rollback_failures)
            return _status(
                "unavailable",
                detail,
                worktree=current,
                common_dir=common_dir,
                hook_directory=hooks,
                worktrees=worktrees,
            )
        removed_overrides.append(override)

    for item in worktrees:
        effective, failure = _effective_hooks_directory(item)
        if failure is not None or effective != hooks:
            rollback_failures = _restore_overrides(tuple(removed_overrides))
            rollback_failures.extend(
                failure
                for deployment in deployments
                if (failure := _restore_hook_bytes(hooks / deployment.name, originals[deployment.name])) is not None
            )
            detail = f"{item}: common-dir Hook did not become the effective Hook directory"
            if failure is not None:
                detail += f": {failure}"
            if rollback_failures:
                detail += "; rollback failures: " + "; ".join(rollback_failures)
            return _status(
                "unavailable",
                detail,
                worktree=current,
                common_dir=common_dir,
                hook_directory=hooks,
                worktrees=worktrees,
            )

    cleanup_failures: list[str] = []
    for override in legacy:
        state, _ = _existing_hook_state(override.hook_path, name="commit-msg", marker_prefix=_MANAGED_MARKER_PREFIX)
        if state == "managed":
            try:
                override.hook_path.unlink()
                override.hook_directory.rmdir()
            except OSError as error:
                cleanup_failures.append(f"{override.hook_directory}: {error}")
    if cleanup_failures:
        return _status(
            "managed",
            "common-dir Hook is active; inactive legacy asset cleanup remains: " + "; ".join(cleanup_failures),
            worktree=current,
            common_dir=common_dir,
            hook_directory=hooks,
            worktrees=worktrees,
        )
    migrated = len(legacy)
    return _status(
        "managed",
        (
            f"LDVH common-dir Git Hook bundle is active for {len(worktrees)} worktree(s); "
            f"migrated {migrated} legacy override(s)"
        ),
        worktree=current,
        common_dir=common_dir,
        hook_directory=hooks,
        worktrees=worktrees,
    )


def bootstrap_commit_msg_hook(**arguments: object) -> CommitMsgHookStatus:
    """Compatibility name for the common-dir deployment operation."""

    return install_commit_msg_hook(**arguments)  # type: ignore[arg-type]


def uninstall_commit_msg_hook(
    *,
    worktree: str,
    workspace_root: str,
    commit_msg_runner: str,
    human_gate_confirmed: bool,
) -> CommitMsgHookStatus:
    current, failure = _worktree(worktree)
    if failure is not None or current is None:
        return _status("unavailable", failure or "worktree is unavailable")
    if not human_gate_confirmed:
        return _status("unavailable", "Human Gate confirmation is required before Git Hook removal", worktree=current)
    try:
        workspace = _absolute_directory(workspace_root, "workspace_root")
        runner = _executable(commit_msg_runner)
    except CommitMsgHookError as error:
        return _status("unavailable", str(error), worktree=current)
    common_dir, failure = _common_dir(current)
    if failure is not None or common_dir is None:
        return _status("unavailable", failure or "Git common-dir is unavailable", worktree=current)
    worktrees, failure = _enumerate_worktrees(current)
    if failure is not None or worktrees is None:
        return _status(
            "unavailable", failure or "worktree inventory is unavailable", worktree=current, common_dir=common_dir
        )
    hooks, failure = _common_hooks_directory(common_dir)
    if failure is not None or hooks is None:
        return _status(
            "conflict",
            failure or "common-dir hooks path is unavailable",
            worktree=current,
            common_dir=common_dir,
            worktrees=worktrees,
        )
    legacy, failure = _override_inventory(worktrees, hooks)
    if failure is not None or legacy:
        return _status(
            "conflict",
            failure or "legacy overrides remain; common-dir removal is unsafe",
            worktree=current,
            common_dir=common_dir,
            hook_directory=hooks,
            worktrees=worktrees,
        )
    deployments = _hook_deployments(commit_msg_runner=runner, workspace_root=workspace)
    paths = tuple(hooks / deployment.name for deployment in deployments)
    states = tuple(
        _existing_hook_state(path, name=deployment.name, marker_prefix=deployment.marker_prefix)[0]
        for path, deployment in zip(paths, deployments, strict=True)
    )
    if all(state == "absent" for state in states):
        return _status(
            "absent",
            "no LDVH Git Hook bundle is installed",
            worktree=current,
            common_dir=common_dir,
            hook_directory=hooks,
            worktrees=worktrees,
        )
    if any(state != "managed" for state in states) or any(
        not _matches(path, deployment.rendered) for path, deployment in zip(paths, deployments, strict=True)
    ):
        return _status(
            "conflict",
            "common-dir Git Hook bundle is not the exact LDVH deployment requested for removal",
            worktree=current,
            common_dir=common_dir,
            hook_directory=hooks,
            worktrees=worktrees,
        )
    originals = {deployment.name: path.read_bytes() for path, deployment in zip(paths, deployments, strict=True)}
    failures: list[str] = []
    for path, deployment in zip(paths, deployments, strict=True):
        failure = _remove_exact(path, deployment.rendered)
        if failure is not None:
            failures.append(failure)
            break
    if failures:
        failures.extend(
            failure
            for deployment in deployments
            if (failure := _restore_hook_bytes(hooks / deployment.name, originals[deployment.name])) is not None
        )
        return _status(
            "unavailable",
            "; ".join(failures),
            worktree=current,
            common_dir=common_dir,
            hook_directory=hooks,
            worktrees=worktrees,
        )
    return _status(
        "absent",
        "the exact LDVH common-dir Git Hook bundle was removed",
        worktree=current,
        common_dir=common_dir,
        hook_directory=hooks,
        worktrees=worktrees,
    )


def _write_status(status: CommitMsgHookStatus) -> None:
    values = (
        ("state", status.state),
        ("detail", status.detail),
        ("worktree_root", status.worktree_root or ""),
        ("git_common_dir", status.git_common_dir or ""),
        ("hook_directory", status.hook_directory or ""),
        ("hook_path", status.hook_path or ""),
        ("worktree_roots", "\t".join(status.worktree_roots)),
    )
    for key, value in values:
        sys.stdout.write(f"{key}={value}\n")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage the LDVH common-dir native Git commit-msg Hook")
    commands = parser.add_subparsers(dest="command", required=True)
    inspect = commands.add_parser("inspect")
    inspect.add_argument("--worktree", required=True)
    for name in ("install", "bootstrap", "uninstall"):
        command = commands.add_parser(name)
        command.add_argument("--worktree", required=True)
        command.add_argument("--workspace-root", required=True)
        command.add_argument("--commit-msg-runner", required=True)
        command.add_argument("--confirm-human-gate", action="store_true")
    return parser


def main(arguments: list[str] | None = None) -> int:
    parsed = _parser().parse_args(arguments)
    if parsed.command == "inspect":
        status = inspect_commit_msg_hook(worktree=parsed.worktree)
    else:
        function = uninstall_commit_msg_hook if parsed.command == "uninstall" else install_commit_msg_hook
        status = function(
            worktree=parsed.worktree,
            workspace_root=parsed.workspace_root,
            commit_msg_runner=parsed.commit_msg_runner,
            human_gate_confirmed=parsed.confirm_human_gate,
        )
    _write_status(status)
    if parsed.command == "uninstall":
        return 0 if status.state == "absent" else 1
    return 0 if status.state == "managed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
