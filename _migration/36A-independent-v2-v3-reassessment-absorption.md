# 36A 独立 V2/V3 复核吸收记录

文件状态：migration audit absorption。本文吸收子对话 `019f2180-8fad-7db2-a1a0-3710b05bf3c7` 对 V2 到 V3 迁移完成度的只读复核结论。本文不授权新环境入口、不安装插件、不恢复 Rules / Skill 顶层机制、不改变 V2 正式关闭记录。

## 背景

在 `c572fc3d docs(runtime): 补 Runtime Protocol hook 入口` 之后，Human 要求新对话重新评估：

1. V2 有效内容是否已经迁移、吸收、强化、后置或废弃；
2. V3 是否相对 V2 有加强；
3. V3 是否脱离 V2 / V3 `00` 的价值判断；
4. Runtime Protocol、薄引用、Hook、插件、receipt 和行动模板是否有遗漏。

本轮复核使用的口径是来源条目级追踪，不按文件名逐字复刻判断完成。

## 吸收结论

复核结论为：无 P0。V2 主体可以维持正式关闭，V3 可以维持当前主线启动；但不得声明 V3 已完整恢复或接管 V2 的全部 runtime / environment hook 自动化能力。

需要固定下来的判断：

1. V3 不是逐文件复刻 V2，而是把 V2 `06` 运行时扩展体系拆分到 `01` 保障与衔接、`10` 管辖项目配置、`30` 安装初始化行动模板、`07` Code 契约、`code/`、`code/docs/` 和 `tests/`；
2. V3 取消 `rules/` 和 `skills/` 顶层机制的方向是正确的，不应因为补 Runtime Protocol 可见入口而恢复第二规则源；
3. `hooks/LDVH-RUNTIME-PROTOCOL.md` 只是 hook-visible entry，状态为可见入口，不是环境自动触发证明；
4. 当前只有 `git.commit-msg` 可以声明为 integrated 自动入口；
5. `session_start`、`pre_tool_use`、`completion_claim` 和 runtime adapter 仍是 manual-ready / external-adapter-ready，不是 integrated；
6. 本机 Codex 插件审计发现仍可能指向 V2 旧路径时，只能记为 stale / available，不得声明为 V3 integrated；
7. V2 `06.Att.09` 外部环境薄引用模板没有完整等价物，V3 需要补一个不恢复 `rules/` 的薄引用模板；
8. V2 `acknowledge_read_plan` / persistent receipt 链路在 V3 中被收窄，需要决定是补入口，还是明确由独立 CLI、validator、runtime receipt 或验证声明承接。

## 关键覆盖判断

| V2 来源 | V3 当前承接 | 复核判定 | 吸收动作 |
|---|---|---|---|
| `specs/06-运行时扩展规范.md` 父层语义 | `specs/01-保障与衔接.md` §6、`01.Att.03-06`、`code/environment_entry_audit.py` | absorbed / strengthened | 维持 01 归口，不恢复运行时扩展为构成要素 |
| V2 canonical events、Hook / Rules 同语义 | `01.Att.01`、`01.Att.05`、`code/runtime_adapter.py` | absorbed / partial | 保留 manual-ready 边界，后续补环境 Hook 真实集成证据 |
| V2 `acknowledge_read_plan`、session receipt、写入门禁 | `01` receipt 边界、`runtime_adapter.py`、Code validator | absorbed / narrowed | 列为 P1 决策：补入口或明确替代承接 |
| V2 `06.Att.09` 外部环境薄引用模板 | `hooks/LDVH-RUNTIME-PROTOCOL.md`、`01.Att.03` | missing / postposed | 列为 P2：补 V3 薄引用模板，但不恢复 `rules/` |
| V2 `hooks/ldvh-hooks.yaml` 多事件 registry | `code/environment_plugins/` 样例、`environment_entry_audit.py`、`01.Att.03-06` | absorbed / postposed | 不声明通用 Hook registry 已完成 |
| V2 Runtime Protocol Rule | `hooks/LDVH-RUNTIME-PROTOCOL.md` | migrated / strengthened | 维持 hook entry 的三类内容限制 |
| V2 Workspace / Maintainer Rules | removed_top_level | discarded | 不恢复顶层 Rules wrapper |
| V2 Skill `ldvh-git-commit` | `06` Git 提交行动、`code/docs/01-Git-Commit-and-Hook-Practice.md`、commit validator | absorbed / strengthened | 维持行动模板和 Code 实现域承接 |
| V2 `33` 安装初始化行动 | `specs/30-LDVH安装初始化管辖项目配置行动模板.md` | migrated / strengthened | 维持 30 独立模板 |
| V2 `32` 环境适配动态投影 | `01`、`30`、`code/docs/02-Environment-Plugin-Practice.md` | postposed / partial | 只在真实插件闭环出现后推进 |

## P1 吸收项

### P1-1 环境 Hook / 插件自动入口未闭环

当前 V3 只能声明：

1. 当前 worktree `git.commit-msg` integrated；
2. Runtime Protocol entry available；
3. manual runtime entrypoints available；
4. 环境插件样例和审计入口存在。

当前 V3 不能声明：

1. Codex / Trae / Claude Code / IDE 环境 Hook 已自动触发；
2. `session_start`、`pre_tool_use` 或 `completion_claim` 已 integrated；
3. stale V2 plugin path 等价于 V3 插件已安装；
4. `hooks/LDVH-RUNTIME-PROTOCOL.md` 本身证明环境接入完成。

后续若推进，必须走 Human Gate，并补齐真实触发点、payload、失败处理、安装状态、回滚方式和正反测试。

### P1-2 `acknowledge_read_plan` / receipt 链路需要决策

V2 曾有更完整的 read-plan acknowledgement 和 persistent receipt 链路。V3 当前把 receipt 约束收敛为 stdout-only / 过程证据，并禁止把 receipt 直接升级为事实源。

后续必须二选一：

1. 在 Code runtime adapter 或相关 CLI 中重新暴露明确的 `acknowledge_read_plan` 承接入口；
2. 明确写成由独立 validator、commit gate、验证声明字段或当次 runtime receipt 承接，不再保留独立 canonical event。

在该决策完成前，不得声明 V2 read-plan acknowledgement 链路已经完整等价迁移。

## P2 吸收项

### P2-1 V3 薄引用模板

V3 需要补一个面向无 Hook 或只支持薄引用环境的模板。该模板应：

1. 指向 `hooks/LDVH-RUNTIME-PROTOCOL.md`；
2. 指向 `specs/01-保障与衔接.md`、`01.Att.01`、`01.Att.03`、`01.Att.05`；
3. 只说明入口、读取顺序和回到 V3 specs 的要求；
4. 不复制 specs 规则；
5. 不恢复 `rules/` 目录或 Rules registry；
6. 不声明任何环境 integrated。

### P2-2 环境插件正反测试

真实插件推进前，需要测试覆盖：

1. payload 透传；
2. PreToolUse 阻断；
3. Stop / completion 非阻断或降级处理；
4. stale V2 path 检测；
5. install / uninstall / rollback。

### P2-3 `git.common_dir` 稳定性

受管项目和 worktree / dogfood 场景可以补 `git.common_dir` 身份线索，提高 target-first resolver 的稳定性。该项不是 V3 启动阻断。

## 后续使用方式

以后判断 V2 是否迁完时，必须按以下方式处理：

1. 先拆 V2 来源条目，而不是只看 V3 是否有同名文件；
2. 对每个条目标注 migrated、absorbed、strengthened、postposed、discarded、missing 或 unclear；
3. 必须给出 V3 目标文件和责任域；
4. 不得把合理精简误判为丢失；
5. 不得把泛化表述误判为完整迁移；
6. 不得把 available、manual-ready 或 visible entry 写成 integrated；
7. 不得用 Code、Web、测试、receipt 或 Hook 输出替代 specs、事实源或 Human Gate。

## 结论

本文不推翻 `_migration/25A-v2-official-closure.md` 的 V2 关闭记录，但收紧 V3 后续表述：

1. 可以说：V2 主体已关闭，V3 是当前主线；
2. 可以说：V3 相对 V2 在规则归口、事实源、行动模板、Code/Web 边界和环境入口状态上有加强；
3. 不可以说：V3 的环境 Hook / 插件自动入口已经完整接管；
4. 不可以说：V2 薄引用模板和 read-plan acknowledgement 链路已经完整等价迁入。
