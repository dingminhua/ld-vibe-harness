---
title: AI 能力资产、Hook 与工程门禁行业实践调研
status: retired
disposition_summary: 已按 v3 基线决定重新研究；本旧 v4 短报告不再作为当前研究入口，外部资料、发现与后续启发须在新 Study 中重新读取和表达。
research_question: Codex Skills/Hooks、Git hooks 与 Agent guardrails 的公开文档如何区分可复用能力、生命周期自动化和强制门禁？
abstract: 调研 Codex Skills/Hooks、Git hooks 与 OpenAI Agents guardrails/HITL 文档。外部模式把技能视为可复用工作流，把 Hook 视为生命周期事件自动化，把 guardrail/HITL 视为输入输出或动作级的阻断/升级；三者职责不同，不能互称。
object_id: study-0004
object_uid: 019ffb52-ebb5-7eb4-b5d5-ceed927dd4e3
fact_type_key: study
created_at: '2026-07-19T11:17:44.511811+08:00'
updated_at: '2026-08-13T14:03:19.011031Z'
urls:
- ref: https://developers.openai.com/codex/skills
  title: developers.openai.com/codex/skills
  summary: 曾用于旧研究的 Codex Skills 文档；不单独支持本项目的能力资产准入。
- ref: https://developers.openai.com/codex/hooks
  title: developers.openai.com/codex/hooks
  summary: 曾用于旧研究的 Codex Hooks 文档；不单独支持本项目的 Hook 设计。
- ref: https://git-scm.com/docs/githooks
  title: git-scm.com/docs/githooks
  summary: 曾用于旧研究的 Git hooks 文档；不单独决定 LDVH 的门禁范围。
- ref: https://openai.github.io/openai-agents-python/guardrails/
  title: openai.github.io/openai-agents-python/guardrails/
  summary: 曾用于旧研究的 Agent guardrails 文档；不单独替代 Human Gate。
- ref: https://openai.github.io/openai-agents-python/human_in_the_loop/
  title: openai.github.io/openai-agents-python/human_in_the_loop/
  summary: 曾用于旧研究的人类介入文档；不单独决定项目授权。
change_log:
- signature:
    product_name: Cindy
    model_name: gpt-5
    agent_runtime_name: codex
  at: '2026-08-13T14:03:19.011031Z'
  summary: 为历史事实对象补齐权威 object_uid，并将同项目 legacy 关系目标改写为 object_uid。
---

## 研究问题

Codex Skills/Hooks、Git hooks 与 Agent guardrails 的公开文档如何区分可复用能力、生命周期自动化和强制门禁？
## 输入与边界

本报告读取并对照了以下外部公开资料：https://developers.openai.com/codex/skills、https://developers.openai.com/codex/hooks、https://git-scm.com/docs/githooks、https://openai.github.io/openai-agents-python/guardrails/、https://openai.github.io/openai-agents-python/human_in_the_loop/。外部资料条目记录在 urls 中；本报告只陈述页面可直接支持的内容，并将 LDVH 适用性与外部事实分开。
## 关键发现

Skills 文档强调可打包、可调用的工作流知识；Hooks 关注会话或生命周期事件触发的脚本；Git hooks 是本地 Git 事件点，适合机械检查但可被环境绕过，需配合 CI/发布检查；Agents 文档把 guardrails 与 Human-in-the-loop 放在不同的输入输出校验和敏感动作暂停位置。
### 旧研究的限制

稳定可吸收的边界是“资产复用 ≠ 事件触发 ≠ 人类授权”。任何门禁都必须注明强制范围、失败结果、可绕过面和更高层复核；外部文档不替 LDVH 决定哪些章节必须 Human Gate。
## 建议

为能力资产登记触发条件、输入输出契约、版本和验证；为 Hook 登记事件、动作类别、失败策略；为 Git Gate、Hook Gate、Human Gate 维护独立术语和测试矩阵。
## 后续分流

供 Spark-0011、Spark-0013；需要改 00 章 1-7 章时仍按 Human Gate 单独取得同意。
