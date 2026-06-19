# Git 提交规范

```yaml
ldvh_doc:
  doc_id: "10"
  doc_kind: "formal_spec"
  title: "Git 提交规范"
  status: "active"
  canonical_path: "specs/10-Git提交规范.md"
  created: "2026-06-19"
  updated: "2026-06-19"
  parent_doc: ""
  relation: ""
  positioning: "定义 LDVH 自身项目及所有管辖项目的 Git 提交格式、提交语言、Code/Web 可解析字段和派生追溯边界"
  scope: "LDVH 自身项目及所有接入 LDVH 且需要通过 Git commit records 追踪文件事实源修改的管辖项目"
  basis:
    - "specs/00-LD-Vibe-Harness理念与纲要.md"
    - "specs/09-事实源边界与承载规范.md"
  related_specs:
    - "specs/01-目录说明.md"
    - "specs/07-Code确定性执行实现规范.md"
    - "specs/08-Web信息同步实现规范.md"
    - "specs/11-测试基础规范.md"
  code_consumption:
    - "doc_metadata"
    - "relations"
    - "structure"
    - "landing_requirements"
```

---
## 1. 本文解决的问题

本文解决整个 LDVH 管辖项目的 Git commit message 应如何格式化书写、AI 和 Human 如何利用 Git 历史理解变更、Code 如何校验提交格式、Web 如何解析和展示提交记录派生视图，以及工作对象是否需要手写关联提交字段的问题。

Git 提交记录不是 LDVH 工作对象，不进入 20-39 工作模型集合，不创建 `ldvh-base/changes/`，也不具备 YAML 状态机。它是事实源修改的 Git 层追溯证据，服务 `specs/09-事实源边界与承载规范.md` 定义的 Git 可追踪原则。

---
## 2. 与 09 和工作模型的关系

09 定义最终事实源必须是 Git 可追踪文件。本文承接 09，专门定义修改这些文件时 Git commit message 应如何写，确保 Git commit records 可读取、可审查、可校验、可被 Code/Web 解析和派生展示。

Git 提交记录与工作模型的边界如下：

| 内容 | 权威位置 |
|---|---|
| 工作对象状态、字段、验收和关闭判断 | 对应 `ldvh-base/` YAML 或 Study Markdown 实例 |
| 工作对象字段契约和状态机 | 20-39 具体工作模型规范 |
| 事实源修改的提交证据 | Git commit records |
| Git 提交格式与派生追溯规则 | 本文 |
| 提交记录的列表、筛选、关联和详情展示 | Code/Web 派生视图，不替代 Git |

工作对象不得手写维护 `related_changes` 这类提交清单字段。需要查看某个对象相关提交时，应由 Code 或 Web 根据 Git 历史、文件路径、对象 ID、提交正文自然文本和必要索引实时派生。派生结果可以展示为“关联提交”或“提交记录”，但不得回写为新的对象事实字段。

---
## 3. 适用范围

以下修改应通过符合本文契约的 Git commit 留痕：

1. 修改 specs 正式规范、规则入口、能力资产、Code、Web、测试或配置；
2. 修改 `ldvh-base/` 下的工作对象事实源；
3. 修改 Study Markdown、docs 正文、docs/studies、docs/sources 或经授权沉淀的项目文档；
4. 修改会影响 Human Gate、状态流转、事实源边界、校验逻辑、Web 呈现或 AI 入口的文件；
5. 完成 WorkPlan、ADR、Memo、Study、Pitfall、WorkArea 等对象的创建、关键字段改写、状态变化、归档或删除；
6. 回退、修正或补充之前已提交的事实源修改。

未进入 Git 的临时实验、构建产物、缓存或本地草稿不形成正式提交记录；一旦提交，就应尽量符合本文格式。

---
## 4. commit message 格式

LDVH 使用 Conventional Commits 1.0.0（约定式提交规范）作为 Git commit message 标准，外部标准链接为 <https://www.conventionalcommits.org/en/v1.0.0/>。提交信息必须在可解析的首行和必要正文中说清楚本次做了什么，不使用 `Refs:`、`Human-Gate:`、`Verification:`、`Risk:` 四类专用 trailer 作为标准格式字段。

标准格式如下：

```text
<type>[optional scope][!]: <description>

[optional body]
[optional footer(s)]
```

| 字段 | 要求 | 说明 |
|---|---|---|
| `type` | 必填 | 提交类型，使用本文 §5 的英文枚举 |
| `scope` | 可选 | 影响范围，使用本文 §6 推荐值或项目扩展值 |
| `!` | 可选 | 破坏性变更标记，对应 Conventional Commits 的 breaking change |
| `description` | 必填 | 简体中文简短说明，推荐不超过 72 字符 |
| `body` | 可选 | 使用简体中文说明做了什么、为什么做、影响范围、关键取舍和必要上下文 |
| `footer` | 可选 | 只使用 Conventional Commits 兼容 footer，例如 `BREAKING CHANGE:`；LDVH 不定义固定尾部字段 |

所有提交都遵守同一套格式。正文长短由变更复杂度决定，不按“普通/特殊”区分提交类别。复杂变更、规范变更、迁移、回退或跨多个事实源的修改，应在正文用自然语言说明变更内容和影响，不拆成 LDVH 自定义固定 trailer 字段。

---
## 5. type 枚举

| type | 简体中文 | 说明 |
|---|---|---|
| `feat` | 功能 | 新增功能、能力或用户可见对象 |
| `fix` | 修复 | 修复缺陷、错误或不符合预期的行为 |
| `docs` | 文档 | 文档修改 |
| `refactor` | 重构 | 重构，不改变外部行为 |
| `test` | 测试 | 测试相关 |
| `chore` | 维护 | 辅助维护、杂项或难以归入其他类型的非功能变更 |
| `build` | 构建 | 构建系统或外部依赖修改 |
| `ci` | CI | CI 配置或流水线修改 |
| `perf` | 性能 | 性能优化 |
| `style` | 样式 | 代码格式、空白、排版等不影响语义的修改 |
| `revert` | 回退 | 回退之前的提交 |
| `spec` | 规范 | LDVH 扩展类型：specs 规范修改 |
| `rule` | 规则 | LDVH 扩展类型：Rules / Instructions 修改 |
| `adr` | 决策 | LDVH 扩展类型：ADR 实例创建或状态变化 |

不得使用 `improve`、`update`、`完善`、`优化` 这类含义不稳定的 type。所谓“完善”必须按实际变更目的落入明确类型：新增能力用 `feat`，修复问题用 `fix`，规范修改用 `spec`，文档修改用 `docs`，代码结构整理用 `refactor`，维护性调整用 `chore`。

---
## 6. scope 推荐值

| scope | 含义 |
|---|---|
| `specs` | specs 规范文档 |
| `docs` | docs 正文或项目文档 |
| `rules` | Rules / Instructions |
| `code` | Code / 工具实现 |
| `web` | Web 实现 |
| `tests` | 测试代码 |
| `config` | 项目配置 |
| `workarea` | WorkArea 实例 |
| `workplan` | WorkPlan 实例 |
| `adr` | ADR 实例 |
| `memo` | Memo 实例 |
| `study` | Study 实例 |
| `pitfall` | Pitfall 实例 |
| `studies` | docs/studies 相关修改 |
| `sources` | docs/sources 相关修改 |

scope 为推荐值。项目可以在不破坏解析的前提下扩展，但不应用 scope 创造新的工作对象类别。

---
## 7. 关联提交派生

工作对象、规范、Code 和 Web 需要“关联提交”时，应按以下优先级派生：

1. commit touched files 与对象事实源路径、规范路径、Code/Web 文件路径的匹配；
2. commit description 或 body 中自然出现的对象 ID、规范编号、规范路径或文件路径；
3. Git 提交时间线、相邻提交、分支上下文和人工审查结论；
4. 必要时由用户或 AI 在当前分析中临时筛选，但不得回写为手填提交字段。

对象 ID、规范编号或路径可以出现在 description 或 body 中，但不得要求 AI 为了追溯而补写固定 `Refs:` 字段。Git 变更由 Git 自身的 hash、文件路径、diff 和时间线追踪。

---
## 8. 提交语言要求

LDVH 自身项目的提交说明必须使用简体中文表达主要人类可读内容。`description`、`body` 和 footer value 应使用简体中文；`type`、`scope`、`BREAKING CHANGE` 等 Conventional Commits 标准 token、路径、命令、对象 ID、英文专名和代码标识可以保留英文或原文。

Code 可机械检查 commit message 是否包含中文字符、是否符合首行格式、type 是否属于枚举、description 是否为空；简体中文与繁体中文的细分判断若无法可靠机械化，应由 Human 审查兜底。

---
## 9. Human Gate 与风险

Git 提交记录本身不额外触发 Human Gate。Human Gate 由被修改的事实源、对象、规范、Code、Web、工作流程或破坏性 Git 操作触发。

以下场景应在提交正文或对应事实源中用自然语言说明确认情况，但不使用 `Human-Gate:` trailer：

1. 修改事实源边界、对象状态机、字段契约、规范编号、目录归属或 AI 入口；
2. 删除、迁移或重命名工作对象事实源；
3. 执行破坏性 Git 操作，例如改写已共享历史、强推、删除分支或批量回退；
4. 修改受控写入、校验、Human Gate、Web 编辑或安全相关能力；
5. 用户明确确认某个高影响方向、迁移策略或验收结论。

需要说明残留风险、未验证内容或兼容性影响时，应写入提交正文或对应工作对象事实源，不使用 `Risk:` trailer。不得用“应该没问题”替代风险说明。

---
## 10. Code 消费规则

Code 可以实现以下能力：

1. 校验 commit message 首行格式、type 枚举、description 长度和中文要求；
2. 检查不得出现 `Refs:`、`Human-Gate:`、`Verification:`、`Risk:` 四类 LDVH 禁用固定 footer；
3. 基于 Git 历史、touched files、description/body 自然文本派生对象关联提交；
4. 为 Web 提供提交列表、提交详情、文件统计和必要的派生关联；
5. 对格式不稳定的提交给出 warning；
6. 检查对象事实源中是否仍出现需要清理的手写提交字段。

Code 输出只是派生诊断、导航或展示数据，不替代 Git commit records。commit message 格式规则变化后，应同步更新 `code/commit_validate.py`、相关测试和 Web API 解析契约。

---
## 11. Web 呈现规则

Web 可以展示 Git 提交记录列表、最近提交、提交详情、文件统计和对象相关提交。

Web 呈现必须遵守：

1. 页面和导航表达为“提交记录”“最近提交”或“Git 提交记录”，不得把它表达为独立工作对象；
2. `/changelog` 可作为路由名保留，但页面文案应表达为提交记录派生视图；
3. Dashboard、ProjectFiles 和 Changelog 应尽量共享同一 commit DTO 或解析契约；
4. 对象详情中的关联提交应由 Git 派生，不从对象 YAML 手写字段读取为权威事实；
5. Web 不展示 `Refs:`、`Human-Gate:`、`Verification:`、`Risk:` 作为固定字段或标签；
6. Web 缓存、页面状态、筛选状态和派生索引不得替代 Git commit records。

---
## 12. 示例

```text
spec(specs): 采用约定式提交规范

将 Git 提交首行统一为 Conventional Commits 格式。
Code 和 Web 可以稳定解析 type、scope、breaking marker 和 description。
```

```text
fix(web): 修复提交记录分类解析

支持 type(scope)!: description 格式，避免 breaking change 提交被识别为 other。
Dashboard 和 Changelog 可以继续按 type 展示提交分类。
```

```text
feat(web)!: 调整提交记录接口字段

返回 category、scope、description 和 isBreaking 字段，供前端统一消费。

BREAKING CHANGE: 旧的仅首行描述消费方需要改为读取 description。
```

---
## 13. 规范落地要求

本文通过以下规范落地要求说明相关要求的同步、检查或审计触发条件。

| 落地要求 | 要求内容 | 保障机制 | 同步类型 | 触发条件 |
|---|---|---|---|---|
| 上位约束承接要求 | 事实源修改应通过 Git 提交记录留下可追溯证据，不再把提交记录建模为工作对象 | 09、本文、06、Human Gate | 事实源治理 | 修改 Git 文件事实源、工作对象状态、规范、Code、Web 或入口资产时 |
| 入口可见要求 | AI 准备提交、审计提交历史或追溯对象相关提交时应能定位本文 | Rules 入口摘要、commit_validate 帮助、Web 提交记录页 | AI 执行入口提示 | 提交、回退、审计、关闭 WorkPlan 或查询关联提交时 |
| 确定性执行要求 | commit message 可机械校验的部分由 Code 检查，关联提交由 Git 派生 | `code/commit_validate.py`、Git 查询、测试夹具 | 校验实现 | 提交契约或关联派生规则变化时 |
| 确定性执行要求 | LDVH 自身仓库应提供或启用提交前 message 校验入口；未启用 Git hook 时，AI 提交前必须手动运行等价预检 | `commit-msg` hook、`code/commit_validate.py --check-message`、CI 或人工降级检查 | 触发保障 | 创建 Git commit、修改提交契约、调整 hook/CI 或迁移仓库入口时 |
| Human 交互要求 | 高影响事实源修改和破坏性 Git 操作必须记录或触发 Human Gate | Human Gate、提交正文或对应事实源 | 人工确认 | 修改事实源边界、状态机、字段契约、入口资产或执行破坏性 Git 操作时 |
| 生命周期触发要求 | 本规范变化后，应同步检查 01、05、05.01、05.02、05.03、06、07、08、Code、Web 和测试 | specs 检查、Code 测试、Web 类型检查、残留搜索 | 触发保障 | 提交格式、关联派生或 Web 展示规则变化时 |

---
## 14. Human Gate 与检查要求

以下情况应评估 Human Gate：

1. 改变 Git 提交记录的事实源定位；
2. 改变 commit message 必填字段、提交语言、提交门禁或破坏性 Git 操作边界；
3. 把提交记录重新建模为工作对象或创建 `ldvh-base/changes/`；
4. 把 Web 缓存、数据库索引或对象 YAML 字段提升为提交记录事实源；
5. 删除 Code 校验或降低高影响事实源修改的追溯要求。

检查至少包括：

| 检查项 | 标准 |
|---|---|
| 事实源边界 | 提交记录由 Git commit records 承载，不创建工作对象实例 |
| 格式契约 | commit message 首行、type、scope、breaking marker 和 description 可被解析 |
| 语言要求 | LDVH 自身提交主要人类可读内容使用简体中文 |
| 提交门禁 | LDVH 自身仓库存在 `commit-msg` hook、CI 或等价预检入口；未启用时提交执行者必须在提交前运行 `code/commit_validate.py --check-message` |
| 派生关联 | 对象关联提交由 Git 历史、文件路径、对象 ID 和正文自然文本派生，不手写维护 |
| Code 边界 | Code 只校验、解析和聚合，不替代 Git |
| Web 边界 | Web 只展示派生视图，不替代 Git |

---
## 15. 待补齐事项

1. 应补齐 LDVH 自身仓库的 `commit-msg` hook 或 CI 提交信息检查，并明确哪些 warning 升级为 error；
2. 若未来支持多仓库管辖项目，应补齐跨仓库提交记录查询和 Web 聚合边界；
3. 若未来需要自动派生对象关联提交，应优先基于 touched files、对象 ID、规范编号和正文自然文本实现，不恢复手写字段或专用 trailer。
