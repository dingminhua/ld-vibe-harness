# V4 Web 表现冻结与 V4 Spark 创建决定

> 记录性质：本文记录 Human 对当前 Web 表现层和 Spark 创建能力的明确决定、实施前置与验证边界。它不是规则源，不自行修改 08/20/31，不证明 Web API、共享 Code 能力或 V4 Spark 创建已经实现。
> 决定日期：2026-07-15
> 当前状态：只记录，暂不实施

## 1. Human 决定

1. 当前 Web 的表现层不得修改，包括 Spark 创建 UI 的视觉、布局、文案、表单字段和交互表现；
2. 不关闭、不隐藏 Spark 创建 UI，也不取消 `POST /api/sparks`；Web 创建 Spark 是明确保留的产品设计意图；
3. `POST /api/sparks` 必须停止自行分配 V3 slug ID、拼装 V3 字段并直接写入 `ldvh-base/sparks`，后续改为依据当前 V4 Spark 来源和受控 Code 能力创建、回读 V4 Spark；
4. 为保持创建后现有列表、详情和成功反馈行为，可以修改后端读取接口、内部 DTO 和 V4→现有前端 DTO 投影，但不得借此改变表现层；
5. 除 Spark 创建外，其它事实类型的 Web 写入 API 当前不需要，不进入建设范围。

该决定取代此前“同时关闭或默认 feature-gate Spark 创建 UI 与 POST API”的计划。旧计划不得继续作为当前路线或安全 Gate。

## 2. 当前实现冲突

现有前端只提交 `{title, description, priority}`。现有后端把它转换为 V3 `id/type/status/created/updated/description/source/related_*`，写入带 slug 的 `ldvh-base/sparks/<id>-<slug>.yaml`。V4 要求 `facts/sparks/<object_id>.yaml`、`object_id/fact_type_key/created_at/updated_at/status/source_refs/summary/priority`，并要求合法 `open` 初态、创建前召回查重、来源定位、受控身份分配、机械校验、原子 no-overwrite 和写后回读。

因此保持 UI 不变不等于可以只替换几个字段名。实施前必须解决：

1. Web quick capture 的 Human 输入如何形成可重新定位且不伪造的 `source_refs`；
2. `{title, description, priority}` 如何在不改变表单的情况下形成合法 `title/summary/priority`，以及 20/31 要求的对象化、类型判断和创建前查重由谁承担；
3. 08 明确 Web 独立服务 Human、不经过 Helper CLI，现有 Helper adapter 不能直接成为 Web shell-out；需要让受控创建的确定性内核成为 Web 可调用的共享 Code 能力，同时保持 Helper 与 Web 各自入口边界；
4. V4 新对象写入后，现有对象列表和详情 API 必须改读 `facts/sparks`，并投影为前端当前 DTO，否则创建成功后页面不可见；
5. 只有 V4 原子创建和精确回读实际成功后才能返回 2xx；拒绝、不可用、失败、回读或回滚异常必须返回非 2xx，并保持前端当前可展示的 `error`/`errors` 契约。

若当前 20/31 无法在不引入 AI 语义判断的 Web quick capture 中合法承接上述行为，应先形成规则差距与方案比较，不能由路由私设“Web 特例”。

## 3. 后续实施边界

该增量实施时必须保持 `web/src/` 中受影响表现层文件零行为变化。允许修改范围原则上包括：

- Web API 的 Spark 创建路由、V4 读取服务与内部 DTO 投影；
- 可被 Helper 和 Web 分别调用、但不取得领域定义权的共享 Python Code 边界；
- 解决 Web Human 输入稳定来源、授权和查重所必需的当前来源或实现规划；
- Web API tests、Code contract tests、跨平台 tests 和实现说明；
- 唯一工作推进控制面与当次验证证据。

不允许顺带新增 ADR、WorkCase、Pitfall、Study 或其它写入 API，也不允许修改前端视觉、布局、导航、文案、表单字段、成功时序或交互流程。

## 4. 最低验证

1. 前端源文件无目标变化，并回归现有浏览器表现基线；
2. POST 继续接受当前三个字段，保持前端实际使用的成功和错误响应边界；
3. 在隔离受管辖临时 Git worktree 中只创建 `facts/sparks/<object_id>.yaml`，不写 `ldvh-base`，对象不含 V3 字段；
4. 覆盖来源、授权、查重、Schema、并发身份、原子 no-overwrite、写后回读和失败/回滚残留；
5. 创建后列表和详情立即能通过 V4 读取与 DTO 投影观察同一对象；
6. Linux、原生 Windows 和 macOS 的相应 Code/API 契约最终通过；在真实 Windows 证据形成前只声明仓库侧候选兼容。

## 5. 完成边界

本决定现在只落盘，不开始 Web 实施。只有表现层保持不变、POST 不再写 V3、V4 对象受控创建并回读、列表/详情读取同一 V4 来源、失败边界可观察且范围匹配测试通过时，才能声明 Web Spark 创建完成。其它 Web 写入能力继续明确为未建设。
