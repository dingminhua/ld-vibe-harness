# LDVH Runtime Protocol

```yaml
ldvh_asset:
  id: "ldvh-runtime-protocol"
  type: "rule"
  status: "active"
  canonical_path: "rules/LDVH-RUNTIME-PROTOCOL.md"
  source_specs:
    - "specs/06-运行时扩展规范.md"
  consumption_scenarios:
    - "AI Hook 路径：环境原生触发 canonical event，trigger_source=hook"
    - "Rules 路径：AI 自觉触发 canonical event，trigger_source=rules"
  inputs:
    - "当前工作目录（cwd）"
  outputs:
    - "canonical event 触发命令"
  handoff: "hook_dispatch.py 统一执行协议 handler；session-start 返回 receipt（read_plan + stop_conditions）指导后续行动"
  verification:
    - "python3 code/hook_dispatch.py run session-start --trigger-source rules --cwd <path>"
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

## 2. 三事件触发表

| 发生时 | canonical event | Rules 路径命令 |
|---|---|---|
| 会话开始 / 恢复 / 上下文压缩后 | `session-start` | `python3 code/hook_dispatch.py run session-start --trigger-source rules --cwd <cwd>` |
| Write / Edit 前 | `pre-tool-use` | `python3 code/hook_dispatch.py run pre-tool-use --trigger-source rules --cwd <cwd>` |
| Git commit 前 | `git.commit-msg` | `python3 code/hook_dispatch.py run git.commit-msg --trigger-source rules --message-file <message-file>` |

Hook 路径：环境适配层将原生事件名映射为 canonical event 后，通过 stdin 传入 `{"event":"<canonical>","cwd":"...","trigger_source":"hook"}`。

## 3. 消费 receipt

`session-start` 返回 receipt，包含 `governed`、`read_plan`（P0/P1 必读原文列表）、`stop_conditions`。AI 必须按 read_plan P0/P1 顺序读取权威原文，不得跳过。

`governed=false` 时 no-op：当前目录不在管辖项目中。

## 4. STOP

- `session-start` 返回 `governed=false` → no-op
- knowledge-map 不可用 → 退回 active specs 原文和 Git 文件事实源
- 涉及 Human Gate 的操作 → 暂停等待 Human 确认
