from __future__ import annotations

from pathlib import Path

import pytest

from ldvh.facts import relations as relations_module
from ldvh.facts.models import FactIssue, FactReference
from ldvh.facts.relations import (
    ProjectFactIndex,
    WorkCaseRouteTargetSnapshot,
    _source_condition,
    _target_condition,
    _target_has_readable_title,
    proposal_route_target_snapshots,
    request_route_target_snapshots,
    validate_project_relations,
    validate_workcase_incoming_dependencies,
    validate_workcase_route_target_alignment,
    validate_workcase_route_target_snapshots,
    workcase_routed_target_identities,
)
from ldvh.facts.repository import FactReadResult
from ldvh.facts.schema import FactSchema

_PROJECT = "current-project"
_FINGERPRINT_A = "a" * 64
_FINGERPRINT_B = "b" * 64


class _CurrentProjectIndex:
    governed_project_id = _PROJECT


def test_spark_routed_to_rejects_study_but_accepts_other_stable_fact_types_across_target_lifecycle_states() -> None:
    assert not _target_condition("spark", "routed-to", "study", "active")
    assert not _target_condition("spark", "routed-to", "spark", "open")
    assert not _target_condition("spark", "routed-to", "file-asset", "active")
    assert _target_condition("spark", "routed-to", "workcase", "open")
    assert _target_condition("spark", "routed-to", "workcase", "closed")


def test_file_asset_is_excluded_from_spark_and_workcase_generic_relations() -> None:
    assert not _target_condition("spark", "related-to", "file-asset", "active")
    assert not _target_condition("workcase", "related-to", "file-asset", "active")
    assert _target_condition("workcase", "has-file-asset", "file-asset", "active")
    assert _target_condition("workcase", "has-file-asset", "file-asset", "archived")
    assert not _target_condition("workcase", "has-file-asset", "file-asset", "retired")


def test_spark_routed_to_requires_a_nonempty_current_target_title() -> None:
    assert _target_has_readable_title("spark", "routed-to", {"title": "Helper 事实对象机械结构校验闭环"})
    assert not _target_has_readable_title("spark", "routed-to", {"title": "  "})
    assert _target_has_readable_title("spark", "related-to", {})


def test_spark_routed_to_source_matches_its_status_semantics() -> None:
    assert _source_condition("spark", "routed-to", {"status": "routed"})
    assert not _source_condition("spark", "routed-to", {"status": "discarded"})


def test_spark_relations_are_limited_to_the_current_project_until_cross_project_is_designed() -> None:
    read = FactReadResult(
        Path("ldvh-base/sparks/spark-0001.yaml"),
        "yaml",
        "mechanically_valid",
        {
            "status": "open",
            "relations": [
                {
                    "relation_key": "related-to",
                    "target": {
                        "governed_project_id": "other-project",
                        "fact_type_key": "workcase",
                        "object_id": "workcase-0001",
                    },
                }
            ],
        },
        None,
        (),
    )

    issues, unavailable = validate_project_relations(
        _CurrentProjectIndex(),
        "spark",
        "spark-0001",
        read,  # type: ignore[arg-type]
    )

    assert not unavailable
    assert any(issue.summary == "Spark 关系目标只允许同一管辖项目" for issue in issues)


def test_routed_spark_requires_at_least_one_routed_to_relation() -> None:
    read = FactReadResult(
        Path("ldvh-base/sparks/spark-0001.yaml"),
        "yaml",
        "mechanically_valid",
        {"status": "routed", "relations": []},
        None,
        (),
    )

    issues, unavailable = validate_project_relations(
        _CurrentProjectIndex(),
        "spark",
        "spark-0001",
        read,  # type: ignore[arg-type]
    )

    assert not unavailable
    assert any(issue.summary == "routed Spark 至少需要一条 routed-to 关系" for issue in issues)


def test_spark_related_to_can_target_an_implemented_spark() -> None:
    assert _target_condition("spark", "related-to", "spark", "implemented")


def _target(
    object_id: str,
    *,
    project_id: str = _PROJECT,
    fact_type_key: str = "workcase",
) -> dict[str, str]:
    return {
        "governed_project_id": project_id,
        "fact_type_key": fact_type_key,
        "object_id": object_id,
    }


def _relation(
    relation_key: str,
    object_id: str,
    *,
    project_id: str = _PROJECT,
    fact_type_key: str = "workcase",
) -> dict[str, object]:
    return {
        "relation_key": relation_key,
        "target": _target(object_id, project_id=project_id, fact_type_key=fact_type_key),
    }


def _read(
    object_id: str,
    status: str,
    *,
    phase: str | None = None,
    relations: list[dict[str, object]] | None = None,
    check_status: str = "mechanically_valid",
    fingerprint: str = _FINGERPRINT_A,
    fact_type_key: str = "workcase",
    title: str = "关系目标",
) -> FactReadResult:
    fields: dict[str, object] = {
        "object_id": object_id,
        "fact_type_key": fact_type_key,
        "status": status,
        "title": title,
    }
    if phase is not None:
        fields["phase"] = phase
    if relations is not None:
        fields["relations"] = relations
    return FactReadResult(
        Path(f"ldvh-base/{fact_type_key}s/{object_id}.yaml").as_posix(),
        "yaml",
        check_status,  # type: ignore[arg-type]
        fields if check_status != "not_found" else None,
        None,
        (),
        fingerprint,
    )


class _MemoryIndex:
    governed_project_id = _PROJECT

    def __init__(self, *reads: FactReadResult, complete: bool = True) -> None:
        self.reads = {
            (str(read.fields["fact_type_key"]), str(read.fields["object_id"])): read
            for read in reads
            if read.fields is not None
        }
        self.complete = complete
        self.fresh_reads: list[tuple[str, str]] = []

    def read(self, fact_type_key: str, object_id: str) -> FactReadResult | None:
        return self.reads.get((fact_type_key, object_id))

    def read_fresh(self, fact_type_key: str, object_id: str) -> FactReadResult | None:
        self.fresh_reads.append((fact_type_key, object_id))
        return self.read(fact_type_key, object_id)

    def base_read(self, fact_type_key: str, object_id: str) -> FactReadResult | None:
        return self.read(fact_type_key, object_id)

    def scan_valid_objects(
        self,
        fact_type_key: str,
        *,
        base: bool = False,
        require_all_canonical_valid: bool = False,
    ) -> tuple[tuple[FactReadResult, ...], bool]:
        del base
        invalid_peer = any(
            current_type == fact_type_key and read.check_status != "mechanically_valid"
            for (current_type, _), read in self.reads.items()
        )
        return (
            tuple(
                read
                for (current_type, _), read in self.reads.items()
                if current_type == fact_type_key and read.check_status == "mechanically_valid"
            ),
            self.complete and (not require_all_canonical_valid or not invalid_peer),
        )


def _validate(
    source: FactReadResult,
    *targets: FactReadResult,
) -> tuple[tuple[FactIssue, ...], bool]:
    assert source.fields is not None
    object_id = str(source.fields["object_id"])
    index = _MemoryIndex(source, *targets)
    return validate_project_relations(index, "workcase", object_id, source)  # type: ignore[arg-type]


@pytest.mark.parametrize("target_status", ["open", "blocked"])
def test_active_workcase_depends_on_requires_an_active_workcase_target(target_status: str) -> None:
    source = _read(
        "workcase-0001",
        "open",
        phase="executing",
        relations=[_relation("depends-on", "workcase-0002")],
    )
    issues, unavailable = _validate(source, _read("workcase-0002", target_status, phase="executing"))

    assert issues == ()
    assert unavailable is False


def test_depends_on_graph_does_not_treat_a_missing_deep_target_as_acyclic() -> None:
    source = _read(
        "workcase-0001",
        "open",
        phase="executing",
        relations=[_relation("depends-on", "workcase-0002")],
    )
    intermediate = _read(
        "workcase-0002",
        "open",
        phase="executing",
        relations=[_relation("depends-on", "workcase-0003")],
    )

    issues, unavailable = _validate(source, intermediate)

    assert unavailable is False
    assert any("关系图包含缺失" in issue.summary for issue in issues)


def test_workcase_depends_on_rejects_closed_target_and_human_closure_waiting_source() -> None:
    closed_target_source = _read(
        "workcase-0001",
        "open",
        phase="executing",
        relations=[_relation("depends-on", "workcase-0002")],
    )
    target_issues, _ = _validate(closed_target_source, _read("workcase-0002", "closed"))

    waiting_source = _read(
        "workcase-0001",
        "open",
        phase="human_closure_confirming",
        relations=[_relation("depends-on", "workcase-0002")],
    )
    source_issues, _ = _validate(waiting_source, _read("workcase-0002", "open", phase="executing"))

    assert any("目标类型或状态" in issue.summary for issue in target_issues)
    assert any("source 状态" in issue.summary for issue in source_issues)


@pytest.mark.parametrize("target_status", ["open", "blocked", "closed"])
def test_closed_workcase_routed_to_remains_valid_across_target_lifecycle(target_status: str) -> None:
    source = _read(
        "workcase-0001",
        "closed",
        relations=[_relation("routed-to", "workcase-0002")],
    )
    issues, unavailable = _validate(source, _read("workcase-0002", target_status, phase="executing"))

    assert issues == ()
    assert unavailable is False


def test_workcase_routed_to_accepts_open_spark_and_only_closed_source_can_declare_it() -> None:
    spark_target = _read("spark-0002", "open", fact_type_key="spark")
    closed_source = _read(
        "workcase-0001",
        "closed",
        relations=[_relation("routed-to", "spark-0002", fact_type_key="spark")],
    )
    target_issues, _ = _validate(closed_source, spark_target)

    active_source = _read(
        "workcase-0001",
        "open",
        phase="executing",
        relations=[_relation("routed-to", "workcase-0002")],
    )
    source_issues, _ = _validate(active_source, _read("workcase-0002", "open", phase="executing"))

    assert target_issues == ()
    assert any("source 状态" in issue.summary for issue in source_issues)


def test_workcase_relations_reject_cross_project_duplicate_self_missing_invalid_and_cycles() -> None:
    cross_project = _read(
        "workcase-0001",
        "open",
        phase="executing",
        relations=[_relation("depends-on", "workcase-0002", project_id="other-project")],
    )
    issues, unavailable = _validate(cross_project)
    assert unavailable is False
    assert any("同一管辖项目" in issue.summary for issue in issues)

    duplicate = _read(
        "workcase-0001",
        "open",
        phase="executing",
        relations=[
            _relation("depends-on", "workcase-0002"),
            _relation("depends-on", "workcase-0002"),
        ],
    )
    issues, _ = _validate(duplicate, _read("workcase-0002", "open", phase="executing"))
    assert any("不得重复" in issue.summary for issue in issues)

    self_ref = _read(
        "workcase-0001",
        "open",
        phase="executing",
        relations=[_relation("depends-on", "workcase-0001")],
    )
    issues, _ = _validate(self_ref)
    assert any("禁止自指" in issue.summary for issue in issues)

    missing = _read(
        "workcase-0001",
        "open",
        phase="executing",
        relations=[_relation("depends-on", "workcase-0002")],
    )
    issues, _ = _validate(missing)
    assert any("不存在" in issue.summary for issue in issues)

    invalid_target = _read("workcase-0002", "open", phase="executing", check_status="invalid")
    issues, _ = _validate(missing, invalid_target)
    assert any("mechanically valid" in issue.summary for issue in issues)

    cyclic_source = _read(
        "workcase-0001",
        "open",
        phase="executing",
        relations=[_relation("depends-on", "workcase-0002")],
    )
    cyclic_target = _read(
        "workcase-0002",
        "open",
        phase="executing",
        relations=[_relation("depends-on", "workcase-0001")],
    )
    issues, _ = _validate(cyclic_source, cyclic_target)
    assert any("有向循环" in issue.summary for issue in issues)


def test_workcase_related_to_allows_cycles_but_cannot_overlap_a_strong_edge() -> None:
    source = _read(
        "workcase-0001",
        "open",
        phase="executing",
        relations=[_relation("related-to", "workcase-0002")],
    )
    target = _read(
        "workcase-0002",
        "open",
        phase="executing",
        relations=[_relation("related-to", "workcase-0001")],
    )

    issues, unavailable = _validate(source, target)

    assert issues == ()
    assert unavailable is False

    overlapping = _read(
        "workcase-0001",
        "open",
        phase="executing",
        relations=[
            _relation("related-to", "workcase-0002"),
            _relation("depends-on", "workcase-0002"),
        ],
    )
    issues, _ = _validate(overlapping, target)
    assert any("强关系重叠" in issue.summary for issue in issues)


def test_unreadable_relation_target_makes_required_project_check_unavailable() -> None:
    source = _read(
        "workcase-0001",
        "open",
        phase="executing",
        relations=[_relation("depends-on", "workcase-0002")],
    )
    unavailable_target = _read(
        "workcase-0002",
        "open",
        phase="executing",
        check_status="unavailable",
    )

    issues, unavailable = _validate(source, unavailable_target)

    assert issues == ()
    assert unavailable is True


def test_proposal_snapshots_deduplicate_same_target_but_reject_conflicting_fingerprint() -> None:
    fields = {
        "closure_proposal": {
            "residual_decisions": [
                {
                    "residual_id": "residual-one",
                    "proposed_disposition": "route_existing",
                    "route_target": {**_target("workcase-0002"), "content_fingerprint": _FINGERPRINT_A},
                },
                {
                    "residual_id": "residual-two",
                    "proposed_disposition": "route_existing",
                    "route_target": {**_target("workcase-0002"), "content_fingerprint": _FINGERPRINT_A},
                },
            ]
        }
    }

    snapshots, issues = proposal_route_target_snapshots(fields)

    assert issues == ()
    assert len(snapshots) == 1
    assert snapshots[0].identity == (_PROJECT, "workcase", "workcase-0002")
    assert snapshots[0].origin_path == "closure_proposal.residual_decisions[0].route_target"

    fields["closure_proposal"]["residual_decisions"][1]["route_target"][  # type: ignore[index]
        "content_fingerprint"
    ] = _FINGERPRINT_B
    _, issues = proposal_route_target_snapshots(fields)
    assert any("fingerprint 必须一致" in issue.summary for issue in issues)


def test_request_snapshots_require_exact_shape_fingerprint_and_unique_target() -> None:
    values = [
        {"target": _target("workcase-0002"), "content_fingerprint": _FINGERPRINT_A},
        {"target": _target("workcase-0002"), "content_fingerprint": _FINGERPRINT_A},
        {"target": _target("workcase-0003"), "content_fingerprint": "not-a-fingerprint"},
    ]

    snapshots, issues = request_route_target_snapshots(values)

    assert len(snapshots) == 1
    assert snapshots[0].origin_path == "route_target_fingerprints[0].target"
    assert any("按目标去重" in issue.summary for issue in issues)
    assert any("64 位" in issue.summary for issue in issues)


def test_route_target_alignment_requires_proposal_after_and_request_exact_target_sets() -> None:
    target_two = WorkCaseRouteTargetSnapshot(
        FactReference(_PROJECT, "workcase", "workcase-0002"),
        _FINGERPRINT_A,
        "route_target_fingerprints[0].target",
    )
    target_three = WorkCaseRouteTargetSnapshot(
        FactReference(_PROJECT, "workcase", "workcase-0003"),
        _FINGERPRINT_B,
        "route_target_fingerprints[1].target",
    )
    after = {"relations": [_relation("routed-to", "workcase-0002")]}

    assert workcase_routed_target_identities(after) == ((_PROJECT, "workcase", "workcase-0002"),)
    assert (
        validate_workcase_route_target_alignment(
            after,
            proposal_snapshots=(target_two,),
            request_snapshots=(target_two,),
        )
        == ()
    )

    issues = validate_workcase_route_target_alignment(
        after,
        proposal_snapshots=(target_two, target_three),
        request_snapshots=(),
    )
    assert len([issue for issue in issues if "精确一致" in issue.summary]) == 2


def test_route_target_snapshot_guard_fresh_reads_and_distinguishes_new_from_unchanged_closed_target() -> None:
    target = WorkCaseRouteTargetSnapshot(
        FactReference(_PROJECT, "workcase", "workcase-0002"),
        _FINGERPRINT_A,
        "route_target_fingerprints[0].target",
    )
    closed_target = _read("workcase-0002", "closed", fingerprint=_FINGERPRINT_A)

    new_index = _MemoryIndex(closed_target)
    new_issues, unavailable = validate_workcase_route_target_snapshots(  # type: ignore[arg-type]
        new_index,
        "workcase-0001",
        (target,),
    )
    assert unavailable is False
    assert any("新形成" in issue.summary for issue in new_issues)
    assert new_index.fresh_reads == [("workcase", "workcase-0002")]

    existing_index = _MemoryIndex(closed_target)
    existing_issues, unavailable = validate_workcase_route_target_snapshots(  # type: ignore[arg-type]
        existing_index,
        "workcase-0001",
        (target,),
        existing_routed_targets=frozenset({target.identity}),
    )
    assert existing_issues == ()
    assert unavailable is False


def test_route_target_snapshot_guard_rejects_stale_invalid_cross_type_cross_project_and_self_targets() -> None:
    open_target = _read("workcase-0002", "open", phase="executing", fingerprint=_FINGERPRINT_A)
    index = _MemoryIndex(open_target)
    snapshots = (
        WorkCaseRouteTargetSnapshot(
            FactReference(_PROJECT, "workcase", "workcase-0002"),
            _FINGERPRINT_B,
            "route_target_fingerprints[0].target",
        ),
        WorkCaseRouteTargetSnapshot(
            FactReference(_PROJECT, "adr", "adr-0002"),
            _FINGERPRINT_A,
            "route_target_fingerprints[1].target",
        ),
        WorkCaseRouteTargetSnapshot(
            FactReference("other-project", "workcase", "workcase-0003"),
            _FINGERPRINT_A,
            "route_target_fingerprints[2].target",
        ),
        WorkCaseRouteTargetSnapshot(
            FactReference(_PROJECT, "workcase", "workcase-0001"),
            _FINGERPRINT_A,
            "route_target_fingerprints[3].target",
        ),
    )

    issues, unavailable = validate_workcase_route_target_snapshots(  # type: ignore[arg-type]
        index,
        "workcase-0001",
        snapshots,
    )

    assert unavailable is False
    assert any("已变化" in issue.summary for issue in issues)
    assert any("只能指向 WorkCase 或 Spark" in issue.summary for issue in issues)
    assert any("同一管辖项目" in issue.summary for issue in issues)
    assert any("禁止自指" in issue.summary for issue in issues)


def test_workcase_cannot_close_while_any_valid_source_depends_on_it() -> None:
    target = _read("workcase-0001", "open", phase="human_closure_confirming")
    dependent = _read(
        "workcase-0002",
        "open",
        phase="executing",
        relations=[_relation("depends-on", "workcase-0001")],
    )

    issues, unavailable = validate_workcase_incoming_dependencies(  # type: ignore[arg-type]
        _MemoryIndex(target, dependent),
        "workcase-0001",
    )

    assert unavailable is False
    assert any("workcase-0002" in issue.summary for issue in issues)


def test_incoming_dependency_guard_reports_incomplete_project_scan_as_unavailable() -> None:
    issues, unavailable = validate_workcase_incoming_dependencies(  # type: ignore[arg-type]
        _MemoryIndex(complete=False),
        "workcase-0001",
    )

    assert any(
        issue.category == "reference" and issue.field_path == "relations" and "入向 depends-on" in issue.summary
        for issue in issues
    )
    assert unavailable is True


def test_incoming_dependency_guard_does_not_silently_ignore_an_invalid_canonical_peer() -> None:
    target = _read("workcase-0001", "open", phase="human_closure_confirming")
    invalid_peer = _read(
        "workcase-0002",
        "open",
        phase="executing",
        check_status="invalid",
    )

    issues, unavailable = validate_workcase_incoming_dependencies(  # type: ignore[arg-type]
        _MemoryIndex(target, invalid_peer),
        "workcase-0001",
    )

    assert any(
        issue.category == "reference" and issue.field_path == "relations" and "入向 depends-on" in issue.summary
        for issue in issues
    )
    assert unavailable is True


def test_project_index_marks_invalid_canonical_peer_incomplete_for_closure_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "ldvh-base/workcases/workcase-0002.yaml"
    invalid_peer = _read(
        "workcase-0002",
        "open",
        phase="executing",
        check_status="invalid",
    )
    monkeypatch.setattr(relations_module, "_identity_issue", lambda *args: (None, None))
    monkeypatch.setattr(relations_module, "safe_list_directory", lambda *args: (path,))
    index = ProjectFactIndex(tmp_path, _PROJECT, {"workcase": FactSchema("workcase", ())})
    key = ("workcase", "workcase-0002")
    index.cache[key] = invalid_peer
    index.base_cache[key] = invalid_peer

    ordinary_reads, ordinary_complete = index.scan_valid_objects("workcase")
    closure_reads, closure_complete = index.scan_valid_objects(
        "workcase",
        require_all_canonical_valid=True,
    )

    assert ordinary_reads == closure_reads == ()
    assert ordinary_complete is True
    assert closure_complete is False


def test_spark_routed_to_current_rules_remain_independent_from_workcase_rules() -> None:
    assert not _target_condition("spark", "routed-to", "study", "active")
    assert not _target_condition("spark", "routed-to", "spark", "open")
    assert _target_condition("spark", "routed-to", "workcase", "closed")
    assert _target_has_readable_title("spark", "routed-to", {"title": "可读标题"})
    assert not _target_has_readable_title("spark", "routed-to", {"title": "  "})
    assert _source_condition("spark", "routed-to", {"status": "routed"})
    assert not _source_condition("spark", "routed-to", {"status": "discarded"})


@pytest.mark.parametrize("target_status", ["draft", "active", "discarded"])
def test_workcase_contributed_to_accepts_pitfall_across_target_lifecycle(target_status: str) -> None:
    source = _read(
        "workcase-0001",
        "open",
        phase="executing",
        relations=[_relation("contributed-to", "pitfall-0002", fact_type_key="pitfall")],
    )
    issues, unavailable = _validate(source, _read("pitfall-0002", target_status, fact_type_key="pitfall"))

    assert issues == ()
    assert unavailable is False


@pytest.mark.parametrize("source_status", ["open", "blocked", "closed"])
def test_workcase_contributed_to_source_condition_allows_active_and_closed_sources(source_status: str) -> None:
    assert _source_condition("workcase", "contributed-to", {"status": source_status})
    assert _source_condition(
        "workcase",
        "contributed-to",
        {"status": "open", "phase": "human_closure_confirming"},
    )
    assert not _target_condition("workcase", "contributed-to", "spark", "discarded")
    assert not _target_condition("workcase", "contributed-to", "adr", "retired")
    assert not _target_condition("workcase", "contributed-to", "pitfall", "retired")
    assert not _target_condition("workcase", "contributed-to", "workcase", "open")
    assert not _target_condition("workcase", "contributed-to", "study", "active")


def test_closed_workcase_contributed_to_remains_valid_when_pitfall_later_discarded() -> None:
    source = _read(
        "workcase-0001",
        "closed",
        relations=[_relation("contributed-to", "pitfall-0002", fact_type_key="pitfall")],
    )
    issues, unavailable = _validate(source, _read("pitfall-0002", "discarded", fact_type_key="pitfall"))

    assert issues == ()
    assert unavailable is False


def test_workcase_contributed_to_rejects_workcase_and_study_targets() -> None:
    workcase_target_source = _read(
        "workcase-0001",
        "open",
        phase="executing",
        relations=[_relation("contributed-to", "workcase-0002")],
    )
    workcase_issues, _ = _validate(workcase_target_source, _read("workcase-0002", "open", phase="executing"))

    study_target_source = _read(
        "workcase-0001",
        "open",
        phase="executing",
        relations=[_relation("contributed-to", "study-0002", fact_type_key="study")],
    )
    study_issues, _ = _validate(study_target_source, _read("study-0002", "active", fact_type_key="study"))

    assert any("目标类型或状态" in issue.summary for issue in workcase_issues)
    assert any("目标类型或状态" in issue.summary for issue in study_issues)


def test_workcase_contributed_to_reports_missing_invalid_and_unavailable_targets() -> None:
    missing_source = _read(
        "workcase-0001",
        "open",
        phase="executing",
        relations=[_relation("contributed-to", "adr-0002", fact_type_key="adr")],
    )
    missing_issues, missing_unavailable = _validate(missing_source)
    assert missing_unavailable is False
    assert any("不存在" in issue.summary for issue in missing_issues)

    invalid_target = _read("adr-0002", "active", fact_type_key="adr", check_status="invalid")
    invalid_issues, _ = _validate(missing_source, invalid_target)
    assert any("mechanically valid" in issue.summary for issue in invalid_issues)

    unavailable_target = _read("adr-0002", "active", fact_type_key="adr", check_status="unavailable")
    unavailable_issues, unavailable = _validate(missing_source, unavailable_target)
    assert unavailable_issues == ()
    assert unavailable is True


def test_workcase_contributed_to_rejects_cross_project_duplicate_and_self_reference() -> None:
    cross_project = _read(
        "workcase-0001",
        "open",
        phase="executing",
        relations=[_relation("contributed-to", "adr-0002", project_id="other-project", fact_type_key="adr")],
    )
    issues, unavailable = _validate(cross_project)
    assert unavailable is False
    assert any("同一管辖项目" in issue.summary for issue in issues)

    duplicate = _read(
        "workcase-0001",
        "open",
        phase="executing",
        relations=[
            _relation("contributed-to", "adr-0002", fact_type_key="adr"),
            _relation("contributed-to", "adr-0002", fact_type_key="adr"),
        ],
    )
    issues, _ = _validate(duplicate, _read("adr-0002", "active", fact_type_key="adr"))
    assert any("不得重复" in issue.summary for issue in issues)

    self_ref = _read(
        "workcase-0001",
        "open",
        phase="executing",
        relations=[_relation("contributed-to", "workcase-0001")],
    )
    issues, _ = _validate(self_ref)
    assert any("禁止自指" in issue.summary for issue in issues)


@pytest.mark.parametrize("target_status", ["active", "archived"])
def test_existing_workcase_file_asset_edge_accepts_valid_lifecycle_states(target_status: str) -> None:
    source = _read(
        "workcase-0001",
        "closed",
        relations=[_relation("has-file-asset", "file-asset-0002", fact_type_key="file-asset")],
    )
    target = _read("file-asset-0002", target_status, fact_type_key="file-asset")

    issues, unavailable = _validate(source, target)

    assert issues == ()
    assert unavailable is False
    assert _source_condition("workcase", "has-file-asset", {"status": "closed"})


def test_workcase_file_asset_edge_rejects_missing_invalid_and_wrong_type_targets() -> None:
    source = _read(
        "workcase-0001",
        "open",
        phase="executing",
        relations=[_relation("has-file-asset", "file-asset-0002", fact_type_key="file-asset")],
    )
    missing_issues, missing_unavailable = _validate(source)
    invalid_issues, invalid_unavailable = _validate(
        source,
        _read("file-asset-0002", "active", fact_type_key="file-asset", check_status="invalid"),
    )

    assert missing_unavailable is False
    assert invalid_unavailable is False
    assert any("不存在" in issue.summary for issue in missing_issues)
    assert any("mechanically valid" in issue.summary for issue in invalid_issues)
    assert not _target_condition("workcase", "has-file-asset", "study", "active")
