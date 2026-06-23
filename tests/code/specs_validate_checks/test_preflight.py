import json
import subprocess
import sys
from pathlib import Path

from .common import checker, write_md


PROJECT_ROOT = Path(__file__).resolve().parents[3]


def test_preflight_existing_spec_update_requires_human_gate_but_does_not_authorize_write(tmp_path):
    write_md(tmp_path / "specs" / "04-Code确定性执行规范.md", "# Code\n")

    report = checker.preflight_build(tmp_path, "specs/04-Code确定性执行规范.md", operation="update")
    codes = {item["code"] for item in report["diagnostics"]}

    assert report["metadata"]["read_only"] is True
    assert report["metadata"]["write_authorized"] is False
    assert report["input"]["asset_type"] == "specs"
    assert report["summary"]["status"] == "needs_human_gate"
    assert "PREFLIGHT_HUMAN_GATE_REQUIRED" in codes
    assert "PREFLIGHT_GIT_TRACE_REQUIRED" in codes
    assert "PREFLIGHT_SYNC_IMPACT_REVIEW_REQUIRED" in codes
    assert not any(item["severity"] == "error" for item in report["diagnostics"])


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
