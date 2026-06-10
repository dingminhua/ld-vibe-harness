# LDVH 学习 ECC 的深度研究：到底要学什么

> 创建日期：2026-06-11
> 定位：从五个独立视角深入研究 LDVH 与 ECC 后的汇总参考文档
> 性质：参考文档，不直接构成 LDVH 正式规范或实施承诺
> 研究方法：5 个独立 Agent 分别从 ECC 架构设计、ECC 机制细节、LDVH 已有评估、ECC 预处理深度分析、LDVH 核心需求五个视角独立研究，再汇总交叉验证
> 来源：ECC 源码及文档、`ecc-preprocess/docs-and-specs/`、`docs/refs/07`、`docs/refs/08`、`docs/research/18`、`docs/research/19`、`docs/specs/00`、`docs/specs/06`、`docs/specs/41`、`docs/specs/42`、`docs/specs/09`

---

## 1. 核心结论

**LDVH 要学的是 ECC 的组织方法，不是 ECC 的内容、规模或安装模型。**

ECC 的价值不在于它有多少 agents、skills、commands、rules，而在于它已经实践过一组运行系统工程化方法。LDVH 应学习这些方法的结构，但必须按 LDVH 自身的目标转译：服务 AI 执行者、回到 Git 文件事实源、遵守 Human Gate 和防递归建设原则。

更具体地说，LDVH 要学的是：

```text
如何让 AI 协作资产具备工程系统的可声明性、可计划性、可验证性和可观察性
```

而不是：

```text
如何复制 ECC 的安装器、CLI、Skills 库、Rules 库或跨平台分发系统
```

---

## 2. LDVH 与 ECC 的根本差异

在讨论"学什么"之前，必须先明确两者的根本差异，否则容易把 ECC 的实现当成 LDVH 的需求。

### 2.1 安装模型完全不同

```
LDVH：git clone → README → 用户对话触发工作流程 → AI 检查引导 → 完成
ECC： CLI 执行 → manifest → profile → plan → executor → state → doctor/repair
```

LDVH 不装多个扩展能力，没有配置选择需求。后续如需扩展技能或 Agent，也是通过增加工作流程，让用户通过对话让 AI 来安装，不是通过 CLI 工具配置。

### 2.2 事实源模型完全不同

| 维度 | LDVH | ECC |
|---|---|---|
| 最终事实源 | Git 可追踪文件 | 安装状态、manifest、state store |
| 工具输出 | 派生视图，不是事实源 | 可以是状态事实源 |
| 缓存/派生数据 | 禁止作为最终事实源 | 允许作为中间状态 |
| 人工确认 | Human Gate 是硬约束 | 部分场景可自动修复 |

### 2.3 执行模型完全不同

| 维度 | LDVH | ECC |
|---|---|---|
| 执行者 | AI 对话本身就是执行器 | 独立安装执行器 |
| 控制方式 | 工作流程 + Human Gate | plan → apply → verify 流水线 |
| 写入权限 | 受控写入，必须 Human Gate | apply 阶段可自动写入 |
| 修复方式 | 诊断但不自动修复 | doctor → repair 自动链路 |

### 2.4 差异带来的约束

因为以上差异，LDVH 学习 ECC 时必须遵守以下约束：

1. 以 AI 执行者为第一服务对象，优先降低 AI 定位、判断、验证和回写成本；
2. 维持开发环境、工作模型、工作流程、Code、Web 五类构成要素边界，不把 ECC 的运行资产形态原样搬入 LDVH；
3. 事实源必须回 Git 文件，不能引入 SQLite、缓存、工具输出或 Web 状态作为最终事实源；
4. 遵守防递归建设原则，先做能服务当前 41/42 dogfood 的最小只读过程输出，不扩张为完整 CLI、安装器、repair、长期状态源或多平台分发系统；
5. `landing-plan`、status、doctor、多视角汇总等都应被视为具体工作流程的过程输出，默认不是事实源，不得隐式触发写入、apply、repair 或缺口关闭。

---

## 3. 六类值得学习的组织方法

### 3.1 方法一：Manifest 化能力描述

**ECC 做了什么**

ECC 通过 manifest 把能力拆成三层：

| 层次 | 作用 | ECC 实现 |
|---|---|---|
| components | 用户或 AI 可理解的能力包 | `install-components.json` |
| modules | 真实文件、目录、目标平台、依赖、成本、稳定性 | `install-modules.json` |
| profiles | 面向不同使用场景的能力组合 | `install-profiles.json` |

这个结构的价值是：AI 不需要临时扫描整套仓库，就能知道某个能力由哪些文件组成、适用于哪些平台、依赖什么、是否默认启用、风险或成本如何。

**LDVH 应学什么**

LDVH 不应把 manifest 首先理解成安装器。LDVH 更需要的是"规范落地与运行投影索引"——让 AI 能快速回答：当前范围读了哪些事实源、有哪些规范落地要求、有哪些缺口、需要哪些 Human Gate、应如何验证、应回写到哪里。

LDVH 可学习的核心方法：

1. **能力分层声明**：把 LDVH 的能力拆成"Human/AI 理解的能力包"和"实际落地的文件模块"两层，让 AI 不靠猜测就知道某个能力由哪些文件组成
2. **事实源边界字段**：每个 module 声明自己是正式规范还是运行投影、是否允许复制正文、是否需要 Human Gate、验证命令是什么
3. **场景画像**：用 profile 表达不同项目类型应启用哪些能力组合

**LDVH 不应做什么**

1. 不应先做完整安装器
2. 不应把 ECC 的 components/modules/profiles 原样复制
3. 不应把 manifest 输出当作最终事实源
4. 不应做跨平台自动分发

**当前落地状态**：04.06 §6 平台实体映射规则已吸收 target adapter 分层思想；`landing-plan` 输出合同已在 `tools/specs_validate.py` 中实现基础版。

---

### 3.2 方法二：Plan / Apply / Verify 分段执行

**ECC 做了什么**

ECC 的 `install-plan.js` 明确先做只读计划，不修改目标。`install-apply.js` 在确认后执行写入。这个分离把"看清楚要做什么"和"真正写入执行"分开。

**LDVH 应学什么**

LDVH 的写入涉及事实源边界、Human Gate、受控写入、验证证据和回写归属，比 ECC 更需要这种分离。LDVH 可学习的核心方法：

1. **Plan 先只读**：`landing plan` 只读生成范围、事实源、缺口、建议动作、Human Gate、验证计划和回写目标，不做任何写入
2. **Apply 需授权**：在 Human 授权后执行最小必要写入，只写 plan 中列出的文件
3. **Verify 必复检**：复检事实源、运行投影、Code/Web/Skill 状态和验证证据

Plan 输出合同的核心字段：

| 字段 | 含义 |
|---|---|
| `scope` | 本次检查范围 |
| `facts_read` | 已读取或聚合的事实源 |
| `capabilities` | 当前环境能力 |
| `requirements` | 规范落地要求摘要 |
| `gaps` | open / degraded / needs_human_gate 缺口 |
| `proposed_actions` | 候选补齐动作 |
| `writes_required` | 是否涉及写入及目标事实源 |
| `human_gate` | 需要确认的事项 |
| `validation_plan` | 验证方式、命令或人工降级检查 |
| `writeback_targets` | 稳定结论应回写的位置 |

**LDVH 不应做什么**

1. 不应先做自动 apply
2. 不应做 repair
3. 不应允许 plan 输出直接改变状态
4. 不应把计划报告保存成新的长期状态源

**当前落地状态**：`landing-plan` 已在 `tools/specs_validate.py` 中实现只读 JSON 与文本报告；41 已定义为过程输出合同；plan/apply/verify 三段式尚未完整实现，当前只有 plan 阶段。

---

### 3.3 方法三：统一入口降低发现成本

**ECC 做了什么**

ECC 的统一 CLI 让 install、plan、catalog、doctor、repair、status、sessions、work-items 等能力有一致入口。它降低了 AI 和 Human 发现命令的成本。

**LDVH 应学什么**

LDVH 当前已有多个工具（`specs_validate.py`、`fact_validate.py`、`runtime-projection` 等），但入口分散，AI 需要记住不同脚本、参数和输出边界。LDVH 可学习的核心方法：

1. **命令输出合同**：每个命令必须定义输入、输出、exit code、事实源回指、写入边界和验证方式
2. **默认只读**：所有命令默认只读，写入必须显式声明
3. **AI 优先**：先服务 AI 定位和诊断，不服务产品化展示

命令输出合同至少包含：

| 项 | 说明 |
|---|---|
| trigger | 用户怎样触发这项能力 |
| source_of_truth | 必须读取哪些事实源 |
| allowed_tools | 允许调用哪些工具或脚本 |
| forbidden_actions | 明确禁止做什么 |
| output_schema | 输出必须包含哪些字段 |
| stop_points | 何时必须停下来等 Human |
| validation | 完成后跑什么检查 |
| write_policy | 允许写哪里，不允许写哪里 |

**LDVH 不应做什么**

1. 不应为了完整性一次性设计庞大命令树
2. 不应绕开现有 `tools/` 重新造一套
3. 不应让 CLI 输出成为最终事实源
4. 不应把没有明确失败条件的语义判断包装成确定性命令

**当前落地状态**：暂缓完整 CLI 统一，当前以 `tools/specs_validate.py` 的子命令为基础逐步扩展。

---

### 3.4 方法四：Status / Audit / Doctor 诊断聚合

**ECC 做了什么**

ECC 的 `status.js`、`platform-audit.js`、`harness-audit.js`、`doctor.js` 把运行系统的健康情况变成可查询、可聚合、可输出的状态视图。三类工具分工明确：

| 类型 | 作用 | 输出倾向 |
|---|---|---|
| status | 当前状态快照 | 简洁、聚合、面向决策 |
| audit | 按 rubric 检查 | 明细、分数/等级、证据 |
| doctor | 诊断和修复建议 | 原因、建议、可执行计划 |

**LDVH 应学什么**

LDVH 当前也需要让 AI 快速看到：事实源是否可读、工作对象是否可查询、规范落地要求是否有缺口、运行投影是否漂移、Human Gate 是否待确认。LDVH 可学习的核心方法：

1. **三类诊断分离**：status 只做状态快照，audit 按固定 rubric 检查，doctor 只诊断不修复
2. **固定 audit rubric**：AI 不得临时发明评分维度，检查维度必须来自规范
3. **诊断结果不是事实源**：status/audit/doctor 输出都是派生聚合视图，不替代 Git 文件事实源
4. **doctor 不自动修复**：只输出修复计划，修复必须经 Human Gate

LDVH status 可聚合的内容：

| 聚合项 | 来源 |
|---|---|
| 工作对象状态分布 | `ldvh-base/` + fact_cli |
| 规范落地要求缺口 | `docs/specs/` + landing-report |
| 平台适配 open_items | 平台适配清单 |
| 运行投影漂移风险 | 04.02、平台清单、实际入口 |
| Human Gate 待确认事项 | Task、ADR、Web、当前流程输出 |
| 最近验证结果 | Code 输出、测试结果、closure evidence |
| 建议回写位置 | 09 事实源边界和对应模型规范 |

**LDVH 不应做什么**

1. 不应创建长期状态登记表
2. 不应让 status 输出替代 Task 状态、ADR 决策或 42 当前报告
3. 不应把 doctor 诊断结果当作已修复证据
4. 不应在没有 Human Gate 的情况下自动 repair

**当前落地状态**：`tools/specs_validate.py ldvh-landing-check` 已实现基础 dogfood 检查；`landing-report`、`runtime-projection`、`human-gate-report` 已实现基础聚合；完整 status/audit/doctor 分离尚未实现。

---

### 3.5 方法五：跨平台运行投影组织

**ECC 做了什么**

ECC 面向多个 harness 组织不同平台表面，包括 Claude、Codex、Cursor、OpenCode、Gemini、Zed 等。它通过 session adapter 机制实现跨平台适配：定义 canonical interface（`canOpen`、`open`、`getSnapshot`），每个平台实现自己的 adapter，系统通过 adapter registry 统一调度。

**LDVH 应学什么**

LDVH 也需要适配不同 AI 开发环境，但 LDVH 的原则是适配不绑定。LDVH 可学习的核心方法：

1. **target adapter 分层**：每个平台声明自己的实体在哪、有什么约束，不创建安装器、不保存安装状态
2. **薄入口模式**：平台目录只做投影和加载说明，不复制核心规范正文
3. **平台差异留在适配清单**：跨平台差异不写进 00 或通用规范正文

LDVH 平台能力映射表：

| LDVH 需要 | 可能环境能力 | LDVH 边界 |
|---|---|---|
| 入口可见 | Rules / Instructions / AGENTS / README 薄入口 | 只放最小导航和 STOP 点 |
| 流程复用 | Skill / Command | 不替代工作流程正文 |
| 独立审查 | Agent / 子 Agent | 输出回主控，稳定结论回写 |
| 生命周期触发 | Hook / CI / 自动运行 | 不定义规范，只实现触发 |
| 确定性反馈 | Code / CLI / CI | 输出不是事实源 |
| Human 确认 | Web / AskUserQuestion / 手工确认 | 不替代 Human 判断 |

**LDVH 不应做什么**

1. 不应同时为多个平台创建持久入口
2. 不应复制平台规则正文到 LDVH specs
3. 不应让运行投影替代正式规范
4. 不应把某个平台能力写成 LDVH 全局必须能力

**当前落地状态**：04.06 §6 平台实体映射规则已落地；04.07 Trae-Solo 适配清单和 04.08 Codex 适配清单已创建；平台薄入口尚未完整试点。

---

### 3.6 方法六：Rules / Skills / Commands / Agents 资产分层

**ECC 做了什么**

ECC 清楚地区分了 rules、skills、commands、agents 等资产形态，并通过目录和注册方式组织它们。核心分工原则是"rules tell what, skills tell how"。

**LDVH 应学什么**

LDVH 应按 04.03 的环境能力承接边界吸收这种分层，但用 LDVH 自己的构成要素体系重新定义：

| 资产形态 | LDVH 中适合承接 | 不适合承接 |
|---|---|---|
| Rules / Instructions | 入口可见、硬约束摘要、事实源边界提示、STOP 点 | 完整规范正文、对象字段契约、低频流程 |
| Skill | 可复用多步骤流程、标准化输入输出、受控检查步骤 | Human Gate 判断本身、稳定规则正文、子 Agent 调度 |
| Command | Code 或流程的稳定入口 | 独立事实源、未经验证的语义判断 |
| Agent | 独立上下文、专项视角、并行审查、权限边界差异 | 简单问答、单文件小改、最终事实源判断 |
| Hook / CI | 生命周期触发、自动提醒、阻断、检查 | 规范正文、不能机械判断的语义结论 |

**LDVH 不应做什么**

1. 不应复制 ECC 大量 skills、commands、rules
2. 不应因为某个流程重要就写进 Rules
3. 不应因为步骤多就创建 Skill
4. 不应允许 Skill 调度 Agent
5. 不应让 Agent 输出直接成为事实源

**当前落地状态**：04.03 环境能力承接边界规范已定义基础分工；11/11.01 已定义第三方 Skill 接管流程；LDVH 自有 Skill 体系尚未建设。

---

## 4. 学习优先级与推进路线

### 4.1 五阶段推进路线

```text
第一阶段：只读诊断
  → 学习 manifest、plan、status 思路，形成 LDVH 只读诊断能力
  → 目标：AI 能快速回答当前范围、事实源、缺口、Human Gate、验证方式、回写位置

第二阶段：统一入口
  → 学习 ECC 统一 CLI 的发现成本降低方式
  → 目标：AI 不再记忆多个脚本，通过稳定入口获得规范索引、工作对象查询和落地缺口报告

第三阶段：运行投影映射
  → 学习 ECC 跨平台表面，转译为 LDVH 平台适配清单和运行投影映射矩阵
  → 目标：明确不同平台如何承接入口可见、流程复用、子 Agent 思考、生命周期触发和 Human 交互

第四阶段：受控写入
  → 只有前三阶段 dogfood 通过后才讨论 apply、repair、受控写入
  → 目标：在 Human Gate、验证、回写、回滚路径明确后，最小化实现受控写入

第五阶段：稳定复用资产
  → 只有某类流程反复出现、输入输出稳定、验证方式明确、主控接管边界清楚时，才沉淀为 LDVH 自建 Skill、Command、Agent 或运行投影
  → 目标：让资产服务闭环，而不是为了资产规模扩张
```

### 4.2 当前已完成项

| 项 | 状态 | 落地位置 |
|---|---|---|
| landing-plan 只读输出 | 已完成基础版 | `tools/specs_validate.py`、41 过程输出合同 |
| 规范落地要求聚合 | 已完成 | `landing-report` |
| 运行投影漂移检查 | 已完成 | `runtime-projection` |
| Human Gate 报告 | 已完成基础版 | `human-gate-report` |
| LDVH dogfood 检查 | 已完成 | `ldvh-landing-check` |
| 04 系列主轴重构 | 已完成 | 5 层主轴：正式规范→落地要求→保障机制→环境适配→运行投影 |
| target adapter 思想 | 已落地 | 04.06 §6 平台实体映射规则 |
| 06 工作流程过程输出边界 | 已完成 | 06、41、42、44 |

### 4.3 当前应优先推进项

| 优先级 | 推进项 | 理由 |
|---|---|---|
| P0 | 完善 `landing-plan` 输出合同，接入验证证据、工作对象证据和 Human Gate 记录 | 直接服务 41/42 dogfood，是当前最小闭环的核心 |
| P0 | 起草 LDVH manifest schema 候选 | 为平台适配、落地检查和漂移检测提供基础数据结构 |
| P1 | 定义 `ldvh status` 只读输出边界 | 提升 Human 与 AI 对当前健康状态的可见性 |
| P1 | 定义 landing audit 固定 rubric | 防止 AI 临时发明评分维度 |
| P1 | 命令输出合同模板化 | 让 CLI、Skill、平台命令都能稳定执行 |
| P2 | 选择一个平台做薄入口试点 | 验证 manifest 和 plan 在实际平台上的可行性 |
| P2 | 第三方 Skill 接管试点 | 有价值，但应在前几项边界清楚后推进 |

### 4.4 明确暂缓项

| 暂缓项 | 暂缓原因 |
|---|---|
| 完整 CLI 统一 | 先在现有 Code 和 Web 中稳定只读过程输出 |
| apply / repair | dogfood 稳定后再讨论 |
| 长期状态源 | 违反事实源原则 |
| 多平台自动分发 | 先做单平台试点 |
| 大量 Skill / Agent 化 | 先让资产服务闭环，不为规模扩张 |
| ECC commands/skills/rules 全量导入 | 接管机制，不接管内容 |

---

## 5. ECC 中 LDVH 完全不需要的部分

经逐模块对照和 LDVH 实际安装模型确认后，以下 ECC 概念 LDVH 完全不需要：

| ECC 概念 | LDVH 不需要的原因 |
|---|---|
| manifests（组件/模块/配置定义） | LDVH 不是一个可配置安装的系统，只有一个项目 |
| profiles（安装变体选择） | 无选择需求，一份项目对应一份规范 |
| install plan（安装计划生成） | 已在 41 landing-plan 中作为工作流程过程输出，不搬 ECC 语义 |
| executor（安装执行器） | AI 对话本身就是执行器，不需要独立的安装执行模块 |
| install state（安装状态持久化） | LDVH 不保存安装状态，42 只做即时检查 |
| doctor/repair（诊断修复） | 工作流程本身包含检查和引导，不需要独立诊断修复合流 |
| lifecycle（安装/修复/卸载生命周期） | 不是一个需要卸载和修复的安装器系统 |
| session adapter | LDVH 不需要跨 harness 统一会话管理 |
| control plane | LDVH 不需要本地可观测性和会话控制面板 |
| skill-create / auto-update | LDVH 不自动生成规则或自动更新 |

---

## 6. 第三方内容接管模型

学习 ECC 的过程中，第三方内容有天然风险：目标不一致、优先级不同、可能鼓励自动修复、可能缺少 Human Gate、可能把平台机制当成事实源。LDVH 必须通过接管流程控制外部输入。

### 6.1 五级接管模型

| 等级 | 含义 | 允许做什么 | 不允许做什么 |
|---|---|---|---|
| T1 阅读参考 | 只作为外部材料 | 放入 refs、摘录机制、做比较 | 不执行、不安装、不写事实源 |
| T2 受限调用 | 在明确范围内辅助生成候选内容 | 生成草稿、提出检查项 | 不自动采纳、不直接生效 |
| T3 主控审查 | LDVH 主控逐条判断是否符合边界 | 改写、裁剪、标注来源 | 不保留第三方优先级 |
| T4 写入事实源 | 通过 Human Gate 后进入 LDVH 文件 | 写 specs、tools、web、ldvh-base | 不保留"外部权威"身份 |
| T5 稳定复用 | 多次验证后成为稳定机制 | 进入工具、测试、平台入口 | 不跳过持续验证 |

### 6.2 接管流程中的证据要求

LDVH 接管第三方内容时，至少应记录：

1. 第三方来源路径或 URL
2. 接管的是原文、机制、字段、流程还是工具思路
3. 为什么符合 LDVH 价值标准
4. 与现有规范是否冲突
5. 是否需要 Human Gate
6. 验证方式是什么
7. 最终写入了哪里
8. 哪些内容明确拒绝吸收

---

## 7. 学习 ECC 的方法论总结

从五视角交叉研究中，可以提炼出 LDVH 学习外部系统的通用方法论：

### 7.1 核心原则

```text
学方法，不学内容
学结构，不学规模
学组织，不学实现
学约束，不学功能
```

### 7.2 学习步骤

1. **先理解差异**：明确 LDVH 与外部系统在安装模型、事实源模型、执行模型上的根本差异
2. **再提取方法**：从外部系统中提取组织方法，而非具体实现
3. **然后转译**：按 LDVH 的目标、约束和构成要素体系转译方法
4. **最小试点**：先做只读、最小、可 dogfood 的试点
5. **逐步扩展**：dogfood 通过后再扩展到下一阶段
6. **持续校准**：每次扩展后回看是否仍符合 LDVH 价值标准

### 7.3 应避免的三个陷阱

1. **把工具自动化替代结构化控制**：ECC 的自动化能力不能替代 LDVH 对事实源边界、Human Gate 和证据沉淀的结构化约束
2. **把执行逻辑直接生搬硬套**：ECC 的执行逻辑不能忽视 LDVH 对 AI 行为控制、事实源稳定和证据沉淀的约束
3. **把简化机制视为可忽略的替代**：ECC 中的简化机制缺乏对 AI 上下文、状态、规则的结构化管理能力，不能替代 LDVH 的核心设计

---

## 8. ECC 预处理素材索引

以下为 `ecc-preprocess/docs-and-specs/` 中的预处理素材，可作为后续深入研究的基础：

| 文件 | 覆盖内容 | 当前价值 |
|---|---|---|
| `cards/01-ECC-manifests机制卡片.md` | components/modules/profiles 三层安装模型 | P0 候选 |
| `cards/02-ECC-install-plan-apply机制卡片.md` | install plan / apply 分离 | P0 候选 |
| `cards/03-ECC-status-audit-doctor机制卡片.md` | status / audit / doctor 诊断体系 | P0 候选 |
| `cards/04-ECC-commands机制卡片.md` | commands 工作流入口与命令合同 | P1 候选 |
| `cards/05-ECC-skills机制卡片.md` | skills 体系与第三方 Skill 接管 | P1 候选 |
| `cards/06-ECC-rules机制卡片.md` | rules 分层与 rules/skills 分工 | P1 候选 |
| `cards/07-ECC-platform-configs机制卡片.md` | 多平台配置与插件 manifest | P1 候选 |
| `deep-dives/01-ECC-manifest对LDVH运行投影的启发.md` | LDVH manifest schema 和运行投影改造方向 | 深度参考 |
| `deep-dives/02-ECC-harness-audit对LDVH落地检查的启发.md` | 固定 audit rubric 与脚本事实源 | 深度参考 |
| `deep-dives/03-ECC-ADR-skill对LDVH工作对象的启发.md` | ADR Skill 对 LDVH 工作对象流程的启发 | 深度参考 |
| `indexes/99-ECC候选接管清单.md` | P0/P1/P2 候选机制与不建议接管项 | 优先级参考 |
| `indexes/100-ECC预处理工作汇总报告.md` | 预处理工作核心结论 | 总览参考 |

---

## 9. 与 18 号文档的对照

本文与 `docs/research/18-LDVH推进评估与候选事项总览.md` 的关系：

| 维度 | 18 号文档 | 本文档 |
|---|---|---|
| 定位 | LDVH 推进评估与候选事项总览 | LDVH 学习 ECC 的深度研究 |
| 范围 | 涵盖 AI 需求匹配、规范落地缺口、候选事项分流、推进方向、ECC 经验转译 | 专注 ECC 学习的深度研究 |
| ECC 相关内容 | §2.1 路线调整、§2.2 ECC 借鉴最终结论 | 全文深入展开六类组织方法 |
| 核心结论一致 | ECC 唯一保留 target adapter，主轴收回 5 层 | 与 18 号文档一致，但补充了六类方法的详细分析 |
| 推进路线 | §7 建议优先行动 | §4 更细化的五阶段推进路线 |

本文不替代 18 号文档，而是作为 18 号文档 §2.1 和 §2.2 的深度展开和独立研究验证。

---

## 10. 阶段性结论

LDVH 应向 ECC 学习的不是目标、规模或内容库，而是运行系统组织方法。

当前最值得学的六类方法：

1. **用 manifest 描述能力边界**——让 AI 不靠猜测就知道某个能力由哪些文件组成、适用于哪些平台
2. **用 plan 先做只读诊断**——把"看清楚要做什么"和"真正写入执行"分开
3. **用统一入口降低发现成本**——让 AI 不再记忆多个脚本和参数
4. **用 status / audit / doctor 做聚合视图和缺口分流**——让 AI 和 Human 快速判断当前系统是否健康
5. **用跨平台表面经验完善平台适配清单**——让 LDVH 能在不同 AI 协作环境中被看见、被触发和被执行
6. **用资产分层原则约束 Rules、Skills、Commands、Agents 的边界**——让每种资产形态只承担自己适合的职责

当前最不该做的六件事：

1. 先做安装器
2. 先做自动 apply / repair
3. 先做大而全 CLI
4. 先做长期状态源
5. 先复制 ECC 的 Skills / Commands / Rules
6. 脱离当前 Dogfood 闭环做跨平台投影扩张

最小下一步是完善 `landing-plan` 输出合同，让 41、42、04、07、09 的判断结果可以被 AI、Human、Code 和 Web 共同消费，并且始终回指 Git 文件事实源。
