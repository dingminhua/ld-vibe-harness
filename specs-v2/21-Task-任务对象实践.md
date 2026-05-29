# Task-任务对象实践

> 创建日期：2026-05-28
> 对象名：Task / 任务
> 适用范围：所有接入 PM Kit 且需要管理可执行任务的项目
> 上位依据：`specs-v2/00-PMKit理念与纲要.md`、`specs-v2/14-管理对象规范.md`、`specs-v2/10-事实源规范.md`、`specs-v2/11-AI协作规范.md`、`specs-v2/12-程序辅助规范.md`、`specs-v2/13-工具展示规范.md`

---

## 一、对象定位与准入

### 1.1 Task 与 Work

Work 是广义工作或候选工作事项，不默认成为独立事实源对象。AI 可以执行许多 Work，但不得因为某个行动是 Work 就自动创建 Task。

Task 是符合准入条件、进入 PM Kit 管理系统的 Work。所有 Task 都是 Work，但不是所有 Work 都是 Task。

一个 Task 至少应具备：

1. 明确目标；
2. 执行边界；
3. 可检查的完成标准；
4. 验证方式；
5. 状态流转；
6. 关闭证据或关闭授权。

### 1.2 Task 准入条件

一个 Work 需要满足以下至少一类管理需求，才应升级为 Task：

1. 需要独立追踪状态；
2. 需要跨会话或跨执行轮次继续推进；
3. 需要可验证完成标准；
4. 需要关闭证据；
5. 需要人类验收或关闭授权；
6. 需要关联 Requirement、ADR、Risk、Dependency 或 Evidence；
7. 需要被工具展示、排序、过滤、聚合或审计；
8. 不升级为 Task 就会导致进度、责任、完成标准或验证结果不可追踪。

以下内容通常不应单独升级为 Task：

1. 读取文件；
2. 搜索引用；
3. 当前 Task 内的一次性分析；
4. 当前 Task 内的一次性检查命令；
5. 当前 Task 内的局部小修改；
6. 不需要跨会话追踪的临时执行步骤；
7. 已由当前 Task 的计划、清单或执行记录覆盖的子步骤；
8. 仅表达想法、发现、提醒但尚未形成明确目标的输入。

### 1.3 Task 与 Task Set

Task Set 是围绕同一需求、阶段、发布或目标组织的一组 Task。Task Set 不一定需要独立结构化文件，可以由 Requirement、阶段目标、发布目标或工具聚合视图承载语义。

Task 通过关联 Requirement 或其他目标事实源形成 Task Set 视图。当前 `pm-kit-base/tasks/` 中，任务通过 `requirement_doc` 关联需求文档，工具可据此聚合同一需求下的任务集合。

### 1.4 Task 最低颗粒度

Task 是最小可执行、可追踪、可验证、可关闭对象。Task 可以有子任务，但不是所有步骤都需要创建子任务。

只有当子步骤需要独立跟踪、独立验收、独立关闭、独立依赖、跨执行者协作，或父任务不拆分就无法判断进度时，才创建子任务。

需求文档中的拆分、步骤、章节或 MVP 列表默认只是计划结构，不等同于 Task。只有被写入 Task 事实源且具备独立状态、验收和关闭条件的对象，才是正式 Task 或子 Task。

---

## 二、事实源边界

> 事实源边界声明：本文档是 Task 对象实践的权威事实源。本文档定义 Task 的准入条件、状态机、字段契约、对象关系和适配规则。本文档不重新定义管理对象语义（见 14）、事实源载体规则和格式契约（见 10）、AI 协作总原则（见 11）、程序辅助总原则（见 12）、工具展示总原则（见 13）。

Task 的权威事实源为项目 Kit Base `pm-kit-base/tasks/` 目录下的 YAML 文件。Task 的结构化字段、状态机和格式契约依据 10 §12.1 和 §12.2 的基础字段约定，本文档定义 Task 特有的扩展字段。

聊天记录、工具缓存、数据库派生视图、运行时索引和 UI 状态都不能成为 Task 状态的权威位置。

---

## 三、状态机

### 3.1 标准状态

Task 标准状态如下：

| 标准状态 | 含义 |
|---|---|
| Ready for Plan | 刚进入系统或已评估，等待规划 |
| Planned | 已有计划，等待执行 |
| Executing | 正在执行 |
| Blocked | 被外部因素阻塞 |
| Decision Needed | 需要人类决策才能继续 |
| Review Needed | 执行完成，等待验收或 Review Gate 检查 |
| Closed | 已完成、验收通过并经人类授权关闭；稳定终态 |
| Cancelled | 不再执行 |

### 3.2 合法状态流转

```text
Ready for Plan → Planned, Cancelled
Planned → Executing, Blocked, Decision Needed, Cancelled
Executing → Blocked, Decision Needed, Review Needed, Cancelled
Blocked → Executing, Decision Needed, Review Needed, Cancelled
Decision Needed → Planned, Executing, Blocked, Review Needed, Cancelled
Review Needed → Executing, Decision Needed, Closed, Cancelled
Closed → 无
Cancelled → Ready for Plan, Planned
```

未在上述规则中列出的流转为非法流转，工具应拒绝执行。

`Closed` 是稳定终态。关闭后发现新增问题或返工需求时，必须新建 Task 承接，不得直接重开原 Task。

### 3.3 完成标准要求

正式 Task 必须具备可检查的完成标准。

`Ready for Plan` 状态允许完成标准暂为空，用于承载刚进入系统、尚待规划的执行对象。Task 进入 `Planned`、`Executing`、`Blocked`、`Decision Needed`、`Review Needed`、`Closed` 前，必须补齐可验证的完成标准。

工具或 AI 在执行状态流转时，应拒绝缺少完成标准的 Task 进入 `Planned` 及后续状态。

### 3.4 状态变更先于执行

执行者在执行 Task 时，必须同步更新 Task 事实源中的任务状态。状态变更是执行动作的前置步骤，不是事后补录。

触发点与同步要求：

| 触发点 | 状态变化 | 必填字段 |
|---|---|---|
| 开始执行 | Planned / Ready for Plan → Executing | status、updated、acceptance |
| 完成执行 | Executing → Review Needed | status、updated、review.required、acceptance |
| 遇到阻塞 | 任意允许来源 → Blocked | status、updated、block_reason |
| 需要决策 | 任意允许来源 → Decision Needed | status、updated、decision_point |
| 任务关闭 | Review Needed → Closed | status、updated 及全部关闭必填字段 |

违反状态同步规则的审计发现级别应为 high。

### 3.5 必须填写原因的流转

以下流转必须填写原因，否则工具应拒绝执行：

| 流转 | 必须填写 |
|---|---|
| Executing → Blocked | 阻塞原因 |
| Executing → Cancelled | 取消原因 |
| Planned → Cancelled | 取消原因 |
| Blocked → Cancelled | 取消原因 |
| Decision Needed → Cancelled | 取消原因 |
| Review Needed → Decision Needed | 决策问题 |
| Review Needed → Executing | 回退原因 |

### 3.6 Review Needed 与 Review Gate

`Review Needed` 不等于 `Closed`，也不等于已经可以提交人类验收。`Review Needed` 表示执行者认为执行已完成，但关闭前仍需要 Review Gate 或 Human Gate 检查。

当 `review.required == true` 时，Task 进入 `Closed` 前必须满足以下任一条件：

1. `review.status == passed && review.human_ready == true`；
2. `review.status == skipped` 且记录了跳过原因。

`review.status` 语义如下：

| review.status | 含义 | human_ready |
|---|---|---|
| pending | 开发完成，等待审查 | false |
| passed | 审查通过 | true |
| failed | 审查失败 | false |
| needs_human | 需要人类决策 | false |
| skipped | 无需审查，需记录原因 | true |

只有 Review Gate 通过或被有原因地跳过后，才允许继续判断是否满足 Human Gate 的关闭授权。

### 3.7 自动修复约束

当 Task 使用自动修复流程时，自动修复次数上限为 3。当 `attempt_count >= max_attempts` 时，自动流程必须停止，Task 应进入 `Decision Needed`。

以下情况必须立即停止自动流程，不等待次数耗尽：

1. 无新变更；
2. 需求不清；
3. 修改范围扩大；
4. 跨项目影响；
5. 需要新增依赖；
6. 需要创建或修改 Skill、Agent；
7. 需要修改规则；
8. 存在安全风险。

### 3.8 关闭条件

Task 进入 `Closed` 前，必须补齐以下内容：

| 内容 | 含义 |
|---|---|
| completion_summary | 完成摘要 |
| validation_result | 验证结果 |
| closure_evidence | 关闭证据 |
| acceptance_result | 验收结果 |

缺少任一内容，工具应拒绝关闭操作。

Task 关闭必须经过人类授权。AI 可以整理关闭证据、验证结果和建议结论，但不得自行绕过 Human Gate 将需要人类确认的 Task 关闭。

### 3.9 取消与历史保留

Task 不应被删除来掩盖历史。取消的 Task 应通过 `Cancelled` 状态保留历史记录。

工具 API 不应提供删除 Task 的常规端点。若底层 Git 文件因文档治理、迁移或用户明确要求被删除，应通过 Git 历史追溯，并确保不是为了绕过状态、证据或验收规则。

---

## 四、字段契约

### 4.1 基础字段

Task 基础字段对齐 10 §12.2：`id`、`type`、`title`、`status`、`created`、`updated`。

### 4.2 Task 扩展字段

10 当前未定义 Task 格式契约，本文档定义 Task 特有的扩展字段：

| 字段 | 必须 | 约束 |
|---|---|---|
| `priority` | 是 | 合法值：P0、P1、P2、P3 |
| `requirement_doc` | 否 | 关联的需求文档路径 |
| `parent_id` | 否 | 父任务 ID |
| `dependencies` | 否 | 依赖的任务 ID 列表 |
| `acceptance` | 条件必须 | Ready for Plan 允许为空，Planned 及后续状态必须具备可检查的验收标准 |
| `closed_at` | 条件必须 | 仅当 status 为 Closed 或 Cancelled 时必须填写 |
| `completion_summary` | 条件必须 | 仅当 status 为 Closed 时必须填写 |
| `validation_result` | 条件必须 | 仅当 status 为 Closed 时必须填写 |
| `closure_evidence` | 条件必须 | 仅当 status 为 Closed 时必须填写 |
| `acceptance_result` | 条件必须 | 仅当 status 为 Closed 时必须填写 |
| `block_reason` | 条件必须 | 仅当 status 为 Blocked 时必须填写 |
| `decision_point` | 条件必须 | 仅当 status 为 Decision Needed 时必须填写 |
| `review` | 条件必须 | 见 §4.3 |
| `auto_fix` | 条件必须 | 见 §4.4 |
| `source` | 是 | 来源，合法值：manual、conversation、audit |
| `tags` | 否 | 标签列表 |

### 4.3 review 子字段

| 字段 | 必须 | 约束 |
|---|---|---|
| `review.required` | 是 | 是否需要 Review，boolean |
| `review.status` | 条件必须 | 仅当 review.required 为 true 时必须填写，合法值：pending、passed、failed、needs_human、skipped |
| `review.reviewer` | 否 | 审查者 |
| `review.human_ready` | 条件必须 | 仅当 review.required 为 true 时必须填写，boolean |
| `review.summary` | 否 | 审查摘要 |
| `review.findings` | 否 | 审查发现列表 |
| `review.checked_at` | 否 | 审查日期 |
| `review.reason` | 条件必须 | 仅当 review.status 为 skipped 时必须填写，跳过原因 |

### 4.4 auto_fix 子字段

| 字段 | 必须 | 约束 |
|---|---|---|
| `auto_fix.enabled` | 是 | 是否启用自动修复，boolean，默认 false |
| `auto_fix.attempt_count` | 条件必须 | 仅当 auto_fix.enabled 为 true 时必须填写 |
| `auto_fix.max_attempts` | 条件必须 | 仅当 auto_fix.enabled 为 true 时必须填写，默认 3 |
| `auto_fix.lock_id` | 否 | 自动修复锁标识 |

### 4.5 文件命名

文件命名格式依据 10 §12.1：

```text
pm-kit-base/tasks/task-{语义标识}.yaml
```

语义标识为该任务的唯一标识或语义标题，英文小写、单词间用中划线。文件名只承载静态类型与标识，禁止将动态状态字段写入文件名。

---

## 五、与其他对象的关系

### 5.1 转化关系

Task 可从以下对象转化而来：

```text
Intent → Requirement → Task
Memo → Task
Audit 发现 → Task
ADR → Task（决策需要执行时）
Risk → Task
```

转化必须满足 Task 准入条件（见 §1.2），转化后源对象状态应标记为已转化，并记录关联 Task ID。转化不得丢失源对象的背景和原因。转化操作须经 Human Gate 评估。

Task 可转化为以下对象：

```text
Task evidence → ADR
Task → Change（任务执行产生实际变更时）
Task → Evidence（任务完成产生验证证据时）
```

### 5.2 依赖关系

Task 可以依赖其他 Task、Risk 或 Dependency。依赖用于判断 Task 是否可执行、是否可关闭。

依赖原则：

1. 依赖关系应显式记录在 `dependencies` 字段中；
2. 阻塞性依赖应被识别和追踪；
3. 依赖解除后应更新 Task 状态。

### 5.3 引用关系

Task 可以引用 Requirement、ADR、Memo、Evidence、Change 等对象。引用通过 `requirement_doc`、`parent_id`、`dependencies` 等字段建立。

引用用于建立语义关联，不表示执行顺序或阻塞关系。对象被引用不等于对象不可关闭或不可修改。

---

## 六、初始化检查项

创建本文档时必须确认以下事项，对齐 14 §3.2 初始化维度：

1. Task 是否满足 14 §9.2 的准入条件：Task 已出现稳定的状态机、字段定义和转化关系，需要独立追踪、独立校验和独立 Human Gate，需要被 AI 高频读取、被程序解析或被工具展示，实践规则具有跨项目复用价值；
2. Task 的状态机是否稳定：8 个标准状态和合法流转路径已在实践中验证；
3. Task 的字段契约是否可定义：基础字段对齐 10 §12.2，扩展字段已在本文档完整定义；
4. Task 的初始化检查项和审计检查项是否可声明：本文档 §6 和 §7 已逐一声明；
5. Task 与 10-13 的适配关系是否可表达：本文档 §8-§11 已声明适配关系。

---

## 七、审计检查项

审查本文档时必须检查以下标准，对齐 14 §3.2 审计维度：

1. 本文是否遵守 14 §9.8 禁止扩张规范：未新增基础规范层已有规则的变体或例外，未扩张基础规范层定义的概念边界，未重写基础规范层的规则正文，未替代基础规范层的权威地位；
2. 本文的适配声明是否与 10-13 一致：§8-§11 的适配声明未重新定义各层规范已有规则；
3. 本文的状态机是否与 14 §六的状态变更原则一致：状态变更先于执行、终态不得重开、不得通过删除掩盖状态历史、Human Gate 流转需人类确认；
4. 本文的字段契约是否与 10 的格式契约对齐：基础字段对齐 10 §12.2，扩展字段未与基础字段冲突；
5. 本文的初始化检查项和审计检查项是否完整且可执行：§6 和 §7 逐一列出检查标准。

---

## 八、AI 协作适配

本节声明 Task 对象的 AI 协作适配规则，对齐 11。AI 协作总原则的权威定义在 11，本文档只声明 Task 的协作适配方式。

### 8.1 AI 读取 Task

AI 进入项目后，应从项目 Kit Base `pm-kit-base/tasks/` 读取 Task 事实源。AI 不得从聊天记录、工具缓存或数据库派生视图读取 Task 状态。

### 8.2 AI 执行 Task

AI 执行 Task 时，必须遵守以下约束：

1. 执行前必须同步 Task 状态到事实源（见 §3.4）；
2. 执行前必须确认 Task 处于允许执行的状态；
3. 执行前必须确认 Task 具备可检查的完成标准（`Ready for Plan` 除外）；
4. AI 不得绕过 Review Gate 直接关闭 Task；
5. AI 不得绕过 Human Gate 将需要人类确认的 Task 关闭。

### 8.3 AI 回写 Task

AI 完成执行后，必须将验证结果和关闭证据写入 Task 事实源。证据不得只停留在聊天记录中。

### 8.4 AI 判断 Human Gate

AI 在以下 Task 相关场景必须暂停并等待人类确认：

1. Review Needed → Closed：验收确认与关闭授权；
2. Decision Needed → Planned / Executing：决策记录；
3. 创建会影响多个项目、规则、Skill、Agent 或工具边界的 Task；
4. 关闭缺少明确验收依据或验证证据的 Task；
5. 跳过 Review Gate；
6. 取消高优先级、阻塞性或已承诺交付的 Task。

---

## 九、Human Gate

### 9.1 必须触发 Human Gate 的流转

| 流转 | 需要确认的内容 |
|---|---|
| Review Needed → Closed | 验收确认与关闭授权 |
| Decision Needed → Planned | 决策记录 |
| Decision Needed → Executing | 决策记录 |

### 9.2 应评估 Human Gate 的场景

1. 创建会影响多个项目、规则、Skill、Agent 或工具边界的 Task；
2. 将原本只是 Memo、Intent 或临时 Work 的内容升级为高影响 Task；
3. 关闭缺少明确验收依据或验证证据的 Task；
4. 跳过 Review Gate；
5. 取消高优先级、阻塞性或已承诺交付的 Task；
6. 改变 Task 的事实源载体、状态机、关闭规则或 Review Gate 语义。

### 9.3 检查要求

| 检查项 | 标准 |
|---|---|
| 准入判断 | 未把临时行动、一次性分析或当前 Task 内步骤过度任务化 |
| 状态合法 | 状态属于标准状态，流转属于合法流转 |
| 状态同步 | 执行前已按触发点同步状态和必填字段 |
| 完成标准 | Planned 及后续状态具备可检查完成标准 |
| Review Gate | Review Needed 任务具备 review 状态和 human_ready 口径 |
| 关闭证据 | Closed 前具备完成摘要、验证结果、关闭证据和验收结果 |
| Human Gate | 需要人类确认的流转未被 AI 或工具绕过 |
| 历史保留 | Cancelled 和 Closed 保留历史，不通过删除掩盖状态 |

---

## 十、程序辅助适配

本节声明 Task 对象的程序辅助适配规则，对齐 12。程序辅助总原则的权威定义在 12，本文档只声明 Task 的辅助适配方式。

### 10.1 程序解析 Task

程序解析 Task YAML 文件时，应依据 10 §12.2 的基础字段和本文档 §4 的扩展字段进行解析。解析失败时应报告具体的失败位置、期望格式和实际内容，不得静默跳过。

### 10.2 程序校验 Task

程序校验 Task 时，至少应覆盖：

| 校验类型 | 校验对象 | 校验依据 |
|---|---|---|
| 字段完整性 | Task 必填字段和条件必填字段 | 本文档 §4 |
| 状态合法性 | Task 状态流转路径 | 本文档 §3.2 |
| 引用有效性 | requirement_doc、parent_id、dependencies | 项目文件存在性 |
| 格式合规性 | 文件命名、YAML 字段 | 10 §12.1、§12.2 |

### 10.3 程序聚合 Task

程序可以聚合项目 Task 状态、Task Set 视图、依赖关系和审计结果。聚合输出属于派生视图数据，不是事实源。

### 10.4 程序受控写入 Task

程序写入 Task 事实源时，必须遵守 12 §八 受控写入原则。写入前必须校验状态流转合法性和字段完整性。程序不得自动修改 Task 状态、关闭 Task 或绕过 Human Gate。

---

## 十一、工具展示适配

本节声明 Task 对象的工具展示适配规则，对齐 13。工具展示总原则的权威定义在 13，本文档只声明 Task 的展示适配方式。

### 11.1 工具展示 Task

工具可以展示 Task 列表、状态、优先级、依赖关系、Review 子状态、关闭证据和待确认事项。工具展示必须可追溯到 Git 文件事实源。

### 11.2 工具展示 Review 子状态

工具展示 Task 的 Review 子状态时，应展示 `review.status`、`review.human_ready` 和 `review.reason`（当 skipped 时）。工具不得将 Review 子状态作为独立事实源维护。

### 11.3 工具受控写入 Task

工具通过受控写入入口修改 Task 事实源时，必须遵守 13 §七 受控写入原则。写入后必须触发项目的 Change 记录。

### 11.4 工具不得维护第二事实源

工具不得维护与 Git 文件不一致的 Task 权威状态。工具缓存和数据库只能作为派生层，失效或重建后不影响事实源完整性。

---

## 十二、待补齐事项

1. Task YAML 扩展字段是否需要在 10 中补齐格式契约，待后续对象实践稳定后确认；
2. Evidence 与 Review 是否拆成独立对象子规范，需等待 Task 关闭证据和验收实践稳定；
3. PM Web Tools 如何展示 Task、Review 子状态、Human Gate 和关闭证据，需由后续工具展示实践展开；
4. Skill / Agent 如何围绕 Task 创建、审查、验收和回写证据，需由后续 AI 协作实践展开；
5. 自动修复相关字段是否作为长期 schema 固化，需等待更多实践验证；
6. Task 文件命名是否需要从 `{PREFIX}-{NNNN}` 迁移到 10 §12.1 定义的 `task-{语义标识}` 格式，待迁移实践确认。
