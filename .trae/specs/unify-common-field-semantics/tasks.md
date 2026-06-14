# Tasks

- [x] Task 1: 在 05.01 中新增公共字段语义定义章节
  - [x] SubTask 1.1: 定义全局公共字段语义表（id, type, title, status, created, updated, description）
  - [x] SubTask 1.2: 定义部分公共字段语义表（source, status_history, acceptance, verification, closure_evidence, completion_evidence, closed_at, archive_reason, blocked_by, notes, related_*, source_*, superseded_by）
  - [x] SubTask 1.3: 明确 source_* 与 related_* 的引用语义边界
  - [x] SubTask 1.4: 更新 05.01 定位说明，从"只定义字段内容格式"扩展为"定义公共字段语义和字段内容格式"

- [x] Task 2: 更新各对象规范字段表
  - [x] SubTask 2.1: 更新 21-ADR-决策.md，公共字段引用 05.01，只保留对象特有字段完整定义
  - [x] SubTask 2.2: 更新 23-Pitfall-踩坑.md，公共字段引用 05.01，只保留对象特有字段完整定义
  - [x] SubTask 2.3: 更新 24-WorkArea-工作域.md，公共字段引用 05.01，只保留对象特有字段完整定义
  - [x] SubTask 2.4: 更新 25-Memo-备忘.md，公共字段引用 05.01，只保留对象特有字段完整定义
  - [x] SubTask 2.5: 更新 26-Task-任务.md，公共字段引用 05.01，只保留对象特有字段完整定义
  - [x] SubTask 2.6: 更新 27-TaskPlan-任务计划.md，公共字段引用 05.01，只保留对象特有字段完整定义
  - [x] SubTask 2.7: 更新 28-SubTask-子任务.md，公共字段引用 05.01，只保留对象特有字段完整定义

- [x] Task 3: 修正实例中违反语义边界的字段内容
  - [x] SubTask 3.1: 将 Task 实例 verification 字段中的"风险、约束和降级说明"迁移到 description 字段
  - [x] SubTask 3.2: 检查 Pitfall 实例中是否有字段内容违反语义边界，如有则修正
  - [x] SubTask 3.3: 检查其他对象实例中是否有字段内容违反语义边界，如有则修正

- [x] Task 4: 同步 Code 和 Web
  - [x] SubTask 4.1: 更新 fact_validate.py，对 verification 字段中包含风险说明的情况给出 warning
  - [x] SubTask 4.2: 更新 fact_cli.py 创建模板，确保新创建的对象字段内容符合语义边界
  - [x] SubTask 4.3: 检查 Web 渲染是否需要根据语义边界调整

- [x] Task 5: 验证
  - [x] SubTask 5.1: 运行 specs、facts、code 和 Web 校验，确认规范、实例和工具一致
  - [x] SubTask 5.2: 检查所有实例的字段内容是否符合新的语义边界定义

# Task Dependencies
- Task 2 depends on Task 1 because 对象规范必须引用 05.01 的公共字段语义定义。
- Task 3 depends on Task 1 and Task 2 because 实例修正需要基于明确的语义边界。
- Task 4 depends on Task 1 and Task 2 because Code 和 Web 需要跟随规范定稿。
- Task 5 depends on Task 3 and Task 4 because 验证需要基于最终状态。
