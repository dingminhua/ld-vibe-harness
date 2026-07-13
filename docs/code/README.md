# V4 Code 入口

> 本文只是 Code 目录、运行和资料入口，不再承担当前实现规划、状态、顺序、验证证据或完成声明。V4 唯一当前推进与 Code 实现规划入口是 [`V4-工作推进总纲.md`](../v4-architecture/V4-工作推进总纲.md)。实现语义必须回到当前有效 Specs 和授权附件。

## 目录边界

- `code/ldvh/`：V4 Python Code 实现。
- `code/tests/`：与 Code 共属的 tests。
- `pyproject.toml`：Python 包、依赖、测试和 Ruff 配置。

Code tests 不代替 `web/tests/`，也不证明环境接入、Web 适配或整个 V4 完成。

## 实现导航

当前 Code 按下列边界组织：

- `code/ldvh/specs/`：当前规则源的发现、结构检查、派生投影与事实类型 Schema 投影。
- `code/ldvh/governance/`：管辖项目配置、Git worktree 身份与管辖范围解析。
- `code/ldvh/facts/`：事实对象载体、关系、验证、候选发现、项目级检查与受控创建。
- `code/ldvh/helper/`：公共请求响应、来源声明绑定、能力发现与 CLI 服务分流。
- `code/ldvh/helper/operations/`：当前规则源已声明公开操作的显式 Code 适配器。

当前已接入的公开操作为：

- `read-specification-candidates`：发现规范候选与 L0–L2 投影。
- `read-specification-content`：按精确选择展开 L3/L4 规则内容。
- `resolve-governance-scope`：解析工作对象的管辖项目范围。
- `find-fact-object-candidates`：从当前 Working Tree 直接发现 F0–F2 事实候选。
- `read-fact-objects`：按精确事实引用读取 F3 完整对象。
- `prepare-fact-object-draft`：无副作用地准备单个事实对象草案与预留信息。
- `create-fact-object`：在预留契约下受控创建单个事实对象。

上述列表是开发者导航，不是第二操作契约。操作是否取得公开身份、请求与结果结构、可用条件及边界，以当前有效 Specs 中的来源声明为准；Code 实现只有与来源声明成功绑定后才会被 Helper 公开。

## 常用检查

V4 Code 要求 Python 3.12 或更高版本。在仓库根目录建立开发环境并运行检查：

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m pytest code/tests
.venv/bin/ruff check .
.venv/bin/ruff format --check .
```

需要快速阅读五个事实类型的完整字段组合时，可以运行：

```bash
.venv/bin/python code/scripts/render_fact_type_fields.py .
```

输出从 `05.Att.01` 统一登记和 20–24 类型绑定实时派生，只用于阅读，不是第二字段权威或手写 Schema。

需要核对当前规则源实际公开的操作及某项请求契约时，运行：

```bash
.venv/bin/ldvh capabilities
.venv/bin/ldvh capabilities find-fact-object-candidates
```

`capabilities` 的返回值是当次 Working Tree 中规则源声明与 Code 实现的实时绑定结果，比本文的导航列表更权威。

已有满足要求的虚拟环境时，不需要重复建立或安装。不得使用低于 3.12 的系统默认 `python` 解释测试收集失败为 Code 回归。

实际通过数、当前实现范围、已知缺口和下一增量的准入条件只在工作推进总纲中更新。替换前的已完成增量详细由 Git 历史保留，不作为并行的当前设计。
