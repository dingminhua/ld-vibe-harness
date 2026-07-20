"""Second-pass mechanical relation checks over one actual project working tree."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ldvh.facts.contracts import LAYOUTS
from ldvh.facts.models import FactIssue
from ldvh.facts.repository import (
    MAX_FACT_BYTES,
    FactReadResult,
    GitIdentityCache,
    _identity_issue,
    read_fact_object,
)
from ldvh.facts.schema import FactSchema
from ldvh.facts.validation import parse_rfc3339
from ldvh.filesystem import safe_list_directory

MAX_GRAPH_OBJECTS = 10_000


@dataclass(slots=True)
class ProjectFactIndex:
    root: Path
    governed_project_id: str
    schemas: dict[str, FactSchema]
    expected_common_dir: Path | None = None
    aggregate_budget_bytes: int | None = None
    cache: dict[tuple[str, str], FactReadResult] = field(default_factory=dict)
    base_cache: dict[tuple[str, str], FactReadResult] = field(default_factory=dict)
    git_identity_cache: GitIdentityCache = field(default_factory=dict)
    aggregate_bytes_read: int = field(default=0, init=False)
    aggregate_budget_exhausted: bool = field(default=False, init=False)

    def read(self, fact_type_key: str, object_id: str) -> FactReadResult | None:
        layout = LAYOUTS.get(fact_type_key)
        schema = self.schemas.get(fact_type_key)
        if layout is None or schema is None or layout.object_id_pattern.fullmatch(object_id) is None:
            return None
        key = (fact_type_key, object_id)
        if key not in self.cache:
            remaining = None
            if self.aggregate_budget_bytes is not None:
                remaining = self.aggregate_budget_bytes - self.aggregate_bytes_read
                if remaining <= 0:
                    self.aggregate_budget_exhausted = True
                    result = FactReadResult(
                        layout.canonical_path(object_id), layout.carrier, "unavailable", None, None,
                        (FactIssue("budget", "事实对象聚合读取预算已耗尽"),),
                    )
                    self.cache[key] = result
                    self.base_cache[key] = result
                    return result
            result = read_fact_object(
                self.root,
                layout,
                schema,
                object_id,
                expected_common_dir=self.expected_common_dir,
                max_bytes=MAX_FACT_BYTES if remaining is None else min(MAX_FACT_BYTES, remaining),
                git_identity_cache=self.git_identity_cache,
            )
            if result.raw_byte_count is not None:
                self.aggregate_bytes_read += result.raw_byte_count
            if (
                remaining is not None and remaining < MAX_FACT_BYTES
                and result.check_status == "unavailable"
                and any(issue.category == "parse" and "读取预算" in issue.summary for issue in result.issues)
            ):
                self.aggregate_budget_exhausted = True
            self.cache[key] = result
            self.base_cache[key] = result
        return self.cache[key]

    def base_read(self, fact_type_key: str, object_id: str) -> FactReadResult | None:
        self.read(fact_type_key, object_id)
        return self.base_cache.get((fact_type_key, object_id))

    def scan_valid_objects(
        self,
        fact_type_key: str,
        *,
        base: bool = False,
    ) -> tuple[tuple[FactReadResult, ...], bool]:
        layout = LAYOUTS[fact_type_key]
        identity_issue, _ = _identity_issue(self.root, self.expected_common_dir, self.git_identity_cache)
        if identity_issue is not None:
            return (), False
        try:
            paths = safe_list_directory(self.root, layout.directory)
        except FileNotFoundError:
            return (), True
        except OSError:
            return (), False
        if len(paths) > MAX_GRAPH_OBJECTS:
            return (), False
        results: list[FactReadResult] = []
        complete = True
        for path in paths:
            if path.suffix != layout.suffix:
                continue
            object_id = path.name.removesuffix(layout.suffix)
            if layout.object_id_pattern.fullmatch(object_id) is None:
                continue
            result = self.read(fact_type_key, object_id)
            if result is None:
                continue
            if base:
                result = self.base_cache[(fact_type_key, object_id)]
            if result.check_status == "unavailable":
                complete = False
            elif result.check_status == "mechanically_valid":
                results.append(result)
        identity_issue, _ = _identity_issue(self.root, self.expected_common_dir, self.git_identity_cache)
        return tuple(results), complete and identity_issue is None


def _relations(read: FactReadResult) -> tuple[dict[str, object], ...]:
    if read.fields is None or not isinstance(read.fields.get("relations"), list):
        return ()
    return tuple(item for item in read.fields["relations"] if isinstance(item, dict))


def _target(relation: dict[str, object]) -> dict[str, object] | None:
    value = relation.get("target")
    return value if isinstance(value, dict) else None


def _target_condition(source_type: str, relation_key: str, target_type: str, target_status: object) -> bool:
    if relation_key == "supersedes":
        if source_type == "spark":
            return target_type == "spark" and target_status in {"routed", "discarded"}
        if source_type == "workcase":
            return target_type == "workcase" and target_status == "closed"
        return target_type == source_type and target_status == "superseded"
    if source_type == "spark" and relation_key == "routed-to":
        return target_type != "spark"
    if source_type == "workcase" and relation_key == "depends-on":
        return target_type == "workcase" and target_status in {"open", "blocked"}
    if source_type == "workcase" and relation_key == "routed-to":
        if target_type == "workcase":
            return target_status in {"open", "blocked"}
        if target_type == "spark":
            return target_status == "open"
        return False
    return True


def _edge_time_valid(
    source_type: str,
    relation_key: str,
    source_fields: dict[str, object],
    target_fields: dict[str, object],
) -> bool:
    if relation_key != "supersedes" or source_type not in {"adr", "pitfall", "study"}:
        return True
    if source_type == "adr":
        target_start = parse_rfc3339(target_fields.get("decided_at"))
        source_start = parse_rfc3339(source_fields.get("decided_at"))
    else:
        target_start = parse_rfc3339(target_fields.get("created_at"))
        source_start = parse_rfc3339(source_fields.get("created_at"))
    target_closed = parse_rfc3339(target_fields.get("closed_at"))
    return (
        target_start is not None
        and source_start is not None
        and target_closed is not None
        and target_start <= source_start <= target_closed
    )


def _source_condition(source_type: str, relation_key: str, source_fields: dict[str, object]) -> bool:
    if source_type == "workcase" and relation_key == "depends-on":
        return source_fields.get("status") in {"open", "blocked"}
    if source_type == "workcase" and relation_key == "routed-to":
        return source_fields.get("status") == "closed"
    return True


def _edge_identity(relation: dict[str, object]) -> tuple[object, object, object, object]:
    target = _target(relation) or {}
    return (
        relation.get("relation_key"),
        target.get("governed_project_id"),
        target.get("fact_type_key"),
        target.get("object_id"),
    )


def _workcase_residual_mapping_issues(fields: dict[str, object]) -> list[FactIssue]:
    if fields.get("workcase_profile") != "control-contract-v1":
        return []
    issues: list[FactIssue] = []
    residuals = fields.get("residual_responsibilities")
    dispositions = {
        residual.get("residual_id"): residual.get("disposition")
        for residual in (residuals if isinstance(residuals, list) else [])
        if isinstance(residual, dict) and isinstance(residual.get("residual_id"), str)
    }
    mapped: set[str] = set()
    for relation_index, relation in enumerate(_relations_from_fields(fields)):
        relation_key = relation.get("relation_key")
        responsibility_ids = relation.get("responsibility_ids")
        path = f"relations[{relation_index}].responsibility_ids"
        if relation_key != "routed-to":
            if "responsibility_ids" in relation:
                issues.append(FactIssue("relation", "只有 routed-to 可以声明 responsibility_ids", path))
            continue
        if not isinstance(responsibility_ids, list):
            issues.append(FactIssue("relation", "current routed-to 必须显式映射 responsibility_ids", path))
            continue
        string_ids = [value for value in responsibility_ids if isinstance(value, str)]
        if len(string_ids) != len(responsibility_ids) or len(string_ids) != len(set(string_ids)):
            issues.append(FactIssue("relation", "responsibility_ids 必须是唯一 residual_id 闭集", path))
        for residual_id in string_ids:
            disposition = dispositions.get(residual_id)
            if disposition != "routed":
                issues.append(
                    FactIssue(
                        "relation",
                        "responsibility_ids 只能映射已声明为 routed 的 residual",
                        path,
                    )
                )
            else:
                mapped.add(residual_id)
    for residual_id, disposition in dispositions.items():
        if disposition == "routed" and residual_id not in mapped:
            issues.append(
                FactIssue(
                    "relation",
                    "routed residual 必须被至少一条 routed-to 关系显式映射",
                    "relations",
                )
            )
        if disposition == "accepted_stop" and residual_id in mapped:
            issues.append(
                FactIssue(
                    "relation",
                    "accepted_stop residual 不得被 routed-to 关系映射",
                    "relations",
                )
            )
    return issues


def _relations_from_fields(fields: dict[str, object]) -> tuple[dict[str, object], ...]:
    values = fields.get("relations")
    if not isinstance(values, list):
        return ()
    return tuple(value for value in values if isinstance(value, dict))


def _graph_status(
    index: ProjectFactIndex,
    start: tuple[str, str],
    relation_key: str,
    *,
    base: bool = False,
) -> tuple[bool, bool]:
    colors: dict[tuple[str, str], int] = {}
    stack: list[tuple[tuple[str, str], bool]] = [(start, False)]
    observed = 0
    while stack:
        node, exiting = stack.pop()
        if exiting:
            colors[node] = 2
            continue
        color = colors.get(node, 0)
        if color == 1:
            return True, True
        if color == 2:
            continue
        observed += 1
        if observed > MAX_GRAPH_OBJECTS:
            return False, False
        read = index.base_read(*node) if base else index.read(*node)
        if read is None or read.check_status in {"not_found", "invalid"}:
            return False, True
        if read.check_status == "unavailable":
            return False, False
        colors[node] = 1
        stack.append((node, True))
        for relation in reversed(_relations(read)):
            if relation.get("relation_key") != relation_key:
                continue
            target = _target(relation)
            if target is None or target.get("governed_project_id") != index.governed_project_id:
                continue
            target_type = target.get("fact_type_key")
            target_id = target.get("object_id")
            if not isinstance(target_type, str) or not isinstance(target_id, str):
                return False, False
            stack.append(((target_type, target_id), False))
    return False, True


def _incoming_supersedes(
    index: ProjectFactIndex,
    fact_type_key: str,
    object_id: str,
    target_read: FactReadResult,
) -> tuple[set[tuple[str, str]], bool]:
    candidates, complete = index.scan_valid_objects(fact_type_key, base=True)
    sources: set[tuple[str, str]] = set()
    assert target_read.fields is not None
    for candidate in candidates:
        assert candidate.fields is not None
        candidate_id = candidate.fields.get("object_id")
        if not isinstance(candidate_id, str):
            continue
        if not _valid_supersedes_source(index, fact_type_key, candidate_id, candidate):
            continue
        matching = [
            relation
            for relation in _relations(candidate)
            if relation.get("relation_key") == "supersedes"
            and (_target(relation) or {}).get("governed_project_id") == index.governed_project_id
            and (_target(relation) or {}).get("fact_type_key") == fact_type_key
            and (_target(relation) or {}).get("object_id") == object_id
        ]
        if len(matching) != 1:
            continue
        target_condition = _target_condition(
            fact_type_key,
            "supersedes",
            fact_type_key,
            target_read.fields.get("status"),
        )
        edge_time_valid = _edge_time_valid(
            fact_type_key,
            "supersedes",
            candidate.fields,
            target_read.fields,
        )
        if target_condition and edge_time_valid:
            sources.add((fact_type_key, candidate_id))
    return sources, complete


def _valid_supersedes_source(
    index: ProjectFactIndex,
    fact_type_key: str,
    object_id: str,
    candidate: FactReadResult,
) -> bool:
    """Check a persisted replacement edge independently of incoming cardinality.

    Establishment requires an active source and a multi-object mutation. Static
    reads must keep the edge valid after that source later reaches a terminal
    status; controlled single-object create/update paths cannot establish it.
    """

    assert candidate.fields is not None
    seen: set[tuple[object, object, object, object]] = set()
    for relation in _relations(candidate):
        identity = _edge_identity(relation)
        if identity in seen:
            return False
        seen.add(identity)
        if relation.get("relation_key") != "supersedes":
            return False
        target = _target(relation)
        if target is None:
            return False
        target_project = target.get("governed_project_id")
        target_type = target.get("fact_type_key")
        target_id = target.get("object_id")
        if (
            target_project != index.governed_project_id
            or target_type != fact_type_key
            or not isinstance(target_id, str)
            or target_id == object_id
        ):
            return False
        target_read = index.base_read(fact_type_key, target_id)
        if target_read is None or target_read.check_status != "mechanically_valid" or target_read.fields is None:
            return False
        if not _target_condition(fact_type_key, "supersedes", fact_type_key, target_read.fields.get("status")):
            return False
        if not _edge_time_valid(fact_type_key, "supersedes", candidate.fields, target_read.fields):
            return False
    cycle, complete = _graph_status(index, (fact_type_key, object_id), "supersedes", base=True)
    return complete and not cycle


def validate_project_relations(
    index: ProjectFactIndex,
    fact_type_key: str,
    object_id: str,
    read: FactReadResult,
) -> tuple[tuple[FactIssue, ...], bool]:
    """Return relation issues and whether a required project-wide check was unavailable."""

    issues: list[FactIssue] = []
    unavailable = False
    assert read.fields is not None
    if fact_type_key == "workcase":
        issues.extend(_workcase_residual_mapping_issues(read.fields))
    seen_edges: set[tuple[object, object, object, object]] = set()
    workcase_superseded_route = False
    for relation_index, relation in enumerate(_relations(read)):
        relation_key = relation.get("relation_key")
        target = _target(relation)
        path = f"relations[{relation_index}].target"
        identity = _edge_identity(relation)
        if identity in seen_edges:
            issues.append(FactIssue("relation", "同一 relation_key 与目标不得重复", path))
        seen_edges.add(identity)
        if not isinstance(relation_key, str) or target is None:
            continue
        target_project = target.get("governed_project_id")
        target_type = target.get("fact_type_key")
        target_id = target.get("object_id")
        if not isinstance(target_project, str) or not isinstance(target_type, str) or not isinstance(target_id, str):
            continue
        layout = LAYOUTS.get(target_type)
        if layout is None or layout.object_id_pattern.fullmatch(target_id) is None:
            issues.append(FactIssue("relation", "关系目标的类型与 object_id 格式不一致", path))
            continue
        if target_project == index.governed_project_id and target_type == fact_type_key and target_id == object_id:
            issues.append(FactIssue("relation", "事实对象关系禁止自指", path))
            continue
        if not _source_condition(fact_type_key, relation_key, read.fields):
            issues.append(FactIssue("relation", "关系不允许由当前 source 状态声明", path))
        if target_project != index.governed_project_id:
            if relation_key == "supersedes":
                issues.append(FactIssue("relation", "supersedes 只允许同一管辖项目", path))
            elif "governance_refs" not in target:
                issues.append(FactIssue("relation", "跨项目目标必须提供 governance_refs", f"{path}.governance_refs"))
            else:
                unavailable = True
            continue
        target_read = index.read(target_type, target_id)
        if target_read is None or target_read.check_status in {"not_found", "invalid"}:
            issues.append(FactIssue("relation", "关系目标不存在或不是 mechanically valid 当前对象", path))
            continue
        if target_read.check_status == "unavailable":
            unavailable = True
            continue
        assert target_read.fields is not None
        if not _target_condition(fact_type_key, relation_key, target_type, target_read.fields.get("status")):
            issues.append(FactIssue("relation", "关系目标类型或状态不满足当前类型机械条件", path))
        if not _edge_time_valid(fact_type_key, relation_key, read.fields, target_read.fields):
            issues.append(FactIssue("relation", "supersedes 跨对象时间顺序不成立", path))
        if (
            fact_type_key == "workcase"
            and relation_key == "routed-to"
            and target_type == "workcase"
            and target_read.fields.get("status") in {"open", "blocked"}
        ):
            workcase_superseded_route = True

    if (
        fact_type_key == "workcase"
        and read.fields.get("closure_outcome") == "superseded"
        and not workcase_superseded_route
    ):
        issues.append(
            FactIssue(
                "relation",
                "closure_outcome superseded 要求 routed-to 当前 open/blocked WorkCase",
                "relations",
            )
        )

    relation_keys = {str(item.get("relation_key")) for item in _relations(read)} - {"related-to"}
    for relation_key in relation_keys:
        cycle, complete = _graph_status(index, (fact_type_key, object_id), relation_key)
        if not complete:
            unavailable = True
        elif cycle:
            issues.append(FactIssue("relation", f"{relation_key} 关系形成有向循环", "relations"))

    if fact_type_key in {"adr", "pitfall", "study"}:
        incoming, complete = _incoming_supersedes(index, fact_type_key, object_id, read)
        if not complete:
            unavailable = True
        status = read.fields.get("status")
        if status == "superseded" and len(incoming) != 1:
            issues.append(
                FactIssue(
                    "relation",
                    "superseded 对象必须有且只有一个有效直接 supersedes source",
                    "relations",
                )
            )
        elif status != "superseded" and incoming:
            issues.append(FactIssue("relation", "非 superseded 对象不得成为有效 supersedes 目标", "relations"))
    return tuple(issues), unavailable


__all__ = ["ProjectFactIndex", "validate_project_relations"]
