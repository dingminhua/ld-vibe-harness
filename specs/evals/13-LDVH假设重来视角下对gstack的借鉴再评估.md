# LDVH 假设重来视角下对 gstack 的借鉴再评估

> 创建日期：2026-06-03
> 定位：LD Vibe Harness 面向 gstack 的补充性参考评估
> 调研边界：不直接构成强制规则
> 执行效力：无，结论需进入 00-79 正式规范区间或 ADR 后才成为稳定规则
> 上位依据：`specs/00-LD-Vibe-Harness理念与纲要.md`
> 相关参考：`specs/evals/02-LDVH对gstack的借鉴评估.md`

---

## 1. 本文解决的问题

本文在既有 `specs/evals/02-LDVH对gstack的借鉴评估.md` 基础上，从一个更激进的假设出发重新评估 gstack 对 LD Vibe Harness 的参考价值：

> 如果 LD Vibe Harness 一切可以重来，且必须牢牢把握 `specs/00-LD-Vibe-Harness理念与纲要.md` 的核心思想，那么 gstack 最值得借鉴的到底是什么？

本文不是正式规范，不直接改变 LDVH 的事实模型、行动模型、Rules、Skill、Tools 或 Human Gate 要求。本文只作为后续规范重构、路线图讨论、ADR 准备或工具规划的参考材料。

---

## 2. 核心判断

如果 LDVH 可以重来，最值得从 gstack 借鉴的不是“多做几个 Skill”，也不是复制 gstack 的浏览器守护进程、命令体系或本地状态目录，而是：

> 把 LDVH 从“规范驱动的治理框架”，进一步前置为“可直接运行的 AI 工程操作系统”：以少量强闭环主流程承载 00 核心价值，用 Skill、工具、事实源和网页视图把 Vibe Coding 的完整生命周期打通。

LDVH 当前优势是理论完整、事实源严谨、Human Gate 和 Git 文件事实源意识强。gstack 的优势是执行摩擦低、角色化流程强、完整交付链条清晰、浏览器/QA/Ship 等工具贴近真实开发。

真正的借鉴方向应是：

> 保留 LDVH 的事实源与治理深度，吸收 gstack 的“使用即流程、流程即交付、交付即证据”的产品化执行方式。

---

## 3. 必须回到 00 的核心思想

本次评估不能以“gstack 有什么功能 LDVH 也该有”为判断标准，而应回到 `specs/00-LD-Vibe-Harness理念与纲要.md` 的核心要求。

LDVH 00 的关键思想包括：

1. LDVH 要解决 Vibe Coding 的非确定性、幻觉和无记忆问题，把随性 AI 编程变成可规划、可执行、可验证、可沉淀的 AI 工程闭环；
2. LDVH 以 AI 执行者为第一服务对象，首先按照 AI 能快速定位、完整理解、正确判断、稳定执行、强制验证和可靠回写的方式组织项目；
3. LDVH 由介质、开发环境机制、工具、事实模型和行动模型五类构成要素共同形成工程驾驭体系；
4. LDVH 的价值实现标准是 V1-V10，包括快速定位、完整理解、正确判断、稳定执行、门禁识别、强制验证、证据沉淀、可靠回写、人类确认质量和持续完善；
5. LDVH 的事实源必须回到 Git 可追踪文件，工具、网页视图、运行时缓存和聊天记忆不能替代最终事实源。

因此，gstack 对 LDVH 的价值不在于具体产品形态，而在于它是否能帮助 LDVH 更好实现 V1-V10。

---

## 4. gstack 最值得借鉴的本质

gstack 的表层形态是一组 Claude Code Skill、CLI 工具、浏览器能力和本地状态机制；更深层看，它把 Vibe Coding 的软件开发生命周期包装成连续流水线：

```text
Think → Plan → Build → Review → Test → Ship → Reflect
```

这个设计的关键价值不是阶段名称本身，而是：

1. 用户不需要先理解完整治理理论，就可以通过一个明确入口进入流程；
2. AI 不需要自由发挥下一步行动，而是被 Skill 引导到特定阶段；
3. 每个阶段都有角色、输入、输出、检查和下游承接；
4. 质量、安全、QA、发布、复盘不是事后补丁，而是主流程的一部分；
5. 工具用于降低执行摩擦，让正确行为成为默认路径。

这对 LDVH 的启发是：

> Vibe Coding 的工程化，不只是建立规范来约束 AI，而是把正确行为包装成 AI 最容易执行的默认路径。

---

## 5. 如果 LDVH 可以重来，顶层应优先改变什么

### 5.1 从“规范体系优先”转向“主闭环优先”

LDVH 当前的规范体系较完整，但对新用户和新 AI 来说，入口复杂度偏高。事实模型、行动模型、Rules、Skill、ADR、Change、Human Gate、Web Tools 都是正确要素，但这些要素不应成为第一体验。

如果重来，LDVH 顶层应先呈现 3-5 条可运行主闭环：

1. **从意图到任务闭环**：人的自然语言意图 → AI 识别场景 → Intent / TaskSet / Task → Human Gate → 可执行任务；
2. **从任务到交付闭环**：Task → 执行计划 → 实施 → lint / typecheck / test / build → Evidence → Change → 状态回写；
3. **从问题到经验闭环**：Bug / 失败 / 踩坑 → Investigation → Fix → Regression Evidence → Pitfall / Rule / Tool 改进建议；
4. **从决策到约束闭环**：方案冲突 / 架构选择 → ADR → Human Gate → accepted 后进入执行依据；
5. **从交付到复盘闭环**：已交付变更 → Review / QA / 用户反馈 → Change / Pitfall / Memo → 后续规则或工具改善。

00 中已经定义了 AI 行动闭环，但如果重来，应把它产品化为 LDVH 的第一层体验，而不是只作为规范文本存在。

### 5.2 从“事实模型很多”转向“最小事实内核 + 渐进扩展”

LDVH 已规划 Intent、TaskSet、Task、Memo、ADR、Risk、Dependency、Evidence、Artifact、Checklist、Change、Pitfall 等事实模型。这些对象都合理，但若从零开始，不应让 AI 和用户一开始面对所有模型。

建议将事实模型分成两层。

第一层是必须有的最小事实内核：

1. **Intent**：人的原始意图与约束；
2. **Task**：AI 可执行单元；
3. **Decision / ADR**：关键决策；
4. **Evidence**：验证证据；
5. **Change**：实际变更记录。

这五类对象足以形成最小闭环：

```text
Intent → Task → Change
          ↓
       Evidence
          ↓
    Decision / ADR
```

第二层是按痛点启用的扩展对象：

```text
Risk
Dependency
Checklist
Artifact
Memo
Pitfall
TaskSet
```

这样更符合 AI 第一服务对象：AI 先获得目标、边界、事实、状态、验收标准和工具入口，而不是先处理过多对象分类。

### 5.3 从“规范完整性”转向“AI 进入速度”作为第一指标

LDVH 仍应保持规范严谨，但实践入口的首要问题应是：

> AI 进入项目后的 30 秒内，能否知道现在该干什么、该读什么、不能干什么、完成后写回哪里？

gstack 的 Skill preamble 会在进入工作流时自动装配分支、配置、项目 learnings、timeline、routing、plan mode 等上下文。LDVH 可以借鉴这种“流程进入时自动装配最小上下文”的思想，但必须坚持 Git 文件事实源权威。

建议 LDVH 建设统一的 **Context Primer**，每次 AI 进入 LDVH 管辖项目时，优先得到：

1. 当前项目；
2. 当前场景；
3. 当前事实源边界；
4. 当前任务状态；
5. 当前 Human Gate 风险；
6. 当前推荐 Skill / 流程；
7. 当前必须验证命令；
8. 当前回写目标。

这将直接服务 V1 快速定位、V2 完整理解、V3 正确判断和 V4 稳定执行。

---

## 6. 对 gstack 机制的具体借鉴判断

### 6.1 Skill 工厂：值得借鉴，但 LDVH 要更克制

gstack 的 Skill 是可执行工作流，而不是普通说明文档。每个 Skill 有触发词、允许工具、执行流程、STOP point 和用户确认机制。

LDVH 应借鉴以下原则：

1. Skill 应围绕高频场景命名，而不是围绕内部对象命名；
2. Skill 应内置 Human Gate、验证、回写和停止条件；
3. Skill 的输出应能喂给下游 Skill；
4. Skill 应让 AI 更容易采取正确行动，而不是增加阅读负担。

但 LDVH 不应照搬 gstack 的大量角色 Skill。更适合先建设少量核心 Skill：

```text
/ldvh-intake
/ldvh-plan
/ldvh-execute
/ldvh-review
/ldvh-close
/ldvh-retro
```

每个 Skill 都应明确：

1. 触发场景；
2. 必读事实源；
3. Human Gate 判断；
4. 允许工具；
5. 验证要求；
6. 回写目标；
7. STOP 条件。

### 6.2 主流程：应形成 LDVH 自己的行动主线

gstack 的 `Think → Plan → Build → Review → Test → Ship → Reflect` 对 LDVH 的直接启发，是让 LDVH 形成更符合自身事实源闭环的行动主线：

```text
Intent → Plan → Execute → Verify → Review → Record → Learn
```

其中：

| LDVH 阶段 | 对应 00 价值 |
|---|---|
| Intent | 人表达意图，AI 识别场景 |
| Plan | 正确判断、Human Gate、任务拆解 |
| Execute | 稳定执行 |
| Verify | 强制验证 |
| Review | 人类确认质量、风险识别 |
| Record | 证据沉淀、可靠回写 |
| Learn | 持续完善 |

这条主线应成为 README、00、L1 Rules、Skill routing 和 Web Tools 的共同核心。

### 6.3 浏览器 daemon：不必复制，但应吸收真实环境验证思想

gstack 的持久浏览器能力解决的是真实页面 QA、截图、交互、登录态和部署验证问题。LDVH 不一定要复制浏览器守护进程，但应吸收它背后的原则：

> Vibe Coding 的验证不能只停留在代码静态检查；必须尽可能接近真实用户环境。

LDVH 可将验证分级：

1. **静态验证**：lint、typecheck、格式检查、schema 检查；
2. **单元验证**：test、pytest、go test、bun test 等；
3. **集成验证**：服务启动、API 调用、数据库迁移 dry-run；
4. **真实交互验证**：浏览器、截图、表单、登录态、移动端；
5. **证据回写**：命令输出、截图、日志摘要、失败原因进入 Evidence。

这将显著增强 V6 强制验证和 V7 证据沉淀。

### 6.4 Memory / gbrain：可借鉴多层记忆，但不能替代 Git 事实源

gstack 的本地 learnings、timeline、context-save/context-restore、gbrain sync 对跨会话连续性很有价值。

LDVH 可借鉴其效率层，但必须坚持：

```text
最终事实源 = Git 可追踪文件
工具输出 = 辅助
网页视图 = 展示
缓存 / 索引 / memory = 加速
聊天记录 = 证据候选，不是事实
```

因此，对应关系应是：

| gstack 做法 | LDVH 借鉴方式 |
|---|---|
| `~/.gstack/projects/*/learnings.jsonl` | 可作为运行缓存，但稳定经验必须回写 Pitfall / Memo / Change |
| context-save / context-restore | 可做会话恢复辅助，但恢复摘要必须指向 Git 事实源 |
| gbrain sync | 可作为索引层，不作为事实权威 |
| transcript ingest | 只能作为待归档证据，不直接变成规范或事实 |

一句话：gstack 的 memory 是效率层，LDVH 的事实源是权威层。

### 6.5 Safety：应把 Human Gate 从规范纪律升级为工具护栏

gstack 的 careful / freeze / guard 通过工具层降低破坏性命令和越界编辑风险。LDVH 已有 Human Gate 理念，但如果重来，应更早把 Human Gate 工具化。

建议 LDVH 建设三类安全工具：

1. **Destructive Action Guard**：检测危险命令、批量删除、强推、数据库破坏性操作；
2. **Fact Source Guard**：编辑 `ldvh-base/`、specs、Rules、ADR 时自动检查是否满足读取规范、状态机、Human Gate；
3. **Scope Freeze Guard**：任务执行期间可限定 AI 只能编辑某些目录或文件类型。

这会让 V5 门禁识别和 V4 稳定执行从“提示词纪律”升级为“环境约束”。

---

## 7. LDVH 不应照搬 gstack 的地方

### 7.1 不应把速度叙事放在价值核心之上

gstack 有很强的生产力叙事，强调一个人通过 AI 工具获得类似团队的产出能力。LDVH 可以吸收“AI 时代完整实现成本下降”的判断，但不能把速度作为最高目标。

LDVH 的最高目标仍然是：

```text
更高效、更稳定、更可控
```

速度必须受事实源、验证、Human Gate 和回写约束，否则会背离 00。

### 7.2 不应把角色 Skill 做成主要复杂度来源

gstack 的角色 Skill 丰富，这是它的产品魅力。但 LDVH 如果一开始建立大量角色，可能破坏 V1 快速定位。

LDVH 更适合：

1. 少量核心闭环 Skill；
2. 每个 Skill 明确读什么、判断什么、写回什么；
3. 复杂角色作为二级增强，而不是主入口。

### 7.3 不应让运行时缓存、网页视图、外部 memory 取代 Git 文件事实源

gstack 为效率可以把很多东西放在本地状态、daemon state、timeline、learn files 或 gbrain 中。LDVH 可以借鉴这些作为工具层，但最终事实源必须回到 Git 可追踪文件。

这应成为 LDVH 借鉴 gstack 时的硬边界。

---

## 8. 假设重来时的 LDVH 新版架构草案

如果 LDVH 今天从零重启，可考虑四层架构。

### 8.1 第一层：LDVH Core Loop

面向用户和 AI 的第一入口：

```text
Intent → Plan → Execute → Verify → Record → Learn
```

这条主线应成为 README、00、L1 Rules、Skill routing、Web Tools 的共同核心。

### 8.2 第二层：最小事实源内核

先稳定 5 类对象：

```text
Intent
Task
Decision / ADR
Evidence
Change
```

其他对象作为可选增强：

```text
Risk
Dependency
Checklist
Artifact
Memo
Pitfall
TaskSet
```

### 8.3 第三层：核心 Skill

先建设少而强的 Skill：

```text
/ldvh-intake
/ldvh-plan
/ldvh-execute
/ldvh-review
/ldvh-close
/ldvh-retro
```

这些 Skill 应优先服务闭环，而不是服务对象数量。

### 8.4 第四层：工具与视图

优先做四类工具：

1. **Context Primer**：生成当前 AI 最小可行动上下文；
2. **Fact Validator**：校验事实模型字段、状态、引用、回写完整性；
3. **Gate Detector**：提示 Human Gate 风险；
4. **Evidence Collector**：收集测试、构建、截图、命令输出并生成 Evidence 候选。

Web Tools 只做展示和受控写入，不做事实权威。

---

## 9. 对当前 LDVH 的建议优先级

### P0：把 00 的闭环主线产品化

当前 00 已经写得清楚，但 README、L1 Rules、Skill 入口和 Web Tools 应进一步围绕同一条主线表达：

```text
Intent → Plan → Execute → Verify → Record → Learn
```

这是最能推动 Vibe Coding 实践的改动。

### P1：降低新用户和新 AI 的入口复杂度

为 AI 提供统一的“进入项目后先看这里”的最小上下文入口，而不是让 AI 在大量 specs 中自行导航。

这不是取消规范，而是增加 AI 友好的调度层。

### P1：把 Human Gate 工具化

不只写“需要 Human Gate”，还要让工具能提示：

1. 正在修改 specs / Rules / ADR / `ldvh-base/`；
2. 该行为可能是高影响变更；
3. 需要确认哪些事项；
4. 确认后应写回什么证据。

### P2：建立 LDVH 自己的 review / verify / close 工作流

gstack 的 review、qa、ship 很实践导向。LDVH 应建立自己的对应链条，但重点不是 push PR，而是：

1. 变更是否符合事实源边界；
2. 状态流转是否正确；
3. 验证证据是否存在；
4. Change 是否记录；
5. Pitfall 是否需要沉淀；
6. 是否触发 ADR 或 Human Gate。

### P2：引入真实交互验证思想

尤其是 Web Tools 本身、前端项目、产品类项目，应借鉴 gstack 的真实浏览器验证理念，让 Evidence 不只来自命令行测试，也来自用户流验证。

---

## 10. 最终结论

gstack 对 LDVH 的真正启发是：

> Vibe Coding 的工程化，不只是建立规范来约束 AI，而是把正确行为包装成 AI 最容易执行的默认路径。

LDVH 00 已经定义了正确方向：AI 第一服务对象、五类构成要素、V1-V10、Git 文件事实源闭环。

如果一切可以重来，LDVH 最该做的是把这些思想更强地压缩成：

1. 一条主闭环；
2. 一个最小事实内核；
3. 一组高频 Skill；
4. 一套验证与回写工具；
5. 一个低摩擦的人机确认界面。

这样 LDVH 才能从“正确但偏重的治理框架”，变成真正推动 Vibe Coding 实践的“AI 工程驾驭系统”。
