# Pitfall 踩坑

> 创建日期：2026-06-03
> 定位：定义 Pitfall 踩坑记录工作模型，包括对象定位、准入条件、事实源边界、状态机、对象关系、Human Gate、字段契约、事实源回写、证据留存、适配原则、机制适配边界和对象特有实例检查
> 适用范围：所有接入 LDVH 且需要沉淀已解决踩坑经验的项目
> 上位依据：`specs/07-工作模型基础规范.md`
> 相关规范：`specs/00-LD-Vibe-Harness理念与纲要.md`、`specs/03-文档规范.md`、`specs/04-事实源边界与承载规范.md`、`specs/05-Trae-Solo环境规范.md`、`specs/06-Python与Web工具规范.md`、`specs/20-工作模型集合索引.md`

---

---
## 1. 本文解决的问题

本文定义 Pitfall 踩坑记录工作模型。Pitfall 是已解决且具有复用价值的踩坑经验，用于沉淀反直觉问题、误判原因、解决方式、验证结果和后续规避策略，帮助 AI、人和工具在后续执行中提前避坑。

本文只定义 Pitfall 对象模型。Pitfall 相关 Rules、Skill、Agent、Tools 契约式校验与执行和 Web 信息同步实践按 §12 机制适配边界和 07 §4.6 承接。

---

## 2. 与 07 的关系

`specs/07-工作模型基础规范.md` 定义工作模型通用规则、文件命名、主规范结构、机制适配边界和工作模型标准组成。本文依据 07 §4.2 定义 Pitfall 对象模型。

本文不重新定义 07 中的通用规则。发生冲突时，以 07 及其上位基础规范为准，除非本文明确说明例外并经 Human Gate 确认。

---

## 3. 对象定位与准入条件

### 3.1 Pitfall 定义

Pitfall 是已解决且具有复用价值的踩坑经验。Pitfall 应记录问题现象、触发条件、误判原因、根因、解决方式、验证结果、规避策略和适用范围。

Pitfall 不是所有问题、Bug、临时错误或失败尝试的默认归宿。只有当问题已经解决，且后续执行可能复现同类误判或重复踩坑时，才应进入 Pitfall 事实源。

### 3.2 Pitfall 与临时问题

临时问题是执行过程中的局部故障、探索失败或一次性误操作，不默认成为 Pitfall。临时问题可以留在当前执行上下文、Task 证据、Evidence、Change 或审计材料中。

一个 Pitfall 至少应具备：

1. 明确的问题现象；
2. 已确认的触发条件或适用场景；
3. 已识别的误判原因或根因；
4. 已验证的解决方式；
5. 后续可执行的规避策略；
6. 可追溯的状态。

### 3.3 Pitfall 准入条件

当一个经验满足以下条件之一时，应考虑形成 Pitfall：

1. 问题已经解决，且解决方式已验证；
2. 问题具有反直觉性，AI 或人后续容易重复误判；
3. 问题跨任务、跨会话或跨项目具有复用价值；
4. 问题暴露了事实源读取、工具使用、验证命令、规则入口或协作流程中的稳定陷阱；
5. 同类问题已经出现多次，需要形成规避策略；
6. 问题可作为 Rules、Skill、Tools、Web 或工作流程后续改进的输入。

不满足 Pitfall 准入条件的临时信息，可以先作为 Memo、Task 证据、Evidence 或当前执行记录保留。

以下内容通常不应单独形成 Pitfall：

1. 尚未解决的问题；
2. 未验证的猜测；
3. 只影响当前一次执行且没有复用价值的错误；
4. 已由 specs、Rules 或 ADR 明确约束且没有新经验的信息；
5. 单纯的命令输出、日志片段或失败记录；
6. 没有规避策略的抱怨或复盘感想。

### 3.4 Pitfall 与 Rules / Skill / Tools 的边界

Pitfall 记录为什么会踩坑、如何解决和以后如何规避；Rules 记录必须遵守的高频行为边界；Skill 记录可复用流程；Tools 记录确定性解析、校验、聚合和受控写入能力。

当 Pitfall 中的规避策略需要形成长期强制行为时，应将规则正文写入 specs 或 Rules，Pitfall 保留问题背景、根因和验证证据。Pitfall 不替代 specs 规范正文，不替代 Rules 执行入口，不替代 Task、Evidence、Change 或 ADR 的事实源。

---

## 4. 事实源边界

本文是 Pitfall 踩坑记录工作模型的权威事实源。本文定义 Pitfall 的准入条件、状态机、对象关系、Human Gate、字段契约和适配原则。

Pitfall 对象实例的权威事实源位置为：

```text
ldvh-base/pitfalls/pitfall-{NNNN}-short-title.yaml
```

编号从 `0001` 开始递增，固定 4 位；英文短标题使用小写短横线；每个项目独立编号，不使用跨项目全局编号。

| 内容 | 权威位置 |
|---|---|
| Pitfall 对象模型 | `specs/23-Pitfall-踩坑.md` |
| Pitfall 对象实例 | `ldvh-base/pitfalls/` |
| Pitfall 展示或聚合视图 | `web/` 或 `tools/` 的派生输出，不作为最终事实源 |

---

## 5. 状态机

### 5.1 标准状态

Pitfall 标准状态如下：

| 标准状态 | 含义 |
|---|---|
| `draft` | 已记录草稿，尚未确认符合准入条件或字段完整性不足 |
| `active` | 已确认且可作为后续执行参考 |
| `superseded` | 已被新的 Pitfall、Rules、Skill、Tools 或规范替代 |
| `archived` | 已归档，不再作为常规参考，但保留历史 |

### 5.2 合法状态流转

```text
draft → active, archived
active → superseded, archived
superseded → 无
archived → 无
```

未在上述规则中列出的流转为非法流转，Tools 辅助和工具应拒绝执行。

`superseded` 和 `archived` 是稳定终态。终态 Pitfall 不得重开；如需重新沉淀，应新建 Pitfall 承接，并在新 Pitfall 中引用原 Pitfall。

`draft` 状态的 Pitfall 不应作为后续执行依据。只有 `active` 状态的 Pitfall 才表示已确认、可作为后续执行参考的踩坑经验。

---

## 6. 与其他对象的关系

### 6.1 Task / Evidence → Pitfall

当 Task 执行过程或 Evidence 中出现已解决且具有复用价值的踩坑经验时，可将该经验整理为 Pitfall。

转化条件：

1. 问题已经解决；
2. 解决方式已经验证；
3. 经验满足 Pitfall 准入条件；
4. 已获得 Human Gate 确认。

转化后，Pitfall 的 `source_objects` 字段应记录来源 Task ID 或 Evidence ID。Task 和 Evidence 侧的记录方式由对应对象模型定义。

### 6.2 Memo → Pitfall

当 Memo 中保留的发现、提醒或复盘内容满足 Pitfall 准入条件时，Memo 可转化为 Pitfall。

转化条件：

1. Memo 内容不是未解决猜测；
2. 已补齐问题现象、根因、解决方式和验证结果；
3. 已获得 Human Gate 确认。

转化后，Pitfall 的 `source_objects` 字段应记录来源 Memo ID。Memo 侧的状态和回链字段由 Memo 对象模型定义。

### 6.3 Pitfall 与 Rules / Skill / Tools

Pitfall 和 Rules / Skill / Tools 是独立对象，不存在转换关系。当 Pitfall 中的规避策略、流程修正或工具需求需要成为稳定协作机制时，应创建新的 Rules、Skill 或 Tools 实体承接，Pitfall 保留不删除。

满足以下条件之一时，应考虑分流：

1. 规避策略需要成为强制规则；
2. 解决流程需要重复执行并可标准化；
3. 校验、筛选、聚合或写入动作可机械化；
4. 问题多次出现，需要改变 AI、人或工具的长期行为；
5. 影响事实源边界、Human Gate、检查要求或对象关闭方式。

分流后应保持：

```text
Pitfall 记录踩坑事实、根因、解决方式和经验来源（保留，不删除）
Rules / Skill / Tools 记录以后必须怎么做或如何机械化执行（新增，独立对象）
```

分流操作必须：

1. 将规则正文、流程实践或工具契约写入对应事实源（创建新实体）；
2. Pitfall 保留问题背景、根因和验证证据，不删除、不转换；
3. 在 Pitfall 的 `related_rules` 或 `related_objects` 字段记录关联的新实体引用；
4. 经 Human Gate 确认。

### 6.4 Pitfall 与 ADR

Pitfall 和 ADR 是独立对象，不存在转换关系。经验是经验，决定是决定，两者可以关联但不可互相替代。

当 Pitfall 暴露的问题需要形成长期决策、改变事实源归属或影响多个工作模型时，应创建新的 ADR。Pitfall 保留踩坑事实和经验不删除，ADR 作为新增决策记录独立存在。Pitfall 通过 `related_objects` 关联 ADR 引用。

当 ADR 的决策执行后踩坑时，应创建新的 Pitfall。ADR 保留决策记录不删除，Pitfall 作为新增经验记录独立存在。Pitfall 通过 `source_objects` 或 `related_objects` 关联 ADR 引用。

### 6.5 不满足准入的信息

不满足 Pitfall 准入条件的信息，应按其性质分流：

1. 尚未任务化但有保留价值 → Memo；
2. 需要执行修复或验证 → Task；
3. 验证结果或关闭证据 → Evidence；
4. 事实源修改记录 → Change；
5. 长期决策 → ADR；
6. 一次性临时信息 → 留在当前执行上下文。

---

## 7. Human Gate

### 7.1 必须触发 Human Gate 的操作

| 操作 | 需要确认的内容 |
|---|---|
| 创建 Pitfall | 准入条件、经验内容、适用范围和是否允许写入 Pitfall 事实源 |
| `draft → active` | 经验已解决、已验证且可作为后续执行参考 |
| `active → superseded` | 替代原因与替代对象 |
| `active → archived` | 归档原因与后续是否仍可参考 |
| Pitfall 分流为 specs、Rules、Skill 或 Tools | 分流内容与事实源归属 |
| Pitfall 文件重命名 | 引用同步更新 |
| 修改已 active Pitfall 的 `avoidance`、`resolution` 或 `root_cause` 字段 | 核心经验内容变更 |

### 7.2 Human Gate 记录要求

Human Gate 确认应保留在对话上下文、相关 Task / Evidence 或受控写入工具记录中。写入 Pitfall 实例时，可在 `verification`、`notes` 或关联对象中保留确认依据，但不得把聊天记忆作为唯一事实源。

---

## 8. 字段契约

Pitfall YAML 字段契约由本文承接，包含字段类别、语义范围和完整 schema。

Pitfall 字段应覆盖：

1. 基础字段：`id`、`type`、`title`、`status`、`created`、`updated`；
2. 问题字段：`symptoms`、`trigger_conditions`、`root_cause`；
3. 经验字段：`resolution`、`verification`、`avoidance`、`applicability`；
4. 关联字段：`source_objects`、`related_objects`、`related_rules`、`superseded_by`；
5. 分类字段：`tags`、`severity`、`repeatability`。

---

## 9. 事实源回写要求

创建或更新 Pitfall 时，应写回对应项目的 `ldvh-base/pitfalls/`。不得只保存在聊天记录、工具输出、临时日志或派生视图中。

涉及 specs、Rules、Skill、Tools、Web 或其他事实实例变更时，应按 Change 工作模型记录变更。Pitfall 不替代 Change；Change 记录事实源实际修改，Pitfall 记录经验沉淀。

---

## 10. 证据留存要求

Pitfall 应保留足够证据，使后续 AI 或人能够判断经验是否可复用。证据可以来自：

1. 相关 Task 或 Evidence ID；
2. 验证命令与结果摘要；
3. 修复前后的现象对比；
4. 关联 Change 或 commit；
5. 相关 ADR、Rules、Skill 或 Tools 修改。

证据摘要应足以支持经验判断，但不得复制大量日志、命令输出或代码片段形成第二事实源。

---

## 11. AI 协作适配

AI 在进入代码、文档、规则或工具修改前，应按项目规则和工作模型入口判断是否需要读取当前项目的 active Pitfall。读取 Pitfall 时，应优先筛选与当前任务类型、目标文件、技术栈、工具命令或事实源类型相关的记录。

AI 发现新的踩坑经验时，应先判断是否满足准入条件；满足时应暂停并通过 Human Gate 确认是否创建 Pitfall。未解决或未验证的信息不得直接写入 active Pitfall。

AI 引用 Pitfall 时，应区分：

1. `active`：可作为后续执行参考；
2. `draft`：只作为待确认经验，不作为执行依据；
3. `superseded`：只作为历史信息，应继续追踪替代对象；
4. `archived`：只作为历史信息。

---

## 12. 机制适配边界

### 12.1 机制承接清单

历史机制文件 23.01-23.06 已删除，内容已回并到本文对应章节。

### 12.2 机制承接适用条件

机制内容已合并到本文、05、06、运行 Rules、未来 Skill/Tools/Web 实现或对应 backlog；历史机制文件 23.01-23.06 已删除。

---

## 13. Tools 契约式校验与执行适配

Pitfall Tools 应依据本文执行字段解析、状态校验、引用检查、状态筛选、聚合查询和受控写入。Tools 不得自行扩张字段契约，不得绕过 Human Gate 创建、激活、归档或替代 Pitfall。

在 Tools 能力未实现前，AI 或人可按本文人工创建或更新 Pitfall，但必须记录降级原因、执行字段检查并按 Change 要求保留变更记录。

---

## 14. Web 信息同步适配

Pitfall Web 展示或编辑入口只能作为派生视图或受控入口，不得成为第二事实源。Web 可展示 active Pitfall、按标签筛选、提示相关任务风险、展示替代链和提供 Human Gate UI。

Web 通用派生视图、Human Gate UI、受控编辑入口和不得维护第二事实源等规则归属 `specs/06-Python与Web工具规范.md`；Pitfall 具体页面、接口、状态呈现和 backlog 归属 `web/`、`web/docs/` 或本文机制适配边界。

Web 写入能力如未来实现，必须通过 Tools 受控写入或等价校验流程写回 `ldvh-base/pitfalls/`。

---

## 15. 对象特有实例检查

检查 Pitfall 工作模型实例是否符合规范时，应确认：

1. 对象定位是否仍为已解决且具有复用价值的踩坑经验；
2. 准入条件是否排除了未解决问题、未验证猜测和一次性临时错误；
3. 事实源是否为 `ldvh-base/pitfalls/`；
4. 状态流转是否符合 §5；
5. 字段契约是否由本文承接；
6. Human Gate 是否覆盖创建、激活、归档、替代和核心经验字段修改；
7. AI 协作是否区分 `active`、`draft`、`superseded` 和 `archived` 的适用性；
8. Tools 和 Web 是否只作为派生或受控入口，不维护第二事实源；
9. 分流到 Rules、Skill、Tools 或 ADR 时是否保持事实源职责分离；
10. `active` Pitfall 是否包含已验证解决方式；
11. `superseded` Pitfall 是否填写替代对象；
12. Pitfall 是否未复制 Task、Evidence、Change、ADR、Rules 或日志形成第二事实源。

本节不定义产品级初始化或产品级审计流程。产品初始化由 42 工作流程负责执行；产品审计由 43 工作流程负责执行。
## 16. 待补齐事项

1. Pitfall Skill 实体待实践稳定后创建；
2. Pitfall Tools 解析、校验、聚合和受控写入能力待通用对象工具框架稳定后实现；
3. Pitfall Web 展示和筛选能力待 Web 信息同步层启动后实现；
4. Pitfall 与 Task、Evidence、Memo、ADR、Change 的跨对象引用校验待对应工作模型全部落地后细化；
5. `severity`、`repeatability` 和 `tags` 的枚举范围待实践验证后收敛。
