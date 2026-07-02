# 环境插件样例包

本文档属于 Code 实现域，承接 `code/docs/02-Environment-Plugin-Practice.md`。本目录只保存 repo-local 环境插件样例包和安装前审计材料，不表示任何插件已安装、启用、trusted 或 integrated。

## 目录规则

每个目标环境应使用独立子目录：

| 路径 | 用途 |
|---|---|
| `codex-ldvh-v3/` | Codex lifecycle hook 样例包 |

后续新增环境样例包时，必须先确认目标环境支持的插件、扩展包或 package 形态，再补对应 manifest、Hook 配置、shim、状态检查和卸载边界。不得把 Codex 样例当成所有环境的总规则。

## 共同边界

环境插件样例包必须满足：

1. 只做薄 shim，核心逻辑留在 LDVH Code；
2. 不复制 specs、事实对象、行动模板、Human Gate 或管辖项目配置；
3. 只通过 LDVH root 定位 `code/runtime_adapter.py` 或稳定 Code 入口；
4. Hook 配置不得覆盖无关用户 Hook；
5. uninstall 只能移除或禁用 LDVH 自己写入的指针；
6. 未经 Human Gate，不得安装、升级、禁用、卸载或写入用户环境配置。

## 当前状态

当前目录只有样例包结构。真实环境状态仍以以下命令为准：

```bash
python3 code/environment_status.py --format text
python3 code/environment_entry_audit.py --format text
```

除当前 worktree 的 `git.commit-msg` 外，样例包存在不等于任何环境入口已自动触发。
