# LDVH 环境投射技术经验吸收研究

> 创建日期：2026-06-11
> 定位：吸收 ECC、Trae Work CN、Codex App、Claude Code CLI 中与 LDVH 环境投射相关的技术经验，重点讨论环境薄入口、人机沟通、Rules / Skills / Hooks / Agents / Commands 的承接方式
> 性质：内部研究文档，不直接构成正式规范、ADR、Task 或运行投影
> 当前结论：环境投射应定义为 LDVH 的主动行为。正式规范先提出落地要求，LDVH 建设或选择能力保障这些要求，再基于目标环境的客观能力清单主动形成运行投影、降级路径和缺口记录；环境不拥有 LDVH 能力，也不反向决定 LDVH 是否建设更优能力。

---

## 1. 本文解决的问题

本文用于补齐 LDVH 环境投射研究中的一个缺口：此前讨论较多集中在 04.06 三环境承接矩阵、Skill + Hook 跨环境不等价、Code baseline 和 42 bootstrap，但对人机沟通机制、Rules、Skills、Hooks、Agents、Commands 等环境投射承接面的整体吸收还不够系统。

本文回答以下问题：

1. LDVH 从 ECC 和三类 AI 开发环境中，应吸收哪些环境投射经验；
2. 哪些能力属于 LDVH 共享内核，哪些只能成为环境薄入口；
3. 人机沟通机制在环境投射中应如何表达；
4. Rules / Instructions、Skills、Hooks、Agents、Commands 如何承接 LDVH 要求；
5. Trae Work CN、Codex App、Claude Code CLI 的能力差异如何映射到 04.06；
6. 后续 04.02、04.03、04.06、42 和 Code 校验应吸收哪些结论。

本文不处理：

1. 直接修改 04.06 正文；
2. 创建运行投影文件；
3. 删除或迁移 04.07 / 04.08；
4. 创建环境规则、Skill、Hook、Agent 或 Command；
5. 宣称任一环境完整承接。

---

## 2. 核心结论

环境投射应被理解为 LDVH 的主动行为，而不是环境对 LDVH 的被动承接。

```text
正式规范提出落地要求
  ↓
LDVH 建设或选择能力保障
  ↓
读取目标环境客观能力清单
  ↓
LDVH 主动形成该环境中的运行投影、降级路径和缺口记录
```

三层分工如下：

| 层 | 作用 | 权威位置 |
|---|---|---|
| 规范落地要求层 | 正式规范声明自身规则要落地需要被看见、复用、校验、触发、确认或被后续规范承接 | `docs/specs/`、`docs/specs/04.01` |
| LDVH 能力保障层 | LDVH 根据规范要求建设或选择工作流程、Code、Web、Human Gate、Rules、Skills、Commands、Hooks、Agents 等能力组合 | `docs/specs/04.03`、`tools/`、`web/`、`ldvh-base/`、能力资产 |
| 环境投射层 | LDVH 基于目标环境的客观能力清单，将能力主动形成环境入口、命令、Skill、Hook、Agent、Web、Code 校验、Human Gate 表达、降级路径或缺口记录 | `docs/specs/04.02`、`docs/specs/04.06`、运行投影 |

环境侧只提供客观能力清单，例如 Rules、Instructions、Skill、Command、Hook、Agent、MCP、Web Preview、approval、sandbox、permissions、context / compact 等是否存在、边界如何、证据是否充分。环境能力清单不是 LDVH 的落地决策，也不拥有 LDVH 能力资产。

最重要的边界是：

```text
环境投射不是事实源。
运行投影不是事实源。
环境能力清单不是 LDVH 的落地决策。
环境薄入口不能复制正式规范正文。
环境能力不足不能降低 LDVH 要求，也不能阻止 LDVH 建设更优保障能力。
环境工具输出只能作为证据或派生视图，稳定结论仍需回写 Git 文件事实源。
```

---

## 3. ECC 可吸收经验

ECC 对 LDVH 的价值不是其完整安装器、资产库或自动 repair 系统，而是它已经实践过多环境能力投射的工程组织方法。

### 3.1 可吸收方法

| ECC 经验 | LDVH 可吸收方式 | 环境投射意义 |
|---|---|---|
| manifest 三层模型 | 转译为能力声明、投射对象、验证命令和事实源边界字段 | 让 AI 知道某个能力由哪些文件、入口和检查组成 |
| target / adapter | 转译为三环境承接矩阵列和环境薄入口 | 不同环境能力不同，但映射回同一 LDVH 要求 |
| compliance matrix | 转译为承接类型、承接检查、承接降级和待补齐事项 | 防止口头支持和虚假承接 |
| command contract | 转译为 LDVH 命令或 Code 输出合同 | 固定输入、输出、STOP 点、验证和写入边界 |
| status / audit / doctor | 转译为 42、Code baseline 和只读诊断报告 | 只诊断和分流，不自动修复 |
| rules / skills 分工 | 转译为 specs / rules / skills / tools 分工 | specs 是权威 what，skills/tools 是 how，入口只是 thin projection |

### 3.2 不应吸收内容

LDVH 不应照搬：

1. ECC 完整安装器；
2. profile 选择器；
3. install state；
4. session control plane；
5. 多环境自动分发系统；
6. 第三方 commands / skills / rules 原文资产库；
7. auto repair 自动写入链路；
8. ECC 对某平台的支持结论。

这些内容即使在 ECC 中成立，也不能直接成为 LDVH 的环境承接事实。

---

## 4. 人机沟通机制

人机沟通是环境投射的核心内容之一。环境薄入口不仅要让 AI 看见规范，还要让 AI 知道何时问 Human、问什么、如何暂停、如何记录授权、如何把结果回写到事实源。

### 4.1 人机沟通在环境投射中的位置

人机沟通不应被理解为单纯 UI 能力，而是环境承接的一组机制：

| 沟通面 | 作用 | 环境投射表达 |
|---|---|---|
| 入口提示 | 告诉 AI 当前应先读什么、禁止做什么 | Rules / Instructions / AGENTS / CLAUDE.md / LDVH-AI-ENTRY |
| 澄清问题 | 在需求不明时收集 Human 决策 | AskUserQuestion、对话、Plan/Spec Gate |
| Human Gate | 高影响写入、状态流转、权限、长期降级前暂停 | Gate 字段、审批 UI、对话确认、Task 记录 |
| STOP 点 | 防止 AI 继续越权执行 | 入口规则、Skill checklist、Command 输出、42 报告 |
| 证据回写 | 把稳定结论回到事实源 | Task / ADR / Memo / Change / Pitfall / specs |
| 最终确认 | 告诉 Human 已做什么、剩余风险是什么 | 42 报告、Task closure evidence、Web 派生视图 |

### 4.2 环境差异

不同环境的人机沟通承接形态不同：

| 环境 | 主要沟通承接 | 风险 |
|---|---|---|
| Trae Work CN | Rules、Skills、Commands、结构化问询、Plan/Spec Gate、预览和 IDE 交互 | 无等价 lifecycle Hook，容易把 checklist 误认为自动触发 |
| Codex App | AGENTS、approval、sandbox、exec 输出、review、CLI / App 交互 | approval / sandbox 不能替代 LDVH Human Gate 事实记录 |
| Claude Code CLI | CLAUDE.md、commands、permissions、hooks、subagents、context / compact、CLI 参数 | refs 和实测不足时不能宣称完整承接 |

### 4.3 投射规则

人机沟通机制进入环境投射时应遵守：

1. Human Gate 必须说明确认事项、确认范围、风险、影响范围和执行前暂停点；
2. 平台 UI 审批不能自动等价为 LDVH Human Gate；
3. 问题澄清应优先使用当前环境最自然的人机入口，但稳定结论必须回写事实源；
4. STOP 点应出现在入口投影、Skill checklist、Command contract 和 42 报告中；
5. 长期授权、长期降级、持久运行投影、自动触发和事实源写入必须显式触发 Human Gate。

---

## 5. Rules / Instructions

Rules / Instructions 适合承接入口可见、硬约束摘要、事实源边界提示、最小读取顺序、场景路由和 STOP 点。

### 5.1 可吸收经验

ECC rules 的经验是：

1. common + specific 分层；
2. specific overrides general；
3. 不 flatten 复制目录；
4. 命名空间隔离；
5. rules tell what, skills tell how。

LDVH 应改写为：

```text
specs = 权威 what
rules / instructions = 环境薄入口中的约束摘要
skills / tools = how
project facts = 当前项目事实
```

### 5.2 不应承接内容

Rules / Instructions 不应承载：

1. 完整正式规范正文；
2. 工作模型字段契约全文；
3. 复杂多步骤 SOP；
4. 临时决策结论；
5. 运行状态；
6. 缺口关闭事实。

### 5.3 04.06 表达方式

在 04.06 中，Rules / Instructions 卡片应记录：

| 字段 | 建议内容 |
|---|---|
| LDVH 要求 | 入口可见、事实源边界、最小读取顺序、STOP 点 |
| 承接检查 | 是否复制正文、是否指向权威路径、是否包含 Gate / STOP 提示 |
| 承接降级 | 无规则时由当前对话显式读取 `LDVH-AI-ENTRY.md` 和必要 specs |
| 待补齐事项 | 环境规则路径、加载证据、规则冲突处理、实测结果 |

---

## 6. Skills / Commands

Skill 和 Command 都可以承接“如何做”，但不能替代工作流程、Task、Human Gate 或事实源。

### 6.1 Skill

Skill 适合：

1. 可复用 SOP；
2. 标准化操作步骤；
3. 检查清单；
4. 输出格式；
5. 特定任务的 AI 执行指导。

Skill 不适合：

1. 独立事实源；
2. 自动触发机制；
3. 子 Agent 生命周期管理；
4. Human Gate 判断本身；
5. 稳定规则正文。

如果一个流程需要子 Agent，Skill 应只返回主控 AI 应调用哪些 Agent、提供哪些输入、如何收口和如何检查；Skill 本身不应被理解为能直接调度 Agent 的执行器。

### 6.2 Command

Command 适合：

1. 固定触发入口；
2. 显式校验命令；
3. 重复流程封装；
4. 输出合同稳定的只读报告；
5. 在无 Hook 环境中替代部分自动化意图。

Command contract 至少应包含：

| 字段 | 作用 |
|---|---|
| trigger | 如何触发 |
| facts_read | 读取哪些事实源 |
| allowed_tools | 允许哪些工具 |
| forbidden_actions | 禁止哪些动作 |
| output_schema | 输出字段 |
| stop_points | 何时停下等 Human |
| validation | 如何验证 |
| write_policy | 是否允许写入 |

### 6.3 04.06 表达方式

Skill / Command 卡片应区分：

1. 是否只是指令承接；
2. 是否有真实命令或 Code wrapper；
3. 是否有验证证据；
4. 是否会被误认为自动触发；
5. 是否需要 Task 承载正式安排。

---

## 7. Hooks / Lifecycle

Hook 是环境差异最大、也最容易误判的投射面。

### 7.1 Hook 能承接什么

Hook 适合承接：

1. 工具调用前检查；
2. 工具调用后审查；
3. 权限请求前决策辅助；
4. 会话启动补充上下文；
5. 停止前验收；
6. 上下文压缩前后处理；
7. 子 Agent 启动和停止的包裹治理。

Hook 不适合承接：

1. 正式规范正文；
2. 复杂语义判断；
3. 无授权写入；
4. 自动关闭 Task / ADR / 规范缺口；
5. 绕过 Human Gate 的自动修复。

### 7.2 无 Hook 环境的降级

当一个环境没有 Hook，但另一个环境有 Skill + Hook 组合时，不得声明等价投射，也不得因为弱环境缺少 Hook 而取消 LDVH 的 Hook / lifecycle 能力建设。

正确拆分方式是：

| 原组合意图 | 无 Hook 环境承接 |
|---|---|
| Skill 定义流程 | Skill 或规则承接 SOP |
| Hook 自动触发 | Rule / Instruction 明示触发条件 |
| 工具前阻断 | Human Gate + 命令白名单 / 黑名单 + 显式检查 |
| 工具后审查 | Command / Code / 测试命令显式运行 |
| 停止前验收 | 最终响应前 checklist |
| 失败后继续 | Task / Todo / Human 决策继续 |

在 04.06 中，这种情况应标为“指令投射”或“人工降级”；只有存在明确 thin entry、Command / Code wrapper 和验证证据时，最多标为“适配投射”。强环境中的 Hook 路径应保留为优先投射方式，弱环境只在自身投射路径中降级并记录残留风险。

---

## 8. Agents / Subagents

Agent / Subagent 适合独立上下文、专项审查、多视角研究和并行分析，但 Agent 不是稳定事实源，也不能绕过主控或 Human Gate。

### 8.1 承接规则

Agent 投射应满足：

1. 主控 AI 负责决定是否调用；
2. Agent 输入必须明确范围、事实源、禁止事项和输出要求；
3. Agent 输出必须回到主控或 Human；
4. Agent 不应直接关闭事实源缺口；
5. 稳定结论需要 Task、ADR、Memo、Change、Pitfall 或 specs 回写后才生效；
6. 环境不支持 Agent 时，应降级为主控 AI 按多视角清单手动执行。

### 8.2 04.06 表达方式

Agent / Subagent 卡片应记录：

| 字段 | 建议内容 |
|---|---|
| LDVH 要求 | 独立上下文、专项视角、输出回主控、不得绕过 Gate |
| 承接检查 | 是否能声明 Agent 类型、输入、输出、收口和事实源回写位置 |
| 承接降级 | 无 Agent 时由主控按多角色模板执行 |
| 待补齐事项 | 环境 Agent refs、实测证据、权限边界、并行能力 |

---

## 9. MCP / External Tools

MCP 和外部工具属于环境能力或连接器承接面，不是 LDVH 事实源。

投射规则如下：

1. MCP 输出必须回指 Git 文件事实源或外部来源；
2. MCP 不得直接成为稳定事实；
3. 连接器缺失时应记录为环境承接缺口或人工降级；
4. 自动运行 MCP 必须受权限、Human Gate 和写入边界约束；
5. 04.06 应记录 MCP 是否存在、承接类型、来源、检查方式、降级方式和待补齐事项。

---

## 10. Context / Memory / Session

上下文、记忆和会话恢复也是环境投射的一部分，但必须避免成为隐藏事实源。

可吸收经验包括：

1. Claude Code 的上下文健康阈值和 `/compact` 思路；
2. Codex / Claude 的会话恢复、压缩、AGENTS / CLAUDE.md 加载机制；
3. ECC 的 session adapter 思想；
4. 用阶段性总结降低上下文漂移。

LDVH 的边界是：

1. 会话记忆不是事实源；
2. 压缩摘要不是事实源；
3. 长期稳定事实必须回写 Git 文件；
4. 上下文不足时应读取权威原文，而不是依赖记忆；
5. 环境薄入口可提示何时 compact、何时重读、何时回写。

---

## 11. Web / Preview / Human-facing

Web 和 Preview 不属于环境能力本身，但会影响人机沟通和 Human Gate 的承接质量。

因此 04.06 中不应把 Web 运行态作为环境能力项，但可以记录：

1. 当前环境是否容易打开 Web 预览；
2. Human 是否能看到派生视图；
3. Human Gate 是否能通过 UI 表达；
4. Web 输出是否清楚标注派生视图和事实源回指；
5. 无 Web 预览时如何人工降级。

这类内容应作为 Human-facing 承接限制或降级说明，而不是环境能力完整支持声明。

---

## 12. 环境投射卡片建议

后续 04.03 中，每个三环境投射项建议使用统一卡片结构：

| 字段 | 含义 |
|---|---|
| 投射项 | 例如 Rules / Instructions、Skill / Command、Hook / Lifecycle、Agent / Subagent、Human Gate |
| LDVH 要求 | 该能力要满足的 LDVH 抽象要求 |
| 环境能力清单 | Trae Work CN、Codex App、Claude Code CLI 的客观能力、边界和证据状态 |
| Trae Work CN 投射方式 | LDVH 在 Trae 中主动形成的入口、流程、校验、降级或缺口记录 |
| Codex App 投射方式 | LDVH 在 Codex 中主动形成的入口、流程、校验、降级或缺口记录 |
| Claude Code CLI 投射方式 | LDVH 在 Claude Code 中主动形成的入口、流程、校验、降级或缺口记录 |
| 来源 | refs、specs、research 或实测证据 |
| 投射检查 | 如何证明投射未越界、未虚假支持、未把环境能力当成 LDVH 决策 |
| 投射降级 | 能力不足时如何人工降级或显式执行 |
| 待补齐事项 | refs、实测、Code 校验、Task、ADR 或 LDVH 能力建设需求 |

---

## 13. 04 系列重写命名草案与成熟度判断

### 13.1 推荐命名

按“规范提出落地要求、LDVH 建设或选择能力保障、LDVH 基于环境能力清单主动投射”的主轴，04 系列可收敛为：

```text
04-规范落地与环境投射基础规范.md
04.01-规范落地要求与类型规范.md
04.02-LDVH能力保障规范.md
04.03-三环境能力清单与投射规范.md
04.04-LDVH特别落地要求规范.md
04.05-个人环境特别要求规范.md
```

其中：

| 文件 | 职责 |
|---|---|
| 04 | 定义 04 系列总模型、边界和子文档分工 |
| 04.01 | 定义正式规范可提出哪些落地要求，以及要求类型如何声明 |
| 04.02 | 定义 LDVH 用哪些能力保障规范要求，能力不足时如何形成能力建设需求 |
| 04.03 | 定义三环境客观能力清单，以及 LDVH 如何基于清单分别形成投射方式、检查、降级和缺口 |
| 04.04 | 定义 LDVH 项目自身的特别落地纪律 |
| 04.05 | 定义个人或维护者环境的特殊路径、命令、偏好和限制 |

### 13.2 成熟度判断

当前主轴已经成熟，但不建议立即把 04 系列正式规范一次性完整重写到最终态。

已成熟的内容：

1. 04 系列三层主轴已经清楚：规范提需求、LDVH 建能力、LDVH 基于环境能力清单主动投射；
2. “环境只提供客观能力清单，不能反向决定 LDVH 是否建设能力”已经清楚；
3. “环境能力不足时，弱环境降级，强环境保留高质量投射路径”已经清楚；
4. ECC 对 LDVH 的价值是机制结构而不是原文接管已经清楚；
5. rules / skills / commands / hooks / agents / Human Gate / Code / Web 的大体分工已经清楚。

尚未完全成熟的内容：

1. 三环境能力清单仍需按 refs 和实测证据重新整理，不能只凭研究结论写成正式支持声明；
2. ECC manifest、plan / apply / verify、audit / status / doctor 等机制是否进入 04.02、04.03、42 或 Code，还需要拆分吸收；
3. Hook / lifecycle 在 Codex App、Claude Code CLI、Trae Work CN 中的边界需要按 refs 明确，不应混写为通用能力；
4. 人机沟通机制已经识别，但还需要明确哪些进入 04.02、哪些进入 04.03、哪些只进入 42 或工作对象证据；
5. Code 校验项仍未形成稳定字段契约，不能先写死为强校验；
6. 04.07 / 04.08 的迁移、历史化或删除需要与 04.03 新矩阵和 42 消费口径同步处理。

因此，当前更适合先做“04 系列重写设计稿 / 差异方案”，再进入正式规范改写。正式改写应按文件逐个推进，而不是一次性大面积替换。

### 13.3 建议推进顺序

1. 先以本文为依据整理 04 系列重写设计稿；
2. 再改 04 父文档，确立“规范落地与环境投射基础规范”的总模型；
3. 再改 04.01，收敛规范落地要求与类型；
4. 再改 04.02，整理 LDVH 能力保障和能力建设需求；
5. 再改 04.03，整理三环境能力清单与投射矩阵；
6. 最后处理 04.04、04.05、04.07、04.08、42 和 Code 校验。

---

## 14. 后续吸收建议

### 14.1 应吸收到正式规范的内容

| 内容 | 建议吸收位置 |
|---|---|
| 环境投射三层模型 | 04 父规范、04.01、04.03、04.02、04.06 |
| 环境能力清单不是落地决策 | 04.02、04.06 |
| 环境能力不足时优先判断 LDVH 能力建设 | 04.03、04.06 |
| 人机沟通机制作为环境投射面 | 04.02、04.03、04.06、42 |
| Rules / Instructions 承接边界 | 04.03、04.06 |
| Skill / Command 承接边界 | 04.03、04.06、11.01 |
| Hook 无等价时的降级规则 | 04.03、04.06 |
| Agent 输出必须回主控 | 04.03、44、04.06 |
| MCP 输出不是事实源 | 04.03、04.06、09 |
| Context / Memory / Session 非事实源边界 | 04.02、09、12 |
| Web / Preview 作为 Human-facing 降级说明 | 04.06、08、42 |

### 14.2 应进入 Code 校验的内容

后续 Code 可检查：

1. 04.06 是否存在环境投射卡片必填字段；
2. 承接类型是否使用合法枚举；
3. Hook / lifecycle 承接项是否包含不可模拟能力和降级说明；
4. Skill-only 是否被误标为 Skill + Hook 等价；
5. Human Gate 是否包含确认范围、风险和暂停点；
6. 环境薄入口是否复制正式规范正文；
7. MCP / Web / tool 输出是否被误写成事实源；
8. 04.07 / 04.08 是否被 42 继续当作长期独立清单。

### 14.3 暂不应做的内容

1. 不创建完整 LDVH manifest / installer；
2. 不创建自动 repair；
3. 不创建环境级长期状态源；
4. 不把 ECC agents / skills / commands / rules 原文导入 LDVH；
5. 不宣称 Trae Skill-only 等价承接 Hook；
6. 不在 refs 和实测不足时宣称 Claude Code CLI 完整承接；
7. 不让 plan 类输出替代 Task。

---

## 15. 当前最小结论

```text
LDVH 环境投射的重点不是复制环境能力，也不是等待环境被动承接，而是由 LDVH 基于规范落地要求和自身能力体系，读取目标环境的客观能力清单，主动形成不同环境中的入口、触发方式、人机沟通、显式校验、降级路径和缺口记录。

Rules / Instructions 负责入口和约束摘要；Skills / Commands 负责流程复用和显式执行；Hooks 负责生命周期触发但不可假装存在；Agents 负责独立视角但必须回主控；Human Gate 负责授权、暂停和风险确认；Code 负责确定性校验；Web 负责 Human-facing 派生视图。

所有环境投射都必须回到 04.06 的三环境能力清单与投射矩阵表达目标环境客观能力、投射方式、来源、投射检查、投射降级和待补齐事项。

运行投影、环境薄入口、平台工具输出和人机沟通界面都不是事实源；稳定结论必须回写 Git 文件事实源。
```
