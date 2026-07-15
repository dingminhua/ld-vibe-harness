# V4 Web Spark 创建接口实施前审核

> 记录性质：本文记录 2026-07-15 对“保持 Web 表现层不变，把现有 Spark POST 与读取接口改接 V4”的实施前只读审核。本文不修改 08、20、31 的规则，不授权 Web 写入，也不证明任何 V4 Web 能力已经实现。
>
> 当前结论：本阶段发现两个 blocker，不能直接把现有 `POST /api/sparks` 接到 V4 创建内核。Web 表现层及现有 V3 写入实现均未在本阶段修改。

## 1. 已确认的 Human 边界

1. Spark 创建 UI 的视觉、布局、文案、字段和交互表现保持不变；
2. Web 创建 Spark 是保留的产品能力，不得通过隐藏、关闭或默认 feature gate 取消；
3. 后续写入目标必须是 V4 `facts/sparks/<object_id>.yaml`，不得继续产生 V3 `ldvh-base/sparks/` 对象；
4. 读取 API 可以改为读取 V4 并投影到既有前端 DTO，但不得借此修改表现层；
5. 其它事实类型的 Web 写入 API 当前不建设。

## 2. 当前实现事实

1. `web/src/components/SparkCreate.tsx` 只提交 `title`、`description`、`priority` 三个字段；
2. `web/api/routes/sparks.ts` 自行分配带 slug 的 V3 ID，直接写入 `ldvh-base/sparks/`，并使用 V3 `pending`、`description`、`source` 等字段；
3. `web/api/services/facts.ts` 的列表和详情读取仍固定扫描 `ldvh-base/`，没有按 02 形成管辖项目与实际 Working Tree 边界；
4. V4 Spark 要求 `object_id` 为 `spark-[0-9]{4,}`、初态为 `open`、正文使用 `summary`，并至少具有一项可重新定位的 `source_refs`；
5. 当前确定性创建实现位于 Helper operation 的私有执行层；08 允许 Web 复用共享 Code，但明确禁止 Web 通过 Helper 服务 Human；
6. 当前创建内核使用 `fcntl`、`O_DIRECTORY`、`dir_fd` 与 hard link 等 Unix 原语，尚不具备原生 Windows 可用性。

## 3. Blocker

### 3.1 Web Human 输入没有稳定来源定位

当前三字段请求没有由既有来源提供的稳定 locator。下列做法均不成立：

- 用新 Spark 自身路径作为形成该 Spark 的来源，造成循环回指；
- 随机生成一个无法再次读取的 Web request ID，冒充可重新定位来源；
- 用 `web`、`conversation` 或 API 路由名代替实际 Human 输入；
- 把对象创建时间、文件名或内容 hash 单独当作原始来源。

在来源承载方式明确前，Code 不能合法生成必填 `source_refs`，POST 不得写入 V4 对象。

### 3.2 Web 请求没有完成 Spark 创建前的语义职责

20 与 31 当前要求创建前完成相邻事实召回，并由 AI 判断跨会话保留价值、对象化必要性、唯一类型、对象粒度及自然语言重复。现有 Web 请求没有 AI 运行时；确定性 Code 可以做机械候选和精确匹配，但不能裁决语义同义或代替 AI 作准入判断。

Human 点击提交能够表达创建意图，但在当前规则下不能自动证明上述语义职责已经完成。未先形成正式承接方案时，不能让路由暗中跳过 20/31，也不能让 Code 以标题或相似度启发式冒充 AI。

## 4. Major 风险

1. Web 不能调用 Helper CLI 规避共享服务设计；需要把确定性创建能力从 Helper operation 中抽成可由 Helper 与 Web 共同调用的 Code 应用服务；
2. V4 读取必须先绑定 02 的唯一管辖项目和实际 Working Tree，不能继续依赖服务器 cwd 或固定根目录；
3. Web 只有基础 API tests，尚无 Spark POST、创建后可见、冲突、并发、回滚和 V4 DTO 投影测试；
4. 当前 Web 没有面向远程多用户写入的认证与授权边界。首版能力只能声明为明确配置的本地、单 Human、单管辖项目模式，不能外推到公开托管写入；
5. Python 创建原语在 Windows 收口前不能支撑三平台 Web 创建声明；
6. 前端仍使用 V3 状态和字段。后端投影至少需要保持 `open → pending`、`routed → resolved`、`discarded → discarded`，以及 `summary → description`、`created_at/updated_at → created/updated`、`object_id/fact_type_key → id/type`；
7. V4 `routed` 可以具有多个承接位置，而既有 `resolved_to` 是单值。投影不得静默选择第一项或丢失其它承接信息。

## 5. 后续最小实施切片

在 blocker 获得正式承接后，按以下独立切片推进，每个切片开始前重新只读审核并单独提交：

1. **来源与语义承接决定**：明确 Web Human 输入的可回读来源载体，以及无 AI quick capture 如何满足或调整 20/31；
2. **共享 Code 应用服务**：从 Helper operation 抽出不依赖 Helper envelope 的管辖、草案、校验、分配、原子创建、回读与回滚服务，Helper 保持现有公开契约；
3. **跨平台创建基础**：替换 Unix 专用锁、目录和 no-overwrite 原语，并在原生 Windows 上取得证据；
4. **V4 Web 读取投影**：按 02 绑定项目/worktree，从 `facts/**` 读取，并投影为现有列表和详情 DTO；前端源文件不改；
5. **Spark POST 接入**：只把现有三字段请求映射到已经获准的 V4 创建输入，成功必须以写后回读为准；
6. **Web 回归与浏览器验证**：验证请求/响应、错误、并发、回滚、创建后可见和表现层基线。

## 6. 表现层冻结与测试边界

当前 `web/src/**`、`web/index.html`、`web/public/**`、`web/dist/**`、前端构建/样式配置、`web/design-workspace/**`、图标和浏览器基线图片均作为冻结对象；后端阶段不得以适配为由修改。重点包括：

- `web/src/components/SparkCreate.tsx`；
- `web/src/i18n/locales.ts` 中 Spark 创建相关文案；
- Spark 创建入口所在页面的布局、按钮、表单字段、提交时序、成功和失败呈现；
- 已有前端消费的 POST 成功/错误 shape 与对象列表、详情 DTO 可观察字段。

后端实施至少需要：

1. 证明上述前端目标文件没有变化，并用浏览器基线核对实际表现；
2. 覆盖非法三字段输入、来源/授权不足、草案过期、冲突、并发、写后回读失败和安全回滚；
3. 证明只写 `facts/sparks/<object_id>.yaml`，不再写 `ldvh-base/`；
4. 证明成功创建的 V4 Spark 能被现有列表和详情界面观察；
5. 在 Linux、macOS 与原生 Windows 的声明支持范围内验证同一契约。

## 7. 待 Human 选择的来源与语义方案

### 方案 A：Web quick capture 专用模式

1. 后端持久化一个可稳定定位的 Web capture envelope，Spark `source_refs` 指向该记录；
2. 当前表单提交明确表示 Human 选择“按 Spark 捕获”并授权创建；
3. Code 完成候选发现、精确来源/标题查重和机械验证；自然语言近似重复留待后续 AI 复核处置；
4. 需要正式定义 capture envelope 的位置、结构、生命周期、原子性、失败残留和读取边界，并修改当前来源/创建规则。

该方案保持当前 UI、三字段请求和即时创建流程，工程边界较小；代价是创建前语义审核弱于 20/31 当前严格链，并新增长期来源资产。

### 方案 B：保持 20/31 当前严格语义

1. 建立稳定 Web 交互事件来源；
2. POST 同步调用实际 AI 语义服务，完成召回、对象化、类型和同义判断；
3. AI 审核通过后再调用共享确定性 Code 创建并回读。

该方案不放宽当前创建标准；代价是新增模型运行、配置、隐私、成本、超时、失败和可用性边界，并可能改变当前提交等待时间。

对象自引用、不可回读 UUID、页面 URL、路由名或只做标题查重都不能作为折中方案。

## 8. 当前停止点

本审核不替 Human 选择方案 A 或 B。该决定会改变事实形成、产品语义或运行成本，不能作为内部实现细节暗定。停止点只影响 Web Spark POST；V4 只读投影、共享 Code 行为保持型拆分、普通安装、Windows 基础、迁移准备和其它不依赖 Web 写入的工作可以继续。
