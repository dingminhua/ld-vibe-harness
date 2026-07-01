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

`_migration/9-v3-mainline-transition-scope.md` 记录阶段 9 的 V3 主线切换范围。它把剩余 V2 内容明确分到 9A 迁移层依赖审计、9B 最小提交入口、9C 事实对象完整迁移、9D Web 数据契约迁移、9E 行动模板候选后置和 9F 主线切换收口；它仍不授权 Hook 启用、Web 写入、真实实例迁移或 V3 正式接管声明。

`_migration/9A-migration-layer-dependency-audit.md` 记录阶段 9A 的迁移层依赖审计。它确认稳定 `code/` 没有 import `_migration`，但 formal review hash gate、迁移测试和少量运行时 source_ref 仍依赖 `_migration`；因此当前不删除 tracked 迁移材料，下一步进入 9B 最小提交入口。

`_migration/9B-minimal-commit-entry.md` 记录阶段 9B 的最小提交入口迁移。它说明 V3 已新增自有 commit gate、`specs_validate.py commit-gate` 和 `code/commit_validate.py` 包装器，但没有安装真实 Git Hook，也没有声明环境入口已生效。

`_migration/9C-fact-object-full-migration.md` 记录阶段 9C 的事实对象完整迁移。它说明 V2 Spark、WorkCase、Pitfall、Study 真实实例已迁入 V3 `ldvh-base/`，ADR 建立空实例目录和字段 schema，Code/tests 已能校验字段闭集、必填字段、legacy 字段、状态、Study 正文骨架和对象关系；它不授权 Web 写入、Hook 启用或正式行动模板实例创建。

`_migration/9D-web-data-contract-migration.md` 记录阶段 9D 的 Web 数据契约迁移。它说明 V2 Web tracked 资产和 Web API 回归测试已迁入 V3，Web facts API 按 08 从 `ldvh-base/` 独立读取并输出 `source_refs`，Spark quick create 作为唯一最小轻写入被保留；它不授权通用 Web 写入、完整 Confirm UI、Hook 启用或 V3 正式主线接管。

`_migration/9E-action-template-candidate-deferral.md` 记录阶段 9E 的行动模板候选后置结论。它说明 Git 提交行动仍是当前唯一正式模板示范，WorkCase 创建、方案审核、执行推进、结果复核、关闭确认、Rules 同步审查和环境入口适配继续作为后置候选；它不授权正式行动模板实例、Hook 启用、Web 通用写入或 Human Gate 自动完成。
