# 融合 LDVH、Gstack 与 Trae Solo 的 Vibe Coding 框架评估（AI 视角）

> 创建日期：2026-06-03
> 定位：LD Vibe Harness 面向"融合 LDVH、Gstack 与 Trae Solo 打造更适合 Vibe Coding 的框架"的 AI 视角评估
> 调研边界：不直接构成强制规则
> 执行效力：无，结论需进入 00-79 正式规范区间或 ADR 后才成为稳定规则
> 上位依据：`specs/00-LD-Vibe-Harness理念与纲要.md`
> 相关参考：`specs/evals/02-LDVH对gstack的借鉴评估.md`、`specs/evals/13-LDVH假设重来视角下对gstack的借鉴再评估.md`

---

## 1. 本文解决的问题

本文从 AI 执行者视角评估：如果吸收 LDVH 和 Gstack 各自的优势，并充分利用 Trae Solo 环境的原生机制，能否打造一个比现有方案更适合 Vibe Coding 的框架？如果能，它应该长什么样？

本文不是正式规范，不直接改变 LDVH 的事实模型、行动模型、Rules、Skill、Tools 或 Human Gate 要求。

---

## 2. AI 视角下的三方优劣势

### 2.1 LDVH：AI 最需要的治理深度

作为 AI 执行者，LDVH 给我最大的价值是：

1. **我知道该读什么**：L0/L1/L2 Rules 分层告诉我进入项目后先读哪个文件、读哪个章节、读多少行；
2. **我知道不能做什么**：硬约束、Human Gate、状态机、事实源边界让我不会越界；
3. **我知道写回哪里**：Git 文件事实源、Change 记录、Evidence 回写让我不会把结论丢在聊天里；
4. **我知道怎么验证**：V1-V10 价值标准让我知道"做完了"不等于"做对了"。

但 LDVH 当前对 AI 来说也有明显的痛点：

| 痛点 | AI 的感受 |
|---|---|
| 入口复杂度高 | 进入项目后面对大量 specs，不知道从哪里开始行动 |
| 闭环停留在文本 | 00 定义了闭环，但我执行时没有 Skill 引导我走完闭环 |
| 事实模型太多 | Intent、TaskSet、Task、Memo、ADR、Risk、Dependency、Evidence、Artifact、Checklist、Change、Pitfall……我一开始不需要面对全部 |
| 工具能力不足 | 我每次都要手动拼凑上下文、手动校验、手动回写，没有工具帮我 |
| 门禁只靠自律 | Human Gate 写在规范里，但没有工具在我即将越界时主动拦我 |

### 2.2 Gstack：AI 最想要的执行体验

作为 AI 执行者，Gstack 给我最大的价值是：

1. **流程即入口**：我不需要先理解完整治理理论，通过一个 Skill 就能进入流程；
2. **阶段即约束**：Think → Plan → Build → Review → Test → Ship → Reflect，每个阶段都有明确输入、输出和检查；
3. **角色即视角**：CEO、Eng、Design、QA、CSO 等角色帮我从不同维度审视同一件事；
4. **验证即证据**：QA、浏览器测试、截图、部署验证不是事后补丁，而是主流程的一部分；
5. **记忆即连续**：context-save / restore、learnings、gbrain 让我跨会话保持连续性。

但 Gstack 对 AI 来说也有明显的问题：

| 问题 | AI 的感受 |
|---|---|
| 平台绑定 | 我在 Trae 里无法直接使用 Claude Code Skill 结构 |
| 事实源模糊 | 很多稳定结论存在 ~/.gstack/ 或聊天记忆里，不在 Git 里 |
| 角色过重 | 不是每个场景都需要独立 Agent，有时我只需要一个检查清单 |
| 本地状态漂移 | learnings、timeline、gbrain 和 Git 事实源可能不一致 |
| 安全依赖自律 | careful / freeze / guard 是提示词纪律，不是环境约束 |

### 2.3 Trae Solo：AI 实际运行的原生环境

作为 AI 执行者，Trae Solo 给我的原生能力是：

| 机制 | AI 能用它做什么 |
|---|---|
| Rules | 始终生效的约束，告诉我必须遵守什么、不能做什么、进入哪个场景读什么 |
| Skill | 按需加载的流程，告诉我遇到某类任务时如何稳定执行 |
| Agent | 独立上下文、并行分析、结论隔离的专业角色 |
| Tools | 确定性校验、聚合、上下文包生成、受控写入 |
| AskUserQuestion | 向用户展示结构化选择题，实现 Human Gate |
| RunCommand | 执行终端命令、构建、测试、部署 |
| Web Preview | 启动本地服务器、预览网页 |
| Schedule | 定时任务、周期性自动化 |
| Memory | 跨会话记忆（但不应替代 Git 事实源） |

Trae 的关键优势是：**这些机制是原生可用的，不需要额外安装 daemon 或 CLI。** 但 Trae 本身不告诉我"应该怎么组织 Vibe Coding 的完整生命周期"——这正是 LDVH + Gstack 思想要补的。

---

## 3. AI 视角下的融合框架设计

### 3.1 设计原则

从 AI 执行者视角，融合框架应遵循以下原则：

1. **AI 进入速度优先**：AI 进入项目后 30 秒内，应知道现在该干什么、该读什么、不能干什么、完成后写回哪里；
2. **主闭环优先**：先呈现 3-5 条可运行主闭环，而不是先呈现完整规范体系；
3. **最小事实内核**：AI 先面对 5 类核心对象（Intent、Task、ADR、Evidence、Change），不是 12+ 类；
4. **使用即流程**：正确行为应被包装成 AI 最容易执行的默认路径，而不是只靠规范约束；
5. **门禁工具化**：Human Gate 应从"提示词纪律"升级为"环境约束"；
6. **验证分级**：从静态检查到真实交互验证，验证不能只停留在代码层面；
7. **事实源权威**：所有稳定事实最终回到 Git 文件，工具输出、网页视图、缓存、记忆只是辅助；
8. **Trae-native**：用 Trae 原生机制表达一切，不引入外部 daemon、CLI 或本地隐藏状态。

### 3.2 融合框架的核心架构

```text
┌─────────────────────────────────────────────────────┐
│                  Core Loop（主闭环）                  │
│  Intent → Plan → Execute → Verify → Record → Learn  │
├─────────────────────────────────────────────────────┤
│              最小事实源内核（5 类对象）                │
│  Intent · Task · ADR · Evidence · Change             │
├─────────────────────────────────────────────────────┤
│              核心 Skill（6 个流程入口）                │
│  intake · plan · execute · review · close · retro    │
├─────────────────────────────────────────────────────┤
│              工具层（4 类确定性能力）                  │
│  Context Primer · Fact Validator · Gate Detector     │
│  Evidence Collector                                  │
├─────────────────────────────────────────────────────┤
│              Trae 原生机制承载层                      │
│  Rules · Skill · Agent · Tools · AskUserQuestion     │
│  RunCommand · Web Preview · Schedule · Memory        │
└─────────────────────────────────────────────────────┘
```

### 3.3 Core Loop：AI 的行动主线

这是 Gstack 的 `Think → Plan → Build → Review → Test → Ship → Reflect` 在 LDVH + Trae 语境下的重新表达：

```text
Intent → Plan → Execute → Verify → Record → Learn
```

| 阶段 | AI 应该做什么 | 对应 LDVH 价值 | 对应 Trae 机制 |
|---|---|---|---|
| Intent | 识别用户意图，判断场景，创建或关联 Intent 对象 | V1 快速定位、V3 正确判断 | Rules 场景入口、Skill 触发 |
| Plan | 拆解任务、评估风险、检查事实源、Human Gate 确认 | V3 正确判断、V5 门禁识别 | AskUserQuestion、Skill 流程 |
| Execute | 按计划实施，遵守约束，限定编辑范围 | V4 稳定执行 | RunCommand、Skill 流程、Rules 约束 |
| Verify | lint / typecheck / test / build / 真实交互验证 | V6 强制验证 | RunCommand、Web Preview、Tools 校验 |
| Record | Evidence 回写、Change 记录、状态更新 | V7 证据沉淀、V8 可靠回写 | Tools 受控写入、Skill 回写流程 |
| Learn | Pitfall 沉淀、Rule 改进、工具改善建议 | V10 持续完善 | Skill 复盘流程、Tools 缺口报告 |

这条主线应成为 README、00、L1 Rules、Skill routing 和 Web Tools 的共同核心。

### 3.4 最小事实源内核

借鉴 `specs/evals/13-LDVH假设重来视角下对gstack的借鉴再评估.md` §5.2，AI 先面对 5 类核心对象：

```text
Intent → Task → Change
          ↓
       Evidence
          ↓
    Decision / ADR
```

| 对象 | AI 需要知道的 | 来源 |
|---|---|---|
| Intent | 用户想要什么、约束是什么、成功标准是什么 | LDVH 事实模型 |
| Task | 我要做什么、当前状态、验收标准、回写目标 | LDVH 事实模型 |
| ADR | 关键决策是什么、为什么这样决定、是否已 accepted | LDVH 事实模型 |
| Evidence | 验证结果是什么、在哪里验证的、证据是什么 | LDVH 事实模型 |
| Change | 实际改了什么、为什么改、影响范围 | LDVH 事实模型 |

扩展对象（Risk、Dependency、Checklist、Artifact、Memo、Pitfall、TaskSet）按痛点启用，不作为 AI 的第一体验。

### 3.5 核心 Skill

借鉴 Gstack 的 Skill 工厂思想，但更克制（依据 `specs/evals/13-LDVH假设重来视角下对gstack的借鉴再评估.md` §6.1），先建设 6 个核心 Skill：

| Skill | 触发场景 | AI 做什么 | Human Gate |
|---|---|---|---|
| ldvh-intake | 用户表达意图 | 识别场景、创建 Intent / Task 草案、关联事实源 | 创建前确认 |
| ldvh-plan | Task 进入 planning | 拆解步骤、评估风险、检查事实源、多视角审视 | 计划确认 |
| ldvh-execute | Task 进入 executing | 按计划实施、限定编辑范围、遵守约束 | 高风险操作前 |
| ldvh-review | Task 进入 review | 检查 Evidence、校验字段、验证引用完整性 | 关闭前确认 |
| ldvh-close | Task 满足关闭条件 | closure_evidence 校验、Change 记录、状态回写 | 关闭确认 |
| ldvh-retro | Task 关闭后 | Pitfall 沉淀、Rule 改进建议、工具改善建议 | 改进建议确认 |

每个 Skill 应明确：触发场景、必读事实源、Human Gate 判断、允许工具、验证要求、回写目标、STOP 条件。

### 3.6 工具层

借鉴 Gstack 的工具降低执行摩擦的思想，但按 LDVH Tools 辅助层边界设计（依据 `specs/12.01-Tools辅助规范.md` §4），优先建设 4 类工具：

| 工具 | 解决的 AI 痛点 | 对应 LDVH 价值 |
|---|---|---|
| Context Primer | AI 每次进入项目都要手动拼凑上下文 | V1 快速定位、V2 完整理解 |
| Fact Validator | AI 修改 YAML 后没有即时校验反馈 | V6 强制验证 |
| Gate Detector | AI 不知道当前操作是否触发 Human Gate | V5 门禁识别 |
| Evidence Collector | AI 完成任务后证据散落在聊天记录中 | V7 证据沉淀 |

这四类工具直接解决 AI 在 Vibe Coding 中最常遇到的四个断裂点：找不到入口、改错了不知道、越界了没拦住、做完了没证据。

---

## 4. AI 视角下的三方融合细节

### 4.1 从 LDVH 吸收什么

| LDVH 能力 | AI 视角价值 | 融合方式 |
|---|---|---|
| V1-V10 价值标准 | 我知道"做完了"不等于"做对了" | 作为框架的验收标准，每个 Skill 和工具都应服务至少一项 |
| L0/L1/L2 Rules 分层 | 我知道进入项目后先读什么 | 保留，但增加 Context Primer 自动装配 |
| 事实源边界 | 我知道稳定事实必须回到 Git | 保留为硬边界，不妥协 |
| Human Gate | 我知道何时必须停下来问人 | 保留，但升级为 Gate Detector 工具化 |
| 状态机 | 我知道对象能从什么状态变到什么状态 | 保留，但通过 Fact Validator 自动校验 |
| Contract 子文档 | 我知道字段契约和引用关系 | 保留，作为 Fact Validator 的输入 |
| Change 记录 | 我知道每次变更都要留痕 | 保留，通过受控写入工具自动生成 |

### 4.2 从 Gstack 吸收什么

| Gstack 能力 | AI 视角价值 | 融合方式 |
|---|---|---|
| 阶段化工程流程 | 我不需要自由发挥，被引导到正确阶段 | 改写为 Core Loop，用 Skill 承载 |
| 计划先行门禁 | 我不会在没想清楚时就动手 | 改写为 ldvh-plan Skill + AskUserQuestion |
| 角色化审查 | 我能从多个维度审视同一件事 | 先作为检查清单（51 多角色思考），必要时才升级 Agent |
| 结构化决策卡片 | 我向用户展示决策时更清晰 | 改写为 AskUserQuestion 的 ELI10 + Stakes + Pros/Cons 格式 |
| 真实环境 QA | 我的验证不只是 lint，还有真实页面 | 改写为验证分级 + Evidence Collector |
| context-save / restore | 我跨会话不会丢失上下文 | 改写为 Context Primer + Git 事实源，不用本地隐藏状态 |
| learn / retro | 我能从错误中学习 | 改写为 ldvh-retro Skill + Pitfall / Change 回写 |
| careful / freeze / guard | 我不会做破坏性操作 | 改写为 Gate Detector + Rules 约束 + 受控写入 |

### 4.3 利用 Trae Solo 环境的什么

| Trae 机制 | 在融合框架中的角色 | 替代 Gstack 的什么 |
|---|---|---|
| Rules（alwaysApply） | L0 工作区桥接、项目识别、必读入口 | Gstack 的 Skill preamble 自动装配 |
| Rules（globs） | L2 场景约束，编辑特定文件时自动生效 | Gstack 的 careful / freeze 触发 |
| Skill | 承载 Core Loop 的 6 个流程入口 | Gstack 的 Skill 工厂（但更克制） |
| Agent | 独立上下文的多角色并行分析 | Gstack 的角色 Agent（但只在必要时创建） |
| AskUserQuestion | Human Gate 的技术实现 | Gstack 的 AskUserQuestion 格式 |
| RunCommand | lint / typecheck / test / build / deploy | Gstack 的 CLI 工具 |
| Web Preview | 真实页面预览和交互验证 | Gstack 的浏览器 daemon（轻量替代） |
| Tools（Python） | 确定性校验、聚合、上下文包、受控写入 | Gstack 的 bin/ CLI 工具（但按 LDVH 边界设计） |
| Schedule | 周期性审计、健康检查、自动化 | Gstack 的 timeline / analytics |
| Memory | 跨会话偏好和项目上下文（辅助，不替代 Git） | Gstack 的 ~/.gstack/ 本地状态（降级为辅助） |

---

## 5. AI 视角下的关键设计决策

### 5.1 为什么 Core Loop 是第一层

AI 在 Vibe Coding 中最大的问题不是"不知道规范"，而是"不知道现在该干什么"。

Gstack 的核心洞察是：**把正确行为包装成 AI 最容易执行的默认路径。** 当 AI 进入一个 Skill 时，它不需要先理解完整治理理论，只需要按步骤执行。

LDVH 的核心洞察是：**规范必须存在，但不应成为 AI 的第一体验。** AI 先获得目标、边界、事实、状态、验收标准和工具入口，而不是先处理 12+ 类对象分类。

融合后的 Core Loop 把两者结合：

```text
AI 进入项目 → Context Primer 自动装配最小上下文 → Core Loop 告诉 AI 当前阶段 → Skill 引导 AI 执行 → Tools 辅助 AI 校验和回写 → Git 事实源沉淀稳定事实
```

### 5.2 为什么最小事实内核只有 5 类

AI 第一服务对象原则（00 §3.2）要求：先按照 AI 能快速定位、完整理解、正确判断、稳定执行、强制验证和可靠回写的方式组织项目。

12+ 类对象对 AI 来说是认知过载。5 类核心对象足以形成最小闭环：

```text
Intent → Task → Change
          ↓
       Evidence
          ↓
    Decision / ADR
```

其他对象按痛点启用。当 AI 遇到风险判断需求时，Risk 自然出现；当 AI 需要任务分组时，TaskSet 自然出现。不是一开始就摆出所有对象。

### 5.3 为什么角色先做检查清单而不是 Agent

Gstack 的 CEO / Eng / QA / CSO 角色很诱人，但从 AI 视角看：

1. **大多数场景不需要独立上下文**：AI 在主上下文中就能完成多视角审视；
2. **Agent 有调度成本**：每次创建子 Agent 都需要传递上下文、等待返回、合并结论；
3. **检查清单更灵活**：AI 可以在主流程中按清单逐项检查，不需要切换上下文；
4. **升级路径清晰**：当检查清单确实不够用（需要并行、需要隔离、需要不同权限），再升级为 Agent。

所以融合框架中的角色化审查路径是：

```text
检查清单（Rules / Skill 内嵌） → 多角色思考（51 行动模型） → 必要时 Agent（11.03 准入门槛）
```

### 5.4 为什么 Human Gate 要工具化

当前 LDVH 的 Human Gate 主要靠 Rules 提醒和 AI 自律。但从 AI 视角看：

1. **AI 不会每次都记得检查**：当 AI 专注于执行时，容易忽略门禁提醒；
2. **工具可以主动拦**：Gate Detector 可以在 AI 即将修改 specs / Rules / ADR / ldvh-base/ 时主动提示；
3. **工具可以结构化呈现**：不是简单说"需要 Human Gate"，而是展示 ELI10、Stakes、Recommendation、Pros/Cons；
4. **工具可以记录**：每次 Human Gate 触发和用户选择都可以成为 Evidence。

这让 V5 门禁识别从"提示词纪律"升级为"环境约束"。

### 5.5 为什么验证要分级

Gstack 的浏览器 QA 解决的是"真实环境验证"问题。但从 AI 视角看：

1. **不是每次都需要浏览器**：lint 和 test 就能覆盖大部分验证；
2. **但有时只有浏览器不够**：部署后的真实交互、登录态、表单提交需要真实环境；
3. **验证结果必须沉淀**：无论哪级验证，结果都应进入 Evidence。

所以融合框架将验证分为 5 级：

| 级别 | 验证方式 | Trae 机制 | 证据形式 |
|---|---|---|---|
| L1 静态 | lint、typecheck、格式检查、schema 检查 | RunCommand | 命令输出 |
| L2 单元 | test、pytest、go test 等 | RunCommand | 测试报告 |
| L3 集成 | 服务启动、API 调用、数据库迁移 | RunCommand + Web Preview | 运行日志 |
| L4 真实交互 | 浏览器、截图、表单、登录态 | Web Preview + Playwright MCP | 截图 + 交互记录 |
| L5 证据回写 | 命令输出、截图、日志摘要、失败原因进入 Evidence | Tools 受控写入 | Evidence YAML |

### 5.6 为什么记忆要用 Trae Memory 而不是 ~/.gstack

Gstack 的 ~/.gstack/ 本地状态对跨会话连续性有价值，但从 AI 视角看：

1. **本地隐藏状态与 Git 事实源可能不一致**：AI 不知道该信哪个；
2. **Trae Memory 是原生机制**：不需要额外安装，不需要维护同步逻辑；
3. **但 Memory 不替代 Git**：Memory 是辅助层，稳定事实仍在 Git 文件中。

融合框架的记忆分层：

```text
Git 文件事实源 = 权威层（最终真相）
Trae Memory    = 辅助层（跨会话偏好、项目上下文摘要）
Tools 缓存     = 加速层（按需计算、可重建）
聊天记录       = 证据候选（不是事实）
```

---

## 6. 融合框架与纯 LDVH、纯 Gstack 的对比

| 维度 | 纯 LDVH | 纯 Gstack | 融合框架 |
|---|---|---|---|
| AI 进入速度 | 慢（需读大量 specs） | 快（Skill 自动装配） | 快（Context Primer + Core Loop） |
| 治理深度 | 深（V1-V10、状态机、Contract） | 浅（靠 Skill 自律） | 深（保留 LDVH 治理 + 工具化） |
| 事实源权威 | 强（Git 文件） | 弱（本地状态 + 聊天） | 强（Git 文件 + Memory 辅助） |
| 执行摩擦 | 高（手动拼凑上下文） | 低（Skill 引导） | 低（Skill + Tools 辅助） |
| Human Gate | 靠 Rules 提醒 | 靠 Skill STOP point | 工具化（Gate Detector） |
| 验证深度 | 依赖 AI 自觉 | 浏览器 QA 强 | 分级验证 + Evidence 回写 |
| 角色化 | 无（或 Agent 过重） | 强（角色 Skill/Agent） | 检查清单 → 多角色思考 → 必要时 Agent |
| 平台适配 | Trae-native | Claude Code 绑定 | Trae-native |
| 复盘能力 | Pitfall / Change 规范完整 | learn / retro 实践导向 | 两者结合：规范 + 流程 + 工具 |

---

## 7. AI 视角下的实施优先级

### P0：让 AI 不再盲

当前 AI 进入 LDVH 项目后最大的痛点是"找不到入口、不知道该干什么"。

1. **Context Primer**：AI 进入项目时自动获得最小可行动上下文（当前项目、当前场景、当前事实源边界、当前任务状态、当前 Human Gate 风险、当前推荐 Skill / 流程、当前必须验证命令、当前回写目标）；
2. **Core Loop 主线**：README、L1 Rules、Skill routing 围绕同一条主线表达：Intent → Plan → Execute → Verify → Record → Learn；
3. **最小事实内核**：先稳定 Intent、Task、ADR、Evidence、Change 五类对象，其他按痛点启用。

### P1：让 AI 不再越界

当前 Human Gate 靠 Rules 提醒和 AI 自律，AI 容易忽略。

1. **Gate Detector**：在 AI 即将修改 specs / Rules / ADR / ldvh-base/ 时主动提示，结构化展示 ELI10 + Stakes + Pros/Cons；
2. **Fact Validator**：AI 修改 YAML 后即时校验字段、状态机、引用完整性；
3. **Scope Freeze**：任务执行期间限定 AI 只能编辑某些目录或文件类型。

### P2：让 AI 不再丢证据

当前 AI 完成任务后证据散落在聊天记录中。

1. **Evidence Collector**：自动收集 lint / test / build 输出，生成 Evidence 候选；
2. **受控写入工具**：多文件事务写入 + 写入前校验 + Change 记录自动生成；
3. **ldvh-close Skill**：关闭前强制检查 acceptance / verification / closure_evidence。

### P3：让 AI 能复盘

当前同类错误反复发生，没有沉淀。

1. **ldvh-retro Skill**：Task 关闭后引导 AI 沉淀 Pitfall、提出 Rule 改进建议、提出工具改善建议；
2. **项目态势聚合器**：聚合所有事实实例，识别缺口和风险；
3. **Schedule 定期审计**：周期性检查 specs / ldvh-base / docs 健康状态。

---

## 8. 融合框架的硬边界

以下边界不可妥协：

1. **Git 文件事实源是权威层**：工具输出、网页视图、缓存、Memory、聊天记录不能替代最终事实源；
2. **Human Gate 不可绕过**：关键决策、高风险操作、状态流转、事实源变更必须用户确认；
3. **Tools 不调用 AI / Skill / Agent**：Tools 只做确定性处理，不做判断；
4. **Skill 不调度 Agent**：Skill 发现需要 Agent 时，建议用户或主控判断；
5. **Agent 只在必要时创建**：独立上下文、结论隔离、并行委派、权限隔离才用 Agent；
6. **不引入本地隐藏状态目录**：稳定事实在 Git 文件中，不用 ~/.ldvh/；
7. **不自动发布、自动提交、自动合并**：LDVH 是治理框架，不是发布机器人；
8. **Trae-native**：用 Trae 原生机制表达一切，不引入外部 daemon 或 CLI。

---

## 9. 后续推进项

以下 6 项经评估，当前均可推进，无硬阻塞。每项标注前置条件实际状态和具体推进方式。

### 9.1 Core Loop 的 6 个 Skill 详细流程设计

- **原写阻塞条件**：11.02 Skill 清单原则和事实模型 23-32 稳定后确定
- **实际状态**：11.02 已 active；事实模型仅 21(ADR)、22(Change)、23(Pitfall) active，24-32 全部 planned
- **能否推进**：可以。先基于 21/22/23 三个 active 对象设计 Skill 流程，planned 对象（Intent、Task、Evidence 等）落地后再扩展。Skill 流程设计本身可以反过来帮助明确 planned 对象需要什么字段。
- **推进方式**：
  1. 先设计 ldvh-intake（基于 Intent 概念草案）和 ldvh-close（基于 21 ADR + 22 Change + 23 Pitfall）两个最不依赖 planned 对象的 Skill；
  2. ldvh-plan、ldvh-execute、ldvh-review、ldvh-retro 先写流程框架，字段引用标注"待 XX 对象规范落地后补充"；
  3. Skill 流程设计产出应进入对应事实模型的 NN.02-Skill.md 实践子文档。

### 9.2 Context Primer 的具体输入输出格式

- **原写阻塞条件**：12-eval P0 工具落地后确定
- **实际状态**：12-eval 是评估文档，P0 工具尚未实现
- **能否推进**：可以。格式规范可以先设计，工具实现是后续步骤。格式设计不需要等工具代码。
- **推进方式**：
  1. 定义 Context Primer 的输入（项目路径、当前任务 ID、场景类型）和输出（8 项最小可行动上下文：当前项目、当前场景、当前事实源边界、当前任务状态、当前 Human Gate 风险、当前推荐 Skill / 流程、当前必须验证命令、当前回写目标）；
  2. 定义输出格式（YAML / Markdown / JSON）和来源映射（每项输出从哪个 Git 文件事实源读取）；
  3. 产出应作为 12.01 Tools 辅助规范中"上下文包生成"职责的详细规格说明。

### 9.3 Gate Detector 与 Trae AskUserQuestion 的集成方式

- **原写阻塞条件**：05 稳定后确定
- **实际状态**：05 已 active，触发条件、参数契约、降级策略均已定义
- **能否推进**：可以。没有实际阻塞。
- **推进方式**：
  1. 定义 Gate Detector 的检测规则（哪些文件路径 + 哪些操作类型触发 Human Gate 检测）；
  2. 定义 Gate Detector 检测到 Human Gate 场景后的输出格式（ELI10 + Stakes + Recommendation + Pros/Cons）；
  3. 定义 Gate Detector 输出如何映射到 AskUserQuestion 的 questions 参数（header、question、options、multiSelect）；
  4. 产出应作为 12.01 Tools 辅助规范中"校验"和"受控写入"职责的扩展规格说明。

### 9.4 验证分级中 L4 真实交互验证的实现方式

- **原写阻塞条件**：工具层建设后评估
- **实际状态**：工具层只有 5 个 specs 检查脚本，无真实交互验证能力
- **能否推进**：可以调研。这是纯调研项，可以直接在 Trae 环境中测试能力边界。
- **推进方式**：
  1. 在 Trae 环境中测试 Web Preview 能力（启动本地服务器、预览页面、获取页面状态）；
  2. 评估 Playwright MCP 在 Trae 中的可用性（是否已接入、能否截图、能否交互）；
  3. 评估 Trae RunCommand + headless browser 的替代方案；
  4. 产出应写入 specs/refs/ 作为外部资料引用，不直接成为 LDVH 强制规则。

### 9.5 角色化审查从检查清单升级为 Agent 的具体门槛

- **原写阻塞条件**：11.03 和 51 稳定后确定
- **实际状态**：11.03 已 active；51 已 active
- **能否推进**：可以。没有实际阻塞。
- **推进方式**：
  1. 基于 11.03 §3 的 5 项治理条件（独立上下文、结论隔离、并行委派、不同权限边界、长期专业入口），逐项定义角色化审查场景的升级门槛；
  2. 基于 51 §10 的 Rules 和 Agent 调度规则，定义检查清单 → 多角色思考 → Agent 的升级路径和触发条件；
  3. 定义升级为 Agent 后的角色定义摘要模板（依据 11.03 §5）；
  4. 产出应作为 51 行动模型的实践补充。

### 9.6 融合框架对现有 LDVH 规范体系的影响范围和迁移路径

- **原写阻塞条件**：ADR 评估后确定
- **实际状态**：ADR 机制已 active，但尚未创建对应 ADR
- **能否推进**：可以。先做影响分析草案，再进 ADR 流程正式确认。
- **推进方式**：
  1. 逐项评估融合框架对现有 specs 的影响：00（理念与纲要是否需要更新 Core Loop 表述）、01（目录说明是否需要增加融合框架章节）、03（文档规范是否需要增加融合框架文档类型）、10-14（基础规范是否需要调整）、20-32（事实模型优先级是否需要调整）、50-51（行动模型是否需要增加 Core Loop 行动）；
  2. 逐项评估对 Rules 的影响：L0/L1/L2 是否需要增加 Core Loop 入口、Context Primer 入口、Gate Detector 入口；
  3. 逐项评估对 Skill 的影响：是否需要新增 6 个核心 Skill；
  4. 逐项评估对 Tools 的影响：是否需要新增 4 类工具；
  5. 影响分析草案完成后，通过 ldvh-adr Skill 创建 ADR，进入正式决策流程。

---

## 10. 从零开始的实施计划

假设所有现有环境设置（Rules、Skills、Tools 等）全部清空，从零建设融合框架。以下计划按"AI 进入速度优先"原则设计，每个阶段独立可用，AI 体验逐阶段提升。

### 10.1 设计原则

1. **先让 AI 能进入，再让 AI 能做事，再让 AI 能做对，再让 AI 能闭环，最后让 AI 能进化**；
2. **每个阶段交付后，AI 在该项目中的体验应比上一阶段有质的提升**；
3. **Rules 先于 Skill，Skill 先于 Tools，Tools 先于 Agent**；
4. **最小事实内核先于完整事实模型**；
5. **Core Loop 是贯穿所有阶段的行动主线**。

### 10.2 Phase 1：AI 能进入

**目标**：AI 进入项目后 30 秒内，知道这是什么项目、该读什么、不能干什么、当前该干什么。

**核心交付物**：

| # | 交付物 | 类型 | 内容 |
|---|---|---|---|
| 1 | 项目目录结构 | 目录 | specs/、ldvh-base/、docs/、tools/、tests/tools/、.trae/rules/、.trae/skills/ |
| 2 | 00 理念与纲要（精简版） | specs | Core Loop 定义、V1-V10 价值标准、五类构成要素、事实源闭环原则 |
| 3 | 01 目录说明 | specs | 编号分区、目录职责 |
| 4 | 02 术语规范 | specs | 核心术语定义 |
| 5 | 10 事实源边界规范（精简版） | specs | Git 文件事实源原则、回写规则、禁止事项 |
| 6 | 05 AskUserQuestion 使用规范 | specs | Human Gate 触发条件、格式规范、降级策略 |
| 7 | L0 工作区规则 | Rules | 项目识别、L1 读取入口、Core Loop 入口、事实模型编辑入口 |
| 8 | L1 项目规则 | Rules | 项目定位、必读入口、硬约束、Core Loop 阶段判断入口 |

**AI 体验变化**：

```text
Phase 0（空白）：AI 进入项目 → 不知道这是什么项目 → 盲目探索
Phase 1（交付后）：AI 进入项目 → L0 告知项目类型 → L1 告知必读入口 → 知道边界和当前阶段
```

**验收标准**：

1. AI 进入项目后能自动识别项目类型和场景；
2. AI 能说出当前项目的事实源边界和硬约束；
3. AI 能说出 Core Loop 的 6 个阶段和当前应处于哪个阶段；
4. AI 知道何时必须停下来问用户（Human Gate 触发条件）。

### 10.3 Phase 2：AI 能做事

**目标**：AI 不仅能识别场景，还能创建和操作最小事实对象，通过第一个 Skill 完成从意图到任务的闭环。

**核心交付物**：

| # | 交付物 | 类型 | 内容 |
|---|---|---|---|
| 1 | Intent 事实模型规范 | specs/24 | 准入条件、字段契约、状态机、Human Gate |
| 2 | Task 事实模型规范 | specs/新编号 | 准入条件、字段契约、状态机、Human Gate |
| 3 | ADR 事实模型规范 | specs/21 | 从现有 21 精简复用 |
| 4 | Evidence 事实模型规范 | specs/29 | 准入条件、字段契约、状态机 |
| 5 | Change 事实模型规范 | specs/22 | 从现有 22 精简复用 |
| 6 | 20 事实模型集合索引 | specs | 5 类核心对象索引，扩展对象标注 planned |
| 7 | Contract 子文档 | specs/NN.06 | 5 类对象的字段契约（供 Tools 消费） |
| 8 | ldvh-base/ 目录结构 | 事实源 | intents/、tasks/、adrs/、evidence/、changes/ |
| 9 | ldvh-intake Skill | Skill | 用户意图 → 识别场景 → 创建 Intent / Task 草案 → Human Gate |
| 10 | ldvh-close Skill | Skill | closure_evidence 校验 → Change 记录 → 状态回写 → Human Gate |
| 11 | L2 场景规则 | Rules | ldvh-base/ YAML 编辑场景约束 |

**AI 体验变化**：

```text
Phase 1：AI 知道边界和阶段 → 但无法创建对象、无法走完闭环
Phase 2：AI 能通过 ldvh-intake 创建任务 → 能通过 ldvh-close 关闭任务 → 最小闭环可运行
```

**验收标准**：

1. AI 能通过 ldvh-intake 从用户自然语言意图创建 Intent 和 Task；
2. AI 能通过 ldvh-close 校验 Evidence、记录 Change、回写状态；
3. AI 创建和关闭对象时能正确触发 Human Gate；
4. 所有对象实例写入 ldvh-base/ 对应目录，可通过 Git 追溯。

### 10.4 Phase 3：AI 能做对

**目标**：AI 不仅能做事，还能在做事过程中被工具拦住越界行为、即时校验错误、分级验证结果。

**核心交付物**：

| # | 交付物 | 类型 | 内容 |
|---|---|---|---|
| 1 | Gate Detector | Tool (Python) | 检测 Human Gate 触发条件，输出结构化决策卡片，映射到 AskUserQuestion |
| 2 | Fact Validator | Tool (Python) | 读取 Contract 子文档，校验 YAML 字段、状态机、引用完整性 |
| 3 | 12 工具基础规范（精简版） | specs | Tools 允许职责、禁止职责、校验原则、受控写入原则 |
| 4 | 12.01 Tools 辅助规范（精简版） | specs | 8 项允许职责详细规则 |
| 5 | 验证分级规范 | specs/新编号 | L1-L5 验证级别定义、证据形式、Trae 机制映射 |
| 6 | ldvh-plan Skill | Skill | 拆解步骤 → 评估风险 → 检查事实源 → 多视角审视 → Human Gate |
| 7 | ldvh-execute Skill | Skill | 按计划实施 → 限定编辑范围 → 遵守约束 → 高风险操作前 Human Gate |

**AI 体验变化**：

```text
Phase 2：AI 能创建和关闭任务 → 但可能越界、可能改错、验证靠自觉
Phase 3：AI 即将越界时被 Gate Detector 拦住 → 修改 YAML 后被 Fact Validator 即时校验 → 验证分级让 AI 知道该做到哪级
```

**验收标准**：

1. Gate Detector 在 AI 修改 specs / Rules / ADR / ldvh-base/ 时能主动提示 Human Gate；
2. Fact Validator 在 AI 修改 YAML 后能即时校验字段、状态机、引用完整性；
3. AI 能按验证分级规范执行 L1-L3 验证（lint / test / build）；
4. 验证结果能进入 Evidence 对象。

### 10.5 Phase 4：AI 能闭环

**目标**：AI 能走完 Core Loop 的完整闭环，从意图到复盘，每个阶段都有 Skill 引导、Tools 辅助、Evidence 沉淀。

**核心交付物**：

| # | 交付物 | 类型 | 内容 |
|---|---|---|---|
| 1 | Context Primer | Tool (Python) | 生成 AI 最小可行动上下文（8 项：项目、场景、事实源边界、任务状态、HG 风险、推荐 Skill、验证命令、回写目标） |
| 2 | Evidence Collector | Tool (Python) | 收集 lint / test / build 输出，生成 Evidence 候选 |
| 3 | 通用受控写入工具 | Tool (Python) | 多文件事务写入 + 写入前校验 + Change 记录自动生成 |
| 4 | ldvh-review Skill | Skill | 检查 Evidence → 校验字段 → 验证引用完整性 → Human Gate |
| 5 | ldvh-retro Skill | Skill | Pitfall 沉淀 → Rule 改进建议 → 工具改善建议 → Human Gate |
| 6 | Pitfall 事实模型规范 | specs/23 | 从现有 23 精简复用 |
| 7 | 11 AI 协作规范 | specs | Rules / Skill / Agent 跨机制选择边界 |
| 8 | 11.01 Rules 机制规范 | specs | Rules 分层、生效方式、设计约束 |
| 9 | 11.02 Skill 机制规范 | specs | Skill 准入、命名、部署、输出、边界 |
| 10 | 11.03 Agent 机制规范 | specs | Agent 准入、调度、定义摘要、生命周期 |

**AI 体验变化**：

```text
Phase 3：AI 能做对 → 但每次进入都要手动拼凑上下文、复盘靠自觉
Phase 4：AI 进入项目时 Context Primer 自动装配上下文 → 6 个 Skill 覆盖完整 Core Loop → Evidence Collector 自动收集证据 → 复盘有 ldvh-retro 引导
```

**验收标准**：

1. AI 进入项目时能通过 Context Primer 获得 8 项最小可行动上下文；
2. AI 能通过 6 个 Skill 走完 Core Loop 完整闭环（Intent → Plan → Execute → Verify → Record → Learn）；
3. 每个阶段的关键操作都有 Evidence 沉淀；
4. 关闭任务后能通过 ldvh-retro 沉淀 Pitfall 和改进建议；
5. 所有稳定事实回到 Git 文件事实源。

### 10.6 Phase 5：AI 能进化

**目标**：AI 不仅能闭环，还能从经验中学习、从多视角审视、定期审计项目健康状态。

**核心交付物**：

| # | 交付物 | 类型 | 内容 |
|---|---|---|---|
| 1 | Risk 事实模型规范 | specs/26 | 按痛点启用 |
| 2 | Memo 事实模型规范 | specs/25 | 按痛点启用 |
| 3 | Dependency 事实模型规范 | specs/27 | 按痛点启用 |
| 4 | Checklist 事实模型规范 | specs/30 | 按痛点启用 |
| 5 | Artifact 事实模型规范 | specs/29 | 按痛点启用 |
| 6 | TaskSet 事实模型规范 | specs/32 | 按痛点启用 |
| 7 | 51 多角色思考行动模型 | specs | 检查清单 → 多角色思考 → 必要时 Agent 的升级路径 |
| 8 | 项目态势聚合器 | Tool (Python) | 聚合所有事实实例，识别缺口和风险 |
| 9 | L4 真实交互验证 | Tool / MCP | Web Preview + Playwright MCP 集成 |
| 10 | Web 信息同步层 | Web | 项目态势展示、Human Gate 工作台 |
| 11 | Schedule 定期审计 | Schedule | 周期性检查 specs / ldvh-base / docs 健康状态 |

**AI 体验变化**：

```text
Phase 4：AI 能闭环 → 但角色审查靠清单、项目健康靠人工、验证到 L3 为止
Phase 5：AI 能从多角色视角并行审视 → 能定期审计项目健康 → 能做 L4 真实交互验证 → 能通过 Web 视图让用户看到项目全貌
```

**验收标准**：

1. AI 能在复杂场景下通过多角色思考获得多维度判断；
2. 项目态势聚合器能输出当前项目所有事实实例的状态、缺口和风险；
3. L4 真实交互验证能在 Trae 环境中运行并产出截图和交互记录；
4. Schedule 定期审计能自动运行并输出健康报告；
5. 扩展对象按痛点启用，不增加 AI 的初始认知负担。

### 10.7 阶段依赖关系

```text
Phase 1（AI 能进入）
  │
  ├─→ Phase 2（AI 能做事）── 需要 Phase 1 的 Rules 和事实源边界
  │     │
  │     ├─→ Phase 3（AI 能做对）── 需要 Phase 2 的事实对象和 Contract
  │     │     │
  │     │     ├─→ Phase 4（AI 能闭环）── 需要 Phase 3 的 Gate Detector 和 Fact Validator
  │     │     │     │
  │     │     │     └─→ Phase 5（AI 能进化）── 需要 Phase 4 的完整 Core Loop
  │     │     │
  │     │     └─ Phase 3 内的 ldvh-plan / ldvh-execute 可与 Phase 2 的 ldvh-intake / ldvh-close 并行设计
  │     │
  │     └─ Phase 2 内的 5 类事实模型规范可并行编写
  │
  └─ Phase 1 内的 L0 / L1 Rules 可并行编写
```

### 10.8 从零开始的关键优势

与在现有 LDVH 上增量改造相比，从零开始有以下优势：

1. **00 可以重写**：Core Loop 可以成为 00 的第一层体验，而不是只作为规范文本存在；
2. **事实模型可以精简**：5 类核心对象先行，7 类扩展对象按痛点启用，AI 不会一开始面对 12+ 类对象；
3. **Rules 可以精简**：L0/L1/L2 只保留必要入口和硬约束，单个 Rules 文件不超过 1000 字符；
4. **Skill 可以聚焦**：6 个核心 Skill 围绕 Core Loop 设计，不是围绕对象分类设计；
5. **Tools 可以统一**：通用 YAML 校验框架 + Contract 驱动，不需要为每个对象写独立工具；
6. **不需要兼容旧规范**：没有迁移成本，没有旧规范与新架构的冲突。

### 10.9 从零开始的关键风险

| 风险 | 表现 | 控制方式 |
|---|---|---|
| 规范真空期 | Phase 1 完成前项目没有任何规范保护 | Phase 1 应尽快交付，不超过 1 个工作周期 |
| 事实模型不完整 | Phase 2 只有 5 类对象，某些场景无法表达 | 扩展对象按痛点启用，不预设全部对象 |
| 工具能力滞后 | Phase 3-4 才有 Gate Detector 和 Fact Validator | Phase 1-2 靠 Rules 提醒和 AI 自律，Phase 3 起工具化 |
| 与现有 LDVH 规范冲突 | 如果未来需要与现有 LDVH 项目互通 | 融合框架的 00 应声明与现有 LDVH 的兼容策略 |
| 过度精简 | 精简版规范可能遗漏关键约束 | 每个精简版规范应标注"精简版"和"完整版待补齐" |

---

## 11. 产品化设计

融合框架不是内部工具，而是面向其他用户的产品。用户需要能安装、配置、初始化、日常使用、定制和升级。本节定义产品化的关键设计决策。

### 11.1 产品化带来的根本变化

| 维度 | 内部框架思维 | 产品思维 |
|---|---|---|
| 用户是谁 | 自己（知道所有设计决策） | 陌生用户（第一次接触框架） |
| 安装方式 | 手动复制文件 | 一键安装 |
| 配置方式 | 直接改 Rules 文件 | 填配置文件，工具生成 Rules |
| 初始化 | 手动建目录 | 一个命令生成项目骨架 |
| 日常使用 | AI 按 specs 行动 | AI 按 Core Loop 行动，用户只做 Human Gate |
| 定制 | 直接改 specs | 通过配置和模板扩展，不直接改框架核心 |
| 升级 | 手动替换 | 工具升级，保留用户自定义 |

### 11.2 框架核心 vs 项目实例

产品化的关键区分：**框架核心随安装包分发，用户不修改；项目实例由用户初始化生成，用户可修改。**

#### 11.2.1 框架核心（随安装包分发）

用户安装后自动获得，升级时自动更新。文件头部标注 `<!-- AUTO-GENERATED by ldvh – do not modify -->` 或等效标记。

| 类别 | 内容 | 安装位置 |
|---|---|---|
| 规范文档 | 00 理念与纲要、01 目录说明、02 术语规范、10 事实源边界、05 AskUserQuestion 规范、11 系列、12 系列、13 事实模型基础、14 行动模型基础、20-32 事实模型规范、50-51 行动模型规范 | `specs/` |
| L0 工作区规则 | 项目识别、L1 读取入口、Core Loop 入口、事实模型编辑入口 | `.trae/rules/ldvh-l0-rules.md` |
| L0 事实模型规则 | 事实实例编辑场景约束 | `.trae/rules/ldvh-l0-fact-model-rules.md` |
| 核心 Skill | ldvh-intake、ldvh-plan、ldvh-execute、ldvh-review、ldvh-close、ldvh-retro | `.trae/skills/ldvh-{name}/` |
| 核心 Tools | Context Primer、Fact Validator、Gate Detector、Evidence Collector、受控写入工具 | `tools/` |
| 测试 | Tools 对应的 pytest 测试 | `tests/tools/` |
| 初始化工具 | ldvh init / ldvh upgrade / ldvh doctor | `tools/ldvh_cli.py` 或独立 CLI |

#### 11.2.2 项目实例（用户初始化时生成）

用户运行 `ldvh init` 后生成，用户可自由修改。升级时不覆盖。

| 类别 | 内容 | 安装位置 |
|---|---|---|
| 项目配置 | 项目名、类型、管辖项目列表、事实源目录、验证命令等 | `.ldvh.yml` |
| L1 项目规则 | 项目定位、必读入口、硬约束、Core Loop 阶段判断入口 | `.trae/rules/ldvh-l1-rules.md` |
| L2 场景规则 | 按项目类型选择的场景约束 | `.trae/rules/ldvh-l2-*-rules.md` |
| 事实实例目录 | intents/、tasks/、adrs/、evidence/、changes/ 等 | `ldvh-base/` |
| 项目文档 | 项目专属文档 | `docs/` |
| 自定义 Skill | 用户自建的 Skill | `.trae/skills/`（非 ldvh- 前缀） |
| 自定义 Tools | 用户自建的工具 | `tools/`（非 ldvh- 前缀） |

### 11.3 安装体验设计

#### 11.3.1 安装方式

| 方式 | 命令 | 适用场景 |
|---|---|---|
| pip 安装 | `pip install ldvh` | Python 用户，最简单 |
| git clone + 安装 | `git clone https://github.com/.../ldvh.git && cd ldvh && pip install -e .` | 想看源码或贡献的用户 |
| Trae 一键导入 | 通过 Trae Agent / Skill 市场 | Trae 用户，最集成 |

安装后用户获得：
1. `ldvh` CLI 命令（init / upgrade / doctor / validate）
2. 框架核心文件模板（在 pip 包的 templates/ 目录下）
3. 核心 Tools Python 模块（在 pip 包的 tools/ 目录下）

#### 11.3.2 初始化流程

```text
用户运行 ldvh init
  │
  ├─→ 询问项目信息（AskUserQuestion 或 CLI 交互）
  │     - 项目名称
  │     - 项目类型（web / api / data / library / monorepo / custom）
  │     - 管辖项目列表（如果有多个子项目）
  │     - 主要语言 / 框架
  │     - 验证命令（lint / test / build）
  │     - 是否需要浏览器 QA
  │
  ├─→ 生成目录结构
  │     - specs/（从模板复制框架核心规范）
  │     - ldvh-base/（创建空目录 + README）
  │     - docs/
  │     - tools/（从模板复制框架核心工具）
  │     - tests/tools/
  │     - .trae/rules/（根据项目类型生成 L0/L1/L2）
  │     - .trae/skills/（从模板复制核心 Skill）
  │
  ├─→ 生成 .ldvh.yml 配置文件
  │
  ├─→ 生成 L1 项目规则（根据配置填充项目名、事实源目录等）
  │
  ├─→ 生成 L2 场景规则（根据项目类型选择模板）
  │
  └─→ 输出初始化报告
        - 创建了哪些文件
        - 用户应检查哪些文件
        - 下一步建议（打开 Trae，开始 Vibe Coding）
```

#### 11.3.3 配置文件设计

`.ldvh.yml` 是项目级配置文件，声明项目基本信息和框架行为偏好：

```yaml
# LDVH 项目配置
version: "1.0"

project:
  name: my-project
  type: web  # web / api / data / library / monorepo / custom
  language: typescript
  framework: next.js

# 管辖项目（多项目工作区）
jurisdictions:
  - name: my-project
    path: .
    fact_source: ldvh-base/

# 验证命令
validation:
  lint: "npm run lint"
  typecheck: "npx tsc --noEmit"
  test: "npm test"
  build: "npm run build"

# Core Loop 偏好
core_loop:
  # 是否在 Plan 阶段自动触发多视角审视
  auto_multi_perspective: true
  # 验证级别：1=静态, 2=单元, 3=集成, 4=真实交互
  default_verify_level: 2
  # 是否在 Execute 阶段启用 Scope Freeze
  scope_freeze: true

# 框架升级策略
upgrade:
  # 是否自动更新框架核心文件
  auto_update_core: true
  # 是否保留用户对 L1/L2 的修改
  preserve_custom_rules: true
```

### 11.4 模板系统

不同项目类型需要不同的 Rules/Skill 组合。模板系统解决"开箱即用"问题。

| 项目类型 | L2 场景规则 | 默认验证级别 | 特殊 Skill | 特殊 Tools |
|---|---|---|---|---|
| web | 前端编辑约束、组件边界 | L3（含 Web Preview） | ldvh-browser-qa | Playwright 集成 |
| api | API 契约约束、接口边界 | L2（含 API 测试） | — | API 测试辅助 |
| data | 数据管道约束、Schema 边界 | L2（含数据验证） | — | 数据校验辅助 |
| library | 包发布约束、API 兼容性 | L2 | — | — |
| monorepo | 子项目边界、依赖约束 | L2 | ldvh-scope-check | 依赖分析 |
| custom | 用户自定义 | 用户自定义 | 用户自定义 | 用户自定义 |

### 11.5 升级策略

```text
用户运行 ldvh upgrade
  │
  ├─→ 检查当前版本和最新版本
  │
  ├─→ 识别框架核心文件（头部有 AUTO-GENERATED 标记）
  │     - 未修改：直接覆盖更新
  │     - 已修改：提示用户选择（保留自定义 / 覆盖 / 合并）
  │
  ├─→ 识别项目实例文件
  │     - 不覆盖用户自定义的 L1/L2 Rules
  │     - 不覆盖 .ldvh.yml
  │     - 不覆盖 ldvh-base/ 下的事实实例
  │     - 不覆盖用户自建 Skill 和 Tools
  │
  ├─→ 更新框架核心文件
  │     - specs/ 下的规范文档
  │     - .trae/rules/ldvh-l0-*.md
  │     - .trae/skills/ldvh-*/
  │     - tools/ldvh_*.py
  │
  └─→ 输出升级报告
        - 更新了哪些文件
        - 哪些文件因用户修改而跳过
        - 是否有破坏性变更需要用户手动处理
```

### 11.6 诊断工具

```text
用户运行 ldvh doctor
  │
  ├─→ 检查目录结构完整性
  │     - specs/ 是否存在核心规范
  │     - ldvh-base/ 是否存在核心对象目录
  │     - .trae/rules/ 是否存在 L0/L1
  │     - .trae/skills/ 是否存在核心 Skill
  │     - tools/ 是否存在核心 Tools
  │
  ├─→ 检查配置文件有效性
  │     - .ldvh.yml 是否存在且格式正确
  │     - 验证命令是否可执行
  │
  ├─→ 检查事实源健康
  │     - ldvh-base/ 下的事实实例是否通过 Fact Validator 校验
  │     - 是否有状态异常的对象
  │     - 是否有引用断裂
  │
  └─→ 输出诊断报告和建议修复方式
```

### 11.7 产品化对实施计划的影响

产品化要求在 §10 的实施计划中增加以下交付物：

| Phase | 新增交付物 | 说明 |
|---|---|---|
| Phase 1 | 安装包骨架（pyproject.toml / setup.py） | 让框架可 pip install |
| Phase 1 | ldvh init CLI | 初始化项目骨架 |
| Phase 1 | .ldvh.yml 配置文件模板 | 项目级配置 |
| Phase 1 | L1 Rules 生成器 | 根据 .ldvh.yml 生成 L1 项目规则 |
| Phase 2 | 项目类型模板 | web / api / data / library / monorepo / custom |
| Phase 2 | L2 Rules 生成器 | 根据项目类型生成 L2 场景规则 |
| Phase 3 | ldvh doctor CLI | 诊断工具 |
| Phase 4 | ldvh upgrade CLI | 升级工具 |
| Phase 4 | AUTO-GENERATED 标记机制 | 区分框架核心和用户自定义 |
| Phase 5 | Trae 一键导入包 | Trae Skill 市场或 Agent 市场分发 |

### 11.8 产品化的关键风险

| 风险 | 表现 | 控制方式 |
|---|---|---|
| 安装体验差 | 用户安装后不知道怎么开始 | ldvh init 后输出清晰的"下一步"指引 |
| 配置过复杂 | .ldvh.yml 选项太多，用户不知道填什么 | 提供合理默认值，只要求必填项 |
| 模板不覆盖 | 用户的项目类型不在预设模板中 | 提供 custom 类型，用户可完全自定义 |
| 升级破坏自定义 | ldvh upgrade 覆盖了用户的 L1/L2 修改 | AUTO-GENERATED 标记 + 升级前 diff 检查 |
| 框架核心被用户修改 | 用户直接改 specs/ 下的规范文档 | 文件头部标记 + ldvh doctor 检测 |
| 多项目工作区复杂 | 用户有多个子项目，初始化和升级逻辑复杂 | .ldvh.yml 支持多管辖项目配置 |
| Trae 机制变化 | Trae 平台更新导致 Rules/Skill/Agent 机制变化 | 框架核心与 Trae 机制解耦，通过适配层映射 |

---

## 12. 最小事实内核的构建路径

5 类核心事实对象（Intent、Task、ADR、Evidence、Change）中，ADR(21) 和 Change(22) 已有完整规范，Intent(24)、Task、Evidence(29) 处于 planned 状态或未分配编号。本节定义从零构建的具体路径。

### 12.1 现有构建标准

`specs/13-LDVH事实模型基础规范.md` §4.2 定义了事实模型的标准组成（18 项）：

1. 对象定位与准入条件
2. 事实源边界
3. 状态机
4. 与其他对象的关系
5. Human Gate
6. 字段契约
7. 事实源回写要求
8. 证据留存要求
9. AI 协作适配
10. Tools 契约式校验与执行适配
11. Web 信息同步适配
12. 附件型实践子文档按需拆分规则
13. 落地前决策
14. 价值与要素审查
15. 落地初始化
16. 落地审计
17. 合规检查
18. 待补齐事项

此外，`specs/04-LDVH模型子文档规范.md` 要求每个事实模型有 6 个附件型实践子文档（NN.01-Rules、NN.02-Skill、NN.03-Agent、NN.04-Tools、NN.05-Web、NN.06-Contract）。

### 12.2 为什么从零开始可以精简

18 项标准组成 + 6 个子文档对一个"最小事实内核"来说过重。从零开始的优势是：

1. **不需要一次写完 18 项**：核心项先行，扩展项按痛点补齐；
2. **不需要一次创建 6 个子文档**：Contract 子文档先行（供 Tools 消费），其他子文档按需创建；
3. **不需要 200 行规范**：精简版规范聚焦 AI 最需要知道的：这是什么、怎么创建、什么状态、怎么流转、何时停下、写回哪里；
4. **有完整参考模板**：21 ADR 是一个 active 的完整事实模型规范，可以直接参考其结构。

### 12.3 精简版事实模型规范模板

从零开始时，每个核心事实对象先写精简版规范，包含以下必要章节：

| 章节 | 对应 13 §4.2 编号 | 为什么必要 | 精简版要求 |
|---|---|---|---|
| 对象定位与准入条件 | 1 | AI 需要知道什么时候该创建这个对象 | 一段定义 + 3-5 条准入条件 |
| 状态机 | 3 | AI 需要知道对象能从什么状态变到什么状态 | 状态列表 + 允许迁移 + 触发条件 |
| 字段契约 | 6 | AI 和 Tools 需要知道对象有哪些字段、什么类型、是否必填 | 字段表（名称、类型、必填、说明） |
| Human Gate | 5 | AI 需要知道何时必须停下来问用户 | 触发场景列表 |
| 事实源边界 | 2 | AI 需要知道实例写回哪个目录 | 目录路径 + 文件命名规则 |
| 与其他对象的关系 | 4 | AI 需要知道对象能引用哪些其他对象 | 引用关系表 |
| 事实源回写要求 | 7 | AI 需要知道写入后要做什么 | 回写规则（Change 记录、状态更新） |

以下章节在精简版中标注"待补齐"，Phase 4-5 再展开：

| 章节 | 对应 13 §4.2 编号 | 精简版处理 |
|---|---|---|
| 证据留存要求 | 8 | 标注"待补齐"，Phase 3 补充 |
| AI 协作适配 | 9 | 标注"待补齐"，Phase 4 补充 |
| Tools 契约式校验与执行适配 | 10 | 标注"待补齐"，Phase 3 补充（Contract 子文档先行） |
| Web 信息同步适配 | 11 | 标注"待补齐"，Phase 5 补充 |
| 附件型实践子文档 | 12 | 只创建 NN.06-Contract，其他标注 not-created |
| 落地前决策 | 13 | 标注"待补齐"，Phase 4 补充 |
| 价值与要素审查 | 14 | 标注"待补齐"，Phase 4 补充 |
| 落地初始化 | 15 | 标注"待补齐"，Phase 4 补充 |
| 落地审计 | 16 | 标注"待补齐"，Phase 5 补充 |
| 合规检查 | 17 | 标注"待补齐"，Phase 5 补充 |

### 12.4 五类核心对象的具体构建计划

#### 12.4.1 Intent（意图）

**当前状态**：planned（24），索引中只有一行描述
**参考**：无直接参考，需从零设计
**Core Loop 位置**：Intent 阶段——用户表达意图，AI 识别场景

精简版规范应定义：

| 章节 | 内容 |
|---|---|
| 定义 | 人的原始目标、范围、成功标准和约束 |
| 准入条件 | 1. 用户表达了明确目标；2. 目标尚未任务化或需要跨任务追踪；3. 影响范围超出单次操作 |
| 状态机 | `draft → active → completed → closed`；draft: 用户刚表达，AI 尚未分析；active: AI 已分析，关联了 Task；completed: 关联 Task 全部完成；closed: 已确认完成并沉淀 |
| 字段契约 | id(string,必填), title(string,必填), description(string,必填), success_criteria(string,必填), constraints(string,选填), source(string,必填,来源), status(enum,必填), related_tasks(list,选填), related_adrs(list,选填), created_at(date,必填), updated_at(date,必填) |
| Human Gate | 创建 Intent 时确认；状态从 active → completed 时确认 |
| 事实源边界 | `ldvh-base/intents/{id}.yaml` |
| 对象关系 | → Task（一对多）, → ADR（多对多） |
| 回写要求 | 创建时记录 Change；状态变更时记录 Change |

#### 12.4.2 Task（任务）

**当前状态**：未分配编号（20 索引中没有独立 Task 条目，TaskSet 为 32）
**参考**：无直接参考，需从零设计；可参考 Gstack 的任务拆解思想
**Core Loop 位置**：Plan → Execute → Verify → Record 阶段

精简版规范应定义：

| 章节 | 内容 |
|---|---|
| 定义 | AI 可执行的工作单元，有明确验收标准和回写目标 |
| 准入条件 | 1. 有明确目标；2. 有可验证的验收标准；3. 有来源（Intent 或用户直接指示）；4. 可在单次或有限次执行轮次内完成 |
| 状态机 | `planned → executing → review_needed → closed`；planned: 已拆解，待执行；executing: 正在执行；review_needed: 执行完成，待审查；closed: 审查通过，已关闭。退回：review_needed → executing（审查不通过） |
| 字段契约 | id(string,必填), title(string,必填), description(string,必填), source_intent(string,选填), source(string,必填), status(enum,必填), acceptance(string,必填,验收标准), verification(string,选填,验证方式), assignee(string,选填), related_adrs(list,选填), related_evidence(list,选填), related_changes(list,选填), created_at(date,必填), updated_at(date,必填), closed_at(date,选填), closure_evidence(string,关闭时必填) |
| Human Gate | 状态从 executing → review_needed 时确认；状态从 review_needed → closed 时确认；高风险操作前确认 |
| 事实源边界 | `ldvh-base/tasks/{id}.yaml` |
| 对象关系 | → Intent（多对一）, → ADR（多对多）, → Evidence（一对多）, → Change（一对多） |
| 回写要求 | 创建时记录 Change；状态变更时记录 Change；关闭时必须填写 closure_evidence |

#### 12.4.3 ADR（决策记录）

**当前状态**：active（21），有完整规范 + 6 个实践子文档
**参考**：直接精简复用现有 21
**Core Loop 位置**：Plan 阶段（决策点）→ Record 阶段（决策沉淀）

精简版处理：

1. 保留 21 的核心章节（对象定位、准入条件、状态机、字段契约、Human Gate、事实源边界、对象关系、回写要求）；
2. 精简 AI 协作适配、Tools 适配、Web 适配、落地前决策等章节为"待补齐"；
3. 保留 21.06-Contract 子文档（供 Fact Validator 消费）；
4. 其他子文档（21.01-21.05）标注 not-created，Phase 4 再激活。

#### 12.4.4 Evidence（验证证据）

**当前状态**：planned（28），索引中只有一行描述
**参考**：无直接参考，需从零设计；可参考 Gstack 的 QA 证据思想
**Core Loop 位置**：Verify → Record 阶段

精简版规范应定义：

| 章节 | 内容 |
|---|---|
| 定义 | 执行摘要、验证结果、关闭证据和验收记录 |
| 准入条件 | 1. 有关联的 Task 或 ADR；2. 有可追溯的验证来源（命令输出、截图、测试报告等）；3. 有明确的验证结论 |
| 状态机 | `candidate → verified → archived`；candidate: 刚收集，尚未确认；verified: 已确认有效；archived: 已归档，不再活跃引用 |
| 字段契约 | id(string,必填), title(string,必填), type(enum,必填,verification/execution/closure/review), source_task(string,选填), source_adr(string,选填), verification_method(string,必填), verification_result(enum,必填,pass/fail/partial), content(string,必填,证据内容或摘要), artifact_path(string,选填,附件路径), created_at(date,必填) |
| Human Gate | verification_result 为 fail 时，关联 Task 不应关闭，需 Human Gate 确认处理方式 |
| 事实源边界 | `ldvh-base/evidence/{id}.yaml` |
| 对象关系 | → Task（多对一）, → ADR（多对多） |
| 回写要求 | 创建时关联到 Task 的 related_evidence；验证失败时触发 Task 退回 |

#### 12.4.5 Change（变更记录）

**当前状态**：active（22），有完整规范
**参考**：直接精简复用现有 22
**Core Loop 位置**：Record 阶段

精简版处理：

1. 保留 22 的核心章节（commit message 格式、关联规则、查询约定）；
2. 22 不使用 ldvh-base/changes/ 目录（以 Git commit 为权威事实源），这一设计在精简版中保留；
3. 22 不需要附件型实践子文档，这一设计在精简版中保留。

### 12.5 构建顺序

```text
Step 1: 复用 ADR(21) 和 Change(22)
  │  精简现有规范，保留核心章节，标注"待补齐"
  │
  ├─→ Step 2: 构建 Intent(24) 精简版规范
  │     参考精简版模板，从零设计
  │     同步创建 24.06-Contract 子文档
  │
  ├─→ Step 3: 构建 Task 精简版规范
  │     参考精简版模板，从零设计
  │     同步创建 Task.06-Contract 子文档
  │
  └─→ Step 4: 构建 Evidence(29) 精简版规范
        参考精简版模板，从零设计
        同步创建 29.06-Contract 子文档
```

Step 2-4 可并行编写，因为三者的字段契约相对独立。

### 12.6 Contract 子文档先行

Contract 子文档（NN.06-Contract.md）是 Tools 消费事实模型的入口。精简版规范中，Contract 子文档应与主规范同步创建，包含：

1. 字段契约表（名称、类型、必填、约束）；
2. 状态机迁移表（从状态、到状态、触发条件、前置条件）；
3. 引用关系表（本对象引用哪些其他对象、被哪些对象引用）；
4. Human Gate 触发条件表。

Fact Validator 工具直接读取 Contract 子文档执行校验，不需要理解主规范全文。

### 12.7 构建产出与验收

每个核心事实对象构建完成后，应能回答以下问题：

| 问题 | 验收标准 |
|---|---|
| AI 知道什么时候创建这个对象吗？ | 准入条件清晰，AI 能判断 |
| AI 知道这个对象有哪些字段吗？ | 字段契约完整，Contract 子文档可被 Tools 解析 |
| AI 知道对象能从什么状态变到什么状态吗？ | 状态机完整，迁移条件明确 |
| AI 知道何时必须停下来问用户吗？ | Human Gate 触发场景明确 |
| AI 知道实例写回哪个目录吗？ | 事实源边界和文件命名规则明确 |
| Tools 能校验这个对象的字段和状态吗？ | Contract 子文档可被 Fact Validator 消费 |
