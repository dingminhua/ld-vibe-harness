from .common import checker, write_md
from spec_checks import deployment_entries as deployment_entries_checks

def write_deployment_entries_fixture(tmp_path):
    for path, title, asset_id in [
        ("LDVH-WORKSPACE-ENTRY.md", "LDVH 工作区入口", "ldvh-workspace-entry"),
        ("LDVH-MAINTAINER-ENTRY.md", "LDVH 维护入口", "ldvh-maintainer-entry"),
    ]:
        canonical_path = f"rules/{path}"
        write_md(
            tmp_path / "rules" / path,
            f"""
# {title}

```yaml
ldvh_asset:
  id: "{asset_id}"
  type: "rule"
  status: "active"
  canonical_path: "{canonical_path}"
  source_specs:
    - "specs/04.02-LDVH能力资产与落地保障规范.md"
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

LDVH 能力资产与落地保障定义见 `specs/04.02-LDVH能力资产与落地保障规范.md`。
""",
        )
    write_md(
        tmp_path / "hooks" / "commit-msg",
        """
#!/bin/sh
# ```yaml
# ldvh_asset:
#   id: "ldvh-commit-msg-hook"
#   type: "hook"
#   status: "active"
#   canonical_path: "hooks/commit-msg"
#   source_specs:
#     - "specs/10-Git提交规范.md"
#   consumption_scenarios:
#     - "测试场景"
#   inputs:
#     - "测试输入"
#   outputs:
#     - "测试输出"
#   handoff: "测试交还"
#   verification:
#     - "python3 code/specs_validate.py deployment-entries"
#   sync_triggers:
#     - "测试触发"
#   deprecation: "测试废弃规则"
# ```
echo test
""",
    )
    return write_md(
        tmp_path / "specs" / "04.02-LDVH能力资产与落地保障规范.md",
        """
# LDVH 能力资产与落地保障规范

## 2. LDVH 能力资产

| 能力资产类型 | 当前固定资产 | 适合保障 | 不适合保障 | 边界 |
|---|---|---|---|---|
| Rules 资产 | `rules/LDVH-WORKSPACE-ENTRY.md`、`rules/LDVH-MAINTAINER-ENTRY.md` | AI 入口分层 | 完整规范正文 | 只做薄入口 |
| Hook 资产 | `hooks/commit-msg` | Git 提交消息校验 | 替代 Code 校验 | 只做本地前置 |
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
    (tmp_path / "rules" / "LDVH-MAINTAINER-ENTRY.md").unlink()
    spec_path = tmp_path / "specs" / "04.02-LDVH能力资产与落地保障规范.md"
    text = spec_path.read_text(encoding="utf-8")
    text = text.replace("| Rules 资产 | `rules/LDVH-WORKSPACE-ENTRY.md`、`rules/LDVH-MAINTAINER-ENTRY.md` | AI 入口分层 | 完整规范正文 | 只做薄入口 |\n", "")
    spec_path.write_text(text, encoding="utf-8")

    codes = deployment_entry_codes(checker.deployment_entries_check(tmp_path))

    assert "DEPLOYMENT_ENTRIES_REQUIRED_TYPE_MISSING" in codes
    assert "DEPLOYMENT_ENTRIES_REQUIRED_ASSET_MISSING" in codes


def test_deployment_entries_reports_forbidden_type_and_ai_entry_ref_missing(tmp_path):
    spec_path = write_deployment_entries_fixture(tmp_path)
    ai_entry = tmp_path / "rules" / "LDVH-WORKSPACE-ENTRY.md"
    ai_entry.write_text("# LDVH 工作区入口\n", encoding="utf-8")
    with spec_path.open("a", encoding="utf-8") as file:
        file.write("| Code | `code/specs_validate.py` | Code 检查 | 不适用 |\n")

    codes = deployment_entry_codes(checker.deployment_entries_check(tmp_path))

    assert "DEPLOYMENT_ENTRIES_FORBIDDEN_TYPE" in codes
    assert "DEPLOYMENT_ENTRIES_AI_ENTRY_REF_MISSING" in codes


def test_deployment_entries_reports_missing_asset_metadata(tmp_path):
    write_deployment_entries_fixture(tmp_path)
    asset_path = tmp_path / "rules" / "LDVH-WORKSPACE-ENTRY.md"
    asset_path.write_text("# LDVH 工作区入口\n\nLDVH 能力资产与落地保障定义见 `specs/04.02-LDVH能力资产与落地保障规范.md`。\n", encoding="utf-8")

    codes = deployment_entry_codes(checker.deployment_entries_check(tmp_path))

    assert "DEPLOYMENT_ENTRIES_ASSET_METADATA_MISSING" in codes


def test_deployment_entries_reports_asset_metadata_mismatch(tmp_path):
    write_deployment_entries_fixture(tmp_path)
    asset_path = tmp_path / "rules" / "LDVH-WORKSPACE-ENTRY.md"
    text = asset_path.read_text(encoding="utf-8")
    asset_path.write_text(text.replace('id: "ldvh-workspace-entry"', 'id: "wrong-entry"'), encoding="utf-8")

    codes = deployment_entry_codes(checker.deployment_entries_check(tmp_path))

    assert "DEPLOYMENT_ENTRIES_ASSET_METADATA_MISMATCH" in codes


def test_deployment_entries_cli_is_in_all(tmp_path, monkeypatch, capsys):
    write_deployment_entries_fixture(tmp_path)
    monkeypatch.setattr(checker, "SPECS_DIR", tmp_path / "specs")
    monkeypatch.setattr(checker, "FORMAL_SPECS_DIR", tmp_path / "specs")
    monkeypatch.setattr(checker, "DOCS_DIR", tmp_path / "docs")
    monkeypatch.setattr(checker, "RUNTIME_PROJECTION_DEFAULT_PATHS", ["rules/LDVH-WORKSPACE-ENTRY.md"])

    exit_code = checker.main(["deployment-entries", "--root", str(tmp_path)])

    assert exit_code == 0
    assert "LDVH 能力资产检查通过" in capsys.readouterr().out
