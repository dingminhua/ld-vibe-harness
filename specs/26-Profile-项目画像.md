# Profile 项目画像

> 创建日期：2026-06-04
> 定位：定义 Profile 项目画像工作模型（精简版），包括对象定位、准入条件、事实源边界、状态机、对象关系、Human Gate、字段契约和事实源回写要求
> 适用范围：所有接入 LDVH 且需要管理项目身份、路径映射和接入配置的项目
> 上位依据：`specs/07-工作模型基础规范.md`
> 相关规范：`specs/00-LD-Vibe-Harness理念与纲要.md`、`specs/03-文档规范.md`、`specs/04-事实源边界与承载规范.md`、`specs/20-工作模型集合索引.md`

---

## 1. 对象定位与准入条件

本文定义 Profile 项目画像工作模型。Profile 承载项目身份、路径映射、项目名册和接入配置，是产品化、多项目治理和初始化体验的基础。

### 1.1 Profile 定义

Profile 承载项目身份、路径映射、项目名册和接入配置，是产品化、多项目治理和初始化体验的基础。Profile 应记录项目名称、项目路径、ldvh-base 路径、语言框架和关联对象。

Profile 不是所有项目配置的默认归宿。AI 可以在当前上下文中直接处理一次性配置，但只有满足准入条件、需要跨会话识别或需要统一名册管理的项目，才应进入 Profile 事实源。

### 1.2 Profile 与临时配置

临时配置是执行过程中的一次性设置、局部调整或临时路径映射，不默认成为 Profile。临时配置可以保留在当前执行上下文中。

一个 Profile 至少应具备：

1. 明确的项目名称；
2. 可定位的项目根路径；
3. 可定位的 ldvh-base 目录路径；
4. 可追溯的状态。

### 1.3 Profile 准入条件

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

## 2. 事实源边界

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
| Profile 展示或聚合视图 | `web/` 或 `tools/` 的派生输出，不作为最终事实源 |

---

## 3. 状态机

### 3.1 标准状态

Profile 标准状态如下：

| 标准状态 | 含义 |
|---|---|
| `draft` | 已创建，待确认 |
| `active` | 已确认，项目已接入 |
| `suspended` | 暂停接入 |
| `archived` | 项目已归档 |

### 3.2 合法状态流转

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

### 3.3 归档条件

Profile 从 `active` 或 `suspended` → `archived` 必须满足：

1. 项目已确认不再需要 LDVH 治理；
2. 关联 Task 已全部关闭或迁移；
3. 已获得 Human Gate 确认。

---

## 4. 与其他对象的关系

### 4.1 Profile → Task

Profile 可关联多个治理 Task，作为项目级工作单元。

创建 Profile 后，关联 Task 的 `related_profiles` 字段应记录 Profile ID（如 Task 模型支持）。Task 的字段和状态由 Task 对象模型（`specs/27-Task-任务.md`）定义。

### 4.2 Profile → ADR

Profile 可关联多个 ADR，作为项目级决策参考。

创建 Profile 后，关联 ADR 的 `related_objects` 字段应记录 Profile ID。ADR 的字段、状态和关闭规则由 ADR 对象模型（`specs/21-ADR-决策.md`）定义。

### 4.3 Profile → Memo

Profile 可关联多个 Memo，作为项目级备忘。

创建 Profile 后，关联 Memo 的 `related_profiles` 字段应记录 Profile ID（如 Memo 模型支持）。Memo 的字段和状态由 Memo 对象模型定义。

### 4.4 Profile → Change

Profile 的创建、状态变更和归档都应记录 Change。Change 以 Git commit 为权威事实源（依据 `specs/22-Change-变更.md`）。

---

## 5. Human Gate

以下场景必须触发 Human Gate：

1. 状态从 `draft` → `active` 时确认；
2. 状态从 `active` → `suspended` 时确认；
3. 状态从 `active` → `archived` 时确认。

Human Gate 在 Trae 中通过 AskUserQuestion 承载（依据 `specs/05-Trae-Solo环境规范.md` §9）。

---

## 6. 字段契约

### 6.1 基础字段

Profile 基础字段遵循 `specs/07-工作模型基础规范.md` §7.3 的字段契约原则。

| 字段名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `id` | string | 是 | Profile 对象 ID，格式为 `profile-{NNNN}` |
| `type` | string | 是 | 固定为 `profile` |
| `title` | string | 是 | 项目画像标题 |
| `status` | string | 是 | Profile 状态，必须属于标准状态枚举 |
| `created` | date | 是 | 对象创建日期 |
| `updated` | date | 是 | 最近更新日期 |

### 6.2 扩展字段

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

字段约束和完整 YAML 示例已回并到本文。

### 6.3 完整 YAML 示例

```yaml
id: profile-0001
type: profile
title: ld-vibe-harness 项目画像
status: active
created: 2026-06-04
updated: 2026-06-04
description: LDVH 核心框架项目，承载规范体系、工作模型和工具链
project_name: ld-vibe-harness
project_path: /Users/dmh2002/trae_projects/ld-vibe-harness
ldvh_base_path: /Users/dmh2002/trae_projects/ld-vibe-harness/ldvh-base
language: Python
framework: ""
rules_path: /Users/dmh2002/trae_projects/ld-vibe-harness/.trae/rules
skills_path: /Users/dmh2002/trae_projects/ld-vibe-harness/.trae/skills
related_tasks:
  - task-0001
related_adrs:
  - adr-0001
notes: LDVH 核心项目，所有规范和工作模型的管辖项目
```

### 6.4 字段约束

1. `status` 必须属于 Profile 标准状态枚举：`draft`、`active`、`suspended`、`archived`；
2. `type` 必须固定为 `profile`；
3. `project_name` 不得为空字符串，应使用项目唯一标识名称；
4. `project_path` 必须为有效绝对路径；
5. `ldvh_base_path` 必须为有效绝对路径，且应为 `project_path` 的子路径；
6. `rules_path` 如填写，必须为有效绝对路径；
7. `skills_path` 如填写，必须为有效绝对路径；
8. `related_tasks` 和 `related_adrs` 应引用已存在的工作模型 ID，引用无效时应标记为校验警告；
9. `id` 格式必须为 `profile-{NNNN}`，编号固定 4 位，从 `0001` 起递增；
10. `created` 和 `updated` 使用 ISO 8601 日期格式（`YYYY-MM-DD`）；
11. `related_tasks`、`related_adrs` 为列表类型，可为空列表，不得省略字段后以 null 替代空列表。

### 6.5 文件命名契约

Profile 实例文件命名规则为 `profile-{NNNN}-project-name.yaml`。编号从 `0001` 起递增，固定 4 位；英文短标题使用小写短横线命名；每个项目独立编号，不使用跨项目全局编号；文件存放位置为 `ldvh-base/profiles/`；文件名变化必须同步检查所有引用该 Profile 的 `related_profiles` 和其他关联字段。

### 6.6 状态流转契约

| 当前状态 | 可流转至 |
|---|---|
| `draft` | `active` |
| `active` | `suspended`, `archived` |
| `suspended` | `active`, `archived` |
| `archived` | 无 |

`active` → `suspended` 为暂停流转，应记录暂停原因。`suspended` → `active` 为恢复流转，应记录恢复原因。

### 6.7 契约消费与检查项

1. Tools 辅助程序解析 Profile 时应依据本文定义的 YAML schema 和字段约束，不得自行扩张格式契约；
2. Tools 辅助程序校验 Profile 时应覆盖字段完整性、状态合法性、条件必填和引用有效性；
3. Tools 辅助程序读取 Profile 时可依据本文状态枚举和字段契约执行状态筛选、详情解析和关联字段解析，但 Profile 读取结果是否可作为当前执行依据由本文和 Skill 流程判断；
4. 实践子文档和工具可以消费本文契约，但不得复制维护契约字段第二事实源；
5. 修改本文契约属于规范变更，应评估 Human Gate 并记录 Change（依据 `specs/22-Change-变更.md`）；
6. Profile YAML 实例字段完整性、`status`、`type`、路径字段、关联引用、文件命名、状态流转、终态重开、暂停原因和恢复原因均属于契约检查项。

---

## 7. 事实源回写与证据留存

### 7.1 事实源回写

1. 创建 Profile 时应记录 Change（依据 `specs/22-Change-变更.md`）；
2. Profile 状态变更时应记录 Change；
3. Profile 关联 Task、ADR、Memo 时应更新对应字段并记录 Change；
4. Profile 实例写入 `ldvh-base/profiles/` 目录后，应确保文件命名符合 `profile-{NNNN}-project-name.yaml` 格式。

### 7.2 证据留存

证据留存通用规则引用 `specs/07-工作模型基础规范.md` §7.4。Profile 对象特有差异：

1. Profile 归档（`archived`）时，应留存归档原因和确认记录。

---

## 8. 适配规则

### 8.1 AI 协作

AI 协作通用规则引用 `specs/07-工作模型基础规范.md` §7.5。Profile 对象特有差异：

1. AI 识别到新项目接入时，应判断是否需要创建 Profile（§1.3）；
2. 创建 Profile 前必须通过 Human Gate 确认（§5）。

### 8.2 Tools 辅助

Tools 辅助通用规则引用 `specs/07-工作模型基础规范.md` §7.6。当前由通用 Fact Validator 消费本文结构化契约完成校验，对象级 Tools 实践待按需创建。

### 8.3 Web 信息同步

Web 信息同步通用规则引用 `specs/07-工作模型基础规范.md` §7.7。当前未实现对象级 Web 实践，待后续统一适配。

---

## 9. 待补齐事项

1. Profile YAML schema 的 JSON Schema 表达待 Tools 实现稳定后补齐；
2. `related_tasks`、`related_adrs` 的引用校验规则待对应对象模型稳定后补充；
3. `project_path` 和 `ldvh_base_path` 的路径有效性校验规则待实践积累后确定是否需要独立字段；
4. `language` 和 `framework` 的枚举值待实践积累后确定是否需要标准化。
