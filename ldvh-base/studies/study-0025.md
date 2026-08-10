---
title: LDVH Windows 受控写入与环境接入的目标平台实测证据
status: active
report_kind: technical_assessment
input_refs:
- kind: spec
  locator: specs/05-事实模型基础规范.md §11.8
- kind: spec
  locator: specs/09-环境接入规范.md §6.3 / §6.3.1
- kind: test
  locator: code/tests/platform/test_native_windows_approved_writes.py
- kind: test
  locator: code/tests/platform/test_native_windows.py
- kind: test
  locator: code/tests/platform/test_native_windows_runner.py
- kind: test
  locator: code/tests/facts/test_atomic_write.py
- kind: test
  locator: code/tests/facts/test_allocator_lock.py
- kind: test
  locator: code/tests/git_hooks/test_commit_msg.py
research_question: LDVH 能否声称支持 Windows？在 09 §6.3 将 Windows 列为「未验证范围、不得声明完整接入成立」的前提下，受控事实写入与 Git Hook 执行能力是否已在目标平台（win32 / NTFS fixed drive / Python 3.13.14）实测通过，从而满足 §6.3.1 恢复 verified 的门槛？
abstract: 本文汇总 2026-08-07 在 Windows 目标平台对 ldvh 受控写入与环境接入的实测证据。native_atomic_fact_writes_supported() 在 Windows 返回 True；11 个 native_windows 标记测试（原子写入、六进程分配器连续 ID、跨 worktree 共享计数器、条件更新单赢、file-only 边界、worktree 隔离、junction/symlink/UNC 拒绝、msvcrt 锁串行化）全绿；经 Helper 服务层 prepare→create→read 端到端写入 spark 成功并读回一致、磁盘无 CRLF；14 个 commit-msg Git Hook 测试在 Windows 经 Git Bash 真实调起并全部通过（含真实 git commit 被钩子拦截/放行）。据此，09 §6.3 §8 未验证清单各项已在目标平台实测通过，满足 §6.3.1「在目标平台实际执行范围匹配的测试并全部通过，且测试结果绑定到当前 worktree」的恢复门槛。
research_intent: 为「把 09 §6.3 中 Windows 从『未验证范围』翻为『已验证平台』」这一 Human Gate 决策留存可回指证据；不替代 Human 决定，仅如实交还实测范围与未验证范围。
recommendation_summary: 建议经 Human Gate 后将 09 §6.3 的 Windows 声明由「未验证范围」更新为「已验证平台（受控写入，file_only 耐久，仅限 NTFS fixed drive）」，并保留 05 §11.8 的授权范围与残留风险声明不变。完整接入的其它平台（非 Windows）仍按未验证范围处理。
change_log:
- signature:
    agent_id: workbuddy-ldvh-verify
    host_environment: Codex
  session_id: verify-windows-support-2026-08-07
  at: '2026-08-07T18:56:39.522746+08:00'
  summary: Created by Windows on-target verification evidence collection.
- at: '2026-08-10T09:05:04.323871Z'
  summary: '受控更正历史 change_log 中的 agent_workbench 格式；修复项为 0: windows-nt-verify -> Codex。原始错误值已由本次更正覆盖并保留本条修复记录。'
  signature:
    agent_workbench: Cindy
    model_id: gpt-5
  session_id: cindy-codex-alias-migration-20260810

object_id: study-0025
fact_type_key: study
created_at: '2026-08-07T18:56:39.522746+08:00'
updated_at: '2026-08-10T09:05:04.323871Z'
---

## 研究问题

LDVH 能否声称支持 Windows？具体门槛来自 09 §6.3：Windows 受控事实写入虽已按 05 §11.8 条件 (a)–(c) 获准，但「仓库入口、运行依赖、路径写法、Git Hook 执行能力和环境接入完整验证」仍列为 §8 未验证范围，且「未在目标平台实测前，不得声明 Windows 完整接入成立」。本 Study 核验这些项是否已在 Windows 真机实测通过。

## 输入与边界

本次证据全部来自 2026-08-07 在以下目标平台的实际执行：

- 平台：`win32`（Windows NT），文件系统 NTFS fixed drive
- 运行时：Python 3.13.14（managed），ldvh 以源码启动器运行
- 绑定 worktree：`E:/WorkBuddy/ld-vibe-harness-v4`，HEAD `c6eac7a6`

边界：仅覆盖受控写入与 Git Hook 执行能力相关路径；不覆盖其它未声称平台，不证明自然语言事实真实性或上层工作完成。

## 关键发现

### 1. 平台写入门已对 Windows 打开

`native_atomic_fact_writes_supported()` 在 Windows 真实返回 `True`（05 §11.8 条件 c 已于 2026-08-07 经 Human Gate 满足）。

### 2. native_windows 写入测试全绿（11 项）

`code/tests/platform` 与 `code/tests/facts` 中标记 `native_windows` 的 11 个测试全部通过（win32 / Py3.13.14 / 10.19s）：原子写入落盘、六进程分配器连续 ID、跨 worktree 共享计数器、条件更新单赢无撕裂、file-only 创建/替换边界精确报告、git linked-worktree 临时索引隔离、junction/symlink/UNC 读取前拒绝、msvcrt 锁串行化且 kill 后恢复。

### 3. 经 Helper 服务层端到端写入与读回（正反例）

在临时 NTFS governed project 走 `prepare-fact-object-draft → create-fact-object → read-fact-objects`：

- 正例：`create` 返回 `outcome=ok`、分配 `object_id=spark-0001`、真实落盘；`read-fact-objects` 读回 title 与写入一致；磁盘校验文件存在、无 CRLF、含正确 object_id。
- 反例：`status="bogus_status"` → `create` 返回 `outcome=rejected`（「事实对象初始状态不符合当前类型来源」），零文件落盘。

### 4. Git Hook 执行能力（§8 最后未验证项）已在 Windows 实测通过

`code/tests/git_hooks/test_commit_msg.py` 共 14 个测试在 Windows 经 Git Bash 真实调起 POSIX `commit-msg` 钩子，全部通过（72.65s）。覆盖：钩子安装到 git common-dir 并覆盖既有/后续 linked worktree、真实 `git commit` 因缺失 body/关键变更被钩子拦截（returncode=1）与合规提交被放行（returncode=0）、legacy override 迁移、冲突零写入、无 Human Gate 确认时 unavailable、注入防护等。

## 建议

按 09 §6.3.1，平台声明从 `unverified` 恢复 `verified` 需「在目标平台实际执行范围匹配的测试并全部通过，且测试结果绑定到当前 worktree」。上述证据已满足该门槛。建议经 Human Gate 后将 09 §6.3 的 Windows 表述更新为「已验证平台（受控写入，file_only 耐久，仅限 NTFS fixed drive）」，并保留 05 §11.8 授权范围与残留风险声明不变。该更新属 Human 决策，本 Study 仅留存证据。

## 后续分流

| 分流类别 | 触发条件 | 下一步 |
|---|---|---|
| 进入规范修订 | Human Gate 接受本证据 | 修订 09 §6.3，将 Windows 翻为已验证平台 |
| 持续回归 | 后续改动触及平台相关面 | 按 §6.3.1 触发重验或回退 unverified |
| 不对象化 | 仅验证写入路径 | 不创建额外对象 |
