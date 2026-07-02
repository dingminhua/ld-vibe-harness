# 23A V2 关闭与 V3 启动判断

文件状态：transition assessment。本文回答 V3 相对 V2 的主要变动与改进、仍未迁入的 V2 内容、以及 V2 关闭 / V3 启动的判断条件。本文不授权新增自动入口、Web 通用写入、外部项目 Hook 安装或 `_migration` 归档。

## 读取依据

1. `specs/00-理念与构成.md`
2. `specs/01-保障与衔接.md`
3. `specs/03-事实源与Git溯源规范.md`
4. `specs/05-事实模型基础规范.md`
5. `specs/06-行动模板基础规范.md`
6. `specs/08-Web信息同步规范.md`
7. `specs/09-测试与验证规范.md`
8. `specs/10-管辖项目配置规范.md`
9. `_migration/11E-v2-v3-capability-coverage-matrix.md`
10. `_migration/12-19-v3-post-mainline-work-plan.md`
11. `_migration/20-22-conditional-audit-closure.md`
12. `_migration/19A-migration-archive-decision.md`
13. README 当前环境边界

## 当前判断

V3 已具备正式启动为日常主线的条件。V2 可以关闭为历史来源、迁移审计依据和对照材料，不再作为日常规则入口。

这个判断的前提是：

1. 不把后置能力声明成已完成；
2. 不恢复 V2 Rules / Skill / 知识地图顶层机制；
3. 不把 `_migration` 当成正式规则源或事实源；
4. 不把 manual-ready runtime 入口写成 integrated；
5. 不扩大 Web 写入、外部 Hook 安装或 Human Gate 自动完成能力。

## V3 相对 V2 的主要变动与改进

| 领域 | V2 | V3 | 改进点 |
|---|---|---|---|
| 构成骨架 | 规范体系、工作模型、行动编排、Code、Web、运行时扩展等旧表达并存 | 五类构成要素：规范体系、事实模型、行动模板、Code、Web；保障与衔接层不作为第六类 | 归口更清楚，避免运行时资产反向成为构成要素 |
| 规则源 | specs 中混有部分实践、流程、附件长表和实现细节 | specs 只承载需求、规则、契约、边界、Human Gate、Stop Conditions 和验证要求 | 规则更稳定，实践变化由 Code/Web/Tests 实现域承接 |
| 事实模型 | 工作模型 / 工作对象术语与事实源边界混杂 | 统一为事实模型 / 事实对象，20-24 成员规范和 77 个真实实例已迁入 | 事实实例可被 Code/tests 校验，AI 后续可稳定接续 |
| 行动体系 | 30-36 行动编排成员较多，部分依赖 Skill/Rules/Hook 资产 | 行动模板化；Git 提交和 WorkCase 最小手动模板进入 06，其它候选后置 | 避免未接入能力被写成默认流程，同时保留可复用行动结构 |
| Code / Web 边界 | Web 和 Code 容易被理解为共用同一派生数据链 | Web 独立读取 Git 文件事实源和 Web 自有 API；Code 输出只作诊断、验证或对照 | 降低维护耦合，避免 Code DTO 变成 Web 主数据契约 |
| 环境入口 | Rules / Skill / Hook / Runtime Protocol 作为运行时扩展体系 | 入口状态由 01 §6 和 `01.Att.03-06` 管；只有 `git.commit-msg` integrated，其它 manual-ready/deferred | 状态口径可验证，避免把文件存在误写成环境接管 |
| Git 提交 | V2 commit body 要求 `关键变更`，read_plan 是 runtime receipt 证据 | V3 已恢复 V2 commit body 口径；`读取依据` 不再是 commit message 字段 | 纠正 10A 自举折中，职责重新分清 |
| 测试验证 | 全量测试和验证声明边界分散 | `09` 定义验证声明，`code/test_runner.py` 提供 smoke/targeted/runtime/full 分层 | 日常反馈更快，高风险仍保留 full 收口 |
| 迁移证据 | V2 历史材料与正式规则容易混用 | `_migration` 保留为历史证据、mapping evidence 和迁移测试，不作为日常入口 | V3 可以独立运行，同时保留审计链 |

## 已迁入或已承接的 V2 主体内容

| V2 内容 | V3 承接 |
|---|---|
| 00 价值与理念 | `00` 重写为最高价值锚点，明确 AI 第一服务对象、事实源边界、五类构成和 V1-V9 |
| 01 规范体系与术语 | `04`、`04.Att.01-06`、`reviews/formal`、formal hash gate |
| 02 事实模型与 20-24 成员 | `05`、`20`-`24`、`ldvh-base/`、Code/tests schema |
| 03 行动编排父层 | `06` 行动模板基础规范 |
| 04 Code 确定性执行 | `07`、`code/`、`code/docs/`、tests/code |
| 05 Web 信息同步 | `08`、`web/`、`web/docs/`、tests/web |
| 06 运行时扩展父层 | `01` §6、`01.Att.03-06`、environment status/audit Code、runtime manual CLIs |
| 07 事实源与 Git 溯源 | `03`、`03.Att.01`、commit validator、当前 worktree `git.commit-msg` Hook |
| 08 测试基础 | `09`、`09.Att.01`、`tests/`、`tests/docs/`、test runner |
| 31 Git 提交行动 | `06` Git 提交行动模板、`code/commit_validate.py`、`hooks/commit-msg` |
| 管辖项目 / target-first 能力 | `10`、`10.Att.01`、`LDVH-GOVERNED-PROJECTS.yaml`、resolver 和外部 Hook adapter |

## 仍未迁入的 V2 内容

这些内容不是遗漏到无法启动 V3，而是分成后置、转实现域、保留迁移证据或废弃。

| V2 内容 | 当前处理 | 是否阻断 V3 启动 |
|---|---|---|
| V2 30/32/33/34/35/36 行动编排全文 | 不整篇迁入；逐项作为行动模板候选，满足来源、验证、回写、Human Gate 和测试闭环后再迁 | 否 |
| WorkCase 完整 `21.Att.01-orchestration字段契约表` | 当前由 21、06、实例 schema 和 Code/tests 承接；完整长表是否迁正式附件仍后置 | 否 |
| 20-24 完整字段表、成员模板和更细状态条件 | 真实实例和最小成员规范已迁；完整表后续按价值筛选 | 否 |
| V2 04.Att.* Code 命令表、诊断表、知识地图 schema | 有价值部分转为 Code/tests；知识地图相关废弃为 legacy_alias | 否 |
| V2 05.Att.* Web DTO/API/Confirm UI/缓存/回归长表 | Web 父层边界已迁；具体实现域放 `web/docs`、Web 代码和 tests/web；完整 Confirm UI 后置 | 否 |
| V2 06.Att.* 环境适配附件族 | 入口类型、状态、payload、安装回滚已浓缩到 `01.Att.03-06`；薄引用模板、Codex/非 Codex 矩阵、部署长表不逐字迁入 | 否 |
| session_start / pre_tool_use / completion_claim 自动触发 | manual-ready；无真实触发点、payload、失败处理和安装证据前保持 deferred | 否 |
| 外部受管项目真实 Hook 安装 | adapter-ready；未安装到任何外部项目，安装/卸载必须 Human Gate | 否 |
| 稳定 runtime receipt 存储 | 不建立独立 receipt 事实源；需要长期保留的内容分流到 WorkCase、验证证据、Git records 或事实对象 | 否 |
| 通用 Web 写入、WorkCase Web 状态推进、完整 Confirm UI | Spark quick create 是唯一正式 Web 写入；其它必须另走 Human Gate 和 tests/web 合同 | 否 |
| `_migration` 归档或删除 | 仍被 mapping evidence、迁移测试和历史 source_refs 使用；不可删除 | 否 |
| V2 Rules / Skill 顶层目录机制 | 废弃为 legacy_alias 或外部包装候选，不恢复顶层权威 | 否 |
| V2 知识地图事实层 / 页面 / 投影 schema | 由 Action Guide / 行动指南承接导航能力；知识地图不作为 V3 正式概念 | 否 |

## 正式关闭 V2 的条件

V2 关闭不是删除 V2 仓库，也不是抹掉历史；它只表示 V2 不再作为当前 LDVH 的日常规则入口。

关闭条件：

1. Human 明确确认：V3 启动为当前主线，V2 关闭为历史来源；
2. README 和当前规范入口都指向 V3；
3. `specs_validate.py all --fail-on-diagnostics` 通过；
4. `code/test_runner.py smoke` 通过；
5. 当前 worktree `git.commit-msg` Hook 状态可检查；
6. 未跟踪或未归口材料完成分流，不把本地临时目录误当作 V3 正式资产；
7. 后置清单被写明，不作为启动阻断。

## V3 正式启动后的第一批后续工作状态

1. `web/design-workspace/` 已登记为 Web 未来设计参考材料并提交；
2. V2 关闭确认记录已形成，见 `_migration/25A-v2-official-closure.md`；
3. 后续若推进完整 Confirm UI / 通用 Web 写入，先开单独 WorkCase 和 Human Gate；
4. 后续若推进外部项目 Hook 安装，只走 `governed_hook_adapter.py`，并要求显式 Human Gate；
5. 后续若归档 `_migration`，必须先替代 mapping evidence、迁移测试和 source_refs，再经 Human Gate。

## 结论

V3 相对 V2 的升级已经不是简单迁文件，而是完成了职责重构：规则源更窄、事实对象更稳定、行动模板更保守、Code/Web 更解耦、环境入口状态更可验证。

当前仍未迁入的 V2 内容主要是有条件能力，不是主体迁移缺口。Human 已在 2026-07-02 确认 V2 关闭为历史来源，V3 已正式启动；启动后继续按后置清单推进能力建设。
