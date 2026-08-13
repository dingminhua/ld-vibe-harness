"""Second-pass mechanical relation checks over one actual project working tree."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Literal

from ldvh.facts.contracts import ACTIVE_STATUSES, LAYOUTS, is_ignored_fact_type_root_entry, is_legacy_spark_object
from ldvh.facts.identity import canonical_object_uid
from ldvh.facts.models import FactIssue, FactReference, StableFactReference, UIDFactReference
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
_CONTENT_FINGERPRINT_PATTERN = re.compile(r"[0-9a-f]{64}\Z")

WorkCaseTargetIdentity = tuple[str, ...]
GraphStatus = Literal["acyclic", "cycle", "invalid", "unavailable"]
GraphStatusKey = tuple[str, str, str]


@dataclass(frozen=True, slots=True)
class WorkCaseRouteTargetSnapshot:
    """One exact route target read consumed from its operation-specific origin."""

    target: StableFactReference
    content_fingerprint: str
    origin_path: str

    @property
    def identity(self) -> WorkCaseTargetIdentity:
        return _stable_reference_identity(self.target)


@dataclass(slots=True)
class ProjectFactIndex:
    root: Path
    governed_project_id: str
    schemas: dict[str, FactSchema]
    expected_common_dir: Path | None = None
    cache: dict[tuple[str, str], FactReadResult] = field(default_factory=dict)
    base_cache: dict[tuple[str, str], FactReadResult] = field(default_factory=dict)
    git_identity_cache: GitIdentityCache = field(default_factory=dict)
    uid_cache: dict[str, list[tuple[str, str, FactReadResult]]] = field(default_factory=dict)
    uid_scan_complete: bool | None = None
    configuration_uid_resolver: Callable[
        [str], tuple[tuple[str, str, str, FactReadResult] | None, str]
    ] | None = None

    def _invalidate_uid_index(self) -> None:
        self.uid_cache.clear()
        self.uid_scan_complete = None

    def read(self, fact_type_key: str, object_id: str) -> FactReadResult | None:
        layout = LAYOUTS.get(fact_type_key)
        if layout is None or layout.object_id_pattern.fullmatch(object_id) is None:
            return None
        key = (fact_type_key, object_id)
        schema = self.schemas.get(fact_type_key)
        if schema is None:
            result = FactReadResult(
                layout.canonical_path(object_id),
                layout.carrier,
                "unavailable",
                None,
                None,
                (FactIssue("schema", "关系目标类型缺少当前派生 Schema"),),
            )
            self.cache[key] = result
            self.base_cache[key] = result
            return result
        if key not in self.cache:
            if self.uid_scan_complete is not None:
                self._invalidate_uid_index()
            result = read_fact_object(
                self.root,
                layout,
                schema,
                object_id,
                expected_common_dir=self.expected_common_dir,
                max_bytes=MAX_FACT_BYTES,
                git_identity_cache=self.git_identity_cache,
            )
            self.cache[key] = result
            self.base_cache[key] = result
        return self.cache[key]

    def read_fresh(self, fact_type_key: str, object_id: str) -> FactReadResult | None:
        """Discard this index's memoized value and read one target again.

        Callers that use this for a write guard must still construct and use the
        index while holding the transaction's fact-type lock.  This method only
        prevents an earlier read through the same index from being reused.
        """

        key = (fact_type_key, object_id)
        self._invalidate_uid_index()
        self.cache.pop(key, None)
        self.base_cache.pop(key, None)
        return self.read(fact_type_key, object_id)

    def base_read(self, fact_type_key: str, object_id: str) -> FactReadResult | None:
        self.read(fact_type_key, object_id)
        return self.base_cache.get((fact_type_key, object_id))

    def _scan_uid_index(self) -> None:
        if self.uid_scan_complete is not None:
            return
        complete = True
        observed = 0
        indexed_keys: set[tuple[str, str]] = set()
        for key, read in self.cache.items():
            if read.fields is None:
                continue
            object_uid = canonical_object_uid(read.fields.get("object_uid"))
            if object_uid is None:
                continue
            self.uid_cache.setdefault(object_uid, []).append((*key, read))
            indexed_keys.add(key)
        for fact_type_key, layout in LAYOUTS.items():
            try:
                paths = safe_list_directory(self.root, layout.directory)
            except FileNotFoundError:
                continue
            except OSError:
                complete = False
                continue
            try:
                paths = tuple(path for path in paths if not is_ignored_fact_type_root_entry(path))
            except OSError:
                complete = False
                continue
            for path in paths:
                if path.suffix != layout.suffix:
                    continue
                object_id = path.name.removesuffix(layout.suffix)
                if layout.object_id_pattern.fullmatch(object_id) is None:
                    continue
                observed += 1
                if observed > MAX_GRAPH_OBJECTS:
                    complete = False
                    break
                read = self.read(fact_type_key, object_id)
                if read is None or read.check_status == "unavailable":
                    complete = False
                    continue
                if read.fields is None:
                    continue
                object_uid = canonical_object_uid(read.fields.get("object_uid"))
                if object_uid is not None and (fact_type_key, object_id) not in indexed_keys:
                    self.uid_cache.setdefault(object_uid, []).append((fact_type_key, object_id, read))
                    indexed_keys.add((fact_type_key, object_id))
            if observed > MAX_GRAPH_OBJECTS:
                break
        self.uid_scan_complete = complete

    def resolve_uid(self, object_uid: str) -> tuple[FactReadResult | None, str]:
        """Resolve one UID in the current project without guessing through collisions."""

        if canonical_object_uid(object_uid) is None:
            return None, "invalid"
        self._scan_uid_index()
        matches = self.uid_cache.get(object_uid, [])
        if not self.uid_scan_complete:
            return None, "unavailable"
        if len(matches) > 1:
            return None, "duplicate"
        if not matches:
            return None, "not_found"
        return matches[0][2], "resolved"

    def resolve_uid_entry(self, object_uid: str) -> tuple[tuple[str, str, FactReadResult] | None, str]:
        if canonical_object_uid(object_uid) is None:
            return None, "invalid"
        self._scan_uid_index()
        matches = self.uid_cache.get(object_uid, [])
        if not self.uid_scan_complete:
            return None, "unavailable"
        if len(matches) > 1:
            return None, "duplicate"
        if not matches:
            return None, "not_found"
        return matches[0], "resolved"

    def scan_valid_objects(
        self,
        fact_type_key: str,
        *,
        base: bool = False,
        require_all_canonical_valid: bool = False,
    ) -> tuple[tuple[FactReadResult, ...], bool]:
        layout = LAYOUTS[fact_type_key]
        identity_issue, _ = _identity_issue(self.root, self.expected_common_dir, self.git_identity_cache)
        if identity_issue is not None:
            return (), False
        try:
            paths = safe_list_directory(self.root, layout.directory)
        except FileNotFoundError:
            # A missing type directory does not prove that no peer of this
            # type exists.  In particular, callers using this scan for a
            # negative relation proof must treat the project set as partial.
            return (), False
        except OSError:
            return (), False
        try:
            paths = tuple(path for path in paths if not is_ignored_fact_type_root_entry(path))
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
            elif require_all_canonical_valid:
                # A closure guard cannot prove that no incoming dependency
                # exists when a canonical peer is invalid or disappears while
                # the project set is being scanned.  Do not consume its
                # untrusted relation fields, but mark the closure incomplete.
                complete = False

        if require_all_canonical_valid and results:
            # A locally valid peer can still be invalid or unavailable after
            # target, status, and graph checks.  Stabilize the complete seed
            # set in one pass so a negative incoming-edge proof never consumes
            # a peer that read-fact-objects would reject at the project level.
            # The local import avoids the relations/project_validation module
            # cycle while preserving the shared project validator as the only
            # authority for this second pass.
            from ldvh.facts.project_validation import stabilize_project_index

            keys = tuple(
                (fact_type_key, str(result.fields["object_id"]))
                for result in results
                if result.fields is not None
            )
            stabilize_project_index(self, keys)
            stable_results: list[FactReadResult] = []
            for key in keys:
                stable = self.cache.get(key)
                if stable is None or stable.check_status != "mechanically_valid" or stable.fields is None:
                    complete = False
                    continue
                stable_results.append(stable)
            results = stable_results
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
        return False
    if source_type == "spark" and relation_key == "related-to":
        return target_type in LAYOUTS
    if source_type == "workcase" and relation_key == "depends-on":
        return target_type == "workcase" and target_status in ACTIVE_STATUSES
    if source_type == "workcase" and relation_key == "routed-to":
        # Formation is intentionally stricter and is checked by
        # validate_workcase_route_target_snapshots.  Once formed, the stable
        # relation remains valid when its WorkCase target later closes.
        return (
            target_type == "workcase" and target_status in {"open", "blocked", "closed"}
        ) or (
            target_type == "spark" and target_status in {"open", "routed", "implemented", "discarded"}
        )
    if source_type == "workcase" and relation_key == "contributed-to":
        # The mechanically-valid-at-formation requirement is carried by the
        # shared target read above; later Pitfall state changes do not affect
        # the edge.  Formation-at-draft is checked by the WorkCase write path.
        return target_type == "pitfall" and target_status in {"draft", "active", "discarded"}
    if source_type == "workcase" and relation_key == "related-to":
        return target_type in LAYOUTS
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
    """Require a title for retained historical Spark route presentation."""

    if source_type != "spark" or relation_key != "routed-to":
        return True
    title = target_fields.get("title")
    return isinstance(title, str) and bool(title.strip())


def _source_condition(source_type: str, relation_key: str, source_fields: dict[str, object]) -> bool:
    if source_type == "workcase" and relation_key == "depends-on":
        return (
            source_fields.get("status") in ACTIVE_STATUSES
            and source_fields.get("phase") != "human_closure_confirming"
        )
    if source_type == "workcase" and relation_key == "routed-to":
        return source_fields.get("status") == "closed"
    if source_type == "workcase" and relation_key == "contributed-to":
        # The edge must be able to exist legally in human_closure_confirming;
        # formation timing is enforced by the update-path transition checks.
        return source_fields.get("status") in {"open", "blocked", "closed"}
    if source_type == "workcase" and relation_key == "related-to":
        return source_fields.get("status") in {"open", "blocked", "closed"}
    return True


def _edge_identity(relation: dict[str, object]) -> tuple[object, object, object, object]:
    target = _target(relation) or {}
    if "object_uid" in target:
        return (relation.get("relation_key"), "uid", target.get("object_uid"), None)
    return (
        relation.get("relation_key"),
        target.get("governed_project_id"),
        target.get("fact_type_key"),
        target.get("object_id"),
    )


def _reference(value: object) -> FactReference | None:
    if not isinstance(value, Mapping):
        return None
    project_id = value.get("governed_project_id")
    fact_type_key = value.get("fact_type_key")
    object_id = value.get("object_id")
    if not all(isinstance(item, str) and item for item in (project_id, fact_type_key, object_id)):
        return None
    return FactReference(project_id, fact_type_key, object_id)


def _stable_reference(value: object, *, allow_fingerprint: bool = False) -> StableFactReference | None:
    if not isinstance(value, Mapping):
        return None
    ignored = {"content_fingerprint"} if allow_fingerprint else set()
    keys = set(value) - ignored
    if keys == {"object_uid"}:
        object_uid = canonical_object_uid(value.get("object_uid"))
        return UIDFactReference(object_uid) if object_uid is not None else None
    if keys != {"governed_project_id", "fact_type_key", "object_id"}:
        return None
    return _reference(value)


def _stable_reference_identity(reference: StableFactReference) -> WorkCaseTargetIdentity:
    if isinstance(reference, UIDFactReference):
        return ("uid", reference.object_uid)
    return (
        "legacy",
        reference.governed_project_id,
        reference.fact_type_key,
        reference.object_id,
    )


def _resolved_target(
    index: ProjectFactIndex,
    value: Mapping[str, object],
) -> tuple[str | None, str | None, FactReadResult | None, str]:
    object_uid = value.get("object_uid")
    if isinstance(object_uid, str):
        configuration_resolver = getattr(index, "configuration_uid_resolver", None)
        if configuration_resolver is not None:
            entry, status = configuration_resolver(object_uid)
            if status != "resolved" or entry is None:
                return None, None, None, status
            target_project_id, fact_type_key, object_id, read = entry
            resolution = "resolved" if target_project_id == index.governed_project_id else "cross_project_resolved"
            return fact_type_key, object_id, read, resolution
        resolver = getattr(index, "resolve_uid", None)
        if resolver is None:
            return None, None, None, "unavailable"
        read, status = resolver(object_uid)
        if status != "resolved" or read is None or read.fields is None:
            return None, None, read, status
        fact_type_key = read.fields.get("fact_type_key")
        object_id = read.fields.get("object_id")
        if not isinstance(fact_type_key, str) or not isinstance(object_id, str):
            return None, None, read, "invalid"
        return fact_type_key, object_id, read, "resolved"
    reference = _reference(value)
    if reference is None:
        return None, None, None, "invalid"
    if reference.governed_project_id != index.governed_project_id:
        return reference.fact_type_key, reference.object_id, None, "cross_project"
    read = index.read(reference.fact_type_key, reference.object_id)
    return reference.fact_type_key, reference.object_id, read, "resolved"


def _snapshot(
    value: object,
    *,
    target_is_nested: bool,
    path: str,
    issues: list[FactIssue],
) -> WorkCaseRouteTargetSnapshot | None:
    if isinstance(value, WorkCaseRouteTargetSnapshot):
        snapshot = value
    elif isinstance(value, Mapping):
        target = _stable_reference(
            value.get("target") if target_is_nested else value,
            allow_fingerprint=not target_is_nested,
        )
        fingerprint = value.get("content_fingerprint")
        if target is None:
            issues.append(FactIssue("relation", "route target 必须是 object_uid 或完整 legacy 三元组", path))
            return None
        if not isinstance(fingerprint, str) or _CONTENT_FINGERPRINT_PATTERN.fullmatch(fingerprint) is None:
            issues.append(
                FactIssue(
                    "reference",
                    "route target content_fingerprint 必须是 64 位小写十六进制 string",
                    f"{path}.content_fingerprint",
                )
            )
            return None
        origin_path = f"{path}.target" if target_is_nested else path
        snapshot = WorkCaseRouteTargetSnapshot(target, fingerprint, origin_path)
    else:
        issues.append(FactIssue("relation", "route target snapshot 必须是 object", path))
        return None
    if _CONTENT_FINGERPRINT_PATTERN.fullmatch(snapshot.content_fingerprint) is None:
        issues.append(
            FactIssue(
                "reference",
                "route target content_fingerprint 必须是 64 位小写十六进制 string",
                f"{path}.content_fingerprint",
            )
        )
        return None
    return snapshot


def proposal_route_target_snapshots(
    fields: Mapping[str, object],
) -> tuple[tuple[WorkCaseRouteTargetSnapshot, ...], tuple[FactIssue, ...]]:
    """Project and deduplicate route target snapshots from one closure proposal.

    Multiple residual decisions may intentionally route to the same target.  In
    that case the target is returned once, but all occurrences must bind the
    same content fingerprint.
    """

    proposal = fields.get("closure_proposal")
    decisions = proposal.get("residual_decisions") if isinstance(proposal, Mapping) else None
    if decisions is None:
        return (), ()
    if not isinstance(decisions, Sequence) or isinstance(decisions, (str, bytes, bytearray)):
        return (), (
            FactIssue(
                "relation",
                "closure proposal residual_decisions 必须是 array",
                "closure_proposal.residual_decisions",
            ),
        )
    issues: list[FactIssue] = []
    snapshots: dict[WorkCaseTargetIdentity, WorkCaseRouteTargetSnapshot] = {}
    for index, decision in enumerate(decisions):
        if not isinstance(decision, Mapping) or decision.get("proposed_disposition") != "route_existing":
            continue
        path = f"closure_proposal.residual_decisions[{index}].route_target"
        snapshot = _snapshot(decision.get("route_target"), target_is_nested=False, path=path, issues=issues)
        if snapshot is None:
            continue
        previous = snapshots.get(snapshot.identity)
        if previous is not None and previous.content_fingerprint != snapshot.content_fingerprint:
            issues.append(FactIssue("reference", "同一 proposal route target 的 fingerprint 必须一致", path))
            continue
        snapshots.setdefault(snapshot.identity, snapshot)
    return tuple(snapshots.values()), tuple(issues)


def request_route_target_snapshots(
    values: object,
) -> tuple[tuple[WorkCaseRouteTargetSnapshot, ...], tuple[FactIssue, ...]]:
    """Parse the exact, target-unique fingerprint array for closed correction."""

    if not isinstance(values, Sequence) or isinstance(values, (str, bytes, bytearray)):
        return (), (FactIssue("relation", "route_target_fingerprints 必须是 array", "route_target_fingerprints"),)
    issues: list[FactIssue] = []
    snapshots: list[WorkCaseRouteTargetSnapshot] = []
    seen: set[WorkCaseTargetIdentity] = set()
    for index, value in enumerate(values):
        path = f"route_target_fingerprints[{index}]"
        snapshot = _snapshot(value, target_is_nested=True, path=path, issues=issues)
        if snapshot is None:
            continue
        if snapshot.identity in seen:
            issues.append(FactIssue("relation", "route_target_fingerprints 必须按目标去重", path))
            continue
        seen.add(snapshot.identity)
        snapshots.append(snapshot)
    return tuple(snapshots), tuple(issues)


def workcase_routed_target_identities(fields: Mapping[str, object]) -> tuple[WorkCaseTargetIdentity, ...]:
    """Return validly-shaped routed-to targets without inventing missing members."""

    identities: list[WorkCaseTargetIdentity] = []
    relations = fields.get("relations")
    for relation in relations if isinstance(relations, list) else []:
        if not isinstance(relation, Mapping) or relation.get("relation_key") != "routed-to":
            continue
        target = _stable_reference(relation.get("target"))
        if target is not None:
            identities.append(_stable_reference_identity(target))
    return tuple(identities)


def validate_workcase_route_target_alignment(
    after_fields: Mapping[str, object],
    *,
    proposal_snapshots: Sequence[WorkCaseRouteTargetSnapshot] | None = None,
    request_snapshots: Sequence[WorkCaseRouteTargetSnapshot] | None = None,
) -> tuple[FactIssue, ...]:
    """Require every supplied route-target authority to name exactly after relations."""

    issues: list[FactIssue] = []
    after_targets = workcase_routed_target_identities(after_fields)
    after_set = set(after_targets)
    if len(after_targets) != len(after_set):
        issues.append(FactIssue("relation", "after 的 routed-to targets 必须按目标去重", "relations"))
    for label, snapshots in (
        ("closure proposal", proposal_snapshots),
        ("route_target_fingerprints", request_snapshots),
    ):
        if snapshots is None:
            continue
        snapshot_targets = [snapshot.identity for snapshot in snapshots]
        if len(snapshot_targets) != len(set(snapshot_targets)):
            issues.append(FactIssue("relation", f"{label} targets 必须按目标去重"))
        if set(snapshot_targets) != after_set:
            issues.append(FactIssue("relation", f"{label} targets 必须与 after 全部 routed-to targets 精确一致"))
    return tuple(issues)


def resolve_workcase_route_target_snapshot(
    index: ProjectFactIndex,
    snapshot: WorkCaseRouteTargetSnapshot,
    *,
    fresh: bool,
) -> tuple[str | None, str | None, FactReadResult | None, str]:
    """Resolve one WorkCase-local route target while preserving its authority shape."""

    target = snapshot.target
    if isinstance(target, FactReference):
        if target.governed_project_id != index.governed_project_id:
            return target.fact_type_key, target.object_id, None, "cross_project"
        read = index.read_fresh(target.fact_type_key, target.object_id) if fresh else index.read(
            target.fact_type_key, target.object_id
        )
        return target.fact_type_key, target.object_id, read, "resolved"
    entry, status = index.resolve_uid_entry(target.object_uid)
    if status != "resolved" or entry is None:
        return None, None, None, status
    fact_type_key, object_id, read = entry
    if fresh:
        read = index.read_fresh(fact_type_key, object_id)
    return fact_type_key, object_id, read, "resolved"


def validate_workcase_route_target_snapshots(
    index: ProjectFactIndex,
    source_object_id: str,
    snapshots: Sequence[WorkCaseRouteTargetSnapshot],
    *,
    existing_routed_targets: frozenset[WorkCaseTargetIdentity] = frozenset(),
) -> tuple[tuple[FactIssue, ...], bool]:
    """Fresh-read route targets and enforce formation/correction state rules.

    An unchanged target already present on a closed source may itself now be
    closed.  Every newly formed target must still be an active WorkCase.
    """

    issues: list[FactIssue] = []
    unavailable = False
    seen: set[WorkCaseTargetIdentity] = set()
    for snapshot in snapshots:
        path = snapshot.origin_path
        identity = snapshot.identity
        if identity in seen:
            issues.append(FactIssue("relation", "route target snapshot 必须按目标去重", path))
            continue
        seen.add(identity)
        target_type, target_id, target_read, resolution = resolve_workcase_route_target_snapshot(
            index, snapshot, fresh=True
        )
        if resolution == "cross_project":
            issues.append(FactIssue("relation", "WorkCase route target 只允许同一管辖项目", path))
            continue
        if resolution == "unavailable":
            unavailable = True
            continue
        if resolution in {"duplicate", "invalid", "not_found"}:
            issues.append(FactIssue("relation", "WorkCase route target 不存在或身份不唯一", path))
            continue
        if target_type not in {"workcase", "spark"} or not isinstance(target_id, str):
            issues.append(FactIssue("relation", "WorkCase routed-to 只能指向 WorkCase 或 Spark", path))
            continue
        layout = LAYOUTS[target_type]
        if layout.object_id_pattern.fullmatch(target_id) is None:
            issues.append(FactIssue("relation", "WorkCase route target object_id 与目标类型不匹配", path))
            continue
        if target_type == "workcase" and target_id == source_object_id:
            issues.append(FactIssue("relation", "WorkCase route target 禁止自指", path))
            continue
        if target_read is None or target_read.check_status in {"not_found", "invalid"}:
            issues.append(FactIssue("relation", "WorkCase route target 不存在或不是 mechanically valid 当前对象", path))
            continue
        if target_read.check_status == "unavailable" or target_read.fields is None:
            unavailable = True
            issues.append(
                FactIssue(
                    "reference",
                    "WorkCase route target 当前不可用，无法完成 fingerprint、状态与项目关系检查",
                    path,
                )
            )
            continue
        if target_read.content_fingerprint != snapshot.content_fingerprint:
            issues.append(FactIssue("reference", "WorkCase route target content_fingerprint 已变化", path))
            continue
        target_status = target_read.fields.get("status")
        if target_type == "workcase":
            allowed_statuses = (
                {"open", "blocked", "closed"}
                if identity in existing_routed_targets
                else {"open", "blocked"}
            )
        else:
            allowed_statuses = (
                {"open", "routed", "implemented", "discarded"}
                if identity in existing_routed_targets
                else {"open"}
            )
        if target_status not in allowed_statuses:
            summary = (
                "未改变的既有 routed-to target 必须保持目标类型的合法后续状态"
                if identity in existing_routed_targets
                else "新形成的 routed-to target 必须为 open/blocked WorkCase 或 open Spark"
            )
            issues.append(FactIssue("relation", summary, path))
    return tuple(issues), unavailable


def validate_workcase_incoming_dependencies(
    index: ProjectFactIndex,
    object_id: str,
) -> tuple[tuple[FactIssue, ...], bool]:
    """Reject closure while any current WorkCase depends on the source."""

    reads, complete = index.scan_valid_objects("workcase", require_all_canonical_valid=True)
    issues: list[FactIssue] = []
    target_identity = (index.governed_project_id, "workcase", object_id)
    for source_read in reads:
        source_fields = source_read.fields
        if source_fields is None or source_fields.get("object_id") == object_id:
            continue
        for relation in _relations(source_read):
            if relation.get("relation_key") != "depends-on":
                continue
            target = _reference(relation.get("target"))
            if target is None:
                continue
            identity = (target.governed_project_id, target.fact_type_key, target.object_id)
            if identity == target_identity:
                source_id = source_fields.get("object_id")
                issues.append(
                    FactIssue(
                        "relation",
                        f"WorkCase 仍有来自 {source_id} 的入向 depends-on，不能关闭",
                        "relations",
                    )
                )
    if not complete:
        issues.append(
            FactIssue(
                "reference",
                "未能完整检查项目范围内全部入向 depends-on",
                "relations",
            )
        )
    return tuple(issues), not complete


def _graph_status(
    index: ProjectFactIndex,
    start: tuple[str, str],
    relation_key: str,
    *,
    base: bool = False,
) -> GraphStatus:
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
            return "cycle"
        if color == 2:
            continue
        observed += 1
        if observed > MAX_GRAPH_OBJECTS:
            return "unavailable"
        read = index.base_read(*node) if base else index.read(*node)
        if read is None or read.check_status in {"not_found", "invalid"}:
            return "invalid"
        if read.check_status == "unavailable":
            return "unavailable"
        colors[node] = 1
        stack.append((node, True))
        for relation in reversed(_relations(read)):
            if relation.get("relation_key") != relation_key:
                continue
            target = _target(relation)
            if target is None:
                continue
            target_type, target_id, _, resolution = _resolved_target(index, target)
            if resolution in {"cross_project", "cross_project_resolved"}:
                continue
            if resolution == "unavailable":
                return "unavailable"
            if resolution != "resolved" or not isinstance(target_type, str) or not isinstance(target_id, str):
                return "invalid"
            stack.append(((target_type, target_id), False))
    return "acyclic"


def validate_project_relations(
    index: ProjectFactIndex,
    fact_type_key: str,
    object_id: str,
    read: FactReadResult,
    *,
    graph_statuses: Mapping[GraphStatusKey, GraphStatus] | None = None,
) -> tuple[tuple[FactIssue, ...], bool]:
    """Return relation issues and whether a required project-wide check was unavailable."""

    issues: list[FactIssue] = []
    unavailable = False
    assert read.fields is not None
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
        target_type, target_id, target_read, resolution = _resolved_target(index, target)
        if resolution == "duplicate":
            issues.append(FactIssue("identity", "关系目标 object_uid 在当前项目重复", path))
            continue
        if resolution == "not_found":
            issues.append(
                FactIssue(
                    "relation",
                    "关系目标不存在或不是 mechanically valid 当前对象",
                    code="TARGET_NOT_EXIST",
                    field_path=path,
                )
            )
            continue
        if resolution == "unavailable":
            unavailable = True
            continue
        if resolution == "invalid" or not isinstance(target_type, str) or not isinstance(target_id, str):
            issues.append(FactIssue("relation", "关系目标身份形状无效", path))
            continue
        layout = LAYOUTS.get(target_type)
        if layout is None or layout.object_id_pattern.fullmatch(target_id) is None:
            issues.append(FactIssue("relation", "关系目标的类型与 object_id 格式不一致", path))
            continue
        source_uid = read.fields.get("object_uid")
        target_uid = target.get("object_uid")
        if (
            isinstance(target_uid, str)
            and isinstance(source_uid, str)
            and target_uid == source_uid
        ) or (
            resolution not in {"cross_project", "cross_project_resolved"}
            and target_type == fact_type_key
            and target_id == object_id
        ):
            issues.append(FactIssue("relation", "事实对象关系禁止自指", path))
            continue
        if not _source_condition(fact_type_key, relation_key, read.fields):
            issues.append(FactIssue("relation", "关系不允许由当前 source 状态声明", path))
        if resolution in {"cross_project", "cross_project_resolved"}:
            if fact_type_key in {"spark", "workcase"}:
                source_label = "Spark" if fact_type_key == "spark" else "WorkCase"
                issues.append(FactIssue("relation", f"{source_label} 关系目标只允许同一管辖项目", path))
                continue
            if resolution == "cross_project":
                unavailable = True
                continue
        if target_read is None or target_read.check_status in {"not_found", "invalid"}:
            issues.append(
                FactIssue(
                    "relation",
                    "关系目标不存在或不是 mechanically valid 当前对象",
                    code="TARGET_NOT_EXIST",
                    field_path=path,
                )
            )
            continue
        if target_read.check_status == "unavailable":
            unavailable = True
            continue
        assert target_read.fields is not None
        if not _target_condition(fact_type_key, relation_key, target_type, target_read.fields.get("status")):
            issues.append(
                FactIssue(
                    "relation",
                    "关系目标类型或状态不满足当前类型机械条件",
                    code="TARGET_NOT_VALID",
                    field_path=path,
                )
            )
        if not _target_has_readable_title(fact_type_key, relation_key, target_read.fields):
            issues.append(FactIssue("relation", "Spark routed-to 目标必须具有可呈现的非空 title", path))

    keys_by_target: dict[tuple[object, object, object], set[object]] = {}
    for relation in _relations(read):
        target = _target(relation) or {}
        identity = (
            "uid",
            target.get("object_uid"),
            None,
        ) if "object_uid" in target else (
            target.get("governed_project_id"),
            target.get("fact_type_key"),
            target.get("object_id"),
        )
        keys_by_target.setdefault(identity, set()).add(relation.get("relation_key"))
    if any("related-to" in keys and len(keys) > 1 for keys in keys_by_target.values()):
        issues.append(FactIssue("relation", "related-to 不得与同一 target 的强关系重叠", "relations"))

    if (
        fact_type_key == "spark"
        and is_legacy_spark_object(read.fields.get("object_id"))
        and read.fields.get("status") == "routed"
    ):
        if not any(item.get("relation_key") == "routed-to" for item in _relations(read)):
            issues.append(FactIssue("relation", "routed Spark 至少需要一条 routed-to 关系", "relations"))

    relation_keys = {str(item.get("relation_key")) for item in _relations(read)} - {"related-to"}
    for relation_key in relation_keys:
        graph_status = (
            _graph_status(index, (fact_type_key, object_id), relation_key)
            if graph_statuses is None
            else graph_statuses.get((fact_type_key, object_id, relation_key), "acyclic")
        )
        if graph_status == "unavailable":
            unavailable = True
        elif graph_status == "invalid":
            issues.append(
                FactIssue(
                    "relation",
                    f"{relation_key} 关系图包含缺失或 mechanically invalid 对象",
                    "relations",
                )
            )
        elif graph_status == "cycle":
            issues.append(FactIssue("relation", f"{relation_key} 关系形成有向循环", "relations"))

    return tuple(issues), unavailable


__all__ = [
    "ProjectFactIndex",
    "WorkCaseRouteTargetSnapshot",
    "WorkCaseTargetIdentity",
    "proposal_route_target_snapshots",
    "request_route_target_snapshots",
    "resolve_workcase_route_target_snapshot",
    "validate_project_relations",
    "validate_workcase_incoming_dependencies",
    "validate_workcase_route_target_alignment",
    "validate_workcase_route_target_snapshots",
    "workcase_routed_target_identities",
]
