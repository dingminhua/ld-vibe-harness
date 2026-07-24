# WorkCase 专属受控变更 Helper 操作实现规划

## 1. 规划身份与实现基线

本规划承接 `workcase-0006` 的已批准范围，适用于 `update-workcase` 及其直接共享基础。实现基线为本工作开始前已提交的 `3d99968f`；当前 Working Tree 中的 `workcase-0004.yaml` 与 `workcase-0006.yaml` 是有效事实载体，但不定义 Code 语义，也不属于生产实现输入。

规则权威保持单向：21 定义 WorkCase 专属操作与 Controller、Reviewer、Human 权责；05 定义共同单对象受控写事务；04 与 04.Att.01 定义共同响应；32 只组织行动选择。Code 不复制 WorkCase phase 图，不从审核结论或普通字段差异决定推进、升版或复审。

## 2. 模块责任与依赖

依赖方向固定为：规则来源 → 纯事实构造/共同事务 → Helper operation adapter → service/CLI。事实层不得导入 Helper。

| 模块 | 责任 | 明确不负责 |
|---|---|---|
| `ldvh.helper.operation_runtime` / `service` | 在有效服务请求边界形成唯一 `event_at`；响应档位组织和异常边界 | 领域 delta、WorkCase 推进判断 |
| `ldvh.facts.update_application` | 类型锁内重新读取、fingerprint CAS、no-change、后继时间、完整候选校验、原子替换、回读与条件回滚 | 解析 Helper 请求、构造 WorkCase 语义变化 |
| `ldvh.facts.workcase_update` | 依据显式顶层 delta 和托管动作确定性形成 current WorkCase after；维护与 21 同源的固定 reset 投影 | 判断实质变化、选择 phase/版本/复审、解释审核内容 |
| `fact_update_operation` | 把既有完整目标请求适配到共享事务并维持原 result 兼容 | 复制事务实现 |
| `workcase_update_request` / `workcase_update_operation` | 闭集请求解析、current-profile 前读、after 构造、共享事务调用和紧凑 receipt | 提供 `advance/pass/close` 等状态机命令 |
| `creation` / creation operation | YAML 稳定序列化；共享协调锁权限失败分类；创建时点复用 | 改变 allocator 位置或并发保证 |

## 3. 请求与结果维护

`update-workcase` 接收稳定 `fact_ref`、`expected_content_fingerprint`、顶层 `set`、`remove` 和闭集 `managed_records`。`set` 与 `remove` 只处理顶层整值，不做 JSON Patch 或嵌套 merge。Controller 必须显式给出 phase、status、plan/result version 及其它语义字段；Helper 只填统一时间、审核 basis/fingerprint、审批版本和固定 reset。

托管动作只覆盖：计划审核整体替换、结果审核新增、结果审核 Controller 处置、执行批准和关闭批准。result review 的 `projection_key` 由调用方显式选择。审核新增与 Controller 处置不得同次形成。单次托管动作最多 16 项，receipt 只返回稳定引用、前后指纹、`event_at`、前后状态投影、变化字段和托管记录索引/指纹；完整对象另行读取。

`update-fact-object` 继续兼容其它事实类型、legacy 和既有 current WorkCase 调用。专属操作是减少手工错误的便利层，不是新的授权来源或唯一写入口。

## 4. 副作用、失败与诊断

所有受控写继续使用 `git_common_dir/ldvh` 的“项目 + 类型”持久协调域。不得回退到 worktree-local、临时目录或无锁。只把进入共同锁前观察到的权限或只读文件系统失败分类为 `controlled_write_lock_unavailable`；目标读取、写入或回读阶段的其它异常不得伪装成锁不可用。

结构错误使用 `invalid_request`；完整 after、当前状态、CAS 或现有 transition 不接受使用 `rejected`；预期环境能力缺失且零写入使用 `unavailable`；未知实现异常或无法形成可信残留结论使用 `error`。诊断不得包含原始异常正文，只返回稳定 code、stage、资源角色、系统错误类别、零写入声明和恢复条件。

`event_at` 在 service 边界只观察一次。确有变化时，它同时用于 `updated_at`、本次托管审核/批准时间和当次 Working Tree observation；不能严格晚于当前 `updated_at` 时拒绝。`no_change` 不生成对象事件或写入。

## 5. Schema、序列化与响应档位

YAML emitter 必须避免自动折行产生行尾空格；不得对序列化结果逐行 `rstrip`，以免改变字符串值。每种载体在写入前仍按完整 parse/schema/transition/project validation 验证。

`compact` 只在资格缺口的拥有位置聚合，不全局合并领域缺口。聚合项使用附件定义的 `member_count`；`diagnostic` 展开实际明细。两个档位不得改变领域 result、顶层 scope/outcome/changes、授权判断、写行为或在相同冻结 `event_at` 下生成的最终载体 bytes。

## 6. 风险与验证

主要风险是：共享事务抽取破坏 generic update 兼容；delta 构造复制状态机；reset 清理超出 21；review index 在并发后错配；锁错误分类过宽；时钟差形成非后继；YAML 修复改变值；compact 聚合丢失缺口。分别使用 API 兼容测试、来源范围匹配、expected fingerprint + index、进入锁阶段定点异常、冻结时钟、serialize/parse roundtrip 和 profile 等价测试约束。

验证至少覆盖：规则发现与安装快照；请求闭集和冲突矩阵；current/legacy/非 WorkCase；计划/结果升版固定 reset 与 audit continuity；四类 Reviewer conclusion 不自动推进；review append/resolve 分步；执行/关闭批准；完整 phase 代表路径与原子关闭；no-change、stale、并发、回读回滚；linked worktree allocator；common-dir 权限失败；compact gap 唯一与 65% fixture 指标；最多 16 项托管动作下 receipt ≤ 4096 canonical JSON bytes；YAML 无行尾空格且语义等价；聚焦测试、Ruff 和 full-v4。

## 7. 明确排除

不修改 00，不改变 21 状态机或 Reviewer/Controller/Human 权责，不实现多对象事务、自动编排、Spark 创建/路由或 legacy 迁移，不改变 C runner/DTO 语义，不修改 Web/WC0004/D/E，不处理 native Windows reparse、稳定签名公共化、output no-follow 或历史 launcher，也不 push 或创建 PR。
