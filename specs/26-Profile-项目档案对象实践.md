# Profile-项目档案对象实践

> 创建日期：2026-05-28
> 对象名：Profile / 项目档案
> 适用范围：所有接入 PM Kit 的产品
> 上位依据：`specs-v2/00-PMKit理念与纲要.md`、`specs-v2/14-管理对象规范.md`、`specs-v2/10-事实源规范.md`、`specs-v2/11-AI协作规范.md`、`specs-v2/12-程序辅助规范.md`、`specs-v2/13-工具展示规范.md`

---

## 一、对象定位与准入

### 1.1 对象定义

Profile 是产品、项目、项目集和接入关系的身份与配置档案。Profile 让 AI 知道当前工作属于哪个项目、该项目是否属于某个产品或项目集、哪些事实源属于该项目。

Profile 的核心特征：

1. Profile 是 PM Kit 对管辖项目的**登记和配置**，不是受管理项目自身的配置；
2. Profile 承载身份（id、name）、路径映射（path）、目录配置（docs、task_base）和项目间关系；
3. Profile 是 AI 进入项目时**首先读取**的事实源；
4. Profile 不应由聊天记忆或工具缓存维护，应由 Git 文件事实源承载。

### 1.2 与临时判断的区别

| 维度 | 临时判断 | Profile |
|---|---|---|
| 性质 | 执行过程中的局部选择 | 项目身份和配置的权威声明 |
| 持续时间 | 一次性 | 长期稳定，变更频率低 |
| 复用价值 | 无 | 所有对象和流程都依赖 Profile |
| 追踪需求 | 不需要独立追踪 | 必须由 Git 文件事实源承载 |

### 1.3 准入条件

每个接入 PM Kit 的产品必须有且仅有一个 Profile。Profile 无需额外准入判断，产品接入即创建。

### 1.4 Profile 不应被误用为

1. 受管理项目的 package.json 或项目配置——Profile 是 PM Kit 对管辖项目的登记；
2. 规则文件——Profile 不定义行为约束，只定义身份和路径；
3. 动态状态——Profile 是相对稳定的配置，变更频率低；
4. 工具配置——Profile 不定义 MCP Server 或工具权限。

### 1.5 Profile 与 Identity 的关系

Identity 是旧命名，现更名为 Profile。两者是同一对象的名称变更：

- Identity → Profile：语义从"身份"扩展为"项目档案"，覆盖身份 + 路径映射 + 目录配置 + 项目间关系
- product.yaml 继续作为 Profile 的落地载体
- 14-管理对象规范 §二 中的 "Identity 让 AI 知道项目、产品和边界是什么" 更新为 "Profile 让 AI 知道项目、产品和边界是什么"

---

## 二、事实源边界

> 事实源边界声明：本文档是 Profile 对象实践的权威事实源。本文档定义 Profile 的对象定位、准入条件、生命周期、字段契约、对象关系和适配规则。本文档不重新定义管理对象语义（见 14）、事实源载体规则和格式契约（见 10）、AI 协作总原则（见 11）、程序辅助总原则（见 12）、工具展示总原则（见 13）。

### 2.1 本文档的权威领域

本文档定义 Profile 的以下实践规则：

1. Profile 的对象定位与准入条件；
2. Profile 的载体规范和 YAML 结构定义；
3. Profile 的 Roster 结构和项目角色判定；
4. Profile 与其他对象的关系；
5. Profile 的初始化检查项和审计检查项；
6. Profile 与 10-13 各层的适配声明。

### 2.2 本文档不重新定义的内容

1. 管理对象语义、对象地图和对象准入总规则——见 14；
2. 事实源载体边界、格式契约和 YAML 字段定义——见 10；
3. AI 协作总原则、Rule/Skill/Agent 行为边界——见 11；
4. 程序辅助总原则、解析校验聚合写入规则——见 12；
5. 工具展示总原则、派生视图边界——见 13。

### 2.3 与其他规范的事实源关系

本文档的规则是对 14 §八管理对象总表中 Profile 定义的实践展开，载体规范对齐 10，适配声明对齐 11/12/13 各层规范。本文档不扩张、不重写、不替代基础规范层已有规则。

---

## 三、生命周期

Profile 无状态机。Profile 的生命周期与产品一致：

1. **创建**：产品接入 PM Kit 时创建 product.yaml；
2. **修改**：管辖项目变更、路径映射调整、目录配置变更时修改 product.yaml；
3. **归档**：产品不再接入 PM Kit 时归档 product.yaml。

Profile 修改频率低，每次修改必须触发 Human Gate。

---

## 四、字段契约

### 4.1 存放位置

```text
{product-root}/product.yaml
```

product.yaml 是 Profile 的唯一权威载体。每个产品（可能包含多个项目）维护一个 product.yaml。

### 4.2 结构定义

```yaml
product:
  id: {product-id}
  name: {product-display-name}
  description: {one-line-description}
  root: {product-root-path}

roster:
  - id: {project-id}
    name: {project-display-name}
    path: {project-relative-path}
    docs: {docs-directory-name}
    task_base: {task-base-directory-name}
```

### 4.3 product 段字段

| 字段 | 必须 | 类型 | 说明 |
|---|---|---|---|
| `id` | 是 | string | 产品唯一标识，小写字母、数字、连字符 |
| `name` | 是 | string | 产品显示名称 |
| `description` | 是 | string | 一句话产品描述 |
| `root` | 是 | string | 产品根目录相对路径，通常为 `.` |

### 4.4 roster 段字段

roster 是 PM Kit 管辖的项目名册。每个条目是一个项目的登记信息。

| 字段 | 必须 | 类型 | 说明 |
|---|---|---|---|
| `id` | 是 | string | 项目唯一标识，小写字母、数字、连字符。单项目产品使用 `self` |
| `name` | 是 | string | 项目显示名称 |
| `path` | 是 | string | 项目目录相对路径（相对于 product.root） |
| `docs` | 是 | string | 项目文档目录名（相对于项目 path） |
| `task_base` | 是 | string | 项目 Kit Base 目录名（相对于项目 path） |

### 4.5 典型实例

**单项目产品**：

```yaml
product:
  id: trae-pm-kit
  name: Trae PM Kit
  description: 帮助 AI 高效、准确、可控地推进 Vibe Coding
  root: .

roster:
  - id: self
    name: PM Kit 自身
    path: .
    docs: docs
    task_base: pm-kit-base
```

**多项目产品**：

```yaml
product:
  id: my-saas
  name: My SaaS Product
  description: 企业级 SaaS 平台
  root: .

roster:
  - id: governance
    name: 治理项目
    path: .
    docs: docs
    task_base: pm-kit-base
  - id: frontend
    name: 前端项目
    path: ../frontend
    docs: docs
    task_base: pm-kit-base
  - id: backend
    name: 后端项目
    path: ../backend
    docs: docs
    task_base: pm-kit-base
```

---

## 五、与其他对象的关系

### 5.1 依赖关系

- 所有对象都依赖 Profile（需要知道项目归属和路径）
- Rules 依赖 Profile（L1 规则路径由 Profile 决定）

### 5.2 引用关系

- Task 通过 `requirement_doc` 字段引用 TaskSet，TaskSet 的路径由 Profile 的 `docs` 字段决定
- Skill 和 Agent 读取 Profile 获取项目路径和目录映射

### 5.3 Profile 在上下文包中的角色

Profile 是项目上下文包的首要来源：

| 上下文包类型 | Profile 的角色 |
|---|---|
| 项目上下文包 | 首先读取 product.yaml，获取项目身份和路径 |
| 任务执行上下文包 | 通过 Profile 定位 Task YAML 和 TaskSet 的路径 |
| 需求规划上下文包 | 通过 Profile 定位 docs 目录和已有 TaskSet |
| Review 上下文包 | 通过 Profile 定位 Task YAML 和变更文件路径 |

---

## 六、初始化检查项

| 检查项 | 标准 |
|---|---|
| 对象定位 | Profile 定义已与 14 §八对齐，明确 Profile 是身份与配置档案 |
| 准入条件 | 已定义 Profile 准入条件（产品接入即创建） |
| 生命周期 | 已定义 Profile 生命周期（创建→修改→归档），无状态机 |
| 字段契约 | 已定义 product.yaml 的 product 段和 roster 段字段 |
| 载体 | 已明确 Profile 存放位置为 product.yaml |
| 项目角色判定 | 已定义单项目/多项目产品治理项目/多项目产品子项目的判定方式 |
| 适配声明 | 已声明与 10-13 各层的适配关系 |

---

## 七、审计检查项

| 检查项 | 标准 |
|---|---|
| 禁止扩张 | 未新增、扩张、重写或替代基础规范 |
| 上位依据 | 已声明 00、14、10-13 为上位依据 |
| 事实源边界 | 核心规则章节开头已声明事实源边界 |
| 文件存在 | product.yaml 存在于产品根目录 |
| product 段完整 | id、name、description、root 四个字段均存在 |
| roster 段完整 | 至少有一个条目，每个条目包含 id、name、path、docs、task_base |
| id 唯一 | roster 中每个 id 不重复 |
| 路径有效 | path、docs、task_base 指向的目录实际存在 |
| 路径相对 | 所有路径使用相对路径，不使用绝对路径 |
| 单项目标记 | 单项目产品的 roster 条目 id 为 `self` |
| 字段一致 | product.yaml 中的项目标识、路径、依赖等字段必须反映项目实际 |
| Human Gate | 修改 product.yaml 字段必须触发 Human Gate |

---

## 八、AI 协作适配

1. AI 进入项目时必须首先读取 product.yaml，获取项目身份和路径映射；
2. AI 不得修改 product.yaml，修改必须触发 Human Gate；
3. AI 读取受管理项目资产时，必须通过 Profile 的路径映射定位目录；
4. AI 不得用聊天记忆或工具缓存替代 Profile 的项目身份判断。

---

## 九、Human Gate

以下 Profile 相关操作必须触发 Human Gate：

1. 新增或删除 roster 条目（管辖项目变更）；
2. 修改 roster 条目的 path、docs 或 task_base 字段（路径映射变更）；
3. 修改 product.id 或 product.name（产品身份变更）；
4. 改变产品/项目角色判定结果（单项目 ↔ 多项目）。

---

## 十、程序辅助适配

1. 程序可校验 product.yaml 的字段完整性和路径有效性；
2. 程序可校验 roster 中 id 的唯一性；
3. 程序可校验 product.yaml 中的路径与实际目录结构是否一致；
4. 程序可根据 Profile 生成项目上下文包。

---

## 十一、工具展示适配

1. 工具可展示产品身份和管辖项目列表；
2. 工具可展示项目间的路径映射和目录配置；
3. 工具可展示产品/项目角色判定结果；
4. 工具不得在 Profile 展示中维护第二事实源。

---

## 十二、待补齐事项

1. product.yaml 的 YAML schema 校验规则待程序辅助规范展开；
2. roster 条目是否需要扩展字段（如 `specs`、`rules` 目录）待实践确认；
3. 多项目产品中子项目的 Profile 是否需要独立文件待实践确认；
4. roster 是否需要支持嵌套（项目集下的项目集）待实践确认；
5. product.yaml 与 L0/L1 规则的路径引用关系是否需要在 Profile 中声明待实践确认；
6. Profile 变更是否需要创建 Change 记录待实践确认。
