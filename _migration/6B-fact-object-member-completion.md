# 6B 事实对象成员规范完成记录

> 文件状态：temporary migration decision。本文记录阶段 6 对 V2 `20-24` 事实对象成员的完成范围、后置项和验证闭环；它不授权真实实例目录、Web 写入、Hook 接入、行动模板实例或 Human Gate 决策。正式规则仍以 `specs/` 正文为准。

## 1. 批次定位

阶段 6 的完成目标，是让 Spark、WorkCase、ADR、Pitfall 和 Study 五类事实对象都具备 V3 正式候选成员规范，并能被 Code/tests 读取其最小对象契约。

本批次不恢复 V2 `ldvh-base` 目录权威，不迁移真实实例，不搬运完整字段表，不建立 Web 写入能力，也不建立 WorkCase 创建、审核或关闭的正式行动模板实例。行动模板实例仍等待 Hook / commit gate 接入与 V3 正式启用前再处理。

## 2. 成员迁移结果

| V2 成员 | V3 结果 | 本批次迁入 | 后置 |
|---|---|---|---|
| `20-Spark-火花` | 新增 `specs/20-Spark-火花.md` | 对象定位、准入、实例路径、`pending/resolved/discarded` 状态、分流/废弃口径、Human Gate | 完整字段表、真实 Spark 实例、Web quick create |
| `21-WorkCase-工作项` | 保留并纳入阶段 6 完成集 | 6A 已迁最小对象规则、状态闭集、关闭口径和 Human Gate | `21.Att.01` 长字段表、完整 schema、真实实例、正式行动模板实例 |
| `22-ADR-决策` | 新增 `specs/22-ADR-决策.md` | 对象定位、实例路径、`active/archived/deprecated` 状态、规范吸收边界、旧状态禁用、Human Gate | 完整字段表、真实 ADR 实例、决策创建/归档行动模板 |
| `23-Pitfall-踩坑经验` | 新增 `specs/23-Pitfall-踩坑经验.md` | 对象定位、实例路径、`active/archived` 状态、已解决已验证准入、经验吸收边界、Human Gate | 完整字段表、标签闭集、真实 Pitfall 实例 |
| `24-Study-研究报告` | 新增 `specs/24-Study-研究报告.md` | 对象定位、`.md` 实例路径、`active/archived` 状态、frontmatter/正文骨架、URL 结构边界、Human Gate | 完整 frontmatter schema、真实 Study 实例、Web 阅读实现 |

## 3. `21.Att.01` 处理

V2 `21.Att.01-orchestration字段契约表.md` 本批次不迁入正式附件。

理由：

1. 该附件是 WorkCase `orchestration` 长字段表，和方案审核、结果复核、执行项状态、Human 确认字段强绑定；
2. 当前 V3 尚未接入 Hook / commit gate，也未正式启用 WorkCase 创建、方案审核、结果复核和关闭确认行动模板；
3. 提前迁入长字段表会形成纸面 schema，增加维护成本，并可能让 Code/Web 在真实入口不存在时误判能力已生效；
4. 阶段 6 已通过 `specs/21-WorkCase-工作项.md` 保留执行项内部化、状态闭集、关闭口径和 Human Gate 的最小契约，足够支撑事实对象成员闭环。

后续若迁入，应作为 WorkCase 字段附件或 Code/tests schema 承接，并绑定真实实例目录、行动模板入口和负例测试。

## 4. 阶段 6 完成条件

阶段 6 完成需要同时满足：

1. `20/21/22/23/24` 五个成员规范均存在；
2. `05` 父规范 related_specs 和待补齐事项已同步；
3. Code 能解析五类成员的 code_consumption、状态闭集、实例事实源路径和 source_refs；
4. validator 能对缺状态、缺事实源边界、缺 Human Gate、缺 legacy 状态边界和 Study 正文骨架缺口报错；
5. formal review hash 已覆盖新增和修改的正式 specs；
6. `specs_validate` 0 diagnostics，`tests/code` 与 `_migration/tests` 通过。

