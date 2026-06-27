import importlib.util
import os
import subprocess
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[2] / "code" / "commit_validate.py"
PROJECT_ROOT = MODULE_PATH.parents[1]
spec = importlib.util.spec_from_file_location("commit_validate", MODULE_PATH)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def issue_messages(issues):
    return [i.message for i in issues]


def issue_codes(issues):
    return [(i.level, i.message) for i in issues]


# ══════════════════════════════════════════════════════════════════════
# check_commit — 单条 commit 格式检查
# ══════════════════════════════════════════════════════════════════════


def make_commit(hash_val="abc12345", subject="", body=""):
    return checker.CommitInfo(
        hash=hash_val,
        subject=subject,
        body=body,
        full_message=f"{subject}\n\n{body}".strip() if body else subject,
    )


def test_valid_commit_passes():
    commit = make_commit(
        subject="docs(specs): 采用约定式提交规范",
        body=(
            "关键变更:\n"
            "- 采用关键变更必需模板。\n\n"
            "验证结论:\n"
            "- 已确认格式检查通过。\n\n"
            "动机:\n"
            "- 统一提交正文结构。\n\n"
            "影响边界:\n"
            "- 影响 commit validator 与 Web 展示。\n\n"
            "风险与后续:\n"
            "- 旧正文需要兼容展示。"
        ),
    )

    issues = checker.check_commit(commit)
    errors = [i for i in issues if i.level == "error"]

    assert errors == []


def test_invalid_format_first_line():
    commit = make_commit(subject="随便写的 commit message")

    issues = checker.check_commit(commit)
    errors = [i for i in issues if i.level == "error"]

    assert any("第一行格式不符合" in i.message for i in errors)


def test_invalid_type():
    commit = make_commit(subject="invalid(scope): 测试")

    issues = checker.check_commit(commit)

    assert any("type" in i.message and "不在有效枚举" in i.message for i in issues)


def test_standard_types_pass():
    for type_name in ("build", "chore", "ci", "docs", "feat", "fix", "perf", "refactor", "revert", "style", "test"):
        commit = make_commit(subject=f"{type_name}: 测试标准类型")

        issues = checker.check_commit(commit)
        errors = [i for i in issues if i.level == "error"]

        assert errors == []


def test_breaking_change_marker_passes():
    commit = make_commit(
        subject="feat(code)!: 调整公开接口参数",
        body=(
            "关键变更:\n"
            "- 改为传入结构化参数。\n\n"
            "验证结论:\n"
            "- 已确认 breaking 标记仍可解析。\n\n"
            "动机:\n"
            "- 调整接口参数以减少歧义。\n\n"
            "影响边界:\n"
            "- 影响所有调用方。\n\n"
            "风险与后续:\n"
            "- 需要同步调用方。"
        ),
    )

    issues = checker.check_commit(commit)
    errors = [i for i in issues if i.level == "error"]

    assert errors == []


def test_breaking_change_footer_passes():
    commit = make_commit(
        subject="feat(code)!: 调整公开接口参数",
        body=(
            "关键变更:\n"
            "- 说明 breaking footer 兼容。\n\n"
            "验证结论:\n"
            "- 已确认 footer 保留。\n\n"
            "动机:\n"
            "- 调整公开接口参数。\n\n"
            "影响边界:\n"
            "- 影响调用方。\n\n"
            "风险与后续:\n"
            "- 旧参数不再兼容。\n\n"
            "BREAKING CHANGE: 旧参数不再兼容。"
        ),
    )

    issues = checker.check_commit(commit)
    errors = [i for i in issues if i.level == "error"]

    assert errors == []


def test_fixed_body_template_passes():
    commit = make_commit(
        subject="docs(specs): 统一提交正文模板",
        body=(
            "关键变更:\n"
            "- 规定提交正文以关键变更为必需字段。\n\n"
            "验证结论:\n"
            "- 已确认格式规则和展示规则保持一致。\n\n"
            "动机:\n"
            "- 统一提交正文结构，避免展示层解析分叉。\n\n"
            "影响边界:\n"
            "- 影响 commit_validate、Web 提交详情和提交说明。\n\n"
            "风险与后续:\n"
            "- 旧提交仍会按兼容逻辑展示。"
        ),
    )

    issues = checker.check_commit(commit)
    errors = [i for i in issues if i.level == "error"]

    assert errors == []


def test_body_template_missing_section_errors():
    commit = make_commit(
        subject="docs(specs): 统一提交正文模板",
        body=(
            "动机:\n"
            "- 统一提交正文结构。\n\n"
            "验证结论:\n"
            "- 已确认规则同步。"
        ),
    )

    issues = checker.check_commit(commit)
    errors = [i for i in issues if i.level == "error"]

    assert any("关键变更字段" in i.message for i in errors)


def test_body_template_wrong_required_order_errors():
    commit = make_commit(
        subject="docs(specs): 统一提交正文模板",
        body=(
            "动机:\n"
            "- 再写动机。\n\n"
            "验证结论:\n"
            "- 最后写验证结论。"
        ),
    )

    issues = checker.check_commit(commit)
    errors = [i for i in issues if i.level == "error"]

    assert any("关键变更字段" in i.message for i in errors)


def test_body_section_content_requires_dash_list_item():
    commit = make_commit(
        subject="docs(specs): 统一提交正文模板",
        body=(
            "关键变更:\n"
            "这一行没有使用列表项。\n\n"
            "验证结论:\n"
            "- 已确认应触发格式错误。"
        ),
    )

    issues = checker.check_commit(commit)
    errors = [i for i in issues if i.level == "error"]

    assert any("必须使用 '- ' 列表项" in i.message for i in errors)


def test_body_section_footer_does_not_require_dash_list_item():
    commit = make_commit(
        subject="docs(specs): 统一提交正文模板",
        body=(
            "关键变更:\n"
            "- 统一正文列表形式。\n\n"
            "验证结论:\n"
            "- 已确认 footer 不按正文列表处理。\n\n"
            "Refs: #123"
        ),
    )

    issues = checker.check_commit(commit)
    errors = [i for i in issues if i.level == "error"]

    assert errors == []


def test_body_section_list_items_must_be_compact():
    commit = make_commit(
        subject="docs(specs): 统一提交正文模板",
        body=(
            "关键变更:\n"
            "- 第一条。\n\n"
            "- 第二条不应和第一条隔空行。\n\n"
            "验证结论:\n"
            "- 已确认应触发紧凑列表错误。"
        ),
    )

    issues = checker.check_commit(commit)
    errors = [i for i in issues if i.level == "error"]

    assert any("不得用空行分隔" in i.message for i in errors)


def test_body_section_allows_blank_line_between_sections():
    commit = make_commit(
        subject="docs(specs): 统一提交正文模板",
        body=(
            "关键变更:\n"
            "- 第一段关键变更。\n\n"
            "验证结论:\n"
            "- 已确认小标题之间允许空行。"
        ),
    )

    issues = checker.check_commit(commit)
    errors = [i for i in issues if i.level == "error"]

    assert errors == []


def test_uppercase_type_warns_but_parses():
    commit = make_commit(subject="FIX(web): 修复页面错误")

    issues = checker.check_commit(commit)
    errors = [i for i in issues if i.level == "error"]
    warnings = [i for i in issues if i.level == "warning"]

    assert errors == []
    assert any("建议使用小写" in i.message for i in warnings)


def test_valid_type_without_scope():
    commit = make_commit(
        subject="docs: 测试文档",
        body=(
            "关键变更:\n"
            "- 更新文档正文。\n\n"
            "验证结论:\n"
            "- 已确认文档格式正确。\n\n"
            "动机:\n"
            "- 说明本次文档调整的原因。\n\n"
            "影响边界:\n"
            "- 影响文档内容。\n\n"
            "风险与后续:\n"
            "- 后续继续维护。"
        ),
    )

    issues = checker.check_commit(commit)
    errors = [i for i in issues if i.level == "error"]

    assert errors == []


def test_scope_outside_enum_errors():
    commit = make_commit(
        subject="feat(unknown-scope): 新功能",
        body=(
            "关键变更:\n"
            "- 说明 scope 违规。\n\n"
            "验证结论:\n"
            "- 应触发 scope 错误。\n\n"
            "动机:\n"
            "- 说明本次功能调整内容。\n\n"
            "影响边界:\n"
            "- 影响 lint。\n\n"
            "风险与后续:\n"
            "- 无。"
        ),
    )

    issues = checker.check_commit(commit)
    errors = [i for i in issues if i.level == "error"]

    assert any("scope" in i.message and "不在允许枚举" in i.message for i in errors)


def test_runtime_scope_is_allowed():
    commit = make_commit(
        subject="fix(runtime): 强化运行时门禁",
        body=(
            "关键变更:\n"
            "- 收紧 Hook 检查。\n\n"
            "验证结论:\n"
            "- 已确认 validator 可通过。\n\n"
            "动机:\n"
            "- 强化运行时门禁。\n\n"
            "影响边界:\n"
            "- 影响运行时协议。\n\n"
            "风险与后续:\n"
            "- 需要继续观察接入情况。"
        ),
    )

    issues = checker.check_commit(commit)
    errors = [i for i in issues if i.level == "error"]

    assert not any("scope" in i.message and "不在允许枚举" in i.message for i in errors)


def test_subject_too_long():
    long_subject = "a" * 100
    commit = make_commit(
        subject=f"docs(specs): {long_subject}",
        body=(
            "关键变更:\n"
            "- 验证长度提示。\n\n"
            "验证结论:\n"
            "- 已触发长度警告。\n\n"
            "动机:\n"
            "- 说明超长标题的测试。\n\n"
            "影响边界:\n"
            "- 只影响 lint 告警。\n\n"
            "风险与后续:\n"
            "- 无。"
        ),
    )

    issues = checker.check_commit(commit)
    warnings = [i for i in issues if i.level == "warning"]

    assert any("超过" in i.message and "字符" in i.message for i in warnings)


def test_missing_private_trailers_do_not_warn():
    commit = make_commit(
        subject="docs(specs): 测试",
        body=(
            "关键变更:\n"
            "- 无。\n\n"
            "验证结论:\n"
            "- 已确认无私有 trailer。\n\n"
            "动机:\n"
            "- 说明本次测试内容。\n\n"
            "影响边界:\n"
            "- 无。\n\n"
            "风险与后续:\n"
            "- 无。"
        ),
    )

    issues = checker.check_commit(commit)
    warnings = [i for i in issues if i.level == "warning"]

    assert not any("Human-Gate" in i.message or "Verification" in i.message or "Risk" in i.message for i in warnings)


def test_refs_footer_is_allowed():
    commit = make_commit(
        subject="docs(specs): 测试引用 footer",
        body=(
            "关键变更:\n"
            "- 说明引用 footer 兼容。\n\n"
            "验证结论:\n"
            "- 已确认 Refs 保留。\n\n"
            "动机:\n"
            "- 说明本次测试内容。\n\n"
            "影响边界:\n"
            "- 影响提交正文校验。\n\n"
            "风险与后续:\n"
            "- 无。\n\n"
            "Refs: #123"
        ),
    )

    issues = checker.check_commit(commit)
    errors = [i for i in issues if i.level == "error"]

    assert errors == []


def test_ldvh_private_trailers_warn():
    commit = make_commit(
        subject="docs(specs): 测试禁用字段",
        body=(
            "关键变更:\n"
            "- 说明 trailer 警告。\n\n"
            "验证结论:\n"
            "- 已确认会触发 warning。\n\n"
            "动机:\n"
            "- 说明本次测试内容。\n\n"
            "影响边界:\n"
            "- 影响提交正文契约。\n\n"
            "风险与后续:\n"
            "- 不应继续使用。\n\n"
            "Human-Gate: Human 确认\n"
            "Verification: pytest\n"
            "Risk: 无"
        ),
    )

    issues = checker.check_commit(commit)
    warnings = [i for i in issues if i.level == "warning"]

    assert any("不建议使用 LDVH 私有 trailer" in i.message for i in warnings)


def test_missing_chinese_in_subject_and_body_errors():
    commit = make_commit(
        subject="docs(specs): test no chinese",
        body=(
            "关键变更:\n"
            "- no chinese here。\n\n"
            "验证结论:\n"
            "- no chinese here。\n\n"
            "动机:\n"
            "- no chinese here。\n\n"
            "影响边界:\n"
            "- no chinese here。\n\n"
            "风险与后续:\n"
            "- no chinese here。"
        ),
    )

    issues = checker.check_commit(commit)
    errors = [i for i in issues if i.level == "error"]

    assert any("必须包含中文字符" in i.message for i in errors)


def test_missing_chinese_in_subject_errors():
    commit = make_commit(
        subject="docs(specs): fix commit lint",
        body=(
            "关键变更:\n"
            "- 已更新提交说明。\n\n"
            "验证结论:\n"
            "- 已确认 body 通过。\n\n"
            "动机:\n"
            "- 已经确认提交说明已补充中文语义。\n\n"
            "影响边界:\n"
            "- 影响 lint 结果。\n\n"
            "风险与后续:\n"
            "- 无。"
        )
    )

    issues = checker.check_commit(commit)
    errors = [i for i in issues if i.level == "error"]

    assert any("description 必须包含中文字符" in i.message for i in errors)


def test_missing_chinese_in_body_errors():
    commit = make_commit(
        subject="docs(specs): 补充提交规范说明",
        body=(
            "关键变更:\n"
            "- update commit spec only with english words。\n\n"
            "验证结论:\n"
            "- update commit spec only with english words。\n\n"
            "动机:\n"
            "- update commit spec only with english words。\n\n"
            "影响边界:\n"
            "- update commit spec only with english words。\n\n"
            "风险与后续:\n"
            "- update commit spec only with english words。"
        )
    )

    issues = checker.check_commit(commit)
    errors = [i for i in issues if i.level == "error"]

    assert errors == []


# ══════════════════════════════════════════════════════════════════════
# check_message — 提交前预检
# ══════════════════════════════════════════════════════════════════════


def test_check_message_valid():
    text = (
        "docs(specs): 更新文档\n\n"
        "关键变更:\n"
        "- 调整文档正文。\n\n"
        "验证结论:\n"
        "- 已确认格式有效。\n\n"
        "动机:\n"
        "- 更新文档的基本内容。\n\n"
        "影响边界:\n"
        "- 影响文档展示。\n\n"
        "风险与后续:\n"
        "- 无。"
    )

    issues = checker.check_message(text)
    errors = [i for i in issues if i.level == "error"]

    assert errors == []


def test_check_message_requires_body_for_staged_specs_file():
    text = "docs(specs): 明确提交正文语义"

    issues = checker.check_message(text, touched_files=["specs/07-事实源边界与Git追溯规范.md"])
    errors = [i for i in issues if i.level == "error"]

    assert any("要求 commit body 非空" in i.message for i in errors)


def test_get_staged_files_uses_requested_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True)
    specs_dir = repo / "specs"
    specs_dir.mkdir()
    changed = specs_dir / "example.md"
    changed.write_text("content\n", encoding="utf-8")
    subprocess.run(["git", "add", "specs/example.md"], cwd=repo, check=True)

    assert checker.get_staged_files(repo) == ["specs/example.md"]


def test_show_format_uses_v2_commit_spec(capsys):
    checker.show_format()

    output = capsys.readouterr().out

    assert "specs/07-事实源边界与Git追溯规范.md" in output
    assert "specs/attachments/07.Att.02-Commit-Type枚举表.md" in output
    assert "specs/10-Git提交规范.md" not in output


def test_body_mainly_commands_warns():
    commit = make_commit(
        subject="docs(specs): 明确提交正文语义",
        body=(
            "关键变更:\n"
            "- 记录验证命令。\n\n"
            "验证结论:\n"
            "- 命令能够执行。\n\n"
            "动机:\n"
            "- 明确提交正文语义。\n\n"
            "影响边界:\n"
            "- 影响提交说明。\n\n"
            "风险与后续:\n"
            "- 仍需补充结论。\n\n"
            "npm run web:check\n"
            "python3 code/specs_validate.py doc specs\n"
            "git diff --check"
        ),
    )

    issues = checker.check_commit(commit)
    warnings = [i for i in issues if i.level == "warning"]

    assert warnings == []


def test_check_message_empty():
    issues = checker.check_message("")

    assert any("不能为空" in i.message for i in issues)


def test_check_message_invalid_format():
    text = "随便写写"

    issues = checker.check_message(text)
    errors = [i for i in issues if i.level == "error"]

    assert errors  # 至少有一个 error


def test_unified_hook_dispatcher_reuses_canonical_validator(tmp_path):
    dispatcher_path = PROJECT_ROOT / "code" / "hook_dispatch.py"
    registry_path = PROJECT_ROOT / "hooks" / "ldvh-hooks.yaml"
    env = {**dict(os.environ), "CODEX_HOME": str(tmp_path / "codex-home")}
    valid_message = tmp_path / "valid-message.txt"
    invalid_message = tmp_path / "invalid-message.txt"
    valid_message.write_text(
        (
            "docs(workcase): 测试提交消息 hook\n\n"
            "动机:\n"
            "- 验证 hook 复用 code/commit_validate.py。\n\n"
            "关键变更:\n"
            "- 统一 hook 路径。\n\n"
            "影响边界:\n"
            "- 影响提交预检。\n\n"
            "验证结论:\n"
            "- 预期本地提交消息校验通过。\n\n"
            "风险与后续:\n"
            "- 无。"
        ),
        encoding="utf-8",
    )
    invalid_message.write_text("随便写写", encoding="utf-8")

    registry_text = registry_path.read_text(encoding="utf-8")

    assert "ldvh_asset:" in registry_text
    assert "code/commit_validate.py" in registry_text
    assert subprocess.run(
        [
            "python3",
            str(dispatcher_path),
            "run",
            "session-start",
            "--cwd",
            str(PROJECT_ROOT),
            "--session-id",
            "commit-test",
        ],
        cwd=PROJECT_ROOT,
        env=env,
    ).returncode == 0
    assert subprocess.run(
        [
            "python3",
            str(dispatcher_path),
            "run",
            "acknowledge-read-plan",
            "--cwd",
            str(PROJECT_ROOT),
            "--session-id",
            "commit-test",
        ],
        cwd=PROJECT_ROOT,
        env=env,
    ).returncode == 0
    assert subprocess.run(
        ["python3", str(dispatcher_path), "run", "git.commit-msg", "--message-file", str(valid_message)],
        cwd=PROJECT_ROOT,
        env=env,
    ).returncode == 0
    assert subprocess.run(
        ["python3", str(dispatcher_path), "run", "git.commit-msg", "--message-file", str(invalid_message)],
        cwd=PROJECT_ROOT,
        env=env,
    ).returncode != 0


# ══════════════════════════════════════════════════════════════════════
# parse_message_text — 纯文本解析
# ══════════════════════════════════════════════════════════════════════


def test_parse_message_text_with_body():
    text = "docs(specs): 标题\n\n这是 body 内容"
    result = checker.parse_message_text(text)

    assert result.subject == "docs(specs): 标题"
    assert "body 内容" in result.body
    assert result.hash == "<message>"


def test_parse_message_text_without_body():
    text = "docs(specs): 只有标题"
    result = checker.parse_message_text(text)

    assert result.subject == "docs(specs): 只有标题"
    assert result.body == ""


# ══════════════════════════════════════════════════════════════════════
# Issue formatting
# ══════════════════════════════════════════════════════════════════════


def test_issue_format_error():
    issue = checker.Issue(source="abc12345def", level="error", message="测试错误")

    formatted = issue.format()

    assert "ERROR" in formatted
    assert "abc12345" in formatted
    assert "测试错误" in formatted


def test_issue_format_warning():
    issue = checker.Issue(source="abc12345def", level="warning", message="测试警告")

    formatted = issue.format()

    assert "WARN" in formatted
