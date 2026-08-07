"""Shared Git commit precheck for Helper and native Git Gate entrypoints."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Literal

from ldvh.commits.contract_source import ATTACHMENT_KEY, CommitContractProjection, project_commit_contract
from ldvh.commits.git_adapter import CommitCandidateObservation, observe_commit_candidate
from ldvh.commits.validation import CommitValidationResult, validate_commit
from ldvh.facts.schema import project_fact_schemas
from ldvh.governance.models import LocatorSource, ScopeDescriptor
from ldvh.governance.resolver import GovernanceResolutionRun, resolve_governance_scope
from ldvh.specs.repository import RepositoryInspection

PrecheckStage = Literal["source", "governance", "candidate", "validation"]


@dataclass(frozen=True, slots=True)
class CommitPrecheckIssue:
    """One stable diagnostic from the shared precheck orchestration."""

    stage: PrecheckStage
    code: str
    message: str


@dataclass(frozen=True, slots=True)
class CommitPrecheckResult:
    """Bound result before either public entrypoint maps its own effects."""

    contract: CommitContractProjection | None
    governance_run: GovernanceResolutionRun | None
    observation: CommitCandidateObservation | None
    validation: CommitValidationResult | None
    issues: tuple[CommitPrecheckIssue, ...]

    @property
    def completed(self) -> bool:
        return self.validation is not None

    @property
    def mechanical_outcome(self) -> Literal["passed", "failed", "unverifiable"]:
        return "unverifiable" if self.validation is None else self.validation.outcome


def _issue(stage: PrecheckStage, code: str, message: str) -> CommitPrecheckIssue:
    return CommitPrecheckIssue(stage, code, message)


def precheck_git_commit(
    *,
    repository: RepositoryInspection,
    locator: str,
    base: Path,
    workspace_root: Path | None,
    message: str,
    index_file: Path | None = None,
) -> CommitPrecheckResult:
    """Apply the single source/governance/Index/validator chain without writes.

    ``index_file`` is an internal trust-boundary input.  Native Git or the
    internal commit executor may provide an event-owned Index.  The Helper
    public operation deliberately never exposes this argument.
    """

    document = repository.document_passing_implemented_checks_by_key("source-of-truth-traceability")
    if document is None:
        issue = _issue("source", "source_unavailable", "当前规则源没有通过检查的 active 03 提交契约")
        return CommitPrecheckResult(None, None, None, None, (issue,))

    attachment = repository.document_passing_implemented_checks_by_key(ATTACHMENT_KEY)
    projected = project_commit_contract(document, attachment)
    if projected.projection is None:
        issues = tuple(
            _issue("source", "contract_projection_unavailable", item.summary) for item in projected.issues
        ) or (_issue("source", "contract_projection_unavailable", "03 提交契约无法形成确定性投影"),)
        return CommitPrecheckResult(None, None, None, None, issues)
    contract = projected.projection

    requested_scope = (ScopeDescriptor(0, locator, LocatorSource.EXPLICIT_LOCATOR),)
    governance_run = resolve_governance_scope(
        requested_scope,
        base=base,
        explicit_workspace_root=workspace_root,
    )
    if governance_run.result is None:
        issues = tuple(
            _issue("governance", "governance_unavailable", item.summary) for item in governance_run.diagnostics
        ) or (_issue("governance", "governance_unavailable", "管辖解析没有形成可信结果"),)
        return CommitPrecheckResult(contract, governance_run, None, None, issues)

    observation = observe_commit_candidate(
        locator=locator,
        base=base,
        message=message,
        contract=contract,
        governance=governance_run.result,
        index_file=index_file,
    )
    if observation.outcome != "observed" or observation.validation_input is None:
        issues = tuple(_issue("candidate", item.stage, item.message) for item in observation.issues) or (
            _issue("candidate", observation.outcome, "Git 候选观察没有形成可信校验输入"),
        )
        return CommitPrecheckResult(contract, governance_run, observation, None, issues)

    validation_input = observation.validation_input
    if validation_input.fact_candidates:
        # Lazy per specs 03 §9.9: the fact Schema projection is derived from
        # the same current rule source only when staged fact candidates exist.
        schemas = project_fact_schemas(repository)
        validation_input = replace(validation_input, fact_schemas=tuple(schemas.values()))
    validation = validate_commit(contract, validation_input)
    issues = tuple(_issue("validation", item.code, item.message) for item in validation.issues)
    return CommitPrecheckResult(contract, governance_run, observation, validation, issues)


__all__ = [
    "CommitPrecheckIssue",
    "CommitPrecheckResult",
    "precheck_git_commit",
]
