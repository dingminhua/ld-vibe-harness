# V4 Code 实现规划

> 当前规划入口：本文是当前唯一的 Code 实现规划及稳定入口。本文不是规则源、产品契约或任务进度记录；实现语义必须回到当前有效规范和授权附件。

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
