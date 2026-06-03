# Evidence 验证证据

> 创建日期：2026-06-03
> 定位：定义 Evidence 验证证据事实模型（精简版），包括对象定位、准入条件、事实源边界、状态机、对象关系、Human Gate、字段契约和事实源回写要求
> 适用范围：所有接入 LDVH 且需要管理验证结果和验收记录的项目
> 上位依据：`specs/13-LDVH事实模型基础规范.md`
> 相关规范：`specs/00-LD-Vibe-Harness理念与纲要.md`、`specs/03-Specs文档规范.md`、`specs/04-LDVH模型子文档规范.md`、`specs/10-事实源边界与承载规范.md`、`specs/20-事实模型集合索引.md`

---

---

## 1. 本文解决的问题

本文定义 Evidence 验证证据事实模型。Evidence 是执行摘要、验证结果、关闭证据和验收记录，用于沉淀 Task 或 ADR 的验证结论，确保"做完了"不等于"做对了"。

本文只定义 Evidence 对象模型。Evidence 相关 Rules、Skill、Agent、Tools 契约式校验与执行和 Web 信息同步实践可按需由 §12 附件型实践子文档承接。

本文是精简版规范，只包含核心章节。13 §4.2 中未展开的章节标注于 §10 待补齐事项。

---

## 2. 与 13 的关系

`specs/13-LDVH事实模型基础规范.md` 定义事实模型通用规则、文件命名、附件型实践子文档命名和事实模型标准组成。本文依据 13 §4.2 定义 Evidence 对象模型。

本文不重新定义 13 中的通用规则。发生冲突时，以 13 及其上位基础规范为准，除非本文明确说明例外并经 Human Gate 确认。

---

## 3. 对象定位与准入条件

### 3.1 Evidence 定义

Evidence 是执行摘要、验证结果、关闭证据和验收记录。Evidence 应记录验证方法、验证结论、证据内容和来源对象。

Evidence 不是所有命令输出的默认归宿。AI 可以在当前任务中直接引用命令输出，但只有满足准入条件、需要作为 Task 关闭依据或 ADR 验证支撑的验证结果，才应进入 Evidence 事实源。

### 3.2 Evidence 与临时输出

临时输出是执行过程中的命令结果、日志片段或调试信息，不默认成为 Evidence。临时输出可以保留在当前执行上下文或 Task 描述中。

一个 Evidence 至少应具备：

1. 明确的验证方法；
2. 明确的验证结论（pass / fail / partial）；
3. 可追溯的验证来源（关联的 Task 或 ADR）；
4. 可追溯的状态。

### 3.3 Evidence 准入条件

当一个验证结果满足以下条件之一时，应考虑形成 Evidence：

1. 有关联的 Task 或 ADR；
2. 有可追溯的验证来源（命令输出、截图、测试报告等）；
3. 有明确的验证结论。

不满足 Evidence 准入条件的临时输出，可以保留在当前执行上下文或 Task 描述中。

以下内容通常不应单独形成 Evidence：

1. 当前执行过程中的调试输出；
2. 不影响 Task 关闭判断的中间结果；
3. 无明确验证结论的原始日志；
4. 已由其他 Evidence 完全覆盖的重复验证。

AI 不得因为执行了验证命令就自动创建 Evidence。只有满足准入条件的验证结果，才应写入 Evidence 事实源。

---

## 4. 事实源边界

本文是 Evidence 验证证据事实模型的权威事实源。本文定义 Evidence 的准入条件、状态机、对象关系、Human Gate 和字段契约。

Evidence 对象实例的权威事实源位置为：

```text
ldvh-base/evidence/ev-{NNNN}-short-title.yaml
```

编号从 `0001` 开始递增，固定 4 位；英文短标题使用小写短横线；每个项目独立编号，不使用跨项目全局编号。

| 内容 | 权威位置 |
|---|---|
| Evidence 对象模型 | `specs/29-Evidence-验证证据.md` |
| Evidence 对象实例 | `ldvh-base/evidence/` |
| Evidence 契约子文档 | `specs/29.06-Contract.md` |
| Evidence 展示或聚合视图 | `web/` 或 `tools/` 的派生输出，不作为最终事实源 |

---

## 5. 状态机

### 5.1 标准状态

Evidence 标准状态如下：

| 标准状态 | 含义 |
|---|---|
| `candidate` | 刚收集，尚未确认 |
| `verified` | 已确认有效 |
| `archived` | 已归档，不再活跃引用 |

### 5.2 合法状态流转

```text
candidate → verified
verified → archived
```

未在上述规则中列出的流转为非法流转，Tools 辅助和工具应拒绝执行。

`archived` 是稳定终态。终态 Evidence 不得重开；如需重新验证，必须新建 Evidence 承接，并在新 Evidence 中引用原 Evidence。

`candidate` 状态的 Evidence 不应作为 Task 关闭的依据。只有 `verified` 状态的 Evidence 才表示已确认有效的验证结果。

---

## 6. 与其他对象的关系

### 6.1 Evidence → Task

Evidence 通常关联一个 Task，作为该 Task 的验证结果或关闭证据。

创建 Evidence 后，关联 Task 的 `related_evidence` 字段应记录 Evidence ID。Task 的字段、状态和关闭规则由 Task 对象模型定义。

当 Evidence 的 `verification_result` 为 `fail` 时，关联 Task 不应关闭，需 Human Gate 确认处理方式。

### 6.2 Evidence → ADR

Evidence 可关联 ADR，作为该 ADR 决策的验证支撑。

创建 Evidence 后，关联 ADR 的 `related_objects` 字段应记录 Evidence ID。ADR 的字段、状态和关闭规则由 ADR 对象模型（`specs/21-ADR-决策记录.md`）定义。

---

## 7. Human Gate

以下场景必须触发 Human Gate：

1. Evidence 的 `verification_result` 为 `fail` 时，关联 Task 不应关闭，需 Human Gate 确认处理方式；
2. Evidence 状态从 `candidate` → `verified` 时，如验证结论为 `fail`，需确认后续处理。

Human Gate 在 Trae 中通过 AskUserQuestion 承载（依据 `specs/05-Trae-Solo AskUserQuestion使用规范.md`）。

---

## 8. 字段契约

### 8.1 基础字段

Evidence 基础字段遵循 `specs/13-LDVH事实模型基础规范.md` §7.3 的字段契约原则。

| 字段名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `id` | string | 是 | Evidence 对象 ID，格式为 `ev-{NNNN}` |
| `type` | string | 是 | 固定为 `evidence` |
| `title` | string | 是 | 证据标题 |
| `status` | string | 是 | Evidence 状态，必须属于标准状态枚举 |
| `created` | date | 是 | 对象创建日期 |
| `updated` | date | 是 | 最近更新日期 |

### 8.2 扩展字段

| 字段名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `evidence_type` | string | 是 | 证据类型：`verification`（验证）、`execution`（执行摘要）、`closure`（关闭证据）、`review`（审查记录） |
| `source_task` | string | 否 | 关联 Task ID |
| `source_adr` | string | 否 | 关联 ADR ID |
| `verification_method` | string | 是 | 验证方法 |
| `verification_result` | string | 是 | 验证结论：`pass`、`fail`、`partial` |
| `content` | string | 是 | 证据内容或摘要 |
| `artifact_path` | string | 否 | 附件路径（截图、日志文件等） |

字段约束和完整 YAML 示例详见 `specs/29.06-Contract.md`。

---

## 9. 事实源回写要求

1. 创建 Evidence 时应记录 Change（依据 `specs/22-Change-变更记录.md`）；
2. Evidence 状态变更时应记录 Change；
3. 创建 Evidence 后应关联到 Task 的 `related_evidence` 字段；
4. Evidence 的 `verification_result` 为 `fail` 时，应触发关联 Task 退回（从 `review_needed` → `executing`）；
5. Evidence 实例写入 `ldvh-base/evidence/` 目录后，应确保文件命名符合 `ev-{NNNN}-short-title.yaml` 格式。

---

## 10. 待补齐事项

以下章节依据 `specs/13-LDVH事实模型基础规范.md` §4.2 应定义但本文未展开，待后续阶段补齐：

| 13 §4.2 编号 | 章节名称 | 计划补齐阶段 |
|---|---|---|
| 8 | 证据留存要求 | Phase 3 |
| 9 | AI 协作适配 | Phase 4 |
| 10 | Tools 契约式校验与执行适配 | Phase 3（Contract 子文档先行） |
| 11 | Web 信息同步适配 | Phase 5 |
| 12 | 附件型实践子文档按需拆分规则 | Phase 4 |
| 13 | 落地前决策 | Phase 4 |
| 14 | 价值与要素审查 | Phase 4 |
| 15 | 落地初始化 | Phase 4 |
| 16 | 落地审计 | Phase 5 |
| 17 | 合规检查 | Phase 5 |
