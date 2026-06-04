# Change 变更记录

> 创建日期：2026-06-03
> 定位：定义 Change 变更记录事实模型，包括对象定位、准入条件、事实源边界、状态机、对象关系、Human Gate、字段契约（映射为 commit message 格式规范）、事实源回写、证据留存、适配原则、落地初始化、落地审计和合规检查
> 适用范围：所有接入 LDVH 且需要追踪事实源变更的项目
> 上位依据：`specs/13-LDVH事实模型基础规范.md`
> 相关规范：`specs/00-LD-Vibe-Harness理念与纲要.md`、`specs/03-Specs文档规范.md`、`specs/01-LDVH目录说明.md`、`specs/10-事实源边界与承载规范.md`、`specs/11-LDVH-Trae-Solo-环境规范.md`、`specs/12-LDVH工具基础规范.md`、`specs/20-事实模型集合索引.md`

---

---
## 1. 本文解决的问题

本文定义 Change 变更记录事实模型。Change 是对事实源产生影响的实际修改记录，用于沉淀项目中每次对规范、Rules、事实实例、工具实现或其他 Git 文件事实源的变更。

Change 与其他事实模型的核心区别在于承载方式：Change 不使用 `ldvh-base/` 下的 YAML 实例文件承载，而是直接以 Git commit 作为事实实例的权威事实源。本文定义 commit message 标准格式、关联规则、查询约定和工具解析要求。

本文只定义 Change 对象模型。Change 不需要附件型实践子文档，各机制适配在主文档中直接说明。

---

## 2. 与 13 的关系

`specs/13-LDVH事实模型基础规范.md` 定义事实模型通用规则、文件命名、附件型实践子文档命名和事实模型标准组成。本文依据 13 §4.2 定义 Change 对象模型。

本文不重新定义 13 中的通用规则。发生冲突时，以 13 及其上位基础规范为准，除非本文明确说明例外并经 Human Gate 确认。

Change 因承载方式特殊（Git commit 而非 YAML 实例文件），以下方面与 13 通用规则存在适配差异：

1. **事实实例位置**：Change 实例不在 `ldvh-base/` 下，而是 Git commit 历史；
2. **字段契约**：Change 字段映射为 commit message 格式，而非 YAML 字段；
3. **状态机**：Change 实例不可变，无状态流转；
4. **附件型实践子文档**：Change 不需要 22.01-22.06 子文档，理由见 §14。

---

## 3. 对象定位与准入条件

### 3.1 Change 定义

Change 是对事实源产生影响的实际修改记录。Change 记录谁在什么时候修改了什么、为什么修改、修改影响了哪些对象。

Change 不是所有文件修改的默认归宿。AI 可以在当前任务中做局部调整、格式修正或临时实验，但只有满足准入条件的变更，才应通过标准 commit message 格式记录为 Change 事实。

### 3.2 Change 与 Git commit 的关系

Git commit 是 Change 事实实例的权威承载。每个符合本文 commit message 格式规范的 commit，即是一个 Change 事实实例。

Change 与 Git commit 的关系：

1. **承载关系**：Git commit 是 Change 的权威事实源，不是 Change 的替代品；
2. **格式约束**：并非所有 Git commit 都自动成为有效 Change 事实实例，只有符合本文 §8 定义格式的 commit 才是；
3. **查询约定**：Change 查询通过 `git log` 命令和格式化输出实现，不需要额外索引文件；
4. **不可变性**：Git commit 一旦创建即不可变，Change 实例同样不可变；
5. **跨仓库**：一次任务可能涉及工作区中多个 Git 仓库的文件修改。每个受影响的仓库应独立提交，各仓库的 commit message 均应符合本文 §8 格式，构成独立的 Change 事实实例。

### 3.3 Change 准入条件

当一个文件修改满足以下条件之一时，应通过标准 commit message 格式记录为 Change：

1. 修改 specs 规范文档；
2. 修改 Rules 文件；
3. 修改 `ldvh-base/` 下的事实实例；
4. 修改 Tools 辅助程序或 Web Tools 实现；
5. 修改项目配置文件（如 pyproject.toml、.gitignore）；
6. 影响其他对象或需要跨会话追溯的修改。

以下修改通常不需要标准 Change 格式：

1. 纯格式修正（如空格、换行）；
2. 临时实验性修改（未合入主分支）；
3. 自动生成的文件（如 lock 文件）。

### 3.4 Change 与 ADR / specs / Rules 的边界

Change 记录做了什么修改，ADR 记录为什么这样决定，specs 或 Rules 记录以后必须怎么做。三者不得互相替代。

当 Change 中的修改涉及需要长期追溯的判断时，应同时创建 ADR 记录决策背景，Change 的 commit message 通过 `Refs:` 关联该 ADR。

---

## 4. 事实源边界

本文是 Change 变更记录事实模型的权威事实源。本文定义 Change 的准入条件、commit message 格式、对象关系、Human Gate 和适配原则。

Change 事实实例的权威事实源位置为：

```text
Git commit 历史
```

| 内容 | 权威位置 |
|---|---|
| Change 对象模型 | `specs/22-Change-变更记录.md` |
| Change 事实实例 | Git commit 历史 |
| Change 展示或聚合视图 | `web/` 或 `tools/` 的派生输出，不作为最终事实源 |

Change 不使用 `ldvh-base/changes/` 目录。`ldvh-base/changes/` 不创建，不作为 Change 事实源。

---

## 5. 状态机

### 5.1 不可变性

Change 实例不可变。Git commit 一旦创建，其内容、作者、时间和关联信息不可修改。

### 5.2 无状态流转

Change 没有状态字段，没有状态流转。一个 Change 事实实例只有"存在"和"不存在"两种情况：

1. **存在**：commit 已创建且符合本文 §8 定义的格式规范；
2. **不存在**：commit 未创建，或 commit 不符合格式规范（不构成 Change 事实实例）。

### 5.3 修正与回退

当 Change 记录的修改需要回退时，应创建新的 revert commit，新 commit 同样应符合本文 §8 定义的格式规范，并通过 `Refs:` 关联被回退的 commit。

不得通过 `git rebase`、`git commit --amend` 或 `git push --force` 修改已推送的 Change 事实实例。

---

## 6. 与其他对象的关系

### 6.1 Change → ADR

当 Change 涉及需要长期追溯的决策时，应创建 ADR 记录决策背景，Change 的 commit message 通过 `Refs: ADR-{NNNN}` 关联该 ADR。

### 6.2 ADR / Task / Memo → Change

当 ADR 状态变更、Task 状态流转或 Memo 转化导致事实源文件修改时，对应的 commit 即为 Change 事实实例，commit message 通过 `Refs:` 关联源对象。

### 6.3 Change 与 specs / Rules

当 Change 修改 specs 或 Rules 文件时，commit message 的 `scope` 应标注影响范围（如 `specs`、`rules`），`Refs:` 可关联相关 ADR。

### 6.4 Record 阶段完成判断条件

Core Loop 的 Record 阶段完成判断需要 Task 和 Change 共同支撑。一个 Task 的 Record 阶段视为完成，当且仅当：

1. **Task 已关闭**：Task 状态为 `closed`，`closure_evidence` 已填写；
2. **对应 Change 已提交**：存在至少一个符合本文 §8 格式的 commit，其 `Refs:` 引用了该 Task ID。

两者缺一不可：
- Task 关闭但无 Change → 变更未沉淀到事实源；
- 有 Change 但 Task 未关闭 → 变更未经过关闭审查。

注：Evidence 独立事实模型已取消，验证和关闭证据由 Task 的 `closure_evidence` 字段和引用结果物承接。

`ldvh-close` Skill 在关闭 Task 时，必然修改事实源（status → closed、closed_at、closure_evidence），属于准入变更，因此必须内部调用 `ldvh-commit` Skill 编排提交，确保 Change 与 Task 关闭同步完成。

Task 的 `related_changes` 字段当前暂不回写，靠 commit message 中的 `Refs:` 实现反向追溯。后续如 Web Dogfood 暴露正向追溯需求，可通过 ADR 决策是否回写。

---

## 7. Human Gate

### 7.1 必须触发 Human Gate 的操作

| 操作 | 需要确认的内容 |
|---|---|
| 修改已 accepted ADR 的 `decision` 字段 | 核心决策内容变更（由 ADR 模型规范 §7 定义） |
| 修改 specs 核心规范 | 影响范围与兼容性 |
| 修改 Rules 文件 | 规则变更影响范围 |

### 7.2 Change 自身不触发额外 Human Gate

Change 记录本身是事实源修改的自然结果，不需要为"记录 Change"这一动作单独触发 Human Gate。Change 的 Human Gate 要求由被修改的源对象模型（如 ADR、Task）定义，Change 只承载修改记录。

### 7.3 commit 纪律

1. 每个 commit 应聚焦单一变更主题，避免在同一 commit 中混合不相关修改；
2. commit message 应符合本文 §8 定义的格式规范；
3. 涉及 Human Gate 的修改，应在 commit message body 中说明确认情况；
4. 任务完成后，应遍历工作区所有 Git 仓库，对每个有修改的仓库独立执行 commit，不可遗漏任何受影响的仓库；
5. commit 前必须调用 `tools/check_22_commit_format.py --check-message` 预检拟提交的 message，预检不通过（exit code ≠ 0）时不得执行 commit。

---

## 8. 字段契约

Change 字段契约映射为 commit message 格式规范。

### 8.1 commit message 格式

```text
<type>(<scope>): <subject>

<body>

Refs: <object-refs>
```

各部分说明：

| 部分 | 必填 | 说明 |
|---|---|---|
| `type` | 是 | 变更类型 |
| `scope` | 否 | 影响范围 |
| `subject` | 是 | 简短描述，不超过 72 字符 |
| `body` | 否 | 详细说明变更原因和内容 |
| `Refs` | 否 | 关联对象，多个对象用逗号分隔 |

### 8.2 type 枚举

| type | 含义 |
|---|---|
| `feat` | 新增功能或对象 |
| `fix` | 修复缺陷 |
| `docs` | 文档修改 |
| `refactor` | 重构，不改变外部行为 |
| `test` | 测试相关 |
| `chore` | 构建、配置或辅助工具修改 |
| `spec` | specs 规范文档修改 |
| `rule` | Rules 文件修改 |
| `adr` | ADR 实例创建或状态变更 |
| `revert` | 回退之前的变更 |

### 8.3 scope 枚举

scope 为可选字段，推荐值如下：

| scope | 含义 |
|---|---|
| `specs` | specs 规范文档 |
| `rules` | Rules 文件 |
| `adr` | ADR 实例 |
| `tools` | Tools 辅助程序 |
| `web` | Web Tools |
| `tests` | 测试代码 |
| `config` | 项目配置 |

scope 不限于上述枚举，可根据项目实际情况扩展。

### 8.4 Refs 格式

`Refs` 用于关联其他事实模型对象，格式为 `{对象类型}-{编号}`，多个对象用逗号分隔：

```text
Refs: ADR-0001, Task-0042
```

对象类型前缀：

| 前缀 | 对象类型 |
|---|---|
| `ADR` | ADR 决策记录 |
| `Task` | Task 任务 |
| `Memo` | Memo 备忘 |
| `Risk` | Risk 风险 |

### 8.5 格式约束

1. `subject` 不得超过 72 字符；
2. `body` 每行不得超过 72 字符；
3. `type` 必须属于 §8.2 定义的枚举值；
4. `Refs` 中的对象编号应引用已存在的事实模型对象；
5. `revert` 类型的 commit 必须在 `Refs` 中关联被回退的 commit hash。

### 8.6 示例

```text
spec(specs): 定义 Change 变更记录事实模型

创建 22-Change-变更记录.md，以 Git commit 作为 Change
事实实例的权威事实源，定义 commit message 标准格式、
关联规则和查询约定。

Refs: ADR-0001
```

```text
adr: 创建 ADR-0002 审计整改决策

Refs: ADR-0002
```

```text
fix(tools): 修复 ADR 索引排序错误

ADR 索引按创建日期降序排列，应改为按编号升序。
```

---

## 9. 事实源回写要求

1. Change 事实实例通过 Git commit 自动回写，不需要额外回写操作；
2. commit message 中的 `Refs` 应在创建 commit 时填写，不得事后补充（除非通过 revert 或新 commit 修正）；
3. Change 回写不绕过被修改对象的 Human Gate 要求；
4. 涉及 `ldvh-base/` 下事实实例修改的 commit，应在 commit message 中说明修改内容和原因。

---

## 10. 证据留存要求

1. Git commit 本身即为 Change 的完整证据，包含作者、时间、变更内容和关联信息；
2. Git commit hash 是 Change 事实实例的唯一标识；
3. Change 证据应存在于 Git 历史中，不得仅存在于对话历史或工具缓存中；
4. 需要回退 Change 时，应创建 revert commit 保留回退证据，不得通过 force push 消除历史。

---

## 11. AI 协作适配

1. AI 读取 Change 时应通过 `git log` 命令获取 commit 历史，按本文 §8 定义的格式解析；
2. AI 在修改 specs、Rules、`ldvh-base/` 事实实例或工具实现后，应按本文 §8 定义的格式编写 commit message；
3. AI 读取 Change 时应从 Git 文件事实源获取信息，不得依赖聊天记忆、工具缓存或 Web 派生状态作为最终依据；
4. AI 应根据 commit message 的 `type` 和 `scope` 判断变更性质，根据 `Refs` 追踪关联对象；
5. AI 读取 Change 后应输出与当前任务相关的变更摘要、影响范围和是否存在冲突；
6. AI 不得因 commit message 格式不规范而拒绝读取变更内容，但应标记为格式不合规；
7. AI 创建 commit 时应遵循本文 §8 定义的格式规范，不得使用无意义或过于简略的 commit message；
8. AI 不得自行执行 `git rebase`、`git commit --amend` 或 `git push --force` 修改已推送的 Change 事实实例。

---

## 12. Tools 辅助适配

1. Tools 辅助程序解析 Change 时应依据本文 §8 定义的 commit message 格式规范；
2. Tools 辅助程序读取 Change 时应通过 `git log --format` 命令生成结构化输出，支持按 type、scope、Refs 筛选和聚合；
3. Tools 只读查询结果不自动成为执行依据；AI 或 Skill 必须按本文格式规范判断读取结果适用性；
4. Tools 辅助程序可聚合 Change 列表、类型分布、影响范围、关联对象和变更频率；
5. 聚合输出属于派生视图数据，不替代 Git commit 事实源；
6. Tools 辅助程序可校验 commit message 格式合规性，包括 type 枚举、subject 长度、Refs 格式和必填字段；
7. Tools 辅助程序不得自行生成 commit、修改 commit message 或执行 force push；
8. Tools 辅助程序不得绕过被修改对象的 Human Gate 要求。

---

## 13. Web 信息同步适配

1. Web 可以同步 Change 列表、类型分布、影响范围、关联对象和变更频率；
2. Web 可以同步最近变更、待确认变更和与特定对象关联的变更历史；
3. Web 信息同步的 Change 信息必须可追溯到 Git commit 事实源；
4. Web 不得维护与 Git commit 事实源不一致的权威状态；
5. Web 不得绕过 Change 格式规范直接展示或编辑派生状态。

---

## 14. 附件型实践子文档

Change 22.01-22.06 六个子文档槽位状态如下：

| 编号 | 子文档 | 状态 | 说明 |
|---|---|---|---|
| 22.01 | Rules.md | active | Change 提交前提醒和提交纪律的权威位置，L0/L1 Rules 的提交纪律入口由此子文档定义 |
| 22.02 | Skill.md | active | ldvh-commit Skill 编排提交流程：diff 展示 → message 起草 → 格式预检 → 确认 → commit |
| 22.03 | Agent.md | not-created | Change 不需要 Agent 并行处理 |
| 22.04 | Tools.md | active | commit message 格式校验由 check_22_commit_format.py 执行，提供 --show-format、--check-message、git log 审计三种能力 |
| 22.05 | Web.md | not-created | Change 不需要独立 Web 编辑入口，读取和查询通过 git log 命令执行；未来如需 Web 变更看板再评估创建 |
| 22.06 | Contract.md | active | commit message 格式契约的权威位置，定义 type 枚举、scope 枚举、正则表达式和契约消费声明 |

22.02 从 not-created 升级为 active 的理由：

1. **提交流程需要多步骤编排**：diff 展示、message 起草、格式预检、用户确认、逐文件 add、commit 是多步骤流程，适合 Skill 编排；
2. **减少 Rules 冗余**：Skill 集中维护提交流程后，Rules 只需引用入口；
3. **确保执行一致性**：Skill 统一编排确保每次提交都经过完整检查链，不会因 AI 上下文差异遗漏步骤。

22.01 从 not-created 升级为 active 的理由：

1. **L0 Rules 的权威来源**：22.01 定义了 Change 提交纪律的完整规则，L0/L1 Rules 从中提取运行时入口摘要，符合 11 §6 Rules 机制规范的分层关系；
2. **提交纪律需要明确边界**：哪些场景必须调用 Skill、哪些不得跳过 Skill 直接 commit、Rules 层不得承载哪些内容，需要权威位置定义；
3. **Change 虽无 YAML 实例但提交纪律独立**：Change 的格式契约、提交流程、校验工具有明确的机制落地需求，不应省略。

22.04 从 not-created 升级为 active 的理由：

1. **Tools 校验已实现并在使用**：check_22_commit_format.py 已实现 --show-format、--check-message、git log 审计三种能力，并提供测试覆盖；
2. **预检是强制制度**：22 §7.3 要求 commit 前必须调用预检工具，需要 Tools 子文档定义命令参数、调用方式和测试要求；
3. **契约消费声明需要落地**：22.06 Contract 定义了格式契约，22.04 声明 Tools 如何消费该契约。

22.06 从 not-created 升级为 active 的理由：

1. **格式契约需要独立权威位置**：commit message 的 type 枚举、scope 枚举、正则表达式、中文字符检测规则需要结构化定义，供 Tools 校验和 AI 遵守消费；
2. **契约子文档是 Tools 和 Rules 的共同依据**：22.04 Tools 校验和 22.01 Rules 提醒都以 22.06 契约为准；
3. **Change 虽无 YAML 但契约格式独立**：commit message 格式契约是 Change 的核心结构化接口，需要独立子文档承载。

22.03、22.05 保持 not-created 状态，理由不变：Change 无独立 YAML 实例、无状态流转、Agent 并行处理和 Web 编辑入口当前不需要。

---

## 15. 落地前决策

Change 对象模型进入项目实践前，应确认以下决策：

1. Change 事实实例以 Git commit 承载，不创建 `ldvh-base/changes/` 目录；
2. Change 读取策略：通过 `git log --format` 命令按本文 §8 格式解析，支持按 type、scope、Refs 筛选；
3. Change 写入策略：通过标准 commit message 格式写入，通过 ldvh-commit Skill 编排提交流程，通过 check_22_commit_format.py 执行格式预检；
4. 已确认在 Rules 中增加提交纪律提醒（22.01）；
5. 已确认 Tools 辅助程序覆盖 commit message 格式校验能力（22.04）；
6. 已确认哪些事项立即落地，哪些事项暂缓。

落地前决策的输出是决策清单，不是初始化产物。未完成落地前决策前，不应声称已经完成落地初始化。

---

## 16. 价值与要素审查

落地前决策完成后、实际落地初始化开始前，必须基于 `specs/00-LD-Vibe-Harness理念与纲要.md` 执行价值与要素审查。

价值与要素审查至少应覆盖：

1. Change 对象模型是否有助于 V7 证据沉淀、V8 可靠回写或 V10 持续完善中的一项或多项；
2. Change 对象模型是否明确归属于 LDVH 事实模型，且未混淆五类构成要素边界；
3. Change 对象模型是否仍以 AI 执行者为第一服务对象，帮助 AI 追溯变更历史、理解变更原因和关联变更对象；
4. 是否避免把工具缓存、Web 状态、Agent 输出、Skill 输出或聊天过程当作 Change 最终事实源；
5. 是否避免创建无必要的规则、Skill、Agent、工具或对象，导致体系膨胀但不提升可控性；
6. 以 Git commit 承载 Change 是否符合 10 事实源边界规范中的最终事实源原则和单一事实源规则。

审查不通过时，应回到落地前决策修正方案、标记暂缓或停止落地；不得直接进入初始化。

---

## 17. 落地初始化

Change 对象模型进入项目实践时，需要完成以下初始化：

1. 确认 Change 事实实例以 Git commit 承载，不创建 `ldvh-base/changes/` 目录；
2. 确认 commit message 格式规范遵循本文 §8；
3. 确认 Change 读取入口为 `git log --format` 命令；
4. 确认 Change 的 22.02、22.01、22.04、22.06 子文档为 active 状态，22.03、22.05 为 not-created 状态，对应子文档文件已创建；
5. 确认项目 Rules 中是否需要增加 commit message 格式提醒；
6. 确认是否需要 Tools 辅助程序覆盖 commit message 格式校验能力；
7. 确认跨仓库 commit 机制：落地初始化涉及多个 Git 仓库时，每个仓库均需独立提交；
8. 记录暂缓项和初始化产物。

---

## 18. 落地审计

Change 对象模型落地审计应覆盖以下内容：

1. 项目 commit message 是否符合本文 §8 定义的格式规范；
2. 涉及 specs、Rules、`ldvh-base/` 事实实例修改的 commit 是否使用了标准格式；
3. commit message 中的 `Refs` 是否引用了有效的事实模型对象；
4. 是否存在 `git rebase`、`git commit --amend` 或 `git push --force` 修改已推送 Change 事实实例的情况；
5. 是否存在应使用标准格式但未使用的 commit；
6. Tools 辅助程序是否覆盖 commit message 格式校验能力；
7. 识别初始化缺口、过期实践和需要整改的事项。

---

## 19. 合规检查

Change 对象模型合规检查应覆盖以下内容：

1. Change 对象模型规范写作是否符合 13 事实模型标准组成（13 §4.2），缺项是否已说明原因；
2. commit message 格式是否符合本文 §8 定义的字段契约；
3. Change 事实源边界是否符合本文 §4 和 10 事实源边界规范；
4. Change 读取策略是否符合本文 §11 和 §12；
5. Change 写入策略是否符合本文 §7 和 §9；
6. Change 不使用 `ldvh-base/changes/` 目录是否符合本文 §4 的声明；
7. Change 附件型实践子文档状态是否符合本文 §14 的定义（22.01、22.02、22.04、22.06 active，22.03、22.05 not-created）。

---

## 20. 待补齐事项

1. Change 与 Task、Memo、Risk、Dependency 的关联规则待对应对象模型稳定后补充；
2. commit message 格式校验工具已实现，后续按需扩展多仓库批量校验能力；
3. Change Web 信息同步能力待按需实现（22.05 当前 not-created，未来如需变更看板再评估）；
4. commit message `type` 枚举是否需要扩展待实践验证；
5. 项目中已有的暂缓标注（"暂缓：Change 记录机制待替换，见 L1 规则"）应替换为对本文的引用。
