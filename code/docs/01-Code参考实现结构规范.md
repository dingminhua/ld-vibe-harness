# LDVH Code 参考实现结构规范

> 版本：0.1
> 更新：2026-06-15
> 范围：`code/` 目录下 LDVH Code 参考实现、命令入口、模块结构和测试映射
> 上位规范：[`specs/07-Code确定性执行实现规范.md`](../../specs/07-Code确定性执行实现规范.md)、[`specs/11-测试基础规范.md`](../../specs/11-测试基础规范.md)

## 0. 上位规范

`specs/07-Code确定性执行实现规范.md` 是 LDVH Code 构成要素、确定性执行边界、需求准入、验证规则、维护规则和 Code 文档边界的权威规范。`specs/11-测试基础规范.md` 是跨构成要素测试治理、验证声明、测试实现归属和测试证据事实源边界的权威规范。

本文只定义 `code/` 参考实现的目录结构、模块拆分、命令入口、测试映射和 AI 修改顺序，不替代 `specs/07-Code确定性执行实现规范.md`、`specs/11-测试基础规范.md`、工作模型规范、工作流程规范、事实源边界规范或具体对象契约。

当本文与 `specs/07-Code确定性执行实现规范.md` 或 `specs/11-测试基础规范.md` 存在冲突或解释不一致时，以 specs 为准；`code/` 实现和 `code/docs/` 文档不得通过实现细节反向改写 specs 正文、对象字段契约、状态机、Human Gate 条件、测试治理规则或事实源归属。

## 1. 本文解决的问题

本文解决 LDVH 当前 `code/` 参考实现如何组织、扩展、拆分和维护的问题。

本文的目标是让 AI 修改 Code 时有稳定执行细则：

1. 保持既有命令入口对 AI、Human、Web 和测试可用；
2. 防止不同检查域继续堆叠到单个脚本；
3. 让新增检查先归入明确能力域，再选择实现位置；
4. 让拆分成为可验证、无行为变化的渐进重构；
5. 让测试文件和实现模块之间有可追溯映射。

## 2. 当前 Code 参考实现清单

当前 `code/` 目录下的参考实现如下：

| 文件 | 当前职责 | 结构治理要求 |
|---|---|---|
| `code/specs_validate.py` | specs 文档结构、引用、保障要求、术语、Human Gate、管辖项目、运行投影、Web validate 派生检查等聚合入口 | 作为 CLI 兼容层和跨模块配置同步层；新增检查不得默认继续堆入此文件，应进入 `code/spec_checks/` |
| `code/fact_cli.py` | 工作对象事实源查询、展示、搜索和统计入口 | 查询能力扩展时应保持输出来源可追溯，必要时拆出共享读取层 |
| `code/fact_validate.py` | 工作对象事实源校验入口 | 字段、状态和对象关系规则变化时同步测试；不得把 specs 规则复制为第二事实源 |
| `code/commit_validate.py` | commit message 校验入口 | 保持轻量单一职责；规则变化应回到对应规范或工作流程 |
| `code/fix_block_scalar.py` | YAML block scalar 辅助修复脚本 | 只作为定向辅助脚本，不扩张为通用写入工具 |

`code/` 中新增文件前，应先判断是否属于既有能力域；若属于 specs 校验域，应优先进入 `code/spec_checks/` 目标结构，而不是新增新的根级大脚本。

## 3. 目录边界

`code/` 参考实现使用以下目录边界：

| 路径 | 用途 | 不应承载 |
|---|---|---|
| `code/*.py` | 稳定 CLI 入口、轻量单一职责脚本或兼容包装入口 | 多个独立能力域的长期堆叠实现 |
| `code/spec_checks/` | specs 校验、索引、聚合和诊断的能力域模块 | 工作对象事实源校验、Web UI 实现、长期规范正文 |
| `code/docs/` | Code 参考实现结构、执行细则、命令说明和迁移计划 | LDVH 稳定规范规则、对象字段契约、状态机、Human Gate 权威条件 |
| `tests/code/` | Code 参考实现测试、正反样例和回归测试 | specs 正文、长期事实源、Web 页面测试 |

`code/spec_checks/` 是 specs 校验域的目标模块目录。该目录不存在时，新增 specs 校验能力可以先在兼容入口中实现，但必须在本文件或任务记录中说明后续归属；一旦创建该目录，新能力应优先进入对应模块。

## 4. `specs_validate.py` 结构治理

`code/specs_validate.py` 当前承担历史聚合入口职责。它可以继续作为 CLI 兼容层存在，但不应继续作为所有 specs 检查规则的默认实现落点。

### 4.1 兼容入口

以下命令属于稳定兼容入口，拆分时必须保持行为兼容：

| 命令 | 兼容要求 |
|---|---|
| `python3 code/specs_validate.py doc specs` | 继续检查 Markdown 文档结构 |
| `python3 code/specs_validate.py refs specs` | 继续检查章节引用 |
| `python3 code/specs_validate.py assurance specs` | 继续检查规范保障要求表 |
| `python3 code/specs_validate.py index --fail-on-diagnostics` | 继续输出派生索引和诊断 |
| `python3 code/specs_validate.py all --fail-on-diagnostics` | 继续作为 specs 综合校验入口 |
| `python3 code/specs_validate.py governed-projects` | 继续检查工作区管辖项目配置 |
| `python3 code/specs_validate.py assurance-report` | 继续聚合规范保障要求报告 |
| `python3 code/specs_validate.py ldvh-assurance-check` | 继续生成 LDVH 部署适配检查派生报告 |
| `python3 code/specs_validate.py assurance-plan` | 继续生成只读 assurance-plan 聚合计划视图 |
| `python3 code/specs_validate.py web-validate` | 继续输出 Web Validate 只读数据合同 |

拆分模块时，CLI 参数、exit code、关键诊断 code 和默认输入范围不得无说明改变。确需改变时，应先更新 `specs/07-Code确定性执行实现规范.md`、本文、测试和下游调用方。

### 4.2 能力域目标模块

`specs_validate.py` 后续应按能力域迁移到以下目标模块：

| 能力域 | 目标模块 | 当前来源 |
|---|---|---|
| 通用类型、路径、Markdown 遍历和 Issue 输出 | `code/spec_checks/common.py` | `Issue`、`iter_markdown_files`、共享正则和路径工具 |
| 运行投影漂移检查 | `code/spec_checks/runtime_projection.py` | `runtime_projection_*` |
| LDVH 能力资产检查 | `code/spec_checks/deployment_entries.py` | `deployment_entries_*` |
| specs 语义一致性检查 | `code/spec_checks/consistency.py` | `consistency_*` |
| 文档结构检查 | `code/spec_checks/doc_structure.py` | `doc_*`、`Heading` |
| 章节引用检查 | `code/spec_checks/refs.py` | `refs_*`、`Document` |
| 规范保障要求表 | `code/spec_checks/assurance.py` | `assurance_*` |
| 规范保障要求聚合报告 | `code/spec_checks/assurance_report.py` | `assurance_report_*`、运行投影和 Human Gate 报告消费 |
| Human Gate 证据结构检查 | `code/spec_checks/human_gate.py` | `human_gate_*` |
| 管辖项目配置检查 | `code/spec_checks/governed_projects.py` | `governed_projects_*` |
| LDVH 部署适配检查和保障计划 | `code/spec_checks/ldvh_assurance.py` | `ldvh_assurance_check_*`、`assurance_plan_*` |
| Web Validate 派生数据压缩 | `code/spec_checks/web_validate.py` | `web_validate_*` |
| specs 派生索引和诊断 | `code/spec_checks/index.py` | `SpecsChecker` 和 `INDEX_*` |

模块迁移应优先选择边界清楚、依赖少、测试覆盖明确的能力域；不得在一次迁移中同时改变行为和搬移大量不相关能力域。

### 4.3 防堆砌规则

出现以下情况时，不得继续把新功能直接追加到 `specs_validate.py` 的主体实现中：

1. 新功能属于 §4.2 已列出的能力域；
2. 新功能需要新增一组独立常量、解析器、诊断 code 和测试样例；
3. 新功能只被某个子命令消费，不需要全文件共享；
4. 新功能会让单个文件继续跨越多个无直接依赖的检查域；
5. 新功能的验证可以在独立模块中完成，并由 CLI 入口聚合调用。

允许临时修改 `specs_validate.py` 主体的情况：

1. 修复已有子命令的阻断 bug；
2. 保持 CLI 兼容、参数解析或跨模块编排；
3. 为即将拆分的模块做无行为变化的提取准备；
4. 当前能力域尚未建模块，且本次任务同时记录后续归属和测试覆盖。

## 5. 新增或修改 Code 的 AI 执行顺序

AI 修改 `code/` 时，应按以下顺序执行：

1. 读取 `specs/07-Code确定性执行实现规范.md` 和本文；
2. 定位需求来源、规则来源、输入范围、失败条件和降级方式；
3. 判断能力域和实现位置；
4. 若为 specs 校验能力，优先选择 `code/spec_checks/` 目标模块或兼容入口中的对应能力域；
5. 先补正例、反例、边界样例、测试命令或等价验证方式；
6. 再做最小实现或无行为变化拆分；
7. 运行对应测试和必要的综合校验；
8. 若改变 CLI、输出结构、诊断 code、写入行为或下游消费方式，同步更新本文、`specs/07-Code确定性执行实现规范.md`、Web 调用方或入口引用。

### 5.1 Code 结构变更记录要求

本文必须始终保持为后续 AI 可直接读取和继续执行的 Code 结构交接文档。AI 做出以下任一调整时，应在同一轮工作中同步更新本文：

1. 新增、删除、移动、重命名或拆分 `code/` 下的模块、包、命令入口或测试入口；
2. 改变 `specs_validate.py` 与 `code/spec_checks/` 之间的职责边界、兼容包装方式或迁移顺序；
3. 改变 CLI 参数、默认输入范围、exit code、诊断 code、结构化输出字段、写入行为或下游消费合同；
4. 新增检查能力、共享 helper、测试目录结构或能力域归属规则；
5. 做出会影响其他 AI 后续判断实现位置、测试位置、迁移状态、拆分优先级或安全边界的调整。

记录时应优先更新本文中最接近的章节，例如 §2 当前清单、§3 目录边界、§4.2 能力域目标模块、§4.3 防堆砌规则、§6 测试映射、§7 拆分顺序或 §8 待补齐事项。记录内容应说明当前事实、后续归属、兼容要求和必要验证方式；不得只在提交说明、聊天记录或临时任务中保留 Code 结构事实。

若调整会改变上位规则、对象字段契约、状态机、Human Gate 条件、事实源归属、长期降级接受、Web/CLI 对外合同或是否继续保留兼容入口，应先回到 `specs/07-Code确定性执行实现规范.md` 和相关正式规范判断；仍需取舍时，应暂停请求 Human 判断，再按判断结果更新本文和必要事实源。

## 6. 测试映射

Code 参考实现测试放在 `tests/code/`。测试文件应能让 AI 直接定位被验证入口：

| 实现入口或模块 | 测试位置 |
|---|---|
| `code/specs_validate.py` | `tests/code/test_specs_validate.py` 保留 CLI 兼容入口加载、`all --fail-on-diagnostics` 聚合入口成功回归和失败回归 |
| `code/spec_checks/common.py` | `tests/code/specs_validate_checks/common.py` 提供 specs 校验测试共享加载和 Markdown 夹具 helper |
| `code/spec_checks/doc_structure.py` | `tests/code/specs_validate_checks/test_doc_structure.py` |
| `code/spec_checks/refs.py` | `tests/code/specs_validate_checks/test_refs.py` |
| `code/spec_checks/assurance_report.py` | `tests/code/specs_validate_checks/test_assurance_report.py` |
| `code/spec_checks/runtime_projection.py` | `tests/code/specs_validate_checks/test_runtime_projection.py` |
| `code/spec_checks/deployment_entries.py` | `tests/code/specs_validate_checks/test_deployment_entries.py` |
| `code/spec_checks/human_gate.py` | `tests/code/specs_validate_checks/test_human_gate.py` |
| `code/spec_checks/governed_projects.py` | `tests/code/specs_validate_checks/test_governed_projects.py` |
| `code/spec_checks/ldvh_assurance.py` | `tests/code/specs_validate_checks/test_ldvh_assurance.py` |
| `code/spec_checks/web_validate.py` | `tests/code/specs_validate_checks/test_web_validate.py` |
| `code/spec_checks/index.py` | `tests/code/specs_validate_checks/test_index.py` |
| `code/spec_checks/consistency.py` | `tests/code/specs_validate_checks/test_consistency.py` |
| `code/fact_validate.py` | `tests/code/test_fact_validate.py` 或对应事实模型测试 |
| `code/fact_cli.py` | `tests/code/test_fact_cli.py` 或 CLI 行为测试 |
| `code/commit_validate.py` | `tests/code/test_commit_validate.py` |
| 受控写入或修复脚本 | 对应脚本名测试，并覆盖写入前阻断和写入后验证 |

当实现模块拆分但 CLI 行为不变时，应保留原 CLI 集成测试，并补充必要的模块级单元测试。拆分提交不得以“只是搬文件”为理由跳过测试。

`npm run test:code` 是 Code 参考实现的日常完整测试入口，必须同时执行 `tests/code` 自动化测试和 `python3 code/specs_validate.py all --fail-on-diagnostics` 综合检查。只需要快速运行 pytest 样例时使用 `npm run test:code:unit`；不得把 `test:code` 降级为仅入口加载、仅模块单元测试或不含 specs 聚合检查的烟雾测试。

`tests/code/specs_validate_checks/` 是 `specs_validate.py` 测试的能力域拆分目录。目录名不得使用 `tests/code/spec_checks/`，避免与实现包 `code/spec_checks/` 在 pytest import 解析中发生同名包冲突。

## 7. `specs_validate.py` 渐进拆分顺序

`specs_validate.py` 拆分应按以下优先级推进：

1. 先提取无写入、依赖少、输出独立的能力域，例如 `runtime_projection`、`governed_projects`、`human_gate`；
2. 再提取表格解析和 Markdown 结构类能力，例如 `doc_structure`、`refs`、`assurance`；
3. 再提取大型聚合报告；`ldvh_assurance` 已迁入 `code/spec_checks/ldvh_assurance.py`，`web_validate` 已迁入 `code/spec_checks/web_validate.py`；
4. 最后处理共享常量较多的 `consistency` 和 `index`，避免早期拆分制造循环依赖；
5. 每次拆分后运行 `python3 code/specs_validate.py all --fail-on-diagnostics` 和对应 `tests/code` 测试。

拆分过程应优先保持行为不变。若必须改变行为，应单独提交，并在提交说明或任务记录中说明规则来源、验证证据和下游影响。

## 8. 待补齐事项

1. `specs_validate.py` 的主要检查能力域已迁入 `code/spec_checks/`；该文件当前只应承担 CLI 兼容、配置同步、常量/函数兼容引用和跨模块编排；
2. `specs_validate.py` 的结构化输出字段、错误码和诊断格式仍需后续统一；
3. Code 与 Web Validate API 的输出合同仍需在 Code 结构稳定后补齐更细的数据结构说明。
