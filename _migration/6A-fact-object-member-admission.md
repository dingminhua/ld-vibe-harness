# 6A 事实对象成员准入与首批迁移记录

> 文件状态：temporary migration decision。本文只记录阶段 6A 的事实对象成员准入判断、首批迁移范围和后置项；它不授权正式 facts、实例目录、Code 行为、Web 行为、Hook 接入、行动模板实例或 Human Gate 决策。正式规则仍以 `specs/` 正文为准。

## 1. 批次定位

阶段 6A 的目标，是从 V2 `20-24` 事实模型成员中选出首个能形成闭环的最小成员规范，验证 V3 可以逐篇承接事实对象，而不是一次性搬运完整字段表、状态机、实例目录或旧目录权威。

本批次不建立正式行动模板实例。Git 提交行动模板当前只保留为 `06` 正文示范；正式模板附件、模板目录和模板 registry 后置到 Hook / commit gate 接入与 V3 正式启用前，避免纸面模板与真实环境入口脱节。

## 2. 准入标准

事实对象成员进入 V3 正式规范前，至少需要满足：

| 准入项 | 最小要求 |
|---|---|
| 对象化价值 | 能说明该对象承接什么稳定事实，以及不对象化会增加什么 AI 负担 |
| 事实源位置 | 能说明实例未来应位于哪个 Git 可追踪事实源位置，且不把测试夹具、Code 输出、Web 状态或迁移材料写成实例 |
| 字段与状态边界 | 能给出最小字段/状态边界，但不要求一次迁入完整 V2 字段表 |
| 证据回指 | 能说明验证、关闭、决策或经验如何回指来源 |
| Human Gate | 能列出创建、状态推进、关闭或高影响改写需要 Human 明示决定的情形 |
| Code/tests 闭环 | 能被 validator 解析，并至少覆盖缺状态、缺事实源边界、缺 Human Gate 或越界字段的负例 |

## 3. 成员准入判断

| V2 成员 | V3 处理 | 理由 | 本批次动作 |
|---|---|---|---|
| `20-Spark-火花` | 后置 | Spark 是前置暂存入口，适合等 WorkCase/ADR/Pitfall 分流边界更清楚后承接 | 保留 V2 来源，不迁实例目录和完整字段表 |
| `21-WorkCase-工作项` | 首批迁入 | WorkCase 直接承接目标、范围、执行状态、验证证据、关闭判断和后续分流，最能减少 AI 的恢复、验证和关闭判断负担 | 新增 `specs/21-WorkCase-工作项.md` 最小成员规范和 validator/tests |
| `22-ADR-决策` | 后置 | ADR 会影响长期规则和 Human 决策边界，应在 WorkCase 最小闭环后迁入 | 保留 V2 来源，不建立决策实例 |
| `23-Pitfall-踩坑经验` | 后置 | Pitfall 要求问题已解决且验证，适合在 WorkCase 验证和关闭口径稳定后迁入 | 保留 V2 来源，不迁完整经验 schema |
| `24-Study-研究报告` | 后置 | Study 涉及 Markdown frontmatter、正文契约和资料区边界，适合在事实对象基础校验稳定后迁入 | 保留 V2 来源，不迁报告模板 |

## 4. WorkCase 首批迁移范围

本批次迁入：

1. WorkCase 对象定位与准入条件；
2. 未来实例事实源位置；
3. 最小状态闭集；
4. 执行项只能作为 WorkCase 内部字段的边界；
5. 执行完成、可提交关闭确认、已关闭、已提交四层完成口径；
6. 方案确认、关闭确认、跳过验证、关键改写等 Human Gate；
7. Code 可消费的成员规范检查和负例测试。

本批次不迁入：

1. V2 `21.Att.01-orchestration字段契约表.md` 长字段表；
2. WorkCase 完整顶层字段表、`orchestration` 全量嵌套 schema、实例目录和真实实例；
3. WorkCase 创建、方案审核、结果复核和关闭确认的正式行动模板；
4. Hook、commit gate、Web 写入、CLI 或 runtime adapter。

## 5. 完成条件

阶段 6A 完成需要同时满足：

1. `specs/21-WorkCase-工作项.md` 存在并通过 formal spec review gate；
2. `05` 父规范说明 WorkCase 已首批迁入，但完整字段表和其它成员仍后置；
3. Code 能解析 WorkCase 最小成员契约并输出到 validation payload；
4. validator 覆盖 WorkCase 缺状态、缺事实源边界、缺关闭口径和缺 Human Gate 的负例；
5. `specs_validate` 0 diagnostics，`tests/code` 与 `_migration/tests` 通过；
6. 迁移计划和吸收索引记录阶段 6A 状态。
