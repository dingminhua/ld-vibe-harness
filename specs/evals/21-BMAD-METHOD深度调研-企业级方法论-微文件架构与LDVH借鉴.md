# BMAD-METHOD 深度调研：企业级方法论、微文件架构与 LDVH 借鉴

> 创建日期：2026-06-05
> 定位：对 BMAD-METHOD 项目的代码级深度调研，覆盖方法论阶段、Agent 体系、微文件架构、质量门禁、企业级特性及对 LDVH 的借鉴价值
> 调研边界：不直接构成强制规则；结论进入正式规范或 ADR 后才成为稳定执行依据
> 代码调研来源：`/Users/dmh2002/trae_projects/BMAD-METHOD`（完整代码库）
> 上位参考：`specs/evals/11-LDVH-Gstack-Trae融合产品方向共识.md`

---

## 1. 本文解决的问题

本文沉淀对 BMAD-METHOD 项目的深度调研结论，作为 LDVH 在微文件架构、Agent 体系、质量门禁、定制化体系和规模自适应方面的决策参考：

1. BMAD 方法论的完整阶段与流程——理解四阶段生命周期的设计
2. Agent/角色体系——理解 6 个具名 Agent 的职责和交互模式
3. 微文件架构——理解步骤文件即规范执行器的设计
4. 人工确认环节——理解 BMAD 的 Gate 分布和设计逻辑
5. 质量门禁与验证——理解七维度评审和 DoD 验证
6. 企业级特性——理解定制化、Headless 模式、外部集成
7. 对 LDVH 的可借鉴之处——理解哪些机制可直接吸收、哪些需要适配

---

## 2. 项目概述与定位

### 2.1 基本信息

- **名称**：BMAD（Build More Architect Dreams）
- **版本**：V6
- **定位**：AI 驱动的敏捷开发全生命周期框架
- **核心载体**：Skill 包 + Agent 定义 + 微文件步骤 + 定制化 TOML
- **协议**：开源

### 2.2 与 Gstack 和 Superpowers 的定位差异

| 维度 | BMAD | Gstack | Superpowers |
|------|------|--------|-------------|
| 核心隐喻 | 企业级方法论 | 虚拟团队 | 工程纪律 |
| 第一价值 | 全生命周期治理 | 速度 | 正确性 |
| 覆盖范围 | 分析→规划→方案→实施 | Think→Plan→Build→Ship→Reflect | Brainstorm→Plan→Build→Review→Verify |
| Agent 设计 | 具名人格 + Party Mode | 角色化 Skill | 匿名子代理 |
| 工作流架构 | 微文件步骤式 | 自由对话 | Skill 编排 |
| 定制化 | 三层 TOML 覆盖 | 本地 marker 文件 | 无 |
| 企业集成 | external_sources + external_handoffs | 无 | 无 |
| 规模自适应 | Stakes 校准（hobby/internal/launch） | 无 | 无 |

---

## 3. 核心方法论与阶段

### 3.1 四阶段生命周期

```
分析（Analysis）→ 规划（Plan）→ 方案设计（Solutioning）→ 实施（Implementation）
```

每个阶段有明确的输入、输出、Agent 职责和质量门禁。

### 3.2 阶段 1：分析（Analysis）

| Skill | 目标 | 关键产出 |
|-------|------|---------|
| bmad-brainstorming | 创意发散 | 创意列表、决策记录 |
| bmad-product-brief | 创建/更新/验证产品简报 | Product Brief 文档 |
| bmad-prfaq | Amazon Working Backwards PRFAQ 挑战 | PRFAQ 文档 |
| bmad-document-project | 棕地项目文档化 | 项目文档 |
| bmad-market-research | 市场研究 | 研究报告 |
| bmad-domain-research | 领域研究 | 研究报告 |
| bmad-technical-research | 技术研究 | 研究报告 |

**bmad-product-brief 工作流**：

1. 激活 → 意图检测（Create/Update/Validate）
2. Discovery（Brain dump + Stakes 校准 + 工作模式选择 Fast/Coaching）
3. 逐步起草
4. Finalize（决策日志审计 + 文档标准 + 外部交接）

**bmad-prfaq 五阶段**：

1. Ignition（原始概念 + 客户优先）
2. Press Release（迭代起草）
3. Customer FAQ（魔鬼代言人）
4. Internal FAQ（利益相关者质疑）
5. Verdict（综合评估）

### 3.3 阶段 2：规划（Plan Workflows）

| Skill | 目标 | 关键产出 |
|-------|------|---------|
| bmad-prd | 创建/更新/验证 PRD | PRD 文档 |
| bmad-ux | 创建 UX 设计 | UX 设计文档 |

**bmad-prd 工作流**：

1. 激活 → 意图检测 → Discovery（Brain dump → Stakes 校准 → 工作模式 + 入口选择）
2. 逐步起草
3. Reviewer Gate（子 Agent 评审）
4. Finalize（8 步：决策日志审计 → 输入对账 → 评审通过 → 分诊开放项 → 润色 → 外部交接 → 关闭 status:final → on_complete）

**PRD 入口选择**：

- Vision+Features：从愿景和功能列表出发
- Journey-led：从用户旅程出发

### 3.4 阶段 3：方案设计（Solutioning）

| Skill | 目标 | 关键产出 |
|-------|------|---------|
| bmad-create-architecture | 创建架构决策文档 | Architecture Decision 文档 |
| bmad-create-epics-and-stories | 将 PRD+架构拆解为 Epic 和 Story | Epic 文件 + Story 文件 |
| bmad-check-implementation-readiness | 验证 PRD/UX/架构/Epics 完整性和对齐 | Implementation Readiness Report |
| bmad-generate-project-context | 生成 AI 规则文件 | project-context.md |

**bmad-create-architecture 微文件步骤**：

step-01-init（发现输入文档，**PRD 为必需**）→ step-02-context → ... 逐步构建，frontmatter 追踪 stepsCompleted。

### 3.5 阶段 4：实施（Implementation）

| Skill | 目标 | 关键产出 |
|-------|------|---------|
| bmad-sprint-planning | 从 Epics 生成 sprint-status.yaml | Sprint Status YAML |
| bmad-dev-story | 执行 Story 实现 | 实现代码 + 测试 |
| bmad-quick-dev | 快速实现任意意图 | 实现代码 |
| bmad-code-review | 对抗性代码审查 | 审查报告 |
| bmad-retrospective | Epic 回顾 | 回顾文档 |
| bmad-checkpoint-preview | 人工审查变更 | 审查确认 |

**bmad-dev-story 10 步 XML 工作流**：

1. 发现 Story → 2. 加载上下文 → 3. 检测 Review 续接 → 4. 标记 in-progress → 5. Red-Green-Refactor 循环 → 6. 编写测试 → 7. 运行验证 → 8. 标记完成 → 9. Story 完成（DoD 验证）→ 10. 完成沟通

---

## 4. Agent/角色体系

### 4.1 六个核心 Agent

| Agent | 名字 | 图标 | 职责 | 触发器 |
|-------|------|------|------|--------|
| Business Analyst | Mary | 📊 | Porter 战略严谨性 + Minto 金字塔原理 | BP, MR, DR, TR, CB, WB, DP |
| Product Manager | John | 📋 | Jobs-to-be-Done 驱动 | PRD, CE, IR, CC |
| System Architect | Winston | 🏗️ | 偏好无聊技术保稳定性 | CA, IR |
| Senior Software Engineer | Amelia | 💻 | 测试优先纪律（Red-Green-Refactor） | DS, QD, QA, CR, SP, CS, ER, IN |
| UX Designer | Sally | 🎨 | 同理心与边缘案例严谨性平衡 | CU |
| Technical Writer | Paige | 📚 | CommonMark/DITA/OpenAPI 大师 | DP, WD, MG, VD, EC |

### 4.2 Agent 激活协议

每个 Agent 遵循统一激活序列：

1. 解析定制化（`resolve_customization.py`）
2. 执行前置步骤（`activation_steps_prepend`）
3. 采纳人格（角色、身份、沟通风格、原则）
4. 加载持久事实（`persistent_facts`）
5. 加载配置（config.yaml）
6. 问候用户（用 `communication_language` + 图标前缀）
7. 执行后置步骤（`activation_steps_append`）
8. 调度或展示菜单

### 4.3 Party Mode

多 Agent 人格可在一个会话中协作讨论，所有 Agent 对话使用 `"Name (Role): dialogue"` 格式。

### 4.4 persistent_facts 机制

三种加载方式：

- `file:` 前缀 — 加载文件内容
- `skill:` 前缀 — 调用 Skill
- 纯文本 — 直接作为事实

---

## 5. 微文件架构

### 5.1 核心设计

BMAD 的所有 Skill 统一采用**微文件架构（Micro-file Architecture）**：

- **每个步骤是自包含文件**，嵌入规则
- **即时加载**：只加载当前步骤文件
- **顺序强制**：不得跳步或优化
- **状态追踪**：frontmatter `stepsCompleted` 数组
- **追加式构建**：文档通过追加内容构建

### 5.2 关键规则（无例外）

1. 不得同时加载多步骤文件
2. 必须完整读取步骤文件
3. 不得跳步
4. 必须在菜单处等待用户输入

### 5.3 frontmatter 状态追踪

```yaml
stepsCompleted: [step-01-init, step-02-context]
status: draft
inputDocuments: [prd, ux]
```

---

## 6. 人工确认环节完整清单

### 6.1 全局级

| 位置 | 类型 | 描述 |
|------|------|------|
| Skill 激活 | 确认 | 激活步骤 prepend/append 非空时，必须确认每项已按序执行 |
| 步骤菜单 | 等待输入 | 每个步骤文件有菜单时必须停止等待用户选择 `[C] Continue` |
| Headless 模式 | 豁免 | `--headless` / `-H` 标志下不询问，但意图模糊时 halt 并返回 blocked JSON |

### 6.2 阶段 1：分析

| Skill | Gate 点 | 描述 |
|-------|---------|------|
| product-brief | Discovery 工作模式选择 | Fast path 或 Coaching path |
| product-brief | Finalize 决策日志审计 | 用户确认每条决策的去向 |
| product-brief | 连续性 | 发现未完成草稿时，询问是否恢复 |
| prfaq | 每阶段 | 阶段间路由需用户确认 |
| brainstorming | Stance 选择 | Facilitator / Creative Partner / Ideate for me |

### 6.3 阶段 2：规划

| Skill | Gate 点 | 描述 |
|-------|---------|------|
| prd | Discovery 工作模式 | Fast path / Coaching path + 入口选择 |
| prd | Reviewer Gate | 用户选择 all/subset/skip 评审 |
| prd | Finalize 8 步 | 每步需用户参与，特别是决策日志审计和分诊开放项 |
| prd | 恢复检测 | 发现未完成 PRD 时询问是否恢复 |

### 6.4 阶段 3：方案设计

| Skill | Gate 点 | 描述 |
|-------|---------|------|
| create-architecture | 输入文档确认 | 发现文档后与用户确认 |
| create-architecture | 每步骤 | `[C] Continue` 确认 |
| create-architecture | PRD 必需 | 无 PRD 时不得继续 |
| create-epics-and-stories | 前置条件验证 | 需确认 PRD 和架构存在 |
| check-implementation-readiness | 文档发现 | 重复文档需用户解决 |

### 6.5 阶段 4：实施

| Skill | Gate 点 | 描述 |
|-------|---------|------|
| dev-story | Story 发现 | 无 ready-for-dev Story 时提供选项菜单 |
| dev-story | HALT 条件 | 新依赖需用户批准、3 次连续实现失败、缺少配置 |
| dev-story | Step 10 完成沟通 | 询问用户是否需要解释 |
| quick-dev | 检查点 | 步骤文件中指定的人工检查点 |
| code-review | 审查结果 | 用户决定 autofix/discuss/defer/ignore |
| retrospective | Epic 确认 | 检测到的 Epic 需用户确认 |
| retrospective | 行动计划批准 | 用户批准完整行动计划 |
| checkpoint-preview | 全程 | 人工审查变更，逐步引导 |

---

## 7. 文档/产物模板体系

### 7.1 核心模板

| 模板 | 必填字段/结构 |
|------|-------------|
| **Product Brief** | Executive Summary, The Problem, The Solution, What Makes This Different, Who This Serves, Success Criteria, Scope, Vision。YAML frontmatter: title, status, created, updated |
| **PRD** | Essential Spine: Document Purpose, Vision, Target User (JTBD + Non-Users + Key User Journeys), Glossary, Features (FR 全局编号 + testable consequences), Non-Goals, MVP Scope, Success Metrics (含 Counter-metrics), Open Questions, Assumptions Index。Adapt-In Menu: Cross-cutting quality, Consumer, Enterprise, Regulated, Developer products, Embedded/hardware, Small-scope。YAML frontmatter: title, status, created, updated |
| **PRFAQ** | Headline, Subheadline, Opening paragraph, Problem paragraph, Solution paragraph, Leader quote, How It Works, User quote, Getting Started, Customer FAQ, Internal FAQ, The Verdict。YAML frontmatter: title, status, created, updated, stage, inputs |
| **Architecture Decision** | 追加式构建。YAML frontmatter: stepsCompleted, inputDocuments, workflowType, project_name, user_name, date |
| **Implementation Readiness Report** | Date, Project |
| **Sprint Status** | YAML: generated, last_updated, project, project_key, tracking_system, story_location, development_status |

### 7.2 辅助文件

| 文件 | 角色 | 生命周期 |
|------|------|---------|
| .decision-log.md | 规范记忆和审计轨迹 | 随对话展开实时记录每个决策、变更和覆盖 |
| addendum.md | 保存属于下游文档的深度内容 | 对话中用户贡献时即时捕获 |
| project-context.md | AI 规则和模式精简文件 | 由 generate-project-context 生成 |
| sprint-status.yaml | Sprint 追踪 | 由 sprint-planning 生成，dev-story/retrospective 更新 |
| Story 文件 | 实现规范 | YAML frontmatter (baseline_commit), Story, AC, Tasks/Subtasks, Dev Notes, Dev Agent Record, File List, Change Log, Status |
| review-{slug}.md | 评审发现 | Reviewer Gate 子 Agent 写入 |
| reconcile-{slug}.md | 输入对账 | Finalize 子 Agent 写入 |
| memlog | 头脑风暴会话记忆 | 通过 memlog.py 管理，原子写入 |

---

## 8. 质量门禁与验证机制

### 8.1 PRD 七维度评审模型

| 维度 | 评判标准 | 级别 |
|------|---------|------|
| Decision-readiness | 决策者能否据此行动？权衡是否诚实？ | strong/adequate/thin/broken |
| Substance over theater | 内容是实质还是摆设？识别人设剧场/创新剧场/NFR 剧场/愿景剧场 | 同上 |
| Strategic coherence | PRD 是否有论点？Feature 是否服务于统一弧线？ | 同上 |
| Done-ness clarity | 工程师能否知道每个 FR 的"完成"定义？每 FR 至少一个可测试后果 | 同上 |
| Scope honesty | 遗漏是否显式？ASSUMPTION/NON-GOAL/NOTE FOR PM 标签使用 | 同上 |
| Downstream usability | UX/架构/Story 创建能否干净地提取？Glossary 一致性、ID 连续性 | 同上 |
| Shape fit | PRD 形状是否匹配产品类型？ | 同上 |

### 8.2 Story 完成门禁（Definition of Done）

- 所有 tasks/subtasks 标记 [x]
- 实现满足每个 Acceptance Criterion
- 单元测试/集成测试/E2E 测试按需添加
- 所有测试通过（无回归）
- 代码质量检查通过
- File List 包含每个变更文件
- Dev Agent Record 包含实现笔记
- Change Log 包含变更摘要
- 仅修改了允许的 Story 区域

### 8.3 实现就绪门禁

- PRD、UX、架构、Epics 文档完整且对齐
- Epics 和 Stories 逻辑一致，覆盖所有需求
- 无重复文档冲突
- 无缺失关键文档

### 8.4 Sprint 状态机

```
Epic:  backlog → in-progress → done
Story: backlog → ready-for-dev → in-progress → review → done
Retro: optional ↔ done
```

**关键规则**：状态永不降级；Epic 在首个 Story 创建时自动转为 in-progress。

### 8.5 代码审查门禁

三层并行对抗性审查：

- **Blind Hunter**：盲点发现
- **Edge Case Hunter**：边缘案例
- **Acceptance Auditor**：验收审计

发现按 Critical/High/Medium/Low 分级，用户决定 autofix/discuss/defer/ignore。

### 8.6 通用验证机制

- **Stakes 校准**：hobby/internal/launch 影响 rigor 深度
- **[ASSUMPTION] 标签**：Fast path 中 AI 推断处标记，用户审查时纠正
- **[NOTE FOR PM] 标注**：延迟决策和未解决张力
- **[NON-GOAL for MVP] 标注**：显式排除
- **Counter-metrics**：每个 Success Metric 配对反指标

---

## 9. 企业级特性

### 9.1 三层定制化覆盖

```
{skill-root}/customize.toml           → 默认
{project-root}/_bmad/custom/{skill}.toml    → 团队覆盖
{project-root}/_bmad/custom/{skill}.user.toml → 个人覆盖
```

**合并规则**：标量覆盖、表深度合并、以 code/id 键的表数组替换匹配项并追加新项、其他数组追加。

### 9.2 外部系统集成

- **external_sources**：按需查询的知识库/MCP 工具注册表
- **external_handoffs**：Finalize 时自动路由产物到 Confluence/Notion/Slack/Jira 等
- **MCP 工具**：命名工具不可用时优雅降级

### 9.3 Headless 模式

- 支持 `--headless` / `-H` 标志
- 不询问用户，从提供的上下文自主完成
- 意图模糊时 halt 并返回 blocked JSON
- 结构化输出：status, intent, artifact_paths, open_questions, external_handoffs

### 9.4 Web Bundles

- 将 Skills 打包为 Google Gemini Gems 和 ChatGPT Custom GPTs
- 在 Web LLM 订阅中完成前期规划（节省 IDE token 成本）
- 产物可导入 IDE 继续实施

### 9.5 模块化架构

- **BMM**（核心）、**BMB**（Builder）、**TEA**（测试架构）、**BMGD**（游戏开发）、**CIS**（创意智能）
- 非交互式安装支持 CI/CD
- `--set <module>.<key>=<value>` 覆盖任意配置

### 9.6 多语言支持

- `communication_language`：Agent 对话语言
- `document_output_language`：文档输出语言

### 9.7 用户技能等级

- beginner / intermediate / expert
- 仅影响对话风格，不影响代码更新

---

## 10. 对 LDVH 的可借鉴之处

### 10.1 高度可借鉴

**1. 微文件步骤架构 → LDVH Skill 工作流**

BMAD 的 step-file 模式（自包含步骤文件 + frontmatter 状态追踪 + 顺序强制 + 人工检查点）与 LDVH 的 Skill 执行模式高度同构。LDVH 可借鉴其"步骤文件即规范"的设计，将工作模型规范拆解为可执行的步骤指令。

**2. .decision-log.md 审计轨迹 → LDVH 可审计性**

BMAD 的决策日志是"规范记忆和审计轨迹——每个决策、变更和覆盖实时记录"，这与 LDVH 的 Change 记录要求高度一致。LDVH 可考虑将决策日志作为事实源的标准化组成部分。

**3. frontmatter 状态追踪 → LDVH 状态机**

BMAD 用 YAML frontmatter 的 `status` 和 `stepsCompleted` 追踪文档和工作流状态，与 LDVH 的 YAML 事实源 + 状态机模式一致。BMAD 的 `status: draft → final` 和 Story 的 `backlog → ready-for-dev → in-progress → review → done` 可作为 LDVH Task 状态机的参考。

**4. 三层定制化覆盖 → LDVH 规则优先级**

BMAD 的 `customize.toml → team override → user override` 三层合并与 LDVH 的工作区规则 → 项目规则 → 场景规则层级相似。BMAD 的 `resolve_customization.py` 合并规则（标量覆盖、表深度合并、数组追加）可作为 LDVH 规则优先级的参考实现。

**5. Stakes 校准 → LDVH 规模自适应**

BMAD 根据 hobby/internal/launch 调整 rigor 深度，LDVH 可借鉴此模式让治理力度随项目规模自适应，避免对小项目施加过重的治理负担。

**6. persistent_facts → LDVH 事实源加载**

BMAD 的 `persistent_facts`（file: 前缀加载文件内容、skill: 前缀调用 Skill、纯文本作为事实）是结构化的事实源加载机制，与 LDVH 的"编辑前读取"规则异曲同工。

### 10.2 部分可借鉴

**1. Headless 模式 → LDVH 自动化场景**

BMAD 的 headless JSON 输出格式可作为 LDVH 自动化执行的结构化输出参考，但 LDVH 的 Human Gate 要求更严格，不能简单跳过。

**2. Reviewer Gate → LDVH 质量门禁**

BMAD 的并行子 Agent 评审 + 分级发现 + 用户决策模式可借鉴，但 LDVH 需要将其与状态机更紧密地绑定。

**3. PRD 七维度评审 → LDVH 验证机制**

BMAD 的 judgment-based 评审（非 checklist ticking）值得借鉴，LDVH 可为每个对象类型定义类似的维度化评审模型。

**4. Counter-metrics → LDVH 治理指标**

BMAD 的反指标思想（"不要优化这个指标"）可应用于 LDVH 的治理指标设计，防止过度治理。

**5. external_handoffs → LDVH Git 事实源回写**

BMAD 的外部交接路由可参考，但 LDVH 的核心事实源是 Git，需要将交接逻辑适配为 git commit + push。

### 10.3 需要注意的差异

| 维度 | BMAD | LDVH | 注意事项 |
|------|------|------|---------|
| 事实源 | 文件系统（Markdown + YAML frontmatter） | Git 仓库中的 YAML 文件 | LDVH 的 Git 事实源有版本控制和不可篡改性优势 |
| Human Gate | 交互式确认（菜单选择、对话确认） | 状态机强制的 Human Gate | LDVH 的 Human Gate 是状态机级别的强制 |
| 状态机 | 隐式（frontmatter status + sprint-status.yaml） | 显式（对象规范定义的状态机） | LDVH 的状态机更严格，状态变更必须先于执行动作 |
| 规范层级 | Skill 内嵌规则 + customize.toml | specs/ 规范体系 + 项目规则 + 场景规则 | LDVH 的规范体系更完整和独立 |
| 对象类型 | 文档（Brief/PRD/Architecture/Story 等） | Intent/Task/Memo/Profile/ADR/Change 等 | LDVH 的对象类型更抽象和治理导向 |
| 禁止事项 | 工作流级别（如"不得跳步"） | 规范级别（如"不得绕过状态机"） | LDVH 的禁止事项更具约束力 |

### 10.4 不应照搬的

1. **Agent 人格化**：BMAD 的具名人格（Mary/John/Winston 等）增加 token 消耗且与 LDVH 的治理导向不匹配
2. **微文件步骤的绝对顺序**：LDVH 的 Core Loop 允许阶段间灵活路由，不应强制线性步骤
3. **文件系统作为事实源**：LDVH 的 Git 事实源有版本控制优势，不应退回到纯文件系统
4. **Headless 模式跳过 Human Gate**：LDVH 的 Human Gate 是治理纪律，不能为了自动化而跳过
5. **Party Mode 多人格对话**：增加复杂度和 token 消耗，LDVH 的多角色通过 Skill 分工而非人格切换实现

### 10.5 核心启示

1. **步骤文件即规范执行器**：BMAD 证明了将规范拆解为可执行的步骤指令是可行的，LDVH 可以将工作模型规范中的流程步骤转化为类似的步骤文件，使规范不仅是文档而是可执行指令。

2. **决策日志作为一等公民**：BMAD 将 `.decision-log.md` 定位为"规范记忆和审计轨迹"，这与 LDVH 的可审计性要求天然契合。LDVH 可将 Change 记录提升为与 Task/ADR 同级的一等对象。

3. **定制化合并规则需要显式定义**：BMAD 的标量覆盖/表深度合并/数组追加规则是显式且可预测的，LDVH 在处理项目规则 → 场景规则 → 对象规范的优先级时需要类似的显式合并规则。

4. **Stakes 校准避免过度治理**：BMAD 的 hobby/internal/launch 三级校准是一个实用的模式，LDVH 可以借鉴以避免对小项目施加过重的治理负担。

5. **子 Agent 模式提升效率**：BMAD 大量使用并行子 Agent（评审、研究、提取），LDVH 在实现复杂验证和交叉检查时可借鉴此模式。

---

## 11. 来源

### 代码来源

- `/Users/dmh2002/trae_projects/BMAD-METHOD/README.md`
- `/Users/dmh2002/trae_projects/BMAD-METHOD/docs/reference/agents.md`
- `/Users/dmh2002/trae_projects/BMAD-METHOD/src/bmm-skills/1-analysis/bmad-product-brief/SKILL.md`
- `/Users/dmh2002/trae_projects/BMAD-METHOD/src/bmm-skills/1-analysis/bmad-document-project/SKILL.md`
- `/Users/dmh2002/trae_projects/BMAD-METHOD/src/bmm-skills/1-analysis/bmad-prfaq/SKILL.md`
- `/Users/dmh2002/trae_projects/BMAD-METHOD/src/bmm-skills/2-plan-workflows/bmad-prd/SKILL.md`
- `/Users/dmh2002/trae_projects/BMAD-METHOD/src/bmm-skills/2-plan-workflows/bmad-create-prd/SKILL.md`
- `/Users/dmh2002/trae_projects/BMAD-METHOD/src/bmm-skills/2-plan-workflows/bmad-agent-pm/SKILL.md`
- `/Users/dmh2002/trae_projects/BMAD-METHOD/src/bmm-skills/3-solutioning/bmad-create-architecture/SKILL.md`
- `/Users/dmh2002/trae_projects/BMAD-METHOD/src/bmm-skills/3-solutioning/bmad-create-epics-and-stories/SKILL.md`
- `/Users/dmh2002/trae_projects/BMAD-METHOD/src/bmm-skills/3-solutioning/bmad-check-implementation-readiness/SKILL.md`
- `/Users/dmh2002/trae_projects/BMAD-METHOD/src/bmm-skills/3-solutioning/bmad-generate-project-context/SKILL.md`
- `/Users/dmh2002/trae_projects/BMAD-METHOD/src/bmm-skills/4-implementation/bmad-quick-dev/SKILL.md`
- `/Users/dmh2002/trae_projects/BMAD-METHOD/src/bmm-skills/4-implementation/bmad-code-review/SKILL.md`
- `/Users/dmh2002/trae_projects/BMAD-METHOD/src/bmm-skills/4-implementation/bmad-dev-story/SKILL.md`
- `/Users/dmh2002/trae_projects/BMAD-METHOD/src/bmm-skills/4-implementation/bmad-sprint-planning/SKILL.md`
- `/Users/dmh2002/trae_projects/BMAD-METHOD/src/bmm-skills/4-implementation/bmad-retrospective/SKILL.md`
- `/Users/dmh2002/trae_projects/BMAD-METHOD/src/bmm-skills/4-implementation/bmad-checkpoint-preview/SKILL.md`
- `/Users/dmh2002/trae_projects/BMAD-METHOD/src/core-skills/bmad-brainstorming/SKILL.md`

### 内部参考

- `specs/evals/11-LDVH-Gstack-Trae融合产品方向共识.md`
- `specs/evals/19-Gstack深度调研-人工确认-测试流程-使用说明与LDVH对比.md`
- `specs/evals/20-Superpowers深度调研-TDD强制-工程纪律与LDVH借鉴.md`
