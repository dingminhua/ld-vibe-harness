# LDVH 自锁 / Repair / Unknown-Gated 设计审计

日期：2026-07-08

## 0. 文档性质

本文是设计审计，不是正式 specs、不是事实源实例、不是实现授权，也不替代 Human Gate。

本文只回答一个问题：在 AI 写坏 LDVH 自己的事实源后，LDVH 如何避免把自己锁死，同时又不把 repair 变成 bypass、自动恢复或自动状态推进。

正式规则修改仍必须回到对应 specs 或附件。本文不修改 runtime code。

## 1. 起因

本轮讨论的起因不是抽象的 Hook governance，而是一个真实事故链：

1. AI 修改 LDVH 事实源对象时写错结构；
2. LDVH 事实对象 validator 产生结构性诊断；
3. 环境 Hook / preflight 把全局事实源诊断当成当前行动阻断；
4. 结果是无关文件写入、坏对象本身修复、甚至恢复 / fork / 继续诊断路径都可能被同一机制挡住；
5. Human 需要介入完善保障机制，但保障机制本身不应提供自动恢复路径。

这说明 LDVH 不能只问“是否有诊断”，而必须问“这个诊断是否属于当前动作、当前 target、当前事件的阻断条件”。

## 2. 总结论

当前实现方向基本正确，但 specs 层面还不能说完全闭环。

已经正确收敛的部分：

| 机制 | 当前判断 | 依据 |
|---|---|---|
| target-scoped blocking | Code 已把 `target_primary` / `runtime_blocker` 作为阻断范围，`unrelated_global` 不阻断普通 runtime | `code/ldvh_specs.py` 的 `_is_blocking_for_runtime` 只统计 `target_primary` 和 `runtime_blocker` |
| repair lane | specs 和 Code 已把 repair 限定为 `ldvh.pre_tool_use` / preflight 下的事实对象结构性修复 | `specs/01` §5.8、`specs/07` §7.1 |
| repair final validation | specs 已写明 final validation 只看 primary target 和必要 direct dependent | `specs/09` §6 |
| unknown / gated | `scope_unknown`、`governed_target_unknown`、`mixed_scope` 已由 `10` 明确定义 | `specs/10` §6-7 |
| completion_claim | Code 已消费 target-scoped preflight diagnostic，不再只看 evidence 非空 | `code/ldvh_specs.py` `completion_claim` 分支和 tests |

仍未完全闭环的部分：

| 缺口 | 判断 |
|---|---|
| Hook 行动边界表 | `01` 已明确列为待补齐：各 LDVH event 的输入、输出、阻断、no-op、degraded、Human Gate 口径还没有形成可检查矩阵 |
| 自锁事故路径验收 | 当前有分散 tests，但没有一张“事实源坏了以后，哪些动作应放行 / 阻断 / repair / Human Gate”的验收表 |
| Human 介入边界 | repair 已限制自动状态推进，但 specs 还需要更清楚表达“保障机制失败时由 Human 介入完善机制，不提供自动恢复路径” |
| fork / 恢复 / 诊断类动作 | 当前规则主要围绕 runtime/preflight 写入，尚未明确这类动作在坏事实对象存在时应归入只读诊断、process output、还是 Human Gate |

结论：下一步应补 specs，不应继续写 runtime code。

## 3. 当前机制如何避免再次自锁

### 3.1 诊断分层

当前 Code 将 validator 诊断分为：

| diagnostic_scope | 含义 | 阻断口径 |
|---|---|---|
| `target_primary` | 当前 target 自身的诊断 | 普通写入 / completion 阻断；repair 下可修复闭集不阻断 repair 本身 |
| `target_cascade` | 与当前 target 直接相关的依赖诊断 | 作为诊断和 final validation 参考，不应变成全局阻断 |
| `unrelated_global` | 与当前 target 无关的全局事实源诊断 | 不阻断当前普通 runtime，只作为 residual risk / diagnostic |
| `runtime_blocker` | read_plan、target unknown、scope mixed 等当前 runtime 条件问题 | 阻断当前事件 |

这正是解除 self-lock 的核心：坏事实对象不能污染所有事件，但坏 target 本身仍不能被普通写入绕过。

### 3.2 repair 不是 bypass

Repair lane 的边界已经比较清楚：

1. 只能通过 `operation=repair` 或等价 `mode=repair` 表达；
2. 不新增 runtime event；
3. 只处理事实对象实例的结构性诊断；
4. target 必须归口为单一事实对象实例；
5. diagnostic code 必须在 `07` 的可修复闭集内；
6. 不推进状态、不关闭对象、不接受风险、不跨对象迁移、不处理业务语义判断；
7. repair 后 primary target 仍未通过时，必须表述为“已写未通过”，不能声明完成或关闭。

这说明 repair 是“让坏对象能被修”的窄通道，不是“让 LDVH 放弃检查”的总开关。

### 3.3 unknown / gated 不是扩大作用域

当前 `10` 已把 scope 分成六类：

| scope_status | 当前自锁语境下的含义 |
|---|---|
| `governed_single` | 可以按当前对象消费保障需求 |
| `non_governed` | 必须静默 no-op，不输出 LDVH guidance / read_plan / deny |
| `scope_unknown` | 不能证明受管，也不能证明非受管；不得擅自当作管辖对象干预 |
| `governed_target_unknown` | 已有管辖范围证据，但当前 target 不明；写入 / 提交 / 完成声明必须 gated |
| `declared_multi_governed` | Human 明确发起跨管辖对象读取 / 审计 / 对比；写入仍需拆分或 Human Gate |
| `mixed_scope` | 未声明混合多个管辖对象或管辖 / 非管辖 target；写入必须阻断、拆分或 Human Gate |

关键点：`unknown` 不能自动升级为全局 LDVH 阻断；只有已有管辖范围证据但当前动作 target 不明时，才进入 `governed_target_unknown`。

## 4. 当前测试覆盖

已有测试覆盖了自锁核心场景：

| 覆盖点 | 测试 |
|---|---|
| unrelated global 不阻断当前 target preflight | `test_preflight_unrelated_global_diagnostics_do_not_block_target` |
| target primary 诊断阻断普通写入 | `test_preflight_target_primary_diagnostic_blocks_normal_write` |
| repair mode 允许可修复 primary + cascade | `test_preflight_repair_mode_allows_repairable_primary_and_cascade` |
| repair final validation 不被 unrelated global 卡死 | `test_preflight_repair_mode_final_validation_only_checks_primary` |
| runtime pre_tool_use 不被 unrelated global 阻断 | `test_runtime_pre_tool_use_unrelated_global_diagnostics_are_not_blocking` |
| non-governed / scope_unknown 外部 target 在 ack 前 no-op | `test_runtime_external_pre_tool_use_noops_before_read_plan_ack` |
| completion_claim 阻断 target_primary diagnostic | `test_runtime_completion_claim_blocks_target_primary_diagnostic_even_with_evidence` |
| completion_claim 把 unrelated_global 保留为 residual risk | `test_runtime_completion_claim_keeps_unrelated_global_diagnostic_as_residual_risk` |
| acknowledge_read_plan bootstrap 不被 read_plan 检查自锁 | `test_codex_sample_shim_allows_acknowledge_read_plan_bootstrap_command_without_acknowledgement` 及 WorkBuddy 对应测试 |
| bootstrap 不能链式写入、不能被 Write 工具伪装 | `test_codex_sample_shim_does_not_allow_chained_acknowledge_bootstrap_write_without_acknowledgement` 等 |

这些测试说明 Code 已经覆盖了核心 bugfix。但它们不能替代 specs 的事件边界矩阵，因为测试只证明当前实现，不能定义未来维护时每个事件应如何分流。

## 5. 仍需 specs 吸收的内容

### 5.1 P0：补 `01` 的 Hook 行动边界表

`01` §12 已写明 Hook 行动边界表仍需补齐。这个表应成为下一步 specs patch 的核心，不应另起一个 code/docs 规则源。

建议矩阵字段：

| 字段 | 用途 |
|---|---|
| `ldvh_event` | `ldvh.session_start`、`ldvh.pre_tool_use`、`ldvh.completion_claim` 等 |
| `input_required` | 该事件必须具备哪些 target、cwd、operation、receipt、evidence |
| `scope_status_handling` | 六类 scope_status 下该事件如何处理 |
| `diagnostic_scope_handling` | target_primary、target_cascade、unrelated_global、runtime_blocker 的处理 |
| `blocking_rule` | 哪些条件阻断当前事件 |
| `no_op_rule` | 哪些条件必须静默 no-op |
| `degraded_rule` | 哪些条件只能输出 capability_gap / unverifiable |
| `repair_rule` | 是否允许 repair；若允许，条件是什么 |
| `human_gate_rule` | 哪些情况必须交还 Human |
| `must_not_claim` | 该事件绝不能声明什么 |

最小事件行应覆盖：

1. `ldvh.session_start`
2. `ldvh.acknowledge_read_plan`
3. `ldvh.pre_tool_use`
4. `ldvh.completion_claim`
5. `git_commit_msg`
6. `human_facing_output`
7. `external_output_intake`
8. `diagnostic_disposition`

### 5.2 P1：补自锁事故验收表

建议在 `09` 或 `01` 授权附件中补一张“自锁事故验收矩阵”，至少覆盖：

| 事故场景 | 期望处理 |
|---|---|
| 坏事实对象存在，写无关 README | 不被坏对象阻断；坏对象作为 residual risk |
| 坏事实对象存在，普通写该坏对象 | 阻断，要求 repair 或 Human |
| 坏事实对象存在，repair 该对象 | 允许进入 repair lane；只处理结构性闭集 |
| repair 后 primary 仍坏 | 记录“已写未通过”，不得完成 / 关闭 |
| repair 后 primary 清除但 unrelated_global 仍坏 | repair 可通过当前 primary；unrelated_global 作为 residual risk |
| target 不明但已有管辖范围证据 | `governed_target_unknown`，写入 / 提交 / 完成 gated |
| 无法证明受管 | `scope_unknown`，不得全局干预非管辖对象 |
| 混合管辖 / 非管辖写入 | `mixed_scope` 阻断、拆分或 Human Gate |
| read_plan receipt 入口自身 | 受控 bootstrap，不得变成任意命令 bypass |
| completion_claim 有 target_primary blocker | 阻断完成声明 |
| completion_claim 只有 unrelated_global | 不阻断当前完成，但必须暴露 residual risk |

### 5.3 P1：明确 Human 介入边界

需要在 `01` 或 `02` 中明确表达：

1. 保障机制失败时，Human 介入的是“完善保障机制或授权一次受控处理”，不是让 LDVH 自动恢复；
2. repair lane 只能修结构性事实对象诊断，不能自动推进 WorkCase 状态、关闭对象或接受风险；
3. bypass / break-glass 如未来需要，必须单次、显式、可见，不写入正式事实源，不复用为长期许可；
4. 当前没有 bypass 需求时，不应提前设计自动恢复路径。

### 5.4 P2：fork / 恢复 / 诊断动作的分类

侧边事故里出现过“无法继续工作 / 无法 fork 或恢复”的风险。这个问题不一定是 runtime code bug，也可能是事件分类没写清：

| 动作 | 建议归类 |
|---|---|
| 只读诊断、读取坏对象、生成失败信息包 | 应允许，除非 target/scope 本身不可判定 |
| fork / resume / new thread 类动作 | 默认不应被事实对象全局健康阻断；若会写正式事实源，则回到对应 target preflight |
| 修复坏事实对象 | repair lane 或 Human Gate |
| 自动恢复坏事实对象 | 不允许作为默认路径 |

这部分可以后置，但应进入 Hook 行动边界表或行动模板的待补齐事项。

## 6. 建议 specs patch 顺序

1. **先补 `01` Hook 行动边界表**：这是当前最关键缺口。它能把 self-lock、unknown/gated、repair、completion、read_plan receipt 都放进同一张事件矩阵。
2. **同步检查 `07` 是否需要只补回指**：如果 `01` 表已经定义事件行为，`07` 只需说明 Code 输出字段与实现边界，不应复制整张规则表。
3. **同步检查 `09` 是否需要补验收矩阵**：重点是自锁事故验收和 repair final validation，不要扩大成全量测试清单。
4. **最后决定是否更新 `02`**：只在需要明确 AI / Human 介入边界时补；不把实现细节写成 AI 行为长表。

## 7. 当前不建议做的事

1. 不继续扩 runtime code。
2. 不新增 runtime event。
3. 不设计自动恢复。
4. 不把 repair 扩大成 bypass。
5. 不把 `scope_unknown` 当成全局阻断理由。
6. 不把测试通过写成 specs 已经完全收敛。
7. 不把本文作为规则源长期引用；本文只能指导下一轮 specs patch。

## 8. 下一步交付物

建议下一步正式交付：

1. `specs/01` 新增或授权附件化的 Hook 行动边界表；
2. `specs/09` 自锁事故验收矩阵，或在 `09` 待补齐事项中明确其最小覆盖；
3. 必要时更新 `tests/code/test_ldvh_specs_validate.py` 的字符串哨兵，确保 `01` 表不会被后续删弱；
4. 复跑 specs validation、相关 targeted tests 和 diff check；
5. 安排只读复审，重点看 repair 是否被写成 bypass、unknown 是否被写成全局阻断、completion 是否误阻断环境正常停止。
