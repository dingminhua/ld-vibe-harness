"""Pure Git commit-contract projection and validation."""

from ldvh.commits.contract_source import CommitContractProjection, project_commit_contract
from ldvh.commits.git_adapter import CommitCandidateObservation, observe_commit_candidate
from ldvh.commits.precheck import CommitPrecheckResult, precheck_git_commit
from ldvh.commits.validation import CommitValidationInput, CommitValidationResult, validate_commit

__all__ = [
    "CommitContractProjection",
    "CommitCandidateObservation",
    "CommitPrecheckResult",
    "CommitValidationInput",
    "CommitValidationResult",
    "project_commit_contract",
    "observe_commit_candidate",
    "precheck_git_commit",
    "validate_commit",
]
