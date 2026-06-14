# 统一工作对象公共字段语义边界 Spec

## Why
LDVH 各工作对象的常见属性字段（如 `description`、`verification`、`notes`、`related_*` 等）语义边界模糊，同名字段在不同对象中含义不一致，不同名字段之间语义重叠，导致 AI 写入、Code 校验和 Web 渲染缺乏统一依据。需要在 05.01 中建立公共字段语义定义，明确每个字段回答什么问题、不应该写什么、哪些对象使用。

## What Changes
- 在 `05.01-工作字段内容格式规范.md` 中新增 `公共字段语义定义` 章节，作为所有工作对象公共字段的权威语义源。
- 定义全局公共字段（所有对象都有）和部分公共字段（2 个以上对象共享）的语义边界。
- 更新各对象规范（21/23/24/25/26/27/28），让对象特有字段保留在对象规范中，公共字段引用 05.01。
- 修正当前实例中违反语义边界的字段内容（如 `verification` 中混入风险说明）。
- 同步 Code 校验和 Web 渲染，使字段消费与语义定义一致。

## Impact
- Affected specs: `specs/05.01-工作字段内容格式规范.md`、`specs/05-工作模型基础规范.md`、`specs/21-ADR-决策.md`、`specs/23-Pitfall-踩坑.md`、`specs/24-WorkArea-工作域.md`、`specs/25-Memo-备忘.md`、`specs/26-Task-任务.md`、`specs/27-TaskPlan-任务计划.md`、`specs/28-SubTask-子任务.md`
- Affected code: `code/fact_validate.py`、`code/fact_cli.py`、`web/src/utils/fieldFormats.ts`
- Affected instances: `ldvh-base/` 下 Task、Pitfall 等实例中违反语义边界的字段内容

## ADDED Requirements

### Requirement: 公共字段语义定义
05.01 SHALL 定义每个公共字段的语义边界，包括：该字段回答什么问题、不应该写什么、适用哪些对象。

#### Scenario: AI 写入字段时判断内容归属
- **WHEN** AI 需要向某个字段写入内容
- **THEN** AI SHALL 根据 05.01 的公共字段语义定义判断内容是否属于该字段，不属于的应写入正确字段

#### Scenario: Code 校验字段语义合规
- **WHEN** Code 校验工作对象字段
- **THEN** Code SHALL 根据 05.01 的公共字段语义定义检测字段内容是否违反语义边界

### Requirement: 全局公共字段语义

以下字段所有工作对象 SHALL 遵循统一语义：

| 字段 | 回答什么问题 | 不应该写什么 |
|------|------------|------------|
| `id` | 唯一标识 | 描述性内容 |
| `type` | 对象类型 | 描述性内容 |
| `title` | 一句话概括 | 详细说明、验证方法、状态变化 |
| `status` | 当前状态 | 状态变化历史 |
| `created` | 创建时间 | 修改时间 |
| `updated` | 最后更新时间 | 创建时间 |
| `description` | 这个对象是什么、为什么存在 | 验证方法、风险说明、约束条件、验收标准、状态变化 |

#### Scenario: description 字段语义
- **WHEN** AI 或 Human 向 `description` 字段写入内容
- **THEN** 内容 SHALL 只包含对象的背景、目标和范围说明，SHALL NOT 包含验证方法、风险说明、约束条件、验收标准或状态变化

### Requirement: 部分公共字段语义

以下字段在使用的对象中 SHALL 遵循统一语义：

| 字段 | 回答什么问题 | 不应该写什么 | 适用对象 |
|------|------------|------------|---------|
| `source` | 这个对象的输入来源 | 一般关联、验证结论 | WorkArea, TaskPlan, Task, SubTask, Memo |
| `status_history` | 状态变化记录 | 非状态变化的日志 | 所有对象 |
| `acceptance` | 完成的判断条件 | 验证方法、风险说明、背景 | Task, SubTask |
| `verification` | 怎么验证完成 | 风险说明、约束条件、背景说明 | Task, SubTask, Pitfall |
| `closure_evidence` | 关闭时的证据 | 验收标准、风险说明 | Task, SubTask |
| `completion_evidence` | 计划关闭时的证据 | 验收标准、风险说明 | TaskPlan |
| `closed_at` | 关闭时间 | 创建时间、更新时间 | Task, SubTask, TaskPlan |
| `archive_reason` | 为什么归档 | 归档后的内容、验证 | ADR, Pitfall, WorkArea, Memo |
| `blocked_by` | 前置依赖 | 后续依赖、一般关联 | Task, SubTask, Pitfall |
| `notes` | 其他字段无法承载的补充说明 | 核心信息、验证方法、决策 | Pitfall |
| `related_docs` | 引用的文档路径 | 对象 ID 引用 | ADR, Pitfall, WorkArea, TaskPlan, Task, Memo |
| `related_adrs` | 关联的决策记录 | 来源决策（用 source_*） | ADR, Pitfall, WorkArea, TaskPlan, Task, Memo |
| `related_memos` | 关联的备忘 | 来源备忘（用 source_memos） | ADR, Pitfall, WorkArea, TaskPlan, Memo |
| `related_changes` | 关联的变更 commit | 非变更关联 | ADR, Pitfall, TaskPlan, Task, Memo |
| `related_workareas` | 关联的工作域 | 所属工作域（用 workarea 字段） | ADR, Pitfall, TaskPlan, Memo |
| `related_taskplans` | 关联的任务计划 | 所属任务计划（用 taskplan 字段） | ADR, Pitfall, Memo |
| `related_tasks` | 关联的任务 | 所属任务（用 task 字段） | ADR, Memo |
| `related_pitfalls` | 关联的踩坑 | 来源踩坑 | WorkArea, TaskPlan |
| `related_rules` | 关联的规范路径 | 一般文档引用（用 related_docs） | ADR, Pitfall |
| `superseded_by` | 替代本对象的新对象 | 一般关联 | ADR, Pitfall |
| `source_tasks` | 本对象的来源任务 | 一般任务关联（用 related_tasks） | Pitfall |
| `source_memos` | 本对象的来源备忘 | 一般备忘关联（用 related_memos） | Pitfall |

#### Scenario: verification 字段语义
- **WHEN** AI 或 Human 向 `verification` 字段写入内容
- **THEN** 内容 SHALL 只包含验证计划、验证命令、验证结果和验证结论，SHALL NOT 包含风险说明、约束条件或背景说明

#### Scenario: source vs related 边界
- **WHEN** AI 或 Human 判断一个引用应放入 `source_*` 还是 `related_*`
- **THEN** 如果该引用是本对象的输入来源，SHALL 放入 `source_*`；如果该引用只是与本对象有关联，SHALL 放入 `related_*`

### Requirement: 对象特有字段保留在各对象规范
各对象规范 SHALL 只定义该对象特有的字段语义，公共字段 SHALL 引用 05.01 定义。

#### Scenario: 对象规范引用公共字段
- **WHEN** 对象规范需要使用公共字段
- **THEN** 对象规范 SHALL 引用 05.01 的公共字段语义定义，SHALL NOT 重复定义公共字段语义

## MODIFIED Requirements

### Requirement: 05.01 定位扩展
05.01 的定位从"只定义字段内容格式"扩展为"定义公共字段语义和字段内容格式"。字段语义定义和字段内容格式是两个互补维度：语义定义回答"这个字段写什么"，内容格式回答"写的内容用什么格式"。

### Requirement: 对象规范字段表简化
各对象规范字段表 SHALL 区分公共字段和对象特有字段。公共字段只列出字段名和对象特有语义补充，完整语义引用 05.01；对象特有字段完整定义。

## REMOVED Requirements

### Requirement: 各对象规范独立定义公共字段语义
**Reason**: 公共字段语义在各对象规范中重复定义且不一致，应统一到 05.01。
**Migration**: 各对象规范中的公共字段语义描述迁移到 05.01，对象规范保留对象特有语义补充。
