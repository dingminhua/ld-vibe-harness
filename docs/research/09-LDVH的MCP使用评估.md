# LD Vibe Harness MCP 使用评估

> 创建日期：2026-05-30
> 定位：LD Vibe Harness 对 MCP 使用的项目级评估
> 调研边界：不直接构成强制规则
> 执行效力：无，结论需进入 00-79 正式规范区间或 ADR 后才成为稳定规则
> 上位依据：`specs/00-LD-Vibe-Harness理念与纲要.md`
> 相关规范：`specs/04-事实源边界与承载规范.md`、`specs/05-Trae-Solo环境规范.md`、`specs/14-Code实现与工具规范.md`、`specs/15-Web信息同步规范.md`、`specs/08-工作流程基础规范.md`
> 来源：`specs/refs/02-Trae-MCP用法调研.md`、`specs/refs/03-社区推荐Rules-Skills-MCP与自定义Agent调研.md`、`specs/refs/01-Sequential-Thinking使用模板.md`、`specs/refs/02-Context7使用模板.md`

---

## 1. 本文解决的问题

本文评估 LD Vibe Harness 在哪些场景可能需要 MCP（Model Context Protocol）作为外部工具能力补充，哪些场景不需要或不适合引入 MCP，以及引入 MCP 时必须遵守的 LDVH 约束。

MCP 是 Trae Solo 环境中 Agent 可调用的外部工具协议层，不是 LDVH 五类构成要素中的独立要素，也不是 04 系列正式治理的三类协作机制（Rules、Skill、Agent）之一。MCP 在 LDVH 中的定位是：**Agent 的可选工具能力来源，受 05 工具基础规范和 03 事实源边界约束**。

本文是内部调研，不直接构成强制规则；调研结论进入 00-79 正式规范区间或 ADR 后才成为稳定规则。

---

## 2. MCP 在 LDVH 体系中的定位

### 2.1 MCP 不属于 LDVH 五类构成要素

LD Vibe Harness 的五类构成要素是介质、Trae Solo 环境机制、LDVH 工具、LDVH 事实模型和 LDVH 行动模型（依据 `specs/00` §三）。MCP 是 Trae Solo 环境中 Agent 可调用的工具协议，属于 Trae 平台提供的能力，不是 LDVH 自定义的构成要素。

### 2.2 MCP 不是 11 系列正式治理对象

11 系列只治理 Rules、Skill、Agent 三类可落地 AI 协作机制（依据 `specs/11` §三）。MCP 不在其中。MCP 在 LDVH 中的角色是 Agent 的工具能力来源，其使用边界由 11 §8 Agent 机制规范和 12 工具基础规范共同约束。

### 2.3 MCP 受 12 工具边界约束

MCP 工具输出与 LDVH 工具输出一样，必须遵守 `specs/12` 和 `specs/03` 的事实源边界：

1. MCP 工具输出不是最终事实源；
2. MCP 工具产生的稳定结论必须回写 Git 文件事实源后才成为 LDVH 稳定事实；
3. MCP 工具缓存、响应裁剪内容和临时上下文不得成为任务状态、证据、决策或审计的唯一来源。

### 2.4 MCP 的 LDVH 定位总结

```text
MCP 是 Agent 的可选工具能力来源。
MCP 不是规则，不是知识库，不是事实源，不是独立协作机制。
MCP 引入按"工具供应链"对待，不是按普通文档或普通规则对待。
```

---

## 3. LDVH specs 正文中的 MCP 需求触点

以下按 specs 正文内容，逐一识别可能需要 MCP 支撑的场景。

### 3.1 行动模型（specs/07）中的 MCP 需求

| 行动模型组件 | 可能需要 MCP 支撑的场景 | 候选 MCP | 评估 |
|---|---|---|---|
| Context 组织 | AI 需要理解外部框架或库的最新用法才能组装上下文 | Context7 | 适合；Context7 可为 AI 注入实时 API 文档上下文，减少 AI 凭训练数据猜测 |
| Context 组织 | AI 需要拆解复杂业务逻辑才能确定最小可行动上下文 | Sequential Thinking | 适合；复杂场景下帮助 AI 逐步推理应读取哪些事实源 |
| Scenario 识别 | 多个场景同时匹配时需要逐步推理选择优先级 | Sequential Thinking | 适合；07 §4.2.3 明确要求"多个场景同时匹配时按优先级选择"，复杂场景可借助逐步推理 |
| Gate 判断 | Gate 条件涉及复杂逻辑判定 | Sequential Thinking | 部分适合；简单 Gate 由规则直接判定，复杂 Gate（如跨项目影响分析）可借助逐步推理 |
| Skill 进入 | Skill 触发条件判断 | 不需要 MCP | Skill 进入由规则和场景匹配决定，不需要外部工具 |
| Agent 调度 | Agent 调度条件判断 | 不需要 MCP | Agent 调度由 11 §8 治理条件决定，不需要外部工具 |
| 事实源回写 | 回写目标判断和写入执行 | 不需要 MCP | 回写由 03 事实源边界和 12.01 受控写入原则决定，Tools 辅助层已覆盖 |

### 3.2 AI 协作机制（specs/11 系列）中的 MCP 需求

| 机制 | 可能需要 MCP 支撑的场景 | 候选 MCP | 评估 |
|---|---|---|---|
| Rules | 规则读取和加载 | 不需要 MCP | Rules 由 Trae 原生机制加载，不需要外部工具 |
| Skill | Skill 执行中的外部信息获取 | Context7、Fetch | 部分适合；Skill 可建议用户使用 Agent 查询外部信息，但 Skill 自身不调度 Agent（依据 11 §7 §七） |
| Agent | Agent 执行中需要外部工具能力 | 按角色分配 | 适合；这是 MCP 的核心使用场景，按 11 §8 权限最小化原则配置 |

### 3.3 工具层（specs/12 系列）中的 MCP 需求

| 工具层 | 可能需要 MCP 支撑的场景 | 候选 MCP | 评估 |
|---|---|---|---|
| Tools 辅助层 | 解析、校验、聚合 | 不需要 MCP | Tools 辅助层处理确定性逻辑，不需要外部工具能力 |
| Tools 辅助层 | 上下文包生成中的外部文档补充 | Context7 | 部分适合；上下文包主要从 Git 文件事实源生成，仅在需要外部框架文档时补充 |
| Web 信息同步层 | UI 实现和验证 | Playwright | 适合；Web Tools 页面开发后的自动化验证 |
| Web 信息同步层 | 人类确认工作台 | 不需要 MCP | 确认工作台是 Web 信息同步层自身功能，不需要外部工具 |

### 3.4 事实模型（specs/13）中的 MCP 需求

| 场景 | 可能需要 MCP 支撑 | 候选 MCP | 评估 |
|---|---|---|---|
| 对象实例创建和状态流转 | 不需要 MCP | — | 由 12.01 受控写入和对象规范决定 |
| 对象校验 | 不需要 MCP | — | 由 Tools 辅助层确定性校验覆盖 |
| 对象聚合和视图 | 不需要 MCP | — | 由 Tools 辅助层聚合和 Web 信息同步层覆盖 |

### 3.5 事实源边界（specs/03）对 MCP 的硬约束

`specs/03` 对 MCP 的硬约束如下：

1. MCP 工具输出不是最终事实源（依据 03 §四）；
2. MCP 工具产生的稳定事实必须回写 Git 文件事实源后才成为 LDVH 稳定事实（依据 03 §七）；
3. MCP 工具缓存、响应裁剪内容不得成为任务状态、证据、决策或审计的唯一来源（依据 03 §七）；
4. MCP 工具不得独立维护与 Git 文件事实源冲突的状态（依据 03 §五）。

---

## 4. 候选 MCP 评估

### 4.1 推荐引入的 MCP

#### 4.1.1 Sequential Thinking

| 维度 | 评估 |
|---|---|
| 对 LDVH 的价值 | 高。直接支撑 07 行动模型中的 Context 组织、Scenario 识别和复杂 Gate 判定；支撑 specs 修改时的跨规范影响分析；支撑事实模型设计时的复杂逻辑拆解 |
| 适用场景 | 复杂业务逻辑拆解、跨 specs 影响分析、Bug 根因排查、技术方案选型、数据流追踪 |
| 不适用场景 | 简单场景识别、直接规则判定、单文件小改、可由规则直接处理的 Gate |
| LDVH 约束 | 输出是过程信息，不是事实源；推理结论需回写 Git 文件事实源后才成为稳定事实；不应给所有 Agent 默认开启，按需分配给需要复杂推理的 Agent |
| 配置建议 | 分配给需要复杂推理的 Agent（如规范分析 Agent、架构决策 Agent），不分配给简单执行型 Agent |
| 参考模板 | `specs/refs/01-Sequential-Thinking使用模板.md` |

#### 4.1.2 Context7

| 维度 | 评估 |
|---|---|
| 对 LDVH 的价值 | 中高。支撑 07 行动模型中的 Context 组织，当 AI 需要理解外部框架或库的最新用法时提供实时文档上下文；支撑 web/ 和 tools/ 代码实现时的框架文档查询 |
| 适用场景 | 前端框架 API 查询、后端框架查询、机器学习框架查询、推理引擎查询、未知库探索 |
| 不适用场景 | 已有稳定内置文档查询工具时、查询内容已在 specs/refs/ 中有引用副本时 |
| LDVH 约束 | Context7 输出是外部文档上下文，不是 LDVH 事实源；查询结果如需长期保留，应写入 specs/refs/；不应替代 specs/ 中已有的权威规则 |
| 配置建议 | 分配给代码开发类 Agent（如 Frontend Architect、Backend Architect），不分配给规范治理或纯文档类 Agent |
| 参考模板 | `specs/refs/02-Context7使用模板.md` |

#### 4.1.3 Playwright

| 维度 | 评估 |
|---|---|
| 对 LDVH 的价值 | 中。支撑 12.02 Web 信息同步层的 UI 自动化验证；支撑 Web Tools 页面开发后的交互测试和截图回归 |
| 适用场景 | Web Tools 页面交互验证、截图回归、E2E 测试、控制台错误检查 |
| 不适用场景 | 非 Web 项目、纯规范治理任务、不需要浏览器操作的场景 |
| LDVH 约束 | 测试结果如需作为验收证据，必须回写到 ldvh-base/对应证据目录；测试截图不得只停留在 MCP 响应中；与 Puppeteer 二选一，不同时启用 |
| 配置建议 | 分配给测试类 Agent 或 Web 开发类 Agent，不分配给规范治理类 Agent |

### 4.2 条件引入的 MCP

#### 4.2.1 Figma AI Bridge

| 维度 | 评估 |
|---|---|
| 对 LDVH 的价值 | 条件性。仅在 LDVH Web Tools 需要基于 Figma 设计稿开发时有用 |
| 引入条件 | 存在 Figma 设计稿且需要 AI 辅助还原 |
| LDVH 约束 | 需要 Figma Personal Access Token，Token 不落库；生成后必须可预览验证；不得擅自修改设计内容 |
| 配置建议 | 如需引入，创建专用 Figma Agent，仅配置 Figma AI Bridge 和必要内置工具 |

#### 4.2.2 Jira / Confluence / Lark MCP

| 维度 | 评估 |
|---|---|
| 对 LDVH 的价值 | 条件性。仅在团队使用对应平台且需要 AI 辅助项目状态同步时有用 |
| 引入条件 | 团队已使用 Atlassian 或飞书体系，且需要 AI 辅助跨环境协作 |
| LDVH 约束 | OAuth / 权限必须严格控制；不得让 MCP 平台数据成为 LDVH 事实源；MCP 平台数据与 Git 文件事实源冲突时以 Git 为准 |
| 配置建议 | 如需引入，分配给 Project Manager Agent 或 Documentation Agent，权限最小化 |

#### 4.2.3 Fetch / Web Search 类

| 维度 | 评估 |
|---|---|
| 对 LDVH 的价值 | 条件性。Trae 已有内置联网搜索，功能可能重叠 |
| 引入条件 | 内置联网搜索无法满足特定需求时 |
| LDVH 约束 | 搜索结果不是事实源；如需长期保留应写入 specs/refs/ |
| 配置建议 | 评估与 Trae 内置能力重叠后按需引入 |

### 4.3 不推荐引入的 MCP

#### 4.3.1 Memory 类 MCP

| 维度 | 评估 |
|---|---|
| 不推荐原因 | 与 LDVH 核心原则直接冲突。LDVH 的核心目标之一是"让 AI 不依赖聊天记忆持续推进项目，而是围绕 Git 可追踪文件读取、执行、检查和回写"（依据 03 §一）。Memory MCP 的内容可能过期、难以审计、与项目文档和 ldvh-base 冲突，不适合承载强约束和正式状态 |
| 替代方案 | 使用 ldvh-base/承载结构化事实实例，使用 docs/ 承载管辖项目资料，使用 specs/refs/ 承载外部资料引用 |
| refs/03 的明确警告 | "对有严格事实源的项目需谨慎，避免与 docs/task-base 等事实源冲突" |

#### 4.3.2 文件系统类 MCP

| 维度 | 评估 |
|---|---|
| 不推荐原因 | Trae 已有内置文件系统工具，功能重叠 |
| 替代方案 | 使用 Trae 内置文件系统工具和 12.01 Tools 辅助层 |

#### 4.3.3 云服务 / 数据库 / 支付类 MCP

| 维度 | 评估 |
|---|---|
| 不推荐原因（对 LDVH 自身） | LDVH 是本地 / 仓库事实源框架，自身不需要云服务、数据库或支付能力 |
| 对管辖项目 | 如管辖项目需要，应由管辖项目按自身需求配置，不进入 LDVH 核心 MCP 配置；必须遵守 11 §8 权限最小化原则和 Human Gate |

---

## 5. MCP 引入的 LDVH 约束

### 5.1 事实源约束

1. MCP 工具输出不是最终事实源（依据 `specs/03` §四）；
2. MCP 工具产生的稳定结论必须回写 Git 文件事实源后才成为 LDVH 稳定事实（依据 `specs/03` §七）；
3. MCP 工具缓存、响应裁剪内容不得成为任务状态、证据、决策或审计的唯一来源（依据 `specs/03` §七）；
4. MCP 工具不得独立维护与 Git 文件事实源冲突的状态（依据 `specs/03` §五）。

### 5.2 工具边界约束

1. MCP 工具能力受 12 工具基础规范约束，不得绕过Tools 辅助层的校验和受控写入边界（依据 `specs/12` §七）；
2. MCP 工具不得直接调用 AI、Skill 或 Agent（依据 `specs/12` §七）；
3. MCP 工具不得替代 specs/、ldvh-base/或 docs/ 的权威事实（依据 `specs/12` §四）。

### 5.3 Agent 权限约束

1. MCP 应按 Agent 职责分配，不得把所有 MCP 都加给所有 Agent（依据 `specs/05-Trae-Solo环境规范.md` §8 和 refs/02 §七）；
2. Agent 的 MCP 权限范围应最小必要（依据 `specs/05-Trae-Solo环境规范.md` §8）；
3. 高风险 MCP 必须绑定专用 Agent，禁止默认开放给通用 Agent（依据 refs/03 §九.3）。

### 5.4 配置安全约束

1. 项目级 `.trae/mcp.json` 不包含明文密钥（依据 refs/02 §五）；
2. 使用的命令和包来源可信（依据 refs/02 §五）；
3. 对外部 API 的权限最小化（依据 refs/02 §五）；
4. 团队项目中应明确谁可以修改 `.trae/mcp.json`（依据 refs/02 §五）。

### 5.5 容量约束

1. 所有 MCP Server 描述信息字符数上限 8000（依据 refs/02 §八.1）；
2. 所有 MCP Server 工具数量上限 40（依据 refs/02 §八.1）；
3. MCP 响应内容可能被动态裁剪（依据 refs/02 §八.2）；
4. 应对策略：每个 Agent 只启用必要 MCP；避免功能重叠的 MCP 同时启用；把工具使用流程沉淀为 Skill，不依赖 MCP 工具描述承载全部说明。

---

## 6. MCP 与 Rules / Skill / Agent 的组合建议

### 6.1 规范分析组合

| 层 | 建议配置 |
|---|---|
| Rules | 复杂规范分析场景建议使用 Sequential Thinking；规范修改前必须评估跨 specs 影响 |
| Skill | 规范影响分析 SOP、跨文档引用检查流程 |
| MCP | Sequential Thinking |
| Agent | 规范分析 Agent（如需独立上下文和结论隔离） |

### 6.2 代码开发组合

| 层 | 建议配置 |
|---|---|
| Rules | 代码修改前先理解现有结构，完成后执行验证命令 |
| Skill | 代码开发 SOP、框架最佳实践 |
| MCP | Context7（查实时文档）、Playwright（Web 验证） |
| Agent | Frontend Architect / Backend Architect |

### 6.3 Web Tools 验证组合

| 层 | 建议配置 |
|---|---|
| Rules | Web 页面修改后必须验证功能和控制台 |
| Skill | Web 自动化测试 SOP、截图保存规范 |
| MCP | Playwright |
| Agent | 测试 Agent 或 API Test Pro |

### 6.4 文档与知识管理组合

| 层 | 建议配置 |
|---|---|
| Rules | 项目事实源优先级、文档更新日志要求、禁止把临时记忆当事实源 |
| Skill | 文档写作标准、资料摘要模板 |
| MCP | Context7（技术文档调研）、Fetch（资料获取，如需） |
| Agent | Documentation Agent |

---

## 7. MCP 引入优先级建议

### 7.1 第一优先级：Sequential Thinking

理由：

1. 直接支撑 07 行动模型的核心组件（Context、Scenario、Gate）；
2. LDVH 规范体系本身复杂度高，跨 specs 影响分析是高频需求；
3. 不依赖外部 API 密钥，本地 stdio 即可运行；
4. 已有使用模板（`specs/refs/01`）。

### 7.2 第二优先级：Context7

理由：

1. 支撑代码开发场景的实时文档查询；
2. web/ 和 tools/ 实现时需要查询框架最新用法；
3. 不依赖付费 API，本地 stdio 即可运行；
4. 已有使用模板（`specs/refs/02`）。

### 7.3 第三优先级：Playwright

理由：

1. 支撑 Web Tools 的自动化验证；
2. 官方教程支持度高；
3. 需要本地安装 Python 3 和浏览器，环境依赖较重；
4. 仅在 Web Tools 开发阶段需要。

### 7.4 条件引入

Figma AI Bridge、Jira / Confluence / Lark MCP、Fetch / Web Search 类按团队实际需要条件引入。

### 7.5 不引入

Memory 类、文件系统类、云服务 / 数据库 / 支付类 MCP 不进入 LDVH 核心 MCP 配置。

---

## 8. 与现有 research 的关系

| 现有 research | 与本文的关系 |
|---|---|
| 01-LDVH对Linear的借鉴评估 | 01 §4.1 速度感和 §4.5 状态流动体验可由 MCP 辅助实现（如 Sequential Thinking 辅助复杂场景识别），但 MCP 不是实现速度感的主要手段 |
| 02-LDVH对Gstack的借鉴评估与深度调研 | 无直接关联 |
| 03-LDVH对Agent-Harness的借鉴评估 | 03 涉及 Agent 调度，MCP 是 Agent 的工具能力来源，本文 4.1 和 4.3 的 MCP 配置建议应与 Agent-Harness 概念对齐 |
| 04-LDVH对Hermes-Agent的借鉴评估与深度调研 | 04 §4 工具注册表和 §9 工具体系对比与 MCP 工具接入策略相关，MCP 工具应纳入工具授权与可用性检查层 |
| 05-LDVH对七层管理模型的借鉴评估 | 无直接关联 |

---

## 9. 待补齐事项

1. 07 LDVH 行动模型稳定后，补齐 Sequential Thinking 在具体行动流程中的使用节点；
2. 12.01 Tools 辅助层稳定后，评估 Context7 输出是否需要纳入上下文包生成流程；
3. 12.02 Web 信息同步层稳定后，补齐 Playwright 在 Web Tools 验证中的使用规范；
4. 如未来创建 LDVH 专用 Agent，应按本文第六节的组合建议配置 MCP；
5. 如未来建立 MCP 配置治理流程，应将本文原 Human Gate 建议纳入正式规范。

---

## 10. 待补齐事项

1. 本文结论如何影响 LDVH MCP 使用策略待工具规范稳定后确定；
2. 本文结论如何影响 MCP 工具接入边界待环境适配规范稳定后确定。
