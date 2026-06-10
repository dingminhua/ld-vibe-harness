# LDVH 应向 ECC 学习的运行系统机制评估

> 创建日期：2026-06-10
> 更新日期：2026-06-10
> 定位：从 LDVH 00 总纲出发，直接评估 LDVH 应向 ECC 学习哪些运行系统机制、如何转译、哪些边界不能越过
> 调研边界：不直接构成强制规则
> 执行效力：无；结论需进入正式 specs、ADR、Task、Code、Web 或运行投影后才成为稳定执行依据
> 来源：ECC 本地源码、LDVH 00 总纲、LDVH 04/06/07/09/10/11/41/42 系列规范、LDVH 既有 ECC 借鉴评估与当前对话评估
> 相关参考：`docs/refs/07-LDVH对ECC-Claude-Code插件的借鉴评估.md`、`docs/research/18-LDVH推进评估与候选事项总览.md`

---

## 1. 本文解决的问题

本文直接回答：LDVH 现在应向 ECC 学习什么。

ECC 的价值不在于它有多少 agents、skills、commands、rules，也不在于 LDVH 要复制一套类似系统。ECC 对 LDVH 最有价值的部分，是它已经实践过一组运行系统工程化方法：如何描述可安装能力、如何先计划再执行、如何统一命令入口、如何做运行状态聚合、如何跨平台组织运行投影、如何分层管理 Rules / Skills / Commands / Agents。

LDVH 应学习这些方法，但必须按 LDVH 的目标转译：服务 AI 执行者，服务 V1-V10 价值标准，进入 Intent → Plan → Execute → Verify → Record → Learn 运行闭环，回到 Git 文件事实源，并遵守 Human Gate、Code 验证和防递归建设原则。

---

## 2. 总结论

LDVH 应向 ECC 学习六类机制：

1. Manifest 化能力描述；
2. Plan / Apply / Verify 分段执行；
3. 统一 CLI 门面；
4. Status / Doctor 诊断聚合；
5. 跨平台运行投影组织；
6. Rules / Skills / Commands / Agents 资产分层。

学习顺序应是：

```text
先学只读描述和诊断
→ 再学命令入口和输出合同
→ 再学跨平台投影映射
→ 最后才评估 apply、repair、自动分发和规模化资产库
```

当前最应该先做的是：围绕 41 规范落地统筹和 42 LDVH落地与检查，设计一个只读的 `landing plan` 输出合同。它可以吸收 ECC 的 manifest、plan、status 思路，但不做自动写入，不做 repair，不做完整安装器。

---

## 3. 学习一：Manifest 化能力描述

### 3.1 ECC 值得学习什么

ECC 通过 manifest 把能力拆成不同层次：

| 层次 | 作用 |
|---|---|
| components | 用户或 AI 可理解的能力包 |
| modules | 真实文件、目录、目标平台、依赖、成本、稳定性 |
| profiles | 面向不同使用场景的能力组合 |

这个结构的价值是：AI 不需要临时扫描整套仓库，就能知道某个能力由哪些文件组成、适用于哪些平台、依赖什么、是否默认启用、风险或成本如何。

### 3.2 LDVH 应如何转译

LDVH 不应把 manifest 首先理解成安装器。LDVH 更需要的是“规范落地与运行投影索引”。

LDVH 可学习 ECC manifest，形成自己的候选描述结构：

| LDVH 字段 | 含义 |
|---|---|
| `capability_id` | 能力标识，例如 landing-plan、fact-query、human-gate-check |
| `ldvh_element` | 归属构成要素：开发环境、工作模型、工作流程、Code、Web 或运行投影 |
| `source_specs` | 来源正式规范和章节 |
| `landing_requirements` | 对应规范落地要求 |
| `runtime_projection` | 可能形成的入口、命令、Skill、Agent、Hook、Web 页面或降级记录 |
| `facts_read` | 读取哪些 Git 文件事实源 |
| `writeback_targets` | 稳定结论应回写到哪里 |
| `validation` | 验证命令、测试、人工检查或降级方式 |
| `human_gate` | 是否涉及 Human Gate |
| `status` | candidate、planned、active、degraded、removed 等候选状态 |

### 3.3 LDVH 当前应做什么

当前只应做 schema 草案和一两个最小样例，优先服务 41/42。

建议先描述以下能力：

1. 规范落地要求聚合；
2. 管辖项目配置检查；
3. 工作对象列表和状态统计；
4. 运行投影缺口检查；
5. Human Gate 记录检查。

### 3.4 不应做什么

1. 不应先做完整安装器；
2. 不应先做跨平台自动分发；
3. 不应把 manifest 输出当作最终事实源；
4. 不应把 ECC 的 components/modules/profiles 原样复制成 LDVH 规范。

---

## 4. 学习二：Plan / Apply / Verify 分段执行

### 4.1 ECC 值得学习什么

ECC 的 `install-plan.js` 明确先做只读计划，不修改目标。它把“看清楚要做什么”和“真正写入执行”分开。

这个分离对 LDVH 很重要，因为 LDVH 的写入涉及事实源边界、Human Gate、受控写入、验证证据和回写归属。

### 4.2 LDVH 应如何转译

LDVH 可把 ECC 的 plan/apply 思路转译为：

```text
ldvh landing plan
→ 只读生成范围、事实源、缺口、建议动作、Human Gate、验证计划和回写目标

ldvh landing apply
→ 在 Human 授权后执行受控写入

ldvh landing verify
→ 复检事实源、运行投影、Code/Web/Skill 状态和验证证据
```

当前只应先讨论 `plan`，不应急着实现 `apply`。

### 4.3 最小 plan 输出合同

`landing plan` 可以先定义以下输出：

| 字段 | 含义 |
|---|---|
| `scope` | 本次检查范围 |
| `facts_read` | 已读取或聚合的事实源 |
| `requirements` | 规范落地要求或工作对象规则摘要 |
| `gaps` | open / degraded / needs_human_gate 缺口 |
| `proposed_actions` | 候选补齐动作 |
| `writes_required` | 是否涉及写入及目标事实源 |
| `human_gate` | 需要确认的事项 |
| `validation_plan` | 验证方式、命令或人工降级检查 |
| `writeback_targets` | 稳定结论应回写的位置 |

### 4.4 LDVH 当前应做什么

1. 先把 42 LDVH落地与检查的报告结构转成只读 plan 合同；
2. 让 41 的规范落地要求聚合结果成为 plan 的输入；
3. 让 plan 明确哪些事项只能当前报告展示，哪些应进入 Task、Memo、ADR、Pitfall、specs、Code 或 Web；
4. 先用当前 LDVH 自身项目 dogfood 一次。

### 4.5 不应做什么

1. 不应先做自动 apply；
2. 不应做 repair；
3. 不应允许 plan 输出直接改变状态；
4. 不应把计划报告保存成新的长期状态源。

---

## 5. 学习三：统一 CLI 门面

### 5.1 ECC 值得学习什么

ECC 的统一 CLI 让 install、plan、catalog、doctor、repair、status、sessions、work-items 等能力有一致入口。它降低了 AI 和 Human 发现命令的成本。

LDVH 当前已经有多个工具，但入口分散，AI 需要记住不同脚本、参数和输出边界。统一入口可以服务 V1 快速定位、V3 正确判断和 V6 强制验证。

### 5.2 LDVH 应如何转译

LDVH 的 CLI 不应首先是产品门面，而应是 Code 构成要素的稳定运行入口。

建议方向：

```text
ldvh specs index
ldvh specs landing-report
ldvh facts list <type>
ldvh facts show <id>
ldvh facts search <keyword>
ldvh facts stats
ldvh governed-projects check
ldvh landing plan --json
```

### 5.3 每个命令必须定义什么

| 项目 | 要求 |
|---|---|
| 输入 | 参数、路径、默认范围 |
| 输出 | 人读文本和 JSON 输出 |
| exit code | 成功、失败、发现缺口、需要 Human Gate |
| 事实源回指 | 输出能定位到文件、对象 ID 或章节 |
| 写入边界 | 默认只读；写入必须显式声明 |
| 验证方式 | 测试、样例或等价验证 |

### 5.4 LDVH 当前应做什么

1. 先包装现有高频只读工具；
2. 优先统一输出结构，不急着增加能力；
3. 先服务 AI 定位和诊断，不服务产品化展示；
4. 后续 Web 如需消费 CLI 输出，应共享同一契约。

### 5.5 不应做什么

1. 不应为了完整性一次性设计庞大命令树；
2. 不应绕开现有 `tools/` 重新造一套；
3. 不应让 CLI 输出成为最终事实源；
4. 不应把没有明确失败条件的语义判断包装成确定性命令。

---

## 6. 学习四：Status / Doctor 诊断聚合

### 6.1 ECC 值得学习什么

ECC 的 status 和 doctor 能聚合运行状态、安装健康、会话、工作项和治理事件，让 AI 和 Human 快速判断当前系统是否可用、哪里有缺口、下一步该做什么。

这对 LDVH 有价值，因为 LDVH 当前也需要让 AI 快速看到：事实源是否可读、工作对象是否可查询、规范落地要求是否有缺口、运行投影是否漂移、Human Gate 是否待确认。

### 6.2 LDVH 应如何转译

LDVH 的 status / doctor 应是派生聚合视图，不是状态事实源。

建议聚合内容：

| 聚合项 | 来源 |
|---|---|
| 工作对象状态分布 | `ldvh-base/` + fact_cli |
| 规范落地要求缺口 | `docs/specs/` + landing-report |
| 平台适配 open_items | 平台适配清单 |
| 运行投影漂移风险 | 04.02、平台清单、实际入口 |
| Human Gate 待确认事项 | Task、ADR、Web、当前流程输出 |
| 最近验证结果 | Code 输出、测试结果、closure evidence |
| 建议回写位置 | 09 事实源边界和对应模型规范 |

### 6.3 LDVH 当前应做什么

1. 先定义 `ldvh status` 的只读输出边界；
2. 先输出事实源路径和缺口分类；
3. 缺口不要自动关闭，只建议进入 Task、Memo、ADR、Pitfall、Code 或 specs；
4. doctor 先做诊断，不做 repair。

### 6.4 不应做什么

1. 不应创建长期状态登记表；
2. 不应让 status 输出替代 Task 状态、ADR 决策或 42 当前报告；
3. 不应把 doctor 诊断结果当作已修复证据；
4. 不应在没有 Human Gate 的情况下自动 repair。

---

## 7. 学习五：跨平台运行投影组织

### 7.1 ECC 值得学习什么

ECC 面向多个 harness 组织不同平台表面，包括 Claude、Codex、Cursor、OpenCode、Gemini、Zed 等。它说明同一套运行系统能力可以在不同环境中通过不同入口承接。

LDVH 也需要适配不同 AI 开发环境，但 LDVH 的原则是适配不绑定：利用环境能力，不把某个平台提升为唯一底座。

### 7.2 LDVH 应如何转译

LDVH 应把 ECC 的跨平台经验转译为平台适配清单和运行投影映射。

建议形成映射表：

| LDVH 需要 | 可能环境能力 | LDVH 边界 |
|---|---|---|
| 入口可见 | Rules / Instructions / AGENTS / README 薄入口 | 只放最小导航和 STOP 点 |
| 流程复用 | Skill / Command | 不替代工作流程正文 |
| 独立审查 | Agent / 子 Agent | 输出回主控，稳定结论回写 |
| 生命周期触发 | Hook / CI / 自动运行 | 不定义规范，只实现触发 |
| 确定性反馈 | Code / CLI / CI | 输出不是事实源 |
| Human 确认 | Web / AskUserQuestion / 手工确认 | 不替代 Human 判断 |

### 7.3 LDVH 当前应做什么

1. 先整理 ECC 各平台表面作为 refs 或 research 输入；
2. 更新或补充平台适配清单 open_items；
3. 只在当前平台做最小运行投影验证；
4. 将跨平台差异留在平台适配清单，不写进 00 或通用规范正文。

### 7.4 不应做什么

1. 不应同时为多个平台创建持久入口；
2. 不应复制平台规则正文到 LDVH specs；
3. 不应让运行投影替代正式规范；
4. 不应把某个平台能力写成 LDVH 全局必须能力。

---

## 8. 学习六：Rules / Skills / Commands / Agents 资产分层

### 8.1 ECC 值得学习什么

ECC 清楚地区分了 rules、skills、commands、agents 等资产形态，并通过目录和注册方式组织它们。这种分层有利于 AI 快速选择入口，降低混用风险。

### 8.2 LDVH 应如何转译

LDVH 应按 04.03 的环境能力承接边界吸收这种分层。

| 资产形态 | LDVH 中适合承接 | 不适合承接 |
|---|---|---|
| Rules / Instructions | 入口可见、硬约束摘要、事实源边界提示、STOP 点 | 完整规范正文、对象字段契约、低频流程 |
| Skill | 可复用多步骤流程、标准化输入输出、受控检查步骤 | Human Gate 判断本身、稳定规则正文、子 Agent 调度 |
| Command | Code 或流程的稳定入口 | 独立事实源、未经验证的语义判断 |
| Agent | 独立上下文、专项视角、并行审查、权限边界差异 | 简单问答、单文件小改、最终事实源判断 |
| Hook / CI | 生命周期触发、自动提醒、阻断、检查 | 规范正文、不能机械判断的语义结论 |

### 8.3 LDVH 当前应做什么

1. 先建立 LDVH 自己的能力承接判断表；
2. 对 ECC skills 只做候选清单，不直接接管；
3. 对高频流程，先判断应进入工作流程、Skill、Code 还是主控上下文；
4. 对第三方 Skill 输出，按 11 完成来源识别、主控接管、验证和回写。

### 8.4 不应做什么

1. 不应复制 ECC 大量 skills、commands、rules；
2. 不应因为某个流程重要就写进 Rules；
3. 不应因为步骤多就创建 Skill；
4. 不应允许 Skill 调度 Agent；
5. 不应让 Agent 输出直接成为事实源。

---

## 9. 学习优先级

### 9.1 第一阶段：只读诊断

优先学习 ECC 的 manifest、plan、status 思路，形成 LDVH 只读诊断能力。

目标：让 AI 能快速回答：当前范围读了哪些事实源、有哪些规范落地要求、有哪些缺口、需要哪些 Human Gate、应如何验证、应回写到哪里。

建议输出：`ldvh landing plan --json` 草案。

### 9.2 第二阶段：统一入口

学习 ECC 统一 CLI 的发现成本降低方式，把 LDVH 现有只读工具收敛到统一命令树。

目标：让 AI 不再记忆多个脚本，而是通过稳定入口获得规范索引、工作对象查询、管辖项目检查和落地缺口报告。

### 9.3 第三阶段：运行投影映射

学习 ECC 跨平台表面，转译为 LDVH 平台适配清单和运行投影映射矩阵。

目标：明确不同平台如何承接入口可见、流程复用、子 Agent 思考、生命周期触发、确定性执行和 Human 交互。

### 9.4 第四阶段：受控写入

只有当前三阶段 dogfood 通过后，才讨论 apply、repair、受控写入和自动修复。

目标：在 Human Gate、验证、回写、回滚路径明确后，最小化实现受控写入。

### 9.5 第五阶段：稳定复用资产

只有某类流程反复出现、输入输出稳定、验证方式明确、主控接管边界清楚时，才沉淀为 LDVH 自建 Skill、Command、Agent 或运行投影。

目标：让资产服务闭环，而不是为了资产规模扩张。

---

## 10. 后续可分流事项

| 候选事项 | 建议去向 | 说明 |
|---|---|---|
| `ldvh landing plan --json` 输出合同 | Task、Code、tests | 当前最高优先级，只读，不做 apply |
| ECC manifest 字段转译表 | research 或 ADR | 作为 LDVH schema 候选，不直接安装 |
| 统一 CLI 最小命令树 | ADR、Task、Code | 包装现有高频只读能力 |
| status / doctor 边界 | ADR、Task、Web docs | 明确聚合视图与事实源边界 |
| ECC 平台表面映射矩阵 | docs/refs 或 research | 作为平台适配清单输入材料 |
| 第三方 Skill 接管策略 | docs/specs/11、11.01 或 Task | 与非 LDVH 来源内容治理合并判断 |

---

## 11. 阶段性结论

LDVH 应向 ECC 学习的不是目标、规模或内容库，而是运行系统组织方法。

当前最值得学的是：

1. 用 manifest 描述能力边界；
2. 用 plan 先做只读诊断；
3. 用统一 CLI 降低发现成本；
4. 用 status / doctor 做聚合视图和缺口分流；
5. 用跨平台表面经验完善平台适配清单；
6. 用资产分层原则约束 Rules、Skills、Commands、Agents 的边界。

当前最不该做的是：

1. 先做安装器；
2. 先做自动 apply / repair；
3. 先做大而全 CLI；
4. 先做长期状态源；
5. 先复制 ECC 的 Skills / Commands / Rules；
6. 脱离当前 Dogfood 闭环做跨平台投影扩张。

最小下一步是设计 `ldvh landing plan --json`，让 41、42、04、07、09 的判断结果可以被 AI、Human、Code 和 Web 共同消费，并且始终回指 Git 文件事实源。
