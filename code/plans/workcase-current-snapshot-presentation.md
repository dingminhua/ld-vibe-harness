# WorkCase 当前快照确定性呈现投影

## 覆盖与起点

本规划覆盖 WorkCase 当前快照呈现投影的 Code 增量：Python 确定性投影、Helper `read-fact-objects` 的 AI 交付面、Web 字段级读取与共享投影、跨语言单向生成、API 消费、诊断和测试。它不定义 WorkCase 生命周期、授权或完成语义；这些语义只来自当前 `specs/21-WorkCase-工作项.md`。Web 的字段级读取与 Human 呈现边界继续来自 `specs/08-Web 呈现与交互规范.md`，Helper 读取结果形状来自 `specs/05-事实模型基础规范.md`。

规划形成时的实现起点是 commit `77519b3d57be37801193221a886eed2e9f549a65`。执行开始后，原有四项 Web 变化已由并行工作在 commit `fd2c91bbc73f4f02ddd6a10896ccf82e065d8f5b` 中提交；本增量已经审阅该提交并把它作为新的代码读取基线，但 Gate 1 已批准的 `prohibited_actions` 仍明确按路径禁止本案修改、暂存或提交这四个文件，因此它们继续作为实施排除项：

- `web/src/pages/ObjectList.tsx`
- `web/src/pages/object-detail/WorkCaseReadingLayout.tsx`
- `web/tests/api/workcase-card-lifecycle-contract.test.ts`
- `web/tests/api/workcase-detail-current-contract.test.ts`

以下事实对象仍是其它工作的未提交变化，本增量同样不得修改、暂存或提交：

- `ldvh-base/workcases/workcase-0036.yaml` 至 `workcase-0039.yaml`

`ldvh-base/workcases/workcase-0041.yaml` 是本增量自身的受控事实对象，只经 Helper 写回，不由普通文件工具修改。本规划与 [Web 字段级事实读取迁移](web-field-level-reading.md) 共同读取：后者仍负责 Web 直接读取事实载体、逐字段问题和未解析结构；本文只细化 WorkCase `status + phase` 呈现投影及来源内容指纹，不改变字段级读取的成立条件。

## 实现目标与明确排除

本增量实现一份非持久、可失效的 `workcase-current-snapshot-presentation/1` 投影。投影以当前载体内容指纹绑定来源快照，以合同身份绑定当前转换程序；它只表达生命周期位置、固定交还叙述 key、结构上的下一必经控制步骤、Web 进展分组/环节和阻塞覆盖层。

明确不实现：

- 不把投影、下一动作、续跑判断或投影指纹写入 WorkCase YAML；
- 不判断自然语言授权是否充分、能力是否可用、行动是否允许、工作是否完成或 phase 是否应推进；
- 不让 Web 完整机械校验成为字段级读取的前置条件；
- 不修改 34 的 Controller 执行循环，也不机械控制 AI 最终自然语言；
- 不把现有 canonical plan/result/authorization projection 改名或扩责为呈现投影；
- 不修改 Gate 1 明确禁止的四个 Web 页面/测试文件，也不回退 `fd2c91bbc` 已交付的授权卡片交互。

## 模块责任

### `code/ldvh/facts/workcase_presentation.py`

唯一 Code 维护点。它承接 21 已定义的 status/phase 闭集与呈现投影表，提供纯函数和稳定合同数据：

- 输入：`status`、`phase`、来源内容指纹；
- 输出：resolved 或 unresolved 的非持久投影；
- resolved 内容：合同身份、来源指纹、生命周期位置、交还叙述 key、结构上下一必经控制步骤、进展分组、可选进展环节、阻塞覆盖层；
- unresolved 内容：合同身份、来源指纹和来源已定义的结构性失败原因，不猜测相邻 phase；
- 辅助输出：由同一表确定性渲染 Web 生成文件。

该模块不读取文件、不调用 Helper、不写事实、不调用模型，也不决定生命周期转换。

### `code/ldvh/helper/operations/fact_object_operation.py`

只在 `read-fact-objects` 已得到 mechanically-valid WorkCase 且有当前 `content_fingerprint` 时调用纯投影函数，并把结果放入该读取 item 的 `current_snapshot_projection`。非 WorkCase、invalid、unavailable 或缺少指纹时不补造 resolved 投影；原有 `check_status`、`fact_object`、issues 和 partial 结果保持权威。

Helper 不重新实现映射，不从 projection 推断读取成功，也不让 projection 替代完整 `fact_object`。

### `code/tools/generate_workcase_presentation_contract.py`

只把 Python 唯一维护点的稳定合同数据确定性渲染到 `web/shared/workcasePresentationContract.generated.ts`。它不解析 Specs、不决定语义、不扫描事实。生成文件头明确标注不可手工维护。

### `web/shared/workcasePresentationContract.generated.ts`

单向生成的 TypeScript 数据，不是第二维护点。它只包含合同身份、phase 映射和闭集类型所需字面量；任何手改都会被同步测试拒绝。

### `web/shared/workcaseStatus.ts`

Web 投影 facade。它消费生成数据并提供：

- `deriveWorkCasePresentationProjection`：对字段级可读的 `status + phase + source_content_fingerprint` 返回 resolved/unresolved；
- 既有 progress helper：改为委托新 facade，保持已有调用方的进展分组/环节接口；
- 类型守卫和显示顺序：只服务 Web/API，不重新维护 phase 语义。

### `web/api/services/localFactReader.ts`

继续负责字段级载体读取。对成功读到的当前载体 bytes 计算 SHA-256 `source_content_fingerprint`，用于绑定 Web 派生投影；该指纹不表示 mechanically valid，也不替代 `read_status`、field issues 或 unparsed structures。

### Web API 与 Human-facing 消费层

`web/api/services/facts.ts`、`web/api/routes/objects.ts`、`web/api/routes/cognition.ts` 和必要的 clean API types 消费 shared facade，不维护自己的 phase 表。API 可以同时保留现有 `progress_group` / `progress_step` 兼容字段和完整 `current_snapshot_projection`；兼容字段必须从同一个 resolved projection 取得。i18n 只维护稳定 key 的显示词，Web docs 只说明消费和呈现，不复制 phase 映射。

本增量把同源投影、阻塞标签 key 和 `next_required_control_step` 交付到 clean shared/API/type 边界；Gate 1 禁止路径中的列表与详情页面消费继续延期，不以当前 git 已 clean 为由扩大批准范围。

## 依赖与调用方向

允许的方向固定为：

```text
specs/21 语义
  -> Python 唯一 Code 维护点
       -> Helper read item
       -> TypeScript generator -> generated contract -> Web shared facade
                                                   -> Web API/类型/文档消费者
current fact carrier bytes -> Helper validator/content_fingerprint -> Helper projection
current fact carrier bytes -> Web field reader/source_content_fingerprint -> Web projection
```

禁止 Web import Python 运行时、Helper 调用 Web、生成文件反向生成 Python、页面或 i18n 自建 phase 映射，以及从测试快照反向定义合同。Specs 与 Code 的同步由语义审查负责，Python 与 TypeScript 的同步由单向生成检查负责。

## 接口与 Schema 维护

21 维护投影语义和闭集；05 只维护 `read-fact-objects` item 中条件 `current_snapshot_projection` 的外部结果形状；08.Att.01 只登记 Web API 对该派生字段的传输资格并回指 21，不复制映射。04 的共同响应和 04.Att.01 无需复制具体操作字段，除非实现审查发现当前共同闭集确实阻止该操作结果扩展。

Python 的 resolved/unresolved TypedDict（或等价只读结构）由 `workcase_presentation.py` 维护。Helper 原样输出 snake_case JSON。生成器把同一数据转换为 TypeScript 字面量和 camelCase facade 所需结构；字段命名转换不得改变枚举或成立条件。

Web `LocalFactItem.source_content_fingerprint` 是 Web 读取元数据，不进入 `fact_object`。API 的 `current_snapshot_projection` 是派生视图，不得被回写。若未来缓存该视图，缓存键必须同时包含来源内容指纹与合同身份；本增量不新增持久缓存。

## 失败与诊断

- Helper mechanically-valid WorkCase 无法形成投影属于实现/合同偏移，保留原读取结果并形成可定位 issue 或失败测试，不能静默猜测；
- Helper invalid/unavailable 或无内容指纹时不输出 resolved 投影，调用方继续依据 `check_status` 和 issues；
- Web 载体不可读时沿用 `unreadable`，不形成投影；
- Web 载体可读但 status/phase 缺失、类型不符或组合非法时返回 unresolved，并继续呈现其它可读字段、field issues 与未解析结构；
- generated TypeScript 与 Python renderer 不一致时，生成同步测试失败并要求重新生成；
- 合同身份不匹配时不得消费缓存或旧生成物。

诊断不得把 unresolved 表达为 blocked、closed、Gate 2 或下一可执行行动。

## 风险与测试映射

| 风险 | 检查 |
|---|---|
| `independent_reviewing` / `closure_preparing` 提前生成 Gate 2 话术 | Python 与 Web 全 phase 表驱动负向测试；只允许 open + `human_closure_confirming` 使用 `gate2_waiting` |
| blocked + `human_closure_confirming` 被写成“仅剩关闭确认” | 单独断言 `gate2_position_blocked`、`blocking_overlay=true`，禁止 `gate2_waiting` |
| closed 与 phase 混用 | closed/no-phase 正例和 closed/phase 非法 unresolved 测试 |
| Web 因完整对象无效而隐藏可读字段 | local field reader 与 API 测试使用可解析但字段不完整的载体，断言 unresolved 与其它字段同时存在 |
| Helper 对 invalid 对象猜投影 | Helper operation 负向测试断言 projection 缺失且原 issues 保留 |
| Python/TypeScript 漂移 | renderer 对生成文件逐字节一致测试；Web 测试覆盖合同 identity 和映射闭集 |
| 旧 API 消费者行为回归 | 使用新建独立契约测试覆盖 clean shared/API/type 边界；不修改 Gate 1 禁止的 lifecycle/detail tests |
| 指纹被误当校验通过 | Web 测试断言 source fingerprint 与 `read_status`/field issues 独立；Specs 明确边界 |
| Code 越权输出授权、ready 或完成结论 | 输出键闭集测试与源代码合同测试，禁止 readiness/authorization/completion 字段 |

目标验证包括 Python facts/helper tests、生成同步测试、新 Web contract/API tests、Web typecheck、相关规范合同测试、`git diff --check`、dirty 路径边界比较和 Helper 全库事实完整性检查。测试通过只证明受测结构与行为，不证明 AI 自然语言、Human 授权、Reviewer 独立性或工作完成。

## 演进与已知缺口

本增量不修改 34，因此“AI 每次回读后必须消费 projection 并连续写回”的流程约束仍由后续 WorkCase 承接；Helper 交付真实投影只消除 AI 无统一输入的问题。列表与详情的最终可见标签消费也因 Gate 1 的明确路径禁令延期，当前只交付 clean API/type 能力和来源规范。

顶层 `resume_from` / `summary`、固定 quality gate 重复、checkpoint 与 Git commit 粒度不属于本规划。当前规则读取仍带有“7 项当前规则源资格条件尚未由 Code 机械证明”的既有缺口；本规划不把它写成已解决或投影成立证据。
