# Study 重建事实契约

## 范围与来源

本规划覆盖以 v3 的研究表达为基线，重建 v4 Study 的事实契约与其 Code/Web 消费面：Study 保持外部调研锚点，正文恢复“研究问题、输入与边界、关键发现、建议、后续分流”五段，生命周期收敛为 `active / retired`，并移除 Study 对 `applicability`、`validation_summary` 和 `supersedes` 的依赖。

直接消费：`00` 的事实源、构成归口、验证与 Human Gate 边界；`05` 的字段登记、对象更新、来源、状态与派生 Schema 边界；`24` 的 Study 类型语义；`07` 的规划、接口、Schema 与测试要求；`08` 的 Web 只读呈现边界。

本规划不重新研究任何外部主题、不创建新的 Study、不把重开队列变成事实对象，也不让 URL、测试、Web 或 Code 证明自然语言研究结论。

> 规划补救说明：这一增量的部分实现已在本规划形成前开始，违反 07 §5.1 的先行要求。本文件用于停止继续偏移、明确已发生范围和后续验证，不把该违规追溯为已满足。

## 模块责任与接口

| 范围 | 责任 | 不承担 |
|---|---|---|
| `specs/24-Study-研究报告.md` | 定义 Study 的外部调研定位、五段正文、两状态和退出边界 | 定义外部事实当前性、研究正确性或下游行动授权 |
| `05.Att.01` 与 `05` | 维护 `urls` 共用结构及 Study 退出共享字段的适用范围 | 复制 Study 的领域语义或定义第二份 Schema |
| `facts/contracts.py`、`study_markdown.py` | 从来源派生 Study 状态闭集、关系闭集与五段 Markdown 机械检查 | 判断研究价值、资料充分性或自然语言质量 |
| `facts/validation.py` 与事实测试 | 检查五类对象共享 URL 成员结构及 Study 机械载体 | 机械裁决 `summary` 是否真的说明了资料价值 |
| Web Study 阅读与状态筛选 | 只读呈现当前来源定义的 Study 字段与状态 | 生成研究结论、关系或验证字段 |

接口维护：统一字段登记与 Study 类型绑定是字段适用范围的唯一来源；Code 常量和 Web 字段列表必须由其派生，不得保留 `superseded`、`applicability` 或 `validation_summary` 的 Study 专用兼容入口。

## 副作用、历史对象与风险

规范与实现变化使既有 v4 Study 载体需要迁移为新 Schema。Human 已决定所有旧 v4 Study 退出；迁移只允许保留原始研究正文、外部 URL 与退出理由，不能把旧短文提升为新的 active 研究。

对既有对象的正式重写应使用 `read-fact-objects` 与 `update-fact-object` 的受控 CAS 流程。当前工作树没有可选定的 governed-projects 配置，因此该入口不可用；在配置恢复前，不宣称这些历史对象已完成受控更新验证。

Web 的字段和状态移除会改变详情页及筛选可见内容。Human 已明确决定 Study 仅保留 `active / retired`，并同意 Study 退出 `applicability`、`validation_summary`；随后明确要求按本整改建议推进。该授权仅覆盖详情页移除这些已退出节点、筛选仅呈现这两个状态，以及其必要的派生显示收敛，不延伸为其它对象或其它产品行为的改动。若需要把具体节点变更作为独立产品承诺，应另取 Human 明确决定。

## 风险与验证映射

| 风险 | 检查 |
|---|---|
| Study 仍接受第三状态或替代关系 | contracts、转移和关系测试；扫描 Study 规范与 Web 筛选 |
| Study 正文仍按旧六段或存在空段 | Markdown carrier 正反测试；逐份载体机械校验 |
| `urls` 语义只在 Study 中生效 | Spark 等其它类型缺 `urls[].summary` 的 Schema 测试 |
| 旧 Study 因字段移除变为不可读 | 受控读取可用时逐份 F3 回读；配置缺失时只报告 direct parser/validator 范围 |
| Web 继续读取已退出字段 | Web API contract tests、typecheck、生产构建与页面字段扫描 |
| 改动破坏相邻事实能力 | 全量 Code tests；若存在既有失败，逐项区分与本增量的因果关系，不能宣称全绿 |

已验证范围包括：规则投影、Study parser/Schema、九份 Study 的 direct mechanical validation、聚焦 Python tests、Web API tests、typecheck、build 和 Ruff。未验证范围包括：受控 Study 更新、真实外部来源当前性、Study 自然语言质量，以及全量 Code suite 中已有的非 Study 失败。
