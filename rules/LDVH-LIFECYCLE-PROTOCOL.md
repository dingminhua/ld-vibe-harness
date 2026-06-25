# LDVH 生命周期协议

```yaml
ldvh_asset:
  id: "ldvh-lifecycle-protocol"
  type: "rule"
  status: "active"
  canonical_path: "rules/LDVH-LIFECYCLE-PROTOCOL.md"
  source_specs:
    - "specs/06-运行时扩展规范.md"
  consumption_scenarios:
    - "AI Hook 路径：SessionStart / PreToolUse / git.commit-msg 事件触发"
    - "Rules 路径：AI 自觉读取并执行协议步骤"
    - "两种路径通过 hook_dispatch.py 统一调用同一 handler"
  inputs:
    - "当前工作目录（cwd）"
    - "环境 Hook 事件名或 AI 自觉触发场景"
  outputs:
    - "每个协议步骤的固定动作和对应命令"
  handoff: "协议本身不负责工作对象处理或产品资产维护；按工作区入口或维护入口进一步路由"
  verification:
    - "python3 code/hook_dispatch.py run session-start --cwd <path>"
    - "python3 code/hook_dispatch.py run pre-tool-use --cwd <path>"
    - "python3 code/hook_dispatch.py run git.commit-msg --message-file <path>"
  sync_triggers:
    - "source_specs 中 specs/06 §7 的协议-Hook-事件映射规则变化"
    - "hook_dispatch.py 的 run 子命令或 handler 接口变化"
    - "新增或废弃 AI Hook 事件"
  deprecation: "废弃前必须评估 Human Gate，并同步 specs/06、06.Att.02 登记表和 hook_dispatch.py"
```

> 文件性质：LDVH 固定 Rules 资产，承载生命周期协议步骤；不是正式规范，不定义设计规则。
> 规范来源：`specs/06-运行时扩展规范.md` §7。
> 适用范围：AI Hook 强制消费路径和 Rules 自觉消费路径，两种路径共享同一份协议步骤。

## 协议步骤

本表定义 AI 在每个关键环节的必做动作。所有步骤不随任务变化，每次固定执行。

| 步骤 | AI Hook 事件 | 触发条件 | 动作 | 命令 |
|---|---|---|---|---|
| 握手 | `SessionStart` | 新会话 / 线程恢复 / 上下文压缩 / 任务开始 | 判定环境类型，补全入口链，返回 receipt | `python3 code/hook_dispatch.py run session-start --cwd <cwd>` |
| 写前确认 | `PreToolUse` | Write / Edit 工具调用前 | 检查本次会话 receipt 是否存在 | `python3 code/hook_dispatch.py run pre-tool-use --cwd <cwd>` |
| 提交校验 | `git.commit-msg` | Git commit 前 | 校验 commit message 格式、追溯和签名 | `python3 code/hook_dispatch.py run git.commit-msg --message-file <message-file>` |

以下事件为候选，待环境实测后启用：

| 步骤 | AI Hook 事件 | 触发条件 | 动作 |
|---|---|---|---|
| 压缩恢复 | `PostCompact`（候选） | 上下文压缩后 | 同握手，重新判定环境、补入口链、返回 receipt |
| 用户输入前置检查 | `UserPromptSubmit`（候选） | 用户输入提交前 | 检查当前上下文、入口状态或风险提示 |

## 消费方式

- **AI Hook 路径**：环境在对应事件触发时自动调用命令，通过 stdin 传入 event 和 payload（cwd、session_id 等）。
- **Rules 路径**：AI 读取本协议后，在对应触发条件出现时自觉执行命令。CLI 参数代替 stdin，`hook_dispatch.py` 执行同一 handler。

两种路径共享同一份协议步骤和同一套 handler，区别仅在于谁发起调用。

> **已废弃**: 合并为 [rules/LDVH-RUNTIME-PROTOCOL.md](LDVH-RUNTIME-PROTOCOL.md)。本文不再独立使用。
