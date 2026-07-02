# 28A Codex 插件环境入口对齐

文件状态：environment entry alignment。本文记录 V3 对 Codex lifecycle Hook 与 LDVH plugin 安装口径的重新对齐，不安装新插件，不修改用户级 Codex 配置，不声明 V3 环境 Hook 已接入。

## 背景

Human 指出：LDVH 应以插件方式安装，V2 中已有该设计，V3 必须明确。

本次复核后确认：

1. Codex 当前支持 lifecycle hooks；
2. hooks 可来自用户级配置、项目级 `.codex`、或已安装插件；
3. `SessionStart`、`PreToolUse`、`Stop` 等事件可作为 V3 session start、pre tool use、completion-adjacent 入口候选；
4. 非 managed command hook 需要 review/trust；
5. 插件可捆绑 lifecycle Hook 配置。

因此，V3 不能继续把 Codex 环境 Hook 只写成“没有真实触发点”。更准确的口径是：

> Codex 有可接机制；V3 的正式接入形态必须是 LDVH Codex plugin。未完成 V3 plugin 安装、trust、payload、失败处理和回滚验证前，不得声明 integrated。

## 本机现状

只读检查结果：

1. `/Users/dmh2002/.codex/hooks.json` 当前为空；
2. `/Users/dmh2002/.codex/config.toml` 中 `ldvh@personal` 插件已启用；
3. 当前插件缓存存在 `hooks/hooks.json`；
4. 该插件 Hook 指向 `/Users/dmh2002/poker_hud_projects/ld-vibe-harness/code/hook_adapter.py`；
5. 当前 V3 根目录是 `/Users/dmh2002/poker_hud_projects/ld-vibe-harness-v3`；
6. 当前 V3 没有 `code/hook_adapter.py` 或 `code/hook_dispatch.py`，只有 `code/runtime_adapter.py`、`code/session_start.py`、`code/pre_tool_use.py` 和 `code/completion_claim.py`。

结论：

1. `ldvh@personal` 不能声明为 V3 environment integrated；
2. 旧插件或历史 trust 记录只能作为迁移输入；
3. V3 后续需要构建或升级 LDVH Codex plugin，使其薄 shim 指向 V3 runtime adapter；
4. 安装或升级插件会改变真实 Codex lifecycle 行为，必须另走 Human Gate。

## 已落账改动

1. `specs/01-保障与衔接.md`：明确 Codex 生命周期环境 Hook 的正式安装形态应是 LDVH Codex plugin；
2. `specs/attachments/01.Att.03-环境入口类型表.md`：把 Codex 插件作为 `environment_hook` 的正式承载方式；
3. `specs/attachments/01.Att.06-环境安装回滚检查表.md`：安装检查项加入插件 manifest、trust 状态和插件 Hook 配置；
4. `code/environment_entry_audit.py`：新增 `codex.ldvh-plugin` 候选，能识别旧插件指向 V2 路径；
5. `tests/code/test_ldvh_specs_validate.py`：增加旧插件负例；
6. `README.md` 与 `10G`：更新当前环境入口口径。

## 后续进入条件

进入 V3 Codex plugin 实装前，需要满足：

1. 明确插件包位置、manifest、hooks.json 和 shim 文件；
2. shim 只调用 V3 runtime adapter，不复制 specs、事实源、行动模板或 Human Gate 判断；
3. 明确 Codex `SessionStart`、`PreToolUse`、`Stop` 到 V3 event 的 payload 映射；
4. 明确失败处理：哪些事件可阻断、哪些只能 diagnostic；
5. 明确安装、trust、升级、禁用和卸载步骤；
6. 通过 `environment_entry_audit.py` 检查插件指向 V3；
7. 经 Human Gate 后再安装或升级真实插件。

## 边界

本次不做：

1. 不修改 `/Users/dmh2002/.codex/config.toml`；
2. 不修改 `/Users/dmh2002/.codex/hooks.json`；
3. 不升级 `/Users/dmh2002/plugins/ldvh`；
4. 不声明 V3 `SessionStart`、`PreToolUse` 或 `Stop` 已 integrated；
5. 不恢复 V3 `rules/` 或 `skills/` 顶层机制。
