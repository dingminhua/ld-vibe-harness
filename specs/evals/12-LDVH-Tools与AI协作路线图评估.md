# LDVH Tools 与 AI 协作路线图评估

> 创建日期：2026-06-03
> 更新日期：2026-06-04
> 定位：LD Vibe Harness 当前 Tools 能力缺口、AI 协作优化方向与实施优先级的多视角评估
> 调研边界：不直接构成强制规则
> 执行效力：无，结论需进入 00-79 正式规范区间或 ADR 后才成为稳定规则
> 上位依据：`specs/00-LD-Vibe-Harness理念与纲要.md`
> 相关规范：`specs/12-LDVH工具基础规范.md`、`specs/12.01-Tools辅助规范.md`、`specs/13-LDVH事实模型基础规范.md`、`specs/14-LDVH行动模型基础规范.md`、`specs/20-事实模型集合索引.md`、`specs/50-行动模型集合索引.md`
> 方向校准：`specs/evals/17-LDVH-Gstack-Trae融合产品方向共识.md`
> 代码调研来源：`/Users/dmh2002/trae_projects/gstack`、`/Users/dmh2002/trae_projects/ld-vibe-harness`

---

## 1. 本文解决的问题

LDVH 当前规范骨架已基本完整（00-14 核心基础规范、20-22 事实模型、50-51 行动模型），但 Tools 辅助层能力集中在 specs 自查和 ADR 索引，Web 信息同步层为零。事实模型 23-32 和行动模型 52-60 全部处于 `planned` 状态，AI 在日常工作中缺少结构化对象可操作，也缺少工具辅助定位、校验和回写。

本文从 00 价值实现标准（V1-V10）、事实模型补齐、行动模型补齐、Tools 能力矩阵和 AI 协作优化五个视角，评估当前缺口和优先实施路线，供后续落地决策参考。

---

## 2. 结论

**LDVH 的核心瓶颈不在规范，在工具。** 当前 Tools 辅助层只有 5 个 Python 脚本，且全部集中在 specs 文档自查和 ADR 基础索引领域。12.01 定义的 8 项允许职责中，"上下文包生成"完全空白，"聚合"只有 specs 文档层面，"受控写入"只有 ADR 局部实现，"校验"缺少对象级字段和状态机校验。这导致 AI 每次进入项目都需要手动拼凑上下文，写入操作缺乏校验安全网，工程闭环在"工具辅助"环节断裂。

原建议优先实施路线：**规则上下文路由器 → Context Pack 生成器 → 通用对象校验框架 → 通用原子写入工具 → 事实模型补齐配套 → 行动模型配套 → Web 层**。其中前三项独立于事实模型/行动模型创建进度，可先行建设。

**2026-06-04 方向校准**：经 evals/17 视角复核、Gstack 实际实现调研和 Trae Skill 能力对比（见 §11-§13），原建议的"先建通用基础设施工具"路线与 evals/17 的"Core Loop 优先、按痛点扩展、防递归建设"原则存在结构性偏差。修正后的优先级见 §14。

---

## 3. 视角一：V1-V10 价值标准落地缺口

对照 `specs/00-LD-Vibe-Harness理念与纲要.md` §4.1 的 10 项价值实现标准，逐项看当前 Tools 支撑情况：

| 标准 | 当前状态 | 缺口 |
|---|---|---|
| V1 快速定位 | `check_03_01_specs_docs.py` 索引了 specs 文档。但**没有工具帮 AI 定位事实实例**（如"当前项目有哪些未关闭的 Task""有哪些 active ADR"） | 需要事实实例索引/查询工具 |
| V2 完整理解 | **没有任何上下文包生成工具**。AI 每次都要自己读取多个文件拼凑上下文，零散且不可复现 | 需要 Context Pack 生成器（最大单一缺口） |
| V3 正确判断 | 无工具辅助场景识别、风险判断或工具选择。**L1 规则要求 AI 根据任务类型和文件路径判断进入哪个规则层（L0/L1/L2）、读取哪些 specs 章节、触发哪些 Gate，但当前完全依赖 AI 每次手动推理** | 依赖行动模型落地 + 规则上下文路由器（Context Router），在关键节点嵌入工具调用 |
| V4 稳定执行 | Rules + Skill 有行为约束，但事实模型不全，缺少结构化对象 | 依赖事实模型 23-32 补齐 |
| V5 门禁识别 | Human Gate 规则在 L0/L1 中有提醒，但**无工具辅助判断**（如"当前操作是否触发 Human Gate"） | 受控写入工具中内置 HG 检查点 |
| V6 强制验证 | 仅有 specs 文档合规检查和 commit 格式检查。**缺少事实实例字段校验、状态机校验、跨对象引用完整性校验** | 需要通用对象校验框架（第二大单一缺口） |
| V7 证据沉淀 | 无工具辅助，完全依赖 AI 自觉 | 依赖 Evidence 事实模型 + 配套工具 |
| V8 可靠回写 | `adr_index.py` 有 ADR 原子写入能力。**但缺少通用多文件原子写入工具** | 需要通用原子写入工具 |
| V9 人类确认质量 | **Web 层完全未实现**，人无法看到项目态势 | Web 信息同步层需从零建设 |
| V10 持续完善 | 无模式识别/缺口发现工具 | 依赖审计行动模型 + Pitfall 事实模型 + 配套工具 |

---

## 4. 视角二：事实模型补齐（23-32）→ Tools 需求链

`specs/20-事实模型集合索引.md` 规划的 10 个事实模型中，只有 ADR(21) 和 Change(22) 已落地。8 个 `planned` 对象各自带出 Tools 需求：

| 事实模型 | 编号 | 需要的 Tools 解析/校验能力 |
|---|---|---|
| TaskSet | 23 | YAML 解析、字段校验、状态机校验、Task 聚合查询 |
| Intent | 24 | YAML 解析、与 TaskSet 的关联校验 |
| Memo | 25 | YAML 解析、转化规则校验（Memo→Task/Intent） |
| Risk | 26 | YAML 解析、关联对象校验 |
| Dependency | 27 | YAML 解析、依赖关系图校验 |
| Evidence | 28 | YAML/Markdown 解析、证据完整性校验、与 Task 关联校验 |
| Artifact | 29 | 引用完整性校验 |
| Checklist | 30 | 检查项完成状态校验 |
| Pitfall | 32 | YAML 解析、复用规则校验 |

**关键判断：不是每个事实模型都需要独立工具脚本。** 按 12.01 的设计理念，应构建**通用 YAML 事实实例解析/校验框架**，各对象通过 Contract 子文档（`NN.06-Contract.md`）声明字段契约，工具层统一读取 Contract 执行校验。避免为每个对象重复写解析逻辑。

当前 `adr_index.py` 中 ADR 的解析和校验逻辑可以作为通用框架的参考起点。

---

## 5. 视角三：行动模型补齐（52-60）→ Tools 参与节点

`specs/50-行动模型集合索引.md` 规划的 9 个行动模型全部是 `planned`。这些是 AI 日常工作的执行骨架，Tools 应在以下节点参与：

| 行动 | 编号 | Tools 参与方式 |
|---|---|---|
| 项目初始化 | 52 | 目录结构生成、初始文件模板写入 |
| 对话转需求 | 53 | 意图解析→Intent YAML 生成 |
| 需求转任务 | 54 | Intent→TaskSet→Task 拆解辅助、字段预填 |
| Task 执行 | 55 | 执行前：Context Pack 生成；执行后：Evidence 模板生成、状态流转校验 |
| Task 阻塞处理 | 56 | 阻塞分类、Risk/Dependency 关联提示 |
| Review 执行 | 57 | Checklist 校验、Evidence 完整性检查 |
| 项目审计 | 58 | **工具最能独立发力的场景**：聚合所有事实实例、识别缺口和风险、生成审计报告 |
| 对象创建 | 59 | 字段模板生成、准入条件校验、Human Gate 判断 |
| 对象状态更新 | 60 | 状态机校验、引用完整性检查、Change 记录自动生成 |

其中项目审计(58)是 Tools 可以最独立、最完整发挥价值的行动——聚合全部事实源、做确定性分析、输出结构化报告，不需要 AI 做大量判断。

---

## 6. 视角四：Tools 能力矩阵 — 当前 vs 需要

按 `specs/12.01-Tools辅助规范.md` §4 定义的 8 项允许职责，逐项评估：

| 职责 | 当前实现 | 需要补齐 |
|---|---|---|
| 读取 | `check_03_*` 读 specs；`adr_index.py` 读 ADR | **通用 YAML 事实实例读取器**（读取 `ldvh-base/` 下所有对象类型） |
| 解析 | specs Markdown + ADR YAML | **通用事实模型 YAML 解析器**（Contract 驱动，按对象类型解析字段） |
| 校验 | specs 文档质量、引用完整性；commit 格式；ADR 索引 | **对象字段校验**（Contract 驱动）、**状态机校验**（按状态迁移规则）、**跨对象引用校验**（如 Task→ADR→Change） |
| 聚合 | specs 文档索引聚合 | **项目态势聚合器**（聚合所有事实实例→给 AI 提供统一上下文，给 Web 提供派生数据） |
| 上下文包生成 | **无** | **Context Pack 生成器**（按场景生成 AI 最小可行动上下文，包含当前项目对象清单、状态、待确认事项和风险） |
| 派生数据生成 | 无 | 为 Web 信息同步层提供聚合数据 |
| 受控写入 | `adr_index.py` 有 ADR 原子写入（多文件 YAML + Change） | **通用原子写入工具**（多文件事务写入 + 写入前校验 + Change 记录自动生成） |
| 缺口报告 | specs 文档缺口 | **事实实例缺口报告**（哪些对象缺实例、哪些缺子文档）、**行动模型合规报告** |
| 规则路由 | **无** | **规则上下文路由器（Context Router）**：根据任务类型和目标文件路径，自动判断应进入的规则层（L0/L1/L2）、应读取的 specs 章节、是否触发 Human Gate、是否需要 ADR 检查、是否需要 Change 记录 |

---

## 7. 视角五：AI 协作优化关键路径

从"以 AI 执行者为第一服务对象"（00 §2）出发，AI 在每次会话中最需要的是：

1. **进入时**：快速知道项目有哪些事实对象、各自什么状态、有什么待处理事项
2. **执行时**：能校验自己的操作是否合法（字段是否对、状态能否流转）
3. **写入时**：有一个安全、可校验、多文件事务性的写入入口
4. **完成后**：能留下可追溯的证据和变更记录

对应 Tools 优先级：

### 7.1 P0 — 没有这些 AI 就是半盲

**规则上下文路由器（Context Router）** — AI 在进入任何任务前，需要知道当前任务触发哪些规则层、应读取哪些规范片段、是否触发 Human Gate。L1 规则（`ldvh-l1-rules.md`）的"入口"段要求 AI 先识别任务类型再按 00-20 读原文片段，L2 引导要求根据文件路径进入不同场景规则，但目前这些判断完全依赖 AI 每次手动推理。Context Router 应实现：

- 从文件路径识别项目上下文和场景类型（specs 编辑、Rules 编辑、事实实例编辑、ADR 操作、Tools 开发等）
- 输出需要加载的规则入口（L0/L1/L2）和生效方式
- 输出建议读取的 specs 文档与章节（按 L1 入口映射和 14 §6.1.1 读取精准原则）
- 输出 Human Gate 风险判断（是否可能触发 Gate、依据是什么）
- 输出 ADR 检查提醒和 Change 记录提醒

这是 L1 规则"入口→L2 引导"流程的机械化落地，也是 V3 的直接支撑。

**Context Pack 生成器** — AI 每次进入项目时自动获取当前项目态势。输出应包含：
- 项目基本信息（名称、路径）
- 事实对象清单（按类型分组，带状态）
- 待确认事项（Human Gate 等待项）
- 活跃风险和阻塞
- 最近变更摘要

这是 V1+V2 的直接落地，也是所有后续工具消费的统一入口。

**通用对象校验器** — AI 修改或创建 YAML 实例后可以立即验证：
- 字段是否符合 Contract 定义
- 状态流转是否合法
- 引用是否有效（如引用的 ADR 是否存在）
- 必填字段是否缺失

这是 V6 的直接落地，也是受控写入的前置条件。

### 7.2 P1 — 让闭环真正转起来

**通用原子写入工具** — AI 可以通过一个命令完成多文件事务写入，当前 `adr_index.py` 已部分实现（创建 ADR + 写 Change 记录），值得抽象为通用能力。应支持：
- 多文件写入的事务性（要么全成功，要么全回滚）
- 写入前调用校验器
- 自动生成 Change 记录
- Human Gate 判断

**项目态势聚合器** — 同时服务于 AI（上下文输入）和 Web（展示数据），是 V9 的前置条件。

### 7.3 P2 — 补齐事实模型后的配套

每个新事实模型落地后，在 Contract 子文档中定义字段契约，工具层统一消费。不需要为每个对象写独立工具。

### 7.4 P3 — 行动模型配套

行动模型落地后，在关键节点（执行前 Context Pack、执行后 Evidence 生成、状态流转时校验）嵌入工具调用。

### 7.5 P4 — Web 层

Web 信息同步层需要从零建设，但前提是 Tools 辅助层有了聚合和派生数据生成能力。

---

## 8. 当前 Tools 现状

`tools/` 目录下现有 5 个 Python 脚本，及对应的 `tests/tools/` 测试：

| 工具 | 功能 | 职责分类 |
|---|---|---|
| `check_03_01_specs_docs.py` | specs 文档质量诊断、规范合规检查 | 校验、聚合 |
| `check_03_specs_doc_standard.py` | 文档标准合规检查 | 校验 |
| `check_03_specs_references.py` | specs 文档引用完整性检查 | 校验 |
| `adr_index.py` | ADR 索引、校验、多文件原子写入 | 读取、解析、校验、受控写入 |
| `check_22_commit_format.py` | commit message 格式校验 | 校验 |

五个工具全部集中在 specs 自查和 ADR 基础能力领域，且全部通过 pytest 测试覆盖。

`web/` 目录不存在，Web 信息同步层零实现。

`ldvh-base/` 下只有 4 个 ADR 实例，没有其他事实类型的实例。

---

## 9. 建议实施优先级

```
第一优先级：规则上下文路由器 + Context Pack 生成器 + 通用对象校验框架
    （独立于事实模型/行动模型创建进度，可先行建设）
    ↓
第二优先级：通用原子写入工具
    （抽象 adr_index.py 的写入能力为通用层）
    ↓
第三优先级：事实模型 23-32 逐步补齐
    （每个对象创建时同步定义 Contract，工具层消费 Contract）
    ↓
第四优先级：行动模型 52-60 逐步补齐
    （在关键节点嵌入工具调用）
    ↓
第五优先级：Web 信息同步层
    （依赖 Tools 辅助层的聚合和派生数据能力）
    ↓
持续：Pitfall 沉淀 + 审计工具
    （V10 持续完善的落地载体）
```

---

## 10. 待补齐事项

1. 规则上下文路由器的场景分类规则表、输出格式和与 AI 上下文的对接方式待进一步设计；
2. Context Pack 生成器的具体输出格式、消费场景和与 AI 上下文的对接方式待进一步设计；
3. 通用对象校验框架的 Contract 消费方式、校验规则 DSL 和错误输出格式待定义；
4. 通用原子写入工具的事务性实现策略（Git 回滚 vs 预写校验）待评估；
5. 事实模型 23-32 的创建顺序和依赖关系待规划；
6. 行动模型 52-60 对 Tools 的调用契约（何时调用、传什么参数、如何消费输出）待定义；
7. Web 信息同步层的技术选型（框架、部署方式）待调研。

---

## 11. 与 evals/17 重构方向的对齐评估

> 本节基于 `specs/evals/17-LDVH-Gstack-Trae融合产品方向共识.md` 的视角，重新审视本文原建议的方向。

### 11.1 原建议与 evals/17 原则的偏差

| evals/17 原则 | 本文原建议 | 偏差判断 |
|---|---|---|
| Core Loop 优先 | 不以 Core Loop 组织优先级，而是以"工具能力矩阵"组织 | **偏差**：工具是手段不是目的，应服务于闭环 |
| 最小事实内核优先 | 为 10 个 planned 事实模型(23-32)全部规划了工具需求 | **偏差**：违反"按痛点启用"原则 |
| 按痛点扩展 | 预先规划了完整的 5 层工具体系 | **偏差**：典型的"为框架建框架" |
| 防递归建设 | P0 的 Context Router 和 Context Pack Generator 本身就是框架基础设施 | **偏差**：这些工具不直接服务最近一次可运行闭环 |
| 当前优先 Change/Record 闭环 | 完全未提及 Change/Record 闭环作为当前优先级 | **偏差**：错过了 evals/17 §8.1 的核心判断 |
| Gstack 提供体验范式而非实现模板 | 未分析 Gstack 如何解决同类问题 | **缺失**：缺少关键参照 |
| 先可解释后自动化 | 通用原子写入工具、通用对象校验器是高度自动化抽象 | **偏差**：跳过了"先人工可运行"阶段 |

### 11.2 原建议中仍有价值的部分

1. V1-V10 价值标准落地缺口分析（§3）是准确的诊断，缺口描述仍然成立；
2. 当前 Tools 现状盘点（§8）是事实性描述，仍有参考价值；
3. "不是每个事实模型都需要独立工具脚本"的判断正确；
4. Contract 驱动校验的方向正确；
5. 项目审计(58)是工具最能独立发力的场景，这个判断仍然成立；
6. 事实模型和行动模型对工具的需求链分析（§4、§5）作为长期参考仍有价值，但不应作为当前实施依据。

### 11.3 核心问题

本文原建议的诊断（工具不够）是准确的，但药方（建通用基础设施工具）开错了。正确药方是 evals/17 的"流程内嵌正确行为"——让 Skill 指令告诉 AI 进入时读什么、执行时校验什么、写入时遵循什么，而非先建独立工具再让 AI 使用工具。

---

## 12. Gstack 实际解决方案调研

> 本节基于 `/Users/dmh2002/trae_projects/gstack` 代码调研，分析 Gstack 如何解决本文 §7 识别的同类问题。

### 12.1 Gstack 的核心策略

Gstack 的核心策略是：**把上下文生成和校验嵌入 Skill 模板，而非构建独立基础设施工具。**

Gstack 不建 Context Router、Context Pack Generator、Universal Object Validator 或 Universal Atomic Write Tool。它用 Resolver 系统 + Skill 模板 + Schema Pack 三层机制，在构建时将动态上下文烘焙进 Skill 提示词，在运行时让 AI 按 Skill 指令执行。

### 12.2 上下文路由：Skill 触发声明 + 约定匹配

Gstack 不建 Context Router。每个 SKILL.md 通过 `triggers` 和 `allowed-tools` 元数据声明自己的适用场景：

```yaml
triggers:
  - unfreeze edits
  - unlock all directories
allowed-tools:
  - Bash
  - Read
```

AI（Claude Code）根据用户意图匹配 trigger，不需要额外路由工具。路由机制是 AI 的语义匹配能力 + Skill 的 description 声明，不是独立工具。

**LDVH 对应物**：L0/L1 Rules 的入口路由已经在做这件事，只是还没产品化为 Skill 触发声明。

### 12.3 上下文包：Resolver 系统嵌入 Skill 模板

Gstack 不建 Context Pack Generator。它用 `{{PLACEHOLDER}}` 模板变量 + Resolver 函数系统，在构建时将上下文注入 Skill 提示词：

- `{{PREAMBLE}}` → 注入写作风格、完成状态、上下文健康
- `{{LEARNINGS_SEARCH}}` → 注入历史 learnings 搜索命令
- `{{BRAIN_PREFLIGHT}}` → 注入 brain 缓存摘要
- `{{REVIEW_DASHBOARD}}` → 注入 review 仪表板
- `{{SCOPE_DRIFT}}` → 注入 scope drift 检测

每个 Resolver 是一个轻量函数（`scripts/resolvers/` 下约 40 个），按需组合，不是统一基础设施。Resolver 的核心接口：

```typescript
type ResolverFn = (ctx: TemplateContext, args?: string[]) => string;
```

`TemplateContext` 包含 `skillName`、`host`、`paths`、`preambleTier` 等字段，Resolver 根据上下文生成不同内容。

**LDVH 对应物**：Skill 提示词中应嵌入场景相关的上下文生成逻辑（"必读文件"段），而非依赖外部 Context Pack 工具。当前 ldvh-intake、ldvh-close 的"必读文件"段已经是运行时等价方案。

### 12.4 校验：Schema Pack + AI 遵循指令

Gstack 不建 Universal Object Validator。它用 `gstack-schema-pack.ts` 定义类型化页面结构（field shape、required、enum values），但运行时校验由 AI 按 Skill 指令执行，不是独立校验工具。

Schema Pack 定义了 8 种页面类型（user-profile、product、goal、developer-persona、brand、competitive-intel、skill-run、take），每种包含字段定义、保留策略和链接关系。Schema Pack 更像"给 AI 的字段契约参考"，而非运行时校验器。

**LDVH 对应物**：Contract 子文档已经在做这件事——定义字段契约供 AI 和 PyTools 消费。`check_fact_model.py` 已经是最小校验实现，不需要先建通用框架再校验。

### 12.5 写入：Skill 内嵌 bash 命令

Gstack 不建 Universal Atomic Write Tool。写入操作直接嵌入 Skill 模板的 bash 命令中：

- `gbrain put "<slug>" --content "..."` — 写入 brain
- 普通 bash 文件写入 — 写入项目文件
- 无事务机制，靠 Skill 指令保证顺序

**LDVH 对应物**：`adr_index.py` 已有 ADR 原子写入能力。按痛点逐步扩展，不需要先抽象通用层。

### 12.6 项目态势聚合：Brain Preflight + Learnings

Gstack 不建 Project Status Aggregator。它用两个嵌入式机制：

- **Brain Preflight**：在规划类 Skill 执行前，加载缓存的 brain 摘要（product、goal、persona 等），每个摘要由 `gstack-brain-cache get` 获取
- **Learnings Search**：搜索历史 `learnings.jsonl`，按 key+type 去重，"latest winner"策略

两者都嵌入 Skill 模板，不是独立聚合工具。

**LDVH 对应物**：ldvh-close 和 ldvh-intake 已在 Skill 层面做上下文聚合，不需要独立聚合器。

### 12.7 Gstack 方法论总结

Gstack 的方法论是"使用即流程"——正确行为成为 AI 默认路径，而不是先建工具再让 AI 使用工具。这对应 evals/17 §3.1 共识三中的第 3 条："使用即流程：正确行为应成为 AI 默认路径，而不是只写在规范里。"

但 Gstack 的 Resolver 系统有一个关键特性：它把上下文获取的摩擦降到了零。AI 进入 Skill 时，相关上下文已经在提示词中，不需要额外操作。这与 Trae 的运行时获取模式存在摩擦差异：

| 方式 | AI 需要做什么 | 摩擦 |
|---|---|---|
| Gstack Resolver | 什么都不用做，上下文已在提示词中 | 零 |
| Trae "必读文件" | 读 4-6 个文件，自己拼凑上下文 | 高 |
| Trae 上下文工具 | 调一次工具，拿到结构化上下文 | 低 |

Gstack 的构建时烘焙在 Trae 环境中无法实现（Trae Skill 是纯静态 Markdown，无模板变量机制）。但 Trae 可以用**运行时工具调用**达到同等效果——AI 进入 Skill 时调一次 `ldvh-context` 工具，拿到结构化上下文，而不是自己读多个文件拼凑。

这意味着：一个轻量的上下文获取 PyTool（如 `ldvh-context`），本质上是 **Trae 原生的 Resolver 等价物**。它不是 evals/12 原建议的"通用基础设施工具"，而是 Gstack Resolver 在 Trae 环境中的自然映射。

---

## 13. Trae Skill 能力对比

> 本节基于 Trae 官方文档和实际 Skill 文件调研，评估 Trae Skill 是否具备实现 Gstack 体验范式的能力。

### 13.1 核心架构对比

| 能力维度 | Gstack | Trae Skill | 差距判断 |
|---|---|---|---|
| 上下文动态生成 | Resolver 系统，构建时将 `{{PLACEHOLDER}}` 替换为动态内容 | 无。SKILL.md 是纯静态文档 | 有差距，但有运行时等价方案 |
| 模板变量 | 40+ Resolver（LEARNINGS_SEARCH、BRAIN_PREFLIGHT、REVIEW_DASHBOARD 等） | 无等价机制 | 有差距 |
| 持久化知识 | gbrain（知识图谱）+ learnings.jsonl（跨会话经验） | Memory 系统（独立于 Skill） | 部分等价 |
| Schema 校验 | schema-pack 定义类型化页面结构 | 无内置机制，靠 AI 遵循指令或 PyTools | 有差距 |
| Skill 路由 | `triggers` + `description` 语义匹配 | `description` + `trigger_keywords` 语义匹配 | 基本等价 |
| 宿主适配 | 多宿主配置（Claude Code、Codex 等） | 单宿主（Trae） | 无需（LDVH 只用 Trae） |
| 运行时命令 | Skill 内嵌 bash 命令 | Skill 指令引导 AI 使用 RunCommand | 等价 |
| Human Gate | AskUserQuestion decision brief | AskUserQuestion | 等价 |
| 外部脚本 | Skill 文件夹可含 bin/ 脚本 | Skill 文件夹可含 Python/Bash 脚本 | 等价 |

### 13.2 关键差距详解

**差距 1：无动态上下文注入**

Gstack 的 Resolver 系统在构建时将动态上下文烘焙进 Skill 提示词。Trae Skill 没有构建时变量替换，每个 SKILL.md 是纯静态 Markdown。

LDVH 当前用"必读文件"段作为运行时等价方案：AI 按 Skill 指令读取多个文件，自己拼凑上下文。这在**功能上等价**，但在**摩擦上不等价**——AI 每次要读 4-6 个文件、自己拼凑、可能遗漏，这正是 Gstack 用 Resolver 消除的摩擦。

Trae 的原生解法是**运行时工具调用**：AI 进入 Skill 时调一次轻量 PyTool（如 `ldvh-context --scene intake`），拿到结构化上下文。一次调用替代多次文件读取，摩擦从"高"降到"低"。这个 PyTool 本质上是 Gstack Resolver 在 Trae 环境中的自然映射，不是"通用基础设施工具"，而是"Trae 原生 Resolver 等价物"。

**差距 2：无 Schema Pack**

Gstack 用 schema-pack 定义类型化页面结构，AI 按 schema 生成/校验数据。Trae Skill 无内置等价物。

LDVH 的等价方案：Contract 子文档（`NN.06-Contract.md`）+ `check_fact_model.py`。Contract 定义字段契约，PyTools 消费 Contract 做校验。这比 Gstack 的 schema-pack 更正式（Git 文件事实源），但运行时自动化程度更低。

**差距 3：无持久化知识集成**

Gstack 的 gbrain 是与 Skill 深度集成的持久化知识图谱。Trae 的 Memory 是独立机制，Skill 无法声明式引用 Memory 内容。

LDVH 的等价方案：Git 文件事实源（`ldvh-base/`）+ Skill 指令引导 AI 读取。比 gbrain 更持久（Git 可追溯），但缺少语义搜索能力。

### 13.3 Trae 官方 Skill 最佳实践要点

> 本节基于 Trae 官方文档 `https://docs.trae.cn/ide/best-practice-for-how-to-write-a-good-skill` 提炼。

#### 13.3.1 五个核心标准

| 标准 | 描述 | 对 LDVH 的启示 |
|---|---|---|
| 边界明确 | 正向条件 + 负向条件，否则命中率低 | LDVH Skill 的"触发条件"和"不适用场景"段符合此标准 |
| 输入输出结构化 | 用函数签名式定义 Input/Output | LDVH Skill 的"输出格式"段部分符合，但缺少 Input 定义 |
| 步骤明确可执行 | 指令式具体动作，不是概括性描述 | LDVH Skill 的"编排流程"段基本符合 |
| 失败策略完备 | 明确失败路径，不让模型自由发挥 | LDVH Skill 有部分失败策略，但不够系统化 |
| 职责绝对单一 | 每个 Skill 只做一件事 | LDVH 当前 Skill 符合（intake/close/commit/adr 各一个） |

#### 13.3.2 指导方式三级自由度

| 自由度 | 适用场景 | 指导方式 | LDVH 对应 |
|---|---|---|---|
| 高 | 存在多种有效方法 | 给原则 | 代码审查、技术方案评估 |
| 中 | 存在首选模式，允许变通 | 给框架/模板 | 报告生成、Evidence 草案 |
| 低 | 操作脆弱易错，一致性至关重要 | 给可执行脚本 | ADR 创建（adr_index.py）、commit 格式校验 |

LDVH 当前 Skill 主要用中自由度（给框架），但 ADR 和 commit 相关操作已经用低自由度（给脚本）。后续 ldvh-context 也应采用低自由度——给可执行脚本，让 AI 调用而非自行拼凑。

#### 13.3.3 渐进式披露

Trae 官方明确推荐：

1. SKILL.md 主体 ≤ 500 行，只含必要信息
2. 详细内容拆到引用文件，保持一层引用深度（避免 A→B→C 链式引用）
3. 长文件加目录

**这是 Gstack 没有但 Trae 官方明确推荐的实践**，对 LDVH 有直接指导意义：

- LDVH 当前 Skill 的"必读文件"段让 AI 读 4-6 个规范文件，这些文件本身又引用其他文件，容易形成链式引用
- 更好的做法：SKILL.md 只引用最必要的 1-2 个文件（如 Contract），其余上下文由 `ldvh-context` 工具聚合后一次性提供
- 这进一步验证了 `ldvh-context` 的必要性：它不仅是 Resolver 等价物，还是渐进式披露的"引用文件层"——AI 不需要自己读多个文件，工具已经聚合好了

#### 13.3.4 评测驱动、失败优先的构建流程

Trae 官方推荐的 Skill 构建流程：

1. 建"无 Skill"基线，识别真实问题
2. 以失败优先定义评测用例
3. 写最小化 Skill，只通过当前评测
4. 补充边界条件与结构化示例
5. 评测回归与持续迭代
6. 结合真实使用路径校准

**这与 evals/17 的"防递归建设"原则高度一致**：

- "无 Skill 基线" ≈ "先人工可运行，再工具自动化"
- "失败优先" ≈ "碰到什么问题补什么能力"
- "最小化 Skill" ≈ "只补当前闭环的最小缺口"
- "评测回归" ≈ "Dogfood 优先于继续抽象"

对 LDVH 的启示：每个新 Skill（ldvh-plan、ldvh-verify、ldvh-context）都应先跑"无 Skill 基线"，识别真实摩擦点，再写最小化 Skill。

#### 13.3.5 可执行脚本加固原则

Trae 官方对 Skill 中引用的脚本提出三个要求：

1. **错误显式处理**：捕获常见异常，返回清晰错误原因和下一步建议，不让模型猜
2. **输出自解释**：成功/失败路径都有明确输出，验证类脚本列出通过项与失败项
3. **避免魔法数字**：常量有语义化名称和设计依据

对 LDVH PyTools 的启示：`check_fact_model.py`、`adr_index.py` 和未来的 `ldvh-context` 都应遵循这些原则，确保输出对 AI 可理解、可决策。

### 13.4 Trae Skill 能做到但 Gstack 做不到的

| 能力 | 说明 |
|---|---|
| Plan / Spec 模式 | Trae 有内置的 Plan 和 Spec 模式，Gstack 没有 |
| Schedule 定时任务 | Trae 有 Schedule 机制，Gstack 无等价物 |
| Agent 子代理 | Trae 有 Task 工具启动子 Agent，Gstack 的 Skill 是单体 |
| Web Preview | Trae 有内置 Web 预览，Gstack 靠 browse daemon |
| Memory 跨会话 | Trae Memory 是平台级能力，Gstack 靠 gbrain |

### 13.5 对 LDVH 的影响判断

**核心结论：Trae Skill 具备实现 Gstack 体验范式的基本能力，但缺少构建时动态注入的"糖衣"。Trae 官方最佳实践提供了 Gstack 没有的工程化指导（渐进式披露、评测驱动迭代、脚本加固），LDVH 应同时吸收 Gstack 的体验范式和 Trae 的工程实践。**

1. **上下文路由**：Trae Skill 的 `description` 语义匹配 ≈ Gstack 的 `triggers`。LDVH 不需要建 Context Router 工具，现有 L0/L1 Rules 入口 + Skill description 已经在做路由。
2. **上下文包**：Trae Skill 无法构建时烘焙动态上下文，"必读文件"段功能等价但摩擦高（AI 需读多个文件自己拼凑）。当摩擦明显时，应建轻量 `ldvh-context` PyTool 作为 Trae 原生 Resolver 等价物——一次调用拿到结构化上下文，替代多次文件读取。这不是"通用基础设施"，而是 Gstack Resolver 在 Trae 中的自然映射。Trae 官方的渐进式披露原则进一步验证了这一点：`ldvh-context` 是"引用文件层"的聚合，避免 AI 自己读多个文件形成链式引用。
3. **校验**：Trae Skill 无法内嵌 schema-pack，但可以调用 PyTools。`check_fact_model.py` 已经是最小实现。不需要建通用对象校验框架——按痛点逐对象扩展即可。
4. **写入**：Trae Skill 可以引导 AI 用 RunCommand 执行写入脚本。`adr_index.py` 已有原子写入。不需要建通用原子写入工具——按痛点扩展。
5. **聚合**：`ldvh-context` 可同时承担聚合职责（按场景返回项目态势），不需要独立项目态势聚合器。
6. **工程实践**：Trae 官方的"评测驱动、失败优先"构建流程与 evals/17 的"防递归建设"高度一致，LDVH 应将其作为 Skill 和 PyTools 开发的标准流程。每个新 Skill/工具都应先跑"无 Skill 基线"识别真实摩擦，再写最小化实现。

---

## 14. 修正后的优先级

> 本节基于 §11-§13 的分析，修正 §9 的原建议优先级，使其与 evals/17 方向对齐。

### 14.1 修正原则

1. **Core Loop 优先**：优先级以 Core Loop 阶段组织，不以工具能力矩阵组织
2. **最小事实内核优先**：只补当前闭环需要的对象，不为 planned 对象预建工具
3. **按痛点扩展**：碰到什么问题补什么能力，不预先规划完整工具体系
4. **防递归建设**：每次新增能力必须服务最近一次可运行闭环
5. **先可解释后自动化**：先让 AI 按 Skill 指令手动跑通，再考虑 PyTools 自动化
6. **Trae 原生 Resolver 等价**：Gstack 用构建时 Resolver 零摩擦注入上下文，Trae 用运行时 PyTool 调用低摩擦获取上下文，两者是同一问题的两种解法；当"必读文件"摩擦明显时，应建轻量上下文获取工具

### 14.2 修正后优先级

```
第一优先级：Change/Record 闭环（evals/17 §8.1 已明确）
    → ldvh-commit + ldvh-close 消费 Task/Evidence/ADR 信息
    → 不需要新建工具，强化现有 Skill 即可
    → Change 暂以 Git commit message 为主承载

第二优先级：Core Loop Skill 补齐 + 上下文获取工具
    → ldvh-plan：围绕 Task 形成执行计划、风险、验证命令
    → ldvh-verify：统一 lint/test/build/真实交互验证和 Evidence 草案
    → ldvh-context：Trae 原生 Resolver 等价物，按场景返回结构化上下文
      · 当"必读文件"摩擦明显时建设（AI 需读多个文件拼凑上下文时）
      · 不是通用基础设施，是 Gstack Resolver 在 Trae 中的自然映射
      · 同时承担项目态势聚合职责，不需要独立聚合器
      · 先服务 intake/close 场景，再扩展到 plan/verify
      · 遵循 Trae 官方渐进式披露原则：SKILL.md 只引用最必要的 1-2 个文件，其余由工具聚合
      · 遵循 Trae 官方脚本加固原则：错误显式处理、输出自解释、避免魔法数字
      · 遵循"评测驱动、失败优先"：先跑无工具基线识别摩擦，再写最小化实现
    → 不需要独立 Context Router（Skill description + Rules 入口已做路由）

第三优先级：PyTools 按痛点扩展
    → check_fact_model.py 逐步消费更多 Contract
    → 不需要先建通用框架
    → 碰到什么对象补什么校验
    → 旧工具按触碰即整理原则迁移

第四优先级：Web 只读态势
    → 消费 PyTools 输出（含 ldvh-context 聚合数据）
    → 不需要独立聚合器
    → 定位：Git 文件事实源 → PyTools 聚合 → Web 只读展示 → 人做更高质量 Human Gate

持续：Pitfall 沉淀 + 审计工具
    → V10 持续完善的落地载体
    → 项目审计(58)仍是工具最能独立发力的场景
```

### 14.3 原建议中各工具的修正处置

| 原建议工具 | 修正处置 | 理由 |
|---|---|---|
| 规则上下文路由器 | **不建**。L0/L1 Rules 入口 + Skill description 已在做路由 | Trae Skill 的 description 语义匹配 ≈ Gstack triggers，不需要独立工具 |
| Context Pack 生成器 | **降级为按痛点建设**。当"必读文件"摩擦明显时，建轻量 `ldvh-context` PyTool | Gstack 用 Resolver 构建时零摩擦注入，Trae 用运行时工具调用低摩擦获取，两者是同一问题的两种解法；`ldvh-context` 是 Trae 原生 Resolver 等价物，不是通用基础设施 |
| 通用对象校验框架 | **不建**。check_fact_model.py 按痛点逐对象扩展 | 防递归：先让 AI 按 Contract 手动校验，痛点明确后再自动化 |
| 通用原子写入工具 | **不建**。adr_index.py 按痛点扩展 | 先让 AI 按 Skill 指令 + PyTools 手动跑通，再考虑抽象 |
| 项目态势聚合器 | **合并到 ldvh-context**。按场景返回项目态势，不需要独立聚合器 | `ldvh-context --scene intake` 可同时返回对象清单、状态、待确认事项 |

### 14.4 与原建议的关系

原建议 §3-§7 的诊断（V1-V10 缺口、事实模型工具需求链、行动模型参与节点、Tools 能力矩阵、AI 协作关键路径）仍然成立，作为长期参考保留。

原建议 §9 的优先级被本节取代。核心变化是：从"先建通用基础设施工具"转向"先跑通 Core Loop 闭环，按痛点扩展 PyTools 和 Skill"。其中 Context Pack 生成器从"不建"修正为"降级为按痛点建设"——当"必读文件"摩擦明显时，建轻量 `ldvh-context` PyTool 作为 Trae 原生 Resolver 等价物，同时承担项目态势聚合职责。