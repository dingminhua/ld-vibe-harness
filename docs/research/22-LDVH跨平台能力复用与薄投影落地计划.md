# LDVH 跨环境承接复用与环境薄入口落地计划

> 创建日期：2026-06-11
> 定位：收敛 LDVH 在 Trae Work CN、Codex App、Claude Code CLI 三个 AI 开发环境上的跨环境承接复用、环境薄入口、承接矩阵、承接检查、跨环境融合落地方式和后续融合计划
> 性质：内部调研与推进计划文档，不直接构成正式规范或实施承诺
> 执行效力：无；稳定结论需进入正式 specs、ADR、Task、Code、Web、测试、运行投影或最佳实践后才具备对应效力
> 来源：`docs/refs/09-ECC跨环境同功能复用机制任务参考.md`、`docs/research/21-LDVH下一阶段推进方向-受控落地执行闭环.md`、2026-06-11 关于 Trae Work CN / Codex App / Claude Code CLI 三环境复用范围的讨论
> 上位依据：`docs/specs/00-LD-Vibe-Harness理念与纲要.md`
> 相关规范：`docs/specs/04.02-LDVH能力保障规范.md`、`docs/specs/04.03-环境能力清单与环境适配规范.md`、`docs/specs/04.03-环境能力清单与环境适配规范.md`、`docs/specs/04.03-环境能力清单与环境适配规范.md`、`docs/specs/04.03-环境能力清单与环境适配规范.md`、`docs/specs/06-工作流程基础规范.md`、`docs/specs/07-Code实现规范.md`、`docs/specs/09-事实源边界与承载规范.md`、`docs/specs/10-运行闭环测试规范.md`、`docs/specs/41-landing-orchestration-规范落地统筹.md`、`docs/specs/42-ldvh-landing-check-LDVH落地与检查.md`

---

## 1. 本文解决的问题

本文用于把 LDVH 的跨环境承接复用、环境薄入口和跨环境融合落地事项从 21 号下一阶段推进文档中抽离出来，形成独立计划。

本文集中回答：

1. LDVH 如何吸收 ECC 的跨环境组织方法；
2. LDVH 如何先用 Trae Work CN、Codex App、Claude Code CLI 三个 AI 开发环境验证跨环境承接复用；
3. 哪些内容必须留在 LDVH 共享内核，哪些内容只能作为环境薄入口或三环境承接矩阵；
4. 环境承接如何声明、检查和防止虚假承接；
5. 三环境跨环境承接复用最终如何融合落地；
6. 后续如何把计划融合回 04.06 三环境承接矩阵、42、landing-plan、CLI 和 Web，并吸收既有 04.07 / 04.08 内容。

本文不替代 21 的受控落地执行闭环。21 继续聚焦 `plan → test design → approve → apply/repair → verify → review_needed → review → writeback → recheck`；本文负责该闭环在不同 AI 开发环境上的入口、承接、承接降级、承接检查、跨环境融合落地方式和融合路径。

---

## 2. 范围收敛

### 2.1 本轮覆盖环境

本轮只覆盖三个 AI 开发环境。本文中的“环境”指 AI 工具及其上下文入口、权限、指令、命令、Hook、MCP、Agent、Human 确认方式等承载条件的组合。

| 环境 | 本轮定位 | 当前材料 |
|---|---|---|
| Trae Work CN | 当前主执行环境和优先试点环境 | 既有 `docs/specs/04.03-环境能力清单与环境适配规范.md`，后续吸收到 04.06 三环境承接矩阵 |
| Codex App | App / AGENTS / approval 对照环境 | 既有 `docs/specs/04.03-环境能力清单与环境适配规范.md`，后续吸收到 04.06 三环境承接矩阵 |
| Claude Code CLI | 第三个跨环境验证环境 | 后续吸收现有 refs 后直接进入 04.06 三环境承接矩阵，不再新增独立 04.09 清单 |

选择这三个平台的原因是：

1. Trae Work CN 能验证 Rules、Skill、Agent、结构化问询、预览和 IDE 型交互；
2. Codex App 能验证 AGENTS、approval、exec、MCP 和 App 型交互；
3. Claude Code CLI 能验证另一套主流 CLI AI 编码工具的 rules / commands / hooks / MCP / agentic workflow 承接形态；
4. 三者组合足以暴露入口加载、上下文压缩、工具权限、Human Gate、环境指令、MCP、Hook、Agent 和降级路径的主要差异。

### 2.2 本轮不覆盖环境

本轮不处理 Cursor、OpenCode、Gemini、Zed、Qwen、Terminal-only、云端托管、网页端或移动端。

这些环境可以作为未来扩展参考，但不得在本轮计划中声明支持，也不得因为 ECC 支持更多环境而扩大 LDVH 当前范围。

---

## 3. 对 ECC 的吸收边界

### 3.1 应吸收的方法

LDVH 应吸收 ECC 的以下组织方法：

1. **LDVH 共享内核 + 环境薄入口**：正式规范、工作模型、工作流程、Code 合同和事实源边界保留在 LDVH 主事实源；环境薄入口只负责引导、加载、触发或承接降级；
2. **承接显式声明**：每个环境必须说明某项 LDVH 承接项如何承接、承接类型、证据、承接检查、限制和承接降级；
3. **环境 adapter 思想**：不同环境可以有不同路径、入口、命令、事件形状和权限模型，但都应映射回同一组 LDVH 要求；
4. **compliance matrix 思想**：用矩阵公开承接类型、unsupported surfaces、承接检查、风险说明和来源，避免口头支持；
5. **承接检查绑定承接声明**：没有承接检查或等价检查方式的环境承接声明，只能是待确认、承接降级或参考。

### 3.2 不应照搬的内容

LDVH 不照搬 ECC 的以下内容：

1. 完整安装器；
2. profile 选择器；
3. install state；
4. 独立 executor；
5. session control plane；
6. 多环境自动分发系统；
7. 第三方 skills / commands / rules 原文资产库；
8. 无授权自动 repair 链路。

LDVH 学 ECC 的组织方法，不复制 ECC 的产品规模、资产库、状态系统或运行控制面。

---

## 4. LDVH 跨环境承接复用模型

### 4.1 三层结构

LDVH 跨环境承接复用应收敛为三层：

```text
LDVH 共享内核层：specs / work models / workflows / Code contracts / Web contracts / facts
  ↓
承接矩阵层：environment adoption matrix / adoption type / evidence / adoption check / adoption degradation
  ↓
环境薄入口层：Trae Work CN / Codex App / Claude Code CLI 的入口、指令、命令、Hook、MCP、Agent 或人工降级
```

这三层分别回答：

| 层级 | 回答的问题 | 权威位置 |
|---|---|---|
| LDVH 共享内核层 | LDVH 承接项是什么、规则是什么、事实源在哪里、闭环如何运行 | `docs/specs/`、`tools/`、`web/`、`ldvh-base/` |
| 承接矩阵层 | 哪个环境如何承接、承接类型是什么、如何承接检查、如何承接降级 | `docs/specs/04.06` 中的三环境承接矩阵 |
| 环境薄入口层 | 入口在哪里、如何加载、如何触发、如何把 Human 和工具接入 | 用户级规则、AGENTS、commands、hooks、MCP、CLI、人工入口 |

### 4.2 共享内核不得分叉

以下内容必须保持统一，不得按环境复制分叉：

1. LDVH 正式规范正文；
2. 工作模型字段契约和状态机；
3. 工作流程准入、Scenario、Human Gate 和事实源回写规则；
4. Code 命令合同、输出合同和校验规则；
5. Web 的 Human-facing 展示与受控交互边界；
6. Git 文件事实源边界；
7. ADR、Task、Memo、Pitfall 等工作对象事实源。

### 4.3 环境薄入口只能做薄承接

环境薄入口可以做：

1. 指向 `LDVH-AI-ENTRY.md`；
2. 引导 AI 读取 04.06 三环境承接矩阵和 42；
3. 暴露平台可用的 Rules / Instructions / Skill / Agent / Command / Hook / MCP / approval 能力；
4. 说明环境限制和承接降级；
5. 触发 Code 校验或运行入口；
6. 把 Human Gate 暂停点呈现给 Human。

环境薄入口不得做：

1. 复制正式规范正文；
2. 改写 LDVH 规则；
3. 保存安装状态、初始化状态或长期运行状态；
4. 把环境工具输出升格为事实源；
5. 绕过 Human Gate；
6. 自动关闭 Task、ADR 或规范缺口；
7. 因环境缺能力而降低 LDVH 正式要求。

---

## 5. 承接类型

以下承接类型借鉴 ECC 的支持分级思想，但不是照搬 ECC 原始命名。LDVH 后续应在 04.06 中吸收中文承接类型，并在必要时保留英文别名用于和外部参考对照：

| 承接类型 | 英文对照 | 含义 |
|---|---|---|
| 原生承接 | Native | 环境原生提供该能力，且有 LDVH 可复用的验证证据 |
| 适配承接 | Adapter-backed | 环境通过薄入口、配置、命令、脚本、MCP、Hook 或 Code wrapper 承接该能力，但语义不完全等价 |
| 指令承接 | Instruction-backed | 环境只能通过规则、指令、AGENTS、Prompt 或人工步骤引导 AI 执行，缺少强制运行时机制 |
| 人工降级 | Manual-degraded | 环境缺少对应能力，当前只能人工执行、人工确认或人工记录证据 |
| 仅作参考 | Reference-only | 只作为设计参考或未来候选，不声明当前支持 |
| 待确认 | Unknown | 尚未读取 refs 或完成实测，不能据此执行完整闭环 |

---

## 6. 三环境承接矩阵

本文建议后续将 Trae Work CN、Codex App、Claude Code CLI 的环境承接信息收敛到 04.06 中的一张三环境承接矩阵。04.07 和 04.08 中已有价值内容应被吸收到该矩阵；Claude Code CLI 不再新增独立 04.09 清单，而是作为矩阵中的第三个环境列补齐。

为避免超宽表格不可读，三环境承接矩阵在文档中采用“承接卡片”表达；后续 Code 或 Web 可以再派生为 JSON / 表格视图。每张承接卡片包含同一组字段：承接项、三环境承接、LDVH 要求、承接检查与承接降级。

### 6.1 入口可见

| 字段 | 内容 |
|---|---|
| 承接项 | Entry visibility |
| Trae Work CN | 用户级 Rules / AGENTS / 会话入口候选 |
| Codex App | `~/.codex/AGENTS.md` / 会话入口候选 |
| Claude Code CLI | 待调研 Claude Code instructions / CLAUDE.md / commands 入口 |
| LDVH 要求 | 只允许薄入口，不复制规范正文 |
| 承接检查与承接降级 | 检查入口是否指向 `LDVH-AI-ENTRY.md`；缺失时人工降级为会话显式读取 |

### 6.2 规则与指令

| 字段 | 内容 |
|---|---|
| 承接项 | Rules / Instructions |
| Trae Work CN | 适配承接 / 指令承接 |
| Codex App | 适配承接 / 指令承接 |
| Claude Code CLI | 待确认 |
| LDVH 要求 | 规则和指令只做入口、边界和约束摘要 |
| 承接检查与承接降级 | 检查是否复制正式规范正文；待确认项不得声明完整承接 |

### 6.3 Skill 与 Command

| 字段 | 内容 |
|---|---|
| 承接项 | Skill / Command |
| Trae Work CN | Trae Skill / Command 候选 |
| Codex App | Codex skills / exec / profile 候选 |
| Claude Code CLI | Claude Code slash commands / skills 候选 |
| LDVH 要求 | 只保留薄入口和触发说明 |
| 承接检查与承接降级 | 检查 Skill / Command 是否越界成为事实源 |

### 6.4 Agent 与子 Agent

| 字段 | 内容 |
|---|---|
| 承接项 | Agent / sub-agent |
| Trae Work CN | Trae Agent 候选 |
| Codex App | Codex subagents 候选 |
| Claude Code CLI | Claude Code subagent / agentic flow 待调研 |
| LDVH 要求 | 统一映射到 44 多角色思考 |
| 承接检查与承接降级 | Agent 输出只作为主控输入，不能绕过 Human Gate |

### 6.5 MCP

| 字段 | 内容 |
|---|---|
| 承接项 | MCP |
| Trae Work CN | Trae MCP 候选 |
| Codex App | Codex MCP 候选 |
| Claude Code CLI | Claude Code MCP 待调研 |
| LDVH 要求 | MCP 输出不得成为事实源 |
| 承接检查与承接降级 | 检查 MCP 输出是否回指 Git 文件事实源或外部来源 |

### 6.6 Human Gate

| 字段 | 内容 |
|---|---|
| 承接项 | Human Gate |
| Trae Work CN | AskUserQuestion / Plan / 对话确认 |
| Codex App | approval / 对话确认 |
| Claude Code CLI | permission prompts / 对话确认待调研 |
| LDVH 要求 | 高影响写入前必须暂停确认 |
| 承接检查与承接降级 | 检查确认证据；缺结构化能力时人工降级为对话确认 |

### 6.7 Hook 与生命周期触发

| 字段 | 内容 |
|---|---|
| 承接项 | Hook / lifecycle |
| Trae Work CN | 不默认自动启用，人工触发优先 |
| Codex App | hooks 候选，不默认自动启用 |
| Claude Code CLI | hooks 候选待调研 |
| LDVH 要求 | 默认不启用静默自动写入 |
| 承接检查与承接降级 | 检查 Hook 是否自动写入；默认人工触发或关闭 |

---

## 7. 跨环境融合落地路线

本文负责跨环境承接复用事项的跨环境融合落地设计。所谓“跨环境融合落地”，不是在本文中直接创建所有环境入口或完成全部 Code / Web 实现，而是由本文定义融合落地顺序、融合落地目标、事实源去向、承接检查、Human Gate、后续 Task / ADR / specs 融合路径，以及 21 与 04 / 42 / landing-plan / CLI / Web 之间的职责边界。

跨环境承接复用事项不得再回流到 21 展开。21 只消费本文沉淀出的环境承接边界和承接降级要求；三环境承接矩阵、环境薄入口、04.06 字段升级、42 检查规则、landing-plan 输出字段和 Web 展示入口，均由本文后续路线负责收敛。

### 7.1 P0：形成三环境最小事实源

P0 目标是让跨环境承接复用从讨论进入可检查事实源。

P0 子项：

1. 在本文固定三环境范围和吸收边界；
2. 保留 Trae 和 Codex 现有清单，避免把环境展开继续堆在 21；
3. 复核并吸收现有 `docs/refs/claude-code/` 调研材料；
4. 将 04.07 / 04.08 中有价值内容吸收到 04.06 三环境承接矩阵；
5. 在 04.06 中吸收承接类型、三环境承接矩阵字段、承接检查、风险说明、来源和待补齐事项字段；
6. 明确三环境入口都只能是薄引用，不复制正式规范正文。

### 7.2 P1：建立承接矩阵和检查规则

P1 目标是让 42 和 landing-plan 能消费环境差异。

P1 子项：

1. 定义 LDVH 三环境承接矩阵字段；
2. 为 Trae Work CN / Codex App / Claude Code CLI 填写承接类型；
3. 给每项承接项绑定承接检查或等价检查方式；
4. 在 42 中增加候选检查：环境承接声明无承接检查、环境入口复制正文、承接项误标原生承接、环境缺失承接降级说明；
5. 在 landing-plan 输出中增加 platform_capabilities、degradations、proposed_actions 和 verification_commands。

### 7.3 P2：三环境试点

P2 目标是用三环境验证“同一 LDVH 共享内核，多套环境薄入口”。

P2 子项：

1. 在 Trae Work CN 中验证入口读取、Human Gate、Code 校验、Web 预览和 review_needed 展示；
2. 在 Codex App 中验证 AGENTS 入口、approval、exec、MCP 候选、校验命令和 diff 证据；
3. 在 Claude Code CLI 中验证入口、commands、hooks、MCP、权限确认和校验命令；
4. 记录每个环境不可等价的承接面；
5. 把环境差异回写到 04.06 三环境承接矩阵、待补齐事项或 Task。

### 7.4 P3：融合进 LDVH 正式体系

P3 目标是把稳定结论从 research 推进到正式体系。

P3 子项：

1. 修改 04.06，正式定义承接类型、三环境承接矩阵字段和检查规则；
2. 吸收 04.07、04.08 内容，并评估将二者标记为待合并、历史参考或迁移后删除；
3. 修改 42，使其能读取并检查 04.06 三环境承接矩阵；
4. 修改 landing-plan 输出合同；
5. 评估是否需要创建 proposed ADR：`LDVH 采用共享内核与环境薄入口实现三环境承接复用`；
6. 创建 Task 承接 Claude Code CLI refs、04.06 三环境承接矩阵、42 检查规则和 landing-plan 输出字段；
7. 在 Web Validate 或后续检查面中展示环境承接差异和承接降级说明。

### 7.5 跨环境融合落地形态

跨环境承接复用最终应落地为一组可被 42、landing-plan、CLI、Web 和 Human 共同消费的事实源与运行入口：

| 落地对象 | 目标位置 | 落地内容 |
|---|---|---|
| 三环境承接矩阵 | `docs/specs/04.03-环境能力清单与环境适配规范.md` | 承接类型、Trae Work CN / Codex App / Claude Code CLI 对比矩阵、承接检查、风险说明、来源和承接降级字段 |
| Trae 既有材料 | `docs/specs/04.03-环境能力清单与环境适配规范.md` | 作为迁移输入吸收到 04.06，迁移后标记为历史参考、待合并或删除候选 |
| Codex 既有材料 | `docs/specs/04.03-环境能力清单与环境适配规范.md` | 作为迁移输入吸收到 04.06，迁移后标记为历史参考、待合并或删除候选 |
| Claude Code CLI 材料 | 后续 refs 调研与 04.06 矩阵列 | Claude Code CLI refs、薄入口、commands / hooks / MCP / permission 承接方式，不新增独立 04.09 清单 |
| 42 检查 | `docs/specs/42-ldvh-landing-check-LDVH落地与检查.md` 和对应 Code | 检查环境承接声明无承接检查、入口复制正文、承接项误标原生承接、缺少承接降级说明等漂移 |
| landing-plan | `tools/specs_validate.py landing-plan` 或后续 `ldvh landing plan` | 输出 platform_capabilities、degradations、proposed_actions 和 verification_commands |
| CLI | 后续最小统一 CLI | 提供稳定查询与验证入口，不作为安装器或第二事实源 |
| Web | Web Validate 或后续检查审核面 | 展示环境承接差异、承接降级说明、检查结果和待审核项 |
| ADR / Task | `ldvh-base/adrs/`、`ldvh-base/tasks/` | 承接稳定决策、执行任务、验证证据和关闭判断 |

跨环境融合落地完成的判断标准是：Human 或 AI 能从 04.06、42 或 landing-plan 看见 Trae Work CN / Codex App / Claude Code CLI 的承接差异、承接降级原因、承接检查和 proposed actions；稳定结论能回到 04.06 三环境承接矩阵、Task、ADR、Code 或 Web；任何环境薄入口都不复制或替代 LDVH 正式规范。

---

## 8. 与 21 的关系

21 号文档应保留：

1. 受控落地执行闭环主线；
2. 测试先行；
3. Human Gate 授权后 apply / repair；
4. verify / review_needed / review / writeback / recheck；
5. 最小 CLI；
6. Web 检查与审核面；
7. 不做安装器、不做第二事实源、不做无授权自动修复。

21 号文档不再展开：

1. 环境映射鸡蛋问题；
2. Trae Work CN / Codex App / Claude Code CLI 的承接对照；
3. manifest 或能力索引的详细字段；
4. ECC 跨环境机制的详细吸收；
5. 04.06 三环境承接矩阵以及 04.07 / 04.08 迁移处理的具体改造计划。

这些内容由本文承接。21 只需要保留一条引用：跨环境承接复用和环境薄入口计划见本文。

---

## 9. 建议进入 ADR 或 Task 的事项

本文是 research，不具备正式决策效力。以下事项建议后续进入 ADR 或 Task。

### 9.1 建议进入 ADR

建议创建 proposed ADR：

```text
LDVH 采用共享内核与环境薄入口实现三环境承接复用
```

ADR 应记录的决策：

1. LDVH 跨环境承接复用首轮只覆盖 Trae Work CN、Codex App、Claude Code CLI；
2. LDVH 正式规范、工作模型、工作流程、Code 合同和事实源边界作为共享内核，不按环境分叉；
3. 环境入口只能作为环境薄入口，不复制正式规范正文；
4. 环境承接声明必须绑定事实源依据、承接检查、风险说明和承接降级；
5. 承接类型采用原生承接、适配承接、指令承接、人工降级、仅作参考、待确认等中文分级；
6. 42 和 landing-plan 应消费 04.06 三环境承接矩阵，但不得把矩阵过程结论变成第二事实源；
7. 不建设 ECC 式安装器、install state、session control plane 或多环境自动分发。

### 9.2 建议进入 Task

建议创建 Task：

```text
建立 LDVH 三环境承接复用与环境薄入口检查模型
```

验收标准：

1. 现有 Claude Code CLI refs 完成复核，并作为 04.06 三环境承接矩阵输入；
2. 04.06 定义承接类型和三环境承接矩阵字段；
3. Trae Work CN、Codex App、Claude Code CLI 三个环境均进入同一张横向对比矩阵；
4. 每项承接声明都有证据、承接检查、承接降级和待补齐事项；
5. 42 能发现环境承接声明无承接检查、入口复制正文、承接项误标原生承接和缺少承接降级说明；
6. landing-plan 能输出环境承接差异和 proposed_actions；
7. 不新增安装器、长期状态源或多环境自动分发；
8. 21 中跨环境展开内容已移出并引用本文。

---

## 10. 阶段性结论

LDVH 的跨环境承接复用不应理解为“每个环境都拥有同样能力”，而应理解为：

```text
同一套 LDVH 共享内核，
通过 Trae Work CN / Codex App / Claude Code CLI 三个环境薄入口承接，
用承接类型和承接检查公开差异，
用 42 和 landing-plan 检查漂移，
用 Git 文件事实源保存稳定结论。
```

一句话结论：

```text
LDVH 应学习 ECC 的共享内核、环境薄入口、承接类型分级和承接检查绑定方法；本轮只用 Trae Work CN、Codex App、Claude Code CLI 验证跨环境承接复用，不复制 ECC 的安装器、状态库、session control plane 或多环境分发系统。
```
