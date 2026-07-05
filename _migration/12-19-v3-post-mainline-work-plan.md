# 12-19 V3 主线后续工作计划

文件状态：post-mainline work plan。本文只记录 V3 主线验收后的后续工作顺序，不授权新能力已经生效。

## 当前基线

阶段 11 后，V3 主体迁移已完成：

1. `specs/` 正式规范和已迁入附件为 active；
2. `ldvh-base/` 承接 V3 事实对象实例；
3. Web 已按 08 独立读取 V3 facts，不依赖 Code 输出作为主数据源；
4. 当前 worktree 已接入 `git.commit-msg` 最小 hard switch；
5. `specs/01-保障与衔接.md` §6 与 `01.Att.03-06` 已承接环境入口分类、状态、payload、receipt、安装和回滚边界；
6. formal review hash gate 已迁入 `reviews/formal/`；
7. `_migration` 保留为历史证据和迁移测试材料，不作为正式规则源或事实源。

后续工作不再属于 V2 到 V3 主体迁移，而是 V3 主线验收后的能力建设、边界补强和历史材料收口。

## 推荐顺序

| 阶段 | 名称 | 目标 | 是否授权能力生效 |
|---|---|---|---|
| 12 | Specs 与实现域边界补强 | 明确 specs 只定义需求、规则、契约和边界，实践细节由 Code/Web/Tests 等实现域承接 | 否 |
| 13 | WorkCase 最小行动模板 | 补齐 WorkCase 创建、执行推进、结果复核和关闭确认的最小行动结构 | 待验证后再判断 |
| 14 | 测试性能与分层优化 | 降低全量测试慢和并行 OOM 风险，优化 smoke/targeted/full 分层 | 否 |
| 15 | runtime 自动入口评估 | 判断 session/pre-tool/completion 是否存在真实可接入触发点 | 否 |
| 16 | 稳定 receipt 存储 | 判断 stdout-only receipt 是否需要长期事实源回写 | 否 |
| 17 | Web Confirm UI 与通用写入 | 增强 Human Gate 可见性和受控交互 | 待 Human Gate |
| 18 | 外部受管项目 Hook adapter | 把当前 worktree commit-msg 能力扩展到外部受管项目 | 待 Human Gate |
| 19 | `_migration` 归档判断 | 判断历史迁移材料是否可以归档或删除 | 待 Human Gate |

## 阶段 12：Specs 与实现域边界补强

目标：

1. 明确 `specs/` 只承载需求、规则、契约、边界、Human Gate、Stop Conditions 和验证要求；
2. 明确实现域实践由 `code/`、`web/`、`tests/`、`hooks/`、实现域文档或对应测试承接；
3. 防止 specs 正文承载具体实现语言、框架、模块拆分、页面组件、测试文件清单、性能实践或执行细节；
4. 防止实现域文档、代码、测试、review 或迁移材料反向改写 specs 正文。

计划动作：

1. 在 `specs/04-Specs基础规范.md` 增加实现域实践边界的上位规则；
2. 在 `specs/07-Code确定性执行规范.md` 明确 `code/` 和 `code/docs/` 承接 Code 实践；
3. 在 `specs/08-Web信息同步规范.md` 明确 `web/` 和 `web/docs/` 承接 Web 实践；
4. 在 `specs/09-测试与验证规范.md` 明确 `tests/` 承接测试实现，不强行新建 `tests/docs/`；
5. 增加 Code/tests 检查，防止该边界再次退化为口头约定。

完成记录：

阶段 12A 已按上述动作完成，记录见 `_migration/12A-implementation-domain-boundary.md`。本阶段只补强职责边界和可验证检查，不新增具体实现域实践文档，也不改变 Hook、runtime、Web 写入或测试分层能力。

## 阶段 13：WorkCase 最小行动模板

目标：

1. 在不声明完整自动化、不依赖完整 Confirm UI 的前提下，建立 WorkCase 最小行动结构；
2. 覆盖 WorkCase 创建、执行推进、结果复核和关闭确认；
3. 保持 Human Gate 显式，不用模板替代 Human 确认；
4. 复用现有事实对象状态机和 manual runtime 入口。

后置边界：

1. 不声明通用 Web 写入已接入；
2. 不声明 pre_tool_use 或 completion_claim 已自动 Hook；
3. 不声明所有 WorkCase 状态推进都能自动执行。

完成记录：

阶段 13A 已建立 WorkCase 最小手动行动模板，记录见 `_migration/13A-workcase-minimal-action-template.md`。本阶段只承接 `manual_equivalent_execution`，不启用 Web 写入、Hook、runtime 自动触发、完整 Confirm UI 或字段表细化。

## 阶段 14：测试性能与分层优化

目标：

1. 解决 `tests/code` 全量慢、并行运行可能 OOM 的风险；
2. 把 e2e / runtime 慢测试拆成更清晰的 tier；
3. 保持 `smoke` 日常快反馈、`targeted` 风险覆盖、`full` 阶段收口的职责边界。

完成记录：

阶段 14A 已补充分层测试契约和 runner 支持，记录见 `_migration/14A-test-tiering-performance.md`。本阶段新增 runtime profile 与 targeted slow policy，不删除慢测试、不降低 full regression，也不默认并行化 slow 层。

## 阶段 15：runtime 自动入口评估

目标：

1. 调查当前协作环境是否存在真实 session start、pre tool use 或 completion claim 触发点；
2. 没有真实触发点时继续保持 deferred，不反复讨论；
3. 有真实触发点时，先补 payload、失败处理、安装状态、回滚、测试和 Human Gate，再判断是否 integrated。

完成记录：

阶段 15A 已完成 runtime 自动入口复核，记录见 `_migration/15A-runtime-auto-entry-assessment.md`。当前除 `git.commit-msg` 外没有可升级为 integrated 的自动入口；manual runtime 三件套继续后置，不再重复讨论，除非出现真实触发点和完整接入证据。

## 阶段 16：稳定 receipt 存储

目标：

1. 判断哪些 receipt 值得长期保存；
2. 定义事实源位置、字段、保留策略和清理策略；
3. 防止 stdout-only 过程输出直接升级为事实源。

完成记录：

阶段 16A 已完成 receipt 存储判断，记录见 `_migration/16A-receipt-storage-decision.md`。当前不建立独立 runtime receipt 事实源；需要长期保留的内容先由 AI 定性，再分流到既有验证证据、WorkCase、Git commit records、迁移记录或事实对象。

## 阶段 17：Web Confirm UI 与通用写入

目标：

1. 先做 Confirm UI 最小闭环；
2. 再评估通用 Web 写入；
3. 继续保持 Web 独立读取事实源，不依赖 Code 输出作为页面/API 主数据源。

完成记录：

阶段 17A 已完成 Web Confirm UI 与通用写入边界判断，记录见 `_migration/17A-web-confirm-ui-write-boundary.md`。当前 Spark quick create 仍是唯一正式 Web 写入；通用事实对象写入、WorkCase 状态推进写入和完整 Confirm UI 继续后置，启用前必须重新进入 Human Gate 和 tests/web 合同验证。

## 阶段 18：外部受管项目 Hook adapter

目标：

1. 复用 `specs/10-安装与配置规范.md` 的 target-first 和 Git common-dir；
2. 支持安装、状态检查、回滚和验证；
3. 不默认覆盖外部项目，不绕过 Human Gate。

完成记录：

阶段 18A 已完成外部受管项目 Hook adapter，记录见 `_migration/18A-governed-project-hook-adapter.md`。新增 `code/governed_hook_adapter.py`，在 install/uninstall 前先做受管项目解析并要求显式 Human Gate；当前没有自动安装到任何外部项目，除当前 worktree 的 `git.commit-msg` 外，其它自动入口仍未 integrated。

## 阶段 19：`_migration` 归档判断

目标：

1. 判断 `_migration/tests` 是否已有稳定替代；
2. 判断 mapping evidence 和历史 source_ref 是否仍需要 `_migration`；
3. 经 Human Gate 后再决定归档、删除或继续保留。

完成记录：

阶段 19A 已完成 `_migration` 归档判断，记录见 `_migration/19A-migration-archive-decision.md`。当前 `reviews/formal`、`tests/code/test_formal_specs.py`、`code/test_runner.py`、`code/ldvh_specs.py` 和 `_migration/tests` 仍依赖 `_migration`；因此本阶段决定继续保留，不删除 tracked 迁移材料，不移动目录，不重写 formal review evidence。

## 停止条件

出现以下情况时，暂停并回到 Human Gate 或对应正式规范：

1. 后续工作试图把实践细节写成 specs 规则；
2. 后续工作试图把后置能力写成已 integrated；
3. 后续工作需要恢复 Rules / Skill 顶层机制；
4. 后续工作需要扩大真实 Hook、Web 写入或外部项目安装范围；
5. 后续工作缺少验证入口，却要声明完成。
