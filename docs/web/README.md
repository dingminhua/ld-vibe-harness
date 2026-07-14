# V4 Web 入口

> 本文只是 Web 目录、运行和资料入口，不再承担当前实现规划、状态、分批顺序、验证证据或完成声明。V4 唯一当前推进与 Web 实现规划入口是 [`V4-工作推进总纲.md`](../v4-architecture/active/V4-工作推进总纲.md)。稳定要求以当前有效 Specs 为准。

## 目录边界

- `web/api/`：Express API。
- `web/src/`：React 页面与组件。
- `web/tests/`：Web 自有 tests。
- `web/docs/`：既有产品实践和实现说明，不是 V4 规则源或当前计划。

当前实际浏览器观察见 [`V4-Web-浏览器表现基线.md`](V4-Web-浏览器表现基线.md)。该记录只承载当次观察证据与未验证范围。

## 常用入口

在 `web/` 目录运行：

```bash
npm ci
npm run dev
npm run check
npm run build
npm run lint
npm test
```

`web/tests/` 只验证 Web，不代替 `code/tests/`。实际结果、当前风险、实施 Gate、分批顺序和 V4 适配边界只在工作推进总纲中更新。
