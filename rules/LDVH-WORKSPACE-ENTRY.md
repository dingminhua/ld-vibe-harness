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
    - "specs/06-运行时扩展规范.md"
    - "specs/attachments/06.Att.02-固定运行时扩展登记表.md"
    - "specs/07-事实源边界与Git追溯规范.md"
  consumption_scenarios:
    - "工作区级管辖项目识别"
    - "管辖项目工作对象处理"
    - "LDVH dogfood 管辖判断"
  inputs:
    - "LDVH-GOVERNED-PROJECTS.yaml"
    - "当前工作目录"
    - "用户任务目标"
  outputs:
    - "最小读取顺序"
    - "场景路由"
    - "STOP 点"
  handoff: "命中 LDVH 产品资产维护时交还 rules/LDVH-MAINTAINER-ENTRY.md"
  verification:
    - "python3 code/specs_validate.py governed-projects"
    - "python3 code/specs_validate.py deployment-entries"
  sync_triggers:
    - "source_specs 中任一 active 规范发生入口职责、事实源边界、Human Gate、Code 诊断或知识地图输入变化"
    - "管辖项目配置规则变化"
    - "工作区入口职责变化"
    - "环境入口适配或薄引用规则变化"
    - "固定运行时扩展登记规则变化"
  deprecation: "废弃、重命名或合并工作区入口前必须评估 Human Gate，并同步 01、02、06、07 和 Code 检查。"
```

> 文件性质：工作区级 Rules 入口资产，不是 specs 正式规范或最终事实源
> 规范来源：`specs/01-规范体系基础规范.md`、`specs/02-事实模型基础规范.md`、`specs/06-运行时扩展规范.md`、`specs/attachments/06.Att.02-固定运行时扩展登记表.md`、`specs/07-事实源边界与Git追溯规范.md`
> 适用范围：安装或使用 LDVH 的工作区级入口、管辖项目识别、管辖项目工作对象处理和 dogfood 管辖判断

---
## 1. 这个文件是什么

这个文件用于工作区级薄入口。它告诉 AI：当前工作区是否使用 LDVH、LDVH 管哪些项目、如何进入管辖项目的事实源和工作对象。

它不是最终事实源。正式规则以 `specs/` 为准，管辖项目清单以工作区根目录 `LDVH-GOVERNED-PROJECTS.yaml` 为准，环境入口适配、部署和检查方法以 `specs/06-运行时扩展规范.md` 为准。

环境入口、项目规则、工作区配置或会话提示只应通过薄引用措施指向本文件，不应复制本文正文或 specs 正文。薄引用正文只应包含入口指向、压缩或恢复后的重读提示，以及 LDVH 管理段开始和结束标记。当前固定运行时扩展登记见 `specs/attachments/06.Att.02-固定运行时扩展登记表.md`。

---
## 2. 入口职责

工作区入口负责管辖治理，不负责维护 LDVH 产品资产。

| 负责 | 不负责 |
|---|---|
| 读取工作区根目录 `LDVH-GOVERNED-PROJECTS.yaml` | 默认维护 LDVH 自身 `specs/`、`rules/`、`code/`、`web/` 等产品资产 |
| 判断当前项目是否为管辖项目 | 把 LDVH 自身开发规则强加给用户项目 |
| 定位管辖项目自身 `ldvh-base/`、项目文档和 Git 事实源 | 默认接管、创建、迁移或重排用户项目 docs |
| 处理所有管辖项目的 WorkCase、ADR、Spark、Pitfall 和 Study，并按 Git 提交记录追溯事实源修改 | 把工作区环境入口写成长期安装状态 |
| 在 LDVH 自身被登记为 dogfood 管辖项目时，处理 LDVH 自身 `ldvh-base/` 工作对象 | 把 LDVH 安装用户的 LDVH 仓库默认视为管辖项目 |

`ldvh-base/` 不因为位于 LDVH 仓库内就属于 LDVH 项目级维护入口。它始终是被管辖项目的工作对象事实源，归工作区级管辖治理入口处理；LDVH 自身源码仓库只有在 `LDVH-GOVERNED-PROJECTS.yaml` 中登记为 dogfood 管辖项目时，才按管辖项目处理其 `ldvh-base/`。

若任务目标是维护 LDVH 产品资产，例如修改 `specs/`、`rules/`、`skills/`、`agents/`、`hooks/`、`code/`、`tests/` 或 `web/`，应转入 `rules/LDVH-MAINTAINER-ENTRY.md`。

---
## 3. 最小启动顺序

AI 进入工作区入口后，应按以下顺序启动：

1. 定位当前工作区根目录；
2. 读取 `LDVH-GOVERNED-PROJECTS.yaml`，确认文件存在、结构有效并理解 `product_name` 与 `product_description`；
3. 判断当前目录或用户目标是否命中某个 `projects[].path`；
4. 命中管辖项目时，按该项目自身事实源工作：`ldvh-base/` 承载工作对象，项目文档按项目约定、README、用户指令或任务上下文定位，事实源修改追溯回到项目 Git commit records；
5. 未命中管辖项目时，不得静默决定接管项目；应说明当前观察，并在需要时生成候选配置草案交由 Human Gate；
6. 涉及工作对象准入、状态流转、关闭、长期降级、项目清单修改或用户文档写入时，回到对应 specs、工作对象事实源和 Human Gate。

常用查询命令如下：

| 查询目标 | 优先命令 | 用途 |
|---|---|---|
| 管辖项目配置 | `python3 code/specs_validate.py governed-projects` | 检查工作区根目录管辖项目配置 |
| specs 规范入口和章节 | `python3 code/specs_validate.py v2-check --format text` | 生成 active specs 规范诊断和知识地图派生预览 |
| 工作对象列表 | `python3 code/fact_cli.py list <type>` | 查询当前项目 WorkCase、ADR、Spark、Pitfall 或 Study 摘要 |
| 工作对象详情 | `python3 code/fact_cli.py show <id>` | 查询单个工作对象详情 |
| 工作对象搜索 | `python3 code/fact_cli.py search <keyword>` | 按关键词搜索工作对象事实源 |
| 工作对象统计 | `python3 code/fact_cli.py stats` | 统计工作对象状态分布 |
| Rules 环境入口接入 | 按 `specs/06-运行时扩展规范.md` §4.1-§4.4 执行 | 官方维护 Codex App 适配路径；默认只生成可复制的 Codex 薄入口文本，由用户自行加入环境规则入口 |

工具输出只作为导航、聚合和诊断结果，不替代权威文件原文。当工具不可用、输出无法回指事实源、结果与原文冲突或当前场景超出工具能力时，应退回 Git 文件事实源、对应规范和人工降级检查。

---
## 4. 场景路由

| 场景 | 先用工具 | 必读权威入口 |
|---|---|---|
| 判断当前是否为管辖项目 | `governed-projects` | `LDVH-GOVERNED-PROJECTS.yaml`、`specs/06-运行时扩展规范.md` |
| 新增、删除或修改管辖项目条目 | `governed-projects` | `specs/06-运行时扩展规范.md`、Human Gate |
| 处理管辖项目工作对象 | `fact_cli.py list/search/show/stats` | 对应项目 `ldvh-base/`、`specs/02-事实模型基础规范.md` 和对应 `specs/20-29` 事实模型规范 |
| 处理管辖项目 Git 提交记录 | Git 历史和必要校验 | 管辖项目 Git commit records、`specs/07-事实源边界与Git追溯规范.md` |
| 读取或修改管辖项目文档 | 项目约定、README、用户指令 | 项目自有文档位置、`specs/01-规范体系基础规范.md`、`specs/07-事实源边界与Git追溯规范.md` |
| 执行 LDVH 部署适配或接入检查 | `governed-projects`、`v2-check` | `specs/06-运行时扩展规范.md`、`specs/03-行动编排规范.md` |
| 维护 LDVH 产品资产 | `index` | 转入 `rules/LDVH-MAINTAINER-ENTRY.md` |

遇到“对应 `specs/20-29` 事实模型规范”时，应按 `specs/02-事实模型基础规范.md` 的成员自描述契约和成员主文件定位具体文件；遇到“对应 `specs/30-59` 行动编排规范”时，应按 `specs/03-行动编排规范.md` 的成员自描述契约和实际存在的成员主文件定位具体文件。

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

---
## 6. 维护规则

修改本文后，应检查：

1. `specs/01-规范体系基础规范.md`；
2. `specs/02-事实模型基础规范.md`；
3. `specs/06-运行时扩展规范.md`；
4. `specs/07-事实源边界与Git追溯规范.md`；
5. `rules/LDVH-MAINTAINER-ENTRY.md`；
6. 本文 `source_specs`、`sync_triggers`、入口路由、STOP 点、验证入口和交接规则；
7. 已授权的工作区级薄入口。
