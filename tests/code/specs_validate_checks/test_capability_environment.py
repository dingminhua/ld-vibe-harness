import json
import subprocess
import sys
from pathlib import Path

from .common import checker
from .test_deployment_entries import DEPLOYMENT_REGISTRY_PATH, write_deployment_entries_fixture
from spec_checks import capability_environment as capability_environment_checks


PROJECT_ROOT = Path(__file__).resolve().parents[3]


def test_capability_environment_core_implementation_lives_in_spec_checks():
    assert checker.capability_environment_checks is capability_environment_checks
    assert capability_environment_checks.capability_environment_report_build.__module__ == "spec_checks.capability_environment"
    assert capability_environment_checks.capability_environment_main.__module__ == "spec_checks.capability_environment"


def test_capability_environment_matrix_links_assets_to_environment_without_install_claim(tmp_path):
    write_deployment_entries_fixture(tmp_path)

    report = checker.capability_environment_report_build(tmp_path)

    assert report["summary"]["status"] == "closed"
    assert report["summary"]["asset_count"] == 4
    assert report["summary"]["environment_installation_status"] == "not_claimed"
    assert report["environment_targets"][0]["name"] == "Codex App"
    workspace_entry = next(item for item in report["matrix"] if item["asset"]["id"] == "ldvh-workspace-entry")
    assert workspace_entry["environment_landing"]["installation_status"] == "not_claimed"
    assert workspace_entry["environment_landing"]["human_gate_required_for_environment_write"] is True
    assert workspace_entry["responsibility_chain"]["environment_owner"] == "Human or target environment owner authorizes local entry writes and installation"


def test_capability_environment_reports_missing_source_spec(tmp_path):
    write_deployment_entries_fixture(tmp_path)
    asset_path = tmp_path / "rules" / "LDVH-WORKSPACE-ENTRY.md"
    text = asset_path.read_text(encoding="utf-8")
    asset_path.write_text(text.replace(DEPLOYMENT_REGISTRY_PATH, "specs/missing.md", 1), encoding="utf-8")

    report = checker.capability_environment_report_build(tmp_path)

    assert report["summary"]["status"] == "open"
    assert "CAPABILITY_ENVIRONMENT_SOURCE_SPEC_MISSING" in report["summary"]["by_code"]


def test_capability_environment_cli_outputs_json(tmp_path, capsys):
    write_deployment_entries_fixture(tmp_path)

    exit_code = checker.main(["capability-environment", "--root", str(tmp_path), "--format", "json"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["metadata"]["report"] == "capability-environment"
    assert payload["summary"]["environment_installation_status"] == "not_claimed"


def test_capability_environment_script_fast_path_outputs_text(tmp_path):
    write_deployment_entries_fixture(tmp_path)

    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "code" / "specs_validate.py"),
            "capability-environment",
            "--root",
            str(tmp_path),
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert "能力资产与环境保障矩阵" in result.stdout
    assert "not_claimed" in result.stdout
    assert result.stderr == ""
