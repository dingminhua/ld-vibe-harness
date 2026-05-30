# LD Vibe Harness 自建 MCP 评估

> 创建日期：2026-05-30
> 状态：内部调研
> 编号归属：70-89 内部调研
> 调研边界：不直接构成强制规则
> 执行效力：无，结论需进入 01-69 正式规范区间或 ADR 后才成为稳定规则
> 上位依据：`specs/00-LD-Vibe-Harness理念与纲要.md`
> 相关规范：`specs/03-事实源边界与承载规范.md`、`specs/04-LDVH-AI协作规范.md`、`specs/05-LDVH工具基础规范.md`、`specs/05.01-Tools辅助规范.md`、`specs/07-LDVH行动模型基础规范.md`
> 参考来源：`specs/refs/02-Trae-MCP用法调研.md`、`specs/evals/06-LDVH的MCP使用评估.md`

---

## 一、本文解决的问题与结论

本文评估 LD Vibe Harness 是否需要自建 MCP Server，以及如果需要，应自建哪些 MCP Server、如何与 05 工具层和 07 行动模型衔接、如何实施、如何控制风险。

本文所说的自建 MCP，指 LDVH 自行开发、部署在项目本地、通过 Trae MCP 协议供 Agent 调用的本地 MCP Server。它面向 LDVH 特有的结构化事实源读取、校验、聚合、上下文包生成和受控写入能力。

本文是内部调研，不直接构成强制规则；调研结论进入 01-69 正式规范区间或 ADR 后才成为稳定规则。

### 1.1 核心结论

LDVH 可以考虑自建 MCP，但自建 MCP 不应成为新的工具层，也不应替代 tools/ Tools 辅助层。它更准确的定位是：

```text
自建 MCP = 05.01 Tools 辅助层面向 Agent 的协议入口
```

因此，自建 MCP 应遵循以下结论：

1. 通用能力使用第三方 MCP，不自建；
2. LDVH 特有语义能力在满足准入条件后可自建；
3. 自建 MCP 只做协议适配和结构化返回，不重新实现业务逻辑；
4. 底层解析、校验、聚合、上下文包和写入能力优先复用 tools/；
5. 自建 MCP 不维护独立权威数据存储；
6. MCP 输出是派生视图、校验结果或上下文包，不是最终事实源；
7. 写入型 MCP 风险最高，应最后实现，并必须受 Human Gate 和状态机约束。

### 1.2 建议优先级

| 优先级 | MCP | 建议 |
|---|---|---|
| 第一优先级 | Fact Reader、Status Aggregator | 先实现只读能力，帮助 Agent 稳定读取事实源和识别项目状态 |
| 第二优先级 | Context Pack、Validator | 在只读能力稳定后，实现上下文包生成和主动校验能力 |
| 第三优先级 | Controlled Writer | 最后实现，并必须依赖成熟的校验、门禁、写入后验证和 Change 记录机制 |

---

## 二、为什么考虑自建 MCP

### 2.1 第三方 MCP 的能力缺口

第三方 MCP 适合提供通用能力，例如复杂推理、外部文档查询和浏览器自动化，但无法理解 LDVH 自身的对象结构、字段契约、状态机和事实源边界。

| LDVH 需求 | 第三方 MCP 能否覆盖 | 缺口说明 |
|---|---|---|
| 读取 `ldvh-base/` 中的生产对象实例 | 否 | 第三方 MCP 不理解 LDVH 对象结构、字段契约和状态机 |
| 校验生产对象字段和状态合法性 | 否 | 校验规则由 10-39 生产对象规范定义，第三方 MCP 不掌握 |
| 聚合项目状态 | 否 | 阻塞视图、待验收视图等依赖 LDVH 目录结构和对象关系 |
| 生成最小可行动上下文包 | 否 | 上下文包由 07 行动模型中的 Context 组件定义 |
| 受控写入 `ldvh-base/` | 否 | 写入必须经过校验、Human Gate 判断和 Change 记录 |
| 查询 specs 规范体系结构 | 否 | specs 编号分区、文档类型和引用纪律是 LDVH 特有规则 |

### 2.2 Trae 内置工具的能力缺口

Trae 内置工具可以读写文件、运行终端命令和搜索文本，但它们主要处理文件级或文本级操作，不能自动保证 LDVH 结构化语义正确。

| LDVH 需求 | Trae 内置工具能否覆盖 | 缺口说明 |
|---|---|---|
| 按 Task 状态筛选 | 部分 | 可以 grep YAML 字段，但无法保证语义正确和状态机合法 |
| 检查对象引用完整性 | 否 | 需要理解对象间关系，不是简单文本搜索 |
| 生成上下文包 | 部分 | 可以读取多个文件拼接，但无法保证最小化和结构化 |
| 受控写入前校验 | 否 | 内置文件工具不校验对象格式、引用和状态流转 |
| 聚合项目视图 | 部分 | 可以临时写脚本聚合，但不稳定、不可复用、无统一输出契约 |

### 2.3 自建 MCP 的核心价值

自建 MCP 的价值不是增加工具数量，而是把 05.01 Tools 辅助层的确定性能力，通过 MCP 协议暴露为 Agent 可调用的结构化工具，让 Agent 不需要理解底层文件格式和校验逻辑，也能完成事实源读取、校验、聚合和受控写入。

这与 03 Agent-Harness 评估中的启发一致：把工具调用纳入治理，而不是追求更多工具。

---

## 三、自建 MCP 的准入判断

### 3.1 触发条件

LDVH 不因存在 Python 程序就自建 MCP，也不因某项能力会被 AI 使用就自建 MCP。只有当某项 LDVH 特有的 Tools 辅助能力需要被 Agent 长期、结构化、权限受控地调用，且第三方 MCP、Trae 内置工具、CLI、Skill 或 Web API 都不足以覆盖时，才应考虑自建 MCP。

应考虑自建 MCP 的条件如下：

| 条件 | 判断标准 |
|---|---|
| LDVH 特有语义 | 能力依赖 LDVH 的对象结构、字段契约、状态机、目录边界或行动模型 |
| 第三方 MCP 不可覆盖 | 通用 MCP 无法理解或安全执行该能力 |
| 内置工具语义不足 | Trae 文件、终端、搜索等内置工具只能完成文本级操作，无法保证语义正确 |
| Agent 高频调用 | 多个 Agent 或长期流程需要重复调用该能力 |
| 结构化输入输出 | 能力可以表达为稳定参数、结构化响应和来源引用 |
| 权限最小化价值 | MCP 化后可以减少 Agent 直接访问文件系统、终端或写入能力的范围 |
| 事实源可追溯 | 输出可以追溯到 Git 文件事实源，且不会形成第二事实源 |
| 底层能力可复用 | 底层解析、校验、聚合或写入逻辑优先来自 tools/ Tools 辅助层 |

### 3.2 不应自建 MCP 的情况

以下情况不应自建 MCP：

1. 只是一次性脚本或临时调试命令；
2. 只是为了让 Python 程序“看起来更智能”；
3. CLI 已足够简单且权限风险可控；
4. Skill 已能稳定编排该流程；
5. Web API 更适合人查看、确认或编辑；
6. 第三方 MCP 已能安全覆盖；
7. 底层对象规范、字段契约或状态机尚未稳定；
8. 自建 MCP 会重新实现一套与 tools/ 重复的业务逻辑；
9. 自建 MCP 需要维护独立权威数据存储；
10. MCP 输出无法追溯到 Git 文件事实源。

---

## 四、自建 MCP 与 05 工具层的关系

### 4.1 自建 MCP 是Tools 辅助层入口，不是替代层

自建 MCP Server 不是新的工具层，而是 05.01 Tools 辅助层面向 Agent 的协议接口：

```text
Tools 辅助层（tools/）
  ├── CLI 入口：供人、AI 或脚本通过终端直接调用
  ├── Skill 流程入口：供 Skill 在授权流程中调用确定性程序
  ├── Web API 入口：供 05.02 Web 展示层调用
  └── MCP 入口：供 Agent 通过 Trae MCP 协议结构化调用
```

这意味着：

1. 自建 MCP 的底层逻辑应复用 tools/ 中的解析、校验、聚合和受控写入模块；
2. 自建 MCP 不另建权威数据存储，所有读写仍指向 Git 文件事实源；
3. 自建 MCP 的输出与 Tools 辅助层输出一样，不是最终事实源；
4. MCP 入口层只做协议适配，不实现业务逻辑，不维护状态，不存储数据。

### 4.2 自建 MCP 不改变 05 工具边界

自建 MCP 引入后，05 工具基础规范的约束仍然适用：

1. MCP 工具输出不是最终事实源；
2. MCP 工具不得绕过Tools 辅助层的校验和受控写入边界；
3. MCP 工具不得直接调用 AI、Skill 或 Agent；
4. MCP 工具不得替代 specs/、ldvh-base/ 或 docs/ 的权威事实。

### 4.3 Python 程序是否 MCP 化的判断

Python 程序属于 05.01 Tools 辅助层的能力实现。MCP 是其中一种面向 Agent 的协议入口，不是 Python 程序的唯一调用方式。

| 入口 | 适用场景 | 边界 |
|---|---|---|
| CLI | 本地开发、一次性检查、简单校验、AI 临时调用 | 依赖命令参数和执行上下文，适合轻量使用 |
| Skill 流程入口 | 可复用多步骤流程中的确定性步骤 | Skill 负责编排，Python 只执行确定性程序逻辑 |
| Web API | 人需要查看、确认、编辑或验收的场景 | Web 展示层负责人机交互，不成为事实源 |
| MCP | Agent 长期、结构化、权限受控地调用工具能力 | MCP 只做协议适配和结构化返回，不实现业务逻辑 |

某个 Python 程序是否需要 MCP 化，应至少满足以下一项：

1. Agent 需要长期、稳定、重复调用；
2. 需要以结构化工具参数替代自由命令行参数；
3. 需要按 Agent 配置最小化权限；
4. 需要返回稳定结构化结果并附带来源引用；
5. 需要降低 Agent 直接读写文件或执行任意命令的风险；
6. 需要作为多 Agent 或专业 Agent 的共享工具能力。

---

## 五、候选自建 MCP 评估

### 5.1 候选能力总览

| MCP | 定位 | 核心工具 | 价值 | 风险 | 优先级 |
|---|---|---|---|---|---|
| Fact Reader | 结构化读取事实源 | `read_task`、`list_tasks`、`read_adr`、`read_memo`、`read_change`、`read_pitfall` | 降低 Agent 组装上下文成本 | 低 | 第一优先级 |
| Status Aggregator | 聚合项目状态视图 | `blocked_tasks`、`review_needed_tasks`、`decision_needed`、`project_summary`、`intent_progress` | 帮助 Agent 快速识别工作入口 | 低 | 第一优先级 |
| Context Pack | 生成最小可行动上下文包 | `task_context`、`decision_context`、`review_context`、`change_context` | 直接支撑 07 Context 组件 | 中 | 第二优先级 |
| Validator | 校验生产对象合法性 | `validate_task`、`validate_change`、`validate_state_transition`、`check_references` | 支撑 Gate 判断和写入前检查 | 中 | 第二优先级 |
| Controlled Writer | 受控写入 `ldvh-base/` | `create_task`、`update_task_status`、`create_change`、`create_memo`、`create_pitfall` | 降低直接写文件风险 | 高 | 第三优先级 |

### 5.2 Fact Reader MCP

Fact Reader MCP 为 Agent 提供结构化事实源读取能力。它按对象类型和 ID 读取 `ldvh-base/` 中的生产对象实例，并返回字段、状态、来源引用等结构化结果。

它直接支撑 07 行动模型中的 Context 组件。Agent 可通过 Fact Reader 快速组装最小可行动上下文，而不是逐文件读取和手动解析 YAML。

事实源约束：只读；输出是 Git 文件事实源的结构化视图，不是独立事实源。

### 5.3 Status Aggregator MCP

Status Aggregator MCP 为 Agent 提供项目状态聚合视图，包括阻塞任务、待验收任务、待决策事项、项目状态摘要和 Intent 进度。

它直接支撑 07 行动模型中的 Scenario 识别。Agent 可通过聚合视图判断当前应进入阻塞处理、Review、需求规划还是任务执行场景。

事实源约束：只读；输出是派生视图，不是事实源；聚合结果必须可追溯到 Git 文件事实源。

### 5.4 Context Pack MCP

Context Pack MCP 为 Agent 生成最小可行动上下文包。典型工具包括任务上下文、决策上下文、Review 上下文和变更上下文。

它把 Fact Reader 和 Status Aggregator 的输出进一步组织为面向行动的上下文包，减少 Agent 自行拼装多个对象和文件的负担。

事实源约束：只读；输出是派生上下文，不是事实源；上下文中新出现的稳定信息如需长期保留，应重新判断对象类型和事实源载体。

### 5.5 Validator MCP

Validator MCP 为 Agent 提供生产对象校验能力，包括字段完整性、状态合法性、状态流转和引用完整性校验。

它支撑 07 行动模型中的 Gate 判断。Agent 可在关键操作前主动校验，减少非法状态流转、引用缺失和格式错误。

事实源约束：只读；校验结果是派生信息，不是事实源；校验失败不得自动修改事实源。

### 5.6 Controlled Writer MCP

Controlled Writer MCP 为 Agent 提供受控写入 `ldvh-base/` 的能力，包括创建 Task、更新 Task 状态、创建 Change、创建 Memo 和创建 Pitfall。

它价值高，但风险最高。写入能力如果绕过 Human Gate、状态机校验或 Change 记录，将直接破坏事实源完整性。

事实源约束：写入目标必须是 Git 文件事实源；写入前必须校验；写入后必须验证并可通过 Git 追溯；关键写入必须触发 Human Gate；写入结果不得只停留在 MCP 响应中。

---

## 六、实现路径

### 6.1 技术选型建议

| 维度 | 建议 | 理由 |
|---|---|---|
| 传输方式 | stdio | LDVH 是本地项目，不需要远程访问；stdio 简单且权限面较小 |
| 运行方式 | 通过 `npx` 或 `uvx` 启动 | 与 Trae 本地 MCP 启动方式一致 |
| 编程语言 | Python | 与 tools/ Tools 辅助层一致，便于复用解析、校验、聚合模块 |
| 配置位置 | `.trae/mcp.json` 项目级配置 | 符合 Trae 项目级 MCP 配置方式，配置跟随项目 |

### 6.2 配置示例

```json
{
  "mcpServers": {
    "ldvh-fact-reader": {
      "command": "uvx",
      "args": ["ldvh-mcp-fact-reader"],
      "env": {
        "LDVH_BASE": "${workspaceFolder}/ldvh-base",
        "LDVH_SPECS": "${workspaceFolder}/specs"
      }
    },
    "ldvh-status-aggregator": {
      "command": "uvx",
      "args": ["ldvh-mcp-status-aggregator"],
      "env": {
        "LDVH_BASE": "${workspaceFolder}/ldvh-base",
        "LDVH_SPECS": "${workspaceFolder}/specs"
      }
    }
  }
}
```

### 6.3 实施阶段

| 阶段 | 内容 | 前置条件 |
|---|---|---|
| 阶段一 | Fact Reader MCP + Status Aggregator MCP | 10-39 至少 Task 和 Change 对象规范稳定；tools/ 解析和聚合模块可用 |
| 阶段二 | Context Pack MCP + Validator MCP | 阶段一稳定；07 行动模型 Context 组件定义明确 |
| 阶段三 | Controlled Writer MCP | 阶段一和阶段二稳定；受控写入模块经过充分测试；Human Gate 判断逻辑可靠 |

### 6.4 代码复用结构

自建 MCP 应复用 tools/ 中的核心模块，而不是重新实现：

```text
tools/
  ├── parsers/          ← 解析模块（YAML、Markdown）
  ├── validators/       ← 校验模块（字段、状态、引用）
  ├── aggregators/      ← 聚合模块（状态视图、上下文包）
  ├── writers/          ← 受控写入模块
  └── mcp_servers/      ← MCP 入口（调用上述模块，通过 MCP 协议暴露）
        ├── fact_reader.py
        ├── status_aggregator.py
        ├── context_pack.py
        ├── validator.py
        └── controlled_writer.py
```

MCP 入口层只负责：

1. 接收 Agent 的工具调用请求；
2. 调用 tools/ 中的对应模块；
3. 将结果格式化为 MCP 工具响应返回。

---

## 七、与第三方 MCP 的分工

| 能力类型 | 第三方 MCP | 自建 MCP | 理由 |
|---|---|---|---|
| 复杂推理 | Sequential Thinking | — | 通用推理能力，LDVH 不需要自建 |
| 外部文档查询 | Context7 | — | 通用文档查询，LDVH 不需要自建 |
| 浏览器自动化 | Playwright | — | 通用浏览器能力，LDVH 不需要自建 |
| 事实源读取 | — | Fact Reader | LDVH 特有对象结构，第三方无法覆盖 |
| 状态聚合 | — | Status Aggregator | LDVH 特有视图模型，第三方无法覆盖 |
| 上下文包生成 | — | Context Pack | LDVH 特有 Context 定义，第三方无法覆盖 |
| 对象校验 | — | Validator | LDVH 特有校验规则，第三方无法覆盖 |
| 受控写入 | — | Controlled Writer | LDVH 特有写入约束，第三方无法覆盖 |

分工原则：

```text
通用能力用第三方 MCP；
LDVH 特有能力用自建 MCP；
两者不重叠，不冲突。
```

---

## 八、容量约束与工具分配

依据 refs/02 §八，Trae 对 MCP 有容量约束，自建 MCP 需要控制工具数量和工具描述长度。

| 约束 | 值 | 对自建 MCP 的影响 |
|---|---|---|
| 所有 MCP Server 描述信息字符数上限 | 8000 | 自建 MCP 的工具描述应精简，每个工具描述控制在 200 字符以内 |
| 所有 MCP Server 工具数量上限 | 40 | 自建 MCP + 第三方 MCP 的工具总数不得超过 40；按 Agent 分配可缓解 |
| MCP 响应内容可能被裁剪 | 动态 | 自建 MCP 应返回结构化摘要，不返回超长全文；重要结果应落盘到项目文件 |

应对策略：

1. 每个 Agent 只启用必要的自建 MCP，不把所有 MCP 都加给所有 Agent；
2. MCP 工具粒度应适中，避免过细占用工具数量，也避免过粗降低可用性；
3. Fact Reader 和 Status Aggregator 适合分配给大多数 Agent；
4. Controlled Writer 只分配给经 Human Gate 授权的写入型 Agent；
5. 工具使用流程可沉淀为 Skill，不依赖 MCP 工具描述承载全部说明。

---

## 九、风险与缓解

| 风险 | 说明 | 缓解措施 |
|---|---|---|
| 写入破坏事实源 | Controlled Writer MCP 如果绕过 Human Gate 或状态机校验，将直接破坏 `ldvh-base/` 完整性 | Controlled Writer 最后实现；写入前执行完整校验链；关键写入触发 Human Gate；写入后验证并追加 Change 记录；初期只实现只读 MCP |
| MCP 输出被当作事实源 | Agent 可能把结构化视图当作权威事实源 | 工具描述明确输出不是事实源；聚合结果包含来源引用；与 Git 文件事实源不一致时以 Git 为准 |
| 对象规范未稳定导致频繁变更 | 生产对象规范变更会导致 MCP 字段和状态机同步变更 | 等至少 Task 和 Change 对象规范稳定后再实现；MCP 与对象规范保持引用关系；初期只覆盖核心对象 |
| 维护成本上升 | 需要适配 Trae MCP 协议、对象规范和 tools/ 模块变更 | MCP 入口层保持薄封装；业务逻辑复用 tools/；入口层只测试协议适配 |
| 与 Web 展示层功能重叠 | Fact Reader、Status Aggregator、Context Pack 与 Web 展示层可能读取同类数据 | 底层复用同一 tools/ 模块；MCP 面向 Agent 结构化调用，Web 面向人可视化交互 |
| 误把 MCP 当作唯一程序入口 | 可能导致所有 Python 脚本被过度 MCP 化 | 明确 MCP 只是Tools 辅助层入口之一；简单能力保留 CLI；多步骤流程由 Skill 编排；面向人确认的能力进入 Web 展示层 |

---

## 十、Human Gate 建议

以下情况应评估 Human Gate：

1. 创建、修改或删除自建 MCP Server；
2. 将 Controlled Writer MCP 开放给 Agent 使用；
3. 自建 MCP 的写入操作绕过 Human Gate 或状态机校验；
4. 自建 MCP 维护独立于 Git 文件事实源的权威数据；
5. 自建 MCP 的工具输出被提升为稳定事实但未回写 Git 文件事实源；
6. 改变自建 MCP 与 05 工具层的职责分工。

---

## 十一、与 06 MCP 使用评估的关系

| 维度 | 06 评估 | 本文 |
|---|---|---|
| 范围 | 第三方 MCP 引入评估 | 自建 MCP 评估 |
| 核心问题 | LDVH 需要哪些第三方 MCP | LDVH 是否需要自建 MCP，以及自建哪些 |
| 定位 | MCP 是 Agent 的可选工具能力来源 | 自建 MCP 是Tools 辅助层的 Agent 接口 |
| 约束来源 | 03 事实源边界 + 05 工具边界 + 04.03 Agent 权限 | 同 06，另加 05.01 Tools 辅助规范的具体约束 |
| 优先级 | Sequential Thinking > Context7 > Playwright | Fact Reader + Status Aggregator > Context Pack + Validator > Controlled Writer |
| 互补关系 | 第三方 MCP 提供通用能力 | 自建 MCP 提供 LDVH 特有能力，两者不重叠 |

自建 MCP 与直接调用 Python 程序不是互斥关系。Python 程序是Tools 辅助层的能力实现，MCP 是其中一种面向 Agent 的协议入口。CLI、Skill、Web API 和 MCP 可以并存，区别在于服务对象、权限边界和交互形态不同。

---

## 十二、待补齐事项

1. 10-39 生产对象规范稳定后，确定 Fact Reader 和 Status Aggregator 的具体工具清单和字段映射；
2. 07 行动模型 Context 组件明确后，确定 Context Pack 的上下文类型和内容模板；
3. 05.01 Tools 辅助层模块可用后，评估 MCP 入口层的实现复杂度和复用比例；
4. Controlled Writer 的 Human Gate 判断逻辑待 07 Gate 组件和具体行动规范稳定后定义；
5. 如未来建立自建 MCP 的实现和测试流程，应将本文 §九 的风险缓解措施纳入实现规范。
