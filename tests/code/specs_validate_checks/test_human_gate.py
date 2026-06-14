import json
from .common import checker, write_md

# ══════════════════════════════════════════════════════════════════════
# human-gate — Human Gate 轻量人类决策记录结构检查
# ══════════════════════════════════════════════════════════════════════

def human_gate_codes(issues):
    return [issue.code for issue in issues]


def test_human_gate_complete_record_passes(tmp_path):
    path = write_md(
        tmp_path / "gate.md",
        """
# Gate

Human Gate 记录：
- 时间：2026-06-10
- 决策：确认推进
- 范围：specs/41、docs/studies/18
- 约束：验证命令通过，剩余 Web 消费未实现，后续写回评估
""",
    )

    assert checker.human_gate_check_file(path) == []


def test_human_gate_missing_fields_are_reported(tmp_path):
    path = write_md(
        tmp_path / "gate-missing.md",
        """
# Gate

Human Gate 记录：
- Human 决策：用户同意
""",
    )

    issues = checker.human_gate_check_file(path)

    assert "HUMAN_GATE_FIELD_MISSING" in human_gate_codes(issues)
    assert any("时间" in issue.message for issue in issues)
    assert any("范围" in issue.message for issue in issues)


def test_human_gate_empty_field_is_reported(tmp_path):
    path = write_md(
        tmp_path / "gate-empty.md",
        """
# Gate

Human Gate 记录：
- 时间：
- 决策：是否关闭
- 范围：docs
- 约束：人工确认
""",
    )

    issues = checker.human_gate_check_file(path)

    assert "HUMAN_GATE_FIELD_EMPTY" in human_gate_codes(issues)
    assert any("时间" in issue.message for issue in issues)


def test_human_gate_continuation_satisfies_field_value(tmp_path):
    path = write_md(
        tmp_path / "gate-continuation.md",
        """
# Gate

Human Gate 记录：
- 时间：
  2026-06-10
- 决策：暂缓
- 范围：Task 和 docs/studies/18
- 约束：测试通过，后续仍需 Web
""",
    )

    assert checker.human_gate_check_file(path) == []


def test_human_gate_template_in_code_block_is_ignored(tmp_path):
    path = write_md(
        tmp_path / "gate-template.md",
        """
# Gate

```text
Human Gate 记录：
- 时间：
- 决策：
```
""",
    )

    assert checker.human_gate_check_file(path) == []


def test_human_gate_cli_reports_issues(tmp_path, capsys):
    path = write_md(
        tmp_path / "gate-cli.md",
        """
# Gate

Human Gate 记录：
- Human 决策：确认
""",
    )

    exit_code = checker.main(["human-gate", str(path)])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Human Gate 轻量人类决策记录结构检查失败" in output
    assert "HUMAN_GATE_FIELD_MISSING" in output


def test_human_gate_report_degraded_when_no_records(tmp_path, monkeypatch):
    monkeypatch.setattr(checker, "PROJECT_ROOT", tmp_path)
    path = write_md(
        tmp_path / "notes.md",
        """
# Notes

No gate records.
""",
    )

    report = checker.human_gate_report_build([str(path)])

    assert report["summary"]["status"] == "degraded"
    assert report["metadata"]["record_count"] == 0
    assert report["metadata"]["issue_count"] == 0


def test_human_gate_report_open_when_record_incomplete(tmp_path, monkeypatch):
    monkeypatch.setattr(checker, "PROJECT_ROOT", tmp_path)
    path = write_md(
        tmp_path / "gate-incomplete.md",
        """
# Gate

Human Gate 记录：
- Human 决策：确认
""",
    )

    report = checker.human_gate_report_build([str(path)])

    assert report["summary"]["status"] == "open"
    assert report["metadata"]["record_count"] == 1
    assert report["metadata"]["issue_count"] > 0
    assert {item["status"] for item in report["issues"]} == {"open"}
    assert "HUMAN_GATE_FIELD_MISSING" in {item["code"] for item in report["issues"]}


def test_human_gate_report_closed_when_record_complete(tmp_path, monkeypatch):
    monkeypatch.setattr(checker, "PROJECT_ROOT", tmp_path)
    path = write_md(
        tmp_path / "gate-complete.md",
        """
# Gate

Human Gate 记录：
- 时间：2026-06-10
- 决策：确认推进
- 范围：specs/41、docs/studies/18
- 约束：验证命令通过，剩余 Web 消费未实现，后续写回评估
""",
    )

    report = checker.human_gate_report_build([str(path)])

    assert report["summary"]["status"] == "closed"
    assert report["metadata"]["record_count"] == 1
    assert report["issues"] == []


def test_human_gate_report_counts_multiple_markdown_records(tmp_path, monkeypatch):
    monkeypatch.setattr(checker, "PROJECT_ROOT", tmp_path)
    path = write_md(
        tmp_path / "gate-multiple.md",
        """
# Gate

Human Gate 记录：
- 时间：2026-06-10
- 决策：确认推进
- 范围：specs/41
- 约束：需要验证

Human Gate 记录：
- 时间：2026-06-11
- 决策：暂缓
- 范围：specs/42
- 约束：等待补充证据
""",
    )

    report = checker.human_gate_report_build([str(path)])

    assert report["summary"]["status"] == "closed"
    assert report["metadata"]["record_count"] == 2
    assert report["issues"] == []


def test_human_gate_report_accepts_yaml_records(tmp_path, monkeypatch):
    monkeypatch.setattr(checker, "PROJECT_ROOT", tmp_path)
    path = write_md(
        tmp_path / "gate.yaml",
        """
human_gate:
  - time: 2026-06-10
    decision: 确认推进
    scope: specs/41
    constraints: 需要验证
  - time: 2026-06-11
    decision: 暂缓
    scope: specs/42
    constraints: 等待补充证据
""",
    )

    report = checker.human_gate_report_build([str(path)])

    assert report["summary"]["status"] == "closed"
    assert report["metadata"]["record_count"] == 2
    assert report["metadata"]["scope"] == "project-local Markdown/YAML facts only"
    assert report["issues"] == []


def test_human_gate_yaml_missing_fields_are_reported(tmp_path, monkeypatch):
    monkeypatch.setattr(checker, "PROJECT_ROOT", tmp_path)
    path = write_md(
        tmp_path / "gate-incomplete.yaml",
        """
human_gates:
  - decision: 确认推进
""",
    )

    report = checker.human_gate_report_build([str(path)])

    assert report["summary"]["status"] == "open"
    assert report["metadata"]["record_count"] == 1
    assert "HUMAN_GATE_FIELD_MISSING" in {item["code"] for item in report["issues"]}


def test_human_gate_report_cli_outputs_json(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(checker, "PROJECT_ROOT", tmp_path)
    path = write_md(
        tmp_path / "gate-cli-report.md",
        """
# Gate

Human Gate 记录：
- Human 决策：确认
""",
    )

    exit_code = checker.main(["human-gate-report", str(path), "--format", "json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert payload["metadata"]["report"] == "human-gate"
    assert payload["summary"]["status"] == "open"
    assert payload["metadata"]["record_count"] == 1

