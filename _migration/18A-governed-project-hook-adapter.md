# 18A 外部受管项目 Hook adapter

文件状态：阶段 18 记录。本文记录外部受管项目 `git.commit-msg` Hook adapter 的实现边界，不授权自动安装到任何外部项目，不扩大 session start、pre tool use、completion claim 或 Web 写入能力。

## 读取依据

1. `specs/00-理念与构成.md`
2. `specs/01-保障与衔接.md`
3. `specs/02-AI行为规范.md`
4. `specs/10-安装与配置规范.md`
5. `specs/01-保障与衔接.md` §6 与 `specs/attachments/01.Att.03-06`
6. `specs/09-测试与验证规范.md`
7. `code/install_git_hooks.py`
8. `LDVH-GOVERNED-PROJECTS.yaml`

## 本阶段承接

阶段 18A 新增 `code/governed_hook_adapter.py`，用于把已有 `git.commit-msg` 安装器包装成受管项目安全入口。

它执行以下顺序：

1. 从 `--governance-root` 读取 `LDVH-GOVERNED-PROJECTS.yaml`；
2. 复用 10 的 target-first / Git common-dir 解析；
3. 确认目标 repo 命中单一受管项目；
4. 对 `install` / `uninstall` 要求显式 `--confirm-human-gate`；
5. 调用 `code/install_git_hooks.py` 的底层安装、状态或回滚能力；
6. 输出 JSON/text receipt，报告 governed project、Hook 状态、diagnostics 和 source_refs。

## 实现变更

| 文件 | 变更 |
|---|---|
| `code/governed_hook_adapter.py` | 新增受管项目 Hook adapter CLI，支持 `status`、`install`、`uninstall` |
| `code/install_git_hooks.py` | 新增 `embed_ldvh_root` 渲染选项，外部 repo Hook 可默认定位到 V3 validator；阶段 21 后 CLI 直接写外部 repo 默认阻断，只作为当前 worktree 安装器和 adapter backend |
| `tests/code/test_ldvh_specs_validate.py` | 增加受管项目安装、回滚、Human Gate 缺失和非受管 repo 阻断测试 |
| `README.md` | 增加外部受管项目 adapter 命令和边界说明 |

## 当前边界

1. 当前 worktree 的 `git.commit-msg` 仍是唯一已经实际 integrated 的自动入口；
2. 外部受管项目 adapter 是可调用能力，不代表任何外部项目已安装 Hook；
3. `status` 只做只读检查，不要求 Human Gate；
4. `install` 和 `uninstall` 必须显式传入 `--confirm-human-gate`；
5. 非受管 target、混合 target、多项目 target 或无法解析的 target 会阻断；
6. 外部受管项目不得直接调用 `code/install_git_hooks.py` CLI 安装或卸载 Hook；
7. 外部 repo Hook 使用嵌入的 LDVH root 找到 V3 validator，但不复制 specs、facts 或 Code 到外部 repo；
8. 本阶段不启用 session start、pre tool use、completion claim 自动触发；
9. 本阶段不恢复 Rules / Skill 顶层机制。

## 使用入口

```bash
python3 code/governed_hook_adapter.py status --repo "<repo>" --governance-root "<ldvh-root>"
python3 code/governed_hook_adapter.py install --repo "<repo>" --governance-root "<ldvh-root>" --confirm-human-gate
python3 code/governed_hook_adapter.py uninstall --repo "<repo>" --governance-root "<ldvh-root>" --confirm-human-gate
```

如需 JSON 输出：

```bash
python3 code/governed_hook_adapter.py status --repo "<repo>" --governance-root "<ldvh-root>" --format json
```

## 结果

阶段 18A 完成后，V3 具备外部受管项目 `git.commit-msg` Hook adapter-ready 能力：可以在 Human Gate 明确授权后，对已登记受管项目执行安装、状态检查和回滚，并验证安装状态。

它不改变当前环境状态结论：除当前 worktree 的 `git.commit-msg` 外，其它自动入口仍未 integrated。
