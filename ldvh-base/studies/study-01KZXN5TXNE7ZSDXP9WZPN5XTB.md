---
title: OpenAI Codex 子 Agent、工作树与协作实践调研
status: retired
disposition_summary: 已按 v3 基线决定重新研究；本旧 v4 短报告不再作为当前研究入口，外部资料、发现与后续启发须在新 Study 中重新读取和表达。
research_question: OpenAI Codex 官方能力如何组织子 Agent、隔离工作树、非交互执行和 App Server 集成，哪些边界可供 LDVH 参考？
abstract: 调研 Codex 官方 Subagents、Worktrees、Non-interactive mode 与 App Server 文档。共同模式是并行的专长 Agent、隔离工作目录和机器可读事件/集成面；这些是能力边界与实现参考，不构成 LDVH 必须复制的产品行为。
object_id: study-01KZXN5TXNE7ZSDXP9WZPN5XTB
object_uid: 019ffb52-ebb5-71ff-96f6-c9e7ed52f74b
fact_type_key: study
created_at: '2026-07-19T11:17:40.443524+08:00'
updated_at: '2026-08-13T15:03:57Z'
urls:
- ref: https://developers.openai.com/codex/subagents
  title: developers.openai.com/codex/subagents
  summary: 曾用于旧研究的 Codex 子 Agent 文档；不单独证明 LDVH 的角色协作设计。
- ref: https://developers.openai.com/codex/app/worktrees
  title: developers.openai.com/codex/app/worktrees
  summary: 曾用于旧研究的 Codex 工作树文档；不单独证明本项目的工作区隔离行为。
- ref: https://developers.openai.com/codex/noninteractive
  title: developers.openai.com/codex/noninteractive
  summary: 曾用于旧研究的 Codex 非交互入口文档；不单独支持当前自动化方案。
- ref: https://developers.openai.com/codex/app-server
  title: developers.openai.com/codex/app-server
  summary: 曾用于旧研究的 Codex App Server 文档；不单独支持当前集成边界。
change_log:
- signature:
    product_name: Cindy
    model_name: gpt-5
    agent_runtime_name: codex
  at: '2026-08-13T14:03:13.445133Z'
  summary: 为历史事实对象补齐权威 object_uid，并将同项目 legacy 关系目标改写为 object_uid。
- signature:
    product_name: Cindy
    model_name: gpt-5
    agent_runtime_name: codex
  at: '2026-08-13T15:03:57Z'
  summary: 将事实对象物理定位符迁移为完整 UUIDv7 的 Crockford Base32 编码。
---

## 研究问题

OpenAI Codex 官方能力如何组织子 Agent、隔离工作树、非交互执行和 App Server 集成，哪些边界可供 LDVH 参考？
## 输入与边界

本报告读取并对照了以下外部公开资料：https://developers.openai.com/codex/subagents、https://developers.openai.com/codex/app/worktrees、https://developers.openai.com/codex/noninteractive、https://developers.openai.com/codex/app-server。外部资料条目记录在 urls 中；本报告只陈述页面可直接支持的内容，并将 LDVH 适用性与外部事实分开。
## 关键发现

Subagents 文档描述可并行启动专门 Agent 并汇总结果，也支持定义自定义 Agent。Worktrees 文档把隔离工作目录作为并行变更的边界。Non-interactive 与 App Server 文档提供面向自动化或宿主集成的机器交互入口。官方能力仍要求调用方自行管理权限、结果验证、冲突合并与 Human 审核。
### 旧研究的限制

可吸收的稳定原则是“角色专长、工作区隔离、结构化回传、调用方验证”四件事，而不是把 Agent 数量、UI 或某个命令名写成 LDVH 规范。限制包括文档覆盖的是 Codex 产品能力，不能证明 LDVH 运行环境或其它 Agent 客户端具备相同实现。
## 建议

在 LDVH 中分别定义 Agent 角色契约、工作树身份契约和回传终态契约；任何跨工作树写入、合并和 Human Gate 仍由本项目规则决定。
## 后续分流

供 Spark-0010（Codex 多 Agent、工作树与角色协作治理）推进；实现性问题进入 WorkCase，不把官方示例直接当作当前 Code 行为。
