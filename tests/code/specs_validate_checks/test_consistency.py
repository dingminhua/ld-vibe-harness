from .common import checker, write_md
from spec_checks import consistency as consistency_checks

def test_consistency_core_implementation_lives_in_spec_checks():
    assert checker.consistency_checks is consistency_checks
    assert consistency_checks.consistency_check.__module__ == "spec_checks.consistency"
    assert consistency_checks.consistency_main.__module__ == "spec_checks.consistency"


def test_consistency_reports_retired_workflow_consumption(tmp_path):
    path = write_md(
        tmp_path / "40-行动编排集合索引.md",
        """
# 工作流程集合索引

## 1. 本文解决的问题

LDVH部署与适配检查读取本文时，应至少确认 active 工作流程输入。
""",
    )

    issues = checker.consistency_retired_semantic_issues([str(tmp_path)])

    assert any(issue.code == "RETIRED_WORKFLOW_CONSUMPTION" and issue.path == path for issue in issues)


def test_consistency_reports_retired_test_source_consumption(tmp_path):
    path = write_md(
        tmp_path / "03.03-行动编排文档规范.md",
        """
# 工作流程文档规范

## 1. 本文解决的问题

具体测试用例进入 11 定义的测试用例事实源或 Code 测试实现。
""",
    )

    issues = checker.consistency_retired_semantic_issues([str(tmp_path)])

    assert any(issue.code == "RETIRED_TEST_SOURCE_CONSUMPTION" and issue.path == path for issue in issues)


def test_consistency_ignores_retired_historical_boundary(tmp_path):
    write_md(
        tmp_path / "02-术语规范.md",
        """
# 术语规范

## 1. 本文解决的问题

LDVH部署与适配检查已退回，待重新设计，只能作为候选输入或历史背景。
""",
    )

    assert checker.consistency_retired_semantic_issues([str(tmp_path)]) == []


# ── 工作模型骨架检查 ──────────────────────────────────────────────


def test_consistency_reports_work_model_section_missing(tmp_path):
    entry_path = tmp_path / "21-Test-测试.md"
    write_md(
        entry_path,
        """
# Test-测试

> 定位：测试

---

## 1. 对象定位与准入条件

## 2. 事实源边界
""",
    )
    entries = [{"number": "21", "title": "21-Test-测试.md", "type": "具体工作模型规范", "status": "active", "path": entry_path, "line": 1}]

    issues = checker.consistency_work_model_skeleton_issues(entries)

    assert any(issue.code == "WORK_MODEL_SECTION_MISSING" for issue in issues)


def test_consistency_reports_work_model_section_title_mismatch(tmp_path):
    entry_path = tmp_path / "21-Test-测试.md"
    write_md(
        entry_path,
        """
# Test-测试

> 定位：测试

---

## 1. 错误的标题名称
""",
    )
    entries = [{"number": "21", "title": "21-Test-测试.md", "type": "具体工作模型规范", "status": "active", "path": entry_path, "line": 1}]

    issues = checker.consistency_work_model_skeleton_issues(entries)

    assert any(issue.code == "WORK_MODEL_SECTION_TITLE_MISMATCH" for issue in issues)


def test_consistency_skips_non_active_work_model(tmp_path):
    entries = [{"number": "21", "title": "21-Test-测试.md", "type": "具体工作模型规范", "status": "removed", "path": tmp_path / "x.md", "line": 1}]

    assert checker.consistency_work_model_skeleton_issues(entries) == []


def test_consistency_reports_collection_index_range_mismatch(tmp_path):
    entries = [{"number": "41", "title": "41-Test-测试.md", "type": "具体工作模型规范", "status": "active", "path": tmp_path / "20-事实模型集合索引.md", "line": 7}]

    issues = checker.consistency_collection_range_issues(entries, "model")

    assert any(issue.code == "COLLECTION_INDEX_RANGE_MISMATCH" for issue in issues)


def test_consistency_reports_work_model_doc_missing(tmp_path):
    entry_path = tmp_path / "21-Not-Exists.md"
    entries = [{"number": "21", "title": "21-Not-Exists.md", "type": "具体工作模型规范", "status": "active", "path": entry_path, "line": 1}]

    issues = checker.consistency_work_model_skeleton_issues(entries)

    assert any(issue.code == "WORK_MODEL_DOC_MISSING" for issue in issues)


# ── 工作流程骨架检查 ──────────────────────────────────────────────


def test_consistency_reports_workflow_section_missing(tmp_path):
    entry_path = tmp_path / "50-Test-测试.md"
    write_md(
        entry_path,
        """
# Test-测试

> 定位：测试

---

## 1. 行动定位与适用场景

## 2. 准入条件
""",
    )
    entries = [{"number": "50", "title": "50-Test-测试.md", "type": "具体工作流程规范", "status": "active", "path": entry_path, "line": 1}]

    issues = checker.consistency_workflow_skeleton_issues(entries)

    assert any(issue.code == "WORKFLOW_SECTION_MISSING" for issue in issues)


def test_consistency_skips_non_active_workflow(tmp_path):
    entries = [{"number": "50", "title": "50-Test-测试.md", "type": "具体工作流程规范", "status": "removed", "path": tmp_path / "x.md", "line": 1}]

    assert checker.consistency_workflow_skeleton_issues(entries) == []


# ── 索引文档强制章节检查 ──────────────────────────────────────────


def test_consistency_reports_index_section_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(checker, "SPECS_DIR", tmp_path)
    write_md(
        tmp_path / "20-事实模型集合索引.md",
        """
# 工作模型集合索引

> 定位：测试

---

## 1. 本文解决的问题

## 2. 与 00 总纲的关系
""",
    )

    issues = checker.consistency_index_skeleton_issues([str(tmp_path)])

    assert any(issue.code == "INDEX_SECTION_MISSING" for issue in issues)


def test_consistency_index_passes_when_required_sections_present(tmp_path, monkeypatch):
    monkeypatch.setattr(checker, "SPECS_DIR", tmp_path)
    write_md(
        tmp_path / "20-事实模型集合索引.md",
        """
# 工作模型集合索引

> 定位：测试

---

## 1. 本文解决的问题

## 2. 与 00 总纲的关系

## 3. 索引范围

## 4. 文档清单

## 5. 维护边界

## 6. 集合关系

## 7. 部署适配检查输入

## 8. 集合一致性检查

## 9. 规范保障要求

## 10. Human Gate 与检查要求

## 11. 待补齐事项
""",
    )

    assert checker.consistency_index_skeleton_issues([str(tmp_path)]) == []


# ── 不推荐裸词检查 ────────────────────────────────────────────────


def test_consistency_reports_bare_term(tmp_path):
    write_md(
        tmp_path / "99-测试.md",
        """
# 测试文档

机制，应被限定。
""",
    )

    issues = checker.consistency_bare_term_issues([str(tmp_path)])

    assert any(issue.code == "BARE_TERM_USAGE" and "机制" in issue.message for issue in issues)


def test_consistency_skips_bare_term_with_modifier(tmp_path):
    write_md(
        tmp_path / "99-测试.md",
        """
# 测试文档

保障机制不应被替代。
""",
    )

    issues = checker.consistency_bare_term_issues([str(tmp_path)])

    assert not any("机制" in issue.message for issue in issues)


def test_consistency_skips_bare_term_in_terminology_spec(tmp_path):
    write_md(
        tmp_path / "02-术语规范.md",
        """
# 术语规范

这个 机制 不得裸用。
""",
    )

    assert checker.consistency_bare_term_issues([str(tmp_path)]) == []


# ── 不推荐表达检查 ────────────────────────────────────────────────


def test_consistency_reports_deprecated_expression(tmp_path):
    write_md(
        tmp_path / "99-测试.md",
        """
# 测试文档

承接项应改为适配项。
""",
    )

    issues = checker.consistency_deprecated_expression_issues([str(tmp_path)])

    assert any(issue.code == "DEPRECATED_EXPRESSION" and "承接项" in issue.message for issue in issues)


def test_consistency_skips_deprecated_in_negative_context(tmp_path):
    write_md(
        tmp_path / "99-测试.md",
        """
# 测试文档

不再使用承接项作为正式术语。
""",
    )

    issues = checker.consistency_deprecated_expression_issues([str(tmp_path)])

    assert not any("承接项" in issue.message for issue in issues)


def test_consistency_skips_deprecated_in_terminology_spec(tmp_path):
    write_md(
        tmp_path / "02-术语规范.md",
        """
# 术语规范

承接项应改为适配项。
""",
    )

    assert checker.consistency_deprecated_expression_issues([str(tmp_path)]) == []


# ── 禁止旧口径检查 ────────────────────────────────────────────────


def test_consistency_reports_forbidden_04_series_range(tmp_path):
    write_md(
        tmp_path / "99-测试.md",
        """
# 测试文档

事实归属范围是 specs/04.01-04.05。
""",
    )

    issues = checker.consistency_forbidden_text_issues([str(tmp_path)])

    assert any(issue.code == "FORBIDDEN_04_SERIES_RANGE" for issue in issues)


def test_consistency_reports_forbidden_trae_cn_rules_dir_path(tmp_path):
    write_md(
        tmp_path / "99-测试.md",
        """
# 测试文档

Trae CN 写入 .trae-cn/rules/ldvh_rules.md。
""",
    )

    issues = checker.consistency_forbidden_text_issues([str(tmp_path)])

    assert any(issue.code == "FORBIDDEN_TRAE_CN_RULES_DIR_PATH" for issue in issues)


def test_consistency_reports_bad_trae_cn_rules_path(tmp_path):
    write_md(
        tmp_path / "99-测试.md",
        """
# 测试文档

Trae CN Rules 写入 .trae-cn/user_rules/other_rules.md。
""",
    )

    issues = checker.consistency_forbidden_text_issues([str(tmp_path)])

    assert any(issue.code == "BAD_TRAE_CN_RULES_PATH" for issue in issues)


def test_consistency_reports_bad_trae_global_rules_path(tmp_path):
    write_md(
        tmp_path / "99-测试.md",
        """
# 测试文档

Trae 国际版写入 .trae/rules/other_rules.md。
""",
    )

    issues = checker.consistency_forbidden_text_issues([str(tmp_path)])

    assert any(issue.code == "BAD_TRAE_GLOBAL_RULES_PATH" for issue in issues)


def test_consistency_reports_forbidden_research_refs_terms(tmp_path):
    write_md(
        tmp_path / "99-测试.md",
        """
# 测试文档

路线图进入 research 入口。
""",
    )

    issues = checker.consistency_forbidden_text_issues([str(tmp_path)])

    assert any(issue.code == "FORBIDDEN_RESEARCH_REFS_TERMS" for issue in issues)


def test_consistency_reports_forbidden_legacy_mechanism_terms(tmp_path):
    write_md(
        tmp_path / "99-测试.md",
        """
# 测试文档

这里定义机制入口。
""",
    )

    issues = checker.consistency_forbidden_text_issues([str(tmp_path)])

    assert any(issue.code == "FORBIDDEN_LEGACY_MECHANISM_TERMS" for issue in issues)


def test_consistency_reports_forbidden_agent_second_definition(tmp_path):
    write_md(
        tmp_path / "99-测试.md",
        """
# 测试文档

Agent 是某种能力。
""",
    )

    issues = checker.consistency_forbidden_text_issues([str(tmp_path)])

    assert any(issue.code == "FORBIDDEN_AGENT_SECOND_DEFINITION" for issue in issues)


# ── 04 系列文件存在性/标题检查 ────────────────────────────────────


def test_consistency_reports_04_series_file_missing(monkeypatch, tmp_path):
    """模拟 04 系列文件缺失场景"""
    original = checker.CONSISTENCY_04_SERIES_FILES
    checker.CONSISTENCY_04_SERIES_FILES = {
        "99-Not-Exists.md": "不存在的文件",
    }

    issues = checker.consistency_04_series_issues()

    assert any(issue.code == "04_SERIES_FILE_MISSING" for issue in issues)

    checker.CONSISTENCY_04_SERIES_FILES = original


def test_consistency_reports_04_series_title_mismatch(monkeypatch, tmp_path):
    """模拟 04 系列文件标题不匹配场景"""
    # 创建一个临时文件，标题不匹配
    fake_file = tmp_path / "04-规范保障与环境适配基础规范.md"
    fake_file.write_text("# 错误的标题\n\n内容", encoding="utf-8")

    original = checker.SPECS_DIR
    checker.SPECS_DIR = tmp_path

    issues = checker.consistency_04_series_issues()

    assert any(issue.code == "04_SERIES_TITLE_MISMATCH" for issue in issues)

    checker.SPECS_DIR = original


def test_consistency_04_series_passes_for_existing_files():
    """实际 04 系列文件都应通过检查"""
    issues = checker.consistency_04_series_issues()

    assert not any(issue.code == "04_SERIES_FILE_MISSING" for issue in issues)
    assert not any(issue.code == "04_SERIES_TITLE_MISMATCH" for issue in issues)
    assert not any(issue.code == "04_SERIES_RETIRED_FILE_PRESENT" for issue in issues)


def test_consistency_reports_retired_04_series_file(monkeypatch, tmp_path):
    """模拟 04 系列退役文件仍存在场景"""
    specs_dir = tmp_path / "specs"
    specs_dir.mkdir()
    retired_file = specs_dir / "04.04-个人环境特别要求规范.md"
    retired_file.write_text("# 个人环境特别要求规范\n", encoding="utf-8")

    original_specs_dir = checker.SPECS_DIR
    original_files = checker.CONSISTENCY_04_SERIES_FILES
    checker.SPECS_DIR = specs_dir
    checker.CONSISTENCY_04_SERIES_FILES = {}

    issues = checker.consistency_04_series_issues()

    assert any(issue.code == "04_SERIES_RETIRED_FILE_PRESENT" for issue in issues)

    checker.SPECS_DIR = original_specs_dir
    checker.CONSISTENCY_04_SERIES_FILES = original_files



# ── 索引越界风险检查 ──────────────────────────────────────────────


def test_consistency_reports_index_overrun_keyword(tmp_path):
    write_md(
        tmp_path / "20-事实模型集合索引.md",
        """
# 工作模型集合索引

## 1. 本文解决的问题

字段契约在此处出现属于越界。
""",
    )

    issues = checker.consistency_index_overrun_issues([str(tmp_path)])

    assert any(issue.code == "INDEX_OVERRUN_KEYWORD" and "字段契约" in issue.message for issue in issues)


def test_consistency_reports_index_overrun_multiple_keywords(tmp_path):
    write_md(
        tmp_path / "40-行动编排集合索引.md",
        """
# 工作流程集合索引

## 1. 本文解决的问题

状态机和执行流程是索引文档中的越界内容。
""",
    )

    issues = checker.consistency_index_overrun_issues([str(tmp_path)])

    assert any(issue.code == "INDEX_OVERRUN_KEYWORD" and "状态机" in issue.message for issue in issues)


def test_consistency_skips_index_overrun_in_non_index_doc(tmp_path):
    write_md(
        tmp_path / "21-ADR-决策记录.md",
        """
# ADR 决策记录

## 1. 本文解决的问题

字段契约和状态机是 ADR 的核心内容。
""",
    )

    issues = checker.consistency_index_overrun_issues([str(tmp_path)])

    assert not any(issue.code == "INDEX_OVERRUN_KEYWORD" for issue in issues)


def test_consistency_skips_index_overrun_in_current_20_40_main_docs(tmp_path):
    write_md(
        tmp_path / "21-WorkCase-工作项.md",
        """
# WorkCase-工作项

## 1. 对象定位与准入条件

字段契约和对象关系是具体工作模型主文件的正文内容。
""",
    )
    write_md(
        tmp_path / "40-action-orchestration-design-audit-行动编排设计审核.md",
        """
# action-orchestration-design-audit-行动编排设计审核

## 1. 行动定位与适用场景

Scenario、Gate 触发条件、执行流程和事实源回写是具体工作流程主文件的正文内容。
""",
    )

    issues = checker.consistency_index_overrun_issues([str(tmp_path)])

    assert not any(issue.code == "INDEX_OVERRUN_KEYWORD" for issue in issues)


def test_consistency_skips_index_overrun_in_code_block(tmp_path):
    write_md(
        tmp_path / "20-事实模型集合索引.md",
        """
# 工作模型集合索引

## 1. 本文解决的问题

```markdown
字段契约不应被检测。
```
""",
    )

    issues = checker.consistency_index_overrun_issues([str(tmp_path)])

    assert not any(issue.code == "INDEX_OVERRUN_KEYWORD" for issue in issues)


def test_consistency_skips_index_overrun_in_negative_context(tmp_path):
    write_md(
        tmp_path / "20-事实模型集合索引.md",
        """
# 工作模型集合索引

## 1. 本文解决的问题

索引文档不得包含字段契约定义。
""",
    )

    issues = checker.consistency_index_overrun_issues([str(tmp_path)])

    assert not any(issue.code == "INDEX_OVERRUN_KEYWORD" for issue in issues)


def test_consistency_skips_index_overrun_in_boundary_context(tmp_path):
    write_md(
        tmp_path / "40-行动编排集合索引.md",
        """
# 工作流程集合索引

## 1. 本文解决的问题

本文不定义具体工作流程的 Context、Scenario、Gate、执行流程或事实源回写要求。
让本文定义具体流程的 Context、Scenario、Gate 或执行流程时应触发 Human Gate。
该流程的核心 Context、Scenario、Gate、执行和事实源回写是什么。
""",
    )

    issues = checker.consistency_index_overrun_issues([str(tmp_path)])

    assert not any(issue.code == "INDEX_OVERRUN_KEYWORD" for issue in issues)


def test_consistency_removed_alias_does_not_match_number_range():
    assert not checker.consistency_line_has_removed_alias("对应 41-59 active 工作流程规范", ["41"])
    assert checker.consistency_line_has_removed_alias("对应 41 active 工作流程规范", ["41"])
