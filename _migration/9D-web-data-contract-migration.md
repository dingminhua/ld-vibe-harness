# 9D Web 数据契约迁移记录

> 文件状态：temporary migration record。本文记录阶段 9D 的 Web 数据契约迁移结论，不授权通用 Web 写入、Hook 启用、Human Gate 自动完成或 V3 正式主线接管。正式规则仍以 `specs/` 正文为准。

## 1. 迁移目标

阶段 9D 的目标不是重做 Web 表现层，而是让既有 Web 能消费 V3 的事实源边界：

1. Web 页面/API 按 08 从同一 Git 文件事实源独立读取，不把 Code validator 输出、Code DTO 或内部对象作为主数据源；
2. Spark、WorkCase、ADR、Pitfall、Study 的列表和详情能回指 `ldvh-base/` 事实实例；
3. Web API 响应保留 `source_refs`，缓存不得成为长期事实；
4. 只迁入最小 Spark quick create 轻写入，并保持 `pending`、回读验证、来源回指和 legacy 字段禁止；
5. Web 回归测试进入 `tests/web`，覆盖 API contract、commit body display contract、project files 和 Spark 写入边界。

## 2. 已迁入内容

已从 V2 迁入以下 tracked Web 资产：

| 对象 | 处理 |
|---|---|
| `web/` | 迁入既有 Web 客户端、API、服务和工具代码；不迁入 `dist/` 或 `node_modules/` 生成物 |
| `tests/web/` | 迁入 Web API、Spark quick create、commit display contract 和 project files 回归测试 |
| `package.json` | 迁入 workspace 脚本，并把 `specs:check` / `facts:check` 改为 V3 `code/specs_validate.py all --fail-on-diagnostics` |
| `web/api/services/facts.ts` | 保留 Web-native Git 文件读取，支持 YAML 事实对象和 Study Markdown frontmatter；新增列表/详情 `source_refs` |
| `web/api/routes/sparks.ts` | 对齐 V3 Spark schema，写入 `pending` Spark 时回读验证，禁止 legacy `status_history` 和 `规范10` |
| `web/api/services/projectFiles.ts` | 支持 V3 根目录 `LDVH-GOVERNED-PROJECTS.yaml`，相对路径按配置文件所在目录解析 |
| `web/api/app.ts` | 为 `/api` 响应加 `Cache-Control: no-store`，避免 API 响应被误作事实源缓存 |

## 3. Web / Code 分离结论

Web 与 Code 仍是同源并列实现：

1. Web facts API 自行读取 `ldvh-base/` 下的 YAML 和 Study Markdown frontmatter；
2. `web/api/services/pytools.ts` 不再保留旧 `fact_cli.py` 调用包装器，避免 Web 主数据路径依赖旧 Code CLI；
3. Code validator 继续负责 specs、commit gate、fact instances 和 e2e 的确定性校验；
4. Web 可以在测试、审计或诊断展示中引用 Code 的 diagnostics、verification summary 或 source refs，但这些输出不得驱动页面字段契约、状态机、排序筛选或事实判断。

## 4. 轻写入边界

本阶段只迁入 Spark quick create：

1. 只能创建 `type=spark`、`status=pending` 的事实实例；
2. 必填字段按 V3 Spark schema 写入，包括 `evolution`、`related_workcases`、`related_adrs`、`related_studies`、`related_docs`；
3. 写入后必须回读并校验 persisted data；
4. API 响应必须包含事实文件 `source_refs`；
5. 不写入 `status_history`、`规范10` 等 legacy 字段；
6. 该轻写入不替代 Git 提交、Human Gate、完成声明或正式关闭。

其它 Web 写入、Confirm UI 完整闭环、页面视觉回归和真实 Human Gate 展示验证继续后置。

## 5. 验证记录

已运行并通过：

```text
npm --prefix web run test:web:api
npm --prefix web run check
npm --prefix web run build
python3 code/specs_validate.py all --format text --fail-on-diagnostics
python3 code/specs_validate.py e2e --target-path tests/code/test_ldvh_specs_validate.py --format text --fail-on-diagnostics
python3 code/specs_validate.py commit-gate --format text --fail-on-diagnostics --message <planned commit message> --acknowledged-path specs/00-理念与构成.md --acknowledged-path specs/01-保障与衔接.md --acknowledged-path specs/02-AI行为规范.md --acknowledged-path _migration/9-v3-mainline-transition-scope.md --acknowledged-path _migration/v3-migration-execution-plan.md --acknowledged-path _migration/9D-web-data-contract-migration.md
python3 -m pytest tests/code _migration/tests -q
```

最终结果：

1. Web API contract tests 通过；
2. Web TypeScript check 通过；
3. Web production build 通过，Vite 仅提示 chunk size warning；
4. specs validator `all` 输出 diagnostics 0；
5. e2e rehearsal 输出 diagnostics 0、blocking 0、`environment_integrated=false`、`Authorization: none`；
6. commit gate 对计划提交消息通过，`read_plan_consumed=true`、diagnostics 0；
7. `tests/code _migration/tests` 输出 `122 passed`。

## 6. 后置边界

以下内容不在 9D 内完成：

1. 不重做 Web 信息架构、视觉表现或页面交互设计；
2. 不把 Web 变成 Code 输出消费者；
3. 不接入通用 Web 写入或完整 Confirm UI；
4. 不安装 Hook，不启用阻断型 commit-msg gate；
5. 不恢复 V2 知识地图页面、投影 schema 或事实层；
6. 不声明 V3 正式主线接管。
