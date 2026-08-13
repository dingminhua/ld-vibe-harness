---
title: LDVH 规则源与五类事实源的局部编辑策略评估
status: active
report_kind: technical_assessment
input_refs:
- kind: specification
  locator: specs/00-理念与构成.md §8.1 工作上下文的信息交付顺序与渐进式披露、§8.2 薄 Skill、Git Hook 与核心职责边界、§10.1 触发条件
  version: ebf09147b1d5e01f54568f5bcefef63b15e94937
  observed_at: '2026-08-12T08:19:01Z'
- kind: specification
  locator: specs/01-规范模型基础规范.md §9 规则读取、§13 规范责任与来源先行闭环、§15 验证要求、§16 Human Gate
  version: ebf09147b1d5e01f54568f5bcefef63b15e94937
  observed_at: '2026-08-12T08:19:01Z'
- kind: specification
  locator: specs/05-事实模型基础规范.md §11 事实对象发现、读取、受控创建与单对象更新
  version: ebf09147b1d5e01f54568f5bcefef63b15e94937
  observed_at: '2026-08-12T08:19:01Z'
- kind: specification
  locator: specs/20-Spark-火花.md、specs/21-WorkCase-工作项.md、specs/22-ADR-决策.md、specs/23-Pitfall-踩坑经验.md、specs/24-Study-研究报告.md
  version: ebf09147b1d5e01f54568f5bcefef63b15e94937
  observed_at: '2026-08-12T08:19:01Z'
- kind: specification
  locator: specs/31-事实对象判定与受控创建行动模板.md、specs/32-事实对象生命周期变更与承接处置行动模板.md
  version: ebf09147b1d5e01f54568f5bcefef63b15e94937
  observed_at: '2026-08-12T08:19:01Z'
- kind: fact-objects
  locator: ldvh-base/studies/study-0028.md
  version: ebf09147b1d5e01f54568f5bcefef63b15e94937
  observed_at: '2026-08-12T08:19:01Z'
- kind: code
  locator: code/ldvh/facts/contracts.py、code/ldvh/facts/update_application.py、code/ldvh/facts/workcase_update.py、code/ldvh/specs/repository.py、code/ldvh/specs/graph.py
  version: ebf09147b1d5e01f54568f5bcefef63b15e94937
  observed_at: '2026-08-12T08:19:01Z'
- kind: helper-call-results
  locator: 2026-08-12 当前会话中的 read-fact-objects、find-fact-object-candidates、prepare-fact-object-draft、read-specification-content 与 read-action-template-content 响应
  observed_at: '2026-08-12T08:19:01Z'
research_question: 针对 LDVH 的规则源 specs/及授权附件与五类受管事实对象，局部编辑、并发处理、治理与正式发布应如何分层；哪些能力能够共享，哪些必须按规则源、Study、Spark、Pitfall、ADR 和 WorkCase 分别处理？
abstract: 本技术评估于 2026-08-12 回读 LDVH 当前规则源、五类事实类型、受控更新实现与 study-0028，并比较其中已记录的条件请求、JSON Patch、TextEdit、Git 三方合并与 OT/CRDT 资料线索。结论是六类资产应采用不同语义策略：规范源走直接工作树编辑、独立复核、风险匹配验证、条件性 Human Gate 与 Git 闭环；五类事实继续由 Helper 的完整对象验证、CAS、原子替换、回读和审计发布。两边可共享局部定位、候选 diff、草稿与 stale 提示，但不能共享写权限、正式生效条件或权威校验。Study 是局部正文请求的首个候选；其余事实类型应先优化各自的候选、草稿、更正或专属生命周期输入。
research_intent: 此前关于大段事实文本局部补丁的研究已产生一个需要重新分层的问题：规则源与事实源都包含 Markdown 或 YAML，但它们的权威边界、授权路径和发布机制不同。项目需要一份可独立复读的技术评估，避免把规范源误写成 Helper 受控事实更新，或把五类事实对象误写成同一种通用 patch。
recommendation_summary: 将共同能力限于局部读取、精确候选与差异审阅。规范源保持直接编辑后的语义治理和 Git 闭环；事实源保持 Helper 完整对象发布。若继续降低事实编辑成本，先以 Study 正文的严格局部请求试点，随后按 Spark、Pitfall、ADR、WorkCase 的字段所有权和生命周期逐类判断，不承诺全类型通用 patch、自动合并或 OT/CRDT。
change_log:
- signature:
    product_name: Cindy
    model_name: chatgpt/gpt-5.6-terra
    agent_runtime_name: claude-code
  summary: Human 要求将规则源与五类事实对象的不同局部编辑、治理和发布策略形成新的独立技术评估，并退休仅覆盖事实对象局部补丁问题的旧 Study。
  at: '2026-08-12T08:21:51.342725Z'
- signature:
    product_name: Cindy
    model_name: gpt-5
    agent_runtime_name: codex
  at: '2026-08-13T14:04:32.694549Z'
  summary: 为历史事实对象补齐权威 object_uid，并将同项目 legacy 关系目标改写为 object_uid。
- signature:
    product_name: Cindy
    model_name: gpt-5
    agent_runtime_name: codex
  at: '2026-08-13T15:03:57Z'
  summary: 将事实对象物理定位符迁移为完整 UUIDv7 的 Crockford Base32 编码。
object_id: study-01KZXN5TXNFV8T3AQS1QCPAQ8B
object_uid: 019ffb52-ebb5-7ed1-a1aa-f90dd9655d0b
fact_type_key: study
created_at: '2026-08-12T08:21:51.342725Z'
updated_at: '2026-08-13T15:03:57Z'
---

## 研究问题

当前项目已拥有两类不能混淆的权威载体：`specs/` 及授权附件构成规则源，`ldvh-base/` 中的 Spark、WorkCase、ADR、Pitfall、Study 构成事实源。两类源都需要编辑长 Markdown 或 YAML，也都可能面对并发、差异审阅和跨 clone 汇合；但它们的写入权、验证与正式生效条件不同。

本报告实际回答：规则源与五类事实对象应怎样分别处理局部编辑、并发冲突、草稿协作和正式发布；哪些底层编辑辅助可以共用，哪些授权、校验、Human Gate、审计和发布语义必须分开。

## 输入与边界

本报告于 2026-08-12 实际回读当前规则源中规则读取、规范变更、事实受控更新、五类事实类型及行动模板的定义，读取 study-0028，并观察当前 Helper 的事实对象读取、草案准备、候选发现和受控更新契约及实现。study-0028 中列出的 HTTP 条件请求、JSON Patch、LSP TextEdit、Git、CommonMark、Tree-sitter、Yjs、Automerge 与 ProseMirror 资料作为已记录的行业比较线索；本次环境对外部站点的实时抓取受网络策略阻断，未将其表述为本次逐页在线复核。

研究不实现新接口、不测量性能、不证明外部资料的当前性，也不决定项目规则、ADR、WorkCase 或 Human Gate。它只评估当前规则和实现下的分层边界，并把未被 Code 机械证明的规则源资格条件保留为缺口。跨 clone 的运行期写前协调、真实多人实时协作和远端服务均不在当前能力范围内。

## 关键发现

### 发现一：规则源与事实源应共享编辑辅助，而非共享发布协议

项目观察：规范源是人类控制的可强制规则边界。规则修改使用直接工作树编辑，并依据规范责任归口、最小充分性、独立复核、风险匹配验证、条件性 Human Gate 和 Git 闭环判断。规范读取 hash 或片段定位只证明当次读取/漂移，当前没有规范写 CAS、写锁或 Helper 事实更新端点。事实源则明确要求匹配类型的 Helper 操作、完整 after、整对象 fingerprint CAS、原子替换、精确回读和独立完整性审计。

项目启发：两边可以共用精确读取、版本绑定的局部定位、before/after diff、候选生成、范围保持证据和 stale 提示；这些工具不产生写权限，也不判断规则资格、语义冲突、授权或行动完成。规范源不得被描述为 Helper 受控事实写入，事实源也不得被直接文件编辑、Git merge 或 TextEdit 绕过。

对后续项目工作的直接影响：若要改善长文编辑，优先建设只读定位与候选审阅能力，并在其输出中明确 source kind、已展开范围、漂移和未验证范围；不要先建设统一 patch 发布 API。

### 发现二：五类事实共享完整对象发布主干，但不共享同一种局部操作

项目观察：当前五类事实载体都以完整对象作为受控更新和 CAS 的单位；Study 为 Markdown，其他四类为 YAML。WorkCase 有 phase、字段所有权、计划/结果版本、评审与批准等专属事务。ADR 的实质决定变化、Pitfall 的单一失败机制与状态冻结、Spark 的状态/关系与演进语义、Study 的研究问题/输入/发现边界，都使“不重叠文本”不能自动推导为“可独立提交”。

项目启发：完整对象 fingerprint、完整 candidate 校验、类型专属生命周期检查、原子替换、回读和审计继续作为五类事实的共同发布主干。局部请求若将来出现，只能由 Helper 在内存形成完整 after 后进入该主干；fragment hash 只能改善 stale 诊断，不能降低最终 CAS 或启用自动合并。

对后续项目工作的直接影响：任何扩展都按事实类型分别证明字段所有权、不可变边界、列表身份和生命周期不变量；不能把 YAML/Markdown 的共同文本形态当作通用 patch 的充分依据。

### 发现三：六类资产的首要优化点不同

项目观察：规则源的主要风险是局部文字改变规则责任、附件授权、关系图或 Human Gate 适用范围；Study 的主要痛点是长正文重复携带、相邻段误删与格式扰动；Spark、Pitfall、ADR 与 WorkCase则分别集中在演进/关系、成组经验更正、既有决定不可回写及复杂专属事务。

项目启发：规范源优先优化局部定位、精确候选 diff、影响分析和审阅，不赋予片段独立发布权。Study 是严格正文局部请求的首个候选，仍以整文档 CAS 发布。Spark 优先优化意图、摘要和演进草稿的候选表达；Pitfall 优先优化成组更正与适用性审阅；ADR 优先优化起草、依据补充和明确事实更正，实质决定变化仍新建或退出；WorkCase 优先优化专属操作的 phase 提示、完整候选和评审输入，而不是通用字段 patch。

对后续项目工作的直接影响：局部编辑能力的路线图应是“六类资产、六套语义策略；共同编辑辅助层；规范源治理路径与五类事实 Helper 发布主干分叉”。没有对象类型证明其不变量可完整编码时，维持完整 after 入口。

### 发现四：行业编辑与协作模式应停留在相称层级

外部资料线索与项目观察：资源级 optimistic concurrency 适合事实源当前的完整 fingerprint CAS；TextEdit 适合单编辑器缓冲区的局部意图；Git 三方合并适合跨 clone 的事后文本汇合与人工审查；JSON Patch 的 test/replace 只在路径、数组身份和字段不变量被明确规格化后才有价值；OT/CRDT 用于实时或离线草稿收敛，并不判断业务语义。

项目启发：规范源可使用直接编辑、IDE TextEdit、Git diff 和三方合并作为起草/汇合工具，但合并后仍需完整规则资格、责任复核、风险验证和必要 Human Gate。事实源的 Git merge 仅是跨 clone 事后汇合，合并后的 canonical 对象仍须重新读取、审计并由 AI/Human 审查。当前没有真实实时多人或离线自动合并需求，故不引入 OT/CRDT；将来如有需求，也只能先用于 Study/Spark 等非权威草稿层。

对后续项目工作的直接影响：将 `fingerprint_stale`、Git 冲突或草稿冲突明确交还为重新读取和重新形成意图的信号，不将无冲突文本合并表述为规则或事实语义已自动解决。

## 建议

### 建议一：先建设双源共用的只读编辑辅助

目标对象类型与创建判断：当长规范或事实对象的定位、审阅成本已实际阻塞工作，并且可在不改变写入权限的前提下交付时，创建 WorkCase。预期目标是按 source kind 提供精确局部读取、候选 diff、范围保持证据、已展开/未展开范围与 stale 反馈。

验收条件：规则源辅助不生成规范写许可、不替代资格/独立复核/Human Gate；事实源辅助不绕过 Helper、完整 after、CAS、回读或审计；标题、数组下标和裸 offset 不作为永久身份；任何无法准确定位或存在漂移的结果均明确报告而不模糊匹配。

### 建议二：事实写入若试点，仅先做 Study 正文严格局部请求

目标对象类型与创建判断：只有 Human 接受方向并准备安排实现时，创建 WorkCase。预期目标是在 Helper 内以不透明、版本绑定的片段引用表达 Study 正文的严格替换，然后重建完整 Study。

验收条件：任意整份 Study 变化都使旧引用失效；同批范围合法且不重叠；失败零写入；完整 Study 仍通过 frontmatter、五段正文、关系与引用校验，并经整文档 CAS、原子替换、精确回读和 `check-fact-integrity`。不引入模糊定位、自动 rebase、三方自动落盘或 CRDT canonical 发布。

### 建议三：按类型逐步改善其余四类事实的输入与审阅

目标对象类型与创建判断：在 Study 试点有实测收益且目标类型的字段所有权、不可变边界、数组身份和生命周期可完整表达时，按类型创建或更新 WorkCase；跨类型公共契约、兼容周期或版本语义需要长期决定时，再创建 ADR。

验收条件：Spark 的状态、关系与终态不被自由 patch；Pitfall 的状态变化不夹带正文自动合并；ADR 的实质决定变化不回写既有决定；WorkCase 继续执行 phase、版本、review 与 Gate 的专属事务；不能证明的字段维持完整 after。

### 建议四：把跨 clone 与实时协作留在显式分流中

目标对象类型与创建判断：若短分支/人工 Git 汇合已造成持续成本，先创建 Spark 记录冲突样本和所需保证；若后续需要长期公共策略，再由 ADR 决定。出现真实实时多人或长时离线协作时，另建 Spark 比较稳定块 ID、显式冲突 UI、OT 与 CRDT 草稿层。

验收条件：不把 Git merge 写成运行期并发保障；跨 clone 汇合后重新检查规则源或事实源的相应完整约束；OT/CRDT 草稿不替代规则源治理、事实 CAS 或 Human Gate；没有可复现痛点与必要样本时继续无需对象化。

## 后续分流

| 建议或未决问题 | 出现何种信号时创建或更新对象 | 继续无需对象化的条件 |
|---|---|---|
| 双源只读编辑辅助 | 长文定位、审阅或误改风险已实际阻塞，且不需要新增写权限 | 现有精确读取和普通 diff 已足够，或未能明确 source kind/影响范围 |
| Study 正文严格局部请求 | Human 接受实现方向，且完整对象 CAS 仍可保留 | Study 更新频率低，完整 after 的成本可接受，或冲突重读成本过高 |
| Spark、Pitfall、ADR、WorkCase 类型专属改进 | 每类已证明其字段/生命周期不变量可完整编码 | 仍主要是低频完整对象更新，或字段语义无法安全分离 |
| 跨类型公共补丁契约 | 至少两个类型的原型、冲突样本和兼容取舍已需要长期决定 | 只有单一 Study 窄接口，或没有实测收益 |
| 跨 clone 汇合策略 | Git 汇合后反复出现需人工重新判断的事实/规则冲突 | 短分支和人工审阅已足够，且无运行期远端协调需求 |
| 实时协作草稿 | 出现真实多人实时或离线自动合并需求 | 单会话编辑为主，偶发冲突可重新读取并重新形成意图 |
