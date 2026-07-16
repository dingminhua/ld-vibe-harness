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

from ldvh.governance.git import resolve_git_identity

_MANAGED_MARKER_PREFIX = "# ldvh-native-commit-msg-hook: v1 sha256:"
_GIT_TIMEOUT_SECONDS = 10
HookState = Literal["absent", "managed", "conflict", "unavailable"]


@dataclass(frozen=True, slots=True)
class CommitMsgHookStatus:
    """Current local ownership state of the one native Git Hook file."""

    state: HookState
    detail: str
    worktree_root: str | None
    hook_directory: str | None
    hook_path: str | None


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
    blocked = {
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_CEILING_DIRECTORIES",
        "GIT_COMMON_DIR",
        "GIT_DIR",
        "GIT_DISCOVERY_ACROSS_FILESYSTEM",
        "GIT_IMPLICIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_WORK_TREE",
    }
    environment = {key: value for key, value in os.environ.items() if key not in blocked}
    environment.update({"GIT_TERMINAL_PROMPT": "0", "LC_ALL": "C"})
    return environment


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


def _configured_hooks_path(worktree: Path) -> tuple[bool | None, str | None]:
    try:
        completed = subprocess.run(
            ("git", "-C", str(worktree), "config", "--show-origin", "--show-scope", "--get-all", "core.hooksPath"),
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
        return False, None
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip() or str(completed.returncode)
        return None, f"Git configuration inspection failed: {detail}"
    return True, "core.hooksPath is already configured and will not be modified or used by this installer"


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


def _hook_directory(worktree: Path) -> tuple[Path | None, str | None]:
    if _has_runtime_config_injection():
        return None, "runtime Git config injection is not accepted for Hook installation"
    configured, failure = _configured_hooks_path(worktree)
    if failure is not None:
        return None, failure
    if configured:
        return None, "core.hooksPath is already configured and will not be modified or used by this installer"
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
    if not _within(directory, worktree):
        return None, "effective hooks directory is outside this worktree; no shared or external Hook is changed"
    if directory.exists() and not directory.is_dir():
        return None, "effective hooks directory exists but is not a directory"
    return directory, None


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


def install_commit_msg_hook(
    *,
    worktree: str,
    workspace_root: str,
    commit_msg_runner: str,
    human_gate_confirmed: bool,
) -> CommitMsgHookStatus:
    """Install or refresh only an LDVH-owned adapter after a Human Gate."""

    status = inspect_commit_msg_hook(worktree=worktree)
    if not human_gate_confirmed:
        return CommitMsgHookStatus(
            "unavailable",
            "Human authorization is required before installing a native Git Hook",
            status.worktree_root,
            status.hook_directory,
            status.hook_path,
        )
    if status.state not in {"absent", "managed"}:
        return status
    try:
        workspace = _absolute_directory(workspace_root, "workspace_root")
        runner = _executable(commit_msg_runner)
        assert status.hook_path is not None
        rendered = render_commit_msg_hook(commit_msg_runner=runner, workspace_root=workspace)
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


def uninstall_commit_msg_hook(*, worktree: str, human_gate_confirmed: bool) -> CommitMsgHookStatus:
    """Remove only a regular Hook file that still carries LDVH's exact marker."""

    status = inspect_commit_msg_hook(worktree=worktree)
    if not human_gate_confirmed:
        return CommitMsgHookStatus(
            "unavailable",
            "Human authorization is required before removing a native Git Hook",
            status.worktree_root,
            status.hook_directory,
            status.hook_path,
        )
    if status.state != "managed":
        return status
    assert status.hook_path is not None
    try:
        Path(status.hook_path).unlink()
    except OSError as error:
        return CommitMsgHookStatus(
            "unavailable",
            f"LDVH commit-msg Hook was not removed: {error}",
            status.worktree_root,
            status.hook_directory,
            status.hook_path,
        )
    return inspect_commit_msg_hook(worktree=worktree)


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
    uninstall = commands.add_parser("uninstall", help="remove only an LDVH-owned commit-msg Hook")
    uninstall.add_argument("--worktree", required=True)
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
    status = uninstall_commit_msg_hook(
        worktree=parsed.worktree,
        human_gate_confirmed=parsed.confirm_human_gate,
    )
    _write_status(status)
    return 0 if status.state == "absent" else 1


if __name__ == "__main__":
    raise SystemExit(main())
