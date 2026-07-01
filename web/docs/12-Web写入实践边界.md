# Web 写入实践边界

本文是 Web 实现域文档，承接 `specs/08-Web信息同步规范.md` 中不应写入 specs 正文的当前实现状态、API 白名单和测试实践。本文不定义新的 Web 写入授权；若与 specs 冲突，以 specs 为准。

## 当前写入白名单

当前 Web 正式写入能力只有 Spark quick create。

边界：

1. 写入对象只限 Spark；
2. 初始状态固定为 `pending`；
3. 写入位置为 Git 可追踪 Spark 事实实例文件；
4. `source` 固定为 `web`；
5. API response 必须包含 `source_refs`；
6. 写入后必须回读验证；
7. 不得写入 legacy 字段；
8. 不得替代 Git 提交、Human Gate、验证声明或完成声明。

现有测试入口：

```bash
npm run test:web:api
```

其中 `tests/web/api/sparks.test.ts` 覆盖创建、字段校验、文件冲突和写后校验失败。

## 后置写入

以下能力未启用：

1. 通用事实对象写入；
2. WorkCase 状态推进写入；
3. ADR、Pitfall、Study 的 Web 创建或状态改写；
4. 完整 Confirm UI；
5. Confirm UI 自动生成 Human Gate 完成记录。

新增或扩大 Web 写入前，必须回到 `specs/08-Web信息同步规范.md` 的 Human Gate、source_refs、写后校验和事实源边界。
