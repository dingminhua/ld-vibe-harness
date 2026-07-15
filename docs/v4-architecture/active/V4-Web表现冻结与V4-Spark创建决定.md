# V4 Web 表现冻结与 V4 Spark 创建决定

> 记录性质：本文记录 Human 对当前 Web 表现层和 Spark 创建能力的明确决定、实施前置与验证边界。它不是规则源；规则语义只回到 08/20/31，也不因未挂载 Code 成立而证明生产 Web API 或 V4 Spark 创建已经实现。
> 决定日期：2026-07-15
> 当前状态：`web-direct-capture` 规则契约、共享创建事务与未挂载 Python service 已形成；TypeScript bridge/DTO、生产 POST+读取原子接管与 V3 writer 删除尚未实施

## 1. Human 决定

1. 当前 Web 的表现层不得修改，包括 Spark 创建 UI 的视觉、布局、文案、表单字段和交互表现；
2. 不关闭、不隐藏 Spark 创建 UI，也不取消 `POST /api/sparks`；Web 创建 Spark 是明确保留的产品设计意图；
3. `POST /api/sparks` 必须停止自行分配 V3 slug ID、拼装 V3 字段并直接写入 `ldvh-base/sparks`，后续改为依据当前 V4 Spark 来源和受控 Code 能力创建、回读 V4 Spark；
4. 为保持创建后现有列表、详情和成功反馈行为，可以修改后端读取接口、内部 DTO 和 V4→现有前端 DTO 投影，但不得借此改变表现层；
5. 除 Spark 创建外，其它事实类型的 Web 写入 API 当前不需要，不进入建设范围。

该决定取代此前“同时关闭或默认 feature-gate Spark 创建 UI 与 POST API”的计划。旧计划不得继续作为当前路线或安全 Gate。

## 2. 当前实现冲突

现有前端只提交 `{title, description, priority}`。现有后端把它转换为 V3 `id/type/status/created/updated/description/source/related_*`，写入带 slug 的 `ldvh-base/sparks/<id>-<slug>.yaml`。V4 要求 `facts/sparks/<object_id>.yaml`、`object_id/fact_type_key/created_at/updated_at/status/source_refs/summary/priority`，并要求合法 `open` 初态、创建前召回查重、来源定位、受控身份分配、机械校验、原子 no-overwrite 和写后回读。

因此保持 UI 不变不等于可以只替换几个字段名。当前规则与未挂载 Code 已承接稳定 source ref、精确查重和不经 Helper CLI 的共享创建事务，生产适配仍必须承接：

1. 以未挂载 TypeScript transport 连接 Python service，不通过 Helper CLI，且不在该切片挂生产路由；
2. 按 02/08 解析 loopback 本机单用户、唯一 governed project、实际 worktree 和 common-dir，不得把服务器 cwd 或 fallback workspace 当成管辖边界；
3. 建立 V4 Spark read/list/detail reader 与 V4→现有前端 DTO projector，包括不丢失多承接位置的可观察映射；
4. 在同一生产增量原子切换 Spark POST 与 list/detail 读取，并永久删除 V3 writer；不允许只切 POST 而使新对象对页面不可见；
5. 只有 V4 原子创建和精确回读实际成功后才能返回 2xx；拒绝、不可用、失败、回读或回滚异常必须映射为非 2xx，并保持前端当前可展示的 `error`/`errors` 契约。

08/20/31 现已形成唯一 `web-direct-capture` carve-out：每次 Human 点击只授权一个 `open` Spark；自包含 data URI 恢复 canonical payload，SHA-256 进入 source version；全状态精确重复统一非 2xx；不同 identity 的语义比较在后续 AI F2/F3 opportunity 中进行。提交 `1d39a4c4` 与 `4fd2935b` 已将该契约落为共享 application transaction 和未挂载 Python service；该实现不改变普通 AI 创建或 Helper 契约。

## 3. 已冻结的规则契约

1. 请求字段继续只有 `{title, description, priority}`；description 只在 canonical payload 中映射为 summary；Unicode 15.1 NFC、枚举 White_Space trim、确定性 JSON escaping、RFC 4648 standard Base64、SHA-256 version 与固定向量均由 08 唯一定义；
2. source ref 为 `kind: web-direct-capture`，locator 自包含 canonical JSON，version 为 digest，observed_at 为服务器观察时点；bare digest、`human-input` 或 `web` 不成立；
3. 同一唯一项目/实际 worktree 中扫描全部 current Spark 状态；唯一精确匹配统一返回 409 `exact_duplicate` 和 existing 稳定引用/状态，多匹配、损坏或 coverage 不完整 fail closed；
4. direct capture 不更新、重开、替代、关联、commit 或回退 V3；语义相似但 identity 不同不由 Code 拒绝，后续只产生 AI F2/F3 reconciliation opportunity；
5. 只允许 loopback 本机单用户和唯一 governed project/worktree/common-dir；远程、Vercel、fallback workspace、零/多项目与多 worktree 均零写入拒绝；
6. 冻结 UI 的窄例外只说明现有三字段已经呈现本次对象内容和预期新增；现有错误区域仍须显示实际分类和残留路径。不能据此声明 Web 整体符合 08。

## 4. 后续实施边界

后续每个增量必须保持 `web/src/` 中受影响表现层文件零行为变化。下一增量只允许建立未挂载 TypeScript bridge/transport、V4 read/list/detail reader、DTO projector 与对应 tests；不得挂载或改写生产路由。随后的原子接管增量才可修改：

- Web API 的 Spark 创建路由、V4 读取服务与内部 DTO 投影；
- 不改变领域定义的内部 transport、loopback/唯一管辖边界和 HTTP 结果映射；
- Web API tests、Code contract tests、跨平台 tests 和实现说明；
- 唯一工作推进控制面与当次验证证据。

不允许顺带新增 ADR、WorkCase、Pitfall、Study 或其它写入 API，也不允许修改前端视觉、布局、导航、文案、表单字段、成功时序或交互流程。

## 5. 验证状态与最低验证

当前已取得：共享创建事务保持 Helper 行为；闭集三字段、source ref、全状态精确查重、Schema/关系稳定化、预算、并发、allocator CAS、原子 no-overwrite、精确回读、条件回滚与残留披露均有 Code tests；linked worktree 共享 counter 但保持已选定 worktree 的重复范围；`web/src/**`、`web/api/**` 和路由在该增量中零变化。当次 macOS/Python 3.12 全量回归为 741 passed / 10 native-only skipped，wheel 可直接导入新 service；该证据不是 Web 集成或原生 Windows 结论。

待取得的最低验证仍包括：

1. 前端源文件无目标变化，并回归现有浏览器表现基线；
2. POST 继续接受当前三个字段，保持前端实际使用的成功和错误响应边界；
3. 生产原子切换后，隔离受管辖临时 Git worktree 只创建 `facts/sparks/<object_id>.yaml`，不再写 `ldvh-base`，对象不含 V3 字段；
4. 创建后列表和详情立即能通过 V4 读取与 DTO 投影观察同一对象，且错误/残留路径在现有表现中可观察；
5. Linux、原生 Windows 和 macOS 的相应 Code/API 契约最终通过；在真实 Windows 证据形成前只声明仓库侧候选兼容。

## 6. 完成边界

当前完成的是规则契约、共享创建事务和未挂载 Python direct-capture service，不得声明 Web Spark 创建已经实现或 available。只有表现层保持不变、POST 不再写 V3、V3 writer 已删除、V4 对象受控创建并回读、列表/详情读取同一 V4 来源、失败边界可观察且范围匹配测试通过时，才能声明 Web Spark 创建完成。其它 Web 写入能力继续明确为未建设。
