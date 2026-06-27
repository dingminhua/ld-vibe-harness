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
    - "当前工作目录（cwd，target 缺失时的 fallback）"
    - "本次操作实际工作对象（target）"
  outputs:
    - "canonical event 触发命令"
  handoff: "hook_dispatch.py 统一执行 canonical event handler；Rules 入口只负责派发事件，后续处理与 next_action 以 dispatcher 输出为准"
  verification:
    - "python3 code/hook_dispatch.py run session-start --trigger-source rules --cwd <cwd> --target <target>"
    - "python3 code/hook_dispatch.py run acknowledge-read-plan --trigger-source rules --cwd <cwd>"
    - "python3 code/hook_dispatch.py run pre-tool-use --trigger-source rules --cwd <cwd> --target <target>"
    - "python3 code/hook_dispatch.py run git.commit-msg --trigger-source rules --message-file <path>"
  sync_triggers:
    - "specs/06 §7 的 canonical event、trigger_source 或 hook_dispatch.py 接口变化"
  deprecation: "废弃前必须评估 Human Gate，并同步 specs/06、06.Att.02 登记表和 hook_dispatch.py"
```

> 文件性质：LDVH 固定 Rules 资产，承载 Runtime Protocol；不是正式规范。
> 来源：合并自 `rules/LDVH-ENTRY.md` + `rules/LDVH-LIFECYCLE-PROTOCOL.md`。
> 规范来源：`specs/06-运行时扩展规范.md` §7。

## 1. 这是什么

LDVH 固定 Rules 入口。它只列出 AI 在 Rules 路径如何把 canonical event 派发给 `hook_dispatch.py`，用于在无原生 Hook 或 Hook 不可观测时模拟同一个事件入口。

两种消费路径：

- **Hook 路径**：环境原生触发，`trigger_source=hook`
- **Rules 路径**：AI 读本协议后自觉触发，`trigger_source=rules`

同一 handler，不写两份逻辑。Rules 路径只负责触发 canonical event；触发后的处理和 next_action 必须由 `hook_dispatch.py` 的同一 dispatcher handler 给出。AI 不得依据本文 prose 自行判定放行或阻断。

本文不得维护 Git 提交行动流程、Skill 执行规则、commit message 契约、Code/Web Schema 或 dispatcher 字段细节；需要时只给出 dispatcher 命令并回指 `source_specs`。

## 2. 四事件触发表

| 发生时 | canonical event | Rules 路径命令 |
|---|---|---|
| 会话开始 / 恢复 / 上下文压缩后 / 子 Agent 启动 | `session-start` | `python3 code/hook_dispatch.py run session-start --trigger-source rules --cwd <cwd> --target <target>` |
| dispatcher 输出要求确认入口读取后 | `acknowledge-read-plan` | `python3 code/hook_dispatch.py run acknowledge-read-plan --trigger-source rules --cwd <cwd>` |
| Write / Edit 前 | `pre-tool-use` | `python3 code/hook_dispatch.py run pre-tool-use --trigger-source rules --cwd <cwd> --target <target>` |
| Git commit 前 | `git.commit-msg` | `python3 code/hook_dispatch.py run git.commit-msg --trigger-source rules --message-file <message-file>` |

Hook 路径：环境适配层将原生事件名映射为 canonical event，并把环境 payload 交给同一个 dispatcher。payload 归一化、字段解释和阻断语义由 Code 与来源规范负责，本文不展开。

## 3. 消费 dispatcher 输出

Rules 路径执行表内命令后，AI 只消费 dispatcher 返回的结构化输出：按其中的 `read_plan`、`next_action`、`stop_conditions`、blocking 状态和回指路径继续行动。

dispatcher 输出要求补充读取、确认、显式 target、Human Gate 或停止时，AI 必须回到对应命令或来源规范，不得用本文 prose 自行放行。

canonical event 之后的字段与逻辑属于 `hook_dispatch.py` 和 `source_specs` 的责任；本文只保留派发入口。

## 4. STOP

只要 dispatcher 返回 blocking、Human Gate、缺少 target、缺少确认或其它停止条件，AI 必须停止当前动作并按 dispatcher 的 `next_action` 或回指规范处理。
