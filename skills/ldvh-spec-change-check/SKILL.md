---
name: "ldvh-spec-change-check"
description: "Checks LDVH spec changes against required validation and governance steps. Invoke after editing specs or before committing spec changes."
---

# LDVH Spec Change Check

## 定位

本 Skill 用于在 LDVH specs 变更后执行最小治理检查，帮助主控 AI 确认变更是否满足正式规范、事实源边界、验证和交还要求。

本 Skill 是 Skill 部署入口资产，只承载可复用 SOP，不新增稳定规则，不替代 specs、Code、Human Gate、Agent 审查或 Git 文件事实源。

## 触发条件

在以下场景调用：

1. 修改 `specs/` 正式规范后；
2. 修改 `rules/`、`skills/`、`agents/`、`hooks/` 等入口资产且影响 04 系列边界时；
3. 准备提交规范或入口资产变更前；
4. 用户要求检查 LDVH 规范变更是否可提交时。

## 不适用场景

以下场景不调用本 Skill：

1. 只回答概念问题且未修改文件；
2. 只修改 Web、Code 或测试实现且不影响规范或入口资产边界；
3. 需要独立语义审查时，应交给 Agent 入口或由主控 AI 按 Agent 降级方式执行；
4. 需要 Human Gate 判断时，本 Skill 只能提醒暂停，不能替 Human 决策。

## 必读入口

执行前至少读取或确认：

1. `rules/LDVH-AI-ENTRY.md`；
2. `specs/04.02-LDVH能力保障规范.md`；
3. `specs/04.03-环境适配规范.md`；
4. 本次变更涉及的正式规范或入口资产文件。

## 输入

主控 AI 应提供：

1. 本次变更目标；
2. 修改文件清单；
3. 是否涉及 Rules、Skill、Agent、Hook 部署入口；
4. 已运行或计划运行的验证命令；
5. 是否存在需要 Human Gate 的动作。

## 流程

1. 确认变更文件是否属于正式规范、入口资产、Code、Web、测试或临时上下文；
2. 对 specs 变更，检查是否遵守规则态写法，不记录状态实例、执行结果、历史过程或不可查询状态；
3. 对入口资产变更，检查是否保持薄入口，不复制完整规范正文，不把 Command、Code、Web、CLI、MCP、CI 或文档写成第五类部署入口；
4. 对 Skill 变更，检查名称是否使用 `ldvh-` 前缀，正文是否只写定位、输入、输出、流程、失败处理、STOP 点、Human Gate、回写和交还；
5. 对 Agent 变更，检查输出是否必须回到主控或 Human，不能直接生效；
6. 对 Hook 变更，检查是否区分原生 Hook、Skill 模拟、Command 触发、CI 或人工检查清单，不能把降级实现写成原生完整支持；
7. 运行或要求运行适用验证，至少包括 `python3 code/specs_validate.py all`；
8. 若变更涉及 Code 测试或验证器行为，运行 `python3 -m pytest tests/code/test_specs_validate.py` 或说明不适用原因；
9. 执行 `git diff --check` 检查目标文件空白问题；
10. 汇总通过项、失败项、Human Gate 项、降级项和后续动作。

## STOP 点

遇到以下情况必须暂停并交还主控或 Human：

1. 变更会改变 Rules、Skill、Agent、Hook、Code、Web、Command 或 Human Gate 的边界；
2. 变更允许入口资产成为最终事实源；
3. 变更声明某环境能力完整可用但缺少可查询证据；
4. 变更新增自动触发、受控写入或危险权限；
5. 验证失败且无法在当前任务内修复；
6. 用户目标、目标项目或事实源边界不清楚。

## 输出

输出必须包含：

1. 检查结论；
2. 修改文件分类；
3. 入口资产边界检查结果；
4. 验证命令和结果；
5. Human Gate 或 STOP 点；
6. 可提交性判断；
7. 需要回写的事实源、Task、ADR、Memo 或临时上下文。

## 交还规则

本 Skill 输出不是稳定事实源。主控 AI 只能在读取输出、必要验证和 Human Gate 后采纳结论，并将稳定事实回写到对应 Git 文件事实源。