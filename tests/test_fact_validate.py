import json
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "tools" / "fact_validate.py"


def run_checker(*paths, extra_args=None):
    cmd = ["python3", str(SCRIPT_PATH), *[str(path) for path in paths]]
    if extra_args:
        cmd.extend(extra_args)
    return subprocess.run(
        cmd,
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def write_yaml(path, content):
    path.write_text(content.strip() + "\n", encoding="utf-8")
    return path


def valid_intent_yaml():
    return """
id: intent-0001
type: intent
title: Valid Intent
status: active
created: "2026-06-03"
updated: "2026-06-03"
description: Define a valid intent fixture
success_criteria:
  - Validator accepts this intent
source: test
related_tasks: []
related_adrs: []
"""


def valid_task_yaml(status="planned", extra=""):
    return f"""
id: task-0001
type: task
title: Valid Task
status: {status}
created: "2026-06-03"
updated: "2026-06-03"
description: Define a valid task fixture
source: test
acceptance:
  - Validator accepts this task
related_adrs: []
related_changes: []
blocked_by: []
{extra}
"""


def valid_profile_yaml(project_root: Path):
    ldvh_base_path = project_root / "ldvh-base"
    docs_path = project_root / "docs"
    environment_record_path = project_root / "LDVH-ENVIRONMENT-INITIALIZATION.md"
    return f"""
id: profile-0001
type: profile
title: Valid Profile
status: active
created: "2026-06-04"
updated: "2026-06-04"
description: Define a valid profile fixture
project_name: test-project
project_kind: governed_project
project_path: {project_root}
ldvh_base_path: {ldvh_base_path}
docs_path: {docs_path}
environment_record_path: {environment_record_path}
related_intents: []
related_tasks: []
related_adrs: []
related_memos: []
related_pitfalls: []
related_docs: []
related_changes: []
"""


def valid_pitfall_yaml(status="active", extra=""):
    return f"""
id: pitfall-0001
type: pitfall
title: Valid Pitfall
status: {status}
created: "2026-06-04"
updated: "2026-06-04"
symptoms: Symptom
trigger_conditions: Trigger condition
root_cause: Root cause
resolution: Resolution
verification: |
  ## 验证结果

  Verified.
avoidance: Avoidance
applicability: Applicability
severity: medium
repeatability: recurring
tags: []
source_tasks: []
source_memos: []
related_intents: []
related_adrs: []
related_profiles: []
related_changes: []
related_docs: []
related_rules: []
{extra}
"""


def prepare_profile_project(tmp_path: Path) -> Path:
    project_root = tmp_path / "project"
    (project_root / "ldvh-base").mkdir(parents=True)
    (project_root / "docs").mkdir()
    (project_root / "LDVH-ENVIRONMENT-INITIALIZATION.md").write_text("# LDVH 环境初始化记录\n", encoding="utf-8")
    return project_root


def valid_memo_yaml(status="active", extra=""):
    return f"""
id: memo-0001
type: memo
title: Valid Memo
status: {status}
created: "2026-06-04"
updated: "2026-06-04"
description: Define a valid memo fixture
source: test
category: gap
{extra}
"""


def valid_adr_yaml(status="accepted"):
    return f"""
id: adr-0001
type: adr
title: Valid ADR
status: {status}
created: "2026-06-04"
updated: "2026-06-04"
context: Define a valid ADR fixture
decision: Accept this ADR fixture
consequences: Validator accepts this ADR
related_tasks: []
related_adrs: []
related_changes: []
"""


def valid_change_yaml():
    return """
id: change-0001
type: change
title: Valid Change
status: proposed
created: "2026-06-04"
updated: "2026-06-04"
description: Define a valid change fixture
change_type: spec
scope: tests
related_tasks: []
related_adrs: []
affected_files: []
"""


def test_valid_intent_cli_exit_zero(tmp_path):
    path = write_yaml(tmp_path / "intent-0001-valid-intent.yaml", valid_intent_yaml())

    result = run_checker(path)

    assert result.returncode == 0
    assert result.stdout.strip() == "检查完成: files=1 errors=0 warnings=0"
    assert result.stderr == ""


def test_valid_task_cli_exit_zero(tmp_path):
    path = write_yaml(tmp_path / "task-0001-valid-task.yaml", valid_task_yaml())

    result = run_checker(path)

    assert result.returncode == 0
    assert result.stdout.strip() == "检查完成: files=1 errors=0 warnings=0"
    assert result.stderr == ""


def test_missing_required_field_cli_exit_one(tmp_path):
    content = valid_intent_yaml().replace("title: Valid Intent\n", "")
    path = write_yaml(tmp_path / "intent-0001-missing-title.yaml", content)

    result = run_checker(path)

    assert result.returncode == 1
    assert "MISSING_REQUIRED_FIELD" in result.stdout
    assert "title" in result.stdout
    assert "检查完成: files=1 errors=1 warnings=0" in result.stdout


def test_invalid_status_cli_exit_one(tmp_path):
    content = valid_task_yaml().replace("status: planned", "status: unknown")
    path = write_yaml(tmp_path / "task-0001-invalid-status.yaml", content)

    result = run_checker(path)

    assert result.returncode == 1
    assert "INVALID_STATUS" in result.stdout
    assert "检查完成: files=1 errors=1 warnings=0" in result.stdout


def test_type_mismatch_cli_exit_one(tmp_path):
    content = valid_intent_yaml().replace("type: intent", "type: wrong")
    path = write_yaml(tmp_path / "intent-0001-type-mismatch.yaml", content)

    result = run_checker(path)

    assert result.returncode == 1
    assert "INVALID_TYPE" in result.stdout
    assert "type 必须是 intent" in result.stdout
    assert "检查完成: files=1 errors=1 warnings=0" in result.stdout


def test_list_type_mismatch_cli_exit_one(tmp_path):
    content = valid_task_yaml().replace("related_adrs: []", "related_adrs: adr-0001")
    path = write_yaml(tmp_path / "task-0001-list-type-mismatch.yaml", content)

    result = run_checker(path)

    assert result.returncode == 1
    assert "INVALID_LIST_FIELD" in result.stdout
    assert "related_adrs" in result.stdout
    assert "检查完成: files=1 errors=1 warnings=0" in result.stdout


def test_blocked_by_not_closed_cli_exit_one(tmp_path):
    write_yaml(tmp_path / "task-0001-blocker.yaml", valid_task_yaml())
    blocked = valid_task_yaml(status="executing").replace("id: task-0001", "id: task-0002")
    blocked = blocked.replace("blocked_by: []", "blocked_by:\n  - task-0001")
    write_yaml(tmp_path / "task-0002-blocked.yaml", blocked)

    result = run_checker(tmp_path)

    assert result.returncode == 1
    assert "BLOCKED_BY_NOT_CLOSED" in result.stdout
    assert "task-0001" in result.stdout


def test_blocked_by_closed_cli_exit_zero(tmp_path):
    blocker = valid_task_yaml(status="closed", extra='closure_evidence: |\n  ## 验证结果\n\n  done\nclosed_at: "2026-06-03"')
    write_yaml(tmp_path / "task-0001-blocker.yaml", blocker)
    blocked = valid_task_yaml(status="executing").replace("id: task-0001", "id: task-0002")
    blocked = blocked.replace("blocked_by: []", "blocked_by:\n  - task-0001")
    write_yaml(tmp_path / "task-0002-blocked.yaml", blocked)

    result = run_checker(tmp_path)

    assert result.returncode == 0
    assert "检查完成: files=2 errors=0 warnings=0" in result.stdout


def test_invalid_filename_cli_exit_one(tmp_path):
    path = write_yaml(tmp_path / "bad-intent-name.yaml", valid_intent_yaml())

    result = run_checker(path)

    assert result.returncode == 1
    assert "INVALID_FILENAME" in result.stdout
    assert "检查完成: files=1 errors=1 warnings=0" in result.stdout


def test_nonexistent_path_cli_exit_two(tmp_path):
    path = tmp_path / "missing.yaml"

    result = run_checker(path)

    assert result.returncode == 2
    assert "INPUT_PATH_MISSING" in result.stdout
    assert "检查完成: files=0 errors=1 warnings=0" in result.stdout


def test_yaml_parse_failure_cli_exit_two(tmp_path):
    path = write_yaml(tmp_path / "intent-0001-broken-yaml.yaml", "title: [unterminated")

    result = run_checker(path)

    assert result.returncode == 2
    assert "YAML_PARSE_ERROR" in result.stdout
    assert "YAML 块标量" in result.stdout
    assert "检查完成: files=1 errors=1 warnings=0" in result.stdout


def test_unrecognized_object_type_cli_exit_two(tmp_path):
    path = write_yaml(
        tmp_path / "unknown-0001-object.yaml",
        """
id: unknown-0001
type: unknown
title: Unknown Object
status: active
""",
    )

    result = run_checker(path)

    assert result.returncode == 2
    assert "UNKNOWN_OBJECT_TYPE" in result.stdout
    assert "检查完成: files=1 errors=1 warnings=0" in result.stdout


def test_directory_batch_validation_summary(tmp_path):
    batch_dir = tmp_path / "facts"
    nested_dir = batch_dir / "nested"
    nested_dir.mkdir(parents=True)
    write_yaml(batch_dir / "intent-0001-valid-intent.yaml", valid_intent_yaml())
    write_yaml(batch_dir / "task-0001-valid-task.yaml", valid_task_yaml())
    write_yaml(nested_dir / "memo-0001-valid-memo.yaml", valid_memo_yaml())
    invalid = valid_task_yaml().replace("status: planned", "status: invalid")
    write_yaml(nested_dir / "task-0001-invalid-status.yaml", invalid)
    (batch_dir / "ignored.yml").write_text("not: scanned\n", encoding="utf-8")

    result = run_checker(batch_dir)

    assert result.returncode == 1
    assert "INVALID_STATUS" in result.stdout
    assert "ignored.yml" not in result.stdout
    assert "检查完成: files=4 errors=1 warnings=0" in result.stdout


def test_valid_profile_cli_exit_zero(tmp_path):
    project_root = prepare_profile_project(tmp_path)
    path = write_yaml(tmp_path / "profile-0001-valid-profile.yaml", valid_profile_yaml(project_root))

    result = run_checker(path)

    assert result.returncode == 0
    assert result.stdout.strip() == "检查完成: files=1 errors=0 warnings=0"
    assert result.stderr == ""


def test_valid_pitfall_cli_exit_zero(tmp_path):
    path = write_yaml(tmp_path / "pitfall-0001-valid-pitfall.yaml", valid_pitfall_yaml())

    result = run_checker(path)

    assert result.returncode == 0
    assert result.stdout.strip() == "检查完成: files=1 errors=0 warnings=0"
    assert result.stderr == ""


def test_valid_memo_cli_exit_zero(tmp_path):
    path = write_yaml(tmp_path / "memo-0001-valid-memo.yaml", valid_memo_yaml())

    result = run_checker(path)

    assert result.returncode == 0
    assert result.stdout.strip() == "检查完成: files=1 errors=0 warnings=0"
    assert result.stderr == ""


def test_valid_adr_cli_exit_zero(tmp_path):
    path = write_yaml(tmp_path / "adr-0001-valid-adr.yaml", valid_adr_yaml())

    result = run_checker(path)

    assert result.returncode == 0
    assert result.stdout.strip() == "检查完成: files=1 errors=0 warnings=0"
    assert result.stderr == ""


def test_rejected_adr_cli_exit_zero(tmp_path):
    path = write_yaml(tmp_path / "adr-0001-rejected-adr.yaml", valid_adr_yaml(status="rejected"))

    result = run_checker(path)

    assert result.returncode == 0
    assert result.stdout.strip() == "检查完成: files=1 errors=0 warnings=0"
    assert result.stderr == ""


def test_change_file_rejected_by_validator(tmp_path):
    """Change YAML 不再被事实验证器支持。Change 使用 Git commit 作为事实源。"""
    path = write_yaml(tmp_path / "change-0001-valid-change.yaml", valid_change_yaml())

    result = run_checker(path)

    assert result.returncode != 0
    assert "UNKNOWN_OBJECT_TYPE" in result.stdout


def test_memo_invalid_category(tmp_path):
    content = valid_memo_yaml().replace("category: gap", "category: invalid")
    path = write_yaml(tmp_path / "memo-0001-invalid-category.yaml", content)

    result = run_checker(path)

    assert result.returncode == 1
    assert "INVALID_CATEGORY" in result.stdout


def test_memo_resolved_missing_resolved_fields(tmp_path):
    content = valid_memo_yaml(status="resolved")
    path = write_yaml(tmp_path / "memo-0001-resolved-no-fields.yaml", content)

    result = run_checker(path)

    assert result.returncode == 1
    assert "MISSING_RESOLVED_FIELD" in result.stdout
    assert "resolved_to" in result.stdout
    assert "resolved_at" in result.stdout


def test_memo_invalid_priority_warning(tmp_path):
    content = valid_memo_yaml().replace("category: gap", "category: gap\npriority: urgent")
    path = write_yaml(tmp_path / "memo-0001-invalid-priority.yaml", content)

    result = run_checker(path)

    assert result.returncode == 0
    assert "INVALID_PRIORITY" in result.stdout
    assert "检查完成: files=1 errors=0 warnings=1" in result.stdout


def test_profile_invalid_status(tmp_path):
    project_root = prepare_profile_project(tmp_path)
    content = valid_profile_yaml(project_root).replace("status: active", "status: unknown")
    path = write_yaml(tmp_path / "profile-0001-invalid-status.yaml", content)

    result = run_checker(path)

    assert result.returncode == 1
    assert "INVALID_STATUS" in result.stdout


def test_profile_project_kind_required_and_valid(tmp_path):
    project_root = prepare_profile_project(tmp_path)
    content = valid_profile_yaml(project_root).replace("project_kind: governed_project", "project_kind: personal")
    path = write_yaml(tmp_path / "profile-0001-invalid-kind.yaml", content)

    result = run_checker(path)

    assert result.returncode == 1
    assert "INVALID_PROJECT_KIND" in result.stdout


def test_active_profile_requires_environment_record(tmp_path):
    project_root = prepare_profile_project(tmp_path)
    content = valid_profile_yaml(project_root).replace(
        f"environment_record_path: {project_root / 'LDVH-ENVIRONMENT-INITIALIZATION.md'}\n",
        "",
    )
    path = write_yaml(tmp_path / "profile-0001-missing-env-record.yaml", content)

    result = run_checker(path)

    assert result.returncode == 1
    assert "MISSING_ACTIVE_PROFILE_PATH" in result.stdout
    assert "environment_record_path" in result.stdout


def test_profile_environment_record_must_use_expected_filename(tmp_path):
    project_root = prepare_profile_project(tmp_path)
    wrong_record = project_root / "ENV.md"
    wrong_record.write_text("# Wrong\n", encoding="utf-8")
    content = valid_profile_yaml(project_root).replace(
        str(project_root / "LDVH-ENVIRONMENT-INITIALIZATION.md"),
        str(wrong_record),
    )
    path = write_yaml(tmp_path / "profile-0001-wrong-env-record.yaml", content)

    result = run_checker(path)

    assert result.returncode == 1
    assert "INVALID_ENVIRONMENT_RECORD_PATH" in result.stdout


def test_pitfall_invalid_repeatability(tmp_path):
    content = valid_pitfall_yaml().replace("repeatability: recurring", "repeatability: always")
    path = write_yaml(tmp_path / "pitfall-0001-invalid-repeatability.yaml", content)

    result = run_checker(path)

    assert result.returncode == 1
    assert "INVALID_REPEATABILITY" in result.stdout


def test_pitfall_superseded_requires_target(tmp_path):
    path = write_yaml(tmp_path / "pitfall-0001-superseded.yaml", valid_pitfall_yaml(status="superseded"))

    result = run_checker(path)

    assert result.returncode == 1
    assert "MISSING_SUPERSEDED_BY" in result.stdout


def test_pitfall_archived_requires_reason_when_not_superseded(tmp_path):
    path = write_yaml(tmp_path / "pitfall-0001-archived.yaml", valid_pitfall_yaml(status="archived"))

    result = run_checker(path)

    assert result.returncode == 1
    assert "MISSING_ARCHIVE_REASON" in result.stdout


def test_json_output_valid(tmp_path):
    path = write_yaml(tmp_path / "intent-0001-valid-intent.yaml", valid_intent_yaml())

    result = run_checker(path, extra_args=["--format", "json"])

    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["ok"] is True
    assert data["command"] == "fact_validate"
    assert data["action"] == "validate"
    assert data["summary"]["files"] == 1
    assert data["summary"]["errors"] == 0
    assert data["summary"]["warnings"] == 0
    assert data["issues"] == []
    assert data["data"] == {}


def test_json_output_with_errors(tmp_path):
    content = valid_task_yaml().replace("status: planned", "status: unknown")
    path = write_yaml(tmp_path / "task-0001-invalid-status.yaml", content)

    result = run_checker(path, extra_args=["--format", "json"])

    assert result.returncode == 1
    data = json.loads(result.stdout)
    assert data["ok"] is False
    assert data["summary"]["errors"] == 1
    assert len(data["issues"]) == 1
    issue = data["issues"][0]
    assert issue["code"] == "INVALID_STATUS"
    assert issue["level"] == "error"
    assert "path" in issue
    assert "message" in issue


def test_text_output_backward_compatible(tmp_path):
    path = write_yaml(tmp_path / "intent-0001-valid-intent.yaml", valid_intent_yaml())

    result_default = run_checker(path)
    result_explicit = run_checker(path, extra_args=["--format", "text"])

    assert result_default.returncode == 0
    assert result_explicit.returncode == 0
    assert result_default.stdout == result_explicit.stdout
    assert "检查完成: files=1 errors=0 warnings=0" in result_default.stdout
