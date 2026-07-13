# V4 Code 入口

> 本文只是 Code 目录、运行和资料入口，不再承担当前实现规划、状态、顺序、验证证据或完成声明。V4 唯一当前推进与 Code 实现规划入口是 [`V4-工作推进总纲.md`](../v4-architecture/V4-工作推进总纲.md)。实现语义必须回到当前有效 Specs 和授权附件。

## 目录边界

- `code/ldvh/`：V4 Python Code 实现。
- `code/tests/`：与 Code 共属的 tests。
- `pyproject.toml`：Python 包、依赖、测试和 Ruff 配置。

Code tests 不代替 `web/tests/`，也不证明环境接入、Web 适配或整个 V4 完成。

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

已有满足要求的虚拟环境时，不需要重复建立或安装。不得使用低于 3.12 的系统默认 `python` 解释测试收集失败为 Code 回归。

实际通过数、当前实现范围、已知缺口和下一增量的准入条件只在工作推进总纲中更新。替换前的已完成增量详细由 Git 历史保留，不作为并行的当前设计。
