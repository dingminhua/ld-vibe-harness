# 知识地图与受控写入 Preflight 实现计划

> 版本：0.1
> 更新：2026-06-23
> 范围：Code 第二版中知识地图只读投影、受控写入前检查和相关测试的实现计划
> 上位规范：[`specs/04-Code确定性执行规范.md`](../../specs/04-Code确定性执行规范.md)、[`specs/attachments/04.Att.05-知识地图输入范围表.md`](../../specs/attachments/04.Att.05-知识地图输入范围表.md)、[`specs/attachments/04.Att.06-知识地图投影Schema表.md`](../../specs/attachments/04.Att.06-知识地图投影Schema表.md)、[`specs/attachments/04.Att.07-受控写入前检查矩阵.md`](../../specs/attachments/04.Att.07-受控写入前检查矩阵.md)、[`specs/08-测试基础规范.md`](../../specs/08-测试基础规范.md)

## 0. 文件性质

本文是 `code/docs/` 下的 Code 参考实现计划，不是正式规范、事实模型、行动编排、Human Gate 条件或事实源边界。

本文只能规划实现顺序、模块归属、测试切分、兼容要求和验收方式。若实现过程中发现规范缺口，应回到 `specs/04-Code确定性执行规范.md`、对应附件、事实模型规范、行动编排规范或 `specs/07-事实源边界与Git追溯规范.md`，不得在本文中直接补权威规则。

## 1. 目标

Code 第二版先完成两个能力：

1. 知识地图只读投影：从授权输入范围解析节点、关系、来源回指和降级诊断，帮助 AI 控制读取范围和判断关联影响；
2. 受控写入 preflight：在写入前只读检查路径、字段、状态、Gate、事实源、Git 追溯和同步影响，帮助 AI 判断是否可以继续、暂停或交给 Human Gate。

这两个能力都不得写入事实源，不得生成长期知识图缓存，不得替代 Human 判断，不得把检查通过解释为写入授权。

## 2. 当前基线

当前实现基线如下：

| 能力 | 当前状态 | 边界 |
|---|---|---|
| `python3 code/specs_validate.py v2-check` | 已能输出 active specs 诊断和只读知识地图预览子集 | 不等于完整知识地图运行时 |
| active specs 输入 | 默认读取当前 `specs/`，测试中保留 `specs-v2` 兼容夹具 | `specs_v2` 作为既有 input_scope 名称先保留兼容 |
| 知识地图查询层 | 已有 `entry`、`neighbors`、`expand`、`raw` 的部分行为 | 未实现 raw 原文层、管辖项目层和 Git history 层 |
| 降级诊断 | 已对部分未实现范围输出 degraded 诊断 | 诊断 Schema 尚未完整统一 |
| preflight | 尚未实现命令或模块 | 不得登记为 active Code 命令 |

## 3. 不做事项

第一轮实现不做以下事项：

1. 不落盘知识地图 JSON、SQLite、外部图数据库或 Web 本地缓存；
2. 不实现自动写入、自动修复、自动提交或事实源代写；
3. 不把历史 v1 事实源解释为 active 权威；
4. 不把 `web_cache`、测试缓存、聊天过程、临时审计或迁移计划作为可信节点边输入；
5. 不把 Web 接入、管辖项目图谱、Git history 图谱和 raw 原文层作为第一批完成目标；
6. 不修改 `code/specs_validate.py v2-check` 的兼容输出，除非同一提交补充测试、文档和下游影响说明。

## 4. 目标模块边界

实现应按以下模块边界推进：

| 模块或入口 | 目标职责 | 不负责 |
|---|---|---|
| `code/spec_checks/v2.py` | 保持 active specs 诊断和 `v2-check` CLI 兼容编排 | 长期承载全部知识地图和 preflight 逻辑 |
| `code/spec_checks/knowledge_map.py` | 知识地图节点、边、source refs、input scope、query layer 和 degraded 诊断的只读投影核心 | 写入事实源、持久缓存、Web UI |
| `code/spec_checks/preflight.py` | 受控写入前检查的只读诊断核心 | 实际写入执行、Human 授权、Git commit 创建 |
| `code/specs_validate.py` | CLI 参数解析、兼容命令调度和聚合入口 | 复杂规则主体 |
| `tests/code/specs_validate_checks/` | 知识地图、preflight 和兼容入口测试 | specs 正文或长期事实源 |

若第一轮只做无行为变化提取，可以先让 `v2-check` 继续调用原有输出结构；新增 CLI 必须等模块、测试和命令边界稳定后再登记。

## 5. 知识地图实现阶段

| 阶段 | 内容 | 验收 |
|---|---|---|
| KM-1 基线固化 | 增补测试记录当前 `v2-check` JSON/text 输出、query layer、input scope 和 degraded 行为 | 行为不变，现有测试通过 |
| KM-2 核心提取 | 从 `v2.py` 提取节点、边、source refs、edge id、诊断和查询过滤到 `knowledge_map.py` | `v2-check` 输出兼容，模块级测试覆盖 |
| KM-3 Schema 对齐 | 补齐 04.Att.06 要求的顶层字段、节点字段、边字段和来源回指缺口 | 缺失能力用 `degraded` 或 `diagnostics` 明示 |
| KM-4 范围约束 | 明确 `specs_v2`、`history_specs_v1`、`governed_projects`、`git_history`、排除输入和禁止输入的处理 | 后置范围返回诊断，不静默伪装支持 |
| KM-5 CLI 收敛 | 评估是否新增 `knowledge-map` 子命令，或继续以 `v2-check` 暴露只读预览 | 若新增命令，再更新 04.Att.02 和测试 |

`specs_v2` 名称虽然保留历史痕迹，但当前含义是 active `specs/` 输入。若后续改名为 `active_specs`，必须提供兼容别名和迁移提示。

## 6. Preflight 实现阶段

| 阶段 | 内容 | 验收 |
|---|---|---|
| PF-1 输入合同草案 | 定义 operation、target path、可选 object type、field path、status、source refs 和 output format | 只作为实现合同，不改变正式规范 |
| PF-2 路径与位置检查 | 判断目标路径是否落在 specs、attachments、code、web、runtime extension、tests 或事实源授权位置 | 输出通过、阻断或需 Human Gate 的诊断 |
| PF-3 字段与状态检查 | 针对已知事实模型、规范身份块、附件身份块和 Code 文档边界做只读检查 | 不完整能力用 degraded 明示 |
| PF-4 Gate 与追溯提示 | 暴露 Human Gate、Git 追溯、同步影响和失败归口 | 检查通过仍不授权写入 |
| PF-5 CLI 登记 | 新增稳定 preflight 子命令并更新 04.Att.02、04.Att.09、08.Att.05 和 Code 文档 | 命令、测试、文档同批提交 |

preflight 输出应优先给出机器可消费诊断，同时保留 Human 可读摘要。任何输出都必须声明 `write_authorized: false` 或等价语义，避免 AI 把通过检查误解为写入许可。

## 7. 测试计划

测试按以下层次补齐：

| 测试层 | 覆盖点 |
|---|---|
| 兼容入口测试 | `v2-check` text/json、exit code、`--fail-on-diagnostics` 和既有参数保持兼容 |
| 知识地图模块测试 | 节点、边、关系类型、source refs、input scope、query layer、degraded 诊断 |
| preflight 模块测试 | 授权位置、禁止位置、字段缺失、状态异常、Human Gate 提示、Git 追溯提示、失败归口 |
| 回归入口 | `npm run test:code`、`python3 code/specs_validate.py v2-check --fail-on-diagnostics --format text`、`git diff --check` |

局部测试可以用于开发过程，但提交前不得替代完整 Code 验证入口。

## 8. 提交切分

推荐按以下提交推进：

1. 计划提交：只新增本文和必要的 Code 文档登记；
2. 基线测试提交：补当前 `v2-check` 行为测试，不改实现；
3. 知识地图核心提取提交：无行为变化拆分；
4. 知识地图 Schema 对齐提交：补字段和降级诊断；
5. preflight 模块提交：只读诊断核心和测试；
6. preflight CLI 提交：新增命令、帮助、命令表和回归入口；
7. 文档收口提交：清理 TODO、更新 Code 结构文档和必要附件。

若某一步需要改变输出结构、诊断码、输入范围或 CLI 参数，应单独提交，不与无行为变化重构混合。

## 9. 待确认事项

1. 是否在实现稳定后把 `specs_v2` 增加 `active_specs` 兼容别名；
2. preflight 输出状态是否采用 `pass`、`blocked`、`needs_human_gate`、`degraded` 的闭集；
3. 第一版 preflight 是否只面向 LDVH 产品资产，管辖项目事实源留到 v2 正式生效后；
4. 是否在 Web 介入前先提供只读 JSON 输出，供 AI 和 CLI 消费。

## 10. 实施记录

| 日期 | 阶段 | 结果 | 验证 |
|---|---|---|---|
| 2026-06-23 | KM-1 基线固化 | 已补充当前 `v2-check` JSON/text 输出、relation type 过滤、raw 降级、start node 回退和非法参数诊断测试；未改变实现行为 | `python3 -m pytest tests/code/specs_validate_checks/test_v2.py -q`、`npm run test:code` |
| 2026-06-23 | KM-2 核心提取 | 已将知识地图节点、边、source refs、查询层、降级投影和关系过滤提取到 `code/spec_checks/knowledge_map.py`；`v2-check` CLI 兼容入口保持不变 | `python3 -m pytest tests/code/specs_validate_checks/test_v2.py -q` |
| 2026-06-23 | KM-3 Schema 对齐 | 已在 `knowledge_map` 输出中补齐 `schema_version`、`generated_at`、`tool`、`input_scope`、`degraded`、`diagnostics`、`source_refs`，并统一节点基础字段 | `python3 -m pytest tests/code/specs_validate_checks/test_v2.py -q` |
