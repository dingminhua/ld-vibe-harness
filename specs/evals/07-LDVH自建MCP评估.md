# LD Vibe Harness 自建 MCP 评估

> 创建日期：2026-05-30
> 状态：内部调研
> 编号归属：70-89 内部调研
> 调研边界：不直接构成强制规则
> 执行效力：无，结论需进入 01-69 正式规范区间或 ADR 后才成为稳定规则
> 上位依据：`specs/00-LD-Vibe-Harness理念与纲要.md`
> 相关规范：`specs/03-事实源边界与承载规范.md`、`specs/04-LDVH-AI协作规范.md`、`specs/05-LDVH工具基础规范.md`、`specs/05.01-程序辅助规范.md`、`specs/07-LDVH行动模型基础规范.md`
> 参考来源：`specs/refs/02-Trae-MCP用法调研.md`、`specs/evals/06-LDVH的MCP使用评估.md`

---

## 一、本文解决的问题

本文评估 LD Vibe Harness 是否需要自建 MCP Server，以及如果需要，应自建哪些 MCP Server、如何与现有 05 工具层和 07 行动模型衔接、自建 MCP 的实现路径和风险。

06 评估了第三方 MCP 的引入优先级和约束，本文聚焦自建 MCP——即 LDVH 自行开发、部署在项目本地、为 Agent 提供结构化事实源访问和受控操作能力的 MCP Server。

本文是内部调研，不直接构成强制规则；调研结论进入 01-69 正式规范区间或 ADR 后才成为稳定规则。

---

## 二、为什么考虑自建 MCP

### 2.1 第三方 MCP 的能力缺口

06 评估的第三方 MCP（Sequential Thinking、Context7、Playwright 等）主要提供通用推理、文档查询和浏览器自动化能力，但无法覆盖 LDVH 特有的结构化事实源操作需求：

| 需求 | 第三方 MCP 能否覆盖 | 缺口说明 |
|---|---|---|
| 读取 ldvh-base/ 中的生产对象实例 | 否 | 第三方 MCP 不理解 LDVH 对象结构、字段契约和状态机 |
| 校验生产对象字段和状态合法性 | 否 | 校验规则由 11-22 具体对象规范定义，第三方 MCP 不掌握 |
| 聚合项目状态（阻塞视图、待验收视图等） | 否 | 聚合逻辑依赖 LDVH 目录结构和对象关系 |
| 生成最小可行动上下文包 | 否 | 上下文包由 07 行动模型的 Context 组件定义 |
| 受控写入 ldvh-base/ | 否 | 写入必须经过校验、Human Gate 判断和 Change 记录 |
| 查询 specs 规范体系结构 | 否 | specs 编号分区、文档类型和引用纪律是 LDVH 特有 |

### 2.2 Trae 内置工具的能力缺口

Trae 内置工具（文件系统、终端、搜索等）可以读写任意文件，但无法理解 LDVH 的结构化语义：

| 需求 | Trae 内置工具能否覆盖 | 缺口说明 |
|---|---|---|
| 按 Task 状态筛选 | 部分 | 可用 grep 搜索 YAML 字段，但无法保证语义正确和状态机合法 |
| 检查对象引用完整性 | 否 | 需要理解对象间关系，不是简单的文本搜索 |
| 生成上下文包 | 部分 | 可读取多个文件拼接，但无法保证最小化和结构化 |
| 受控写入前校验 | 否 | 内置工具不校验写入内容的对象格式和状态流转 |
| 聚合视图 | 部分 | 可用脚本聚合，但每次需重新编写和调试 |

### 2.3 自建 MCP 的核心价值

自建 MCP 的核心价值是：**把 05.01 程序辅助层的确定性能力，通过 MCP 协议暴露为 Agent 可调用的结构化工具，让 Agent 不需要理解文件格式和校验逻辑，只需调用工具即可完成事实源读取、校验、聚合和受控写入**。

这与 03 Agent-Harness 评估中的启发一致："把工具调用纳入治理，而不是追求更多工具"——自建 MCP 不是增加工具数量，而是让已有程序辅助能力以更结构化、更受控的方式被 Agent 使用。

---

## 三、自建 MCP 与 05 工具层的关系

### 3.1 关键判断：自建 MCP 是程序辅助层的 Agent 接口，不是替代

自建 MCP Server 不是新的工具层，而是 05.01 程序辅助层面向 Agent 的协议接口：

```text
程序辅助层（tools/）
  ├── 命令行入口（当前已有）
  ├── Web API 入口（供 05.02 Web 展示层调用）
  └── MCP 入口（供 Agent 通过 Trae MCP 协议调用）  ← 自建 MCP 在此
```

这意味着：

1. 自建 MCP 的底层逻辑应复用 tools/ 中的解析、校验、聚合和受控写入模块；
2. 自建 MCP 不另建权威数据存储，所有读写仍指向 Git 文件事实源；
3. 自建 MCP 的输出与程序辅助层输出一样，不是最终事实源。

### 3.2 自建 MCP 不改变 05 工具边界

自建 MCP 引入后，05 工具基础规范的所有约束仍然适用：

1. MCP 工具输出不是最终事实源（依据 `specs/05` §四）；
2. MCP 工具不得绕过程序辅助层的校验和受控写入边界（依据 `specs/05` §七）；
3. MCP 工具不得直接调用 AI、Skill 或 Agent（依据 `specs/05` §七）；
4. MCP 工具不得替代 specs/、ldvh-base/ 或 docs/ 的权威事实（依据 `specs/05` §四）。

---

## 四、候选自建 MCP 评估

### 4.1 LDVH Fact Reader MCP

| 维度 | 评估 |
|---|---|
| 定位 | 为 Agent 提供结构化的事实源读取能力 |
| 核心工具 | `read_task`：按 ID 读取 Task 实例并返回结构化字段；`list_tasks`：按状态、优先级、项目筛选 Task 列表；`read_adr`：按 ID 读取 ADR 实例；`read_memo`：按 ID 读取 Memo 实例；`read_change`：按 ID 读取 Change 记录；`read_pitfall`：按 ID 读取 Pitfall 记录 |
| 对 LDVH 的价值 | 高。Agent 当前读取 ldvh-base/ 只能通过文件系统工具逐文件解析，无法按对象类型、状态或关系筛选；Fact Reader 让 Agent 以语义化方式访问生产对象，降低上下文组装成本 |
| 与 05.01 的关系 | 复用 tools/ 中的解析模块，通过 MCP 协议暴露为结构化工具 |
| 与 07 的关系 | 直接支撑 Context 组件——Agent 可通过 Fact Reader 快速组装最小可行动上下文 |
| 事实源约束 | 只读，不写入；输出是 Git 文件事实源的结构化视图，不是独立事实源 |
| 实现复杂度 | 中。需要解析 YAML 文件并按对象规范定义字段契约；11-22 对象规范稳定后实现更可靠 |
| 优先级 | 第一优先级 |

### 4.2 LDVH Status Aggregator MCP

| 维度 | 评估 |
|---|---|
| 定位 | 为 Agent 提供项目状态聚合视图 |
| 核心工具 | `blocked_tasks`：返回所有 Blocked 状态的 Task 及阻塞原因；`review_needed_tasks`：返回所有 Review Needed 状态的 Task；`decision_needed`：返回所有需要决策的 Task 和 ADR；`project_summary`：返回项目整体状态摘要（Task 数量按状态分布、阻塞数、待验收数等）；`intent_progress`：返回 Intent 及其下属 TaskSet/Task 的完成进度 |
| 对 LDVH 的价值 | 高。01 Linear 借鉴评估中识别的"阻塞视图"和"待验收视图"是 AI 行动模型最关键的工作入口；Status Aggregator 让 Agent 快速定位当前最需处理的任务，不需要逐文件扫描 |
| 与 05.01 的关系 | 复用 tools/ 中的聚合模块，按 01 评估 §4.3 的视图模型设计聚合维度 |
| 与 07 的关系 | 直接支撑 Scenario 识别——Agent 可通过 Status Aggregator 判断当前应进入阻塞处理、Review 还是需求规划场景 |
| 事实源约束 | 只读，不写入；输出是派生视图，不是事实源；聚合结果必须可追溯到 Git 文件事实源 |
| 实现复杂度 | 中。需要遍历 ldvh-base/ 中的对象实例并按状态聚合；对象规范稳定后实现更可靠 |
| 优先级 | 第一优先级 |

### 4.3 LDVH Context Pack MCP

| 维度 | 评估 |
|---|---|
| 定位 | 为 Agent 生成最小可行动上下文包 |
| 核心工具 | `task_context`：生成指定 Task 的完整上下文（Task YAML + source_doc + dependencies + acceptance + 最近更新）；`decision_context`：生成决策上下文（决策问题 + 选项 + 相关 ADR + 影响范围）；`review_context`：生成 Review 上下文（变更摘要 + 验证结果 + closure_evidence + 待验收事项）；`change_context`：生成变更上下文（变更原因 + 影响文件 + 验证状态） |
| 对 LDVH 的价值 | 高。03 Agent-Harness 评估 §6.2 明确建议"强化最小可行动上下文"；01 Linear 借鉴评估 §6.5 建议"一键复制 AI 上下文"是 LDVH 区别于 Linear 的核心能力 |
| 与 05.01 的关系 | 复用 tools/ 中的上下文包生成模块，按 07 §4.1 的 Context 组织原则实现 |
| 与 07 的关系 | 直接实现 Context 组件——Agent 可通过 Context Pack MCP 获取当前任务的最小可行动上下文，不需要自行从多个文件拼装 |
| 事实源约束 | 只读，不写入；输出是派生上下文，不是事实源；上下文中出现的新信息如需长期保留，应重新判断对象类型和事实源载体 |
| 实现复杂度 | 中高。需要跨多个对象和文件聚合信息，且需要按 07 的 Context 类型（项目初始化、任务执行、需求规划、Review、审计）动态调整内容 |
| 优先级 | 第二优先级（依赖 Fact Reader 和 Status Aggregator） |

### 4.4 LDVH Validator MCP

| 维度 | 评估 |
|---|---|
| 定位 | 为 Agent 提供生产对象校验能力 |
| 核心工具 | `validate_task`：校验 Task 字段完整性、状态合法性和引用有效性；`validate_change`：校验 Change 记录格式和关联对象存在性；`validate_state_transition`：校验状态流转是否合法；`check_references`：检查对象间引用完整性 |
| 对 LDVH 的价值 | 中高。05.01 程序辅助规范 §六已定义解析与校验原则，但当前校验只能通过命令行或 Web 界面触发；Validator MCP 让 Agent 在执行任务时可以主动校验，减少非法状态流转和引用缺失 |
| 与 05.01 的关系 | 直接复用 tools/ 中的校验模块，通过 MCP 协议暴露 |
| 与 07 的关系 | 支撑 Gate 判断——Agent 可通过 Validator 在关键操作前校验合法性，辅助 Human Gate 判断 |
| 事实源约束 | 只读，不写入；校验结果是派生信息，不是事实源；校验失败不得自动修改事实源 |
| 实现复杂度 | 中。校验逻辑由 11-22 对象规范定义，规范稳定后实现更可靠 |
| 优先级 | 第二优先级 |

### 4.5 LDVH Controlled Writer MCP

| 维度 | 评估 |
|---|---|
| 定位 | 为 Agent 提供受控写入 ldvh-base/ 的能力 |
| 核心工具 | `create_task`：创建 Task 实例并校验必填字段；`update_task_status`：更新 Task 状态并校验状态流转合法性；`create_change`：创建 Change 记录；`create_memo`：创建 Memo 实例；`create_pitfall`：创建 Pitfall 实例 |
| 对 LDVH 的价值 | 高但高风险。当前 Agent 写入 ldvh-base/ 只能通过文件系统工具直接写文件，无法校验格式、状态流转和 Human Gate；Controlled Writer 让写入经过校验和门禁，但引入了 Agent 直接修改事实源的能力 |
| 与 05.01 的关系 | 直接复用 tools/ 中的受控写入模块，按 05.01 §八 的写入前检查和写入后验证原则实现 |
| 与 07 的关系 | 支撑事实源回写——Agent 可通过 Controlled Writer 按规范回写事实源，而不是直接写文件 |
| 事实源约束 | 写入目标必须是 Git 文件事实源；写入前必须校验；写入后必须可通过 Git 追溯；关键写入必须触发 Human Gate；写入结果不得只停留在 MCP 响应中 |
| 实现复杂度 | 高。需要实现完整的写入前校验、Human Gate 判断、写入后验证和 Change 记录追加；任何写入错误都可能导致事实源损坏 |
| 风险 | 高。写入能力是最需要审慎对待的能力：如果 MCP 写入绕过了 Human Gate 或状态机校验，将直接破坏事实源完整性 |
| 优先级 | 第三优先级（最后实现，且必须在前四个 MCP 稳定后） |

---

## 五、自建 MCP 的实现路径

### 5.1 技术选型

| 维度 | 建议 | 理由 |
|---|---|---|
| 传输方式 | stdio | LDVH 是本地项目，不需要远程访问；stdio 最简单、最安全 |
| 运行方式 | 通过 `npx` 或 `uvx` 启动 | 与 Trae 官方推荐的本地 MCP 启动方式一致 |
| 编程语言 | Python | 与 tools/ 程序辅助层一致，可复用已有解析、校验、聚合模块 |
| 配置位置 | `.trae/mcp.json` 项目级配置 | 符合 Trae 项目级 MCP 规范，配置跟随项目 |

### 5.2 配置示例

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

### 5.3 实现阶段

| 阶段 | 内容 | 前置条件 |
|---|---|---|
| 阶段一 | Fact Reader MCP + Status Aggregator MCP | 11-22 至少 Task 和 Change 对象规范稳定；tools/ 解析和聚合模块可用 |
| 阶段二 | Context Pack MCP + Validator MCP | 阶段一稳定；07 行动模型 Context 组件定义明确 |
| 阶段三 | Controlled Writer MCP | 阶段一和阶段二稳定；受控写入模块经过充分测试；Human Gate 判断逻辑可靠 |

### 5.4 与 tools/ 程序辅助层的代码复用

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

MCP 入口层不实现业务逻辑，不维护状态，不存储数据。

---

## 六、自建 MCP 与第三方 MCP 的分工

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

## 七、自建 MCP 的容量约束评估

依据 refs/02 §八，Trae 对 MCP 有以下容量约束：

| 约束 | 值 | 对自建 MCP 的影响 |
|---|---|---|
| 所有 MCP Server 描述信息字符数上限 | 8000 | 自建 MCP 的工具描述应精简，每个工具描述控制在 200 字符以内 |
| 所有 MCP Server 工具数量上限 | 40 | 自建 MCP + 第三方 MCP 的工具总数不得超过 40；按 Agent 分配可缓解 |
| MCP 响应内容可能被裁剪 | 动态 | 自建 MCP 应返回结构化摘要，不返回超长全文；重要结果应落盘到项目文件 |

容量约束应对策略：

1. 每个 Agent 只启用必要的自建 MCP，不把所有自建 MCP 都加给所有 Agent；
2. 自建 MCP 的工具粒度应适中——太细会占用工具数量，太粗会降低可用性；
3. Fact Reader 和 Status Aggregator 适合分配给大多数 Agent；
4. Controlled Writer 只分配给经 Human Gate 授权的写入型 Agent；
5. 工具使用流程沉淀为 Skill，不依赖 MCP 工具描述承载全部说明。

---

## 八、自建 MCP 的风险与缓解

### 8.1 风险：写入破坏事实源

| 维度 | 说明 |
|---|---|
| 风险描述 | Controlled Writer MCP 如果绕过 Human Gate 或状态机校验，将直接破坏 ldvh-base/ 中的事实源完整性 |
| 缓解措施 | 1. Controlled Writer 最后实现，且必须在前四个 MCP 稳定后；2. 写入前必须执行完整校验链；3. 关键写入必须触发 Human Gate，由人确认后才执行；4. 写入后必须验证并追加 Change 记录；5. 初期可只实现只读 MCP，写入仍由人通过 Web 界面或命令行完成 |

### 8.2 风险：MCP 输出被当作事实源

| 维度 | 说明 |
|---|---|
| 风险描述 | Agent 可能将 MCP 返回的结构化视图当作权威事实源，而不是回到 Git 文件事实源 |
| 缓解措施 | 1. MCP 工具描述中明确标注"输出是派生视图，不是事实源"；2. 聚合结果包含来源引用，使每个数据项可追溯到 Git 文件事实源；3. MCP 输出与 Git 文件事实源不一致时以 Git 为准 |

### 8.3 风险：对象规范未稳定导致 MCP 频繁变更

| 维度 | 说明 |
|---|---|
| 风险描述 | 11-22 对象规范当前均为 planned 状态，MCP 实现后如果对象字段或状态机变更，MCP 需要同步修改 |
| 缓解措施 | 1. 等 11-22 至少 Task 和 Change 对象规范稳定后再开始实现；2. MCP 实现应与对象规范保持引用关系，规范变更时同步更新 MCP；3. 初期可只实现最核心的对象类型（Task、Change），其他对象待规范稳定后逐步加入 |

### 8.4 风险：MCP 维护成本

| 维度 | 说明 |
|---|---|
| 风险描述 | 自建 MCP 需要持续维护：适配 Trae MCP 协议更新、适配对象规范变更、修复 Bug |
| 缓解措施 | 1. MCP 入口层保持薄封装，业务逻辑复用 tools/ 模块，减少重复维护；2. MCP 实现应与 tools/ 模块版本对齐；3. 如 tools/ 模块已有测试，MCP 入口层只需测试协议适配 |

### 8.5 风险：MCP 与 Web 展示层功能重叠

| 维度 | 说明 |
|---|---|
| 风险描述 | Fact Reader / Status Aggregator / Context Pack 的部分能力与 05.02 Web 展示层重叠 |
| 缓解措施 | 1. 两者底层都复用 tools/ 模块，不重复实现；2. MCP 面向 Agent 的结构化调用，Web 展示层面向人的可视化交互，服务对象和输出格式不同；3. 不因 MCP 存在就减少 Web 展示层能力，也不因 Web 展示层存在就不建 MCP |

---

## 九、自建 MCP 的 Human Gate 建议

以下情况应评估 Human Gate：

1. 创建、修改或删除自建 MCP Server；
2. 将 Controlled Writer MCP 开放给 Agent 使用；
3. 自建 MCP 的写入操作绕过 Human Gate 或状态机校验；
4. 自建 MCP 维护独立于 Git 文件事实源的权威数据；
5. 自建 MCP 的工具输出被提升为稳定事实但未回写 Git 文件事实源；
6. 改变自建 MCP 与 05 工具层的职责分工。

---

## 十、与 06 MCP 使用评估的关系

| 维度 | 06 评估 | 本文 |
|---|---|---|
| 范围 | 第三方 MCP 引入评估 | 自建 MCP 评估 |
| 核心问题 | LDVH 需要哪些第三方 MCP | LDVH 是否需要自建 MCP，以及自建哪些 |
| 定位 | MCP 是 Agent 的可选工具能力来源 | 自建 MCP 是程序辅助层的 Agent 接口 |
| 约束来源 | 03 事实源边界 + 05 工具边界 + 04.03 Agent 权限 | 同 06，另加 05.01 程序辅助规范的具体约束 |
| 优先级 | Sequential Thinking > Context7 > Playwright | Fact Reader + Status Aggregator > Context Pack + Validator > Controlled Writer |
| 互补关系 | 第三方 MCP 提供通用能力 | 自建 MCP 提供 LDVH 特有能力，两者不重叠 |

---

## 十一、待补齐事项

1. 11-22 对象规范稳定后，确定 Fact Reader 和 Status Aggregator 的具体工具清单和字段映射；
2. 07 行动模型 Context 组件明确后，确定 Context Pack 的上下文类型和内容模板；
3. 05.01 程序辅助层模块可用后，评估 MCP 入口层的实现复杂度和复用比例；
4. Controlled Writer 的 Human Gate 判断逻辑待 07 Gate 组件和具体行动规范稳定后定义；
5. 如未来建立自建 MCP 的实现和测试流程，应将本文 §八 的风险缓解措施纳入实现规范。
