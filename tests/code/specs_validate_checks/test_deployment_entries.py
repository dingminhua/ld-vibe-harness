import subprocess
import sys
from pathlib import Path

from .common import checker, write_md
from spec_checks import deployment_entries as deployment_entries_checks


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEPLOYMENT_REGISTRY_PATH = "specs/attachments/06.Att.02-固定运行时扩展登记表.md"


def write_deployment_entries_fixture(tmp_path):
    write_md(
        tmp_path / "rules" / "LDVH-RUNTIME-PROTOCOL.md",
        f"""
# LDVH Runtime Protocol

```yaml
ldvh_asset:
  id: "ldvh-runtime-protocol"
  type: "rule"
  status: "active"
  canonical_path: "rules/LDVH-RUNTIME-PROTOCOL.md"
  source_specs:
    - "{DEPLOYMENT_REGISTRY_PATH}"
  consumption_scenarios:
    - "测试场景"
  inputs:
    - "测试输入"
  outputs:
    - "测试输出"
  handoff: "测试交还"
  verification:
    - "python3 code/specs_validate.py deployment-entries"
  sync_triggers:
    - "测试触发"
  deprecation: "测试废弃规则"
```

固定运行时扩展登记见 `{DEPLOYMENT_REGISTRY_PATH}`。

## 1. 这是什么

LDVH 固定 Rules 入口。Rules 路径只负责把 canonical event 派发给 `hook_dispatch.py`。

## 2. 四事件触发表

| 发生时 | canonical event | Rules 路径命令 |
|---|---|---|
| 会话开始 | `session-start` | `python3 code/hook_dispatch.py run session-start --trigger-source rules --cwd <cwd> --target <target>` |
| dispatcher 输出要求确认入口读取后 | `acknowledge-read-plan` | `python3 code/hook_dispatch.py run acknowledge-read-plan --trigger-source rules --cwd <cwd>` |
| Write / Edit 前 | `pre-tool-use` | `python3 code/hook_dispatch.py run pre-tool-use --trigger-source rules --cwd <cwd> --target <target>` |
| Git commit 前 | `git.commit-msg` | `python3 code/hook_dispatch.py run git.commit-msg --trigger-source rules --message-file <message-file>` |

Hook 路径：环境原生事件映射为 canonical event，并交给同一 dispatcher。

## 3. 消费 dispatcher 输出

Rules 路径执行表内命令后，AI 只消费 dispatcher 返回的结构化输出。

## 4. STOP

dispatcher 返回停止条件时，AI 必须停止当前动作并按 dispatcher 输出处理。
""",
    )
    write_md(
        tmp_path / "hooks" / "ldvh-hooks.yaml",
        f"""
ldvh_asset:
  id: "ldvh-hook-registry"
  type: "hook"
  status: "active"
  canonical_path: "hooks/ldvh-hooks.yaml"
  source_specs:
    - "{DEPLOYMENT_REGISTRY_PATH}"
  consumption_scenarios:
    - "测试场景"
  inputs:
    - "测试输入"
  outputs:
    - "测试输出"
  handoff: "测试交还"
  verification:
    - "python3 code/specs_validate.py deployment-entries"
  sync_triggers:
    - "测试触发"
  deprecation: "测试废弃规则"
hooks:
  - id: "test"
    event: "git.commit-msg"
    command:
      - "python3"
      - "code/commit_validate.py"
""",
    )
    write_md(
        tmp_path / "skills" / "ldvh-git-commit" / "SKILL.md",
        f"""
---
name: ldvh-git-commit
description: Prepare, validate, and create LDVH Git commits under specs/07.
---

# LDVH Git Commit

```yaml
ldvh_asset:
  id: "ldvh-git-commit"
  type: "skill"
  status: "active"
  canonical_path: "skills/ldvh-git-commit/SKILL.md"
  source_specs:
    - "{DEPLOYMENT_REGISTRY_PATH}"
  consumption_scenarios:
    - "测试场景"
  inputs:
    - "测试输入"
  outputs:
    - "测试输出"
  handoff: "测试交还"
  verification:
    - "python3 code/specs_validate.py deployment-entries"
  sync_triggers:
    - "测试触发"
  deprecation: "测试废弃规则"
```
""",
    )
    return write_md(
        tmp_path / DEPLOYMENT_REGISTRY_PATH,
        """
# 固定运行时扩展登记表

## 2. 登记表

| 类型 | 当前固定承载物 | 权威路径 | 边界 |
|---|---|---|---|
| Rules | Runtime Protocol | `rules/LDVH-RUNTIME-PROTOCOL.md` | 只做统一入口 |
| Skill | Git 提交 Skill | `skills/ldvh-git-commit/SKILL.md` | 只做执行转换 |
| Hook | Hook registry | `hooks/ldvh-hooks.yaml` | 只做统一登记 |
""",
    )


def deployment_entry_codes(issues):
    return [issue.code for issue in issues]


def test_deployment_entries_core_implementation_lives_in_spec_checks():
    assert checker.deployment_entries_checks is deployment_entries_checks
    assert deployment_entries_checks.deployment_entries_check.__module__ == "spec_checks.deployment_entries"
    assert deployment_entries_checks.deployment_entries_main.__module__ == "spec_checks.deployment_entries"


def test_deployment_entries_valid_fixture_passes(tmp_path):
    write_deployment_entries_fixture(tmp_path)

    assert checker.deployment_entries_check(tmp_path) == []


def test_deployment_entries_reports_missing_spec(tmp_path):
    issues = checker.deployment_entries_check(tmp_path)

    assert "DEPLOYMENT_ENTRIES_SPEC_MISSING" in deployment_entry_codes(issues)


def test_deployment_entries_reports_required_type_and_asset_problems(tmp_path):
    write_deployment_entries_fixture(tmp_path)
    (tmp_path / "rules" / "LDVH-RUNTIME-PROTOCOL.md").unlink()
    spec_path = tmp_path / DEPLOYMENT_REGISTRY_PATH
    text = spec_path.read_text(encoding="utf-8")
    text = text.replace("| Rules | Runtime Protocol | `rules/LDVH-RUNTIME-PROTOCOL.md` | 只做统一入口 |\n", "")
    spec_path.write_text(text, encoding="utf-8")

    codes = deployment_entry_codes(checker.deployment_entries_check(tmp_path))

    assert "DEPLOYMENT_ENTRIES_REQUIRED_TYPE_MISSING" in codes
    assert "DEPLOYMENT_ENTRIES_REQUIRED_ASSET_MISSING" in codes


def test_deployment_entries_reports_forbidden_type_and_ai_entry_ref_missing(tmp_path):
    spec_path = write_deployment_entries_fixture(tmp_path)
    ai_entry = tmp_path / "rules" / "LDVH-RUNTIME-PROTOCOL.md"
    ai_entry.write_text("# LDVH Runtime Protocol\n", encoding="utf-8")
    with spec_path.open("a", encoding="utf-8") as file:
        file.write("| Code | `code/specs_validate.py` | Code 检查 | 不适用 |\n")

    codes = deployment_entry_codes(checker.deployment_entries_check(tmp_path))

    assert "DEPLOYMENT_ENTRIES_FORBIDDEN_TYPE" in codes
    assert "DEPLOYMENT_ENTRIES_AI_ENTRY_REF_MISSING" in codes


def test_deployment_entries_reports_missing_asset_metadata(tmp_path):
    write_deployment_entries_fixture(tmp_path)
    asset_path = tmp_path / "rules" / "LDVH-RUNTIME-PROTOCOL.md"
    asset_path.write_text(f"# LDVH Runtime Protocol\n\n固定运行时扩展登记见 `{DEPLOYMENT_REGISTRY_PATH}`。\n", encoding="utf-8")

    codes = deployment_entry_codes(checker.deployment_entries_check(tmp_path))

    assert "DEPLOYMENT_ENTRIES_ASSET_METADATA_MISSING" in codes


def test_deployment_entries_reports_asset_metadata_mismatch(tmp_path):
    write_deployment_entries_fixture(tmp_path)
    asset_path = tmp_path / "rules" / "LDVH-RUNTIME-PROTOCOL.md"
    text = asset_path.read_text(encoding="utf-8")
    asset_path.write_text(text.replace('id: "ldvh-runtime-protocol"', 'id: "wrong-entry"'), encoding="utf-8")

    codes = deployment_entry_codes(checker.deployment_entries_check(tmp_path))

    assert "DEPLOYMENT_ENTRIES_ASSET_METADATA_MISMATCH" in codes


def test_deployment_entries_reports_runtime_protocol_whitelist_violation(tmp_path):
    write_deployment_entries_fixture(tmp_path)
    asset_path = tmp_path / "rules" / "LDVH-RUNTIME-PROTOCOL.md"
    text = asset_path.read_text(encoding="utf-8")
    asset_path.write_text(text + "\nreceipt 细节：`governed_subject`。\n", encoding="utf-8")

    codes = deployment_entry_codes(checker.deployment_entries_check(tmp_path))

    assert "DEPLOYMENT_ENTRIES_RUNTIME_PROTOCOL_WHITELIST_VIOLATION" in codes


def test_deployment_entries_cli_is_in_all(tmp_path, monkeypatch, capsys):
    write_deployment_entries_fixture(tmp_path)
    monkeypatch.setattr(checker, "SPECS_DIR", tmp_path / "specs")
    monkeypatch.setattr(checker, "FORMAL_SPECS_DIR", tmp_path / "specs")
    monkeypatch.setattr(checker, "DOCS_DIR", tmp_path / "docs")
    monkeypatch.setattr(checker, "RUNTIME_PROJECTION_DEFAULT_PATHS", ["rules/LDVH-RUNTIME-PROTOCOL.md"])

    exit_code = checker.main(["deployment-entries", "--root", str(tmp_path)])

    assert exit_code == 0
    assert "固定运行时扩展登记检查通过" in capsys.readouterr().out


def test_deployment_entries_script_fast_path_outputs_text(tmp_path):
    write_deployment_entries_fixture(tmp_path)

    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "code" / "specs_validate.py"),
            "deployment-entries",
            "--root",
            str(tmp_path),
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert "固定运行时扩展登记检查通过。" in result.stdout
    assert result.stderr == ""
