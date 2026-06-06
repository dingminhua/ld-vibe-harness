# Gstack 深度调研：人工确认环节、测试流程、使用说明与 LDVH 对比

> 创建日期：2026-06-05
> 定位：对 Gstack 项目的代码级深度调研，覆盖人工确认环节、测试流程、使用说明、LDVH 对比和社区口碑
> 调研边界：不直接构成强制规则；结论进入正式规范或 ADR 后才成为稳定执行依据
> 代码调研来源：`/Users/dmh2002/trae_projects/gstack`（完整代码库）
> 上位参考：`specs/evals/25-LDVH全盘确认与核心吸收建议.md`

---

## 1. 本文解决的问题

本文沉淀对 Gstack 项目的四维度深度调研结论，作为 LDVH 后续产品化决策的事实基础：

1. Gstack 在哪些环节需要人确认——理解 Gstack 的 Human Gate 分布和设计逻辑
2. Gstack 的测试流程——理解 Gstack 如何组织 QA、Review、Ship 的质量闭环
3. Gstack 的详尽使用说明——理解 Gstack 的完整工作流和操作方法
4. LDVH 与 Gstack 的区别——理解两者在理念、架构、治理、安全模型上的根本差异
5. Gstack 的社区真实口碑——理解外部用户对 Gstack 的真实评价和已知问题

---

## 2. Gstack 人工确认环节分析

### 2.1 Gstack Human Gate 总览

Gstack 的人工确认机制通过 Claude Code 的 `AskUserQuestion` 工具实现。与 LDVH 的 Human Gate 不同，Gstack 的确认点更分散、更轻量，且大量确认点服务于"偏好选择"而非"治理纪律"。

Gstack 的人工确认可分为四类：

| 类型 | 说明 | 典型场景 |
|------|------|----------|
| **偏好选择** | 让用户在多个方案中选择 | CEO Review 的范围模式选择、设计风格偏好 |
| **安全护栏** | 阻止潜在危险操作 | `/careful` 拦截 rm -rf、force-push 等 |
| **流程门禁** | 阶段完成前的确认 | `/ship` 发布前审查、`/spec` 质量门禁 |
| **首次配置** | 一次性初始化确认 | 遥测选择、Skill 路由注入、GBrain 信任策略 |

### 2.2 各 Skill 的人工确认点

#### 2.2.1 首次运行确认（Preamble 阶段）

每个 Skill 启动时自动执行的 Preamble 包含多个首次确认：

1. **遥测选择**：首次运行时询问是否共享匿名使用数据（A: 推荐/B: 匿名/C: 关闭）
2. **主动建议开关**：是否允许 Gstack 主动推荐 Skill（A: 开启/B: 关闭）
3. **Skill 路由注入**：是否向项目 CLAUDE.md 添加路由规则（A: 添加/B: 拒绝）
4. **Vendoring 迁移警告**：检测到 vendored 安装时建议迁移到 team mode
5. **写作风格选择**：V1 简化风格 vs V0 简洁风格
6. **Artifacts 同步模式**：全量/仅产物/关闭
7. **功能发现**：Continuous checkpoint、Model overlay 等新功能提示

**关键发现**：Gstack 的 Preamble 确认点数量多（7+），但每个都是一次性确认（通过 marker 文件去重），且在 spawned session（OpenClaw 等编排器）中自动选择推荐选项，不阻塞自动化流程。

#### 2.2.2 `/plan-ceo-review` — CEO 审查

- **范围模式选择**：4 种模式——Expansion（扩展）、Selective Expansion（选择性扩展）、Hold Scope（保持范围）、Reduction（缩减）
- **每个前提挑战**：对每个被挑战的前提，用户需同意/不同意/调整
- **实现方案选择**：3 种实现方案 + 工作量估算
- **最终推荐确认**：是否接受推荐方案

#### 2.2.3 `/plan-eng-review` — 工程审查

- **架构决策确认**：关键架构选择需用户确认
- **测试计划确认**：生成的测试矩阵需用户审查

#### 2.2.4 `/plan-design-review` — 设计审查

- **交互式设计选择**：每个设计维度逐一 AskUserQuestion，0-10 评分后询问是否采纳改进建议
- 这是 Gstack 中交互密度最高的 Skill

#### 2.2.5 `/review` — 代码审查

- **AUTO-FIXED vs ASK 分类**：审查发现的问题分为两类
  - AUTO-FIXED：明显问题自动修复，无需确认
  - ASK：需要用户判断的问题，通过 AskUserQuestion 确认
- **范围漂移检测**：检测到 scope drift 时暂停，询问是否继续

#### 2.2.6 `/qa` — QA 测试

- **Bug 修复确认**：发现 bug 后，修复方案需确认
- **认证信息**：需要用户提供测试凭证（通过环境变量）
- **测试框架选择**：检测到无测试框架时，询问是否引导安装

#### 2.2.7 `/ship` — 发布

- **预飞行检查**：发布前展示所有检查结果，需确认
- **版本提升级别**：MINOR/MAJOR/PATCH 选择
- **测试覆盖审查**：展示测试增量，需确认
- **PR 创建确认**：最终 PR body 展示后确认

#### 2.2.8 `/spec` — 规格编写

- **五阶段门禁**：Why → Scope → Technical → Draft → Quality Gate
- **Quality Gate**：Codex 评分低于 7/10 时阻塞，需用户决定是否继续
- **Secret 检测**：发现敏感信息时阻塞

#### 2.2.9 `/careful` — 安全护栏

- **破坏性命令拦截**：检测到 rm -rf、DROP TABLE、force-push、git reset --hard 等命令时暂停并要求确认
- 用户可选择覆盖（override）任何警告

#### 2.2.10 `/investigate` — 调试

- **铁律门禁**：不允许未经调查就修复——3 次修复失败后必须暂停
- **模块冻结**：自动 `/freeze` 到正在调查的模块

#### 2.2.11 `/retro` — 复盘

- **焦点领域选择**：用户选择复盘关注点
- **改进计划确认**：生成的改进建议需确认

#### 2.2.12 `/design-shotgun` — 设计探索

- **变体选择**：每轮 4-6 个变体中用户选择偏好
- **反馈循环**：用户可提供文字反馈（"更多留白""更大标题"等）

### 2.3 Gstack Human Gate 的设计特点

1. **偏好驱动而非纪律驱动**：Gstack 的确认点主要服务于"让用户表达偏好"，而非"强制治理纪律"。用户始终可以选择跳过或覆盖。
2. **推荐选项明确**：每个 AskUserQuestion 都标注 `(recommended)` 选项，降低决策负担。
3. **自动化友好**：spawned session 自动选择推荐选项，不阻塞 OpenClaw 等编排器。
4. **无状态持久**：确认结果不写入 Git 事实源，仅通过本地 marker 文件（`~/.gstack/`）去重。
5. **安全护栏可选**：`/careful`、`/freeze`、`/guard` 是可选工具，默认不开启。

### 2.4 与 LDVH Human Gate 的关键差异

| 维度 | Gstack | LDVH |
|------|--------|------|
| 驱动力 | 偏好选择 | 治理纪律 |
| 持久化 | 本地 marker 文件 | Git 事实源 + 状态机 |
| 可追溯性 | 无（本地文件，不入 Git） | 有（YAML 状态、Change 记录） |
| 强制性 | 可覆盖、可跳过 | 状态机强制，不可绕过 |
| 自动化兼容 | spawned session 自动选推荐 | 需显式 Human Gate 确认 |
| 覆盖范围 | 所有 Skill 内嵌 | 仅关键状态流转和写入 |

---

## 3. Gstack 测试流程分析

### 3.1 Gstack 测试体系总览

Gstack 的测试分为三个层次：

| 层次 | 内容 | 成本 | 速度 |
|------|------|------|------|
| Tier 1 — 静态验证 | 解析 SKILL.md 中的 `$B` 命令，对照命令注册表验证 | 免费 | <5s |
| Tier 2 — E2E 测试 | 通过 `claude -p` 启动真实 Claude 会话，运行 Skill，检查错误 | ~$3.85/次 | ~20min |
| Tier 3 — LLM 评判 | Sonnet 对文档的清晰度/完整性/可操作性评分 | ~$0.15/次 | ~30s |

Tier 1 在每次 `bun test` 时自动运行。Tier 2+3 需设置 `EVALS=1` 环境变量。

### 3.2 测试基础设施

#### 3.2.1 Session Runner

E2E 测试通过 `test/helpers/session-runner.ts` 实现：

1. 将 prompt 写入临时文件（避免 shell 转义问题）
2. 启动 `sh -c 'cat prompt | claude -p --output-format stream-json --verbose'`
3. 流式读取 NDJSON 输出
4. 与可配置超时竞争
5. 将完整 NDJSON 转录解析为结构化结果

#### 3.2.2 Eval Store

`EvalCollector` 累积测试结果，两种写入方式：

1. **增量**：`savePartial()` 每个测试后写入 `_partial-e2e.json`（原子写入：先写 `.tmp`，再 `fs.renameSync`）
2. **最终**：`finalize()` 写入带时间戳的 eval 文件

#### 3.2.3 可观测性

所有可观测性 I/O 包裹在 try/catch 中——写入失败不会导致测试失败。测试本身是真相来源，可观测性是尽力而为。

### 3.3 浏览器测试（browse 模块）

browse 模块有独立的测试体系，是最密集的测试区域：

| 测试类型 | 文件数 | 覆盖范围 |
|----------|--------|----------|
| 单元测试 | 30+ | 命令解析、配置、安全、Cookie、代理等 |
| E2E 测试 | 10+ | 完整浏览器交互流程 |
| 安全测试 | 8+ | 对抗性安全、注入检测、审计等 |
| 集成测试 | 5+ | 侧边栏、标签页隔离、SSE 等 |

### 3.4 `/qa` Skill 的测试流程

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

### 3.5 `/review` Skill 的审查流程

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

### 3.6 `/ship` Skill 的发布流程

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

### 3.7 测试流程的关键设计

1. **测试框架自动引导**：`/ship` 和 `/qa` 检测到无测试框架时，自动引导安装（Jest/Vitest/pytest 等）
2. **回归测试自动生成**：每个 `/qa` bug 修复自动生成回归测试
3. **100% 测试覆盖目标**：Gstack 明确追求 100% 测试覆盖率
4. **跨模型验证**：`/codex` 提供独立的 OpenAI Codex 审查，与 Claude 审查交叉验证
5. **真实验证优先**：`/qa` 使用真实浏览器（Chromium daemon）验证，而非静态分析

---

## 4. Gstack 详尽使用说明

### 4.1 安装

**前置条件**：Claude Code、Git、Bun v1.0+、Node.js（仅 Windows）

**安装命令**（在 Claude Code 中粘贴）：

```bash
git clone --single-branch --depth 1 https://github.com/garrytan/gstack.git ~/.claude/skills/gstack && cd ~/.claude/skills/gstack && ./setup
```

**Team Mode**（推荐，自动更新）：

```bash
(cd ~/.claude/skills/gstack && ./setup --team) && ~/.claude/skills/gstack/bin/gstack-team-init required && git add .claude/ CLAUDE.md && git commit -m "require gstack for AI-assisted work"
```

### 4.2 核心工作流

Gstack 的核心工作流遵循 **Think → Plan → Build → Review → Test → Ship → Reflect** 生命周期：

```
/office-hours → /plan-ceo-review → /plan-eng-review → [编码] → /review → /qa → /ship → /retro
```

每个 Skill 的输出成为下一个 Skill 的输入，形成产物连续交接。

### 4.3 完整 Skill 清单与用途

#### 4.3.1 Think 阶段

| Skill | 角色 | 用途 |
|-------|------|------|
| `/office-hours` | YC Office Hours | 6 个强制问题重构产品思路，生成设计文档 |
| `/investigate` | 调试员 | 系统化根因调试，铁律：不调查不修复 |

#### 4.3.2 Plan 阶段

| Skill | 角色 | 用途 |
|-------|------|------|
| `/plan-ceo-review` | CEO/创始人 | 4 种范围模式审查产品方向 |
| `/plan-eng-review` | 工程经理 | 锁定架构、数据流、边界情况、测试计划 |
| `/plan-design-review` | 高级设计师 | 0-10 评分每个设计维度，交互式改进 |
| `/plan-devex-review` | DX 负责人 | 开发者体验审查，TTHW 基准 |
| `/autoplan` | 审查流水线 | 一键运行 CEO → 设计 → 工程审查 |
| `/spec` | 规格作者 | 5 阶段将模糊意图转为精确规格 |

#### 4.3.3 Build 阶段

| Skill | 角色 | 用途 |
|-------|------|------|
| `/design-consultation` | 设计伙伴 | 从零构建设计系统 |
| `/design-shotgun` | 设计探索者 | 4-6 个 AI 变体 + 比较面板 + 反馈循环 |
| `/design-html` | 设计工程师 | 变体 → 生产 HTML（Pretext 布局，30KB，零依赖） |
| `/design-review` | 写代码的设计师 | 审查 + 修复，原子提交，前后截图 |

#### 4.3.4 Review 阶段

| Skill | 角色 | 用途 |
|-------|------|------|
| `/review` | 工程主管 | 预着陆审查，AUTO-FIXED + ASK 分类 |
| `/codex` | 第二意见 | OpenAI Codex 独立审查，跨模型交叉验证 |
| `/cso` | 安全官 | OWASP Top 10 + STRIDE 威胁建模 |
| `/devex-review` | DX 测试员 | 实际测试 onboarding 流程 |

#### 4.3.5 Test 阶段

| Skill | 角色 | 用途 |
|-------|------|------|
| `/qa` | QA 负责人 | 真实浏览器测试，发现 → 修复 → 回归 → 验证 |
| `/qa-only` | QA 报告员 | 只报告不修复 |
| `/browse` | QA 工程师 | 持久无头 Chromium，~100ms/命令 |
| `/benchmark` | 性能工程师 | 页面加载、Core Web Vitals、资源大小基准 |

#### 4.3.6 Ship 阶段

| Skill | 角色 | 用途 |
|-------|------|------|
| `/ship` | 发布工程师 | 同步 main → 测试 → 审查 → 推送 → PR |
| `/land-and-deploy` | 发布工程师 | 合并 PR → CI → 部署 → 验证生产健康 |
| `/canary` | SRE | 部署后监控循环 |
| `/document-release` | 技术写作 | 更新所有文档匹配已发布内容 |
| `/document-generate` | 文档作者 | 从零生成文档（Diataxis 框架） |

#### 4.3.7 Reflect 阶段

| Skill | 角色 | 用途 |
|-------|------|------|
| `/retro` | 工程经理 | 每周复盘，每人统计，发布连续性，测试健康趋势 |
| `/learn` | 记忆 | 管理跨会话学习，审查/搜索/修剪/导出 |

#### 4.3.8 安全与工具

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

### 4.4 浏览器操作（`/browse`）

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

### 4.5 GBrain 持久知识库

GBrain 是 Gstack 的跨会话记忆系统，4 种初始化路径：

1. **Supabase 已有 URL**：粘贴 Session Pooler URL
2. **Supabase 自动配置**：粘贴 Personal Access Token，~90s 完成
3. **PGLite 本地**：零账户零网络，~30s
4. **远程 GBrain MCP**：跨机器记忆

**信任策略**：每个仓库三级——read-write / read-only / deny

### 4.6 多宿主支持

Gstack 支持 10 种 AI 编码 Agent：

| Agent | 安装位置 |
|-------|----------|
| Claude Code | `~/.claude/skills/gstack-*/` |
| OpenAI Codex CLI | `~/.codex/skills/gstack-*/` |
| Cursor | `~/.cursor/skills/gstack-*/` |
| OpenClaw | 通过 ACP 直接使用 |
| 其他（Slate、Kiro、Hermes 等） | 各自目录 |

### 4.7 Continuous Checkpoint Mode

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

## 5. LDVH 与 Gstack 的区别对比

### 5.1 理念层对比

| 维度 | Gstack | LDVH |
|------|--------|------|
| 核心定位 | AI 编程效率工具包 | Vibe Coding 治理框架 |
| 第一服务对象 | 单人开发者（solo builder） | AI 协作者 + 人类决策者 |
| 核心隐喻 | 虚拟工程团队（23 角色） | 治理骨架（事实模型 + 状态机） |
| 价值主张 | 速度优先——810× 效率提升 | 可审计优先——每个变更可追溯 |
| 工作流哲学 | Think → Plan → Build → Review → Test → Ship → Reflect | Intent → Plan → Execute → Verify → Record → Learn |
| 规范定位 | 规范是 AI 需要记住的提示词 | 规范是可推理的权威依据 |

### 5.2 架构层对比

| 维度 | Gstack | LDVH |
|------|--------|------|
| 事实源 | `~/.gstack/` 本地隐藏目录 + GBrain | Git 文件事实源（`ldvh-base/` YAML） |
| 状态管理 | 本地 JSON/JSONL 文件，不入 Git | YAML 状态机，入 Git，可审计 |
| 持久化策略 | 本地文件 + 可选 Supabase/PGLite | Git 仓库 + PyTools 校验 |
| Skill 承载 | SKILL.md 提示词 + SKILL.md.tmpl 模板 | Trae Skill 机制 + specs 规范 |
| 浏览器能力 | 持久化 Chromium daemon（核心硬能力） | Trae Preview + RunCommand（轻量替代） |
| 多宿主 | 10 种 AI Agent 支持 | Trae Solo 原生 |
| 安全模型 | 多层防御（ML 分类器 + Canary + 双监听器） | Human Gate + 事实源边界 + 状态机 |

### 5.3 治理层对比

| 维度 | Gstack | LDVH |
|------|--------|------|
| Human Gate | 偏好选择型，可覆盖，可跳过 | 治理纪律型，状态机强制，不可绕过 |
| 变更追溯 | 无（本地文件不入 Git） | Change 记录 + Git commit + Evidence |
| 决策记录 | 无独立 ADR 机制 | ADR 状态机（proposed → accepted → superseded） |
| 状态机 | 无（Skill 无状态） | 7 个事实模型各有状态机 |
| 验证 | 浏览器真实验证 + 测试覆盖 | PyTools 校验 + Fact Validator + Evidence |
| 可审计性 | 低（本地状态，无持久化） | 高（Git 事实源，可追溯） |

### 5.4 安全模型对比

| 维度 | Gstack | LDVH |
|------|--------|------|
| 安全哲学 | 纵深防御（多层 ML + 规则 + 审计） | 治理优先（Human Gate + 事实源边界） |
| Prompt 注入防御 | 6 层防御（L1-L6） | 不直接处理（由宿主环境负责） |
| Cookie 安全 | Keychain 审批 + 内存解密 + 只读数据库 | 不涉及 |
| 网络安全 | 双监听器 + 隧道隔离 + 速率限制 | 不涉及 |
| 破坏性操作防护 | `/careful` 可选拦截 | Rules 强制约束 |
| 事实源保护 | 无（本地文件可随意修改） | 场景规则强制（不得直接编辑 `ldvh-base/`） |

### 5.5 产品化层对比

| 维度 | Gstack | LDVH |
|------|--------|------|
| 安装体验 | 一行命令，30 秒 | 规则 + Skill + Tools 组合 |
| 学习曲线 | 低（斜杠命令，推荐选项） | 中（需理解规范体系） |
| 自动化程度 | 高（自动提交、自动推送、自动发布） | 低（每步需 Human Gate） |
| 跨项目复用 | 高（team mode + auto-update） | 中（规则 + Skill 可复用，事实源项目级） |
| Web 展示 | 无（CLI 为主） | Web MVP（只读态势 + 受控操作） |
| 遥测 | 可选匿名遥测 | 无 |

### 5.6 Gstack 值得 LDVH 借鉴的

1. **流程即入口**：AI 不应先面对大量规范，而应先进入一条清晰工作流
2. **阶段即约束**：每个阶段有明确输入、输出、检查和停止条件
3. **使用即流程**：正确行为应成为 AI 默认路径
4. **产物连续交接**：前一阶段输出成为后一阶段输入
5. **AskUserQuestion decision brief**：结构化问询协议
6. **真实验证优先**：浏览器 QA、持久交互环境、可验证页面状态
7. **Skill 模板化**：SKILL.md.tmpl + 生成器避免手工漂移
8. **安全护栏可选**：`/careful`、`/freeze`、`/guard` 按需启用

### 5.7 Gstack 不应照搬的

1. `~/.gstack/` 本地隐藏目录作为事实源
2. Claude Code slash command 结构
3. 大量人格化角色 Skill 的目录形态
4. 自动遥测和自动更新默认开启
5. 自动提交、自动推送、自动发布
6. pair-agent / ngrok 远程浏览器控制
7. 复杂 ML prompt-injection classifier
8. 超长 monolithic Skill 运行时上下文
9. 以 solo-builder 速度优先替代治理纪律

---

## 6. Gstack 社区真实口碑与用户反馈

### 6.1 基本信息

- **作者**：Garry Tan（Y Combinator CEO）
- **开源时间**：2026 年 3 月 12 日
- **GitHub Star**：约 10 万
- **协议**：MIT，完全免费
- **核心定位**：Claude Code 技能包，23 个专业角色 + 8 个工具模块

### 6.2 正面评价

1. **角色分离范式被认可**：多个独立团队不约而同收敛到"基于角色的 AI 开发"模式，被认为是"趋同进化"
2. **`/plan-ceo-review` 被视为核心价值**：能像 YC 合伙人一样拷问产品方向，多位用户认为"仅凭这一个技能就足以让它属于不同类别"
3. **浏览器子系统技术含量获认可**：持久化 Chromium daemon、~100ms 延迟、Cookie 安全模型
4. **对独立开发者和小团队价值显著**：相当于"免费技术顾问团队"
5. **交互设计友好**：给出 A/B/C 选项而非开放式问题

### 6.3 负面评价

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

### 6.4 重大争议

1. **Star 数量争议**：社区质疑 Star 增速异常，HN 讨论帖被标记/降权
2. **"810 倍效率"指标之争**：社区共识为"用 KLOC 衡量生产力"是倒退
3. **AI 制造"虚假工程师幻觉"**：Mo Bitar 核心论点——大模型不是"能力放大器"，而是"自信放大器"
4. **心理健康担忧**：Garry Tan 自称每晚只睡四小时

### 6.5 与竞品对比（用户观点）

| 维度 | Gstack | Superpowers | AI-SDLC | BMAD |
|------|--------|-------------|---------|------|
| 核心理念 | 角色分工 | 强制 TDD + 工程纪律 | 完整生命周期 | 企业级方法论 |
| TDD 强制 | 否 | 是 | 审查阶段处理 | — |
| 安全设计 | 安全审查员角色 | 无专门设计 | 独立安全阶段 | — |
| 自我改进 | 否 | 否 | 是 | — |

社区建议：Superpowers + Gstack 组合使用效果最佳——Superpowers 管工程纪律，Gstack 管角色分工。

### 6.6 总结判断

Gstack 是一个被名人效应放大但确实有实质价值的工具。核心贡献：

1. 确立了"角色分离"作为 AI 协作范式
2. 浏览器守护进程是真正的工程产出
3. 编码了一个人的判断力（Garry Tan 的 YC 方法论）

局限同样明显：本质仍是提示词工程、AI 审查自己存在根本缺陷、与个人工作流深度耦合、上下文膨胀问题未解决。最适合独立开发者和小团队做技术规格审查，不适合替代真正的工程团队。

---

## 7. 对 LDVH 的启示

### 7.1 应优先吸收的经验

1. **Core Loop 应成为 AI 第一体验**：Gstack 证明了"流程即入口"比"规范即入口"更有效
2. **AskUserQuestion decision brief 是好设计**：结构化选项 + 推荐标注降低决策负担
3. **安全护栏应可选但易启用**：`/careful`、`/freeze` 模式值得 LDVH 借鉴
4. **Skill 模板化避免漂移**：SKILL.md.tmpl + 生成器思路应进入 LDVH Skill 体系
5. **真实验证能力是长期方向**：浏览器 daemon 的产品思想应保留，但实现方式应 Trae-native

### 7.2 应避免的陷阱

1. **不要把 Human Gate 变成偏好选择**：LDVH 的 Human Gate 是治理纪律，不是 UX 便利
2. **不要追求自动提交/自动发布**：Gstack 的自动化以牺牲可审计性为代价
3. **不要用本地隐藏目录做事实源**：`~/.gstack/` 模式不可审计、不可追溯
4. **不要让 AI 审查自己**：Gstack 的根本缺陷，LDVH 应通过独立验证和 Evidence 避免
5. **不要忽视上下文膨胀**：Gstack 的 3-Skill 后精度下降问题，LDVH 应通过最小必要读取策略避免

---

## 8. 来源

### 8.1 代码来源

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

### 8.2 社区反馈来源

- Gstack 实测文章（今日头条多篇文章）
- GitHub Issues（238 个 Open Issues）
- Hacker News 讨论帖
- YouTube Mo Bitar 评测视频（150 万浏览）
- Reddit 社区讨论
- 与 Superpowers、AI-SDLC、BMAD 的对比文章

### 8.3 内部参考

- `specs/evals/25-LDVH全盘确认与核心吸收建议.md`
