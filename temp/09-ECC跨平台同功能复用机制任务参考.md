# ECC 跨平台同功能复用机制任务参考

> 创建日期：2026-06-11
> 定位：研究 ECC 如何让不同平台使用相同功能，并为 LDVH 后续平台适配与运行投影设计提供任务参考
> 性质：参考文档，不直接构成 LDVH 正式规范或实施承诺
> 来源：ECC 本地源码与文档、`docs/architecture/harness-adapter-compliance.md`、`docs/ECC-2.0-REFERENCE-ARCHITECTURE.md`、`docs/ECC-2.0-SESSION-ADAPTER-DISCOVERY.md`、`scripts/lib/install-manifests.js`、`scripts/lib/harness-adapter-compliance.js`

---

## 1. 任务目标

本任务要回答：ECC 为什么能让 Claude Code、Codex、Cursor、OpenCode、Gemini、Zed、Terminal-only 等不同平台使用相同能力。

研究结论应服务 LDVH 后续判断：

1. LDVH 是否需要借鉴 ECC 的跨平台组织方式；
2. LDVH 应把哪些内容放在共享事实源，哪些内容放在平台薄入口；
3. LDVH 的 04.06 平台适配清单、04.07 Trae-Solo 适配清单、04.08 Codex 适配清单是否需要补充类似机制；
4. LDVH 后续如果生成 Skill、Command、Agent 或 Rules 投影，应如何避免平台差异污染正式规范。

---

## 2. 一句话结论

ECC 能跨平台复用相同功能，靠的不是让所有平台能力完全一致，而是把功能拆成三层：

```text
共享资产层：skills / rules / commands / hooks / scripts / MCP reference configs
  ↓
能力声明层：manifest 声明哪些 module 支持哪些 target
  ↓
平台适配层：每个平台只做加载、路径、事件形状、命令名和能力限制的薄适配
```

换句话说，ECC 的核心策略是：

```text
同一份能力内核，多套平台入口；共享逻辑不分叉，平台差异在边缘适配。
```

---

## 3. ECC 的跨平台复用结构

### 3.1 共享资产留在公共源

ECC 在 `docs/architecture/harness-adapter-compliance.md` 中明确：durable units 保持在 shared sources：

| 共享资产 | 作用 |
|---|---|
| `skills/*/SKILL.md` | 可复用任务能力 |
| `rules/` | 通用规则或约束 |
| `commands/` | 工作流入口与命令说明 |
| `hooks/hooks.json` | Hook 配置描述 |
| `scripts/hooks/` | Hook 真实执行逻辑 |
| MCP reference configs | MCP 参考配置 |
| session and observability contracts | 会话与可观察性输出合同 |

这些内容是 ECC 的功能内核。平台目录不应复制并分叉这些逻辑，只应适配加载方式、事件形状、命令名称或平台限制。

### 3.2 manifest 声明 module 支持哪些 target

ECC 的 `scripts/lib/install-manifests.js` 通过 manifest 读取 components、modules、profiles，并要求每个 module 都声明 `targets`。

关键机制包括：

1. `SUPPORTED_INSTALL_TARGETS` 定义可支持的平台目标，例如 `claude`、`cursor`、`codex`、`gemini`、`opencode`、`zed` 等；
2. 每个 module 必须声明自己的 `targets`，否则校验失败；
3. `readModuleTargetsOrThrow` 会拒绝未知 target；
4. `intersectTargets` 会计算一个 component 下所有 module 的共同可用平台；
5. `listInstallComponents` 可以按 target 过滤能力，避免把平台不支持的能力展示为可用；
6. `TARGET_DEFAULT_EXCLUSIONS` 可声明某个平台默认排除某些 module，例如 OpenCode 默认排除 hooks-runtime，直到用户显式 opt-in。

这说明 ECC 不是假设所有平台都支持全部能力，而是让每项能力显式声明支持范围。

### 3.3 install target adapter 处理平台路径和落地方式

ECC 在 `scripts/lib/install-targets/` 下为不同平台提供 target adapter，例如：

| 平台 | adapter 文件 |
|---|---|
| Claude | `claude-home.js`、`claude-project.js` |
| Codex | `codex-home.js` |
| Cursor | `cursor-project.js` |
| Gemini | `gemini-project.js` |
| OpenCode | `opencode-home.js` |
| Zed | `zed-project.js` |
| Qwen | `qwen-home.js` |

这些 adapter 负责处理：

1. 平台配置文件应该写到哪里；
2. 平台如何加载 rules、skills、commands 或 instructions；
3. 平台已有配置是否需要保留；
4. 哪些能力只能以 instruction-backed 形式存在；
5. 哪些 hook、event、command 语义不能直接等价。

因此，ECC 的同功能跨平台不是通过复制多份实现，而是通过 target adapter 把同一套共享资产映射到不同平台的原生入口。

### 3.4 session adapter 统一运行时状态形状

ECC 2.0 还通过 session adapter 处理不同运行时的会话差异。

`ECC-2.0-SESSION-ADAPTER-DISCOVERY.md` 提出 canonical session adapter contract：

```ts
type SessionAdapter = {
  id: string;
  canOpen(target: SessionTarget): boolean;
  open(target: SessionTarget): Promise<AdapterHandle>;
};

type AdapterHandle = {
  getSnapshot(): Promise<CanonicalSessionSnapshot>;
  streamEvents?(onEvent: (event: SessionEvent) => void): Promise<() => void>;
  runAction?(action: SessionAction): Promise<ActionResult>;
};
```

这层的作用不是安装能力，而是把不同运行时的会话状态统一成 `ecc.session.v1` 这样的 canonical snapshot。

可适配对象包括：

1. tmux-orchestrated workers；
2. plain Claude sessions；
3. Codex worktree sessions；
4. OpenCode sessions；
5. future GitHub/App or remote-control sessions。

这说明 ECC 的跨平台复用包含两类 adapter：

| adapter 类型 | 解决的问题 |
|---|---|
| install target adapter | 同一能力如何安装或投影到不同平台 |
| session adapter | 不同运行时的状态如何统一读取和观察 |

### 3.5 compliance matrix 防止虚假平台支持

ECC 通过 `harness-adapter-compliance.md` 和 `scripts/lib/harness-adapter-compliance.js` 维护跨平台能力矩阵。

矩阵为每个平台记录：

| 字段 | 含义 |
|---|---|
| `id` | 平台标识 |
| `state` | 支持状态 |
| `supported_assets` | 支持哪些共享资产 |
| `unsupported_surfaces` | 不支持或语义不同的能力面 |
| `install_or_onramp` | 安装或接入方式 |
| `verification_commands` | 验证命令 |
| `risk_notes` | 风险说明 |
| `last_verified_at` | 最近验证时间 |
| `owner` | 责任方 |
| `source_docs` | 依据文档 |

ECC 的支持状态分为：

| 状态 | 含义 |
|---|---|
| Native | ECC 可直接安装或验证该平台能力面 |
| Adapter-backed | 有薄 adapter、plugin 或 package surface，但平台间不完全等价 |
| Instruction-backed | 可提供指导和文件，但平台缺少运行时 hook/session enforcement |
| Reference-only | 只作为设计压力或外部参考，不声明直接支持 |

这个矩阵的关键价值是：不把“能复制文件”误判为“平台能力等价”。

---

## 4. ECC 跨平台机制的完整链路

ECC 的链路可以概括为：

```text
共享能力资产
  ↓
manifest 声明 module、profile、target
  ↓
install plan 根据 target 选择可落地 module
  ↓
install target adapter 写入平台原生入口
  ↓
harness adapter compliance matrix 标注支持等级、限制和验证命令
  ↓
session adapter 将不同运行时状态归一为 canonical snapshot
  ↓
status / audit / observability 消费统一输出
```

其中最关键的是：

1. 共享能力不因平台不同而复制分叉；
2. 平台支持不靠口头声明，而靠 manifest、adapter、matrix、verification command 共同约束；
3. 不同平台能力不等价时，明确标成 Instruction-backed、Adapter-backed 或 Reference-only；
4. 运行时状态统一靠 canonical snapshot，不让 UI 或上层逻辑直接读取某个平台内部细节。

---

## 5. 对 LDVH 的借鉴判断

### 5.1 LDVH 应学习什么

LDVH 应学习 ECC 的四个方法：

1. **共享内核 + 平台薄投影**：正式规范、工作流程、Code 合同保持在 LDVH 主事实源，Trae、Codex 等平台只保留薄入口和加载说明；
2. **平台能力显式声明**：每个平台清单必须说明支持什么、不支持什么、降级方式是什么、验证方式是什么；
3. **能力支持分级**：不要把平台能力简单标成支持/不支持，应区分 Native、Adapter-backed、Instruction-backed、Reference-only 这类状态；
4. **验证命令绑定平台声明**：每个平台支持声明都应有验证入口，否则只能是 candidate 或 reference。

### 5.2 LDVH 不应照搬什么

LDVH 不应照搬：

1. ECC 的完整安装器；
2. ECC 的 install state；
3. ECC 的 session control plane；
4. ECC 的多平台自动分发；
5. ECC 的 commands、skills、rules 原文；
6. ECC 的 repair 自动修复链路。

### 5.3 对 04 系列的可能启发

ECC 对 LDVH 04 系列的启发应限制在平台适配内部规则，不应扩张 04 主轴。

可考虑的后续方向：

| LDVH 位置 | 可吸收内容 |
|---|---|
| 04.06 平台适配清单规范 | 增加平台支持状态分级、验证命令、风险说明、source docs 字段 |
| 04.07 Trae-Solo 适配清单 | 明确 Trae 是 Native、Adapter-backed 还是 Instruction-backed 的具体能力项 |
| 04.08 Codex 适配清单 | 明确 Codex 中 AGENTS.md、commands、hooks、skills 的真实支持等级 |
| 42 LDVH落地与检查 | 消费平台支持状态，发现“声明支持但无验证命令”的漂移 |
| landing-plan | 输出平台能力差异、降级原因和 proposed_actions |

---

## 6. 建议任务拆解

### 6.1 任务名称

建立 LDVH 平台能力复用与薄投影检查模型。

### 6.2 任务目标

基于 ECC 跨平台机制，梳理 LDVH 如何在 Trae、Codex 等平台复用同一套 LDVH 能力，同时避免平台入口复制正式规范、平台能力声明失真或运行投影漂移。

### 6.3 建议输入

1. `docs/specs/04.06-平台适配清单规范.md`
2. `docs/specs/04.03-环境能力清单与环境适配规范.md`
3. `docs/specs/04.03-环境能力清单与环境适配规范.md`
4. `docs/specs/42-ldvh-landing-check-LDVH落地与检查.md`
5. `tools/specs_validate.py landing-plan`
6. ECC `docs/architecture/harness-adapter-compliance.md`
7. ECC `scripts/lib/harness-adapter-compliance.js`
8. ECC `scripts/lib/install-manifests.js`

### 6.4 建议输出

1. LDVH 平台能力支持状态枚举草案；
2. 平台适配清单字段补充草案；
3. Trae / Codex 能力对照表；
4. `landing-plan` 平台能力差异输出字段建议；
5. 42 检查中“平台声明无验证命令”“平台入口复制正文”“平台能力误标 Native”的诊断规则候选。

### 6.5 验收标准

1. 能解释同一 LDVH 能力如何在不同平台通过薄入口复用；
2. 能区分平台真实支持、适配支持、指令支持和仅参考；
3. 每个支持声明都有事实源依据和验证方式；
4. 不新增安装器、长期状态源或自动 repair；
5. 不改变 04 系列五层主轴。

---

## 7. 阶段性结论

ECC 跨平台复用相同功能的关键，不是平台能力真的一样，而是它把“能力内核”和“平台表面”分开：

1. 共享资产保持统一；
2. manifest 声明支持范围；
3. target adapter 处理平台落地差异；
4. session adapter 处理运行时观察差异；
5. compliance matrix 公开支持等级、风险和验证证据。

LDVH 最适合吸收的是这套“共享内核 + 平台薄投影 + 支持状态分级 + 验证命令绑定”的组织方法。它应进入 04.06/04.07/04.08、42 和 landing-plan 的候选改进，而不是变成安装器、session control plane 或多平台自动分发系统。
