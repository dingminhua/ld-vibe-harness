# LDVH — LD Vibe Harness

LDVH 以 AI 执行者为第一服务对象，帮助 AI 在长期项目中保持**判断有据、行动可续、结果可验**；同时直接服务 Human，使决策提请清晰可决、授权执行受控可续、入档闭环节点可验，并让项目演进脉络可循。积累效用如何直观可见仍是当前明确待加强的能力，不因事实对象、提交或页面存在就宣称已经实现。

它由规范（Specs）、事实对象（Fact Objects）与行动模板（Action Templates）构成，通过薄 Skill、Helper CLI、Git Gate 和 Web 界面交付，适用于需要 AI 跨会话保持一致、Human 返回后能够核查并接续，以及在不同 AI 开发环境中复用规则的长期项目。

---

## 快速开始

### 安装

核心只安装在仓库根的 `.venv`，一台机器一份，所有 AI 环境共用。先检查是否已安装：

```bash
.venv/bin/ldvh capabilities
```

能返回公开操作清单且确认 editable 指向本仓库、git pull 后 pyproject 未变，即安装有效，直接进入验证；否则执行：

```bash
python3.12 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/ldvh capabilities
```

`ldvh capabilities` 用于发现当前公开能力。安装核心不等于已经将 LDVH 接入目标开发环境。

当前已验证平台为 macOS；Windows 下 venv 入口位于 `.venv\Scripts\`，相关路径尚未实测，按未验证范围处理。

### 更新

`git pull` 后在任一已接入环境告诉 AI「LDVH 更新了」即可：由 AI 按下述规则判断变化类型、只执行必要动作（重装核心或重放部署件），并完成重验。手动判断时遵循：规范与规则源更新不需要任何环境侧动作（薄 Skill 现取现用）；以下三类变化需要处理：

- `pyproject.toml` 变化（依赖或入口）：重跑 `.venv/bin/pip install -e '.[dev]'`；
- `skill/SKILL.md`、CLI 入口或 Git Gate 安装器变化：将各环境部署件与新模板逐字节比对，过期者重新部署；
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

环境接入的完整流程：**获取核心 → 安装 → 部署 → 接入 → 验证**。

将以下提示复制给你的 AI 开发环境（如 Trae、Cursor、ZCode 等）：

可复制给目标环境 AI 的提示：

> 请阅读 README，完成 LDVH 的安装、部署、接入与验证，并如实报告已验证与未验证的范围。

执行该提示的 AI 请注意：权威流程不在本文件。安装核心后，先经
`ldvh call read-action-template-candidates` 定位，再经
`ldvh call read-action-template-content` 读取当次环境接入行动模板，照模板执行；
全部入口的调用契约以 `specs/attachments/09.Att.01-环境接入面.md` 当次内容为准；
薄 Skill 部署件必须与 canonical 模板 `skill/SKILL.md` 逐字节一致。

AI 完成安装后应提示你执行以下操作：

1. **确认技能已加载** — 在 AI 环境设置中确认已部署的 LDVH Skill 已启用，且其可见会话范围覆盖目标会话
2. **验证真实递达** — 启动一次新会话，确认 AI 实际经路由取得 LDVH 规则引导与行动模板，而非来自历史上下文恢复（hydrate）

仅完成文件安装和部署不等于 Skill 已被环境加载。

### 诊断已有工作区

```bash
.venv/bin/ldvh-doctor \
  --workspace-root "<管辖配置所在工作区的绝对路径>" \
  --work-object-locator "<目标项目或 worktree 的绝对路径>" \
  --helper-executable "<LDVH_ROOT>/.venv/bin/ldvh"
```

Doctor 只诊断当前发行物、显式工作区和已交付入口的静态状态，不扫描目标 AI 环境，也不证明环境已经接入或完成真实验证。

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
| **Git Gate** | 在 commit 时自动校验提交信息是否符合项目规范 |
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

LDVH 核心是环境无关的——它不绑定任何特定 AI 开发环境。每个环境的接入通过薄 Skill 实现：一个只含路由信息的轻量技能文件（canonical 来源为 `skill/SKILL.md`），把落入 LDVH 领域的工作引导至 Helper CLI；提交把关由 Git Gate 在受管辖 worktree 中承接。

---

## 构建发行物

```bash
python3.12 -m pip install -e '.[dev]'
python3.12 -m build --sdist --wheel
```

---

## 详细文档

- [环境安装、部署、接入与验证行动模板](specs/33-环境安装、部署、接入与验证行动模板.md) — 给 AI 的最简提示、执行步骤与授权
- [环境接入规范](specs/09-环境接入规范.md) — 接入成立条件和验证边界
- [环境接入面](specs/attachments/09.Att.01-环境接入面.md) — 当前发行物已交付的环境无关入口
- [事实模型基础规范](specs/05-事实模型基础规范.md) — 事实对象的完整 Schema 和生命周期

---

## 许可证

本项目采用 [MIT License](LICENSE)。
