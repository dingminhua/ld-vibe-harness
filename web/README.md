# LDVH Web

LDVH 事实对象展示面板。

## 快速启动

```bash
# 安装依赖
npm install

# 启动开发服务器（自动清理端口占用）
./restart.sh

# 或手动启动
npm run dev
```

- 前端：http://localhost:5173
- 后端：http://localhost:3001

## 重启

端口固定为 5173（前端）和 3001（后端）。如果端口被占用，使用重启脚本自动清理：

```bash
./restart.sh
```

## 构建

```bash
npm run build
```
