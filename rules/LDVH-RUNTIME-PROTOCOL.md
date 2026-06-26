# LDVH Runtime Protocol

```yaml
ldvh_asset:
  id: "ldvh-runtime-protocol"
  type: "rule"
  status: "active"
  canonical_path: "rules/LDVH-RUNTIME-PROTOCOL.md"
  source_specs:
    - "specs/06-运行时扩展规范.md"
    - "specs/attachments/06.Att.02-固定运行时扩展登记表.md"
  consumption_scenarios:
    - "AI Hook 路径：环境原生触发 canonical event，trigger_source=hook"
    - "Rules 路径：AI 自觉触发 canonical event，trigger_source=rules"
  inputs:
    - "当前工作目录（cwd）"
  outputs:
    - "canonical event 触发命令"
  handoff: "hook_dispatch.py 统一执行协议 handler；session-start 返回 receipt（read_plan + stop_conditions）指导后续行动；acknowledge-read-plan 写入消费证据；pre-tool-use / git.commit-msg 对写入和提交执行硬门禁"
  verification:
    - "python3 code/hook_dispatch.py run session-start --trigger-source rules --cwd <path>"
    - "python3 code/hook_dispatch.py run acknowledge-read-plan --trigger-source rules --cwd <path>"
    - "python3 code/hook_dispatch.py run pre-tool-use --trigger-source rules --cwd <path>"
    - "python3 code/hook_dispatch.py run git.commit-msg --trigger-source rules --message-file <path>"
  sync_triggers:
    - "specs/06 §7 的 canonical event、trigger_source 或 hook_dispatch.py 接口变化"
  deprecation: "废弃前必须评估 Human Gate，并同步 specs/06、06.Att.02 登记表和 hook_dispatch.py"
```

> 文件性质：LDVH 固定 Rules 资产，承载 Runtime Protocol；不是正式规范。
> 来源：合并自 `rules/LDVH-ENTRY.md` + `rules/LDVH-LIFECYCLE-PROTOCOL.md`。
> 规范来源：`specs/06-运行时扩展规范.md` §7。

## 1. 这是什么

LDVH 运行时协议。定义 AI 在三个关键环节必须触发的 canonical event。

两种消费路径：

- **Hook 路径**：环境原生触发，`trigger_source=hook`
- **Rules 路径**：AI 读本协议后自觉触发，`trigger_source=rules`

同一 handler，不写两份逻辑。

## 2. 四事件触发表

| 发生时 | canonical event | Rules 路径命令 |
|---|---|---|
| 会话开始 / 恢复 / 上下文压缩后 / 子 Agent 启动 | `session-start` | `python3 code/hook_dispatch.py run session-start --trigger-source rules --cwd <cwd>` |
| AI 已按 receipt 回读 P0/P1 read_plan 后 | `acknowledge-read-plan` | `python3 code/hook_dispatch.py run acknowledge-read-plan --trigger-source rules --cwd <cwd>` |
| Write / Edit 前 | `pre-tool-use` | `python3 code/hook_dispatch.py run pre-tool-use --trigger-source rules --cwd <cwd>` |
| Git commit 前 | `git.commit-msg` | `python3 code/hook_dispatch.py run git.commit-msg --trigger-source rules --message-file <message-file>` |

Hook 路径：环境适配层将原生事件名映射为 canonical event 后，通过 stdin 传入 `{"event":"<canonical>","cwd":"...","trigger_source":"hook"}` 或环境等价 payload。Codex 当前 payload 使用 `hook_event_name`、`tool_name`、`session_id` 等字段，dispatcher 必须先归一化再执行 canonical handler。

## 3. 消费 receipt

`session-start` 返回 receipt，包含 `governed`、`read_plan`（P0/P1 必读原文列表）、`stop_conditions`。AI 必须按 read_plan P0/P1 顺序读取权威原文，不得跳过。

AI 读完 P0/P1 后必须触发 `acknowledge-read-plan`，在对应 session receipt 中写入 `read_plan_consumed.status=acknowledged`、确认时间和 required paths。该确认是 AI 对已消费入口读取计划的运行证据，不替代规范、事实源或验证证据。

`governed=false` 时 no-op：当前目录不在管辖项目中。若当前目录是 Codex worktree 或 Git worktree，dispatcher 可通过 Git `common_dir` 与 `LDVH-GOVERNED-PROJECTS.yaml` 登记项目匹配；AI 不得用路径相似或记忆自行判定管辖关系。receipt 若包含 `governed_via`、`governed_project_id`、`governed_project_path` 或 `git_common_dir`，应作为本轮运行链路证据消费。

支持 `session_id` 的 Hook 环境应把 receipt 写入用户级运行时状态。Codex 使用 `~/.codex/ldvh/session-receipts/<session_id>.json`。该文件只证明当前环境会话完成或补建了 Runtime Protocol 握手，不是事实源，不得替代 Git 文件事实源、规范、WorkCase 或验证证据。

若当前环境未在对话中展示 `SessionStart` 输出，AI 不得直接判定 Hook 无效；应检查是否存在对应 session receipt，或由 `PreToolUse` 在管辖项目中补建 receipt。`PreToolUse` 输出中的 `session_receipt=found` 或 `session_receipt=created_by_pre_tool_use` 只表示握手证据存在或已补建，不表示 AI 已消费 read_plan。

在管辖项目内，`pre-tool-use` 对 Write / Edit / apply_patch / 明确写入型 Bash 等写类工具执行硬门禁：若找不到 `read_plan_consumed.status=acknowledged`，必须阻断并返回 required paths 与 next action。`git.commit-msg` 在提交前也必须检查最近匹配当前 cwd 的 session receipt；缺少 read_plan 消费证据时阻断提交。只读命令可继续执行，但仍应保留 warning 或 receipt 查验证据。支持 `session_id` 且已存在 receipt 的环境，`PreToolUse` 应在 receipt 中更新 `last_pre_tool_use` 或等价可观测字段，使新会话验收能区分“只有 SessionStart 生效”和“工具前检查也确实触发”。

## 4. STOP

- `session-start` 返回 `governed=false` → no-op
- knowledge-map 不可用 → 退回 active specs 原文和 Git 文件事实源
- 写入 / 提交前缺少 `read_plan_consumed.status=acknowledged` → blocking，先回读 P0/P1 并运行 `acknowledge-read-plan`
- 涉及 Human Gate 的操作 → 暂停等待 Human 确认
