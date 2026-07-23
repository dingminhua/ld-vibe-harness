---
title: AI 能力资产、Hook 与工程门禁行业实践调研
status: active
applicability: 用于 LDVH 能力资产准入、Hook 动作分类、Git Gate/Hook Gate/Human Gate
  词汇和工程门禁设计；不改变 00 章对 Human Gate 的授权。
validation_summary: 已读取 OpenAI Codex Skills/Hooks、Git 官方 hooks 和 OpenAI Agents
  guardrails/HITL 公开文档；没有把第三方插件行为当作官方保证，也未验证本仓库每个 Hook 的覆盖率。
research_question: Codex Skills/Hooks、Git hooks 与 Agent guardrails
  的公开文档如何区分可复用能力、生命周期自动化和强制门禁？
abstract: 调研 Codex Skills/Hooks、Git hooks 与 OpenAI Agents guardrails/HITL
  文档。外部模式把技能视为可复用工作流，把 Hook 视为生命周期事件自动化，把 guardrail/HITL
  视为输入输出或动作级的阻断/升级；三者职责不同，不能互称。
object_id: study-0004
fact_type_key: study
created_at: '2026-07-19T11:17:44.511811+08:00'
updated_at: '2026-07-23T14:21:35.783731+08:00'
urls:
- ref: https://developers.openai.com/codex/skills
  title: developers.openai.com/codex/skills
  summary: 外部研究资料；具体支持范围与限制见本报告正文。
- ref: https://developers.openai.com/codex/hooks
  title: developers.openai.com/codex/hooks
  summary: 外部研究资料；具体支持范围与限制见本报告正文。
- ref: https://git-scm.com/docs/githooks
  title: git-scm.com/docs/githooks
  summary: 外部研究资料；具体支持范围与限制见本报告正文。
- ref: https://openai.github.io/openai-agents-python/guardrails/
  title: openai.github.io/openai-agents-python/guardrails/
  summary: 外部研究资料；具体支持范围与限制见本报告正文。
- ref: https://openai.github.io/openai-agents-python/human_in_the_loop/
  title: openai.github.io/openai-agents-python/human_in_the_loop/
  summary: 外部研究资料；具体支持范围与限制见本报告正文。
---

## 研究问题

Codex Skills/Hooks、Git hooks 与 Agent guardrails 的公开文档如何区分可复用能力、生命周期自动化和强制门禁？
## 输入、方法与观察边界

本报告读取并对照了以下外部公开资料：https://developers.openai.com/codex/skills、https://developers.openai.com/codex/hooks、https://git-scm.com/docs/githooks、https://openai.github.io/openai-agents-python/guardrails/、https://openai.github.io/openai-agents-python/human_in_the_loop/。外部资料条目记录在 urls 中；本报告只陈述页面可直接支持的内容，并将 LDVH 适用性与外部事实分开。
## 关键发现

Skills 文档强调可打包、可调用的工作流知识；Hooks 关注会话或生命周期事件触发的脚本；Git hooks 是本地 Git 事件点，适合机械检查但可被环境绕过，需配合 CI/发布检查；Agents 文档把 guardrails 与 Human-in-the-loop 放在不同的输入输出校验和敏感动作暂停位置。
## 结论与限制

稳定可吸收的边界是“资产复用 ≠ 事件触发 ≠ 人类授权”。任何门禁都必须注明强制范围、失败结果、可绕过面和更高层复核；外部文档不替 LDVH 决定哪些章节必须 Human Gate。
## 建议

为能力资产登记触发条件、输入输出契约、版本和验证；为 Hook 登记事件、动作类别、失败策略；为 Git Gate、Hook Gate、Human Gate 维护独立术语和测试矩阵。
## 后续分流

供 Spark-0011、Spark-0013；需要改 00 章 1-7 章时仍按 Human Gate 单独取得同意。
