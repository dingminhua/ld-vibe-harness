# Core Loop Skill 与 Rules 入口 Spec

## Why

事实模型规范（Intent/Task/Evidence）已就绪，但 AI 进入项目后仍不知道该干什么、怎么走流程。需要创建 ldvh-intake 和 ldvh-close Skill 让 AI 能创建 Intent/Task、关闭 Task，最小闭环可运行；同时更新 L0/L1 Rules 加入 Core Loop 入口，让 AI 进入项目后能自动识别当前阶段。

## What Changes

- 新增 ldvh-intake Skill：用户意图 → 识别场景 → 创建 Intent/Task 草案 → Human Gate 确认
- 新增 ldvh-close Skill：closure_evidence 校验 → Change 记录 → 状态回写 → Human Gate 确认
- 更新 L0 工作区规则：加入 Core Loop 阶段识别入口
- 更新 L1 项目规则：加入 Core Loop 阶段判断和 Skill 路由

## Impact

- Affected specs: specs/11.02-Skill机制规范.md、specs/24-Intent-意图.md、specs/28-Evidence-验证证据.md、specs/31-Task-任务.md
- Affected code: .trae/skills/ldvh-intake/SKILL.md、.trae/skills/ldvh-close/SKILL.md、.trae/rules/ldvh-l0-rules.md、.trae/rules/ldvh-l1-rules.md

## ADDED Requirements

### Requirement: ldvh-intake Skill

系统 SHALL 提供 ldvh-intake Skill，在用户表达意图时由 AI 主控应用，完成从意图到 Intent/Task 草案的创建流程。

#### Scenario: 用户表达需要跨任务追踪的意图
- **WHEN** 用户表达了满足 Intent 准入条件的意图（跨任务追踪、影响范围超出单次操作、需要跨会话连续性）
- **THEN** AI 应用 ldvh-intake Skill，识别场景，创建 Intent 草案，通过 AskUserQuestion 请求用户确认后写入 ldvh-base/intents/

#### Scenario: 用户表达简单请求
- **WHEN** 用户表达了不满足 Intent 准入条件的简单请求
- **THEN** AI 应用 ldvh-intake Skill，识别为简单请求，直接创建 Task 草案，通过 AskUserQuestion 请求用户确认后写入 ldvh-base/tasks/

#### Scenario: 用户取消创建
- **WHEN** 用户在 Human Gate 确认时选择取消
- **THEN** Skill 流程停止，不写入任何事实源

### Requirement: ldvh-close Skill

系统 SHALL 提供 ldvh-close Skill，在 Task 满足关闭条件时由 AI 主控应用，完成从审查到关闭的流程。

#### Scenario: Task 满足关闭条件
- **WHEN** Task 处于 review_needed 状态，且 closure_evidence 已填写，且关联 Evidence 的 verification_result 不为 fail
- **THEN** AI 应用 ldvh-close Skill，校验关闭条件，通过 AskUserQuestion 请求用户确认后更新 Task 状态为 closed

#### Scenario: Task 缺少 closure_evidence
- **WHEN** Task 处于 review_needed 状态，但 closure_evidence 未填写
- **THEN** AI 提示用户补充 closure_evidence，不执行关闭

#### Scenario: 关联 Evidence 验证失败
- **WHEN** Task 处于 review_needed 状态，但关联 Evidence 的 verification_result 为 fail
- **THEN** AI 提示用户验证失败，建议退回 Task 到 executing 状态

### Requirement: Core Loop Rules 入口

L0 工作区规则 SHALL 包含 Core Loop 阶段识别入口，AI 进入项目后能判断当前应处于 Intent → Plan → Execute → Verify → Record → Learn 的哪个阶段。

L1 项目规则 SHALL 包含 Core Loop 阶段与 Skill 的路由关系，AI 能根据当前阶段推荐使用 ldvh-intake 或 ldvh-close Skill。

#### Scenario: AI 进入项目
- **WHEN** AI 进入项目，读取 L0/L1 Rules
- **THEN** AI 能识别当前 Core Loop 阶段，推荐对应 Skill

## MODIFIED Requirements

无

## REMOVED Requirements

无
