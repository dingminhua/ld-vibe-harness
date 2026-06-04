# Profile 项目画像

> 创建日期：2026-06-04
> 定位：定义 Profile 项目画像工作模型（精简版），包括对象定位、准入条件、事实源边界、状态机、对象关系、Human Gate、字段契约和事实源回写要求
> 适用范围：所有接入 LDVH 且需要管理项目身份、路径映射和接入配置的项目
> 上位依据：`specs/07-工作模型基础规范.md`
> 相关规范：`specs/00-LD-Vibe-Harness理念与纲要.md`、`specs/03-文档规范.md`、`specs/04-事实源边界与承载规范.md`、`specs/20-工作模型集合索引.md`

---

---

## 1. 本文解决的问题

本文定义 Profile 项目画像工作模型。Profile 承载项目身份、路径映射、项目名册和接入配置，是产品化、多项目治理和初始化体验的基础。

本文只定义 Profile 对象模型。Profile 相关 Rules、Skill、Agent、Tools 契约式校验与执行和 Web 信息同步实践应按 §12 机制适配边界和 07 §4.6 承接。

本文是精简版规范，只包含核心章节。07 §4.2 中未展开的章节标注于 §10 待补齐事项。

---

## 2. 与 07 的关系

`specs/07-工作模型基础规范.md` 定义工作模型通用规则、文件命名、主规范结构、机制适配边界和工作模型标准组成。本文依据 07 §4.2 定义 Profile 对象模型。

本文不重新定义 07 中的通用规则。发生冲突时，以 07 及其上位基础规范为准，除非本文明确说明例外并经 Human Gate 确认。

---

## 3. 对象定位与准入条件

### 3.1 Profile 定义

Profile 承载项目身份、路径映射、项目名册和接入配置，是产品化、多项目治理和初始化体验的基础。Profile 应记录项目名称、项目路径、ldvh-base 路径、语言框架和关联对象。

Profile 不是所有项目配置的默认归宿。AI 可以在当前上下文中直接处理一次性配置，但只有满足准入条件、需要跨会话识别或需要统一名册管理的项目，才应进入 Profile 事实源。

### 3.2 Profile 与临时配置

临时配置是执行过程中的一次性设置、局部调整或临时路径映射，不默认成为 Profile。临时配置可以保留在当前执行上下文中。

一个 Profile 至少应具备：

1. 明确的项目名称；
2. 可定位的项目根路径；
3. 可定位的 ldvh-base 目录路径；
4. 可追溯的状态。

### 3.3 Profile 准入条件

当一个项目满足以下条件之一时，应考虑形成 Profile：

1. 项目需要接入 LDVH 治理；
2. 项目需要被 AI 识别和自动配置；
3. 多项目需要统一名册和路径映射；
4. 项目初始化流程需要读取项目身份和配置。

不满足 Profile 准入条件的临时配置，可以直接在当前上下文中执行。

以下内容通常不应单独形成 Profile：

1. 一次性配置或临时设置；
2. 不需要 LDVH 治理的项目；
3. 已有 Profile 的重复项目。

AI 不得因为用户提出了任何请求就自动创建 Profile。只有满足准入条件的项目，才应写入 Profile 事实源。

---

## 4. 事实源边界

本文是 Profile 项目画像工作模型的权威事实源。本文定义 Profile 的准入条件、状态机、对象关系、Human Gate 和字段契约。

Profile 对象实例的权威事实源位置为：

```text
ldvh-base/profiles/profile-{NNNN}-project-name.yaml
```

编号从 `0001` 开始递增，固定 4 位；英文短标题使用小写短横线；每个项目独立编号，不使用跨项目全局编号。

| 内容 | 权威位置 |
|---|---|
| Profile 对象模型 | `specs/26-Profile-项目画像.md` |
| Profile 对象实例 | `ldvh-base/profiles/` |
| Profile 字段契约文件 | `specs/26.06-Contract.md` |
| Profile 展示或聚合视图 | `web/` 或 `tools/` 的派生输出，不作为最终事实源 |

---

## 5. 状态机

### 5.1 标准状态

Profile 标准状态如下：

| 标准状态 | 含义 |
|---|---|
| `draft` | 已创建，待确认 |
| `active` | 已确认，项目已接入 |
| `suspended` | 暂停接入 |
| `archived` | 项目已归档 |

### 5.2 合法状态流转

```text
draft → active
active → suspended
suspended → active
active → archived
suspended → archived
```

未在上述规则中列出的流转为非法流转，Tools 辅助和工具应拒绝执行。

`archived` 是稳定终态。终态 Profile 不得重开；如需重新接入，必须新建 Profile 承接，并在新 Profile 中引用原 Profile。

`active` → `suspended` 流转时，应记录暂停原因，并更新 `updated` 字段。

`suspended` → `active` 流转时，应记录恢复原因，并更新 `updated` 字段。

### 5.3 归档条件

Profile 从 `active` 或 `suspended` → `archived` 必须满足：

1. 项目已确认不再需要 LDVH 治理；
2. 关联 Task 已全部关闭或迁移；
3. 已获得 Human Gate 确认。

---

## 6. 与其他对象的关系

### 6.1 Profile → Task

Profile 可关联多个治理 Task，作为项目级工作单元。

创建 Profile 后，关联 Task 的 `related_profiles` 字段应记录 Profile ID（如 Task 模型支持）。Task 的字段和状态由 Task 对象模型（`specs/27-Task-任务.md`）定义。

### 6.2 Profile → ADR

Profile 可关联多个 ADR，作为项目级决策参考。

创建 Profile 后，关联 ADR 的 `related_objects` 字段应记录 Profile ID。ADR 的字段、状态和关闭规则由 ADR 对象模型（`specs/21-ADR-决策记录.md`）定义。

### 6.3 Profile → Memo

Profile 可关联多个 Memo，作为项目级备忘。

创建 Profile 后，关联 Memo 的 `related_profiles` 字段应记录 Profile ID（如 Memo 模型支持）。Memo 的字段和状态由 Memo 对象模型定义。

### 6.4 Profile → Change

Profile 的创建、状态变更和归档都应记录 Change。Change 以 Git commit 为权威事实源（依据 `specs/22-Change-变更记录.md`）。

---

## 7. Human Gate

以下场景必须触发 Human Gate：

1. 状态从 `draft` → `active` 时确认；
2. 状态从 `active` → `suspended` 时确认；
3. 状态从 `active` → `archived` 时确认。

Human Gate 在 Trae 中通过 AskUserQuestion 承载（依据 `specs/05-Trae-Solo环境规范.md` §9）。

---

## 8. 字段契约

### 8.1 基础字段

Profile 基础字段遵循 `specs/07-工作模型基础规范.md` §7.3 的字段契约原则。

| 字段名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `id` | string | 是 | Profile 对象 ID，格式为 `profile-{NNNN}` |
| `type` | string | 是 | 固定为 `profile` |
| `title` | string | 是 | 项目画像标题 |
| `status` | string | 是 | Profile 状态，必须属于标准状态枚举 |
| `created` | date | 是 | 对象创建日期 |
| `updated` | date | 是 | 最近更新日期 |

### 8.2 扩展字段

| 字段名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `description` | string | 是 | 项目画像详细描述 |
| `project_name` | string | 是 | 项目名称 |
| `project_path` | string | 是 | 项目根路径 |
| `ldvh_base_path` | string | 是 | ldvh-base 目录路径 |
| `language` | string | 否 | 主要编程语言 |
| `framework` | string | 否 | 主要框架 |
| `rules_path` | string | 否 | .trae/rules/ 路径 |
| `skills_path` | string | 否 | .trae/skills/ 路径 |
| `related_tasks` | list of string | 否 | 关联 Task ID 列表 |
| `related_adrs` | list of string | 否 | 关联 ADR ID 列表 |
| `notes` | string | 否 | 补充说明 |

字段约束和完整 YAML 示例详见 `specs/26.06-Contract.md`。

---

## 9. 事实源回写要求

1. 创建 Profile 时应记录 Change（依据 `specs/22-Change-变更记录.md`）；
2. Profile 状态变更时应记录 Change；
3. Profile 关联 Task、ADR、Memo 时应更新对应字段并记录 Change；
4. Profile 实例写入 `ldvh-base/profiles/` 目录后，应确保文件命名符合 `profile-{NNNN}-project-name.yaml` 格式。

---

## 10. 待补齐事项

以下章节依据 `specs/07-工作模型基础规范.md` §4.2 应定义但本文未展开，待后续阶段补齐：

| 07 §4.2 编号 | 章节名称 | 计划补齐阶段 |
|---|---|---|
| 8 | 证据留存要求 | Phase 3 |
| 9 | AI 协作适配 | Phase 4 |
| 10 | Tools 契约式校验与执行适配 | Phase 3（Contract 机制文件先行） |
| 11 | Web 信息同步适配 | Phase 5 |
| 12 | 机制适配边界 | Phase 4 |
