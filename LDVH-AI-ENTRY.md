# LDVH AI 统一入口

> 文件性质：AI 统一入口运行投影，不是 docs/specs 正式规范
> 规范来源：`docs/specs/04.02-LDVH能力保障规范.md`
> 适用范围：AI 进入 LDVH 自身项目、用户工作区级入口或管辖项目接入判断时的最小导航

---
## 1. 这个文件是什么

这个文件用于告诉 AI：进入 LDVH 时先查什么、如何判断场景、何时读取权威原文、遇到缺口时在哪里暂停。

它不是最终事实源。正式规则以 `docs/specs/` 为准，管辖项目清单以工作区根目录 `LDVH-GOVERNED-PROJECTS.yaml` 为准，环境适配方法以 `docs/specs/04.03-环境适配规范.md` 和 `docs/specs/04.04-环境适配措施实践.md` 为准，42 LDVH落地与检查只输出当前落地与检查报告；需要长期保留的稳定事实必须按事实源归属进入对应 Git 文件。管辖项目内容事实以对应项目的 `docs/`、`ldvh-base/` 或其他权威 Git 文件为准。

环境入口、项目规则、工作区配置或会话提示只应指向本文件，不应复制本文正文或 docs/specs 正文。

---
## 2. 入口角色区分

本文件不拆分为“工作区入口”和“LDVH 项目入口”两个文件。`LDVH-AI-ENTRY.md` 是唯一默认 AI 统一入口文件，但进入后必须先区分当前使用的是哪一种入口视角。

| 入口视角 | 适用对象 | 主要职责 | 不应做什么 |
|---|---|---|---|
| 工作区入口 | 所有接入 LDVH 的管辖项目，以及指向 LDVH 的工作区级薄入口 | 识别当前管辖项目，定位 `LDVH-GOVERNED-PROJECTS.yaml`、管辖项目自身 `docs/`、`ldvh-base/`、环境适配规范、42 LDVH落地与检查流程和必要 STOP 点 | 不接管用户项目原有入口，不维护管辖项目规则正文，不默认修改 LDVH 自身规范 |
| LDVH 管理入口 | 维护 LDVH 自身项目时使用 | 管理 `docs/specs/`、`code/`、`tests/`、`web/`、根目录配置、环境适配、适配措施和 LDVH 自身项目的工作对象实例 | 不把 LDVH 自身维护规则默认强加给管辖项目 |

当前环境适配规则按 `docs/specs/04.03-环境适配规范.md` 定位；Trae Work CN 与 Codex App 的具体适配措施按 `docs/specs/04.04-环境适配措施实践.md` 定位；个人环境特别要求按 `docs/specs/04.05-个人环境特别要求规范.md` 定位。

AI 进入本文件后，应先判断当前任务是“管辖项目工作区使用 LDVH”，还是“维护 LDVH 自身项目”。若当前目录或用户目标不清楚，应先查询管辖项目配置并说明判断依据；不能判断时暂停请求 Human 确认。

---
## 3. 最小启动顺序

AI 进入 LDVH 时，先读取本文件确认事实源边界、查询入口、场景路由和 STOP 点。能由 Code 定位、聚合或检查的内容，优先使用 Code 工具查询；工具输出只作为导航、聚合和诊断结果，不替代权威文件原文。

最小启动顺序如下：

1. 读取本文件，确认当前任务属于工作区入口视角还是 LDVH 管理入口视角；
2. 运行对应查询命令，定位规范、工作对象、环境适配规则、适配措施或管辖项目配置；
3. 按查询结果读取最小必要的权威文件原文；
4. 涉及写入、状态流转、关闭、删除、长期降级或高影响判断时，回到对应规范、工作对象和 Human Gate；
5. 修改完成后运行对应校验命令，并把稳定结论写回权威事实源。

常用查询命令如下：

| 查询目标 | 优先命令 | 用途 |
|---|---|---|
| specs 规范入口和章节 | `python3 code/specs_validate.py index` | 生成规范派生索引，辅助定位文件、章节、引用和诊断 |
| 规范落地要求状态 | `python3 code/specs_validate.py landing-report` | 聚合正式规范的落地要求、状态和建议回写方向 |
| specs 文档结构 | `python3 code/specs_validate.py doc docs/specs` | 检查正式规范文档结构 |
| specs 章节引用 | `python3 code/specs_validate.py refs docs/specs` | 检查正式规范中的章节引用 |
| specs 落地要求表 | `python3 code/specs_validate.py landing docs/specs` | 检查规范落地要求表结构 |
| specs 综合检查 | `python3 code/specs_validate.py all` | 执行 docs/specs 综合校验 |
| 管辖项目配置 | `python3 code/specs_validate.py governed-projects` | 检查工作区根目录管辖项目配置 |
| 工作对象列表 | `python3 code/fact_cli.py list <type>` | 查询 ADR、Intent、Memo、Pitfall 或 Task 摘要 |
| 工作对象详情 | `python3 code/fact_cli.py show <id>` | 查询单个工作对象详情 |
| 工作对象搜索 | `python3 code/fact_cli.py search <keyword>` | 按关键词搜索工作对象事实源 |
| 工作对象统计 | `python3 code/fact_cli.py stats` | 统计工作对象状态分布 |
| 规范关联对象 | `python3 code/fact_cli.py related <spec_path>` | 查询与指定 specs 路径关联的 ADR |

当工具不可用、输出无法回指事实源、结果与原文冲突或当前场景超出工具能力时，应退回 Git 文件事实源、对应规范和人工降级检查，不得把工具输出当作最终事实。

---
## 4. 场景路由

| 场景 | 入口视角 | 先用工具 | 必读权威入口 |
|---|---|---|---|
| 判断当前是否为管辖项目 | 工作区入口 | `governed-projects` | `LDVH-GOVERNED-PROJECTS.yaml`、`docs/specs/03.06-管辖项目配置规范.md` |
| 执行 LDVH落地与检查 | 工作区入口 | `governed-projects`、`landing-report`、必要时 `fact_cli.py stats` | `docs/specs/04.03-环境适配规范.md`、`docs/specs/04.04-环境适配措施实践.md`、`docs/specs/04.05-个人环境特别要求规范.md`、`docs/specs/40-工作流程集合索引.md` |
| 处理管辖项目工作对象 | 工作区入口 | `fact_cli.py list/search/show/stats` | 对应管辖项目自身 `ldvh-base/`、`docs/specs/05-工作模型基础规范.md`、`docs/specs/20-工作模型集合索引.md` 和对应工作模型规范 |
| 理解 LDVH 总体规则 | 共同入口 | `index` | `docs/specs/00-LD-Vibe-Harness理念与纲要.md`、`docs/specs/01-目录说明.md`、`docs/specs/02-术语规范.md` |
| 判断事实源、证据或回写出口 | 共同入口 | `index`、`fact_cli.py search/show` | `docs/specs/09-事实源边界与承载规范.md`、对应工作模型或文档规范 |
| 判断术语、命名或不推荐表达 | 共同入口 | `index` | `docs/specs/02-术语规范.md` |
| 判断目录、编号或文件归属 | 共同入口 | `index` | `docs/specs/01-目录说明.md`、`docs/specs/03-文档基础规范.md` |
| 修改 docs/specs 正式规范 | LDVH 管理入口 | `index`、`doc`、`refs`、`landing` | `docs/specs/03-文档基础规范.md`、`docs/specs/03.01-规范文档规范.md`、`docs/specs/04.01-规范落地声明规范.md`、目标规范 |
| 修改或理解工作模型规范 | LDVH 管理入口 | `index` | `docs/specs/05-工作模型基础规范.md`、`docs/specs/20-工作模型集合索引.md` 和对应 `docs/specs/21-39` 工作模型规范 |
| 处理 LDVH 自身项目工作对象 | LDVH 管理入口 | `fact_cli.py list/search/show/stats` | LDVH 自身项目 `ldvh-base/`、`docs/specs/05-工作模型基础规范.md`、`docs/specs/20-工作模型集合索引.md` 和对应工作模型规范 |
| 处理工作流程 | LDVH 管理入口 | `index`、`landing-report` | `docs/specs/06-工作流程基础规范.md`、`docs/specs/40-工作流程集合索引.md` 和对应 `docs/specs/41-59` 工作流程规范 |
| 处理规范落地、环境适配或适配措施 | LDVH 管理入口 | `landing-report`、`index` | `docs/specs/04-规范落地与环境适配基础规范.md`、`docs/specs/04.02-LDVH能力保障规范.md`、`docs/specs/04.03-环境适配规范.md`、`docs/specs/04.04-环境适配措施实践.md` |
| 处理 Code、工具、脚本或校验 | LDVH 管理入口 | 对应工具帮助、测试命令 | `docs/specs/04.05-个人环境特别要求规范.md`、`docs/specs/07-Code确定性执行实现规范.md`、对应 `code/` 实现和 `tests/`；原运行闭环测试机制已退回 docs/research/，不作为当前校验入口 |
| 处理 Web 或 Human-facing 入口 | LDVH 管理入口 | `index`、相关后端或 Web 校验 | `docs/specs/08-Web信息同步实现规范.md` |

场景同时命中多个入口时，选择最小足够查询和读取集。涉及正式规范变更、规范落地要求变化、落地缺口、适配措施漂移或 Code/Web/Skill/Agent/Hook/CI 边界变化时，应先读取 `docs/specs/40-工作流程集合索引.md` 确认当前 active 工作流程，再按对应规范执行。

遇到“对应 `docs/specs/21-39` 工作模型规范”时，应先读 `docs/specs/20-工作模型集合索引.md` 定位具体文件；遇到“对应 `docs/specs/41-59` 工作流程规范”时，应先读 `docs/specs/40-工作流程集合索引.md` 定位具体文件。不得凭编号区段、标题记忆或聊天上下文猜测文件。

---
## 5. 入口分层与使用边界

工作区级入口属于用户自己的开发环境配置。初始化时只应在 Human 授权下加入一条醒目的薄引用，把 AI 引向本文件，并使用本文件中的工作区入口视角，不应复制规则正文。

LDVH 管理入口视角随本文件提交，用于维护 LDVH 自身项目。该视角可以指向 `docs/specs/`、`code/`、`tests/`、`web/`、根目录配置和适配措施治理，但不得被误用为所有管辖项目的项目级规则正文。

管辖项目和 LDVH 自身项目均不创建项目级环境入口或项目级 AI 指令。所有项目统一通过工作区级薄入口进入 LDVH 治理链路；管辖项目通过工作区根目录管辖项目配置、自身 `docs/`、自身 `ldvh-base/` 承载项目事实；项目事实仍由管辖项目自身内容事实源承载。

---
## 6. STOP 点

出现以下情况时，AI 应暂停并说明需要 Human 确认：

1. 要创建、删除、移动或重命名 `LDVH-AI-ENTRY.md`；
2. 要修改工作区级入口、环境入口、项目规则或等价配置；
3. 要为管辖项目创建环境入口或项目级 AI 指令；
4. `LDVH-GOVERNED-PROJECTS.yaml` 缺失、格式异常或无法定位目标管辖项目；
5. 要创建、修改或删除 LDVH 自身项目的持久适配措施，但尚未现场确认当前环境、权限边界、Human 授权和必要降级方式；
6. 入口内容与 docs/specs 正式规范、管辖项目配置、工作对象事实或 Code 校验结果冲突；
7. 需要接受长期降级、关闭关键缺口、绕过 Human Gate 或改变事实源边界。

---
## 7. 维护规则

修改本文后，应检查：

1. `docs/specs/04.02-LDVH能力保障规范.md`；
2. `docs/specs/04.02-LDVH能力保障规范.md`；
3. `docs/specs/01-目录说明.md`；
4. `docs/specs/40-工作流程集合索引.md`；
5. 当前环境适配规范和适配措施；
6. 已授权的环境薄入口。

若发现入口漂移，应按 `docs/specs/40-工作流程集合索引.md` 确认当前 active 工作流程，不得直接把本文件中的旧摘要当成正式规则。
