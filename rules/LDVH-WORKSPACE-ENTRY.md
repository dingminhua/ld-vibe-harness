# LDVH 工作区入口

```yaml
ldvh_asset:
  id: "ldvh-workspace-entry"
  type: "rule"
  status: "active"
  canonical_path: "rules/LDVH-WORKSPACE-ENTRY.md"
  source_specs:
    - "specs/01-规范体系基础规范.md"
    - "specs/02-事实模型基础规范.md"
    - "specs/04-Code确定性执行规范.md"
    - "specs/06-运行时扩展规范.md"
    - specs/30-rules-entry-sync-review-Rules入口同步审查.md
    - specs/attachments/06.Att.02-固定运行时扩展登记表.md
    - "specs/07-事实源边界与Git追溯规范.md"
    - specs/31-git-commit-action-Git提交行动编排.md
  consumption_scenarios:
    - "工作区级管辖项目识别"
    - "管辖项目工作对象处理"
    - "LDVH dogfood 管辖判断"
    - "知识地图任务导航和 Rules 入口同步审查"
  inputs:
    - "LDVH-GOVERNED-PROJECTS.yaml"
    - "当前工作目录"
    - "用户任务目标"
  outputs:
    - "最小读取顺序"
    - "场景路由"
    - "STOP 点"
    - "知识地图任务导航入口"
  handoff: "命中 LDVH 产品资产维护时交还 rules/LDVH-MAINTAINER-ENTRY.md"
  verification:
    - "python3 code/specs_validate.py governed-projects"
    - "python3 code/specs_validate.py knowledge-map --input-scope entry_navigation --layer neighbors --start-node rules/LDVH-WORKSPACE-ENTRY.md --task-type workspace_entry --format text"
    - "python3 code/specs_validate.py deployment-entries"
    - "python3 code/specs_validate.py capability-environment"
    - "python3 code/specs_validate.py v2-check --input-scope entry_navigation --fail-on-diagnostics --format text"
  sync_triggers:
    - "source_specs 中任一 active 规范发生入口职责、事实源边界、Human Gate、Code 诊断、知识地图输入或知识地图任务导航触发条件变化"
    - "管辖项目配置规则变化"
    - "工作区入口职责变化"
    - "环境入口适配或薄引用规则变化"
    - "固定运行时扩展登记规则变化"
  deprecation: "废弃、重命名或合并工作区入口前必须评估 Human Gate，并同步 01、02、04、06、07、30 和 Code 检查。"
```

> 文件性质：工作区级 Rules 入口资产，不是 specs 正式规范或最终事实源
> 规范来源：`specs/01-规范体系基础规范.md`、`specs/02-事实模型基础规范.md`、`specs/04-Code确定性执行规范.md`、`specs/06-运行时扩展规范.md`、`specs/30-rules-entry-sync-review-Rules入口同步审查.md`、`specs/attachments/06.Att.02-固定运行时扩展登记表.md`、`specs/07-事实源边界与Git追溯规范.md`、`specs/31-git-commit-action-Git提交行动编排.md`
> 适用范围：安装或使用 LDVH 的工作区级入口、管辖项目识别、管辖项目工作对象处理和 dogfood 管辖判断

---
## 1. 这个文件是什么

这个文件用于工作区级薄入口。它告诉 AI：当前工作区是否使用 LDVH、LDVH 管哪些项目、如何进入管辖项目的事实源和工作对象。

它不是最终事实源。正式规则以 `specs/` 为准，管辖项目清单以工作区根目录 `LDVH-GOVERNED-PROJECTS.yaml` 为准，环境入口适配、部署和检查方法以 `specs/06-运行时扩展规范.md` 为准。

本文可以指向 Code 知识地图投影，帮助 AI 定位 active specs、固定运行时扩展、来源回指、读取建议和同步影响；但不得缓存、复制或改写知识地图输出，也不得把知识地图当成事实源。

环境入口、项目规则、工作区配置或会话提示只应通过薄引用措施指向本文件，不应复制本文正文或 specs 正文。薄引用正文只应包含入口指向、压缩或恢复后的重读提示，以及 LDVH 管理段开始和结束标记。当前固定运行时扩展登记见 `specs/attachments/06.Att.02-固定运行时扩展登记表.md`。

---
## 2. 入口职责

工作区入口负责管辖治理，不负责维护 LDVH 产品资产。

| 负责 | 不负责 |
|---|---|
| 读取工作区根目录 `LDVH-GOVERNED-PROJECTS.yaml` | 默认维护 LDVH 自身 `specs/`、`rules/`、`code/`、`web/` 等产品资产 |
| 判断当前项目是否为管辖项目 | 把 LDVH 自身开发规则强加给用户项目 |
| 定位管辖项目自身 `ldvh-base/`、项目文档和 Git 事实源 | 默认接管、创建、迁移或重排用户项目 docs |
| 指向知识地图和 Code 投影以辅助入口导航、读取建议和影响判断 | 把知识地图投影写成运行时事实源或替代 active specs |
| 处理所有管辖项目的 WorkCase、ADR、Spark、Pitfall 和 Study，并按 Git 提交记录追溯事实源修改 | 把工作区环境入口写成长期安装状态 |
| 在 LDVH 自身被登记为 dogfood 管辖项目时，处理 LDVH 自身 `ldvh-base/` 工作对象 | 把 LDVH 安装用户的 LDVH 仓库默认视为管辖项目 |

`ldvh-base/` 不因为位于 LDVH 仓库内就属于 LDVH 项目级维护入口。它始终是被管辖项目的工作对象事实源，归工作区级管辖治理入口处理；LDVH 自身源码仓库只有在 `LDVH-GOVERNED-PROJECTS.yaml` 中登记为 dogfood 管辖项目时，才按管辖项目处理其 `ldvh-base/`。

若任务目标是维护 LDVH 产品资产，例如修改 `specs/`、`rules/`、`skills/`、`agents/`、`hooks/`、`code/`、`tests/` 或 `web/`，应转入 `rules/LDVH-MAINTAINER-ENTRY.md`。

---
## 3. 最小启动顺序

AI 进入工作区入口后，应按以下顺序启动：

1. 定位当前工作区根目录；
2. 读取 `LDVH-GOVERNED-PROJECTS.yaml`，确认文件存在、结构有效并理解 `product_name` 与 `product_description`；
3. 选择最小 `start_node`：默认用 `rules/LDVH-WORKSPACE-ENTRY.md`；用户点名项目、文件、WorkCase/ADR/Spark/Pitfall/Study 或变化来源时，优先用被点名对象；
4. 选择 `task_type`：工作区入口用 `workspace_entry`，管辖判断用 `governed_project_check`，工作对象处理用 `work_object`，Rules 同步用 `rules_sync_review`，Git 追溯用 `git_trace`；
5. 运行 `python3 code/specs_validate.py knowledge-map --input-scope entry_navigation --layer neighbors --start-node <path-or-node> --task-type <task_type> --format json` 建立任务视图；
6. 先消费 `navigation`、`read_plan`、`next_queries`、`stop_conditions` 和 `impact_summary`：只读取 P0/P1 的权威原文，P2/P3 按任务需要展开；若输出要求追加查询，按 `next_queries` 渐进展开；
7. 判断当前目录或用户目标是否命中某个 `projects[].path`；命中后按该项目自身事实源工作，未命中时不得静默接管；
8. 涉及工作对象准入、状态流转、关闭、长期能力缺口、项目清单修改或用户文档写入时，回到对应 specs、工作对象事实源和 Human Gate。

常用查询命令如下：

| 查询目标 | 优先命令 | 用途 |
|---|---|---|
| Code 依赖自举 | `python3 code/bootstrap_code.py` | 在新环境缺少 `PyYAML` 或 `pytest` 时安装 Code 与 Code 测试 Python 依赖；不安装 Web 依赖，不声明环境完整支持 LDVH |
| 管辖项目配置 | `python3 code/specs_validate.py governed-projects` | 检查工作区根目录管辖项目配置 |
| specs 汇总健康检查 | `python3 code/specs_validate.py v2-check --format text` | 生成 active specs 结构诊断和知识地图汇总预览；不得替代具体任务导航 |
| 知识地图任务导航 | `python3 code/specs_validate.py knowledge-map --input-scope entry_navigation --layer neighbors --start-node <path-or-node> --task-type <task_type> --format json` | 围绕具体规范、附件、行动成员、Rules 入口、管辖项目、工作对象或承载物生成 `read_plan`、后续查询、STOP 和影响摘要 |
| 固定运行时扩展自描述 | `python3 code/specs_validate.py v2-check --input-scope runtime_extensions --format text` | 只读投影固定运行时扩展 `ldvh_asset`，用于入口、来源规范和同步触发定位 |
| 能力资产环境保障矩阵 | `python3 code/specs_validate.py capability-environment` | 只读投影固定能力资产的来源规范、同步责任、验证链和环境落地边界；不声明环境已安装 |
| 工作对象列表 | `python3 code/fact_cli.py list <type>` | 查询当前项目 WorkCase、ADR、Spark、Pitfall 或 Study 摘要 |
| 工作对象详情 | `python3 code/fact_cli.py show <id>` | 查询单个工作对象详情 |
| 工作对象搜索 | `python3 code/fact_cli.py search <keyword>` | 按关键词搜索工作对象事实源 |
| 工作对象统计 | `python3 code/fact_cli.py stats` | 统计工作对象状态分布 |
| Rules 环境入口接入 | 按 `specs/06-运行时扩展规范.md` §4.1-§4.4 执行 | 官方维护 Codex App 适配路径；默认只生成可复制的 Codex 薄入口文本，由用户自行加入环境规则入口 |

工具输出、知识地图投影和读取建议只作为导航、聚合和诊断结果，不替代权威文件原文。当工具不可用、输出无法回指事实源、结果与原文冲突或当前场景超出工具能力时，应报告问题原因，并退回 Git 文件事实源、对应规范和临时核对动作。若 active specs、工作对象事实源、Rules 入口和知识地图投影冲突，优先级为 active specs 与 Git 文件事实源、工作对象事实源、Rules 入口、知识地图投影。

不得用 `ls`、全文 Read 或只查看 `v2-check` 摘要替代知识地图任务导航。手工文件读取只能用于核对知识地图 `read_plan` 定位出的权威原文，或在工具不可用、输出不足、来源缺失或事实冲突后按本文说明的事实源顺序执行临时核对动作。

本文承载的入口表达只包括：入口判断、场景路由、最小读取、STOP 点、工具导航、交接、缺口提示和来源规范回指。知识地图入口只能表现为 Code 命令、读取建议和影响判断，不得在本文内展开或固化图谱内容。

按 active `specs/30-rules-entry-sync-review-Rules入口同步审查.md`，active specs、附件或行动成员主文件变化若影响本文的入口路由、最小读取、STOP、工具入口、交接、验证、缺口提示、知识地图任务导航、知识地图入口或 Code 检查入口含义，应转入维护入口执行 Rules 入口同步审查。普通文案澄清、路径错字或不改变入口行为的读取建议调整，可在说明依据并完成验证后处理；修改职责边界、STOP、`source_specs`、`sync_triggers`、canonical path、固定承载物身份、权限含义或环境薄引用前，必须评估 Human Gate。

---
## 4. 任务类型与起点

| 场景 | `task_type` | 默认 `start_node` | 问题分流 |
|---|---|---|---|
| 工作区入口理解 | `workspace_entry` | `rules/LDVH-WORKSPACE-ENTRY.md` | 本文、`LDVH-GOVERNED-PROJECTS.yaml` 和 `source_specs` |
| 判断当前是否为管辖项目 | `governed_project_check` | `LDVH-GOVERNED-PROJECTS.yaml` 或当前项目路径 | `governed-projects`、Human Gate |
| 处理管辖项目工作对象 | `work_object` | 目标 WorkCase/ADR/Spark/Pitfall/Study 路径或对象 ID | `fact_cli.py show/list/search/stats` 和对应事实源原文 |
| 处理管辖项目 Git 提交记录或提交准备 | `git_trace` | 目标工作对象、变化文件或提交范围 | 31、Git commit records 和 07 |
| 判断 specs 变化是否影响固定 Rules 入口表达 | `rules_sync_review` | 变化来源文件或受影响 Rules 入口 | 转入维护入口并按 active 30 执行 |
| 维护 LDVH 产品资产 | `rules_entry` | `rules/LDVH-MAINTAINER-ENTRY.md` 或用户点名资产 | 转入 `rules/LDVH-MAINTAINER-ENTRY.md` |

场景同时命中多个入口时，先用最具体的用户点名对象作为 `start_node`。若知识地图 `read_plan` 给出 P0/P1 权威原文，应以该计划替代本文的静态读取猜测；本文只保留管辖判断、起点选择、任务类型、STOP 和问题分流规则。

---
## 5. STOP 点

出现以下情况时，AI 应暂停并说明需要 Human 确认：

1. `LDVH-GOVERNED-PROJECTS.yaml` 缺失、格式异常或无法定位目标管辖项目；
2. 要新增、删除或修改管辖项目条目；
3. 要创建、删除、移动或重命名管辖项目 `ldvh-base/` 中的工作对象事实源目录；
4. 要写入、覆盖或删除工作区级入口、环境入口、项目规则或等价配置；
5. 要为管辖项目创建环境入口或项目级 AI 指令；
6. 要默认接管、创建、迁移、重排或强制校验用户项目 docs；
7. 要把 LDVH 自身 dogfood 条目解释为用户安装 LDVH 后的默认管辖项目；
8. 要声明任一环境完整支持 LDVH，或把一次本地适配检查结果写成环境类型结论；
9. 入口内容与 specs 正式规范、管辖项目配置、工作对象事实或 Code 校验结果冲突。
10. 要修改本文职责边界、STOP、入口交接、`source_specs`、`sync_triggers`、canonical path、固定承载物身份、权限含义或环境薄引用。

---
## 6. 维护规则

修改本文后，应检查：

1. 运行 `python3 code/specs_validate.py knowledge-map --input-scope entry_navigation --layer neighbors --start-node rules/LDVH-WORKSPACE-ENTRY.md --task-type rules_sync_review --format text`，确认 `read_plan`、`next_queries` 和 `stop_conditions`；
2. 按 `read_plan` P0/P1 回读权威原文，必要时执行 `next_queries`，不得用本文维护静态 specs 清单替代；
3. 检查本文 `source_specs`、`sync_triggers`、入口路由、STOP 点、验证入口和交接规则是否仍与 30 和知识地图输出一致；
4. 运行 `python3 code/specs_validate.py governed-projects`、`python3 code/specs_validate.py deployment-entries`、`python3 code/specs_validate.py capability-environment` 和 `python3 code/specs_validate.py v2-check --input-scope entry_navigation --fail-on-diagnostics --format text`；
5. 若改变职责边界、STOP、入口交接、固定承载物身份、权限含义、项目清单或环境薄引用，必须评估 Human Gate。
