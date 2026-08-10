---
title: 跨平台变更传播与再验证纪律：规则落点与触发机制设计
status: active
report_kind: technical_assessment
research_question: 在 LDVH 走向 macOS+Windows 双平台支持后，当任一平台侧改动触及平台相关面时，另一侧平台的已验证声明应如何失效并触发范围匹配重验或回退 unverified，以及该纪律的规则落点、清单界定、触发机制、测试/CI 方案与验收矩阵应如何设计？
abstract: 本报告为 spark-0057 议题的全面调研，围绕「跨平台变更传播与再验证纪律」的五个核心问题——规则落点（09 环境接入 vs 07 Code 实践）、平台相关面清单界定标准与防腐机制、重验触发机制（含 Git Gate 可行性边界）、测试/CI 最小方案、与 spark-0004 验收矩阵的衔接——逐项给出判断与设计建议。核心结论：触发规则落点应为 09 §6 平台声明生命周期，不新增独立规范；清单界定标准为「路径/平台抽象层/平台条件分支，且改动可能改变另一侧平台上的行为语义」，以机械扫描 + AI 复核双轨防腐；重验触发采用 Git Gate 路径匹配 + AI 语义判断的分级机制；测试以 CI matrix 为主、Windows 本地跑为辅的最小方案。报告同时给出可直接进入规范修订的最小增量草案。
research_intent: spark-0057 以「修订漂移使跨平台验证失效」为缺口保留议题，要求判断规则落点（09 环境接入的平台声明生命周期 vs 07 Code 平台相关面工程约束）、平台相关面清单如何界定、重验范围如何分级、纪律如何进入 spark-0004 验收矩阵。本研究为 spark-0057 的收敛提供完整调研基础，使后续规范修订与 WorkCase 创建有据可依。
recommendation_summary: 建议规则落点放在 09 §6，在 09 §6.3 中新增「平台声明生命周期」条款，07 仅增加一条回指引用；平台相关面清单以「路径/平台抽象函数/平台条件分支」为机械扫描标准，以 AI 复核擅入检查为语义过滤；重验触发采用 Git Gate 路径匹配拦截 + message 声明格式的分级机制；测试采用 CI matrix（macOS + Windows）为主、Windows 本地验收跑为辅；验收面在 spark-0004 中新增「跨平台变更传播后重验」验收行。方案已成熟可直接进入规范修订，但需 Human 授权后按 01 §13.6 顺序执行。
relations:
- relation_key: inspired-by
  target:
    governed_project_id: ldvh
    fact_type_key: spark
    object_id: spark-0057
- relation_key: informs
  target:
    governed_project_id: ldvh
    fact_type_key: spark
    object_id: spark-0057
- relation_key: informs
  target:
    governed_project_id: ldvh
    fact_type_key: spark
    object_id: spark-0004
input_refs:
- kind: specification
  locator: specs/01-规范模型基础规范.md
  version: cb03dc809
  observed_at: '2026-08-06T01:00:00+08:00'
- kind: specification
  locator: specs/05-事实模型基础规范.md
  version: cb03dc809
  observed_at: '2026-08-06T01:00:00+08:00'
- kind: specification
  locator: specs/07-Code 实践与测试规范.md
  version: cb03dc809
  observed_at: '2026-08-06T01:00:00+08:00'
- kind: specification
  locator: specs/09-环境接入规范.md
  version: cb03dc809
  observed_at: '2026-08-06T01:00:00+08:00'
- kind: specification
  locator: specs/24-Study-研究报告.md
  version: cb03dc809
  observed_at: '2026-08-06T01:00:00+08:00'
- kind: fact-objects
  locator: ldvh-base/sparks/spark-0004.yaml
  version: cb03dc809
  observed_at: '2026-08-06T01:00:00+08:00'
- kind: fact-objects
  locator: ldvh-base/sparks/spark-0057.yaml
  version: cb03dc809
  observed_at: '2026-08-06T01:00:00+08:00'
- kind: fact-objects
  locator: ldvh-base/sparks/spark-0022.yaml
  version: cb03dc809
  observed_at: '2026-08-06T01:00:00+08:00'
- kind: code-analysis
  locator: code/ldvh/filesystem.py
  version: cb03dc809
  observed_at: '2026-08-06T01:05:00+08:00'
- kind: code-analysis
  locator: code/ldvh/governance/git.py
  version: cb03dc809
  observed_at: '2026-08-06T01:05:00+08:00'
- kind: code-analysis
  locator: code/ldvh/testing/test_runs.py
  version: cb03dc809
  observed_at: '2026-08-06T01:05:00+08:00'
- kind: code-analysis
  locator: code/tests/platform/test_native_windows.py
  version: cb03dc809
  observed_at: '2026-08-06T01:05:00+08:00'
change_log:
- signature:
    agent_id: GLM-5.2
    host_environment: Claude
  session_id: session-20260806-spark-0057-study
  at: '2026-08-06T01:29:48.505010+08:00'
  summary: Human 授权在 spark-0057 议题基础上完成跨平台变更传播与再验证纪律的全面调研；本 Study 将规范回读、代码扫描、归口判断与建议合并入档
- at: '2026-08-10T08:49:02.679904Z'
  summary: '受控更正历史 change_log 中的 agent_workbench 格式；修复项为 0: claude-code-mcp -> Claude。原始错误值已由本次更正覆盖并保留本条修复记录。'
  signature:
    agent_workbench: Cindy
    model_id: gpt-5
  session_id: cindy-legacy-signature-migration-20260810

object_id: study-0024
fact_type_key: study
created_at: '2026-08-06T01:29:48.505010+08:00'
updated_at: '2026-08-10T08:49:02.679904Z'
---

## 研究问题

本报告为 spark-0057 议题的全面技术调研。核心问题：在 LDVH 走向 macOS+Windows 双平台支持后，当任一平台侧改动触及平台相关面时，另一侧平台的已验证声明应如何失效并触发范围匹配重验或回退 unverified？具体需要回答五个子问题：

1. **规则落点**：「改动触及平台相关面 → 另一侧平台验证声明失效、须范围匹配重验或回退 unverified」这条触发规则应放 09（环境接入的平台声明生命周期）还是 07（Code 平台相关面工程约束），还是拆分两处？按 01 §13.1 给出归口判断记录。
2. **平台相关面清单**：当前实测为 `code/ldvh/filesystem.py`、`code/ldvh/governance/git.py`、`code/ldvh/testing/test_runs.py` + 根 `ldvh` launcher + `git_hooks/`。给出清单的界定标准（什么算平台相关面）与防腐机制（清单如何不随代码演进失真，可否机械扫描）。
3. **重验触发机制**：改动触及清单内文件时如何回退/重验？Git Gate 做机械路径匹配是否可行、边界在哪（语义判断归 AI/Human）？message 声明格式怎么约定？
4. **测试与 CI**：同一套测试两侧跑的最小方案（Windows 本地跑 vs CI matrix），mac 改动破坏 Windows 语义的探测面设计。
5. **与 spark-0004 验收矩阵的衔接**：「变更传播后重验」验收面怎么写。

## 输入与边界

### 输入来源

本报告依赖以下输入：

- `specs/01-规范模型基础规范.md`（§13 规范修订判断顺序、§13.1 固定判断顺序、§13.5 独立复核）
- `specs/05-事实模型基础规范.md`（§9.4 跨 clone 撞号处置规则、§11 受控创建契约）
- `specs/07-Code 实践与测试规范.md`（平台相关工程约束候选落点）
- `specs/09-环境接入规范.md`（§6 四项工作与变更计划边界、§6.3 已验证平台声明、§8 能力判定）
- `specs/24-Study-研究报告.md`（Study 类型定义与正文骨架）
- `ldvh-base/sparks/spark-0004.yaml`（原生 Windows 支持验收矩阵）
- `ldvh-base/sparks/spark-0057.yaml`（本议题对象）
- `ldvh-base/sparks/spark-0022.yaml`（撞号处置承接现状）
- `code/ldvh/filesystem.py`、`code/ldvh/governance/git.py`、`code/ldvh/testing/test_runs.py`（平台相关面代码扫描）
- `code/tests/platform/test_native_windows.py`（Windows 原生测试样例）

### 边界与排除

本报告不涉及以下内容：

- 跨 clone 事实对象身份冲突（已由 05 §9.4 承接）
- Windows 环境接入的具体部署流程（属于环境接入行动模板）
- 双平台分叉实现（已由 spark-0057 三层结论禁止）
- 新机械入口的设计与实现（只给出触发机制设计，不编写代码）

### 观察时点

所有代码与规范引用基于当前 working tree HEAD `cb03dc809`，观察时点 2026-08-06T01:00:00+08:00。

### 关键术语

- **平台相关面**：代码中因操作系统差异（macOS vs Windows）而行为不同，且改动可能改变另一侧平台上运行时语义的模块、入口或配置。
- **平台声明**：09 §6.3 末段「当前已验证平台为 macOS。其它平台（含 Windows）的仓库入口、运行依赖、路径写法与 Git Hook 执行能力按 §8 未验证范围处理」。
- **已验范围（verified）**：在目标平台实际跑通并有输出。
- **未验范围（unverified）**：尚未在目标平台实测或当前证据不足。
- **不支持（unsupported）**：权威资料或范围匹配观察肯定证明不存在所需能力。

## 关键发现

### 发现 1：规则落点应为 09 §6 平台声明生命周期

**按 01 §13.1 固定判断顺序的记录**

1. **约束对象**：受管辖项目在 09 §6.3 中声明的平台验证状态，因代码变更而失效时的处置规则。
2. **候选规则清单**：
   - R1：改动触及平台相关面清单时，受影响的另一侧平台验证声明失效、回退 unverified。
   - R2：重验通过后平台声明恢复 verified 或保持 unverified。
   - R3：平台相关面清单须随代码演进维护，以机械扫描 + AI 复核双轨防腐。
   - R4：提交 message 须声明受影响的平台验证范围。

3. **现有规范承载检查**：

   | 候选规则 | 00 承担 | 09 承担 | 07 承担 | 其它 |
   |---|---|---|---|---|
   | R1 声明失效触发 | 不承担具体触发规则 | 09 §6.3 已有「当前已验证平台为 macOS」静态声明，但无失效触发规则 | 07 有平台差异属测试选择因子（§6 风险选择），但无平台声明生命周期管理 | 缺口 |
   | R2 重验后恢复 | 00 §9 验证要求的一般原则 | 09 §10 验证表已有「验证对象」框架 | 07 §6 测试覆盖与验证 | 已有框架但未绑定到平台声明失效→恢复的具体闭环 |
   | R3 清单防腐 | 不承担 | 不承担 | 07 §5 模块责任、§6 测试映射可承载清单标准 | 05 事实模型不适用（清单不是事实对象） |
   | R4 message 声明 | 不承担 | 不承担 | 不承担 | 03 §9.3/§9.4 提交消息契约可扩展 |

4. **重复与实现细节移除**：R2 已由 09 §10 验证表和 07 §6 测试覆盖框架有原则性指导，不需要在本规则中完整重复验证流程，只须回指现有验证框架。

5. **承载位置比较（按 01 §13.3）**：

   | 候选内容 | 最适合位置 | 理由 |
   |---|---|---|
   | R1 触发规则：改动触及平台相关面 → 声明失效/unverified | 09 §6 作为「平台声明生命周期」条款 | 平台验证声明是环境接入声明的组成部分，09 §6.3 已是声明位置，生命周期管理应同处一处 |
   | R3 清单界定标准 | 07 §5 模块责任 | 清单界定哪些代码模块属于平台相关，本质是工程分类标准，归 07 Code 实践 |
   | R4 message 声明格式 | 03 §9.3/§9.4 提交消息契约 | message 格式是信息溯源契约的内容 |
   | 防腐机制（机械扫描规则） | 07 或 Git Gate 实现层 | 具体实现规则，不属规范正文 |

6. **独立规范判断**（按 01 §13.2）：不满足条件——候选规则在移除已有承担后，剩余独有规则（R1 触发规则 + R3 清单界定）不足以独立成立新规范。R1 适合放入 09 §6，R3 适合放入 07 §5。无需新建独立规范。

7. **结论**：R1（触发规则）落点为 09 §6，在「6.3 四项工作与变更计划」中新增「平台声明生命周期」子节；R3（清单界定标准）落点为 07 §5；R4（message 格式）留待 03 扩展。07 只增加一条回指引用 09 §6 的平台声明生命周期规则。

### 发现 2：平台相关面清单界定标准与防腐机制

**当前实测清单**（初始）：
- `code/ldvh/filesystem.py`——文件系统操作抽象层（路径、锁、原子写），包含显式 `os.name` 分支（posix/nt）
- `code/ldvh/governance/git.py`——Git 身份解析，含 `PureWindowsPath` 导入和 `platform_name` 参数
- `code/ldvh/testing/test_runs.py`——测试运行记录，依赖文件系统路径操作
- `ldvh`（根 launcher）——Python 入口，含 `.venv/Scripts/python.exe` Windows 候选路径
- `git_hooks/`——Git Hook 部署件，含 shell 脚本和路径引用

**界定标准**：

一条代码路径或模块属于「平台相关面」，当且仅当满足以下任一条件：
1. **路径抽象层**：直接调用 `os.name`、`sys.platform`、`platform.system()` 等平台判定 API，或包含 `posix`/`nt` 显式分支；
2. **平台原生调用**：直接调用 Windows API（`ctypes.windll`）、POSIX 特有系统调用（`os.fork`、`pty`）、或条件导入平台特有模块（`msvcrt`、`fcntl`）；
3. **路径语义依赖**：路径构造、规范化、大小写行为依赖操作系统路径语义（`Path`、`PureWindowsPath`、盘符、UNC）；
4. **入口与部署**：作为环境入口（launcher、shell 脚本、Hook 部署件）且其行为因 shell、换行、执行权限机制而不同；
5. **条件分支继承**：直接调用本条 1-4 范围内函数，且调用路径无法在编译/加载时消除，运行时行为因平台不同而不同。

**防腐机制**（双轨）：

- **机械扫描轨**：在 Git Gate 或 CI 中维护一份机械可执行的路径 glob 模式清单（如 `code/ldvh/filesystem.py`、`code/ldvh/governance/git.py`、`ldvh`、`git_hooks/**`），每次提交扫描 Index 是否包含匹配路径。匹配则触发平台声明失效流程。glob 模式随代码重构同步更新（列入 Code 实现规划）。

- **AI 复核轨**：机械扫描无法覆盖语义级「擅入」（例如一个非平台相关模块新增了 `import os` + `os.name` 条件分支），由 AI 在 Code review 中判断是否触及平台相关面。AI 发现新的平台相关面文件时，应同时建议更新机械扫描 glob 清单。

机械扫描清单与代码模块结构耦合，无法完全避免失真是正常的——核心是机械扫描覆盖已知面，AI 复核覆盖未知面，两者互补而非追求机械完备。

### 发现 3：重验触发机制设计——分级触发

**分级触发模型**：

| 级别 | 触发条件 | 动作 | Gate 角色 |
|---|---|---|---|
| L1 机械阻断 | Index 包含平台相关面清单内文件 | Git Gate block，要求提交者声明受影响平台范围 | 机械路径匹配，纯确定性 |
| L2 消息声明 | commit message 必须包含 `Platform-Affected:` 或 `Platform-Verified:` trailer | precheck 验证 trailer 存在性及格式 | 机械格式校验 |
| L3 语义判断 | AI/Human 判断改动是否实际改变了另一平台的运行时语义 | 决定重验范围：全部重验、子集重验、或确认无影响（声明 `unaffected`） | AI/Human 语义判断，非机械 |

**Git Gate 可行性边界**：

- **可行**：机械路径匹配——Git Gate 读取 Index 中 `staged` 文件路径，与平台相关面 glob 清单比对。这是纯确定性操作，适合 Git Gate 的封闭机械检查边界。
- **边界**：Git Gate 只做路径匹配，不做语义判断。匹配到平台相关面文件时，Git Gate 只能 block 并要求 message 声明，不能自动判定改动是否真的影响另一侧平台。语义判断（L3）归 AI 或 Human。
- **不可行**：Git Gate 不应尝试 diff 分析、AST 扫描或语义推断来判定「是否真的影响另一侧」。这些超出 Git Gate 的机械检查范围。

**Message 声明格式约定**（候选）：

在 commit message body 中新增以下 trailer（按 03 §9.3/§9.4 现有 trailer 闭集扩展）：

```
Platform-Affected: macos | windows | both | unaffected
Platform-Verified: macos | windows | both | none
```

- `Platform-Affected`：AI/Human 判断本次改动影响哪些平台的运行时语义。
- `Platform-Verified`：本次提交前已在哪些平台完成验证。
- 两者不一致时（如 Affected=both 但 Verified=macos），另一侧视为 unverified，须在后续提交或 CI 中补验。

### 发现 4：测试与 CI 最小方案

**架构原则**：一套代码，同一套测试用例，两侧跑。

**方案**：

| 维度 | macOS（当前已验证） | Windows（当前 unverified） |
|---|---|---|
| 日常开发 | 本地 full test suite | 可选本地 subset（`pytest -m "not native_windows"`） |
| CI matrix | GitHub Actions `macos-latest` runner | GitHub Actions `windows-latest` runner |
| 平台专属测试 | 不需特别标记 | 标记 `@pytest.mark.native_windows`（已实现） |
| 验收跑 | 本地提交前 | Windows CI PR gate 或 Human 授权后手动触发 |

**mac 改动破坏 Windows 语义的探测面设计**：

1. **共享测试层**：平台无关逻辑测试在两侧都跑，mac 侧改动若破坏平台抽象层接口，Windows 侧的同一测试会失败。
2. **平台专属测试**：`code/tests/platform/test_native_windows.py` 已在 `native_windows` marker 下覆盖 Windows 特有行为（junction、symlink、lock、drive letter、UNC）。这些测试在 macOS CI 中被 skip，只在 Windows CI 中跑——mac 改动若破坏 Windows 底层语义，Windows CI 会暴露。
3. **CI 门禁**：Windows CI 作为 PR merge 的必要门禁（非阻塞门禁时至少为 required check）。mac 改动在 Windows CI 失败时，提交者必须判断：是平台抽象层接口不兼容（须修抽象层），还是 Windows 测试环境问题（须调测试）。
4. **依赖探测**：根 launcher 的 `_ensure_dependency_runtime` 已处理 `.venv/Scripts/python.exe` Windows 候选路径，Windows CI 中应验证此路径探测逻辑。

**CI 成本**：Windows runner 分钟数需额外预算。最小方案下，仅 PR 含平台相关面文件时才触发 Windows CI job，纯规范/文档/Web 变更跳过。

### 发现 5：与 spark-0004 验收矩阵的衔接

spark-0004 当前验收面：
- CLI 与文档入口
- 路径与管辖判定
- Git 与 AI 入口
- Web 与测试

建议在 spark-0004 的验收矩阵中新增「跨平台变更传播后重验」验收面，包含以下验收行：

| 验收项 | 验收条件 | 验证方法 |
|---|---|
| 平台相关面清单覆盖 | ？清单文件有新增/删除时，维护者更新 glob 模式 | 提交历史检查 |
| Git Gate 路径匹配 | Index 包含清单内文件时 Git Gate 正确 block | 真实提交事件测试（mac 侧） |
| Message 声明格式 | precheck 验证 `Platform-Affected:` / `Platform-Verified:` 格式正确 | precheck 单元测试 |
| AI 判断重验范围 | AI 能给出 `unaffected` / `both` 判断并记录理由 | AI 行为抽查 |
| CI matrix 平台覆盖 | PR 含平台相关面文件时自动触发 Windows CI | CI 配置检查 |
| 平台声明状态同步 | 09 §6.3 平台声明与实际已验证范围一致 | 定期审计 |

## 建议

### 建议 1：规范修订（可立即进入）

按 01 §13.6 的「规则缺口的来源先行闭环」，以下最小增量草案可直接进入规范修订：

**09 §6.3 新增「平台声明生命周期」条款（建议位置：09 §6.3 末段后作为 09 §6.3.1）**：

> ##### 6.3.1 平台声明的变更触发与失效
>
> 当受管辖 worktree 的 Git Index 包含平台相关面清单（按 07 §5 界定）内文件的改动时，该 worktree 的「已验证平台」声明中受影响平台侧自动失效、回退 `unverified`。
> 
> 失效的平台侧在以下任一条件成立后方可恢复 verified：
> 1. 在目标平台实际执行范围匹配的测试并全部通过，且测试结果绑定到当前 worktree；
> 2. AI/Human 判断改动不影响目标平台运行时语义，并在 commit message 中以 `Platform-Affected： unaffected` 声明。
>
> 验证恢复的测试结果或判断依据须保留在对应 WorkCase 或 Study 中。

**07 §5 新增「平台相关面界定」条款（建议位置：07 §5 末）**：

> ##### 5.x 平台相关面的界定与维护
>
> 平台相关面指代码中因操作系统差异（macOS vs Windows）而行为不同的模块、入口或配置。一条代码路径属于平台相关面，当且仅当满足 §5.x.1–§5.x.5 任一条件。（具体条件见本报告发现 2 的界定标准。）
>
> 平台相关面清单以机械可执行的 glob 模式维护在 Git Gate 配置中；新增/删除清单条目须同步更新 glob 模式。机械扫描无法覆盖的语义级「擅入」由 AI 在 Code review 中识别并建议更新清单。

### 建议 2：创建 WorkCase「跨平台重验 Git Gate 实现」

目标：在现有 Git Gate 中增加平台相关面路径匹配逻辑，验证 message trailer 格式，形成 L1+L2 机械阻断能力。
验收条件：
- Git Gate 在 Index 含平台相关面文件时返回 block，diagnostics 包含匹配路径清单
- precheck 验证 `Platform-Affected：` / `Platform-Verified：` trailer 格式
- 测试覆盖：正例（清单内文件被改动→block）、反例（清单外文件→pass）、边界（空 Index、删除清单文件）

### 建议 3：更新 spark-0004 验收矩阵

将发现 5 的六项验收行追加到 spark-0004 的验收矩阵中。

## 后续分流

| 项目 | 承接对象 | 判断标准 | 状态 |
|---|---|---|
| 09 §6.3.1 条款新增 | 规范修订（Human 授权后执行） | Human 确认归口判断正确 | 已给出草案，待授权 |
| 07 §5.x 条款新增 | 规范修订（Human 授权后执行） | Human 确认归口判断正确 | 已给出草案，待授权 |
| 03 §9.3/§9.4 trailer 扩展 | 规范修订（Human 授权后执行） | 09/07 修订完成后 | 方案已明确，等待前置修订 |
| Git Gate L1+L2 实现 | 新 WorkCase | 规范修订完成，Human 授权实现 | 建议已给出，等待创建 |
| spark-0004 验收矩阵更新 | spark-0004 更新（属 spark 事实更新，不需要 WorkCase） | Human 确认验收行 | 草案已给出 |
| Windows CI 矩阵配置 | 环境接入行动（属 WorkCase 或 环境接入） | 有 Windows runner 可用且 Human 授权 | 等待条件成立 |
