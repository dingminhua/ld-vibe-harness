# 9F 主线切换收口记录

> 文件状态：temporary migration closure。本文记录阶段 9F 的 V3 soft mainline switch 结论，不授权 Hook 安装、阻断型环境入口、通用 Web 写入、Human Gate 自动完成或 hard switch。正式规则仍以 `specs/` 正文为准。

## 1. 收口结论

阶段 9F 将 V3 切到日常规则和事实维护主线，但这是 soft switch，不是环境强制接管。

soft switch 生效后：

1. 日常规则判断以 V3 `specs/` 为准；
2. Spark、WorkCase、ADR、Pitfall、Study 事实对象以 V3 `ldvh-base/`、成员规范和 Code schema 为准；
3. Web 保留既有表现层，按 V3 数据契约和 `source_refs` 读取事实对象；
4. Git 提交行动使用 V3 commit message 契约、read_plan 消费证据和验证声明边界；
5. Action Guide / 行动指南承接 V2 知识地图导航能力，旧知识地图不再作为正式概念；
6. `_migration` 只保留为历史审计、formal review hash gate 和迁移测试证据，不作为日常规则源或事实维护入口。

soft switch 不代表：

1. session start、pre tool use、completion claim 或其它环境事件已经自动拦截；
2. Hook、Rules、runtime adapter 或通用环境入口已经启用；
3. WorkCase 创建、方案审核、结果复核、关闭确认模板已经正式可执行；
4. Web 通用写入、完整 Confirm UI 或 Human Gate 自动记录已经启用；
5. Code、Web、测试或 commit gate 输出可以替代 Human Gate、事实源或完成声明。

当前环境边界仍是：

```yaml
switch_mode: soft_mainline
environment_integrated: false
hook_integrated: false
authorization: none
```

## 2. 日常使用入口

| 使用场景 | V3 主线入口 | 边界 |
|---|---|---|
| 查规则 | `specs/` | V2 只作为历史来源，不作为日常规则入口 |
| 查事实对象 | `ldvh-base/` | Code/Web 可读取和诊断，但不得替代事实源 |
| 查项目归属 | `LDVH-GOVERNED-PROJECTS.yaml` + `python3 code/specs_validate.py governed-projects ...` | 静态解析不等于 Hook 已拦截 |
| 规则/事实校验 | `python3 code/specs_validate.py all --format text --fail-on-diagnostics` | 输出是诊断，不是授权 |
| 静态闭环演练 | `python3 code/specs_validate.py e2e --target-path <path> --format text --fail-on-diagnostics` | `environment_integrated=false` 仍是预期 |
| 提交前检查 | `python3 code/specs_validate.py commit-gate ... --fail-on-diagnostics` 或 `python3 code/commit_validate.py ...` | 可手动运行；不声称所有提交路径都被自动拦截 |
| Web 验证 | `npm --prefix web run test:web:api`、`npm --prefix web run check`、`npm --prefix web run build` | Web API 轻写入仅限 Spark quick create |

## 3. `_migration` 保留与归档条件

9F 不删除 tracked `_migration` 内容。原因是：

1. formal review hash gate 仍读取 `_migration/reviews/*`；
2. `_migration/tests` 仍覆盖迁移 gate、fixture 和 V2 吸收回归；
3. 9A-9F 记录仍是主线切换审计线索；
4. 删除这些材料会降低追溯能力，且不减少当前 AI 日常判断负担。

后续满足以下条件后，才可再次判断归档或删除：

1. formal review hash gate 已迁出 `_migration` 或有稳定替代；
2. `_migration/tests` 的仍有效用例已迁入正式 `tests/` 或明确废弃；
3. 9A-9F 结论已被正式 docs、specs、tests 或 release notes 承接；
4. 用户明确接受删除历史迁移证据的残留风险。

## 4. Hard Switch 后置条件

hard switch 必须另起环境接入工作，至少满足：

1. Hook / Rules / adapter 的触发事件、payload、target 解析和失败处理已定义；
2. commit-msg、session_start、pre_tool_use、completion_claim 等入口的启用范围和回滚方式已确认；
3. Code 输出继续保持 `authorization=none`，Human Gate 路径独立存在；
4. 有安装、卸载、失败、unknown event、payload 缺失和 no-op 的测试；
5. 用户明示同意启用会改变真实工作流的阻断型入口。

## 5. 最终验证

9F 属于阶段收口和主线切换声明，已运行慢速全量验证：

```text
python3 code/specs_validate.py all --format text --fail-on-diagnostics
python3 code/specs_validate.py e2e --target-path tests/code/test_ldvh_specs_validate.py --format text --fail-on-diagnostics
python3 -m pytest tests/code _migration/tests -q
npm --prefix web run test:web:api
npm --prefix web run check
npm --prefix web run build
python3 code/specs_validate.py commit-gate --format text --fail-on-diagnostics --message <planned commit message> ...
```

最终结果：

1. `specs_validate.py all` 输出 diagnostics 0；
2. `specs_validate.py e2e` 输出 diagnostics 0、blocking 0、`environment_integrated=false`、`Authorization: none`；
3. `python3 -m pytest tests/code _migration/tests -q` 输出 `122 passed`；
4. `npm --prefix web run test:web:api` 通过；
5. `npm --prefix web run check` 通过；
6. `npm --prefix web run build` 通过，Vite 仅提示 chunk size warning；
7. commit gate 对计划提交消息通过，`read_plan_consumed=true`、diagnostics 0、`Authorization: none`。
