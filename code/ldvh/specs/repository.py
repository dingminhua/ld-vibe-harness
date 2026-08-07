"""Thin orchestration of specification discovery, checks, graph, and projection."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from ruamel.yaml import YAML

from ldvh.diagnostics import Issue, SourceLocation
from ldvh.specs.discovery import Candidate, DiscoveryResult, discover_candidates
from ldvh.specs.field_registry import REGISTRY_KEY, FieldRegistryInspection, inspect_field_registry
from ldvh.specs.graph import BasisReachabilityOverlap, GraphResult, validate_graph
from ldvh.specs.identity import FormalDocument, parse_identity
from ldvh.specs.markdown import MarkdownResult, parse_markdown
from ldvh.specs.projection import ProjectionItem, project_l0_l2
from ldvh.specs.source import RuleSourceIdentity
from ldvh.specs.structure import validate_structure

UNCHECKED_CONDITIONS = (
    "规范责任重复、承载净价值和新建或实质变更所需独立复核",
    "授权附件正文是否只承载父规范已经定义并授权的结构化内容",
    "supersedes 正文是否完整说明旧职责中仍适用内容的保留、转移或退出",
    "Index 中准备提交的完整内容及提交后 HEAD 历史锚点",
    "跨 Git 历史的 retired 职责是否曾被重新启用或职责标识符是否被改派",
    "跨 Git 历史的 retired 字段登记是否被删除，或 field_key 与字段位置是否被改派",
    "跨 Git 历史的 fact_type_key 是否被删除、重新启用或改派给其它事实类型语义",
)

_FOUNDATION_KEY = "specification-model-foundation"
_ROOT_KEY = "ldvh-root"
_ROOT_PATH = "specs/00-理念与构成.md"


@dataclass(frozen=True, slots=True)
class RepositoryInspection:
    repository_root: Path
    candidates: tuple[Candidate, ...]
    parsed_documents: tuple[FormalDocument, ...]
    active_documents_passing_implemented_checks: tuple[FormalDocument, ...]
    projections: tuple[ProjectionItem, ...]
    issues: tuple[Issue, ...]
    incomplete_scope: tuple[str, ...]
    unchecked_conditions: tuple[str, ...]
    basis_reachability_overlaps: tuple[BasisReachabilityOverlap, ...]
    implemented_checks_complete: bool
    source_identity: RuleSourceIdentity | None = None
    field_registry: FieldRegistryInspection | None = None

    def document_passing_implemented_checks_by_key(self, key: str) -> FormalDocument | None:
        matches = [document for document in self.active_documents_passing_implemented_checks if document.key == key]
        return matches[0] if len(matches) == 1 else None


@dataclass(frozen=True, slots=True)
class _BootstrapEnvelope:
    candidate: Candidate
    spec_key: str
    status: str | None


def _bootstrap_issue(summary: str, affected: str, *, path: str = ".") -> Issue:
    return Issue(
        summary=summary,
        location=SourceLocation(path),
        affected=(affected,),
    )


def _minimal_spec_envelope(candidate: Candidate, result: MarkdownResult) -> _BootstrapEnvelope | None:
    """Pre-read only the fixed top level and 01 bootstrap key/status fields."""

    if candidate.kind != "spec" or result.document.yaml_text is None:
        return None
    yaml = YAML(typ="safe")
    yaml.version = (1, 2)
    yaml.allow_duplicate_keys = False
    try:
        loaded = yaml.load(result.document.yaml_text)
        if not isinstance(loaded, Mapping) or set(loaded) != {"ldvh_spec"}:
            return None
        identity = loaded.get("ldvh_spec")
        if not isinstance(identity, Mapping):
            return None
        spec_key = identity.get("spec_key")
        status = identity.get("status")
    except Exception:  # the full identity parser owns detailed YAML diagnostics
        return None
    if not isinstance(spec_key, str):
        return None
    return _BootstrapEnvelope(
        candidate=candidate,
        spec_key=spec_key,
        status=status if isinstance(status, str) else None,
    )


def _validate_candidate(
    markdown_result: MarkdownResult,
) -> tuple[FormalDocument | None, tuple[Issue, ...]]:
    issues: list[Issue] = list(markdown_result.issues)
    if markdown_result.issues:
        return None, tuple(issues)
    identity_result = parse_identity(markdown_result.document)
    issues.extend(identity_result.issues)
    if identity_result.document is None:
        return None, tuple(issues)
    structure_issues = validate_structure(identity_result.document)
    issues.extend(structure_issues)
    if structure_issues:
        return None, tuple(issues)
    return identity_result.document, tuple(issues)


def _stopped_inspection(
    discovery: DiscoveryResult,
    *,
    parsed_documents: tuple[FormalDocument, ...],
    issues: list[Issue],
    incomplete: set[str],
    source_identity: RuleSourceIdentity,
) -> RepositoryInspection:
    return RepositoryInspection(
        repository_root=discovery.repository_root,
        candidates=discovery.candidates,
        parsed_documents=parsed_documents,
        active_documents_passing_implemented_checks=(),
        projections=(),
        issues=tuple(issues),
        incomplete_scope=tuple(sorted(incomplete)),
        unchecked_conditions=UNCHECKED_CONDITIONS,
        basis_reachability_overlaps=(),
        implemented_checks_complete=False,
        source_identity=source_identity,
    )


def inspect_repository(repository_root: Path) -> RepositoryInspection:
    """Inspect the current Working Tree without falling back to Index or HEAD."""

    discovery: DiscoveryResult = discover_candidates(repository_root)
    identity = RuleSourceIdentity("working_tree", git_worktree_root=discovery.repository_root)
    return inspect_repository_source(discovery, identity)


def inspect_repository_source(
    discovery: DiscoveryResult,
    source_identity: RuleSourceIdentity,
    *,
    markdown_results: dict[str, MarkdownResult] | None = None,
) -> RepositoryInspection:
    """Run the common repository checks over one already-selected source view."""

    issues: list[Issue] = list(discovery.issues)
    incomplete = {affected for issue in discovery.issues for affected in (issue.affected or (issue.location.path,))}

    # Read every candidate once so bootstrap and full validation observe the same
    # Working Tree bytes.  Full diagnostics are deliberately deferred until the
    # root/foundation startup contract has closed.
    if markdown_results is None:
        markdown_results = {
            candidate.relative_path: parse_markdown(candidate.absolute_path, candidate.relative_path)
            for candidate in discovery.candidates
        }
    envelopes = tuple(
        envelope
        for candidate in discovery.candidates
        if (envelope := _minimal_spec_envelope(candidate, markdown_results[candidate.relative_path])) is not None
    )
    foundation_envelopes = tuple(envelope for envelope in envelopes if envelope.spec_key == _FOUNDATION_KEY)
    if len(foundation_envelopes) != 1:
        issues.append(
            _bootstrap_issue(
                "最小 envelope 必须唯一定位 specification-model-foundation 候选规范",
                _FOUNDATION_KEY,
            )
        )
        incomplete.add(_FOUNDATION_KEY)
        return _stopped_inspection(
            discovery,
            parsed_documents=(),
            issues=issues,
            incomplete=incomplete,
            source_identity=source_identity,
        )

    foundation_envelope = foundation_envelopes[0]
    if foundation_envelope.status != "active":
        issues.append(
            _bootstrap_issue(
                "specification-model-foundation 候选规范必须在最小 envelope 中声明为 active",
                _FOUNDATION_KEY,
                path=foundation_envelope.candidate.relative_path,
            )
        )
        incomplete.add(_FOUNDATION_KEY)
        return _stopped_inspection(
            discovery,
            parsed_documents=(),
            issues=issues,
            incomplete=incomplete,
            source_identity=source_identity,
        )

    root_candidates = tuple(candidate for candidate in discovery.candidates if candidate.relative_path == _ROOT_PATH)
    if len(root_candidates) != 1:
        issues.append(
            _bootstrap_issue(
                "当前 00 必须在 root profile 固定路径上唯一存在",
                _ROOT_KEY,
                path=_ROOT_PATH,
            )
        )
        incomplete.add(_ROOT_KEY)
        return _stopped_inspection(
            discovery,
            parsed_documents=(),
            issues=issues,
            incomplete=incomplete,
            source_identity=source_identity,
        )

    root_candidate = root_candidates[0]
    root_document, root_issues = _validate_candidate(
        markdown_results[root_candidate.relative_path],
    )
    issues.extend(root_issues)
    if (
        root_document is None
        or root_document.kind != "root"
        or root_document.key != _ROOT_KEY
        or root_document.status != "active"
    ):
        if not root_issues:
            issues.append(
                _bootstrap_issue(
                    "当前 00 无法按 root profile 验证为 active ldvh-root",
                    _ROOT_KEY,
                    path=_ROOT_PATH,
                )
            )
        incomplete.add(_ROOT_KEY)
        return _stopped_inspection(
            discovery,
            parsed_documents=(),
            issues=issues,
            incomplete=incomplete,
            source_identity=source_identity,
        )

    foundation_document, foundation_issues = _validate_candidate(
        markdown_results[foundation_envelope.candidate.relative_path],
    )
    issues.extend(foundation_issues)
    if (
        foundation_document is None
        or foundation_document.kind != "spec"
        or foundation_document.key != _FOUNDATION_KEY
        or foundation_document.status != "active"
    ):
        if not foundation_issues:
            issues.append(
                _bootstrap_issue(
                    "specification-model-foundation 候选规范无法通过完整契约验证",
                    _FOUNDATION_KEY,
                    path=foundation_envelope.candidate.relative_path,
                )
            )
        incomplete.add(_FOUNDATION_KEY)
        return _stopped_inspection(
            discovery,
            parsed_documents=(root_document,),
            issues=issues,
            incomplete=incomplete,
            source_identity=source_identity,
        )

    startup_attachment_prefix = f"specs/attachments/{foundation_document.current_id}.Att."
    startup_attachment_candidates = tuple(
        candidate
        for candidate in discovery.candidates
        if candidate.kind == "attachment" and candidate.relative_path.startswith(startup_attachment_prefix)
    )
    startup_documents: list[FormalDocument] = [root_document, foundation_document]
    startup_paths = {
        _ROOT_PATH,
        foundation_envelope.candidate.relative_path,
        *(candidate.relative_path for candidate in startup_attachment_candidates),
    }
    for candidate in startup_attachment_candidates:
        document, candidate_issues = _validate_candidate(
            markdown_results[candidate.relative_path],
        )
        issues.extend(candidate_issues)
        if document is None:
            incomplete.add(candidate.relative_path)
            continue
        startup_documents.append(document)

    startup_graph = validate_graph(startup_documents)
    startup_passing_keys = {document.key for document in startup_graph.active_documents_passing_implemented_checks}
    foundation_attachments_pass = set(foundation_document.authorized_attachments).issubset(startup_passing_keys)
    if foundation_document.key not in startup_passing_keys or not foundation_attachments_pass:
        issues.extend(startup_graph.issues)
        incomplete.update(startup_graph.incomplete_keys)
        incomplete.add(_FOUNDATION_KEY)
        return _stopped_inspection(
            discovery,
            parsed_documents=tuple(sorted(startup_documents, key=lambda document: document.canonical_path)),
            issues=issues,
            incomplete=incomplete,
            source_identity=source_identity,
        )

    documents = startup_documents.copy()
    for candidate in discovery.candidates:
        if candidate.relative_path in startup_paths:
            continue
        document, candidate_issues = _validate_candidate(
            markdown_results[candidate.relative_path],
        )
        issues.extend(candidate_issues)
        if document is None:
            incomplete.add(candidate.relative_path)
            continue
        documents.append(document)

    parsed_documents = tuple(sorted(documents, key=lambda document: document.canonical_path))

    initial_graph: GraphResult = validate_graph(parsed_documents)
    field_registry = None
    if any(document.key == REGISTRY_KEY for document in initial_graph.active_documents_passing_implemented_checks):
        field_registry = inspect_field_registry(initial_graph.active_documents_passing_implemented_checks)

    if field_registry is not None and field_registry.issues:
        central_failure = any(REGISTRY_KEY in issue.affected for issue in field_registry.issues)
        invalid_source_keys = {
            affected
            for issue in field_registry.issues
            for affected in issue.affected
            if affected != REGISTRY_KEY and any(document.key == affected for document in parsed_documents)
        }
        excluded_keys = invalid_source_keys | ({REGISTRY_KEY} if central_failure else set())
        graph = validate_graph(tuple(document for document in parsed_documents if document.key not in excluded_keys))
        issues.extend(field_registry.issues)
        incomplete.update(excluded_keys)
    else:
        graph = initial_graph
    issues.extend(graph.issues)
    incomplete.update(graph.incomplete_keys)
    projections = project_l0_l2(graph)
    blocking_issues = [issue for issue in issues if issue.blocks_projection]
    return RepositoryInspection(
        repository_root=discovery.repository_root,
        candidates=discovery.candidates,
        parsed_documents=parsed_documents,
        active_documents_passing_implemented_checks=graph.active_documents_passing_implemented_checks,
        projections=projections,
        issues=tuple(issues),
        incomplete_scope=tuple(sorted(incomplete)),
        unchecked_conditions=UNCHECKED_CONDITIONS,
        basis_reachability_overlaps=graph.basis_reachability_overlaps,
        implemented_checks_complete=discovery.complete and not blocking_issues and not incomplete,
        source_identity=source_identity,
        field_registry=field_registry,
    )
