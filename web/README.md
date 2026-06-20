# LDVH Web

LDVH 事实对象展示面板。

## 快速启动

```bash
# 从仓库根安装 Web 依赖
npm --prefix web install

# 从仓库根启动开发服务器（自动清理端口占用）
npm run web:restart

# 或在 web/ 目录内手动启动
cd web
npm run dev
```

- 前端：http://localhost:5173
- 后端：http://localhost:3001

## 重启

端口固定为 5173（前端）和 3001（后端）。如果端口被占用，使用重启脚本自动清理：

```bash
npm run web:restart
```

## 构建

```bash
npm run web:build
```

## 检查

LDVH 的测试统一放在仓库根 `tests/` 下。Web API 测试也从根级入口运行。

```bash
npm run check
npm run test:web:api
```

## 开发文档入口

Web 页面开发先阅读：

1. [`web/docs/10-Web开发现状与设计语言基线.md`](./docs/10-Web开发现状与设计语言基线.md)
2. [`web/docs/01-全局设计约束.md`](./docs/01-全局设计约束.md)
3. 当前页面对应文档，例如 ObjectList、ObjectDetail 或 Changelog。

当前设计语言以提交、研究、决策、备忘、经验五个已完善模块为基线。后续页面改造应优先复用它们的列表卡片、详情身份头部、正文节点、关联行、复制语义和右侧扩展阅读语言。
