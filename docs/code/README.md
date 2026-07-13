# V4 Code 实现规划

> 当前规划入口：本文是当前唯一的 Code 实现规划及稳定入口。本文不是规则源，也不是完整的 V4 进展总览；当前状态与跨构成要素边界见 [`V4-当前进展.md`](../v4-architecture/V4-当前进展.md)。实现语义必须回到当前有效规范和授权附件。

## 当前开发执行策略：多模型并行与主任务复核

本节记录 Human 当前确认的开发执行偏好，不是正式 Specs，不定义 LDVH 架构概念，也不使用“Agent”作为构成要素或产品术语。后续 LDVH 开发在任务能够安全拆分时采用以下方式，Human 另行调整或工具能力不支持时据实报告：

1. 主任务使用 `gpt-5.6-sol` 和 `xhigh` 推理强度，承担 00 对齐、Specs 前置判断、任务拆分、共享接口收敛、集成、完整验证与最终结论；不使用 `pro` 推理档位。
2. 边界清晰的独立实现优先交给其它模型的独立 Codex 任务：一般实现与聚焦测试默认使用 `gpt-5.6-terra` + `xhigh`；低风险、机械性强且验收条件确定的实现或检查可以使用 `gpt-5.6-luna` + `xhigh`。模型不可用或当次工具不能指定模型时，不冒充已经按该分工执行，并由主任务说明实际安排。
3. 需要不同模型时使用独立 Codex 任务和独立 Git worktree/分支；普通内部并行如果不能选择模型，只用于不要求模型分工的只读调查、独立复核或边界明确的子任务。
4. 并行开始前必须先在适用 Specs 中固定服务语义、范围和结果边界，并在本规划中明确模块责任、接口、文件所有权、测试风险和集成顺序。实现任务不得自行补造或改变 Specs。
5. 并行任务不得修改同一生产文件或共同编排位置。共享接口、公共 Schema、服务注册、冲突处理和跨模块集成由主任务单线完成；无法形成互斥所有权时不并行编码。
6. 每个并行结果必须提供提交、聚焦测试、已知缺口和来源回指。主任务逐项检查 diff 与契约，按明确顺序集成，再运行受影响测试、完整回归、静态检查和必要的真实环境验证；分支模型的完成声明不能替代主任务复核。
7. 多模型并行只用于缩短等待时间，不降低 00、当前有效 Specs、Human Gate、Stop Conditions、术语审计和未覆盖范围如实声明的要求。架构不确定、来源冲突或需要 Human 选择时，受影响范围返回主任务处理，不由并行任务自行决定。

是否采用并行由任务结构决定：可独立验证且文件所有权互斥时并行；强顺序依赖、共同接口尚未收敛或会并发修改核心文件时保持单线。该策略约束开发过程，不反向成为 Helper 服务、规范模型、事实模型、行动模板、Code 或 Web 的产品定义。

## 已完成增量：管辖范围解析公开操作

| 项目 | 当前决定 |
|---|---|
| 实现起点 | Specs 固定提交 `25ec579d`；Code 模块边界提交 `c16d1ab7` |
| 目标 | 实现 `resolve-governance-scope`，从当前配置、路径和 Git 观察形成逐对象管辖判定及聚合结果，并完整兼容同一项目的 main/linked worktree |
| 不覆盖 | 规则适用判断、对象专属规范或事实读取、配置写入、worktree 创建或切换、环境 Hook/adapter、远端仓库身份和状态变更 |
| 直接来源 | `work-object-governance-scope` §§5–11、`governed-projects-config-fields`、`helper-cli-service-contract` §§5–7、`helper-cli-request-response-fields`、`source-of-truth-traceability`、`code-engineering-practices` |

本增量不读取目标 worktree 的 Specs 来决定自身公开身份。Helper 仍先从与实际 Code 共置的当前规则源发现操作，再由领域实现只读取请求涉及的配置、路径和 Git 信息；管辖结果形成后，其它操作是否读取目标 worktree 内容由各自来源契约决定。

### 模块责任与依赖

| 模块 | 唯一维护责任 | 不承担 |
|---|---|---|
| `ldvh.governance.configuration` | 配置候选发现、真实路径去重、YAML 当前内容、字段闭集和结构校验 | 不运行 Git，不判断对象归属 |
| `ldvh.governance.git` | 路径定位、真实 worktree 根、common-dir 和 Git 技术失败 | 不读取配置，不选择管辖项目 |
| `ldvh.governance.models` | 02 领域状态、逐对象结果、确定性聚合和 JSON 序列化 | 不访问文件系统，不选择 Helper outcome |
| `ldvh.governance.resolver` | 组合配置、Git 身份和匹配规则，保留每个 locator 的结果、来源和缺口 | 不构造共同响应，不读取项目内容 |
| `ldvh.helper.operations.governance_scope_request` | 按 02 §10.1 校验领域输入并把实际进程 `cwd` 作为显式执行上下文 | 不发现配置，不调用 Git |
| `ldvh.helper.operations.governance_scope_operation` | 把 resolver 结果映射为可用性和 `OperationExecution` | 不复制共同响应 Schema或重新实现领域判断 |
| `ldvh.helper.service` | 在服务边界捕获一次实际 `cwd` 并注入操作运行时 | 不从请求中的 `task` 或 `observed_context` 猜测目录 |

允许依赖方向为：

```text
governance.models <──────── governance.configuration
        ^
        └────────────────── governance.resolver <── governance.git

helper governance request -> helper governance operation -> governance.resolver
helper governance operation -> operation_runtime
service -> operation_runtime
```

`models` 是领域状态与结果结构的唯一 Code 表示；配置模块只复用其中的 `ConfigStatus`，Git 模块保持独立，resolver 是唯一组合位置。共同请求和响应仍分别由 `ldvh.helper.requests` 与 `ldvh.helper.responses` 维护。附件中的字段语义不在 tests 或 handler 中复制成第二来源；内部类型只承接当前契约。

### 冻结接口与错误边界

配置模块接收显式 `workspace_root`，或由 resolver 提供的对象路径搜索起点、common-dir 父目录搜索起点和需排除的 Git worktree 根；它按真实配置路径去重并区分 `valid/missing/invalid/conflict`。Git 模块返回成功身份、确定性非 worktree 或技术失败，不能把 Git 可执行文件缺失、权限、I/O 和进程失败伪装成非管辖。models 只聚合已经完成的逐对象结果；`partial` 的未完成范围由 Helper scope 保留，不用聚合状态覆盖。

首个实现只接受路径 string locator；相对路径以实际进程 `cwd` 为基准。领域结果携带 `locator_index`、原始 locator、实际 `git_worktree_root`、`git_common_dir` 和配置登记路径。登记路径只用于配置校验和直接路径命中；任何后续内容读取不得由它替代实际目标 worktree。

### 并行实施与集成顺序

第一阶段三个独立 worktree 分别拥有 `configuration.py`、`git.py`、`models.py` 及其聚焦 tests，禁止修改 Specs、Web 或彼此生产文件。主线程按 models → Git → configuration 集成并核对接口，再单线实现 resolver、领域请求和 Helper handler；涉及共同 service/operation runtime 的变化只在主线程完成，避免多个分支并发改动公共编排。

### 风险与测试映射

| 风险 | 主要证据 |
|---|---|
| 上层 `cwd` 猜中子项目或覆盖显式 locator | 真实进程测试覆盖上层目录、空 locator、显式 V4 locator和相对路径 |
| 临时 worktree 找不到外部配置 | 真实 linked worktree 测试覆盖从 common-dir 父目录发现配置，并跳过 Git worktree 根内同名文件 |
| V3/V4 或临时 worktree 内容串读 | 配置入口与目标 worktree 放置不同哨兵内容，断言只返回和使用实际目标 root |
| remote、分支或目录名被误作身份 | 独立 clone 同 remote、branch switch、detached HEAD 反例 |
| submodule 被父路径穿透 | 未登记与独立登记 submodule 场景 |
| 配置或 Git 技术失败被包装成确定结论 | missing/invalid/conflict 与 permission/process/dependency failure 分层测试 |
| 重复 locator、相同配置多路线发现或多对象聚合丢失 | locator_index、真实路径去重、single/multiple/mixed/unknown contract tests |
| 新操作声明被旧测试或 Code 白名单阻断 | 操作发现测试同时验证“来源已定义、实现未接入”和集成后的来源绑定实现 |

完成条件：配置、Git、模型、resolver、领域请求和 Helper handler 的局部与契约 tests 通过；main/linked worktree、外部配置发现、上层 `cwd`、独立 clone、submodule、配置无效和技术失败均有范围匹配证据；真实 `ldvh capabilities/call` 只从当前来源发现并调用实现；完整 pytest、Ruff、格式、diff-check 和独立复核通过。未实现的对象专属规则/事实读取、环境接入和跨平台真实环境继续明确标记未验证。

### 当前 Working Tree 实现结果

本增量已完成配置发现与校验、Git worktree 身份观察、领域结果模型、逐对象解析、请求解析和 Helper 公开操作接入。实现以登记路径确认项目身份，以实际目标 `git_worktree_root` 保持内容操作边界，并通过实时派生的 `git_common_dir` 将同一 Git 仓库的 main/linked worktree 解析为同一管辖项目；分支、HEAD、remote 和目录名均不作为项目身份。

领域未知与技术未完成已经分开：配置 `missing/invalid/conflict` 只为观察已完成的对象形成 `scope_unknown`，Git 依赖、权限、I/O、进程或超时失败进入 `not_completed`，不会被包装成确定性非管辖结论。Git 子进程设有 10 秒超时，内部诊断不直接泄漏到公开结果。

当次验证结果为 279 项 Code tests 全部通过，Ruff、格式和 diff-check 通过，独立复核没有 Blocker 或 Major。真实 CLI 已验证当前 V4 worktree、位于工作区外的 linked worktree，以及从上层目录无 locator 调用三类场景：前两者均通过外部管辖配置解析为同一 `ldvh` 项目并保留各自实际 worktree 根；第三类只判断实际 `cwd`，不会猜测其下的 V4 项目。

本增量没有实现对象专属 Specs/事实读取、规则适用判断、配置写入、worktree 生命周期管理或环境接入；这些范围仍不得声明为可用或已完成。

---

## 已完成增量：规范候选读取公开操作

| 项目 | 当前决定 |
|---|---|
| 实现起点 | Git commit `69d7f7467520ca3d94e9b33c87fe5acf893f1383` |
| 目标 | 让 `read-specification-candidates` 从已定义但未实现，推进为能够按 01 契约实际读取 Working Tree 中 L0–L2 信息的 Helper 公开操作 |
| 不覆盖 | L3/L4、任务相关性判断、管辖范围解析、规则适用判断、状态变更、普通 wheel 规则源部署和其它领域公开操作 |
| 直接来源 | `specification-model-foundation` §§6、9.2–9.5，`helper-cli-service-contract` §§5–7，`helper-cli-request-response-fields`，`source-of-truth-traceability`，`code-engineering-practices` |

本增量采用三个独立 Git worktree 并行实施。并行只缩短实现等待时间，不允许各分支修改 Specs、Web、公共规划或彼此拥有的生产文件；发现来源契约歧义时返回主线程处理，不在实现分支自行补造规则。

### 并行文件所有权

| 并行线 | 生产文件所有权 | 测试文件所有权 | 不承担 |
|---|---|---|---|
| A：领域请求 | 新建 `ldvh.helper.operations.specification_candidate_request` | 新建同名聚焦测试 | 不读取仓库、不生成 L0–L2、不修改服务分流 |
| B：候选读取 | 新建 `ldvh.helper.operations.specification_candidates` | 新建同名聚焦测试 | 不解析原始 JSON、不选择公开操作、不构造共同响应 |
| C：服务运行时 | 新建 `ldvh.helper.operation_runtime`，并修改 `ldvh.helper.service`、必要时最小扩展 `ldvh.helper.responses` | 新建运行时测试并修改现有服务测试 | 不实现 01 的领域读取，不硬编码公开操作结果，不修改来源规范 |

三个分支不得同时修改同一生产文件或测试文件。`ldvh.helper.operations` 包的 `__init__.py` 由主线程在集成时建立，避免 A/B 同时创建产生无意义冲突。

### 冻结的最小接口

A 线导出：

```python
parse_specification_candidate_request(
    request: CommonRequest,
) -> SpecificationCandidateRequestParseResult
```

成功结果必须只包含 `responsibility_keys: tuple[str, ...]` 和已经把 `null` 归一为 `L0` 的 `disclosure: Literal["L0", "L1", "L2"]`；失败结果只包含领域输入问题，不生成共同响应或选择外层 `outcome`。A 线同时从 01 的输入契约形成 `required_inputs` 与 `optional_inputs` 的可复核描述；当前操作没有领域必填输入，两个可选输入为 `arguments.responsibility_keys` 与共同字段 `requested_disclosure`。Code 中的字段表示必须由 tests 对照来源章节检查，不能反向成为领域权威。

B 线导出：

```python
read_specification_candidates(
    repository: RepositoryInspection,
    *,
    responsibility_keys: tuple[str, ...],
    disclosure: Literal["L0", "L1", "L2"],
) -> SpecificationCandidateReadResult
```

B 线只消费已经验证的领域输入和现有 repository/projection 结果。返回对象必须分别提供：领域 `items` 或 `null`、requested/completed/not-completed 范围、来源回指、逐层 disclosure parts、实际机械检查的 verification、资格与未完成 gaps、必要 diagnostics，以及按 01/04 已定义条件建议的 `ok`、`partial` 或 `unavailable`。它不得构造共同响应顶层、判断任务相关性或重新解析规范文件。

C 线导出一个内部实现绑定与解析器。绑定只连接“来源声明中已存在的 `operation_key`”和 Code 实现，不授予公开操作身份；运行时先以 `OperationSourceInspection` 确认声明，再查找实现。C 线使用 fake implementation 独立验证以下共同行为：

1. 有来源、无实现：发现但不可调用；
2. 有实现、无来源：不进入公开操作清单，只报告契约缺口；
3. 来源与实现同时存在：发现结果显示实现依据，并由实现提供输入清单；
4. 未知 key：`invalid_request`；
5. 实现异常：`error`，不丢失可定位范围与诊断。

C 线在自身分支不导入 A/B 尚未集成的模块，也不预先注册 `read-specification-candidates`；实际绑定由主线程按 A → B → C 的顺序集成后增加。这样 C 可以与 A/B 并行完成通用运行时，而不通过临时桩或领域硬编码制造错误依赖。

### 集成顺序与完成条件

主线程依次集成 A、B、C，然后只在集成分支完成 `read-specification-candidates` 的实际绑定和端到端测试。发生接口偏移时优先让实现回到本节和来源规范，不通过扩大共同 Schema、修改 Specs 或复制转换逻辑解决。

完成条件：通用发现返回完整输入清单和可复核实现依据；单项 `capabilities` 对有效请求报告实际可用范围；`call` 按 L0–L2 形成累积结果、来源、验证和资格缺口；未知 key、未知职责标识符、混合完成范围、L3/L4、错误字段和关系缺口均有来源匹配的结果；Code tests、Ruff、格式、真实 CLI 与独立复核全部通过。

### 当前 Working Tree 实现结果

三个独立 worktree 已分别完成领域请求解析、候选读取和来源绑定运行时，主线程已按 A → B → C 集成并建立实际绑定。当前实现满足：

1. 公开操作身份仍只来自 01 的声明；显式 Code 映射只连接来源已定义 key 与实现，无来源实现不能进入公开清单；
2. `responsibility_keys` 字段闭集、类型、非空、去重和 L0–L2/null 已实现，L3/L4 明确返回 `invalid_request`；
3. 空 key 列表按路径与职责标识符确定排序读取全部 `active` 且通过适用已实现检查的候选，精确列表保持请求顺序且不做模糊回退；
4. L0–L2 按请求累积形成 `items`、来源、disclosure parts、整体机械检查 verification、资格 gaps、范围和 diagnostics；
5. 局部候选错误不再全局吞掉有效读取；失败候选不进入 `items`，但按 01 §9.5 保留在 `not_completed`、`gaps` 和必要诊断中，存在独立成功与失败范围时返回 `partial`；
6. 实现异常收敛为有边界的 `error`，不会泄露内部异常文本；共同响应保持 04/04.Att.01 的字段闭集。

当次真实 CLI 结果：通用发现报告 1 项来源定义且 `implementation.present: true` 的操作；默认单项 `capabilities` 为 `available_for_request`；默认 `call` 返回 12 项 L0，混合已知/未知 key 返回 `partial`，L2 返回累积概览与关系。当前仍保留 5 类未由 Code 自动证明的规则源资格条件、basis 直接必要性语义复核候选，以及“契约目标章节完整字段语义尚未由通用读取器自动证明”的缺口；实现和 tests 不把这些缺口改写为已保障。

---

## 已完成增量：Helper CLI 基础服务与公开操作发现

| 项目 | 当前决定 |
|---|---|
| 实现起点 | Git commit `ee40306bb667465eaa1dcaf7a6aa82b2b44fe910` 及其包含的规范读取与公开操作声明候选读取能力；本规划与本增量 Code/tests 的未提交变化一并属于当前实现对象 |
| 目标 | 保持 `ldvh` 进程入口、共同 JSON 请求与响应及 `capabilities`/`call` 基础分流，并从当前来源声明发现 `read-specification-candidates`，如实区分已定义、未实现、当次不可调用和直接调用不可用 |
| 不覆盖 | `read-specification-candidates` 的领域调用实现、领域输入清单机械解析、管辖范围解析、事实对象、行动模板执行、状态变更、Human 文本模式、环境 Hook/插件/adapter 接入和普通 wheel 的规则源部署 |
| 直接来源 | `ldvh-root`、`helper-cli-service-contract`、`helper-cli-request-response-fields`、`source-of-truth-traceability`、`code-engineering-practices` |

本增量不由 Code、tests 或实现注册表补造领域公开操作。通用 `ldvh capabilities` 只从当前来源的 `Helper 公开操作` 声明形成发现结果：已有声明但没有实现时仍返回该操作，`implementation.present` 为 `false`，并保留领域输入清单尚未机械确认、规则源资格尚未完整证明及实现缺失等缺口。针对已定义但未实现操作的单项 `capabilities` 完成可用性检查并返回 `unavailable_for_request`；直接 `call` 返回 `unavailable`。未知操作仍返回 `invalid_request`。

### 规则源定位与安装边界

公开请求没有定义规则源根目录参数，当前规范也没有定义外部配置文件或环境变量。为避免从 `cwd`、工作对象名称或隐藏变量猜测，本增量只支持 Code 源文件位于 LDVH Git Working Tree 内的源码运行或 editable install：定位器从实际导入的 `ldvh` 包路径向上检查父目录，取得首个同时包含固定 `specs/00-理念与构成.md` 和 `code/ldvh/` 的共置候选，再由现有 discovery 验证其是否为 Git worktree。定位器不得读取 `cwd`，不得跨越包路径的祖先链搜索，也不得仅凭同名目录把候选报告为可用规则源。

普通 wheel、复制出的单独 Python 包或其它未与当前规则源 Working Tree 共置的安装不在本增量支持范围。进程能够启动但无法定位上述根目录时，合法的通用发现请求返回 `unavailable`，并在 `gaps` 和 `diagnostics` 中说明规则源定位缺口；不得回退到打包快照、`HEAD`、缓存或空规则源并返回成功。未来需要支持独立安装时，必须先由相应规划明确规则源部署和外部配置契约，不在本增量增加未定义的公开参数或隐藏环境变量。

### 模块责任、接口与依赖方向

| 模块 | 承担内容 | 不承担内容 |
|---|---|---|
| `ldvh.helper.requests` | 解析标准输入中的零个或一个 JSON 对象；维护共同请求字段闭集、类型、缺省值和 `operation_key` 格式检查 | 不读取规则源，不判断操作是否存在，不解释领域 `arguments` |
| `ldvh.helper.responses` | 唯一维护共同响应和共同嵌套对象的 Code 表示与序列化；构造空范围、后续信息、来源、缺口和诊断 | 不选择业务 `outcome`，不创建领域结果或全局诊断码闭集 |
| `ldvh.helper.rule_source` | 按上述共置边界定位根目录，并调用既有 repository 与 operation source inspection | 不读 `cwd`、环境变量、缓存或 `HEAD`，不授予候选声明正式操作身份 |
| `ldvh.helper.service` | 编排请求、规则源检查、发现和调用分流；选择 04 已定义的外层 `outcome` 与退出码 | 不重复维护请求/响应字段，不实现领域操作，不形成全局操作注册表 |
| `ldvh.cli` | 解析三个公开命令形态、读取 stdin、调用 service、只向 stdout 写一个 JSON 对象并返回对应退出码 | 不读取规范、不判断能力、不在 stderr 承载完整结果所需信息 |

允许依赖方向为：

```text
ldvh.cli -> ldvh.helper.service
ldvh.helper.service -> ldvh.helper.requests
ldvh.helper.service -> ldvh.helper.responses
ldvh.helper.service -> ldvh.helper.rule_source
ldvh.helper.rule_source -> ldvh.specs.repository
ldvh.helper.rule_source -> ldvh.helper.operation_sources
```

`requests` 与 `responses` 不依赖 repository、operation sources 或 CLI；既有 specs 模块不反向依赖 Helper service。共同响应 Schema 的唯一 Code 维护位置是 `ldvh.helper.responses`，共同请求 Schema 的唯一 Code 维护位置是 `ldvh.helper.requests`。tests 通过共享 contract 断言检查完整共同结构，命令场景只断言自身差异，不在每个测试复制全部字段。

### 结果、退出码与诊断边界

本增量严格使用 04 §7.2：`ok=0`、`invalid_request=2`、`unavailable=5`、未预期且无法形成可信服务结果的实现异常为 `error=1`。当前没有领域实现，因此不会产生 `no_change`、`partial` 或 `rejected`。通用发现和已定义操作的单项可用性检查都完成了相应发现请求，外层返回 `ok`；直接调用已定义但未实现的操作返回 `unavailable`。repository 和 operation inspection 尚未自动证明的规则源资格条件必须逐项保留在 `gaps`，不得因发现了操作或外层成功而静默丢弃；没有返回规范信息时 `disclosure` 保持 `null`，没有符合来源契约的验证条目时不通过 `verification` 自造状态值。未知或格式错误的操作标识返回 `invalid_request`；请求 JSON、顶层类型、未知共同字段和字段类型错误同样返回 `invalid_request`。

能够识别 `capabilities` 或 `call`、取得一个非空 `operation_key` 且只是出现额外命令参数时，进程能够形成满足共同响应闭集的 JSON `invalid_request`。缺少 `call` 的必填 `operation_key`、空 key、未知入口或没有入口时，当前共同响应无法同时满足 `request_kind` 和非通用入口 `operation_key` 的必填约束，因此只返回进程级 usage 与退出码 `2`，不伪造一个违反附件闭集的机器响应。若未来要求这些形态也形成 JSON，必须先由 Helper 契约定义其合法字段表示。

规则源检查问题不得被改写成 0 个公开操作。能够定位规则源但本增量现有机械检查存在阻断问题时，返回 `unavailable` 并保留实际问题、受影响范围和未检查条件；未预期内部异常返回 `error`。诊断只使用可定位摘要和结构化 details，不建立来源规范未定义的 `code`。

### 风险与测试映射

| 风险 | 必须验证 |
|---|---|
| 来源声明被隐藏或被内部实现补造 | 当前真实 Working Tree 的 `capabilities` 返回 `ok`，只发现 `read-specification-candidates`，明确 `implementation.present: false`；已定义操作的检查与调用分别返回不可调用和不可用，未知 key 为 `invalid_request` |
| 共同 JSON 契约漂移 | 共享响应 contract test 一次检查全部顶层字段和共同嵌套闭集；请求参数化反例覆盖非 UTF-8、未知字段、非对象、无效 JSON、错误类型和通用发现非空 `arguments` |
| stdout 被日志污染或退出码丢失 | 使用真实子进程调用入口，验证 stdout 只能解析为一个 JSON 对象、stderr 为空、退出码与 `outcome` 对应 |
| `cwd` 改变规则源 | 从仓库外临时目录启动真实子进程，仍从包路径定位同一 Working Tree；不存在共置规则源的定位器组件测试返回明确缺口 |
| 规则源错误被包装为空发现 | 注入不完整 inspection，验证 `unavailable`、缺口、诊断和未完成范围，不返回 `ok` 空集合 |
| 测试形成第二套响应构造 | 完整共同结构只由一份共享断言检查；场景测试复用该断言且只补充场景差异 |

本增量完成条件：规划与实现一致；`ldvh` console script 已声明；真实进程覆盖通用发现、已定义但未实现操作的检查与调用、未知操作、无效 JSON 和仓库外 `cwd`；Code tests、Ruff 和格式检查全部通过；当前真实来源声明的操作能够被发现且不冒充已有实现；未实现的独立安装、具体操作调用、领域输入清单解析、管辖解析、环境接入和 Human 文本模式明确保留为未验证、不可用范围。

---

## 已完成增量：规范模型确定性基础

## 1. 当前实现范围与起点

| 项目 | 当前内容 |
|---|---|
| 实现增量 | 规范候选发现、当前规则源的可机械检查部分、L0–L2 派生信息和 Helper 公开操作声明读取 |
| 实现起点 | Git commit `f8a2363907221a5ac31e1409c2b471bbabe36e11` |
| 当前 Working Tree | 已形成根级 `pyproject.toml`、`code/ldvh/` 下的首批实现、`code/tests/` 中的 Code tests 及本规划的同步修改；这些内容共同构成本增量，不以是否已经提交改变当前读取对象 |
| 覆盖对象 | Python 包、规范读取模块、公开操作声明读取模块、测试和工程配置 |
| 不覆盖 | Helper CLI 进程入口、`capabilities` 响应、具体公开操作、事实对象、行动模板执行、管辖范围解析、环境接入、Web 适配、Index 提交前验证和跨历史重启 `retired` 职责检查 |
| 旧规划 | 无；`archive/v3/` 中的实现和文档不承担当前规划责任 |

首个增量只建立 Helper 后续消费规范模型所需的确定性基础，不把 V3 解析器缩减后复制回来。Helper CLI 仍是下一项直接消费者，而不是被放到全部领域实现之后；但当前规则源尚未定义 Helper 安装位置或当前规范根目录的外部配置契约，因此本增量不通过 Code 猜测该契约，也不提前发布只能在某个偶然 `cwd` 下工作的 CLI。

## 2. 当前规则源与实现目标

本增量直接消费：

1. `ldvh-root`：Code 提供解析、索引、校验和确定性反馈，并且不得扩大能力与完成声明；
2. `specification-model-foundation`：候选路径、固定 YAML 身份块、根规范启动顺序、普通规范与附件身份、当前 Working Tree、正文结构、关系和 L0–L2；
3. `helper-cli-service-contract` 及 `helper-cli-request-response-fields`：只读取 `Helper 公开操作` 声明结构，不能由实现注册表补造公开操作；
4. `source-of-truth-traceability`：未提交内容属于当前读取视图，`HEAD` 只提供实现起点和历史锚点；
5. `code-engineering-practices`：规划先行、模块责任、唯一维护位置、诊断、风险驱动测试和证据边界。

实现完成时应当能够：

1. 从显式传入的 LDVH 仓库根目录发现当前 Working Tree 中未被 Git ignore 排除、不跟随符号链接且精确命中 01 路径规则的规范与附件候选；
2. 按 01 的启动顺序，先用最小 envelope 唯一定位 active 01 候选，验证 root profile 与 00，再完整验证 01 及其他普通规范和附件；
3. 对 `active` 文件的身份、路径、标题、字符串双引号、字段闭集、关系、授权、`supersedes`、H2 结构和循环形成确定性结果；
4. 对通过本增量已实现检查的 active 文档范围生成 L0–L2 派生信息，同时保留不完整范围、问题和尚未自动检查的条件；
5. 从通过本增量已实现检查的 active 文档中定位固定 `Helper 公开操作` 表，形成声明候选并验证 key、表头、来源位置和契约引用；未检查条件满足前不授予当前规则源或正式公开操作资格；
6. 对当前真实仓库给出可重复结果，同时明确不能由 Code 单独证明的语义审核、规则适用、实现可用和完成范围。

## 3. 技术选择

### 3.1 Python 3.12

本增量使用 Python 3.12。选择依据是：任务以本地文件、Markdown/YAML 解析、关系检查和 CLI 后续复用为主；Python 能以较小构建负担提供清楚的模块与类型边界；当前开发环境已有 Python 3.12。V3 曾使用 Python 只作为历史事实，不是本次选择依据。

本增量不选择 TypeScript 作为共享语言。Web 不经过 Helper，不能为了复用语言把 Web 和 Helper 绑定为同一运行边界；首个增量也不需要浏览器或 Node 专属能力。若后续真实消费者或部署证据改变净收益，应先更新本规划，不把本次选择扩大为所有 LDVH 实现的永久语言规则。

### 3.2 工程结构与依赖

准备采用：

```text
pyproject.toml
code/
  ldvh/
    specs/
    helper/
  tests/
    specs/
    helper/
```

Code tests 统一位于 `code/tests/`，与被验证的 Code 构成要素共同归入 `code/`；Web API、component、E2E、可访问性与响应式测试在后续 Web 适配时归入 `web/tests/`。仓库根目录不设置 `tests/`。未来可以提供统一执行入口依次调用两套测试，但统一执行不改变各自的实现归属、工具链和测试文件位置。

1. 使用 `pyproject.toml` 声明构建、运行和测试依赖，并把 Python 包发现位置显式映射到 `code/`；`code/` 直接对应 00 的 Code 构成要素，使 AI 和 Human 不需要把通用 Python `src/` 习惯再解释为 LDVH Code；
2. 使用 `ruamel.yaml` 的 YAML 1.2 模式读取身份块；在构造对象前检查 token/event 和原始标量样式，显式禁止重复 key、多个文档、自定义标签、锚点、别名、合并键及未使用双引号的字符串值或字符串列表成员；不使用 PyYAML 的默认 YAML 1.1 标量行为替代 01 的 YAML 1.2.2 要求；
3. 使用标准库 `dataclasses`、`pathlib` 和类型标注表达内部结构，不在首个增量引入通用框架、依赖注入容器或全局 Schema 注册表；
4. 使用 `pytest` 组织 tests，并以共享 fixture 和参数化反例避免按每份规范复制相同断言；
5. 使用 `ruff` 做静态与格式检查。静态检查只补充行为测试，不作为功能正确证明。

上述选择参考 Python Packaging User Guide 对 [`pyproject.toml`](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/) 的说明，以及 `ruamel.yaml` 对 [YAML 1.2 支持](https://yaml.dev/doc/ruamel.yaml/overview/)和[重复 key 默认拒绝](https://yaml.dev/doc/ruamel.yaml/api/)的维护者文档。它们只支持工具适用性判断，不成为 LDVH 规则源；`code/` 名称来自 00 已确认的构成要素，不声称是 Python 行业统一目录标准。

## 4. 模块责任与依赖方向

| 模块 | 承担内容 | 不承担内容 |
|---|---|---|
| `ldvh.specs.discovery` | 验证显式仓库根是 Git worktree；从当前文件系统精确发现候选；调用 Git 判断 ignore；拒绝符号链接、近似路径和额外嵌套路径 | 不解析 Markdown/YAML，不读取 Index 或用 `HEAD` 补回已删除文件 |
| `ldvh.specs.markdown` | 通过逐级不跟随符号链接的文件打开与读取前后文件身份核对取得源码；完成固定 H1、紧邻 YAML 围栏、H2/H3 和严格 Markdown 表格的定位与最小解析 | 不判断规范是否生效，不解释领域规则，不渲染完整 GFM |
| `ldvh.specs.identity` | 根规范、普通规范和附件身份字段、字符串样式、类型与字段闭集检查 | 不扫描目录，不建立跨文件关系，不决定规则适用 |
| `ldvh.specs.structure` | 根据已解析身份选择根规范或普通规范 profile，检查 H2 顺序、连续编号、固定头尾、验证要求固定七列表头和声明所在章节结构 | 不建立规范依据、授权或替代关系 |
| `ldvh.specs.graph` | 消费 identity 结果，检查 key/编号唯一性、规范依据、结构归属、附件授权、替代关系、类型匹配、自指、重复和循环；报告可经其它直接依据到达的 `basis` 重叠候选，计算受机械问题影响的最小范围 | 不以图可达性替代“直接且必要”的语义判断，不发现文件，不重复解析 YAML，不生成 L0–L2 |
| `ldvh.specs.projection` | 消费 identity 与 graph 中通过本增量已实现检查的 active 文档节点、关系和影响范围生成 L0–L2；每项明确携带 `layer`，并保留 key、仓库相对路径、字段/标题/表行位置 | 不自行修正规则源问题，不生成规则适用或能力状态 |
| `ldvh.specs.repository` | 按 01 两阶段启动顺序薄编排：通过 `markdown` 的固定 YAML 位置只预读最小 envelope，先唯一定位 active 01 候选并验证 00，再完整验证 01 和其他候选；合并 discovery、identity、structure、graph 和 projection 结果 | 不成为 Schema、关系、诊断或投影的第二维护位置，不读取 V3/Web/事实实例 |
| `ldvh.helper.operation_sources` | 从仓库检查结果中通过本增量检查的 active 文档读取 `Helper 公开操作` 表，形成声明候选，验证表格与契约引用，并保留来源位置与未检查条件 | 不授予当前规则源资格，不形成正式公开操作，不实现操作，不计算当次可用性，不生成 Helper 响应 |
| `ldvh.diagnostics` | 内部问题对象、文件位置和面向调用者的确定性汇总 | 不创建跨规范错误码闭集，不改变来源规则语义 |

依赖只允许：

```text
operation_sources -> specs.repository
operation_sources -> specs.markdown

specs.repository -> specs.discovery
specs.repository -> specs.markdown
specs.repository -> specs.identity -> specs.markdown
specs.repository -> specs.structure -> specs.identity
                                      -> specs.markdown
specs.repository -> specs.graph -> specs.identity
specs.repository -> specs.projection -> specs.identity
                                           -> specs.graph

all error-producing modules -> diagnostics
```

`operation_sources` 只把 `repository` 提供的、通过本增量检查的 active 文档范围交给 `markdown` 定位 H3、严格表格和契约标题，不自行重新读取或重新解释身份，也不把该范围冒充已经满足全部规则源资格。`repository` 直接使用 `markdown` 安全读取并缓存每个候选的当次观察；最小 envelope 只用于启动定位，完整 Schema 仍由 `identity` 唯一维护。所有可能产生问题的模块直接依赖叶层 `diagnostics`，在最接近文件系统、Git、YAML、结构或关系失败的位置形成内部问题对象；`repository` 只合并，不把一种失败重写为另一种语义。`specs.markdown` 不依赖身份、仓库或 Helper；`specs.repository` 不依赖 Helper；任何模块都不读取 `archive/v3/` 或 `web/`。若实现需要未声明的横向 import、反向 import、全局可变注册表或在一个中心函数中按规范编号不断追加分支，必须先停止并重新检查责任划分。

`graph` 可以机械证明某个已直接列出的 `basis` 也能经另一直接依据到达，但图可达性不能单独证明该依据对当前规范已不再直接且必要：规范依据不使上位规范的全部具体规则自动传递生效。此类结果因此作为重叠候选单独报告，交由对照规范正文的语义复核判断；Code 不自动删除关系，也不据此阻断文档。明确重复 key、自指、缺失目标、非 active 目标或循环仍按机械关系错误处理。

## 5. 接口与 Schema 维护

首个增量只建立内部 Python 接口：

1. 所有读取入口显式接收 `repository_root: Path`，不使用模块级 `LDVH_ROOT`、隐藏环境变量或 `cwd` 猜测；
2. 文件读取必须在逐级拒绝符号链接后通过已打开的文件描述符完成，并核对读取前后文件身份；文件内容、身份对象、关系对象、诊断和派生行使用不可变 dataclass 或只读集合传递；
3. YAML 字段、允许值和声明表头只在对应生产模块维护一次；tests 使用一份集中、直接回指 01/04 章节的独立契约预期，不能从被测生产常量推导字段闭集、允许值和表头。共享 builder 只减少仓库和文件搭建重复，不决定断言期望；
4. L0–L2 只镜像 01 已定义的身份和关系，不加入实现状态、规则适用结果或领域字段；
5. 公开操作声明读取结果只包含通过本增量检查的 active 文档中符合固定结构的声明候选，并同时保留尚未自动检查的规则源资格条件；它不独立授予当前规则源资格或正式公开操作身份。当前仓库没有具体声明候选时，合法结果是空集合，不得用示例行或内部函数补造操作。

本增量不发布 JSON Schema，也不建立持久缓存。未来 Helper 共同请求与响应由 04 的授权附件定义；相应 Code 实现开始前必须在本规划中补充其唯一维护位置和消费者。

仓库薄编排接口返回一个内部检查结果，至少包含：

1. 当次实际观察到的候选文件及仓库相对路径；
2. 通过本增量全部适用检查的规范与附件范围；
3. 已形成的 L0–L2 派生项、每项明确的 `layer` 及逐项来源位置；
4. 每个问题、原始原因、来源位置和受影响 key/路径；
5. 因启动失败、关系传播或未实现检查而不完整的范围；
6. 本增量未自动检查的语义审核、Index 提交内容和跨历史生命周期条件。

部分失败时只保留能够独立成立的范围。01 或 00 无法唯一定位时不生成依赖其身份契约的派生项；重复 key、关系错误或授权错误至少暂停冲突成员及其依赖范围；无关候选仍可形成观察与诊断，但不能用局部成功冒充完整当前规则源已经验证。

## 6. 错误、诊断与可观察信息

1. 文件读取、UTF-8、YAML、Markdown 结构、身份、关系和声明错误必须保留文件路径与可定位位置；
2. 一个 `active` 规范或已授权 `active` 附件不成立时，不生成假定完整的当前规则源派生结果，也不回退读取 `HEAD`；
3. `draft` 和 `retired` 文件可以被定位和诊断，但不得进入当前派生结果；
4. 多个独立问题应尽量一次返回；`specification-model-foundation` 或根规范无法唯一定位时，只暂停依赖相应身份契约的后续检查；
5. 内部异常不得被转换为“没有规范”“没有操作”或成功空集合；
6. Git 可执行文件不可用、worktree 查询失败或 ignore 查询无法形成可信结果时，由 discovery 保留原始失败并把相应候选发现范围标为不完整，不按“未忽略”继续；
7. 文件内容和本机绝对路径只在定位问题确实需要时保留；未来机器响应的来源位置优先使用仓库相对路径。

## 7. 风险与测试映射

| 风险 | 主要检查范围 | 必须覆盖 |
|---|---|---|
| 候选发现错误读取旧文件或越界文件 | Git 临时仓库组合测试 | 非 Git 根、ignored、untracked、Working Tree 已删除但 `HEAD` 仍存在、符号链接、worktree 外文件、近似文件名、额外嵌套路径，以及 Git/worktree/ignore 查询异常不得被吞掉 |
| YAML 解析器与 01 契约不一致 | 局部组件行为、真实当前规范样例 | YAML 1.2 标量、字符串与字符串列表成员双引号、重复 key、多文档、标签、锚点/别名、顶层闭集、非映射 |
| 启动顺序形成循环或猜测 00/01 | 仓库组合测试 | 01 缺失、重复、非 active、00 缺失或身份错误、正常启动 |
| 无效 active 文件被静默忽略 | 仓库组合测试 | 路径/H1/编号/字段/H2/固定头尾/验证要求七列表头错误时整体结果含诊断且不回退 `HEAD` |
| 关系、附件授权与替代关系漂移 | 仓库组合测试 | 缺失或类型错误依据、非 active 依据、自指/重复/循环、`basis` 可达重叠候选及其非自动语义判断边界、父规范错误、未授权/多父附件、`supersedes` 同类型目标/旧成员状态及 L2 回指 |
| 声明示例或实现反向成为公开操作 | 声明契约测试 | 示例不进入结果、错误或重复的精确 `Helper 公开操作` H3、表格未紧邻 H3、错误表头/行、重复 key、越源或悬空引用、契约目标精确标题重复导致歧义、合法声明 |
| 生产常量与测试同步漂移 | 独立契约预期与故意变异反例 | 集中维护、直接回指来源的独立字面量预期；故意增删字段、允许值或表头时 tests 失败 |
| 测试复制导致 V3 式冗长 | tests 结构复核 | 共享最小仓库 builder、参数化错误样例、共同诊断断言只维护一次；builder 不生成契约预期 |
| 只在合成样例通过 | 真实组合测试 | 当前 Working Tree 的 9 份通过本增量已实现检查的 active 规范、3 份同范围 active 附件、0 项声明候选 |

测试不会恢复 V3 的 runner/profile/fixture 闭集，也不把每份规范的全部共同字段复制成独立测试。当前真实仓库测试只证明本次 Working Tree 和被执行路径，不证明规则语义审核、Helper 可用、Web 合规或环境接入。

## 8. 实现顺序与完成条件

实现顺序只表示本增量内部的建设前置：

1. 建立 `pyproject.toml`、包边界和最小测试入口；
2. 实现 YAML/Markdown 固定结构读取及局部反例；
3. 实现 discovery、身份与结构检查，以及 Git 临时仓库反例；
4. 实现 graph 的关系、附件、替代和影响范围检查；
5. 实现带来源位置和不完整范围的 L0–L2 派生结果；
6. 实现公开操作声明候选读取及契约引用检查；
7. 对当前 Working Tree 运行真实组合测试、静态检查和完整测试。

本增量只有同时满足以下条件才可以视为完成：

1. 本文覆盖的模块、依赖、接口和测试与真实实现一致；
2. 必要局部、组合、声明和真实仓库 tests 全部通过，没有 skip、隔离或 flaky 被计入通过；
3. 静态检查通过，失败诊断没有被空结果掩盖；
4. 当前仓库结果准确报告 9 份通过本增量已实现检查的 active 规范、3 份同范围 active 附件和 0 项声明候选，并列出尚未自动检查的条件；
5. ignored/untracked/deleted/symlink/越界路径、Git 查询失败、双引号、验证要求七列表头、`basis` 可达重叠候选、关系、附件、`supersedes`、L0–L2 `layer` 与来源回指、公开操作重复 H3/非紧邻表格/契约标题歧义、部分失败和独立契约预期 tests 全部通过；
6. 未实现的 Index 提交前验证、跨历史生命周期、语义审核、Helper CLI、管辖解析、领域能力、Web 和环境范围仍明确保留为未实现，不使用本增量结果声明完整当前规则源、available、integrated 或 completed。

## 9. 重新评估条件

出现以下任一情况时，先更新本文再继续相应实现：

1. 准备新增 Helper CLI 进程入口、规范根目录定位或安装配置；
2. 准备实现 `capabilities` 共同响应、具体操作调用或实现发现；
3. 准备扫描事实类型或行动模板声明；
4. 需要持久缓存、生成文件、跨进程服务、并发写入或 Web 共享解析；
5. 模块责任、允许依赖、Schema 维护位置或测试映射与本文发生偏移；
6. 当前规则源变化使首个增量的字段、关系或声明契约不再充分。
