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
    if source_type == "spark" and relation_key == "routed-to":
        return target_type not in {"spark", "study"}
    if source_type == "workcase" and relation_key == "depends-on":
        return target_type == "workcase" and target_status in {"open", "blocked"}
    if source_type == "workcase" and relation_key == "routed-to":
        if target_type == "workcase":
            return target_status in {"open", "blocked"}
        if target_type == "spark":
            return target_status == "open"
        return False
    if source_type == "study" and relation_key == "inspired-by":
        return target_type in {"spark", "workcase", "adr"}
    if source_type == "study" and relation_key == "informs":
        return target_type in {"workcase", "adr", "spark"}
    return True


def _target_has_readable_title(
    source_type: str,
    relation_key: str,
    target_fields: dict[str, object],
) -> bool:
    """Require the current title needed by Spark routed-to Human presentation."""

    if source_type != "spark" or relation_key != "routed-to":
        return True
    title = target_fields.get("title")
    return isinstance(title, str) and bool(title.strip())


def _edge_time_valid(
    source_type: str,
    relation_key: str,
    source_fields: dict[str, object],
    target_fields: dict[str, object],
) -> bool:
    return True


def _source_condition(source_type: str, relation_key: str, source_fields: dict[str, object]) -> bool:
    if source_type == "spark" and relation_key == "routed-to":
        return source_fields.get("status") == "routed"
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
    """Residual disposition is expressed in its own readable summary, not relation members."""
    return []


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
            if fact_type_key == "spark":
                issues.append(FactIssue("relation", "Spark 关系目标只允许同一管辖项目", path))
                continue
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
        if not _target_has_readable_title(fact_type_key, relation_key, target_read.fields):
            issues.append(FactIssue("relation", "Spark routed-to 目标必须具有可呈现的非空 title", path))

    if fact_type_key == "spark" and read.fields.get("status") == "routed":
        if not any(item.get("relation_key") == "routed-to" for item in _relations(read)):
            issues.append(FactIssue("relation", "routed Spark 至少需要一条 routed-to 关系", "relations"))

    relation_keys = {str(item.get("relation_key")) for item in _relations(read)} - {"related-to"}
    for relation_key in relation_keys:
        cycle, complete = _graph_status(index, (fact_type_key, object_id), relation_key)
        if not complete:
            unavailable = True
        elif cycle:
            issues.append(FactIssue("relation", f"{relation_key} 关系形成有向循环", "relations"))

    return tuple(issues), unavailable


__all__ = ["ProjectFactIndex", "validate_project_relations"]
