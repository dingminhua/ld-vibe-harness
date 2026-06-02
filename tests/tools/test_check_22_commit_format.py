import importlib.util
import subprocess
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(__file__).resolve().parents[2] / "tools" / "check_22_commit_format.py"
spec = importlib.util.spec_from_file_location("check_22_commit_format", MODULE_PATH)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def make_commit(hash, subject, body=""):
    """构造 CommitInfo 对象。"""
    full = f"{subject}\n\n{body}".strip() if body else subject
    return checker.CommitInfo(hash=hash, subject=subject, body=body, full_message=full)


def issues_messages(issues):
    return [i.message for i in issues]


def test_valid_type_and_subject():
    commit = make_commit("a" * 40, "docs: add README")
    errors = [i for i in checker.check_commit(commit) if i.level == "error"]
    assert errors == []


def test_valid_type_with_scope():
    commit = make_commit("a" * 40, "spec(specs): update rules")
    errors = [i for i in checker.check_commit(commit) if i.level == "error"]
    assert errors == []


def test_invalid_type():
    commit = make_commit("a" * 40, "unknown: some change")
    issues = checker.check_commit(commit)
    msgs = issues_messages(issues)
    assert any("不在有效枚举中" in m for m in msgs)


def test_subject_too_long():
    long_subject = "docs: " + "x" * 73
    commit = make_commit("a" * 40, long_subject)
    issues = checker.check_commit(commit)
    msgs = issues_messages(issues)
    assert any("超过 72 字符" in m for m in msgs)


def test_empty_subject_format_error():
    # "docs:   " — 冒号后只有空格，regex 不匹配，返回格式错误
    commit = make_commit("a" * 40, "docs:   ")
    issues = checker.check_commit(commit)
    msgs = issues_messages(issues)
    assert any("第一行格式不符合" in m for m in msgs)


def test_missing_refs_warning():
    commit = make_commit("a" * 40, "docs: add feature")
    issues = checker.check_commit(commit)
    msgs = issues_messages(issues)
    assert any("缺少 Refs" in m for m in msgs)


def test_with_refs_no_warning():
    commit = make_commit(
        "a" * 40,
        "docs: add feature",
        "Some body text\n\nRefs: 22-Change-变更记录"
    )
    issues = checker.check_commit(commit)
    msgs = issues_messages(issues)
    assert not any("缺少 Refs" in m for m in msgs)


def test_unrecognized_scope_warning():
    commit = make_commit("a" * 40, "docs(custom): add feature")
    issues = checker.check_commit(commit)
    msgs = issues_messages(issues)
    assert any("不在推荐枚举中" in m for m in msgs)


def test_no_header_format():
    commit = make_commit("a" * 40, "just a message without format")
    issues = checker.check_commit(commit)
    msgs = issues_messages(issues)
    assert any("第一行格式不符合" in m for m in msgs)


def test_multiple_issues():
    commit = make_commit("a" * 40, "unknown: some change")
    issues = checker.check_commit(commit)
    msgs = issues_messages(issues)
    assert any("不在有效枚举中" in m for m in msgs)
    assert any("缺少 Refs" in m for m in msgs)


def test_all_valid_types():
    for t in checker.VALID_TYPES:
        commit = make_commit("a" * 40, f"{t}: some change")
        issues = checker.check_commit(commit)
        # 只有 Refs 缺失 warning，无 error
        errors = [i for i in issues if i.level == "error"]
        assert errors == [], f"type '{t}' should be valid"


def test_all_recommended_scopes():
    for s in checker.RECOMMENDED_SCOPES:
        commit = make_commit("a" * 40, f"docs({s}): some change")
        issues = checker.check_commit(commit)
        warnings = [i for i in issues if "不在推荐枚举中" in i.message]
        assert warnings == [], f"scope '{s}' should be recognized"


def test_subject_at_boundary():
    # 恰好 72 字符
    commit = make_commit("a" * 40, "docs: " + "x" * 66)
    issues = checker.check_commit(commit)
    msgs = issues_messages(issues)
    assert not any("超过 72 字符" in m for m in msgs)


def test_refs_with_multiple_objects():
    commit = make_commit(
        "a" * 40,
        "docs: add feature",
        "Body\n\nRefs: 22-Change-变更记录, ADR-0001"
    )
    issues = checker.check_commit(commit)
    msgs = issues_messages(issues)
    assert not any("缺少 Refs" in m for m in msgs)


@patch("subprocess.run")
def test_git_log_parsing(mock_run):
    mock_run.return_value = subprocess.CompletedProcess(
        args=[], returncode=0,
        stdout="abc12345\x00feat: add feature\x00Body text\n\nRefs: ADR-0001\x1e",
        stderr=""
    )
    commits = checker.git_log(1)
    assert len(commits) == 1
    assert commits[0].hash == "abc12345"
    assert commits[0].subject == "feat: add feature"
    assert "Refs: ADR-0001" in commits[0].body


@patch("subprocess.run")
def test_git_log_failure(mock_run, capsys):
    mock_run.return_value = subprocess.CompletedProcess(
        args=[], returncode=1, stdout="", stderr="fatal: not a git repository"
    )
    try:
        checker.git_log(1)
    except SystemExit:
        pass
    # 不验证具体输出，只验证不会崩溃


# -------- check_message 提交前预检 --------


def test_check_message_valid():
    msg = "spec(tools): add pre-commit check\n\nBody text\n\nRefs: 22-Change-变更记录"
    issues = checker.check_message(msg)
    errors = [i for i in issues if i.level == "error"]
    assert errors == []


def test_check_message_invalid_type():
    msg = "badtype: broken"
    issues = checker.check_message(msg)
    msgs = issues_messages(issues)
    assert any("不在有效枚举中" in m for m in msgs)


def test_check_message_empty():
    issues = checker.check_message("")
    msgs = issues_messages(issues)
    assert any("不能为空" in m for m in msgs)


def test_check_message_no_header_format():
    msg = "just a regular sentence without proper format"
    issues = checker.check_message(msg)
    msgs = issues_messages(issues)
    assert any("第一行格式不符合" in m for m in msgs)


def test_check_message_too_long():
    msg = "docs: " + "x" * 73
    issues = checker.check_message(msg)
    msgs = issues_messages(issues)
    assert any("超过 72 字符" in m for m in msgs)


# -------- parse_message_text --------


def test_parse_message_text_simple():
    commit = checker.parse_message_text("feat: add feature")
    assert commit.hash == "<message>"
    assert commit.subject == "feat: add feature"
    assert commit.body == ""
    assert commit.full_message == "feat: add feature"


def test_parse_message_text_with_body():
    text = "feat: add feature\n\nSome description\nMore details\n\nRefs: ADR-0001"
    commit = checker.parse_message_text(text)
    assert commit.hash == "<message>"
    assert commit.subject == "feat: add feature"
    assert "Some description" in commit.body
    assert "Refs: ADR-0001" in commit.full_message


# -------- show_format --------


def test_show_format_output(capsys):
    checker.show_format()
    captured = capsys.readouterr()
    assert "正确的 commit message 格式" in captured.out
    assert "<type>(<scope>): <subject>" in captured.out
    assert "feat" in captured.out
    assert "specs" in captured.out