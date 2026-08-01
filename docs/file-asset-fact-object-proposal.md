# FileAsset（文件资产）事实对象方案草案

> 起草时间：2026-07-31
> 状态：Human 已确认事实语义并恢复拟准入方向；尚未形成当前有效事实类型、Schema 或实现
> 目标：为项目内需要长期保留、集中发现和稳定引用的原生文件建立受控承载
> 非目标：本方案不创建 FileAsset 事实对象，不迁移现有 `docs/` 文件，也不声明 Helper、Git Gate 或 Web 已经支持本类型

---

## 一、结论摘要

建议按拟准入方向继续推进第六类事实类型 **FileAsset（文件资产）**，机器键候选为 `file-asset`；正式定义来源继续保持 draft，直到同批规则、登记、实现边界与独立复核闭合。

FileAsset 表达的是一个被纳入项目事实源管理、客观存在的原生文件内容对象。它具有稳定身份、canonical 内容、完整性指纹、纳入签名和受控生命周期，可以被一个或多个事实对象稳定引用；它本身不声明证明力、结论、正确性、当前适用性、采纳状态或行动完成。

本方案要解决的核心问题不是“给 `docs/` 分类”，而是：

1. 日志、截图、审计报告、导出文件和其它原生文件散落在 `docs/` 或临时路径后，可能在普通整理中被随手删除；
2. 路径和文件名不是稳定对象身份，移动、改名或重组目录后引用容易失效；
3. 当前事实对象缺少统一的文件资产引用入口，AI 无法可靠发现“有哪些文件资产”及“哪些对象正在使用它”；
4. 原始文件缺少统一的内容指纹、本次纳入签名、完整性回读和受控归档边界；
5. 后续行动虽然可能保留提炼后的结论，却无法稳定回到形成这些结论时使用的原生材料。

因此，FileAsset 的价值是建立一个**集中登记、可发现、可校验完整性、可稳定引用并可派生反向导航的文件资产管理域**。这里的“受保护”只表示：删除会使对象进入可检测的无效状态，并且在相应 Git Gate 实现后，已暂存的普通删除可在提交前被阻断；它不保证 Working Tree 中的文件无法被本地命令直接删除。

---

## 二、概念定义与边界

### 2.1 定义

FileAsset 是一个需要跨行动、会话、执行者或阶段持续保留，并且需要独立身份、完整性校验、稳定引用或受控生命周期的项目内原生文件资产。

一个 FileAsset 由两部分共同构成：

1. **manifest**：保存事实对象身份、标题、状态、文件元数据、内容指纹和纳入签名；
2. **payload**：实际保存的原生文件字节。

manifest 与 payload 是同一对象不可分割的组成部分。只存在 manifest、payload 缺失、内容指纹不匹配或目录边界不成立时，都不能把该对象作为完整 FileAsset 消费。

### 2.2 与“授权附件”的术语边界

`Attachment / 附件` 已由 `specification-model-foundation` 定义为规范体系中的“授权附件（Authorized Attachment）”，并使用 `specs/attachments/`、`attachment_key`、`attachment_id` 和 `kind: attachment` 等机器身份。本方案不复用这些术语或机器键。

本类型正式名称固定使用 `FileAsset / 文件资产`。面向 Human 的界面或对话可以使用“添加附件”这一动作表达，但必须能够回指实际创建或关联的是 FileAsset；“附件”不得作为本事实类型名称、`fact_type_key`、对象 ID 前缀、canonical 目录或 relation key。

### 2.3 FileAsset 回答什么

- 这个文件资产的稳定身份是什么；
- 当前 canonical 文件是否存在且字节完整；
- 文件的媒体类型、原始名称、字节大小和内容指纹是什么；
- 本次把最终文件 bytes 直接交给受控摄取边界的是 Human，还是哪个实际可观察的 AI agent；
- 它当前是否仍作为默认候选被发现；
- 哪些事实对象通过正向引用使用它（反向结果由 Code 派生）。

### 2.4 FileAsset 不回答什么

- 文件内容是否真实、正确或具有证明力；
- 审计是否通过、结论是否成立或建议是否被采纳；
- Human 是否批准内容或接受风险；
- 生成文件资产内容的工作是否完成；
- 文件与消费对象之间是否存在证据、依赖、贡献或其它业务关系；
- AI 应如何执行审计、研究、设计或验证。

这些判断继续由消费该文件资产的 Spark、WorkCase、ADR、Pitfall、Study、普通稳定文档、适用规则和 Human 决定。

### 2.5 正例

- Human 提供的一份 PDF 审计报告，需要后续 WorkCase 和 ADR 稳定引用；
- AI 按 Human 目标生成的 Markdown 审计报告，需要保留实际报告文件而不只保留结论摘要；
- 一张记录目标环境真实界面状态的截图，需要跨会话保留并被环境接入判断引用；
- 一份命令完整输出、诊断日志或导出的 JSON，需要保留原始字节供后续复核；
- 一个设计 mockup、协议样例或其它无法自然嵌入事实对象字段的原生文件；Human 或 AI 原本提供的压缩包也可以作为单一原生 payload 保存。

### 2.6 反例

- 只服务当前推理、无需跨会话保留的临时输出；
- 能由现有事实对象自然语言字段无损表达、没有独立文件消费价值的简短观察；
- 仅用于重新访问外部资料的 HTTP(S) 地址，继续使用现有 `urls`；
- 为满足模板而保存、没有独立消费价值的逐命令流水；
- 缓存、构建产物、可由当前来源确定性再生成且没有保留必要的中间文件；
- 只因文件重要、体积较大或已有扩展名而要求对象化的普通文档。

---

## 三、与相邻承载方案的比较

| 方案 | 可以解决 | 不能解决或主要风险 | 判断 |
|---|---|---|---|
| 继续放在 `docs/` | Human 可直接阅读，成本最低 | 容易被当作临时材料清理；路径引用不稳定；无统一发现、指纹、签名和生命周期 | 不满足当前保全目标 |
| 新建受保护普通文件目录 | 可集中保存；实现相应规则后，Git Gate 可在提交时阻断删除 | 缺少稳定事实身份、跨类型统一引用、Helper 候选发现、状态和反向导航 | 适合只需要保全、不需要对象语义的场景 |
| 把原始内容内联到现有事实对象 | 结论与材料在同一文件 | 二进制和大文件不适用；复制会造成多份权威；对象正文退化为材料包 | 不采用 |
| FileAsset 事实类型 | 同时提供 canonical 存储、稳定身份、完整性、纳入签名、引用、发现和生命周期 | 需要修改共同事实边界、字段登记、Helper、Git Gate、Code、tests 和 Web | 当前推荐继续设计 |

新增类型的必要性不只来自“防止删除”，还来自以下组合需求：稳定对象 ID、跨事实引用、Helper 发现、内容完整性、纳入签名、受控归档和反向导航。若最终只保留“防止删除”一个需求，应退回受保护普通文件目录，不准入新类型。

最强反对意见是：当前问题首先是文件保全问题，一个受控文件目录加机械完整性检查可能已经足够，不必扩张事实模型。只有真实试点证明稳定 ID、跨对象引用、Helper 发现、生命周期和反向导航都是持续需求，且普通目录不能自然承接时，FileAsset 才有资格成为第六事实类型。

### 3.1 `05 §6.1` 七项准入审计现状

> 历史快照：本小节记录首次 formal draft 与 Human 事实语义澄清之前的判断，不是当前准入结论；当前判断以 §23 为准。

| 准入条件 | 当前判断 | 仍需完成 |
|---|---|---|
| 1. 是否需要跨会话持续保留 | 已有 Human 目标与审计、截图、日志等例子支持 | 用试点确认不是一次性文件整理需求 |
| 2. 是否需要对象化 | 在稳定 ID、跨对象引用、发现、生命周期均成立时支持 | 证明受控普通目录不足以承接组合需求 |
| 3. 语义与对象边界是否稳定 | 部分设计 | 用重复字节、来源漂移、崩溃残留和归档场景验证 |
| 4. 是否完成替代方案比较 | 已形成初步比较 | 以试点数据比较普通目录、内联和事实类型 |
| 5. 是否存在唯一正式定义来源 | 尚未成立 | 准入后由候选 `specs/25-FileAsset-文件资产.md` 承担，不能由本文承担 |
| 6. V1–V8 净价值是否成立 | 当时尚未证明 | 计算规范、实现、迁移、运行和维护成本，并完成独立复核 |
| 7. 术语与治理是否闭合 | 部分成立 | 已与规范“授权附件”消歧；仍需完成字段登记、关系模型和 Human Gate 治理 |

因此，本方案在当时只能用于候选讨论；该历史判断已由 §23 的拟准入恢复取代，仍不得据此跳过 activation 条件直接进入正式实现。

---

## 四、对象粒度与 canonical 承载

### 4.1 对象粒度

初版采用**一个 FileAsset 对象对应一个原生 payload 文件**。

多个文件即使来自同一次审计或同一轮验证，也分别形成 FileAsset；由消费方分别引用，或者由一个报告文件资产在正文中说明其它文件资产的稳定引用。初版不建立多文件 bundle，系统也不得为了绕过“一对象一 payload”而主动把多个文件打包为压缩包。若 Human 或 AI 原本提供的文件就是压缩包，它仍是一个原生 payload，但对象只承诺保存该压缩包字节，不把包内成员自动提升为文件资产对象。

重复字节不自动决定对象是否相同：

- 内容哈希只证明字节相同，不证明对象语义、纳入签名或使用边界相同；
- 相同字节、相同纳入签名且服务同一独立用途时，创建方应优先建议复用既有 FileAsset，但不得由 Code 自动合并；
- 相同字节由不同主体在不同摄取动作中直接提交，或需要保留不同纳入责任时，可以形成不同 FileAsset；
- 是否复用是基于实际来源和消费边界的语义判断，不能只比较 SHA-256。

### 4.2 推荐目录

```text
ldvh-base/
└── file-assets/
    └── file-asset-0001/
        ├── file-asset.yaml
        └── payload
```

约束建议：

- `object_id` 匹配 `file-asset-[0-9]{4,}`；
- 对象目录名必须与 `object_id` 完全一致；
- manifest 文件名固定为 `file-asset.yaml`；
- payload 文件名固定为 `payload`，原始文件名和媒体类型保存在 manifest，避免路径由用户输入决定；下载或预览界面可使用 manifest 中的原始文件名，直接依赖 OS 通过 canonical 文件名预览不属于初版设计条件；
- 对象目录只能包含上述两个普通文件；不得包含 symlink、目录、设备文件、socket 或其它成员；
- payload 可以是文本或二进制，但必须是 Git Working Tree 中的真实普通文件；
- 创建时必须把来源字节复制进入该 canonical 目录，不能继续指向 `docs/`、会话目录、下载目录或外部临时路径；
- 创建前记录来源文件身份与初始指纹，在受控 staging 中边复制边计算哈希，并在提交前重新检查来源身份和内容；若复制期间来源漂移，不形成 canonical 对象并报告失败；
- staging 必须位于 canonical 候选命名空间之外；只有 manifest、payload 和全部机械检查通过后，才能以目录原子重命名进入 canonical 位置；
- manifest 与 payload 必须由同一受控事务形成并完成写后回读；不得先留下孤立 manifest 或孤立 payload；崩溃残留不得被发现为候选，只有能证明属于未完成事务时才可安全清理，归属不明时必须报告而非静默删除。

目录载体与当前五类“一文件一对象”的实现不同，属于需要明确实现和验证的新 carrier，不得让 Code 根据目录形状自行推导语义。

---

## 五、候选字段模型

以下只说明信息需求和候选 shape，不构成正式字段登记。全部字段仍需按 `fact-model-foundation` 完成全局字段与结构查重、唯一登记、类型绑定和独立复核。

### 5.1 manifest 示例

```yaml
object_id: file-asset-0001
fact_type_key: file-asset
title: Codex Desktop cold-start 审计报告
status: active
created_at: "2026-07-31T14:00:00+08:00"
updated_at: "2026-07-31T14:00:00+08:00"

filename: codex-desktop-cold-start-audit.md
media_type: text/markdown
size_bytes: 18342
content_sha256: 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef

signature:
  signer_type: ai-agent
  agent_id: codex
  host_environment: Codex Desktop
```

### 5.2 公共字段

FileAsset 继承当前全部事实对象的公共必填字段：

- `object_id`
- `fact_type_key`
- `title`
- `created_at`
- `updated_at`
- `status`（若最终状态模型成立）

`urls` 默认禁止；外部地址不是已捕获的项目内文件资产。`relations` 只在 FileAsset 自身确有派生或替代业务关系时按类型来源定义，不用于保存“被哪些对象引用”。

### 5.3 FileAsset 专属信息需求

| 候选字段 | 回答的问题 | 明确不表示 |
|---|---|---|
| `filename` | Human 直接提供或 AI agent 代表自身提交 payload 时实际使用的可读文件名是什么 | canonical 路径、历史原名、作者命名或稳定身份 |
| `media_type` | payload 被声明或推导为何种 IANA media type | 内容正确、无恶意、可安全执行或 Code 已证明真实格式 |
| `size_bytes` | 当前 canonical payload 的精确字节数 | 大小限制已经满足 |
| `content_sha256` | 当前 canonical payload 的字节身份是什么 | 来源真实、内容正确或密码学签名 |
| `signature` | 本次把最终 canonical bytes 直接交给受控摄取边界的是 Human，还是哪个可观察的 AI agent | Human 批准、授权、验收、历史作者、原始生成者、来源真实性证明或内容证明力 |

canonical payload 路径由 `object_id` 和类型来源机械派生，不在对象中保存可漂移的 `path` 字段。

### 5.4 纳入签名（Signature）

本类型中的 `signature` 是**本次纳入责任签名**，不是密码学签名，也不表达历史作者、原始生成者、触发者、授权者或批准者。它只回答“本次是谁把最终 bytes 直接交给受控摄取边界”，并只允许两种情况：

1. Human 直接提供最终 payload，AI 只原样复制进入 canonical 位置：签名为 `human`；
2. 否则，由实际生成、修改、捕获、导出、下载、选择或提交最终 bytes 的可观察 AI agent 签 `ai-agent`。即使由 Human 要求 AI 完成该动作，仍签实际代表自身提交的 AI agent。

候选结构：

```yaml
signature:
  signer_type: human
```

```yaml
signature:
  signer_type: ai-agent
  agent_id: codex
  host_environment: Codex Desktop
```

签名纪律：

- `signer_type` 闭集为 `human`、`ai-agent`；
- Human 分支只记录 `signer_type: human`，不要求或推断个人标识，也不记录代为存储的 AI；
- AI 分支必须写本次实际代表自身提交最终 bytes 的可观察 `agent_id`；`host_environment` 对 AI 必填；
- AI 不得签 Human，也不得为不可观察的其它 agent 或环境代签；
- AI 只把 Human 文件原样复制进入 canonical 位置时，签名仍是 Human；
- AI 对 Human 文件作任何实质内容修改时，必须形成新的 FileAsset，签名改为实际修改内容的 AI agent；
- 签名在对象创建后不可原地改变；发现归属错误时通过更正或替代流程处理，不能静默重签；
- 历史文件、混合生成内容或来源不明材料若不能明确归入“Human 直接提供最终 bytes”或“当前可观察 AI agent 代表自身提交最终 bytes”之一，必须停止创建或迁移，直到形成一次提交主体明确的摄取动作；
- Code 只能校验闭集、条件字段、字节复制与 canonical 内容一致性，不能证明 Human 或 AI 归属陈述真实；
- 签名是来源归属记录，不是密码学证明；它不替代 `content_sha256`，也不等于 Human Gate、授权 receipt、验收或数字签名。

---

## 六、文件资产引用模型

### 6.1 初版正向引用

初版不新增共同字段，复用当前事实模型的 `relations`。引用由消费对象正向保存，FileAsset 不维护 `referenced_by`。

候选 shape：

```yaml
relations:
  - relation_key: has-file-asset
    target:
      governed_project_id: ldvh
      fact_type_key: file-asset
      object_id: file-asset-0001
```

语义边界：

- `target` 使用稳定事实三元组，不保存路径或标题副本；
- `has-file-asset` 只表示消费对象持有一个文件资产资源引用，不自动提升为 `depends-on`、`informed-by`、`evidence-for` 或其它业务关系；
- Spark、WorkCase、ADR、Pitfall、Study 等每个允许引用文件资产的类型，都必须在自己的正式类型来源中显式定义 `has-file-asset`，包括目标类型固定为 `file-asset`、基数、终态和目标缺失时的规则；实现不得因存在 FileAsset 就默认全部类型可用；
- 该文件资产在当前对象中的实际用途，写入消费对象已有的适当自然语言字段或正文；当前闭集 relation 结构不为此临时增加 `usage_summary`；
- 同一消费对象不得重复建立指向同一 FileAsset 的 `has-file-asset`；
- 引用成立前必须精确读取目标 manifest，并验证 payload 存在、哈希一致且状态允许当前消费；
- 只有真实试点证明 `relations + 消费对象正文` 不能自然表达文件资产资源引用时，才可以按完整字段准入与 Human Gate 另行提议专用 `file_asset_refs` 字段；本方案不预先引入该字段。

### 6.2 反向导航

“哪些对象引用当前 FileAsset”只由 Code 根据当前事实对象的正向 `relations: has-file-asset` 派生：

- 不写入 `referenced_by`；
- 反向结果不是第二事实源；
- 派生范围、未扫描类型、无效对象和缺失引用必须可见；
- 没有发现引用不自动证明无人使用，也不自动触发归档或删除。

### 6.3 普通稳定文档引用

普通稳定文档需要引用 FileAsset 时，应保留完整稳定三元组，必要时同时提供由当前 Working Tree 派生的可点击路径。路径只用于打开当前载体，不替代稳定引用。

是否建立专用 Markdown 引用语法或 Helper 渲染能力属于后续实现设计，不由本候选方案预先发明。

---

## 七、生命周期与不可变边界

### 7.1 建议状态

初版候选状态：

| 状态 | 语义 | 默认发现 |
|---|---|---|
| `active` | 在对象通过当次机械完整性检查时，作为默认文件资产候选 | 是 |
| `archived` | 从默认候选中排除，但仍可被精确读取和历史引用 | 否 |

状态本身不证明 payload 存在、完整或安全；这些是每次读取时单独验证的机械条件。初始状态只能是 `active`。正常转换只允许 `active → archived`。是否允许恢复、替代或增加终态，需要在正式类型来源中重新判断；本方案不预设自动恢复。

### 7.2 payload 不可变

- 创建成功后，payload 字节不可原地更新；
- 内容变化必须创建新的 FileAsset；
- 原文件资产继续保留其真实历史内容；
- 新旧对象确需表达派生或替代关系时，由 FileAsset 类型来源定义正向关系，不通过文件覆盖或复用对象 ID 实现；
- 标题、原始文件名或签名变化若实质改变内容身份，同样不得伪装成普通元数据更新。

### 7.3 归档与删除

- 无人引用不等于应归档；
- 归档必须基于实际使用边界和保留价值作出语义判断；
- `archived` 不等于删除，payload 仍保留在当前 Working Tree；
- 初版正常生命周期**不支持物理删除 FileAsset**；一旦本地删除，机械检查应把对象报告为缺失或无效，已暂存删除在相应 Git Gate 实现后应被提交前阻断，但这不能阻止 Working Tree 中发生原始删除操作；
- 涉及敏感信息、许可问题、法律要求或明确类型退出而必须物理删除时，初版没有可用例外路径，必须停止并取得 Human 决定，再单独设计可审计的一次性移除能力、入向引用处置与恢复边界；Code 或 Git Gate 不得仅凭“可能经过 Human Gate”自行推断允许删除；
- Git history 只提供历史锚点，不代替当前 payload，也不能作为“删除后仍然安全”的理由。

---

## 八、审计报告示例

### 8.1 Human 提供审计报告

Human 上传 `security-audit.pdf`，AI 只负责受控存储：

1. payload 原样复制进入新的 FileAsset 目录；
2. `signature.signer_type = human`；
3. Human 分支不要求个人标识，也不把代为存储的 AI 写入签名；
4. Code 计算大小和 SHA-256；媒体类型按正式来源规则声明或推导，并且不作为安全渲染依据；
5. 后续 ADR 或 WorkCase 通过正式类型来源允许的 `relations: has-file-asset` 引用该稳定对象。

### 8.2 Human 要求 AI 编写审计报告

Human 要求 Codex 编写一份审计报告，AI 生成 `audit.md`：

1. 审计目标、方法、检查范围和结论仍由适用审计规则、行动模板和 Human 目标约束；
2. 完成的 `audit.md` 作为 payload 进入新的 FileAsset；
3. `signature.signer_type = ai-agent`；
4. `signature.agent_id = codex`，并记录实际宿主环境；
5. FileAsset 只负责保存报告文件和纳入签名，不把“已保存”写成“审计通过”；
6. 后续事实对象引用报告时，自行说明该报告对当前判断的实际用途和边界。

### 8.3 AI 修改 Human 报告

AI 对 Human 提供的 PDF 或 Markdown 做实质修改：

1. 原 Human FileAsset 保持不变；
2. 修改后的文件创建为新的 FileAsset；
3. 新对象签实际修改内容的 AI agent；
4. 需要时通过类型来源允许的 `derived-from` 关系指向原 FileAsset；
5. 不复用原 ID，不改变原签名，不覆盖原 payload。

---

## 九、Helper 与受控操作需求

FileAsset 具有多文件 carrier 和原始字节输入，不能直接假定当前 `create-fact-object` 的单文件 JSON/YAML 写入事务已经适用。正式设计至少需要覆盖：

1. **候选发现**：F1 能形成完整对象清单；F2 投影标题、状态、媒体类型、大小、签名主体和更新时间，不展开 payload；
2. **精确读取**：读取 manifest，机械验证目录闭集、payload 类型、大小和哈希，并返回可回指的 canonical 内容入口；
3. **受控创建**：安全读取 Human 或 AI 已选择的来源文件，记录来源身份与初始指纹，将字节复制到 canonical 命名空间之外的受控 staging，复制后重检来源漂移，分配身份、生成 manifest、计算指纹并原子形成对象目录；
4. **引用检查**：解析各类型正式定义的 `relations: has-file-asset`，验证目标和 payload 完整性，形成有范围说明的反向导航；
5. **生命周期变更**：只允许来源定义的 manifest 状态变化，不允许通过普通更新替换 payload；
6. **冲突与回滚**：处理来源文件漂移、目标 ID 并发、磁盘失败、部分写入、哈希不一致、写后回读失败和对象目录残留；
7. **资源边界**：报告实际文件大小上限、超限和读取能力缺口，不通过截断后声明完整；
8. **内容交付**：二进制 payload 不应无界内联进 Helper JSON；读取结果应提供受控内容入口及元数据，具体传输方式由 04 和目标环境能力定义。

应优先评估扩展现有跨类型操作是否仍能保持清楚契约；若二进制输入和多文件原子性不能自然承接，再建立 FileAsset 专属操作。不得仅因实现方便复制整套发现、读取或生命周期语义。

---

## 十、机械完整性与 Git Gate

### 10.1 创建和读取时检查

- canonical 目录、manifest 和 payload 精确存在；
- 对象目录没有未知成员；
- 全部载体均为普通文件且不经过 symlink；
- `object_id`、目录名、`fact_type_key` 和 manifest 身份一致；
- payload 实际字节数等于 `size_bytes`；
- payload SHA-256 等于 `content_sha256`；
- `media_type` 的字段 shape、签名结构和状态满足类型来源；不得把媒体类型校验表述为已证明真实格式或安全性；
- `relations: has-file-asset` 满足各消费类型来源，其目标存在、完整且引用结构闭合；
- 当前 Working Tree 与当次管辖项目、实际 worktree 绑定。

### 10.2 Git Gate 目标

在 FileAsset 能被称为“提交边界受保护”之前，Git Gate 必须实际实现并验证：

- 新增或修改对象时验证 manifest/payload 完整性；
- 阻止 payload 原地变化、manifest/payload 单边新增或单边删除；
- 阻止任意 FileAsset 目录被普通 commit 删除或移动；初版不提供由 Gate 猜测的例外删除分支；
- 阻止新建悬空或类型来源未允许的 `has-file-asset` relation；
- 对不能完整扫描的类型或引用范围明确阻断或报告未完成，不静默放行；
- Helper 主动预检和真实 Git 事件 Gate 使用同一检查核心。

当前 `spark-0039` 已记录 Git Gate 尚不校验事实对象内容。因此，在相应实现和真实事件验证完成前，只能说 FileAsset 方案要求在提交边界阻断删除，不能说当前 Gate 已经提供该保护。即使实现完成，该保证也只覆盖已接入并实测的 Git 事件，不阻止本地 Working Tree 删除；本地删除只能被后续检查发现。

---

## 十一、安全、隐私与资源边界

- AI 不得因为文件可读取就自动把它纳入 FileAsset；创建仍需 Human 当前授权或准确覆盖的 WorkCase 授权；
- 来源文件疑似包含密码、token、私钥、个人敏感信息、许可受限材料或不应进入 Git 的内容时，暂停创建并进入适用 Human Gate；
- Code 负责路径规范化、目录逃逸、symlink、文件类型、大小、哈希和原子 I/O；媒体类型只能按正式来源规则声明或推导，Code 无法对所有格式证明其语义真实性；Code 也不得根据文件内容自动判断语义价值、敏感性或许可；
- 初版不以“1 MB”或“50 MB”等未经来源论证的数字作为语义规则；实现必须定义确定性资源上限，并把超限作为未完成范围如实交还；
- 可执行文件、压缩包、HTML、SVG 或其它主动内容即使进入 FileAsset，也只表示字节被保存，不表示可以安全执行或渲染；
- Web 或环境预览不得信任 manifest 的媒体类型作为安全边界；必须结合内容检查与安全策略决定下载、文本显示、沙箱预览或拒绝，不得因对象机械有效就直接执行或渲染内容。

---

## 十二、规范与实现影响面

### 12.1 规则源候选变更

1. 新建 FileAsset 唯一定义来源候选，例如 `specs/25-FileAsset-文件资产.md`；
2. 修改 `specs/05-事实模型基础规范.md`：
   - 完成第六类型准入；
   - 扩展 canonical 拓扑；
   - 明确 FileAsset 对原生 payload、目录 carrier 和资源引用的共同边界例外或新基线；
3. 修改 `05.Att.01`：登记 FileAsset 结构、字段和签名条件结构；初版不新增 `file_asset_refs` foundation 字段；
4. 修改 `05.Att.02`：登记目录 carrier、payload 完整性、签名、引用、不可变和提交边界删除阻断机械规则；
5. 评估 20–24：哪些现有类型需要显式定义 `has-file-asset` relation 及其基数、终态和目标缺失规则，不得由实现默认全部启用；
6. 修改 31/32：纳入 FileAsset 创建、不可变 payload 和归档边界；若文件摄取具有独立稳定行动结构，再按 06 判断是否需要专属行动模板；
7. 评估 03：原生文件来源、内容指纹、当前 Working Tree 和历史边界是否需要精确化；
8. 评估 08 与 Web 文件资产：列表、详情、下载/预览、反向引用和无效对象呈现；
9. 薄 Skill 不增加 FileAsset 业务指引，继续只路由到 Helper 和当前规则源。

### 12.2 Code 与测试候选变更

- 类型与 carrier 投影；
- 目录安全扫描和 manifest parser；
- Schema、状态和签名 validator；
- payload 哈希、大小计算和媒体类型元数据处理；
- 多文件 staging、原子创建、回读和故障回滚；
- F0/F1/F2/F3 发现与读取；
- `relations: has-file-asset` 正向校验和反向索引；
- 生命周期变更与 payload 不可变检查；
- fact integrity 与 Git Gate 同核；
- Web API、下载与安全预览；
- 正反例、路径攻击、symlink、超限、并发、部分写入和真实 Git 事件测试。

---

## 十三、迁移策略

现有 `docs/` 内容不得批量自动升级为 FileAsset。迁移按对象逐项判断：

1. 盘点候选原生文件及其当前消费者；
2. 排除临时输出、可再生成缓存、无独立消费价值和已有自然承载位置的内容；
3. 对确需保留的文件确定本次最终 canonical bytes 是由 Human 直接提供，还是由当前可观察 AI agent 代表自身提交；无法确认直接提交主体时停止迁移，直到 Human 重新直接提供确定 bytes，或一个可观察 AI agent 重新取得并提交；
4. 经受控入口复制到新 FileAsset，生成内容指纹并回读；
5. 在真实消费对象中建立其类型来源允许的正向 `relations: has-file-asset`；
6. 验证反向导航和 payload 完整性；
7. 原 `docs/` 文件在 FileAsset 和全部引用完成验证前保持不动；
8. 原路径后续是否删除、保留说明页或建立迁移提示，由 Human 根据实际引用和历史价值决定，不由迁移工具自动清理。

优先试点建议：选择一份 Human 提供的原生文件和一份 Human 要求 AI 编写的 Markdown 审计报告，分别验证两类签名记录、创建、引用、反向导航、归档和 Git Gate 对已暂存删除的阻断。

---

## 十四、分阶段交付建议

### 阶段 A：准入与独立复核

- 完成 05 §6.1 七项准入审计；
- 比较受保护普通文件目录与 FileAsset 类型；
- 确认一对象一 payload、目录 carrier、签名两分类和引用入口；
- 完成字段/结构全局查重和独立方案复核；
- 由 Human 决定共同事实边界、迁移负担和各消费类型新增 relation key 的长期成本。

### 阶段 B：规则与投影

- 起草 25；
- 同批修改 05、05.Att.01、05.Att.02 及受影响类型来源；
- 形成可机械派生的 carrier、Schema、状态、引用和验证合同；
- 保持候选 `draft`，直到来源资格和验证要求成立。

### 阶段 C：最小只读纵切

- 先实现目录扫描、manifest/payload 精确读取、完整性校验和候选发现；
- 对手工 fixture 验证有效、缺失、哈希不符、symlink、未知成员和超限场景；
- 不在只读闭环成立前开放创建或迁移。

### 阶段 D：受控创建与引用

- 实现安全摄取、身份分配、多文件原子创建和写后回读；
- 实现各类型正式定义的 `relations: has-file-asset` 正向校验与反向导航；
- 覆盖 Human 与 AI agent 两类签名；
- 使用两类试点文件资产做端到端验证。

### 阶段 E：生命周期、Git Gate 与消费面

- 实现 `active → archived`；
- 实现 payload 不可变和 Git 提交边界的目录删除阻断；
- 将同核检查接入 Helper 预检与真实 Git Gate；
- 增加 Web 下载/预览和无效对象呈现；
- 完成真实 Git allow/block 事件验证后，才声明受保护闭环成立。

---

## 十五、验收条件

方案进入实现前至少应满足：

1. FileAsset 与普通稳定文件、现有五类事实对象、规范授权附件及外部 URL 的边界没有实质歧义；
2. 已证明当前目标同时需要稳定身份、引用、发现、完整性和生命周期，而不只是新目录；
3. 一对象一 payload 和目录 carrier 的身份、当前位置与原子边界清楚；
4. Human / AI agent 两类签名语义完整，且不冒充批准、授权或证明力；
5. `has-file-asset` 与现有 relation keys、`urls` 完成全局语义查重；只有试点证明现有关系承载不足时，才重新评估新字段；
6. payload 不可变、归档、物理删除和敏感内容边界清楚；
7. Helper、Code、Git Gate、Web 和测试影响没有被缩写为“支持查询和创建”；
8. 至少一名独立 Reviewer 已检查准入、对象粒度、字段、引用、安全、生命周期和迁移，并由主执行者逐项处置反馈；
9. Human 已决定是否接受修改共同事实边界和各消费类型新增 relation key 带来的长期维护成本。

实现完成后才可进一步验收：

1. Human 提供文件和 AI agent 生成文件均能受控创建为 FileAsset，并按当次已知来源记录对应签名结构；
2. manifest/payload 单边缺失、哈希错误、原地修改、symlink 和目录逃逸均被拒绝；
3. 后续事实对象可稳定引用 FileAsset，并可派生反向导航；
4. active 或 archived FileAsset 的已暂存普通删除均被真实 Git 提交事件阻断，同时如实说明本地 Working Tree 删除只能被发现、不能被 Gate 预防；
5. Helper 主动预检与 Git Gate 使用同一机械检查核心；
6. 全部声明只覆盖实际验证的文件类型、大小、环境、入口和事件范围。

---

## 十六、待 Human 决定

1. 是否确认“集中处理”包括稳定 ID、跨事实引用、Helper 发现、纳入签名、生命周期与提交边界删除阻断，从而继续按第六事实类型推进；
2. 是否接受新增目录 carrier，以及由各消费类型显式定义跨类型 `has-file-asset` relation 所造成的共同模型变更；
3. 初版是否坚持一对象一 payload，暂不支持 bundle；
4. 是否接受初版正常生命周期只允许归档，敏感或法律删除没有默认例外路径，必须暂停并另行设计；
5. AI agent 签名中的可观察身份应使用环境提供的哪个 agent 标识，宿主环境字段如何取得；这些字段只能机械校验结构，不能证明归属真实；
6. 是否以一份 Human 提供文件和一份 AI 生成审计报告作为首轮试点。

---

## 十七、当前已知边界

- 本文只是普通候选方案，不是 `file-asset` 类型定义来源；
- 当前 Helper 仍只发现和处理五类正式事实对象；
- 当前 Git Gate 尚未提供本方案要求的事实对象检查与 FileAsset 提交边界删除阻断；
- 当前 `05` 对命令、日志、文件路径和材料包进入事实对象有明确限制，FileAsset 若准入必须正面处理共同边界，不能靠类型专属字段静默绕过；
- 当前没有 `has-file-asset` 正式 relation key、目录 carrier、文件资产原子创建或二进制内容交付合同；初版也不提议新增 `file_asset_refs` 字段；
- 薄 Skill 不因本方案出现而增加类型正文、字段清单或具体操作说明；
- 任何候选目录、字段、状态、Helper 操作和实现步骤，在相应规则进入当前规则源且实际实现验证前均不得表述为已支持。

---

## 十八、独立审核结论与处置

Subagent 独立审核结论为：**有条件接受作为候选方案，不接受直接进入实现**。审核认为集中保管和稳定引用的需求真实，但 `05 §6.1` 的七项类型准入尚未闭合。该审核发生在候选类型仍使用 `Attachment` 名称时；本次只完成术语和对应机器身份迁移，不改变审核所针对的对象语义及其余处置结论。

| 审核意见 | 本版处置 |
|---|---|
| 纳入签名真实性不能由 Code 机械证明，Human 分支不应额外要求个人 ID | 改为 Human / AI agent 条件结构；Human 只记 `human`；明确签名是归属记录而非证明，并增加提交主体不明时的停止条件 |
| 新建专用文件资产引用字段与当前统一 `relations` 模型冲突 | 初版改用各消费类型显式定义的 `relations: has-file-asset`；只有试点证明不足时才重新提议新字段 |
| “不会误删”和“禁止删除”超过 Git Gate 实际能力 | 限定为完整性检查可发现本地删除、Git Gate 可阻断已暂存删除；不宣称阻止 Working Tree 操作 |
| 对象 carrier 缺少重复字节、来源漂移与崩溃残留边界 | 增加不自动去重、staging、复制前后检查、原子目录提交和残留处置规则 |
| 状态、MIME 与机械完整性或安全性混在一起 | 将状态限定为默认发现策略；完整性每次单独检查；MIME 不作为真实格式或安全渲染证明 |

这些处置只提升了候选方案完整度，不等于审核人或 Human 已接受第六事实类型准入。

---

## 十九、首轮非 canonical 准入试点

### 19.1 试点性质与样本

本试点于 2026-07-31 在 `/tmp/ldvh-file-asset-pilot.tzC5DO` 执行，只验证候选 carrier、字节一致性、两类签名 shape 和关系目标 shape。试点目录不在 `ldvh-base/`，不进入事实源，不预留对象 ID，也不表示 Helper、Schema、Git Gate 或正式类型已经支持 FileAsset。

| 候选 ID（仅试点） | 原始文件 | 纳入签名 | 字节数 | SHA-256 |
|---|---|---|---:|---|
| `file-asset-0001` | `docs/跨环境接入分析汇总报告-2026-07-30.md` | `human` | 9271 | `58b4a1a5b84ff7470c974b2a16b7beea28b916253762401664ed67b2a1a171b0` |
| `file-asset-0002` | `docs/ldvh-environment-hook-claim-audit-2026-07-31.md` | `ai-agent`：`codex` / `Codex Desktop` | 11124 | `57ca7ee0c5f006a0736b618fdc526a55e21d0f3ff068de10e7043b6090b6f8ac` |

Human 在当前对话中明确把第一份文件指定为外部提供的试点文档，因此按本方案的二分类记录为 `human`；该签名只表示最终字节由 Human 提供给当前系统，不进一步断言文件最初作者身份。第二份审计由 Human 当次要求当前 Codex agent 编写，因此记录实际 AI agent。

### 19.2 实际执行与结果

1. 对两个来源文件分别计算大小和 SHA-256；复制进入各自独立 staging 后重新计算，字节数和摘要均完全一致。
2. staging 位于 canonical 候选命名空间之外；每个对象目录只包含 `file-asset.yaml` 与 `payload` 两个普通文件，没有 symlink 或未知成员。
3. manifest 的 `object_id` 与目录名一致，`fact_type_key` 固定为 `file-asset`；payload 大小与 SHA-256 均与 manifest 一致。
4. Human manifest 只含 `signature.signer_type: human`；AI manifest 含 `signer_type: ai-agent`、`agent_id: codex` 和 `host_environment: Codex Desktop`。两种条件 shape 检查均通过。
5. 在全部检查通过后，将两个 staging 目录分别重命名为 `file-asset-0001`、`file-asset-0002`；试点观察到完整目录一次出现，没有先把孤立 manifest 或 payload 放进候选位置。
6. 另建非事实源 relation shape，同时以 `relations: has-file-asset` 指向两个稳定三元组；relation key、项目 ID、目标类型、目标唯一性和目标目录存在检查均通过。
7. 复制完成后再次读取原始来源，两份来源 SHA-256 均未变化；本轮没有命中来源漂移分支。

机械检查结果：两个候选的 `members_closed`、`regular_files`、`identity_matches`、`size_matches`、`sha256_matches` 和 `signature_shape_valid` 均为 `true`；关系模拟的 `relation_keys_valid`、`project_ids_valid`、`target_types_valid`、`targets_unique` 和 `targets_exist` 均为 `true`。

### 19.3 审计样本带来的语义观察

Human 样本记录的是 2026-07-30 的跨环境接入分析，其中仍把 Plugin SessionStart Hook 作为接入方向。AI 样本对 2026-07-31 当前 Working Tree 审计后的结论是：当前正式规则源和发行接入面已经排除环境 Hook、插件或 adapter 接入层，但旧 `docs/`、Hook 风格核心输入和外部环境仍需分开表达。

这组样本证明 FileAsset 可以同时保留“历史原始材料”和“当前复核报告”的稳定字节与不同纳入签名；也证明 FileAsset 本身不能决定哪个结论当前适用，消费对象仍必须说明时间、用途、当前规则依据和被取代范围。

### 19.4 本轮没有验证的范围

- 没有创建 canonical FileAsset，也没有修改任何正式事实对象；
- 当前 Helper 仍不认识 `file-asset`，本轮检查是试点脚本与人工语义审核，不是正式 validator；
- `has-file-asset` 尚未进入任何消费类型来源，关系模拟不是有效事实关系；
- 未执行来源复制中途漂移、并发 ID、磁盘失败、崩溃残留、归档和物理删除反例；
- 未验证 Git Gate 对 FileAsset 新增、修改或已暂存删除的 allow/block；
- 未比较大文件、二进制文件、恶意主动内容或资源上限。

试点结束后应删除 `/tmp/ldvh-file-asset-pilot.tzC5DO`；该临时目录不是交付物，试点依据由本节记录的输入身份、摘要、实际检查与未完成范围承担。

### 19.5 对准入判断的影响

1. “跨行动持续保留”得到两个真实文件样本支持。
2. “纳入签名两分类”和“一对象一 payload”在当前两个 Markdown 样本上可行。
3. 稳定引用可以避免消费方继续依赖 `docs/` 路径，但关系的正式语义与消费者仍未准入。
4. 历史报告与当前复核报告的并存显示纳入签名、时间切片和稳定回读具有消费价值；同时也暴露 FileAsset 不负责内容当前性判断。
5. 本轮仍不能单独证明事实类型优于“受控普通文件目录”，也不能完成 §6.1 的唯一定义来源、V1–V8 净价值和治理条件。

---

## 二十、正式 draft 的独立复核与主执行者处置

> 历史快照：本节记录 Human 澄清“客观存在的内容事实”之前的首次 formal draft 复核。其 carrier、签名、引用和安全 findings 继续保留；关于类型必要性和“必须产生普通资产库无法取得的领域结论”的判断已由 §23 修正。

2026-07-31，主执行者起草 `specs/25-FileAsset-文件资产.md`（`status: draft`）后，交由此前主张“受保护普通资产库可能是更小方案”的独立 subagent 复核。Reviewer 结论为：**有条件接受未生效设计草案；拒绝当前转为 `active`，也不认为第六类型和独立规范必要性已经证明。** Reviewer 未修改文件。

| 独立复核 finding | 主执行者处置 |
|---|---|
| raw 截图、日志、诊断和导出 bytes 作为 FileAsset payload 与 05 §7.2.1 的共同边界冲突 | 在 25 §7 与 §9 增加 activation blocker：05 必须只为 FileAsset 专属 payload carrier 建立窄例外，同时继续禁止命令、路径、日志文字、会话定位进入 manifest 和其它事实字段；该共同边界未完成前不能创建正式对象 |
| 普通文档三元组没有唯一可解析语法，不能证明删除和类型退出的完整入向引用闭包；跨项目关系也无法闭合 | 初版 `has-file-asset` 限制为同一管辖项目；普通文档文字只作导航提示，不属于受保护引用闭包；未来需先定义共同机器语法才能取得完整性保证；普通文档使用仍可能存在时，不得以“引用已清空”为由物理删除 |
| Human 分支回答“谁提供”，AI 分支回答“谁生成/修改”，两支语义不对称，也覆盖不了工具日志、截图和下载文件 | 保留 Human 明确要求的两分类，但统一为“谁把最终 bytes 直接交给受控摄取边界承担本次签名责任”：Human 直接提供为 `human`；否则由实际生成、修改、捕获、导出、下载、选择或提交 bytes 的 AI agent 签 `ai-agent`。它不是历史作者或原始生成者；工具/系统不另成第三 signer |
| 受保护普通资产库仍未被排除，relation shape 试点不证明真实事实关系消费 | 25 §1、§4、§9 明确保持未通过：转 active 前必须有至少一个跨后续行动的真实消费者，对比普通资产库，证明事实关系、F1/F2 类型发现或状态消费具有不可替代价值；若不能证明则取消候选类型 |
| FileAsset 快照与可编辑 Markdown、Study 或其它语义来源可能形成双重权威 | 25 §4 明确：当前语义继续由正确的普通文档或事实类型承担；只有精确不可变 bytes / 原始格式有独立价值时才额外形成 FileAsset，并由消费方说明使用的是快照还是当前语义来源 |
| `original_filename` 对 AI 内存生成内容可能是伪造字段；agent ID 只能是自报标签 | 候选字段改为 `filename`：Human 使用所提供 basename，AI 使用实际生成/捕获/导出/提交文件的 basename，内存 bytes 先明确物化；`agent_id` 明确只是当次可观察自报标签，不表示全局稳定身份 |
| draft 使用 provisional 编号和 key，但不能用它们反向证明独立责任 | 25 状态说明明确标题、key、编号和路径只是 draft 复核定位；更小方案成立时取消候选，不因已经编号而保留 |

本轮独立复核确认的良好边界包括：draft 未占用正式类型解析入口；目录 carrier 的成员闭集、symlink、size/hash、no-overwrite 原子思路基本闭合；payload 与签名等不可变；`referenced_by` 已删除；archived 不等于删除；Git Gate 不被表述为能阻止 Working Tree 先发生变化；签名不冒充密码学、作者、证明力或安全渲染。

Reviewer 未复算两个试点 hash，未检查不存在的 FileAsset Code、Helper、Git Gate、Web、并发、资源上限或负例实现，未重新逐项审核全部 current/retired 字段，也未扫描全部潜在普通文档或跨 workspace 消费者。上述处置只使 formal draft 更诚实和可复核，不关闭类型准入；下一项必要证据仍是“真实后续消费者 vs 受保护普通资产库”的对照试点。

本节记录的 formal draft 处置晚于本文前述候选设计；若前文的旧签名语义、跨项目引用、普通文档引用闭包或字段名与本节及 `specs/25-FileAsset-文件资产.md` 不一致，应将前文视为被本次复核修正的历史方案。类型必要性的当前结论再由 §23 取代，不得据任一历史快照前置实现。

---

## 二十一、00 双价值标准完成后的重基线

Human 于 2026-07-31 明确说明 `specs/00-理念与构成.md` 的并发修改已经完成。主执行者随后通过 Helper `read-specification-content` 精确读取 00 §6 当前 Working Tree 内容，确认 LDVH 现在要求按照实际服务对象分别判断 V1–V8 AI 价值和 HV1–HV5 Human 价值；一组价值不能替代另一组，实际冲突或重大取舍必须进入 Human Gate。Helper 本次读取成功，同时仍保留“7 项当前规则源资格条件尚未由 Code 机械证明”的通用资格缺口；该缺口没有被读取成功静默扩大为全量资格证明。

FileAsset formal draft 已据此重写价值判断、准入审计、activation 条件、验证和 Human Gate：

1. 对 AI，候选主要服务 V1、V2、V3、V5、V6、V7、V8；V4 只有在 Helper、受控写入与 Git Gate 实际提供可复用行动结构和确定性反馈后才能声明；
2. 对 Human，最直接的候选价值是 HV3：Human 要求跨行动保留的关键文件不再只留在临时 `docs/`，并可回读其稳定承载、完整性、状态和关键节点；
3. FileAsset 只有在决策材料用途、边界和未知范围清楚时才支持 HV1；它不保存授权基线，不能单独证明 HV2；
4. HV4 必须由真实后续使用/复用、可观察效用、依据、适用边界和未验证范围证明，不能由对象数量、关系 shape 或页面存在证明；
5. HV5 只有在文件与长期意图、决定、重要工作和结果的真实关系已由其它正确来源记录并可读时才可能支持，FileAsset 不自行拼接项目演进叙事；
6. 转为 `active` 前的真实消费者试点必须同时比较两种承载方案，并给出相应 AI/Human 价值的范围匹配证据；两组价值冲突或重大维护取舍进入 Human Gate。

因此，00 完成消除了“并发规则尚未定稿”的重基线风险，但没有让 FileAsset 自动通过准入。当时把下一项证据错误地表述为“FileAsset 必须让消费者取得普通资产库无法取得的领域结论”；Human 对“客观存在的内容事实”的后续澄清和 §23 已经修正该标准。

---

## 二十二、隔离语义读取 A/B 试点与准入结果

### 22.1 对照设计

2026-07-31，主执行者使用 §19 的两份真实审计样本建立隔离 A/B 试点，并让 fresh reader 回答同一个实际问题：“当前 Hook 审计之后，哪些残留应继续保留、另行处置或明确保持未验证？”完整消费记录见 `docs/file-asset-ab-consumer-hook-residual-disposition-2026-07-31.md`。两个 consumer envelope 都是试点专用 synthetic 结构，不是当前有效 WorkCase、ADR、Study 或其它事实对象，因此本轮不是现有事实消费者的真实关系集成试点。

- A 方案是受保护普通资产库：稳定 `asset_id`、封闭目录、sidecar manifest、固定 payload、size/hash、Human / AI agent 纳入签名、active/archived 和带用途的 `asset_refs`；
- B 方案是 FileAsset 候选：相同 payload 保护能力，加公共事实身份、类型、状态与 `relations: has-file-asset`，具体用途仍由消费者正文映射；
- 两个 fresh-context subagent 分别只获准读取一套模型，不得读取另一套、仓库其它文件或本提案，也不得联网或写文件；
- 主执行者另行执行正例解析、精确标题筛选、envelope 反向匹配和状态谓词模拟，并保留了 B-tampered、A-missing、B-unknown 三个非对称负例。

### 22.2 机械结果

两种模型的正例 shape 都能：

1. 按稳定 ID 精确解析两个样本；
2. 检查目录身份、成员闭集、payload 存在、size 和 SHA-256；
3. 按相同状态谓词把 active 纳入默认候选；
4. 以标题精确词 `Hook` 手工筛选时只定位当前审计；
5. 从第二份资产与 envelope 手工反向匹配同一 consumer。

现存负例分别证明：B-tampered 的实际 size/hash 不匹配，A-missing 缺少 payload，B-unknown 多出 `extra` 成员。没有保留 A-tampered、A-unknown、B-missing、archived fixture、读取器或执行日志，因此不能写成两边已经实际通过全部对称负例与归档验证；只能说这些机械谓词在设计上都可施加于两种目录。

两份 A manifest 分别为 359、417 bytes，两份 B manifest 分别为 414、472 bytes；A consumer envelope 为 395 bytes，B 为 644 bytes。A 把用途直接放在 `asset_refs[].usage`，B 按公共 relation 边界把用途拆到 `usage_by_object_id`，所以 envelope 大小差异不公平，不能作为准入或长期成本证据。

### 22.3 隔离语义消费结果

按主执行者的 subagent 执行记录，两个消费者独立得出相同结论；后续 independent reviewer 没有访问其对话或执行日志，只确认所记录结果与输入一致：

- 2026-07-30 报告保留为历史时间切片，不作为当前规则或环境状态；
- 当前审计支持“正式规则源和发行接入面已经没有环境 Hook/插件/adapter 层”，但不支持扩大为所有历史材料或外部环境都已没有；
- Git Gate 的原生 Git Hook、环境中性 work-context 输入和 context-recovery 功能继续保留；
- `adapter` 用词、`hooks/context_recovery.py` 包路径、`plugin` 图标文件名可以另案评估，本消费不授权修改；
- 仓库外目标环境的实际安装、启用和触发状态保持未验证。

A 消费者明确判定普通资产库对本任务充分；若要把历史输入、直接输入或取代范围机械化，优先给专用 consumer envelope 增加少量类型化用途。B 消费者确认 `has-file-asset` 的实际收益只是统一、类型化的目标定位；判断仍必须依赖关系之外的用途正文，因为关系自身不表达历史时间切片、取代、证据用途或权威等级。

### 22.4 原准入解释为什么错误

本轮在准确的“两个 Markdown 样本 + 预编码用途的 synthetic envelope + 单项目单 store + fresh reader”范围内证明：

1. A/B 让消费者取得相同 bytes、相同完整性结果、相同处置结论和相同未知范围；
2. FileAsset 的公共事实身份和 `has-file-asset` 提供统一、类型化定位，具体用途继续由消费对象正文说明；
3. A 不是零成本普通目录，而是一套需要唯一规则、Schema、ID 域、受控摄取/读取、引用、Git Gate、资源和安全合同的平行结构化资产模型。

主执行者当时错误地把“两个消费者得到相同领域结论”解释成 FileAsset 没有额外价值，并据此建议退回 A。这个标准混淆了事实对象的承载责任与消费方的领域判断：FileAsset 本来就只应稳定记录一份内容的身份、bytes、完整性、签名和状态，不负责让同一 payload 产生不同结论。A/B 结论相同只能证明两边读取了同一内容，不能否定 FileAsset。

### 22.5 独立复核

未参与 A/B 搭建的原 independent reviewer 复算了两个仓库源文件、A/B 正例、三个现存负例、两个 envelope 和标题筛选，并在 Human 澄清前选择“当前退回普通资产库”。该结论同样接受了上述错误标准，现已被 §23 取代。Reviewer 的最强反对意见仍然有效：A 本身可能只是 FileAsset 的平行私有实现，如果不计算其来源规则、字段合同、ID 命名空间、写入、引用完整性、Git Gate、资源和安全成本，就会人为放大 B 的治理负担。

Reviewer 还确认本轮不足以证明现有 WorkCase/ADR/Study 集成等价、A 长期成本更低、跨项目稳定引用成立、归档与删除保护已实现。主执行者继续保留这些真实限制：试点只证明有限 carrier 和消费 shape，不证明 activation 能力；但这些限制不再被扩大为 FileAsset 的事实语义或准入方向不成立。

---

## 二十三、Human 对事实语义的澄清与拟准入恢复

### 23.1 Human 澄清

Human 于 2026-07-31 明确：FileAsset 所谓“事实”不是“证据”，而是**客观存在的一份确定内容**。它需要记录的事实是：这组 bytes 以稳定对象身份存在于项目事实源中，具有可核对的完整性元数据、本次纳入签名和生命周期状态。FileAsset 不声明 payload 内容真实、正确、当前适用或具有证明力。

这一“事实内容不等于证据”的语义分工与当前 `fact-model-foundation` 一致：05 §5.1 允许对需要对象化、状态化或证据化管理的稳定事实内容建立类型，其中三者是“至少一种”而非必须证据化；05 §7.2.1 明确“事实对象不是用来证明自身正确的材料包”；05 §8 明确来源回指不单独证明内容正确或证据充分。此前把 FileAsset 是否产生额外领域判断当作类型准入标准，是主执行者的错误扩张。carrier 边界尚未完全一致：当前 05 §7.2.1 仍禁止命令、日志和文件路径进入事实对象，FileAsset 转 active 前必须同批建立只适用于其 canonical raw payload 的窄例外，不能由 draft 25 单方面覆盖。

### 23.2 稳定事实与消费语义的分工

FileAsset 负责：

1. 稳定对象身份与 canonical payload；
2. 实际 bytes、大小与 SHA-256；
3. Human / AI agent 二分纳入签名；
4. 对象可发现、可精确读取、可引用和可归档；
5. payload 缺失、篡改、未知成员或引用失效时的机械失败边界。

消费对象负责：

1. 为什么引用该 FileAsset；
2. 它是历史时间切片、当前输入、附件、交付物还是其它资源；
3. 内容能支持什么判断、具有什么证明力；
4. 当前是否仍适用、是否被其它内容替代；
5. 未验证范围、风险和实际结论。

因此 `active` FileAsset 只表示该内容对象在完整性检查通过后进入默认候选，不表示 payload 内的陈述仍然有效。A/B 两位消费者对相同 bytes 得出相同 Hook 残留处置，正是上述分工成立的表现。

### 23.3 其它承载位置比较的修正

根级 `docs/` 适合临时材料，不能自然提供稳定对象身份、签名、完整性、统一发现、引用和生命周期。现有 WorkCase、ADR、Pitfall、Study 或 Spark 各自承担特定项目语义，不能无损承载任意独立文件内容。

A 方案为了满足同一需求已经引入 `asset_id`、sidecar manifest、payload、签名、状态、`asset_refs`、反向扫描和专用发现；若正式落地，还需要另一套规则、Schema、Helper、Git Gate、资源限制和安全消费。它不是较小的普通文件位置，而是平行资产对象体系。AI 将不得不判断使用 `object_id` 还是 `asset_id`、`relations` 还是 `asset_refs`、事实发现还是资产发现、事实生命周期还是资产生命周期，增加长期定位、理解和维护负担。

所以 05 §6.1 第 4 项不应问“A 能否临时做出相同输出”，而应问“其它正确承载位置能否在不混淆责任的情况下自然承担”。A 只有复制事实对象能力才能满足需求，因而不能作为更自然的替代位置；统一 FileAsset 类型是更小的长期语义模型。

### 23.4 修正后的拟准入结论

当前候选判断为：

| 05 §6.1 条件 | 修正后判断 |
|---|---|
| 跨行动持续保留 | 通过候选判断；Human 明确要求关键内容离开临时 `docs/` 并可继续引用 |
| 对象化、状态化或证据化需要 | 通过候选判断；稳定身份、完整性、签名、引用和生命周期构成对象化需要，不依赖证据化 |
| 稳定语义和对象边界 | 通过候选判断；一对象一确定 payload，内容变化形成新对象 |
| 其它位置不能自然承担 | 通过候选判断；普通文件不具备所需能力，A 会形成平行对象体系并混淆责任 |
| 唯一当前定义来源 | 起草阶段未完成；`specs/25-FileAsset-文件资产.md` 保持 draft，等待同批 activation |
| V1–V8 / HV1–HV5 净价值 | 通过候选判断；当前支持 V1、V2、V3、V5、V6、V7 与 HV3，V4、V8、HV1、HV4、HV5 只在实际机制或复用范围声明 |
| 术语和机器治理 | 部分完成；FileAsset 已与 Authorized Attachment 消歧，登记与正式解析入口待同批生效 |

因此恢复 FileAsset **拟准入**方向。恢复拟准入不等于转为 `active`，也不授权创建 canonical 对象。下一阶段只推进 activation 变更包设计与验证：05 raw payload 窄例外、canonical 拓扑、字段/结构登记、机械目录、至少一个消费类型的 `has-file-asset`、目录 carrier 受控写入、Helper F0–F4、Git Gate、安全消费和独立复核。

### 23.5 A/B 试点现在能够证明什么

经修正后，本轮试点支持：

- 两种签名分支和两个真实 Markdown payload 的 carrier shape 可形成；
- FileAsset 的目录身份、成员闭集、size/hash 与关系目标 shape 可机械检查；
- fresh reader 可以从稳定目标取得 bytes，并把文件客观存在与内容当前适用性分开判断；
- 同一 payload 产生相同领域结论不否定事实对象，反而确认 carrier 没有擅自改写内容语义；
- 平行资产库若满足完整需求会复制对象模型，统一 FileAsset 可以避免第二套身份、引用、发现和生命周期。

本轮仍不证明：正式 Schema、Helper、受控写入、归档、对称负例、Git Gate、Web、资源限制、多项目或迁移已经成立。这些保持为 activation 与实现验证范围。

---

## 二十四、下一实施纵切

下一步不直接创建正式 FileAsset，也不一次修改全部 Web 和生命周期入口。先建立一个**非公开、非 canonical、只读 carrier 纵切**，用于把 draft 中最关键的目录与完整性边界转成可执行反馈：

1. 从隔离 fixture 读取 `file-asset.yaml + payload` 目录，不扫描或创建 `ldvh-base/file-assets/`；
2. 检查目录/`object_id`/`fact_type_key`、成员闭集、普通文件、symlink、由 draft 25 派生且只供本试点使用的 provisional Schema、签名条件、状态、实际 size 和完整 SHA-256；该 Schema 不登记、不成为当前合同，也不取得正式 Schema 身份；
3. 区分 manifest 已读、成员名闭集、payload 全量读取所得 size、完整 SHA-256 已计算四类 integrity coverage；
4. 只有完整 payload 读取通过时才返回“当前 bytes 存在且与登记一致”，不得由 `active` 或 manifest 声明代替；
5. 建立 Human 文本与 AI agent 二进制 payload 两个正例；建立 missing、tampered、unknown member、symlink、身份不一致、签名 shape、archived 缺少处置、预算不足和二进制 manifest 负例；另以 mechanically valid archived 正例确认其可精确读取但不进入默认候选；
6. 此纵切不登记公开 Helper operation，不取得类型能力身份，也不修改当前五类事实发现结果。

只读纵切通过后，再设计 activation 的最小正式消费者：优先选择 WorkCase，在其当前 `relations` 闭集中加入同项目 `has-file-asset`，由 WorkCase 的现有适当自然语言字段说明具体用途。第一消费纵切只验证精确目标读取、关系 target、active/archived 边界、缺失/invalid 目标、范围化反向导航和 closed 对象保留规则；不同时给全部 20–24 类型开放关系。

随后再形成同批 activation 包：05 raw payload 窄例外与 canonical 拓扑、05.Att.01 字段/结构登记、05.Att.02 机械规则 coverage、25 正式声明入口、WorkCase 关系闭集、Helper F0–F4 carrier 契约、受控创建、Git Gate 与术语登记。Web 下载/预览只有在实际提供入口前闭合安全契约；没有实现的能力继续据实不可用。

### 24.1 只读 carrier 纵切实测

2026-07-31 已在 `code/ldvh/testing/file_asset_candidate.py` 建立测试域内的显式路径 reader，并以 `code/tests/facts/test_file_asset_candidate.py` 覆盖 Human / AI agent 两类签名、文本与二进制 payload、active / archived、成员闭集、普通文件与 symlink、身份、provisional Schema、size/hash、读取预算和正式类型隔离。reader 不写文件、不枚举类型目录、不登记 Helper operation、不修改当前 `LAYOUTS`；它只接受绝对试点 root 下精确的 `file-asset-fixtures/<object_id>` 两级隔离命名空间，因此 canonical 路径、大小写别名和把 canonical 子目录重绑定成 root 的调用都不能进入读取流程。

本轮结果只支持以下有限结论：manifest、目录成员名、payload size 和完整 SHA-256 的实际检查范围可以分别报告；只有整个对象机械有效、payload 已全量读取且实际 size/hash 同时匹配时，`current_bytes_confirmed` 才为真；mechanically valid archived 对象仍可精确确认 bytes，但 `default_candidate` 为假；二进制 payload 不经文本解码，只有 manifest 必须是 UTF-8 YAML。这里的 `current` 只指本次函数调用的稳定观察窗口，不是持续有效状态；正式 Helper DTO 仍须绑定 `observed_at`、Working Tree / 对象集身份或等价观察上下文。

第一次独立代码复核发现，若 manifest 与 payload 各自重新从路径遍历，上层目录发生 ABA 换入再换回时可能混读两个目录。reader 已改为 POSIX 上先以 no-follow descriptor 持有 root 和同一个候选目录，再从该候选目录 descriptor 枚举并打开两个成员，读取后从持有的 root descriptor 重开当前路径并核对目录身份；祖先目录 swap-and-restore 回归确认不能再把另一目录的 payload 拼给已读 manifest。尚未具备此种目录句柄保证的非 POSIX 平台直接返回 `unavailable`，不回退到按路径拼接后确认 current bytes。

后续独立代码复核又依次发现并关闭：第二路径段使用 `..` 逃出 fixture、目录成员一次性无界枚举、初始枚举不稳定仍误报 closure、最终枚举出现第三成员却仍确认 current bytes。当前在任何 open 前要求第二段匹配 `file-asset-[0-9]{4,}`；descriptor-scandir 在第三项立即停止；初始或最终 closure 未完成都会清除 `members-closed` 并留下 issue；`current_bytes_confirmed` 还防御性要求整个对象 mechanically valid、`members_closed`、完整 payload size/hash 同时成立。最终独立复核未发现剩余 P1/P2，且 reviewer 未编辑文件。

试点 provisional Schema 由 draft 25 人工固化在测试模块中，只为在正式字段登记前暴露 carrier 反馈。FileAsset 转为 active 时，该实现必须删除，或改为单向消费正式字段登记与 Schema 投影；不得让测试 Schema 与正式 validator 并存为两个权威。当前已覆盖 manifest、payload 和候选目录 symlink、祖先目录确定性 ABA 换入/恢复及超过默认预算的大型二进制；仍未验证真实并发压力、Windows directory handle / reparse、正式 Schema 组合、全仓发现、受控创建、Git Gate 或 Web。精确测试数与扩大回归结果以本轮最终验证记录为准，不由本普通文档替代测试输出。
