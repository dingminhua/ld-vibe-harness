import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = PROJECT_ROOT / "tools" / "check_fact_model.py"


def run_checker(*paths):
    return subprocess.run(
        ["python3", str(SCRIPT_PATH), *[str(path) for path in paths]],
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
related_evidence: []
related_changes: []
{extra}
"""


def valid_evidence_yaml():
    return """
id: ev-0001
type: evidence
title: Valid Evidence
status: verified
created: "2026-06-03"
updated: "2026-06-03"
evidence_type: verification
verification_method: pytest
verification_result: pass
content: Validator accepts this evidence
source_task: task-0001
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


def test_valid_evidence_cli_exit_zero(tmp_path):
    path = write_yaml(tmp_path / "ev-0001-valid-evidence.yaml", valid_evidence_yaml())

    result = run_checker(path)

    assert result.returncode == 0
    assert result.stdout.strip() == "检查完成: files=1 errors=0 warnings=0"
    assert result.stderr == ""


def test_valid_evidence_block_scalar_with_colon_cli_exit_zero(tmp_path):
    content = valid_evidence_yaml().replace(
        "content: Validator accepts this evidence",
        "content: |\n  Validator accepts long text with colon: pass\n  command: python3 tools/check_fact_model.py",
    )
    path = write_yaml(tmp_path / "ev-0001-valid-evidence.yaml", content)

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
    content = valid_task_yaml().replace("related_evidence: []", "related_evidence: ev-0001")
    path = write_yaml(tmp_path / "task-0001-list-type-mismatch.yaml", content)

    result = run_checker(path)

    assert result.returncode == 1
    assert "INVALID_LIST_FIELD" in result.stdout
    assert "related_evidence" in result.stdout
    assert "检查完成: files=1 errors=1 warnings=0" in result.stdout


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
    write_yaml(nested_dir / "ev-0001-valid-evidence.yaml", valid_evidence_yaml())
    invalid = valid_task_yaml().replace("status: planned", "status: invalid")
    write_yaml(nested_dir / "task-0001-invalid-status.yaml", invalid)
    (batch_dir / "ignored.yml").write_text("not: scanned\n", encoding="utf-8")

    result = run_checker(batch_dir)

    assert result.returncode == 1
    assert "INVALID_STATUS" in result.stdout
    assert "ignored.yml" not in result.stdout
    assert "检查完成: files=4 errors=1 warnings=0" in result.stdout
