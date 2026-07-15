"""Resolve work objects against the current governed-projects configuration.

The resolver is deliberately below the Helper service boundary.  It returns an
immutable runtime record that keeps domain completion separate from technical
non-completion; callers remain responsible for constructing the common Helper
response and selecting its outer outcome.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from types import MappingProxyType
from typing import Any

from ldvh.governance.configuration import (
    ConfigurationAccessError,
    ConfigurationDiagnostic,
    ConfigurationReadResult,
    ConfigurationStatus,
    GovernedProjectRegistration,
    read_governed_projects_configuration,
)
from ldvh.governance.git import (
    GitIdentityResolution,
    GitWorktreeIdentity,
    TechnicalFailure,
    resolve_git_identity,
    windows_path_problem,
)
from ldvh.governance.models import (
    ConfigStatus,
    GovernanceScopeResult,
    GovernedVia,
    ObjectResolution,
    ObjectStatus,
    ScopeDescriptor,
)

type SourceReference = Mapping[str, Any]


class TechnicalOutcome(StrEnum):
    """Service-level classification of a scope that could not be completed."""

    UNAVAILABLE = "unavailable"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class TechnicalNonCompletion:
    outcome: TechnicalOutcome
    stage: str
    summary: str
    scope: tuple[ScopeDescriptor, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "scope", tuple(self.scope))


@dataclass(frozen=True, slots=True)
class ResolutionGap:
    summary: str
    scope: tuple[ScopeDescriptor, ...]
    source_refs: tuple[SourceReference, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "scope", tuple(self.scope))
        object.__setattr__(self, "source_refs", _freeze_sources(self.source_refs))


@dataclass(frozen=True, slots=True)
class ResolutionDiagnostic:
    stage: str
    summary: str
    scope: tuple[ScopeDescriptor, ...]
    source_refs: tuple[SourceReference, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "scope", tuple(self.scope))
        object.__setattr__(self, "source_refs", _freeze_sources(self.source_refs))


@dataclass(frozen=True, slots=True)
class GovernanceResolutionRun:
    """Complete internal output, including any service-level unfinished scope."""

    result: GovernanceScopeResult | None
    requested_scope: tuple[ScopeDescriptor, ...]
    completed_scope: tuple[ScopeDescriptor, ...]
    technical_non_completions: tuple[TechnicalNonCompletion, ...]
    sources: tuple[SourceReference, ...]
    gaps: tuple[ResolutionGap, ...]
    diagnostics: tuple[ResolutionDiagnostic, ...]

    def __post_init__(self) -> None:
        requested = tuple(self.requested_scope)
        completed = tuple(self.completed_scope)
        requested_by_index = {item.locator_index: item for item in requested}
        if len(requested_by_index) != len(requested):
            raise ValueError("requested_scope locator indexes must be unique")
        if any(requested_by_index.get(item.locator_index) != item for item in completed):
            raise ValueError("completed_scope must be a subset of requested_scope")
        object.__setattr__(self, "requested_scope", requested)
        object.__setattr__(self, "completed_scope", completed)
        object.__setattr__(self, "technical_non_completions", tuple(self.technical_non_completions))
        object.__setattr__(self, "sources", _freeze_sources(self.sources))
        object.__setattr__(self, "gaps", tuple(self.gaps))
        object.__setattr__(self, "diagnostics", tuple(self.diagnostics))

    @property
    def not_completed_scope(self) -> tuple[ScopeDescriptor, ...]:
        completed_indexes = {item.locator_index for item in self.completed_scope}
        return tuple(item for item in self.requested_scope if item.locator_index not in completed_indexes)


@dataclass(frozen=True, slots=True)
class _ValidatedProject:
    registration: GovernedProjectRegistration
    identity: GitWorktreeIdentity


def resolve_governance_scope(
    requested_scope: Sequence[ScopeDescriptor],
    *,
    base: Path,
    explicit_workspace_root: Path | None = None,
) -> GovernanceResolutionRun:
    """Resolve every requested locator without reading target-project content."""

    requested = tuple(requested_scope)
    _validate_requested_scope(requested)
    if explicit_workspace_root is not None:
        path_problem = windows_path_problem(explicit_workspace_root)
        if path_problem is not None:
            return _global_technical_run(
                requested,
                TechnicalOutcome.ERROR,
                "configuration_discovery",
                f"The explicit workspace root is unsupported on Windows: {path_problem}",
                (),
            )
    observed_at = datetime.now(UTC).astimezone().isoformat(timespec="seconds")
    observations = tuple((item, resolve_git_identity(item.locator, base=base)) for item in requested)
    observation_sources = tuple(
        source for item, observation in observations for source in _observation_sources(item, observation, observed_at)
    )

    path_starts = tuple(
        observation.path.probe_path for _, observation in observations if observation.path.probe_path is not None
    )
    identities = tuple(
        observation.identity
        for _, observation in observations
        if observation.status == "git_worktree" and observation.identity is not None
    )
    common_parent_starts = tuple(identity.common_dir.parent for identity in identities)
    excluded_roots, exclusion_failures = _discovery_exclusions(observations)

    try:
        configuration = read_governed_projects_configuration(
            explicit_workspace_root=explicit_workspace_root,
            path_search_starts=path_starts,
            common_dir_parent_search_starts=common_parent_starts,
            excluded_worktree_roots=excluded_roots,
        )
    except ConfigurationAccessError:
        return _global_technical_run(
            requested,
            TechnicalOutcome.ERROR,
            "configuration_read",
            "The selected governed-projects configuration could not be read",
            observation_sources,
        )

    config_sources = _configuration_sources(configuration, observed_at, fallback=base)
    all_sources = _deduplicate_sources((*observation_sources, *config_sources))
    locator_failures = tuple((item, observation.failure) for item, observation in observations if observation.failure)

    # With automatic discovery, an unobserved Git identity can hide another
    # configuration route.  A conflict is already conclusive; every other
    # selection remains incomplete until all discovery routes are observed.
    if explicit_workspace_root is None and exclusion_failures:
        return _technical_run_for_failures(
            requested,
            exclusion_failures,
            all_sources,
            stage_prefix="configuration_discovery",
        )
    if (
        explicit_workspace_root is None
        and locator_failures
        and configuration.status is not ConfigurationStatus.CONFLICT
    ):
        return _technical_run_for_failures(
            requested,
            locator_failures,
            all_sources,
            stage_prefix="configuration_discovery",
        )

    if configuration.status is not ConfigurationStatus.VALID:
        return _non_valid_configuration_run(requested, observations, configuration, all_sources)

    assert configuration.configuration is not None
    validated_projects: list[_ValidatedProject] = []
    project_failures: list[tuple[ScopeDescriptor, TechnicalFailure]] = []
    project_sources: list[SourceReference] = []
    validation_diagnostics: list[ResolutionDiagnostic] = []
    structurally_invalid = False
    synthetic_scope = requested or ()
    for registration in configuration.configuration.projects:
        resolved = resolve_git_identity(str(registration.path), base=configuration.configuration.workspace_root)
        registration_sources = _registered_project_sources(registration, resolved, observed_at)
        project_sources.extend(registration_sources)
        if resolved.status == "technical_failure":
            assert resolved.failure is not None
            # Project validation affects every requested object because common-
            # dir uniqueness is a configuration-wide invariant.
            for item in synthetic_scope:
                project_failures.append((item, resolved.failure))
            continue
        if (
            resolved.status != "git_worktree"
            or resolved.identity is None
            or resolved.path.real_path != registration.path
            or resolved.identity.worktree_root != registration.path
        ):
            structurally_invalid = True
            validation_diagnostics.append(
                ResolutionDiagnostic(
                    stage="configuration_validation",
                    summary=f"Registered project {registration.project_id!r} is not an actual Git worktree root",
                    scope=requested,
                    source_refs=_deduplicate_sources((*config_sources, *registration_sources)),
                )
            )
            continue
        validated_projects.append(_ValidatedProject(registration, resolved.identity))

    all_sources = _deduplicate_sources((*all_sources, *project_sources))
    if project_failures:
        return _technical_run_for_failures(
            requested,
            tuple(project_failures),
            all_sources,
            stage_prefix="configuration_validation",
        )

    common_dirs = [project.identity.common_dir for project in validated_projects]
    if len(common_dirs) != len(set(common_dirs)):
        structurally_invalid = True
        validation_diagnostics.append(
            ResolutionDiagnostic(
                stage="configuration_validation",
                summary="Registered project Git common directories must be unique within the configuration",
                scope=requested,
                source_refs=config_sources,
            )
        )

    if structurally_invalid:
        invalid_configuration = replace(
            configuration,
            status=ConfigurationStatus.INVALID,
            configuration=None,
            diagnostics=(),
        )
        invalid_run = _non_valid_configuration_run(
            requested,
            observations,
            invalid_configuration,
            all_sources,
        )
        return replace(
            invalid_run,
            diagnostics=(*invalid_run.diagnostics, *validation_diagnostics),
        )

    resolutions: list[ObjectResolution] = []
    failures: list[tuple[ScopeDescriptor, TechnicalFailure]] = []
    gaps: list[ResolutionGap] = []
    diagnostics: list[ResolutionDiagnostic] = []
    for item, observation in observations:
        if observation.status == "technical_failure":
            assert observation.failure is not None
            failures.append((item, observation.failure))
            continue
        resolution = _resolve_object(item, observation, tuple(validated_projects), all_sources, observed_at)
        resolutions.append(resolution)
        if resolution.status is ObjectStatus.UNKNOWN:
            gaps.append(
                ResolutionGap(
                    resolution.unknown_reason or "Object governance is unknown",
                    (item,),
                    resolution.source_refs,
                )
            )

    domain_result = None
    completed = tuple(item.scope_descriptor for item in resolutions)
    if resolutions:
        domain_result = GovernanceScopeResult(
            workspace_root=str(configuration.workspace_root) if configuration.workspace_root else None,
            config_path=str(configuration.config_path) if configuration.config_path else None,
            config_status=ConfigStatus.VALID,
            object_resolutions=tuple(resolutions),
            source_refs=all_sources,
        )

    technical = _technical_non_completions(failures)
    for unfinished in technical:
        gaps.append(ResolutionGap(unfinished.summary, unfinished.scope, all_sources))
        diagnostics.append(ResolutionDiagnostic(unfinished.stage, unfinished.summary, unfinished.scope))
    return GovernanceResolutionRun(
        result=domain_result,
        requested_scope=requested,
        completed_scope=completed,
        technical_non_completions=technical,
        sources=all_sources,
        gaps=tuple(gaps),
        diagnostics=tuple(diagnostics),
    )


def _validate_requested_scope(requested: tuple[ScopeDescriptor, ...]) -> None:
    indexes = [item.locator_index for item in requested]
    if len(indexes) != len(set(indexes)):
        raise ValueError("requested_scope locator indexes must be unique")


def _discovery_exclusions(
    observations: Sequence[tuple[ScopeDescriptor, GitIdentityResolution]],
) -> tuple[tuple[Path, ...], tuple[tuple[ScopeDescriptor, TechnicalFailure], ...]]:
    observed_identities = tuple(
        (item, observation.identity)
        for item, observation in observations
        if observation.status == "git_worktree" and observation.identity is not None
    )
    roots = {identity.worktree_root for _, identity in observed_identities}
    failures: list[tuple[ScopeDescriptor, TechnicalFailure]] = []
    # For an external linked worktree, common_dir.parent is commonly the main
    # worktree root.  Observe it instead of inferring from a directory name, so
    # a repository-local configuration there is skipped while discovery keeps
    # walking toward an external workspace configuration.
    for item, identity in observed_identities:
        common_parent = identity.common_dir.parent
        metadata_ancestors = _git_metadata_ancestors(common_parent)
        roots.update(metadata_ancestors)
        metadata_root = next((path for path in metadata_ancestors if path.name == ".git"), None)
        candidate_root = metadata_root.parent if metadata_root is not None else common_parent
        if candidate_root in roots:
            continue
        observed_parent = resolve_git_identity(".", base=candidate_root)
        if observed_parent.status == "technical_failure":
            assert observed_parent.failure is not None
            failures.append((item, observed_parent.failure))
            continue
        if (
            observed_parent.status == "git_worktree"
            and observed_parent.identity is not None
            and observed_parent.identity.worktree_root == candidate_root
        ):
            roots.add(candidate_root)
    return tuple(sorted(roots, key=str)), tuple(failures)


def _git_metadata_ancestors(start: Path) -> tuple[Path, ...]:
    """Exclude candidates inside a conventional ``.git`` metadata tree."""

    ancestors = (start, *start.parents)
    git_metadata_root = next((path for path in ancestors if path.name == ".git"), None)
    if git_metadata_root is None:
        return ()
    return tuple(path for path in ancestors if path == git_metadata_root or git_metadata_root in path.parents)


def _resolve_object(
    item: ScopeDescriptor,
    observed: GitIdentityResolution,
    projects: tuple[_ValidatedProject, ...],
    config_sources: tuple[SourceReference, ...],
    observed_at: str,
) -> ObjectResolution:
    refs = _deduplicate_sources((*_observation_sources(item, observed, observed_at), *config_sources))
    path = observed.path.real_path or observed.path.absolute_path
    if observed.status == "not_git_worktree":
        return ObjectResolution(
            locator_index=item.locator_index,
            locator=item.locator,
            resolved_identity=str(path),
            identity_evidence=refs,
            source=item.source,
            status=ObjectStatus.NOT_GOVERNED,
            governed_project_id=None,
            registered_project_path=None,
            governed_via=None,
            git_worktree_root=None,
            git_common_dir=None,
            source_refs=refs,
            unknown_reason=None,
        )

    assert observed.identity is not None
    path_matches = tuple(
        project
        for project in projects
        if observed.identity.worktree_root == project.identity.worktree_root
        and _is_within(path, project.registration.path)
    )
    common_matches = tuple(
        project for project in projects if observed.identity.common_dir == project.identity.common_dir
    )
    if len(path_matches) == 1:
        return _governed_resolution(item, observed, path_matches[0], GovernedVia.PATH, refs)
    if not path_matches and len(common_matches) == 1:
        return _governed_resolution(item, observed, common_matches[0], GovernedVia.GIT_COMMON_DIR, refs)
    if len(path_matches) > 1 or len(common_matches) > 1:
        return ObjectResolution(
            locator_index=item.locator_index,
            locator=item.locator,
            resolved_identity=str(path),
            identity_evidence=refs,
            source=item.source,
            status=ObjectStatus.UNKNOWN,
            governed_project_id=None,
            registered_project_path=None,
            governed_via=None,
            git_worktree_root=str(observed.identity.worktree_root),
            git_common_dir=str(observed.identity.common_dir),
            source_refs=refs,
            unknown_reason="The work object does not uniquely match one governed project",
        )
    return ObjectResolution(
        locator_index=item.locator_index,
        locator=item.locator,
        resolved_identity=str(path),
        identity_evidence=refs,
        source=item.source,
        status=ObjectStatus.NOT_GOVERNED,
        governed_project_id=None,
        registered_project_path=None,
        governed_via=None,
        git_worktree_root=str(observed.identity.worktree_root),
        git_common_dir=str(observed.identity.common_dir),
        source_refs=refs,
        unknown_reason=None,
    )


def _governed_resolution(
    item: ScopeDescriptor,
    observed: GitIdentityResolution,
    project: _ValidatedProject,
    via: GovernedVia,
    refs: tuple[SourceReference, ...],
) -> ObjectResolution:
    assert observed.identity is not None
    path = observed.path.real_path or observed.path.absolute_path
    return ObjectResolution(
        locator_index=item.locator_index,
        locator=item.locator,
        resolved_identity=str(path),
        identity_evidence=refs,
        source=item.source,
        status=ObjectStatus.GOVERNED,
        governed_project_id=project.registration.project_id,
        registered_project_path=str(project.registration.path),
        governed_via=via,
        git_worktree_root=str(observed.identity.worktree_root),
        git_common_dir=str(observed.identity.common_dir),
        source_refs=refs,
        unknown_reason=None,
    )


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _non_valid_configuration_run(
    requested: tuple[ScopeDescriptor, ...],
    observations: tuple[tuple[ScopeDescriptor, GitIdentityResolution], ...],
    configuration: ConfigurationReadResult,
    sources: tuple[SourceReference, ...],
) -> GovernanceResolutionRun:
    status = ConfigStatus(configuration.status.value)
    reason = {
        ConfigStatus.MISSING: "No governed-projects configuration was selected",
        ConfigStatus.INVALID: "The selected governed-projects configuration is structurally invalid",
        ConfigStatus.CONFLICT: "Multiple governed-projects configurations were discovered",
        ConfigStatus.VALID: "",
    }[status]
    completed_observations = tuple(
        (item, observation) for item, observation in observations if observation.status != "technical_failure"
    )
    completed = tuple(item for item, _ in completed_observations)
    failures = tuple(
        (item, observation.failure)
        for item, observation in observations
        if observation.status == "technical_failure" and observation.failure is not None
    )
    result = (
        _unknown_result(completed, completed_observations, configuration, status, reason, sources)
        if completed
        else None
    )
    technical = _technical_non_completions(failures)
    gaps = ([ResolutionGap(reason, completed, sources)] if completed else []) + [
        ResolutionGap(item.summary, item.scope, sources) for item in technical
    ]
    diagnostics = [_configuration_diagnostic(item, completed, sources) for item in configuration.diagnostics] + [
        ResolutionDiagnostic(item.stage, item.summary, item.scope) for item in technical
    ]
    return GovernanceResolutionRun(
        result=result,
        requested_scope=requested,
        completed_scope=completed,
        technical_non_completions=technical,
        sources=sources,
        gaps=tuple(gaps),
        diagnostics=tuple(diagnostics),
    )


def _unknown_result(
    requested: tuple[ScopeDescriptor, ...],
    observations: tuple[tuple[ScopeDescriptor, GitIdentityResolution], ...],
    configuration: ConfigurationReadResult,
    status: ConfigStatus,
    reason: str,
    sources: tuple[SourceReference, ...],
) -> GovernanceScopeResult:
    by_index = {item.locator_index: observed for item, observed in observations}
    resolutions = []
    for item in requested:
        observed = by_index[item.locator_index]
        identity = observed.identity
        refs = _deduplicate_sources((*_observation_sources(item, observed, _source_time(sources)), *sources))
        path = observed.path.real_path or observed.path.absolute_path
        resolutions.append(
            ObjectResolution(
                locator_index=item.locator_index,
                locator=item.locator,
                resolved_identity=str(path) if path else None,
                identity_evidence=refs if observed.status != "technical_failure" else (),
                source=item.source,
                status=ObjectStatus.UNKNOWN,
                governed_project_id=None,
                registered_project_path=None,
                governed_via=None,
                git_worktree_root=str(identity.worktree_root) if identity else None,
                git_common_dir=str(identity.common_dir) if identity else None,
                source_refs=refs or sources,
                unknown_reason=reason,
            )
        )
    return GovernanceScopeResult(
        workspace_root=str(configuration.workspace_root) if configuration.workspace_root else None,
        config_path=str(configuration.config_path) if configuration.config_path else None,
        config_status=status,
        object_resolutions=tuple(resolutions),
        source_refs=sources,
    )


def _technical_run_for_failures(
    requested: tuple[ScopeDescriptor, ...],
    failures: Sequence[tuple[ScopeDescriptor, TechnicalFailure]],
    sources: tuple[SourceReference, ...],
    *,
    stage_prefix: str,
) -> GovernanceResolutionRun:
    technical = _technical_non_completions(failures, stage_prefix=stage_prefix)
    return GovernanceResolutionRun(
        result=None,
        requested_scope=requested,
        completed_scope=(),
        technical_non_completions=technical,
        sources=sources,
        gaps=tuple(ResolutionGap(item.summary, item.scope, sources) for item in technical),
        diagnostics=tuple(ResolutionDiagnostic(item.stage, item.summary, item.scope) for item in technical),
    )


def _global_technical_run(
    requested: tuple[ScopeDescriptor, ...],
    outcome: TechnicalOutcome,
    stage: str,
    summary: str,
    sources: tuple[SourceReference, ...],
) -> GovernanceResolutionRun:
    item = TechnicalNonCompletion(outcome, stage, summary, requested)
    return GovernanceResolutionRun(
        result=None,
        requested_scope=requested,
        completed_scope=(),
        technical_non_completions=(item,),
        sources=sources,
        gaps=(ResolutionGap(summary, requested, sources),),
        diagnostics=(ResolutionDiagnostic(stage, summary, requested),),
    )


def _technical_non_completions(
    failures: Sequence[tuple[ScopeDescriptor, TechnicalFailure]],
    *,
    stage_prefix: str | None = None,
) -> tuple[TechnicalNonCompletion, ...]:
    return tuple(
        TechnicalNonCompletion(
            outcome=TechnicalOutcome.UNAVAILABLE if failure.stage == "git_dependency" else TechnicalOutcome.ERROR,
            stage=f"{stage_prefix}.{failure.stage}" if stage_prefix else failure.stage,
            summary=_safe_failure_summary(failure),
            scope=(item,),
        )
        for item, failure in failures
    )


def _safe_failure_summary(failure: TechnicalFailure) -> str:
    # failure.details can contain raw Git stderr and host paths.  It is kept out
    # of the public-facing runtime diagnostics by design.
    return {
        "path": "The work object path could not be observed",
        "git_dependency": "Git is unavailable for the required identity observation",
        "git_process": "Git could not complete the required identity observation",
        "git_output": "Git returned an unusable identity observation",
    }[failure.stage]


def _configuration_diagnostic(
    diagnostic: ConfigurationDiagnostic,
    scope: tuple[ScopeDescriptor, ...],
    sources: tuple[SourceReference, ...],
) -> ResolutionDiagnostic:
    return ResolutionDiagnostic("configuration", diagnostic.summary, scope, sources)


def _observation_sources(
    item: ScopeDescriptor,
    observed: GitIdentityResolution,
    observed_at: str,
) -> tuple[SourceReference, ...]:
    path = observed.path
    path_source: dict[str, Any] = {
        "kind": "path_observation",
        "locator": str(path.absolute_path),
        "observed_at": observed_at,
        "details": {
            "locator_index": item.locator_index,
            "original_locator": item.locator,
            "base": path.original_base,
            "exists": path.exists,
            "uses_existing_ancestor": path.probe_uses_existing_ancestor,
        },
    }
    if observed.identity is None:
        return (_freeze_source(path_source),)
    git_source = {
        "kind": "git_identity_observation",
        "locator": str(observed.identity.worktree_root),
        "observed_at": observed_at,
        "details": {
            "locator_index": item.locator_index,
            "git_common_dir": str(observed.identity.common_dir),
        },
    }
    return (_freeze_source(path_source), _freeze_source(git_source))


def _registered_project_sources(
    registration: GovernedProjectRegistration,
    resolved: GitIdentityResolution,
    observed_at: str,
) -> tuple[SourceReference, ...]:
    details: dict[str, Any] = {
        "project_id": registration.project_id,
        "status": resolved.status,
    }
    if resolved.identity is not None:
        details.update(
            {
                "git_worktree_root": str(resolved.identity.worktree_root),
                "git_common_dir": str(resolved.identity.common_dir),
            }
        )
    return (
        _freeze_source(
            {
                "kind": "registered_project_git_identity",
                "locator": str(registration.path),
                "observed_at": observed_at,
                "details": details,
            }
        ),
    )


def _configuration_sources(
    result: ConfigurationReadResult,
    observed_at: str,
    *,
    fallback: Path,
) -> tuple[SourceReference, ...]:
    sources: list[SourceReference] = []
    for discovered in result.discovered:
        sources.append(
            _freeze_source(
                {
                    "kind": "governed_projects_configuration",
                    "locator": str(discovered.path),
                    "observed_at": observed_at,
                    "details": {
                        "discovery_bases": [
                            {"kind": basis.kind, "start": str(basis.start)} for basis in discovered.bases
                        ]
                    },
                }
            )
        )
    if not sources:
        locator = result.workspace_root or (result.search_bases[0].start if result.search_bases else fallback)
        sources.append(
            _freeze_source(
                {
                    "kind": "configuration_discovery_observation",
                    "locator": str(locator),
                    "observed_at": observed_at,
                    "details": {"status": result.status.value},
                }
            )
        )
    return tuple(sources)


def _source_time(sources: Sequence[SourceReference]) -> str:
    for source in sources:
        observed_at = source.get("observed_at")
        if isinstance(observed_at, str):
            return observed_at
    return datetime.now(UTC).astimezone().isoformat(timespec="seconds")


def _freeze_source(value: Mapping[str, Any]) -> SourceReference:
    return MappingProxyType({str(key): _freeze_value(item) for key, item in value.items()})


def _freeze_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): _freeze_value(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_value(item) for item in value)
    return value


def _freeze_sources(values: Iterable[SourceReference]) -> tuple[SourceReference, ...]:
    return tuple(_freeze_source(value) for value in values)


def _deduplicate_sources(values: Iterable[SourceReference]) -> tuple[SourceReference, ...]:
    unique: list[SourceReference] = []
    keys: set[str] = set()
    for value in values:
        key = repr(_plain_value(value))
        if key in keys:
            continue
        keys.add(key)
        unique.append(value)
    return _freeze_sources(unique)


def _plain_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _plain_value(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_plain_value(item) for item in value]
    return value


__all__ = [
    "GovernanceResolutionRun",
    "ResolutionDiagnostic",
    "ResolutionGap",
    "TechnicalNonCompletion",
    "TechnicalOutcome",
    "resolve_governance_scope",
]
