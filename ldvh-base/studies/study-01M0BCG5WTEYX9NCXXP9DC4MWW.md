---
title: 跨 AI 编码产品 Hook/生命周期事件支持度调研
status: active
report_kind: external_research
research_intent: 调研主流 AI 编码产品对宿主生命周期 Hook 的支持程度，评估 LDVH Stop gate 跨环境接入的可行性与路径。
research_question: Claude Code、Codex、Pi、Cindy、DSH、Trae、WorkBuddy 七个产品对 AI 生命周期 Hook（Stop/PreToolUse/PostToolUse/会话事件）的支持程度如何？LDVH 的 Stop gate 跨环境接入路径是什么？
abstract: 基于仓库内已有平台机制事实附件（09.Att.03/04/05）与多轮协同 Worker 调研（Cindy 从 Ghost 手册、Pi 从源码仓库、Trae/WorkBuddy/DSH 从联网搜索 + npm registry），系统评估七个产品的 Hook 支持度。核心发现：LDVH 的 Stop gate 只有一个真正业务驱动的 hook 需求（AI 停止前拦截纠偏）；Git Gate 跨全部产品零适配（Git 原生）；DSH 通过 dsh-bridges 插件可桥接 Claude Code hooks；Pi 通过 TS 扩展可实现等价功能。
recommendation_summary: LDVH 的跨环境 hook 策略应分为两层：Git Gate + Skill 路由（零 hook 适配，覆盖全部产品）作为最小接入层；Stop gate 按环境能力渐进增强（Claude Code 原生 → Codex 原生 → Pi TS 扩展 → DSH 经 dsh-bridges 桥接 → Cindy soft-warning → 其余靠 AI 自律）。维护模式与 Skill 一致：一份核心逻辑 + 多环境薄 wrapper。
object_id: study-01M0BCG5WTEYX9NCXXP9DC4MWW
object_uid: 01a016c8-179a-77ba-9ab3-bdb25ac2539c
fact_type_key: study
created_at: '2026-08-19T03:30:00+08:00'
updated_at: '2026-08-19T03:30:00+08:00'
urls:
- ref: https://github.com/yhlooo/dsh-bridges
  title: yhlooo/dsh-bridges
  summary: DSH 的第三方插件，将 Claude Code/Codex/Pi/Gemini CLI/Cursor 的 Skills、Memory、Hooks、Permissions 桥接到 DSH，无需迁移。
- ref: https://www.npmjs.com/package/dsh-bridges
  title: "npm: dsh-bridges"
  summary: dsh-bridges 的 npm 包，v0.2.3，支持 Claude Code/Codex/CodeBuddy Code/Gemini CLI/Cursor 的 Hooks 桥接。
- ref: https://github.com/earendil-works/pi
  title: Pi Agent Harness 源码仓库
  summary: Pi 的 TypeScript 扩展系统源码，含完整生命周期事件定义（agent_end/tool_call/session_shutdown 等）。
- ref: https://github.com/deepseek-ai/dsh
  title: DeepSeek Harness 源码仓库
  summary: DSH 主仓库，@deepseek-ai/dsh，v1.0.3，描述为"A Smart Shell for LLMs"，未发现公开的插件/扩展系统文档。
change_log:
- signature:
    product_name: Cindy
    model_name: kimi-k3
  at: '2026-08-19T03:30:00+08:00'
  summary: 初次创建 Study
---
## 研究问题

Claude Code、Codex、Pi、Cindy、DSH、Trae、WorkBuddy 七个产品对 AI 生命周期 Hook（Stop/PreToolUse/PostToolUse/会话事件）的支持程度如何？LDVH 的 Stop gate 跨环境接入路径是什么？

## 输入与边界

- 范围：七个主流 AI 编码产品的宿主 Hook/lifecycle 事件支持度
- 不覆盖：模型能力、UI 体验、价格、非 hook 的扩展机制细节
- 证据来源：仓库内 09.Att.03/04/05 旧卡；协同 Worker 调研 Cindy（Ghost 手册第一手核实）、Pi（源码仓库逐文件核实）、Trae/WorkBuddy/DSH（联网搜索）；dsh-bridges npm registry 直接抓取
- 时间：2026-08-19

## 关键发现

### 1. LDVH 真正需要的 Hook 只有一个：Stop gate

从规范 09 SS5.7-5.8 和业务流程倒推，LDVH 依赖的宿主 hook 只有两类：
- Git commit-msg（必选，但 Git 原生，零宿主适配）
- 宿主 Stop 事件（可选但有价值，controller_owned 阶段的机械保障）

PreToolUse/PostToolUse 被 09 SS5.1 明确禁止作为通用工具拦截层。

### 2. 七个产品的 Hook 支持度矩阵

| 产品 | Stop hook (block) | PreToolUse | Skill | Git Gate | 配置方式 |
|---|---|---|---|---|---|
| Claude Code | 原生 block | 原生 block | ~/.claude/skills/ | 天然 | JSON 声明 |
| Codex | 原生 block | approve/reject | 未确认 | 天然 | JSON 声明 |
| Pi | TS 扩展 block | TS 扩展 block | Agent Skills 标准 | 天然 | TypeScript 编程式 |
| Cindy | 无 block | 无 | ~/.agents/skills/ | 天然 | Ghost 插件 subscribe |
| DSH | 原生无；经 dsh-bridges 可桥接 | 同左 | .dsh/skills/ 多根 | 天然 | 需装 dsh-bridges |
| Trae | 无 | 无 | .trae/rules/ | 天然 | 无 hook 机制 |
| WorkBuddy | 未发现 | 未发现 | 未确认 | 天然 | 未知 |

### 3. dsh-bridges：DSH 的 hook 桥接方案

dsh-bridges（v0.2.3）将 Claude Code/Codex/Gemini CLI/Cursor 的 Hooks 桥接到 DSH。安装方式：dsh plugin add dsh-bridges。DSH 环境下 LDVH 的 Stop gate 不需要额外适配。

### 4. Cindy 是上层 harness，不是独立引擎

Cindy 可挂载 Claude Code/Codex/Pi 等 agent。Stop gate 在 agent 层生效，不依赖 Cindy 自身的 Ghost 插件机制。

### 5. Hook 适配层维护模式与 Skill 一致

一份核心逻辑（code/ldvh/hooks/workcase_stop.py）+ 多环境薄 wrapper（.claude/hooks/、.codex/hooks/、.pi/extensions/）。

## 建议

1. **LDVH 跨环境 hook 策略分两层**：Git Gate + Skill 路由（零 hook 适配，覆盖全部产品）作为最小接入层；Stop gate 按环境能力渐进增强
2. **Stop gate 接入优先级**：Claude Code 原生 → Codex 原生 → Pi TS 扩展 → DSH 经 dsh-bridges → Cindy soft-warning → 其余靠 AI 自律
3. **Pi 扩展待建**：需编写 .pi/extensions/ldvh-stop.ts，把 stdin/stdout 协议桥接到 Pi 的 agent_end + event.block() API
4. **WorkBuddy/Trae 不做 Stop gate 适配**：原因不是技术缺陷，而是它们没有 agentic loop 中的停止点概念

## 后续分流

- Pi 扩展实现：需实际编写 .pi/extensions/ldvh-stop.ts 并在 Pi 环境测试
- dsh-bridges 实际验证：需在 DSH 环境安装 dsh-bridges 并验证 Stop gate 桥接效果
- Codex 完整事件列表：需安装 Codex CLI 实际确认 PreToolUse/PostToolUse/SessionStart
- WorkBuddy 官方文档：需 Human 补充外部权威源确认 hook 能力
- 本调研结论可作为 09.Att 新附件的输入

