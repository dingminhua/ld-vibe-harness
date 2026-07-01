# 15A runtime 自动入口复核

文件状态：阶段 15 记录。本文只记录当前环境入口复核结论，不安装新入口，不声明 manual 入口已经自动触发。

## 复核目标

阶段 15 用于再次确认当前仓库是否存在真实可接入的 session start、pre tool use、completion claim、tool hook、completion hook、Codex repo instruction 或外部 runtime adapter 自动入口。

判定依据沿用 `specs/01-保障与衔接.md` §6 与 `01.Att.03-06`：

1. 真实触发点；
2. 稳定 payload；
3. 失败阻断或失败处理；
4. 安装状态检查；
5. 回滚方式；
6. 测试或可复现验证；
7. Human Gate。

缺少任一关键条件时，不得声明 `integrated`。

## 本次复核结果

命令：

```bash
python3 code/environment_entry_audit.py --format json
python3 code/environment_status.py --format json
```

结论：

1. `git.commit-msg` 仍是当前唯一 integrated 自动入口；
2. `manual.runtime_adapter`、`manual.session_start`、`manual.pre_tool_use` 和 `manual.completion_claim` 均 available/manual-ready，但 `integrated=false`；
3. `runtime.session_start.auto`、`runtime.pre_tool_use.auto`、`runtime.completion_claim.auto` 和 `runtime.adapter.auto` 仍为 `deferred`；
4. `rules.top_level_mechanism` 和 `skills.top_level_mechanism` 仍为 `removed_top_level`；
5. `codex.repo-instructions` 当前为 `absent`；
6. 本次复核 diagnostics 为 0，authorization 为 `none`。

## 决策

阶段 15 不新增代码能力，不安装 Hook，不创建 repo instruction，不恢复 Rules / Skill 顶层机制。

后续只有发现真实触发点，并能补齐 payload、失败处理、安装状态、回滚、测试和 Human Gate 时，才进入具体接入实现。否则 session start、pre tool use、completion claim、tool hook、completion hook、Codex repo instruction 和 external runtime adapter 继续保持后置。

## 验证

本阶段验证入口：

1. `python3 code/environment_entry_audit.py --format json`；
2. `python3 code/environment_status.py --format json`；
3. `python3 code/test_runner.py smoke`；
4. `python3 -m pytest tests/code/test_ldvh_specs_validate.py::test_environment_entry_audit_marks_rules_and_skills_removed_top_level tests/code/test_ldvh_specs_validate.py::test_environment_entry_audit_does_not_treat_agent_file_as_integration tests/code/test_ldvh_specs_validate.py::test_environment_status_reports_commit_hook_and_manual_entries -q`。
