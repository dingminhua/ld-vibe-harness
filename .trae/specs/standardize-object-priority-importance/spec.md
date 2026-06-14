# 统一工作对象优先级与重要程度 Spec

## Why
LDVH 当前工作对象中存在 `priority`（优先级）、`severity`（严重程度）、`risk_assessment`（风险判断）等相近字段，容易混淆“执行调度”“价值判断”和“影响描述”。需要在上位工作模型规范中统一判断标准，并把具体字段落到合适对象，避免重复事实源和对象职责漂移。

## What Changes
- 在 `05-工作模型基础规范.md` 中新增 `priority`（优先级）和 `importance`（重要程度）的统一语义、枚举、判断标准和对象适用边界。
- 在 `27-TaskPlan-任务计划.md` 中新增 `priority`（优先级）和 `importance`（重要程度）字段。
- 在 `25-Memo-备忘.md` 中将 `priority`（优先级）替换为 `importance`（重要程度）。
- 在 `26-Task-任务.md` 中移除 `risk_assessment`（风险判断）字段，将执行风险、约束和降级方式并入现有叙述字段。
- 在 `23-Pitfall-踩坑.md` 中移除 `severity`（严重程度）字段，将影响描述并入现有叙述字段。
- 同步 Code 校验、CLI 创建模板、Web 展示和现有 YAML 实例，使字段契约、实例和工具一致。
- **BREAKING**：既有 Memo YAML 的 `priority`（优先级）需要迁移为 `importance`（重要程度）。
- **BREAKING**：既有 Task YAML 的 `risk_assessment`（风险判断）字段已移除。
- **BREAKING**：既有 Pitfall YAML 的 `severity`（严重程度）字段已移除。

## Impact
- Affected specs: `specs/05-工作模型基础规范.md`、`specs/25-Memo-备忘.md`、`specs/27-TaskPlan-任务计划.md`、`specs/26-Task-任务.md`、`specs/23-Pitfall-踩坑.md`、必要时 `specs/08-Web信息同步实现规范.md`
- Affected code: `code/fact_validate.py`、`code/fact_cli.py`、Web 对象展示和 Memo 创建入口、`ldvh-base/` 下 Memo、TaskPlan、Task、Pitfall 实例

## ADDED Requirements
### Requirement: 上位调度与重要程度标准
The system SHALL define `priority`（优先级） and `importance`（重要程度） in the upper work-model specification.

#### Scenario: 统一判断标准
- **WHEN** AI、Code、Web 或 Human 判断工作对象的调度顺序或价值程度
- **THEN** they SHALL use the unified standards in `05-工作模型基础规范.md`

### Requirement: priority（优先级）标准
The system SHALL use `priority`（优先级） only for execution scheduling.

#### Scenario: TaskPlan scheduling
- **WHEN** a TaskPlan（任务计划） is created or updated
- **THEN** it SHALL include `priority`（优先级） with one of `P0`、`P1`、`P2`、`P3`

#### Scenario: P0 priority
- **WHEN** not handling a TaskPlan immediately would block the current mainline, cause fact-source drift, make key capability unavailable, break validation flow, cause major rework, or spread obvious errors
- **THEN** `priority`（优先级） SHALL be `P0`

#### Scenario: P1 priority
- **WHEN** a TaskPlan should be handled early because it clearly affects current goal progress, key closure, or near-term delivery, but does not override all P0 work
- **THEN** `priority`（优先级） SHALL be `P1`

#### Scenario: P2 priority
- **WHEN** a TaskPlan has clear value but can follow P0 and P1 work under normal scheduling
- **THEN** `priority`（优先级） SHALL be `P2`

#### Scenario: P3 priority
- **WHEN** a TaskPlan is deferrable, candidate, optimization, supplementary, or does not affect current mainline closure
- **THEN** `priority`（优先级） SHALL be `P3`

### Requirement: importance（重要程度）标准
The system SHALL use `importance`（重要程度） for value, long-term impact, and retention significance.

#### Scenario: TaskPlan and Memo value judgment
- **WHEN** a TaskPlan（任务计划） or Memo（备忘） is created or updated
- **THEN** it SHALL include `importance`（重要程度） with one of `high`（高）、`medium`（中）、`low`（低）

#### Scenario: high importance
- **WHEN** an object affects core goals, long-term fact-source stability, architectural direction, key capability, key user value, or key governance boundary
- **THEN** `importance`（重要程度） SHALL be `high`（高）

#### Scenario: medium importance
- **WHEN** an object clearly helps the current goal or local capability but is not a core success condition
- **THEN** `importance`（重要程度） SHALL be `medium`（中）

#### Scenario: low importance
- **WHEN** an object is local, marginal, experience optimization, replaceable, discardable, or does not affect the mainline
- **THEN** `importance`（重要程度） SHALL be `low`（低）

## MODIFIED Requirements
### Requirement: TaskPlan field contract
TaskPlan（任务计划） SHALL own execution scheduling fields and include both `priority`（优先级） and `importance`（重要程度）.

### Requirement: Memo field contract
Memo（备忘） SHALL use `importance`（重要程度） for retention and follow-up value judgment, and SHALL NOT use `priority`（优先级）.

### Requirement: Task field contract
Task（任务） SHALL NOT contain `priority`（优先级）、`importance`（重要程度） or `risk_assessment`（风险判断） fields. Execution risks, constraints, downgrade notes, and validation concerns SHALL be written into existing narrative fields such as `description`（描述）、`acceptance`（验收标准） or `verification`（验证）.

### Requirement: Pitfall field contract
Pitfall（踩坑） SHALL NOT contain `priority`（优先级）、`importance`（重要程度） or `severity`（严重程度） fields. Impact and consequences SHALL be written into existing narrative fields such as `symptoms`（问题现象）、`applicability`（适用范围）、`avoidance`（规避策略） or `notes`（备注）.

### Requirement: Object applicability boundary
WorkArea（工作域）、Task（任务）、SubTask（子任务）、ADR（决策）、Pitfall（踩坑） and Change（变更） SHALL NOT contain `priority`（优先级） or `importance`（重要程度） fields.

## REMOVED Requirements
### Requirement: Memo priority field
**Reason**: Memo（备忘） is an input and retention pool, not an execution scheduling object.
**Migration**: Convert existing Memo `priority`（优先级） values to `importance`（重要程度） values where possible.

### Requirement: Task risk_assessment field
**Reason**: `risk_assessment`（风险判断） overlaps with execution notes and can be confused with scheduling or importance.
**Migration**: Move existing risk content into `description`（描述）、`acceptance`（验收标准） or `verification`（验证） according to context.

### Requirement: Pitfall severity field
**Reason**: `severity`（严重程度） can be confused with `importance`（重要程度） and is not needed as a separate formal field.
**Migration**: Move existing severity meaning into `symptoms`（问题现象）、`applicability`（适用范围）、`avoidance`（规避策略） or `notes`（备注） according to context.
