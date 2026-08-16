---
title: LDVH 规范残留问题：宿主生命周期事件取消后的文本与实现残留
status: active
report_kind: internal_audit
research_question: LDVH 取消宿主生命周期事件要求后，规范文本、SKILL.md、CLI 实现和场景表中仍残留哪些与该政策变更不匹配的约束、参数和路径假设？
abstract: 对 LDVH 自身规范体系进行内部审计，发现政策取消宿主生命周期事件对象后，09 §5.4、SKILL.md、CLI work-context 入口、09 场景表和 09.Att.01 中仍有 5 处残留，导致 Kimi Work 环境下 AI 被引导经历无意义的'尝试首选→失败→降级'仪式。
research_intent: LDVH 已决定不再强制要求 AI 宿主环境原生提供生命周期事件对象。本审计旨在确认该政策变更后，规范源中仍残留的结构性不匹配，以便后续决定是修订规范文本、修复 CLI 实现，还是两者并行。
recommendation_summary: 建议方案 B（规范层修正）为主、方案 A（Code 层修复）为辅：09 §5.4 和 SKILL.md 应将精确规则读取设为默认路径；ldvh work-context 的 --helper-executable 参数应移除或改为可选；09 场景表应增加'入口直接不可调用'场景。
input_refs:
- kind: specification
  locator: specs/09-环境接入规范.md §5.4
  version: 当前 working tree
  observed_at: '2026-08-05T15:04:00+08:00'
- kind: specification
  locator: specs/00-理念与构成.md §8.1/§8.2
  version: 当前 working tree
  observed_at: '2026-08-05T15:04:00+08:00'
- kind: skill
  locator: skill/SKILL.md
  version: 当前 working tree
  observed_at: '2026-08-05T15:04:00+08:00'
- kind: attachment
  locator: specs/attachments/09.Att.01-环境接入面.md
  version: 当前 working tree
  observed_at: '2026-08-05T15:04:00+08:00'
- kind: cli_observation
  locator: ./ldvh work-context --help
  version: 当前 working tree
  observed_at: '2026-08-05T15:05:00+08:00'
action_relevance: 清理宿主生命周期事件取消后的文本残留时，确保实现说明与规范声明一致，不遗留无来源支撑的声称
change_log:
- signature:
    agent_id: kimi
    host_environment: Kimi
  session_id: wd_ld-vibe-harness-v4_24baa608d511
  at: '2026-08-05T15:41:03.043451+08:00'
  summary: Human 授权创建 Study，审计 LDVH 规范残留问题。
- at: '2026-08-10T08:55:59.308269Z'
  summary: '受控更正历史 change_log 中的 agent_workbench 格式；修复项为 0: Kimi Work -> Kimi。原始错误值已由本次更正覆盖并保留本条修复记录。'
  signature:
    agent_workbench: Cindy
    model_id: gpt-5
  session_id: cindy-explicit-signature-migration-20260810
- at: '2026-08-10T09:27:43.727753Z'
  summary: '受控更正历史 change_log 中的 agent_workbench 格式；修复项为 0: Kimi Work -> kimi。原始错误值已由本次更正覆盖并保留本条修复记录。'
  signature:
    agent_workbench: Cindy
    model_id: gpt-5
  session_id: session-20260810-kimi-model-id-migration
- signature:
    product_name: Cindy
    model_name: gpt-5
    agent_runtime_name: codex
  at: '2026-08-13T14:04:06.542467Z'
  summary: 为历史事实对象补齐权威 object_uid，并将同项目 legacy 关系目标改写为 object_uid。
- signature:
    product_name: Cindy
    model_name: gpt-5
    agent_runtime_name: codex
  at: '2026-08-13T15:03:57Z'
  summary: 将事实对象物理定位符迁移为完整 UUIDv7 的 Crockford Base32 编码。
- summary: 补 action_relevance 字段值（规范修订：24/05 新增必填字段定义与登记）
  signature:
    product_name: Cindy
    model_name: glm-5.2
    agent_runtime_name: claude-code
  at: 2026-08-16T21:30:34.415045Z
object_id: study-01KZXN5TXNFY99TKZKNZ3HZ3A5
object_uid: 019ffb52-ebb5-7f92-9d4f-f3afc71f8d45
fact_type_key: study
created_at: '2026-08-05T15:41:03.043451+08:00'
updated_at: '2026-08-16T21:42:45.620720Z'
---

## 研究问题

LDVH 已决定取消宿主生命周期事件对象的强制要求。本报告审计：该政策变更后，规范文本、SKILL.md、CLI 实现和场景表中仍残留哪些与该变更不匹配的结构性假设？这些残留对 Kimi Work 环境下的 AI 路由行为产生了什么实际影响？

## 输入与边界

本审计基于以下内部来源：

| 来源 | 用途 | 限制 |
|---|---|---|
| `specs/09-环境接入规范.md` | 规则引导路由定义 | 只审计 §5.4 及场景表，不审计完整环境接入流程 |
| `specs/00-理念与构成.md` | 根规范 §8.1/§8.2 | 只验证其内容是否被正确消费，不审计其自身正确性 |
| `skill/SKILL.md` | 薄 Skill 路由纪律 | 只审计规则引导路由章节 |
| `specs/attachments/09.Att.01-环境接入面.md` | 入口交付状态登记 | 只审计 `work-context-core` 行 |
| `./ldvh work-context` CLI 实际调用 | 验证入口可用性 | 仅在当前 working tree、当前 Python 环境下测试 |

未覆盖：其它宿主环境（如 Cindy、ZCode）的行为；LDVH Web 端的实际呈现；04 Helper 服务契约的完整字段表。

## 关键发现

### 发现 1：09 §5.4 的条件分支结构残留

**位置**：`specs/09-环境接入规范.md:138`

**问题**：规范仍把"宿主提供生命周期事件"设为首选路径的前提条件，把精确规则读取设为降级。对 Kimi Work 而言，该条件永久为假，导致无意义的条件判定。

**对项目的影响**：每次会话开始都需先判定一次注定失败的条件，再退回来走降级路径，增加审计噪音和路径混淆。

### 发现 2：SKILL.md 仍保留 `work-context-core` 条件引用

**位置**：`skill/SKILL.md:16-20`

**问题**：SKILL.md 仍把 `work-context-core` 作为条件分支中的首选入口引用，虽然已改为"宿主提供时才使用"，但对 Kimi Work 实质是永远不可用的代码路径。

**对项目的影响**：AI 被引导在每次会话开始时关注一个不可用的入口，分散对实际可用路径（精确规则读取）的注意力。

### 发现 3：`ldvh work-context` 的 `--helper-executable` 参数残留

**位置**：CLI 实现层

**问题**：`./ldvh work-context` 仍要求 `--helper-executable` 参数，但 `./ldvh capabilities` 和 `./ldvh call` 已经集成了 Helper dispatcher，不再需要该参数。这导致入口**直接不可调用**（exit=2），而非返回结构化 `unavailable`。

**对项目的影响**：场景表假设的"返回 unavailable"行为不成立；AI 无法通过 `work-context` 入口取得任何响应。

### 发现 4：09 场景表未覆盖"入口直接不可调用"情况

**位置**：`specs/09-环境接入规范.md:281`

**问题**：场景表只覆盖 `ldvh work-context` 返回 `unavailable` 的情况，未覆盖因参数缺失直接报错（exit=2）的情况。

**对项目的影响**：AI 遇到入口不可调用时无规范指导，只能自行判断如何处理。

### 发现 5：09.Att.01 的 `work-context-core` 登记为"已交付"但不可用

**位置**：`specs/attachments/09.Att.01-环境接入面.md:22`

**问题**：虽然 Code 存在，但对 Kimi Work 该入口不可调用。登记为"已交付"在技术上成立，但对目标环境的实际可用性声明有误导性。

## 建议

### 方案 A：Code 层修复（最小侵入）

- 让 `ldvh work-context` 自动解析已确认的 Helper，不再要求 `--helper-executable`
- 当宿主不提供生命周期事件时，`work-context` 内部自动降级为精确规则读取

### 方案 B：规范层修正（推荐）

- 09 §5.4：将"首选/降级"结构改为"按宿主能力直接路由"
- SKILL.md：用环境中性方式将精确规则读取设为默认路径
- 09 场景表：增加"入口直接不可调用"场景

### 方案 C：混合方案

- 先执行方案 A，使 `work-context` 可调用且自动降级
- 再评估是否仍需方案 B 的规范澄清

**建议采纳**：方案 C，以方案 B 的规范修正为最终目标。

## 后续分流

| 建议 | 承载方向 | 判断标准 |
|---|---|---|
| 修订 09 §5.4 路由结构 | ADR 或规范修订 WorkCase | Human 授权后由项目承担 |
| 修订 SKILL.md 默认路径 | ADR 或规范修订 WorkCase | 需确认跨环境兼容性 |
| 移除/软化 `--helper-executable` | Code 修复 WorkCase | 需确认不影响其它宿主环境 |
| 增加场景表覆盖 | 规范修订 WorkCase | 可与 09 §5.4 修订合并 |
| 09.Att.01 可用性限定 | 规范附件修订 | 可与主规范修订同步 |

若上述任一建议被采纳，本 Study 可保持 `active` 作为历史审计入口；若全部否决或长期无行动，可在 6 个月后评估是否 `retired`。
