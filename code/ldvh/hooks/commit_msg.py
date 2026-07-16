"""Shared mechanical gate for a native Git ``commit-msg`` Hook."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import ldvh
from ldvh.commits.contract_source import CommitContractProjection, project_commit_contract
from ldvh.commits.git_adapter import CommitCandidateObservation, observe_commit_candidate
from ldvh.commits.validation import CommitValidationResult, validate_commit
from ldvh.governance.models import LocatorSource, ScopeDescriptor
from ldvh.governance.resolver import GovernanceResolutionRun, resolve_governance_scope
from ldvh.helper.rule_source import inspect_colocated_repository

GateOutcome = Literal["passed", "failed", "unverifiable"]


class CommitMsgHookError(ValueError):
    """The native Git event could not be bound to the current LDVH contract."""


@dataclass(frozen=True, slots=True)
class CommitMsgGateResult:
    """Internal result for one Git-provided message and candidate Index."""

    outcome: GateOutcome
    issues: tuple[str, ...]

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


def _load_contract() -> CommitContractProjection:
    inspected = inspect_colocated_repository(Path(ldvh.__file__))
    if inspected.problem is not None or inspected.repository is None:
        raise CommitMsgHookError(f"current LDVH rule source is unavailable: {inspected.problem or 'unknown problem'}")
    document = inspected.repository.document_passing_implemented_checks_by_key("source-of-truth-traceability")
    if document is None:
        raise CommitMsgHookError("current LDVH rule source does not provide one active 03 document")
    projection = project_commit_contract(document)
    if projection.projection is None:
        details = "; ".join(issue.summary for issue in projection.issues) or "unknown projection problem"
        raise CommitMsgHookError(f"03 commit contract is unavailable: {details}")
    return projection.projection


def _resolve_governance(worktree: Path, workspace_root: Path):
    run: GovernanceResolutionRun = resolve_governance_scope(
        (ScopeDescriptor(0, str(worktree), LocatorSource.EXPLICIT_LOCATOR),),
        base=worktree,
        explicit_workspace_root=workspace_root,
    )
    if run.result is None:
        details = "; ".join(item.summary for item in run.diagnostics) or "governance resolution did not complete"
        raise CommitMsgHookError(f"governance is unavailable: {details}")
    return run.result


def _observation_result(observation: CommitCandidateObservation) -> CommitMsgGateResult:
    if observation.outcome == "observed" and observation.validation_input is not None:
        raise AssertionError("observed candidates must be handled with the current contract")
    details = tuple(f"{item.stage}: {item.message}" for item in observation.issues)
    return CommitMsgGateResult("unverifiable", details or (f"candidate observation was {observation.outcome}",))


def _validation_result(value: CommitValidationResult) -> CommitMsgGateResult:
    return CommitMsgGateResult(
        value.outcome,
        tuple(f"{item.code}: {item.message}" for item in value.issues),
    )


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

    contract = _load_contract()
    governance = _resolve_governance(current_worktree, workspace)
    observation = observe_commit_candidate(
        locator=str(current_worktree),
        base=current_worktree,
        message=message,
        contract=contract,
        governance=governance,
        index_file=active_index,
    )
    if observation.outcome != "observed" or observation.validation_input is None:
        return _observation_result(observation)
    return _validation_result(validate_commit(contract, observation.validation_input))


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
