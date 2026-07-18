"""Shared mechanical gate for a native Git ``commit-msg`` Hook."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import ldvh
from ldvh.commits.precheck import precheck_git_commit
from ldvh.helper.rule_source import inspect_colocated_repository

GateOutcome = Literal["passed", "failed", "unverifiable"]


class CommitMsgHookError(ValueError):
    """The native Git event could not be bound to the current LDVH contract."""


@dataclass(frozen=True, slots=True)
class CommitMsgGateResult:
    """Internal result for one Git-provided message and candidate Index."""

    outcome: GateOutcome
    issues: tuple[str, ...]
    source_fingerprint: str | None = None
    snapshot_identity: str | None = None

    @property
    def allowed(self) -> bool:
        return self.outcome == "passed"


def _absolute_directory(value: str, field: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise CommitMsgHookError(f"{field} must be a non-empty absolute directory path")
    path = Path(value)
    if not path.is_absolute():
        raise CommitMsgHookError(f"{field} must be an absolute directory path")
    try:
        resolved = path.resolve(strict=True)
    except OSError as error:
        raise CommitMsgHookError(f"{field} could not be resolved: {error}") from error
    if not resolved.is_dir():
        raise CommitMsgHookError(f"{field} does not identify a current directory")
    return resolved


def _absolute_file(value: str, field: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise CommitMsgHookError(f"{field} must be a non-empty absolute file path")
    path = Path(value)
    if not path.is_absolute():
        raise CommitMsgHookError(f"{field} must be an absolute file path")
    try:
        resolved = path.resolve(strict=True)
    except OSError as error:
        raise CommitMsgHookError(f"{field} could not be resolved: {error}") from error
    if not resolved.is_file():
        raise CommitMsgHookError(f"{field} does not identify a current file")
    return resolved


def run_commit_msg_gate(
    *,
    workspace_root: str,
    worktree: str,
    message_file: str,
    index_file: str | None = None,
) -> CommitMsgGateResult:
    """Apply only 03's mechanical contract to the current native Git event."""

    workspace = _absolute_directory(workspace_root, "workspace_root")
    current_worktree = _absolute_directory(worktree, "worktree")
    message_path = _absolute_file(message_file, "message_file")
    active_index = None if index_file is None else _absolute_file(index_file, "index_file")
    try:
        message = message_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise CommitMsgHookError(f"message_file could not be read as UTF-8: {error}") from error

    inspected = inspect_colocated_repository(Path(ldvh.__file__))
    if inspected.problem is not None or inspected.repository is None:
        raise CommitMsgHookError(f"current LDVH rule source is unavailable: {inspected.problem or 'unknown problem'}")
    result = precheck_git_commit(
        repository=inspected.repository,
        locator=str(current_worktree),
        base=current_worktree,
        workspace_root=workspace,
        message=message,
        index_file=active_index,
    )
    return CommitMsgGateResult(
        result.mechanical_outcome,
        tuple(f"{item.stage}/{item.code}: {item.message}" for item in result.issues),
        None if result.contract is None else result.contract.content_fingerprint,
        None if result.observation is None else result.observation.snapshot_identity,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the LDVH native Git commit-msg mechanical gate")
    parser.add_argument("--workspace-root", required=True)
    parser.add_argument("--worktree", required=True)
    parser.add_argument("--message-file", required=True)
    parser.add_argument("--index-file")
    return parser


def _write_failure(result: CommitMsgGateResult) -> None:
    sys.stderr.write(f"LDVH commit-msg gate {result.outcome}:\n")
    for issue in result.issues:
        sys.stderr.write(f"- {issue}\n")


def main(arguments: list[str] | None = None) -> int:
    parsed = _parser().parse_args(arguments)
    try:
        result = run_commit_msg_gate(
            workspace_root=parsed.workspace_root,
            worktree=parsed.worktree,
            message_file=parsed.message_file,
            index_file=parsed.index_file,
        )
    except Exception as error:  # native lifecycle failures must never become an allow decision
        sys.stderr.write(f"LDVH commit-msg gate unavailable: {error}\n")
        return 1
    if result.allowed:
        return 0
    _write_failure(result)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
