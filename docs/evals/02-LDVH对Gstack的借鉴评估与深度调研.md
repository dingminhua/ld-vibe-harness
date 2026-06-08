# LD Vibe Harness 对 Gstack 的借鉴评估与深度调研

> 创建日期：2026-05-30
> 更新日期：2026-06-09
> 定位：LD Vibe Harness 对 Gstack 的项目级借鉴评估与深度调研
> 调研边界：不直接构成强制规则
> 执行效力：无；规范规则需进入 docs/specs 正文区，决策或工作事实需进入对应工作对象后才生效
> 上位依据：`docs/specs/00-LD-Vibe-Harness理念与纲要.md`
> 相关规范：`docs/specs/02-术语规范.md`、`docs/specs/01-目录说明.md`、`docs/specs/04-事实源边界与承载规范.md`
> 代码调研来源：`/Users/dmh2002/trae_projects/gstack`（完整代码库）

---

## 1. 本文解决的问题

本文评估 LD Vibe Harness 应如何借鉴 Gstack 的设计思想，同时保持自身"面向 Vibe Coding 的工程驾驭框架"的独特定位。本文在初始借鉴评估基础上，进一步沉淀对 Gstack 项目的深度调研结论，覆盖人工确认环节、测试流程、使用说明、LDVH 对比和社区口碑，作为 LDVH 后续产品化决策的事实基础。本文是内部调研，不直接构成强制规则；调研结论进入 docs/specs 正文区或 ADR 后才成为稳定规则。

---

## 2. 结论

Gstack 对 LD Vibe Harness 有较高参考价值，但 LD Vibe Harness 不应复制 Gstack 的产品形态。

更准确的判断是：

> Gstack 是面向 Claude Code 的 AI 工程工作流与技能工厂；LD Vibe Harness 是面向 Vibe Coding + Trae Solo 场景的工程驾驭框架，围绕事实源、事实模型和行动模型设计。

LD Vibe Harness 最值得借鉴 Gstack 的不是具体命令数量，也不是浏览器守护进程本身，而是以下能力组合：

1. 把 AI 协作拆成明确阶段和专业角色
2. 把高频协作流程固化为可复用 Skill
3. 把质量、QA、安全、发布、复盘纳入同一条工程链路
4. 坚持用户主权：AI 建议，人类决策
5. 用工具降低执行摩擦，但不让工具取代事实源和治理判断

深度调研进一步确认：Gstack 的 Human Gate 以偏好选择为主、可覆盖可跳过，与 LDVH 的治理纪律型 Human Gate 有根本差异；Gstack 的测试体系（三层 Tier + 浏览器 QA）和完整 Skill 工作流对 LDVH 有流程设计启发，但不应照搬其本地隐藏状态、自动发布和 AI 自审模式。

---

## 3. 项目概览（基于真实仓库阅读）

通过阅读 garrytan/gstack 仓库，Gstack 是一个围绕 Claude Code 构建的 AI 工程工作流项目。它通过一组 Markdown Skill、CLI 工具、浏览器能力和本地状态机制，把单个 AI 编程助手扩展成类似"虚拟工程团队"的协作体系。

从仓库结构观察，Gstack 的核心组成包括：

| 模块 | 作用 | 真实仓库中的体现 |
|---|---|---|
| Skill 集合 | 将 CEO、工程、设计、QA、安全、发布、复盘等角色固化为可调用工作流 | `autoplan/`, `review/`, `qa/`, `context-save/`, `context-restore/`, `spec/` 等目录，每个包含 SKILL.md 和模板 |
| 浏览器能力 | 通过持久化 Chromium 守护进程支持真实页面 QA、截图、交互和验证 | `browse/` 目录，包含 src、test，以及 bin 工具（chrome-cdp、find-browse、remote-slug） |
| 计划评审流程 | 在编码前进行产品、工程、设计、DX 等多视角评审 | `plan-ceo-review/`, `plan-eng-review/`, `plan-design-review/`, `plan-devex-review/` |
| 实现后门禁 | 通过 review、qa、cso、ship、land-and-deploy 等流程提升交付质量 | `ship/`, `land-and-deploy/`, `review/`, `cso/` |
| 记忆与复盘 | 通过 context-save、context-restore、learn、retro 等能力沉淀上下文和经验 | `context-save/`, `context-restore/`, `learn/`, `retro/` |
| 安全约束 | 通过 careful、freeze、guard、权限隔离、隧道隔离等方式降低误操作风险 | `careful/`, `freeze/`, `guard/`, `browse/src/` 中的安全相关逻辑 |
| 工具与 CLI | 一组 CLI 工具用于同步状态、配置、脑记忆、归档等 | `bin/` 目录下包含 `gstack-brain-sync`, `gstack-config`, `gstack-analytics`, `gstack-question-preference` 等 |
| 规范与约定 | 一套完整的 AskUserQuestion 格式、ELI10 解释风格、风险决策模板 | `docs/askuserquestion-split.md`, `docs/explanation-diataxis-in-gstack.md` 等 |

这说明 Gstack 的重点不是"任务管理"，而是"让 AI 编程流程可重复、可审查、可提速、可交付"。

从仓库结构和代码阅读中，我们发现 Gstack 的一个关键设计选择是：**所有 Skill 都以 Markdown + shell 混合形式编写，Skill 文件本身就是可执行的工作流说明**。

---

## 4. 与 LD Vibe Harness 的关系判断（基于真实仓库观察）

| 维度 | Gstack | LD Vibe Harness |
|---|---|---|
| 产品形态 | Claude Code Skill + CLI + 浏览器工具 | 本地规范 + Harness 工具 + 事实模型 + 行动模型 |
| 核心对象 | Skill、Agent 角色、浏览器会话、发布流程、上下文记忆 | Intent、Task、Memo、ADR、Evidence、Change、Pitfall |
| 主要目标 | 把 AI 编码助手扩展成工程团队流水线 | 让 AI 进入项目后知道读什么、做什么、不能做什么、何时停下、如何回写 |
| 数据事实源 | 技能文件、仓库文档、运行状态、上下文存档 | Git 仓库中的 specs、ldvh-base、docs |
| AI 角色 | 直接驱动 AI 工作流（AI 是主要执行者） | AI 是行动模型的执行者，不是工具直接调用的对象 |
| 工具价值 | 降低 AI 工程执行摩擦 | 降低读取、校验、聚合、展示和受控写入事实源的成本 |
| 风险边界 | 浏览器、远程配对、安全令牌、自动发布 | 事实源漂移、状态流转违规、门禁未触发、证据未回写 |
| 本地状态管理 | ~/.gstack/ 目录，包含配置、学习记录、问题偏好、会话状态等 | 目前事实源全在 Git 仓库中，无本地隐藏状态 |

LD Vibe Harness 不应成为 Gstack clone。LD Vibe Harness 可以吸收 Gstack 的工程化协作思想，但必须保持自身边界：

```text
LD Vibe Harness 不直接调用 AI
LD Vibe Harness 不成为事实源（事实源始终是 Git）
LD Vibe Harness 不替代 Human Gate
LD Vibe Harness 的工具只做聚合视图和受控编辑入口
```

### 4.1 关于 LDVH 在早期阶段"是否可以借鉴 Gstack"的判断

结合对 Gstack 仓库的阅读，我们重新评估：

> **对于早期 LDVH（当前阶段），非常适合借鉴 Gstack 的产品形态设计思路；但不应复制 Gstack 的具体实现方式（如 Claude Code Skill 结构、浏览器守护进程、本地隐藏状态目录等）。**

理由是：
1. LDVH 当前处于从"规范集合"向"可操作框架"过渡的阶段；
2. Gstack 提供了一个完整的例子：如何把复杂的工程治理包装成连续、可调用、低摩擦的交互体验；
3. LDVH 早期的高价值目标不是"是否符合现有设计假设"，而是"能否把现有规范变成实际可运行的治理工作台"；
4. Gstack 的结构（入口化 Skill、可执行工作流、显性化 Human Gate、上下文恢复）正好可以启发 LDVH 的早期形态设计；
5. 但 LDVH 的核心优势（Git 文件事实源、事实模型、行动模型）必须保留，不能被本地隐藏状态或临时上下文替代。

---

## 5. Gstack 人工确认环节分析

### 5.1 Gstack Human Gate 总览

Gstack 的人工确认机制通过 Claude Code 的 `AskUserQuestion` 工具实现。与 LDVH 的 Human Gate 不同，Gstack 的确认点更分散、更轻量，且大量确认点服务于"偏好选择"而非"治理纪律"。

Gstack 的人工确认可分为四类：

| 类型 | 说明 | 典型场景 |
|------|------|----------|
| **偏好选择** | 让用户在多个方案中选择 | CEO Review 的范围模式选择、设计风格偏好 |
| **安全护栏** | 阻止潜在危险操作 | `/careful` 拦截 rm -rf、force-push 等 |
| **流程门禁** | 阶段完成前的确认 | `/ship` 发布前审查、`/spec` 质量门禁 |
| **首次配置** | 一次性初始化确认 | 遥测选择、Skill 路由注入、GBrain 信任策略 |

### 5.2 各 Skill 的人工确认点

#### 5.2.1 首次运行确认（Preamble 阶段）

每个 Skill 启动时自动执行的 Preamble 包含多个首次确认：

1. **遥测选择**：首次运行时询问是否共享匿名使用数据（A: 推荐/B: 匿名/C: 关闭）
2. **主动建议开关**：是否允许 Gstack 主动推荐 Skill（A: 开启/B: 关闭）
3. **Skill 路由注入**：是否向项目 CLAUDE.md 添加路由规则（A: 添加/B: 拒绝）
4. **Vendoring 迁移警告**：检测到 vendored 安装时建议迁移到 team mode
5. **写作风格选择**：V1 简化风格 vs V0 简洁风格
6. **Artifacts 同步模式**：全量/仅产物/关闭
7. **功能发现**：Continuous checkpoint、Model overlay 等新功能提示

**关键发现**：Gstack 的 Preamble 确认点数量多（7+），但每个都是一次性确认（通过 marker 文件去重），且在 spawned session（OpenClaw 等编排器）中自动选择推荐选项，不阻塞自动化流程。

#### 5.2.2 `/plan-ceo-review` — CEO 审查

- **范围模式选择**：4 种模式——Expansion（扩展）、Selective Expansion（选择性扩展）、Hold Scope（保持范围）、Reduction（缩减）
- **每个前提挑战**：对每个被挑战的前提，用户需同意/不同意/调整
- **实现方案选择**：3 种实现方案 + 工作量估算
- **最终推荐确认**：是否接受推荐方案

#### 5.2.3 `/plan-eng-review` — 工程审查

- **架构决策确认**：关键架构选择需用户确认
- **测试计划确认**：生成的测试矩阵需用户审查

#### 5.2.4 `/plan-design-review` — 设计审查

- **交互式设计选择**：每个设计维度逐一 AskUserQuestion，0-10 评分后询问是否采纳改进建议
- 这是 Gstack 中交互密度最高的 Skill

#### 5.2.5 `/review` — 代码审查

- **AUTO-FIXED vs ASK 分类**：审查发现的问题分为两类
  - AUTO-FIXED：明显问题自动修复，无需确认
  - ASK：需要用户判断的问题，通过 AskUserQuestion 确认
- **范围漂移检测**：检测到 scope drift 时暂停，询问是否继续

#### 5.2.6 `/qa` — QA 测试

- **Bug 修复确认**：发现 bug 后，修复方案需确认
- **认证信息**：需要用户提供测试凭证（通过环境变量）
- **测试框架选择**：检测到无测试框架时，询问是否引导安装

#### 5.2.7 `/ship` — 发布

- **预飞行检查**：发布前展示所有检查结果，需确认
- **版本提升级别**：MINOR/MAJOR/PATCH 选择
- **测试覆盖审查**：展示测试增量，需确认
- **PR 创建确认**：最终 PR body 展示后确认

#### 5.2.8 `/spec` — 规格编写

- **五阶段门禁**：Why → Scope → Technical → Draft → Quality Gate
- **Quality Gate**：Codex 评分低于 7/10 时阻塞，需用户决定是否继续
- **Secret 检测**：发现敏感信息时阻塞

#### 5.2.9 `/careful` — 安全护栏

- **破坏性命令拦截**：检测到 rm -rf、DROP TABLE、force-push、git reset --hard 等命令时暂停并要求确认
- 用户可选择覆盖（override）任何警告

#### 5.2.10 `/investigate` — 调试

- **铁律门禁**：不允许未经调查就修复——3 次修复失败后必须暂停
- **模块冻结**：自动 `/freeze` 到正在调查的模块

#### 5.2.11 `/retro` — 复盘

- **焦点领域选择**：用户选择复盘关注点
- **改进计划确认**：生成的改进建议需确认

#### 5.2.12 `/design-shotgun` — 设计探索

- **变体选择**：每轮 4-6 个变体中用户选择偏好
- **反馈循环**：用户可提供文字反馈（"更多留白""更大标题"等）

### 5.3 Gstack Human Gate 的设计特点

1. **偏好驱动而非纪律驱动**：Gstack 的确认点主要服务于"让用户表达偏好"，而非"强制治理纪律"。用户始终可以选择跳过或覆盖。
2. **推荐选项明确**：每个 AskUserQuestion 都标注 `(recommended)` 选项，降低决策负担。
3. **自动化友好**：spawned session 自动选择推荐选项，不阻塞 OpenClaw 等编排器。
4. **无状态持久**：确认结果不写入 Git 事实源，仅通过本地 marker 文件（`~/.gstack/`）去重。
5. **安全护栏可选**：`/careful`、`/freeze`、`/guard` 是可选工具，默认不开启。

### 5.4 与 LDVH Human Gate 的关键差异

| 维度 | Gstack | LDVH |
|------|--------|------|
| 驱动力 | 偏好选择 | 治理纪律 |
| 持久化 | 本地 marker 文件 | Git 事实源 + 状态机 |
| 可追溯性 | 无（本地文件，不入 Git） | 有（YAML 状态、Change 记录） |
| 强制性 | 可覆盖、可跳过 | 状态机强制，不可绕过 |
| 自动化兼容 | spawned session 自动选推荐 | 需显式 Human Gate 确认 |
| 覆盖范围 | 所有 Skill 内嵌 | 仅关键状态流转和写入 |

---

## 6. Gstack 测试流程分析

### 6.1 Gstack 测试体系总览

Gstack 的测试分为三个层次：

| 层次 | 内容 | 成本 | 速度 |
|------|------|------|------|
| Tier 1 — 静态验证 | 解析 SKILL.md 中的 `$B` 命令，对照命令注册表验证 | 免费 | <5s |
| Tier 2 — E2E 测试 | 通过 `claude -p` 启动真实 Claude 会话，运行 Skill，检查错误 | ~$3.85/次 | ~20min |
| Tier 3 — LLM 评判 | Sonnet 对文档的清晰度/完整性/可操作性评分 | ~$0.15/次 | ~30s |

Tier 1 在每次 `bun test` 时自动运行。Tier 2+3 需设置 `EVALS=1` 环境变量。

### 6.2 测试基础设施

#### 6.2.1 Session Runner

E2E 测试通过 `test/helpers/session-runner.ts` 实现：

1. 将 prompt 写入临时文件（避免 shell 转义问题）
2. 启动 `sh -c 'cat prompt | claude -p --output-format stream-json --verbose'`
3. 流式读取 NDJSON 输出
4. 与可配置超时竞争
5. 将完整 NDJSON 转录解析为结构化结果

#### 6.2.2 Eval Store

`EvalCollector` 累积测试结果，两种写入方式：

1. **增量**：`savePartial()` 每个测试后写入 `_partial-e2e.json`（原子写入：先写 `.tmp`，再 `fs.renameSync`）
2. **最终**：`finalize()` 写入带时间戳的 eval 文件

#### 6.2.3 可观测性

所有可观测性 I/O 包裹在 try/catch 中——写入失败不会导致测试失败。测试本身是真相来源，可观测性是尽力而为。

### 6.3 浏览器测试（browse 模块）

browse 模块有独立的测试体系，是最密集的测试区域：

| 测试类型 | 文件数 | 覆盖范围 |
|----------|--------|----------|
| 单元测试 | 30+ | 命令解析、配置、安全、Cookie、代理等 |
| E2E 测试 | 10+ | 完整浏览器交互流程 |
| 安全测试 | 8+ | 对抗性安全、注入检测、审计等 |
| 集成测试 | 5+ | 侧边栏、标签页隔离、SSE 等 |

### 6.4 `/qa` Skill 的测试流程

`/qa` 是 Gstack 最核心的质量保证 Skill，其测试流程如下：

```
1. 初始化
   ├── 检测测试框架（无则引导安装）
   ├── 检测未提交更改
   └── 确认测试目标 URL

2. 认证（如需）
   ├── 通过环境变量获取凭证
   └── 导入浏览器 Cookie

3. 定向
   ├── $B goto URL
   ├── $B snapshot -i（获取交互元素）
   └── $B console（检查 JS 错误）

4. 探索
   ├── 遍历主要用户流程
   ├── 截图记录每一步
   └── 记录所有发现的问题

5. 文档化
   ├── 每个问题生成 bug 报告
   └── 分类：critical / major / minor

6. 修复循环（对每个可修复问题）
   ├── 定位源头代码
   ├── 实现修复
   ├── 原子提交
   ├── 生成回归测试
   └── 再测试验证

7. QA 报告
   ├── 问题汇总
   ├── 修复状态
   ├── 回归测试覆盖
   └── 剩余风险
```

### 6.5 `/review` Skill 的审查流程

```
1. 预检查
   ├── 平台检测
   ├── 分支状态检查
   └── 范围漂移检测

2. 差异分析
   ├── 生成 diff
   ├── 读取审查清单
   └── 分派专家审查

3. 专家审查（并行）
   ├── API 契约审查
   ├── 数据迁移审查
   ├── 可维护性审查
   ├── 性能审查
   ├── 安全审查
   ├── 测试审查
   └── 红队审查

4. 分类处理
   ├── AUTO-FIXED：自动修复
   └── ASK：需用户确认

5. 修复后审查
   └── 验证修复正确性

6. 持久化结果
```

### 6.6 `/ship` Skill 的发布流程

```
1. 预飞行检查
   ├── 分发管道检查
   ├── 合并基分支
   └── 未提交更改检测

2. 测试执行
   ├── 运行测试套件
   ├── 测试覆盖审计
   └── 无测试框架则引导安装

3. 计划完成检查
   ├── scope drift 检测
   └── plan-completion review

4. 预着陆审查
   ├── 调用 /review
   └── Review Readiness Dashboard

5. 版本提升
   ├── 检测版本类型
   └── 用户确认级别

6. 更新变更日志

7. 提交 + 推送

8. 创建 PR
   └── PR body 包含：测试摘要、覆盖变化、review 结果
```

### 6.7 测试流程的关键设计

1. **测试框架自动引导**：`/ship` 和 `/qa` 检测到无测试框架时，自动引导安装（Jest/Vitest/pytest 等）
2. **回归测试自动生成**：每个 `/qa` bug 修复自动生成回归测试
3. **100% 测试覆盖目标**：Gstack 明确追求 100% 测试覆盖率
4. **跨模型验证**：`/codex` 提供独立的 OpenAI Codex 审查，与 Claude 审查交叉验证
5. **真实验证优先**：`/qa` 使用真实浏览器（Chromium daemon）验证，而非静态分析

---

## 7. Gstack 详尽使用说明

### 7.1 安装

**前置条件**：Claude Code、Git、Bun v1.0+、Node.js（仅 Windows）

**安装命令**（在 Claude Code 中粘贴）：

```bash
git clone --single-branch --depth 1 https://github.com/garrytan/gstack.git ~/.claude/skills/gstack && cd ~/.claude/skills/gstack && ./setup
```

**Team Mode**（推荐，自动更新）：

```bash
(cd ~/.claude/skills/gstack && ./setup --team) && ~/.claude/skills/gstack/bin/gstack-team-init required && git add .claude/ CLAUDE.md && git commit -m "require gstack for AI-assisted work"
```

### 7.2 核心工作流

Gstack 的核心工作流遵循 **Think → Plan → Build → Review → Test → Ship → Reflect** 生命周期：

```
/office-hours → /plan-ceo-review → /plan-eng-review → [编码] → /review → /qa → /ship → /retro
```

每个 Skill 的输出成为下一个 Skill 的输入，形成产物连续交接。

### 7.3 完整 Skill 清单与用途

#### 7.3.1 Think 阶段

| Skill | 角色 | 用途 |
|-------|------|------|
| `/office-hours` | YC Office Hours | 6 个强制问题重构产品思路，生成设计文档 |
| `/investigate` | 调试员 | 系统化根因调试，铁律：不调查不修复 |

#### 7.3.2 Plan 阶段

| Skill | 角色 | 用途 |
|-------|------|------|
| `/plan-ceo-review` | CEO/创始人 | 4 种范围模式审查产品方向 |
| `/plan-eng-review` | 工程经理 | 锁定架构、数据流、边界情况、测试计划 |
| `/plan-design-review` | 高级设计师 | 0-10 评分每个设计维度，交互式改进 |
| `/plan-devex-review` | DX 负责人 | 开发者体验审查，TTHW 基准 |
| `/autoplan` | 审查流水线 | 一键运行 CEO → 设计 → 工程审查 |
| `/spec` | 规格作者 | 5 阶段将模糊意图转为精确规格 |

#### 7.3.3 Build 阶段

| Skill | 角色 | 用途 |
|-------|------|------|
| `/design-consultation` | 设计伙伴 | 从零构建设计系统 |
| `/design-shotgun` | 设计探索者 | 4-6 个 AI 变体 + 比较面板 + 反馈循环 |
| `/design-html` | 设计工程师 | 变体 → 生产 HTML（Pretext 布局，30KB，零依赖） |
| `/design-review` | 写代码的设计师 | 审查 + 修复，原子提交，前后截图 |

#### 7.3.4 Review 阶段

| Skill | 角色 | 用途 |
|-------|------|------|
| `/review` | 工程主管 | 预着陆审查，AUTO-FIXED + ASK 分类 |
| `/codex` | 第二意见 | OpenAI Codex 独立审查，跨模型交叉验证 |
| `/cso` | 安全官 | OWASP Top 10 + STRIDE 威胁建模 |
| `/devex-review` | DX 测试员 | 实际测试 onboarding 流程 |

#### 7.3.5 Test 阶段

| Skill | 角色 | 用途 |
|-------|------|------|
| `/qa` | QA 负责人 | 真实浏览器测试，发现 → 修复 → 回归 → 验证 |
| `/qa-only` | QA 报告员 | 只报告不修复 |
| `/browse` | QA 工程师 | 持久无头 Chromium，~100ms/命令 |
| `/benchmark` | 性能工程师 | 页面加载、Core Web Vitals、资源大小基准 |

#### 7.3.6 Ship 阶段

| Skill | 角色 | 用途 |
|-------|------|------|
| `/ship` | 发布工程师 | 同步 main → 测试 → 审查 → 推送 → PR |
| `/land-and-deploy` | 发布工程师 | 合并 PR → CI → 部署 → 验证生产健康 |
| `/canary` | SRE | 部署后监控循环 |
| `/document-release` | 技术写作 | 更新所有文档匹配已发布内容 |
| `/document-generate` | 文档作者 | 从零生成文档（Diataxis 框架） |

#### 7.3.7 Reflect 阶段

| Skill | 角色 | 用途 |
|-------|------|------|
| `/retro` | 工程经理 | 每周复盘，每人统计，发布连续性，测试健康趋势 |
| `/learn` | 记忆 | 管理跨会话学习，审查/搜索/修剪/导出 |

#### 7.3.8 安全与工具

| Skill | 用途 |
|-------|------|
| `/careful` | 破坏性命令安全护栏 |
| `/freeze` | 限制编辑到单一目录 |
| `/guard` | `/careful` + `/freeze` |
| `/context-save` | 保存进度 |
| `/context-restore` | 恢复上下文 |
| `/gstack-upgrade` | 自更新 |
| `/setup-gbrain` | GBrain 初始化 |
| `/sync-gbrain` | 同步代码到 GBrain |
| `/setup-deploy` | 部署配置 |
| `/setup-browser-cookies` | 导入浏览器 Cookie |
| `/pair-agent` | 跨 Agent 协调 |
| `/health` | 代码质量仪表板 |
| `/plan-tune` | 调整问题敏感度 |

### 7.4 浏览器操作（`/browse`）

Gstack 的浏览器是其核心硬能力。通过持久化 Chromium daemon 实现：

- **首次启动**：~3s，自动启动
- **后续命令**：~100-200ms
- **空闲超时**：30 分钟自动关闭
- **状态持久**：Cookie、标签页、登录会话跨命令保持

**核心命令**：

| 类别 | 命令 | 说明 |
|------|------|------|
| 导航 | `goto`、`back`、`forward`、`reload` | 页面导航 |
| 读取 | `text`、`html`、`links`、`forms`、`console`、`network` | 页面内容 |
| 交互 | `click`、`fill`、`press`、`select`、`upload`、`hover` | 元素操作 |
| 检查 | `is visible`、`is enabled`、`is checked`、`attrs`、`css` | 状态断言 |
| 截图 | `screenshot`、`responsive`、`snapshot -a` | 视觉证据 |
| 快照 | `snapshot -i`（交互元素）、`snapshot -D`（diff） | 可访问性树 + @ref |
| 标签 | `newtab`、`tab`、`tabs`、`closetab` | 多标签管理 |

**@ref 系统**：`snapshot -i` 生成 `@e1`、`@e2` 等引用，后续命令通过引用操作元素，无需 CSS 选择器。

### 7.5 GBrain 持久知识库

GBrain 是 Gstack 的跨会话记忆系统，4 种初始化路径：

1. **Supabase 已有 URL**：粘贴 Session Pooler URL
2. **Supabase 自动配置**：粘贴 Personal Access Token，~90s 完成
3. **PGLite 本地**：零账户零网络，~30s
4. **远程 GBrain MCP**：跨机器记忆

**信任策略**：每个仓库三级——read-write / read-only / deny

### 7.6 多宿主支持

Gstack 支持 10 种 AI 编码 Agent：

| Agent | 安装位置 |
|-------|----------|
| Claude Code | `~/.claude/skills/gstack-*/` |
| OpenAI Codex CLI | `~/.codex/skills/gstack-*/` |
| Cursor | `~/.cursor/skills/gstack-*/` |
| OpenClaw | 通过 ACP 直接使用 |
| 其他（Slate、Kiro、Hermes 等） | 各自目录 |

### 7.7 Continuous Checkpoint Mode

可选的自动提交模式：

```bash
gstack-config set checkpoint_mode continuous
```

- 自动以 `WIP:` 前缀提交工作进度
- 包含结构化 `[gstack-context]` body（决策、剩余工作、失败方法）
- `/context-restore` 读取这些提交重建会话状态
- `/ship` 在 PR 前过滤压缩 WIP 提交
- Push 默认关闭（`checkpoint_push=false`）

---

## 8. LDVH 与 Gstack 的区别对比

### 8.1 理念层对比

| 维度 | Gstack | LDVH |
|------|--------|------|
| 核心定位 | AI 编程效率工具包 | Vibe Coding 治理框架 |
| 第一服务对象 | 单人开发者（solo builder） | AI 协作者 + 人类决策者 |
| 核心隐喻 | 虚拟工程团队（23 角色） | 治理骨架（事实模型 + 状态机） |
| 价值主张 | 速度优先——810× 效率提升 | 可审计优先——每个变更可追溯 |
| 工作流哲学 | Think → Plan → Build → Review → Test → Ship → Reflect | Intent → Plan → Execute → Verify → Record → Learn |
| 规范定位 | 规范是 AI 需要记住的提示词 | 规范是可推理的权威依据 |

### 8.2 架构层对比

| 维度 | Gstack | LDVH |
|------|--------|------|
| 事实源 | `~/.gstack/` 本地隐藏目录 + GBrain | Git 文件事实源（`ldvh-base/` YAML） |
| 状态管理 | 本地 JSON/JSONL 文件，不入 Git | YAML 状态机，入 Git，可审计 |
| 持久化策略 | 本地文件 + 可选 Supabase/PGLite | Git 仓库 + PyTools 校验 |
| Skill 承载 | SKILL.md 提示词 + SKILL.md.tmpl 模板 | Trae Skill 机制 + specs 规范 |
| 浏览器能力 | 持久化 Chromium daemon（核心硬能力） | Trae Preview + RunCommand（轻量替代） |
| 多宿主 | 10 种 AI Agent 支持 | Trae Solo 原生 |
| 安全模型 | 多层防御（ML 分类器 + Canary + 双监听器） | Human Gate + 事实源边界 + 状态机 |

### 8.3 治理层对比

| 维度 | Gstack | LDVH |
|------|--------|------|
| Human Gate | 偏好选择型，可覆盖，可跳过 | 治理纪律型，状态机强制，不可绕过 |
| 变更追溯 | 无（本地文件不入 Git） | Change 记录 + Git commit + Evidence |
| 决策记录 | 无独立 ADR 机制 | ADR 状态机（proposed → accepted → superseded） |
| 状态机 | 无（Skill 无状态） | 7 个事实模型各有状态机 |
| 验证 | 浏览器真实验证 + 测试覆盖 | PyTools 校验 + Fact Validator + Evidence |
| 可审计性 | 低（本地状态，无持久化） | 高（Git 事实源，可追溯） |

### 8.4 安全模型对比

| 维度 | Gstack | LDVH |
|------|--------|------|
| 安全哲学 | 纵深防御（多层 ML + 规则 + 审计） | 治理优先（Human Gate + 事实源边界） |
| Prompt 注入防御 | 6 层防御（L1-L6） | 不直接处理（由宿主环境负责） |
| Cookie 安全 | Keychain 审批 + 内存解密 + 只读数据库 | 不涉及 |
| 网络安全 | 双监听器 + 隧道隔离 + 速率限制 | 不涉及 |
| 破坏性操作防护 | `/careful` 可选拦截 | Rules 强制约束 |
| 事实源保护 | 无（本地文件可随意修改） | 场景规则强制（不得直接编辑 `ldvh-base/`） |

### 8.5 产品化层对比

| 维度 | Gstack | LDVH |
|------|--------|------|
| 安装体验 | 一行命令，30 秒 | 规则 + Skill + Tools 组合 |
| 学习曲线 | 低（斜杠命令，推荐选项） | 中（需理解规范体系） |
| 自动化程度 | 高（自动提交、自动推送、自动发布） | 低（每步需 Human Gate） |
| 跨项目复用 | 高（team mode + auto-update） | 中（规则 + Skill 可复用，事实源项目级） |
| Web 展示 | 无（CLI 为主） | Web MVP（只读态势 + 受控操作） |
| 遥测 | 可选匿名遥测 | 无 |

---

## 9. Gstack 社区真实口碑与用户反馈

### 9.1 基本信息

- **作者**：Garry Tan（Y Combinator CEO）
- **开源时间**：2026 年 3 月 12 日
- **GitHub Star**：约 10 万
- **协议**：MIT，完全免费
- **核心定位**：Claude Code 技能包，23 个专业角色 + 8 个工具模块

### 9.2 正面评价

1. **角色分离范式被认可**：多个独立团队不约而同收敛到"基于角色的 AI 开发"模式，被认为是"趋同进化"
2. **`/plan-ceo-review` 被视为核心价值**：能像 YC 合伙人一样拷问产品方向，多位用户认为"仅凭这一个技能就足以让它属于不同类别"
3. **浏览器子系统技术含量获认可**：持久化 Chromium daemon、~100ms 延迟、Cookie 安全模型
4. **对独立开发者和小团队价值显著**：相当于"免费技术顾问团队"
5. **交互设计友好**：给出 A/B/C 选项而非开放式问题

### 9.3 负面评价

1. **"本质就是一堆提示词"**：最核心批评——YouTube 博主 Mo Bitar（150 万浏览）尖锐指出 Gstack 本质是 Markdown 提示词文件夹
2. **AI 审查自己写的代码**：让 Claude 审查自己刚写的代码，存在"自己给自己打分"的根本性缺陷
3. **5 大实际使用痛点**：
   - 无清晰的审查状态提示
   - 会话切换后无法同步已做决策
   - 会话污染（审查思维残留）
   - 上下文积累过快（3 个 Skill 后不精准）
   - 强依赖底层模型
4. **GitHub Issues 中的技术问题**（238 个 Open）：
   - `sync-gbrain` 的 `rm -rf` 误删仓库根目录（严重）
   - Windows 兼容性问题
   - 浏览器守护进程崩溃循环
   - 安全审计正则遗漏现代 API Key 格式
5. **与个人工作流过度耦合**：核心设计针对 Claude Code，迁移到 Cursor 等工具成本高
6. **每个技能文件嵌入 GarrysList.org 广告**，引发用户反感

### 9.4 重大争议

1. **Star 数量争议**：社区质疑 Star 增速异常，HN 讨论帖被标记/降权
2. **"810 倍效率"指标之争**：社区共识为"用 KLOC 衡量生产力"是倒退
3. **AI 制造"虚假工程师幻觉"**：Mo Bitar 核心论点——大模型不是"能力放大器"，而是"自信放大器"
4. **心理健康担忧**：Garry Tan 自称每晚只睡四小时

### 9.5 与竞品对比（用户观点）

| 维度 | Gstack | Superpowers | AI-SDLC | BMAD |
|------|--------|-------------|---------|------|
| 核心理念 | 角色分工 | 强制 TDD + 工程纪律 | 完整生命周期 | 企业级方法论 |
| TDD 强制 | 否 | 是 | 审查阶段处理 | — |
| 安全设计 | 安全审查员角色 | 无专门设计 | 独立安全阶段 | — |
| 自我改进 | 否 | 否 | 是 | — |

社区建议：Superpowers + Gstack 组合使用效果最佳——Superpowers 管工程纪律，Gstack 管角色分工。

### 9.6 总结判断

Gstack 是一个被名人效应放大但确实有实质价值的工具。核心贡献：

1. 确立了"角色分离"作为 AI 协作范式
2. 浏览器守护进程是真正的工程产出
3. 编码了一个人的判断力（Garry Tan 的 YC 方法论）

局限同样明显：本质仍是提示词工程、AI 审查自己存在根本缺陷、与个人工作流深度耦合、上下文膨胀问题未解决。最适合独立开发者和小团队做技术规格审查，不适合替代真正的工程团队。

---

## 10. 最值得借鉴的设计思想（基于真实仓库阅读）

### 10.1 阶段化 AI 工程流程

Gstack 将软件开发拆成多个阶段：想法澄清、计划评审、工程评审、设计评审、实现、QA、安全、发布、复盘。每个阶段都有明确入口和输出。

LD Vibe Harness 可以借鉴这种阶段化方式，但落点不是"自动执行这些阶段"，而是让 Harness 行动模型能判断一个意图或任务当前处于什么治理阶段。

建议 LD Vibe Harness 在行动模型中强化以下阶段：

| 阶段 | LD Vibe Harness 中的呈现 |
|---|---|
| 输入 | Intent 或 Memo |
| 分析 | 关联 docs / ADR / 审计发现 |
| 决策 | Decision Needed / Human Gate |
| 执行 | Task 进入 Executing |
| 验证 | Review Needed，若升级为正式规范，宜要求验证证据 |
| 关闭 | Closed，若升级为正式规范，宜要求 closure_evidence |
| 复盘 | 进入 Change、Pitfall 或 ADR |

这能把 LD Vibe Harness 的状态机从"字段"变成"AI 理解的流程"。

### 10.2 AskUserQuestion 格式的启发

Gstack 对 Human Gate 有非常具体的格式要求，这点对 LDVH 极有启发：

```markdown
D<N> — <one-line question title>
Project/branch/task: <1 short grounding sentence>
ELI10: <plain English a 16-year-old could follow, 2-4 sentences, name the stakes>
Stakes if we pick wrong: <one sentence on what breaks, what user sees, what's lost>
Recommendation: <choice> because <one-line reason>
Completeness: A=X/10, B=Y/10 (or: Note: options differ in kind, not coverage — no completeness score)
Pros / cons:
A) <option label> (recommended)
  ✅ <pro — concrete, observable, ≥40 chars>
  ❌ <con — honest, ≥40 chars>
B) <option label>
  ✅ <pro>
  ❌ <con>
Net: <one-line synthesis of what you're actually trading off>
```

关键设计亮点：
- **ELI10**：每个决策都必须用普通人能懂的语言解释（Explain Like I'm 10）；
- **Stakes**：明确指出选错的后果；
- **Completeness Score**：评估选项在完整性上的差异；
- **Pros/Cons**：每个选项都至少有 2 个正面点和 1 个负面点，且至少 40 字符；
- **Net synthesis**：总结实际权衡关系；
- **Hard Stop**：破坏性操作要求必须是 "✅ No cons — this is a hard-stop choice"。

LDVH 可以直接借鉴这种格式，把 Human Gate 从简单的"停下来"变成结构化的决策卡片。

### 10.3 角色化 Skill 矩阵（轻量版）

Gstack 的一个核心优势是角色非常清晰：CEO reviewer、eng manager、designer、QA lead、security officer、release engineer 等。每个 Skill 不只是提示词，而是一个稳定工作流。

但基于真实仓库阅读，Gstack 实际采用的是"先 Skill 后 Agent"的路径：

```text
先有稳定的 Skill 工作流 → 确有需要时再做成 Agent
```

LD Vibe Harness 可以借鉴角色矩阵，但不宜一开始创建大量 Agent。更适合的路径是：

```text
先沉淀角色视角（检查清单/格式/提示词）→ 再沉淀 Skill（可调用工作流）→ 最后在确有隔离需求时创建 Agent
```

可参考的 LD Vibe Harness 角色视角：

| Gstack 角色 | LD Vibe Harness 可借鉴角色 | 用途 |
|---|---|---|
| CEO reviewer | 意图价值审视 | 判断目标是否值得做、是否偏离方向 |
| Eng reviewer | 规范与架构审视 | 判断状态机、事实源、接口边界是否正确 |
| Designer | 体验审视 | 判断视图是否清楚、操作是否低摩擦 |
| QA lead | 验证证据审视 | 判断完成标准和验证方式是否充分 |
| CSO | 风险与权限审视 | 判断是否涉及破坏性操作、依赖、密钥、跨项目影响 |
| Release engineer | 关闭与发布审视 | 判断是否可关闭、是否需要 Change 或 ADR |

这与 LD Vibe Harness 后续 Trae Solo 环境机制规范中 Rule / Skill / Agent 的边界一致：默认优先 Rule + Skill，只有独立上下文、权限隔离、并行委派或调度明确需要时才升级为 Agent。

### 10.4 "计划先行"的门禁体验

Gstack 中 plan-ceo-review、plan-eng-review、plan-design-review、plan-devex-review 和 autoplan 体现了一个重要原则：重要工作在执行前应先被多视角审视。

LD Vibe Harness 可借鉴为行动模型中的前置检查能力：

| 场景 | LD Vibe Harness 可提示的问题 |
|---|---|
| 新 Intent 进入分析 | 目标是否清楚？成功标准是否可验证？是否已有事实源？ |
| Task 创建 | 是否有 source_doc / source_intent？是否有 acceptance？是否能关闭？ |
| 状态进入 Executing | 前置条件是否满足？是否有阻塞依赖？ |
| 状态进入 Review Needed | 是否有验证方式和证据？ |
| 状态进入 Closed | closure_evidence 是否完整？是否需要 Change 或 ADR？ |

这类提示不需要 LD Vibe Harness 调用 AI，也可以先用规则校验和静态检查实现。

### 10.5 "真实环境 QA"意识

Gstack 很重视浏览器 QA，强调真实 Chromium、真实点击、截图、响应式、表单、上传、弹窗和部署后验证。

LD Vibe Harness 目前不是浏览器自动化工具，但可以借鉴它的 QA 证据思维：任务关闭前必须能回答"在哪里验证、怎么验证、证据是什么"。

建议 LD Vibe Harness 在事实模型规范中强化：

| 字段或视图 | 借鉴点 |
|---|---|
| acceptance | 用可观察行为描述完成标准 |
| verification | 记录实际验证命令、页面、截图或检查方式 |
| closure_evidence | 关闭时必须填入证据 |
| related_audit | 审计发现关闭要能回链到验证结果 |

LD Vibe Harness 不必内置 Gstack 式浏览器守护进程，但可以让任务天然容纳来自人工、Trae、浏览器工具或其他 QA 工具的验证证据。

### 10.6 安全与破坏性操作边界

Gstack 的 careful、freeze、guard、隧道双监听、安全令牌、cookie 处理等设计体现了清晰的风险分层。

从 Gstack 代码中观察到，风险分层通常包括：
- **Hard Stop**：必须停止的操作（如 rm -rf, DROP TABLE 等）；
- **Careful**：需要确认的高风险操作；
- **Freeze**：限制编辑范围的操作；
- **Guard**：同时激活 careful + freeze。

LD Vibe Harness 可借鉴为门禁规则：

| 风险类型 | LD Vibe Harness 中的建议处理 |
|---|---|
| 删除文件、重排文档编号、变更事实源 | 触发 Human Gate |
| 新增依赖、引入 GUI 框架、修改工具架构 | 触发 Human Gate |
| 跨项目影响、接口契约变化 | 触发跨项目评估 |
| 审计发现自动转任务 | 不能无脑任务化，必须先分类 |
| 修改规则或规范 | 必须同步创建 Change 和更新索引 |

LD Vibe Harness 已有硬约束。Gstack 的启发是：门禁不应只写在文档里，也应在 Harness 工具和 AI 行动模型中可见。

### 10.7 用户主权原则

Gstack 的 ETHOS 强调"AI models recommend, users decide"。这与 LD Vibe Harness 的 Human Gate 原则高度一致。

从 Gstack 仓库观察到，这条原则不是口号，而是具体的设计约束：
- 没有 AskUserQuestion 的 Skill 不能执行关键决策；
- 5 个以上选项时必须使用分拆问题链（不能直接做选择）；
- 即使两个 AI 模型都同意，也不能自动执行（只是更强的推荐）。

LD Vibe Harness 应继续坚持：

```text
AI 可以建议
工具可以提示
审计可以发现
但关键决策必须由用户确认
```

尤其是以下场景不能自动执行：

1. 架构方向变化
2. 文档编号重排
3. 删除或归档关键资产
4. 新增依赖
5. 跨项目规则或契约变化
6. 把不确定审计发现自动变成执行任务

---

## 11. 对 LD Vibe Harness 的启发

### 11.1 从"看板"升级为"协作驾驭体系"

Gstack 的命令集合覆盖了从想法到发布的完整链路。LD Vibe Harness 可将自身设计为项目治理驾驶舱，而不是普通任务列表。

建议强化五类入口：

| 入口 | 目标 |
|---|---|
| 今日行动 | 展示当前最该处理的 Task |
| 决策等待 | 聚合 Decision Needed 和 Human Gate |
| 验证等待 | 聚合 Review Needed 和缺少 closure_evidence 的任务 |
| 审计闭环 | 展示审计发现分类、处理状态、关闭证据 |
| AI 上下文 | 一键生成当前任务需要阅读的 specs、docs、ADR、审计摘要 |

### 11.2 给每个任务生成"下一步提示"

Gstack 的 Skill 是可执行流程，LD Vibe Harness 可以先从轻量的下一步提示做起。

例如任务状态为 `Review Needed` 时，Harness 工具或 AI 行动模型应提示：

```text
关闭前需要：
1. 填写验证方式
2. 填写 closure_evidence
3. 判断是否需要创建 Change
4. 若涉及决策，确认是否已有 ADR
```

这样可以把规范转化为产品体验，降低 AI 和人记忆规则的负担。

### 11.3 把"AI 上下文包"产品化

Gstack 通过 context-save/context-restore 解决跨会话上下文恢复。LD Vibe Harness 的优势是项目事实源更明确，因此更适合生成任务级上下文包。

建议 LD Vibe Harness 提供：

| 上下文包 | 内容 |
|---|---|
| Task 上下文 | 当前任务 YAML、source_doc、dependencies、acceptance、closure_evidence |
| Intent 上下文 | Intent 文档、关联 TaskSet、相关 ADR |
| Audit 上下文 | 审计快照、审计发现、分类结果、待关闭任务 |
| Human Gate 上下文 | 决策问题、选项、影响范围、推荐阅读 |

这些上下文包可以提供给 AI 或人，但 LD Vibe Harness 本身不需要直接调用 AI。

---

## 12. 产品借鉴意义重新评估

重新评估后，Gstack 对 LD Vibe Harness 的产品借鉴意义不应停留在"是否也做一组 Skill 或命令"，而应上升到"如何把治理框架转化为用户能直接感知的产品体验"。

LD Vibe Harness 当前的核心资产是事实源边界、事实模型、行动模型、Human Gate 和工具分层；这些资产如果只停留在规范文本中，用户感知会接近"规则很多"。Gstack 的产品启发在于：同样是复杂工程链路，可以通过阶段入口、角色视角、下一步动作、门禁反馈和上下文恢复，转化为用户能够连续操作的工作台体验。

### 12.1 产品定位上的借鉴

| Gstack 产品特征 | 对 LD Vibe Harness 的启发 | LDVH 应采用的产品表达 |
|---|---|---|
| 把 AI 编程助手包装成工程团队流水线 | 用户需要的不是对象字段，而是"现在该谁判断、该做什么、做到哪一步" | 将事实模型和行动模型呈现为治理驾驶舱、待决策队列、待验证队列和上下文入口 |
| Skill/命令有清晰场景名 | 产品入口应使用人的任务语言，而不是内部模型语言 | 用"开始审计""准备上下文""关闭任务""请求决策""复盘变更"等操作表达模型动作 |
| 计划、评审、QA、安全、发布形成连续链路 | LDVH 可以把分散规范转成端到端闭环 | 围绕 Intent → Task → Evidence → Change/Pitfall/ADR 展示闭环进度 |
| 真实 QA 与截图证据强化完成感 | 关闭动作应让用户感知证据是否充分 | 在任务关闭、Review、审计闭环中突出 verification 和 closure_evidence |
| 上下文保存/恢复降低跨会话成本 | LDVH 的事实源优势可转化为更强的上下文恢复体验 | 提供面向 AI 和人的"当前任务上下文包"和"推荐阅读包" |

产品定位上，LDVH 不宜宣传为"更多 AI 自动化能力"，而应表达为：

```text
让人和 AI 在同一个事实源治理工作台中推进需求、任务、证据、决策和复盘。
```

这比"任务管理工具""规范仓库""AI 命令集合"都更贴近 LDVH 的独特价值。

### 12.2 产品形态上的借鉴

Gstack 的强产品感来自"可调用入口"而不是"文档解释"。LDVH 可以借鉴这种入口化思路，但入口不应复制 slash command，而应落到 Web 信息同步层和 Tools 辅助层的分工上。

| 产品入口 | 用户看到的问题 | 背后对应的 LDVH 能力 |
|---|---|---|
| 今日推进 | 今天最应该推进哪些任务，为什么是它们 | Task 状态、依赖、阻塞、Review Needed、Decision Needed 聚合 |
| 决策等待 | 哪些地方必须由人确认，选项和影响是什么 | Human Gate、ADR 候选、关键状态流转、风险提示 |
| 关闭检查 | 这个任务为什么还不能关闭 | acceptance、verification、closure_evidence、Change/Pitfall/ADR 关联检查 |
| 上下文包 | 继续这个任务前应该读什么 | source_doc、related ADR、相关规范片段、依赖对象聚合 |
| 审计闭环 | 审计发现是否被分类、处理和验证 | Audit 结果、Task 分流、关闭证据和复盘对象回链 |
| 复盘沉淀 | 哪些经验应该变成 Pitfall 或 ADR | Change、失败记录、反复出现的问题、决策稳定性判断 |

这些入口的共同点是：用户先看到"要做的事"和"为什么"，再进入对象字段或事实源编辑。这样可以把 LDVH 的严谨性转化为低摩擦体验，而不是让用户直接面对对象规范复杂度。

### 12.3 产品优先级上的借鉴

重新评估后，LDVH 更应优先产品化以下能力：

1. **状态解释**：不仅展示状态，还解释为什么处于该状态、允许流转到哪里、缺少什么证据；
2. **门禁显性化**：Human Gate 不只是规则要求，而是产品中的待确认卡片、影响说明和可选动作；
3. **上下文一键化**：把 AI 继续工作所需的 specs、docs、ADR、对象实例和检查要求聚合成可复制上下文；
4. **关闭仪式感**：关闭任务时强制呈现验收标准、验证结果、证据和是否需要 Change/Pitfall/ADR 的判断；
5. **审计可闭环**：审计发现不能只显示问题列表，而要显示分类、处理路径、责任对象、关闭证据和遗留风险；
6. **角色视角轻量化**：先用产品视角和检查清单承载"意图价值、工程规范、体验、QA、安全、发布"六类审视，不急于创建大量 Agent；
7. **规范到操作的翻译**：每条关键规范应尽量在产品中表现为提示、检查、入口、阻止或证据要求。

这些优先级说明：LDVH 的下一阶段产品价值，不在于把 Gstack 的角色和命令搬过来，而在于把既有 LDVH 规范变成更容易被人和 AI 执行的交互系统。

### 12.4 不应借鉴的产品方向

| 不应借鉴 | 原因 |
|---|---|
| 把产品主入口设计成命令大全 | LDVH 的用户痛点是事实源治理和闭环推进，不是记住更多命令 |
| 把角色 Skill 作为早期产品卖点 | 角色过早产品化会掩盖事实源、证据和门禁这些基础能力 |
| 把浏览器自动化作为核心差异 | 真实 QA 很重要，但 LDVH 当前更需要先接收和治理证据，而不是自建自动化执行器 |
| 把自动发布、自动提交、自动合并做成默认能力 | 这会削弱 Human Gate 和用户主权，也容易越过 LDVH 工具边界 |
| 把工具输出包装成事实源 | 产品体验再顺滑，也不能让 UI 状态、缓存或派生视图替代 Git 文件事实源 |

### 12.5 重新评估结论

Gstack 对 LDVH 的最大产品借鉴意义是：它证明复杂 AI 工程治理可以被包装成连续、可调用、低摩擦的产品体验。

LDVH 应吸收这种产品化能力，但采用自己的事实源治理路径：

```text
Gstack 的产品核心：把 AI 工程团队化。
LDVH 的产品核心：把事实源治理、Human Gate、证据闭环和 AI 上下文协作工作台化。
```

因此，后续 LDVH 产品设计应优先围绕"今日推进、决策等待、关闭检查、上下文包、审计闭环、复盘沉淀"形成工作台，而不是优先复制 Gstack 的命令体系、浏览器守护进程或大量角色 Skill。

---

## 13. 可落地建议（基于真实 Gstack 仓库启发）

### 13.1 短期建议（现在可以做）

| 建议 | 说明 | 借鉴点 |
|---|---|---|
| 在任务详情增加下一步提示 | 根据状态机提示允许流转、必填证据和 Human Gate | Gstack 的 Skill 中每步都有明确下一步 |
| 设计 AI 上下文复制入口 | 从 Task / Intent / Audit 聚合推荐阅读材料 | Gstack 的 context-save/context-restore |
| 强化 Review Needed 视图 | 聚合所有待验证、缺证据、待关闭任务 | Gstack 的 review/qa 视图聚合 |
| 审计发现分类时显示理由 | 避免"自动任务化"黑盒 | Gstack 的明确分类理由 |
| 将 closure_evidence 做成关闭门槛 | 关闭不是改状态，而是提交证据 | Gstack 的 qa/ship 证据要求 |
| 实现 Human Gate 结构化卡片 | 使用类似 Gstack 的 AskUserQuestion 格式（ELI10、Stakes、Completeness、Pros/Cons） | Gstack 的决策卡片设计 |
| 建立"今日推进"入口 | 展示当前最应该推进的任务，说明为什么 | Gstack 的 autoplan 入口设计 |

### 13.2 中期建议（接下来可以做）

| 建议 | 说明 | 借鉴点 |
|---|---|---|
| 建立 LD Vibe Harness Skill 矩阵 | 围绕意图审查、任务关闭、审计分类、上下文生成沉淀 Skill | Gstack 的 Skill 组织结构 |
| 增加决策等待视图 | 聚合 Decision Needed、ADR 候选、Human Gate 等待项 | Gstack 的 guard/careful 设计 |
| 增加关闭检查入口 | 关闭前显式检查 acceptance、verification、closure_evidence、Change/Pitfall/ADR | Gstack 的 ship/land-and-deploy 检查 |
| 增加复盘视图 | 从 Change、Pitfall、关闭任务中形成周期性回顾 | Gstack 的 retro 能力 |
| 增加治理健康分 | 用静态检查展示 specs、ldvh-base、docs 的健康状态 | Gstack 的 review 评分思路 |

### 13.3 暂不建议（当前阶段不宜做）

| 不建议项 | 原因 |
|---|---|
| 复制 Gstack 的大量 slash commands | LD Vibe Harness 的主要对象不同，照搬会制造复杂度 |
| 让 LD Vibe Harness 直接调用 AI | 违反当前工具边界，且会模糊事实源与执行者 |
| 内置浏览器自动化守护进程 | 当前 LD Vibe Harness 不是 QA 自动化工具，可先接收外部证据 |
| 一次性创建大量 LD Vibe Harness Agent | Agent 有上下文和权限成本，应先用 Skill 验证流程稳定性 |
| 自动发布、自动提交、自动合并 | LD Vibe Harness 是治理框架，不是发布机器人 |
| 引入 ~/.ldvh/ 本地隐藏状态目录 | LDVH 的事实源应该始终在 Git 仓库中，避免本地状态与事实源不一致 |

---

## 14. 风险评估

| 风险 | 表现 | 控制方式 |
|---|---|---|
| 过度 Gstack 化 | LD Vibe Harness 变成 AI 命令集合，失去事实源治理定位 | 坚持 specs/ldvh-base//docs 为事实源 |
| Skill 泛滥 | 每个想法都做 Skill，维护成本升高 | 只有重复、多步骤、稳定输出的流程才做 Skill |
| Agent 泛滥 | 角色很多但没有独立上下文必要 | 按 Trae Solo 环境机制规范中的 Agent 创建门槛执行 |
| 自动化越权 | 工具直接替用户做关键决策 | Human Gate 必须可见、可审计 |
| 证据形式化 | closure_evidence 变成空字段 | 关闭时校验非空、可追溯、能说明验证结果 |
| 外部项目误读 | 把 Gstack 的 Claude Code 实现当成 Trae 事实 | Trae 落地以 Trae Solo 环境机制规范为准 |

---

## 15. 评估结论（基于真实仓库阅读）

基于对 garrytan/gstack 真实仓库的阅读，我们重新评估后得出：

> 对于早期 LDVH（当前阶段），非常适合借鉴 Gstack 的产品形态设计思路；但不应复制 Gstack 的具体实现方式。

Gstack 对 LD Vibe Harness 的核心启发可以浓缩为一句话：

> 把 AI 协作从"临场聊天"升级为"有角色、有阶段、有证据、有门禁、有复盘的工程系统"。

LD Vibe Harness 应吸收这一思想，但走自己的路径：

```text
Gstack：让 AI 更像一支工程团队（通过 Claude Code Skill + CLI + 浏览器工具）
LD Vibe Harness：让项目事实源和 AI 协作治理更像一个可操作的驾驭工作台（通过 specs/ldvh-base/docs + 聚合工具 + 事实模型）
```

因此，LD Vibe Harness 后续最优先的借鉴方向不是增加更多 AI 能力，而是把现有规范产品化：

1. 状态流转可见（且解释为什么在该状态）
2. 下一步动作可见（结构化提示）
3. 关闭证据可见（强制验收）
4. Human Gate 可见（用 ELI10 + Stakes + Completeness + Pros/Cons 的决策卡片）
5. AI 上下文可复制（一键式上下文包）
6. 审计闭环可追踪（从发现到处理到验证到复盘）
7. 意图全貌可理解（从目标到依赖到证据到复盘）

当这些能力稳定后，再逐步把高频治理流程沉淀为 LD Vibe Harness Skill；只有在独立上下文、权限隔离、并行委派或调度成为真实需求时，再考虑 LD Vibe Harness Agent。

---

## 16. 来源

### 16.1 代码来源

- `/Users/dmh2002/trae_projects/gstack/README.md`
- `/Users/dmh2002/trae_projects/gstack/SKILL.md`
- `/Users/dmh2002/trae_projects/gstack/ARCHITECTURE.md`
- `/Users/dmh2002/trae_projects/gstack/plan-ceo-review/SKILL.md`
- `/Users/dmh2002/trae_projects/gstack/review/SKILL.md`
- `/Users/dmh2002/trae_projects/gstack/qa/SKILL.md`
- `/Users/dmh2002/trae_projects/gstack/ship/SKILL.md`
- `/Users/dmh2002/trae_projects/gstack/careful/SKILL.md`
- `/Users/dmh2002/trae_projects/gstack/investigate/SKILL.md`
- `/Users/dmh2002/trae_projects/gstack/retro/SKILL.md`
- `/Users/dmh2002/trae_projects/gstack/spec/SKILL.md`
- `/Users/dmh2002/trae_projects/gstack/browse/src/` 目录下多个源文件
- `/Users/dmh2002/trae_projects/gstack/lib/gbrain-guards.ts`

### 16.2 社区反馈来源

- Gstack 实测文章（今日头条多篇文章）
- GitHub Issues（238 个 Open Issues）
- Hacker News 讨论帖
- YouTube Mo Bitar 评测视频（150 万浏览）
- Reddit 社区讨论
- 与 Superpowers、AI-SDLC、BMAD 的对比文章

### 16.3 内部参考

- `docs/evals/21-LDVH全盘确认与核心吸收建议.md`

---

## 17. 待补齐事项

1. 本文结论如何进入 12 系列工具规范待工具规范稳定后确定；
2. 本文结论如何影响 20-49 事实模型规范待对象规范稳定后确定；
3. 本文结论如何影响 50-79 行动模型规范待行动模型规范稳定后确定；
4. 本文结论如何影响 11 系列 Trae Solo 环境机制规范（Skill / Agent 设计）待机制规范稳定后确定；
5. Human Gate 结构化卡片设计（借鉴 Gstack 的 AskUserQuestion 格式）待 11 系列规范稳定后确定。
