# 20-22 有条件审核收口记录

文件状态：conditional audit closure。本文记录 2026-07-02 只读审核“有条件通过”后的收口处理，不授权新增 Web 写入、外部项目自动安装 Hook、runtime 自动入口或 `_migration` 删除。

## 读取依据

1. `specs/00-理念与构成.md`
2. `specs/01-保障与衔接.md`
3. `specs/02-AI行为规范.md`
4. `specs/04-Specs基础规范.md`
5. `specs/06-行动模板基础规范.md`
6. `specs/08-Web信息同步规范.md`
7. `specs/09-测试与验证规范.md`
8. `specs/01-保障与衔接.md` §6 与 `specs/attachments/01.Att.03-06`
9. `code/install_git_hooks.py`
10. `code/governed_hook_adapter.py`

## 审核结论承接

只读审核结论是“有条件通过，无 P0”。需要优先收口两项：

1. specs 中残留实现域细节；
2. 外部 Hook 安装入口边界。

## 阶段 20：Specs / 实现域边界二次清理

本阶段把 specs 中偏实现域的命令、当前状态和 runner 操作实践迁出到实现域文档。

新增或更新：

| 文件 | 用途 |
|---|---|
| `code/docs/01-Git-Commit-and-Hook-Practice.md` | 承接 Git 提交命令、Hook 状态检查、当前 worktree Hook 和底层安装器实践 |
| `tests/docs/01-Test-Runner-Practice.md` | 承接 smoke/targeted/runtime/full 命令、slow policy、并行边界和 `_migration/tests` 实践 |
| `web/docs/12-Web写入实践边界.md` | 承接当前 Spark quick create 写入白名单、API 测试和后置写入状态 |
| `specs/06-行动模板基础规范.md` | 保留 Git/WorkCase 行动模板规则和 Gate，移出命令长串与具体实例操作细节 |
| `specs/08-Web信息同步规范.md` | 保留 Web 受控写入规则，移出当前 Spark quick create 实现状态 |
| `specs/09-测试与验证规范.md` | 保留分层验证职责，移出具体 runner 命令和 slow policy 操作说明 |
| `specs/01-保障与衔接.md`、`01.Att.03-06` | 保留入口类型和状态声明规则，移出当前 hook path 和安装实践 |

收口后，specs 仍定义需求、规则、契约、边界、Human Gate、Stop Conditions 和验证要求；实践细节由 `code/docs/`、`tests/docs/`、`web/docs/`、README 和可执行代码承接。

## 阶段 21：外部 Hook 安装入口收紧

本阶段把 `install_git_hooks.py` 的 CLI 写入口收紧为当前 LDVH worktree / backend 用途。

处理结果：

1. `code/install_git_hooks.py install/uninstall --repo <外部repo>` 默认阻断；
2. 阻断信息要求外部 repo 使用 `code/governed_hook_adapter.py`，并带受管项目解析和 `--confirm-human-gate`；
3. adapter backend 或测试临时 repo 可以显式使用 `--backend-allow-external`，但该标记不得替代 Human Gate；
4. `governed_hook_adapter.py` 继续负责外部受管项目解析、Human Gate 确认、安装、状态检查和回滚；
5. README 和 `code/docs/01-Git-Commit-and-Hook-Practice.md` 已把底层安装器定位为当前 worktree 安装器 / adapter backend。

## 阶段 22：收口判断

P1-1 处理结果：

1. specs 中的命令长串、当前实现状态和 runner 操作策略已经迁到实现域文档；
2. specs 保留规则口径和可消费结构；
3. formal review hash 已同步 `06/08/09/11`。

P1-2 处理结果：

1. 底层 installer CLI 不能默认写外部 repo；
2. 外部受管项目写入口只保留 governed adapter；
3. 已补直接调用底层 installer 写外部 repo 的负例测试。

仍后置但不阻断：

1. 通用 Web 写入；
2. 完整 Confirm UI；
3. WorkCase Web 状态推进；
4. session/pre-tool/completion 自动触发；
5. dedicated receipt storage；
6. 外部受管项目真实安装 Hook；
7. `_migration` 归档或删除。

## 验证要求

本阶段至少需要：

1. `python3 code/specs_validate.py all --format text --fail-on-diagnostics`
2. `python3 -m pytest tests/code/test_formal_specs.py -q`
3. Hook installer / adapter 相关目标测试
4. `python3 code/test_runner.py targeted --slow skip` 覆盖本次 Code/specs/tests/docs 变更
5. `git diff --check`

## 结果

有条件审核的两个优先条件已完成工程收口。V3 主线状态不变：当前 worktree 的 `git.commit-msg` 是唯一 integrated 自动入口；manual runtime 三件套、通用 Web 写入和外部项目真实 Hook 安装仍后置。
