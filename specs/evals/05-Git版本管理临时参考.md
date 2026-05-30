# LD Vibe Harness Git 版本管理临时参考

> 创建日期：2026-05-30
> 状态：内部调研 / 临时参考
> 编号归属：70-89 内部调研
> 调研边界：不直接构成强制规则
> 执行效力：无，结论需进入 01-69 正式规范区间或 ADR 后才成为稳定规则
> AI 执行边界：本文是临时参考，不授权 AI 据此自动执行 commit、push、tag、release 或分支切换
> 来源：`trae-pm-kit/references/16-LD-Vibe-Harness-Git版本管理架构与迁移计划.md`
> 上位依据：`specs/00-LD-Vibe-Harness理念与纲要.md`
> 相关规范：`specs/01-specs文档结构规范.md`、`specs/02-LDVH目录说明.md`、`specs/03-事实源边界与承载规范.md`

---

## 一、本文解决的问题

本文是内部调研和临时参考，不直接构成当前 LD Vibe Harness 的执行规则；其中涉及分支、提交、tag、release、日志方案和迁移流程的内容，需在后续进入正式规范或 ADR 后才成为稳定规则。

---

## 二、来源文档核心判断

来源文档提出的核心原则如下：

| 原则 | 含义 |
|---|---|
| Git commit 就是日志 | 变更记录优先依赖 git log、commit message 和 diff |
| 人管推送和版本 | push、tag、release 由人确认和执行，AI 不自动推送 |
| 发布有节奏 | main 保持里程碑级历史，日常零碎提交在 dev 上沉淀 |
| main 对外干净 | 外部用户默认查看 main，main 历史应尽量保持清晰 |

该判断的核心价值，是把“日常开发过程”和“对外发布历史”分离：dev 可以承载高频迭代，main 只呈现阶段性成果。

---

## 三、核心认知：版本是标签，不是容器

来源文档强调：版本不是把 commit 放进一个容器，而是在某个 commit 上贴一个 tag。

```text
v0.1.0                              v0.2.0                              v0.3.0
  │                                    │                                    │
  ●────●────●────●────●────●────●────●────●────●────●────●────●────●────●
  │    │    │    │    │    │    │    │    │    │    │    │    │    │    │
  │   feat  fix  docs feat spec feat  │   fix  feat feat fix  │   feat spec feat
  │                                    │                        │
  │←── 这些 commit 都属于 v0.2.0 ──→│                        │
  │                                    │←── 这些属于 v0.3.0 ──→│
```

commit 是连续演进的项目历史，tag 是人选择某个稳定时刻后贴上的版本标识。

---

## 四、main + dev 双分支策略

### 4.1 分支分工

| 分支 | 定位 | commit 形态 | push 策略 | tag 策略 |
|---|---|---|---|---|
| `main` | 对外发布分支 | 里程碑级，一个版本一个主要节点 | 里程碑时推送 | 只在 main 打 tag |
| `dev` | 日常开发分支 | 零碎提交，可细可乱 | 可推可不推 | 不打 tag |
| `feature/*` | 可选的大功能分支 | 从 dev 拉出，完成后回 dev | 按需 | 不打 tag |
| `hotfix/*` | 可选的紧急修复分支 | 短期存在 | 按需 | 合入 main 后再判断 |

### 4.2 分支关系示意

```text
dev:  ●──●──●──●──●──●──●──●──●──●──●──●──●
                  │                    │
main:             ●────────────────────●
                  v0.0.1               v0.1.0
```

main 的外部历史应尽量呈现为：

```text
b7e4d2a  feat: 迁移规范体系、规则文件和 Web 工具  (v0.1.0)
a1b2c3d  chore: 初始化项目                        (v0.0.1)
```

### 4.3 里程碑合并流程

```bash
git checkout dev
git add .
git commit -m "feat(xxx): 最后一个零碎提交"

git checkout main
git merge --squash dev
git commit -m "feat: 迁移规范体系、规则文件和 Web 工具"
git tag -a v0.1.0 -m "release: v0.1.0 迁移核心内容"
git push origin main
git push origin v0.1.0

git checkout dev
```

该流程的重点是：dev 承载过程，main 承载阶段性结果，tag 由人确认后创建。

---

## 五、提交规范参考

来源文档建议使用 Conventional Commits。

### 5.1 提交格式

```text
<type>(<scope>): <description>

[可选 body]

[可选 footer]
```

### 5.2 Type 参考

| Type | 含义 | 语义化版本影响 |
|---|---|---|
| `feat` | 新功能、新规范、新工具 | MINOR |
| `fix` | 修复 bug 或规范错误 | PATCH |
| `docs` | 文档变更 | 无 |
| `refactor` | 重构，不改变行为 | 无 |
| `spec` | 规范体系变更 | MINOR 或 PATCH |
| `tool` | 工具代码变更 | MINOR 或 PATCH |
| `chore` | 构建、配置、依赖等杂项 | 无 |

### 5.3 Scope 参考

| Scope | 对应目录或模块 |
|---|---|
| `specs` | 规范文档 |
| `rules` | 规则文件 |
| `skills` | Skill 定义 |
| `agents` | Agent 定义 |
| `web` | Web 工具 |
| `core` | 核心框架 |
| `infra` | 项目基础设施 |

### 5.4 示例

```text
feat(specs): 新增事实源治理规范
fix(web): 修复任务列表分页显示错误
spec(rules): 调整 L1 规则读取机制
tool(web): 新增备忘批量导出功能
docs: 更新 README 产品定义
chore(infra): 配置 GitHub Actions 发布流程
```

---

## 六、版本管理参考

### 6.1 语义化版本

```text
MAJOR.MINOR.PATCH
```

| 变更类型 | 版本升级 | 示例 |
|---|---|---|
| 不兼容的规范或架构变更 | MAJOR | 1.x → 2.0 |
| 向后兼容的新功能或新规范 | MINOR | 1.0 → 1.1 |
| 向后兼容的修复 | PATCH | 1.0.0 → 1.0.1 |

### 6.2 Git Tag 规则参考

| 规则 | 说明 |
|---|---|
| 只在 main 上打 tag | tag 对应对外发布节点 |
| tag 由人手动创建和推送 | AI 不自动推送版本 |
| tag 不覆盖 | 打错后用新的 patch 修正 |

### 6.3 从 tag 获取版本号

```bash
git describe --tags --abbrev=0
git describe --tags
```

Python 示例：

```python
import subprocess


def get_version():
    try:
        return subprocess.check_output(
            ["git", "describe", "--tags", "--abbrev=0"],
            stderr=subprocess.DEVNULL,
        ).decode().strip().lstrip("v")
    except subprocess.CalledProcessError:
        return "dev"
```

### 6.4 版本节奏参考

| 版本 | 含义 |
|---|---|
| `v0.0.1` | 项目初始化 |
| `v0.1.0` | 迁移核心内容完成 |
| `v0.x.x` | 早期开发阶段，不承诺稳定 |
| `v1.0.0` | 第一个稳定版本 |
| `v1.x.0` | 增量迭代 |
| `v1.x.y` | 小修小补 |
| `v2.0.0` | 大版本重构 |

---

## 七、零碎提交转为版本的过程参考

### 7.1 日常开发

```bash
git checkout dev

git add .
git commit -m "feat(web): 新增任务看板视图"
git commit -m "fix(web): 修复列表排序错误"
git commit -m "docs: 更新安装说明"
git commit -m "feat(specs): 新增 AI 协作规范"
git commit -m "fix(rules): 修正 L1 规则路径"
```

### 7.2 查看累计改动

```bash
git checkout dev
git log v0.0.1..HEAD --oneline
```

### 7.3 合并到 main 并打版本

```bash
git checkout main
git merge --squash dev
git commit -m "feat: 新增看板视图、协作规范，修复排序和路径问题"
git tag -a v0.1.0 -m "release: v0.1.0 迁移核心内容"
git push origin main
git push origin v0.1.0
git checkout dev
```

---

## 八、发布流程参考

### 8.1 tag 到 GitHub Release

```bash
git tag -a v1.0.0 -m "release: v1.0.0 第一个稳定版本"
git push origin v1.0.0
```

之后可在 GitHub 仓库页面基于 tag 创建 Release。

### 8.2 Release Notes 生成

```bash
git log v0.2.0..v1.0.0 --pretty=format:"- %s"
```

Release Notes 参考结构：

```text
## v1.0.0 (2026-05-29)

### 新功能
- feat(web): 新增任务看板视图
- feat(specs): 新增 AI 协作规范

### 修复
- fix(web): 修复任务列表排序错误

### 规范变更
- spec(specs): 调整事实源治理规范

### 破坏性变更
- 无
```

---

## 九、日志方案参考

来源文档提出：git log 可作为 changelog 的主要来源。

| 需求 | 命令 |
|---|---|
| 查看某版本变更 | `git log v1.0.0..v1.1.0 --oneline` |
| 查看某模块变更 | `git log --oneline -- specs/` |
| 查看某类型变更 | `git log --oneline --grep="^feat"` |
| 查看完整 changelog | `git log v1.0.0..v1.1.0 --pretty=format:"- %s"` |
| 查看某文件历史 | `git log --oneline -- web/server.py` |
| 查看某次 commit 详情 | `git show abc1234` |

当前 LD Vibe Harness 是否采用“只以 git log 作为变更记录”的方式，需要后续结合现有事实源和 Change 记录实践另行决策。

---

## 十、目录结构与 Git scope 参考

| 目录 | 建议 commit scope |
|---|---|
| `specs/` | `specs` |
| `rules/` | `rules` |
| `skills/` | `skills` |
| `agents/` | `agents` |
| `web/` | `web` |
| `core/` | `core` |
| `references/` | `docs` |
| `docs/` | `docs` |
| `ldvh-base/` | `base` |
| `README.md` | `docs` |
| `.gitignore` | `infra` |

---

## 十一、迁移计划参考

来源文档建议 LD Vibe Harness 作为新 repo 干净起步，旧 repo 归档保留。

| 旧项目内容 | 迁移判断 | 说明 |
|---|---|---|
| `specs/` | 迁移并重组 | 核心规范体系 |
| `specs-v2/` | 迁移并重组 | 新版规范，可作为重构来源 |
| `pm-kit-web/` | 迁移 | Web 工具可改名为 `web/` |
| `references/` | 选择性迁移 | 按需迁移参考资料 |
| `docs/` | 选择性迁移 | PM Kit 产品需求不迁 |
| `pm-kit-base/` | 部分迁移 | ADR 按需迁移，过程性对象慎迁 |
| `product.yaml` | 迁移并改写 | 更新品牌定义 |
| `.trae/rules/` | 迁移并改写 | 更新项目规则 |
| `plan/` | 不迁移 | 过程性材料留在旧 repo |

来源文档中的迁移步骤包括：初始化 main 并打 `v0.0.1`、创建 dev 承载零碎迁移、阶段性 squash merge 到 main 并打 `v0.1.0`、后续继续迭代。

---

## 十二、Git 基础概念速查

| 概念 | 理解方式 |
|---|---|
| commit | 一次快照，记录某个时刻所有文件状态 |
| branch | 指向某个 commit 的可移动指针 |
| tag | 指向某个 commit 的固定标签 |
| merge | 把两个分支的改动合在一起 |
| squash merge | 把一个分支上的多个 commit 压成一个再合入 |
| rebase | 把一组 commit 挪到另一个基点上 |
| remote | 远程仓库引用 |
| push | 把本地 commit 推送到远程 |
| pull | 从远程拉取 commit 到本地 |

常用命令：

```bash
git status
git log --oneline
git log --oneline --graph
git log --oneline -- path/to/file
git show <commit-hash>
git tag -l
git show v0.2.0
git branch
git checkout dev
git checkout main
git checkout -b dev
git reset --soft HEAD~1
git reset --hard HEAD~1
git commit --amend -m "新的 message"
```

---

## 十三、.gitignore 参考

```text
# Python
__pycache__/
*.pyc
*.pyo
.venv/
venv/

# Node
node_modules/

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db

# Runtime
*.pid
*.log

# Environment
.env
.env.local
```

---

## 十四、Human Gate 与检查要求

以下情况若发生，建议评估 Human Gate：

1. 将本文内容升级为正式 Git 版本管理规范；
2. 改变 LD Vibe Harness 当前分支策略、tag 策略或发布策略；
3. 取消或替换现有 Change 记录实践；
4. 将 push、tag、release 等远程操作交由 AI 自动执行；
5. 改变 `main`、`dev` 或远程仓库的使用约定。

检查项：

| 检查项 | 标准 |
|---|---|
| 临时性 | 已标记为内部调研 / 临时参考 |
| main/dev 保留 | 已保留 main + dev 双分支策略内容 |
| 规则升级 | 未直接升级为正式执行规则 |
| 远程操作 | 未要求 AI 自动 push、tag 或 release |
| 来源追踪 | 已记录来源文档路径 |

---

## 十五、待补齐事项

1. 是否将 main + dev 双分支策略升级为正式规范，待 Git 管理实践稳定后决定；
2. 是否继续维护 Change YAML 与 git log 的关系，待事实源治理进一步评估；
3. 是否新增 04-07 或 40-69 中的 Git 行动模型规则，待行动模型规范重构时确定；
4. 是否创建 ADR 固化 Git 版本管理决策，待用户确认。