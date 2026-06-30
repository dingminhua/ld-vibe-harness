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
