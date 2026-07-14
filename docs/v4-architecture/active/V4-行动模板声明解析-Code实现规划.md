# V4 行动模板声明解析 Code 实现规划

> 当前规划版本：2；初版形成时间：2026-07-15 03:41:22 +08:00；实现起点 commit：`554558c076895f42b46ab1703693f5d9a31fcacd`。§§1–9 记录声明解析首增量，§10 记录三模板与 Helper 读取后续扩展；本文是 07 定义的 Code 实现规划，不是规则源。

## 1. 实现目标与来源

本增量依据当前有效的 `action-template-foundation` §5.2，实现通用行动模板声明的确定性解析与派生检查，并以 `git-commit-action-template` 草案作为代表性结构样本。`specification-model-foundation` 提供当前规则源候选和结构读取边界，`code-engineering-practices` 提供本规划、模块、诊断与测试要求。

本增量只实现：

1. 从已经通过现有机械检查的 `active` 普通规范中定位唯一 `行动模板声明` H3；
2. 校验固定三列表头、非空数据行、`template_key` 格式、同来源与跨来源唯一性；
3. 校验 `definition_ref` 只回指同一来源中唯一 H2 或 H3，且不指向声明 H3 自身；
4. 形成可回指来源和定义范围的派生声明结果，并保留逐来源未完成与诊断；
5. 以风险匹配 tests 证明上述机械范围。

本增量不实现模板语义适用判断、自然语言召回、Git 状态读取或写入、commit 创建、Helper 公开操作、缓存/中央目录、事实对象、Skill、Hook、adapter 或环境接入。30 仍为 `draft` 时不得进入当前派生模板集合；测试使用的草案内容不因此取得规则效力。

## 2. 模块责任

新增 `ldvh.specs.action_templates`，内聚承担声明表解析、定义引用解析、定义范围计算、跨来源 key 冲突处理和派生诊断。输入是现有 `RepositoryInspection`，只消费其 `active_documents_passing_implemented_checks`、已有 issues、未完成范围和未自动证明条件；输出是不可变的声明对象与检查结果，不读取文件系统、不调用 Git、不写入状态。

现有 `ldvh.specs.markdown` 继续唯一承担 Markdown 标题和 GFM 表格的机械读取；`ldvh.specs.identity` 继续承担规范身份与 key 基础格式；`ldvh.specs.repository` 继续承担候选发现、身份/结构/图检查和 active 来源集合，不反向依赖行动模板模块。`code/tests/specs/test_action_templates.py` 只承担行为证据，不成为 Schema 或规则来源。

## 3. 依赖与调用方向

允许方向为：消费方或 tests → `ldvh.specs.action_templates` → `RepositoryInspection` 数据结构、`identity.KEY_PATTERN`、`markdown` 解析结果和共同 `diagnostics`。`repository` 不导入 `action_templates`，避免把某类派生声明塞入规范启动闭环并形成循环。

禁止行动模板模块自行扫描路径、回退 Index/`HEAD`、读取 draft/retired 文档、调用 Helper、解释摘要相关性或维护手工注册表。后续 Helper 模板操作已经按 06 正式契约消费本模块结果，不复制解析器。

## 4. 接口与 Code 侧表示

模块公开维护两个不可变 Code 侧表示：

1. `ActionTemplateDeclaration`：保存 `template_key`、`summary`、来源规范 key、定义标题、定义起止行、来源位置和来源文档；
2. `ActionTemplateSourceInspection`：保存已接受声明、issues、`incomplete_sources` 和从 repository 继承的 `unchecked_conditions`。

公开入口 `inspect_action_template_sources(repository)` 只返回派生检查结果，不声明模板已经适用、可执行或可由 Helper 调用。字段语义唯一来自 06 §5.2；Code dataclass 是内部表示，不是新的外部 Schema。以后字段或范围语义变化时先修改正式来源，再同步本模块与 tests。

## 5. 错误与诊断

声明 H3 重复、缺表、表头错误、空表或声明区含额外内容时，暂停该来源的全部声明。单行 key、单元格或引用错误只暂停该行；同一或跨来源 key 重复时暂停全部冲突行，其它有效行继续保留。

每项 Issue 必须定位当前规范路径和尽可能精确的声明行，并通过 `affected` 保留来源 key；key 冲突同时包含模板 key。Repository 已有问题与未完成范围原样传播，不能被声明检查隐藏或改写为成功。本模块只处理公开规范内容，不记录凭据或额外文件内容。

## 6. 风险与测试映射

| 风险 | 测试检查范围 |
|---|---|
| 合法 H2/H3 定义引用被错误拒绝或范围切错 | 分别建立 H2、H3 定义，断言标题、起止行与来源 |
| draft、retired 或未通过现有检查的来源被误纳 | Repository 输入只含 active 通过集合，构造 parsed 但未进入 active 集合的文档并断言排除 |
| H3 重复、缺表、错误表头、空表、声明区额外正文造成部分脏数据泄漏 | 每种来源级错误断言该来源全部声明暂停并产生精确诊断 |
| 非法/空行、key 格式、越源、多个 `::`、目标缺失/歧义/指向自身 | 参数化行级失败测试，断言坏行暂停而同表其它合法行保留 |
| 同来源或跨来源重复 key 只删除一侧 | 断言所有冲突声明均被移除、每个来源有诊断、其它 key 保留 |
| Code 把声明存在扩大为适用或能力 | 输出不含 applicable、authorized、executable、available 或 Helper 能力字段；测试只断言派生身份和来源 |
| 现有规范解析与投影被回归破坏 | 运行新增测试、现有 specs 结构/身份/发现测试和可执行的相关回归集合 |

测试使用临时普通 Markdown 文件和真实当前解析器，不用 mock 替代表格与标题解析。它不执行真实 Git commit、Hook 或 Helper，因此不证明这些环境范围。

## 7. 演进、激活与缺口

本规划实现和测试完成后，已经回读 30 准入记录、身份、声明和第二轮处置，并把 30 从 `draft` 改为 `active`。激活后的当前仓库派生检查只发现 `git-commit` 且来源回指正确；当前仓库其它既有缺口仍按 §9 报告，不得用新增模块的局部通过替代。

初版完成时，Helper 模板发现/内容读取、第二个真实模板与 Git 执行封装仍待后续正式契约和实现；跨 Git 历史的 key 改派与 retired tombstone 检查也是未实现资格条件。后续扩展已经按本节触发条件重新评估接口、派生范围和测试矩阵，当前结果见 §10。

## 8. 与其它当前规划的关系

`active/V4-工作推进总纲.md` 是稳定当前规划入口并决定工作顺序；本文细化其中“通用行动模板声明解析”这一 Code 增量。总纲负责顺序、已完成和未完成范围，本文负责本模块的具体责任、依赖、接口、诊断和风险测试；两者不得互相替代。

本文不修改或替代事实对象、Helper 现有操作、Web 或其它 Code 规划，也不覆盖当前 Working Tree 中用户已有的 `V4-Audit-Report-GLM5.2-2026-07-14.md` 删除及其它不属于本增量的变化。

## 9. 实现与验证结果

本增量新增 `code/ldvh/specs/action_templates.py` 和 `code/tests/specs/test_action_templates.py`，并同步当前仓库/CLI 对新增 active 规范数量的测试断言。实现只消费现有 `RepositoryInspection` 的 active 通过集合，不产生文件或 Git 副作用。

验证结果：

1. 新增行动模板解析风险 tests：19 passed；
2. 新增测试与现有身份、结构、Markdown、发现回归组合：98 passed；
3. 30 真实来源 active 模拟及激活后检查：唯一派生 `git-commit`，来源为 `git-commit-action-template`，定义范围为当前文件第 86–163 行，无行动模板专项诊断；
4. Ruff：`code/` 全量通过；
5. 将已移动的五类型准入记录在内存中指向实际 `docs/v4-architecture/active/` 路径后，仓库检查为 0 issues、19 个 active 载体、15 个非附件、57 个 L0–L2 投影、8 个既有 Helper 操作和 1 个行动模板；
6. 未修正既有路径漂移的当前 Working Tree 全量 `code/tests`：337 passed、46 failed、102 errors。失败和 setup error 共同受到 `field_registry.ADMISSION_AUDIT_PATH` 与 fixture 仍指向重组前路径的上游影响；本增量未越界修改事实模型路径契约。

因此，初版规划覆盖的声明解析、派生身份、冲突处理和 tests 已完成。当时尚未验证和未实现的真实 Git commit、Helper 模板公开操作及五类型准入路径漂移已在后续增量处理；Hook/Skill/adapter 接入仍未实现。当前扩展证据见 §10。

## 10. 后续扩展：三模板与 Helper 读取

2026-07-15，31 与 32 加入后，声明解析在真实当前来源中同时发现 `git-commit`、`fact-object-controlled-creation` 和 `fact-object-lifecycle-change`，并继续保持 key 唯一、来源精确和定义范围机械切片。

06 新增 `read-action-template-candidates` 与 `read-action-template-content` 两个只读公开操作。实现复用 `inspect_action_template_sources` 的同一次 `RepositoryInspection`，不重新扫描路径：候选操作返回稳定 key、摘要、来源与定义行范围，并列出 Code 未自动证明的准入条件；内容操作按精确 key 和请求顺序返回定义章节、完整来源规范及各自 SHA-256。两者不作自然语言适用、授权、能力或执行判断，不建立跨调用运行状态。

风险测试覆盖三真实模板组合、精确顺序、未知 key 的 partial/unavailable、空 key 与 disclosure 拒绝、capabilities 可用性、定义/来源双指纹、同一快照读取和真实 CLI 调用。当前未完成范围是环境 Hook/Skill/adapter、跨 Git 历史 key tombstone 自动检查、模板语义自动选择与执行；其中后两项不得因只读 Helper 存在而外推成立。
