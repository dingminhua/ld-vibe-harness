---
title: Vibe Coding 从 Demo 到产品级与 LDVH 增强方向调研
status: active
urls:
- ref: https://dora.dev/
  title: DORA / Google Cloud DevOps Research
  summary: 用于说明产品级交付需要用可度量的软件交付表现衡量，而不是只看 demo 是否跑通。
- ref: https://dora.dev/research/2024/dora-report/
  title: 2024 DORA Report
  summary: 用于支撑报告中关于 AI、平台工程、质量和交付效能需要进入持续改进闭环的判断。
- ref: https://csrc.nist.gov/pubs/sp/800/218/final
  title: NIST SSDF SP 800-218
  summary: 用于说明产品级开发必须把安全软件开发实践纳入需求、实现、验证和发布流程。
- ref: https://owasp.org/www-project-application-security-verification-standard/
  title: OWASP ASVS
  summary: 用于说明产品级应用安全需要可验证的安全要求，而不是事后笼统审查。
- ref: https://owasp.org/www-project-samm/
  title: OWASP SAMM Project
  summary: 用于支撑安全成熟度应作为工程能力分阶段建设，而不是单次 checklist。
- ref: https://owasp.org/www-project-top-10-ci-cd-security-risks/
  title: OWASP Top 10 CI/CD Security Risks
  summary: 用于说明 AI 原生开发进入产品级后，CI/CD 和供应链路径本身也需要风险治理。
- ref: https://slsa.dev/
  title: SLSA
  summary: 用于支撑供应链完整性、构建来源和发布可信度应成为产品级工程的一部分。
- ref: https://sre.google/sre-book/evolving-sre-engagement-model/
  title: Google SRE Production Readiness Review
  summary: 用于说明上线前需要生产就绪审查，覆盖服务可靠性、交接和运行风险。
- ref: https://sre.google/sre-book/service-level-objectives/
  title: Google SRE Service Level Objectives
  summary: 用于支撑产品级系统需要用 SLO 表达可靠性目标，并指导发布和运营判断。
- ref: https://opentelemetry.io/docs/what-is-opentelemetry/
  title: OpenTelemetry Overview
  summary: 用于支撑产品级开发需要标准化遥测能力，让运行状态可观察、可追踪。
- ref: https://12factor.net/
  title: The Twelve-Factor App
  summary: 用于支撑配置、依赖、构建、发布和运行分离等产品级应用基础约束。
- ref: https://www.iso.org/standard/72089.html
  title: ISO/IEC/IEEE 29148 Requirements Engineering
  summary: 用于说明产品级开发需要更稳定的需求工程承载，而不是只依赖一次性提示词。
- ref: https://iso25000.com/index.php/en/iso-25000-standards/iso-25010
  title: ISO/IEC 25010 Quality Model
  summary: 用于支撑质量属性应覆盖性能、可靠性、安全性、可维护性等多个维度。
- ref: https://developers.openai.com/blog/run-long-horizon-tasks-with-codex
  title: Codex Long-Horizon Tasks
  summary: 用于说明 AI 执行复杂工程任务时需要更长周期的上下文、验证和任务分解机制。
research_intent: 调研 Vibe Coding 从 demo 到产品级需要哪些变化，以及 LDVH 未来面向产品级开发还需要增强哪些环节。
research_question: Vibe Coding 做 demo 和做产品级开发的本质差异是什么？从 demo 到产品级需要补齐哪些软件工程能力？LDVH 当前已经做了规范和基础流程，未来若面向产品级开发还需要增强哪些环节？
abstract: Vibe Coding 从 demo 到产品级的核心变化不是"让 AI 多写代码"，而是把 AI 生成代码纳入产品工程闭环。产品级要求需求、架构、质量、安全、供应链、发布、运行、观测、事故、用户反馈和成本都可管理、可验证、可追溯。LDVH 当前已经有规范、工作模型、基础流程、Code 和 Web 的底盘，但仍需要增强产品需求层、架构治理、质量门禁、DevSecOps、生产就绪、运行观测、发布治理、AI 评测和 Human-facing 驾驶舱。
recommendation_summary: LDVH 下一阶段应从"规范和基础事实源治理"升级为"AI 原生产品工程治理"。建议优先增强三条主线：产品级事实源（需求、用户旅程、架构、接口、数据、质量属性、发布对象）、产品级门禁（测试策略、安全审查、供应链、生产就绪、SLO、回滚、事故复盘）、AI 原生执行保障（角色契约、子 Agent 审查、代码评测、上下文包、风险仪表盘、自动化校验）。
object_id: study-01KZXN5TXNEZ6VF5Q8RV9TRWFE
object_uid: 019ffb52-ebb5-77cd-b796-e8c6d3ac71ee
fact_type_key: study
created_at: '2026-07-24T13:30:00+08:00'
updated_at: '2026-08-16T21:42:45.620720Z'
action_relevance: 评估 LDVH 增强方向时，区分 Vibe Coding 从 Demo 到产品级的不同阶段需求，不对应完整 Harness 结构
change_log:
- signature:
    product_name: Cindy
    model_name: gpt-5
    agent_runtime_name: codex
  at: '2026-08-13T14:03:37.924520Z'
  summary: 为历史事实对象补齐权威 object_uid，并将同项目 legacy 关系目标改写为 object_uid。
- signature:
    product_name: Cindy
    model_name: gpt-5
    agent_runtime_name: codex
  at: '2026-08-13T15:03:57Z'
  summary: 将事实对象物理定位符迁移为完整 UUIDv7 的 Crockford Base32 编码。
- summary: 补 action_relevance 字段值（规范修订：24/05 新增必填字段定义与登记）
  signature:
    product_name: Cindy
    model_name: glm-5.2
    agent_runtime_name: claude-code
  at: 2026-08-16T21:30:34.415045Z
---

## 研究问题

本报告回答三个问题：

1. Vibe Coding 做 demo 和做产品级开发的本质差异是什么；
2. 从 demo 到产品级，需要补齐哪些软件工程能力；
3. LDVH 当前已经做了规范和基础流程，未来若面向产品级开发，还需要增强哪些环节。

这里的产品级不是指大型企业流程，也不是指一开始就上复杂平台。产品级的最低含义是：软件不只在一次演示中可运行，而是能被真实用户持续使用，能演进，能被验证，能上线，能观测，能处理失败，能修复，能追溯，能被多人或多轮 AI 协作维护。

## 输入与边界

本报告输入分为三类。

第一类是行业工程标准：DORA 交付效能研究、NIST SSDF 安全开发框架、OWASP ASVS/SAMM 应用安全标准、SLSA 供应链完整性、Google SRE 生产就绪审查和 SLO 实践、OpenTelemetry 可观测性、十二要素应用、ISO 需求工程和质量模型。

第二类是 AI 编程工具实践：Codex Long-Horizon Tasks、Claude Code 常见工作流和代码审查流程。

第三类是 LDVH 现状：当前 active 的 specs 体系、事实模型、WorkCase 流程、Code 和 Web 实现。

边界如下：

- 本报告不评估 LDVH 当前是否已经达到产品级；
- 本报告不制定具体实施计划，只提出增强方向；
- 本报告不比较不同 AI 编程工具的优劣，只关注产品级工程能力的共性要求。

## 关键发现

### Demo 和产品级的本质差异是工程闭环

Vibe Coding 做 demo 时，只需要让 AI 生成一段能跑起来的代码，Human 看一遍觉得不错就行。但产品级要求需求、架构、质量、安全、供应链、发布、运行、观测、事故、用户反馈和成本都可管理、可验证、可追溯。DORA 研究说明，产品级交付需要用可度量的表现衡量。NIST SSDF 和 OWASP 标准说明，安全不能是事后审查，必须嵌入需求、实现、验证和发布流程。SLSA 说明供应链完整性需要从构建来源到发布可信度的全链路保证。

对 LDVH 的启发是：产品级不只是"把 spec 写得更详细"，而是需要完整的工程闭环。LDVH 当前的规范体系（00-24）建立了基础事实源和流程纪律，但产品级还需要需求工程、架构治理、质量门禁、生产就绪审查和运行观测这些上层能力。

### 产品级需要三类增强

根据行业标准调研，LDVH 未来面向产品级需要增强三条主线：

第一是产品级事实源：当前 V4 的事实类型（Spark、WorkCase、ADR、Pitfall、Study）覆盖了项目治理类信息，但缺少需求、用户旅程、架构、接口、数据模型、质量属性和发布对象这类产品级事实类型。ISO 29148 和 ISO 25010 为这些提供了行业参考框架。

第二是产品级门禁：当前 V4 的 Git Gate 和 Hook Gate 只做机械检查，但产品级还需要测试策略、安全审查、供应链验证、生产就绪审查、SLO 告警、回滚判定和事故复盘等门禁。OWASP SAMM 和 SLSA 提供了分阶段建设路径。

第三是 AI 原生执行保障：当前 V4 的 03 行动编排和 WorkCase 流程定义了基本的执行秩序，但产品级还需要角色契约、子 Agent 审查、代码评测、上下文包、风险仪表盘和自动化校验。Codex Long-Horizon Tasks 说明 AI 执行复杂工程任务时需要更长周期的上下文和验证机制。

### 当前 V4 的底盘已经具备升级基础

LDVH 当前的规范体系（00 理念与构成、05 事实模型基础、21 WorkCase、24 Study）、Code 实现（Helper CLI、Git Gate、Hook Gate）和 Web 呈现已经建立了可扩展的底盘。产品级增强不需要重写现有体系，而是在现有底盘上逐层叠加。DORA 和 SAMM 都强调持续改进，而不是一次性完美。

## 建议

### 优先增强产品级事实源

建议在现有五类事实类型基础上，按实际需求逐步引入产品级事实类型。优先考虑需求记录（比 Spark 更正式的用户需求承接）、架构决策记录（扩展 ADR 覆盖架构层面）、质量属性基线（与 ISO 25010 对应的可验证质量目标）。这些新类型应先通过 05 的准入条件，不与现有类型职责重叠。

### 分阶段建设产品级门禁

建议按 SAMM 的分阶段思路：第一阶段建立可验证的测试策略和基本安全审查；第二阶段引入生产就绪审查和 SLO 基线；第三阶段建立供应链验证和事故复盘机制。每个阶段先通过 WorkCase 验证，再考虑是否固化为规范。

### 增强 AI 原生执行保障

建议在 03 行动编排规范中补充角色契约和子 Agent 审查机制，并在 WorkCase 执行记录中增加上下文包和结果评测字段。这些可以先在具体 WorkCase 中实践，积累经验后再决定是否上升为规范。

## 后续分流

| 分流目标 | 建议动作 | 理由 |
|---|---|---|
| WorkCase | 建立"产品级事实源试点"工作项 | 选择一个现有类型验证扩展方向 |
| WorkCase | 建立"测试策略门禁"工作项 | 第一阶段门禁的起点 |
| ADR | 决策"产品级事实源是否应新增类型" | 涉及事实模型扩展，需要长期取舍 |
| 无需对象化 | 架构治理、运行观测等方向暂不推进 | 当前 V4 尚未进入这些阶段 |
