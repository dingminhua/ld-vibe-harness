"""Pure Git commit-contract projection and validation."""

from ldvh.commits.candidate_index import (
    CandidatePreparationResult,
    PreparedCommitCandidate,
    discard_prepared_candidate,
    prepare_commit_candidate,
)
from ldvh.commits.contract_source import CommitContractProjection, project_commit_contract
from ldvh.commits.execution import CallerCommitApproval, CommitExecutionResult, execute_prepared_commit
from ldvh.commits.git_adapter import CommitCandidateObservation, observe_commit_candidate
from ldvh.commits.precheck import CommitPrecheckResult, precheck_git_commit
from ldvh.commits.validation import CommitValidationInput, CommitValidationResult, validate_commit

__all__ = [
    "CommitContractProjection",
    "CommitCandidateObservation",
    "CommitPrecheckResult",
    "CandidatePreparationResult",
    "CallerCommitApproval",
    "CommitExecutionResult",
    "CommitValidationInput",
    "CommitValidationResult",
    "PreparedCommitCandidate",
    "discard_prepared_candidate",
    "execute_prepared_commit",
    "prepare_commit_candidate",
    "project_commit_contract",
    "observe_commit_candidate",
    "precheck_git_commit",
    "validate_commit",
]
