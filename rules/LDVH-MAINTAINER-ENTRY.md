# LDVH 维护入口

```yaml
ldvh_asset:
  id: "ldvh-maintainer-entry"
  type: "rule"
  status: "active"
  canonical_path: "rules/LDVH-MAINTAINER-ENTRY.md"
  source_specs:
    - "specs/01-规范体系基础规范.md"
    - "specs/04-Code确定性执行规范.md"
    - "specs/06-运行时扩展规范.md"
    - specs/30-rules-entry-sync-review-Rules入口同步审查.md
    - specs/attachments/06.Att.02-固定运行时扩展登记表.md
    - "specs/07-事实源边界与Git追溯规范.md"
    - specs/31-git-commit-action-Git提交行动编排.md
    - "specs/08-测试基础规范.md"
  consumption_scenarios:
    - "LDVH 产品资产维护"
    - "specs、rules、skills、agents、hooks、code、tests、web 修改入口"
    - "能力资产漂移判断"
    - "知识地图任务导航和 Rules 入口同步审查"
  inputs:
    - "用户维护目标"
    - "LDVH 仓库文件事实源"
    - "Code 校验输出"
  outputs:
    - "产品资产维护最小读取顺序"
    - "维护场景路由"
    - "STOP 点"
    - "知识地图任务导航入口"
  handoff: "处理管辖项目工作对象时交还 rules/LDVH-WORKSPACE-ENTRY.md"
  verification:
    - "python3 code/specs_validate.py v2-check --fail-on-diagnostics --format text"
    - "python3 code/specs_validate.py knowledge-map --input-scope entry_navigation --layer neighbors --start-node rules/LDVH-MAINTAINER-ENTRY.md --task-type rules_entry --format text"
    - "python3 code/specs_validate.py v2-check --input-scope entry_navigation --fail-on-diagnostics --format text"
    - "python3 code/specs_validate.py all --fail-on-diagnostics"
    - "python3 code/specs_validate.py deployment-entries"
    - "python3 code/specs_validate.py capability-environment"
  sync_triggers:
    - "source_specs 中任一 active 规范发生入口职责、Human Gate、Code 诊断、知识地图输入、知识地图任务导航触发条件、Git 追溯或运行时扩展边界变化"
    - "LDVH 产品资产目录边界变化"
    - "固定运行时扩展登记规则变化"
    - "环境入口适配或部署规则变化"
    - "Git 提交规范、Git 提交行动编排或事实源追溯规则变化"
  deprecation: "废弃、重命名或合并维护入口前必须评估 Human Gate，并同步 01、06、30、工作区入口和 Code 检查。"
```

> 文件性质：LDVH 项目级 Rules 入口资产，不是 specs 正式规范或最终事实源
> 规范来源：`specs/01-规范体系基础规范.md`、`specs/04-Code确定性执行规范.md`、`specs/06-运行时扩展规范.md`、`specs/30-rules-entry-sync-review-Rules入口同步审查.md`、`specs/attachments/06.Att.02-固定运行时扩展登记表.md`、`specs/07-事实源边界与Git追溯规范.md`、`specs/31-git-commit-action-Git提交行动编排.md`、`specs/08-测试基础规范.md`
> 适用范围：维护 LDVH 自身产品资产时的项目级入口

---
## 1. 这个文件是什么

这个文件用于 LDVH 源码仓库的项目级薄入口。它告诉 AI：进入 `ld-vibe-harness` 仓库维护 LDVH 产品资产时，先查什么、如何判断事实源、何时暂停。

它不是最终事实源。正式规则以 `specs/` 为准，运行时扩展原则以 `specs/06-运行时扩展规范.md` 为准，固定运行时扩展登记以 `specs/attachments/06.Att.02-固定运行时扩展登记表.md` 为准，环境入口适配、部署和检查方法以 `specs/06-运行时扩展规范.md` 为准。

本文可以指向 Code 知识地图投影，帮助 AI 定位 active specs、固定运行时扩展、来源回指、读取建议、影响范围和同步风险；但不得缓存、复制或改写知识地图输出，也不得把知识地图当成事实源。

环境入口、项目规则、工作区配置或会话提示只应通过薄引用措施指向本文件，不应复制本文正文或 specs 正文。薄引用正文只应包含入口指向、压缩或恢复后的重读提示，以及 LDVH 管理段开始和结束标记。

---
## 2. 入口职责

LDVH 维护入口负责产品资产维护，不负责管辖项目工作对象治理。

| 负责 | 不负责 |
|---|---|
| 维护 `specs/` 正式规范 | 直接处理任何项目的 `ldvh-base/` 工作对象 |
| 维护 `rules/`、`skills/`、`agents/`、`hooks/` 文本能力资产 | 判断工作区中哪些项目被 LDVH 管辖 |
| 维护 `code/`、`tests/`、`web/` 参考实现和验证 | 把 LDVH 源码仓库默认登记为安装用户的管辖项目 |
| 维护 README、目录结构、规范索引和能力资产边界 | 默认接管用户项目文档或项目级入口 |
| 指向知识地图和 Code 投影以辅助规范定位、影响判断和同步审查 | 把知识地图投影写成运行时事实源或替代 active specs |
| 判断 LDVH 产品资产与正式规范、Code 校验、Web 展示之间是否漂移 | 把工作对象事实源当成产品资产目录 |

`ldvh-base/` 始终是被管辖项目的工作对象事实源。即使它位于 LDVH 源码仓库内，也应通过工作区级 `rules/LDVH-WORKSPACE-ENTRY.md` 和 `LDVH-GOVERNED-PROJECTS.yaml` 判断后处理。

若工作目标是处理 WorkCase、ADR、Spark、Pitfall 或 Study 等工作对象，应转入 `rules/LDVH-WORKSPACE-ENTRY.md`；若目标是追溯事实源修改，应读取 Git commit records 和 `specs/07-事实源边界与Git追溯规范.md`。

---
## 3. 最小启动顺序

AI 进入 LDVH 维护入口后，应按以下顺序启动：

1. 确认当前任务是否维护 LDVH 产品资产；
2. 选择最小 `start_node`：默认用 `rules/LDVH-MAINTAINER-ENTRY.md`；用户点名文件、变化来源、目标规范、行动成员、Rules 入口或 Code 文件时，优先用被点名对象；
3. 选择 `task_type`：入口理解用 `rules_entry`，规范修改用 `spec_change`，Rules 同步用 `rules_sync_review`，Code 修改用 `code_change`，Web 修改用 `web_change`，Git 提交准备用 `git_trace`；
4. 运行 `python3 code/specs_validate.py knowledge-map --input-scope entry_navigation --layer neighbors --start-node <path-or-node> --task-type <task_type> --format json` 建立任务视图；
5. 先消费 `navigation`、`read_plan`、`next_queries`、`stop_conditions` 和 `impact_summary`：只读取 `read_plan` 中 P0/P1 的权威原文，P2/P3 仅在当前判断需要时展开；若 `next_queries` 要求 expand 或换范围，按其建议追加查询；
6. 若知识地图工具不可用、输出不足、无来源回指、起点无法定位或与原文冲突，说明问题原因，并退回 active specs、产品资产文件、Rules 入口、07 Git 文件事实源和临时核对动作；
7. 修改前按任务目标运行必要的 `preflight`、`deployment-entries`、`capability-environment`、`v2-check` 或测试；修改后运行对应校验命令，并把稳定结论写回权威事实源。

常用查询命令如下：

| 查询目标 | 优先命令 | 用途 |
|---|---|---|
| Code 依赖自举 | `python3 code/bootstrap_code.py` | 在新环境缺少 `PyYAML` 或 `pytest` 时安装 Code 与 Code 测试 Python 依赖；不安装 Web 依赖，不声明环境完整支持 LDVH |
| specs 汇总健康检查 | `python3 code/specs_validate.py v2-check --format text` | 生成 active specs 结构诊断和知识地图汇总预览；不得替代具体任务导航 |
| 知识地图任务导航 | `python3 code/specs_validate.py knowledge-map --input-scope entry_navigation --layer neighbors --start-node <path-or-node> --task-type <task_type> --format json` | 围绕具体规范、附件、行动成员、Rules 入口、工作对象或承载物生成 `read_plan`、后续查询、STOP 和影响摘要 |
| 固定运行时扩展自描述 | `python3 code/specs_validate.py v2-check --input-scope runtime_extensions --format text` | 只读投影固定运行时扩展 `ldvh_asset`，辅助定位 Rules/Skill/Hook 来源规范和同步影响 |
| 能力资产环境保障矩阵 | `python3 code/specs_validate.py capability-environment` | 只读投影固定能力资产的来源规范、同步责任、验证链和环境落地边界；不声明环境已安装 |
| specs 写入前检查 | `python3 code/specs_validate.py preflight --target-path <path>` | 只读提示 Human Gate、Git 追溯、同步影响和固定 Rules 资产影响；不授权写入 |
| specs 综合检查 | `python3 code/specs_validate.py all --fail-on-diagnostics` | 执行 active specs 综合校验 |
| LDVH Git 提交准备 | `specs/31-git-commit-action-Git提交行动编排.md`、`ldvh-git-commit` Skill、`python3 code/commit_validate.py --check-message-file <message-file>` | 按 31 的行动流程和 07 的 commit message 契约拆分、编写、预检并创建提交 |
| Rules 环境入口接入 | 按 `specs/06-运行时扩展规范.md` §7 执行 | LDVH 提供插件方式和 Rules 方式两种接入方式；按目标环境 AI Hook 能力生成对应入口文本，由用户自行加入环境规则入口 |

工具输出、知识地图投影和读取建议只作为导航、聚合和诊断结果，不替代权威文件原文。当工具不可用、输出无法回指事实源、结果与原文冲突或当前场景超出工具能力时，应报告问题原因，并退回 Git 文件事实源、对应规范和临时核对动作。若 active specs、产品资产文件、Rules 入口和知识地图投影冲突，优先级为 active specs 与 Git 文件事实源、产品资产文件、Rules 入口、知识地图投影。

不得用 `ls`、全文 Read 或只查看 `v2-check` 摘要替代知识地图任务导航。手工文件读取只能用于核对知识地图 `read_plan` 定位出的权威原文，或在工具不可用、输出不足、来源缺失或事实冲突后按本文说明的事实源顺序执行临时核对动作。

本文承载的入口表达只包括：入口判断、场景路由、最小读取、STOP 点、工具导航、交接、缺口提示和来源规范回指。知识地图入口只能表现为 Code 命令、读取建议和影响判断，不得在本文内展开或固化图谱内容。

按 active `specs/30-rules-entry-sync-review-Rules入口同步审查.md`，active specs、附件或行动成员主文件变化若影响固定 Rules 的入口路由、最小读取、STOP、工具入口、交接、验证、缺口提示、知识地图任务导航、知识地图入口或 Code 检查入口含义，应执行 Rules 入口同步审查。普通文案澄清、路径错字或不改变入口行为的读取建议调整，可在说明依据并完成验证后处理；修改职责边界、STOP、`source_specs`、`sync_triggers`、canonical path、固定承载物身份、权限含义或环境薄引用前，必须评估 Human Gate。

---
## 4. 任务类型与起点

| 场景 | `task_type` | 默认 `start_node` | 问题分流 |
|---|---|---|---|
| 理解或修改维护入口 | `rules_entry` | `rules/LDVH-MAINTAINER-ENTRY.md` | 本文、`source_specs` 和固定运行时扩展登记 |
| 修改 specs、附件或行动成员 | `spec_change` | 用户点名文件或变化来源文件 | 目标原文、01、04、06、07 和 `preflight` |
| 判断 Rules 同步影响 | `rules_sync_review` | 变化来源文件；不明确时用受影响 Rules 入口 | 30、06 §4.2、受影响 Rules 原文和临时核对动作 |
| 修改 Code 或测试 | `code_change` | 目标 Code / test 文件 | 04、08、对应测试命令和工具帮助 |
| 修改 Web 或 Human-facing 入口 | `web_change` | 目标 Web / API / 文档文件 | 05、08 和相关 Web 校验 |
| 准备 Git 提交或追溯事实源 | `git_trace` | 变化文件或提交范围 | 31、07、commit records、`commit_validate.py` |
| 处理 LDVH 自身工作对象 | `work_object` | 目标 WorkCase/ADR/Spark/Pitfall/Study | 转入 `rules/LDVH-WORKSPACE-ENTRY.md` |

场景同时命中多个入口时，先用最具体的用户点名对象作为 `start_node`。若知识地图 `read_plan` 给出 P0/P1 权威原文，应以该计划替代本文的静态读取猜测；本文只保留起点选择、任务类型、STOP 和问题分流规则。

---
## 5. STOP 点

出现以下情况时，AI 应暂停并说明需要 Human 确认：

1. 要创建、删除、移动或重命名 `rules/LDVH-WORKSPACE-ENTRY.md` 或 `rules/LDVH-MAINTAINER-ENTRY.md`；
2. 要改变 `specs/`、`docs/`、`rules/`、`skills/`、`agents/`、`hooks/`、`code/`、`tests/` 或 `web/` 的定位；
3. 要修改工作区级入口、环境入口、项目规则或等价配置；
4. 要声明任一环境完整支持 LDVH，或把一次本地适配检查结果写成环境类型结论；
5. 要把 LDVH 项目级维护入口用于默认处理管辖项目工作对象；
6. 要接受长期能力缺口、关闭关键缺口、绕过 Human Gate 或改变事实源边界；
7. 入口内容与 specs 正式规范、固定运行时扩展登记、Code 校验结果或工作区入口冲突。
8. 要修改本文职责边界、STOP、入口交接、`source_specs`、`sync_triggers`、canonical path、固定承载物身份、权限含义或环境薄引用。

---
## 6. 维护规则

修改本文后，应检查：

1. 运行 `python3 code/specs_validate.py knowledge-map --input-scope entry_navigation --layer neighbors --start-node rules/LDVH-MAINTAINER-ENTRY.md --task-type rules_sync_review --format text`，确认 `read_plan`、`next_queries` 和 `stop_conditions`；
2. 按 `read_plan` P0/P1 回读权威原文，必要时执行 `next_queries`，不得用本文维护静态 specs 清单替代；
3. 检查本文 `source_specs`、`sync_triggers`、入口路由、STOP 点、验证入口和交接规则是否仍与 30 和知识地图输出一致；
4. 运行 `python3 code/specs_validate.py deployment-entries`、`python3 code/specs_validate.py capability-environment` 和 `python3 code/specs_validate.py v2-check --input-scope entry_navigation --fail-on-diagnostics --format text`；
5. 若改变职责边界、STOP、入口交接、固定承载物身份或环境薄引用，必须评估 Human Gate。

> **已废弃**: 合并为 [rules/LDVH-ENTRY.md](LDVH-ENTRY.md)。本文不再作为独立入口使用。
