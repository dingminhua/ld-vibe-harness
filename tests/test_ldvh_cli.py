import importlib.util
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PROJECT_ROOT / "tools" / "ldvh_cli.py"
sys.path.insert(0, str(PROJECT_ROOT / "tools"))
spec = importlib.util.spec_from_file_location("ldvh_cli", MODULE_PATH)
ldvh_cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ldvh_cli)


def test_help_lists_minimal_command_tree(capsys):
    exit_code = ldvh_cli.main(["--help"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "status" in output
    assert "landing" in output
    assert "facts" in output
    assert "specs" in output


def test_status_outputs_stable_json_contract(capsys):
    exit_code = ldvh_cli.main(["status", "--format", "json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["metadata"]["contract_version"] == "ldvh-cli/v1"
    assert payload["summary"]["status"] == "ready"
    assert "landing plan" in payload["commands"]
    assert "facts list/show/search/stats" in payload["commands"]
    assert "facts validate" in payload["commands"]
    assert "specs validate" in payload["commands"]


def test_landing_plan_delegates_to_specs_validate(monkeypatch):
    called = {}

    def fake_landing_plan_main(workspace_root, output_format):
        called["workspace_root"] = workspace_root
        called["format"] = output_format
        return 0

    monkeypatch.setattr(ldvh_cli.specs_validate, "landing_plan_main", fake_landing_plan_main)

    exit_code = ldvh_cli.main(["landing", "plan", "--workspace-root", "/tmp/ldvh", "--format", "json"])

    assert exit_code == 0
    assert called == {"workspace_root": "/tmp/ldvh", "format": "json"}


def test_facts_validate_returns_wrapped_failure_code(tmp_path, capsys):
    missing_path = tmp_path / "missing"

    exit_code = ldvh_cli.main(["facts", "validate", str(missing_path), "--format", "json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 2
    assert payload["command"] == "fact_validate"
    assert payload["issues"][0]["code"] == "INPUT_PATH_MISSING"


def test_landing_apply_requires_plan_boundary_before_delegation(capsys):
    exit_code = ldvh_cli.main(["landing", "apply", "--patch", "patch.json", "--write"])

    output = capsys.readouterr().err
    assert exit_code == 2
    assert "--plan" in output
