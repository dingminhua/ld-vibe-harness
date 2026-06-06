# LDVH 全盘确认与核心吸收建议

> 创建日期：2026-06-07
> 定位：LD Vibe Harness 当前 specs 与 evals 多轮迭代后的项目级全盘确认参考
> 调研边界：不直接构成强制规则
> 执行效力：无，结论需进入 00-79 正式规范区间或 ADR 后才成为稳定规则
> 上位依据：`specs/00-LD-Vibe-Harness理念与纲要.md`
> 相关规范：`specs/01-目录说明.md`、`specs/03-文档规范.md`、`specs/04-事实源边界与承载规范.md`、`specs/08-工作流程基础规范.md`、`specs/20-工作模型集合索引.md`

---

## 1. 本文解决的问题

本文承接 LD Vibe Harness 项目在多轮 specs 编写、evals 调研、外部项目借鉴和内部机制讨论后的全盘确认需求，整理当前最值得吸收进入正式规范体系的核心内容、应暂缓吸收的方向和不建议吸收的外部机制。

本文不是正式规范正文，不直接定义强制规则。本文用于辅助后续重写或确认 00 总纲、08 工作流程基础规范、20-27 工作模型规范、41 多角色思考流程以及 Rules、Skill、Tools、Web 相关机制边界。

当前项目已经积累了足够多的素材、调研和机制判断。后续重点不应继续无边界扩张，而应将已经反复出现、方向一致、能服务 AI 工作闭环的内容正式吸收进主规范；仍然只是参考、实验或局部灵感的内容，应继续留在 evals 或进入待确认状态。

---

## 2. 结论

LDVH 当前最值得正式吸收的，不是某个外部项目的具体功能，而是多轮迭代中反复被证明有效的 AI 工作闭环纪律：AI 第一体验、Git 文件事实源、四类构成要素、Core Loop、Human Gate、未验证不完成、Change / Record / Learn 回流，以及 specs 向 Rules、Skill、Tools、Web、Tests 派生的长期路线。

建议全盘确认以下核心判断：

1. LDVH 是面向 Vibe Coding 的规范驱动 AI 工作 Harness；
2. LDVH 以 AI 执行者为第一服务对象，同时保留 Human 的关键判断权；
3. Git 可追踪文件是最终事实源，聊天、工具输出、Web 状态、MCP memory、Skill 输出和 Agent 输出都不是最终事实源；
4. 开发环境、辅助工具、工作模型、工作流程是 LDVH 的四类构成要素，事实源不是第五类要素，而是贯穿四类要素的权威原则；
5. LDVH 的标准运行闭环是 Intent → Plan → Execute → Verify → Record → Learn；
6. 未验证不完成，没有 evidence 的 done 不是真正的 done；
7. Human Gate 是判断权和授权权边界，不是普通偏好选择，也不是 AI 懒得判断时的随意提问；
8. specs 定义产品 DNA，Rules、Skill、Tools、Web、Tests 是派生能力，实践结果通过 Change、Pitfall、ADR、Memo 和 specs 回流。

---

## 3. 应正式吸收的内容

### 3.1 产品定义

建议正式确认：LD Vibe Harness 是面向 Vibe Coding 的规范驱动 AI 工作 Harness。

这一判断应成为 00 总纲的核心产品定义之一。LDVH 不应被描述为单纯的文档体系、工具集合、Web 后台、任务管理器或 Agent 框架。它的核心价值在于通过规范、事实源、工作模型、工作流程、Code 确定性执行和 Web 桥接能力，把随性的 AI 编程转化为可读取、可判断、可执行、可验证、可回写、可演进的工程闭环。

可吸收表达：

```text
LD Vibe Harness 是面向 Vibe Coding 的规范驱动 AI 工作 Harness。它以 specs 定义产品 DNA，以事实源承载稳定状态，以工作模型组织工程对象，以工作流程约束 AI 行动，以 Code 提供确定性执行，以 Web 桥接 Human 判断，最终形成可读取、可判断、可执行、可验证、可回写、可演进的 AI 工程闭环。
```

### 3.2 AI 第一体验

建议将 AI 第一体验正式确认为 LDVH 的设计原则。

LDVH 的第一体验不是 Human 管理界面，而是 AI 能否快速进入项目、理解事实、判断边界、执行任务、验证结果并回写事实源。Human 是判断者，AI 是主要执行者，Code 是确定性执行者，Web 是桥接界面。

该原则会影响后续机制设计：

1. Web MVP 不应先做复杂后台，而应先做 AI 和 Human 都能理解的态势入口；
2. Tools 不应只服务人手动操作，而应服务 AI 读取、校验和聚合；
3. specs 不应只是人类文档，应逐渐增强机器可消费性；
4. Task 不应只是项目管理卡片，而应是 AI 可执行工作单元；
5. Human Gate 不应退化为偏好选择，而应体现判断权边界。

### 3.3 Core Loop 六阶段

建议正式吸收以下 Core Loop：

```text
Intent → Plan → Execute → Verify → Record → Learn
```

该链路已经在多轮调研和内部讨论中反复出现，适合作为 LDVH 主运行闭环。当前项目已有局部雏形：ldvh-intake 对应 Intent，ldvh-plan 对应 Plan，ldvh-close 对应 Verify / Record，ldvh-commit 对应 Change；Execute 和 Learn 仍需要进一步补齐。

建议吸收路径：

1. 在 00 中作为运行闭环总原则；
2. 在 08 中作为工作流程基础框架；
3. 在 27 中映射 Task 生命周期；
4. 在 40-59 区间逐步补齐 Plan、Execute、Verify、Record、Learn 相关工作流程。

### 3.4 未验证不完成

建议将“未验证不完成”上升为 LDVH 的工程纪律。

可吸收表达：

```text
完成必须以可验证结果和可追溯证据为依据。AI 的口头总结、主观判断或未执行的检查，不构成完成依据。
```

该原则适合进入 00 运行闭环标准、08 工作流程基础规范、27 Task 关闭条件、ldvh-close Skill 和 10 工作流测试。它与当前 Task acceptance、closure_evidence、verifying / review_needed 状态和独立审计机制方向一致。

### 3.5 Human Gate 是判断权边界

建议将 Human Gate 明确为 Human 判断权、授权权和责任边界的显式化机制。

Human Gate 不应是普通偏好选择，也不应是 AI 无法决定时的随意提问。它应覆盖关键事实源创建、关键状态流转、高风险变更、ADR 接受或废弃、删除或覆盖、任务关闭、自动化授权、发布或外部影响、多方案存在实质差异等场景。

可吸收表达：

```text
Human Gate 是 LDVH 中 Human 判断权、授权权和责任边界的显式化机制，不是普通交互确认，也不是 AI 无法判断时的随意提问。
```

### 3.6 事实源不可替代

建议继续强化 Git 文件事实源作为底层权威原则。

需要明确排除以下机制成为最终事实源：聊天上下文、工具输出、Skill 输出、Agent 输出、Web UI 状态、数据库派生视图、MCP memory、隐藏本地状态目录、临时 task json、Trae Spec 中间产物。

可吸收表达：

```text
任何机制只要不能回到 Git 可追踪事实源，就只能是过程辅助，不能成为 LDVH 的稳定事实。
```

该原则是防止 Web、MCP、Skill、Agent 或外部工作流形成第二事实源的关键边界。

### 3.7 Web MVP 只读态势入口优先

建议吸收 Web 方向，但只吸收原则，不在 00 中写死页面布局、组件名或技术栈。

推荐原则：

```text
Web MVP 优先作为事实源的只读态势入口和 Human Gate 辅助界面，不先作为复杂写入后台。
```

可优先考虑的 Web 信息同步范围包括 Task 列表、Task 详情、Intent 详情、Fact Validation 面板、Change / Record 视图、Docs 入口、Human Gate 页面和 Runtime Panel。

Web 写入能力应晚于事实源解析、校验、状态聚合和 Human Gate 规则成熟之后。

### 3.8 Skill 生命周期化

建议正式确认 LDVH Skill 不应按角色无限扩张，而应优先按 Core Loop 生命周期补位。

当前核心 Skill 可映射为：

| Core Loop 阶段 | 当前 Skill / 状态 |
|---|---|
| Intent | ldvh-intake |
| Plan | ldvh-plan |
| Execute | 待建设 |
| Verify / Record | ldvh-close |
| Decision | ldvh-adr |
| Change | ldvh-commit |
| Learn | 待建设 |

Skill 写作和维护应吸收以下要求：Use / Do NOT Use、输入输出契约、失败处理、Human Gate 条件、事实源读取要求、评估用例、不调度 Agent、不链式调度 Skill、输出不是事实源且回写后才成立。

短期重点不应是大量新增 Skill，而应是升级现有核心 Skill 质量。

### 3.9 独立审计 Agent 作为 Verify 阶段机制

建议将独立审计 Agent 吸收为 Verify 阶段的重要机制，但不应对所有任务无差别强制。

可吸收分级：

1. 普通任务：工具验证和 acceptance 检查；
2. 中等任务：建议独立审计；
3. 高风险任务：必须独立审计；
4. 规范、状态、事实源变更：Human Gate 与验证必需。

可吸收表达：

```text
对于任务关闭、高风险变更、复杂规范变更和多模块影响，AI 主控不得只凭自身执行上下文完成审查；应通过独立上下文审计、工具验证或 Human Gate 形成外部证据。
```

### 3.10 规范即机制长期路线

建议将“规范即机制”吸收为长期方向，而不是立即全面落地。

长期目标是：

```text
specs → Rules
specs → Skill
specs → Validators
specs → Web schema
specs → Tests
```

但当前 specs 结构还未完全机器可消费，字段契约、状态机、流转矩阵、Human Gate 条件和历史 Contract 文档仍需进一步整理。因此建议先吸收方向，后续再通过结构化契约、validator 覆盖矩阵和 drift 检测逐步落地。

---

## 4. 应暂缓吸收的内容

### 4.1 自建 MCP

自建 MCP 可以保留为远期方向，但当前不宜进入核心体系。

原因包括：PyTools 尚未完全稳定，Web 只读态势入口尚未落地，Fact Validator、Context Pack 和 Status Aggregator 仍可用本地 Tools 推进，写入型 MCP 风险较高，过早 MCP 化会分散主线。

建议路线：先做 PyTools，只读聚合和校验成熟后，再考虑 MCP 协议入口。

### 4.2 ProjectGroup 工作模型

多项目治理方向有价值，但当前不建议新增 ProjectGroup 工作模型。

可先吸收 Profile tags、项目身份、project_path、ldvh_base_path 和多项目只读聚合。当管辖项目数量和跨项目聚合需求达到稳定阈值后，再评估是否引入 ProjectGroup。

### 4.3 Trae Spec Ingest 完整机制

Trae Spec 可以作为规划辅助，但不应成为第二权威事实源。

可吸收原则：Task 是治理锚点，Trae Spec 是规划产物，Spec 确认不等于执行授权，Spec 必须被吸收后才能成为执行依据。

不建议当前立即将完整 ldvh-spec-ingest 机制写入主规范，除非后续确定进入实现阶段。

### 4.4 多角色思考扩张

41 多角色思考规范已有基础，不建议继续扩张为角色体系或人格化 Agent 系统。

应保留主上下文轻量模式、多 Agent 模式、同轮最多 4 个并行 Agent、输出不是事实源、回写建议由主控判断等原则。多角色思考应是复杂判断方法，不是组织架构。

### 4.5 Web 写入后台

Web 可以后续做受控写入，但当前不应直接发展成复杂写入后台。

过早写入会带来绕过 Human Gate、产生第二事实源、UI 状态与 Git 事实源不一致、为了前端体验牺牲对象规范等风险。

---

## 5. 不建议吸收的内容

### 5.1 隐藏本地状态目录

不建议吸收隐藏本地状态目录、memory store、local database、agent state 或本地 task json 作为 LDVH 核心事实源。

这些机制可以作为缓存或派生视图，但必须明确不是事实源。

### 5.2 自动 push、release、merge

LDVH 可以辅助 commit 草案、commit 校验和变更记录，但不应自动 push、release 或 merge。

这些行为属于 Human 权限边界。

### 5.3 分数式完成标准

不建议吸收 score >= 80 等分数式完成标准。

LDVH 的完成标准应依据 acceptance 是否满足、验证是否执行、evidence 是否存在、Human Gate 是否通过、Change 是否记录和对象状态是否正确，而不是模糊评分。

### 5.4 人格化 Agent 系统

不建议吸收人格化 Agent 系统。

LDVH 中的 Agent 应作为独立上下文、专业审计或隔离评估能力，而不是人格角色扮演系统。

### 5.5 AI 自审即完成

不建议接受 AI 主控仅凭自身总结完成审查和关闭。

LDVH 的 Verify 应具备外部性，包括工具验证、测试结果、独立上下文审计、Human Gate、Git diff、validator 输出或其他可追溯 evidence。

---

## 6. 全盘确认命题

### 6.1 产品定义

LDVH 是面向 Vibe Coding 的规范驱动 AI 工作 Harness。

### 6.2 第一服务对象

LDVH 以 AI 执行者为第一服务对象，但 Human 保留关键判断权。

### 6.3 事实源原则

Git 可追踪文件是最终事实源；聊天、工具输出、Web 状态、MCP memory、Skill 输出和 Agent 输出都不是最终事实源。

### 6.4 四类构成要素

开发环境、辅助工具、工作模型、工作流程是 LDVH 的四类构成要素；事实源不是第五类要素，而是贯穿四类要素的权威原则。

### 6.5 运行闭环

LDVH 的标准运行闭环是 Intent → Plan → Execute → Verify → Record → Learn。

### 6.6 完成标准

未验证不完成；没有 evidence 的 done，不是真正的 done。

### 6.7 Human Gate 原则

Human Gate 是判断权和授权权边界，不是普通偏好选择，也不是 AI 懒得判断时的随意提问。

### 6.8 演进方式

specs 定义产品 DNA，Rules、Skill、Tools、Web、Tests 是派生能力；实践结果通过 Change、Pitfall、ADR、Memo 和 specs 回流。

---

## 7. 对 00 总纲的建议影响

如果围绕 00 总纲进行全盘确认，建议形成以下结构逻辑：

1. 为什么存在：解释 Vibe Coding 的问题和 LDVH 的使命；
2. 以 AI 执行者为第一服务对象：解释 AI 依赖、AI 能力、AI 本质，以及 Human / AI / Code / Web 分工；
3. 四类构成要素与事实源原则：解释开发环境、辅助工具、工作模型、工作流程和事实源原则；
4. 价值实现标准：解释什么样的机制值得进入 LDVH；
5. 运行闭环标准：正式吸收 Intent → Plan → Execute → Verify → Record → Learn；
6. 机制落地关系：解释 00 如何约束后续 specs、Rules、Skill、Tools、Web；
7. Human Gate 与检查要求：明确 Human Gate 是判断权边界；
8. 待补齐事项：放置仍未定稿、不宜立即固化的内容。

当前 00 的第 1、2 章已经基本稳定。第 3 章适合确认四类构成要素、事实源原则和协作关系。第 4 章之后适合重点吸收 Core Loop、验证铁律、Human Gate 和规范即机制长期路线。

---

## 8. 建议优先级

### 8.1 最优先吸收

1. 产品定义：LDVH 是面向 Vibe Coding 的规范驱动 AI 工作 Harness；
2. AI 第一体验：设计首先服务 AI 进入项目、理解事实、执行任务、验证和回写；
3. Core Loop：Intent → Plan → Execute → Verify → Record → Learn；
4. 验证铁律：未验证不完成，没有 evidence 的 done 不是真正的 done；
5. 规范即机制长期路线：specs → Rules / Skill / Validators / Web / Tests。

### 8.2 优先清理

1. Evidence / Risk 等已取消或 deferred 概念的残留引用；
2. Human Gate 删除豁免与高风险事实源删除之间的边界；
3. 项目规则中产品方向入口编号与实际 evals 文档编号不一致的问题；
4. 11 最佳实践与当前 Task verifying / review_needed 机制之间的措辞对齐；
5. Profile 与工作区管辖项目配置之间的名册权威边界。

### 8.3 暂不推进

1. 自建 MCP；
2. Web 写入后台；
3. ProjectGroup 工作模型；
4. Trae Spec Ingest 完整机制；
5. 大量新增 Skill；
6. 大量角色 Agent。

---

## 9. 待补齐事项

1. 将本文核心命题逐条与 00 总纲修订方案对齐；
2. 判断 Core Loop 是否需要 ADR 确认，尤其是其对 08、27 和 Skill 生命周期的长期影响；
3. 梳理 Evidence / Risk / ProjectGroup / Trae Spec Ingest 等候选概念的正式状态；
4. 为 Verify 阶段建立分级审计和 evidence 类型说明；
5. 为 specs → Rules / Skill / Tools / Web / Tests 派生路线建立结构化契约和 validator 覆盖矩阵。
