---
title: LDVH 大段文本受控写入的局部补丁方案评估
status: retired
report_kind: external_research
urls:
- ref: https://www.rfc-editor.org/rfc/rfc5789.html
  title: 'RFC 5789: PATCH Method for HTTP'
  summary: 确认局部修改请求、失败原子性及结合条件请求防止并发冲突的标准语义。
- ref: https://www.rfc-editor.org/rfc/rfc6902.html
  title: 'RFC 6902: JSON Patch'
  summary: 评估结构化元数据的路径级操作、顺序执行与失败终止语义。
- ref: https://www.rfc-editor.org/rfc/rfc7396.html
  title: 'RFC 7396: JSON Merge Patch'
  summary: 核对 null、对象和数组替换限制，说明其不宜作为通用受控写入契约。
- ref: https://www.rfc-editor.org/rfc/rfc9110.html#section-13.1.1
  title: 'RFC 9110 §13.1.1: If-Match'
  summary: 确认强条件匹配可避免 lost update，并保留整对象指纹作为最终闸门。
- ref: https://github.com/microsoft/language-server-protocol/blob/gh-pages/_specifications/lsp/3.18/types/textEdit.md
  title: 'Language Server Protocol 3.18: TextEdit'
  summary: 评估范围加新文本的严格正文替换和批量编辑不得重叠。
- ref: https://github.com/microsoft/language-server-protocol/blob/gh-pages/_specifications/lsp/3.18/types/textDocumentEdit.md
  title: 'Language Server Protocol 3.18: TextDocumentEdit'
  summary: 确认文本编辑可携带文档版本前置条件并拒绝版本不匹配。
- ref: https://git-scm.com/docs/git-apply
  title: 'Git Documentation: git-apply'
  summary: 评估统一 diff 的上下文匹配、检查和三方回退；适合预览或显式冲突处理。
- ref: https://github.com/google/diff-match-patch/wiki/API
  title: diff-match-patch API
  summary: 核对近似匹配与逐块成功状态；其语义不符合受控事实写入的 fail-closed 要求。
- ref: https://spec.commonmark.org/0.31.2/
  title: CommonMark Specification 0.31.2
  summary: 界定 Markdown 标题与块结构，并确认标题没有稳定唯一身份。
- ref: https://tree-sitter.github.io/tree-sitter/using-parsers/3-advanced-parsing.html
  title: 'Tree-sitter: Advanced Parsing'
  summary: 评估增量解析和变更范围定位；用于识别原文边界而非全量重排文本。
- ref: https://docs.yjs.dev/api/document-updates
  title: 'Yjs Documentation: Document Updates'
  summary: 评估可交换、结合、幂等的增量更新；只在实时或离线多方协作时具有相称收益。
- ref: https://automerge.org/docs/reference/concepts/
  title: Automerge Concepts
  summary: 评估 CRDT 的并发变更与合并语义及其额外文档状态成本。
- ref: https://prosemirror.net/docs/guide/#collab
  title: 'ProseMirror Guide: Collaborative Editing'
  summary: 核对中央排序、版本号和客户端变换；作为未来草稿层参考。
research_question: 在保留 LDVH 单对象 CAS、完整校验、原子落盘和写后审计的前提下，如何降低大段 Markdown 与结构化事实更新必须提交完整对象所带来的上下文、误删和格式扰动成本；局部补丁、定位及并发模型中哪些最适合当前项目？
abstract: 本报告于 2026-08-11 对照 HTTP PATCH/条件请求、JSON Patch、LSP TextEdit、Git patch、Markdown 解析与 CRDT/协作编辑的一手规范和官方文档。结论是把请求语义粒度与持久化发布粒度分开：客户端只提交严格局部操作，Helper 在当前完整对象上应用后仍执行现有 Schema、状态转换、引用、CAS、原子落盘、精确回读与完整性审计。元数据采用 JSON Patch 风格并补充稳定 ID 的类型化数组操作；Markdown 正文采用绑定文档与片段指纹的 TextEdit 风格替换。统一 diff、模糊匹配、三方合并和 CRDT 不宜成为首版规范接口。未做性能基准或实现原型，建议仍需 Human 决定后由 WorkCase 承接。
research_intent: 当前受控更新以完整事实对象作为提交输入，对短对象清晰可靠，但对长篇 Study 正文会放大上下文传输、无关文本复述、误删相邻内容和序列化扰动。Human 要求联网调查更友好的处理方式；本研究为是否增加局部更新能力、怎样不削弱现有事实边界与并发安全提供可复读依据。
recommendation_summary: 建议分两步试行：先增加只读片段定位与 Study 正文严格补丁，片段引用绑定完整文档指纹和片段指纹，内部使用 UTF-8 字节半开区间，操作不重叠且任一失败零写入；再增加 JSON Patch 风格结构化字段操作，禁止 Code 托管字段，对列表优先使用稳定 ID 的类型化操作。两步都在内存重建完整候选对象后沿用完整校验、CAS、原子发布、精确回读和完整性审计，并保留整对象更新。除非出现实时多人或离线合并需求，否则不引入 CRDT/OT。
change_log:
- signature:
    model_id: gpt-5
    agent_workbench: Cindy
  session_id: cindy-study-local-patch-research-20260811
  summary: Human 明确要求创建 Study：记录大段文本受控写入的外部方案调研、适用边界与建议分流。
  at: '2026-08-10T19:43:14.082563Z'
- signature:
    product_name: Cindy
    model_name: chatgpt/gpt-5.6-terra
    agent_runtime_name: claude-code
  summary: Human 决定新建双源、六类资产技术评估并退休本报告；本报告保留历史内容，仅退出当前研究入口。
  at: '2026-08-12T08:24:05.240745Z'
- signature:
    product_name: Cindy
    model_name: gpt-5
    agent_runtime_name: codex
  at: '2026-08-13T14:04:26.850121Z'
  summary: 为历史事实对象补齐权威 object_uid，并将同项目 legacy 关系目标改写为 object_uid。
disposition_summary: 本报告保留为仅讨论事实源局部补丁的历史研究。其后续调研已将规则源与五类事实对象的不同编辑、治理和发布边界独立展开为 study-0030；旧报告不通过 supersedes 关系替代该新研究。
object_id: study-0028
object_uid: 019ffb52-ebb5-774d-90a5-e23d37bab4a3
fact_type_key: study
created_at: '2026-08-10T19:43:14.082563Z'
updated_at: '2026-08-13T14:04:26.850121Z'
---

## 研究问题

当前项目需要这轮报告，是因为受控写入把完整事实对象作为更新输入：它对短对象便于审阅，但长篇 Markdown 正文每次都要重新携带大量无关文本，增加模型上下文、请求体、误删相邻段落和格式扰动成本。Human 于 2026-08-11 要求联网调查更友好的处理方式。

本报告实际回答：在不削弱 LDVH 现有单对象 CAS、完整 Schema 与状态转换校验、原子落盘、精确回读和完整性审计的前提下，应怎样定义局部更新请求；结构化元数据和 Markdown 正文分别适合什么补丁表达；哪些并发、定位与协作模型当前不值得引入。

## 输入与边界

本报告于 2026-08-11（Asia/Shanghai）实际读取 RFC Editor、Microsoft LSP、Git、CommonMark、Tree-sitter、Yjs、Automerge 与 ProseMirror 的规范或官方文档。HTTP PATCH、If-Match、JSON Patch 与 Merge Patch 提供局部请求、失败原子性、路径操作和并发前置条件；LSP TextEdit 提供严格范围替换；Git apply 与 diff-match-patch用于评估上下文补丁及模糊匹配；CommonMark 与 Tree-sitter 用于评估 Markdown 定位；Yjs、Automerge 与 ProseMirror 用于判断协作模型的适用门槛。

研究只比较接口与一致性模型，没有实现原型、性能基准、故障注入或可用性测试，也未测量当前 Helper 的文件 I/O 占比。结论适用于“单个事实对象通常由单个 AI/Human 会话受控更新，偶有并发”的现状，不覆盖实时多人编辑、长时间离线分支自动合并或数十至数百 MB 单文件。各来源解决的层次不同，没有直接冲突；本报告对 LDVH 的选择是项目推断，不是外部来源直接规定。

## 关键发现

### 发现一：局部请求与整文件原子发布可以同时成立

外部观察：RFC 5789 把 PATCH 定义为对资源应用修改指令，并要求成功前原子应用完整补丁；RFC 9110 的 If-Match 用强验证器阻止基于陈旧版本的写入。两者都没有要求底层按片段持久化。

项目启发：Helper 可以只缩小调用方提交的语义范围：读取完整对象并核对基准指纹，在内存应用局部操作，形成完整候选对象，再执行现有 Schema、状态转换、引用闭包、CAS、原子替换、精确回读与完整性审计。完整对象仍是事实和验证单位。

对后续项目工作的直接影响：Human 采纳后应新建一个 WorkCase 实现首版片段读取与正文补丁；无需先改事实模型或创建 ADR，现有整对象更新继续作为兼容入口。

### 发现二：结构化元数据适合 JSON Patch 风格，但列表需要领域约束

外部观察：RFC 6902 提供按 JSON Pointer 路径顺序执行的 add、remove、replace、move、copy、test，任一操作失败时整体失败。RFC 7396 的 Merge Patch 用 null 表示删除，无法表达目标值为 null，并把数组整体替换。

项目启发：标题、摘要、状态等字段适合 JSON Patch 风格操作，并用全对象指纹作最终 CAS。object_id、fact_type_key、created_at、updated_at 等 Code 托管字段必须在路径层禁止。relations、urls、work_items 等列表不宜长期依赖数字下标；有稳定业务 ID 时应按 ID 提供类型化操作，否则要求整字段替换并显式 test 前值。

对后续项目工作的直接影响：正文补丁稳定后，可更新同一 WorkCase 或新建第二个 WorkCase承接结构化补丁；验收覆盖托管字段拒绝、未知路径、列表错位、test 失败及任一失败零写入。只有跨五类事实的公共契约需要长期确定时才创建 ADR。

### 发现三：Markdown 正文宜采用严格 TextEdit，而不是模糊 diff

外部观察：LSP TextEdit 用“范围 + 新文本”表达替换并要求同批编辑不重叠；TextDocumentEdit 可绑定文档版本。Git patch 依赖上下文并可三方回退；diff-match-patch 会尝试近似匹配。

项目启发：片段读取应返回不透明 fragment_ref、document_fingerprint、fragment_fingerprint 与精确文本；更新只提交 replacement 和前置条件。Helper 内部将片段解析为 UTF-8 字节半开区间，拒绝越界、重叠、非编码边界、文档陈旧或片段已变更。任何操作失败都零写入，不自动漂移到相似段落。统一 diff 只作为预览、导入或显式冲突处理格式。

对后续项目工作的直接影响：首版 WorkCase 应优先实现 read-fact-fragments 与 patch-study-body，并提供 stale_base、fragment_changed、overlap、forbidden_path、invalid_transition、schema_invalid 等稳定错误分类；模糊应用和自动三方合并不进入首版。

### 发现四：标题路径只适合定位入口，不能充当永久身份

外部观察：CommonMark 定义标题与块的解析，但标题可重复且没有内建稳定身份。Tree-sitter 支持增量更新语法树和定位变化范围，并不要求重写源文本。

项目启发：首版可用 Markdown 解析器识别 H2/H3 或段落边界，再返回绑定当前 document_fingerprint 的不透明 fragment_ref。解析器只确定原文区间，不通过 AST stringify 重排整篇正文。只有明确要求在无关段落并发变化后继续重放旧引用时，持久块 ID 才可能值得其迁移和唯一性成本。

对后续项目工作的直接影响：首版 WorkCase 不修改 Markdown Schema 增加块 ID；验收需证明重复标题不误定位、引用跨文档版本会拒绝、片段之外字节不变。若无关并发冲突频繁，再创建 Spark 评估稳定块 ID。

### 发现五：CRDT/OT 只在实时或离线协作需求成立时划算

外部观察：Yjs 的增量更新可交换、结合且幂等；Automerge 合并并发变更；ProseMirror 用中央顺序、版本号和变换处理协作编辑。这些模型也引入文档状态、操作历史、同步或冲突呈现职责。

项目启发：当前痛点是受控 API 对长文本提交过重，不是实时多人编辑。严格片段补丁加整对象 CAS 已覆盖主要需求。若以后确有实时或离线协作，应把 CRDT/OT 放在草稿层，明确发布时生成 Markdown 快照并经过现有受控校验；CRDT 状态不能替代事实源。

对后续项目工作的直接影响：当前不创建 CRDT/OT WorkCase 或 ADR。监测信号是同一 Study 高频并发、离线编辑必须自动合并、严格 CAS 冲突率持续影响工作；信号出现时先创建 Spark 澄清产品需求。

### 发现六：局部补丁降低交互成本，不消除超大文件的物理重写

外部观察：PATCH 与 TextEdit 描述修改语义，不保证底层存储按块更新；普通 Markdown 的安全发布仍可能生成并替换完整内容。

项目启发：局部接口能减少模型上下文、请求负担和非目标内容扰动，但最终磁盘写入仍可能是整文件。若单对象达到数十或数百 MB，真正降低 I/O 需要分块存储、内容寻址或数据库页级更新，这会改变“一文件一对象”的事实模型。

对后续项目工作的直接影响：首版 WorkCase 不承诺减少磁盘写放大，只测量请求字节、模型输出量、非目标字节保持和冲突行为。只有基准证明 I/O 成为主要瓶颈时，才新建 Study/ADR 比较分块存储。

## 建议

### 建议一：创建正文片段补丁 WorkCase

目标对象类型与创建判断：Human 接受方向后新建 WorkCase；当前尚未创建。预期目标是增加 read-fact-fragments 与 patch-study-body，读取返回不透明片段引用、文档指纹、片段指纹和精确文本，写入只提交替换文本与前置条件。

验收条件：同批范围合法且不重叠；任一 stale_base、fragment_changed、越界、编码边界、结构、Schema、状态转换或引用校验失败均零写入；成功后目标范围外字节不变；继续经过完整对象校验、CAS、原子落盘、精确回读和 check-fact-integrity；现有 update-fact-object 不变。首版引用跨任意文档变化即失效，以多一点冲突换取明确语义。

### 建议二：正文方案稳定后承接结构化字段补丁

目标对象类型与创建/更新判断：建议一的 WorkCase 范围可控时更新它；协议与测试面明显独立时新建第二个 WorkCase。预期目标是提供 JSON Pointer 风格字段操作，并为有稳定 ID 的列表提供类型化操作。

验收条件：托管字段和未知路径 fail-closed；操作有序且任一失败零写入；数字下标错位有拒绝或 test 防护；完整对象 CAS 和既有校验仍为最终闸门。JSON Merge Patch 不作为通用接口。

### 建议三：仅在公共契约取舍成立时创建 ADR

目标对象类型与创建判断：当前不创建 ADR。若原型证明局部补丁要成为五类事实的长期公共契约，或必须在严格版本绑定与无关变化后重放之间作项目级选择，再创建 ADR。

预期目标是决定补丁寻址、版本语义、稳定块 ID、错误分类和兼容周期。验收条件是已有原型数据、冲突样本、迁移成本和替代方案比较；ADR 不能用本 Study 代替 Human 决定。

### 建议四：暂不对象化模糊合并与实时协作

目标对象类型与创建判断：不创建 WorkCase/ADR；只有监测信号出现才创建 Spark。预期目标是在保持实现简单的同时避免无证据扩张。

验收条件：首版统计严格 CAS 冲突率、用户重试成本与真实多人/离线需求；无持续痛点则继续无需对象化。信号成立后，Spark 先区分稳定块 ID、显式三方冲突 UI、OT 与 CRDT 草稿层。

## 后续分流

| 建议或未决问题 | 出现何种信号时创建或更新对象 | 继续无需对象化的条件 |
|---|---|---|
| 正文片段补丁 | Human 接受方向并愿意安排实现时，新建 WorkCase | 继续只用整对象更新，或长文本更新频率不足以抵消新接口成本 |
| 结构化字段补丁 | 正文原型稳定且元数据更新仍有明显复述或数组误改成本时，更新同一 WorkCase或新建独立 WorkCase | 元数据足够短且错误率低，或列表无稳定身份 |
| 跨类型公共契约 | 扩展至五类事实且兼容或并发语义需要长期统一时，创建 ADR | 仅保留 Study 正文的窄接口并随实现迭代 |
| 稳定块 ID | 无关段落变化频繁使片段引用大量失效时，创建 Spark | 冲突少且重新读取成本可接受 |
| 三方合并、OT 或 CRDT | 出现真实实时多人、长时间离线编辑或严格 CAS 冲突持续阻塞时，创建 Spark | 单会话编辑为主，偶发冲突可重读重提 |
| 分块存储 | 基准证明数十/数百 MB 对象整文件 I/O 是主要瓶颈时，新建 Study，随后由 ADR 决策 | 当前瓶颈主要是上下文和请求，而非磁盘发布 |
