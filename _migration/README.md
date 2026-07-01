# LDVH v3 迁移工作区

本目录是过渡迁移脚手架。

它不是稳定 v3 产品面的一部分：

- `_migration/schemas/` 不是 `specs/schemas/`。
- `_migration/code/` 不是正式 `code/`。
- `_migration/fixtures/` 不是正式 `tests/fixtures/`。
- `_migration/tests/` 不是永久 v3 测试套件。

本目录只用于在 v2 材料进入 v3 前进行分类。迁移决定可以说明某个来源应迁移、后置、拒绝，或转换为 schema、code、tests，而不是复制成另一个事实源。

满足以下条件后，删除整个目录：

- 第一批 v3 迁移完成；
- 稳定 v3 迁移规则已经存在；
- 迁移决定已经由永久 specs、schemas 或 tests 承接；
- 没有活跃工作依赖过渡分类 fixture。

稳定 v3 code 不得 import `_migration` 模块。

`_migration/inventory/` 下的 inventory 文件是临时 review 辅助材料。它们可以列出 v2 specs、附件和建议迁移动作，但不授权 v3 specs、schemas、Code 行为或 Action Guides。

`_migration/code/md_spec_extractor.py` 下的 Markdown 提取原型用于验证一个优先方向：Code 直接从 Markdown spec 正文读取稳定结构，再为 Action Guide compiler 生成内存中的行动来源。不得把它变成需要人工维护的一篇 Markdown 对应一份 YAML 的投影系统。

`_migration/inventory/md-direct-read-coverage.yaml` 下的覆盖说明是提取原型的临时证据。它们记录原型当前能解析什么，不是来源权威。

`_migration/code/spec_bloat_scan.py` 下的重复结构扫描器用于探索 v2 specs 是否存在重复骨架或泛化边界文本，这些内容可能应转为父级规则、生成式 Action Guide 内容或 Code 检查。扫描报告只作为 review 证据，不授权删除 spec 内容。

`_migration/v2-runtime-capability-migration-notes.md` 整合了根目录 V2 运行时临时讨论残余，用于支持删除根目录草稿后的追溯。它只记录 Rules、Skill、Hook/runtime 和知识地图能力的迁移证据；不授权 v3 specs、Code 行为、Action Guide 输出、Human Gate 决策或环境支持声明。

`_migration/v3-migration-execution-plan.md` 记录 V3 迁移执行节奏。它说明大量 specs 迁移应按消费闭环分批进入正式 `specs/`，而不是当前一次性导入或最后整批搬运；它仍是临时计划，不授权正式规则或 Code 行为。

`_migration/stage-5-v2-absorption-checklist.md` 记录第 5 阶段开始前必须完成的 V2 来源吸收、语义转换和测试前置条件。它用于阻止跳过吸收清单直接重写 Hook、Commit 或行动模板代码；它仍是临时证据，不授权环境接入、Hook 安装或提交门禁。

`_migration/v3-formal-spec-numbering-decision.md` 记录 V3 正式 specs 的目标编号和重编号理由。它用于指导当前 02/03/04 重排和后续 V2 吸收归口；它仍是临时决策证据，不替代正式 `specs/` 正文。

`_migration/v3-specs-absorption-index.md` 记录 V3 正式 `03/05/06/07/08/09/10` 应吸收哪些 V2/旧 specs 内容、哪些只能保留在迁移材料、哪些应转为 Code 或 tests。它用于支撑正式 specs 创建和 review 收据；它仍是临时迁移索引，不授权正式规则或实现行为。

`_migration/7-governed-project-admission.md` 记录阶段 7 受管项目接入范围。它说明 V3 已迁入受管项目静态解析、配置契约和 target-first resolver，但不授权 Hook 安装、commit gate、Web 写入或真实 `ldvh-base/` 实例迁移。

`_migration/8-end-to-end-closure.md` 记录阶段 8 静态端到端闭环演练。它说明 V3 已能把受管项目解析、Action Guide、runtime facade、preflight、验证、commit message 和 completion claim 串成只读闭环，但不授权真实环境接入或产品化启用。

`_migration/9-v3-mainline-transition-scope.md` 记录阶段 9 的 V3 主线切换范围。它把剩余 V2 内容明确分到 9A 迁移层依赖审计、9B 最小提交入口、9C 事实对象完整迁移、9D Web 数据契约迁移、9E 行动模板候选后置和 9F 主线切换收口；它仍不授权 Hook 启用、Web 通用写入、真实实例不可逆迁移或 hard switch。

`_migration/9A-migration-layer-dependency-audit.md` 记录阶段 9A 的迁移层依赖审计。它确认稳定 `code/` 没有 import `_migration`，但 formal review hash gate、迁移测试和少量运行时 source_ref 仍依赖 `_migration`；因此当前不删除 tracked 迁移材料，下一步进入 9B 最小提交入口。

`_migration/9B-minimal-commit-entry.md` 记录阶段 9B 的最小提交入口迁移。它说明 V3 已新增自有 commit gate、`specs_validate.py commit-gate` 和 `code/commit_validate.py` 包装器，但没有安装真实 Git Hook，也没有声明环境入口已生效。

`_migration/9C-fact-object-full-migration.md` 记录阶段 9C 的事实对象完整迁移。它说明 V2 Spark、WorkCase、Pitfall、Study 真实实例已迁入 V3 `ldvh-base/`，ADR 建立空实例目录和字段 schema，Code/tests 已能校验字段闭集、必填字段、legacy 字段、状态、Study 正文骨架和对象关系；它不授权 Web 写入、Hook 启用或正式行动模板实例创建。

`_migration/9D-web-data-contract-migration.md` 记录阶段 9D 的 Web 数据契约迁移。它说明 V2 Web tracked 资产和 Web API 回归测试已迁入 V3，Web facts API 按 08 从 `ldvh-base/` 独立读取并输出 `source_refs`，Spark quick create 作为唯一最小轻写入被保留；它不授权通用 Web 写入、完整 Confirm UI、Hook 启用或 V3 正式主线接管。

`_migration/9E-action-template-candidate-deferral.md` 记录阶段 9E 的行动模板候选后置结论。它说明 Git 提交行动仍是当前唯一正式模板示范，WorkCase 创建、方案审核、执行推进、结果复核、关闭确认、Rules 同步审查和环境入口适配继续作为后置候选；它不授权正式行动模板实例、Hook 启用、Web 通用写入或 Human Gate 自动完成。

`_migration/9F-mainline-soft-switch-closure.md` 记录阶段 9F 的 V3 soft mainline 收口结论。它说明 V3 已成为日常规则和事实维护主线，并开始用 `code/test_runner.py` 承接 smoke / targeted / full 分层测试入口；其中 `environment_integrated=false`、`hook_integrated=false`、`authorization=none` 是 9F 当时边界。10A 之后当前 worktree 已单独接入 `commit-msg` 最小 Hook。

`_migration/10A-commit-msg-hard-switch.md` 记录当前 worktree 的 `commit-msg` 最小 hard switch。它说明 V3 已通过 worktree-local `core.hooksPath=hooks` 接管真实 Git commit message 校验，并从提交正文 `读取依据:` 段提取 read_plan 消费证据；它不授权 session start、pre tool use、completion claim、Rules/runtime adapter、通用 Web 写入或外部受管项目 Hook adapter。

`_migration/10B-session-start-manual-entry.md` 记录 `session_start` 手动入口。它说明当前环境没有可安装的真实会话启动 Hook，V3 只新增 `code/session_start.py` 作为手动/外部 adapter 可调用 read_plan 入口；它不声明 session start 已自动接管，也不授权 pre tool use、completion claim 或 Rules/runtime adapter。

`_migration/10C-pre-tool-use-manual-entry.md` 记录 `pre_tool_use` 手动入口。它说明当前环境没有真实工具调用前置 Hook，V3 只新增 `code/pre_tool_use.py` 作为手动/外部 adapter 可调用写入前检查入口；它不声明 apply_patch、Edit、Write 或 shell 写入已被自动拦截，也不授权 completion claim 或 Rules/runtime adapter。

`_migration/10D-completion-claim-manual-entry.md` 记录 `completion_claim` 手动入口。它说明当前环境没有真实完成前 Hook，V3 只新增 `code/completion_claim.py` 作为手动/外部 adapter 可调用完成声明前检查入口；它不声明自然语言完成声明已被自动拦截，也不替代 Human Gate、验收或 Rules/runtime adapter。

`_migration/10E-runtime-adapter-feasibility.md` 记录 runtime adapter 可行性和统一入口。它说明当前支持两类接入：真实 `git.commit-msg` Hook 和 manual/external adapter-ready 三件套；`code/runtime_adapter.py` 只提供统一 payload/CLI 转发，不声明 session、tool 或 completion 事件已被真实环境自动触发。

`_migration/10F-environment-status-check.md` 记录环境接入状态检查入口。它说明 `code/environment_status.py` 统一报告真实 `git.commit-msg` Hook 与 manual runtime entrypoints 的可用/接入状态；该入口只读诊断当前边界，不安装新 Hook，也不声明 manual 入口已自动触发。

`_migration/10G-rules-environment-entry-audit.md` 记录外部环境入口与 legacy Rules/Skill 审计。它说明 `code/environment_entry_audit.py` 已确认当前除 `git.commit-msg` 外，没有可复现证据证明 tool hook、completion hook、Codex repo 指令或外部 runtime adapter 已自动触发；Rules / Skill 顶层机制已取消并标记为 `removed_top_level`，早期骨架占位目录已删除。

`_migration/11A-human-gate-constitutional-remediation.md` 记录第 11 阶段对构成体系变更的 Human Gate 补救。它不声称早期迁移前已有完整确认，只确认从阶段 11 起以当前 V3 五类构成、保障与衔接层、Rules/Skill 顶层取消和环境适配归口作为整改基线。

`_migration/11B-spec-status-activation.md` 记录正式 specs 和附件从 candidate 收口为 active 的处理结果。它只说明规则源状态激活，不授权环境自动入口、Web 通用写入或非提交行动模板。

`_migration/11C-environment-adaptation-admission.md` 记录 `specs/11-环境适配规范.md` 和 11 附件的迁入结果。它承接环境入口类型、接入状态、runtime payload、receipt、安装回滚和 Rules/Skill legacy 边界。

`_migration/11D-runtime-automatic-integration-boundary.md` 记录真实 runtime 自动入口审计结论。当前除 `git.commit-msg` 外，没有 tool hook、completion hook、session hook、Rules 顶层机制或 Skill 顶层机制可以升级为 integrated。

`_migration/11E-v2-v3-capability-coverage-matrix.md` 记录 V2 到 V3 能力覆盖矩阵，把已迁入、转归口、后置和废弃项放到同一张表中。

`_migration/11F-action-template-minimal-closure.md` 记录行动模板最小闭环。Git 提交行动仍是唯一正式模板示范，WorkCase 创建、方案审核、执行推进、结果复核和关闭确认继续后置。

`_migration/11G-migration-dependency-independence.md` 记录迁移层依赖独立处理。formal review hash gate 已迁到 `reviews/formal/`；`_migration/reviews/` 不再是稳定 gate 读取位置，但 `_migration` 仍保留历史证据和迁移测试。

`_migration/12-19-v3-post-mainline-work-plan.md` 记录 V3 主线验收后的后续工作计划。它把阶段 12-19 分为 specs 与实现域边界补强、WorkCase 最小行动模板、测试性能分层、runtime 自动入口评估、稳定 receipt 存储、Web Confirm UI、外部受管项目 Hook adapter 和 `_migration` 归档判断；它不授权这些能力已经生效。

`_migration/12A-implementation-domain-boundary.md` 记录阶段 12A 的实现域实践边界补强。它说明 specs 只定义需求、规则、契约和边界，Code/Web/Tests 的实践分别由 `code/`、`code/docs/`、`web/`、`web/docs/`、`tests/` 和对应实现域承接；它不新增具体实现文档、Web 页面、测试分层或环境入口能力。

`_migration/13A-workcase-minimal-action-template.md` 记录阶段 13A 的 WorkCase 最小行动模板。它说明 `06` 已承接 WorkCase 创建、执行推进、结果复核和关闭确认的手动等价行动结构；它不授权 Web 写入、Hook、runtime 自动触发、完整 Confirm UI 或字段表细化。

`_migration/14A-test-tiering-performance.md` 记录阶段 14A 的测试性能与分层优化。它说明 `09` 已定义 smoke/targeted/runtime/full 分层契约，Code runner 支持 runtime profile 和 targeted slow policy；它不删除慢测试、不降低 full regression 覆盖，也不默认并行化 slow 层。

`_migration/15A-runtime-auto-entry-assessment.md` 记录阶段 15A 的 runtime 自动入口复核。它确认当前除 `git.commit-msg` 外没有可升级为 integrated 的 session/tool/completion 自动入口，manual runtime 三件套仍是 manual-ready，Rules / Skill 顶层机制仍是 removed_top_level。

`_migration/16A-receipt-storage-decision.md` 记录阶段 16A 的 receipt 存储判断。它决定当前不建立独立 runtime receipt 事实源；需要长期保留的 receipt 内容必须先由 AI 定性，并分流到验证证据、WorkCase 关闭证据、Git commit records、迁移记录或其它既有事实对象。

`_migration/17A-web-confirm-ui-write-boundary.md` 记录阶段 17A 的 Web Confirm UI 与通用写入边界判断。它确认 Spark quick create 仍是当前唯一正式 Web 写入；通用事实对象写入、WorkCase 状态推进写入和完整 Confirm UI 继续后置，启用前必须重新进入 Human Gate 和 tests/web 合同验证。
