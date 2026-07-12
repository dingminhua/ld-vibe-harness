"""Strict identity parsing for LDVH specifications and authorized attachments."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from dataclasses import field as dataclass_field
from types import MappingProxyType
from typing import Literal

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap
from ruamel.yaml.events import DocumentStartEvent
from ruamel.yaml.scalarstring import DoubleQuotedScalarString
from ruamel.yaml.tokens import AliasToken, AnchorToken, KeyToken, ScalarToken, TagToken, ValueToken

from ldvh.diagnostics import Issue, SourceLocation
from ldvh.specs.markdown import MarkdownDocument

FormalKind = Literal["root", "spec", "attachment"]
IdentityDiscriminator = Literal["ldvh_spec", "ldvh_attachment"]

KEY_PATTERN = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*\Z")
SPEC_PATH_PATTERN = re.compile(r"specs/(?P<id>[0-9]{2,})-(?P<title>[^/]+)\.md\Z")
ATTACHMENT_PATH_PATTERN = re.compile(
    r"specs/attachments/(?P<parent_id>[0-9]{2,})\.Att\.(?P<sequence>[0-9]{2,})-(?P<title>[^/]+)\.md\Z"
)

ROOT_FIELDS = frozenset(
    {
        "spec_id",
        "spec_kind",
        "title",
        "status",
        "authority",
        "canonical_path",
        "parent_spec",
        "relation",
        "positioning",
        "scope",
        "basis",
        "related_specs",
        "code_consumption",
    }
)
SPEC_REQUIRED_FIELDS = frozenset(
    {
        "spec_key",
        "spec_id",
        "spec_kind",
        "title",
        "status",
        "canonical_path",
        "positioning",
        "scope",
        "basis",
        "authorized_attachments",
    }
)
SPEC_OPTIONAL_FIELDS = frozenset({"parent_spec", "relation", "supersedes"})
ATTACHMENT_REQUIRED_FIELDS = frozenset(
    {"attachment_key", "attachment_id", "title", "status", "canonical_path", "positioning"}
)
ATTACHMENT_OPTIONAL_FIELDS = frozenset({"supersedes"})
STATUSES = frozenset({"draft", "active", "retired"})


@dataclass(frozen=True, slots=True)
class FormalDocument:
    kind: FormalKind
    key: str
    current_id: str
    title: str
    status: str
    canonical_path: str
    positioning: str
    scope: str | None
    basis: tuple[str, ...]
    parent_spec: str | None
    relation: str | None
    authorized_attachments: tuple[str, ...]
    supersedes: tuple[str, ...]
    markdown: MarkdownDocument
    field_locations: Mapping[str, SourceLocation] = dataclass_field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        object.__setattr__(self, "field_locations", MappingProxyType(dict(self.field_locations)))


@dataclass(frozen=True, slots=True)
class IdentityResult:
    document: FormalDocument | None
    issues: tuple[Issue, ...]


def _issue(document: MarkdownDocument, summary: str, *, cause: str | None = None) -> Issue:
    return Issue(
        summary=summary,
        location=SourceLocation(document.relative_path, document.yaml_line),
        cause=cause,
    )


def _has_merge_key(tokens: list[object]) -> bool:
    return any(
        isinstance(tokens[index - 1], KeyToken)
        and isinstance(token, ScalarToken)
        and token.value == "<<"
        and token.style is None
        and isinstance(tokens[index + 1], ValueToken)
        for index, token in enumerate(tokens[1:-1], start=1)
    )


def _field_locations(identity: CommentedMap, document: MarkdownDocument) -> Mapping[str, SourceLocation]:
    locations: dict[str, SourceLocation] = {}
    for field_name in identity:
        line, _ = identity.lc.key(field_name)
        locations[str(field_name)] = SourceLocation(
            path=document.relative_path,
            line=(document.yaml_line or 0) + line + 1,
        )
    return MappingProxyType(locations)


def _load_identity_yaml(
    document: MarkdownDocument,
) -> tuple[tuple[IdentityDiscriminator, Mapping[str, object], Mapping[str, SourceLocation]] | None, list[Issue]]:
    issues: list[Issue] = []
    yaml = YAML(typ="rt")
    yaml.version = (1, 2)
    yaml.preserve_quotes = True
    yaml.allow_duplicate_keys = False

    try:
        events = list(yaml.parse(document.yaml_text))
        tokens = list(yaml.scan(document.yaml_text))
    except Exception as exc:  # ruamel exposes several parser/scanner exception types
        return None, [_issue(document, "YAML 身份块无法按 YAML 1.2 解析", cause=str(exc))]

    if sum(isinstance(event, DocumentStartEvent) for event in events) > 1:
        issues.append(_issue(document, "YAML 身份块不得包含多个 YAML 文档"))
    if any(isinstance(token, (AnchorToken, AliasToken)) for token in tokens):
        issues.append(_issue(document, "YAML 身份块不得包含锚点或别名"))
    if any(isinstance(token, TagToken) for token in tokens):
        issues.append(_issue(document, "YAML 身份块不得包含标签"))
    if _has_merge_key(tokens):
        issues.append(_issue(document, "YAML 身份块不得包含合并键"))
    if issues:
        return None, issues

    try:
        loaded = yaml.load(document.yaml_text)
    except Exception as exc:
        return None, [_issue(document, "YAML 身份块无法构造唯一映射", cause=str(exc))]
    if not isinstance(loaded, CommentedMap):
        return None, [_issue(document, "YAML 身份块顶层必须是映射")]
    if set(loaded) not in ({"ldvh_spec"}, {"ldvh_attachment"}):
        return None, [_issue(document, "YAML 身份块顶层必须且只能包含 ldvh_spec 或 ldvh_attachment")]

    discriminator: IdentityDiscriminator = "ldvh_spec" if "ldvh_spec" in loaded else "ldvh_attachment"
    root_value = loaded[discriminator]
    if not isinstance(root_value, CommentedMap):
        return None, [_issue(document, "YAML 身份对象必须是映射")]

    for field, value in root_value.items():
        if not isinstance(field, str):
            issues.append(_issue(document, f"YAML 身份字段名 {field!r} 必须是字符串"))
            continue
        if isinstance(value, str) and not isinstance(value, DoubleQuotedScalarString):
            issues.append(_issue(document, f"字符串字段 {field!r} 必须使用双引号"))
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, str) and not isinstance(item, DoubleQuotedScalarString):
                    issues.append(_issue(document, f"字符串列表字段 {field!r} 的成员必须使用双引号"))
    if issues:
        return None, issues
    return (discriminator, root_value, _field_locations(root_value, document)), []


def _require_string(
    identity: Mapping[str, object],
    field: str,
    document: MarkdownDocument,
    issues: list[Issue],
    *,
    allow_empty: bool = False,
) -> str:
    value = identity.get(field)
    if not isinstance(value, str) or (not allow_empty and not value):
        issues.append(_issue(document, f"字段 {field!r} 必须是{'可为空的' if allow_empty else '非空'}字符串"))
        return ""
    return str(value)


def _require_string_list(
    identity: Mapping[str, object],
    field: str,
    document: MarkdownDocument,
    issues: list[Issue],
    *,
    non_empty: bool = False,
) -> tuple[str, ...]:
    value = identity.get(field)
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        issues.append(_issue(document, f"字段 {field!r} 必须是非空字符串成员组成的列表"))
        return ()
    if non_empty and not value:
        issues.append(_issue(document, f"字段 {field!r} 不得为空列表"))
    return tuple(str(item) for item in value)


def _check_fields(
    identity: Mapping[str, object], required: frozenset[str], optional: frozenset[str], document: MarkdownDocument
) -> list[Issue]:
    actual = set(identity)
    missing = sorted(required - actual)
    unknown = sorted(actual - required - optional)
    issues: list[Issue] = []
    if missing:
        issues.append(_issue(document, f"YAML 身份缺少字段: {', '.join(missing)}"))
    if unknown:
        issues.append(_issue(document, f"YAML 身份包含未知字段: {', '.join(unknown)}"))
    return issues


def _validate_common_path_and_title(
    document: MarkdownDocument, current_id: str, title: str, canonical_path: str, *, attachment: bool
) -> list[Issue]:
    issues: list[Issue] = []
    pattern = ATTACHMENT_PATH_PATTERN if attachment else SPEC_PATH_PATTERN
    match = pattern.fullmatch(document.relative_path)
    if match is None:
        return [_issue(document, "文件路径不符合身份类型的候选路径规则")]
    expected_id = f"{match.group('parent_id')}.Att.{match.group('sequence')}" if attachment else match.group("id")
    if current_id != expected_id:
        issues.append(_issue(document, f"身份编号 {current_id!r} 与文件名编号 {expected_id!r} 不一致"))
    if title != document.h1:
        issues.append(_issue(document, "YAML title 与 H1 必须一致"))
    if canonical_path != document.relative_path:
        issues.append(_issue(document, "canonical_path 与当前仓库相对路径不一致"))
    return issues


def _parse_root(
    identity: Mapping[str, object],
    document: MarkdownDocument,
    field_locations: Mapping[str, SourceLocation],
) -> IdentityResult:
    issues = _check_fields(identity, ROOT_FIELDS, frozenset(), document)
    spec_id = _require_string(identity, "spec_id", document, issues)
    spec_kind = _require_string(identity, "spec_kind", document, issues)
    title = _require_string(identity, "title", document, issues)
    status = _require_string(identity, "status", document, issues)
    authority = _require_string(identity, "authority", document, issues)
    canonical_path = _require_string(identity, "canonical_path", document, issues)
    parent_spec = _require_string(identity, "parent_spec", document, issues, allow_empty=True)
    relation = _require_string(identity, "relation", document, issues, allow_empty=True)
    positioning = _require_string(identity, "positioning", document, issues)
    scope = _require_string(identity, "scope", document, issues)
    basis = _require_string_list(identity, "basis", document, issues)
    related_specs = _require_string_list(identity, "related_specs", document, issues)
    _require_string_list(identity, "code_consumption", document, issues, non_empty=True)

    expected = {
        "spec_id": "00",
        "spec_kind": "spec",
        "title": "理念与构成",
        "status": "active",
        "authority": "active",
        "canonical_path": "specs/00-理念与构成.md",
        "parent_spec": "",
        "relation": "",
    }
    actual = {
        "spec_id": spec_id,
        "spec_kind": spec_kind,
        "title": title,
        "status": status,
        "authority": authority,
        "canonical_path": canonical_path,
        "parent_spec": parent_spec,
        "relation": relation,
    }
    for field, expected_value in expected.items():
        if actual[field] != expected_value:
            issues.append(_issue(document, f"根规范字段 {field!r} 必须固定为 {expected_value!r}"))
    if basis:
        issues.append(_issue(document, "根规范 basis 必须为空列表"))
    if related_specs:
        issues.append(_issue(document, "根规范 related_specs 当前必须为空列表"))
    if document.relative_path != "specs/00-理念与构成.md" or document.h1 != "理念与构成":
        issues.append(_issue(document, "根规范路径与 H1 必须使用固定身份"))
    if issues:
        return IdentityResult(None, tuple(issues))
    return IdentityResult(
        FormalDocument(
            kind="root",
            key="ldvh-root",
            current_id="00",
            title=title,
            status=status,
            canonical_path=canonical_path,
            positioning=positioning,
            scope=scope,
            basis=(),
            parent_spec=None,
            relation=None,
            authorized_attachments=(),
            supersedes=(),
            markdown=document,
            field_locations=field_locations,
        ),
        (),
    )


def _parse_spec(
    identity: Mapping[str, object],
    document: MarkdownDocument,
    field_locations: Mapping[str, SourceLocation],
) -> IdentityResult:
    issues = _check_fields(identity, SPEC_REQUIRED_FIELDS, SPEC_OPTIONAL_FIELDS, document)
    key = _require_string(identity, "spec_key", document, issues)
    spec_id = _require_string(identity, "spec_id", document, issues)
    spec_kind = _require_string(identity, "spec_kind", document, issues)
    title = _require_string(identity, "title", document, issues)
    status = _require_string(identity, "status", document, issues)
    canonical_path = _require_string(identity, "canonical_path", document, issues)
    positioning = _require_string(identity, "positioning", document, issues)
    scope = _require_string(identity, "scope", document, issues)
    basis = _require_string_list(identity, "basis", document, issues)
    attachments = _require_string_list(identity, "authorized_attachments", document, issues)
    supersedes = _require_string_list(identity, "supersedes", document, issues) if "supersedes" in identity else ()
    parent_spec = _require_string(identity, "parent_spec", document, issues) if "parent_spec" in identity else None
    relation = _require_string(identity, "relation", document, issues) if "relation" in identity else None

    if not KEY_PATTERN.fullmatch(key):
        issues.append(_issue(document, "spec_key 格式无效"))
    if not re.fullmatch(r"[0-9]{2,}", spec_id):
        issues.append(_issue(document, "spec_id 必须是至少两位数字"))
    if spec_kind != "spec":
        issues.append(_issue(document, "spec_kind 必须固定为 'spec'"))
    if status not in STATUSES:
        issues.append(_issue(document, "status 必须是 draft、active 或 retired"))
    if (parent_spec is None) != (relation is None):
        issues.append(_issue(document, "parent_spec 与 relation 必须同时出现或同时省略"))
    if relation is not None and relation != "refines":
        issues.append(_issue(document, "当前普通规范 relation 只允许 'refines'"))
    issues.extend(_validate_common_path_and_title(document, spec_id, title, canonical_path, attachment=False))
    if issues:
        return IdentityResult(None, tuple(issues))
    return IdentityResult(
        FormalDocument(
            kind="spec",
            key=key,
            current_id=spec_id,
            title=title,
            status=status,
            canonical_path=canonical_path,
            positioning=positioning,
            scope=scope,
            basis=basis,
            parent_spec=parent_spec,
            relation=relation,
            authorized_attachments=attachments,
            supersedes=supersedes,
            markdown=document,
            field_locations=field_locations,
        ),
        (),
    )


def _parse_attachment(
    identity: Mapping[str, object],
    document: MarkdownDocument,
    field_locations: Mapping[str, SourceLocation],
) -> IdentityResult:
    issues = _check_fields(identity, ATTACHMENT_REQUIRED_FIELDS, ATTACHMENT_OPTIONAL_FIELDS, document)
    key = _require_string(identity, "attachment_key", document, issues)
    attachment_id = _require_string(identity, "attachment_id", document, issues)
    title = _require_string(identity, "title", document, issues)
    status = _require_string(identity, "status", document, issues)
    canonical_path = _require_string(identity, "canonical_path", document, issues)
    positioning = _require_string(identity, "positioning", document, issues)
    supersedes = _require_string_list(identity, "supersedes", document, issues) if "supersedes" in identity else ()

    if not KEY_PATTERN.fullmatch(key):
        issues.append(_issue(document, "attachment_key 格式无效"))
    if not re.fullmatch(r"[0-9]{2,}\.Att\.[0-9]{2,}", attachment_id):
        issues.append(_issue(document, "attachment_id 格式无效"))
    if status not in STATUSES:
        issues.append(_issue(document, "status 必须是 draft、active 或 retired"))
    issues.extend(_validate_common_path_and_title(document, attachment_id, title, canonical_path, attachment=True))
    if issues:
        return IdentityResult(None, tuple(issues))
    return IdentityResult(
        FormalDocument(
            kind="attachment",
            key=key,
            current_id=attachment_id,
            title=title,
            status=status,
            canonical_path=canonical_path,
            positioning=positioning,
            scope=None,
            basis=(),
            parent_spec=None,
            relation=None,
            authorized_attachments=(),
            supersedes=supersedes,
            markdown=document,
            field_locations=field_locations,
        ),
        (),
    )


def parse_identity(document: MarkdownDocument) -> IdentityResult:
    """Parse and validate one fixed YAML identity block."""

    loaded_identity, issues = _load_identity_yaml(document)
    if loaded_identity is None:
        return IdentityResult(None, tuple(issues))
    discriminator, identity, field_locations = loaded_identity
    attachment_path = document.relative_path.startswith("specs/attachments/")

    if discriminator == "ldvh_attachment":
        if not attachment_path:
            return IdentityResult(
                None,
                (_issue(document, "YAML 顶层 ldvh_attachment 只能用于授权附件候选路径"),),
            )
        return _parse_attachment(identity, document, field_locations)

    if attachment_path:
        return IdentityResult(
            None,
            (_issue(document, "YAML 顶层 ldvh_spec 不能用于授权附件候选路径"),),
        )
    if document.relative_path == "specs/00-理念与构成.md":
        return _parse_root(identity, document, field_locations)
    return _parse_spec(identity, document, field_locations)
