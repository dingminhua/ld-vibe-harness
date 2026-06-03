# Tasks

- [ ] Task 1: 创建 ldvh-intake Skill
  - [ ] SubTask 1.1: 创建 .trae/skills/ldvh-intake/SKILL.md，包含 YAML 头部、定位、触发条件、不适用场景、必读文件、编排流程、输出格式、Human Gate、事实源回写、Agent 边界
  - [ ] SubTask 1.2: 编排流程设计：1.识别场景（Intent 准入 vs 简单请求）→ 2.创建草案（Intent+Task 或仅 Task）→ 3.Human Gate 确认 → 4.写入 ldvh-base/ → 5.记录 Change
- [ ] Task 2: 创建 ldvh-close Skill
  - [ ] SubTask 2.1: 创建 .trae/skills/ldvh-close/SKILL.md，包含 YAML 头部、定位、触发条件、不适用场景、必读文件、编排流程、输出格式、Human Gate、事实源回写、Agent 边界
  - [ ] SubTask 2.2: 编排流程设计：1.校验关闭条件（closure_evidence、Evidence 验证结果）→ 2.提示补充或退回（条件不满足时）→ 3.Human Gate 确认 → 4.更新 Task 状态 → 5.记录 Change
- [ ] Task 3: 更新 L0 工作区规则
  - [ ] SubTask 3.1: 在 .trae/rules/ldvh-l0-rules.md 中加入 Core Loop 阶段识别入口和 Skill 路由
- [ ] Task 4: 更新 L1 项目规则
  - [ ] SubTask 4.1: 在 .trae/rules/ldvh-l1-rules.md 中加入 Core Loop 阶段判断和 ldvh-intake/ldvh-close 路由

# Task Dependencies

- Task 1 和 Task 2 可并行
- Task 3 和 Task 4 可并行
- Task 3/4 不依赖 Task 1/2（Rules 定义入口，Skill 定义流程，互不依赖）
