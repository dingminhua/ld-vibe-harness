# Tasks

- [ ] Task 1: 迁移核心基础规范文档（10-14 及子文档）
  - [ ] SubTask 1.1: 将 temp/03-事实源边界与承载规范.md 复制为 specs/10-事实源边界与承载规范.md，更新内部引用
  - [ ] SubTask 1.2: 将 temp/04-LDVH-AI协作规范.md 复制为 specs/11-LDVH-AI协作规范.md，更新内部引用
  - [ ] SubTask 1.3: 将 temp/04.01-Rules机制规范.md 复制为 specs/11.01-Rules机制规范.md，更新内部引用
  - [ ] SubTask 1.4: 将 temp/04.02-Skill机制规范.md 复制为 specs/11.02-Skill机制规范.md，更新内部引用
  - [ ] SubTask 1.5: 将 temp/04.03-Agent机制规范.md 复制为 specs/11.03-Agent机制规范.md，更新内部引用
  - [ ] SubTask 1.6: 将 temp/05-LDVH工具基础规范.md 复制为 specs/12-LDVH工具基础规范.md，更新内部引用
  - [ ] SubTask 1.7: 将 temp/05.01-Tools辅助规范.md 复制为 specs/12.01-Tools辅助规范.md，更新内部引用
  - [ ] SubTask 1.8: 将 temp/05.02-Web展示规范.md 复制为 specs/12.02-Web展示规范.md，更新内部引用
  - [ ] SubTask 1.9: 将 temp/06-LDVH生产对象基础规范.md 复制为 specs/13-LDVH生产对象基础规范.md，更新内部引用
  - [ ] SubTask 1.10: 将 temp/07-LDVH行动模型基础规范.md 复制为 specs/14-LDVH行动模型基础规范.md，更新内部引用

- [ ] Task 2: 迁移生产对象规范文档（20-21）
  - [ ] SubTask 2.1: 将 temp/10-生产对象集合索引.md 复制为 specs/20-生产对象集合索引.md，更新内部引用
  - [ ] SubTask 2.2: 将 temp/11-ADR-决策记录.md 复制为 specs/21-ADR-决策记录.md，更新内部引用

- [ ] Task 3: 迁移行动模型规范文档（50-51 及子文档）
  - [ ] SubTask 3.1: 将 temp/40-行动模型集合索引.md 复制为 specs/50-行动模型集合索引.md，更新内部引用
  - [ ] SubTask 3.2: 将 temp/41-multi-role-thinking-多角色思考.md 复制为 specs/51-multi-role-thinking-多角色思考.md，更新内部引用
  - [ ] SubTask 3.3: 将 temp/41.01-Rules.md 复制为 specs/51.01-Rules.md，更新内部引用
  - [ ] SubTask 3.4: 将 temp/41.02-Skill.md 复制为 specs/51.02-Skill.md，更新内部引用
  - [ ] SubTask 3.5: 将 temp/41.03-Agent.md 复制为 specs/51.03-Agent.md，更新内部引用
  - [ ] SubTask 3.6: 将 temp/41.04-Tools.md 复制为 specs/51.04-Tools.md，更新内部引用
  - [ ] SubTask 3.7: 将 temp/41.05-Web.md 复制为 specs/51.05-Web.md，更新内部引用
  - [ ] SubTask 3.8: 将 temp/41.06-Contract.md 复制为 specs/51.06-Contract.md，更新内部引用

- [ ] Task 4: 更新现有 specs 文档（00、01、02、03）中的"规划中的"标记和待补齐事项
  - [ ] SubTask 4.1: 更新 00 总纲：移除"规划中的"标记，更新待补齐事项
  - [ ] SubTask 4.2: 更新 01 目录说明：移除"规划中的"标记
  - [ ] SubTask 4.3: 确认 02 术语规范无需变更
  - [ ] SubTask 4.4: 更新 03 文档规范：移除"规划中的"标记，更新待补齐事项

- [ ] Task 5: 更新 L0 工作区规则中的旧编号引用
  - [ ] SubTask 5.1: 更新 .trae/rules/ldvh-l0-rules.md 中 41 → 51 的引用
  - [ ] SubTask 5.2: 确认 L1 项目规则无需变更

- [ ] Task 6: 删除 temp 目录

- [ ] Task 7: 全局引用一致性验证

# Task Dependencies

- [Task 1] [Task 2] [Task 3] 可并行执行
- [Task 4] 依赖 [Task 1] [Task 2] [Task 3] 完成
- [Task 5] 依赖 [Task 1] [Task 2] [Task 3] 完成
- [Task 6] 依赖 [Task 1] [Task 2] [Task 3] [Task 4] [Task 5] 完成
- [Task 7] 依赖 [Task 6] 完成
