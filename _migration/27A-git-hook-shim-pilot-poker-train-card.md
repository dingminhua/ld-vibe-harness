# 27A Git Hook Shim 试点：poker-train-card

文件状态：pilot record。本文记录 `poker-train-card` 的 Git `commit-msg` hook shim 试点，不授权批量安装其它项目，不授权环境 Hook 自动接入，不改变 specs 规则源。

## 目标

验证 V3 已明确的 Git Hook 模型：

1. Git hook 安装在目标 Git repo 中；
2. 目标 repo 中的 hook 只能是薄 shim；
3. 核心逻辑保留在 LDVH V3；
4. LDVH 读取工作区级 `LDVH-GOVERNED-PROJECTS.yaml` 判定目标是否为管辖项目；
5. 安装、状态检查、触发验证和卸载回滚均可复现。

## Human Gate

Human 在当前对话中要求“你行动吧”。本记录将其解释为授权对单个试点项目 `poker-train-card` 执行 Git hook shim 试点。授权范围仅限：

1. 对 `poker-train-card` 运行 `governed_hook_adapter.py status`；
2. 对 `poker-train-card` 安装 LDVH managed `commit-msg` hook shim；
3. 手动执行 hook 验证成功路径和失败路径；
4. 验证卸载回滚路径。

不包含：

1. 对 `poker-train-video` 安装 hook；
2. 创建真实业务 commit；
3. 接入环境 Hook；
4. 修改 poker 项目业务文件；
5. 批量安装其它项目。

## 初始状态

状态检查命令：

```bash
python3 code/governed_hook_adapter.py status \
  --repo /Users/dmh2002/poker_hud_projects/poker-train-card \
  --governance-root /Users/dmh2002/poker_hud_projects \
  --ldvh-root /Users/dmh2002/poker_hud_projects/ld-vibe-harness-v3 \
  --format json
```

结果：

1. `governed: true`；
2. `governed_project_id: poker-train-card`；
3. `governed_via: path`；
4. `hook_installed: false`；
5. `hook_integrated: none`；
6. `diagnostics: 0`。

## 安装验证

安装命令：

```bash
python3 code/governed_hook_adapter.py install \
  --repo /Users/dmh2002/poker_hud_projects/poker-train-card \
  --governance-root /Users/dmh2002/poker_hud_projects \
  --ldvh-root /Users/dmh2002/poker_hud_projects/ld-vibe-harness-v3 \
  --confirm-human-gate \
  --format json
```

结果：

1. `status: ok`；
2. `governed_project_id: poker-train-card`；
3. `hook_integrated: git.commit-msg`；
4. `active_hook: /Users/dmh2002/poker_hud_projects/poker-train-card/hooks/commit-msg`；
5. `core_hooks_path: hooks`；
6. `common_hook_exists: false`；
7. `human_gate_confirmed: true`。

安装后的目标 repo hook 是薄 shim。它只定位目标 repo、定位 LDVH validator，并调用 `code/commit_validate.py`；校验逻辑、契约读取和 Human Gate 规则均保留在 LDVH。

首次手动触发时发现实现缺口：外部 repo 通过 hook 调用 `commit_validate.py --repo <target-repo>` 后，validator 把目标 repo 当成 specs 根目录，尝试读取 `poker-train-card/specs/attachments/03.Att.01-Commit-Message契约字段表.md`，导致 `FileNotFoundError`。这是 Code 实现问题，不是模型边界问题。

已修正：

1. `code/commit_validate.py` 增加 `--ldvh-root`，并使用 LDVH 根读取 specs、附件和提交契约；
2. `--repo` 仅表示目标 Git repo，用于读取 staged paths；
3. `hooks/commit-msg` 显式传入 `--ldvh-root "$LDVH_ROOT"`；
4. `code/install_git_hooks.py uninstall` 对外部 repo 会删除 LDVH managed shim，并保留 LDVH 自身模板。

修正后手动触发结果：

1. 合法消息 `docs(docs): 验证外部hook` 返回 `0`，`environment_integrated: True`；
2. 因未提供 staged paths，输出 warning `COMMIT_CHANGED_PATHS_MISSING`，不阻断；
3. 非法消息 `invalid header` 返回 `1`，输出 blocking `COMMIT_HEADER_INVALID`；
4. 不再出现 `FileNotFoundError`。

## 回滚验证

回滚命令：

```bash
python3 code/governed_hook_adapter.py uninstall \
  --repo /Users/dmh2002/poker_hud_projects/poker-train-card \
  --governance-root /Users/dmh2002/poker_hud_projects \
  --ldvh-root /Users/dmh2002/poker_hud_projects/ld-vibe-harness-v3 \
  --confirm-human-gate \
  --format json
```

结果：

1. `status: ok`；
2. `hook_installed: false`；
3. `hook_integrated: none`；
4. `core_hooks_path: ""`；
5. `active_hook_exists: false`；
6. `diagnostics: 0`；
7. `poker-train-card` 的 `git status --short --untracked-files=all` 为空。

## 结论

本次试点验证了 V3 当前 Git Hook 架构可以成立：

1. 外部 Git repo 只安装薄 shim；
2. LDVH 通过工作区级管辖项目配置判断目标是否受管；
3. 提交校验逻辑和 specs 契约读取保留在 LDVH；
4. 安装、状态检查、手动触发、失败阻断和卸载回滚均可复现；
5. 试点结束后没有在 `poker-train-card` 留下 hook 或业务文件改动。

本记录不表示 `poker-train-video` 或其它项目已经安装 Hook。批量安装、环境 Hook 接入和真实业务提交仍需单独 Human Gate。
