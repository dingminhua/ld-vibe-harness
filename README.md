# LDVH V3

当前仓库处于 V3 soft mainline 状态：日常规则判断、事实对象维护和 Web 数据读取以 V3 为准；Hook、Rules、runtime adapter 和阻断型环境入口尚未强制接管。

## 当前主线

- `specs/`：规则源。Markdown specs 是正式规则权威，不是事实源。
- `ldvh-base/`：事实对象实例。当前承接 Spark、WorkCase、ADR、Pitfall、Study。
- `code/`：确定性解析、校验、诊断、commit gate 和 e2e rehearsal。
- `web/`：Human-facing 展示和 Web API。Web 独立读取 V3 `ldvh-base/`，不依赖 Code 输出作为主数据源。
- `tests/`：正式回归检查。
- `_migration/`：历史迁移证据、formal review hash gate 和迁移测试材料；不作为日常规则源或事实维护入口。
- `rules/`、`hooks/`、`skills/`：仍未正式启用。Skill 不作为 V3 顶层机制。

## 环境边界

```yaml
switch_mode: soft_mainline
environment_integrated: false
hook_integrated: false
authorization: none
```

这意味着 V3 已是日常主线，但系统不会自动拦截所有 session start、pre tool use、completion claim 或真实 Git 操作。需要时应手动运行对应 Code 命令；Code、Web、测试或 commit gate 输出都不替代 Human Gate。

## 常用验证

优先使用分层测试入口。日常小改用 smoke 或 targeted，阶段收口、跨域迁移和高风险回归再跑 full：

```bash
python3 code/test_runner.py smoke
python3 code/test_runner.py targeted --changed specs/09-测试与验证规范.md
python3 code/test_runner.py full
```

等价 npm scripts：

```bash
npm run test:smoke
npm run test:targeted -- --changed web/api/app.ts
npm run test:full
```

底层验证命令仍可直接运行：

```bash
python3 code/specs_validate.py all --format text --fail-on-diagnostics
python3 code/specs_validate.py e2e --target-path tests/code/test_ldvh_specs_validate.py --format text --fail-on-diagnostics
python3 code/specs_validate.py commit-gate --format text --fail-on-diagnostics --message "<message>"
npm --prefix web run test:web:api
npm --prefix web run check
```

慢速全量测试适用于阶段收口、主线切换、跨域迁移或高风险回归：

```bash
python3 code/test_runner.py full
```

## 当前正式 specs 编号

- `00`：理念与构成
- `01`：保障与衔接
- `02`：AI 行为规范
- `03`：事实源与 Git 溯源规范
- `04`：Specs 基础规范
- `05`：事实模型基础规范
- `06`：行动模板基础规范
- `07`：Code 确定性执行规范
- `08`：Web 信息同步规范
- `09`：测试与验证规范
- `10`：受管项目接入规范
- `20`：Spark-火花
- `21`：WorkCase-工作项
- `22`：ADR-决策
- `23`：Pitfall-踩坑经验
- `24`：Study-研究报告
