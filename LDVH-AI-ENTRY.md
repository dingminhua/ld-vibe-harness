# LDVH AI 统一入口

> 文件性质：AI 统一入口运行投影，不是 docs/specs 正式规范
> 规范来源：`docs/specs/04.02-环境适配与运行投影规范.md`
> 适用范围：AI 进入 LDVH 自身项目、用户工作区级入口或管辖项目接入判断时的最小导航

---
## 1. 这个文件是什么

这个文件用于告诉 AI：进入 LDVH 时先读什么、如何判断场景、遇到缺口时在哪里暂停。

它不是最终事实源。正式规则以 `docs/specs/` 为准，管辖项目清单以 `LDVH-GOVERNED-PROJECTS.yaml` 为准，LDVH 自身环境适配以 `LDVH-ENVIRONMENT-INITIALIZATION.md` 为准，工作对象事实以对应 Git 文件为准。

平台入口、项目规则、工作区配置或会话提示只应指向本文件，不应复制本文正文或 docs/specs 正文。

---
## 2. 最小读取顺序

AI 进入 LDVH 时，先按以下顺序读取：

1. `docs/specs/00-LD-Vibe-Harness理念与纲要.md`；
2. `docs/specs/01-目录说明.md`；
3. `docs/specs/02-术语规范.md`；
4. 当前任务涉及规范落地、运行投影、入口、环境适配或闭环缺口时，读取 `docs/specs/41-landing-orchestration-规范落地统筹.md`；
5. 需要识别管辖项目时，读取 `LDVH-GOVERNED-PROJECTS.yaml` 和 `docs/specs/03.06-管辖项目配置规范.md`；
6. 需要创建、修改或删除 LDVH 自身项目运行投影时，读取 `LDVH-ENVIRONMENT-INITIALIZATION.md`、`docs/specs/04-规范落地与环境适配基础规范.md`、`docs/specs/04.02-环境适配与运行投影规范.md` 和 `docs/specs/04.03-环境初始化与适配记录规范.md`；
7. 需要处理平台适配、平台清单或要求响应矩阵时，读取 `docs/specs/04.07-平台适配清单规范.md`，当前平台为 Trae Solo 时读取 `docs/specs/04.08-Trae-Solo适配清单.md`；
8. 需要执行产品初始化或产品审计时，读取 `docs/specs/42-product-initialization-产品初始化.md`、`docs/specs/43-product-audit-产品审计.md`，并回到当前平台适配清单中的要求响应矩阵。

---
## 3. 场景路由

| 场景 | 读取入口 |
|---|---|
| 理解 LDVH 总体规则 | `docs/specs/00-LD-Vibe-Harness理念与纲要.md`、`docs/specs/01-目录说明.md`、`docs/specs/02-术语规范.md` |
| 修改 docs/specs 正式规范 | `docs/specs/03-文档基础规范.md`、`docs/specs/03.01-规范文档规范.md`、`docs/specs/04.01-规范落地声明规范.md`、`docs/specs/41-landing-orchestration-规范落地统筹.md`，以及目标规范 |
| 判断术语、命名或不推荐表达 | `docs/specs/02-术语规范.md` |
| 判断目录、编号或文件归属 | `docs/specs/01-目录说明.md`、`docs/specs/03-文档基础规范.md` |
| 判断管辖项目 | `LDVH-GOVERNED-PROJECTS.yaml`、`docs/specs/03.06-管辖项目配置规范.md` |
| 执行产品初始化 | `docs/specs/42-product-initialization-产品初始化.md`、`docs/specs/04.07-平台适配清单规范.md`、当前平台适配清单；当前平台为 Trae Solo 时读取 `docs/specs/04.08-Trae-Solo适配清单.md` |
| 处理工作模型或工作对象 | `docs/specs/05-工作模型基础规范.md`、`docs/specs/20-工作模型集合索引.md` 和对应 `docs/specs/21-39` 工作模型规范 |
| 处理工作流程 | `docs/specs/06-工作流程基础规范.md`、`docs/specs/40-工作流程集合索引.md` 和对应 `docs/specs/41-59` 工作流程规范 |
| 处理规范落地、环境适配、平台清单或运行投影 | `docs/specs/04-规范落地与环境适配基础规范.md`、`docs/specs/04.01-规范落地声明规范.md`、`docs/specs/04.02-环境适配与运行投影规范.md`、`docs/specs/04.03-环境初始化与适配记录规范.md`、`docs/specs/04.05-LDVH落地特别要求规范.md`、`docs/specs/04.07-平台适配清单规范.md`、当前平台适配清单和 `docs/specs/41-landing-orchestration-规范落地统筹.md` |
| 执行产品审计 | `docs/specs/43-product-audit-产品审计.md`、`docs/specs/42-product-initialization-产品初始化.md`、`docs/specs/04.07-平台适配清单规范.md`、当前平台适配清单和 `docs/specs/40-工作流程集合索引.md` |
| 处理 Code、工具、脚本或校验 | `docs/specs/07-Code实现规范.md`、对应 `tools/` 实现和 `tests/` |
| 处理 Web 或 Human-facing 入口 | `docs/specs/08-Web信息同步规范.md` |
| 判断事实源、证据或回写出口 | `docs/specs/09-事实源边界与承载规范.md` |
| 判断运行闭环测试 | `docs/specs/10-运行闭环测试规范.md` |

场景同时命中多个入口时，选择最小足够读取集。执行产品初始化时进入 `docs/specs/42-product-initialization-产品初始化.md` 并读取当前平台适配清单；执行产品审计时进入 `docs/specs/43-product-audit-产品审计.md` 并审计要求响应矩阵；只要涉及正式规范变更、落地缺口、运行投影漂移或产品审计输入，应优先进入 `docs/specs/41-landing-orchestration-规范落地统筹.md`。

遇到“对应 `docs/specs/21-39` 工作模型规范”时，应先读 `docs/specs/20-工作模型集合索引.md` 定位具体文件；遇到“对应 `docs/specs/41-59` 工作流程规范”时，应先读 `docs/specs/40-工作流程集合索引.md` 定位具体文件。不得凭编号区段、标题记忆或聊天上下文猜测文件。

---
## 4. 入口分层

工作区级入口属于用户自己的开发环境配置。初始化时只应在 Human 授权下加入一条醒目的薄引用，把 AI 引向 LDVH 管理入口或本文件，不应复制规则正文。

LDVH 自身项目级入口可以随本项目提交，但也只应指向本文件。

管辖项目一般不创建平台入口或项目级 AI 指令。管辖项目通过 LDVH 根目录管辖项目配置、项目 `docs/`、项目 `ldvh-base/` 和工作区级薄入口进入 LDVH 管理链路。

---
## 5. STOP 点

出现以下情况时，AI 应暂停并说明需要 Human 确认或进入 `docs/specs/41-landing-orchestration-规范落地统筹.md`：

1. 要创建、删除、移动或重命名 `LDVH-AI-ENTRY.md`；
2. 要修改工作区级入口、平台入口、项目规则或等价配置；
3. 要为管辖项目创建平台入口或项目级 AI 指令；
4. `LDVH-GOVERNED-PROJECTS.yaml` 缺失、格式异常或无法定位目标管辖项目；
5. 要创建、修改或删除 LDVH 自身项目的持久运行投影，但 `LDVH-ENVIRONMENT-INITIALIZATION.md` 不存在或不匹配当前环境；
6. 入口内容与 docs/specs 正式规范、管辖项目配置、工作对象事实或 Code 校验结果冲突；
7. 需要接受长期降级、关闭关键缺口、绕过 Human Gate 或改变事实源边界。

---
## 6. 维护规则

修改本文后，应检查：

1. `docs/specs/04.02-环境适配与运行投影规范.md`；
2. `docs/specs/04.05-LDVH落地特别要求规范.md`；
3. `docs/specs/04.02-环境适配与运行投影规范.md`；
4. `docs/specs/01-目录说明.md`；
5. `docs/specs/41-landing-orchestration-规范落地统筹.md`；
6. `LDVH-ENVIRONMENT-INITIALIZATION.md`；
7. 已登记的平台薄入口。

若发现入口漂移，应进入 `docs/specs/41-landing-orchestration-规范落地统筹.md` 判断缺口归属，不得直接把本文件中的旧摘要当成正式规则。
