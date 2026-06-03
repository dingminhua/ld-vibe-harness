# LD Vibe Harness 对 gstack 的借鉴评估

> 创建日期：2026-05-30
> 定位：LD Vibe Harness 对 gstack 的项目级借鉴评估
> 调研边界：不直接构成强制规则
> 执行效力：无，结论需进入 00-79 正式规范区间或 ADR 后才成为稳定规则
> 上位依据：`specs/00-LD-Vibe-Harness理念与纲要.md`
> 相关规范：`specs/02-LDVH术语规范.md`、`specs/01-LDVH目录说明.md`、`specs/10-事实源边界与承载规范.md`

---

## 1. 本文解决的问题

本文评估 LD Vibe Harness 应如何借鉴 gstack 的设计思想，同时保持自身"面向 Vibe Coding 的工程驾驭框架"的独特定位。本文是内部调研，不直接构成强制规则；调研结论进入 00-79 正式规范区间或 ADR 后才成为稳定规则。

---

## 2. 结论

gstack 对 LD Vibe Harness 有较高参考价值，但 LD Vibe Harness 不应复制 gstack 的产品形态。

更准确的判断是：

> gstack 是面向 Claude Code 的 AI 工程工作流与技能工厂；LD Vibe Harness 是面向 Vibe Coding + Trae Solo 场景的工程驾驭框架，围绕事实源、事实模型和行动模型设计。

LD Vibe Harness 最值得借鉴 gstack 的不是具体命令数量，也不是浏览器守护进程本身，而是以下能力组合：

1. 把 AI 协作拆成明确阶段和专业角色
2. 把高频协作流程固化为可复用 Skill
3. 把质量、QA、安全、发布、复盘纳入同一条工程链路
4. 坚持用户主权：AI 建议，人类决策
5. 用工具降低执行摩擦，但不让工具取代事实源和治理判断

---

## 3. 项目概览（基于真实仓库阅读）

通过阅读 garrytan/gstack 仓库，gstack 是一个围绕 Claude Code 构建的 AI 工程工作流项目。它通过一组 Markdown Skill、CLI 工具、浏览器能力和本地状态机制，把单个 AI 编程助手扩展成类似"虚拟工程团队"的协作体系。

从仓库结构观察，gstack 的核心组成包括：

| 模块 | 作用 | 真实仓库中的体现 |
|---|---|---|
| Skill 集合 | 将 CEO、工程、设计、QA、安全、发布、复盘等角色固化为可调用工作流 | `autoplan/`, `review/`, `qa/`, `context-save/`, `context-restore/`, `spec/` 等目录，每个包含 SKILL.md 和模板 |
| 浏览器能力 | 通过持久化 Chromium 守护进程支持真实页面 QA、截图、交互和验证 | `browse/` 目录，包含 src、test，以及 bin 工具（chrome-cdp、find-browse、remote-slug） |
| 计划评审流程 | 在编码前进行产品、工程、设计、DX 等多视角评审 | `plan-ceo-review/`, `plan-eng-review/`, `plan-design-review/`, `plan-devex-review/` |
| 实现后门禁 | 通过 review、qa、cso、ship、land-and-deploy 等流程提升交付质量 | `ship/`, `land-and-deploy/`, `review/`, `cso/` |
| 记忆与复盘 | 通过 context-save、context-restore、learn、retro 等能力沉淀上下文和经验 | `context-save/`, `context-restore/`, `learn/`, `retro/` |
| 安全约束 | 通过 careful、freeze、guard、权限隔离、隧道隔离等方式降低误操作风险 | `careful/`, `freeze/`, `guard/`, `browse/src/` 中的安全相关逻辑 |
| 工具与 CLI | 一组 CLI 工具用于同步状态、配置、脑记忆、归档等 | `bin/` 目录下包含 `gstack-brain-sync`, `gstack-config`, `gstack-analytics`, `gstack-question-preference` 等 |
| 规范与约定 | 一套完整的 AskUserQuestion 格式、ELI10 解释风格、风险决策模板 | `docs/askuserquestion-split.md`, `docs/explanation-diataxis-in-gstack.md` 等 |

这说明 gstack 的重点不是"任务管理"，而是"让 AI 编程流程可重复、可审查、可提速、可交付"。

从仓库结构和代码阅读中，我们发现 gstack 的一个关键设计选择是：**所有 Skill 都以 Markdown + shell 混合形式编写，Skill 文件本身就是可执行的工作流说明**。

---

## 4. 与 LD Vibe Harness 的关系判断（基于真实仓库观察）

| 维度 | gstack | LD Vibe Harness |
|---|---|---|
| 产品形态 | Claude Code Skill + CLI + 浏览器工具 | 本地规范 + Harness 工具 + 事实模型 + 行动模型 |
| 核心对象 | Skill、Agent 角色、浏览器会话、发布流程、上下文记忆 | Intent、Task、Memo、ADR、Evidence、Change、Pitfall |
| 主要目标 | 把 AI 编码助手扩展成工程团队流水线 | 让 AI 进入项目后知道读什么、做什么、不能做什么、何时停下、如何回写 |
| 数据事实源 | 技能文件、仓库文档、运行状态、上下文存档 | Git 仓库中的 specs、ldvh-base、docs |
| AI 角色 | 直接驱动 AI 工作流（AI 是主要执行者） | AI 是行动模型的执行者，不是工具直接调用的对象 |
| 工具价值 | 降低 AI 工程执行摩擦 | 降低读取、校验、聚合、展示和受控写入事实源的成本 |
| 风险边界 | 浏览器、远程配对、安全令牌、自动发布 | 事实源漂移、状态流转违规、门禁未触发、证据未回写 |
| 本地状态管理 | ~/.gstack/ 目录，包含配置、学习记录、问题偏好、会话状态等 | 目前事实源全在 Git 仓库中，无本地隐藏状态 |

LD Vibe Harness 不应成为 gstack clone。LD Vibe Harness 可以吸收 gstack 的工程化协作思想，但必须保持自身边界：

```text
LD Vibe Harness 不直接调用 AI
LD Vibe Harness 不成为事实源（事实源始终是 Git）
LD Vibe Harness 不替代 Human Gate
LD Vibe Harness 的工具只做聚合视图和受控编辑入口
```

### 4.1 关于 LDVH 在早期阶段"是否可以借鉴 gstack"的判断

结合对 gstack 仓库的阅读，我们重新评估：

> **对于早期 LDVH（当前阶段），非常适合借鉴 gstack 的产品形态设计思路；但不应复制 gstack 的具体实现方式（如 Claude Code Skill 结构、浏览器守护进程、本地隐藏状态目录等）。**

理由是：
1. LDVH 当前处于从"规范集合"向"可操作框架"过渡的阶段；
2. gstack 提供了一个完整的例子：如何把复杂的工程治理包装成连续、可调用、低摩擦的交互体验；
3. LDVH 早期的高价值目标不是"是否符合现有设计假设"，而是"能否把现有规范变成实际可运行的治理工作台"；
4. gstack 的结构（入口化 Skill、可执行工作流、显性化 Human Gate、上下文恢复）正好可以启发 LDVH 的早期形态设计；
5. 但 LDVH 的核心优势（Git 文件事实源、事实模型、行动模型）必须保留，不能被本地隐藏状态或临时上下文替代。

---

## 5. 最值得借鉴的设计思想（基于真实仓库阅读）

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

### 5.2 AskUserQuestion 格式的启发

gstack 对 Human Gate 有非常具体的格式要求，这点对 LDVH 极有启发：

```markdown
D<N> — <one-line question title>
Project/branch/task: <1 short grounding sentence>
ELI10: <plain English a 16-year-old could follow, 2-4 sentences, name the stakes>
Stakes if we pick wrong: <one sentence on what breaks, what user sees, what's lost>
Recommendation: <choice> because <one-line reason>
Completeness: A=X/10, B=Y/10 (or: Note: options differ in kind, not coverage — no completeness score)
Pros / cons:
A) <option label> (recommended)
  ✅ <pro — concrete, observable, ≥40 chars>
  ❌ <con — honest, ≥40 chars>
B) <option label>
  ✅ <pro>
  ❌ <con>
Net: <one-line synthesis of what you're actually trading off>
```

关键设计亮点：
- **ELI10**：每个决策都必须用普通人能懂的语言解释（Explain Like I'm 10）；
- **Stakes**：明确指出选错的后果；
- **Completeness Score**：评估选项在完整性上的差异；
- **Pros/Cons**：每个选项都至少有 2 个正面点和 1 个负面点，且至少 40 字符；
- **Net synthesis**：总结实际权衡关系；
- **Hard Stop**：破坏性操作要求必须是 "✅ No cons — this is a hard-stop choice"。

LDVH 可以直接借鉴这种格式，把 Human Gate 从简单的"停下来"变成结构化的决策卡片。

### 5.3 角色化 Skill 矩阵（轻量版）

gstack 的一个核心优势是角色非常清晰：CEO reviewer、eng manager、designer、QA lead、security officer、release engineer 等。每个 Skill 不只是提示词，而是一个稳定工作流。

但基于真实仓库阅读，gstack 实际采用的是"先 Skill 后 Agent"的路径：

```text
先有稳定的 Skill 工作流 → 确有需要时再做成 Agent
```

LD Vibe Harness 可以借鉴角色矩阵，但不宜一开始创建大量 Agent。更适合的路径是：

```text
先沉淀角色视角（检查清单/格式/提示词）→ 再沉淀 Skill（可调用工作流）→ 最后在确有隔离需求时创建 Agent
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

### 5.4 "计划先行"的门禁体验

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

### 5.5 "真实环境 QA"意识

gstack 很重视浏览器 QA，强调真实 Chromium、真实点击、截图、响应式、表单、上传、弹窗和部署后验证。

LD Vibe Harness 目前不是浏览器自动化工具，但可以借鉴它的 QA 证据思维：任务关闭前必须能回答"在哪里验证、怎么验证、证据是什么"。

建议 LD Vibe Harness 在事实模型规范中强化：

| 字段或视图 | 借鉴点 |
|---|---|
| acceptance | 用可观察行为描述完成标准 |
| verification | 记录实际验证命令、页面、截图或检查方式 |
| closure_evidence | 关闭时必须填入证据 |
| related_audit | 审计发现关闭要能回链到验证结果 |

LD Vibe Harness 不必内置 gstack 式浏览器守护进程，但可以让任务天然容纳来自人工、Trae、浏览器工具或其他 QA 工具的验证证据。

### 5.6 安全与破坏性操作边界

gstack 的 careful、freeze、guard、隧道双监听、安全令牌、cookie 处理等设计体现了清晰的风险分层。

从 gstack 代码中观察到，风险分层通常包括：
- **Hard Stop**：必须停止的操作（如 rm -rf, DROP TABLE 等）；
- **Careful**：需要确认的高风险操作；
- **Freeze**：限制编辑范围的操作；
- **Guard**：同时激活 careful + freeze。

LD Vibe Harness 可借鉴为门禁规则：

| 风险类型 | LD Vibe Harness 中的建议处理 |
|---|---|
| 删除文件、重排文档编号、变更事实源 | 触发 Human Gate |
| 新增依赖、引入 GUI 框架、修改工具架构 | 触发 Human Gate |
| 跨项目影响、接口契约变化 | 触发跨项目评估 |
| 审计发现自动转任务 | 不能无脑任务化，必须先分类 |
| 修改规则或规范 | 必须同步创建 Change 和更新索引 |

LD Vibe Harness 已有硬约束。gstack 的启发是：门禁不应只写在文档里，也应在 Harness 工具和 AI 行动模型中可见。

### 5.7 用户主权原则

gstack 的 ETHOS 强调"AI models recommend, users decide"。这与 LD Vibe Harness 的 Human Gate 原则高度一致。

从 gstack 仓库观察到，这条原则不是口号，而是具体的设计约束：
- 没有 AskUserQuestion 的 Skill 不能执行关键决策；
- 5 个以上选项时必须使用分拆问题链（不能直接做选择）；
- 即使两个 AI 模型都同意，也不能自动执行（只是更强的推荐）。

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

## 6. 对 LD Vibe Harness 的启发

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

## 7. 产品借鉴意义重新评估

重新评估后，gstack 对 LD Vibe Harness 的产品借鉴意义不应停留在“是否也做一组 Skill 或命令”，而应上升到“如何把治理框架转化为用户能直接感知的产品体验”。

LD Vibe Harness 当前的核心资产是事实源边界、事实模型、行动模型、Human Gate 和工具分层；这些资产如果只停留在规范文本中，用户感知会接近“规则很多”。gstack 的产品启发在于：同样是复杂工程链路，可以通过阶段入口、角色视角、下一步动作、门禁反馈和上下文恢复，转化为用户能够连续操作的工作台体验。

### 7.1 产品定位上的借鉴

| gstack 产品特征 | 对 LD Vibe Harness 的启发 | LDVH 应采用的产品表达 |
|---|---|---|
| 把 AI 编程助手包装成工程团队流水线 | 用户需要的不是对象字段，而是“现在该谁判断、该做什么、做到哪一步” | 将事实模型和行动模型呈现为治理驾驶舱、待决策队列、待验证队列和上下文入口 |
| Skill/命令有清晰场景名 | 产品入口应使用人的任务语言，而不是内部模型语言 | 用“开始审计”“准备上下文”“关闭任务”“请求决策”“复盘变更”等操作表达模型动作 |
| 计划、评审、QA、安全、发布形成连续链路 | LDVH 可以把分散规范转成端到端闭环 | 围绕 Intent → Task → Evidence → Change/Pitfall/ADR 展示闭环进度 |
| 真实 QA 与截图证据强化完成感 | 关闭动作应让用户感知证据是否充分 | 在任务关闭、Review、审计闭环中突出 verification 和 closure_evidence |
| 上下文保存/恢复降低跨会话成本 | LDVH 的事实源优势可转化为更强的上下文恢复体验 | 提供面向 AI 和人的“当前任务上下文包”和“推荐阅读包” |

产品定位上，LDVH 不宜宣传为“更多 AI 自动化能力”，而应表达为：

```text
让人和 AI 在同一个事实源治理工作台中推进需求、任务、证据、决策和复盘。
```

这比“任务管理工具”“规范仓库”“AI 命令集合”都更贴近 LDVH 的独特价值。

### 7.2 产品形态上的借鉴

gstack 的强产品感来自“可调用入口”而不是“文档解释”。LDVH 可以借鉴这种入口化思路，但入口不应复制 slash command，而应落到 Web 信息同步层和 Tools 辅助层的分工上。

| 产品入口 | 用户看到的问题 | 背后对应的 LDVH 能力 |
|---|---|---|
| 今日推进 | 今天最应该推进哪些任务，为什么是它们 | Task 状态、依赖、阻塞、Review Needed、Decision Needed 聚合 |
| 决策等待 | 哪些地方必须由人确认，选项和影响是什么 | Human Gate、ADR 候选、关键状态流转、风险提示 |
| 关闭检查 | 这个任务为什么还不能关闭 | acceptance、verification、closure_evidence、Change/Pitfall/ADR 关联检查 |
| 上下文包 | 继续这个任务前应该读什么 | source_doc、related ADR、相关规范片段、依赖对象聚合 |
| 审计闭环 | 审计发现是否被分类、处理和验证 | Audit 结果、Task 分流、关闭证据和复盘对象回链 |
| 复盘沉淀 | 哪些经验应该变成 Pitfall 或 ADR | Change、失败记录、反复出现的问题、决策稳定性判断 |

这些入口的共同点是：用户先看到“要做的事”和“为什么”，再进入对象字段或事实源编辑。这样可以把 LDVH 的严谨性转化为低摩擦体验，而不是让用户直接面对对象规范复杂度。

### 7.3 产品优先级上的借鉴

重新评估后，LDVH 更应优先产品化以下能力：

1. **状态解释**：不仅展示状态，还解释为什么处于该状态、允许流转到哪里、缺少什么证据；
2. **门禁显性化**：Human Gate 不只是规则要求，而是产品中的待确认卡片、影响说明和可选动作；
3. **上下文一键化**：把 AI 继续工作所需的 specs、docs、ADR、对象实例和检查要求聚合成可复制上下文；
4. **关闭仪式感**：关闭任务时强制呈现验收标准、验证结果、证据和是否需要 Change/Pitfall/ADR 的判断；
5. **审计可闭环**：审计发现不能只显示问题列表，而要显示分类、处理路径、责任对象、关闭证据和遗留风险；
6. **角色视角轻量化**：先用产品视角和检查清单承载“意图价值、工程规范、体验、QA、安全、发布”六类审视，不急于创建大量 Agent；
7. **规范到操作的翻译**：每条关键规范应尽量在产品中表现为提示、检查、入口、阻止或证据要求。

这些优先级说明：LDVH 的下一阶段产品价值，不在于把 gstack 的角色和命令搬过来，而在于把既有 LDVH 规范变成更容易被人和 AI 执行的交互系统。

### 7.4 不应借鉴的产品方向

| 不应借鉴 | 原因 |
|---|---|
| 把产品主入口设计成命令大全 | LDVH 的用户痛点是事实源治理和闭环推进，不是记住更多命令 |
| 把角色 Skill 作为早期产品卖点 | 角色过早产品化会掩盖事实源、证据和门禁这些基础能力 |
| 把浏览器自动化作为核心差异 | 真实 QA 很重要，但 LDVH 当前更需要先接收和治理证据，而不是自建自动化执行器 |
| 把自动发布、自动提交、自动合并做成默认能力 | 这会削弱 Human Gate 和用户主权，也容易越过 LDVH 工具边界 |
| 把工具输出包装成事实源 | 产品体验再顺滑，也不能让 UI 状态、缓存或派生视图替代 Git 文件事实源 |

### 7.5 重新评估结论

gstack 对 LDVH 的最大产品借鉴意义是：它证明复杂 AI 工程治理可以被包装成连续、可调用、低摩擦的产品体验。

LDVH 应吸收这种产品化能力，但采用自己的事实源治理路径：

```text
gstack 的产品核心：把 AI 工程团队化。
LDVH 的产品核心：把事实源治理、Human Gate、证据闭环和 AI 上下文协作工作台化。
```

因此，后续 LDVH 产品设计应优先围绕“今日推进、决策等待、关闭检查、上下文包、审计闭环、复盘沉淀”形成工作台，而不是优先复制 gstack 的命令体系、浏览器守护进程或大量角色 Skill。

---

## 8. 可落地建议（基于真实 gstack 仓库启发）

### 8.1 短期建议（现在可以做）

| 建议 | 说明 | 借鉴点 |
|---|---|---|
| 在任务详情增加下一步提示 | 根据状态机提示允许流转、必填证据和 Human Gate | gstack 的 Skill 中每步都有明确下一步 |
| 设计 AI 上下文复制入口 | 从 Task / Intent / Audit 聚合推荐阅读材料 | gstack 的 context-save/context-restore |
| 强化 Review Needed 视图 | 聚合所有待验证、缺证据、待关闭任务 | gstack 的 review/qa 视图聚合 |
| 审计发现分类时显示理由 | 避免"自动任务化"黑盒 | gstack 的明确分类理由 |
| 将 closure_evidence 做成关闭门槛 | 关闭不是改状态，而是提交证据 | gstack 的 qa/ship 证据要求 |
| 实现 Human Gate 结构化卡片 | 使用类似 gstack 的 AskUserQuestion 格式（ELI10、Stakes、Completeness、Pros/Cons） | gstack 的决策卡片设计 |
| 建立"今日推进"入口 | 展示当前最应该推进的任务，说明为什么 | gstack 的 autoplan 入口设计 |

### 8.2 中期建议（接下来可以做）

| 建议 | 说明 | 借鉴点 |
|---|---|---|
| 建立 LD Vibe Harness Skill 矩阵 | 围绕意图审查、任务关闭、审计分类、上下文生成沉淀 Skill | gstack 的 Skill 组织结构 |
| 增加决策等待视图 | 聚合 Decision Needed、ADR 候选、Human Gate 等待项 | gstack 的 guard/careful 设计 |
| 增加关闭检查入口 | 关闭前显式检查 acceptance、verification、closure_evidence、Change/Pitfall/ADR | gstack 的 ship/land-and-deploy 检查 |
| 增加复盘视图 | 从 Change、Pitfall、关闭任务中形成周期性回顾 | gstack 的 retro 能力 |
| 增加治理健康分 | 用静态检查展示 specs、ldvh-base、docs 的健康状态 | gstack 的 review 评分思路 |

### 8.3 暂不建议（当前阶段不宜做）

| 不建议项 | 原因 |
|---|---|
| 复制 gstack 的大量 slash commands | LD Vibe Harness 的主要对象不同，照搬会制造复杂度 |
| 让 LD Vibe Harness 直接调用 AI | 违反当前工具边界，且会模糊事实源与执行者 |
| 内置浏览器自动化守护进程 | 当前 LD Vibe Harness 不是 QA 自动化工具，可先接收外部证据 |
| 一次性创建大量 LD Vibe Harness Agent | Agent 有上下文和权限成本，应先用 Skill 验证流程稳定性 |
| 自动发布、自动提交、自动合并 | LD Vibe Harness 是治理框架，不是发布机器人 |
| 引入 ~/.ldvh/ 本地隐藏状态目录 | LDVH 的事实源应该始终在 Git 仓库中，避免本地状态与事实源不一致 |

---

## 9. 风险评估

| 风险 | 表现 | 控制方式 |
|---|---|---|
| 过度 gstack 化 | LD Vibe Harness 变成 AI 命令集合，失去事实源治理定位 | 坚持 specs/ldvh-base//docs 为事实源 |
| Skill 泛滥 | 每个想法都做 Skill，维护成本升高 | 只有重复、多步骤、稳定输出的流程才做 Skill |
| Agent 泛滥 | 角色很多但没有独立上下文必要 | 按 Trae Solo 环境机制规范中的 Agent 创建门槛执行 |
| 自动化越权 | 工具直接替用户做关键决策 | Human Gate 必须可见、可审计 |
| 证据形式化 | closure_evidence 变成空字段 | 关闭时校验非空、可追溯、能说明验证结果 |
| 外部项目误读 | 把 gstack 的 Claude Code 实现当成 Trae 事实 | Trae 落地以 Trae Solo 环境机制规范为准 |

---

## 10. 评估结论（基于真实仓库阅读）

基于对 garrytan/gstack 真实仓库的阅读，我们重新评估后得出：

> 对于早期 LDVH（当前阶段），非常适合借鉴 gstack 的产品形态设计思路；但不应复制 gstack 的具体实现方式。

gstack 对 LD Vibe Harness 的核心启发可以浓缩为一句话：

> 把 AI 协作从"临场聊天"升级为"有角色、有阶段、有证据、有门禁、有复盘的工程系统"。

LD Vibe Harness 应吸收这一思想，但走自己的路径：

```text
gstack：让 AI 更像一支工程团队（通过 Claude Code Skill + CLI + 浏览器工具）
LD Vibe Harness：让项目事实源和 AI 协作治理更像一个可操作的驾驭工作台（通过 specs/ldvh-base/docs + 聚合工具 + 事实模型）
```

因此，LD Vibe Harness 后续最优先的借鉴方向不是增加更多 AI 能力，而是把现有规范产品化：

1. 状态流转可见（且解释为什么在该状态）
2. 下一步动作可见（结构化提示）
3. 关闭证据可见（强制验收）
4. Human Gate 可见（用 ELI10 + Stakes + Completeness + Pros/Cons 的决策卡片）
5. AI 上下文可复制（一键式上下文包）
6. 审计闭环可追踪（从发现到处理到验证到复盘）
7. 意图全貌可理解（从目标到依赖到证据到复盘）

当这些能力稳定后，再逐步把高频治理流程沉淀为 LD Vibe Harness Skill；只有在独立上下文、权限隔离、并行委派或调度成为真实需求时，再考虑 LD Vibe Harness Agent。

---

## 11. 待补齐事项

1. 本文结论如何进入 12 系列工具规范待工具规范稳定后确定；
2. 本文结论如何影响 20-49 事实模型规范待对象规范稳定后确定；
3. 本文结论如何影响 50-79 行动模型规范待行动模型规范稳定后确定；
4. 本文结论如何影响 11 系列 Trae Solo 环境机制规范（Skill / Agent 设计）待机制规范稳定后确定；
5. Human Gate 结构化卡片设计（借鉴 gstack 的 AskUserQuestion 格式）待 11 系列规范稳定后确定。
