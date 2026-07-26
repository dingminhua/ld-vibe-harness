from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from ldvh.facts import relations
from ldvh.facts.creation import CreationBoundary
from ldvh.facts.models import FactIssue
from ldvh.facts.repository import FactReadResult
from ldvh.facts.schema import FactSchema
from ldvh.filesystem import UnsafePathError
from ldvh_web_facts import machine as web_machine
from ldvh_web_facts import read_application as web_read_application
from ldvh_web_facts.machine import MachineRequestError
from ldvh_web_facts.read_application import (
    FactTypeRawSnapshot,
    discover_fact_type_raw,
    read_web_spark_list,
    read_web_workcase_detail,
    read_web_workcase_list,
)


def _reparse_rejected(*args: object, **kwargs: object) -> tuple[Path, ...]:
    raise UnsafePathError("simulated reparse directory")


def test_web_machine_only_exposes_read_operations() -> None:
    assert web_machine._OPERATIONS == frozenset(
        {"list-sparks", "read-spark", "list-workcases", "read-workcase"}
    )


def test_web_machine_rejects_removed_create_operation() -> None:
    request = {
        "protocol_version": 1,
        "operation": "create-spark",
        "scope": {},
        "arguments": {},
    }
    try:
        web_machine._request_parts(request)
    except MachineRequestError as exc:
        assert "not supported" in str(exc)
    else:
        raise AssertionError("create-spark must not remain supported")


def test_web_machine_script_runs_under_isolated_python_and_emits_one_json_line() -> None:
    script = Path(web_machine.__file__).resolve()
    request = {
        "protocol_version": 1,
        "operation": "create-spark",
        "scope": {},
        "arguments": {},
    }
    completed = subprocess.run(
        [sys.executable, "-I", "-B", "-X", "utf8", str(script)],
        input=json.dumps(request, separators=(",", ":")).encode("utf-8"),
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0
    assert completed.stderr == b""
    assert completed.stdout.endswith(b"\n")
    assert completed.stdout[:-1].count(b"\n") == 0
    response = json.loads(completed.stdout)
    assert response == {
        "protocol_version": 1,
        "operation": "create-spark",
        "status": "invalid",
        "result": None,
        "error": "operation is not supported",
        "completion_unknown": False,
    }


def test_raw_type_scan_detects_listing_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    def changing_listing(*args: object, **kwargs: object) -> tuple[Path, ...]:
        nonlocal calls
        calls += 1
        return () if calls == 1 else (tmp_path / "ldvh-base/sparks/spark-0001.yaml",)

    monkeypatch.setattr(web_read_application, "_identity_issue", lambda *args: (None, None))
    monkeypatch.setattr(web_read_application, "safe_list_directory", changing_listing)

    snapshot = discover_fact_type_raw(
        tmp_path,
        "sample",
        tmp_path / ".git",
        {"spark": FactSchema("spark", ())},
        "spark",
    )

    assert snapshot.coverage_complete is False
    assert snapshot.objects == ()
    assert "扫描期间发生变化" in snapshot.structural_problems[-1]["issues"][0]["summary"]


def test_raw_type_scan_marks_unsafe_directory_incomplete(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(web_read_application, "_identity_issue", lambda *args: (None, None))
    monkeypatch.setattr(web_read_application, "safe_list_directory", _reparse_rejected)

    snapshot = discover_fact_type_raw(
        tmp_path,
        "sample",
        tmp_path / ".git",
        {"spark": FactSchema("spark", ())},
        "spark",
    )

    assert snapshot.coverage_complete is False
    assert snapshot.objects == ()
    assert "无法安全、完整地枚举" in snapshot.structural_problems[0]["issues"][0]["summary"]


def test_raw_type_scan_counts_noncanonical_carriers_toward_coverage_budget(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = tuple(tmp_path / f"legacy-{index}.yaml" for index in range(relations.MAX_GRAPH_OBJECTS + 1))
    monkeypatch.setattr(web_read_application, "_identity_issue", lambda *args: (None, None))
    monkeypatch.setattr(web_read_application, "safe_list_directory", lambda *args, **kwargs: paths)

    snapshot = discover_fact_type_raw(
        tmp_path,
        "sample",
        tmp_path / ".git",
        {"spark": FactSchema("spark", ())},
        "spark",
    )

    assert snapshot.coverage_complete is False
    assert snapshot.objects == ()
    assert "10,000" in snapshot.structural_problems[0]["issues"][0]["summary"]


def test_raw_type_scan_preserves_invalid_read_instead_of_filtering_it(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "ldvh-base/sparks/spark-0001.yaml"
    monkeypatch.setattr(web_read_application, "_identity_issue", lambda *args: (None, None))
    monkeypatch.setattr(
        web_read_application,
        "safe_list_directory",
        lambda _root, directory: (path,) if directory == "ldvh-base/sparks" else (),
    )
    monkeypatch.setattr(
        web_read_application.ProjectFactIndex,
        "read",
        lambda *args, **kwargs: FactReadResult(
            "ldvh-base/sparks/spark-0001.yaml",
            "yaml",
            "invalid",
            None,
            None,
            (FactIssue("schema", "forced invalid"),),
        ),
    )

    snapshot = discover_fact_type_raw(
        tmp_path,
        "sample",
        tmp_path / ".git",
        {"spark": FactSchema("spark", ())},
        "spark",
    )

    assert snapshot.coverage_complete is True
    assert snapshot.objects[0][1].check_status == "invalid"


def test_projected_budget_problem_uses_the_public_issue_category_closed_set(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    read = FactReadResult(
        "ldvh-base/sparks/spark-0001.yaml",
        "yaml",
        "mechanically_valid",
        {"object_id": "spark-0001", "summary": "x" * 256},
        None,
        (),
        content_fingerprint="0" * 64,
    )
    snapshot = FactTypeRawSnapshot("spark", (("spark-0001", read),), (), True)
    monkeypatch.setattr(web_read_application, "discover_fact_type_raw", lambda *args, **kwargs: snapshot)
    monkeypatch.setattr(web_read_application, "MAX_WEB_SPARK_PROJECTED_BYTES", 1)

    listed = read_web_spark_list(
        CreationBoundary("sample", tmp_path, tmp_path / ".git"),
        {},
    )

    issue = listed.structural_problems[0]["issues"][0]
    assert issue == {
        "category": "reference",
        "field_path": None,
        "summary": "Spark Web 读取结果超过 1 bytes 聚合预算",
    }


def test_workcase_list_only_exposes_mechanically_valid_fact_content(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    valid = FactReadResult(
        "ldvh-base/workcases/workcase-0001.yaml",
        "yaml",
        "mechanically_valid",
        {"fact_type_key": "workcase", "object_id": "workcase-0001", "goal": "完成目标"},
        None,
        (),
        content_fingerprint="1" * 64,
    )
    invalid = FactReadResult(
        "ldvh-base/workcases/workcase-0002.yaml",
        "yaml",
        "invalid",
        {"fact_type_key": "workcase", "object_id": "workcase-0002", "goal": "不得泄露的解析内容"},
        None,
        (),
        content_fingerprint="2" * 64,
    )
    snapshot = FactTypeRawSnapshot(
        "workcase",
        (("workcase-0001", valid), ("workcase-0002", invalid)),
        (),
        True,
    )
    monkeypatch.setattr(web_read_application, "discover_fact_type_raw", lambda *args, **kwargs: snapshot)

    listed = read_web_workcase_list(
        CreationBoundary("sample", tmp_path, tmp_path / ".git"),
        {},
    )

    assert listed.status == "complete"
    assert [item["object_ref"]["object_id"] for item in listed.items] == ["workcase-0001"]
    assert listed.items[0]["fact_object"] == valid.fields
    assert listed.object_problems[0]["check_status"] == "invalid"
    assert listed.object_problems[0]["fact_object"] is None
    assert listed.object_problems[0]["content_fingerprint"] is None


def test_workcase_list_coverage_distinguishes_completed_and_unavailable_objects(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    valid = FactReadResult(
        "ldvh-base/workcases/workcase-0001.yaml",
        "yaml",
        "mechanically_valid",
        {"fact_type_key": "workcase", "object_id": "workcase-0001", "goal": "完成目标"},
        None,
        (),
        content_fingerprint="1" * 64,
    )
    unavailable = FactReadResult(
        "ldvh-base/workcases/workcase-0002.yaml",
        "yaml",
        "unavailable",
        None,
        None,
        (),
    )
    boundary = CreationBoundary("sample", tmp_path, tmp_path / ".git")

    monkeypatch.setattr(
        web_read_application,
        "discover_fact_type_raw",
        lambda *args, **kwargs: FactTypeRawSnapshot(
            "workcase", (("workcase-0001", valid), ("workcase-0002", unavailable)), (), True
        ),
    )
    assert read_web_workcase_list(boundary, {}).status == "partial"

    monkeypatch.setattr(
        web_read_application,
        "discover_fact_type_raw",
        lambda *args, **kwargs: FactTypeRawSnapshot(
            "workcase", (("workcase-0002", unavailable),), (), True
        ),
    )
    assert read_web_workcase_list(boundary, {}).status == "unavailable"


def test_workcase_detail_reads_exact_identity_without_scanning_the_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    read = FactReadResult(
        "ldvh-base/workcases/workcase-0001.yaml",
        "yaml",
        "mechanically_valid",
        {"fact_type_key": "workcase", "object_id": "workcase-0001", "goal": "完成目标"},
        None,
        (),
        content_fingerprint="1" * 64,
    )

    class ExactIndex:
        def __init__(self, *args: object) -> None:
            self.cache = {("workcase", "workcase-0001"): read}

        def read(self, fact_type_key: str, object_id: str) -> FactReadResult:
            assert (fact_type_key, object_id) == ("workcase", "workcase-0001")
            return read

    monkeypatch.setattr(web_read_application, "ProjectFactIndex", ExactIndex)
    monkeypatch.setattr(web_read_application, "stabilize_project_index", lambda *args: None)
    monkeypatch.setattr(
        web_read_application,
        "discover_fact_type_raw",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("detail must not scan")),
    )

    detail = read_web_workcase_detail(
        CreationBoundary("sample", tmp_path, tmp_path / ".git"),
        {},
        "workcase-0001",
    )

    assert detail.status == "ok"
    assert detail.item is not None
    assert detail.item["check_status"] == "mechanically_valid"
    assert detail.item["fact_object"] == read.fields


def test_type_scan_reports_noncanonical_carriers_instead_of_silently_ignoring_them(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    foreign = tmp_path / "ldvh-base" / "workcases" / "workcase-0001.yml"
    monkeypatch.setattr(web_read_application, "safe_list_directory", lambda *args: (foreign,))
    monkeypatch.setattr(web_read_application, "_identity_issue", lambda *args: (None, None))

    snapshot = discover_fact_type_raw(
        tmp_path,
        "sample",
        tmp_path / ".git",
        {"workcase": FactSchema("workcase", ())},
        "workcase",
    )

    assert snapshot.coverage_complete is False
    assert snapshot.structural_problems == (
        {
            "fact_type_key": "workcase",
            "canonical_path": "ldvh-base/workcases/workcase-0001.yml",
            "check_status": "unavailable",
            "issues": [
                {
                    "category": "location",
                    "field_path": None,
                    "summary": "该载体不符合当前事实类型的权威文件路径与对象身份规则",
                }
            ],
        },
    )
