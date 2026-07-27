"""Stabilize project-wide fact checks without request-order dependence."""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable, Mapping
from dataclasses import replace

from ldvh.facts.models import FactIssue
from ldvh.facts.relations import (
    MAX_GRAPH_OBJECTS,
    GraphStatus,
    GraphStatusKey,
    ProjectFactIndex,
    validate_project_relations,
)
from ldvh.facts.repository import FactReadResult

FactKey = tuple[str, str]


def _locally_valid(read: FactReadResult | None) -> bool:
    return read is not None and read.check_status == "mechanically_valid" and read.fields is not None


def _same_project_relation_targets(
    index: ProjectFactIndex,
    read: FactReadResult,
) -> tuple[FactKey, ...]:
    assert read.fields is not None
    relations = read.fields.get("relations")
    targets: list[FactKey] = []
    for relation in relations if isinstance(relations, list) else []:
        if not isinstance(relation, Mapping):
            continue
        target = relation.get("target")
        if not isinstance(target, Mapping):
            continue
        if target.get("governed_project_id") != index.governed_project_id:
            continue
        fact_type_key = target.get("fact_type_key")
        object_id = target.get("object_id")
        if isinstance(fact_type_key, str) and isinstance(object_id, str):
            targets.append((fact_type_key, object_id))
    return tuple(targets)


def _reverse_reachable(
    reverse: Mapping[FactKey, set[FactKey]],
    seeds: set[FactKey],
) -> set[FactKey]:
    reached = set(seeds)
    pending: deque[FactKey] = deque(seeds)
    while pending:
        target_key = pending.popleft()
        for source_key in reverse.get(target_key, ()):
            if source_key not in reached:
                reached.add(source_key)
                pending.append(source_key)
    return reached


def _relation_graph_statuses(
    index: ProjectFactIndex,
    base_reads: Mapping[FactKey, FactReadResult],
    budget_blocked: set[FactKey],
) -> dict[GraphStatusKey, GraphStatus]:
    """Resolve every reachable same-key graph result once for the closure.

    Repeatedly running a fresh DFS from every source makes a linear dependency
    chain quadratic.  Reverse propagation resolves invalid and unavailable
    terminals, while removing all zero-outdegree nodes leaves exactly the nodes
    that can reach a directed cycle.  Each relation-key graph is therefore
    solved in linear time.
    """

    adjacency_by_relation: dict[str, dict[FactKey, set[FactKey]]] = {}
    invalid_by_relation: dict[str, set[FactKey]] = {}
    unavailable_by_relation: dict[str, set[FactKey]] = {}
    for source_key, read in base_reads.items():
        assert read.fields is not None
        relations = read.fields.get("relations")
        for relation in relations if isinstance(relations, list) else []:
            if not isinstance(relation, Mapping):
                continue
            relation_key = relation.get("relation_key")
            if not isinstance(relation_key, str) or relation_key == "related-to":
                continue
            adjacency = adjacency_by_relation.setdefault(relation_key, {})
            adjacency.setdefault(source_key, set())
            invalid = invalid_by_relation.setdefault(relation_key, set())
            unavailable = unavailable_by_relation.setdefault(relation_key, set())
            target = relation.get("target")
            if not isinstance(target, Mapping):
                continue
            if target.get("governed_project_id") != index.governed_project_id:
                continue
            target_type = target.get("fact_type_key")
            target_id = target.get("object_id")
            if not isinstance(target_type, str) or not isinstance(target_id, str):
                invalid.add(source_key)
                continue
            target_key = (target_type, target_id)
            if target_key in base_reads:
                adjacency[source_key].add(target_key)
                adjacency.setdefault(target_key, set())
                continue
            target_read = index.cache.get(target_key)
            if target_read is not None and target_read.check_status == "unavailable":
                unavailable.add(source_key)
            else:
                invalid.add(source_key)

    statuses: dict[GraphStatusKey, GraphStatus] = {}
    for relation_key, adjacency in adjacency_by_relation.items():
        reverse: dict[FactKey, set[FactKey]] = {key: set() for key in adjacency}
        outdegree = {key: len(targets) for key, targets in adjacency.items()}
        for source_key, targets in adjacency.items():
            for target_key in targets:
                reverse[target_key].add(source_key)

        invalid_reaching = _reverse_reachable(
            reverse,
            invalid_by_relation.get(relation_key, set()),
        )
        unavailable_reaching = _reverse_reachable(
            reverse,
            unavailable_by_relation.get(relation_key, set())
            | (budget_blocked & adjacency.keys()),
        )
        removable: deque[FactKey] = deque(
            key for key, degree in outdegree.items() if degree == 0
        )
        while removable:
            target_key = removable.popleft()
            for source_key in reverse[target_key]:
                outdegree[source_key] -= 1
                if outdegree[source_key] == 0:
                    removable.append(source_key)
        for fact_key, degree in outdegree.items():
            status: GraphStatus = "acyclic"
            if degree > 0:
                status = "cycle"
            if fact_key in invalid_reaching:
                status = "invalid"
            if fact_key in unavailable_reaching:
                status = "unavailable"
            statuses[(*fact_key, relation_key)] = status
    return statuses


def _evaluated_read(
    index: ProjectFactIndex,
    key: FactKey,
    base_read: FactReadResult,
    graph_statuses: Mapping[GraphStatusKey, GraphStatus],
) -> FactReadResult:
    relation_issues, relation_unavailable = validate_project_relations(
        index,
        key[0],
        key[1],
        base_read,
        graph_statuses=graph_statuses,
    )
    if relation_unavailable:
        return replace(
            base_read,
            check_status="unavailable",
            issues=(
                *base_read.issues,
                *relation_issues,
                FactIssue("reference", "项目级关系集合未能完成必需机械检查", code="RELATION_CHECK_UNAVAILABLE"),
            ),
        )
    if relation_issues:
        return replace(
            base_read,
            check_status="invalid",
            issues=(*base_read.issues, *relation_issues),
        )
    return base_read


def stabilize_project_index(
    index: ProjectFactIndex,
    seed_keys: Iterable[FactKey],
) -> None:
    """Validate the caller-seeded relation closure and propagate target failures."""

    seeds = tuple(dict.fromkeys(seed_keys))
    base_reads: dict[FactKey, FactReadResult] = {}
    for key in seeds:
        base_read = index.base_cache.get(key, index.cache.get(key))
        if _locally_valid(base_read):
            assert base_read is not None
            base_reads[key] = base_read
    if not base_reads:
        return

    reverse_dependencies: dict[FactKey, set[FactKey]] = {}
    pending: deque[FactKey] = deque(base_reads)
    expanded: set[FactKey] = set()
    observed: set[FactKey] = set(base_reads)
    budget_blocked: set[FactKey] = set()
    if len(observed) > MAX_GRAPH_OBJECTS:
        budget_blocked.update(base_reads)
        pending.clear()

    while pending:
        source_key = pending.popleft()
        if source_key in expanded:
            continue
        expanded.add(source_key)
        source = base_reads[source_key]
        for target_key in _same_project_relation_targets(index, source):
            reverse_dependencies.setdefault(target_key, set()).add(source_key)
            if target_key not in observed:
                if len(observed) >= MAX_GRAPH_OBJECTS:
                    budget_blocked.add(source_key)
                    continue
                observed.add(target_key)
            index.read(*target_key)
            target_base = index.base_cache.get(target_key)
            if target_key not in base_reads and _locally_valid(target_base):
                assert target_base is not None
                base_reads[target_key] = target_base
                pending.append(target_key)

    graph_statuses = _relation_graph_statuses(index, base_reads, budget_blocked)

    changed: deque[FactKey] = deque()
    queued: set[FactKey] = set()

    def enqueue(key: FactKey) -> None:
        if key not in queued:
            changed.append(key)
            queued.add(key)

    budget_issue = FactIssue(
        "reference",
        f"项目级关系闭包超过 {MAX_GRAPH_OBJECTS} 个对象读取预算",
    )
    for key in budget_blocked:
        current = index.cache.get(key)
        if current is not None and current.check_status != "mechanically_valid":
            enqueue(key)
            continue
        base_read = base_reads.get(key)
        if base_read is None:
            continue
        index.cache[key] = replace(
            base_read,
            check_status="unavailable",
            issues=(*base_read.issues, budget_issue),
        )
        enqueue(key)

    for key, base_read in base_reads.items():
        current = index.cache.get(key)
        if current is not None and current.check_status != "mechanically_valid":
            enqueue(key)
            continue
        evaluated = _evaluated_read(index, key, base_read, graph_statuses)
        index.cache[key] = evaluated
        if evaluated.check_status != "mechanically_valid":
            enqueue(key)

    while changed:
        target_key = changed.popleft()
        queued.remove(target_key)
        for source_key in reverse_dependencies.get(target_key, ()):
            current = index.cache.get(source_key)
            if current is not None and current.check_status != "mechanically_valid":
                continue
            base_read = base_reads.get(source_key)
            if base_read is None:
                continue
            evaluated = _evaluated_read(index, source_key, base_read, graph_statuses)
            index.cache[source_key] = evaluated
            if evaluated.check_status != "mechanically_valid":
                enqueue(source_key)


__all__ = ["stabilize_project_index"]
