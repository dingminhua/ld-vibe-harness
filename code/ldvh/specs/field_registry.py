"""Deterministic structure checks for the fact-object field registry.

The registry exposes exact identities, references, containers, and machine
shapes.  This module deliberately does not compare natural-language field
semantics.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from ldvh.diagnostics import Issue, SourceLocation
from ldvh.specs.fact_types import FactTypeDefinition, inspect_fact_types
from ldvh.specs.identity import KEY_PATTERN, FormalDocument
from ldvh.specs.markdown import Heading, MarkdownTable, parse_table_after_heading

REGISTRY_KEY = "fact-object-field-registry"
STRUCTURE_HEADING = "结构登记表"
REGISTRY_HEADING = "统一字段登记表"
STRUCTURE_HEADERS = (
    "structure_key",
    "JSON type",
    "definition_scope",
    "applies_to",
    "definition_ref",
    "status",
)
REGISTRY_HEADERS = (
    "field_key",
    "container_ref",
    "field_path",
    "JSON type",
    "field_role",
    "value_structure",
    "base_presence",
    "definition_scope",
    "applies_to",
    "definition_ref",
    "status",
)
STRUCTURE_DEFINITION_HEADERS = ("structure_key", "meaning", "not_meaning", "constraints")
STRUCTURE_ADMISSION_HEADERS = (
    "information_need",
    "compared_structure_keys",
    "decision",
    "resulting_structure_key",
    "rationale",
    "review_ref",
)
PUBLIC_FIELD_HEADERS = ("field_key", "字段", "JSON 类型", "共同出现规则", "共同语义与边界", "类型可定义")
MEMBER_FIELD_HEADERS = ("field_key", "字段", "JSON 类型", "出现规则", "含义与边界")
TYPE_FIELD_HEADERS = ("field_key", "field_path", "JSON type", "meaning", "not_meaning", "constraints")
ADMISSION_HEADERS = (
    "information_need",
    "compared_field_keys",
    "decision",
    "resulting_field_key",
    "rationale",
    "review_ref",
)
BINDING_HEADERS = ("field_key", "field_path", "presence", "type_constraints")
REVIEW_HEADERS = ("review_key", "reviewer", "reviewed_scope", "findings", "disposition")
DEFINITION_HEADERS = frozenset({PUBLIC_FIELD_HEADERS, MEMBER_FIELD_HEADERS, TYPE_FIELD_HEADERS})
JSON_TYPES = frozenset({"string", "boolean", "integer", "number", "object", "array"})
FIELD_ROLES = frozenset({"object-field", "structure-member"})
DEFINITION_SCOPES = frozenset({"foundation", "type"})
STATUSES = frozenset({"current", "retired"})
FIELD_PATH_PATTERN = re.compile(r"[a-z][a-z0-9_]*\Z")
REVIEW_KEY_PATTERN = re.compile(r"field-review-[0-9]{4}\Z")
DECISIONS = frozenset({"reuse", "promote", "differentiate", "new"})
PRESENCE_VALUES = frozenset({"required", "conditional", "forbidden"})
BASE_PRESENCE_VALUES = frozenset({"required", "conditional"})


@dataclass(frozen=True, slots=True)
class FieldStructure:
    structure_key: str
    json_type: str
    definition_scope: str
    applies_to: tuple[str, ...] | None
    definition_key: str
    definition_heading: str
    definition_row_key: str
    status: str
    source: SourceLocation


@dataclass(frozen=True, slots=True)
class FieldRegistration:
    field_key: str
    container_ref: str
    field_path: str
    json_type: str
    field_role: str
    value_structure: str | None
    base_presence: str
    definition_scope: str
    applies_to: tuple[str, ...] | None
    definition_key: str
    definition_heading: str
    status: str
    source: SourceLocation


@dataclass(frozen=True, slots=True)
class FieldRegistryInspection:
    structures: tuple[FieldStructure, ...]
    registrations: tuple[FieldRegistration, ...]
    fact_types: tuple[FactTypeDefinition, ...]
    issues: tuple[Issue, ...]

    @property
    def complete(self) -> bool:
        return not self.issues


def _issue(document: FormalDocument, summary: str, *, line: int | None = None) -> Issue:
    return Issue(
        summary=summary,
        location=SourceLocation(document.canonical_path, line=line),
        affected=(REGISTRY_KEY,),
    )


def _exact_h2_table(
    document: FormalDocument,
    title: str,
    headers: tuple[str, ...],
    issues: list[Issue],
) -> MarkdownTable | None:
    headings = document.markdown.find_headings(title, level=2)
    if len(headings) != 1:
        issues.append(_issue(document, f"{title} H2 必须恰好出现一次"))
        return None
    table = parse_table_after_heading(document.markdown, headings[0])
    if table is None or table.headers != headers:
        issues.append(_issue(document, f"{title} 必须紧接固定表头", line=headings[0].line))
        return None
    if not table.rows:
        issues.append(_issue(document, f"{title} 至少包含一个数据行", line=table.line))
        return None
    return table


def _parse_structures(registry: FormalDocument, issues: list[Issue]) -> tuple[FieldStructure, ...]:
    table = _exact_h2_table(registry, STRUCTURE_HEADING, STRUCTURE_HEADERS, issues)
    if table is None:
        return ()

    structures: list[FieldStructure] = []
    seen: set[str] = set()
    for offset, row in enumerate(table.rows, start=2):
        line = table.line + offset
        if len(row) != len(STRUCTURE_HEADERS) or any(not value for value in row):
            issues.append(_issue(registry, "结构登记行必须包含六个非空单元格", line=line))
            continue
        structure_key, json_type, definition_scope, applies_raw, definition_ref, status = row
        if KEY_PATTERN.fullmatch(structure_key) is None:
            issues.append(_issue(registry, f"非法 structure_key {structure_key!r}", line=line))
        if structure_key in seen:
            issues.append(_issue(registry, f"重复 structure_key {structure_key!r}", line=line))
        seen.add(structure_key)
        if json_type != "object":
            issues.append(_issue(registry, f"结构 {structure_key!r} 的 JSON type 必须是 object", line=line))
        if definition_scope not in DEFINITION_SCOPES:
            issues.append(_issue(registry, f"结构 {structure_key!r} 使用非法 definition_scope", line=line))
        if status not in STATUSES:
            issues.append(_issue(registry, f"结构 {structure_key!r} 使用非法 status", line=line))
        applies_to = _parse_applies_to(
            registry,
            definition_scope=definition_scope,
            raw_value=applies_raw,
            line=line,
            issues=issues,
        )
        reference_parts = definition_ref.split("::")
        if len(reference_parts) != 3 or not all(reference_parts) or reference_parts[2] != structure_key:
            issues.append(
                _issue(registry, f"结构 {structure_key!r} 的 definition_ref 格式或 structure_key 回显错误", line=line)
            )
            continue
        structures.append(
            FieldStructure(
                structure_key=structure_key,
                json_type=json_type,
                definition_scope=definition_scope,
                applies_to=applies_to,
                definition_key=reference_parts[0],
                definition_heading=reference_parts[1],
                definition_row_key=reference_parts[2],
                status=status,
                source=SourceLocation(registry.canonical_path, line=line),
            )
        )
    return tuple(structures)


def _parse_applies_to(
    registry: FormalDocument,
    *,
    definition_scope: str,
    raw_value: str,
    line: int,
    issues: list[Issue],
) -> tuple[str, ...] | None:
    if raw_value == "*":
        if definition_scope != "foundation":
            issues.append(_issue(registry, "只有 foundation 字段可以使用 applies_to *", line=line))
        return None

    values = tuple(raw_value.split(","))
    if (
        not raw_value
        or any(KEY_PATTERN.fullmatch(value) is None for value in values)
        or len(values) != len(set(values))
        or values != tuple(sorted(values))
    ):
        issues.append(_issue(registry, "applies_to 必须是唯一且按 ASCII 排序的 fact_type_key 闭集", line=line))
        return values
    if definition_scope == "foundation" and len(values) < 2:
        issues.append(_issue(registry, "部分复用的 foundation 字段必须至少适用于两个事实类型", line=line))
    if definition_scope == "type" and len(values) != 1:
        issues.append(_issue(registry, "type 字段必须恰好适用于一个事实类型", line=line))
    return values


def _parse_registrations(
    registry: FormalDocument,
    structures: tuple[FieldStructure, ...],
    issues: list[Issue],
) -> tuple[FieldRegistration, ...]:
    table = _exact_h2_table(registry, REGISTRY_HEADING, REGISTRY_HEADERS, issues)
    if table is None:
        return ()

    structure_keys = {structure.structure_key for structure in structures}
    registrations: list[FieldRegistration] = []
    seen_keys: set[str] = set()
    seen_locations: set[tuple[str, str]] = set()
    for offset, row in enumerate(table.rows, start=2):
        line = table.line + offset
        if len(row) != len(REGISTRY_HEADERS) or any(not value for value in row):
            issues.append(_issue(registry, "统一字段登记行必须包含十一个非空单元格", line=line))
            continue
        (
            field_key,
            container_ref,
            field_path,
            json_type,
            field_role,
            value_structure_raw,
            base_presence,
            definition_scope,
            applies_raw,
            definition_ref,
            status,
        ) = row
        if KEY_PATTERN.fullmatch(field_key) is None:
            issues.append(_issue(registry, f"非法 field_key {field_key!r}", line=line))
        if field_key in seen_keys:
            issues.append(_issue(registry, f"重复 field_key {field_key!r}", line=line))
        seen_keys.add(field_key)
        if container_ref not in structure_keys:
            issues.append(_issue(registry, f"字段 {field_key!r} 的 container_ref 未登记", line=line))
        if FIELD_PATH_PATTERN.fullmatch(field_path) is None:
            issues.append(_issue(registry, f"非法 field_path {field_path!r}", line=line))
        location_key = (container_ref, field_path)
        if location_key in seen_locations:
            issues.append(_issue(registry, f"字段位置重复 {container_ref!r} + {field_path!r}", line=line))
        seen_locations.add(location_key)
        if json_type not in JSON_TYPES:
            issues.append(_issue(registry, f"字段 {field_key!r} 使用非法 JSON type", line=line))
        if field_role not in FIELD_ROLES:
            issues.append(_issue(registry, f"字段 {field_key!r} 使用非法 field_role", line=line))
        expected_role = "object-field" if container_ref == "fact-object" else "structure-member"
        if field_role != expected_role:
            issues.append(_issue(registry, f"字段 {field_key!r} 的 field_role 与 container_ref 不一致", line=line))
        if base_presence not in BASE_PRESENCE_VALUES:
            issues.append(_issue(registry, f"字段 {field_key!r} 使用非法 base_presence", line=line))
        value_structure = None if value_structure_raw == "none" else value_structure_raw
        if value_structure is not None and value_structure not in structure_keys:
            issues.append(_issue(registry, f"字段 {field_key!r} 的 value_structure 未登记", line=line))
        if json_type == "object" and value_structure is None:
            issues.append(_issue(registry, f"object 字段 {field_key!r} 必须引用 value_structure", line=line))
        if json_type not in {"object", "array"} and value_structure is not None:
            issues.append(_issue(registry, f"标量字段 {field_key!r} 不得引用 value_structure", line=line))
        if definition_scope not in DEFINITION_SCOPES:
            issues.append(_issue(registry, f"字段 {field_key!r} 使用非法 definition_scope", line=line))
        if status not in STATUSES:
            issues.append(_issue(registry, f"字段 {field_key!r} 使用非法 status", line=line))
        applies_to = _parse_applies_to(
            registry,
            definition_scope=definition_scope,
            raw_value=applies_raw,
            line=line,
            issues=issues,
        )
        reference_parts = definition_ref.split("::")
        if len(reference_parts) != 3 or not all(reference_parts) or reference_parts[2] != field_key:
            issues.append(
                _issue(registry, f"字段 {field_key!r} 的 definition_ref 格式或 field_key 回显错误", line=line)
            )
            continue
        registrations.append(
            FieldRegistration(
                field_key=field_key,
                container_ref=container_ref,
                field_path=field_path,
                json_type=json_type,
                field_role=field_role,
                value_structure=value_structure,
                base_presence=base_presence,
                definition_scope=definition_scope,
                applies_to=applies_to,
                definition_key=reference_parts[0],
                definition_heading=reference_parts[1],
                status=status,
                source=SourceLocation(registry.canonical_path, line=line),
            )
        )
    return tuple(registrations)


def _definition_rows_in_h2(
    document: FormalDocument,
    heading: Heading,
) -> tuple[tuple[MarkdownTable, tuple[str, ...]], ...]:
    following_h2_lines = [
        item.line for item in document.markdown.headings if item.level == 2 and item.line > heading.line
    ]
    end_line = min(following_h2_lines, default=len(document.markdown.raw_lines) + 1)
    rows: list[tuple[MarkdownTable, tuple[str, ...]]] = []
    for item in document.markdown.headings:
        if item.line < heading.line or item.line >= end_line or item.level not in {2, 3}:
            continue
        table = parse_table_after_heading(document.markdown, item)
        if table is None or table.headers not in DEFINITION_HEADERS:
            continue
        rows.extend((table, row) for row in table.rows if row and len(row) == len(table.headers))
    return tuple(rows)


def _structure_definition_rows_in_h2(
    document: FormalDocument,
    heading: Heading,
) -> tuple[tuple[MarkdownTable, tuple[str, ...]], ...]:
    following_h2_lines = [
        item.line for item in document.markdown.headings if item.level == 2 and item.line > heading.line
    ]
    end_line = min(following_h2_lines, default=len(document.markdown.raw_lines) + 1)
    rows: list[tuple[MarkdownTable, tuple[str, ...]]] = []
    for item in document.markdown.headings:
        if item.line < heading.line or item.line >= end_line or item.level not in {2, 3}:
            continue
        table = parse_table_after_heading(document.markdown, item)
        if table is None or table.headers != STRUCTURE_DEFINITION_HEADERS:
            continue
        rows.extend((table, row) for row in table.rows if len(row) == len(table.headers))
    return tuple(rows)


def _validate_structures(
    structures: tuple[FieldStructure, ...],
    registrations: tuple[FieldRegistration, ...],
    documents_by_key: dict[str, FormalDocument],
    registry: FormalDocument,
    issues: list[Issue],
) -> None:
    structure_by_key = {structure.structure_key: structure for structure in structures}
    fact_object = structure_by_key.get("fact-object")
    if (
        fact_object is None
        or fact_object.status != "current"
        or fact_object.definition_scope != "foundation"
        or fact_object.applies_to is not None
    ):
        issues.append(_issue(registry, "fact-object 必须是 current、foundation 且 applies_to 为 * 的基础结构"))
    for structure in structures:
        if structure.status != "current":
            continue
        target = documents_by_key.get(structure.definition_key)
        if target is None:
            issues.append(_issue(registry, f"结构 {structure.structure_key!r} 的 definition_ref 目标不存在"))
            continue
        headings = target.markdown.find_headings(structure.definition_heading, level=2)
        if len(headings) != 1:
            issues.append(_issue(registry, f"结构 {structure.structure_key!r} 的 definition_ref 必须唯一指向 H2"))
            continue
        matches = [
            row
            for _, row in _structure_definition_rows_in_h2(target, headings[0])
            if row[0] == structure.definition_row_key
        ]
        if len(matches) != 1:
            issues.append(
                _issue(registry, f"结构 {structure.structure_key!r} 必须在 definition_ref H2 中恰有一个定义行")
            )
        if structure.definition_scope == "foundation" and structure.definition_key != REGISTRY_KEY:
            issues.append(_issue(registry, "foundation 结构必须由字段登记附件唯一定义"))
        if structure.definition_scope == "type" and structure.definition_key == REGISTRY_KEY:
            issues.append(_issue(registry, "type 结构必须由相应具体类型来源唯一定义"))
        expected_heading = (
            "基础结构定义表"
            if structure.definition_scope == "foundation" and structure.applies_to is None
            else "跨类型共享结构定义表"
            if structure.definition_scope == "foundation"
            else structure.definition_heading
        )
        if structure.definition_heading != expected_heading:
            issues.append(_issue(registry, f"结构 {structure.structure_key!r} 未使用其 definition_scope 对应的定义表"))
        if structure.status == "current" and not any(
            registration.container_ref == structure.structure_key and registration.status == "current"
            for registration in registrations
        ):
            issues.append(
                _issue(registry, f"current 结构 {structure.structure_key!r} 必须至少登记一个 current 直接字段")
            )

    registered_structure_keys = {structure.structure_key for structure in structures}
    seen_structure_definitions: set[str] = set()
    for document in documents_by_key.values():
        for heading in (item for item in document.markdown.headings if item.level == 2):
            for _, row in _structure_definition_rows_in_h2(document, heading):
                structure_key = row[0]
                if structure_key not in registered_structure_keys:
                    issues.append(_issue(registry, f"结构定义 {structure_key!r} 未进入结构登记表", line=heading.line))
                if structure_key in seen_structure_definitions:
                    issues.append(_issue(registry, f"结构 {structure_key!r} 存在多个定义行", line=heading.line))
                seen_structure_definitions.add(structure_key)
    for registration in registrations:
        if registration.status != "current":
            continue
        container = structure_by_key.get(registration.container_ref)
        if container is not None and container.status != "current":
            issues.append(_issue(registry, f"current 字段 {registration.field_key!r} 不得属于 retired container_ref"))
        if container is not None and not _applicability_covers(container.applies_to, registration.applies_to):
            issues.append(
                _issue(registry, f"字段 {registration.field_key!r} 的 applies_to 超出 container_ref 适用范围")
            )
        if registration.value_structure is None:
            continue
        target_structure = structure_by_key.get(registration.value_structure)
        if target_structure is not None and target_structure.status != "current":
            issues.append(_issue(registry, f"current 字段 {registration.field_key!r} 不得引用 retired value_structure"))
        if target_structure is not None and not _applicability_covers(
            target_structure.applies_to, registration.applies_to
        ):
            issues.append(
                _issue(registry, f"字段 {registration.field_key!r} 的 applies_to 超出 value_structure 适用范围")
            )


def _applicability_covers(available: tuple[str, ...] | None, needed: tuple[str, ...] | None) -> bool:
    if available is None:
        return True
    if needed is None:
        return False
    return set(needed).issubset(available)


def _validate_definition(
    registration: FieldRegistration,
    documents_by_key: dict[str, FormalDocument],
    registry: FormalDocument,
    issues: list[Issue],
) -> None:
    if registration.status != "current":
        return
    target = documents_by_key.get(registration.definition_key)
    if target is None:
        issues.append(
            _issue(
                registry,
                f"字段 {registration.field_key!r} 的 definition_ref 目标不存在",
                line=registration.source.line,
            )
        )
        return
    headings = target.markdown.find_headings(registration.definition_heading, level=2)
    if len(headings) != 1:
        issues.append(
            _issue(
                registry,
                f"字段 {registration.field_key!r} 的 definition_ref 必须唯一指向 H2",
                line=registration.source.line,
            )
        )
        return
    matches = [
        (table, row) for table, row in _definition_rows_in_h2(target, headings[0]) if row[0] == registration.field_key
    ]
    if len(matches) != 1:
        issues.append(
            _issue(
                registry,
                f"字段 {registration.field_key!r} 必须在 definition_ref H2 范围内恰有一个合法定义行",
                line=registration.source.line,
            )
        )
        return
    table, row = matches[0]
    values = dict(zip(table.headers, row, strict=True))
    defined_path = values.get("field_path", values.get("字段"))
    defined_type = values.get("JSON type", values.get("JSON 类型"))
    if defined_path != registration.field_path or defined_type != registration.json_type:
        issues.append(
            _issue(
                registry,
                f"字段 {registration.field_key!r} 的登记路径或 JSON 类型与唯一字段定义不一致",
                line=registration.source.line,
            )
        )
    if registration.definition_scope == "foundation" and registration.definition_key != REGISTRY_KEY:
        issues.append(_issue(registry, "foundation 字段必须由字段登记附件唯一定义", line=registration.source.line))
    if registration.definition_scope == "type" and registration.definition_key == REGISTRY_KEY:
        issues.append(_issue(registry, "type 字段必须由相应具体类型来源唯一定义", line=registration.source.line))
    if registration.definition_scope == "type" and table.headers != TYPE_FIELD_HEADERS:
        issues.append(_issue(registry, "type 字段必须由固定六列专属字段表定义", line=registration.source.line))
    expected_headers = (
        PUBLIC_FIELD_HEADERS
        if registration.definition_scope == "foundation"
        and registration.applies_to is None
        and registration.field_role == "object-field"
        else MEMBER_FIELD_HEADERS
        if registration.definition_scope == "foundation"
        and registration.applies_to is None
        and registration.field_role == "structure-member"
        else TYPE_FIELD_HEADERS
    )
    if table.headers != expected_headers:
        issues.append(
            _issue(
                registry,
                f"字段 {registration.field_key!r} 未使用其归口与角色对应的定义表",
                line=registration.source.line,
            )
        )
    expected_heading = (
        "公共顶层字段"
        if registration.definition_scope == "foundation"
        and registration.applies_to is None
        and registration.container_ref == "fact-object"
        else "来源与证据引用字段"
        if registration.definition_scope == "foundation"
        and registration.applies_to is None
        and registration.container_ref == "source-ref"
        else "事实对象关系字段"
        if registration.definition_scope == "foundation"
        and registration.applies_to is None
        and registration.container_ref == "relation"
        else "事实对象关系目标字段"
        if registration.definition_scope == "foundation"
        and registration.applies_to is None
        and registration.container_ref == "relation-target"
        else "跨类型共享字段定义表"
        if registration.definition_scope == "foundation"
        else registration.definition_heading
    )
    if registration.definition_heading != expected_heading:
        issues.append(
            _issue(
                registry,
                f"字段 {registration.field_key!r} 未使用其 container_ref 与 definition_scope 对应的定义章节",
                line=registration.source.line,
            )
        )


def _validate_reverse_definition_coverage(
    documents: tuple[FormalDocument, ...],
    registrations: tuple[FieldRegistration, ...],
    registry: FormalDocument,
    issues: list[Issue],
) -> None:
    registered_keys = {registration.field_key for registration in registrations}
    seen_definition_keys: set[str] = set()
    for document in documents:
        for heading in (item for item in document.markdown.headings if item.level == 2):
            for _, row in _definition_rows_in_h2(document, heading):
                field_key = row[0]
                if field_key not in registered_keys:
                    issues.append(
                        _issue(
                            registry,
                            f"字段定义 {field_key!r} 未进入统一字段登记表",
                            line=heading.line,
                        )
                    )
                if field_key in seen_definition_keys:
                    issues.append(_issue(registry, f"字段 {field_key!r} 存在多个定义行", line=heading.line))
                seen_definition_keys.add(field_key)


def _type_issue(definition: FactTypeDefinition, summary: str, *, line: int | None = None) -> Issue:
    return Issue(
        summary=summary,
        location=SourceLocation(definition.document.canonical_path, line=line),
        affected=(definition.source_key, definition.fact_type_key),
    )


def _type_h3(definition: FactTypeDefinition, title: str) -> tuple[Heading, ...]:
    start = definition.definition_heading.line
    following_h2 = [
        heading.line for heading in definition.document.markdown.headings if heading.level == 2 and heading.line > start
    ]
    end = min(following_h2, default=len(definition.document.markdown.raw_lines) + 1)
    return tuple(
        heading
        for heading in definition.document.markdown.headings
        if heading.level == 3 and heading.title == title and start < heading.line < end
    )


def _required_type_table(
    definition: FactTypeDefinition,
    title: str,
    headers: tuple[str, ...],
    issues: list[Issue],
) -> MarkdownTable | None:
    headings = _type_h3(definition, title)
    if len(headings) != 1:
        issues.append(_type_issue(definition, f"类型定义中 {title} H3 必须恰好出现一次"))
        return None
    table = parse_table_after_heading(definition.document.markdown, headings[0])
    if table is None or table.headers != headers:
        issues.append(_type_issue(definition, f"{title} 必须紧接固定表头", line=headings[0].line))
        return None
    if not table.rows:
        issues.append(_type_issue(definition, f"{title} 至少包含一个数据行", line=table.line))
        return None
    return table


def _optional_type_table(
    definition: FactTypeDefinition,
    *,
    title: str,
    headers: tuple[str, ...],
    empty_statement: str,
    issues: list[Issue],
) -> MarkdownTable | None:
    headings = _type_h3(definition, title)
    if len(headings) != 1:
        issues.append(_type_issue(definition, f"类型定义中 {title} H3 必须恰好出现一次"))
        return None
    heading = headings[0]
    table = parse_table_after_heading(definition.document.markdown, heading)
    if table is not None:
        if table.headers != headers:
            issues.append(_type_issue(definition, f"{title} 使用了错误表头", line=table.line))
            return None
        if not table.rows:
            issues.append(_type_issue(definition, f"{title} 不得建立空表", line=table.line))
            return None
        return table
    next_heading_lines = [
        item.line for item in definition.document.markdown.headings if item.line > heading.line and item.level in {2, 3}
    ]
    end = min(next_heading_lines, default=len(definition.document.markdown.raw_lines) + 1)
    content = tuple(
        line.strip() for line in definition.document.markdown.raw_lines[heading.line : end - 1] if line.strip()
    )
    if content != (empty_statement,):
        issues.append(_type_issue(definition, f"{title} 无表时必须使用固定声明", line=heading.line))
    return None


def _validate_registration_type_targets(
    structures: tuple[FieldStructure, ...],
    registrations: tuple[FieldRegistration, ...],
    fact_types: tuple[FactTypeDefinition, ...],
    registry: FormalDocument,
    issues: list[Issue],
) -> None:
    definitions_by_type = {definition.fact_type_key: definition for definition in fact_types}
    for item in (*structures, *registrations):
        item_key = item.structure_key if isinstance(item, FieldStructure) else item.field_key
        if item.status != "current":
            continue
        if item.applies_to is not None:
            unknown = tuple(key for key in item.applies_to if key not in definitions_by_type)
            if unknown:
                issues.append(_issue(registry, f"登记 {item_key!r} 的 applies_to 包含未知事实类型"))
        if item.definition_scope != "type" or item.applies_to is None or len(item.applies_to) != 1:
            continue
        definition = definitions_by_type.get(item.applies_to[0])
        if definition is None:
            continue
        if (
            item.definition_key != definition.source_key
            or item.definition_heading != definition.definition_heading.title
        ):
            issues.append(_issue(registry, f"type 登记 {item_key!r} 的 definition_ref 未指向其唯一适用类型"))


def _parse_review_keys(
    definition: FactTypeDefinition,
    issues: list[Issue],
) -> set[str]:
    table = _required_type_table(definition, "字段独立复核", REVIEW_HEADERS, issues)
    if table is None:
        return set()
    review_keys: set[str] = set()
    for offset, row in enumerate(table.rows, start=2):
        line = table.line + offset
        if len(row) != len(REVIEW_HEADERS) or any(not value for value in row):
            issues.append(_type_issue(definition, "字段独立复核行必须包含五个非空单元格", line=line))
            continue
        review_key = row[0]
        if REVIEW_KEY_PATTERN.fullmatch(review_key) is None:
            issues.append(_type_issue(definition, f"非法 review_key {review_key!r}", line=line))
        if review_key in review_keys:
            issues.append(_type_issue(definition, f"重复 review_key {review_key!r}", line=line))
        review_keys.add(review_key)
    return review_keys


def _parse_admissions(
    definition: FactTypeDefinition,
    registrations_by_key: dict[str, FieldRegistration],
    review_keys: set[str],
    issues: list[Issue],
) -> tuple[set[str], tuple[str, ...]]:
    table = _required_type_table(definition, "字段准入记录", ADMISSION_HEADERS, issues)
    if table is None:
        return set(), ()
    information_needs: set[str] = set()
    resulting_keys: set[str] = set()
    promoted_keys: list[str] = []
    for offset, row in enumerate(table.rows, start=2):
        line = table.line + offset
        if len(row) != len(ADMISSION_HEADERS) or any(not value for value in row):
            issues.append(_type_issue(definition, "字段准入记录行必须包含六个非空单元格", line=line))
            continue
        information_need, compared_raw, decision, resulting_key, _, review_ref = row
        if information_need in information_needs:
            issues.append(_type_issue(definition, f"重复 information_need {information_need!r}", line=line))
        information_needs.add(information_need)
        if resulting_key in resulting_keys:
            issues.append(_type_issue(definition, f"重复 resulting_field_key {resulting_key!r}", line=line))
        compared: tuple[str, ...] = ()
        if compared_raw != "none":
            compared = tuple(compared_raw.split(","))
            if compared != tuple(sorted(set(compared))) or any(key not in registrations_by_key for key in compared):
                issues.append(_type_issue(definition, "compared_field_keys 必须引用已登记字段并唯一排序", line=line))
        if decision not in DECISIONS:
            issues.append(_type_issue(definition, f"非法字段准入 decision {decision!r}", line=line))
        elif decision in {"reuse", "promote"} and resulting_key not in compared:
            issues.append(
                _type_issue(definition, f"{decision} 决定必须在 compared_field_keys 中包含结果字段", line=line)
            )
        elif decision == "differentiate" and not compared:
            issues.append(_type_issue(definition, "differentiate 决定必须列出被区分的已登记字段", line=line))
        registration = registrations_by_key.get(resulting_key)
        if registration is None or registration.status != "current":
            issues.append(_type_issue(definition, f"resulting_field_key {resulting_key!r} 未登记为 current", line=line))
        elif decision == "new" and (
            registration.definition_scope != "type" or registration.applies_to != (definition.fact_type_key,)
        ):
            issues.append(_type_issue(definition, "new 决定必须产生归属于本类型的 type 字段", line=line))
        elif decision == "differentiate" and (
            registration.definition_scope != "type" or registration.applies_to != (definition.fact_type_key,)
        ):
            issues.append(_type_issue(definition, "differentiate 决定必须产生归属于本类型的 type 字段", line=line))
        elif decision == "promote" and (
            registration.definition_scope != "foundation"
            or (registration.applies_to is not None and definition.fact_type_key not in registration.applies_to)
        ):
            issues.append(
                _type_issue(definition, "promote 决定必须指向已提升并适用于本类型的 foundation 字段", line=line)
            )
        elif decision == "promote":
            promoted_keys.append(resulting_key)
        elif (
            decision == "reuse"
            and registration.applies_to is not None
            and definition.fact_type_key not in registration.applies_to
        ):
            issues.append(_type_issue(definition, "reuse 决定引用了不适用于本类型的字段", line=line))
        reference_parts = review_ref.split("::")
        if (
            len(reference_parts) != 3
            or reference_parts[0] != definition.source_key
            or reference_parts[1] != definition.definition_heading.title
            or reference_parts[2] not in review_keys
        ):
            issues.append(_type_issue(definition, "review_ref 未指向本类型字段独立复核表中的有效行", line=line))
        resulting_keys.add(resulting_key)
    return resulting_keys, tuple(promoted_keys)


def _validate_bindings(
    definition: FactTypeDefinition,
    registrations: tuple[FieldRegistration, ...],
    admission_keys: set[str],
    issues: list[Issue],
) -> set[str]:
    table = _required_type_table(definition, "类型字段使用绑定", BINDING_HEADERS, issues)
    if table is None:
        return set()
    applicable = {
        registration.field_key: registration
        for registration in registrations
        if registration.status == "current"
        and registration.container_ref == "fact-object"
        and registration.field_role == "object-field"
        and (registration.applies_to is None or definition.fact_type_key in registration.applies_to)
    }
    bound: set[str] = set()
    for offset, row in enumerate(table.rows, start=2):
        line = table.line + offset
        if len(row) != len(BINDING_HEADERS) or any(not value for value in row):
            issues.append(_type_issue(definition, "类型字段使用绑定行必须包含四个非空单元格", line=line))
            continue
        field_key, field_path, presence, type_constraints = row
        registration = applicable.get(field_key)
        if registration is None:
            issues.append(_type_issue(definition, f"绑定字段 {field_key!r} 未登记、非对象直接字段或不适用", line=line))
        elif field_path != registration.field_path:
            issues.append(_type_issue(definition, f"绑定字段 {field_key!r} 的 field_path 与登记不一致", line=line))
        if presence not in PRESENCE_VALUES:
            issues.append(_type_issue(definition, f"绑定字段 {field_key!r} 使用非法 presence", line=line))
        if registration is not None and registration.base_presence == "required" and presence != "required":
            issues.append(_type_issue(definition, f"基础必填字段 {field_key!r} 必须绑定为 required", line=line))
        if registration is not None and registration.applies_to is not None and presence == "forbidden":
            issues.append(
                _type_issue(definition, f"明确适用于本类型的字段 {field_key!r} 不得绑定为 forbidden", line=line)
            )
        if registration is not None and registration.definition_scope == "type":
            if presence == "required" and type_constraints != "none":
                issues.append(
                    _type_issue(
                        definition,
                        f"required type 字段 {field_key!r} 的 type_constraints 必须为 none",
                        line=line,
                    )
                )
            if presence == "conditional" and (
                not type_constraints.startswith("出现条件：") or type_constraints == "出现条件："
            ):
                issues.append(
                    _type_issue(
                        definition,
                        f"conditional type 字段 {field_key!r} 的 type_constraints 必须只声明出现条件",
                        line=line,
                    )
                )
        if field_key in bound:
            issues.append(_type_issue(definition, f"类型重复绑定字段 {field_key!r}", line=line))
        bound.add(field_key)
        if field_key not in admission_keys:
            issues.append(_type_issue(definition, f"绑定字段 {field_key!r} 没有字段准入记录", line=line))
    missing = sorted(set(applicable) - bound)
    extra = sorted(bound - set(applicable))
    if missing:
        issues.append(_type_issue(definition, f"类型字段使用绑定缺少适用字段：{', '.join(missing)}"))
    if extra:
        issues.append(_type_issue(definition, f"类型字段使用绑定包含不适用字段：{', '.join(extra)}"))
    return bound


def _validate_type_definitions(
    definition: FactTypeDefinition,
    registrations: tuple[FieldRegistration, ...],
    issues: list[Issue],
) -> None:
    expected = {
        registration.field_key: registration
        for registration in registrations
        if registration.status == "current"
        and registration.definition_scope == "type"
        and registration.applies_to == (definition.fact_type_key,)
    }
    table = _optional_type_table(
        definition,
        title="类型专属字段定义",
        headers=TYPE_FIELD_HEADERS,
        empty_statement="本类型没有类型专属字段",
        issues=issues,
    )
    if table is None:
        if expected:
            issues.append(_type_issue(definition, "本类型已登记 type 字段但没有专属字段定义表"))
        return
    defined: set[str] = set()
    for offset, row in enumerate(table.rows, start=2):
        line = table.line + offset
        if len(row) != len(TYPE_FIELD_HEADERS) or any(not value for value in row):
            issues.append(_type_issue(definition, "类型专属字段定义行必须包含六个非空单元格", line=line))
            continue
        field_key, field_path, json_type, _, _, _ = row
        registration = expected.get(field_key)
        if registration is None:
            issues.append(_type_issue(definition, f"专属字段 {field_key!r} 未登记为本类型 type 字段", line=line))
        elif field_path != registration.field_path or json_type != registration.json_type:
            issues.append(_type_issue(definition, f"专属字段 {field_key!r} 的路径或类型与登记不一致", line=line))
        if field_key in defined:
            issues.append(_type_issue(definition, f"重复定义专属字段 {field_key!r}", line=line))
        defined.add(field_key)
    missing = sorted(set(expected) - defined)
    if missing:
        issues.append(_type_issue(definition, f"类型专属字段定义缺少已登记字段：{', '.join(missing)}"))


def _validate_type_structures(
    definition: FactTypeDefinition,
    structures: tuple[FieldStructure, ...],
    review_keys: set[str],
    issues: list[Issue],
) -> tuple[str, ...]:
    structures_by_key = {structure.structure_key: structure for structure in structures}
    admission_table = _optional_type_table(
        definition,
        title="结构准入记录",
        headers=STRUCTURE_ADMISSION_HEADERS,
        empty_statement="本类型没有结构准入事项",
        issues=issues,
    )
    information_needs: set[str] = set()
    admitted: set[str] = set()
    promoted: list[str] = []
    if admission_table is not None:
        for offset, row in enumerate(admission_table.rows, start=2):
            line = admission_table.line + offset
            if len(row) != len(STRUCTURE_ADMISSION_HEADERS) or any(not value for value in row):
                issues.append(_type_issue(definition, "结构准入记录行必须包含六个非空单元格", line=line))
                continue
            information_need, compared_raw, decision, resulting_key, _, review_ref = row
            if information_need in information_needs:
                issues.append(_type_issue(definition, f"重复结构 information_need {information_need!r}", line=line))
            information_needs.add(information_need)
            if resulting_key in admitted:
                issues.append(_type_issue(definition, f"重复 resulting_structure_key {resulting_key!r}", line=line))
            compared: tuple[str, ...] = ()
            if compared_raw != "none":
                compared = tuple(compared_raw.split(","))
                if compared != tuple(sorted(set(compared))) or any(key not in structures_by_key for key in compared):
                    issues.append(
                        _type_issue(definition, "compared_structure_keys 必须引用已登记结构并唯一排序", line=line)
                    )
            structure = structures_by_key.get(resulting_key)
            if decision not in DECISIONS:
                issues.append(_type_issue(definition, f"非法结构准入 decision {decision!r}", line=line))
            elif decision in {"reuse", "promote"} and resulting_key not in compared:
                issues.append(
                    _type_issue(definition, f"{decision} 决定必须在 compared_structure_keys 中包含结果结构", line=line)
                )
            elif decision == "differentiate" and not compared:
                issues.append(_type_issue(definition, "differentiate 决定必须列出被区分的已登记结构", line=line))
            if structure is None or structure.status != "current":
                issues.append(
                    _type_issue(definition, f"resulting_structure_key {resulting_key!r} 未登记为 current", line=line)
                )
            elif decision in {"new", "differentiate"} and (
                structure.definition_scope != "type" or structure.applies_to != (definition.fact_type_key,)
            ):
                issues.append(_type_issue(definition, f"{decision} 决定必须产生归属于本类型的 type 结构", line=line))
            elif decision == "promote" and (
                structure.definition_scope != "foundation"
                or (structure.applies_to is not None and definition.fact_type_key not in structure.applies_to)
            ):
                issues.append(_type_issue(definition, "promote 决定必须指向适用于本类型的 foundation 结构", line=line))
            elif decision == "promote":
                promoted.append(resulting_key)
            elif (
                decision == "reuse"
                and structure.applies_to is not None
                and definition.fact_type_key not in structure.applies_to
            ):
                issues.append(_type_issue(definition, "reuse 决定引用了不适用于本类型的结构", line=line))
            reference_parts = review_ref.split("::")
            if (
                len(reference_parts) != 3
                or reference_parts[0] != definition.source_key
                or reference_parts[1] != definition.definition_heading.title
                or reference_parts[2] not in review_keys
            ):
                issues.append(
                    _type_issue(definition, "结构 review_ref 未指向本类型字段独立复核表中的有效行", line=line)
                )
            admitted.add(resulting_key)

    expected = {
        structure.structure_key: structure
        for structure in structures
        if structure.status == "current"
        and structure.definition_scope == "type"
        and structure.applies_to == (definition.fact_type_key,)
    }
    expected_admissions = {
        structure.structure_key
        for structure in structures
        if structure.status == "current"
        and structure.applies_to is not None
        and definition.fact_type_key in structure.applies_to
    }
    definition_table = _optional_type_table(
        definition,
        title="类型专属结构定义",
        headers=STRUCTURE_DEFINITION_HEADERS,
        empty_statement="本类型没有类型专属结构",
        issues=issues,
    )
    defined: set[str] = set()
    if definition_table is not None:
        for offset, row in enumerate(definition_table.rows, start=2):
            line = definition_table.line + offset
            if len(row) != len(STRUCTURE_DEFINITION_HEADERS) or any(not value for value in row):
                issues.append(_type_issue(definition, "类型专属结构定义行必须包含四个非空单元格", line=line))
                continue
            structure_key = row[0]
            if structure_key in defined:
                issues.append(_type_issue(definition, f"重复定义专属结构 {structure_key!r}", line=line))
            defined.add(structure_key)
    missing_definitions = sorted(set(expected) - defined)
    if missing_definitions:
        issues.append(_type_issue(definition, f"类型专属结构定义缺少已登记结构：{', '.join(missing_definitions)}"))
    missing_admissions = sorted(expected_admissions - admitted)
    if missing_admissions:
        issues.append(_type_issue(definition, f"类型专属结构缺少准入记录：{', '.join(missing_admissions)}"))
    extra_definitions = sorted(defined - set(expected))
    if extra_definitions:
        issues.append(_type_issue(definition, f"类型专属结构定义包含非本类型结构：{', '.join(extra_definitions)}"))
    return tuple(promoted)


def _validate_fact_type_fields(
    fact_types: tuple[FactTypeDefinition, ...],
    structures: tuple[FieldStructure, ...],
    registrations: tuple[FieldRegistration, ...],
    registry: FormalDocument,
    issues: list[Issue],
) -> None:
    registrations_by_key = {registration.field_key: registration for registration in registrations}
    field_promotion_sources: dict[str, list[str]] = {}
    structure_promotion_sources: dict[str, list[str]] = {}
    for definition in fact_types:
        review_keys = _parse_review_keys(definition, issues)
        promoted_structures = _validate_type_structures(definition, structures, review_keys, issues)
        for structure_key in promoted_structures:
            structure_promotion_sources.setdefault(structure_key, []).append(definition.fact_type_key)
        admissions, promoted_keys = _parse_admissions(definition, registrations_by_key, review_keys, issues)
        for field_key in promoted_keys:
            field_promotion_sources.setdefault(field_key, []).append(definition.fact_type_key)
        expected_nonuniversal_admissions = {
            registration.field_key
            for registration in registrations
            if registration.status == "current"
            and registration.applies_to is not None
            and definition.fact_type_key in registration.applies_to
        }
        missing_admissions = sorted(expected_nonuniversal_admissions - admissions)
        if missing_admissions:
            issues.append(_type_issue(definition, f"类型缺少非全局字段准入记录：{', '.join(missing_admissions)}"))
        _validate_bindings(definition, registrations, admissions, issues)
        _validate_type_definitions(definition, registrations, issues)
    for registration in registrations:
        if (
            registration.status != "current"
            or registration.definition_scope != "foundation"
            or registration.applies_to is None
        ):
            continue
        sources = field_promotion_sources.get(registration.field_key, [])
        if len(sources) != 1:
            rendered = ", ".join(sources) if sources else "none"
            issues.append(
                _issue(
                    registry,
                    f"有限共享字段 {registration.field_key!r} 必须恰有一个 promote 来源；当前为 {rendered}",
                    line=registration.source.line,
                )
            )
    for structure in structures:
        if structure.status != "current" or structure.definition_scope != "foundation" or structure.applies_to is None:
            continue
        sources = structure_promotion_sources.get(structure.structure_key, [])
        if len(sources) != 1:
            rendered = ", ".join(sources) if sources else "none"
            issues.append(
                _issue(
                    registry,
                    f"有限共享结构 {structure.structure_key!r} 必须恰有一个 promote 来源；当前为 {rendered}",
                    line=structure.source.line,
                )
            )


def inspect_field_registry(documents: tuple[FormalDocument, ...]) -> FieldRegistryInspection:
    """Inspect exact field registration structure without interpreting semantics."""

    registries = tuple(document for document in documents if document.key == REGISTRY_KEY)
    if len(registries) != 1:
        issue = Issue(
            summary="当前规则源必须恰好包含一份事实对象统一字段登记",
            location=SourceLocation("."),
            affected=(REGISTRY_KEY,),
        )
        return FieldRegistryInspection((), (), (), (issue,))

    registry = registries[0]
    issues: list[Issue] = []
    structures = _parse_structures(registry, issues)
    registrations = _parse_registrations(registry, structures, issues)
    fact_type_inspection = inspect_fact_types(documents)
    issues.extend(fact_type_inspection.issues)
    documents_by_key = {document.key: document for document in documents}
    _validate_structures(structures, registrations, documents_by_key, registry, issues)
    _validate_registration_type_targets(
        structures,
        registrations,
        fact_type_inspection.definitions,
        registry,
        issues,
    )
    for registration in registrations:
        _validate_definition(registration, documents_by_key, registry, issues)
    _validate_reverse_definition_coverage(documents, registrations, registry, issues)
    _validate_fact_type_fields(fact_type_inspection.definitions, structures, registrations, registry, issues)
    return FieldRegistryInspection(structures, registrations, fact_type_inspection.definitions, tuple(issues))
