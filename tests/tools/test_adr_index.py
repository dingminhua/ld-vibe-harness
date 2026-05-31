from datetime import datetime
import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[2] / "tools" / "adr_index.py"
spec = importlib.util.spec_from_file_location("adr_index", MODULE_PATH)
adr_index = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adr_index)


def write_adr(path, **overrides):
    data = {
        "id": "adr-0001",
        "type": "adr",
        "title": "测试 ADR",
        "status": "accepted",
        "created": "2026-06-01",
        "updated": "2026-06-01",
        "date": "2026-06-01",
        "context": "测试背景",
        "decision": "测试决策",
        "consequences": "测试影响",
        "affects": ["specs/12.01-Tools辅助规范.md"],
        "related_rules": ["specs/21.06-Contract.md"],
    }
    data.update(overrides)
    lines = []
    for key, value in data.items():
        if isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"  - {item}")
        else:
            lines.append(f"{key}: {value}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_fmt_date_handles_datetime_and_empty_values():
    assert adr_index.fmt_date(datetime(2026, 6, 1)) == "2026-06-01"
    assert adr_index.fmt_date(None) == "N/A"
    assert adr_index.fmt_date("2026-06-01") == "2026-06-01"


def test_load_adr_reads_yaml_and_attaches_source_path(tmp_path):
    path = tmp_path / "adr-0001-test.yaml"
    write_adr(path)

    adr = adr_index.load_adr(path)

    assert adr["id"] == "adr-0001"
    assert adr["_file"] == "adr-0001-test.yaml"
    assert adr["_path"] == str(path)


def test_load_adr_returns_none_for_empty_yaml(tmp_path):
    path = tmp_path / "adr-0001-empty.yaml"
    path.write_text("", encoding="utf-8")

    assert adr_index.load_adr(path) is None


def test_load_all_adrs_reads_only_adr_yaml_files(tmp_path, monkeypatch):
    write_adr(tmp_path / "adr-0002-second.yaml", id="adr-0002", title="第二个 ADR")
    write_adr(tmp_path / "adr-0001-first.yaml", id="adr-0001", title="第一个 ADR")
    write_adr(tmp_path / "memo-0001.yaml", id="memo-0001", title="不应读取")
    monkeypatch.setattr(adr_index, "ADRS_DIR", tmp_path)

    adrs = adr_index.load_all_adrs()

    assert [adr["id"] for adr in adrs] == ["adr-0001", "adr-0002"]


def test_cmd_search_matches_decision_text(capsys):
    adrs = [
        {"id": "adr-0001", "title": "标题", "status": "accepted", "decision": "采用 pytest", "created": "2026-06-01"}
    ]

    adr_index.cmd_search(adrs, "pytest")

    output = capsys.readouterr().out
    assert "找到 1 个匹配的 ADR" in output
    assert "adr-0001" in output


def test_cmd_related_matches_affects_and_related_rules(capsys):
    adrs = [
        {
            "id": "adr-0001",
            "title": "标题",
            "status": "accepted",
            "created": "2026-06-01",
            "affects": ["specs/12.01-Tools辅助规范.md"],
            "related_rules": [],
        },
        {
            "id": "adr-0002",
            "title": "标题",
            "status": "accepted",
            "created": "2026-06-01",
            "affects": [],
            "related_rules": ["specs/21.06-Contract.md"],
        },
    ]

    adr_index.cmd_related(adrs, "21.06")

    output = capsys.readouterr().out
    assert "共 1 个" in output
    assert "adr-0002" in output
    assert "adr-0001" not in output


def test_cmd_validate_accepts_valid_adr(capsys):
    adrs = [
        {
            "_file": "adr-0001-test.yaml",
            "id": "adr-0001",
            "type": "adr",
            "title": "测试 ADR",
            "status": "accepted",
            "created": "2026-06-01",
            "updated": "2026-06-01",
            "date": "2026-06-01",
            "context": "测试背景",
            "decision": "测试决策",
            "consequences": "测试影响",
        }
    ]

    adr_index.cmd_validate(adrs)

    output = capsys.readouterr().out
    assert "校验结果: 通过 1，不合规 0" in output


def test_cmd_validate_reports_missing_field_invalid_status_and_superseded_target(capsys):
    adrs = [
        {
            "_file": "invalid.yaml",
            "id": "adr-0001",
            "type": "adr",
            "title": "测试 ADR",
            "status": "invalid",
            "created": "2026-06-01",
            "updated": "2026-06-01",
            "date": "2026-06-01",
            "context": "测试背景",
            "decision": "测试决策",
        },
        {
            "_file": "adr-0002-test.yaml",
            "id": "adr-0002",
            "type": "adr",
            "title": "测试 ADR",
            "status": "superseded",
            "created": "2026-06-01",
            "updated": "2026-06-01",
            "date": "2026-06-01",
            "context": "测试背景",
            "decision": "测试决策",
            "consequences": "测试影响",
        },
    ]

    adr_index.cmd_validate(adrs)

    output = capsys.readouterr().out
    assert "必填字段缺失: consequences" in output
    assert "状态不合法: invalid" in output
    assert "文件命名不匹配" in output
    assert "状态为 superseded 时 superseded_by 为必填" in output
    assert "校验结果: 通过 0，不合规 2" in output
