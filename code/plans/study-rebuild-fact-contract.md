# Study 阅读与 V4 事实详情修复计划

## 1. 实现目标与来源

本计划在编码前落实已冻结的来源修正：

- `specs/24-Study-研究报告.md`：Study 是外部调研形成的项目启发；摘要层依次使用 `research_intent`、`abstract`、`recommendation_summary`，`research_question` 留在完整报告；五个 H2 保持，但研究质量不退化为 H3 数量或固定表格的填空检查。
- `specs/05-事实模型基础规范.md` §§11.2–11.7：精确事实读取/写入的 `canonical_path`、`carrier` 与读取状态有来源边界；`canonical_path` 只是预期位置，不单独证明内容存在或有效。
- `specs/08-Web 呈现与交互规范.md` §§5、7、10：Web 独立读取事实；预览、源路径复制和正文阅读先取得精确读取；路径、载体和读取状态必须可追溯；已读 Markdown 以声明载体渲染，失败不回退为 object ID、route target、推测状态或原始 Markdown；有效对象身份区显示类型、状态和 ID。
- `specs/07-Code 实践与测试规范.md` §§5、7、10–11：本计划先于后续跨 API/前端/测试实现，明确接口、职责、失败边界与风险测试。

Human 已授权的范围是：修复 v4 Study 相对 v3 的可读性回退，并把同一条路径/载体/身份投影缺陷在所有 V4 事实详情与预览中一并解决。文件名不迁移；Web 不通过 Helper 读取事实；不重建 V3 的 `user_intent`、旧关系或审计字段；不把 Web 或测试变成事实源。

本计划替换先前把 Study 正文按 H2 直接铺在详情页、并以文件扩展名推断内容格式的实现设想。此前已有的实现先行不构成符合 07 §5.1 的证据；本文件仅规定从当前 Working Tree 开始的整改。

## 2. 已确认的缺陷与目标行为

| 观察到的缺陷 | 根因 | 目标行为 |
|---|---|---|
| V4 Study 详情将 `research_question` 与意图、摘要、建议并列，并在下方直接展开整份报告 | `StudyReadingLayout` 把五项都作为同级节点，`StudyReportBodyEntry` 再按 H2 拆开内联 | 详情和对象预览只显示三个摘要字段；正文只保留同一源正文的深入阅读入口，H2/H3/表格在深入阅读内完整呈现 |
| Study 深入阅读显示字面 `##` 和 `|` | `StudyReportBodyEntry` 把 object ID 当作 `docPath`；`DocPreview` 仅从 `.md` 后缀猜测 Markdown | Panel payload 显式携带已读取对象的 Markdown carrier；`DocPreview` 优先按 carrier 渲染，路径后缀只保留给独立文档加载的兼容判断 |
| 详情页和对象预览复制 `study-0010` 而不是 `ldvh-base/studies/study-0010.md` | API 详情响应保留 `canonical_path` 却没有规范化 `path`；前端回退到 `target`/ID | 所有 V4 精确详情以 `canonical_path` 作为唯一 source path；没有该值时不显示复制路径，也绝不把 ID 或 target 当文件路径 |
| V4 详情头缺少可读的类型标签 | `ObjectIdentityHeader` 仅在 compact 模式显示类型；主详情只将状态塞进复制操作区 | 已读有效对象的详情与预览均显示类型、类型状态词和稳定 ID；读取失败显示读状态和范围，不猜测领域状态 |
| Web 本地读取器丢弃 carrier，且用 `unverified/parse_failed` 混合“读到内容”和“未验证” | `LocalFactItem` 未携带 carrier；`projectItem` 未投影 carrier；读取结果没有面向 Web 的可消费状态模型 | 维持 Web 独立读取，但为所有 V4 事实保留 path/carrier/read status；Web 的 `readable` 只表示本地读取和最小结构检查成功，不冒充 05 Helper 的 `mechanically_valid` |
| Study parser 仍要求固定 H3、至少两个发现和固定分流表 | `study_markdown.py` 先于来源修正实现了过窄的模板 | parser 只检查 frontmatter、五个唯一且顺序固定的非空 H2；研究发现、建议、分流的实质质量留给 AI/Human 审核 |

## 3. 模块责任、依赖与接口

| 模块/边界 | 责任 | 允许依赖 | 不承担 |
|---|---|---|---|
| `code/ldvh/facts/carriers/study_markdown.py` | 按 24 解析 frontmatter，机械检查五个 H2 的唯一性、顺序和非空 | 事实模型 carrier/model | H3 标题/数量、表格形状、研究价值或外部资料质量判断 |
| `code/tests/facts/test_study_carrier.py` 与 `code/tests/specs/*` | 覆盖放宽后的 carrier 边界，并将登记数从 120 同步到 122 | 当前 specs、carrier | 以旧测试反向收紧当前来源 |
| `web/api/services/localFactReader.ts` | 在确定管辖范围后独立读取当前文件，确定预期路径、类型载体、最小解析结果和本地读取状态 | Node 文件读取、YAML、当前事实位置约定 | Helper 调用、自然语言/完整 Schema 语义校验、`mechanically_valid` 声明 |
| `web/api/services/facts.ts` 与 `web/api/routes/objects.ts` | 将精确读取的 source metadata 与可读事实一起交给详情；将无效/缺失/不可用读取以可呈现失败结构交给前端 | local reader、路由 DTO | 以 API 定义事实字段或状态语义 |
| `web/src/utils/factReadMeta.ts`（新增纯函数）与 `web/src/utils/api.ts` | 从精确详情提取 source path、carrier、读取状态/问题；拒绝 ID、target 充当路径 | API detail 类型 | 解析正文或决定领域状态 |
| `ObjectDetail`、`PanelContent`、`panelContext` | 只在 readable 精确结果上展示语义详情和正文；将 carrier 明确传至 doc panel；复用同一 Study 摘要语义 | `factReadMeta`、现有布局/Panel | 重组正文、从路径猜 carrier、掩盖读取失败 |
| `ObjectIdentityHeader` | 以传入的已读对象身份显示类型、状态和 ID；路径复制只使用 source path | i18n/现有视觉组件 | 以 status 缺失推断领域状态 |
| `web/docs/04-ObjectDetail.md`、`web/docs/10-Web开发现状与设计语言基线.md` | 记录实现设计与测试映射，回指 08/24 | 冻结 specs、当前实现 | 充当规则源或保留已废弃的页面契约 |

读取方向固定为：`Web 路由 → facts service → localFactReader → Working Tree`；详情数据再经 `api.ts/factReadMeta → ObjectDetail 或 ReadingPanel`。正文的呈现方向固定为：`Study body + carrier → StudyReportBodyEntry → PanelContent DocPreview`。不得从组件反向读取文件、从 `target` 生成路径，或让 Panel 按后缀猜测已知事实正文的格式。

### 3.1 精确读取的 Web 技术表示

Web 的本地读取结果不是 05 Helper 返回值，因而不得把自己的成功标为 `mechanically_valid`。实现新增一个只服务 Web 的读取状态闭集：

- `readable`：目标文件已完整读取、载体与请求类型相符、frontmatter/最小身份解析成功，正文可以按返回 carrier 呈现；
- `invalid`：文件或最小身份/载体/解析不成立；可返回预期路径、carrier、问题与请求身份，但不返回可消费正文或领域状态；
- `not_found`、`unavailable`：精确读取未得到目标文件或受 I/O/范围限制；同样只返回预期位置（可安全计算时）、carrier、实际问题和未读取范围。

该状态是 Web 的读取与呈现边界，不是新增事实状态、事实字段或 05 的机械有效性结论。`facts.ts` 的扁平有效详情投影必须同时保留 `canonical_path`、`carrier` 和 `check_status: readable`；失败详情使用明确的 read-failure envelope，而不是把半解析 `fact_object` 当对象详情。前端的 source-path helper 只接受 `canonical_path`，不接受 `path` 的 ID 回退或 `target`。

## 4. 实现顺序与修改点

1. 先调整 `study_markdown.py` 与 Python tests，移除 `_REQUIRED_H3_BY_H2`、固定表头、发现/建议数量及其测试；保留 fenced code 内标题、额外 H2、五段顺序和非空的正反例。同步字段登记基线断言为 122。
2. 更新 `localFactReader.ts` 的 `LocalFactItem`：加入类型派生的 `carrier`，区分 `readable/invalid`；身份缺失、类型/文件名不符、frontmatter/YAML 解析失败和载体错误均不得输出可读对象。`readLocalFact` 为 `not_found/unavailable` 生成仅含读取元数据的失败结果。
3. 更新 `facts.ts`/objects route 的详情映射：有效路径投影包含 `canonical_path`、`carrier`、`check_status`、`read_issues`；无效读取保持 HTTP/API 可观察的 failure envelope，使页面能显示预期位置与实际失败，而不是仅抛出泛化错误。列表仍是候选/摘要，不能把它当作正文/复制路径的来源。
4. 新增 `factReadMeta.ts`，以纯函数从精确详情取得 source path 与 readable carrier。将 `ObjectDetail`、`PanelContent`、关联引用的复制与 object path 统一改用该函数；删除所有 V4 `obj.path || detail.target || objectId` 作为源路径的回退。详情头在有效对象显示类型、状态和 ID。
5. 重构 Study 布局：`STUDY_READING_NODES` 只保留 `research_intent`、`abstract`、`recommendation_summary` 和一个 body entry；`research_question` 仍被过滤，避免作为额外字段重复出现。`StudyReportBodyEntry` 只显示同一正文的进入/复制（可用时）行，不解析/内联 H2；打开 Panel 时传入 canonical path、`data` 和 `carrier: markdown`。
6. 扩展 `PanelContent` 的 doc payload，声明性传递 `carrier`。`DocPreview` 对有 carrier 的内存正文优先按 carrier 渲染，尤其 Markdown；仅对普通独立文档加载保留路径后缀兼容。读取失败不生成 doc payload。对象预览与详情复用 Study 布局及 source-path helper。
7. 同步 `web/docs/04`、`web/docs/10`：删去“研究问题为详情一级节点”“正文 H2 直接展开”“`data.path`/target 回退”“Study 尚未接入”的过时叙述，记录三层 source metadata 与阅读层级。
8. 重新审阅 active `study-0010`。若其正文只有通用谨慎说明、没有由外部比较得出的具体方向/取舍，则在重读实际外部资料后，通过 `read-fact-objects → update-fact-object` 的 CAS 改写为新研究；不直接编辑 Markdown 文件、不改文件名，也不以 UI/测试通过证明研究质量。

## 5. 风险、测试与验收

| 风险 | 主要检查 | 通过边界 |
|---|---|---|
| 旧 parser 继续将研究写成模板 | `test_study_carrier.py` 正反例：五 H2 必须成立，单个强发现、列表式分流和自由 H3 必须可通过 | 只证明 carrier 骨架，不证明研究质量 |
| 新字段登记与 spec 测试漂移 | `test_field_registry.py`、`test_repository.py` 断言 122，并运行 `code/tests/specs` | 只证明当前规则文件的已实现结构检查 |
| 详情/API 丢失 carrier 或以 ID 复制路径 | Web API/纯函数 tests 覆盖 readable metadata、non-path target、无 canonical path、failure envelope | 只证明映射和复制输入，不证明文件本身有效 |
| Markdown 深入阅读又退化为原文本 | Panel doc-format 纯函数/组件 contract test：显式 Markdown carrier 在 path 为 `study-0010` 时仍选择 Markdown；plain document 不受影响 | 只证明渲染选择和代表性结构 |
| Study 正文在主视图重复 | Study layout contract 覆盖三摘要字段、无一级 `research_question`、无内联 H2，且对象预览同源 | 只证明字段次序和入口，不评估正文好坏 |
| 无效读取冒充 active/retired | API/UI contract 覆盖 `invalid/not_found/unavailable`：显示读取状态/预期位置，不显示领域状态、正文或 ID 路径复制 | 只证明失败边界 |
| 其它 V4 对象仍有相同投影缺陷 | 使用 workcase/ADR/Pitfall/Spark/Study representative fixture 覆盖 source-path helper 与 header identity | 只证明已覆盖的五类型投影 |

实施后依次执行：受影响 Python carrier/registry tests、`web` API/contract tests、`npm run check`、`npm run build`、目标 lint、`git diff --check`；再以浏览器回读 v4 `study-0010`，检查详情头、三项摘要、深入阅读的真实 Markdown 表格/标题、复制的 canonical path 和一个失败/缺路径场景。全量 lint 或其它既有失败必须单独列出，不能借本计划掩盖或宣称全绿。

## 6. 非目标、风险余量与完成条件

本增量不迁移 Study 文件名、不批量改写 retired Study、不恢复 V3 旧字段/关系、不增加 Web 写入、不让 Web 调用事实 Helper、不把本地 reader 扩大为完整事实 validator，也不承诺所有历史外部资料仍当前。

只有当来源规格、实现设计文档、Python carrier、Web API/详情/预览和测试映射一致，实际页面满足本计划的可观察验收，且任何 `study-0010` 改写经过受控 CAS 回读后，才能声明该阅读回退已在所检查范围修复。未重研的 v3 主题、外部资料时效、自然语言研究价值和未覆盖的响应式/辅助技术范围必须保留为未验证范围。
