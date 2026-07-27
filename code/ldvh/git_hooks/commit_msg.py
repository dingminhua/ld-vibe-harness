"""Install a thin native Git ``commit-msg`` adapter without taking over Git config."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import os
import shlex
import stat
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from ldvh.governance.git import isolated_git_environment, resolve_git_identity
from ldvh.governance.models import LocatorSource, ScopeDescriptor, ScopeStatus
from ldvh.governance.resolver import resolve_governance_scope

_MANAGED_MARKER_PREFIX = "# ldvh-native-commit-msg-hook: v1 sha256:"
_GIT_TIMEOUT_SECONDS = 10
_BOOTSTRAP_HOOKS_PATH = ".githooks-v4"
_TRUE_GIT_BOOLEAN_VALUES = frozenset(("1", "on", "true", "yes"))
HookState = Literal["absent", "managed", "conflict", "unavailable"]


@dataclass(frozen=True, slots=True)
class CommitMsgHookStatus:
    """Current local ownership state of the one native Git Hook file."""

    state: HookState
    detail: str
    worktree_root: str | None
    hook_directory: str | None
    hook_path: str | None


@dataclass(frozen=True, slots=True)
class _GitConfigEntry:
    """The one effective Git configuration value, including its actual scope."""

    scope: str
    origin: str
    value: str


class CommitMsgHookError(ValueError):
    """A requested install or removal cannot safely touch the target Hook."""


def _status(
    state: HookState,
    detail: str,
    *,
    worktree: Path | None = None,
    hook_directory: Path | None = None,
) -> CommitMsgHookStatus:
    hook_path = None if hook_directory is None else hook_directory / "commit-msg"
    return CommitMsgHookStatus(
        state=state,
        detail=detail,
        worktree_root=None if worktree is None else str(worktree),
        hook_directory=None if hook_directory is None else str(hook_directory),
        hook_path=None if hook_path is None else str(hook_path),
    )


def _has_runtime_config_injection() -> bool:
    return "GIT_CONFIG_COUNT" in os.environ or any(
        key.startswith(("GIT_CONFIG_KEY_", "GIT_CONFIG_VALUE_")) for key in os.environ
    )


def _installation_environment() -> dict[str, str]:
    return isolated_git_environment()


def _run_git(worktree: Path, *arguments: str) -> tuple[str | None, str | None]:
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
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip() or str(completed.returncode)
        return None, f"Git inspection failed: {detail}"
    return completed.stdout.strip(), None


def _effective_git_config(worktree: Path, key: str) -> tuple[_GitConfigEntry | None, str | None]:
    """Read one effective Git setting without guessing its scope or origin."""

    try:
        completed = subprocess.run(
            ("git", "-C", str(worktree), "config", "--null", "--show-origin", "--show-scope", "--get", key),
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
        return None, f"Git configuration inspection could not start: {error}"
    except subprocess.TimeoutExpired:
        return None, f"Git configuration inspection exceeded {_GIT_TIMEOUT_SECONDS} seconds"
    if completed.returncode == 1 and not completed.stdout and not completed.stderr:
        return None, None
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip() or str(completed.returncode)
        return None, f"Git configuration inspection failed: {detail}"
    fields = completed.stdout.split("\0")
    if fields and fields[-1] == "":
        fields.pop()
    if len(fields) != 3 or not all(fields):
        return None, f"Git configuration inspection returned an invalid effective {key} record"
    return _GitConfigEntry(*fields), None


def _configuration_origin_path(worktree: Path, origin: str) -> Path | None:
    if not origin.startswith("file:"):
        return None
    candidate = Path(origin.removeprefix("file:"))
    if not candidate.is_absolute():
        candidate = worktree / candidate
    try:
        return candidate.resolve(strict=False)
    except (OSError, RuntimeError):
        return None


def _configured_hooks_path(worktree: Path) -> tuple[_GitConfigEntry | None, str | None]:
    configured, failure = _effective_git_config(worktree, "core.hooksPath")
    if failure is not None or configured is None:
        return configured, failure
    if configured.scope != "worktree":
        return None, "effective core.hooksPath is not scoped to this actual worktree"
    expected_origin, failure = _run_git(
        worktree,
        "rev-parse",
        "--path-format=absolute",
        "--git-path",
        "config.worktree",
    )
    if failure is not None or expected_origin is None:
        return None, failure
    try:
        expected = Path(expected_origin).resolve(strict=False)
    except (OSError, RuntimeError) as error:
        return None, f"worktree Git configuration path could not be resolved: {error}"
    if _configuration_origin_path(worktree, configured.origin) != expected:
        return None, "effective core.hooksPath does not originate from this worktree's config.worktree"
    return configured, None


def _within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _worktree(value: str) -> tuple[Path | None, str | None]:
    if not isinstance(value, str) or not value.strip():
        return None, "worktree must be a non-empty absolute path"
    requested = Path(value)
    if not requested.is_absolute():
        return None, "worktree must be an absolute path"
    identity = resolve_git_identity(str(requested), base=requested)
    if identity.status != "git_worktree" or identity.identity is None:
        detail = identity.failure.summary if identity.failure is not None else identity.non_worktree_reason
        return None, f"worktree is not an available non-bare Git worktree: {detail}"
    return identity.identity.worktree_root, None


def _effective_hooks_directory(worktree: Path, *, require_within_worktree: bool) -> tuple[Path | None, str | None]:
    output, failure = _run_git(worktree, "rev-parse", "--path-format=absolute", "--git-path", "hooks")
    if failure is not None or output is None:
        return None, failure
    candidate = Path(output)
    if not candidate.is_absolute():
        return None, "Git did not return an absolute effective hooks directory"
    try:
        directory = candidate.resolve(strict=False)
    except (OSError, RuntimeError) as error:
        return None, f"effective hooks directory could not be resolved: {error}"
    if candidate != directory:
        return None, "effective hooks directory must not traverse a symbolic link"
    if require_within_worktree and not _within(directory, worktree):
        return None, "effective hooks directory is outside this worktree; no shared or external Hook is changed"
    if directory.exists() and not directory.is_dir():
        return None, "effective hooks directory exists but is not a directory"
    return directory, None


def _hook_directory(worktree: Path) -> tuple[Path | None, str | None]:
    if _has_runtime_config_injection():
        return None, "runtime Git config injection is not accepted for Hook installation"
    configured, failure = _configured_hooks_path(worktree)
    if failure is not None:
        return None, failure
    return _effective_hooks_directory(worktree, require_within_worktree=True)


def _existing_hook_state(path: Path) -> tuple[HookState, str]:
    if path.is_symlink():
        return "conflict", "existing commit-msg Hook is a symbolic link and is not managed by LDVH"
    try:
        info = path.stat()
    except FileNotFoundError:
        return "absent", "no commit-msg Hook is installed at the effective Git Hook path"
    except OSError as error:
        return "unavailable", f"existing commit-msg Hook could not be inspected: {error}"
    if not stat.S_ISREG(info.st_mode):
        return "conflict", "existing commit-msg Hook is not a regular file"
    try:
        contents = path.read_bytes()
    except OSError as error:
        return "conflict", f"existing commit-msg Hook cannot be identified safely: {error}"
    prefix = b"#!/bin/sh\n"
    marker, delimiter, body = contents.removeprefix(prefix).partition(b"\n")
    expected_prefix = _MANAGED_MARKER_PREFIX.encode("ascii")
    if contents.startswith(prefix) and delimiter and marker.startswith(expected_prefix):
        observed = marker.removeprefix(expected_prefix)
        expected = hashlib.sha256(body).hexdigest().encode("ascii")
        if hmac.compare_digest(observed, expected):
            return "managed", "LDVH owns the current commit-msg Hook"
        return "conflict", "existing commit-msg Hook carries an invalid LDVH ownership digest"
    return "conflict", "an existing commit-msg Hook is not owned by LDVH"


def inspect_commit_msg_hook(*, worktree: str) -> CommitMsgHookStatus:
    """Read one effective Hook location without changing Git or the filesystem."""

    current_worktree, failure = _worktree(worktree)
    if failure is not None or current_worktree is None:
        return _status("unavailable", failure or "worktree is unavailable")
    directory, failure = _hook_directory(current_worktree)
    if failure is not None or directory is None:
        return _status("conflict", failure or "effective hooks directory is unavailable", worktree=current_worktree)
    state, detail = _existing_hook_state(directory / "commit-msg")
    return _status(state, detail, worktree=current_worktree, hook_directory=directory)


def _absolute_directory(value: str, field: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise CommitMsgHookError(f"{field} must be a non-empty absolute directory path")
    candidate = Path(value)
    if not candidate.is_absolute():
        raise CommitMsgHookError(f"{field} must be an absolute directory path")
    try:
        path = candidate.resolve(strict=True)
    except OSError as error:
        raise CommitMsgHookError(f"{field} could not be resolved: {error}") from error
    if not path.is_dir():
        raise CommitMsgHookError(f"{field} does not identify a current directory")
    if "\n" in str(path) or "\r" in str(path):
        raise CommitMsgHookError(f"{field} contains a newline and cannot be represented by the POSIX adapter")
    return path


def _executable(value: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise CommitMsgHookError("commit_msg_runner must be a non-empty absolute file path")
    candidate = Path(value)
    if not candidate.is_absolute():
        raise CommitMsgHookError("commit_msg_runner must be an absolute file path")
    try:
        path = candidate.resolve(strict=True)
    except OSError as error:
        raise CommitMsgHookError(f"commit_msg_runner could not be resolved: {error}") from error
    if not path.is_file() or not os.access(path, os.X_OK):
        raise CommitMsgHookError("commit_msg_runner must identify an executable file")
    if "\n" in str(path) or "\r" in str(path):
        raise CommitMsgHookError("commit_msg_runner contains a newline and cannot be represented by the POSIX adapter")
    return path


def render_commit_msg_hook(*, commit_msg_runner: Path, workspace_root: Path) -> str:
    """Render the complete POSIX adapter; it contains no LDVH rule data."""

    runner = shlex.quote(str(commit_msg_runner))
    workspace = shlex.quote(str(workspace_root))
    body = "\n".join(
        (
            "set -eu",
            'if [ "$#" -ne 1 ]; then',
            '  printf "%s\\n" "LDVH commit-msg Hook expected one message-file argument" >&2',
            "  exit 1",
            "fi",
            "worktree=$(git rev-parse --show-toplevel) || {",
            '  printf "%s\\n" "LDVH commit-msg Hook could not determine the current worktree" >&2',
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
            f'  exec {runner} --workspace-root {workspace} --worktree "$worktree" '
            f'--message-file "$message_file" --index-file "$index_file"',
            "fi",
            f'exec {runner} --workspace-root {workspace} --worktree "$worktree" --message-file "$message_file"',
            "",
        )
    )
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    return f"#!/bin/sh\n{_MANAGED_MARKER_PREFIX}{digest}\n{body}"


def _atomic_write(path: Path, content: str) -> None:
    directory = path.parent
    directory.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=".ldvh-commit-msg-", dir=directory)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
        temporary.chmod(0o755)
        state, detail = _existing_hook_state(path)
        if state not in {"absent", "managed"}:
            raise CommitMsgHookError(f"commit-msg Hook changed before installation: {detail}")
        os.replace(temporary, path)
    except Exception:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        raise


def _rendered_hook_matches(path: Path, rendered: str) -> tuple[bool | None, str | None]:
    if path.is_symlink():
        return None, "existing commit-msg Hook became a symbolic link"
    try:
        contents = path.read_bytes()
    except OSError as error:
        return None, f"existing commit-msg Hook could not be read: {error}"
    return hmac.compare_digest(contents, rendered.encode("utf-8")), None


def _remove_rendered_hook(path: Path, rendered: str) -> str | None:
    matches, failure = _rendered_hook_matches(path, rendered)
    if failure is not None:
        return failure
    if not matches:
        return "prepared commit-msg Hook changed before cleanup"
    try:
        path.unlink()
    except OSError as error:
        return f"prepared commit-msg Hook could not be removed: {error}"
    return None


def _governance_failure(worktree: Path, workspace: Path) -> str | None:
    run = resolve_governance_scope(
        (ScopeDescriptor(0, str(worktree), LocatorSource.EXPLICIT_LOCATOR),),
        base=worktree,
        explicit_workspace_root=workspace,
    )
    if run.result is None:
        details = "; ".join(item.summary for item in run.diagnostics) or "governance resolution did not complete"
        return f"actual worktree governance is unavailable: {details}"
    if run.result.scope_status is not ScopeStatus.GOVERNED_SINGLE:
        return f"actual worktree must resolve as governed_single, not {run.result.scope_status.value}"
    resolution = run.result.object_resolutions[0]
    if resolution.git_worktree_root is None:
        return "governance did not bind the actual Git worktree"
    try:
        governed_worktree = Path(resolution.git_worktree_root).resolve(strict=True)
    except OSError as error:
        return f"governance worktree identity could not be resolved: {error}"
    if governed_worktree != worktree:
        return "governance did not bind the requested actual Git worktree"
    return None


def _active_hook_assets(directory: Path, *, ignore: frozenset[str] = frozenset()) -> tuple[str, ...] | None:
    """Find active Hook assets that a new hooksPath would hide or begin running."""

    if not directory.exists():
        return ()
    if directory.is_symlink() or not directory.is_dir():
        return None
    try:
        entries = tuple(directory.iterdir())
    except OSError:
        return None
    active: list[str] = []
    for entry in entries:
        if entry.name in ignore or entry.name.endswith(".sample"):
            continue
        if entry.is_symlink() or (entry.is_file() and os.access(entry, os.X_OK)):
            active.append(entry.name)
    return tuple(sorted(active))


def _bootstrap_directory(worktree: Path) -> tuple[Path | None, str | None]:
    candidate = worktree / _BOOTSTRAP_HOOKS_PATH
    try:
        directory = candidate.resolve(strict=False)
    except (OSError, RuntimeError) as error:
        return None, f"worktree-local bootstrap Hook directory could not be resolved: {error}"
    if candidate != directory or not _within(directory, worktree):
        return (
            None,
            "worktree-local bootstrap Hook directory must remain inside the actual worktree without symbolic links",
        )
    if directory.exists() and not directory.is_dir():
        return None, "worktree-local bootstrap Hook directory exists but is not a directory"
    state, detail = _existing_hook_state(directory / "commit-msg")
    if state not in {"absent", "managed"}:
        return None, f"worktree-local bootstrap Hook directory cannot be activated safely: {detail}"
    active = _active_hook_assets(directory, ignore=frozenset({"commit-msg"}))
    if active is None:
        return None, "worktree-local bootstrap Hook directory cannot be inspected safely"
    if active:
        return None, "worktree-local bootstrap Hook directory contains active Hook assets: " + ", ".join(active)
    return directory, None


def _worktree_configuration_enabled(worktree: Path) -> tuple[bool, str | None]:
    configured, failure = _effective_git_config(worktree, "extensions.worktreeConfig")
    if failure is not None:
        return False, failure
    return configured is not None and configured.value.lower() in _TRUE_GIT_BOOLEAN_VALUES, None


def _configure_worktree_hooks_path(worktree: Path) -> str | None:
    enabled, failure = _worktree_configuration_enabled(worktree)
    if failure is not None:
        return failure
    if not enabled:
        return "extensions.worktreeConfig must already be true before a worktree-local Hook path can be configured"
    _, failure = _run_git(worktree, "config", "--worktree", "core.hooksPath", _BOOTSTRAP_HOOKS_PATH)
    return failure


def _rollback_bootstrap_attempt(
    *,
    worktree: Path,
    hook_path: Path,
    rendered: str,
    remove_prepared_hook: bool,
) -> str | None:
    """Undo only this attempt's exact configuration and prepared wrapper after a failed activation."""

    failures: list[str] = []
    configured, failure = _configured_hooks_path(worktree)
    if failure is not None:
        failures.append(f"worktree Hook configuration could not be re-read: {failure}")
    elif configured is not None:
        if configured.value != _BOOTSTRAP_HOOKS_PATH:
            failures.append("worktree Hook configuration changed before bootstrap cleanup")
        else:
            _, failure = _run_git(worktree, "config", "--worktree", "--unset-all", "core.hooksPath")
            if failure is not None:
                failures.append(f"worktree Hook configuration could not be removed: {failure}")
    if remove_prepared_hook:
        failure = _remove_rendered_hook(hook_path, rendered)
        if failure is not None:
            failures.append(failure)
    return None if not failures else "; ".join(failures)


def install_commit_msg_hook(
    *,
    worktree: str,
    workspace_root: str,
    commit_msg_runner: str,
    human_gate_confirmed: bool,
) -> CommitMsgHookStatus:
    """Install one exact LDVH-owned adapter after a Human Gate."""

    status = inspect_commit_msg_hook(worktree=worktree)
    if not human_gate_confirmed:
        return CommitMsgHookStatus(
            "unavailable",
            "Human authorization is required before installing a native Git Hook",
            status.worktree_root,
            status.hook_directory,
            status.hook_path,
        )
    try:
        workspace = _absolute_directory(workspace_root, "workspace_root")
        if status.worktree_root is None:
            raise CommitMsgHookError("actual worktree is unavailable")
        scope_failure = _governance_failure(Path(status.worktree_root), workspace)
        if scope_failure is not None:
            return CommitMsgHookStatus(
                "conflict",
                scope_failure,
                status.worktree_root,
                status.hook_directory,
                status.hook_path,
            )
        runner = _executable(commit_msg_runner)
        rendered = render_commit_msg_hook(commit_msg_runner=runner, workspace_root=workspace)
        if status.state == "managed":
            assert status.hook_path is not None
            matches, failure = _rendered_hook_matches(Path(status.hook_path), rendered)
            if failure is not None:
                return CommitMsgHookStatus(
                    "unavailable",
                    f"LDVH commit-msg Hook binding could not be verified: {failure}",
                    status.worktree_root,
                    status.hook_directory,
                    status.hook_path,
                )
            if matches:
                return status
            return CommitMsgHookStatus(
                "conflict",
                "existing LDVH commit-msg Hook has a different runner or workspace binding and will not be replaced",
                status.worktree_root,
                status.hook_directory,
                status.hook_path,
            )
        if status.state != "absent":
            return status
        assert status.hook_path is not None
        _atomic_write(Path(status.hook_path), rendered)
    except (CommitMsgHookError, OSError) as error:
        return CommitMsgHookStatus(
            "unavailable",
            f"LDVH commit-msg Hook was not installed: {error}",
            status.worktree_root,
            status.hook_directory,
            status.hook_path,
        )
    return inspect_commit_msg_hook(worktree=worktree)


def bootstrap_commit_msg_hook(
    *,
    worktree: str,
    workspace_root: str,
    commit_msg_runner: str,
    human_gate_confirmed: bool,
) -> CommitMsgHookStatus:
    """Create one safe worktree-local Hook path, then install the shared thin adapter."""

    status = inspect_commit_msg_hook(worktree=worktree)
    if not human_gate_confirmed:
        return CommitMsgHookStatus(
            "unavailable",
            "Human authorization is required before bootstrapping a native Git Hook",
            status.worktree_root,
            status.hook_directory,
            status.hook_path,
        )
    current_worktree, failure = _worktree(worktree)
    if failure is not None or current_worktree is None:
        return _status("unavailable", failure or "worktree is unavailable")
    try:
        workspace = _absolute_directory(workspace_root, "workspace_root")
        runner = _executable(commit_msg_runner)
    except CommitMsgHookError as error:
        return _status("unavailable", str(error), worktree=current_worktree)
    scope_failure = _governance_failure(current_worktree, workspace)
    if scope_failure is not None:
        return _status("conflict", scope_failure, worktree=current_worktree)
    if _has_runtime_config_injection():
        return _status(
            "conflict",
            "runtime Git config injection is not accepted for Hook installation",
            worktree=current_worktree,
        )
    configured, failure = _effective_git_config(current_worktree, "core.hooksPath")
    if failure is not None:
        return _status("unavailable", failure, worktree=current_worktree)
    if configured is not None:
        return install_commit_msg_hook(
            worktree=worktree,
            workspace_root=str(workspace),
            commit_msg_runner=str(runner),
            human_gate_confirmed=True,
        )
    default_directory, failure = _effective_hooks_directory(current_worktree, require_within_worktree=False)
    if failure is not None or default_directory is None:
        return _status("unavailable", failure or "default hooks directory is unavailable", worktree=current_worktree)
    active = _active_hook_assets(default_directory)
    if active is None:
        return _status(
            "conflict",
            "default hooks directory cannot be inspected safely before configuring a worktree-local Hook path",
            worktree=current_worktree,
        )
    if active:
        return _status(
            "conflict",
            "default hooks directory contains active Hook assets and would be shadowed: " + ", ".join(active),
            worktree=current_worktree,
        )
    directory, failure = _bootstrap_directory(current_worktree)
    if failure is not None or directory is None:
        return _status("conflict", failure or "worktree-local Hook directory is unavailable", worktree=current_worktree)
    hook_path = directory / "commit-msg"
    rendered = render_commit_msg_hook(commit_msg_runner=runner, workspace_root=workspace)
    state, detail = _existing_hook_state(hook_path)
    prepared_by_attempt = False
    if state == "managed":
        matches, failure = _rendered_hook_matches(hook_path, rendered)
        if failure is not None:
            return _status(
                "unavailable",
                f"worktree-local bootstrap Hook binding could not be verified: {failure}",
                worktree=current_worktree,
                hook_directory=directory,
            )
        if not matches:
            return _status(
                "conflict",
                "worktree-local bootstrap Hook has a different runner or workspace binding and will not be activated",
                worktree=current_worktree,
                hook_directory=directory,
            )
    elif state == "absent":
        try:
            _atomic_write(hook_path, rendered)
        except (CommitMsgHookError, OSError) as error:
            return _status(
                "unavailable",
                f"worktree-local bootstrap Hook was not prepared: {error}",
                worktree=current_worktree,
                hook_directory=directory,
            )
        prepared_by_attempt = True
    else:
        return _status(
            state,
            f"worktree-local bootstrap Hook cannot be activated safely: {detail}",
            worktree=current_worktree,
            hook_directory=directory,
        )
    failure = _configure_worktree_hooks_path(current_worktree)
    if failure is not None:
        cleanup = _rollback_bootstrap_attempt(
            worktree=current_worktree,
            hook_path=hook_path,
            rendered=rendered,
            remove_prepared_hook=prepared_by_attempt,
        )
        detail = f"worktree-local Hook configuration was not activated: {failure}"
        if cleanup is not None:
            detail += f"; cleanup incomplete: {cleanup}"
        return _status("unavailable", detail, worktree=current_worktree, hook_directory=directory)
    configured, failure = _configured_hooks_path(current_worktree)
    if failure is not None or configured is None or configured.value != _BOOTSTRAP_HOOKS_PATH:
        detail = failure or "worktree-local core.hooksPath did not persist the expected value"
        cleanup = _rollback_bootstrap_attempt(
            worktree=current_worktree,
            hook_path=hook_path,
            rendered=rendered,
            remove_prepared_hook=prepared_by_attempt,
        )
        if cleanup is not None:
            detail += f"; cleanup incomplete: {cleanup}"
        return _status("unavailable", detail, worktree=current_worktree, hook_directory=directory)
    installed = install_commit_msg_hook(
        worktree=worktree,
        workspace_root=str(workspace),
        commit_msg_runner=str(runner),
        human_gate_confirmed=True,
    )
    if installed.state == "managed":
        return installed
    cleanup = _rollback_bootstrap_attempt(
        worktree=current_worktree,
        hook_path=hook_path,
        rendered=rendered,
        remove_prepared_hook=prepared_by_attempt,
    )
    detail = f"worktree-local Hook configuration did not verify after activation: {installed.detail}"
    if cleanup is not None:
        detail += f"; cleanup incomplete: {cleanup}"
    return _status("unavailable", detail, worktree=current_worktree, hook_directory=directory)


def uninstall_commit_msg_hook(
    *,
    worktree: str,
    workspace_root: str,
    commit_msg_runner: str,
    human_gate_confirmed: bool,
) -> CommitMsgHookStatus:
    """Remove only the exact current environment binding after a Human Gate."""

    status = inspect_commit_msg_hook(worktree=worktree)
    if not human_gate_confirmed:
        return CommitMsgHookStatus(
            "unavailable",
            "Human authorization is required before removing a native Git Hook",
            status.worktree_root,
            status.hook_directory,
            status.hook_path,
        )
    try:
        workspace = _absolute_directory(workspace_root, "workspace_root")
        if status.worktree_root is None:
            raise CommitMsgHookError("actual worktree is unavailable")
        scope_failure = _governance_failure(Path(status.worktree_root), workspace)
        if scope_failure is not None:
            return CommitMsgHookStatus(
                "conflict",
                scope_failure,
                status.worktree_root,
                status.hook_directory,
                status.hook_path,
            )
        if status.state != "managed":
            return status
        runner = _executable(commit_msg_runner)
        assert status.hook_path is not None
        rendered = render_commit_msg_hook(commit_msg_runner=runner, workspace_root=workspace)
        matches, failure = _rendered_hook_matches(Path(status.hook_path), rendered)
        if failure is not None:
            return CommitMsgHookStatus(
                "unavailable",
                f"LDVH commit-msg Hook binding could not be verified: {failure}",
                status.worktree_root,
                status.hook_directory,
                status.hook_path,
            )
        if not matches:
            return CommitMsgHookStatus(
                "conflict",
                "existing LDVH commit-msg Hook has a different runner or workspace binding and will not be removed",
                status.worktree_root,
                status.hook_directory,
                status.hook_path,
            )
        Path(status.hook_path).unlink()
    except (CommitMsgHookError, OSError) as error:
        return CommitMsgHookStatus(
            "unavailable",
            f"LDVH commit-msg Hook was not removed: {error}",
            status.worktree_root,
            status.hook_directory,
            status.hook_path,
        )
    removed = inspect_commit_msg_hook(worktree=worktree)
    if removed.state != "absent" or status.worktree_root is None:
        return removed
    configured, failure = _configured_hooks_path(Path(status.worktree_root))
    if failure is not None:
        return CommitMsgHookStatus(
            "unavailable",
            f"LDVH commit-msg Hook was removed, but retained Hook configuration could not be observed: {failure}",
            removed.worktree_root,
            removed.hook_directory,
            removed.hook_path,
        )
    if configured is None:
        return removed
    return CommitMsgHookStatus(
        "absent",
        removed.detail + "; effective worktree-local core.hooksPath remains unchanged",
        removed.worktree_root,
        removed.hook_directory,
        removed.hook_path,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect or manage one LDVH native Git commit-msg Hook")
    commands = parser.add_subparsers(dest="command", required=True)
    status = commands.add_parser("status", help="read the effective commit-msg Hook without changing it")
    status.add_argument("--worktree", required=True)
    install = commands.add_parser("install", help="install an LDVH-owned commit-msg Hook")
    install.add_argument("--worktree", required=True)
    install.add_argument("--workspace-root", required=True)
    install.add_argument("--commit-msg-runner", required=True)
    install.add_argument("--confirm-human-gate", action="store_true")
    bootstrap = commands.add_parser(
        "bootstrap",
        help="configure one safe worktree-local Hook path, then install an LDVH-owned commit-msg Hook",
    )
    bootstrap.add_argument("--worktree", required=True)
    bootstrap.add_argument("--workspace-root", required=True)
    bootstrap.add_argument("--commit-msg-runner", required=True)
    bootstrap.add_argument("--confirm-human-gate", action="store_true")
    uninstall = commands.add_parser("uninstall", help="remove only the exact LDVH-owned commit-msg Hook binding")
    uninstall.add_argument("--worktree", required=True)
    uninstall.add_argument("--workspace-root", required=True)
    uninstall.add_argument("--commit-msg-runner", required=True)
    uninstall.add_argument("--confirm-human-gate", action="store_true")
    return parser


def _write_status(status: CommitMsgHookStatus) -> None:
    sys.stdout.write(f"LDVH commit-msg Hook {status.state}: {status.detail}\n")
    if status.worktree_root is not None:
        sys.stdout.write(f"worktree: {status.worktree_root}\n")
    if status.hook_path is not None:
        sys.stdout.write(f"hook: {status.hook_path}\n")


def main(arguments: list[str] | None = None) -> int:
    parsed = _parser().parse_args(arguments)
    if parsed.command == "status":
        status = inspect_commit_msg_hook(worktree=parsed.worktree)
        _write_status(status)
        return 0 if status.state in {"absent", "managed"} else 1
    if parsed.command == "install":
        status = install_commit_msg_hook(
            worktree=parsed.worktree,
            workspace_root=parsed.workspace_root,
            commit_msg_runner=parsed.commit_msg_runner,
            human_gate_confirmed=parsed.confirm_human_gate,
        )
        _write_status(status)
        return 0 if status.state == "managed" else 1
    if parsed.command == "bootstrap":
        status = bootstrap_commit_msg_hook(
            worktree=parsed.worktree,
            workspace_root=parsed.workspace_root,
            commit_msg_runner=parsed.commit_msg_runner,
            human_gate_confirmed=parsed.confirm_human_gate,
        )
        _write_status(status)
        return 0 if status.state == "managed" else 1
    status = uninstall_commit_msg_hook(
        worktree=parsed.worktree,
        workspace_root=parsed.workspace_root,
        commit_msg_runner=parsed.commit_msg_runner,
        human_gate_confirmed=parsed.confirm_human_gate,
    )
    _write_status(status)
    return 0 if status.state == "absent" else 1


if __name__ == "__main__":
    raise SystemExit(main())
