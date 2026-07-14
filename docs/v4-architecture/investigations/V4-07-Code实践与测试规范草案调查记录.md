# V4 07 Code 实践与测试规范草案调查记录

> 记录性质：本文记录 `specs/07-Code 实践与测试规范.md` 草案的责任边界、身份选择、V3 输入处置和外部一手工程资料核验。本文不是规则源；外部资料、比较结论和本记录本身都不能直接约束 LDVH Code 或 tests。

## 1. 调查目的与范围

Human 已确认候选规范中文名为“Code 实践与测试规范”，并要求新版本不要继续形成“想到什么做什么”的巨型 Code，而应在 Code 实践层先完成系统规划。当前草案需要把该意图收敛为稳定规则，同时避免：

1. 把 5000 行写成脱离上下文的全局失败阈值；
2. 用固定目录、架构风格、runner、profile 或测试金字塔代替实际规划；
3. 重新定义 Helper 外部契约、领域 Schema 或环境 adapter；
4. 把外部工程资料、Code 或 tests 变成第二规则源；
5. 恢复 V3 的巨型 facade、diagnostic 闭集、旧 runner/profile/fixture 或兼容义务；
6. 把 Code 实现规划和测试拆成两份需要重复读取、同步维护的横向规范。

初稿阶段只新建 07 草案及本文。后续集中审核为了使候选术语在同一 Working Tree 中保持一致，已同步修改 active 03、双语术语表和相应架构记录；仍未修改 Code、tests、`web/`、`icons/` 或归档。

## 2. 当前规则源与历史输入

### 2.1 直接规范依据

07 的直接 `basis` 包含 `ldvh-root`。00 已经定义：

1. Code 是五类构成要素之一；
2. Code 提供解析、索引、聚合、校验、测试、上下文压缩和受控写入等确定性能力；
3. Code 在实现层实现 Helper CLI，但 Helper 在架构层不是 Code 的普通附属能力；
4. 测试和 Code 输出只能支持其实际证据范围内的声明。

新增当前 Code 实现规划定位规则后，07 同时直接依据 `source-of-truth-traceability`：它使用该规范对 Working Tree 当前内容、未提交或未跟踪文件、`HEAD` 与 Git history 的边界，避免把 commit 变成当前规划和进行中实现被消费的前置条件。

`specification-model-foundation` 规定草案身份、结构和 `basis` 判断，但这是所有普通规范共同接受的治理约束，不是 07 工程语义的直接依据。Helper、领域规范、具体 Schema 和环境契约是相应实现增量的输入前置，不是 07 共同工程要求自身的规范依据。

### 2.2 已通过的责任边界

`docs/v4-architecture/V4-Specs-责任重新审计记录.md` §3.4 已确认 07 的独有责任：

1. 首次实现前明确模块责任、依赖方向、接口、Schema 维护责任和测试策略，并随改变同步更新；
2. 定义模块责任、允许依赖和公共接口/Schema 的唯一维护责任；
3. 定义风险驱动测试、正例、反例、边界、失败覆盖和测试同步；
4. 定义内部错误传播、诊断定位和可观察性；
5. 按责任、耦合、复杂度、变更频率、可测试性和可导航性判断重构，不采用无上下文全局行数上限；
6. 核验外部工程资料的来源和 LDVH 适用性，再由当前规则源正式吸收；
7. 处理 Code 实现规划与真实实现偏移。

该审计同时明确：具体目录、文件、命令、runner、fixture、单次计划、Helper 外部字段、领域 Schema 语义和环境协议不进入 07。

### 2.3 V3 覆盖输入

`docs/v4-architecture/investigations/V3-设计覆盖与V4下游审核清单.md` 对 07 草案保留以下问题输入：

1. 内部模块、诊断和 tests 归 Code 实践；公开 CLI 和机器结果归 Helper，adapter 归环境，领域行为归具体来源；
2. 测试应风险驱动，覆盖正反例、失败边界，并如实保留未验证范围；
3. 多入口共享的确定性逻辑可以进入共享 Code 能力，但未知输入不得猜测；
4. V3 单体模块、巨型 facade、两个过重 shim、旧路径、旧诊断闭集和旧 runner/profile/fixture 不直接继承。

这些内容只证明 V4 应重新处理相应问题，不证明 V3 实现或测试已经适合 V4。

## 3. 名称与职责标识符判断

### 3.1 标题

- Human 确认中文标题：`Code 实践与测试规范`
- 建议并采用的英文标题：`Code Practices and Testing Specification`

该标题把测试责任显式呈现出来，避免“实践”被误读为只管编码风格；正文仍把首次实现前规划、持续重构和测试视为同一 Code 工程责任。

“Code”已经是当前双语术语；“实践与测试 / Practices and Testing”在标题中使用自然描述，不建立新的 LDVH 核心术语或机器表示，因此标题本身不要求修改双语术语表。正文新增的 `Code 实现规划 / Code Implementation Plan` 已另行按 01 §12 审核并登记。

### 3.2 `spec_key` 比较

| 候选 | 稳定性判断 |
|---|---|
| `code-engineering-practices` | 覆盖首次实现前规划、模块与接口维护、诊断、重构和测试这一完整持续责任；不依赖当前标题是否显式写出“测试”，并已在此前责任与命名审计中完成独立复核 |
| `code-practices-testing` | 能镜像当前标题，但更容易被理解为“Code practices”与横向“testing”两项并列责任；如果未来只调整标题措辞，key 也容易显得被标题绑定 |

结论：草案使用 `code-engineering-practices`。

理由不是因为旧候选已经 active——它从未取得 active 身份，而是因为 01 要求职责标识符表示稳定责任而不是标题镜像。本次标题变化只是把原责任中始终存在的测试显式化，没有新增、拆分或转移规则对象。若未来 Human 真正决定把测试拆成独立横向责任，必须重新执行 01 §13，不能靠改 key 暗示拆分已经发生。

## 4. 外部一手资料核验

观察日期为 2026-07-12。只记录公开页面能够直接支持的内容；付费标准未读取的正文不作推断。

| 来源与分类 | 当次可确认内容 | 对 07 的参考价值 | 没有采用的内容 |
|---|---|---|---|
| [ISO/IEC/IEEE 42010:2022 — Architecture description](https://www.iso.org/standard/74393.html)，国际标准，Edition 2，2022-11，状态 Published | 公开摘要规定架构描述的结构与表达要求，同时明确不规定创建和管理架构描述的方法、表示法、工具、格式或介质 | 仅作间接类比：支持可检查结构说明与不固定表达工具可以并存；它不直接要求 LDVH 在实现前建立 Code 实现规划 | 未声称 07 符合该标准，也未复制其 viewpoint、model kind 或一致性模型 |
| [SWEBOK Guide V4.0a](https://www.computer.org/education/bodies-of-knowledge/software-engineering)，IEEE Computer Society 共识性知识指南；观察日入口页面以 SWEBOK V4.0 概称，当前下载版标示 V4.0a | 官方页面说明其汇总 generally accepted、consensus-driven knowledge，并以 18 个知识领域组织当前软件工程知识 | 支持确认软件设计、架构、测试、安全与工程运营是具有可靠出处的工程关注领域，但不直接决定 LDVH 的具体规则 | SWEBOK 不是 LDVH 规则源；未把全部知识领域、术语或推荐做法整体引入 07，也不把页面摘要未展开的细节写成已核验规则 |
| [ISO/IEC 25010:2023 — Product quality model](https://www.iso.org/standard/78176.html)，国际标准，Edition 2，2023-11，状态 Published | 公开摘要说明九类产品质量特性可用于要求、设计目标、测试目标、质量控制、验收条件和度量 | 支持按具体质量风险选择设计与测试目标，而不是只看代码行数或覆盖率 | 未复制九类特性形成 LDVH 闭集，也未建立统一质量分数或门槛 |
| [ISO/IEC/IEEE 29119-2:2021 — Test processes](https://www.iso.org/standard/79428.html)，国际标准，Edition 2，2021-10，状态 Published | 公开摘要说明其测试过程可用于治理、管理和实施软件测试，并适用于各种软件生命周期模型 | 只确认该标准声明适用于各种软件生命周期模型；“测试必须与每次实现变化同步”是 LDVH 基于自身风险作出的内部规则选择，不是该摘要的直接要求 | 未声明采用完整 29119 流程、文档模板、角色或一致性要求 |
| [ISTQB CTFL Syllabus v4.0.1](https://istqb.org/wp-content/uploads/2024/11/ISTQB_CTFL_Syllabus_v4.0.1.pdf)，官方认证教学大纲，2024-09-15 | 官方大纲说明产品风险分析可影响测试范围、测试层次、测试类型、技术、覆盖、投入和优先级 | 直接支持“风险影响测试检查范围与深度”的候选工程要求；07 不复制其 test levels | ISTQB 大纲不是国际标准；未复制其完整术语、流程、角色或认证要求，也未把风险公式写成强制模型 |
| [NIST SP 800-218 SSDF v1.1](https://csrc.nist.gov/pubs/sp/800/218/final)，美国 NIST Final Publication，2022-02 | 官方摘要将安全实践描述为可整合进不同 SDLC 的高层实践，并强调降低漏洞、影响和复发根因 | 支持在适用时把安全、信息泄露和复发根因纳入风险与重构考虑 | 该来源只直接覆盖安全软件开发；观察日另有 v1.2 draft，本记录只采用已发布 final v1.1，不把 draft 内容写入当前结论，也未把 SSDF 全套实践扩张为所有 LDVH Code 的通用流程 |
| [Google Engineering Practices — Small CLs](https://google.github.io/eng-practices/review/developer/small-cls.html)，组织一手工程指南 | 页面明确小变更的“小”是概念聚焦而非简单行数，并建议逻辑变化同步测试、重构前先建立测试保护 | 支持拒绝“单一行数自动裁决”，并支持重构与测试保护相联系 | Google 内部实践不是行业统一标准；未引入其 CL 数字建议、评审流程或“所有变更必须同一方式处理” |
| [Google Engineering Practices — What to look for in a code review](https://google.github.io/eng-practices/review/reviewer/looking-for.html)，组织一手工程指南 | 页面要求按变化选择 unit/integration/end-to-end tests，并检查测试在 Code 被破坏时是否真正失败；同时提醒 tests 也是需要维护的 Code | 支持按变更选择适当检查范围、测试缺陷敏感性以及 tests 自身可维护性 | 未把 Google review 规则、语言风格或组织角色引入 LDVH |

本轮 07 集中审核在同一观察日重新读取上述官方入口：三个 ISO 页面仍分别标示 42010:2022、25010:2023 和 29119-2:2021；IEEE Computer Society 入口页面以 SWEBOK V4.0 概称，当前下载版标示 V4.0a；ISTQB v4.0.1 PDF 仍可取得；NIST v1.1 仍为 Final，v1.2 是 2025-12-17 发布且评论期已经结束的 Initial Public Draft，不作为当前规则依据；Google 两页仍明确“小”不是硬性行数规则、测试应随变化选择且应能在被保护行为破坏时失败。上述复核只确认本表实际采用的有限内容，不表示外部来源整体被 LDVH 采用。

### 4.1 来源结论边界

上述来源共同说明模块化、接口边界、质量风险、持续测试和测试敏感性是有可靠出处的工程关注点，但没有一份来源能够直接决定 LDVH 的：

1. 模块列表或目录布局；
2. 唯一架构风格或层数；
3. 5000 行失败阈值；
4. 固定测试金字塔、覆盖率百分比或各层数量；
5. runner、profile、fixture、命令和报告格式；
6. Helper、事实、行动模板或环境的外部契约。

因此 07 只吸收与 LDVH 已审定问题和 V1–V8 净价值相符的稳定要求。吸收后的规则效力来自 07 在未来转为 active 后的正文，而不是上述链接。

## 5. 草案关键设计选择

### 5.1 系统规划进入 Code 实践责任

草案要求在首次实现或实质改变模块、依赖、接口、Schema、诊断和测试策略前，先形成相应 Code 实现规划。规划至少连接：

1. 当前有效来源与本次实现范围；
2. 模块责任和不承担内容；
3. 允许依赖、调用方向和禁止绕行；
4. 接口与 Schema 的语义来源、Code 维护责任和消费者；
5. 副作用、错误与诊断边界；
6. 风险、测试检查范围、真实依赖/test double 和未验证范围；
7. 设计缺口、暂缓边界和重新评估条件。

规划必须先于相应实现并与变化同步，解决“事后给既成 Code 补一张合理化架构图”的问题。草案不规定规划文件名和目录；动态实施步骤、当前进度和具体文件仍属于实现说明或其它适当载体，不进入 07 规则正文。

### 5.2 大文件是信号，不是唯一判断

Human 提出的单个 Code 超过 5000 行是明确的风险信号。草案把它纳入“规模已经妨碍 Human/AI 理解和导航”以及“项目局部阈值或同类偏离”的重构评估入口，但不把 5000 写成全局失败线。

实际评估同时检查责任是否混杂、依赖是否循环或绕行、接口/Schema 是否重复、测试能否隔离、失败能否定位、变更与回归是否集中。这样既能阻止继续向巨型模块无计划叠加，也不会把内聚、生成或简单表驱动内容机械拆碎。

### 5.3 测试不形成第二横向规范

草案定义：

1. 风险决定测试深度、层次和真实依赖范围；
2. 局部组件行为、接口契约、真实组合、公开入口贯通四类 LDVH 本地检查范围；它们只帮助表达真实依赖和证据边界，不对应或替代 ISTQB 的 component、component integration、system、system integration、acceptance test levels；
3. 回归、特征、基于性质、模糊、性能、安全、并发和兼容性测试是可以跨检查范围使用的目的或技术；
4. 正例、反例、边界、失败、部分结果和诊断按风险选取；
5. test double、静态检查、覆盖率、skip 和 flaky 的证据边界；
6. Code、接口、Schema、诊断变化与 tests 同步。

具体规则是否成立仍由各来源规范定义；真实环境触发仍由环境责任定义。07 只管理 Code 如何设计 tests 和使用测试证据。

### 5.4 无附件

当前没有稳定、已证明需要独立维护的允许依赖矩阵、接口登记或度量阈值，因此 07 使用 `authorized_attachments: []`。未来只有正文先定义相应对象和边界，且结构化附件比实现说明具有明确净价值时，才重新按 01 判断。

## 6. 明确未采用

本轮没有采用：

1. Clean Architecture、Hexagonal Architecture、DDD、微服务或其它固定架构风格；
2. 固定 package/module/directory 层次；
3. “一个模块只能一个函数/类”或“所有循环都用同一方法消除”；
4. 全局 5000 行、圈复杂度或依赖数失败线；
5. 固定测试金字塔、70/20/10 等比例或统一覆盖率门槛；
6. V3 runner、profile、fixture、diagnostic code、repair/runtime 闭集；
7. 把 Code 实现规划、测试报告或外部资料登记为规则源或事实模型；
8. 对尚未 active 的 Helper、事实类型、行动模板或 adapter 字段作实现承诺。

## 7. 草案自检

当前草案已经检查：

1. YAML 固定为 `spec_id: "07"`、`status: "active"`、`parent_spec: "ldvh-root"`、`relation: "refines"`、`basis: ["ldvh-root", "source-of-truth-traceability"]`、无附件；
2. 中文标题与 Human 决定一致，英文标题自然对应；
3. `spec_key` 按稳定责任而非标题镜像选择；
4. 固定头部与固定尾部齐全，H2 连续；
5. Code 实现规划、模块、依赖、接口、Schema、诊断、重构、风险驱动测试、测试检查范围与证据边界均已覆盖；
6. 未定义 Helper 外部契约、具体领域语义、环境协议、目录、算法、runner 或 profile；
7. 5000 行只作为代表性评估信号；
8. 外部资料全部保留来源身份、版本/日期、适用范围和未采用边界；
9. 没有声称本文是行业最佳实践集合，也没有声称 V4 Code/tests 已实现或通过验证。

本文已经完成主执行检查、独立术语复核和架构边界复核。复核提出的当前规划定位、强制 Code tests 与未验证范围、外部来源精度和记录时态问题已经修正；修正后最终复核为 0 blocker、0 major、0 minor。07 与 `Code 实现规划 / Code Implementation Plan` 已完成原子激活；该状态不表示 Code/tests 已经开始实现或通过验证。
