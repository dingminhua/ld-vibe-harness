# LDVH、Gstack 与 Trae Solo 融合产品方向共识

> 创建日期：2026-06-03
> 定位：LDVH 后续产品化演进的共识起点，用于避免多行动分支后偏离主线
> 调研边界：不直接构成强制规则
> 执行效力：无，结论需进入 00-79 正式规范区间或 ADR 后才成为稳定规则
> 上位依据：`specs/00-LD-Vibe-Harness理念与纲要.md`
> 相关参考：`specs/evals/13-LDVH假设重来视角下对gstack的借鉴再评估.md`、`specs/evals/02-LDVH对gstack的借鉴评估.md`、`specs/evals/14-Gstack照搬进入Trae环境可行性评估.md`
> 关键前置：`specs/evals/13-LDVH假设重来视角下对gstack的借鉴再评估.md` 是本文的底层架构前置，优先级高于 14 号评估；14 号文档用于 Trae 环境融合可行性与执行路线补充

---

## 1. 本文解决的问题

本文沉淀当前阶段对 LDVH、Gstack 与 Trae Solo 三者关系的共识，作为后续沟通、计划、Spec、ADR 和实现工作的固定起点。

本文用于避免以下问题：

1. 把 Gstack 误解为要照搬的实现模板；
2. 把 LDVH 误解为只是一套内部规范文档；
3. 把 Trae Solo 误解为普通编辑器环境；
4. 在多个行动分支并行后，忘记主线目标；
5. 在工具、Skill、事实模型、Rules、产品化之间迷失优先级。

---

## 2. 关键前置文档

本文的底层架构前置是 `specs/evals/13-LDVH假设重来视角下对gstack的借鉴再评估.md`。

13 号文档比 14 号文档更基础，原因是：

1. 13 号文档回答"如果 LDVH 重来，顶层应如何设计"；
2. 13 号文档提出主闭环优先、最小事实内核、AI 进入速度、少量核心 Skill、四类工具与视图；
3. 13 号文档直接给出 LDVH 新版架构草案：Core Loop、最小事实源内核、核心 Skill、工具与视图；
4. 14 号文档更多回答"如何融合 Trae Solo 环境与产品化执行路线"，是 13 号文档之后的环境适配和路线细化。

因此，后续涉及 LDVH 产品方向、Core Loop、事实模型、Skill、PyTools、Web MVP 或防递归建设时，应优先读取 17 号入口文档，再按需回读 13 号文档；14 号文档用于补充 Trae 环境落地方案。

---

## 3. 核心共识

### 3.1 共识一：基于 Gstack 的思想来完善 LDVH

LDVH 不照搬 Gstack 的具体实现，但吸收 Gstack 对 AI 编程工作流产品化的关键洞察。

Gstack 对 LDVH 的价值在于提供体验范式，而不是提供可直接复制的技术结构。

可吸收的 Gstack 思想包括：

1. **流程即入口**：AI 不应先面对大量规范，而应先进入一条清晰工作流；
2. **阶段即约束**：每个阶段都有明确输入、输出、检查和停止条件；
3. **使用即流程**：正确行为应成为 AI 默认路径，而不是只写在规范里；
4. **质量门禁前置**：Plan、Human Gate、Verify、Evidence、Change 应进入主流程；
5. **产品体验优先**：框架应让 AI 更容易正确工作，而不是只让规范更完整。

Gstack 的具体实现，如 Claude Code Skill 结构、slash command、本地隐藏状态目录、浏览器 daemon、大量角色 Agent，不作为 LDVH 在 Trae Solo 环境中的直接实现模板。

### 3.2 共识二：LDVH 将演进为更适合 Vibe Coding 的产品

LDVH 的目标不是单纯的规范库，也不是一组内部规则，而是面向真实用户的 Vibe Coding 产品框架。

这个产品应具备：

1. **可安装**：用户可以通过安装、初始化和升级流程获得框架能力；
2. **可配置**：用户可以通过项目配置和模板适配自己的项目；
3. **可被 AI 快速理解**：AI 进入项目后能快速知道当前项目、当前阶段、当前约束和下一步；
4. **可执行**：AI 能通过 Skill 走完核心流程；
5. **可验证**：AI 的输出能通过 PyTools / Fact Validator / Gate Detector / Evidence Collector 校验；
6. **可沉淀**：Intent、Task、ADR、Evidence、Change、Pitfall 等事实能回到 Git 文件事实源；
7. **可演进**：框架能通过 Learn、Retro、Rule 改进、Tools 改进和版本升级持续优化。

---

## 4. 三者分工

### 4.1 Gstack 提供体验范式

Gstack 的作用是启发 LDVH 如何把 AI 工程工作流做成低摩擦产品体验。

它提供的不是实现边界，而是体验参照：

```text
Think → Plan → Build → Review → Test → Ship → Reflect
```

在 LDVH 中，这条经验被改写为：

```text
Intent → Plan → Execute → Verify → Record → Learn
```

### 4.2 LDVH 提供治理骨架

LDVH 的作用是提供 Vibe Coding 产品框架的治理骨架。

LDVH 应保留并强化：

1. 事实源边界；
2. 事实模型；
3. 状态机；
4. Human Gate；
5. Change 记录；
6. Evidence 沉淀；
7. Rules / Skill / Agent / Tools 的机制边界；
8. AI 第一服务对象原则；
9. V1-V10 价值判断标准。

但 LDVH 需要降低 AI 初始使用摩擦，让 Core Loop 成为第一体验。

### 4.3 Trae Solo 提供运行环境

Trae Solo 的作用是提供原生运行机制。

LDVH 应充分利用 Trae Solo 的：

1. Rules：项目入口、场景约束、压缩保护；
2. Skill：稳定流程；
3. Agent：必要时的独立上下文、并行分析和结论隔离；
4. Tools / PyTools：确定性校验、契约消费、证据收集和受控写入；
5. AskUserQuestion：Human Gate 技术承载；
6. RunCommand：测试、构建、校验和脚本执行；
7. Web Preview：真实页面验证；
8. Schedule：周期性审计和健康检查；
9. Memory：辅助跨会话连续性，但不替代 Git 文件事实源。

---

## 5. 产品公式

当前共识可以压缩为：

```text
Gstack 的体验范式
+ LDVH 的治理骨架
+ Trae Solo 的原生机制
= 面向 Vibe Coding 的产品框架
```

更具体地说：

```text
Gstack 提供体验范式；
LDVH 提供治理骨架；
Trae 提供运行环境；
三者融合，形成可安装、可配置、可验证、可沉淀、可演进的 Vibe Coding 产品框架。
```

---

## 6. 当前已落地基础

截至本文创建时，已经完成以下基础件：

### 6.1 核心事实对象

已补齐最小事实内核中的 3 个对象：

| 对象 | 规范 | 契约 | 状态 |
|---|---|---|---|
| Intent | `specs/24-Intent-意图.md` | `specs/24.06-Contract.md` | active |
| Evidence | `specs/29-Evidence-验证证据.md` | `specs/29.06-Contract.md` | active |
| Task | `specs/27-Task-任务.md` | `specs/27.06-Contract.md` | active |

ADR(21) 和 Change(22) 已有完整规范。Intent、Task、Evidence 当前为精简版规范，后续按阶段补齐完整版。

### 6.2 Core Loop Skill 入口

已创建：

1. `ldvh-intake`：用户意图 → 识别场景 → 创建 Intent/Task → Human Gate → 写入事实源；
2. `ldvh-close`：关闭条件校验 → Human Gate → 状态更新 → Change 记录。

### 6.3 Core Loop Rules 入口

L0 / L1 Rules 已加入 Core Loop 入口和路由：

```text
Intent → ldvh-intake
Record → ldvh-close
Plan / Execute / Verify / Learn → 待建设
```

### 6.4 当前阶段快照（2026-06-04）

截至 2026-06-04，LDVH MVP 骨架已经推进到 **Dogfood 1 完成并进入生产对象体系梳理** 阶段：

1. **最小事实内核已具备**：Intent / Task / Evidence 已有精简版规范和 Contract；ADR / Change 已有完整规范；Pitfall 已有正式规范。
2. **PyTools 最小校验能力已具备**：`tools/check_fact_model.py` 已实现，可校验 Intent / Task / Evidence YAML；`tests/tools/test_check_fact_model.py` 已覆盖合法、非法、输入错误和目录批量校验。
3. **YAML 长文本问题已完成一次闭环**：`task-0002` 已关闭，`ev-0002` 已记录验证通过；`ldvh-intake`、`ldvh-close` 与 Fact Validator 已补充块标量提示和测试覆盖。
4. **规范判断回原文已回流正式规范**：相关原则已进入 `specs/11`、`specs/11.01`、`specs/11.02`，不再只停留在 L1 Rules 或 evals/17。
5. **Core Loop Skill 已部署到工作区顶层**：`ldvh-intake` 与 `ldvh-close` 已从项目内草案目录迁移到 `/Users/dmh2002/trae_projects/.trae/skills/`，项目内 `.trae/skills/` 草案目录已删除。
6. **运行时文件忽略已处理**：`pm-kit-web/.pm-kit.pid` 已加入 `.gitignore`。
7. **当前真正下一步**：先完成 LDVH 生产对象整体梳理，把确定要做的对象、要降级的概念、要删除或不吸收的内容写入正式规范和本文，避免后续按过时 planned 清单扩张。
8. **待讨论流程缺口**：执行主线 Task 时，AI 发现 bug、缺口、规范遗漏或流程问题后，应如何自动创建关联 Task、区分 blocking 与 follow-up、如何影响主线 Task 关闭条件，目前尚未进入正式规范；该问题需要在生产对象边界清晰后再进入 TaskSet / Task 关系设计。

---

## 7. 下一步主线

当前下一步主线不是继续围绕单个工具扩张，而是先把 LDVH 生产对象体系梳理清楚：哪些对象必须落地为事实模型，哪些概念应降级为字段、模板或 Markdown 文档，哪些来自 Gstack 或 specs-v2 的内容当前不吸收。

### 7.1 为什么先梳理生产对象

继续扩张 Tools、Web、Skill 或 Agent 之前，必须先明确生产对象边界，否则会出现三个问题：

1. AI 会把发现的问题、风险、依赖、检查项和产物都误创建为 Task 或 ADR；
2. 过时 planned 清单会推动 Risk / Dependency / Artifact / Checklist 等概念过早成为独立事实模型；
3. Gstack 中的流程产物、runtime artifacts 或角色分工会被误认为 LDVH 必须照搬的事实对象。

因此当前主线是：

```text
梳理生产概念 → 区分事实模型 / 字段 / 模板 / 文档 → 更新 13 / 20 / 17 → 再决定下一批对象落地
```

### 7.2 当前对象边界共识

| Object / Concept | 中文 | 当前结论 | 承载方式 |
|---|---|---|---|
| Intent | 意图 | 已落地事实模型 | `ldvh-base/intents/` |
| Task | 任务 | 已落地事实模型 | `ldvh-base/tasks/` |
| Evidence | 证据 | 已落地事实模型 | `ldvh-base/evidence/` |
| ADR | 决策记录 | 已落地事实模型 | `ldvh-base/adrs/` |
| Change | 变更记录 | 已落地事实模型 | Git commit |
| Pitfall | 踩坑记录 | 已落地事实模型 | 待按 23 规范实例化 |
| Memo | 备忘 | 高优先级待落地事实模型 | 25 |
| Profile | 项目画像 | 高优先级待落地事实模型 | 26 |
| TaskSet | 任务集 | 高优先级待落地事实模型 | 28 |
| Risk | 风险 | 降级为字段候选 | Task / Memo / ADR / TaskSet 字段 |
| Dependency | 依赖 | 降级为关系字段 | Task / TaskSet 的 blocked_by、blocks、relation_type 等 |
| Artifact | 产物 | 降级为路径或输出字段 | Evidence artifact_path、Task / TaskSet 输出字段 |
| Checklist | 检查清单 | 降级为模板、字段或 Skill section | Task / TaskSet 验收项，执行结果进入 Evidence |
| Roadmap | 路线图 | 暂作 Markdown 文档 | evals/17、docs 或未来路线图文档 |

### 7.3 Gstack 借鉴边界

Gstack 对 LDVH 的价值主要是流程和产物连续交接，而不是事实对象模型本身。LDVH 当前只吸收以下方向：

1. 阶段化流程：让 AI 知道当前在 Intent、Plan、Execute、Verify、Record、Learn 哪一段；
2. 产物连续交接：前一阶段输出应成为后一阶段输入；
3. 质量门禁前置：测试、检查、review、ship summary 不能只靠最后补救；
4. 角色化审查思路：在必要时用少量高价值 Agent 或 Skill 辅助，而不是一次性创建大量角色；
5. JSONL、ship sections、TODO.md 等只作为流程产物参考，不作为 LDVH 权威事实源。

### 7.4 删除、降级与不吸收清单

当前明确删除、降级或不吸收：

1. 不把 Risk / 风险、Dependency / 依赖、Artifact / 产物、Checklist / 检查清单、Roadmap / 路线图列入当前独立事实模型落地优先队列；
2. 不直接吸收 Gstack 的 browser daemon、remote tunnel、本地隐藏状态目录、runtime cache 或 telemetry 作为权威事实源；
3. 不一次性创建大量 Agent、角色 Skill 或复杂 review army；
4. 不自动发布、自动合并、自动提交；提交仍按 `ldvh-commit` Skill 和 Change 纪律执行；
5. 不把 checklist、artifact、dependency 这类属性型概念强行对象化；
6. 不把 Roadmap / 路线图做成 YAML 对象，除非后续证明它需要独立状态、负责人、完成度统计或 Web 聚合。

### 7.5 后续落地顺序

生产对象边界稳定后，下一步优先级应是：

1. 先落地 TaskSet / 任务集，因为它直接解决“主线任务、支线任务、关联任务和自动归类”的问题；
2. 再落地 Memo / 备忘，用于承接尚未任务化但有保留价值的发现，避免所有问题都变成 Task；
3. 再落地 Profile / 项目画像，用于产品化、多项目接入和初始化体验；
4. Pitfall / 踩坑记录已有规范，后续应在真实错误复盘中实例化；
5. 初始化流程、审计流程、开发实践、交付实践和推荐 Agent 清单继续作为 specs-v2 保留建议，但必须逐项满足 LDVH 准入条件后再落地。

---

## 8. 从 evals/15 与 evals/16 吸收的补充共识

### 8.1 Trae Plan / Spec 是 LDVH 的原生规划增强层

Trae Plan 与 Spec 不替代 LDVH 的 Rules、事实模型、Skill 和 Tools，而应作为 Trae Solo 原生规划能力被 LDVH 分级利用。

吸收自 `specs/evals/15-LDVH对Trae-Plan与Spec功能的利用评估.md` 的共识：

1. Plan 适合作为中风险任务的轻量前置，强化"先计划，再执行"；
2. Spec 适合作为系统级复杂任务、planned 对象升级、重大规范创建或大规模重构的前置流程；
3. Plan/Spec 的关键产出应尽量回写或映射到 LDVH 事实源，而不是停留在对话或 `.trae/specs/` 中；
4. `.trae/specs/` 可被视为"规划态"资产，但执行态和权威状态仍应回到 `ldvh-base/` 或 `specs/`；
5. 低风险任务不强制 Plan/Spec，避免过度流程化。

### 8.2 Plan / Spec 是执行层脚手架，LDVH 做闭环验收

本次进一步形成的共识：Plan 与 Spec 首先属于执行层机制，而不是 LDVH 的长期事实源本体。

1. Plan 是短周期执行策略，用于帮助 AI 在当前轮次拆解步骤、暴露风险和获得确认；默认不应长期入库。
2. Spec 是复杂任务执行前的规划材料，可作为规划态资产保留，但不应成为执行状态或验收状态的权威来源。
3. LDVH 不应逐步验收 Plan 或 Spec 中的每个执行细节，而应验收最终交付是否契合 Intent / Task 的目标、约束和验收标准。
4. 当实际执行路径偏离 Plan / Spec，但最终结果满足 LDVH 闭环验收要求时，不需要为了同步过程材料而回写或修正 Plan / Spec。
5. 只有当偏离 Plan / Spec 形成重要决策、范围变化、风险、踩坑或长期经验时，才应沉淀为 ADR、Change、Pitfall 或 Learn 类事实。

LDVH 的闭环验收关注：

1. **目标一致性**：最终产出是否回应用户原始目标和 Task 目标；
2. **范围一致性**：是否存在明显做多、做少或偏题；
3. **约束一致性**：是否遵守 Rules、事实模型、状态机、Human Gate 和已接受 ADR；
4. **验证充分性**：是否执行了与任务风险匹配的 lint、typecheck、test、build、真实交互或人工检查；
5. **证据充分性**：Evidence 是否能支撑完成判断；
6. **变更可追溯性**：Change 或等价记录是否说明发生了什么变化、为什么变化、影响范围是什么；
7. **后续沉淀**：是否存在需要继续形成 ADR、Pitfall、Rule 改进或后续 Task 的内容。

因此，Plan / Spec 对 LDVH 的价值不是“完整归档过程”，而是为闭环验收提供输入。LDVH 应只吸收其中经确认且影响交付判断的稳定事实。

### 8.3 Spec 三文档与 LDVH 核心事实对象的映射

Trae Spec 三文档与 LDVH 最小事实内核存在自然映射：

| Trae Spec 文档 | LDVH 对象 | 映射含义 |
|---|---|---|
| `spec.md` | Intent | 目标、范围、成功标准、影响边界 |
| `tasks.md` | Task | 可执行任务拆解 |
| `checklist.md` | Evidence 输入 | 验收设想和验证提示，执行后才形成 Evidence |

该映射是后续 `ldvh-spec` Skill、Spec→LDVH 对象转换、Dogfood 测试和产品化安装体验的重要基础。映射时不应全文搬运或维护双重状态；`spec.md`、`tasks.md` 和 `checklist.md` 只提供来源和候选输入，权威状态仍回到 Intent、Task、Evidence、Change、ADR 等 LDVH 事实对象。

### 8.4 specs-v2 中应吸收的新对象与流程

吸收自 `specs/evals/16-specs-v2内容价值评估.md` 的共识：specs-v2 中最有价值的是当前 specs/ 缺失的新对象和新流程，而不是已有等价规范。

优先关注：

1. **Memo**：承载尚未任务化但有保留价值的输入、发现和提醒，避免误创建 Task/ADR；
2. **Profile**：承载项目身份、路径映射和项目名册，是产品化、多项目管理和安装配置体验的基础；
3. **初始化流程**：定义项目接入 LDVH 时如何判断项目类型、创建目录、生成 Rules/Skill/事实源；
4. **审计流程**：定义规范审计、技术审计、全量审计以及审计发现如何分流到 Task/Memo；
5. **开发实践规范**：定义 AI 如何知道怎么启动、检查、验证和汇报开发完成情况；
6. **交付实践规范**：定义发布前检查、发布后验证、回滚方案和发布记录要求；
7. **推荐 Agent 清单**：为后续少量高价值 Agent 建设提供候选，而不是一次性创建大量 Agent。

### 8.5 specs-v2 吸收原则

1. specs-v2 内容必须完成术语适配（PM Kit → LDVH，pm-kit-base → ldvh-base）；
2. specs-v2 对象实践不能原样复制，应改写为 LDVH 主文档 + NN.01-NN.06 子文档结构；
3. 已有等价对象（ADR、Task、Pitfall、Change）不重复吸收；
4. Memo / Profile / 初始化 / 审计 / 开发实践 / 交付实践优先级高于扩展对象和复杂 Web 展示；
5. 推荐 Agent 清单只能作为候选池，仍须满足 11.03 Agent 准入条件。

---

## 9. 优先级原则

后续行动如出现分支，应按以下原则排序：

1. **先入口，后深度**：先让 AI 知道当前阶段和下一步，再补复杂治理；
2. **先核心闭环，后扩展对象**：先稳定 Intent / Task / ADR / Evidence / Change，再扩展 Risk / Memo / Dependency / Artifact / Checklist / TaskSet；
3. **先 Contract 消费，后复杂自动化**：先让 PyTools 能读契约校验事实，再做自动修复、受控写入和 Web 展示；
4. **先 Dogfood，后产品扩张**：先在 LDVH 自身验证 Core Loop，再考虑外部用户安装体验；
5. **先 Trae-native，后外部依赖**：优先使用 Trae 原生机制，不急于引入外部 daemon 或复杂 CLI；
6. **先可解释，后自动化**：所有自动化必须能解释依据、来源和影响范围。

---

## 10. 不做什么

为避免偏离主线，当前明确不做：

1. 不照搬 Gstack 的 Claude Code Skill 结构；
2. 不引入 `~/.ldvh/` 本地隐藏状态目录作为稳定事实源；
3. 不一次性创建大量 Agent；
4. 不在 Tools 中调用 AI、Skill 或 Agent；
5. 不把 Memory 当作 Git 文件事实源的替代品；
6. 不自动发布、自动提交、自动合并；
7. 不先做复杂 Web 产品再验证 Core Loop；
8. 不在没有 Contract 消费规则的情况下扩张 PyTools。

---

## 11. 长期约束

> 回流状态：本节第 2-4 条已回流到 11 系列正式规范，分别由 `specs/11-LDVH-AI协作规范.md`、`specs/11.01-Rules机制规范.md` 和 `specs/11.02-Skill机制规范.md` 承接；本文保留为产品方向入口摘要，不替代正式规范。

1. Skill 提示词、Skill 文档和面向 AI 的 Skill 编排说明应使用中文，除非外部平台字段或技术标识必须使用英文。
2. 涉及规范、Rules、Skill、Agent、Tools、事实模型、状态机、部署边界或目录边界的判断，AI 不得只凭记忆、目录现状或经验推断；必须先定位并读取对应规范原文，再给出结论。
3. 当 AI 发现自己依赖了错误记忆、跳过规范原文、混淆层级或误判部署边界时，应把该错误转化为可执行检查项：明确触发场景、必读原文、检查顺序和停止条件。
4. LDVH 的价值不在于要求 AI 永远不犯错，而在于把已发现的错误模式沉淀为 Rules、Skill、Tools 或事实源检查，降低同类错误复发概率。

---

## 12. 防递归建设原则

LDVH 当前处于"用框架完善框架"阶段。该阶段必须防止递归死循环：为了完善框架不断要求先补更多框架能力，导致永远无法进入真实使用和产品验证。

### 12.1 核心原则

1. **框架建设必须服务最近一次可运行闭环**：每次新增规范、Skill、Tools 或对象，都必须说明它服务哪个已定义闭环，不能只服务未来假想能力；
2. **只补当前闭环的最小缺口**：不得因为发现更大体系缺口而扩张当前任务边界；
3. **Dogfood 优先于继续抽象**：当某个闭环具备最小可运行条件时，优先用 LDVH 自身跑一次，而不是继续补规范；
4. **一层抽象后必须落地一次**：每新增一层抽象（规范、对象、Skill、Tools 分类），必须安排一个实例化验证；
5. **禁止无限前置条件**：不得把"先补另一个规范/工具/对象"作为默认阻塞，除非它是当前闭环不可运行的硬阻塞；
6. **先人工可运行，再工具自动化**：流程先允许 AI + Human Gate 手动跑通，再考虑 PyTools 自动校验或 Web 展示。

### 12.2 递归停止规则

当出现以下信号时，应停止继续扩张框架，转入实例验证或 Dogfood：

1. 连续两个任务都在新增规范，而没有创建或验证任何事实实例；
2. 当前任务的输出无法被 Intent / Task / Evidence / Change 之一承载；
3. 新增能力不能改善 AI 进入、执行、验证、沉淀或演进中的任一环节；
4. 需要新增第三个前置规范才能完成当前规范；
5. 讨论开始围绕"为了建框架还需要什么框架"而不是"如何跑通下一个闭环"。

### 12.3 当前适用的最小闭环

当前阶段的最小闭环是：

```text
共识/需求 → ldvh-intake → Intent/Task → 执行 → Evidence → ldvh-close → Change → 复盘
```

后续每个新增能力应优先回答：

1. 它是否帮助这个闭环更容易跑通？
2. 它是否让事实对象更容易被校验？
3. 它是否减少 AI 迷路、越界或丢证据？
4. 它是否能在本项目中 Dogfood？

如果不能回答，应暂缓。

### 12.4 Web 最小展示入口

Web 展示应纳入 MVP，但必须限定为只读的最小态势入口，避免提前演变成复杂 Web 产品分支。

需要 Web 最小入口的原因：AI 可以通过 Rules、Skill、搜索和上下文理解项目全貌，但人无法高效从大量 `specs/` 与 `ldvh-base/` 文件中快速获得整体态势。没有 Web 入口时，Human Gate 的质量也会下降，因为用户缺少可视化全局视角。

当前阶段的 Web MVP 只应服务以下目标：

1. 展示当前 Core Loop 状态；
2. 展示 Intent / Task / Evidence / ADR / Change 的数量、状态和关联；
3. 展示哪些 Task 待执行、待审查、待关闭；
4. 展示哪些 Evidence 失败或缺失；
5. 展示最近 Change 与当前风险提示；
6. 为 Human Gate 提供只读上下文。

当前阶段明确不做：

1. 不做 Web 写入事实源；
2. 不做复杂权限系统；
3. 不做数据库持久化；
4. 不做复杂看板拖拽；
5. 不让 Web 成为新的事实源；
6. 不替代 `ldvh-base/` 或 `specs/`。

Web MVP 的定位是：

```text
Git 文件事实源 → PyTools 聚合 → Web 只读展示 → 人做更高质量 Human Gate
```

因此，Web 最小入口可以作为当前 MVP 的一部分，但它应排在 PyTools 聚合和基础事实实例之后；没有 PyTools 聚合时，Web 不应直接复杂解析所有规范。

---

## 13. 固定沟通起点

本文在 LDVH 产品完成前作为产品方向入口文档。后续涉及 LDVH 产品化、Gstack 借鉴、Trae Solo 利用、Core Loop、PyTools、事实模型、Skill、Rules、Agent、Web 或安装配置体验的任务，应优先回到本文确认主线。

后续如果发现重要共识、关键决策、方向修正、长期约束、产品定位变化或可能导致行动分支漂移的内容，应更新本文进行记录，避免跨会话遗忘。

后续如果出现方向不清，应回到本文确认：

1. 当前行动是否服务于 Gstack 思想完善 LDVH？
2. 当前行动是否推动 LDVH 成为更适合 Vibe Coding 的产品？
3. 当前行动是否利用了 Trae Solo 原生机制？
4. 当前行动是否强化了 Core Loop？
5. 当前行动是否避免了事实源漂移？
6. 当前行动是否提升了 AI 进入、执行、验证、沉淀或演进能力？

如果答案是否定的，应暂停该分支，重新评估是否进入 ADR 或推迟。
