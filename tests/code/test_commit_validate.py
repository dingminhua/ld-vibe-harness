import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[2] / "code" / "commit_validate.py"
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
        subject="spec(specs): 采用约定式提交规范",
        body=(
            "明确 Git 提交记录使用 Conventional Commits。\n"
            "提交信息使用格式化首行和自然语言正文说明变更内容。"
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
        subject="feat(api)!: 调整公开接口参数",
        body="旧参数不再兼容，调用方需要改为传入新的结构化参数。",
    )

    issues = checker.check_commit(commit)
    errors = [i for i in issues if i.level == "error"]

    assert errors == []


def test_footer_is_disallowed():
    commit = make_commit(
        subject="feat(api)!: 调整公开接口参数",
        body="BREAKING CHANGE: 旧参数不再兼容。",
    )

    issues = checker.check_commit(commit)
    errors = [i for i in issues if i.level == "error"]

    assert any("不得使用 commit footer" in i.message for i in errors)


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
        body="说明本次文档调整内容。",
    )

    issues = checker.check_commit(commit)
    errors = [i for i in issues if i.level == "error"]

    assert errors == []


def test_scope_not_recommended_warns():
    commit = make_commit(subject="feat(unknown-scope): 新功能", body="说明本次功能调整内容。")

    issues = checker.check_commit(commit)
    warnings = [i for i in issues if i.level == "warning"]

    assert any("scope" in i.message and "不在推荐枚举" in i.message for i in warnings)


def test_subject_too_long():
    long_subject = "a" * 100
    commit = make_commit(subject=f"docs(specs): {long_subject}", body="说明")

    issues = checker.check_commit(commit)
    warnings = [i for i in issues if i.level == "warning"]

    assert any("超过" in i.message and "字符" in i.message for i in warnings)


def test_missing_trailers_do_not_warn():
    commit = make_commit(subject="docs(specs): 测试", body="说明本次测试内容。")

    issues = checker.check_commit(commit)
    warnings = [i for i in issues if i.level == "warning"]

    assert not any("Refs" in i.message or "Human-Gate" in i.message or "Verification" in i.message or "Risk" in i.message for i in warnings)


def test_ldvh_fixed_footers_are_disallowed():
    commit = make_commit(
        subject="docs(specs): 测试禁用字段",
        body=(
            "说明本次测试内容。\n\n"
            "Refs: memo-0001\n"
            "Human-Gate: 用户确认\n"
            "Verification: pytest\n"
            "Risk: 无"
        ),
    )

    issues = checker.check_commit(commit)
    errors = [i for i in issues if i.level == "error"]

    assert any("不得使用 LDVH 固定 footer 字段" in i.message for i in errors)


def test_missing_chinese_errors():
    commit = make_commit(subject="docs(specs): test no chinese", body="no chinese here")

    issues = checker.check_commit(commit)
    errors = [i for i in issues if i.level == "error"]

    assert any("必须包含中文字符" in i.message for i in errors)


# ══════════════════════════════════════════════════════════════════════
# check_message — 提交前预检
# ══════════════════════════════════════════════════════════════════════


def test_check_message_valid():
    text = (
        "docs(specs): 更新文档\n\n"
        "更新内容。"
    )

    issues = checker.check_message(text)
    errors = [i for i in issues if i.level == "error"]

    assert errors == []


def test_check_message_requires_body_for_staged_specs_file():
    text = "spec(specs): 明确提交正文语义"

    issues = checker.check_message(text, touched_files=["specs/10-Git提交规范.md"])
    errors = [i for i in issues if i.level == "error"]

    assert any("要求 commit body 非空" in i.message for i in errors)


def test_body_mainly_commands_warns():
    commit = make_commit(
        subject="spec(specs): 明确提交正文语义",
        body=(
            "npm run web:check\n"
            "python3 code/specs_validate.py doc specs\n"
            "git diff --check"
        ),
    )

    issues = checker.check_commit(commit)
    warnings = [i for i in issues if i.level == "warning"]

    assert any("主要由检查命令组成" in i.message for i in warnings)


def test_check_message_empty():
    issues = checker.check_message("")

    assert any("不能为空" in i.message for i in issues)


def test_check_message_invalid_format():
    text = "随便写写"

    issues = checker.check_message(text)
    errors = [i for i in issues if i.level == "error"]

    assert errors  # 至少有一个 error


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
