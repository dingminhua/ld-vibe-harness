# Codex Desktop 功能调研

> 创建日期：2026-06-01
> 来源：OpenAI 官方介绍、Codex 官方文档、Tech Times、IntuitionLabs、ses-base、notai.jp、ai-revolution.co.jp、ai-reboot.io、MorphLLM、Educative、网易、lilting 等
> 定位：外部资料引用，不直接成为 LDVH 强制规则

---

## 1. 结论摘要

Codex Desktop（正式名称：Codex app / Codex Mac app / Codex Windows app）是 OpenAI 在 2026 年推出的 AI 编码代理桌面应用。它是 OpenAI 在 2025 年 4 月推出的 Codex 编码代理体系的最新前端形态，与 Codex CLI、Codex IDE 扩展（VS Code 等）共享同一执行引擎和 `config.toml` 配置。

一句话理解：

```text
Codex Desktop 不是另一个聊天客户端；
它是面向"多智能体并行 + 长时间任务 + 真实桌面操作"的智能体指挥中心。
```

核心要点：

| 维度 | 结论 |
|---|---|
| 发布日期 | 2026-02-02 推出 macOS 版；2026-03-04 推出 Windows 版；Linux 暂只支持 CLI |
| 支持平台 | macOS（Apple Silicon 优先）、Windows（Microsoft Store 分发） |
| 默认模型 | GPT-5.2-Codex（256K 上下文）；后续 2026-02 推出 GPT-5.3-Codex，2026-04 起 Pro 预览 |
| 形态 | Electron / Tauri 风格的原生桌面应用，提供 GUI、Tab/Panel 多任务 UI、实时仪表盘 |
| 核心能力 | 多智能体并行、Git Worktree 隔离、Skills 插件体系、Automations 自动化、Computer Use 桌面操作、Codex for Chrome 浏览器扩展、In-App Browser、Image Generation、Memory / Chronicle、AGENTS.md 项目指令 |
| 接入方式 | ChatGPT 账号（OAuth）或 OpenAI API Key（`OPENAI_API_KEY` 环境变量） |
| 底层生态 | 与 Codex CLI、IDE 扩展共享执行引擎与配置；同一 thread 记录与设置跨端延续 |
| 订阅与计费 | 与 ChatGPT 套餐绑定；2026-04-02 起 Business/Enterprise 改用按 token 计费；个人端保留 5 小时滚动窗口额度 |
| 典型用户群 | 个人开发者、Pro 重度用户、Enterprise 安全合规团队、独立开发者之外的"指挥多个智能体"型开发者 |

推荐理解：

```text
CLI 决定自动化与脚本能力；
Desktop 决定可视化指挥与并行协作；
IDE 扩展决定编辑器内不切换上下文；
三者共享模型、Skills、AGENTS.md、config.toml。
```

---

## 2. 产品演进时间线

Codex 体系经历三代演进，桌面应用是第三代的最新形态。

| 时间 | 事件 | 含义 |
|---|---|---|
| 2021-08 | OpenAI 发布初代 Codex 模型（GPT-3 衍生） | 支撑 GitHub Copilot、Codex API |
| 2023-03-23 | 初代 Codex API 被废弃 | 官方建议迁移到 GPT-3.5 Turbo |
| 2025-04 | OpenAI 推出"新 Codex"：云端编码代理（codex-1，基于 o3 微调） | CLI / IDE / Web 三端 |
| 2025-12 | GPT-5.2-Codex 模型发布 | 上下文 256K；Codex 整体使用量翻倍 |
| 2026-01 | 月活突破 100 万 | 编码代理走向主流 |
| 2026-02-02 | Codex Desktop 正式发布（macOS） | 多智能体并行成为旗舰场景 |
| 2026-02 | GPT-5.3-Codex 发布 | Pro 计划预览访问 |
| 2026-03-04 | Windows 版在 Microsoft Store 上线 | 50 万人等候名单 |
| 2026-04-02 | Business / Enterprise 切换为按 token 计费 | 取消"N credits / message" |
| 2026-04-09 | ChatGPT Pro $100 计划上线 | Codex 5× 限额（限时 10×） |
| 2026-04-16 | "Codex for (almost) everything"：Computer Use、In-App Browser、gpt-image-1.5、Memory、Automations、90+ 插件 | 通用桌面代理化 |
| 2026-05-07 | Codex for Chrome 扩展发布 | 操作"用户已登录"的真实 Chrome |
| 2026-05-07/08 | Codex CLI 0.129 / 0.130 | Modal Vim、`/hooks`、Goals、`codex remote-control`、Bedrock 认证 |
| 2026-05-14 | Chronicle（截图式环境记忆）正式发布 | 独立安全审计最受关注的功能 |
| 2026-05-24 | Codex 跨入 Mobile + Desktop Agent 形态 | 通过截图、键盘、鼠标跨应用操作 |

引用要点：

- macOS 版首周下载量超过 100 万。
- 2026-04 周活开发者 300 万；2026-05 周活超 400 万。
- ChatGPT 限时将 Codex 纳入 Free / Go 套餐；Plus / Pro / Business / Enterprise / Edu 全档可用，付费档 2× 限额。

---

## 3. 三大入口形态

Codex 不是单一产品，而是"同一执行引擎 + 三种前端"。

| 形态 | 定位 | 适合场景 | 核心优势 |
|---|---|---|---|
| Codex CLI（`@openai/codex`，Apache 2.0） | 终端优先 | 自动化、CI/CD、脚本、SSH 远程 | 灵活、可脚本化、非交互 `exec` 模式 |
| Codex Desktop（Mac / Windows 原生应用） | 多智能体指挥中心 | 并行任务、长时间任务、桌面级操作、跨端协调 | GUI、可视 diff、Worktree 隔离、实时仪表盘 |
| Codex IDE 扩展（VS Code、JetBrains） | 编辑器内不切上下文 | 阅读代码、内联修改、Pair Programming | 不离开编辑器；与 ChatGPT 订阅直接联动 |

三者共享：

- 同一执行引擎与同一模型体系（GPT-5.2-Codex、GPT-5.3-Codex、codex-mini）。
- 同一 `config.toml` 配置文件。
- 同一 thread（会话）记录与设置，跨端延续。
- 同一 AGENTS.md 项目指令。
- 同一 Skills 体系。
- 同一 Approval Mode / Sandbox 策略。

CLI 安装示意：

```bash
# macOS / Linux
npm install -g @openai/codex

# macOS
brew install codex

# Windows
winget install Codex -s msstore

# 验证
codex --version
```

前置依赖：

1. OpenAI API Key 或 ChatGPT Plus / Pro / Team / Enterprise 订阅。
2. Node.js 22+（macOS / Linux CLI）。
3. Git（用于读取仓库结构）。

---

## 4. 桌面应用的核心能力

Codex Desktop 不是"换个皮的聊天框"，它在产品形态上有明确创新。

### 4.1 多智能体并行（Multi-Agent Threads）

- 多个智能体同时运行在按项目（Project）整理的独立线程（Thread）中。
- 用户在不同 Thread 之间切换不丢失上下文。
- 应用内置最多约 8 个智能体并行（不同来源描述为"最多 8 个 agent 同时执行"）。
- 多个智能体可在同一代码库中同时工作而不冲突，关键机制是 Git Worktree。
- 智能体运行过程中，用户可以随时查看本机 diff、跳到编辑器手动修改、不影响本机 Git 状态。

### 4.2 Git Worktree 隔离环境

- 每个智能体在独立的代码副本（worktree）中工作。
- 主工作区不会因并行任务被污染。
- 可同时尝试多个方案，再选择合并。
- 操作完成后，提供 `Create branch here` 与 `Sync with local` 两种合并方式。
- 配合 IDE 同步，可在编辑器中打开 worktree 进行人工微调。

### 4.3 Skills（技能）插件体系

- 技能（Skill）是"指令 + 资源 + 脚本"的打包，等价于"用自然语言写的小程序 + 可选代码附件"。
- 在 Codex Desktop 中有专门管理界面：浏览开源 Skill 包（GitHub 托管）、安装、自建。
- Skills 业界标准：`agentskills.io`；OpenAI 官方提供 curated 集合，例如 `imagegen`（GPT Image 驱动）、`develop-web-game`。
- 社区示例：抓 YouTube 字幕、生成 Excalidraw 图、自动部署移动端测试包、Figma 转代码、Linear / Jira 工单管理等。
- 用户可显式指定 Skill，也可由 Codex 按任务自动套用。

### 4.4 Automations（自动化）

- 类似"自然语言 cron job"：可按日 / 周 / 触发器自动执行任务。
- 示例：每早跑测试并把结果发到 inbox；监听文件变更并分析影响范围。
- 与 Skills 组合可实现"流程化作业"，例如"每晚同步 Figma → 跑视觉回归 → 推 PR"。

### 4.5 Computer Use（桌面级操作）

- Codex Mac app 的标志性能力：Codex 拥有自己的"虚拟光标 + 键盘"，可像人一样操作 macOS 上的任意应用。
- 关键技术：截图 → 视觉识别 → 计划动作 → 执行。
- 用户焦点和光标不被夺取，Codex 在"沙箱化虚拟工作空间"中运行。
- 运行环境：Apple Silicon + macOS 14（Sonoma）以上。
- 必须授权 macOS 的"屏幕录制"与"辅助功能"两个权限。
- Windows / Linux / 移动端目前不支持 Computer Use。
- OpenAI 官方不推荐在包含敏感信息的任务上使用，建议专用 macOS 账户 + 最小权限 App Approval。

### 4.6 In-App Browser 与 Codex for Chrome

三种"浏览器操作"能力并存：

| 名称 | 能力范围 | 适用场景 |
|---|---|---|
| In-App Browser | 嵌入式浏览器会话 | 在 Codex 内部打开页面、提取信息、跑测试，不污染用户浏览器 |
| Computer Use | 操作系统级点击、键盘、屏幕识别 | 跨任意 App 自动化 |
| Codex for Chrome（2026-05-07 扩展） | 直接操作用户已登录的 Chrome | LinkedIn / Salesforce / Gmail / 内部 SaaS 自动化 |

### 4.7 Image Generation（gpt-image-1.5）

- 调用 GPT Image 1.5 在 Codex 内部生成图片。
- 与 Skills 组合可实现"从设计稿到可玩 demo"的端到端流程。
- 官方展示案例：用 `imagegen` + `develop-web-game` 一次性消耗 700 万 token 构建 3D 卡丁车游戏 Voxel Velocity。

### 4.8 Memory / Chronicle（环境记忆）

- 2026-04-20 上线 Chronicle；2026-05-14 正式版。
- 后台沙箱中的智能体周期性截屏 → OCR → 摘要为 Markdown 记忆 → 存到本机。
- 后续提问（如"接着昨天的"）可由 Codex 自动解析。
- OpenAI 自述风险：
  - 消耗速率额度快；
  - 增大 prompt injection 风险；
  - Markdown 记忆以**未加密**形式存于本机，对其他应用可见；
  - 选中帧会被送到 OpenAI 服务器处理，6 小时以上自动删除。
- 建议：会议前 / 浏览敏感信息前暂停 Chronicle。

### 4.9 内置 Git 流程

- Codex Desktop 内置：提交代码、推送到远程仓库、创建 Pull Request。
- 全流程不离开 App：diff 审阅 → 提交 → push → PR。

### 4.10 IDE 同步与编辑器内 Pairing

- 与 VS Code / JetBrains 等 IDE 配对（Pairing）后，Codex 任务可在编辑器内直接接管与编辑。
- 支持"云端执行 + 本地查看 diff"与"本地执行"两种模式，可按任务复杂度切换。
- App-server WebSocket：可与本地 CLI 形成 WebSocket 双向通信，便于自定义 IDE 或第三方工具联动。

### 4.11 AGENTS.md（项目级指令）

- 在项目根目录放 `AGENTS.md`（类似 `CLAUDE.md`），告诉 Codex 该项目的工作约定。
- 实测可显著提升任务执行精度。
- 与 OpenAI 的"AGENTS.md 开放规范"兼容，社区通用。

### 4.12 其它细节

- 语音输入（Voice）。
- Personality：可调整 Codex 的回复风格。
- 实时仪表盘：进度、Token 消耗、当前操作可视化。
- 视觉 diff：相比 CLI 的文本 diff，Desktop 提供并排 / 内联 / 折叠 diff。
- 拖拽文件 / 文件夹进对话框直接作为上下文。

---

## 5. 权限与沙箱模型

Codex 桌面应用延续 CLI 的"三档权限"模型，但在 GUI 中可视化。

| 权限模式 | 行为 | 适合 |
|---|---|---|
| Default（默认） | 可读写工作区；离开工作区或高风险操作需要弹窗确认 | 日常使用 |
| Auto Review（自动审查） | Codex 自审自批，省去人工 | 信任度高的批量任务 |
| Full Access（完全访问） | 几乎不弹确认框 | 高自动化场景，需自己承担风险 |

沙箱（Sandbox）维度：

- 沙箱化虚拟工作空间：智能体在隔离环境中运行；
- 离开工作区：默认会被拦截；
- 网络策略：可限制 Codex 出站访问范围（关键合规能力）；
- 企业部署：可接入 SAML SSO、MFA、SCIM、审计日志、自定义数据保留。

---

## 6. 模型与上下文

| 模型 | 上下文 | 定位 | 适用订阅 |
|---|---|---|---|
| GPT-5.2-Codex | 256K tokens | 桌面默认；理解精度较 GPT-4.5 提升约 40% | Plus 起 |
| GPT-5.3-Codex | 400K 输入 / 128K 输出 | 2026-02 起 Pro 预览 | Pro / Business / Enterprise |
| gpt-image-1.5 | 图像生成 | 配合 Skills | Plus 起 |
| codex-mini | 轻量 | 简单任务 | Plus 起 |

注意：模型版本与"代号"持续演化，2026 上半年的"5.2 / 5.3 / 5.4"在不同来源中均有出现，应以 OpenAI 官方 `developers.openai.com/codex` 与 `help.openai.com` 实时信息为准。

---

## 7. 订阅、计费与额度

### 7.1 个人与团队订阅

| 计划 | 价格 | Codex 入口 | 关键额度 |
|---|---|---|---|
| Free / Go | $0 | 限时试用 | 极有限 |
| ChatGPT Plus | $20/月 | 全量 | 本地 45–225 messages / 5h（限时 2×） |
| ChatGPT Pro $200 | $200/月 | 全量 + 优先 | 本地 300–1500 messages / 5h |
| ChatGPT Pro $100（2026-04-09 上线） | $100/月 | 全量 | Codex 5× 限额（限时 10×，至 2026-05-31） |
| ChatGPT Business | $20 / $25 / $30 per user | 全量 + 大 VM | 与 Plus 相当，附加安全合规 |
| ChatGPT Enterprise | 自定义 | 优先 + 信用池 | 无固定 5h 限额，按额度计 |

### 7.2 5 小时滚动窗口

- 不用月结，用 5h 滚动窗口：从首条消息起 5h 后重置。
- 复杂 refactor 一次就可能用完 Plus 窗口。
- 2025-11-02 曾出现 5h 配额异常消耗 bug，OpenAI 给予 $200 信用补偿。

### 7.3 按 Token 计费（2026-04-02 起，Business / Enterprise）

- 取消"N credits / message"旧模型；
- 改按模型 / 1M tokens 计费；
- 新增 Codex-only 座位：纯使用量计费，无 rate limit；
- 新工作区每用户赠送 $100、最高 $500 信用（截至 2026-04-30）；
- Business 座位价从 $25 降至 $20。

### 7.4 API Key 计费

- `OPENAI_API_KEY` 环境变量；
- 按 token 计费：输入约 $1.50 / 1M tokens，输出约 $6 / 1M tokens（codex-mini）；
- 75% prompt caching 折扣；
- 月用量 < 10–15 次会话时，API 比订阅更划算。

### 7.5 Codex-only 座位（Business / Enterprise）

- 纯按用量计费，无固定 rate limit；
- 适合：开发人员多于 ChatGPT 全家桶需求时；
- 与"GitHub Copilot Premium Requests"结构类似但模型更细。

---

## 8. 典型使用模式

### 8.1 自动化案例（OpenAI 官方展示）

任务：构建 3D 卡丁车游戏 Voxel Velocity。

```text
提示（整理后）：
Implement Voxel Velocity as a 3D voxel kart racer using Three.js,
with exactly one mode: Single Race (always 3 laps, 1 human vs 7 CPU,
and all 8 tracks available immediately with no progression).
Build a minimal pre-race flow with only:
Track (8), Character (8), Difficulty (Chill/Standard/Mean),
optional Mirror Mode, optional Allow Clones, and Start Race.
```

执行：

- 使用 Skills：`imagegen`（GPT Image 1.5）+ `develop-web-game`；
- 单条提示、消耗 700 万 token；
- Codex 同时扮演设计师 / 开发者 / QA，自己玩自己验证。

### 8.2 个人开发者典型流

1. 启动 App，登录 ChatGPT；
2. 选择本地项目文件夹作为工作区；
3. 选择权限模式（建议新手选 Auto Review）；
4. 用自然语言下达任务："帮我分析这个文件夹的空间占用，找出 > 500MB 的大文件，给出清理建议"；
5. Codex 跑命令 → 生成报告 → 用户确认 → 执行清理；
6. 项目内：要求"在此分支加单元测试并创建 PR"，Codex 走完 Worktree → 改 → diff → 提 PR。

### 8.3 团队 / 企业典型流

- ChatGPT Business 提供 SAML SSO、MFA、不用客户数据训练模型；
- ChatGPT Enterprise 提供 SCIM、EKM、RBAC、审计、自定义数据保留；
- 配合 Codex-only 座位按用量计费；
- 通过网络沙箱限制 Codex 出站；
- 在项目根目录维护 `AGENTS.md` 写明团队规范。

### 8.4 与 Claude Code、Gemini CLI 对比

| 维度 | Codex Desktop / CLI | Claude Code | Gemini CLI |
|---|---|---|---|
| 默认模型 | GPT-5.2-Codex / 5.3-Codex | Claude Opus 4.x | Gemini 2.5 Pro |
| 上下文 | 256K–400K | 最高 1M（带 Compaction） | 1M |
| 形态 | Desktop + CLI + IDE | CLI + IDE 插件 | CLI |
| 核心卖点 | 多智能体并行 + Worktree + Skills + Computer Use | Agentic 自主多文件编辑 + PR 管理 | ReAct Agent + Google 搜索 + MCP |
| TerminalBench 2.0 基准 | 77.3% | 65.4% | — |
| SWE-Bench（bug fix） | — | 80.8% | — |
| Computer Use | ✅（Mac 限定） | ✅ | ❌ |
| 跨平台 | macOS / Windows（Desktop）；Linux 仅 CLI | macOS / Linux / Windows | macOS / Linux / Windows |
| 开源 | CLI Apache 2.0 | 商业 | Apache 2.0 |

---

## 9. 安全、合规与风险

Codex Desktop 引入的"真实桌面操作"显著拉高了攻击面，需重点关注：

| 风险 | 触发场景 | 缓解建议 |
|---|---|---|
| Prompt Injection（Chronicle） | 浏览含隐藏指令的网页，Codex 后续读取记忆时被劫持 | 会议前 / 处理敏感信息前暂停 Chronicle |
| 本地未加密记忆泄露 | Markdown 记忆存于本机，其他应用可读 | 不要在工作设备启用，或使用专用账户 |
| Computer Use 误操作 | Agent 误点 / 误输入 | 用专用账户 + Auto Review 模式 + 最小权限 |
| 第三方 Skills 不可信 | 90+ 插件来源不一 | 只装来自 OpenAI 官方 curated 或可信社区的 Skill |
| 数据用于训练 | 默认 ChatGPT 套餐会用于训练 | Business / Enterprise 关闭"数据训练" |
| 大量 token 消耗 | 5h 窗口很快耗尽 | 复杂任务用 Pro 计划；监控 token |

合规优势：

- Business / Enterprise：SOC 2 Type 2、CSA STAR、GDPR、CCPA。
- Enterprise：数据驻留可指定 10 个区域。
- Enterprise：SCIM、EKM、RBAC、审计日志。
- 默认不训练：Business / Enterprise。

---

## 10. 对 LDVH 的启发（参考）

虽然 refs 仅作外部资料记录，但以下几点与 LDVH 多角色 / 多 agent 思路相关：

| LDVH 概念 | Codex Desktop 实践 | 启发 |
|---|---|---|
| 多角色思考（`specs/51-...`） | 多个 Agent 并行 + Skills 切换角色 | 把"角色"显式建模为可加载的 Skill 集合 |
| Human Gate | 权限模式三档（Default / Auto Review / Full Access） | Human Gate 在 Codex 体系内有清晰颗粒度，可作类比 |
| L0/L1/L2 规则分层 | `AGENTS.md` 项目级 + 桌面 / CLI / IDE 全局默认 | 项目级规则 + 全局默认 = 分层规则 |
| Skills vs Agent | Skills = 自然语言 + 脚本包；Agent = 调度 + 工具组合 | Skills 与 Agent 在 Codex 中是组合关系，可借鉴 |
| 事实模型边界 | Worktree 隔离 = 智能体副本 | 隔离 = 防污染主线；事实模型有 worktree 隐喻 |
| 压缩保护 | Codex CLI 共享 `config.toml` | 共享配置是"压缩保护"的一种实现 |

注意：以上仅为"参考启发"，refs 文件不构成 LDVH 强制规则；规则变更须经 `specs/11.01-Rules机制规范.md` §7 审计。

---

## 11. 待观察与未决问题

| 主题 | 待观察 |
|---|---|
| 模型版本 | GPT-5.2 / 5.3 / 5.4 命名在不同来源中并存，需以 `developers.openai.com/codex` 为准 |
| Pro $100 5× / 10× 限时 | 2026-05-31 后的实际限额未确认 |
| Linux 桌面 | 截至 2026-05 仅支持 Linux CLI，无原生 Linux 桌面应用 |
| 移动端 | Tech Times 提到"runs on mobile"，但 Codex Desktop 移动端形态未在官方渠道明确定义 |
| Codex for Chrome 隐私 | 已登录 Chrome 由 Agent 操作等同于完全接管账户，需关注官方后续对敏感站点的策略 |
| Chronicle 默认状态 | 是否默认开启，文档存在不一致 |
| Skills 开放标准 | `agentskills.io` 与 MCP 之间的关系尚在演化 |

---

## 12. 参考链接

- OpenAI：介绍 Codex 应用程式（macOS / Windows）
  - https://openai.com/zh-Hant/index/introducing-the-codex-app/
- OpenAI Developers Codex App
  - https://developers.openai.com/codex/app
- OpenAI Codex Memories / Chronicle
  - https://developers.openai.com/codex/memories/chronicle
- OpenAI Codex Rate Card
  - https://help.openai.com/en/articles/20001106-codex-rate-card
- Tech Times：OpenAI Codex Becomes Desktop Agent
  - https://www.techtimes.com/articles/317074/20260524/openai-codex-becomes-desktop-agent-controls-mac-apps-watches-screen-runs-mobile.htm
- IntuitionLabs：OpenAI Codex App: A Guide to Multi-Agent AI Coding
  - https://intuitionlabs.ai/pdfs/openai-codex-app-a-guide-to-multi-agent-ai-coding.pdf
- IntuitionLabs：Claude Code vs Codex vs Gemini CLI
  - https://intuitionlabs.ai/pdfs/claude-code-vs-codex-vs-gemini-cli-feature-comparison.pdf
- ses-base：Codex デスクトップアプリの使い方と活用術【2026 年版】
  - https://ses-base.com/articles/openai-codex-cli-desktop-app-guide/
- notai.jp：OpenAI Codex アプリ版完全ガイド
  - https://notai.jp/blog/openai-codex-app/
- ai-revolution.co.jp：OpenAI Codex Computer Use 使い方完全ガイド
  - https://ai-revolution.co.jp/media/openai-codex-computer-use/
- ai-reboot.io：Codex Windows 版の使い方完全ガイド
  - https://ai-reboot.io/academy/blog/codex-windows-guide
- MorphLLM：Codex Pricing (2026)
  - https://www.morphllm.com/codex-pricing
- lilting：OpenAI Codex switched to per-token pricing
  - https://lilting.ch/en/articles/openai-codex-token-based-pricing-rate-card
- Educative：Setting Up Codex: CLI, Desktop App, and IDE Extension
  - https://www.educative.io/courses/mastering-openai-codex-for-agentic-coding/setting-up-codex-cli-desktop-app-and-ide-extension
- 网易：Codex 零基础实战教程（程序员鱼皮）
  - https://www.163.com/dy/article/KTFLQCPL0556DREL.html
- Qiita：ChatGPT Pro $100 プラン入門
  - https://qiita.com/kai_kou/items/9407ee914d80d5eb6c48
- Agent Skills（开放标准）
  - https://agentskills.io/home
- OpenAI Codex on GitHub
  - https://github.com/openai/codex
- Codex Skills Curated（OpenAI 官方）
  - https://github.com/openai/skills/blob/main/skills/.curated/

---

> 备注：本文为外部资料调研快照，Codex 体系处于快速迭代期（5–7 天一次小版本、约 1 个月一次桌面端大版本）。任何对外决策应回到 OpenAI 官方文档与 `help.openai.com` 的最新信息。
