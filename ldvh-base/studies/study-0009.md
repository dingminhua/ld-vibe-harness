---
title: Superpowers 工程约束工作流调研
status: active
applicability: 用于 LDVH 能力资产、Hook/WorkCase 流程、验证优先和分支收尾设计；不直接安装插件、不继承其 skill
  文件或遥测行为。
validation_summary: 已读取 Superpowers 当前 README/仓库页面，观察到 2026-07-02 的 v6.1.1
  页面信息、安装方式、基本工作流、技能目录、MIT License 与可选遥测说明；未运行其插件或 eval harness。
research_question: obra/superpowers 当前公开技能框架如何把头脑风暴、计划、工作树、TDD、并行 Agent、Review
  和收尾串成强制工作流？
abstract: 调研 Superpowers README 与公开技能清单。其基本流程从
  brainstorming、worktree、writing-plans，经过
  subagent-driven-development/TDD/review，最后到 branch finishing；项目强调 mandatory
  workflows、evidence over claims，并以 MIT 许可发布。它提供过程设计参考，不改变 LDVH 的 Gate 术语或授权模型。
object_id: study-0009
fact_type_key: study
created_at: '2026-07-19T11:17:59.111588+08:00'
updated_at: '2026-07-23T14:21:35.783731+08:00'
urls:
- ref: https://github.com/obra/superpowers
  title: github.com/obra/superpowers
  summary: 外部研究资料；具体支持范围与限制见本报告正文。
- ref: https://github.com/obra/superpowers/blob/main/README.md
  title: github.com/obra/superpowers/blob/main/README.md
  summary: 外部研究资料；具体支持范围与限制见本报告正文。
- ref: https://github.com/obra/superpowers/tree/main/skills
  title: github.com/obra/superpowers/tree/main/skills
  summary: 外部研究资料；具体支持范围与限制见本报告正文。
---

## 研究问题

obra/superpowers 当前公开技能框架如何把头脑风暴、计划、工作树、TDD、并行 Agent、Review 和收尾串成强制工作流？
## 输入、方法与观察边界

本报告读取并对照了以下外部公开资料：https://github.com/obra/superpowers、https://github.com/obra/superpowers/blob/main/README.md、https://github.com/obra/superpowers/tree/main/skills。外部资料条目记录在 urls 中；本报告只陈述页面可直接支持的内容，并将 LDVH 适用性与外部事实分开。
## 关键发现

公开流程把设计确认、隔离工作树、细粒度计划、每任务新 Agent/双阶段审查、RED-GREEN-REFACTOR、代码 Review 和分支收尾串联，明确这些是 mandatory workflows 而非建议。项目还公开 skill 行为测试/eval、插件基础设施测试、MIT 许可，并说明部分可选视觉伴随能力有遥测退出环境变量。
## 结论与限制

可吸收的核心是“先澄清设计、再隔离、计划、实现、验证、Review、收尾”的过程约束和证据优先；不能把其强制 workflow、插件安装、遥测或 TDD 口号直接变成 LDVH 的 Gate。限制是仓库说明属于项目方自述，未在 LDVH 上验证跨 Harness 一致性。
## 建议

把有价值的流程拆成 LDVH 自己的 Spark/WorkCase/能力资产，逐项绑定现有 Git Gate、Hook Gate、Human Gate；保留不适用时的停止和例外记录。
## 后续分流

供 Spark-0011、Spark-0013；若要吸收某个 skill，先做许可、字段、触发和验证闭环，不复制整个外部框架。
