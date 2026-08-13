---
title: 开源项目公共契约与发布就绪外部实践调研
status: retired
disposition_summary: 已按 v3 基线决定重新研究；本旧 v4 短报告不再作为当前研究入口，外部资料、发现与后续启发须在新 Study 中重新读取和表达。
research_question: GitHub 与 OpenSSF 当前如何定义一个可公开协作、可发布和可复核的开源项目最低公共契约？
abstract: 调研 GitHub 官方仓库治理/许可/Release 指南与 OpenSSF OSPS Baseline。共同结论是：开源发布不是只公开代码，而是同时提供许可、README、贡献与行为边界、可复核的发布快照以及按版本管理的安全基线；这些资料提供检查维度，不自动决定 LDVH 的许可证或发布时点。
object_id: study-01KZXN5TXNEJJSBR71A8GV7W2R
object_uid: 019ffb52-ebb5-74a5-95e0-e15221b3f058
fact_type_key: study
created_at: '2026-07-19T11:17:38.765050+08:00'
updated_at: '2026-08-13T15:03:57Z'
urls:
- ref: https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/adding-a-license-to-a-repository
  title: docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/adding-a-license-to-a-repository
  summary: 曾用于旧研究的 GitHub 许可证实践资料；不单独支持当前 LDVH 的许可证或发布决定。
- ref: https://docs.github.com/en/enterprise-cloud@latest/repositories/creating-and-managing-repositories/best-practices-for-repositories
  title: docs.github.com/en/enterprise-cloud@latest/repositories/creating-and-managing-repositories/best-practices-for-repositories
  summary: 曾用于旧研究的 GitHub 仓库实践资料；不单独证明本项目已符合任何实践。
- ref: https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases
  title: docs.github.com/en/repositories/releasing-projects-on-github/about-releases
  summary: 曾用于旧研究的 GitHub Release 说明；不单独证明本项目的发布已就绪。
- ref: https://baseline.openssf.org/
  title: baseline.openssf.org
  summary: 曾用于旧研究的 OpenSSF 基线入口；不表示本项目已通过或采用该基线。
change_log:
- signature:
    product_name: Cindy
    model_name: gpt-5
    agent_runtime_name: codex
  at: '2026-08-13T14:03:10.662730Z'
  summary: 为历史事实对象补齐权威 object_uid，并将同项目 legacy 关系目标改写为 object_uid。
- signature:
    product_name: Cindy
    model_name: gpt-5
    agent_runtime_name: codex
  at: '2026-08-13T15:03:57Z'
  summary: 将事实对象物理定位符迁移为完整 UUIDv7 的 Crockford Base32 编码。
---

## 研究问题

GitHub 与 OpenSSF 当前如何定义一个可公开协作、可发布和可复核的开源项目最低公共契约？
## 输入与边界

本报告读取并对照了以下外部公开资料：https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/adding-a-license-to-a-repository、https://docs.github.com/en/enterprise-cloud@latest/repositories/creating-and-managing-repositories/best-practices-for-repositories、https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases、https://baseline.openssf.org/。外部资料条目记录在 urls 中；本报告只陈述页面可直接支持的内容，并将 LDVH 适用性与外部事实分开。
## 关键发现

GitHub 把 README、许可证、贡献说明、行为准则等视为让公共协作者理解项目边界的基础材料；没有许可证时，公开代码并不自动授予他人按开源方式使用的权利。GitHub Release 以 tag 对应的代码快照和发布说明组织可复核交付。OpenSSF OSPS Baseline 是有版本的控制基线，应明确采用的基线版本和未满足项。
### 旧研究的限制

外部实践支持“公共契约 + 版本化发布 + 安全基线”的三层结构，但没有替 LDVH 选择具体许可证、支持矩阵、威胁接受或发布承诺。最大限制是文档存在不等于实践已执行，OSPS 页面也不等于本仓库已经通过基线。
## 建议

把许可证、README、CONTRIBUTING、CODE_OF_CONDUCT、SECURITY、CHANGELOG/Release 与可复核测试证据作为候选发布清单；对每一项区分“存在”“内容合规”“本次发布已验证”。
## 后续分流

供 Spark-0006（开源发布就绪与公共契约）和 Spark-0007（多项目配置拓扑）继续拆解；只有 Human 选定许可证、公开支持范围或风险接受后，才进入 ADR/WorkCase。
