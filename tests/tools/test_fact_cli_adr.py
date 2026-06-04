"""Tests for ADR subcommands in tools/fact_cli.py: search / stats / related / link-rule / deprecate / supersede."""

from __future__ import annotations

import importlib.util
import subprocess
from datetime import datetime
from pathlib import Path

import pytest
import yaml


MODULE_PATH = Path(__file__).resolve().parents[2] / "tools" / "fact_cli.py"
spec = importlib.util.spec_from_file_location("fact_cli", MODULE_PATH)
fact_cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fact_cli)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = PROJECT_ROOT / "tools" / "fact_cli.py"


def run_cli(*args, base_dir: str | None = None):
    """Run fact_cli.py with the given arguments."""
    cmd = ["python3", str(SCRIPT_PATH)]
    if base_dir is not None:
        cmd.append(args[0])
        cmd.extend(["--base-dir", base_dir])
        cmd.extend(args[1:])
    else:
        cmd.extend(args)
    return subprocess.run(
        cmd,
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


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


# ── ADR 专属工具函数测试 ────────────────────────────────────────────────


def test_parse_list_values_handles_none_and_comma_separated():
    assert fact_cli._parse_list_values(None) == []
    assert fact_cli._parse_list_values(["a,b", "c"]) == ["a", "b", "c"]


def test_ensure_authorized_rejects_missing_gate():
    args = Args(human_gate_confirmed=False, confirmed_by="user", confirmation_context="ctx")
    with pytest.raises(SystemExit):
        fact_cli._ensure_authorized(args)


def test_ensure_authorized_rejects_missing_confirmed_by():
    args = Args(human_gate_confirmed=True, confirmed_by=None, confirmation_context="ctx")
    with pytest.raises(SystemExit):
        fact_cli._ensure_authorized(args)


def test_ensure_authorized_rejects_missing_context():
    args = Args(human_gate_confirmed=True, confirmed_by="user", confirmation_context=None)
    with pytest.raises(SystemExit):
        fact_cli._ensure_authorized(args)


def test_load_all_of_type_returns_objects(tmp_path):
    adrs_dir = tmp_path / "ldvh-base" / "adrs"
    adrs_dir.mkdir(parents=True)
    write_adr(adrs_dir / "adr-0001-test.yaml")
    write_adr(adrs_dir / "adr-0002-second.yaml", id="adr-0002", title="第二个 ADR")

    objects, errors = fact_cli._load_all_of_type("adr", tmp_path)
    assert len(objects) == 2
    assert errors == []


def test_load_all_of_type_reports_parse_errors(tmp_path):
    adrs_dir = tmp_path / "ldvh-base" / "adrs"
    adrs_dir.mkdir(parents=True)
    write_adr(adrs_dir / "adr-0001-good.yaml")
    bad_path = adrs_dir / "adr-0002-bad.yaml"
    bad_path.write_text("id: adr-0002\ntype: adr\nstatus: [broken\n", encoding="utf-8")

    objects, errors = fact_cli._load_all_of_type("adr", tmp_path)
    assert len(objects) == 1
    assert len(errors) == 1


def test_find_adr_by_id_returns_matching_adr(tmp_path):
    adrs_dir = tmp_path / "ldvh-base" / "adrs"
    adrs_dir.mkdir(parents=True)
    write_adr(adrs_dir / "adr-0001-test.yaml")
    write_adr(adrs_dir / "adr-0002-second.yaml", id="adr-0002")

    adrs, _ = fact_cli._load_all_of_type("adr", tmp_path)
    found = fact_cli._find_adr_by_id(adrs, "adr-0002")
    assert found["id"] == "adr-0002"


def test_find_adr_by_id_raises_on_missing(tmp_path):
    adrs_dir = tmp_path / "ldvh-base" / "adrs"
    adrs_dir.mkdir(parents=True)
    write_adr(adrs_dir / "adr-0001-test.yaml")

    adrs, _ = fact_cli._load_all_of_type("adr", tmp_path)
    with pytest.raises(SystemExit):
        fact_cli._find_adr_by_id(adrs, "adr-9999")


def test_build_adr_data_includes_gate_record():
    args = Args(**adr_content(), **auth_args())
    now = "2026-06-01T10:00:00"
    data = fact_cli._build_adr_data("adr-0001", args, now)
    assert data["id"] == "adr-0001"
    assert data["status"] == "proposed"
    assert "Human Gate 确认记录" in data["context"]
    assert data["decision"] == "测试决策"


# ── search 子命令测试 ──────────────────────────────────────────────────


def test_search_matches_keyword(tmp_path):
    adrs_dir = tmp_path / "ldvh-base" / "adrs"
    adrs_dir.mkdir(parents=True)
    write_adr(adrs_dir / "adr-0001-test.yaml", title="采用 pytest", decision="使用 pytest 框架")

    result = run_cli("search", "pytest", base_dir=str(tmp_path))
    assert result.returncode == 0
    assert "找到 1 个匹配的对象" in result.stdout
    assert "adr-0001" in result.stdout


def test_search_no_match(tmp_path):
    result = run_cli("search", "nonexistent-keyword", base_dir=str(tmp_path))
    assert result.returncode == 0
    assert "未找到" in result.stdout


def test_search_with_type_filter(tmp_path):
    adrs_dir = tmp_path / "ldvh-base" / "adrs"
    adrs_dir.mkdir(parents=True)
    write_adr(adrs_dir / "adr-0001-test.yaml", title="采用 pytest")

    result = run_cli("search", "pytest", "--type", "adr", base_dir=str(tmp_path))
    assert result.returncode == 0
    assert "adr-0001" in result.stdout


# ── stats 子命令测试 ───────────────────────────────────────────────────


def test_stats_shows_status_distribution(tmp_path):
    adrs_dir = tmp_path / "ldvh-base" / "adrs"
    adrs_dir.mkdir(parents=True)
    write_adr(adrs_dir / "adr-0001-test.yaml", status="accepted")
    write_adr(adrs_dir / "adr-0002-second.yaml", id="adr-0002", status="proposed")

    result = run_cli("stats", "--type", "adr", base_dir=str(tmp_path))
    assert result.returncode == 0
    assert "adr 总数: 2" in result.stdout
    assert "accepted: 1" in result.stdout
    assert "proposed: 1" in result.stdout


def test_stats_empty_directory(tmp_path):
    result = run_cli("stats", "--type", "adr", base_dir=str(tmp_path))
    assert result.returncode == 0
    assert "adr 总数: 0" in result.stdout


# ── related 子命令测试 ─────────────────────────────────────────────────


def test_related_matches_affects_and_related_rules(tmp_path):
    adrs_dir = tmp_path / "ldvh-base" / "adrs"
    adrs_dir.mkdir(parents=True)
    write_adr(adrs_dir / "adr-0001-test.yaml", affects=["specs/12.01-Tools辅助规范.md"], related_rules=[])
    write_adr(adrs_dir / "adr-0002-second.yaml", id="adr-0002", title="第二个", affects=[], related_rules=["specs/21.06-Contract.md"])

    result = run_cli("related", "21.06", base_dir=str(tmp_path))
    assert result.returncode == 0
    assert "共 1 个" in result.stdout
    assert "adr-0002" in result.stdout
    assert "adr-0001" not in result.stdout


def test_related_no_match(tmp_path):
    result = run_cli("related", "nonexistent", base_dir=str(tmp_path))
    assert result.returncode == 0
    assert "未找到" in result.stdout


# ── link-rule 子命令测试 ───────────────────────────────────────────────


def test_link_rule_appends_unique_rule(tmp_path):
    adrs_dir = tmp_path / "ldvh-base" / "adrs"
    adrs_dir.mkdir(parents=True)
    write_adr(adrs_dir / "adr-0001-test.yaml", related_rules=[])

    result = run_cli(
        "link-rule", "adr-0001",
        "--rule", "specs/21.04-Tools.md",
        "--human-gate-confirmed", "--confirmed-by", "user",
        "--confirmation-context", "测试",
        base_dir=str(tmp_path),
    )
    assert result.returncode == 0
    assert "已更新 related_rules" in result.stdout

    data = read_yaml(adrs_dir / "adr-0001-test.yaml")
    assert data["related_rules"] == ["specs/21.04-Tools.md"]


def test_link_rule_rejects_without_human_gate(tmp_path):
    adrs_dir = tmp_path / "ldvh-base" / "adrs"
    adrs_dir.mkdir(parents=True)
    write_adr(adrs_dir / "adr-0001-test.yaml", related_rules=[])

    result = run_cli("link-rule", "adr-0001", "--rule", "specs/test.md", base_dir=str(tmp_path))
    assert result.returncode != 0
    assert "缺少 --human-gate-confirmed" in result.stderr


def test_link_rule_no_change_when_duplicate(tmp_path):
    adrs_dir = tmp_path / "ldvh-base" / "adrs"
    adrs_dir.mkdir(parents=True)
    write_adr(adrs_dir / "adr-0001-test.yaml", related_rules=["specs/existing.md"])

    result = run_cli(
        "link-rule", "adr-0001",
        "--rule", "specs/existing.md",
        "--human-gate-confirmed", "--confirmed-by", "user",
        "--confirmation-context", "测试",
        base_dir=str(tmp_path),
    )
    assert result.returncode == 0
    assert "无变化" in result.stdout


# ── deprecate 子命令测试 ───────────────────────────────────────────────


def test_deprecate_updates_status_and_reason(tmp_path):
    adrs_dir = tmp_path / "ldvh-base" / "adrs"
    adrs_dir.mkdir(parents=True)
    write_adr(adrs_dir / "adr-0001-test.yaml", status="accepted", consequences="原影响")

    result = run_cli(
        "deprecate", "adr-0001",
        "--reason", "已不适用",
        "--human-gate-confirmed", "--confirmed-by", "user",
        "--confirmation-context", "测试",
        base_dir=str(tmp_path),
    )
    assert result.returncode == 0
    assert "已废弃 ADR" in result.stdout

    data = read_yaml(adrs_dir / "adr-0001-test.yaml")
    assert data["status"] == "deprecated"
    assert "废弃原因：已不适用" in data["consequences"]


def test_deprecate_rejects_without_human_gate(tmp_path):
    adrs_dir = tmp_path / "ldvh-base" / "adrs"
    adrs_dir.mkdir(parents=True)
    write_adr(adrs_dir / "adr-0001-test.yaml", status="accepted")

    result = run_cli("deprecate", "adr-0001", "--reason", "已不适用", base_dir=str(tmp_path))
    assert result.returncode != 0
    assert "缺少 --human-gate-confirmed" in result.stderr


def test_deprecate_rejects_illegal_transition(tmp_path):
    adrs_dir = tmp_path / "ldvh-base" / "adrs"
    adrs_dir.mkdir(parents=True)
    write_adr(adrs_dir / "adr-0001-test.yaml", status="rejected")

    result = run_cli(
        "deprecate", "adr-0001",
        "--reason", "已不适用",
        "--human-gate-confirmed", "--confirmed-by", "user",
        "--confirmation-context", "测试",
        base_dir=str(tmp_path),
    )
    assert result.returncode != 0
    assert "非法" in result.stderr


def test_deprecate_writes_reason_to_context(tmp_path):
    adrs_dir = tmp_path / "ldvh-base" / "adrs"
    adrs_dir.mkdir(parents=True)
    write_adr(adrs_dir / "adr-0001-test.yaml", status="accepted", context="原背景")

    result = run_cli(
        "deprecate", "adr-0001",
        "--reason", "已不适用",
        "--reason-field", "context",
        "--human-gate-confirmed", "--confirmed-by", "user",
        "--confirmation-context", "测试",
        base_dir=str(tmp_path),
    )
    assert result.returncode == 0

    data = read_yaml(adrs_dir / "adr-0001-test.yaml")
    assert data["status"] == "deprecated"
    assert "废弃原因：已不适用" in data["context"]


# ── supersede 子命令测试 ───────────────────────────────────────────────


def test_supersede_creates_new_adr_and_updates_old(tmp_path):
    adrs_dir = tmp_path / "ldvh-base" / "adrs"
    adrs_dir.mkdir(parents=True)
    write_adr(adrs_dir / "adr-0001-old.yaml", id="adr-0001", status="accepted", title="旧 ADR")

    result = run_cli(
        "supersede",
        "--old-adr-id", "adr-0001",
        "--slug", "new-adr",
        "--title", "新 ADR",
        "--context", "新背景",
        "--decision", "新决策",
        "--consequences", "新影响",
        "--human-gate-confirmed", "--confirmed-by", "user",
        "--confirmation-context", "测试",
        base_dir=str(tmp_path),
    )
    assert result.returncode == 0
    assert "已创建替代 ADR" in result.stdout
    assert "已更新旧 ADR" in result.stdout

    old_data = read_yaml(adrs_dir / "adr-0001-old.yaml")
    new_data = read_yaml(adrs_dir / "adr-0002-new-adr.yaml")
    assert old_data["status"] == "superseded"
    assert old_data["superseded_by"] == "adr-0002"
    assert new_data["status"] == "proposed"
    assert "adr-0001" in new_data["related_objects"]


def test_supersede_rejects_without_human_gate(tmp_path):
    adrs_dir = tmp_path / "ldvh-base" / "adrs"
    adrs_dir.mkdir(parents=True)
    write_adr(adrs_dir / "adr-0001-old.yaml", id="adr-0001", status="accepted")

    result = run_cli(
        "supersede",
        "--old-adr-id", "adr-0001",
        "--slug", "new-adr",
        "--title", "新 ADR",
        "--decision", "新决策",
        "--consequences", "新影响",
        base_dir=str(tmp_path),
    )
    assert result.returncode != 0
    assert "缺少 --human-gate-confirmed" in result.stderr


def test_supersede_rejects_non_accepted_old_adr(tmp_path):
    adrs_dir = tmp_path / "ldvh-base" / "adrs"
    adrs_dir.mkdir(parents=True)
    write_adr(adrs_dir / "adr-0001-old.yaml", id="adr-0001", status="proposed")

    result = run_cli(
        "supersede",
        "--old-adr-id", "adr-0001",
        "--slug", "new-adr",
        "--title", "新 ADR",
        "--decision", "新决策",
        "--consequences", "新影响",
        "--human-gate-confirmed", "--confirmed-by", "user",
        "--confirmation-context", "测试",
        base_dir=str(tmp_path),
    )
    assert result.returncode != 0
    assert "非法" in result.stderr


# ── ADR create Human Gate 强制检查 ─────────────────────────────────────


def test_create_adr_requires_human_gate(tmp_path):
    result = run_cli("create", "adr", "--title", "Test ADR", base_dir=str(tmp_path))
    assert result.returncode != 0
    assert "缺少 --human-gate-confirmed" in result.stderr


def test_create_adr_with_human_gate_succeeds(tmp_path):
    result = run_cli(
        "create", "adr", "--title", "Test ADR",
        "--human-gate-confirmed", "--confirmed-by", "user",
        "--confirmation-context", "测试",
        base_dir=str(tmp_path),
    )
    assert result.returncode == 0
    # Should output ADR file path and Change file path
    lines = result.stdout.strip().splitlines()
    assert len(lines) >= 1


# ── ADR transition Human Gate 强制检查 ─────────────────────────────────


def test_transition_adr_requires_human_gate(tmp_path):
    adrs_dir = tmp_path / "ldvh-base" / "adrs"
    adrs_dir.mkdir(parents=True)
    write_adr(adrs_dir / "adr-0001-test.yaml", status="proposed")

    result = run_cli("transition", str(adrs_dir / "adr-0001-test.yaml"), "--to", "accepted")
    assert result.returncode != 0
    assert "缺少 --human-gate-confirmed" in result.stderr


def test_transition_adr_with_human_gate_succeeds(tmp_path):
    adrs_dir = tmp_path / "ldvh-base" / "adrs"
    adrs_dir.mkdir(parents=True)
    write_adr(adrs_dir / "adr-0001-test.yaml", status="proposed")

    result = run_cli(
        "transition", str(adrs_dir / "adr-0001-test.yaml"),
        "--to", "accepted",
        "--human-gate-confirmed", "--confirmed-by", "user",
        "--confirmation-context", "测试",
        base_dir=str(tmp_path),
    )
    assert result.returncode == 0
    assert "proposed → accepted" in result.stdout


def test_transition_adr_rejects_illegal_status_change(tmp_path):
    adrs_dir = tmp_path / "ldvh-base" / "adrs"
    adrs_dir.mkdir(parents=True)
    write_adr(adrs_dir / "adr-0001-test.yaml", status="proposed")

    # proposed → superseded is not a valid ADR transition
    result = run_cli(
        "transition", str(adrs_dir / "adr-0001-test.yaml"),
        "--to", "superseded",
        "--human-gate-confirmed", "--confirmed-by", "user",
        "--confirmation-context", "测试",
    )
    assert result.returncode != 0
    assert "不允许的流转" in result.stderr


def test_transition_adr_rejects_terminal_status_reopen(tmp_path):
    adrs_dir = tmp_path / "ldvh-base" / "adrs"
    adrs_dir.mkdir(parents=True)
    write_adr(adrs_dir / "adr-0001-test.yaml", status="rejected")

    result = run_cli(
        "transition", str(adrs_dir / "adr-0001-test.yaml"),
        "--to", "accepted",
        "--human-gate-confirmed", "--confirmed-by", "user",
        "--confirmation-context", "测试",
    )
    assert result.returncode != 0
    # rejected → accepted is caught by either "不允许的流转" or "终态"
    assert "不允许的流转" in result.stderr or "终态" in result.stderr


# ── --write-change 测试 ────────────────────────────────────────────────


def test_deprecate_with_write_change_creates_change_record(tmp_path):
    adrs_dir = tmp_path / "ldvh-base" / "adrs"
    adrs_dir.mkdir(parents=True)
    write_adr(adrs_dir / "adr-0001-test.yaml", status="accepted")

    result = run_cli(
        "deprecate", "adr-0001",
        "--reason", "已不适用",
        "--human-gate-confirmed", "--confirmed-by", "user",
        "--confirmation-context", "测试",
        "--write-change",
        base_dir=str(tmp_path),
    )
    assert result.returncode == 0

    changes_dir = tmp_path / "ldvh-base" / "changes"
    change_files = list(changes_dir.glob("change-*.yaml"))
    assert len(change_files) >= 1
    change_data = read_yaml(change_files[0])
    assert change_data["human_gate"]["confirmed_by"] == "user"


def test_link_rule_with_write_change_creates_change_record(tmp_path):
    adrs_dir = tmp_path / "ldvh-base" / "adrs"
    adrs_dir.mkdir(parents=True)
    write_adr(adrs_dir / "adr-0001-test.yaml", related_rules=[])

    result = run_cli(
        "link-rule", "adr-0001",
        "--rule", "specs/21.04-Tools.md",
        "--human-gate-confirmed", "--confirmed-by", "user",
        "--confirmation-context", "测试",
        "--write-change",
        base_dir=str(tmp_path),
    )
    assert result.returncode == 0

    changes_dir = tmp_path / "ldvh-base" / "changes"
    change_files = list(changes_dir.glob("change-*.yaml"))
    assert len(change_files) >= 1
