"""Read Helper declaration candidates from active documents passing implemented checks."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass

from ldvh.diagnostics import Issue, SourceLocation
from ldvh.specs.identity import KEY_PATTERN, FormalDocument
from ldvh.specs.markdown import Heading, MarkdownTable, parse_table_after_heading
from ldvh.specs.repository import RepositoryInspection

DECLARATION_HEADING = "Helper 公开操作"
DECLARATION_HEADERS = (
    "operation_key",
    "summary",
    "effect",
    "arguments_contract",
    "result_contract",
)
EFFECTS = frozenset({"read", "may_change_state"})
RESERVED_OPERATION_KEYS = frozenset({"capabilities"})


@dataclass(frozen=True, slots=True)
class OperationDeclarationCandidate:
    operation_key: str
    summary: str
    effect: str
    arguments_contract: str
    result_contract: str
    source_key: str
    source: SourceLocation


@dataclass(frozen=True, slots=True)
class _ObservedOperationKey:
    operation_key: str
    source_key: str
    source: SourceLocation


@dataclass(frozen=True, slots=True)
class OperationSourceInspection:
    candidate_declarations: tuple[OperationDeclarationCandidate, ...]
    issues: tuple[Issue, ...]
    incomplete_sources: tuple[str, ...]
    unchecked_conditions: tuple[str, ...]


def _issue(document: FormalDocument, summary: str, *, line: int | None = None) -> Issue:
    return Issue(
        summary=summary,
        location=SourceLocation(document.canonical_path, line),
        affected=(document.key,),
    )


def _parse_reference(
    value: str,
    source: FormalDocument,
    allowed_sources: dict[str, FormalDocument],
    issues: list[Issue],
    line: int,
) -> bool:
    if value.count("::") != 1:
        issues.append(_issue(source, f"契约引用 {value!r} 必须且只能包含一个 '::'", line=line))
        return False
    source_key, heading_text = value.split("::", 1)
    if not heading_text:
        issues.append(_issue(source, f"契约引用 {value!r} 缺少精确标题文本", line=line))
        return False
    target = allowed_sources.get(source_key)
    if target is None:
        issues.append(_issue(source, f"契约引用 {value!r} 越过声明来源或其授权附件", line=line))
        return False
    matches = target.markdown.find_headings(heading_text)
    if len(matches) != 1:
        issues.append(_issue(source, f"契约引用 {value!r} 的精确标题缺失或不唯一", line=line))
        return False
    return True


def _source_declarations(
    source: FormalDocument,
    documents_passing_implemented_checks: dict[str, FormalDocument],
) -> tuple[list[OperationDeclarationCandidate], list[_ObservedOperationKey], list[Issue], bool]:
    headings = source.markdown.find_headings(DECLARATION_HEADING, level=3)
    if not headings:
        return [], [], [], True
    if len(headings) != 1:
        return [], [], [_issue(source, "同一来源至多包含一个精确的 Helper 公开操作 H3")], False

    heading: Heading = headings[0]
    table: MarkdownTable | None = parse_table_after_heading(source.markdown, heading)
    if table is None:
        return [], [], [_issue(source, "Helper 公开操作 H3 后必须紧接固定 Markdown 表格", line=heading.line)], False
    if table.headers != DECLARATION_HEADERS:
        return [], [], [_issue(source, "Helper 公开操作表头与固定字段不一致", line=table.line)], False
    if not table.rows:
        return [], [], [_issue(source, "Helper 公开操作声明表至少包含一个数据行", line=table.line)], False

    allowed_keys = {source.key, *source.authorized_attachments}
    allowed_sources = {
        key: documents_passing_implemented_checks[key]
        for key in allowed_keys
        if key in documents_passing_implemented_checks
    }
    declarations: list[OperationDeclarationCandidate] = []
    observed_keys: list[_ObservedOperationKey] = []
    issues: list[Issue] = []
    complete = True
    for row_index, row in enumerate(table.rows, start=2):
        line = table.line + row_index
        if len(row) == len(DECLARATION_HEADERS) and row[0]:
            observed_keys.append(
                _ObservedOperationKey(
                    operation_key=row[0],
                    source_key=source.key,
                    source=SourceLocation(source.canonical_path, line, DECLARATION_HEADING),
                )
            )
        if len(row) != len(DECLARATION_HEADERS) or any(not cell for cell in row):
            issues.append(_issue(source, "Helper 公开操作声明行必须恰有五个非空单元格", line=line))
            complete = False
            continue
        operation_key, summary, effect, arguments_contract, result_contract = row
        row_valid = True
        if KEY_PATTERN.fullmatch(operation_key) is None:
            issues.append(_issue(source, f"operation_key {operation_key!r} 格式无效", line=line))
            row_valid = False
        elif operation_key in RESERVED_OPERATION_KEYS:
            issues.append(
                _issue(source, f"operation_key {operation_key!r} 是 Helper 保留入口，不得作为领域操作", line=line)
            )
            row_valid = False
        if effect not in EFFECTS:
            issues.append(_issue(source, f"effect {effect!r} 不是 read 或 may_change_state", line=line))
            row_valid = False
        row_valid &= _parse_reference(arguments_contract, source, allowed_sources, issues, line)
        row_valid &= _parse_reference(result_contract, source, allowed_sources, issues, line)
        if not row_valid:
            complete = False
            continue
        declarations.append(
            OperationDeclarationCandidate(
                operation_key=operation_key,
                summary=summary,
                effect=effect,
                arguments_contract=arguments_contract,
                result_contract=result_contract,
                source_key=source.key,
                source=SourceLocation(source.canonical_path, line, DECLARATION_HEADING),
            )
        )
    return declarations, observed_keys, issues, complete


def _duplicate_operation_keys(observed_keys: Iterable[_ObservedOperationKey]) -> set[str]:
    return {key for key, count in Counter(observed.operation_key for observed in observed_keys).items() if count > 1}


def inspect_operation_sources(repository: RepositoryInspection) -> OperationSourceInspection:
    """Inspect exact declaration tables without creating implementation-backed operations."""

    documents_passing_implemented_checks = {
        document.key: document for document in repository.active_documents_passing_implemented_checks
    }
    declarations: list[OperationDeclarationCandidate] = []
    observed_keys: list[_ObservedOperationKey] = []
    issues: list[Issue] = list(repository.issues)
    incomplete: set[str] = set(repository.incomplete_scope)
    for document in repository.active_documents_passing_implemented_checks:
        if document.kind == "attachment":
            continue
        source_declarations, source_observed_keys, source_issues, complete = _source_declarations(
            document,
            documents_passing_implemented_checks,
        )
        declarations.extend(source_declarations)
        observed_keys.extend(source_observed_keys)
        issues.extend(source_issues)
        if not complete:
            incomplete.add(document.key)

    duplicate_keys = _duplicate_operation_keys(observed_keys)
    if duplicate_keys:
        declarations = [declaration for declaration in declarations if declaration.operation_key not in duplicate_keys]
        for observed in observed_keys:
            if observed.operation_key in duplicate_keys:
                issues.append(
                    Issue(
                        summary=f"operation_key {observed.operation_key!r} 在本次声明候选中重复",
                        location=observed.source,
                        affected=(observed.source_key, observed.operation_key),
                    )
                )
                incomplete.add(observed.source_key)

    contract_conditions = ("契约目标章节是否完整定义字段、类型、必填性、空值和闭集语义",) if observed_keys else ()
    return OperationSourceInspection(
        candidate_declarations=tuple(sorted(declarations, key=lambda declaration: declaration.operation_key)),
        issues=tuple(issues),
        incomplete_sources=tuple(sorted(incomplete)),
        unchecked_conditions=repository.unchecked_conditions + contract_conditions,
    )
