# LDVH V4

LDVH（LD Vibe Harness）帮助 AI 在长期项目中保持判断有据、行动可续、结果可验。它由规范、事实对象与行动模板构成，并通过 Helper CLI、环境 Hook 和 Web 交付。

## 安装 LDVH 核心

交付到新环境时，请提供固定的发行版本或 Git commit、LDVH 根目录、目标工作区和工作对象的绝对路径；不要把含未提交改动的工作目录作为交付版本。

在该固定版本的项目目录中安装核心：

```bash
python3.12 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/ldvh capabilities
```

`ldvh capabilities` 用于发现当前公开能力。安装核心不等于已经将 LDVH 接入目标开发环境。

## 启动 Web（本地开发）

需要 Node.js 与 npm。在仓库根目录执行：

```bash
cd web
npm ci
npm run dev
```

按当前本地开发脚本，前端固定监听 [http://127.0.0.1:5173](http://127.0.0.1:5173)；端口被占用时会启动失败。本地 API 默认使用 `3001`，可由 `PORT` 覆盖；如已通过环境变量调整 API 目标或端口，以实际输出和配置为准。

## 接入新的开发环境

环境接入的完整流程是：获取核心 → 安装 → 部署 → 接入 → 验证。安装只取得核心；部署将既有接入单元和配置放到位；接入才是原生事件连接既有入口；验证需要对应真实事件的证据。

可复制给目标环境 AI 的提示：

> 请阅读 README，完成 LDVH 的安装、部署、接入与验证，并如实报告已验证与未验证的范围。

详细规则不在 README 重复：

- [环境安装、部署、接入与验证行动模板](specs/33-环境安装、部署、接入与验证行动模板.md)：给 AI 的最简提示、执行步骤、授权、逐事件验证与交还。
- [环境接入规范](specs/09-环境接入规范.md)：接入成立条件和验证边界。
- [环境接入面](specs/attachments/09.Att.01-环境接入面.md)：当前发行物已交付的环境无关入口。

## 诊断已有工作区（可选）

`ldvh-doctor` 必须显式传入管辖配置所在工作区、目标项目或 worktree，以及 Helper 可执行文件的绝对路径：

```bash
.venv/bin/ldvh-doctor \
  --workspace-root "<管辖配置所在工作区的绝对路径>" \
  --work-object-locator "<目标项目或 worktree 的绝对路径>" \
  --helper-executable "<LDVH_ROOT>/.venv/bin/ldvh"
```

Doctor 只诊断当前发行物、显式工作区和已交付入口的静态状态；它不扫描目标 AI 环境，也不证明环境已经接入、自动触发或完成真实验证。

## 项目地图与构建

- `code/`：确定性执行层，包括 Helper CLI、Hook 和 Git Gate。
- `web/`：面向 Human 的 Web 交互层。
- `ldvh-base/`：V4 事实对象载体。
- `specs/`：规则、事实类型和行动模板。

构建 Python 发行物：

```bash
python3.12 -m pip install -e '.[dev]'
python3.12 -m build --sdist --wheel
```
