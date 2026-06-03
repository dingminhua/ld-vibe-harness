# LDVH Web 网站重做推进基础文档

> 创建日期：2026-06-04
> 定位：基于 evals/17 产品方向共识、当前 LDVH 事实源与 pm-kit-web 现状，为重新建设 LDVH Web 网站提供推进基础
> 编号归属：specs/evals/ 项目评估文档，自然序号 19
> 调研边界：基于当前仓库文档、事实源、Tools 与 pm-kit-web 代码现状；不直接构成强制规则
> 执行效力：无，结论需进入正式 specs、ADR、Task 或实现计划后才成为稳定执行依据
> 上位依据：`specs/00-LD-Vibe-Harness理念与纲要.md`、`specs/12-LDVH工具基础规范.md`、`specs/12.02-Web信息同步规范.md`
> 相关参考：`specs/evals/17-LDVH-Gstack-Trae融合产品方向共识.md`
> 代码调研来源：`pm-kit-web/`、`tools/check_fact_model.py`、`ldvh-base/`

---

## 1. 本文解决的问题

本文用于承接“基于现状参考之前设计，重新做一个 Web 网站”的推进需求。

本文解决以下问题：

1. 明确新 LDVH Web 网站应继承和放弃什么；
2. 明确当前 `pm-kit-web/` 与 LDVH 新事实内核之间的差距；
3. 把 evals/17 中关于 Web MVP 的共识转化为可执行的产品边界；
4. 为后续 Spec、Task、ADR 或实现工作提供固定起点；
5. 防止新 Web 再次变成第二套任务系统、第二套事实源或复杂产品先行。

本文不是正式 Web 规范，也不是 UI 设计稿。本文只作为推进基础文档。

---

## 2. 结论

新 LDVH Web 网站应重做，而不是在旧 `pm-kit-web/` 上继续累加复杂功能。

重做的核心判断是：

```text
Git 文件事实源 → PyTools 聚合 → Web 只读展示 → 人做更高质量 Human Gate
```

新 Web 的第一阶段定位应是 **LDVH 只读态势网站**，而不是任务写入系统、事实源编辑器或 AI 自动执行平台。

第一阶段应围绕五类最小事实内核展示：

```text
Intent / Task / ADR / Evidence / Change
```

同时补充 Pitfall、Fact Validator、Core Loop 阶段态势和 Human Gate 待确认上下文。

旧 `pm-kit-web/` 中值得保留的是产品经验和交互经验，不是数据模型和事实源假设。具体来说：

1. 保留“驾驶舱 + 看板 + 待决策 + 最近变化 + 健康检查”的产品表达；
2. 保留 FastAPI + 静态前端这种低成本本地 Web 形态作为候选实现方式；
3. 保留状态颜色、中文别名、刷新、详情面板、Human Gate 提示等交互经验；
4. 放弃对 `product.yaml`、`docs/*.md`、`task-base/`、旧 PM Kit 状态字段和旧需求文档结构的核心依赖；
5. 放弃第一阶段受控写入，先建立可信只读态势。

新 Web 的第一目标不是“管理所有事情”，而是让人一眼看懂：

```text
当前 LDVH 处于什么阶段；
有哪些事实对象；
哪些 Task 正在推进；
哪些 Evidence 支撑关闭；
哪些 ADR 是 accepted；
哪些校验失败；
哪些事项需要 Human Gate；
最近发生了什么 Change。
```

---

## 3. 当前 LDVH 状态理解

### 3.1 已具备的基础

截至本文创建时，LDVH 已具备 Web 重做所需的最小基础：

1. `ldvh-base/` 已存在结构化事实实例目录；
2. ADR、Intent、Task、Evidence、Pitfall 已有实例；
3. Intent、Task、Evidence、Pitfall 已纳入 `tools/check_fact_model.py` 最小校验；
4. ADR 已有 `tools/adr_index.py` 相关能力；
5. Change 已有规范、commit message 校验工具与 `ldvh-commit` Skill；
6. `ldvh-intake` 与 `ldvh-close` 已形成 Core Loop 的 Intent / Record 阶段入口；
7. L0 / L1 Rules 已加入 Core Loop 路由；
8. evals/17 已明确 Web MVP 只读对齐 `ldvh-base` 的方向。

这说明新 Web 可以从真实事实源读取，而不需要先发明一套 Web 内部任务模型。

### 3.2 当前最小闭环

当前已跑通的最小闭环是：

```text
Intent → Task → Evidence → Close
```

从 Web 视角看，第一阶段应把这个闭环可视化：

1. Intent 是否 active / completed；
2. Task 是否 planned / executing / review_needed / closed；
3. Task 关闭是否有关联 Evidence；
4. Evidence 是否 verified；
5. 关闭动作是否可追溯到 Change / commit；
6. 过程中是否产生 Pitfall 或 ADR。

### 3.3 当前关键缺口

新 Web 不能忽略当前 LDVH 的缺口：

1. Change / Record 关系仍在澄清中；
2. Plan / Execute / Verify / Learn 阶段 Skill 尚未稳定；
3. Fact Validator 还不是通用 Contract 消费器；
4. Reference Validator、State Machine Validator、统一聚合器尚未形成；
5. `pm-kit-web/` 尚未对齐 `ldvh-base/`；
6. `pm-kit-web/` 仍包含旧 PM Kit 的 docs / task-base / requirement 扫描逻辑；
7. 当前仓库没有 `product.yaml`，旧 Web 启动后会天然进入配置缺失路径。

因此，新 Web 的推进顺序必须先补只读聚合和事实源适配，再谈写入、复杂交互和产品扩展。

---

## 4. 旧 pm-kit-web 现状评估

### 4.1 当前形态

`pm-kit-web/` 当前是一个本地 FastAPI + 静态前端工作台原型。

主要结构包括：

| 路径 | 当前作用 |
|---|---|
| `pm-kit-web/server/main.py` | FastAPI 入口、API 路由、静态页面挂载 |
| `pm-kit-web/server/config.py` | 读取 `product.yaml`、项目列表、旧任务状态映射、缓存 |
| `pm-kit-web/server/requirements.py` | 扫描 `docs/*.md` 需求文档、解析执行对象、执行旧状态流转 |
| `pm-kit-web/server/taskbase.py` | 扫描旧 `task-base/tasks` 与 `task-base/memos` YAML |
| `pm-kit-web/server/views.py` | 聚合 dashboard、action board、waiting decisions、panorama 等视图 |
| `pm-kit-web/client/index.html` | 静态页面骨架，包含总览、任务、任务集、产品、备忘、设置等区域 |
| `pm-kit-web/client/app.js` | 前端状态、tab、渲染、刷新、复制 prompt、详情面板等逻辑 |
| `pm-kit-web/client/style.css` | 视觉样式 |
| `pm-kit-web/start.sh` | 本地启动脚本，默认端口 8770 |

### 4.2 已有价值

旧 Web 已经验证了一些可继承的产品经验：

1. 本地 Web 工作台可以作为人类态势入口；
2. 总览卡片、最近变化、任务指标、待决策入口是有效的信息组织方式；
3. 状态标准化、状态颜色、中文别名能降低阅读成本；
4. 详情抽屉适合展示对象上下文；
5. 待决策、阻塞、待验收等视图有利于 Human Gate；
6. 刷新和文件变更缓存可以改善本地体验；
7. 启动脚本可降低 Web Preview 验证成本。

这些经验应被吸收为新 Web 的交互参考。

### 4.3 不应继续继承的部分

旧 Web 的核心问题是它服务的是旧 PM Kit 结构，不是当前 LDVH 事实内核。

不应继续继承为核心依赖的部分包括：

1. `product.yaml` 作为必须配置入口；
2. `docs/*.md` 中嵌入执行对象的旧解析方式；
3. `task-base/tasks`、`task-base/memos` 作为任务和备忘事实源；
4. 旧状态集合 `Ready for Plan / Planned / Executing / Blocked / Decision Needed / Review Needed / Closed / Cancelled` 直接作为 LDVH Task 状态机；
5. Web 内部直接执行旧状态流转写回；
6. 从 `docs/adr` 扫描 ADR，而不是读取 `ldvh-base/adrs/`；
7. 把旧需求文档、旧任务对象和旧备忘对象作为主要信息架构。

这些部分可以作为历史参考，但不应成为新 Web 的架构基础。

---

## 5. 新 Web 产品定位

### 5.1 第一阶段定位

新 LDVH Web 第一阶段是：

```text
LDVH 只读态势网站
```

它面向人类用户，帮助用户在 Human Gate、验收、审查和方向判断时获得高质量上下文。

第一阶段不承担事实源写入，不承担 AI 调用，不承担状态流转，不承担自动修复。

### 5.2 第一阶段用户问题

新 Web 第一阶段应回答以下问题：

1. 当前项目有哪些 Intent、Task、ADR、Evidence、Pitfall；
2. 当前 Core Loop 处于哪些阶段；
3. 哪些 Task 正在执行、待验收或已关闭；
4. 已关闭 Task 的关闭证据是什么；
5. Evidence 的验证结果是什么；
6. 哪些 ADR 是 accepted，哪些只是 proposed；
7. 哪些事实源校验失败；
8. 哪些对象缺少关联或存在状态不一致；
9. 最近的 Change / commit 摘要是什么；
10. 哪些事项需要 Human Gate。

### 5.3 第一阶段不做什么

第一阶段明确不做：

1. 不做事实源写入；
2. 不做 Web 内状态流转；
3. 不做 Web 内任务创建；
4. 不调用 AI、Skill 或 Agent；
5. 不引入数据库作为权威状态；
6. 不把浏览器页面状态当作事实源；
7. 不做复杂多项目产品管理平台；
8. 不优先适配旧 PM Kit docs / task-base；
9. 不在 Change / Record 边界未清晰前扩大写入入口。

---

## 6. 信息架构建议

### 6.1 首页：LDVH 态势总览

首页应展示：

| 模块 | 内容 |
|---|---|
| Core Loop 状态 | Intent / Plan / Execute / Verify / Record / Learn 当前覆盖情况 |
| 对象计数 | Intent、Task、ADR、Evidence、Pitfall 数量与状态分布 |
| 当前焦点 | active Intent、executing Task、review_needed Task |
| 校验状态 | Fact Validator 最新结果 |
| Human Gate | 待用户确认、待验收、待决策事项 |
| 最近变化 | 最近 commit / Change 摘要 |
| 风险提示 | proposed ADR、缺少 Evidence、状态不一致、引用缺失 |

### 6.2 Task 页面

Task 页面应展示：

1. Task 列表；
2. 状态分组；
3. acceptance；
4. source；
5. parent Intent；
6. related_evidence；
7. related_adrs；
8. related_changes；
9. closed_at 与 closure_evidence；
10. 校验问题。

Task 页面第一阶段只读。

### 6.3 Intent 页面

Intent 页面应展示：

1. Intent 列表；
2. description；
3. success_criteria；
4. related_tasks；
5. related_adrs；
6. 状态；
7. 完成判断是否有 Task / Evidence 支撑。

### 6.4 Evidence 页面

Evidence 页面应展示：

1. Evidence 列表；
2. evidence_type；
3. verification_method；
4. verification_result；
5. source_task / source_adr；
6. content 摘要；
7. 是否支撑 Task closure。

### 6.5 ADR 页面

ADR 页面应展示：

1. ADR 列表；
2. status；
3. accepted / proposed / superseded / deprecated 分组；
4. accepted ADR 对当前执行的影响；
5. proposed ADR 不作为执行依据的提示；
6. 与 Task / Intent / Evidence 的关联。

### 6.6 Validate 页面

Validate 页面应展示：

1. `check_fact_model.py` 执行结果；
2. error / warning 统计；
3. 按对象分组的问题；
4. 问题定位到文件路径；
5. 后续可扩展 Reference Validator、State Machine Validator、Specs Checker。

第一阶段可以由后端调用确定性 PyTools 获取输出，但不得让 Web 直接修复。

### 6.7 Change 页面

Change 页面应谨慎处理。

在 Change YAML 实例尚未决定前，Change 页面可以展示：

1. 最近 Git commit 摘要；
2. 是否符合 `specs/22` 的提交格式；
3. 与 Task / Evidence / ADR 的显式文本引用；
4. Record 阶段仍未清晰的提示。

Change 页面不得伪造 `ldvh-base/changes/` 事实实例。

---

## 7. 数据与技术路线

### 7.1 数据来源优先级

新 Web 数据来源优先级应为：

1. `ldvh-base/` YAML 事实实例；
2. `specs/` 正式规范与 evals 参考文档；
3. `tools/` 确定性校验和聚合输出；
4. Git commit 信息；
5. 运行时缓存。

其中只有 Git 文件事实源和 Git 历史是稳定事实来源。Web 缓存和页面状态只能是派生层。

### 7.2 推荐后端路线

后端可以继续采用 Python + FastAPI，但应重建数据层：

```text
ldvh-base reader
→ object normalizer
→ relation resolver
→ validator runner
→ view model builder
→ read-only API
```

新的后端模块可以按职责拆分：

| 模块 | 职责 |
|---|---|
| object reader | 读取 `ldvh-base/` 下各类 YAML |
| schema adapter | 依据当前 Contract 做字段归一化 |
| relation resolver | 解析 related_tasks、related_evidence、related_adrs、source_task 等引用 |
| validator runner | 调用 Fact Validator 等确定性工具 |
| change reader | 读取 Git commit 摘要和格式检查结果 |
| view builder | 生成前端只读视图模型 |

### 7.3 推荐前端路线

前端第一阶段应保持简单：

1. 可以继续使用静态 HTML / CSS / 原生 JS；
2. 也可以在后续 Spec 中评估是否引入现代前端框架；
3. 不应为了 UI 技术栈先扩大工程复杂度；
4. 应优先保证本地可启动、可预览、可验证。

如果使用旧 `pm-kit-web/client` 作为参考，应只迁移视觉和交互模式，不迁移旧数据假设。

### 7.4 路径与命名建议

根据 `specs/01-LDVH目录说明.md`，正式 Web Tools 实现目录应是 `web/`。

因此后续实现可评估以下两种路线：

| 路线 | 说明 | 建议 |
|---|---|---|
| 新建 `web/` | 按正式目录重新建设 LDVH Web | 推荐 |
| 改造 `pm-kit-web/` | 保留旧目录名继续重构 | 不推荐作为最终形态 |

如果短期需要复用旧代码，可先保留 `pm-kit-web/` 作为历史原型，再把新实现放入 `web/`，避免新旧事实模型混杂。

---

## 8. 分阶段推进建议

### 8.1 阶段一：只读事实源聚合

目标：让 Web 能从 `ldvh-base/` 读取并展示核心对象。

范围：

1. Intent 列表；
2. Task 列表；
3. Evidence 列表；
4. ADR 列表；
5. Pitfall 列表；
6. 对象状态计数；
7. 文件路径和更新时间。

验收标准：

1. 不依赖 `product.yaml`；
2. 不依赖旧 `docs/*.md` 执行对象；
3. 不依赖旧 `task-base/`；
4. Web 数据可追溯到 `ldvh-base/` 文件；
5. 页面状态不写回事实源。

### 8.2 阶段二：关系与闭环展示

目标：展示最小闭环关系。

范围：

1. Intent → Task；
2. Task → Evidence；
3. Task → ADR；
4. Evidence → source_task / source_adr；
5. Task closure evidence；
6. proposed ADR 风险提示。

验收标准：

1. 能识别引用缺失；
2. 能展示关闭证据链；
3. 能提示无法作为执行依据的 ADR；
4. 不新增事实源字段。

### 8.3 阶段三：校验与健康度

目标：让 Web 展示确定性校验结果。

范围：

1. 集成 Fact Validator 输出；
2. 展示 error / warning；
3. 按对象和文件分组；
4. 展示校验命令和时间；
5. 后续预留 Reference Validator 与 State Machine Validator。

验收标准：

1. 校验结果来自 Tools；
2. Web 不直接修改 YAML；
3. 校验失败时能定位文件；
4. 校验输出不替代 Evidence。

### 8.4 阶段四：Human Gate 上下文

目标：提升人类确认质量。

范围：

1. 待验收 Task；
2. proposed ADR；
3. 缺少 Evidence 的关闭候选；
4. 触发规范或事实源高影响变更的提示；
5. 可复制给 AI 的上下文摘要。

验收标准：

1. Web 只展示确认上下文；
2. Human Gate 仍由 AskUserQuestion、事实源记录和相关 Skill 承载；
3. Web 按文件事实源回读刷新。

### 8.5 阶段五：受控写入评估

只有在 Change / Record 闭环清晰、Tools 受控写入能力稳定、Human Gate 记录方式明确后，才评估 Web 写入。

可能写入范围：

1. 触发已验证 Tools 的受控写入；
2. 生成待确认 YAML 草案；
3. 写入后运行 validator；
4. 写入后要求 Evidence / Change。

本阶段不应提前进入实现。

---

## 9. 与 evals/17 的对齐

本文对 evals/17 的承接关系如下：

| evals/17 共识 | 本文承接方式 |
|---|---|
| Gstack 提供体验范式 | 吸收驾驶舱、阶段入口、真实验证和 Gate 上下文体验 |
| LDVH 提供治理骨架 | Web 只展示 Git 文件事实源和规范化对象关系 |
| Trae Solo 提供运行环境 | 使用本地服务、RunCommand、Web Preview、AskUserQuestion 周边能力 |
| Core Loop 是第一体验 | 首页围绕 Intent / Plan / Execute / Verify / Record / Learn 展示 |
| 最小事实内核优先 | 第一阶段围绕 Intent / Task / ADR / Evidence / Change |
| 先 Record / Change，后 Web 写入 | 本文明确第一阶段不做写入 |
| 先 Contract 消费，后复杂自动化 | Web 优先消费 PyTools / Contract 方向，不自定义新事实模型 |
| 先 Dogfood，后产品扩张 | 新 Web 先服务 LDVH 自身项目态势 |
| Web MVP 只读对齐 `ldvh-base` | 本文将其作为第一阶段核心目标 |

---

## 10. 后续建议动作

建议后续按以下顺序推进：

1. 创建正式实现 Spec，明确 `web/` 目录、API、页面和验收标准；
2. 为 Web 重做创建 LDVH Task；
3. 先实现只读 `ldvh-base` 聚合器；
4. 运行 `tools/check_fact_model.py ldvh-base` 并在 Web 展示结果；
5. 实现首页与 Task / Intent / Evidence / ADR 详情页；
6. 用当前 LDVH 自身事实源进行 Web Preview 验证；
7. 记录 Evidence；
8. 完成后再评估是否需要 ADR 决定 `pm-kit-web/` 的去留、迁移或归档。

如果后续决定把 Web 实现目录从 `pm-kit-web/` 正式迁移到 `web/`，应评估是否触发目录定位、工具实现边界或历史原型处理相关的 ADR。

---

## 11. 风险与约束

当前主要风险包括：

1. 继续沿用旧 `pm-kit-web/` 导致新旧事实源混杂；
2. 过早做写入导致绕过 Change / Record 闭环；
3. 页面状态被误当成事实源；
4. 过早引入复杂前端框架，分散对事实源对齐的注意力；
5. 为了 Web 好看而弱化对象状态机、Evidence 和 Human Gate；
6. Change 还未实例化时，Web 伪造变更对象；
7. 只展示对象列表而不展示关系和闭环，导致对 Human Gate 帮助有限。

约束原则：

1. Web 永远不是最终事实源；
2. 第一阶段只读；
3. 数据必须可追溯到 Git 文件事实源；
4. Tools 负责确定性处理，Web 负责人类可读体验；
5. Web 不直接调用 AI、Skill 或 Agent；
6. 写入能力必须等待 Record / Change 和 Human Gate 链路稳定后再评估；
7. 每一步都必须服务最近一次可运行闭环。

---

## 12. 固定沟通起点

后续讨论 LDVH Web 重做时，应优先回到本文确认：

1. 当前方案是否仍是只读优先；
2. 当前数据是否来自 `ldvh-base/` 或确定性 Tools 输出；
3. 当前页面是否提升 Human Gate 质量；
4. 当前实现是否避免旧 PM Kit 数据模型回流；
5. 当前实现是否避免 Web 成为第二事实源；
6. 当前阶段是否仍服务 LDVH 自身 Dogfood；
7. 当前变更是否需要进入正式 Spec、Task、Evidence、ADR 或 Change。

本文的核心压缩表达是：

```text
重做 LDVH Web，不续写旧 PM Kit；只读对齐 ldvh-base；先聚合、后展示、再验证；先 Human Gate 上下文，后受控写入；Web 是态势入口，不是事实源。
```

---

## 13. 基于实际运行验证的结构建议

> 本节基于实际启动 trae-pm-kit/pm-kit-web 并检查所有 API 和 HTML 结构后的结论。

### 13.1 当前页面结构现状

当前 6 Tab 导航中，实际有内容的只有 2 个：

| Tab | 实际状态 |
|---|---|
| 总览 | 有内容（指标卡片 6 个 + 备忘 + 需求进度 + 最近变化） |
| 任务 | 空壳，无 section |
| 任务集 | 预留，只有标题和描述 |
| 产品 | 预留，只有标题和描述 |
| 备忘 | 预留，只有标题和描述 |
| 设置 | 有内容（项目规则 + 产品配置 + 全景视图 + 关于，共 4 个二级 Tab） |

此外还有旧隐藏区域：`#actions`（行动列表/看板）、`#requirements`（需求文档）、`#governance`（治理/决策/审计）、`#legacyOverview`（旧驾驶舱）。

全局交互组件：Health Bar 顶部栏、任务详情抽屉、Command Menu 预留、新增/编辑/归档备忘弹窗、状态流转弹窗。

### 13.2 导航结构建议

**6 Tab 收敛为 5 Tab：**

| 新 Tab | 来源 | 说明 |
|---|---|---|
| 态势（首页） | 总览改造 | 核心入口，围绕 Core Loop 展示 |
| 任务 | 新实现 | 直接读 `ldvh-base/tasks/*.yaml` |
| 决策 | 新 Tab | 来自 `ldvh-base/adrs/*.yaml` |
| 证据 | 新 Tab | 来自 `ldvh-base/evidence/*.yaml` |
| 设置 | 保留改造 | 规则/配置/全景/关于 |

**建议删除的 Tab：**

- **任务集**：已无实质内容，且 PM Kit 的 ADR-0009 已经移除 TaskSet 层
- **产品**：作为单项目 Web，产品维度信息可以放到设置/首页，不值得单独 Tab
- **备忘**：LDVH 事实源体系中 Memo 不是核心对象，可合并到设置或移除

### 13.3 态势页（首页）建议

| 区块 | 建议 | 来源 |
|---|---|---|
| Core Loop 状态条 | 新增：展示 Intent/Plan/Execute/Verify/Record/Learn 覆盖情况 | — |
| 任务指标卡片 | 保留但改造：Planned/Executing/Review/Closed，点击可跳转 | 旧 6 卡片 → 按 LDVH 状态改造 |
| 焦点分区 | 保留：active Intent、executing Task、review_needed Task | 旧"进行中"概念 |
| 待 Human Gate | 保留：替代旧"待决策" | 旧待决策/治理 |
| 校验状态 | 新增：Fact Validator 结果摘要 | — |
| 最近变化 | 保留但改造：对接 Change/Git commit | 旧最近变化 |
| 最近证据 | 新增：显示最新 Evidence | — |

### 13.4 任务页建议

| 区块 | 建议 | 来源 |
|---|---|---|
| 列表 | 保留，直接读 YAML | 旧行动列表 |
| 状态筛选 | 保留 | 旧筛选 |
| 详情抽屉 | 保留并增强：parent Intent、related Evidence、related ADRs | 旧右侧滑出面板 |
| 看板视图 | 保留旧代码经验 | 旧看板 |

### 13.5 决策页（新）

| 区块 | 建议 |
|---|---|
| ADR 列表 | status 分组：accepted / proposed / superseded |
| 详情 | context、decision、consequences |
| 风险提示 | proposed ADR 提示"不作为执行依据" |

### 13.6 证据页（新）

| 区块 | 建议 |
|---|---|
| 列表 | evidence_type 分组 |
| 详情 | verification_result、关联 Task |
| 关闭证据链 | 哪些 Evidence 支撑了哪些 Task 关闭 |

### 13.7 设置页建议

| 二级 Tab | 建议 |
|---|---|
| 项目规则 | 保留 |
| 产品配置 | 简化，去掉 product.yaml 依赖 |
| 全景视图 | 保留 mermaid 图，但基于真实事实源生成 |
| 关于 | 保留 |

### 13.8 整体原则

1. 一级导航对齐 LDVH 最小事实内核：Intent/Task/ADR/Evidence/Change
2. 旧 PM Kit 交互经验保留：刷新、详情抽屉、状态颜色、中文别名、弹窗流转、Command Menu 预留结构
3. 不保留旧数据模型：不读 docs/*.md 执行对象、不读旧 task-base、不依赖 product.yaml
4. 技术栈保持简单：第一阶段 FastAPI + 静态前端，后续再评估是否需要框架
5. 页面永远不是事实源：所有数据可追溯到 `ldvh-base/` YAML 文件
```
