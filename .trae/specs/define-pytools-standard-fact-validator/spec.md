# 定义 PyTools 标准并实现最小 Fact Validator Spec

## Why

LDVH 已有多个 PyTools，但 CLI、输出、Issue 表达、退出码和 Contract 消费方式尚未形成统一标准。Intent / Task / Evidence 精简版事实对象已落地，当前最小闭环需要一个最小 Fact Validator 来校验 `ldvh-base/` YAML，避免 Dogfood 阶段依赖人工逐项检查。

## What Changes

- 定义 PyTools 最小统一标准，作为新工具实现和旧工具渐进迁移的依据
- 新增最小 Fact Validator：`tools/check_fact_model.py`
- 为最小 Fact Validator 新增 pytest 测试：`tests/tools/test_check_fact_model.py`
- 不一次性重构已有 PyTools；仅在新工具中采用标准
- 不实现复杂 Contract parser、自动修复、受控写入、Web 展示或数据库/缓存

## Impact

- Affected specs: `specs/12.01-Tools辅助规范.md`、`specs/24.06-Contract.md`、`specs/28.06-Contract.md`、`specs/31.06-Contract.md`、`specs/evals/17-LDVH-Gstack-Trae融合产品方向共识.md`
- Affected code: `tools/check_fact_model.py`、`tests/tools/test_check_fact_model.py`

## ADDED Requirements

### Requirement: PyTools 最小统一标准

系统 SHALL 为新增 PyTools 采用最小统一标准，包括 CLI、输出、Issue、退出码、只读/写入边界和测试约定。

#### Scenario: 新增只读校验工具
- **WHEN** 新增只读校验类 PyTools
- **THEN** 工具应提供清晰 CLI、结构化 Issue 输出、确定性退出码，并不得修改任何事实源文件

#### Scenario: 工具校验通过
- **WHEN** 工具检查目标文件且未发现 error
- **THEN** 工具应返回 exit code 0，并输出通过摘要

#### Scenario: 工具校验失败
- **WHEN** 工具检查目标文件发现 error
- **THEN** 工具应返回 exit code 1，并输出包含文件、字段或规则来源的错误信息

#### Scenario: 工具输入无效
- **WHEN** 工具收到不存在路径、无法识别的对象类型或 YAML 解析失败
- **THEN** 工具应返回 exit code 2，并输出输入或解析错误原因

### Requirement: 最小 Fact Validator

系统 SHALL 提供 `tools/check_fact_model.py`，用于校验 Intent、Task、Evidence 三类事实实例 YAML。

#### Scenario: 校验 Intent 文件
- **WHEN** 用户执行 `python3 tools/check_fact_model.py ldvh-base/intents/intent-0001-example.yaml`
- **THEN** 工具应校验文件名、必填字段、`id` 格式、`type: intent`、`status` 枚举和基础 list 字段类型

#### Scenario: 校验 Task 文件
- **WHEN** 用户执行 `python3 tools/check_fact_model.py ldvh-base/tasks/task-0001-example.yaml`
- **THEN** 工具应校验文件名、必填字段、`id` 格式、`type: task`、`status` 枚举，以及 closed 状态下的 `closed_at` 和 `closure_evidence` 条件必填

#### Scenario: 校验 Evidence 文件
- **WHEN** 用户执行 `python3 tools/check_fact_model.py ldvh-base/evidence/ev-0001-example.yaml`
- **THEN** 工具应校验文件名、必填字段、`id` 格式、`type: evidence`、`status` 枚举、`evidence_type` 枚举、`verification_result` 枚举，以及 `source_task` / `source_adr` 至少填写一个

#### Scenario: 批量校验目录
- **WHEN** 用户执行 `python3 tools/check_fact_model.py ldvh-base/tasks/`
- **THEN** 工具应递归或直接扫描该目录下的 `.yaml` 文件并逐个校验，输出汇总结果

#### Scenario: 只读边界
- **WHEN** 工具执行校验
- **THEN** 工具不得创建、修改或删除任何事实源文件

### Requirement: Fact Validator 测试

系统 SHALL 为 `tools/check_fact_model.py` 提供 pytest 测试，覆盖合法样例、非法样例、输入错误和目录批量校验。

#### Scenario: 测试合法样例
- **WHEN** 测试运行合法 Intent / Task / Evidence YAML 样例
- **THEN** 工具应返回 exit code 0

#### Scenario: 测试非法样例
- **WHEN** 测试运行缺少必填字段、状态非法、type 不匹配或文件名非法的样例
- **THEN** 工具应返回 exit code 1 或 2，并包含明确错误信息

## MODIFIED Requirements

### Requirement: Tools 测试与验收原则

`tools/` 下新增 Python 文件时，必须在 `tests/tools/` 下新增对应 pytest 测试文件。本次新增 `tools/check_fact_model.py` 必须同步新增 `tests/tools/test_check_fact_model.py`。

## REMOVED Requirements

无
