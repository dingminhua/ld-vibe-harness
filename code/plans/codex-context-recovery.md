# Codex startup/resume 有界责任候选恢复实现规划

## 1. 规划身份与基线

本规划承接 `workcase-0007` plan version 1，只覆盖共享上下文恢复与 Codex 薄 adapter 的同一关闭判断。规则权威保持单向：02 定义工作对象、登记项目候选与恢复绑定边界；05 定义 F0–F4、完整 coverage 与 Helper 输入/回显；21 定义 WorkCase 当前绑定、唯一机械候选与 active items；09 定义共享交付投影和 adapter 映射。Code 不把唯一配置项、唯一非终态 WorkCase、Git dirty、标题或顺序提升为当前任务。

当前只读基线为 Codex `0.145.0-alpha.18`。两个固定回归 fixture 的现有完整 `additionalContext` 分别为 27,831 和 9,660 UTF-8 bytes；新输出预算固定为 13,915 和 4,830 bytes。预算测量包含 adapter 固定前缀与共享投影，并隔离时间戳、临时路径长度等非目标波动。

## 2. 模块责任与依赖

依赖方向固定为：02/05/09/21 → governance/fact Helper 只读结果 → `ldvh.hooks.context_recovery` 共享投影 → Codex adapter。

| 模块 | 责任 | 明确不负责 |
|---|---|---|
| `ldvh.governance` / `resolve-governance-scope` | 返回对象管辖结论及完整有效的登记项目候选 | 为环境选择自然语言任务、把 workspace 根改写 governed |
| `find-fact-object-candidates` / `read-fact-objects` | 提供 F0/F1 分页和精确 F3 读取 | 判断当前 WorkCase 或生成环境文本 |
| `ldvh.hooks.context_recovery` | 运行只读调用、验证页间连续性、形成内部 binding 与 bounded recovery projection | 修改事实、授权、判断语义适用或完成 |
| `code/plugins/ldvh/scripts/codex_context.py` | 验证 Codex payload、调用共享入口、把完整投影包装为 `additionalContext` | 解析 Helper 原始 JSON、重算候选或 binding |
| packaging/configuration | 分发同一共享实现与薄 adapter，验证兼容配置 | 自动安装、信任或扩大用户/工作区范围 |

共享 function/runner 的输入闭集为 `helper_executable`、`workspace_root`、唯一 `work_object_locator`、`helper_cwd` 与可选 `current_workcase_ref`。后者只允许 `{governed_project_id, fact_type_key, object_id}` 稳定三元组，且 `fact_type_key` 必须为 `workcase`；它由调用共享入口的上层维护者显式提供。当前 Codex 事件 payload 没有该字段，因此 Codex adapter 固定省略/传 `null`，不得从 cwd、event、source 或其它 payload 字段补造。

## 3. 登记项目候选与项目 binding

`resolve-governance-scope` 的领域结果增加 `registered_project_candidates` 闭集投影。候选只来自 `config_status=valid` 的全部登记条目及其现场 Git worktree/common-dir 身份，按项目 ID 排序；其它配置状态固定为空。该数组不参与 `scope_status`。

共享恢复首先保留普通 `governed_single` 对象的实际 worktree binding。输入对象是与显式 `workspace_root` 同一真实路径的非管辖 workspace 根时，只有候选完整且恰有一项才形成恢复项目 binding；零项、多项、配置/身份不完整或路径不相等均为 `unresolved`。后续事实调用使用选中候选的实际登记 worktree，原管辖响应仍保留 workspace 根 `non_governed`。

候选集合完整但无法全部装入交付预算时，投影仅保留总数/已交付数/省略数、来源和重新调用 `resolve-governance-scope` 的展开入口，`delivery_coverage=incomplete`、project binding 与 WorkCase binding 均为 `unresolved`。不得根据被截断后的零/一/多项建立绑定。

## 4. WorkCase coverage、binding 与投影

选定项目后，恢复以 F1 默认请求继续全部 `next_cursor`。每页必须保持 governed project、card layer、page size、Schema fingerprint 和 object-set fingerprint；cursor 只消费上一页返回值。任何非 `ok`、coverage 非 complete、指纹/查询漂移、无效/不可读对象、页循环、资源或时间预算中断都使 WorkCase coverage `unresolved`，不得按已返回卡片数量作全量判断。

只保留 `open`/`blocked` WorkCase 卡片。调用方提供精确 `current_workcase_ref` 时，先确认它属于当前项目和全量候选，再使用 `read-fact-objects` 展开；没有精确引用时，恰有一个候选可以作为 `sole_mechanical_candidate` 展开，但 `current_binding` 仍为 `unresolved`。零个候选明确为没有机械候选而不是当前任务不存在；多个候选全部保留最小卡片，不排序选中。

展开投影包含稳定引用、status、phase、summary、条件适用的 resume/waiting 字段，以及所有 in_progress/blocked work item。active items 按 item ID 排序，只复制对象中实际存在的条件字段和 evidence locator。

Helper coverage 完整但全部 F1 卡片无法装入输出预算时，保留已独立成立的 `project_binding=bound`，设置 `delivery_coverage=incomplete` 和 `workcase_binding=unresolved`，并保留总数/已交付数/省略数、来源和展开入口。不得以截断后数量建立 sole candidate，也不得把 Helper coverage 改写为投影 coverage。

## 5. 有界恢复投影与按需展开

共享入口返回内部 `ldvh-context-recovery/1` 投影，不再把原始 exchange 数组作为 adapter 正常输出。投影至少包含：

- `project_binding`：`bound|unresolved`、选中项目、候选与来源；
- `workcase_binding`：`bound|unresolved`、精确或 sole-candidate 原因、coverage 与候选；
- `delivery_coverage`：`complete|incomplete`、项目候选和必需 F1 卡片的总数/已交付数/省略数；
- `operations[]`：operation key、outcome、完成/未完成范围计数、来源 locator、gap/diagnostic 摘要；
- 可用时的 `workcase` 最小展开和 `active_items[]`；
- `expand[]`：可重新调用的 Helper operation key 与最小请求，不复制授权或语义判断。

投影不包含完整 Helper response、完整 fact object、规则全文、逐项重复来源 details 或原始异常。缩减只改变呈现，不改变实际 Helper 调用、outcome、coverage 或 unresolved 判断。相同冻结 fixture 必须满足完整 `additionalContext` byte budgets。

## 6. 失败、兼容与诊断

共享入口继续验证 Helper contract、operation key、outcome/exit code 和 JSON。单个读取失败进入对应 operation 摘要，并使受影响 binding unresolved；不得退回旧缓存或原始 `cwd` 猜测。

资源预算冻结为：F1 `page_size=100`，最多 8 页，最多接收 800 张匹配卡片，从首次管辖调用前开始的 monotonic 总 deadline 为 20 秒，整条恢复最多 10 次 Helper operation（1 次管辖 + 8 页 F1 + 1 次 F3 读取）。总 deadline 小于 adapter 对 runner 的 30 秒超时；每次 Helper 调用使用当时剩余 deadline 作为更小的超时。第 8 页后仍有 `next_cursor`、卡片数超过 800、操作数将超 10 或 deadline 不足时立即停止新读取，保留已完成范围，增加 `resource_budget_exceeded` diagnostic，使受影响的 coverage、delivery 与 binding 为 incomplete/unresolved。

Codex adapter 仍只接受其已声明事件/payload，调用共享 runner 并验证 `ldvh-context-recovery/1`。配置是否升版只由实际字段兼容性决定。`startup|resume` 进入真实验证范围；`clear|compact|SubagentStart` 只固定共享映射不回归，不由本增量声明真实通过。

## 7. 测试与验证映射

| 风险 | 主要检查 |
|---|---|
| workspace 候选冒充 governed | 02 resolver/operation tests 断言 scope 不变、候选闭集和零/一/多分支 |
| 任意扫描或路径猜测 | 配置外相邻 repo、名称相似、remote 相同均不进入候选 |
| F1 单页冒充完整 | 多页、cursor 漂移、指纹漂移、partial、invalid/unavailable、页循环与预算测试 |
| sole candidate 冒充当前绑定 | 无精确 ref 时始终 unresolved；精确 ref 正反与跨项目拒绝 |
| active item 补造或选一 | 零/一/多 in_progress/blocked，条件字段与 evidence 出现矩阵 |
| 输出缩减吞缺口 | operation/outcome/scope/source/gap/diagnostic/binding/expand contract tests |
| byte budget 只测子对象 | 两个固定完整 adapter output fixture 分别断言 ≤13,915/4,830 bytes |
| adapter 复制语义 | adapter fixture 只验证调用与原样投影，候选逻辑只在共享 tests |
| installed snapshot 漂移 | wheel/sdist/context runner/plugin packaging tests |

规则差异在生产 Code 消费前按 01 完成独立语义复核。实现后先运行聚焦 tests 与 Ruff，再运行 full-v4。当前用户 Codex 安装、升级、停用或恢复不由本规划授权；必须先按 33 回读当时实际版本、安装对象、用户资产、净变化和逐对象回滚，另行进入 09 Human Gate。

## 8. 明确排除

不新增 Helper 公开操作或事实字段，不修改 WorkCase 生命周期，不实现语义相关性或自动完成，不修复 `requested_disclosure` 通用请求 bug，不承接 clear/compact/SubagentStart 的真实环境声明，不扩展到其它环境、用户、Windows、Web、发布、push 或 PR。
