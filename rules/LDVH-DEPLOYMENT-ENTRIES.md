# LDVH 部署入口资产清单

> 文件性质：AI 入口资产清单运行投影，不是 specs 正式规范，不是环境安装状态记录
> 规范来源：`specs/04-规范落地与环境适配基础规范.md`、`specs/04.02-LDVH能力保障规范.md`、`specs/04.03-环境适配规范.md`、`specs/04.04-环境适配措施实践.md`
> 入口来源：`rules/LDVH-AI-ENTRY.md`

---
## 1. 这个文件是什么

本文列出当前仓库中 LDVH 四类必备部署入口资产的最小可查询清单，供 AI、后续 Code 检查和 Web 展示定位入口资产。

本文不新增稳定规则，不替代 specs，不声明任何环境已经安装、启用或原生完整支持四类入口。正式规则以 `specs/` 为准；当前环境能力、承载方式、降级证据和 Human Gate 状态必须按 04.03、04.04、环境适配记录、Code 输出或 Human Gate 查询。

---
## 2. 入口资产总表

| 入口类型 | 当前资产 | 位置 | 当前资产状态 | 何时使用 | 降级方式 |
|---|---|---|---|---|---|
| Rules | LDVH AI 统一入口 | `rules/LDVH-AI-ENTRY.md` | 已有最小 Rules 入口资产 | AI 进入 LDVH、判断入口视角、定位事实源边界、场景路由和 STOP 点时 | Human 在会话中显式提供入口摘要、权威路径和必读边界 |
| Skill | LDVH 规范变更检查 Skill | `skills/ldvh-spec-change-check/SKILL.md` | 已有最小 Skill 文本能力资产 | 修改 specs 或入口资产后、提交前、需要检查规范变更治理步骤时 | 主控 AI 按 Skill 正文手动执行 SOP，并记录流程复用缺口 |
| Agent | LDVH 规范语义审查 Agent | `agents/ldvh-spec-semantic-review.md` | 已有最小 Agent 文本能力资产 | 需要独立上下文、专项语义审查、职责边界审查或复杂争议分析时 | 主控 AI 顺序模拟 Agent 审查，并显式记录输入、输出、证据和未决问题 |
| Hook | LDVH 生命周期检查 Hook | `hooks/ldvh-lifecycle-check.md` | 已有最小 Hook 文本能力资产 | 修改前后、验证前后、提交前、声明环境能力完整支持前或关闭缺口前 | 使用 Skill 模拟、Command 手动触发、CI 触发或人工检查清单，并记录残留风险 |

---
## 3. 使用顺序

AI 需要使用部署入口资产时，应按以下顺序处理：

1. 先读取 `rules/LDVH-AI-ENTRY.md`，确认入口视角、事实源边界、场景路由和 STOP 点；
2. 再读取本文，确认四类必备部署入口的当前仓库资产位置；
3. 根据任务类型读取对应入口资产；
4. 若入口资产内容与 specs、Code 输出、Human Gate 或事实源冲突，以正式事实源和 Human Gate 为准；
5. 若当前环境没有原生承载方式，应按 04.03 和 04.04 记录配置适配、指令适配、人工降级、检查证据和残留风险。

---
## 4. 边界

1. 本文只记录当前仓库中的入口资产清单，不记录当前用户环境是否已安装、启用或验证；
2. 四类必备部署入口限定为 Rules、Skill、Agent、Hook；
3. Code、Web、CLI、MCP、Command、CI 和文档可以支撑四类入口，但不是同一层级的部署入口；
4. Skill 可以模拟 Hook 提醒或检查流程，但不得写成 Hook 原生完整支持；
5. Hook 触发不等于检查通过；
6. Agent 输出不得直接生效，必须交还主控 AI 或 Human；
7. 入口资产不得复制完整 specs 正文，不得成为最终事实源；
8. 涉及长期入口、自动触发、危险权限、跨工作区写入、完整支持声明或关闭关键降级项时，必须触发 Human Gate。

---
## 5. 维护规则

修改本文时，应同步检查：

1. `rules/LDVH-AI-ENTRY.md`；
2. `specs/04.02-LDVH能力保障规范.md`；
3. `specs/04.03-环境适配规范.md`；
4. `specs/04.04-环境适配措施实践.md`；
5. `skills/`、`agents/`、`hooks/` 中对应入口资产是否存在；
6. 是否需要更新临时上下文、Task、ADR 或后续 Code / Web 检查。

删除、重命名、移动或关闭本文列出的任何入口资产前，必须暂停并请求 Human Gate。