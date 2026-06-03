# LDVH、Gstack 与 Trae Solo 融合产品方向共识

> 创建日期：2026-06-03
> 更新日期：2026-06-04
> 定位：LDVH 后续产品化演进的共识起点，承接原 evals/10、12、13、14、15、16、18 中仍有价值的判断，用于避免后续删除旧评估文档后丢失主线
> 调研边界：不直接构成强制规则
> 执行效力：无，结论需进入 00-79 正式规范区间或 ADR 后才成为稳定规则
> 上位依据：`specs/00-LD-Vibe-Harness理念与纲要.md`
> 相关参考：原 evals/10、12、13、14、15、16、18 的有价值内容已吸收到本文
> 代码调研来源：`/Users/dmh2002/trae_projects/gstack`、`/Users/dmh2002/trae_projects/ld-vibe-harness`

---

## 1. 本文解决的问题

本文沉淀当前阶段对 LDVH、Gstack 与 Trae Solo 三者关系的共识，作为后续沟通、计划、Spec、ADR 和实现工作的固定起点。

本文用于避免以下问题：

1. 把 Gstack 误解为要照搬的实现模板；
2. 把 LDVH 误解为只是一套内部规范文档；
3. 把 Trae Solo 误解为普通编辑器环境；
4. 在多个行动分支并行后，忘记主线目标；
5. 在工具、Skill、事实模型、Rules、产品化之间迷失优先级；
6. 在 evals 旧文档清理后，丢失 Gstack、Trae Plan / Spec、specs-v2、Web MVP、PyTools、Core Loop 的关键共识。

本文不是正式规范。本文中的判断只有进入正式 `specs/`、Rules、ADR 或事实源后，才成为稳定执行依据。

---

## 2. 结论

当前产品方向保持不变：

```text
Gstack 的体验范式
+ LDVH 的治理骨架
+ Trae Solo 的原生机制
= 面向 Vibe Coding 的产品框架
```

更具体地说：

1. **Gstack 提供体验范式**：它证明 AI 工程协作不应只靠零散 prompt，而应被产品化为阶段清晰、角色明确、产物连续、质量门禁前置的工作流。
2. **LDVH 提供治理骨架**：LDVH 的核心价值仍是 Git 文件事实源、事实模型、状态机、Human Gate、Evidence、Change、ADR、Rules、Skill、Tools 与 AI 第一服务对象原则。
3. **Trae Solo 提供运行环境**：Trae Solo 的 Rules、Skill、Agent、Tools、AskUserQuestion、RunCommand、Preview、Schedule、Memory 等能力，是 LDVH 在当前环境中产品化的原生承载层。
4. **三者融合的目标不是复刻 Gstack，而是形成 Trae-native 的 LDVH Core Loop**：把 `Intent → Plan → Execute → Verify → Record → Learn` 做成 AI 进入项目后的第一体验。
5. **当前 LDVH 已经具备最小 Dogfood 基础**：7 个事实对象、4 个 Core Loop Skill、Fact Validator 覆盖全部对象类型。
6. **当前最应优先补齐的不是继续抽象新对象，而是 Record / Change 闭环和执行中发现问题的分流规则**。

---

## 3. 核心共识

### 3.1 共识一：基于 Gstack 的思想来完善 LDVH

LDVH 不照搬 Gstack 的具体实现，但吸收 Gstack 对 AI 编程工作流产品化的关键洞察。

通过读取 Gstack 代码可以确认，Gstack 的本质不是单一浏览器工具，也不是一批 prompt，而是一套把 AI 工程工作流做成产品的机制：

1. 顶层工作流把工程过程组织为 `Think → Plan → Build → Review → Test → Ship → Reflect`；
2. 大量 `SKILL.md` 将产品、计划、工程、Review、QA、发布、复盘等环节角色化；
3. `SKILL.md.tmpl`、生成器、host config 和 runtime assets 共同避免多宿主、多 Skill 手工漂移；
4. browse daemon 把浏览器变成低延迟、可连续操作、可验证真实页面的硬能力；
5. AskUserQuestion decision brief 把 Human Gate 变成结构化问询协议；
6. review / qa / ship 等 Skill 把 scope drift、真实浏览器 QA、回归验证、发布 gate 纳入流程；
7. trust boundary、CDP allowlist、scoped token 等机制说明工具输出和网页内容必须分可信边界。

Gstack 对 LDVH 的价值在于提供体验范式，而不是提供可直接复制的技术结构。

可吸收的 Gstack 思想包括：

1. **流程即入口**：AI 不应先面对大量规范，而应先进入一条清晰工作流；
2. **阶段即约束**：每个阶段都有明确输入、输出、检查和停止条件；
3. **使用即流程**：正确行为应成为 AI 默认路径，而不是只写在规范里；
4. **质量门禁前置**：Plan、Human Gate、Verify、Evidence、Change 应进入主流程；
5. **产物连续交接**：前一阶段产物应成为后一阶段输入，而不是散落在对话中；
6. **真实环境验证**：对 Web、CLI、安装、发布类任务，真实交互验证比静态自信更重要；
7. **信任边界显式化**：网页内容、外部工具输出、运行时缓存、AI 记忆均不能自动等同于权威事实源；
8. **产品体验优先**：框架应让 AI 更容易正确工作，而不是只让规范更完整。

Gstack 的具体实现，如 Claude Code Skill 结构、slash command、本地隐藏状态目录、浏览器 daemon、大量角色 Agent、自动遥测、自动更新、自动提交、自动发布、ngrok tunnel 和 ML prompt-injection classifier，不作为 LDVH 在 Trae Solo 环境中的直接实现模板。

### 3.2 共识二：LDVH 将演进为更适合 Vibe Coding 的产品

LDVH 的目标不是单纯的规范库，也不是一组内部规则，而是面向真实用户和 AI 协作者的 Vibe Coding 产品框架。

这个产品应具备：

1. **可安装**：用户可以通过安装、初始化和升级流程获得框架能力；
2. **可配置**：用户可以通过项目配置、Profile、模板和 Rules 适配自己的项目；
3. **可被 AI 快速理解**：AI 进入项目后能快速知道当前项目、当前阶段、当前约束和下一步；
4. **可执行**：AI 能通过 Skill 和 Rules 走完核心流程；
5. **可验证**：AI 的输出能通过 PyTools、Fact Validator、Gate Detector、Evidence Collector、测试和真实交互验证；
6. **可沉淀**：Intent、Task、ADR、Evidence、Change、Pitfall、Memo 等事实能回到 Git 文件事实源或正式规范；
7. **可审计**：Human Gate、状态流转、事实源写入、验证命令和 Change 记录可追溯；
8. **可演进**：框架能通过 Learn、Retro、Rule 改进、Tools 改进和版本升级持续优化。

因此，LDVH 不应继续以"先补全所有规范"为第一体验，而应以 Core Loop 为第一体验：

```text
Intent → Plan → Execute → Verify → Record → Learn
```

### 3.3 共识三：最小事实内核优先，扩展对象按痛点启用

LDVH 当前和下一阶段都应坚持最小事实内核优先。

第一层最小事实内核是：

```text
Intent / Task / ADR / Evidence / Change
```

这五类对象分别回答：

| 对象 | 回答的问题 |
|---|---|
| Intent | 人真正想达成什么，约束是什么 |
| Task | AI 当前要执行什么，验收标准是什么 |
| ADR | 长期决策为什么这样做，何时成为执行依据 |
| Evidence | 完成判断靠什么证据支撑 |
| Change | 实际发生了什么变化，为什么变化，影响范围是什么 |

第二层扩展对象按痛点启用，包括 TaskSet、Memo、Profile、Pitfall、Risk、Dependency、Artifact、Checklist 等。

这意味着：

1. 不应让 AI 一进入项目就面对所有对象；
2. 不应因为发现一个潜在对象就立刻扩张事实模型；
3. 扩展对象必须服务最近一次可运行闭环；
4. TaskSet / Memo / Profile / Pitfall 已在真实 Dogfood 压力下落地为事实模型；
5. Risk、Dependency、Artifact、Checklist 等对象应在真实 Dogfood 压力出现后再进入主线。

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

Gstack 中最值得 LDVH 借鉴的是：

1. 生命周期式 Skill，而不是零散命令；
2. 计划、评审、QA、发布、复盘之间的产物交接；
3. AskUserQuestion decision brief 形式的 Human Gate；
4. 浏览器 QA 和真实交互验证思想；
5. Skill 模板化和宿主适配机制；
6. 工具输出的 trust boundary；
7. team mode 中"可选试点 / 强制接入"的 adoption 思路；
8. scope drift detection 和 plan-completion review；
9. release / ship 之前的强 gate；
10. learn / retro 把失败和经验转化为后续默认行为；
11. `When to invoke`、触发词、允许工具、前置探测、Step、STOP、输出格式等 Skill prompt 组织方式；
12. review / qa / ship / retro / learn 等 Skill 对"何时进入、读什么、做什么、何时停、如何交付"的流程化表达。

Gstack 中不应直接照搬的是：

1. `~/.gstack/` 或类似本地隐藏目录作为稳定事实源；
2. Claude Code slash command 结构；
3. 大量人格化角色 Skill 的目录形态；
4. 自动遥测和自动更新默认开启；
5. 自动提交、自动 push、自动发布；
6. pair-agent / ngrok 远程浏览器控制；
7. 复杂 ML prompt-injection classifier；
8. 超长 monolithic Skill 运行时上下文；
9. 以 solo-builder 速度优先替代 LDVH 的事实源和 Human Gate 纪律。

### 4.2 LDVH 提供治理骨架

LDVH 的作用是提供 Vibe Coding 产品框架的治理骨架。

LDVH 应保留并强化：

1. Git 文件事实源边界；
2. 事实模型与对象状态机；
3. Human Gate；
4. ADR 决策记录；
5. Evidence 验证证据；
6. Change 变更记录；
7. Pitfall 与 Learn 沉淀；
8. Rules / Skill / Agent / Tools / Web 的机制边界；
9. AI 第一服务对象原则；
10. V1-V10 价值判断标准。

但 LDVH 需要降低 AI 初始使用摩擦，让 Core Loop 成为第一体验。

Human Gate 应从规范纪律升级为工具护栏，建议三类安全工具：

1. **Destructive Action Guard**：阻止未授权的破坏性操作（force push、reset --hard、clean -f 等）；
2. **Fact Source Guard**：阻止绕过事实源写入流程的直接文件修改；
3. **Scope Freeze Guard**：阻止超出当前 Task 范围的未授权变更。

LDVH 的产品化不是把规范削弱，而是把规范从"AI 需要主动记住的文档"转化为：

1. Rules 中的入口路由；
2. Skill 中的稳定流程；
3. Tools 中的确定性校验；
4. Evidence 中的验证证据；
5. Change 中的变更追溯；
6. Web 中的人类可读态势；
7. ADR 中的长期决策依据。

### 4.3 Trae Solo 提供运行环境

Trae Solo 的作用是提供原生运行机制。

LDVH 应充分利用 Trae Solo 的：

1. Rules：项目入口、场景约束、压缩保护；
2. Skill：稳定流程与 Core Loop 阶段入口；
3. Agent：必要时的独立上下文、并行分析和结论隔离；
4. Tools / PyTools：确定性校验、契约消费、证据收集和受控写入；
5. AskUserQuestion：Human Gate 技术承载；
6. RunCommand：测试、构建、校验和脚本执行；
7. Web Preview：真实页面验证；
8. Schedule：周期性审计和健康检查；
9. Memory：辅助跨会话连续性，但不替代 Git 文件事实源；
10. Plan / Spec：作为规划增强层，但不替代 LDVH 权威事实源。

Trae Solo 的 Plan / Spec 应被分级使用：

| 场景 | 推荐使用 |
|---|---|
| 低风险、单点修改 | 可直接执行，不强制 Plan / Spec |
| 中风险、多步骤任务 | 使用 Plan 或等价计划说明 |
| 系统级复杂任务、重大规范创建、大规模重构 | 使用 Spec 或等价规划材料 |
| 涉及 LDVH Human Gate 的关键变更 | Plan / Spec 不能替代 AskUserQuestion |

`.trae/specs/` 可作为规划态资产和候选输入，但不应成为权威执行状态。权威状态仍应回到 `ldvh-base/`、正式 `specs/`、ADR、Evidence、Change 或 Git commit 记录。

### 4.4 Skill、视角与 Agent 的产品化分层

Gstack 的大量角色 Skill 说明：AI 工程协作可以通过提示词把专业流程产品化。更准确地说，Gstack 倾向于用 Skill 承载稳定行动入口：Skill 不只是 prompt，而是行动入口、上下文装配、流程约束、工具授权和产物契约的组合。

在 Gstack 中，一个 Skill 通常同时回答：什么时候进入这个流程、进入前要读取或探测什么上下文、允许使用哪些工具、执行步骤和 STOP 点是什么、Human Gate 如何触发、最终要交付什么产物。因此，Gstack 的 Skill 是一种构建行动上下文的产品机制，而不是单纯的角色文本。

但这不意味着所有行动都应该变成 Skill。LDVH 不应把这个经验简化为"所有入口 Skill 化"，也不应简化为"不要角色 Skill"，而应拆成四层吸收：

| 层级 | LDVH 建议 | 适用场景 |
|---|---|---|
| 稳定行动入口 | 优先评估 Skill 化 | 需要上下文装配、工具授权、流程约束、Human Gate 和产物契约的高频行动 |
| 生命周期流程 | 建设为 Skill | 符合 Core Loop、输入输出稳定、高频复用、需要降低 AI 进入摩擦 |
| 临时角色视角 | 在主上下文运行时切换 | 只需要产品、工程、QA、安全、架构等视角补充判断，不需要隔离上下文 |
| 多角色子 Agent | 由主控按需并行调度 | 需要独立上下文、并行分析、结论隔离或大上下文分摊 |
| 长期专业入口 | 谨慎建设正式 Agent 或稳定规范 | 角色长期复用、权限边界明确、输出契约稳定 |

因此，`ldvh-plan`、`ldvh-verify`、`ldvh-review`、`ldvh-close`、`ldvh-retro` 这类生命周期流程适合逐步 Skill 化；某些稳定工程动作如果需要重复装配上下文、执行门禁和交付结构化产物，也可以进入 Skill 候选。但"产品经理视角""架构师视角""QA 视角""安全视角"等不应默认创建成独立 Skill 或 Agent。它们更适合作为运行时视角参数，由主控根据任务复杂度决定是在主上下文临时切换，还是启动一个或多个子 Agent。

Trae Solo 中子 Agent 可以并行，也可以在授权边界内调用 Skill。LDVH 对这项能力的产品判断是：

1. 子 Agent 调用 Skill 可以作为复杂任务的能力组合方式；
2. 子 Agent 是否可调用某个 Skill，应由主控输入、行动模型或 Agent 定义明确授权；
3. 子 Agent 输出必须回到主控汇总，不能直接成为权威事实源；
4. 子 Agent 发现 Human Gate、状态流转、ADR、事实源写入或高风险变更时，应停止相关修改并报告主控；
5. Skill 不应主动调度 Agent 的边界仍然成立，Agent 可调用 Skill 不等于 Skill 可反向调度 Agent；
6. 多角色并行的价值在于扩大视角和隔离上下文，不应替代事实源、Evidence、Change 或 Human Gate。

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
三者融合，形成可安装、可配置、可执行、可验证、可沉淀、可审计、可演进的 Vibe Coding 产品框架。
```

---

## 6. 当前已落地基础

### 6.1 核心事实对象

已补齐最小事实内核中的 7 个对象：

| 对象 | 规范 | 契约 | 状态 |
|---|---|---|---|
| Intent | `specs/24-Intent-意图.md` | `specs/24.06-Contract.md` | active |
| Task | `specs/27-Task-任务.md` | `specs/27.06-Contract.md` | active |
| TaskSet | `specs/28-TaskSet-任务集.md` | `specs/28.06-Contract.md` | active |
| Evidence | `specs/29-Evidence-验证证据.md` | `specs/29.06-Contract.md` | active |
| Memo | `specs/25-Memo-备忘.md` | `specs/25.06-Contract.md` | active |
| Profile | `specs/26-Profile-项目画像.md` | `specs/26.06-Contract.md` | active |
| Pitfall | `specs/23-Pitfall-踩坑记录.md` | `specs/23.06-Contract.md` | active |

ADR(21) 和 Change(22) 已有完整规范。Intent、Task、Evidence 当前为精简版规范，后续按阶段补齐完整版。Task 已新增子任务机制（parent_task/sub_tasks）和关联任务自动创建流程。

### 6.2 Core Loop Skill 入口

已创建：

1. `ldvh-intake`：用户意图 → 识别场景 → 创建 Intent/Task/TaskSet/Memo/Profile → TaskSet 自动归类 → Human Gate → 写入事实源；
2. `ldvh-close`：关闭条件校验（含子任务联动、TaskSet 关闭）→ Human Gate → 状态更新 → 级联检查（Intent/TaskSet/父任务）→ Change 记录；
3. `ldvh-adr`：ADR 创建、状态流转和受控写入；
4. `ldvh-commit`：准入变更提交编排。

### 6.3 当前最小闭环状态

当前 LDVH 已经跑通过两轮最小闭环：

```text
Intent → Task → Evidence → Close
```

第一轮：

```text
intent-0001 → task-0001 → ev-0001 → task closed → intent completed
```

第二轮：

```text
Dogfood 暴露 YAML 长文本问题 → task-0002 → Skill / Tool / Test 修复 → ev-0002 → task closed
```

这说明 LDVH 已经不只是规范草案，而是能用自身机制处理自身问题。

### 6.4 当前仍未完成的关键环节

当前缺口主要集中在以下方面：

1. **Change / Record 闭环不够清晰**：Change 已有规范和 commit message 校验，但与 Task closure、Evidence、commit、Skill 的关系仍需更明确；
2. **Plan / Execute / Verify / Learn 阶段尚未形成稳定 Skill**：当前只有 Intent 与 Record 入口较明确；
3. **Fact Validator 仍是最小实现**：尚未通用消费 Contract，尚未完整覆盖状态机和跨文件引用；
4. **PyTools 标准化未完全完成**：Issue 输出、退出码、CLI 参数、受控写入边界仍需逐步统一；
5. **pm-kit-web 尚未对齐 `ldvh-base/` 新事实内核**：当前更像旧 PM Kit 工作台原型；
6. **`.trae/specs/` 与事实源状态存在局部不同步**：它应保持规划态资产定位，不应成为第二套权威状态；
7. **执行中发现问题如何分流尚未规范化**：blocking、follow-up、opportunistic fix、ADR 候选、Pitfall 候选之间的判断需要进入行动模型或 Task 流程。

### 6.5 当前阶段快照（2026-06-04）

截至 2026-06-04，LDVH MVP 骨架已经推进到 **生产对象体系梳理完成并进入 Dogfood 验证** 阶段：

1. **最小事实内核已扩展至 7 个对象**：Intent / Task / TaskSet / Evidence / Memo / Profile / Pitfall 均已有精简版规范和 Contract；ADR / Change 已有完整规范。
2. **PyTools 校验能力已覆盖全部 7 种对象**：`tools/check_fact_model.py` 已支持 Intent / Task / TaskSet / Evidence / Memo / Profile / Pitfall；`tests/tools/test_check_fact_model.py` 已覆盖 22 个测试用例。
3. **Dogfood 实例已创建**：taskset-0001（核心事实模型 Dogfood）、profile-0001（ld-vibe-harness 项目画像）、memo-0001（22 子文档状态缺口）、pitfall-0001/0002/0003 已实例化。
4. **Skill 已支持新对象类型**：`ldvh-intake` 新增 TaskSet/Memo/Profile 创建分支和 TaskSet 自动归类；`ldvh-close` 新增 TaskSet 关闭、子任务联动、级联检查。
5. **Task 子任务机制已落地**：parent_task/sub_tasks 字段、深度限制两层、关闭前置条件。
6. **Pitfall-0002/0003 已修复并 superseded**：22 主文档与子文档状态矛盾已修复；提交纪律规则重复维护已通过 L0 去重修复（权威位置确定为 22.01-Rules.md）。
7. **specs 文档规范已清理**：32 个 not-created 子文档章节编号补齐，22.02 编号跳跃修复，check_03 问题从 113 降至 0。

---

## 7. 对象边界与 Gstack 借鉴边界

### 7.1 当前对象边界共识

| Object / Concept | 中文 | 当前结论 | 承载方式 |
|---|---|---|---|
| Intent | 意图 | 已落地事实模型 | `ldvh-base/intents/` |
| Task | 任务 | 已落地事实模型 | `ldvh-base/tasks/` |
| TaskSet | 任务集 | 已落地事实模型 | `ldvh-base/tasksets/` |
| Evidence | 证据 | 已落地事实模型 | `ldvh-base/evidence/` |
| Memo | 备忘 | 已落地事实模型 | `ldvh-base/memos/` |
| Profile | 项目画像 | 已落地事实模型 | `ldvh-base/profiles/` |
| ADR | 决策记录 | 已落地事实模型 | `ldvh-base/adrs/` |
| Change | 变更记录 | 已落地事实模型 | Git commit |
| Pitfall | 踩坑记录 | 已落地事实模型 | `ldvh-base/pitfalls/` |
| Risk | 风险 | 降级为字段候选 | Task / Memo / ADR / TaskSet 字段 |
| Dependency | 依赖 | 降级为关系字段 | Task / TaskSet 的 blocked_by、blocks、relation_type 等 |
| Artifact | 产物 | 降级为路径或输出字段 | Evidence artifact_path、Task / TaskSet 输出字段 |
| Checklist | 检查清单 | 降级为模板、字段或 Skill section | Task / TaskSet 验收项，执行结果进入 Evidence |
| Roadmap | 路线图 | 暂作 Markdown 文档 | evals/17、docs 或未来路线图文档 |

### 7.2 Gstack 借鉴边界

Gstack 对 LDVH 的价值主要是流程和产物连续交接，而不是事实对象模型本身。LDVH 当前只吸收以下方向：

1. 阶段化流程：让 AI 知道当前在 Intent、Plan、Execute、Verify、Record、Learn 哪一段；
2. 产物连续交接：前一阶段输出应成为后一阶段输入；
3. 质量门禁前置：测试、检查、review、ship summary 不能只靠最后补救；
4. 角色化审查思路：在必要时用少量高价值 Agent 或 Skill 辅助，而不是一次性创建大量角色；
5. JSONL、ship sections、TODO.md 等只作为流程产物参考，不作为 LDVH 权威事实源。

### 7.3 删除、降级与不吸收清单

当前明确删除、降级或不吸收：

1. 不把 Risk / 风险、Dependency / 依赖、Artifact / 产物、Checklist / 检查清单、Roadmap / 路线图列入当前独立事实模型落地优先队列；
2. 不直接吸收 Gstack 的 browser daemon、remote tunnel、本地隐藏状态目录、runtime cache 或 telemetry 作为权威事实源；
3. 不一次性创建大量 Agent、角色 Skill 或复杂 review army；
4. 不自动发布、自动合并、自动提交；提交仍按 `ldvh-commit` Skill 和 Change 纪律执行；
5. 不把 checklist、artifact、dependency 这类属性型概念强行对象化；
6. 不把 Roadmap / 路线图做成 YAML 对象，除非后续证明它需要独立状态、负责人、完成度统计或 Web 聚合。

---

## 8. 从旧 evals 吸收的长期共识

### 8.1 从原 14 号文档吸收的内容

原 14 号文档的价值在于融合框架论证。本文吸收以下内容：

1. LDVH 提供治理深度，Gstack 提供执行体验，Trae Solo 提供原生运行机制；
2. Core Loop 应成为 AI 第一层入口；
3. 最小事实内核应优先于全对象铺开；
4. 核心 Skill 可围绕 `ldvh-intake`、`ldvh-plan`、`ldvh-execute`、`ldvh-review`、`ldvh-close`、`ldvh-retro` 逐步建设；
5. 四类工具能力应保留为长期方向：Context Primer、Fact Validator、Gate Detector、Evidence Collector；
6. 验证应分级：静态验证（lint / schema）、单元验证（单对象校验）、集成验证（跨对象引用和状态机）、真实交互验证（Web / CLI / 安装）、证据回写（验证结果沉淀为 Evidence）；
7. Web MVP 应服务只读态势和 Human Gate 质量，而不是先成为复杂产品。

### 8.2 从原 15 号文档吸收的内容

原 15 号文档的价值在于 Trae Plan / Spec 定位。本文吸收以下内容：

1. Plan / Spec 是 Trae-native 的规划增强层；
2. Plan 适合中风险任务的轻量前置；
3. Spec 适合系统级复杂任务、重大规范创建或大规模重构；
4. `spec.md` 可映射为 Intent 候选输入；
5. `tasks.md` 可映射为 Task 候选输入；
6. `checklist.md` 可映射为 Evidence 候选输入，但只有执行后的验证结果才形成 Evidence；
7. `.trae/specs/` 是规划态资产，不是权威执行事实源；
8. Plan / Spec 不能替代 LDVH 正式要求的 AskUserQuestion Human Gate。

### 8.3 从原 16 号文档吸收的内容

原 16 号文档的价值在于 specs-v2 删除前价值清单。本文吸收以下内容：

1. Memo 是高价值对象，用于承载尚未任务化但有保留价值的输入、发现和提醒；
2. Profile 是高价值对象，用于承载项目身份、路径映射、项目名册和安装配置体验；
3. 初始化流程是产品化接入的关键能力；
4. 审计流程是项目治理和长期维护的关键能力；
5. 开发实践规范应明确 AI 如何启动、检查、验证和汇报开发完成情况；
6. 交付实践规范应明确发布前检查、发布后验证、回滚方案和发布记录；
7. 推荐 Agent 清单只能作为候选池，不应一次性创建大量 Agent；
8. specs-v2 内容必须完成术语适配，不能原样复制。

---

## 9. 下一步主线

### 9.1 当前真正下一步：补齐 Change / Record 闭环

当前下一步不再是"创建 Fact Validator Spec"，也不再是"证明最小事实内核能否跑通"。这些已经有初步成果。

当前真正下一步是：

```text
明确 Change 在 Record 阶段的最小承载方式
```

需要回答的问题是：

1. Change 的最小事实源是否继续以 Git commit message 为主？
2. `ldvh-close` 关闭 Task 时，是否必须产生 Change 摘要？
3. `ldvh-commit` 提交时，如何消费 Task / Evidence / ADR 信息形成 Change 记录？
4. Task 的 `related_changes` 当前为空时，是否影响关闭判断？
5. 是否需要 `ldvh-base/changes/` YAML 实例目录？
6. 如果需要新增 Change YAML，是否必须先通过 ADR 决策事实源归属变化？
7. 如果暂不新增 Change YAML，Evidence、Task closure、commit message 三者如何共同支撑 Record 阶段完成判断？

本文建议短期采用过渡策略：

```text
Change 暂以 specs/22 定义的 Git commit message / ldvh-commit / check_22_commit_format.py 为主承载；
Task closure 和 Evidence 中保留足够摘要；
暂不直接新增 ldvh-base/changes/ YAML；
若未来决定实例化 Change YAML，应先进入 ADR 或正式规范升级流程。
```

### 9.2 第二步：固化执行中发现问题的分流规则

Dogfood 过程中已经暴露一个更普遍的问题：执行主线 Task 时，AI 会发现 bug、规范缺口、工具缺口、流程缺口或新机会。

需要形成最小分流规则：

| 类型 | 判断 | 建议动作 |
|---|---|---|
| blocking | 不解决则当前 Task 无法完成 | 暂停当前 Task，创建或切换阻塞 Task |
| follow-up | 当前 Task 可完成，但后续应处理 | 当前 Task 可关闭，创建关联后续 Task |
| opportunistic fix | 当前 Task 范围内可低风险修复 | 在当前 Task 中修复并记录 Evidence |
| ADR candidate | 改变长期边界或协作方式 | 进入 ADR 判断，不直接当作临时修复 |
| Pitfall candidate | 属于可复发错误模式 | 先记录 Evidence / 后续 Pitfall 候选 |
| Memo candidate | 有保留价值但尚未任务化 | 创建 Memo 承载 |

这条规则会直接提升 Execute、Verify、Record 三阶段的稳定性。

### 9.3 第三步：继续推进 PyTools 标准化

Fact Validator 已经是可用的最小工具，但还不是最终工具体系。

后续 PyTools 应按以下顺序推进：

1. 固化 Issue 输出格式、退出码、CLI 参数、只读/写入边界；
2. 将 `check_fact_model.py` 作为 PyTools 标准样板；
3. 逐步补 Reference Validator 和 State Machine Validator；
4. 逐步从内置常量转向消费 Contract；
5. 旧工具按触碰即整理原则迁移；
6. Web 只读聚合优先消费 PyTools 输出，而不是直接复杂解析所有事实源。

### 9.4 第四步：补齐最小 Plan / Verify 入口

Core Loop 当前最弱的是 Plan、Execute、Verify、Learn。

不建议一次性创建全部 Skill。建议优先补：

1. `ldvh-plan`：围绕 Task 形成执行计划、风险、验证命令和 Human Gate 判断；
2. `ldvh-verify`：统一 lint、typecheck、test、build、真实交互验证和 Evidence 草案；
3. Execute 阶段先由 Rules + Task 状态 + 人工执行承接；
4. Learn 阶段待 Pitfall / Memo 压力更明显后再建设。

### 9.5 第五步：吸收 Gstack Skill Prompt 经验并设计生命周期 Skill

Gstack 的 Skill prompt 不是简单的"角色 Skill 目录"，其中包含大量值得 LDVH 吸收的工程经验。后续应专门从 Gstack 的 `review`、`qa`、`ship`、`retro`、`learn`、`plan-tune`、`spec`、`skillify` 等 Skill 中提炼提示词结构。

优先吸收的 prompt 经验包括：

1. **入口判断**：`When to invoke this skill`、触发词、主动建议条件、禁用条件；
2. **工具边界**：allowed tools、Plan Mode safe operations、Skill Invocation During Plan Mode；
3. **前置探测**：分支、仓库模式、配置、历史 learnings、上下文恢复和能力探测；
4. **Human Gate 表达**：AskUserQuestion 的触发条件、选项设计、STOP 点和继续条件；
5. **流程步骤**：Step 化执行、每步输入、动作、产物、失败处理和交接；
6. **质量门禁**：scope drift、plan-completion review、真实 QA、测试证据、release gate；
7. **输出契约**：最终报告、TODO 格式、PR body、测试摘要、复盘报告、学习记录；
8. **经验回灌**：learnings、timeline、retro、question tuning、developer profile 等跨会话改进机制。

结合 Trae 官方最佳实践，LDVH 设计自有 Skill 时还应补充以下原则：

1. **元数据即入口**：Skill 的 `name` 和 `description` 直接影响模型发现与触发准确率；
2. **边界优先**：每个 Skill 必须明确 Use when 和 Do NOT use when；
3. **输入输出结构化**：用类似函数签名的方式定义 Input / Output；
4. **步骤必须可执行**：Skill 的步骤应是具体指令，而不是概括性描述；
5. **失败策略显式化**：验证失败、输入缺失、依赖不可用等场景应有明确停止、重试、回退或上报规则；
6. **职责绝对单一**：单个 Skill 只解决一个核心动作；
7. **渐进式披露**：`SKILL.md` 作为入口和导航，保持最小必要信息；
8. **工作流与反馈闭环**：复杂 Skill 应显式定义计划、验证、执行、再验证的检查清单；
9. **脚本输出自解释**：Skill 依赖的脚本必须失败可预期、输出可理解、参数可解释；
10. **评测驱动、失败优先**：先建立无 Skill 基线和失败用例，再写最小化 Skill。

建议下一批生命周期 Skill 的设计顺序为：

1. `ldvh-spec`：负责需求澄清、规格草案、验收标准、Human Gate 选项和事实源归属判断；
2. `ldvh-plan`：吸收 Gstack plan / spec / review 的任务澄清、风险识别、scope drift 和验证计划表达；
3. `ldvh-verify`：吸收 Gstack QA 的真实验证、分级检查、修复后复验和证据摘要；
4. `ldvh-review`：吸收 Gstack review 的 diff 审查、结构性问题、trust boundary 和 pre-landing gate；
5. `ldvh-retro`：吸收 Gstack retro / learn 的经验沉淀、趋势复盘和可执行改进；
6. `ldvh-close` 继续强化：吸收 ship / release gate 的完成判断、变更摘要和交付前检查。

### 9.6 第六步：明确 Spec / Plan 与自有 Skill 的协同边界

Trae Solo 的原生 `/spec` 和 `/plan` 不能被普通 Skill 在内部程序化调用。它们属于用户主动触发的交互层工作流，拥有普通 Skill 不具备的平台特权。

推荐协同模式如下：

1. 复杂需求短期可由用户触发 `/spec`，确认规格后，再触发 `ldvh-intake`、`ldvh-plan` 或后续执行类 Skill；
2. 复杂工程任务短期可由用户触发 `/plan`，确认计划后，再由 LDVH Skill 按计划执行、验证和记录；
3. 简单、稳定、生命周期化的行动可以直接触发对应 LDVH Skill，不强制进入 Spec / Plan；
4. Skill 可以消费 Spec / Plan 产物作为输入上下文，但不能在内部触发 `/spec` 或 `/plan`；
5. Spec / Plan 的用户确认不自动替代 LDVH 的 Human Gate、ADR、Evidence 或 Change 记录；
6. 自有 `ldvh-spec` / `ldvh-plan` 的目标不是复制原生 Spec / Plan，而是把规格、计划、验收、验证和任务推进治理化。

### 9.7 第七步：Web MVP 只读对齐 `ldvh-base`

`pm-kit-web/` 已有工作台原型，但当前尚未对齐 LDVH 新事实内核。

下一步 Web 不应先做写入，而应先做只读聚合：

1. 展示 Intent / Task / Evidence / ADR 状态；
2. 展示 Task 关闭证据与验证结果；
3. 展示 Fact Validator 输出；
4. 展示待 Human Gate 的对象；
5. 展示 Change / commit 摘要；
6. 为用户提供更高质量的 Human Gate 上下文。

Web MVP 的定位仍是：

```text
Git 文件事实源 → PyTools 聚合 → Web 只读展示 → 人做更高质量 Human Gate
```

---

## 10. 优先级原则

后续行动如出现分支，应按以下原则排序：

1. **先入口，后深度**：先让 AI 知道当前阶段和下一步，再补复杂治理；
2. **先兼容原生规划，后沉淀自有 Skill**：复杂需求和复杂工程任务短期可消费原生 Spec / Plan 产物，长期应由 `ldvh-spec`、`ldvh-plan` 等自有 Skill 承接治理化规格、计划和验收流程；
3. **先生命周期 Skill，后角色目录**：符合 Core Loop、输入输出稳定、高频复用的流程优先 Skill 化；需要上下文装配、工具授权、流程约束、Human Gate 和产物契约的稳定行动入口应进入 Skill 候选；临时角色优先运行时视角切换；
4. **先核心闭环，后扩展对象**：先稳定 Intent / Task / ADR / Evidence / Change，再扩展 Risk / Memo / Dependency / Artifact / Checklist / TaskSet；
5. **先 Record / Change，后 Web 写入**：没有可追溯变更记录之前，不应扩大写入入口；
6. **先 Contract 消费，后复杂自动化**：先让 PyTools 能读契约校验事实，再做自动修复、受控写入和 Web 展示；
7. **先 Dogfood，后产品扩张**：先在 LDVH 自身验证 Core Loop，再考虑外部用户安装体验；
8. **先 Trae-native，后外部依赖**：优先使用 Trae 原生机制，不急于引入外部 daemon 或复杂 CLI；
9. **先可解释，后自动化**：所有自动化必须能解释依据、来源和影响范围；
10. **先低风险信任边界，后高成本安全栈**：先做 untrusted envelope、allowlist、scoped token，再考虑复杂模型检测。

---

## 11. 不做什么

为避免偏离主线，当前明确不做：

1. 不照搬 Gstack 的 Claude Code Skill 结构；
2. 不引入 `~/.ldvh/` 本地隐藏状态目录作为稳定事实源；
3. 不按人格化角色目录一次性创建大量 Skill 或 Agent；
4. 不把临时专业视角固化为默认 Skill；
5. 不把 Skill 写成一次性 Prompt 或写给人看的长说明；
6. 不在 Tools 中调用 AI、Skill 或 Agent；
7. 不把 Memory 当作 Git 文件事实源的替代品；
8. 不自动发布、自动提交、自动合并；
9. 不先做复杂 Web 产品再验证 Core Loop；
10. 不在没有 Contract 消费规则的情况下扩张 PyTools；
11. 不把 `.trae/specs/` 变成第二套权威状态；
12. 不让 Skill 内部触发 `/spec` 或 `/plan`；
13. 不把 Plan / Spec 确认当作正式 Human Gate 的替代品；
14. 不把 Gstack 的 telemetry、auto-update、browser tunnel、pair-agent 作为默认能力；
15. 不让子 Agent 绕过主控、Human Gate、事实源写入和 Change 记录；
16. 不为了未来可能需要的对象而打断当前最小闭环。

---

## 12. 长期约束

> 回流状态：本节第 2-4 条已回流到 11 系列正式规范，分别由 `specs/11-LDVH-AI协作规范.md`、`specs/11.01-Rules机制规范.md` 和 `specs/11.02-Skill机制规范.md` 承接；本文保留为产品方向入口摘要，不替代正式规范。

1. Skill 提示词、Skill 文档和面向 AI 的 Skill 编排说明应使用中文，除非外部平台字段或技术标识必须使用英文。
2. 涉及规范、Rules、Skill、Agent、Tools、事实模型、状态机、部署边界或目录边界的判断，AI 不得只凭记忆、目录现状或经验推断；必须先定位并读取对应规范原文，再给出结论。
3. 当 AI 发现自己依赖了错误记忆、跳过规范原文、混淆层级或误判部署边界时，应把该错误转化为可执行检查项：明确触发场景、必读原文、检查顺序和停止条件。
4. LDVH 的价值不在于要求 AI 永远不犯错，而在于把已发现的错误模式沉淀为 Rules、Skill、Tools 或事实源检查，降低同类错误复发概率。

---

## 13. 防递归建设原则

LDVH 当前处于"用框架完善框架"阶段。该阶段必须防止递归死循环：为了完善框架不断要求先补更多框架能力，导致永远无法进入真实使用和产品验证。

### 13.1 核心原则

1. **框架建设必须服务最近一次可运行闭环**：每次新增规范、Skill、Tools 或对象，都必须说明它服务哪个已定义闭环，不能只服务未来假想能力；
2. **只补当前闭环的最小缺口**：不得因为发现更大体系缺口而扩张当前任务边界；
3. **Dogfood 优先于继续抽象**：当某个闭环具备最小可运行条件时，优先用 LDVH 自身跑一次，而不是继续补规范；
4. **一层抽象后必须落地一次**：每新增一层抽象（规范、对象、Skill、Tools 分类），必须安排一个实例化验证；
5. **禁止无限前置条件**：不得把"先补另一个规范/工具/对象"作为默认阻塞，除非它是当前闭环不可运行的硬阻塞；
6. **先人工可运行，再工具自动化**：流程先允许 AI + Human Gate 手动跑通，再考虑 PyTools 自动校验或 Web 展示。

### 13.2 递归停止规则

当出现以下信号时，应停止继续扩张框架，转入实例验证或 Dogfood：

1. 连续两个任务都在新增规范，而没有创建或验证任何事实实例；
2. 当前任务的输出无法被 Intent / Task / Evidence / Change 之一承载；
3. 新增能力不能改善 AI 进入、执行、验证、沉淀或演进中的任一环节；
4. 需要新增第三个前置规范才能完成当前规范；
5. 讨论开始围绕"为了建框架还需要什么框架"而不是"如何跑通下一个闭环"。

### 13.3 当前适用的最小闭环

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

### 13.4 Web 最小展示入口

Web 展示应纳入 MVP，但必须限定为只读的最小态势入口，避免提前演变成复杂 Web 产品分支。

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

---

## 14. 固定沟通起点

本文在 LDVH 产品完成前作为产品方向入口文档。后续涉及 LDVH 产品化、Gstack 借鉴、Trae Solo 利用、Core Loop、PyTools、事实模型、Skill、Rules、Agent、Web、Plan / Spec、安装配置体验或 evals 清理的任务，应优先回到本文确认主线。

后续如果发现重要共识、关键决策、方向修正、长期约束、产品定位变化或可能导致行动分支漂移的内容，应更新本文进行记录，避免跨会话遗忘。

后续如果出现方向不清，应回到本文确认：

1. 当前行动是否服务于 Gstack 思想完善 LDVH？
2. 当前行动是否推动 LDVH 成为更适合 Vibe Coding 的产品？
3. 当前行动是否利用了 Trae Solo 原生机制？
4. 当前行动是否强化了 Core Loop？
5. 当前行动是否避免了事实源漂移？
6. 当前行动是否提升了 AI 进入、执行、验证、沉淀或演进能力？
7. 当前行动是否让 Change / Evidence / Task / ADR 的关系更清晰？
8. 当前行动是否避免了为了框架继续堆框架？

如果答案是否定的，应暂停该分支，重新评估是否进入 ADR、Task、Memo 候选或推迟。
