# LDVH 规范落地统筹执行缺口清单

> 创建日期：2026-06-09
> 定位：LDVH 使用 41 规范落地统筹工作流程对当前 docs/specs 正文区执行的一次内部审计、缺口分流和后续承接建议
> 调研边界：不直接构成强制规则
> 执行效力：无；本文结论需进入 docs/specs 正文区、工作对象、Code、Web、测试、运行投影或最佳实践后才具备对应效力
> 来源：当前 `docs/specs/` 正文区、`docs/specs/41-landing-orchestration-规范落地统筹.md`、`LDVH-ENVIRONMENT-INITIALIZATION.md`、`LDVH-GOVERNED-PROJECTS.yaml`、`.trae/rules/ldvh-project-rules.md`、`tools/specs_validate.py`、`tools/fact_validate.py`、`tools/commit_validate.py`
> 关联对象：
> 上位依据：`docs/specs/00-LD-Vibe-Harness理念与纲要.md`
> 相关规范：`docs/specs/01-目录说明.md`、`docs/specs/02-术语规范.md`、`docs/specs/03-文档基础规范.md`、`docs/specs/04.01-规范落地要求规范.md`、`docs/specs/04.02-环境适配与运行投影规范.md`、`docs/specs/04.04-环境能力承接边界.md`、`docs/specs/06-工作流程基础规范.md`、`docs/specs/07-Code实现规范.md`、`docs/specs/08-Web信息同步规范.md`、`docs/specs/09-事实源边界与承载规范.md`、`docs/specs/10-运行闭环测试规范.md`、`docs/specs/40-工作流程集合索引.md`、`docs/specs/41-landing-orchestration-规范落地统筹.md`

---
## 1. 本文解决的问题

本文按 `docs/specs/41-landing-orchestration-规范落地统筹.md` 的流程，对当前 `docs/specs/` 正文区执行一次落地统筹审计，回答：

1. 当前正式规范是否都声明了规范落地要求；
2. 已有哪些要求具备 Code、事实源、环境记录或流程承接；
3. 哪些要求仍停留在文档声明、人工降级或待补齐状态；
4. 要让 LDVH 最小运作跑起来，还需要优先补什么。

本文不是新的正式规范，也不是 Task。它只作为当前缺口清单和后续承接输入。

---
## 2. 审计范围与方法

本次审计范围：

1. `docs/specs/` 根目录 37 篇正式规范；
2. 当前 LDVH 自身环境初始化记录；
3. 当前管辖项目配置；
4. 当前项目级 Trae 薄入口；
5. 当前 `tools/` 和 `tests/` 中已有 Code 校验能力。

本次采用的检查方式：

1. 使用 `tools/specs_validate.py all docs/specs` 检查文档结构、引用、规范落地要求、环境初始化记录和管辖项目配置；
2. 聚合 `docs/specs/` 中所有“规范落地要求”表；
3. 按 41 的执行流程判断每类要求是否已有保障机制、运行投影、验证方式、降级方式和回写出口；
4. 将缺口分流为 specs、Code、Web、工作流程、运行投影、Human Gate、测试或后续 Task 候选。

---
## 3. 当前统计结果

| 项目 | 结果 |
|---|---:|
| 正式规范文件数 | 37 |
| 缺少“规范落地要求”章节的正式规范 | 0 |
| 提取到的规范落地要求总数 | 157 |
| 上位约束承接要求 | 32 |
| 入口可见要求 | 30 |
| 流程复用要求 | 6 |
| 子 Agent 思考要求 | 3 |
| 确定性执行要求 | 31 |
| Human 交互要求 | 26 |
| 生命周期触发要求 | 29 |

结构结论：

1. 文档层面已基本闭合：正式规范都具备规范落地要求章节；
2. 表格字段、章节结构、引用和基础校验通过；
3. 执行层未完全闭合：大量要求仍依赖人工降级、运行入口摘要、后续 Code、后续流程或 Human Gate 会话纪律。

---
## 4. 已闭合或基本闭合的部分

| 领域 | 当前状态 | 依据 |
|---|---|---|
| 规范落地要求结构 | 已闭合 | `tools/specs_validate.py landing` 能检查章节、表头、字段和类型 |
| specs 文档结构和 § 引用 | 已闭合 | `tools/specs_validate.py doc`、`refs`、`all` 已通过 |
| LDVH 自身环境初始化记录结构 | 基本闭合 | `tools/specs_validate.py env-init` 已检查根目录记录 |
| 管辖项目配置结构 | 基本闭合 | `tools/specs_validate.py governed-projects` 已检查根目录配置 |
| 工作对象 YAML 校验 | 部分闭合 | `tools/fact_validate.py`、`tools/fact_cli.py` 已覆盖 ADR、Pitfall、Intent、Memo、Task 等当前对象 |
| Change / commit message 校验 | 部分闭合 | `tools/commit_validate.py` 已覆盖 commit message 格式 |
| 工作流程集合状态 | 文档层闭合 | 40 已登记 41 规范落地统筹和 44 多角色思考为 active |

这些闭合主要是结构层和部分 Code 层闭合，不等于运行投影、自动触发、产品初始化或产品审计已闭合。

---
## 5. 主要未闭合缺口

| 编号 | 缺口 | 状态 | 影响 | 建议承接 |
|---|---|---|---|---|
| G-01 | 缺少规范落地要求全局聚合报告命令 | open | AI 需要手工跨文件聚合 157 条要求，容易遗漏 | Code：扩展 `tools/specs_validate.py`，输出 landing report |
| G-02 | 运行投影漂移检查 Code 缺失 | open | 规范变化后，不知道 Rules / Instructions、Skill、Agent、Hook、CI、Web、Code 入口是否过期 | Code + 04.02：新增 drift / projection 检查能力 |
| G-03 | 薄入口尚未指向 41 | needs_human_gate | 当前 `.trae/rules/ldvh-project-rules.md` 只指向环境初始化、00、01、03、04，未提醒 specs 变更先走 41 | 运行投影：经 Human Gate 后更新项目级薄入口 |
| G-04 | 产品初始化 42 未建立 | open | 管辖项目或 LDVH 自身项目如何完成最低可用接入还没有正式流程 | 工作流程：创建 42 产品初始化 |
| G-05 | 产品审计 43 未建立 | open | 无法稳定检查初始化是否持续有效、入口是否漂移、Human Gate 是否被绕过 | 工作流程：创建 43 产品审计 |
| G-06 | 生命周期触发仍以人工降级为主 | degraded | specs 变更、commit 前后、会话停止前、Task 关闭前等触发依赖 AI 记忆 | 运行投影 + Code：Hook / CI / 人工降级清单逐步承接 |
| G-07 | 运行闭环测试用例事实源位置未稳定 | open | 具体流程的可测试性锚点无法沉淀为长期测试用例 | 10 + Code：确定测试用例事实源或先以 tests 承接 |
| G-08 | 工作流程 45-58 仍为候选 | open | 意图接入、任务规划、任务执行、验证关闭等最小运作流程尚未 formalize | 工作流程：逐个讨论并创建或降级 |
| G-09 | Human Gate 证据仍以对话为主 | degraded | 高影响确认可执行，但难以形成长期可追溯事实 | 工作流程 + Web / 工作对象：定义 Gate 证据回写 |
| G-10 | Web 信息同步仍停留在规范层 | open | Human-facing 闭环、受控编辑和 Gate UI 未形成稳定运行面 | Web：待 08、10、42、43 稳定后实现或校准 |

---
## 6. 按落地要求类型的分流判断

| 类型 | 当前判断 | 优先动作 |
|---|---|---|
| 上位约束承接要求 | 多数通过上位依据、相关规范和索引承接；语义承接仍需审计辅助 | 由 41 + 后续 Code 聚合报告辅助检查 |
| 入口可见要求 | 文档入口基本存在，但项目级薄入口没有覆盖 41；运行入口摘要仍不稳定 | Human Gate 后更新薄入口，并在产品初始化中验证 |
| 流程复用要求 | 04.04、06、41 已规定判断方法；真正可复用流程还少 | 先建立 42、43，再判断哪些子步骤适合 Skill |
| 子 Agent 思考要求 | 44 已承接多角色思考；会话级可用，项目级投影缺失 | 保持会话级降级，后续由 42/43 判断是否需要持久投影 |
| 确定性执行要求 | 已有结构校验、对象校验、commit 校验；缺全局聚合、漂移检查、流程状态检查 | P0 扩展 `tools/specs_validate.py` landing report |
| Human 交互要求 | 会话中能执行；项目级 Gate 提示、证据和 Web 支持未稳定 | 先在 42/43 定义最低 Human Gate 证据要求 |
| 生命周期触发要求 | 大多只写人工降级、CI、Hook 或后续检查，未实例化 | 先由 Code 命令承接，再评估 Hook / CI |

---
## 7. P0 最小落地路径

要让当前规范体系从“文档自洽”进入“可以运作”，建议先补 P0：

1. **P0-1：扩展 Code 聚合报告**
   - 承接位置：`tools/specs_validate.py`
   - 目标：新增可读报告或 JSON 输出，列出所有规范落地要求、类型、保障机制、触发条件和明显缺口。
   - 原因：没有这个工具，41 每次都要手工聚合，无法稳定执行。

2. **P0-2：更新项目级薄入口**
   - 承接位置：`.trae/rules/ldvh-project-rules.md` 或当前环境等价入口。
   - 目标：增加一句“涉及 docs/specs 正式规范变更、落地缺口、运行投影或闭环判断时，先读取 41”。
   - 注意：这是项目级持久运行投影变更，需 Human Gate。

3. **P0-3：创建 42 产品初始化**
   - 承接位置：`docs/specs/42-product-initialization-产品初始化.md`
   - 目标：定义一个项目最低可用接入 LDVH 时要检查什么，包括管辖项目配置、目录、工作模型、工作流程、Code、Web、薄入口、运行投影和降级方式。

4. **P0-4：创建 43 产品审计**
   - 承接位置：`docs/specs/43-product-audit-产品审计.md`
   - 目标：定期或关键变更后检查 42 的结果是否漂移，并调用 41 输出缺口。

P0 完成前，不建议大规模迁移 45-58 的具体流程，因为它们会继续重复“如何落地”的判断。

---
## 8. 建议的回写与后续承接

| 事项 | 建议回写位置 | 说明 |
|---|---|---|
| 规范落地要求聚合报告 | Code / `tools/specs_validate.py` / tests | 形成最小确定性执行能力 |
| 薄入口补 41 | 运行投影入口 + 环境初始化记录 | 需 Human Gate；完成后同步记录 |
| 42 产品初始化 | `docs/specs/42-product-initialization-产品初始化.md` | 应调用 41，不重复定义 04 规则 |
| 43 产品审计 | `docs/specs/43-product-audit-产品审计.md` | 应检查 42、41、20、40、Code、Web 和运行投影 |
| 运行投影漂移检查 | Code + 04.02 / 41 后续缺口 | 先实现最小检查，再考虑 Hook / CI |
| 流程测试用例事实源 | 10 或 tests 后续规则 | 当前先保留 open，不强行定路径 |
| Human Gate 证据 | 42 / 43 / 08 / 工作对象字段 | 先定义最低证据，再考虑 Web 支持 |

---
## 9. Human Gate 判断

以下后续动作需要 Human Gate：

1. 修改 `.trae/rules/ldvh-project-rules.md` 或其他项目级持久入口；
2. 创建或启用 Hook、CI、automation、Skill、Agent 或其他持久运行投影；
3. 判定某个 open / degraded 缺口可以关闭；
4. 创建 42、43 并改变 40 中 planned / active 状态；
5. 接受“人工降级检查”作为长期替代方案；
6. 将本文任何建议升级为正式规范、Code 实现、Web 实现或工作对象。

---
## 10. 当前结论

当前 LDVH 的规范层已经具备“落地要求声明能力”，但还没有完全具备“落地要求执行能力”。

最核心的断点是：

```text
规范已经能说出自己要落地什么，
但系统还不能稳定自动聚合、检查、触发、漂移诊断和初始化审计。
```

因此，下一步不应继续只扩写规范正文，而应优先补：

1. Code 聚合报告；
2. 入口触发；
3. 产品初始化；
4. 产品审计。

这四项补齐后，后续 45-58 工作流程迁移才更容易判断哪些是真流程、哪些只是 Skill、Agent、Code、Web 或最佳实践。

---
## 11. 待补齐事项

1. 本文稳定后，可将 P0-1 转为 Code 修改任务；
2. 若 Human 确认，可修改项目级薄入口指向 41；
3. 42、43 创建后，应回看本文并标注哪些缺口已被正式承接；
4. `docs/evals/19-LDVH规范落地统筹机制与闭环缺口评估.md` 与本文均被吸收后，可评估是否删除或标注已吸收；
5. 后续 Code 聚合报告实现后，应重新生成本文的统计结果，避免长期依赖手工聚合。
