# 9B 最小提交入口

> 文件状态：temporary migration decision。本文记录阶段 9B 对 Git 提交行动和最小 commit gate 的迁移结果；它不授权安装 Hook、覆盖现有 Git 配置、写入 Web 或迁移真实事实对象实例。正式规则仍以 `specs/` 正文为准。

## 1. 迁移目标

9B 只迁最小提交入口：

1. Git 提交行动继续作为当前唯一正式行动模板示范；
2. commit message 契约由 `03` 和 `03.Att.01` 授权；
3. 验证声明边界由 `09` 和 `09.Att.01` 授权；
4. 提交前 read_plan 消费证据复用 `01.Att.02` 的 `git_commit_msg` 承接；
5. Code 提供只读 commit gate 诊断，不输出授权、不安装 Hook、不替代 Human Gate。

## 2. 已完成

| 交付物 | 作用 | 边界 |
|---|---|---|
| `build_commit_gate` | 解析 commit message，校验 type/scope/body/read_plan 证据 | 只读诊断，不创建提交 |
| `code/specs_validate.py commit-gate` | 暴露 V3 commit gate CLI | 不安装 Hook |
| `code/commit_validate.py` | 给未来 commit-msg Hook 调用的包装器 | 默认只按 blocking/error 退出非零 |
| `tests/code/test_ldvh_specs_validate.py` | 覆盖正例、非法 scope、缺 body、缺 read_plan、CLI 和 wrapper | 不证明真实环境 Hook 已启用 |

## 3. 校验范围

commit gate 当前检查：

1. header 符合 `type(scope): description` 或 `type: description`；
2. `type` 属于 `03.Att.01` Type 闭集；
3. `scope` 属于 `03.Att.01` Scope 允许枚举；
4. 高影响文件、事实对象字段、多文件范围或边界变化触发 body 必填；
5. body 必填时必须包含 `关键变更:` 小标题；
6. 默认要求提供 00/01/02 的 read_plan 消费证据；
7. 输出 `authorization: none`、`environment_integrated: false`、`hook_integrated: false`。

## 4. 未启用项

以下内容没有执行：

1. 不安装 `.git/hooks/commit-msg`；
2. 不修改全局 Git 模板或本机 Hook 配置；
3. 不接入 session_start、pre_tool_use、completion_claim 等通用 Hook；
4. 不让 commit gate 输出成为 Human 授权、风险接受或验收；
5. 不迁移真实 `ldvh-base/` 实例。

真实 Hook 启用会改变用户提交路径，必须进入 Human Gate。当前 9B 只完成 V3 自有校验器和可调用包装器。

## 5. 验证声明

| 验证目标 | 验证方式 | 验证入口 | 关键输出 | 结论 | 残留风险 |
|---|---|---|---|---|---|
| commit gate Code 能力 | 自动化测试 | `python3 -m pytest tests/code/test_ldvh_specs_validate.py -q` | 87 passed | 通过 | 尚未跑全量 suite |
| commit gate CLI | 命令校验 | `python3 code/specs_validate.py commit-gate ... --fail-on-diagnostics` | status ok，diagnostics 0 | 通过 | 仍未安装 Hook |
| Hook wrapper | 命令校验 | `python3 code/commit_validate.py --check-message-file ...` | status ok，diagnostics none | 通过 | 只验证本地 wrapper，不验证真实 Git hook |

## 6. 下一步

9B 的 Code gate 已完成。下一步进入 9C 事实对象完整迁移；若要启用真实 Hook，应先由 Human 明示确认接入范围、失败处理和回滚方式。
