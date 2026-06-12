# LDVH 推进评估与候选事项总览

> 创建日期：2026-06-09
> 更新日期：2026-06-10（第五次更新）
> 定位：LDVH 对 AI 执行者需求匹配、规范落地缺口、候选事项分流和推进方向的内部评估与行动参考
> 调研边界：不直接构成强制规则
> 执行效力：无；稳定结论需进入 docs/specs 正文区、工作对象、Code、Web、测试、运行投影或最佳实践后才具备对应效力
> 来源：原 `docs/research/18-LDVH候选事项承接评估.md`、`docs/research/19-LDVH规范落地统筹机制与闭环缺口评估.md`、`docs/research/20-LDVH规范落地统筹执行缺口清单.md`、`docs/research/21-LDVH面向AI执行者需求的推进评估.md` 合并重建
> 上位依据：`docs/specs/00-LD-Vibe-Harness理念与纲要.md`
> 相关规范：`docs/specs/01-目录说明.md`、`docs/specs/02-术语规范.md`、`docs/specs/03-文档基础规范.md`、`docs/specs/04.01-规范落地声明规范.md`、`docs/specs/04.02-LDVH能力保障规范.md`、`docs/specs/04.03-环境能力清单与环境适配规范.md`、`docs/specs/05-工作模型基础规范.md`、`docs/specs/06-工作流程基础规范.md`、`docs/specs/07-Code确定性执行实现规范.md`、`docs/specs/08-Web信息同步实现规范.md`、`docs/specs/09-事实源边界与承载规范.md`、`docs/specs/10-运行闭环测试规范.md`、`docs/specs/11-非LDVH来源内容治理规范.md`、`docs/specs/12-最佳实践.md`、`docs/specs/20-工作模型集合索引.md`、`docs/specs/40-工作流程集合索引.md`、`docs/specs/41-landing-orchestration-规范落地统筹.md`、`docs/specs/42-ldvh-landing-check-LDVH落地与检查.md`

---

## 1. 本文解决的问题

本文整合四个维度的评估：

1. **AI 执行者需求匹配**：当前 LDVH 是否符合 AI 作为执行者的理解、执行和自我约束需求；
2. **规范落地缺口**：当前 Code 派生的规范落地要求中，哪些已有保障机制，哪些仍停留在声明或人工降级；
3. **候选事项分流**：跨规范的候选、暂缓和拒绝事项如何识别、承接和防护；
4. **推进方向**：下一步应优先补什么，避免什么；
5. **ECC 运行系统经验转译**：LDVH 应学习 ECC 的哪些运行系统组织方法，以及如何受 00 总纲约束地收敛到当前最小闭环。

本文不替代任何正式规范。稳定结论应吸收到对应正式规范、工作对象、Code、Web 或运行投影后才生效。

### 1.1 当前对齐状态

截至 2026-06-10，本轮已经完成以下落地：

| 落地项 | 当前状态 | 已进入位置 | 备注 |
|---|---|---|---|
| 00 总纲表达收敛 | 已落地 | `docs/specs/00-LD-Vibe-Harness理念与纲要.md` | 已补充“启动有序少读、推理有据少猜、行止有规可依、结果有证可验”的总纲表达，并形成 V1-V10 价值实现标准 |
| AI 统一入口与场景路由 | 已落地基础入口 | `LDVH-AI-ENTRY.md` | 已形成最小启动顺序、场景路由、常用查询命令和 STOP 点；入口已提示 LDVH落地与检查读取 42，specs 变更、落地缺口或运行投影漂移优先进入 41 |
| 工作模型集合重组 | 已落地 | `docs/specs/20-工作模型集合索引.md`、`docs/specs/21-26` | ADR、Change、Pitfall、Intent、Memo、Task 已成为 active 工作模型；Profile、TaskSet、Evidence 已取消独立对象化，Dependency/Risk/Artifact/Checklist/Roadmap 已降级为字段、模板或文档承载 |
| 工作流程集合重组 | 已落地基础索引 | `docs/specs/40-工作流程集合索引.md`、`docs/specs/41-44` | 41 规范落地统筹、42 LDVH落地与检查、44 多角色思考已 active；43 已并入 42 并作为 removed 槽位保留；45-58 仍为 candidate，不得当作已生效主文档 |
| 反合理化、失败暂停和完成证据 | 已落地基础规则 | `docs/specs/06-工作流程基础规范.md`、`docs/specs/10-运行闭环测试规范.md`、`docs/specs/26-Task-任务.md`、`docs/specs/41-landing-orchestration-规范落地统筹.md` | 已明确未验证不得关闭、失败需暂停分流、closure evidence 需可追溯 |
| Code 可验证先行 | 已落地 | `docs/specs/07-Code确定性执行实现规范.md` | 不强制经典 TDD，但强制新增、扩展或修改 Code 前明确成功条件、失败条件、正反样例、边界样例、测试命令或等价验证方式 |
| landing report 基础实现 | 已落地 | `tools/specs_validate.py landing-report`、`tests/test_specs_validate.py`、`docs/specs/41-landing-orchestration-规范落地统筹.md` | 当前输出 41 篇来源文件、185 条落地要求 + 4 条能力缺口；未关闭缺口 78 个，按 owner_area 分类：code 16、human_gate 28、runtime_projection 29、specs 1、workflow 4；报告状态为 Code 派生启发式，不是事实源 |
| Human Gate 最小证据结构 | 已落地基础规则与 Code 检查 | `docs/specs/06-工作流程基础规范.md`、`docs/specs/08-Web信息同步实现规范.md`、`docs/specs/21-ADR-决策.md`、`docs/specs/26-Task-任务.md`、`docs/specs/41-landing-orchestration-规范落地统筹.md`、`tools/specs_validate.py human-gate-report`、`tests/test_specs_validate.py` | 已形成通用最小记录块（时间/决策/范围/约束），并让 Task、ADR、Web UI 和 landing orchestration 引用同一结构；Human Gate 已收敛为轻量人类决策记录，不强制关联 Task；Code 已能检查已写出的 `Human Gate 记录` 文本块和 YAML 结构；landing-report 已能按 Human Gate 子类分流缺口（必须人类决策记录 21、规范口径说明 5、承接实现支持 1、Code 降级提示/覆盖 1）；后续仍需 Web/事实源回写消费 |
| 规范落地治理吸收 | 已落地 | `docs/specs/00`、`04` 系列、`06`、`07`、`10`、`26`、`41` | 规范落地要求、环境适配、运行投影、平台清单、LDVH/个人特别要求已重组为 04 系列链路 |
| Web 语义化与阅读体验改进 | 已部分落地 | `web/`、`web/docs/`、`docs/specs/08-Web信息同步实现规范.md` | 已有 Dashboard、ObjectList、ObjectDetail、Validate、Changelog、ReadingPanel 等实现与设计文档；Human Gate 证据导出、受控回写和检查面仍未闭环 |
| ECC 运行系统经验对照 | 已形成最终结论并完成规范对齐 | §2.2、`docs/specs/04.03-环境能力清单与环境适配规范.md` §6 | 最终结论见 §2.2：LDVH 安装模型与 ECC 完全不同，唯一保留 target adapter 思想落地为 04.06 §6；04 主轴已收回 5 层 |
| Web Validate 落地检查摘要 | 已落地基础展示 | `tools/specs_validate.py web-validate`、`web/api/routes/validate.ts`、`web/src/pages/Validate.tsx`、`web/docs/05-Validate.md` | Validate 页面已消费 Code 只读数据合同，展示 `landingCheck`、`landingReport`、`humanGateReport` 摘要、剩余缺口和能力缺口；当前仍为展示和诊断面，不替代事实源或 Human Gate |

仍在推进中的事项不因本文标注而自动关闭。本文只记录“已进入正式承接位置或 Code 实现”的事实，后续验收仍应回到对应规范、Code 测试、运行投影、工作对象或 Human Gate 证据。

---

## 2. 核心判断

LDVH 当前整体推进方向符合 AI 执行者的真实需求。

LDVH 的价值不在于让 AI 记住更多规则，而在于用稳定事实源、明确入口、工作模型、工作流程、Code、Web 和 Human Gate 托住 AI 的概率性、上下文依赖和无状态问题，使 AI 能更稳定地读取、判断、执行、验证、回写和学习。

当前方向可以概括为：

```text
从"AI 能读懂规范"
推进到"AI 能基于最小上下文快速判断"
再推进到"AI 能通过 Code 和流程稳定执行、验证、停顿和回写"
```

更准确的判断是：理念层和规范层较好符合 AI 需求，工具层和执行层仍需继续补齐。

规范落地要求的价值边界：

```text
规范服务 AI
机制托住 AI
Code 减轻 AI
Web 协调 Human
事实源沉淀闭环
```

### 2.1 ECC 对照后的路线调整

研读工作区 ECC 项目、00 总纲和 06 工作流程基础规范后，当前推进路线需要从“继续细挖单类缺口”调整为“先把复杂工作流程的过程输出规范化，再由具体流程定义自己的只读计划、状态、诊断或汇总输出”。

ECC 值得学习的不是大量 Rules、Skills、Commands、Agents 或完整安装器，而是组织方法：用 manifest 描述能力边界，用 plan 先只读解析操作，用统一入口降低发现成本，用 status/doctor 聚合健康状态，用跨环境 target/adapters 组织运行投影。

LDVH 吸收这些经验时必须受 00 总纲和 06 工作流程基础规范约束：

1. 以 AI 执行者为第一服务对象，优先降低 AI 定位、判断、验证和回写成本；
2. 维持开发环境、工作模型、工作流程、Code、Web 五类构成要素边界，不把 ECC 的运行资产形态原样搬入 LDVH；
3. 事实源必须回 Git 文件，不能引入 SQLite、缓存、工具输出或 Web 状态作为最终事实源；
4. 遵守防递归建设原则，先做能服务当前 41/42 dogfood 的最小只读过程输出，不扩张为完整 CLI、安装器、repair、长期状态源或多平台分发系统；
5. `landing-plan`、status、doctor、多视角汇总等都应被视为具体工作流程的过程输出，默认不是事实源，不得隐式触发写入、apply、repair 或缺口关闭。

因此当前路线已调整为：06 先定义工作流程过程输出的通用边界；41 将 `landing-plan` 定义为规范落地统筹流程的只读过程输出合同；42 消费 `landing-plan` 做检查、状态聚合和缺口诊断；44 将"多视角"收敛为模式选择与汇总输出，而不套用 `landing-plan`；07/08/09/10 分别约束 Code 实现、Web 展示、事实源回写和验证。下一步应基于这条路线重构 04 系列，而不是继续把 `landing-plan` 解释为 00 级新层。

### 2.2 ECC 借鉴最终结论（2026-06-10）

经逐模块对照和 LDVH 实际安装模型确认后，得出以下最终判断：

**LDVH 的安装模型与 ECC 完全不同：**

```
LDVH：git clone → README → 用户对话触发工作流程 → AI 检查引导 → 完成
ECC： CLI 执行 → manifest → profile → plan → executor → state → doctor/repair
```

LDVH 不装多个扩展能力，没有配置选择需求。后续如需扩展技能或 Agent，也是通过增加工作流程，让用户通过对话让 AI 来安装，不是通过 CLI 工具配置。

**ECC 有哪些是 LDVH 不需要的：**

| ECC 概念 | LDVH 不需要的原因 |
|---|---|
| manifests（组件/模块/配置定义） | LDVH 不是一个可配置安装的系统，只有一个项目 |
| profiles（安装变体选择） | 无选择需求，一份项目对应一份规范 |
| install plan（安装计划生成） | 已在 41 landing-plan 中作为工作流程过程输出，不搬 ECC 语义 |
| executor（安装执行器） | AI 对话本身就是执行器，不需要独立的安装执行模块 |
| install state（安装状态持久化） | LDVH 不保存安装状态，42 只做即时检查 |
| doctor/repair（诊断修复） | 工作流程本身包含检查和引导，不需要独立诊断修复合流 |
| lifecycle（安装/修复/卸载生命周期） | 不是一个需要卸载和修复的安装器系统 |

**唯一值得保留的：**

| ECC 概念 | LDVH 吸收方式 | 落地位置 |
|---|---|---|
| target adapter 分层思想 | 每个平台声明自己的实体在哪、有什么约束，不创建安装器、不保存安装状态 | 04.06 §6 平台实体映射规则 |

**主轴回收结论：**

04 系列主轴应从之前过度转译的 9 层收回为 5 层：

```
正式规范 → 规范落地要求 → 保障机制 → 环境适配映射 → 运行投影
```

多出来的概念各回各家：落地承接单元归 04.03 内部规则，环境适配规则归 04.06 内部规则，候选/实际证据区分归 41/42 内部规则，分流/事实源回写归 09 内部规则。ECC 借鉴已完成，不应让转译痕迹留在 04 主轴中。

---

## 3. AI 执行者需求与当前匹配

### 3.1 AI 关键需求

| 需求维度 | AI 需要什么 |
|---|---|
| 明确边界 | 当前任务场景、应读事实源、可改范围、只能参考的内容、必须暂停的时机 |
| 稳定事实 | 能回到 Git 可追踪文件的事实，而非聊天记录、模型记忆或工具缓存 |
| 关联信息 | 当前任务关联的规范、Task、ADR、Memo、Pitfall、Code、Web 或运行投影 |
| 可见状态 | 任务、决策、缺口、LDVH落地与检查和验证的当前状态 |
| 可用工具 | 可机械化的检查、索引、聚合、验证和受控写入应交给 Code |
| 停顿机制 | 明确知道何时不能自行继续 |
| 验证反馈 | 可复现反馈，而非"看起来可以"等自述 |
| 经验回流 | 重复错误、规范缺口、事实源漂移回流到 Pitfall、Memo、ADR 等 |

### 3.2 已符合 AI 需求的部分

| 领域 | 当前状态 | 符合的需求维度 |
|---|---|---|
| AI 入口方向 | LDVH-AI-ENTRY.md 提供最小读取顺序和场景路由 | 快速定位 |
| 五类构成要素分工 | 00 拆成开发环境、工作模型、工作流程、Code、Web | 边界判断 |
| 工作流程逐步成型 | 41 统筹、42 LDVH落地与检查、44 多角色思考 | 稳定执行 |
| 工作模型承载事实 | ADR、Task、Intent、Memo、Pitfall 围绕同一组事实追踪 | 无状态补偿 |
| Code 方向正确 | 结构校验、对象校验、commit 校验和 landing report 已部分覆盖 | 确定性反馈 |
| Human Gate 逐步成型 | 多规范明确高影响写入、入口变更、状态关闭需 Gate | 停顿机制 |
| 规范落地要求机制 | 04 系列拆出"规范→落地要求→保障机制→环境适配→运行投影→漂移检查"链路 | 综合需求 |

### 3.3 仍不够符合的部分

| 缺口 | 影响 | 对应需求维度 |
|---|---|---|
| AI 仍需读太多 | 复杂任务可能需同时读取 10+ 规范 | 明确边界、可用工具 |
| 规范落地要求已有基础聚合视图但缺验证证据接入 | `landing-report` 已能聚合正式规范落地要求，但状态仍为启发式，尚未接入测试证据、工作对象证据或 Human 确认记录 | 可见状态、可用工具、验证反馈 |
| 工作对象事实源存在历史漂移风险 | 旧路径、缺失引用会制造看似稳定但实际失效的依据 | 稳定事实 |
| Human Gate 证据机制仍需回写消费 | 最小证据结构已进入 06、08、21、26、41，Code 已能检查已写出的记录块，但 Web 和事实源回写链路尚未消费 | 停顿机制、验证反馈 |
| Web 尚未充分承担 AI-Human 桥接 | Human 看不见 AI 的方向、风险、状态和待确认事项 | 可见状态 |
| 继续抽象存在负担风险 | 过多流程/对象/规则增加选择和上下文负担 | 明确边界 |
| 规范落地要求存在形式化风险 | 填表不等于落地，有保障机制描述不等于已实例化 | 验证反馈 |

---

## 4. 当前缺口清单

以下为按 `docs/specs/41-landing-orchestration-规范落地统筹.md` 执行检查后的主要缺口。当前 `tools/specs_validate.py landing-report` Code 派生聚合范围为 41 篇正式规范、185 条规范落地要求 + 4 条能力缺口。

当前 `landing-report` 输出摘要为：

| 状态 | 数量 |
|---|---:|
| closed | 111 |
| open | 14 |
| degraded | 35 |
| needs_human_gate | 25 |
| 能力缺口（degraded） | 4 |
| **未关闭缺口总计** | **78** |

未关闭缺口按 owner_area 分类：

| 分类 | 数量 | 主要状态 |
|---|---:|---|
| Code / Test | 16 | degraded 4、open 12 |
| Human Gate | 28 | degraded 3、needs_human_gate 24、open 1 |
| 运行投影 | 29 | degraded 29 |
| Specs | 1 | needs_human_gate 1 |
| Workflow / Skill | 4 | degraded 3、open 1 |

上述状态是 Code 派生启发式，不是最终事实源。关闭、降级或转入 Human Gate 仍需回到正式规范、验证证据、工作对象或 Human 确认记录。

运行投影 29 个 degraded 缺口已经进入 `landing-plan` 的 `gaps` 与 `proposed_actions`，并由 remediation 分类给出初步行动方向。经 ECC 对照和 06 过程输出规范化后，这些缺口不应继续只按单项逐条修复，而应由 41/42 过程输出判断是补入口、补 Code、补 Web、补 docs、补 Task，还是保持 degraded。

状态说明：`closed-basic` 表示基础实现已落地，但仍存在增强或证据接入后续项。

| 编号 | 缺口 | 状态 | 影响 | 建议承接 |
|---|---|---|---|---|
| G-01 | 缺少规范落地要求全局聚合报告命令 | closed-basic | 基础命令已落地，AI 不再必须手工跨文件聚合；但验证状态、运行投影漂移和事实证据仍需扩展 | 已由 `tools/specs_validate.py landing-report` 承接；后续接入验证证据、工作对象证据、Human 确认和漂移检查 |
| G-02 | 运行投影漂移检查 Code | closed-basic | `tools/specs_validate.py runtime-projection` 已能检查项目内运行投影是否缺少权威来源、引用不存在规范、复制规范正文或路径漂移；当前项目内检查结果为 closed | 已由 `tools/specs_validate.py runtime-projection` 承接；后续需扩展到用户级运行投影检查 |
| G-03 | AI 统一入口已指向 42 和 41，但持久运行投影仍需检查 | closed-basic | `LDVH-AI-ENTRY.md` 已提示 LDVH落地与检查进入 42，specs 变更、落地缺口或运行投影漂移进入 41；但工作区级薄入口、环境入口或管辖项目入口是否同步仍需 42 现场检查 | 42 + 运行投影：检查所有已授权入口是否只保留薄引用且未复制正文 |
| G-04 | 42 LDVH落地与检查 dogfood | closed-basic | `tools/specs_validate.py ldvh-landing-check` 已能对 LDVH 自身执行只读检查，汇总 governed-projects、landing-report、runtime-projection、human-gate-report、fact_validate 和 spec_validate；当前 dogfood 结果：governed_projects closed、landing_report open、runtime_projection closed、human_gate degraded、fact_validate closed、spec_validate closed | 已由 `tools/specs_validate.py ldvh-landing-check` 承接；后续需持续复检并补齐 human_gate 和 landing_report 缺口 |
| G-05 | 43 独立产品审计已取消 | removed | 原 43 职责已并入 42；不得把 43 当作后置独立审计流程恢复 | 40 保留 removed 槽位；后续检查回到 42 |
| G-06 | 生命周期触发仍以人工降级为主 | degraded | specs 变更、commit 前后、会话停止前等触发依赖 AI 记忆 | 运行投影 + Code：Hook / CI / 人工降级清单逐步承接 |
| G-07 | 运行闭环测试用例事实源位置未稳定 | open | 具体流程的可测试性锚点无法沉淀为长期测试用例 | 10 + Code：确定测试用例事实源或先以 tests 承接 |
| G-08 | 工作流程 45-58 仍为候选 | open | 意图接入、任务规划、任务执行、验证关闭等最小运作流程尚未 formalize | 工作流程：逐个讨论并创建或降级 |
| G-09 | Human Gate 最小证据结构已定义，Code 已能检查记录块 | closed-basic | 06 已定义最小记录块（时间/决策/范围/约束），Task、ADR、Web UI 和 41 已引用；Human Gate 已收敛为轻量人类决策记录，不强制关联 Task；`tools/specs_validate.py human-gate-report` 已能检查已写出的 `Human Gate 记录` 是否缺字段或字段为空；landing-report 已能按 Human Gate 子类分流缺口（必须人类决策记录 21、规范口径说明 5、承接实现支持 1、Code 降级提示/覆盖 1）；但 Web 尚未形成自动导出、受控写入或事实源回写链路 | Web / 工作对象：实现 Gate 证据导出、回写与消费检查 |
| G-10 | Web 信息同步已形成基础检查摘要，Human Gate 和回写闭环仍未完成 | degraded | Validate 页面已消费 `web-validate` 只读数据合同，展示 42 检查、landing-report、Human Gate、剩余缺口和能力缺口摘要；但 Human-facing 确认、受控编辑、Gate UI、证据导出和事实源回写未形成稳定运行面 | Web：继续展示风险、待确认事项、验证证据、缺口状态、事实源漂移、Task 关闭条件和 ADR 影响，并补 Human Gate 证据导出与受控回写 |
| G-11 | 工作对象事实源历史路径漂移 | closed-basic | `python3 tools/fact_validate.py ldvh-base` 当前报告 files=89 errors=0 warnings=0；旧路径引用已修复为当前规范路径，历史引用已保留为描述性历史叙事；后续新增事实源仍需持续校验 | 已由 `tools/fact_validate.py` 承接；后续需在 42 检查中持续消费 |

---

## 5. 候选事项清单

候选事项是已显示出复用价值、治理价值或风险提示价值，但尚未完全确定正式归属的内容。状态含义：

| 状态 | 含义 |
|---|---|
| covered | 已由当前正式规范主体覆盖，本文仅保留一致性提醒 |
| candidate | 有价值，但需在承接位置继续讨论或细化 |
| deferred | 暂缓，不进入当前最小运作主线 |
| rejected | 不吸收，后续不得以同一理由恢复 |

### 5.1 已由正式规范主体覆盖的事项

| 候选事项 | 当前承接 |
|---|---|
| LDVH 是面向 Vibe Coding 的规范驱动 AI 工作 Harness | 00 |
| AI 执行者是第一服务对象，Human 保留关键判断权 | 00、06、08 |
| Git 可追踪文件是最终事实源 | 00、09 |
| 五类构成要素与事实源贯穿原则 | 00、01 |
| Intent → Plan → Execute → Verify → Record → Learn | 00、06、40；其中 45-58 具体流程仍为 candidate |
| Task 作为执行治理锚点 | 00、05、20、26 |
| Human Gate 是判断权、授权权和责任边界 | 00、06、08、21-26、41-44 |
| Web 优先作为事实源态势入口和 Human Gate 辅助界面 | 00、08、web/docs、web 实现基础 |
| 非 LDVH 来源内容必须先接管再生效 | 11、11.01、40 的 57 candidate |
| 工作模型集合索引和对象状态边界 | 20；21-26 active，27-29 removed，30-34 deferred，35-39 reserved |
| 工作流程集合索引和候选状态边界 | 40；41-44 active，45-58 candidate，59 reserved |
| 运行投影和环境适配链路 | 04.02、04.03、04.06、04.07、04.08、LDVH-AI-ENTRY.md |

### 5.2 需要继续承接的候选事项

| 候选事项 | 优先承接位置 | 承接要求 |
|---|---|---|
| Core Loop 各阶段的具体流程 | 40、42-50 | 45-50 已登记为 candidate；应逐个判断意图接入、任务规划、任务执行、验证关闭、决策记录、变更提交是否独立成 active 流程 |
| 反合理化红旗与失败暂停 | 06、10、12、26、47、53 | 已进入 06、10、26、41 的基础规则；后续 47/53/12 可继续补具体执行与审查场景 |
| closure_evidence 结构化证据层 | 05.01、10、26、47、48、08 | 26 已补关闭证据最低要求，10/41 已补验证与证据边界；后续再判断是否需要结构化字段、47/48 流程规则和 Web 展示 |
| 独立审计 Agent 与只读审阅边界 | 06、41、44、47、53、54、10 | 44 已提供多角色思考流程；高风险任务、规范变更、事实源状态流转和关闭判断仍需在 47/54 中细化审阅边界 |
| 工具权限面和阶段化能力暴露 | 04.03、06、07、10、41 | Intake、Plan、Execute、Verify、Review、Close 不应默认暴露同一套写入与执行能力；应由环境适配清单、运行投影和工具实现共同承接 |
| 渐进式上下文加载与 Context Pack | 06、07、10、40、55 | 06 已补 Context 派生输入边界和“少读不是不读”；后续由 Code/Web/55 继续承接最小上下文生成 |
| 第三方 Skill 脚手架与治理接管 | 11、11.01、40、57 | 第三方 Skill 可作为能力供给方，持续开发和正式产物必须回到 LDVH 主控、验证和事实源回写；57 已登记为 candidate |
| Trae Spec 或其他平台规划产物纳入 Task 治理 | 11、26、40、45、46、57 | 平台规划产物不是执行授权；被 LDVH 吸收后才可作为执行依据；不得形成第二权威事实源 |
| 多项目边界与管辖项目配置校准 | 03.05、40、52、42 | 当前以根目录管辖项目配置承接，不恢复 Profile 工作模型或 Profile tags 字段路线；52 已登记为 candidate |
| Web 三层信息架构 | 08、Web 实现文档、10、42 | Workbench、Docs、Runtime Panel 可作为设计参考；正式实现不得绕过 08 和 Git 文件事实源；优先与检查面、Gate 证据和风险呈现对齐 |
| 最佳实践升级流程 | 12、40、58 | 当最佳实践反复承担强制规则功能时，必须按内容性质升级到正式规范、工作模型、工作流程、Code、Web 或测试；58 已登记为 candidate |
| 工作对象历史路径漂移修复 | Task、42、Code | 应优先处理 `fact_validate.py ldvh-base` 暴露的路径不存在和证据格式提示，避免旧路径继续误导 AI |
| landing-report 证据接入 | 07、10、41、42、Code | 在现有状态聚合上接入验证结果、工作对象证据、Human Gate 记录、运行投影漂移和回写建议 |
| Human Gate 证据导出与消费 | 08、21、26、41、42、Web | 在最小证据结构和 Code 检查基础上，补 Web 展示、导出、受控回写和事实源消费链路 |

### 5.3 暂缓事项

| 候选事项 | 暂缓原因 |
|---|---|
| 自建 MCP 作为核心能力入口 | 当前 Code、Web、Validator、Context Pack 和受控写入边界尚未稳定；优先本地 Code 和 Web |
| ProjectGroup 工作模型 | 当前管辖项目配置已能承接最小项目名册；跨项目聚合需求未稳定 |
| Automation / Cron 工作模型 | Task、Change、Verify、Web 和 Validator 闭环尚未稳定 |
| 大规模生成 Rules、Skill、Validators 或 Web schema | 规范结构化程度、字段契约、状态机、Human Gate 条件和测试覆盖仍需逐步整理 |
| Web 开放式写入后台 | 受控轻写入可以讨论，开放式 YAML 编辑或任意字段写入不得先行 |

### 5.4 不吸收事项

| 候选事项 | 理由 |
|---|---|
| 隐藏本地状态目录、memory store、local database 或 Web 数据库作为核心事实源 | 会制造第二事实源 |
| AI 自动 push、release、merge | 属于 Human 权限边界 |
| 分数式完成标准 | LDVH 完成标准应基于 acceptance、验证、evidence、Human Gate、Change 和状态机 |
| 人格化 Agent 系统 | LDVH 中的 Agent 是独立上下文、专业审计或隔离评估能力，不是人格角色系统 |
| AI 主控仅凭自身总结完成审查和关闭 | Verify 必须具备外部性和可追溯证据 |
| 平台能力替代 LDVH 内核 | Codex、Trae、MCP、第三方 Skill 或 Web 能增强底座，但不能替代事实模型、Task 治理、Human Gate 和运行闭环 |

---

## 6. specs 文档体系与推进原则

### 6.1 不建议为编号完美而大规模重排

当前 `docs/specs/` 主干已形成相对稳定的 AI 入口和规范定位。若仅为追求编号顺序上的理论完整而重编号，会带来路径引用漂移、AI 入口漂移、Web 预览失效、Code 校验断裂和历史工作对象引用失效等风险。

更符合 AI 需求的方向是：保持当前主干稳定，强化边界说明、入口路由、Code 聚合、Human Gate 证据和局部重组。

### 6.2 文档治理与事实源的关系

```text
01 负责目录与编号映射
03 负责 Markdown 文档工作区治理
09 负责跨 Markdown、YAML、Code、Web、运行投影和工具输出的最终事实源权威原则
```

事实源不是文档治理的前置章节，也不是 LDVH 的第六类构成要素。00 总纲已明确：事实源是贯穿开发环境、工作模型、工作流程、Code 和 Web 的底层权威原则。

### 6.3 当前主干应重点做结构澄清和局部重组

1. 04 系列需整理为更清晰的"规范落地与环境适配链路"；
2. 03 与 09 的职责需避免混淆；
3. 01 需更明确展示五类构成要素与当前编号区段的映射；
4. 20 和 40 应继续作为集合索引；
5. candidate、planned、reserved 项不应被 AI 当成已创建正式 Markdown 路径；
6. research/refs 的结论不应被直接当作 specs 正文事实消费；
7. Code/Web/运行投影不应被误升格为最终事实源。

### 6.4 后续扩展区规划

| 构成要素 | 当前基础规范 | 当前集合索引 | 未来扩展区 |
|---|---|---|---|
| 开发环境 | 04 | 暂无 | 60-69 |
| 工作模型 | 05 | 20 | 21-39 |
| 工作流程 | 06 | 40 | 41-59 |
| Code | 07 | 暂无 | 70-79 |
| Web | 08 | 暂无 | 80-89 |

未来如需真正启用 60-89，应先经 Human Gate，明确编号区段定位、集合索引职责、是否创建正式 Markdown 文件、是否影响 Code/Web/入口/运行投影，并通过校验确认不会造成事实源漂移。

### 6.5 面向 AI 需求的推进原则

| 原则 | 含义 |
|---|---|
| 让 AI 少读 | 优先建设聚合、索引、摘要和最小上下文能力，而非减少事实源 |
| 让 AI 少猜 | 能机械检查的内容应交给 Code |
| 让 AI 停得准 | Human Gate 按类型分层：澄清/授权/风险/验收/决策 |
| 让 AI 做完后能证明 | Task、ADR、检查结果应能回答做了什么、为什么、依据、验证、结果、回写、谁确认、残留风险 |
| 少新增抽象，多跑闭环 | 每新增一层抽象后，应优先安排一次实例化验证 |
| 规范落地要求少形式、多实例 | 每项要求应能被追问：是否降低 AI 负担、是否有保障机制、是否已映射到可定位实体、是否有验证方式 |

---

## 7. 建议优先行动

1. **~~设计并实现只读 `landing-plan` 最小输出~~**：已完成基础版。第一版已聚合 `landing-report`、`runtime-projection`、`human-gate-report`、`ldvh-landing-check`、`fact_validate` 和 `specs_validate`，输出 `scope`、`facts_read`、`capabilities`、`requirements`、`gaps`、`proposed_actions`、`writes_required`、`human_gate`、`validation_plan` 和 `writeback_targets`；默认只读，不写入、不 repair、不创建长期状态源。

2. **~~规范工作流程过程输出边界~~**：已完成第一轮承接。06 已定义“工作流程过程输出”通用规则；41 定义 `landing-plan` 合同；42 定义消费 `landing-plan` 和自身检查/状态/诊断输出边界；44 定义多视角触发、模式选择和汇总输出；07/08/09/10 分别约束实现、展示、回写和验证。

3. **~~重构 04 系列主轴~~**：已完成。第一轮 ECC 对照后主轴重构为 9 层；经逐模块对照和 LDVH 实际安装模型确认后，最终结论为收回 5 层（正式规范→落地要求→保障机制→环境适配→运行投影）。ECC 唯一保留的 target adapter 思想已落地为 04.06 §6 平台实体映射规则。其余概念（落地承接单元、环境适配规则、候选/实际证据区分、分流/回写）归入各子文档或工作流程内部规则，不挂在 04 主轴。详见 §2.2。

4. **建立平台能力映射表作为辅助线**：吸收 ECC 跨环境 target/adapters 的组织方法，但不直接创建多平台持久入口；先映射入口可见、流程复用、子 Agent、生命周期触发、确定性反馈、Human 确认在 Trae/Codex 等环境中的候选承接与降级边界。

5. **~~修复或分流工作对象事实源漂移~~**：已完成。`fact_validate.py ldvh-base` 当前报告 files=89 errors=0 warnings=0。

6. **~~Dogfood 42~~**：已完成。`tools/specs_validate.py ldvh-landing-check` 已能对 LDVH 自身执行只读检查；当前 dogfood 结果为 landing_report open、human_gate degraded，其余 closed。

7. **推进 Human Gate 证据回写消费**：最小证据结构已进入 06、08、21、26 和 41，Human Gate 已收敛为轻量人类决策记录，Code 已能检查已写出的 `Human Gate 记录`；landing-report 已能按 Human Gate 子类分流缺口；当前 28 个 Human Gate 缺口中 21 个为"未来触发时记录"，不需要现在补记录；Validate 已展示 Human Gate 摘要，但 Web/Human-facing 确认、导出和事实源回写仍需补齐。

8. **暂缓完整 CLI、apply/repair 和规模化资产库**：统一 CLI、受控写入、repair、多平台自动分发、大量 Skill/Agent 化都不作为当前第一步；先在现有 Code 和 Web 中稳定只读过程输出，dogfood 稳定后再讨论是否包装为统一 `ldvh` 命令。

---

## 8. 后续吸收建议

| 内容 | 建议吸收出口 |
|---|---|
| AI 需求维度 | 00 或最佳实践 |
| 最小上下文生成 | 07、41 或后续 Code Task |
| landing report | 基础实现已进入 Code、测试和 41；后续吸收验证状态、证据来源、漂移检查和 Web 消费入口 |
| 工作流程过程输出 | 已进入 06、41、42、44、07、08、09、10；后续由具体流程按需定义输出合同 |
| landing-plan | 已进入 41 过程输出合同和 Code 最小实现；后续应由 42、Web 和 04 系列继续消费，不作为事实源或 00 级新层 |
| Web Validate 检查摘要 | 已进入 Code 合同、Web API、Validate 页面和 Web 文档；后续补 Human Gate 确认、证据导出和受控回写 |
| Human Gate 证据结构 | 基础结构已进入 06、08、21、26、41；Code 检查已由 `tools/specs_validate.py human-gate-report` 承接；后续由 Web/42 和工作对象回写链路消费 |
| Web Human-facing 检查面 | 08 和 Web 实现 Task |
| 事实源漂移修复 | Task 或 42 检查发现 |
| 少新增抽象、多跑闭环 | 00 防递归建设原则、12 最佳实践或 41/42 检查建议 |
| 规范落地要求价值边界与形式化风险 | 00 价值一致性判断、04.01、41、Code 校验诊断 |
| specs 主干稳定与局部重组 | 01、03、04、20、40、41 或后续重构 Task |
| 文档治理与事实源关系 | 03、09、01 |
| 60-89 未来扩展区规划 | 01，需 Human Gate 后再进入正式编号分区 |
| 候选事项承接 | 对应正式规范按 04.01 声明规范落地要求 |

适合进入 00 的只应是原则级内容：

```text
让 AI 少读、少猜、停得准、做完能证明。
少新增抽象，多跑现有闭环。
当 AI 需要反复跨文档聚合时，优先用 Code 或 Web 承接，而不是复制更多入口摘要。
新增机制必须证明服务 LDVH 价值实现标准，否则不进入核心体系。
```

不宜进入 00 的内容包括：规范落地要求字段定义、具体状态、环境适配映射细则、Skill 命名、Human Gate 证据字段、landing report 格式、Web 页面字段和工具实现细节。

---

## 9. 候选事项升级前确认点

以下情况在升级候选事项前，建议评估 Human Gate：

1. 将 candidate 升级为正式规范规则、工作模型、工作流程、Code、Web 或运行投影；
2. 将 deferred 升级为 candidate 或正式规则；
3. 恢复 rejected 事项；
4. 改变候选事项优先承接位置；
5. 删除仍被其他正式规范引用的候选事项；
6. 将候选事项直接写成 00 级原则；
7. 创建新的工作模型、工作流程或实现层能力来承接候选事项。

升级前至少检查：

| 检查项 | 标准 |
|---|---|
| 归属唯一 | 已选择唯一优先承接位置 |
| 状态清晰 | covered、candidate、deferred、rejected 未混用 |
| 不越权 | candidate 未被当作 active 规则执行 |
| 不重复 | 未在多个正式规范复制维护同一规则正文 |
| 不恢复取消项 | Profile、Evidence、ProjectGroup、Automation 等已取消或暂缓项未绕过本文恢复 |
| 事实源边界 | 未把 research、refs、聊天、Web、Skill 或 Agent 输出当作最终事实源 |

---

## 10. 待补齐事项

1. ~~`landing-plan` 最小输出合同~~：已在 `tools/specs_validate.py` 中形成只读 JSON 与文本报告，并由 41 定义为过程输出合同；后续应继续校准字段语义、证据来源和 Web 消费，不写入、不 repair、不创建长期状态源；
2. 42-58 工作流程逐步创建后，应同步检查 §5.2 的候选事项是否已被承接或需要降级；
3. Task 执行、验证与关闭流程稳定后，应重新评估 closure_evidence 结构化证据层是否需要进入 26、47 或 48 的强规则；
4. Web 实现文档稳定后，应重新评估 Web 三层信息架构是否仍需保留在 candidate 清单中；
5. Code 校验能力增强后，可补充 candidate、deferred、rejected 误用检查；
6. Code 聚合报告已增加缺口分类输出（gap_categories）、运行投影漂移检查（runtime-projection）、Human Gate 报告（human-gate-report）、LDVH dogfood 检查（ldvh-landing-check）、`landing-plan` 和 `web-validate`；后续应继续扩展验证状态、证据来源和 candidate/deferred/rejected 误用检查；
7. Dogfood 42 已完成，当前 dogfood 结果为 landing_report open、human_gate degraded，其余 closed；后续应回看 §4 缺口清单并标注哪些已被正式承接；
8. 本文中已完成的缺口（G-02、G-04、G-11）和优先行动（§7 第 1、2、5、6 项）已标注完成状态；后续稳定结论被正式规范、工作流程或 Code 吸收后，应持续标注已吸收状态；
9. ~~`fact_validate.py ldvh-base` 暴露的历史路径漂移和证据格式提示~~：已修复，当前 files=89 errors=0 warnings=0；
10. Human Gate 证据回写消费、Web 检查面和受控轻写入，应按 08、41、42 和 Web 实现文档继续补齐；当前 Validate 已展示 Human Gate 摘要，但尚未形成确认和回写闭环；
11. 运行投影 29 个 degraded 缺口需继续通过 `landing-plan.gaps` 和 `landing-plan.proposed_actions` 判断是入口缺失、证据不足、平台能力限制还是规范口径问题；
12. ECC manifest 经验只先转译为能力/运行投影最小索引，不作为安装器；平台能力映射先作为诊断表，不直接创建多环境入口；完整 CLI、apply/repair、长期状态源、多平台自动分发和大量 Skill/Agent 化暂缓；
13. ~~04 系列是下一轮主要重构对象~~：已完成主轴重构并收回为 5 层（§2.2）。后续 04.04/04.05 校准和 04.07/04.08 实测补齐按需进行，不构成紧急重构项。
