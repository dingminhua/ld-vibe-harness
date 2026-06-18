---
id: study-0005
type: study
title: Vibe Coding 从 Demo 到产品级与 LDVH 增强方向调研
status: active
created: '2026-06-18T08:49:21'
updated: '2026-06-18T21:14:45+08:00'
summary: |
  Vibe Coding 从 demo 到产品级的核心变化，不是“让 AI 多写代码”，而是把 AI 生成代码纳入产品工程闭环。产品级要求需求、架构、质量、安全、供应链、发布、运行、观测、事故、用户反馈和成本都可管理、可验证、可追溯。LDVH 当前已经有规范、工作模型、基础流程、Code 和 Web 的底盘，但仍需要增强产品需求层、架构治理、质量门禁、DevSecOps、生产就绪、运行观测、发布治理、AI 评测和 Human-facing 驾驶舱。
user_intent: 用户要求调研 Vibe Coding 从 demo 到产品级需要哪些变化，以及 LDVH 未来面向产品级开发还需要增强哪些环节。
conclusion: |
  LDVH 下一阶段应从“规范和基础事实源治理”升级为“AI 原生产品工程治理”。建议优先增强三条主线：一是产品级事实源，包括需求、用户旅程、架构、接口、数据、质量属性和发布对象；二是产品级门禁，包括测试策略、安全审查、供应链、生产就绪、SLO、回滚和事故复盘；三是 AI 原生执行保障，包括角色契约、子 Agent 审查、代码评测、上下文包、风险仪表盘和自动化校验。这样才能让 Vibe Coding 从快速 demo 进入可持续交付。
related_refs:
  - https://dora.dev/
  - https://dora.dev/research/2024/dora-report/
  - https://csrc.nist.gov/pubs/sp/800/218/final
  - https://csrc.nist.gov/pubs/sp/800/218/r1/ipd
  - https://owasp.org/www-project-application-security-verification-standard/
  - https://owasp.org/www-project-samm/
  - https://owaspsamm.org/
  - https://owasp.org/www-project-top-10-ci-cd-security-risks/
  - https://slsa.dev/
  - https://sre.google/sre-book/evolving-sre-engagement-model/
  - https://sre.google/sre-book/service-level-objectives/
  - https://sre.google/workbook/implementing-slos/
  - https://opentelemetry.io/docs/what-is-opentelemetry/
  - https://opentelemetry.io/docs/concepts/observability-primer/
  - https://12factor.net/
  - https://www.iso.org/standard/72089.html
  - https://iso25000.com/index.php/en/iso-25000-standards/iso-25010
  - https://developers.openai.com/blog/run-long-horizon-tasks-with-codex
  - https://docs.anthropic.com/en/docs/claude-code/common-workflows
  - https://code.claude.com/docs/en/code-review
related_memos:
  - memo-0008
related_workareas: []
related_workplans: []
related_adrs: []
related_pitfalls: []
related_docs:
  - specs/00-LD-Vibe-Harness理念与纲要.md
  - specs/04.02-LDVH能力资产与落地保障规范.md
  - specs/06-工作流程基础规范.md
  - specs/07-Code确定性执行实现规范.md
  - specs/08-Web信息同步实现规范.md
  - specs/10-测试基础规范.md
  - specs/21-WorkPlan-工作计划.md
archive_reason:
---

# Vibe Coding 从 Demo 到产品级与 LDVH 增强方向调研

## 研究问题

本报告回答三个问题：

1. Vibe Coding 做 demo 和做产品级开发的本质差异是什么；
2. 从 demo 到产品级，需要补齐哪些软件工程能力；
3. LDVH 当前已经做了规范和基础流程，未来若面向产品级开发，还需要增强哪些环节。

这里的“产品级”不是指大型企业流程，也不是指一开始就上复杂平台。产品级的最低含义是：软件不只在一次演示中可运行，而是能被真实用户持续使用，能演进，能被验证，能上线，能观测，能处理失败，能修复，能追溯，能被多人或多轮 AI 协作维护。

## 资料边界

本次调研使用公开一手或准一手资料，访问时间为 2026-06-18：

- DORA / Google Cloud DevOps research：https://dora.dev/ ，https://dora.dev/research/2024/dora-report/
- NIST SSDF SP 800-218：https://csrc.nist.gov/pubs/sp/800/218/final
- NIST SSDF SP 800-218 revision initial public draft：https://csrc.nist.gov/pubs/sp/800/218/r1/ipd
- OWASP ASVS：https://owasp.org/www-project-application-security-verification-standard/
- OWASP SAMM：https://owasp.org/www-project-samm/ ，https://owaspsamm.org/
- OWASP Top 10 CI/CD Security Risks：https://owasp.org/www-project-top-10-ci-cd-security-risks/
- SLSA：https://slsa.dev/
- Google SRE Production Readiness Review：https://sre.google/sre-book/evolving-sre-engagement-model/
- Google SRE SLO：https://sre.google/sre-book/service-level-objectives/
- Google SRE Implementing SLOs：https://sre.google/workbook/implementing-slos/
- OpenTelemetry：https://opentelemetry.io/docs/what-is-opentelemetry/ ，https://opentelemetry.io/docs/concepts/observability-primer/
- Twelve-Factor App：https://12factor.net/
- ISO/IEC/IEEE 29148 requirements engineering：https://www.iso.org/standard/72089.html
- ISO/IEC 25010 quality model：https://iso25000.com/index.php/en/iso-25000-standards/iso-25010
- OpenAI Codex long-horizon task guidance：https://developers.openai.com/blog/run-long-horizon-tasks-with-codex
- Claude Code workflow and review guidance：https://docs.anthropic.com/en/docs/claude-code/common-workflows ，https://code.claude.com/docs/en/code-review

这些资料不直接替代 LDVH specs。它们用于提炼产品级开发能力框架和 LDVH 后续增强方向。

## Demo 级 Vibe Coding 的典型形态

Demo 级 Vibe Coding 的优势很明确：

1. 从自然语言到可运行界面的速度很快；
2. AI 能快速拼接框架、组件、API、样例数据和局部逻辑；
3. Human 能在短时间内验证一个想法“看起来是否成立”；
4. 对单人、短周期、低风险探索非常高效。

但 demo 级通常存在以下隐含假设：

1. 需求不稳定也没关系，因为目标只是展示；
2. 数据不真实也没关系，因为只要样子像；
3. 安全、权限、异常、迁移、并发和边界条件可以之后再说；
4. 没有生产用户，因此可用性、恢复、监控和事故处理不重要；
5. 代码债可以接受，因为重写成本看似不高；
6. 质量主要靠 Human 看一眼，而不是系统验证；
7. 上下文主要在聊天里，而不是在可追踪事实源里。

这就是 demo 的甜点，也是产品级的陷阱。AI 越能快速生成，越容易把未经验证的复杂性也快速堆起来。

## 产品级开发的变化

从 demo 到产品级，至少发生十个变化。

### 1. 从“能跑”到“满足真实需求”

产品级要求需求可追踪、可验收、可变更。ISO/IEC/IEEE 29148 把需求工程放在系统和软件生命周期中处理，强调需求过程和需求信息项。对 Vibe Coding 来说，这意味着不能只让 AI 读一句“做个 CRM”，而要有用户、场景、约束、验收、非目标和变更记录。

LDVH 当前已有 WorkPlan 和 Memo，但缺更产品化的需求层。例如：

- 用户画像；
- 用户旅程；
- 业务流程；
- 产品目标；
- 功能清单；
- 非功能需求；
- 验收样例；
- 需求到实现、测试、发布的追踪关系。

### 2. 从“局部功能”到“系统架构”

Demo 可以由 AI 按默认框架拼起来；产品级需要架构边界、模块职责、接口契约、数据模型、依赖关系、扩展点和迁移路径。

Twelve-Factor App 强调 codebase、dependencies、config、backing services、build/release/run、logs 等应用工程边界。CNCF 对 cloud native 的定义也强调安全、弹性、可管理、可持续和可观测。

LDVH 当前有 ADR，但还缺系统架构事实源和接口治理能力。未来需要能让 AI 快速回答：

- 系统边界在哪里；
- 模块之间如何通信；
- 数据从哪里来，到哪里去；
- 哪些接口是稳定契约；
- 哪些依赖是关键风险；
- 哪些设计决策已经定型。

### 3. 从“看起来可用”到“质量属性可验证”

ISO/IEC 25010 把软件质量拆成多个质量特征，例如功能适合性、性能效率、兼容性、可用性、可靠性、安全性、可维护性和可移植性。产品级不能只问“功能有没有”，还要问“是否可靠、是否安全、是否可维护、是否易用、是否能被迁移和扩展”。

LDVH 当前价值标准中已有强制验证和证据沉淀，但还没有把质量属性系统化映射到 WorkPlan、测试、评审和发布门禁。

### 4. 从“人工验收”到“测试金字塔和回归体系”

产品级需要单元测试、集成测试、端到端测试、契约测试、迁移测试、可访问性检查、性能测试、安全测试和回归样例。不是每个项目一开始都要全量，但至少要能按风险选择。

Claude Code 和 Codex 相关资料都强调让 AI 运行构建、测试和 lint，建立自我验证循环。Claude Code Review 的公开说明也强调多 agent 分工查找不同类别问题，并用实际代码行为验证候选问题以过滤误报。

LDVH 目前有 `specs/10-测试基础规范.md`，但还需要把产品级测试策略变成可执行的工作流和质量门禁，而不仅是测试治理原则。

### 5. 从“代码生成”到“安全开发生命周期”

NIST SSDF 把安全软件开发实践组织为可集成到 SDLC 的高层实践。OWASP ASVS 提供 Web 应用安全验证要求。OWASP SAMM 则用成熟度模型帮助组织按风险持续改进软件安全。OWASP CI/CD Security Risks 和 SLSA 进一步指出，现代软件风险不只在代码本身，也在 CI/CD、依赖、构建、发布和供应链。

Vibe Coding 的安全风险更尖锐：

- AI 可能生成不安全默认配置；
- AI 可能引入过时依赖；
- AI 可能误用认证和授权；
- AI 可能把密钥写入代码或日志；
- AI 可能绕过最小权限；
- AI 可能不知道组织合规边界；
- AI 生成的大量代码增加审查负担。

LDVH 当前没有完整 DevSecOps 层，后续需要安全需求、威胁建模、依赖治理、密钥治理、权限审查、CI/CD 安全和供应链证据。

### 6. 从“本地运行”到“可发布、可回滚、可迁移”

产品级需要环境隔离、配置管理、构建产物、发布流程、数据库迁移、灰度、回滚、备份和版本兼容。Twelve-Factor App 的 build/release/run 分离、config 外置、logs 事件流等原则对这里很有启发。

LDVH 目前 Change 记录 Git commit，但还没有 Release / Deployment / Migration 等对象或流程。一个产品级项目需要 AI 能回答：

- 这次改动是否可发布；
- 发布前检查是什么；
- 数据迁移是否可逆；
- 回滚路径是什么；
- 失败后如何恢复；
- 哪些配置和密钥必须由环境提供。

### 7. 从“上线即完成”到“运行可观测”

OpenTelemetry 把 telemetry 数据归为 traces、metrics 和 logs，并提供生成、导出和收集这些数据的框架。Google SRE 强调 SLO 是由 SLI 测量的目标值或范围，error budget 用于平衡可靠性与迭代速度。

产品级软件必须让团队知道：

- 用户是否真的成功完成任务；
- 性能是否退化；
- 错误率是否上升；
- 哪个发布导致问题；
- 哪个依赖或接口变慢；
- 事故是否正在消耗错误预算。

LDVH 目前缺运行态事实源和观测闭环。后续需要把 SLO、指标、日志、trace、告警、仪表盘、事故和复盘接入工作模型与 Web。

### 8. 从“单次交付”到“持续交付能力”

DORA 研究长期关注软件交付和运维表现。DORA 四个核心指标在行业中常用于衡量交付表现：部署频率、变更前置时间、变更失败率、恢复时间。产品级不是一次性交付，而是持续改进。

LDVH 当前能记录 Change，但还不能系统衡量交付吞吐、质量和恢复能力。后续需要能看见：

- 一个需求从 Memo / WorkPlan 到发布用了多久；
- 哪类变更最容易失败；
- 哪些对象长期卡住；
- 哪些测试或门禁阻塞最多；
- 事故后恢复时间如何；
- AI 是否真的提高了交付质量，而不是只提高代码产量。

### 9. 从“Human 看结果”到“Human 驾驶产品态势”

Demo 阶段 Human 直接看界面即可；产品级 Human 需要看到需求状态、风险、证据、发布、事故、质量、成本和用户反馈。Web 不只是对象浏览器，而应该成为产品工程驾驶舱。

LDVH 当前 Web 定位是 Human-facing 桥接和受控轻写入，这很正确，但产品级还需要：

- 需求和工作态势；
- 质量门禁状态；
- 发布准备度；
- 风险热力图；
- 安全和依赖风险；
- 运行指标和事故；
- Human Gate 队列；
- AI 贡献与验证质量。

### 10. 从“AI 写代码”到“AI 工程系统”

AI coding 的产品级关键不是让 AI 无限自治，而是给 AI 明确事实源、上下文包、角色契约、工具权限、验证命令、审查机制和停止条件。

这与前一份子 Agent 调研相互呼应：Codex、TRAE CN、Claude Code CLI 都在走向专业角色、隔离上下文、工具权限和多 agent 审查。但 LDVH 必须把这些运行期能力沉淀为环境无关的 Role Contract 和事实源回写边界。

## LDVH 当前已具备的底盘

从现有 specs 看，LDVH 已经具备几个重要底盘：

1. 00 总纲已经把 LDVH 定位为面向 AI 协作的事实源治理和运行闭环，而不是普通文档集合；
2. WorkArea / WorkPlan / ADR / Memo / Pitfall / Study / Change 已经覆盖目标、计划、决策、经验、报告和变更；
3. Memo + Study 已经解决了“想法暂存”和“稳定报告”分离；
4. WorkPlan 已经把执行编排、验证证据、关闭证据放在一次工作对象内；
5. 10 测试基础规范已经建立验证声明、测试归属和事实源边界；
6. Code 和 Web 已经在理念层被定义为确定性执行与 Human-facing 桥接；
7. 最近子 Agent 调研已经开始把多角色抽象为 Role Contract，而不是绑定具体环境线程。

这说明 LDVH 已经解决了 demo 到产品级的一个核心底盘：AI 不再只靠聊天记忆，而是有事实源、有对象、有流程、有证据、有变更。

## LDVH 仍缺的产品级能力

### 1. 产品需求层

当前 WorkPlan 更像一次可验收工作计划，Memo 更像议题入口。产品级还需要更稳定的产品需求层。候选能力包括：

- ProductGoal / 产品目标；
- User / 用户画像；
- Journey / 用户旅程；
- Feature / 功能对象；
- Requirement / 需求对象；
- AcceptanceExample / 验收样例；
- Feedback / 用户反馈；
- Roadmap / 路线图。

不一定都要变成工作模型，但 LDVH 至少需要定义这些信息应放在哪里、如何被 AI 读取、如何与 WorkPlan 关联。

### 2. 架构与接口治理

当前 ADR 可以记录决策，但产品级还需要持续可读的系统事实。候选能力包括：

- 系统上下文图；
- 模块边界；
- 数据模型；
- API / event / contract catalog；
- dependency map；
- 迁移记录；
- 环境配置矩阵；
- 技术债清单。

这些能力可以先进入 docs 或 Study，再判断是否需要工作对象。

### 3. 质量属性与测试策略

LDVH 需要把 ISO 25010 式质量属性转成 AI 可执行的门禁语言。例如：

- 功能正确性：需求验收、回归样例、契约测试；
- 可靠性：错误处理、重试、幂等、降级、SLO；
- 性能：基准、预算、压测、前端性能；
- 可用性：可访问性、关键路径 UX、移动端适配；
- 安全性：认证、授权、输入校验、密钥、依赖；
- 可维护性：模块边界、复杂度、代码审查；
- 可移植性：配置、环境、部署方式。

这需要在 WorkPlan 的成功标准、验证证据和关闭证据中形成模板或检查项。

### 4. DevSecOps 与供应链

LDVH 需要补齐：

- threat modeling 工作流；
- dependency review；
- SBOM / provenance / SLSA 证据；
- secret scanning；
- SAST / DAST / dependency scanning；
- CI/CD 权限和 token 边界；
- release artifact 签名或来源证明；
- 高风险变更安全 Human Gate。

这些内容不能只写成“注意安全”，必须成为工具、检查、证据和门禁。

### 5. 发布与生产就绪

参考 Google SRE 的 Production Readiness Review，产品级需要上线前检查：

- 服务重要性；
- 依赖和容量；
- SLO / SLI；
- 监控和告警；
- runbook；
- rollback；
- 数据备份和恢复；
- 隐私和合规；
- on-call 或责任人；
- 事故处理流程。

LDVH 可考虑新增 Release / ProductionReadiness / Deployment / Migration 等对象或流程，也可以先通过 WorkPlan 模板和 Study 试运行。

### 6. 运行观测与事故复盘

LDVH 当前主要治理开发期事实源，产品级需要运行期闭环：

- metrics / logs / traces；
- alert；
- incident；
- postmortem；
- SLO 消耗；
- 用户影响；
- 修复 WorkPlan；
- Pitfall / ADR / docs 回流。

这会显著扩大 LDVH 范围，需要谨慎分阶段，不宜一次性全做。

### 7. AI 产出评测与审查

Vibe Coding 产品级需要专门衡量 AI 产出质量：

- AI 生成代码的测试通过率；
- AI 修复引入回归的比例；
- AI 误判 Human Gate 的次数；
- AI 审查发现率和误报率；
- 任务从计划到关闭的可恢复性；
- 上下文压缩后是否能继续；
- 子 Agent 汇总是否可追溯；
- AI 是否遵守事实源边界。

这部分是 LDVH 相比传统工程体系的独特价值。

### 8. Web 驾驶舱

LDVH Web 未来需要从“对象阅读器”升级为“产品工程态势驾驶舱”。建议逐步增加：

- WorkPlan 看板；
- 风险队列；
- Human Gate 队列；
- 验证证据状态；
- 发布准备度；
- 测试与 CI 状态；
- 安全和依赖风险；
- SLO 和事故概览；
- AI 执行质量指标。

Web 仍不能成为开放编辑后台，但可以成为 Human 介入、验收和方向校正的主界面。

## 建议的 LDVH 增强路线

### 第一阶段：产品级准备度最小闭环

目标是让 LDVH 不只管“工作是否完成”，还管“是否可以交付给真实用户”。

建议新增或增强：

1. WorkPlan 模板：加入产品级验收、质量属性、风险、发布影响和回滚问题；
2. Release readiness checklist：先作为工作流程或 Study 模板，不急着建对象；
3. 测试策略模板：按风险选择 unit / integration / e2e / contract / security / performance；
4. Web 显示验证证据和 Human Gate 队列；
5. Code 校验 WorkPlan 是否有可复现验证证据。

### 第二阶段：安全与供应链闭环

目标是防止 AI 快速引入不可见安全和供应链风险。

建议新增或增强：

1. Security Review 工作流程；
2. Dependency Review 工作流程；
3. Secret / credential 边界规则；
4. CI/CD 安全检查；
5. ASVS / SSDF / SLSA 映射模板；
6. 安全风险进入 Pitfall、ADR 或 WorkPlan 的分流规则。

### 第三阶段：生产运行闭环

目标是让产品上线后仍在 LDVH 体系中可观测、可恢复、可学习。

建议新增或增强：

1. SLO / SLI / error budget 记录方式；
2. observability mapping；
3. Incident / Postmortem 工作对象或流程；
4. runbook 和 rollback 事实源；
5. Web 运行态风险展示；
6. 事故后经验回流。

### 第四阶段：AI 原生工程度量

目标是衡量 LDVH 是否真的提升 AI 产品级开发能力。

建议新增或增强：

1. AI 执行质量指标；
2. 子 Agent 审查质量指标；
3. 上下文恢复成功率；
4. Human Gate 命中率与误判率；
5. 需求到发布 lead time；
6. 变更失败率和恢复时间；
7. 重复 Pitfall 下降情况。

## 对 00 总纲的候选补充方向

后续修改 00 时，可以吸收以下理念：

```text
LDVH 面向的不是“让 AI 更快生成 demo”，而是“让 AI 参与真实产品持续演进”。产品级 Vibe Coding 的关键不在于代码生成速度，而在于需求、架构、质量、安全、发布、运行和反馈能否形成可验证、可追溯、可恢复的工程闭环。
```

还可以补充：

```text
当 LDVH 从基础规范和工作流走向产品级开发支撑时，应逐步把产品需求、架构接口、质量属性、安全供应链、发布就绪、运行观测、事故复盘和 AI 产出评测纳入事实源治理。任何新增能力都必须继续服务 AI 第一执行者与 Human 高质量确认，而不是制造新的流程负担。
```

## 残留不确定性

1. LDVH 是否应新增 Product / Feature / Release / Incident 等工作模型，还是先用 docs + WorkPlan + Study 承接，需要后续单独决策。
2. 产品级能力很容易膨胀成大型 ALM / DevOps 平台，LDVH 应保持“AI 工程驾驭体系”的边界，不应复制 Jira、GitHub、Datadog 或 CI 平台。
3. 不同项目的产品级门槛不同。个人工具、SaaS、医疗、金融、交易系统、安全产品的质量和合规要求差异巨大，LDVH 需要风险分级，而不是一刀切。
4. Web 驾驶舱的增强必须谨慎控制写入边界，避免 Web 变成第二事实源。

## 后续分流建议

1. 先创建或补充 WorkPlan，聚焦“产品级 readiness 最小闭环”。
2. 在 00 中补充产品级 Vibe Coding 的价值边界，但避免一次性把所有产品工程能力写成承诺。
3. 在 06 或 40-59 中新增“产品级准备度评审”工作流程。
4. 在 10 中补充产品级测试策略和质量属性映射。
5. 在 04.02 中补充 AI coding 环境能力资产与产品级工程能力的关系。
6. 在 07 中规划 Code 校验路线：需求追踪、验证证据、引用完整性、门禁状态、发布准备度。
7. 在 08 中规划 Web 路线：Human Gate、验证证据、风险、发布准备度和产品态势。
