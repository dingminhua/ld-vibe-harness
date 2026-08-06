# 原生 Windows 能力断言集合对齐当前 18 项公开操作

本规划只分配实现责任、依赖、接口、副作用、诊断和测试，不定义或覆盖规则源语义。

## 背景与动机

`code/tests/platform/test_native_windows.py` 第 107 行的探针

```python
assert {item["operation_key"] for item in response["result"]["operations"]} == OPERATIONS
```

以写死的 `OPERATIONS` 集合（原为 12 个 key）与 `ldvh capabilities` 的实时结果做严格相等比较。自该测试写就后，LDVH 的公开操作已由 12 项增至 18 项（新增 `check-fact-integrity`、`close-workcase`、`correct-closed-workcase`、`migrate-legacy-change-log`、`prepare-closed-workcase-candidate`、`read-specification-context`），导致该探针在真 Windows 上**必然失败**，且与 Windows 支持无关——是测试断言过期。

该文件第 25–28 行为模块级 `pytestmark`，仅在 `win32/nt` 下执行，故 Linux/macOS 的 CI 整体跳过此文件，能力增长时未被任何常规测试捕获，直到在真 Windows 上跑 workcase-0008 的 preflight 才暴露（现存 `E:/ldvh-evidence/preflight-001` 即因此首项 `native_environment_and_console` failed）。

Human 选定**方案 B**：保持严格 `==`，将 `OPERATIONS` 更新为当前权威 18 个 key（而非放宽为子集包含）。

## 实现责任

- 文件：`code/tests/platform/test_native_windows.py`
- 改动：仅替换第 30–43 行区域的 `OPERATIONS` 集合字面量，由 12 key 扩展为当前 `ldvh capabilities` 返回的 18 key。
- 权威来源：2026-08-05 在真 Windows 上 `ldvh capabilities` 的 `scope.completed`（18 项，按字母序录入集合）。

## 依赖

- 无新增/变更第三方或内部依赖。
- 与 `tools/verify_native_windows.py` 的 preflight `BASE_PROBES` 对齐：被引用的探针函数名 `test_native_environment_is_windows_ntfs_with_source_launcher` 未变，工具调用方式不变。

## 接口

- 仅修改测试内部集合字面量，不改 `_cli` helper、源码 `ldvh` 启动器或任何 CLI 行为。
- 探针语义保持为："原生 Windows runner 上 `ldvh capabilities` 恰好返回当前规则源发现的公开操作集合"（严格守卫，任何增/删都会失败）。

## 副作用

- 无运行时副作用；探针仅只读调用 `ldvh capabilities`。
- 本改动使 workcase-0008 的 preflight 首项探针在真 Windows 上可获通过（前提是其余探针也通过）。但本规划**不覆盖** workcase-0008 的执行授权或其余探针/core-readonly 的验收，仅修正测试断言。

## 诊断

- 若未来 `ldvh capabilities` 再次增减，该严格 `==` 会立即失败并明确指向 `OPERATIONS` 集合（fail-loud），符合方案 B"能力清单冻结守卫"的意图；届时需同步更新本集合字面量。

## 测试

- 已在真 Windows（`sys.platform=win32`, `os.name=nt`, NTFS E:）验证：
  `.venv/Scripts/python.exe -m pytest code/tests/platform/test_native_windows.py -k test_native_environment_is_windows_ntfs_with_source_launcher -p no:cacheprovider -q`
  结果：`. [100%]`，exit 0，1 passed（2026-08-05）。
- 其余 Windows 探针、`core-readonly` 策略探针及写矩阵不在本规划范围。
