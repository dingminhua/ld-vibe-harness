# LD Vibe Harness 对 Linear 的借鉴评估

> 创建日期：2026-05-30
> 状态：内部调研
> 编号归属：70-89 内部调研
> 调研边界：不直接构成强制规则
> 执行效力：无，结论需进入 01-69 正式规范区间或 ADR 后才成为稳定规则
> 上位依据：`specs/00-LD-Vibe-Harness理念与纲要.md`
> 相关规范：`specs/01-specs文档结构规范.md`、`specs/02-LDVH目录说明.md`、`specs/03-事实源边界与承载规范.md`

---

## 一、本文解决的问题

本文评估 LD Vibe Harness 应如何借鉴 Linear 的设计思想，同时保持自身"面向 Vibe Coding 的工程驾驭框架"的独特定位。本文是内部调研，不直接构成强制规则；调研结论进入 01-69 正式规范区间或 ADR 后才成为稳定规则。

---

## 二、LD Vibe Harness 与 Linear 的关系判断

| 维度 | LD Vibe Harness | Linear |
|---|---|---|
| 产品形态 | 本地规范 + 工具 + Harness 体系 | 云端 SaaS |
| 第一服务对象 | AI 执行者 | 软件研发人员 |
| 数据事实源 | Git 仓库中的 specs、ldvh-base、docs | Linear 云端数据库 |
| 核心对象 | Intent、Task、Memo、ADR、Evidence、Change、Pitfall | Issue、Project、Cycle、Roadmap |
| AI 协作 | 原生围绕 AI 行动模型设计 | AI 是增强能力，不是底层治理模型 |
| 审计闭环 | 核心能力（事实回写、门禁识别） | 非核心能力 |
| 状态流转 | 强约束，带 Human Gate | 团队自定义 Workflow |
| 工具定位 | Harness 工具 + 受控编辑入口 | 项目/问题管理系统 |

LD Vibe Harness 可以在任务治理体验上借鉴 Linear，但核心目标不是替代 Linear，而是把 Git 仓库里的项目事实源变成 AI 可读取、可执行、可回写的工程驾驭体系。

---

## 三、结论

LD Vibe Harness 不应定义为 Linear clone。更准确的判断是：

> LD Vibe Harness 可以学习 Linear 的高速任务处理手感，但应保持自身定位：Git 文件事实源 + AI 行动模型 + Harness 生产对象 + 受控执行闭环。

Linear 最值得学习的不是功能清单，而是它在高频任务处理上的速度感、清晰度和低打扰体验——这些体验可以让 AI 和人围绕同一组事实源更高效地协作。

---

## 四、可学习方向

### 4.1 学习速度感

Linear 的核心体验是任何操作都很快：页面打开快、列表切换快、状态更新快、键盘操作快、创建任务快、搜索快、过滤快。

LD Vibe Harness 应该让 AI 和人可以在几秒内完成：

```text
读取最小可行动上下文 → 识别当前任务场景 → 判断允许流转 → 执行或等待 Human Gate → 回写事实源
```

对应优化方向：

| 场景 | 目标体验 |
|---|---|
| AI 进入项目 | 立即读取 specs、ldvh-base 核心状态 |
| 看任务 | AI 一眼知道哪些 Blocked、哪些 Review Needed |
| 改状态 | 不需要复杂表单，按状态机允许流转执行 |
| 找意图 | 快速定位 Intent 和 source_doc |
| 找决策 | 快速查 ADR 和 Decision Needed |
| 给人确认 | 一键展示当前任务上下文、证据和 Human Gate 问题 |

### 4.2 学习 Issue 体验

Linear 的 Issue 好用，是因为它把一个可执行工作对象设计得非常清楚。

LD Vibe Harness 的 Task 可以学习这种体验，但字段建议保持自身语义；若升级为正式规范，宜满足 YAML 结构化承载原则：

| Linear Issue | LD Vibe Harness Task |
|---|---|
| title | title |
| description | 背景 / 目标 |
| status | 标准状态机 |
| priority | high / medium / low |
| project | project_id |
| project / initiative | source_intent / source_doc |
| relation | dependencies / blocked_by |
| comments | 更新日志 / 任务事件 |
| docs link | source_doc |
| acceptance criteria | acceptance |
| evidence | closure_evidence |

LD Vibe Harness 的任务详情页（或 AI 读取的任务 YAML）应成为一个完整上下文入口，回答：

1. 这个任务是什么
2. 为什么做（关联 Intent 或 source_doc）
3. 属于哪个意图或任务集
4. 当前卡在哪里
5. 前置依赖是什么
6. 关闭需要什么证据
7. 相关 specs / ADR 是什么
8. AI 继续执行时应带哪些上下文

### 4.3 学习视图模型

Linear 的一个强点是同一批任务可以用不同视图查看。

LD Vibe Harness 也应坚持同一事实源、多种视图，但视图要围绕 AI 行动模型设计：

| LD Vibe Harness 视图 | 作用 |
|---|---|
| 今日行动 | 当前最该处理的 Task |
| 阻塞视图 | 所有 Blocked / Decision Needed |
| 待验收视图 | 所有 Review Needed |
| 意图全貌 | Intent 与 TaskSet 状态 |
| 审计发现 | 所有待分流 / 待关闭审计项 |
| 决策视图 | ADR 与 Decision Needed 任务 |
| AI 上下文视图 | 选择任务后生成推荐阅读上下文 |

其中，阻塞视图和待验收视图对 AI 协作特别关键。AI 需要快速识别当前哪些任务进入 Human Gate、缺少什么证据、下一步允许流转到哪里。

### 4.4 学习快捷命令

Linear 的 Command Menu 值得借鉴。

LD Vibe Harness 可以设计轻量命令入口，支持：

- 搜索任务 / 意图 / ADR
- 新增 memo / intent
- 修改任务状态（按状态机允许流转）
- 跳转到 blocked 任务
- 跳转到 Review Needed 任务
- 复制 AI 上下文（Task + source_doc + ADR + dependencies + acceptance）
- 打开源文件位置

这类能力适合 Harness 工具定位，能减少 AI 和人在多个文件或页面之间反复查找。

### 4.5 学习状态流动体验

LD Vibe Harness 已有更严格的状态机和 Human Gate，但状态流转需要产品化：可见、可点、可解释。

任务详情页可以显示当前状态下允许的下一步，例如：

```text
当前状态：Executing

可流转到：
- Blocked：需要填写阻塞原因
- Decision Needed：需要填写决策问题
- Review Needed：需要填写验证结果
- Cancelled：需要填写取消原因
```

如果用户或 AI 触发非法流转，建议不只报错，也解释原因，例如：

```text
当前状态不能直接进入 Closed，请先进入 Review Needed，验收后再关闭。
```

这能把 LD Vibe Harness 的规则变成产品体验，而不是要求 AI 和人背规则。

### 4.6 学习轻量输入

Linear 创建 Issue 很轻，通常标题先行，后续补充。

LD Vibe Harness 也可支持轻量输入，但建议区分对象类型：

- 随手想法 → Memo
- 正式输入 → Intent
- 可执行工作 → Task

建议体验：

```text
输入一句话 → 选择类型 → 落到 ldvh-base 中对应事实源
```

例如用户输入：

```text
任务关闭前应该检查更新日志
```

LD Vibe Harness 可以允许用户选择：

- 作为 Memo 保存
- 作为 Intent 待分流
- 作为规则修改候选
- 关联到某个 TaskSet

重点是不宜一开始要求用户填写完整表单。

### 4.7 学习关联关系

Linear 的对象关系清楚。LD Vibe Harness 应强化自己的关系图：

```text
Intent
  └── TaskSet
        └── Task
              ├── dependencies
              ├── source_doc
              ├── related_adr
              ├── related_audit
              └── closure_evidence
```

最重要的关系包括：

| 关系 | 价值 |
|---|---|
| Task → source_doc | 知道任务来自哪个意图或需求 |
| Task → dependencies | 知道为什么阻塞 |
| Task → ADR | 知道依赖什么决策 |
| Audit Finding → Intent → Task | 审计闭环可追踪 |
| Memo → Intent → Task | 随手记录可沉淀 |
| Task → closure_evidence | 关闭可验证 |

这些关系会让 LD Vibe Harness 比普通任务看板更有治理感。

### 4.8 学习空状态和引导

工具不应让 AI 或人面对空白文件或页面。

典型空状态设计：

#### 没有 ldvh-base 时

```text
当前项目尚未初始化 ldvh-base。
可从 Intent 文档生成 TaskSet，或创建第一个 Intent。
```

#### 没有 blocked 任务时

```text
当前没有阻塞任务，项目推进顺畅。
```

#### 没有 ADR 时

```text
当前没有架构决策记录。遇到不可逆技术选择时应创建 ADR。
```

空状态应该帮助 AI 和人理解下一步，而不是只展示空列表。

### 4.9 学习少即是多

LD Vibe Harness 不应把所有规范都堆到 AI 上下文中，而应该把规范转化为：

- 提示（Action Model 中的 Gate 判断）
- 校验（状态机允许流转）
- 可点击动作（Harness 工具入口）
- 错误解释（非法流转说明）
- 上下文摘要（AI 读取的最小可行动上下文）

页面优先级应是：

1. 当前状态
2. 当前需要处理什么
3. 为什么卡住
4. 下一步能做什么
5. 相关事实源在哪里

---

## 五、不应照搬的地方

| Linear 能力 | LD Vibe Harness 是否应照搬 | 原因 |
|---|---|---|
| 云端账号体系 | 不建议 | LD Vibe Harness 是本地 / 仓库事实源工具 |
| 团队权限系统 | 暂不需要 | 会增加复杂度，且 LD Vibe Harness 以 AI 为第一服务对象 |
| 大型 SaaS 数据模型 | 不需要 | LD Vibe Harness 不维护数据库，事实源必须是 Git 文件 |
| 自动同步第三方工具 | 暂缓 | 容易偏离核心，应先做好 AI 行动闭环 |
| 重评论系统 | 不建议早期做 | 更新日志 / 任务事件更适合结构化承载 |
| Sprint / Cycle 重模型 | 谨慎 | LD Vibe Harness 更关注 AI 协作状态，不一定需要敏捷仪式 |
| 复杂 Roadmap | 后置 | 先做好意图全貌和任务流动 |

---

## 六、建议优先级

建议 LD Vibe Harness 优先吸收以下 5 个方向：

### 6.1 快捷操作入口

快速搜索、跳转、创建、改状态。适合 Harness 工具实现。

### 6.2 Task Detail 上下文

把任务详情（或 YAML 结构）做成 AI 协作上下文入口，包含 source_doc、dependencies、acceptance、closure_evidence。

### 6.3 Inbox / Intent Flow

让输入快速进入系统，再分流，而不是一开始就要求变成任务。

### 6.4 Blocked / Review Needed 视图

这两个队列是 AI 行动模型最关键的工作入口，AI 需要快速识别哪些任务进入 Human Gate、缺少什么证据。

### 6.5 一键复制 AI 上下文

这是 LD Vibe Harness 可以区别于 Linear 的核心能力。

用户或 AI 选中一个任务后，Harness 工具应能整理：

- 当前任务 YAML
- source_doc / Intent
- 相关 ADR
- 依赖任务
- 验收标准
- 最近更新

然后作为最小可行动上下文提供给 AI 继续执行。

---

## 七、产品原则沉淀

LD Vibe Harness 学习 Linear 的正确方向是：

> 让任务治理流动得很快、很清楚、很少打扰 AI 和人。

应吸收：

- 快捷操作
- 清晰任务详情
- 多视图
- 状态流转体验
- 轻量输入
- 关联关系
- 空状态引导

但必须保留自己的独特定位：

> Git 文件事实源 + AI 行动模型 + Harness 生产对象 + 受控执行闭环。

---

## 八、Human Gate 与检查要求

本文是内部调研，不直接触发 Human Gate。

当本文结论需要进入 01-69 正式规范区间或创建 ADR 时，应评估 Human Gate。

调研检查至少包括：

| 检查项 | 标准 |
|---|---|
| 上位依据 | 已声明上位依据 |
| 调研边界 | 明确不直接构成强制规则 |
| 与 00 总纲一致性 | 不违背 LD Vibe Harness 理念和五类构成要素 |
| 与事实源边界一致性 | 不定义新的事实源规则，只讨论体验优化方向 |
| 升级路径 | 明确结论进入正式规范或 ADR 的路径 |

---

## 九、待补齐事项

1. 本文结论如何进入 05 LDVH 工具基础规范（如快捷操作、视图模型）待工具规范稳定后确定；
2. 本文结论如何影响 10-39 生产对象规范（如 Task 字段设计）待对象规范稳定后确定；
3. 本文结论如何影响 40-69 行动模型规范（如状态流转提示、上下文生成）待行动模型规范稳定后确定。
