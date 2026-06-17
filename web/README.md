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
