import json
from .common import checker
from spec_checks import web_validate as web_validate_checks
from .test_ldvh_assurance import build_ldvh_assurance_check_fixture

# ── web-validate 子命令测试 ──────────────────────────────────────


def test_web_validate_core_implementation_lives_in_spec_checks():
    assert checker.web_validate_checks is web_validate_checks
    assert web_validate_checks.web_validate_build.__module__ == "spec_checks.web_validate"
    assert web_validate_checks.web_validate_main.__module__ == "spec_checks.web_validate"


def test_web_validate_build_returns_dict():
    """web_validate_build 应返回包含必要字段的字典"""
    report = checker.web_validate_build()

    assert isinstance(report, dict)
    assert "ok" in report
    assert "command" in report
    assert "summary" in report
    assert "issues" in report
    assert "reports" in report


def test_web_validate_build_has_reports():
    """web_validate_build 的 reports 应包含 assuranceCheck、assuranceReport 和 humanGateReport"""
    report = checker.web_validate_build()

    reports = report.get("reports", {})

    assert "assuranceCheck" in reports
    assert "assuranceReport" in reports
    assert "humanGateReport" in reports


def test_web_validate_format_text():
    """web_validate_format_text 应生成可读文本"""
    report = checker.web_validate_build()
    text = checker.web_validate_format_text(report)

    assert isinstance(text, str)
    assert len(text) > 0


def test_web_validate_main_text_output(capsys):
    """web_validate_main text 模式应输出并返回 0"""
    exit_code = checker.web_validate_main(output_format="text")

    captured = capsys.readouterr()
    assert exit_code in (0, 1)  # 取决于事实模型是否有错误
    assert captured.out != ""


def test_web_validate_main_json_output(capsys):
    """web_validate_main json 模式应输出合法 JSON"""
    exit_code = checker.web_validate_main(output_format="json")

    captured = capsys.readouterr()
    report = json.loads(captured.out)  # 不应抛异常

    assert "ok" in report
    assert "summary" in report


# ══════════════════════════════════════════════════════════════════════
# web-validate — Web Validate 页面只读数据合同
# ══════════════════════════════════════════════════════════════════════

def test_web_validate_builds_web_contract_from_code(tmp_path, monkeypatch):
    build_ldvh_assurance_check_fixture(tmp_path, monkeypatch)

    report = checker.web_validate_build(str(tmp_path))

    assert report["command"] == "web_validate"
    assert report["action"] == "validate"
    assert report["target"] == "ldvh-base"
    assert report["summary"]["files"] == 1
    assert report["summary"]["errors"] == 0
    assert "assuranceCheck" in report["reports"]
    assert "assuranceReport" in report["reports"]
    assert "humanGateReport" in report["reports"]
    assert report["reports"]["assuranceCheck"]["summary"]["status"] == "open"
    assert report["reports"]["assuranceReport"]["summary"]["gap_total"] >= 1
    assert report["reports"]["humanGateReport"]["metadata"]["record_count"] == 0


def test_web_validate_cli_outputs_json_without_failing_on_open_status(tmp_path, monkeypatch, capsys):
    build_ldvh_assurance_check_fixture(tmp_path, monkeypatch)

    exit_code = checker.main(["web-validate", "--workspace-root", str(tmp_path), "--format", "json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "web_validate"
    assert payload["reports"]["assuranceCheck"]["summary"]["status"] == "open"
