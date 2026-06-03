# 规范判断回原文与规则回流 specs 正式化 Spec

## Why

当前“规范判断必须回原文”和“重要规则应回流 specs”的原则已经写入 L1 Rules 与 evals/17，但这些不是可迁移的正式规范来源。为了避免换环境初始化后遗忘，需要将该原则沉淀进 11 系列正式规范，让 Rules 只作为运行时投影，而不是第二事实源。

## What Changes

- 在 `specs/11-LDVH-AI协作规范.md` 中新增通用要求：涉及机制、事实模型、状态机、部署边界或目录边界判断时，必须先定位并读取对应规范原文，再结合当前实例状态判断
- 在 `specs/11.01-Rules机制规范.md` 中新增规则回流要求：Rules 中发现具有跨环境复用价值的稳定原则时，应回流 specs；Rules 只能保留入口摘要、必读提醒或压缩保护
- 在 `specs/11.02-Skill机制规范.md` 中新增 Skill 部署判断检查：判断 LDVH 通用 Skill 是否落地时必须同时检查规范部署边界、工作区顶层 `.trae/skills/`、YAML `name`、文件结构和 Human Gate
- 更新 `specs/evals/17-LDVH-Gstack-Trae融合产品方向共识.md`，标记相关共识已回流 11 系列正式规范
- 不新增 Tools、不新增 Skill、不部署 Skill、不创建 ADR 实例

## Impact

- Affected specs: `specs/11-LDVH-AI协作规范.md`、`specs/11.01-Rules机制规范.md`、`specs/11.02-Skill机制规范.md`、`specs/evals/17-LDVH-Gstack-Trae融合产品方向共识.md`
- Affected code: 无

## ADDED Requirements

### Requirement: 规范判断必须回到权威原文

系统 SHALL 要求 AI 在涉及机制、事实模型、状态机、部署边界、目录边界或规则归属判断时，先定位并读取对应正式规范原文，再给出结论。

#### Scenario: 判断 Skill 是否部署正确
- **WHEN** AI 需要判断某个 `ldvh-*` Skill 是否已落地或可调用
- **THEN** AI 必须先读取 `specs/11.02-Skill机制规范.md` 的命名与部署边界，再检查工作区顶层 `.trae/skills/` 与实际 Skill 文件

#### Scenario: 判断某条规则是否应该写入 Rules
- **WHEN** AI 发现一条新规则或长期约束
- **THEN** AI 必须先判断该规则是否已有 specs 权威来源；若具备跨环境复用价值，应优先回流 specs，再由 Rules 保留入口摘要

#### Scenario: 目录现状与规范记忆冲突
- **WHEN** 目录现状、聊天记忆或工具结果与规范记忆发生冲突
- **THEN** AI 必须以正式 specs 原文为判断依据，并说明当前目录现状是否符合规范

### Requirement: 错误模式转化为检查项

系统 SHALL 要求 AI 在发现自己依赖错误记忆、跳过规范原文、混淆层级或误判部署边界时，把错误模式转化为可执行检查项。

#### Scenario: 出现机制部署误判
- **WHEN** AI 发现自己误判了 Skill、Rules、Agent 或 Tools 的部署边界
- **THEN** AI 应将该误判沉淀为检查项，包含触发场景、必读原文、检查顺序和停止条件

### Requirement: Rules 是运行时投影而不是规范来源

系统 SHALL 明确 Rules 对正式规范的关系：Rules 可以承载入口摘要、压缩保护、场景触发和项目专属硬约束，但不得长期承载具有跨环境复用价值的框架原则正文。

#### Scenario: L1 规则新增长期原则
- **WHEN** L1 Rules 新增了具有 LDVH 框架级复用价值的长期原则
- **THEN** 该原则应回流到对应 specs 正式规范，L1 Rules 只保留摘要和规范引用

### Requirement: Skill 部署判断标准化

系统 SHALL 在 Skill 机制规范中定义 LDVH 通用 Skill 部署判断检查。

#### Scenario: 判断 LDVH 通用 Skill 可调用性
- **WHEN** AI 判断 `ldvh-intake`、`ldvh-close` 或其他 `ldvh-*` Skill 是否可调用
- **THEN** AI 应检查：11.02 部署边界、工作区顶层 `.trae/skills/ldvh-*`、`SKILL.md` YAML `name` 与目录一致、文件结构符合 11.02 §5、创建或迁移是否经过 Human Gate

## MODIFIED Requirements

### Requirement: 11 系列协作规范治理

11 系列规范应明确：机制判断不只检查当前文件或目录，还必须回到对应正式规范原文；机制运行时入口（Rules / Skill / Agent）不是稳定事实的最终来源。

## REMOVED Requirements

无
