"""Parse the rule-declared locations of non-rule mechanical audit evidence."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath

from ldvh.diagnostics import Issue, SourceLocation
from ldvh.specs.identity import KEY_PATTERN, FormalDocument
from ldvh.specs.markdown import MarkdownDocument, parse_table_after_heading

REGISTRY_KEY = "fact-object-field-registry"
LOCATOR_HEADING = "审计证据定位表"
LOCATOR_HEADERS = ("audit_record_key", "canonical_path", "audit_namespace")


@dataclass(frozen=True, slots=True)
class AuditEvidenceLocator:
    audit_record_key: str
    canonical_path: str
    audit_namespace: str
    source: SourceLocation


@dataclass(frozen=True, slots=True)
class AuditEvidenceLocatorInspection:
    locators: tuple[AuditEvidenceLocator, ...]
    issues: tuple[Issue, ...]

    @property
    def complete(self) -> bool:
        return not self.issues


def _issue(registry: FormalDocument, summary: str, *, line: int | None = None) -> Issue:
    return Issue(summary=summary, location=SourceLocation(registry.canonical_path, line=line), affected=(REGISTRY_KEY,))


def _normal_canonical_path(value: str) -> bool:
    path = PurePosixPath(value)
    return (
        bool(value)
        and not value.startswith("/")
        and "\\" not in value
        and "//" not in value
        and all(part not in {"", ".", ".."} for part in path.parts)
        and path.as_posix() == value
    )


def _is_rule_candidate_path(value: str) -> bool:
    path = PurePosixPath(value)
    if len(path.parts) == 2 and path.parts[0] == "specs":
        return path.name.endswith(".md") and path.name[:2].isdigit() and "-" in path.name
    if len(path.parts) == 3 and path.parts[:2] == ("specs", "attachments"):
        return path.name.endswith(".md") and ".Att." in path.name and "-" in path.name
    return False


def inspect_audit_evidence_locators(documents: tuple[FormalDocument, ...]) -> AuditEvidenceLocatorInspection:
    registries = tuple(
        document for document in documents if document.key == REGISTRY_KEY and document.status == "active"
    )
    if len(registries) != 1:
        issue = Issue(
            summary="审计证据定位表要求唯一 active fact-object-field-registry",
            location=SourceLocation("."),
            affected=(REGISTRY_KEY,),
        )
        return AuditEvidenceLocatorInspection((), (issue,))
    registry = registries[0]
    headings = registry.markdown.find_headings(LOCATOR_HEADING, level=2)
    if len(headings) != 1:
        return AuditEvidenceLocatorInspection((), (_issue(registry, "审计证据定位表 H2 必须恰好出现一次"),))
    table = parse_table_after_heading(registry.markdown, headings[0])
    if table is None or table.headers != LOCATOR_HEADERS or not table.rows:
        return AuditEvidenceLocatorInspection(
            (),
            (_issue(registry, "审计证据定位表必须紧接固定三列表且至少一行", line=headings[0].line),),
        )

    issues: list[Issue] = []
    locators: list[AuditEvidenceLocator] = []
    seen_keys: set[str] = set()
    seen_paths: set[str] = set()
    seen_namespaces: set[str] = set()
    for offset, row in enumerate(table.rows, start=2):
        line = table.line + offset
        if len(row) != 3 or any(not cell for cell in row):
            issues.append(_issue(registry, "审计证据定位行必须包含三个非空单元格", line=line))
            continue
        record_key, canonical_path, namespace = row
        if KEY_PATTERN.fullmatch(record_key) is None:
            issues.append(_issue(registry, f"非法 audit_record_key {record_key!r}", line=line))
        if not _normal_canonical_path(canonical_path) or _is_rule_candidate_path(canonical_path):
            issues.append(_issue(registry, f"非法机械证据 canonical_path {canonical_path!r}", line=line))
        if "::" in namespace or not namespace.strip():
            issues.append(_issue(registry, f"非法 audit_namespace {namespace!r}", line=line))
        if record_key in seen_keys:
            issues.append(_issue(registry, f"重复 audit_record_key {record_key!r}", line=line))
        if canonical_path in seen_paths:
            issues.append(_issue(registry, f"重复机械证据 canonical_path {canonical_path!r}", line=line))
        if namespace in seen_namespaces:
            issues.append(_issue(registry, f"重复 audit_namespace {namespace!r}", line=line))
        seen_keys.add(record_key)
        seen_paths.add(canonical_path)
        seen_namespaces.add(namespace)
        locators.append(
            AuditEvidenceLocator(
                record_key,
                canonical_path,
                namespace,
                SourceLocation(registry.canonical_path, line=line),
            )
        )
    return AuditEvidenceLocatorInspection(tuple(locators), tuple(issues))


def validate_audit_document(locator: AuditEvidenceLocator, document: MarkdownDocument) -> tuple[Issue, ...]:
    issues: list[Issue] = []
    if document.relative_path != locator.canonical_path or not document.raw_lines:
        return (
            Issue(
                summary="准入审计证据文档不存在或无法安全读取",
                location=SourceLocation(locator.canonical_path),
                affected=(REGISTRY_KEY,),
            ),
        )
    headings = document.find_headings(locator.audit_namespace, level=2)
    if len(headings) != 1:
        issues.append(
            Issue(
                summary="准入审计证据 H2 必须与定位表命名空间唯一一致",
                location=SourceLocation(locator.canonical_path),
                affected=(REGISTRY_KEY,),
            )
        )
        return tuple(issues)
    start = headings[0].line
    following = [heading.line for heading in document.headings if heading.level == 2 and heading.line > start]
    end = min(following, default=len(document.raw_lines) + 1)
    declaration = f"> `audit_record_key: {locator.audit_record_key}`"
    matches = tuple(line.strip() for line in document.raw_lines[start : end - 1] if line.strip() == declaration)
    if len(matches) != 1:
        issues.append(
            Issue(
                summary="准入审计证据必须在声明命名空间内恰好声明一次稳定 audit_record_key",
                location=SourceLocation(locator.canonical_path, line=start),
                affected=(REGISTRY_KEY,),
            )
        )
    return tuple(issues)


__all__ = [
    "AuditEvidenceLocator",
    "AuditEvidenceLocatorInspection",
    "inspect_audit_evidence_locators",
    "validate_audit_document",
]
