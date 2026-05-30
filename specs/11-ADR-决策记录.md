# ADR 决策记录

> 创建日期：2026-05-30
> 定位：定义 ADR 决策记录生产对象模型，包括对象定位、准入条件、事实源边界、状态机、对象关系、Human Gate、字段契约、适配原则、执行文件规划和实例检查
> 适用范围：所有接入 LDVH 且需要管理长期决策的项目
> 上位依据：`specs/06-LDVH生产对象基础规范.md`
> 相关规范：`specs/00-LD-Vibe-Harness理念与纲要.md`、`specs/01-specs文档结构规范.md`、`specs/02-LDVH目录说明.md`、`specs/03-事实源边界与承载规范.md`、`specs/04-LDVH-AI协作规范.md`、`specs/05-LDVH工具基础规范.md`、`specs/10-生产对象集合索引.md`

---

## 一、本文解决的问题

本文定义 ADR 决策记录生产对象模型。ADR 是已确认、后续应遵守的决策记录，用于沉淀需要跨会话、跨任务或跨执行轮次追溯的长期决策。

本文只定义 ADR 对象模型。ADR 相关 Rules、Skill、Agent、程序辅助、工具展示、功能初始化和功能审计的执行内容，由 §十二规划的执行文件承载。

---

## 二、与 06 的关系

`specs/06-LDVH生产对象基础规范.md` 定义生产对象通用规则、文件命名、执行文件命名和生产对象模型标准组成。本文依据 06 §4.2 定义 ADR 对象模型。

本文不重新定义 06 中的通用规则。发生冲突时，以 06 及其上位基础规范为准，除非本文明确说明例外并经 Human Gate 确认。

---

## 三、对象定位与准入条件

### 3.1 ADR 定义

ADR 是已确认、后续应遵守的决策记录。ADR 应记录决策内容、背景、原因、选择、影响范围、决策后果和后续约束。

ADR 不是所有判断的默认归宿。AI 可以在当前任务中做临时判断、记录分析结论或选择局部执行策略，但只有满足准入条件、影响长期执行方式或需要跨会话追溯的决策，才应进入 ADR 事实源。

### 3.2 ADR 与临时判断

临时判断是 AI 或人在执行过程中做出的局部选择，不默认成为 ADR。临时判断可以保留在当前执行上下文、Memo、Task 证据或讨论材料中。

ADR 是满足准入条件、进入 LDVH 生产对象体系的决策。所有 ADR 都是判断，但不是所有判断都应成为 ADR。

一个 ADR 至少应具备：

1. 明确的决策内容；
2. 决策背景和原因；
3. 决策后果；
4. 影响范围；
5. 可追溯的状态。

### 3.3 ADR 准入条件

当一个判断满足以下条件之一时，应考虑形成 ADR：

1. 影响多个生产对象；
2. 改变长期执行方式；
3. 改变事实源归属；
4. 形成长期行为边界；
5. 反复出现且需要稳定约束；
6. 影响 AI、人或工具后续协作方式；
7. 影响 specs、Rules、工具或对象模型的长期边界。

不满足 ADR 准入条件的临时判断，可以先作为 Memo、Task 证据或讨论材料保留。

以下内容通常不应单独形成 ADR：

1. 当前 Task 内的局部技术选择；
2. 一次性执行方式调整；
3. 不影响其他对象的临时方案；
4. 尚未稳定的讨论或想法；
5. 已由 specs 或 Rules 明确约束的重复判断；
6. 仅涉及当前会话的执行策略。

AI 不得因为某个判断看起来重要就自动创建 ADR。只有满足准入条件的判断，才应写入 ADR 事实源。

### 3.4 ADR 与 specs / Rules 的边界

ADR 记录为什么这样决定，specs 或 Rules 记录以后必须怎么做。两者不得互相替代。

当 ADR 中的决策升级为长期基础规范时，应将规则正文写入 specs 或 Rules，ADR 保留原因和背景。ADR 不替代 specs 规范正文，不替代 Rules 执行入口，不替代 ldvh-base 中的其他对象状态。

---

## 四、事实源边界

本文是 ADR 决策记录生产对象模型的权威事实源。本文定义 ADR 的准入条件、状态机、对象关系、Human Gate、字段契约和适配原则。

ADR 对象实例的权威事实源位置为：

```text
ldvh-base/adrs/adr-{NNNN}-short-title.yaml
```

编号从 `0001` 开始递增，固定 4 位；英文短标题使用小写短横线；每个项目独立编号，不使用跨项目全局编号。

| 内容 | 权威位置 |
|---|---|
| ADR 对象模型 | `specs/11-ADR-决策记录.md` |
| ADR 对象实例 | `ldvh-base/adrs/` |
| ADR 执行文件 | `specs/11.01-规则.md` 至 `specs/11.07-功能审计.md` |
| ADR 展示或聚合视图 | `web/` 或 `tools/` 的派生输出，不作为最终事实源 |

---

## 五、状态机

### 5.1 标准状态

ADR 标准状态如下：

| 标准状态 | 含义 |
|---|---|
| `proposed` | 已提出，尚未确认 |
| `accepted` | 已确认，后续应遵守 |
| `deprecated` | 已废弃，不再建议遵守，但保留历史 |
| `superseded` | 已被新 ADR 替代 |
| `rejected` | 已否决，不采纳 |

### 5.2 合法状态流转

```text
proposed → accepted, rejected
accepted → deprecated, superseded
deprecated → 无
superseded → 无
rejected → 无
```

未在上述规则中列出的流转为非法流转，程序辅助和工具应拒绝执行。

`deprecated`、`superseded` 和 `rejected` 是稳定终态。终态 ADR 不得重开；如需重新决策，必须新建 ADR 承接，并在新 ADR 中引用原 ADR。

`proposed` 状态的 ADR 不应作为执行依据。只有 `accepted` 状态的 ADR 才表示已确认、后续应遵守的决策。

---

## 六、与其他对象的关系

### 6.1 Memo → ADR

当 Memo 中的输入涉及需要长期追溯的判断或选择，且满足 ADR 准入条件时，Memo 可转化为 ADR。

转化条件：

1. Memo 内容满足 ADR 准入条件；
2. 决策内容已明确，不再只是未任务化输入；
3. 已获得 Human Gate 确认。

转化后，ADR 的 `related_objects` 字段应记录来源 Memo ID。Memo 侧的状态和回链字段由 Memo 对象模型定义。

### 6.2 Task / Evidence → ADR

当 Task 执行过程或 Evidence 中产生的判断满足 ADR 准入条件时，可将该判断升级为 ADR。

转化条件：

1. 判断满足 ADR 准入条件；
2. 判断影响范围超出当前 Task；
3. 已获得 Human Gate 确认。

转化后，ADR 的 `related_objects` 字段应记录来源 Task ID 或 Evidence ID。Task 和 Evidence 侧的记录方式由对应对象模型定义。

### 6.3 ADR → Task

当 ADR 的决策需要具体执行时，应创建 Task 承接执行工作，ADR 保留决策记录。

创建 Task 后，ADR 的 `related_objects` 字段应记录相关 Task ID。Task 的字段、状态和关闭规则由 Task 对象模型定义。

### 6.4 ADR → specs / Rules

当 ADR 满足升级条件时，决策应升级为 specs 或 Rules 中的规则正文。

满足以下条件之一时，应考虑升级：

1. 影响多个项目或所有接入项目；
2. 改变 AI、人或工具的长期行为；
3. 改变事实源归属；
4. 改变 Human Gate 判断；
5. 多次重复出现且需要稳定约束；
6. 影响功能初始化、工具写入或对象关闭方式。

升级后应保持：

```text
ADR 记录为什么这样决定
specs 或 Rules 记录以后必须怎么做
```

升级操作必须：

1. 将规则正文写入 specs 或 Rules；
2. ADR 保留原因和背景，不删除；
3. 在 ADR 的 `related_rules` 字段记录升级后的规则文件；
4. 经 Human Gate 确认。

### 6.5 不满足准入的判断

不满足 ADR 准入条件的判断，应按其性质分流：

1. 有保留价值但暂不任务化 → Memo；
2. 已有明确目标和完成标准 → Task 或现有 Task 的子步骤；
3. 已确认的风险 → Risk；
4. 已确认的依赖 → Dependency；
5. 一次性执行策略 → 留在当前执行上下文。

---

## 七、Human Gate

### 7.1 必须触发 Human Gate 的操作

| 操作 | 需要确认的内容 |
|---|---|
| `proposed → accepted` | 决策确认与影响范围认可 |
| `accepted → deprecated` | 废弃原因与后续处理 |
| `accepted → superseded` | 替代决策与新 ADR 关联 |
| ADR 升级为 specs 或 Rules | 升级内容与规则归属 |
| ADR 文件重命名 | 引用同步更新 |
| 修改已 accepted ADR 的 `decision` 字段 | 核心决策内容变更 |

### 7.2 应评估 Human Gate 的情况

1. 新增影响多个项目、规则、Skill、Agent、工具或生产对象边界的 ADR；
2. 将原本只是 Memo、Intent、Task 证据或临时判断的内容升级为 ADR；
3. 推翻或废弃已长期执行的 ADR；
4. 修改 ADR 的核心决策内容；
5. 改变 ADR 的事实源载体、状态机或升级路径语义。

### 7.3 推翻与废弃规则

1. ADR 不得删除。推翻旧决策时，不得删除旧 ADR 文件，应通过状态变更表达。
2. 推翻旧决策时，将旧 ADR 的 `status` 标记为 `superseded`，并在 `superseded_by` 字段引用新 ADR 的 ID。新 ADR 的 `context` 中应说明推翻旧决策的原因。
3. 废弃决策时，将 ADR 的 `status` 标记为 `deprecated`，表示不再建议遵守但保留历史。废弃应在 `consequences` 或 `context` 中补充废弃原因。
4. ADR 文件名可因标题修正而调整，但重命名时必须同步更新所有引用该 ADR 的 `related_objects`、`superseded_by` 和其他关联字段。
5. 终态 ADR 不得重开。如需对已终态的决策重新判断，必须新建 ADR，并在新 ADR 中引用原 ADR。
6. 推翻或废弃操作须经 Human Gate 确认。

---

## 八、字段契约

### 8.1 基础字段

ADR 基础字段遵循 06 §6.4 的字段契约原则。

| 字段名 | 必填 | 说明 |
|---|---|---|
| `id` | 是 | ADR 对象 ID |
| `type` | 是 | 固定为 `adr` |
| `title` | 是 | 决策标题 |
| `status` | 是 | ADR 状态 |
| `created` | 是 | 对象创建日期 |
| `updated` | 是 | 最近更新日期 |

### 8.2 ADR 扩展字段

| 字段名 | 必填 | 说明 |
|---|---|---|
| `date` | 是 | 决策日期 |
| `context` | 是 | 决策背景 |
| `decision` | 是 | 决策内容 |
| `consequences` | 是 | 决策后果 |
| `alternatives` | 否 | 考虑过但未采纳的替代方案 |
| `affects` | 否 | 影响范围列表 |
| `related_objects` | 否 | 关联生产对象 ID 列表 |
| `related_rules` | 否 | 关联的 specs 或 Rules 文件列表 |
| `superseded_by` | 条件必填 | 仅当 `status` 为 `superseded` 时必须填写，指向替代本决策的新 ADR ID |

### 8.3 字段约束

1. `status` 必须属于 ADR 标准状态；
2. `type` 必须固定为 `adr`；
3. `superseded_by` 仅在 `status: superseded` 时必填；
4. `related_objects` 应引用已存在的生产对象 ID；
5. `related_rules` 应引用已存在的 specs 或 Rules 文件路径；
6. 已 accepted ADR 的 `decision` 字段变更必须触发 Human Gate；
7. ADR 文件名变化必须同步检查所有引用。

---

## 九、AI 协作适配

1. AI 读取 ADR 时应优先读取 `accepted` 状态的 ADR，作为已确认决策的执行依据。
2. AI 不得将 `proposed` 状态的 ADR 作为执行依据。
3. AI 读取终态 ADR 时，应识别其历史语境，不作为当前执行依据。
4. AI 不得因为某个判断看起来重要就自动创建 ADR，必须先判断是否满足 ADR 准入条件。
5. AI 创建 ADR 时，初始状态应为 `proposed`，不得直接创建为 `accepted`。
6. AI 不得自行推翻、废弃或升级 `accepted` 状态的 ADR，必须经 Human Gate 确认。

---

## 十、程序辅助适配

1. 程序解析 ADR 时应依据本文定义的字段契约和文件命名规则。
2. 程序校验 ADR 时应覆盖字段完整性、状态合法性、条件必填、引用有效性、格式合规性和 Human Gate。
3. 程序可聚合 ADR 列表、状态分布、升级路径、影响范围和推翻历史。
4. 聚合输出属于派生视图数据，不替代 ADR 事实源。
5. 程序写入 ADR 时应校验字段完整性、状态合法性和引用有效性。
6. 程序不得自动执行 ADR 状态流转中需要 Human Gate 确认的操作。

---

## 十一、工具展示适配

1. 工具可以展示 ADR 列表、状态分布、影响范围、关联对象、升级路径和推翻历史。
2. 工具可以展示待确认 ADR、已终态 ADR，以及 ADR 与 specs、Rules、Task、Memo、Evidence 的关联。
3. 工具展示的 ADR 信息必须可追溯到 Git 文件事实源。
4. 工具不得维护与 ADR 事实源不一致的权威状态。
5. 工具展示 ADR 状态变更时，应提示 Human Gate 要求。
6. 工具不得绕过 ADR 字段契约直接维护派生状态。

---

## 十二、执行文件规划

执行文件含义和命名规则见 06 §4.5。ADR 执行文件规划如下：

| 文件 | 状态 |
|---|---|
| `11.01-规则.md` | planned |
| `11.02-技能.md` | planned |
| `11.03-Agent.md` | planned |
| `11.04-程序.md` | planned |
| `11.05-展示.md` | planned |
| `11.06-功能初始化.md` | planned |
| `11.07-功能审计.md` | planned |

---

## 十三、实例初始化检查

创建 ADR 实例时，应检查：

| # | 检查项 | 标准 |
|---|---|---|
| 1 | 文件命名 | 符合 `ldvh-base/adrs/adr-{NNNN}-short-title.yaml` |
| 2 | 必填字段 | 具备 id、type、title、status、created、updated、date、context、decision、consequences |
| 3 | 类型固定 | `type` 为 `adr` |
| 4 | 状态合法 | `status` 属于 ADR 标准状态 |
| 5 | 内容明确 | context、decision、consequences 可理解、可追溯 |
| 6 | 引用有效 | related_objects、related_rules、superseded_by 引用有效 |
| 7 | Human Gate | 直接创建或流转为 `accepted` 时已获确认 |

---

## 十四、实例审计检查

审计 ADR 实例时，应检查：

| # | 检查项 | 标准 |
|---|---|---|
| 1 | 准入判断 | 未把临时判断、一次性选择或局部方案过度 ADR 化 |
| 2 | 状态流转 | ADR 状态属于标准状态，流转属于合法流转 |
| 3 | 条件必填 | `superseded` 状态具备 `superseded_by` 字段 |
| 4 | 升级路径 | 满足升级条件的 ADR 已考虑升级为 specs 或 Rules |
| 5 | 转化记录 | Memo、Task 或 Evidence 转化为 ADR 时已记录来源对象 ID |
| 6 | 推翻证据 | 推翻旧 ADR 时已标记状态、引用新 ADR、补充原因 |
| 7 | 历史保留 | ADR 不得删除，终态 ADR 保留历史 |
| 8 | Human Gate | 需要人类确认的操作未被 AI、程序或工具绕过 |
| 9 | 事实源边界 | ADR 模型、实例、执行文件和工具展示未混淆事实源位置 |

---

## 十五、待补齐事项

1. ADR 与 Risk、Dependency 的转化关系待对应对象模型稳定后补充；
2. ADR 的自动过期或定期审查机制待实践验证；
3. ADR YAML schema 待 `11.04-程序.md` 创建时细化；
4. ADR 相关 Rules、Skill、Agent、展示、功能初始化和功能审计待对应执行文件创建时展开。
