# Pitfall-踩坑记录对象实践

> 创建日期：2026-05-28
> 对象名：Pitfall / 踩坑记录
> 适用范围：所有接入 PM Kit 且需要管理可复用踩坑经验的项目
> 上位依据：`specs-v2/00-PMKit理念与纲要.md`、`specs-v2/14-管理对象规范.md`、`specs-v2/10-事实源规范.md`、`specs-v2/11-AI协作规范.md`、`specs-v2/12-程序辅助规范.md`、`specs-v2/13-工具展示规范.md`

---

## 一、对象定位与准入

### 1.1 对象定义

Pitfall 是已解决且具有复用价值、可用于 AI 后续规避错误的踩坑经验（14 §八 管理对象总表）。

Pitfall 不是问题日志、错误记录或 AI 长期记忆。Pitfall 记录的是已确认的踩坑经验，目的是让 AI 在后续执行中识别和规避同类问题。

### 1.2 Pitfall 与临时问题

临时问题是 AI 或人在执行过程中遇到的错误或异常，不默认成为 Pitfall。临时问题可以记录在 Memo、Task evidence 或讨论材料中。

Pitfall 是满足准入条件、进入 PM Kit 管理系统的踩坑经验。所有 Pitfall 都是问题记录，但不是所有问题记录都是 Pitfall。

一个 Pitfall 至少应具备：

1. 明确的场景和触发条件；
2. 可复现的错误表现；
3. 已确认的根因；
4. 已验证的规避或修复方式。

### 1.3 准入条件

当一个问题满足以下全部条件时，应考虑形成 Pitfall：

1. 问题已解决或已有规避方式；
2. 具有复用价值，AI 在后续执行中可能再次遇到；
3. 规避方式不显而易见，需要显式记录。

不满足 Pitfall 准入条件的问题，可以先作为 Memo、Task evidence 或讨论材料保留。

以下内容通常不应单独形成 Pitfall：

1. 尚未解决的问题（应先作为 Task 或 Risk 处理）；
2. 一次性环境问题（如临时网络故障）；
3. 已由 specs 或 Rules 明确约束的重复错误；
4. 仅涉及当前会话的执行异常；
5. 显而易见的语法或格式错误。

AI 不得因为某个问题"出现过"就自动创建 Pitfall。只有满足准入条件的踩坑经验，才应写入 Pitfall 事实源。

### 1.4 Pitfall 与 specs / Rules 的边界

Pitfall 记录踩坑经验和规避方式，specs 或 Rules 记录以后必须怎么做。两者不得互相替代。

当 Pitfall 中的规避方式升级为长期基础规范时，应将规则正文写入 specs 或 Rules，Pitfall 保留经验记录。Pitfall 不替代 specs 规范正文，不替代 Rules 执行入口。

---

## 二、事实源边界

> 事实源边界声明：本文档是 Pitfall 对象实践的权威事实源。本文档定义 Pitfall 的准入条件、状态机、字段契约、对象关系和适配规则。本文档不重新定义管理对象语义（见 14）、事实源载体规则和格式契约（见 10）、AI 协作总原则（见 11）、程序辅助总原则（见 12）、工具展示总原则（见 13）。

Pitfall 的事实源载体为 Kit Base `pitfalls/` 子目录，格式契约对齐 10 §12.4。本文档只声明 Pitfall 如何使用这些载体和契约，不重新定义载体边界和格式契约。

---

## 三、状态机

### 3.1 标准状态

| 标准状态 | 含义 |
|---|---|
| open | 已记录，尚未确认规避方式有效 |
| resolved | 已确认规避方式有效，可用于后续规避 |
| deprecated | 已过时，不再适用，但保留历史 |

### 3.2 合法状态流转

```text
open → resolved, deprecated
resolved → deprecated
deprecated → 无
```

未在上述规则中列出的流转为非法流转，工具应拒绝执行。

### 3.3 终态规则

`deprecated` 是稳定终态。终态 Pitfall 不得重开；如需重新记录，必须新建 Pitfall，并在新 Pitfall 中引用原 Pitfall。

`open` 状态的 Pitfall 不应作为执行依据。只有 `resolved` 状态的 Pitfall 才表示已确认、可用于后续规避的踩坑经验。

### 3.4 废弃规则

1. Pitfall 不得删除。废弃时，不得删除 Pitfall 文件，应通过状态变更表达。
2. 废弃 Pitfall 时，将 Pitfall 的 `status` 标记为 `deprecated`，表示不再适用但保留历史。废弃应在 `workaround` 或 `root_cause` 中补充废弃原因。
3. 终态 Pitfall 不得重开。如需对已终态的踩坑经验重新记录，必须新建 Pitfall，并在新 Pitfall 中引用原 Pitfall。
4. 废弃操作须经 Human Gate 确认（见 §九）。

---

## 四、字段契约

### 4.1 基础字段

Pitfall 基础字段对齐 10 §12.2：`id`、`type`、`title`、`status`、`created`、`updated`。

### 4.2 Pitfall 扩展字段

Pitfall 扩展字段对齐 10 §12.4，字段名及简要说明如下：

| 字段 | 简要说明 |
|---|---|
| `date` | 记录日期，格式 YYYY-MM-DD |
| `scenario` | 触发场景 |
| `trigger` | 触发条件 |
| `symptom` | 错误表现 |
| `root_cause` | 根因 |
| `workaround` | 规避或修复方式 |
| `scope` | 适用范围列表（可选，用于 AI 快速筛选） |
| `tags` | 标签列表（可选） |
| `related_objects` | 关联的管理对象 ID 列表（可选） |

文件命名与格式契约对齐 10 §12.4：`pitfall-{NNNN}-short-title.yaml`，编号从 `0001` 开始递增，固定 4 位，每个项目独立编号。

---

## 五、与其他对象的关系

### 5.1 转化关系

#### 5.1.1 Memo → Pitfall

当 Memo 中的输入涉及已解决的踩坑经验，且满足 Pitfall 准入条件时，Memo 可转化为 Pitfall。

转化条件：

1. Memo 内容满足 Pitfall 准入条件（§1.3）；
2. 问题已解决，规避方式已验证；
3. 已获得人类确认。

转化后 Memo 状态应变为 `converted`，并记录 `linked_pitfall_id`。

#### 5.1.2 Task evidence → Pitfall

当 Task 执行过程中产生的踩坑经验满足 Pitfall 准入条件时，可将经验从 Task evidence 升级为 Pitfall。

转化条件：

1. 踩坑经验满足 Pitfall 准入条件（§1.3）；
2. 问题已解决，规避方式已验证；
3. 已获得人类确认。

转化后应在 Pitfall 的 `related_objects` 字段记录来源 Task ID，在 Task 的 evidence 中记录 Pitfall ID。

#### 5.1.3 不满足准入的问题

不满足 Pitfall 准入条件的问题，应按其性质分流：

1. 尚未解决的问题 → Task 或 Risk；
2. 有保留价值但暂不沉淀 → Memo；
3. 一次性环境问题 → 留在当前执行上下文。

### 5.2 依赖关系

Pitfall 不存在对其他对象的阻塞性依赖。Pitfall 的创建和状态变更不依赖其他对象的状态。

### 5.3 引用关系

Pitfall 可通过 `related_objects` 字段引用 Task、Memo、ADR、Risk 等对象。被引用对象的状态变更不影响 Pitfall 的状态。

---

## 六、初始化检查项

创建本文档时必须确认以下事项，对齐 14 §3.2 初始化维度：

1. Pitfall 是否满足 14 §9.2 的准入条件：Pitfall 已出现稳定的状态机和字段定义，需要独立追踪和校验，需要被 AI 高频读取，实践规则具有跨项目复用价值。
2. Pitfall 的状态机是否稳定：open / resolved / deprecated 三态及流转路径已稳定。
3. Pitfall 的字段契约是否可定义：基础字段对齐 10 §12.2，扩展字段对齐 10 §12.4。
4. Pitfall 的初始化检查项和审计检查项是否可声明：本文档 §六和 §七已声明。
5. Pitfall 与 10-13 的适配关系是否可表达：本文档 §八、§十、§十一已声明。

---

## 七、审计检查项

审查本文档时必须检查以下标准，对齐 14 §3.2 审计维度：

1. 文档是否遵守 14 §9.8 禁止扩张规范：本文档未新增基础规范层已有规则的变体或例外，未扩张基础规范层定义的概念边界，未重写基础规范层的规则正文，未替代基础规范层的权威地位。
2. 文档的适配声明是否与 10-13 一致：§八、§十、§十一的适配声明未重新定义各层规范已有规则。
3. 文档的状态机是否与 14 §六的状态变更原则一致：状态变更先于执行，终态不得重开，不得通过删除掩盖状态历史。
4. 文档的字段契约是否与 10 的格式契约对齐：基础字段对齐 10 §12.2，扩展字段对齐 10 §12.4，未自行扩张格式契约。
5. 文档的初始化检查项和审计检查项是否完整且可执行：§六和 §七覆盖 14 §3.2 两个维度。

---

## 八、AI 协作适配

本节声明 Pitfall 对象的 AI 协作适配规则，对齐 11，不重新定义 11 的规则。

1. AI 读取 Pitfall 时，应从 Kit Base `pitfalls/` 子目录读取结构化 YAML 文件，依据 10 §12.4 的格式契约解析。
2. AI 执行前应按场景匹配读取相关 Pitfall，优先读取 `resolved` 状态的 Pitfall 作为执行依据，`open` 状态的 Pitfall 不作为执行依据。
3. AI 创建 Pitfall 时，必须先判断是否满足 §1.3 的准入条件，不满足准入条件的问题不得写入 Pitfall 事实源。
4. AI 将 Memo 或 Task evidence 转化为 Pitfall 时，必须满足 §5.1 的转化条件，转化操作须经 Human Gate 确认。
5. AI 废弃 Pitfall 时，必须将 `status` 标记为 `deprecated` 并补充废弃原因，废弃操作须经 Human Gate 确认。
6. AI 编写代码前，应先查看当前项目的 `pm-kit-base/pitfalls/`，了解已记录的反直觉问题和规避策略（对齐 11 §五.5.7 第 8 条）。

---

## 九、Human Gate

以下 Pitfall 相关操作应触发或评估 Human Gate：

1. 新增影响后续执行方式的 Pitfall；
2. 将重要 Memo 或 Task evidence 转为 Pitfall；
3. 废弃已确认的 Pitfall。

检查至少包括：

| 检查项 | 标准 |
|---|---|
| 准入判断 | 未把临时错误、一次性问题或未解决问题过度 Pitfall 化 |
| 状态合法 | 状态属于标准状态，流转属于合法流转 |
| 必填字段 | Pitfall 具备 id、title、status、date、scenario、trigger、symptom、root_cause、workaround |
| 转化记录 | Memo → Pitfall、Task evidence → Pitfall 的转化已记录关联 ID |
| 历史保留 | Pitfall 不得删除，终态 Pitfall 保留历史 |
| Human Gate | 需要人类确认的操作未被 AI 或工具绕过 |

---

## 十、程序辅助适配

本节声明 Pitfall 对象的程序辅助适配规则，对齐 12，不重新定义 12 的规则。

1. 程序可解析 Kit Base `pitfalls/` 子目录下的结构化 YAML 文件，依据 10 §12.4 的格式契约校验字段完整性和状态合法性。
2. 程序可校验 Pitfall 状态流转是否属于 §3.2 定义的合法流转路径，非法流转应被拒绝。
3. 程序可聚合 Pitfall 列表，按 `scope`、`tags` 或 `status` 筛选，生成 AI 执行上下文包或工具派生视图数据。
4. 程序受控写入 Pitfall 事实源时，必须校验必填字段完整、状态流转合法，并评估 Human Gate。
5. 程序不得自动修改 Pitfall 状态、自动创建 Pitfall 或自动废弃 Pitfall。

---

## 十一、工具展示适配

本节声明 Pitfall 对象的工具展示适配规则，对齐 13，不重新定义 13 的规则。

1. 工具可展示 Pitfall 列表、状态和匹配视图，但不得维护第二套 Pitfall 事实源。
2. 工具展示的 Pitfall 数据必须可追溯到 Kit Base `pitfalls/` 子目录下的 Git 文件事实源。
3. 工具可按 `scope`、`tags`、`status` 筛选和聚合 Pitfall，作为派生视图数据供人审查。
4. 工具受控写入 Pitfall 事实源时，必须遵守 13 §七的受控写入原则，写入后触发 Change 记录。
5. 工具不得绕过 Human Gate 自动完成 Pitfall 创建、状态变更或废弃操作。

---

## 十二、待补齐事项

1. Pitfall 与 Risk、Dependency 的转化关系待后续对象实践稳定后补充；
2. PM Web Tools 如何展示 Pitfall 状态和匹配视图，需由后续工具展示实践展开；
3. Skill / Agent 如何围绕 Pitfall 创建、匹配和回写，需由后续 AI 协作实践展开；
4. Python 程序如何校验 Pitfall 格式和状态流转，需由后续程序辅助实践展开。
