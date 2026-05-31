from datetime import datetime
import importlib.util
from pathlib import Path

import pytest
import yaml


MODULE_PATH = Path(__file__).resolve().parents[2] / "tools" / "adr_index.py"
spec = importlib.util.spec_from_file_location("adr_index", MODULE_PATH)
adr_index = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adr_index)


class Args:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def auth_args(**overrides):
    data = {
        "human_gate_confirmed": True,
        "confirmed_by": "user",
        "confirmation_context": "测试 Human Gate 确认",
        "write_change": False,
    }
    data.update(overrides)
    return data


def adr_content(**overrides):
    data = {
        "id": None,
        "slug": "test-adr",
        "title": "测试 ADR",
        "context": "测试背景",
        "decision": "测试决策",
        "consequences": "测试影响",
        "date": "2026-06-01",
        "alternatives": None,
        "affects": None,
        "related_objects": None,
        "related_rules": None,
    }
    data.update(overrides)
    return data


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
        "related_objects": [],
        "related_rules": ["specs/21.06-Contract.md"],
    }
    data.update(overrides)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def read_yaml(path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


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


def test_next_adr_id_uses_highest_existing_number():
    adrs = [{"id": "adr-0001"}, {"id": "adr-0009"}, {"id": "memo-0001"}]

    assert adr_index.next_adr_id(adrs) == "adr-0010"


def test_cmd_draft_outputs_valid_proposed_yaml(capsys):
    args = Args(**adr_content(affects=["specs/21-ADR-决策记录.md"], related_rules=["specs/21.06-Contract.md"]))

    adr_index.cmd_draft(args, [])

    data = yaml.safe_load(capsys.readouterr().out)
    assert data["id"] == "adr-0001"
    assert data["status"] == "proposed"
    assert data["affects"] == ["specs/21-ADR-决策记录.md"]


def test_create_requires_human_gate_authorization(tmp_path, monkeypatch):
    monkeypatch.setattr(adr_index, "ADRS_DIR", tmp_path)
    args = Args(**adr_content(), human_gate_confirmed=False, confirmed_by="user", confirmation_context="确认", write_change=False)

    with pytest.raises(adr_index.ToolError, match="缺少 --human-gate-confirmed"):
        adr_index.cmd_create(args, [])

    assert not list(tmp_path.glob("*.yaml"))


def test_create_writes_proposed_adr_and_change_record(tmp_path, monkeypatch):
    adrs_dir = tmp_path / "adrs"
    changes_dir = tmp_path / "changes"
    monkeypatch.setattr(adr_index, "ADRS_DIR", adrs_dir)
    monkeypatch.setattr(adr_index, "CHANGES_DIR", changes_dir)
    args = Args(**adr_content(related_rules=["specs/21.06-Contract.md"]), **auth_args(write_change=True))

    adr_index.cmd_create(args, [])

    path = adrs_dir / "adr-0001-test-adr.yaml"
    data = read_yaml(path)
    assert data["status"] == "proposed"
    assert data["related_rules"] == ["specs/21.06-Contract.md"]
    change_files = list(changes_dir.glob("*.yaml"))
    assert len(change_files) == 1
    assert read_yaml(change_files[0])["human_gate"]["confirmed_by"] == "user"


def test_transition_rejects_illegal_status_change(tmp_path, monkeypatch):
    path = tmp_path / "adr-0001-test.yaml"
    write_adr(path, status="proposed")
    monkeypatch.setattr(adr_index, "ADRS_DIR", tmp_path)
    adrs = adr_index.load_all_adrs()
    args = Args(adr_id="adr-0001", status="deprecated", superseded_by=None, **auth_args())

    with pytest.raises(adr_index.ToolError, match="非法"):
        adr_index.cmd_transition(args, adrs)

    assert read_yaml(path)["status"] == "proposed"


def test_transition_accepts_proposed_to_accepted(tmp_path, monkeypatch):
    path = tmp_path / "adr-0001-test.yaml"
    write_adr(path, status="proposed")
    monkeypatch.setattr(adr_index, "ADRS_DIR", tmp_path)
    adrs = adr_index.load_all_adrs()
    args = Args(adr_id="adr-0001", status="accepted", superseded_by=None, **auth_args())

    adr_index.cmd_transition(args, adrs)

    assert read_yaml(path)["status"] == "accepted"


def test_link_rule_appends_unique_rule(tmp_path, monkeypatch):
    path = tmp_path / "adr-0001-test.yaml"
    write_adr(path, related_rules=[])
    monkeypatch.setattr(adr_index, "ADRS_DIR", tmp_path)
    adrs = adr_index.load_all_adrs()
    args = Args(adr_id="adr-0001", rule=["specs/21.04-Tools.md"], **auth_args())

    adr_index.cmd_link_rule(args, adrs)

    assert read_yaml(path)["related_rules"] == ["specs/21.04-Tools.md"]


def test_deprecate_updates_status_and_reason(tmp_path, monkeypatch):
    path = tmp_path / "adr-0001-test.yaml"
    write_adr(path, status="accepted", consequences="原影响")
    monkeypatch.setattr(adr_index, "ADRS_DIR", tmp_path)
    adrs = adr_index.load_all_adrs()
    args = Args(adr_id="adr-0001", reason="已不适用", reason_field="consequences", **auth_args())

    adr_index.cmd_deprecate(args, adrs)

    data = read_yaml(path)
    assert data["status"] == "deprecated"
    assert "废弃原因：已不适用" in data["consequences"]


def test_supersede_creates_new_adr_and_updates_old(tmp_path, monkeypatch):
    old_path = tmp_path / "adr-0001-old.yaml"
    write_adr(old_path, id="adr-0001", status="accepted", title="旧 ADR")
    monkeypatch.setattr(adr_index, "ADRS_DIR", tmp_path)
    adrs = adr_index.load_all_adrs()
    args = Args(old_adr_id="adr-0001", **adr_content(slug="new-adr", title="新 ADR"), **auth_args())

    adr_index.cmd_supersede(args, adrs)

    old_data = read_yaml(old_path)
    new_data = read_yaml(tmp_path / "adr-0002-new-adr.yaml")
    assert old_data["status"] == "superseded"
    assert old_data["superseded_by"] == "adr-0002"
    assert new_data["status"] == "proposed"
    assert "adr-0001" in new_data["related_objects"]
