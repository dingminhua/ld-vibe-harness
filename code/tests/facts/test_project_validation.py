from __future__ import annotations

from pathlib import Path

import pytest

from ldvh.facts import project_validation
from ldvh.facts.contracts import LAYOUTS
from ldvh.facts.project_validation import stabilize_project_index
from ldvh.facts.relations import ProjectFactIndex, validate_project_relations
from ldvh.facts.repository import FactReadResult
from ldvh.facts.schema import FactSchema

_PROJECT = "sample"
_UID_A = "0198f1c7-8a2b-7c3d-9e4f-123456789abc"
_UID_B = "0198f1c7-8a2b-7c3d-9e4f-123456789abd"


def _target(fact_type_key: str, object_id: str) -> dict[str, str]:
    return {
        "governed_project_id": _PROJECT,
        "fact_type_key": fact_type_key,
        "object_id": object_id,
    }


def _relation(relation_key: str, fact_type_key: str, object_id: str) -> dict[str, object]:
    return {
        "relation_key": relation_key,
        "target": _target(fact_type_key, object_id),
    }


def test_configuration_uid_target_in_another_project_is_not_folded_into_local_graph() -> None:
    source = _read(
        "study",
        "study-0001",
        "active",
        object_uid=_UID_A,
        relations=[{"relation_key": "informs", "target": {"object_uid": _UID_B}}],
    )
    remote = _read("workcase", "workcase-0002", "open", phase="executing", object_uid=_UID_B)
    index = _IncompleteScanIndex(source)
    index.configuration_uid_resolver = lambda object_uid: (
        ("other", "workcase", "workcase-0002", remote),
        "resolved",
    )

    stabilize_project_index(index, (("study", "study-0001"),))

    assert index.cache[("study", "study-0001")].check_status == "mechanically_valid"


def _read(
    fact_type_key: str,
    object_id: str,
    status: str,
    *,
    phase: str | None = None,
    relations: list[dict[str, object]] | None = None,
    object_uid: str | None = None,
) -> FactReadResult:
    fields: dict[str, object] = {
        "object_id": object_id,
        "fact_type_key": fact_type_key,
        "status": status,
        "title": f"{fact_type_key} relation node",
    }
    if phase is not None:
        fields["phase"] = phase
    if relations is not None:
        fields["relations"] = relations
    if object_uid is not None:
        fields["object_uid"] = object_uid
    return FactReadResult(
        LAYOUTS[fact_type_key].canonical_path(object_id),
        LAYOUTS[fact_type_key].carrier,
        "mechanically_valid",
        fields,
        None,
        (),
    )


class _IncompleteScanIndex:
    governed_project_id = _PROJECT

    def __init__(
        self,
        candidate: FactReadResult,
        *stored: FactReadResult,
        scan_reads: tuple[FactReadResult, ...] = (),
    ) -> None:
        assert candidate.fields is not None
        candidate_key = (
            str(candidate.fields["fact_type_key"]),
            str(candidate.fields["object_id"]),
        )
        self.cache = {candidate_key: candidate}
        self.base_cache = {candidate_key: candidate}
        self.storage = {
            (str(read.fields["fact_type_key"]), str(read.fields["object_id"])): read
            for read in (*stored, *scan_reads)
            if read.fields is not None
        }
        self.scan_reads = scan_reads
        self.scan_calls = 0
        self.read_calls = 0
        for read in scan_reads:
            assert read.fields is not None
            key = (str(read.fields["fact_type_key"]), str(read.fields["object_id"]))
            self.cache[key] = read
            self.base_cache[key] = read

    def read(self, fact_type_key: str, object_id: str) -> FactReadResult | None:
        self.read_calls += 1
        key = (fact_type_key, object_id)
        if key not in self.cache:
            read = self.storage.get(key)
            if read is None:
                layout = LAYOUTS.get(fact_type_key)
                if layout is None or layout.object_id_pattern.fullmatch(object_id) is None:
                    return None
                read = FactReadResult(
                    layout.canonical_path(object_id),
                    layout.carrier,
                    "not_found",
                    None,
                    None,
                    (),
                )
            self.cache[key] = read
            self.base_cache[key] = read
        return self.cache[key]

    def base_read(self, fact_type_key: str, object_id: str) -> FactReadResult | None:
        self.read(fact_type_key, object_id)
        return self.base_cache.get((fact_type_key, object_id))

    def resolve_uid(self, object_uid: str) -> tuple[FactReadResult | None, str]:
        matches = [
            read
            for read in self.storage.values()
            if read.fields is not None and read.fields.get("object_uid") == object_uid
        ]
        for read in self.cache.values():
            if read.fields is not None and read.fields.get("object_uid") == object_uid and read not in matches:
                matches.append(read)
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
        self.scan_calls += 1
        del require_all_canonical_valid
        reads: list[FactReadResult] = []
        for read in self.scan_reads:
            assert read.fields is not None
            if read.fields["fact_type_key"] != fact_type_key:
                continue
            key = (str(read.fields["fact_type_key"]), str(read.fields["object_id"]))
            self.cache.setdefault(key, read)
            self.base_cache.setdefault(key, read)
            reads.append(self.base_cache[key] if base else self.cache[key])
        return tuple(reads), False


def test_fixed_point_absorbs_recursive_targets_across_relation_keys_when_scans_are_incomplete() -> None:
    candidate = _read(
        "study",
        "study-0001",
        "active",
        relations=[_relation("informs", "spark", "spark-0001")],
    )
    spark = _read(
        "spark",
        "spark-0001",
        "routed",
        relations=[_relation("routed-to", "workcase", "workcase-0001")],
    )
    workcase = _read(
        "workcase",
        "workcase-0001",
        "open",
        phase="executing",
        relations=[_relation("depends-on", "workcase", "workcase-0002")],
    )
    index = _IncompleteScanIndex(candidate, spark, workcase)

    stabilize_project_index(index, (("study", "study-0001"),))  # type: ignore[arg-type]

    assert index.cache[("workcase", "workcase-0001")].check_status == "invalid"
    assert index.cache[("spark", "spark-0001")].check_status == "invalid"
    assert index.cache[("study", "study-0001")].check_status == "invalid"
    assert index.cache[("workcase", "workcase-0002")].check_status == "not_found"
    assert index.scan_calls == 0


def test_fixed_point_follows_uid_targets_and_propagates_invalidity() -> None:
    candidate = _read(
        "study",
        "study-0001",
        "active",
        object_uid=_UID_A,
        relations=[{"relation_key": "informs", "target": {"object_uid": _UID_B}}],
    )
    workcase = _read(
        "workcase",
        "workcase-0001",
        "open",
        phase="executing",
        object_uid=_UID_B,
        relations=[_relation("depends-on", "workcase", "workcase-0002")],
    )
    index = _IncompleteScanIndex(candidate, workcase)

    stabilize_project_index(index, (("study", "study-0001"),))  # type: ignore[arg-type]

    assert index.cache[("workcase", "workcase-0001")].check_status == "invalid"
    assert index.cache[("study", "study-0001")].check_status == "invalid"


def test_duplicate_object_uid_invalidates_candidate_without_guessing() -> None:
    candidate = _read("spark", "spark-0001", "open", object_uid=_UID_A)
    duplicate = _read("workcase", "workcase-0001", "open", phase="executing", object_uid=_UID_A)
    index = _IncompleteScanIndex(candidate, duplicate)

    stabilize_project_index(index, (("spark", "spark-0001"),))  # type: ignore[arg-type]

    result = index.cache[("spark", "spark-0001")]
    assert result.check_status == "invalid"
    assert any(issue.category == "identity" and "object_uid" in issue.summary for issue in result.issues)


def test_incomplete_unrelated_scans_do_not_poison_a_relation_free_candidate() -> None:
    candidate = _read("spark", "spark-0001", "open")
    unrelated = _read(
        "workcase",
        "workcase-0001",
        "open",
        phase="executing",
        relations=[_relation("depends-on", "workcase", "workcase-0002")],
    )
    index = _IncompleteScanIndex(candidate, scan_reads=(unrelated,))

    stabilize_project_index(index, (("spark", "spark-0001"),))  # type: ignore[arg-type]

    assert index.cache[("spark", "spark-0001")].check_status == "mechanically_valid"
    assert index.cache[("spark", "spark-0001")].issues == ()
    assert index.cache[("workcase", "workcase-0001")].check_status == "mechanically_valid"
    assert index.scan_calls == 0


def test_known_target_type_without_a_derived_schema_is_unavailable_not_invalid(
    tmp_path: Path,
) -> None:
    source = _read(
        "study",
        "study-0001",
        "active",
        relations=[_relation("informs", "spark", "spark-0001")],
    )
    index = ProjectFactIndex(
        tmp_path,
        _PROJECT,
        {"study": FactSchema("study", ())},
    )
    index.cache[("study", "study-0001")] = source
    index.base_cache[("study", "study-0001")] = source

    issues, unavailable = validate_project_relations(index, "study", "study-0001", source)
    target = index.cache[("spark", "spark-0001")]

    assert unavailable is True
    assert target.check_status == "unavailable"
    assert any("缺少当前派生 Schema" in issue.summary for issue in target.issues)
    assert issues == ()


def test_relation_closure_budget_marks_only_reachable_sources_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate = _read(
        "study",
        "study-0001",
        "active",
        relations=[_relation("informs", "spark", "spark-0001")],
    )
    spark = _read(
        "spark",
        "spark-0001",
        "routed",
        relations=[_relation("routed-to", "workcase", "workcase-0001")],
    )
    workcase = _read(
        "workcase",
        "workcase-0001",
        "open",
        phase="executing",
        relations=[_relation("depends-on", "workcase", "workcase-0002")],
    )
    unrelated = _read("adr", "adr-0001", "active")
    index = _IncompleteScanIndex(candidate, spark, workcase, scan_reads=(unrelated,))
    monkeypatch.setattr(project_validation, "MAX_GRAPH_OBJECTS", 3)

    stabilize_project_index(index, (("study", "study-0001"),))  # type: ignore[arg-type]

    assert index.cache[("spark", "spark-0001")].check_status == "unavailable"
    assert index.cache[("study", "study-0001")].check_status == "unavailable"
    assert index.cache[("adr", "adr-0001")].check_status == "mechanically_valid"
    assert index.cache[("workcase", "workcase-0001")].check_status == "unavailable"
    assert ("workcase", "workcase-0002") not in index.cache


def test_long_dependency_chain_is_stabilized_with_linear_target_reads() -> None:
    node_count = 1_000
    reads = [
        _read(
            "workcase",
            f"workcase-{index:04d}",
            "open",
            phase="executing",
            relations=(
                [_relation("depends-on", "workcase", f"workcase-{index + 1:04d}")]
                if index < node_count
                else None
            ),
        )
        for index in range(1, node_count + 1)
    ]
    index = _IncompleteScanIndex(reads[0], *reads[1:])

    stabilize_project_index(index, (("workcase", "workcase-0001"),))  # type: ignore[arg-type]

    assert all(read.check_status == "mechanically_valid" for read in index.cache.values())
    assert index.read_calls <= 2 * node_count


def test_single_pass_graph_analysis_marks_cycle_and_all_reaching_sources_invalid() -> None:
    first = _read(
        "workcase",
        "workcase-0001",
        "open",
        phase="executing",
        relations=[_relation("depends-on", "workcase", "workcase-0002")],
    )
    second = _read(
        "workcase",
        "workcase-0002",
        "open",
        phase="executing",
        relations=[_relation("depends-on", "workcase", "workcase-0003")],
    )
    third = _read(
        "workcase",
        "workcase-0003",
        "open",
        phase="executing",
        relations=[_relation("depends-on", "workcase", "workcase-0002")],
    )
    index = _IncompleteScanIndex(first, second, third)

    stabilize_project_index(index, (("workcase", "workcase-0001"),))  # type: ignore[arg-type]

    for object_id in ("workcase-0001", "workcase-0002", "workcase-0003"):
        read = index.cache[("workcase", object_id)]
        assert read.check_status == "invalid"
        assert any("有向循环" in issue.summary for issue in read.issues)
