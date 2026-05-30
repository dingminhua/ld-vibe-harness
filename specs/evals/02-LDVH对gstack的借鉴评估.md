# LD Vibe Harness 对 gstack 的借鉴评估

> 创建日期：2026-05-30
> 状态：内部调研
> 编号归属：70-89 内部调研
> 调研边界：不直接构成强制规则
> 执行效力：无，结论需进入 01-69 正式规范区间或 ADR 后才成为稳定规则
> 上位依据：`specs/00-LD-Vibe-Harness理念与纲要.md`
> 相关规范：`specs/01-specs文档结构规范.md`、`specs/02-LDVH目录说明.md`、`specs/03-事实源边界与承载规范.md`

---

## 一、本文解决的问题

本文评估 LD Vibe Harness 应如何借鉴 gstack 的设计思想，同时保持自身"面向 Vibe Coding 的工程驾驭框架"的独特定位。本文是内部调研，不直接构成强制规则；调研结论进入 01-69 正式规范区间或 ADR 后才成为稳定规则。

---

## 二、结论

gstack 对 LD Vibe Harness 有较高参考价值，但 LD Vibe Harness 不应复制 gstack 的产品形态。

更准确的判断是：

> gstack 是面向 Claude Code 的 AI 工程工作流与技能工厂；LD Vibe Harness 是面向 Vibe Coding + Trae Solo 场景的工程驾驭框架，围绕事实源、生产对象和行动模型设计。

LD Vibe Harness 最值得借鉴 gstack 的不是具体命令数量，也不是浏览器守护进程本身，而是以下能力组合：

1. 把 AI 协作拆成明确阶段和专业角色
2. 把高频协作流程固化为可复用 Skill
3. 把质量、QA、安全、发布、复盘纳入同一条工程链路
4. 坚持用户主权：AI 建议，人类决策
5. 用工具降低执行摩擦，但不让工具取代事实源和治理判断

---

## 三、项目概览

gstack 是一个围绕 Claude Code 构建的 AI 工程工作流项目。它通过一组 Markdown Skill、CLI 工具、浏览器能力和本地状态机制，把单个 AI 编程助手扩展成类似"虚拟工程团队"的协作体系。

从公开仓库观察，gstack 的核心组成包括：

| 模块 | 作用 |
|---|---|
| Skill 集合 | 将 CEO、工程、设计、QA、安全、发布、复盘等角色固化为可调用工作流 |
| 浏览器能力 | 通过持久化 Chromium 守护进程支持真实页面 QA、截图、交互和验证 |
| 计划评审流程 | 在编码前进行产品、工程、设计、DX 等多视角评审 |
| 实现后门禁 | 通过 review、qa、cso、ship、land-and-deploy 等流程提升交付质量 |
| 记忆与复盘 | 通过 context-save、context-restore、learn、retro 等能力沉淀上下文和经验 |
| 安全约束 | 通过 careful、freeze、guard、权限隔离、隧道隔离等方式降低误操作风险 |

这说明 gstack 的重点不是"任务管理"，而是"让 AI 编程流程可重复、可审查、可提速、可交付"。

---

## 四、与 LD Vibe Harness 的关系判断

| 维度 | gstack | LD Vibe Harness |
|---|---|---|
| 产品形态 | Claude Code Skill + CLI + 浏览器工具 | 本地规范 + Harness 工具 + 生产对象 + 行动模型 |
| 核心对象 | Skill、Agent 角色、浏览器会话、发布流程、上下文记忆 | Intent、Task、Memo、ADR、Evidence、Change、Pitfall |
| 主要目标 | 把 AI 编码助手扩展成工程团队流水线 | 让 AI 进入项目后知道读什么、做什么、不能做什么、何时停下、如何回写 |
| 数据事实源 | 技能文件、仓库文档、运行状态、上下文存档 | Git 仓库中的 specs、ldvh-base、docs |
| AI 角色 | 直接驱动 AI 工作流 | AI 是行动模型的执行者，不是工具直接调用的对象 |
| 工具价值 | 降低 AI 工程执行摩擦 | 降低读取、校验、聚合、展示和受控写入事实源的成本 |
| 风险边界 | 浏览器、远程配对、安全令牌、自动发布 | 事实源漂移、状态流转违规、门禁未触发、证据未回写 |

LD Vibe Harness 不应成为 gstack clone。LD Vibe Harness 可以吸收 gstack 的工程化协作思想，但必须保持自身边界：

```text
LD Vibe Harness 不直接调用 AI
LD Vibe Harness 不成为事实源
LD Vibe Harness 不替代 Human Gate
LD Vibe Harness 的工具只做聚合视图和受控编辑入口
```

---

## 五、最值得借鉴的设计思想

### 5.1 阶段化 AI 工程流程

gstack 将软件开发拆成多个阶段：想法澄清、计划评审、工程评审、设计评审、实现、QA、安全、发布、复盘。每个阶段都有明确入口和输出。

LD Vibe Harness 可以借鉴这种阶段化方式，但落点不是"自动执行这些阶段"，而是让 Harness 行动模型能判断一个意图或任务当前处于什么治理阶段。

建议 LD Vibe Harness 在行动模型中强化以下阶段：

| 阶段 | LD Vibe Harness 中的呈现 |
|---|---|
| 输入 | Intent 或 Memo |
| 分析 | 关联 docs / ADR / 审计发现 |
| 决策 | Decision Needed / Human Gate |
| 执行 | Task 进入 Executing |
| 验证 | Review Needed，若升级为正式规范，宜要求验证证据 |
| 关闭 | Closed，若升级为正式规范，宜要求 closure_evidence |
| 复盘 | 进入 Change、Pitfall 或 ADR |

这能把 LD Vibe Harness 的状态机从"字段"变成"AI 理解的流程"。

### 5.2 角色化 Skill 矩阵

gstack 的一个核心优势是角色非常清晰：CEO reviewer、eng manager、designer、QA lead、security officer、release engineer 等。每个 Skill 不只是提示词，而是一个稳定工作流。

LD Vibe Harness 可以借鉴角色矩阵，但不宜一开始创建大量 Agent。更适合的路径是：

```text
先沉淀角色视角 → 再沉淀 Skill → 最后在确有隔离需求时创建 Agent
```

可参考的 LD Vibe Harness 角色视角：

| gstack 角色 | LD Vibe Harness 可借鉴角色 | 用途 |
|---|---|---|
| CEO reviewer | 意图价值审视 | 判断目标是否值得做、是否偏离方向 |
| Eng reviewer | 规范与架构审视 | 判断状态机、事实源、接口边界是否正确 |
| Designer | 体验审视 | 判断视图是否清楚、操作是否低摩擦 |
| QA lead | 验证证据审视 | 判断完成标准和验证方式是否充分 |
| CSO | 风险与权限审视 | 判断是否涉及破坏性操作、依赖、密钥、跨项目影响 |
| Release engineer | 关闭与发布审视 | 判断是否可关闭、是否需要 Change 或 ADR |

这与 LD Vibe Harness 后续 Trae Solo 环境机制规范中 Rule / Skill / Agent 的边界一致：默认优先 Rule + Skill，只有独立上下文、权限隔离、并行委派或调度明确需要时才升级为 Agent。

### 5.3 "计划先行"的门禁体验

gstack 中 plan-ceo-review、plan-eng-review、plan-design-review、plan-devex-review 和 autoplan 体现了一个重要原则：重要工作在执行前应先被多视角审视。

LD Vibe Harness 可借鉴为行动模型中的前置检查能力：

| 场景 | LD Vibe Harness 可提示的问题 |
|---|---|
| 新 Intent 进入分析 | 目标是否清楚？成功标准是否可验证？是否已有事实源？ |
| Task 创建 | 是否有 source_doc / source_intent？是否有 acceptance？是否能关闭？ |
| 状态进入 Executing | 前置条件是否满足？是否有阻塞依赖？ |
| 状态进入 Review Needed | 是否有验证方式和证据？ |
| 状态进入 Closed | closure_evidence 是否完整？是否需要 Change 或 ADR？ |

这类提示不需要 LD Vibe Harness 调用 AI，也可以先用规则校验和静态检查实现。

### 5.4 "真实环境 QA"意识

gstack 很重视浏览器 QA，强调真实 Chromium、真实点击、截图、响应式、表单、上传、弹窗和部署后验证。

LD Vibe Harness 目前不是浏览器自动化工具，但可以借鉴它的 QA 证据思维：任务关闭前必须能回答"在哪里验证、怎么验证、证据是什么"。

建议 LD Vibe Harness 在生产对象规范中强化：

| 字段或视图 | 借鉴点 |
|---|---|
| acceptance | 用可观察行为描述完成标准 |
| verification | 记录实际验证命令、页面、截图或检查方式 |
| closure_evidence | 关闭时必须填入证据 |
| related_audit | 审计发现关闭要能回链到验证结果 |

LD Vibe Harness 不必内置 gstack 式浏览器守护进程，但可以让任务天然容纳来自人工、Trae、浏览器工具或其他 QA 工具的验证证据。

### 5.5 安全与破坏性操作边界

gstack 的 careful、freeze、guard、隧道双监听、安全令牌、cookie 处理等设计体现了清晰的风险分层。

LD Vibe Harness 可借鉴为门禁规则：

| 风险类型 | LD Vibe Harness 中的建议处理 |
|---|---|
| 删除文件、重排文档编号、变更事实源 | 触发 Human Gate |
| 新增依赖、引入 GUI 框架、修改工具架构 | 触发 Human Gate |
| 跨项目影响、接口契约变化 | 触发跨项目评估 |
| 审计发现自动转任务 | 不能无脑任务化，必须先分类 |
| 修改规则或规范 | 必须同步创建 Change 和更新索引 |

LD Vibe Harness 已有硬约束。gstack 的启发是：门禁不应只写在文档里，也应在 Harness 工具和 AI 行动模型中可见。

### 5.6 用户主权原则

gstack 的 ETHOS 强调"AI models recommend, users decide"。这与 LD Vibe Harness 的 Human Gate 原则高度一致。

LD Vibe Harness 应继续坚持：

```text
AI 可以建议
工具可以提示
审计可以发现
但关键决策必须由用户确认
```

尤其是以下场景不能自动执行：

1. 架构方向变化
2. 文档编号重排
3. 删除或归档关键资产
4. 新增依赖
5. 跨项目规则或契约变化
6. 把不确定审计发现自动变成执行任务

---

## 六、对 LD Vibe Harness 的启发

### 6.1 从"看板"升级为"协作驾驭体系"

gstack 的命令集合覆盖了从想法到发布的完整链路。LD Vibe Harness 可将自身设计为项目治理驾驶舱，而不是普通任务列表。

建议强化五类入口：

| 入口 | 目标 |
|---|---|
| 今日行动 | 展示当前最该处理的 Task |
| 决策等待 | 聚合 Decision Needed 和 Human Gate |
| 验证等待 | 聚合 Review Needed 和缺少 closure_evidence 的任务 |
| 审计闭环 | 展示审计发现分类、处理状态、关闭证据 |
| AI 上下文 | 一键生成当前任务需要阅读的 specs、docs、ADR、审计摘要 |

### 6.2 给每个任务生成"下一步提示"

gstack 的 Skill 是可执行流程，LD Vibe Harness 可以先从轻量的下一步提示做起。

例如任务状态为 `Review Needed` 时，Harness 工具或 AI 行动模型应提示：

```text
关闭前需要：
1. 填写验证方式
2. 填写 closure_evidence
3. 判断是否需要创建 Change
4. 若涉及决策，确认是否已有 ADR
```

这样可以把规范转化为产品体验，降低 AI 和人记忆规则的负担。

### 6.3 把"AI 上下文包"产品化

gstack 通过 context-save/context-restore 解决跨会话上下文恢复。LD Vibe Harness 的优势是项目事实源更明确，因此更适合生成任务级上下文包。

建议 LD Vibe Harness 提供：

| 上下文包 | 内容 |
|---|---|
| Task 上下文 | 当前任务 YAML、source_doc、dependencies、acceptance、closure_evidence |
| Intent 上下文 | Intent 文档、关联 TaskSet、相关 ADR |
| Audit 上下文 | 审计快照、审计发现、分类结果、待关闭任务 |
| Human Gate 上下文 | 决策问题、选项、影响范围、推荐阅读 |

这些上下文包可以提供给 AI 或人，但 LD Vibe Harness 本身不需要直接调用 AI。

---

## 七、可落地建议

### 7.1 短期建议

| 建议 | 说明 |
|---|---|
| 在任务详情增加下一步提示 | 根据状态机提示允许流转、必填证据和 Human Gate |
| 设计 AI 上下文复制入口 | 从 Task / Intent / Audit 聚合推荐阅读材料 |
| 强化 Review Needed 视图 | 聚合所有待验证、缺证据、待关闭任务 |
| 审计发现分类时显示理由 | 避免"自动任务化"黑盒 |
| 将 closure_evidence 做成关闭门槛 | 关闭不是改状态，而是提交证据 |

### 7.2 中期建议

| 建议 | 说明 |
|---|---|
| 建立 LD Vibe Harness Skill 矩阵 | 围绕意图审查、任务关闭、审计分类、上下文生成沉淀 Skill |
| 增加决策视图 | 聚合 Decision Needed、ADR 候选、Human Gate 等待项 |
| 增加复盘视图 | 从 Change、Pitfall、关闭任务中形成周期性回顾 |
| 增加治理健康分 | 用静态检查展示 specs、ldvh-base、docs 的健康状态 |

### 7.3 暂不建议

| 不建议项 | 原因 |
|---|---|
| 复制 gstack 的大量 slash commands | LD Vibe Harness 的主要对象不同，照搬会制造复杂度 |
| 让 LD Vibe Harness 直接调用 AI | 违反当前工具边界，且会模糊事实源与执行者 |
| 内置浏览器自动化守护进程 | 当前 LD Vibe Harness 不是 QA 自动化工具，可先接收外部证据 |
| 一次性创建大量 LD Vibe Harness Agent | Agent 有上下文和权限成本，应先用 Skill 验证流程稳定性 |
| 自动发布、自动提交、自动合并 | LD Vibe Harness 是治理框架，不是发布机器人 |

---

## 八、风险评估

| 风险 | 表现 | 控制方式 |
|---|---|---|
| 过度 gstack 化 | LD Vibe Harness 变成 AI 命令集合，失去事实源治理定位 | 坚持 specs/ldvh-base/docs 为事实源 |
| Skill 泛滥 | 每个想法都做 Skill，维护成本升高 | 只有重复、多步骤、稳定输出的流程才做 Skill |
| Agent 泛滥 | 角色很多但没有独立上下文必要 | 按 Trae Solo 环境机制规范中的 Agent 创建门槛执行 |
| 自动化越权 | 工具直接替用户做关键决策 | Human Gate 必须可见、可审计 |
| 证据形式化 | closure_evidence 变成空字段 | 关闭时校验非空、可追溯、能说明验证结果 |
| 外部项目误读 | 把 gstack 的 Claude Code 实现当成 Trae 事实 | Trae 落地以 Trae Solo 环境机制规范为准 |

---

## 九、评估结论

gstack 对 LD Vibe Harness 的核心启发可以浓缩为一句话：

> 把 AI 协作从"临场聊天"升级为"有角色、有阶段、有证据、有门禁、有复盘的工程系统"。

LD Vibe Harness 应吸收这一思想，但走自己的路径：

```text
gstack：让 AI 更像一支工程团队
LD Vibe Harness：让项目事实源和 AI 协作治理更像一个可操作的驾驭框架
```

因此，LD Vibe Harness 后续最优先的借鉴方向不是增加更多 AI 能力，而是把现有规范产品化：

1. 状态流转可见
2. 下一步动作可见
3. 关闭证据可见
4. Human Gate 可见
5. AI 上下文可复制
6. 审计闭环可追踪
7. 意图全貌可理解

当这些能力稳定后，再逐步把高频治理流程沉淀为 LD Vibe Harness Skill；只有在独立上下文、权限隔离、并行委派或调度成为真实需求时，再考虑 LD Vibe Harness Agent。

---

## 十、Human Gate 与检查要求

本文是内部调研，不直接触发 Human Gate。

当本文结论需要进入 01-69 正式规范区间或创建 ADR 时，应评估 Human Gate。

调研检查至少包括：

| 检查项 | 标准 |
|---|---|
| 上位依据 | 已声明上位依据 |
| 调研边界 | 明确不直接构成强制规则 |
| 与 00 总纲一致性 | 不违背 LD Vibe Harness 理念和五类构成要素 |
| 与事实源边界一致性 | 不定义新的事实源规则，只讨论体验优化方向 |
| 升级路径 | 明确结论进入正式规范或 ADR 的路径 |

---

## 十一、待补齐事项

1. 本文结论如何进入 05 LDVH 工具基础规范待工具规范稳定后确定；
2. 本文结论如何影响 10-39 生产对象规范待对象规范稳定后确定；
3. 本文结论如何影响 40-69 行动模型规范待行动模型规范稳定后确定；
4. 本文结论如何影响 04 Trae Solo 环境机制规范（Skill / Agent 设计）待机制规范稳定后确定。
