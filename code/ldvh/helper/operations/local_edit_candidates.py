"""Build read-only exact local-edit candidate material."""

from __future__ import annotations

import difflib
import hashlib
import json
from dataclasses import dataclass
from typing import Any, Literal

from ldvh.facts.carriers.study_markdown import STUDY_H2_TITLES, _body_headings
from ldvh.facts.contracts import LAYOUTS
from ldvh.facts.repository import FactReadResult, read_fact_object
from ldvh.facts.schema import project_fact_schemas
from ldvh.governance.resolver import GovernanceResolutionRun, resolve_governance_scope
from ldvh.helper.operations.fact_operation_support import plain, reading_boundary
from ldvh.helper.operations.local_edit_request import LocalEditRequest, RuleLocalEditRequest, StudyLocalEditRequest
from ldvh.helper.responses import source_reference
from ldvh.helper.source_refs import GeneratedSourceReference, RuleReferenceBinder
from ldvh.specs.identity import FormalDocument
from ldvh.specs.repository import RepositoryInspection

JsonObject = dict[str, object]
Outcome = Literal["ok", "rejected", "unavailable", "error"]

_QUALIFICATION_SOURCE: JsonObject = source_reference("rule", "specs/01-规范模型基础规范.md#6.2-进入当前规则源的条件")
_STUDY_RULE_SOURCE: JsonObject = source_reference("rule", "specs/24-Study-研究报告.md")


class LocalEditSelectionError(ValueError):
    """An exact target could not be established."""

    def __init__(self, problems: tuple[str, ...], *, sources: tuple[JsonObject, ...] = ()) -> None:
        super().__init__("local edit target is invalid")
        self.problems = problems
        self.sources = sources


@dataclass(frozen=True, slots=True)
class LocalEditReadResult:
    items: tuple[JsonObject, ...] | None
    requested_scope: tuple[JsonObject, ...]
    completed_scope: tuple[JsonObject, ...]
    not_completed_scope: tuple[JsonObject, ...]
    governance_resolution: JsonObject | None
    sources: tuple[JsonObject, ...]
    gaps: tuple[JsonObject, ...]
    verification: tuple[JsonObject, ...]
    diagnostics: tuple[JsonObject, ...]
    outcome: Outcome


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _deduplicate_sources(sources: list[JsonObject]) -> tuple[JsonObject, ...]:
    results: list[JsonObject] = []
    seen: set[str] = set()
    for source in sources:
        identity = json.dumps(source, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        if identity not in seen:
            seen.add(identity)
            results.append(source)
    return tuple(results)


def _diff(before: str, candidate_after: str | None, *, label: str) -> str | None:
    if candidate_after is None:
        return None
    return "".join(
        difflib.unified_diff(
            before.splitlines(keepends=True),
            candidate_after.splitlines(keepends=True),
            fromfile=f"{label}:before",
            tofile=f"{label}:candidate",
            lineterm="\n",
        )
    )


def _baseline(value: str, expected: str | None, *, kind: str) -> JsonObject:
    return {"kind": kind, "value": value, "matches_expected": None if expected is None else expected == value}


def _rule_document(repository: RepositoryInspection, request: RuleLocalEditRequest) -> FormalDocument:
    documents = [
        document
        for document in repository.active_documents_passing_implemented_checks
        if document.key == request.responsibility_key
    ]
    if len(documents) == 1:
        return documents[0]
    if len(documents) > 1:
        raise LocalEditSelectionError(("当前规则源中职责标识符不唯一，无法确定局部编辑目标",))
    parsed = [document for document in repository.parsed_documents if document.key == request.responsibility_key]
    sources = tuple(source_reference("rule", document.canonical_path) for document in parsed)
    if parsed and parsed[0].status != "active":
        raise LocalEditSelectionError(
            (f"职责标识符 {request.responsibility_key!r} 当前未声明为 active，不能读取局部编辑候选",), sources=sources
        )
    if parsed:
        raise LocalEditSelectionError(("目标规则载体未通过既有机械检查，Stop Conditions 禁止读取",), sources=sources)
    if repository.issues or repository.incomplete_scope:
        raise LocalEditSelectionError(("当前规则源存在未完成范围，无法确定请求职责标识符",))
    raise LocalEditSelectionError((f"未精确匹配职责标识符 {request.responsibility_key!r}",))


def _rule_range(document: FormalDocument, heading_path: tuple[str, ...]) -> tuple[int, int]:
    headings = document.markdown.headings
    h2_matches = [heading for heading in headings if heading.level == 2 and heading.title == heading_path[0]]
    if len(h2_matches) != 1:
        raise LocalEditSelectionError(
            (f"H2 无法精确唯一匹配: {heading_path[0]!r}",), sources=(source_reference("rule", document.canonical_path),)
        )
    h2 = h2_matches[0]
    next_h2 = min(
        (heading.line for heading in headings if heading.level == 2 and heading.line > h2.line),
        default=len(document.markdown.raw_lines) + 1,
    )
    if len(heading_path) == 1:
        return h2.line, next_h2 - 1
    h3_matches = [
        heading
        for heading in headings
        if heading.level == 3 and h2.line < heading.line < next_h2 and heading.title == heading_path[1]
    ]
    if len(h3_matches) != 1:
        raise LocalEditSelectionError(
            (f"H2 {heading_path[0]!r} 中 H3 无法精确唯一匹配: {heading_path[1]!r}",),
            sources=(source_reference("rule", document.canonical_path),),
        )
    target = h3_matches[0]
    end = min(
        (heading.line for heading in headings if heading.line > target.line and heading.level in {2, 3}),
        default=len(document.markdown.raw_lines) + 1,
    )
    return target.line, end - 1


def _bound_rule_source(
    repository: RepositoryInspection,
    document: FormalDocument,
    heading_path: tuple[str, ...],
    start_line: int,
    end_line: int,
) -> JsonObject:
    if repository.source_identity is None:
        raise LocalEditSelectionError(("当前规则源身份未形成，不能绑定局部编辑证据",))
    observed_at = document.markdown.observed_at
    if observed_at is None:
        raise LocalEditSelectionError(("当前规则源缺少可回指的 observed_at，不能形成可信局部读取证据",))
    source = source_reference(
        "rule",
        f"{document.canonical_path}#L{start_line}-L{end_line}",
        responsibility_key=document.key,
        path=document.canonical_path,
        heading_path=list(heading_path),
        start_line=start_line,
        end_line=end_line,
    )
    source["observed_at"] = observed_at
    assert isinstance(source, GeneratedSourceReference)
    return RuleReferenceBinder(repository.source_identity, (document,)).bind(source)


def _rule_item(
    repository: RepositoryInspection, request: RuleLocalEditRequest
) -> tuple[JsonObject, JsonObject, tuple[JsonObject, ...]]:
    document = _rule_document(repository, request)
    start_line, end_line = _rule_range(document, request.heading_path)
    before = "".join(document.markdown.raw_text.splitlines(keepends=True)[start_line - 1 : end_line])
    source = _bound_rule_source(repository, document, request.heading_path, start_line, end_line)
    current = _hash(before)
    stale = request.expected_baseline is not None and request.expected_baseline != current
    target: JsonObject = {"responsibility_key": request.responsibility_key, "heading_path": list(request.heading_path)}
    item: JsonObject = {
        "source_kind": "rule",
        "target": target,
        "baseline": _baseline(current, request.expected_baseline, kind="content_sha256"),
        "stale": stale,
        "before": before,
        "candidate_after": request.candidate_after,
        "unified_diff": _diff(before, request.candidate_after, label=document.canonical_path),
        "source_ranges": [{"source_ref": source, "start_line": start_line, "end_line": end_line, "scope": target}],
        "scope_coverage": {
            "expanded": [target],
            "unexpanded": [
                {"responsibility_key": request.responsibility_key, "scope": "同一规则载体内未选中的其它内容"}
            ],
        },
        "publication_boundary": {
            "summary": (
                "规则候选只能进入直接工作树编辑后的规则治理、独立复核、风险匹配验证、条件性 Human Gate 与 Git 闭环。"
            ),
            "source_refs": [source_reference("rule", "specs/01-规范模型基础规范.md")],
        },
    }
    gap: JsonObject | None = None
    if stale:
        gap = {
            "summary": "调用方提供的规则内容基线已漂移；必须重新读取并重新形成候选，不进行模糊匹配、合并或发布",
            "scope": [target],
            "source_refs": [source],
            "code": "baseline_stale",
        }
    return item, target, (() if gap is None else (gap,))


def _study_scope(request: StudyLocalEditRequest) -> JsonObject:
    return {"fact_ref": request.fact_ref.to_json(), "body_heading": request.body_heading}


def _study_source(root: Any, read: FactReadResult, body_heading: str, start_line: int, end_line: int) -> JsonObject:
    return {
        "kind": "working_tree",
        "locator": (root / read.canonical_path).as_posix(),
        "details": {
            "view": "Working Tree",
            "heading_path": [body_heading],
            "start_line": start_line,
            "end_line": end_line,
        },
    }


def _study_range(read: FactReadResult, body_heading: str) -> tuple[int, int, str]:
    if read.raw_text is None or read.body is None:
        raise LocalEditSelectionError(("当前 Study 没有可用于局部候选的原始 Markdown 内容",))
    headings = _body_headings(read.body)
    matches = [(index, title) for index, level, title in headings if level == 2 and title == body_heading]
    if len(matches) != 1:
        raise LocalEditSelectionError((f"Study 固定正文 H2 无法精确唯一匹配: {body_heading!r}",))
    body_lines = read.body.splitlines(keepends=True)
    body_index = matches[0][0]
    next_h2 = next((index for index, level, _ in headings if level == 2 and index > body_index), len(body_lines))
    before = "".join(body_lines[body_index:next_h2])
    raw_lines = read.raw_text.splitlines(keepends=True)
    body_first_line = len(raw_lines) - len(body_lines) + 1
    return body_first_line + body_index, body_first_line + next_h2 - 1, before


def _study_read(repository: RepositoryInspection, request: StudyLocalEditRequest) -> LocalEditReadResult:
    run: GovernanceResolutionRun = resolve_governance_scope(
        request.governance_scope, base=request.base, explicit_workspace_root=None
    )
    requested = (_study_scope(request),)
    governance_json = None if run.result is None else plain(run.result.to_json())
    boundary = reading_boundary(run)
    if boundary is None:
        return LocalEditReadResult(
            None,
            requested,
            (),
            requested,
            governance_json,
            tuple(plain(source) for source in run.sources),
            (
                {
                    "summary": "Study 请求未形成唯一受管项目、实际 Git Working Tree 与 common-dir 读取边界",
                    "scope": list(requested),
                    "source_refs": [plain(source) for source in run.sources],
                },
            ),
            (),
            (),
            "unavailable",
        )
    project_id, root, common_dir = boundary
    if request.fact_ref.governed_project_id != project_id:
        return LocalEditReadResult(
            None,
            requested,
            (),
            requested,
            governance_json,
            tuple(plain(source) for source in run.sources),
            (
                {
                    "summary": "Study 请求项目与实际 Working Tree 的管辖项目不一致",
                    "scope": list(requested),
                    "source_refs": [plain(source) for source in run.sources],
                },
            ),
            (),
            (),
            "unavailable",
        )
    schemas = project_fact_schemas(repository)
    schema = schemas.get("study")
    if schema is None:
        return LocalEditReadResult(
            None,
            requested,
            (),
            requested,
            governance_json,
            tuple(plain(source) for source in run.sources),
            (
                {
                    "summary": "当前规则源未能形成 Study 的完整派生 Schema",
                    "scope": list(requested),
                    "source_refs": [_STUDY_RULE_SOURCE.copy()],
                },
            ),
            (),
            (),
            "unavailable",
        )
    read = read_fact_object(root, LAYOUTS["study"], schema, request.fact_ref.object_id, expected_common_dir=common_dir)
    sources = [*tuple(plain(source) for source in run.sources), _STUDY_RULE_SOURCE.copy()]
    if read.check_status != "mechanically_valid" or read.content_fingerprint is None:
        item_sources = [
            _STUDY_RULE_SOURCE.copy(),
            {
                "kind": "working_tree",
                "locator": (root / read.canonical_path).as_posix(),
                "details": {"view": "Working Tree"},
            },
        ]
        sources.extend(item_sources)
        return LocalEditReadResult(
            None,
            requested,
            (),
            requested,
            governance_json,
            _deduplicate_sources(sources),
            (
                {
                    "summary": "Study 当前载体未通过完整机械读取，不能形成局部编辑候选",
                    "scope": list(requested),
                    "source_refs": item_sources,
                },
            ),
            (),
            tuple(
                {"summary": issue.summary, "details": {"category": issue.category, "field_path": issue.field_path}}
                for issue in read.issues
            ),
            "unavailable",
        )
    try:
        start_line, end_line, before = _study_range(read, request.body_heading)
    except LocalEditSelectionError as error:
        return LocalEditReadResult(
            None,
            requested,
            (),
            requested,
            governance_json,
            _deduplicate_sources(sources),
            ({"summary": error.problems[0], "scope": list(requested), "source_refs": [_STUDY_RULE_SOURCE.copy()]},),
            (),
            (),
            "rejected",
        )
    source = _study_source(root, read, request.body_heading, start_line, end_line)
    sources.append(source)
    target = _study_scope(request)
    stale = request.expected_baseline is not None and request.expected_baseline != read.content_fingerprint
    item: JsonObject = {
        "source_kind": "study",
        "target": target,
        "baseline": _baseline(read.content_fingerprint, request.expected_baseline, kind="content_fingerprint"),
        "stale": stale,
        "before": before,
        "candidate_after": request.candidate_after,
        "unified_diff": _diff(before, request.candidate_after, label=read.canonical_path),
        "source_ranges": [{"source_ref": source, "start_line": start_line, "end_line": end_line, "scope": target}],
        "scope_coverage": {
            "expanded": [target],
            "unexpanded": [
                {
                    "fact_ref": request.fact_ref.to_json(),
                    "body_headings": [title for title in STUDY_H2_TITLES if title != request.body_heading],
                }
            ],
        },
        "publication_boundary": {
            "summary": "Study 候选只能经完整 after、整对象 CAS、原子替换、精确回读和独立完整性审计发布。",
            "source_refs": [_STUDY_RULE_SOURCE.copy()],
        },
    }
    gaps: tuple[JsonObject, ...] = ()
    if stale:
        gaps = (
            {
                "summary": (
                    "调用方提供的 Study content_fingerprint 已漂移；必须重新读取"
                    "并重新形成候选，不进行模糊匹配、合并或发布"
                ),
                "scope": [target],
                "source_refs": [source],
                "code": "baseline_stale",
            },
        )
    return LocalEditReadResult(
        (item,),
        requested,
        requested,
        (),
        governance_json,
        _deduplicate_sources(sources),
        gaps,
        (
            {
                "check": "Study 当前载体、Schema、身份与固定正文结构的机械读取已通过",
                "status": "passed",
                "scope": [target],
                "evidence": [source, _STUDY_RULE_SOURCE.copy()],
            },
        ),
        (),
        "ok",
    )


def read_local_edit_candidates(repository: RepositoryInspection, request: LocalEditRequest) -> LocalEditReadResult:
    """Read one exact rule or Study target without changing any state."""

    if request.source_kind == "study":
        assert request.study is not None
        return _study_read(repository, request.study)
    assert request.rule is not None
    target = {"responsibility_key": request.rule.responsibility_key, "heading_path": list(request.rule.heading_path)}
    try:
        item, target, stale_gaps = _rule_item(repository, request.rule)
    except LocalEditSelectionError as error:
        return LocalEditReadResult(
            None,
            (target,),
            (),
            (target,),
            None,
            error.sources,
            ({"summary": error.problems[0], "scope": [target], "source_refs": list(error.sources)},),
            (),
            (),
            "rejected",
        )
    sources = [entry["source_ref"] for entry in item["source_ranges"]]  # type: ignore[index]
    gaps = list(stale_gaps)
    for condition in repository.unchecked_conditions:
        gaps.append(
            {
                "summary": f"尚未由 Code 机械证明当前规则源资格条件：{condition}",
                "scope": [target],
                "source_refs": [_QUALIFICATION_SOURCE.copy()],
            }
        )
    return LocalEditReadResult(
        (item,),
        (target,),
        (target,),
        (),
        None,
        _deduplicate_sources(sources),
        tuple(gaps),
        (
            {
                "check": "规则目标已从同一 RepositoryInspection 快照按精确 H2/H3 边界读取",
                "status": "passed",
                "scope": [target],
                "evidence": sources,
            },
        ),
        (),
        "ok",
    )


__all__ = ["LocalEditReadResult", "LocalEditSelectionError", "read_local_edit_candidates"]
