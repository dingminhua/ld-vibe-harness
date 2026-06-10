# LDVH 对 ECC Claude Code 插件的借鉴评估

> 创建日期：2026-06-10
> 定位：对 ECC（Everything Claude Code / affaan-m/ECC）Claude Code 插件与跨 Harness 运行系统的参考调研，分析其对 LDVH 的可借鉴机制、接管边界和后续候选事项
> 调研边界：本文属于外部引用与参考材料，不直接构成 LDVH 正式规范或稳定结论
> 执行效力：无；稳定结论需进入 `docs/specs/`、`ldvh-base/`、`tools/`、`web/`、平台适配清单或其他 Git 文件事实源后才具备对应效力
> 来源仓库：`https://github.com/affaan-m/ECC`
> 本地副本：`/Users/dmh2002/poker_hud_projects/临时参考/ecc/ECC`
> 参考基线：下载时 HEAD 为 `10c303e609a6769c565de9cc7ec288b7afdefb6c`
> 相关 LDVH 规范：`docs/specs/00-LD-Vibe-Harness理念与纲要.md`、`docs/specs/01-目录说明.md`、`docs/specs/04.02-环境适配与运行投影规范.md`、`docs/specs/07-Code实现规范.md`、`docs/specs/11-非LDVH来源内容治理规范.md`、`docs/specs/42-ldvh-landing-check-LDVH落地与检查.md`

---

## 1. 本文解决的问题

本文解决三个问题：

1. ECC 的 Claude Code 插件和跨 Harness 代码组织方式是什么；
2. ECC 的哪些机制对 LDVH 的开发环境适配、运行投影、Code 工具、Skill/Rules 接管、状态审计和落地检查有借鉴价值；
3. LDVH 在吸收 ECC 经验时应如何避免把第三方内容直接提升为事实源或正式规则。

本文只作为 `docs/refs/` 外部参考材料。ECC 的代码、插件清单、命令文档、技能和规则均属于非 LDVH 来源内容，按 LDVH 的非 LDVH 来源内容治理原则，只能作为候选输入、参考材料或待接管素材；任何稳定结论都必须由 LDVH 主控重新归属、验证并写入对应权威位置。

---

## 2. ECC 的核心定位

ECC 当前不是单一 Claude Code 配置包，而更像一个跨 AI 编程环境的 Harness-native operator system。其仓库同时承载：

1. 插件清单：`.claude-plugin/plugin.json`、`.codex-plugin/plugin.json` 等；
2. 平台适配面：`.claude/`、`.codex/`、`.cursor/`、`.gemini/`、`.opencode/`、`.qwen/`、`.zed/`、`.trae/` 等；
3. 行为资产：`agents/`、`commands/`、`skills/`、`rules/`、`hooks/`、`contexts/`；
4. 分发清单：`package.json`、`manifests/`；
5. 执行工具：`scripts/` 中的安装、计划、审计、状态、修复、会话和工作项脚本；
6. 文档与示例：`README.md`、`README.zh-CN.md`、`docs/`、`examples/`；
7. 控制面原型：`ecc2/` Rust 控制面。

ECC README 将其描述为“harness-native operator system for agentic work”，并说明它由真实跨 Harness 工程工作流沉淀而来，覆盖 skills、agents、hooks、rules、MCP 配置、命令 shim 和 operator workflows。本地副本中可重点查看：

- `/Users/dmh2002/poker_hud_projects/临时参考/ecc/ECC/README.md`
- `/Users/dmh2002/poker_hud_projects/临时参考/ecc/ECC/.claude-plugin/plugin.json`
- `/Users/dmh2002/poker_hud_projects/临时参考/ecc/ECC/package.json`
- `/Users/dmh2002/poker_hud_projects/临时参考/ecc/ECC/manifests/`
- `/Users/dmh2002/poker_hud_projects/临时参考/ecc/ECC/scripts/`

对 LDVH 而言，ECC 最有价值的不是命令、Skill 或 Agent 的数量，而是它把“AI 工作流资产”组织成可分发、可选择安装、可审计、可状态化、可跨平台适配的运行系统。

---

## 3. ECC Claude Code 插件清单观察

ECC 的 Claude Code 插件清单位于：

```text
/Users/dmh2002/poker_hud_projects/临时参考/ecc/ECC/.claude-plugin/plugin.json
```

核心内容包括：

```json
{
  "name": "ecc",
  "version": "2.0.0-rc.1",
  "description": "Harness-native ECC plugin for engineering teams - 64 agents, 261 skills, 84 legacy command shims, reusable hooks, rules, MCP conventions, and operator workflows for Claude Code plus adjacent agent harnesses",
  "repository": "https://github.com/affaan-m/ECC",
  "license": "MIT",
  "skills": [
    "./skills/"
  ],
  "commands": [
    "./commands/"
  ]
}
```

该清单显示 ECC 对 Claude Code 插件的最小公开能力主要是 skills 与 commands；agents、hooks、rules 等资产虽然存在于仓库中，但并未直接作为 Claude 插件 manifest 的同级字段声明。`.claude-plugin/README.md` 还特别提示了 Claude 插件 manifest 的未公开约束：组件字段必须是数组，`agents` 不是受支持字段，`version` 字段对可靠安装必要。

这对 LDVH 有两个直接启发：

1. **平台 manifest 能力边界必须尊重平台原生约束**：不要把 LDVH 想提供的抽象能力直接塞进平台不支持的字段；应通过平台适配清单记录“平台支持什么、LDVH 如何映射、不能映射时如何降级”。
2. **运行投影不能替代正式事实源**：插件 manifest 是运行投影，只应指向可加载资产和入口，不应承载 LDVH 正式规则正文。

---

## 4. ECC 的三层安装模型

ECC 最值得 LDVH 借鉴的结构之一，是 `manifests/` 下的三层安装模型：

```text
/Users/dmh2002/poker_hud_projects/临时参考/ecc/ECC/manifests/install-components.json
/Users/dmh2002/poker_hud_projects/临时参考/ecc/ECC/manifests/install-modules.json
/Users/dmh2002/poker_hud_projects/临时参考/ecc/ECC/manifests/install-profiles.json
```

三层职责如下：

| 层级 | 面向对象 | 作用 | LDVH 可借鉴点 |
|---|---|---|---|
| components | 用户或 AI 可理解的能力包 | 把底层模块组织成如 baseline、language、capability 等组件 | 可表达“入口接入”“工作对象工具”“平台适配”“Web 桥接”“审计工具”等能力包 |
| modules | 实际安装单元 | 声明 kind、paths、targets、dependencies、defaultInstall、cost、stability | 可显式声明运行投影路径、目标平台、依赖、稳定性和上下文成本 |
| profiles | 场景化安装画像 | 将多个 modules 组合成 minimal、core、developer、security、research、full 等模式 | 可定义 LDVH 的最小接入、标准管辖项目、LDVH 自身维护、只读审计、Web 管理等 profile |

ECC 的 `install-modules.json` 中，一个 module 会声明真实路径、目标平台、依赖、默认安装、成本和稳定性。这比单纯“复制某个目录”更适合治理，因为它让安装行为成为可解释、可 dry-run、可验证的结构化计划。

LDVH 目前已经在 `docs/specs/04.02-环境适配与运行投影规范.md` 中定义了“正式规范 → 规范落地要求 → 保障机制 → 环境适配映射 → 运行投影 → 漂移检查与事实源回写”的链路。ECC 的 manifest 三层结构可作为 LDVH 未来把这条链路 Code 化的参考模型。

---

## 5. ECC 的计划/执行分离

ECC 的安装执行层主要包括：

```text
/Users/dmh2002/poker_hud_projects/临时参考/ecc/ECC/scripts/install-plan.js
/Users/dmh2002/poker_hud_projects/临时参考/ecc/ECC/scripts/install-apply.js
```

`install-plan.js` 负责列出 profile、module、component，或根据 profile/component/target 生成安装计划；`install-apply.js` 才实际执行安装，并支持 `--dry-run`、`--json`、多 target 和 state manifest。

这对 LDVH 的借鉴价值很高：

1. LDVH 落地检查应先生成“计划”，再在 Human Gate 后执行“应用”；
2. 只读计划输出可以作为 AI 与 Human 讨论的共同对象；
3. JSON 输出可被 Web、CI 或后续审计工具消费；
4. dry-run 可降低 AI 误改入口、误写事实源或误复制规则正文的风险；
5. apply 后可记录实际写入文件、跳过文件、冲突文件和回滚线索。

LDVH 当前 `42-ldvh-landing-check-LDVH落地与检查.md` 已要求“先检查当前事实源和环境，输出当前缺口；经 Human 授权后逐项落地；完成后复检”。ECC 的 `install-plan` / `install-apply` 分离可作为这条流程的 Code 化参考。

---

## 6. ECC 的统一 CLI 与治理动作

ECC 在 `package.json` 中暴露了 `ecc`、`ecc-control-pane`、`ecc-install` 等 bin，其中 `scripts/ecc.js` 是统一入口，包装 install、plan、catalog、consult、control-pane、list-installed、doctor、repair、auto-update、status、platform-audit、security-ioc-scan、sessions、work-items、session-inspect、loop-status、uninstall 等动作。

LDVH 当前已有多个 Python 工具入口：

```text
/Users/dmh2002/poker_hud_projects/ld-vibe-harness/tools/specs_validate.py
/Users/dmh2002/poker_hud_projects/ld-vibe-harness/tools/fact_cli.py
/Users/dmh2002/poker_hud_projects/ld-vibe-harness/tools/fact_validate.py
/Users/dmh2002/poker_hud_projects/ld-vibe-harness/tools/commit_validate.py
```

但从 AI 可发现性角度看，LDVH 仍可考虑未来提供统一 CLI 门面，例如：

```text
ldvh specs index
ldvh specs landing-report
ldvh projection check
ldvh fact list task
ldvh fact show task-0001
ldvh landing plan
ldvh landing apply
ldvh status
ldvh doctor
```

统一 CLI 的价值不是减少脚本数量，而是降低 AI 和 Human 的入口寻找成本，并让命令输出合同更稳定。

---

## 7. ECC 的审计、状态和健康检查

ECC 中多个脚本体现了“运行系统可审计”的思想：

```text
/Users/dmh2002/poker_hud_projects/临时参考/ecc/ECC/scripts/harness-audit.js
/Users/dmh2002/poker_hud_projects/临时参考/ecc/ECC/scripts/platform-audit.js
/Users/dmh2002/poker_hud_projects/临时参考/ecc/ECC/scripts/status.js
/Users/dmh2002/poker_hud_projects/临时参考/ecc/ECC/scripts/skills-health.js
/Users/dmh2002/poker_hud_projects/临时参考/ecc/ECC/scripts/list-installed.js
/Users/dmh2002/poker_hud_projects/临时参考/ecc/ECC/scripts/doctor.js
/Users/dmh2002/poker_hud_projects/临时参考/ecc/ECC/scripts/repair.js
```

其中 `/harness-audit` 命令文档强调脚本是评分事实源，不要让 AI 临时发明额外维度。这一点非常适合 LDVH：

1. LDVH 的 `landing-report`、`runtime-projection`、`human-gate` 等检查应明确输出合同；
2. Code 输出是派生诊断，不是最终事实源；
3. AI 不应临时扩大检查维度并宣称通过或失败；
4. 审计结果应能以 text、json、markdown 等形式服务 AI、Web 和 CI；
5. 支持 exit code 的审计可进入提交前、CI 或人工降级清单。

LDVH 当前 `tools/specs_validate.py` 已包含运行投影检查、规范落地报告和 Human Gate 检查的雏形。ECC 提醒 LDVH 可以进一步把“状态聚合视图”做成一等能力：聚合工作对象状态、运行投影漂移、平台适配缺口、Human Gate 待办、Code 校验结果和 Web 同步状态。

---

## 8. ECC 的 commands、skills、rules 分工

ECC 的行为资产主要分布在：

```text
/Users/dmh2002/poker_hud_projects/临时参考/ecc/ECC/commands
/Users/dmh2002/poker_hud_projects/临时参考/ecc/ECC/skills
/Users/dmh2002/poker_hud_projects/临时参考/ecc/ECC/rules
/Users/dmh2002/poker_hud_projects/临时参考/ecc/ECC/agents
```

ECC 的 rules README 明确了一个对 LDVH 很有价值的分工：

```text
Rules tell you what to do; skills tell you how to do it.
```

映射到 LDVH，可以更严格地表述为：

| ECC 概念 | LDVH 借鉴映射 | 边界 |
|---|---|---|
| rules | specs / 平台薄入口中的约束投影 | specs 是权威；平台 rules 只投影，不复制正文 |
| skills | 工作流程或可复用执行流程 | 不能绕过 Task、Human Gate、事实源回写和验证 |
| commands | 触发某个流程或工具的用户入口 | 应绑定脚本、事实源、STOP 点和输出合同 |
| agents | 专业视角或子任务执行者 | 不能替代主控判断、最终验收和 Human Gate |
| hooks | 生命周期触发器 | 平台支持时可作为运行投影；不支持时必须降级 |

ECC 的命令文档值得借鉴的是“命令绑定脚本与输出合同”。例如 `/harness-audit` 明确要求调用特定脚本，而不是让 AI 自己凭印象评分。LDVH 后续若沉淀 commands 或 skills，也应保持这种写法：说明调用哪个工具、读取哪个事实源、输出必须包含什么、不能做什么、何时暂停。

---

## 9. ECC 对 LDVH 当前结构的对照判断

LDVH 当前已具备比 ECC 更明确的事实源治理和规范边界：

1. `docs/specs/` 是正式规范事实源；
2. `ldvh-base/` 承载 ADR、Intent、Memo、Pitfall、Task 等结构化事实实例；
3. `tools/` 提供确定性校验、聚合和 CLI；
4. `web/` 提供 Human-facing 桥接；
5. `LDVH-AI-ENTRY.md` 是运行投影，不是正式规范；
6. `docs/research/` 与 `docs/refs/` 是输入材料，不直接生效。

ECC 则在“分发、安装、运行诊断、跨平台插件表面、命令/技能资产规模”上更成熟。两者的互补关系可以概括为：

```text
LDVH 强在事实源边界、工作模型、工作流程、Human Gate 与规范治理；
ECC 强在跨 Harness 分发、选择性安装、命令/技能资产组织、运行审计与状态工具。
```

因此，LDVH 不应直接复制 ECC 的大量 skills、commands 和 rules，而应借鉴其机制结构：manifest 化、plan/apply 分离、审计脚本、状态聚合、跨平台投影、命令输出合同。

---

## 10. 最值得 LDVH 优先借鉴的六项机制

### 10.1 Manifest 化运行投影与安装模型

建议 LDVH 未来将平台入口、Skill、Agent、Hook、Code 检查、Web 页面、工作对象工具等可落地能力，抽象为 manifest：

```text
components：用户/AI 可理解的能力包
modules：真实文件、目标平台、依赖、成本、稳定性
profiles：最小接入、标准管辖项目、LDVH 自身维护、只读审计、完整管理等场景
```

该机制可承接 `04.02` 的环境适配映射，并使 42 的落地检查可以从 manifest 中生成计划和缺口报告。

### 10.2 Plan / Apply / Verify 三段式落地

借鉴 ECC 的 `install-plan.js` 与 `install-apply.js`，LDVH 可形成：

```text
ldvh landing plan
→ 只读生成计划、缺口、影响范围、需要 Human Gate 的项

ldvh landing apply
→ 在授权后执行受控写入

ldvh landing verify
→ 复检入口、事实源、运行投影、Code/Web/Skill 状态
```

这与 LDVH 的 Human Gate、42 落地与检查、运行投影漂移检查高度一致。

### 10.3 统一 CLI 门面

LDVH 现有工具分散但功能已开始成型。可借鉴 ECC 的 `ecc <command>` 入口，未来设计统一命令门面，降低 AI 发现成本，并稳定输出合同。

### 10.4 状态聚合视图

ECC `status.js` 聚合 sessions、skill runs、install health、governance events 和 work items。LDVH 可设计 `ldvh status`，聚合：

1. 工作对象状态分布；
2. open / degraded / needs_human_gate 的规范落地要求；
3. 运行投影漂移风险；
4. 平台适配清单 open_items；
5. Web 同步状态；
6. 最近验证结果；
7. 待 Human Gate 事项。

该能力会直接服务 LDVH 价值标准中的 V1 快速定位、V5 门禁识别、V6 强制验证、V9 人类确认质量。

### 10.5 命令文档绑定工具合同

LDVH 后续若沉淀 commands 或 skills，不应只写“做某事”的自然语言提示，而应像 ECC `/harness-audit` 一样写清：

1. 调用哪个脚本；
2. 输入参数；
3. 输出格式；
4. 成功/失败条件；
5. AI 不得自行解释或替换的边界；
6. 结果应回写到哪里，或为什么不得回写。

### 10.6 第三方 Skill 接管流水线

ECC 的大量 skills 可作为 LDVH 后续第三方 Skill 接管研究素材。但接管应分级：

1. T1：只作为阅读参考；
2. T2：受限调用，生成候选材料；
3. T3：由 LDVH 主控审查、验证和归属；
4. T4：写入对应事实源或 LDVH 自建 Skill；
5. T5：多次有效后沉淀为稳定复用机制。

这与 `docs/specs/11-非LDVH来源内容治理规范.md` 和 `docs/specs/11.01-第三方Skill接管落地选项.md` 保持一致。

---

## 11. 不建议直接吸收的部分

### 11.1 不直接复制大量 commands / skills / rules

ECC 的规模很大，commands、skills、rules、agents 数量多。直接复制会带来：

1. LDVH 上下文负担增加；
2. 第三方规则与 LDVH 事实源边界冲突；
3. 运行投影漂移风险增加；
4. Human Gate、Task 状态机、工作对象字段契约被绕过；
5. AI 误以为第三方内容已具备 LDVH 效力。

正确方式是先把 ECC 放在 `docs/refs/` 或临时参考区，按用途逐项接管。

### 11.2 不直接采用 ECC 的规则优先级作为 LDVH 正式规则

ECC 的 rules 分层是 common + language-specific，适合通用工程规则包。但 LDVH 的核心是 specs、工作模型、工作流程、Code、Web 和事实源治理。LDVH 不能让平台 rules 或语言 rules 反向定义正式规范。

### 11.3 不把插件 manifest 当作平台完整支持证据

`.claude-plugin/plugin.json` 能说明 ECC 如何声明 Claude Code 插件，但不能证明 LDVH 在 Claude Code、Trae、Codex 或 Cursor 中完整支持某项能力。LDVH 的平台支持仍应回到 `04.06` 平台适配清单、当前平台事实、运行投影验证和 42 现场检查。

### 11.4 不直接引入外部自动更新/修复机制

ECC 有 auto-update、repair、doctor 等工具方向。LDVH 可借鉴诊断和建议，但自动修复、自动覆盖入口、自动写入事实源都必须受到 Human Gate、dry-run、diff、验证和可回滚约束。

---

## 12. 候选承接事项

以下事项可作为后续 Task、Memo 或规范候选输入，不因本文自动生效。

| 编号 | 候选事项 | 建议归属 | 优先级 | 说明 |
|---|---|---|---|---|
| ECC-LDVH-01 | 设计 LDVH manifest 三层模型 | `docs/specs/04.02`、`tools/`、Task | 高 | 对应 components/modules/profiles，服务运行投影和落地计划 |
| ECC-LDVH-02 | 增加 landing plan / apply / verify 工具合同 | `tools/specs_validate.py` 或新 CLI | 高 | 先只读计划，再授权写入，最后复检 |
| ECC-LDVH-03 | 设计 `ldvh status` 聚合视图 | `tools/`、`web/` | 高 | 聚合工作对象、落地缺口、Human Gate、运行投影漂移 |
| ECC-LDVH-04 | 形成命令/Skill 文档输出合同模板 | `docs/specs/11.01`、`docs/specs/12` | 中 | 要求命令绑定脚本、事实源、STOP 点、输出格式 |
| ECC-LDVH-05 | 建立第三方 Skill 接管试点 | `docs/specs/11.01`、Task | 中 | 选 1-2 个低风险 Skill 做 T1-T4 接管试验 |
| ECC-LDVH-06 | 增强运行投影漂移检查 | `tools/specs_validate.py` | 高 | 检查平台 manifest、薄入口、Skill/Agent/Hook 引用是否过期 |
| ECC-LDVH-07 | 评估 Claude Code 平台适配清单 | 新平台适配清单或候选 Memo | 中 | 仅在 Human 明确需要 Claude Code 支持时进入 |

---

## 13. 对 LDVH 的阶段性结论

ECC 对 LDVH 的核心启发可以总结为：

```text
把 AI 工作流资产从“散落提示词和目录”提升为“可声明、可选择、可计划、可应用、可审计、可状态化、可跨平台投影的运行系统”。
```

LDVH 已经具备更强的事实源边界和工作治理模型，因此不应追求 ECC 式的资产数量扩张，而应吸收其工程化分发与运行诊断能力。优先方向应是：

1. 用 manifest 让运行投影和平台适配可声明；
2. 用 plan/apply/verify 让落地动作可控；
3. 用 status/audit/doctor 让链路健康可见；
4. 用命令输出合同让 AI 执行不靠临时发挥；
5. 用第三方内容接管流程吸收 ECC 的经验而不破坏 LDVH 权威边界。

对 LDVH 当前阶段而言，最值得优先推进的是 **manifest 化安装/运行投影模型** 与 **landing plan/apply/verify Code 化**。这两项能直接补强 42 落地与检查、04.02 运行投影、07 Code 实现和 Web/Human Gate 的衔接，也最符合 LDVH “规范服务 AI，机制托住 AI，Code 减轻 AI，Web 协调 Human，事实源沉淀闭环”的价值边界。
