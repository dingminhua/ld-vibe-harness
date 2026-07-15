# Web V4 bridge 停放记录

日期：2026-07-15

停放分支：`codex/park-web-v4-bridge-20260715`

基线：`dev-v4` / `f4308b08`

状态：暂停，不得合入 `dev-v4`，不得据此声明可发布

## 停放范围

本分支保存尚未挂载的 V4 Spark closed-JSON Python machine、list/detail/create 应用边界、TypeScript transport、V4→现有 DTO projector、普通 wheel/sdist machine 验证及对应测试。生产 `web/api/app.ts`、现有 routes、V3 writer、`web/api/services/facts.ts` 与 `web/src/**` 均未修改；`/api/v4/sparks` 仍为 404。

## 审核结论

1. PRE review：允许实施，但要求包内 machine、禁止调用 Helper CLI、无法由单值 `resolved_to` 表达的 routed 状态必须 fail closed。
2. 第一次 COMMIT gate：REQUEST CHANGES。发现 optional 空数组被补造、create 未预期异常完成状态错误、list 聚合预算缺失，以及 timeout、stream/process error、逐 operation runtime validator、普通 venv symlink 等问题。
3. 第二次 COMMIT gate：REQUEST CHANGES。发现 routed/discarded 条件字段 fixture 与 Schema 相反、create duplicate scan 未共用聚合预算、预算使用读取前 `lstat` 而非安全读取实际结果、response 状态与字段语义校验不够严格。
4. 上述第二轮 blocker/major 已在工作树继续修正，但用户在第三次全量验证期间明确暂停该方向；因此没有取得最终 COMMIT gate APPROVE，不得把当前实现视为已闭合。

仍保留的 reviewer minor：解释器 symlink 链验证后为保持普通 venv 语义仍启动配置路径，存在验证到 spawn 的链接重定向窗口；恢复时应重新评估可移植且不破坏 venv 的执行身份方案。

## 最后验证证据

- Web：`npm run check`、28 项 API/transport/projector 测试与 `npm run build` 通过；真实 TS transport 已完成临时项目的 list/create/read。
- Python 聚焦回归：89 项通过。
- 第三轮 Python 全量回归被用户暂停指令中断：当时 331 项通过，未形成最终全量结论。
- 更早一轮（第二轮修正前）Python 全量为 761 passed / 10 native-Windows-only skipped；该结果不能替代当前分支的最终回归。
- 普通 venv 的 direct wheel 与 sdist-derived wheel machine 矩阵曾为 2 passed；在最后一轮聚合预算下沉后未重新形成最终矩阵结论。

## 恢复条件

恢复本分支前必须重新进行 subagent PRE review；先核对本记录、当前 `dev-v4` 演进和三份审计结论，再 rebase/重做必要部分。随后完成全量 Python、Web build/test、普通 wheel/sdist、原生 Windows 证据及最终 COMMIT gate。未经这些证据不得挂载生产路由或合入 `dev-v4`。
