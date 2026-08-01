# FileAsset A/B 试点：Hook 残留处置消费报告

> 状态：2026-07-31 非 canonical 设计试点记录；已按 Human 对“客观存在的内容事实”的澄清修正准入解释。本文不是当前规则源或事实源，不创建正式 FileAsset，不授权修改 Hook 相关规则、Code、历史文档或外部环境。试点中的对象 ID、关系和目录都只用于对比两种承载模型。

## 一、消费问题与结论

本次让同一个后续消费者回答：

> 当前 Hook 审计之后，哪些残留应继续保留、另行处置或明确保持未验证？

消费结论如下：

1. `docs/跨环境接入分析汇总报告-2026-07-30.md` 应继续保留为 2026-07-30 历史方案的原始时间切片；它不能作为当前 LDVH 环境接入规则或当前环境状态。
2. `docs/ldvh-environment-hook-claim-audit-2026-07-31.md` 可作为本次处置判断的直接审计输入。其受检查范围支持的当前结论是：正式规则源和发行接入面已经不定义环境 Hook、插件或 adapter 接入层；薄 Skill 是默认且唯一环境接入形态，原生 Git Hook 只承接 Git Gate。
3. `work-context-core` 中的 `adapter` 用词、`code/ldvh/hooks/context_recovery.py` 包路径和 `ldvh-plugin-icon-*` 文件名属于可另行评估的术语或实现命名残留。本次消费不授权修改，也不把它们解释成当前正式接入层。
4. 仓库外目标环境是否仍安装、启用或触发旧 Hook、插件或 adapter 保持未验证；本次材料不支持把“正式设计已移除”扩大成“所有外部环境都已经没有”。
5. 根级 `docs/` 中其它旧接入报告应按历史材料处理，不宜无差别改写成当前结论。若后续集中保全，应保留原始 bytes，并在消费位置明确其时间切片与被取代范围。

两种模型都使 fresh reader 得到相同的上述语义判断，这是同一 payload 被完整读取后的预期结果。FileAsset 记录的是“一份确定内容以稳定身份客观存在”，不是证据或自动改变领域判断的推理机制；它不应因为没有让消费者对同一 bytes 得出不同结论而被拒绝。本轮真正观察到的差异是：A 要满足同一需求必须另建 `asset_id`、`asset_refs`、状态、发现和生命周期，B 则把客观存在的文件内容纳入现有事实身份、公共关系与恢复体系。因此，本轮支持继续推进 FileAsset 拟准入设计，但不使 draft、正式对象或实现能力自动生效。

## 二、输入样本

| 样本 | 当次用途 | 字节数 | SHA-256 | 纳入签名候选 |
|---|---|---:|---|---|
| `docs/跨环境接入分析汇总报告-2026-07-30.md` | 历史方案时间切片 | 9271 | `58b4a1a5b84ff7470c974b2a16b7beea28b916253762401664ed67b2a1a171b0` | `human` |
| `docs/ldvh-environment-hook-claim-audit-2026-07-31.md` | 当前残留处置的直接审计输入 | 11124 | `57ca7ee0c5f006a0736b618fdc526a55e21d0f3ff068de10e7043b6090b6f8ac` | `ai-agent`：`codex` / `Codex Desktop` |

第一份文件由 Human 在本次对话中指定为外部提供样本，签名只表示 Human 把最终 bytes 直接提供给本次受控摄取边界；第二份审计由 Human 要求当前 AI agent 编写，签名属于实际生成并提交最终 bytes 的当前 agent。两者都不表示密码学签名、历史作者、审批或内容证明力。

## 三、A/B 承载模型

试点原位于临时目录 `/tmp/ldvh-file-asset-ab.MI32yS`。独立复核完成后，主执行者于 2026-07-31 将该精确目录可恢复地移入 `/Users/dmh2002/.Trash/ldvh-file-asset-ab.MI32yS-20260731`，并确认原 `/tmp` 路径已经不存在；废纸篓副本不是长期依据，可以由 Human 正常清空。本报告记录可复算输入摘要、检查结果和未验证范围，不依赖临时目录或废纸篓副本长期存在。

### 3.1 A：受保护普通资产库

每份资产使用 `protected-assets/<asset_id>/{asset.yaml,payload}`，sidecar 保存稳定 `asset_id`、标题、状态、文件名、媒体类型、字节数、SHA-256、形成时间和纳入签名。消费者使用带用途说明的 `asset_refs` 精确引用两个资产。

这不进入公共事实类型与 `relations`，但已经是一套结构化资产对象模型，而不是“普通目录免费获得保护”：它若要成为长期稳定来源，同样需要唯一规则、字段合同、ID 域、受控摄取/读取、专用引用、Git Gate、资源限制和安全消费。试点只构造了可由专用确定性读取器承接的 shape，没有实现这些正式能力。

### 3.2 B：FileAsset 候选事实对象

每份资产使用 `file-assets/<object_id>/{file-asset.yaml,payload}`，manifest 额外带有公共事实身份、类型、状态和更新时间。消费者使用两个 `relations: has-file-asset` 稳定三元组引用，并另以消费正文映射说明每份文件的具体用途。

这些目录、字段和关系都未进入当前规则源；它们只模拟 `specs/25-FileAsset-文件资产.md` 草案提出的候选形状。

## 四、机械与负例结果

两种模型的两个正例都通过以下实际检查：

- 目录名与 `asset_id` 或 `object_id` 一致；
- 直接成员闭集只有 manifest 与 `payload`；
- payload 存在且实际字节数匹配 manifest；
- 完整 payload SHA-256 匹配 manifest；
- 按试点状态谓词，默认候选只返回 `active`；
- 精确消费者引用均可解析；
- 从两份 envelope 手工反向匹配第二份资产，均可找到消费者 `hook-residual-disposition-2026-07-31`；
- 以标题精确词 `Hook` 手工筛选时，两边都只命中第二份资产。

负例实际结果：

| 已保留负例 | 实际观察 | 候选处置 |
|---|---|---|
| FileAsset payload 追加 `TAMPERED-PILOT-BYTES` | `size_matches=false`，SHA-256 不匹配 | 拒绝作为有效资产消费 |
| 普通资产缺少 payload | `payload_exists=false` | 拒绝作为有效资产消费 |
| FileAsset 目录增加未知成员 `extra` | `members_closed=false` | 拒绝作为有效资产消费 |

现存材料只分别证明 A 的 missing、B 的 tampered 与 unknown fixture；没有保留对称负例、archived fixture、读取器或运行日志。相同 size/hash、成员闭包和状态谓词在设计上可以施加于两种目录，但本轮不能把“可表达”扩大成两边都已实际实现和验证。

## 五、隔离消费者结果

主执行者分别启动两个全新上下文的 subagent。A 消费者只获准读取普通资产库及其 consumer envelope；B 消费者只获准读取 FileAsset 候选目录及其 consumer envelope。按主执行者记录，两者都不得读取仓库其它文件、联网或写文件，因此不能借用本报告的比较结论；独立 reviewer 没有访问其对话或执行日志，只确认所记录结果与输入一致。

两位消费者独立完成了目录、身份、成员闭包、普通文件、字节数和 SHA-256 复算，并得到了相同的 Hook 残留处置分类。两者也都明确保留了同一证据边界：它们验证了审计 payload 的字节完整性，但没有在受限任务中重新读取该审计引用的规则、Code 或外部环境，所以不能把 payload 所载结论冒充成消费者独立重做的仓库审计。

A 消费者判定“受保护普通资产库 + consumer envelope”足以完成本次有界阅读任务。这个结论只说明 A 可以把同一 payload 交给消费者，不回答 LDVH 是否应为此维护第二套身份、引用、发现和生命周期。它建议增加类型化用途，反而说明 A 会继续演化出平行资产对象合同。

B 消费者判定 FileAsset 组合对本任务同样充分。它识别出的公共关系实际收益是：`has-file-asset` 提供统一、类型化、无需猜文件名的目标定位；对象外的 `usage_by_object_id` 区分历史时间切片和直接审计输入。这不是 FileAsset 缺陷，而是职责分离：FileAsset 负责内容客观存在、身份与完整性，消费对象负责用途、当前适用性、证明力和权威等级。

因此，隔离消费证明两种 carrier 都能交付相同 bytes，同时证明 B 可以保持“文件内容事实”与“消费用途判断”的边界。是否准入不能再以 B 是否产生 A 无法表达的领域结论判断，而应比较哪种承载位置不混淆责任：A 已经需要平行对象治理，B 复用现有事实身份与关系。本轮尚未把 B 集成进当前有效 WorkCase、ADR、Study 或其它事实对象，所以正式关系、F1–F4 与长期实现成本仍是 activation 验证范围。

## 六、成本与能力对比

| 判断维度 | A：受保护普通资产库 | B：FileAsset | 本轮结论 |
|---|---|---|---|
| 集中保管与稳定 ID | 候选可提供 | 候选可提供 | 本次单 store 等价；多项目与迁移未验证 |
| 原始 bytes、大小与 hash | 可提供 | 可提供 | 等价 |
| Human / AI agent 纳入签名 | 可提供 | 可提供 | 等价 |
| active 默认发现、archived 精确回读 | shape 可表达 | shape 可表达 | archived 未实际验证 |
| 精确引用与反向扫描 | 专用 `asset_refs` shape | 公共 `relations` shape | 单 store 可手工重建；正式能力未验证 |
| F2 式标题候选 | 专用读取器可表达 | Helper 事实发现可表达 | 当前只有手工精确词筛选 |
| 消费用途语义 | synthetic `asset_refs[].usage` 直接携带 | synthetic relation 之外仍需消费正文 | 设计不对称，不据此判断优劣 |
| 消费 envelope 大小 | 395 bytes | 644 bytes | B 多 249 bytes；因用途结构不对称，不作准入证据 |
| 两份 manifest 大小 | 359 / 417 bytes | 414 / 472 bytes | B 每份多 55 bytes |
| 共同事实关系复用 | 无，需新增平行 `asset_refs` | 有，复用 `relations` 与稳定事实目标 | B 避免第二种跨对象引用体系；用途仍由消费对象正文承担 |
| 治理与实现影响面 | 需新建资产规则、Schema、ID 域、读取/写入、引用、Git Gate、资源与安全合同 | 需新增第六事实类型并修改共同规范、登记、消费类型、Helper、Schema、Git Gate、Web | 两边都有成本；A 还增加第二套对象治理，B 的成本集中于扩展现有体系 |

“进入统一系统”在这里不是视觉整齐，而是避免 AI 同时学习两套 ID、引用、发现、状态和生命周期语义。FileAsset 的准入价值是让一份客观存在的文件内容获得现有事实模型的稳定身份、恢复与关系能力，不是让同一内容在读取后产生不同领域结论。

## 七、准入判定

本次 A/B 试点经 Human 澄清事实语义后的判定为：**FileAsset 方向恢复为拟准入，继续完成同批定义与验证；当前仍保持 draft，不直接激活。**

理由是：FileAsset 的稳定事实语义已经明确为“确定内容以该身份客观存在”，不包含内容正确性或证明力；稳定 ID、完整性、Human/AI agent 签名、跨行动发现、引用和生命周期构成真实对象化需求。A 能完成同一读取，但为了长期成立已经复制这些能力，形成第二套资产对象体系，不能作为不混淆责任的普通文件承载位置。B 复用现有事实身份、`relations` 和恢复链，候选净价值不以改变 payload 的领域结论为前提。

FileAsset 从 draft 转为 active 前仍必须完成：

1. 05 对 FileAsset raw payload carrier 的窄例外和 canonical 拓扑；
2. 字段、签名结构、机械验证目录和 Schema 登记；
3. 至少一个现有消费类型对同项目 `has-file-asset` 的正式关系定义；
4. 目录 carrier 的受控创建、完整读取、归档、故障残留和资源限制；
5. Helper F0–F4、Git Gate 与安全下载/预览的范围匹配验证；
6. 对修正后事实语义、独立规范责任和完整影响面的独立复核。

在上述 activation 包闭合前，不创建 canonical FileAsset，不把 `file-asset` 加入当前类型登记，也不声明 Helper、Git Gate 或 Web 已支持。可以继续修改 draft、设计同批规则和实现验证方案。

第一次独立 reviewer 在 Human 澄清前选择过“当前退回普通资产库”；该结论使用了“B 是否产生 A 无法取得的领域结论”这一错误标准。其可保留 finding 是：A 不是免费目录，而是平行结构化资产模型；本轮仍只覆盖 synthetic envelope、单项目单 store 和有限非对称负例，删除保护、归档、F0–F4、反向扫描与完整成本尚未正式验证。修正后的准入方向已由两位 independent reviewer 重新复核，均支持继续 draft 拟准入且不提前转 active。

## 八、未验证范围

- 没有检查仓库外任何目标环境的 Hook、插件或 adapter 安装与触发状态；
- 没有创建、更新、归档或删除 canonical 资产；
- 没有实现 A 或 B 的正式 Helper、Schema、Git Gate、Web、并发 ID、资源上限或主动内容安全策略；
- 没有把任一方案集成进当前有效 WorkCase、ADR、Study 或其它事实对象；
- 没有验证多项目、跨 workspace、linked worktree、store 迁移或跨项目反向引用；
- 没有审计 A 形成正式稳定资产库所需的完整规范和实现变更包；
- 没有保留对称负例、archived fixture、读取器或试点执行日志；
- 两个样本都是 Markdown 小文件，未覆盖大文件、二进制、压缩包、恶意内容或摄取中途崩溃；
- A 的专用 `asset_refs` 和 B 的 `has-file-asset` 都是试点契约，不是当前正式来源；
- 语义结论只覆盖两份 payload 声明的审计范围，不证明未读取材料、当前外部环境或未来版本状态。

## 九、形成说明

本报告由 Human 要求当前 Codex AI agent 执行试点后形成。报告记录的是试点输入、实际检查、消费结论和准入判断；它不是 FileAsset，因此这里的形成说明不冒充正式 FileAsset 签名字段。
