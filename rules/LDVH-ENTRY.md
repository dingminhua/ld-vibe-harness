# LDVH 入口

```yaml
ldvh_asset:
  id: "ldvh-entry"
  type: "rule"
  status: "active"
  canonical_path: "rules/LDVH-ENTRY.md"
  source_specs:
    - "specs/01-规范体系基础规范.md"
    - "specs/02-事实模型基础规范.md"
    - "specs/04-Code确定性执行规范.md"
    - "specs/06-运行时扩展规范.md"
    - specs/30-rules-entry-sync-review-Rules入口同步审查.md
    - specs/attachments/06.Att.02-固定运行时扩展登记表.md
    - "specs/07-事实源边界与Git追溯规范.md"
    - specs/31-git-commit-action-Git提交行动编排.md
    - "specs/08-测试基础规范.md"
  consumption_scenarios:
    - "LDVH 统一入口：管辖项目工作对象处理 + LDVH 产品资产维护"
    - "工作区级管辖项目识别"
    - "知识地图任务导航和 Rules 入口同步审查"
    - "能力资产漂移判断"
  inputs:
    - "LDVH-GOVERNED-PROJECTS.yaml"
    - "当前工作目录"
    - "用户任务目标"
    - "Code 校验输出"
  outputs:
    - "场景路由"
    - "STOP 点"
    - "知识地图任务导航入口"
  verification:
    - "python3 code/specs_validate.py governed-projects"
    - "python3 code/specs_validate.py knowledge-map --input-scope entry_navigation --layer neighbors --start-node rules/LDVH-ENTRY.md --task-type rules_entry --format text"
    - "python3 code/specs_validate.py deployment-entries"
    - "python3 code/specs_validate.py capability-environment"
    - "python3 code/specs_validate.py v2-check --input-scope entry_navigation --fail-on-diagnostics --format text"
    - "python3 code/specs_validate.py all --fail-on-diagnostics"
  sync_triggers:
    - "source_specs 中任一 active 规范发生入口职责、Human Gate、Code 诊断、知识地图输入、知识地图任务导航触发条件、事实源边界、Git 追溯或运行时扩展边界变化"
    - "管辖项目配置规则变化"
    - "LDVH 产品资产目录边界变化"
    - "固定运行时扩展登记规则变化"
    - "环境入口适配、部署规则或薄引用规则变化"
    - "Git 提交规范、Git 提交行动编排或事实源追溯规则变化"
  deprecation: "废弃、重命名或合并本入口前必须评估 Human Gate，并同步 01、02、04、06、07、08、30、AGENTS.md 和 Code 检查。"
```

> 文件性质：LDVH 统一 Rules 入口资产，不是 specs 正式规范或最终事实源
> 合并自：`rules/LDVH-WORKSPACE-ENTRY.md`（管辖治理）+ `rules/LDVH-MAINTAINER-ENTRY.md`（产品资产维护）
> 规范来源：`specs/01-规范体系基础规范.md`、`specs/02-事实模型基础规范.md`、`specs/04-Code确定性执行规范.md`、`specs/06-运行时扩展规范.md`、`specs/30-rules-entry-sync-review-Rules入口同步审查.md`、`specs/attachments/06.Att.02-固定运行时扩展登记表.md`、`specs/07-事实源边界与Git追溯规范.md`、`specs/31-git-commit-action-Git提交行动编排.md`、`specs/08-测试基础规范.md`

---

## 1. 这个文件是什么

LDVH 统一入口。它告诉 AI：进入 LDVH 后先读什么、如何判断职责对象、如何获取知识地图导航、何时暂停。

职责分两类，由入口路由到不同场景：

| 职责对象 | 典型任务 |
|---|---|
| 管辖项目工作对象 | 处理 WorkCase、ADR、Spark、Pitfall、Study；追溯 Git 事实源 |
| LDVH 产品资产 | 修改 specs、rules、skills、agents、hooks、code、tests、web；判断能力资产漂移 |

正式规则以 `specs/` 为准，管辖项目清单以 `LDVH-GOVERNED-PROJECTS.yaml` 为准。本文可指向知识地图投影辅助定位和影响判断，但不得缓存、复制或改写其输出。

环境入口只应通过薄引用指向本文，薄引用正文只含入口指向、压缩恢复重读提示和管理段标记。

---

## 2. 入口职责

| 负责 | 不负责 |
|---|---|
| 读取 `LDVH-GOVERNED-PROJECTS.yaml`，判断管辖项目 | 把 LDVH 自身开发规则强加给用户项目 |
| 处理管辖项目 `ldvh-base/` 工作对象（WorkCase/ADR/Spark/Pitfall/Study） | 默认接管、创建、迁移或重排用户项目 docs |
| 维护 LDVH `specs/`、`rules/`、`skills/`、`agents/`、`hooks/`、`code/`、`tests/`、`web/` | 把 LDVH 源码仓库默认登记为安装用户的管辖项目 |
| 判断产品资产与正式规范、Code 校验、Web 展示之间是否漂移 | 把知识地图投影写成运行时事实源 |
| 指向知识地图和 Code 投影辅助导航与影响判断 | 把工作对象事实源当成产品资产目录 |

`ldvh-base/` 始终是被管辖项目的工作对象事实源。即使它位于 LDVH 源码仓库内，也只在 `LDVH-GOVERNED-PROJECTS.yaml` 登记为 dogfood 管辖项目时才按管辖项目处理。

---

## 3. 最小启动顺序

AI 进入 LDVH 后：

1. 读取 `rules/LDVH-LIFECYCLE-PROTOCOL.md`，按协议步骤执行握手（session-start）。
2. 握手 receipt 返回后，按 `read_plan` P0/P1 读取权威原文。
3. 根据任务目标选择最小 `start_node`：默认用 `rules/LDVH-ENTRY.md`；用户点名文件时优先用被点名对象。
4. 根据职责对象选择 `task_type`（见 §4）。
5. 运行 `python3 code/specs_validate.py knowledge-map --input-scope entry_navigation --layer neighbors --start-node <path-or-node> --task-type <task_type> --format json` 建立任务视图。
6. 消费 `navigation`、`read_plan`、`next_queries`、`stop_conditions` 和 `impact_summary`：只读 P0/P1，P2/P3 按需展开。
7. 若知识地图不可用、输出不足或无法回指来源，说明问题原因，退回 active specs、资产原文、07 Git 文件事实源和临时核对动作。
8. 修改前运行必要的 preflight/deployment-entries/capability-environment/v2-check 或测试，修改后运行对应校验。

不得用 `ls`、全文 Read 或 `v2-check` 摘要替代知识地图任务导航。

---

## 4. 场景路由

| 场景 | `task_type` | 默认 `start_node` | 问题分流 |
|---|---|---|---|
| 入口理解 | `rules_entry` | `rules/LDVH-ENTRY.md` | 本文、`source_specs` 和固定运行时扩展登记 |
| 判断管辖项目 | `governed_project_check` | `LDVH-GOVERNED-PROJECTS.yaml` | `governed-projects`、Human Gate |
| 处理管辖项目工作对象 | `work_object` | 目标 WorkCase/ADR/Spark/Pitfall/Study | `fact_cli.py show/list/search/stats` 和事实源原文 |
| 修改 specs、附件或行动成员 | `spec_change` | 用户点名文件 | 目标原文、01、04、06、07 和 `preflight` |
| 判断 Rules 同步影响 | `rules_sync_review` | 变化来源文件 | 30、06、受影响 Rules 和临时核对动作 |
| 修改 Code 或测试 | `code_change` | 目标 Code/test 文件 | 04、08、对应测试命令 |
| 修改 Web | `web_change` | 目标 Web/API/文档文件 | 05、08 和相关 Web 校验 |
| 追溯事实源或 Git 提交 | `git_trace` | 变化文件或提交范围 | 31、07、commit records、`commit_validate.py` |

场景同时命中多个入口时，先用最具体的用户点名对象作为 `start_node`。知识地图 `read_plan` 给出 P0/P1 后应替代本文静态猜测。

## 5. 常用命令

| 查询目标 | 优先命令 | 用途 |
|---|---|---|
| 握手 | `python3 code/hook_dispatch.py run session-start --cwd <path>` | 判定环境类型，补全入口链，返回 receipt |
| 写前确认 | `python3 code/hook_dispatch.py run pre-tool-use --cwd <path>` | 管辖项目中确认握手已完成 |
| Code 依赖自举 | `python3 code/bootstrap_code.py` | 安装 Code 依赖，不声明环境完整支持 |
| 管辖项目配置 | `python3 code/specs_validate.py governed-projects` | 检查工作区管辖项目配置 |
| 知识地图任务导航 | `python3 code/specs_validate.py knowledge-map --input-scope entry_navigation --layer neighbors --start-node <path-or-node> --task-type <task_type> --format json` | 生成 read_plan、后续查询、STOP 和影响摘要 |
| specs 汇总健康检查 | `python3 code/specs_validate.py v2-check --format text` | 诊断和知识地图预览；不替代任务导航 |
| 固定运行时扩展自描述 | `python3 code/specs_validate.py v2-check --input-scope runtime_extensions --format text` | 只读投影固定运行时扩展 ldvh_asset |
| 能力资产环境保障矩阵 | `python3 code/specs_validate.py capability-environment` | 只读投影来源规范、同步、验证链和环境落地 |
| specs 写入前检查 | `python3 code/specs_validate.py preflight --target-path <path>` | 只读提示 Human Gate、Git 追溯、同步影响 |
| specs 综合检查 | `python3 code/specs_validate.py all --fail-on-diagnostics` | 执行 active specs 综合校验 |
| LDVH Git 提交 | `specs/31-git-commit-action-Git提交行动编排.md`、`ldvh-git-commit` Skill、`python3 code/commit_validate.py --check-message-file <message-file>` | 按 31 流程和 07 契约提交 |
| 工作对象列表 | `python3 code/fact_cli.py list <type>` | 查询管辖项目工作对象摘要 |
| 工作对象详情 | `python3 code/fact_cli.py show <id>` | 查询单个工作对象 |
| 工作对象搜索 | `python3 code/fact_cli.py search <keyword>` | 按关键词搜索 |
| 工作对象统计 | `python3 code/fact_cli.py stats` | 统计工作对象状态分布 |
| Rules 环境入口接入 | 按 `specs/06-运行时扩展规范.md` §7 | 两种接入方式，按 AI Hook 能力选择 |

---

## 6. STOP 点

出现以下情况时，AI 应暂停并说明需要 Human 确认：

1. `LDVH-GOVERNED-PROJECTS.yaml` 缺失、格式异常或无法定位目标管辖项目；
2. 要新增、删除或修改管辖项目条目；
3. 要创建、删除、移动或重命名管辖项目 `ldvh-base/` 工作对象事实源目录；
4. 要写入、覆盖或删除环境入口、项目规则或等价配置；
5. 要为管辖项目创建环境入口或项目级 AI 指令；
6. 要默认接管、创建、迁移、重排或强制校验用户项目 docs；
7. 要把 LDVH 自身 dogfood 条目解释为用户安装 LDVH 后的默认管辖项目；
8. 要改变 `specs/`、`docs/`、`rules/`、`skills/`、`agents/`、`hooks/`、`code/`、`tests/` 或 `web/` 的定位；
9. 要声明任一环境完整支持 LDVH，或把一次本地适配检查结果写成环境类型结论；
10. 要接受长期能力缺口、关闭关键缺口、绕过 Human Gate 或改变事实源边界；
11. 入口内容与 specs 正式规范、管辖项目配置、工作对象事实或 Code 校验结果冲突；
12. 要修改本文职责边界、STOP、`source_specs`、`sync_triggers`、canonical path、固定承载物身份、权限含义或环境薄引用。

---

## 7. 维护规则

修改本文后，应检查：

1. 运行 `python3 code/specs_validate.py knowledge-map --input-scope entry_navigation --layer neighbors --start-node rules/LDVH-ENTRY.md --task-type rules_sync_review --format text`；
2. 按 `read_plan` P0/P1 回读权威原文；
3. 检查 `source_specs`、`sync_triggers`、入口路由、STOP 点、验证入口和交接规则是否与 30 和知识地图输出一致；
4. 运行 `governed-projects`、`deployment-entries`、`capability-environment`、`v2-check --input-scope entry_navigation --fail-on-diagnostics`；
5. 若改变职责边界、STOP、固定承载物身份、权限含义或环境薄引用，必须评估 Human Gate。
