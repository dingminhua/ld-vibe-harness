# Evidence（证据）事实对象判断报告

> 报告生成时间：2026-07-31
> 生成环境：Claude Code（Anthropic 官方 CLI），macOS arm64
> 仓库：`/Users/dmh2002/poker_hud_projects/ld-vibe-harness-v4`
> 报告定位：供 spark-0039 后续事实类型决策参考；本报告自身是 evidence 候选材料，不是正式事实对象

---

## 一、判断结论

**建议新建 Evidence（证据）作为 LDVH 第六个事实对象类型，类型键 `evidence`，放在 `ldvh-base/evidences/` 下，使用 YAML 格式。**

判断等级：**推荐**，理由充分性见下文逐节。

---

## 二、问题陈述：docs/ 下的内容现在是什么状态

当前 `docs/` 目录下散落以下内容：

| 文件 | 性质 | 能否被现有事实类型承接 |
|------|------|----------------------|
| 跨环境接入分析汇总报告 | 多份接入报告的交叉分析结论 | 勉强算 study，但 study 规范不要求交叉验证签名 |
| Codex Desktop / TRAE / ZCode / Claude Code / Codex-Cindy / WorkBuddy 六份接入分析 | 分环境实证记录，含成败、截图、命令输出 | ❌ study 太正式、workcase 太过程化、spark 太轻量 |
| cindy-ldvh-integration-study | 架构研究 | ✅ 可以转为 study（已标注"候选稿"） |
| human-cognition-web-mockup.html + .png | 认知流程设计稿，设计过程中的半成品 | ❌ 不是 ADR 决策、不是 study、不是 spark |
| study-rebuild-queue.md | 待办研究清单 | ❌ 不是事实对象，是过程管理 |

**六份接入分析报告尤其典型**——它们包含了：
- 每条 CLI 命令的实际输出（原始 stdout/stderr）
- 失败路径的 diagnostics 记录
- 环境版本号、时间戳、执行人
- 当时判断为"未验证""已验证""不支持"的如实标记

这些内容对后续环境接入有持续参考价值，但现有五个事实类型都无法恰当承接：

- **Study**：要求正式研究问题、输入边界、关键发现、建议、后续分流——六份接入分析没有研究问题，只是"跑一遍并记录结果"
- **Spark**：要求一个启发性的洞察或假设——这些是实证记录，不是洞察
- **ADR**：要求决策问题、决策、理由、后果——这些不是决策
- **WorkCase**：要求工作项的目标、计划、执行记录——这些是"环境调查"而非"工作任务"
- **Pitfall**：要求一个可复现的失败模式——这些报告包含失败路径，但主体是"完整的接入过程记录"

**结论**：`docs/` 下的内容存在真实承接缺口，散落是因为没有合适的事实类型可以容纳它们。

---

## 三、证据事实对象的定义

### 3.1 定义

证据（Evidence）是一份**可溯源、可验证、有时间锚定和环境签名的原始记录**，用于支持 LDVH 管辖项目中的判断、结论、设计选择或验收。证据本身不声明"证明什么"——它只记录"观察到了什么"，由消费方（AI、Human、Study、ADR 等）决定其证明力。

### 3.2 与现有事实类型的区别

| 维度 | Evidence | Study | Spark | Pitfall |
|------|----------|-------|-------|---------|
| 核心问题 | 我观察到了什么 | 我研究了什么 | 我假设了什么 | 我踩了什么坑 |
| 产出形式 | 原始记录 + 元数据 | 分析报告 | 结构化假设 | 可复现失败模式 |
| 是否需要结论 | 不需要 | 需要关键发现和建议 | 需要可验证假设 | 需要复现步骤 |
| 是否需要签名 | **必须** | 建议 | 不要求 | 不要求 |
| 生命周期 | 创建→引用/归档 | 创建→更新→关闭 | 创建→验证→接受/拒绝 | 创建→确认→修补 |
| 是否有大小限制 | **建议 1MB 上限** | 无 | 无 | 无 |

### 3.3 格式定义

```yaml
# ldvh-base/evidences/evidence-0001.yaml
evidence_key: evidence-0001
title: "Codex Desktop 环境 ldvh-work-context cold start 验证记录"
status: active # active | superseded | archived

# 签名：记录是谁、在什么环境下、什么时间产生的
signature:
 agent: "claude-code" # AI 宿主名
 agent_version: "0.146.0-alpha.3.1" # 宿主版本（如有）
 environment: "Codex Desktop" # 目标环境名称
 host_os: "macOS arm64 15.x" # 操作系统
 timestamp: "2026-07-30T14:22:00+08:00" # ISO 8601
 recorded_by: "dmh2002" # Human 或 AI 标识
 session_id: "..." # 可选：会话 ID，用于回溯

# 证据内容：可以是路径引用或内联
content:
 kind: "file_reference" # file_reference | inline_text | inline_json | screenshot | conversation_excerpt | external_url
 path: "docs/Codex Desktop 环境 接入LDVH.md"
 size_bytes: 8710
 content_hash: "sha256:..." # 可选，防篡改

# 来源：这个证据是怎么来的
source:
 type: "manual_execution" # manual_execution | automated_test | human_observation | external
 command: "ldvh-work-context --helper-executable ..." # 产生证据的命令（如有）
 cwd: "/Users/dmh2002/poker_hud_projects/ld-vibe-harness-v4"

# 引用关系：被哪些事实对象引用
referenced_by: []
```

### 3.4 内容 kind 说明

证据的内容可以是以下任意形式：

| kind | 说明 | 示例 |
|------|------|------|
| `file_reference` | 引用项目内已有文件（最常用） | docs/ 下的 md、截图 |
| `inline_text` | 简短文本直接内联 | 单条命令输出、对话节选 |
| `inline_json` | 结构化数据内联 | CLI 返回的 JSON |
| `screenshot` | 截图（引用路径） | human-cognition-web-mockup.png |
| `conversation_excerpt` | AI 对话中的关键段落 | 记录一次关键判断的上下文 |
| `external_url` | 外部链接 | GitHub issue、文档链接 |

### 3.5 大小限制

- **单条证据建议上限：1MB**（含引用的文件）
- 超过 1MB 的内容：拆分为多条证据，或只引用路径不内联
- `ldvh-base/evidences/` 目录整体不建议超过 50MB（受 Git 仓库大小约束）
- 截图类证据强烈建议压缩后引用（`.png` → `.jpg` 或 `.webp`）
- 长文本日志应截取关键段落而非全文内联

### 3.6 生命周期

```
active ──→ superseded（被新证据替代）
 │
 └──→ archived（不再被任何事实对象引用，自动清理候选）
```

- **创建**：观察到值得记录的结果时创建
- **被替代**：同一观察点出现更完整/更新的证据时，旧证据标记 `superseded`
- **归档**：不再被任何 study、spark、ADR、pitfall、workcase 引用时，可标记 `archived`
- **清理**：归档后通过 Git 历史可追溯，不强制删除；`ldvh-doctor` 可报告长期未引用的归档证据

---

## 四、签名机制（必须）

每条证据必须包含签名块。签名的目的是：

1. **溯源**：知道是谁在什么环境下产生的记录，避免跨环境误用
2. **可信度分级**：不同环境的证据可信度不同（已验证的 cold start > 理论分析 > 未验证的假设）
3. **可复现**：签名中的环境信息帮助后续 AI 判断"我能否复现这个结果"

### 4.1 签名格式

```yaml
signature:
 agent: "claude-code" # 必填：产生证据的 AI 宿主
 agent_version: "0.x.x" # 推荐：宿主版本
 environment: "Codex Desktop" # 必填：目标环境名称
 host_os: "macOS arm64 15.0" # 推荐：操作系统
 timestamp: "2026-07-30T14:22:00+08:00" # 必填：ISO 8601
 recorded_by: "dmh2002" # 必填：记录者标识
 session_id: "..." # 可选：会话 ID，用于回溯
```

### 4.2 AI 生成证据的签名纪律

AI 在产生证据时，必须在签名中声明自己的身份和环境。**禁止将未经验证的环境签名写成"已验证"**。

示例：
- ✅ 正确：`agent: "claude-code", environment: "Claude Code CLI", evidence_scope: "理论分析（未在目标环境实测）"`
- ✅ 正确：`agent: "claude-code", environment: "Codex Desktop", evidence_scope: "本环境 cold start 实测，source=startup 真实触发"`
- ❌ 错误：`agent: "claude-code", environment: "ZCode"`——本环境是 claude-code，不能签名 ZCode 环境的结果

**跨环境原则**：AI 只能为**自己当前所在环境**产生"实测"证据；其他环境的证据只能通过分析、引用或 Human 提供。

### 4.3 签名与证据 scope 的关系

```yaml
signature:
 # ... 签名块 ...
 evidence_scope: "本环境 cold start 实测" # 可选：说明这条证据的覆盖范围
```

`evidence_scope` 用于说明这条证据的实际覆盖范围，例如：
- `"本环境 cold start 实测"`
- `"理论分析，未在目标环境实测"`
- `"基于本环境实测结果对其他环境的推论"`
- `"Human 在 ZCode 环境手动执行后口述"`

---

## 五、证据目录结构

```
ldvh-base/
├── evidences/ # 证据目录
│ ├── evidence-0001.yaml
│ ├── evidence-0002.yaml
│ └── ...
├── evidences-attachments/ # 证据引用的附件（截图、长日志等）
│ ├── codex-desktop-cold-start-output.log
│ └── trae-hooks-format-error.png
├── adrs/
├── pitfalls/
├── sparks/
├── studies/
└── workcases/
```

为什么证据附件独立于 `evidences/` 之外：
- YAML 元数据文件很小，保持 `evidences/` 下只有 YAML 便于 Helper 快速扫描
- 大文件（截图、日志）放在 `evidences-attachments/` 下，不受 YAML 目录的扫描干扰
- 两者通过 `content.path` 的相对路径关联

---

## 六、预期收益

1. **docs/ 内容有家可归**：六份接入分析报告可以转为 evidence，不再散落
2. **跨环境知识可溯源**：签名机制让后续 AI 能判断"这个结论是在什么环境下得出的"
3. **降低 study 准入门槛**：一个单纯的观察记录不需要写完整的研究问题——先记下来，需要时再升级为 study
4. **审计文档天然是 evidence**：记录了"当时看到了什么"，满足审计的不可否认性
5. **自动清理可行**：未被引用的 evidence 可归档，Git 历史保留可追溯
6. **AI 的如实纪律可验证**：签名机制让 AI 不能冒充其他环境

---

## 七、风险和边界

1. **不应成为"随手记"垃圾桶**：不是所有观察都值得建 evidence——只有具有持续参考价值的记录才应对象化。临时笔记留在 docs/ 或 conversation 中即可。
2. **大小限制需要执行纪律**：截图和大文件应引用路径而非内联，否则 Git 仓库膨胀
3. **签名依赖 AI 自律**：签名机制是规范层面的约束，不是技术防伪——AI 仍需遵守 LDVH 如实纪律。违反签名纪律属于违规，由 Human 审计发现
4. **证据不等于结论**：一条 evidence 记录"命令返回了 X"不意味着"X 是正确行为"——消费方仍需判断
5. **与现有事实类型的引用关系需要维护**：evidence 被引用时，应在 `referenced_by` 中登记；消费方（study、ADR 等）也应在自己的事实对象中引用 evidence
6. **归档后不删除**：归档标记 `status: archived`，物理文件保留在 Git 历史中可追溯，不强制删除

---

## 八、与现有事实类型规范的关系

Evidence 事实对象的定义来源（本报告）建议的规范位置：

- **新 specs 文件**：`specs/25-Evidence-证据.md`，作为事实类型规范（同 20-24 的定位）
- **基础依据**：`specs/05-事实模型基础规范.md`（事实对象共同规则）
- **授权附件**：`fact-object-field-registry` 中新增 evidence 专属字段
- **事实源边界**：`specs/03-事实源与信息溯源规范.md`
- **Helper 操作**：evidence 的只读查询和创建纳入 Helper CLI 操作清单

---

## 九、后续步骤（如果决定新建）

1. 起草 Evidence 事实类型规范（`specs/25-Evidence-证据.md`）
2. 在 `fact-object-field-registry` 中登记 evidence 专属字段
3. 创建 `ldvh-base/evidences/` 和 `ldvh-base/evidences-attachments/` 目录
4. 将 docs/ 下具有持续参考价值的内容迁移为 evidence 对象
5. 更新 `ldvh-helper-cli` 支持 evidence 的只读查询和创建
6. 在 SKILL.md 中补充 evidence 的使用指引

---

## 附录：本报告自身作为 evidence 的签名块

```yaml
signature:
 agent: "claude-code"
 agent_version: "Anthropic Claude Code CLI（当前会话）"
 environment: "Claude Code（本机 macOS）"
 host_os: "macOS arm64"
 timestamp: "2026-07-31T10:00:00+08:00"
 recorded_by: "GLM（智谱AI）——本会话中的 AI 助手"
 evidence_scope: "基于 docs/ 目录内容分析、已有事实类型规范（specs/05、specs/20-24）和当前会话讨论生成的判断报告；未在目标环境（Codex Desktop、ZCode 等）实测"
```