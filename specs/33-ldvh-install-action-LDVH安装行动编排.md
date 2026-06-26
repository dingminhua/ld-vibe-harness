# LDVH安装与首次配置行动编排

```yaml
v2_spec:
  spec_id: "33"
  spec_kind: "member_spec"
  title: "LDVH安装与首次配置行动编排"
  status: "active"
  authority: "active"
  canonical_path: "specs/33-ldvh-install-action-LDVH安装行动编排.md"
  created: "2026-06-26"
  updated: "2026-06-26"
  parent_spec: "specs/03-行动编排规范.md"
  relation: "action_member"
  positioning: "定义 AI 引导用户安装 LDVH 并完成首次管辖项目配置的行动流程：判断环境 AI Hook 能力、选择安装方式、放置薄引用或插件、验证安装、配置管辖项目并确认生效"
  scope: "用户首次接触 LDVH、要求安装或接入 LDVH、安装后首次对项目启用 LDVH 时的 AI 引导行动"
  basis:
    - "specs/00-LDVH理念与价值标准.md"
    - "specs/01-规范体系基础规范.md"
    - "specs/03-行动编排规范.md"
    - "specs/06-运行时扩展规范.md"
  related_specs:
    - "specs/04-Code确定性执行规范.md"
    - "specs/07-事实源边界与Git追溯规范.md"
    - "specs/32-environment-entry-adaptation-环境入口落地与适配检查.md"
    - "specs/attachments/03.Att.01-成员身份字段表.md"
    - "specs/attachments/03.Att.02-成员主文件骨架模板.md"
    - "specs/attachments/06.Att.02-固定运行时扩展登记表.md"
    - "specs/attachments/06.Att.09-薄引用模板.md"
    - "specs/attachments/06.Att.15-环境Hook事件映射表.md"
  migration_sources: []
  active_fact_source:
    - "specs/33-ldvh-install-action-LDVH安装行动编排.md"
  code_consumption:
    - "v2_spec_metadata"
    - "action_member_identity"
    - "action_member_anchors"
    - "ldvh_install_action"
  migration_status: "not_applicable"
```

```yaml
v2_action_member:
  spec_id: "33"
  kind: "action_process"
  name_en: "ldvh-install-action"
  name_zh: "LDVH安装与首次配置行动编排"
  collection_status: "active"
  canonical_path: "specs/33-ldvh-install-action-LDVH安装行动编排.md"
  scenario_anchor: "§8"
  context_anchor: "§7"
  gate_anchor: "§12"
  execution_anchor: "§9"
  issue_routing_anchor: "§10"
  writeback_anchor: "§14"
  evidence_anchor: "§14"
  testability_anchor: "§16"
  assurance_takeover:
    - "source_spec=specs/03-行动编排规范.md; requirement=流程复用要求; scope=AI 引导用户安装 LDVH 的可复用行动流程，不替代环境自身安装步骤"
    - "source_spec=specs/06-运行时扩展规范.md; requirement=双路径接入要求; scope=按 AI Hook 能力分流：推荐插件方式，提供 Rules 方式；不得将一种方式写成唯一终态"
    - "source_spec=specs/32-environment-entry-adaptation-环境入口落地与适配检查.md; requirement=环境落地适配; scope=安装后须引导用户完成首次管辖项目配置和验证"
  capability_assets:
    - "type=rule; path=rules/LDVH-RUNTIME-PROTOCOL.md; purpose=Rules 方式安装的目标薄引用入口; status=required"
    - "type=code; path=code/hook_dispatch.py; purpose=安装后验证（session-start + pre-tool-use）; status=required"
    - "type=code; path=code/specs_validate.py; purpose=governed-projects 验证管辖项目配置; status=conditional"
```

> 文件性质：03 行动编排成员。定义 AI 引导用户安装 LDVH 的行动流程。
> 不定义：环境自身产品安装步骤、插件发布机制、LDVH 产品资产的本体规则。

---

## 1. 这个问题怎么触发

当用户对本会话中的 AI 说出以下任一时，AI 应按本文执行安装行动：

- "安装 LDVH"
- "接入 LDVH"
- "帮我设置 LDVH"
- "怎么开始用 LDVH"
- 用户表达了接入 LDVH 的意图但不清楚步骤

---

## 2. 上位依据

| 来源规范 | 章节 | 本文承接 |
|---|---|---|
| `specs/03-行动编排规范.md` | §5-§12 | 行动成员身份、流程复用、Gate、证据和回写 |
| `specs/06-运行时扩展规范.md` | §7 | 双路径接入（插件方式 / Rules 方式） |
| `specs/32-environment-entry-adaptation-环境入口落地与适配检查.md` | — | 安装后环境落地适配 |

---

## 3. 本文解决的问题

用户在接触 LDVH 时面临三个不确定：

1. **我的环境支持 AI Hook 吗？** — 不确定该走插件还是 Rules
2. **我需要放什么东西、放在哪？** — 薄引用还是插件安装，路径在哪
3. **装完后怎么确认成功了？** — 验证手段是什么

本文减少这些不确定性，让 AI 按照固定流程引导用户，不因环境差异给出矛盾建议。

---

## 4. 构成要素归属与价值判断

| 要素 | 归口 |
|---|---|
| AI Hook 能力判断逻辑 | 本文 §4 |
| 插件方式安装步骤 | 本文 §5 |
| Rules 方式安装步骤 | 本文 §6 |
| 安装后验证 | 本文 §7 |
| STOP 与 Human Gate | 本文 §11 |
| 环境落地适配（安装后） | `specs/32` |
| 薄引用模板正文 | `06.Att.09` |
| 环境 Hook 事件映射 | `06.Att.15` |

---

## 5. 第一步：判断目标环境的 AI Hook 能力

AI 必须先从对话上下文中判断用户当前使用的环境是否支持 AI Hook。

### 4.1 已知能力矩阵

| 环境 | AI Hook 能力 | 推荐安装方式 |
|---|---|---|
| WorkBuddy | 支持 | 插件方式 |
| Codex | 支持 | 插件方式 |
| Claude Code | 支持 | 插件方式 |
| Trae | 不支持 | Rules 方式 |
| 其它未知环境 | 待确认 | 按本节规则判断 |

### 4.2 未知环境的判断规则

AI 可以询问用户以下问题，或根据上下文推断：

1. "你当前使用的 AI 工具支持自定义 Hook 或插件吗？"
2. "你的环境有类似 AGENTS.md、rules、instructions 等可被 AI 稳定读取的入口吗？"

若用户无法确认 AI Hook 能力，AI 应采取**安全默认**：推荐 Rules 方式。

### 4.3 设计约束

- **不得**向用户宣称某个未验证的环境支持 AI Hook。
- **不得**将 Rules 方式表述为"受限路径"或"不完整方案"。
- 已知能力矩阵的变化（新增环境、实测结果）应通过 06.Att.15 和本文更新，不在此处重复定义。

---

## 6. 插件方式（AI Hook 环境推荐）

### 5.1 适用条件

- 环境已确认支持 AI Hook（WorkBuddy / Codex / Claude Code）

### 5.2 安装步骤

AI 引导用户执行：

1. **安装 LDVH 插件**：按环境自身的插件管理方式安装 LDVH 插件。插件内含 `hooks/hooks.json` 或等价 Hook 配置。
2. **信任/授权**：环境弹出信任对话框时，用户确认信任。
3. **验证**：重启环境或开启新会话后，环境自动触发 SessionStart Hook，`hook_dispatch.py` 执行 `session-start`。若 cwd 命中管辖项目，返回 `governed=true` + receipt。

### 5.3 AI 的引导话术要求

- 说明这是推荐方式，因为环境有 AI Hook，能自动触发协议。
- 提醒用户只需安装 + 授权，不需要手动写任何文件。
- 告知用户：安装后新建会话即可验证是否生效。

### 5.4 安装后

用户可继续配置管辖项目（`LDVH-GOVERNED-PROJECTS.yaml`），详见 `specs/32` §8。

---

## 7. Rules 方式（无 AI Hook 环境或用户选择）

### 6.1 适用条件

- 环境不支持 AI Hook（Trae 等），或用户明确选择不使用插件

### 6.2 安装步骤

AI 引导用户执行：

1. **定位环境目录入口**：
   - AI 根据用户环境判断可稳定被 AI 读取的入口位置（如 AGENTS.md、rules、instructions 等）
   - 若环境有 AGENTS.md：在文件中追加薄引用
   - 若环境使用其它入口机制：在对应位置放置薄引用

2. **生成薄引用正文**：
   按 `06.Att.09` 模板，将 `<LDVH_RUNTIME_PROTOCOL>` 替换为当前机器上 `rules/LDVH-RUNTIME-PROTOCOL.md` 的真实绝对路径。

3. **验证**：
   指导用户在新会话中确认 AI 已自动读取薄引用 → 读完 RUNTIME-PROTOCOL → 跑 `session-start --trigger-source rules`。

### 6.3 AI 的引导话术要求

- 说明 Rules 方式与插件方式是 LDVH 的两种平等接入方式。
- 解释：环境没有 AI Hook，所以 AI 会自觉按 RUNTIME-PROTOCOL 触发协议步骤。
- 不要把 Rules 方式说成"备选""受限路径"或"不完整"。

### 6.4 薄引用正文

```markdown
#### LDVH AI 入口引用开始

读取并遵守：

<LDVH_RUNTIME_PROTOCOL>

发生 `/compact`、自动上下文压缩、线程恢复或上下文恢复后，重新读取上述 LDVH AI 入口。

#### LDVH AI 入口引用结束
```

`<LDVH_RUNTIME_PROTOCOL>` 由 AI 替换为真实绝对路径。例如：

```
/Users/dmh2002/poker_hud_projects/ld-vibe-harness/rules/LDVH-RUNTIME-PROTOCOL.md
```

---

## 8. 安装后验证

无论哪种安装方式，AI 都应引导用户完成验证。分两步：

### 8.1 安装连通性验证

```bash
python3 code/hook_dispatch.py run session-start --trigger-source rules --cwd <任意目录>
```

预期输出中 `governed: false` 且无报错，说明 LDVH 已可连通。若命令不可执行，回到第 5 或第 6 步检查安装。

### 8.2 管辖项目首次配置验证

安装连通后，继续 §9 配置首个管辖项目。

---

## 9. 首次配置管辖项目

安装验证通过后，AI 引导用户对第一个项目启用 LDVH。

### 9.1 用户指定项目

AI 询问："你想对哪个项目启用 LDVH？"

用户提供项目目录路径后，AI 定位该目录下的 `LDVH-GOVERNED-PROJECTS.yaml`：

- 若不存在 → 进入 §9.2 创建
- 若已存在 → 进入 §9.3 追加

### 9.2 创建管辖项目配置

AI 在用户项目根目录下生成 `LDVH-GOVERNED-PROJECTS.yaml`：

```yaml
version: "1.0"
governed_instance: "/Users/<用户>/poker_hud_projects/ld-vibe-harness"
projects:
  - path: "<用户项目路径>"
```

`governed_instance` 为 LDVH 仓库在本机的绝对路径。AI 必须让用户确认后再写入，不得静默创建。

### 9.3 已有配置时追加

若文件已存在，AI 检查当前项目是否已在 `projects` 列表中：

- 已在 → 无需操作
- 不在 → 提示用户追加条目，由用户确认后写入

### 9.4 配置后验证

```bash
python3 code/hook_dispatch.py run session-start --trigger-source rules --cwd <项目目录>
```

预期：`governed: true`，`receipt: ok`。

若 `governed: false`：检查 `LDVH-GOVERNED-PROJECTS.yaml` 路径是否正确。

### 9.5 完成

验证通过后，AI 告知用户：

- **插件方式**："下次在这个项目中新建会话，SessionStart Hook 会自动触发 LDVH 协议。"
- **Rules 方式**："AI 每次新会话会读取 Runtime Protocol，自觉触发协议步骤。子 Agent 启动时同样自觉执行。"

---

## 11. 场景入口（AI 如何回到本文）

| 用户动作 | AI 应从本文读取的入口 |
|---|---|
| 首次安装与配置 | §4 → §5/§6 → §8 → §9 |
| 询问"插件还是 Rules" | §4.1 能力矩阵 |
| 安装后不生效 | §8 验证 + §12 问题分流 |
| 更换环境重新安装 | §4.1 重新判断环境能力 |
| 仅需薄引用正文模板 | §6.4，同时参照 `06.Att.09` |
| 对新项目启用 LDVH | §9 首次配置管辖项目 |

---

## 11. 执行顺序

```text
1. 判断环境 AI Hook 能力（§4）
   ├── 支持 → 推荐插件方式（§5）
   └── 不支持或用户选择 → Rules 方式（§6）
2. 执行安装
3. 验证安装（§7）
4. 通过 → 告知用户安装完成，可继续配置管辖项目（→ specs/32）
   不通过 → 回到步骤 2 或分流 §10
```

---

## 12. 问题分流

| 症状 | 可能原因 | 分流位置 |
|---|---|---|
| 插件安装后 Hook 不触发 | 环境未信任、插件未启用、cwd 不在管辖项目 | §8 验证步骤 |
| AI 未读取薄引用 | 入口路径不存在或不被环境读取 | §6.2 定位环境目录入口 |
| 配置后 governed=false | LDVH-GOVERNED-PROJECTS.yaml 路径错误或未写 | §9.4 配置后验证 |
| session-start 返回 non-zero | knowledge-map 不可用、管辖配置异常 | `hook_dispatch.py` 输出 |
| 用户不知道环境是否支持 Hook | 未知环境 | §4.2 判断规则 |

---

## 13. Human Gate

| STOP 条件 | 处理 |
|---|---|
| 用户拒绝安装 | 停止。不强行安装、不修改用户配置文件 |
| 环境 AI Hook 能力不明且用户拒绝确认 | 停止。不得替用户判断 |
| 安装后三次验证均失败 | 暂停。记录错误输出，建议 Human 复核 |
| 要覆盖用户已有的 AGENTS、rules、instructions | Human Gate。不得静默覆盖 |
| 要在用户项目中创建 `LDVH-GOVERNED-PROJECTS.yaml` | Human Gate。仅建议，不自动创建 |

---

## 14. 需要通知相关方

- `specs/06`：若本文新增或改变了环境接入的推荐路径
- `specs/32`：安装完毕后应引导用户进入环境落地检查
- `06.Att.09`：若薄引用模板变更

---

## 15. 回写与证据

安装行动完成后，AI 应：
1. 告知用户安装方式（插件 / Rules）和验证结果。
2. 如有异常，记录 `hook_dispatch.py` 输出作为诊断证据。
3. 如需要配置管辖项目，将用户引导到 `specs/32`。

---

## 16. 交付物

一次成功安装的交付物是：

- 插件方式：环境已启用 LDVH 插件，SessionStart Hook 可自动触发
- Rules 方式：环境目录中存在指向 `LDVH-RUNTIME-PROTOCOL.md` 的薄引用，AI 可稳定读取

---

## 17. 测试与验证

| 验证项 | 命令 / 检查 |
|---|---|
| Rules 安装后验证 | `python3 code/hook_dispatch.py run session-start --trigger-source rules --cwd <管辖项目>` |
| 薄引用路径存在 | 检查 `<环境目录>/AGENTS.md` 或等价入口是否包含 `LDVH-RUNTIME-PROTOCOL.md` 绝对路径 |
| 管辖项目配置 | `python3 code/specs_validate.py governed-projects` |


---

## 18. 规范保障要求

本节是 03 要求的成员一致性兼容章节，不生成新的规范保障要求。本文承接的来源要求见 v2_action_member.assurance_takeover。

| 保障要求 | 要求内容 | 保障机制 | 同步类型 | 触发条件 |
|---|---|---|---|---|
| 来源承接：03 流程复用与行动成员要求 | 回指 specs/03 §5、§11、§12；本文只承接安装行动的执行闭环、证据、Gate 和能力映射 | 本文 v2_action_member.assurance_takeover、§10 执行顺序、§12 Human Gate、§14 回写 | 行动编排治理 | 03 的成员机制、承接边界或 active 判定变化时 |
| 来源承接：06 双路径接入要求 | 回指 specs/06 §7；本文按 AI Hook 能力分流推荐安装方式，不将任一种写成唯一终态 | 本文 §5（插件方式）、§6（Rules 方式）、capability_assets | 能力资产编排 | 06 §7 接入规则或 canonical event 变化时 |
| 来源承接：32 环境落地适配 | 安装完毕后应引导用户进入 specs/32 环境落地检查 | 本文 §8（安装后验证） | 行动编排治理 | 32 环境落地流程变化时 |
| 行动 Gate 阻断 | 回指 03 Human Gate 原则和 06/32 的环境边界；本文只列出安装行动中必须暂停的触发条件 | 本文 §12 Human Gate | Human 确认 | 用户拒绝、环境能力不明、验证失败或覆盖已有配置时 |

---

## 19. 待补齐事项

1. 插件方式的安装步骤与具体环境的插件发布机制待对接。
2. 首次安装后与 specs/32 环境落地流程的衔接步骤待实测验证。
