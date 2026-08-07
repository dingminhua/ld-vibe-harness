"""Bind only Helper-generated rule and implementation references to one source view."""

from __future__ import annotations

import copy
import json
import re
from contextvars import ContextVar, Token
from typing import Any

from ldvh.specs.identity import FormalDocument
from ldvh.specs.source import RuleSourceIdentity

_SOURCE_ARRAY_KEYS = frozenset({"sources", "source_refs", "evidence"})
_IDENTITY_DETAIL_KEYS = frozenset(
    {
        "rule_source_view",
        "implementation_source_view",
        "git_worktree_root",
    }
)


class GeneratedSourceReference(dict[str, Any]):
    """Marker for trusted Helper metadata; it adds no serialized field."""

    def copy(self) -> GeneratedSourceReference:
        return GeneratedSourceReference(self)

    def __copy__(self) -> GeneratedSourceReference:
        return self.copy()

    def __deepcopy__(self, memo: dict[int, object]) -> GeneratedSourceReference:
        return GeneratedSourceReference(copy.deepcopy(dict(self), memo))


def generated_source_reference(kind: str, locator: str, **details: Any) -> dict[str, Any]:
    result: dict[str, Any] = {"kind": kind, "locator": locator}
    if details:
        result["details"] = details
    if kind in {"rule", "implementation"}:
        return GeneratedSourceReference(result)
    return result


class RuleReferenceBinder:
    def __init__(self, identity: RuleSourceIdentity, documents: tuple[FormalDocument, ...]) -> None:
        self.identity = identity
        self.by_key = {document.key: document for document in documents}
        self.by_path = {document.canonical_path: document for document in documents}

    def bind(self, reference: GeneratedSourceReference) -> dict[str, Any]:
        kind = reference.get("kind")
        if kind not in {"rule", "implementation"}:
            raise ValueError("generated source reference has an unsupported kind")
        if "version" in reference:
            raise ValueError("generated source reference cannot pre-bind version")
        raw_details = reference.get("details", {})
        if not isinstance(raw_details, dict) or _IDENTITY_DETAIL_KEYS & set(raw_details):
            raise ValueError("generated source reference contains conflicting source identity details")
        result = {"kind": kind, "locator": reference["locator"]}
        if "observed_at" in reference:
            result["observed_at"] = reference["observed_at"]
        details = dict(raw_details)
        if kind == "rule":
            details = self._rule_details(str(reference["locator"]), details)
            details["rule_source_view"] = self.identity.view
            details["git_worktree_root"] = self.identity.git_worktree_root.as_posix()
        else:
            details["implementation_source_view"] = "working_tree"
            details["git_worktree_root"] = self.identity.git_worktree_root.as_posix()
        result["details"] = details
        return result

    def _rule_details(self, locator: str, details: dict[str, Any]) -> dict[str, Any]:
        document = self._document(locator, details)
        if document is None:
            return details
        details.setdefault("responsibility_key", document.key)
        details.setdefault("path", document.canonical_path)
        start, end, heading_path = self._range(document, locator, details)
        details.setdefault("heading_path", heading_path)
        details.setdefault("start_line", start)
        details.setdefault("end_line", end)
        return details

    def _document(self, locator: str, details: dict[str, Any]) -> FormalDocument | None:
        key = details.get("responsibility_key") or details.get("source_key")
        if isinstance(key, str) and key in self.by_key:
            return self.by_key[key]
        if "::" in locator and locator.split("::", 1)[0] in self.by_key:
            return self.by_key[locator.split("::", 1)[0]]
        path = re.split(r"#|:[0-9]+\Z", locator, maxsplit=1)[0]
        return self.by_path.get(path)

    @staticmethod
    def _range(
        document: FormalDocument,
        locator: str,
        details: dict[str, Any],
    ) -> tuple[int, int, list[str] | None]:
        if isinstance(details.get("start_line"), int) and isinstance(details.get("end_line"), int):
            heading = details.get("heading_path")
            return details["start_line"], details["end_line"], heading if isinstance(heading, list) else None
        line = details.get("line")
        if isinstance(line, int):
            return line, line, None
        if "::" in locator:
            title = locator.split("::", 1)[1]
            matches = document.markdown.find_headings(title)
            if len(matches) == 1:
                target = matches[0]
                end = min(
                    (
                        heading.line - 1
                        for heading in document.markdown.headings
                        if heading.line > target.line and heading.level <= target.level
                    ),
                    default=len(document.markdown.raw_lines),
                )
                if target.level == 3:
                    parents = [
                        heading.title
                        for heading in document.markdown.headings
                        if heading.level == 2 and heading.line < target.line
                    ]
                    return target.line, end, [parents[-1], target.title] if parents else [target.title]
                return target.line, end, [target.title]
        return 1, len(document.markdown.raw_lines), None


_BINDER: ContextVar[RuleReferenceBinder | None] = ContextVar("ldvh_source_reference_binder", default=None)


def set_reference_binder(binder: RuleReferenceBinder | None) -> Token[RuleReferenceBinder | None]:
    return _BINDER.set(binder)


def reset_reference_binder(token: Token[RuleReferenceBinder | None]) -> None:
    _BINDER.reset(token)


_OMIT = object()


def project_generated_sources(value: Any) -> Any:
    binder = _BINDER.get()

    def visit(item: Any) -> tuple[Any, bool]:
        if isinstance(item, GeneratedSourceReference):
            return (_OMIT, True) if binder is None else (binder.bind(item), True)
        if isinstance(item, dict):
            result: dict[str, Any] = {}
            generated = False
            for key, child in item.items():
                if isinstance(child, list):
                    projected: list[Any] = []
                    generated_identities: set[str] = set()
                    child_generated = False
                    for member in child:
                        mapped, was_generated = visit(member)
                        child_generated |= was_generated
                        if mapped is _OMIT:
                            continue
                        if key in _SOURCE_ARRAY_KEYS and was_generated:
                            identity = json.dumps(mapped, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                            if identity in generated_identities:
                                continue
                            generated_identities.add(identity)
                        projected.append(mapped)
                    result[key] = projected
                    generated |= child_generated
                else:
                    mapped, was_generated = visit(child)
                    if mapped is not _OMIT:
                        result[key] = mapped
                    generated |= was_generated
            return result, generated
        if isinstance(item, tuple):
            mapped_items = [visit(member) for member in item]
            return tuple(mapped for mapped, _ in mapped_items if mapped is not _OMIT), any(
                generated for _, generated in mapped_items
            )
        return item, False

    return visit(value)[0]


__all__ = [
    "GeneratedSourceReference",
    "RuleReferenceBinder",
    "generated_source_reference",
    "project_generated_sources",
    "reset_reference_binder",
    "set_reference_binder",
]
