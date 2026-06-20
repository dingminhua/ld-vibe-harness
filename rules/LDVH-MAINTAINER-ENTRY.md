# LDVH 维护入口

```yaml
ldvh_asset:
  id: "ldvh-maintainer-entry"
  type: "rule"
  status: "active"
  canonical_path: "rules/LDVH-MAINTAINER-ENTRY.md"
  source_specs:
    - "specs/01-目录说明.md"
    - "specs/03-文档基础规范.md"
    - "specs/04.02-LDVH能力资产与落地保障规范.md"
    - "specs/04.03-环境入口适配与部署规范.md"
    - "specs/10-Git提交规范.md"
  consumption_scenarios:
    - "LDVH 产品资产维护"
    - "specs、rules、skills、agents、hooks、code、tests、web 修改入口"
    - "能力资产漂移判断"
  inputs:
    - "用户维护目标"
    - "LDVH 仓库文件事实源"
    - "Code 校验输出"
  outputs:
    - "产品资产维护最小读取顺序"
    - "维护场景路由"
    - "STOP 点"
  handoff: "处理管辖项目工作对象时交还 rules/LDVH-WORKSPACE-ENTRY.md"
  verification:
    - "python3 code/specs_validate.py index"
    - "python3 code/specs_validate.py deployment-entries"
  sync_triggers:
    - "LDVH 产品资产目录边界变化"
    - "固定能力资产登记规则变化"
    - "环境入口适配或部署规则变化"
    - "Git 提交规范或事实源追溯规则变化"
  deprecation: "废弃、重命名或合并维护入口前必须评估 Human Gate，并同步 01、04.02、04.03、工作区入口和 Code 检查。"
```

> 文件性质：LDVH 项目级 Rules 入口资产，不是 specs 正式规范或最终事实源
> 规范来源：`specs/01-目录说明.md`、`specs/03-文档基础规范.md`、`specs/04.02-LDVH能力资产与落地保障规范.md`、`specs/04.03-环境入口适配与部署规范.md`
> 适用范围：维护 LDVH 自身产品资产时的项目级入口

---
## 1. 这个文件是什么

这个文件用于 LDVH 源码仓库的项目级薄入口。它告诉 AI：进入 `ld-vibe-harness` 仓库维护 LDVH 产品资产时，先查什么、如何判断事实源、何时暂停。

它不是最终事实源。正式规则以 `specs/` 为准，能力资产定义以 `specs/04.02-LDVH能力资产与落地保障规范.md` 为准，环境入口适配、部署和检查方法以 `specs/04.03-环境入口适配与部署规范.md` 为准。

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
| 判断 LDVH 产品资产与正式规范、Code 校验、Web 展示之间是否漂移 | 把工作对象事实源当成产品资产目录 |

`ldvh-base/` 始终是被管辖项目的工作对象事实源。即使它位于 LDVH 源码仓库内，也应通过工作区级 `rules/LDVH-WORKSPACE-ENTRY.md` 和 `LDVH-GOVERNED-PROJECTS.yaml` 判断后处理。

若工作目标是处理 WorkArea、WorkPlan、ADR、Memo、Pitfall 或 Study 等工作对象，应转入 `rules/LDVH-WORKSPACE-ENTRY.md`；若目标是追溯事实源修改，应读取 Git commit records 和 `specs/10-Git提交规范.md`。

---
## 3. 最小启动顺序

AI 进入 LDVH 维护入口后，应按以下顺序启动：

1. 确认当前任务是否维护 LDVH 产品资产；
2. 涉及目录、编号或文件归属判断时，读取 `specs/01-目录说明.md`；
3. 涉及术语、命名或不推荐表达时，读取 `specs/02-术语规范.md`；
4. 涉及 specs 修改时，读取 `specs/03-文档基础规范.md`、`specs/03.01-规范文档规范.md`、目标规范和必要的 04/06/09 规范；
5. 涉及能力资产、Rules、Skill、Agent、Hook、Code、Web 或环境适配时，读取 `specs/04.02-LDVH能力资产与落地保障规范.md` 和 `specs/04.03-环境入口适配与部署规范.md`；
6. 能由 Code 定位、聚合或检查的内容，优先使用 Code 工具查询；工具输出只作为导航、聚合和诊断结果，不替代权威文件原文；
7. 修改完成后运行对应校验命令，并把稳定结论写回权威事实源。

常用查询命令如下：

| 查询目标 | 优先命令 | 用途 |
|---|---|---|
| specs 规范入口和章节 | `python3 code/specs_validate.py index` | 生成规范派生索引，辅助定位文件、章节、引用和诊断 |
| 规范落地要求状态 | `python3 code/specs_validate.py landing-report` | 聚合正式规范的落地要求、状态和建议回写方向 |
| specs 文档结构 | `python3 code/specs_validate.py doc specs` | 检查正式规范文档结构 |
| specs 章节引用 | `python3 code/specs_validate.py refs specs` | 检查正式规范中的章节引用 |
| specs 落地要求表 | `python3 code/specs_validate.py landing specs` | 检查规范落地要求表结构 |
| specs 综合检查 | `python3 code/specs_validate.py all` | 执行 specs 综合校验 |
| LDVH Git 提交准备 | `ldvh-git-commit` Skill、`python3 code/commit_validate.py --check-message-file <message-file>` | 按 10 号规范拆分、编写、预检并创建提交 |
| Rules 环境入口接入 | 按 `specs/04.03-环境入口适配与部署规范.md` §4.1-§4.4 执行 | 官方维护 Codex App 适配路径；默认只生成可复制的 Codex 薄入口文本，由用户自行加入环境规则入口 |

---
## 4. 场景路由

| 场景 | 先用工具 | 必读权威入口 |
|---|---|---|
| 理解 LDVH 总体规则 | `index` | `specs/00-LD-Vibe-Harness理念与纲要.md`、`specs/01-目录说明.md`、`specs/02-术语规范.md` |
| 修改 specs 正式规范 | `index`、`doc`、`refs`、`landing` | `specs/03-文档基础规范.md`、`specs/03.01-规范文档规范.md`、`specs/04.01-规范落地声明规范.md`、目标规范 |
| 修改或理解工作模型规范 | `index` | `specs/05-工作模型基础规范.md`、`specs/03.02-工作模型文档规范.md` 和对应 `specs/20-39` 工作模型规范 |
| 处理工作流程规范 | `index`、`landing-report` | `specs/06-工作流程基础规范.md`、`specs/03.03-工作流程文档规范.md` 和对应 `specs/40-59` 工作流程规范 |
| 处理规范落地、环境适配或适配措施 | `landing-report`、`index` | `specs/04-规范落地与环境适配基础规范.md`、`specs/04.02-LDVH能力资产与落地保障规范.md`、`specs/04.03-环境入口适配与部署规范.md` |
| 处理 Code、工具、脚本或校验 | 对应工具帮助、测试命令 | `specs/04.03-环境入口适配与部署规范.md`、`specs/07-Code确定性执行实现规范.md`、对应 `code/` 实现和 `tests/` |
| 处理 Web 或 Human-facing 入口 | `index`、相关后端或 Web 校验 | `specs/08-Web信息同步实现规范.md` |
| 准备 LDVH Git 提交 | `ldvh-git-commit`、`commit_validate.py` | `specs/10-Git提交规范.md`、`skills/ldvh-git-commit/SKILL.md`、`hooks/ldvh-hooks.yaml` |
| 处理 LDVH 自身工作对象 | `governed-projects`、`fact_cli.py list/search/show/stats` | 转入 `rules/LDVH-WORKSPACE-ENTRY.md`，按 dogfood 管辖项目处理 |

场景同时命中多个入口时，选择最小足够查询和读取集。涉及正式规范变更、规范落地要求变化、落地缺口、适配措施漂移或 Code/Web/Skill/Agent/Hook/CI 边界变化时，应读取 `specs/06-工作流程基础规范.md`、`specs/03.03-工作流程文档规范.md` 和 `specs/40-59` 中实际存在的工作流程主文件，判断是否存在 active 具体工作流程。

---
## 5. STOP 点

出现以下情况时，AI 应暂停并说明需要 Human 确认：

1. 要创建、删除、移动或重命名 `rules/LDVH-WORKSPACE-ENTRY.md` 或 `rules/LDVH-MAINTAINER-ENTRY.md`；
2. 要改变 `specs/`、`docs/`、`rules/`、`skills/`、`agents/`、`hooks/`、`code/`、`tests/` 或 `web/` 的定位；
3. 要修改工作区级入口、环境入口、项目规则或等价配置；
4. 要声明任一环境完整支持 LDVH，或把一次本地适配检查结果写成环境类型结论；
5. 要把 LDVH 项目级维护入口用于默认处理管辖项目工作对象；
6. 要接受长期降级、关闭关键缺口、绕过 Human Gate 或改变事实源边界；
7. 入口内容与 specs 正式规范、能力资产定义、Code 校验结果或工作区入口冲突。

---
## 6. 维护规则

修改本文后，应检查：

1. `specs/01-目录说明.md`；
2. `specs/04.02-LDVH能力资产与落地保障规范.md`;
3. `specs/04.03-环境入口适配与部署规范.md`;
4. `rules/LDVH-WORKSPACE-ENTRY.md`；
5. LDVH 仓库项目级薄入口。
