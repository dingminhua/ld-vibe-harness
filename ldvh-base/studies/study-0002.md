---
title: OpenAI Codex 子 Agent、工作树与协作实践调研
status: active
applicability: 用于 LDVH 多 Agent 角色、linked worktree、Helper/Code/Web
  接口和回传可观察性的方案比较；不改变 Git identity、Human Gate 或当前项目授权边界。
validation_summary: 已读取 developers.openai.com/codex 下四份官方入口（当前页面重定向至 ChatGPT
  Learn 文档）；未在 LDVH 中运行这些 Codex 能力，也未验证不同客户端的完全一致性。
research_question: OpenAI Codex 官方能力如何组织子 Agent、隔离工作树、非交互执行和 App Server
  集成，哪些边界可供 LDVH 参考？
abstract: 调研 Codex 官方 Subagents、Worktrees、Non-interactive mode 与 App Server
  文档。共同模式是并行的专长 Agent、隔离工作目录和机器可读事件/集成面；这些是能力边界与实现参考，不构成 LDVH 必须复制的产品行为。
object_id: study-0002
fact_type_key: study
created_at: '2026-07-19T11:17:40.443524+08:00'
updated_at: '2026-07-23T14:21:35.783731+08:00'
urls:
- ref: https://developers.openai.com/codex/subagents
  title: developers.openai.com/codex/subagents
  summary: 外部研究资料；具体支持范围与限制见本报告正文。
- ref: https://developers.openai.com/codex/app/worktrees
  title: developers.openai.com/codex/app/worktrees
  summary: 外部研究资料；具体支持范围与限制见本报告正文。
- ref: https://developers.openai.com/codex/noninteractive
  title: developers.openai.com/codex/noninteractive
  summary: 外部研究资料；具体支持范围与限制见本报告正文。
- ref: https://developers.openai.com/codex/app-server
  title: developers.openai.com/codex/app-server
  summary: 外部研究资料；具体支持范围与限制见本报告正文。
---

## 研究问题

OpenAI Codex 官方能力如何组织子 Agent、隔离工作树、非交互执行和 App Server 集成，哪些边界可供 LDVH 参考？
## 输入、方法与观察边界

本报告读取并对照了以下外部公开资料：https://developers.openai.com/codex/subagents、https://developers.openai.com/codex/app/worktrees、https://developers.openai.com/codex/noninteractive、https://developers.openai.com/codex/app-server。外部资料条目记录在 urls 中；本报告只陈述页面可直接支持的内容，并将 LDVH 适用性与外部事实分开。
## 关键发现

Subagents 文档描述可并行启动专门 Agent 并汇总结果，也支持定义自定义 Agent。Worktrees 文档把隔离工作目录作为并行变更的边界。Non-interactive 与 App Server 文档提供面向自动化或宿主集成的机器交互入口。官方能力仍要求调用方自行管理权限、结果验证、冲突合并与 Human 审核。
## 结论与限制

可吸收的稳定原则是“角色专长、工作区隔离、结构化回传、调用方验证”四件事，而不是把 Agent 数量、UI 或某个命令名写成 LDVH 规范。限制包括文档覆盖的是 Codex 产品能力，不能证明 LDVH 运行环境或其它 Agent 客户端具备相同实现。
## 建议

在 LDVH 中分别定义 Agent 角色契约、工作树身份契约和回传终态契约；任何跨工作树写入、合并和 Human Gate 仍由本项目规则决定。
## 后续分流

供 Spark-0010（Codex 多 Agent、工作树与角色协作治理）推进；实现性问题进入 WorkCase，不把官方示例直接当作当前 Code 行为。
