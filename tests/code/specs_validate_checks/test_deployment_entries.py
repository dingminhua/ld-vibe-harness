from .common import checker, write_md
from spec_checks import deployment_entries as deployment_entries_checks

def write_deployment_entries_fixture(tmp_path):
    for path, title in [
        ("LDVH-WORKSPACE-ENTRY.md", "LDVH 工作区入口"),
        ("LDVH-MAINTAINER-ENTRY.md", "LDVH 维护入口"),
    ]:
        write_md(
            tmp_path / "rules" / path,
            f"""
# {title}

LDVH 能力资产与落地保障定义见 `specs/04.02-LDVH能力资产与落地保障规范.md`。
""",
        )
    write_md(tmp_path / "skills" / "ldvh-spec-change-check" / "SKILL.md", "# Skill")
    write_md(tmp_path / "agents" / "ldvh-spec-semantic-review.md", "# Agent")
    write_md(tmp_path / "hooks" / "ldvh-lifecycle-check.md", "# Hook")
    return write_md(
        tmp_path / "specs" / "04.02-LDVH能力资产与落地保障规范.md",
        """
# LDVH 能力资产与落地保障规范

## 2. LDVH 能力资产

| 能力资产类型 | 当前固定资产 | 适合保障 | 不适合保障 | 边界 |
|---|---|---|---|---|
| Rules 资产 | `rules/LDVH-WORKSPACE-ENTRY.md`、`rules/LDVH-MAINTAINER-ENTRY.md` | AI 入口分层 | 完整规范正文 | 只做薄入口 |
| Skill 资产 | `skills/ldvh-spec-change-check/SKILL.md` | 治理检查 SOP | 稳定规则正文 | 不新增稳定规则 |
| Agent 资产 | `agents/ldvh-spec-semantic-review.md` | 独立语义审查 | 直接生效结论 | 输出回主控 |
| Hook 资产 | `hooks/ldvh-lifecycle-check.md` | 生命周期检查入口 | 规范正文 | 触发不等于通过 |
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
    (tmp_path / "hooks" / "ldvh-lifecycle-check.md").unlink()
    spec_path = tmp_path / "specs" / "04.02-LDVH能力资产与落地保障规范.md"
    text = spec_path.read_text(encoding="utf-8")
    text = text.replace("| Agent 资产 | `agents/ldvh-spec-semantic-review.md` | 独立语义审查 | 直接生效结论 | 输出回主控 |\n", "")
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


def test_deployment_entries_cli_is_in_all(tmp_path, monkeypatch, capsys):
    write_deployment_entries_fixture(tmp_path)
    monkeypatch.setattr(checker, "SPECS_DIR", tmp_path / "specs")
    monkeypatch.setattr(checker, "FORMAL_SPECS_DIR", tmp_path / "specs")
    monkeypatch.setattr(checker, "DOCS_DIR", tmp_path / "docs")
    monkeypatch.setattr(checker, "RUNTIME_PROJECTION_DEFAULT_PATHS", ["rules/LDVH-WORKSPACE-ENTRY.md"])

    exit_code = checker.main(["deployment-entries", "--root", str(tmp_path)])

    assert exit_code == 0
    assert "LDVH 能力资产检查通过" in capsys.readouterr().out
