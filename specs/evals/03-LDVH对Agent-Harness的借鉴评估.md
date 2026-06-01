# LD Vibe Harness 对 Agent Harness 的借鉴评估

> 创建日期：2026-05-30
> 定位：LD Vibe Harness 对 Agent Harness 的项目级借鉴评估
> 调研边界：不直接构成强制规则
> 执行效力：无，结论需进入 00-79 正式规范区间或 ADR 后才成为稳定规则
> 上位依据：`specs/00-LD-Vibe-Harness理念与纲要.md`
> 相关规范：`specs/02-LDVH术语规范.md`、`specs/01-LDVH目录说明.md`、`specs/10-事实源边界与承载规范.md`

---

## 1. 本文解决的问题

本文评估 Agent Harness 这一产品形态和工程理念对 LD Vibe Harness 的借鉴价值，同时明确 LD Vibe Harness 不应简单复制通用 Agent 平台或自动化执行框架，而应保持自身“面向 Vibe Coding 的工程驾驭框架”定位。本文是内部调研，不直接构成强制规则；调研结论进入 00-79 正式规范区间或 ADR 后才成为稳定规则。

---

## 2. 结论

Agent Harness 对 LD Vibe Harness 有很高参考价值，因为二者都在解决同一个底层问题：如何让大语言模型不只是生成文本，而是在工程场景中可控、可验证、可追溯地行动。

但 LD Vibe Harness 不应把自己定义为通用 Agent Harness 平台。更准确的判断是：

> Agent Harness 是围绕 LLM 构建的执行约束系统；LD Vibe Harness 是面向 Vibe Coding + Trae Solo 场景的工程驾驭框架，核心在于 Git 文件事实源、Harness 事实模型和 AI 行动模型。

LD Vibe Harness 最值得借鉴 Agent Harness 的不是“让 AI 更自主”，而是以下能力组合：

1. 把模型能力包进受控执行框架，而不是依赖单轮提示词；
2. 用规则、上下文、工具、验证和记忆共同约束 AI 行动；
3. 把执行过程拆成可观察、可停止、可恢复、可审计的步骤；
4. 用测试、检查、证据和门禁降低非确定性风险；
5. 把经验和失败沉淀为长期事实源，而不是留在聊天上下文里。

一句话说：

```text
Agent Harness 的启发不是替代人让 AI 全自动干活，而是给 AI 的行动装上工程化的身体、刹车、仪表盘和记忆系统。
```

---

## 3. Agent Harness 概念概览

在 AI 工程语境下，Agent Harness 通常指围绕 LLM 构建的一整套“非模型”工程系统。它把模型的理解、规划和生成能力接入规则、工具、运行环境、验证机制和记忆系统，使 AI 能从聊天助手变成可执行任务的 Agent。

常见公式是：

```text
Agent = LLM + Harness
```

这里的 Harness 不只是提示词，也不只是某个 SDK 或工具调用接口，而是一套执行约束和工程闭环。

| 组成 | 作用 |
|---|---|
| Rules / Policy | 定义 AI 能做什么、不能做什么、按什么规则做 |
| Context Manager | 控制给 AI 的上下文范围，减少遗漏和过载 |
| Tool Router | 连接文件、Shell、浏览器、API、数据库等外部能力 |
| Runtime / Sandbox | 控制执行环境、权限、超时、隔离和回滚 |
| Test Harness | 用测试、lint、typecheck、安全扫描验证结果 |
| Guardrails | 拦截高风险操作、敏感信息、越权执行和破坏性变更 |
| Memory Store | 沉淀任务、决策、错误、经验和长期上下文 |
| Feedback Loop | 捕获失败、修复、复测，并把经验写回系统 |

Agent Harness 的核心价值是把 LLM 的随机生成能力，放进一个可执行、可检查、可治理的工程容器里。

---

## 4. 与 LD Vibe Harness 的关系判断

| 维度 | Agent Harness | LD Vibe Harness |
|---|---|---|
| 产品形态 | 通用 Agent 执行框架、运行时或工程理念 | 本地规范 + Harness 工具 + 事实模型 + 行动模型 |
| 第一服务对象 | LLM Agent 的执行能力 | AI 执行者在项目中的稳定协作 |
| 核心目标 | 让 AI 能调用工具、执行任务、验证结果 | 让 AI 知道读什么、做什么、不能做什么、何时停下、如何回写 |
| 数据事实源 | 可能是数据库、向量库、运行日志、任务状态或外部系统 | Git 仓库中的 specs、ldvh-base、docs |
| 记忆方式 | 会话记忆、长期记忆、检索索引、任务轨迹 | ADR、Task、Memo、Pitfall、Change 等 Git 文件事实源 |
| 工具定位 | Agent 执行能力的一部分 | 读取、校验、聚合、展示和受控写入事实源的辅助能力 |
| 风险边界 | 工具越权、沙箱逃逸、错误执行、幻觉调用 | 事实源漂移、状态流转违规、Human Gate 未触发、证据未回写 |
| 人的角色 | 可能是监督者、审批者或任务发起者 | 表达意图、补充约束、确认关键节点、验收结果 |

LD Vibe Harness 与 Agent Harness 的关系可以概括为：

```text
Agent Harness 解决“怎样让 AI 像 Agent 一样行动”；
LD Vibe Harness 解决“怎样让 AI 在真实项目事实源中受控行动并留下证据”。
```

因此，LD Vibe Harness 可以吸收 Agent Harness 的执行框架思想，但必须保持自身边界：

```text
LD Vibe Harness 不直接成为通用 Agent 平台
LD Vibe Harness 不把运行时记忆当作最终事实源
LD Vibe Harness 不鼓励绕过 Human Gate 的全自动执行
LD Vibe Harness 的核心价值仍是事实源治理和 AI 行动控制
```

---

## 5. 最值得借鉴的设计思想

### 5.1 Harness 不是提示词，而是工程底座

Agent Harness 的第一层启发是：稳定的 AI 协作不能只靠更好的 Prompt。

Prompt 可以改善一次回答，但不能稳定解决以下问题：

- AI 是否读取了正确事实源；
- AI 是否理解当前目录和对象边界；
- AI 是否知道哪些操作必须停下；
- AI 是否执行了验证命令；
- AI 是否把结果写回可追溯文件；
- 下一次会话是否能恢复关键上下文。

LD Vibe Harness 应继续坚持：规则、事实源、工具、事实模型和行动模型共同构成工程底座。Prompt 只是入口之一，不能替代 Harness。

对应到 LD Vibe Harness：

| Agent Harness 启发 | LD Vibe Harness 落点 |
|---|---|
| Prompt 不等于治理 | specs / rules / action model 才是稳定约束 |
| 工具调用需要上下文边界 | 事实源边界和最小可行动上下文 |
| 执行必须可验证 | Task 的 acceptance、verification、closure_evidence |
| 长期经验需要沉淀 | ADR、Pitfall、Change、Memo |

### 5.2 把 AI 行动拆成可控循环

Agent Harness 通常不会让模型“一步到底”，而是把行动拆成观察、计划、执行、检查和修正等循环。

LD Vibe Harness 可以借鉴这种循环意识，但落点不是引入复杂 Agent Runtime，而是让 Harness 行动模型更加清楚地表达 AI 的行动步骤：

```text
读取事实源 → 识别场景 → 判断 Gate → 拆解任务 → 执行变更 → 验证结果 → 回写证据 → 等待验收或关闭
```

这与 `specs/00-LD-Vibe-Harness理念与纲要.md` 中“AI 进入项目后，如何知道该读什么、做什么、不能做什么、何时停下等待人确认，以及完成后如何把事实写回项目”的核心问题一致。

建议 LD Vibe Harness 后续在行动模型中强化：

| 行动步骤 | 需要回答的问题 |
|---|---|
| 读取 | 当前任务最小上下文是什么 |
| 判断 | 这是执行、验收、决策、审计还是复盘场景 |
| Gate | 是否涉及 Human Gate 或高风险操作 |
| 执行 | 允许修改哪些文件，禁止触碰哪些边界 |
| 验证 | 应运行哪些检查，证据如何记录 |
| 回写 | 结果进入 Task、Change、ADR、Pitfall 还是 Memo |

### 5.3 把工具调用纳入治理，而不是追求更多工具

Agent Harness 往往强调 Tool Use：文件、Shell、浏览器、API、数据库、搜索、代码执行环境等。它的价值不在于工具数量，而在于工具调用发生在受控上下文里。

LD Vibe Harness 可以借鉴工具治理思想：

| 工具能力 | 借鉴点 | LD Vibe Harness 边界 |
|---|---|---|
| 文件读写 | AI 能真实修改项目 | 必须遵守事实源边界和 Change 要求 |
| Shell | AI 能运行检查和验证 | 不自动执行高风险、远程发布或不可逆命令 |
| 浏览器 | AI 能观察真实界面 | 证据可进入 Task，但工具截图不自动成为唯一事实源 |
| 搜索 | AI 能校正幻觉 | 搜索结果必须回到文件事实源判断 |
| 自动修复 | AI 能形成反馈闭环 | 修复后必须复测并留下验证结果 |

因此，LD Vibe Harness 的工具建设不应以“接入更多外部能力”为第一目标，而应优先让已有工具更好地读取、聚合、校验和受控写入 Git 文件事实源。

### 5.4 Guardrails 应产品化、可见化

Agent Harness 的 Guardrails 通常包括权限控制、敏感信息保护、沙箱隔离、高危操作确认、输出过滤和策略检查。

LD Vibe Harness 已有 Human Gate、事实源边界和项目规则，但 Agent Harness 的启发是：护栏不应只存在于文档中，也应成为 AI 和人都能看见的行动提示。

可借鉴的产品化方向：

| 场景 | 可见化提示 |
|---|---|
| 修改 specs 正式规范 | 显示可能触发 Human Gate 的原因和影响范围 |
| 创建或关闭 Task | 显示必填 evidence / verification / closure_evidence |
| 变更事实源目录 | 提示对应权威规范和 Change 记录要求 |
| 新增依赖或工具能力 | 提示安全、维护成本和规则边界 |
| 尝试非法状态流转 | 解释为什么不能流转，以及下一步允许动作 |

这能把“Rules 约束”转化为“操作时的即时引导”，降低 AI 和人记忆规范的成本。

### 5.5 Memory Store 的核心不是存更多，而是存可复用事实

许多 Agent Harness 会设计 Memory Store，用于保存长期偏好、历史任务、环境信息、错误经验和上下文摘要。它的风险是：如果记忆不可审计、不可追踪、不可更新，就会变成新的幻觉来源。

LD Vibe Harness 在这一点上应坚持自身优势：长期记忆必须回到 Git 文件事实源，而不是依赖模型记忆、聊天上下文、向量库缓存或工具运行状态。

建议继续强化：

| 记忆类型 | LD Vibe Harness 承载 |
|---|---|
| 已完成工作 | Task 状态和 closure_evidence |
| 变更事实 | Change |
| 架构决策 | ADR |
| 踩坑经验 | Pitfall |
| 随手记录 | Memo |
| 审计发现 | Audit / Finding 相关对象 |

Agent Harness 的启发不是替换这些对象，而是让 AI 在行动前更容易命中相关记忆，在行动后更稳定地把新经验写回对应对象。

### 5.6 Test Harness 是把“感觉完成”变成“证据完成”

Vibe Coding 容易出现“看起来完成了”的错觉。Agent Harness 强调测试和反馈循环，能提醒 LD Vibe Harness：完成不应以 AI 自述为准，而应以可追溯证据为准。

LD Vibe Harness 后续可以在事实模型和行动模型中进一步强化：

| 阶段 | 证据要求 |
|---|---|
| Task 创建 | acceptance 应可观察、可验证 |
| 执行中 | 记录关键修改和风险 |
| Review Needed | 提供验证命令、检查结果或人工验证说明 |
| Closed | closure_evidence 能说明为什么可以关闭 |
| 失败或返工 | 必要时沉淀 Pitfall 或更新行动模型 |

这与 LD Vibe Harness 的价值标准 V4“证据沉淀”和 V5“事实回写”一致。

---

## 6. 对 LD Vibe Harness 的启发

### 6.1 把“Agent 能力”转译为“行动模型能力”

Agent Harness 常说的 Agent 能力，包括规划、工具调用、反思、记忆和自主执行。LD Vibe Harness 不宜直接追求“更强 Agent”，而应把这些能力转译为行动模型中的可治理能力。

| Agent 能力 | LD Vibe Harness 转译 |
|---|---|
| Planning | Intent / TaskSet / Task 的拆解和状态流转 |
| Tool Use | 受控读取、编辑、检查和回写事实源 |
| Reflection | Review、验证结果、Pitfall、Change |
| Memory | ADR、Task、Memo、Pitfall、Change |
| Autonomy | 在 Human Gate 之前的安全范围内自主推进 |
| Delegation | Skill 进入和必要时的 Agent 调度 |

这能避免 LD Vibe Harness 被“Agent 平台化”带偏，同时吸收 Agent Harness 的工程化价值。

### 6.2 强化最小可行动上下文

Agent Harness 的上下文管理提醒 LD Vibe Harness：AI 不是读得越多越好，而是要读到足够、相关、可行动的上下文。

建议后续围绕以下上下文包设计工具或行动规范：

| 上下文包 | 内容 |
|---|---|
| Task 上下文 | 当前 Task、source_doc、dependencies、acceptance、最近更新 |
| Decision 上下文 | 决策问题、选项、相关 ADR、影响范围、Human Gate |
| Review 上下文 | 变更摘要、验证结果、closure_evidence、待验收事项 |
| Pitfall 上下文 | 历史踩坑、规避方式、关联文件或规范 |
| Change 上下文 | 本次变更原因、影响文件、验证状态 |

这些上下文包可以供 AI 或人复制使用，但最终依据仍应是 Git 文件事实源。

### 6.3 让 Human Gate 成为执行循环的一部分

Agent Harness 中的审批和 Guardrails 通常嵌入执行循环。LD Vibe Harness 也应避免把 Human Gate 当成文档里的静态条款，而应让 AI 在行动中持续判断：

```text
这一步是否会改变权威规范？
这一步是否会改变事实源位置？
这一步是否涉及删除、重排、远程发布或新增高影响依赖？
这一步是否需要用户确认后才能继续？
```

如果触发 Human Gate，AI 应暂停并说明：

1. 触发原因；
2. 涉及事实源；
3. 影响范围；
4. 建议确认事项；
5. 可选路径。

这与 LD Vibe Harness “人主 AI 辅”的定位一致。

### 6.4 把反馈循环写回事实源

Agent Harness 的 Feedback Loop 价值在于执行失败后不只是重试，而是将失败转化为系统改进。

LD Vibe Harness 可以借鉴为：

| 反馈类型 | 回写位置 |
|---|---|
| 一次普通执行结果 | Task 更新和 closure_evidence |
| 文档或规则变更 | Change |
| 架构或治理决策 | ADR |
| 重复踩坑或反直觉问题 | Pitfall |
| 未成熟想法 | Memo |
| 行动模型缺口 | 进入 40-69 正式规范候选或 ADR |

这样，AI 的每一次执行都不只是当前任务的完成，也可能改善后续协作系统。

---

## 7. 可落地建议

### 7.1 短期建议

| 建议 | 说明 |
|---|---|
| 将 Agent Harness 组件映射到 LDVH 五类构成要素 | 明确 Rules、Tooling、Memory、Feedback Loop 分别落在哪类构成要素中 |
| 在行动模型中强化“读取 → 判断 → 执行 → 验证 → 回写”循环 | 让 AI 进入项目后的步骤更清楚 |
| 增强 Task 上下文包 | 聚合 source_doc、dependencies、acceptance、verification、closure_evidence |
| 在工具中展示 Human Gate 提示 | 把护栏变成可见交互，而不是只写在规范里 |
| 强化关闭证据检查 | 防止任务仅凭 AI 自述进入 Closed |

### 7.2 中期建议

| 建议 | 说明 |
|---|---|
| 建立行动场景分类 | 区分意图澄清、任务执行、验收关闭、决策等待、复盘沉淀等场景 |
| 将高频执行循环沉淀为 Skill | 如任务关闭检查、上下文生成、Human Gate 判断、Pitfall 复盘 |
| 设计 Memory 命中机制 | 让 AI 在执行前更容易读取相关 ADR、Pitfall、Change 和 Task 历史 |
| 建立事实源健康检查 | 校验对象字段、状态流转、证据缺口和引用关系 |
| 建立反馈沉淀提示 | 当出现失败、返工、规则缺口时提示是否创建 Pitfall / Change / ADR |

### 7.3 暂不建议

| 不建议项 | 原因 |
|---|---|
| 把 LD Vibe Harness 做成通用 Agent Runtime | 会偏离 Git 文件事实源和 AI 行动治理定位 |
| 让工具直接调用 AI 自主执行任务 | 当前定位是 Harness 工具和事实源治理，不是 AI 执行平台 |
| 用向量库或运行时数据库替代 Git 文件事实源 | 会削弱可审计性和项目可追溯性 |
| 追求完全自动关闭任务 | 关闭必须依赖 evidence、review 和必要的人类确认 |
| 过早引入复杂沙箱和权限系统 | 当前更应先做好事实源边界、状态流转和证据回写 |

---

## 8. 风险评估

| 风险 | 表现 | 控制方式 |
|---|---|---|
| 过度 Agent 化 | LD Vibe Harness 变成追求自主执行的 Agent 平台 | 坚持 AI 行动模型服务事实源治理 |
| 事实源漂移 | 运行时记忆、缓存或工具状态取代 Git 文件 | 坚持 specs、ldvh-base、docs 为最终事实源 |
| 自动化越权 | AI 或工具绕过 Human Gate 执行高影响操作 | 将 Gate 判断嵌入行动模型和工具提示 |
| 工具复杂度膨胀 | 为了像 Agent Harness 而接入过多能力 | 优先做读取、校验、聚合、受控写入 |
| 证据形式化 | verification / closure_evidence 只填空泛说明 | 建立关闭前证据检查和 Review 入口 |
| 记忆污染 | 不可靠摘要或缓存被当成事实 | 长期记忆必须可追溯、可审查、可修改 |

---

## 9. 评估结论

Agent Harness 对 LD Vibe Harness 的核心启发可以浓缩为一句话：

> 不要只让 AI 会生成代码，要让 AI 在规则、上下文、工具、验证、门禁和记忆构成的工程系统中行动。

LD Vibe Harness 应吸收这一思想，但走自己的路径：

```text
Agent Harness：给 LLM 装上可执行的工程外骨骼
LD Vibe Harness：给 Vibe Coding 装上可追溯的项目事实源和行动治理系统
```

因此，LD Vibe Harness 后续最优先的借鉴方向不是增加 AI 自主性，而是把现有规范和对象体系产品化、流程化、证据化：

1. 最小可行动上下文更容易生成；
2. AI 行动步骤更清楚；
3. Human Gate 更可见；
4. 工具调用更受控；
5. 验证证据更完整；
6. 反馈循环能沉淀到 Change、Pitfall、ADR、Task、Memo；
7. 运行时便利不替代 Git 文件事实源。

当这些能力稳定后，再考虑将高频流程沉淀为 Skill；只有在独立上下文、权限隔离、并行委派或调度成为真实需求时，再考虑更重的 Agent 机制。

---

## 10. 待补齐事项

1. 本文结论如何进入 04 LDVH AI 协作规范（Skill / Agent / Rules 使用边界）待机制规范稳定后确定；
2. 本文结论如何影响 05 LDVH 工具基础规范（如上下文包、Human Gate 可见化、事实源健康检查）待工具规范稳定后确定；
3. 本文结论如何影响 10-39 事实模型规范（如 Task evidence、verification、closure_evidence）待对象规范稳定后确定；
4. 本文结论如何影响 40-69 行动模型规范（如执行循环、Gate 判断、反馈沉淀）待行动模型规范稳定后确定。
