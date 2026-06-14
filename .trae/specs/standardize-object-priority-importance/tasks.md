# Tasks

- [x] Task 1: 更新上位工作模型规范
  - [x] SubTask 1.1: 在 `specs/05-工作模型基础规范.md` 中新增 `priority`（优先级）和 `importance`（重要程度）的统一语义、枚举、判断标准和对象适用边界
  - [x] SubTask 1.2: 明确 `priority`（优先级）只用于 TaskPlan（任务计划），`importance`（重要程度）只用于 TaskPlan（任务计划）和 Memo（备忘）
  - [x] SubTask 1.3: 明确不再使用 `risk_assessment`（风险判断）和 `severity`（严重程度）作为正式工作对象字段

- [x] Task 2: 更新具体工作对象规范
  - [x] SubTask 2.1: 更新 `specs/27-TaskPlan-任务计划.md`，新增 `priority`（优先级）和 `importance`（重要程度）字段并引用 05 判断标准
  - [x] SubTask 2.2: 更新 `specs/25-Memo-备忘.md`，将 `priority`（优先级）替换为 `importance`（重要程度）
  - [x] SubTask 2.3: 更新 `specs/26-Task-任务.md`，移除 `risk_assessment`（风险判断）字段并说明迁移承载位置
  - [x] SubTask 2.4: 更新 `specs/23-Pitfall-踩坑.md`，移除 `severity`（严重程度）字段并说明影响描述承载位置

- [x] Task 3: 同步 Code 字段契约
  - [x] SubTask 3.1: 更新 `code/fact_validate.py` 中 Memo、TaskPlan、Task、Pitfall 的字段校验口径
  - [x] SubTask 3.2: 更新 `code/fact_cli.py` 中创建模板、摘要字段和默认字段口径
  - [x] SubTask 3.3: 确保 Validator 对旧字段给出明确诊断或迁移提示

- [x] Task 4: 迁移现有工作对象实例
  - [x] SubTask 4.1: 将 Memo（备忘）实例中的 `priority`（优先级）迁移为 `importance`（重要程度）
  - [x] SubTask 4.2: 将 Task（任务）实例中的 `risk_assessment`（风险判断）内容迁移到合适的叙述字段
  - [x] SubTask 4.3: 将 Pitfall（踩坑）实例中的 `severity`（严重程度）含义迁移到合适的叙述字段
  - [x] SubTask 4.4: 为 TaskPlan（任务计划）实例补齐 `priority`（优先级）和 `importance`（重要程度）

- [x] Task 5: 同步 Web 和测试验证
  - [x] SubTask 5.1: 更新 Web 对象展示、筛选或 Memo 创建入口中与 `priority`（优先级）、`importance`（重要程度）相关的字段口径
  - [x] SubTask 5.2: 更新或补充相关测试
  - [x] SubTask 5.3: 运行 specs、facts、code 和 Web 相关校验，确认规范、实例和工具一致

# Verification
- [x] `python3 -m pytest -q`：148 passed
- [x] `python3 -m pytest tests/code/test_fact_validate.py tests/code/test_fact_cli.py tests/code/test_specs_validate.py -q`：133 passed
- [x] `npm run test:web:api`：通过
- [x] `npm run check`：通过
- [x] `npm run lint`：0 errors，10 个既有 react-refresh warning
- [x] `python3 code/specs_validate.py all`：未出现 error；仍有 `specs/04.03-环境入口适配与部署规范.md` 中用户级入口示例路径的既有 `BROKEN_MARKDOWN_PATH` warning
- [x] `python3 code/fact_validate.py ldvh-base tests/web/fixtures/taskplan-with-subtasks/ldvh-base`：旧字段迁移已生效；剩余 errors 为既有失效文档路径引用，warnings 为既有 Evidence/块标量提示

# Task Dependencies
- Task 2 depends on Task 1 because具体工作对象规范必须引用上位判断标准。
- Task 3 depends on Task 1 and Task 2 because Code 字段契约必须跟随规范定稿。
- Task 4 depends on Task 2 and Task 3 because实例迁移需要明确字段契约和校验口径。
- Task 5 depends on Task 3 and Task 4 because Web 和测试验证需要基于最终字段和实例状态。
