"""Cross-document identity, relationship, authorization, and cycle checks."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable
from dataclasses import dataclass

from ldvh.diagnostics import Issue, SourceLocation
from ldvh.specs.identity import FormalDocument


@dataclass(frozen=True, slots=True)
class BasisReachabilityOverlap:
    spec_key: str
    direct_basis: str
    reachable_via: str


@dataclass(frozen=True, slots=True)
class GraphResult:
    active_documents_passing_implemented_checks: tuple[FormalDocument, ...]
    issues: tuple[Issue, ...]
    incomplete_keys: tuple[str, ...]
    attachment_parents: tuple[tuple[str, str], ...]
    basis_reachability_overlaps: tuple[BasisReachabilityOverlap, ...]
    relationship_target_paths: tuple[tuple[str, str], ...]


def _issue(document: FormalDocument, summary: str, *affected: str) -> Issue:
    return Issue(
        summary=summary,
        location=SourceLocation(document.canonical_path, document.markdown.yaml_line),
        affected=affected or (document.key,),
    )


def _duplicates(values: Iterable[str]) -> set[str]:
    return {value for value, count in Counter(values).items() if count > 1}


def _cycle_members(edges: dict[str, tuple[str, ...]]) -> set[str]:
    visiting: set[str] = set()
    visited: set[str] = set()
    stack: list[str] = []
    cycles: set[str] = set()

    def visit(node: str) -> None:
        if node in visiting:
            index = stack.index(node)
            cycles.update(stack[index:])
            return
        if node in visited:
            return
        visiting.add(node)
        stack.append(node)
        for target in edges.get(node, ()):
            if target in edges:
                visit(target)
        stack.pop()
        visiting.remove(node)
        visited.add(node)

    for node in edges:
        visit(node)
    return cycles


def _reachable(start: str, target: str, edges: dict[str, tuple[str, ...]]) -> bool:
    pending = list(edges.get(start, ()))
    seen: set[str] = set()
    while pending:
        node = pending.pop()
        if node == target:
            return True
        if node in seen:
            continue
        seen.add(node)
        pending.extend(edges.get(node, ()))
    return False


def validate_graph(documents: Iterable[FormalDocument]) -> GraphResult:
    """Validate relations and retain the active range passing implemented graph checks."""

    docs = tuple(documents)
    issues: list[Issue] = []
    blocked: set[str] = set()

    duplicate_keys = _duplicates(document.key for document in docs)
    duplicate_spec_ids = _duplicates(document.current_id for document in docs if document.kind in {"root", "spec"})
    duplicate_attachment_ids = _duplicates(document.current_id for document in docs if document.kind == "attachment")
    for document in docs:
        if document.key in duplicate_keys:
            issues.append(_issue(document, f"职责标识符 {document.key!r} 重复"))
            blocked.add(document.key)
        if document.kind in {"root", "spec"} and document.current_id in duplicate_spec_ids:
            issues.append(_issue(document, f"规范编号 {document.current_id!r} 重复"))
            blocked.add(document.key)
        if document.kind == "attachment" and document.current_id in duplicate_attachment_ids:
            issues.append(_issue(document, f"附件编号 {document.current_id!r} 重复"))
            blocked.add(document.key)

    by_key: dict[str, FormalDocument] = {
        document.key: document for document in docs if document.key not in duplicate_keys
    }
    active_specs = {
        key: document
        for key, document in by_key.items()
        if document.status == "active" and document.kind in {"root", "spec"}
    }
    active_attachments = {
        key: document
        for key, document in by_key.items()
        if document.status == "active" and document.kind == "attachment"
    }

    basis_edges: dict[str, tuple[str, ...]] = {}
    parent_edges: dict[str, tuple[str, ...]] = {}
    supersedes_edges: dict[str, tuple[str, ...]] = {}

    for key, document in active_specs.items():
        basis_edges[key] = document.basis
        parent_edges[key] = (document.parent_spec,) if document.parent_spec else ()
        if len(set(document.basis)) != len(document.basis):
            issues.append(_issue(document, "basis 不得包含重复 key"))
            blocked.add(key)
        if document.parent_spec == key or key in document.basis:
            issues.append(_issue(document, "规范关系不得自指"))
            blocked.add(key)
        for target_key in document.basis:
            target = active_specs.get(target_key)
            if target is None:
                issues.append(_issue(document, f"basis 目标 {target_key!r} 缺失、类型错误或非 active"))
                blocked.add(key)
        if document.parent_spec is not None:
            target = active_specs.get(document.parent_spec)
            if target is None:
                issues.append(_issue(document, f"parent_spec 目标 {document.parent_spec!r} 缺失、类型错误或非 active"))
                blocked.add(key)
        if len(set(document.authorized_attachments)) != len(document.authorized_attachments):
            issues.append(_issue(document, "authorized_attachments 不得包含重复 key"))
            blocked.add(key)

    for relation_name, edges in (("basis", basis_edges), ("结构归属", parent_edges)):
        for key in _cycle_members(edges):
            document = active_specs[key]
            issues.append(_issue(document, f"{relation_name} 关系形成循环"))
            blocked.add(key)

    overlaps: list[BasisReachabilityOverlap] = []
    for key, document in active_specs.items():
        for direct_basis in document.basis:
            for via in document.basis:
                if via != direct_basis and _reachable(via, direct_basis, basis_edges):
                    overlaps.append(BasisReachabilityOverlap(key, direct_basis, via))

    authorizers: dict[str, list[FormalDocument]] = defaultdict(list)
    for document in active_specs.values():
        for attachment_key in document.authorized_attachments:
            authorizers[attachment_key].append(document)
            if attachment_key not in active_attachments:
                issues.append(_issue(document, f"授权附件 {attachment_key!r} 缺失、类型错误或非 active"))
                blocked.add(document.key)

    attachment_parents: list[tuple[str, str]] = []
    for key, attachment in active_attachments.items():
        parents = authorizers.get(key, [])
        if len(parents) != 1:
            issues.append(_issue(attachment, "active 附件必须且只能由一个 active 父规范授权"))
            blocked.add(key)
            continue
        parent = parents[0]
        attachment_parent_id = attachment.current_id.split(".Att.", 1)[0]
        if attachment_parent_id != parent.current_id:
            issues.append(_issue(attachment, "attachment_id 的父规范编号与授权父规范不一致", key, parent.key))
            blocked.update({key, parent.key})
            continue
        attachment_parents.append((key, parent.key))

    for document in docs:
        if len(set(document.supersedes)) != len(document.supersedes):
            issues.append(_issue(document, "supersedes 不得包含重复 key"))
            blocked.add(document.key)
        supersedes_edges[document.key] = document.supersedes
        for target_key in document.supersedes:
            target = by_key.get(target_key)
            if target_key == document.key:
                issues.append(_issue(document, "supersedes 不得自指"))
                blocked.add(document.key)
            elif target is None or target.kind != document.kind:
                issues.append(_issue(document, f"supersedes 目标 {target_key!r} 缺失或类型错误"))
                blocked.add(document.key)
            elif document.status == "active" and target.status != "retired":
                issues.append(
                    _issue(document, f"active 替代者要求旧职责 {target_key!r} 在当前 Working Tree 为 retired")
                )
                blocked.add(document.key)
    for key in _cycle_members(supersedes_edges):
        document = by_key.get(key)
        if document is None:
            continue
        issues.append(_issue(document, "supersedes 关系形成循环"))
        blocked.add(key)

    changed = True
    while changed:
        changed = False
        for key, document in active_specs.items():
            if key in blocked:
                continue
            blocked_basis = sorted(set(document.basis) & blocked)
            blocked_parent = document.parent_spec if document.parent_spec in blocked else None
            if blocked_basis:
                issues.append(_issue(document, f"规范依据目标存在阻断问题: {', '.join(blocked_basis)}"))
            if blocked_parent is not None:
                issues.append(_issue(document, f"结构归属目标存在阻断问题: {blocked_parent}"))
            if blocked_basis or blocked_parent is not None:
                blocked.add(key)
                changed = True
        parent_map = dict(attachment_parents)
        for key in active_attachments:
            parent_key = parent_map.get(key)
            if parent_key in blocked and key not in blocked:
                issues.append(_issue(active_attachments[key], "附件的授权父规范存在阻断问题"))
                blocked.add(key)
                changed = True

    active_documents_passing_implemented_checks = tuple(
        sorted(
            (
                document
                for document in (*active_specs.values(), *active_attachments.values())
                if document.key not in blocked
            ),
            key=lambda document: document.canonical_path,
        )
    )
    return GraphResult(
        active_documents_passing_implemented_checks=active_documents_passing_implemented_checks,
        issues=tuple(issues),
        incomplete_keys=tuple(sorted(blocked)),
        attachment_parents=tuple(sorted(attachment_parents)),
        basis_reachability_overlaps=tuple(
            sorted(overlaps, key=lambda item: (item.spec_key, item.direct_basis, item.reachable_via))
        ),
        relationship_target_paths=tuple(
            sorted((document.key, document.canonical_path) for document in by_key.values())
        ),
    )
