# Change 变更

> 创建日期：2026-06-03
> 定位：定义 Change 变更记录工作模型，包括对象定位、准入条件、事实源边界、状态机、对象关系、Human Gate、字段契约（映射为 commit message 格式规范）、事实源回写与证据留存、适配规则
> 适用范围：所有接入 LDVH 且需要追踪事实源变更的项目
> 上位依据：`specs/07-工作模型基础规范.md`
> 相关规范：`specs/00-LD-Vibe-Harness理念与纲要.md`、`specs/03-文档规范.md`、`specs/01-目录说明.md`、`specs/04-事实源边界与承载规范.md`、`specs/05-Trae-Solo环境规范.md`、`specs/14-Code实现与工具规范.md`、`specs/15-Web信息同步规范.md`、`specs/20-工作模型集合索引.md`

---

## 1. 对象定位与准入条件

Change 是对事实源产生影响的实际修改记录，用于沉淀项目中每次对规范、Rules、事实实例、工具实现或其他 Git 文件事实源的变更。本文定义 Change 变更记录工作模型，包括对象定位、准入条件、事实源边界、状态机、对象关系、Human Gate、字段契约（映射为 commit message 格式规范）、事实源回写、证据留存和适配原则。

Change 与其他工作模型的核心区别在于承载方式：Change 不使用 `ldvh-base/` 下的 YAML 实例文件承载，而是直接以 Git commit 作为事实实例的权威事实源。本文定义 commit message 标准格式、关联规则、查询约定和工具解析要求。

本文只定义 Change 对象模型。Change 不需要固定拆分文件，各机制适配在主规范中直接说明。

### 1.1 Change 定义

Change 是对事实源产生影响的实际修改记录。Change 记录谁在什么时候修改了什么、为什么修改、修改影响了哪些对象。

Change 不是所有文件修改的默认归宿。AI 可以在当前任务中做局部调整、格式修正或临时实验，但只有满足准入条件的变更，才应通过标准 commit message 格式记录为 Change 事实。

### 1.2 Change 与 Git commit 的关系

Git commit 是 Change 事实实例的权威承载。每个符合本文 commit message 格式规范的 commit，即是一个 Change 事实实例。

Change 与 Git commit 的关系：

1. **承载关系**：Git commit 是 Change 的权威事实源，不是 Change 的替代品；
2. **格式约束**：并非所有 Git commit 都自动成为有效 Change 事实实例，只有符合本文 §6 定义格式的 commit 才是；
3. **查询约定**：Change 查询通过 `git log` 命令和格式化输出实现，不需要额外索引文件；
4. **不可变性**：Git commit 一旦创建即不可变，Change 实例同样不可变；
5. **跨仓库**：一次任务可能涉及工作区中多个 Git 仓库的文件修改。每个受影响的仓库应独立提交，各仓库的 commit message 均应符合本文 §6 格式，构成独立的 Change 事实实例。

### 1.3 Change 准入条件

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

### 1.4 Change 与 ADR / specs / Rules 的边界

Change 记录做了什么修改，ADR 记录为什么这样决定，specs 或 Rules 记录以后必须怎么做。三者不得互相替代。

当 Change 中的修改涉及需要长期追溯的判断时，应同时创建 ADR 记录决策背景，Change 的 commit message 通过 `Refs:` 关联该 ADR。

### 1.5 与 07 通用规则的适配差异

`specs/07-工作模型基础规范.md` 定义工作模型通用规则。本文依据 07 §4.2 定义 Change 对象模型，不重新定义 07 中的通用规则。发生冲突时，以 07 及其上位基础规范为准，除非本文明确说明例外并经 Human Gate 确认。

Change 因承载方式特殊（Git commit 而非 YAML 实例文件），以下方面与 07 通用规则存在适配差异：

1. **事实实例位置**：Change 实例不在 `ldvh-base/` 下，而是 Git commit 历史；
2. **字段契约**：Change 字段映射为 commit message 格式，而非 YAML 字段；
3. **状态机**：Change 实例不可变，无状态流转；
4. **机制适配边界**：Change 机制适配见 §8。

---

## 2. 事实源边界

本文是 Change 变更记录工作模型的权威事实源。本文定义 Change 的准入条件、commit message 格式、对象关系、Human Gate 和适配原则。

Change 事实实例的权威事实源位置为：

```text
Git commit 历史
```

| 内容 | 权威位置 |
|---|---|
| Change 对象模型 | `specs/22-Change-变更.md` |
| Change 事实实例 | Git commit 历史 |
| Change 展示或聚合视图 | `web/` 或 `tools/` 的派生输出，不作为最终事实源 |

Change 不使用 `ldvh-base/changes/` 目录。`ldvh-base/changes/` 不创建，不作为 Change 事实源。

---

## 3. 状态机

### 3.1 不可变性

Change 实例不可变。Git commit 一旦创建，其内容、作者、时间和关联信息不可修改。

### 3.2 无状态流转

Change 没有状态字段，没有状态流转。一个 Change 事实实例只有"存在"和"不存在"两种情况：

1. **存在**：commit 已创建且符合本文 §6 定义的格式规范；
2. **不存在**：commit 未创建，或 commit 不符合格式规范（不构成 Change 事实实例）。

### 3.3 修正与回退

当 Change 记录的修改需要回退时，应创建新的 revert commit，新 commit 同样应符合本文 §6 定义的格式规范，并通过 `Refs:` 关联被回退的 commit。

不得通过 `git rebase`、`git commit --amend` 或 `git push --force` 修改已推送的 Change 事实实例。

---

## 4. 与其他对象的关系

### 4.1 Change → ADR

当 Change 涉及需要长期追溯的决策时，应创建 ADR 记录决策背景，Change 的 commit message 通过 `Refs: ADR-{NNNN}` 关联该 ADR。

### 4.2 ADR / Task / Memo → Change

当 ADR 状态变更、Task 状态流转或 Memo 转化导致事实源文件修改时，对应的 commit 即为 Change 事实实例，commit message 通过 `Refs:` 关联源对象。

### 4.3 Change 与 specs / Rules

当 Change 修改 specs 或 Rules 文件时，commit message 的 `scope` 应标注影响范围（如 `specs`、`rules`），`Refs:` 可关联相关 ADR。

### 4.4 Record 阶段完成判断条件

Core Loop 的 Record 阶段完成判断需要 Task 和 Change 共同支撑。一个 Task 的 Record 阶段视为完成，当且仅当：

1. **Task 已关闭**：Task 状态为 `closed`，`closure_evidence` 已填写；
2. **对应 Change 已提交**：存在至少一个符合本文 §6 格式的 commit，其 `Refs:` 引用了该 Task ID。

两者缺一不可：
- Task 关闭但无 Change → 变更未沉淀到事实源；
- 有 Change 但 Task 未关闭 → 变更未经过关闭审查。

注：Evidence 独立工作模型已取消，验证和关闭证据由 Task 的 `closure_evidence` 字段和引用结果物承接。

`ldvh-close` Skill 在关闭 Task 时，必然修改事实源（status → closed、closed_at、closure_evidence），属于准入变更，因此必须内部调用 `ldvh-commit` Skill 编排提交，确保 Change 与 Task 关闭同步完成。

Task 的 `related_changes` 字段当前暂不回写，靠 commit message 中的 `Refs:` 实现反向追溯。后续如 Web Dogfood 暴露正向追溯需求，可通过 ADR 决策是否回写。

---

## 5. Human Gate

### 5.1 必须触发 Human Gate 的操作

| 操作 | 需要确认的内容 |
|---|---|
| 修改已 accepted ADR 的 `decision` 字段 | 核心决策内容变更（由 ADR 模型规范 §7 定义） |
| 修改 specs 核心规范 | 影响范围与兼容性 |
| 修改 Rules 文件 | 规则变更影响范围 |

### 5.2 Change 自身不触发额外 Human Gate

Change 记录本身是事实源修改的自然结果，不需要为"记录 Change"这一动作单独触发 Human Gate。Change 的 Human Gate 要求由被修改的源对象模型（如 ADR、Task）定义，Change 只承载修改记录。

### 5.3 commit 纪律

1. 每个 commit 应聚焦单一变更主题，避免在同一 commit 中混合不相关修改；
2. commit message 应符合本文 §6 定义的格式规范；
3. 涉及 Human Gate 的修改，应在 commit message body 中说明确认情况；
4. 任务完成后，应遍历工作区所有 Git 仓库，对每个有修改的仓库独立执行 commit，不可遗漏任何受影响的仓库；
5. commit 前必须调用 `tools/commit_validate.py --check-message` 预检拟提交的 message，预检不通过（exit code ≠ 0）时不得执行 commit。

---

## 6. 字段契约

Change 字段契约映射为 commit message 格式规范。

### 6.1 commit message 格式

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

### 6.2 type 枚举

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

### 6.3 scope 枚举

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

### 6.4 Refs 格式

`Refs` 用于关联其他工作模型对象，格式为 `{对象类型}-{编号}`，多个对象用逗号分隔：

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

### 6.5 格式约束

1. `subject` 不得超过 72 字符；
2. `body` 每行不得超过 72 字符；
3. `type` 必须属于 §6.2 定义的枚举值；
4. `Refs` 中的对象编号应引用已存在的工作模型对象；
5. `revert` 类型的 commit 必须在 `Refs` 中关联被回退的 commit hash。

### 6.6 示例

```text
spec(specs): 定义 Change 变更记录工作模型

创建 22-Change-变更.md，以 Git commit 作为 Change
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

## 7. 事实源回写与证据留存

通用规则引用 07 §7.4。以下仅保留 Change 对象特有差异。

### 7.1 回写特有

1. Change 事实实例通过 Git commit 自动回写，不需要额外回写操作；
2. commit message 中的 `Refs` 应在创建 commit 时填写，不得事后补充（除非通过 revert 或新 commit 修正）。

### 7.2 证据特有

1. Git commit 本身即为 Change 的完整证据，包含作者、时间、变更内容和关联信息；
2. Git commit hash 是 Change 事实实例的唯一标识；
3. 需要回退 Change 时，应创建 revert commit 保留回退证据，不得通过 force push 消除历史。

---

## 8. 适配规则

通用规则引用 07 §7.5/§7.6/§7.7。以下仅保留 Change 对象特有差异。

### 8.1 AI 协作

1. AI 读取 Change 时应通过 `git log` 命令获取 commit 历史，按本文 §6 定义的格式解析；
2. AI 应根据 commit message 的 `type` 和 `scope` 判断变更性质，根据 `Refs` 追踪关联对象；
3. AI 不得自行执行 `git rebase`、`git commit --amend` 或 `git push --force` 修改已推送的 Change 事实实例。

### 8.2 Tools 辅助

1. Tools 辅助程序读取 Change 时应通过 `git log --format` 命令生成结构化输出，支持按 type、scope、Refs 筛选和聚合；
2. Tools 辅助程序可校验 commit message 格式合规性，包括 type 枚举、subject 长度、Refs 格式和必填字段。

### 8.3 Web 信息同步

1. Web 可以同步 Change 列表、类型分布、影响范围、关联对象和变更频率；
2. Web 可以同步最近变更、待确认变更和与特定对象关联的变更历史。

---

## 9. 待补齐事项

1. Change 与 Task、Memo、Risk、Dependency 的关联规则待对应对象模型稳定后补充；
2. Change Web 信息同步能力待按需实现，未来如需变更看板再评估；
3. commit message `type` 枚举是否需要扩展待实践验证；
4. 项目中已有的暂缓标注（"暂缓：Change 记录机制待替换，见项目规则"）应替换为对本文的引用。
