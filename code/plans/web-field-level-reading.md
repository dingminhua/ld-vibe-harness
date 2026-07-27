# Web 字段级事实读取迁移计划

## 1. 目标、来源与范围

本规划实施 00 §8.3、03 §6、05 §11、08 §§5、7、10 已定义的 Web 字段级读取边界：Web 在 Helper 已确认的单一管辖项目范围内直接读取 Working Tree 当前事实载体；页面消费字段可独立呈现，字段问题与未消费结构保持可见，而 Helper 的完整机械校验、CAS 和受控写入仍只服务 AI 路径。

直接来源为 00、02、03、05、07、08 及 20–24；字段身份、条件出现规则和面向 Human 的标题继续由 05 的登记及具体类型规范定义。本规划不改变上述来源、不新增事实字段、状态或写入能力，也不改变 `code/ldvh/` 的 Helper、校验、关系或 CAS 实现。

实现起点为当前 `dev-v4` Working Tree。它替代既有规划中与 Web V4 Python machine、`mechanically_valid` 页面前置和 local reader `invalid` 整对象失败相关的实现安排；Spark 内容阅读、Study 载体阅读及 WorkCase 专属字段语义仍由各自既有规划和来源定义。本规划只统一其 Web 读取与呈现边界。

Human 已明确授权的可观察变更范围是：对象列表、详情、关联预览和 Dashboard 从“完整校验后才可读”改为“字段级如实呈现并披露问题”；不包括改变事实内容、状态、关系、创建或任何写入操作。

## 2. 模块责任与调用方向

| 模块 | 责任 | 不负责 |
|---|---|---|
| `web/api/services/governanceScope.ts` | 通过 `ldvh call resolve-governance-scope` 请求并逐项校验单一工作对象的配置、范围、身份和 worktree 证据，返回 Web 可使用的读取边界 | 读取事实、把 Helper 输出变成页面事实或判断规则适用 |
| `web/api/services/projectFiles.ts` | 复用共享管辖解析服务取得项目文件浏览边界 | 维护第二套 Helper 请求/响应校验 |
| `web/api/services/localFactReader.ts` | 在已验证边界中读取 YAML/Markdown 载体，形成字段值、字段问题、未解析结构和读取元数据 | 完整 Schema/状态/关系校验、身份语义裁决、写入或 CAS |
| `web/api/services/facts.ts` | 对全部类型统一编排字段级 list/detail 投影，保留范围、字段问题和未解析结构 | 为 WorkCase 保留 V4 Python/Code machine 特判或用字段问题伪造机械结论 |
| `web/src/pages/object-detail/*` | 呈现类型来源规定的字段、缺失必填字段的空态、未解析结构和关联读取状态 | 推断事实内容、补写字段、用 ID 充当未读关系目标名称 |
| `web/src/pages/{ObjectList,Dashboard}.tsx` 与 API routes | 将无法形成 WorkCase 进展分组的对象和范围如实可见，不混入第五个分组 | 用未知 phase 猜测分组、遗漏对象或把派生分组写回事实 |
| `web/tests/**` | 覆盖字段级解析、管辖范围失败、WorkCase 统一读取、页面呈现与旧链路删除 | 将页面读取通过宣称为完整机械有效 |

调用方向固定为：`Web route/service → governanceScope (仅范围) → localFactReader → Working Tree → Web projection → UI`。范围解析是唯一允许的 Web→Helper 调用；事实内容不经 Helper。Web 不启动 Python 进程、不调用 `ProjectFactIndex`、不执行项目级关系稳定化或完整机械校验。

## 3. 读取与接口契约

`localFactReader` 为每一页面声明实际消费字段集合；集合是 Web 投影配置，不定义字段语义。输出区分：

1. `read_status: readable`：载体可读取且可解析；消费字段逐一返回，缺失或类型不符产生 `field_issues`，不会把对象升级为读取失败；
2. `read_status: unreadable`：仅限 I/O 失败或 YAML/frontmatter 不能解析为载体；保留预期路径、声明载体、范围和读取问题；
3. `unparsed_structures[]`：未消费字段、退出字段或不能归入消费结构的值，以稳定路径、原因和原始 JSON 值（存在时）交付；它不表示对象无效。

已有 `check_status` 不再承载 Web 本地完整校验结论。需要呈现 Helper 精确读取结果时，仍原样保留来源定义的 `check_status` 并标明其来源。列表不承诺详情的 source metadata；详情使用实际读取得到的 `canonical_path` 与 `carrier`，不从 ID、target 或文件名猜测。

## 4. 风险、失败与测试

| 风险 | 防护与验证 |
|---|---|
| 未验证或跨项目路径被读取 | Helper 范围响应逐项校验测试；失败时所有事实读取返回范围不可确认且无本地回退 |
| 字段问题再次造成整对象失败 | 缺失、类型不符、身份不匹配的 YAML/Markdown fixture；断言可解析消费字段仍返回 |
| 额外/旧/嵌套结构被静默丢弃 | 断言每项进入 `unparsed_structures`，含路径、原因和原值 |
| WorkCase 仍启动 Python 或使用完整校验 | 删除 V4 machine/transport，静态与 API tests 断言所有类型统一走 local reader |
| 必填空态或 WorkCase 分组问题被 UI 隐藏 | 组件/API tests 覆盖字段空态、`进展分组不可判定`、`工作项进展不可判定` 与 Dashboard 未分组范围 |
| 关系目标用 ID 冒充名称 | 读取中/失败状态测试，断言显示稳定身份和读取状态，不把 ID 放入名称槽 |
| 改造引入性能倒退 | 对同一 fixture 记录 WorkCase 前后 list/detail 的进程/响应时间；新路径不得有 Python 冷启动或全量关系校验 |

验证至少运行 Web API tests、TypeScript check、build、相关 Code/Helper tests及字段级页面/组件 tests；全量验证只声明其实际运行范围。旧 V4 transport、Python machine 和相应 tests/docs 必须在新链路覆盖后同时删除或更新，不能双路径并存。

## 5. 已知边界与演进

字段消费集合、空态和未解析结构只服务当前页面；它们不成为事实 Schema、通用 DTO 语义或 AI 消费契约。若未来需要改变字段身份、出现条件、状态、关系、写入、跨项目读取或授权边界，必须先修正相应 Specs 并完成独立复核，再更新本规划与实现。
