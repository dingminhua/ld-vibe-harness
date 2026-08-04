# 环境无关启用、只读 doctor 与发行物快照实现规划

> **已退役。** 本规划记录原 distribution/规则快照实现，不再承担当前实现责任。当前唯一载体为源码仓库，入口、Doctor、依赖准备与 common-dir Hook 以 01、04、09、09.Att.01 及当前 Code 为准；正文仅保留为历史实施证据。

## 1. 规划身份、来源与实现基线

本规划承接 `workcase-0009` plan version 2，覆盖环境无关的获取、安装、LDVH 自有配置检查、接入面发现和验证基础。规则权威保持单向：09 定义共同接入方法、`ldvh-doctor/1` 最低边界、功能型 Hook 和能力状态；04 定义 Helper 共同请求/响应；02 定义管辖解析；03 定义 commit-msg Gate；07 定义本规划与风险驱动测试；33 只组织一个已有接入单元的安装、验证和回滚。Code 不研究厂商协议，不判断具体 AI 开发环境是否支持，也不把静态入口存在提升为真实接入。

实现起点为 `ed7df76c7fb1d8c7139cef676631d777b6e17e7f`。本规划是在 result version 1 首轮独立审核指出缺少稳定 Code Implementation Plan 后形成的当前补正规划，覆盖当前 Working Tree 中尚未提交的 doctor、打包和 tests 变化；它不声称在这些实现开始前已经存在。补正动作同时逐项比较当前实现与本规划，发现偏移时以当前来源为准修正实现或规划。

本规划与 `codex-context-recovery.md` 共同读取共享上下文恢复入口，但不覆盖 Codex adapter、事件映射和真实环境验证；与 `workcase-controlled-update.md` 共同消费 Helper CLI，但不覆盖事实写事务；与 `full-v4-working-tree-evidence.md` 共同消费完整测试记录，但不改变 runner 或证据 DTO。

## 2. 实现目标与明确排除

本增量提供：可从当前源码构建和回指的 wheel/sdist；安装后可调用的 `ldvh-doctor`；对显式 workspace、工作对象、Helper、LDVH 配置和既有接入面的只读诊断；规则快照与已声明接入面附件的随发行物投影；隔离安装、核心直调、卸载和完整测试证据。

本增量不提供公共 registry 或 marketplace 发布，不实现目标环境 manifest、script 或 adapter，不扫描或修改目标 AI 开发环境，不安装外部工具，不登录、写凭据、触发信任或重启，不新增 Helper 公开操作、统一厂商 payload、事件路由或事实 Schema。版本发布规范与行动模板由 `spark-0023` 独立承接。

## 3. 模块责任与依赖方向

依赖方向固定为：09/04/02/03 当前来源 → 既有 Helper 与入口 → `ldvh.doctor` 只读聚合 → console entry point；发行配置只把 Code、规则快照和已声明接入面附件装入 artifact，不反向定义诊断或环境语义。

| 模块或资产 | 内聚责任与输入输出 | 副作用 | 明确不负责 |
|---|---|---|---|
| `ldvh.doctor` | 校验显式绝对 workspace/helper 与非空 locator；调用既有 Helper；形成 `ldvh-doctor/1` JSON | 启动两个只读 Helper 子进程，读取 distribution metadata 与入口文件 | 目标环境发现、配置写入、安装、修复或支持判定 |
| `ldvh.helper` / `ldvh.governance` | 通过 `capabilities` 与 `resolve-governance-scope` 返回当前共同合同和管辖事实 | 只读来源、配置、路径和 Git 身份 | 为 doctor 建立专属操作或第二管辖模型 |
| `pyproject.toml` | 登记 `ldvh-doctor` console entry point、包版本、Python 和依赖声明 | 安装时生成脚本 | 声明公共发布已经发生或扩大平台实测范围 |
| `setup.py` | 冻结规则快照，并投影 `09.Att.01` 已声明的接入面附件到发行物 | 构建目录和 artifact 写入 | 复制或改写根级 `docs/` 临时材料，联网解析依赖 |
| `code/tests/doctor` / `packaging` | 分别验证只读诊断和发行生命周期 | 使用临时目录、Git 仓库、venv 和本地构建 | 证明任一具体 AI 开发环境已接入 |

禁止 `doctor` 导入环境 adapter、厂商 SDK 或事实写操作。根级 `docs/` 是临时材料，不随发行物打包，也不进入 doctor 或其它能力验证；`09.Att.01` 的发行投影来自当前规则源，不能与根级 `docs/` 混同。接入面清单只引用已存在的 console entry point 和规则来源，不从文件名猜测更多能力。

## 4. 接口、Schema 与维护责任

`ldvh-doctor/1` 的最低语义来源是 09；Code 维护位置唯一为 `code/ldvh/doctor.py`，CLI 与测试消费同一结果。结果顶层稳定包含：`contract`、`status`、distribution、helper、configuration、integration surfaces、checks、limitations 和 diagnostics。根级 `docs/` 不进入结果或 `status` 计算。`status` 只允许 `ready|attention|unavailable`：所有受检查边界均肯定通过才可 `ready`；可形成可信结果但存在缺口为 `attention`；输入、进程、合同或结果身份不足以形成可信结果为 `unavailable`。

Helper 共同响应仍由 04 与现有 validator 维护。doctor 只消费 `contract`、请求身份、`outcome`、进程 exit code 和两个操作的必要 result 字段；任何非 `ok` Helper outcome 不得因内层残留字段看似有效而形成 `ready`。Helper 合同或进程身份不一致直接失败，不猜测或回退。

接入面投影当前包含 Helper CLI、环境无关上下文恢复、Git commit-msg Gate 和 Git Hook 管理器。其具体请求、结果和失败语义继续由各自来源/实现维护；doctor 只报告脚本是否存在且可执行。新增、移除或改名时必须同步 `pyproject.toml`、`doctor.py`、接入面文档和 packaging/doctor tests，且需要相应来源先成立。

## 5. 错误、诊断和信息边界

显式输入缺失、路径不是绝对目录、Helper 不可执行、子进程失败或超时、非单一 JSON、合同/请求身份/outcome 与 exit code不一致、distribution 缺失，统一转为 `unavailable`，CLI exit code 为 1。可可信读取但配置、管辖、入口或 Helper 管辖调用不是 `ok` 时为 `attention`，CLI exit code 为 0，调用方必须读取结构化 checks，不能把 exit 0 当成完整接入成立。

诊断保留稳定摘要和异常类型，不输出凭据、完整环境变量、Helper stderr、目标环境配置或任意目录扫描结果。子进程固定 20 秒超时、关闭 stdin、捕获有限单次输出；当前实现不承担通用输出 byte budget，若 Helper 输出规模或外部暴露面改变必须重新评估。

## 6. 风险与测试映射

| 风险 | 主要检查范围 |
|---|---|
| 相对路径、缺失 helper 或隐式 cwd 被猜测 | doctor 输入负例和 CLI unavailable 契约测试 |
| Helper 合同、请求身份、outcome/exit 不一致被吞掉 | `_invoke_helper` 定向测试及 CLI 错误路径 |
| 非 `ok` 管辖响应携带残留 valid 字段却误报 ready | partial/non-ok outcome 回归测试，configuration/governance 必须 attention |
| 静态入口被表述为真实环境接入 | limitations、独立语义复核和入口行为 tests |
| 模拟 Hook 成功或能力状态 fixture 被提升为真实环境证据 | 三类 synthetic fixture、肯定依据逐项负例和无真实环境身份断言 |
| 接入面入口或来源漂移 | doctor surface 集合、规则来源和 console entry point tests |
| wheel/sdist 漏掉 doctor、entry point 或规则快照 | direct wheel、无 Git sdist→wheel 与 archive 内容检查 |
| 安装或升级留下旧 RECORD，卸载后入口残留 | 隔离 venv 的旧版→当前版替换、核心直调、卸载和回读 |
| 本地 artifact 被冒充离线或公共发布 | distribution metadata、运行记录与未公共发布边界 |
| 测试污染用户工作树 | full-v4 before/after Working Tree 证据和 `changes=[]` |

聚焦验证至少运行 doctor/specs/packaging tests 与 Ruff；最终完成声明使用 `tools/run_full_tests.py start --plan full-v4` 的耐久化记录。macOS 当前环境和临时 POSIX venv 的通过不证明 Windows 或任一具体 AI 开发环境；native Windows 及真实目标环境保持 unverified。

## 7. 当前比较结果、演进与缺口

首轮规划补正比较确认：doctor 依赖方向、两次 Helper 调用、只读副作用、三态结果、接入面投影、规则快照投影方向和主要 tests 与本规划一致。发现的一个偏移是管辖 Helper 返回非 `ok` 但仍携带 `valid/governed_single` 字段时可能误报 `ready`；本增量将其修正为 `attention` 并加入回归测试。第二轮结果审核发现固定 `dist/` artifact 仍早于该修复，且 item-05 的三类模拟 fixture 尚未形成；本增量重建并实装回读当前 artifact，同时用纯 tests fixture 检查模拟调用成功、未知保持 `unverified`、只有范围匹配肯定缺失依据才为 `unsupported`。这些 fixture 不进入生产 Code，也不映射真实厂商。

尚未验证范围为原生 Windows、公共发布和任何具体 AI 开发环境真实触发。若未来需要新增 manifest、script、薄 adapter、厂商 payload 转换、网络获取或新的 Helper/Gate 合同，必须停止复用本规划作为充分覆盖，先读取具体环境来源并建立独立 Code Implementation Plan；已有接入单元完成后才可进入 33。
