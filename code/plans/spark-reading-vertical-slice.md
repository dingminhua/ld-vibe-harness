# Spark 完整语义与分层阅读纵切实现规划

## 1. 目标与规则边界

本规划覆盖 Spark 从当前事实源、Helper 候选读取到 Web 详情阅读的同一条纵向能力。直接来源是 00、02、04、05、07、08、20–24 与 31；其中 20 定义 Spark 语义，05/04 定义候选与 Helper 共同接口，02 定义实际 worktree 管辖边界，08 定义 Web 独立读取与 direct capture，07 定义实现规划和测试，21–24 是共享 `cards[]` 的相邻类型消费者，31 定义 AI 创建审核。00 是最高原则且不由本增量修改。

本增量实现三项已经由来源明确的责任：Spark `summary` 保存完整当前语义；Helper F2 只返回最小字段与有界原样摘要摘录，选中后以稳定引用进入 F3；Web 独立读取当前完整事实对象并将 `summary` 作为 Markdown 完整展示。`source_refs` 只承担来源定位、版本与观察边界，不得改名、推导或投影为“意图”。Web direct capture 继续使用 Human 已确认的 `title/description/priority` 三字段，其中 `description` 经 08 唯一定义的 NFC 与两端 White_Space 规范化后、不作额外语义改写地成为完整 `summary`，不新增 `intent` 字段。

本规划不定义固定写作模板、关键词、最小字符数或全局行动白名单，不让 Helper 候选卡、Web DTO、UI 或缓存反向限制事实正文。它不覆盖其它事实类型的阅读改造，不覆盖 WorkCase，不决定既有 Spark 的删除、合并或状态迁移，也不授权批量改写对象。

实现起点 commit 为 `6e2b8669f7e52e6d8f0ec5c3ff36ef2519ad7e08`。开始规划时，Working Tree 已包含 05/08/20/31 的 Spark 完整摘要与有界摘录来源草案、`ldvh-base/sparks/spark-0005.yaml` 的未完成语义更新，以及 Web Spark 详情、关联投影、样式和 tests 的未提交/未跟踪变化；本规划承接其中仅与 Spark 纵切直接相关的部分。其它 Specs、规范上下文 Helper、通用 Web、WorkCase 页面和审计文档变化不在本规划范围。

本规划与 `specification-context-reading.md` 没有实现责任重叠；只共同消费 Helper 的共享请求、响应与 operation runtime。它消费 `full-v4-working-tree-evidence.md` 的验证入口但不修改 runner 或证据模型。它与 `codex-context-recovery.md` 共同涉及 F1 `cards[]`：本规划更具体地维护 05 新增的 `excerpts` envelope 与 Helper producer，恢复规划继续维护分页、binding 和有界交付；`code/ldvh/hooks/context_recovery.py` 忽略 F1 空 `excerpts`，其聚焦 tests 与 byte-budget fixtures 负责兼容回归。事实对象内容审核以 20/31 为来源，不能由本规划取得语义决定权。

本次可观察 Web 变化已经由当前 Human 对 Spark 的连续明确指令覆盖：作用范围仅为 Spark；变更前是 Human source locator 被另名为“意图”、摘要被自动断句、三行输入框只提示“记录信息”，变更后是来源仍在“关联/外部输入”中显示、完整 `summary` 原 Markdown 直接渲染、三字段输入框提示多段完整摘要；验收依据是来源身份不丢失、正文不改写、Web 不使用 Helper 的 F2 预算。当前 Human 也已明确要求按该方向推进，并要求以 00 判断和由 subagent 审核。`spark-0005` 的授权只覆盖把未提交摘要中错误的 Web Helper-first 判断更正为上述边界并回读；不覆盖状态、关系、删除、合并或其它 Spark。

### 1.1 来源门槛、Gate 与停止审核

| 来源 | 当次适用与验证门槛 | Human Gate / Stop 结论与恢复 |
|---|---|---|
| 00 | 保持 AI/Human/Code 分工、事实源、风险匹配验证和 V1–V8；以差异、subagent 审核和真实 tests 证明当次范围 | 不改变 00 或基本职责；本纵切也不触及 01 定义的 L0–L4。若出现第二权威、固定许可矩阵或证据越权则停相应实现，删除越权机制后恢复 |
| 02 | 候选扫描继续绑定唯一 governed project 与实际 worktree/common-dir | 不改变管辖接口；若真实边界不能形成则沿用 unavailable/partial，不能扩大扫描，边界恢复后重试 |
| 04 | `cards[]` 仍通过共同 Helper 响应传播，outcome、scope、sources、gaps、diagnostics 不变 | 不新增操作或写能力，未触发 Gate；若响应闭集、错误传播或消费者漂移则暂停可用声明，修正并跑共同契约 tests |
| 05、20–24 | 05 已定义共享 `excerpts` 与 Spark 专属摘要摘录；其它类型只增加空 envelope，不改变其事实字段或语义；按真实对象覆盖 511/512/513、摘录外命中、F1/其它 F2 | 不改变字段登记或类型 Schema，未触发字段 Gate；若摘录改写、无界泄露、F3 引用丢失或相邻类型消费者不兼容则暂停候选能力，恢复契约一致后重测 |
| 07 | 编码前规划模块、接口、Schema、诊断、风险和消费者，使用风险匹配聚焦检查及 full-v4 | 当前规划是门槛；若实现超出覆盖或测试证据不匹配则先更新规划/验证记录再继续 |
| 08 | Web 独立完整读取；有意删除伪“意图”、保留来源并改善三字段完整摘要提示 | 命中有意行为变更 Gate，已由当前 Human 对 Spark 的明确指令限定授权；若来源消失、正文改写、Web 改经 Helper 或缺少范围匹配依据则停止相应呈现，修正并验证后恢复 |
| 20、31 与 `spark-0005` | AI 审核完整摘要；事实更正保留来源，更新时间更新并写后回读 | 当前 Human 指令覆盖该摘要更正，未触发额外 Gate；任何状态/关系变化或可能丢失价值的合并、替代、删除仍逐对象按 20 §10、05 §14 与 lifecycle 来源判断，命中条件才进入 Gate |

当前没有 Stop Condition 命中；上表是当次来源审核记录，不进入 Code、不形成 preflight、许可状态或行动白名单。

## 2. 模块责任与依赖方向

Helper 方向固定为：20 的完整事实语义 → 05 的 F2/F3 契约 → request 校验与候选扫描 → Helper 共同响应。Web 方向固定为：当前事实文件 → Web 只读 application/API → 详情投影 → 阅读组件。Web 不经由 Helper 才能读取事实，也不复制 Helper 的渐进式上下文预算；两条消费者路径共同回到同一事实 Schema 与类型来源。

| 模块或边界 | 责任 | 明确不负责 |
|---|---|---|
| `code/ldvh/helper/operations/fact_candidate_request.py` | 维护 F2 可检索字段闭集；允许 Spark `summary` 作为完整检索来源 | 把 `summary` 作为无界卡片字段，判断语义相关性或内容充分性 |
| `code/ldvh/helper/operations/fact_candidate_operation.py` | 从完整当前 `summary` 形成最多 512 个 Unicode scalar values 的原样前缀，返回 `field_path/text/complete`；F1 摘录为空 | 改写、trim、补省略号、摘要生成，或用摘录代替 F3 |
| `code/tests/helper/test_fact_candidate_operation.py` 及 request tests | 用真实事实对象和 Helper service 验证短于、等于、长于预算、摘录外命中、F1 空摘录与响应闭集 | 用 test fixture 创造新的领域字段或语义阈值 |
| `code/ldvh/hooks/context_recovery.py` 与专属 tests | 作为现有 F1 消费者验证 `excerpts` 必须为空，再继续只投影既有恢复字段与 byte budget | 消费 Spark F2、把摘录注入恢复上下文或改变 WorkCase binding |
| `code/ldvh/facts/carriers/yaml_object.py` 与 `code/tests/facts/test_yaml_carrier.py` | 继续保证 YAML 1.2 UTF-8 载体只形成可用于 scalar-value 摘录的 string；以 escaped lone-surrogate 反例锁定 parser 拒绝边界 | 修复、替换或静默删除非法 Unicode |
| `code/ldvh/facts/web_direct_capture.py` 与 `web/api/routes/sparks.ts` | 继续将三字段 Human capture 中的 `description` 按 08 canonicalization 映射为 Spark `summary` 并保留自包含来源 | 自动补写意图、扩写内容、语义查重或用来源 locator 代替正文 |
| `web/src/pages/object-detail/factReadingProjection.ts` | 只投影关系、来源、证据及未解析项的结构；保持字段含义 | 从 locator 生成意图、自动改写摘要结构或裁剪完整正文 |
| `web/src/pages/object-detail/FactReadingLayouts.tsx` | 直接完整渲染 `summary` Markdown；按“摘要、演变、分流、关联”组织 Spark 阅读 | 建立虚构 `intent_source` 节点，按 Helper F2 预算截断 Web，或隐藏内容不足 |
| `web/src/pages/object-detail/FactAssociationsSection.tsx` | 将关系、项目材料、Human/外部输入、URL 与未解析项分组；删除意图节点后仍完整保留 Human source | 把 locator 提升为正文，或为了简洁过滤 Human input |
| `web/src/components/SparkCreate.tsx` 与 `web/src/i18n/locales.ts` | 保持三字段 capture；通过标签、帮助文本和可多行输入提示 Human 记录形成原因、当前问题、已知判断、边界和剩余不确定性 | 新增必填字段、固定段落模板、字符门槛或由 Web 宣称内容充分 |
| `web/api/services/facts.ts`、`localFactReader.ts` 与 `v4SparkProjector.ts` | 保持 Web 从当前事实文件独立读取 list/detail，并只加 transport metadata | 调用 Helper 候选接口、裁剪摘要或创造事实字段 |
| `web/tests/api/fact-reading-projection.test.ts`、`local-facts.test.ts` 与 Spark reading contract test | 验证 Human source 保留、完整 Markdown 经过唯一 canonicalization 后在创建/list/detail 一致，以及组件不恢复 intent/摘要改写 | 以静态文件存在代替 API/事实回读全部证据 |
| `web/src/pages/ObjectDetail.tsx`、`object-detail/model.ts`、`web/src/index.css` | 继续提供共享 ReadingNode、Markdown renderer、字段隐藏和既有 14px/26px 阅读样式；本纵切只消费并回归当前未提交 Spark 相关变化 | 在本纵切重构通用详情、WorkCase 或另定事实语义 |

Web 可以与 Helper 共享底层事实解析或 application service，但 Browser 不执行 CLI，Web 也不以 Helper operation 作为事实读取的必经网关。若未来引入共享核心，必须另行更新规划和测试依赖方向。

## 3. 接口与 Schema 维护

Spark Schema 和字段语义唯一由 05 与 20 组合形成；本增量不新增事实字段。Helper `cards[]` 增加来源已经定义的 `excerpts` 投影：F1 固定空数组；Spark F2 的 `fields` 排除 `summary`，`excerpts` 精确一项；其它 F2 类型暂为空数组并保持现有直接字段投影。`text_match.field_paths` 对 Spark 仍允许 `summary`，匹配在完整字段上执行，命中位置不扩大返回摘录。已识别消费者是 Helper service/CLI/installed projection、`code/ldvh/hooks/context_recovery.py`、Code contract/packaging tests 及未来按 05 消费卡片的 AI；共同响应允许该来源定义字段，恢复消费者只读取 `fact_ref/fields` 并忽略空 `excerpts`。同步验证覆盖 operation/service/CLI、installed/packaging 与 context recovery；新增消费者仍必须回到 05。

摘录按 Python 字符串切片实现，但其“Unicode scalar values”成立依赖当前 YAML 1.2 parser 对 escaped lone surrogate 的拒绝；本增量以 `test_yaml_carrier.py` 反例锁定该前置条件，不把任意 Python surrogate 当作合法事实值。不得按 UTF-8 bytes 截断。`complete` 只比较完整合法值长度是否不超过 512，512 恰好完整，513 为不完整。卡片仍携带 `fact_ref`，由既有 `read-fact-objects` 完成 F3。

Web 不新增 Spark “意图”接口。删除 `getSparkHumanIntentSources`、`formatSparkSummaryForReading` 及相应消费，因为前者越权重命名来源，后者改变事实正文。来源和 Human capture 继续在“关联”中的外部输入/来源分组展示；`summary` 原值直接交给现有 Markdown renderer。

## 4. 错误、诊断与副作用

Helper 候选读取保持只读，既有 invalid/unavailable/partial、cursor 与 coverage 语义不变。摘录形成只对已经机械有效且 `summary` 为合法 Unicode scalar string 的 Spark 执行；载体/parser/Schema 无效对象继续进入既有问题范围，不以空摘录掩盖。响应与测试失败诊断不得输出匹配字段的其余正文或意外记录完整 `summary`，也不得因摘要超过预算报错。

Web 详情读取失败、未知引用与 malformed association 沿用当前显式错误/未解析呈现；删除“意图”投影不得删除对应 `source_refs`。创建仍是既有本机受控写入副作用，不新增写路径、权限、Hook、token、receipt 或行动许可状态。内容是否充分由 AI 按 20/31 审核；Human 提供输入或反馈，Code 只校验来源已经定义的机械结构，direct capture 成功不冒充已经完成充分性审核。

既有 Spark 的语义补全必须逐对象回读可定位来源，不能用 UI 文案、相邻对象或模型猜测填充。删除、合并、替代和终态变更必须逐对象按 20 §10、05 §14 与 lifecycle 来源判断；只有命中来源条件时才进入 Human Gate，本规划既不自动扩大也不绕过 Gate。

## 5. 风险与测试映射

| 风险 | 检查 |
|---|---|
| 完整摘要继续无界进入 Helper F2 | 真实 Spark 513+ code points，断言 `fields` 无 `summary`、摘录 512、`complete=false`、同卡有稳定 `fact_ref` |
| Unicode 或边界错误 | 分别覆盖 511、512、513 个 Unicode scalar values，包含非 ASCII 字符 |
| 检索被摘录预算缩窄 | 查询只在第 513 位之后命中，仍返回卡片，但摘录保持同一 512 前缀 |
| F1/其它类型响应形状漂移 | 断言每张卡都有 `excerpts`；F1 和当前无类型化摘录的 F2 卡固定空数组 |
| Web 将来源伪装成意图 | 投影 tests 断言没有 intent API/派生字段，Human input 保留在 external inputs |
| Web 改写或截断摘要 | 详情组件直接消费原始 Markdown；projection tests 不再做自动断句/编号重写 |
| 创建继续诱导一句话 | 组件测试或静态断言覆盖多行输入与内容帮助文本；API tests 断言 description 经 08 canonicalization 后、内部 Markdown/换行不再改写地成为 summary，并复用固定向量 |
| Web 被错误改为 Helper 网关 | Web API 真实只读路径与 V4 transport tests 保持通过；无 Browser→CLI 依赖 |
| 事实内容不足被渲染掩盖 | 内容审核独立列账；Web 完整显示实际字段，不自动扩写 |
| 混合 Working Tree 误伤 | 聚焦 diff、真实 Helper/Web tests、typecheck/build 后再运行 full-v4 Working Tree 证据入口 |

聚焦验证先执行 Helper candidate request/operation tests、Ruff、Web projection/API tests、typecheck 与 build。增量完成后通过 `tools/run_full_tests.py start --plan full-v4` 取得耐久全量证据，并回读终态、各步骤与 Working Tree before/after 指纹。subagent 的来源审核与代码审核是独立检查，不代替真实 tests。

## 6. 演进与已知缺口

当前只完成 Spark。V4 既有 Spark 中从 V3 迁移后被压缩、丢失演变或来源精度不足的对象，需要在实现稳定后逐对象建立来源账本并补全；无法由当前来源证明的内容保持缺口，不猜测。`spark-0005` 的当前未提交摘要已经按可定位 Human 输入与现行规则纠正 Web Helper-first 冲突；本纵切只负责回读并验证该修正，不再次产生修改授权，也不更改其状态或关系。

其它事实类型按独立纵切后续处理，WorkCase 最后处理。“不覆盖 WorkCase”表示不修改其领域字段、事实内容、Web 列表/详情或专用布局；它仍随 05 的共享 `cards[]` envelope 接收空 `excerpts` 并执行兼容回归。未来若 Human 明确改变三字段 create UI、增加正式 `intent` 字段、让 Web 通过 Helper 读取或引入共享跨语言 projection，必须先回到相应 Specs 和 Human Gate，再更新本规划或由替代规划承接。
