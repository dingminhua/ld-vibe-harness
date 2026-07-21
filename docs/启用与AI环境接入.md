# LDVH 启用与 AI 环境接入

本文是用户和目标环境 AI 共用的环境无关指南。目标流程是：

> 获取 → 安装 → 配置 → 接入 → 验证

本文不提供厂商候选清单或固定厂商步骤。具体 AI 开发环境的协议、权限和安装位置必须在实际任务中依据当前官方或实际权威资料确认。

## 1. 获取

当前仓库没有声明已经发布到公共 Python registry。可以从当前源码构建本地发行物：

```bash
python3.12 -m pip install -e '.[dev]'
python3.12 -m build --sdist --wheel
python3.12 - <<'PY'
from hashlib import sha256
from pathlib import Path

for path in sorted(Path("dist").iterdir()):
    if path.is_file():
        print(f"{sha256(path.read_bytes()).hexdigest()}  {path}")
PY
```

记录源码 revision、包版本、artifact 文件名和 SHA-256。`pyproject.toml` 当前声明 Python `>=3.12`，运行依赖为 `ruamel.yaml>=0.18.10,<0.19`。构建工具和运行依赖通常需要从已配置的 Python 包源取得；本地 wheel 不等于已经包含全部依赖，也不构成离线安装声明。

## 2. 安装

优先安装到独立虚拟环境：

```bash
python3.12 -m venv .venv-ldvh
.venv-ldvh/bin/python -m pip install dist/ld_vibe_harness-0.1.0-py3-none-any.whl
.venv-ldvh/bin/ldvh capabilities
```

Windows 使用 `.venv-ldvh\Scripts\python.exe` 和对应 `.exe` 入口。安装成功只证明 Python distribution 和 console entry point 存在，不证明任何 AI 开发环境已经接入。

## 3. 配置

LDVH 使用显式 workspace root 和其中的 `LDVH-GOVERNED-PROJECTS.yaml` 解析管辖项目。最小结构由 `specs/02-工作对象与管辖范围规范.md` 和附件定义，例如：

```yaml
product_name: My Workspace
product_description: Projects governed in this workspace.
projects:
  - id: my-project
    path: /absolute/path/to/my-project
    name: My Project
    description: The governed project.
```

配置写入是独立副作用；只在用户明确要求并确认目标内容后执行。本指南和 doctor 都不会自动登记项目。

先运行只读诊断：

```bash
.venv-ldvh/bin/ldvh-doctor \
  --workspace-root /absolute/path/to/workspace \
  --work-object-locator /absolute/path/to/my-project \
  --helper-executable /absolute/path/to/.venv-ldvh/bin/ldvh
```

`ready` 只表示 LDVH 自有入口、显式配置和当前管辖检查成立；`attention` 表示诊断完成但存在缺口；二者都不证明目标 AI 开发环境已经接入。

## 4. 接入

把以下任务交给目标 AI 开发环境中的 AI：

```text
请只读研究当前 AI 开发环境的官方或实际权威资料，并记录资料 URL/稳定定位、观察时间、
产品版本、平台和账号/权限范围。按功能确认是否存在能够自动触发外部命令或扩展、传递当前
工作对象所需输入、并把完整结果或可回查诊断反馈给 AI/Human 的机制；不要只搜索 “Hook”
这个名称。然后对照 docs/LDVH接入面.md：
1. 判断原生事件是否与某个既有 LDVH 入口语义对应；
2. 列出实际输入、输出、partial/error、超时、权限、用户资产和回滚；
3. 若可直接配置到既有入口，形成精确安装方案并在写入前请求 Human Gate；
4. 若必须新增 manifest、启动脚本或薄 adapter，停止安装，先形成独立 Code 计划；
5. 若资料或权限不足，保持 unverified；只有肯定依据证明所需自动机制不存在时，才报告
   完整接入 unsupported；
6. 不修改 LDVH 规则、Helper 字段、事实 Schema，不把 fixture 或 shell 直调当成真实触发。
```

### 能力状态

| 当前依据 | 状态 |
|---|---|
| 尚未调查、资料未找到、版本不明、权限不足或不可观察 | `unverified` |
| 找到候选自动机制，但尚未安装或真实触发 | `unverified` |
| 权威资料或范围匹配的实际观察肯定证明不存在能承接必需输入与反馈的自动机制 | `unsupported` |
| 静态安装或核心直调通过，但没有真实环境事件 | 对应子范围已观察；完整接入仍为 `unverified` |
| 代表性真实事件自动进入同一 LDVH 入口，成功和主要失败路径均有当次证据 | 只对当次环境、版本、入口、事件和工作对象声明 verified |

`partial` 只能说明已完成的子范围，不能覆盖 `unsupported` 或 `unverified`。

### 两条接入分支

直接配置分支要求目标环境已经能够把原生机制指向[现有 LDVH 接入面](LDVH接入面.md)，且无需创建新的 manifest、脚本或 adapter。写入前按 `specs/33-环境接入安装与验证行动模板.md` 检查用户资产、权限、净变化和回滚，并取得所需 Human Gate。

新 adapter 分支不属于安装动作。先依据具体环境资料和 `specs/07-Code 实践与测试规范.md` 建立独立 Code 计划，完成实现、tests 和可安装对象；之后再回到 33 执行安装验证。

## 5. 验证

验证必须分层，前一层不能替代后一层：

1. 静态安装：包、入口、manifest、Hook 或配置可回读。
2. LDVH 核心直调：实际适用的 Helper、共享行为或机械 Gate 对明确输入返回当前合同结果。
3. adapter/薄引用检查：只证明受测映射和 fixture，不证明真实环境事件。
4. 真实自动触发：目标环境的代表事件自动调用同一 LDVH 入口，并忠实返回成功、`partial`、错误或 allow/block。
5. 失败和降级：至少验证一个与主要风险匹配的输入不足、调用失败或能力差异路径。
6. 禁用和回滚：目标环境不再自动调用，或恢复到变更前连接；无关用户资产未受损，残留明确。

无法启动目标环境、需要重启/信任/UI 操作或只能由用户观察时，AI 应交还最小恢复断点：环境与版本、用户动作、正常表现、需要返回的原始结果、复跑入口和未验证范围。没有真实触发证据时，不得声明完整接入完成。

## 卸载 LDVH Python distribution

```bash
.venv-ldvh/bin/python -m pip uninstall -y ld-vibe-harness
```

这只卸载 Python distribution。具体环境中已经安装的 manifest、Hook、插件或 adapter 必须按其安装前基线和 `specs/33` 单独禁用、卸载或回滚；不能从 pip 卸载成功推断环境连接已经移除。
