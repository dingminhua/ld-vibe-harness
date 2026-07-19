---
title: 开源项目公共契约与发布就绪外部实践调研
status: active
source_refs:
- kind: web-page
  locator:
    https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/adding-a-license-to-a-repository
  observed_at: '2026-07-19T10:00:00+08:00'
- kind: web-page
  locator:
    https://docs.github.com/en/enterprise-cloud@latest/repositories/creating-and-managing-repositories/best-practices-for-repositories
  observed_at: '2026-07-19T10:00:00+08:00'
- kind: web-page
  locator:
    https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases
  observed_at: '2026-07-19T10:00:00+08:00'
- kind: web-page
  locator: https://baseline.openssf.org/
  observed_at: '2026-07-19T10:00:00+08:00'
evidence_refs:
- kind: web-page
  locator:
    https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/adding-a-license-to-a-repository
  observed_at: '2026-07-19T10:00:00+08:00'
- kind: web-page
  locator:
    https://docs.github.com/en/enterprise-cloud@latest/repositories/creating-and-managing-repositories/best-practices-for-repositories
  observed_at: '2026-07-19T10:00:00+08:00'
- kind: web-page
  locator:
    https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases
  observed_at: '2026-07-19T10:00:00+08:00'
- kind: web-page
  locator: https://baseline.openssf.org/
  observed_at: '2026-07-19T10:00:00+08:00'
applicability: 用于 LDVH V4 的开源发布就绪检查、公共文档和可复核 Release 契约设计；不替代 Human
  对许可证、隐私、威胁模型和首次发布范围的决定。
validation_summary: 已读取 GitHub 官方许可、仓库最佳实践与 Release 文档，以及 OpenSSF OSPS Baseline
  主页；结论限于这些公开页面在 2026-07-19 的内容，未对 LDVH 仓库逐项完成 OSPS 认证。
research_question: GitHub 与 OpenSSF 当前如何定义一个可公开协作、可发布和可复核的开源项目最低公共契约？
abstract: 调研 GitHub 官方仓库治理/许可/Release 指南与 OpenSSF OSPS
  Baseline。共同结论是：开源发布不是只公开代码，而是同时提供许可、README、贡献与行为边界、可复核的发布快照以及按版本管理的安全基线；这些资料提供检查维度，不自动决定
  LDVH 的许可证或发布时点。
object_id: study-0001
fact_type_key: study
created_at: '2026-07-19T11:17:38.765050+08:00'
updated_at: '2026-07-19T11:17:38.765050+08:00'
---

## 研究问题

GitHub 与 OpenSSF 当前如何定义一个可公开协作、可发布和可复核的开源项目最低公共契约？
## 输入、方法与观察边界

本报告读取并对照了以下外部公开资料：https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/adding-a-license-to-a-repository、https://docs.github.com/en/enterprise-cloud@latest/repositories/creating-and-managing-repositories/best-practices-for-repositories、https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases、https://baseline.openssf.org/。观察时间统一记录在 evidence_refs；本报告只陈述页面可直接支持的内容，并将 LDVH 适用性与外部事实分开。
## 关键发现

GitHub 把 README、许可证、贡献说明、行为准则等视为让公共协作者理解项目边界的基础材料；没有许可证时，公开代码并不自动授予他人按开源方式使用的权利。GitHub Release 以 tag 对应的代码快照和发布说明组织可复核交付。OpenSSF OSPS Baseline 是有版本的控制基线，应明确采用的基线版本和未满足项。
## 结论与限制

外部实践支持“公共契约 + 版本化发布 + 安全基线”的三层结构，但没有替 LDVH 选择具体许可证、支持矩阵、威胁接受或发布承诺。最大限制是文档存在不等于实践已执行，OSPS 页面也不等于本仓库已经通过基线。
## 建议

把许可证、README、CONTRIBUTING、CODE_OF_CONDUCT、SECURITY、CHANGELOG/Release 与可复核测试证据作为候选发布清单；对每一项区分“存在”“内容合规”“本次发布已验证”。
## 后续分流

供 Spark-0006（开源发布就绪与公共契约）和 Spark-0007（多项目配置拓扑）继续拆解；只有 Human 选定许可证、公开支持范围或风险接受后，才进入 ADR/WorkCase。
