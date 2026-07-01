# 阶段 9 V3 主线切换范围

> 文件状态：temporary migration decision。本文记录阶段 9 的剩余 V2 内容归口、用户参与边界和 V3 主线切换完成标准；它不授权 Hook 安装、Web 写入、Human Gate 决策或 V3 正式接管声明。正式规则仍以 `specs/` 正文为准。

## 1. 用户校正口径

阶段 9 采用以下口径推进：

1. 行动模板不做全量迁移。最小迁移范围是 Git 提交行动；WorkCase 创建、方案审核、结果复核、关闭确认等行动模板实例先后置。
2. Web 表现层不重做。Web 之前已完成的展示体验继续保留；阶段 9 只迁 Code、数据契约、来源回指、独立读取和测试边界。
3. 事实对象需要完整迁移。Spark、WorkCase、ADR、Pitfall、Study 的完整字段、schema、实例路径和真实 `ldvh-base/` 实例应进入 V3；编号和目录结构可以按 V3 重新构造，不照搬 V2 权威。
4. 知识地图旧形态不恢复。V2 知识地图的任务导航能力已由 Action Guide / 行动指南承接；旧知识地图页面、投影 schema 和事实层不作为 V3 长期对象。
5. Hook 在阶段 9 环境入口接入中迁移。先接最小 Git 提交链路 Hook / commit gate，再判断是否接 session_start、pre_tool_use、completion_claim 等通用入口。

## 2. 阶段 9 子项

| 子项 | 目标 | 迁移范围 | 暂不迁入 |
|---|---|---|---|
| 9A 迁移层依赖审计 | 防止 `_migration` 继续充当事实源或规则源 | 审计正式 code/tests/review gate 对 `_migration` 的依赖，划分保留、吸收、删除和归档 | 不删除仍被 review hash gate 或迁移测试依赖的材料 |
| 9B 最小提交入口 | 让 V3 接管提交链路 | Git 提交行动、commit message 契约、read_plan 消费证据、验证声明边界、commit-msg / commit gate 接入 | 不一次性接所有 Hook，不把 gate 输出写成 Human 授权 |
| 9C 事实对象完整迁移 | 让 V3 承接长期事实 | 20-24 完整字段、schema、实例路径、真实 `ldvh-base/` 实例和字段级 validator | 不照搬 V2 编号、目录权威或旧 TaskPlan/Task/SubTask 兼容层 |
| 9D Web 数据契约迁移 | 让已有 Web 表现消费 V3 数据边界 | 已完成。迁入 Web tracked 资产、API 数据契约、页面数据来源、Confirm UI 边界、缓存同步、Spark quick create 轻写入白名单和 Web 回归测试 | 不重做表现层，不让 Web 依赖 Code 输出作为主数据源，不启用通用 Web 写入 |
| 9E 行动模板候选后置 | 保持行动模板不早产 | 已完成。记录 WorkCase 创建、方案审核、执行推进、结果复核、关闭确认、Rules 同步审查和环境入口适配候选的后置理由与准入条件 | 不作为 V3 主线切换阻断项 |
| 9F 主线切换收口 | 让 V3 成为日常规则和事实维护主线 | 用户文档、启用边界、迁移层归档/删除条件、最终验证声明 | 不保留 `_migration` 作为长期事实源 |

## 3. 需要 Human 参与的情况

默认推进不需要 Human 中途参与。以下情况必须回到 Human Gate：

1. 安装或启用会阻断真实工作的 Hook、Rules、commit gate 或环境入口；
2. 删除、废弃或不可逆转换 V2 中尚未被本文或吸收索引明确处理的能力；
3. 迁移真实 `ldvh-base/` 实例时发生字段丢失、语义冲突、编号冲突或无法自动映射；
4. Web 写入、Confirm UI 或缓存策略会改变 Human 可见状态、授权语义或事实源回写；
5. 声明 V3 正式接管主线，或接受仍未迁移能力的残留风险；
6. 发现 V2 内容和 V3 specs 上位规则冲突，且不能通过既定分流规则解决。

以下事项不需要 Human 中途参与：

1. 迁移记录、执行计划、索引和用户文档的普通澄清；
2. Code/tests 中可逆、只读、可验证的解析和诊断增强；
3. 按既定映射迁移字段、schema 或实例，并保留 source_refs 和回滚线索；
4. 删除测试产生的缓存、临时输出或未被 Git 跟踪的生成物；
5. 运行验证命令并记录结果。

## 4. V3 主线切换完成标准

阶段 9 完成后，应能声明：

1. 日常规则判断以 V3 `specs/` 为准，V2 只作为历史来源；
2. Git 提交入口使用 V3 契约、read_plan 消费证据和验证声明边界；
3. Spark、WorkCase、ADR、Pitfall、Study 的完整事实对象能力由 V3 schema、事实源路径和 validator 承接；
4. Web 保留原表现层，但数据契约、来源回指、写入边界和回归验证对齐 V3；
5. Action Guide / 行动指南完全承接 V2 知识地图导航能力，旧知识地图不再作为正式概念；
6. `_migration` 只保留为历史审计或已明确的临时 review gate，不再参与日常规则判断和事实维护。

## 5. 当前下一步

9A 已完成迁移层依赖审计，结论见 `_migration/9A-migration-layer-dependency-audit.md`。9B 已完成 V3 自有 commit gate、CLI 和 Hook wrapper，但未启用真实 Git Hook。9C 已完成事实对象完整迁移，结论见 `_migration/9C-fact-object-full-migration.md`。9D 已完成 Web 数据契约迁移，结论见 `_migration/9D-web-data-contract-migration.md`。9E 已完成行动模板候选后置，结论见 `_migration/9E-action-template-candidate-deferral.md`。当前下一步是 9F 主线切换收口。
