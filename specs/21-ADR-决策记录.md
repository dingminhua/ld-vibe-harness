# ADR 决策记录

> 创建日期：2026-05-30
> 定位：定义 ADR 决策记录生产对象模型，包括对象定位、准入条件、事实源边界、状态机、对象关系、Human Gate、字段契约、事实源回写、证据留存、适配原则、附件型实践子文档、落地初始化、落地审计和合规检查
> 适用范围：所有接入 LDVH 且需要管理长期决策的项目
> 上位依据：`specs/13-LDVH生产对象基础规范.md`
> 相关规范：`specs/00-LD-Vibe-Harness理念与纲要.md`、`specs/03-Specs文档规范.md`、`specs/01-LDVH目录说明.md`、`specs/10-事实源边界与承载规范.md`、`specs/11-LDVH-AI协作规范.md`、`specs/12-LDVH工具基础规范.md`、`specs/20-生产对象集合索引.md`

---

## 一、本文解决的问题

本文定义 ADR 决策记录生产对象模型。ADR 是已确认、后续应遵守的决策记录，用于沉淀需要跨会话、跨任务或跨执行轮次追溯的长期决策。

本文只定义 ADR 对象模型。ADR 相关 Rules、Skill、Agent、Tools 辅助和 Web 展示实践可按需由 §十二附件型实践子文档承接。

---

## 二、与 13 的关系

`specs/13-LDVH生产对象基础规范.md` 定义生产对象通用规则、文件命名、附件型实践子文档命名和生产对象模型标准组成。本文依据 13 §4.2 定义 ADR 对象模型。

本文不重新定义 13 中的通用规则。发生冲突时，以 13 及其上位基础规范为准，除非本文明确说明例外并经 Human Gate 确认。

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
| ADR 对象模型 | `specs/21-ADR-决策记录.md` |
| ADR 对象实例 | `ldvh-base/adrs/` |
| ADR 模型实践子文档 | `specs/21.01-Rules.md` 至 `specs/21.05-Web.md` |
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

未在上述规则中列出的流转为非法流转，Tools 辅助和工具应拒绝执行。

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
6. 影响检查要求、工具写入或对象关闭方式。

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

ADR 基础字段遵循 13 §6.4 的字段契约原则。

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

## 九、事实源回写要求

1. ADR 状态变更时，必须先更新 ADR YAML 实例中的状态字段，再执行后续操作。
2. ADR 被 `accepted` 或 `superseded` 后，相关 specs 文档如需同步更新，应在 ADR 实例的 `affects` 字段中声明受影响文件，并按 10 事实源边界规范执行回写。
3. ADR 推翻或废弃时，应在 ADR 实例中记录推翻原因和替代 ADR 引用，不得直接删除 ADR 文件。
4. ADR 回写不得绕过 Human Gate，涉及正式规范变更的 ADR 必须经确认后才能回写。

---

## 十、证据留存要求

1. ADR 从 `proposed` 变更为 `accepted` 时，应留存决策依据和确认记录。
2. ADR 推翻或废弃时，应留存推翻原因、替代方案和确认记录。
3. ADR 升级时，应留存升级原因、新旧 ADR 关联和确认记录。
4. 证据留存位置为 ADR YAML 实例的 `context`、`decision`、`consequences` 字段和 `ldvh-base/changes/`中的 Change 记录。
5. ADR 证据应可追溯到 Git 文件事实源，不得仅存在于对话历史或工具缓存中。

---

## 十一、AI 协作适配

1. AI 读取 ADR 时应优先读取 `accepted` 状态的 ADR，作为已确认决策的执行依据。
2. AI 不得将 `proposed` 状态的 ADR 作为执行依据。
3. AI 读取终态 ADR 时，应识别其历史语境，不作为当前执行依据。
4. AI 不得因为某个判断看起来重要就自动创建 ADR，必须先判断是否满足 ADR 准入条件。
5. AI 创建 ADR 时，初始状态应为 `proposed`，不得直接创建为 `accepted`。
6. AI 不得自行推翻、废弃或升级 `accepted` 状态的 ADR，必须经 Human Gate 确认。

---

## 十二、Tools 辅助适配

1. Tools 辅助程序解析 ADR 时应依据本文定义的字段契约和文件命名规则。
2. Tools 辅助程序校验 ADR 时应覆盖字段完整性、状态合法性、条件必填、引用有效性、格式合规性和 Human Gate。
3. Tools 辅助程序可聚合 ADR 列表、状态分布、升级路径、影响范围和推翻历史。
4. 聚合输出属于派生视图数据，不替代 ADR 事实源。
5. Tools 辅助程序写入 ADR 时应校验字段完整性、状态合法性和引用有效性。
6. Tools 辅助程序不得自动执行 ADR 状态流转中需要 Human Gate 确认的操作。

---

## 十三、Web 展示适配

1. Web 可以展示 ADR 列表、状态分布、影响范围、关联对象、升级路径和推翻历史。
2. Web 可以展示待确认 ADR、已终态 ADR，以及 ADR 与 specs、Rules、Task、Memo、Evidence 的关联。
3. Web 展示的 ADR 信息必须可追溯到 Git 文件事实源。
4. Web 不得维护与 ADR 事实源不一致的权威状态。
5. Web 展示 ADR 状态变更时，应提示 Human Gate 要求。
6. Web 不得绕过 ADR 字段契约直接维护派生状态。

---

## 十四、附件型实践子文档

附件型实践子文档含义和命名规则见 13 §4.6。ADR 附件型实践子文档按需创建，不是 ADR 模型完整性的默认要求。当前规划如下：

| 文件 | 状态 |
|---|---|
| `21.01-Rules.md` | active |
| `21.02-Skill.md` | active |
| `21.03-Agent.md` | planned |
| `21.04-Tools.md` | planned |
| `21.05-Web.md` | planned |
| `21.06-Contract.md` | planned |

---

## 十五、落地前决策

ADR 对象模型进入项目实践前，应确认以下决策：

1. 是否需要在 L1 或 L2 Rules 中增加 ADR 准入条件入口摘要；
2. 是否需要为 ADR 创建 Rules、Skill、Agent、Tools 或 Web 附件型实践子文档；
3. 是否需要 Tools 辅助程序覆盖 ADR 字段完整性校验和状态合法性校验；
4. 哪些事项立即落地，哪些事项暂缓，暂缓原因和后续评估方式是什么；
5. 哪些事项触发 Human Gate，是否已获得确认。

落地前决策的输出是决策清单，不是初始化产物。未完成落地前决策前，不应声称已经完成落地初始化。

---

## 十六、价值与要素审查

落地前决策完成后、实际落地初始化开始前，必须基于 `specs/00-LD-Vibe-Harness理念与纲要.md` 执行价值与要素审查。

价值与要素审查至少应覆盖：

1. ADR 对象模型是否有助于 V1 稳定理解、V2 受控执行、V3 门禁识别、V4 证据沉淀、V5 事实回写、V6 人类确认质量或 V7 持续改进中的一项或多项；
2. ADR 对象模型是否明确归属于 LDVH 生产对象，且未混淆五类构成要素边界；
3. ADR 对象模型是否仍以 AI 执行者为第一服务对象，帮助 AI 读取事实源、创建和更新 ADR 实例、触发 Human Gate 和回写事实；
4. 是否避免把工具缓存、Web 状态、Agent 输出、Skill 输出或聊天过程当作 ADR 最终事实源；
5. 是否避免创建无必要的规则、Skill、Agent、工具或对象，导致体系膨胀但不提升可控性；
6. 是否明确需要 Human Gate 的事项，并在确认后再进入落地初始化。

审查不通过时，应回到落地前决策修正方案、标记暂缓或停止落地；不得直接进入初始化。

---

## 十七、落地初始化

ADR 对象模型进入项目实践时，需要完成以下初始化：

1. 创建 `ldvh-base/adrs/` 目录；
2. 确认 ADR 编号从 `0001` 起递增，固定 4 位；
3. 确认 ADR 实例文件命名规则为 `adr-{NNNN}-short-title.yaml`；
4. 确认 ADR 状态流转遵循本文 §五 定义的状态机；
5. 确认 ADR Human Gate 触发条件遵循本文 §七；
6. 在项目 Rules 摘要中引用 ADR 准入条件（本文 §3.3）；
7. 确认 Tools 辅助程序已覆盖 ADR 字段完整性校验和状态合法性校验；
8. 记录暂缓项和初始化产物。

---

## 十八、落地审计

ADR 对象模型落地审计应覆盖以下内容：

1. `ldvh-base/adrs/` 目录是否存在且与 Git 文件事实源一致；
2. ADR 实例文件命名是否符合 `adr-{NNNN}-short-title.yaml` 格式；
3. ADR 实例字段是否完整，必填字段是否齐全；
4. ADR 状态流转是否合法，是否存在非法流转；
5. `superseded` 状态的 ADR 是否已填写 `superseded_by` 字段；
6. Human Gate 触发操作是否有确认记录；
7. ADR 引用的 `related_objects` 和 `related_rules` 是否有效；
8. 是否存在 `proposed` 状态 ADR 被作为执行依据的情况；
9. 附件型实践子文档是否按需创建、非空、不替代主模型；
10. 识别初始化缺口、过期实践和需要整改的附件型实践子文档。

---

## 十九、合规检查

ADR 对象模型合规检查应覆盖以下内容：

1. ADR 对象模型规范写作是否符合 13 生产对象模型标准组成（13 §4.2），缺项是否已说明原因；
2. ADR 实例字段是否符合本文 §八 定义的字段契约；
3. ADR 状态流转是否符合本文 §五 定义的状态机；
4. ADR 对象关系引用是否符合本文 §六 定义的关系规则；
5. ADR 事实源边界是否符合本文 §四 和 10 事实源边界规范；
6. ADR Human Gate 是否符合本文 §七 定义的触发条件；
7. ADR 事实源回写是否符合本文 §九；
8. ADR 证据留存是否符合本文 §十；
9. ADR AI 协作适配是否符合本文 §十一；
10. ADR Tools 辅助适配是否符合本文 §十二；
11. ADR Web 展示适配是否符合本文 §十三；
12. ADR 附件型实践子文档命名是否符合 13 §4.6，是否按需创建且经 Human Gate 确认。

---

## 二十、待补齐事项

1. ADR 与 Risk、Dependency 的转化关系待对应对象模型稳定后补充；
2. ADR 的自动过期或定期审查机制待实践验证；
3. ADR YAML schema 待按需创建的 `21.04-Tools.md` 或 `21.06-Contract.md` 中细化；
4. ADR 相关 Rules、Skill、Agent、Tools 和 Web 实践待对应附件型实践子文档按需创建时展开。
