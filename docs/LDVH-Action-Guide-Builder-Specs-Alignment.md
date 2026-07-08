# LDVH Action Guide Builder Specs 对照表

日期：2026-07-08

## 0. 文档性质

本文是 Action Guide builder 实现前的 specs 对照表，不是正式 specs、不是事实源实例、不是实现授权，也不替代 Human Gate。

本文只回答一个问题：在进入 Code builder 之前，哪些 Action Guide 职责已经由 specs 定义，哪些只能作为实现欠账推进，哪些一旦需要新增语义就必须回到 specs。

## 1. 判断锚点

1. `specs/00-理念与构成.md` 是目标层，不因 builder 实现而修改。
2. `specs/01-保障与衔接.md` §7 是 Action Guide 本体职责来源。
3. `specs/07-Code确定性执行规范.md` 只定义 Code 如何消费和输出，不反向定义 Action Guide 规则。
4. `specs/10-安装与配置规范.md` 定义管辖项目、`scope_status` 和项目事实源入口。
5. `specs/09-测试与验证规范.md` 定义验证入口选择、完成声明和未验证范围。
6. Code builder 只能把这些规则编译成当次任务导航输出；不得新增规则源、授权、事实源、Human Gate 或完成证明。

## 2. 总体结论

当前 specs 已足够支持一个最小 Action Guide builder，但只能实现“导航投影”和“缺口暴露”，不能实现授权、状态推进、自动恢复、长期缓存或 Human Gate。

最小 builder 应从现有 `build_action_guide` 扩展，而不是另起第二套规则系统。当前 Code 已有基础输出：`task_read_plan`、`stop_conditions`、`validation_guard`、`next_queries`、`source_refs`、`impact_summary`、`capability_gap`、`unverifiable`、`scope_status` 和项目事实源入口分流。待补的是：`task_context`、`relationship_projection`、`read_order` 的更完整语义、`read_mode`、`guide_receipt` / brief、`suggested_sections` 和更强的渐进式披露。

## 3. 输入对照

| 输入 | specs 来源 | 当前 Code 状态 | builder 要求 | 禁止事项 |
|---|---|---|---|---|
| 用户目标 / task | `01` §7.2 | `build_action_guide(task=...)` 已接收 | 只能作为任务导航上下文，不得由 Code 猜测价值取舍 | 不得把自然语言理解写成事实源或授权 |
| cwd / target / target_paths | `10` §6-7、`01` §7.4 | 已进入 resolver 和 runtime payload | target-first；缺 target 时按 `missing_fields` / `governed_target_unknown` 分流 | 不得用 cwd、路径相似或对话记忆替代 target |
| `scope_status` | `10` §6-7、`01` §7.4 | 已输出六类 scope status | 按 `governed_single`、`non_governed`、`scope_unknown`、`governed_target_unknown`、`declared_multi_governed`、`mixed_scope` 分流 | 不得用布尔 governed 替代六类分流 |
| specs / attachments | `01` §7.1-7.3、`04` 结构规则 | 已解析 identity、role_sections、requirements 等部分结构 | 只读取正式 specs 和授权附件，保留 source_refs | 不得从 docs/code docs 反向定义规则 |
| 事实对象 / WorkCase / Spark / Study / ADR | `01` §7.1-7.2、`03`、成员规范 | 当前 builder 对项目事实源仅定位入口，未充分投影对象关系 | 可作为任务脉络和关系投影输入；是否权威按事实源规则判断 | 不得把过程输出或测试 fixture 写成事实实例 |
| 项目事实源入口 | `10` §8、`01` §7.4 | 已按 `governed_project_path/ldvh-base/` 输出可用 / 缺失 | `governed_single` 才能生成单项目事实源 read_plan；`declared_multi_governed` 必须拆分 | 不得 fallback 到 LDVH 本体 `ldvh-base/` |
| receipt / acknowledged paths | `01` §5.6、§6.8、§7.3 | runtime cache / acknowledge 已有基础 | 只作为当次过程输出和消费依据 | 不得作为事实源、授权或长期健康状态 |
| 验证入口 / testing result | `09` | test runner 已有 `verification_plan` | 作为 `validation_guard`、未验证范围和 residual risk 输入 | 不得用测试通过替代完成声明或 Human Gate |

## 4. 输出对照

| 输出 | specs 来源 | 当前 Code 状态 | builder 待补 | 验收口径 |
|---|---|---|---|---|
| `task_context` | `01` §7.3 | 未成形 | 输出当前任务、目标对象、已知事实、关键约束、当前阶段 | 不能是自由摘要；必须可回指 source_refs |
| `relationship_projection` | `01` §7.1-7.3 | 未成形 | 投影 specs、附件、事实对象、WorkCase、证据、测试、环境入口关系 | 只能实时生成，不缓存成事实源 |
| `task_read_plan` | `01` §7.3、`02` 行为要求 | 已有 | 保留 P0/P1/P2/P3、source_type、role、reason；支持项目 facts | 不得生成空 read_plan 后继续写入 |
| `read_order` | `01` §7.3 | 当前由 priority / role 间接表达 | 明确读取顺序和角色：authority / context / verification / fallback | P0/P1 必须有语义上限 |
| `read_mode` | `01` §7.1-7.3 | 未实现 | 支持 `result`、`contract`、`section`、`full` | 需要回读权威原文时必须升级 section/full |
| `guide_receipt` | `01` §7.3、receipt 边界 | 未实现 | 同 session/cwd/target/action hint 已消费时返回 brief / receipt | receipt 不得成为授权或事实源 |
| `suggested_sections` | `01` §7.3 | 未实现 | 输出章节、字段、对象、关系或证据片段 | 只作导航；source_refs 不足时必须暴露缺口 |
| `next_queries` | `01` §7.3 | 已有基础 | 承接 P2/P3、跨项目召回、远关系展开、未验证范围 | 不得默认全文注入跨项目上下文 |
| `stop_conditions` | `01` §7.3、`02`、`09` | 已有 | 保留 requirement_id、condition、disposition | 触发时必须暂停、分流或 Human Gate |
| `validation_guard` | `01` §7.3、`09` | 已有 | 映射到本次 completion/write/commit/handoff 前验证 | 不得写成“测试已通过所以完成” |
| `capability_gap` / `missing_fields` / `unverifiable` | `01` §5.7、§7.2、`07` | 已有 | 作为 builder 的主要失败态和 degraded 输出 | 不得静默或伪造完整导航 |
| `impact_summary` | `01` §7.3 | 已有路径级基础 | 扩展到 specs / facts / tests / Hook / Web / env 影响面 | 不得把影响判断写成事实状态 |

## 5. 分流对照

| `scope_status` / 场景 | builder 行为 | 禁止事项 |
|---|---|---|
| `governed_single` | 可生成单项目任务脉络、项目事实源 read_plan、source_refs、validation_guard、impact_summary | 不得把目录存在写成事实实例存在或 Hook integrated |
| `non_governed` | 静默 no-op；不输出 LDVH guidance、项目事实源 read_plan、deny 或 completion warning | 不得干预非管辖项目 |
| `scope_unknown` | degraded；输出 `missing_fields`、`capability_gap`、`unverifiable` | 不得把 unknown 当作管辖对象注入行动指南 |
| `governed_target_unknown` | 要求补 target、拆分范围或 Human Gate；target 清楚前不得生成项目事实源 read_plan | 不得用工作区根或对话意图替代 target |
| `declared_multi_governed` | 只读审计 / 对比可按每个 `governed_subject` 拆分 read_plan、source_refs、风险和验证 | 不得合并成一个不可拆行动指南 |
| `mixed_scope` | 写入、提交、迁移、事实源回写必须阻断、拆分或 Human Gate | 不得用其中一个项目 read_plan 覆盖全部 target |
| source_refs 不足 | 输出 `unverifiable` 或 fallback，并说明不足 | 不得生成看似完整的任务导航 |
| 规则冲突 / 高影响判断 | 升级到 `section` / `full` 读取，并进入 Stop Conditions 或 Human Gate | 不得用短契约掩盖冲突 |

## 6. 渐进式披露对照

| 层级 | 用途 | 触发 | 禁止事项 |
|---|---|---|---|
| `result` | 只消费 Code / Action Guide 派生出的当前任务结论 | 普通执行、低风险复用、已有可信 source_refs | 不得用于修改权威文件 |
| `contract` | 消费可审计短契约和关键边界 | 会话入口、常见写入前检查、重复任务 | 不得替代必要章节读取 |
| `section` | 读取指定章节、字段、对象或证据片段 | 修改目标文件、source_refs 不足、规则冲突、Human Gate / Stop 相关 | 不得把章节读取写成全文已读 |
| `full` | 读取完整文件 | 核心规范修改、事实对象结构修改、高影响声明、冲突无法局部判断 | 不得默认对所有相关文件全文注入 |

负担控制规则：

1. P0 / P1 默认必须数量受控，并说明为什么是当前任务必要输入。
2. P2 / P3、跨项目召回和远关系展开默认进入 `next_queries`、影响面判断或 fallback。
3. 同 session、cwd、target、action hint 和输入摘要未变化时，可以只返回 `guide_receipt` / brief。
4. brief / receipt 只降低重复输出，不降低规则要求；遇到冲突、高影响或 source_refs 不足必须重新展开。

## 7. 当前 Code builder 缺口

| 缺口 | 当前证据 | 建议实现顺序 |
|---|---|---|
| `task_context` | `build_action_guide` 尚未输出 | 先用 task、target、scope_status、consumption_timing、当前 stage 组成结构化字段 |
| `relationship_projection` | 现有 `source_refs` 和 `impact_summary` 只覆盖路径和 requirements | 从 specs role_sections、事实对象引用、WorkCase/Spark 状态和 project facts 生成实时关系投影 |
| `read_mode` | 当前只有 priority/role | 给 read_plan 项补 `read_mode`，默认 `contract`，目标修改 / source_refs 不足时升级 `section/full` |
| `guide_receipt` / brief | runtime receipt 有基础，但 builder 未输出 | 不写长期缓存；先输出 deterministic receipt key / input fingerprint 候选，由 runtime cache 承接 |
| `suggested_sections` | 当前无章节级定位 | 先从 role_sections、member specs、fact object type 和 target 类型派生 |
| P0/P1 上限 | 当前 `priority_for_ref` 静态返回 P0/P1/P2 | 增加预算字段和 overflow 到 `next_queries` |
| 项目事实源内容投影 | 当前只定位 `ldvh-base/` 入口 | 先只做索引级读取和 source_refs；不解析业务语义，不跨项目全文注入 |
| 测试覆盖 | 已有 governed project / no-op / scope_unknown / mixed_scope 测试 | 新增 builder 字段快测、渐进式披露快测、负例：不能输出授权 / 完成证明 |

## 8. 进入 Code builder 的允许范围

可以直接作为实现欠账推进：

1. 在现有 `build_action_guide` 输出中增加 `task_context`、`relationship_projection`、`read_mode`、`guide_receipt`、`suggested_sections`。
2. 给 `task_read_plan` 增加 disclosure / budget / overflow 信息。
3. 增加 tests，覆盖字段存在、no-op、scope_unknown、declared_multi_governed、mixed_scope、渐进式披露和非授权语义。
4. 更新 CLI / session_start 文本输出，使其展示 brief / receipt 和关键 next_queries。

必须回到 specs 再做：

1. 新增 Action Guide 状态机、长期缓存、事实源实例或 Web 数据契约。
2. 让 builder 自动判断 Human Gate 已完成、风险已接受、对象已关闭或任务已完成。
3. 让 builder 修改事实源、推进 WorkCase 状态或写入项目配置。
4. 新增 `scope_status`、读取层级、canonical event 或 receipt 语义。
5. 允许非管辖项目输出 LDVH guidance、deny 或 completion warning。

## 9. 建议下一步

1. 安排只读复审本文，确认它没有把 docs 变成规则源，也没有遗漏旧知识地图能力。
2. 若复审通过，提交本文作为 builder 前审计材料。
3. 下一步再进入 Code builder 最小实现：先补结构化输出和 tests，不改 Hook 安装、不改 Human Gate、不改事实源状态。

