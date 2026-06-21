import json
from .common import checker, write_md
from spec_checks import ldvh_landing as ldvh_landing_checks
from .test_landing_report import build_landing_report_fixture
from .test_governed_projects import write_governed_projects

# ══════════════════════════════════════════════════════════════════════
# ldvh-landing-check — 42 LDVH落地与检查派生报告
# ══════════════════════════════════════════════════════════════════════

def test_ldvh_landing_core_implementation_lives_in_spec_checks():
    assert checker.ldvh_landing_checks is ldvh_landing_checks
    assert ldvh_landing_checks.ldvh_landing_check_build.__module__ == "spec_checks.ldvh_landing"
    assert ldvh_landing_checks.landing_plan_build.__module__ == "spec_checks.ldvh_landing"


def build_ldvh_landing_check_fixture(tmp_path, monkeypatch):
    docs_specs = build_landing_report_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(checker, "SPECS_DIR", docs_specs)
    evidence_file = tmp_path / "tests" / "code" / "specs_validate_checks" / "test_ldvh_landing.py"
    evidence_file.parent.mkdir(parents=True, exist_ok=True)
    evidence_file.write_text("# evidence fixture\n", encoding="utf-8")
    write_governed_projects(
        tmp_path,
        """
product_name: LD Vibe Harness
product_description: |
  测试管辖项目配置。
projects:
  - id: ldvh-test
    path: /tmp/ldvh-test
""",
    )
    workarea_dir = tmp_path / "ldvh-base" / "workareas"
    workarea_dir.mkdir(parents=True, exist_ok=True)
    (workarea_dir / "workarea-0001-test.yaml").write_text(
        """
id: workarea-0001
type: workarea
title: 测试工作域
status: active
created: '2026-06-10T00:00:00'
updated: '2026-06-10T00:00:00'
description: 测试工作域说明
source: 测试
related_docs: []
related_adrs: []
related_sparks: []
related_pitfalls: []
workcases:
  - workcase-0001
""".strip()
        + "\n",
        encoding="utf-8",
    )
    workcase_dir = tmp_path / "ldvh-base" / "workcases"
    workcase_dir.mkdir(parents=True, exist_ok=True)
    (workcase_dir / "workcase-0001-test.yaml").write_text(
        """
id: workcase-0001
type: workcase
title: 测试工作项
goal: |
  验证测试工作项夹具。
status: active
created: '2026-06-10T00:00:00'
updated: '2026-06-10T00:00:00'
workarea: workarea-0001
priority: P2
description: 测试工作项说明
success_criteria: |
  - [ ] 可验证条件
source: 测试
orchestration:
  mode: single
  execution_items:
    - id: item-1
      title: 测试执行项
      role: code
      mode: single
      input_refs:
        - code/specs_validate.py
      expected_output: 测试落地检查。
      status: done
      result_summary: 已完成。
      evidence_refs:
        - tests/code/specs_validate_checks/test_ldvh_landing.py
      blocking_reason:
  review:
    controller_self_check: true
    specialist_review:
      required: false
      role:
      expected_output:
    human_closure_review: true
verification_evidence: ''
closure_evidence: ''
review_requested_at: ''
closed_at: ''
related_docs: []
related_adrs: []
related_sparks: []
related_pitfalls: []
related_workcases: []
""".strip()
        + "\n",
        encoding="utf-8",
    )
    return docs_specs


def test_ldvh_landing_check_consumes_existing_reports(tmp_path, monkeypatch):
    build_ldvh_landing_check_fixture(tmp_path, monkeypatch)

    report = checker.ldvh_landing_check_build(tmp_path)

    assert report["metadata"]["report"] == "ldvh-landing-check"
    assert report["metadata"]["source_of_truth"] is False
    assert {item["id"] for item in report["checks"]} == {
        "governed_projects",
        "landing_report",
        "runtime_projection",
        "human_gate",
        "fact_validate",
        "spec_validate",
    }
    assert report["summary"]["status"] == "open"
    assert report["summary"]["bootstrap_baseline_status"] == "open"
    assert report["summary"]["bootstrap_baseline_open_item_count"] >= 1
    assert next(item for item in report["checks"] if item["id"] == "governed_projects")["status"] == "closed"
    assert next(item for item in report["checks"] if item["id"] == "fact_validate")["status"] == "closed"
    assert any(item["id"] == "human_gate" and item["status"] == "degraded" for item in report["remaining_gaps"])
    baseline = report["bootstrap_baseline"]
    assert [item["id"] for item in baseline["definitions"]] == [
        "specs_integrity",
        "asset_directories",
        "governed_projects_config",
        "work_model_workflow_indexes",
        "environment_matrix",
        "runtime_projection_entry",
        "code_self_check",
        "web_asset",
        "report_structure",
        "gap_classification_routing",
    ]
    assert {item["id"] for item in baseline["items"]} == {item["id"] for item in baseline["definitions"]}
    assert baseline["summary"]["item_count"] == 10
    assert next(item for item in baseline["items"] if item["id"] == "web_asset")["status"] == "open"
    assert next(item for item in baseline["items"] if item["id"] == "report_structure")["status"] == "closed"
    assert "环境承接" in next(item for item in baseline["items"] if item["id"] == "environment_matrix")["gap_categories"]
    assert set(baseline["summary"]["gap_categories"]) <= {"规范", "Code", "Web", "WorkCase", "事实源", "环境承接", "Human Gate"}


def test_ldvh_landing_check_reports_missing_governed_projects(tmp_path, monkeypatch):
    build_landing_report_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(checker, "SPECS_DIR", tmp_path / "docs" / "specs")

    report = checker.ldvh_landing_check_build(tmp_path)

    governed = next(item for item in report["checks"] if item["id"] == "governed_projects")
    assert report["summary"]["status"] == "open"
    assert governed["status"] == "open"
    assert governed["issues"][0]["code"] == "GOVERNED_PROJECTS_MISSING"


def test_ldvh_landing_check_reports_fact_validation_issues(tmp_path, monkeypatch):
    build_ldvh_landing_check_fixture(tmp_path, monkeypatch)
    bad_workcase = tmp_path / "ldvh-base" / "workcases" / "workcase-0002-bad.yaml"
    bad_workcase.write_text("id: bad\ntype: workcase\n", encoding="utf-8")

    report = checker.ldvh_landing_check_build(tmp_path)

    fact_check = next(item for item in report["checks"] if item["id"] == "fact_validate")
    assert report["summary"]["status"] == "open"
    assert fact_check["status"] == "open"
    assert fact_check["issue_count"] > 0


def test_ldvh_landing_check_cli_outputs_json(tmp_path, monkeypatch, capsys):
    build_ldvh_landing_check_fixture(tmp_path, monkeypatch)

    exit_code = checker.main(["ldvh-landing-check", "--workspace-root", str(tmp_path), "--format", "json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert payload["metadata"]["report"] == "ldvh-landing-check"
    assert payload["summary"]["status"] == "open"
    assert payload["metadata"]["bootstrap_baseline_source"] == "docs/studies/42-ldvh-landing-check-LDVH落地与检查.md (已退回 studies，待重新设计)"
    assert payload["bootstrap_baseline"]["summary"]["item_count"] == 10
    assert payload["remaining_gaps"]
