import json
import subprocess
import sys
from pathlib import Path

from .common import checker, write_md


PROJECT_ROOT = Path(__file__).resolve().parents[3]


def test_preflight_existing_spec_update_requires_human_gate_but_does_not_authorize_write(tmp_path):
    write_md(tmp_path / "specs" / "04-Code确定性执行规范.md", "# Code\n")
    write_md(
        tmp_path / "rules" / "LDVH-MAINTAINER-ENTRY.md",
        """
# LDVH 维护入口

```yaml
ldvh_asset:
  id: "ldvh-maintainer-entry"
  type: "rule"
  status: "active"
  canonical_path: "rules/LDVH-MAINTAINER-ENTRY.md"
  source_specs:
    - "specs/04-Code确定性执行规范.md"
  consumption_scenarios:
    - "测试场景"
  inputs:
    - "测试输入"
  outputs:
    - "测试输出"
  handoff: "测试交还"
  verification:
    - "python3 code/specs_validate.py v2-check --fail-on-diagnostics --format text"
  sync_triggers:
    - "source_specs 变化"
  deprecation: "测试废弃规则"
```
""",
    )

    report = checker.preflight_build(tmp_path, "specs/04-Code确定性执行规范.md", operation="update")
    codes = {item["code"] for item in report["diagnostics"]}

    assert report["metadata"]["read_only"] is True
    assert report["metadata"]["write_authorized"] is False
    assert report["input"]["asset_type"] == "specs"
    assert report["summary"]["status"] == "needs_human_gate"
    assert "PREFLIGHT_HUMAN_GATE_REQUIRED" in codes
    assert "PREFLIGHT_GIT_TRACE_REQUIRED" in codes
    assert "PREFLIGHT_SYNC_IMPACT_REVIEW_REQUIRED" in codes
    assert "PREFLIGHT_RULES_ASSET_IMPACT_REVIEW_REQUIRED" in codes
    assert report["rules_asset_impact"]["required"] is True
    assert report["rules_asset_impact"]["basis"] == "source_specs"
    assert [asset["canonical_path"] for asset in report["rules_asset_impact"]["assets"]] == ["rules/LDVH-MAINTAINER-ENTRY.md"]
    assert not any(item["severity"] == "error" for item in report["diagnostics"])


def test_preflight_spec_update_still_requires_rules_review_without_exact_source_match(tmp_path):
    write_md(tmp_path / "specs" / "05-Web信息同步规范.md", "# Web\n")

    report = checker.preflight_build(tmp_path, "specs/05-Web信息同步规范.md", operation="update")
    codes = {item["code"] for item in report["diagnostics"]}

    assert "PREFLIGHT_RULES_ASSET_IMPACT_REVIEW_REQUIRED" in codes
    assert "PREFLIGHT_RULES_ENTRY_SYNC_REVIEW_REQUIRED" in codes
    assert report["rules_asset_impact"]["required"] is True
    assert report["rules_asset_impact"]["assets"] == []
    assert report["rules_entry_sync_review"]["required"] is True
    assert report["rules_entry_sync_review"]["path"] == "specs/30-rules-entry-sync-review-Rules入口同步审查.md"


def test_preflight_rules_entry_sync_review_only_targets_specs_surface(tmp_path):
    write_md(tmp_path / "rules" / "LDVH-MAINTAINER-ENTRY.md", "# Rules\n")

    report = checker.preflight_build(tmp_path, "rules/LDVH-MAINTAINER-ENTRY.md", operation="update")
    codes = {item["code"] for item in report["diagnostics"]}

    assert "PREFLIGHT_RULES_ASSET_IMPACT_REVIEW_REQUIRED" in codes
    assert "PREFLIGHT_RULES_ENTRY_SYNC_REVIEW_REQUIRED" not in codes
    assert report["rules_entry_sync_review"]["required"] is False
    assert report["rules_entry_sync_review"]["basis"] == "not_applicable"


def test_preflight_blocks_update_for_missing_target(tmp_path):
    report = checker.preflight_build(tmp_path, "code/missing.py", operation="update")
    codes = {item["code"] for item in report["diagnostics"]}

    assert report["input"]["asset_type"] == "code"
    assert report["summary"]["status"] == "blocked"
    assert "PREFLIGHT_TARGET_MISSING" in codes


def test_preflight_blocks_unauthorized_location(tmp_path):
    write_md(tmp_path / "scratch" / "note.md", "# Scratch\n")

    report = checker.preflight_build(tmp_path, "scratch/note.md", operation="update")
    codes = {item["code"] for item in report["diagnostics"]}

    assert report["input"]["asset_type"] is None
    assert report["summary"]["status"] == "blocked"
    assert "PREFLIGHT_TARGET_LOCATION_UNAUTHORIZED" in codes


def test_preflight_allows_pyproject_as_code_dependency_entry(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[project]\nname = \"fixture\"\n", encoding="utf-8")

    report = checker.preflight_build(tmp_path, "pyproject.toml", operation="update")
    codes = {item["code"] for item in report["diagnostics"]}

    assert report["input"]["asset_type"] == "code"
    assert report["summary"]["status"] == "pass"
    assert "PREFLIGHT_TARGET_LOCATION_UNAUTHORIZED" not in codes


def test_preflight_blocks_create_when_target_exists(tmp_path):
    write_md(tmp_path / "tests" / "code" / "test_existing.py", "# existing\n")

    report = checker.preflight_build(tmp_path, "tests/code/test_existing.py", operation="create")
    codes = {item["code"] for item in report["diagnostics"]}

    assert report["input"]["asset_type"] == "tests"
    assert report["summary"]["status"] == "blocked"
    assert "PREFLIGHT_CREATE_TARGET_EXISTS" in codes


def test_preflight_field_and_status_are_degraded_warnings(tmp_path):
    write_md(tmp_path / "ldvh-base" / "sparks" / "SP-1.yaml", "id: SP-1\n")

    report = checker.preflight_build(
        tmp_path,
        "ldvh-base/sparks/SP-1.yaml",
        operation="update",
        field_path="status",
        status="closed",
    )
    codes = {item["code"] for item in report["diagnostics"]}

    assert report["input"]["asset_type"] == "fact_source"
    assert report["summary"]["status"] == "needs_human_gate"
    assert "PREFLIGHT_FIELD_PATH_NOT_VALIDATED" in codes
    assert "PREFLIGHT_STATUS_CHANGE_REQUIRES_OWNER_RULE" in codes
    assert "PREFLIGHT_HUMAN_GATE_REQUIRED" in codes


def test_preflight_identifies_known_field_owner_and_knowledge_map_context(tmp_path):
    write_md(
        tmp_path / "specs" / "04-Code确定性执行规范.md",
        """
# Code确定性执行规范

```yaml
v2_spec:
  spec_id: "04"
  spec_kind: "spec"
  title: "Code确定性执行规范"
  status: "active"
  authority: "active"
  canonical_path: "specs/04-Code确定性执行规范.md"
  created: "2026-06-23"
  updated: "2026-06-23"
  parent_spec: ""
  relation: ""
  positioning: "Code"
  scope: "Code"
  basis: []
  related_specs: []
  migration_sources: []
  active_fact_source: []
  code_consumption:
    - "knowledge_map_projection"
  migration_status: "migrated"
```

## 1. 本文解决的问题

Code。

## 2. 上位依据

无。

## 3. 构成要素归属与价值判断

Code。

## 4. 规范保障要求

| 保障要求 | 要求内容 | 保障机制 | 同步类型 | 触发条件 |
|---|---|---|---|---|
| 确定性执行要求 | 检查 | Code | 校验实现 | 变化时 |

## 5. Human Gate

高影响变化暂停。

## 6. 待补齐事项

无。
""",
    )

    report = checker.preflight_build(
        tmp_path,
        "specs/04-Code确定性执行规范.md",
        operation="update",
        field_path="v2_spec.status",
    )
    codes = {item["code"] for item in report["diagnostics"]}

    assert "PREFLIGHT_FIELD_PATH_OWNER_IDENTIFIED" in codes
    assert "PREFLIGHT_FIELD_PATH_NOT_VALIDATED" not in codes
    assert report["field_path_analysis"]["owner"] == "01-规范体系基础规范"
    assert report["knowledge_map_context"]["available"] is True
    assert report["knowledge_map_context"]["recommended_reads"]


def test_preflight_cli_json_and_text_outputs(tmp_path, capsys):
    write_md(tmp_path / "code" / "example.py", "print('ok')\n")

    exit_code = checker.preflight_main(tmp_path, "code/example.py", operation="update", output_format="json")
    report = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert report["metadata"]["tool"] == "code/specs_validate.py preflight"
    assert report["metadata"]["write_authorized"] is False
    assert report["summary"]["status"] == "pass"

    exit_code = checker.preflight_main(tmp_path, "missing/outside.md", operation="update", output_format="text")
    text_output = capsys.readouterr().out

    assert exit_code == 1
    assert "受控写入 preflight 完成" in text_output
    assert "- status: blocked" in text_output
    assert "PREFLIGHT_TARGET_LOCATION_UNAUTHORIZED" in text_output


def test_preflight_script_fast_path_outputs_json_without_full_cli_imports(tmp_path):
    write_md(tmp_path / "code" / "example.py", "print('ok')\n")

    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "code" / "specs_validate.py"),
            "preflight",
            "--root",
            str(tmp_path),
            "--target-path",
            "code/example.py",
            "--format",
            "json",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    report = json.loads(result.stdout)

    assert result.returncode == 0
    assert report["metadata"]["tool"] == "code/specs_validate.py preflight"
    assert report["summary"]["status"] == "pass"
    assert "active specs 规范诊断完成" not in result.stdout
