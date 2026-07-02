# LDVH V3 只读审核转达文档

> 审核对象：`/Users/dmh2002/poker_hud_projects/ld-vibe-harness-v3`  
> 分支：`dev-v3`  
> 审核性质：只读审核；未修改仓库文件、未提交。  
> 转达目的：判断 V3 是否已达到“可作为主线”的状态，并指出剩余风险与需要 Human Gate 的事项。

---

## 一、总体结论

**结论：有条件通过。**

V3 当前已经基本具备作为主线的条件：

1. `specs/`、`ldvh-base/`、`code/`、`web/`、`tests/`、`reviews/formal/` 的主线分工已经成立；
2. V2 中应迁内容大体已按“已迁入 / 转实现域 / 后置 / 废弃 / legacy evidence”分流；
3. 阶段 12-19 的完成口径总体真实，且多数阶段都明确“不授权新能力立即生效”；
4. 未发现 P0 阻断问题；
5. 未发现明显违反 `specs/00-理念与构成.md` 价值判断的结构性问题。

但目前不建议给“无条件通过”，原因主要有两类：

- **阶段 12 的目标尚未完全干净收口**：部分 specs 正文仍夹带实现域细节、当前实现状态或命令级实践；
- **外部 Hook 安装边界需要进一步收紧表达**：`governed_hook_adapter.py` 本身安全，但底层 `install_git_hooks.py` 仍可被直接调用，存在被误用于外部受管项目、绕过 adapter Human Gate 的风险。

---

## 二、P0 / P1 / P2 问题分级

## P0：阻断问题

**未发现 P0 阻断问题。**

没有发现以下严重问题：

- Human Gate 被直接绕过；
- manual-ready 被误写成 integrated；
- Web 依赖 Code 输出作为主数据源；
- stdout-only receipt 被升级为事实源；
- `_migration/` 被错误当作可删除对象；
- V3 脱离 `00` 的价值锚点。

---

## P1：需要优先处理的问题

### P1-1：阶段 12“specs 只定义规则/契约/边界”的目标未完全达成

**类型：客观缺口。**

涉及文件或段落：

- `specs/06-行动模板基础规范.md:131-139`
- `specs/06-行动模板基础规范.md:145-157`
- `specs/08-Web信息同步规范.md:132`
- `specs/09-测试与验证规范.md:117-123`
- `specs/11-环境适配规范.md:58,94-115,141`
- `_migration/12A-implementation-domain-boundary.md:13-24`

问题说明：

`_migration/12A-implementation-domain-boundary.md` 的阶段目标是：specs 只承载需求、规则、契约、边界、Human Gate、Stop Conditions 和验证要求；实现语言、命令、模块、测试实践应由 `code/`、`web/`、`tests/` 或实现域文档承接。

但当前部分 specs 正文仍包含偏实现域的内容，例如：

- `specs/06` 中写到了 `git status --short --untracked-files=all`、stage、commit validator、提交后交还等执行细节；
- `specs/06` 中 WorkCase 最小行动模板写入 `ldvh-base/workcases/`、状态推进顺序、字段回写位置等具体流程；
- `specs/08` 中写入“V3 当前只迁入 Spark quick create”、`pending`、`source_refs`、legacy 字段等当前实现状态；
- `specs/09` 中写入 smoke / targeted / runtime / full、slow 层不得默认并行、OOM/端口/flaky 等测试运行策略；
- `specs/11` 中写入“当前 worktree 只有 git.commit-msg”、`core.hooksPath=hooks` 等当前环境状态和安装细节。

这些内容并非全部错误，但更像实现域实践文档、迁移记录或 README 当前状态说明。它们与阶段 12 的“specs 不塞实践细节”目标存在张力。

违反依据：

- `specs/04-Specs基础规范.md:306-307`：Code 覆盖状态不应被手写成固定正文清单；
- `specs/04-Specs基础规范.md:353-355`：规则被 Code、review、迁移材料反向改写，或 Code 派生内容手写罗列时应暂停；
- `_migration/12A-implementation-domain-boundary.md:13-24`：实现经验、命令说明、模块说明或测试维护方法应留在实现域。

影响判断：

这不阻断 V3 作为主线，但说明阶段 12 仍存在“概念上完成、正文未完全干净”的风险。

建议：

后续把当前状态、命令实践、测试 runner 细节迁到 `code/docs/`、`web/docs/`、`tests` 或 README；specs 中只保留规则口径、边界和 Human Gate 条件。

---

### P1-2：外部 Hook adapter 安全，但底层安装器仍可能被误用绕过受管项目 Human Gate

**类型：客观缺口。**

涉及文件或段落：

- `code/governed_hook_adapter.py:87-96`
- `code/governed_hook_adapter.py:149-178`
- `code/install_git_hooks.py:149-177`
- `README.md:84-100`
- `_migration/18A-governed-project-hook-adapter.md:38-47,63-67`

判断：

`governed_hook_adapter.py` 本身是安全的：

- 先做受管项目解析和配置校验；
- 非受管 target 会阻断；
- `install/uninstall` 缺少 Human Gate 会阻断；
- 输出中保留 authority、authorization、source_refs、diagnostics。

但底层 `install_git_hooks.py` 仍公开支持：

- `status / install / uninstall`；
- `--repo` 指定目标 repo；
- 没有 Human Gate 参数；
- 不做受管项目解析。

README 虽然同时列出外部受管项目应使用 `governed_hook_adapter.py`，但如果操作者直接使用底层 `install_git_hooks.py` 指向外部 repo，就可能绕过 `specs/10` 的 target-first 解析和 `specs/11` 的 Human Gate 要求。

违反依据：

- `specs/10-受管项目接入规范.md:106-112`：不得用 cwd、路径相似或用户意图替代 target-first 解析；
- `specs/11-环境适配规范.md:167-174`：安装、覆盖、卸载或扩大真实自动 Hook 影响范围必须 Human Gate；
- `specs/11-环境适配规范.md:180-185`：安装或卸载真实入口前没有回滚方式、状态检查和 Human 确认时必须暂停。

影响判断：

这不是 adapter 的实现错误，而是入口暴露边界风险。

建议：

明确把 `install_git_hooks.py` 定位为“当前 LDVH worktree 本地 Hook 安装器 / backend”；外部受管项目只能通过 `governed_hook_adapter.py`。

---

## P2：非阻断但建议收口的问题

### P2-1：`_migration/` 不是正式规则源，但仍被测试、formal review 和 read plan 依赖，README 口径需避免被误解为可删除

**类型：术语 / 口径风险，不是客观阻断。**

涉及文件或段落：

- `README.md:13`
- `_migration/19A-migration-archive-decision.md:19-39,56-75`
- `code/test_runner.py:57-60,148-149`
- `reviews/formal/README.md:7-11`

判断：

README 写明 `_migration/` 是历史迁移证据和迁移测试材料，不作为日常规则源、事实维护入口或正式 review ledger。这个判断本身正确。

但同时：

- `_migration/19A` 明确 `_migration` 仍被 formal review mapping evidence、`tests/code/test_formal_specs.py`、`code/test_runner.py`、`code/ldvh_specs.py`、`_migration/tests` 依赖；
- `code/test_runner.py` 的 full profile 仍运行 `_migration/tests`；
- targeted profile 对 `_migration/code`、`_migration/tests` 等变更仍跑 migration pytest；
- `reviews/formal/README.md` 允许 mapping evidence 回指 `_migration/`。

结论：

`_migration/` 不是正式规则源，但仍是历史证据、迁移测试和 mapping evidence 的稳定承载区。不能删除，不能随意移动。

建议：

README 可补一句：

> 不作为日常规则源 ≠ 可删除；当前 `_migration/` 仍被 formal evidence / test runner / migration tests 依赖。

---

### P2-2：WorkCase 最小行动模板边界正确，但正文实现细节偏重

**类型：客观轻微缺口。**

涉及文件或段落：

- `specs/06-行动模板基础规范.md:145-157`
- `_migration/13A-workcase-minimal-action-template.md:19-23`

判断：

边界是正确的：

- 只支持 `manual_equivalent_execution`；
- 不启用 Web 写入；
- 不安装 Hook；
- 不声明 runtime 自动触发；
- 不创建完整 Confirm UI；
- 不替代 Human Gate。

未发现越权声明自动化、Hook、Web 写入或完整 Confirm UI。

但 `specs/06` 把状态推进顺序、实例路径、字段回写位置写得较具体。它不构成能力越权，但与阶段 12 的“specs 不塞实践细节”存在轻微张力。

建议：

保留规则边界，把具体执行步骤和字段回写实践迁入实现域文档或行动模板实现文档。

---

## 三、关键问题逐项结论

| 检查问题 | 结论 |
|---|---|
| 1. specs 是否只规定需求、规则、契约、边界？ | 大体是，但未完全。`06/08/09/11` 有实现状态、命令、测试实践细节渗入，见 P1-1。 |
| 2. Code、Web、Tests 是否独立实现职责？Web 是否没有依赖 Code 输出作为主数据源？ | 通过。V3 明确 Web 同源独立读取，Code 输出只可作为诊断、验证或测试对照，不作为 Web 主数据源。 |
| 3. WorkCase 最小行动模板是否只是 `manual_equivalent_execution`？ | 通过。未发现越权声明自动化、Hook、Web 写入或完整 Confirm UI。 |
| 4. 测试分层是否合理？是否降低 full regression 覆盖？ | 通过。smoke / targeted / runtime / full 职责清楚；full 包含 smoke、e2e、code + migration pytest、web check/api/build，未降低 full regression。 |
| 5. runtime 自动入口判断是否客观？ | 通过。仅 `git.commit-msg` 为 integrated；manual entrypoints 未误写 integrated。 |
| 6. receipt 存储判断是否合理？ | 通过。stdout-only receipt 明确只是过程输出，不是事实源；当前不建立 dedicated receipt facts。 |
| 7. Web Confirm UI 与通用写入是否正确后置？ | 通过。通用写入、WorkCase 推进、完整 Confirm UI 后置；Spark quick create 仍是唯一正式 Web 写入。 |
| 8. 外部受管项目 Hook adapter 是否安全？ | adapter 本身通过；底层安装器入口暴露有 P1 风险。 |
| 9. `_migration` 是否有充分保留理由？ | 通过。仍被 formal evidence、test runner、migration tests 依赖，不应删除。 |
| 10. V2 未迁内容是否合理分流？ | 基本通过。已分为已迁入、转实现域、后置、废弃、legacy evidence。 |
| 11. 是否存在违反 Human Gate 的地方？ | 未发现 P0。高影响领域大多保留 Human Gate；外部 Hook 底层安装器需收紧说明。 |
| 12. 是否有“概念升级但实现退化”风险？ | 有低到中风险，主要来自 specs 概念升级后仍混入实现细节，可能造成维护分叉；未发现核心能力退化。 |

---

## 四、分类状态表

| 分类 | 内容 |
|---|---|
| 已完成 | V3 主线切换；00-11 主规范体系；事实对象主线；Web 同源独立读取；Spark quick create；commit-msg 最小 hard switch；formal review hash gate；runtime manual 三件套；测试分层；外部 Hook adapter-ready；`_migration` 保留决策。 |
| 仍后置 | 通用 Web 写入；完整 Confirm UI；WorkCase Web 状态推进；session/pre-tool/completion 自动触发；非 Git runtime 自动入口；dedicated receipt storage；外部受管项目真实安装 Hook；更多行动模板正式化。 |
| 建议删除 | 暂无建议删除 tracked 内容。`_migration/` 当前不应删除。只可清理 `.DS_Store` 等无迁移价值本地噪声。 |
| 需要 Human Gate | 扩大 Web 写入；启用完整 Confirm UI；把 manual runtime 入口升级为 integrated；外部受管项目安装/卸载 Hook；移动/删除 `_migration`；新增事实源或 dedicated receipt 存储；改变五类构成要素、状态闭集、事实源归属或 Human Gate 口径。 |

---

## 五、建议转达口径

可以这样转达：

> V3 当前可以作为主线，但建议按“有条件通过”处理。主线能力没有发现 P0 阻断，也没有发现 V2 能力无说明丢失或 Human Gate 被直接绕过。阶段 12-19 总体真实完成，后置项边界也清楚。  
> 需要优先补的是两件事：第一，把 specs 中仍残留的实现细节、当前状态说明、命令实践迁出到实现域文档，完成阶段 12 的真正收口；第二，明确 `install_git_hooks.py` 只能作为当前 worktree / backend 安装器，外部受管项目必须通过 `governed_hook_adapter.py` 并要求 Human Gate。  
> `_migration/` 目前不能删除，它虽然不是日常规则源，但仍被 formal evidence、test runner 和 migration tests 依赖。

---

## 六、剩余风险

1. specs 与实现域边界仍需二次清理，否则阶段 12 会停留在“概念上完成、正文未完全干净”的状态；
2. 外部 Hook 的安全入口是 `governed_hook_adapter.py`，但底层安装器仍需更强说明或保护，避免被误用于外部项目；
3. 当前仓库工作区存在未跟踪目录 `web/design-workspace/`；本次只读审核未判断其内容，不应把它计入已迁入主线能力。

---

## 七、最终判断

**V3 当前是能力增强，不是能力退化；可以作为主线，但应保留条件通过结论，并优先收口 specs / 实现域边界与外部 Hook 安装入口边界。**
