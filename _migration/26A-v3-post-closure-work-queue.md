# 26A V3 关闭后后置工作队列

文件状态：post-closure queue。本文整理 V2 正式关闭后的 V3 后置工作，不授权任何后置能力已经生效，不替代 Spark、WorkCase、ADR 或正式 specs。本文的作用是减少后续反复讨论：哪些可推进、哪些必须等条件、哪些暂不再讨论。

## 当前基线

V2 已于 2026-07-02 关闭为历史来源，记录见 `_migration/25A-v2-official-closure.md`。V3 已作为当前 LDVH 日常主线启动。

当前已生效能力：

1. `specs/` 是当前规则源；
2. `ldvh-base/` 是当前事实对象实例位置；
3. 当前 worktree 的 `git.commit-msg` 已 integrated；
4. Web 按 08 独立读取 V3 Git 文件事实源；
5. smoke 验证和 specs 全量校验可作为日常收口入口。

当前未生效能力：

1. `session_start`、`pre_tool_use`、`completion_claim` 仍为 manual-ready，不是 integrated 自动入口；
2. 外部受管项目 Hook 未自动安装；
3. 通用 Web 写入、完整 Confirm UI 和 WorkCase Web 状态推进未启用；
4. 用户级 LDVH 配置目录只是候选记录；
5. `_migration` 未归档，仍作为历史证据、mapping evidence 和迁移测试承载区保留。

## 队列分级

| 级别 | 含义 | 处理原则 |
|---|---|---|
| P1 | 值得优先推进，但必须满足前置条件 | 有明确触发条件后进入 Spark / WorkCase / Human Gate |
| P2 | 有价值但不急，适合在真实需求出现时推进 | 不主动扩大范围，不阻断 V3 日常主线 |
| Parked | 已判断不应反复讨论，除非条件变化 | 不作为下一步计划 |
| Closed | 明确不恢复或不迁入 | 不重新开启，除非 Human 明确改变方向 |

## P1 队列

| 编号 | 工作 | 来源 | 当前状态 | 前置条件 | 下一步 |
|---|---|---|---|---|---|
| Q1 | Spark 可用性与候选转入方式 | 24A、25A | blocked | Spark 创建 / 更新入口可靠可用，且不绕过事实源和 Human Gate | Spark 可用后，先把 24A 用户级配置候选转入 Spark |
| Q2 | 管辖项目配置生成位置选择 | 24A | candidate | Q1 完成，Human 确认进入正式设计 | 生成配置前必须提问三选一：工作区根目录（推荐，默认 LDVH 安装目录上一级）、用户级 LDVH 配置目录、当前项目根目录；再决定 `LDVH_USER_HOME`、workspace pointer、冲突策略、10 / 10.Att.01 / Code / tests |
| Q3 | 外部受管项目 Hook 安装试点 | 18A、25A | adapter-ready / gated | Human 指定目标 repo，并显式确认 install / uninstall 风险 | 使用 `code/governed_hook_adapter.py` 做 status，再按 Human Gate 安装或回滚 |
| Q4 | Web Confirm UI 最小闭环 | 17A、25A | deferred / gated | Human 确认要推进 Web 写入能力，且先建立 WorkCase 或明确验收目标 | 先做 Confirm UI 的最小确认记录，不直接做通用写入 |

## P2 队列

| 编号 | 工作 | 来源 | 当前状态 | 触发条件 | 下一步 |
|---|---|---|---|---|---|
| Q5 | WorkCase 行动模板实战打磨 | 13A、21、25A | minimal manual template ready | 出现真实 WorkCase 创建、推进、复核或关闭场景暴露缺口 | 只补实际缺口，不整篇迁回 V2 30-36 行动编排 |
| Q6 | 测试输出可观测性增强 | 14A、用户关于全量测试进度的讨论 | optional | full / runtime 测试实际耗时影响日常判断，且引入依赖不会增加维护负担 | 可增强 test runner 分阶段输出或进度显示；不得降低 full 覆盖 |
| Q7 | 成员字段表与长表筛选 | 05、20-24、23A | demand-driven | 某个事实对象的真实读写、Web 展示或验证出现字段缺口 | 逐对象迁入最小字段，不批量搬运 V2 长表 |
| Q8 | Web 设计参考吸收 | web/design-workspace、23A | reference-only | Human 确认要把设计参考转为正式 Web 改造 | 先开 Web 设计 / 实现 WorkCase，再落代码和 tests/web |

## Parked 队列

| 编号 | 工作 | 当前状态 | 不再反复讨论的条件 | 重新开启条件 |
|---|---|---|---|---|
| Q9 | runtime 自动入口接入 | manual-ready / deferred | 当前除 `git.commit-msg` 外没有真实 session/tool/completion 触发点 | 出现可验证的环境触发机制、payload、失败处理、安装状态、回滚和测试入口 |
| Q10 | 稳定 runtime receipt 存储 | no independent receipt source | 16A 已判断当前不建立独立 receipt 事实源 | 出现必须长期保留且不能归入 WorkCase、验证证据、Git records 或事实对象的 receipt |
| Q11 | `_migration` 归档或删除 | retained | 19A 已确认 formal review、迁移测试、test runner 和 source_refs 仍依赖 `_migration` | mapping evidence、迁移测试和 read plan 依赖全部有稳定替代，并经 Human Gate |

## Closed 队列

| 编号 | 工作 | 结论 | 说明 |
|---|---|---|---|
| Q12 | 恢复 V2 Rules 顶层机制 | closed | V3 不恢复 `rules/` 顶层权威；可见入口能力只能转为 repo instruction、manual entrypoint、外部 adapter 或环境薄引用候选 |
| Q13 | 恢复 V2 Skill 顶层机制 | closed | V3 不恢复 `skills/` 顶层机制；可复用能力只进入行动模板、Action Guide、Code CLI 或外部包装候选 |
| Q14 | 恢复知识地图作为正式概念 | closed | 知识地图不作为 V3 正式概念；导航能力由 Action Guide / 行动指南方向承接 |
| Q15 | 按 V2 全文批量迁移剩余行动编排和附件长表 | closed | 后续只按价值、消费方、验证闭环逐项迁入，不做整篇搬运 |

## 推荐推进顺序

如果没有新的用户目标，推荐顺序是：

1. 等 Spark 可用后处理 Q1 / Q2，把 24A 转入正式候选链路；
2. 如果 Human 想先验证外部项目保护能力，处理 Q3；
3. 如果 Human 想提升 Web 可控写入，处理 Q4；
4. 真实工作中遇到 WorkCase、测试或字段缺口时，再处理 Q5 / Q6 / Q7；
5. Q9-Q15 不作为主动下一步。

## Human Gate

以下动作必须重新进入 Human Gate：

1. 新增、删除、重命名或批量迁移管辖项目登记；
2. 修改配置生成落点选择、默认工作区根目录、用户级配置目录或默认路径策略；
3. 安装、卸载或扩大任何外部项目 Hook；
4. 启用通用 Web 写入、完整 Confirm UI 或 WorkCase Web 状态推进；
5. 改变 `_migration` 的保留、移动、删除或归档策略；
6. 恢复任何 V2 Rules / Skill / 知识地图顶层机制。

## 验证口径

本文只是队列整理，验证以文档一致性为主。后续任何队列项进入实现时，应至少说明：

1. 来源依据；
2. 目标和非目标；
3. 是否需要修改 specs；
4. 是否需要 Code / Web / tests；
5. Human Gate；
6. 验证命令；
7. 后置风险和回滚方式。
