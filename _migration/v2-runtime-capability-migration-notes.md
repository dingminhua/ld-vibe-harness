# V2 运行时能力迁移说明

> 本文只作为过渡迁移证据。本文记录 V3 迁移过程中如何理解 V2 的运行时能力与保障能力，不授权 V3 specs、Code 行为、Action Guide 输出、Human Gate 决策、环境支持声明或事实源变更。

## 范围

本文保留根目录讨论材料中仍有迁移价值的部分。当前正式权威仍在：

- `specs/00-理念与构成.md`
- `specs/01-保障与衔接.md`
- `specs/02-Specs基础规范.md`
- `specs/03-AI行为规范.md`

原根目录讨论草稿已经不再作为当前行动依据。本文只保留迁移映射：哪些 V2 能力不能丢，以及这些能力在 V3 中应由哪里承接。

## V2 Skill 能力

V2 Skill 不是独立规则源。它更像运行时按需加载的可复用工作流包，用来承载稳定执行步骤、预检、失败处理、验证入口和交还方式。

V3 迁移判断如下：

| V2 能力 | V3 去向 | 不能丢失的能力 |
|---|---|---|
| Skill 作为可复用工作流 | 行动模板 | 可复用执行顺序、输入、输出、验证入口、失败处理和交还形态 |
| Skill 触发条件 | 保障与环境入口层，并在可用时由 Code 或运行时识别 | 在正确消费时机提示或要求使用行动模板 |
| Skill plan 输出 | Action Guide 输入或 action template plan | 提供当前任务指导，但不成为第二规则源 |
| Skill 验证与交还 | 行动模板、测试、Git 追溯，必要时进入 Human Gate | 证据、残留风险说明和受控交还 |

V3 不应保留 Skill 作为 LDVH 独立顶层机制。若外部环境支持 Skill 系统，可以由环境适配层把行动模板包装成环境 Skill；LDVH 的权威仍回到 specs、行动模板、事实源、Code 校验和 Human Gate 边界。

## V2 Rules 能力

V2 Rules 已经很薄。它最重要的作用不是承载 LDVH 规则，而是在没有原生 Hook 或 Hook 不可观测时，提供固定环境入口。

V3 迁移判断如下：

| V2 能力 | V3 去向 | 不能丢失的能力 |
|---|---|---|
| `rules/LDVH-RUNTIME-PROTOCOL.md` | 指向 Runtime Protocol 或等价入口契约的环境薄引用 | 入口可见、自描述，以及 AI 进入同一套运行时消费模型的稳定路径 |
| Rules 路径 | 环境薄引用路径 | 不支持 Hook 的环境仍可进入同一套保障语义 |
| Rules 资产登记 | 取消为独立 LDVH 机制 | 避免制造第二套规则资产体系 |
| Rules 与 Hook 同步 | Runtime Protocol、环境入口、Hook 或 dispatcher 同步 | Hook 路径和非 Hook 路径不得分裂成互相竞争的规则体系 |

V3 不应把环境 rules、instructions 或 AGENTS 文件当成 LDVH 权威。它们可以指向 LDVH，但不得复制或重定义 LDVH specs。

## V2 Hook 与 Runtime 能力

V2 Hook 机制展示了一条有价值的运行链：

```text
环境事件或薄引用
  -> Runtime Protocol
  -> canonical event
  -> dispatcher 或等价消费方
  -> read_plan / check / blocker / receipt / diagnostic
  -> AI 判断
  -> 事实源回写或缺口分流
```

V3 应保留能力，而不是继承具体实现。需要保留的迁移残余如下：

| 能力 | V3 去向 | 边界 |
|---|---|---|
| Runtime Protocol | 保障与环境入口层 | 暴露生命周期语义，不成为规则源 |
| canonical event | 环境入口、Code、运行时或后续环境适配规范 | 必须统一 Hook 与薄引用路径 |
| Hook 触发路径 | 环境入口和适配层 | 更强触发路径，但不证明规则已经满足 |
| 薄引用路径 | 环境入口层 | 给无 Hook 环境使用的较弱路径，不形成第二套规则 |
| receipt | 保障、事实源、Git 和测试边界 | 证明动作发生过，不等于最终事实或 Human 授权 |
| diagnostic | 保障与 AI 行为规则 | 必须分类和分流，本身不是最终裁决 |

旧 V2 图只作为历史证据有用，不得复制到当前 specs 中形成实现承诺。

## 知识地图能力

V2 知识地图承载过有价值的只读关系定位能力：定位相关 specs、事实、后续查询、停止条件和影响摘要。

V3 迁移判断如下：

| V2 能力 | V3 去向 | 不能丢失的能力 |
|---|---|---|
| 知识地图 | Action Guide 输入和 Code 派生关系定位 | 快速定位相关规则、事实、依赖和停止条件 |
| read_plan | Action Guide 和 Code 派生导航 | AI 应少读，但读对来源 |
| impact_summary | Action Guide 输入或 review 证据 | AI 行动前能判断风险和影响范围 |
| 派生关系输出 | 只作为过程证据 | 不成为独立事实源 |

只读关系能力可以支持 Action Guide 生成，但 Action Guide 输出和 Code 派生关系视图不得替代 specs、用户事实源或 Human Gate。

## 共同迁移判断

当前 V3 方向：

| V2 名称 | V3 去向 | 保留 | 不保留 |
|---|---|---|---|
| Rules | 环境薄引用 + Runtime Protocol 入口 | 入口可见和无 Hook fallback | 独立 Rules 权威 |
| Skill | 行动模板 + Action Guide 消费 | 可复用工作流能力 | 独立 Skill 权威 |
| Hook | 环境入口和运行时触发路径 | 事件触发、阻断、receipt、diagnostic | 把 V2 安装路径或 dispatcher 形态写成 spec 规则 |
| 知识地图 | Action Guide 输入和 Code 关系定位 | read_plan、next_queries、stop_conditions、impact_summary | 独立知识地图事实层 |

共同规则：

```text
specs 定义规则；
行动模板组织可复用行动结构；
Action Guide 组织当前行动；
环境入口和 Hook / Rules 路径触发消费；
Code 提供确定性支撑；
AI 保持判断责任；
Human Gate 只能由 Human 完成。
```

## 需要持续保留的风险

后续迁移应继续关注以下风险：

| 风险 | 处理方向 |
|---|---|
| 行动模板膨胀成第二套 specs | 保持模板轻量：引用规则，不重定义规则 |
| 删除 Skill 名称后丢失可复用工作流能力 | 确保行动模板能承接稳定步骤、验证入口、失败处理和交还方式 |
| 删除 Rules 名称后丢失无 Hook 环境入口可见性 | 保留环境薄引用和 Runtime Protocol 入口 |
| Hook 路径和薄引用路径分裂 | 两者都进入同一套保障语义和 diagnostic 分类 |
| receipt 被误当成规则满足证明 | receipt 只作为过程证据 |
| 派生关系视图变成事实源 | Code 和 Action Guide 输出必须从属于 Git 可追踪用户事实源 |

## 已整合的来源材料

本文整合了以下已删除根目录临时文件中仍有价值的迁移残余：

- `00-事实源解耦与运行框架比较草稿.md`
- `01-保障与承接-讨论草稿.md`
- `v2-hook-mechanism.md`

`00-svg-preview.md` 和 `00-ldvh-problem-loop.svg` 未保留，因为图示内容与 `specs/00-理念与构成.md` 当前五类构成要素结构冲突。
