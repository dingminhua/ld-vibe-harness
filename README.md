# LDVH — LD Vibe Harness

LDVH 以 AI 执行者为第一服务对象，帮助 AI 在长期项目中保持**判断有据、行动可续、结果可验**；同时直接服务 Human，使决策提请清晰可决、授权执行受控可续、入档闭环节点可验，并让项目演进脉络可循。积累效用如何直观可见仍是当前明确待加强的能力，不因事实对象、提交或页面存在就宣称已经实现。

它由规范（Specs）、事实对象（Fact Objects）与行动模板（Action Templates）构成，以源码仓库为能力本体，通过薄 Skill、Helper CLI、必部署的 Git Hook、其承接的 Git Gate 和 Web 界面交付，适用于需要 AI 跨会话保持一致、Human 返回后能够核查并接续，以及在不同 AI 开发环境中复用规则的长期项目。

---

## 快速开始

### 取得源码

LDVH 默认不打包、不安装本体，也不需要 pip。源码仓库就是能力本体：

```bash
git clone https://github.com/dingminhua/ld-vibe-harness.git
cd ld-vibe-harness
```

若已经有源码仓库，记录其 remote（存在时）、当前 revision 与工作树状态。随后先读 `specs/attachments/09.Att.01-环境接入面.md` 的当前交付状态：只有稳定源码 Helper launcher、源码模式 doctor、common-dir 级 Git Hook 管理入口和 Git Gate 源码入口均标记为已交付时，才继续完整接入。不要用 PATH 中来源不明的同名命令或既有 distribution console entry point 替代，也不要构建或安装 wheel、sdist、editable distribution。

按当前 09.Att.01 的交付状态，上述源码 launcher 和 common-dir 级 Git Hook 管理实现尚未交付，因此新的默认接入流程必须停在迁移缺口，不能声明可用或完整接入。源码 launcher 后续交付后，Helper capabilities 用于发现当前公开能力；所有 Helper 入口仍无条件读取 stdin 至 EOF，在 AI 环境或无 tty 的自动化中调用时必须闭合 stdin。若仓库入口依赖的运行时或第三方库未满足，应按仓库当次声明准备运行条件；这不等于打包或安装 LDVH 本体。

当前已验证平台为 macOS；其它平台的仓库入口、运行依赖、路径与 Git Hook 执行能力尚未实测，按未验证范围处理。

### 更新

`git pull` 后在任一已接入环境告诉 AI「LDVH 更新了」即可：由 AI 按下述规则判断变化类型、只重放受影响部署件，并完成重验。手动判断时遵循：

- 规范与规则源更新：仓库入口现取现用；仍需按受影响范围复核行为，不安装 LDVH 包；
- `skill/SKILL.md` 变化：将各环境部署件与新模板逐字节比对，过期者重新部署；
- 源码 launcher、运行依赖声明、Git Hook 管理实现或 Git Gate 核心入口变化：验证源码入口，并按目标 common-dir 重新检查或部署承接 Git Gate 的 Git Hook；
- 上述处理后按 specs/09 §6.5 与 specs/attachments/09.Att.02 重验受影响范围，不沿用旧验证结论。

## 启动 Web（本地开发）

需要 Node.js 与 npm。在仓库根目录执行：

```bash
cd web
npm ci
npm run dev
```

按当前本地开发脚本，前端固定监听 [http://127.0.0.1:5173](http://127.0.0.1:5173)；端口被占用时会启动失败。本地 API 默认使用 `3001`，可由 `PORT` 覆盖；如已通过环境变量调整 API 目标或端口，以实际输出和配置为准。

### 接入 AI 开发环境

环境接入的完整流程包含四项工作：**环境接入（取得源码、确认必需入口、部署薄 Skill） → 管辖配置 → Git Hook 部署 → 验证**。

将以下提示复制给你的 AI 开发环境（如 Trae、Cursor、ZCode 等）：

可复制给目标环境 AI 的提示：

> 请阅读 README，完成 LDVH 的环境接入、管辖配置、Git Hook 部署与验证，并如实报告已验证与未验证的范围。

执行该提示的 AI 请注意：权威流程不在本文件。取得并确认源码仓库后，先读取环境接入面附件；若源码 Helper launcher 尚未交付，如实交还迁移缺口并停止完整接入。入口已交付时，先经该 launcher 的 `read-action-template-candidates` 定位，再经 `read-action-template-content` 读取当次环境接入行动模板，照模板执行；
全部入口的调用契约以 `specs/attachments/09.Att.01-环境接入面.md` 当次内容为准；
薄 Skill 部署件必须与 canonical 模板 `skill/SKILL.md` 逐字节一致；目标项目必须按 02 建立或核验管辖配置并取得当次解析结果；承接 Git Gate 的 Git Hook 必须部署到目标 Git common-dir。环境接入、管辖配置、Git Hook 部署与验证都是完整接入的必需工作，不能二选一。

AI 完成部署后应提示你执行以下操作：

1. **确认技能已加载** — 在 AI 环境设置中确认已部署的 LDVH Skill 已启用，且其可见会话范围覆盖目标会话
2. **确认管辖成立** — 对目标工作对象执行当次管辖解析，确认配置来源、结果与范围
3. **验证真实递达** — 启动一次新会话，确认 AI 实际经路由取得 LDVH 规则引导与行动模板，而非来自历史上下文恢复（hydrate）
4. **验证最终闸门** — 在共享目标 common-dir 的主 worktree 与一个 linked worktree（存在时）中触发代表性真实 Git 事件，确认 Git Gate 分别绑定 actual worktree、当次 Index 与 commit message

一次 common-dir 部署覆盖主 worktree、现有 linked worktree 和以后新建的 linked worktree；新 linked worktree 不需要重复部署。纳入接入目标的独立 clone 因 common-dir 不同，必须单独部署和验证；未纳入目标时不要求为验收而创建 clone。仅完成文件复制或 Git Hook 静态部署不等于完整接入已经成立。

### 诊断已有工作区

源码模式 doctor 尚未交付；不得用当前依赖 distribution metadata 的 doctor 冒充。后续交付后，其实际源码入口与调用合同以 09.Att.01 为准。Doctor 只诊断当前源码仓库、显式工作区和已交付入口的静态状态，不扫描目标 AI 环境，也不证明环境已经接入或完成真实验证。

---

## 为什么需要 LDVH？

AI 在长期项目中常见的问题：

- **上下文断裂** — 新会话丢失了之前的判断和决策，需要重复讨论
- **经验丢失** — 踩过的坑没有记录，下次可能再犯
- **行动不可追溯** — 不清楚某个决定是怎么做出的，依据是什么
- **跨环境不一致** — 在不同 AI 开发环境中行为不同

LDVH 通过以下方式解决：

| 机制 | 作用 |
|---|---|
| **规范（Specs）** | 定义项目规则、事实类型和行动模板，作为 AI 行为的权威依据 |
| **事实对象（Fact Objects）** | 结构化记录决策（ADR）、失败经验（Pitfall）、待处理问题（Spark）、研究报告（Study）和工作项（WorkCase） |
| **薄 Skill** | 把落入 LDVH 领域的工作路由至 Helper CLI，AI 按需取得规则引导与行动模板 |
| **Helper CLI** | 提供可审计的只读查询和受控写入操作 |
| **Git Hook 与 Git Gate** | Git Hook 是完整接入必部署的 Git 原生事件入口；Git Gate 是其在真实 commit 中按 actual worktree、Index 与 message 执行的最终机械检查 |
| **Web** | 面向 Human 如实呈现当前来源、状态、待决定事项和可核查节点，不建立第二事实源 |

---

## 项目结构

```
├── code/               # 确定性执行层：Helper CLI、Git Gate
├── web/                # 面向 Human 的 Web 交互层
├── ldvh-base/          # 事实对象载体（ADR、Pitfall、Spark、Study、WorkCase）
├── specs/              # 规则、事实类型定义和行动模板
└── README.md
```

---

## 核心概念

### 规范驱动

所有行为由 `specs/` 下的规范文件定义，而非硬编码逻辑。规范文件是 AI 行为的权威来源。

### 事实对象

| 类型 | 用途 | 状态 |
|---|---|---|
| **ADR** | 架构决策记录 | active → retired |
| **Pitfall** | 踩坑经验与规避方法 | active → retired |
| **Spark** | 待处理的议题或缺口 | open → routed / implemented / discarded |
| **Study** | 研究报告 | active → retired |
| **WorkCase** | 有明确验收标准的工作项 | open → blocked / closed |

### 环境无关设计

LDVH 核心是环境无关的——它不绑定任何特定 AI 开发环境。源码仓库是能力本体，不需要把 LDVH 打成 Python 包。每个环境的 AI 接入只通过薄 Skill 实现：一个只含路由信息的轻量技能文件（canonical 来源为 `skill/SKILL.md`），把落入 LDVH 领域的工作引导至仓库中的 Helper CLI。完整接入还必须按 02 建立或核验管辖配置，并部署承接 Git Gate 的 Git Hook：它以 Git common-dir 为部署边界，但每次真实事件仍独立绑定实际 worktree、当次 Index 与 commit message。四项工作均需要独立验证。

---

## 详细文档

- [环境接入、管辖配置、Git Hook 部署与验证行动模板](specs/33-环境接入行动模板.md) — 给 AI 的最简提示、四项工作、执行步骤与授权
- [环境接入规范](specs/09-环境接入规范.md) — 接入成立条件和验证边界
- [环境接入面](specs/attachments/09.Att.01-环境接入面.md) — 源码仓库交付的环境无关入口与接入资产
- [事实模型基础规范](specs/05-事实模型基础规范.md) — 事实对象的完整 Schema 和生命周期

---

## 许可证

本项目采用 [MIT License](LICENSE)。
