# 27B Git Hook 正式接入：poker 管辖项目

文件状态：execution record。本文记录 `poker-train-card` 和 `poker-train-video` 的 Git `commit-msg` hook 正式接入结果。

## 目标

将两个已登记的 poker 管辖项目接入 LDVH V3 Git 提交门禁：

1. `poker-train-card`；
2. `poker-train-video`。

本次只接入 Git Hook，不接入环境 Hook，不创建真实业务 commit，不修改 poker 项目业务文件。

## Human Gate

Human 已在当前对话中确认：“清楚了，按你计划行动”。本记录将其解释为授权对上述两个已登记管辖项目安装 Git `commit-msg` 薄 shim，并验证成功路径、失败路径和状态检查。

授权范围不包含：

1. 安装 Codex、Trae、IDE、Agent 或其它环境 Hook；
2. 对未登记项目安装 Hook；
3. 创建业务提交；
4. 修改 poker 项目业务文件；
5. 使用 `git commit --no-verify` 绕过 Hook。

## 安装模型

外部管辖项目使用 Git 本地目录承载薄 shim：

```text
<target-repo>/.git/ldvh-hooks/commit-msg
```

每个目标 repo 的 worktree-local 配置为：

```bash
git config --worktree core.hooksPath <target-repo>/.git/ldvh-hooks
```

该模型的目的：

1. 目标 repo 的真实 `git commit` 会触发 LDVH `commit-msg` gate；
2. shim 只定位 LDVH validator，不复制 specs、事实源、管辖项目规则或校验逻辑；
3. hook 文件不进入业务工作树，不产生 `git status` 未跟踪文件；
4. LDVH 自身仍使用仓库内 `hooks/commit-msg` 作为模板和本仓库 Hook。

## 安装结果

### poker-train-card

安装状态：

1. `governed: true`；
2. `governed_project_id: poker-train-card`；
3. `hook_installed: true`；
4. `hook_integrated: git.commit-msg`；
5. `core_hooks_path: /Users/dmh2002/poker_hud_projects/poker-train-card/.git/ldvh-hooks`；
6. `active_hook: /Users/dmh2002/poker_hud_projects/poker-train-card/.git/ldvh-hooks/commit-msg`；
7. `diagnostics: 0`。

### poker-train-video

安装状态：

1. `governed: true`；
2. `governed_project_id: poker-train-video`；
3. `hook_installed: true`；
4. `hook_integrated: git.commit-msg`；
5. `core_hooks_path: /Users/dmh2002/poker_hud_projects/poker-train-video/.git/ldvh-hooks`；
6. `active_hook: /Users/dmh2002/poker_hud_projects/poker-train-video/.git/ldvh-hooks/commit-msg`；
7. `diagnostics: 0`。

## 验证结果

验证方式：

1. 在目标 repo 中临时 stage `.ldvh-hook-check.tmp`；
2. 从目标 repo 根目录触发 `.git/ldvh-hooks/commit-msg`；
3. 合法消息使用 `docs(docs): 验证<project>提交hook`；
4. 非法消息使用 `invalid header`；
5. 验证后撤销临时 staged 文件并删除临时文件。

验证结果：

| 项目 | 合法消息 | 非法消息 | changed paths | diagnostics |
|---|---:|---:|---:|---|
| `poker-train-card` | exit `0`, status `ok` | exit `1`, status `blocked` | `1` | 合法消息 none；非法消息 `COMMIT_HEADER_INVALID` |
| `poker-train-video` | exit `0`, status `ok` | exit `1`, status `blocked` | `1` | 合法消息 none；非法消息 `COMMIT_HEADER_INVALID` |

最终状态：

1. `poker-train-card` 的 `git status --short --untracked-files=all` 为空；
2. `poker-train-video` 的 `git status --short --untracked-files=all` 为空；
3. 两个项目的 `core.hooksPath` 均指向各自 `.git/ldvh-hooks`；
4. 两个项目的 `commit-msg` shim 均可执行。

## 结论

两个 poker 管辖项目已经正式接入 V3 Git `commit-msg` 提交门禁。此后通过这两个 repo 创建真实 `git commit` 时，提交消息会按 LDVH V3 commit gate 校验。

边界仍然成立：

1. 这是 Git Hook 接入，不是环境 Hook 接入；
2. AI 的提交前行动仍需按 LDVH 行动规则执行；
3. `git commit --no-verify` 可以绕过 Git Hook；
4. 新 clone、新机器或重建 worktree 需要重新安装 Hook；
5. 卸载应通过 `code/governed_hook_adapter.py uninstall` 执行。
