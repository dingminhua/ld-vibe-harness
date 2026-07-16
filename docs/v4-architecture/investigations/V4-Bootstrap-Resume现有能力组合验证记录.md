# V4 Bootstrap/Resume 现有能力组合验证记录

> 记录性质：本文记录一次只读组合验证及其结论边界，不是规则源、Helper 契约、环境 adapter 设计或新的当前状态登记。
> 验证日期：2026-07-16。
> 验证基线：`dev-v4` 提交 `46d892e0`，本仓库实际 Working Tree、当前 `.venv/bin/ldvh` 和现有工作区管辖配置。

## 1. 目标与边界

本次回答：现有 Codex `SessionStart startup|resume` 管辖注入、Helper 能力发现、F0/F1、规则候选和来源回指，能否在不新增 Helper 的前提下，让一个缺少既有聊天上下文的 AI 低成本建立当前项目上下文并恢复已有工作责任。

验证只执行读取：没有创建或更新事实对象，没有修改管辖配置、插件安装、Helper、Specs、Code 或 tests，也没有为了通过流程制造 WorkCase 或其它事实。本次直接调用仓库 adapter 脚本和 Helper，证明受控输入下的当前组合；没有把手工调用冒充为新的 Codex 真实自动触发。2026-07-15 的真实 `startup|resume` 事件证据仍只覆盖当时已经安装的插件版本。

## 2. 组合路径

当前可以按以下顺序复用已有入口：

1. `SessionStart startup|resume` adapter 使用事件 `cwd` 和已配置 `workspace_root` 调用 `resolve-governance-scope`；
2. AI 在需要了解可调用范围时执行通用 `capabilities`；
3. 取得唯一 `governed_project_id` 后调用 `find-fact-object-candidates` 的 F1；同一结果同时返回 F0 recovery manifest；
4. 只在任务需要时，根据能力结果中的规则来源调用 `read-specification-candidates` L1/L2 或 `read-specification-content` L3/L4；
5. F1 或已有恢复指针选中具体事实后，再用 `read-fact-objects` 展开 F3。本次没有真实事实指针，因此没有执行空转的精确读取。

前三步是当前最小启动基线：一次 adapter 内部 Helper 调用，加两次 AI 按需 Helper 调用。规则概览是第四次可选调用，不应在没有任务需要时自动全文展开。

## 3. 当次实测

工作对象为 `/Users/dmh2002/poker_hud_projects/ld-vibe-harness-v4`，显式工作区根为 `/Users/dmh2002/poker_hud_projects`。所有 Helper 响应均为 `ldvh-helper-cli/2`、`compact`、退出码 0，且 `changes` 为空。

| 入口 | 结果 | 响应体量 | 当次耗时 | 空值信号 |
|---|---|---:|---:|---|
| adapter `startup` | 注入 `governed_single` 及完整管辖结果 | 外层 12,303 bytes；additional context 11,271 bytes | 未单独计时 | 只含管辖结果，不含 capabilities 或 F0/F1 |
| adapter `resume` | 与 startup 相同的当前管辖身份 | 外层 12,302 bytes；additional context 11,270 bytes | 未单独计时 | 同上 |
| `capabilities` | 10 项当前来源绑定的公开操作 | 35,576 bytes | 0.42 s | 递归计数 69 个 null、36 个空 array；通用发现按契约不计算请求可用性 |
| `find-fact-object-candidates` F1 | F0 coverage complete；F1 0 cards | 16,456 bytes | 0.65 s | 7 个 null、12 个空 array；`current_workcase_ref: null`、`selected_fact_refs: []` |
| 六项基础责任 L1 概览 | 00、01、02、04、05、06 的标题、路径和 overview | 10,057 bytes | 0.42 s | 12 个 null、7 个空 array；保留两项未机械证明的资格缺口 |

实际启动基线的原始上下文体量约为 64,335 bytes；再读取六项 L1 概览后约为 74,392 bytes。一次当次 shell 侧字段投影在保留项目身份、十项能力、能力来源、F0/F1、六项规则概览、coverage、验证和缺口后为 20,543 bytes，但这只是验证时的调用方派生视图，不是新的稳定接口、规则源或可跨环境依赖的 bootstrap packet。

空字段中有相当部分来自共同响应和 `capabilities` 的闭集契约，不能只因当前为空就删除。实测仍表明：如果调用方把完整管辖结果、通用能力结果和 F0/F1 原样连续注入，新会话会重复接收管辖来源和大量当次不适用字段；现有信息是结构化且可筛选的，但原样组合尚不能称为低成本。

## 4. 恢复能力判断

| 恢复问题 | 当次结论 | 依据与边界 |
|---|---|---|
| 当前工作对象属于哪个项目 | 已成立 | `scope_status: governed_single`，项目为 `ldvh`，实际 worktree/common-dir 和配置来源均可回指 |
| 当前有哪些公开能力 | 已成立 | 通用发现返回十项来源绑定操作及各自规则、实现和输入清单 |
| 当前规则从哪里继续读取 | 已成立 | operation source refs 回到 01、02、05、06；按需 L1 进一步返回 00、01、02、04、05、06 的实际路径和 overview |
| 当前事实集合是否完整扫描 | 已成立于空基线 | F0 指纹、五类十五种状态计数、invalid/unavailable 和 F1 coverage 均形成；当前全部计数为 0 |
| 当前应恢复哪个 WorkCase | 未成立 | `current_workcase_ref` 为 null，F1 没有 open/blocked WorkCase 卡片；Code 按来源不得猜测当前责任 |
| 已选择事实能否精确续读 | 未形成真实证据 | `selected_fact_refs` 为空且没有真实卡片，因而没有正向验证 `cards[].source_refs` → F3 的实际接续 |
| 能否恢复当前聊天中的临时计划或执行步骤 | 不应成立 | 聊天记忆、命令和临时步骤不是事实源；需要跨会话保留的当前责任必须进入适用事实或稳定项目文档 |
| 能否恢复 LDVH 全局推进位置 | 可通过仓库入口按需读取 | 根 `README.md` 回指唯一控制面 `V4-工作推进总纲.md`；它不是 Helper 事实卡，也不能替代真实 WorkCase |

## 5. 结论与下一 Gate

现有能力足以完成低风险 bootstrap 的机械部分：确定项目、确认规则源和 Helper 身份、发现能力、检查是否存在可恢复事实，并把后续精确规则/事实读取保持为按需操作。当前 adapter 只自动注入管辖结果；capabilities、F0/F1 和规则读取仍由 AI 按需组合，不是已经自动执行的环境流程。当前无需新增 Helper、公共字段、状态机、中央登记或自动摘要。

但“跨会话 resume 已成立”不能据此声明。当前真实来源没有 WorkCase 或其它事实对象，F1 正确返回空集合；这首先是没有可恢复责任，而不是 Helper 缺少另一个发现操作。原始响应体量也说明，未来真实 dogfood 应测量 AI 是否能够稳定只消费必要字段，而不是预先把四个完整响应无条件塞入 adapter。

下一 Gate 因此是 Human 选择一个真实受管辖工作，并决定是否建立 WorkCase。若建立，则使用现有 prepare/create/update、F0/F1 和 F3 完成一次真实中断与换会话恢复，核对当前责任、selected refs、事实来源指针、遗漏和上下文成本。只有该实测仍证明现有入口无法形成稳定边界时，才重新评估调用方组合、adapter 投影或 Helper 能力；本次不提前设计任何一项。

## 6. 验证收口

当次分别直接执行 adapter `startup`、`resume`，以及 Helper 的管辖解析、通用能力发现、F0/F1 和六项 L1 规则概览；相关 adapter、governance、Helper service/CLI、事实候选、规范候选和来源回指回归为 95 passed。父提交 `46d892e0` 已完成 787 passed、10 个原生 Windows 用例按既有条件 skipped 的全量回归；本增量只修改 README、当前推进总纲和本文，没有修改 Code、tests、Specs、插件或事实源，`git diff --check` 通过。
