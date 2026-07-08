# LDVH 全量待办汇总与外部评审计划

日期：2026-07-08

文档定位：汇总此前讨论中已经识别出的待办、决策、边界、风险和未决问题，并吸收独立审计后的执行排序，供 Human、主控 AI、子 agent 和外部 AI 进行整体评审。

文档性质：评审草案，不是 specs，不是事实源实例，不是行动授权，不替代 Human Gate。任何正式规则修改仍必须回到对应 specs，并按 Human Gate 要求执行。

相关材料：

- `specs/00-理念与构成.md`
- `specs/01-保障与衔接.md`
- `specs/02-AI行为规范.md`
- `specs/03-事实源与Git溯源规范.md`
- `specs/07-Code确定性执行规范.md`
- `specs/09-测试与验证规范.md`
- `specs/10-安装与配置规范.md`
- `specs/21-WorkCase-工作项.md`
- `specs/attachments/01.Att.01-保障消费时机表.md`
- `specs/attachments/10.Att.01-管辖项目配置字段表.md`
- `specs/attachments/21.Att.01-orchestration字段契约表.md`
- `/private/tmp/ldvh-review/LDVH-00-Communication-Notes.md`

## 0. 本文要解决的问题

此前讨论已经拆出了很多问题，但它们散落在临时记录、hook review、重构计划、能力调查和 specs 修改中。Human 的当前要求是：

> 把所有已经讨论出来要做的事情汇总起来，形成一份可以交给其它 AI 审核的完整材料。

因此，本文不是再提出一个新方向，而是把现有讨论收敛成：

1. 已确认的原则；
2. 已经做过或部分做过的事项；
3. 仍需做的事项；
4. 每项的责任归口；
5. 优先级；
6. 外部 AI 应该重点评审的问题。

## 1. 总目标

LDVH 的总目标不变：

> LDVH 服务于 AI 在持续 Vibe Coding 中准确行动，降低概率性推理、上下文依赖和无状态带来的风险。

当前要修复的不是某个单点 Hook，也不是补一个工具，而是让 `00` 的目标能够被下位规范、事实源、Code、Action Guide、Hook、测试和 Human 协作稳定承接。

## 2. 已确认的上位决策

| 编号 | 决策 | 状态 | 说明 |
|---|---|---|---|
| D1 | 当前不修改 `00` | 已确认 | `00` 是最高目标锚点；实现细节下放到对应 specs |
| D2 | `00` 是一切起点 | 已确认 | 其它机制只是实现 `00` 的方法 |
| D3 | LDVH 第一服务对象是 AI 准确行动 | 已确认 | 约束、阻断、验证、回写都是手段 |
| D4 | Hook 不是规则源 | 已确认 | Hook 是环境入口或触发器，不替代 specs / Human Gate |
| D5 | Action Guide 不是授权器 | 已确认 | 它是 AI 当前行动前的承接包 |
| D6 | 过程输出不是事实源 | 已确认 | receipt、diagnostic、Action Guide、测试输出都不能自动变成事实源 |
| D7 | 只影响可技术归口的管辖对象 | 已确认 | 非管辖对象 no-op；归口不明不得擅自扩大作用域 |
| D8 | 当前不处理远端主线增强 | 已确认 | 当前聚焦 action-time 保障、本地可复跑验证和事实源闭环；也不得依赖未纳入当前计划的增强来降低现有本地门禁要求 |
| D9 | V2 删除准备度必须围绕 V3 的 `00` 审核 | 已确认 | Human 已审核把握 V3 的 `00`，其它 V2 内容按 `00` 判断是否迁移 |

## 2.1 子 agent 复审采纳口径

子 agent `Laplace` 已对本文第一版做只读复审。本文采纳以下意见：

| 复审意见 | 处理 |
|---|---|
| 外部评审输入不完整 | 已补 `01`、`02`、`03`、`07`、`09`、`10`、`21` 和关键附件 |
| P0/P2 优先级冲突 | 已把 code-first self-lock 修复、runtime scoping 和 shim 漏洞复核上移到 P0 |
| 缺少 `session_start` / `completion_claim` scoping P0 | 已加入 P0 验收 |
| `01 §12` “当前无缺口”与当前认知冲突 | 已列为 P0 spec-first + Human Gate 待办 |
| 多处事项缺少唯一主归口 | 已在 §4 增加主归口 / 协作归口 / 执行类型总表 |
| 测试 L0-L5 可能重复发明规则 | 已明确 L0-L5 只能映射到 `09` 现有验证入口，不得成为第二套规则源 |
| 顶层 WorkCase 承接不足 | 已列为 Human 决策项 |
| 远端主线增强被过度排除 | 调整采纳：当前不建设、不纳入计划；但也不得用它作为现有本地门禁降级的前提 |

## 2.2 独立审计吸收口径

外部独立审计已完成，本文吸收其源码核实后的结论。审计报告本身不作为长期保留文档；以下结论已进入本文主表。

| 审计结论 | 本文吸收方式 |
|---|---|
| 分层 diagnostic、target-scoped blocking、repair_mode、non_governed no-op、runtime receipt cache、sed-i 修复大体已实现 | 从 P0 实现项降级为测试覆盖确认或漂移治理 |
| repair lane Code 已实现，但 `01/07/09` 没有 specs 契约 | 已完成 P0 specs 回写；后续保留测试和实现对齐复核 |
| `01/02/07/09` 的待补齐口径与当前缺口认知不一致 | 已完成四处待补齐事项同步修正；后续按缺口清单推进 |
| completion_claim 只检查 evidence 非空，不消费 preflight diagnostic | P1 已开始承接：runtime 已消费 target-scoped preflight diagnostic，真实环境 completion / Stop 可见性仍需验收 |
| Code 顶层无显式六类 `scope_status` | P1 已开始承接：resolver、preflight 和 runtime summary 已补本地输出，仍需真实多 target 使用验收 |
| Code 不支持 `declared_multi_governed` | P1 已开始承接：只读 / 审计 / 对比路径已补本地 resolver 分流，写入和提交仍保持 mixed_scope 阻断 |
| cwd 在 ldvh_root 内且无 receipt 时，生成 receipt 的入口也会被 Hook 拦截 | P1 已开始承接：Code / shim 已补 `acknowledge_read_plan` bootstrap allowance 和回归，仍需真实环境当次验收 |
| Codex / WorkBuddy shim sed-i 已对齐，但命令分类已有 `&` 漂移 | 新增 P1：抽共享分类器 |

## 3. 已讨论出的工作总表

### 3.1 `00` 理解与下位拆解

问题：

- AI 一度把 Hook、Code、测试、远端门禁、文档结构等机制当成目标本身；
- Human 校正：`00` 是目标，后续都是方法；
- 当前不能把实现细节塞进 `00`，否则 `00` 会失去最高锚点作用。

待办：

| 事项 | 归口 | 状态 | 优先级 |
|---|---|---|---|
| 保持 `00` 不改 | Human + specs governance | 已确认 | P0 |
| 把 `00` 目标映射到 `01`、`07`、`09`、`10`、事实模型 | specs | 部分完成 | P0 |
| 记录“LDVH 服务 AI 准确行动”为下位规范解释原则 | `01` / `02` | 待确认是否需要正式吸收 | P1 |
| 避免用机制反向定义目标 | review checklist | 待做 | P1 |

外部 AI 需评审：

- 当前是否正确保持 `00` 不动；
- 哪些内容如果不写入 `00` 会导致目标失真；
- 哪些内容其实只是下位实现，不应进入 `00`。

### 3.2 V2 收口与删除准备度

问题：

- Human 正在准备关闭 V2；
- 但担心 V2 的关键内容没有迁到 V3；
- Human 明确自己审核过 V3 的 `00`，其它内容不确定；
- 因此 V2 迁移审核不能按“把 V2 全部搬过来”，而应按“是否服务 V3 的 `00`”判断。

待办：

| 事项 | 归口 | 状态 | 优先级 |
|---|---|---|---|
| WorkCase 0024 承接 V2 deletion readiness | WorkCase | 已存在，仍需收口 | P0 |
| 汇总 V3 specs / workcases / sparks 中提到 V2 的待办 | Code + review | 部分做过，需复核 | P0 |
| 判断每个 V2 残留是否服务 V3 `00` | 主控 AI + Human | 待做 | P0 |
| 明确 Git history 是追溯手段，不是默认上下文来源 | `03` / review | 已被 `03` 吸收，仍需 V2 残留扫描验证 | P1 |
| 删除或关闭过期测试、临时检查、旧迁移承诺 | docs / specs / tests | 部分做过，需复核 | P1 |

外部 AI 需评审：

- V2 收口是否应该以 V3 `00` 为筛选标准；
- 是否还有 V2 关键机制没有被 V3 的 specs / Code / tests 承接；
- 是否存在“V2 概念换名后残留”的风险。

### 3.3 Hook governance 与 self-lock 修复

问题起因：

- AI 写坏事实源；
- LDVH 随后因全局事实源诊断阻断无关写入；
- 修坏对象本身也可能被同一个全局阻断挡住；
- 这说明 preflight / runtime 把全局健康和当前动作阻断混在一起。

已讨论结论：

- 修法是 scoping，不是 dedupe；
- `summary.blocking` 只能统计当前动作应阻断的 `target_primary` 和 `runtime_blocker`；
- `unrelated_global` 应保留为 diagnostic / residual risk，但不阻断无关写入；
- repair lane 应作为 `pre_tool_use mode=repair`，不是新增 runtime event；
- repair final validation 仅验证 primary target 及必要 direct dependent；
- `sed -i` 只读误判是实锤洞，需要修 Codex / WorkBuddy shim；
- bypass / break-glass 如后续需要，必须是单次、可见、不可写入正式事实源。

待办：

| 事项 | 归口 | 状态 | 优先级 |
|---|---|---|---|
| repair lane specs 契约回写 | `01` / `07` / `09` | 已在 01/07/09 承接；后续保留测试和实现对齐复核 | P1 |
| diagnostic 分类：`target_primary` / `target_cascade` / `unrelated_global` / `runtime_blocker` | Code + tests | 已实现，保留测试覆盖确认 | P1 |
| runtime event builder / preflight target-scoped blocking | Code + tests | 已实现，保留回归确认 | P1 |
| `ldvh.session_start` / `ldvh.pre_tool_use` scoping 验收 | Code + tests | 已实现，保留回归确认 | P1 |
| `ldvh.completion_claim` 完成前诊断消费 | `01` / `07` / Code | runtime 已消费 target-scoped preflight diagnostic；真实环境 completion / Stop 可见性仍需验收 | P1 |
| repair final validation 仅验证 primary target 及必要 direct dependent | `09` / tests | specs 已承接，测试仍需确认 | P1 |
| `sed -i` 分类洞修复 | hooks / tests | 已修复 | P1 |
| Codex / WorkBuddy shim 共享分类器 | Code + hooks | `sed -i` 已对齐，但命令分类出现 `&` 漂移 | P1 |
| bypass 契约 | `01` + Human Gate | 后置，不急 | P2 |
| quarantine lane 评估 | design | 后置 | P2 |

外部 AI 需评审：

- target-scoped preflight 是否会误放过真正应阻断的问题；
- repair lane 是否会变成绕过机制；
- diagnostic 分类是否足够表达当前问题；
- Hook governance 是否仍有“总开关”倾向。

### 3.4 LDVH canonical event 与环境 Hook 边界

问题：

- 不同 AI 环境的原生事件名称、时机、payload 和阻断能力不同；
- LDVH 不能要求所有环境有同名事件；
- 应验收 LDVH 自己的 canonical event 是否正常；
- LDVH 事件必须带 `ldvh.` 前缀，与环境原生事件区分。

当前 specs 消费时机包括：

- `session_start`
- `acknowledge_read_plan`
- `pre_tool_use`
- `git_commit_msg`
- `human_facing_output`
- `external_output_intake`
- `diagnostic_disposition`
- `completion_claim`

待办：

| 事项 | 归口 | 状态 | 优先级 |
|---|---|---|---|
| 梳理 LDVH canonical event 名称和消费时机的关系 | `01` / attachments | 部分完成 | P0 |
| 建立 Hook 行动边界表 | `01` | 待做 | P0 |
| 为每个时机定义输入、输出、阻断、no-op、degraded、Human Gate | `01` / `07` | 待做 | P0 |
| 环境原生事件到 `ldvh.*` 的映射规则 | `01` / environment docs | 部分完成 | P1 |
| integrated 声明只基于当时可观测验收 | `01` / `10` | 已讨论，需复核 | P1 |
| Codex / WorkBuddy 行为边界与 payload parity | hooks / tests | 待复核 | P1 |
| hook bootstrapping 死锁 | `01` / `07` / Code | Codex / WorkBuddy shim 已补 `acknowledge_read_plan` 受控 bootstrap allowance；仍需真实环境当次验收 | P1 |

外部 AI 需评审：

- 当前消费时机是否完整；
- 哪些时机应该由环境 Hook 承接，哪些只能由主控 AI / Code /行动模板承接；
- `ldvh.*` canonical event 设计是否足够避免环境绑定。

### 3.5 Action Guide 责任与管辖项目服务

问题：

- Action Guide 的概念已在 `01` 写出，但它如何服务管辖项目还不够清楚；
- Action Guide 之后要为管辖项目服务，通过管辖项目的事实源向 AI 提供信息；
- 当前 Code 实现可能更偏向 LDVH 本体 specs / facts，缺少项目事实源感知。

待办：

| 事项 | 归口 | 状态 | 优先级 |
|---|---|---|---|
| 明确 Action Guide 是行动前承接包，不是规则源 | `01` | 已有 | P0 |
| 定义 Action Guide for governed project | `01` / `07` / `10` | specs 契约已补；Code builder 待做 | P1 |
| 输出区分 LDVH specs、LDVH facts、governed project facts、process outputs | `07` | specs 契约已补；Code builder 待做 | P1 |
| 当 target 命中管辖项目时，读取或引用该项目 `ldvh-base/` 事实源入口 | `07` / Code | `10` / `07` 契约已补；Code builder 待做 | P1 |
| 只有 `governed_single` 才能生成项目事实源 read_plan；`non_governed` 静默 no-op；`scope_unknown` 只能 degraded / capability_gap | `01` / `07` / `10` | specs 契约已补；Code builder 待做 | P1 |
| 对多管辖项目任务按项目拆分 read_plan / source_refs / validation_guard | `01` / `07` / `10` | specs 契约已补；Code builder 待做 | P1 |
| Action Guide 缺输入时输出 `missing_fields` / `capability_gap` / `unverifiable` | `01` / Code | specs 契约已补；Code builder 待做 | P1 |

外部 AI 需评审：

- Action Guide 是否被过度赋权；
- 管辖项目事实源如何进入 Action Guide；
- 是否需要单独 schema，还是语义契约足够；
- source boundary 是否能防止过程输出伪装成事实源。

### 3.6 管辖范围与 target-first

问题：

- Hook 和 preflight 曾无法识别 `ldvh-base/workcases/...` 这类事实对象路径；
- 管辖对象判断不能是单一 `governed=true/false`；
- `scope_unknown` 不能擅自升级为管辖对象；
- Human 可能发起多管辖项目审计，例如同时审计两个扑克项目，需要和多项目写入区别处理。

已讨论并部分吸收的六类结果：

- `governed_single`
- `non_governed`
- `scope_unknown`
- `governed_target_unknown`
- `declared_multi_governed`
- `mixed_scope`

待办：

| 事项 | 归口 | 状态 | 优先级 |
|---|---|---|---|
| `10` 明确六类管辖解析 | `10` | specs 已改，保留复核 | P1 |
| `01` 消费六类解析 | `01` | 已部分改，保留复核 | P1 |
| `07` 要求 Code 输出六类解析和证据 | `07` | Code schema 已补 `scope_status`，保留真实使用验收 | P1 |
| `09` 测试覆盖六类解析正反例 | `09` / tests | 已补 resolver / preflight 关键正反例，仍需真实多 target 使用验收 | P1 |
| Code resolver 输出显式 `scope_status` 字段 | Code | 已补 resolver、preflight 和 runtime summary 输出 | P1 |
| 非管辖静默 no-op | Hook / Code | 已实现，保留测试覆盖确认 | P1 |
| `scope_unknown` degraded，不注入 LDVH guidance | Hook / Code | 待实现 | P1 |
| `declared_multi_governed` 只读审计路径 | `10` / `07` / Code | 已补只读 / 审计 / 对比 resolver / preflight 分流；写入和提交仍阻断 | P1 |
| 多管辖读取审计与多管辖写入分流 | `10` / `01` / tests | 已补本地 resolver 正反例，仍需真实多 target 使用验收 | P1 |

外部 AI 需评审：

- 六类是否足够；
- `scope_unknown` 的路径是否会产生分歧；
- 多管辖审计和多管辖写入的边界是否可执行；
- 是否还有 target 归口无法识别的基础设施缺口。

### 3.7 测试与验证分层

问题：

- 当前测试没有足够区分局部验证、目标验证、runtime 验证、环境插件验证和全局收口；
- AI 容易为了稳而默认跑大范围测试；
- 开发过程因此变慢；
- 但小测试又没有明确说明覆盖范围和未验证范围。

已讨论模型：

```text
target -> operation -> risk -> phase -> decision / verification_plan -> diagnostics -> residual_risk
```

候选 phase：

- `inner_loop`
- `handoff`
- `pre_commit`
- `closure`

候选测试层：

- L0 `smoke`
- L1 `target`
- L2 `runtime`
- L3 `hook/install`
- L4 `web`
- L5 `full`

这些层级只能作为 runner profile 或验证入口选择的表达方式，必须映射回 `09` 现有验证入口和验证语义，不得成为与 `09` 并列的第二套测试规则源。

待办：

| 事项 | 归口 | 状态 | 优先级 |
|---|---|---|---|
| 将验证选择协议映射到 `09` 现有验证入口 | `09` | 已由 runner `matrix_refs` 回指 `09 §5`，不新建第二套规则 | P1 |
| `07` 要求 test runner 输出 verification plan | `07` | 已同步为本地承接，保留回归要求 | P1 |
| test runner 输出选择理由、覆盖层级、未验证范围 | Code | 已实现 `VerificationPlan` 输出 | P1 |
| 修复 runtime-sensitive specs 改动可能只跑 smoke 的缺口 | tests | 已修复并补 targeted runner 自测 | P1 |
| 建立“不该 full”和“该升级”的 runner 自测 | tests | 已补关键自测；后续按新增 profile 继续扩展 | P1 |
| 更新测试实践文档 | docs / tests | 已更新 `tests/docs/01-Test-Runner-Practice.md` | P1 |

外部 AI 需评审：

- 这个模型是否能同时解决 preflight 分流和测试分层；
- L0-L5 是否过细或不足；
- 如何避免局部验证被误写成完成证明；
- 哪些 phase 需要更强验证。

### 3.8 事实源、receipt、diagnostic、evidence 边界

问题：

- 讨论中曾多次混淆“验收当时状态”“留证据”“标记状态”；
- Human 明确：验收都是当时状态，不是把状态标记为永久完成；
- receipt、diagnostic、evidence、事实源实例、Git history、测试输出必须区分。

待办：

| 事项 | 归口 | 状态 | 优先级 |
|---|---|---|---|
| 在 specs 中明确验收是当时状态 | `01` / `09` | 已讨论，需复核是否吸收 | P0 |
| receipt 不等于 evidence，不等于事实源 | `01` / `03` | 已讨论，需复核 | P0 |
| diagnostic 是分流输入，不是事实源 | `01` / `07` | 部分已有 | P0 |
| Git history 是追溯手段，不是默认事实消费入口 | `03` | 待确认 | P1 |
| 完成声明必须说明验证覆盖和未验证范围 | `02` / `09` | 部分已有，需复核 | P1 |

外部 AI 需评审：

- 当前边界是否足够防止 AI 把过程输出当成事实；
- 是否需要新增附件字段表；
- 是否还存在“留证据”口径导致误解。

### 3.9 WorkCase 与事实对象完整性

问题：

- WorkCase 是持续推进、恢复上下文、关闭判断、验证回写的核心对象；
- V2 迁移时曾把 WorkCase 完整字段 / orchestration 最小契约列为 P0；
- 事实对象坏掉会影响 Hook / preflight / completion。

待办：

| 事项 | 归口 | 状态 | 优先级 |
|---|---|---|---|
| WorkCase 完整字段 / orchestration 最小契约复核 | `21` + attachments | 需复核 | P0 |
| workcase-0024 V2 deletion readiness 收口 | WorkCase | 需收口 | P0 |
| 创建或指定顶层 WorkCase 承接本轮体系重构 | Human / `21` | docs 计划不能替代 WorkCase 事实对象 | P1 |
| workcase-0022 关闭策略 | WorkCase | Human 曾倾向直接关闭，需确认现状 | P1 |
| 事实对象引用错误的 repair / validation 路径 | `05` / `21` / Code | 部分设计，需落地 | P1 |
| circular reference 一次修 primary + direct dependent | Code / tests | 待复核 | P2 |

外部 AI 需评审：

- WorkCase schema 是否足以支撑恢复、关闭和验证回写；
- 是否还有 V2 中关键事实对象字段未迁入；
- WorkCase 错误是否会再次 poison 无关动作。

### 3.10 Git commit 契约

问题：

- Git commit-msg 是当前较真实接入的自动门禁；
- 但此前曾混淆“Git hook 完整”和“AI lifecycle Hook 完整”；
- Git hook 完整只能说明该 Git 事件已接入，不说明 session / pre_tool / completion 已接入。

待办：

| 事项 | 归口 | 状态 | 优先级 |
|---|---|---|---|
| commit message 契约字段和附件复核 | `03` / attachment | 已有，需复核 | P1 |
| commit type / scope / body 条件从 V2 迁移复核 | `03` | 需复核 | P1 |
| 非事实源排除清单复核 | `03` / Code | 需复核 | P1 |
| 明确 Git hook 只证明 Git 事件，不证明 AI lifecycle | `01` / `10` | 已讨论，需复核 | P0 |

外部 AI 需评审：

- Git hook 当前的证明范围是否表达清楚；
- commit 契约是否还有 V2 关键字段缺失；
- 是否把 Git hook 误当作环境 Hook。

### 3.11 文档结构与 specs 结构

问题：

- Human 质疑现在 LDVH 文档结构是否要变，文件名是否要变，是否要拆散；
- 附件有附件规范，不能变成子文档树；
- `code/docs` 只是实践文档，不是规范；
- docs 下的评审 / 计划 / 研究材料也不能替代 specs。

待办：

| 事项 | 归口 | 状态 | 优先级 |
|---|---|---|---|
| 明确 specs / attachments / docs / code/docs / facts 的层级边界 | `04` / docs governance | 待做 | P1 |
| 附件只承载字段表、矩阵、闭集、契约，不扩展成子规范树 | `04` | 待复核 | P1 |
| docs 作为评审、计划、研究，不具备规范权威 | docs governance | 待确认 | P1 |
| code/docs 只记录实践和实现说明，不反向定义 specs | `07` / code docs | 待确认 | P1 |
| 判断是否需要 V4 | Human + architecture review | 当前不建议立即开，除非 `00` 或结构目标发生根本变化 | P2 |

外部 AI 需评审：

- 当前文档层级是否自洽；
- 是否需要重命名或拆分 specs；
- 附件和 docs 的边界是否清晰；
- 是否真的需要新版本，还是 V3 内部重构即可。

### 3.12 能力模型与工具边界

问题：

- Human 指出：本质问题是 LDVH 想做什么，环境和各类工具可以做到什么，没有整理清楚；
- Codex、WorkBuddy 等 AI 环境应作为一个维度讨论，不应割裂；
- 01 必须既理解 `00` 意图，也理解可提供能力与限制，才能正确拆解。

已讨论能力维度：

- AI / Agent 环境；
- Hook / plugin / extension；
- Git Hook；
- Code / runtime adapter / validators；
- Tests；
- Web / Confirm UI；
- Git / 文件系统；
- Human Gate。

待办：

| 事项 | 归口 | 状态 | 优先级 |
|---|---|---|---|
| 形成能力匹配模型正文口径 | `01` | 待做 | P1 |
| 能力匹配模型附件化 | `01.Att` | 待做；附件只能承载矩阵，不承载核心规则 | P1 |
| 区分硬能力、软能力、不可掌握能力 | `01` / `07` | 待做 | P1 |
| AI 开发环境作为统一维度，provider 差异作为子项 | `01` / environment docs | 待做 | P1 |
| 任何能力缺口输出 `capability_gap` / `unverifiable` | `01` / `07` | 部分已有 | P1 |
| 避免把工具能力写成目标 | review checklist | 待做 | P1 |

外部 AI 需评审：

- 能力维度是否完整；
- 哪些能力 LDVH 能硬掌握，哪些只能软提示，哪些完全不能掌握；
- `01` 是否应该增加能力匹配模型。

### 3.13 01 拆解与重构

问题：

- `01` 既要承接 `00`，又要理解环境能力、Hook、Action Guide、diagnostic、receipt、Human Gate；
- 当前 `01` 有正确原则，但可能过重、过散、矩阵太薄；
- 拆得太细会破坏附件规范，拆得太少又难维护。

待办：

| 事项 | 归口 | 状态 | 优先级 |
|---|---|---|---|
| 判断 `01` 是否需要瘦身或分层 | Human + specs review | 待评审 | P1 |
| 同步修正 `01/02/07/09` 待补齐事项与当前缺口认知冲突 | `01/02/07/09` + Human Gate | 待做 | P0 |
| 补能力匹配模型 | `01` | 待做 | P1 |
| 补 Hook 行动边界表 | `01` | 待做 | P1 |
| 补 Action Guide governed project 模式 | `01` | 待做 | P1 |
| 补 consumption timing 与 canonical event 映射 | `01.Att.01` / `01` | 部分完成 | P1 |
| 不把 runbook 放进基础规范正文 | docs governance | 待复核 | P1 |

外部 AI 需评审：

- `01` 应该重构还是局部补强；
- 附件和正文如何分工；
- 哪些内容必须 spec-first，哪些只是 code practice。

### 3.14 Code 实现责任

问题：

- Code 既是执行能力，也是 Action Guide / preflight / runtime 输出来源；
- 但 Code 不能成为规则源或授权器；
- 当前实现仍可能没有完全对齐六类管辖解析和 Action Guide 管辖项目服务。

待办：

| 事项 | 归口 | 状态 | 优先级 |
|---|---|---|---|
| resolver 输出显式六类 `scope_status` | Code | 已补 resolver、preflight 和 runtime summary 输出；保留真实多 target 使用验收 | P1 |
| Action Guide builder 消费管辖项目事实源 | Code | 待做 | P1 |
| preflight 区分对象归口、动作条件、无关全局诊断 | Code | 已实现，保留回归确认 | P1 |
| runtime event 输出不把 global poison 注入所有事件 | Code | 已实现，保留回归确认 | P1 |
| test runner 输出 verification plan | Code | 已实现，保留 plan/stage 一致性回归 | P1 |
| Code 输出声明 authority / authorization / source boundary | `07` / Code | 部分已有，需复核 | P1 |

外部 AI 需评审：

- Code 是否被赋予了不该有的权限；
- 当前 Code 输出是否足够机器可消费；
- 哪些能力必须先有 specs 才能实现。

### 3.15 Human Gate 与失败处理

问题：

- Human 强调：如果保障机制失败，应该由人介入完善保障机制，不允许有自动恢复路径；
- 这不是禁止 repair，而是禁止未授权自动绕过或自动升级事实；
- Human Gate 需要清楚表达触发条件和消费方式。

待办：

| 事项 | 归口 | 状态 | 优先级 |
|---|---|---|---|
| 失败机制不得自动自愈的原则归口 | `01` / `02` / `09` | 待确认 | P1 |
| repair 与 Human Gate 边界 | `01` / `07` / `21` | 待做 | P1 |
| 状态推进、关闭、风险接受必须 Human Gate | `21` / `02` | 已有，需复核 | P0 |
| Human-facing output 必须呈现依据、风险、未验证范围 | `01` / `02` | 部分已有 | P1 |

外部 AI 需评审：

- 失败处理是否过度依赖 Human；
- repair 是否足够受控；
- Human Gate 是否会被 receipt、diagnostic 或 Action Guide 替代。

## 4. 优先级总排

本节是执行时的主表。前面分项表允许写协作归口；本节必须写清楚唯一主归口、协作归口和执行类型。

执行类型：

| 类型 | 含义 |
|---|---|
| `review-only` | 只读审计、整理意见，不改正式规则或代码 |
| `code-first bugfix` | 修复已确认实现 bug，不改变正式规则语义 |
| `spec-first + HG` | 先改 specs，且需要 Human Gate 后才能实施 |
| `code-after-spec` | specs 已明确后再实现 |
| `decision/HG` | 需要 Human 决策或 Human Gate，不能由 AI 自行推进 |
| `docs-governance` | 只整理评审、计划或实践文档，不具备规范权威 |

### P0-A：先把审稿包修到可评审

| 事项 | 主归口 | 协作归口 | 执行类型 | 说明 |
|---|---|---|---|---|
| 补全外部评审输入集 | 主控 AI | docs governance | `docs-governance` | 已补关键 specs 和附件 |
| 外部 AI / 子 agent 审核本文 | 主控 AI | Human | `review-only` | 只审完整性、归口、优先级 |
| 形成采纳 / 不采纳 / 待 Human 决策表 | 主控 AI | Human | `review-only` | 防止评审意见散落 |
| 固化 `00` 不改、下位承接的决策 | Human | specs governance | `decision/HG` | 作为后续所有行动前提 |

### P0-B：补最小 specs 责任（已完成）

| 事项 | 主归口 | 协作归口 | 执行类型 | 说明 |
|---|---|---|---|---|
| repair lane specs 契约回写 | `01` | `07` / `09` / Human | `spec-first + HG` | 已在 01/07/09 承接；后续补测试覆盖 |
| `01/02/07/09` 待补齐事项同步修正 | `01/02/07/09` | Human | `spec-first + HG` | 已同步修正为真实缺口清单 |
| 当前本地门禁要求不得因未纳入计划的远端增强而降级 | `03` | Code / Human | `decision/HG` | 当前只是不建设该增强，不等于放松已有门禁 |

### P1：运行链路、schema 与测试对齐

| 事项 | 主归口 | 协作归口 | 执行类型 | 说明 |
|---|---|---|---|---|
| hook bootstrapping 死锁 | `01` | `07` / Code | `code-after-existing-spec` | Code / shim 已补受控入口，仍需真实环境当次验收；receipt 生成入口本身不能被 read_plan 检查拦截 |
| completion_claim 消费当前 diagnostic | `01` | `07` / Code / tests | `code-after-existing-spec` | runtime 已补 target-scoped diagnostic 消费和回归；真实环境 completion / Stop 可见性仍需验收 |
| resolver 输出显式六类 `scope_status` | `07` | Code / `10` / tests | `code-after-existing-spec` | resolver、preflight 和 runtime summary 已补本地输出；仍需真实多 target 使用验收 |
| `declared_multi_governed` 只读审计路径 | `10` | `07` / Code / tests | `code-after-existing-spec` | Human 显式跨对象审计已补 resolver 分流；写入和提交仍阻断 |
| Action Guide governed project 链路 | `01` | `07` / `10` / Code | `code-after-spec` | specs 契约已补：10 入口、07 读取、01 消费；下一步补 Code builder 和回归 |
| 验证选择协议与 test_runner verification_plan | `09` | `01` / `07` / Code / tests | `spec-first + HG` -> `code-after-spec` | 映射到现有验证入口，不新建第二套规则 |
| 能力匹配模型附件化 | `01` | `07` / `10` | `spec-first + HG` | 正文定义口径，附件只承载矩阵 |
| runtime scoping / no-op / repair 回归覆盖确认 | tests | Code | `code-after-spec` | 已实现项保留回归保护 |
| Codex / WorkBuddy shim 共享分类器 | Code | hooks / tests | `code-first bugfix` | sed-i 已修，`&` 漂移需收敛 |
| 创建或指定顶层 WorkCase 承接全量待办 | Human | `21` / 主控 AI | `decision/HG` | docs 计划不能替代 WorkCase 事实对象 |

### P2：事实源、WorkCase 与 V2 收口

| 事项 | 主归口 | 协作归口 | 执行类型 | 说明 |
|---|---|---|---|---|
| WorkCase orchestration 复核 | `21` | Code / tests | `spec-first + HG` | 支撑恢复、关闭、验证回写 |
| workcase-0024 V2 deletion readiness 收口 | WorkCase | Human / 主控 AI | `decision/HG` | 按 V3 `00` 判断 V2 残留 |
| commit message / Git 溯源边界复核 | `03` | Code / tests | `spec-first + HG` | Git hook 证明范围不得外扩 |
| docs / specs / attachments / code docs 层级整理 | docs governance | `04` / `07` | `docs-governance` | 防止 docs 或 code docs 反向定义规范 |

### P3：后置评估

| 事项 | 主归口 | 协作归口 | 执行类型 | 说明 |
|---|---|---|---|---|
| 判断是否需要 V3 内部结构重构或新版本 | Human | architecture review | `decision/HG` | 当前不建议抢在 P0 前做 |
| 清理过期临时文档和过期测试 | docs governance | tests | `docs-governance` | 只清理确认过期内容 |
| 把外部能力调查整理成正式 Study 或 docs | 主控 AI | Human | `decision/HG` | 取决于 Human 是否要事实源化 |
| bypass / quarantine 评估 | `01` | Human / `07` | `spec-first + HG` | 后置；依赖 repair lane specs 契约，不得写入正式事实源 |
| 继续收敛 V2 遗留术语和路径 | WorkCase | specs governance | `decision/HG` | 依赖 workcase-0024 |

## 5. 建议执行顺序

建议不要直接进入大规模实现，而按以下顺序走：

1. **确认 P0 specs 小步补强已完成**：repair lane 契约已回写，`01/02/07/09` 待补齐事项已同步修正；
2. **Human 决策 WorkCase**：决定是否创建或指定顶层 WorkCase 承接本轮体系重构；
3. **收尾 P1 bootstrapping**：本地已实现 read_plan receipt 生成入口的受控放行路径，下一步补真实环境当次验收；
4. **收尾 P1 scope schema**：completion_claim、`scope_status`、`declared_multi_governed` 已本地补齐；后续保留真实环境 / 真实多 target 使用验收；
5. **补 Action Guide / 验证选择 / 能力模型**：Action Guide governed project specs 契约已补；下一步补 Code builder，再进入验证选择和能力模型；
6. **处理 shim 漂移和回归测试**：抽共享分类器，补 runtime scoping / no-op / repair / mixed scope 回归；
7. **V2 收口复核**：根据 V3 `00` 和补强后的 specs，重新判断 V2 是否可删除；
8. **提交与复审**：每个阶段可独立提交、复审、回退。

## 6. 外部 AI 审核任务说明

请外部 AI 不要直接假设本文正确，而按以下问题审：

1. 这份总表是否覆盖了前面讨论出的主要问题？
2. 是否仍有遗漏的 P0 基础问题？
3. 是否有把 `00` 目标改写成实现细节的风险？
4. 是否有把 Hook、Action Guide、Code、测试或 docs 提升为规则源的风险？
5. `01`、`07`、`09`、`10`、`21`、`03` 的责任归口是否合理？
6. V2 收口是否应该按 V3 `00` 判断，而不是按 V2 全量复制判断？
7. 六类管辖解析是否足以处理非管辖、unknown、多管辖和 mixed scope？
8. Action Guide 服务管辖项目事实源的定义是否足够明确？
9. target / operation / risk / phase 是否足以统一 preflight 与测试选择？
10. repair lane specs 回写是否足以约束已实现的 repair_mode？
11. completion_claim、hook bootstrapping、scope_status、declared_multi_governed 是否还有遗漏风险？
12. WorkCase 和事实对象 schema 是否还有必须先补的缺口？
13. 文档结构是否自洽：specs、attachments、docs、code/docs、hooks、facts 是否边界清楚？
14. 当前哪些事项必须先 Human Gate，哪些可以 code-first 修 bug？
15. 是否建议开新版本，还是应在 V3 内收敛？

## 7. 给外部 AI 的可复制提示词

```text
请独立复审 LDVH V3 当前全量待办汇总的“独立审计吸收版”：

仓库：/Users/dmh2002/poker_hud_projects/ld-vibe-harness-v3
主文档：docs/LDVH-All-Open-Work-Review-Plan.md
参考文档：
- specs/00-理念与构成.md
- specs/01-保障与衔接.md
- specs/02-AI行为规范.md
- specs/03-事实源与Git溯源规范.md
- specs/07-Code确定性执行规范.md
- specs/09-测试与验证规范.md
- specs/10-安装与配置规范.md
- specs/21-WorkCase-工作项.md
- specs/attachments/01.Att.01-保障消费时机表.md
- specs/attachments/10.Att.01-管辖项目配置字段表.md
- specs/attachments/21.Att.01-orchestration字段契约表.md
- /private/tmp/ldvh-review/LDVH-00-Communication-Notes.md

评审目标：
1. 判断独立审计结论是否已被正确吸收；
2. 判断 P0 specs 小步补强是否已正确完成；
3. 找出遗漏、职责混淆、优先级错误和过度设计；
4. 判断是否正确保持 00 不动，并把实现细节归口到下位 specs / Code / tests；
5. 特别审查 completion_claim、hook bootstrapping、scope_status、declared_multi_governed、Action Guide 管辖项目事实源、测试分层、V2 收口、WorkCase、Human Gate 的边界；
6. 输出 P0/P1/P2 问题清单，并说明每项建议归口。

请不要直接改文件，先给审计意见。
```

## 8. 当前结论

当前最重要的不是继续增加新机制，而是在 P0 specs 小步补强完成后进入 P1 运行链路和 schema 缺口：

- repair lane 的 Code 行为已回到 `01/07/09` specs 契约；
- `01/02/07/09` 的待补齐口径已同步修正为真实缺口清单；
- P1 运行链路和 schema 缺口必须先 spec-first，再 code-after-spec；
- 已实现的 self-lock 修复、no-op、receipt cache 和 sed-i 修复不再作为 P0 反复讨论，只保留测试覆盖和漂移治理。

只有这一步通过，后续 Code、tests、V2 收口和 WorkCase 承接才不会继续反复。
