# Change-变更

> 创建日期：2026-06-09
> 定位：定义 Change / 变更工作模型，包括对象定位、准入条件、事实源边界、commit message 字段契约、对象关系、Human Gate、事实源回写、证据留存和适配规则
> 适用范围：所有接入 LDVH 且需要追踪 Git 文件事实源变更、提交纪律、变更证据和对象关联的项目
> 上位依据：`specs/05-工作模型基础规范.md`
> 相关规范：`specs/07-Code确定性执行实现规范.md`、`specs/20-WorkArea-工作域.md`、`specs/21-TaskPlan-任务计划.md`、`specs/22-Task-任务.md`

```yaml
ldvh_member:
  spec_id: "27"
  kind: work_model
  name_en: Change
  name_zh: 变更
  collection_status: active
  canonical_path: specs/27-Change-变更.md
  instance_root: Git commit records
  schema_anchor: "§6"
  state_machine_anchor: "§3"
  human_gate_anchor: "§5"
  code_consumption:
    - commit_message_contract
    - relationship_refs
    - instance_checks
```

---
## 1. 对象定位与准入条件

Change / 变更是对 Git 文件事实源产生影响的实际修改记录。Change 记录谁在什么时候修改了什么、为什么修改、影响哪些事实源，以及与哪些工作模型对象有关。

Change 是工作模型中的特殊对象：它不使用 `ldvh-base/changes/` 下的 YAML 实例承载，而是直接以 Git commit 作为事实实例的权威事实源。本文定义 commit message 格式、关联规则、查询约定、Human Gate 边界和 Code 校验要求。

### 1.1 Change 准入条件

以下修改应通过符合本文 §6 的 commit message 记录为 Change：

1. 修改 specs 正式规范、docs/studies 吸收结果、docs/sources 摘要或参考与研究材料吸收结论；
2. 修改 docs 正文、docs/studies 或 docs/sources 中的稳定项目事实；
3. 修改 `ldvh-base/` 下的事实实例；
4. 修改 Rules / Instructions、Skill、Agent、环境适配记录或适配措施；
5. 修改 Code、Web、测试、配置或会影响 LDVH 行为的实现文件；
6. 完成 WorkArea、TaskPlan、Task、SubTask、ADR、Memo、Pitfall 等对象的创建、状态变化、关闭或删除；
7. 影响其他对象、规范入口、事实源边界或需要跨会话追溯的修改。

以下修改通常不需要单独作为 Change 强制记录，但如果被提交，commit message 仍应符合本文格式：

1. 未保留的临时实验；
2. 本地缓存、构建产物或派生数据；
3. 未进入 Git 的草稿性输出。

### 1.2 Change 与 Git commit 的关系

Git commit 是 Change 事实实例的权威承载。每个符合本文 commit message 格式规范的 commit，即是一个 Change 事实实例。

规则如下：

1. Git commit 是 Change 的权威事实源，不是 Change 的替代品；
2. 并非所有既有 commit 都自动符合当前 Change 格式；
3. Change 查询通过 `git log`、Code 解析或 Web 派生视图实现，不创建额外索引文件；
4. commit 创建后即不可变；如需修正，应创建新的修正或 revert commit；
5. 一个工作可能涉及多个 Git 仓库时，每个受影响仓库应独立提交，分别形成 Change。

---
## 2. 事实源边界

本文是 Change 工作模型的权威规范，定义 Change 的准入条件、commit message 字段契约、对象关系、Human Gate、事实源回写和证据留存要求。

Change 实例的权威事实源位置为：

```text
Git commit 记录
```

| 内容 | 权威位置 |
|---|---|
| Change 工作模型规范 | `specs/27-Change-变更.md` |
| Change 事实实例 | Git commit 记录 |
| Change 字段契约 | commit message 格式 |
| Change 展示、聚合或查询结果 | `web/` 或 `code/` 的派生输出，不作为最终事实源 |

Change 不使用 `ldvh-base/changes/` 目录。`ldvh-base/changes/` 不创建，不作为 Change 事实源。

Change 的当前稳定规则以本文为准。

---
## 3. 状态机

### 3.1 不可变状态

Change 没有 YAML `status` 字段，也没有普通工作模型意义上的状态流转。Change 实例只有以下事实状态：

| 状态 | 含义 |
|---|---|
| exists | commit 已创建并存在于 Git 记录中 |
| invalid-format | commit 存在，但 message 不符合本文字段契约 |
| reverted | 后续存在 revert commit 或修正 commit 回退该变更 |

`invalid-format` 和 `reverted` 不是可写入字段，而是 Code 或 AI 根据 Git 记录派生出的判断。

### 3.2 修正与回退

Change 实例创建后不得通过 `git commit --amend`、`git rebase` 或 `git push --force` 修改已共享提交记录。需要修正时，应创建新的 commit：

1. 内容错误但仍需保留修改记录时，创建后续修正 commit；
2. 需要回退修改时，创建 `revert` 类型 commit；
3. 修正或回退 commit 应通过 `Refs:` 关联原 commit hash 或相关工作对象。

未推送、未共享且明确处于本地草稿阶段的提交记录整理，仍应遵守当前项目和 Human Gate 的授权边界。

---
## 4. 对象关系

### 4.1 Change 与 Task

Task 的创建、状态变化、关闭和关键事实源修改都应留下 Change。Task 关闭与 Record 阶段完成至少需要：

1. Task 状态为 `closed`；
2. `closure_evidence` 已填写；
3. 存在至少一个符合本文格式的 commit，其 `Refs:` 或 body 明确关联该 Task，或 Task 的 `related_changes` 记录该 commit。

Task 规范由 `specs/22-Task-任务.md` 定义。Change 不替代 Task 的验收标准、关闭证据或状态机。

### 4.2 Change 与 WorkArea 和 TaskPlan

WorkArea 的创建、归档、恢复和范围变更都应留下 Change。TaskPlan 的创建、状态变化、关闭审查、成功标准变更和任务列表调整都应留下 Change。工作域边界由 `specs/20-WorkArea-工作域.md` 定义；任务计划关闭判断由 `specs/21-TaskPlan-任务计划.md` 定义。

### 4.3 Change 与 ADR

当 Change 涉及长期决策、事实源边界、架构方向或高影响规则变化时，应创建或关联 ADR。ADR 的准入、状态和字段契约由 `specs/24-ADR-决策.md` 定义。

### 4.4 Change 与 Memo、Pitfall

Memo 的准入、状态和字段契约由 `specs/26-Memo-备忘.md` 定义。Pitfall 的准入、状态和字段契约由 `specs/25-Pitfall-踩坑.md` 定义。Change 可通过 `Refs:` 或 body 记录相关 Memo、Pitfall ID、路径或摘要。

### 4.5 Change 与规范、Code、Web

修改 specs、Code、Web、测试、环境适配记录或适配措施时，Change 应在 `type`、`scope`、subject 或 body 中说明影响范围。Change 只记录变更事实，不定义规范规则、Code 行为或 Web 状态。

---
## 5. Human Gate

Change 自身不为“记录变更”额外触发 Human Gate。Human Gate 由被修改的事实源、对象、规范、Code、Web 或工作流程定义。

以下情况应评估 Human Gate：

1. 修改 specs 正式规范、事实源边界、工作模型字段契约或状态机；
2. 修改 `ldvh-base/` 中高影响事实实例；
3. 修改 Rules / Instructions、Skill、Agent 或环境适配措施；
4. 修改 Code 受控写入、校验、Human Gate 或 Web 受控编辑能力；
5. 进行破坏性 Git 操作，例如改写已共享提交记录、强推或删除分支；
6. 试图把 Change 从 Git commit 记录改为 `ldvh-base/changes/` YAML 实例；
7. 删除或绕过 commit message 校验要求。

commit 前应检查当前工作区是否存在不属于本次变更的用户修改；不得把不相关修改混入同一个 commit。

---
## 6. 字段契约

Change 字段契约映射为 commit message 格式。

### 6.1 commit message 格式

```text
<type>(<scope>): <subject>

<body>

Refs: <object-refs>
```

| 字段 | 必填 | 说明 | 示例 |
|---|---|---|---|
| `type` | 是 | 变更类型 | `docs` |
| `scope` | 否 | 影响范围 | `specs` |
| `subject` | 是 | 简短说明，推荐不超过 72 字符 | `更新 Change 工作模型` |
| `body` | 否 | 说明变更原因、内容、风险和 Human Gate 结果 | `新增 specs/22...` |
| `Refs` | 建议 | 关联对象、规范编号、commit hash 或任务 ID | `Refs: task-0001, 27-Change-变更` |

`Refs` 暂为建议字段。没有明确对象可关联时，可以省略，但 Code 应给出 warning 而不是 error。

### 6.2 type 枚举

| type | 含义 |
|---|---|
| `feat` | 新增功能、能力或对象 |
| `fix` | 修复缺陷 |
| `docs` | 文档修改 |
| `refactor` | 重构，不改变外部行为 |
| `test` | 测试相关 |
| `chore` | 构建、配置或辅助维护 |
| `spec` | specs 规范文档修改 |
| `rule` | Rules / Instructions 修改 |
| `adr` | ADR 实例创建或状态变更 |
| `revert` | 回退之前的变更 |

### 6.3 scope 推荐值

| scope | 含义 |
|---|---|
| `specs` | specs 规范文档 |
| `docs` | 管辖项目文档或项目说明 |
| `rules` | Rules / Instructions |
| `adr` | ADR 实例 |
| `code` | Code / 工具实现 |
| `web` | Web 实现 |
| `tests` | 测试代码 |
| `config` | 项目配置 |
| `studies` | 内部评估或 docs/studies 相关修改 |
| `sources` | 外部引用资料或 docs/sources 相关修改 |

scope 为推荐值，项目可以在不破坏解析的前提下扩展。若历史 commit 使用旧研究或旧引用分类，仅视为提交分类别名，不改变 docs/studies 与 docs/sources 的事实源归属。

### 6.4 Refs 格式

`Refs` 用于关联其他工作模型对象、规范编号或 commit hash。推荐格式如下：

| 引用类型 | 格式示例 |
|---|---|
| WorkArea | `workarea-0001` |
| TaskPlan | `taskplan-0001` |
| Task | `task-0001` |
| SubTask | `subtask-0001` |
| ADR | `adr-0001` |
| Memo | `memo-0001` |
| Pitfall | `pitfall-0001` |
| 规范文档 | `27-Change-变更` |
| commit hash | `abc1234` |

Risk、Dependency、Artifact、Checklist 当前不是独立工作模型，不应作为默认 Refs 对象前缀。需要表达这些信息时，应通过 Task 字段、正文说明或对应产物路径承接。

### 6.5 格式约束

1. 第一行必须符合 `<type>(<scope>): <subject>` 或 `<type>: <subject>`；
2. `type` 必须属于 §6.2 枚举；
3. `subject` 必须非空，推荐不超过 72 字符；
4. body 应说明关键变更原因、影响范围或 Human Gate 结果；
5. `Refs` 中的工作对象应引用已存在对象；对象尚未创建或尚未生效时，可先保留规范编号、路径或说明；
6. `revert` 类型 commit 应在 `Refs` 或 body 中关联被回退的 commit hash；
7. 当前 LDVH 自身项目的 `code/commit_validate.py` 要求 commit message 的 subject 或 body 包含中文字符；这是当前 Code 实现纪律，后续是否泛化为所有管辖项目规则需单独评估。

### 6.6 示例

```text
docs(specs): 更新 Change 工作模型

新增 specs/27-Change-变更.md，明确 Change 以 Git
commit 记录作为事实实例，不创建 ldvh-base/changes/。

Refs: 27-Change-变更
```

```text
fix(tools): 修正 commit message 校验引用

将 commit_validate.py 中的 Change 规范引用更新到
specs/27-Change-变更.md。

Refs: 27-Change-变更
```

```text
revert(specs): 回退错误的 Task 字段契约修改

回退 abc1234 中对 Task 状态机的错误调整。

Refs: abc1234, task-0001
```

---
## 7. 事实源回写与证据留存

### 7.1 回写规则

Change 回写遵循以下规则：

1. Change 事实实例通过 Git commit 产生，不需要额外 YAML 写入；
2. commit message 应在 commit 创建时写完整，不依赖事后补充；
3. commit 前应运行或评估 commit message 校验；
4. commit 后应通过 `git status --short` 确认目标工作区状态；
5. 多仓库变更应分别提交，不得只提交当前仓库而遗漏其他受影响仓库；
6. 如果 commit message、关联对象或变更内容出错，应通过新的修正或 revert commit 留痕。

### 7.2 证据留存

Git commit 本身是 Change 的完整证据，至少包含：

1. commit hash；
2. 作者和时间；
3. 修改文件和 diff；
4. commit message；
5. 关联对象或说明；
6. revert 或修正记录。

Change 的派生列表、Web 看板、工具输出和统计结果不得替代 Git commit 记录。

---
## 8. 适配边界

### 8.1 AI 协作

AI 处理 Change 时应遵守：

1. 修改事实源后，应判断是否需要形成 commit；
2. commit 前检查工作区，避免混入不相关修改；
3. commit message 应按本文 §6 编写；
4. 涉及 Human Gate 的修改，应在 body 或相关对象中记录确认情况；
5. 不得通过 amend、rebase 或 force push 改写已共享 Change 记录；
6. 不得因为 Change 不使用 YAML 实例，就跳过变更追溯。

### 8.2 Code 辅助

Code 可依据本文实现以下能力：

1. 校验拟提交的 commit message；
2. 扫描 Git 记录并报告格式不合规 commit；
3. 按 type、scope、Refs、时间、文件路径聚合 Change；
4. 生成对象关联的 Change 列表；
5. 检查 WorkArea、TaskPlan、Task、SubTask 等对象是否缺少关联 Change；
6. 诊断 Code 实现自身与本文格式约束之间的漂移。

当前 `code/commit_validate.py` 是既有 Code 消费方，已同步到 `specs/27-Change-变更.md` 规范路径。后续 commit message 契约变化时，应同步更新该实现和对应测试。

### 8.3 Web 信息同步

Web 可展示 Change 列表、类型分布、影响范围、关联对象、最近变更、待确认变更和与特定对象关联的变更记录。

Web 不得把数据库缓存、页面状态或派生索引替代 Git commit 记录。涉及受控提交或确认时，应遵守 Human Gate 和 Code 校验要求。

### 8.4 工作流程与环境适配

提交、关闭任务、记录变更和审计变更的具体行动流程由后续 40-59 工作流程规范承接。本文只定义 Change 实例的事实规则和 commit message 契约。

环境不支持自动 commit 校验或 Git 记录解析时，应记录降级方式，例如人工检查 commit message、直接使用 Git 命令查询或暂停提交；不得把未校验 commit 表述为完整通过。

---
## 9. 规范落地要求

本文通过以下规范落地要求说明相关要求的同步、检查或审计触发条件。

| 落地要求 | 要求内容 | 保障机制 | 同步类型 | 触发条件 |
|---|---|---|---|---|
| 上位约束承接要求 | 后续工作模型、工作流程和提交实践应遵守本文定义的 Change 事实源边界、commit message 契约和 Git 记录不可变原则 | 05、03.03、本文、Human Gate | 工作模型治理 | 创建、提交、回退、审计或查询 Change 时 |
| 入口可见要求 | AI 执行事实源修改、关闭 Task、关闭任务计划或准备提交时，应能定位本文 | 成员自描述、commit 流程入口、运行入口摘要 | AI 执行入口提示 | Git 提交、任务关闭、任务计划关闭、规范吸收、Code/Web 修改或多仓库变更时 |
| 确定性执行要求 | commit message 格式、type、scope、Refs、subject 长度和中文约束应由 Code 校验或记录缺口 | `code/commit_validate.py`、`specs/07-Code确定性执行实现规范.md`、正反样例 | 校验实现 | commit 格式、枚举、Refs 规则或校验实现变化时 |
| Human 交互要求 | 高影响事实源修改、提交记录改写、强推、删除校验或改变 Change 承载方式应触发 Human Gate | Human Gate、影响范围说明、确认记录 | 工作模型治理 | §5 中任一场景发生时 |
| 生命周期触发要求 | Change 规范变化后，应检查 commit_validate、测试、WorkArea、TaskPlan、Task、SubTask、Web、适配措施和相关工作流程是否需要同步 | Code 测试、对象关系检查、Web 联动检查、人工降级检查 | 触发保障 | Change 字段契约、事实源边界、提交纪律或适配规则变化时 |

---
## 10. 检查要求

Change 规范检查至少包括：

| 检查项 | 标准 |
|---|---|
| 准入判断 | 已说明哪些修改需要 commit 追溯 |
| 事实源位置 | Change 实例由 Git commit 记录承载，不创建 `ldvh-base/changes/` |
| 字段契约 | commit message 符合 §6 |
| 状态例外 | 已说明 Change 无 YAML 状态流转，派生状态不写入事实源 |
| 对象关系 | WorkArea、TaskPlan、Task、SubTask、ADR、Memo、Pitfall 引用边界清晰 |
| 暂缓对象化 | Risk、Dependency、Artifact、Checklist 未作为默认 Refs 对象前缀 |
| Human Gate | 高影响修改和破坏性 Git 操作已评估 Human Gate |
| Code 边界 | commit_validate 等 Code 只校验和诊断，不替代 Git commit 记录 |
| Web 边界 | Web 派生视图未替代 Git commit 记录 |

---
## 11. 待补齐事项

1. Change Web 信息同步能力待 Web 实现规划时补齐；
2. commit message 是否继续强制包含中文，需在更通用的管辖项目场景中评估；
3. 任务关闭、任务计划关闭和提交之间的工作流程待 40-59 承接；
4. `code/commit_validate.py` 的正反样例应随本文 commit message 契约变化持续维护。
